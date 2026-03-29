# Implements: REQ-F-BOOT-001
# Implements: REQ-F-BOOT-002
# Implements: REQ-F-BOOT-003
# Implements: REQ-F-BOOT-004
# Implements: REQ-F-BOOT-011
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
    from genesis_sdlc.evidence.docs import synthesize_user_guide
    from genesis_sdlc.runtime.resolve import compile_resolved_runtime
    from genesis_sdlc.runtime.state import ensure_runtime_state_dir
    from genesis_sdlc.release.bootloader import spec_hash, synthesize_bootloader
    from genesis_sdlc.release.territory import (
        install_design_snapshot,
        install_operating_standards,
        install_project_scaffold,
        install_project_templates,
        install_runtime_carrier,
        install_runtime_package,
        install_test_snapshot,
        install_versioned_snapshot,
    )
    from genesis_sdlc.release.wrapper import load_project_requirements, render_wrapper
else:
    from ..evidence.docs import synthesize_user_guide
    from ..runtime.resolve import compile_resolved_runtime
    from ..runtime.state import ensure_runtime_state_dir
    from .bootloader import spec_hash, synthesize_bootloader
    from .territory import (
        install_design_snapshot,
        install_operating_standards,
        install_project_scaffold,
        install_project_templates,
        install_runtime_carrier,
        install_runtime_package,
        install_test_snapshot,
        install_versioned_snapshot,
    )
    from .wrapper import load_project_requirements, render_wrapper


VERSION = "1.0rc1"
TENANT_FAMILY = "abiogenesis"
TENANT_VARIANT = "python"
TENANT_LABEL = f"{TENANT_FAMILY}/{TENANT_VARIANT}"
TENANT_ROOT = f"build_tenants/{TENANT_LABEL}"
TENANT_DESIGN_ROOT = f"{TENANT_ROOT}/design"
FP_CUSTOMIZATION_ROOT = f"{TENANT_DESIGN_ROOT}/fp/edge-overrides"
_BOOTLOADER_START = "<!-- SDLC_BOOTLOADER_START -->"
_BOOTLOADER_END = "<!-- SDLC_BOOTLOADER_END -->"
_ENGINE_COMMANDS = ("gen-start", "gen-gaps", "gen-status")
_DOMAIN_COMMANDS = ("gen-iterate", "gen-review")
_RUNTIME_RESET_DIRS = (
    Path(".ai-workspace/events"),
    Path(".ai-workspace/features"),
    Path(".ai-workspace/fp_manifests"),
    Path(".ai-workspace/fp_results"),
    Path(".ai-workspace/runtime"),
    Path(".ai-workspace/reviews"),
    Path(".ai-workspace/uat"),
)


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
    installer = (
        source_root.parent
        / "abiogenesis"
        / "build_tenants"
        / "abiogenesis"
        / "python"
        / "code"
        / "gen-install.py"
    )
    if not installer.exists():
        raise FileNotFoundError(f"abiogenesis installer not found: {installer}")
    return installer


def _abiogenesis_command_dir(source_root: Path) -> Path:
    command_dir = (
        source_root.parent
        / "abiogenesis"
        / "build_tenants"
        / "abiogenesis"
        / "python"
        / ".claude-plugin"
        / "plugins"
        / "genesis"
        / "commands"
    )
    if not command_dir.exists():
        raise FileNotFoundError(f"abiogenesis commands not found: {command_dir}")
    return command_dir


