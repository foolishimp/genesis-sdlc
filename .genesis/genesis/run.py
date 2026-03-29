# Implements: REQ-R-ABG2-RUN
"""
run — Execution attempt governance.

RunState, run_state, find_pending_run, supersede_run.
"""
from __future__ import annotations

from dataclasses import dataclass


# Valid run states (ADR-027)
RUN_STATES = frozenset({
    "queued", "started", "dispatched", "pending",
    "assessed", "failed", "timed_out", "superseded",
})

# Failure classifications (ADR-027 REQ-F-RUN-002)
FAILURE_CLASSES = frozenset({
    "transport_failure", "no_output", "bad_output", "certification_failure",
})


@dataclass(frozen=True)
class RunState:
    """
    Derived state of a single run attempt.

    ADR-027 REQ-F-RUN-001: state derived entirely from events — no mutable state.
    ADR-030: extended with binding identity fields.
    """
    work_key: str | None
    run_id: str
    edge: str
    state: str  # one of RUN_STATES
    vector_id: str | None = None         # operational handle (REQ-L-GTL2-IDENTITY)
    job_id: str | None = None           # GTL job identity (REQ-R-ABG2-RUN-006)
    worker_id: str | None = None        # bound worker (REQ-R-ABG2-RUN-007)
    role_id: str | None = None          # bound role (REQ-R-ABG2-RUN-007)
    authority_ref: str | None = None    # external authority (REQ-R-ABG2-RUN-008)
    failure_class: str | None = None
    attempt_number: int = 1
    superseded_by: str | None = None


def run_state(
    all_events: list[dict],
    run_id: str,
) -> RunState | None:
    """
    Derive current RunState for a given run_id by replaying events.

    Returns None if no events reference this run_id.
    """
    state = None
    work_key = None
    edge = None
    vector_id = None
    job_id = None
    worker_id = None
    role_id = None
    authority_ref = None
    failure_class = None
    attempt_number = 1
    superseded_by = None

    for e in all_events:
        etype = e.get("event_type")
        edata = e.get("data", {})
        erun = edata.get("run_id")

        if erun != run_id:
            if etype == "run_superseded" and edata.get("superseded_run_id") == run_id:
                state = "superseded"
                superseded_by = edata.get("superseded_by")
            continue

        if etype == "run_bound":
            # ADR-030 §10: run_bound is the authoritative binding event.
            # It carries the full binding identity but does NOT change
            # lifecycle state — it is a binding fact, not a state.
            work_key = edata.get("work_key", work_key)
            edge = edata.get("edge", edge)
            vector_id = edata.get("vector_id", vector_id)
            job_id = edata.get("job_id", job_id)
            worker_id = edata.get("worker_id", worker_id)
            role_id = edata.get("role_id", role_id)
            authority_ref = edata.get("authority_ref", authority_ref)

        elif etype == "run_queued":
            # ADR-030 §10: transport-separated runtimes emit run_queued.
            # Local inline runtimes skip directly to run_started.
            state = "queued"
            work_key = edata.get("work_key", work_key)
            edge = edata.get("edge", edge)

        elif etype == "run_pending":
            # ADR-030 §10: run accepted by scheduler, awaiting start.
            state = "pending"
            work_key = edata.get("work_key", work_key)
            edge = edata.get("edge", edge)

        elif etype == "run_started":
            state = "started"
            work_key = edata.get("work_key", work_key)
            edge = edata.get("edge", edge)
            attempt_number = edata.get("attempt_number", attempt_number)
            # run_started may carry identity fields for backwards compat,
            # but run_bound is authoritative when present.
            job_id = edata.get("job_id", job_id)
            worker_id = edata.get("worker_id", worker_id)

        elif etype == "fp_dispatched":
            state = "dispatched"
            edge = edata.get("edge", edge)

        elif etype == "assessed":
            state = "assessed"
            edge = edata.get("edge", edge)

        elif etype == "run_failed":
            state = "failed"
            failure_class = edata.get("failure_class")

        elif etype == "run_timed_out":
            state = "timed_out"

    if state is None:
        return None

    return RunState(
        work_key=work_key,
        run_id=run_id,
        edge=edge or "",
        state=state,
        vector_id=vector_id,
        job_id=job_id,
        worker_id=worker_id,
        role_id=role_id,
        authority_ref=authority_ref,
        failure_class=failure_class,
        attempt_number=attempt_number,
        superseded_by=superseded_by,
    )


def find_pending_run(
    all_events: list[dict],
    edge_name: str,
    *,
    work_key: str | None = None,
) -> RunState | None:
    """
    Find an active (queued/pending/started/dispatched) run for this (edge, work_key).

    ADR-027 REQ-F-RUN-003: at most one run in an active state
    per (work_key, edge).
    """
    candidate_run_ids: list[str] = []
    for e in all_events:
        edata = e.get("data", {})
        erun = edata.get("run_id")
        if not erun:
            continue
        evt_edge = edata.get("edge")
        if evt_edge != edge_name:
            continue
        evt_wk = edata.get("work_key")
        if work_key is not None:
            if evt_wk != work_key:
                continue
        elif evt_wk is not None:
            continue
        if erun not in candidate_run_ids:
            candidate_run_ids.append(erun)

    for rid in reversed(candidate_run_ids):
        rs = run_state(all_events, rid)
        if rs is not None and rs.state in ("queued", "pending", "started", "dispatched"):
            return rs

    return None


def supersede_run(
    old_run_id: str,
    new_run_id: str,
    edge: str,
    work_key: str | None = None,
) -> dict:
    """Construct a run_superseded event for the caller to emit."""
    data: dict = {
        "superseded_run_id": old_run_id,
        "superseded_by": new_run_id,
        "edge": edge,
    }
    if work_key is not None:
        data["work_key"] = work_key
    return {
        "event_type": "run_superseded",
        "data": data,
    }
