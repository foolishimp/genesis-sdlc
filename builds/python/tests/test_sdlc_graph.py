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
# Validates: REQ-F-TEST-002
# Validates: REQ-F-TEST-003
# Validates: REQ-F-MDECOMP-001
# Validates: REQ-F-MDECOMP-002
# Validates: REQ-F-MDECOMP-003
# Validates: REQ-F-MDECOMP-004
# Validates: REQ-F-MDECOMP-005
# Validates: REQ-F-UAT-002
# Validates: REQ-F-UAT-003
# Validates: REQ-F-DOCS-002
# Validates: REQ-F-VAR-001
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

    def test_package_has_ten_assets(self, pkg):
        assert len(pkg.assets) == 10

    def test_asset_names(self, pkg):
        names = {a.name for a in pkg.assets}
        assert names == {"intent", "requirements", "feature_decomp", "design",
                         "module_decomp", "code", "unit_tests",
                         "integration_tests", "user_guide", "uat_tests"}

    def test_package_has_nine_edges(self, pkg):
        assert len(pkg.edges) == 9

    def test_edge_names(self, pkg):
        names = {e.name for e in pkg.edges}
        assert "intent→requirements" in names
        assert "requirements→feature_decomp" in names
        assert "feature_decomp→design" in names
        assert "design→module_decomp" in names
        assert "module_decomp→code" in names
        assert "code↔unit_tests" in names
        assert "unit_tests→integration_tests" in names
        assert "integration_tests→user_guide" in names
        assert "user_guide→uat_tests" in names

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

    def test_code_lineage_is_module_decomp(self, pkg):
        c = self._asset(pkg, "code")
        assert any(a.name == "module_decomp" for a in c.lineage)

    def test_unit_tests_lineage_is_code(self, pkg):
        ut = self._asset(pkg, "unit_tests")
        assert any(a.name == "code" for a in ut.lineage)

    def test_integration_tests_lineage_is_unit_tests(self, pkg):
        it = self._asset(pkg, "integration_tests")
        assert any(a.name == "unit_tests" for a in it.lineage)

    def test_user_guide_lineage_is_integration_tests(self, pkg):
        ug = self._asset(pkg, "user_guide")
        assert any(a.name == "integration_tests" for a in ug.lineage)

    def test_uat_tests_lineage_is_user_guide(self, pkg):
        uat = self._asset(pkg, "uat_tests")
        assert any(a.name == "user_guide" for a in uat.lineage)

    def test_integration_tests_markov_includes_sandbox(self, pkg):
        it = self._asset(pkg, "integration_tests")
        assert "sandbox_install_passes" in it.markov
        assert "e2e_scenarios_pass" in it.markov

    def test_uat_tests_markov_is_accepted_by_human_only(self, pkg):
        uat = self._asset(pkg, "uat_tests")
        assert "accepted_by_human" in uat.markov
        assert "sandbox_install_passes" not in uat.markov
        assert "e2e_scenarios_pass" not in uat.markov

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

    def test_module_decomp_code_edge_has_operators(self, pkg):
        e = next(e for e in pkg.edges if e.name == "module_decomp→code")
        assert len(e.using) >= 1

    def test_intent_req_edge_has_human_operator(self, pkg):
        e = next(e for e in pkg.edges if e.name == "intent→requirements")
        categories = {op.category for op in e.using}
        assert F_H in categories

    def test_module_decomp_code_edge_no_human(self, pkg):
        """module_decomp→code is a pure construction edge — no F_H gate."""
        e = next(e for e in pkg.edges if e.name == "module_decomp→code")
        categories = {op.category for op in e.using}
        assert F_H not in categories

    def test_design_module_decomp_edge_has_human(self, pkg):
        """design→module_decomp has an F_H gate to approve the module schedule."""
        e = next(e for e in pkg.edges if e.name == "design→module_decomp")
        categories = {op.category for op in e.using}
        assert F_H in categories


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
        """F_D evaluators that invoke pytest as a test runner must exclude e2e tests."""
        for ev in self._all_evaluators():
            invokes_pytest = (
                ev.category == F_D
                and ev.command
                and ("python -m pytest" in ev.command or ev.command.strip().startswith("pytest "))
            )
            if invokes_pytest:
                assert "not e2e" in ev.command, (
                    f"F_D evaluator {ev.name!r} runs pytest without -m 'not e2e' — "
                    "risk of recursive genesis invocation"
                )

    def test_guide_uat_edge_has_fh_gate(self, pkg):
        e = next(e for e in pkg.edges if e.name == "user_guide→uat_tests")
        categories = {op.category for op in e.using}
        assert F_H in categories

    def test_guide_uat_edge_has_human_rule(self, pkg):
        e = next(e for e in pkg.edges if e.name == "user_guide→uat_tests")
        assert e.rule is not None

    def test_guide_uat_edge_is_pure_fh(self, pkg):
        """user_guide→uat_tests is a pure F_H gate — no F_D or F_P."""
        e = next(e for e in pkg.edges if e.name == "user_guide→uat_tests")
        categories = {op.category for op in e.using}
        assert F_H in categories
        assert F_D not in categories
        assert F_P not in categories

    def test_tdd_job_has_e2e_exists_evaluator(self):
        """code↔unit_tests job must include e2e_tests_exist to enforce integration-primary testing."""
        from genesis_sdlc import sdlc_graph as sg
        job = next(j for j in sg.worker.can_execute if j.edge.name == "code↔unit_tests")
        names = [ev.name for ev in job.evaluators]
        assert "e2e_tests_exist" in names, f"e2e_tests_exist missing from tdd job; got: {names}"

    def test_unit_itest_job_evaluators(self):
        from genesis_sdlc import sdlc_graph as sg
        job = next(j for j in sg.worker.can_execute if j.edge.name == "unit_tests→integration_tests")
        categories = {ev.category for ev in job.evaluators}
        assert F_D in categories, "integration_tests job must have F_D evaluator (sandbox report check)"
        assert F_P in categories, "integration_tests job must have F_P evaluator (sandbox runner)"

    def test_sandbox_report_evaluator_has_command(self):
        from genesis_sdlc import sdlc_graph as sg
        job = next(j for j in sg.worker.can_execute if j.edge.name == "unit_tests→integration_tests")
        fd_evs = [ev for ev in job.evaluators if ev.category == F_D]
        assert fd_evs, "integration_tests job must have at least one F_D evaluator"
        assert fd_evs[0].command, "integration_tests F_D evaluator must have a command"
        assert "sandbox_report.json" in fd_evs[0].command

    def test_itest_guide_job_evaluators(self):
        from genesis_sdlc import sdlc_graph as sg
        job = next(j for j in sg.worker.can_execute if j.edge.name == "integration_tests→user_guide")
        categories = {ev.category for ev in job.evaluators}
        assert F_D in categories, "user_guide job must have F_D evaluators"
        assert F_P in categories, "user_guide job must have F_P evaluator"

    def test_guide_version_evaluator_checks_version_field(self):
        """guide_version_current must check '**Version**: {ver}', not just any occurrence."""
        from genesis_sdlc import sdlc_graph as sg
        job = next(j for j in sg.worker.can_execute if j.edge.name == "integration_tests→user_guide")
        ev = next(e for e in job.evaluators if e.name == "guide_version_current")
        assert "**Version**:" in ev.command, (
            "guide_version_current must check the '**Version**: ' field, not just any version token"
        )
        # Must NOT rely on literal double-quote chars inside the sh command — POSIX sh quoting bug
        # The VERSION regex must capture digits without embedding \" in the shell string
        assert '\\"' not in ev.command, (
            "guide_version_current command contains \\\" which breaks in POSIX sh (exit code 2)"
        )

    def test_guide_coverage_evaluator_checks_covers_tags(self):
        """guide_req_coverage must check <!-- Covers: REQ-F-* --> blocks, not any REQ-F-* token."""
        from genesis_sdlc import sdlc_graph as sg
        job = next(j for j in sg.worker.can_execute if j.edge.name == "integration_tests→user_guide")
        ev = next(e for e in job.evaluators if e.name == "guide_req_coverage")
        assert "<!-- Covers:" in ev.command, (
            "guide_req_coverage must search for <!-- Covers: ... --> blocks, "
            "not just any REQ-F-* token in the file"
        )
        assert "package.requirements" in ev.command or "pkg.requirements" in ev.command, (
            "guide_req_coverage must check completeness against package.requirements, "
            "not just presence of any coverage block"
        )

    def test_guide_req_coverage_passes_against_current_guide(self):
        """All package.requirements keys must appear in <!-- Covers: --> blocks in USER_GUIDE.md."""
        import re, pathlib, importlib
        guide = pathlib.Path("docs/USER_GUIDE.md").read_text()
        covered = set(
            r for t in re.findall(r"<!-- Covers:([^>]+)-->", guide)
            for r in re.findall(r"REQ-F-[A-Z0-9-]+", t)
        )
        from genesis_sdlc import sdlc_graph as sg
        missing = sorted(set(sg.package.requirements) - covered)
        assert not missing, (
            f"USER_GUIDE.md is missing <!-- Covers: --> tags for: {missing}"
        )


