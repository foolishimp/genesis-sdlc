# SCHEMA: `.gsdlc/workspace` as Graph and GTL Customization Layer

## Refinement

`.gsdlc/workspace/` should not be treated only as scratch runtime state.

It is more useful as the mutable customization layer over the immutable
`.gsdlc/release/` base.

## Proposed Split

```text
.genesis/                # immutable ABG kernel

.gsdlc/
  release/               # immutable shipped GSDLC release
  workspace/             # mutable graph / GTL customization layer

.ai-workspace/           # project/process/runtime evidence
```

## Meaning of `.gsdlc/release`

Owns the stable base:

- released workflow graph
- released package wrapper
- released config
- released workflow manifests

This territory is immutable between releases.

## Meaning of `.gsdlc/workspace`

Owns project- or tenant-specific customization over that base.

Examples:

- graph overlays
- custom contexts
- tenant-specific package composition
- local GTL extensions or adapters
- generated binding artifacts
- release-local customization metadata

This is the place where GSDLC can adapt the base methodology to a specific project
without mutating the released substrate.

## Composition Rule

Runtime should be understood as:

```text
ABG kernel (.genesis)
  executes
GSDLC released base (.gsdlc/release)
  composed with
GSDLC local customization (.gsdlc/workspace)
```

So:

- `release` defines the stable base graph and GTL realization
- `workspace` layers local customization over that base
- `workspace` must not silently rewrite `release`

## Why This Matters

If `.gsdlc/workspace` is only “scratch space”, then all meaningful customization
pressure gets pushed either into:

- `builds/` (wrong — authoring surface, not deployed runtime), or
- `.ai-workspace/` (too mixed — process/runtime evidence plus methodology customizations)

Treating `.gsdlc/workspace` as the mutable customization layer gives a cleaner model:

- `.genesis` = kernel
- `.gsdlc/release` = shipped methodology
- `.gsdlc/workspace` = local graph/GTL adaptation
- `.ai-workspace` = evidence, state, comments, reviews, backlog

## Decision

Adopt the stronger interpretation:

> `.gsdlc/workspace/` is the mutable graph and GTL customization layer over the immutable `.gsdlc/release/` base.

That is a more coherent territory model than using `.gsdlc/workspace/` only for temporary runtime state.
