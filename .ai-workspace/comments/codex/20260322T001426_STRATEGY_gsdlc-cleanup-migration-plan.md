# STRATEGY: GSDLC Cleanup Migration Plan

## Goal

Recover a clean `gsdlc` territory model and rebuild the installed runtime from
authoritative sources, not by manual copying.

Target model:

- `.genesis/` = immutable `abg + gtl`
- `.gsdlc/release/` = immutable installed `gsdlc` release
- `.gsdlc/workspace/` = mutable graph / GTL customization layer
- `.ai-workspace/` = project/process/runtime evidence
- `builds/` = authoring / release-candidate source only

## Core Rule

> Installed runtime surfaces must be created by installers, not by ad hoc manual copying.

If a deployed file matters, it must have a reproducible installer path.

## Phase 0: Recovery Point

Before any cleanup:

1. Create a dedicated recovery commit containing the current mixed state.
2. Tag it clearly for rollback/reference.
3. Record:
   - current active workflow
   - current installed wrapper target
   - current version naming split (`1.0.0b1` vs `1.0.0-beta`)
   - current sandbox test status

This tag is not “good architecture.” It is the safety checkpoint before aggressive pruning.

## Phase 1: Declare the New Territories

Ratify the intended ownership:

- `.genesis/` owns only deployed `abg` kernel and `gtl`
- `.gsdlc/release/` owns installed `gsdlc` wrapper, workflow releases, and config
- `.gsdlc/workspace/` owns mutable graph/GTL customization
- `.ai-workspace/` owns events, features, reviews, comments, backlog, UAT evidence
- `builds/` owns source under development only

This should be treated as the new boundary contract before any file movement.

## Phase 2: Aggressive Pruning

Delete or retire anything that blurs the territories.

Primary candidates:

- duplicate or conflicting installed release directories
- stale release names that express the same release twice
- legacy installed wrappers under `.genesis/` that should live under `gsdlc`
- stale `.claude/commands` content that references obsolete graph edges
- plugin-only or dead build directories that look like active build targets
- any installed config that points deployed runtime back into `builds/`

Rule:

> If a path makes it harder to answer “is this build source or deployed runtime?”, prune it or relocate it.

## Phase 3: Stop Hand-Assembling the Installed Surface

No more manual copying into installed runtime territories.

Instead:

1. Treat `builds/python` as the authoring / release-candidate source.
2. Make installer outputs the only supported way to materialize:
   - `.genesis/`
   - `.gsdlc/release/`
   - `.gsdlc/workspace/` bootstrap if needed
3. Require that every deployed file in those territories has an installer origin.

Manual patching of installed runtime should be treated as emergency-only and non-authoritative.

## Phase 4: Split the Installers Cleanly

The installer chain should become:

### `abg` installer

Produces only:

- `.genesis/genesis`
- `.genesis/gtl`

No `gsdlc` workflow/package release content should be installed there.

### `gsdlc` installer

Produces:

- `.gsdlc/release/gtl_spec/packages/project_package.py`
- `.gsdlc/release/workflows/...`
- `.gsdlc/release/active-workflow.json`
- `.gsdlc/release/genesis.yml` or equivalent released runtime config
- optional `.gsdlc/workspace/` bootstrap

This installer should consume authoritative build artifacts and generate the deployed
`gsdlc` surface reproducibly.

## Phase 5: Recreate, Do Not Migrate In Place

Preferred method:

1. Tag current state.
2. Prune confusing installed/runtime surfaces.
3. Recreate `.genesis/` from `abg` installer.
4. Recreate `.gsdlc/release/` from `gsdlc` installer.
5. Recreate `.gsdlc/workspace/` bootstrap if required.
6. Keep `.ai-workspace/` as evidence/state unless specific migration is needed.

This is safer than trying to hand-edit the current hybrid state into correctness.

## Phase 6: Make Sandbox-Installed Tests Authoritative

After recreation, the release gate must be:

1. fresh sandbox install
2. deployed runtime invocation
3. no dependency on `builds/python/src`
4. no ambiguity about which release is executing

This gate should be mandatory before trusting `gen-*` commands again.

## Phase 7: Re-enable Methodological Dogfooding

Only after the rebuilt installed surface is passing sandbox proof:

1. trust `gsdlc 1.0-beta` as the deployed network/service layer
2. use it to rebuild/close the remaining `abg 1.0` gaps
3. then dogfood `gsdlc 1.1`

## Decision

Recommended cleanup sequence:

1. recovery commit + recovery tag
2. declare new territory ownership
3. aggressively prune confusing runtime/release residue
4. stop manual copying
5. rebuild installed surfaces through installers only
6. trust only sandbox-installed proof

This is the safest path from the current mixed state to a truthful release boundary.
