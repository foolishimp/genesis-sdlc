# Implements: REQ-F-MDECOMP-003
# Implements: REQ-F-TAG-001
# Implements: REQ-F-TAG-002
# Implements: REQ-F-DOCS-002
# Implements: REQ-F-TEST-001
# Implements: REQ-F-UAT-002
# Implements: REQ-F-BOOTDOC-002
"""Deterministic checks used by workflow F_D evaluators."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from importlib import import_module
from pathlib import Path


REQ_TAG_PATTERN = re.compile(r"^# (Implements|Validates): REQ-[A-Z0-9-]+\b", re.MULTILINE)
WORKSPACE_REF_PATTERN = re.compile(r"workspace://([^\s)]+)")
BOOTLOADER_SPEC_HASH_PATTERN = re.compile(r"^Spec-Hash:\s*(\S+)\s*$", re.MULTILINE)
BOOTLOADER_VERSION_PATTERN = re.compile(r"^Version:\s*(\S+)\s*$", re.MULTILINE)
VERSION_PATTERN = re.compile(r"version\s*[:=]\s*[\"']?([A-Za-z0-9._-]+)[\"']?", re.IGNORECASE)


def _import_symbol(ref: str):
    module_name, symbol_name = ref.split(":", 1)
    module = import_module(module_name)
    return getattr(module, symbol_name)


def _iter_python_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(
        path
        for path in root.rglob("*.py")
        if path.name != "__init__.py"
    )


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _exit(ok: bool, message: str) -> int:
    if not ok:
        print(message, file=sys.stderr)
        return 1
    print(message)
    return 0


def check_requirements_loaded(package_ref: str) -> int:
    package = _import_symbol(package_ref)
    requirements = package.metadata.get("requirements")
    ok = isinstance(requirements, list)
    return _exit(ok, f"requirements_loaded={len(requirements) if ok else 'invalid'}")


def check_module_coverage(modules_root: Path) -> int:
    module_files = sorted(modules_root.glob("*.yml"))
    if not module_files:
        return _exit(False, f"no module yaml files in {modules_root}")

    required_fields = {
        "id",
        "name",
        "description",
        "implements_features",
        "dependencies",
        "rank",
        "interfaces",
        "source_files",
    }
    names: set[str] = set()
    dependencies_by_name: dict[str, list[str]] = {}
    for path in module_files:
        text = _read_text(path)
        keys = {line.split(":", 1)[0].strip() for line in text.splitlines() if ":" in line and not line.startswith("  -")}
        missing = required_fields - keys
        if missing:
            return _exit(False, f"{path} missing fields: {sorted(missing)}")
        name_match = re.search(r"^name:\s*([A-Za-z0-9_/-]+)\s*$", text, re.MULTILINE)
        if not name_match:
            return _exit(False, f"{path} missing module name")
        name = name_match.group(1)
        names.add(name)
        dependencies_by_name[name] = _parse_dependencies(text)

    for name, deps in dependencies_by_name.items():
        for dep in deps:
            if dep not in names:
                return _exit(False, f"unknown dependency {dep!r} in module {name!r}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(name: str) -> bool:
        if name in visited:
            return True
        if name in visiting:
            return False
        visiting.add(name)
        for dep in dependencies_by_name.get(name, []):
            if not visit(dep):
                return False
        visiting.remove(name)
        visited.add(name)
        return True

    acyclic = all(visit(name) for name in names)
    return _exit(acyclic, "module_coverage=ok" if acyclic else "module dependency cycle detected")


def _parse_dependencies(text: str) -> list[str]:
    inline = re.search(r"^dependencies:\s*\[\s*\]\s*$", text, re.MULTILINE)
    if inline:
        return []

    dependencies: list[str] = []
    in_block = False
    for line in text.splitlines():
        if re.match(r"^dependencies:\s*$", line):
            in_block = True
            continue
        if in_block and re.match(r"^[A-Za-z0-9_]+:\s*", line):
            break
        if in_block:
            match = re.match(r"^\s*-\s*([A-Za-z0-9_/-]+)\s*$", line)
            if match:
                dependencies.append(match.group(1))
    return dependencies


def check_trace_tags(root: Path, tag_type: str) -> int:
    files = _iter_python_files(root)
    if not files:
        return _exit(False, f"no python files found in {root}")
    tag_prefix = "Implements" if tag_type == "implements" else "Validates"
    missing = [
        str(path)
        for path in files
        if not re.search(rf"^# {tag_prefix}: REQ-[A-Z0-9-]+\b", _read_text(path), re.MULTILINE)
    ]
    return _exit(not missing, "all files tagged" if not missing else f"missing tags: {missing}")


def check_e2e_tests_exist(root: Path) -> int:
    test_files = sorted(root.rglob("test_*.py")) if root.exists() else []
    if not test_files:
        return _exit(False, f"no e2e tests found in {root}")
    found = any("@pytest.mark.e2e" in _read_text(path) for path in test_files)
    return _exit(found, "e2e_tests_exist=ok" if found else "no @pytest.mark.e2e test found")


def check_sandbox_report_exists(path: Path) -> int:
    if not path.exists():
        return _exit(False, f"sandbox report missing: {path}")
    data = json.loads(_read_text(path))
    ok = bool(data.get("all_pass"))
    return _exit(ok, "sandbox_report_exists=ok" if ok else "sandbox report not passing")


def check_guide_version_current(guide_path: Path, version_path: Path) -> int:
    if not guide_path.exists():
        return _exit(False, f"user guide missing: {guide_path}")
    if not version_path.exists():
        return _exit(False, f"version surface missing: {version_path}")
    guide_text = _read_text(guide_path)
    version_text = _read_text(version_path)
    guide_match = BOOTLOADER_VERSION_PATTERN.search(guide_text) or VERSION_PATTERN.search(guide_text)
    version_match = VERSION_PATTERN.search(version_text) or BOOTLOADER_VERSION_PATTERN.search(version_text)
    if not guide_match or not version_match:
        return _exit(False, "version marker missing from guide or workflow surface")
    ok = guide_match.group(1) == version_match.group(1)
    return _exit(ok, "guide_version_current=ok" if ok else "guide version does not match workflow version")


def check_guide_req_coverage(guide_path: Path) -> int:
    if not guide_path.exists():
        return _exit(False, f"user guide missing: {guide_path}")
    text = _read_text(guide_path)
    ok = "REQ-F-" in text
    return _exit(ok, "guide_req_coverage=ok" if ok else "user guide missing REQ-F-* tags")


def check_spec_hash_current(package_ref: str, bootloader_path: Path) -> int:
    if not bootloader_path.exists():
        return _exit(False, f"bootloader missing: {bootloader_path}")
    package = _import_symbol(package_ref)
    requirements = package.metadata.get("requirements", [])
    expected = "sha256:" + hashlib.sha256("\n".join(requirements).encode("utf-8")).hexdigest()
    match = BOOTLOADER_SPEC_HASH_PATTERN.search(_read_text(bootloader_path))
    if not match:
        return _exit(False, "bootloader missing Spec-Hash header")
    ok = match.group(1) == expected
    return _exit(ok, "spec_hash_current=ok" if ok else "bootloader spec hash mismatch")


def check_version_current(bootloader_path: Path, version_path: Path) -> int:
    if not bootloader_path.exists():
        return _exit(False, f"bootloader missing: {bootloader_path}")
    if not version_path.exists():
        return _exit(False, f"version surface missing: {version_path}")
    bootloader_text = _read_text(bootloader_path)
    version_text = _read_text(version_path)
    bootloader_match = BOOTLOADER_VERSION_PATTERN.search(bootloader_text)
    version_match = VERSION_PATTERN.search(version_text) or BOOTLOADER_VERSION_PATTERN.search(version_text)
    if not bootloader_match or not version_match:
        return _exit(False, "version marker missing from bootloader or workflow surface")
    ok = bootloader_match.group(1) == version_match.group(1)
    return _exit(ok, "version_current=ok" if ok else "bootloader version mismatch")


def check_section_coverage_complete(bootloader_path: Path) -> int:
    if not bootloader_path.exists():
        return _exit(False, f"bootloader missing: {bootloader_path}")
    text = _read_text(bootloader_path)
    required_sections = (
        "## Authority",
        "## Axioms",
        "## Active Docs",
        "## Commands",
    )
    missing = [section for section in required_sections if section not in text]
    return _exit(not missing, "section_coverage_complete=ok" if not missing else f"missing sections: {missing}")


def check_references_valid(bootloader_path: Path) -> int:
    if not bootloader_path.exists():
        return _exit(False, f"bootloader missing: {bootloader_path}")
    root = Path.cwd()
    refs = WORKSPACE_REF_PATTERN.findall(_read_text(bootloader_path))
    missing = [ref for ref in refs if not (root / ref).exists()]
    return _exit(not missing, "references_valid=ok" if not missing else f"missing refs: {missing}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("requirements_loaded")
    p.add_argument("--package-ref", required=True)

    p = sub.add_parser("module_coverage")
    p.add_argument("--modules-root", type=Path, required=True)

    p = sub.add_parser("implements_tags")
    p.add_argument("--path", type=Path, required=True)

    p = sub.add_parser("validates_tags")
    p.add_argument("--path", type=Path, required=True)

    p = sub.add_parser("e2e_tests_exist")
    p.add_argument("--path", type=Path, required=True)

    p = sub.add_parser("sandbox_report_exists")
    p.add_argument("--path", type=Path, required=True)

    p = sub.add_parser("guide_version_current")
    p.add_argument("--guide-path", type=Path, required=True)
    p.add_argument("--version-path", type=Path, required=True)

    p = sub.add_parser("guide_req_coverage")
    p.add_argument("--guide-path", type=Path, required=True)

    p = sub.add_parser("spec_hash_current")
    p.add_argument("--package-ref", required=True)
    p.add_argument("--bootloader-path", type=Path, required=True)

    p = sub.add_parser("version_current")
    p.add_argument("--bootloader-path", type=Path, required=True)
    p.add_argument("--version-path", type=Path, required=True)

    p = sub.add_parser("section_coverage_complete")
    p.add_argument("--bootloader-path", type=Path, required=True)

    p = sub.add_parser("references_valid")
    p.add_argument("--bootloader-path", type=Path, required=True)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "requirements_loaded":
        return check_requirements_loaded(args.package_ref)
    if args.command == "module_coverage":
        return check_module_coverage(args.modules_root)
    if args.command == "implements_tags":
        return check_trace_tags(args.path, "implements")
    if args.command == "validates_tags":
        return check_trace_tags(args.path, "validates")
    if args.command == "e2e_tests_exist":
        return check_e2e_tests_exist(args.path)
    if args.command == "sandbox_report_exists":
        return check_sandbox_report_exists(args.path)
    if args.command == "guide_version_current":
        return check_guide_version_current(args.guide_path, args.version_path)
    if args.command == "guide_req_coverage":
        return check_guide_req_coverage(args.guide_path)
    if args.command == "spec_hash_current":
        return check_spec_hash_current(args.package_ref, args.bootloader_path)
    if args.command == "version_current":
        return check_version_current(args.bootloader_path, args.version_path)
    if args.command == "section_coverage_complete":
        return check_section_coverage_complete(args.bootloader_path)
    if args.command == "references_valid":
        return check_references_valid(args.bootloader_path)
    raise AssertionError(args.command)


if __name__ == "__main__":
    raise SystemExit(main())
