# REVIEW: genesis_sdlc Structural Self-Audit — v0.4.0

**Author**: Claude Code
**Date**: 2026-03-20T14:00:00Z
**Scope**: Full repo structure, every file and directory justified
**For**: all

---

## Methodology

Enumerated every file in the repo (excluding `.git/`, `__pycache__/`). Each item classified as:
- **Axiom** — constitutional source, read-only normative surface
- **Build source** — GCC 2.0 being developed
- **Install artifact** — GCC 1.0 deployed by installer, regenerated on cascade
- **Workspace state** — runtime event stream, features, reviews
- **Documentation** — user-facing, non-normative
- **Structural** — config, gitignore, agent constraints

---

## Directory-Level Audit

### `specification/` — Axiom (DNA)

| File | Verdict | Notes |
|------|---------|-------|
| `INTENT.md` | **CORRECT** | Three intents (INT-001, INT-002, INT-003). Axiomatic. |
| `requirements.md` | **CORRECT** | 31 REQ keys with acceptance criteria. Traces to intents. |
| `feature_decomposition.md` | **CORRECT** | 14 features, dependency DAG, module mapping. |
| `standards/BACKLOG.md` | **CORRECT** | Backlog item format standard. |
| `standards/CONVENTIONS.md` | **CORRECT** | Design marketplace post format. |
| `standards/RELEASE.md` | **CORRECT** | Release process. Source of truth for installed copy. |
| `standards/SPEC.md` | **CORRECT** | Spec writing standard — disambiguation pipeline. |
| `standards/USER_GUIDE.md` | **CORRECT** | User guide writing standard. |
| `standards/WRITING.md` | **CORRECT** | General writing standard. |

**Verdict**: Clean. This is the axiomatic ontology. Homeostasis starts here.

---

### `builds/python/` — Build Source (GCC 2.0)

| File | Verdict | Notes |
|------|---------|-------|
| `src/genesis_sdlc/__init__.py` | **CORRECT** | Package init, `__version__ = "0.4.0"` |
| `src/genesis_sdlc/sdlc_graph.py` | **CORRECT** | The Package — typed asset graph, REQ key registry |
| `src/genesis_sdlc/install.py` | **CORRECT** | Cascade installer, VERSION 0.4.0 |
| `src/genesis_sdlc/backlog.py` | **CORRECT** | Backlog management module |
| `src/genesis_sdlc/RELEASE.md` | **QUESTION** | Quick-reference cascade doc (48 lines). Overlaps with `specification/standards/RELEASE.md` (197 lines). Different content — this is a dev-facing cheat sheet. Tolerable but creates a maintenance surface. |
| `tests/test_sdlc_graph.py` | **CORRECT** | Graph topology tests |
| `tests/test_installer.py` | **CORRECT** | Installer idempotency, migration, layer tests |
| `tests/test_e2e_sandbox.py` | **CORRECT** | E2E sandbox — runs GCC 2.0 as compiler |
| `tests/test_gaps.py` | **CORRECT** | Gap/convergence evaluator tests |
| `tests/test_backlog.py` | **CORRECT** | Backlog module tests |
| `tests/__init__.py` | **CORRECT** | Package marker |
| `pyproject.toml` | **CORRECT** | Package metadata, version 0.4.0 |
| `CHANGELOG.md` | **CORRECT** | Release history with spec_hash |
| `design/adrs/ADR-001..007` | **CORRECT** | Immutable architectural decisions |
| `uat_sandbox/` | **CORRECT** | E2E test fixture. Gitignored. Not tracked. |

**Verdict**: Clean. Single source of truth for the standard library.

---

### `builds/claude_code/` — Build Source (Agent Commands)

| File | Verdict | Notes |
|------|---------|-------|
| `.claude-plugin/plugin.json` | **CORRECT** | Plugin manifest, inherits abiogenesis |
| `.claude-plugin/.../gen-iterate.md` | **CORRECT** | Source for gen-iterate command |
| `.claude-plugin/.../gen-review.md` | **CORRECT** | Source for gen-review command |
| `.claude-plugin/.../config/edge_params/` | **EMPTY** | V2+ extensibility point. Intentional. |
| `.claude-plugin/.../hooks/` | **EMPTY** | V2+ extensibility point. Intentional. |

**Verdict**: Clean. Two commands authored here; three inherited from abiogenesis.

---

### `builds/codex/`, `builds/gemini/`, `builds/gemini_cloud/` — Empty Build Territories

| Directory | Verdict | Notes |
|-----------|---------|-------|
| `builds/codex/` | **EMPTY** | V2+ Codex build territory. Not tracked in git. |
| `builds/gemini/` | **EMPTY** | V2+ Gemini build territory. Not tracked in git. |
| `builds/gemini_cloud/` | **EMPTY** | V2+ Gemini Cloud territory. Not tracked in git. |

