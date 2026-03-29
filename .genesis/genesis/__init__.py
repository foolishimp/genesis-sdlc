# Implements: REQ-R-ABG2-INTERPRET
"""
genesis — GTL-native AI SDLC engine.

Consumes Module, Graph, GraphVector, Node natively.

    binding      — ExecutableJob, Worker, WorkSurface, bind_fd, bind_fp, render_delta
    convergence  — EvaluatorOutcome, ConvergenceResult, delta, parent_converged
    interpret    — Traversal, traverse, schedule, apply_selection
    services     — Scope, module_to_executable_jobs, start, iterate_edge, gaps
    selection    — enumerate_candidates, validate_selection, SelectionDecision
    provenance   — provenance_snapshot
    events       — EventStream, emit
    projection   — project
    transport    — Subprocess transport for F_P actor invocations (ADR-022)
    cli_adapter  — CLI entry point wiring
    selfhosting  — Bootloader consistency checks
    __main__     — CLI entry point
"""
__version__ = "1.1.0.dev0"
