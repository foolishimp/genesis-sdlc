# ADR-010: Test Structure and Coverage Evaluation

**Status**: Accepted
**Date**: 2026-03-21
**Implements**: REQ-F-TEST-001, REQ-F-TEST-002, REQ-F-GATE-001

## Context

The `code↔unit_tests` edge needs evaluators that enforce test quality without creating circular dependencies. F_D evaluators must not invoke genesis subcommands (acyclicity constraint).

## Decision

### Primary test surface: integration and e2e (REQ-F-TEST-001)

`@pytest.mark.e2e` tests are the acceptance proof. They exercise the full install→evaluate→converge cycle against a real sandbox. The `e2e_tests_exist` F_D evaluator checks at least one exists.

Pure unit tests are supplementary — acceptable for write-primitive invariants (emit, project, EventStream) but not sufficient for workflow features.

### coverage_complete F_P evaluator (REQ-F-TEST-002)

The `coverage_complete` F_P assessment checks that the test suite covers all REQ keys with integration or e2e scenarios. Assessment is against REQ key traceability (`# Validates: REQ-*` tags), not line coverage metrics. Pure unit tests mocking internals do not satisfy coverage.

### F_H gates at spec/design boundaries (REQ-F-GATE-001)

F_H evaluators are defined on edges in `sdlc_graph.py` via the `human_gate` operator. At bind time, the engine projects the event stream for `approved{kind: fh_review}` events using Event Calculus fluent semantics (`holdsAt(operative(edge, wv), now)`). The F_D→F_P→F_H ordering invariant prevents reviewing candidates with deterministic failures.

### PYTHONPATH sandboxing (REQ-F-TEST-003)

All F_D evaluator commands use `PYTHONPATH=builds/python/src/:.genesis` so tests import from the build source tree. Covered by ADR-006.

## Tech Stack

- pytest with markers (`e2e`, `not e2e`)
- F_D evaluators run as subprocesses with pinned PYTHONPATH
- F_D evaluator acyclicity: test commands never invoke genesis subcommands

## Consequences

- `pytest -m 'not e2e'` for the fast F_D loop; `pytest -m e2e` for sandbox acceptance
- Every test file must carry `# Validates: REQ-*` tags (enforced by `check_test_op`)
- No mocking of genesis internals in integration tests — real imports, real event streams
