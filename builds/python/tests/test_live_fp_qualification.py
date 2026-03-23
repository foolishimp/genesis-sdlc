# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-003
# Validates: REQ-F-GRAPH-001
# Validates: REQ-F-GRAPH-002
# Validates: REQ-F-GATE-001
# Validates: REQ-F-TAG-001
# Validates: REQ-F-COV-001
# Validates: REQ-F-MDECOMP-001
# Validates: REQ-F-MDECOMP-005
# Validates: REQ-F-UAT-001
# Validates: REQ-F-DOCS-002
"""
Live F_P Prompt Sufficiency Qualification for genesis_sdlc.

This is NOT a protocol test. This tests whether the manifest prompt
the engine produces is sufficient for a real LLM to generate acceptable
SDLC artifacts at each F_P edge.

The LLM receives ONLY what production guarantees:
  - the manifest prompt (preconditions, current state, gap, context, output contract)
  - nothing else — no hidden side channels

The deterministic judge for each edge checks the produced artifact.
The LLM's self-assessment is not trusted — only the judge verdict counts.

SDLC graph has 7 edges with F_P evaluators:
  1. requirements→feature_decomp   decomp_complete          — feature vectors
  2. feature_decomp→design         design_coherent           — ADRs
  3. design→module_decomp          module_schedule           — module YAMLs
  4. module_decomp→code            code_complete             — source code
  5. code↔unit_tests               coverage_complete         — tests
  6. unit_tests→integration_tests  sandbox_e2e_passed        — sandbox report
  7. integration_tests→user_guide  guide_content_certified   — user guide

Two qualification lanes:
  Lane 1 (this file): Fresh-sandbox qualification — one sandbox, one dispatch,
    one verdict. Parametrized, atomic, parallel-safe. This is the release gate.
    "Does the prompt produce a valid artifact?"
  Lane 2 (deferred): Entropy campaign — shared sandbox, ordered sequential
    dispatches, delta trend. Requires artifact fallback removal first.
    "Does the system converge over accumulated state?"

Transport: subprocess with env sanitization (ADR-022)
Architecture: F_D → subprocess → F_P

Requires: ANTHROPIC_API_KEY set, claude CLI available on PATH.
Run: pytest tests/test_live_fp_qualification.py -v -m live_fp

Archive: test_runs/live_fp_qualification/<timestamp_testname>/
  - manifest.json         — what the engine produced
  - prompt.txt            — exact payload sent to the LLM
  - raw_response.txt      — what the LLM returned
  - artifact.txt          — final artifact on disk
  - judge_verdict.json    — deterministic judge result
  - events.jsonl          — full event chain
"""
import json
import re
from pathlib import Path

import pytest

from scenario_helpers import (
    # Infrastructure
    RunArchive, install_sandbox, run_genesis, run_genesis_json, read_events,
    invoke_live_fp, _has_mcp_transport,
    # Artifact writers (for upstream convergence)
    write_intent, write_requirements, write_features, write_adrs,
    write_modules, write_source_code, write_tests, write_e2e_test,
    write_sandbox_report, write_user_guide,
    # Lifecycle
    approve_edge, assess_edge,
    converge_intent_to_requirements, converge_requirements_to_feature_decomp,
    converge_feature_decomp_to_design, converge_design_to_module_decomp,
    converge_module_decomp_to_code, converge_tdd,
    converge_unit_tests_to_integration_tests,
    converge_integration_tests_to_user_guide,
    converge_through_design, converge_through_code,
    converge_through_unit_tests,
    # Assertions
    get_gaps,
    # Constants
    EDGE_REQ_FEAT, EDGE_FEAT_DESIGN, EDGE_DESIGN_MDECOMP,
    EDGE_MDECOMP_CODE, EDGE_TDD, EDGE_UNIT_ITEST, EDGE_ITEST_GUIDE,
    EVAL_DECOMP_FP, EVAL_DESIGN_FP, EVAL_MODULE_FP,
    EVAL_CODE_FP, EVAL_COVERAGE_FP, EVAL_SANDBOX_FP, EVAL_GUIDE_FP,
    DEFAULT_SLUG,
)


# ── Skip if no agent CLI ─────────────────────────────────────────────────────

pytestmark = pytest.mark.live_fp

