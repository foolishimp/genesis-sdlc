# Validates: REQ-F-TEST-001
# Validates: REQ-F-TEST-005
# Validates: REQ-F-MVP-002
# Validates: REQ-F-ASSURE-001
"""Minimal project fixture and artifact materializers for workflow qualification."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from genesis_sdlc.evidence.coverage import (
    assess_code_artifact,
    assess_design_artifact,
    assess_feature_decomp_artifact,
    assess_integration_artifact,
    assess_module_decomp_artifact,
    assess_unit_tests_artifact,
)
from genesis_sdlc.evidence.docs import assess_bootloader_artifact, assess_user_guide_artifact, synthesize_user_guide
from genesis_sdlc.evidence.uat import write_sandbox_report
from genesis_sdlc.release.bootloader import synthesize_bootloader
from genesis_sdlc.runtime.prompt_view import (
    render_effective_prompt,
    render_effective_prompt_from_manifest,
)
from genesis_sdlc.release.install import VERSION
from genesis_sdlc.release.wrapper import load_project_requirements
from genesis_sdlc.workflow.transforms import build_constructive_prompt, edge_override_filename


INTEGRATION_EDGE = "[code, unit_tests]→integration_tests"
USER_GUIDE_EDGE = "[design, integration_tests]→user_guide"
BOOTLOADER_EDGE = "[requirements, design, integration_tests]→bootloader"
UAT_EDGE = "[requirements, integration_tests]→uat_tests"
DOWNSTREAM_RELEASE_EDGES = {USER_GUIDE_EDGE, BOOTLOADER_EDGE, UAT_EDGE}

FEATURE_DECOMP_ARTIFACT = Path("output/feature_decomp.md")
DESIGN_ARTIFACT = Path("output/design.md")
MODULE_DECOMP_ARTIFACT = Path("output/module_decomp.md")
CODE_ARTIFACT = Path("output/src/calculator.py")
UNIT_TESTS_ARTIFACT = Path("output/tests/test_calculator.py")
INTEGRATION_ARTIFACT = Path("output/tests/test_integration.py")
USER_GUIDE_ARTIFACT = Path(".gsdlc/release/USER_GUIDE.md")
BOOTLOADER_ARTIFACT = Path(".gsdlc/release/SDLC_BOOTLOADER.md")


MINIMAL_INTENT = """# Intent

## Summary

This sandbox project exists to qualify the real genesis_sdlc workflow against a
small bounded software problem rather than against the genesis_sdlc framework
itself.

## Goal

Carry a simple project from intent through requirements, feature decomposition,
design, module decomposition, code, unit tests, integration tests, user guide,
bootloader, and UAT acceptance.

## Project Shape

The project is a tiny Python calculator capability with two operations:

- add(a, b)
- multiply(a, b)

The implementation should stay intentionally small and easy to reason about in a
single live or fake qualification turn.
"""


MINIMAL_REQUIREMENTS = """# Core Requirements

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


MINIMAL_DESIGN = """# Project Design

This project is a tiny calculator qualification surface.

## Components

- calculator module
- unit test module
- integration test module

## Guidance

Prefer small files, direct imports, and deterministic test evidence.
"""


MINIMAL_FP_INTENT = """# F_P Customization Intent

## Goal

Keep each constructive turn tightly bounded to the minimal calculator project.

## Requirement Mapping

- REQ-PROJ-001
- REQ-PROJ-002
- REQ-PROJ-003
- REQ-PROJ-004

## Design Mapping

- specification/design/README.md

## Boundaries

- Do not expand the project beyond the calculator scope.
- Do not rewrite unrelated workspace files.
"""


def seed_minimal_project_spec(workspace: Path, *, archive=None) -> None:
    spec_root = workspace / "specification"
    requirements_root = spec_root / "requirements"
    design_root = spec_root / "design"
    fp_root = design_root / "fp"
    overrides_root = fp_root / "edge-overrides"

    if requirements_root.exists():
        shutil.rmtree(requirements_root)
    if design_root.exists():
        shutil.rmtree(design_root)
    requirements_root.mkdir(parents=True, exist_ok=True)
    overrides_root.mkdir(parents=True, exist_ok=True)

    (spec_root / "INTENT.md").write_text(MINIMAL_INTENT, encoding="utf-8")
    (requirements_root / "01-project-core.md").write_text(MINIMAL_REQUIREMENTS, encoding="utf-8")
    (requirements_root / "README.md").write_text(
        "# Project Requirements\n\nThis sandbox uses a minimal project requirement surface for qualification.\n",
        encoding="utf-8",
    )
    (design_root / "README.md").write_text(MINIMAL_DESIGN, encoding="utf-8")
    (fp_root / "README.md").write_text(
        "# F_P Customization\n\nThis sandbox uses per-edge overrides to keep the workflow bounded to the calculator project.\n",
        encoding="utf-8",
    )
    (fp_root / "INTENT.md").write_text(MINIMAL_FP_INTENT, encoding="utf-8")
    (overrides_root / "README.md").write_text(
        "# Edge Overrides\n\nOnly edge override files in this folder are loaded by the installed prompt helper.\n",
        encoding="utf-8",
    )
    _write_fp_overrides(overrides_root)

    if archive is not None:
        archive.capture_text("seeded_INTENT.md", MINIMAL_INTENT)
        archive.capture_text("seeded_requirements_01-project-core.md", MINIMAL_REQUIREMENTS)
        archive.capture_text("seeded_design_README.md", MINIMAL_DESIGN)
        archive.capture_text("seeded_fp_INTENT.md", MINIMAL_FP_INTENT)
        archive.update_summary(
            seeded_project_spec=True,
            seeded_requirement_keys=["REQ-PROJ-001", "REQ-PROJ-002", "REQ-PROJ-003", "REQ-PROJ-004"],
        )


