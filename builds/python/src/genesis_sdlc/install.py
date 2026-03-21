# Implements: REQ-F-BOOT-001
# Implements: REQ-F-BOOT-002
# Implements: REQ-F-BOOT-003
# Implements: REQ-F-BOOT-004
# Implements: REQ-F-BOOT-005
# Implements: REQ-F-BOOT-006
# Implements: REQ-F-TERRITORY-001
# Implements: REQ-F-TERRITORY-002
#!/usr/bin/env python3
"""
genesis_sdlc installer — deploys the full SDLC code builder into a target project.

After installation a cold Claude Code session in the target project is immediately
operational: it knows the methodology, can run /gen-start, and understands the
project structure.

Usage:
    python -m genesis_sdlc.install --target /path/to/project
    python -m genesis_sdlc.install --target .
    python -m genesis_sdlc.install --target . --platform java
    python -m genesis_sdlc.install --target . --verify
    python -m genesis_sdlc.install --target . --audit
    python -m genesis_sdlc.install --target . --migrate-full-copy

Territory model
───────────────
Kernel     .genesis/                                              ABG engine + GTL — owned by abiogenesis
Release    .gsdlc/release/workflows/genesis_sdlc/standard/vX_Y_Z/  immutable versioned release — written once
Wrapper    .gsdlc/release/gtl_spec/packages/<slug>.py               system-owned generated wrapper — replaced on redeploy
Config     .gsdlc/release/active-workflow.json                      mutable active baseline pointer

The generated wrapper calls instantiate(slug) from the versioned release. Redeploy updates
active-workflow.json and rewrites the wrapper; versioned releases are never modified.
The gsdlc installer owns .gsdlc/release/; abg installer owns .genesis/.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.0.0b1"
SDLC_BOOTLOADER_VERSION = "1.1.0"  # matches **Version**: in SDLC_BOOTLOADER.md

# Commands inherited from the abiogenesis engine plugin.
ABIOGENESIS_COMMANDS = [
    "gen-start",
    "gen-gaps",
    "gen-status",
]

# Commands owned by genesis_sdlc — SDLC additions on top of the engine.
GENESIS_SDLC_COMMANDS = [
    "gen-iterate",
    "gen-review",
]

# CLAUDE.md markers for idempotent SDLC bootloader injection.
# The GTL bootloader uses its own markers (<!-- GTL_BOOTLOADER_START/END -->)
# and is appended by the abiogenesis installer — not by genesis_sdlc.
_BOOTLOADER_START = "<!-- SDLC_BOOTLOADER_START -->"
_BOOTLOADER_END = "<!-- SDLC_BOOTLOADER_END -->"

# Legacy markers from the monolithic bootloader — used for migration only.
_LEGACY_BOOTLOADER_START = "<!-- GENESIS_BOOTLOADER_START -->"
_LEGACY_BOOTLOADER_END = "<!-- GENESIS_BOOTLOADER_END -->"

_OPERATING_PROTOCOL = """\
## Operating protocol

**Always route user intent through commands — never do work directly.**
When the user asks to build, fix, or iterate anything, that is `/gen-start` or
`/gen-iterate`. Direct edits bypass the F_D evaluation chain and nothing is traced.

| Intent | Command |
|--------|---------|
| "go" / "next" / "build X" / "fix Y" | `/gen-start --auto --human-proxy` |
| "one step" / "iterate edge E" | `/gen-iterate --feature F --edge E` |
| "what's broken" / "gaps" / "coverage" | `/gen-gaps` |
| "status" / "where am I" | `/gen-status` |
| "review" / "approve" | `/gen-review --feature F` |

"""

_CLAUDE_MD_HEADER = """\
# CLAUDE.md — {project_name}

This project uses the **Genesis SDLC code builder** (abiogenesis + genesis_sdlc).

## Quick start

```bash
# Check project state and gaps
PYTHONPATH=.genesis python -m genesis gaps --workspace .

# Start the methodology engine (auto-loop)
/gen-start --auto
```

## Project structure

```
{project_name}/
├── specification/                     ← axiomatic ontology (intent, requirements, standards)
├── builds/{platform}/
│   ├── src/                           ← implementation source
│   ├── tests/                         ← test suite
│   └── design/adrs/                   ← architecture decision records
├── .genesis/                          ← ABG kernel (immutable, owned by abiogenesis)
│   ├── genesis/                       ← abiogenesis engine
│   ├── gtl/                           ← GTL type system
│   └── genesis.yml                    ← project config (package/worker/pythonpath)
├── .gsdlc/release/                    ← gsdlc methodology release (immutable between releases)
│   ├── workflows/genesis_sdlc/        ← versioned release snapshots
│   └── gtl_spec/packages/{slug}.py    ← generated workflow wrapper (system-owned)
└── .ai-workspace/                     ← runtime state (events, features, reviews)
```

## Invocation

```bash
PYTHONPATH=.genesis python -m genesis start --auto --workspace .
PYTHONPATH=.genesis python -m genesis gaps  --workspace .
```

## Slash commands

| Command | What it does |
|---------|-------------|
| `/gen-start [--auto] [--human-proxy]` | State machine — select next edge, iterate, loop |
| `/gen-iterate [--feature F] [--edge E]` | One F_D→F_P→F_H cycle on a specific edge |
| `/gen-gaps [--feature F]` | Convergence state — delta per edge |
| `/gen-review --feature F` | Explicit F_H gate — present candidate for human approval |
| `/gen-status [--feature F]` | Workspace status — events, features, edge state |

---

