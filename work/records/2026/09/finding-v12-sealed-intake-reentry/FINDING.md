# Re-enter sealed intake without losing the original held reason

Ledger Work: W144335. Discovery: W71879 review claim144288, actual run1.

## 2026-09-11T12:28:12Z — baton.codex — confirmed defect, deferred

**Observed:** the retained run at `/home/sl/.local/state/baton/v12/w71879-run1`
has A implementation and B review terminals with disposition `unable` after
provider status1/api-error. Their output artifacts exist in custody, and the
last serve report refuses both repeated conclude calls because output is
`sealed`, while intake requires `frozen`. Neither integration started.
Exact assessment/evidence lives at
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/review-2026-09-11T12-28-12Z.md`.

**Confirmed by source:** `v12/python/src/baton_v12/job_manager/review_driver.py`
`_collected` calls `request_intake` on each live-runtime ending entry.
`v12/python/src/baton_v12/worker_manager/intake.py` `request_intake` calls
`_collectable` before any replay; `_collectable` only admits `output=frozen`.
Successful `record_intake` changes that axis to `sealed`. Thus an ending that
retains custody and then remains held cannot re-enter its collection step.
This is independent of a provider error's upstream cause.

**Inferred first-pass explanation, not a retained first-pass trace:** A reaches
`integration/driver.py:retain_proposal`, which refuses any disposition other
than completed. B reaches `review_driver.py:review_verdict_from_result`, which refuses
an unable review and returns a held outcome through `_ended_review`. Subsequent
calls fail earlier at collection. The retained serve.log contains only the last
sweep, so it does not independently prove the original refusal text.

**Proposed boundary:** make the existing custody owner safely answer an exact
re-entry from its validated recorded receipt, preserving result/assignment/
operation identity and custody disposition. Preserve retention replay and the
original honest unable/held outcome. Do not reset the output axis, recollect
mutable bytes, bypass correlation, manufacture a proposal/verdict, clean up a
live assignment, or turn unable into completed. Decide at implementation
revalidation whether the correction belongs in the public intake owner or its
driver consumer; a raw receipt fallback without those checks is insufficient.

This is separable failure/re-entry hardening. It does not make a failed provider
turn succeed and is not a prerequisite for legitimate first-pass A/B success.
It is explicitly deferred under the campaign's 2026-09-11T00:30:54Z acceptance
clarification. No W71830/W71879 containment or dependency is created.

No source, existing test, live store, runtime or credential was changed. No
workaround was performed. This filing grants no implementation claim or budget.
