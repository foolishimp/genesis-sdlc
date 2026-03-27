# ADR-004 — Ecosystem Lifecycle

**Status**: Approved
**Date**: 2026-03-27
**Implements**: REQ-F-BACKLOG-*, REQ-F-ECO-*

---

## Context

The base process workflow defines the development lifecycle that genesis_sdlc must realize as a framework.

That is necessary, but not sufficient, to describe the wider ecosystem that the framework belongs to.

The requirement surface now states that genesis_sdlc exists inside a larger homeostatic system:

- pre-intent incubation exists before the workflow
- accepted artifacts move into operational use after the workflow
- operational observation produces signals
- signals are evaluated and returned to the pre-intent holding area

Without this wider framing, the workflow appears to stop at `uat_tests`, even though the method already assumes a reverse path from real-world use back to new intent.

---

## Decision

genesis_sdlc adopts the following ecosystem lifecycle model:

```text
creche -> intent -> requirements -> feature_decomp -> design -> module_decomp
       -> code -> unit_tests -> integration_tests -> user_guide -> uat_tests
       -> publish -> operational_env -> monitoring -> homeostatic_eval -> creche
```

The base process workflow remains the 1.0 lifecycle law.

The post-`uat_tests` extension is Phase 2:

- `publish`
- `operational_env`
- `monitoring`
- `homeostatic_eval`

This shared design record interprets that requirement surface and preserves the 1.0 / Phase 2 boundary.

---

## Interpretation

The ecosystem stages mean:

- `creche` — pre-intent incubation and holding area for emerging signals before they are formalized as intent
- `publish` — transition from accepted development artifact to available released artifact
- `operational_env` — live usage or deployment environment where the released artifact is actually exercised
- `monitoring` — operational observation surface: install outcomes, runtime behavior, incidents, drift, usage, and other field signals
- `homeostatic_eval` — evaluation of operational signals into actionable observations suitable for backlog or renewed intent

The return path is:

- `monitoring` produces signals
- `homeostatic_eval` interprets those signals
- resulting observations return to `creche`
- promoted items later become intent vectors through backlog and the normal renewal path

This keeps the ecosystem cyclical while allowing the base process workflow itself to remain a forward lifecycle shape.

---

## Boundaries

The ecosystem lifecycle does not mean:

- the 1.0 base process workflow must already contain these Phase 2 stages as required graph assets
- `ci_cd` is itself a constitutional lifecycle node
- one implementation mechanism is prescribed for publish, deployment, or monitoring

`ci_cd`, installers, release tooling, deployment topology, telemetry stacks, and runtime infrastructure are design encodings of these ecosystem stages, not the stages themselves.

---

## Consequences

- the SDLC is now framed as part of a larger ecosystem rather than a pipeline that ends at acceptance
- `publish` and `monitoring` have a clear ontological role even before they become framework requirements
- operational observation is explicitly tied back to backlog and new intent
- future Phase 2 repricing can promote some or all of these ecosystem stages into the formal framework requirement surface when the project is ready
