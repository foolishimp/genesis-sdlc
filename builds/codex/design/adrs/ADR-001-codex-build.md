# ADR-001: Stand Up a Standalone Codex Build

## Status

Accepted

## Context

`genesis_sdlc` previously only carried the Python/Claude realization. To close the
Codex bootstrap chain, the project needs a Codex-native build surface that can be
installed from the abiogenesis Codex seed without depending on the Python/Claude
authoring surface.

## Decision

Create a standalone Codex build under `builds/codex` with:

- `code/genesis_sdlc/` as the authoring source
- a Codex-native installer that copies the abiogenesis Codex engine seed directly
- Codex-specific evaluator paths and worker identity
- a restored private `builds/codex/.workspace/` territory for tenant-local traces

## Consequences

- The Codex path can evolve independently.
- The installer no longer shells out to the Claude build.
- Shared `.ai-workspace/` and private `builds/codex/.workspace/` remain separate runtime territories.