"""


def _source_root_from_package() -> Path | None:
    """Locate genesis_sdlc source root from the installed package location."""
    try:
        import genesis_sdlc
        pkg_path = Path(genesis_sdlc.__file__).resolve().parent
        for parent in [
            pkg_path.parent.parent,
            pkg_path.parent.parent.parent,
            pkg_path.parent.parent.parent.parent,
        ]:
            if (parent / ".genesis" / "gtl_spec").exists() and (parent / ".genesis").exists():
                return parent
    except ImportError:
        pass
    return None


def _source_root_from_script() -> Path:
    """install.py is at: <root>/builds/python/src/genesis_sdlc/install.py → parents[4]"""
    return Path(__file__).resolve().parents[4]


def resolve_source(explicit: str | None) -> Path:
    if explicit:
        p = Path(explicit).resolve()
        if not p.is_dir():
            raise FileNotFoundError(f"--source directory not found: {p}")
        return p
    from_pkg = _source_root_from_package()
    if from_pkg:
        return from_pkg
    return _source_root_from_script()


def _run_abiogenesis_installer(source: Path, target: Path, slug: str, platform: str) -> dict:
    candidates = [
        source.parent / "abiogenesis" / "builds" / "claude_code" / "code" / "gen-install.py",
    ]
    installer = next((c.resolve() for c in candidates if c.resolve().exists()), None)

    if not installer:
        raise FileNotFoundError(
            "Cannot find abiogenesis gen-install.py. "
            "Pass --source /path/to/genesis_sdlc or ensure abiogenesis is a sibling directory."
        )

    result = subprocess.run(
        [sys.executable, str(installer),
         "--target", str(target),
         "--project-slug", slug,
         "--platform", platform],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gen-install.py failed:\n{result.stderr}")
    return json.loads(result.stdout)


def _sdlc_graph_source(source: Path) -> Path | None:
    """Locate sdlc_graph.py from source root or installed package."""
    candidates = [
        source / "builds" / "python" / "src" / "genesis_sdlc" / "sdlc_graph.py",
    ]
    for c in candidates:
        if c.exists():
            return c
    try:
        import genesis_sdlc
        p = Path(genesis_sdlc.__file__).parent / "sdlc_graph.py"
        if p.exists():
            return p
    except ImportError:
        pass
    return None


def install_workflow_release(source: Path, target: Path) -> str:
    """
    Install the versioned immutable workflow release into:
        .gsdlc/release/workflows/genesis_sdlc/standard/v{VERSION}/spec.py

    # Implements: REQ-F-TERRITORY-001

    This directory is written once and never overwritten — it is the immutable release
    artifact. Reinstalling a newer version adds a new versioned directory alongside
    existing ones; old releases remain on disk for provenance.
    """
    ver_dir = (
        target / ".gsdlc" / "release" / "workflows" / "genesis_sdlc"
        / "standard"
        / f"v{VERSION.replace('.', '_')}"
    )
    spec_file = ver_dir / "spec.py"

    if spec_file.exists():
        return "exists"  # immutable — never overwrite

    src = _sdlc_graph_source(source)
    if src is None:
        return "source_missing"

    ver_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py files so the versioned package is importable
    for init_dir in [
        target / ".gsdlc" / "release" / "workflows",
        target / ".gsdlc" / "release" / "workflows" / "genesis_sdlc",
        target / ".gsdlc" / "release" / "workflows" / "genesis_sdlc" / "standard",
        ver_dir,
    ]:
        init_py = init_dir / "__init__.py"
        if not init_py.exists():
            init_py.touch()

    shutil.copy2(src, spec_file)

    manifest = {
        "workflow": "genesis_sdlc.standard",
        "version": VERSION,
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "spec_file": "spec.py",
    }
    (ver_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return "installed"


def install_active_workflow(target: Path) -> tuple[str, bool, str | None]:
    """
    Write/update .gsdlc/release/active-workflow.json — the mutable active baseline pointer.

    # Implements: REQ-F-TERRITORY-001

    Returns (status, needs_migration, previous_version).

    needs_migration is True when upgrading from the old "genesis_sdlc" workflow name to
    "genesis_sdlc.standard" — the provenance migration runs once on this transition.
    """
    release_dir = target / ".gsdlc" / "release"
    release_dir.mkdir(parents=True, exist_ok=True)
    active_path = release_dir / "active-workflow.json"

    # Also check old location for migration detection
    legacy_active_path = target / ".genesis" / "active-workflow.json"

    needs_migration = False
    previous_version: str | None = None
    # Check new location first, then legacy .genesis/ location
    for check_path in [active_path, legacy_active_path]:
        if check_path.exists():
            try:
                old = json.loads(check_path.read_text(encoding="utf-8"))
                previous_version = old.get("version")
                if old.get("workflow") != "genesis_sdlc.standard":
                    needs_migration = True
                if check_path == legacy_active_path:
                    needs_migration = True  # migrating from old territory
            except Exception:
                pass
            break
    else:
        # No active-workflow.json in either location — check event stream.
        events_file = target / ".ai-workspace" / "events" / "events.jsonl"
        if events_file.exists():
            try:
                with events_file.open(encoding="utf-8") as _f:
                    for _line in _f:
                        _line = _line.strip()
                        if not _line:
                            continue
                        try:
                            _ev = json.loads(_line)
                        except Exception:
                            continue
                        if _ev.get("event_type") == "genesis_sdlc_installed":
                            previous_version = _ev.get("data", {}).get("version")
                            needs_migration = True
            except Exception:
                pass

    data = {
        "workflow": "genesis_sdlc.standard",
        "version": VERSION,
        "spec_module": f"workflows.genesis_sdlc.standard.v{VERSION.replace('.', '_')}.spec",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    active_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return "installed", needs_migration, previous_version


def install_immutable_spec(source: Path, target: Path) -> str:
    """
    Install sdlc_graph.py into .gsdlc/release/spec/genesis_sdlc.py (backwards compat shim).

    # Implements: REQ-F-TERRITORY-001

    This path is kept so that user-owned local specs written before the territory model
    (which import from spec.genesis_sdlc) continue to work after reinstall. New generated
    wrappers import from the versioned release path instead.
    """
    spec_dir = target / ".gsdlc" / "release" / "spec"
    spec_dir.mkdir(parents=True, exist_ok=True)
    init_py = spec_dir / "__init__.py"
    if not init_py.exists():
        init_py.touch()

    src = _sdlc_graph_source(source)
    if src is None:
        return "source_missing"

    shutil.copy2(src, spec_dir / "genesis_sdlc.py")
    return "installed"


# ── Generated wrapper template (Layer 3 — system-owned) ───────────────────────
#
# This file is always rewritten on redeploy as long as the genesis_sdlc-generated
# marker is present. Two lines: import instantiate from the versioned release,
# then call it with the project slug. All customisation lives in sdlc_graph.instantiate.

_GENERATED_WRAPPER_TEMPLATE = '''\
# genesis_sdlc-generated — system-owned; rewritten on every redeploy.
# Implements: REQ-F-CUSTODY-002
import re
from pathlib import Path

from workflows.genesis_sdlc.standard.v{VERSION_UNDERSCORED}.spec import instantiate


def _load_reqs():
    """Parse REQ-* keys from specification/requirements.md headers."""
    req_file = Path("specification/requirements.md")
    if not req_file.exists():
        return []
    reqs = []
    for line in req_file.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^### (REQ-[A-Z0-9][-A-Z0-9]*)", line)
        if m:
            reqs.append(m.group(1))
    return reqs


package, worker = instantiate(slug="{slug}", requirements=_load_reqs())
'''


def _render_wrapper(slug: str) -> str:
    """Render the generated wrapper template for a given slug."""
    return (
        _GENERATED_WRAPPER_TEMPLATE
        .replace("{VERSION_UNDERSCORED}", VERSION.replace(".", "_"))
        .replace("{slug}", slug)
    )


def install_sdlc_starter_spec(source: Path, target: Path, slug: str,
                               platform: str = "python") -> str | None:
    """
    Write the generated wrapper into .gsdlc/release/gtl_spec/packages/{slug}.py.

    # Implements: REQ-F-TERRITORY-001

    The wrapper is rewritten whenever it carries an explicit system-ownership marker:
      - genesis_sdlc-generated  (new model — always replaced)
      - genesis_sdlc-stub       (old thin-wrapper — upgraded to new model)
      - spec→output             (abiogenesis stub — replaced by genesis_sdlc)

    Any other content is treated as user-owned and not touched. Legacy full-copy specs
    from pre-0.2.0 installs fall into this category; use --migrate-full-copy to opt in.
    """
    wrapper_dir = target / ".gsdlc" / "release" / "gtl_spec" / "packages"
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    wrapper_path = wrapper_dir / f"{slug}.py"

    # Also check legacy .genesis/ location for migration
    legacy_wrapper = target / ".genesis" / "gtl_spec" / "packages" / f"{slug}.py"

    if wrapper_path.exists():
        existing = wrapper_path.read_text(encoding="utf-8")
        is_system_owned = (
            "genesis_sdlc-generated" in existing
            or "genesis_sdlc-stub" in existing
            or "spec→output" in existing
        )
        if not is_system_owned:
            return "already_customised"
    elif legacy_wrapper.exists():
        # Migrating from old territory — treat as writable
        pass
    else:
        # Fresh install — wrapper doesn't exist anywhere yet, create it
        pass

    # Create __init__.py for the gtl_spec.packages namespace
    for init_dir in [
        target / ".gsdlc" / "release" / "gtl_spec",
        wrapper_dir,
    ]:
        init_py = init_dir / "__init__.py"
        if not init_py.exists():
            init_py.touch()

    wrapper_path.write_text(_render_wrapper(slug), encoding="utf-8")
    return "installed"


_REQUIREMENTS_SCAFFOLD = """\
# Project Requirements

