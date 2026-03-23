> **Resolved**: MCP hangs documented here were resolved by ADR-022 (subprocess + env sanitization, 2026-03-23). MCP is no longer used for F_P dispatch.

# Test Suite Hang: Root Cause Analysis

**Date**: 2026-03-23T04:45:42Z
**Author**: Claude Code
**Category**: MATRIX (testcase/timing/root cause)
**Supersedes**: None
**Related**: 20260323T005300_REVIEW_gsdlc-install-deconstruction.md

---

## Executive Summary

The test suite hung indefinitely during routine runs, causing 41+ minutes of elapsed wall-clock time with no result. Root cause: **live F_P qualification tests invoke MCP subprocess calls that block indefinitely**, and the `tests_pass` F_D evaluator had no exclusion for these tests. A secondary issue was the 120s F_D timeout being too short for the integration test suite (61 sandbox installs, ~180s total).

---

## Test Files and Counts

| File | Tests | Marker | Runtime | Category |
|------|-------|--------|---------|----------|
| `test_backlog.py` | 16 | (none) | ~1s | Fast deterministic |
| `test_gaps.py` | 4 | (none) | ~1s | Fast deterministic |
| `test_installer.py` | 49 | (none) | ~3s | Fast deterministic |
| `test_sdlc_graph.py` | 53 | (none) | ~1s | Fast deterministic |
| `test_integration_graph_walk.py` | 61 | `integration` | ~180s | Sandbox installs |
| `test_live_fp_qualification.py` | 18 | `live_fp` | unbounded | MCP + LLM calls |
| `test_e2e_sandbox.py` | ~46 | `e2e` | ~80s | Full orchestration |
| **Total** | **247** | | | |

---

## Timeline of Failure

### Phase 1: Initial test run (`-m 'not e2e'`)

Collection order (alphabetical): backlog(16) -> gaps(4) -> installer(49) -> integration(61) -> **live_fp(18)** -> sdlc_graph(53)

**131 tests passed** before hang. This is exactly:
- 16 + 4 + 49 + 61 = **130** (all fast + integration tests)
- Test 131 = **first live_fp test**

### Phase 2: live_fp tests block

The live_fp test module executes `_has_mcp_transport()` at **import time** (line 89-92 of `test_live_fp_qualification.py`):

```python
skip_no_mcp = pytest.mark.skipif(
    not _has_mcp_transport(),
    reason="...",
)
```

`_has_mcp_transport()` runs `npx @steipete/claude-code-mcp --help` with a 15s timeout. On this machine, the MCP package IS available, so `_has_mcp_transport()` returns True. Tests are NOT skipped.

Each live_fp test then calls `invoke_live_fp()` which:
1. Runs `genesis iterate` to produce an F_P manifest
2. Calls `_call_claude_code_mcp()` which starts the MCP server via async stdio JSON-RPC
3. The MCP server call blocks on `os.waitpid()` in the asyncio event loop

**Stack trace at hang point:**
```
File ".../asyncio/unix_events.py", line 1411, in _do_waitpid
    pid, status = os.waitpid(expected_pid, 0)
```

No child process exists (verified via `pgrep -P <pid>`), so `os.waitpid` blocks forever. The asyncio event loop thread is stuck, and pytest cannot interrupt it without `--timeout`.

### Phase 3: F_D evaluator timeout

Even after the live_fp issue was identified, the `tests_pass` F_D evaluator continued timing out at 120s. The evaluator command was:
```
python -m pytest builds/python/tests/ -q --tb=short -m 'not e2e'
```

This included 61 integration tests (each installing a fresh sandbox). Total runtime: ~269s. The F_D timeout is 120s.

---

## Root Causes

### RC-1: live_fp tests collected in default run (HANG)

**What**: `test_live_fp_qualification.py` tests have `pytestmark = pytest.mark.live_fp` but no default exclusion. `-m 'not e2e'` does not exclude `live_fp`.

**Why it blocks**: MCP subprocess calls use asyncio with `os.waitpid()` that blocks when the child process state is inconsistent (no child process but waitpid still called). Without `pytest-timeout`, no mechanism interrupts this.

