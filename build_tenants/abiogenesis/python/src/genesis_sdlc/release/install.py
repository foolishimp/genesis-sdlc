# Implements: REQ-F-BOOT-001
# Implements: REQ-F-BOOT-002
# Implements: REQ-F-BOOT-003
# Implements: REQ-F-BOOT-004
# Implements: REQ-F-CUSTODY-003
# Implements: REQ-F-TERRITORY-001
# Implements: REQ-F-TERRITORY-002
"""Installer for the Abiogenesis/Python genesis_sdlc realization."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

if __package__ in {None, ""}:
    _SRC_ROOT = Path(__file__).resolve().parents[2]
    if str(_SRC_ROOT) not in sys.path:
        sys.path.insert(0, str(_SRC_ROOT))
    from genesis_sdlc.release.bootloader import spec_hash, synthesize_bootloader
    from genesis_sdlc.release.territory import (
        install_operating_standards,
        install_runtime_package,
        install_specification,
        install_tenant_snapshot,
        install_versioned_snapshot,
        scaffold_project_requirements,
    )
    from genesis_sdlc.release.wrapper import load_project_requirements, render_wrapper
else:
    from .bootloader import spec_hash, synthesize_bootloader
    from .territory import (
        install_operating_standards,
        install_runtime_package,
        install_specification,
        install_tenant_snapshot,
        install_versioned_snapshot,
        scaffold_project_requirements,
    )
    from .wrapper import load_project_requirements, render_wrapper


VERSION = "1.0.0rc1"
_BOOTLOADER_START = "<!-- SDLC_BOOTLOADER_START -->"
_BOOTLOADER_END = "<!-- SDLC_BOOTLOADER_END -->"


def _repo_root_from_file() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "build_tenants" / "abiogenesis" / "python").is_dir() and (parent / "specification").is_dir():
            return parent
    return None


def resolve_source(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    resolved = _repo_root_from_file()
    if resolved is None:
        raise FileNotFoundError("could not resolve genesis_sdlc source root; pass --source")
    return resolved


def _abiogenesis_installer(source_root: Path) -> Path:
    installer = source_root.parent / "abiogenesis" / "builds" / "claude_code" / "code" / "gen-install.py"
    if not installer.exists():
        raise FileNotFoundError(f"abiogenesis installer not found: {installer}")
    return installer


def _run_abiogenesis_install(source_root: Path, target_root: Path) -> dict[str, object]:
    installer = _abiogenesis_installer(source_root)
    result = subprocess.run(
        [sys.executable, str(installer), "--target", str(target_root)],
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"abiogenesis install failed (exit {result.returncode})\n"
            f"stdout:\n{result.stdout}\n\nstderr:\n{result.stderr}"
        )
    return json.loads(result.stdout)


def _write_runtime_contract(target_root: Path, slug: str) -> Path:
    contract_path = target_root / ".gsdlc" / "release" / "genesis.yml"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        "\n".join(
            [
                "# genesis_sdlc runtime contract",
                f"module: gtl_spec.packages.{slug}:package",
                f"package: gtl_spec.packages.{slug}:package",
                f"worker: gtl_spec.packages.{slug}:worker",
                "pythonpath:",
                "  - .gsdlc/release",
                "active_workflow: .gsdlc/release/active-workflow.json",
                "workflow_root: .gsdlc/release/workflows",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return contract_path


def _wire_kernel_contract(target_root: Path) -> None:
    kernel_path = target_root / ".genesis" / "genesis.yml"
    if not kernel_path.exists():
        return
    text = kernel_path.read_text(encoding="utf-8")
    desired = "runtime_contract: .gsdlc/release/genesis.yml"
    if desired in text:
        return
    if "# runtime_contract: path/to/domain/genesis.yml" in text:
        text = text.replace("# runtime_contract: path/to/domain/genesis.yml", desired)
    else:
        text = text.rstrip() + f"\n{desired}\n"
    kernel_path.write_text(text, encoding="utf-8")


def _write_active_workflow(target_root: Path, slug: str) -> Path:
    active_path = target_root / ".gsdlc" / "release" / "active-workflow.json"
    active_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "workflow": "genesis_sdlc.standard",
        "version": VERSION,
        "slug": slug,
        "package": f"gtl_spec.packages.{slug}:package",
        "worker": f"gtl_spec.packages.{slug}:worker",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    active_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return active_path


def _write_wrapper(target_root: Path, slug: str) -> Path:
    wrapper_path = target_root / ".gsdlc" / "release" / "gtl_spec" / "packages" / f"{slug}.py"
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    for init_dir in [
        target_root / ".gsdlc" / "release" / "gtl_spec",
        target_root / ".gsdlc" / "release" / "gtl_spec" / "packages",
    ]:
        init_path = init_dir / "__init__.py"
        if not init_path.exists():
            init_path.write_text("", encoding="utf-8")
    wrapper_path.write_text(render_wrapper(slug=slug, version=VERSION), encoding="utf-8")
    return wrapper_path


def _write_user_guide(target_root: Path, requirements: list[str]) -> Path:
    guide_path = target_root / "build_tenants" / "abiogenesis" / "python" / "release" / "USER_GUIDE.md"
    guide_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Genesis SDLC User Guide",
        "",
        f"Version: {VERSION}",
        "",
        "## Install",
        "",
        "Run the ABG installer first, then genesis_sdlc install into the target workspace.",
        "",
        "## First Session",
        "",
        "Bootstrap the workspace, inspect gaps, then iterate the next edge.",
        "",
        "## Operating Loop",
        "",
        "Use `genesis gaps`, `genesis iterate`, and `genesis start` against the installed workspace.",
        "",
        "## Recovery",
        "",
        "Repair missing files, restore references, then rerun gap analysis.",
        "",
    ]
    if requirements:
        lines.append("## Requirement Tags")
        lines.append("")
        lines.extend(f"- {req}" for req in requirements[:10])
        lines.append("")
    guide_path.write_text("\n".join(lines), encoding="utf-8")
    return guide_path


def _install_domain_bootloader(target_root: Path, requirements: list[str]) -> Path:
    release_bootloader = target_root / ".gsdlc" / "release" / "SDLC_BOOTLOADER.md"
    synthesize_bootloader(requirements=requirements, version=VERSION, output_path=release_bootloader)

    source_bootloader = target_root / "build_tenants" / "abiogenesis" / "python" / "release" / "SDLC_BOOTLOADER.md"
    shutil.copy2(release_bootloader, source_bootloader)
    return release_bootloader


def _install_control_surface(target_root: Path) -> str:
    claude_md = target_root / "CLAUDE.md"
    section = (
        f"{_BOOTLOADER_START}\n"
        "The installed genesis_sdlc release is active.\n"
        "Read workspace://.gsdlc/release/SDLC_BOOTLOADER.md first, then follow its referenced docs.\n"
        f"{_BOOTLOADER_END}\n"
    )
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
        if _BOOTLOADER_START in text and _BOOTLOADER_END in text:
            start = text.index(_BOOTLOADER_START)
            end = text.index(_BOOTLOADER_END) + len(_BOOTLOADER_END)
            updated = text[:start] + section + text[end:]
            claude_md.write_text(updated, encoding="utf-8")
            return "updated"
        claude_md.write_text(text.rstrip() + "\n\n" + section, encoding="utf-8")
        return "appended"
    claude_md.write_text(section, encoding="utf-8")
    return "created"


def _emit_install_event(target_root: Path, slug: str, requirements: list[str]) -> None:
    events_dir = target_root / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "event_type": "genesis_sdlc_installed",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "data": {
            "version": VERSION,
            "slug": slug,
            "spec_hash": spec_hash(requirements),
            "status": "installed",
        },
    }
    with (events_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event) + "\n")


def install(
    target: Path,
    *,
    source: Path | None = None,
    slug: str = "sandbox_project",
    audit_only: bool = False,
) -> dict[str, object]:
    target_root = target.resolve()
    source_root = resolve_source(str(source) if source is not None else None)

    if audit_only:
        required = [
            target_root / ".genesis" / "genesis.yml",
            target_root / ".gsdlc" / "release" / "genesis.yml",
            target_root / ".gsdlc" / "release" / "active-workflow.json",
            target_root / ".gsdlc" / "release" / "gtl_spec" / "packages" / f"{slug}.py",
            target_root / ".gsdlc" / "release" / "genesis_sdlc" / "workflow" / "package.py",
        ]
        missing = [str(path.relative_to(target_root)) for path in required if not path.exists()]
        return {"status": "ok" if not missing else "drift_detected", "missing": missing}

    abg = _run_abiogenesis_install(source_root, target_root)
    install_specification(source_root, target_root)
    scaffold_project_requirements(target_root)
    install_tenant_snapshot(source_root, target_root)
    install_runtime_package(source_root, target_root)
    version_dir = install_versioned_snapshot(source_root, target_root, VERSION)
    standards = install_operating_standards(source_root, target_root)
    contract_path = _write_runtime_contract(target_root, slug)
    _wire_kernel_contract(target_root)
    active_workflow = _write_active_workflow(target_root, slug)
    wrapper_path = _write_wrapper(target_root, slug)
    requirements = load_project_requirements(target_root)
    guide_path = _write_user_guide(target_root, requirements)
    bootloader_path = _install_domain_bootloader(target_root, requirements)
    control_surface = _install_control_surface(target_root)
    _emit_install_event(target_root, slug, requirements)

    return {
        "status": "installed",
        "version": VERSION,
        "slug": slug,
        "target": str(target_root),
        "source": str(source_root),
        "abiogenesis": abg.get("status"),
        "active_workflow": str(active_workflow.relative_to(target_root)),
        "runtime_contract": str(contract_path.relative_to(target_root)),
        "wrapper": str(wrapper_path.relative_to(target_root)),
        "guide": str(guide_path.relative_to(target_root)),
        "bootloader": str(bootloader_path.relative_to(target_root)),
        "versioned_release": str(version_dir.relative_to(target_root)),
        "operating_standards": standards,
        "claude_md": control_surface,
        "requirements_loaded": len(requirements),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--source")
    parser.add_argument("--project-slug", default="sandbox_project")
    parser.add_argument("--audit", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = install(
        Path(args.target),
        source=Path(args.source).resolve() if args.source else None,
        slug=args.project_slug,
        audit_only=args.audit,
    )
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("status") in {"installed", "ok"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
