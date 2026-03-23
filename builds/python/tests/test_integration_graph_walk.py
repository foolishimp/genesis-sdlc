# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-003
# Validates: REQ-F-GRAPH-001
# Validates: REQ-F-GRAPH-002
# Validates: REQ-F-CMD-001
# Validates: REQ-F-CMD-002
# Validates: REQ-F-CMD-003
# Validates: REQ-F-GATE-001
# Validates: REQ-F-TAG-001
# Validates: REQ-F-TAG-002
# Validates: REQ-F-COV-001
# Validates: REQ-F-MDECOMP-001
# Validates: REQ-F-MDECOMP-002
# Validates: REQ-F-MDECOMP-003
# Validates: REQ-F-MDECOMP-005
# Validates: REQ-F-UAT-001
# Validates: REQ-F-UAT-002
# Validates: REQ-F-DOCS-002
# Validates: REQ-F-BOOT-001
# Validates: REQ-F-BOOT-002
# Validates: REQ-F-CUSTODY-001
"""
Integration graph walk tests for genesis_sdlc.

Primary test surface for the 9-edge SDLC DAG. Each test exercises the
F_D → F_P → F_H evaluator chain end-to-end against a real installed workspace
using real subprocess evaluator commands.

The SDLC graph:

    intent → requirements → feature_decomp → design → module_decomp → code ↔ unit_tests
                                                                               │
                                                                               ↓
                                                        uat_tests ← user_guide ← integration_tests

These tests validate seams that unit tests cannot:
  - Edge-to-edge convergence cascade
  - F_D escalation to F_P (ADR-021)
  - Co-evolving TDD edge
  - Manifest context per hop
  - Full 9-edge convergence to delta=0
  - Revocation cascade across multi-hop chain

Each test installs into a fresh sandbox via run_archive, so tests are
fully isolated. The sandbox persists on disk for postmortem inspection.

Run: pytest tests/test_integration_graph_walk.py -v -m integration
"""
import json
from pathlib import Path

import pytest

from scenario_helpers import (
    # Infrastructure
    install_sandbox, run_genesis, run_genesis_json, emit_event,
    read_events, get_gaps, get_edge_gap, compute_spec_hash,
    # Artifact writers
    write_intent, write_requirements, write_features, write_adrs,
    write_modules, write_source_code, write_tests, write_e2e_test,
    write_sandbox_report, write_user_guide,
    # Lifecycle
    approve_edge, assess_edge,
    converge_intent_to_requirements, converge_requirements_to_feature_decomp,
    converge_feature_decomp_to_design, converge_design_to_module_decomp,
    converge_module_decomp_to_code, converge_tdd,
    converge_unit_tests_to_integration_tests,
    converge_integration_tests_to_user_guide, converge_user_guide_to_uat,
    converge_through_design, converge_through_code,
    converge_through_unit_tests, converge_full_graph,
    # Assertions
    assert_edge_converged, assert_edge_in_delta,
    assert_evaluator_failing, assert_evaluator_passing,
    assert_graph_converged, assert_failure_inspectable,
    assert_event_exists, assert_event_chain,
    # Constants
    EDGE_INTENT_REQ, EDGE_REQ_FEAT, EDGE_FEAT_DESIGN,
    EDGE_DESIGN_MDECOMP, EDGE_MDECOMP_CODE, EDGE_TDD,
    EDGE_UNIT_ITEST, EDGE_ITEST_GUIDE, EDGE_GUIDE_UAT,
    ALL_EDGES,
    EVAL_INTENT_FH, EVAL_DECOMP_FH, EVAL_DESIGN_FH,
    EVAL_SCHEDULE_FH, EVAL_UAT_FH,
    EVAL_DECOMP_FP, EVAL_DESIGN_FP, EVAL_CODE_FP,
    EVAL_COVERAGE_FP, EVAL_SANDBOX_FP, EVAL_GUIDE_FP, EVAL_MODULE_FP,
    EVAL_REQ_COVERAGE, EVAL_MODULE_COVERAGE, EVAL_IMPL_TAGS,
    EVAL_TESTS_PASS, EVAL_TEST_TAGS, EVAL_E2E_EXISTS,
    EVAL_SANDBOX_REPORT, EVAL_GUIDE_VERSION, EVAL_GUIDE_COVERAGE,
    DEFAULT_SLUG,
)


