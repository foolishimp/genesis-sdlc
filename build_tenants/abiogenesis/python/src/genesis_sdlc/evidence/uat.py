# Implements: REQ-F-UAT-002
# Implements: REQ-F-UAT-003
"""UAT evidence helpers."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def write_sandbox_report(
    report_path: Path,
    *,
    scenario: str,
    install_success: bool = True,
    test_count: int = 1,
    pass_count: int = 1,
    fail_count: int = 0,
    all_pass: bool = True,
    sandbox_path: str | None = None,
) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "install_success": install_success,
                "sandbox_path": sandbox_path,
                "test_count": test_count,
                "pass_count": pass_count,
                "fail_count": fail_count,
                "all_pass": all_pass,
                "scenario": scenario,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return report_path
