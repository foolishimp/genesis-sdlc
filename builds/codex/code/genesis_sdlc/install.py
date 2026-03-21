# Implements: REQ-F-BOOT-001
# Implements: REQ-F-BOOT-002
# Implements: REQ-F-BOOT-003
# Implements: REQ-F-BOOT-004
# Implements: REQ-F-BOOT-005
# Implements: REQ-F-BOOT-006
#!/usr/bin/env python3
"""
Codex installer for genesis_sdlc.

This build installs the abiogenesis Codex engine seed plus the genesis_sdlc
Codex workflow surface into a target project. It is the Codex-side bootstrap
step required to close the `abg.codex.bootstrap -> gsdlc.codex -> abg.codex`
chain.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.5.1"
SDLC_BOOTLOADER_VERSION = "1.2.0"

ENGINE_MODULES = [
    "__init__.py",
    "__main__.py",
    "bind.py",
    "commands.py",
    "core.py",
    "manifest.py",
    "schedule.py",
]
GTL_MODULES = ["__init__.py", "core.py"]
SEED_SPEC_FILES = [
    "gtl_spec/__init__.py",
    "gtl_spec/packages/__init__.py",
    "gtl_spec/packages/genesis_core.py",
    "gtl_spec/packages/abiogenesis.py",
    "gtl_spec/GTL_BOOTLOADER.md",
    "gtl_spec/GENESIS_BOOTLOADER.md",
]
COMMAND_NAMES = ["gen-start", "gen-gaps", "gen-status", "gen-iterate", "gen-review"]

_GTL_BOOTLOADER_START = "<!-- GTL_BOOTLOADER_START -->"
_GTL_BOOTLOADER_END = "<!-- GTL_BOOTLOADER_END -->"
_SDLC_BOOTLOADER_START = "<!-- SDLC_BOOTLOADER_START -->"
_SDLC_BOOTLOADER_END = "<!-- SDLC_BOOTLOADER_END -->"
_LEGACY_BOOTLOADER_START = "<!-- GENESIS_BOOTLOADER_START -->"
_LEGACY_BOOTLOADER_END = "<!-- GENESIS_BOOTLOADER_END -->"

_CLAUDE_MD_HEADER = """\
# CLAUDE.md — {project_name}

This project uses the **Genesis SDLC code builder** (abiogenesis Codex seed + genesis_sdlc Codex workflow).

## Quick start

```bash
PYTHONPATH=.genesis python -m genesis gaps --workspace .
PYTHONPATH=.genesis python -m genesis start --auto --workspace .
```

## Project structure

```text
{project_name}/
├── specification/                     ← axiomatic ontology
├── builds/codex/
│   ├── code/                          ← implementation source
│   ├── tests/                         ← test suite
│   ├── design/adrs/                   ← ADRs
│   └── .workspace/                    ← Codex-local manifests / iterations / scratch traces
├── .genesis/                          ← installed engine + workflow release
└── .ai-workspace/                     ← shared metabolic state
```

---

"""

_OPERATING_PROTOCOL = """\
## Operating protocol

Always route build/iterate/gap requests through the engine.

| Intent | Command |
|--------|---------|
| build / continue | `/gen-start --auto` |
| one step | `/gen-iterate` |
| inspect gaps | `/gen-gaps` |
| inspect workspace | `/gen-status` |
| explicit review | `/gen-review` |
"""

_GENERATED_WRAPPER_TEMPLATE = """\
# genesis_sdlc-generated — system-owned; rewritten on every redeploy.
from workflows.genesis_sdlc.standard.v{version_underscored}.spec import instantiate
package, worker = instantiate(slug="{slug}")
"""

_STARTER_INTENT_TEMPLATE = """\
# {project_name} — Intent

## INT-001 — Problem

Describe the problem, value proposition, and scope boundary for this project.
"""

_STARTER_REQUIREMENTS_TEMPLATE = """\
# {project_name} — Requirements

Define the normative REQ keys and their acceptance criteria here.
"""

_STARTER_FD_TEMPLATE = """\
# {project_name} — Feature Decomposition

