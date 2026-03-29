# Implements: REQ-R-ABG2-INTERPRET
# Implements: REQ-R-ABG2-CONVERGENCE
# Implements: REQ-R-ABG2-SELECTION-APPLICATION
"""
interpret — Graph interpretation loop.

iterate, schedule, apply_selection.

apply_selection owns lawful application of a SelectionDecision:
validate interface, apply substitute(), emit workflow_selected.
Per GTL_2_MODULE_DESIGN §4.4, interpret owns event emission — selection
and subwork are pure kernel modules that return values.
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

from gtl.operator_model import Evaluator, Rule, F_D, F_H, F_P
from gtl.graph import Graph, GraphVector
from gtl.function_model import GraphFunction, RefinementBoundary, CandidateFamily
from gtl.module_model import Module
from gtl.algebra import substitute

from .binding import (
    ExecutableJob,
    Worker,
    BoundJob,
    WorkSurface,
    PrecomputedManifest,
    bind_fp,
    module_to_executable_jobs,
)
from .events import EventStream
from .selection import (
    SelectionDecision,
    accept_selection,
    validate_selection,
)
from .subwork import LeafTask


# ── V2 Traversal ─────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class Traversal:
    """First-class ABG runtime traversal contract.

    Names one runtime traversal attempt over one GTL contract boundary.
    Traversal.metadata is input-side runtime metadata only — no hidden strategy.
    """
    work_key: str
    target: GraphFunction | CandidateFamily | RefinementBoundary
    evaluators: tuple[Evaluator, ...] = ()
    rule: Rule | None = None
    selection: SelectionDecision | None = None
    metadata: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.work_key:
            raise ValueError("Traversal.work_key must be non-empty")
        forbidden = {
            "strategy",
            "candidate_choice",
            "selected_candidate",
            "selection_strategy",
            "refinement_strategy",
        }
        hidden = forbidden & set(self.metadata.keys())
        if hidden:
            raise ValueError(
                f"Traversal.metadata must not carry hidden strategy keys: {sorted(hidden)}"
            )
        if self.selection is not None and not isinstance(self.target, CandidateFamily):
            raise ValueError(
                "Traversal.selection is only valid when target is a CandidateFamily"
            )
        if isinstance(self.target, CandidateFamily) and self.selection is None:
            raise ValueError(
                "Traversal over CandidateFamily requires an explicit SelectionDecision"
            )


@dataclass
class TraversalRuntime:
    """Explicit runtime execution context for a traversal attempt.

    This is an ABG helper shape: services discover the next work item,
    interpret owns the deterministic protocol once that work item is named.
    """
    module: Module
    executable_job: ExecutableJob
    precomputed: PrecomputedManifest
    workspace_root: Path
    stream: EventStream
    worker: Worker
    spec_hash: str
    build: str = "claude_code"
    work_key: str | None = None
    workflow_version: str = "unknown"
    on_fp_dispatch: Optional[Callable[[BoundJob], None]] = None
    leaf_tasks: tuple[LeafTask, ...] = ()
    on_leaf_dispatch: Optional[Callable[[LeafTask, dict], tuple[dict | None, str | None]]] = None
    leaf_task_inputs: dict[str, dict] = field(default_factory=dict)
    run_id: Optional[str] = None


@dataclass(frozen=True)
class TraversalOutcome:
    """Structured result of one traversal attempt."""
    surface: WorkSurface
    result: dict
    updated_module: Module | None = None
    updated_worker: Worker | None = None


def _blocking_reason(pre: PrecomputedManifest) -> str | None:
    """Return the typed blocking reason for one precomputed traversal state."""
    if any(ev.regime is F_P for ev in pre.failing_evaluators):
        return "fp_dispatch"
    if any(ev.regime is F_H for ev in pre.failing_evaluators) and not any(
        ev.regime in (F_D, F_P) for ev in pre.failing_evaluators
    ):
        return "fh_gate"
    if any(ev.regime is F_D for ev in pre.failing_evaluators):
        return "fd_gap"
    return None


def _boundary_inputs(vector: GraphVector) -> tuple:
    return vector.source if isinstance(vector.source, tuple) else (vector.source,)


def _append_events(stream: EventStream, events: tuple[dict, ...] | list[dict]) -> None:
    for event in events:
        stream.append(event["event_type"], event["data"])


def _selection_outcome(
    surface: WorkSurface,
    runtime: TraversalRuntime,
    family: CandidateFamily,
    selection: SelectionDecision,
) -> TraversalOutcome:
    vector = runtime.executable_job.vector
    candidates = family.candidates
    if not candidates:
        raise ValueError(
            f"_selection_outcome(): no candidates available for vector {vector.id!r}"
        )
    matching = [candidate for candidate in candidates if candidate.name == selection.graph_function]
    if len(matching) != 1:
        raise ValueError(
            "_selection_outcome(): SelectionDecision.graph_function must resolve to "
            f"exactly one candidate in family {family.name!r}"
        )
    candidate = matching[0]
    decision = accept_selection(
        family,
        candidate,
        contract_id=selection.contract_id,
        work_key=selection.work_key,
        selected_by=selection.selected_by,
        selection_mode=selection.selection_mode,
        rationale=selection.rationale,
    )
    if decision != selection:
        raise ValueError(
            "_selection_outcome(): explicit SelectionDecision did not validate "
            "against the CandidateFamily contract"
        )
    sel_result = apply_selection(runtime.module, vector.id, decision, candidate)

    containing_graph_id = sel_result.containing_graph_id
    updated_graphs = tuple(
        sel_result.substituted_graph if g.id == containing_graph_id else g
        for g in runtime.module.graphs
    )

    from gtl.work_model import Job as GtlJob, ContractRef

    old_vec_ids = {vec.id for g in runtime.module.graphs for vec in g.vectors}
    new_vec_ids = {vec.id for g in updated_graphs for vec in g.vectors}
    surviving_jobs = tuple(
        j for j in runtime.module.jobs
        if any(ref.target_id in new_vec_ids for ref in j.contracts)
    )
    surviving_jobs_by_vec_id = {
        ref.target_id: job
        for job in surviving_jobs
        for ref in job.contracts
        if ref.kind == "graph_vector"
    }
    parent_roles = runtime.executable_job.job.roles
    ordered_jobs = []
    for graph in updated_graphs:
        for vec in graph.vectors:
            if not vec.evaluators:
                continue
            existing = surviving_jobs_by_vec_id.get(vec.id)
            if existing is not None:
                ordered_jobs.append(existing)
            else:
                ordered_jobs.append(
                    GtlJob(
                        name=vec.name,
                        contracts=(ContractRef(kind="graph_vector", target_id=vec.id),),
                        roles=parent_roles,
                    )
                )
    updated_module = Module(
        name=runtime.module.name,
        graphs=updated_graphs,
        graph_functions=runtime.module.graph_functions,
        refinement_boundaries=runtime.module.refinement_boundaries,
        candidate_families=runtime.module.candidate_families,
        jobs=tuple(ordered_jobs),
        roles=runtime.module.roles,
        operators=runtime.module.operators,
        evaluators=runtime.module.evaluators,
        rules=runtime.module.rules,
        imports=runtime.module.imports,
        metadata=runtime.module.metadata,
    )
    updated_worker = Worker(
        id=runtime.build,
        can_execute=module_to_executable_jobs(updated_module),
        role_ids=tuple(r.id for r in updated_module.roles),
    )

    stream_events: list[dict] = list(sel_result.events)
    contract_edge = runtime.executable_job.vector.name
    for vec_name in sel_result.inner_vectors:
        if runtime.work_key is not None:
            child_key = f"{runtime.work_key}/{vec_name}"
        else:
            child_key = f"{contract_edge}/{sel_result.graph_function}/{vec_name}"
        stream_events.append({
            "event_type": "work_spawned",
            "data": {
                "parent_key": runtime.work_key or "",
                "child_key": child_key,
                "graph_function": sel_result.graph_function,
            },
        })

    _append_events(runtime.stream, stream_events)

    result = {
        "status": "selected",
        "edge": contract_edge,
        "graph_function": sel_result.graph_function,
        "children_spawned": len(sel_result.inner_vectors),
        "reason": (
            f"Edge {contract_edge!r} refined via "
            f"GraphFunction {sel_result.graph_function!r}. Re-enter to dispatch children."
        ),
    }

    next_metadata = dict(surface.metadata)
    next_metadata["traversal_outcome"] = {
        "status": "selected",
        "graph_function": sel_result.graph_function,
        "children_spawned": len(sel_result.inner_vectors),
    }
    return TraversalOutcome(
        surface=WorkSurface(
            events=tuple(stream_events),
            artifacts=surface.artifacts,
            context_consumed=surface.context_consumed,
            context_emitted=surface.context_emitted,
            findings=surface.findings,
            attestations=surface.attestations,
            metadata=next_metadata,
        ),
        result=result,
        updated_module=updated_module,
        updated_worker=updated_worker,
    )


def _iterated_outcome(
    surface: WorkSurface,
    runtime: TraversalRuntime,
) -> TraversalOutcome:
    vector = runtime.executable_job.vector
    pre = runtime.precomputed
    blocking_reason = _blocking_reason(pre)

    fd_failing = [ev for ev in pre.failing_evaluators if ev.regime is F_D]
    fp_failing = [ev for ev in pre.failing_evaluators if ev.regime is F_P]
    fh_failing = [ev for ev in pre.failing_evaluators if ev.regime is F_H]

    run_id = runtime.run_id or str(uuid.uuid4())

    runtime.stream.work_key = runtime.work_key
    runtime.stream.run_id = run_id

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    edge_slug = vector.name.replace("→", "_").replace("↔", "_")
    manifest_id = f"{edge_slug}_{ts}"

    from .run import find_pending_run

    if fp_failing:
        pending = find_pending_run(
            runtime.stream.all_events(),
            vector.name,
            work_key=runtime.work_key,
        )
        if pending is not None:
            result = {
                "status": "pending",
                "reason": f"F_P dispatch already in flight for edge {vector.name!r}",
                "pending_run_id": pending.run_id,
                "edge": vector.name,
                "blocking_reason": "fp_dispatch",
            }
            next_metadata = dict(surface.metadata)
            next_metadata["traversal_outcome"] = {
                "status": "pending",
                "pending_run_id": pending.run_id,
                "blocking_reason": "fp_dispatch",
            }
            return TraversalOutcome(
                surface=WorkSurface(
                    events=surface.events,
                    artifacts=surface.artifacts,
                    context_consumed=surface.context_consumed,
                    context_emitted=surface.context_emitted,
                    findings=surface.findings,
                    attestations=surface.attestations,
                    metadata=next_metadata,
                ),
                result=result,
            )

    result_path = ""
    if fp_failing:
        fp_results_dir = runtime.workspace_root / ".ai-workspace" / "fp_results"
        fp_results_dir.mkdir(parents=True, exist_ok=True)
        result_path = str(fp_results_dir / f"{manifest_id}.json")

    run_bound_data: dict = {
        "edge": vector.name,
        "vector_id": vector.id,
        "run_id": run_id,
        "job_id": runtime.executable_job.job.id,
        "worker_id": runtime.worker.id,
    }
    if runtime.executable_job.job.roles:
        run_bound_data["role_id"] = runtime.executable_job.job.roles[0].id
    if runtime.worker.authority_ref:
        run_bound_data["authority_ref"] = runtime.worker.authority_ref
    if runtime.work_key is not None:
        run_bound_data["work_key"] = runtime.work_key
    runtime.stream.append("run_bound", run_bound_data)

    run_started_data: dict = {
        "edge": vector.name,
        "vector_id": vector.id,
        "run_id": run_id,
        "job_id": runtime.executable_job.job.id,
        "worker_id": runtime.worker.id,
    }
    if runtime.work_key is not None:
        run_started_data["work_key"] = runtime.work_key
    runtime.stream.append("run_started", run_started_data)

    bound = bind_fp(pre, runtime.executable_job, result_path=result_path)
    bound.manifest_id = manifest_id

    edge_started_data: dict = {
        "edge": vector.name,
        "vector_id": vector.id,
        "build": runtime.build,
        "target": vector.target.name,
    }
    if runtime.work_key is not None:
        edge_started_data["work_key"] = runtime.work_key
    runtime.stream.append("edge_started", edge_started_data)

    iter_surface = _realize_iteration(
        bound,
        on_fp_dispatch=runtime.on_fp_dispatch,
        leaf_tasks=list(runtime.leaf_tasks) if runtime.leaf_tasks else None,
        on_leaf_dispatch=runtime.on_leaf_dispatch,
        leaf_task_inputs=runtime.leaf_task_inputs,
        run_id=run_id,
    )
    _append_events(runtime.stream, iter_surface.events)

    result: dict = {
        "status": "iterated",
        "edge": vector.name,
        "delta_before": pre.delta,
        "failing_evaluators": [ev.name for ev in pre.failing_evaluators],
        "events_emitted": len(iter_surface.events) + 3,
        "prompt_words": len(bound.prompt.split()),
        "surface_artifacts": iter_surface.artifacts,
        "context_consumed": [c.name for c in iter_surface.context_consumed],
        "run_id": run_id,
    }
    if blocking_reason is not None:
        result["blocking_reason"] = blocking_reason
    if runtime.work_key is not None:
        result["work_key"] = runtime.work_key

    if fp_failing:
        manifests_dir = runtime.workspace_root / ".ai-workspace" / "fp_manifests"
        manifests_dir.mkdir(parents=True, exist_ok=True)
        manifest_file = manifests_dir / f"{manifest_id}.json"

        src = vector.source
        if isinstance(src, tuple):
            source_asset = [a.name for a in src]
            source_markov = {a.name: a.markov for a in src}
        else:
            source_asset = src.name
            source_markov = {src.name: src.markov}

        contexts = []
        for ctx in vector.contexts:
            ctx_entry: dict = {
                "name": ctx.name,
                "locator": ctx.locator,
                "digest": ctx.digest,
            }
            if ctx.name in pre.relevant_contexts:
                ctx_entry["content"] = pre.relevant_contexts[ctx.name]
            contexts.append(ctx_entry)

        manifest: dict = {
            "manifest_id": manifest_id,
            "edge": vector.name,
            "source_asset": source_asset,
            "target_asset": vector.target.name,
            "source_markov": source_markov,
            "target_markov": vector.target.markov,
            "failing_evaluators": [
                {
                    "name": ev.name,
                    "regime": ev.regime.__name__,
                    "description": ev.description,
                }
                for ev in fp_failing
            ],
            "fd_results": pre.fd_results,
            "delta": pre.delta,
            "delta_summary": pre.delta_summary,
            "contexts": contexts,
            "current_asset": pre.current_asset,
            "prompt": bound.prompt,
            "result_path": result_path,
            "spec_hash": runtime.spec_hash,
            "requirements": runtime.module.metadata.get("requirements", []),
            "run_id": run_id,
        }
        if runtime.work_key is not None:
            manifest["work_key"] = runtime.work_key
        manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        result["fp_manifest_path"] = str(manifest_file)

    if fh_failing:
        result["fh_gate"] = {
            "edge": vector.name,
            "evaluators": [ev.name for ev in fh_failing],
            "criteria": [ev.description for ev in fh_failing],
        }

    next_metadata = dict(iter_surface.metadata)
    next_metadata.update(surface.metadata)
    next_metadata["traversal_outcome"] = {
        "status": result["status"],
        "run_id": run_id,
    }
    if blocking_reason is not None:
        next_metadata["traversal_outcome"]["blocking_reason"] = blocking_reason
    return TraversalOutcome(
        surface=WorkSurface(
            events=iter_surface.events,
            artifacts=iter_surface.artifacts,
            context_consumed=iter_surface.context_consumed,
            context_emitted=iter_surface.context_emitted,
            findings=iter_surface.findings,
            attestations=iter_surface.attestations,
            metadata=next_metadata,
        ),
        result=result,
    )


def _stamp_traversal_surface(
    traversal: Traversal,
    *,
    surface: WorkSurface,
) -> WorkSurface:
    """Stamp traversal identity onto a surface without altering execution truth."""
    next_metadata = dict(surface.metadata)
    next_metadata["traversal"] = {
        "work_key": traversal.work_key,
        "target_name": traversal.target.name,
        "target_kind": type(traversal.target).__name__,
        "evaluators": tuple(ev.name for ev in traversal.evaluators),
        "rule": traversal.rule.name if traversal.rule is not None else None,
    }
    if traversal.metadata:
        next_metadata["traversal_input"] = dict(traversal.metadata)

    base_surface = WorkSurface(
        events=surface.events,
        artifacts=surface.artifacts,
        context_consumed=surface.context_consumed,
        context_emitted=surface.context_emitted,
        findings=surface.findings,
        attestations=surface.attestations,
        metadata=next_metadata,
    )
    return base_surface


def traverse(
    traversal: Traversal,
    *,
    runtime: TraversalRuntime,
    surface: WorkSurface | None = None,
) -> TraversalOutcome:
    """Execute one named traversal attempt through the ABG runtime seam."""
    base_surface = _stamp_traversal_surface(traversal, surface=surface or WorkSurface())
    boundary_inputs = tuple(traversal.target.inputs)
    boundary_outputs = tuple(traversal.target.outputs)
    job_inputs = _boundary_inputs(runtime.executable_job.vector)
    job_outputs = (runtime.executable_job.vector.target,)
    if boundary_inputs != job_inputs or boundary_outputs != job_outputs:
        raise ValueError("traverse(): target boundary does not match executable job contract")

    if isinstance(traversal.target, CandidateFamily):
        return _selection_outcome(base_surface, runtime, traversal.target, traversal.selection)

    return _iterated_outcome(base_surface, runtime)


# ── iteration realization ────────────────────────────────────────────────────


def _realize_iteration(
    bound_job: BoundJob,
    on_fp_dispatch: Optional[Callable[[BoundJob], None]] = None,
    leaf_tasks: Optional[list[LeafTask]] = None,
    on_leaf_dispatch: Optional[Callable[[LeafTask, dict], tuple[dict | None, str | None]]] = None,
    run_id: Optional[str] = None,
    leaf_task_inputs: Optional[dict[str, dict]] = None,
) -> WorkSurface:
    """Singular runtime realization path for one bound job.

    This is the execution core used by the traversal seam.
    """
    pre = bound_job.precomputed
    job = bound_job.executable_job

    events: list[dict] = []
    artifacts: list[str] = []

    fd_failing = [ev for ev in pre.failing_evaluators if ev.regime is F_D]
    fp_failing = [ev for ev in pre.failing_evaluators if ev.regime is F_P]
    fh_failing = [ev for ev in pre.failing_evaluators if ev.regime is F_H]

    if fd_failing:
        kind = "fd_findings" if fp_failing else "fd_gap"
        events.append({
            "event_type": "found",
            "data": {
                "kind": kind,
                "edge": job.vector.name,
                "failing": [ev.name for ev in fd_failing],
                "delta_summary": pre.delta_summary,
            },
        })

    if fp_failing and leaf_tasks and on_leaf_dispatch:
        parent_run_id = run_id or bound_job.manifest_id or "unknown"
        _leaf_inputs = leaf_task_inputs or {}
        for task in leaf_tasks:
            sub_run_id = f"{parent_run_id}/leaf/{task.name}"
            events.append({
                "event_type": "leaf_task_started",
                "data": {
                    "task": task.name,
                    "run_id": sub_run_id,
                    "parent_run_id": parent_run_id,
                    "edge": job.vector.name,
                },
            })
            input_data = _leaf_inputs.get(task.name, {})
            output, failure_class = on_leaf_dispatch(task, input_data)
            if failure_class is not None:
                events.append({
                    "event_type": "leaf_task_failed",
                    "data": {
                        "task": task.name,
                        "run_id": sub_run_id,
                        "failure_class": failure_class,
                        "edge": job.vector.name,
                    },
                })
            else:
                events.append({
                    "event_type": "leaf_task_completed",
                    "data": {
                        "task": task.name,
                        "run_id": sub_run_id,
                        "edge": job.vector.name,
                    },
                })
                if output:
                    artifacts.append(f"leaf:{task.name}")

    if fp_failing:
        fp_dispatch_data: dict = {
            "edge": job.vector.name,
            "failing_evaluators": [ev.name for ev in fp_failing],
            "prompt_length": len(bound_job.prompt),
            "job_id": job.job.id,
        }
        if run_id:
            fp_dispatch_data["run_id"] = run_id
        if bound_job.manifest_id:
            fp_dispatch_data["manifest_id"] = bound_job.manifest_id
        events.append({
            "event_type": "fp_dispatched",
            "data": fp_dispatch_data,
        })
        if bound_job.manifest_id:
            manifests_dir = ".ai-workspace/fp_manifests"
            artifacts.append(f"{manifests_dir}/{bound_job.manifest_id}.json")
        if bound_job.result_path:
            artifacts.append(bound_job.result_path)
        if on_fp_dispatch is not None:
            on_fp_dispatch(bound_job)

    if fh_failing and not fd_failing and not fp_failing:
        events.append({
            "event_type": "fh_gate_pending",
            "data": {
                "edge": job.vector.name,
                "evaluators": [ev.name for ev in fh_failing],
                "criteria": [ev.description for ev in fh_failing],
            },
        })

    return WorkSurface(
        events=tuple(events),
        artifacts=tuple(artifacts),
        context_consumed=tuple(job.vector.contexts),
    )


# ── schedule ──────────────────────────────────────────────────────────────────

def schedule(workers: list[Worker]) -> list[list[Worker]]:
    """Partition workers into parallel-safe execution batches."""
    if not workers:
        return []

    batches: list[list[Worker]] = []
    remaining = list(workers)

    while remaining:
        batch = [remaining[0]]
        still_remaining = []

        for w in remaining[1:]:
            if not any(w.conflicts_with(b) for b in batch):
                batch.append(w)
            else:
                still_remaining.append(w)

        batches.append(batch)
        remaining = still_remaining

    return batches


# ── apply_selection — lawful application of a SelectionDecision ───────────

@dataclass
class SelectionResult:
    """Outcome of apply_selection — the substituted graph and provenance."""
    graph_function: str
    substituted_graph: Graph
    containing_graph_id: str  # REQ-L-GTL2-IDENTITY-007: id of the graph being replaced
    inner_vectors: list[str]
    events: list[dict]


def apply_selection(
    module: Module,
    vector_id: str,
    decision: SelectionDecision,
    candidate: GraphFunction,
) -> SelectionResult:
    """
    Lawful application of a SelectionDecision.

    vector_id: the .id of the target vector (REQ-L-GTL2-IDENTITY-006).

    REQ-R-ABG2-SELECTION-APPLICATION-002: accept external selection, apply it.
    REQ-R-ABG2-SELECTION-APPLICATION-003: record provenance via workflow_selected.
    REQ-R-ABG2-SELECTION-APPLICATION-004: validate interface before application.

    Per GTL_2_MODULE_DESIGN §4.4: interpret owns event emission.
    selection.py is pure — it returns values. This function emits events.

    Returns SelectionResult with the substituted graph — the caller is
    responsible for persisting the new topology (e.g., rebuilding Jobs
    from the updated Module via module_to_jobs).

    Raises ValueError if the selection fails validation or the candidate
    template is not materializable.
    """
    # Find the vector and its containing graph — by id (REQ-L-GTL2-IDENTITY-006)
    target_vec = None
    containing_graph = None
    for graph in module.graphs:
        for vec in graph.vectors:
            if vec.id == vector_id:
                target_vec = vec
                containing_graph = graph
                break
        if target_vec is not None:
            break

    if target_vec is None or containing_graph is None:
        raise ValueError(
            f"apply_selection: vector id {vector_id!r} not found in module {module.name!r}"
        )

    # REQ-R-ABG2-SELECTION-APPLICATION-004: validate before application
    if not validate_selection(decision, candidate, target_vec):
        raise ValueError(
            f"apply_selection: selection {decision.graph_function!r} does not "
            f"satisfy contract for vector id {vector_id!r}"
        )

    # Materialize the candidate's inner graph
    if not callable(candidate.template):
        raise ValueError(
            f"apply_selection: candidate {candidate.name!r} template is not callable"
        )
    inner_graph = candidate.template()

    # Apply substitute() by vector id (REQ-L-GTL2-IDENTITY-006)
    substituted = substitute(containing_graph, target_vec.id, inner_graph)

    # REQ-R-ABG2-SELECTION-APPLICATION-003: provenance event
    inner_vector_names = [v.name for v in inner_graph.vectors]
    events = [{
        "event_type": "workflow_selected",
        "data": {
            "edge": target_vec.name,
            "graph_function": decision.graph_function,
            "selected_by": decision.selected_by,
            "selection_mode": decision.selection_mode,
            "rationale": decision.rationale,
            "work_key": decision.work_key,
            "inner_vectors": inner_vector_names,
        },
    }]

    return SelectionResult(
        graph_function=decision.graph_function,
        substituted_graph=substituted,
        containing_graph_id=containing_graph.id,
        inner_vectors=inner_vector_names,
        events=events,
    )