def write_result_file(result_path: Path, *, edge: str, actor: str, assessments: list[dict]) -> None:
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


def workflow_version(workspace: Path) -> str:
    data = json.loads((workspace / ".gsdlc" / "release" / "active-workflow.json").read_text(encoding="utf-8"))
    return str(data["version"])


def current_requirement_keys(workspace: Path) -> list[str]:
    return load_project_requirements(workspace)


def edge_artifact(edge: str) -> Path | None:
    return {
        "requirements→feature_decomp": FEATURE_DECOMP_ARTIFACT,
        "feature_decomp→design": DESIGN_ARTIFACT,
        "design→module_decomp": MODULE_DECOMP_ARTIFACT,
        "module_decomp→code": CODE_ARTIFACT,
        "module_decomp→unit_tests": UNIT_TESTS_ARTIFACT,
        INTEGRATION_EDGE: INTEGRATION_ARTIFACT,
        USER_GUIDE_EDGE: USER_GUIDE_ARTIFACT,
        BOOTLOADER_EDGE: BOOTLOADER_ARTIFACT,
    }.get(edge)


def build_fake_artifact(edge: str, workspace: Path, manifest: dict | None = None) -> Path:
    relative = edge_artifact(edge)
    if relative is None:
        raise KeyError(f"no fake artifact declared for edge: {edge}")

    artifact = workspace / relative
    artifact.parent.mkdir(parents=True, exist_ok=True)
    requirements = list(manifest["requirements"]) if manifest is not None else current_requirement_keys(workspace)

    if edge == "requirements→feature_decomp":
        _write(artifact, _feature_decomp_text(requirements))
    elif edge == "feature_decomp→design":
        _write(artifact, _design_text())
    elif edge == "design→module_decomp":
        _write(artifact, _module_decomp_text())
    elif edge == "module_decomp→code":
        _write(artifact, _code_text())
    elif edge == "module_decomp→unit_tests":
        _write(artifact, _unit_tests_text())
    elif edge == INTEGRATION_EDGE:
        _write(artifact, _integration_test_text())
        write_sandbox_report(
            workspace / ".ai-workspace" / "uat" / "sandbox_report.json",
            scenario="full_cycle",
            sandbox_path=str(workspace),
        )
    elif edge == USER_GUIDE_EDGE:
        synthesize_user_guide(artifact, version=workflow_version(workspace), requirements=requirements)
    elif edge == BOOTLOADER_EDGE:
        synthesize_bootloader(
            requirements=requirements,
            version=workflow_version(workspace),
            output_path=artifact,
            workspace_root=workspace,
        )
    return artifact


def edge_assessments(edge: str, workspace: Path, manifest: dict | None = None) -> list[dict]:
    artifact = workspace / edge_artifact(edge) if edge_artifact(edge) is not None else None
    if artifact is None:
        raise KeyError(f"no assessment declared for edge: {edge}")
    requirements = list(manifest["requirements"]) if manifest is not None else current_requirement_keys(workspace)
    if edge == "requirements→feature_decomp":
        return assess_feature_decomp_artifact(artifact, requirements)
    if edge == "feature_decomp→design":
        return assess_design_artifact(artifact)
    if edge == "design→module_decomp":
        return assess_module_decomp_artifact(artifact)
    if edge == "module_decomp→code":
        return assess_code_artifact(artifact)
    if edge == "module_decomp→unit_tests":
        return assess_unit_tests_artifact(artifact)
    if edge == INTEGRATION_EDGE:
        return assess_integration_artifact(artifact)
    if edge == USER_GUIDE_EDGE:
        return assess_user_guide_artifact(artifact, requirements)
    if edge == BOOTLOADER_EDGE:
        return assess_bootloader_artifact(artifact)
    raise KeyError(f"no assessment declared for edge: {edge}")


def default_archive_name(edge: str) -> str:
    relative = edge_artifact(edge)
    return relative.name if relative is not None else "artifact.json"


def constructive_prompt(edge: str, manifest: dict, *, workspace: Path, artifact_path: Path) -> str:
    return render_effective_prompt_from_manifest(
        manifest,
        workspace_root=workspace,
        artifact_override=artifact_path,
    )


def effective_prompt_from_manifest(manifest_path: Path, *, workspace: Path) -> str:
    return render_effective_prompt(manifest_path, workspace)


