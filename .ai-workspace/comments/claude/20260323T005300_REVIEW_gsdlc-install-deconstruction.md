# REVIEW: GSDLC Installer Deconstruction — State vs Specification vs ABG v1.0

**Author**: Claude
**Date**: 2026-03-23T00:53:00+11:00
**Addresses**: `builds/codex/code/genesis_sdlc/install.py`, `builds/python/src/genesis_sdlc/install.py`, `sdlc_graph.py`, specification/
**For**: all

## Summary

Two divergent installer implementations exist. Neither produces a correct install when tested against a clean target. This review deconstructs both against the specification (`requirements.md`, `feature_decomposition.md`) and the ABG v1.0 architecture that shipped.

---

## Finding 0: Two Installers Exist

| | Codex build | Python build |
|---|---|---|
| Path | `builds/codex/code/genesis_sdlc/install.py` | `builds/python/src/genesis_sdlc/install.py` |
| Lines | 847 | 1,557 |
| VERSION | `0.5.1` | `1.0.0b1` |
| Bootloader version | `1.2.0` | `1.1.0` |
| Territory model | Single (.genesis/) | Three-layer (.genesis/ + .gsdlc/release/) |
| ABG delegation | Installs engine directly from `abiogenesis/builds/codex/code/` | Delegates to `gen-install.py` via subprocess |
| runtime_contract | No | Yes (.gsdlc/release/genesis.yml) |
| MCP install | No | Via ABG delegation |

**Verdict**: The Python build is architecturally closer to correct — it delegates ABG installation and uses the three-layer territory model. The Codex build reimplements ABG's job (badly, from a stale source) and dumps everything into `.genesis/`. However, neither is fully correct.

---

## Finding 1: Codex Installer Pulls from Stale ABG Source

**Spec**: REQ-F-BOOT-001 — "gen-install bootstraps target with engine + methodology"

**Problem**: The Codex installer hardcodes `abiogenesis/builds/codex/code/` as the ABG engine source. ABG v1.0 shipped from `builds/claude_code/code/`. The codex build is a pre-v1.0 fork:

- Missing `fp_dispatch.py` (8th engine module, added for MCP/ADR-020)
- `__init__.py` says "Codex build" — the v1.0 release says "genesis — GTL-first AI SDLC engine, V1"
- `ENGINE_MODULES` list has 7 items, not 8
- `SEED_SPEC_FILES` references `gtl_spec/GENESIS_BOOTLOADER.md` which does not exist

**Impact**: Any project installed via the Codex path gets a pre-release engine with no MCP transport capability. F_P dispatch is broken from day one.

---

## Finding 2: Codex Installer Ships ABG Domain Packages Into Kernel Territory

**Spec**: REQ-F-TERRITORY-001 — "gsdlc installer writes release artifacts to .gsdlc/release/"

**ABG Lesson #2**: "The kernel must not ship domain packages"

**Problem**: The Codex `SEED_SPEC_FILES` list includes:
```
gtl_spec/packages/genesis_core.py
gtl_spec/packages/abiogenesis.py
```
These are ABG's own self-hosting specification packages. They contain:
- ABG-specific evaluator commands (`python -m pytest builds/claude_code/tests/...`)
- ABG-specific context locators (`workspace://builds/claude_code/design/adrs/`)
- ABG-specific markov conditions (`engine_modules_complete`)
- 40 ABG-specific REQ keys

A vanilla GSDLC install into a new project ships these ABG packages into `.genesis/gtl_spec/packages/`. The target project now has a kernel that references files and paths that don't exist in it.

**Impact**: Contaminated kernel. `gen-gaps` would attempt to evaluate ABG-specific criteria against a project that has no ABG source tree.

---

## Finding 3: Codex Installer Has No Territory Separation

**Spec**: REQ-F-TERRITORY-001 — "gsdlc installer writes release artifacts to .gsdlc/release/"
**Spec**: REQ-F-TERRITORY-002 — "Runtime resolves from installed territories, not build source"

**Problem**: The Codex installer writes everything into `.genesis/`:
- `.genesis/workflows/genesis_sdlc/standard/v0_5_1/spec.py`
- `.genesis/active-workflow.json`
- `.genesis/spec/genesis_sdlc.py`
- `.genesis/gtl_spec/packages/{slug}.py`

