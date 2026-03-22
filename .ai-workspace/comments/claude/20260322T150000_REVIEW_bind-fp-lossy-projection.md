# REVIEW: bind_fp is a lossy projection — F_P actors get a degraded view of the GTL graph

**Author**: claude
**Date**: 2026-03-22
**For**: ABG engine maintainers (claude_code + codex builds)

## Problem

`_assemble_prompt()` in `genesis/bind.py` is the function that projects GTL types into an F_P-executable prompt. It is the implementation of `iterate()` for agent work. It is currently lossy and hardcoded where it should be a faithful projection of the graph.

### What GSDLC puts on each edge (correct)

```python
Edge(
    source=design,          # markov: [adrs_recorded, tech_stack_decided, ...]
    target=module_decomp,   # markov: [modules_identified, boundaries_clear, ...]
    context=[gtl_bootloader, sdlc_bootloader, this_spec, design_adrs],
    using=[claude_agent, check_boundaries_op],
)
```

### What bind_fd computes (correct)

`PrecomputedManifest` contains: full resolved contexts, all F_D results, failing evaluators, current asset state. Everything is available. Nothing is lost at this stage.

### What bind_fp passes to the F_P actor (broken)

| GTL concept | What happens | Problem |
|---|---|---|
| Methodology (Context[]) | Replaced by 6 hardcoded INVARIANTS lines | ABG-specific: "Exactly 6 modules" leaks into every project using the engine |
| Context documents | Truncated to 4000 chars each | GTL bootloader is ~17KB — actor gets ~25%. Design ADRs truncated. |
| Source asset markov | Not included | F_P doesn't know what's guaranteed from upstream |
| Target asset markov | Included in OUTPUT CONTRACT | Already correct |
| Feature / REQ keys | Not included | F_P doesn't know the intent chain or which requirements drive this edge |
| Work surface | Not specified | F_P doesn't know where to write artifacts (derived from asset type + platform) |

### The `[INVARIANTS]` section is the primary defect

```python
sections.append(
    "[INVARIANTS]\n"
    "- Assets are projections of the event stream — never mutate state directly.\n"
    "- emit() is the only write path. event_time is system-assigned.\n"
    "- Implement only V1 features. No V2 (spawn, consensus, release, multi-tenant).\n"
    "- All code files must carry: # Implements: REQ-* tags.\n"
    "- All test files must carry: # Validates: REQ-* tags.\n"
    "- Exactly 6 modules: core, bind, schedule, manifest, commands, __main__."
)
```

Lines 1-2 are universal GTL axioms (§V). Lines 3-6 are ABG-specific rules that should not exist in the engine. Any project using genesis_sdlc gets told to implement "exactly 6 modules" — nonsensical for a web app, a data pipeline, or any non-ABG project.

The methodology IS the Context[] documents. The bootloader IS the invariants. Hardcoding them bypasses the entire Context mechanism and makes the engine project-specific rather than domain-blind.

### The 4000-char truncation breaks the constraint surface

```python
snippet = content[:4000] + ("…[truncated]" if len(content) > 4000 else "")
```

The GTL bootloader (17KB), SDLC bootloader (11KB), and design ADRs are all truncated to 4000 chars. The F_P actor receives fragments of the constraint surface that was carefully declared on the edge by GSDLC. The entire point of Context[] on the edge is to define what the actor sees — truncating it defeats the purpose.

Note: for the Claude Code MCP transport, the full bootloader reaches the actor via CLAUDE.md (loaded automatically). This is why the system works at all. But this is transport-dependent — an API call, Codex dispatch, or any non-Claude-Code transport would get only the truncated manifest.

## Architectural analysis

The function signature is adequate:

```
iterate(Asset<Tn>, Context[], Evaluators) → Event+
```

GSDLC correctly parameterizes each edge. The engine correctly computes everything in `bind_fd`. The types carry everything. The failure is exclusively in `_assemble_prompt()` — a bottleneck that throws away what every other layer correctly provides.

The fix is entirely in ABG's engine source: `builds/claude_code/code/genesis/bind.py`, function `_assemble_prompt()`.

## Fix

### 1. Remove hardcoded INVARIANTS

The methodology comes from Context[] (the bootloader documents declared on the edge). The engine must not inject project-specific rules. Replace the hardcoded section with a header that introduces the context documents.

### 2. Remove 4000-char truncation

Pass full context documents. The constraint surface declared by GSDLC on each edge should reach the F_P actor without loss. Context budget management (if needed) is a transport concern, not an engine concern.

### 3. Add source.markov as preconditions

The F_P actor should know what's guaranteed from upstream (source asset stability conditions) alongside what's required (target asset markov conditions, already present in OUTPUT CONTRACT).

### 4. Feature / intent chain (future)

The feature ID and REQ keys are not currently available in PrecomputedManifest. Adding them requires threading the feature ID through `gen_iterate → bind_fd → PrecomputedManifest`. This is a larger change — tracked separately.

## Prompt structure after fix

```
[PRECONDITIONS]     — source.markov: what's guaranteed from upstream
[CURRENT STATE]     — edge, status, converged edges
[GAP]               — failing evaluators with F_D detail (unchanged)
[CONTEXT]           — full Context[] documents, no truncation
[OUTPUT CONTRACT]   — target.markov + assessment path (unchanged)
```

No `[INVARIANTS]` section. The Context[] documents ARE the invariants.