skip_no_agent = pytest.mark.skipif(
    not _has_mcp_transport(),
    reason="Claude Code CLI not available — live F_P qualification requires claude on PATH",
)

REQ_KEYS = ["REQ-F-IT-001"]


# ══════════════════════════════════════════════════════════════════════════════
# JUDGES — deterministic artifact quality checks per edge
#
# Each judge receives:
#   artifact: Path   — the file the LLM produced
#   manifest: dict   — the engine manifest (edge, evaluators, contexts, prompt)
#
# Each judge returns:
#   list[dict]        — [{evaluator, result, evidence}, ...]
#
# Rules come from the F_P evaluator descriptions in sdlc_graph.py and
# the F_D evaluator commands that will validate the artifacts downstream.
# The judges test the same things the engine will test — if the judge passes,
# the real F_D evaluators should pass too.
# ══════════════════════════════════════════════════════════════════════════════


def judge_feature_decomp(artifact: Path, manifest: dict) -> list[dict]:
    """Judge for requirements→feature_decomp: decomp_complete.

    Rules (from eval_decomp_fp description + req_coverage F_D):
      1. Artifact is a YAML file with id, name, satisfies fields
      2. satisfies list covers the project's REQ-F-* keys
      3. File is in .ai-workspace/features/active/ directory
    """
    # Check all .yml files in the features directory
    features_dir = artifact.parent
    yml_files = list(features_dir.glob("*.yml"))
    if not yml_files:
        # Check broader — LLM may have written elsewhere
        ws = _find_workspace(artifact)
        features_dir = ws / ".ai-workspace" / "features" / "active"
        yml_files = list(features_dir.glob("*.yml")) if features_dir.exists() else []

    failures = []

    if not yml_files:
        failures.append("no .yml feature vector files found in .ai-workspace/features/active/")
    else:
        all_content = "\n".join(f.read_text(encoding="utf-8") for f in yml_files)

        # Rule 1: well-formed YAML with required fields
        has_id = bool(re.search(r'^id:', all_content, re.MULTILINE))
        has_satisfies = bool(re.search(r'^satisfies:', all_content, re.MULTILINE))
        if not has_id:
            failures.append("feature vector missing 'id:' field")
        if not has_satisfies:
            failures.append("feature vector missing 'satisfies:' field")

        # Rule 2: REQ key coverage
        found_reqs = set(re.findall(r'REQ-F-[A-Z0-9][-A-Z0-9]*', all_content))
        expected_reqs = set(manifest.get("requirements", REQ_KEYS))
        missing = expected_reqs - found_reqs
        if missing:
            failures.append(f"uncovered REQ keys: {sorted(missing)}")

    if failures:
        return [{"evaluator": EVAL_DECOMP_FP, "result": "fail",
                 "evidence": "; ".join(failures)}]
    return [{"evaluator": EVAL_DECOMP_FP, "result": "pass",
             "evidence": f"feature vectors found ({len(yml_files)} files), "
                         f"required fields present, REQ keys covered"}]


def judge_design(artifact: Path, manifest: dict) -> list[dict]:
    """Judge for feature_decomp→design: design_coherent.

    Rules (from eval_design_fp description):
      1. ADR files exist in design/adrs/
      2. Each ADR has title, Decision/Context section
      3. Tech stack or interface mentioned
    """
    ws = _find_workspace(artifact)
    adr_dir = ws / "design" / "adrs"
    adr_files = list(adr_dir.glob("*.md")) if adr_dir.exists() else []

    failures = []

    if not adr_files:
        failures.append("no ADR .md files found in design/adrs/")
    else:
        all_content = "\n".join(f.read_text(encoding="utf-8") for f in adr_files)

        has_decision = bool(re.search(r'(Decision|Context|Consequences)', all_content, re.IGNORECASE))
        if not has_decision:
            failures.append("ADRs missing Decision/Context/Consequences sections")

        has_heading = bool(re.search(r'^#', all_content, re.MULTILINE))
        if not has_heading:
            failures.append("ADRs have no markdown headings")

    if failures:
        return [{"evaluator": EVAL_DESIGN_FP, "result": "fail",
                 "evidence": "; ".join(failures)}]
    return [{"evaluator": EVAL_DESIGN_FP, "result": "pass",
             "evidence": f"{len(adr_files)} ADR(s) with headings and decision sections"}]


