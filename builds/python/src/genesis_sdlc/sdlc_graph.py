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
sdlc_graph — standard SDLC bootstrap graph as a GTL Package.

Exports `package` and `worker` — the pre-built, standard SDLC graph
covering the bootstrap path:

    intent → requirements → feature_decomp → design → module_decomp → code ↔ unit_tests
        → integration_tests → user_guide → uat_tests

module_decomp sits between design and code: decomposes design ADRs into a ranked
module dependency graph (leaf-to-root build order) before any code is written.

integration_tests and user_guide are first-class blocking assets (INT-003):
- integration_tests: sandbox install + e2e run; F_D checks structured report
- user_guide: version tag + REQ coverage tag F_D checks; content F_P certifies
- uat_tests: pure F_H gate — human approves once sandbox proof and guide are current

F_D evaluators must be acyclic — never invoke genesis subcommands from pytest.

Import as a starting point:

    from genesis_sdlc.sdlc_graph import package, worker

Or reference via .genesis/genesis.yml:

    package: genesis_sdlc.sdlc_graph:package
    worker:  genesis_sdlc.sdlc_graph:worker

Evaluator commands assume the standard layout: builds/python/src/ and builds/python/tests/. Override for other platforms.
"""
from gtl.core import (
    Package, Asset, Edge, Operator, Rule, Context, Evaluator, Job, Worker,
    F_D, F_P, F_H, consensus,
    OPERATIVE_ON_APPROVED, OPERATIVE_ON_APPROVED_NOT_SUPERSEDED,
)


# ── Contexts ──────────────────────────────────────────────────────────────────

gtl_bootloader = Context(
    name="gtl_bootloader",
    locator="workspace://.genesis/gtl_spec/GTL_BOOTLOADER.md",
    digest="sha256:" + "0" * 64,
)

sdlc_bootloader = Context(
    name="sdlc_bootloader",
    locator="workspace://.gsdlc/release/SDLC_BOOTLOADER.md",
    digest="sha256:" + "0" * 64,
)

this_spec = Context(
    name="sdlc_spec",
    locator="workspace://builds/python/src/genesis_sdlc/sdlc_graph.py",
    digest="sha256:" + "0" * 64,
)

intent_doc = Context(
    name="intent",
    locator="workspace://specification/INTENT.md",
    digest="sha256:" + "0" * 64,
)

design_adrs = Context(
    name="design_adrs",
    locator="workspace://builds/python/design/adrs/",
    digest="sha256:" + "0" * 64,
)

modules_dir = Context(
    name="modules_dir",
    locator="workspace://.ai-workspace/modules/",
    digest="sha256:" + "0" * 64,
)


# ── Operators ─────────────────────────────────────────────────────────────────

claude_agent      = Operator("claude_agent",      F_P, "agent://claude/genesis")
human_gate        = Operator("human_gate",        F_H, "fh://single")
pytest_op         = Operator("pytest",            F_D, "exec://python -m pytest builds/python/tests/ -q -m 'not e2e'")
check_impl_op     = Operator("check_impl",        F_D, "exec://python -m genesis check-tags --type implements --path builds/python/src/")
check_test_op     = Operator("check_test",        F_D, "exec://python -m genesis check-tags --type validates --path builds/python/tests/")
check_modules_op  = Operator("check_modules",     F_D, "exec://python -c \"import pathlib,sys; fd=pathlib.Path('.ai-workspace/features/'); md=pathlib.Path('.ai-workspace/modules/'); fids={f.stem for f in fd.rglob('*.yml')} if fd.exists() else set(); mfiles=list(md.rglob('*.yml')) if md.exists() else []; content=' '.join(m.read_text() for m in mfiles); covered={fid for fid in fids if fid in content}; uncovered=fids-covered; print({'uncovered':sorted(uncovered),'passes':not bool(uncovered)}); sys.exit(0 if not uncovered and mfiles else 1)\"")


# ── Rules ─────────────────────────────────────────────────────────────────────

standard_gate = Rule("standard_gate", approve=consensus(1, 1), dissent="recorded")


# ── Assets ────────────────────────────────────────────────────────────────────

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


# ── Edges ─────────────────────────────────────────────────────────────────────

e_intent_req = Edge(
    name="intent→requirements",
    source=intent, target=requirements,
    using=[claude_agent, human_gate],
    rule=standard_gate,
    context=[gtl_bootloader, sdlc_bootloader, this_spec],
)

e_req_feat = Edge(
    name="requirements→feature_decomp",
    source=requirements, target=feature_decomp,
    using=[claude_agent, human_gate],
    rule=standard_gate,
    context=[gtl_bootloader, sdlc_bootloader, this_spec, intent_doc],
)

e_feat_design = Edge(
    name="feature_decomp→design",
    source=feature_decomp, target=design,
    using=[claude_agent, human_gate],
    rule=standard_gate,
    context=[gtl_bootloader, sdlc_bootloader, this_spec, intent_doc],
)

e_design_mdecomp = Edge(
    name="design→module_decomp",
    source=design, target=module_decomp,
    using=[claude_agent, check_modules_op, human_gate],
    rule=standard_gate,
    context=[gtl_bootloader, sdlc_bootloader, this_spec, design_adrs],
)

e_mdecomp_code = Edge(
    name="module_decomp→code",
    source=module_decomp, target=code,
    using=[claude_agent, check_impl_op],
    context=[gtl_bootloader, sdlc_bootloader, this_spec, design_adrs, modules_dir],
)

e_tdd = Edge(
    name="code↔unit_tests",
    source=[code, unit_tests], target=unit_tests,
    co_evolve=True,
    using=[claude_agent, pytest_op, check_impl_op, check_test_op],
    context=[gtl_bootloader, sdlc_bootloader, this_spec, design_adrs],
)

e_unit_itest = Edge(
    name="unit_tests→integration_tests",
    source=unit_tests, target=integration_tests,
    using=[claude_agent],
    context=[gtl_bootloader, sdlc_bootloader, this_spec],
)

e_itest_guide = Edge(
    name="integration_tests→user_guide",
    source=integration_tests, target=user_guide,
    using=[claude_agent, human_gate],
    rule=standard_gate,
    context=[gtl_bootloader, sdlc_bootloader, this_spec],
)

e_guide_uat = Edge(
    name="user_guide→uat_tests",
    source=user_guide, target=uat_tests,
    using=[human_gate],
    rule=standard_gate,
    context=[gtl_bootloader, sdlc_bootloader, this_spec],
)


# ── Evaluators ────────────────────────────────────────────────────────────────

eval_intent_fh = Evaluator(
    "intent_approved", F_H,
    "Human confirms: problem stated, value proposition clear, scope bounded",
)

eval_req_coverage = Evaluator(
    "req_coverage", F_D,
    "Every REQ key in Package.requirements appears in ≥1 feature vector",
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
    "Human approves: feature set complete, dependency order correct, MVP boundary clear",
)

eval_design_fp = Evaluator(
    "design_coherent", F_P,
    "Agent: ADRs cover all features, tech stack decided, interfaces specified",
)
eval_design_fh = Evaluator(
    "design_approved", F_H,
    "Human approves design before code is written",
)

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

eval_impl_tags = Evaluator(
    "impl_tags", F_D,
    "All source files carry # Implements: REQ-* tags, zero untagged",
    command="python -m genesis check-tags --type implements --path builds/python/src/",
)
eval_code_fp = Evaluator(
    "code_complete", F_P,
    "Agent: code implements all features per design ADRs, importable, no V2 features",
)

# F_D evaluators must NOT invoke genesis commands (acyclicity constraint).
# Use -m 'not e2e' to exclude tests that may invoke genesis subcommands.
eval_tests_pass = Evaluator(
    "tests_pass", F_D,
    "pytest: zero failures, zero errors (excluding e2e tests — F_D evaluators must be acyclic)",
    command="PYTHONPATH=builds/python/src/:.gsdlc/release:.genesis python -m pytest builds/python/tests/ -q --tb=short -m 'not e2e'",
)
eval_test_tags = Evaluator(
    "validates_tags", F_D,
    "All test files carry # Validates: REQ-* tags, zero untagged",
    command="python -m genesis check-tags --type validates --path builds/python/tests/",
)
eval_e2e_exists = Evaluator(
    "e2e_tests_exist", F_D,
    "At least one @pytest.mark.e2e test exists — e2e/integration scenarios are the primary "
    "test surface; pure unit tests are supplementary",
    command=(
        "PYTHONPATH=builds/python/src/:.gsdlc/release:.genesis python -c \""
        "import pathlib,sys; "
        "tests=list(pathlib.Path('builds/python/tests/').rglob('*.py')); "
        "has_e2e=any('@pytest.mark.e2e' in f.read_text() for f in tests); "
        "sys.exit(0 if has_e2e else 1)"
        "\""
    ),
)
eval_coverage_fp = Evaluator(
    "coverage_complete", F_P,
    "Agent: tests cover all features, no REQ key without a test",
)

# unit_tests→integration_tests: sandbox e2e is the acceptance proof.
# F_D checks the structured report written by F_P actor.
eval_sandbox_report = Evaluator(
    "sandbox_report_exists", F_D,
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
eval_sandbox_run = Evaluator(
    "sandbox_e2e_passed", F_P,
    "Install into a fresh sandbox: "
    "python builds/python/src/genesis_sdlc/install.py --target /tmp/uat_sandbox_{timestamp} --project-slug {slug}. "
    "Then run e2e tests in that sandbox: "
    "PYTHONPATH=.gsdlc/release:.genesis python -m pytest builds/python/tests/ -m e2e -q. "
    "Write a structured report to .ai-workspace/uat/sandbox_report.json: "
    "{install_success: bool, sandbox_path: str, test_count: int, pass_count: int, fail_count: int, all_pass: bool, timestamp: ISO}. "
    "Unit tests alone do not satisfy this edge — sandbox e2e is the acceptance proof.",
)

# integration_tests→user_guide: version currency and REQ coverage are deterministic.
eval_guide_version = Evaluator(
    "guide_version_current", F_D,
    "USER_GUIDE.md **Version**: field matches current release version in builds/python/src/genesis_sdlc/install.py",
    command=(
        "python -c \""
        "import re,sys,pathlib; "
        "guide=pathlib.Path('docs/USER_GUIDE.md').read_text(); "
        "install=pathlib.Path('builds/python/src/genesis_sdlc/install.py').read_text(); "
        "ver=re.search(r'VERSION = .([0-9][0-9.]+).', install).group(1); "
        "sys.exit(0 if ('**Version**: '+ver) in guide else 1)"
        "\""
    ),
)
eval_guide_coverage = Evaluator(
    "guide_req_coverage", F_D,
    "USER_GUIDE.md <!-- Covers: --> tags include every key in package.requirements",
    command=(
        "PYTHONPATH=builds/python/src:.gsdlc/release:.genesis python -c \""
        "import re,sys,pathlib,importlib; "
        "guide=pathlib.Path('docs/USER_GUIDE.md').read_text(); "
        "covered=set(r for t in re.findall(r'<!-- Covers:([^>]+)-->', guide) "
        "for r in re.findall(r'REQ-F-[A-Z0-9-]+', t)); "
        "pkg=importlib.import_module('genesis_sdlc.sdlc_graph').package; "
        "missing=sorted(set(pkg.requirements)-covered); "
        "print('uncovered:', missing) if missing else None; "
        "sys.exit(len(missing))\""
    ),
)
eval_guide_content = Evaluator(
    "guide_content_certified", F_P,
    "Agent: verify USER_GUIDE.md coherently answers: install steps, first session, "
    "gen-start/gen-gaps/gen-iterate commands, operating loop, and recovery paths. "
    "Version string must match current release. REQ-F-* coverage tags must be present.",
)

# user_guide→uat_tests: pure F_H gate.
eval_uat_fh = Evaluator(
    "uat_accepted", F_H,
    "Human confirms: (1) sandbox_report.json shows all_pass: true, "
    "(2) USER_GUIDE.md is coherent and version-current, "
    "(3) every operator-facing feature is documented. "
    "No release ships without sandbox proof and a current guide.",
)


# ── Jobs ──────────────────────────────────────────────────────────────────────

job_intent_req    = Job(e_intent_req,    [eval_intent_fh])
job_req_feat      = Job(e_req_feat,      [eval_req_coverage, eval_decomp_fp, eval_decomp_fh])
job_feat_design   = Job(e_feat_design,   [eval_design_fp, eval_design_fh])
job_design_mdecomp = Job(e_design_mdecomp, [eval_module_coverage, eval_module_schedule_fp, eval_schedule_fh])
job_mdecomp_code  = Job(e_mdecomp_code,  [eval_impl_tags, eval_code_fp])
job_tdd           = Job(e_tdd,           [eval_tests_pass, eval_test_tags, eval_e2e_exists, eval_coverage_fp])
job_unit_itest    = Job(e_unit_itest,    [eval_sandbox_report, eval_sandbox_run])
job_itest_guide   = Job(e_itest_guide,   [eval_guide_version, eval_guide_coverage, eval_guide_content])
job_guide_uat     = Job(e_guide_uat,     [eval_uat_fh])


# ── Worker + Package ──────────────────────────────────────────────────────────

worker = Worker(
    id="claude_code",
    can_execute=[job_intent_req, job_req_feat, job_feat_design, job_design_mdecomp, job_mdecomp_code, job_tdd, job_unit_itest, job_itest_guide, job_guide_uat],
)

package = Package(
    name="genesis_sdlc",
    assets=[intent, requirements, feature_decomp, design, module_decomp, code, unit_tests, integration_tests, user_guide, uat_tests],
    edges=[e_intent_req, e_req_feat, e_feat_design, e_design_mdecomp, e_mdecomp_code, e_tdd, e_unit_itest, e_itest_guide, e_guide_uat],
    operators=[claude_agent, human_gate, pytest_op, check_impl_op, check_test_op, check_modules_op],
    rules=[standard_gate],
    contexts=[gtl_bootloader, sdlc_bootloader, this_spec, intent_doc, design_adrs, modules_dir],
    requirements=[
        "REQ-F-BOOT-001", "REQ-F-BOOT-002",
        "REQ-F-BOOT-003", "REQ-F-BOOT-004", "REQ-F-BOOT-005", "REQ-F-BOOT-006",
        "REQ-F-GRAPH-001", "REQ-F-GRAPH-002",
        "REQ-F-CMD-001", "REQ-F-CMD-002", "REQ-F-CMD-003",
        "REQ-F-GATE-001",
        "REQ-F-TAG-001", "REQ-F-TAG-002",
        "REQ-F-COV-001",
        "REQ-F-DOCS-001", "REQ-F-DOCS-002",
        "REQ-F-TEST-001", "REQ-F-TEST-002", "REQ-F-TEST-003",
        "REQ-F-UAT-001", "REQ-F-UAT-002", "REQ-F-UAT-003",
        "REQ-F-BACKLOG-001", "REQ-F-BACKLOG-002", "REQ-F-BACKLOG-003", "REQ-F-BACKLOG-004",
        "REQ-F-MDECOMP-001", "REQ-F-MDECOMP-002", "REQ-F-MDECOMP-003",
        "REQ-F-MDECOMP-004", "REQ-F-MDECOMP-005",
        "REQ-F-VAR-001",
        "REQ-F-CUSTODY-001", "REQ-F-CUSTODY-002", "REQ-F-CUSTODY-003",
        "REQ-F-TERRITORY-001", "REQ-F-TERRITORY-002",
    ],
)


# ── instantiate ───────────────────────────────────────────────────────────────

def instantiate(slug: str, req_keys=None, *,
                platform: str = "python", src_dir: str = "src"):
    """
    Return (package, worker) customised for the given project.

    Parameterizes all build paths so the SDLC graph works correctly for
    any project layout (e.g. builds/python/src/ vs builds/claude_code/code/).

    Args:
        slug: Project identifier used for import paths and config resolution.
        req_keys: Optional list of REQ-* keys for this project. When provided,
            these replace the workflow's hardcoded keys. When None, defaults to
            empty list — the workflow's keys are gsdlc's requirements, not the
            project's.  # Implements: REQ-F-CUSTODY-001
        platform: Build platform directory name (default: "python").
        src_dir: Source subdirectory name (default: "src"). Use "code" for ABG.
    """
    src_path = f"builds/{platform}/{src_dir}"
    test_path = f"builds/{platform}/tests"
    adr_path = f"builds/{platform}/design/adrs"

    # ── Contexts (parameterized) ─────────────────────────────────────────────
    _this_spec = Context(
        name="sdlc_spec",
        locator=f"workspace://.gsdlc/release/gtl_spec/packages/{slug}.py",
        digest="sha256:" + "0" * 64,
    )
    _design_adrs = Context(
        name="design_adrs",
        locator=f"workspace://{adr_path}/",
        digest="sha256:" + "0" * 64,
    )

    # ── Operators (parameterized) ────────────────────────────────────────────
    _pytest_op = Operator(
        "pytest", F_D,
        f"exec://python -m pytest {test_path}/ -q -m 'not e2e'",
    )
    _check_impl_op = Operator(
        "check_impl", F_D,
        f"exec://python -m genesis check-tags --type implements --path {src_path}/",
    )
    _check_test_op = Operator(
        "check_test", F_D,
        f"exec://python -m genesis check-tags --type validates --path {test_path}/",
    )

    # ── Evaluators (parameterized) ───────────────────────────────────────────
    _eval_req_coverage = Evaluator(
        "req_coverage", F_D,
        "Every REQ key in Package.requirements appears in ≥1 feature vector",
        command=(
            f"python -m genesis check-req-coverage "
            f"--package gtl_spec.packages.{slug}:package "
            f"--features .ai-workspace/features/"
        ),
    )
    _eval_impl_tags = Evaluator(
        "impl_tags", F_D,
        "All source files carry # Implements: REQ-* tags, zero untagged",
        command=f"python -m genesis check-tags --type implements --path {src_path}/",
    )
    _eval_tests_pass = Evaluator(
        "tests_pass", F_D,
        "pytest: zero failures, zero errors (excluding e2e tests — F_D evaluators must be acyclic)",
        command=f"PYTHONPATH={src_path}/:.gsdlc/release:.genesis python -m pytest {test_path}/ -q --tb=short -m 'not e2e'",
    )
    _eval_test_tags = Evaluator(
        "validates_tags", F_D,
        "All test files carry # Validates: REQ-* tags, zero untagged",
        command=f"python -m genesis check-tags --type validates --path {test_path}/",
    )
    _eval_e2e_exists = Evaluator(
        "e2e_tests_exist", F_D,
        "At least one @pytest.mark.e2e test exists — e2e/integration scenarios are the primary "
        "test surface; pure unit tests are supplementary",
        command=(
            f"PYTHONPATH={src_path}/:.gsdlc/release:.genesis python -c \""
            f"import pathlib,sys; "
            f"tests=list(pathlib.Path('{test_path}/').rglob('*.py')); "
            f"has_e2e=any('@pytest.mark.e2e' in f.read_text() for f in tests); "
            f"sys.exit(0 if has_e2e else 1)"
            f"\""
        ),
    )
    _eval_sandbox_run = Evaluator(
        "sandbox_e2e_passed", F_P,
        f"Install into a fresh sandbox: "
        f"PYTHONPATH={src_path}/:.gsdlc/release:.genesis python -m genesis_sdlc.install "
        f"--target /tmp/uat_sandbox_{{timestamp}} --project-slug {slug}. "
        f"Then run e2e tests in that sandbox: "
        f"PYTHONPATH=.gsdlc/release:.genesis python -m pytest {test_path}/ -m e2e -q. "
        f"Write a structured report to .ai-workspace/uat/sandbox_report.json: "
        f"{{install_success: bool, sandbox_path: str, test_count: int, pass_count: int, "
        f"fail_count: int, all_pass: bool, timestamp: ISO}}. "
        f"Unit tests alone do not satisfy this edge — sandbox e2e is the acceptance proof.",
    )
    _eval_guide_version = Evaluator(
        "guide_version_current", F_D,
        "USER_GUIDE.md **Version**: field matches current release version in .gsdlc/release/active-workflow.json",
        command=(
            "python -c \""
            "import json,re,sys,pathlib; "
            "guide=pathlib.Path('docs/USER_GUIDE.md').read_text(); "
            "ver=json.loads(pathlib.Path('.gsdlc/release/active-workflow.json').read_text())['version']; "
            "sys.exit(0 if ('**Version**: '+ver) in guide else 1)"
            "\""
        ),
    )
    _eval_guide_coverage = Evaluator(
        "guide_req_coverage", F_D,
        "USER_GUIDE.md <!-- Covers: --> tags include every key in package.requirements",
        command=(
            f"PYTHONPATH=.gsdlc/release:.genesis python -c \""
            f"import re,sys,pathlib,importlib; "
            f"guide=pathlib.Path('docs/USER_GUIDE.md').read_text(); "
            f"covered=set(r for t in re.findall(r'<!-- Covers:([^>]+)-->', guide) "
            f"for r in re.findall(r'REQ-F-[A-Z0-9-]+', t)); "
            f"pkg=importlib.import_module('gtl_spec.packages.{slug}').package; "
            f"missing=sorted(set(pkg.requirements)-covered); "
            f"print('uncovered:', missing) if missing else None; "
            f"sys.exit(len(missing))\""
        ),
    )

    # ── Edges (rebuild those using parameterized operators/contexts) ──────────
    _e_design_mdecomp = Edge(
        name="design→module_decomp",
        source=design, target=module_decomp,
        using=[claude_agent, check_modules_op, human_gate],
        rule=standard_gate,
        context=[gtl_bootloader, sdlc_bootloader, _this_spec, _design_adrs],
    )
    _e_mdecomp_code = Edge(
        name="module_decomp→code",
        source=module_decomp, target=code,
        using=[claude_agent, _check_impl_op],
        context=[gtl_bootloader, sdlc_bootloader, _this_spec, _design_adrs, modules_dir],
    )
    _e_tdd = Edge(
        name="code↔unit_tests",
        source=[code, unit_tests], target=unit_tests,
        co_evolve=True,
        using=[claude_agent, _pytest_op, _check_impl_op, _check_test_op],
        context=[gtl_bootloader, sdlc_bootloader, _this_spec, _design_adrs],
    )

    # Upstream edges use only generic contexts — rebind spec context only
    _e_intent_req = Edge(
        name="intent→requirements",
        source=intent, target=requirements,
        using=[claude_agent, human_gate],
        rule=standard_gate,
        context=[gtl_bootloader, sdlc_bootloader, _this_spec],
    )
    _e_req_feat = Edge(
        name="requirements→feature_decomp",
        source=requirements, target=feature_decomp,
        using=[claude_agent, human_gate],
        rule=standard_gate,
        context=[gtl_bootloader, sdlc_bootloader, _this_spec, intent_doc],
    )
    _e_feat_design = Edge(
        name="feature_decomp→design",
        source=feature_decomp, target=design,
        using=[claude_agent, human_gate],
        rule=standard_gate,
        context=[gtl_bootloader, sdlc_bootloader, _this_spec, intent_doc],
    )
    _e_unit_itest = Edge(
        name="unit_tests→integration_tests",
        source=unit_tests, target=integration_tests,
        using=[claude_agent],
        context=[gtl_bootloader, sdlc_bootloader, _this_spec],
    )
    _e_itest_guide = Edge(
        name="integration_tests→user_guide",
        source=integration_tests, target=user_guide,
        using=[claude_agent, human_gate],
        rule=standard_gate,
        context=[gtl_bootloader, sdlc_bootloader, _this_spec],
    )
    _e_guide_uat = Edge(
        name="user_guide→uat_tests",
        source=user_guide, target=uat_tests,
        using=[human_gate],
        rule=standard_gate,
        context=[gtl_bootloader, sdlc_bootloader, _this_spec],
    )

    # ── Jobs (rebuild with parameterized evaluators) ─────────────────────────
    _all_edges = [
        _e_intent_req, _e_req_feat, _e_feat_design, _e_design_mdecomp,
        _e_mdecomp_code, _e_tdd, _e_unit_itest, _e_itest_guide, _e_guide_uat,
    ]

    _job_intent_req    = Job(_e_intent_req,    [eval_intent_fh])
    _job_req_feat      = Job(_e_req_feat,      [_eval_req_coverage, eval_decomp_fp, eval_decomp_fh])
    _job_feat_design   = Job(_e_feat_design,   [eval_design_fp, eval_design_fh])
    _job_design_mdecomp = Job(_e_design_mdecomp, [eval_module_coverage, eval_module_schedule_fp, eval_schedule_fh])
    _job_mdecomp_code  = Job(_e_mdecomp_code,  [_eval_impl_tags, eval_code_fp])
    _job_tdd           = Job(_e_tdd,           [_eval_tests_pass, _eval_test_tags, _eval_e2e_exists, eval_coverage_fp])
    _job_unit_itest    = Job(_e_unit_itest,    [eval_sandbox_report, _eval_sandbox_run])
    _job_itest_guide   = Job(_e_itest_guide,   [_eval_guide_version, _eval_guide_coverage, eval_guide_content])
    _job_guide_uat     = Job(_e_guide_uat,     [eval_uat_fh])

    _all_jobs = [
        _job_intent_req, _job_req_feat, _job_feat_design, _job_design_mdecomp,
        _job_mdecomp_code, _job_tdd, _job_unit_itest, _job_itest_guide, _job_guide_uat,
    ]

    # ── Package + Worker ─────────────────────────────────────────────────────
    _package = Package(
        name=slug,
        assets=list(package.assets),
        edges=_all_edges,
        operators=[claude_agent, human_gate, _pytest_op, _check_impl_op, _check_test_op, check_modules_op],
        rules=list(package.rules),
        contexts=[gtl_bootloader, sdlc_bootloader, _this_spec, intent_doc, _design_adrs, modules_dir],
        requirements=list(req_keys) if req_keys is not None else [],  # Implements: REQ-F-CUSTODY-001
    )

    _worker = Worker(
        id=worker.id,
        can_execute=_all_jobs,
    )

    return _package, _worker
