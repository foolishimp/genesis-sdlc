# Validates: REQ-F-TEST-005
"""Qualification shim over the product runtime worker-dispatch layer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from genesis_sdlc.runtime.backends import probe_backends
from genesis_sdlc.runtime.resolve import invoke_worker_turn, load_resolved_runtime


def resolved_assignments(work_folder: str | Path) -> dict[str, dict[str, Any]]:
    workspace_root = Path(work_folder)
    resolved = load_resolved_runtime(workspace_root)
    assignments = resolved.get("role_assignments", {})
    if not isinstance(assignments, dict):
        raise ValueError("resolved runtime role_assignments must be an object")
    return {
        role_id: assignment
        for role_id, assignment in assignments.items()
        if isinstance(role_id, str) and isinstance(assignment, dict)
    }


def selected_assignment(
    work_folder: str | Path,
    *,
    role: str | None = None,
    edge: str | None = None,
) -> dict[str, Any]:
    workspace_root = Path(work_folder)
    assignments = resolved_assignments(workspace_root)
    selected_role = role
    if edge is not None:
        resolved = load_resolved_runtime(workspace_root)
        edge_payload = resolved.get("edges", {}).get(edge, {})
        if not isinstance(edge_payload, dict):
            raise KeyError(f"no resolved runtime edge payload for edge: {edge}")
        profile = edge_payload.get("profile", {})
        if not isinstance(profile, dict):
            raise ValueError(f"resolved runtime edge profile must be an object for edge: {edge}")
        selected_role = str(profile.get("role_id", "")).strip()
    if not isinstance(selected_role, str) or not selected_role:
        raise ValueError("selected_assignment requires a role or edge")
    assignment = assignments.get(selected_role)
    if not isinstance(assignment, dict):
        raise KeyError(f"no resolved worker assignment for role: {selected_role}")
    return assignment


def call_agent(prompt: str, work_folder: str, *, role: str, timeout: int) -> dict[str, Any]:
    workspace_root = Path(work_folder)
    return invoke_worker_turn(
        role,
        prompt,
        workspace_root,
        timeout=timeout,
        workspace_root=workspace_root,
    )


def roles_ready(work_folder: str | Path) -> tuple[bool, dict[str, dict[str, Any]]]:
    workspace_root = Path(work_folder)
    assignments = resolved_assignments(workspace_root)
    probes = probe_backends(workspace_root)
    unavailable: dict[str, dict[str, Any]] = {}
    for role_id, assignment in assignments.items():
        backend = assignment.get("backend")
        if not isinstance(backend, str) or not backend:
            unavailable[role_id] = assignment
            continue
        if not probes.get(backend, {}).get("available"):
            unavailable[role_id] = assignment
    return not unavailable, unavailable
