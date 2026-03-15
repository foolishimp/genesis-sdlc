# ADR-001: Package Structure

**Status**: Accepted
**Implements**: REQ-F-BOOT-001, REQ-F-BOOT-002, REQ-F-GRAPH-001

## Decision

genesis_sdlc is a Python package with this layout:

```
genesis_sdlc/
├── src/genesis_sdlc/       ← installable package
│   ├── __init__.py         ←   version + public API
│   └── sdlc_graph.py       ←   standard SDLC Package + Worker (importable template)
├── tests/                  ← pytest suite
│   ├── __init__.py
│   ├── test_sdlc_graph.py  ←   graph loads, edges/evaluators correct
│   └── test_gaps.py        ←   gen gaps runs against a fresh workspace
├── spec/packages/          ← GTL spec (this project's own methodology graph)
│   └── genesis_sdlc.py
├── .genesis/               ← bootstrapped engine (abiogenesis v1.0.0)
├── design/adrs/            ← these files
├── INTENT.md
├── README.md
└── pyproject.toml
```

## Rationale

- `src/` layout avoids accidental imports from the project root during testing
- `sdlc_graph.py` exports a ready-to-use SDLC Package — users import it as a starting point or reference
- The `.genesis/` bootstrap is the only engine dependency; no `genesis` pip install needed at runtime
- `spec/genesis_sdlc.py` is the methodology graph for building genesis_sdlc itself (dog-fooding)

## Consequences

- `pyproject.toml` declares `packages = [{include = "genesis_sdlc", from = "src"}]`
- Tests run with `PYTHONPATH=src:. pytest tests/` (src for genesis_sdlc, . for spec)
- The genesis engine is invoked as `PYTHONPATH=.genesis python -m genesis ...`
