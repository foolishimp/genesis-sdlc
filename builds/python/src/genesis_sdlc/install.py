# Implements: REQ-F-BOOT-001
# Implements: REQ-F-BOOT-002
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

What gets installed:
    .genesis/                       ← abiogenesis engine (via gen-install.py)
    gtl_spec/packages/<slug>.py     ← SDLC bootstrap graph as starter spec
    builds/<platform>/              ← src/, tests/, design/adrs/ scaffold
    .claude/commands/gen-*.md       ← all genesis slash commands
    CLAUDE.md                       ← project orientation + Genesis Bootloader

Source resolution order (--source flag or auto-detected):
    1. --source /path/to/genesis_sdlc    local disk clone
    2. Detected from installed package   sys.path resolution
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.1"

# Commands inherited from the abiogenesis engine plugin.
# Source: <abiogenesis>/builds/claude_code/.claude-plugin/plugins/genesis/commands/
ABIOGENESIS_COMMANDS = [
    "gen-start",
    "gen-gaps",
    "gen-status",
]

# Commands owned by genesis_sdlc — SDLC additions on top of the engine.
# Source: builds/claude_code/.claude-plugin/plugins/genesis/commands/
GENESIS_SDLC_COMMANDS = [
    "gen-iterate",
    "gen-review",
]

