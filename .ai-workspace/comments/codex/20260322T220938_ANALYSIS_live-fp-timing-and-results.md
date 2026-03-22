# ANALYSIS: Live F_P Timing And Results

**Date**: 2026-03-22T22:09:38+11:00
**Scope**: review of current `abiogenesis` live F_P qualification archives

## Batches Reviewed

- Schema qualification:
  - `/Users/jim/src/apps/abiogenesis/builds/claude_code/tests/runs/test_live_fp_qualification/20260322T102640_test_schema_qualification`
- UAT qualification, first full batch:
  - `/Users/jim/src/apps/abiogenesis/builds/claude_code/tests/runs/test_live_fp_qualification/20260322T103154_test_uat_qualification`
- UAT qualification, current rerun batch:
  - `/Users/jim/src/apps/abiogenesis/builds/claude_code/tests/runs/test_live_fp_qualification/20260322T104737_test_uat_qualification`

## Results

| Batch | Runs counted | Outcome | Notes |
|---|---:|---|---|
| Schema qualification | 10 | 10/10 pass | Fully green. |
| UAT qualification, first full batch | 10 | 4/10 pass | Failures were semantic quality failures, not transport crashes. |
| UAT qualification, current rerun | 8 completed at review time | 8/8 pass so far | Rerun appears materially improved. |

## Timing Breakdown

All timings are derived from archived `run.json` timestamps.

| Batch | Avg total / run | `iterate` | MCP `claude_code` | `assess-result` | `gaps` + `finalize` | Total range |
|---|---:|---:|---:|---:|---:|---:|
| Schema qualification | 56.2s | 0.8s | 55.3s | `<0.1s` | `<0.1s` | 42.2s to 98.8s |
| UAT qualification, first full batch | 85.5s | 1.0s | 84.3s | `<0.1s` | `<0.1s` | 69.9s to 104.9s |
| UAT qualification, current rerun | 80.7s | 1.0s | 79.6s | `<0.1s` | `<0.1s` | 61.6s to 104.7s |

Representative single runs:

| Run | Result | Total | `iterate` | MCP `claude_code` | `assess-result` | `gaps` + `finalize` |
|---|---|---:|---:|---:|---:|---:|
| `schema_run_0` | pass | 57.1s | 0.8s | 56.1s | 0.0s | 0.1s |
| `uat_run_1` in first batch | pass | 104.9s | 0.6s | 104.2s | 0.0s | 0.1s |
| `uat_run_0` in rerun batch | pass | 104.7s | 0.6s | 103.9s | 0.0s | 0.1s |

## Evidence

- Schema batch summary:
  - `/Users/jim/src/apps/abiogenesis/builds/claude_code/tests/runs/test_live_fp_qualification/20260322T102640_test_schema_qualification/summary.json`
- Schema example run:
  - `/Users/jim/src/apps/abiogenesis/builds/claude_code/tests/runs/test_live_fp_qualification/20260322T102640_test_schema_qualification/schema_run_0/run.json`
- Schema generated artifact:
  - `/Users/jim/src/apps/abiogenesis/builds/claude_code/tests/runs/test_live_fp_qualification/20260322T102640_test_schema_qualification/workspace/schema_run_0/output/schema.sql`
- UAT first-batch example:
  - `/Users/jim/src/apps/abiogenesis/builds/claude_code/tests/runs/test_live_fp_qualification/20260322T103154_test_uat_qualification/uat_run_1/run.json`
- UAT rerun example:
  - `/Users/jim/src/apps/abiogenesis/builds/claude_code/tests/runs/test_live_fp_qualification/20260322T104737_test_uat_qualification/uat_run_0/run.json`

## Analysis

The runtime cost is overwhelmingly concentrated in the live MCP Claude step. `iterate`, `assess-result`, and `gaps` are essentially negligible. That means the current latency is not coming from ABG app logic. It is dominated by:

- fresh MCP stdio client startup
- fresh `npx @steipete/claude-code-mcp` startup
- fresh MCP session initialization
- fresh Claude subprocess invocation under the MCP tool
- fresh isolated sandbox per run

This points much more strongly to **cold-start transport overhead** than to an inherently slower or degraded operating mode.

The behavioral result is also important:

- schema is already qualified strongly under the live lane
- UAT was initially mixed but the rerun batch improved materially
- the earlier UAT failures were stable semantic failures (`no numbered steps`, `no Expected Result sections`), not random transport failures

## Conclusion

Current evidence supports this reading:

- **performance concern**: mostly startup/session overhead, likely optimizable
- **behavioral concern**: UAT prompt/contract quality was the real issue, and current rerun data suggests improvement

This does **not** currently look like a fundamentally worse execution mode than direct Claude. It looks like an expensive cold-start harness around a viable mode.
