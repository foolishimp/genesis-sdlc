# STRATEGY: Territory Cleanup — Immutable ABG vs Released GSDLC

## Problem

The current installed surface mixes two different concepts:

- `.genesis/` is acting as the immutable deployed kernel
- `.genesis/` is also carrying released `gsdlc` workflow/package artifacts
- deployed evaluator/runtime paths still reach back into `builds/python/src`

This creates the current build-vs-deployed confusion:

- the engine is deployed from `.genesis/genesis`
- the project package wrapper is deployed from `.genesis/gtl_spec/packages/project_package.py`
- the workflow release is deployed from `.genesis/workflows/...`
- but `genesis.yml` and multiple evaluator commands still pull from `builds/python/src`

That makes the runtime boundary non-truthful. Claude is not confused in the abstract; the territories are currently mixed.

## Proposal

Separate the installed territories cleanly:

```text
.genesis/                # immutable ABG kernel only
  genesis/
  gtl/

.gsdlc/
  release/               # immutable installed GSDLC workflow/package surface
    gtl_spec/
      packages/
        project_package.py
    workflows/
      genesis_sdlc/
        standard/
          vX_Y_Z/
            spec.py
            manifest.json
    active-workflow.json
    genesis.yml

  workspace/             # optional GSDLC-private mutable runtime territory

.ai-workspace/           # project/process/runtime evidence
  events/
  features/
  comments/
  reviews/
  backlog/
  operating-standards/
  uat/

builds/                  # authoring / release-candidate source only
specification/           # human-authored source
```

## Boundary Rule

### `.genesis/`

Owns only:

- `abiogenesis` runtime
- GTL core

It must not contain:

- released `gsdlc` workflow versions
- project package wrappers
- mutable SDLC runtime state

### `.gsdlc/release/`

Owns:

- installed `gsdlc` package wrapper
- installed workflow releases
- `gsdlc` runtime config pointing at the released package

It must be treated as immutable between releases.

### `.gsdlc/workspace/`

Optional private mutable territory for `gsdlc`-local machinery if needed.

### `.ai-workspace/`

Owns project-visible mutable state:

- events
- feature vectors
- comments / reviews
- backlog
- UAT and operating evidence

## Runtime Contract

The deployed invocation should conceptually become:

```bash
PYTHONPATH=.genesis:.gsdlc/release python -m genesis gaps --workspace .
```

The kernel imports:

- `genesis` from `.genesis`
- `gtl` from `.genesis`

The workflow imports:

- `gtl_spec.packages.project_package` from `.gsdlc/release`
- `workflows.genesis_sdlc.standard.vX_Y_Z.spec` from `.gsdlc/release`

No deployed runtime path should require `builds/python/src`.

## Why This Fixes the Current Failure

It removes the current ambiguity:

- `abg` kernel release is one territory
- `gsdlc` release is another territory
- authoring source is not on the deployed runtime path

That means:

- release reasoning becomes truthful
- Claude/Codex command surfaces stop oscillating between build and deployed views
- sandbox-installed tests can become the single authority

## Migration Rule

The cleanup should preserve one invariant:

> If a file is needed for deployed execution, it must live in an installed release territory, not under `builds/`.

Minimum migration sequence:

1. Freeze `.genesis/` to `abg + gtl` only.
2. Move installed `gsdlc` wrapper/workflow/config surface into `.gsdlc/release/`.
3. Remove deployed references to `builds/python/src` from installed config.
4. Keep `.ai-workspace/` as mutable project/process territory.
5. Make sandbox-installed tests the authoritative release gate.

## Decision

Adopt:

- `.genesis/` = immutable ABG kernel
- `.gsdlc/release/` = immutable installed GSDLC release
- `.gsdlc/workspace/` = optional GSDLC-private mutable territory
- `.ai-workspace/` = mutable project/process/runtime evidence

This is the cleanest territory model currently discussed, and it directly addresses the release-methodology confusion now visible in the live repo.