Define your project-specific requirements here. Each `### REQ-*` header
is parsed by the genesis engine as a requirement key for coverage tracking.

---

## Example (REQ-F-EXAMPLE-*)

### REQ-F-EXAMPLE-001 — Replace with your first requirement

Describe what the system must do.

**Acceptance Criteria**:
- AC-1: Measurable criterion
"""


def _scaffold_requirements_md(target: Path) -> str:
    """Create specification/requirements.md if absent.  # Implements: REQ-F-CUSTODY-003"""
    spec_dir = target / "specification"
    req_file = spec_dir / "requirements.md"
    if req_file.exists():
        return "already_exists"
    spec_dir.mkdir(parents=True, exist_ok=True)
    req_file.write_text(_REQUIREMENTS_SCAFFOLD, encoding="utf-8")
    return "scaffolded"


def migrate_full_copy(target: Path, slug: str) -> dict:
    """
    Explicit migration for legacy full-copy local specs (pre-0.2.0 installs).

    Safe content heuristics cannot reliably distinguish a pristine old copy from a
    user-edited one, so migration is opt-in via --migrate-full-copy. This command:
      1. Moves {slug}.py → {slug}_legacy_{timestamp}.py
      2. Writes the new generated wrapper to {slug}.py
      3. Creates {slug}_local.py if absent
      4. Returns a report of what was moved and what must be ported manually.
    """
    wrapper_path = target / ".gsdlc" / "release" / "gtl_spec" / "packages" / f"{slug}.py"
    # Also check legacy location
    legacy_location = target / ".genesis" / "gtl_spec" / "packages" / f"{slug}.py"
    source_path = wrapper_path if wrapper_path.exists() else legacy_location
    if not source_path.exists():
        return {"status": "no_spec_found"}

    existing = source_path.read_text(encoding="utf-8")

    if "genesis_sdlc-generated" in existing:
        return {"status": "already_migrated", "message": "Spec is already the generated wrapper."}
    if "spec→output" in existing:
        return {"status": "abiogenesis_stub", "message": "Use regular install to replace this stub."}
    if "genesis_sdlc-stub" in existing:
        return {"status": "already_migrated", "message": "Spec is the old thin-wrapper stub; regular install will upgrade it."}

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    backup_dir = target / ".gsdlc" / "release" / "gtl_spec" / "packages"
    backup_dir.mkdir(parents=True, exist_ok=True)
    legacy_path = backup_dir / f"{slug}_legacy_{ts}.py"
    shutil.move(str(source_path), str(legacy_path))

    wrapper_path.parent.mkdir(parents=True, exist_ok=True)
    wrapper_path.write_text(_render_wrapper(slug), encoding="utf-8")

    return {
        "status": "migrated",
        "legacy_path": str(legacy_path),
        "message": (
            f"Legacy spec moved to {legacy_path.name}. "
            f"Review it and port any customisations to the project spec directly."
        ),
    }


def install_commands(source: Path, target: Path) -> list[str]:
    abiogenesis_src = (
        source.parent / "abiogenesis" / "builds" / "claude_code"
        / ".claude-plugin" / "plugins" / "genesis" / "commands"
    ).resolve()
    genesis_sdlc_src = (
        source / "builds" / "claude_code" / ".claude-plugin" / "plugins" / "genesis" / "commands"
    ).resolve()

    if not abiogenesis_src.exists():
        raise FileNotFoundError(
            f"abiogenesis commands not found at {abiogenesis_src}. "
            "Ensure abiogenesis is a sibling directory of genesis_sdlc."
        )
    if not genesis_sdlc_src.exists():
        raise FileNotFoundError(
            f"genesis_sdlc commands not found at {genesis_sdlc_src}."
        )

    commands_dir = target / ".claude" / "commands"
    commands_dir.mkdir(parents=True, exist_ok=True)

    current = {f"{cmd}.md" for cmd in ABIOGENESIS_COMMANDS + GENESIS_SDLC_COMMANDS}
    for stale in commands_dir.glob("gen-*.md"):
        if stale.name not in current:
            stale.unlink()

    installed = []
    for cmd in ABIOGENESIS_COMMANDS:
        src = abiogenesis_src / f"{cmd}.md"
        if src.exists():
            shutil.copy2(src, commands_dir / f"{cmd}.md")
            installed.append(cmd)

    for cmd in GENESIS_SDLC_COMMANDS:
        src = genesis_sdlc_src / f"{cmd}.md"
        if src.exists():
            shutil.copy2(src, commands_dir / f"{cmd}.md")
            installed.append(cmd)

    stamp = commands_dir / ".genesis-installed"
    stamp.write_text(
        json.dumps({"version": VERSION, "installed": installed,
                    "timestamp": datetime.now(timezone.utc).isoformat()}, indent=2)
    )
    return installed


def _sdlc_bootloader_source(source: Path) -> Path | None:
    """Locate SDLC_BOOTLOADER.md from genesis_sdlc source."""
    candidates = [
        source / "builds" / "python" / "src" / "genesis_sdlc" / "SDLC_BOOTLOADER.md",
        Path(__file__).resolve().parent / "SDLC_BOOTLOADER.md",
    ]
    return next((p for p in candidates if p.exists()), None)