def judge_module_decomp(artifact: Path, manifest: dict) -> list[dict]:
    """Judge for design→module_decomp: module_schedule.

    Rules (from eval_module_schedule_fp description):
      1. Module YAML files exist in .ai-workspace/modules/
      2. Each has: id, name, implements_features, dependencies
      3. At least one module references a feature ID
    """
    ws = _find_workspace(artifact)
    mod_dir = ws / ".ai-workspace" / "modules"
    yml_files = list(mod_dir.glob("*.yml")) if mod_dir.exists() else []

    failures = []

    if not yml_files:
        failures.append("no module .yml files in .ai-workspace/modules/")
    else:
        all_content = "\n".join(f.read_text(encoding="utf-8") for f in yml_files)

        has_id = bool(re.search(r'^id:', all_content, re.MULTILINE))
        has_name = bool(re.search(r'^name:', all_content, re.MULTILINE))
        has_features = bool(re.search(r'implements_features:', all_content))
        has_deps = bool(re.search(r'dependencies:', all_content))

        if not has_id:
            failures.append("module YAML missing 'id:' field")
        if not has_name:
            failures.append("module YAML missing 'name:' field")
        if not has_features:
            failures.append("module YAML missing 'implements_features:' field")
        if not has_deps:
            failures.append("module YAML missing 'dependencies:' field")

        # Feature linkage
        has_fd_ref = bool(re.search(r'FD-\d+', all_content))
        if not has_fd_ref:
            failures.append("no feature ID references (FD-*) found in modules")

    if failures:
        return [{"evaluator": EVAL_MODULE_FP, "result": "fail",
                 "evidence": "; ".join(failures)}]
    return [{"evaluator": EVAL_MODULE_FP, "result": "pass",
             "evidence": f"{len(yml_files)} module(s) with required fields and feature linkage"}]


def judge_code(artifact: Path, manifest: dict) -> list[dict]:
    """Judge for module_decomp→code: code_complete.

    Rules (from eval_code_fp + impl_tags F_D):
      1. Python source files exist in builds/python/src/<slug>/
      2. Files contain # Implements: REQ-F-* tags
      3. Files contain function/class definitions (not just comments)
    """
    ws = _find_workspace(artifact)
    src_dir = ws / "builds" / "python" / "src" / DEFAULT_SLUG
    py_files = list(src_dir.rglob("*.py")) if src_dir.exists() else []

    failures = []

    if not py_files:
        failures.append(f"no .py files in builds/python/src/{DEFAULT_SLUG}/")
    else:
        all_content = "\n".join(f.read_text(encoding="utf-8") for f in py_files)

        # Rule: Implements tags
        impl_tags = re.findall(r'# Implements: (REQ-F-[A-Z0-9][-A-Z0-9]*)', all_content)
        if not impl_tags:
            failures.append("no # Implements: REQ-F-* tags in source files")

        # Rule: actual code (not just tags/comments)
        has_code = bool(re.search(r'(def |class )', all_content))
        if not has_code:
            failures.append("no function or class definitions found")

    if failures:
        return [{"evaluator": EVAL_CODE_FP, "result": "fail",
                 "evidence": "; ".join(failures)}]
    return [{"evaluator": EVAL_CODE_FP, "result": "pass",
             "evidence": f"{len(py_files)} source file(s) with Implements tags and definitions"}]


def judge_tests(artifact: Path, manifest: dict) -> list[dict]:
    """Judge for code↔unit_tests: coverage_complete.

    Rules (from eval_coverage_fp + validates_tags + tests_pass + e2e_exists F_D):
      1. Test files exist in builds/python/tests/
      2. Files contain # Validates: REQ-F-* tags
      3. Files contain test functions (def test_*)
    """
    ws = _find_workspace(artifact)
    test_dir = ws / "builds" / "python" / "tests"
    py_files = [f for f in test_dir.rglob("*.py")
                if f.name.startswith("test_")] if test_dir.exists() else []

    failures = []

    if not py_files:
        failures.append("no test_*.py files in builds/python/tests/")
    else:
        all_content = "\n".join(f.read_text(encoding="utf-8") for f in py_files)

        val_tags = re.findall(r'# Validates: (REQ-F-[A-Z0-9][-A-Z0-9]*)', all_content)
        if not val_tags:
            failures.append("no # Validates: REQ-F-* tags in test files")

        has_test_fns = bool(re.search(r'def test_', all_content))
        if not has_test_fns:
            failures.append("no test functions (def test_*) found")

    if failures:
        return [{"evaluator": EVAL_COVERAGE_FP, "result": "fail",
                 "evidence": "; ".join(failures)}]
    return [{"evaluator": EVAL_COVERAGE_FP, "result": "pass",
             "evidence": f"{len(py_files)} test file(s) with Validates tags and test functions"}]


