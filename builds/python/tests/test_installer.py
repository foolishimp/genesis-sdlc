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

VERSION = "0.2.1"
VERSION_UNDERSCORED = VERSION.replace(".", "_")

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
    def test_starter_spec_imports_layer2(self, tmp_path):
        """Layer 3 spec must call instantiate() from the versioned workflow release."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec = (tmp_path / "gtl_spec" / "packages" / "my_proj.py").read_text()
        assert f"from workflows.genesis_sdlc.standard.v{VERSION_UNDERSCORED}.spec import instantiate" in spec
        assert "spec→output" not in spec

    def test_slug_substituted(self, tmp_path):
        _install(tmp_path, ["--project-slug", "acme_corp"])
        spec = (tmp_path / "gtl_spec" / "packages" / "acme_corp.py").read_text()
        assert 'slug="acme_corp"' in spec

    def test_req_coverage_references_slug(self, tmp_path):
        """instantiate(slug) must produce a req_coverage evaluator pointing at the project package."""
        import os
        _install(tmp_path, ["--project-slug", "acme_corp"])
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path / ".genesis")
        result = subprocess.run(
            [sys.executable, "-c",
             "import sys; sys.path.insert(0, 'gtl_spec'); "
             "from workflows.genesis_sdlc.standard.v{ver}.spec import instantiate; "
             "pkg, _ = instantiate(slug='acme_corp'); "
             "evs = [ev for j in [next(j for j in _.can_execute if j.edge.name == 'requirements\u2192feature_decomp')] for ev in j.evaluators if ev.name == 'req_coverage']; "
             "print(evs[0].command)".format(ver=VERSION_UNDERSCORED)],
            capture_output=True, text=True, env=env, cwd=str(tmp_path),
        )
        assert result.returncode == 0, f"instantiate import failed:\n{result.stderr}"
        assert "acme_corp" in result.stdout
        assert "genesis_sdlc" not in result.stdout

    def test_layer3_imports_layer2_at_runtime(self, tmp_path):
        """After install, the versioned Layer 2 spec must be importable from .genesis."""
        import os
        _install(tmp_path, ["--project-slug", "my_proj"])
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path / ".genesis")
        result = subprocess.run(
            [sys.executable, "-c",
             f"from workflows.genesis_sdlc.standard.v{VERSION_UNDERSCORED}.spec import package, worker; print('ok')"],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, (
            f"versioned workflow import failed — Layer 2 is not importable:\n{result.stderr}"
        )
        assert "ok" in result.stdout

    def test_platform_paths_in_layer2_not_layer3(self, tmp_path):
        """Platform-specific evaluator paths live in Layer 2; Layer 3 is platform-agnostic."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        layer3 = (tmp_path / "gtl_spec" / "packages" / "my_proj.py").read_text()
        layer2 = (
            tmp_path / ".genesis" / "workflows" / "genesis_sdlc"
            / "standard" / f"v{VERSION_UNDERSCORED}" / "spec.py"
        ).read_text()
        # Layer 3 is a two-line wrapper — no platform paths baked in
        assert "builds/python/src/" not in layer3
        # Layer 2 carries the evaluator commands with platform paths
        assert "builds/python/src/" in layer2

    def test_layer3_overrides_this_spec_context(self, tmp_path):
        """instantiate(slug) must produce an sdlc_spec context for the project's own spec."""
        import os
        _install(tmp_path, ["--project-slug", "my_proj"])
        env = os.environ.copy()
        env["PYTHONPATH"] = str(tmp_path / ".genesis")
        result = subprocess.run(
            [sys.executable, "-c",
             "from workflows.genesis_sdlc.standard.v{ver}.spec import instantiate; "
             "pkg, _ = instantiate(slug='my_proj'); "
             "ctx = next(c for c in pkg.contexts if c.name == 'sdlc_spec'); "
             "print(ctx.locator)".format(ver=VERSION_UNDERSCORED)],
            capture_output=True, text=True, env=env,
        )
        assert result.returncode == 0, f"instantiate context check failed:\n{result.stderr}"
        assert "my_proj.py" in result.stdout
        assert "genesis_sdlc.py" not in result.stdout

    def test_reinstall_does_not_clobber_customised_spec(self, tmp_path):
        """Once user has edited their spec (no stub marker), reinstall must not overwrite."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec_path = tmp_path / "gtl_spec" / "packages" / "my_proj.py"
        spec_path.write_text("# user customisation\n")
        result = _install(tmp_path, ["--project-slug", "my_proj"])
        assert result["sdlc_starter_spec"] == "already_customised"
        assert "user customisation" in spec_path.read_text()

    def test_reinstall_upgrades_genesis_sdlc_stub(self, tmp_path):
        """A genesis_sdlc-stub spec (auto-generated, not yet customised) is replaced on reinstall."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec_path = tmp_path / "gtl_spec" / "packages" / "my_proj.py"
        # Simulate an old install that still carries the genesis_sdlc-stub marker
        spec_path.write_text("# genesis_sdlc-stub — old generated content\npackage = None\n")
        result = _install(tmp_path, ["--project-slug", "my_proj"])
        assert result["sdlc_starter_spec"] == "installed"
        assert "genesis_sdlc-generated" in spec_path.read_text()
        assert f"from workflows.genesis_sdlc.standard.v{VERSION_UNDERSCORED}.spec import instantiate" in spec_path.read_text()

    def test_generated_wrapper_always_replaced(self, tmp_path):
        """A wrapper carrying genesis_sdlc-generated is always replaced on reinstall."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec_path = tmp_path / "gtl_spec" / "packages" / "my_proj.py"
        original = spec_path.read_text()
        assert "genesis_sdlc-generated" in original
        # Simulate drift (e.g. old version) — still carries the marker
        spec_path.write_text("# genesis_sdlc-generated — stale\npackage = None\n")
        result = _install(tmp_path, ["--project-slug", "my_proj"])
        assert result["sdlc_starter_spec"] == "installed"
        assert f"from workflows.genesis_sdlc.standard.v{VERSION_UNDERSCORED}.spec import instantiate" in spec_path.read_text()

    def test_reinstall_does_not_clobber_old_full_copy_spec(self, tmp_path):
        """A pre-0.2.0 full-copy spec without a stub marker is treated as user-owned."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec_path = tmp_path / "gtl_spec" / "packages" / "my_proj.py"
        # Simulate an old full-copy install: genesis_sdlc.py copied verbatim, no stub marker.
        # Ownership is ambiguous — the user may have edited it. Conservative policy: do not touch.
        # The only safe migration path is explicit: delete the file and reinstall.
        old_full_copy = (
            '""" genesis_sdlc — project spec as GTL Package """\n'
            'from gtl.core import Package, Context, Worker\n'
            'this_spec = Context(\n'
            '    name="genesis_sdlc_spec",\n'
            '    locator="workspace://gtl_spec/packages/genesis_sdlc.py",\n'
            '    digest="sha256:" + "0" * 64,\n'
            ')\n'
            'package = Package(name="my_proj")\n'
        )
        spec_path.write_text(old_full_copy)
        result = _install(tmp_path, ["--project-slug", "my_proj"])
        assert result["sdlc_starter_spec"] == "already_customised", (
            "Old full-copy spec without a stub marker must not be silently overwritten"
        )
        assert "from gtl.core import" in spec_path.read_text()


