# Validates: REQ-F-GRAPH-001
# Validates: REQ-F-GRAPH-002
# Validates: REQ-F-GATE-001
# Validates: REQ-F-CMD-001
# Validates: REQ-F-CMD-002
# Validates: REQ-F-CMD-003
# Validates: REQ-F-TAG-001
# Validates: REQ-F-TAG-002
# Validates: REQ-F-COV-001
# Validates: REQ-F-BOOT-002
# Validates: REQ-F-DOCS-001
"""Tests for genesis_sdlc.sdlc_graph — the standard SDLC bootstrap graph."""
import pytest
from gtl.core import (
    Package, Worker, Asset, Edge, Evaluator, Job, Operator, Rule,
    F_D, F_P, F_H,
    OPERATIVE_ON_APPROVED, OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)


@pytest.fixture
def pkg():
    from genesis_sdlc.sdlc_graph import package
    return package


@pytest.fixture
def wkr():
    from genesis_sdlc.sdlc_graph import worker
    return worker


# ── Package integrity ─────────────────────────────────────────────────────────

class TestPackageStructure:
    def test_package_is_package(self, pkg):
        assert isinstance(pkg, Package)

    def test_package_name(self, pkg):
        assert pkg.name == "genesis_sdlc"

    def test_package_has_seven_assets(self, pkg):
        assert len(pkg.assets) == 7

    def test_asset_names(self, pkg):
        names = {a.name for a in pkg.assets}
        assert names == {"intent", "requirements", "feature_decomp", "design", "code", "unit_tests", "uat_tests"}

    def test_package_has_six_edges(self, pkg):
        assert len(pkg.edges) == 6

    def test_edge_names(self, pkg):
        names = {e.name for e in pkg.edges}
        assert "intent→requirements" in names
        assert "requirements→feature_decomp" in names
        assert "feature_decomp→design" in names
        assert "design→code" in names
        assert "code↔unit_tests" in names
        assert "unit_tests→uat_tests" in names

    def test_requirements_list_not_empty(self, pkg):
        assert len(pkg.requirements) >= 12


# ── Asset lineage ─────────────────────────────────────────────────────────────

class TestAssetLineage:
    def _asset(self, pkg, name):
        return next(a for a in pkg.assets if a.name == name)

    def test_requirements_lineage_is_intent(self, pkg):
        req = self._asset(pkg, "requirements")
        assert any(a.name == "intent" for a in req.lineage)

    def test_feature_decomp_lineage_is_requirements(self, pkg):
        fd = self._asset(pkg, "feature_decomp")
        assert any(a.name == "requirements" for a in fd.lineage)

    def test_design_lineage_is_feature_decomp(self, pkg):
        d = self._asset(pkg, "design")
        assert any(a.name == "feature_decomp" for a in d.lineage)

    def test_code_lineage_is_design(self, pkg):
        c = self._asset(pkg, "code")
        assert any(a.name == "design" for a in c.lineage)

    def test_unit_tests_lineage_is_code(self, pkg):
        ut = self._asset(pkg, "unit_tests")
        assert any(a.name == "code" for a in ut.lineage)

    def test_uat_tests_lineage_is_unit_tests(self, pkg):
        uat = self._asset(pkg, "uat_tests")
        assert any(a.name == "unit_tests" for a in uat.lineage)

    def test_uat_tests_markov_includes_sandbox(self, pkg):
        uat = self._asset(pkg, "uat_tests")
        assert "sandbox_install_passes" in uat.markov
        assert "e2e_scenarios_pass" in uat.markov
        assert "accepted_by_human" in uat.markov

    def test_requirements_operative(self, pkg):
        req = self._asset(pkg, "requirements")
        assert req.operative is not None

    def test_design_operative_not_superseded(self, pkg):
        d = self._asset(pkg, "design")
        assert d.operative == OPERATIVE_ON_APPROVED_NOT_SUPERSEDED


# ── Edge evaluators ───────────────────────────────────────────────────────────

