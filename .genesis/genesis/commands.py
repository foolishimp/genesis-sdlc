# Implements: REQ-F-CMD-001
# Implements: REQ-F-CMD-002
# Implements: REQ-F-CMD-003
# Implements: REQ-F-GRAPH-001
# Implements: REQ-F-GRAPH-002
# Implements: REQ-F-EVAL-002
# Implements: REQ-F-VIS-001
"""
commands — gen_start, gen_iterate, gen_gaps, Scope.

Three commands as named compositions of core functions. None introduce new
primitives. Phase 4 of the approved execution plan. See ADR-004 (Scope).

  /gen-gaps    = bind_fd over scope → delta_summary fields
  /gen-iterate = bind one Job → iterate exactly once
  /gen-start   = derive state → select job → bind → iterate
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from gtl.core import Job, Package, Worker

from .bind import bind_fd, bind_fp, req_hash
from .core import ContextResolver, EventStream, project
from .manifest import BoundJob
from .schedule import delta, iterate, schedule


# ── Scope ─────────────────────────────────────────────────────────────────────

@dataclass
class Scope:
    """
    First-class scope object. Every command requires one. No ambient inference.

    Ambiguous scope fails closed — the command returns an error describing the
    available scopes rather than guessing. See ADR-004.

    worker: the Worker that executes jobs in this scope. When provided, the
        command layer is fully domain-blind — no spec import occurs. When None,
        _resolve_worker() falls back to the genesis self-hosting spec import
        (V1 CLI convenience; remove in V2 — callers should always supply worker).

    V1: build is always "claude_code". Multi-tenant deferred to V2.
    """
    package: Package
    workspace_root: Path
    feature: Optional[str] = None     # feature vector ID override (None = all)
    edge: Optional[str] = None        # edge name override (None = topological)
    build: str = "claude_code"
    worker: Optional[Worker] = None   # explicit worker; None = spec-import fallback


# ── gen_gaps — bind_fd over scope ─────────────────────────────────────────────

def gen_gaps(scope: Scope, stream: EventStream) -> dict:
    """
    /gen-gaps = bind_fd over selected jobs → return delta_summary fields.

    Requires explicit Scope — fails closed on ambiguity.
    Runs bind_fd only (no F_P dispatch).

    Returns: jobs considered, failing evaluators per job, total delta.
    """
    resolver = ContextResolver(scope.workspace_root)
    worker = _resolve_worker(scope)
    jobs = _scoped_jobs(scope, worker)

    if not jobs:
        return {
            "status": "error",
            "reason": "no jobs in scope — check --feature and --edge flags",
        }

    # Pre-compute which edges already have a well-formed edge_converged certificate
    # (one that includes 'target' — the canonical schema). Events without 'target'
    # (e.g. hand-emitted Phase C entries) do not count: they cannot serve feature-
    # scoped projection and should be superseded by a properly-formed entry.
    certified_edges: set[str] = {
        e["data"]["edge"]
        for e in stream.all_events()
        if e.get("event_type") == "edge_converged"
        and e.get("data", {}).get("target")
    }

    spec_hash = req_hash(scope.package.requirements)

    results = []
    for job in jobs:
        pre = bind_fd(job, stream, resolver, scope.workspace_root, spec_hash=spec_hash)
        results.append({
            "edge": job.edge.name,
            "delta": pre.delta,
            "failing": [ev.name for ev in pre.failing_evaluators],
            "passing": [ev.name for ev in pre.passing_evaluators],
            "delta_summary": pre.delta_summary,
        })
        # Emit edge_converged when freshly confirmed delta=0 and not yet certified.
        # Idempotent: once a well-formed certificate exists in the log (edge + target),
        # repeated gen_gaps calls over a converged workspace do not append duplicates.
        # feature is included so feature-scoped project() calls can match this event.
        if pre.delta == 0 and job.edge.name not in certified_edges:
            cert: dict = {
                "edge": job.edge.name,
                "target": job.edge.target.name,
                "delta": 0,
                "certified_by": "gen_gaps",
            }
            stream.append("edge_converged", cert)
            certified_edges.add(job.edge.name)  # prevent duplicate within same run

    total_delta = sum(r["delta"] for r in results)
    return {
        "scope": {
            "package": scope.package.name,
            "feature": scope.feature,
            "edge": scope.edge,
            "build": scope.build,
        },
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
    /gen-iterate = bind one Job → iterate exactly once.

    The most important command to keep pure.
    One Job. One Asset. One iterate call.
    """
    resolver = ContextResolver(scope.workspace_root)
    worker = _resolve_worker(scope)
    jobs = _scoped_jobs(scope, worker)

    if not jobs:
        return {"status": "nothing_to_do", "reason": "no jobs in scope"}

    spec_hash = req_hash(scope.package.requirements)

    # Select the first unconverged job in topological order
    selected_job = None
    selected_pre = None
    for job in jobs:
        pre = bind_fd(job, stream, resolver, scope.workspace_root, spec_hash=spec_hash)
        if pre.has_gap:
            selected_job = job
            selected_pre = pre
            break

    if selected_job is None:
        return {
            "status": "converged",
            "reason": "all jobs in scope have delta = 0",
        }

    # Determine result_path for F_P actor output (written before bind_fp)
    from gtl.core import F_P as _F_P, F_H as _F_H
    fp_failing = [ev for ev in selected_pre.failing_evaluators if ev.category is _F_P]
    fh_failing = [ev for ev in selected_pre.failing_evaluators if ev.category is _F_H]

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    edge_slug = selected_job.edge.name.replace("→", "_").replace("↔", "_")

    result_path = ""
    if fp_failing:
        fp_results_dir = scope.workspace_root / ".ai-workspace" / "fp_results"
        fp_results_dir.mkdir(parents=True, exist_ok=True)
        result_path = str(fp_results_dir / f"{edge_slug}_{ts}.json")

    # Bind + iterate
    bound = bind_fp(selected_pre, selected_job, result_path=result_path)
    stream.append("edge_started", {
        "edge": selected_job.edge.name,
        "build": scope.build,
    })

    surface = iterate(bound, on_fp_dispatch=on_fp_dispatch)

    # Emit surface events
    for event in surface.events:
        stream.append(event["event_type"], event["data"])

    result: dict = {
        "status": "iterated",
        "edge": selected_job.edge.name,
        "delta_before": selected_pre.delta,
        "failing_evaluators": [ev.name for ev in selected_pre.failing_evaluators],
        "events_emitted": len(surface.events) + 1,  # +1 for edge_started
        "prompt_words": len(bound.prompt.split()),
    }

    # Write F_P manifest to disk when F_P dispatch is needed.
    # gen-start.md reads fp_manifest_path to get the prompt for MCP dispatch.
    if fp_failing:
        manifests_dir = scope.workspace_root / ".ai-workspace" / "fp_manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = manifests_dir / f"{edge_slug}_{ts}.json"
        manifest = {
            "edge": selected_job.edge.name,
            "failing_evaluators": [
                {"name": ev.name, "description": ev.description}
                for ev in fp_failing
            ],
            "prompt": bound.prompt,
            "result_path": result_path,
            "spec_hash": spec_hash,
        }
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        result["fp_manifest_path"] = str(manifest_file)

    # Include F_H gate criteria so skill can evaluate without extra reads.
    if fh_failing:
        result["fh_gate"] = {
            "edge": selected_job.edge.name,
            "evaluators": [ev.name for ev in fh_failing],
            "criteria": [ev.description for ev in fh_failing],
        }

    return result


