# Implements: REQ-F-CTRL-003
# Implements: REQ-F-CTRL-006
"""Backend registry and adapter execution for the runtime control plane."""

from __future__ import annotations

import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable

from .state import adapter_contract_path, backend_registry_path, infer_workspace_root, load_json


_ADAPTER_METHODS = frozenset(
    {
        "probe",
        "invoke",
        "normalize",
        "failure_model",
        "capabilities",
    }
)
_BACKEND_ENTRY_FIELDS = frozenset({"transport", "failure_model", "capabilities"})


def _registry_paths(workspace_root: Path | None = None) -> tuple[Path, Path]:
    try:
        workspace = infer_workspace_root(workspace_root)
    except FileNotFoundError:
        repo_root = _repo_root_from_file()
        if repo_root is None:
            raise
        release_runtime = repo_root / "build_tenants" / "abiogenesis" / "python" / "release" / "runtime"
        return release_runtime / "backends.json", release_runtime / "adapter-contract.json"
    return backend_registry_path(workspace), adapter_contract_path(workspace)


def load_backend_registry(workspace_root: Path | None = None) -> dict[str, Any]:
    registry_path, contract_path = _registry_paths(workspace_root)
    registry = load_json(registry_path, default={})
    contract = load_json(contract_path, default={})
    if not isinstance(registry, dict):
        raise ValueError(f"backend registry must be an object: {registry_path}")
    if not isinstance(contract, dict):
        raise ValueError(f"adapter contract must be an object: {contract_path}")
    _validate_adapter_contract(contract, contract_path)
    _validate_backend_registry(registry, registry_path)
    registry["contract"] = contract
    registry["_path"] = str(registry_path)
    registry["_contract_path"] = str(contract_path)
    return registry


def _validate_adapter_contract(contract: dict[str, Any], contract_path: Path) -> None:
    required_methods = contract.get("required_methods")
    if not isinstance(required_methods, list) or not required_methods:
        raise ValueError(f"adapter contract required_methods missing in {contract_path}")
    required_set = {str(method) for method in required_methods}
    unknown = required_set - _ADAPTER_METHODS
    if unknown:
        raise ValueError(f"adapter contract declares unsupported methods {sorted(unknown)} in {contract_path}")

    result_shape = contract.get("result_shape")
    if not isinstance(result_shape, dict):
        raise ValueError(f"adapter contract result_shape missing in {contract_path}")
    expected_shape = {"backend", "content", "capabilities"}
    if set(result_shape) != expected_shape:
        raise ValueError(
            f"adapter contract result_shape must declare {sorted(expected_shape)} in {contract_path}"
        )


def _validate_backend_registry(registry: dict[str, Any], registry_path: Path) -> None:
    backends = registry.get("backends")
    if not isinstance(backends, dict) or not backends:
        raise ValueError(f"backend registry backends missing in {registry_path}")
    for backend, entry in backends.items():
        if not isinstance(entry, dict):
            raise ValueError(f"backend registry entry must be an object: {backend}")
        missing = [field for field in sorted(_BACKEND_ENTRY_FIELDS) if field not in entry]
        if missing:
            raise ValueError(f"backend registry entry {backend!r} missing fields {missing}")
        if not isinstance(entry.get("transport"), str) or not str(entry.get("transport")).strip():
            raise ValueError(f"backend transport must be a non-empty string: {backend}")
        if not isinstance(entry.get("capabilities"), dict):
            raise ValueError(f"backend capabilities must be an object: {backend}")
        if not isinstance(entry.get("failure_model"), str) or not str(entry.get("failure_model")).strip():
            raise ValueError(f"backend failure_model must be a non-empty string: {backend}")


def _registry_entry(backend: str, workspace_root: Path | None = None) -> dict[str, Any]:
    registry = load_backend_registry(workspace_root)
    backends = registry.get("backends", {})
    if not isinstance(backends, dict):
        raise ValueError("backend registry backends must be an object")
    entry = backends.get(backend)
    if not isinstance(entry, dict):
        raise KeyError(f"backend not declared: {backend}")
    return entry


