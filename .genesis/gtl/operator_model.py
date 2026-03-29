# Implements: REQ-L-GTL2-OPERATOR
# Implements: REQ-L-GTL2-EVALUATOR
# Implements: REQ-L-GTL2-RULE
"""
gtl.operator_model — Effect and convergence declarations.

V2 domain model: Regime base class, frozen Operator/Evaluator/Rule with
the accepted field shapes from the constitutional design.

No external dependencies. Dataclasses + stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field


# ── Regime hierarchy ──────────────────────────────────────────────────────

class Regime:
    """Base class for evaluation/operator regimes."""

class F_D(Regime):
    """Deterministic — zero ambiguity, pass/fail."""

class F_P(Regime):
    """Probabilistic — agent/LLM, bounded ambiguity."""

class F_H(Regime):
    """Human — persistent ambiguity, judgment required."""


# ── Operator (V2) ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Operator:
    """
    Typed effectful action declaration.

    REQ-L-GTL2-OPERATOR-001: frozen, immutable, name/regime/binding/tags.
    Operators perform work. Realization is plugin-dependent.
    """
    name: str
    regime: type[Regime] = F_D
    binding: str = ""            # plugin URI
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        if not issubclass(self.regime, Regime):
            raise TypeError(f"Operator.regime must be a Regime subclass, got {self.regime!r}")


# ── Evaluator (V2) ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class Evaluator:
    """
    Typed convergence / attestation declaration.

    REQ-L-GTL2-EVALUATOR-001: frozen, immutable, name/regime/description/binding/tags.
    REQ-L-GTL2-EVALUATOR-006: description is a human-readable convergence contract.
    Evaluators check or attest convergence. Realization is plugin-dependent.
    """
    name: str
    regime: type[Regime] = F_D
    description: str = ""        # human-readable convergence contract (NODE-006 pattern)
    binding: str = ""            # plugin URI
    tags: tuple[str, ...] = ()

    def __post_init__(self):
        if not issubclass(self.regime, Regime):
            raise TypeError(f"Evaluator.regime must be a Regime subclass, got {self.regime!r}")


# ── Rule (V2) ────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class Rule:
    """
    Declarative constraint — what must hold.

    REQ-L-GTL2-RULE-001: declarative constraint type (consensus, coverage,
    policy, type-consistency, etc.). Rules are passive.
    """
    name: str
    kind: str = "policy"         # "consensus", "coverage", "policy", etc.
    config: dict = field(default_factory=dict)
    tags: tuple[str, ...] = ()
