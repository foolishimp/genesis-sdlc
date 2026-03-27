# Build Tenants

**Status**: Ratified
**Purpose**: Topology and registry root for shared and tenant-local realization surfaces

---

## Definition

A `build_tenant` is an inviolable realization boundary for a shared specification.

The repository specification defines the constitutional `what`.

`build_tenants/` defines the lawful `how` surfaces beneath that shared `what`.

`build_tenants/` may be hierarchical when one realization family has multiple bindings or deployment variants.

---

## Topology

- `build_tenants/common/` contains shared realization assets adopted across tenants
- `build_tenants/common/gtl/` contains portable GTL-level definitions and precedents intended to survive tenant changes
- `build_tenants/<family>/` contains family-level realization assets for one substrate or realization family
- `build_tenants/<family>/<variant>/` contains a concrete binding or deployment variant within that family
- `builds/<variant>/` contains the concrete implementation and runtime surface for a materialized variant in this repo

Nothing becomes shared merely because it exists in one family or variant.

Promotion to a shared surface is explicit.

---

## Principles

1. Tenanted builds are inviolable.
2. Shared principles, shared libraries, and shared services belong under `build_tenants/common/`.
3. Portable GTL-level definitions belong under `build_tenants/common/gtl/`, not inside one tenant family.
4. Family-local prompts, tooling, design, traces, and implementation remain under that family or variant unless explicitly promoted.
5. A folder under `builds/` is not authoritative merely by existing.
6. Shared realization law is written under `build_tenants/common/`, not inferred from any tenant implementation.

---

## Naming Principle

Names should identify the stable boundary that explains why the realization is separate.

Family names express realization families or substrates.

Variant names express bindings or deployment modes within a family.

Names remain concise. Qualifiers appear only when they carry real boundary meaning.

---

## Registry

| Entry | Kind | Path | Status | Notes |
| --- | --- | --- | --- | --- |
| `common` | shared root | `build_tenants/common/` | Active | Shared realization law across all tenants |
| `common/gtl` | shared definition layer | `build_tenants/common/gtl/` | Active | Portable GTL definitions and precedents intended to survive tenant changes |
| `abiogenesis` | family | `build_tenants/abiogenesis/` | Active | Current realization family built on Abiogenesis |
| `abiogenesis/python` | variant | `build_tenants/abiogenesis/python/` and `builds/python/` | Active | Current active binding and implementation surface |

---

## Surface Roles

`build_tenants/common/` carries shared realization law.

`build_tenants/common/gtl/` carries portable GTL definitions and precedents.

`build_tenants/<family>/` carries family-level realization law.

`build_tenants/<family>/<variant>/` and `builds/<variant>/` carry variant-local realization surfaces.

The registry is the reminder surface for the LLM: shared is explicit, tenant-local is inviolate.