ABG v1.0 established that `.genesis/` is kernel territory, owned exclusively by ABG. Domain content belongs in `.gsdlc/release/`. The Codex installer violates this boundary completely.

**Impact**: ABG reinstall would nuke the domain content. No clean separation of kernel vs domain lifecycle.

---

## Finding 4: Python Installer Delegates ABG Correctly but Has Wrong Invocation

**Problem**: The Python installer delegates to ABG correctly:
```python
candidates = [
    source.parent / "abiogenesis" / "builds" / "claude_code" / "code" / "gen-install.py",
]
```

It passes `--project-slug` and `--platform` to ABG's installer. But ABG v1.0's `gen-install.py` does NOT accept `--project-slug` — it was removed precisely because the kernel must not know about domain slugs. ABG v1.0 accepts `--target`, `--verify`, and `--platform` only.

**Impact**: The subprocess call will fail with an unrecognised argument error on `--project-slug`.

---

## Finding 5: Python Installer's runtime_contract Is Not Connected to ABG

**Spec**: REQ-F-TERRITORY-002 — "Runtime resolves from installed territories"

**Problem**: `_write_domain_runtime_contract()` writes `.gsdlc/release/genesis.yml`:
```yaml
package: gtl_spec.packages.{slug}:package
worker:  gtl_spec.packages.{slug}:worker
pythonpath:
  - .gsdlc/release
```

But ABG v1.0's `__main__.py` reads `.genesis/genesis.yml` and follows `runtime_contract:` if set. The Python installer never writes `runtime_contract: .gsdlc/release/genesis.yml` into `.genesis/genesis.yml`. The indirection chain is broken — ABG will boot with the seed config (no binding) and never discover the domain contract.

**Impact**: Engine starts with no package, no worker. Every command fails immediately.

---

## Finding 6: Two Divergent sdlc_graph.py Files

| | Python build | Codex build |
|---|---|---|
| Lines | 698 | 586 |
| Docstring | Full — describes graph topology, module_decomp, INT-003 | "Codex build" — minimal |
| Platform awareness | `builds/python/src/` and `builds/python/tests/` | `builds/codex/code/` and `builds/codex/tests/` |

Both define the same graph topology (10 assets, 9 edges), but evaluator commands reference different paths. The Python build references `builds/python/src/` and `builds/python/tests/`. The Codex build references `builds/codex/code/` and `builds/codex/tests/`.

**Problem**: The `instantiate()` function in both should parameterize the platform path. The Python build does accept `platform` and `src_dir` parameters; the Codex build only accepts `slug`. This means the Codex build's evaluator commands are hardcoded to a single build layout.

**Impact**: Platform-agnostic installation is broken in the Codex build. Only works for `builds/codex/code/` layout.

---

## Finding 7: Two Divergent SDLC_BOOTLOADER.md Files

| | Python build | Codex build |
|---|---|---|
| Version | 1.1.1 | 1.2.0 |
| Section numbering | Starts at "SDLC Graph" (no section numbers) | Starts at "XII. Completeness Visibility" |
| Content | Older, fewer sections | Newer, includes completeness visibility, workspace territory, human proxy mode |

The Codex build's bootloader is newer and more complete. But the Python installer references the Python build's older version.

**Impact**: Which bootloader is authoritative? Neither build is the canonical source — they've diverged.

---

## Finding 8: Command Source Paths Are Wrong or Missing

**Codex installer** looks for commands at:
```
builds/codex/.claude-plugin/plugins/genesis/commands/
```

**Python installer** looks for ABG commands at:
```
../abiogenesis/builds/claude_code/.claude-plugin/plugins/genesis/commands/
```
and GSDLC commands at:
```
builds/claude_code/.claude-plugin/plugins/genesis/commands/
```

Neither path is verified to exist. The Codex installer will fail if `.claude-plugin/` doesn't exist. The Python installer references `builds/claude_code/` for GSDLC commands — but GSDLC's code lives in `builds/python/` or `builds/codex/`, not `builds/claude_code/`.

**Impact**: Command installation fails silently or with confusing errors.

---

## Finding 9: Python Installer's _source_root_from_package Uses Wrong Heuristic