def fd_repair_prompt(edge: str, workspace: Path) -> str:
    artifact = edge_artifact(edge)
    if artifact is None:
        raise KeyError(f"no artifact target declared for edge: {edge}")
    requirements = current_requirement_keys(workspace)
    return build_constructive_prompt(
        edge,
        {
            "edge": edge,
            "requirements": requirements,
            "prompt": (
                "Repair the active artifact so deterministic checks on version, "
                "requirement coverage, and workspace references pass against the current project surface."
            ),
        },
        artifact_path=artifact,
        workspace_root=workspace,
    )


def _write_fp_overrides(overrides_root: Path) -> None:
    design_ref = "specification/design/README.md"
    edge_refs = {
        "requirements→feature_decomp": ["REQ-PROJ-001", "REQ-PROJ-002", "REQ-PROJ-003", "REQ-PROJ-004"],
        "feature_decomp→design": ["REQ-PROJ-001", "REQ-PROJ-002", "REQ-PROJ-004"],
        "design→module_decomp": ["REQ-PROJ-001", "REQ-PROJ-002", "REQ-PROJ-003", "REQ-PROJ-004"],
        "module_decomp→code": ["REQ-PROJ-001", "REQ-PROJ-002"],
        "module_decomp→unit_tests": ["REQ-PROJ-003"],
        INTEGRATION_EDGE: ["REQ-PROJ-004"],
        USER_GUIDE_EDGE: ["REQ-PROJ-001", "REQ-PROJ-002", "REQ-PROJ-003", "REQ-PROJ-004"],
        BOOTLOADER_EDGE: ["REQ-PROJ-001", "REQ-PROJ-002", "REQ-PROJ-003", "REQ-PROJ-004"],
    }
    for edge, artifact in {
        "requirements→feature_decomp": FEATURE_DECOMP_ARTIFACT,
        "feature_decomp→design": DESIGN_ARTIFACT,
        "design→module_decomp": MODULE_DECOMP_ARTIFACT,
        "module_decomp→code": CODE_ARTIFACT,
        "module_decomp→unit_tests": UNIT_TESTS_ARTIFACT,
        INTEGRATION_EDGE: INTEGRATION_ARTIFACT,
        USER_GUIDE_EDGE: USER_GUIDE_ARTIFACT,
        BOOTLOADER_EDGE: BOOTLOADER_ARTIFACT,
    }.items():
        payload = {
            "edge": edge,
            "customization_intent": "Keep this constructive turn bounded to the minimal calculator qualification project.",
            "requirement_refs": edge_refs[edge],
            "design_refs": [design_ref],
            "guidance_append": "Prefer the seeded calculator scope, small files, and direct requirement traceability.",
            "suggested_output": artifact.as_posix(),
        }
        (overrides_root / edge_override_filename(edge)).write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _feature_decomp_text(requirements: list[str]) -> str:
    coverage = "\n".join(f"- {requirement}: feature mapped" for requirement in requirements)
    return f"""# Feature Decomposition

## Features

- Calculator arithmetic
- Unit-test surface
- Integration scenario

## Dependency Order

1. Feature decomposition
2. Design
3. Module decomposition
4. Code and unit tests
5. Integration tests

## Coverage Map

{coverage}

This decomposition preserves add, multiply, and integration behavior.
"""


def _design_text() -> str:
    return """# Design

## Components

- calculator module
- unit-test module
- integration-test module

## Interfaces

- `add(a, b)`
- `multiply(a, b)`

## Decomposition

The calculator module stays intentionally small. Unit test and integration test
surfaces validate the add and multiply operations.

## Dependency Chain

Design feeds module decomposition, then implementation, then unit test and
integration evidence.

## Sequencing

Complete the calculator implementation, then unit tests, then the integration
scenario.
"""


def _module_decomp_text() -> str:
    return """# Module Decomposition

## Modules

- `calculator`
- `tests.test_calculator`
- `tests.test_integration`

## Dependencies

- tests depend on calculator
- integration tests depend on calculator and pytest

## Build Order

1. calculator
2. unit tests
3. integration tests

This module decomposition keeps the calculator and tests explicit and
dependency-aware.
"""


def _code_text() -> str:
    return '''# Implements: REQ-PROJ-001
# Implements: REQ-PROJ-002
"""Simple calculator module for workflow qualification."""


def add(a: int, b: int) -> int:
    return a + b


def multiply(a: int, b: int) -> int:
    return a * b
'''


def _unit_tests_text() -> str:
    return '''# Validates: REQ-PROJ-001
# Validates: REQ-PROJ-002
# Validates: REQ-PROJ-003
from calculator import add, multiply


def test_add() -> None:
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_multiply() -> None:
    assert multiply(3, 4) == 12
    assert multiply(-2, 5) == -10
'''


def _integration_test_text() -> str:
    return '''# Validates: REQ-PROJ-004
from calculator import add, multiply


def test_calculator_flow() -> None:
    total = add(2, 3)
    product = multiply(total, 4)
    assert total == 5
    assert product == 20
'''
