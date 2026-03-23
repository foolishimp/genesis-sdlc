# REVIEW: `gsdlc.install` vs Specification and ABG 1.0

**Date**: 2026-03-23T01:01:52+11:00
**Scope**: review of the current Codex-side `genesis_sdlc` installer against:

- the current installer source:
  - `builds/codex/code/genesis_sdlc/install.py`
  - `builds/codex/code/genesis_sdlc/sdlc_graph.py`
- the domain specification:
  - `specification/requirements.md`
- the cleaned `abg 1.0` runtime model

## Executive Summary

Current `gsdlc.install` is still architected against an **old ABG world**.

It is trying to do three jobs at once:

1. install the ABG kernel
2. install the GSDLC domain release
3. scaffold a project workspace

The result is boundary collapse:

- domain artifacts are written into `.genesis/`
- mutable workflow state is written into `.genesis/`
- bootstrap binds directly to installed spec packages under `.genesis/`
- `.gsdlc/release/` is not the authoritative domain release territory the spec describes

The clean `test_install/` snapshot at review time now shows only the **ABG baseline**:

- `.genesis/genesis/`
- `.genesis/gtl/`
- `.ai-workspace/events/`
- `.ai-workspace/runtime/`
- no `.gsdlc/release/`

That is good as a baseline, but it also makes the core problem obvious:

**the current `gsdlc.install` source is not layered on top of ABG 1.0 yet.**

## What the Specification Requires

The current `genesis_sdlc` specification says:

- `.genesis/` is ABG kernel, immutable
- `.gsdlc/release/` is GSDLC methodology, immutable between releases
- `.ai-workspace/` is runtime evidence
- no gsdlc workflow/wrapper/config artifacts belong in `.genesis/`

Key clauses:

- `REQ-F-BOOT-001`:
  - five-territory structure with `.genesis/` for kernel and `.gsdlc/release/` for methodology
- `REQ-F-BOOT-003`:
  - frozen methodology spec goes to `.gsdlc/release/spec/`
- `REQ-F-BOOT-004`:
  - generated wrapper goes to `.gsdlc/release/gtl_spec/packages/{slug}.py`
- `REQ-F-TERRITORY-001`:
  - workflow release in `.gsdlc/release/workflows/...`
  - wrapper in `.gsdlc/release/gtl_spec/packages/...`
  - `.genesis/` contains only ABG engine (`genesis/`) and GTL (`gtl/`)
  - no gsdlc workflow, wrapper, or config artifacts are written to `.genesis/`
- `REQ-F-TERRITORY-002`:
  - runtime resolves from `.gsdlc/release`, not `builds/`

So the specification is already clear on the main separation:

**kernel in `.genesis`, domain release in `.gsdlc/release`.**

## What the Current Installer Actually Does

### 1. It installs ABG seed spec into `.genesis/`

`install_engine_seed()` copies not just engine + GTL, but also ABG seed spec files into `.genesis/`:

- `gtl_spec/packages/genesis_core.py`
- `gtl_spec/packages/abiogenesis.py`
- `gtl_spec/GTL_BOOTLOADER.md`
- `gtl_spec/GENESIS_BOOTLOADER.md`

Source:
- `install.py:216-240`

This is already wrong against the ABG 1.0 cleanup. Vanilla ABG no longer ships installed `gtl_spec` as kernel truth.

### 2. It binds bootstrap directly to `.genesis/gtl_spec/packages/{slug}.py`

`install_genesis_yml()` writes:

- `package: gtl_spec.packages.<slug>:package`
- `worker:  gtl_spec.packages.<slug>:worker`
- `pythonpath: [builds/codex/code]`

Source:
- `install.py:245-257`

This is wrong in two ways:

- it binds directly to a package expected inside `.genesis/gtl_spec`
- it uses `builds/codex/code` rather than a domain release territory

Against ABG 1.0, `.genesis/genesis.yml` should be a **bootstrap config**, not the main domain binding point. The kernel should follow a domain `runtime_contract`, not carry the domain package path as first-class truth.

### 3. It writes the workflow release into `.genesis/workflows/`

`install_workflow_release()` installs:

- `.genesis/workflows/genesis_sdlc/standard/v{VERSION}/spec.py`

Source:
- `install.py:260-290`

Specification requires:

- `.gsdlc/release/workflows/genesis_sdlc/standard/v{VERSION}/...`

So the current installer is writing the domain release into the kernel territory.

### 4. It writes active workflow state into `.genesis/active-workflow.json`

`install_active_workflow()` writes:

- `.genesis/active-workflow.json`

Source:
- `install.py:293-301`

This is not just a spec mismatch. It also violates the ABG 1.0 territory rule that mutable runtime/provenance belongs under `.ai-workspace/`.

### 5. It writes a frozen spec shim into `.genesis/spec/`

`install_immutable_spec()` writes:

- `.genesis/spec/genesis_sdlc.py`

Source:
- `install.py:305-310`

Again, the specification says the immutable methodology layer belongs in `.gsdlc/release/spec/`, not inside `.genesis/`.

### 6. It writes the project wrapper into `.genesis/gtl_spec/packages/{slug}.py`

`install_sdlc_starter_spec()` writes:

- `.genesis/gtl_spec/packages/{slug}.py`

Source:
- `install.py:313-326`

Specification requires:

- `.gsdlc/release/gtl_spec/packages/{slug}.py`

This is a direct territory violation.

### 7. It writes operating standards into `.ai-workspace/operating-standards/`

`install_operating_standards()` writes:

- `.ai-workspace/operating-standards/`

