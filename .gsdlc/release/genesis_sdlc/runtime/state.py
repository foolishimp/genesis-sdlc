# Implements: REQ-F-CTRL-001
# Implements: REQ-F-CTRL-002
# Implements: REQ-F-BOOT-009
"""Filesystem and state helpers for the runtime control plane."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ACTIVE_WORKFLOW_RELATIVE = Path(".gsdlc/release/active-workflow.json")
RELEASE_RUNTIME_RELATIVE = Path(".gsdlc/release/runtime")
RUNTIME_STATE_RELATIVE = Path(".ai-workspace/runtime")
RESOLVED_RUNTIME_NAME = "resolved-runtime.json"
SESSION_OVERRIDES_NAME = "session-overrides.json"
DOCTOR_SNAPSHOT_NAME = "doctor.json"


def infer_workspace_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for parent in [current, *current.parents]:
        if (parent / ACTIVE_WORKFLOW_RELATIVE).exists():
            return parent
    raise FileNotFoundError(f"could not infer workspace root from {current}")


def active_workflow_path(workspace_root: Path) -> Path:
    return workspace_root / ACTIVE_WORKFLOW_RELATIVE


def release_runtime_dir(workspace_root: Path) -> Path:
    return workspace_root / RELEASE_RUNTIME_RELATIVE


def runtime_state_dir(workspace_root: Path) -> Path:
    return workspace_root / RUNTIME_STATE_RELATIVE


def resolved_runtime_path(workspace_root: Path) -> Path:
    return runtime_state_dir(workspace_root) / RESOLVED_RUNTIME_NAME


def session_overrides_path(workspace_root: Path) -> Path:
    return runtime_state_dir(workspace_root) / SESSION_OVERRIDES_NAME


def doctor_snapshot_path(workspace_root: Path) -> Path:
    return runtime_state_dir(workspace_root) / DOCTOR_SNAPSHOT_NAME


def backend_registry_path(workspace_root: Path) -> Path:
    return release_runtime_dir(workspace_root) / "backends.json"


def adapter_contract_path(workspace_root: Path) -> Path:
    return release_runtime_dir(workspace_root) / "adapter-contract.json"


def worker_registry_path(workspace_root: Path) -> Path:
    return release_runtime_dir(workspace_root) / "workers.json"


def role_assignments_path(workspace_root: Path) -> Path:
    return release_runtime_dir(workspace_root) / "role-assignments.json"


def ensure_runtime_state_dir(workspace_root: Path) -> Path:
    root = runtime_state_dir(workspace_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def load_json(path: Path, *, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_active_workflow(workspace_root: Path) -> dict[str, Any]:
    payload = load_json(active_workflow_path(workspace_root), default={})
    if not isinstance(payload, dict):
        raise ValueError("active-workflow.json must contain a JSON object")
    return payload


def load_session_overrides(workspace_root: Path) -> dict[str, Any]:
    payload = load_json(session_overrides_path(workspace_root), default={})
    if not isinstance(payload, dict):
        raise ValueError("session-overrides.json must contain a JSON object")
    return payload


def write_session_overrides(workspace_root: Path, payload: dict[str, Any]) -> Path:
    ensure_runtime_state_dir(workspace_root)
    return write_json(session_overrides_path(workspace_root), payload)
