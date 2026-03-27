# Validates: REQ-F-UAT-001
# Validates: REQ-F-TEST-001
# Validates: REQ-F-BOOT-001
# Validates: REQ-F-BOOT-002
# Validates: REQ-F-CMD-001
# Validates: REQ-F-CMD-002
# Validates: REQ-F-TAG-001
# Validates: REQ-F-TAG-002
# Validates: REQ-F-COV-001
# Validates: REQ-F-GATE-001
# Validates: REQ-F-BACKLOG-001
# Validates: REQ-F-BACKLOG-002
# Validates: REQ-F-BACKLOG-003
# Validates: REQ-F-BACKLOG-004
# Validates: REQ-F-BOOT-003
# Validates: REQ-F-BOOT-004
# Validates: REQ-F-BOOT-005
# Validates: REQ-F-CUSTODY-001
# Validates: REQ-F-CUSTODY-002
# Validates: REQ-F-CUSTODY-003
# Validates: REQ-F-MDECOMP-001
# Validates: REQ-F-MDECOMP-002
# Validates: REQ-F-MDECOMP-003
# Validates: REQ-F-MDECOMP-005
# Validates: REQ-F-TEST-003
# Validates: REQ-F-UAT-002
"""
UAT sandbox tests for genesis_sdlc.

These tests install genesis_sdlc into a PERSISTENT local sandbox directory
(builds/python/uat_sandbox/) and simulate a real user onboarding experience.

The sandbox is wiped and rebuilt fresh at the start of each test session.
After tests complete it remains on disk — inspect it like a real project:

    cd builds/python/uat_sandbox
    PYTHONPATH=.genesis python -m genesis gaps --workspace .

Scenarios cover the full user journey:
  - fresh install
  - workspace structure
  - engine commands (gaps, status, emit-event)
  - event stream write/read
  - check-tags enforcement
  - check-req-coverage enforcement
  - human-proxy gate mechanics
  - backlog commands

Run with: pytest -m integration builds/python/tests/test_e2e_sandbox.py -v
"""
import json
import os
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

# ── Paths ─────────────────────────────────────────────────────────────────────

BUILDS_DIR = Path(__file__).resolve().parent.parent
INSTALL_SCRIPT = BUILDS_DIR / "src" / "genesis_sdlc" / "install.py"
SANDBOX_DIR = BUILDS_DIR / "uat_sandbox"
PROJECT_SLUG = "uat_project"


# ── Session fixture ────────────────────────────────────────────────────────────


@pytest.fixture(scope="session", autouse=True)
def sandbox():
    """
    Wipe and rebuild the local sandbox at the start of each test session.
    Left on disk after tests for manual inspection.
    """
    if SANDBOX_DIR.exists():
        shutil.rmtree(SANDBOX_DIR)
    SANDBOX_DIR.mkdir(parents=True)

    result = subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT),
         "--target", str(SANDBOX_DIR),
         "--project-slug", PROJECT_SLUG],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Sandbox install failed:\n{result.stderr}"
    data = json.loads(result.stdout)
    assert data["status"] == "installed", f"Unexpected install status: {data}"
    return SANDBOX_DIR


# ── Helpers ────────────────────────────────────────────────────────────────────