Capture the feature vectors, dependency ordering, and MVP boundary here.
"""


def _source_root_from_package() -> Path | None:
    try:
        import genesis_sdlc

        pkg_path = Path(genesis_sdlc.__file__).resolve().parent
        for parent in [
            pkg_path.parent.parent,
            pkg_path.parent.parent.parent,
            pkg_path.parent.parent.parent.parent,
        ]:
            if (parent / "builds" / "codex" / "code" / "genesis_sdlc").is_dir():
                return parent
    except ImportError:
        return None
    return None


def _source_root_from_script() -> Path:
    return Path(__file__).resolve().parents[4]


def resolve_source(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit).resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"--source directory not found: {path}")
        return path
    return _source_root_from_package() or _source_root_from_script()


def _abiogenesis_code_root(source: Path) -> Path:
    candidate = source.parent / "abiogenesis" / "builds" / "codex" / "code"
    if not candidate.is_dir():
        raise FileNotFoundError(
            "Cannot find abiogenesis Codex seed at "
            f"{candidate}. Ensure abiogenesis is present as a sibling checkout."
        )
    return candidate.resolve()


def _sdlc_code_root(source: Path) -> Path:
    return source / "builds" / "codex" / "code" / "genesis_sdlc"


def _commands_source_root(source: Path) -> Path:
    return source / "builds" / "codex" / ".claude-plugin" / "plugins" / "genesis" / "commands"


def _copy_replace(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _source_hash(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _string_hash(text: str) -> str:
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _render_wrapper(slug: str) -> str:
    return _GENERATED_WRAPPER_TEMPLATE.format(
        version_underscored=VERSION.replace(".", "_"),
        slug=slug,
    )


def _sdlc_graph_source(source: Path) -> Path:
    return _sdlc_code_root(source) / "sdlc_graph.py"


def _bootloader_source(source: Path) -> Path:
    return _sdlc_code_root(source) / "SDLC_BOOTLOADER.md"


def _existing_pythonpath(genesis_yml: Path) -> list[str] | None:
    if not genesis_yml.exists():
        return None
    text = genesis_yml.read_text(encoding="utf-8")
    matches = re.findall(r"^\s+-\s+(.+)$", text, re.MULTILINE)
    return [match.strip() for match in matches] if matches else None


def install_engine_seed(abg_code: Path, target: Path) -> dict:
    result = {"engine": [], "gtl": [], "seed_spec": []}

    genesis_dir = target / ".genesis" / "genesis"
    gtl_dir = target / ".genesis" / "gtl"
    for dest in (genesis_dir, gtl_dir):
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

    for module in ENGINE_MODULES:
        src = abg_code / "genesis" / module
        _copy_replace(src, genesis_dir / module)
        result["engine"].append(module)

    for module in GTL_MODULES:
        src = abg_code / "gtl" / module
        _copy_replace(src, gtl_dir / module)
        result["gtl"].append(module)

    for rel in SEED_SPEC_FILES:
        src = abg_code / rel
        dst = target / ".genesis" / rel
        _copy_replace(src, dst)
        result["seed_spec"].append(rel)

    return result


def install_genesis_yml(target: Path, slug: str, *, platform: str = "codex") -> str:
    config_path = target / ".genesis" / "genesis.yml"
    pythonpaths = _existing_pythonpath(config_path) or [f"builds/{platform}/code"]
    lines = [
        "# Genesis project config — written by genesis_sdlc Codex installer",
        f"package: gtl_spec.packages.{slug}:package",
        f"worker:  gtl_spec.packages.{slug}:worker",
        "pythonpath:",
        *[f"  - {entry}" for entry in pythonpaths],
    ]
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return "installed"


def install_workflow_release(source: Path, target: Path) -> str:
    ver_dir = (
        target
        / ".genesis"
        / "workflows"
        / "genesis_sdlc"
        / "standard"
        / f"v{VERSION.replace('.', '_')}"
    )
    spec_file = ver_dir / "spec.py"
    if spec_file.exists():
        return "exists"

    src = _sdlc_graph_source(source)
    ver_dir.mkdir(parents=True, exist_ok=True)
    for init_dir in [
        target / ".genesis" / "workflows",
        target / ".genesis" / "workflows" / "genesis_sdlc",
        target / ".genesis" / "workflows" / "genesis_sdlc" / "standard",
        ver_dir,
    ]:
        (init_dir / "__init__.py").touch()
    shutil.copy2(src, spec_file)
    manifest = {
        "workflow": "genesis_sdlc.standard",
        "version": VERSION,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "spec_file": "spec.py",
    }
    (ver_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return "installed"


def install_active_workflow(target: Path) -> str:
    path = target / ".genesis" / "active-workflow.json"
    payload = {
        "workflow": "genesis_sdlc.standard",
        "version": VERSION,
        "spec_module": f"workflows.genesis_sdlc.standard.v{VERSION.replace('.', '_')}.spec",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return "installed"


def install_immutable_spec(source: Path, target: Path) -> str:
    dst = target / ".genesis" / "spec" / "genesis_sdlc.py"
    dst.parent.mkdir(parents=True, exist_ok=True)
    (dst.parent / "__init__.py").touch()
    shutil.copy2(_sdlc_graph_source(source), dst)
    return "installed"


def install_sdlc_starter_spec(target: Path, slug: str) -> str:
    wrapper_path = target / ".genesis" / "gtl_spec" / "packages" / f"{slug}.py"
    if wrapper_path.exists():
        existing = wrapper_path.read_text(encoding="utf-8")
        is_system_owned = (
            "genesis_sdlc-generated" in existing
            or "genesis_sdlc-stub" in existing
            or "spec→output" in existing
        )
        if not is_system_owned:
            return "already_customised"
    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_path.write_text(_render_wrapper(slug), encoding="utf-8")
    return "installed"


def install_workspace_territories(target: Path) -> None:
    shared_dirs = [
        ".ai-workspace/backlog",
        ".ai-workspace/comments/codex",
        ".ai-workspace/events",
        ".ai-workspace/features/active",
        ".ai-workspace/features/completed",
        ".ai-workspace/modules",
        ".ai-workspace/operating-standards",
        ".ai-workspace/reviews/pending",
        ".ai-workspace/reviews/proxy-log",
        ".ai-workspace/uat",
    ]
    private_dirs = [
        "builds/codex/code",
        "builds/codex/tests",
        "builds/codex/design/adrs",
        "builds/codex/.workspace/manifests",
        "builds/codex/.workspace/iterations",
        "builds/codex/.workspace/working_surfaces",
    ]
    for rel in [*shared_dirs, *private_dirs]:
        (target / rel).mkdir(parents=True, exist_ok=True)


def install_starter_specification(target: Path, project_name: str) -> list[str]:
    created: list[str] = []
    files = {
        "specification/INTENT.md": _STARTER_INTENT_TEMPLATE.format(project_name=project_name),
        "specification/requirements.md": _STARTER_REQUIREMENTS_TEMPLATE.format(project_name=project_name),
        "specification/feature_decomposition.md": _STARTER_FD_TEMPLATE.format(project_name=project_name),
    }
    for rel, content in files.items():
        path = target / rel
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(rel)
    return created


def install_commands(source: Path, target: Path) -> list[str]:
    src_root = _commands_source_root(source)
    if not src_root.is_dir():
        raise FileNotFoundError(f"Codex command sources not found at {src_root}")
    dest_root = target / ".claude" / "commands"
    dest_root.mkdir(parents=True, exist_ok=True)
    installed: list[str] = []
    for command in COMMAND_NAMES:
        src = src_root / f"{command}.md"
        dst = dest_root / f"{command}.md"
        shutil.copy2(src, dst)
        installed.append(command)
    stamp = {
        "version": VERSION,
        "installed": installed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    (dest_root / ".genesis-installed").write_text(json.dumps(stamp, indent=2), encoding="utf-8")
    return installed


def install_operating_standards(source: Path, target: Path) -> str:
    src_root = source / "specification" / "standards"
    if not src_root.is_dir():
        return "source_missing"
    dest_root = target / ".ai-workspace" / "operating-standards"
    dest_root.mkdir(parents=True, exist_ok=True)
    for src in sorted(src_root.glob("*.md")):
        shutil.copy2(src, dest_root / src.name)
    return "installed"


def _upsert_block(text: str, start: str, end: str, block: str) -> tuple[str, str]:
    if start in text and end in text:
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.DOTALL)
        return pattern.sub(block, text), "updated"
    if text.strip():
        return text.rstrip() + f"\n\n---\n\n{block}\n", "appended"
    return block + "\n", "created"


def install_claude_md(
    source: Path,
    target: Path,
    slug: str,
    *,
    project_name: str,
    abiogenesis_code: Path,
) -> str:
    gtl_bootloader = (abiogenesis_code / "gtl_spec" / "GTL_BOOTLOADER.md").read_text(encoding="utf-8")
    sdlc_bootloader = _bootloader_source(source).read_text(encoding="utf-8")
    gtl_block = f"{_GTL_BOOTLOADER_START}\n{gtl_bootloader}\n{_GTL_BOOTLOADER_END}"
    sdlc_block = (
        f"{_SDLC_BOOTLOADER_START}\n{_OPERATING_PROTOCOL}\n\n{sdlc_bootloader}\n{_SDLC_BOOTLOADER_END}"
    )

    claude_md = target / "CLAUDE.md"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")
    else:
        text = _CLAUDE_MD_HEADER.format(project_name=project_name)

    if _LEGACY_BOOTLOADER_START in text and _LEGACY_BOOTLOADER_END in text:
        pattern = re.compile(
            re.escape(_LEGACY_BOOTLOADER_START)
            + r".*?"
            + re.escape(_LEGACY_BOOTLOADER_END),
            re.DOTALL,
        )
        text = pattern.sub("", text)

    text, gtl_status = _upsert_block(text, _GTL_BOOTLOADER_START, _GTL_BOOTLOADER_END, gtl_block)
    text, sdlc_status = _upsert_block(text, _SDLC_BOOTLOADER_START, _SDLC_BOOTLOADER_END, sdlc_block)

    if _GTL_BOOTLOADER_START in text and _SDLC_BOOTLOADER_START in text:
        gtl_idx = text.index(_GTL_BOOTLOADER_START)
        sdlc_idx = text.index(_SDLC_BOOTLOADER_START)
        if gtl_idx > sdlc_idx:
            gtl_pattern = re.compile(
                re.escape(_GTL_BOOTLOADER_START) + r".*?" + re.escape(_GTL_BOOTLOADER_END),
                re.DOTALL,
            )
            sdlc_pattern = re.compile(
                re.escape(_SDLC_BOOTLOADER_START) + r".*?" + re.escape(_SDLC_BOOTLOADER_END),
                re.DOTALL,
            )
            gtl_match = gtl_pattern.search(text)
            sdlc_match = sdlc_pattern.search(text)
            if gtl_match and sdlc_match:
                stripped = gtl_pattern.sub("", text)
                stripped = sdlc_pattern.sub("", stripped).rstrip()
                text = stripped + f"\n\n---\n\n{gtl_block}\n\n---\n\n{sdlc_block}\n"

    claude_md.write_text(text, encoding="utf-8")
    if not claude_md.exists():
        return "created"
    if "updated" in {gtl_status, sdlc_status}:
        return "updated"
    if "appended" in {gtl_status, sdlc_status}:
        return "appended"
    return "created"


def _emit_event(target: Path, event_type: str, data: dict, *, event_time: str | None = None) -> None:
    events_dir = target / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    record = {
        "event_type": event_type,
        "event_time": event_time or datetime.now(timezone.utc).isoformat(),
        "data": data,
    }
    with (events_dir / "events.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record) + "\n")


def install(
    target: Path,
    *,
    source: Path | None = None,
    slug: str = "project_package",
    verify_only: bool = False,
    audit_only: bool = False,
) -> dict:
    target = target.resolve()
    src = resolve_source(str(source) if source else None)
    project_name = target.name
    abg_code = _abiogenesis_code_root(src)

    result: dict = {
        "version": VERSION,
        "target": str(target),
        "source": str(src),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": None,
        "workflow_release": None,
        "active_workflow": None,
        "immutable_spec": None,
        "commands": [],
        "claude_md": None,
        "sdlc_starter_spec": None,
        "operating_standards": None,
        "seed_specification": [],
        "errors": [],
    }

    if verify_only:
        return _verify(target, result)
    if audit_only:
        return _audit(target, result, src, slug, abg_code)

    try:
        seed = install_engine_seed(abg_code, target)
        result["engine"] = f"installed:{len(seed['engine'])}"
        result["seed_spec"] = seed["seed_spec"]
    except Exception as exc:
        result["errors"].append(f"engine: {exc}")

    try:
        result["genesis_yml"] = install_genesis_yml(target, slug)
    except Exception as exc:
        result["errors"].append(f"genesis_yml: {exc}")

    try:
        result["workflow_release"] = install_workflow_release(src, target)
    except Exception as exc:
        result["errors"].append(f"workflow_release: {exc}")

    try:
        result["active_workflow"] = install_active_workflow(target)
    except Exception as exc:
        result["errors"].append(f"active_workflow: {exc}")

    try:
        result["immutable_spec"] = install_immutable_spec(src, target)
    except Exception as exc:
        result["errors"].append(f"immutable_spec: {exc}")

    try:
        result["sdlc_starter_spec"] = install_sdlc_starter_spec(target, slug)
    except Exception as exc:
        result["errors"].append(f"sdlc_starter_spec: {exc}")

    try:
        install_workspace_territories(target)
    except Exception as exc:
        result["errors"].append(f"workspace: {exc}")

    try:
        result["seed_specification"] = install_starter_specification(target, project_name)
    except Exception as exc:
        result["errors"].append(f"specification: {exc}")

    try:
        result["commands"] = install_commands(src, target)
    except Exception as exc:
        result["errors"].append(f"commands: {exc}")

    try:
        result["claude_md"] = install_claude_md(
            src,
            target,
            slug,
            project_name=project_name,
            abiogenesis_code=abg_code,
        )
    except Exception as exc:
        result["errors"].append(f"claude_md: {exc}")

    try:
        result["operating_standards"] = install_operating_standards(src, target)
    except Exception as exc:
        result["errors"].append(f"operating_standards: {exc}")

    _emit_event(
        target,
        "workflow_activated",
        {
            "workflow": "genesis_sdlc.standard",
            "version": VERSION,
            "target": str(target),
        },
    )
    _emit_event(
        target,
        "genesis_sdlc_installed",
        {
            "version": VERSION,
            "target": str(target),
            "claude_md": result.get("claude_md"),
            "commands_installed": len(result.get("commands", [])),
        },
        event_time=result["timestamp"],
    )

    result["status"] = "installed" if not result["errors"] else "partial"
    return result


def _verify(target: Path, result: dict) -> dict:
    ver_dir = (
        target
        / ".genesis"
        / "workflows"
        / "genesis_sdlc"
        / "standard"
        / f"v{VERSION.replace('.', '_')}"
    )
    claude_md = target / "CLAUDE.md"
    source = resolve_source(None)
    source_standards = source / "specification" / "standards"
    installed_standards = target / ".ai-workspace" / "operating-standards"
    source_files = {path.name for path in source_standards.glob("*.md")} if source_standards.is_dir() else set()
    installed_files = {path.name for path in installed_standards.glob("*.md")} if installed_standards.is_dir() else set()

    checks = {
        "engine": (target / ".genesis" / "genesis" / "__main__.py").exists(),
        "gtl": (target / ".genesis" / "gtl" / "core.py").exists(),
        "genesis_yml": (target / ".genesis" / "genesis.yml").exists(),
        "workflow_release": (ver_dir / "spec.py").exists(),
        "active_workflow": (target / ".genesis" / "active-workflow.json").exists(),
        "immutable_spec": (target / ".genesis" / "spec" / "genesis_sdlc.py").exists(),
        "gtl_spec": (target / ".genesis" / "gtl_spec" / "packages").is_dir(),
        "builds_code": (target / "builds" / "codex" / "code").is_dir(),
        "builds_tests": (target / "builds" / "codex" / "tests").is_dir(),
        "private_workspace": (target / "builds" / "codex" / ".workspace").is_dir(),
        "commands": (target / ".claude" / "commands" / "gen-start.md").exists(),
        "claude_md": claude_md.exists(),
        "gtl_bootloader": (_GTL_BOOTLOADER_START in claude_md.read_text(encoding="utf-8")) if claude_md.exists() else False,
        "sdlc_bootloader": (_SDLC_BOOTLOADER_START in claude_md.read_text(encoding="utf-8")) if claude_md.exists() else False,
        "operating_standards": bool(source_files) and source_files.issubset(installed_files),
        "intent_seed": (target / "specification" / "INTENT.md").exists(),
    }
    result["checks"] = checks
    result["missing"] = [name for name, ok in checks.items() if not ok]
    result["status"] = "ok" if not result["missing"] else "incomplete"
    return result


def _audit(target: Path, result: dict, source: Path, slug: str, abg_code: Path) -> dict:
    findings: list[dict] = []
    ver_tag = f"v{VERSION.replace('.', '_')}"

    def finding(component: str, status: str, detail: str = "") -> None:
        payload = {"component": component, "status": status}
        if detail:
            payload["detail"] = detail
        findings.append(payload)

    installed_spec = (
        target / ".genesis" / "workflows" / "genesis_sdlc" / "standard" / ver_tag / "spec.py"
    )
    source_spec = _sdlc_graph_source(source)
    if not installed_spec.exists():
        finding("workflow_release", "missing")
    elif _source_hash(installed_spec) != _source_hash(source_spec):
        finding("workflow_release", "drifted", "Installed versioned spec differs from source")
    else:
        finding("workflow_release", "ok")

    active_path = target / ".genesis" / "active-workflow.json"
    if not active_path.exists():
        finding("active_workflow", "missing")
    else:
        active = json.loads(active_path.read_text(encoding="utf-8"))
        expected_module = f"workflows.genesis_sdlc.standard.{ver_tag}.spec"
        if active.get("version") != VERSION or active.get("spec_module") != expected_module:
            finding("active_workflow", "drifted", "active-workflow.json differs from expected release pointer")
        else:
            finding("active_workflow", "ok")

    commands_root = target / ".claude" / "commands"
    src_commands = _commands_source_root(source)
    for command in COMMAND_NAMES:
        src = src_commands / f"{command}.md"
        dst = commands_root / f"{command}.md"
        if not dst.exists():
            finding(f"command:{command}", "missing")
        elif _source_hash(src) != _source_hash(dst):
            finding(f"command:{command}", "drifted", "Installed command differs from source")
        else:
            finding(f"command:{command}", "ok")

    stamp = commands_root / ".genesis-installed"
    if not stamp.exists():
        finding("commands_stamp", "missing")
    else:
        stamp_data = json.loads(stamp.read_text(encoding="utf-8"))
        finding("commands_stamp", "ok" if stamp_data.get("version") == VERSION else "drifted")

    standards_source = source / "specification" / "standards"
    standards_target = target / ".ai-workspace" / "operating-standards"
    for src in sorted(standards_source.glob("*.md")):
        dst = standards_target / src.name
        if not dst.exists():
            finding(f"standard:{src.name}", "missing")
        elif _source_hash(src) != _source_hash(dst):
            finding(f"standard:{src.name}", "drifted")
        else:
            finding(f"standard:{src.name}", "ok")

    claude_md = target / "CLAUDE.md"
    if not claude_md.exists():
        finding("claude_md", "missing")
    else:
        text = claude_md.read_text(encoding="utf-8")
        gtl_source = (abg_code / "gtl_spec" / "GTL_BOOTLOADER.md").read_text(encoding="utf-8")
        sdlc_source = _bootloader_source(source).read_text(encoding="utf-8")
        expected_gtl = f"{_GTL_BOOTLOADER_START}\n{gtl_source}\n{_GTL_BOOTLOADER_END}"
        expected_sdlc = f"{_SDLC_BOOTLOADER_START}\n{_OPERATING_PROTOCOL}\n\n{sdlc_source}\n{_SDLC_BOOTLOADER_END}"
        gtl_match = re.search(
            re.escape(_GTL_BOOTLOADER_START) + r".*?" + re.escape(_GTL_BOOTLOADER_END),
            text,
            re.DOTALL,
        )
        sdlc_match = re.search(
            re.escape(_SDLC_BOOTLOADER_START) + r".*?" + re.escape(_SDLC_BOOTLOADER_END),
            text,
            re.DOTALL,
        )
        if not gtl_match:
            finding("gtl_bootloader_content", "missing")
        elif _string_hash(gtl_match.group(0)) != _string_hash(expected_gtl):
            finding("gtl_bootloader_content", "drifted")
        else:
            finding("gtl_bootloader_content", "ok")
        if not sdlc_match:
            finding("sdlc_bootloader_content", "missing")
        elif _string_hash(sdlc_match.group(0)) != _string_hash(expected_sdlc):
            finding("sdlc_bootloader_content", "drifted")
        else:
            finding("sdlc_bootloader_content", "ok")
        if _GTL_BOOTLOADER_START in text and _SDLC_BOOTLOADER_START in text:
            finding(
                "bootloader_order",
                "ok" if text.index(_GTL_BOOTLOADER_START) < text.index(_SDLC_BOOTLOADER_START) else "drifted",
            )

    genesis_yml = target / ".genesis" / "genesis.yml"
    if not genesis_yml.exists():
        finding("genesis_yml", "missing")
    else:
        text = genesis_yml.read_text(encoding="utf-8")
        pkg_match = re.search(r"^package:\s+(\S+)", text, re.MULTILINE)
        worker_match = re.search(r"^worker:\s+(\S+)", text, re.MULTILINE)
        if not pkg_match or not worker_match:
            finding("genesis_yml_contract", "drifted")
        else:
            old_path = sys.path[:]
            try:
                sys.path.insert(0, str(target / ".genesis"))
                module_name, _, attr = pkg_match.group(1).partition(":")
                module = __import__(module_name, fromlist=[attr])
                finding("genesis_yml_package", "ok" if hasattr(module, attr) else "drifted")
            except Exception:
                finding("genesis_yml_package", "drifted")
            finally:
                sys.path[:] = old_path

    wrapper = target / ".genesis" / "gtl_spec" / "packages" / f"{slug}.py"
    if not wrapper.exists():
        finding("layer3_wrapper", "missing")
    elif wrapper.read_text(encoding="utf-8").strip() != _render_wrapper(slug).strip():
        finding("layer3_wrapper", "drifted")
    else:
        finding("layer3_wrapper", "ok")

    manifest = target / ".genesis" / "workflows" / "genesis_sdlc" / "standard" / ver_tag / "manifest.json"
    if not manifest.exists():
        finding("manifest", "missing")
    else:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        finding("manifest", "ok" if data.get("version") == VERSION else "drifted")

    shim = target / ".genesis" / "spec" / "genesis_sdlc.py"
    if not shim.exists():
        finding("immutable_spec_shim", "missing")
    elif _source_hash(shim) != _source_hash(source_spec):
        finding("immutable_spec_shim", "drifted")
    else:
        finding("immutable_spec_shim", "ok")

    drifted = [item["component"] for item in findings if item["status"] == "drifted"]
    missing = [item["component"] for item in findings if item["status"] == "missing"]
    result["audit"] = {
        "version": VERSION,
        "sdlc_bootloader_version": SDLC_BOOTLOADER_VERSION,
        "findings": findings,
        "summary": {
            "total": len(findings),
            "ok": sum(1 for item in findings if item["status"] == "ok"),
            "drifted": len(drifted),
            "missing": len(missing),
        },
    }
    if drifted:
        result["audit"]["drifted"] = drifted
    if missing:
        result["audit"]["missing"] = missing
    result["status"] = "ok" if not drifted and not missing else "drift_detected"
    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="genesis_sdlc.install",
        description=f"genesis_sdlc Codex installer v{VERSION}",
    )
    parser.add_argument("--target", default=".", help="Target project directory")
    parser.add_argument("--source", default=None, help="genesis_sdlc source root")
    parser.add_argument("--project-slug", default="project_package", help="Generated wrapper slug")
    parser.add_argument("--verify", action="store_true", help="Verify install only")
    parser.add_argument("--audit", action="store_true", help="Audit install content")
    args = parser.parse_args()

    slug = args.project_slug
    if not slug.isidentifier():
        print(f"ERROR: invalid --project-slug: {slug!r}", file=sys.stderr)
        sys.exit(1)

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"ERROR: target directory does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    result = install(
        target,
        source=Path(args.source).resolve() if args.source else None,
        slug=slug,
        verify_only=args.verify,
        audit_only=args.audit,
    )
    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") in {"installed", "ok"} else 1)


if __name__ == "__main__":
    main()
