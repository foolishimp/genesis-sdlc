# Validates: REQ-F-UAT-001
# Validates: REQ-F-BOOT-001
# Validates: REQ-F-BOOT-002
"""
E2E sandbox tests for genesis_sdlc.

These tests install genesis_sdlc into a fresh temporary directory and verify
the installed workspace is operational. They are the acceptance proof for the
unit_tests→uat_tests edge — unit tests alone are not sufficient.

Run with: pytest -m e2e builds/python/tests/test_e2e_sandbox.py -v
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

INSTALL_SCRIPT = (
    Path(__file__).resolve().parent.parent / "src" / "genesis_sdlc" / "install.py"
)


@pytest.fixture(scope="module")
def sandbox(tmp_path_factory):
    """Install genesis_sdlc into a fresh sandbox. Shared across tests in module."""
    sandbox_dir = tmp_path_factory.mktemp("uat_sandbox")
    result = subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT),
         "--target", str(sandbox_dir),
         "--project-slug", "test_uat"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Sandbox install failed:\n{result.stderr}"
    install_data = json.loads(result.stdout)
    assert install_data["status"] == "installed", f"Unexpected status: {install_data}"
    return sandbox_dir


@pytest.mark.e2e
class TestSandboxInstall:
    """Verify the installer produces a functional workspace."""

    def test_install_succeeds(self, sandbox):
        assert (sandbox / ".genesis" / "genesis.yml").exists()
        assert (sandbox / ".genesis" / "genesis" / "__main__.py").exists()
        assert (sandbox / ".genesis" / "gtl" / "core.py").exists()

    def test_commands_installed(self, sandbox):
        commands_dir = sandbox / ".claude" / "commands"
        assert commands_dir.exists()
        for cmd in ["gen-start.md", "gen-gaps.md", "gen-iterate.md", "gen-review.md"]:
            assert (commands_dir / cmd).exists(), f"Missing command: {cmd}"

    def test_starter_spec_installed(self, sandbox):
        spec = sandbox / "gtl_spec" / "packages" / "test_uat.py"
        assert spec.exists(), "Starter spec not installed"

    def test_build_scaffold_created(self, sandbox):
        assert (sandbox / "builds" / "python" / "src").exists()
        assert (sandbox / "builds" / "python" / "tests").exists()


@pytest.mark.e2e
class TestInstalledEngineOperational:
    """Verify the installed engine responds to commands."""

    def _run_genesis(self, sandbox, *args):
        env = {**os.environ, "PYTHONPATH": str(sandbox / ".genesis")}
        return subprocess.run(
            [sys.executable, "-m", "genesis", *args, "--workspace", str(sandbox)],
            capture_output=True, text=True, cwd=str(sandbox), env=env,
            timeout=30,
        )

    def test_gaps_returns_json(self, sandbox):
        result = self._run_genesis(sandbox, "gaps")
        assert result.returncode == 0, f"gaps failed:\n{result.stderr}"
        data = json.loads(result.stdout)
        assert "jobs_considered" in data
        assert "total_delta" in data

    def test_gaps_sees_full_graph(self, sandbox):
        result = self._run_genesis(sandbox, "gaps")
        data = json.loads(result.stdout)
        assert data["jobs_considered"] == 6, (
            f"Expected 6 jobs (7-asset graph), got {data['jobs_considered']}"
        )
