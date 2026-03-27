# Bootloader Asset Requirements

**Family**: REQ-F-BOOTDOC-*
**Status**: Active
**Category**: Verification

Bootloader asset requirements define how the SDLC bootloader becomes a convergence-tracked graph artifact rather than a hand-maintained side document.

### REQ-F-BOOTDOC-001 — bootloader is a compiled graph asset with F_D currency validation

The bootloader is a derived document — a compiled constraint surface synthesised from specification, standards, and design. It is a graph asset with its own edge, evaluators, and convergence lifecycle. It is not a primary source. It may be released as a standalone artifact and/or embedded into supported agent control surfaces, but those carrier files are design choices rather than requirement truth.

**Acceptance Criteria**:
- AC-1: `bootloader` is an asset in the Package with ID format `BOOT-{SEQ}` and lineage `[requirements, design]`
- AC-2: Markov conditions: `spec_hash_current`, `version_current`, `section_coverage_complete`, `references_valid`
- AC-3: Edge E8 `[requirements, design, integration_tests]→bootloader` — creative input from requirements and design, evidence gate from integration_tests
- AC-4: Operative: `OPERATIVE_ON_APPROVED` — bootloader is not usable until human-approved

### REQ-F-BOOTDOC-002 — F_D evaluators validate bootloader currency without LLM

Four deterministic evaluators catch staleness. All computable without LLM invocation.

**Acceptance Criteria**:
- AC-1: `spec_hash_current` — hash of `Package.requirements` matches hash embedded in bootloader header
- AC-2: `version_current` — bootloader version matches `active-workflow.json` version
- AC-3: `section_coverage_complete` — all mandatory sections present in the bootloader
- AC-4: `references_valid` — every `workspace://` path in the bootloader points to an existing file

### REQ-F-BOOTDOC-003 — F_P regenerates bootloader from source documents

The bootloader is synthesised from three authored planes, not hand-maintained. F_P regenerates all content; F_D validates the structure. Control-surface carrier files consume this compiled artifact; they do not replace it as a source of truth.

**Acceptance Criteria**:
- AC-1: F_P evaluator `synthesize_bootloader` regenerates the bootloader from specification, standards, and design documents
- AC-2: Fixed section structure — sections are invariant, content within each section is synthesised
- AC-3: Size budget: ~150-200 lines (10:1 compression from source documents)
- AC-4: Each section carries `workspace://` references for depth — the bootloader orients, source documents provide detail

### REQ-F-BOOTDOC-004 — Bootloader is a leaf node with no downstream dependents

The bootloader is methodology observability, not product acceptance. Nothing depends on it.

**Acceptance Criteria**:
- AC-1: No edge in the Package has `bootloader` as a source
- AC-2: `uat_tests` does not depend on `bootloader` — product acceptance is separate from methodology health
- AC-3: Bootloader convergence is tracked by `gen-gaps` but does not block downstream edges
