"""
genesis_sdlc — project spec as GTL Package

This file IS the spec. The type system is the law.

  Asset.markov     → acceptance criteria for that asset type
  Job.evaluators   → convergence tests for that edge
  Edge.context     → constraint surface for that transition
  Worker           → who executes what

genesis_sdlc follows the standard SDLC bootstrap graph:

    intent → requirements → feature_decomp → design → code ↔ unit_tests

genesis_sdlc depends on abiogenesis (the GTL engine) and is built using it.
The engine lives at .genesis/genesis/; run as:
    PYTHONPATH=.genesis python -m genesis <command> --workspace .

No separate requirements document. REQ keys emerge from this Package
and are traced through feature vectors in .ai-workspace/features/.
"""
from gtl.core import (
    Package, Asset, Edge, Operator, Rule, Context, Evaluator, Job, Worker,
    F_D, F_P, F_H, consensus,
    OPERATIVE_ON_APPROVED, OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)


# ── Contexts ──────────────────────────────────────────────────────────────────
# Constraint surfaces loaded into the agent prompt at each edge.
# Digests are sha256 of file content — PENDING until content stabilises.

bootloader = Context(
    name="bootloader",
    locator="workspace://spec/GENESIS_BOOTLOADER.md",
    digest="sha256:" + "0" * 64,   # PENDING
)

this_spec = Context(
    name="genesis_sdlc_spec",
    locator="workspace://spec/packages/genesis_sdlc.py",
    digest="sha256:" + "0" * 64,   # PENDING — self-referential
)

intent_doc = Context(
    name="intent",
    locator="workspace://INTENT.md",
    digest="sha256:" + "0" * 64,   # PENDING — written at intent edge
)

design_adrs = Context(
    name="design_adrs",
    locator="workspace://design/adrs/",
    digest="sha256:" + "0" * 64,   # PENDING — written at design edge
)


# ── Operators ─────────────────────────────────────────────────────────────────

claude_agent  = Operator("claude_agent",  F_P, "agent://claude/genesis")
human_gate    = Operator("human_gate",    F_H, "fh://single")
pytest_op     = Operator("pytest",        F_D, "exec://python -m pytest tests/ -q")
check_impl_op = Operator("check_impl",    F_D, "exec://python -m genesis check-tags --type implements --path src/")
check_test_op = Operator("check_test",    F_D, "exec://python -m genesis check-tags --type validates --path tests/")


# ── Rules ─────────────────────────────────────────────────────────────────────

standard_gate = Rule(
    "standard_gate", approve=consensus(1, 1), dissent="recorded"
)


# ── Assets ────────────────────────────────────────────────────────────────────
# markov conditions ARE the acceptance criteria for each asset type.

intent = Asset(
    name="intent",
    id_format="INT-{SEQ}",
    markov=["problem_stated", "value_proposition_clear", "scope_bounded"],
)

requirements = Asset(
    name="requirements",
    id_format="REQ-{SEQ}",
    lineage=[intent],
    markov=["keys_testable", "intent_covered", "no_implementation_details"],
    operative=OPERATIVE_ON_APPROVED,
)

feature_decomp = Asset(
    name="feature_decomp",
    id_format="FD-{SEQ}",
    lineage=[requirements],
    markov=["all_req_keys_covered", "dependency_dag_acyclic", "mvp_boundary_defined"],
    operative=OPERATIVE_ON_APPROVED,
)

design = Asset(
    name="design",
    id_format="DES-{SEQ}",
    lineage=[feature_decomp],
    markov=["adrs_recorded", "tech_stack_decided", "interfaces_specified", "no_implementation_details"],
    operative=OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)

code = Asset(
    name="code",
    id_format="CODE-{SEQ}",
    lineage=[design],
    markov=["implements_tags_present", "importable", "no_v2_features"],
)

unit_tests = Asset(
    name="unit_tests",
    id_format="TEST-{SEQ}",
    lineage=[code],
    markov=["all_pass", "validates_tags_present"],
)


# ── Edges ─────────────────────────────────────────────────────────────────────

e_intent_req = Edge(
    name="intent→requirements",
    source=intent,
    target=requirements,
    using=[claude_agent, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec],
)

e_req_feat = Edge(
    name="requirements→feature_decomp",
    source=requirements,
    target=feature_decomp,
    using=[claude_agent, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec, intent_doc],
)