# ── Versioned workflow release (Layer 2) ──────────────────────────────────────

class TestWorkflowRelease:
    def _ver_dir(self, tmp_path):
        return tmp_path / ".genesis" / "workflows" / "genesis_sdlc" / "standard" / f"v{VERSION_UNDERSCORED}"

    def test_versioned_spec_written(self, tmp_path):
        """install_workflow_release must write spec.py into the versioned directory."""
        _install(tmp_path, ["--project-slug", "test_proj"])
        assert (self._ver_dir(tmp_path) / "spec.py").exists()

    def test_versioned_manifest_written(self, tmp_path):
        """install_workflow_release must write manifest.json alongside spec.py."""
        _install(tmp_path, ["--project-slug", "test_proj"])
        manifest_path = self._ver_dir(tmp_path) / "manifest.json"
        assert manifest_path.exists()
        data = json.loads(manifest_path.read_text())
        assert data["workflow"] == "genesis_sdlc.standard"
        assert data["version"] == VERSION

    def test_workflow_release_result_in_output(self, tmp_path):
        """install() result must include workflow_release field."""
        result = _install(tmp_path, ["--project-slug", "test_proj"])
        assert result["workflow_release"] in ("installed", "exists")

    def test_workflow_release_immutable_on_reinstall(self, tmp_path):
        """Versioned spec.py must not be overwritten on reinstall — it is immutable."""
        _install(tmp_path, ["--project-slug", "test_proj"])
        spec_path = self._ver_dir(tmp_path) / "spec.py"
        sentinel = "# SENTINEL — must survive reinstall\n"
        spec_path.write_text(sentinel + spec_path.read_text())
        result = _install(tmp_path, ["--project-slug", "test_proj"])
        assert result["workflow_release"] == "exists"
        assert sentinel in spec_path.read_text(), "Immutable versioned spec was overwritten"

    def test_init_py_files_created(self, tmp_path):
        """Workflow directories must have __init__.py so the package is importable."""
        _install(tmp_path, ["--project-slug", "test_proj"])
        genesis_root = tmp_path / ".genesis"
        assert (genesis_root / "workflows" / "__init__.py").exists()
        assert (genesis_root / "workflows" / "genesis_sdlc" / "__init__.py").exists()
        assert (genesis_root / "workflows" / "genesis_sdlc" / "standard" / "__init__.py").exists()
        assert (self._ver_dir(tmp_path) / "__init__.py").exists()

    def test_active_workflow_json_written(self, tmp_path):
        """install_active_workflow must write .genesis/active-workflow.json."""
        result = _install(tmp_path, ["--project-slug", "test_proj"])
        assert result["active_workflow"] == "installed"
        active_path = tmp_path / ".genesis" / "active-workflow.json"
        assert active_path.exists()
        data = json.loads(active_path.read_text())
        assert data["workflow"] == "genesis_sdlc.standard"
        assert data["version"] == VERSION
        assert "standard" in data["spec_module"]
        assert f"v{VERSION_UNDERSCORED}" in data["spec_module"]

    def test_active_workflow_json_updated_on_reinstall(self, tmp_path):
        """active-workflow.json must be refreshed on every reinstall."""
        _install(tmp_path, ["--project-slug", "test_proj"])
        result = _install(tmp_path, ["--project-slug", "test_proj"])
        assert result["active_workflow"] == "installed"


