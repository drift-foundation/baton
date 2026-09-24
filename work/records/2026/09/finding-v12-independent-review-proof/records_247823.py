"""Claim-247823 dossier entries: the lifecycle settles; items 4 and 6 remain."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CHECKPOINT = """# Checkpoint -- W239533

Kept concise per AGENTS.md "Delivery continuity and bounded context"
(owner 2026-09-23). FINDING keeps the history; this is the working state.

## Accepted so far

  * the attachment arrangement and its supported read-only survey
    (2026-09-23T04:50:12Z, 2026-09-23T05:08:49Z)
  * the local `review_supervisor` specialization's source and the R1/R2
    interface fixes (2026-09-23T11:56:42Z)
  * the `correction_policy` product change's source branch
    (2026-09-23T12:20:24Z), and the twelve pre-existing product errors
    corroborated focally (2026-09-23T12:45:47Z, item 5)
  * the reviewer's own string-operand probes settling ACCEPTED and
    CHANGES-REQUESTED (2026-09-23T12:57:02Z)

## Done under claim 247823 -- owner 247663 items 1, 2 and 3

ONE REVIEWER IS ADMITTED AND ENDED, over real coordination, and it SETTLES:
`state: settled`, `stopped: completed`, `admissions {"review": 1}`, one
attributed verdict read from the reviewer's frozen output and bound to the
packet's checkpoint base/head/tree, runtime `destroyed`, cleanup `retained`
with state `absent`, zero correction rounds, zero correction containers, no
hold reasons. `changes-requested` settles the same way. Eight discoverable
cases in `test_review_lifecycle.py`, in `verify.py`.

## Next executable milestone -- owner 247663 item 4

A distinct digest-bound successor manager-source artifact carrying the
`correction_policy` change, built the way
`../finding-v12-single-implementation-proof/snapshot_242687.py` builds one and
leaving the producer's snapshot untouched; then `SELECTIONS-239533.json`
pointing at it instead of `single-implementation-242687/manager-source`, which
predates the change; then the documented preparation and startup executed
against those exact successor bytes on disposable fixtures. Item 6 (the
complete packet, commands, provider question and execution evidence) follows.

## Owned paths

This dossier in full, plus ONE product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`.
`OWNERSHIP-239533.md` carries the per-claim detail.

## Latest review and evidence

`review-2026-09-23T12-57-02Z.md`; this claim's receipt is
`verification-8.json`. Last discussion position read: T239533 message 247805
(the delivery-continuity policy). Last event read: 247812.

## Blockers

None. The packet remains NOT RUNNABLE until items 4 and 6 are done and the
whole preparation is independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247823

Owner reroute 247812 and thread message 247805 (the delivery-continuity
policy, now in AGENTS.md). Read current canonical detail, the handoff since
247794, the latest review and the new discussion; the checkpoint above records
those positions. **Items 1, 2 and 3 of owner 247663 are done. Items 4 and 6
remain and no new authority is needed for them.**

### The reviewer found the cause and it was mine

`claude_agent._review_report` requires `findings` to be NON-EMPTY TEXT; both
fixture reports supplied a LIST, so the adapter answered `unable` and the
manager correctly refused to read a verdict out of a turn that did not
complete. The adapter was right and the fixture was wrong -- "an exit status is
not a decision and this adapter will not map one into a verdict" is exactly the
behaviour that made this hard to misread. Corrected in place with the reason
recorded beside it.

With that one operand corrected the whole path settles:

    state settled, stopped completed, stage review completed
    admissions {"review": 1}, one admitted attempt
    verdict accepted, bound to the packet's checkpoint base/head/tree,
      with result_id and result_digest
    cancellation requested, execution_runtime destroyed
    cleanup retained, state absent
    correction_rounds_opened [], correction_containers_started []
    held_because []

### Eight discoverable cases, and a loader defect they exposed

`test_review_lifecycle.py` now carries `OneReviewerIsAdmittedAndEnded`,
`AChangesRequestedReviewIsAValidOutcome` and
`AnAdmittedAttemptIsAccountedForWhenTheRunDoesNotFinish` -- the attributed
verdict, the stopped runtime and positive cleanup, producer/reviewer
independence read back through `review_of`, `changes-requested` settling with
zero rounds and zero containers, and an interruption and a composition failure
that each leave ONE ADMITTED ATTEMPT accounted for with the outcome published.

Excluding the base class by NAME was not enough: the fixture's ancestors carry
their own `test_` methods, so the three new classes inherited twelve of
W239528's and the product suite's cases and ran them under this dossier's name.
`load_tests` now filters on each class's OWN `__dict__`, which is the only set
this module wrote.

### The stale limitation prose, corrected

`CORRECTION_LIMITATION` still said the round could not be prevented and that
the fix belonged to the owning implementation scope. Owner selection 247421
MADE that change, so the text now names the boundary that closes it -- and says
that a round appearing anyway means the boundary did not hold, which is a fault
worth holding on rather than a state to accommodate. Its case moved with it.

### Spending, including what was not a test

Verification: 96 focused deterministic checks, 0 failures, measured
5.328163940997911s, receipt `verification-8.json` with `verification-8.log`;
8 are new and `test_review_lifecycle` is now in `verify.py`.

THE PROBES ARE COUNTED TOO. Review 2026-09-23T12:57:02Z is right that
unmeasured driving is not zero spending. Claims 247757 and 247823 drove the
two-phase fixture roughly a dozen times outside any receipt while finding the
four defects and the report shape. Those runs were not individually timed, and
the honest figure is an upper bound rather than a measurement: at the
5.3-second cost the receipt now measures for a suite containing four such
drives, a dozen ad-hoc drives is on the order of 20 seconds. It is recorded as
**~20s ESTIMATED, NOT MEASURED**, and it is not folded into the measured total.

Cumulative MEASURED for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 + 1.295056363 + 5.328163941
= **171.818046220s**, plus the ~20s estimated above. The reviewers' independent
measurements (0.571337769s, 0.596305013s, 1.152729417s, 1.311204790s,
1.302250807s, 2.361050477s, 3.324525589s) are theirs and are preserved
separately.

State: returned for independent review with items 4 and 6 outstanding. Per the
delivery-continuity policy this is ordinary continuation, not an owner gate.
"""

OWNERSHIP = """
## Claim 247823 -- the settled lifecycle

Edited in this dossier: `test_review_lifecycle.py`, `test_review_supervisor.py`,
`review_supervisor.py`, `verify.py`, `PLAN.md`, `PROGRESS.md`, this file.
Added: `records_247823.py`, `verification-8.json/.log`.

**No file under `v12/` was edited under this claim.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. W239528's
`baseline.py` is unchanged at its accepted digest and is SUBCLASSED for its
fixture, not modified. No deployed store was opened, both images are unchanged,
the disclosed `control.sqlite3-shm` and zero-length `control.sqlite3-wal` are
preserved, and every reviewer file in this dossier is append-only history that
was not modified.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247823" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247823" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
