# W359718 — implementer progress

## claim359749 — a reservation owns both names

Answers the child `FINDING.md` and parent review R12 under handoff359746.
Cumulative candidate `candidate-359749/`, manifest
`b7287b7b72f191679c033ec1cb180e2f93cce18a767c253d4d2117af00f94c7b`, fourteen
members carried forward from the parent's immutable `candidate-359603`
(`ad9a63db…`). The manifest records, per member, its canonical base digest, its
candidate digest, the parent candidate's digest, and whether **this slice**
changed it — three files did. Base
`302453869d07eb5579e79a6572586d3c3cf62a5c`; the canonical tree is untouched and
every parent and sibling candidate is preserved.

### The defect, exactly

`submission._unclaimed` loaded reservations whose **Job ids** occurred in the
incoming document. A second submission that reused the reserved **submission
id** for an entirely different Job matched nothing, recorded itself, and the
retry — whose operation identity is derived from that submission id — then
collided *after* it had already published a deployment binding. A reservation
owns two names and only knew about one.

### The correction

- `submission._unclaimed` selects reservations by `submission_id = ? OR job_id
  IN (…)`, and names which of the two was taken, because a submission reusing a
  reserved **Job** and one reusing a reserved **submission id** for something
  unrelated are different mistakes.
- `fresh_attempt._reserved` additionally refuses when another reservation
  already holds this submission identity for a different document — two fresh
  attempts may pick their own names, but not one name for two intents, and
  finding that out at `submit` would be finding it out with a binding already
  published. That one is durable: it is a fact about another reservation rather
  than about the operation identity being protected.

The conflicting-ordinary refusal stays **non-durable**, which the child FINDING
accepts as an implementation choice. Sealing it under an operation identity
derived from the submission id would poison the one submission the reservation
exists to admit; a case proves the retry completes after exactly that rejection.

### Verification

`evidence/claim-359749/`. **Red to green, measured:** the two decisive cases — a
nonoverlapping Job taking the reserved submission id, and the retry completing
afterwards — FAIL against the parent candidate's `submission.py` and pass here.
`R12.txt` is the verbose run; `SUITES.txt` records both sides. The other four
cases in the class already held under the parent and are labelled as the
regression cover they are, not as new proof.

Six cases in the new class: the nonoverlapping steal refused with nothing
recorded; the retry completing and then replaying after that rejection; the
ordinary-first order refusing the retry before any reservation, Work or binding;
two retry intents refused for sharing one submission identity; the intended
document still admissible; and an unrelated submission untouched, because the
rule owns two names rather than every submission.

Focused suite **84 cases, 0 failures**. Whole `tests/job_manager` **1102 cases,
one failure** — the same pre-existing `test_native_permission` case.
`test_bootstrap`, `test_scheduler_trace` and `test_single_worker` 522 cases with
the one pre-existing `test_single_worker` failure baselined under the parent.
The four inventory suites produce the identical 116 failures as the canonical
base.

### Limits

This slice is submission identity only. The host lifetime and identity
corrections (R13/R14) are W359719's and are **not** addressed here; the parent's
own limits stand unchanged — no engine, provider, runtime or credential is
reached, so that a fresh attempt succeeds is still not proved.
`tests.tools.test_stage_execution` was not re-run this claim: no member it
covers changed since the parent candidate, where it passed 477 cases.

### Cost

Three focused-suite runs, zero failing; one deliberate red run against the
parent bytes to establish the regression; `tests/job_manager` twice whole; the
bootstrap/scheduler-trace/single-worker group once at 92s; the inventory suites
once against the retained canonical baseline. No product execution, no instance
operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. Parent and sibling candidates, the parent
PROGRESS and the reviewer's records and evidence are untouched. I wrote only
this child's candidate, its evidence and this file.

## claim359821 — the journal owns the submission identity too

