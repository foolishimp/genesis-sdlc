# Command Requirements

**Family**: REQ-F-CMD-*
**Status**: Active
**Category**: Capability

Command requirements define the named operational surfaces that expose the SDLC graph to users and automation.

### REQ-F-CMD-001 — gen gaps reports delta per edge

`gen-gaps` computes the convergence state of the workspace by running evaluators over all jobs.

**Acceptance Criteria**:
- AC-1: Returns JSON with `total_delta`, `converged`, and per-job `gaps[]`
- AC-2: Each gap entry contains: `edge`, `delta`, `failing` (evaluator names), `passing`, `delta_summary`
- AC-3: Runs all F_D evaluators as subprocesses; evaluates F_H via event stream projection; evaluates F_P via assessed event matching with spec_hash validation
- AC-4: `converged: true` iff `total_delta == 0`

### REQ-F-CMD-002 — gen iterate runs one bind-and-iterate pass

`gen-iterate` selects the first unconverged job and executes one F_D→F_P→F_H cycle.

**Acceptance Criteria**:
- AC-1: Selects first unconverged job in topological edge order
- AC-2: Calls `bind_fd()` to pre-compute all F_D results, F_H gates, and F_P assessments
- AC-3: Enforces F_D→F_P→F_H ordering — no F_P dispatch while F_D failing, no F_H gate while F_P unresolved
- AC-4: On F_D failure: reports failing evaluator details, exits code 4
- AC-5: On F_P needed: writes manifest to `.ai-workspace/fp_manifests/`, exits code 2
- AC-6: On F_H needed: reports evaluator criteria, exits code 3
- AC-7: On convergence: exits code 0

### REQ-F-CMD-003 — gen start --auto loops until blocked

`gen-start` is the state-machine entry point that loops `gen-iterate` until convergence or a blocking condition.

**Acceptance Criteria**:
- AC-1: Determines workspace convergence state before iterating
- AC-2: If converged: closes completed features, exits code 0
- AC-3: If not converged: dispatches `gen-iterate` for the next job
- AC-4: `--auto` loops up to MAX_AUTO (50) iterations, stopping on: convergence, `fp_dispatched`, `fh_gate_pending`, `fd_gap`, or max iterations
- AC-5: `--human-proxy` requires `--auto`; performs F_H evaluation per proxy protocol
- AC-6: Exit codes: 0 (converged), 2 (fp_dispatched), 3 (fh_gate_pending), 4 (fd_gap), 5 (max_iterations)

### REQ-F-CMD-004 — Project-local F_P customization is compiled through the control plane

The installed operator path resolves project-local F_P customization through the control-plane compile rather than through a separate legacy prompt-assembly path.

**Acceptance Criteria**:
- AC-1: The installed system defines `specification/design/fp/edge-overrides/` as the project-local surface for per-edge F_P customization
- AC-2: Project-local per-edge overrides are compiled into the effective edge runtime profile before falling back to installed defaults
- AC-3: A project-local override can declare customization intent, requirement refs, design refs, and per-edge guidance or output-path adjustments
- AC-4: If the installed release exposes a helper that renders an effective F_P prompt, that helper derives its output from the resolved runtime or compiled edge runtime profile and remains a read model rather than a separate operative path
- AC-5: Once the control-plane compile exists, direct legacy prompt assembly is not a conforming runtime path
