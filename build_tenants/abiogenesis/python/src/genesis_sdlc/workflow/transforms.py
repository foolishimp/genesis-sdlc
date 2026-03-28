# Implements: REQ-F-CMD-001
"""Default bounded transform contracts for workflow F_P edges."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path


LIVE_MODE_PREAMBLE = "[LIVE QUALIFICATION MODE]\n"
CONSTRUCTIVE_TURN_RULES = (
    "This is a bounded constructive F_P turn.\n"
    "Write the target artifact to: {artifact_path}\n"
    "Do not write the assessment result JSON yourself.\n"
    "Do not modify any other workspace files.\n"
)
ASSESSMENT_TURN_RULES = (
    "This is a bounded F_P qualification turn.\n"
    "Use the supplied manifest context as the authority surface for this turn.\n"
    "Write the required assessment JSON to: {result_path}\n"
    "Do not modify any other workspace files unless the manifest provides an explicit output path for them.\n"
    "If the manifest context is sufficient, write a pass assessment with concise evidence and stop.\n"
    "If the manifest context is insufficient, write a fail assessment with concise evidence and stop.\n"
)

FEATURE_DECOMP_SECTIONS = (
    "# Feature Decomposition",
    "## Features",
    "## Dependency Order",
    "## Coverage Map",
)
DESIGN_SECTIONS = (
    "# Design",
    "## Components",
    "## Interfaces",
    "## Decomposition",
    "## Dependency Chain",
    "## Sequencing",
)
MODULE_DECOMP_SECTIONS = (
    "# Module Decomposition",
    "## Modules",
    "## Dependencies",
    "## Build Order",
)
USER_GUIDE_SECTIONS = (
    "## Installation",
    "## First Session",
    "## Operating Loop",
    "## Recovery",
)
BOOTLOADER_SECTIONS = (
    "## Authority",
    "## Axioms",
    "## Active Docs",
    "## Commands",
)


@dataclass(frozen=True)
class EdgeTransformContract:
    edge: str
    target_asset: str
    artifact_kind: str
    authority_contexts: tuple[str, ...]
    suggested_output: str
    guidance: str
    required_sections: tuple[str, ...] = ()


EDGE_TRANSFORM_CONTRACTS: dict[str, EdgeTransformContract] = {
    "requirements→feature_decomp": EdgeTransformContract(
        edge="requirements→feature_decomp",
        target_asset="feature_decomp",
        artifact_kind="feature decomposition",
        authority_contexts=("requirements_surface",),
        suggested_output="output/feature_decomp.md",
        guidance=(
            "Treat this as the requirements→feature_decomp transform. "
            "Cover the active requirement surface, preserve dependency order, "
            "and keep the decomposition proportional to the project scope."
        ),
        required_sections=FEATURE_DECOMP_SECTIONS,
    ),
    "feature_decomp→design": EdgeTransformContract(
        edge="feature_decomp→design",
        target_asset="design",
        artifact_kind="design document",
        authority_contexts=("requirements_surface", "python_design_surface"),
        suggested_output="output/design.md",
        guidance=(
            "Define the design needed to realize the approved feature set. "
            "Make interfaces, decomposition, dependencies, and sequencing explicit."
        ),
        required_sections=DESIGN_SECTIONS,
    ),
    "design→module_decomp": EdgeTransformContract(
        edge="design→module_decomp",
        target_asset="module_decomp",
        artifact_kind="module decomposition",
        authority_contexts=("requirements_surface", "python_design_surface"),
        suggested_output="output/module_decomp.md",
        guidance=(
            "Turn the design into a buildable module schedule with clean boundaries, "
            "explicit dependencies, and a clear build order."
        ),
        required_sections=MODULE_DECOMP_SECTIONS,
    ),
    "module_decomp→code": EdgeTransformContract(
        edge="module_decomp→code",
        target_asset="code",
        artifact_kind="source implementation",
        authority_contexts=("requirements_surface", "python_design_surface"),
        suggested_output="output/src/main.py",
        guidance="Materialize the approved module surface as small, importable source code.",
    ),
    "module_decomp→unit_tests": EdgeTransformContract(
        edge="module_decomp→unit_tests",
        target_asset="unit_tests",
        artifact_kind="unit-test surface",
        authority_contexts=("requirements_surface", "python_design_surface"),
        suggested_output="output/tests/test_unit.py",
        guidance="Materialize runnable unit tests for the declared module interfaces and invariants.",
    ),
    "[code, unit_tests]→integration_tests": EdgeTransformContract(
        edge="[code, unit_tests]→integration_tests",
        target_asset="integration_tests",
        artifact_kind="integration and sandbox evidence",
        authority_contexts=("requirements_surface", "python_design_surface"),
        suggested_output="output/tests/test_integration.py",
        guidance="Produce integrated runnable evidence that exercises the code and tests together in one operator-facing flow.",
    ),
    "[design, integration_tests]→user_guide": EdgeTransformContract(
        edge="[design, integration_tests]→user_guide",
        target_asset="user_guide",
        artifact_kind="operator guide",
        authority_contexts=("requirements_surface", "python_design_surface", "standards_surface"),
        suggested_output="build_tenants/abiogenesis/python/release/USER_GUIDE.md",
        guidance="Compile an operator guide from design and integrated evidence, covering install, first session, the operating loop, and recovery.",
        required_sections=USER_GUIDE_SECTIONS,
    ),
    "[requirements, design, integration_tests]→bootloader": EdgeTransformContract(
        edge="[requirements, design, integration_tests]→bootloader",
        target_asset="bootloader",
        artifact_kind="compiled domain bootloader",
        authority_contexts=("requirements_surface", "bootloader_synthesis_surface"),
        suggested_output="build_tenants/abiogenesis/python/release/SDLC_BOOTLOADER.md",
        guidance=(
            "Compile the domain bootloader from the active requirement surface. "
            "Prefer the installed `genesis_sdlc.release.bootloader.synthesize_bootloader()` "
            "helper or produce an equivalent exact compilation."
        ),
        required_sections=BOOTLOADER_SECTIONS,
    ),
}


def get_edge_transform_contract(edge: str) -> EdgeTransformContract | None:
    return EDGE_TRANSFORM_CONTRACTS.get(edge)


def transform_contract_manifest(edge: str) -> dict[str, object] | None:
    contract = get_edge_transform_contract(edge)
    return asdict(contract) if contract is not None else None


def build_constructive_prompt(
    edge: str,
    manifest: dict[str, object],
    *,
    artifact_path: Path,
    extra_instructions: str | None = None,
) -> str:
    contract = get_edge_transform_contract(edge)
    if contract is None:
        raise KeyError(f"no transform contract declared for edge: {edge}")

    lines = [
        LIVE_MODE_PREAMBLE.rstrip(),
        CONSTRUCTIVE_TURN_RULES.format(artifact_path=artifact_path).rstrip(),
        f"Target asset: {contract.target_asset}",
        f"Artifact kind: {contract.artifact_kind}",
        f"Authority contexts: {', '.join(contract.authority_contexts)}",
        f"Suggested output: {contract.suggested_output}",
        contract.guidance,
    ]
    if contract.required_sections:
        lines.append("The artifact must contain these exact sections:")
        lines.extend(f"- {section}" for section in contract.required_sections)
    if extra_instructions:
        lines.append(extra_instructions)
    lines.extend(("", str(manifest["prompt"])))
    return "\n".join(lines)


def build_assessment_prompt(manifest: dict[str, object]) -> str:
    return (
        LIVE_MODE_PREAMBLE
        + ASSESSMENT_TURN_RULES.format(result_path=manifest["result_path"])
        + "\n"
        + str(manifest["prompt"])
    )


__all__ = [
    "ASSESSMENT_TURN_RULES",
    "BOOTLOADER_SECTIONS",
    "CONSTRUCTIVE_TURN_RULES",
    "DESIGN_SECTIONS",
    "EDGE_TRANSFORM_CONTRACTS",
    "EdgeTransformContract",
    "FEATURE_DECOMP_SECTIONS",
    "LIVE_MODE_PREAMBLE",
    "MODULE_DECOMP_SECTIONS",
    "USER_GUIDE_SECTIONS",
    "build_assessment_prompt",
    "build_constructive_prompt",
    "get_edge_transform_contract",
    "transform_contract_manifest",
]
