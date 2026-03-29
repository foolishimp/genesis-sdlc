# Abiogenesis Python Qualification

**Status**: Active
**Path**: `build_tenants/abiogenesis/python/tests/`
**Purpose**: Canonical qualification root for the Abiogenesis/Python realization of genesis_sdlc

---

## Scope

This root owns the executable qualification surfaces for the active `abiogenesis/python` variant.

It contains:

- sandbox and workflow qualification under `tests/e2e/`
- archive and harness support under `tests/`
- the tenant-local test surface map for the active executable corpus

The governing test map is:

- [test_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/tests/test_surface_map.md)

## Boundary

This root does not define shared qualification law.

Shared qualification law lives under:

- [build_tenants/common/qualification/README.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/qualification/README.md)

Tests remain tenant-local unless explicitly promoted.
