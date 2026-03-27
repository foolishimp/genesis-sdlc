# ADR-003 — Base Process Workflow

**Status**: Approved
**Date**: 2026-03-27
**Implements**: REQ-F-GRAPH-*, REQ-F-MDECOMP-*, REQ-F-DOCS-*, REQ-F-UAT-*, REQ-F-BOOTDOC-*

---

## Context

genesis_sdlc needs one shared base process workflow for the software-development lifecycle that can be realized across build-tenant families and variants.

Three source surfaces matter here:

- the current gsdlc intent and requirement surface, which already ratifies an 11-asset DAG
- the SDLC-lite GTL tests in abiogenesis, which show that smaller review and zoom variants can be declared lawfully in GTL
- the GTL use-case mockup for U1-U4, which shows profile selection, gap-triggered refinement, consensus review, and parallel harvest as reusable operator patterns

These sources do not carry the same authority.

The current gsdlc specification defines the constitutional baseline for the base process.

The SDLC-lite tests and GTL mockups are design evidence. They prove that alternative shapes and richer operator patterns are realizable, but they do not by themselves redefine the base process workflow.

---

## Decision

The base process workflow for genesis_sdlc is the current 11-asset, 10-edge lifecycle shape:

```text
intent → requirements → feature_decomp → design → module_decomp
module_decomp → code
module_decomp → unit_tests
[code, unit_tests] → integration_tests
[design, integration_tests] → user_guide
[requirements, design, integration_tests] → bootloader
[requirements, integration_tests] → uat_tests
```

The baseline asset set is:

- `intent`
- `requirements`
- `feature_decomp`
- `design`
- `module_decomp`
- `code`
- `unit_tests`
- `integration_tests`
- `user_guide`
- `bootloader`
- `uat_tests`

This is shared lifecycle law for the base software-development process. It is not specific to one engine, one build-tenant family, one implementation language, or one encoding strategy.

The graph is one lawful encoding of this workflow. Other solutions may encode the same workflow differently, provided they preserve the same lifecycle obligations and dependency order.

---

## Scope

The base process workflow scope includes:

- the shared lifecycle stages that every conformant realization must respect
- the structural dependency order between those stages
- the split between creative lineage and evidence prerequisites already ratified in the current workflow shape
- `bootloader` as a compiled graph asset rather than a hand-maintained side document
- `module_decomp` as the structural bridge between design and construction

The base process workflow scope does not include:

- profile selection or candidate-family choice as part of the graph shape
- gap-triggered refinement as a mandatory baseline feature
- explicit review vectors, consensus rounds, or parallel candidate harvest as mandatory baseline nodes
- role assignment, worker mix, or multi-worker routing
- concrete carrier filenames or concrete implementation layout
- family-local or variant-local realization detail

Those concerns remain lawful design techniques below the base process workflow. They may refine how a lifecycle boundary is realized without becoming new baseline stages by default.

---

## Derived Interpretation Of The Reference Material

The SDLC-lite GTL helper contributes two useful readings:

- `requirements → design → code` proves a lawful minimal path
- review and zoom variants prove that explicit `design_review` or intermediate planning stages can be expressed as design variants

Those are valid realizations of slices of the lifecycle, but they are not the base process workflow because the current gsdlc specification already ratifies a richer lifecycle surface.

The GTL U1-U4 mockup contributes a second reading:

- `candidate_family` is a profile-selection mechanism
- `deferred_refinement` is a lawful topology-change boundary
- `fan_out`, `fan_in`, `gate`, and `recurse` express review, consensus, and harvest patterns

These are operator-level patterns for realizing workflow boundaries. They belong to GTL and downstream design, not to the base process workflow itself.

---

## Consequences

- common design now has one fixed base process workflow to converge around
- realization families and variants may encode or implement richer edge internals without redefining the shared lifecycle stages
- review, zoom, profile, and harvest patterns stay available as optional refinements
- if a future lifecycle stage is important enough to become base-process law, it must first be repriced into intent and requirements rather than entering through implementation precedent

The base process workflow is not the whole ecosystem lifecycle. Operational extension and the homeostatic return path are defined separately in shared design.
