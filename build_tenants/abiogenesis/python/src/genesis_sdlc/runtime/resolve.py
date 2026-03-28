# Implements: REQ-F-CTRL-001
# Implements: REQ-F-CTRL-004
# Implements: REQ-F-WORKER-001
# Implements: REQ-F-WORKER-002
# Implements: REQ-F-WORKER-003
"""Resolved-runtime compilation and worker assignment for the assurance control plane."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from genesis_sdlc.workflow.roles import workflow_job_roles, workflow_role_manifest
from genesis_sdlc.workflow.transforms import (
    EDGE_TRANSFORM_CONTRACTS,
    edge_override_filename,
    load_project_edge_override,
    resolve_edge_transform_contract,
)

from .backends import (
    backend_capabilities,
    invoke_backend,
    load_backend_registry,
)
from .state import (
    ensure_runtime_state_dir,
    infer_workspace_root,
    load_active_workflow,
    load_json,
    load_session_overrides,
    resolved_runtime_path,
    role_assignments_path,
    worker_registry_path,
    write_json,
)


def _declared_role_ids() -> tuple[str, ...]:
    return tuple(str(role["id"]) for role in workflow_role_manifest())


def _relative_to_workspace(path: Path, workspace_root: Path) -> str:
    try:
        return str(path.resolve().relative_to(workspace_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _require_mapping(value: Any, *, path: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _validate_legacy_runtime_fields(active_workflow: dict[str, Any], session_overrides: dict[str, Any]) -> None:
    customization = active_workflow.get("customization", {})
    if isinstance(customization, dict) and "fp_transport_agent" in customization:
        raise ValueError(
            "legacy field .gsdlc/release/active-workflow.json#/customization/fp_transport_agent is no longer supported; reinstall the release to get worker-assignment defaults"
        )
    if "fp_transport_agent" in session_overrides:
        raise ValueError(
            "legacy field .ai-workspace/runtime/session-overrides.json#/fp_transport_agent is no longer supported; use worker_assignments instead"
        )


def load_worker_registry(workspace_root: Path | None = None) -> dict[str, Any]:
    workspace = infer_workspace_root(workspace_root)
    workers_path = worker_registry_path(workspace)
    assignments_path = role_assignments_path(workspace)

    registry = load_json(workers_path, default={})
    assignments = load_json(assignments_path, default={})
    if not isinstance(registry, dict):
        raise ValueError(f"worker registry must be an object: {workers_path}")
    if not isinstance(assignments, dict):
        raise ValueError(f"role assignments must be an object: {assignments_path}")

    backend_registry = load_backend_registry(workspace)
    _validate_worker_registry(
        registry,
        assignments,
        backend_registry=backend_registry,
        workers_path=workers_path,
        assignments_path=assignments_path,
    )
    registry["role_assignments"] = assignments["roles"]
    registry["_path"] = str(workers_path)
    registry["_assignments_path"] = str(assignments_path)
    return registry


def _validate_worker_registry(
    registry: dict[str, Any],
    assignments: dict[str, Any],
    *,
    backend_registry: dict[str, Any],
    workers_path: Path,
    assignments_path: Path,
) -> None:
    workers = registry.get("workers")
    if not isinstance(workers, dict) or not workers:
        raise ValueError(f"worker registry workers missing in {workers_path}")

    declared_backends = backend_registry.get("backends", {})
    if not isinstance(declared_backends, dict) or not declared_backends:
        raise ValueError("backend registry must declare at least one backend before workers are validated")

    declared_roles = set(_declared_role_ids())
    if not declared_roles:
        raise ValueError("workflow declares no runtime roles for worker validation")

    for worker_id, entry in workers.items():
        if not isinstance(entry, dict):
            raise ValueError(f"worker registry entry must be an object: {worker_id}")
        declared_worker_id = entry.get("worker_id")
        if not isinstance(declared_worker_id, str) or declared_worker_id != worker_id:
            raise ValueError(f"worker registry entry {worker_id!r} must repeat worker_id exactly")
        roles = entry.get("roles")
        if not isinstance(roles, list) or not roles:
            raise ValueError(f"worker registry entry {worker_id!r} must declare non-empty roles")
        unknown_roles = sorted(role for role in roles if role not in declared_roles)
        if unknown_roles:
            raise ValueError(f"worker registry entry {worker_id!r} declares unknown roles {unknown_roles}")
        backend = entry.get("backend")
        if not isinstance(backend, str) or not backend.strip():
            raise ValueError(f"worker registry entry {worker_id!r} must declare a backend")
        if backend not in declared_backends:
            raise ValueError(
                f"worker registry entry {worker_id!r} binds undeclared backend {backend!r}"
            )
        capabilities = entry.get("capabilities")
        if not isinstance(capabilities, dict):
            raise ValueError(f"worker registry entry {worker_id!r} capabilities must be an object")

    roles_payload = assignments.get("roles")
    if not isinstance(roles_payload, dict) or not roles_payload:
        raise ValueError(f"role assignments missing roles object in {assignments_path}")

    missing_assignments = sorted(role for role in declared_roles if role not in roles_payload)
    if missing_assignments:
        raise ValueError(
            f"role assignments missing declared roles {missing_assignments} in {assignments_path}"
        )

    for role_id, worker_id in roles_payload.items():
        if role_id not in declared_roles:
            raise ValueError(f"role assignments declare unknown role {role_id!r}")
        if not isinstance(worker_id, str) or not worker_id.strip():
            raise ValueError(f"role assignment for {role_id!r} must be a non-empty worker id")
        worker = workers.get(worker_id)
        if not isinstance(worker, dict):
            raise ValueError(f"role assignment for {role_id!r} references unknown worker {worker_id!r}")
        worker_roles = worker.get("roles", [])
        if role_id not in worker_roles:
            raise ValueError(
                f"role assignment for {role_id!r} references worker {worker_id!r} without declared role coverage"
            )


def _active_worker_assignment_hints(active_workflow: dict[str, Any]) -> dict[str, str]:
    customization = _require_mapping(
        active_workflow.get("customization"),
        path=".gsdlc/release/active-workflow.json#/customization",
    )
    hints = customization.get("default_worker_assignments")
    if hints is None:
        return {}
    if not isinstance(hints, dict):
        raise ValueError(
            ".gsdlc/release/active-workflow.json#/customization/default_worker_assignments must be an object"
        )
    return {
        str(role_id): str(worker_id)
        for role_id, worker_id in hints.items()
        if isinstance(role_id, str) and isinstance(worker_id, str) and worker_id
    }


def _session_worker_assignment_overrides(session_overrides: dict[str, Any]) -> dict[str, str]:
    overrides = session_overrides.get("worker_assignments")
    if overrides is None:
        return {}
    if not isinstance(overrides, dict):
        raise ValueError(".ai-workspace/runtime/session-overrides.json#/worker_assignments must be an object")
    return {
        str(role_id): str(worker_id)
        for role_id, worker_id in overrides.items()
        if isinstance(role_id, str) and isinstance(worker_id, str) and worker_id
    }


def resolve_worker_assignments(
    workspace_root: Path | None = None,
    *,
    active_workflow: dict[str, Any] | None = None,
    session_overrides: dict[str, Any] | None = None,
    worker_registry: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    workspace = infer_workspace_root(workspace_root)
    active = active_workflow or load_active_workflow(workspace)
    session = session_overrides or load_session_overrides(workspace)
    _validate_legacy_runtime_fields(active, session)
    registry = worker_registry or load_worker_registry(workspace)

    workers = registry.get("workers", {})
    if not isinstance(workers, dict) or not workers:
        raise ValueError("worker registry workers must be an object")
    release_defaults = registry.get("role_assignments", {})
    if not isinstance(release_defaults, dict):
        raise ValueError("worker registry role_assignments must be an object")

    backend_registry = load_backend_registry(workspace)
    role_hints = _active_worker_assignment_hints(active)
    role_overrides = _session_worker_assignment_overrides(session)

    role_assignments: dict[str, dict[str, Any]] = {}
    for role_id in _declared_role_ids():
        if role_id in role_overrides:
            worker_id = role_overrides[role_id]
            provenance = {
                "source_layer": "runtime_state",
                "source_path": f".ai-workspace/runtime/session-overrides.json#/worker_assignments/{role_id}",
            }
        elif role_id in role_hints:
            worker_id = role_hints[role_id]
            provenance = {
                "source_layer": "release_declaration",
                "source_path": f".gsdlc/release/active-workflow.json#/customization/default_worker_assignments/{role_id}",
            }
        elif role_id in release_defaults:
            worker_id = release_defaults[role_id]
            provenance = {
                "source_layer": "release_runtime",
                "source_path": f".gsdlc/release/runtime/role-assignments.json#/roles/{role_id}",
            }
        else:
            raise ValueError(f"no worker assignment declared for role {role_id!r}")

        worker = workers.get(worker_id)
        if not isinstance(worker, dict):
            raise ValueError(
                f"worker {worker_id!r} selected for role {role_id!r} is not declared in .gsdlc/release/runtime/workers.json"
            )
        worker_roles = worker.get("roles", [])
        if role_id not in worker_roles:
            raise ValueError(
                f"worker {worker_id!r} selected for role {role_id!r} does not declare role coverage"
            )
        backend = worker.get("backend")
        if not isinstance(backend, str) or not backend:
            raise ValueError(f"worker {worker_id!r} does not declare a backend binding")
        declared_backends = backend_registry.get("backends", {})
        if not isinstance(declared_backends, dict) or backend not in declared_backends:
            raise ValueError(
                f"worker {worker_id!r} binds backend {backend!r} that is not declared in .gsdlc/release/runtime/backends.json"
            )
        worker_caps = worker.get("capabilities", {})
        if not isinstance(worker_caps, dict):
            raise ValueError(f"worker {worker_id!r} capabilities must be an object")
        backend_caps = backend_capabilities(backend, workspace)
        role_assignments[role_id] = {
            "role_id": role_id,
            "worker_id": worker_id,
            "backend": backend,
            "worker_capabilities": worker_caps,
            "backend_capabilities": backend_caps,
            "capabilities": {**backend_caps, **worker_caps},
            "provenance": provenance,
        }
    return role_assignments


def _constructive_role_for_edge(edge: str) -> str:
    role_ids = workflow_job_roles().get(edge, ())
    if len(role_ids) != 1:
        raise ValueError(f"edge {edge!r} does not resolve to exactly one constructive role")
    return role_ids[0]


def _edge_profile(
    edge: str,
    workspace_root: Path,
    role_assignments: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract = resolve_edge_transform_contract(edge, workspace_root)
    if contract is None:
        raise KeyError(f"no transform contract declared for edge: {edge}")

    role_id = _constructive_role_for_edge(edge)
    assignment = role_assignments.get(role_id)
    if not isinstance(assignment, dict):
        raise KeyError(f"no resolved worker assignment for role: {role_id}")

    profile = asdict(contract)
    profile["authority_contexts"] = list(contract.authority_contexts)
    profile["required_sections"] = list(contract.required_sections)
    profile["requirement_refs"] = list(contract.requirement_refs)
    profile["design_refs"] = list(contract.design_refs)
    profile["role_id"] = role_id
    profile["worker_id"] = assignment["worker_id"]
    profile["backend"] = assignment["backend"]

    default_source = {
        "source_layer": "workflow_default",
        "source_path": ".gsdlc/release/genesis_sdlc/workflow/transforms.py",
    }

    override_payload = load_project_edge_override(edge, workspace_root)
    override_path = Path("specification/design/fp/edge-overrides") / edge_override_filename(edge)
    override_source = {
        "source_layer": "project_tuning",
        "source_path": override_path.as_posix(),
    }

    provenance: dict[str, Any] = {}
    for field in (
        "target_asset",
        "artifact_kind",
        "authority_contexts",
        "suggested_output",
        "guidance",
        "required_sections",
        "customization_intent",
        "requirement_refs",
        "design_refs",
    ):
        provenance[field] = default_source

    if isinstance(override_payload, dict):
        if "authority_contexts" in override_payload:
            provenance["authority_contexts"] = override_source
        if "suggested_output" in override_payload:
            provenance["suggested_output"] = override_source
        if "required_sections" in override_payload:
            provenance["required_sections"] = override_source
        if "customization_intent" in override_payload:
            provenance["customization_intent"] = override_source
        if "requirement_refs" in override_payload:
            provenance["requirement_refs"] = override_source
        if "design_refs" in override_payload:
            provenance["design_refs"] = override_source
        if "guidance" in override_payload or "guidance_append" in override_payload:
            provenance["guidance"] = override_source

    provenance["role_id"] = {
        "source_layer": "workflow_default",
        "source_path": ".gsdlc/release/genesis_sdlc/workflow/graph.py",
    }
    provenance["worker_id"] = assignment["provenance"]
    provenance["backend"] = {
        "source_layer": "runtime_resolution",
        "source_path": f".ai-workspace/runtime/resolved-runtime.json#/role_assignments/{role_id}/backend",
    }
    return profile, provenance


def compile_resolved_runtime(workspace_root: Path | None = None) -> dict[str, Any]:
    workspace = infer_workspace_root(workspace_root)
    ensure_runtime_state_dir(workspace)

    active_workflow = load_active_workflow(workspace)
    session_overrides = load_session_overrides(workspace)
    _validate_legacy_runtime_fields(active_workflow, session_overrides)

    backend_registry = load_backend_registry(workspace)
    worker_registry = load_worker_registry(workspace)
    role_assignments = resolve_worker_assignments(
        workspace,
        active_workflow=active_workflow,
        session_overrides=session_overrides,
        worker_registry=worker_registry,
    )

    edges: dict[str, Any] = {}
    for edge in EDGE_TRANSFORM_CONTRACTS:
        profile, provenance = _edge_profile(edge, workspace, role_assignments)
        edges[edge] = {
            "profile": profile,
            "provenance": provenance,
        }

    payload = {
        "schema_version": 2,
        "compiled_at": datetime.now(timezone.utc).isoformat(),
        "workspace_root": str(workspace),
        "release_declaration": ".gsdlc/release/active-workflow.json",
        "release_runtime": ".gsdlc/release/runtime/",
        "project_tuning_root": "specification/design/fp/edge-overrides",
        "runtime_state_root": ".ai-workspace/runtime/",
        "version": active_workflow.get("version"),
        "worker_registry": {
            "path": ".gsdlc/release/runtime/workers.json",
            "assignments_path": ".gsdlc/release/runtime/role-assignments.json",
            "declared_workers": sorted((worker_registry.get("workers") or {}).keys()),
        },
        "backend_registry": {
            "path": ".gsdlc/release/runtime/backends.json",
            "declared_backends": sorted((backend_registry.get("backends") or {}).keys()),
        },
        "role_assignments": role_assignments,
        "session_overrides": session_overrides,
        "edges": edges,
    }
    write_json(resolved_runtime_path(workspace), payload)
    return payload


def load_resolved_runtime(workspace_root: Path | None = None) -> dict[str, Any]:
    workspace = infer_workspace_root(workspace_root)
    loaded = compile_resolved_runtime(workspace)
    if not isinstance(loaded, dict):
        raise ValueError("resolved runtime must be an object")
    return loaded


def invoke_worker_turn(
    role: str,
    prompt: str,
    work_folder: str | Path,
    *,
    timeout: int,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    workspace = infer_workspace_root(workspace_root or Path(work_folder))
    resolved = load_resolved_runtime(workspace)
    assignments = resolved.get("role_assignments", {})
    if not isinstance(assignments, dict):
        raise ValueError("resolved runtime role_assignments must be an object")
    assignment = assignments.get(role)
    if not isinstance(assignment, dict):
        raise KeyError(f"no resolved worker assignment for role: {role}")
    backend = assignment.get("backend")
    if not isinstance(backend, str) or not backend:
        raise ValueError(f"resolved worker assignment for role {role!r} declares no backend")
    result = invoke_backend(
        prompt,
        work_folder,
        backend=backend,
        timeout=timeout,
        workspace_root=workspace,
    )
    result["role_id"] = role
    result["worker_id"] = assignment.get("worker_id")
    result["worker_capabilities"] = assignment.get("worker_capabilities", {})
    return result
