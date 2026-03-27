# ADR-001 — Realization Topology

**Status**: Approved
**Date**: 2026-03-27
**Implements**: REQ-F-GRAPH-*, REQ-F-BOOT-*, REQ-F-TERRITORY-*

---

## Context

The specification defines the SDLC constitutional `what`, but the repository still needs a shared realization topology for how multiple lawful realizations are organized.

That topology must satisfy four constraints:

- shared GTL-level definition law must remain portable
- shared design law must not be inferred from one implementation
- different realization families must be able to coexist without ambient bleed
- concrete implementation layout must remain downstream of design rather than being treated as constitutional by habit

---

## Decision

genesis_sdlc adopts a hierarchical realization topology:

- `build_tenants/common/` is the shared realization root
- `build_tenants/common/gtl/` holds portable GTL-level definitions and precedents
- `build_tenants/common/design/` holds shared design law across realization families
- `build_tenants/<family>/` holds family-level realization surfaces for one substrate or realization family
- `build_tenants/<family>/<variant>/` holds a concrete binding or deployment variant within that family

The current active realization family is `abiogenesis`.

The current active variant is `abiogenesis/python`.

No folder becomes authoritative merely by existing. Authority flows from ratified design surfaces, not from ambient filesystem precedent.

---

## Consequences

- GTL portability is preserved as a shared surface rather than hidden inside one family
- new realization families can be added without redefining the constitutional specification
- family-local and variant-local design can diverge lawfully without contaminating common design
- any future concrete implementation layout must be intentionally adopted beneath the family or variant that owns it
