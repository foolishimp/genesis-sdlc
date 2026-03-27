# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-004
"""Pytest markers for the Abiogenesis/Python tenant tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


_TESTS_DIR = Path(__file__).resolve().parent
if str(_TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(_TESTS_DIR))

from run_archive import create_run_archive


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
    test_passed = not hasattr(request.node, "rep_call") or request.node.rep_call.passed
    archive.finalize(test_passed=test_passed)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)
