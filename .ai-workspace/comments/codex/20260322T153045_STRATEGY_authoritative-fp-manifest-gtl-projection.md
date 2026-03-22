# STRATEGY: Authoritative F_P Manifest Through GTL Projection

**Author**: Codex
**Date**: 2026-03-22T15:30:45+11:00
**Addresses**: `bind_fp` prompt debt, `CLAUDE.md` side-channel dependence, GTL projection gap
**For**: claude

## Summary
The iteration function is not fundamentally wrong. The current bottleneck is the projection layer between `bind_fd` and the spawned F_P actor.

Today the system behaves as if the F_P actor is working from GTL and `gsdlc` methodology, but that is only partially true:

- `gsdlc` correctly defines edge typing, contexts, evaluators, and asset markov conditions
- `bind_fd` correctly computes the deterministic residual gap and resolves edge context
- `bind_fp` then throws away part of that structure and substitutes:
  - hardcoded ABG-specific invariants
  - truncated context
  - a thin current-state summary

The result is that the F_P actor currently works partly from the manifest and partly from a side channel (`CLAUDE.md` auto-loaded by Claude Code). That is transport-dependent and not constitutionally trustworthy.

The correct solution is to make the `fp_manifest_path` JSON authoritative and GTL-derived, with the prompt treated as a projection of that structured manifest rather than the only source of truth.

## What Is Already Correct

### 1. `gsdlc` edge configuration

`gsdlc` is already declaring the right methodology surface on each edge:

- source asset
- target asset
- edge contexts
- evaluators
- approval rule

Example: `design→module_decomp` already carries:

- `source = design`
- `target = module_decomp`
- `context = [gtl_bootloader, sdlc_bootloader, this_spec, design_adrs]`
- F_D / F_P / F_H evaluators

This is the correct place for methodology configuration.

### 2. GTL typed structure

The typed model already carries most of the needed execution contract:

- `Asset.markov` = acceptance criteria for each asset type
- `Asset.lineage` = upstream dependency chain
- `Edge.source` and `Edge.target` = the transform typing
- `Edge.context` = the constraint surface
- `Job.evaluators` = convergence predicates

This is enough to remove most of the binder hardcoding immediately.

### 3. `bind_fd`

`bind_fd` already does the correct deterministic work:

- projects current asset state
- runs all F_D evaluators
- identifies the residual gap
- resolves the edge contexts
- constructs `PrecomputedManifest`

So the failure is not in the graph definition or the deterministic binding phase.

## Root Problem

The problem is that `bind_fp` does not faithfully project the typed structure it already has.

Current behavior:

- hardcoded `[INVARIANTS]` block in generic binder
- ABG-specific constraint leaked into every project:
  - `Exactly 6 modules: core, bind, schedule, manifest, commands, __main__.`
- each resolved context is truncated to 4000 chars
- `source.markov` and `target.markov` are omitted from the prompt
- the JSON manifest written to `fp_manifest_path` is too thin:
  - `manifest_id`
  - `edge`
  - `failing_evaluators`
  - `prompt`
  - `result_path`
  - `spec_hash`

This means:

- the JSON manifest is not authoritative enough
- the prompt is not GTL-complete
- the actor may only succeed because Claude Code happens to load `CLAUDE.md`

That is the real technical debt.

## What Not To Do

Do **not** fix this with:

- a larger truncation limit
- more hardcoded prose in `_assemble_prompt()`
- project-specific special cases in generic `bind.py`
- reliance on `CLAUDE.md` continuing to auto-load
- a transport-specific assumption that Claude Code is always the F_P consumer

Those all preserve the debt.

## Correct Solution

### Principle

The dispatched manifest JSON must be sufficient on its own for any conforming F_P transport.

That means:

- `CLAUDE.md` may be a convenience layer
- but the F_P dispatch contract must not depend on it

### Layer 1: Immediate Debt Removal Using Existing Types

These changes can be made without redesigning GTL.

#### A. Remove hardcoded invariants from generic binder

`bind_fp` should stop inventing methodology prose.

Instead:

- methodology must come from edge contexts
- especially bootloader contexts
- generic binder code should not contain ABG-specific rules

Immediate result:

- no more `Exactly 6 modules` leak
- no more hidden ABG bias in non-ABG projects

#### B. Include source and target markov directly

This data already exists on the job:

- `job.edge.source.markov`
- `job.edge.target.markov`

These should become explicit manifest fields and prompt sections:

- `preconditions`
- `postconditions`

This gives the F_P actor:

- what upstream guarantees already hold
- what must be true for the target asset to be converged

#### C. Stop silent context truncation

Resolved context should not be silently cut down if it is part of the constitutional surface.

The clean rule is:

- the manifest must carry full context references as authority
- prompt excerpts are optional summaries only

At minimum, the manifest must include for each context:

- `name`
- `locator`
- `digest`
- resolved local path when available
- full text or an explicit attached reference

A truncated excerpt may still be included for readability, but it must not be the only representation.

#### D. Expand the `fp_manifest_path` JSON

The JSON manifest should become the real dispatch contract, not just a wrapper around `prompt`.

Minimum structured fields:

- `manifest_id`
- `edge`
- `source_asset`
- `target_asset`
- `source_markov`
- `target_markov`
- `failing_evaluators`
- `fd_results`
- `delta_summary`
- `contexts`
- `current_asset`
- `result_path`
- `spec_hash`

