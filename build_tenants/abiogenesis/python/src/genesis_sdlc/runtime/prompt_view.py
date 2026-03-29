# Implements: REQ-F-CMD-004
# Implements: REQ-F-CTRL-006
# Implements: REQ-F-CTRL-008
"""Read-model prompt rendering from the resolved runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from genesis_sdlc.workflow.transforms import CONSTRUCTIVE_TURN_RULES, LIVE_MODE_PREAMBLE

from .resolve import load_resolved_runtime
from .state import infer_workspace_root


LOCATOR_FIRST_AXIOMS = (
    "Treat the listed locators as the authoritative context for this edge.",
    "You have workspace and tool access; read only the files you need from those locators.",
    "Keep the turn bounded to the declared output contract and evaluator targets.",
)


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, str) and str(item).strip()]


def _context_refs(manifest: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for entry in manifest.get("contexts", []):
        if not isinstance(entry, dict):
            continue
        name = str(entry.get("name", "")).strip()
        locator = str(entry.get("locator", "")).strip()
        digest = str(entry.get("digest", "")).strip()
        if not name or not locator:
            continue
        refs.append({"name": name, "locator": locator, "digest": digest})
    return refs


def _role_assignment(resolved_runtime: dict[str, Any], role_id: str) -> dict[str, Any]:
    assignments = resolved_runtime.get("role_assignments", {})
    if not isinstance(assignments, dict):
        return {}
    assignment = assignments.get(role_id)
    return assignment if isinstance(assignment, dict) else {}


def _supports_locator_first(assignment: dict[str, Any]) -> bool:
    capabilities = assignment.get("capabilities", {})
    if not isinstance(capabilities, dict):
        return False
    return bool(capabilities.get("interactive_cli")) and bool(capabilities.get("workspace_write"))


def _render_locator_first_prompt(
    manifest: dict[str, Any],
    *,
    profile: dict[str, Any],
    assignment: dict[str, Any],
    artifact_path: Path,
) -> str:
    lines = [
        LIVE_MODE_PREAMBLE.rstrip(),
        CONSTRUCTIVE_TURN_RULES.format(artifact_path=artifact_path).rstrip(),
        "Context delivery: locator-first",
        f"Edge: {manifest['edge']}",
        f"Source asset: {manifest.get('source_asset', 'unknown')}",
        f"Target asset: {profile['target_asset']}",
        f"Artifact kind: {profile['artifact_kind']}",
        f"Constructive role: {profile['role_id']}",
        f"Assigned worker: {assignment.get('worker_id', profile['worker_id'])}",
        f"Derived backend: {assignment.get('backend', profile['backend'])}",
        f"Suggested output: {artifact_path}",
    ]

    delta_summary = str(manifest.get("delta_summary", "")).strip()
    if delta_summary:
        lines.extend(("", "Gap summary:", delta_summary))

    failing = _string_list(manifest.get("failing_evaluators"))
    if failing:
        lines.append("Evaluators to satisfy:")
        lines.extend(f"- {evaluator}" for evaluator in failing)

    lines.append("Axioms:")
    lines.extend(f"- {axiom}" for axiom in LOCATOR_FIRST_AXIOMS)

    refs = _context_refs(manifest)
    if refs:
        lines.append("Authoritative context locators:")
        for ref in refs:
            digest = f" ({ref['digest']})" if ref["digest"] else ""
            lines.append(f"- {ref['name']}: {ref['locator']}{digest}")

    customization_intent = str(profile.get("customization_intent", "")).strip()
    if customization_intent:
        lines.append(f"Project customization intent: {customization_intent}")

    requirement_refs = _string_list(profile.get("requirement_refs"))
    if requirement_refs:
        lines.append("Project requirement refs:")
        lines.extend(f"- {ref}" for ref in requirement_refs)

    design_refs = _string_list(profile.get("design_refs"))
    if design_refs:
        lines.append("Project design refs:")
        lines.extend(f"- {ref}" for ref in design_refs)

    required_sections = _string_list(profile.get("required_sections"))
    if required_sections:
        lines.append("The artifact must contain these exact sections:")
        lines.extend(f"- {section}" for section in required_sections)

    guidance = str(profile.get("guidance", "")).strip()
    if guidance:
        lines.extend(("", guidance))

    return "\n".join(lines)


def _render_inline_snapshot_prompt(
    manifest: dict[str, Any],
    *,
    profile: dict[str, Any],
    artifact_path: Path,
) -> str:
    lines = [
        LIVE_MODE_PREAMBLE.rstrip(),
        CONSTRUCTIVE_TURN_RULES.format(artifact_path=artifact_path).rstrip(),
        "Context delivery: inline-snapshot",
        f"Target asset: {profile['target_asset']}",
        f"Artifact kind: {profile['artifact_kind']}",
        f"Constructive role: {profile['role_id']}",
        f"Assigned worker: {profile['worker_id']}",
        f"Derived backend: {profile['backend']}",
        f"Authority contexts: {', '.join(profile.get('authority_contexts', []))}",
        f"Suggested output: {artifact_path}",
        str(profile["guidance"]),
    ]
    customization_intent = str(profile.get("customization_intent", "")).strip()
    if customization_intent:
        lines.append(f"Project customization intent: {customization_intent}")
    requirement_refs = _string_list(profile.get("requirement_refs"))
    if requirement_refs:
        lines.append("Project requirement refs:")
        lines.extend(f"- {ref}" for ref in requirement_refs)
    design_refs = _string_list(profile.get("design_refs"))
    if design_refs:
        lines.append("Project design refs:")
        lines.extend(f"- {ref}" for ref in design_refs)
    required_sections = _string_list(profile.get("required_sections"))
    if required_sections:
        lines.append("The artifact must contain these exact sections:")
        lines.extend(f"- {section}" for section in required_sections)
    lines.extend(("", str(manifest["prompt"])))
    return "\n".join(lines)


def render_effective_prompt_from_manifest(
    manifest: dict[str, Any],
    *,
    workspace_root: Path,
    artifact_override: Path | None = None,
) -> str:
    resolved_runtime = load_resolved_runtime(workspace_root)
    edge = str(manifest["edge"])
    edge_payload = resolved_runtime.get("edges", {}).get(edge)
    if not isinstance(edge_payload, dict):
        raise KeyError(f"no resolved runtime profile for edge: {edge}")
    profile = edge_payload.get("profile", {})
    if not isinstance(profile, dict):
        raise ValueError(f"edge profile must be an object for edge: {edge}")
    assignment = _role_assignment(resolved_runtime, str(profile["role_id"]))

    artifact_path = artifact_override or Path(str(profile["suggested_output"]))

    if _supports_locator_first(assignment):
        return _render_locator_first_prompt(
            manifest,
            profile=profile,
            assignment=assignment,
            artifact_path=artifact_path,
        )

    return _render_inline_snapshot_prompt(
        manifest,
        profile=profile,
        artifact_path=artifact_path,
    )


def render_effective_prompt(manifest_path: Path, workspace_root: Path | None = None) -> str:
    workspace = infer_workspace_root(workspace_root or manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return render_effective_prompt_from_manifest(manifest, workspace_root=workspace)
