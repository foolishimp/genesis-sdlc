# Implements: REQ-F-GRAPH-001
# Implements: REQ-F-GRAPH-002
# Implements: REQ-F-TAG-001
# Implements: REQ-F-TAG-002
# Implements: REQ-F-COV-001
# Implements: REQ-F-GATE-001
# Implements: REQ-F-CMD-001
# Implements: REQ-F-CMD-002
# Implements: REQ-F-CMD-003
# Implements: REQ-F-MDECOMP-001
# Implements: REQ-F-MDECOMP-002
# Implements: REQ-F-MDECOMP-003
# Implements: REQ-F-MDECOMP-004
# Implements: REQ-F-MDECOMP-005
# Implements: REQ-F-TEST-003
# Implements: REQ-F-UAT-002
# Implements: REQ-F-UAT-003
# Implements: REQ-F-DOCS-002
# Implements: REQ-F-VAR-001
"""
Codex build of the standard SDLC bootstrap graph as a GTL Package.

This build keeps the methodology topology aligned with the current genesis_sdlc
surface while switching the concrete realization to `builds/codex`.
"""

from __future__ import annotations

from gtl.core import (
    Asset,
    Context,
    Edge,
    Evaluator,
    F_D,
    F_H,
    F_P,
    Job,
    Operator,
    Package,
    Rule,
    Worker,
    consensus,
    OPERATIVE_ON_APPROVED,
    OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)


bootloader = Context(
    name="bootloader",
    locator="workspace://.genesis/gtl_spec/GENESIS_BOOTLOADER.md",
    digest="sha256:" + "0" * 64,
)

this_spec = Context(
    name="sdlc_spec",
    locator="workspace://builds/codex/code/genesis_sdlc/sdlc_graph.py",
    digest="sha256:" + "0" * 64,
)

intent_doc = Context(
    name="intent",
    locator="workspace://specification/INTENT.md",
    digest="sha256:" + "0" * 64,
)

design_adrs = Context(
    name="design_adrs",
    locator="workspace://builds/codex/design/adrs/",
    digest="sha256:" + "0" * 64,
)

modules_dir = Context(
    name="modules_dir",
    locator="workspace://.ai-workspace/modules/",
    digest="sha256:" + "0" * 64,
)


codex_agent = Operator("codex_agent", F_P, "agent://codex/genesis")
human_gate = Operator("human_gate", F_H, "fh://single")
pytest_op = Operator(
    "pytest",
    F_D,
    "exec://python -m pytest builds/codex/tests/ -q -m 'not e2e'",
)
check_impl_op = Operator(
    "check_impl",
    F_D,
    "exec://python -m genesis check-tags --type implements --path builds/codex/code/",
)
check_test_op = Operator(
    "check_test",
    F_D,
    "exec://python -m genesis check-tags --type validates --path builds/codex/tests/",
)
check_modules_op = Operator(
    "check_modules",
    F_D,
    "exec://python -c \"import pathlib,sys; fd=pathlib.Path('.ai-workspace/features/'); md=pathlib.Path('.ai-workspace/modules/'); fids={f.stem for f in fd.rglob('*.yml')} if fd.exists() else set(); mfiles=list(md.rglob('*.yml')) if md.exists() else []; content=' '.join(m.read_text() for m in mfiles); covered={fid for fid in fids if fid in content}; uncovered=fids-covered; print({'uncovered':sorted(uncovered),'passes':not bool(uncovered)}); sys.exit(0 if not uncovered and mfiles else 1)\"",
)


standard_gate = Rule("standard_gate", approve=consensus(1, 1), dissent="recorded")


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

integration_tests = Asset(
    name="integration_tests",
    id_format="ITEST-{SEQ}",
    lineage=[unit_tests],
    markov=["sandbox_install_passes", "e2e_scenarios_pass"],
)

