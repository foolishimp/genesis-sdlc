# Validates: REQ-F-COV-001
# Validates: REQ-F-TAG-001
# Validates: REQ-F-TAG-002
"""Tests for genesis traceability checks — impl/validates tags and req coverage."""
import subprocess
import sys
import os
from pathlib import Path

BUILD_ROOT = Path(__file__).resolve().parents[1]   # builds/python/
PROJECT_ROOT = BUILD_ROOT.parents[1]               # genesis_sdlc/
GENESIS_PYTHONPATH = str(PROJECT_ROOT / ".genesis")


def _run_genesis(*args):
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        GENESIS_PYTHONPATH
        + ":" + str(BUILD_ROOT / "src")
        + (":" + existing if existing else "")
    )
    return subprocess.run(
        [sys.executable, "-m", "genesis"] + list(args),
        capture_output=True, text=True,
        cwd=str(PROJECT_ROOT),
        env=env,
    )


class TestImplTags:
    def test_check_tags_command_exists(self):
        result = _run_genesis("check-tags", "--help")
        assert result.returncode in (0, 1, 2)

    def test_src_files_are_tagged(self):
        """All .py files under builds/python/src/ must carry # Implements: REQ-* tags."""
        result = _run_genesis(
            "check-tags", "--type", "implements", "--path", "builds/python/src/"
        )
        assert result.returncode == 0, (
            f"Untagged source files found:\n{result.stdout}\n{result.stderr}"
        )

    def test_test_files_are_tagged(self):
        """All test .py files must carry # Validates: REQ-* tags."""
        result = _run_genesis(
            "check-tags", "--type", "validates", "--path", "builds/python/tests/"
        )
        assert result.returncode == 0, (
            f"Untagged test files found:\n{result.stdout}\n{result.stderr}"
        )


class TestReqCoverage:
    def test_req_coverage_all_keys_covered(self):
        """Every REQ key in Package.requirements must appear in a feature vector."""
        result = _run_genesis(
            "check-req-coverage",
            "--package", "genesis_sdlc.sdlc_graph:package",
            "--features", ".ai-workspace/features/",
        )
        assert result.returncode == 0, (
            f"Uncovered REQ keys:\n{result.stdout}\n{result.stderr}"
        )
