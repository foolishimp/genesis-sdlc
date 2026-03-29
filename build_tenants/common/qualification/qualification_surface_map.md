# genesis_sdlc Qualification Surface Map

**Status**: Active
**Date**: 2026-03-30
**Derived from**: [07-testing.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/07-testing.md), [08-uat.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/08-uat.md), [13-bootloader-asset.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/13-bootloader-asset.md), [16-assurance.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/16-assurance.md), [module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md), [M04-evidence-acceptance.yml](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/modules/M04-evidence-acceptance.yml), [test_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/tests/test_surface_map.md)

## Purpose

Make the current `M04 evidence_acceptance` qualification boundary explicit during the `genesis_sdlc`
self-host migration to `gsdlc 1.0`.

This surface is structural only.
It does not change test behavior, test selection, or release criteria.

## Classification Rules

- `M04 evidence_acceptance` is the owning module for traceability, documentation certification, integration evidence, UAT support, bootloader validation, runtime provenance, and bundled fake/live qualification
- `build_tenants/common/qualification/` holds qualification law that is genuinely shared across realizations
- `build_tenants/abiogenesis/python/tests/` remains the canonical executable qualification root for the active variant
- executable qualification stays tenant-local unless another active tenant consumes it unchanged or it is rewritten as tenant-neutral shared law

## Current Shared Qualification Law

At this stage, the shared qualification surfaces are:

- this classification map
- the module-owned qualification boundary declared in `M04-evidence-acceptance.yml`

Executable qualification remains tenant-local.

## Canonical Python Qualification Root

The current canonical qualification root is:

- [build_tenants/abiogenesis/python/tests/README.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/tests/README.md)
- [build_tenants/abiogenesis/python/tests/test_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/tests/test_surface_map.md)

That root owns:

- executable `test_*.py` scenario and workflow qualification
- sandbox/archive harness support
- live and fake lane qualification over the resolved runtime path

## Shared-Candidate Qualification Surfaces Still Held In Python

These surfaces currently govern the released python qualification story but are not yet promoted into
`common/qualification/`.

| Surface | Current location | Why not yet promoted |
| --- | --- | --- |
| `tests/e2e/test_spec_method_trace.py` | `build_tenants/abiogenesis/python/tests/e2e/` | Repo-level self-host trace gate, but still written around the active python tenant and installed repo shape |
| `tests/run_archive.py` and `tests/e2e/sandbox_runtime.py` | `build_tenants/abiogenesis/python/tests/` | Canonical archive and sandbox harness, not yet exercised unchanged by another active tenant |
| `tests/e2e/live_transport.py` and `tests/e2e/minimal_project.py` | `build_tenants/abiogenesis/python/tests/e2e/` | Current qualification support surfaces remain python-tenant specific |

Promotion trigger:

- a second active tenant consumes the same qualification surface unchanged, or
- the surface is rewritten as tenant-neutral qualification law