user_guide = Asset(
    name="user_guide",
    id_format="GUIDE-{SEQ}",
    lineage=[integration_tests],
    markov=["version_current", "req_coverage_tagged", "content_certified"],
)

uat_tests = Asset(
    name="uat_tests",
    id_format="UAT-{SEQ}",
    lineage=[user_guide],
    markov=["accepted_by_human"],
)


e_intent_req = Edge(
    name="intent→requirements",
    source=intent,
    target=requirements,
    using=[codex_agent, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec],
)

e_req_feat = Edge(
    name="requirements→feature_decomp",
    source=requirements,
    target=feature_decomp,
    using=[codex_agent, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec, intent_doc],
)

e_feat_design = Edge(
    name="feature_decomp→design",
    source=feature_decomp,
    target=design,
    using=[codex_agent, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec, intent_doc],
)

e_design_mdecomp = Edge(
    name="design→module_decomp",
    source=design,
    target=module_decomp,
    using=[codex_agent, check_modules_op, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec, design_adrs],
)

e_mdecomp_code = Edge(
    name="module_decomp→code",
    source=module_decomp,
    target=code,
    using=[codex_agent, check_impl_op],
    context=[bootloader, this_spec, design_adrs, modules_dir],
)

e_tdd = Edge(
    name="code↔unit_tests",
    source=[code, unit_tests],
    target=unit_tests,
    co_evolve=True,
    using=[codex_agent, pytest_op, check_impl_op, check_test_op],
    context=[bootloader, this_spec, design_adrs],
)

e_unit_itest = Edge(
    name="unit_tests→integration_tests",
    source=unit_tests,
    target=integration_tests,
    using=[codex_agent],
    context=[bootloader, this_spec],
)

e_itest_guide = Edge(
    name="integration_tests→user_guide",
    source=integration_tests,
    target=user_guide,
    using=[codex_agent, human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec],
)

e_guide_uat = Edge(
    name="user_guide→uat_tests",
    source=user_guide,
    target=uat_tests,
    using=[human_gate],
    rule=standard_gate,
    context=[bootloader, this_spec],
)


eval_intent_fh = Evaluator(
    "intent_approved",
    F_H,
    "Human confirms: problem stated, value proposition clear, scope bounded",
)

eval_req_coverage = Evaluator(
    "req_coverage",
    F_D,
    "Every REQ key in Package.requirements appears in ≥1 feature vector",
    command="python -m genesis check-req-coverage --package genesis_sdlc.sdlc_graph:package --features .ai-workspace/features/",
)
eval_decomp_fp = Evaluator(
    "decomp_complete",
    F_P,
    "Construct feature vectors for all uncovered REQ keys — write one .yml per feature to .ai-workspace/features/active/ with a satisfies: list covering the assigned REQ-F-* keys.",
)
eval_decomp_fh = Evaluator(
    "decomp_approved",
    F_H,
    "Human approves: feature set complete, dependency order correct, MVP boundary clear",
)

eval_design_fp = Evaluator(
    "design_coherent",
    F_P,
    "Agent: ADRs cover all features, tech stack decided, interfaces specified",
)
eval_design_fh = Evaluator(
    "design_approved",
    F_H,
    "Human approves design before code is written",
)

eval_module_coverage = Evaluator(
    "module_coverage",
    F_D,
    "Every feature vector stem in .ai-workspace/features/ appears in ≥1 module YAML in .ai-workspace/modules/",
    command="python -c \"import pathlib,sys; fd=pathlib.Path('.ai-workspace/features/'); md=pathlib.Path('.ai-workspace/modules/'); fids={f.stem for f in fd.rglob('*.yml')} if fd.exists() else set(); mfiles=list(md.rglob('*.yml')) if md.exists() else []; content=' '.join(m.read_text() for m in mfiles); covered={fid for fid in fids if fid in content}; uncovered=fids-covered; print({'uncovered':sorted(uncovered),'passes':not bool(uncovered)}); sys.exit(0 if not uncovered and mfiles else 1)\"",
)
eval_module_schedule_fp = Evaluator(
    "module_schedule",
    F_P,
    "Agent: decompose design ADRs into modules — write one .yml per module to .ai-workspace/modules/ with id, name, description, implements_features, dependencies, rank, interfaces, source_files.",
)
eval_schedule_fh = Evaluator(
    "schedule_approved",
    F_H,
    "Human confirms: module boundaries are clean, dependency DAG is acyclic, build order is sensible, every feature is assigned.",
)

