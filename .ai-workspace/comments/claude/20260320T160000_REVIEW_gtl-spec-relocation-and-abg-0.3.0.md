# REVIEW: gtl_spec relocation under .genesis/ and abiogenesis 0.3.0

**Date**: 2026-03-20
**Scope**: abiogenesis 0.3.0 + genesis_sdlc 0.4.0 installer alignment
**ADR**: ADR-008 (four-territory model and bootstrap boundary enforcement)

---

## What changed

`gtl_spec/` moved from the project root into `.genesis/gtl_spec/` for **all** projects, not just genesis_sdlc self-hosting. This completes the four-territory boundary model.

### Territory ownership

```
abg owns:     .genesis/genesis/              engine
              .genesis/gtl/                  type system
              .genesis/gtl_spec/             spec package (genesis_core, bootloader, starter wrapper)
              .genesis/genesis.yml           config (package: gtl_spec.packages.{slug}:package)

gsdlc layers: .genesis/workflows/            versioned release (Layer 2)
              .genesis/spec/                 immutable shim
              .genesis/active-workflow.json
              .claude/commands/              slash commands
              CLAUDE.md                      bootloader embedded
              .ai-workspace/operating-standards/
```

`PYTHONPATH=.genesis` resolves both `gtl` and `gtl_spec` imports from one search path.

### Dependency chain for downstream projects

```
python -m genesis_sdlc.install --target /new/project
  -> gsdlc calls ../abiogenesis/builds/claude_code/code/gen-install.py (live sibling)
  -> abg creates .genesis/{genesis/, gtl/, gtl_spec/} + builds/ scaffold
  -> gsdlc layers on: workflows, commands, CLAUDE.md, operating-standards
  -> gsdlc overwrites the gtl_spec starter wrapper with genesis_sdlc-generated version
```

Downstream projects get the latest abg automatically via the sibling-directory reference. No separate abg install step needed.

### Files modified

**abiogenesis (committed as v0.3.0)**:
- `gen-install.py` — spec files, starter package, __init__.py all write to `.genesis/gtl_spec/` instead of root `gtl_spec/`
- `pyproject.toml` — version bump 0.2.1 -> 0.3.0
- `test_cli_config.py` — test assertions updated, PYTHONPATH includes `workspace/.genesis`

**genesis_sdlc**:
- `install.py` — `install_sdlc_starter_spec()`, `migrate_full_copy()`, `_verify()`, `_audit()` all target `.genesis/gtl_spec/`; CLAUDE.md template shows four-territory structure; bootloader search prefers `.genesis/gtl_spec/` with legacy fallback
- `sdlc_graph.py` — locators: `workspace://.genesis/gtl_spec/...`
- `test_installer.py`, `test_e2e_sandbox.py` — all path assertions updated
- `ADR-008` — "next release" section replaced with "completed" checklist
- `USER_GUIDE.md`, `CHATBOT_WALKTHROUGH.md`, `RELEASE.md`, `feature_decomposition.md` — all `gtl_spec/` references updated

### Validation

- genesis_sdlc: 145 tests pass, 2 skipped, 0 failures
- abiogenesis: 310 tests pass, 1 pre-existing failure (unrelated F_H convergence)
- Cascade install: clean
- Audit: 20/20 components ok, 0 drifted

### Why this matters

Before this change, `gtl_spec/` at the project root was editable, driftable, and confused with build source (the GCC bootstrap boundary violation documented in the GAP post). Now the entire installed compiler lives under `.genesis/` — write-once territory owned by the installer. Project overrides go in `.ai-workspace/`. The boundary is enforced by `--audit`.