def install_claude_md(source: Path, target: Path, slug: str, platform: str,
                      project_name: str) -> str:
    """Append the SDLC bootloader to CLAUDE.md between SDLC markers.

    Each GTL Package appends its own bootloader section:
    - abiogenesis appends GTL_BOOTLOADER (universal axioms) between GTL markers
    - genesis_sdlc appends SDLC_BOOTLOADER (SDLC instantiation) between SDLC markers

    If a legacy monolithic GENESIS_BOOTLOADER block is found, it is removed —
    the split bootloaders supersede it.
    """
    bl_path = _sdlc_bootloader_source(source)
    if bl_path is None:
        raise FileNotFoundError(
            "SDLC_BOOTLOADER.md not found in genesis_sdlc source"
        )

    bootloader = bl_path.read_text(encoding="utf-8")
    operating_protocol = _OPERATING_PROTOCOL.format(slug=slug, platform=platform)
    bootloader_section = f"{_BOOTLOADER_START}\n{operating_protocol}\n{bootloader}\n{_BOOTLOADER_END}"

    header = _CLAUDE_MD_HEADER.format(
        project_name=project_name, slug=slug, platform=platform
    )

    claude_md = target / "CLAUDE.md"
    if claude_md.exists():
        import re
        existing = claude_md.read_text(encoding="utf-8")

        # Remove legacy monolithic bootloader if present
        if _LEGACY_BOOTLOADER_START in existing:
            legacy_pattern = re.compile(
                re.escape(_LEGACY_BOOTLOADER_START) + r".*?" + re.escape(_LEGACY_BOOTLOADER_END),
                re.DOTALL,
            )
            existing = legacy_pattern.sub("", existing)

        # Prepend project header if missing (ABG creates CLAUDE.md first
        # with just the GTL bootloader — no project-specific section).
        if "# CLAUDE.md" not in existing:
            existing = header + existing

        if _BOOTLOADER_START in existing:
            pattern = re.compile(
                re.escape(_BOOTLOADER_START) + r".*?" + re.escape(_BOOTLOADER_END),
                re.DOTALL,
            )
            updated = pattern.sub(bootloader_section, existing)
            claude_md.write_text(updated, encoding="utf-8")
            return "updated"
        else:
            with open(claude_md, "w", encoding="utf-8") as f:
                f.write(existing.rstrip() + f"\n\n---\n\n{bootloader_section}\n")
            return "appended"
    else:
        claude_md.write_text(header + bootloader_section + "\n", encoding="utf-8")
        return "created"


def install_operating_standards(source: Path, target: Path) -> str:
    """Install operating standards into .gsdlc/release/operating-standards/.

    # Implements: REQ-F-TERRITORY-001

    Standards are immutable release artifacts from the methodology layer,
    not runtime evidence — they belong in .gsdlc/release/, not .ai-workspace/.
    """
    src_standards = source / "specification" / "standards"
    if not src_standards.exists():
        return "source_missing"

    dest = target / ".gsdlc" / "release" / "operating-standards"
    dest.mkdir(parents=True, exist_ok=True)

    installed = []
    for src_file in sorted(src_standards.glob("*.md")):
        shutil.copy2(src_file, dest / src_file.name)
        installed.append(src_file.name)

    return f"installed:{','.join(installed)}" if installed else "empty"


def _read_worker_ref(target: Path) -> tuple[str | None, str | None]:
    """Return (module, attr) for the project worker declared in genesis.yml."""
    genesis_yml = target / ".genesis" / "genesis.yml"
    if not genesis_yml.exists():
        return None, None
    import re
    text = genesis_yml.read_text(encoding="utf-8")
    m = re.search(r"^worker:\s+(\S+):(\w+)", text, re.MULTILINE)
    if not m:
        return None, None
    return m.group(1), m.group(2)


def _read_existing_slug(target: Path) -> str | None:
    genesis_yml = target / ".genesis" / "genesis.yml"
    if not genesis_yml.exists():
        return None
    import re
    text = genesis_yml.read_text(encoding="utf-8")
    m = re.search(r"^package:\s+gtl_spec\.packages\.(\w+):package", text, re.MULTILINE)
    return m.group(1) if m else None


def _install_bootloader_release(source: Path, target: Path) -> str:
    """Install SDLC_BOOTLOADER.md into .gsdlc/release/ as a release artifact.

    # Implements: REQ-F-TERRITORY-001

    The bootloader is injected into CLAUDE.md at install time, but the
    released copy in .gsdlc/release/ is the audit reference.
    """
    bl_path = _sdlc_bootloader_source(source)
    if bl_path is None:
        return "source_missing"
    dest = target / ".gsdlc" / "release" / "SDLC_BOOTLOADER.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bl_path, dest)
    return "installed"


def _update_genesis_yml_pythonpath(target: Path) -> str:
    """
    Update genesis.yml pythonpath to point to .gsdlc/release instead of builds/python/src.

    # Implements: REQ-F-TERRITORY-002

    The engine reads pythonpath entries from genesis.yml and adds them to sys.path.
    After territory separation, the deployed runtime is at .gsdlc/release, not builds/.
    """
    import re
    genesis_yml = target / ".genesis" / "genesis.yml"
    if not genesis_yml.exists():
        return "no_genesis_yml"

    text = genesis_yml.read_text(encoding="utf-8")

    # Replace pythonpath section: remove builds/python/src, add .gsdlc/release
    # Handle the YAML list format: "pythonpath:\n  - entry\n  - entry"
    new_pythonpath = "pythonpath:\n  - .gsdlc/release\n"

    if "pythonpath:" in text:
        # Replace entire pythonpath block (key + indented list items)
        text = re.sub(
            r"^pythonpath:\s*\n(?:\s+-\s+.+\n?)*",
            new_pythonpath,
            text,
            flags=re.MULTILINE,
        )
    else:
        text = text.rstrip() + "\n" + new_pythonpath

    genesis_yml.write_text(text, encoding="utf-8")
    return "updated"


