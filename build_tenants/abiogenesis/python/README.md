# Abiogenesis Python Variant

**Status**: Ratified
**Path**: `build_tenants/abiogenesis/python/`
**Purpose**: Abiogenesis and GTL realization surface for genesis_sdlc on Python

---

## Scope

The `abiogenesis/python` variant owns the concrete Python realization surfaces for this family.

Its design surfaces are:

- [design/README.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/README.md)
- [design/module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md)
- `design/modules/*.yml`
- [tests/README.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/tests/README.md)
- [tests/test_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/tests/test_surface_map.md)

Concrete source, test, and release directories live under this variant.

---

## Boundary

The `abiogenesis/python` variant does not own shared constitutional truth.

It realizes:

- `specification/`
- `build_tenants/common/`
- `build_tenants/abiogenesis/`

Any principle, library, or service discovered inside the `abiogenesis/python` variant becomes shared only after explicit adoption into a common surface.
