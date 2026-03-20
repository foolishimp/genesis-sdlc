Feature: all
Edge: intent→requirements
Iteration: 1
Timestamp: 2026-03-21T14:00:00Z
Decision: approved

Criteria:
- Criterion: Problem stated
  Evidence: INT-001 states "abiogenesis provides a GTL engine but ships no SDLC graph — every project must define its own Package from scratch". INT-002 states "design→code edge is a single large leap" conflating decomposition and construction. INT-003 states "integration tests and user guide are outside the graph" with no F_D evaluators.
  Satisfied: yes — all three intents articulate clear, specific problems

- Criterion: Value proposition clear
  Evidence: INT-001 delivers "a complete graph with convergence guarantees, traceability, and event-sourced state". INT-002 inserts module_decomp for build scheduling. INT-003 adds integration_tests and user_guide as first-class assets with F_D checks.
  Satisfied: yes — each intent states what the user gets and why it matters

- Criterion: Scope bounded
  Evidence: INT-001 explicitly lists out-of-scope (multi-agent, GUI, package distribution). INT-002 excludes basis projections and parallel scheduling. INT-003 excludes guide rewriting and multiple formats. All three have success criteria.
  Satisfied: yes — scope is bounded with explicit exclusions and measurable success criteria
