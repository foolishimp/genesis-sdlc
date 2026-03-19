# ADR-006: Test Version Sandboxing — Evaluator Commands Pin to RC Source

**Status**: Accepted
**Implements**: REQ-F-TEST-003
**Date**: 2026-03-19

## Context

genesis_sdlc dogfoods the discipline it enforces on downstream projects. One of the
SDLC principles is that every test layer must run against an explicitly pinned version
of the code under test — never the installed package from the environment.

During development, two versions of genesis_sdlc exist simultaneously:
- The **installed version** (`.genesis/spec/genesis_sdlc.py` — Layer 2, frozen)
- The **release candidate** (`builds/python/src/` — what we're building)

Without version pinning, `import genesis_sdlc` in a pytest test picks up whichever
version `sys.path` resolves first — typically the installed package, not the RC source.
This means tests pass on stale code, masking regressions in the RC.

## Decision

All F_D evaluator commands that invoke pytest or python one-liners must prepend:

```
PYTHONPATH=builds/python/src/:.genesis
```

This pins the import resolution to:
1. `builds/python/src/` — the RC source (genesis_sdlc package under development)
2. `.genesis` — the abiogenesis engine (GTL, genesis runner)

Affected evaluators in both `sdlc_graph.py` and `genesis_sdlc.py`:
- `tests_pass` — pytest run (already implemented)
- `e2e_tests_exist` — python one-liner checking for e2e markers (genesis_sdlc.py only)

UAT sandbox evaluator is unchanged — it already version-sandboxes correctly by
installing the RC into a fresh `/tmp` directory.

## Consequences

- **Positive**: Tests always run against the RC being evaluated, not the installed version.
  A failing RC produces failing tests regardless of what's installed.
- **Positive**: `gen gaps` works in an environment without genesis_sdlc installed at all.
- **Positive**: Mechanically enforces the same discipline genesis_sdlc recommends to users.
- **Neutral**: Evaluator commands are slightly longer, but this is a one-time change.
- **Negative**: None — the env var is standard and portable across POSIX systems.

## Alternatives Rejected

**Rely on virtual environment**: Fragile — depends on the active venv, which may have
an older release installed. The build loop should be hermetic.

**pytest conftest.py sys.path patch**: Breaks the F_D acyclicity constraint — conftest
runs inside pytest, which is the subprocess being evaluated.
