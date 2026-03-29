# Validates: REQ-F-BOOT-001
# Validates: REQ-F-BOOT-002
# Validates: REQ-F-BOOT-003
# Validates: REQ-F-BOOT-004
# Validates: REQ-F-BOOT-006
# Validates: REQ-F-CUSTODY-002
# Validates: REQ-F-TERRITORY-001
# Validates: REQ-F-TERRITORY-002
"""Helpers for real sandbox install and execution tests."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from ..run_archive import RunArchive


_TESTS_DIR = Path(__file__).resolve().parent
_VARIANT_ROOT = _TESTS_DIR.parent.parent
_SOURCE_ROOT = _VARIANT_ROOT.parents[2]
_INSTALLER = _VARIANT_ROOT / "src" / "genesis_sdlc" / "release" / "install.py"


def _run_installer(
    target: Path,
    *args: str,
    archive: RunArchive | None = None,
    label: str = "genesis_sdlc install",
) -> dict[str, Any]:
    result = subprocess.run(
        [
            sys.executable,
            str(_INSTALLER),
            "--target",
            str(target),
            "--source",
            str(_SOURCE_ROOT),
            *args,
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    if archive is not None:
        archive.log_subprocess(label, result)
    assert result.returncode == 0, (
        f"{label} failed (exit {result.returncode})\n"
        f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
    )
    payload = json.loads(result.stdout)
    if archive is not None:
        archive.capture_json(f"{label.replace(' ', '_')}.json", payload)
    return payload


def install_real_sandbox(
    target: Path,
    *,
    slug: str = "sandbox_project",
    self_host: bool = False,
    archive: RunArchive | None = None,
) -> dict[str, Any]:
    extra_args: list[str] = []
    if self_host:
        extra_args.append("--self-host")
    payload = _run_installer(
        target,
        "--project-slug",
        slug,
        *extra_args,
        archive=archive,
        label="genesis_sdlc install",
    )
    if archive is not None:
        archive.update_summary(
            installer_status=payload.get("status"),
            installer_target=payload.get("target"),
            project_slug=payload.get("project_slug"),
        )
    return payload


def reset_runtime_sandbox(
    target: Path,
    *,
    archive: RunArchive | None = None,
) -> dict[str, Any]:
    return _run_installer(
        target,
        "--reset-runtime",
        archive=archive,
        label="genesis_sdlc reset-runtime",
    )


def audit_real_sandbox(
    target: Path,
    *,
    slug: str = "sandbox_project",
    self_host: bool = False,
    archive: RunArchive | None = None,
) -> dict[str, Any]:
    extra_args: list[str] = []
    if self_host:
        extra_args.append("--self-host")
    return _run_installer(
        target,
        "--project-slug",
        slug,
        "--audit",
        *extra_args,
        archive=archive,
        label="genesis_sdlc audit",
    )


def installed_env(workspace: Path) -> dict[str, str]:
    env = os.environ.copy()
    paths = [
        str(workspace / ".gsdlc" / "release"),
        str(workspace / ".genesis"),
    ]
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join(paths + ([existing] if existing else []))
    return env


def run_genesis(
    workspace: Path,
    *args: str,
    archive: RunArchive | None = None,
    label: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [sys.executable, "-m", "genesis", *args, "--workspace", str(workspace)],
        cwd=str(workspace),
        env=installed_env(workspace),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if archive is not None:
        archive.log_subprocess(label or f"genesis {' '.join(args)}", result)
    return result