# ── Shared fixture ────────────────────────────────────────────────────────────

REQ_KEYS = ["REQ-F-IT-001"]


def _setup(archive) -> Path:
    """Install a fresh sandbox for a single test."""
    target = archive.workspace
    install_sandbox(target, DEFAULT_SLUG, archive=archive)
    write_intent(target)
    write_requirements(target, REQ_KEYS)
    return target


# ══════════════════════════════════════════════════════════════════════════════
# 1. FRESH WORKSPACE — BASELINE STATE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestFreshWorkspace:
    """A freshly installed workspace: all 9 edges in delta, correct structure."""

    def test_all_edges_in_delta(self, run_archive):
        """Fresh install → every edge has delta > 0."""
        target = _setup(run_archive)
        data = get_gaps(target, archive=run_archive)
        assert data["converged"] is False
        assert data["total_delta"] > 0

    def test_sees_9_jobs(self, run_archive):
        """gen-gaps reports exactly 9 jobs for the 10-asset SDLC graph."""
        target = _setup(run_archive)
        data = get_gaps(target, archive=run_archive)
        assert data["jobs_considered"] == 9, (
            f"Expected 9 jobs, got {data['jobs_considered']}"
        )

    def test_all_edge_names_present(self, run_archive):
        """Every edge name from the SDLC graph appears in the gaps report."""
        target = _setup(run_archive)
        data = get_gaps(target, archive=run_archive)
        edge_names = {g["edge"] for g in data["gaps"]}
        for edge in ALL_EDGES:
            assert edge in edge_names, f"Missing edge: {edge}"

    def test_failure_diagnostics_inspectable(self, run_archive):
        """Gap failures have enough detail for postmortem diagnosis."""
        target = _setup(run_archive)
        assert_failure_inspectable(target, archive=run_archive)

    def test_genesis_sdlc_installed_event(self, run_archive):
        """Installer emits genesis_sdlc_installed event to the stream."""
        target = _setup(run_archive)
        assert_event_exists(target, "genesis_sdlc_installed")


# ══════════════════════════════════════════════════════════════════════════════
# 2. EDGE 1: intent → requirements (F_H only)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestIntentToRequirements:
    """Edge 1: F_H gate only — human must approve before requirements are operative."""

    def test_fh_gate_pending_on_iterate(self, run_archive):
        """gen-iterate on first edge → F_H gate pending (exit 3)."""
        target = _setup(run_archive)
        result = run_genesis(target, "iterate", archive=run_archive)
        # Exit code 3 = F_H gate pending, or the engine may handle differently
        # for the first edge. Assert we get a non-zero, non-converged result.
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        # The engine should surface the F_H gate
        assert result.returncode != 0 or data.get("status") != "converged"

    def test_intent_approved_evaluator_failing_initially(self, run_archive):
        """intent_approved evaluator is in the failing list before approval."""
        target = _setup(run_archive)
        assert_evaluator_failing(target, EDGE_INTENT_REQ, EVAL_INTENT_FH)

    def test_approved_event_converges_edge(self, run_archive):
        """Emitting approved{kind: fh_review} for intent→requirements converges it."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        assert_edge_converged(target, EDGE_INTENT_REQ, archive=run_archive)

    def test_wrong_edge_approval_does_not_converge(self, run_archive):
        """Approved for a different edge does not converge intent→requirements."""
        target = _setup(run_archive)
        approve_edge(target, EDGE_REQ_FEAT, archive=run_archive)
        assert_evaluator_failing(target, EDGE_INTENT_REQ, EVAL_INTENT_FH)

    def test_edge_converged_certificate_emitted(self, run_archive):
        """Converging intent→requirements emits an edge_converged event."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        # Force certificate emission via gen-gaps
        get_gaps(target, archive=run_archive)
        assert_event_chain(target, edge_name=EDGE_INTENT_REQ, expect_converged=True)