**Verdict**: Intentional placeholders. Not tracked. No action needed.

---

### `gtl_spec/` — Install Artifact (GCC 1.0 Entry Point)

| File | Verdict | Notes |
|------|---------|-------|
| `__init__.py` | **CORRECT** | Package marker |
| `GENESIS_BOOTLOADER.md` | **CORRECT** | Bootloader v3.1.0 — source of truth for all embedded copies |
| `packages/__init__.py` | **CORRECT** | Package marker |
| `packages/project_package.py` | **CORRECT** | System-owned wrapper → imports from `.genesis/workflows/.../v0_3_0/spec.py`. Regenerated on cascade. |
| `packages/genesis_core.py` | **CORRECT** | Abiogenesis Package spec. Installed by abg engine. Not ours. |
| ~~`packages/genesis_sdlc.py`~~ | **DELETED** | Removed in this session. Was a GCC 2.0 duplicate causing bootstrap boundary confusion. |

**Verdict**: Clean after today's fix. `project_package.py` correctly routes engine to GCC 1.0.

---

### `.genesis/` — Installed Compiler (GCC 1.0)

25 files tracked in git. Contains:
- `genesis/` — abiogenesis engine (core.py, commands.py, bind.py, etc.)
- `gtl/` — GTL type system (core.py)
- `spec/genesis_sdlc.py` — backwards-compat shim
- `workflows/genesis_sdlc/standard/v0_2_0/`, `v0_2_1/`, `v0_3_0/` — versioned releases
- `genesis.yml` — engine config pointing to `gtl_spec.packages.project_package`
- `active-workflow.json` — runtime state

| Finding | Severity | Notes |
|---------|----------|-------|
| `.genesis/` is tracked in git | **INFO** | For genesis_sdlc (self-hosting), this makes sense — the bootstrap compiler IS the product. For downstream projects, `.genesis/` is typically `.gitignore`d. |
| No `v0_4_0` workflow installed | **EXPECTED** | Cascade install hasn't been run for v0.4.0 yet. GCC 1.0 is still v0.3.0. |
| `spec/genesis_sdlc.py` locator points to deleted file | **STALE** | `locator="workspace://gtl_spec/packages/genesis_sdlc.py"` — file no longer exists. This is in the installed GCC 1.0, so it will be corrected on next cascade install. Not a runtime error (locators are metadata, not imports). |

**Verdict**: Correct for GCC 1.0. Will update to v0.4.0 on cascade install.

---

### `.claude/commands/` — Install Artifact (Deployed Commands)

| File | Verdict | Notes |
|------|---------|-------|
| `gen-start.md` | **STALE** | Installed by abiogenesis. Source is in abg repo. |
| `gen-gaps.md` | **STALE** | Same. |
| `gen-status.md` | **STALE** | Same. |
| `gen-iterate.md` | **DRIFTED** | Still has `fp_assessment`, `review_approved`. Source updated to `assessed`, `approved`. |
| `gen-review.md` | **DRIFTED** | Same drift. |
| `.genesis-installed` | **CORRECT** | Stamp file. |

**Verdict**: All five commands are stale — need cascade install to sync with v0.4.0 sources.

---

### `.ai-workspace/` — Workspace State

| Directory | Status | Notes |
|-----------|--------|-------|
| `events/events.jsonl` | **ACTIVE** | 278 events. Canonical control surface. |
| `features/completed/` (15 YAMLs) | **CORRECT** | All features converged. No active features. |
| `features/active/` | **EMPTY** | All work converged. Correct. |
| `comments/claude/` (24 posts) | **CORRECT** | Design marketplace — active intellectual record. |
| `comments/codex/` (4 posts) | **CORRECT** | Codex review contributions. |
| `backlog/` (12 items) | **CORRECT** | V2+ incubation queue. |
| `modules/` (1 YAML) | **CORRECT** | MOD-001 binding. |
| `reviews/pending/` | **EMPTY** | No outstanding F_H gates. Correct. |
| `reviews/proxy-log/` (7 logs) | **CORRECT** | Audit trail for `--human-proxy` decisions. |
| `operating-standards/` (6 files) | **DRIFTED** | RELEASE.md has old event names. Source updated. |
| `fp_manifests/`, `fp_results/` | **GITIGNORED** | Trace surface. Present on disk, not tracked. Correct. |
| `uat/sandbox_report.json` | **CORRECT** | Last sandbox health signal. |
| `agents/`, `context/`, `claims/` | **EMPTY** | V2+ reserved territories. Intentional. |

