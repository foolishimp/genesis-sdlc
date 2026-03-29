# genesis_sdlc Python Test Surface Map

**Status**: Active
**Date**: 2026-03-30
**Derived from**: [07-testing.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/07-testing.md), [08-uat.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/08-uat.md), [13-bootloader-asset.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/13-bootloader-asset.md), [16-assurance.md](/Users/jim/src/apps/genesis_sdlc/specification/requirements/16-assurance.md), [qualification_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/qualification/qualification_surface_map.md), [module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md), [README.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/tests/README.md)

## Purpose

Review and trace the canonical `abiogenesis/python` executable test surface from live requirements
through design authority into the current `test_*.py` corpus.

This document is structural only.
It does not change what runs.

## Rule

Every `test_*.py` file under `build_tenants/abiogenesis/python/tests/e2e/` shall appear here with:

- the live requirement ids it validates
- the governing design surfaces it derives from

## Harness Support Surfaces

These files support the executable qualification root but are not themselves `test_*.py` entries in
this map:

- `tests/conftest.py`
- `tests/run_archive.py`
- `tests/e2e/sandbox_runtime.py`
- `tests/e2e/live_transport.py`
- `tests/e2e/minimal_project.py`

They remain governed by `M04-evidence_acceptance` and the shared qualification surface map.

## Executable Test Surfaces

### test_full_cycle.py

- Requirements: `REQ-F-CMD-001`, `REQ-F-GATE-001`, `REQ-F-DOCS-002`, `REQ-F-UAT-003`, `REQ-F-BOOTDOC-001`, `REQ-F-TEST-001`, `REQ-F-TEST-005`, `REQ-F-MVP-003`, `REQ-F-ASSURE-003`
- Design: [module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md), [M04-evidence-acceptance.yml](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/modules/M04-evidence-acceptance.yml), [ADR-002-assurance-control-plane.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/adrs/ADR-002-assurance-control-plane.md), [qualification_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/qualification/qualification_surface_map.md)

### test_sandbox_steel_thread.py

- Requirements: `REQ-F-CMD-001`, `REQ-F-GATE-001`, `REQ-F-GRAPH-001`, `REQ-F-TEST-001`, `REQ-F-MVP-002`, `REQ-F-ASSURE-002`
- Design: [module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md), [M04-evidence-acceptance.yml](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/modules/M04-evidence-acceptance.yml), [qualification_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/qualification/qualification_surface_map.md)

### test_sandbox_usecases_live.py

- Requirements: `REQ-F-CMD-001`, `REQ-F-TEST-001`, `REQ-F-TEST-004`, `REQ-F-TEST-005`, `REQ-F-MVP-003`, `REQ-F-ASSURE-002`
- Design: [module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md), [M04-evidence-acceptance.yml](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/modules/M04-evidence-acceptance.yml), [ADR-002-assurance-control-plane.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/adrs/ADR-002-assurance-control-plane.md), [qualification_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/qualification/qualification_surface_map.md)

### test_sandbox_workflow.py

- Requirements: `REQ-F-BOOT-001`, `REQ-F-BOOT-002`, `REQ-F-BOOT-003`, `REQ-F-BOOT-004`, `REQ-F-BOOT-005`, `REQ-F-BOOT-006`, `REQ-F-BOOT-007`, `REQ-F-BOOT-008`, `REQ-F-BOOT-009`, `REQ-F-TERRITORY-003`, `REQ-F-CUSTODY-002`, `REQ-F-CMD-001`, `REQ-F-CMD-002`, `REQ-F-CMD-003`, `REQ-F-GATE-001`, `REQ-F-TEST-001`, `REQ-F-TEST-003`, `REQ-F-UAT-001`, `REQ-F-ASSURE-002`, `REQ-F-CMD-004`, `REQ-F-CTRL-007`, `REQ-F-CTRL-008`, `REQ-F-WORKER-005`
- Design: [module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md), [M02-release-bootstrap.yml](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/modules/M02-release-bootstrap.yml), [M04-evidence-acceptance.yml](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/modules/M04-evidence-acceptance.yml), [qualification_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/qualification/qualification_surface_map.md)

### test_spec_method_trace.py

- Requirements: `REQ-F-BOOT-001`, `REQ-F-BOOT-010`, `REQ-F-BOOT-011`, `REQ-F-GRAPH-001`
- Design: [README.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/design/README.md), [module_decomp.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/abiogenesis/python/design/module_decomp.md), [qualification_surface_map.md](/Users/jim/src/apps/genesis_sdlc/build_tenants/common/qualification/qualification_surface_map.md)
