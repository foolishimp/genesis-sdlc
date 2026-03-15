# ADR-003: Traceability Enforcement

**Status**: Accepted
**Implements**: REQ-F-TAG-001, REQ-F-TAG-002, REQ-F-COV-001

## Decision

Traceability is enforced by F_D evaluators that run deterministic checks:

1. **`impl_tags`** at `design→code`: `gen check-tags --type implements --path src/`
   - Every `.py` file under `src/` (except `__init__.py`) must carry `# Implements: REQ-*`
   - Exit 0 = all tagged. Exit 1 = untagged files listed.

2. **`validates_tags`** at `code↔unit_tests`: `gen check-tags --type validates --path tests/`
   - Every `.py` test file (except `__init__.py`) must carry `# Validates: REQ-*`

3. **`req_coverage`** at `requirements→feature_decomp`: `gen check-req-coverage --package spec.packages.genesis_sdlc:package --features .ai-workspace/features/`
   - Every REQ key in `Package.requirements` must appear in a feature vector's `satisfies:` field

## Rationale

- Traceability breaks if it relies on discipline; deterministic checks make it structural
- The `gen check-*` commands are already implemented in abiogenesis — no new code needed
- REQ key coverage is checkable at any time without LLM — `gen check-req-coverage` is pure grep

## Consequences

- Every new source file added to `src/` must be tagged before `design→code` converges
- Every new test file added to `tests/` must be tagged before `code↔unit_tests` converges
- New requirements added to `Package.requirements` must be covered by a feature vector before `requirements→feature_decomp` converges