def judge_sandbox_report(artifact: Path, manifest: dict) -> list[dict]:
    """Judge for unit_tests→integration_tests: sandbox_e2e_passed.

    Rules (from eval_sandbox_run description + sandbox_report_exists F_D):
      1. sandbox_report.json exists at .ai-workspace/uat/
      2. JSON is well-formed with required fields
      3. all_pass and install_success are true
    """
    ws = _find_workspace(artifact)
    report_path = ws / ".ai-workspace" / "uat" / "sandbox_report.json"

    failures = []

    if not report_path.exists():
        failures.append("sandbox_report.json not found at .ai-workspace/uat/")
    else:
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return [{"evaluator": EVAL_SANDBOX_FP, "result": "fail",
                     "evidence": f"sandbox_report.json is not valid JSON: {e}"}]

        for field in ("install_success", "all_pass", "test_count", "sandbox_path"):
            if field not in data:
                failures.append(f"missing required field: {field}")

        if not data.get("install_success"):
            failures.append("install_success is not true")
        if not data.get("all_pass"):
            failures.append("all_pass is not true")

    if failures:
        return [{"evaluator": EVAL_SANDBOX_FP, "result": "fail",
                 "evidence": "; ".join(failures)}]
    return [{"evaluator": EVAL_SANDBOX_FP, "result": "pass",
             "evidence": "sandbox report well-formed, install_success=true, all_pass=true"}]


def judge_user_guide(artifact: Path, manifest: dict) -> list[dict]:
    """Judge for integration_tests→user_guide: guide_content_certified.

    Rules (from eval_guide_content description + guide_version + guide_coverage F_D):
      1. USER_GUIDE.md exists at docs/
      2. Contains **Version**: tag
      3. Contains <!-- Covers: REQ-F-* --> tags
      4. Covers install, commands, getting started
    """
    ws = _find_workspace(artifact)
    guide_path = ws / "docs" / "USER_GUIDE.md"

    failures = []

    if not guide_path.exists():
        failures.append("docs/USER_GUIDE.md not found")
    else:
        content = guide_path.read_text(encoding="utf-8")

        # Version tag
        has_version = bool(re.search(r'\*\*Version\*\*:', content))
        if not has_version:
            failures.append("missing **Version**: tag")

        # REQ coverage tags
        covers_tags = re.findall(r'<!-- Covers:([^>]+)-->', content)
        found_reqs = set()
        for tag in covers_tags:
            found_reqs.update(re.findall(r'REQ-F-[A-Z0-9][-A-Z0-9]*', tag))
        if not found_reqs:
            failures.append("no <!-- Covers: REQ-F-* --> tags found")

        # Content quality — must mention commands and getting started
        has_commands = bool(re.search(
            r'(gen-start|gen-gaps|gen-iterate|command)',
            content, re.IGNORECASE,
        ))
        if not has_commands:
            failures.append("no mention of genesis commands (gen-start, gen-gaps, gen-iterate)")

        has_getting_started = bool(re.search(
            r'(getting started|install|setup|quick start|overview)',
            content, re.IGNORECASE,
        ))
        if not has_getting_started:
            failures.append("no getting started / install / overview section")

    if failures:
        return [{"evaluator": EVAL_GUIDE_FP, "result": "fail",
                 "evidence": "; ".join(failures)}]
    return [{"evaluator": EVAL_GUIDE_FP, "result": "pass",
             "evidence": f"USER_GUIDE.md present, version tag, "
                         f"{len(found_reqs)} REQ coverage tags, commands documented"}]