# ── Migration (--migrate-full-copy) ───────────────────────────────────────────

class TestMigration:
    def test_migrate_full_copy_moves_legacy_spec(self, tmp_path):
        """--migrate-full-copy must rename the old file and write a new generated wrapper."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        spec_path = tmp_path / "gtl_spec" / "packages" / "my_proj.py"
        # Simulate pre-0.2.0 full-copy (no marker)
        spec_path.write_text("# user spec — no marker\npackage = None\n")
        result = _install(tmp_path, ["--project-slug", "my_proj", "--migrate-full-copy"])
        assert result["status"] == "migrated"
        assert "legacy_path" in result
        legacy = tmp_path / "gtl_spec" / "packages" / Path(result["legacy_path"]).name
        assert legacy.exists()
        assert "user spec" in legacy.read_text()
        # New wrapper must be in place
        assert "genesis_sdlc-generated" in spec_path.read_text()

    def test_migrate_already_generated_is_noop(self, tmp_path):
        """--migrate-full-copy on a genesis_sdlc-generated wrapper is a no-op."""
        _install(tmp_path, ["--project-slug", "my_proj"])
        result = _install(tmp_path, ["--project-slug", "my_proj", "--migrate-full-copy"])
        assert result["status"] == "already_migrated"


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
        assert data["version"] == VERSION


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
        assert data["jobs_considered"] == 9  # full SDLC graph with integration_tests + user_guide, not the stub
