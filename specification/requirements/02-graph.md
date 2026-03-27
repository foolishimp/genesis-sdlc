# SDLC Graph Requirements

**Family**: REQ-F-GRAPH-*
**Status**: Still needed
**Category**: Capability

Graph requirements define the admissible SDLC topology and asset stability model.

### REQ-F-GRAPH-001 — GTL Package defines the SDLC graph

The Package declares a typed asset graph with admissible transitions. The graph is a clean DAG — no reflexive edges. Each edge explicitly separates creative input (lineage) from evidence prerequisites (convergence gates).

**Acceptance Criteria**:
- AC-1: Eleven assets: `intent`, `requirements`, `feature_decomp`, `design`, `module_decomp`, `code`, `unit_tests`, `integration_tests`, `user_guide`, `bootloader`, `uat_tests`
- AC-2: Ten edges with the DAG topology: E1 `intent→requirements`, E2 `requirements→feature_decomp`, E3 `feature_decomp→design`, E4 `design→module_decomp`, E5 `module_decomp→code`, E6 `module_decomp→unit_tests`, E7 `[code, unit_tests]→integration_tests`, E8 `[requirements, design, integration_tests]→bootloader`, E9 `[design, integration_tests]→user_guide`, E10 `[requirements, integration_tests]→uat_tests`
- AC-3: Each edge has at least one evaluator
- AC-4: Four multi-source edges (E7, E8, E9, E10). No reflexive or co-evolving edges. The graph is a DAG.
- AC-5: Package is loadable: `python builds/python/src/genesis_sdlc/sdlc_graph.py` produces valid JSON describing the graph

### REQ-F-GRAPH-002 — Asset.markov conditions are acceptance criteria

Each asset type defines its own stability conditions.

**Acceptance Criteria**:
- AC-1: Every `Asset` in the Package has a non-empty `markov` list of named conditions
- AC-2: Markov conditions are surfaced in the F_P manifest as part of the output contract
- AC-3: An asset is stable when all markov conditions are met and all edge evaluators pass
