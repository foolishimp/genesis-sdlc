# Validates: REQ-F-GRAPH-001
# Validates: REQ-F-GRAPH-002
# Validates: REQ-F-GATE-001
# Validates: REQ-F-CMD-001
# Validates: REQ-F-CMD-002
# Validates: REQ-F-CMD-003
# Validates: REQ-F-TAG-001
# Validates: REQ-F-TAG-002
# Validates: REQ-F-COV-001
# Validates: REQ-F-TEST-003
# Validates: REQ-F-MDECOMP-001
# Validates: REQ-F-UAT-002
# Validates: REQ-F-DOCS-002
# Validates: REQ-F-VAR-001
"""Tests for the Codex genesis_sdlc graph surface."""

from __future__ import annotations

from gtl.core import Evaluator, F_D, F_H, F_P, Package, Worker

from genesis_sdlc import sdlc_graph as sg


def test_package_surface_shape():
    assert isinstance(sg.package, Package)
    assert sg.package.name == "genesis_sdlc"
    assert len(sg.package.assets) == 10
    assert len(sg.package.edges) == 9


def test_worker_is_codex():
    assert isinstance(sg.worker, Worker)
    assert sg.worker.id == "codex"


def test_codex_paths_are_used():
    assert sg.this_spec.locator == "workspace://builds/codex/code/genesis_sdlc/sdlc_graph.py"
    assert sg.design_adrs.locator == "workspace://builds/codex/design/adrs/"


def test_fd_evaluators_have_commands():
    evaluators = [
        getattr(sg, name)
        for name in dir(sg)
        if isinstance(getattr(sg, name), Evaluator)
    ]
    for evaluator in evaluators:
        if evaluator.category is F_D:
            assert evaluator.command


def test_pytest_fd_evaluators_exclude_e2e():
    evaluators = [
        getattr(sg, name)
        for name in dir(sg)
        if isinstance(getattr(sg, name), Evaluator)
    ]
    for evaluator in evaluators:
        if evaluator.category is F_D and "python -m pytest" in evaluator.command:
            assert "not e2e" in evaluator.command


def test_instantiate_rewrites_installed_contexts():
    package, worker = sg.instantiate("my_proj")
    assert package.name == "my_proj"
    assert worker.id == "codex"
    for job in worker.can_execute:
        for context in job.edge.context:
            if context.name == "sdlc_spec":
                assert context.locator == "workspace://.genesis/gtl_spec/packages/my_proj.py"


def test_instantiate_rewrites_slug_bound_commands():
    _, worker = sg.instantiate("my_proj")
    req_job = next(job for job in worker.can_execute if job.edge.name == "requirements→feature_decomp")
    guide_job = next(job for job in worker.can_execute if job.edge.name == "integration_tests→user_guide")
    req_cov = next(ev for ev in req_job.evaluators if ev.name == "req_coverage")
    guide_cov = next(ev for ev in guide_job.evaluators if ev.name == "guide_req_coverage")
    assert "gtl_spec.packages.my_proj:package" in req_cov.command
    assert "gtl_spec.packages.my_proj" in guide_cov.command


def test_uat_edge_is_pure_human_gate():
    edge = next(edge for edge in sg.package.edges if edge.name == "user_guide→uat_tests")
    categories = {operator.category for operator in edge.using}
    assert categories == {F_H}


def test_tdd_job_still_contains_fp_surface():
    job = next(job for job in sg.worker.can_execute if job.edge.name == "code↔unit_tests")
    categories = {ev.category for ev in job.evaluators}
    assert F_D in categories
    assert F_P in categories
