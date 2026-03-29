# Implements: REQ-F-CUSTODY-002
# Implements: REQ-F-BOOT-004
"""Wrapper generation and requirement loading for installed sandboxes."""

from __future__ import annotations

import re
from pathlib import Path


REQ_HEADER_PATTERN = re.compile(r"^### (REQ-[A-Z0-9-]+)\b", re.MULTILINE)


def load_project_requirements(root: Path) -> list[str]:
    """Load project REQ keys from specification/requirements/*.md in deterministic order."""
    requirements_dir = root / "specification" / "requirements"
    if not requirements_dir.exists():
        return []

    reqs: list[str] = []
    for path in sorted(
        p for p in requirements_dir.rglob("*.md")
        if p.name != "README.md"
    ):
        matches = REQ_HEADER_PATTERN.findall(path.read_text(encoding="utf-8"))
        reqs.extend(matches)
    return reqs


def render_wrapper(slug: str, version: str) -> str:
    version_tag = version.replace(".", "_")
    return f'''# genesis_sdlc-generated — system-owned; rewritten on reinstall.
# Implements: REQ-F-CUSTODY-002
# Implements: REQ-F-BOOT-004
from pathlib import Path

from workflows.genesis_sdlc.standard.v{version_tag}.genesis_sdlc.workflow import (
    instantiate,
    worker as active_worker,
)


def _load_reqs() -> list[str]:
    import re

    requirements_dir = Path("specification") / "requirements"
    if not requirements_dir.exists():
        return []

    reqs: list[str] = []
    for path in sorted(
        p for p in requirements_dir.rglob("*.md")
        if p.name != "README.md"
    ):
        text = path.read_text(encoding="utf-8")
        reqs.extend(re.findall(r"^### (REQ-[A-Z0-9-]+)\\b", text, re.MULTILINE))
    return reqs


package = instantiate(
    slug="{slug}",
    requirements=_load_reqs(),
    requirement_root=Path("specification") / "requirements",
)
worker = active_worker
WORKFLOW_VERSION = "{version}"
WORKFLOW_RELEASE = "workflows.genesis_sdlc.standard.v{version_tag}"
'''
