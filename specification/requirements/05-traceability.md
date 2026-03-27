# Traceability Requirements

**Family**: REQ-F-TAG-*, REQ-F-COV-*
**Status**: Active
**Category**: Verification

Traceability requirements define the deterministic surfaces that prove implementation and tests remain grounded in REQ authority.

### REQ-F-TAG-001 — Implements: tags enforced on all source files

Every source file must trace to at least one REQ key.

**Acceptance Criteria**:
- AC-1: `check-tags --type implements --path <src/>` scans for `# Implements: REQ-*` comments
- AC-2: Exit 0 if every `.py` file (excluding `__init__.py`) has at least one tag; exit 1 otherwise
- AC-3: Output lists files with their tag status

### REQ-F-TAG-002 — Validates: tags enforced on all test files

Every test file must trace to at least one REQ key.

**Acceptance Criteria**:
- AC-1: `check-tags --type validates --path <tests/>` scans for `# Validates: REQ-*` comments
- AC-2: Exit 0 if every test file has at least one tag; exit 1 otherwise

### REQ-F-COV-001 — REQ key coverage enforced by check-req-coverage

Every REQ key in the Package must appear in at least one feature vector.

**Acceptance Criteria**:
- AC-1: `check-req-coverage --package <pkg:var> --features <dir/>` loads Package.requirements and scans YAML `satisfies:` lists
- AC-2: Exit 0 if every REQ key appears in at least one feature vector; exit 1 with gap list otherwise
- AC-3: Coverage computable without LLM invocation — pure F_D check
