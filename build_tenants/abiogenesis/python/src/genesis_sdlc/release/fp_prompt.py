# Implements: REQ-F-CMD-004
"""Render effective F_P prompts from manifests using project-local customization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from genesis_sdlc.workflow.transforms import build_constructive_prompt, resolve_edge_transform_contract


def infer_workspace_root(manifest_path: Path) -> Path:
    resolved = manifest_path.resolve()
    for parent in [resolved.parent, *resolved.parents]:
        if (parent / ".gsdlc" / "release" / "active-workflow.json").exists():
            return parent
    raise FileNotFoundError(f"could not infer workspace root from manifest: {manifest_path}")


def render_effective_prompt(manifest_path: Path, workspace_root: Path | None = None) -> str:
    workspace = workspace_root or infer_workspace_root(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    edge = str(manifest["edge"])
    contract = resolve_edge_transform_contract(edge, workspace)
    if contract is None:
        raise KeyError(f"no transform contract declared for edge: {edge}")
    return build_constructive_prompt(
        edge,
        manifest,
        artifact_path=Path(contract.suggested_output),
        workspace_root=workspace,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--workspace")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    workspace = Path(args.workspace).resolve() if args.workspace else None
    prompt = render_effective_prompt(Path(args.manifest), workspace)
    print(prompt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
