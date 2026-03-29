# Territory Model Requirements

**Family**: REQ-F-TERRITORY-*
**Status**: Active
**Category**: Constraint / Guarantee

Territory model requirements define the install boundary between ABG kernel surfaces and gsdlc methodology surfaces.

### REQ-F-TERRITORY-001 — gsdlc installer writes release artifacts to .gsdlc/release/

The gsdlc installer must produce its own territory separate from the ABG kernel.

**Acceptance Criteria**:
- AC-1: Workflow releases written to `.gsdlc/release/workflows/genesis_sdlc/standard/v{VERSION}/`
- AC-2: Generated wrapper written to `.gsdlc/release/gtl_spec/packages/{slug}.py`
- AC-3: Active workflow pointer written to `.gsdlc/release/active-workflow.json`
- AC-4: `.genesis/` contains only ABG engine (`genesis/`) and GTL type system (`gtl/`) after install
- AC-5: No gsdlc workflow, wrapper, or config artifacts are written to `.genesis/`

### REQ-F-TERRITORY-002 — Runtime resolves from installed territories, not build source

The deployed runtime path must not include authoring-source roots.

**Acceptance Criteria**:
- AC-1: `genesis.yml` pythonpath contains `.gsdlc/release`, not a build-tenant source root
- AC-2: `PYTHONPATH=.genesis python -m genesis gaps --workspace .` resolves Package from `.gsdlc/release/gtl_spec/packages/{slug}.py`
- AC-3: No import in the runtime chain requires authoring-source roots on sys.path
- AC-4: Evaluator commands MAY reference build-tenant source roots — they test source, not deploy it

### REQ-F-TERRITORY-003 — Default install excludes copied framework authoring territory from the target root

The product install boundary excludes copied framework authoring-source territory. If a release needs design, tests, or related methodology artifacts at runtime, they are staged under `.gsdlc/release/`, not copied into the target as source working trees. Project-owned roots such as `build_tenants/` and `docs/` remain lawful parts of the installed target structure.

**Acceptance Criteria**:
- AC-1: Default install does not copy the framework's own `build_tenants/` working tree into the target root
- AC-2: Default install does not create copied source design or source test trees in the target root
- AC-3: Release snapshots required by runtime or audit live under `.gsdlc/release/`
- AC-4: Default install does not create `specification/standards/` in the target root
- AC-5: Any framework source-snapshot or self-hosting install mode is explicit and non-default
- AC-6: Project-owned roots such as `build_tenants/` and `docs/` may be scaffolded in the target root without being treated as copied framework authoring territory
- AC-7: In an explicit self-host install mode, project-owned methodology authoring surfaces such as `specification/standards/` may remain in the target root without being classified as default-install drift
- AC-8: Audit interprets forbidden-vs-allowed authoring territory according to the explicit install mode recorded in the active workflow declaration

### REQ-F-TERRITORY-004 — Runtime control state lives under .ai-workspace/runtime/

The mutable runtime control plane is a separate territory from both install-managed release surfaces and project-truth specification surfaces.

**Acceptance Criteria**:
- AC-1: Resolved runtime state, backend availability state, doctor state, and session-local overrides live under `.ai-workspace/runtime/`
- AC-2: `.ai-workspace/runtime/` is not treated as install-managed release territory
- AC-3: `.ai-workspace/runtime/` is not treated as project customization territory
- AC-4: Rebuilding runtime state after reset or re-resolution does not require mutating `.gsdlc/release/active-workflow.json`
