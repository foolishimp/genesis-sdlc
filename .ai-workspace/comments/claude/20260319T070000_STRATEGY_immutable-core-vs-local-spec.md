# STRATEGY: Immutable Core vs Local Project Spec

**Author**: Claude Code
**Date**: 2026-03-19
**Addresses**: REQ-F-BOOT install architecture — gap exposed during v0.2.0 module_decomp development
**For**: all

## Summary

The current installer installs the runner but not the spec. This means `gtl_spec/` is simultaneously the source under development AND the live file the installed runner evaluates. These two roles must be separated. When genesis_sdlc is installed into any project, there must be an immutable core spec (the frozen methodology) and a mutable local spec (project-specific customisation).

---

## The Problem

Currently, when genesis_sdlc is installed into a project:

```
.genesis/
    genesis/         ← runner installed ✓
    genesis.yml      ← points to gtl_spec/packages/genesis_sdlc.py

gtl_spec/
    packages/
        genesis_sdlc.py   ← live file, read by runner on every invocation
```

`gtl_spec/packages/genesis_sdlc.py` serves two roles at once:

1. **The source under development** — the thing being built and iterated on
2. **The runtime spec** — the live constitutional surface the installed runner evaluates every time `gen-start` runs

This creates a self-hosting bootstrapping problem. When we added `module_decomp` to `gtl_spec/genesis_sdlc.py` mid-development, the v0.1.6 runner immediately started evaluating the v0.2.0 graph. Old `fp_assessment` events became stale (spec_hash changed). The `design→code` edge disappeared from the live graph. The development workspace and the installed runtime are no longer at the same version.

More fundamentally: **every project that installs genesis_sdlc has this same problem**. Their `gtl_spec/` is their local customisation surface, but there is no stable, immutable copy of the standard methodology to build on top of.

---

## The Proposal

When genesis_sdlc installs into a target project, it must create two distinct layers:

```
.genesis/
    genesis/                    ← runner (immutable — installed from release)
    spec/
        genesis_sdlc.py         ← CORE SPEC (immutable — installed from release)
        genesis_core.py         ← GTL primitives (immutable — installed from release)
    genesis.yml                 ← points to local spec (gtl_spec/)

gtl_spec/
    packages/
        {project_slug}.py       ← LOCAL SPEC (mutable — project customisation)
                                   imports core from .genesis/spec/genesis_sdlc
                                   extends or overrides for this project
```

**Invariant**: `.genesis/spec/` is never edited by the project. It is owned by the genesis_sdlc release. On upgrade, it is replaced atomically. A project that edits `.genesis/spec/` has voided its warranty.

**`genesis.yml`** points to the local spec:
```yaml
package: gtl_spec.packages.{project_slug}:package
worker:  gtl_spec.packages.{project_slug}:worker
```

The local spec imports the standard graph from the installed core:
```python
from genesis.spec.genesis_sdlc import (
    intent, requirements, feature_decomp, design, module_decomp,
    code, unit_tests, uat_tests,
    standard_gate, claude_agent, human_gate, ...
)
```

The project may use the standard graph as-is, override evaluator commands, add project-specific edges, or restrict to a profile (e.g. PoC).

---

## The genesis_sdlc Special Case

genesis_sdlc is self-hosting. Its `gtl_spec/packages/genesis_sdlc.py` is both:
- The **source under development** (future v0.2.0 core)
- Used as the local spec during its own development build

This is acceptable as a special case. The invariant is:

> During genesis_sdlc development, `gtl_spec/` IS the thing being built. On release, it gets copied into `.genesis/spec/` of downstream projects as the immutable core. Downstream projects never have this dual-role problem because they receive a frozen copy.

---

## Impact on install.py

The installer (`builds/python/src/genesis_sdlc/install.py`) currently copies only the runner into `.genesis/genesis/`. It must also:

1. Copy `gtl_spec/packages/genesis_sdlc.py` → `{target}/.genesis/spec/genesis_sdlc.py`
2. Copy `gtl_spec/packages/genesis_core.py` → `{target}/.genesis/spec/genesis_core.py` (if applicable)
3. Generate a starter `{target}/gtl_spec/packages/{project_slug}.py` that imports from `.genesis/spec/genesis_sdlc`
4. Write `{target}/.genesis/genesis.yml` pointing to the local spec

Reinstall is idempotent on `.genesis/spec/` (replace) and non-destructive on `gtl_spec/` (never overwrite local customisation).

---

## New REQ Keys Required

This proposal requires new requirements. Suggested keys for v0.2.0:

| Key | Statement |
|-----|-----------|
| `REQ-F-BOOT-003` | Installer copies core spec into `{target}/.genesis/spec/` as immutable layer |
| `REQ-F-BOOT-004` | Installer generates starter local spec in `{target}/gtl_spec/packages/{slug}.py` |
| `REQ-F-BOOT-005` | Reinstall replaces `.genesis/spec/` atomically; never overwrites local `gtl_spec/` |

---

## Relationship to module_decomp Work

The current v0.2.0 development (module_decomp, REQ-F-MDECOMP-*) can continue as-is. This proposal does not block it. However, the v0.2.0 release should include these BOOT additions so that the first project to install v0.2.0 gets the correct two-layer structure. Shipping module_decomp without fixing the install architecture means every downstream project will have the same dual-role problem we just hit.

## Recommended Action

1. Add `REQ-F-BOOT-003/004/005` to `gtl_spec/packages/genesis_sdlc.py`
2. Create feature vector `REQ-F-BOOT-V2.yml` covering these keys
3. Update `install.py` to implement the two-layer copy
4. Include in v0.2.0 release — do not ship module_decomp without this fix
