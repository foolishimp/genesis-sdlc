# Common Design

**Status**: Ratified
**Authority**: `build_tenants/README.md`
**Purpose**: Shared design surface for genesis_sdlc realization law

---

## Scope

`build_tenants/common/design/` is the shared design surface for cross-tenant realization rules.

It is where the repo defines:

- common realization principles
- shared build-tenant boundaries
- the family/variant hierarchy for tenant design
- the rules for promoting libraries or services to common use
- any design law that applies across more than one tenant

It is not tenant-local implementation design.

---

## Core Principles

1. A `build_tenant` is an inviolable local realization boundary.
2. Shared principles are written here, not inferred from a tenant implementation.
3. Shared libraries and shared services are common only after explicit adoption into `build_tenants/common/`.
4. Tenant-local implementation remains local even if another tenant happens to make a similar choice.
5. Cross-tenant sharing is explicit, never ambient.
6. Variant-local realization detail stays with the owning family or variant unless explicitly promoted.

---

## Naming Principle

Build-tenant names identify the stable family or variant boundary.

Family names express realization family or substrate.

Variant names express binding or deployment mode.

Qualifiers appear only when they carry real boundary meaning.

---

## Sharing Principle

Common assets are promoted, not assumed.

The promotion test is:

- the asset serves more than one tenant
- the asset has a shared contract or shared design law
- the asset is intended to remain tenant-neutral

If those claims do not hold, the asset remains tenant-local.

---

## Engine Boundary

Shared engine orchestration is not tenant design.

If a surface schedules, traverses, binds, or projects generic graph state across domains, it belongs
to the engine that consumes a tenant package, not to the tenant-local module schedule.

Tenant design owns:

- package declarations
- lifecycle nodes and vectors
- evaluator definitions and bindings
- release and evidence surfaces
- domain-local operational and homeostatic surfaces

Engine design owns:

- deterministic binding execution
- convergence queries and delta projection
- iterate/start traversal loops
- generic human-gate projection and dispatch ordering

Command requirements may remain active framework truth in specification without implying tenant-local
ownership of those engine surfaces.

---

## Shared Design Set

Upstream lifecycle ontology is defined in specification, especially:

- [02-graph.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/02-graph.md)
- [14-ecosystem-lifecycle.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/14-ecosystem-lifecycle.md)

The shared ADR set below is reserved for design-specific decisions that remain after that requirement truth is fixed.

- [ADR-001-realization-topology.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/design/adrs/ADR-001-realization-topology.md)
- [ADR-002-bootloader-and-control-carriers.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/design/adrs/ADR-002-bootloader-and-control-carriers.md)

These records define shared realization structure. Family-local and variant-local design belongs below the relevant family or variant surface, not here.