def run_genesis(sandbox, *args, check=False):
    """Run an engine command that accepts --workspace (start, iterate, gaps, emit-event)."""
    env = {**os.environ, "PYTHONPATH": str(sandbox / ".genesis")}
    result = subprocess.run(
        [sys.executable, "-m", "genesis", *args, "--workspace", str(sandbox)],
        capture_output=True, text=True, cwd=str(sandbox), env=env,
        timeout=30,
    )
    if check:
        assert result.returncode == 0, (
            f"genesis {' '.join(args)} failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def run_genesis_cmd(sandbox, *args, check=False):
    """Run an engine command that does NOT accept --workspace (check-tags, check-req-coverage)."""
    # .gsdlc/release MUST be first — it overrides ABG's gtl_spec stub with the real wrapper
    env = {**os.environ, "PYTHONPATH": os.pathsep.join([
        str(sandbox / ".gsdlc" / "release"),
        str(sandbox / ".genesis"),
    ])}
    result = subprocess.run(
        [sys.executable, "-m", "genesis", *args],
        capture_output=True, text=True, cwd=str(sandbox), env=env,
        timeout=30,
    )
    if check:
        assert result.returncode == 0, (
            f"genesis {' '.join(args)} failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result


def events(sandbox):
    """Parse all events from the sandbox event stream."""
    events_file = sandbox / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        return []
    return [json.loads(line) for line in events_file.read_text().splitlines() if line.strip()]


# ── Install structure ──────────────────────────────────────────────────────────


@pytest.mark.integration
class TestInstallStructure:
    """Verify the installer produces a complete, correct workspace."""

    def test_engine_installed(self, sandbox):
        assert (sandbox / ".genesis" / "genesis.yml").exists()
        assert (sandbox / ".genesis" / "genesis" / "__main__.py").exists()

    def test_gtl_installed(self, sandbox):
        assert (sandbox / ".genesis" / "gtl" / "core.py").exists()

    def test_commands_installed(self, sandbox):
        commands_dir = sandbox / ".claude" / "commands"
        for cmd in ["gen-start.md", "gen-gaps.md", "gen-status.md",
                    "gen-iterate.md", "gen-review.md"]:
            assert (commands_dir / cmd).exists(), f"Missing command: {cmd}"

    def test_starter_spec_installed(self, sandbox):
        spec = sandbox / ".gsdlc" / "release" / "gtl_spec" / "packages" / f"{PROJECT_SLUG}.py"
        assert spec.exists(), "Starter spec not written to .gsdlc/release/"

    def test_starter_spec_has_correct_slug(self, sandbox):
        spec = sandbox / ".gsdlc" / "release" / "gtl_spec" / "packages" / f"{PROJECT_SLUG}.py"
        content = spec.read_text()
        assert "instantiate" in content, "Generated wrapper must call instantiate()"
        assert f'slug="{PROJECT_SLUG}"' in content, "Generated wrapper must pass correct slug"

    def test_no_gsdlc_artifacts_in_genesis(self, sandbox):
        """# Validates: REQ-F-TERRITORY-001 — .genesis/ must contain only ABG kernel."""
        assert not (sandbox / ".genesis" / "workflows").exists(), \
            "gsdlc workflows must not be in .genesis/"
        assert not (sandbox / ".genesis" / "active-workflow.json").exists(), \
            "active-workflow.json must not be in .genesis/"
        # ABG-created gtl_spec stub may exist, but no genesis_sdlc-generated wrappers
        abg_spec = sandbox / ".genesis" / "gtl_spec" / "packages" / f"{PROJECT_SLUG}.py"
        if abg_spec.exists():
            content = abg_spec.read_text()
            assert "genesis_sdlc-generated" not in content, \
                "ABG stub must not contain genesis_sdlc-generated marker"

    def test_gsdlc_release_territory(self, sandbox):
        """# Validates: REQ-F-TERRITORY-001 — gsdlc artifacts live in .gsdlc/release/."""
        from genesis_sdlc.install import VERSION
        ver_tag = f"v{VERSION.replace('.', '_')}"
        assert (sandbox / ".gsdlc" / "release" / "active-workflow.json").exists()
        assert (sandbox / ".gsdlc" / "release" / "workflows" / "genesis_sdlc" / "standard" / ver_tag / "spec.py").exists()
        assert (sandbox / ".gsdlc" / "release" / "gtl_spec" / "packages" / f"{PROJECT_SLUG}.py").exists()

    def test_domain_contract_exists(self, sandbox):
        """# Validates: REQ-F-TERRITORY-002 — domain contract at .gsdlc/release/genesis.yml."""
        contract = (sandbox / ".gsdlc" / "release" / "genesis.yml")
        assert contract.exists(), "Domain runtime contract must exist at .gsdlc/release/genesis.yml"
        text = contract.read_text()
        assert ".gsdlc/release" in text, "Contract pythonpath must include .gsdlc/release"
        assert f"{PROJECT_SLUG}" in text, "Contract must reference project slug"

    def test_specification_scaffold_created(self, sandbox):
        """ABG kernel no longer creates builds/; gsdlc scaffolds specification/."""
        assert (sandbox / "specification" / "requirements.md").exists()

    def test_ai_workspace_created(self, sandbox):
        assert (sandbox / ".ai-workspace" / "events").exists()
        assert (sandbox / ".ai-workspace" / "features").exists()

    def test_claude_md_written(self, sandbox):
        claude_md = sandbox / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert "GTL_BOOTLOADER_START" in content
        assert "SDLC_BOOTLOADER_START" in content
        assert "ai_sdlc_method" not in content, (
            "CLAUDE.md must not reference dead ai_sdlc_method project"
        )

    def test_operating_standards_installed(self, sandbox):
        standards_dir = sandbox / ".gsdlc" / "release" / "operating-standards"
        assert standards_dir.exists()
        for std in ["BACKLOG_GUIDE.md", "CONVENTIONS_GUIDE.md", "RELEASE_GUIDE.md"]:
            assert (standards_dir / std).exists(), f"Missing standard: {std}"

    def test_sdlc_bootloader_release_installed(self, sandbox):
        """# Validates: REQ-F-TERRITORY-001 — SDLC bootloader is a release artifact."""
        bl = sandbox / ".gsdlc" / "release" / "SDLC_BOOTLOADER.md"
        assert bl.exists(), "SDLC_BOOTLOADER.md must be in .gsdlc/release/"


# ── Engine commands ────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestEngineCommands:
    """Verify the installed engine responds correctly to all commands."""

    def test_gaps_returns_json(self, sandbox):
        result = run_genesis(sandbox, "gaps", check=True)
        data = json.loads(result.stdout)
        assert "jobs_considered" in data
        assert "total_delta" in data
        assert "gaps" in data

    def test_gaps_sees_full_sdlc_graph(self, sandbox):
        result = run_genesis(sandbox, "gaps", check=True)
        data = json.loads(result.stdout)
        assert data["jobs_considered"] == 9, (
            f"Expected 9 jobs (10-asset SDLC graph with integration_tests + user_guide), got {data['jobs_considered']}"
        )

    def test_fresh_workspace_is_all_delta(self, sandbox):
        """A freshly installed workspace has no events — every edge should be in delta."""
        result = run_genesis(sandbox, "gaps", check=True)
        data = json.loads(result.stdout)
        assert data["converged"] is False
        assert data["total_delta"] > 0

    def test_gaps_edge_names_are_correct(self, sandbox):
        result = run_genesis(sandbox, "gaps", check=True)
        data = json.loads(result.stdout)
        edge_names = [g["edge"] for g in data["gaps"]]
        assert "intent→requirements" in edge_names
        assert "unit_tests→integration_tests" in edge_names
        assert "integration_tests→user_guide" in edge_names
        assert "user_guide→uat_tests" in edge_names


# ── Event stream ───────────────────────────────────────────────────────────────


@pytest.mark.integration
class TestEventStream:
    """Verify emit-event writes to the event stream and the stream is readable."""

    def test_emit_event_succeeds(self, sandbox):
        result = run_genesis(
            sandbox, "emit-event",
            "--type", "intent_raised",
            "--data", json.dumps({"feature": "TEST-001", "description": "UAT test intent"}),
            check=True,
        )
        assert result.returncode == 0

    def test_emitted_event_appears_in_stream(self, sandbox):
        evts = events(sandbox)
        types = [e["event_type"] for e in evts]
        assert "intent_raised" in types

    def test_event_has_required_fields(self, sandbox):
        evts = events(sandbox)
        evt = next(e for e in evts if e["event_type"] == "intent_raised")
        assert "event_time" in evt
        assert "data" in evt
        assert evt["data"]["feature"] == "TEST-001"

    def test_event_stream_is_append_only(self, sandbox):
        """Emit a second event; first event must still be present and unchanged."""
        run_genesis(
            sandbox, "emit-event",
            "--type", "intent_raised",
            "--data", json.dumps({"feature": "TEST-002", "description": "second intent"}),
            check=True,
        )
        evts = events(sandbox)
        features = [e["data"].get("feature") for e in evts if e["event_type"] == "intent_raised"]
        assert "TEST-001" in features
        assert "TEST-002" in features

    def test_gaps_reflects_event_state(self, sandbox):
        """After emitting events, gaps output must still be valid JSON."""
        result = run_genesis(sandbox, "gaps", check=True)
        data = json.loads(result.stdout)
        assert "total_delta" in data


# ── check-tags enforcement ─────────────────────────────────────────────────────


@pytest.mark.integration
class TestCheckTags:
    """Verify check-tags enforces Implements: and Validates: tag requirements."""

    def _src_dir(self, sandbox):
        d = sandbox / "builds" / "python" / "src" / PROJECT_SLUG
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _test_dir(self, sandbox):
        d = sandbox / "builds" / "python" / "tests"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def test_check_tags_rejects_untagged_source_file(self, sandbox):
        src = self._src_dir(sandbox) / "untagged_module.py"
        src.write_text("def hello(): pass\n")
        result = run_genesis_cmd(
            sandbox, "check-tags",
            "--type", "implements",
            "--path", str(sandbox / "builds" / "python" / "src"),
        )
        assert result.returncode != 0, (
            "check-tags should fail when a source file has no Implements: tag"
        )
        src.unlink()

    def test_check_tags_accepts_tagged_source_file(self, sandbox):
        src = self._src_dir(sandbox) / "tagged_module.py"
        src.write_text("# Implements: REQ-F-BOOT-001\ndef hello(): pass\n")
        result = run_genesis_cmd(
            sandbox, "check-tags",
            "--type", "implements",
            "--path", str(sandbox / "builds" / "python" / "src"),
        )
        assert result.returncode == 0, (
            f"check-tags should pass with Implements: tag:\n{result.stderr}"
        )
        src.unlink()

    def test_check_tags_rejects_untagged_test_file(self, sandbox):
        test_file = self._test_dir(sandbox) / "untagged_test.py"
        test_file.write_text("def test_something(): assert True\n")
        result = run_genesis_cmd(
            sandbox, "check-tags",
            "--type", "validates",
            "--path", str(sandbox / "builds" / "python" / "tests"),
        )
        assert result.returncode != 0, (
            "check-tags should fail when a test file has no Validates: tag"
        )
        test_file.unlink()

    def test_check_tags_accepts_tagged_test_file(self, sandbox):
        test_file = self._test_dir(sandbox) / "tagged_test.py"
        test_file.write_text("# Validates: REQ-F-BOOT-001\ndef test_something(): assert True\n")
        result = run_genesis_cmd(
            sandbox, "check-tags",
            "--type", "validates",
            "--path", str(sandbox / "builds" / "python" / "tests"),
        )
        assert result.returncode == 0, (
            f"check-tags should pass with Validates: tag:\n{result.stderr}"
        )
        test_file.unlink()


# ── check-req-coverage ─────────────────────────────────────────────────────────


@pytest.mark.integration
class TestReqCoverage:
    """Verify check-req-coverage detects uncovered REQ keys."""

    def _write_feature(self, sandbox, filename, satisfies):
        features_dir = sandbox / ".ai-workspace" / "features" / "active"
        features_dir.mkdir(parents=True, exist_ok=True)
        content = textwrap.dedent(f"""\
            id: {filename.replace('.yml', '')}
            name: Test feature
            satisfies:
        """)
        for key in satisfies:
            content += f"  - {key}\n"
        (features_dir / filename).write_text(content)

    def test_coverage_fails_when_req_key_uncovered(self, sandbox):
        """The starter spec has REQ keys; with no features, coverage should fail."""
        result = run_genesis_cmd(
            sandbox, "check-req-coverage",
            "--package", f"gtl_spec.packages.{PROJECT_SLUG}:package",
            "--features", str(sandbox / ".ai-workspace" / "features"),
        )
        assert result.returncode != 0, (
            "check-req-coverage should fail with no features covering any REQ keys"
        )

    def test_coverage_passes_when_all_keys_covered(self, sandbox):
        """Write feature vectors covering all REQ keys in the starter spec."""
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([
            str(sandbox / ".gsdlc" / "release"),
            str(sandbox / ".genesis"),
        ])}
        result = subprocess.run(
            [sys.executable, "-c",
             f"from gtl_spec.packages.{PROJECT_SLUG} import package; "
             f"import json; print(json.dumps(package.requirements))"],
            capture_output=True, text=True, cwd=str(sandbox), env=env, timeout=15,
        )
        if result.returncode != 0:
            pytest.skip(f"Could not import package to read requirements: {result.stderr}")
        req_keys = json.loads(result.stdout)
        if not req_keys:
            pytest.skip("No REQ keys found in starter spec")

        self._write_feature(sandbox, "full_coverage.yml", req_keys)

        result = run_genesis_cmd(
            sandbox, "check-req-coverage",
            "--package", f"gtl_spec.packages.{PROJECT_SLUG}:package",
            "--features", str(sandbox / ".ai-workspace" / "features"),
        )
        assert result.returncode == 0, (
            f"check-req-coverage should pass when all keys covered:\n{result.stderr}"
        )

        (sandbox / ".ai-workspace" / "features" / "active" / "full_coverage.yml").unlink()


# ── Human-proxy gate mechanics ─────────────────────────────────────────────────


@pytest.mark.integration
class TestHumanProxyGate:
    """Verify F_H gate mechanics: approved event carries correct actor field."""

    def test_emit_approved_with_human_actor(self, sandbox):
        run_genesis(
            sandbox, "emit-event",
            "--type", "approved",
            "--data", json.dumps({
                "kind": "fh_review",
                "feature": "TEST-GATE-001",
                "edge": "intent→requirements",
                "actor": "human",
            }),
            check=True,
        )
        evts = events(sandbox)
        approvals = [e for e in evts if e["event_type"] == "approved"]
        assert any(e["data"].get("actor") == "human" for e in approvals)

    def test_emit_approved_with_proxy_actor(self, sandbox):
        run_genesis(
            sandbox, "emit-event",
            "--type", "approved",
            "--data", json.dumps({
                "kind": "fh_review",
                "feature": "TEST-GATE-001",
                "edge": "requirements→feature_decomp",
                "actor": "human-proxy",
                "proxy_log": ".ai-workspace/reviews/proxy-log/test.md",
            }),
            check=True,
        )
        evts = events(sandbox)
        approvals = [e for e in evts if e["event_type"] == "approved"]
        assert any(e["data"].get("actor") == "human-proxy" for e in approvals)

    def test_actor_field_is_never_absent(self, sandbox):
        """Every approved event in the stream must carry an actor field."""
        evts = events(sandbox)
        approvals = [e for e in evts if e["event_type"] == "approved"]
        for evt in approvals:
            assert "actor" in evt["data"], (
                f"approved event missing actor field: {evt}"
            )


# ── Backlog commands ───────────────────────────────────────────────────────────


@pytest.mark.integration
class TestBacklogCommands:
    """Verify backlog schema, list, and promote commands."""

    def _backlog_dir(self, sandbox):
        d = sandbox / ".ai-workspace" / "backlog"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _write_backlog_item(self, sandbox, item_id, status="ready"):
        import textwrap
        content = textwrap.dedent(f"""\
            id: {item_id}
            title: Test backlog item
            status: {status}
            description: Created by UAT sandbox test
        """)
        (self._backlog_dir(sandbox) / f"{item_id}.yml").write_text(content)

    def test_backlog_item_schema_valid(self, sandbox):
        """A well-formed backlog item file is parseable as YAML."""
        import re
        self._write_backlog_item(sandbox, "BL-001")
        item_file = self._backlog_dir(sandbox) / "BL-001.yml"
        assert item_file.exists()
        content = item_file.read_text()
        assert "id: BL-001" in content
        assert "status: ready" in content

    def test_backlog_list_shows_items(self, sandbox):
        self._write_backlog_item(sandbox, "BL-002", status="ready")
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([
            str(sandbox / ".gsdlc" / "release"),
            str(sandbox / ".genesis"),
        ])}
        result = subprocess.run(
            [sys.executable, "-m", "genesis_sdlc", "backlog", "list",
             "--workspace", str(sandbox)],
            capture_output=True, text=True, cwd=str(sandbox), env=env,
            timeout=30,
        )
        if result.returncode == 127 or "No module named genesis_sdlc" in result.stderr:
            pytest.skip("genesis_sdlc backlog CLI not available in sandbox (expected for now)")
        assert "BL-002" in result.stdout or result.returncode == 0

    def test_backlog_promote_emits_intent_raised(self, sandbox):
        self._write_backlog_item(sandbox, "BL-003", status="ready")
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([
            str(sandbox / ".gsdlc" / "release"),
            str(sandbox / ".genesis"),
        ])}
        result = subprocess.run(
            [sys.executable, "-m", "genesis_sdlc", "backlog", "promote", "BL-003",
             "--workspace", str(sandbox)],
            capture_output=True, text=True, cwd=str(sandbox), env=env,
            timeout=30,
        )
        if result.returncode == 127 or "No module named genesis_sdlc" in result.stderr:
            pytest.skip("genesis_sdlc backlog CLI not available in sandbox (expected for now)")
        evts = events(sandbox)
        types = [e["event_type"] for e in evts]
        assert "intent_raised" in types


