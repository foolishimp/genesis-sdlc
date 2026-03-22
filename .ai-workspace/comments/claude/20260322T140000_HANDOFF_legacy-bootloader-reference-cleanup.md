# HANDOFF: Legacy GENESIS_BOOTLOADER reference cleanup

**Author**: claude
**Date**: 2026-03-22
**For**: any agent continuing this work

## Background

The monolithic `GENESIS_BOOTLOADER.md` was split into two files on 2026-03-20:
- **GTL_BOOTLOADER.md** — universal formal system (sections I-XI), owned by abiogenesis
- **SDLC_BOOTLOADER.md** — SDLC domain instantiation (sections XII-XX), owned by genesis_sdlc

The split was completed and the files renamed, but many references throughout both repos still point to the old `GENESIS_BOOTLOADER.md` name. This causes a **runtime failure**: the Context locator in the workflow spec resolves to a file that doesn't exist, so `ContextResolver.load()` raises `FileNotFoundError` and F_P dispatches either degrade (missing context) or block entirely.

## Territory model (critical — read before editing)

There are four territories with strict write ownership. **Agents must never edit installed territories directly — fix the source and reinstall.**

| Territory | What writes it | Source location |
|---|---|---|
| `.genesis/` | ABG installer (`gen-install.py`) | `abiogenesis/builds/claude_code/code/` |
| `.gsdlc/release/` | GSDLC installer (`install.py`) | `genesis_sdlc/builds/python/src/genesis_sdlc/` |
| `.claude/commands/` | GSDLC installer (`install_commands()`) | ABG: `abiogenesis/builds/claude_code/.claude-plugin/.../commands/`, GSDLC: `genesis_sdlc/builds/claude_code/.claude-plugin/.../commands/` |
| `specification/`, `builds/` | Authored in place | (these ARE the sources) |

Cascade order: `abiogenesis source → ABG installer → .genesis/` then `gsdlc source → GSDLC installer → .gsdlc/release/ + .claude/commands/`

## What was done in this session

### Fixed (GSDLC source files — this repo):
| File | Change |
|---|---|
| `specification/standards/RELEASE.md` | `GENESIS_BOOTLOADER.md` → `GTL_BOOTLOADER.md` + `SDLC_BOOTLOADER.md` |
| `GEMINI.md` | Updated bootloader file reference |
| `builds/claude_code/.claude-plugin/.../gen-iterate.md` | Was already correct |

### Fixed (ABG source files — abiogenesis repo):
| File | Change |
|---|---|
| `builds/claude_code/code/gtl_spec/packages/genesis_core.py:30` | `locator` → `workspace://.genesis/gtl_spec/GTL_BOOTLOADER.md` |
| `builds/claude_code/code/genesis/__main__.py:374` | Comment: `GENESIS_BOOTLOADER §V` → `GTL Bootloader §V` |
| `builds/claude_code/code/genesis/bind.py:457` | Comment: `GENESIS_BOOTLOADER §V` → `GTL Bootloader §V` |
| `builds/claude_code/.claude-plugin/.../gen-start.md:58` | Comment: `GENESIS_BOOTLOADER §V` → `GTL Bootloader §V` |

### Fixed (ABG source — remaining stale refs, session 2):
| File | Change |
|---|---|
| `builds/claude_code/code/gtl_spec/packages/abiogenesis.py:35` | `GENESIS_BOOTLOADER.md` → `GTL_BOOTLOADER.md` |
| `builds/claude_code/code/gtl_spec/packages/project_package.py:38` | `GENESIS_BOOTLOADER.md` → `GTL_BOOTLOADER.md` |
| `builds/codex/code/gtl_spec/packages/genesis_core.py:26` | `GENESIS_BOOTLOADER.md` → `GTL_BOOTLOADER.md` |
| `builds/codex/code/gtl_spec/packages/abiogenesis.py:30` | `GENESIS_BOOTLOADER.md` → `GTL_BOOTLOADER.md` |
| `builds/claude_code/tests/test_e2e_sandbox.py:69,86` | `GENESIS_BOOTLOADER.md` → `GTL_BOOTLOADER.md` (sandbox file + context locator) |
| `builds/claude_code/tests/test_commands.py:35` | `GENESIS_BOOTLOADER.md` → `GTL_BOOTLOADER.md` (test fixture context locator) |

### NOT fixed (cosmetic only — no runtime impact):
| File | Reference |
|---|---|
| `builds/claude_code/design/adrs/ADR-014` | Prose reference to `GENESIS_BOOTLOADER §VII` — cosmetic, does not affect runtime |

Note: `gen-install.py` references to `GENESIS_BOOTLOADER_START/END` markers are **correct** — they are the legacy migration code that detects and removes old markers. Do not change those.

