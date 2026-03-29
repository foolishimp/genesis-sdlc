# Validates: REQ-F-BOOT-001 REQ-F-BOOT-010 REQ-F-BOOT-011 REQ-F-GRAPH-001
from __future__ import annotations

import re
from pathlib import Path


REQ_REF_RE = re.compile(r"REQ-[A-Z0-9*-]+(?:-[A-Z0-9*-]+)*")
INTENT_REF_RE = re.compile(r"\bINT-\d{3}\b")
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
BACKTICK_PATH_RE = re.compile(r"`([^`]+)`")


def _repo_root() -> Path:
    current = Path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "specification").is_dir() and (candidate / "build_tenants").is_dir():
            return candidate
    raise AssertionError("unable to locate genesis_sdlc repo root from test path")


REPO_ROOT = _repo_root()
SPEC_ROOT = REPO_ROOT / "specification"
REQUIREMENTS_ROOT = SPEC_ROOT / "requirements"
TENANT_REGISTRY = REPO_ROOT / "build_tenants" / "TENANT_REGISTRY.md"
COMMON_DESIGN_ROOT = REPO_ROOT / "build_tenants" / "common" / "design"
COMMON_QUALIFICATION_ROOT = REPO_ROOT / "build_tenants" / "common" / "qualification"
VARIANT_ROOT = REPO_ROOT / "build_tenants" / "abiogenesis" / "python"
VARIANT_DESIGN_ROOT = VARIANT_ROOT / "design"
MODULE_ROOT = VARIANT_DESIGN_ROOT / "modules"
VARIANT_TEST_ROOT = VARIANT_ROOT / "tests"
VARIANT_TEST_SURFACE_MAP = VARIANT_TEST_ROOT / "test_surface_map.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _metadata_value(text: str, label: str) -> str | None:
    match = re.search(rf"^\*\*{re.escape(label)}\*\*:\s*(.+)$", text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def _intent_ids() -> set[str]:
    return set(re.findall(r"^## (INT-\d{3})\b", _read(SPEC_ROOT / "INTENT.md"), re.MULTILINE))


def _requirement_files() -> list[Path]:
    return sorted(path for path in REQUIREMENTS_ROOT.glob("*.md") if path.name != "README.md")


def _requirement_ids() -> set[str]:
    ids: set[str] = set()
    for path in _requirement_files():
        ids.update(re.findall(r"^### (REQ-[A-Z0-9-]+)\b", _read(path), re.MULTILINE))
    return ids


def _requirement_refs(value: str | None) -> list[str]:
    if not value:
        return []
    return REQ_REF_RE.findall(value)


def _pattern_matches_requirement(ref: str, requirement_ids: set[str]) -> bool:
    if "*" in ref:
        return any(req.startswith(ref.replace("*", "")) for req in requirement_ids)
    return ref in requirement_ids


def _resolve_links(text: str, base: Path) -> list[Path]:
    resolved: list[Path] = []
    for target in LINK_RE.findall(text):
        if target.startswith("http://") or target.startswith("https://"):
            continue
        if target.startswith("/"):
            resolved.append(Path(target))
            continue
        resolved.append((base.parent / target).resolve())
    if resolved:
        return resolved
    for target in BACKTICK_PATH_RE.findall(text):
        if "/" not in target and not target.endswith(".md"):
            continue
        if target.startswith("/"):
            resolved.append(Path(target))
            continue
        resolved.append((REPO_ROOT / target).resolve())
    return resolved


def _top_level_source_files(module_path: Path) -> list[str]:
    source_files: list[str] = []
    collecting = False
    for line in _read(module_path).splitlines():
        if line.startswith("source_files:"):
            collecting = True
            continue
        if collecting:
            if line.startswith("  - "):
                source_files.append(line[4:].strip())
                continue
            if line and not line.startswith(" "):
                break
    return source_files


def _top_level_scalar(module_path: Path, key: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(key)}:\s*(.+)$", re.MULTILINE)
    match = pattern.search(_read(module_path))
    if match:
        return match.group(1).strip()
    return None


def _test_surface_map_sections() -> dict[str, str]:
    parts = re.split(r"^### (test_[^\n]+\.py)\s*$", _read(VARIANT_TEST_SURFACE_MAP), flags=re.MULTILINE)
    sections: dict[str, str] = {}
    for i in range(1, len(parts), 2):
        sections[parts[i].strip()] = parts[i + 1]
    return sections


def test_self_host_repo_has_installed_system_surfaces() -> None:
    expected_paths = [
        REPO_ROOT / ".genesis" / "genesis.yml",
        REPO_ROOT / ".gsdlc" / "release" / "active-workflow.json",
        REPO_ROOT / ".claude" / "commands" / "gen-start.md",
        REPO_ROOT / ".claude" / "commands" / "gen-gaps.md",
        REPO_ROOT / ".claude" / "commands" / "gen-iterate.md",
        REPO_ROOT / "CLAUDE.md",
        REPO_ROOT / "AGENTS.md",
        REPO_ROOT / "docs" / "README.md",
        TENANT_REGISTRY,
        VARIANT_DESIGN_ROOT / "fp" / "README.md",
        VARIANT_DESIGN_ROOT / "fp" / "INTENT.md",
        VARIANT_DESIGN_ROOT / "fp" / "edge-overrides" / "README.md",
    ]
    for path in expected_paths:
        assert path.is_file(), f"missing installed self-host surface {path}"


def test_live_requirement_files_have_family_metadata_and_declared_requirements() -> None:
    requirement_ids = _requirement_ids()
    assert requirement_ids, "no live requirement ids discovered"

    for path in _requirement_files():
        text = _read(path)
        assert _metadata_value(text, "Family"), f"{path.name} is missing **Family** metadata"
        assert _metadata_value(text, "Status"), f"{path.name} is missing **Status** metadata"
        file_requirement_ids = re.findall(r"^### (REQ-[A-Z0-9-]+)\b", text, re.MULTILINE)
        assert file_requirement_ids, f"{path.name} declares no requirement ids"


def test_design_surfaces_trace_to_live_requirement_and_intent_authority() -> None:
    intent_ids = _intent_ids()
    requirement_ids = _requirement_ids()
    assert intent_ids, "no live intent ids discovered"

    design_docs = [
        COMMON_DESIGN_ROOT / "README.md",
        *sorted((COMMON_DESIGN_ROOT / "adrs").glob("ADR-*.md")),
        VARIANT_DESIGN_ROOT / "README.md",
        VARIANT_DESIGN_ROOT / "module_decomp.md",
        *sorted((VARIANT_DESIGN_ROOT / "adrs").glob("ADR-*.md")),
    ]

    for path in design_docs:
        text = _read(path)
        authority = _metadata_value(text, "Authority")
        if authority:
            links = _resolve_links(authority, path)
            assert links, f"{path.name} has no resolvable authority link"
            for link in links:
                assert link.exists(), f"{path.name} links to missing authority surface {link}"

        implements = _metadata_value(text, "Implements")
        if implements:
            refs = _requirement_refs(implements)
            assert refs, f"{path.name} names no requirement refs in **Implements**"
            for ref in refs:
                assert _pattern_matches_requirement(ref, requirement_ids), (
                    f"{path.name} implements unknown requirement ref {ref}"
                )

        derives = _metadata_value(text, "Derives from")
        if derives:
            for ref in INTENT_REF_RE.findall(derives):
                assert ref in intent_ids, f"{path.name} derives from unknown intent id {ref}"
            for link in _resolve_links(derives, path):
                assert link.exists(), f"{path.name} links to missing derived authority {link}"


def test_module_schedule_source_files_resolve_to_variant_sources() -> None:
    module_files = sorted(MODULE_ROOT.glob("M*.yml"))
    assert module_files, "no module schedule surfaces discovered"

    for module_path in module_files:
        delivery_status = _top_level_scalar(module_path, "delivery_status")
        source_files = _top_level_source_files(module_path)
        if delivery_status == "deferred":
            assert not source_files, f"{module_path.name} is deferred but still declares source_files"
            continue
        assert source_files, f"{module_path.name} declares no source_files"
        for relative_path in source_files:
            resolved = VARIANT_ROOT / relative_path
            assert resolved.exists(), f"{module_path.name} source file is missing: {relative_path}"


def test_tenant_registry_declares_shared_and_active_variant_entries() -> None:
    text = _read(TENANT_REGISTRY)
    assert "build_tenants/common/" in text, "tenant registry does not declare the shared common root"
    assert "build_tenants/abiogenesis/" in text, "tenant registry does not declare the abiogenesis family"
    assert "build_tenants/abiogenesis/python/" in text, (
        "tenant registry does not declare the active abiogenesis/python variant"
    )


def test_common_qualification_surfaces_trace_to_live_requirement_authority() -> None:
    requirement_ids = _requirement_ids()
    qualification_docs = [
        COMMON_QUALIFICATION_ROOT / "README.md",
        COMMON_QUALIFICATION_ROOT / "qualification_surface_map.md",
    ]

    for path in qualification_docs:
        assert path.exists(), f"missing shared qualification surface {path}"

    map_text = _read(COMMON_QUALIFICATION_ROOT / "qualification_surface_map.md")
    for ref in _requirement_refs(map_text):
        assert _pattern_matches_requirement(ref, requirement_ids), (
            f"qualification_surface_map.md references unknown requirement ref {ref}"
        )
    for link in _resolve_links(map_text, COMMON_QUALIFICATION_ROOT / "qualification_surface_map.md"):
        assert link.exists(), f"qualification_surface_map.md links to missing authority surface {link}"


def test_python_test_surface_map_covers_current_executable_tests() -> None:
    requirement_ids = _requirement_ids()
    sections = _test_surface_map_sections()
    current_tests = sorted(path.name for path in (VARIANT_TEST_ROOT / "e2e").glob("test_*.py"))

    assert VARIANT_TEST_SURFACE_MAP.exists(), "missing tenant test surface map"
    assert sorted(sections) == current_tests, "test surface map does not cover the current executable test corpus"

    for filename, section in sections.items():
        req_refs = _requirement_refs(section)
        assert req_refs, f"{filename} has no requirement refs in test_surface_map.md"
        for ref in req_refs:
            assert _pattern_matches_requirement(ref, requirement_ids), (
                f"{filename} references unknown requirement ref {ref} in test_surface_map.md"
            )
        links = _resolve_links(section, VARIANT_TEST_SURFACE_MAP)
        assert links, f"{filename} has no resolvable design links in test_surface_map.md"
        for link in links:
            assert link.exists(), f"{filename} links to missing authority surface {link}"
