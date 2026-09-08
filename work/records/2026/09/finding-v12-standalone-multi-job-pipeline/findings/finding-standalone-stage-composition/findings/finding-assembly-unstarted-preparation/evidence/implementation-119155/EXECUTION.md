# Focused verification, W119113 claim119155 — baton.claude

All commands run from `v12/python` in the repository checkout. No live model,
no container daemon, no OCI campaign, no canonical target import, no
coordination-store read and no mutating Git operation. The deterministic
engine and the child-process provider are the accepted seams the port suite
already owns.

## The focused gate

    PYTHONPATH=.:src python3 -m unittest -v \
        tests.tools.test_stage_execution \
        tests.tools.test_integration_worker \
        tests.tools.test_single_worker \
        tests.integration.test_driver

**308 tests, OK, 15.070s** — `focused.txt`. This is the correction's own
module, the production port it drives, the worker half it shares and the two
accepted drivers it selects between. No whole-subtree run was performed: the
retained gate log at
`b4f19ea440037846d4e1a5b0abfb3a84e4a0d8da05e1e66fa01770c4fe4f70c6` is audited
in PROGRESS rather than repeated, and it would not answer the composed
lifecycle that W119114 owns.

## The defect, reproduced against the reviewed bytes

`prior-stage_execution.py` is the handoff119024 candidate reconstructed by
inverting exactly this claim's one source hunk; it hashes to the reviewed
`dee7a1c9e20831f25d2edd1727dbd7acf767c0aa00658d76174bcd065006d3ca`, which is
the proof that nothing else in the module moved. The three affected classes
run against it in `prior-source-regression.txt`:

**19 tests, 1 failure and 1 error** — the fresh-port case refuses with
`attempt 'integrator-attempt' has no credential delivery from this execution's
own preparation`, the exact refusal review 2026-09-08T12:41:47Z measured, and
the approved never-started expectation records `observed` without `prepare`.
The other 17 pass on both versions, so the controls are not carried by the fix.

## The candidate

`assertion-audit.json` compares this candidate with review 119091's retained
snapshot: 26 prior test classes AST-identical, two classes added, one method
added, and exactly one existing test method changed —
`TheIntegrationStageConsumesTheAcceptedPort.
test_a_delivery_with_no_started_runtime_is_not_refreshed`, which is the change
M118923 approved. `tools/single_worker.py`, `tests/tools/test_single_worker.py`
and `tools/parallel_test.py` are byte-identical to the reviewed snapshot.