def _emit_workflow_activated_event(target: Path, previous_version: str | None) -> None:
    """Append a workflow_activated event to the event stream."""
    events_dir = target / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "event_type": "workflow_activated",
        "event_time": datetime.now(timezone.utc).isoformat(),
        "data": {
            "workflow": "genesis_sdlc.standard",
            "version": VERSION,
            "previous_version": previous_version,
            "target": str(target),
        },
    }
    with (events_dir / "events.jsonl").open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def _migrate_provenance(target: Path) -> dict:
    """
    One-time provenance migration: scan for old fp_assessment/review_approved events and
    re-emit as assessed{kind: fp}/approved{kind: fh_review} with spec_hash and workflow_version.

    Called on first activation when upgrading from old event naming.
    Only the most-recent passing assessment per (edge, evaluator) is migrated.
    Only the most-recent approval per edge is migrated.
    """
    import hashlib as _hashlib
    import importlib
    import re as _re
    import sys as _sys

    events_file = target / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        return {"migrated": 0, "skipped": "no_events_file"}

    events: list[dict] = []
    with events_file.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass

    if not events:
        return {"migrated": 0, "skipped": "no_events"}

    # Collect most-recent passing fp_assessment per (edge, evaluator)
    fp_seen: dict = {}
    for e in events:
        if (
            e.get("event_type") == "fp_assessment"
            and e.get("data", {}).get("result") == "pass"
        ):
            key = (e["data"].get("edge"), e["data"].get("evaluator"))
            fp_seen[key] = e

    # Collect most-recent review_approved per edge
    fh_seen: dict = {}
    for e in events:
        if e.get("event_type") == "review_approved":
            edge = e.get("data", {}).get("edge")
            if edge:
                fh_seen[edge] = e

    if not fp_seen and not fh_seen:
        return {"migrated": 0, "skipped": "no_convergence_events"}

    # Import the project's actual worker from genesis.yml so custom edges are included.
    # Fall back to the standard spec only if the project worker cannot be loaded.
    genesis_path = str(target / ".genesis")
    added_to_path = genesis_path not in _sys.path
    if added_to_path:
        _sys.path.insert(0, genesis_path)

    # Also add .gsdlc/release for territory model imports
    gsdlc_release_path = str(target / ".gsdlc" / "release")
    added_gsdlc = gsdlc_release_path not in _sys.path
    if added_gsdlc:
        _sys.path.insert(0, gsdlc_release_path)

    # Collect extra pythonpath entries declared in genesis.yml
    added_project_paths: list[str] = []
    genesis_yml = target / ".genesis" / "genesis.yml"
    if genesis_yml.exists():
        import re as _re2
        _yml_text = genesis_yml.read_text(encoding="utf-8")
        for _pp in _re2.findall(r"^\s+-\s+(.+)$", _yml_text, _re2.MULTILINE):
            _pp_abs = str((target / _pp.strip()).resolve())
            if _pp_abs not in _sys.path:
                _sys.path.insert(0, _pp_abs)
                added_project_paths.append(_pp_abs)

    migr_worker = None
    try:
        # Prefer the project's own worker (resolves custom edges like design→code)
        _worker_mod, _worker_attr = _read_worker_ref(target)
        if _worker_mod and _worker_attr:
            _mod = importlib.import_module(_worker_mod)
            migr_worker = getattr(_mod, _worker_attr)
    except Exception:
        migr_worker = None

    if migr_worker is None:
        # Fallback: standard genesis_sdlc spec
        try:
            ver = VERSION.replace(".", "_")
            spec_mod = importlib.import_module(
                f"workflows.genesis_sdlc.standard.v{ver}.spec"
            )
            slug = _read_existing_slug(target) or "project_package"
            instantiate_fn = getattr(spec_mod, "instantiate", None)
            if instantiate_fn:
                _, migr_worker = instantiate_fn(slug=slug)
            else:
                migr_worker = spec_mod.worker
        except Exception as exc:
            for _p in added_project_paths:
                try:
                    _sys.path.remove(_p)
                except ValueError:
                    pass
            if added_gsdlc:
                try:
                    _sys.path.remove(gsdlc_release_path)
                except ValueError:
                    pass
            if added_to_path:
                try:
                    _sys.path.remove(genesis_path)
                except ValueError:
                    pass
            return {"migrated": 0, "error": f"workflow_import_failed: {exc}"}

    def _job_hash(job) -> str:
        """Mirror of genesis.bind.job_evaluator_hash — must stay in sync."""
        lines = sorted(
            f"{ev.name}:{ev.category.__name__}:{getattr(ev, 'command', '') or ''}:{ev.description}"
            for ev in job.evaluators
        )
        raw = "\n".join(_re.sub(r"\s+", " ", line.strip()) for line in lines)
        return _hashlib.sha256(raw.encode()).hexdigest()[:16]

    job_by_edge = {job.edge.name: job for job in migr_worker.can_execute}

    # Read workflow_version from the just-written active-workflow.json
    active_path = target / ".gsdlc" / "release" / "active-workflow.json"
    try:
        active_data = json.loads(active_path.read_text(encoding="utf-8"))
        workflow_version = f"{active_data['workflow']}@{active_data['version']}"
    except Exception:
        workflow_version = "unknown"

    now = datetime.now(timezone.utc).isoformat()
    migrated_fp = 0
    migrated_fh = 0

    with events_file.open("a", encoding="utf-8") as f:
        for (edge, evaluator), orig in fp_seen.items():
            job = job_by_edge.get(edge)
            if job is None:
                continue  # edge no longer in graph — skip
            spec_hash = _job_hash(job)
            data = {
                "edge": edge,
                "evaluator": evaluator,
                "result": "pass",
                "spec_hash": spec_hash,
                "migrated_from": orig.get("event_time"),
                "actor": "migration",
            }
            f.write(json.dumps({"event_type": "assessed", "event_time": now, "data": {**data, "kind": "fp"}}) + "\n")
            migrated_fp += 1

        for edge, orig in fh_seen.items():
            data = dict(orig.get("data", {}))
            data["workflow_version"] = workflow_version
            data["migrated_from"] = orig.get("event_time")
            f.write(json.dumps({"event_type": "approved", "event_time": now, "data": {**data, "kind": "fh_review"}}) + "\n")
            migrated_fh += 1

    for _p in added_project_paths:
        try:
            _sys.path.remove(_p)
        except ValueError:
            pass
    if added_gsdlc:
        try:
            _sys.path.remove(gsdlc_release_path)
        except ValueError:
            pass
    if added_to_path:
        try:
            _sys.path.remove(genesis_path)
        except ValueError:
            pass

    return {
        "migrated": migrated_fp + migrated_fh,
        "fp_assessments": migrated_fp,
        "review_approvals": migrated_fh,
    }


