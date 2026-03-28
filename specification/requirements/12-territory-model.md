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

### REQ-F-TERRITORY-003 — Default install excludes authoring territory from the target root

The product install boundary excludes authoring-source territory. If a release needs design, tests, or related methodology artifacts at runtime, they are staged under `.gsdlc/release/`, not copied into the target as source working trees.

**Acceptance Criteria**:
- AC-1: Default install does not create `build_tenants/` in the target root
- AC-2: Default install does not create copied source design or source test trees in the target root
- AC-3: Release snapshots required by runtime or audit live under `.gsdlc/release/`
- AC-4: Default install does not create `specification/standards/` in the target root
- AC-5: Any source-snapshot or self-hosting install mode is explicit and non-default