# ── Workspace finder ──────────────────────────────────────────────────────────

def _find_workspace(artifact: Path) -> Path:
    """Walk up from artifact path to find the workspace root (.genesis/ marker)."""
    p = artifact.resolve()
    for _ in range(10):
        if (p / ".genesis").exists():
            return p
        p = p.parent
    return artifact.parent


# ══════════════════════════════════════════════════════════════════════════════
# SETUP HELPERS — converge upstream edges before F_P dispatch
#
# Each setup function installs a sandbox, writes the minimal artifacts needed
# for all upstream edges to converge, then leaves the target edge's F_D gates
# passing so that gen-iterate can dispatch F_P.
# ══════════════════════════════════════════════════════════════════════════════

def _base_setup(archive: RunArchive, req_keys: list[str] = None) -> Path:
    """Install sandbox with intent + requirements."""
    req_keys = req_keys or REQ_KEYS
    target = archive.workspace
    install_sandbox(target, DEFAULT_SLUG, archive=archive)
    write_intent(target)
    write_requirements(target, req_keys)
    return target


def _setup_for_decomp(archive: RunArchive) -> Path:
    """Setup for requirements→feature_decomp F_P dispatch.

    Upstream: intent→requirements (F_H only — converge with approval).
    F_D on this edge: req_coverage — must PASS for F_P dispatch (REQ-F-GATE-002).
    We write minimal feature vectors that satisfy req_coverage but leave
    decomp_complete (F_P) un-assessed so iterate dispatches F_P.
    """
    target = _base_setup(archive)
    converge_intent_to_requirements(target, archive=archive)
    # Write minimal features to pass req_coverage F_D gate
    write_features(target, REQ_KEYS)
    return target


def _setup_for_design(archive: RunArchive) -> Path:
    """Setup for feature_decomp→design F_P dispatch.

    Upstream: converge through feature_decomp.
    """
    target = _base_setup(archive)
    converge_intent_to_requirements(target, archive=archive)
    converge_requirements_to_feature_decomp(target, REQ_KEYS, archive=archive)
    return target


def _setup_for_module_decomp(archive: RunArchive) -> Path:
    """Setup for design→module_decomp F_P dispatch.

    Upstream: converge through design.
    F_D on this edge: module_coverage — every feature stem must appear in ≥1 module YAML.
    We write minimal module YAMLs that reference the feature IDs to pass module_coverage.
    """
    target = _base_setup(archive)
    converge_through_design(target, REQ_KEYS, archive=archive)
    # Write minimal modules to pass module_coverage F_D gate
    write_modules(target, ["FD-001"])
    return target


def _setup_for_code(archive: RunArchive) -> Path:
    """Setup for module_decomp→code F_P dispatch.

    Upstream: converge through module_decomp.
    """
    target = _base_setup(archive)
    converge_through_design(target, REQ_KEYS, archive=archive)
    converge_design_to_module_decomp(target, ["FD-001"], archive=archive)
    return target


def _setup_for_tests(archive: RunArchive) -> Path:
    """Setup for code↔unit_tests F_P dispatch.

    Upstream: converge through code.
    F_D on this edge: tests_pass, validates_tags, e2e_tests_exist.
    We write minimal test files that pass all F_D gates to enable F_P dispatch.
    """
    target = _base_setup(archive)
    converge_through_code(target, DEFAULT_SLUG, REQ_KEYS, archive=archive)
    # Write minimal tests to pass F_D gates (tests_pass, validates_tags, e2e_tests_exist)
    write_tests(target, DEFAULT_SLUG, REQ_KEYS)
    write_e2e_test(target, DEFAULT_SLUG)
    return target


def _setup_for_sandbox(archive: RunArchive) -> Path:
    """Setup for unit_tests→integration_tests F_P dispatch.

    Upstream: converge through unit_tests.
    F_D on this edge: sandbox_report_exists.
    We write a placeholder sandbox report to pass F_D and enable F_P dispatch.
    """
    target = _base_setup(archive)
    converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=archive)
    # Write placeholder sandbox report to pass sandbox_report_exists F_D gate
    write_sandbox_report(target)
    return target


