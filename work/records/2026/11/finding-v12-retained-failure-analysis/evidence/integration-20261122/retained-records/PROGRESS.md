# Progress

## 2026-11-22 — baton.codxpc E385631 native kickoff preparation

M385630 preparation completed at evidence/native-kickoff-385631/KICKOFF.md, TASK.txt, verification-argv.json, required-inputs.json, immutable input templates, binding-observations.json, REPORT.md and manifest.json. Native implementation outcome remains unimplemented. Existing tools and /3 native review are used; no bespoke launcher. Different-family composition unavailable on inspected hard-coded Claude/Opus path; explicit supported alternate or owner same-family selection is required, not inferred. Required allocation/task bytes await owner checkpoint; exact paths and hashes retained, and final source is selected once after checkpoint without evidence-only repin loops. Commands remain conditional and unexecuted. Literal verification argv and shell/Python syntax mechanically checked; disk-backed host parent roots/image/source compatibility inspected. No tests/build/provider/instance/credential/Git/graph mutation or host feature changes. Return to baton.decide with exact blockers for kickoff selection; W385624/W385625 remain separate dependent outcomes.

## 2026-11-22 — native Work 905166b2-W1 Stage 1-A implemented

Stage 1-A is implemented in the isolated native candidate and submitted to
`baton.reviewer-native`. Evidence, candidate digests and the changed-path/reason
accounting are at `evidence/native-stage-1a-385623/` (`REPORT.md`,
`manifest.json` and the retained logs); scratch is not published alone.

Added `v12/python/src/baton_v12/job_manager/failure_analysis.py` — the trigger
on a durably attributed terminal `verification-failed` ending with a successful
provider turn and a candidate validated against its measured bytes; the
six-selector failure key; the immutable fixed input; the declared analysis
worker/profile authority (`baton.v12.recovery-analysis-worker/1`, no provider or
model bound to the role); the owner-approved `stage1-analysis/1` definition held
as data and digested to `a4be8b48…`; five durable journal records; the four
finite endings that preserve partials and deliver one owner item; and the
automatic observe → intent → dispatch → report → owner-item path. Added the
submitted acceptance module
`v12/python/tests/job_manager/test_retained_failure_analysis.py` (87 ids, all
passing). Modified `v12/python/tools/parallel_test.py` with two additive
registrations TESTING.md §6/§9 require for a discoverable new module and its one
consumed owner-approved definition file; no existing test, assertion, registry
entry or expectation was changed.

Analysis cannot mutate candidate, verifier or execution state: a frozen analysis
result carrying any output outside its permitted set is refused, and a case
compares the whole control store byte-for-byte across the path. W385624's owner
decision/successor admission and W385625's verification/review recovery are not
implemented and their graphs are untouched; `fresh_attempt`, `review_driver`,
`job_control`, `episodes` and `cancellation` are unchanged.

Submitted verification: 87 collected, 87 passed, 0 failed/errors/skips, 1.546 s,
exit 0. Focused regressions: `tests.tools.test_parallel_runner` 73/73 (16.34 s)
and `tests.manager.test_attempt_failure_cause` 117/117 (0.78 s). Owning group
`job_manager`, per module: 1809 collected, 1720 passed, 88 failures, 1 error.
All 89 non-passes are in `test_fresh_attempt`, `test_native_permission`,
`test_store_readonly` and `test_tool`, which this change does not touch; each was
re-run in this candidate with the change moved aside and the failing id sets are
identical in both directions. Their cause is environmental and is reported, not
waived: those cases need a disk-backed directory outside the checkout, and here
the checkout is `/output`, `/var/tmp` and `~/.cache` are unwritable and `/tmp` is
a tmpfs the workspace boundary refuses; `BATON_V12_STACK_TEST_ROOT` cannot be
satisfied. No `OPTIONAL_SKIPS` entry was added and no coverage was weakened.

Not run, and named rather than implied: the accounted `just test-group` /
`just test-all` entries, because `just` is absent and the prepared interpreter
at `~/.local/state/baton-v12-venv` has not been prepared in this candidate — so
this run has no `--account` ledger and no content-bound source-identity
document. No full suite, Docker-daemon campaign, nested live-provider test, live
instance change or Git mutation. No provider or model was invoked anywhere.

No unresolved product or authority decision arose, so no `/3` handoff to
`baton.slaw` and no `handoff/request.json` was written. Awaiting independent
native review of the exact candidate at declared base
`72e1093dccb3ded9763fd2c42f0f713a7ff2c88f`. An owner Git checkpoint of the
candidate and this evidence is due once that review is recorded.

