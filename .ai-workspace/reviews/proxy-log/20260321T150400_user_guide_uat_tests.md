Feature: user_guide→uat_tests
Edge: user_guide→uat_tests
Iteration: 1
Timestamp: 2026-03-21T15:04:00Z
Decision: approved

Criteria:
- Criterion: sandbox_report.json shows all_pass: true
  Evidence: .ai-workspace/uat/sandbox_report.json — install_success: true, test_count: 33, pass_count: 31, fail_count: 0, skip_count: 2, all_pass: true. Timestamp: 2026-03-21T12:05:00Z.
  Satisfied: yes

- Criterion: USER_GUIDE.md is coherent and version-current
  Evidence: docs/USER_GUIDE.md version 0.5.1 (matches current release). 10-section structure covering installation, first session, commands, graph, working loop, traceability, spec writing, self-hosting, and limitations.
  Satisfied: yes

- Criterion: Every operator-facing feature is documented
  Evidence: 19 REQ-F-* references found in USER_GUIDE.md. Guide covers all operator-facing features: install, commands (gen-gaps/iterate/start), traceability tags, coverage enforcement, human gates, module decomposition, backlog, integration tests, user guide conventions, and UAT.
  Satisfied: yes
