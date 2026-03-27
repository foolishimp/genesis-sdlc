# Implements: REQ-F-BOOTDOC-003
# Implements: REQ-F-BOOTDOC-002
"""Bootloader synthesis for released sandboxes."""

from __future__ import annotations

import hashlib
from pathlib import Path


def spec_hash(requirements: list[str]) -> str:
    return "sha256:" + hashlib.sha256("\n".join(requirements).encode("utf-8")).hexdigest()


def synthesize_bootloader(
    *,
    requirements: list[str],
    version: str,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    content = f"""# SDLC Bootloader

Version: {version}
Spec-Hash: {spec_hash(requirements)}

## Authority

- This carrier orients the agent to the installed genesis_sdlc release.
- ABG owns engine execution. genesis_sdlc owns the domain workflow and evidence surface.

## Axioms

- Specification defines the what.
- Design defines the how.
- Evaluate and close gaps before claiming convergence.

## Active Docs

- workspace://specification/INTENT.md
- workspace://specification/requirements/02-graph.md
- workspace://build_tenants/common/design/README.md
- workspace://build_tenants/abiogenesis/python/design/module_decomp.md

## Commands

- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis gaps --workspace .`
- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis iterate --workspace .`
- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis start --workspace .`
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path
