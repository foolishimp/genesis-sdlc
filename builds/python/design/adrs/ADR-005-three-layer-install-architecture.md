**Implements**: REQ-F-BOOT-003, REQ-F-BOOT-004, REQ-F-BOOT-005

# ADR-005: Three-Layer Install Architecture — Immutable Core vs Local Spec

**Status**: Accepted
**Date**: 2026-03-19
**Addresses**: REQ-F-BOOT-003/004/005
**Supersedes**: ADR-001 (install section only — package structure unchanged)

---

## Intent Traceability

**INT-001** identified the core value proposition:

> *"Traceability — REQ keys thread from intent through requirements, features, design, code, and tests."*
> *"AI in the right role — deterministic checks (F_D) run first."*

The installation architecture is the foundation that makes this possible in any downstream project. A broken install — one that conflates the frozen methodology with the mutable project spec — undermines traceability from the first `gen-start`. INT-001 implicitly requires install correctness.

**INT-002** (module_decomp) exposed the defect. Editing `gtl_spec/packages/genesis_sdlc.py` to add `module_decomp` immediately changed the live graph the v0.1.6 runner was evaluating. The `spec_hash` changed, old `fp_assessment` events became stale, and the `design→code` edge disappeared from the live evaluation. This is what a conflated spec/development surface looks like in practice.

**REQ-F-BOOT-001** requires `gen-install` to bootstrap `.genesis/` into a target project.
**REQ-F-BOOT-002** requires `genesis.yml` to resolve Package/Worker from the spec.
**REQ-F-BOOT-003/004/005** (this ADR) specify what must be true about the layering of those resolved packages.

---

## Context

ADR-001 established the package structure. The installer copies the abiogenesis runner into `.genesis/genesis/` and `.genesis/gtl/`. This is already correct and immutable.

What ADR-001 did not specify: the `genesis_sdlc` methodology graph (the standard SDLC Package) is currently written directly into `gtl_spec/packages/genesis_sdlc.py` — the same path used as the live runtime spec and as the source under active development. One module path carries three roles:

1. Last released `genesis_sdlc` baseline — should be frozen
2. Local project-spec surface — should be mutable
3. Next `genesis_sdlc` version under development — should be mutable (genesis_sdlc repo only)

The runner cannot distinguish between these. It evaluates whatever `gtl_spec.packages.genesis_sdlc` resolves to at invocation time. When a developer edits the spec mid-development, the live evaluation state changes immediately — spec_hash invalidation, edge topology changes, stale events.

*(Analysis developed collaboratively: Claude Code STRATEGY post `20260319T070000_STRATEGY_immutable-core-vs-local-spec.md` and Codex REVIEW `20260319T072724_REVIEW_response-to-claude-release-spec-conflation.md`.)*

---

## Decision

Three-layer install architecture. Each layer has a distinct owner, mutability, and update mechanism.

```
.genesis/
    genesis/                    ← Layer 1: abiogenesis runner (already correct)
    gtl/                        ← Layer 1: GTL primitives (already correct)
    spec/
        genesis_sdlc.py         ← Layer 2: released genesis_sdlc methodology (NEW)
    genesis.yml                 ← points to Layer 3 (local spec)

gtl_spec/
    packages/
        {project_slug}.py       ← Layer 3: local/project spec (mutable)
```

| Layer | Owner | Mutability | Updated by |
|-------|-------|-----------|------------|
| 1 — abiogenesis runner | abiogenesis release | Immutable | `gen-install --upgrade` |
| 2 — genesis_sdlc methodology | genesis_sdlc release | Immutable | `genesis_sdlc install --target` |
| 3 — local project spec | project | Mutable | developer |

---

## Layer 2: `.genesis/spec/genesis_sdlc.py`

Installed by `genesis_sdlc install` from the release source. Never edited by the project. Replaced atomically on upgrade.

The local spec (Layer 3) imports from this path:

```python
# gtl_spec/packages/myproject.py
from genesis.spec.genesis_sdlc import (
    intent, requirements, feature_decomp, design, module_decomp,
    code, unit_tests, uat_tests,
    standard_gate, claude_agent, human_gate,
    eval_intent_fh, eval_req_coverage, ...   # import only what you need
)

# Override evaluator commands for this project's layout
eval_impl_tags_local = Evaluator(
    "impl_tags", F_D,
    "All source files carry Implements: tags",
    command="python -m genesis check-tags --type implements --path src/",  # override
)

package = Package(
    name="myproject",
    assets=[intent, requirements, feature_decomp, design, code, unit_tests, uat_tests],
    edges=[...],   # use standard edges or override
    ...
)
```

