# Validates: REQ-F-TEST-005
"""Thin bridge to the upstream ABG live transport."""

from __future__ import annotations

import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Callable


_THIS_FILE = Path(__file__).resolve()
_REPO_ROOT = _THIS_FILE.parents[5]
_ABG_CODE = _REPO_ROOT.parent / "abiogenesis" / "builds" / "claude_code" / "code"


@lru_cache(maxsize=1)
def _transport_bindings() -> tuple[Callable[..., str], Callable[[str], bool]] | None:
    if not _ABG_CODE.exists():
        return None
    if str(_ABG_CODE) not in sys.path:
        sys.path.insert(0, str(_ABG_CODE))
    try:
        from genesis.transport import call_agent, has_agent
    except Exception:
        return None
    return call_agent, has_agent


def call_agent(prompt: str, work_folder: str, *, agent: str, timeout: int) -> str:
    if agent == "codex":
        cmd = [
            "codex",
            "exec",
            "--sandbox",
            "workspace-write",
            "--full-auto",
            "--skip-git-repo-check",
            prompt,
        ]
        result = subprocess.run(
            cmd,
            cwd=work_folder,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"Codex transport failed in {work_folder} with exit {result.returncode}\n"
                f"stdout:\n{result.stdout[:2000]}\n\nstderr:\n{result.stderr[:2000]}"
            )
        return result.stdout

    bindings = _transport_bindings()
    if bindings is None:
        raise RuntimeError(f"ABG transport unavailable from {_ABG_CODE}")
    fn, _ = bindings
    return fn(prompt, work_folder, agent=agent, timeout=timeout, retries=0)


def has_agent(agent: str) -> bool:
    if agent == "codex":
        return shutil.which("codex") is not None
    bindings = _transport_bindings()
    if bindings is None:
        return False
    _, fn = bindings
    return fn(agent)
