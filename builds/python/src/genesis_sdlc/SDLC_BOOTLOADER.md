# SDLC Bootloader: AI SDLC Instantiation of the GTL Formal System

**Version**: 1.1.1
**Requires**: GTL Bootloader (universal axioms)

---

## SDLC Graph

```
intent → requirements → feature_decomp → design → module_decomp → code ↔ unit_tests
                                                                        │
                                                                        ↓
                                                 uat_tests ← user_guide ← integration_tests
```

Spec/design boundary at `feature_decomp → design`. Upstream = WHAT (tech-agnostic). Downstream = HOW (tech-bound).

## Feature Vectors

A feature is a trajectory through the graph. REQ keys thread from spec to runtime:

```
Spec: REQ-F-AUTH-001 → Design: Implements: REQ-F-AUTH-001 → Code: # Implements: → Tests: # Validates:
```

Feature vectors have `satisfies:` listing covered REQ keys — the coverage projection mechanism.

## Completeness Visibility

Computable at any point without LLM:
- **Coverage**: every REQ-* in at least one feature's `satisfies:` field
- **Convergence visibility**: iteration summary (after each iterate), edge convergence (delta=0), feature completion (all edges converged)

A convergence event not made visible before downstream proceeds is a spec violation.

## Profiles

| Profile | When | Graph |
|---------|------|-------|
| **standard** | Normal feature work | Core edges + decomposition |
| **poc** | Proof of concept | Core edges, decomp collapsed |
| **hotfix** | Emergency fix | Direct → code ↔ tests |
| **minimal** | Trivial change | Single edge |

## Agent Write Territory (hard constraint)

| Territory | Who writes | Rule |
|-----------|-----------|------|
| `events/events.jsonl` | All agents via `emit_event()` only | **Never write directly.** Append-only. |
| `features/active/*.yml` | Owning agent | Update only your feature. |
| `comments/claude/` | Claude Code only | Never write to other agents' directories. |
| `comments/codex/` | Codex only | Same exclusivity. |
| `reviews/pending/` | All agents | Proposals; human gate resolves. |
| `reviews/proxy-log/` | Proxy actor only | Written before each `review_approved`. |

Post naming: `YYYYMMDDTHHMMSS_CATEGORY_SUBJECT.md`. Categories: `REVIEW`, `STRATEGY`, `GAP`, `SCHEMA`, `HANDOFF`, `MATRIX`. Immutable once written — supersede with new file.

## Operating Standards

Load from `.gsdlc/release/operating-standards/` before: writing posts (`CONVENTIONS_GUIDE.md`), backlog items (`BACKLOG_GUIDE.md`), human-facing docs (`WRITING_GUIDE.md`), user guides (`USER_GUIDE_GUIDE.md`), releases (`RELEASE_GUIDE.md`).

## Human Proxy Mode

- `--human-proxy` requires `--auto`. Explicit flag only, never persisted.
- Proxy writes proxy-log before emitting `review_approved{actor: "human-proxy"}`.
- Rejection halts auto-loop immediately. No retry in same session.
- `/gen-status` surfaces proxy decisions for morning review.

## Bug Triage

Fix directly. Emit `bug_fixed` event with `root_cause: coding_error|design_flaw|unknown`. No feature vector, no iterate cycle, no human gate required. Post-mortem determines escalation.
