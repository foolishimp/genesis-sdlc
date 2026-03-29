# Implements: REQ-R-ABG2-CONVERGENCE
"""
convergence — Delta computation and convergence visibility.

Protocol types: EvaluatorOutcome, ConvergenceResult, delta (vector-capable).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Optional

from gtl.operator_model import Evaluator, Regime, Rule, F_D, F_H, F_P

from .binding import ContextResolver, PrecomputedManifest, bind_fd
from .events import EventStream
from .lineage import _discover_children
from .projection import project


# ── V2 Protocol Types ────────────────────────────────────────────────────────


@dataclass(frozen=True)
class EvaluatorOutcome:
    """One outcome per evaluator invocation over one contract boundary in one round.

    Carries no domain semantics beyond normalized status.
    REQ-R-ABG2-PROVENANCE-005: per-evaluator identity, regime, and outcome.
    """
    contract_id: str
    evaluator_name: str
    regime: type[Regime]
    status: Literal["pass", "fail", "open", "error"]
    round_index: int
    rationale: str = ""
    payload_ref: str | None = None


@dataclass(frozen=True)
class ConvergenceResult:
    """Aggregate protocol result over one round or one evaluator-result vector.

    aggregate_state is determined from declared rule/evaluator surface,
    never hidden domain logic.
    REQ-R-ABG2-CONVERGENCE-007: vector convergence support.
    REQ-R-ABG2-CONVERGENCE-008: declared ordering and escalation policy.
    """
    contract_id: str
    outcomes: tuple[EvaluatorOutcome, ...]
    aggregate_state: Literal["closed", "open", "error"]
    next_action: Literal["continue", "repeat_round", "escalate", "fail"]
    next_regime: type[Regime] | None
    round_index: int


# ── Regime ordering for escalation ───────────────────────────────────────────

_REGIME_ORDER = {F_D: 0, F_P: 1, F_H: 2}
_REGIME_ESCALATION = {F_D: F_P, F_P: F_H}


def _next_regime(current: type[Regime]) -> type[Regime] | None:
    """Return the next escalation regime, or None if already at F_H."""
    return _REGIME_ESCALATION.get(current)


def outcomes_from_precomputed(
    contract_id: str,
    precomputed: PrecomputedManifest,
    *,
    round_index: int = 0,
) -> tuple[EvaluatorOutcome, ...]:
    """Convert one precomputed manifest into typed evaluator outcomes.

    This is the singular assessment basis for the Claude build runtime.
    """
    outcomes: list[EvaluatorOutcome] = []
    passing = {ev.name for ev in precomputed.passing_evaluators}
    failing = {ev.name for ev in precomputed.failing_evaluators}

    for ev in precomputed.executable_job.evaluators:
        if ev.name in passing:
            status: Literal["pass", "fail", "open", "error"] = "pass"
        elif ev.name in failing:
            status = "fail" if ev.regime is F_D else "open"
        else:
            status = "error"
        outcomes.append(
            EvaluatorOutcome(
                contract_id=contract_id,
                evaluator_name=ev.name,
                regime=ev.regime,
                status=status,
                round_index=round_index,
            )
        )
    return tuple(outcomes)


def unresolved_fraction(outcomes: tuple[EvaluatorOutcome, ...]) -> float:
    """Legacy convergence score derived from typed evaluator outcomes."""
    if not outcomes:
        return 0.0
    unresolved = sum(1 for o in outcomes if o.status != "pass")
    return unresolved / len(outcomes)


def convergence_from_precomputed(
    contract_id: str,
    precomputed: PrecomputedManifest,
    *,
    round_index: int = 0,
) -> ConvergenceResult:
    """Engine-facing convergence result over one precomputed contract boundary.

    This preserves the existing ABG regime frontier semantics while using
    typed evaluator outcomes as the canonical assessment surface.
    """
    outcomes = outcomes_from_precomputed(contract_id, precomputed, round_index=round_index)
    failing = precomputed.failing_evaluators
    if not failing:
        return ConvergenceResult(
            contract_id=contract_id,
            outcomes=outcomes,
            aggregate_state="closed",
            next_action="continue",
            next_regime=None,
            round_index=round_index,
        )

    failing_regimes = {ev.regime for ev in failing}
    if F_D in failing_regimes:
        next_regime = F_P if any(ev.regime is F_P for ev in precomputed.executable_job.evaluators) else None
        return ConvergenceResult(
            contract_id=contract_id,
            outcomes=outcomes,
            aggregate_state="open",
            next_action="continue" if next_regime is not None else "fail",
            next_regime=next_regime,
            round_index=round_index,
        )
    if F_P in failing_regimes:
        return ConvergenceResult(
            contract_id=contract_id,
            outcomes=outcomes,
            aggregate_state="open",
            next_action="continue",
            next_regime=None,
            round_index=round_index,
        )
    return ConvergenceResult(
        contract_id=contract_id,
        outcomes=outcomes,
        aggregate_state="open",
        next_action="continue",
        next_regime=None,
        round_index=round_index,
    )


# ── V2 delta (vector-capable) ────────────────────────────────────────────────


def delta(
    contract_id: str,
    outcomes: tuple[EvaluatorOutcome, ...],
    *,
    rule: Rule | None = None,
) -> ConvergenceResult:
    """Deterministically aggregate one evaluator or evaluator-result vector.

    Uses declared Rule.config for quorum when present.
    Defaults to all-pass only when no explicit aggregation policy is declared.
    Must not invent domain scoring or merge semantics.
    """
    if not outcomes:
        raise ValueError("delta(): empty outcomes")

    # Validate all outcomes share contract_id
    for o in outcomes:
        if o.contract_id != contract_id:
            raise ValueError(
                f"delta(): mixed contract_id — expected {contract_id!r}, "
                f"got {o.contract_id!r}"
            )

    round_index = max(o.round_index for o in outcomes)

    # Error propagation
    errors = [o for o in outcomes if o.status == "error"]
    if errors:
        return ConvergenceResult(
            contract_id=contract_id,
            outcomes=outcomes,
            aggregate_state="error",
            next_action="fail",
            next_regime=None,
            round_index=round_index,
        )

    passes = sum(1 for o in outcomes if o.status == "pass")
    total = len(outcomes)

    # Determine quorum threshold
    if rule and "quorum" in rule.config:
        quorum = rule.config["quorum"]
        if not isinstance(quorum, int) or quorum <= 0 or quorum > total:
            raise ValueError(
                f"delta(): invalid or contradictory rule config quorum={quorum!r} "
                f"for total outcomes={total}"
            )
    else:
        quorum = total  # default: all must pass

    if passes >= quorum:
        return ConvergenceResult(
            contract_id=contract_id,
            outcomes=outcomes,
            aggregate_state="closed",
            next_action="continue",
            next_regime=None,
            round_index=round_index,
        )

    # Not closed — determine next action
    # Check if escalation is needed (open status at a regime with higher available)
    open_outcomes = [o for o in outcomes if o.status == "open"]
    if open_outcomes:
        highest_open = max(open_outcomes, key=lambda o: _REGIME_ORDER.get(o.regime, 0))
        next_r = _next_regime(highest_open.regime)
        if next_r is not None:
            return ConvergenceResult(
                contract_id=contract_id,
                outcomes=outcomes,
                aggregate_state="open",
                next_action="escalate",
                next_regime=next_r,
                round_index=round_index,
            )

    # Quorum not met, no escalation possible — repeat round if rule allows
    if rule and rule.config.get("quorum"):
        return ConvergenceResult(
            contract_id=contract_id,
            outcomes=outcomes,
            aggregate_state="open",
            next_action="repeat_round",
            next_regime=None,
            round_index=round_index,
        )

    # Default: open, escalate to next regime if any non-pass exists
    failing = [o for o in outcomes if o.status == "fail"]
    if failing:
        highest_fail = max(failing, key=lambda o: _REGIME_ORDER.get(o.regime, 0))
        next_r = _next_regime(highest_fail.regime)
        if next_r is not None:
            return ConvergenceResult(
                contract_id=contract_id,
                outcomes=outcomes,
                aggregate_state="open",
                next_action="escalate",
                next_regime=next_r,
                round_index=round_index,
            )

    return ConvergenceResult(
        contract_id=contract_id,
        outcomes=outcomes,
        aggregate_state="open",
        next_action="fail",
        next_regime=None,
        round_index=round_index,
    )


def parent_converged(
    parent_key: str,
    stream: EventStream,
    jobs: list[Job],
    workspace_root: Path,
    spec_hash: str | None = None,
    current_workflow_version: str = "unknown",
    carry_forward: list[dict] | None = None,
) -> bool:
    """
    Check if a parent work_key is converged by checking all descendants.

    REQ-F-FRAG-004 AC-3/AC-4: parent convergence is a projection
    over all descendant convergence.
    """
    events = stream.all_events()
    child_keys = _discover_children(events, parent_key)

    if not child_keys:
        resolver = ContextResolver(workspace_root)
        for job in jobs:
            precomputed = bind_fd(
                job,
                stream,
                resolver,
                workspace_root,
                spec_hash=spec_hash,
                current_workflow_version=current_workflow_version,
                carry_forward=carry_forward,
                work_key=parent_key,
            )
            d = unresolved_fraction(outcomes_from_precomputed(job.vector.id, precomputed))
            if d > 0:
                return False
        return True

    for ck in child_keys:
        if not parent_converged(ck, stream, jobs, workspace_root,
                                spec_hash, current_workflow_version,
                                carry_forward):
            return False

    return True