# CLAUDE.md markers for idempotent bootloader injection
_BOOTLOADER_START = "<!-- GENESIS_BOOTLOADER_START -->"
_BOOTLOADER_END = "<!-- GENESIS_BOOTLOADER_END -->"

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
├── gtl_spec/packages/{slug}.py   ← GTL spec — the construction contract
├── builds/{platform}/
│   ├── src/                      ← implementation source
│   ├── tests/                    ← test suite
│   └── design/adrs/              ← architecture decision records
├── .genesis/                     ← abiogenesis engine (do not edit)
└── .ai-workspace/                ← runtime state (events, features, reviews)
```

## Invocation

```bash
PYTHONPATH=.genesis python -m genesis start --auto --workspace .
PYTHONPATH=.genesis python -m genesis gaps  --workspace .
```

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
        # install.py lives at .../genesis_sdlc/builds/python/src/genesis_sdlc/
        # So the project root is 4 levels up from the package directory.
        pkg_path = Path(genesis_sdlc.__file__).resolve().parent
        for parent in [
            pkg_path.parent.parent,           # builds/python/
            pkg_path.parent.parent.parent,    # builds/
            pkg_path.parent.parent.parent.parent,  # genesis_sdlc/ ← correct root
        ]:
            if (parent / "gtl_spec").exists() and (parent / ".genesis").exists():
                return parent
    except ImportError:
        pass
    return None


def _source_root_from_script() -> Path:
    """Source root relative to this script: src/genesis_sdlc/install.py → project root.

    install.py is at: <root>/builds/python/src/genesis_sdlc/install.py
      parents[0] = .../genesis_sdlc/          (package dir)
      parents[1] = .../src/
      parents[2] = .../builds/python/
      parents[3] = .../builds/
      parents[4] = <root>/                    ← genesis_sdlc project root
    """
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
    """
    Delegate engine installation to abiogenesis gen-install.py.
    Resolves gen-install.py from the sibling abiogenesis directory.
    Returns the parsed result dict.
    """
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


def install_commands(source: Path, target: Path) -> list[str]:
    """Copy gen-*.md commands into target/.claude/commands/.

    Composes from two sources:
      1. abiogenesis engine commands  — inherited, single source of truth in abiogenesis
      2. genesis_sdlc own commands    — SDLC additions, owned here
    """
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

    # Write install stamp
    stamp = commands_dir / ".genesis-installed"
    stamp.write_text(
        json.dumps({"version": VERSION, "installed": installed,
                    "timestamp": datetime.now(timezone.utc).isoformat()}, indent=2)
    )
    return installed


def install_claude_md(source: Path, target: Path, slug: str, platform: str,
                      project_name: str) -> str:
    """
    Write or update CLAUDE.md in target.

    The Genesis Bootloader section is always replaced with the latest version.
    Everything outside the bootloader markers is preserved.
    """
    bootloader_path = source / "gtl_spec" / "GENESIS_BOOTLOADER.md"
    if not bootloader_path.exists():
        # Fallback: abiogenesis bootloader
        bootloader_path = (
            source.parent / "abiogenesis" / "gtl_spec" / "GENESIS_BOOTLOADER.md"
        ).resolve()

    if not bootloader_path.exists():
        raise FileNotFoundError(f"GENESIS_BOOTLOADER.md not found at {bootloader_path}")

    bootloader = bootloader_path.read_text(encoding="utf-8")
    bootloader_section = f"{_BOOTLOADER_START}\n{bootloader}\n{_BOOTLOADER_END}\n"

    header = _CLAUDE_MD_HEADER.format(
        project_name=project_name, slug=slug, platform=platform
    )

    claude_md = target / "CLAUDE.md"
    if claude_md.exists():
        existing = claude_md.read_text(encoding="utf-8")
        if _BOOTLOADER_START in existing:
            # Replace existing bootloader section
            import re
            pattern = re.compile(
                re.escape(_BOOTLOADER_START) + r".*?" + re.escape(_BOOTLOADER_END),
                re.DOTALL,
            )
            updated = pattern.sub(bootloader_section.rstrip(), existing)
            claude_md.write_text(updated, encoding="utf-8")
            return "updated"
        else:
            # Append bootloader to existing CLAUDE.md
            with claude_md.open("a", encoding="utf-8") as f:
                f.write(f"\n\n---\n\n{bootloader_section}")
            return "appended"
    else:
        # Fresh install — write header + bootloader
        claude_md.write_text(header + bootloader_section, encoding="utf-8")
        return "created"


def install_sdlc_starter_spec(source: Path, target: Path, slug: str,
                              platform: str = "python") -> str | None:
    """
    Replace the minimal abiogenesis starter spec with the full SDLC bootstrap graph.

    Substitutions applied to the genesis_sdlc template:
      - Package name: "genesis_sdlc" → slug
      - req_coverage package ref: gtl_spec.packages.genesis_sdlc → gtl_spec.packages.<slug>
      - builds/python/src/  → builds/<platform>/src/
      - builds/python/tests/ → builds/<platform>/tests/
      - builds/python/design/adrs/ → builds/<platform>/design/adrs/

    Only written if the file still contains the abiogenesis stub (safe to re-run).
    """
    starter_path = target / "gtl_spec" / "packages" / f"{slug}.py"
    if not starter_path.exists():
        return None  # abiogenesis installer should have written it — skip

    existing = starter_path.read_text(encoding="utf-8")
    # Only replace if it still has the abiogenesis stub (not yet customised)
    if "spec→output" not in existing:
        return "already_customised"

    sdlc_spec_src = source / "gtl_spec" / "packages" / "genesis_sdlc.py"
    if not sdlc_spec_src.exists():
        return None

    template = sdlc_spec_src.read_text(encoding="utf-8")
    adapted = (
        template
        # Package identity
        .replace('name="genesis_sdlc"', f'name="{slug}"')
        .replace("genesis_sdlc — standard SDLC bootstrap graph",
                 f"{slug} — standard SDLC bootstrap graph")
        # Self-referential spec path in req_coverage evaluator
        .replace("gtl_spec.packages.genesis_sdlc:package",
                 f"gtl_spec.packages.{slug}:package")
        # Platform-specific build paths
        .replace("builds/python/src/", f"builds/{platform}/src/")
        .replace("builds/python/tests/", f"builds/{platform}/tests/")
        .replace("builds/python/design/adrs/", f"builds/{platform}/design/adrs/")
    )
    starter_path.write_text(adapted, encoding="utf-8")
    return "installed"


def install(
    target: Path,
    *,
    source: Path | None = None,
    slug: str = "project_package",
    platform: str = "python",
    verify_only: bool = False,
) -> dict:
    target = target.resolve()
    src = resolve_source(str(source) if source else None)
    project_name = target.name

    result: dict = {
        "version": VERSION,
        "target": str(target),
        "source": str(src),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "engine": None,
        "commands": [],
        "claude_md": None,
        "sdlc_starter_spec": None,
        "errors": [],
    }

    if verify_only:
        return _verify(target, result, platform=platform)

    # 1. Engine + gtl_spec + builds/<platform>/ scaffold via abiogenesis installer
    try:
        engine_result = _run_abiogenesis_installer(src, target, slug, platform)
        result["engine"] = engine_result.get("status")
        if engine_result.get("errors"):
            result["errors"].extend(engine_result["errors"])
    except (FileNotFoundError, RuntimeError) as exc:
        result["errors"].append(f"engine: {exc}")

    # 2. Replace abiogenesis stub with full SDLC bootstrap graph
    try:
        result["sdlc_starter_spec"] = install_sdlc_starter_spec(src, target, slug, platform)
    except Exception as exc:
        result["errors"].append(f"sdlc_starter_spec: {exc}")

    # 3. Slash commands
    try:
        result["commands"] = install_commands(src, target)
    except FileNotFoundError as exc:
        result["errors"].append(f"commands: {exc}")

    # 4. CLAUDE.md + bootloader
    try:
        result["claude_md"] = install_claude_md(src, target, slug, platform, project_name)
    except FileNotFoundError as exc:
        result["errors"].append(f"claude_md: {exc}")

    # 5. Emit install event
    _emit_install_event(target, result)

    result["status"] = "installed" if not result["errors"] else "partial"
    return result


def _verify(target: Path, result: dict, platform: str = "python") -> dict:
    checks = {
        "engine": (target / ".genesis" / "genesis" / "__main__.py").exists(),
        "gtl": (target / ".genesis" / "gtl" / "core.py").exists(),
        "genesis_yml": (target / ".genesis" / "genesis.yml").exists(),
        "gtl_spec": (target / "gtl_spec" / "packages").is_dir(),
        "builds_src": (target / "builds" / platform / "src").is_dir(),
        "builds_tests": (target / "builds" / platform / "tests").is_dir(),
        "commands": (target / ".claude" / "commands" / "gen-start.md").exists(),
        "claude_md": (target / "CLAUDE.md").exists(),
        "bootloader": (
            _BOOTLOADER_START in (target / "CLAUDE.md").read_text(encoding="utf-8")
            if (target / "CLAUDE.md").exists() else False
        ),
    }
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
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)

    print(json.dumps(result, indent=2))
    sys.exit(0 if result.get("status") in ("installed", "ok") else 1)


if __name__ == "__main__":
    main()
