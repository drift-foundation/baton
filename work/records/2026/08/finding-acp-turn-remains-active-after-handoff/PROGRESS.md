# Progress

The two-hour v11 turn deadline is approved and recorded. No implementation
claim exists yet. The live defect is ready to pass from approval to the
bounded template-alignment implementation; W38956 remains the current campaign
focus.

## 2026-08-29 — `baton.tuner`

Implemented the bounded template crossing under W39092. Added the approved
`turnTimeoutMs=7200000` policy to `conf/acp-bridge.template.json`,
`conf/acp-claude.template.json`, and `conf/acp-gemini.template.json`; extended
the lifecycle acceptance test to require the generic template in the shipped
set and pin the exact deadline across all three.

Verification passed: all 42 tests in
`tests/work/test_w459_fresh_contexts.py`, all 89 tests in the ACP bridge suite,
the two focused template assertions after final edits, and `git diff --check`.
No live configuration, installed release, launcher, process domain, or service
was changed. State: implementation complete and awaiting review before the
operator-owned cutover.