eval_impl_tags = Evaluator(
    "impl_tags",
    F_D,
    "All source files carry # Implements: REQ-* tags, zero untagged",
    command="python -m genesis check-tags --type implements --path builds/codex/code/",
)
eval_code_fp = Evaluator(
    "code_complete",
    F_P,
    "Agent: code implements all features per design ADRs, importable, no V2 features",
)

eval_tests_pass = Evaluator(
    "tests_pass",
    F_D,
    "pytest: zero failures, zero errors (excluding e2e tests — F_D evaluators must be acyclic)",
    command="python -m pytest builds/codex/tests/ -q --tb=short -m 'not e2e'",
)
eval_test_tags = Evaluator(
    "validates_tags",
    F_D,
    "All test files carry # Validates: REQ-* tags, zero untagged",
    command="python -m genesis check-tags --type validates --path builds/codex/tests/",
)
eval_e2e_exists = Evaluator(
    "e2e_tests_exist",
    F_D,
    "At least one @pytest.mark.e2e test exists — e2e/integration scenarios are the primary test surface",
    command="python -c \"import pathlib,sys; tests=list(pathlib.Path('builds/codex/tests/').rglob('*.py')); has_e2e=any('@pytest.mark.e2e' in f.read_text() for f in tests); sys.exit(0 if has_e2e else 1)\"",
)
eval_coverage_fp = Evaluator(
    "coverage_complete",
    F_P,
    "Agent: tests cover all features, no REQ key without a test",
)

eval_sandbox_report = Evaluator(
    "sandbox_report_exists",
    F_D,
    "Sandbox e2e report exists at .ai-workspace/uat/sandbox_report.json with all_pass: true",
    command="python -c \"import json,sys,pathlib; r=pathlib.Path('.ai-workspace/uat/sandbox_report.json'); d=json.loads(r.read_text()) if r.exists() else {}; sys.exit(0 if d.get('all_pass') and d.get('install_success') else 1)\"",
)
eval_sandbox_run = Evaluator(
    "sandbox_e2e_passed",
    F_P,
    "Install into a fresh sandbox with python builds/codex/code/genesis_sdlc/install.py --target /tmp/uat_sandbox_{timestamp} --project-slug {slug}. Then run e2e tests in that sandbox and write .ai-workspace/uat/sandbox_report.json.",
)

eval_guide_version = Evaluator(
    "guide_version_current",
    F_D,
    "USER_GUIDE.md **Version**: field matches the active workflow version in .genesis/active-workflow.json",
    command="python -c \"import json,sys,pathlib; guide=pathlib.Path('docs/USER_GUIDE.md'); active=pathlib.Path('.genesis/active-workflow.json'); text=guide.read_text() if guide.exists() else ''; version=json.loads(active.read_text()).get('version') if active.exists() else ''; sys.exit(0 if version and ('**Version**: '+version) in text else 1)\"",
)
eval_guide_coverage = Evaluator(
    "guide_req_coverage",
    F_D,
    "USER_GUIDE.md <!-- Covers: --> tags include every key in package.requirements",
    command="python -c \"import importlib,re,sys,pathlib; guide=pathlib.Path('docs/USER_GUIDE.md'); text=guide.read_text() if guide.exists() else ''; covered=set(r for t in re.findall(r'<!-- Covers:([^>]+)-->', text) for r in re.findall(r'REQ-F-[A-Z0-9-]+', t)); pkg=importlib.import_module('genesis_sdlc.sdlc_graph').package; missing=sorted(set(pkg.requirements)-covered); print('uncovered:', missing) if missing else None; sys.exit(len(missing))\"",
)
eval_guide_content = Evaluator(
    "guide_content_certified",
    F_P,
    "Agent: verify USER_GUIDE.md coherently answers install steps, first session, commands, operating loop, and recovery paths.",
)

