# Implements: REQ-F-BOOT-001
# Implements: REQ-F-BOOT-002
# Implements: REQ-F-BOOT-003
# Implements: REQ-F-BOOT-004
# Implements: REQ-F-BOOT-005
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
    python -m genesis_sdlc.install --target . --migrate-full-copy

Three-layer model
─────────────────
Layer 1  .genesis/genesis/                                  abiogenesis engine — replaced on reinstall
Layer 2  .genesis/workflows/genesis_sdlc/standard/vX_Y_Z/  immutable versioned release — written once
Layer 3  gtl_spec/packages/<slug>.py                        system-owned generated wrapper — replaced on redeploy

The generated wrapper calls instantiate(slug) from the versioned release. Redeploy updates
active-workflow.json and rewrites the wrapper; versioned releases are never modified.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.3.0"
BOOTLOADER_VERSION = "3.0.2"  # matches **Version**: in gtl_spec/GENESIS_BOOTLOADER.md

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

# CLAUDE.md markers for idempotent bootloader injection
_BOOTLOADER_START = "<!-- GENESIS_BOOTLOADER_START -->"
_BOOTLOADER_END = "<!-- GENESIS_BOOTLOADER_END -->"

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
├── gtl_spec/packages/{slug}.py        ← generated workflow wrapper (system-owned)
├── gtl_spec/packages/{slug}_local.py  ← local overlay (user-owned, optional)
├── builds/{platform}/
│   ├── src/                           ← implementation source
│   ├── tests/                         ← test suite
│   └── design/adrs/                   ← architecture decision records
├── .genesis/                          ← engine + versioned workflow releases
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
            if (parent / "gtl_spec").exists() and (parent / ".genesis").exists():
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
        .genesis/workflows/genesis_sdlc/standard/v{VERSION}/spec.py

    This directory is written once and never overwritten — it is the immutable release
    artifact. Reinstalling a newer version adds a new versioned directory alongside
    existing ones; old releases remain on disk for provenance.
    """
    ver_dir = (
        target / ".genesis" / "workflows" / "genesis_sdlc"
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
        target / ".genesis" / "workflows",
        target / ".genesis" / "workflows" / "genesis_sdlc",
        target / ".genesis" / "workflows" / "genesis_sdlc" / "standard",
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
    Write/update .genesis/active-workflow.json — the mutable active baseline pointer.

    Returns (status, needs_migration, previous_version).

    needs_migration is True when upgrading from the old "genesis_sdlc" workflow name to
    "genesis_sdlc.standard" — the provenance migration runs once on this transition.
    """
    active_path = target / ".genesis" / "active-workflow.json"

    needs_migration = False
    previous_version: str | None = None
    if active_path.exists():
        try:
            old = json.loads(active_path.read_text(encoding="utf-8"))
            previous_version = old.get("version")
            if old.get("workflow") != "genesis_sdlc.standard":
                needs_migration = True
        except Exception:
            pass
    else:
        # No active-workflow.json means a pre-0.2.1 install (the file is new in 0.2.1).
        # Check the event stream for prior genesis_sdlc_installed events so migration runs.
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
                            # Keep scanning — use the last installed version found
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
    Install sdlc_graph.py into .genesis/spec/genesis_sdlc.py (backwards compat shim).

    This path is kept so that user-owned local specs written before the 4-layer model
    (which import from spec.genesis_sdlc) continue to work after reinstall. New generated
    wrappers import from the versioned release path instead.
    """
    spec_dir = target / ".genesis" / "spec"
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
from workflows.genesis_sdlc.standard.v{VERSION_UNDERSCORED}.spec import instantiate
package, worker = instantiate(slug="{slug}")
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
    Write the generated wrapper (Layer 3) into gtl_spec/packages/{slug}.py.

    The wrapper is rewritten whenever it carries an explicit system-ownership marker:
      - genesis_sdlc-generated  (new model — always replaced)
      - genesis_sdlc-stub       (old thin-wrapper — upgraded to new model)
      - spec→output             (abiogenesis stub — replaced by genesis_sdlc)

    Any other content is treated as user-owned and not touched. Legacy full-copy specs
    from pre-0.2.0 installs fall into this category; use --migrate-full-copy to opt in.
    """
    wrapper_path = target / "gtl_spec" / "packages" / f"{slug}.py"
    if not wrapper_path.exists():
        return None  # abiogenesis installer should have written it

    existing = wrapper_path.read_text(encoding="utf-8")
    is_system_owned = (
        "genesis_sdlc-generated" in existing
        or "genesis_sdlc-stub" in existing
        or "spec→output" in existing
    )
    if not is_system_owned:
        return "already_customised"

    wrapper_path.write_text(_render_wrapper(slug), encoding="utf-8")
    return "installed"


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
    wrapper_path = target / "gtl_spec" / "packages" / f"{slug}.py"
    if not wrapper_path.exists():
        return {"status": "no_spec_found"}

    existing = wrapper_path.read_text(encoding="utf-8")

    if "genesis_sdlc-generated" in existing:
        return {"status": "already_migrated", "message": "Spec is already the generated wrapper."}
    if "spec→output" in existing:
        return {"status": "abiogenesis_stub", "message": "Use regular install to replace this stub."}
    if "genesis_sdlc-stub" in existing:
        return {"status": "already_migrated", "message": "Spec is the old thin-wrapper stub; regular install will upgrade it."}

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    legacy_path = target / "gtl_spec" / "packages" / f"{slug}_legacy_{ts}.py"
    shutil.move(str(wrapper_path), str(legacy_path))

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