### NOT yet fixed (installed territories — will be fixed by reinstall):
| Installed file | Source that fixes it |
|---|---|
| `.genesis/gtl_spec/packages/genesis_core.py` | Already fixed in ABG source |
| `.genesis/genesis/__main__.py` | Already fixed in ABG source |
| `.genesis/genesis/bind.py` | Already fixed in ABG source |
| `.gsdlc/release/workflows/.../spec.py` | Source `sdlc_graph.py` is already correct |
| `.gsdlc/release/operating-standards/RELEASE.md` | Source `specification/standards/RELEASE.md` is already fixed |
| `.claude/commands/gen-start.md` | Source in ABG is already fixed |
| `.claude/commands/gen-iterate.md` | Source in GSDLC already correct |

### GSDLC source `sdlc_graph.py` — already correct

`builds/python/src/genesis_sdlc/sdlc_graph.py` already uses the split model:
```python
gtl_bootloader = Context(name="gtl_bootloader", locator="workspace://.genesis/gtl_spec/GTL_BOOTLOADER.md", ...)
sdlc_bootloader = Context(name="sdlc_bootloader", locator="workspace://.gsdlc/release/SDLC_BOOTLOADER.md", ...)
```

But the **installed** workflow spec (`.gsdlc/release/workflows/.../spec.py`) still has the old monolithic `bootloader` context pointing to `GENESIS_BOOTLOADER.md`. The installed copy diverges from source because `spec.py` is generated by the installer's workflow release step, not a direct copy of `sdlc_graph.py`. Reinstalling GSDLC will regenerate it from the correct source.

## To propagate all fixes

```bash
# 1. In abiogenesis — commit the source fixes
cd /Users/jim/src/apps/abiogenesis
# (remaining ABG stale refs in abiogenesis.py, project_package.py, codex build, tests should be fixed first)

# 2. Reinstall ABG into genesis_sdlc
cd /Users/jim/src/apps/genesis_sdlc
python /Users/jim/src/apps/abiogenesis/builds/claude_code/code/gen-install.py --target .

# 3. Reinstall GSDLC into itself
python builds/python/src/genesis_sdlc/install.py --source . --target .

# 4. Cascade to all dependents
# (each dependent gets: python builds/python/src/genesis_sdlc/install.py --source /path/to/genesis_sdlc --target /path/to/dependent)
```

## Trustworthiness assessment (Codex-reviewed)

A fix is trustworthy only if all three are true:
1. It exists in source under `builds/`
2. It is committed
3. The installed artifact is reproduced from the installer and matches source

| Fix domain | In source | Committed | Installed matches | Status |
|---|---|---|---|---|
| GSDLC Python-builder (sdlc_graph.py, install.py) | Yes | Yes (80acacc, e625846) | Yes | **Permanent** |
| ABG runtime-contract discovery (__main__.py, commands.py) | Yes | Yes (f63d95d) | Yes | **Permanent** |
| ABG bootloader locator (genesis_core.py) | Yes | **No** — uncommitted working tree | **No** — installed copy stale | **Needs commit + cascade** |
| ABG engine comments (__main__.py, bind.py) | Yes | **No** — uncommitted working tree | **No** — installed copy stale | **Needs commit + cascade** |
| ABG gen-start.md command | Yes | **No** — uncommitted working tree | **No** — installed copy stale | **Needs commit + cascade** |
| ABG package locators (abiogenesis.py, project_package.py) | Yes | **No** — uncommitted working tree | N/A | **Needs commit + cascade** |
| ABG codex build packages (genesis_core.py, abiogenesis.py) | Yes | **No** — uncommitted working tree | N/A | **Needs commit + cascade** |
| ABG test fixtures (test_e2e_sandbox.py, test_commands.py) | Yes | **No** — uncommitted working tree | N/A | **Needs commit** |

### To close the loop on ABG:
1. ~~Fix remaining stale refs in ABG source~~ — **Done** (session 2)
2. Commit all ABG source fixes in the abiogenesis repo
3. Reinstall ABG into genesis_sdlc (and into abiogenesis itself)
4. Verify installed copies match source

**Do not trust abiogenesis's installed `.genesis/` until recascaded from committed source.**

## Error made during this session

The agent initially edited `.genesis/`, `.gsdlc/release/`, and `.claude/commands/` directly — all installed territories. These edits were reverted via `git checkout`. The correct approach is always: fix source → commit → reinstall → installed files update as a consequence.

## Related context

- `20260321T120000_REVIEW_bootloader-drift-fixed-asset-proposal.md` — proposed making bootloaders first-class graph assets so they stay current via F_D evaluation rather than manual maintenance. Not yet implemented.
- `20260320T183000_REVIEW_bootloader-split-completed.md` — documents the original split
- User intent: bootloaders should be a synthesis of operating model + specification + design, optimised for LLM context. ABG has `REQ-F-BOOTDOC-*` for this; GSDLC does not yet.