eval_uat_fh = Evaluator(
    "uat_accepted",
    F_H,
    "Human confirms sandbox proof is present, USER_GUIDE.md is coherent, and operator-facing features are documented.",
)


job_intent_req = Job(e_intent_req, [eval_intent_fh])
job_req_feat = Job(e_req_feat, [eval_req_coverage, eval_decomp_fp, eval_decomp_fh])
job_feat_design = Job(e_feat_design, [eval_design_fp, eval_design_fh])
job_design_mdecomp = Job(
    e_design_mdecomp,
    [eval_module_coverage, eval_module_schedule_fp, eval_schedule_fh],
)
job_mdecomp_code = Job(e_mdecomp_code, [eval_impl_tags, eval_code_fp])
job_tdd = Job(e_tdd, [eval_tests_pass, eval_test_tags, eval_e2e_exists, eval_coverage_fp])
job_unit_itest = Job(e_unit_itest, [eval_sandbox_report, eval_sandbox_run])
job_itest_guide = Job(
    e_itest_guide,
    [eval_guide_version, eval_guide_coverage, eval_guide_content],
)
job_guide_uat = Job(e_guide_uat, [eval_uat_fh])


worker = Worker(
    id="codex",
    can_execute=[
        job_intent_req,
        job_req_feat,
        job_feat_design,
        job_design_mdecomp,
        job_mdecomp_code,
        job_tdd,
        job_unit_itest,
        job_itest_guide,
        job_guide_uat,
    ],
)

package = Package(
    name="genesis_sdlc",
    assets=[
        intent,
        requirements,
        feature_decomp,
        design,
        module_decomp,
        code,
        unit_tests,
        integration_tests,
        user_guide,
        uat_tests,
    ],
    edges=[
        e_intent_req,
        e_req_feat,
        e_feat_design,
        e_design_mdecomp,
        e_mdecomp_code,
        e_tdd,
        e_unit_itest,
        e_itest_guide,
        e_guide_uat,
    ],
    operators=[codex_agent, human_gate, pytest_op, check_impl_op, check_test_op, check_modules_op],
    rules=[standard_gate],
    contexts=[bootloader, this_spec, intent_doc, design_adrs, modules_dir],
    requirements=[
        "REQ-F-BOOT-001",
        "REQ-F-BOOT-002",
        "REQ-F-BOOT-003",
        "REQ-F-BOOT-004",
        "REQ-F-BOOT-005",
        "REQ-F-BOOT-006",
        "REQ-F-GRAPH-001",
        "REQ-F-GRAPH-002",
        "REQ-F-CMD-001",
        "REQ-F-CMD-002",
        "REQ-F-CMD-003",
        "REQ-F-GATE-001",
        "REQ-F-TAG-001",
        "REQ-F-TAG-002",
        "REQ-F-COV-001",
        "REQ-F-DOCS-001",
        "REQ-F-DOCS-002",
        "REQ-F-TEST-001",
        "REQ-F-TEST-002",
        "REQ-F-TEST-003",
        "REQ-F-UAT-001",
        "REQ-F-UAT-002",
        "REQ-F-UAT-003",
        "REQ-F-BACKLOG-001",
        "REQ-F-BACKLOG-002",
        "REQ-F-BACKLOG-003",
        "REQ-F-BACKLOG-004",
        "REQ-F-MDECOMP-001",
        "REQ-F-MDECOMP-002",
        "REQ-F-MDECOMP-003",
        "REQ-F-MDECOMP-004",
        "REQ-F-MDECOMP-005",
        "REQ-F-VAR-001",
    ],
)


