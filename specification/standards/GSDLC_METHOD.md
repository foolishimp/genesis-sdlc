# GSDLC Method

**Governance**: Maintained by the methodology author. Read-only for agents. Propose changes via `STRATEGY` post.

**Derived from**: `SPEC_METHOD.md`

**Scope**: Domain refinement of the general spec-driven method for the software development process domain implemented by `genesis_sdlc`.

---

## Position

`SPEC_METHOD.md` is the general baseline.

`GSDLC_METHOD.md` is the software-development-process refinement of that baseline.

`*_GUIDE.md` files are application standards that explain how to operate within the method.

`*_TEMPLATE.md` files are starter scaffolds and examples. They are convenience surfaces, not constitutional authority.

---

## Domain Boundary

Within this architecture:

- `genesis_sdlc` is the software development process domain
- `abiogenesis` is the engine/runtime that realizes declared process structure
- project `INTENT.md`, `requirements/`, design, code, and evidence surfaces are downstream of the method

Therefore the canonical software-development-process doctrine belongs with `genesis_sdlc`, not with the ABG engine.

---

## Folder Semantics

`specification/standards/` is the canonical methodology folder for genesis_sdlc.

It contains three classes of document:

- `*_METHOD.md` — process constitutions and domain refinements
- `*_GUIDE.md` — operational guides and writing/application standards
- `*_TEMPLATE.md` — reusable starter forms and examples

Only `*_METHOD.md` documents are constitutional method surfaces.

`*_GUIDE.md` documents refine how the method is applied.

`*_TEMPLATE.md` documents are convenience artifacts only.

---

## GSDLC Refinements

The genesis_sdlc method refines the general baseline in these ways:

- the live requirement surface is folder-based under `specification/requirements/`
- requirements may be stored individually or in requirement families
- the method is declarative-first: truth, structure, evaluators, and evidence surfaces are declared before imperative mechanism
- the software-development-process domain is upstream of the engine that executes it

These refinements specialize the baseline method. They do not replace it.
