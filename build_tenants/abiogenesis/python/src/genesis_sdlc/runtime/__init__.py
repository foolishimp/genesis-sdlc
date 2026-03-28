# Implements: REQ-F-CTRL-001
"""Runtime control-plane surfaces for the Abiogenesis/Python realization."""

from .backends import (
    backend_capabilities,
    describe_backend_failure,
    has_backend,
    load_backend_registry,
    normalize_backend_result,
    probe_backends,
)
from .doctor import doctor
from .prompt_view import render_effective_prompt, render_effective_prompt_from_manifest
from .resolve import (
    compile_resolved_runtime,
    invoke_worker_turn,
    load_resolved_runtime,
    load_worker_registry,
    resolve_worker_assignments,
)
from .state import (
    ensure_runtime_state_dir,
    infer_workspace_root,
    load_session_overrides,
    write_session_overrides,
)

__all__ = [
    "backend_capabilities",
    "compile_resolved_runtime",
    "describe_backend_failure",
    "doctor",
    "ensure_runtime_state_dir",
    "has_backend",
    "infer_workspace_root",
    "invoke_worker_turn",
    "load_backend_registry",
    "load_resolved_runtime",
    "load_worker_registry",
    "load_session_overrides",
    "normalize_backend_result",
    "probe_backends",
    "render_effective_prompt",
    "render_effective_prompt_from_manifest",
    "resolve_worker_assignments",
    "write_session_overrides",
]
