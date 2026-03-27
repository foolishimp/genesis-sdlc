# Human Gate Requirements

**Family**: REQ-F-GATE-*
**Status**: Still needed
**Category**: Governance

Human gate requirements define where and how explicit human approval is constitutionally required.

### REQ-F-GATE-001 — F_H evaluators gate spec/design boundaries

Human approval is required at spec and design boundaries before downstream work proceeds.

**Acceptance Criteria**:
- AC-1: F_H evaluators detected at bind time by projecting the event stream for `approved{kind: fh_review}` events
- AC-2: If no operative approval exists for the current edge, the evaluator is in the `failing` set
- AC-3: `iterate()` emits `fh_gate_pending` with evaluator criteria and exits code 3
- AC-4: F_H gate criteria surfaced verbatim from `Evaluator.description`
- AC-5: `actor` field mandatory on all `approved` events: `"human"` or `"human-proxy"` — never absent
- AC-6: The ordering invariant (F_D→F_P→F_H) prevents reviewing candidates with deterministic failures