```python
for parent in [pkg_path.parent.parent, ...]:
    if (parent / ".genesis" / "gtl_spec").exists() and (parent / ".genesis").exists():
        return parent
```

This detects source root by looking for `.genesis/gtl_spec/` — but ABG v1.0 no longer ships `gtl_spec/` into `.genesis/`. The kernel install is clean: `.genesis/genesis/`, `.genesis/gtl/`, `.genesis/genesis.yml`. No `gtl_spec/`.

**Impact**: Auto-detection of source root fails on any project that received a clean ABG v1.0 install.

---

## Finding 10: Specification Coverage Assessment

### REQ keys with implementations in neither installer:

| REQ Key | Status |
|---|---|
| REQ-F-BOOT-001 (bootstrap) | Partial — both claim it, but Codex ships stale engine and Python subprocess invocation is broken |
| REQ-F-BOOT-002 (genesis.yml resolves Package/Worker) | Broken — Codex writes to wrong territory; Python's runtime_contract is disconnected |
| REQ-F-BOOT-003 (released spec into .gsdlc/release/spec/) | Python only (Codex writes to .genesis/) |
| REQ-F-BOOT-004 (generated wrapper) | Both — but Codex writes to .genesis/, Python to .gsdlc/release/ |
| REQ-F-BOOT-005 (reinstall atomicity) | Untested — cannot verify without a working first install |
| REQ-F-BOOT-006 (--audit) | Both have _audit(), but both audit against their own broken expectations |
| REQ-F-TERRITORY-001 (.gsdlc/release/) | Python only — Codex has no territory separation |
| REQ-F-TERRITORY-002 (runtime contract) | Python writes it, but doesn't connect it to .genesis/genesis.yml |
| REQ-F-CUSTODY-002 (wrapper loads project reqs) | Python only — Codex wrapper has no req loading |
| REQ-F-CUSTODY-003 (scaffold requirements.md) | Python only |

---

## Root Cause Analysis

The two installers diverged because `builds/codex/` and `builds/python/` were treated as independent development branches rather than platform variants of one specification. The Codex build was created as a fork, not a parameterization.

Meanwhile, ABG v1.0 shipped fundamental architecture changes (territory separation, runtime_contract, MCP transport, removal of gtl_spec from kernel) that invalidated assumptions in both installers but were only partially adopted by the Python build and not at all by the Codex build.

The specification itself is correct — REQ-F-TERRITORY-001/002 describe the right model. The code just never caught up.

---

## Recommendation

**There should be one installer, not two.**

The specification defines one territory model, one install surface, one set of REQ keys. Platform variance (python vs codex vs java) is a parameter to `instantiate()`, not a reason for a separate installer.

The Python build (`builds/python/src/genesis_sdlc/install.py`) is the stronger foundation:
1. It delegates ABG installation (correct boundary)
2. It uses .gsdlc/release/ territory (correct model)
3. It has runtime_contract, provenance migration, audit
4. It parameterizes platform/src_dir

But it needs:
1. Fix ABG subprocess invocation (remove `--project-slug`)
2. Write `runtime_contract:` into `.genesis/genesis.yml` after ABG installs
3. Fix source root detection heuristic (no `gtl_spec/` in kernel)
4. Consolidate sdlc_graph.py (one file, parameterized)
5. Consolidate SDLC_BOOTLOADER.md (one file)
6. Fix command source paths
7. Reconcile bootloader version (1.1.1 vs 1.2.0)
8. Clean install into empty target as the release gate

The Codex build installer should be deleted. It is architecturally wrong and cannot be fixed without becoming the Python build.

---

## Clean Install Test Evidence

ABG v1.0 gen-install.py into empty `test_install/`:
```
status: installed
14 files, 8 engine modules, MCP transport, no domain leaks
genesis.yml: seed config, no binding — waiting for domain installer
```

Codex installer into empty `test_install/`:
```
status: partial
error: GENESIS_BOOTLOADER.md not found
engine: installed but stale (7 modules, no fp_dispatch)
territory: everything in .genesis/ — no .gsdlc/release/
contamination: abiogenesis.py and genesis_core.py in kernel
```

Python installer: not tested in this session (requires ABG subprocess invocation fix first).
