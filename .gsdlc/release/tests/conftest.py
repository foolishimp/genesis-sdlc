# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-004
# Validates: REQ-F-ASSURE-002
"""Pytest markers for the Abiogenesis/Python tenant tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest


_TESTS_DIR = Path(__file__).resolve().parent
_VARIANT_SRC = _TESTS_DIR.parent / "src"
if str(_VARIANT_SRC) not in sys.path:
    sys.path.insert(0, str(_VARIANT_SRC))
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from run_archive import create_run_archive


def _report_outcome(node: pytest.Item) -> tuple[bool, str, str | None, str | None]:
    setup = getattr(node, "rep_setup", None)
    call = getattr(node, "rep_call", None)
    teardown = getattr(node, "rep_teardown", None)

    for stage, report in (("setup", setup), ("call", call), ("teardown", teardown)):
        if report is None:
            continue
        if report.failed:
            reason = getattr(report, "longreprtext", None) or str(getattr(report, "longrepr", ""))
            return False, "failed", stage, reason.strip() or None
        if report.skipped:
            reason = getattr(report, "longreprtext", None) or str(getattr(report, "longrepr", ""))
            return False, "skipped", stage, reason.strip() or None
    return True, "passed", "call" if call is not None else None, None


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "e2e: sandbox end-to-end workflow test")
    config.addinivalue_line("markers", "live_fp: live F_P qualification tests (requires agent CLI)")
    config.addinivalue_line("markers", "usecase_id(name): stable run-archive grouping for postmortem")


@pytest.fixture
def run_archive(request: pytest.FixtureRequest):
    marker = request.node.get_closest_marker("usecase_id")
    if marker and marker.args:
        usecase_id = str(marker.args[0])
    else:
        usecase_id = request.node.module.__name__.split(".")[-1].replace("test_", "")

    archive = create_run_archive(usecase_id, request.node.name)
    yield archive
    test_passed, outcome, outcome_stage, outcome_reason = _report_outcome(request.node)
    archive.finalize(
        test_passed=test_passed,
        outcome=outcome,
        outcome_stage=outcome_stage,
        outcome_reason=outcome_reason,
    )


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
