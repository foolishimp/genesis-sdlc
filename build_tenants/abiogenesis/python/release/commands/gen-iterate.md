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
   - inspect `.gsdlc/release/active-workflow.json` for `customization.fp_transport_agent`
   - treat `specification/design/fp/` as the project-local F_P tuning surface
   - render the effective bounded prompt from the manifest with:

```bash
PYTHONPATH=.gsdlc/release:.genesis python -m genesis_sdlc.release.fp_prompt --manifest <manifest_path> --workspace .
```

   - dispatch that rendered prompt through the configured transport
   - write the result JSON to the manifest's `result_path`
   - ingest it with:

```bash
PYTHONPATH=.gsdlc/release:.genesis python -m genesis assess-result --result <result_path> --workspace .
```

4. If the engine reports `fh_gate`, surface the criteria and wait for approval.

5. If the engine reports `fd_gap`, surface the deterministic failures exactly and stop. Do not re-dispatch F_P until the deterministic surface is repaired.