def install(
    target: Path,
    *,
    source: Path | None = None,
    slug: str = "project_package",
    platform: str = "python",
    verify_only: bool = False,
    audit_only: bool = False,
    do_migrate: bool = False,
) -> dict:
    target = target.resolve()
    src = resolve_source(str(source) if source else None)
    project_name = target.name

    existing_slug = _read_existing_slug(target)
    if existing_slug and slug == "project_package":
        # Caller didn't pass an explicit slug — honour the installed one.
        slug = existing_slug

    if do_migrate:
        return migrate_full_copy(target, slug)

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
        "migration": None,
        "errors": [],
    }

    if verify_only:
        return _verify(target, result, platform=platform)

    if audit_only:
        return _audit(target, result, src, slug, platform=platform)

    # 1. Engine + .genesis/gtl_spec + builds/<platform>/ scaffold via abiogenesis
    try:
        engine_result = _run_abiogenesis_installer(src, target, slug, platform)
        result["engine"] = engine_result.get("status")
        if engine_result.get("errors"):
            result["errors"].extend(engine_result["errors"])
        # Verify abg installed the GTL bootloader into CLAUDE.md
        if engine_result.get("claude_md") == "source_missing":
            result["errors"].append("engine: GTL bootloader not installed into CLAUDE.md")
    except (FileNotFoundError, RuntimeError) as exc:
        result["errors"].append(f"engine: {exc}")

    # 2. Versioned immutable workflow release (Layer 2 — written once, never overwritten)
    try:
        result["workflow_release"] = install_workflow_release(src, target)
    except Exception as exc:
        result["errors"].append(f"workflow_release: {exc}")

    # 3. Active baseline pointer + migration detection
    needs_migration = False
    previous_version: str | None = None
    try:
        active_status, needs_migration, previous_version = install_active_workflow(target)
        result["active_workflow"] = active_status
    except Exception as exc:
        result["errors"].append(f"active_workflow: {exc}")

    # 4. Backwards-compat shim: spec/genesis_sdlc.py for old imports
    try:
        result["immutable_spec"] = install_immutable_spec(src, target)
    except Exception as exc:
        result["errors"].append(f"immutable_spec: {exc}")

    # 5a. Scaffold specification/requirements.md if absent  # Implements: REQ-F-CUSTODY-003
    try:
        result["requirements_scaffold"] = _scaffold_requirements_md(target)
    except Exception as exc:
        result["errors"].append(f"requirements_scaffold: {exc}")

    # 5b. Generated wrapper (Layer 3 — rewritten when system-ownership marker present)
    try:
        result["sdlc_starter_spec"] = install_sdlc_starter_spec(src, target, slug, platform)
    except Exception as exc:
        result["errors"].append(f"sdlc_starter_spec: {exc}")

    # 5c. Update genesis.yml pythonpath to .gsdlc/release  # Implements: REQ-F-TERRITORY-002
    try:
        result["genesis_yml_pythonpath"] = _update_genesis_yml_pythonpath(target)
    except Exception as exc:
        result["errors"].append(f"genesis_yml_pythonpath: {exc}")

    # 6. Slash commands
    try:
        result["commands"] = install_commands(src, target)
    except FileNotFoundError as exc:
        result["errors"].append(f"commands: {exc}")

    # 7. CLAUDE.md + bootloader
    try:
        result["claude_md"] = install_claude_md(src, target, slug, platform, project_name)
    except FileNotFoundError as exc:
        result["errors"].append(f"claude_md: {exc}")

    # 8. Operating standards → .gsdlc/release/operating-standards/
    try:
        result["operating_standards"] = install_operating_standards(src, target)
    except Exception as exc:
        result["errors"].append(f"operating_standards: {exc}")

    # 8b. SDLC bootloader release copy → .gsdlc/release/SDLC_BOOTLOADER.md
    try:
        result["sdlc_bootloader_release"] = _install_bootloader_release(src, target)
    except Exception as exc:
        result["errors"].append(f"sdlc_bootloader_release: {exc}")

    # 9. SDLC workspace directories
    for ws_dir in [
        ".ai-workspace/features/active",
        ".ai-workspace/features/completed",
        ".ai-workspace/reviews/pending",
        ".ai-workspace/reviews/proxy-log",
        ".ai-workspace/comments/claude",
        ".ai-workspace/backlog",
    ]:
        (target / ws_dir).mkdir(parents=True, exist_ok=True)

    # 10. Workflow activation event + one-time provenance migration
    _emit_workflow_activated_event(target, previous_version)
    if needs_migration:
        try:
            result["migration"] = _migrate_provenance(target)
        except Exception as exc:
            result["errors"].append(f"migration: {exc}")
            result["migration"] = {"error": str(exc)}

    # 11. Install event
    _emit_install_event(target, result)

    result["status"] = "installed" if not result["errors"] else "partial"
    return result


def _verify(target: Path, result: dict, platform: str = "python") -> dict:
    ver_spec = (
        target / ".gsdlc" / "release" / "workflows" / "genesis_sdlc"
        / "standard" / f"v{VERSION.replace('.', '_')}" / "spec.py"
    )
    _standards_dir = target / ".gsdlc" / "release" / "operating-standards"
    _src_standards = resolve_source(None) / "specification" / "standards"
    _installed_files = set(p.name for p in _standards_dir.glob("*.md")) if _standards_dir.is_dir() else set()
    _source_files = set(p.name for p in _src_standards.glob("*.md")) if _src_standards.is_dir() else set()
    _standards_ok = _source_files.issubset(_installed_files) and bool(_source_files)

    checks = {
        # Kernel territory (.genesis/) — owned by ABG
        "engine": (target / ".genesis" / "genesis" / "__main__.py").exists(),
        "gtl": (target / ".genesis" / "gtl" / "core.py").exists(),
        "genesis_yml": (target / ".genesis" / "genesis.yml").exists(),
        # Release territory (.gsdlc/release/) — owned by gsdlc
        "workflow_release": ver_spec.exists(),
        "active_workflow": (target / ".gsdlc" / "release" / "active-workflow.json").exists(),
        "immutable_spec": (target / ".gsdlc" / "release" / "spec" / "genesis_sdlc.py").exists(),
        "gtl_spec": (target / ".gsdlc" / "release" / "gtl_spec" / "packages").is_dir(),
        # Build territory
        "builds_src": (target / "builds" / platform / "src").is_dir(),
        "builds_tests": (target / "builds" / platform / "tests").is_dir(),
        # Commands and documentation
        "commands": (target / ".claude" / "commands" / "gen-start.md").exists(),
        "claude_md": (target / "CLAUDE.md").exists(),
        "gtl_bootloader": (
            "<!-- GTL_BOOTLOADER_START -->" in (target / "CLAUDE.md").read_text(encoding="utf-8")
            if (target / "CLAUDE.md").exists() else False
        ),
        "sdlc_bootloader": (
            _BOOTLOADER_START in (target / "CLAUDE.md").read_text(encoding="utf-8")
            if (target / "CLAUDE.md").exists() else False
        ),
        "operating_standards": _standards_ok,
    }
    if not _standards_ok:
        result["standards_drift"] = sorted(_source_files - _installed_files)
    result["checks"] = checks
    result["status"] = "ok" if all(checks.values()) else "incomplete"
    result["missing"] = [k for k, v in checks.items() if not v]
    return result


