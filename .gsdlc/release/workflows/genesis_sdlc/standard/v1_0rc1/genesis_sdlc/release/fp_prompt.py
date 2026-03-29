# Implements: REQ-F-CMD-004
"""Render effective F_P prompts from the resolved runtime."""

from __future__ import annotations

import argparse
from pathlib import Path

from genesis_sdlc.runtime.prompt_view import render_effective_prompt as render_effective_prompt_from_runtime
from genesis_sdlc.runtime.state import infer_workspace_root


def render_effective_prompt(manifest_path: Path, workspace_root: Path | None = None) -> str:
    workspace = workspace_root or infer_workspace_root(manifest_path)
    return render_effective_prompt_from_runtime(manifest_path, workspace)


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