e_feat_design = Edge(
    name="feature_decomp→design",
    source=feature_decomp,
    target=design,
    using=[claude_agent, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec, intent_doc],
)

e_design_code = Edge(
    name="design→code",
    source=design,
    target=code,
    using=[claude_agent, check_impl_op],
    context=[bootloader, this_spec, design_adrs],
)

e_tdd = Edge(
    name="code↔unit_tests",
    source=[code, unit_tests],
    target=unit_tests,
    co_evolve=True,
    using=[claude_agent, pytest_op, check_impl_op, check_test_op],
    context=[bootloader, this_spec, design_adrs],
)


# ── Evaluators ────────────────────────────────────────────────────────────────

# intent→requirements
eval_intent_fh = Evaluator(
    "intent_approved", F_H,
    "Human confirms: problem is clearly stated, value proposition is evident, scope is bounded",
)

# requirements→feature_decomp
eval_req_coverage = Evaluator(
    "req_coverage", F_D,
    "Every REQ key in Package.requirements appears in ≥1 feature vector satisfies: field",
    command="python -m genesis check-req-coverage --package spec.packages.genesis_sdlc:package --features .ai-workspace/features/",
)
eval_decomp_fh = Evaluator(
    "decomp_approved", F_H,
    "Human approves: feature set is complete, dependency order is correct, MVP boundary is clear",
)

# feature_decomp→design
eval_design_fp = Evaluator(
    "design_coherent", F_P,
    "Agent: ADRs cover all features, tech stack is decided, interfaces are specified, no implementation details have leaked into spec",
)
eval_design_fh = Evaluator(
    "design_approved", F_H,
    "Human approves design before any code is written",
)

# design→code
eval_impl_tags = Evaluator(
    "impl_tags", F_D,
    "All source files carry at least one # Implements: REQ-* tag, zero untagged",
    command="python -m genesis check-tags --type implements --path src/",
)
eval_code_fp = Evaluator(
    "code_complete", F_P,
    "Agent: code implements all features per design ADRs; no V2 features present; importable",
)

# code↔unit_tests
eval_tests_pass = Evaluator(
    "tests_pass", F_D,
    "pytest: zero failures, zero errors",
    command="python -m pytest tests/ -q --tb=short",
)
eval_test_tags = Evaluator(
    "validates_tags", F_D,
    "All test files carry at least one # Validates: REQ-* tag, zero untagged",
    command="python -m genesis check-tags --type validates --path tests/",
)
eval_coverage_fp = Evaluator(
    "coverage_complete", F_P,
    "Agent: test suite covers all features; no REQ key without a corresponding test",
)


# ── Jobs ──────────────────────────────────────────────────────────────────────

job_intent_req  = Job(e_intent_req,  [eval_intent_fh])
job_req_feat    = Job(e_req_feat,    [eval_req_coverage, eval_decomp_fh])
job_feat_design = Job(e_feat_design, [eval_design_fp, eval_design_fh])
job_design_code = Job(e_design_code, [eval_impl_tags, eval_code_fp])
job_tdd         = Job(e_tdd,         [eval_tests_pass, eval_test_tags, eval_coverage_fp])


# ── Worker ────────────────────────────────────────────────────────────────────

worker = Worker(
    id="claude_code",
    can_execute=[job_intent_req, job_req_feat, job_feat_design, job_design_code, job_tdd],
)


# ── Package ───────────────────────────────────────────────────────────────────
# requirements list is the authoritative REQ key registry for this project.
# Add keys here as requirements are written; check-req-coverage enforces coverage.

package = Package(
    name="genesis_sdlc",
    assets=[intent, requirements, feature_decomp, design, code, unit_tests],
    edges=[e_intent_req, e_req_feat, e_feat_design, e_design_code, e_tdd],
    operators=[claude_agent, human_gate, pytest_op, check_impl_op, check_test_op],
    rules=[standard_gate],
    contexts=[bootloader, this_spec, intent_doc, design_adrs],
    requirements=[
        # Populated as requirements are written.
        # gen check-req-coverage --package spec.packages.genesis_sdlc:package
        #     --features .ai-workspace/features/
        # will verify every key here appears in a feature vector.
    ],
)


if __name__ == "__main__":
    import json
    print(json.dumps({
        "package": package.name,
        "assets": [a.name for a in package.assets],
        "edges": [e.name for e in package.edges],
        "jobs": len(worker.can_execute),
        "worker": worker.id,
        "requirements": package.requirements,
    }, indent=2))