def _file_hash(path: Path) -> str:
    """SHA-256 hex digest of a file's content, or empty string if missing."""
    import hashlib
    if not path.exists():
        return ""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _file_hash_str(text: str) -> str:
    """SHA-256 hex digest of a string."""
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _audit(target: Path, result: dict, source: Path, slug: str,
           platform: str = "python") -> dict:
    """
    Content-integrity audit: verify installed artifacts match what this
    version of the installer would produce.  Unlike --verify (file existence),
    --audit compares content hashes, version strings, package wiring, and
    the generated Layer 3 wrapper.

    Checks: workflow release, active-workflow pointer, commands, command stamp,
    operating standards, CLAUDE.md bootloader block, genesis.yml package/worker
    contract (including import resolution), Layer 3 wrapper template, manifest,
    and immutable spec shim.
    """
    import hashlib
    import re

    findings: list[dict] = []
    ver_tag = f"v{VERSION.replace('.', '_')}"

    def _finding(component: str, status: str, detail: str = "",
                 expected: str = "", actual: str = "") -> None:
        f: dict = {"component": component, "status": status}
        if detail:
            f["detail"] = detail
        if expected:
            f["expected"] = expected
        if actual:
            f["actual"] = actual
        findings.append(f)

    # ── 1. Workflow release — immutable spec.py content hash ──
    spec_src = _sdlc_graph_source(source)
    spec_installed = (
        target / ".gsdlc" / "release" / "workflows" / "genesis_sdlc"
        / "standard" / ver_tag / "spec.py"
    )
    if not spec_installed.exists():
        _finding("workflow_release", "missing",
                 f".gsdlc/release/workflows/genesis_sdlc/standard/{ver_tag}/spec.py not found")
    elif spec_src and _file_hash(spec_src) != _file_hash(spec_installed):
        _finding("workflow_release", "drifted",
                 "Installed spec.py content differs from build source",
                 expected=_file_hash(spec_src)[:16],
                 actual=_file_hash(spec_installed)[:16])
    else:
        _finding("workflow_release", "ok")

    # ── 2. Active workflow pointer — version and module path ──
    active_path = target / ".gsdlc" / "release" / "active-workflow.json"
    if not active_path.exists():
        _finding("active_workflow", "missing")
    else:
        try:
            active = json.loads(active_path.read_text(encoding="utf-8"))
            expected_module = f"workflows.genesis_sdlc.standard.{ver_tag}.spec"
            if active.get("version") != VERSION:
                _finding("active_workflow", "version_mismatch",
                         expected=VERSION, actual=active.get("version", ""))
            elif active.get("spec_module") != expected_module:
                _finding("active_workflow", "module_mismatch",
                         expected=expected_module,
                         actual=active.get("spec_module", ""))
            else:
                _finding("active_workflow", "ok")
        except Exception as exc:
            _finding("active_workflow", "error", str(exc))

    # ── 3. Commands — content hash of each installed command vs source ──
    abiogenesis_cmd_src = (
        source.parent / "abiogenesis" / "builds" / "claude_code"
        / ".claude-plugin" / "plugins" / "genesis" / "commands"
    ).resolve()
    genesis_sdlc_cmd_src = (
        source / "builds" / "claude_code" / ".claude-plugin"
        / "plugins" / "genesis" / "commands"
    ).resolve()
    commands_dir = target / ".claude" / "commands"

    for cmd, cmd_src_dir in [
        *[(c, abiogenesis_cmd_src) for c in ABIOGENESIS_COMMANDS],
        *[(c, genesis_sdlc_cmd_src) for c in GENESIS_SDLC_COMMANDS],
    ]:
        src_file = cmd_src_dir / f"{cmd}.md"
        installed_file = commands_dir / f"{cmd}.md"
        if not installed_file.exists():
            _finding(f"command:{cmd}", "missing")
        elif not src_file.exists():
            _finding(f"command:{cmd}", "source_missing",
                     f"Source not found at {src_file}")
        elif _file_hash(src_file) != _file_hash(installed_file):
            _finding(f"command:{cmd}", "drifted",
                     f"Installed {cmd}.md differs from source")
        else:
            _finding(f"command:{cmd}", "ok")

    # ── 4. Commands stamp — version in .genesis-installed ──
    stamp = commands_dir / ".genesis-installed"
    if stamp.exists():
        try:
            stamp_data = json.loads(stamp.read_text(encoding="utf-8"))
            if stamp_data.get("version") != VERSION:
                _finding("commands_stamp", "version_mismatch",
                         expected=VERSION, actual=stamp_data.get("version", ""))
            else:
                _finding("commands_stamp", "ok")
        except Exception as exc:
            _finding("commands_stamp", "error", str(exc))
    else:
        _finding("commands_stamp", "missing")

    # ── 5. Operating standards — content hash per file ──
    src_standards = source / "specification" / "standards"
    dest_standards = target / ".gsdlc" / "release" / "operating-standards"
    if src_standards.is_dir():
        for src_file in sorted(src_standards.glob("*.md")):
            installed = dest_standards / src_file.name
            if not installed.exists():
                _finding(f"standard:{src_file.name}", "missing")
            elif _file_hash(src_file) != _file_hash(installed):
                _finding(f"standard:{src_file.name}", "drifted",
                         "Installed standard differs from source")
            else:
                _finding(f"standard:{src_file.name}", "ok")

    # ── 6. CLAUDE.md bootloader content (both GTL and SDLC blocks) ──
    _GTL_START = "<!-- GTL_BOOTLOADER_START -->"
    _GTL_END = "<!-- GTL_BOOTLOADER_END -->"
    claude_md = target / "CLAUDE.md"
    if claude_md.exists():
        text = claude_md.read_text(encoding="utf-8")

        # 6a. GTL bootloader (installed by abiogenesis)
        if _GTL_START in text and _GTL_END in text:
            gtl_start = text.index(_GTL_START)
            gtl_end = text.index(_GTL_END) + len(_GTL_END)
            installed_gtl = text[gtl_start:gtl_end]
            # Verify against the installed copy in .genesis/gtl_spec/
            gtl_source = target / ".genesis" / "gtl_spec" / "GTL_BOOTLOADER.md"
            if gtl_source.exists():
                gtl_content = gtl_source.read_text(encoding="utf-8")
                expected_gtl = f"{_GTL_START}\n{gtl_content}\n{_GTL_END}"
                if _file_hash_str(installed_gtl) != _file_hash_str(expected_gtl):
                    _finding("gtl_bootloader_content", "drifted",
                             "CLAUDE.md GTL bootloader block differs from .genesis/gtl_spec/GTL_BOOTLOADER.md")
                else:
                    _finding("gtl_bootloader_content", "ok")
            else:
                _finding("gtl_bootloader_content", "source_missing",
                         "GTL_BOOTLOADER.md not found in .genesis/gtl_spec/")
        else:
            _finding("gtl_bootloader_content", "missing",
                     "GTL bootloader markers not found in CLAUDE.md — abiogenesis install may have failed")

        # 6b. SDLC bootloader (installed by genesis_sdlc)
        if _BOOTLOADER_START in text and _BOOTLOADER_END in text:
            bl_start = text.index(_BOOTLOADER_START)
            bl_end = text.index(_BOOTLOADER_END) + len(_BOOTLOADER_END)
            installed_block = text[bl_start:bl_end]
            bl_source = _sdlc_bootloader_source(source)
            if bl_source:
                bl_content = bl_source.read_text(encoding="utf-8")
                op = _OPERATING_PROTOCOL.format(slug=slug, platform=platform)
                expected_block = (
                    f"{_BOOTLOADER_START}\n{op}\n{bl_content}\n{_BOOTLOADER_END}"
                )
                if _file_hash_str(installed_block) != _file_hash_str(expected_block):
                    _finding("sdlc_bootloader_content", "drifted",
                             "CLAUDE.md SDLC bootloader block differs from source")
                else:
                    _finding("sdlc_bootloader_content", "ok")
            else:
                _finding("sdlc_bootloader_content", "source_missing",
                         "SDLC_BOOTLOADER.md not found in genesis_sdlc source")
        else:
            _finding("sdlc_bootloader_content", "missing",
                     "SDLC bootloader markers not found in CLAUDE.md")

        # 6c. Block ordering: GTL must precede SDLC
        if _GTL_START in text and _BOOTLOADER_START in text:
            if text.index(_GTL_START) > text.index(_BOOTLOADER_START):
                _finding("bootloader_order", "invalid",
                         "GTL bootloader must appear before SDLC bootloader in CLAUDE.md")

        # 6d. Legacy monolithic bootloader (should have been migrated)
        if _LEGACY_BOOTLOADER_START in text:
            _finding("legacy_bootloader", "stale",
                     "Legacy GENESIS_BOOTLOADER markers still present — reinstall to migrate")
    else:
        _finding("gtl_bootloader_content", "missing", "CLAUDE.md not found")
        _finding("sdlc_bootloader_content", "missing", "CLAUDE.md not found")

    # ── 7. genesis.yml package/worker contract ──
    genesis_yml = target / ".genesis" / "genesis.yml"
    if genesis_yml.exists():
        yml_text = genesis_yml.read_text(encoding="utf-8")
        pkg_match = re.search(r"^package:\s+(\S+)", yml_text, re.MULTILINE)
        worker_match = re.search(r"^worker:\s+(\S+)", yml_text, re.MULTILINE)
        if pkg_match:
            pkg_ref = pkg_match.group(1)
            # Verify the module:attr reference is importable
            mod_path, _, attr = pkg_ref.rpartition(":")
            try:
                import importlib
                _old_path = sys.path[:]
                if str(target / ".genesis") not in sys.path:
                    sys.path.insert(0, str(target / ".genesis"))
                if str(target / ".gsdlc" / "release") not in sys.path:
                    sys.path.insert(0, str(target / ".gsdlc" / "release"))
                if str(target) not in sys.path:
                    sys.path.insert(0, str(target))
                mod = importlib.import_module(mod_path)
                if hasattr(mod, attr):
                    _finding("genesis_yml_package", "ok",
                             detail=f"Package {pkg_ref} resolves")
                else:
                    _finding("genesis_yml_package", "broken",
                             f"Module {mod_path} loaded but {attr!r} not found")
            except ImportError as exc:
                _finding("genesis_yml_package", "broken",
                         f"Package {pkg_ref} cannot be imported: {exc}")
            finally:
                sys.path[:] = _old_path
        else:
            _finding("genesis_yml_package", "missing",
                     "No package: line in genesis.yml")

        if worker_match:
            _finding("genesis_yml_worker", "ok",
                     detail=f"Worker ref: {worker_match.group(1)}")
        else:
            _finding("genesis_yml_worker", "missing",
                     "No worker: line in genesis.yml")
    else:
        _finding("genesis_yml", "missing", "genesis.yml not found")

    # ── 8. Generated wrapper — content matches expected template ──
    wrapper_path = target / ".gsdlc" / "release" / "gtl_spec" / "packages" / f"{slug}.py"
    if wrapper_path.exists():
        wrapper_text = wrapper_path.read_text(encoding="utf-8")
        if "genesis_sdlc-generated" in wrapper_text:
            expected_wrapper = _render_wrapper(slug)
            if wrapper_text.strip() != expected_wrapper.strip():
                _finding("layer3_wrapper", "drifted",
                         f"Generated wrapper at {wrapper_path.name} differs from "
                         f"expected template for v{VERSION}")
            else:
                _finding("layer3_wrapper", "ok")
        else:
            _finding("layer3_wrapper", "customised",
                     "Wrapper is user-owned (no genesis_sdlc-generated marker)")
    else:
        _finding("layer3_wrapper", "missing",
                 f"No wrapper found for slug {slug!r}")

    # ── 10. Manifest version consistency ──
    manifest_path = (
        target / ".gsdlc" / "release" / "workflows" / "genesis_sdlc"
        / "standard" / ver_tag / "manifest.json"
    )
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest.get("version") != VERSION:
                _finding("manifest", "version_mismatch",
                         expected=VERSION, actual=manifest.get("version", ""))
            else:
                _finding("manifest", "ok")
        except Exception as exc:
            _finding("manifest", "error", str(exc))
    else:
        _finding("manifest", "missing")

    # ── 11. Immutable spec shim ──
    shim = target / ".gsdlc" / "release" / "spec" / "genesis_sdlc.py"
    if spec_src and shim.exists():
        if _file_hash(spec_src) != _file_hash(shim):
            _finding("immutable_spec_shim", "drifted",
                     "Backwards-compat shim differs from build source")
        else:
            _finding("immutable_spec_shim", "ok")
    elif not shim.exists():
        _finding("immutable_spec_shim", "missing")

    # ── Build result ──
    ok_count = sum(1 for f in findings if f["status"] == "ok")
    total = len(findings)
    drifted = [f for f in findings if f["status"] == "drifted"]
    missing = [f for f in findings if f["status"] == "missing"]
    errors = [f for f in findings if f["status"] not in ("ok", "drifted", "missing")]

    result["audit"] = {
        "version": VERSION,
        "sdlc_bootloader_version": SDLC_BOOTLOADER_VERSION,
        "findings": findings,
        "summary": {
            "total": total,
            "ok": ok_count,
            "drifted": len(drifted),
            "missing": len(missing),
            "errors": len(errors),
        },
    }
    if drifted:
        result["audit"]["drifted"] = [f["component"] for f in drifted]
    if missing:
        result["audit"]["missing"] = [f["component"] for f in missing]

    result["status"] = "ok" if ok_count == total else "drift_detected"
    return result


