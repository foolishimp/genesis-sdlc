# Implements: REQ-L-GTL2-MODULE
"""
gtl.module_model — Publication and import boundary.

Module replaces Package as the named, composable unit of GTL declarations.
ModuleImport declares cross-module dependencies.

No external dependencies. Dataclasses + stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from gtl.graph import Graph
from gtl.operator_model import Operator, Evaluator, Rule
from gtl.function_model import GraphFunction, RefinementBoundary, CandidateFamily
from gtl.work_model import Job, Role


@dataclass(frozen=True)
class ModuleImport:
    """Cross-module import declaration."""
    source: str              # module name
    names: tuple[str, ...] = ()  # imported declaration names
    version: str = ""


@dataclass(frozen=True)
class Module:
    """
    Publication boundary — the named, composable unit of GTL declarations.

    Module is a pure declaration boundary;
    runtime concerns (workers, requirements) belong to ABG.

    metadata: mapping visible to policy/evaluator layers
    (REQ-L-GTL2-MODULE-001). Attribute binding is frozen; dict contents
    are conventionally immutable after construction (shallow freeze,
    matching the accepted design in GTL_2_MODULE_DESIGN.md).
    """
    name: str
    graphs: tuple[Graph, ...] = ()
    graph_functions: tuple[GraphFunction, ...] = ()
    refinement_boundaries: tuple[RefinementBoundary, ...] = ()
    candidate_families: tuple[CandidateFamily, ...] = ()
    jobs: tuple[Job, ...] = ()
    roles: tuple[Role, ...] = ()
    operators: tuple[Operator, ...] = ()
    evaluators: tuple[Evaluator, ...] = ()
    rules: tuple[Rule, ...] = ()
    imports: tuple[ModuleImport, ...] = ()
    metadata: dict = field(default_factory=dict)