Source:
- `install.py:392-400`

Specification says the installed operating standards are part of the immutable methodology layer:

- `.gsdlc/release/operating-standards/`

So current behavior makes them mutable/shared runtime state instead of immutable installed domain release.

### 8. Its verification/audit logic encodes the same old territory model

`_verify()` and `_audit()` still assert the old world:

- workflow release under `.genesis/workflows/...`
- active workflow under `.genesis/active-workflow.json`
- immutable spec under `.genesis/spec/...`
- wrapper under `.genesis/gtl_spec/...`

Source:
- `install.py:609-680`

This means the installer is not only wrong in implementation; it also certifies the wrong architecture as correct.

## What the Current SDLC Graph Still Assumes

The source `sdlc_graph.py` is also still aligned to the old installed layout:

- bootloader locator points to `workspace://.genesis/gtl_spec/GENESIS_BOOTLOADER.md`
  - `sdlc_graph.py:48-52`
- installed wrapper context points to `workspace://.genesis/gtl_spec/packages/{slug}.py`
  - `sdlc_graph.py:507-510`

Both assumptions conflict with the cleaned ABG model and with the `genesis_sdlc` territory requirements.

The bootloader path is also stale in filename:

- `GENESIS_BOOTLOADER.md` instead of `GTL_BOOTLOADER.md`

## What the Current `test_install/` Baseline Shows

At the moment of this review, `test_install/` contains only the ABG baseline:

- `.genesis/genesis/`
- `.genesis/gtl/`
- `.genesis/genesis.yml` bootstrap comments only
- `.ai-workspace/events/events.jsonl`
- `.ai-workspace/runtime/`

Notably absent:

- `.gsdlc/release/`
- domain runtime contract
- installed wrapper
- workflow release
- active workflow metadata

This is useful because it proves the clean kernel baseline is now available.

It also proves the next step clearly:

**`gsdlc.install` should layer on top of this baseline, not recreate the old `.genesis` world.**

## Where the Specification Itself Needs Re-Alignment

Most of the territory model in `requirements.md` is now directionally correct, but two areas need updating to match ABG 1.0:

### A. Bootstrap config should become `runtime_contract`-first

Current spec still says:

- `.genesis/genesis.yml` points directly to `gtl_spec.packages.<slug>:package`
- and `worker`

That is older than ABG 1.0.

The cleaner model is:

- `.genesis/genesis.yml` is kernel bootstrap only
- it points to `runtime_contract: .gsdlc/release/genesis.yml`
- the domain contract carries package/worker/pythonpath

### B. Active workflow provenance should move out of immutable territory

Current spec says:

- `.gsdlc/release/active-workflow.json`

ABG 1.0 moved active workflow/runtime provenance toward mutable runtime state under `.ai-workspace/runtime/`.

So the specification needs an explicit decision:

- either `active_workflow` is immutable release metadata
- or it is mutable runtime provenance

It should not drift by accident.

Given the ABG cleanup, the more consistent answer is:

- immutable workflow release under `.gsdlc/release/workflows/...`
- mutable active workflow pointer under `.ai-workspace/runtime/active-workflow.json`
- referenced from the domain runtime contract

## Net Assessment

### Against ABG 1.0

Current `gsdlc.install` is **not aligned**.

It still assumes:

- installed `gtl_spec`
- domain workflow under `.genesis`
- mutable workflow pointer under `.genesis`
- direct package binding in `.genesis/genesis.yml`

### Against GSDLC Specification

Current `gsdlc.install` is **materially out of spec** on territory layout:

- should install domain release into `.gsdlc/release/`
- currently installs it into `.genesis/`

### Against GTL / runtime model

Current `gsdlc.install` is still trying to do ABG’s bootstrap job and the domain’s release job in one pass. That is exactly the boundary collapse ABG 1.0 just removed.

## Recommended Next Steps

### Phase 1 — Rebase on ABG 1.0

- stop copying ABG seed spec into `.genesis/`
- stop writing domain wrapper/spec/workflows into `.genesis/`
- call/use ABG installer as the kernel prerequisite

### Phase 2 — Install domain release into `.gsdlc/release/`

Move these from `.genesis/...` to `.gsdlc/release/...`:

- `genesis.yml` domain runtime contract
- versioned workflow release
- generated wrapper
- immutable methodology spec
- operating standards

### Phase 3 — Make bootstrap config kernel-only

`.genesis/genesis.yml` should carry:

- `runtime_contract: .gsdlc/release/genesis.yml`

not:

- direct `package:` / `worker:` for the domain

### Phase 4 — Decide active workflow ownership explicitly

Recommended:

- workflow release metadata in `.gsdlc/release/workflows/...`
- active workflow pointer in `.ai-workspace/runtime/active-workflow.json`
- referenced by the domain contract

### Phase 5 — Fix the installed graph assumptions

Update `sdlc_graph.py` to stop assuming:

- `.genesis/gtl_spec/...`
- `GENESIS_BOOTLOADER.md`

and bind installed contexts against the real domain release territory.

## Bottom Line

The clean ABG baseline is now available. That is the good news.

The bad news is that current `gsdlc.install` is still architected as if ABG had not been cleaned up:

- it repopulates `.genesis` with domain artifacts
- it makes `.genesis` carry mutable workflow state
- it certifies the wrong territory model in its own verify/audit logic

So the right reading is:

**`gsdlc.install` is not yet a thin domain layer on top of ABG 1.0. It is still a stale bootstrap stack that must be rebased before the rest of the GSDLC cleanup can be trusted.**
