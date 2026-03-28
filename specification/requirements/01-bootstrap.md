# Bootstrap Requirements

**Family**: REQ-F-BOOT-*
**Status**: Active
**Category**: Governance

Bootstrap requirements govern how genesis_sdlc installs and validates its methodology surface and agent-facing bootstrap/control surfaces in a target project.

### REQ-F-BOOT-001 — gen-install bootstraps target project with engine + methodology

The installer copies the genesis engine and methodology into a target project so it can run without an installed package. It establishes the installed runtime surface: `.genesis/` (ABG kernel, immutable), `.gsdlc/release/` (gsdlc methodology release, immutable between reinstalls), `.ai-workspace/` (runtime evidence), and project-local `specification/` (constitutional source for the target project).

**Acceptance Criteria**:
- AC-1: `install(target, source)` creates `.genesis/genesis/` with engine modules copied from the abiogenesis engine
- AC-2: Creates `.genesis/genesis.yml` pointing to `gtl_spec.packages.<slug>:package` and `gtl_spec.packages.<slug>:worker` with `pythonpath: [.gsdlc/release]`
- AC-3: Creates `.ai-workspace/` directory structure (events/, features/active/, features/completed/, comments/, reviews/)
- AC-4: Installs operating standards from `specification/standards/` into `.gsdlc/release/operating-standards/`
- AC-5: Installs command files from plugin sources into `.claude/commands/`
- AC-6: Installs or updates the supported agent bootstrap/control surfaces defined by the active design
- AC-7: Delivered bootstrap/control surfaces carry bare operating axioms and route the agent to the canonical released process documents
- AC-8: Idempotent — re-running updates engine files and standards, preserves workspace state and local specs
- AC-9: Emits `genesis_sdlc_installed` event on completion with version, spec_hash, and install outcome

### REQ-F-BOOT-002 — .genesis/genesis.yml config resolves Package/Worker

The engine reads its Package and Worker from a config file at startup.

**Acceptance Criteria**:
- AC-1: `genesis.yml` contains `package:` and `worker:` fields as Python import paths (`module:var`)
- AC-2: Missing `genesis.yml` produces an informative error, not a crash
- AC-3: Engine resolves Package and Worker via `importlib` from the configured path

### REQ-F-BOOT-003 — Installer copies released spec into .gsdlc/release/spec/ as immutable layer

The install architecture separates immutable methodology spec from mutable project spec, with gsdlc artifacts in `.gsdlc/release/` (not `.genesis/`).

**Acceptance Criteria**:
- AC-1: `install()` copies the realized workflow package and supporting release assets into `.gsdlc/release/` as the frozen methodology layer
- AC-2: The installed spec is versioned: `.gsdlc/release/workflows/genesis_sdlc/standard/v{VERSION}/` contains the release snapshot
- AC-3: The frozen spec is never modified after install — it represents the methodology version that was installed

### REQ-F-BOOT-004 — Installer generates wrapper in .gsdlc/release/gtl_spec/packages/{slug}.py

Projects get a generated wrapper that imports from the installed methodology release. The wrapper is system-owned and rewritten on every redeploy.

**Acceptance Criteria**:
- AC-1: Installer generates `.gsdlc/release/gtl_spec/packages/{slug}.py` importing from the versioned workflow release
- AC-2: If the file carries the `genesis_sdlc-generated` marker, it is replaced on reinstall
- AC-3: If the file has been customised (no marker), installer does not overwrite — use `--migrate-full-copy` to opt in

### REQ-F-BOOT-005 — Reinstall replaces .gsdlc/release/ methodology atomically; never overwrites customised specs

Upgrade safety: the methodology layer is replaceable, project customisations are sacred.

**Acceptance Criteria**:
- AC-1: `install()` replaces `.gsdlc/release/spec/` and `.gsdlc/release/workflows/` atomically on reinstall
- AC-2: System-owned wrappers (with marker) are replaced; customised specs are never overwritten
- AC-3: On reinstall, provenance reconciliation emits events under the current schema and workflow version

### REQ-F-BOOT-006 — --audit validates installed artifacts match the release

The installer can verify that a deployment is consistent with the version it claims to be. This is the GCC bootstrap boundary validator.

**Acceptance Criteria**:
- AC-1: `install(target, audit_only=True)` returns structured JSON with per-component findings (ok, drifted, missing, error)
- AC-2: Checks content hashes of workflow release, commands, operating standards, bootstrap/control-surface artifacts, and immutable spec shim against build source
- AC-3: Checks version consistency across active-workflow.json, manifest.json, and commands stamp
- AC-4: Verifies genesis.yml package/worker references resolve via import (not just exist as files)
- AC-5: Verifies Layer 3 wrapper content matches expected template for the installed version
- AC-6: Returns `status: "ok"` only when all checks pass; `status: "drift_detected"` otherwise

### REQ-F-BOOT-007 — The installed command carrier is a composed surface

The installed `.claude/commands/` directory is a derived composition of engine-owned and domain-owned command carriers.

**Acceptance Criteria**:
- AC-1: The installed command carrier includes the engine-owned commands `gen-start`, `gen-gaps`, and `gen-status`
- AC-2: The installed command carrier includes the gsdlc-owned commands `gen-iterate` and `gen-review`
- AC-3: The command carrier is written to `.claude/commands/` as a managed surface on install or reinstall
- AC-4: Installer writes a command stamp describing the installed command set and version
- AC-5: Reinstall removes stale `gen-*.md` command files that are no longer part of the active command set

### REQ-F-BOOT-008 — The installed workflow exposes a narrow customization surface

The installed release does not invite arbitrary edits to managed artifacts. It exposes a small declared customization surface.

**Acceptance Criteria**:
- AC-1: The installed active workflow declaration identifies the project requirement surface as the primary customization boundary
- AC-2: The installed active workflow declaration exposes the selected F_P transport agent as a narrow runtime customization setting
- AC-3: The installed active workflow declaration lists the managed install surfaces that should not be edited directly
- AC-4: The customization surface is machine-readable and shipped with the installed release

### REQ-F-BOOT-009 — Runtime reset clears execution state without destroying the installed release

Resetting workflow state is a supported operator action. It clears runtime evidence and transient execution state while preserving the installed methodology and project truth.

**Acceptance Criteria**:
- AC-1: A runtime reset operation clears execution-state surfaces under `.ai-workspace/`
- AC-2: Runtime reset preserves `.genesis/`, `.gsdlc/release/`, `.claude/commands/`, and project-local `specification/`
- AC-3: Runtime reset returns structured JSON describing what was cleared and what was preserved
- AC-4: Reinstall remains the managed reset path for system-owned install surfaces