def _domain_command_dir(source_root: Path) -> Path:
    command_dir = source_root / "build_tenants" / "abiogenesis" / "python" / "release" / "commands"
    if not command_dir.exists():
        raise FileNotFoundError(f"genesis_sdlc commands not found: {command_dir}")
    return command_dir


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
        "managed_surfaces": [
            ".genesis/",
            ".gsdlc/release/",
            ".claude/commands/",
            "CLAUDE.md[SDLC_BOOTLOADER]",
            "AGENTS.md[SDLC_BOOTLOADER]",
        ],
        "territory_boundary": {
            "authoring_forbidden_on_default_install": [
                "specification/standards/",
            ],
            "release_managed": [
                ".genesis/",
                ".gsdlc/release/",
                ".claude/commands/",
            ],
            "customization": [
                "specification/",
                "build_tenants/",
                "docs/",
                ".gsdlc/release/active-workflow.json[customization]",
            ],
            "runtime_state": [
                ".ai-workspace/runtime/",
            ],
        },
        "customization": {
            "requirements_root": "specification/requirements",
            "tenant_design_root": TENANT_DESIGN_ROOT,
            "fp_customization_root": FP_CUSTOMIZATION_ROOT,
            "default_worker_assignments": {
                "constructor": "claude_code",
                "implementer": "claude_code",
            },
        },
        "reset": {
            "runtime": {
                "mode": "reset-runtime",
                "clears": [str(path) for path in _RUNTIME_RESET_DIRS],
            },
            "managed": {
                "mode": "reinstall",
                "preserves": [
                    "specification/",
                    ".ai-workspace/comments/",
                ],
            },
        },
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    active_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return active_path


