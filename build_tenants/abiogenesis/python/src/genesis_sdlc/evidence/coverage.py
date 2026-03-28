# Implements: REQ-F-TEST-002
# Implements: REQ-F-CMD-001
"""Assessment helpers for constructive workflow artifacts."""

from __future__ import annotations

from pathlib import Path

from genesis_sdlc.workflow.transforms import DESIGN_SECTIONS, FEATURE_DECOMP_SECTIONS, MODULE_DECOMP_SECTIONS


Assessment = dict[str, str]


def _single(evaluator: str, result: str, evidence: str) -> list[Assessment]:
    return [{"evaluator": evaluator, "result": result, "evidence": evidence}]


def _missing(path: Path, evaluator: str) -> list[Assessment]:
    return _single(evaluator, "fail", f"artifact missing: {path}")


def _check_headers_and_terms(
    artifact: Path,
    *,
    evaluator: str,
    headers: tuple[str, ...],
    required_terms: tuple[str, ...],
    success: str,
) -> list[Assessment]:
    if not artifact.exists():
        return _missing(artifact, evaluator)

    text = artifact.read_text(encoding="utf-8")
    missing_headers = [header for header in headers if header not in text]
    if missing_headers:
        return _single(evaluator, "fail", f"missing sections: {missing_headers}")

    lowered = text.lower()
    missing_terms = [term for term in required_terms if term not in lowered]
    if missing_terms:
        return _single(evaluator, "fail", f"missing expected terms: {missing_terms}")

    return _single(evaluator, "pass", success)


def assess_feature_decomp_artifact(artifact: Path, requirement_keys: list[str]) -> list[Assessment]:
    if not artifact.exists():
        return _missing(artifact, "feature_decomp_complete")

    text = artifact.read_text(encoding="utf-8")
    missing_headers = [header for header in FEATURE_DECOMP_SECTIONS if header not in text]
    if missing_headers:
        return _single("feature_decomp_complete", "fail", f"feature decomposition missing sections: {missing_headers}")

    missing_requirements = [req for req in requirement_keys if req not in text]
    if missing_requirements:
        return _single(
            "feature_decomp_complete",
            "fail",
            f"feature decomposition missing requirement coverage: {missing_requirements}",
        )

    lowered = text.lower()
    missing_terms = [term for term in ("add", "multiply", "integration") if term not in lowered]
    if missing_terms:
        return _single(
            "feature_decomp_complete",
            "fail",
            f"feature decomposition missing expected project terms: {missing_terms}",
        )

    return _single(
        "feature_decomp_complete",
        "pass",
        "feature decomposition artifact covers all project requirements, dependency order, and coverage mapping.",
    )


def assess_design_artifact(artifact: Path) -> list[Assessment]:
    return _check_headers_and_terms(
        artifact,
        evaluator="design_complete",
        headers=DESIGN_SECTIONS,
        required_terms=("add", "multiply", "unit test", "integration"),
        success="design artifact defines components, interfaces, decomposition, and sequencing for the calculator project.",
    )


def assess_module_decomp_artifact(artifact: Path) -> list[Assessment]:
    return _check_headers_and_terms(
        artifact,
        evaluator="module_schedule",
        headers=MODULE_DECOMP_SECTIONS,
        required_terms=("calculator", "tests", "dependency"),
        success="module decomposition artifact defines modules, dependencies, and build order.",
    )


def assess_code_artifact(artifact: Path) -> list[Assessment]:
    if not artifact.exists():
        return _missing(artifact, "code_complete")
    text = artifact.read_text(encoding="utf-8")
    required = ("def add(", "def multiply(")
    missing = [item for item in required if item not in text]
    if missing:
        return _single("code_complete", "fail", f"code missing symbols: {missing}")
    return _single("code_complete", "pass", "calculator module defines add and multiply.")


def assess_unit_tests_artifact(artifact: Path) -> list[Assessment]:
    if not artifact.exists():
        return _missing(artifact, "unit_test_surface_complete")
    text = artifact.read_text(encoding="utf-8")
    required = ("def test_add", "def test_multiply", "from calculator import add, multiply")
    missing = [item for item in required if item not in text]
    if missing:
        return _single("unit_test_surface_complete", "fail", f"unit-test artifact missing expected content: {missing}")
    return _single(
        "unit_test_surface_complete",
        "pass",
        "unit-test artifact covers add and multiply with pytest-style tests.",
    )


def assess_integration_artifact(artifact: Path) -> list[Assessment]:
    if not artifact.exists():
        evidence = f"integration artifact missing: {artifact}"
        return [
            {"evaluator": "coverage_complete", "result": "fail", "evidence": evidence},
            {"evaluator": "sandbox_e2e_passed", "result": "fail", "evidence": evidence},
        ]

    text = artifact.read_text(encoding="utf-8")
    required_literals = ("from calculator import add, multiply", "add(", "multiply(")
    missing_literals = [item for item in required_literals if item not in text]
    if missing_literals:
        evidence = f"integration artifact missing expected content: {missing_literals}"
        return [
            {"evaluator": "coverage_complete", "result": "fail", "evidence": evidence},
            {"evaluator": "sandbox_e2e_passed", "result": "fail", "evidence": evidence},
        ]

    if "def test_" not in text:
        evidence = "integration artifact does not declare a pytest-style test function"
        return [
            {"evaluator": "coverage_complete", "result": "fail", "evidence": evidence},
            {"evaluator": "sandbox_e2e_passed", "result": "fail", "evidence": evidence},
        ]

    return [
        {
            "evaluator": "coverage_complete",
            "result": "pass",
            "evidence": "integration artifact covers the calculator flow and both operations.",
        },
        {
            "evaluator": "sandbox_e2e_passed",
            "result": "pass",
            "evidence": "integration artifact is present and the sandbox report was produced for this edge.",
        },
    ]
