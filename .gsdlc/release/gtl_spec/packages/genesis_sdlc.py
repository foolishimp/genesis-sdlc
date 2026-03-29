# genesis_sdlc-generated — system-owned; rewritten on reinstall.
# Implements: REQ-F-CUSTODY-002
# Implements: REQ-F-BOOT-004
from pathlib import Path

from workflows.genesis_sdlc.standard.v1_0rc1.genesis_sdlc.workflow import (
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
        reqs.extend(re.findall(r"^### (REQ-[A-Z0-9-]+)\b", text, re.MULTILINE))
    return reqs


package = instantiate(
    slug="genesis_sdlc",
    requirements=_load_reqs(),
    requirement_root=Path("specification") / "requirements",
)
worker = active_worker
WORKFLOW_VERSION = "1.0rc1"
WORKFLOW_RELEASE = "workflows.genesis_sdlc.standard.v1_0rc1"
