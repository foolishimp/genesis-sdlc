# SDLC Bootloader

Version: 1.0rc1
Spec-Hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

## Authority

- genesis_sdlc owns the SDLC workflow surface.
- abiogenesis owns runtime orchestration.

## Axioms

- specification defines the what
- design defines the how
- convergence is evidence-driven

## Active Docs

- workspace://specification/INTENT.md
- workspace://build_tenants/TENANT_REGISTRY.md
- workspace://specification/requirements/02-graph.md
- workspace://build_tenants/common/design/README.md
- workspace://build_tenants/abiogenesis/python/design/module_decomp.md

## Commands

- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis gaps --workspace .`
- `PYTHONPATH=.gsdlc/release:.genesis python -m genesis iterate --workspace .`
