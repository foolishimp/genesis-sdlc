# Implements: REQ-F-CTRL-005
"""Runtime readiness reporting for the assurance control plane."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .backends import probe_backends
from .resolve import compile_resolved_runtime
from .state import doctor_snapshot_path, infer_workspace_root, write_json


def doctor(workspace_root: Path | None = None) -> dict[str, Any]:
    workspace = infer_workspace_root(workspace_root)
    findings: list[dict[str, Any]] = []
    resolved: dict[str, Any] | None = None
    role_assignments: dict[str, Any] = {}

    try:
        resolved = compile_resolved_runtime(workspace)
        resolved_assignments = resolved.get("role_assignments")
        if isinstance(resolved_assignments, dict):
            role_assignments = resolved_assignments
    except Exception as exc:
        findings.append(
            {
                "severity": "error",
                "kind": "runtime_misconfiguration",
                "message": str(exc),
            }
        )

    try:
        probes = probe_backends(workspace)
    except Exception as exc:
        probes = {}
        findings.append(
            {
                "severity": "error",
                "kind": "backend_registry_invalid",
                "message": str(exc),
            }
        )

    for role_id, assignment in role_assignments.items():
        if not isinstance(assignment, dict):
            continue
        backend = assignment.get("backend")
        worker_id = assignment.get("worker_id")
        if not isinstance(backend, str) or not backend:
            continue
        selected_probe = probes.get(backend, {"available": False})
        if not selected_probe.get("available"):
            findings.append(
                {
                    "severity": "error",
                    "kind": "backend_unavailable",
                    "role_id": role_id,
                    "worker_id": worker_id,
                    "backend": backend,
                    "message": f"selected backend is unavailable for role {role_id}: {backend}",
                }
            )

    payload = {
        "status": "ok" if not findings else "degraded",
        "workspace_root": str(workspace),
        "role_assignments": role_assignments,
        "resolved_runtime_path": ".ai-workspace/runtime/resolved-runtime.json",
        "resolved_runtime_available": resolved is not None,
        "backend_probes": probes,
        "findings": findings,
    }
    write_json(doctor_snapshot_path(workspace), payload)
    return payload
