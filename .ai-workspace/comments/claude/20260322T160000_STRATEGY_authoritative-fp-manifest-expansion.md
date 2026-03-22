# STRATEGY: Authoritative F_P Manifest — Structured JSON Expansion

**Author**: claude
**Date**: 2026-03-22T16:00:00+11:00
**Addresses**: F_P dispatch contract debt, prompt-coupled manifest, CLAUDE.md transport dependence
**For**: codex, ABG engine maintainers
**Supersedes**: `claude/20260322T150000_REVIEW_bind-fp-lossy-projection.md` (historical bug review — pre-fix state)

## Current State (post-fix)

Commit `0d5de8f` removed the worst debt from `_assemble_prompt()`:
- Hardcoded `[INVARIANTS]` with ABG-specific rules — removed
- 4000-char context truncation — removed
- Source markov `[PRECONDITIONS]` — added
- Domain-blind `[CONTEXT]` projection of edge.context[] — added

The prompt is now a faithful projection of GTL types. But the **dispatch contract is still prompt-coupled**. The manifest JSON at `fp_manifest_path` (`commands.py:365`) contains:

```json
{
  "manifest_id": "mf-...",
  "edge": "design→module_decomp",
  "failing_evaluators": [{"name": "...", "description": "..."}],
  "prompt": "... (the entire prompt as a string) ...",
  "result_path": ".ai-workspace/fp_results/...",
  "spec_hash": "..."
}
```

A conforming F_P transport that reads only this JSON gets: a prompt string, a result path, and a spec hash. All structure is flattened into prose. The transport must parse the prompt to recover what the engine already computed.

## Problem

1. **Prompt is the primary artifact** — the JSON wraps it rather than the prompt being a render of the JSON. Inversion of authority.
2. **Transport dependence** — Claude Code works because CLAUDE.md supplies additional context. An API dispatch, Codex dispatch, or any non-Claude-Code transport gets only the prompt string. Not constitutionally trustworthy.
3. **Missing typed fields** — `PrecomputedManifest` already carries `job`, `current_asset`, `failing_evaluators`, `passing_evaluators`, `fd_results`, `relevant_contexts`, `delta_summary`. None of these reach the manifest JSON as structured data.
4. **Missing model fields** — `intent_surface` (feature ID, REQ keys, satisfies chain) and `work_surface` (write paths, read paths, platform) do not exist on GTL types yet.

## Correct GTL iterate signature (for reference)

```python
# gtl/core.py:337
iterate(job: Job, evaluator_fn: Callable[[Asset], bool], asset: Asset) -> (Asset, WorkingSurface)
```

The engine's `bind_fd → bind_fp → gen_iterate` chain is the implementation of this protocol. The manifest JSON is the serialized dispatch contract for the F_P invocation within that chain.

## Plan

### Phase 1: Expand manifest JSON from PrecomputedManifest (immediate)

Source: `builds/claude_code/code/genesis/commands.py` — manifest dict at line 365.

Expand the manifest JSON to carry structured fields that `PrecomputedManifest` already computes:

```json
{
  "manifest_id": "mf-...",
  "edge": "design→module_decomp",
  "source_asset": "design",
  "target_asset": "module_decomp",
  "source_markov": {"design": ["adrs_recorded", "tech_stack_decided"]},
  "target_markov": ["modules_identified", "boundaries_clear"],
  "failing_evaluators": [
    {"name": "decomp_coherent", "category": "F_P", "description": "..."}
  ],
  "fd_results": {
    "module_coverage": {"passes": false, "detail": "..."}
  },
  "delta": 2,
  "delta_summary": "2 evaluators failing: decomp_coherent (F_P), boundary_check (F_D)",
  "contexts": [
    {
      "name": "gtl_bootloader",
      "locator": "workspace://.genesis/gtl_spec/GTL_BOOTLOADER.md",
      "content": "... (full text, no truncation) ..."
    }
  ],
  "current_asset": {"status": "in_progress", "edges_converged": ["intent→requirements"]},
  "prompt": "... (human-readable render of the above — convenience, not authority) ...",
  "result_path": ".ai-workspace/fp_results/...",
  "spec_hash": "..."
}
```

Changes required:
- `commands.py`: expand the manifest dict to include structured fields from `selected_pre` and `selected_job`
- `bind.py`: `_assemble_prompt()` becomes a render function over the same data (already effectively is — just making the relationship explicit)
- Tests: assert manifest JSON contains structured fields, not just prompt text

Data sources (all already computed, no new computation needed):
| Field | Source |
|-------|--------|
| `source_asset` | `job.edge.source.name` |
| `target_asset` | `job.edge.target.name` |
| `source_markov` | `job.edge.source.markov` |
| `target_markov` | `job.edge.target.markov` |
| `fd_results` | `pre.fd_results` |
| `delta` | `pre.delta` |
| `delta_summary` | `pre.delta_summary` |
| `contexts` | `pre.relevant_contexts` (with locator from `job.edge.context[]`) |
| `current_asset` | `pre.current_asset` |

### Phase 2: Add intent_surface and work_surface to GTL types

These fields do not exist on GTL types yet. They require model extensions.

**intent_surface** — the feature ID and REQ keys driving this edge traversal:
```json
{
  "feature_id": "REQ-F-AUTH-001",
  "satisfies": ["REQ-F-AUTH-001", "REQ-F-AUTH-002"],
  "lineage": ["intent", "requirements", "feature_decomp", "design"]
}
```

Source: feature vector `satisfies:` field + graph topology. Requires threading feature ID through `gen_iterate → bind_fd → PrecomputedManifest`.

**work_surface** — where the F_P actor should write artifacts:
```json
{
  "target_asset_type": "module_decomp",
  "write_paths": [".ai-workspace/modules/"],
  "read_paths": ["builds/python/design/adrs/", "specification/"],
  "platform": "python"
}
```

Source: `WorkingSurface` type already exists in `gtl/core.py` but is not yet populated by GSDLC or threaded into the manifest. Requires domain package to declare work surface per asset type.

### Phase 3: Transport conformance

All F_P transports must prove they can execute from the manifest JSON alone:
- Claude Code (MCP dispatch via gen-start skill)
- API dispatch (direct Claude API call)
- Codex dispatch (OpenAI Codex)

CLAUDE.md may be a convenience layer but must not be required for correct execution. Test: run F_P dispatch with CLAUDE.md absent and verify the manifest carries sufficient context.

## What this does NOT change

- `_assemble_prompt()` structure (already fixed — domain-blind, full context)
- `bind_fd` computation (already correct)
- GSDLC edge configuration (already correct — methodology via Context[])
- Event stream invariants
- Result file / emit-event pipeline

## Delivery order

Phase 1 is immediate — all data already computed, just needs serialization into the manifest JSON. Phase 2 requires GTL type extensions and GSDLC configuration. Phase 3 requires transport implementations beyond Claude Code.
