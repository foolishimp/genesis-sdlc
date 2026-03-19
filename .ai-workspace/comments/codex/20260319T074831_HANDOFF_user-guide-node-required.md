# HANDOFF: User Guide Must Be a Graph Node

**Author**: Codex
**Date**: 2026-03-19T07:48:31Z
**Addresses**: current `genesis_sdlc` graph topology; `REQ-F-DOCS-001`; BOOT-V2 work
**For**: claude

## Summary

Do not lose the user-guide requirement while the install-layer split is being worked. The current package lists documentation as a REQ key, but the guide is not a first-class asset. That means documentation can drift without affecting delta or convergence. If changes are supposed to be traceable to the user guide the same way they are traceable to code and tests, the guide has to sit on the graph.

## Current Implementation Reality

The live package includes `intent`, `requirements`, `feature_decomp`, `design`, `module_decomp`, `code`, `unit_tests`, and `uat_tests`. There is no `user_guide` asset in `gtl_spec/packages/genesis_sdlc.py`.

The live edge set ends at `unit_tests→uat_tests`. There is no job whose convergence depends on the guide.

`REQ-F-DOCS-001` exists in the package requirements list. `.ai-workspace/features/completed/REQ-F-DOCS.yml` also exists. That records intent. It does not create an executable convergence contract.

`docs/USER_GUIDE.md` exists, but no F_D evaluator checks it and no F_P evaluator certifies it. There is no `edge_converged` certificate for documentation and no delta surface for stale operator docs.

Drift is already visible. `builds/python/src/genesis_sdlc/__init__.py` and `builds/python/src/genesis_sdlc/install.py` report version `0.1.7`. `docs/USER_GUIDE.md` still says `Version: 0.1.3`.

## Consequence

The current model guarantees that code, tests, and UAT participate in convergence. It does not guarantee that the operator-facing guide reflects the shipped behavior.

A listed REQ key is not enough. Requirements become enforceable when they are bound to assets, edges, and evaluators. Without that binding the guide is outside the constitutional path.

## Required Contract

The user guide needs to become a first-class asset with its own lineage, edge placement, and evaluators.

The exact placement is a design choice. The invariant is not. Workspace convergence must fail when the guide is stale.

The traceability contract for the guide should be explicit. Markdown tags such as `<!-- Covers: REQ-* -->` are the obvious form.

The F_D side then needs a deterministic coverage check over the guide surface. Scope that check to the public or operator-facing REQ set, not to every internal invariant.

The F_P side should certify that the guide still answers the operational questions a practitioner needs: install, first session, commands, operating loop, and recovery paths.

## Recommended Action

1. Carry a DOCS-V2 feature alongside BOOT-V2 so the graph change is not dropped during install work.
2. Add `user_guide` as an asset in `gtl_spec/packages/genesis_sdlc.py`.
3. Put the guide on the blocking path so total convergence cannot be true while docs are stale.
4. Add markdown traceability tags and a deterministic evaluator for guide coverage.
5. Add at least one test that changes a public command or versioned behavior and proves the docs edge fails until the guide is updated.
