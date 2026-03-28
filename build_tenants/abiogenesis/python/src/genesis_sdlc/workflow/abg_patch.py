# Implements: REQ-F-WORKER-004
"""Runtime patch points for ABG integration under the gsdlc control plane."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any


def _parse_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    config: dict[str, Any] = {}
    current_list_key: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if current_list_key is not None and stripped.startswith("- "):
            config[current_list_key].append(stripped[2:].strip())
            continue
        current_list_key = None
        if ":" in stripped:
            key, _, value = stripped.partition(":")
            key = key.strip()
            value = value.strip()
            if value == "":
                config[key] = []
                current_list_key = key
            else:
                config[key] = value
    return config


def _load_project_config(workspace_root: Path) -> dict[str, Any]:
    kernel_config = _parse_yaml_config(workspace_root / ".genesis" / "genesis.yml")
    contract_ref = kernel_config.get("runtime_contract")
    if isinstance(contract_ref, str) and contract_ref:
        contract_path = (workspace_root / contract_ref).resolve()
        if contract_path.exists():
            return _parse_yaml_config(contract_path)
    return kernel_config


def _resolve_configured_worker(workspace_root: Path):
    try:
        from genesis.binding import Worker
    except Exception:
        return None

    config = _load_project_config(workspace_root)
    worker_ref = config.get("worker")
    if not isinstance(worker_ref, str) or ":" not in worker_ref:
        return None

    module_name, _, symbol_name = worker_ref.partition(":")
    try:
        module = importlib.import_module(module_name)
    except Exception:
        return None
    worker = getattr(module, symbol_name, None)
    if not isinstance(worker, Worker):
        return None
    return worker


def apply_abg_scope_worker_patch() -> None:
    """Ensure ABG CLI scope binds the configured worker/router from genesis.yml."""

    try:
        from genesis.services import Scope
    except Exception:
        return

    if getattr(Scope, "_gsdlc_worker_patch", False):
        return

    original_post_init = Scope.__post_init__

    def patched_post_init(self) -> None:
        original_post_init(self)
        current_worker = getattr(self, "worker", None)
        if current_worker is None:
            return
        if getattr(current_worker, "authority_ref", None) == "runtime://role-dispatch":
            return
        if getattr(current_worker, "id", None) != getattr(self, "build", None):
            return
        configured_worker = _resolve_configured_worker(Path(self.workspace_root))
        if configured_worker is not None:
            self.worker = configured_worker

    Scope.__post_init__ = patched_post_init
    Scope._gsdlc_worker_patch = True