Answers `review-2026-10-23T22-52-41Z.md` R15 under handoff359817. Candidate
`candidate-359821/` supersedes `candidate-359749` (preserved), manifest
`9f06dbe34e17407ad06d2e62a368f36f10b6d0d11052bf28814cb5730ff9ca67`, fourteen
members; **two** changed in this round -- `fresh_attempt.py` and
`test_fresh_attempt.py`. Base `302453869d07eb5579e79a6572586d3c3cf62a5c`;
canonical tree untouched; parent and sibling candidates preserved.

### The defect

`_reserved` consulted `submissions` and `fresh_attempts`. But
`store.transact` journals a DURABLE REFUSAL as that operation's committed
outcome, so `submission.record:<id>` can be settled forever with no
`submissions` row at all -- and an absent row is not a free name. The
reservation passed, the binding published, and the immutable journal
signature was met at `submit`, where nothing could be done about it.

### The correction

`_reserved` reads the operations journal for
`submission.operation_id(submission_id)` and refuses when it is settled for a
different document -- before the reservation, the Work and the binding. The
earlier outcome is neither erased nor renamed: history is what makes the
refusal true, and a case asserts the row is byte-identical afterwards.

**And the advice changed, because the old advice was unfollowable.** Every
other post-reservation refusal is repaired by running the same request again;
an operation identity already settled for another intent never will be. This
one says to choose another submission identity, and the submit-time wrapper
no longer tells a caller to loop on an `operation-collision`.

### What my own case caught

Writing the recovery case -- "choose another submission identity, then it
works" -- proved that it did not. The journal refusal was durable, so it
sealed `fresh_attempt.intend:<job>`, and the corrected request under a new
submission id collided with the refusal that had just told it to try one.
All three submission-identity refusals in `_reserved` are now ordinary, for
the reason the intruder rejection already was: a durable refusal is a
committed outcome for THIS operation identity, this intent's identity is
derived from the fresh JOB id, and the remedy is a different SUBMISSION id
for the same Job. Sealing it made the remedy impossible.

### Verification

`evidence/claim-359821/`. **Red to green:** the new six-case class produces
three failures and one error against `candidate-359749`'s `fresh_attempt.py`
and passes here; `R15.txt` is the verbose run and `SUITES.txt` records both
sides. The class covers the review's list -- a prior durable refusal with no
submission row, an incompatible committed submission, the honest advice, the
earlier outcome preserved byte for byte, recovery under another submission
identity, and the lost completion that must NOT refuse.

The lost-completion case restores the one column cut C would not yet have
written, rather than recording a submission with no reservation -- a state
this operation cannot reach and which its own Job check correctly refuses.
It proves the resumed request finishes with one binding effect and one Job
row.

Focused suite **90 cases, 0 failures**. Whole `tests/job_manager` **1108
cases, one failure** -- the same pre-existing `test_native_permission` case.
`test_bootstrap`, `test_scheduler_trace` and `test_single_worker` 522 cases
with the one pre-existing `test_single_worker` failure. The four inventory
suites produce the identical 116 failures as the canonical base.

### Limits

Submission identity only; R13/R14 host lifetime and identity remain
W359719's. The parent's limits stand -- no engine, provider, runtime or
credential is reached, so that a fresh attempt succeeds is still not proved.
`tests.tools.test_stage_execution` was not re-run: no member it exercises
changed since the parent candidate, where it passed 477 cases.

### Cost

Six focused-suite runs (three failing: two assertions superseded by the
stronger journal refusal, and the recovery case that exposed the durability
defect above); one deliberate red run against the prior candidate; one
abandoned edit script that left the file untouched and was redone;
`tests/job_manager` twice whole; the bootstrap/scheduler-trace/single-worker
group once at 92s; the inventory suites once against the retained canonical
baseline. No product execution, no instance operation, no total manufactured.

### Boundaries

No Git, no live provider, engine, credential read, install, deployment or
retained-instance operation. No store opened, copied or traversed outside the
disposable ones the cases create. Parent and sibling candidates,
`candidate-359749` and the reviewer's records and evidence are untouched. I
wrote only this candidate, its evidence and this file.