def _clone_edge(edge: Edge, *, replacement_spec: Context) -> Edge:
    contexts = [
        replacement_spec if ctx.name == "sdlc_spec" else ctx
        for ctx in edge.context
    ]
    return Edge(
        name=edge.name,
        source=edge.source,
        target=edge.target,
        using=list(edge.using),
        rule=edge.rule,
        context=contexts,
        co_evolve=edge.co_evolve,
    )


def instantiate(slug: str):
    """
    Return (package, worker) customised for the given project slug.

    Overrides the package-bound evaluator imports and rewrites every edge context
    that refers to the source graph so the installed workflow binds against the
    generated Layer 3 wrapper instead of the authoring source file.
    """

    installed_spec = Context(
        name="sdlc_spec",
        locator=f"workspace://.genesis/gtl_spec/packages/{slug}.py",
        digest="sha256:" + "0" * 64,
    )

    installed_edges = {
        edge.name: _clone_edge(edge, replacement_spec=installed_spec)
        for edge in package.edges
    }

    installed_req_coverage = Evaluator(
        "req_coverage",
        F_D,
        "Every REQ key in Package.requirements appears in ≥1 feature vector",
        command=(
            "python -m genesis check-req-coverage "
            f"--package gtl_spec.packages.{slug}:package "
            "--features .ai-workspace/features/"
        ),
    )
    installed_guide_coverage = Evaluator(
        "guide_req_coverage",
        F_D,
        "USER_GUIDE.md <!-- Covers: --> tags include every key in package.requirements",
        command=(
            "python -c "
            "\"import importlib,re,sys,pathlib; "
            "guide=pathlib.Path('docs/USER_GUIDE.md'); "
            "text=guide.read_text() if guide.exists() else ''; "
            "covered=set(r for t in re.findall(r'<!-- Covers:([^>]+)-->', text) "
            "for r in re.findall(r'REQ-F-[A-Z0-9-]+', t)); "
            f"pkg=importlib.import_module('gtl_spec.packages.{slug}').package; "
            "missing=sorted(set(pkg.requirements)-covered); "
            "print('uncovered:', missing) if missing else None; "
            "sys.exit(len(missing))\""
        ),
    )

    installed_jobs = [
        Job(installed_edges["intent→requirements"], [eval_intent_fh]),
        Job(
            installed_edges["requirements→feature_decomp"],
            [installed_req_coverage, eval_decomp_fp, eval_decomp_fh],
        ),
        Job(installed_edges["feature_decomp→design"], [eval_design_fp, eval_design_fh]),
        Job(
            installed_edges["design→module_decomp"],
            [eval_module_coverage, eval_module_schedule_fp, eval_schedule_fh],
        ),
        Job(installed_edges["module_decomp→code"], [eval_impl_tags, eval_code_fp]),
        Job(
            installed_edges["code↔unit_tests"],
            [eval_tests_pass, eval_test_tags, eval_e2e_exists, eval_coverage_fp],
        ),
        Job(
            installed_edges["unit_tests→integration_tests"],
            [eval_sandbox_report, eval_sandbox_run],
        ),
        Job(
            installed_edges["integration_tests→user_guide"],
            [eval_guide_version, installed_guide_coverage, eval_guide_content],
        ),
        Job(installed_edges["user_guide→uat_tests"], [eval_uat_fh]),
    ]

    installed_package = Package(
        name=slug,
        assets=list(package.assets),
        edges=list(installed_edges.values()),
        operators=list(package.operators),
        rules=list(package.rules),
        contexts=[
            installed_spec if ctx.name == "sdlc_spec" else ctx
            for ctx in package.contexts
        ],
        requirements=list(package.requirements),
    )
    installed_worker = Worker(id=worker.id, can_execute=installed_jobs)
    return installed_package, installed_worker
