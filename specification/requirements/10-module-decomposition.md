# Module Decomposition Requirements

**Family**: REQ-F-MDECOMP-*
**Status**: Still needed
**Category**: Capability

Module decomposition requirements define the structural bridge between design and code construction.

### REQ-F-MDECOMP-001 — design→module_decomp edge

**Acceptance Criteria**:
- AC-1: `design→module_decomp` edge exists in the Package with F_D, F_P, and F_H evaluators
- AC-2: F_P evaluator (`module_schedule`) decomposes design ADRs into modules
- AC-3: Output: one `.yml` per module in `.ai-workspace/modules/` with fields: `id`, `name`, `description`, `implements_features`, `dependencies`, `rank`, `interfaces`, `source_files`

### REQ-F-MDECOMP-002 — Module dependency DAG is acyclic with defined build order

**Acceptance Criteria**:
- AC-1: Module `dependencies` fields form an acyclic directed graph
- AC-2: `rank` field defines build order: rank=1 modules have no dependencies (leaves), higher ranks depend on lower
- AC-3: Build order is leaf-to-root — each module is built against stable interfaces from already-built dependencies

### REQ-F-MDECOMP-003 — module_coverage F_D evaluator

**Acceptance Criteria**:
- AC-1: F_D evaluator `module_coverage` checks every feature vector stem appears in at least one module YAML
- AC-2: Exit 0 if all features assigned; exit 1 with uncovered list
- AC-3: Pure F_D check — no LLM invocation

### REQ-F-MDECOMP-004 — F_H gate: module schedule approved before code

**Acceptance Criteria**:
- AC-1: F_H evaluator `schedule_approved` gates the `design→module_decomp` edge
- AC-2: Human confirms: module boundaries are clean, dependency DAG is acyclic, build order is sensible, every feature is assigned
- AC-3: No code is written until the module schedule is approved

### REQ-F-MDECOMP-005 — module_decomp→code replaces design→code

**Acceptance Criteria**:
- AC-1: The Package has no direct `design→code` edge
- AC-2: Code construction proceeds from `module_decomp→code` — the module schedule is the input constraint for code, not design directly
- AC-3: `module_decomp→code` evaluators include `impl_tags` (F_D) and `code_complete` (F_P)