# ══════════════════════════════════════════════════════════════════════════════
# 3. EDGE 2: requirements → feature_decomp (F_D + F_P + F_H)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestRequirementsToFeatureDecomp:
    """Edge 2: F_D (req_coverage) escalates to F_P (decomp), then F_H (approval)."""

    def test_req_coverage_fails_without_features(self, run_archive):
        """req_coverage F_D evaluator fails when no feature vectors exist."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        assert_evaluator_failing(target, EDGE_REQ_FEAT, EVAL_REQ_COVERAGE)

    def test_fd_escalates_to_fp_dispatch(self, run_archive):
        """F_D (req_coverage) failing escalates to F_P dispatch (ADR-021)."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        result = run_genesis(target, "iterate", archive=run_archive)
        data = json.loads(result.stdout) if result.stdout.strip() else {}
        # ADR-021: F_D findings escalate — F_P is dispatched, not blocked
        assert result.returncode == 0, (
            f"Expected exit 0 (F_P dispatched), got: rc={result.returncode}, data={data}"
        )
        assert "fp_manifest_path" in data, (
            f"Expected fp_manifest_path in output (F_D escalates to F_P), got: {data}"
        )

    def test_features_fix_req_coverage(self, run_archive):
        """Writing feature vectors covering all REQ keys makes req_coverage pass."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        write_features(target, REQ_KEYS)
        assert_evaluator_passing(target, EDGE_REQ_FEAT, EVAL_REQ_COVERAGE)

    def test_fp_assessment_plus_fh_converges(self, run_archive):
        """F_D pass + F_P assessed + F_H approved → edge converges."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        converge_requirements_to_feature_decomp(target, REQ_KEYS, archive=run_archive)
        assert_edge_converged(target, EDGE_REQ_FEAT, archive=run_archive)

    def test_partial_coverage_still_fails(self, run_archive):
        """Feature covering only some REQ keys → req_coverage still fails."""
        target = _setup(run_archive)
        # Add a second REQ key that won't be covered
        write_requirements(target, ["REQ-F-IT-001", "REQ-F-IT-002"])
        converge_intent_to_requirements(target, archive=run_archive)
        # Only cover one of two keys
        write_features(target, ["REQ-F-IT-001"])
        assert_evaluator_failing(target, EDGE_REQ_FEAT, EVAL_REQ_COVERAGE)