def _installed_slug(target_root: Path, fallback: str) -> str:
    active_path = target_root / ".gsdlc" / "release" / "active-workflow.json"
    if not active_path.exists():
        return fallback
    try:
        payload = json.loads(active_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return fallback
    slug = payload.get("slug")
    return slug if isinstance(slug, str) and slug else fallback


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
    guide_path = target_root / ".gsdlc" / "release" / "USER_GUIDE.md"
    return synthesize_user_guide(guide_path, version=VERSION, requirements=requirements)


def _install_domain_bootloader(target_root: Path, requirements: list[str]) -> Path:
    release_bootloader = target_root / ".gsdlc" / "release" / "SDLC_BOOTLOADER.md"
    synthesize_bootloader(
        requirements=requirements,
        version=VERSION,
        output_path=release_bootloader,
        workspace_root=target_root,
    )
    return release_bootloader


def _default_worker_assignments(target_root: Path) -> dict[str, str]:
    active_workflow = target_root / ".gsdlc" / "release" / "active-workflow.json"
    if not active_workflow.exists():
        return {}
    try:
        payload = json.loads(active_workflow.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    customization = payload.get("customization", {})
    if not isinstance(customization, dict):
        return {}
    assignments = customization.get("default_worker_assignments", {})
    if not isinstance(assignments, dict):
        return {}
    return {
        str(role_id): str(worker_id)
        for role_id, worker_id in assignments.items()
        if isinstance(role_id, str) and role_id and isinstance(worker_id, str) and worker_id
    }


def _control_surface_section(target_root: Path) -> str:
    default_assignments = _default_worker_assignments(target_root)
    default_assignment_lines = "\n".join(
        f"- `{role_id}` -> `{worker_id}`" for role_id, worker_id in sorted(default_assignments.items())
    ) or "- No default worker assignments declared."
    return (
        f"{_BOOTLOADER_START}\n"
        "The installed genesis_sdlc release is active.\n"
        "Read workspace://.gsdlc/release/SDLC_BOOTLOADER.md first, then follow its referenced docs.\n"
        "\n"
        "Installed axioms:\n"
        "- Specification defines project truth; design surfaces define realization.\n"
        "- `workspace://build_tenants/TENANT_REGISTRY.md` is the canonical registry of tenant families, variants, and activity state.\n"
        "- The only lawful operative path is the resolved runtime at workspace://.ai-workspace/runtime/resolved-runtime.json.\n"
        "- One edge traversal binds one role and one worker assignment.\n"
        "- Backend identity is derived from worker assignment, not selected independently.\n"
        "- Managed methodology surfaces live under workspace://.gsdlc/release/; project-owned surfaces live under workspace://specification/, workspace://build_tenants/, and workspace://docs/.\n"
        "- Runtime/session state lives under workspace://.ai-workspace/runtime/; when it differs from release defaults, the resolved runtime wins.\n"
        "\n"
        "Default role assignments for this install:\n"
        f"{default_assignment_lines}\n"
        f"{_BOOTLOADER_END}\n"
    )


def _upsert_control_surface(path: Path, section: str) -> str:
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if _BOOTLOADER_START in text and _BOOTLOADER_END in text:
            start = text.index(_BOOTLOADER_START)
            end = text.index(_BOOTLOADER_END) + len(_BOOTLOADER_END)
            updated = text[:start] + section + text[end:]
            path.write_text(updated, encoding="utf-8")
            return "updated"
        path.write_text(text.rstrip() + "\n\n" + section, encoding="utf-8")
        return "appended"
    path.write_text(section, encoding="utf-8")
    return "created"


def _install_control_surfaces(target_root: Path) -> dict[str, str]:
    section = _control_surface_section(target_root)
    return {
        "claude_md": _upsert_control_surface(target_root / "CLAUDE.md", section),
        "agents_md": _upsert_control_surface(target_root / "AGENTS.md", section),
    }


def _install_commands(source_root: Path, target_root: Path) -> list[str]:
    commands_dir = target_root / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    command_sources = (
        (_ENGINE_COMMANDS, _abiogenesis_command_dir(source_root)),
        (_DOMAIN_COMMANDS, _domain_command_dir(source_root)),
    )
    active_files = {f"{name}.md" for names, _ in command_sources for name in names}

    for stale in commands_dir.glob("gen-*.md"):
        if stale.name not in active_files:
            stale.unlink()

    installed: list[str] = []
    for names, root in command_sources:
        for name in names:
            src = root / f"{name}.md"
            if not src.exists():
                raise FileNotFoundError(f"command source missing: {src}")
            shutil.copy2(src, commands_dir / f"{name}.md")
            installed.append(name)

    stamp = commands_dir / ".genesis-installed"
    stamp.write_text(
        json.dumps(
            {
                "version": VERSION,
                "installed": installed,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return installed


def reset_runtime(target: Path) -> dict[str, object]:
    target_root = target.resolve()
    cleared: list[str] = []
    for relative in _RUNTIME_RESET_DIRS:
        path = target_root / relative
        if path.exists():
            shutil.rmtree(path)
            cleared.append(str(relative))
        path.mkdir(parents=True, exist_ok=True)
    return {
        "status": "runtime_reset",
        "target": str(target_root),
        "cleared": cleared,
        "preserved": [
            ".genesis/",
            ".gsdlc/release/",
            ".claude/commands/",
            "specification/",
        ],
    }


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
        audit_slug = _installed_slug(target_root, slug)
        required = [
            target_root / ".genesis" / "genesis.yml",
            target_root / ".gsdlc" / "release" / "genesis.yml",
            target_root / ".gsdlc" / "release" / "active-workflow.json",
            target_root / ".gsdlc" / "release" / "gtl_spec" / "packages" / f"{audit_slug}.py",
            target_root / ".gsdlc" / "release" / "genesis_sdlc" / "workflow" / "package.py",
            target_root / ".gsdlc" / "release" / "design" / "module_decomp.md",
            target_root / ".gsdlc" / "release" / "tests",
            target_root / ".gsdlc" / "release" / "USER_GUIDE.md",
            target_root / ".gsdlc" / "release" / "runtime" / "backends.json",
            target_root / ".gsdlc" / "release" / "runtime" / "adapter-contract.json",
            target_root / ".gsdlc" / "release" / "runtime" / "workers.json",
            target_root / ".gsdlc" / "release" / "runtime" / "role-assignments.json",
            target_root / ".gsdlc" / "release" / "SDLC_BOOTLOADER.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "INTENT_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "TENANT_REGISTRY_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "common" / "README_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "common" / "design" / "README_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "README_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "design" / "README_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "design" / "fp" / "README_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "design" / "fp" / "INTENT_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "design" / "fp" / "edge-overrides" / "README_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "build_tenants" / "variant" / "design" / "fp" / "edge-overrides" / "EDGE_OVERRIDE_TEMPLATE.json",
            target_root / ".gsdlc" / "release" / "project-templates" / "docs" / "README_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "requirements" / "README_TEMPLATE.md",
            target_root / ".gsdlc" / "release" / "project-templates" / "requirements" / "STARTER_REQUIREMENTS_TEMPLATE.md",
            target_root / "specification" / "INTENT.md",
            target_root / "build_tenants" / "TENANT_REGISTRY.md",
            target_root / "build_tenants" / "common" / "README.md",
            target_root / "build_tenants" / "common" / "design" / "README.md",
            target_root / "build_tenants" / TENANT_FAMILY / TENANT_VARIANT / "README.md",
            target_root / "build_tenants" / TENANT_FAMILY / TENANT_VARIANT / "design" / "README.md",
            target_root / "build_tenants" / TENANT_FAMILY / TENANT_VARIANT / "design" / "fp" / "README.md",
            target_root / "build_tenants" / TENANT_FAMILY / TENANT_VARIANT / "design" / "fp" / "INTENT.md",
            target_root / "build_tenants" / TENANT_FAMILY / TENANT_VARIANT / "design" / "fp" / "edge-overrides" / "README.md",
            target_root / "docs" / "README.md",
            target_root / "specification" / "requirements" / "README.md",
            target_root / "AGENTS.md",
            target_root / ".claude" / "commands" / "gen-start.md",
            target_root / ".claude" / "commands" / "gen-gaps.md",
            target_root / ".claude" / "commands" / "gen-status.md",
            target_root / ".claude" / "commands" / "gen-iterate.md",
            target_root / ".claude" / "commands" / "gen-review.md",
            target_root / ".claude" / "commands" / ".genesis-installed",
        ]
        missing = [str(path.relative_to(target_root)) for path in required if not path.exists()]
        forbidden = [
            target_root / "specification" / "standards",
        ]
        present_forbidden = [str(path.relative_to(target_root)) for path in forbidden if path.exists()]
        return {
            "status": "ok" if not missing and not present_forbidden else "drift_detected",
            "slug": audit_slug,
            "missing": missing,
            "forbidden_present": present_forbidden,
        }

    target_root.mkdir(parents=True, exist_ok=True)
    abg = _run_abiogenesis_install(source_root, target_root)
    install_project_templates(source_root, target_root)
    install_project_scaffold(source_root, target_root)
    install_runtime_package(source_root, target_root)
    install_runtime_carrier(source_root, target_root)
    install_design_snapshot(source_root, target_root)
    install_test_snapshot(source_root, target_root)
    version_dir = install_versioned_snapshot(source_root, target_root, VERSION)
    standards = install_operating_standards(source_root, target_root)
    contract_path = _write_runtime_contract(target_root, slug)
    _wire_kernel_contract(target_root)
    active_workflow = _write_active_workflow(target_root, slug)
    wrapper_path = _write_wrapper(target_root, slug)
    commands = _install_commands(source_root, target_root)
    requirements = load_project_requirements(target_root)
    guide_path = _write_user_guide(target_root, requirements)
    bootloader_path = _install_domain_bootloader(target_root, requirements)
    control_surfaces = _install_control_surfaces(target_root)
    ensure_runtime_state_dir(target_root)
    resolved_runtime = compile_resolved_runtime(target_root)
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
        "commands": commands,
        "guide": str(guide_path.relative_to(target_root)),
        "bootloader": str(bootloader_path.relative_to(target_root)),
        "resolved_runtime": ".ai-workspace/runtime/resolved-runtime.json",
        "versioned_release": str(version_dir.relative_to(target_root)),
        "operating_standards": standards,
        **control_surfaces,
        "requirements_loaded": len(requirements),
        "selected_assignments": resolved_runtime.get("role_assignments", {}),
        "role_assignments": resolved_runtime.get("role_assignments", {}),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--source")
    parser.add_argument("--project-slug", default="sandbox_project")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--reset-runtime", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if args.reset_runtime:
        payload = reset_runtime(Path(args.target))
    else:
        payload = install(
            Path(args.target),
            source=Path(args.source).resolve() if args.source else None,
            slug=args.project_slug,
            audit_only=args.audit,
        )
    print(json.dumps(payload, indent=2))
    return 0 if payload.get("status") in {"installed", "ok", "runtime_reset"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
