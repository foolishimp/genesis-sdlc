# /gen-review — Human Evaluator Gate

Surfaces the current F_H gate for explicit approval against the installed workflow.

## Usage

```
/gen-review
```

## Instructions

1. Run:

```bash
PYTHONPATH=.gsdlc/release:.genesis python -m genesis gaps --workspace .
```

2. Identify the current blocking edge and any `fh_gate_pending` criteria.

3. Present:
   - the current edge
   - the current candidate artifact
   - the F_H criteria for that edge
   - the current deterministic status from the gap report

4. On approval, emit:

```bash
PYTHONPATH=.gsdlc/release:.genesis python -m genesis emit-event --type approved --data '{"kind":"fh_review","edge":"<edge>","actor":"human"}' --workspace .
```

5. On rejection, stop and report the rejection reason. Do not invent a pass event.