## 2026-11-22 — W385623 correction Job: the automatic path is connected

This is a SEPARATE execution of the independent reviewer's correction, from the
retained candidate `f13e0b1255cfd43e145fe2ced565704e888e3e17` (original base
`72e1093dccb3ded9763fd2c42f0f713a7ff2c88f`). The prior native Job
`905166b2-W1` completed execution and its review returned changes-requested;
that Job's clocks, allowance and evidence are untouched. Canonical owner Work
remains W385623/T385623. Evidence:
`evidence/native-stage-1a-correction-385623/` (`REPORT.md`, `manifest.json`,
the retained logs and the group ledger).

**The reviewed finding, and what it is now.** `failure_analysis.py` was
library-only: no production caller reached `observe_terminal_failure`,
`admit_dispatch`, `deliver_analysis` or `deliver_endpoint`, and no deployment
produced `baton.v12.recovery-analysis-worker/1`. Both are connected:

* `failure_analysis.advance_recovery` is a new level-triggered pass —
  observe, dispatch, deliver — derived from the Job store's own SETTLED ending
  records and the five recovery records, with a bounded `recovery.analysis`
  document per act it performs, holds or reports.
* `manager.sweep` calls it on every tick through `manager._analyse`, so every
  `tools/job_manager.py serve` and `--once`, and every `reconcile` resume,
  reaches it. `ManagerOperations` carries the seam as an optional capability
  beside the runtime start and the exchange halves.
* `failure_analysis.declared_analysis_worker` PRODUCES the declaration from
  the four facts a deployment owns; the schema, the role, the owner-approved
  `stage1-analysis/1`, its digest and the permitted outputs come from the
  definition the module holds and digests at import, so an operator cannot
  select an unapproved profile by typing one.
* `tools/stage_execution.py` is the deployment producer: an optional
  `analysis_worker` configuration member validated by `_held_analysis` before
  anything is opened, the produced declaration, `AnalysisExecution` over the
  accepted non-stage worker lifecycle, and `RecoveryAnalysis` exposed as
  `recovery_analysis` on the composed operations object.
* `failure_analysis.analysis_attempt_id` derives the analysis attempt identity
  from the failure key, so an exact retry reuses it and no seam is ever handed
  a fresh one.
* `job_manager/__init__.py` exports the operation and its configuration
  contract.

Preserved exactly: the approved `stage1-analysis/1` profile and its digest
`a4be8b48…`, the immutable validated evidence and its revalidation before both
dispatch and delivery, the six-selector failure key and task attribution, the
role's permitted outputs, cancellation/expiry/unknown cessation, and no retry
or recursive analysis. Nothing in the reviewed `failure_analysis.py` sections
1–9 was weakened; the new section 10 only decides WHEN to call them.

**Verification.** Submitted acceptance command, run exactly as configured: 140
collected, 140 passed, 0 failed/errors/skips, 3.312 s, exit 0 — the 87 prior
ids are all present and passing by name, plus 53 new ones driving the real
`manager.sweep`, including one that drives the whole path through the real
`ManagerOperations`. Owning group `job_manager`: 31 modules, 1862 collected,
1773 passed, 88 failures, 1 error, 0 skipped. All 89 non-passes are the same four
environmental modules the prior run reported (`test_fresh_attempt`,
`test_native_permission`, `test_store_readonly`, `test_tool`) with identical
counts; they need a disk-backed directory outside the checkout, which this
environment cannot supply. Reported, not waived, and no `OPTIONAL_SKIPS` entry
was added.

**Corrected accounting.** The prior REPORT/manifest claim of 32 modules in the
owning group was wrong: there are 31 (30 existing + 1 new) and 27 were OK, not
28. Both files now carry the corrected figures with an explicit Correction
section/member; no measured count, log or ledger byte was rewritten.

Not run and named rather than implied: `just test-group` / `just test-all`
(`just` absent, prepared interpreter unprepared), so this run has no
`--account` ledger and no content-bound source-identity document. No full
suite, Docker-daemon campaign, nested live-provider test, live instance change
or main-checkout Git mutation. No provider or model was invoked anywhere; the
analysis turn is a deterministic replay at its normal boundary. W385624's owner
decision/successor admission and W385625's verification/review recovery remain
unimplemented and their graphs untouched. Awaiting independent native review of
the exact candidate; the owner Git checkpoint remains due.