def backend_capabilities(backend: str, workspace_root: Path | None = None) -> dict[str, Any]:
    entry = _registry_entry(backend, workspace_root)
    capabilities = entry.get("capabilities", {})
    if not isinstance(capabilities, dict):
        raise ValueError(f"backend capabilities must be an object: {backend}")
    return capabilities


def normalize_backend_result(raw_result: str, backend: str, workspace_root: Path | None = None) -> dict[str, Any]:
    return {
        "backend": backend,
        "content": raw_result.strip(),
        "capabilities": backend_capabilities(backend, workspace_root),
    }


def describe_backend_failure(
    raw_failure: BaseException | str,
    backend: str,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    message = str(raw_failure)
    return {
        "backend": backend,
        "message": message,
        "failure_model": _registry_entry(backend, workspace_root).get("failure_model", "transport_error"),
    }


def _repo_root_from_file() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "build_tenants" / "abiogenesis" / "python").is_dir() and (parent / "specification").is_dir():
            return parent
    return None


@lru_cache(maxsize=1)
def _transport_bindings() -> tuple[Callable[..., str], Callable[[str], bool]] | None:
    try:
        from genesis.transport import call_agent, has_agent
    except Exception:
        repo_root = _repo_root_from_file()
        if repo_root is None:
            return None
        abg_code = repo_root.parent / "abiogenesis" / "builds" / "claude_code" / "code"
        if not abg_code.exists():
            return None
        if str(abg_code) not in sys.path:
            sys.path.insert(0, str(abg_code))
        try:
            from genesis.transport import call_agent, has_agent
        except Exception:
            return None
    return call_agent, has_agent


def has_backend(backend: str, workspace_root: Path | None = None) -> bool:
    entry = _registry_entry(backend, workspace_root)
    transport = str(entry.get("transport", backend))
    if transport == "codex_exec":
        return shutil.which("codex") is not None
    bindings = _transport_bindings()
    if bindings is None:
        return False
    _, has_agent = bindings
    return has_agent(str(entry.get("agent", backend)))


def probe_backends(workspace_root: Path | None = None) -> dict[str, dict[str, Any]]:
    registry = load_backend_registry(workspace_root)
    backends = registry.get("backends", {})
    if not isinstance(backends, dict):
        raise ValueError("backend registry backends must be an object")
    return {
        backend: {
            "available": has_backend(backend, workspace_root),
            "capabilities": backend_capabilities(backend, workspace_root),
            "transport": entry.get("transport"),
        }
        for backend, entry in backends.items()
        if isinstance(entry, dict)
    }


def invoke_backend(
    prompt: str,
    work_folder: str | Path,
    *,
    backend: str,
    timeout: int,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    entry = _registry_entry(backend, workspace_root)
    transport = str(entry.get("transport", backend))
    cwd = str(Path(work_folder))

    if transport == "codex_exec":
        cmd = [
            "codex",
            "exec",
            "--sandbox",
            "workspace-write",
            "--full-auto",
            "--skip-git-repo-check",
            prompt,
        ]
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            failure = describe_backend_failure(
                RuntimeError(
                    f"Codex transport failed in {cwd} with exit {result.returncode}\n"
                    f"stdout:\n{result.stdout[:2000]}\n\nstderr:\n{result.stderr[:2000]}"
                ),
                backend,
                workspace_root,
            )
            raise RuntimeError(failure["message"])
        return normalize_backend_result(result.stdout, backend, workspace_root)

    bindings = _transport_bindings()
    if bindings is None:
        failure = describe_backend_failure("ABG transport unavailable", backend, workspace_root)
        raise RuntimeError(failure["message"])
    call_agent, _ = bindings
    raw_result = call_agent(prompt, cwd, agent=str(entry.get("agent", backend)), timeout=timeout, retries=0)
    return normalize_backend_result(raw_result, backend, workspace_root)