class TestEdgeEvaluators:
    def _job(self, pkg, edge_name):
        # Jobs are not on Package directly; import from module
        from genesis_sdlc import sdlc_graph as sg
        for attr in dir(sg):
            obj = getattr(sg, attr)
            if hasattr(obj, "edge") and obj.edge.name == edge_name:
                return obj
        return None

    def test_tdd_edge_is_co_evolve(self, pkg):
        e = next(e for e in pkg.edges if e.name == "code↔unit_tests")
        assert e.co_evolve is True

    def test_design_code_edge_has_operators(self, pkg):
        e = next(e for e in pkg.edges if e.name == "design→code")
        assert len(e.using) >= 1

    def test_intent_req_edge_has_human_operator(self, pkg):
        e = next(e for e in pkg.edges if e.name == "intent→requirements")
        categories = {op.category for op in e.using}
        assert F_H in categories

    def test_design_code_edge_no_human(self, pkg):
        e = next(e for e in pkg.edges if e.name == "design→code")
        categories = {op.category for op in e.using}
        assert F_H not in categories


# ── Evaluators with commands ──────────────────────────────────────────────────

class TestEvaluatorCommands:
    def _all_evaluators(self):
        from genesis_sdlc import sdlc_graph as sg
        return [
            getattr(sg, attr) for attr in dir(sg)
            if isinstance(getattr(sg, attr), Evaluator)
        ]

    def test_fd_evaluators_have_command(self):
        for ev in self._all_evaluators():
            if ev.category == F_D:
                assert ev.command, f"F_D evaluator {ev.name!r} missing command"

    def test_impl_tags_evaluator_exists(self):
        evs = {ev.name: ev for ev in self._all_evaluators()}
        assert "impl_tags" in evs
        assert evs["impl_tags"].category == F_D
        assert "check-tags" in evs["impl_tags"].command

    def test_tests_pass_evaluator_exists(self):
        evs = {ev.name: ev for ev in self._all_evaluators()}
        assert "tests_pass" in evs
        assert "pytest" in evs["tests_pass"].command

    def test_validates_tags_evaluator_exists(self):
        evs = {ev.name: ev for ev in self._all_evaluators()}
        assert "validates_tags" in evs
        assert "check-tags" in evs["validates_tags"].command

    def test_fd_evaluators_exclude_e2e(self):
        """F_D evaluators must not run e2e tests (acyclicity constraint)."""
        for ev in self._all_evaluators():
            if ev.category == F_D and ev.command and "pytest" in ev.command:
                assert "not e2e" in ev.command, (
                    f"F_D evaluator {ev.name!r} runs pytest without -m 'not e2e' — "
                    "risk of recursive genesis invocation"
                )

    def test_uat_edge_has_fh_gate(self, pkg):
        e = next(e for e in pkg.edges if e.name == "unit_tests→uat_tests")
        categories = {op.category for op in e.using}
        assert F_H in categories

    def test_uat_edge_has_human_rule(self, pkg):
        e = next(e for e in pkg.edges if e.name == "unit_tests→uat_tests")
        assert e.rule is not None

    def test_uat_job_evaluators(self):
        from genesis_sdlc import sdlc_graph as sg
        job_uat = next(j for j in sg.worker.can_execute if j.edge.name == "unit_tests→uat_tests")
        categories = {ev.category for ev in job_uat.evaluators}
        assert F_D in categories, "UAT job must have F_D evaluator (sandbox report check)"
        assert F_P in categories, "UAT job must have F_P evaluator (sandbox runner)"
        assert F_H in categories, "UAT job must have F_H gate (human confirmation)"

    def test_uat_report_evaluator_has_command(self):
        from genesis_sdlc import sdlc_graph as sg
        job_uat = next(j for j in sg.worker.can_execute if j.edge.name == "unit_tests→uat_tests")
        fd_evs = [ev for ev in job_uat.evaluators if ev.category == F_D]
        assert fd_evs, "UAT job must have at least one F_D evaluator"
        assert fd_evs[0].command, "UAT F_D evaluator must have a command"
        assert "sandbox_report.json" in fd_evs[0].command


# ── Worker ─────────────────────────────────────────────────────────────────────

class TestWorker:
    def test_worker_is_worker(self, wkr):
        assert isinstance(wkr, Worker)

    def test_worker_id(self, wkr):
        assert wkr.id == "claude_code"

    def test_worker_can_execute_all_jobs(self, wkr):
        assert len(wkr.can_execute) == 6


# ── Public API ─────────────────────────────────────────────────────────────────

class TestPublicAPI:
    def test_import_from_init(self):
        from genesis_sdlc import package, worker
        assert package is not None
        assert worker is not None

    def test_version(self):
        import genesis_sdlc
        assert genesis_sdlc.__version__ == "0.1.3"

    def test_all_exports(self):
        import genesis_sdlc
        assert "package" in genesis_sdlc.__all__
        assert "worker" in genesis_sdlc.__all__
