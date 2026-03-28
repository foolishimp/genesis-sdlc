# Validates: REQ-F-CMD-001
# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-004
# Validates: REQ-F-TEST-005
"""Live qualification lane for sandbox-backed workflow scenarios."""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from genesis_sdlc.workflow.transforms import (
    DESIGN_SECTIONS,
    FEATURE_DECOMP_SECTIONS,
    MODULE_DECOMP_SECTIONS,
    build_assessment_prompt,
    build_constructive_prompt,
    get_edge_transform_contract,
)

from .live_transport import call_agent, has_agent
from .sandbox_runtime import install_real_sandbox, run_genesis


INTEGRATION_EDGE = "[code, unit_tests]→integration_tests"
DOWNSTREAM_RELEASE_EDGES = {
    "[design, integration_tests]→user_guide",
    "[requirements, design, integration_tests]→bootloader",
    "[requirements, integration_tests]→uat_tests",
}


pytestmark = [pytest.mark.e2e, pytest.mark.live_fp]

_FEATURE_DECOMP_ARTIFACT = Path("output/feature_decomp.md")
_DESIGN_ARTIFACT = Path("output/design.md")
_MODULE_DECOMP_ARTIFACT = Path("output/module_decomp.md")
_CODE_ARTIFACT = Path("output/src/calculator.py")
_UNIT_TESTS_ARTIFACT = Path("output/tests/test_calculator.py")
_INTEGRATION_ARTIFACT = Path("output/tests/test_integration.py")


def _word_count(text: str) -> int:
    return len(text.split())


_MINIMAL_INTENT = """# Intent

## Summary

This sandbox project exists to qualify the real genesis_sdlc workflow against a
small bounded software problem rather than against the genesis_sdlc framework
itself.

## Goal

Carry a simple project from intent through requirements, feature decomposition,
design, module decomposition, code, unit tests, and integration tests.

## Project Shape

The project is a tiny Python calculator capability with two operations:

- add(a, b)
- multiply(a, b)

The implementation should stay intentionally small and easy to reason about in a
single live agent turn.
"""


_MINIMAL_REQUIREMENTS = """# Core Requirements

### REQ-PROJ-001
The project shall provide an `add(a, b)` operation that returns the arithmetic
sum of two integers.

Acceptance Criteria
- `add(2, 3) == 5`
- `add(-1, 1) == 0`

### REQ-PROJ-002
The project shall provide a `multiply(a, b)` operation that returns the
arithmetic product of two integers.

Acceptance Criteria
- `multiply(3, 4) == 12`
- `multiply(-2, 5) == -10`

### REQ-PROJ-003
The project shall include unit tests that verify the add and multiply
operations.

Acceptance Criteria
- unit tests cover positive and negative examples
- the unit-test surface is runnable by pytest

### REQ-PROJ-004
The project shall include an integration test that proves the calculator module
can be imported and its operations used together in one flow.

Acceptance Criteria
- the integration test imports the project code
- the integration test exercises both operations in one scenario
"""


def _live_agent() -> str:
    return os.environ.get("GSDLC_LIVE_AGENT", "codex")


def _live_enabled() -> bool:
    return os.environ.get("CODEX_LIVE_FP") == "1" and has_agent(_live_agent())


def _seed_minimal_project_spec(workspace: Path, *, archive) -> None:
    spec_root = workspace / "specification"
    requirements_root = spec_root / "requirements"

    if requirements_root.exists():
        shutil.rmtree(requirements_root)
    requirements_root.mkdir(parents=True, exist_ok=True)

    (spec_root / "INTENT.md").write_text(_MINIMAL_INTENT, encoding="utf-8")
    (requirements_root / "01-project-core.md").write_text(_MINIMAL_REQUIREMENTS, encoding="utf-8")
    (requirements_root / "README.md").write_text(
        "# Project Requirements\n\nThis sandbox uses a minimal project requirement surface for live qualification.\n",
        encoding="utf-8",
    )

    archive.capture_text("seeded_INTENT.md", _MINIMAL_INTENT)
    archive.capture_text("seeded_requirements_01-project-core.md", _MINIMAL_REQUIREMENTS)
    archive.update_summary(
        seeded_project_spec=True,
        seeded_requirement_keys=["REQ-PROJ-001", "REQ-PROJ-002", "REQ-PROJ-003", "REQ-PROJ-004"],
    )


