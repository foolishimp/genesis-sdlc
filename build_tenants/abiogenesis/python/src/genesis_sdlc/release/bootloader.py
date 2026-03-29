# Implements: REQ-F-BOOTDOC-003
# Implements: REQ-F-BOOTDOC-002
"""Bootloader synthesis for released sandboxes."""

from __future__ import annotations

import hashlib
from pathlib import Path


def _discover_requirement_docs(workspace_root: Path) -> list[str]:
    requirements_root = workspace_root / "specification" / "requirements"
    if not requirements_root.exists():
        return []
    return sorted(
        f"workspace://{path.relative_to(workspace_root).as_posix()}"
        for path in requirements_root.rglob("*.md")
        if path.name != "README.md"
    )


def _active_docs(workspace_root: Path) -> list[str]:
    docs: list[str] = []
    preferred = [
        workspace_root / "specification" / "INTENT.md",
        workspace_root / "build_tenants" / "TENANT_REGISTRY.md",
        workspace_root / ".gsdlc" / "release" / "operating-standards" / "SPEC_METHOD.md",
        workspace_root / ".gsdlc" / "release" / "operating-standards" / "GSDLC_METHOD.md",
        workspace_root / ".gsdlc" / "release" / "design" / "README.md",
        workspace_root / ".gsdlc" / "release" / "design" / "module_decomp.md",
    ]
    for path in preferred:
        if path.exists():
            docs.append(f"workspace://{path.relative_to(workspace_root).as_posix()}")
    docs.extend(_discover_requirement_docs(workspace_root))
    return docs


def _infer_workspace_root(path: Path) -> Path:
    resolved = path.resolve()
    for parent in resolved.parents:
        if (parent / "specification").exists() and (
            (parent / "build_tenants").exists() or (parent / ".gsdlc").exists()
        ):
            return parent
    return resolved.parent


def spec_hash(requirements: list[str]) -> str:
    return "sha256:" + hashlib.sha256("\n".join(requirements).encode("utf-8")).hexdigest()


def synthesize_bootloader(
    *,
    requirements: list[str],
    version: str,
    output_path: Path,
    workspace_root: Path | None = None,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workspace = (workspace_root or _infer_workspace_root(output_path)).resolve()
    active_docs = _active_docs(workspace)
    docs_block = "\n".join(f"- {ref}" for ref in active_docs) or "- workspace://specification/INTENT.md"
    content = f"""# SDLC Bootloader

Version: {version}
Spec-Hash: {spec_hash(requirements)}

## Authority

- This carrier orients the agent to the installed genesis_sdlc release.
- ABG owns engine execution. genesis_sdlc owns the domain workflow and evidence surface.
- Read the referenced source documents for depth; this bootloader is a compiled orientation surface.

## Axioms

- Specification defines the what.
- Design defines the how.
- Evaluate and close gaps before claiming convergence.
- F_D proves deterministic currency. F_P performs bounded construction. F_H approves release-critical gates.

## Active Docs

{docs_block}

## Commands

- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis gaps --workspace .`
- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis iterate --workspace .`
- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis start --workspace .`
- Use `genesis gaps` when drift is suspected, `genesis iterate` for the next blocking edge, and `genesis start` for the next executable job.
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path