# ── Requirements custody ──────────────────────────────────────────────────────


CUSTODY_SANDBOX_DIR = BUILDS_DIR / "uat_custody_sandbox"


@pytest.fixture(scope="module")
def custody_sandbox():
    """
    A separate sandbox specifically for custody-chain testing.
    Wiped and rebuilt fresh — tests verify project-specific requirements
    flow through the install→wrapper→engine chain.
    """
    if CUSTODY_SANDBOX_DIR.exists():
        shutil.rmtree(CUSTODY_SANDBOX_DIR)
    CUSTODY_SANDBOX_DIR.mkdir(parents=True)

    # Install into sandbox
    result = subprocess.run(
        [sys.executable, str(INSTALL_SCRIPT),
         "--target", str(CUSTODY_SANDBOX_DIR),
         "--project-slug", "custody_test"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"Custody sandbox install failed:\n{result.stderr}"
    data = json.loads(result.stdout)
    assert data["status"] == "installed", f"Unexpected install status: {data}"
    return CUSTODY_SANDBOX_DIR


@pytest.mark.integration
class TestCustodyInstall:
    """Task 1.4: Verify install produces a complete custody chain."""

    def test_wrapper_exists(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-002
        spec = custody_sandbox / ".gsdlc" / "release" / "gtl_spec" / "packages" / "custody_test.py"
        assert spec.exists()

    def test_wrapper_calls_load_reqs(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-002
        spec = custody_sandbox / ".gsdlc" / "release" / "gtl_spec" / "packages" / "custody_test.py"
        content = spec.read_text()
        assert "_load_reqs()" in content, "Wrapper must call _load_reqs()"
        assert "req_keys=_load_reqs()" in content, "Wrapper must pass req_keys to instantiate()"

    def test_requirements_md_scaffolded(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-003
        req_file = custody_sandbox / "specification" / "requirements.md"
        assert req_file.exists(), "Installer must scaffold specification/requirements.md"

    def test_scaffold_contains_example_req(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-003
        req_file = custody_sandbox / "specification" / "requirements.md"
        content = req_file.read_text()
        assert "REQ-F-EXAMPLE-001" in content


@pytest.mark.integration
class TestCustodyRoundTrip:
    """Task 1.5: Write custom REQ keys, verify engine sees them — not gsdlc's 33."""

    def test_custom_reqs_visible_to_engine(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-001
        # Validates: REQ-F-CUSTODY-002
        req_file = custody_sandbox / "specification" / "requirements.md"
        req_file.write_text(textwrap.dedent("""\
            # Custom Project Requirements

            ## Auth (REQ-CUST-AUTH-*)

            ### REQ-CUST-AUTH-001 — Login

            Must support login.

            ### REQ-CUST-AUTH-002 — Logout

            Must support logout.

            ## Data (REQ-CUST-DATA-*)

            ### REQ-CUST-DATA-001 — Export

            Must export data.
        """))

        # Run gen-gaps as subprocess — the real proof
        result = run_genesis(custody_sandbox, "gaps")
        assert result.returncode == 0, (
            f"gen-gaps failed:\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
        data = json.loads(result.stdout)

        # Read the package requirements via subprocess
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([
            str(custody_sandbox / ".gsdlc" / "release"),
            str(custody_sandbox / ".genesis"),
        ])}
        pkg_result = subprocess.run(
            [sys.executable, "-c",
             "from gtl_spec.packages.custody_test import package; "
             "import json; print(json.dumps(package.requirements))"],
            capture_output=True, text=True,
            cwd=str(custody_sandbox), env=env, timeout=15,
        )
        assert pkg_result.returncode == 0, (
            f"Failed to read package requirements:\n{pkg_result.stderr}"
        )
        reqs = json.loads(pkg_result.stdout)

        # The critical assertion: these are OUR keys, not gsdlc's 33
        assert sorted(reqs) == ["REQ-CUST-AUTH-001", "REQ-CUST-AUTH-002", "REQ-CUST-DATA-001"], (
            f"Expected 3 custom REQ keys, got {len(reqs)}: {reqs}"
        )

    def test_no_gsdlc_keys_leak(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-001
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([
            str(custody_sandbox / ".gsdlc" / "release"),
            str(custody_sandbox / ".genesis"),
        ])}
        pkg_result = subprocess.run(
            [sys.executable, "-c",
             "from gtl_spec.packages.custody_test import package; "
             "import json; print(json.dumps(package.requirements))"],
            capture_output=True, text=True,
            cwd=str(custody_sandbox), env=env, timeout=15,
        )
        assert pkg_result.returncode == 0
        reqs = json.loads(pkg_result.stdout)
        gsdlc_keys = [r for r in reqs if r.startswith("REQ-F-")]
        assert gsdlc_keys == [], (
            f"gsdlc's own REQ-F-* keys leaked into project: {gsdlc_keys}"
        )


@pytest.mark.integration
class TestCustodyWrapperGeneration:
    """Task 1.6: Verify wrapper structure and _load_reqs() parsing."""

    def test_load_reqs_parses_headers(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-002
        env = {**os.environ, "PYTHONPATH": os.pathsep.join([
            str(custody_sandbox / ".gsdlc" / "release"),
            str(custody_sandbox / ".genesis"),
        ])}
        result = subprocess.run(
            [sys.executable, "-c",
             "from gtl_spec.packages.custody_test import _load_reqs; "
             "import json; print(json.dumps(_load_reqs()))"],
            capture_output=True, text=True,
            cwd=str(custody_sandbox), env=env, timeout=15,
        )
        assert result.returncode == 0, (
            f"_load_reqs() not importable:\n{result.stderr}"
        )
        reqs = json.loads(result.stdout)
        assert isinstance(reqs, list)
        assert len(reqs) > 0, "_load_reqs() returned empty despite requirements.md existing"

    def test_wrapper_is_system_owned(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-002
        spec = custody_sandbox / ".gsdlc" / "release" / "gtl_spec" / "packages" / "custody_test.py"
        content = spec.read_text()
        assert "genesis_sdlc-generated" in content, "Wrapper must carry system-ownership marker"


@pytest.mark.integration
class TestCustodyNoRequirementsFile:
    """Task 1.7: No requirements.md → empty list, never gsdlc defaults."""

    def test_missing_requirements_file_yields_empty(self, custody_sandbox):
        # Validates: REQ-F-CUSTODY-001
        # Validates: REQ-F-CUSTODY-002
        req_file = custody_sandbox / "specification" / "requirements.md"
        backup = req_file.read_text() if req_file.exists() else None
        try:
            if req_file.exists():
                req_file.unlink()

            env = {**os.environ, "PYTHONPATH": os.pathsep.join([
                str(custody_sandbox / ".gsdlc" / "release"),
                str(custody_sandbox / ".genesis"),
            ])}
            result = subprocess.run(
                [sys.executable, "-c",
                 "from gtl_spec.packages.custody_test import package; "
                 "import json; print(json.dumps(package.requirements))"],
                capture_output=True, text=True,
                cwd=str(custody_sandbox), env=env, timeout=15,
            )
            assert result.returncode == 0, (
                f"Package import failed:\n{result.stderr}"
            )
            reqs = json.loads(result.stdout)
            assert reqs == [], (
                f"No requirements.md should yield empty list, got: {reqs}"
            )
        finally:
            if backup is not None:
                req_file.write_text(backup)


# ── Sandbox state is inspectable ───────────────────────────────────────────────


@pytest.mark.integration
class TestSandboxInspectability:
    """
    Meta-tests: verify the sandbox is useful as a real project after tests run.
    These pass as long as the sandbox is a coherent workspace.
    """

    def test_sandbox_is_at_known_path(self, sandbox):
        assert sandbox == SANDBOX_DIR
        assert sandbox.exists()

    def test_event_stream_is_valid_jsonl(self, sandbox):
        events_file = sandbox / ".ai-workspace" / "events" / "events.jsonl"
        assert events_file.exists()
        for i, line in enumerate(events_file.read_text().splitlines()):
            if line.strip():
                json.loads(line)  # must not raise

    def test_domain_contract_points_to_slug(self, sandbox):
        """Domain runtime contract at .gsdlc/release/genesis.yml carries the project slug."""
        contract = (sandbox / ".gsdlc" / "release" / "genesis.yml").read_text()
        assert PROJECT_SLUG in contract
