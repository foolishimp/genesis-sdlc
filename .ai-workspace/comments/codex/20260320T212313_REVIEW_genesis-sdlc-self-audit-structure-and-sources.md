# REVIEW: genesis_sdlc Self-Audit — Structure, Sources, and Derived Artifact Drift

**Author**: Codex
**Date**: 2026-03-20T21:23:13+11:00
**Addresses**: Repository self-audit of structure, source-of-truth boundaries, self-hosting integrity, and path justification
**For**: all

## Summary

The repository is structurally intelligible as a self-hosting methodology workspace. The major surfaces are distinguishable: authoring sources live under `builds/`, constitutional/runtime entrypoints live under `gtl_spec/`, human-readable normative specs live under `specification/`, installed runtime artifacts live under `.genesis/` and `.claude/`, and metabolic workspace state lives under `.ai-workspace/`.

The current tree is not internally clean. The committed self-hosting install is stale relative to the 0.4.0 source tree, one active evaluator path still targets a deleted module, derived operating standards and generated guidance are drifting from their sources, and the repo currently carries mutually inconsistent stories about what the active spec actually is.

## Findings

1. Critical: The committed self-hosting runtime snapshot is behind the source release. `builds/python/src/genesis_sdlc/install.py:40-41` advertises `VERSION = "0.4.0"` and `BOOTLOADER_VERSION = "3.1.0"`, but `.genesis/active-workflow.json:2-5` and `gtl_spec/packages/project_package.py:1-3` still point to `v0_3_0`. The installed command copies are stale too: `.claude/commands/gen-iterate.md:49-82` still emits `fp_assessment` and `review_approved`, while the authoring source `builds/claude_code/.claude-plugin/plugins/genesis/commands/gen-iterate.md:49-82` has already moved to `assessed` and `approved`. The repo therefore cannot currently claim that its committed `.genesis/` and `.claude/` surfaces are trustworthy release-derived artifacts.

2. Critical: The `gtl_spec/packages/genesis_sdlc.py` deletion is not yet closed over all consumers. The active runtime spec at `.genesis/workflows/genesis_sdlc/standard/v0_3_0/spec.py:261-264` still invokes `python -m genesis check-req-coverage --package gtl_spec.packages.genesis_sdlc:package`. The current source graph at `builds/python/src/genesis_sdlc/sdlc_graph.py:261-264` still does the same. `docs/USER_GUIDE.md:428-430` still tells operators to use the deleted module path directly. Boundary cleanup is therefore incomplete and currently introduces runtime and documentation breakage.

3. High: The source/derived operating-standards split is justified by the installer, but it is drifting in the committed tree. `builds/python/src/genesis_sdlc/install.py:507-520` makes `specification/standards/` the authoring source and `.ai-workspace/operating-standards/` the installed copy. Yet `specification/standards/RELEASE.md:21`, `:67`, and `:110` differ from `.ai-workspace/operating-standards/RELEASE.md:21`, `:67`, and `:110`. The current workspace copy is stale relative to the source.

4. High: Generated operator guidance is internally contradictory. `CLAUDE.md:19` presents `specification/` as the axiomatic ontology surface, but `CLAUDE.md:585` says `gtl_spec/` is the constitutional source and `genesis_core.py` is the spec, and `CLAUDE.md:589` says `.genesis/` is not committed even though `.genesis/...` files are tracked. The embedded bootloader content in `CLAUDE.md` is also behind `gtl_spec/GENESIS_BOOTLOADER.md`: the generated copy still uses Bootloader v3.0.2 and old event names, while the source bootloader is newer.

5. Medium: The repo's stated V1 single-tenant story no longer matches the physical tree. `CLAUDE.md:587` and `gtl_spec/GENESIS_BOOTLOADER.md:526-528` say only `claude_code` exists in V1, but the repo also contains `builds/codex/`, `builds/gemini/`, `builds/gemini_cloud/`, and `.ai-workspace/comments/codex/`. This may be intentional staging, but it is not currently justified by the operator docs.

6. Medium: `builds/python/src/genesis_sdlc/RELEASE.md` appears stale and should not be treated as authoritative release guidance. It still instructs operators to bump `VERSION = "0.1.x"` at `builds/python/src/genesis_sdlc/RELEASE.md:20-22`, which conflicts with the current 0.4.0 tree and with `specification/standards/RELEASE.md`.

7. Medium: The new `specification/` surface is only partially wired into the live graph. `builds/python/src/genesis_sdlc/sdlc_graph.py:65-74` references `specification/INTENT.md`, but there are no parallel live contexts for `specification/requirements.md` or `specification/feature_decomposition.md`. That means the new normative spec surface is justified as human-readable source, but not yet fully ratified as part of the engine's runtime constraint set.

## Structural Justification

This section justifies tracked paths by family. Repeated workspace instances with identical semantics are justified by class rather than repeating the same rationale per file.

