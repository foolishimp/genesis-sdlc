# Implements: REQ-F-CMD-001
"""Default bounded transform contracts for workflow F_P edges."""

from __future__ import annotations

import json
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
    customization_intent: str = ""
    requirement_refs: tuple[str, ...] = ()
    design_refs: tuple[str, ...] = ()


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
        suggested_output=".gsdlc/release/USER_GUIDE.md",
        guidance="Compile an operator guide from design and integrated evidence, covering install, first session, the operating loop, and recovery.",
        required_sections=USER_GUIDE_SECTIONS,
    ),
    "[requirements, design, integration_tests]→bootloader": EdgeTransformContract(
        edge="[requirements, design, integration_tests]→bootloader",
        target_asset="bootloader",
        artifact_kind="compiled domain bootloader",
        authority_contexts=("requirements_surface", "bootloader_synthesis_surface"),
        suggested_output=".gsdlc/release/SDLC_BOOTLOADER.md",
        guidance=(
            "Compile the domain bootloader from the active requirement surface. "
            "Prefer the installed `genesis_sdlc.release.bootloader.synthesize_bootloader()` "
            "helper or produce an equivalent exact compilation."
        ),
        required_sections=BOOTLOADER_SECTIONS,
    ),
}


def edge_override_filename(edge: str) -> str:
    safe = (
        edge.replace("[", "")
        .replace("]", "")
        .replace(", ", "__and__")
        .replace("→", "__to__")
        .replace(" ", "")
    )
    return f"{safe}.json"


def _infer_workspace_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    candidates = [current, *current.parents]
    for parent in candidates:
        if (parent / ".gsdlc" / "release" / "active-workflow.json").exists():
            return parent
        if (parent / "specification").exists() and (parent / ".gsdlc").exists():
            return parent
    return None


def _fp_override_root(workspace_root: Path | None) -> Path | None:
    if workspace_root is None:
        return None
    return workspace_root / "specification" / "design" / "fp" / "edge-overrides"


def load_project_edge_override(edge: str, workspace_root: Path | None = None) -> dict[str, object] | None:
    root = _fp_override_root(workspace_root)
    if root is None:
        return None
    path = root / edge_override_filename(edge)
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"edge override must be a JSON object: {path}")
    return payload


def resolve_edge_transform_contract(edge: str, workspace_root: Path | None = None) -> EdgeTransformContract | None:
    base = EDGE_TRANSFORM_CONTRACTS.get(edge)
    if base is None:
        return None

    override = load_project_edge_override(edge, workspace_root)
    if override is None:
        return base

    payload = asdict(base)
    payload["authority_contexts"] = tuple(payload["authority_contexts"])
    payload["required_sections"] = tuple(payload["required_sections"])
    payload["requirement_refs"] = tuple(payload["requirement_refs"])
    payload["design_refs"] = tuple(payload["design_refs"])

    if "authority_contexts" in override:
        payload["authority_contexts"] = tuple(str(item) for item in override["authority_contexts"])
    if "suggested_output" in override:
        payload["suggested_output"] = str(override["suggested_output"])
    if "required_sections" in override:
        payload["required_sections"] = tuple(str(item) for item in override["required_sections"])
    if "customization_intent" in override:
        payload["customization_intent"] = str(override["customization_intent"])
    if "requirement_refs" in override:
        payload["requirement_refs"] = tuple(str(item) for item in override["requirement_refs"])
    if "design_refs" in override:
        payload["design_refs"] = tuple(str(item) for item in override["design_refs"])
    if "guidance" in override:
        payload["guidance"] = str(override["guidance"])
    guidance_append = override.get("guidance_append")
    if guidance_append:
        payload["guidance"] = f"{payload['guidance']} {str(guidance_append)}".strip()

    return EdgeTransformContract(**payload)


def get_edge_transform_contract(edge: str) -> EdgeTransformContract | None:
    return resolve_edge_transform_contract(edge)


def transform_contract_manifest(edge: str, workspace_root: Path | None = None) -> dict[str, object] | None:
    contract = resolve_edge_transform_contract(edge, workspace_root)
    return asdict(contract) if contract is not None else None


def build_constructive_prompt(
    edge: str,
    manifest: dict[str, object],
    *,
    artifact_path: Path | None = None,
    workspace_root: Path | None = None,
    extra_instructions: str | None = None,
) -> str:
    contract = resolve_edge_transform_contract(edge, workspace_root or _infer_workspace_root())
    if contract is None:
        raise KeyError(f"no transform contract declared for edge: {edge}")
    resolved_artifact = artifact_path or Path(contract.suggested_output)

    lines = [
        LIVE_MODE_PREAMBLE.rstrip(),
        CONSTRUCTIVE_TURN_RULES.format(artifact_path=resolved_artifact).rstrip(),
        f"Target asset: {contract.target_asset}",
        f"Artifact kind: {contract.artifact_kind}",
        f"Authority contexts: {', '.join(contract.authority_contexts)}",
        f"Suggested output: {contract.suggested_output}",
        contract.guidance,
    ]
    if contract.customization_intent:
        lines.append(f"Project customization intent: {contract.customization_intent}")
    if contract.requirement_refs:
        lines.append("Project requirement refs:")
        lines.extend(f"- {ref}" for ref in contract.requirement_refs)
    if contract.design_refs:
        lines.append("Project design refs:")
        lines.extend(f"- {ref}" for ref in contract.design_refs)
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
    "edge_override_filename",
    "get_edge_transform_contract",
    "load_project_edge_override",
    "resolve_edge_transform_contract",
    "transform_contract_manifest",
]
