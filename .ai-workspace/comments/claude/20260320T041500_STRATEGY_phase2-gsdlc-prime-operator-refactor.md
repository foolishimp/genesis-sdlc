# STRATEGY: Phase 2 — genesis_sdlc Prime Operator Refactor

**Author**: Claude Code
**Date**: 2026-03-20T04:15:00Z
**Supersedes**: Phase 2 section of `20260320T020432_STRATEGY_prime-operator-refactor-plan.md`
**Prerequisite**: Phase 1 complete — abiogenesis v0.2.0 released and cascaded
**For**: human review before execution

---

## Principle

**Spec leads, code follows.** Update normative surfaces first (bootloader, spec, commands, standards), then implementation (installer, tests), then docs. Verify with tests. Commit.

---

## Scope

Rename old event names to EC prime operators across all genesis_sdlc owned files:

| Old | New | Notes |
|-----|-----|-------|
| `fp_assessment` | `assessed{kind: fp}` | Carries `spec_hash`, `evaluator`, `result` |
| `review_approved` | `approved{kind: fh_review}` | Carries `actor`, `edge` |
| `review_rejected` | `assessed{kind: fh_review, result: reject}` | Carries `actor`, `reason` |
| `fd_gap_found` | `found{kind: fd_gap}` | `happensAt` only — audit record |

No new event types added to genesis_sdlc (engine already has `revoked`). No backward-compat branches.

---

## What We Learned from Phase 1 (abiogenesis)

1. **Spec leads, code follows** — update normative surfaces first, verify code matches
2. **"Unknown" fallback is design, not compat** — `workflow_version == "unknown"` is the unversioned fallback for workspaces without `active-workflow.json`, not backward compatibility
3. **Migration logic legitimately references old names** — `_migrate_provenance()` transforms old events to new schema. That's its job. Don't blindly rename inside it — understand what it does
4. **Comments/features/completed/ are historical** — don't rewrite history in workspace artifacts. Only update normative and source files
5. **Bootloader version must bump** — any change to GENESIS_BOOTLOADER.md requires BOOTLOADER_VERSION bump and at least MINOR version for genesis_sdlc

---

## File Inventory (by execution order)

### Step 1 — Normative surfaces (spec leads)

| # | File | Changes | Old refs |
|---|------|---------|----------|
| 1 | `gtl_spec/GENESIS_BOOTLOADER.md` | §XIX proxy protocol: `review_approved` → `approved{kind: fh_review}` (3 refs). §XX bug triage: no changes needed. Bump `**Version**:` line. | 3 |
| 2 | `standards/RELEASE.md` | `fp_assessment` → `assessed{kind: fp}` (2 refs). Source copy — installed to operating-standards/ | 2 |
| 3 | `.ai-workspace/operating-standards/RELEASE.md` | Same changes as #2 (installed copy) | 2 |

### Step 2 — Skill commands (the LLM instruction surface)

| # | File | Changes | Old refs |
|---|------|---------|----------|
| 4 | `.claude/commands/gen-start.md` | `fp_assessment` → `assessed` with kind/spec_hash (2). `review_approved` → `approved` with kind (3). `review_rejected` → `assessed{kind: fh_review, result: reject}` (1). | 6 |
| 5 | `.claude/commands/gen-iterate.md` | Same pattern as gen-start.md | 6 |
| 6 | `.claude/commands/gen-review.md` | `review_approved` → `approved` (2). `review_rejected` → `assessed{kind: fh_review, result: reject}` (2). | 4 |
| 7 | `builds/claude_code/.claude-plugin/plugins/genesis/commands/gen-iterate.md` | Mirror of #5 (abiogenesis-owned source) | 6 |
| 8 | `builds/claude_code/.claude-plugin/plugins/genesis/commands/gen-review.md` | Mirror of #6 | 4 |

### Step 3 — Implementation source

| # | File | Changes | Old refs |
|---|------|---------|----------|
| 9 | `builds/python/src/genesis_sdlc/install.py` | **Migration function** (`_migrate_provenance`): old event names are the MIGRATION SURFACE — they must stay as string literals in the scan/collect logic (lines 595-610) because they describe what the function is looking for in old logs. The RE-EMIT logic (lines 708-715) must emit NEW event types. Docstring (line 566-567): update description. Backward-compat shim (line 307): evaluate. | 5 source refs + migration surface |

### Step 4 — Tests

| # | File | Changes | Old refs |
|---|------|---------|----------|
| 10 | `builds/python/tests/test_e2e_sandbox.py` | All `review_approved` assertions → `approved`. All `fp_assessment` assertions → `assessed`. ~10 refs. | ~10 |

### Step 5 — Documentation