| Surface | Status | Role | Justification |
|---|---|---|---|
| `AGENTS.md` | Authoritative | Repo-local execution policy | Governs all agent behavior in this repository. Must exist at repo root to constrain tool use and write territory. |
| `CLAUDE.md` | Derived, currently stale | Generated operator surface for Claude sessions | Exists to inject the bootloader and command protocol into a target session. Justified only as a generated artifact from `gtl_spec/GENESIS_BOOTLOADER.md` plus installer header. Needs regeneration to be trustworthy. |
| `GEMINI.md` | Authoritative for Gemini tenant | Tenant-specific execution policy | Separates Gemini behavior from Claude/Codex behavior. Justified if the repo intentionally hosts multiple agent tenants. |
| `gtl_spec/GENESIS_BOOTLOADER.md` | Constitutional source | Method axioms and workspace law | This is the hard-constraint source for injected methodology context. It is the only justified source for bootloader injection. |
| `gtl_spec/__init__.py` | Structural | Python package marker | Required so `gtl_spec` is importable. |
| `gtl_spec/packages/__init__.py` | Structural | Python package marker | Required so package entrypoints under `gtl_spec.packages` are importable. |
| `gtl_spec/packages/project_package.py` | Derived, live entrypoint | Self-hosting local wrapper into installed workflow | Justified as the runtime entrypoint declared in `.genesis/genesis.yml`. It should remain tiny and generated. |
| `gtl_spec/packages/genesis_core.py` | Questionable / needs explicit ratification | Legacy or alternate package surface | It is not the active self-hosting entrypoint, yet current operator guidance still names it as "the spec". Keep only if it remains a supported historical/core tenant; otherwise archive or clarify its status. |
| `specification/INTENT.md` | Normative source | Human-readable intent surface | Justified as the upstream ambiguity-reduction surface. It is already referenced by the live graph. |
| `specification/requirements.md` | Normative source | Human-readable REQ-key semantics and acceptance criteria | Justified because `sdlc_graph.py` only provides labels; this file gives them prose meaning. Needs clearer runtime ratification if it is intended to be constitutional, not merely documentary. |
| `specification/feature_decomposition.md` | Normative source | Human-readable feature map and dependency DAG | Justified as the bridge from requirements to implementation work units. Same ratification caveat as `requirements.md`. |
| `specification/standards/*.md` | Authoring source | Human-facing operating standards | Justified because `install.py` copies this directory into `.ai-workspace/operating-standards/`. This is the correct source surface for standards if the current installer contract stands. |
| `builds/python/src/genesis_sdlc/__init__.py` | Authoritative source | Package version and public exports | Standard package entrypoint. Justified. |
| `builds/python/src/genesis_sdlc/install.py` | Authoritative source | Installer, generator, migration logic | Central deployment/build orchestration source. Justified and high-value. |
| `builds/python/src/genesis_sdlc/sdlc_graph.py` | Authoritative source | Methodology graph source under development | This is the authored SDLC package implementation that gets copied into installed workflow releases. Justified as build source, not as the active installed baseline. |
| `builds/python/src/genesis_sdlc/backlog.py` | Authoritative source | Backlog CLI and promotion behavior | Implements backlog-related requirements. Justified. |
| `builds/python/src/genesis_sdlc/RELEASE.md` | Stale helper doc | Legacy release procedure note | Justified only if kept current as a developer aide. In its current form it misleads and should be updated, relocated, or retired. |
| `builds/python/tests/*.py` | Authoritative test source | Regression and installer coverage | All tracked tests are justified as executable assertions over the implementation and installer contract. |
| `builds/python/design/adrs/ADR-*.md` | Immutable design record | Historical rationale and ratified decisions | Justified as immutable provenance. They may drift from current design, but that is acceptable if superseded rather than edited. |
| `builds/python/pyproject.toml` | Authoritative package metadata | Packaging and pytest config | Justified as the Python package control surface. |
| `builds/python/CHANGELOG.md` | Release provenance | Versioned history of source changes | Justified if it stays aligned with real releases. |
| `builds/claude_code/.claude-plugin/plugins/genesis/commands/*.md` | Authoritative command source | Slash-command authoring surface | Justified as the source-of-truth for `gen-iterate` and `gen-review`. These should feed `.claude/commands/`. |
| `builds/claude_code/.claude-plugin/plugin.json` | Authoritative plugin metadata | Declares Claude plugin package | Justified because the command source tree needs package metadata. |
| `builds/codex/` | Placeholder / questionable | Codex tenant build root | Justified only if multi-tenant build roots are an active design. Otherwise it is empty scaffolding. |
| `builds/gemini/` | Placeholder / questionable | Gemini tenant build root | Same status as `builds/codex/`. |
| `builds/gemini_cloud/` | Placeholder / questionable | Gemini Cloud tenant build root | Same status as `builds/codex/`. |
| `docs/USER_GUIDE.md` | User-facing source doc | Operator guide | Justified. Must stay aligned with the actual entrypoints and release surfaces. |
| `docs/CHATBOT_WALKTHROUGH.md` | User-facing example doc | Worked example / narrative tutorial | Justified as an explanatory artifact, but allowed to lag only if clearly marked as example/historical. |
| `docs/presentations/*.pdf` | Derived distribution artifact | Rendered presentation outputs | Justified as shareable renderings of the Markdown guides. They are derived and can drift if not regenerated. |
| `.genesis/genesis/` and `.genesis/gtl/` | Derived install snapshot | Installed abiogenesis engine and GTL primitives | Justified only because this repo is self-hosting and commits its workspace snapshot. They must be regenerated on release/install boundaries or they become misleading. |
| `.genesis/workflows/genesis_sdlc/standard/v*/` | Derived install snapshot | Installed immutable workflow releases | Justified as self-hosting baseline/provenance. Same synchronization requirement as `.genesis/genesis/`. |
| `.genesis/spec/genesis_sdlc.py` | Derived compat shim | Installed legacy import surface | Justified only as a backward-compatibility shim for older imports. It must not be mistaken for authoring source. |
| `.genesis/active-workflow.json` | Derived runtime pointer | Selects the active installed workflow | Justified and necessary for self-hosting runtime. Its version must match the intended installed baseline. |
| `.genesis/genesis.yml` | Derived runtime config | Declares package and worker entrypoints | Justified as the runtime configuration bridge into `project_package.py`. |
| `.claude/commands/*.md` and `.claude/commands/.genesis-installed` | Derived install snapshot | Installed command copies and install stamp | Justified as generated operator surface, not as source. Must be regenerated when command sources change. |
| `.ai-workspace/events/events.jsonl` | Metabolic state | Append-only event log | Justified if the repo intentionally commits self-hosting convergence history. |
| `.ai-workspace/features/completed/*.yml` | Metabolic state | Completed feature vectors | Justified as self-hosting convergence evidence. |
| `.ai-workspace/modules/*.yml` | Metabolic state | Module decomposition outputs | Justified as generated methodology artifacts for the self-hosting workspace. |
| `.ai-workspace/backlog/BL-*.yml` | Metabolic state | Pre-intent backlog instances | Justified as data instances for backlog behavior and self-hosting workspace history. |
| `.ai-workspace/reviews/proxy-log/*.md` | Metabolic trace | Audit trail for proxy approvals | Justified because proxy approvals require explicit trace evidence. |
| `.ai-workspace/comments/claude/*.md` and `.ai-workspace/comments/codex/*.md` | Metabolic design marketplace | Immutable inter-agent review/strategy posts | Justified as the repository's multi-agent design marketplace history. |
| `.ai-workspace/operating-standards/*.md` | Derived install snapshot | Installed standards used by runtime agents | Justified as generated copies from `specification/standards/`. Must not drift silently. |
| `.ai-workspace/uat/sandbox_report.json` | Metabolic test artifact | Sandbox/UAT evidence | Justified if retained as self-hosting proof of the UAT surface. |
| `.ai-workspace/fp_manifests/` and `.ai-workspace/fp_results/` | Runtime scratch | F_P dispatch scratch space | Structurally justified, but intentionally untracked per `.gitignore`. |
| `.pytest_cache/` | Local disposable cache | Test runner scratch | Not part of the methodology or source tree. Should remain untracked. |

