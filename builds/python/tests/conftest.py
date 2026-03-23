# Validates: REQ-F-TEST-001
"""
Pytest conftest — provides the run_archive fixture for persistent forensic archives
and registers markers for the integration test suite.

Every scenario test receives a RunArchive that persists the full sandbox
workspace, subprocess logs, provenance, and artifacts at:
  tests/runs/<usecase_id>/<YYYYMMDDTHHMMSS_testname>/

The archive is finalized on test teardown regardless of pass/fail.
Failed runs are at least as valuable as passing runs.

NOTE: The session-scoped `sandbox` fixture for basic integration tests remains in
test_e2e_sandbox.py (inline). This conftest adds graph-walk integration fixtures
that do NOT conflict with the existing session fixture.
"""
import pytest
from scenario_helpers import create_run_archive



def pytest_configure(config):
    config.addinivalue_line("markers", "integration: integration and end-to-end sandbox tests")
    config.addinivalue_line("markers", "live_fp: live F_P qualification tests (requires ANTHROPIC_API_KEY)")


@pytest.fixture
def run_archive(request):
    """Persistent run archive for postmortem investigation.

    Yields a RunArchive with:
      .workspace  — Path to the sandbox directory (install target)
      .run_dir    — Path to the full archive directory
      .artifacts_dir — Path for copied manifests/results
      .log_subprocess(label, result) — log command output

    On teardown: writes run.json, summary.json, copies artifacts.
    """
    module_name = request.node.module.__name__
    usecase = module_name.split(".")[-1].replace("test_", "")
    test_name = request.node.name

    archive = create_run_archive(usecase, test_name)
    yield archive

    test_passed = not hasattr(request.node, "rep_call") or request.node.rep_call.passed
    archive.finalize(test_passed=test_passed)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test outcome on the item for the run_archive fixture to read."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
