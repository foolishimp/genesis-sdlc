# Implements: REQ-F-TERRITORY-001
# Implements: REQ-F-TERRITORY-002
"""Helpers for staging release and scaffold territories into a target workspace."""

from __future__ import annotations

import shutil
from pathlib import Path


def _copy_tree(src: Path, dst: Path, *, exclude_subtree: Path | None = None) -> None:
    if dst.exists():
        shutil.rmtree(dst)

    ignored_name: str | None = None
    ignored_parent: tuple[str, ...] | None = None
    if exclude_subtree is not None:
        src_root = src.resolve()
        try:
            excluded_parts = exclude_subtree.resolve().relative_to(src_root).parts
        except ValueError:
            excluded_parts = ()
        if excluded_parts:
            ignored_name = excluded_parts[-1]
            ignored_parent = excluded_parts[:-1]

    def _ignore(current_dir: str, names: list[str]) -> set[str]:
        ignored = set(
            shutil.ignore_patterns(
                "__pycache__",
                "*.pyc",
                ".pytest_cache",
                "test_runs",
            )(current_dir, names)
        )
        if ignored_name is not None and ignored_parent is not None:
            try:
                rel_parts = Path(current_dir).resolve().relative_to(src.resolve()).parts
            except ValueError:
                rel_parts = ()
            if rel_parts == ignored_parent and ignored_name in names:
                ignored.add(ignored_name)
        return ignored

    shutil.copytree(
        src,
        dst,
        ignore=_ignore,
    )


def install_runtime_package(source_root: Path, target_root: Path) -> None:
    src = source_root / "build_tenants" / "abiogenesis" / "python" / "src" / "genesis_sdlc"
    dst = target_root / ".gsdlc" / "release" / "genesis_sdlc"
    _copy_tree(src, dst)


def install_design_snapshot(source_root: Path, target_root: Path) -> None:
    src = source_root / "build_tenants" / "abiogenesis" / "python" / "design"
    dst = target_root / ".gsdlc" / "release" / "design"
    _copy_tree(src, dst)


def install_test_snapshot(source_root: Path, target_root: Path) -> None:
    src = source_root / "build_tenants" / "abiogenesis" / "python" / "tests"
    dst = target_root / ".gsdlc" / "release" / "tests"
    _copy_tree(src, dst)


def install_project_templates(source_root: Path, target_root: Path) -> None:
    src = source_root / "specification" / "standards" / "templates"
    dst = target_root / ".gsdlc" / "release" / "project-templates"
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


def _copy_template_if_absent(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if not dst.exists():
        shutil.copy2(src, dst)


def install_project_scaffold(_source_root: Path, target_root: Path) -> None:
    templates_root = target_root / ".gsdlc" / "release" / "project-templates"
    template_map = {
        templates_root / "INTENT_TEMPLATE.md": target_root / "specification" / "INTENT.md",
        templates_root / "requirements" / "README_TEMPLATE.md": target_root / "specification" / "requirements" / "README.md",
        templates_root / "requirements" / "STARTER_REQUIREMENTS_TEMPLATE.md": target_root / "specification" / "requirements" / "00-starter.md",
        templates_root / "design" / "README_TEMPLATE.md": target_root / "specification" / "design" / "README.md",
        templates_root / "design" / "fp" / "README_TEMPLATE.md": target_root / "specification" / "design" / "fp" / "README.md",
        templates_root / "design" / "fp" / "INTENT_TEMPLATE.md": target_root / "specification" / "design" / "fp" / "INTENT.md",
        templates_root / "design" / "fp" / "edge-overrides" / "README_TEMPLATE.md": (
            target_root / "specification" / "design" / "fp" / "edge-overrides" / "README.md"
        ),
    }
    for src, dst in template_map.items():
        if not src.exists():
            raise FileNotFoundError(f"project scaffold template missing: {src}")
        _copy_template_if_absent(src, dst)


def install_operating_standards(source_root: Path, target_root: Path) -> list[str]:
    standards_src = source_root / "specification" / "standards"
    standards_dst = target_root / ".gsdlc" / "release" / "operating-standards"
    standards_dst.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    for path in sorted(standards_src.glob("*.md")):
        shutil.copy2(path, standards_dst / path.name)
        installed.append(path.name)
    return installed
    starter = requirements_dir / "00-starter.md"
    if not starter.exists():
        starter.write_text(
            "# Starter Requirements\n\n"
            "### REQ-F-STARTER-001 — Replace me\n\n"
            "Describe the first project-specific requirement.\n",
            encoding="utf-8",
        )