def install_claude_md(source: Path, target: Path, slug: str, platform: str,
                      project_name: str) -> str:
    bootloader_path = source / "gtl_spec" / "GENESIS_BOOTLOADER.md"
    if not bootloader_path.exists():
        bootloader_path = (
            source.parent / "abiogenesis" / "gtl_spec" / "GENESIS_BOOTLOADER.md"
        ).resolve()

    if not bootloader_path.exists():
        raise FileNotFoundError(f"GENESIS_BOOTLOADER.md not found at {bootloader_path}")

    bootloader = bootloader_path.read_text(encoding="utf-8")
    operating_protocol = _OPERATING_PROTOCOL.format(slug=slug, platform=platform)
    bootloader_section = f"{_BOOTLOADER_START}\n{operating_protocol}\n{bootloader}\n{_BOOTLOADER_END}\n"

    header = _CLAUDE_MD_HEADER.format(
        project_name=project_name, slug=slug, platform=platform
    )

    claude_md = target / "CLAUDE.md"
    if claude_md.exists():
        existing = claude_md.read_text(encoding="utf-8")
        if _BOOTLOADER_START in existing:
            import re
            pattern = re.compile(
                re.escape(_BOOTLOADER_START) + r".*?" + re.escape(_BOOTLOADER_END),
                re.DOTALL,
            )
            updated = pattern.sub(bootloader_section.rstrip(), existing)
            claude_md.write_text(updated, encoding="utf-8")
            return "updated"
        else:
            with claude_md.open("a", encoding="utf-8") as f:
                f.write(f"\n\n---\n\n{bootloader_section}")
            return "appended"
    else:
        claude_md.write_text(header + bootloader_section, encoding="utf-8")
        return "created"


def install_operating_standards(source: Path, target: Path) -> str:
    src_standards = source / "standards"
    if not src_standards.exists():
        return "source_missing"

    dest = target / ".ai-workspace" / "operating-standards"
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
    One-time provenance migration: re-emit passing fp_assessments with job_evaluator_hash
    spec_hash, and review_approved events with workflow_version.

    Called on first activation when upgrading from old "genesis_sdlc" workflow naming.
    Only the most-recent passing assessment per (edge, evaluator) is migrated.
    Only the most-recent review_approved per edge is migrated.
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
    active_path = target / ".genesis" / "active-workflow.json"
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
            f.write(json.dumps({"event_type": "fp_assessment", "event_time": now, "data": data}) + "\n")
            migrated_fp += 1

        for edge, orig in fh_seen.items():
            data = dict(orig.get("data", {}))
            data["workflow_version"] = workflow_version
            data["migrated_from"] = orig.get("event_time")
            f.write(json.dumps({"event_type": "review_approved", "event_time": now, "data": data}) + "\n")
            migrated_fh += 1

    for _p in added_project_paths:
        try:
            _sys.path.remove(_p)
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
    do_migrate: bool = False,
) -> dict:
    target = target.resolve()
    src = resolve_source(str(source) if source else None)
    project_name = target.name

    existing_slug = _read_existing_slug(target)
    if existing_slug and existing_slug != slug:
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

    # 1. Engine + gtl_spec + builds/<platform>/ scaffold via abiogenesis
    try:
        engine_result = _run_abiogenesis_installer(src, target, slug, platform)
        result["engine"] = engine_result.get("status")
        if engine_result.get("errors"):
            result["errors"].extend(engine_result["errors"])
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

    # 5. Generated wrapper (Layer 3 — rewritten when system-ownership marker present)
    try:
        result["sdlc_starter_spec"] = install_sdlc_starter_spec(src, target, slug, platform)
    except Exception as exc:
        result["errors"].append(f"sdlc_starter_spec: {exc}")

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

    # 8. Operating standards
    try:
        result["operating_standards"] = install_operating_standards(src, target)
    except Exception as exc:
        result["errors"].append(f"operating_standards: {exc}")

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
        target / ".genesis" / "workflows" / "genesis_sdlc"
        / "standard" / f"v{VERSION.replace('.', '_')}" / "spec.py"
    )
    _standards_dir = target / ".ai-workspace" / "operating-standards"
    _src_standards = resolve_source(None) / "standards"
    _installed_files = set(p.name for p in _standards_dir.glob("*.md")) if _standards_dir.is_dir() else set()
    _source_files = set(p.name for p in _src_standards.glob("*.md")) if _src_standards.is_dir() else set()
    _standards_ok = _source_files.issubset(_installed_files) and bool(_source_files)

    checks = {
        "engine": (target / ".genesis" / "genesis" / "__main__.py").exists(),
        "gtl": (target / ".genesis" / "gtl" / "core.py").exists(),
        "genesis_yml": (target / ".genesis" / "genesis.yml").exists(),
        "workflow_release": ver_spec.exists(),
        "active_workflow": (target / ".genesis" / "active-workflow.json").exists(),
        "immutable_spec": (target / ".genesis" / "spec" / "genesis_sdlc.py").exists(),
        "gtl_spec": (target / "gtl_spec" / "packages").is_dir(),
        "builds_src": (target / "builds" / platform / "src").is_dir(),
        "builds_tests": (target / "builds" / platform / "tests").is_dir(),
        "commands": (target / ".claude" / "commands" / "gen-start.md").exists(),
        "claude_md": (target / "CLAUDE.md").exists(),
        "bootloader": (
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
                        help="Verify installation only — do not install")
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
            do_migrate=args.migrate_full_copy,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") in ("installed", "ok", "migrated") else 1)


if __name__ == "__main__":
    main()
