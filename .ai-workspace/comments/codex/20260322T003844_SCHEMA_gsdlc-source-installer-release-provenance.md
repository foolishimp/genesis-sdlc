# SCHEMA: GSDLC Source → Installer → Release Provenance

## Purpose

This note defines the provenance chain for `gsdlc` so the build source, installer,
and deployed release are not conflated.

The main rule is simple:

> `abg` is the kernel. `gsdlc` is a library/service built on top of it.  
> `abg` must not know `gsdlc` internals.  
> `gsdlc` must materialize its own released surface from its own build source.

## Territory Model

```text
project/
├── .genesis/                 # immutable ABG kernel only
│   ├── genesis/
│   └── gtl/
│
├── .gsdlc/
│   ├── release/              # immutable deployed GSDLC release
│   └── workspace/            # mutable graph / GTL customization layer
│
├── .ai-workspace/            # mutable runtime evidence/state
│
├── specification/            # human-authored source
└── builds/python/            # GSDLC authoring / release-candidate source
```

## Provenance Rules

### 1. Authoring truth

The authoring source of truth for `gsdlc` lives in:

- `specification/`
- `builds/python/`

For the current repo this specifically means:

- `specification/INTENT.md`
- `specification/requirements.md`
- `specification/feature_decomposition.md`
- `builds/python/src/genesis_sdlc/`
- `builds/python/tests/`
- `builds/python/design/`

This surface is editable and evolves during development.

### 2. Released GSDLC truth

The deployed `gsdlc` runtime surface must live under:

- `.gsdlc/release/`

This is not authoring source. It is the immutable installed release produced from the
authoring source.

Examples of what belongs there:

- `.gsdlc/release/gtl_spec/packages/project_package.py`
- `.gsdlc/release/workflows/genesis_sdlc/standard/vX_Y_Z/spec.py`
- `.gsdlc/release/workflows/genesis_sdlc/standard/vX_Y_Z/manifest.json`
- `.gsdlc/release/active-workflow.json`
- `.gsdlc/release/spec/...` only if a compatibility shim is still needed
- released runtime config for resolving package/worker bindings

### 3. Kernel truth

The deployed kernel must live under:

- `.genesis/`

This is owned by `abg`, not by `gsdlc`.

It contains only:

- deployed `genesis` engine
- deployed `gtl` core

`abg` must not own or install `gsdlc` workflow releases as part of its final architecture.

### 4. Mutable runtime truth

The mutable runtime/event/evidence surface lives under:

- `.ai-workspace/`

This includes:

- event stream
- manifests and results
- feature vectors
- comments / reviews
- backlog
- UAT evidence

This is expected to accumulate over time. It is not immutable release state.

## Bootstrap Sequence

The intended lifecycle is:

### Phase A: Build and release ABG

`abg` is authored, qualified, and released as a standalone kernel.

Its installer materializes:

- `.genesis/genesis`
- `.genesis/gtl`
- mutable runtime support as needed in `.ai-workspace`

### Phase B: Deploy ABG into a project

The target project receives:

- `.genesis/`
- `.ai-workspace/`

At this point the project has a kernel, not yet a released `gsdlc` methodology layer.

### Phase C: Bootstrap GSDLC in the project

The project establishes its `gsdlc` authoring truth:

- `specification/`
- `builds/python/`

This is where the graph, evaluators, installer, docs, tests, and standards are authored.

### Phase D: GSDLC installer materializes the deployed methodology

`gsdlc.installer` is responsible for:

1. calling `abg.installer` if the kernel is missing or needs refresh
2. reading `gsdlc` authoring truth from `specification/` + `builds/python/`
3. creating `.gsdlc/release/`
4. creating `.gsdlc/workspace/` if required
5. configuring runtime binding so the kernel loads the released `gsdlc` package

This is the critical boundary:

> The deployed `gsdlc` release is produced by the installer from the build source.  
> It is not hand-copied and it is not executed directly from `builds/python/`.

## Installer Responsibilities

### ABG installer

Owns only kernel installation.

It must not need to know:

- `gsdlc` workflow names
- `gsdlc` release versions
- `gsdlc` package layout
- `gsdlc` graph customization

It installs a generic kernel substrate.

### GSDLC installer

Owns the methodology layer.

It knows:

- how `gsdlc` authoring source maps into a deployed release
- where the released wrapper lives
- where released workflow versions live
- how runtime should resolve the project package
- how local customization overlays are applied

This is where `gsdlc`-specific binding belongs.

## Runtime Resolution

The runtime must conceptually resolve like this:

```text
ABG kernel (.genesis)
  loads
released GSDLC package (.gsdlc/release)
  optionally composed with
local GSDLC customization (.gsdlc/workspace)
```

So the runtime import path should reflect installed territories, not authoring source.

Conceptually:

```bash
PYTHONPATH=.genesis:.gsdlc/release python -m genesis gaps --workspace .
```

Not:

```bash
PYTHONPATH=.genesis:builds/python/src ...
```

because `builds/python/src` is authoring truth, not deployed truth.

## Customization Layer

`.gsdlc/workspace/` is the mutable customization layer over the immutable release.

It may contain:

- graph overlays
- custom contexts
- tenant-specific package composition
- GTL adaptation/binding artifacts
- local release customization metadata

This allows `gsdlc` to adapt the base methodology without mutating `.gsdlc/release/`.

## Anti-Patterns

These are the states to eliminate:

### 1. Build source on deployed runtime path

If deployed execution needs `builds/python/src`, the release boundary is broken.

### 2. GSDLC release under `.genesis`

If `.genesis` contains `gsdlc` workflow releases or project wrappers, kernel and
library territories are mixed.

### 3. Manual copying into installed runtime

If deployed files are maintained by ad hoc copy/edit rather than installer output,
provenance is untrustworthy.

### 4. Unclear source of truth

If the same concept exists simultaneously as:

- build source
- installed release
- mutable workspace scratch

without explicit ownership, the methodology becomes non-truthful.

## Canonical Provenance Statement

For `gsdlc`, the provenance chain should be stated as:

1. Human-authored source is created in `specification/` and `builds/python/`.
2. `gsdlc.installer` transforms that source into a deployed immutable release under `.gsdlc/release/`.
3. `abg` executes the installed release through the kernel in `.genesis/`.
4. `.gsdlc/workspace/` layers mutable customization over the released base.
5. `.ai-workspace/` accumulates the runtime evidence and process state produced by execution.

That is the coherent source → installer → release → runtime provenance model.
