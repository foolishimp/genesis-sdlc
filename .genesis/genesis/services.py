# Implements: REQ-R-ABG2-INTERPRET
# Implements: REQ-R-ABG2-BINDING
# Implements: REQ-R-ABG2-SELECTION-APPLICATION
"""
genesis.services — Named app services.

Orchestrates kernel modules into user-facing commands:
gen_gaps, gen_iterate, gen_start, Scope.

Three commands as named compositions of core functions. None introduce new
primitives. See ADR-004 (Scope).

  /gen-gaps    = bind_fd over scope → delta_summary fields
  /gen-iterate = discover one unconverged work item → traverse once
  /gen-start   = derive state → select work item → traverse
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from gtl.module_model import Module

from .binding import (
    ExecutableJob,
    Worker,
    bind_fd,
    bind_fh,
    BoundJob,
    ContextResolver,
    WorkSurface,
    module_to_executable_jobs,
)
from .convergence import convergence_from_precomputed, outcomes_from_precomputed, unresolved_fraction
from .correction import find_latest_reset
from .events import EventStream
from .interpret import (
    Traversal,
    TraversalRuntime,
    traverse,
)
from .lineage import WorkInstance, _discover_children, active_work_keys
from .provenance import req_hash, executable_job_hash, job_evaluator_hash, _read_workflow_version
from .selection import (
    resolve_candidate_family,
    resolve_refinement_boundary,
    validate_module_selection_surface,
    validate_module_traversal_surface,
)


# ── Workflow provenance helpers ───────────────────────────────────────────────

def _read_carry_forward(scope: "Scope") -> list[dict]:
    """
    Read approved_carry_forward from the variant manifest.json.

    Path: {workflow_root}/{pkg}/{variant}/{version}/manifest.json
    where workflow "my_domain.standard@0.2.0" → pkg="my_domain",
    variant="standard", version="0.2.0".

    When scope.workflow_root is set (from genesis.yml runtime contract), it is
    used as the base directory. Otherwise falls back to .genesis/workflows/.

    Returns [] if workflow_version is "unknown", file absent, or key missing.
    """
    if scope.workflow_version == "unknown":
        return []
    workflow, version = scope.workflow_version.split("@", 1)
    parts = workflow.split(".", 1)
    pkg_name = parts[0]
    variant = parts[1] if len(parts) > 1 else "default"
    version_dir = "v" + version.replace(".", "_")
    if scope.workflow_root:
        wf_base = (scope.workspace_root / scope.workflow_root).resolve()
    else:
        wf_base = scope.workspace_root / ".genesis" / "workflows"
    manifest_path = (
        wf_base / pkg_name / variant / version_dir / "manifest.json"
    )
    try:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        cf = data.get("approved_carry_forward", [])
        return cf if isinstance(cf, list) else []
    except Exception:
        return []


# ── Scope ─────────────────────────────────────────────────────────────────────

@dataclass
class Scope:
    """
    First-class scope object. Every command requires one. No ambient inference.

    Ambiguous scope fails closed — the command returns an error describing the
    available scopes rather than guessing. See ADR-004.

    module: Module — the authoritative entry point. ExecutableJobs and Worker are
        derived directly from Module via module_to_executable_jobs().

    workflow_version: derived at construction from active-workflow.json.
        "{workflow}@{version}" when file present and valid; "unknown" otherwise.
        When "unknown", provenance checks are bypassed.

    Build identifier is build-layer specific. This Claude Code build defaults to "claude_code".
    """
    module: Module = None
    workspace_root: Path = field(default_factory=lambda: Path("."))
    work_key_filter: Optional[str] = None   # work_key scope (CLI --feature normalizes here)
    edge_filter: Optional[str] = None       # edge name scope (CLI --edge normalizes here)
    build: str = "claude_code"
    worker: Optional[Worker] = None   # explicit worker; None = derived
    active_workflow_path: Optional[str] = None  # runtime contract: path to active-workflow.json
    workflow_root: Optional[str] = None         # runtime contract: base dir for workflow releases
    work_key: Optional[str] = None    # work identity (ADR-023); None = global scope
    run_id: Optional[str] = None      # attempt identity (ADR-023); None = global scope
    workflow_version: str = field(init=False, default="unknown")

    def __post_init__(self) -> None:
        if self.module is None:
            raise ValueError("Scope requires a Module.")
        validate_module_selection_surface(self.module)
        validate_module_traversal_surface(self.module)

        # Derive Worker from Module's jobs/vectors
        # ADR-030 §5: single-worker build satisfies all declared roles
        if self.worker is None:
            jobs = module_to_executable_jobs(self.module)
            role_ids = tuple(r.id for r in self.module.roles)
            self.worker = Worker(id=self.build, can_execute=jobs, role_ids=role_ids)

        self.workflow_version = _read_workflow_version(
            self.workspace_root, self.active_workflow_path
        )


# ── work_key enumeration ────────────────────────────────────────────────────

# active_work_keys is re-exported from .lineage (imported above).


def _resolve_work_keys(scope: "Scope",
                       stream: Optional["EventStream"] = None) -> list[str]:
    """
    Determine active work_keys for this scope.

    Priority:
    1. scope.work_key set explicitly (CLI override) → [scope.work_key]
    2. scope.work_key_filter set (feature_id IS work_key) → [scope.work_key_filter]
    3. Enumerate from active feature vectors + spawned children
    4. Empty list → global scope (no work_key scoping)
    """
    if scope.work_key is not None:
        return [scope.work_key]
    if scope.work_key_filter is not None:
        return [scope.work_key_filter]
    return active_work_keys(scope.workspace_root, stream)


def _work_key_matches_job(work_key: str | None, job: ExecutableJob) -> bool:
    """
    Return True when a work_key lawfully scopes to the given executable job.

    Spawned child work uses `parent_key/<edge-name>` and must only bind to the
    executable job for that edge. Global/feature keys keep the broader scope.
    """
    if work_key is None:
        return True
    segment = work_key.rsplit("/", 1)[-1]
    if "→" in segment or "↔" in segment:
        return segment == job.vector.name
    return True


# ── gen_gaps — bind_fd over scope ─────────────────────────────────────────────

def gen_gaps(scope: Scope, stream: EventStream) -> dict:
    """
    /gen-gaps = bind_fd over selected jobs → return delta_summary fields.

    Requires explicit Scope — fails closed on ambiguity.
    Runs bind_fd only (no F_P dispatch).

    Returns: jobs considered, failing evaluators per job, total delta.
    """
    stream.workflow_version = scope.workflow_version
    resolver = ContextResolver(scope.workspace_root)
    worker = _resolve_worker(scope)
    jobs = _scoped_jobs(scope, worker)

    if not jobs:
        return {
            "status": "error",
            "reason": "no jobs in scope — check --feature and --edge flags",
        }

    # Pre-compute which (edge, work_key) tuples already have a well-formed certificate.
    # REQ-F-CMD-004: deduplication keyed on (edge, work_key).
    # ADR-026: certificates predating the latest applicable reset are stale —
    # they don't satisfy live convergence queries and must be re-earned.
    all_events = stream.all_events()
    certified_keys: set[tuple] = set()
    for e in all_events:
        if e.get("event_type") == "edge_converged" and e.get("data", {}).get("target"):
            ed = e["data"]
            cert_wk = ed.get("work_key")
            # ADR-026: check if this certificate predates the latest applicable reset
            reset = find_latest_reset(all_events, edge=ed.get("edge"), work_key=ed.get("work_key"))
            if reset and e.get("event_time", "") <= reset.get("event_time", ""):
                continue  # Stale certificate — shadowed by reset boundary
            certified_keys.add((ed["edge"], cert_wk))

    carry_forward = _read_carry_forward(scope)
    resolver = ContextResolver(scope.workspace_root)

    # Enumerate work_keys: explicit override, feature-derived, or global scope [None].
    work_keys = _resolve_work_keys(scope, stream)
    work_key_list = work_keys if work_keys else [None]

    results = []
    for job in jobs:
        if scope.workflow_version == "unknown":
            spec_hash = req_hash(scope.module.metadata.get("requirements", []))
        else:
            spec_hash = job_evaluator_hash(job)
        for wk in work_key_list:
            if not _work_key_matches_job(wk, job):
                continue
            # Set stream identity for any events emitted under this work_key
            stream.work_key = wk
            pre = bind_fd(
                job, stream, resolver, scope.workspace_root,
                spec_hash=spec_hash,
                current_workflow_version=scope.workflow_version,
                carry_forward=carry_forward,
                work_key=wk,
            )
            outcomes = outcomes_from_precomputed(job.vector.id, pre)
            d = unresolved_fraction(outcomes)
            entry: dict = {
                "edge": job.vector.name,
                "delta": d,
                "failing": [ev.name for ev in pre.failing_evaluators],
                "passing": [ev.name for ev in pre.passing_evaluators],
                "delta_summary": pre.delta_summary,
            }
            if wk is not None:
                entry["work_key"] = wk
            results.append(entry)
            # Emit edge_converged when freshly confirmed delta=0 and not yet certified.
            # Idempotent: once a well-formed certificate exists in the log,
            # repeated gen_gaps calls over a converged workspace do not append duplicates.
            cert_key = wk if wk is not None else scope.work_key_filter
            if d == 0.0 and (job.vector.name, cert_key) not in certified_keys:
                cert: dict = {
                    "edge": job.vector.name,
                    "vector_id": job.vector.id,
                    "target": job.vector.target.name,
                    "work_key": wk or scope.work_key_filter,
                    "delta": 0,
                    "certified_by": "gen_gaps",
                }
                # ADR-027: run_id is auto-injected by EventStream if stream.run_id
                # is set. For gen_gaps, run_id may not be set — that's correct:
                # edge_converged from gen_gaps is a certification, not a run event.
                # run_state() should NOT require edge_converged to carry run_id —
                # convergence is derived from assessed events, not certificates.
                stream.append("edge_converged", cert)
                certified_keys.add((job.vector.name, cert_key))

    total_delta = sum(r["delta"] for r in results)
    scope_info: dict = {
        "package": scope.module.name,
        "work_key_filter": scope.work_key_filter,
        "edge_filter": scope.edge_filter,
        "build": scope.build,
    }
    if work_keys:
        scope_info["work_keys"] = work_keys
    return {
        "scope": scope_info,
        "jobs_considered": len(results),
        "total_delta": total_delta,
        "converged": total_delta == 0,
        "gaps": results,
    }


# ── gen_iterate — bind + iterate once ─────────────────────────────────────────

def gen_iterate(
    scope: Scope,
    stream: EventStream,
    on_fp_dispatch: Optional[Callable[[BoundJob], None]] = None,
) -> dict:
    """
    /gen-iterate = bind one executable job → iterate exactly once.

    The most important command to keep pure.
    One Job. One Asset. One iterate call.
    When work_keys are active, selects the first unconverged (job, work_key) pair.
    """
    stream.workflow_version = scope.workflow_version
    resolver = ContextResolver(scope.workspace_root)
    worker = _resolve_worker(scope)
    jobs = _scoped_jobs(scope, worker)

    if not jobs:
        return {"status": "nothing_to_do", "reason": "no jobs in scope"}

    carry_forward = _read_carry_forward(scope)
    resolver = ContextResolver(scope.workspace_root)

    # Enumerate work_keys: explicit override, feature-derived, or global scope [None].
    work_keys = _resolve_work_keys(scope, stream)
    work_key_list = work_keys if work_keys else [None]

    # Pre-compute selection topology from event stream (ADR-025).
    # refined_parents: work_keys that have children from prior selection — skip.
    # spawned_children: work_keys that were spawned — don't re-select them.
    all_events_snapshot = stream.all_events()
    refined_parents: set[str] = set()
    spawned_children: set[str] = set()
    for e in all_events_snapshot:
        if e.get("event_type") == "work_spawned":
            pk = e.get("data", {}).get("parent_key")
            ck = e.get("data", {}).get("child_key")
            if pk:
                refined_parents.add(pk)
            if ck:
                spawned_children.add(ck)

    # Build WorkInstances — the first-class dispatch unit (ADR-024).
    # Select the first unconverged instance in topological order.
    # Uses typed convergence over the precomputed contract boundary.
    # Refined parents are skipped — their children are in
    # work_key_list and will be selected instead.
    selected_wi: WorkInstance | None = None
    selected_pre = None
    selected_spec_hash = ""
    for job in jobs:
        # ADR-030 §5: conjunctive eligibility — skip jobs this worker cannot realize.
        if not scope.worker.is_eligible(job):
            continue
        if scope.workflow_version == "unknown":
            spec_hash = req_hash(scope.module.metadata.get("requirements", []))
        else:
            spec_hash = job_evaluator_hash(job)
        for wk in work_key_list:
            if not _work_key_matches_job(wk, job):
                continue
            if wk is not None and wk in refined_parents:
                continue  # Delegate to children (fold-back)
            pre = bind_fd(
                job, stream, resolver, scope.workspace_root,
                spec_hash=spec_hash,
                current_workflow_version=scope.workflow_version,
                carry_forward=carry_forward,
                work_key=wk,
            )
            conv = convergence_from_precomputed(job.vector.id, pre)
            if conv.aggregate_state != "closed":
                selected_wi = WorkInstance(executable_job=job, work_key=wk)
                selected_pre = pre
                selected_spec_hash = spec_hash
                break
        if selected_wi is not None:
            break

    if selected_wi is None:
        return {
            "status": "converged",
            "reason": "all jobs in scope have delta = 0",
        }

    family = resolve_candidate_family(scope.module, selected_wi.executable_job.vector.id)
    boundary = resolve_refinement_boundary(scope.module, selected_wi.executable_job.vector.id)
    if family is None and boundary is None:
        raise ValueError(
            "gen_iterate(): no published traversal target for "
            f"vector {selected_wi.executable_job.vector.name!r}"
        )
    if family is not None and boundary is None:
        raise ValueError(
            "gen_iterate(): CandidateFamily traversal requires an explicit "
            f"SelectionDecision for vector {selected_wi.executable_job.vector.name!r}"
        )
    traversal = Traversal(
        work_key=selected_wi.work_key or selected_wi.executable_job.vector.id,
        target=boundary or family,
        evaluators=selected_wi.executable_job.vector.evaluators,
    )
    runtime = TraversalRuntime(
        module=scope.module,
        executable_job=selected_wi.executable_job,
        precomputed=selected_pre,
        workspace_root=scope.workspace_root,
        stream=stream,
        worker=scope.worker,
        spec_hash=selected_spec_hash,
        build=scope.build,
        work_key=selected_wi.work_key,
        workflow_version=scope.workflow_version,
        on_fp_dispatch=on_fp_dispatch,
        run_id=scope.run_id,
    )
    outcome = traverse(traversal, runtime=runtime, surface=WorkSurface())

    if outcome.updated_module is not None:
        scope.module = outcome.updated_module
    if outcome.updated_worker is not None:
        scope.worker = outcome.updated_worker

    return outcome.result


# ── gen_start — state machine ──────────────────────────────────────────────────

def gen_start(
    scope: Scope,
    stream: EventStream,
    auto: bool = False,
    on_fp_dispatch: Optional[Callable[[BoundJob], None]] = None,
) -> dict:
    """
    /gen-start = derive state → select job → traverse.

    State machine: reads workspace, selects the next unconverged job,
    delegates to gen_iterate. In --auto mode, loops until converged or blocked.
    """
    state = _derive_state(scope, stream)

    if state["status"] == "converged":
        _close_completed_features(scope)
        return {
            "status": "converged",
            "message": "All jobs in scope have delta = 0. Run /gen-gaps for full report.",
        }

    if state["status"] == "nothing_to_do":
        return {
            "status": "nothing_to_do",
            "reason": state.get("reason", ""),
        }

    # IN_PROGRESS — dispatch to gen_iterate
    if not auto:
        return gen_iterate(scope, stream, on_fp_dispatch=on_fp_dispatch)

    # --auto: loop until converged, blocked, or max iterations.
    # Stopping conditions come from the typed traversal result, not raw event scans.
    MAX_AUTO = 50
    result: dict = {}

    for _ in range(MAX_AUTO):
        result = gen_iterate(scope, stream, on_fp_dispatch=on_fp_dispatch)
        result["auto"] = True

        if result["status"] in ("converged", "nothing_to_do", "pending"):
            if result.get("blocking_reason"):
                result["stopped_by"] = result["blocking_reason"]
            return result

        blocking_reason = result.get("blocking_reason")
        if blocking_reason is not None:
            result["stopped_by"] = blocking_reason
            return result

    result["stopped_by"] = "max_iterations"
    return result


def _derive_state(scope: Scope, stream: EventStream) -> dict:
    """
    Derive project state from workspace. Never stored — always derived.

    Uses typed convergence checking over precomputed manifests.
    """
    worker = _resolve_worker(scope)
    jobs = _scoped_jobs(scope, worker)

    if not jobs:
        return {"status": "nothing_to_do", "reason": "no jobs in scope"}

    carry_forward = _read_carry_forward(scope)
    resolver = ContextResolver(scope.workspace_root)

    # Enumerate work_keys: explicit override, feature-derived, or global scope [None].
    work_keys = _resolve_work_keys(scope, stream)
    work_key_list = work_keys if work_keys else [None]

    # Build WorkInstances — the first-class dispatch unit (ADR-024).
    instances = [
        WorkInstance(executable_job=job, work_key=wk)
        for job in jobs
        for wk in work_key_list
        if _work_key_matches_job(wk, job)
    ]

    total_delta = 0.0
    for wi in instances:
        if scope.workflow_version == "unknown":
            spec_hash = req_hash(scope.module.metadata.get("requirements", []))
        else:
            spec_hash = executable_job_hash(wi.executable_job)
        pre = bind_fd(
            wi.executable_job,
            stream,
            resolver,
            scope.workspace_root,
            spec_hash=spec_hash,
            current_workflow_version=scope.workflow_version,
            carry_forward=carry_forward,
            work_key=wi.work_key,
        )
        total_delta += unresolved_fraction(
            outcomes_from_precomputed(wi.executable_job.vector.id, pre)
        )

    if total_delta == 0:
        return {"status": "converged"}

    return {"status": "in_progress", "delta": total_delta}


# ── internal helpers ──────────────────────────────────────────────────────────

def _resolve_worker(scope: Scope) -> Worker:
    """
    Resolve the worker for the given scope.

    Domain-blind: scope.worker must be explicitly supplied by the caller.
    The CLI resolves worker from --worker flag or .genesis/genesis.yml.
    """
    if scope.worker is None:
        raise RuntimeError(
            "scope.worker is None — supply worker via Scope(worker=...) "
            "or configure .genesis/genesis.yml (written by gen-install.py)"
        )
    return scope.worker


def _scoped_jobs(scope: Scope, worker: Worker) -> list[Job]:
    """
    Return jobs from worker.can_execute, filtered by scope overrides.

    edge override: exact match on job.vector.name — narrows which jobs run.

    feature override: existence validation only.
      Single-trajectory scope — Jobs are not tagged by feature_id.
      --feature REQ-F-CORE validates that feature exists in the workspace;
      it does not narrow which jobs run (all jobs cover the single trajectory).
      Unknown feature ID → empty list (fails closed; caller reports error).
    """
    jobs = list(worker.can_execute)

    if scope.work_key_filter:
        known = _known_feature_ids(scope.workspace_root)
        if scope.work_key_filter not in known:
            return []  # fail closed — unknown feature

    if scope.edge_filter:
        jobs = [j for j in jobs if j.vector.name == scope.edge_filter]

    return jobs


def _close_completed_features(scope: Scope) -> None:
    """
    Move all active feature YAMLs to features/completed/ and update status field.

    Called by gen_start when it arrives and finds all edges have delta=0 — the
    worker came back, found the work done, closes the ticket.
    """
    active_dir = scope.workspace_root / ".ai-workspace" / "features" / "active"
    completed_dir = scope.workspace_root / ".ai-workspace" / "features" / "completed"
    completed_dir.mkdir(parents=True, exist_ok=True)

    if not active_dir.exists():
        return

    for yml in sorted(active_dir.glob("*.yml")):
        text = yml.read_text(encoding="utf-8")
        # Update status field regardless of current value
        for old_status in ("status: not_started", "status: active", "status: iterating"):
            if old_status in text:
                text = text.replace(old_status, "status: completed", 1)
                break
        (completed_dir / yml.name).write_text(text, encoding="utf-8")
        yml.unlink()


def _known_feature_ids(workspace_root: Path) -> set[str]:
    """Return feature IDs from YAML filenames in .ai-workspace/features/."""
    features_dir = workspace_root / ".ai-workspace" / "features"
    ids: set[str] = set()
    for subdir in ("active", "completed"):
        d = features_dir / subdir
        if d.exists():
            ids.update(f.stem for f in d.glob("*.yml"))
    return ids
