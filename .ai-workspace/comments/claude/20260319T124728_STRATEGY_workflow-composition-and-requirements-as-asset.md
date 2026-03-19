# STRATEGY: Workflow Composition and Requirements as First-Class Asset

**Author**: Claude Code
**Date**: 2026-03-19T12:47:28Z
**Addresses**: genesis_sdlc installer 4-layer model; `Package.requirements` conflation; local overlay escape hatch
**For**: all

## Summary

Two related architectural decisions emerged from design review. First: project-level customisation belongs at the workflow variant level, expressed through named versioned releases of genesis_sdlc, composed from primitives — not through per-project local overlays. Second: `Package.requirements` conflates graph topology with workspace asset; requirements are produced by iteration of the `intent → requirements` edge and become `Context[]` for downstream edges, identical in kind to any other converged asset.

---

## Decision 1 — Customisation Through Variant Composition

### Current model (4-layer)

```
Layer 1  .genesis/genesis/                     abiogenesis engine
Layer 2  .genesis/workflows/genesis_sdlc/vX_Y_Z/  versioned release
Layer 3  gtl_spec/packages/{slug}.py           generated wrapper
Layer 4  gtl_spec/packages/{slug}_local.py     user-owned overlay
```

Layer 4 exists because the generator anticipated projects needing to deviate from the base workflow. In practice, every category of deviation maps to one of:

| What someone would put in the overlay | What it actually is |
|--------------------------------------|---------------------|
| Stricter evaluators, code review gates | Workflow variant — sharable |
| Collapsed graph (skip module_decomp) | Named projection — sharable |
| Additional F_H gates | Workflow policy — sharable |
| Project slug, requirement keys | Instantiation data — not customisation |

Nothing is genuinely project-local except the slug and the requirements — and requirements are a workspace asset, not a parameter (see Decision 2).

### Proposed model

Customisation is expressed as a named versioned variant of genesis_sdlc, composed from primitives:

```
genesis_sdlc.standard        — base SDLC graph
genesis_sdlc.enterprise      — standard + architecture review gate + compliance edges
genesis_sdlc.poc             — collapsed graph, module_decomp removed
genesis_sdlc.regulated       — standard + audit trail + security evaluators
```

Each variant is a proper Python package with its own versioned releases, test suite, and `instantiate(slug)` entry point. Variants compose from each other and from shared edge/evaluator libraries.

The generated wrapper becomes a pure instantiation binding:

```python
# genesis_sdlc-generated — data binding only
from workflows.genesis_sdlc.enterprise.v1_2_0 import instantiate
package, worker = instantiate(slug="my_proj")
```

Layer 4 (`{slug}_local.py`) is removed. Customisation that cannot be expressed as a variant is explicitly out of scope for the automated upgrade path.

### Consequences

- Every customisation is versioned, tested, and shareable across projects using the same variant.
- The upgrade path from vX to vY is always clean — no per-project overlay drift to reconcile.
- The contribution model is explicit: propose a variant or extension to genesis_sdlc rather than editing a local file.
- The installer simplifies: no overlay template, no overlay-existence check, no `customize_package`/`customize_worker` protocol.

### Open question

The variant selection mechanism. `active-workflow.json` currently records `{"workflow": "genesis_sdlc", "version": "0.2.0"}`. With named variants this becomes `{"workflow": "genesis_sdlc.enterprise", "version": "1.2.0"}`. The installer needs a `--workflow` flag; the generated wrapper imports from the selected variant's versioned path.

---

## Decision 2 — Requirements as Converged Asset, Not Package Parameter

### The conflation

```python
package = Package(
    requirements=["REQ-F-BOOT-001", "REQ-F-BOOT-002", ...],
    ...
)
```

`Package` is a graph definition: topology, evaluators, operators. `requirements` is the stable output of the `intent → requirements` edge traversal — a workspace artifact. These are different things occupying the same field.

The current `req_coverage` evaluator reads `package.requirements` (a Python list frozen at import time). This is why the generated wrapper had to override it with a slug-specific command pointing at the project's Package object — to avoid the evaluator checking genesis_sdlc's own requirements list against the project's feature vectors.

### The formal system reading

`iterate()` takes:

```
iterate(Asset<Tn>, Context[], Evaluators(edge_type)) → Event+
```

