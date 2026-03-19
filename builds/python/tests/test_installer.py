# Validates: REQ-F-BOOT-001
# Validates: REQ-F-BOOT-002
# Validates: REQ-F-BOOT-003
# Validates: REQ-F-BOOT-004
# Validates: REQ-F-BOOT-005
"""Tests for genesis_sdlc.install — the product installer."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

BUILD_ROOT = Path(__file__).resolve().parents[1]   # builds/python/
PROJECT_ROOT = BUILD_ROOT.parents[1]               # genesis_sdlc/
INSTALL_MODULE = BUILD_ROOT / "src" / "genesis_sdlc" / "install.py"

# Installer requires abiogenesis as a sibling — skip if not present
ABIOGENESIS_ROOT = PROJECT_ROOT.parent / "abiogenesis"
pytestmark = pytest.mark.skipif(
    not ABIOGENESIS_ROOT.exists(),
    reason="abiogenesis sibling directory not found",
)


def _install(target: Path, extra_args: list = ()) -> dict:
    result = subprocess.run(
        [sys.executable, str(INSTALL_MODULE),
         "--target", str(target),
         "--source", str(PROJECT_ROOT)]
        + list(extra_args),
        capture_output=True, text=True,
    )
    assert result.stdout.strip(), f"No output from installer:\n{result.stderr}"
    return json.loads(result.stdout)


# ── Source root detection ─────────────────────────────────────────────────────

class TestSourceRootDetection:
    def test_script_source_root_resolves_correctly(self):
        """_source_root_from_script() must return the genesis_sdlc project root."""
        sys.path.insert(0, str(BUILD_ROOT / "src"))
        try:
            from genesis_sdlc.install import _source_root_from_script
            root = _source_root_from_script()
            assert (root / "gtl_spec").exists(), f"gtl_spec not found under {root}"
            assert (root / ".genesis").exists(), f".genesis not found under {root}"
        finally:
            sys.path.pop(0)

    def test_explicit_source_accepted(self, tmp_path):
        """--source flag overrides auto-detection."""
        result = _install(tmp_path, ["--source", str(PROJECT_ROOT),
                                      "--project-slug", "test_proj"])
        assert result["status"] == "installed"
        assert result["source"] == str(PROJECT_ROOT)


# ── Engine installation ───────────────────────────────────────────────────────

class TestEngineInstall:
    def test_engine_installed(self, tmp_path):
        result = _install(tmp_path, ["--project-slug", "test_proj"])
        assert result["engine"] == "installed"
        assert (tmp_path / ".genesis" / "genesis" / "__main__.py").exists()

    def test_gtl_vendored(self, tmp_path):
        _install(tmp_path, ["--project-slug", "test_proj"])
        assert (tmp_path / ".genesis" / "gtl" / "core.py").exists()

    def test_genesis_yml_written(self, tmp_path):
        _install(tmp_path, ["--project-slug", "my_domain"])
        text = (tmp_path / ".genesis" / "genesis.yml").read_text()
        assert "my_domain" in text
        assert "gtl_spec.packages.my_domain:package" in text
        assert "pythonpath" in text
        assert "builds/python/src" in text


# ── SDLC starter spec ─────────────────────────────────────────────────────────

class TestSdlcStarterSpec:
    def test_starter_spec_is_sdlc_graph(self, tmp_path):
        """Starter spec must be the full SDLC graph, not the minimal abiogenesis stub."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec = (tmp_path / "gtl_spec" / "packages" / "my_proj.py").read_text()
        assert "intent→requirements" in spec
        assert "spec→output" not in spec

    def test_slug_substituted(self, tmp_path):
        _install(tmp_path, ["--project-slug", "acme_corp"])
        spec = (tmp_path / "gtl_spec" / "packages" / "acme_corp.py").read_text()
        assert 'name="acme_corp"' in spec
        assert 'name="genesis_sdlc"' not in spec

    def test_req_coverage_references_slug(self, tmp_path):
        """req_coverage evaluator must point at the project's own package, not genesis_sdlc."""
        _install(tmp_path, ["--project-slug", "acme_corp"])
        spec = (tmp_path / "gtl_spec" / "packages" / "acme_corp.py").read_text()
        assert "gtl_spec.packages.acme_corp:package" in spec
        assert "gtl_spec.packages.genesis_sdlc:package" not in spec

    def test_platform_paths_substituted_default(self, tmp_path):
        """Default python platform: builds/python/ paths in spec."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec = (tmp_path / "gtl_spec" / "packages" / "my_proj.py").read_text()
        assert "builds/python/src/" in spec
        assert "builds/python/tests/" in spec

    def test_platform_paths_substituted_custom(self, tmp_path):
        """--platform java: builds/java/ paths in spec, not builds/python/."""
        _install(tmp_path, ["--project-slug", "my_proj", "--platform", "java"])
        spec = (tmp_path / "gtl_spec" / "packages" / "my_proj.py").read_text()
        assert "builds/java/src/" in spec
        assert "builds/java/tests/" in spec
        assert "builds/python/" not in spec

    def test_reinstall_does_not_clobber_customised_spec(self, tmp_path):
        """Once user has edited their spec (no stub marker), reinstall must not overwrite."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec_path = tmp_path / "gtl_spec" / "packages" / "my_proj.py"
        spec_path.write_text("# user customisation\n")
        result = _install(tmp_path, ["--project-slug", "my_proj"])
        assert result["sdlc_starter_spec"] == "already_customised"
        assert "user customisation" in spec_path.read_text()


