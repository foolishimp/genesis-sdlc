# Implements: REQ-F-PKG-001
"""
custody_test — project GTL spec for genesis.

Edit assets, edges, and evaluators to match your domain.
Run: PYTHONPATH=.genesis python -m genesis gaps --workspace .
"""
from gtl.core import (
    Asset, Edge, Evaluator, Job, Operator,
    Package, Worker, F_D, F_P,
)

# ── Assets ────────────────────────────────────────────────────────────────────
spec   = Asset(name="spec",   id_format="SPEC-{SEQ}")
output = Asset(name="output", id_format="OUT-{SEQ}",  lineage=[spec])

# ── Edge ──────────────────────────────────────────────────────────────────────
op = Operator("agent", F_P, "agent://claude/genesis")
edge = Edge(name="spec→output", source=spec, target=output, using=[op])

eval_complete = Evaluator(
    "output_complete", F_P,
    "agent: output satisfies spec",
)
job = Job(edge=edge, evaluators=[eval_complete])

# ── Package + Worker ──────────────────────────────────────────────────────────
package = Package(
    name="custody_test",
    assets=[spec, output],
    edges=[edge],
    operators=[op],
)
worker = Worker(id="claude_code", can_execute=[job])

if __name__ == "__main__":
    import json
    print(json.dumps({
        "package": package.name,
        "assets": [a.name for a in package.assets],
        "edges": [e.name for e in package.edges],
        "worker": worker.id,
    }, indent=2))
