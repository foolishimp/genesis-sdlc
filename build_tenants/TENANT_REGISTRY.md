# Tenant Registry

**Status**: Ratified
**Purpose**: Canonical registry and topology root for shared and tenant-local realization surfaces

---

## Definition

A `build_tenant` is an inviolable realization boundary for a shared specification.

The repository specification defines the constitutional `what`.

`build_tenants/` defines the lawful `how` surfaces beneath that shared `what`.

`build_tenants/` may be hierarchical when one realization family has multiple bindings or deployment variants.

One project specification may therefore support `1 -> n` independent build tenants.

---

## Topology

- `build_tenants/common/` contains shared realization assets adopted across tenants
- `build_tenants/<family>/` contains family-level realization assets for one substrate or realization family
- `build_tenants/<family>/<variant>/` contains a concrete binding or deployment variant within that family

Nothing becomes shared merely because it exists in one family or variant.

Promotion to a shared surface is explicit.

---

## Principles

1. Tenanted builds are inviolable.
2. Shared principles, shared libraries, and shared services belong under `build_tenants/common/`.
3. Family-local prompts, tooling, design, traces, and implementation remain under that family or variant unless explicitly promoted.
4. Shared realization law is written under `build_tenants/common/`, not inferred from any tenant implementation.
5. A project may define multiple build tenants while actively working on only one tenant at a time.

---

## Naming Principle

Names should identify the stable boundary that explains why the realization is separate.

Family names express realization families or substrates.

Variant names express bindings or deployment modes within a family.

Names remain concise. Qualifiers appear only when they carry real boundary meaning.

---

## Registry

This file is the canonical registry surface for project build tenants.

It should record:

- the shared roots
- each family and variant
- its current lifecycle state
- any operator note needed to understand active focus

Suggested lifecycle states include:

- `In Development`
- `Paused`
- `Released`
- `Deprecated`

| Entry | Kind | Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `common` | shared root | `build_tenants/common/` | Active | Shared realization law across all tenants |
| `abiogenesis` | family | `build_tenants/abiogenesis/` | Active | Realization family built on Abiogenesis |
| `abiogenesis/python` | variant | `build_tenants/abiogenesis/python/` | Active | ABG and GTL realization surface on Python |

---

## Surface Roles

`build_tenants/common/` carries shared realization law.

`build_tenants/<family>/` carries family-level realization law.

`build_tenants/<family>/<variant>/` carries variant-local realization surfaces.

The tenant registry is the reminder surface for the LLM and the operator: shared is explicit, tenant-local is inviolate, and active tenant status is explicit rather than ambient.
