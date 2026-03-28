# /gen-iterate — Run One Iteration Cycle

Runs one F_D→F_P→F_H cycle on the next blocking edge in the installed workspace.

## Usage

```
/gen-iterate
```

## Instructions

1. Run:

```bash
PYTHONPATH=.gsdlc/release:.genesis python -m genesis iterate --workspace .
```

2. Parse stdout as JSON and route on `blocking_reason` or status.

3. If the engine reports `fp_dispatch`:
   - read the manifest path from the engine output
   - treat `.gsdlc/release/active-workflow.json` as the install-managed default hint only
   - treat `specification/design/fp/` as the project-local F_P tuning surface
   - treat `.ai-workspace/runtime/` as the mutable runtime/session state surface
   - render the effective bounded prompt from the manifest with:

```bash
PYTHONPATH=.gsdlc/release:.genesis python -m genesis_sdlc.release.fp_prompt --manifest <manifest_path> --workspace .
```

   - dispatch that rendered prompt through the backend selected by the resolved runtime under `.ai-workspace/runtime/resolved-runtime.json`
   - treat worker assignment as primary:
     - resolve the winning `role -> worker -> backend` mapping from `.ai-workspace/runtime/resolved-runtime.json`
     - dispatch through the selected worker for the constructive role
     - treat backend choice as derived from that worker assignment, not as a separate selector
   - write the result JSON to the manifest's `result_path`
   - ingest it with:

```bash
PYTHONPATH=.gsdlc/release:.genesis python -m genesis assess-result --result <result_path> --workspace .
```

4. If the engine reports `fh_gate`, surface the criteria and wait for approval.

5. If the engine reports `fd_gap`, surface the deterministic failures exactly and stop. Do not re-dispatch F_P until the deterministic surface is repaired.