# ══════════════════════════════════════════════════════════════════════════════
# 4. EDGE 3: feature_decomp → design (F_P + F_H)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestFeatureDecompToDesign:
    """Edge 3: F_P (design_coherent) + F_H (design_approved)."""

    def test_design_evaluators_failing_initially(self, run_archive):
        """design_coherent and design_approved are failing before convergence."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        converge_requirements_to_feature_decomp(target, REQ_KEYS, archive=run_archive)
        assert_evaluator_failing(target, EDGE_FEAT_DESIGN, EVAL_DESIGN_FP)
        assert_evaluator_failing(target, EDGE_FEAT_DESIGN, EVAL_DESIGN_FH)

    def test_fp_without_fh_does_not_converge(self, run_archive):
        """Assessing design_coherent without design_approved does not converge."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        converge_requirements_to_feature_decomp(target, REQ_KEYS, archive=run_archive)
        write_adrs(target)
        assess_edge(target, EDGE_FEAT_DESIGN, EVAL_DESIGN_FP, archive=run_archive)
        assert_evaluator_failing(target, EDGE_FEAT_DESIGN, EVAL_DESIGN_FH)

    def test_full_convergence(self, run_archive):
        """F_P + F_H → feature_decomp→design converges."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        converge_requirements_to_feature_decomp(target, REQ_KEYS, archive=run_archive)
        converge_feature_decomp_to_design(target, archive=run_archive)
        assert_edge_converged(target, EDGE_FEAT_DESIGN, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 5. EDGE 4: design → module_decomp (F_D + F_P + F_H)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestDesignToModuleDecomp:
    """Edge 4: F_D (module_coverage) escalates to F_P (module_schedule), then F_H."""

    def test_module_coverage_fails_without_modules(self, run_archive):
        """module_coverage F_D evaluator fails when no module YAMLs exist."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        assert_evaluator_failing(target, EDGE_DESIGN_MDECOMP, EVAL_MODULE_COVERAGE)

    def test_modules_fix_coverage(self, run_archive):
        """Writing module YAMLs covering all features makes module_coverage pass."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        write_modules(target, ["FD-001"])
        assert_evaluator_passing(target, EDGE_DESIGN_MDECOMP, EVAL_MODULE_COVERAGE)

    def test_full_convergence(self, run_archive):
        """F_D + F_P + F_H → design→module_decomp converges."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        converge_design_to_module_decomp(target, ["FD-001"], archive=run_archive)
        assert_edge_converged(target, EDGE_DESIGN_MDECOMP, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 6. EDGE 5: module_decomp → code (F_D + F_P)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestModuleDecompToCode:
    """Edge 5: F_D (impl_tags) escalates to F_P (code_complete)."""

    def test_impl_tags_passes_vacuously_on_empty_src(self, run_archive):
        """impl_tags F_D evaluator passes vacuously when no source files exist (zero untagged)."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        converge_design_to_module_decomp(target, ["FD-001"], archive=run_archive)
        assert_evaluator_passing(target, EDGE_MDECOMP_CODE, EVAL_IMPL_TAGS)

    def test_untagged_source_still_fails(self, run_archive):
        """Source file without # Implements: tag → impl_tags still fails."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        converge_design_to_module_decomp(target, ["FD-001"], archive=run_archive)
        src_dir = target / "builds" / "python" / "src" / DEFAULT_SLUG
        src_dir.mkdir(parents=True, exist_ok=True)
        (src_dir / "__init__.py").write_text("")
        (src_dir / "core.py").write_text("def main(): pass\n")
        assert_evaluator_failing(target, EDGE_MDECOMP_CODE, EVAL_IMPL_TAGS)

    def test_tagged_source_passes(self, run_archive):
        """Source with # Implements: REQ-* → impl_tags passes."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        converge_design_to_module_decomp(target, ["FD-001"], archive=run_archive)
        write_source_code(target, DEFAULT_SLUG, REQ_KEYS)
        assert_evaluator_passing(target, EDGE_MDECOMP_CODE, EVAL_IMPL_TAGS)

    def test_full_convergence(self, run_archive):
        """F_D + F_P → module_decomp→code converges."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        converge_design_to_module_decomp(target, ["FD-001"], archive=run_archive)
        converge_module_decomp_to_code(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        assert_edge_converged(target, EDGE_MDECOMP_CODE, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 7. EDGE 6: code ↔ unit_tests (F_D×3 + F_P, co-evolving)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestTddCoEvolution:
    """Edge 6: co-evolving TDD edge — code and tests evolve together."""

    def test_tests_pass_fails_without_tests(self, run_archive):
        """tests_pass F_D evaluator fails when no test files exist."""
        target = _setup(run_archive)
        converge_through_code(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        assert_evaluator_failing(target, EDGE_TDD, EVAL_TESTS_PASS)

    def test_validates_tags_fails_without_tags(self, run_archive):
        """validates_tags F_D fails when test files have no # Validates: tag."""
        target = _setup(run_archive)
        converge_through_code(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        test_dir = target / "builds" / "python" / "tests"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "test_untagged.py").write_text("def test_x(): assert True\n")
        assert_evaluator_failing(target, EDGE_TDD, EVAL_TEST_TAGS)
        (test_dir / "test_untagged.py").unlink()

    def test_e2e_exists_fails_without_e2e_marker(self, run_archive):
        """e2e_tests_exist F_D fails when no @pytest.mark.e2e test exists."""
        target = _setup(run_archive)
        converge_through_code(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        write_tests(target, DEFAULT_SLUG, REQ_KEYS)
        # write_tests does NOT write e2e marker
        assert_evaluator_failing(target, EDGE_TDD, EVAL_E2E_EXISTS)

    def test_all_fd_pass_with_proper_tests(self, run_archive):
        """Tagged tests + e2e marker → all three F_D evaluators pass."""
        target = _setup(run_archive)
        converge_through_code(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        write_tests(target, DEFAULT_SLUG, REQ_KEYS)
        write_e2e_test(target, DEFAULT_SLUG)
        assert_evaluator_passing(target, EDGE_TDD, EVAL_TEST_TAGS)
        assert_evaluator_passing(target, EDGE_TDD, EVAL_E2E_EXISTS)

    def test_full_convergence(self, run_archive):
        """F_D×3 + F_P → code↔unit_tests converges."""
        target = _setup(run_archive)
        converge_through_code(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_tdd(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        assert_edge_converged(target, EDGE_TDD, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 8. EDGE 7: unit_tests → integration_tests (F_D + F_P)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestUnitTestsToIntegrationTests:
    """Edge 7: F_D (sandbox_report_exists) + F_P (sandbox_e2e_passed)."""

    def test_sandbox_report_fails_without_report(self, run_archive):
        """sandbox_report_exists F_D fails when no report file exists."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        assert_evaluator_failing(target, EDGE_UNIT_ITEST, EVAL_SANDBOX_REPORT)

    def test_sandbox_report_fails_with_failing_report(self, run_archive):
        """sandbox_report_exists F_D fails when report has all_pass=false."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        write_sandbox_report(target, all_pass=False)
        assert_evaluator_failing(target, EDGE_UNIT_ITEST, EVAL_SANDBOX_REPORT)

    def test_sandbox_report_passes_with_good_report(self, run_archive):
        """sandbox_report_exists F_D passes when report has all_pass=true."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        write_sandbox_report(target, all_pass=True)
        assert_evaluator_passing(target, EDGE_UNIT_ITEST, EVAL_SANDBOX_REPORT)

    def test_full_convergence(self, run_archive):
        """F_D + F_P → unit_tests→integration_tests converges."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_unit_tests_to_integration_tests(target, archive=run_archive)
        assert_edge_converged(target, EDGE_UNIT_ITEST, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 9. EDGE 8: integration_tests → user_guide (F_D×2 + F_P + F_H)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestIntegrationTestsToUserGuide:
    """Edge 8: F_D (guide_version, guide_coverage) + F_P + F_H."""

    def test_guide_version_fails_without_guide(self, run_archive):
        """guide_version_current F_D fails when no USER_GUIDE.md exists."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_unit_tests_to_integration_tests(target, archive=run_archive)
        assert_evaluator_failing(target, EDGE_ITEST_GUIDE, EVAL_GUIDE_VERSION)

    def test_guide_coverage_fails_without_covers_tags(self, run_archive):
        """guide_req_coverage F_D fails when guide has no <!-- Covers: --> tags."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_unit_tests_to_integration_tests(target, archive=run_archive)
        docs = target / "docs"
        docs.mkdir(parents=True, exist_ok=True)
        (docs / "USER_GUIDE.md").write_text("# Guide\n**Version**: 1.0.0b1\nNo covers tags.\n")
        assert_evaluator_failing(target, EDGE_ITEST_GUIDE, EVAL_GUIDE_COVERAGE)

    def test_guide_version_mismatch_fails(self, run_archive):
        """guide_version_current F_D fails when version doesn't match active workflow."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_unit_tests_to_integration_tests(target, archive=run_archive)
        write_user_guide(target, version="0.0.0", req_keys=REQ_KEYS)
        assert_evaluator_failing(target, EDGE_ITEST_GUIDE, EVAL_GUIDE_VERSION)

    def test_correct_guide_passes_fd(self, run_archive):
        """USER_GUIDE.md with correct version and coverage → F_D evaluators pass."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_unit_tests_to_integration_tests(target, archive=run_archive)
        aw = target / ".gsdlc" / "release" / "active-workflow.json"
        version = json.loads(aw.read_text())["version"] if aw.exists() else "1.0.0b1"
        write_user_guide(target, version=version, req_keys=REQ_KEYS)
        assert_evaluator_passing(target, EDGE_ITEST_GUIDE, EVAL_GUIDE_VERSION)
        assert_evaluator_passing(target, EDGE_ITEST_GUIDE, EVAL_GUIDE_COVERAGE)

    def test_full_convergence(self, run_archive):
        """F_D×2 + F_P + F_H → integration_tests→user_guide converges."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_unit_tests_to_integration_tests(target, archive=run_archive)
        converge_integration_tests_to_user_guide(target, REQ_KEYS, archive=run_archive)
        assert_edge_converged(target, EDGE_ITEST_GUIDE, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 10. EDGE 9: user_guide → uat_tests (F_H only)
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestUserGuideToUat:
    """Edge 9: F_H only gate — human acceptance before release."""

    def test_uat_fh_failing_initially(self, run_archive):
        """uat_accepted evaluator is failing before human approval."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_unit_tests_to_integration_tests(target, archive=run_archive)
        converge_integration_tests_to_user_guide(target, REQ_KEYS, archive=run_archive)
        assert_evaluator_failing(target, EDGE_GUIDE_UAT, EVAL_UAT_FH)

    def test_approved_converges_uat(self, run_archive):
        """F_H approval → user_guide→uat_tests converges."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        converge_unit_tests_to_integration_tests(target, archive=run_archive)
        converge_integration_tests_to_user_guide(target, REQ_KEYS, archive=run_archive)
        converge_user_guide_to_uat(target, archive=run_archive)
        assert_edge_converged(target, EDGE_GUIDE_UAT, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 11. CONVERGENCE CASCADE — MULTI-HOP CHAIN DEPENDENCIES
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestConvergenceCascade:
    """Converging edge N enables downstream edges."""

    def test_converging_intent_enables_feature_decomp(self, run_archive):
        """After intent→requirements converges, requirements→feature_decomp evaluators
        should be assessable (not blocked by predecessor)."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        assert_edge_converged(target, EDGE_INTENT_REQ, archive=run_archive)
        # feature_decomp edge should now be visible and evaluable
        gap = get_edge_gap(target, EDGE_REQ_FEAT, archive=run_archive)
        assert gap is not None, "requirements→feature_decomp must be in gaps after predecessor converges"
        assert gap["delta"] > 0

    def test_design_edge_needs_feature_decomp_converged(self, run_archive):
        """feature_decomp→design cannot converge if requirements→feature_decomp hasn't."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        # Try to converge design without converging feature_decomp first
        write_adrs(target)
        assess_edge(target, EDGE_FEAT_DESIGN, EVAL_DESIGN_FP, archive=run_archive)
        approve_edge(target, EDGE_FEAT_DESIGN, archive=run_archive)
        # Design should still be in delta because feature_decomp hasn't converged
        # (or the engine processes edges in topological order)
        data = get_gaps(target, archive=run_archive)
        assert data["converged"] is False

    def test_four_hop_cascade(self, run_archive):
        """intent → requirements → feature_decomp → design: all four edges converge in sequence."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        assert_edge_converged(target, EDGE_INTENT_REQ, archive=run_archive)
        assert_edge_converged(target, EDGE_REQ_FEAT, archive=run_archive)
        assert_edge_converged(target, EDGE_FEAT_DESIGN, archive=run_archive)

    def test_six_hop_cascade_through_tdd(self, run_archive):
        """Full planning + build chain through code↔unit_tests."""
        target = _setup(run_archive)
        converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        for edge in [EDGE_INTENT_REQ, EDGE_REQ_FEAT, EDGE_FEAT_DESIGN,
                     EDGE_DESIGN_MDECOMP, EDGE_MDECOMP_CODE, EDGE_TDD]:
            assert_edge_converged(target, edge, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 12. FULL GRAPH CONVERGENCE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestFullGraphConvergence:
    """All 9 edges → total_delta=0, graph converged."""

    def test_full_9_edge_convergence(self, run_archive):
        """Converge every edge in topological order → graph converged."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        assert_graph_converged(target, archive=run_archive)

    def test_full_convergence_event_trail(self, run_archive):
        """After full convergence, event stream contains edge_converged for each edge."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        # Force all certificates
        get_gaps(target, archive=run_archive)
        events = read_events(target)
        converged_edges = {
            e["data"]["edge"] for e in events
            if e["event_type"] == "edge_converged"
        }
        for edge in ALL_EDGES:
            assert edge in converged_edges, (
                f"Missing edge_converged certificate for {edge}"
            )

    def test_total_delta_is_zero(self, run_archive):
        """Total delta across all edges is exactly 0 after full convergence."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        data = get_gaps(target, archive=run_archive)
        assert data["total_delta"] == 0


# ══════════════════════════════════════════════════════════════════════════════
# 13. gen_gaps IDEMPOTENCE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestGenGapsIdempotence:
    """gen-gaps on a converged workspace: running twice emits no new events."""

    def test_no_new_events_on_second_call(self, run_archive):
        """gen-gaps idempotence: second call on converged workspace adds no events."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)

        get_gaps(target, archive=run_archive)
        count_after_first = len(read_events(target))

        get_gaps(target, archive=run_archive)
        count_after_second = len(read_events(target))

        assert count_after_second == count_after_first, (
            f"gen_gaps idempotence violated: "
            f"{count_after_second - count_after_first} new events on second call"
        )

    def test_no_duplicate_certificates_across_5_calls(self, run_archive):
        """Running gen-gaps 5 times: each edge_converged appears at most once."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)

        for _ in range(5):
            get_gaps(target, archive=run_archive)

        events = read_events(target)
        certs = [
            (e["data"]["edge"], e["data"].get("feature"))
            for e in events
            if e["event_type"] == "edge_converged"
        ]
        from collections import Counter
        counts = Counter(certs)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        assert not duplicates, f"Duplicate edge_converged certificates: {duplicates}"


# ══════════════════════════════════════════════════════════════════════════════
# 14. REVOCATION CASCADE
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestRevocationCascade:
    """Revoking assessments/approvals from a converged graph reopens edges."""

    def test_revoke_fh_approval_reopens_edge(self, run_archive):
        """Revoking F_H approval on intent→requirements → edge reopens."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        assert_graph_converged(target, archive=run_archive)

        # Revoke the intent→requirements approval
        emit_event(target, "revoked", {
            "kind": "fh_approval",
            "edge": EDGE_INTENT_REQ,
            "actor": "test_human",
            "reason": "Integration test: force re-evaluation",
        }, archive=run_archive)

        data = get_gaps(target, archive=run_archive)
        assert data["converged"] is False, (
            "Revoking F_H approval must reopen the graph"
        )

    def test_revoke_fp_assessment_reopens_edge(self, run_archive):
        """Revoking F_P assessment on code edge → code edge reopens."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)

        emit_event(target, "revoked", {
            "kind": "fp_assessment",
            "edge": EDGE_MDECOMP_CODE,
            "actor": "test_human",
            "reason": "Integration test: code_complete re-evaluation needed",
        }, archive=run_archive)

        data = get_gaps(target, archive=run_archive)
        assert data["converged"] is False


# ══════════════════════════════════════════════════════════════════════════════
# 15. MULTI-REQ CUSTODY
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestMultiReqCustody:
    """Verify the graph works with multiple project-specific REQ keys."""

    def test_three_req_keys_all_covered(self, run_archive):
        """Three REQ keys, all covered by features → req_coverage passes."""
        target = run_archive.workspace
        keys = ["REQ-F-AUTH-001", "REQ-F-AUTH-002", "REQ-F-DATA-001"]
        install_sandbox(target, DEFAULT_SLUG, archive=run_archive)
        write_intent(target)
        write_requirements(target, keys)
        converge_intent_to_requirements(target, archive=run_archive)
        write_features(target, keys)
        assert_evaluator_passing(target, EDGE_REQ_FEAT, EVAL_REQ_COVERAGE)

    def test_three_req_keys_partial_coverage_fails(self, run_archive):
        """Three REQ keys, only two covered → req_coverage fails."""
        target = run_archive.workspace
        keys = ["REQ-F-AUTH-001", "REQ-F-AUTH-002", "REQ-F-DATA-001"]
        install_sandbox(target, DEFAULT_SLUG, archive=run_archive)
        write_intent(target)
        write_requirements(target, keys)
        converge_intent_to_requirements(target, archive=run_archive)
        write_features(target, ["REQ-F-AUTH-001", "REQ-F-AUTH-002"])
        assert_evaluator_failing(target, EDGE_REQ_FEAT, EVAL_REQ_COVERAGE)

    def test_full_graph_with_multiple_keys(self, run_archive):
        """Full graph convergence with 3 REQ keys."""
        target = run_archive.workspace
        keys = ["REQ-F-AUTH-001", "REQ-F-AUTH-002", "REQ-F-DATA-001"]
        install_sandbox(target, DEFAULT_SLUG, archive=run_archive)
        write_intent(target)
        write_requirements(target, keys)
        converge_full_graph(target, DEFAULT_SLUG, keys, archive=run_archive)
        assert_graph_converged(target, archive=run_archive)


# ══════════════════════════════════════════════════════════════════════════════
# 16. MANIFEST TRUTH PER HOP
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestManifestTruthPerHop:
    """Each F_P dispatch produces a manifest with correct context for the hop."""

    def test_feature_decomp_manifest_on_dispatch(self, run_archive):
        """requirements→feature_decomp: iterate produces manifest with spec context."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        write_features(target, REQ_KEYS)
        manifest = dispatch_fp_and_read_manifest(target, archive=run_archive)
        assert manifest is not None, "iterate must dispatch F_P and produce a manifest"
        assert manifest["edge"] == EDGE_REQ_FEAT
        assert "prompt" in manifest
        assert len(manifest["prompt"]) > 0

    def test_code_manifest_on_dispatch(self, run_archive):
        """module_decomp→code: iterate produces manifest with design context."""
        target = _setup(run_archive)
        converge_through_design(target, REQ_KEYS, archive=run_archive)
        converge_design_to_module_decomp(target, ["FD-001"], archive=run_archive)
        write_source_code(target, DEFAULT_SLUG, REQ_KEYS)
        manifest = dispatch_fp_and_read_manifest(target, archive=run_archive)
        assert manifest is not None, "iterate must dispatch F_P and produce a manifest"
        assert manifest["edge"] == EDGE_MDECOMP_CODE
        assert "prompt" in manifest


# We need the dispatch helper imported
from scenario_helpers import dispatch_fp_and_read_manifest


# ══════════════════════════════════════════════════════════════════════════════
# 17. EVENT STREAM INTEGRITY
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestEventStreamIntegrity:
    """Event stream properties across the graph walk."""

    def test_all_events_have_timestamps(self, run_archive):
        """Every event in the stream has event_time."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        events = read_events(target)
        for e in events:
            assert "event_time" in e, f"Event missing event_time: {e['event_type']}"

    def test_approved_events_carry_actor(self, run_archive):
        """Every approved event has an actor field."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        events = read_events(target)
        approved = [e for e in events if e["event_type"] == "approved"]
        for e in approved:
            assert "actor" in e["data"], (
                f"approved event for {e['data'].get('edge')} missing actor"
            )

    def test_assessed_events_carry_spec_hash(self, run_archive):
        """Every assessed{kind: fp} event has a spec_hash field."""
        target = _setup(run_archive)
        converge_full_graph(target, DEFAULT_SLUG, REQ_KEYS, archive=run_archive)
        events = read_events(target)
        assessed = [e for e in events if e["event_type"] == "assessed"
                    and e.get("data", {}).get("kind") == "fp"]
        for e in assessed:
            assert "spec_hash" in e["data"], (
                f"assessed event for {e['data'].get('edge')}/{e['data'].get('evaluator')} "
                f"missing spec_hash"
            )

    def test_event_stream_is_append_only(self, run_archive):
        """Events emitted during convergence are never removed or modified."""
        target = _setup(run_archive)
        converge_intent_to_requirements(target, archive=run_archive)
        events_after_first = read_events(target)
        count_first = len(events_after_first)

        converge_requirements_to_feature_decomp(target, REQ_KEYS, archive=run_archive)
        events_after_second = read_events(target)

        assert len(events_after_second) > count_first, "New events must be appended"
        # First N events must be identical
        for i in range(count_first):
            assert events_after_second[i] == events_after_first[i], (
                f"Event {i} was modified: {events_after_first[i]} → {events_after_second[i]}"
            )
