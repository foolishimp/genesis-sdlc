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

The deployed runtime path must not include `builds/`.

**Acceptance Criteria**:
- AC-1: `genesis.yml` pythonpath contains `.gsdlc/release`, not `builds/python/src`
- AC-2: `PYTHONPATH=.genesis python -m genesis gaps --workspace .` resolves Package from `.gsdlc/release/gtl_spec/packages/{slug}.py`
- AC-3: No import in the runtime chain requires `builds/` on sys.path
- AC-4: Evaluator commands MAY reference `builds/` — they test source, not deploy it
