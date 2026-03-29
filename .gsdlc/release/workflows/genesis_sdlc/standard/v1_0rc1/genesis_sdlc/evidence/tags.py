# Implements: REQ-F-TAG-001
# Implements: REQ-F-TAG-002
"""Traceability tag helpers."""

from __future__ import annotations

from pathlib import Path

from .fd_checks import check_trace_tags


def check_tags(root: Path, *, kind: str) -> int:
    if kind not in {"implements", "validates"}:
        raise ValueError(f"unsupported tag kind: {kind}")
    return check_trace_tags(root, kind)


def check_implements_tags(root: Path) -> int:
    return check_tags(root, kind="implements")


def check_validates_tags(root: Path) -> int:
    return check_tags(root, kind="validates")
