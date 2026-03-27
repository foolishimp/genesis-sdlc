# Abiogenesis Family

**Status**: Ratified
**Purpose**: Realization family for genesis_sdlc variants built on Abiogenesis

---

## Scope

`build_tenants/abiogenesis/` is the family boundary for implementations that realize the shared specification through Abiogenesis.

It is where the repo records:

- family-level realization assumptions
- family-local design law that applies across Abiogenesis variants
- the set of active Abiogenesis variants

It does not own portable GTL definition law.

---

## Boundary

The Abiogenesis family realizes:

- `specification/`
- `build_tenants/common/`
- `build_tenants/common/gtl/`

Current active variant:

- [python/README.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/README.md)

Future variants may include other bindings or deployment modes under this family when they become real.
