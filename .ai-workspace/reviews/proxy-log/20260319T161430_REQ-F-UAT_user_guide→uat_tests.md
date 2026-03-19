Feature: REQ-F-UAT
Edge: user_guide→uat_tests
Iteration: 1
Timestamp: 2026-03-19T16:14:30Z
Decision: approved

Criteria:
- Criterion: sandbox_report.json shows all_pass: true
  Evidence: .ai-workspace/uat/sandbox_report.json (2026-03-19T16:09:58Z): install_success=true, test_count=33, pass_count=31, fail_count=0, skipped_count=2, all_pass=true. The 2 skipped tests are for backlog CLI not installed in sandbox (expected). 31 e2e tests pass including graph shape, install, coverage evaluator, tag check, and integration scenarios.
  Satisfied: yes

- Criterion: USER_GUIDE.md is coherent and version-current
  Evidence: USER_GUIDE.md **Version**: 0.2.1 matches install.py VERSION="0.2.1". guide_version_current F_D evaluator passes (exit 0). guide_content_certified F_P assessment passed — guide coherently covers install steps, first session, all commands (gen gaps/iterate/start/review/backlog), operating loop, recovery paths. Content is technically accurate.
  Satisfied: yes

- Criterion: Every operator-facing feature is documented
  Evidence: 32/32 package.requirements keys covered by <!-- Covers: REQ-F-* --> blocks. guide_req_coverage F_D evaluator passes (exit 0, uses importlib to check completeness against pkg.requirements). All operator-facing REQ families documented: GRAPH, CMD, COV, GATE, TAG, TEST, UAT, MDECOMP, BOOT, DOCS, BACKLOG, VAR.
  Satisfied: yes