| # | File | Changes | Old refs |
|---|------|---------|----------|
| 11 | `docs/USER_GUIDE.md` | Full pass: `review_approved` → `approved{kind: fh_review}` (~11 refs), `fd_gap_found` → `found{kind: fd_gap}` (2 refs). Rewrite manual approval CLI example. | ~13 |
| 12 | `docs/CHATBOT_WALKTHROUGH.md` | `review_approved` → `approved{kind: fh_review}` (3 refs). CLI examples. | 3 |
| 13 | `builds/python/design/adrs/ADR-005-three-layer-install-architecture.md` | `fp_assessment` → `assessed{kind: fp}` (1 ref) | 1 |
| 14 | `CLAUDE.md` | `review_approved` → `approved{kind: fh_review}` (3 refs in §XIX proxy protocol). Will be overwritten by installer on next cascade — but fix source for consistency. | 3 |

### Step 6 — GTL specs (verify only)

| # | File | Changes | Old refs |
|---|------|---------|----------|
| 15 | `gtl_spec/packages/genesis_sdlc.py` | **Verify** — spec already abstracts from event names. No changes expected. | 0 |
| 16 | `gtl_spec/packages/genesis_core.py` | **Verify** `intent_approved` evaluator name — this is an evaluator name, not an event type. No change needed unless it causes confusion. | 0 |

### NOT touched

| Category | Rationale |
|----------|-----------|
| `.ai-workspace/comments/` | Historical design marketplace posts — immutable records |
| `.ai-workspace/features/completed/` | Historical feature vectors — immutable records |
| `.ai-workspace/backlog/` | Historical backlog items |
| `builds/python/CHANGELOG.md` | Historical release notes |
| `.ai-workspace/events/events.jsonl` | Runtime state — archival is Phase 4 |
| `.ai-workspace/fp_manifests/`, `.ai-workspace/fp_results/` | Runtime artifacts |

---

## install.py Migration Logic — Detail

The `_migrate_provenance()` function (lines 564-733) is the trickiest part. It does:

1. **Scans** old event stream for `fp_assessment` and `review_approved` events (by old name)
2. **Collects** them with their timestamps
3. **Re-emits** them with enhanced schema (spec_hash, workflow_version, actor: "migration")

After the refactor:
- The **scan** logic KEEPS old event type strings — it's looking for events written before the rename
- The **re-emit** logic CHANGES to emit `assessed{kind: fp}` and `approved{kind: fh_review}` with appropriate payloads
- The docstring updates to describe what the function actually transforms

This is NOT a simple find-replace. The function's job is to bridge old → new, so it must know both names.

---

## Version Bump

| File | Current | New | Rationale |
|------|---------|-----|-----------|
| `builds/python/src/genesis_sdlc/install.py` VERSION | `0.3.0` | `0.4.0` | Breaking: event schema change, bootloader bump |
| `builds/python/src/genesis_sdlc/install.py` BOOTLOADER_VERSION | `3.0.2` | `3.1.0` | New invariant (spec authority) + EC event names in §XIX |
| `builds/python/src/genesis_sdlc/__init__.py` | `0.3.0` | `0.4.0` | |
| `builds/python/pyproject.toml` | `0.3.0` | `0.4.0` | |
| `builds/python/tests/test_sdlc_graph.py` | `0.3.0` | `0.4.0` | Version assertion |
| `builds/python/tests/test_installer.py` | `0.3.0` | `0.4.0` | Version assertion |
| `gtl_spec/GENESIS_BOOTLOADER.md` Version | `3.0.2` | `3.1.0` | |

---

## Execution Sequence

```
1. Snapshot commit (recovery point)
2. Bootloader: update §XIX event names, bump version         [Step 1]
3. Standards: RELEASE.md fp_assessment refs                   [Step 1]
4. Commands: gen-start, gen-iterate, gen-review               [Step 2]
5. install.py: migration re-emit logic, docstrings            [Step 3]
6. Tests: update assertions, run suite, confirm green         [Step 4]
7. Docs: USER_GUIDE, CHATBOT_WALKTHROUGH, ADR-005, CLAUDE.md [Step 5]
8. Version bump: all 7 files                                  [release]
9. CHANGELOG entry                                            [release]
10. Run tests, confirm green                                  [release]
11. Commit, tag v0.4.0                                        [release]
12. Cascade install to self + dependents                      [Phase 3]
```

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| install.py migration logic breaks on blind rename | Detailed analysis above — scan keeps old names, re-emit uses new names |
| CLAUDE.md drift from bootloader | CLAUDE.md is overwritten by installer — fix source, cascade will deploy |
| Missed reference | Grep sweep before test run (156 refs inventoried above) |
| Test suite red after rename | Run tests after Step 4, before docs. Fix before proceeding. |
| Bootloader version not bumped | Explicit in version bump table — BOOTLOADER_VERSION in install.py must match |

---

## Decision Gate

Phase 2 touches ~14 source files with ~60 actionable references (excluding historical/immutable artifacts). The install.py migration function is the only non-trivial change — everything else is string replacement with schema updates.

Confirm before executing.