def _emit_install_event(target: Path, install_result: dict) -> None:
    events_dir = target / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    event = {
        "event_type": "genesis_sdlc_installed",
        "event_time": install_result["timestamp"],
        "data": {
            "version": VERSION,
            "engine_status": install_result.get("engine"),
            "commands_installed": len(install_result.get("commands", [])),
            "claude_md": install_result.get("claude_md"),
            "operating_standards": install_result.get("operating_standards"),
            "migration": install_result.get("migration"),
            "target": install_result["target"],
        },
    }
    events_file = events_dir / "events.jsonl"
    with events_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="genesis_sdlc.install",
        description=f"genesis_sdlc v{VERSION} — SDLC code builder installer",
    )
    parser.add_argument("--target", metavar="DIR", default=".",
                        help="Target project directory (default: cwd)")
    parser.add_argument("--source", metavar="DIR", default=None,
                        help="genesis_sdlc source root (auto-detected if omitted)")
    parser.add_argument("--project-slug", metavar="SLUG", default="project_package",
                        help="Python identifier for starter spec module (default: project_package)")
    parser.add_argument("--platform", metavar="PLATFORM", default="python",
                        help="Build platform name for builds/<platform>/ (default: python)")
    parser.add_argument("--verify", action="store_true",
                        help="Verify installation only — do not install (file existence)")
    parser.add_argument("--audit", action="store_true",
                        help="Deep content-integrity audit — verify installed content matches release")
    parser.add_argument("--migrate-full-copy", action="store_true",
                        help="Migrate a legacy full-copy local spec to the 4-layer model")
    args = parser.parse_args()

    slug = args.project_slug
    if not slug.isidentifier():
        print(f"ERROR: --project-slug must be a valid Python identifier, got {slug!r}",
              file=sys.stderr)
        sys.exit(1)

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"ERROR: target directory does not exist: {target}", file=sys.stderr)
        sys.exit(1)

    try:
        result = install(
            target,
            source=Path(args.source) if args.source else None,
            slug=slug,
            platform=args.platform,
            verify_only=args.verify,
            audit_only=args.audit,
            do_migrate=args.migrate_full_copy,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") in ("installed", "ok", "migrated") else 1)


if __name__ == "__main__":
    main()