# ── Worker ─────────────────────────────────────────────────────────────────────

class TestWorker:
    def test_worker_is_worker(self, wkr):
        assert isinstance(wkr, Worker)

    def test_worker_id(self, wkr):
        assert wkr.id == "claude_code"

    def test_worker_can_execute_all_jobs(self, wkr):
        assert len(wkr.can_execute) == 9


# ── Public API ─────────────────────────────────────────────────────────────────

class TestPublicAPI:
    def test_import_from_init(self):
        from genesis_sdlc import package, worker
        assert package is not None
        assert worker is not None

    def test_version(self):
        import genesis_sdlc
        assert genesis_sdlc.__version__ == "1.0.0b1"

    def test_all_exports(self):
        import genesis_sdlc
        assert "package" in genesis_sdlc.__all__
        assert "worker" in genesis_sdlc.__all__


# ── instantiate ───────────────────────────────────────────────────────────────

class TestInstantiate:
    def test_instantiate_returns_package_and_worker(self):
        from genesis_sdlc.sdlc_graph import instantiate
        pkg, wkr = instantiate(slug="my_project")
        assert isinstance(pkg, Package)
        assert isinstance(wkr, Worker)

    def test_instantiate_sets_package_name(self):
        from genesis_sdlc.sdlc_graph import instantiate
        pkg, _ = instantiate(slug="acme_corp")
        assert pkg.name == "acme_corp"

    def test_instantiate_overrides_req_coverage_command(self):
        from genesis_sdlc.sdlc_graph import instantiate
        _, wkr = instantiate(slug="acme_corp")
        job = next(j for j in wkr.can_execute if j.edge.name == "requirements\u2192feature_decomp")
        ev = next(ev for ev in job.evaluators if ev.name == "req_coverage")
        assert "acme_corp" in ev.command
        assert "genesis_sdlc" not in ev.command

    def test_instantiate_overrides_sdlc_spec_context(self):
        from genesis_sdlc.sdlc_graph import instantiate
        pkg, _ = instantiate(slug="my_project")
        ctx = next(c for c in pkg.contexts if c.name == "sdlc_spec")
        assert "my_project.py" in ctx.locator
        assert "genesis_sdlc.py" not in ctx.locator

    def test_instantiate_preserves_all_jobs(self):
        from genesis_sdlc.sdlc_graph import instantiate, worker
        _, wkr = instantiate(slug="some_slug")
        assert len(wkr.can_execute) == len(worker.can_execute)

    def test_instantiate_defaults_to_empty_requirements(self):
        """No requirements arg → empty list (not workflow's keys).  # Validates: REQ-F-CUSTODY-001"""
        from genesis_sdlc.sdlc_graph import instantiate
        pkg, _ = instantiate(slug="some_slug")
        assert pkg.requirements == []

    def test_instantiate_accepts_project_requirements(self):
        """Explicit requirements override workflow keys.  # Validates: REQ-F-CUSTODY-001"""
        from genesis_sdlc.sdlc_graph import instantiate
        project_reqs = ["REQ-PROJ-001", "REQ-PROJ-002"]
        pkg, _ = instantiate(slug="some_slug", requirements=project_reqs)
        assert pkg.requirements == project_reqs

    def test_different_slugs_produce_different_hashes(self):
        """Two instantiations with different slugs produce different job_evaluator hashes."""
        import hashlib, re
        from genesis_sdlc.sdlc_graph import instantiate
        _, wkr_a = instantiate(slug="project_a")
        _, wkr_b = instantiate(slug="project_b")
        job_a = next(j for j in wkr_a.can_execute if j.edge.name == "requirements\u2192feature_decomp")
        job_b = next(j for j in wkr_b.can_execute if j.edge.name == "requirements\u2192feature_decomp")

        def _hash(job):
            lines = sorted(
                f"{ev.name}:{ev.category.__name__}:{getattr(ev, 'command', '') or ''}:{ev.description}"
                for ev in job.evaluators
            )
            raw = "\n".join(re.sub(r"\s+", " ", l.strip()) for l in lines)
            return hashlib.sha256(raw.encode()).hexdigest()[:16]

        assert _hash(job_a) != _hash(job_b)
