# REVIEW: GCC Bootstrap Boundary — Resolved

**Author**: Claude Code
**Date**: 2026-03-20T15:00:00Z
**Resolves**: `20260320T120000_GAP_gcc-bootstrap-boundary-violation.md`
**For**: all

## What the GAP identified

The running engine (GCC 1.0) was reading `gtl_spec/packages/genesis_sdlc.py` — a live-editable near-duplicate of the build source at `builds/python/src/genesis_sdlc/sdlc_graph.py`. The compiler being built was rewriting the compiler being run.

## How it was resolved

### Structural fixes

1. **Deleted `gtl_spec/packages/genesis_sdlc.py`** — the GCC 2.0 duplicate. No code references it; the engine uses `project_package.py`.
2. **Moved `gtl_spec/` under `.genesis/`** — it's the installed compiler's spec entry point, not an editable project root artifact. The engine resolves it via `PYTHONPATH=.genesis`.
3. **Four-territory model** — every file in the repo now lives in exactly one territory with clear access semantics.

### The four territories

| Territory | Access | What lives there |
|-----------|--------|-----------------|
| `.genesis/` | **Write-once** (installer deposits, never edited) | Engine, gtl_spec, workflows — GCC 1.0 |
| `.ai-workspace/` | **Read-write** (runtime) | Events, features, reviews, overrides |
| `specification/` | **Read-only** (human-authored axioms) | Intent, requirements, standards |
| `builds/` | **Read-write** (agents build here) | GCC 2.0 source |

### The installer as constitutional enforcer

The installer is now the mechanism that creates and enforces this boundary:

- **Creates** the four-territory structure on install
- **Deposits** GCC 1.0 into `.genesis/` (engine + gtl_spec + workflows)
- **Generates** the Layer 3 wrapper pointing to the installed release version
- **Validates** the boundary with `--audit` — content-hash verification of every installed artifact against the release source

The `--audit` flag checks 20 components across 11 categories:
- Workflow release content hash
- Active workflow version + module pointer
- Command content hashes (5 commands)
- Command stamp version
- Operating standard content hashes (6 standards)
- CLAUDE.md bootloader block content hash
- genesis.yml package/worker import resolution
- Layer 3 wrapper template match
- Manifest version
- Immutable spec shim content hash

### The GCC test — now passing

> Can I edit `builds/python/src/genesis_sdlc/sdlc_graph.py` without affecting my current `gen-gaps` output?

**Yes.** The engine reads from `.genesis/gtl_spec/packages/project_package.py` which imports from `.genesis/workflows/genesis_sdlc/standard/v0_3_0/spec.py`. The build source is just source code.

> Can I run `--audit` at any time to verify the install is correct?

**Yes.** `python -m genesis_sdlc.install --target . --audit` returns structured JSON with per-component status.

## Recommended actions (GAP checklist)

| GAP recommendation | Status |
|--------------------|--------|
| 1. genesis.yml points at installed Package in .genesis/ | **Done** — via project_package.py → .genesis/workflows/ |
| 2. Remove genesis_sdlc.py from gtl_spec/ | **Done** — deleted |
| 3. Document as self-hosting boundary rule | **Done** — this post + audit post |
| 4. V1 close-out item | **In progress** — cascade install for v0.4.0 still pending |

## What remains

- **Cascade install** for v0.4.0 against genesis_sdlc itself (resolves all remaining drift)
- **Installer update** to place `gtl_spec/` under `.genesis/` for downstream projects too (future release)
- **Specification templates** — installer should scaffold `specification/` with starter INTENT.md, requirements.md (future release)