def _setup_for_guide(archive: RunArchive) -> Path:
    """Setup for integration_tests→user_guide F_P dispatch.

    Upstream: converge through integration_tests.
    F_D on this edge: guide_version_current, guide_req_coverage.
    We write a placeholder USER_GUIDE.md to pass F_D and enable F_P dispatch.
    """
    target = _base_setup(archive)
    converge_through_unit_tests(target, DEFAULT_SLUG, REQ_KEYS, archive=archive)
    converge_unit_tests_to_integration_tests(target, archive=archive)
    # Write placeholder user guide to pass F_D gates
    write_user_guide(target, req_keys=REQ_KEYS)
    return target


# ══════════════════════════════════════════════════════════════════════════════
# SMOKE TESTS — single-run protocol validation per edge
#
# Does the prompt produce anything the judge can evaluate?
# We don't assert pass — we assert the protocol completed.
# ══════════════════════════════════════════════════════════════════════════════

@skip_no_agent
class TestLiveFpSmoke:
    """Single-run smoke: does each edge's manifest prompt produce a judgeable artifact?"""

    def test_decomp_single_run(self, run_archive):
        """requirements→feature_decomp: LLM produces feature vectors."""
        target = _setup_for_decomp(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=".ai-workspace/features/active/FD-001.yml",
            edge_name=EDGE_REQ_FEAT,
            judge=judge_feature_decomp,
            archive=run_archive,
        )
        assert result.failure_class is None, (
            f"transport failure ({result.failure_class}): "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'unknown'}"
        )
        assert result.raw_response, "LLM must produce a response"
        assert result.judge_assessments, "judge must produce assessments"
        assert result.model, "model must be recorded"

    def test_design_single_run(self, run_archive):
        """feature_decomp→design: LLM produces ADRs."""
        target = _setup_for_design(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path="design/adrs/ADR-001-initial.md",
            edge_name=EDGE_FEAT_DESIGN,
            judge=judge_design,
            archive=run_archive,
        )
        assert result.failure_class is None, (
            f"transport failure ({result.failure_class}): "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'unknown'}"
        )
        assert result.raw_response, "LLM must produce a response"
        assert result.judge_assessments, "judge must produce assessments"

    def test_module_decomp_single_run(self, run_archive):
        """design→module_decomp: LLM produces module YAMLs."""
        target = _setup_for_module_decomp(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=".ai-workspace/modules/MOD-001.yml",
            edge_name=EDGE_DESIGN_MDECOMP,
            judge=judge_module_decomp,
            archive=run_archive,
        )
        assert result.failure_class is None, (
            f"transport failure ({result.failure_class}): "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'unknown'}"
        )
        assert result.raw_response, "LLM must produce a response"
        assert result.judge_assessments, "judge must produce assessments"

    def test_code_single_run(self, run_archive):
        """module_decomp→code: LLM produces source code."""
        target = _setup_for_code(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=f"builds/python/src/{DEFAULT_SLUG}/core.py",
            edge_name=EDGE_MDECOMP_CODE,
            judge=judge_code,
            archive=run_archive,
        )
        assert result.failure_class is None, (
            f"transport failure ({result.failure_class}): "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'unknown'}"
        )
        assert result.raw_response, "LLM must produce a response"
        assert result.judge_assessments, "judge must produce assessments"

    def test_tests_single_run(self, run_archive):
        """code↔unit_tests: LLM produces test files."""
        target = _setup_for_tests(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=f"builds/python/tests/test_{DEFAULT_SLUG}.py",
            edge_name=EDGE_TDD,
            judge=judge_tests,
            archive=run_archive,
        )
        assert result.failure_class is None, (
            f"transport failure ({result.failure_class}): "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'unknown'}"
        )
        assert result.raw_response, "LLM must produce a response"
        assert result.judge_assessments, "judge must produce assessments"

    def test_sandbox_single_run(self, run_archive):
        """unit_tests→integration_tests: LLM runs sandbox + writes report."""
        target = _setup_for_sandbox(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=".ai-workspace/uat/sandbox_report.json",
            edge_name=EDGE_UNIT_ITEST,
            judge=judge_sandbox_report,
            archive=run_archive,
        )
        assert result.failure_class is None, (
            f"transport failure ({result.failure_class}): "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'unknown'}"
        )
        assert result.raw_response, "LLM must produce a response"
        assert result.judge_assessments, "judge must produce assessments"

    def test_guide_single_run(self, run_archive):
        """integration_tests→user_guide: LLM produces USER_GUIDE.md."""
        target = _setup_for_guide(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path="docs/USER_GUIDE.md",
            edge_name=EDGE_ITEST_GUIDE,
            judge=judge_user_guide,
            archive=run_archive,
        )
        assert result.failure_class is None, (
            f"transport failure ({result.failure_class}): "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'unknown'}"
        )
        assert result.raw_response, "LLM must produce a response"
        assert result.judge_assessments, "judge must produce assessments"


