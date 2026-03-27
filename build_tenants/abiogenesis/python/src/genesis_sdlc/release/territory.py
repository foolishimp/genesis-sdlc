# Implements: REQ-F-TERRITORY-001
# Implements: REQ-F-TERRITORY-002
"""Helpers for staging release and source territories into a target workspace."""

from __future__ import annotations

import shutil
from pathlib import Path


def _copy_tree(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns(
            "__pycache__",
            "*.pyc",
            ".pytest_cache",
            "test_runs",
        ),
    )


def install_runtime_package(source_root: Path, target_root: Path) -> None:
    src = source_root / "build_tenants" / "abiogenesis" / "python" / "src" / "genesis_sdlc"
    dst = target_root / ".gsdlc" / "release" / "genesis_sdlc"
    _copy_tree(src, dst)


def install_versioned_snapshot(source_root: Path, target_root: Path, version: str) -> Path:
    version_dir = (
        target_root
        / ".gsdlc"
        / "release"
        / "workflows"
        / "genesis_sdlc"
        / "standard"
        / f"v{version.replace('.', '_')}"
    )
    package_dir = version_dir / "genesis_sdlc"
    src = source_root / "build_tenants" / "abiogenesis" / "python" / "src" / "genesis_sdlc"
    version_dir.mkdir(parents=True, exist_ok=True)
    _copy_tree(src, package_dir)

    init_chain = [
        target_root / ".gsdlc" / "release" / "workflows",
        target_root / ".gsdlc" / "release" / "workflows" / "genesis_sdlc",
        target_root / ".gsdlc" / "release" / "workflows" / "genesis_sdlc" / "standard",
        version_dir,
    ]
    for init_dir in init_chain:
        init_path = init_dir / "__init__.py"
        init_path.parent.mkdir(parents=True, exist_ok=True)
        if not init_path.exists():
            init_path.write_text("", encoding="utf-8")
    return version_dir


def install_tenant_snapshot(source_root: Path, target_root: Path) -> None:
    build_tenants_root = source_root / "build_tenants"
    _copy_tree(build_tenants_root, target_root / "build_tenants")


def install_specification(source_root: Path, target_root: Path) -> None:
    src = source_root / "specification"
    _copy_tree(src, target_root / "specification")


def install_operating_standards(source_root: Path, target_root: Path) -> list[str]:
    standards_src = source_root / "specification" / "standards"
    standards_dst = target_root / ".gsdlc" / "release" / "operating-standards"
    standards_dst.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    for path in sorted(standards_src.glob("*.md")):
        shutil.copy2(path, standards_dst / path.name)
        installed.append(path.name)
    return installed


def scaffold_project_requirements(target_root: Path) -> None:
    requirements_dir = target_root / "specification" / "requirements"
    requirements_dir.mkdir(parents=True, exist_ok=True)
    starter = requirements_dir / "00-starter.md"
    if not starter.exists():
        starter.write_text(
            "# Starter Requirements\n\n"
            "### REQ-F-STARTER-001 — Replace me\n\n"
            "Describe the first project-specific requirement.\n",
            encoding="utf-8",
        )