`Context[]` is the set of stable assets accumulated from prior edge convergences. The requirements document joins `Context[]` after the `intent → requirements` edge converges. It is `Context[1]` for every downstream edge. This is identical in kind to how the design document becomes context for `module_decomp`, or how module_decomp becomes context for `code`.

The `intent → requirements` edge is the edge at which the requirements context item is produced. Requirements are not special. They are asset zero — the first stable artifact in the graph.

### The clean model

```
Graph traversal:
  Edge 1: intent → requirements
    Context[] = [intent_doc]
    Produces: requirements_doc → workspace artifact → joins Context[]

  Edge 2: requirements → feature_decomp
    Context[] = [intent_doc, requirements_doc]
    Produces: feature_decomp → joins Context[]

  Edge N: ...
    Context[] = [intent_doc, requirements_doc, feature_decomp, design, ...]
```

`Package.requirements` either:

- **Is removed** from the Package primitive. The graph topology (Package) carries no workspace state.
- **Is derived** at load time from the workspace artifact if present, empty otherwise.

The first option is cleaner. `Package` defines the graph. The workspace holds the assets. These are distinct concerns.

### The `req_coverage` evaluator

Reads directly from the workspace requirements artifact:

```bash
python -m genesis check-req-coverage --workspace .
```

No slug. No Package import. The evaluator compares REQ keys in the stable requirements artifact against REQ keys in the `satisfies:` fields of feature vectors. Both live in the workspace.

The slug-specific override in the generated wrapper disappears. The wrapper has nothing to override.

### Self-consistency of genesis_sdlc's own spec

`sdlc_graph.py` currently carries `package.requirements = ["REQ-F-BOOT-001", ...]`. This is correct for genesis_sdlc-the-product: those requirements are the stable output of genesis_sdlc's own `intent → requirements` iteration, committed to the repo as part of its workspace state. The list belongs there because genesis_sdlc iterated and produced it. It is not a template pattern for installed projects.

When a project installs genesis_sdlc, their requirements do not exist yet. Their `package.requirements` starts empty. Their requirements emerge from their own iteration of the `intent → requirements` edge.

### Consequences

- `Package.requirements` for installed projects is always empty at install time. No pre-declaration required.
- `req_coverage` evaluator is slug-agnostic. No override in the generated wrapper.
- The generated wrapper loses both overrides (`_eval_req_coverage` and `_this_spec` context) and becomes a pure instantiation binding.
- The requirements artifact path needs a canonical workspace location (proposed: `.ai-workspace/assets/requirements.md`).
- The `intent → requirements` edge F_D evaluators need to check artifact existence, format validity, and non-emptiness.

---

## Interaction Between Decisions

Decision 1 eliminates the overlay. Decision 2 eliminates the two overrides in the generated wrapper. Together, the generated wrapper becomes:

```python
# genesis_sdlc-generated — data binding only
from workflows.genesis_sdlc.standard.v0_2_0 import instantiate
package, worker = instantiate(slug="my_proj")
```

The `instantiate()` function in the variant sets `name=slug`, `requirements=[]`, and the correct `this_spec` context locator. The wrapper contains no logic. There is nothing to override at the project level.

---

## What Requires Spec Change vs. Implementation Change

| Item | Scope |
|------|-------|
| Remove `Package.requirements` field (or make it derived) | GTL primitive — spec-level ADR required |
| `req_coverage` reads from workspace artifact | genesis_sdlc evaluator implementation |
| Named variant packages (`genesis_sdlc.enterprise`, etc.) | genesis_sdlc project structure |
| `--workflow` flag on installer | genesis_sdlc installer |
| Remove Layer 4 (`{slug}_local.py`) | genesis_sdlc installer |
| `instantiate(slug)` entry point per variant | genesis_sdlc variant API |
| Canonical requirements artifact path | Workspace convention — operating standards |

The GTL primitive change (removing or deriving `Package.requirements`) requires a spec-level ADR because it affects any workflow built on GTL, not just genesis_sdlc.

---

## Recommended Action

1. Ratify or reject the two decisions independently — they are separable.
2. If Decision 2 is accepted, raise a spec-level ADR for the `Package.requirements` primitive change before any implementation work.
3. If Decision 1 is accepted, define the variant naming convention and the `instantiate(slug)` API contract before restructuring the installer.
4. The current 4-layer installer implementation remains valid as a transitional state. No immediate rollback needed.
