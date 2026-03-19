"""
genesis_sdlc — project spec as GTL Package

This file IS the spec. The type system is the law.

  Asset.markov     → acceptance criteria for that asset type
  Job.evaluators   → convergence tests for that edge
  Edge.context     → constraint surface for that transition
  Worker           → who executes what

genesis_sdlc follows the standard SDLC bootstrap graph:

    intent → requirements → feature_decomp → design → code ↔ unit_tests → uat_tests

UAT is constitutional: shipping requires sandbox e2e proof, not unit tests alone.
Integration and E2E tests are the primary test surface. Unit tests exist only for
write-primitive invariants (emit, project, EventStream). F_D evaluators must be
acyclic — never invoke genesis subcommands from pytest.

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
    locator="workspace://gtl_spec/GENESIS_BOOTLOADER.md",
    digest="sha256:" + "0" * 64,   # PENDING
)

this_spec = Context(
    name="genesis_sdlc_spec",
    locator="workspace://gtl_spec/packages/genesis_sdlc.py",
    digest="sha256:" + "0" * 64,   # PENDING — self-referential
)

intent_doc = Context(
    name="intent",
    locator="workspace://INTENT.md",
    digest="sha256:" + "0" * 64,   # PENDING — written at intent edge
)

design_adrs = Context(
    name="design_adrs",
    locator="workspace://builds/python/design/adrs/",
    digest="sha256:" + "0" * 64,   # PENDING — written at design edge
)

modules_dir = Context(
    name="modules_dir",
    locator="workspace://.ai-workspace/modules/",
    digest="sha256:" + "0" * 64,   # PENDING — written at module_decomp edge
)


# ── Operators ─────────────────────────────────────────────────────────────────

claude_agent      = Operator("claude_agent",  F_P, "agent://claude/genesis")
human_gate        = Operator("human_gate",    F_H, "fh://single")
pytest_op         = Operator("pytest",        F_D, "exec://python -m pytest builds/python/tests/ -q -m 'not e2e'")
check_impl_op     = Operator("check_impl",    F_D, "exec://python -m genesis check-tags --type implements --path builds/python/src/")
check_test_op     = Operator("check_test",    F_D, "exec://python -m genesis check-tags --type validates --path builds/python/tests/")
check_modules_op  = Operator("check_modules", F_D, "exec://python -c \"import pathlib,sys; fd=pathlib.Path('.ai-workspace/features/'); md=pathlib.Path('.ai-workspace/modules/'); fids={f.stem for f in fd.rglob('*.yml')} if fd.exists() else set(); mfiles=list(md.rglob('*.yml')) if md.exists() else []; content=' '.join(m.read_text() for m in mfiles); covered={fid for fid in fids if fid in content}; uncovered=fids-covered; print({'uncovered':sorted(uncovered),'passes':not bool(uncovered)}); sys.exit(0 if not uncovered and mfiles else 1)\"" )


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

module_decomp = Asset(
    name="module_decomp",
    id_format="MOD-{SEQ}",
    lineage=[design],
    markov=["all_features_assigned", "dependency_dag_acyclic", "build_order_defined"],
    operative=OPERATIVE_ON_APPROVED,
)

code = Asset(
    name="code",
    id_format="CODE-{SEQ}",
    lineage=[module_decomp],
    markov=["implements_tags_present", "importable", "no_v2_features"],
)

unit_tests = Asset(
    name="unit_tests",
    id_format="TEST-{SEQ}",
    lineage=[code],
    markov=["all_pass", "validates_tags_present"],
)

uat_tests = Asset(
    name="uat_tests",
    id_format="UAT-{SEQ}",
    lineage=[unit_tests],
    markov=["sandbox_install_passes", "e2e_scenarios_pass", "accepted_by_human"],
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

e_design_mdecomp = Edge(
    name="design→module_decomp",
    source=design,
    target=module_decomp,
    using=[claude_agent, check_modules_op, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec, design_adrs],
)

e_mdecomp_code = Edge(
    name="module_decomp→code",
    source=module_decomp,
    target=code,
    using=[claude_agent, check_impl_op],
    context=[bootloader, this_spec, design_adrs, modules_dir],
)

e_tdd = Edge(
    name="code↔unit_tests",
    source=[code, unit_tests],
    target=unit_tests,
    co_evolve=True,
    using=[claude_agent, pytest_op, check_impl_op, check_test_op],
    context=[bootloader, this_spec, design_adrs],
)

e_unit_uat = Edge(
    name="unit_tests→uat_tests",
    source=unit_tests,
    target=uat_tests,
    using=[claude_agent, human_gate],
    rule=standard_gate,
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
    command="python -m genesis check-req-coverage --package gtl_spec.packages.genesis_sdlc:package --features .ai-workspace/features/",
)
eval_decomp_fp = Evaluator(
    "decomp_complete", F_P,
    "Construct feature vectors for all uncovered REQ keys — write one .yml per feature to "
    ".ai-workspace/features/active/ with a satisfies: list covering the assigned REQ-F-* keys. "
    "Group related keys into cohesive features. Each vector must cover at least one uncovered key.",
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

# design→module_decomp
eval_module_coverage = Evaluator(
    "module_coverage", F_D,
    "Every feature vector stem in .ai-workspace/features/ appears in ≥1 module YAML in .ai-workspace/modules/",
    command="python -c \"import pathlib,sys; fd=pathlib.Path('.ai-workspace/features/'); md=pathlib.Path('.ai-workspace/modules/'); fids={f.stem for f in fd.rglob('*.yml')} if fd.exists() else set(); mfiles=list(md.rglob('*.yml')) if md.exists() else []; content=' '.join(m.read_text() for m in mfiles); covered={fid for fid in fids if fid in content}; uncovered=fids-covered; print({'uncovered':sorted(uncovered),'passes':not bool(uncovered)}); sys.exit(0 if not uncovered and mfiles else 1)\"",
)
eval_module_schedule_fp = Evaluator(
    "module_schedule", F_P,
    "Agent: decompose design ADRs into modules — write one .yml per module to .ai-workspace/modules/ "
    "with fields: id, name, description, implements_features (list of feature IDs), "
    "dependencies (list of MOD-* ids), rank (int, 1=leaf), interfaces, source_files. "
    "Dependency DAG must be acyclic. Build order: rank=1 modules have no dependencies.",
)
eval_schedule_fh = Evaluator(
    "schedule_approved", F_H,
    "Human confirms: module boundaries are clean, dependency DAG is acyclic, "
    "build order is sensible, every feature is assigned, no circular dependencies.",
)

# module_decomp→code
eval_impl_tags = Evaluator(
    "impl_tags", F_D,
    "All source files carry at least one # Implements: REQ-* tag, zero untagged",
    command="python -m genesis check-tags --type implements --path builds/python/src/",
)
eval_code_fp = Evaluator(
    "code_complete", F_P,
    "Agent: code implements all features per design ADRs; no V2 features present; importable",
)

# code↔unit_tests
eval_tests_pass = Evaluator(
    "tests_pass", F_D,
    "pytest: zero failures, zero errors (excluding e2e tests — F_D evaluators must be acyclic)",
    command="python -m pytest builds/python/tests/ -q --tb=short -m 'not e2e'",
)
eval_test_tags = Evaluator(
    "validates_tags", F_D,
    "All test files carry at least one # Validates: REQ-* tag, zero untagged",
    command="python -m genesis check-tags --type validates --path builds/python/tests/",
)
eval_e2e_exists = Evaluator(
    "e2e_tests_exist", F_D,
    "At least one @pytest.mark.e2e test exists — e2e/integration scenarios are the primary "
    "test surface; pure unit tests are supplementary",
    command=(
        "python -c \""
        "import pathlib,sys; "
        "tests=list(pathlib.Path('builds/python/tests/').rglob('*.py')); "
        "has_e2e=any('@pytest.mark.e2e' in f.read_text() for f in tests); "
        "sys.exit(0 if has_e2e else 1)"
        "\""
    ),
)
eval_coverage_fp = Evaluator(
    "coverage_complete", F_P,
    "Agent: test suite covers all REQ keys with integration or E2E scenarios as primary evidence. "
    "Unit tests acceptable only for write-primitive invariants (emit, project, EventStream). "
    "Pure unit tests mocking internals do not satisfy coverage for workflow features.",
)

# unit_tests→uat_tests
# F_D verifier: checks that the F_P actor wrote a structured sandbox report.
# The report is created by the F_P actor during sandbox installation and e2e run.
# No genesis subcommands — reads a JSON file. Acyclicity preserved.
eval_uat_report = Evaluator(
    "uat_sandbox_report", F_D,
    "Sandbox e2e report exists at .ai-workspace/uat/sandbox_report.json with all_pass: true",
    command=(
        "python -c \""
        "import json,sys,pathlib; "
        "r=pathlib.Path('.ai-workspace/uat/sandbox_report.json'); "
        "d=json.loads(r.read_text()) if r.exists() else {}; "
        "sys.exit(0 if d.get('all_pass') and d.get('install_success') else 1)"
        "\""
    ),
)
eval_uat_fp = Evaluator(
    "uat_e2e_passed", F_P,
    "Install into a fresh sandbox: "
    "python builds/python/src/genesis_sdlc/install.py --target /tmp/uat_sandbox_{timestamp} --project-slug {slug}. "
    "Then run e2e tests in that sandbox: "
    "PYTHONPATH=.genesis python -m pytest builds/python/tests/ -m e2e -q. "
    "Write a structured report to .ai-workspace/uat/sandbox_report.json: "
    "{install_success: bool, sandbox_path: str, test_count: int, pass_count: int, fail_count: int, all_pass: bool, timestamp: ISO}. "
    "Unit tests alone do not satisfy this edge — sandbox e2e is the acceptance proof.",
)
eval_uat_fh = Evaluator(
    "uat_accepted", F_H,
    "Human confirms: (1) .ai-workspace/uat/sandbox_report.json shows all_pass: true, "
    "(2) all e2e scenarios pass end-to-end in the sandbox, "
    "(3) every feature acceptance criterion is demonstrated by at least one scenario. "
    "No feature is shipped without sandbox proof.",
)


# ── Jobs ──────────────────────────────────────────────────────────────────────

job_intent_req     = Job(e_intent_req,     [eval_intent_fh])
job_req_feat       = Job(e_req_feat,       [eval_req_coverage, eval_decomp_fp, eval_decomp_fh])
job_feat_design    = Job(e_feat_design,    [eval_design_fp, eval_design_fh])
job_design_mdecomp = Job(e_design_mdecomp, [eval_module_coverage, eval_module_schedule_fp, eval_schedule_fh])
job_mdecomp_code   = Job(e_mdecomp_code,   [eval_impl_tags, eval_code_fp])
job_tdd            = Job(e_tdd,            [eval_tests_pass, eval_test_tags, eval_e2e_exists, eval_coverage_fp])
job_uat            = Job(e_unit_uat,       [eval_uat_report, eval_uat_fp, eval_uat_fh])


# ── Worker ────────────────────────────────────────────────────────────────────

worker = Worker(
    id="claude_code",
    can_execute=[job_intent_req, job_req_feat, job_feat_design, job_design_mdecomp, job_mdecomp_code, job_tdd, job_uat],
)


# ── Package ───────────────────────────────────────────────────────────────────
# requirements list is the authoritative REQ key registry for this project.
# Add keys here as requirements are written; check-req-coverage enforces coverage.

package = Package(
    name="genesis_sdlc",
    assets=[intent, requirements, feature_decomp, design, module_decomp, code, unit_tests, uat_tests],
    edges=[e_intent_req, e_req_feat, e_feat_design, e_design_mdecomp, e_mdecomp_code, e_tdd, e_unit_uat],
    operators=[claude_agent, human_gate, pytest_op, check_impl_op, check_test_op, check_modules_op],
    rules=[standard_gate],
    contexts=[bootloader, this_spec, intent_doc, design_adrs, modules_dir],
    requirements=[
        # Bootstrap
        "REQ-F-BOOT-001",   # gen-install bootstraps .genesis/ into target project
        "REQ-F-BOOT-002",   # .genesis/genesis.yml config resolves Package/Worker
        # SDLC graph
        "REQ-F-GRAPH-001",  # GTL Package defines 7-asset SDLC graph
        "REQ-F-GRAPH-002",  # Asset.markov conditions are acceptance criteria
        # Commands
        "REQ-F-CMD-001",    # gen gaps reports delta per edge
        "REQ-F-CMD-002",    # gen iterate runs one bind-and-iterate pass
        "REQ-F-CMD-003",    # gen start --auto loops until blocked
        # Human gates
        "REQ-F-GATE-001",   # F_H evaluators gate spec/design boundaries
        # Traceability
        "REQ-F-TAG-001",    # Implements: tags enforced on all source files
        "REQ-F-TAG-002",    # Validates: tags enforced on all test files
        "REQ-F-COV-001",    # REQ key coverage enforced by check-req-coverage
        # Documentation
        "REQ-F-DOCS-001",   # User guide covers install, first session, operating loop
        # Testing philosophy
        "REQ-F-TEST-001",   # Integration and E2E tests are the primary test surface; e2e_tests_exist F_D enforces minimum
        "REQ-F-TEST-002",   # coverage_complete F_P evaluates integration coverage, not unit test count
        # UAT
        "REQ-F-UAT-001",    # unit_tests→uat_tests edge: sandbox install + e2e proof required to ship
        # Backlog
        "REQ-F-BACKLOG-001",  # .ai-workspace/backlog/BL-*.yml schema and directory convention
        "REQ-F-BACKLOG-002",  # sensory system surfaces ready items in gen gaps/status output
        "REQ-F-BACKLOG-003",  # gen backlog list — show all items with status
        "REQ-F-BACKLOG-004",  # gen backlog promote BL-xxx — emit intent_raised, mark promoted
        # Module decomposition (INT-002)
        "REQ-F-MDECOMP-001",  # design→module_decomp edge: modules decomposed from design ADRs
        "REQ-F-MDECOMP-002",  # module dependency DAG is acyclic and build order is defined (leaf-to-root)
        "REQ-F-MDECOMP-003",  # module_coverage F_D: every design feature assigned to ≥1 module
        "REQ-F-MDECOMP-004",  # F_H gate: module schedule approved before code is written
        "REQ-F-MDECOMP-005",  # module_decomp→code replaces design→code edge
        # Three-layer install architecture (ADR-005)
        "REQ-F-BOOT-003",     # installer copies released spec into .genesis/spec/ as immutable layer
        "REQ-F-BOOT-004",     # installer generates starter local spec in gtl_spec/packages/{slug}.py
        "REQ-F-BOOT-005",     # reinstall replaces .genesis/spec/ atomically; never overwrites local gtl_spec/
        # Test version sandboxing
        "REQ-F-TEST-003",     # test evaluator commands pin PYTHONPATH to builds/python/src/ — tests run against RC source, never installed version
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
