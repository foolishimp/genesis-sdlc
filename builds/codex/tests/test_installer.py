# Validates: REQ-F-BOOT-001
# Validates: REQ-F-BOOT-002
# Validates: REQ-F-BOOT-003
# Validates: REQ-F-BOOT-004
# Validates: REQ-F-BOOT-005
# Validates: REQ-F-BOOT-006
"""Installer tests for the Codex genesis_sdlc build."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


BUILD_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = BUILD_ROOT.parents[1]
INSTALL_MODULE = BUILD_ROOT / "code" / "genesis_sdlc" / "install.py"
ABIOGENESIS_ROOT = PROJECT_ROOT.parent / "abiogenesis"
VERSION = "0.5.1"
VERSION_UNDERSCORED = VERSION.replace(".", "_")

pytestmark = pytest.mark.skipif(
    not ABIOGENESIS_ROOT.exists(),
    reason="abiogenesis sibling directory not found",
)


def _install(target: Path, extra_args: list[str] | None = None) -> dict:
    args = [
        sys.executable,
        str(INSTALL_MODULE),
        "--target",
        str(target),
        "--source",
        str(PROJECT_ROOT),
    ]
    if extra_args:
        args.extend(extra_args)
    result = subprocess.run(args, capture_output=True, text=True)
    assert result.stdout.strip(), result.stderr
    return json.loads(result.stdout)


def test_install_writes_engine_seed(tmp_path):
    result = _install(tmp_path, ["--project-slug", "my_proj"])
    assert result["status"] == "installed"
    assert (tmp_path / ".genesis" / "genesis" / "__main__.py").exists()
    assert (tmp_path / ".genesis" / "gtl" / "core.py").exists()
    assert (tmp_path / ".genesis" / "gtl_spec" / "packages" / "genesis_core.py").exists()


def test_install_writes_codex_genesis_yml(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    text = (tmp_path / ".genesis" / "genesis.yml").read_text(encoding="utf-8")
    assert "gtl_spec.packages.my_proj:package" in text
    assert "gtl_spec.packages.my_proj:worker" in text
    assert "builds/codex/code" in text


def test_workflow_release_and_wrapper_are_written(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    ver_dir = (
        tmp_path
        / ".genesis"
        / "workflows"
        / "genesis_sdlc"
        / "standard"
        / f"v{VERSION_UNDERSCORED}"
    )
    assert (ver_dir / "spec.py").exists()
    wrapper = tmp_path / ".genesis" / "gtl_spec" / "packages" / "my_proj.py"
    text = wrapper.read_text(encoding="utf-8")
    assert f"from workflows.genesis_sdlc.standard.v{VERSION_UNDERSCORED}.spec import instantiate" in text
    assert 'slug="my_proj"' in text


def test_installed_layer2_imports_and_rewrites_contexts(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path / ".genesis")
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from workflows.genesis_sdlc.standard.v{ver}.spec import instantiate; "
                "pkg, worker = instantiate('my_proj'); "
                "job = next(j for j in worker.can_execute if j.edge.name == 'requirements\\u2192feature_decomp'); "
                "ctx = next(c for c in job.edge.context if c.name == 'sdlc_spec'); "
                "ev = next(e for e in job.evaluators if e.name == 'req_coverage'); "
                "print(ctx.locator); print(ev.command)"
            ).format(ver=VERSION_UNDERSCORED),
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert ".genesis/gtl_spec/packages/my_proj.py" in result.stdout
    assert "gtl_spec.packages.my_proj:package" in result.stdout


def test_install_creates_private_and_shared_workspace_dirs(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    assert (tmp_path / "builds" / "codex" / ".workspace" / "manifests").is_dir()
    assert (tmp_path / "builds" / "codex" / ".workspace" / "iterations").is_dir()
    assert (tmp_path / ".ai-workspace" / "comments" / "codex").is_dir()
    assert (tmp_path / ".ai-workspace" / "backlog").is_dir()
    assert (tmp_path / ".ai-workspace" / "modules").is_dir()


def test_install_seeds_specification_surface(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    assert (tmp_path / "specification" / "INTENT.md").exists()
    assert (tmp_path / "specification" / "requirements.md").exists()
    assert (tmp_path / "specification" / "feature_decomposition.md").exists()


def test_install_commands_and_stamp(tmp_path):
    result = _install(tmp_path, ["--project-slug", "my_proj"])
    assert set(result["commands"]) == {"gen-start", "gen-gaps", "gen-status", "gen-iterate", "gen-review"}
    stamp = tmp_path / ".claude" / "commands" / ".genesis-installed"
    assert stamp.exists()
    assert json.loads(stamp.read_text(encoding="utf-8"))["version"] == VERSION


def test_claude_md_contains_both_bootloaders(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    text = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "<!-- GTL_BOOTLOADER_START -->" in text
    assert "<!-- SDLC_BOOTLOADER_START -->" in text
    assert text.index("<!-- GTL_BOOTLOADER_START -->") < text.index("<!-- SDLC_BOOTLOADER_START -->")
    assert "builds/codex/.workspace/" in text


def test_verify_ok_after_install(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    result = _install(tmp_path, ["--project-slug", "my_proj", "--verify"])
    assert result["status"] == "ok"
    assert result["missing"] == []


def test_audit_ok_after_install(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    result = _install(tmp_path, ["--project-slug", "my_proj", "--audit"])
    assert result["status"] == "ok", result["audit"]
    assert result["audit"]["summary"]["drifted"] == 0
    assert result["audit"]["summary"]["missing"] == 0


def test_audit_detects_command_drift(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    command = tmp_path / ".claude" / "commands" / "gen-iterate.md"
    command.write_text("tampered\n", encoding="utf-8")
    result = _install(tmp_path, ["--project-slug", "my_proj", "--audit"])
    assert result["status"] == "drift_detected"
    assert "command:gen-iterate" in result["audit"]["drifted"]


def test_genesis_gaps_runs_after_install(tmp_path):
    _install(tmp_path, ["--project-slug", "my_proj"])
    env = os.environ.copy()
    env["PYTHONPATH"] = str(tmp_path / ".genesis")
    result = subprocess.run(
        [sys.executable, "-m", "genesis", "gaps", "--workspace", str(tmp_path)],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env=env,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["scope"]["package"] == "my_proj"
    assert data["jobs_considered"] == 9