**Verdict**: Workspace is healthy. One drifted standard (RELEASE.md) needs cascade install.

---

### Root Files

| File | Verdict | Notes |
|------|---------|-------|
| `CLAUDE.md` | **DRIFTED** | Embeds bootloader v3.0.2; source is v3.1.0. Cascade install will regenerate. |
| `AGENTS.md` | **CORRECT** | Codex constraints — reviewer-only, territory-bound. |
| `GEMINI.md` | **CORRECT** | Gemini constraints — reviewer-only, territory-bound. |
| `.gitignore` | **CORRECT** | Excludes `__pycache__/`, `.venv/`, fp_manifests, fp_results, uat_sandbox. |

---

### `docs/` — Documentation

| File | Verdict | Notes |
|------|---------|-------|
| `USER_GUIDE.md` | **CORRECT** | Comprehensive user guide. Updated today with GCC boundary language. |
| `CHATBOT_WALKTHROUGH.md` | **CORRECT** | Worked example — chatbot built with genesis_sdlc. |
| `presentations/USER_GUIDE.pdf` | **QUESTION** | Binary PDF tracked in git. Generated from USER_GUIDE.md? If so, should be regenerated, not tracked. If hand-authored, legitimate. |
| `presentations/CHATBOT_WALKTHROUGH.pdf` | **QUESTION** | Same question. |

---

## Findings Summary

### Critical (blocks correctness)

None.

### Drift (resolved by cascade install)

| Item | Source | Installed | Delta |
|------|--------|-----------|-------|
| `.claude/commands/gen-iterate.md` | `assessed`, `approved` (v0.4.0) | `fp_assessment`, `review_approved` (v0.3.0) | Event names |
| `.claude/commands/gen-review.md` | `approved` (v0.4.0) | `review_approved` (v0.3.0) | Event names |
| `.ai-workspace/operating-standards/RELEASE.md` | Updated paths + event names | Old paths + event names | 4 lines |
| `CLAUDE.md` bootloader | v3.1.0 | v3.0.2 embedded | Version + event names |
| `project_package.py` | Should import v0_4_0 | Imports v0_3_0 | Version |
| `.genesis/workflows/` | Should have v0_4_0 | Only has v0_2_0, v0_2_1, v0_3_0 | Missing version |

**All six are resolved by running cascade install for v0.4.0.** This is the expected state — v0.4.0 was committed and tagged but cascade install was not yet run against genesis_sdlc itself.

### Resolved During Audit

| # | Decision | Action Taken |
|---|----------|-------------|
| Q1 | `builds/python/src/genesis_sdlc/RELEASE.md` redundant — `specification/standards/RELEASE.md` is the single standard | **Deleted** |
| Q2 | `docs/presentations/*.pdf` — generated from MDs but user wants them tracked for distribution (email, non-MD-friendly contexts) | **Kept** |
| Q3 | `gtl_spec/` moved under `.genesis/` — it's the installed compiler's spec entry point, not editable project root | **Moved** via `git mv gtl_spec/ .genesis/gtl_spec/` |

### Architectural Clarification: The Four-Territory Model

Resolved during audit — the project has exactly four territories with distinct access semantics:

| Directory | Role | Access | Writes by |
|-----------|------|--------|-----------|
| `.genesis/` | Installed compiler (GCC 1.0) — engine, type system, `gtl_spec/`, workflows | **Write-once** (installer only) | Installer |
| `.ai-workspace/` | Runtime state — events, features, reviews, **and project-specific overrides** | **Read-write** | Engine + agents |
| `specification/` | Axioms — intent, requirements, standards | **Read-only** | Human author |
| `builds/` | GCC 2.0 source being developed | **Read-write** | Agents (build) |

**Key insight**: If a project needs to override anything from `gtl_spec/` (Layer 3 customization), those overrides belong in `.ai-workspace/` — the only read-write runtime surface. The installed `gtl_spec/` inside `.genesis/` is immutable. This replaces the prior model where `gtl_spec/` sat at the project root as an editable directory.

**Installer implication**: Future installer versions should place `gtl_spec/` inside `.genesis/` for all projects (not just genesis_sdlc). Layer 3 overrides would be written to `.ai-workspace/` and composed at runtime.

### Installer Output Contract: The Four-Territory Scaffold

The four-territory model defines exactly what the installer should create. A freshly installed project gets the complete structure with starter templates — the developer never has to guess what directories to create.

