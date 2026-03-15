# ADR-002: SDLC Graph as Importable Template

**Status**: Accepted
**Implements**: REQ-F-GRAPH-001, REQ-F-GRAPH-002

## Decision

`src/genesis_sdlc/sdlc_graph.py` exports a pre-built, standard SDLC Package and Worker that any project can import and customise:

```python
from genesis_sdlc.sdlc_graph import package, worker
```

The Package defines the 6-asset bootstrap graph:
`intent → requirements → feature_decomp → design → code ↔ unit_tests`

with concrete evaluators for each edge (tag checks, pytest, coverage check, human gates).

## Rationale

- The canonical use case is: install genesis_sdlc, import the standard graph, configure paths for your project, run gen gaps
- Exporting from `src/` makes genesis_sdlc a library — no magic, no registration, just Python
- The Package is parameterised only by path conventions (src_path, tests_path); a project adapts by subclassing or overriding evaluator commands
- The standard graph is the dog-food spec itself — genesis_sdlc used it to build itself

## Interface

```python
# src/genesis_sdlc/sdlc_graph.py
package: Package   # standard SDLC graph, src_path="src/", tests_path="tests/"
worker: Worker     # single worker: claude_code
```

## Consequences

- The Package in `sdlc_graph.py` and the Package in `spec/packages/genesis_sdlc.py` are the same graph — the spec is the template
- Path conventions (`src/`, `tests/`) are the only coupling point; other projects override evaluator commands
