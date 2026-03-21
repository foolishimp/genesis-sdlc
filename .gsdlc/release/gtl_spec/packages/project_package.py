# genesis_sdlc-generated — system-owned; rewritten on every redeploy.
# Implements: REQ-F-CUSTODY-002
import re
from pathlib import Path

from workflows.genesis_sdlc.standard.v1_0_0b1.spec import instantiate


def _load_reqs():
    """Parse REQ-* keys from specification/requirements.md headers."""
    req_file = Path("specification/requirements.md")
    if not req_file.exists():
        return []
    reqs = []
    for line in req_file.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (REQ-[A-Z0-9][-A-Z0-9]*)", line)
        if m:
            reqs.append(m.group(1))
    return reqs


package, worker = instantiate(slug="project_package", requirements=_load_reqs())