# ══════════════════════════════════════════════════════════════════════════════
# Lane 1: Fresh-sandbox qualification — release gate
#
# Each parametrized run gets its own sandbox. One dispatch, one verdict.
# Parallel-safe. "Does the prompt produce a valid artifact in isolation?"
#
# Lane 2 (entropy campaign — shared sandbox, sequential, delta trend) is
# deferred until the raw_response→artifact fallback is removed.
# ══════════════════════════════════════════════════════════════════════════════

_QUAL_RUNS = 10


@skip_no_agent
class TestDecompQualification:
    """requirements→feature_decomp: 10 fresh-sandbox runs. Release gate."""

    @pytest.mark.parametrize("run_id", range(_QUAL_RUNS))
    def test_decomp_run(self, run_id, run_archive):
        target = _setup_for_decomp(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=".ai-workspace/features/active/FD-001.yml",
            edge_name=EDGE_REQ_FEAT,
            judge=judge_feature_decomp,
            archive=run_archive,
        )
        assert result.judge_passed, (
            f"run {run_id}: "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'no assessment'}"
        )


@skip_no_agent
class TestDesignQualification:
    """feature_decomp→design: 10 fresh-sandbox runs. Release gate."""

    @pytest.mark.parametrize("run_id", range(_QUAL_RUNS))
    def test_design_run(self, run_id, run_archive):
        target = _setup_for_design(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path="design/adrs/ADR-001-initial.md",
            edge_name=EDGE_FEAT_DESIGN,
            judge=judge_design,
            archive=run_archive,
        )
        assert result.judge_passed, (
            f"run {run_id}: "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'no assessment'}"
        )


@skip_no_agent
class TestModuleDecompQualification:
    """design→module_decomp: 10 fresh-sandbox runs. Release gate."""

    @pytest.mark.parametrize("run_id", range(_QUAL_RUNS))
    def test_module_decomp_run(self, run_id, run_archive):
        target = _setup_for_module_decomp(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=".ai-workspace/modules/MOD-001.yml",
            edge_name=EDGE_DESIGN_MDECOMP,
            judge=judge_module_decomp,
            archive=run_archive,
        )
        assert result.judge_passed, (
            f"run {run_id}: "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'no assessment'}"
        )


@skip_no_agent
class TestCodeQualification:
    """module_decomp→code: 10 fresh-sandbox runs. Release gate."""

    @pytest.mark.parametrize("run_id", range(_QUAL_RUNS))
    def test_code_run(self, run_id, run_archive):
        target = _setup_for_code(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=f"builds/python/src/{DEFAULT_SLUG}/core.py",
            edge_name=EDGE_MDECOMP_CODE,
            judge=judge_code,
            archive=run_archive,
        )
        assert result.judge_passed, (
            f"run {run_id}: "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'no assessment'}"
        )


@skip_no_agent
class TestTestsQualification:
    """code↔unit_tests: 10 fresh-sandbox runs. Release gate."""

    @pytest.mark.parametrize("run_id", range(_QUAL_RUNS))
    def test_tests_run(self, run_id, run_archive):
        target = _setup_for_tests(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=f"builds/python/tests/test_{DEFAULT_SLUG}.py",
            edge_name=EDGE_TDD,
            judge=judge_tests,
            archive=run_archive,
        )
        assert result.judge_passed, (
            f"run {run_id}: "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'no assessment'}"
        )


