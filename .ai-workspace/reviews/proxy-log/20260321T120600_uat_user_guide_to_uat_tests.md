Feature: all
Edge: user_guide→uat_tests
Iteration: 1
Timestamp: 2026-03-21T12:06:00Z
Decision: approved

Criteria:

- Criterion: sandbox_report_shows_all_pass
  Evidence: .ai-workspace/uat/sandbox_report.json contains {"install_success": true, "all_pass": true, "pass_count": 31, "fail_count": 0, "skip_count": 2}. Sandbox install succeeded (v0.4.0, engine installed, claude_md appended, 0 errors). 31 e2e tests passed, 2 skipped (no failures).
  Satisfied: yes

- Criterion: user_guide_coherent_and_version_current
  Evidence: docs/USER_GUIDE.md carries **Version**: 0.4.0 matching install.py VERSION. F_D guide_version_current and guide_req_coverage both pass. Sections cover: installation, first session, all three commands (gen-start, gen-gaps, gen-iterate), the SDLC graph, the working loop, traceability, writing your own spec, self-hosting spec, and current limitations.
  Satisfied: yes

- Criterion: every_operator_facing_feature_documented
  Evidence: USER_GUIDE.md documents: gen-start/gen-iterate/gen-gaps commands (§4), the 10-asset graph (§5), F_D→F_P→F_H ordering (§6), REQ key traceability (§7), and the self-hosting spec model (§9). Covers bootstrap install, operating loop, and recovery from each stop reason.
  Satisfied: yes
