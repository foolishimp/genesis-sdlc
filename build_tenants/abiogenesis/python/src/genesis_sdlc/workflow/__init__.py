"""Workflow declaration surfaces for the Abiogenesis/Python realization."""

# Implements: REQ-F-CUSTODY-001

from __future__ import annotations

from importlib import import_module


_PACKAGE_EXPORTS = {
    "graph_manifest",
    "instantiate",
    "instantiate_local",
    "module",
    "package",
    "worker",
}
_TRANSFORM_EXPORTS = {
    "build_assessment_prompt",
    "build_constructive_prompt",
    "edge_override_filename",
    "get_edge_transform_contract",
    "load_project_edge_override",
    "resolve_edge_transform_contract",
}

__all__ = sorted(_PACKAGE_EXPORTS | _TRANSFORM_EXPORTS)


def __getattr__(name: str):
    if name in _PACKAGE_EXPORTS:
        return getattr(import_module(".package", __name__), name)
    if name in _TRANSFORM_EXPORTS:
        return getattr(import_module(".transforms", __name__), name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
