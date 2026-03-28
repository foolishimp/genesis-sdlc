# Implements: REQ-F-CMD-004
# Implements: REQ-F-CTRL-006
"""Read-model prompt rendering from the resolved runtime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from genesis_sdlc.workflow.transforms import CONSTRUCTIVE_TURN_RULES, LIVE_MODE_PREAMBLE

from .resolve import load_resolved_runtime
from .state import infer_workspace_root


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

    artifact_path = artifact_override or Path(str(profile["suggested_output"]))

    lines = [
        LIVE_MODE_PREAMBLE.rstrip(),
        CONSTRUCTIVE_TURN_RULES.format(artifact_path=artifact_path).rstrip(),
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
    requirement_refs = profile.get("requirement_refs", [])
    if requirement_refs:
        lines.append("Project requirement refs:")
        lines.extend(f"- {ref}" for ref in requirement_refs)
    design_refs = profile.get("design_refs", [])
    if design_refs:
        lines.append("Project design refs:")
        lines.extend(f"- {ref}" for ref in design_refs)
    required_sections = profile.get("required_sections", [])
    if required_sections:
        lines.append("The artifact must contain these exact sections:")
        lines.extend(f"- {section}" for section in required_sections)
    lines.extend(("", str(manifest["prompt"])))
    return "\n".join(lines)


def render_effective_prompt(manifest_path: Path, workspace_root: Path | None = None) -> str:
    workspace = infer_workspace_root(workspace_root or manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return render_effective_prompt_from_manifest(manifest, workspace_root=workspace)
