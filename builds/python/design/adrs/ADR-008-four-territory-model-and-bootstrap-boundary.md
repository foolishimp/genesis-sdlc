**Implements**: REQ-F-BOOT-001, REQ-F-BOOT-004, REQ-F-BOOT-006

# ADR-008: Four-Territory Model and Bootstrap Boundary Enforcement

**Status**: Accepted
**Date**: 2026-03-20
**Addresses**: REQ-F-BOOT-001/004/005/006, GCC bootstrap boundary violation
**Supersedes**: ADR-005 (Layer 3 location and self-hosting model)

---

## Intent Traceability

**INT-001** requires traceability from intent to runtime.
**INT-002** requires the methodology to be self-hosting.

ADR-005 established the three-layer install architecture. During self-hosting development, a recurring defect emerged: the running engine (GCC 1.0) was reading live-editable build source (GCC 2.0) because `gtl_spec/` sat at the project root — editable, driftable, and confused with the build source.

The boundary violation was documented in GAP post `20260320T120000_GAP_gcc-bootstrap-boundary-violation.md` and resolved in `20260320T150000_REVIEW_gcc-bootstrap-boundary-resolved.md`.

---

## Decision

### Four territories with distinct access semantics

Every file in a genesis_sdlc-managed project belongs to exactly one territory:

| Territory | Access | Owner | Content |
|-----------|--------|-------|---------|
| `.genesis/` | **Write-once** | Installer | Engine, gtl_spec, workflows, spec shim — GCC 1.0 |
| `.ai-workspace/` | **Read-write** | Engine + agents | Events, features, reviews, overrides |
| `specification/` | **Read-only** | Human author | Intent, requirements, feature decomposition, standards |
| `builds/` | **Read-write** | Agents | GCC 2.0 source code, tests, ADRs, generated assets |

### gtl_spec moves under .genesis/

**Supersedes ADR-005 §Layer 3 location.** The `gtl_spec/` directory is the installed compiler's spec entry point. It is not a project-editable surface. It belongs with the rest of the installed compiler inside `.genesis/`.

```
.genesis/
    genesis/                              ← Layer 1: abiogenesis engine
    gtl/                                  ← Layer 1: GTL type system
    gtl_spec/                             ← installed spec entry point
        GENESIS_BOOTLOADER.md             ← compiled constraint document (see §Provenance)
        packages/
            {slug}.py                     ← Layer 3: generated wrapper → Layer 2
            genesis_core.py               ← abiogenesis Package spec
    workflows/genesis_sdlc/standard/
        v{VERSION}/spec.py                ← Layer 2: immutable versioned release
    spec/genesis_sdlc.py                  ← backwards-compat shim
    genesis.yml                           ← engine config
```

The engine resolves `gtl_spec.packages.{slug}:package` via `PYTHONPATH=.genesis`. The import path is unchanged — only the filesystem location moves.

### Project overrides belong in .ai-workspace/

If a project needs to override anything from the installed Package (custom evaluators, additional edges), those overrides live in `.ai-workspace/` — the only read-write runtime surface. The installed `gtl_spec/` inside `.genesis/` is immutable.

---

## Provenance Chain

### Source of truth hierarchy

```
specification/                    ← PRIMARY (axioms, human-authored)
    ├── INTENT.md
    ├── requirements.md
    ├── feature_decomposition.md
    └── standards/                ← methodology standards

builds/                           ← BUILD SOURCE (code + generated assets)
    └── python/src/genesis_sdlc/
        ├── sdlc_graph.py         ← Package definition (GCC 2.0)
        └── install.py            ← constitutional enforcer

.genesis/                         ← DEPLOYED (all derived, write-once)
    ├── gtl_spec/
    │   ├── GENESIS_BOOTLOADER.md ← compiled from specification/
    │   └── packages/{slug}.py    ← generated from sdlc_graph.py template
    ├── workflows/.../spec.py     ← copy of sdlc_graph.py at release
    └── spec/genesis_sdlc.py      ← backwards-compat copy

.ai-workspace/                    ← RUNTIME (all derived, read-write)
    ├── operating-standards/      ← copied from specification/standards/
    └── ...

CLAUDE.md                         ← compiled from GENESIS_BOOTLOADER.md
.claude/commands/                 ← copied from builds/
```

### GENESIS_BOOTLOADER.md is a compiled asset

The bootloader is **not a primary source**. It is a compiled constraint summary derived from `specification/` — every section traces back to the axioms in intent, requirements, and standards. Its provenance:

