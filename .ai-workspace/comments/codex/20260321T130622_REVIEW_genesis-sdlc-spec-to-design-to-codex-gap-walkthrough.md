# REVIEW: genesis_sdlc Spec -> Design -> Codex Gap Walkthrough

## Scope

This review walks the current `genesis_sdlc` constitutional surfaces into the new Codex build and records where the chain still breaks:

- `specification/INTENT.md`
- `specification/requirements.md`
- `specification/feature_decomposition.md`
- `specification/standards/BACKLOG.md`
- `specification/standards/RELEASE.md`
- `builds/python/design/adrs/ADR-008-four-territory-model-and-bootstrap-boundary.md`
- `builds/python/design/adrs/ADR-009-engine-commands.md`
- `builds/python/design/adrs/ADR-011-backlog-schema-and-commands.md`
- `builds/codex/code/genesis_sdlc/*`
- `builds/codex/design/adrs/ADR-001-codex-build.md`
- abiogenesis Codex runtime used by this build:
  - `/Users/jim/src/apps/abiogenesis/builds/codex/code/genesis/core.py`
  - `/Users/jim/src/apps/abiogenesis/builds/codex/code/genesis/commands.py`

The question is not whether `builds/codex` works mechanically. It does. The question is whether the current spec and design surfaces are sufficient to derive it cleanly and ratify it as a first-class self-hosting path.

## Findings

### 1. Critical: the constitutional registry is still Python/Claude-specific, so Codex is not yet derivable from the ratified surfaces

The current constitutional documents still treat the Python/Claude realization as the authoritative source:

- `specification/requirements.md` is explicitly derived from `builds/python/src/genesis_sdlc/sdlc_graph.py`
- `specification/feature_decomposition.md` names `builds/python/src/genesis_sdlc/sdlc_graph.py` as the REQ key registry and maps the implementation only to `install.py`, `sdlc_graph.py`, and `__init__.py` in the Python build
- `specification/INTENT.md` still scopes V1 to a single worker, explicitly `claude_code`
- `ADR-005`, `ADR-006`, `ADR-008`, and the release standard all continue to treat `builds/python` as the constitutional authoring surface

The Codex build exists in `builds/codex`, but the spec/design chain still describes a world in which the Python build is the source of truth and Codex does not exist. That makes `gsdlc.codex` an implementation that is mechanically valid but still extra-constitutional.

This is the main gap if the goal is an independent Codex evolution loop.

### 2. Critical: the private `builds/codex/.workspace` territory is not yet an executable boundary

The Codex build intentionally reintroduced a private tenant-local workspace:

- `builds/codex/code/genesis_sdlc/install.py` creates `builds/codex/.workspace/manifests`, `iterations`, and `working_surfaces`
- `builds/codex/code/genesis_sdlc/SDLC_BOOTLOADER.md` documents the split between shared `.ai-workspace/` and private `builds/<tenant>/.workspace/`
- `builds/codex/design/adrs/ADR-001-codex-build.md` ratifies that split for the Codex build

But the runtime that `gsdlc.codex` actually installs still comes from the abiogenesis Codex seed, and that runtime continues to use only shared workspace paths:

- `/Users/jim/src/apps/abiogenesis/builds/codex/code/genesis/core.py` bootstraps `.ai-workspace/events`, `.ai-workspace/features/*`, `.ai-workspace/fp_manifests`, `.ai-workspace/fp_results`, `.ai-workspace/reviews/proxy-log`
- `/Users/jim/src/apps/abiogenesis/builds/codex/code/genesis/commands.py` writes F_P manifests and results to `.ai-workspace/fp_manifests` and `.ai-workspace/fp_results`

So the private territory now exists in installer/bootloader prose, but the live runtime still routes its most important execution traces through shared `.ai-workspace`.

This is not just missing polish. It means the restored isolation boundary is not yet real.

### 3. High: the backlog contract is split three ways, and the current code follows the standard, not the ratified requirements/ADR

There are now three incompatible backlog definitions:

Requirements + ADR:

- `specification/requirements.md` defines backlog fields `description`, `priority`, `signal_source` and statuses `draft | ready | promoted | deferred`
- `ADR-011-backlog-schema-and-commands.md` repeats that schema and also says backlog is surfaced through `gen-gaps`, `gen-status`, and engine commands `gen backlog list` / `gen backlog promote`

Standard + current code:

- `specification/standards/BACKLOG.md` defines statuses `idea | incubating | ready | promoted | abandoned`
- `builds/codex/code/genesis_sdlc/backlog.py` implements exactly that standard, not the requirement/ADR schema
- the Codex backlog CLI is `python -m genesis_sdlc.backlog ...`, not `gen backlog ...`
- neither the abiogenesis Codex engine nor the `genesis_sdlc` Codex build surfaces ready backlog counts through `gen-gaps` or `gen-status`

So the backlog path is currently:

- constitution says one thing
- design ADR says the same thing
- operating standard says something else
- code follows the operating standard

This is a clear spec/design/code split, not an implementation edge case.

### 4. High: release and governance are still Python-only, so Codex has no ratified release path

`specification/standards/RELEASE.md` is fully Python-bound:

- all version bump locations point at `builds/python/...`
- all test invocations point at `builds/python/src` and `builds/python/tests`
- the changelog location is `builds/python/CHANGELOG.md`
- bootloader/version checks name the Python installer paths directly

`specification/feature_decomposition.md` also still maps the implementation only to the Python modules.

That means `gsdlc.codex` now has a working implementation and a test suite, but it does not yet have a ratified release procedure, versioning checklist, or governance surface. Until that exists, Codex can evolve technically but not methodologically.

### 5. Medium: the Codex installer now seeds `specification/`, but that behavior is not yet justified by the constitutional documents

`builds/codex/code/genesis_sdlc/install.py` creates starter files for:

- `specification/INTENT.md`
- `specification/requirements.md`
- `specification/feature_decomposition.md`

That is a pragmatic bootstrap choice, but the current requirements and ADRs do not say the installer is allowed to author normative specification documents. The constitutional model currently says `specification/` is the read-only human-authored surface.

This may still be the right choice. But if kept, it needs to be explicitly ratified. Otherwise the installer is now doing more than the spec/design chain authorizes.

## Walkthrough

### Intent layer

The intent still describes a single-worker `claude_code` V1 package. That was coherent for the Python build. It is not coherent for a repo that now contains a standalone Codex tenant build intended to enter its own bootstrap loop.

### Requirements layer

The requirements still bind the package registry, test pathing, and loadability checks to `builds/python`. The backlog and workspace requirements are also stale relative to both the standards and the Codex build.

### Design layer

The accepted ADR set still ratifies:

- four territories only
- shared `.ai-workspace` as the sole runtime write surface
- Python build surfaces as the constitutional source
- backlog integration through engine commands that do not exist in the current Codex path

The new Codex ADR correctly records what the Codex build is doing, but it has not yet been propagated back into the older accepted design chain.

### Code layer

The Codex code successfully stands up:

- a standalone installer
- a standalone graph package
- a Codex backlog module
- a private `builds/codex/.workspace`
- a passing Codex test suite

So the implementation is no longer the blocker. The blocker is that the constitutional and design surfaces still largely describe the Python/Claude world, while the runtime substrate used by Codex still has shared-workspace assumptions that undercut the new private-workspace model.

## What Is Already Solid

The core graph and installer structure translated cleanly:

- the SDLC graph topology ports cleanly into `builds/codex/code/genesis_sdlc/sdlc_graph.py`
- the three-layer workflow release model also ports cleanly
- the Codex installer can bootstrap a project from the abiogenesis Codex seed without using the Claude build path
- the new Codex test suite passes

So this is not a failed port. It is a successful port that exposed the remaining constitutional gaps.

## Recommended Ratification Order

1. Decide whether `builds/codex` is now a first-class constitutional build target or still a bootstrap-only exception.
2. Resolve the workspace model:
   - either ratify shared `.ai-workspace` only and drop private `.workspace`
   - or ratify private tenant-local `.workspace` and update the runtime to actually use it
3. Resolve backlog in favor of one contract:
   - requirements/ADR
   - or `standards/BACKLOG.md`
   - but not both
4. Write a Codex release/governance path parallel to the Python one.
5. Decide whether installer-authored starter `specification/*.md` files are legitimate methodology behavior.

## Bottom Line

`gsdlc.codex` is mechanically real now, but constitutionally incomplete.

The main gap is no longer code. It is that the spec/design chain still describes the Python/Claude path, while the Codex build has already forced three unresolved questions into the open:

- Is Codex constitutional or bootstrap-exception?
- Is runtime state shared-only or shared + private-per-tenant?
- Is backlog governed by requirements/ADR or by the operating standard?

Those are the next ratification points if the Codex path is meant to become a true self-hosting evolution loop.