# ── Commands ──────────────────────────────────────────────────────────────────

class TestCommandsInstall:
    def test_gen_start_installed(self, tmp_path):
        _install(tmp_path, ["--project-slug", "test_proj"])
        assert (tmp_path / ".claude" / "commands" / "gen-start.md").exists()

    def test_gen_iterate_installed(self, tmp_path):
        _install(tmp_path, ["--project-slug", "test_proj"])
        assert (tmp_path / ".claude" / "commands" / "gen-iterate.md").exists()

    def test_all_commands_installed(self, tmp_path):
        result = _install(tmp_path, ["--project-slug", "test_proj"])
        # 3 from abiogenesis + 2 from genesis_sdlc
        assert len(result["commands"]) == 5
        assert set(result["commands"]) == {
            "gen-start", "gen-gaps", "gen-status", "gen-iterate", "gen-review"
        }

    def test_stamp_file_written(self, tmp_path):
        _install(tmp_path, ["--project-slug", "test_proj"])
        stamp = tmp_path / ".claude" / "commands" / ".genesis-installed"
        assert stamp.exists()
        data = json.loads(stamp.read_text())
        assert data["version"] == "0.2.0"


# ── CLAUDE.md ─────────────────────────────────────────────────────────────────

class TestClaudeMd:
    def test_claude_md_created(self, tmp_path):
        result = _install(tmp_path, ["--project-slug", "test_proj"])
        assert result["claude_md"] == "created"
        assert (tmp_path / "CLAUDE.md").exists()

    def test_bootloader_injected(self, tmp_path):
        _install(tmp_path, ["--project-slug", "test_proj"])
        text = (tmp_path / "CLAUDE.md").read_text()
        assert "<!-- GENESIS_BOOTLOADER_START -->" in text
        assert "<!-- GENESIS_BOOTLOADER_END -->" in text

    def test_reinstall_updates_bootloader(self, tmp_path):
        """Bootloader section is always replaced on reinstall."""
        _install(tmp_path, ["--project-slug", "test_proj"])
        result = _install(tmp_path, ["--project-slug", "test_proj"])
        assert result["claude_md"] == "updated"

    def test_existing_claude_md_content_preserved(self, tmp_path):
        """User content outside bootloader markers is not clobbered."""
        _install(tmp_path, ["--project-slug", "test_proj"])
        claude_md = tmp_path / "CLAUDE.md"
        existing = claude_md.read_text()
        # Inject user content after the bootloader end marker
        claude_md.write_text(existing + "\n# My project notes\n")
        _install(tmp_path, ["--project-slug", "test_proj"])
        assert "My project notes" in claude_md.read_text()


# ── Verify ────────────────────────────────────────────────────────────────────

class TestVerify:
    def test_verify_ok_after_install(self, tmp_path):
        _install(tmp_path, ["--project-slug", "test_proj"])
        result = _install(tmp_path, ["--project-slug", "test_proj", "--verify"])
        assert result["status"] == "ok"
        assert result["missing"] == []

    def test_verify_incomplete_without_install(self, tmp_path):
        result = subprocess.run(
            [sys.executable, str(INSTALL_MODULE),
             "--target", str(tmp_path),
             "--source", str(PROJECT_ROOT),
             "--verify"],
            capture_output=True, text=True,
        )
        data = json.loads(result.stdout)
        assert data["status"] == "incomplete"
        assert len(data["missing"]) > 0


# ── End-to-end: engine boots after install ────────────────────────────────────

class TestEngineBootsAfterInstall:
    def test_gaps_runs_after_install(self, tmp_path):
        """After genesis_sdlc install, engine must boot and return a valid gaps report."""
        import os
        _install(tmp_path, ["--project-slug", "my_domain"])
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path / ".genesis")
        result = subprocess.run(
            [sys.executable, "-m", "genesis", "gaps", "--workspace", str(tmp_path)],
            capture_output=True, text=True, cwd=str(tmp_path), env=env,
        )
        assert result.returncode == 0, f"gaps failed:\n{result.stderr}"
        data = json.loads(result.stdout)
        assert data["scope"]["package"] == "my_domain"
        assert data["jobs_considered"] == 7  # full SDLC graph with module_decomp + UAT, not the stub
