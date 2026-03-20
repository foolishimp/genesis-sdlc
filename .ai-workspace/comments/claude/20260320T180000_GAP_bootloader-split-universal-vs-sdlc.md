# GAP: Single bootloader conflates universal axioms with SDLC instantiation

**Date**: 2026-03-20
**Severity**: Architectural — a non-SDLC GTL project would inherit SDLC constraints that don't apply

---

## Problem

One `GENESIS_BOOTLOADER.md` (527 lines) serves two purposes:

1. **Universal formal system** (I–XI): Four primitives, iterate(), event stream, gradient, evaluators, sensory systems, IntentEngine, tolerances, asset stability. Domain-agnostic — applies to any GTL Package.

2. **SDLC instantiation** (XII–XXI): Completeness visibility via feature vectors and REQ keys, the SDLC graph topology, profiles, spec/design separation, invariants table, workspace territory, bug triage. Applies only to genesis_sdlc projects.

A non-SDLC project (e.g. a chatbot, data pipeline, or infrastructure project using GTL) would get 200+ lines of SDLC-specific constraints that don't apply and would actively mislead the LLM.

Section XXI ("Abiogenesis Project — Local Write Territory Amendment") is project-specific to abiogenesis itself — it shouldn't be in either bootloader.

## Resolution

Split into two bootloaders with clear ownership:

| Document | Owner | Content | Sections |
|----------|-------|---------|----------|
| `GTL_BOOTLOADER.md` | abiogenesis | Universal formal system — four primitives, event stream, gradient, evaluators | I–XI |
| `SDLC_BOOTLOADER.md` | genesis_sdlc | SDLC instantiation — graph, features, profiles, workspace, bug triage | XII–XX |

The gsdlc installer composes both into CLAUDE.md: `GTL_BOOTLOADER + SDLC_BOOTLOADER`.
Section XXI moves to abiogenesis's CLAUDE.md template as a project-local amendment.

## Why the split is clean at section XII

- Sections I–XI contain zero SDLC references. They define the formal system in purely abstract terms.
- Section XII is where "feature decomposition", "REQ-* keys", and "feature vectors" first appear.
- A future non-SDLC Package would use its own domain bootloader instead of SDLC_BOOTLOADER.md, while keeping GTL_BOOTLOADER.md unchanged.