def _run_json(workspace: Path, *args: str, archive=None, label: str | None = None) -> dict:
    result = run_genesis(workspace, *args, archive=archive, label=label)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def _emit_event(workspace: Path, event_type: str, data: dict, *, archive=None, label: str | None = None) -> None:
    result = run_genesis(
        workspace,
        "emit-event",
        "--type",
        event_type,
        "--data",
        json.dumps(data),
        archive=archive,
        label=label or f"emit {event_type}",
    )
    assert result.returncode == 0, result.stderr


def _write_passing_sandbox_report(workspace: Path) -> None:
    report_path = workspace / ".ai-workspace" / "uat" / "sandbox_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "all_pass": True,
                "scenario": "live_steel_thread",
                "notes": "integration edge evidence produced by live steel-thread test",
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _write_result_file(result_path: Path, *, edge: str, actor: str, assessments: list[dict]) -> None:
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text(
        json.dumps(
            {
                "edge": edge,
                "actor": actor,
                "assessments": assessments,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _judge_feature_decomp(artifact: Path, required_keys: list[str]) -> list[dict]:
    if not artifact.exists():
        return [
            {
                "evaluator": "feature_decomp_complete",
                "result": "fail",
                "evidence": f"feature decomposition artifact missing: {artifact}",
            }
        ]

    text = artifact.read_text(encoding="utf-8")
    missing_headers = [header for header in FEATURE_DECOMP_SECTIONS if header not in text]
    if missing_headers:
        return [
            {
                "evaluator": "feature_decomp_complete",
                "result": "fail",
                "evidence": f"feature decomposition missing sections: {missing_headers}",
            }
        ]

    missing_requirements = [req for req in required_keys if req not in text]
    if missing_requirements:
        return [
            {
                "evaluator": "feature_decomp_complete",
                "result": "fail",
                "evidence": f"feature decomposition missing requirement coverage: {missing_requirements}",
            }
        ]

    missing_terms = [term for term in ("add", "multiply", "integration") if term not in text.lower()]
    if missing_terms:
        return [
            {
                "evaluator": "feature_decomp_complete",
                "result": "fail",
                "evidence": f"feature decomposition missing expected project terms: {missing_terms}",
            }
        ]

    return [
        {
            "evaluator": "feature_decomp_complete",
            "result": "pass",
            "evidence": "feature decomposition artifact covers all project requirements, dependency order, and coverage mapping.",
        }
    ]


def _judge_headers_and_requirements(
    artifact: Path,
    *,
    evaluator: str,
    headers: tuple[str, ...],
    required_terms: tuple[str, ...],
    evidence_label: str,
) -> list[dict]:
    if not artifact.exists():
        return [{"evaluator": evaluator, "result": "fail", "evidence": f"artifact missing: {artifact}"}]

    text = artifact.read_text(encoding="utf-8")
    missing_headers = [header for header in headers if header not in text]
    if missing_headers:
        return [{"evaluator": evaluator, "result": "fail", "evidence": f"missing sections: {missing_headers}"}]

    missing_terms = [term for term in required_terms if term not in text.lower()]
    if missing_terms:
        return [{"evaluator": evaluator, "result": "fail", "evidence": f"missing expected terms: {missing_terms}"}]

    return [{"evaluator": evaluator, "result": "pass", "evidence": evidence_label}]


def _judge_code_artifact(artifact: Path) -> list[dict]:
    if not artifact.exists():
        return [{"evaluator": "code_complete", "result": "fail", "evidence": f"code artifact missing: {artifact}"}]
    text = artifact.read_text(encoding="utf-8")
    required = ("def add(", "def multiply(")
    missing = [item for item in required if item not in text]
    if missing:
        return [{"evaluator": "code_complete", "result": "fail", "evidence": f"code missing symbols: {missing}"}]
    return [{"evaluator": "code_complete", "result": "pass", "evidence": "calculator module defines add and multiply."}]


def _judge_unit_tests_artifact(artifact: Path) -> list[dict]:
    if not artifact.exists():
        return [
            {
                "evaluator": "unit_test_surface_complete",
                "result": "fail",
                "evidence": f"unit-test artifact missing: {artifact}",
            }
        ]
    text = artifact.read_text(encoding="utf-8")
    required = ("def test_add", "def test_multiply", "from calculator import add, multiply")
    missing = [item for item in required if item not in text]
    if missing:
        return [
            {
                "evaluator": "unit_test_surface_complete",
                "result": "fail",
                "evidence": f"unit-test artifact missing expected content: {missing}",
            }
        ]
    return [
        {
            "evaluator": "unit_test_surface_complete",
            "result": "pass",
            "evidence": "unit-test artifact covers add and multiply with pytest-style tests.",
        }
    ]


def _judge_integration_artifact(artifact: Path) -> list[dict]:
    if not artifact.exists():
        return [
            {"evaluator": "coverage_complete", "result": "fail", "evidence": f"integration artifact missing: {artifact}"},
            {"evaluator": "sandbox_e2e_passed", "result": "fail", "evidence": f"integration artifact missing: {artifact}"},
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


def _dispatch_live_fp(workspace: Path, manifest: dict, *, archive, agent: str, stem: str) -> None:
    run_archive = archive
    run_archive.capture_json(f"{stem}_manifest.json", manifest)
    qualification_prompt = build_assessment_prompt(manifest)
    run_archive.capture_text(f"{stem}_prompt.txt", qualification_prompt)

    response = call_agent(
        qualification_prompt,
        str(workspace),
        agent=agent,
        timeout=240,
    )
    run_archive.capture_text(f"{stem}_raw_response.txt", response)

    result_path = Path(manifest["result_path"])
    assert result_path.is_file(), "live agent must write the requested result JSON"
    result_payload = json.loads(result_path.read_text(encoding="utf-8"))
    run_archive.capture_json(f"{stem}_result.json", result_payload)

    assess = run_genesis(
        workspace,
        "assess-result",
        "--result",
        str(result_path),
        archive=run_archive,
        label=f"genesis assess-result {manifest['edge']}",
    )
    assert assess.returncode == 0, assess.stderr


def _qualify_feature_decomp_live(workspace: Path, manifest: dict, *, archive, agent: str) -> None:
    artifact_path = workspace / _FEATURE_DECOMP_ARTIFACT
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    if not artifact_path.exists():
        artifact_path.write_text("# Feature Decomposition\n", encoding="utf-8")

    prompt = build_constructive_prompt(
        manifest["edge"],
        manifest,
        artifact_path=_FEATURE_DECOMP_ARTIFACT,
    )
    archive.capture_text("feature_decomp_live_prompt.txt", prompt)
    archive.update_summary(prompt_words=_word_count(prompt))
    response = call_agent(prompt, str(workspace), agent=agent, timeout=240)
    archive.capture_text("feature_decomp_live_raw_response.txt", response)

    assessments = _judge_feature_decomp(artifact_path, manifest["requirements"])
    archive.copy_file(artifact_path, dest_name="feature_decomp.md")

    result_path = Path(manifest["result_path"])
    _write_result_file(
        result_path,
        edge=manifest["edge"],
        actor="live_feature_decomp_judge",
        assessments=assessments,
    )
    archive.capture_json("feature_decomp_live_result.json", json.loads(result_path.read_text(encoding="utf-8")))

    assess = run_genesis(
        workspace,
        "assess-result",
        "--result",
        str(result_path),
        archive=archive,
        label=f"genesis assess-result {manifest['edge']}",
    )
    assert assess.returncode == 0, assess.stderr


def _design_assessments(artifact: Path) -> list[dict]:
    return _judge_headers_and_requirements(
        artifact,
        evaluator="design_complete",
        headers=DESIGN_SECTIONS,
        required_terms=("add", "multiply", "unit test", "integration"),
        evidence_label="design artifact defines components, interfaces, decomposition, and sequencing for the calculator project.",
    )


def _module_decomp_assessments(artifact: Path) -> list[dict]:
    return _judge_headers_and_requirements(
        artifact,
        evaluator="module_schedule",
        headers=MODULE_DECOMP_SECTIONS,
        required_terms=("calculator", "tests", "dependency"),
        evidence_label="module decomposition artifact defines modules, dependencies, and build order.",
    )


_CONSTRUCTIVE_ARTIFACTS = {
    "feature_decomp→design": (_DESIGN_ARTIFACT, "design.md", _design_assessments),
    "design→module_decomp": (_MODULE_DECOMP_ARTIFACT, "module_decomp.md", _module_decomp_assessments),
    "module_decomp→code": (_CODE_ARTIFACT, "calculator.py", _judge_code_artifact),
    "module_decomp→unit_tests": (_UNIT_TESTS_ARTIFACT, "test_calculator.py", _judge_unit_tests_artifact),
    INTEGRATION_EDGE: (_INTEGRATION_ARTIFACT, "test_integration.py", _judge_integration_artifact),
}


def _qualify_live_edge(workspace: Path, manifest: dict, *, archive, agent: str) -> None:
    edge = manifest["edge"]

    if edge == "requirements→feature_decomp":
        _qualify_feature_decomp_live(workspace, manifest, archive=archive, agent=agent)
        return

    contract = get_edge_transform_contract(edge)
    artifact_spec = _CONSTRUCTIVE_ARTIFACTS.get(edge)
    if contract is None or artifact_spec is None:
        _dispatch_live_fp(workspace, manifest, archive=archive, agent=agent, stem=edge.replace("→", "_"))
        return

    artifact_path, archive_name, judge = artifact_spec
    artifact = workspace / artifact_path
    prompt = build_constructive_prompt(edge, manifest, artifact_path=artifact_path)
    artifact.parent.mkdir(parents=True, exist_ok=True)
    response = call_agent(prompt, str(workspace), agent=agent, timeout=240)
    safe_stem = edge.replace("→", "_").replace("[", "").replace("]", "").replace(", ", "_").replace(" ", "")
    archive.capture_text(f"{safe_stem}_prompt.txt", prompt)
    archive.capture_text(f"{safe_stem}_raw_response.txt", response)
    archive.capture_json(f"{safe_stem}_manifest.json", manifest)
    archive.copy_file(artifact, dest_name=archive_name)
    archive.update_summary(prompt_words=_word_count(prompt))

    if edge == INTEGRATION_EDGE:
        _write_passing_sandbox_report(workspace)

    result_path = Path(manifest["result_path"])
    assessed_payload = judge(artifact)
    _write_result_file(
        result_path,
        edge=edge,
        actor=f"live_{safe_stem}_judge",
        assessments=assessed_payload,
    )
    archive.capture_json(f"{safe_stem}_result.json", json.loads(result_path.read_text(encoding="utf-8")))

    assess = run_genesis(
        workspace,
        "assess-result",
        "--result",
        str(result_path),
        archive=archive,
        label=f"genesis assess-result {edge}",
    )
    assert assess.returncode == 0, assess.stderr


@pytest.mark.usecase_id("workflow_fp_dispatch")
@pytest.mark.skipif(
    not _live_enabled(),
    reason="set CODEX_LIVE_FP=1 and ensure the selected agent CLI is available",
)
def test_workflow_advances_from_fh_gate_to_live_fp_qualification(run_archive) -> None:
    workspace = run_archive.workspace
    agent = _live_agent()
    install_real_sandbox(workspace, archive=run_archive)
    _seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="live", edge="requirements→feature_decomp", agent=agent)

    approve = run_genesis(
        workspace,
        "emit-event",
        "--type",
        "approved",
        "--data",
        json.dumps(
            {
                "kind": "fh_intent",
                "edge": "intent→requirements",
                "actor": "human",
            }
        ),
        archive=run_archive,
        label="emit approved fh_intent",
    )
    assert approve.returncode == 0, approve.stderr

    iterate = run_genesis(workspace, "iterate", archive=run_archive, label="genesis iterate live")
    assert iterate.returncode == 0, iterate.stderr
    iterate_data = json.loads(iterate.stdout)
    run_archive.capture_json("iterate_live_fp.json", iterate_data)

    assert iterate_data["blocking_reason"] == "fp_dispatch"
    assert iterate_data["edge"] == "requirements→feature_decomp"

    manifest_path = Path(iterate_data["fp_manifest_path"])
    assert manifest_path.is_file()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_archive.capture_json("fp_live_manifest.json", manifest)
    run_archive.update_summary(
        lane="live",
        edge=manifest["edge"],
        manifest_id=manifest["manifest_id"],
        transport_agent=agent,
        result_path=manifest["result_path"],
    )

    _qualify_feature_decomp_live(workspace, manifest, archive=run_archive, agent=agent)

    gaps = run_genesis(workspace, "gaps", archive=run_archive, label="genesis gaps after live fp")
    assert gaps.returncode == 0, gaps.stderr
    gaps_data = json.loads(gaps.stdout)
    run_archive.capture_json("gaps_after_live_fp.json", gaps_data)
    edge_map = {entry["edge"]: entry for entry in gaps_data["gaps"]}
    run_archive.update_summary(total_delta=gaps_data["total_delta"], converged=gaps_data["converged"])

    assert "feature_decomp_complete" not in edge_map["requirements→feature_decomp"]["failing"]


@pytest.mark.usecase_id("gsdlc_steel_thread")
@pytest.mark.skipif(
    not _live_enabled(),
    reason="set CODEX_LIVE_FP=1 and ensure the selected agent CLI is available",
)
def test_light_steel_thread_live_qualification_through_integration_tests(run_archive) -> None:
    workspace = run_archive.workspace
    agent = _live_agent()
    install_real_sandbox(workspace, slug="steel_thread", archive=run_archive)
    _seed_minimal_project_spec(workspace, archive=run_archive)
    run_archive.note("scenario", lane="live", through_edge=INTEGRATION_EDGE, agent=agent)

    _emit_event(
        workspace,
        "intent_raised",
        {
            "feature": "STEEL-001",
            "summary": "simple intent to code and tests",
        },
        archive=run_archive,
        label="emit intent_raised",
    )

    max_steps = 20
    for _ in range(max_steps):
        gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps")
        edge_map = {entry["edge"]: entry for entry in gaps["gaps"]}
        if edge_map[INTEGRATION_EDGE]["delta"] == 0:
            break

        iterate = _run_json(workspace, "iterate", archive=run_archive, label="genesis iterate")
        edge = iterate["edge"]
        blocking_reason = iterate.get("blocking_reason")

        if edge == INTEGRATION_EDGE:
            _write_passing_sandbox_report(workspace)

        if blocking_reason == "fh_gate":
            _emit_event(
                workspace,
                "approved",
                {
                    "kind": "fh_intent" if edge == "intent→requirements" else "fh_review",
                    "edge": edge,
                    "actor": "steel_thread_live_tester",
                },
                archive=run_archive,
                label=f"emit approved {edge}",
            )
            continue

        if blocking_reason == "fp_dispatch":
            manifest = json.loads(Path(iterate["fp_manifest_path"]).read_text(encoding="utf-8"))
            safe_stem = edge.replace("→", "_").replace("[", "").replace("]", "").replace(", ", "_").replace(" ", "")
            run_archive.capture_json(f"{safe_stem}_manifest.json", manifest)
            _qualify_live_edge(workspace, manifest, archive=run_archive, agent=agent)
            continue

        raise AssertionError(f"unexpected iterate outcome: {iterate}")
    else:
        raise AssertionError(f"live steel thread did not reach {INTEGRATION_EDGE} within {max_steps} steps")

    final_gaps = _run_json(workspace, "gaps", archive=run_archive, label="genesis gaps final")
    run_archive.capture_json("gaps_final_live.json", final_gaps)
    final_edge_map = {entry["edge"]: entry for entry in final_gaps["gaps"]}
    run_archive.update_summary(
        lane="live",
        converged=final_edge_map[INTEGRATION_EDGE]["delta"] == 0,
        total_delta=final_gaps["total_delta"],
        completed_edge=INTEGRATION_EDGE,
        transport_agent=agent,
    )

    assert final_edge_map["intent→requirements"]["delta"] == 0
    assert final_edge_map["requirements→feature_decomp"]["delta"] == 0
    assert final_edge_map["feature_decomp→design"]["delta"] == 0
    assert final_edge_map["design→module_decomp"]["delta"] == 0
    assert final_edge_map["module_decomp→code"]["delta"] == 0
    assert final_edge_map["module_decomp→unit_tests"]["delta"] == 0
    assert final_edge_map[INTEGRATION_EDGE]["delta"] == 0

    for edge in DOWNSTREAM_RELEASE_EDGES:
        assert final_edge_map[edge]["delta"] > 0
