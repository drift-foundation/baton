# M385773 accounting correction — appended 2026-11-23

This supersedes the identified claims in retained candidate 4e869a1d, not the
original logs. All original native evidence remains byte-identical in
`retained-proposal/objects.bundle` and in the cumulative candidate under
`evidence/native-stage-1c-385625/`.

* REPORT.md limitation 6 incorrectly claims two authority failures. The retained
  authority.log says 511 tests, OK. The authority result is 511 passed, zero
  failures/errors/skips.
* Native PROGRESS.md's “six cases” statement is incorrect. Its baseline and
  candidate logs identify four nonpassing cases: three failures and one error.
  The later “same four results” wording is the supported historical account.
* COUNTS.md's focused table is malformed: its rows are per-class counts, not
  nine-column run summaries. Use the corrected run-level table below. These
  are historical native runs, not reruns by codxpc.

| Native run | Collected | Passed | Failed | Errors | Skipped | unittest seconds | wall seconds | Original log |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| focused | 162 | 162 | 0 | 0 | 0 | 7.935 | 8.141 | native-stage-1c-385625/focused.log |
| repeat | 162 | 162 | 0 | 0 | 0 | 7.875 | 8.085 | native-stage-1c-385625/focused-repeat.log |

The native report's claim that the deployment composes the verification seam
was premature for 4e869a1d. Its joined test called advance directly for the
three middle acts and used FakeOperations for reviewer admission. The new
correction wires the seam into bootstrap/stage composition and uses real
manager reconciliation for materialization, execution and handoff. Its separate
scheduler admission assertion remains explicitly simulated. No reviewer model
or container is run by this correction; no substantive verdict is fabricated.

The native “restart at every cut” claim did not cover result journal committed
but verification account missing. New pass/fail restart and concurrent replay
probes inject that exact cut. A durable result is accounted without another
child; an intent without result still holds as unknown.
