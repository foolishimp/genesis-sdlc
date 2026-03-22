# SCHEMA: ABG App Runtime Contract And GSDLC Bootstrap

**Author**: Codex
**Date**: 2026-03-22T11:01:13+11:00
**Addresses**: app-vs-sdk boundary, `.gsdlc` runtime binding, workflow provenance loading
**For**: claude

## Summary
The correct fix is not to make the engine “search `.gsdlc` first.” That would just hardcode one domain into the engine and kick the same problem down the road.

The cleaner model is:
- `abg.sdk` stays domain-blind
- `abg.app` consumes a configured runtime contract
- `gsdlc.installer` writes that contract

The current break exists because the app runtime contract is too small for a domain-installed workflow release.

## Problem Statement

Right now the system has three layers, but only two of them are properly separated:

- `abg.sdk`
  - primitives
  - bind/schedule/iterate/project
  - no domain knowledge

- `abg.app`
  - `python -m genesis`
  - CLI argument parsing
  - config loading
  - package/worker resolution
  - workflow/provenance loading

- `gsdlc`
  - domain methodology
  - workflow release
  - wrapper generation
  - installer/bootstrap

The bug is that `abg.app` still assumes old filesystem locations:
- `.genesis/active-workflow.json`
- `.genesis/workflows/...`

But `gsdlc.installer` now writes:
- `.gsdlc/release/active-workflow.json`
- `.gsdlc/release/workflows/...`

So the app is reading stale territory assumptions while the installer is writing a newer runtime layout.

## What Not To Do

Do **not** patch the engine with:

- “check `.gsdlc` first, then `.genesis`”
- “if `.gsdlc` exists, prefer that”

That is only a territory-specific search hack. It bakes `gsdlc` into the engine and does not solve the architectural problem.

If another domain package later installs its own release territory, the same problem returns.

## Correct Model

### 1. `abg.sdk`

The SDK should know nothing about:
- `.gsdlc`
- workflow names
- wrapper layout
- install territories
- project slugs

It should only expose execution primitives and explicit inputs:
- package
- worker
- workspace root
- workflow version
- carry-forward / provenance context

### 2. `abg.app`

The app is the runtime shell over the SDK. It is allowed to read filesystem config and launch the SDK.

Its job is:
- load runtime config
- add configured `pythonpath`
- resolve package and worker
- resolve workflow/provenance metadata
- call the SDK

This is where territory awareness belongs.

### 3. `gsdlc`

`gsdlc` is a domain installer/builder over the app.

Its job is:
- install `.gsdlc/release`
- install wrapper/workflow release
- write the runtime contract the app consumes
- keep the app configured against the installed `gsdlc` release

## The Missing Runtime Contract

Right now `abg.app` effectively reads only:

```yaml
package: gtl_spec.packages.<slug>:package
worker: gtl_spec.packages.<slug>:worker
pythonpath:
  - .gsdlc/release
```

That is no longer enough.

The app also needs to know where workflow metadata lives.

A fuller runtime contract should look like:

```yaml
package: gtl_spec.packages.abiogenesis:package
worker: gtl_spec.packages.abiogenesis:worker
pythonpath:
  - .gsdlc/release

active_workflow: .gsdlc/release/active-workflow.json
workflow_root: .gsdlc/release/workflows
release_root: .gsdlc/release
```

Then:
- `gsdlc.installer` writes this contract
- `abg.app` reads this contract
- `abg.sdk` remains unaware of the territory layout

## ABG App Entry Points

These are the actual app entry points that must become contract-driven:

### 1. `gsdlc.installer`

This is the bootstrap origin.

It must:
- call `abg.installer`
- install `.gsdlc/release`
- write the app runtime contract into `.genesis/genesis.yml`
- ensure commands and bootloader documents reflect the installed runtime

### 2. Fresh Claude Session

A fresh session uses installed slash commands and bootloader guidance.

If installer-written config is wrong, every new session starts from a bad runtime contract.

### 3. `python -m genesis gaps|start|iterate`

This is the main app entrypoint.

It currently:
- reads `.genesis/genesis.yml`
- adds `pythonpath`
- resolves package/worker
- constructs `Scope`

It must also read workflow/provenance paths from config rather than hardcoding them.

### 4. `python -m genesis emit-event`

This is a pre-stack app entrypoint.

It currently reads workflow version directly from old territory assumptions.

It must use the same configured runtime contract as the rest of the app.

### 5. Provenance Helpers In Command Layer

These are currently the exact hardcoded seam:
- `_read_workflow_version()`
- `_read_carry_forward()`

They should stop assuming:
- `.genesis/active-workflow.json`
- `.genesis/workflows/...`

and instead use the configured locations provided by the app contract.

### 6. Installed Package Resolution

The wrapper in `.gsdlc/release/gtl_spec/packages/<slug>.py` is part of the domain release.

The app should not know its territory by name. It should only know:
- what module to import
- what `pythonpath` to add

### 7. Slash Command Surface

`.claude/commands/*.md` is the human/agent-facing adapter layer over the app.

These docs must match the real runtime contract and invocation model.

## Boot Sequence

The clean boot sequence is:

1. `gsdlc.installer`
   - calls `abg.installer`
   - writes `.gsdlc/release`
   - writes the full runtime contract into `.genesis/genesis.yml`

2. Fresh session starts
   - slash command invokes `python -m genesis ...`

3. `abg.app`
   - reads `.genesis/genesis.yml`
   - adds configured `pythonpath`
   - resolves package/worker
   - reads configured workflow/provenance paths
   - executes the SDK against the installed domain release

This keeps roles clean:
- installer writes contract
- app consumes contract
- sdk executes work

## Recommended Action

1. Do not patch the engine with a `.gsdlc`-specific search order.
2. Extend the `abg.app` runtime contract so it includes workflow/provenance locations, not just package/worker/pythonpath.
3. Make `gsdlc.installer` the writer of that contract.
4. Retarget:
   - app config loading
   - `emit-event`
   - `_read_workflow_version()`
   - `_read_carry_forward()`
   to use the configured runtime contract.
5. Keep `.gsdlc` out of the SDK entirely.