@skip_no_agent
class TestSandboxQualification:
    """unit_tests→integration_tests: 10 fresh-sandbox runs. Release gate."""

    @pytest.mark.parametrize("run_id", range(_QUAL_RUNS))
    def test_sandbox_run(self, run_id, run_archive):
        target = _setup_for_sandbox(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path=".ai-workspace/uat/sandbox_report.json",
            edge_name=EDGE_UNIT_ITEST,
            judge=judge_sandbox_report,
            archive=run_archive,
        )
        assert result.judge_passed, (
            f"run {run_id}: "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'no assessment'}"
        )


@skip_no_agent
class TestGuideQualification:
    """integration_tests→user_guide: 10 fresh-sandbox runs. Release gate."""

    @pytest.mark.parametrize("run_id", range(_QUAL_RUNS))
    def test_guide_run(self, run_id, run_archive):
        target = _setup_for_guide(run_archive)
        result = invoke_live_fp(
            target,
            artifact_path="docs/USER_GUIDE.md",
            edge_name=EDGE_ITEST_GUIDE,
            judge=judge_user_guide,
            archive=run_archive,
        )
        assert result.judge_passed, (
            f"run {run_id}: "
            f"{result.judge_assessments[0]['evidence'] if result.judge_assessments else 'no assessment'}"
        )


# ══════════════════════════════════════════════════════════════════════════════
# MANIFEST TRUTH — verify the engine produces correct manifests per edge
#
# These tests don't require the agent CLI — they validate the manifest structure
# that the LLM would receive, without actually invoking the LLM.
# ══════════════════════════════════════════════════════════════════════════════

@pytest.mark.integration
class TestManifestSufficiency:
    """Verify the manifest contains everything the LLM needs per edge.

    These are deterministic — no LLM, no agent. They prove the engine
    assembles the right context for each F_P dispatch.
    """

    def test_decomp_manifest_has_requirements_context(self, run_archive):
        """requirements→feature_decomp manifest carries spec context."""
        target = _setup_for_decomp(run_archive)
        result = run_genesis(target, "iterate", archive=run_archive)
        assert result.returncode == 0, f"iterate failed (exit {result.returncode}):\n{result.stderr}"
        data = json.loads(result.stdout)
        assert "fp_manifest_path" in data, "iterate must produce fp_manifest_path"
        manifest = json.loads(Path(data["fp_manifest_path"]).read_text())
        assert "prompt" in manifest
        assert len(manifest["prompt"]) > 100, "prompt too short to be useful"
        assert EDGE_REQ_FEAT in manifest.get("edge", "")

    def test_design_manifest_has_intent_context(self, run_archive):
        """feature_decomp→design manifest carries intent + spec context."""
        target = _setup_for_design(run_archive)
        result = run_genesis(target, "iterate", archive=run_archive)
        assert result.returncode == 0, f"iterate failed (exit {result.returncode}):\n{result.stderr}"
        data = json.loads(result.stdout)
        assert "fp_manifest_path" in data, "iterate must produce fp_manifest_path"
        manifest = json.loads(Path(data["fp_manifest_path"]).read_text())
        assert "prompt" in manifest
        prompt = manifest["prompt"]
        assert "design" in prompt.lower() or "feature" in prompt.lower()

    def test_code_manifest_has_design_context(self, run_archive):
        """module_decomp→code manifest carries design ADR context."""
        target = _setup_for_code(run_archive)
        result = run_genesis(target, "iterate", archive=run_archive)
        assert result.returncode == 0, f"iterate failed (exit {result.returncode}):\n{result.stderr}"
        data = json.loads(result.stdout)
        assert "fp_manifest_path" in data, "iterate must produce fp_manifest_path"
        manifest = json.loads(Path(data["fp_manifest_path"]).read_text())
        assert "prompt" in manifest
        assert len(manifest["prompt"]) > 50

    def test_guide_manifest_has_spec_context(self, run_archive):
        """integration_tests→user_guide manifest carries spec context."""
        target = _setup_for_guide(run_archive)
        result = run_genesis(target, "iterate", archive=run_archive)
        assert result.returncode == 0, f"iterate failed (exit {result.returncode}):\n{result.stderr}"
        data = json.loads(result.stdout)
        assert "fp_manifest_path" in data, "iterate must produce fp_manifest_path"
        manifest = json.loads(Path(data["fp_manifest_path"]).read_text())
        assert "prompt" in manifest
        assert "guide" in manifest["prompt"].lower() or "user" in manifest["prompt"].lower()
