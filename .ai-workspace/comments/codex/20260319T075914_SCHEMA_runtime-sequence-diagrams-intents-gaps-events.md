# SCHEMA: Runtime Sequence Diagrams for Intents, Gaps, and Events

**Author**: Codex
**Date**: 2026-03-19T07:59:14Z
**Addresses**: engine runtime flow; gap detection; feature emergence; backlog promotion; event storage surfaces
**For**: all

## Summary

These diagrams document current implementation reality. They show where state is stored, which functions read it, and which event types the engine actually consumes to identify gaps and convergence.

Two boundaries matter:

- `fp_assessment`, `review_approved`, and `edge_converged` participate directly in convergence
- `intent_raised` is currently emitted, but no engine path consumes it to create feature vectors automatically

## Storage Surfaces

- `.ai-workspace/events/events.jsonl` — append-only event log
- `.ai-workspace/fp_manifests/*.json` — F_P dispatch manifests written by `gen_iterate`
- `.ai-workspace/fp_results/*.json` — F_P assessment payloads written by the actor
- `.ai-workspace/features/active/*.yml` and `.ai-workspace/features/completed/*.yml` — feature vectors
- `.ai-workspace/backlog/BL-*.yml` — pre-intent backlog items
- `.ai-workspace/reviews/proxy-log/*.md` — human-proxy review audit trail

## Diagram 1 — `gen start` / `gen iterate`: how graph work advances toward code

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI as genesis __main__.py
    participant Config as .genesis/genesis.yml
    participant WS as workspace_bootstrap()
    participant Log as events.jsonl
    participant Start as gen_start()
    participant Bind as bind_fd()
    participant Iter as gen_iterate()/iterate()
    participant Manifest as fp_manifests/*.json
    participant Result as fp_results/*.json
    participant Actor as F_P actor
    participant Files as workspace artifacts

    User->>CLI: python -m genesis start --auto --workspace .
    CLI->>Config: load package, worker, pythonpath
    CLI->>WS: bootstrap workspace
    WS->>Log: ensure .ai-workspace/events/events.jsonl exists
    CLI->>Start: gen_start(scope, stream, auto=True)

    loop topological job scan
        Start->>Bind: bind_fd(job, stream, resolver, workspace, spec_hash)
        Bind->>Log: read all_events() + project(current)
        Bind->>Files: run F_D evaluator commands
    end

    alt selected job has only F_P gap
        Start->>Iter: gen_iterate(selected_job)
        Iter->>Log: append edge_started{edge,target}
        Iter->>Manifest: write dispatch manifest
        Iter->>Log: append fp_dispatched{edge,failing_evaluators}
        CLI-->>User: exit 2 + fp_manifest_path
        User->>Actor: dispatch prompt from manifest
        Actor->>Files: write target artifact(s)
        Actor->>Result: write assessment JSON
        User->>CLI: python -m genesis emit-event --type fp_assessment ...
        CLI->>Log: append fp_assessment{edge,evaluator,result,spec_hash}
        Note over Start,Files: The next /gen-start or /gen-gaps re-runs bind_fd against the updated files and event log.
    else selected job has only F_H gap
        Start->>Iter: gen_iterate(selected_job)
        Iter->>Log: append edge_started{edge,target}
        Iter->>Log: append fh_gate_pending{edge,criteria}
        CLI-->>User: exit 3 + gate criteria
        User->>CLI: python -m genesis emit-event --type review_approved ...
        CLI->>Log: append review_approved{edge,actor}
    else selected job still has F_D gap
        Start->>Iter: gen_iterate(selected_job)
        Iter->>Log: append fd_gap_found{edge,failing,delta_summary}
        CLI-->>User: exit 4 + failing evaluators
    end
```

## Diagram 2 — `gen gaps`: where gaps are identified and convergence is certified

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant CLI as genesis gaps
    participant Gaps as gen_gaps()
    participant Bind as bind_fd()
    participant Eval as F_D evaluators
    participant Log as events.jsonl

    User->>CLI: python -m genesis gaps --workspace .
    CLI->>Gaps: gen_gaps(scope, stream)

    loop each job in scope
        Gaps->>Bind: bind_fd(job, stream, resolver, workspace, spec_hash)
        Bind->>Log: read fp_assessment, review_approved, edge_started history
        Bind->>Eval: rerun deterministic commands against workspace
        Eval-->>Bind: pass/fail detail
        Bind-->>Gaps: delta, passing, failing, delta_summary

        alt delta == 0 and no existing certificate
            Gaps->>Log: append edge_converged{edge,target,feature?,delta=0}
        else delta > 0
            Gaps-->>CLI: keep gap in response only
        end
    end

    CLI-->>User: total_delta + per-edge failing evaluators
    Note over Gaps,Log: edge_converged is an audit certificate emitted by gen_gaps. It does not bypass F_D re-evaluation.
```

## Diagram 3 — requirements coverage gap: how a missing feature is detected today

```mermaid
sequenceDiagram
    autonumber
    actor SpecAuthor as Spec author
    participant Spec as Package.requirements
    participant Start as gen_start/gen_iterate
    participant Coverage as check-req-coverage
    participant Features as features/*.yml
    participant Log as events.jsonl

    SpecAuthor->>Spec: add REQ-F-NEW-001
    SpecAuthor->>Start: run /gen-start or /gen-iterate
    Start->>Coverage: check-req-coverage --package ... --features .ai-workspace/features/
    Coverage->>Features: scan satisfies: keys
    Features-->>Coverage: REQ-F-NEW-001 missing
    Coverage-->>Start: passes = false
    Start->>Log: append fd_gap_found{edge=requirements→feature_decomp}
    Start-->>SpecAuthor: stopped_by = fd_gap

    Note over Start,Log: Current code enforces F_D before F_P dispatch. An uncovered REQ key does not automatically dispatch decomp_complete.

    SpecAuthor->>Features: seed or repair feature YAMLs out of band
    SpecAuthor->>Start: rerun /gen-start
    Start->>Coverage: recheck coverage
    Coverage-->>Start: passes = true
    Start->>Log: append edge_started + fp_dispatched
    Note over Features,Log: After F_D goes green, the F_P actor can refine feature decomposition and emit fp_assessment.
```

## Diagram 4 — backlog promotion: how a need enters the event log as intent

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Backlog as BL-xxx.yml
    participant Promote as genesis_sdlc.backlog promote
    participant Emit as genesis emit-event
    participant Log as events.jsonl
    participant Engine as gen_start/gen_gaps

    User->>Promote: python -m genesis_sdlc.backlog promote BL-011 --feature REQ-F-DOCS-V2
    Promote->>Backlog: set status=promoted, promoted_to, promotion_reason
    Promote->>Emit: python -m genesis emit-event --type intent_raised ...
    Emit->>Log: append intent_raised{backlog_id,title,feature,reason}
    Engine->>Log: read event history during projection

    Note over Engine,Log: Current engine code consumes fp_assessment, review_approved, edge_converged, and edge_started during convergence checks. No runtime path currently consumes intent_raised to auto-create a feature vector.
```

## Recommended Action

1. Use these diagrams as the current-state baseline while BOOT-V2 is being implemented.
2. Decide whether the desired future flow is `gap_detected -> intent_raised -> feature_vector_created` or `gap_detected -> feature_vector_created` directly.
3. If the intent path is desired, add a concrete engine or skill consumer for `intent_raised`; today it is emit-only.
4. If automatic feature creation from uncovered REQ keys is desired, the `requirements→feature_decomp` edge needs a mechanism that can act while `req_coverage` is red.