# ── gen_start — state machine ──────────────────────────────────────────────────

def gen_start(
    scope: Scope,
    stream: EventStream,
    auto: bool = False,
    on_fp_dispatch: Optional[Callable[[BoundJob], None]] = None,
) -> dict:
    """
    /gen-start = derive state → select job → bind → iterate.

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

    # --auto: loop until converged, F_H gate, F_P dispatch, or max iterations.
    # Stop immediately on F_P dispatch (need actor response) or F_H gate (need human).
    MAX_AUTO = 50
    last_event_count = len(stream.all_events())
    result: dict = {}

    for _ in range(MAX_AUTO):
        result = gen_iterate(scope, stream, on_fp_dispatch=on_fp_dispatch)
        result["auto"] = True

        if result["status"] in ("converged", "nothing_to_do"):
            return result

        # Inspect events emitted by this iteration
        new_events = stream.all_events()[last_event_count:]
        last_event_count += len(new_events)

        # Stop on any condition that cannot auto-resolve without external input.
        new_types = {e["event_type"] for e in new_events}
        if "fp_dispatched" in new_types:
            result["stopped_by"] = "fp_dispatch"
            return result
        if "fh_gate_pending" in new_types:
            result["stopped_by"] = "fh_gate"
            return result
        if "fd_gap_found" in new_types:
            result["stopped_by"] = "fd_gap"
            return result

    result["stopped_by"] = "max_iterations"
    return result


def _derive_state(scope: Scope, stream: EventStream) -> dict:
    """Derive project state from workspace. Never stored — always derived."""
    resolver = ContextResolver(scope.workspace_root)
    worker = _resolve_worker(scope)
    jobs = _scoped_jobs(scope, worker)

    if not jobs:
        return {"status": "nothing_to_do", "reason": "no jobs in scope"}

    spec_hash = req_hash(scope.package.requirements)

    total_delta = 0
    for job in jobs:
        pre = bind_fd(job, stream, resolver, scope.workspace_root, spec_hash=spec_hash)
        total_delta += pre.delta

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

    edge override: exact match on job.edge.name — narrows which jobs run.

    feature override (V1 behaviour): existence validation only.
      V1 has a single trajectory — Jobs are not tagged by feature_id.
      --feature REQ-F-CORE validates that feature exists in the workspace;
      it does not narrow which jobs run (all 5 jobs cover the single trajectory).
      Unknown feature ID → empty list (fails closed; caller reports error).
      Per-job feature routing is a V2 concern when multiple packages coexist.
    """
    jobs = list(worker.can_execute)

    if scope.feature:
        known = _known_feature_ids(scope.workspace_root)
        if scope.feature not in known:
            return []  # fail closed — unknown feature

    if scope.edge:
        jobs = [j for j in jobs if j.edge.name == scope.edge]

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
