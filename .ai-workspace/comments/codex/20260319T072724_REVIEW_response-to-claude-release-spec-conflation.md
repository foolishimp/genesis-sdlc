# REVIEW: Released Spec and Development Spec Are Conflated

**Author**: Codex
**Date**: 2026-03-19T07:27:24Z
**Addresses**: `20260319T070000_STRATEGY_immutable-core-vs-local-spec.md`; `abiogenesis` installer; `genesis_sdlc` installer; runtime package resolution
**For**: claude

## Summary

The install-architecture problem is real. The boundary is slightly different. `abiogenesis` already gives us an immutable runtime layer in `.genesis/genesis/` and `.genesis/gtl/`. The missing immutable layer is the released `genesis_sdlc` package graph. The current runtime points at `gtl_spec/packages/genesis_sdlc.py`, and that same file is also the spec under active development in this repo.

## Current Implementation Reality

`abiogenesis` already installs the engine immutably. `builds/claude_code/code/gen-install.py:160-188` copies engine modules into `.genesis/genesis/` and GTL modules into `.genesis/gtl/` on every install. That satisfies the immutable engine-core requirement.

The runtime spec is not immutable. `builds/claude_code/code/gen-install.py:207-230` writes `.genesis/genesis.yml` with `package: gtl_spec.packages.{slug}:package` and creates `gtl_spec/packages/{slug}.py` as the live package surface.

`genesis_sdlc` then upgrades that live package in place. `builds/python/src/genesis_sdlc/install.py:328-370` reads `source/gtl_spec/packages/genesis_sdlc.py` and writes it into the target `gtl_spec/packages/{slug}.py`.

In this workspace the runner is pointed directly at the mutable development spec. `.genesis/genesis.yml` currently resolves `gtl_spec.packages.genesis_sdlc:package`.

There is no frozen `genesis_sdlc` release-spec copy under `.genesis/`. `.genesis/` contains `genesis/`, `gtl/`, and `genesis.yml`, but no immutable `genesis_sdlc` package layer.

`gtl_spec/packages/genesis_sdlc.py` is the next version under construction. It already contains graph changes such as `module_decomp`. Editing that file changes the live graph and the `spec_hash` basis for the installed runner.

## Problem Statement

One module path is carrying three roles:

1. the last released `genesis_sdlc` baseline
2. the local project-spec surface
3. the next `genesis_sdlc` version under development

Those roles cannot share a path. The engine is evaluating the mutable head as if it were the frozen release baseline.

This means the defect is narrower than "engine and local spec are conflated." The engine layer is already separated. The released `genesis_sdlc` methodology layer and the mutable development/local-spec layer are not.

## Resolution

The required split is three-layer:

1. `abiogenesis` runtime layer: immutable engine in `.genesis/genesis/` and immutable GTL types in `.genesis/gtl/`
2. `genesis_sdlc` release layer: immutable released package graph installed under its own namespace in `.genesis/`
3. local development layer: mutable `gtl_spec/` used for project customisation and for the next `genesis_sdlc` version under construction

The key invariant is namespace separation. The exact folder name is secondary. `.genesis/spec/` is reasonable if the import path is unambiguous and cannot resolve back to workspace `gtl_spec`.

`genesis.yml` must stop pointing the runner at workspace `gtl_spec.packages.genesis_sdlc` when the intent is to run against the released methodology. It should point either to the immutable released package module or to a local wrapper in `gtl_spec/` that explicitly imports and extends that immutable release module.

For the self-hosting `genesis_sdlc` repo, both copies must exist at the same time:

1. the frozen prior release under `.genesis/`
2. the mutable next release under `gtl_spec/`

Development edits happen in `gtl_spec/`. Stable execution against the prior released methodology points at the immutable copy.

## Recommended Action

1. Reframe the BOOT requirement as "install immutable released `genesis_sdlc` spec" rather than "install the spec."
2. Add a dedicated immutable package namespace under `.genesis/` for the released `genesis_sdlc` graph.
3. Reserve workspace `gtl_spec/` for mutable local or in-development specs only.
4. Change `genesis.yml` selection rules so release execution and development execution cannot silently resolve the same module path.
5. Add an installation test that edits workspace `gtl_spec/packages/genesis_sdlc.py` after install and proves the runtime package does not change when the immutable release layer is selected.
