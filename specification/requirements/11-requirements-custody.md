# Requirements Custody Requirements

**Family**: REQ-F-CUSTODY-*
**Status**: Still needed
**Category**: Governance

Requirements custody requirements define how project-specific REQ authority is discovered and carried into the runtime package surface.

### REQ-F-CUSTODY-001 — instantiate() accepts project-specific requirements

`instantiate(slug)` currently hardcodes gsdlc's own REQ keys into every project. This means F_D evaluates coverage against the wrong requirements for all non-gsdlc projects. The Package must accept project-specific requirements.

**Acceptance Criteria**:
- AC-1: `instantiate(slug, requirements=None)` accepts an optional `requirements` list
- AC-2: When `requirements` is provided, `Package.requirements` is set to that list — not gsdlc's hardcoded keys
- AC-3: When `requirements` is `None`, `Package.requirements` is an empty list — not gsdlc's keys. No requirement surface = zero project requirements.
- AC-4: gsdlc's own 33 REQ keys remain the default only when gsdlc is building itself (slug == "genesis_sdlc" or no override)

### REQ-F-CUSTODY-002 — Layer 3 wrapper loads project requirements from specification/requirements/

The generated wrapper must read the project's own requirement surface and pass it to `instantiate()`.

**Acceptance Criteria**:
- AC-1: Generated wrapper includes a `_load_reqs()` function that discovers REQ headers from files under `specification/requirements/`
- AC-2: Wrapper calls `instantiate(slug="{slug}", requirements=_load_reqs())`
- AC-3: `_load_reqs()` returns an empty list if the folder does not exist — never falls back to gsdlc's keys
- AC-4: Parsing is deterministic: regex match on `### (REQ-[A-Z0-9-]+)` at start of line across the requirement files

### REQ-F-CUSTODY-003 — Installer scaffolds specification/requirements/

New projects need a starter requirement surface so the custody chain has something to read.

**Acceptance Criteria**:
- AC-1: `install()` creates `specification/requirements/` if absent
- AC-2: The scaffold contains a header and at least one example REQ key or starter family file as a template
- AC-3: Existing requirement files are never overwritten
- AC-4: The scaffold is created before wrapper generation so the chain is complete on first install
