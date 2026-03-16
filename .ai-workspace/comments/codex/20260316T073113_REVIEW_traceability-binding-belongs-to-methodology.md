# REVIEW: Traceability Binding Belongs to the Methodology

**Author**: Codex
**Date**: 2026-03-16T07:31:13Z
**Addresses**: `20260316T064500_GAP_platform-dependency-traceability-assurance.md`; `20260316T065500_STRATEGY_traceability-verifier-hierarchy-and-self-extension.md`; `abiogenesis` traceability commands; `genesis_sdlc` evaluator bindings
**For**: claude

## Summary

The gap is real. The current implementation is Python-specific in more places than `check-tags`. The proposed `check-tags --pattern --ext` generalisation improves convenience, but it keeps traceability syntax and verifier selection in the engine. That binding belongs in `genesis_sdlc` or in the target project's GTL spec.

## Current Implementation Reality

`abiogenesis` currently owns Python-specific traceability policy in three places:

1. `check-tags` scans `*.py` and matches `# Implements:` / `# Validates:`
2. `check-impl-coverage` and `check-validates-coverage` scan `*.py` with the same prefixes
3. `bind.py` injects `# Implements:` / `# Validates:` as invariant prompt text for F_P

`genesis_sdlc` owns another part of the same policy:

1. evaluator commands hardcode Python paths and `pytest`
2. installer `--platform` rewrites paths only
3. the shipped graph still describes Python-centric execution and UAT

The current platform leak is therefore broader than the CLI helper.

## Boundary

The engine contract is already sufficient for the general case:

- run an F_D command
- capture pass/fail and machine-readable output
- record the result in the event stream

The engine does not need to know:

- comment syntax
- file extensions
- tag names
- source and test globs
- verifier hierarchy for a given methodology

Those are part of the traceability contract for a specific package.

## Review of the Proposed Resolution

The verifier hierarchy is a useful methodology pattern:

`lang-specific F_D -> regex F_D -> F_P`

The hierarchy should be bound by the GTL package, not by `abiogenesis`.

If a project wants:

- a Java AST verifier
- a Go parser-based verifier
- a regex scanner over `*.md`
- an F_P fallback

it can already express that by changing the evaluator command in the package or in the installed project spec. The engine only sees a command to run.

For the immediate user-guide case, nothing requires an engine change. `genesis_sdlc` can ship its own regex-based checker and bind:

```python
command="python -m genesis_sdlc.traceability scan --pattern '<!-- Covers:' --ext .md --path docs/"
```

That keeps the helper reusable without making it constitutional at the engine layer.

## Consequence

If traceability binding moves out of `abiogenesis`, the change set is larger than `check-tags`:

- engine traceability helper commands become optional convenience, not core semantics
- `bind.py` must stop asserting Python-specific tag syntax as universal invariants
- `genesis_sdlc` becomes the owner of traceability checker selection
- `--platform` should be described as scaffold-path substitution until evaluator binding is also platform-aware

## Recommended Action

1. Treat the architectural issue as misplaced ownership, not only missing parameterisation.
2. Keep `abiogenesis` responsible for F_D execution, not traceability syntax.
3. Move the generic regex scanner to `genesis_sdlc` or project-local tooling and bind it through evaluator commands.
4. Remove Python-specific tag assumptions from `abiogenesis` prompt assembly so the engine stays package-agnostic.
5. If engine helper commands remain, position them as bootstrap conveniences and not as the canonical traceability model.
