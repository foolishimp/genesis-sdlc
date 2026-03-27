# Abiogenesis Python Variant

**Status**: Ratified
**Path**: `builds/python/`
**Purpose**: Current active Abiogenesis binding for genesis_sdlc implementation

---

## Scope

The `abiogenesis/python` variant owns the concrete Python realization surfaces:

- implementation under `builds/python/src/`
- tests under `builds/python/tests/`
- tenant-local design under `builds/python/design/`
- packaging, release, and sandbox execution surfaces under `builds/python/`

---

## Boundary

The `abiogenesis/python` variant does not own shared constitutional truth.

It realizes:

- `specification/`
- `build_tenants/common/`
- `build_tenants/abiogenesis/`

Any principle, library, or service discovered inside the `abiogenesis/python` variant becomes shared only after explicit adoption into a common surface.