```
<project>/
├── .genesis/                              ← WRITE-ONCE (installer deposits, never edited)
│   ├── genesis/                           ← abiogenesis engine
│   ├── gtl/                               ← GTL type system
│   ├── gtl_spec/                          ← installed Package entry point
│   │   ├── GENESIS_BOOTLOADER.md          ← bootloader (frozen at release version)
│   │   └── packages/
│   │       ├── <slug>.py                  ← generated wrapper → workflows/
│   │       └── genesis_core.py            ← abiogenesis Package spec
│   ├── workflows/genesis_sdlc/standard/v{VERSION}/
│   │   ├── spec.py                        ← immutable versioned release
│   │   └── manifest.json                  ← version metadata
│   ├── spec/genesis_sdlc.py               ← backwards-compat shim
│   ├── genesis.yml                        ← engine config
│   └── active-workflow.json               ← runtime state
│
├── .ai-workspace/                         ← READ-WRITE (runtime state + overrides)
│   ├── events/events.jsonl                ← canonical event stream (empty on install)
│   ├── features/active/                   ← in-progress feature vectors
│   ├── features/completed/                ← converged features
│   ├── comments/claude/                   ← Claude design marketplace
│   ├── comments/codex/                    ← Codex design marketplace
│   ├── comments/gemini/                   ← Gemini design marketplace
│   ├── reviews/pending/                   ← F_H gate proposals
│   ├── reviews/proxy-log/                 ← human-proxy audit trail
│   ├── backlog/                           ← incubation queue
│   ├── modules/                           ← module decomposition artifacts
│   ├── operating-standards/               ← deployed standards (from specification/)
│   │   ├── BACKLOG.md
│   │   ├── CONVENTIONS.md
│   │   ├── RELEASE.md
│   │   ├── SPEC.md
│   │   ├── USER_GUIDE.md
│   │   └── WRITING.md
│   ├── uat/                               ← UAT health signals
│   ├── context/                           ← shared context (V2+)
│   ├── agents/                            ← agent identity state (V2+)
│   └── claims/                            ← formal assertions (V2+)
│
├── specification/                         ← READ-ONLY (axioms — human fills templates)
│   ├── INTENT.md                          ← starter: "What is this project?"
│   ├── requirements.md                    ← starter: REQ key template with examples
│   ├── feature_decomposition.md           ← starter: feature vector template
│   └── standards/                         ← methodology standards (copied from source)
│       ├── BACKLOG.md
│       ├── CONVENTIONS.md
│       ├── RELEASE.md
│       ├── SPEC.md
│       ├── USER_GUIDE.md
│       └── WRITING.md
│
├── builds/                                ← READ-WRITE (GCC 2.0 — where code gets built)
│   └── python/
│       ├── src/<slug>/
│       │   └── __init__.py                ← starter: package marker
│       ├── tests/
│       │   └── __init__.py                ← starter: test package marker
│       └── design/adrs/                   ← architecture decision records
│
├── docs/                                  ← user-facing documentation
├── CLAUDE.md                              ← generated from bootloader + project instructions
├── AGENTS.md                              ← agent constraints (Codex)
└── GEMINI.md                              ← agent constraints (Gemini)
```

**Current gap**: The installer creates `.genesis/` and `.ai-workspace/` but does NOT scaffold `specification/` or `builds/`. A freshly installed project has a compiler but no axioms and no build directory. The methodology can't start without `specification/INTENT.md` — the `intent → requirements` edge has no input.

**Starter templates**: The `specification/` templates are not empty files. Each carries:
- The file's purpose and what the downstream edge needs
- An example REQ key or intent vector
- A reference back to the methodology standard that governs it

This makes the installer the complete onboarding experience: install, fill in `specification/INTENT.md`, run `/gen-start`.

### Structural Health Scorecard

| Dimension | Score | Notes |
|-----------|-------|-------|
| **Axiom completeness** | 10/10 | Intent, requirements, feature decomp, 6 standards |
| **Build source integrity** | 10/10 | Single source in `builds/python/src/` |
| **GCC boundary** | 9/10 | Fixed today (deleted duplicate). Cascade install pending. |
| **Install artifact freshness** | 6/10 | v0.3.0 installed, v0.4.0 built. Cascade pending. |
| **Workspace health** | 10/10 | 278 events, 15 features converged, 12 backlog items |
| **Documentation** | 9/10 | Comprehensive. PDF tracking question open. |
| **Agent territory** | 10/10 | AGENTS.md, GEMINI.md, territory boundaries enforced |
| **Forward compatibility** | 10/10 | Empty V2+ territories properly reserved |

---

## Recommended Next Step

**Run cascade install** for v0.4.0 against genesis_sdlc itself. This resolves all six drift items in one operation:

```bash
PYTHONPATH=builds/python/src:.genesis python -m genesis_sdlc.install \
  --target . \
  --project-slug genesis_sdlc
```

This is Step 7 of the release process — genesis_sdlc is always first in the cascade.
