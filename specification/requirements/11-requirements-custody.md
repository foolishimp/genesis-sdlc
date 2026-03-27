# Requirements Custody Requirements

**Family**: REQ-F-CUSTODY-*
**Status**: Active
**Category**: Governance

Requirements custody requirements define how project-specific REQ authority is discovered and carried into the runtime package surface.

### REQ-F-CUSTODY-001 — instantiate() accepts project-specific requirements

The Package accepts a project-specific requirement list and carries that list into runtime evaluation.

**Acceptance Criteria**:
- AC-1: `instantiate(slug, requirements=None)` accepts an optional `requirements` list
- AC-2: When `requirements` is provided, `Package.requirements` is set to that list
- AC-3: When `requirements` is `None`, `Package.requirements` is an empty list. No requirement surface = zero project requirements.
- AC-4: A caller that needs a project-local requirement set supplies it explicitly

### REQ-F-CUSTODY-002 — Layer 3 wrapper loads project requirements from specification/requirements/

The generated wrapper must read the project's own requirement surface and pass it to `instantiate()`.

**Acceptance Criteria**:
- AC-1: Generated wrapper includes a `_load_reqs()` function that discovers REQ headers from `specification/requirements/*.md`, excluding non-family files such as `README.md`
- AC-2: Wrapper calls `instantiate(slug="{slug}", requirements=_load_reqs())`
- AC-3: `_load_reqs()` returns an empty list if the folder does not exist
- AC-4: Parsing is deterministic: files are read in lexicographic path order and REQ headers are matched with regex `### (REQ-[A-Z0-9-]+)` at start of line

### REQ-F-CUSTODY-003 — Installer scaffolds specification/requirements/

New projects need a starter requirement surface so the custody chain has something to read.

**Acceptance Criteria**:
- AC-1: `install()` creates `specification/requirements/` if absent
- AC-2: The scaffold contains a header and at least one example REQ key or starter family file as a template
- AC-3: Existing requirement files are never overwritten
- AC-4: The scaffold is created before wrapper generation so the chain is complete on first install