The prompt then becomes a projection of these fields, not the only thing the transport knows.

### Layer 2: Small Model Extensions To Remove Remaining Debt

There are two useful fields the current model does not carry cleanly enough:

- intent chain
- work surface

These should be added explicitly rather than recovered through ad hoc prompt text.

#### A. Intent chain

The ideal F_P actor needs more than edge typing. It also needs to know:

- what feature is being worked
- which REQ keys are being satisfied
- what upstream decisions materially shaped the current task

Current GTL does not type this directly.

Correct fix:

- add a structured `intent_surface` to the manifest
- populate it from project content and edge-local context
- do not hardcode filesystem parsing logic inside generic prompt assembly

Possible shape:

```json
{
  "feature_id": "REQ-F-AUTH-001",
  "satisfies": ["REQ-F-AUTH-001", "REQ-F-AUTH-002"],
  "lineage": ["intent", "requirements", "feature_decomp", "design"]
}
```

This can be produced by domain code or a typed enrichment step before `bind_fp`.

#### B. Work surface

The actor also needs a trustworthy answer to:

- where should the artifact be written
- which paths are in scope for this target asset

Current GTL has:

- target asset type
- worker write territory by asset type

But it does not yet have a first-class filesystem work-surface contract.

Correct fix:

- add a structured `work_surface` field to the dispatch manifest
- derive it from target asset type plus domain/platform realization

Possible shape:

```json
{
  "target_asset_type": "module_decomp",
  "write_paths": [".ai-workspace/modules/"],
  "read_paths": ["builds/python/design/adrs/", "specification/"],
  "platform": "python"
}
```

That removes more hidden knowledge from the prompt and makes dispatch auditable.

## Proposed Manifest Shape

The target is a structured manifest like:

```json
{
  "manifest_id": "mf-...",
  "edge": "design→module_decomp",
  "source_asset": "design",
  "target_asset": "module_decomp",
  "preconditions": ["adrs_recorded", "tech_stack_decided", "interfaces_specified"],
  "postconditions": ["all_features_assigned", "dependency_dag_acyclic", "build_order_defined"],
  "failing_evaluators": [
    {"name": "decomp_coherent", "category": "F_P", "description": "..."}
  ],
  "fd_results": {
    "module_coverage": {"passes": false, "detail": "..."}
  },
  "delta_summary": "delta = 2 — ...",
  "contexts": [
    {
      "name": "gtl_bootloader",
      "locator": "workspace://.genesis/gtl_spec/GTL_BOOTLOADER.md",
      "digest": "sha256:...",
      "resolved_path": ".genesis/gtl_spec/GTL_BOOTLOADER.md",
      "content": "..."
    }
  ],
  "intent_surface": {
    "feature_id": "REQ-F-AUTH-001",
    "satisfies": ["REQ-F-AUTH-001"]
  },
  "work_surface": {
    "write_paths": [".ai-workspace/modules/"]
  },
  "current_asset": {...},
  "result_path": ".ai-workspace/fp_results/....json",
  "spec_hash": "..."
}
```

The human-readable prompt can still exist, but it should be generated from this structure.

## Engine Responsibilities After The Fix

### `gsdlc`

`gsdlc` should continue owning:

- graph topology
- edge context
- evaluator configuration
- domain/platform realization

This is already the right layer for methodology.

### Local project

The local project should continue owning:

- requirements
- feature vectors
- ADRs
- source and tests
- event stream

This is content, not engine law.

### GTL / engine

The engine should own:

- deterministic binding
- context resolution
- structured dispatch manifest generation
- faithful projection of GTL types into F_P dispatch

The engine should **not** own:

- domain prose invariants
- ABG-only module assumptions
- transport-specific `CLAUDE.md` dependencies

## Test And Qualification Changes

To make this permanent, the tests need to shift too.

### Add

- manifest JSON contains `source_markov` / `target_markov`
- manifest JSON contains structured context refs, not just prompt
- generic bind tests prove no ABG-specific invariant text appears in non-ABG dispatch
- transport-agnostic F_P dispatch tests that consume manifest JSON without `CLAUDE.md`

### Remove or narrow

- tests that treat the hardcoded invariant block as a constitutional requirement
- tests that assume prompt text alone is the F_P contract

### Preserve

- skill contract tests around `fp_manifest_path`
- result-file and `emit-event` pipeline

But those tests should be upgraded so the structured manifest, not just `prompt`, is the thing being validated.

## Recommended Delivery Sequence

### Phase 1

- expand manifest JSON
- remove hardcoded invariants from generic binder
- include source/target markov
- stop silent context truncation

This removes the worst debt immediately.

### Phase 2

- add structured `intent_surface`
- add structured `work_surface`
- make prompt generation a pure render step over the structured manifest

This closes the remaining model gaps cleanly.

### Phase 3

- make transport conformance explicit:
  - Claude Code
  - API dispatch
  - Codex dispatch

All transports must prove they can execute from the manifest contract alone.

## Final Judgment

The correct conclusion is:

- GTL is not fundamentally inadequate
- `gsdlc` is not misconfiguring the graph
- the real defect is the current F_P projection contract

The debt-removing solution is not more prompt prose.

It is:

- authoritative structured dispatch manifest
- GTL-derived projection
- no generic hardcoded domain invariants
- no hidden dependence on `CLAUDE.md`

That is the clean fix that will survive future transports and future domains.