---

## `genesis.yml` Resolution Rules

`genesis.yml` points to the **local spec** (Layer 3), not the installed core:

```yaml
package: gtl_spec.packages.{project_slug}:package
worker:  gtl_spec.packages.{project_slug}:worker
```

The local spec imports from Layer 2. This means:
- Editing `gtl_spec/packages/{slug}.py` changes the live evaluation (correct — that is the local surface)
- Editing `.genesis/spec/genesis_sdlc.py` is prohibited — changes are ignored until the next install (correct — that is immutable)
- Editing the released source (`builds/python/src/genesis_sdlc/sdlc_graph.py`) has no effect until release + install (correct — that is the development surface)

---

## The genesis_sdlc Self-Hosting Special Case

genesis_sdlc is self-hosting. During development, **both Layer 2 and Layer 3 must coexist**:

```
.genesis/spec/genesis_sdlc.py      ← Layer 2: frozen v0.1.6 (the prior release)
gtl_spec/packages/genesis_sdlc.py  ← Layer 3: v0.2.0 under development
```

`genesis.yml` points at Layer 3 during development (normal). The frozen Layer 2 exists for reference and for the post-release install test.

On release:
1. `builds/python/src/genesis_sdlc/sdlc_graph.py` is the canonical source
2. The release process copies it into `.genesis/spec/genesis_sdlc.py` of the genesis_sdlc repo (self-install)
3. Downstream installs copy it into their `.genesis/spec/genesis_sdlc.py`

After release, `gtl_spec/packages/genesis_sdlc.py` and `.genesis/spec/genesis_sdlc.py` are identical until the next development cycle begins.

---

## Installer Changes (REQ-F-BOOT-003/004/005)

`builds/python/src/genesis_sdlc/install.py` must be updated to:

**REQ-F-BOOT-003** — Copy released methodology into immutable layer:
```python
# Copy sdlc_graph.py into .genesis/spec/genesis_sdlc.py
spec_dest = target / ".genesis" / "spec"
spec_dest.mkdir(parents=True, exist_ok=True)
shutil.copy(source / "sdlc_graph.py", spec_dest / "genesis_sdlc.py")
# Also copy __init__.py so it's importable as genesis.spec.genesis_sdlc
(spec_dest / "__init__.py").touch()
```

**REQ-F-BOOT-004** — Generate starter local spec if not present:
```python
local_spec = target / "gtl_spec" / "packages" / f"{project_slug}.py"
if not local_spec.exists():
    local_spec.write_text(STARTER_LOCAL_SPEC_TEMPLATE.format(slug=project_slug))
# Never overwrite existing local spec — it contains project customisation
```

**REQ-F-BOOT-005** — Reinstall is idempotent and non-destructive:
- Replace `.genesis/spec/genesis_sdlc.py` unconditionally (immutable layer is always the release version)
- Never overwrite `gtl_spec/packages/{slug}.py` (local layer is owned by the project)

---

## Installation Test (per Codex recommendation)

Add to `test_installer.py`:

```python
# Validates: REQ-F-BOOT-003, REQ-F-BOOT-005
def test_immutable_layer_not_affected_by_local_spec_edit(tmp_path):
    """Editing gtl_spec/ after install must not change .genesis/spec/ content."""
    install(target=tmp_path, project_slug="test")
    frozen = (tmp_path / ".genesis/spec/genesis_sdlc.py").read_text()

    # Simulate developer editing local spec
    local = tmp_path / "gtl_spec/packages/test.py"
    local.write_text(local.read_text() + "\n# local edit\n")

    # Frozen layer must be unchanged
    assert (tmp_path / ".genesis/spec/genesis_sdlc.py").read_text() == frozen
```

---

## Consequences

**Positive**:
- Downstream projects always run against a known, stable methodology version
- Spec_hash is stable for the lifetime of an installed version — F_P assessment events remain valid until the project explicitly upgrades
- Development on genesis_sdlc no longer disturbs the live evaluation state of dependent projects
- Clear upgrade path: `genesis_sdlc install --target .` replaces Layer 2 only

**Trade-offs**:
- Two copies of `genesis_sdlc.py` in the genesis_sdlc repo during development — manageable given the self-hosting special case is well-understood
- Projects importing from `.genesis/spec/genesis_sdlc` have a non-standard import path — mitigated by the installer generating the correct import in the starter local spec
