# Implements: REQ-F-DOCS-001
# Implements: REQ-F-DOCS-002
# Implements: REQ-F-BOOTDOC-003
"""Documentation and bootloader evidence helpers."""

from __future__ import annotations

from pathlib import Path

from genesis_sdlc.workflow.transforms import BOOTLOADER_SECTIONS, USER_GUIDE_SECTIONS


Assessment = dict[str, str]
GUIDE_TERMS = (
    "genesis start",
    "gen-start",
    "genesis iterate",
    "gen-iterate",
    "genesis gaps",
    "gen-gaps",
    "f_d",
    "f_p",
    "f_h",
    "event stream",
    "delta",
    "fd_gap",
    "fp_dispatch",
    "fh_gate",
)
BOOTLOADER_TERMS = (
    "workspace://",
    "specification defines the what",
    "design defines the how",
    "genesis gaps",
    "genesis iterate",
    "genesis start",
)


def _single(evaluator: str, result: str, evidence: str) -> list[Assessment]:
    return [{"evaluator": evaluator, "result": result, "evidence": evidence}]


def synthesize_user_guide(output_path: Path, *, version: str, requirements: list[str]) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    requirement_lines = "\n".join(f"- {requirement}" for requirement in requirements) or "- none"
    content = f"""# Genesis SDLC User Guide

Version: {version}

## Installation

Install the ABG kernel first, then install the genesis_sdlc release into the target workspace.
Use `genesis start` (`gen-start`), `genesis iterate` (`gen-iterate`), and `genesis gaps` (`gen-gaps`)
from the installed workspace.

## First Session

Raise or inspect intent, run `genesis gaps`, and review the current delta before iterating the next
edge. Treat the event stream as the durable record of approvals, assessed results, and convergence
state.

## Operating Loop

`F_D` closes deterministic checks, `F_P` performs bounded construction or assessment, and `F_H`
approves release-critical gates. Delta falls as each blocking edge is satisfied; keep iterating until
the required release edges are closed.

## Recovery

If `fd_gap` appears, repair the deterministic surface and rerun gap analysis. If `fp_dispatch`
appears, complete the bounded construction or assessment and submit the result. If an `fh_gate`
appears, perform the required review and approval. Re-run `genesis gaps` after each recovery step.

## Requirement Tags

{requirement_lines}
"""
    output_path.write_text(content, encoding="utf-8")
    return output_path


def assess_user_guide_artifact(artifact: Path, requirement_keys: list[str]) -> list[Assessment]:
    if not artifact.exists():
        return _single("guide_content_certified", "fail", f"user guide missing: {artifact}")

    text = artifact.read_text(encoding="utf-8")
    missing_headers = [header for header in USER_GUIDE_SECTIONS if header not in text]
    if missing_headers:
        return _single("guide_content_certified", "fail", f"user guide missing sections: {missing_headers}")

    lowered = text.lower()
    missing_terms = [term for term in GUIDE_TERMS if term not in lowered]
    if missing_terms:
        return _single("guide_content_certified", "fail", f"user guide missing expected terms: {missing_terms}")

    missing_requirements = [req for req in requirement_keys if req not in text]
    if missing_requirements:
        return _single(
            "guide_content_certified",
            "fail",
            f"user guide missing active requirement tags: {missing_requirements}",
        )

    return _single(
        "guide_content_certified",
        "pass",
        "user guide covers installation, first session, operating loop, recovery, and active requirement tags.",
    )


def assess_bootloader_artifact(artifact: Path) -> list[Assessment]:
    if not artifact.exists():
        return _single("synthesize_bootloader", "fail", f"bootloader missing: {artifact}")

    text = artifact.read_text(encoding="utf-8")
    missing_headers = [header for header in BOOTLOADER_SECTIONS if header not in text]
    if missing_headers:
        return _single("synthesize_bootloader", "fail", f"bootloader missing sections: {missing_headers}")

    lowered = text.lower()
    missing_terms = [term for term in BOOTLOADER_TERMS if term not in lowered]
    if missing_terms:
        return _single("synthesize_bootloader", "fail", f"bootloader missing expected terms: {missing_terms}")

    return _single(
        "synthesize_bootloader",
        "pass",
        "bootloader contains the required sections, runtime commands, and workspace references.",
    )
