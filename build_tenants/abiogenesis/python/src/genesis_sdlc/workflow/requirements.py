# Implements: REQ-F-CUSTODY-002
"""Requirement discovery for the local specification surface."""

from __future__ import annotations

import re
from pathlib import Path


REQ_HEADER = re.compile(r"^### (REQ-[A-Z0-9-]+)\b", re.MULTILINE)


def find_requirements_root(start: Path | None = None) -> Path | None:
    """Find the nearest `specification/requirements/` root from a starting path."""
    current = (start or Path.cwd()).resolve()
    candidates = (current, *current.parents)
    for base in candidates:
        root = base / "specification" / "requirements"
        if root.is_dir():
            return root
    return None


def load_requirements(root: Path | None = None) -> list[str]:
    if root is None:
        return []

    root_path = root
    if not root_path.exists():
        return []

    requirement_keys: list[str] = []
    seen: set[str] = set()
    for path in sorted(root_path.glob("*.md")):
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        for match in REQ_HEADER.findall(text):
            if match not in seen:
                seen.add(match)
                requirement_keys.append(match)
    return requirement_keys


def requirement_manifest(root: Path | None = None) -> dict[str, list[str]]:
    if root is None:
        return {}

    root_path = root
    if not root_path.exists():
        return {}

    manifest: dict[str, list[str]] = {}
    for path in sorted(root_path.glob("*.md")):
        if path.name == "README.md":
            continue
        manifest[path.name] = REQ_HEADER.findall(path.read_text(encoding="utf-8"))
    return manifest


def load_local_requirements(start: Path | None = None) -> list[str]:
    """Explicit self-hosting helper for local workspace requirement discovery."""
    return load_requirements(find_requirements_root(start))
