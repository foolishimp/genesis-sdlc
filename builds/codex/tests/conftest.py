# Validates: REQ-F-TEST-001
"""Test configuration for the Codex genesis_sdlc build."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
CODE_ROOT = PROJECT_ROOT / "builds" / "codex" / "code"
ABG_CODE_ROOT = PROJECT_ROOT.parent / "abiogenesis" / "builds" / "codex" / "code"

for root in (CODE_ROOT, ABG_CODE_ROOT):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