```
specification/ (axioms)
    ↓ compiled into
GENESIS_BOOTLOADER.md (constraint summary for LLM consumption)
    ↓ installed into
.genesis/gtl_spec/GENESIS_BOOTLOADER.md
    ↓ embedded into
CLAUDE.md (agent constraint surface)
```

The bootloader is authored in `builds/` or `specification/` (authoring surface TBD) and deployed by the installer. It is versioned (`BOOTLOADER_VERSION` in install.py). Changes to the bootloader require a release.

### Derived artifacts are disposable

Every file outside `specification/` and `builds/` is derived. The installer can regenerate all of them:

| Derived artifact | Generated from |
|-----------------|----------------|
| `.genesis/workflows/.../spec.py` | `builds/python/src/genesis_sdlc/sdlc_graph.py` |
| `.genesis/gtl_spec/packages/{slug}.py` | Template in `install.py` + version |
| `.genesis/gtl_spec/GENESIS_BOOTLOADER.md` | Source bootloader |
| `.genesis/spec/genesis_sdlc.py` | `sdlc_graph.py` (shim copy) |
| `.ai-workspace/operating-standards/*.md` | `specification/standards/*.md` |
| `.claude/commands/*.md` | `builds/claude_code/.../commands/` + abiogenesis commands |
| `CLAUDE.md` (bootloader section) | GENESIS_BOOTLOADER.md + template |

If you can delete it and the installer recreates it identically, it's derived.

---

## The Installer as Constitutional Enforcer

The installer is the executable form of this ADR. It:

1. **Creates** the four-territory structure
2. **Deposits** GCC 1.0 into `.genesis/` (engine + gtl_spec + workflows)
3. **Generates** the Layer 3 wrapper pointing to the installed release
4. **Validates** the boundary with `--audit` (REQ-F-BOOT-006)

`--audit` checks content hashes, version consistency, genesis.yml import resolution, wrapper template match, and bootloader block integrity. It is the runtime proof that the boundary holds.

---

## The GCC Bootstrap Boundary

**Invariant**: The running engine evaluates against the released Package (GCC 1.0), never the build source (GCC 2.0).

| Question | Answer |
|----------|--------|
| Can I edit `builds/.../sdlc_graph.py` without affecting `gen-gaps`? | **Yes** — engine reads from `.genesis/`, not `builds/` |
| Can I delete `builds/` and still have a working dev env? | **Yes** — `.genesis/` has everything the engine needs |
| Where does GCC 2.0 run as a compiler? | **Only** in the sandbox e2e test (`test_e2e_sandbox.py`) |
| How do I verify the boundary? | `python -m genesis_sdlc.install --target . --audit` |

---

## What This Supersedes in ADR-005

| ADR-005 said | ADR-008 says |
|-------------|-------------|
| Layer 3 at `gtl_spec/` (project root) | Layer 3 at `.genesis/gtl_spec/` (inside installed compiler) |
| `gtl_spec/` is mutable, project-owned | `.genesis/gtl_spec/` is write-once, installer-owned |
| Self-hosting: both Layer 2 and 3 coexist during development | Self-hosting: `.genesis/` is GCC 1.0, `builds/` is GCC 2.0, no confusion |
| No audit capability | `--audit` validates the boundary (REQ-F-BOOT-006) |
| Bootloader is a primary source in `gtl_spec/` | Bootloader is a compiled asset derived from `specification/` |

ADR-005's three-layer model is preserved — the layers still exist. What changes is where Layer 3 lives and what the boundary enforcement mechanism is.

---

## Migration Path

### Completed (this session)

1. `gtl_spec/` moved under `.genesis/` via `git mv` (genesis_sdlc self-hosting)
2. `gtl_spec/packages/genesis_sdlc.py` deleted (GCC 2.0 duplicate)
3. `--audit` implemented and tested (7 tests)
4. REQ-F-BOOT-006 added to spec, Package, feature vector, user guide
5. All references in `specification/` updated
6. Installer writes `gtl_spec/` under `.genesis/` for **all** projects
7. `_CLAUDE_MD_HEADER` template updated (four-territory structure)
8. `_verify()` updated to check `.genesis/gtl_spec/`
9. `sdlc_graph.py` locators updated (`workspace://.genesis/gtl_spec/...`)
10. Abiogenesis `gen-install.py` updated (creates `.genesis/gtl_spec/` instead of root `gtl_spec/`)
11. All test assertions updated — 145 passing, 0 failures

### Ratified transitions required

No more implicit structural changes. Each transition:
- Starts with a spec update (`specification/requirements.md`)
- Is recorded in an ADR
- Is implemented in the installer
- Is validated by `--audit`
- Is released with a version bump
