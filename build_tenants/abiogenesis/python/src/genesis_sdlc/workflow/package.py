# Implements: REQ-F-CUSTODY-001
# Implements: REQ-F-CUSTODY-002
"""Published module and worker surfaces for the Abiogenesis/Python workflow."""

from __future__ import annotations

from pathlib import Path

from genesis.binding import Worker, module_to_executable_jobs
from gtl.module_model import Module

from .assets import BASE_NODES
from .graph import (
    BASE_EVALUATORS,
    BASE_JOBS,
    BASE_OPERATORS,
    BASE_REFINEMENT_BOUNDARIES,
    BASE_ROLES,
    BASE_RULES,
    workflow_graph,
)
from .requirements import find_requirements_root, load_local_requirements, requirement_manifest
from .transforms import transform_contract_manifest


def instantiate(
    slug: str = "genesis_sdlc",
    requirements: list[str] | None = None,
    requirement_root: Path | None = None,
) -> Module:
    requirement_keys = list(requirements) if requirements is not None else []
    metadata = {
        "slug": slug,
        "requirements": requirement_keys,
        "assets": [node.name for node in BASE_NODES],
        "vectors": [vector.name for vector in workflow_graph.vectors],
    }
    if requirement_root is not None:
        metadata["requirement_root"] = str(requirement_root)
    return Module(
        name=slug,
        graphs=(workflow_graph,),
        refinement_boundaries=BASE_REFINEMENT_BOUNDARIES,
        jobs=BASE_JOBS,
        roles=BASE_ROLES,
        operators=BASE_OPERATORS,
        evaluators=BASE_EVALUATORS,
        rules=BASE_RULES,
        metadata=metadata,
    )


def instantiate_local(slug: str = "genesis_sdlc", start: Path | None = None) -> Module:
    """Explicit self-hosting helper that binds requirements from a local workspace."""
    root = find_requirements_root(start)
    return instantiate(
        slug=slug,
        requirements=load_local_requirements(start),
        requirement_root=root,
    )


def graph_manifest(bound_module: Module | None = None, requirement_root: Path | None = None) -> dict[str, object]:
    active_module = bound_module or module
    root = requirement_root
    if root is None:
        configured_root = active_module.metadata.get("requirement_root")
        if isinstance(configured_root, str) and configured_root:
            root = Path(configured_root)
    return {
        "module": active_module.name,
        "requirements": list(active_module.metadata.get("requirements", [])),
        "requirement_manifest": requirement_manifest(root),
        "graph": workflow_graph.name,
        "asset_count": len(workflow_graph.nodes),
        "vector_count": len(workflow_graph.vectors),
        "assets": [
            {
                "name": node.name,
                "schema": node.schema,
                "markov": list(node.markov),
            }
            for node in workflow_graph.nodes
        ],
        "vectors": [
            {
                "name": vector.name,
                "source": [n.name for n in vector.source]
                if isinstance(vector.source, tuple)
                else [vector.source.name],
                "target": vector.target.name,
                "evaluators": [ev.name for ev in vector.evaluators],
                "transform_contract": transform_contract_manifest(vector.name),
            }
            for vector in workflow_graph.vectors
        ],
    }


module = instantiate()
package = module

worker = Worker(
    id="abiogenesis_python",
    can_execute=module_to_executable_jobs(module),
    role_ids=tuple(role.id for role in BASE_ROLES),
)


def bind_requirements(requirements: list[str]) -> Module:
    """Return a module whose metadata requirements are the runtime requirement truth."""
    return instantiate(slug=module.name, requirements=requirements)