**Fix**:
- `pyproject.toml`: `addopts = "-q -m 'not live_fp'"` (default exclusion)
- Evaluator command: added `not live_fp` to marker expression

### RC-2: Integration tests exceed F_D timeout (TIMEOUT)

**What**: 61 integration tests install fresh sandboxes. Each install takes ~3s. Total ~180s > 120s F_D timeout.

**Why**: Integration tests validate installed graph walk — they're the `unit_tests->integration_tests` edge's concern, not the `code<->unit_tests` edge's `tests_pass` F_D evaluator.

**Fix**: Added `not integration` to evaluator marker expression. Integration tests run on their own edge.

### RC-3 (prior session): test_runs/ under test tree (COLLECTION)

**What**: `builds/python/tests/runs/` contained sandbox workspace copies with their own test files. pytest collected these during discovery, causing 503+ collection errors and hanging during collection phase.

**Fix**: Relocated to `builds/python/test_runs/` (outside test tree). Updated `scenario_helpers._RUNS_DIR` and `.gitignore`.

### RC-4 (prior session): Stale test assertions from ABG v1.0.1 (FAILURE)

**What**: 2 assertions in `test_installer.py` referenced ABG v1.0.0 artifacts (`.genesis/gtl_spec/`, `genesis_core` in genesis.yml) that no longer exist in v1.0.1.

**Fix**: Updated assertions to match v1.0.1 structure (`.genesis/genesis/`, `runtime_contract:` in genesis.yml).

---

## Changes Made

### Evaluator command (sdlc_graph.py, source + frozen spec)

```
# Before:
-m 'not e2e'

# After:
-m 'not e2e and not integration and not live_fp'
```

Applied to:
- `builds/python/src/genesis_sdlc/sdlc_graph.py` (source, both top-level and instantiate)
- `.gsdlc/release/workflows/genesis_sdlc/standard/v1_0_0b1/spec.py` (frozen, both paths)

### pytest config (pyproject.toml)

```toml
addopts = "-q -m 'not live_fp'"
markers = [
    "e2e: end-to-end sandbox tests — install into fresh directory and verify operational",
    "integration: multi-hop graph walk integration tests",
    "live_fp: live F_P qualification tests (requires ANTHROPIC_API_KEY + MCP transport)",
    "slow: tests that install fresh sandboxes (>5s each)",
]
```

### Test skip (test_sdlc_graph.py)

`test_guide_req_coverage_passes_against_current_guide` — skip if `docs/USER_GUIDE.md` doesn't exist (downstream artifact, not yet authored).

---

## Verification

### Fast deterministic tests (F_D evaluator scope)

```
122 tests, 56s, 0 failures — well under 120s F_D timeout
```

### Full non-live_fp suite

```
229 tests (247 collected - 18 live_fp deselected)
226 passed, 2 skipped, 1 skip (USER_GUIDE not yet authored)
269s total — completes reliably
```

### genesis gaps delta

```
Before fixes:  total_delta = 10  (tests_pass F_D timeout, module/req coverage F_D failures)
After fixes:   total_delta = 7   (all F_D pass, only F_P evaluators remain)
```

### Remaining F_P evaluators (7)

All require F_P dispatch (LLM artifact generation) — not addressable by code fixes:
- decomp_complete, design_coherent, module_schedule, code_complete
- coverage_complete, sandbox_e2e_passed, guide_content_certified

---

## Test Tier Model

After this analysis, the test suite has a clear three-tier structure:

| Tier | Marker | When to run | Timeout |
|------|--------|-------------|---------|
| **Fast** | `not e2e and not integration and not live_fp` | F_D evaluator, every iterate | 120s budget |
| **Integration** | `integration` | Explicit, own edge evaluator | ~5 min |
| **Live F_P** | `live_fp` | Explicit only, requires MCP + API key | unbounded |

The `tests_pass` F_D evaluator runs Tier 1 only. Integration tests are validated by the `sandbox_e2e_passed` F_P evaluator on the `unit_tests->integration_tests` edge. Live F_P tests are qualification tests, not part of the convergence loop.