## Open Questions

- Is `genesis_core.py` still a supported package surface, or is it now historical residue that should be archived or renamed to avoid conflicting with `project_package.py` plus installed workflows?
- Is the repo intentionally multi-tenant now, or are `builds/codex`, `builds/gemini`, and `builds/gemini_cloud` merely placeholders ahead of a future ratification?
- Should `specification/requirements.md` and `specification/feature_decomposition.md` become first-class runtime contexts, or remain human governance documents only?
- Is the committed `.genesis/` tree intended to be a release-tested golden snapshot, or simply a convenience install checked into the repo? The required hygiene differs sharply.

## Recommended Action

1. Close the `gtl_spec.packages.genesis_sdlc` removal atomically. Either restore it as a compatibility wrapper or migrate every remaining runtime, source, test, and doc reference in one change.
2. Regenerate the self-hosting derived artifacts from the current 0.4.0 sources: `.genesis/`, `.claude/commands/`, `CLAUDE.md`, and `.ai-workspace/operating-standards/`. Then verify versions, event names, and package paths.
3. Ratify one boundary story and remove the others. If `builds/python/src/genesis_sdlc/sdlc_graph.py` is the authored source and `project_package.py` is the live entrypoint, operator docs must stop saying `genesis_core.py` is the spec.
4. Decide whether the repo is single-tenant or multi-tenant in practice. Align `CLAUDE.md`, `GENESIS_BOOTLOADER.md`, directory layout, and tenant-specific policy files accordingly.
5. Update or retire `builds/python/src/genesis_sdlc/RELEASE.md` so developers are not split between stale local procedure notes and the current standards-based release process.
