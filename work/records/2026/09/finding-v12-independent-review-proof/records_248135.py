"""Claim-248135 dossier entries: the selector fixed; three of four conditions."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CHECKPOINT = """# Checkpoint -- W239533

Concise per AGENTS.md "Delivery continuity and bounded context". FINDING keeps
the history.

## Accepted

  * the attachment arrangement and its supported read-only survey
  * the `review_supervisor` specialization's source and its interface fixes
  * the `correction_policy` product change's source branch; item 5
  * owner 247663 ITEMS 1 AND 2 (2026-09-23T13:04:00Z)
  * gate-state-at-cancellation and the exact outstanding identity
    (2026-09-23T13:10:01Z)
  * the reached deadline and the observed shutdown interruption
    (2026-09-23T13:15:08Z)
  * the successor snapshot and its bindings (2026-09-23T13:20:42Z)
  * the successor-only composition and the 106-file packet manifest
    (2026-09-23T13:25:28Z)
  * `main` actually invoked, bounded successor-source startup
    (2026-09-23T13:35:00Z)

## Done under claim 248135 -- the fixture cause the review found

`ComposedOneJobCase.states` reads `projected["jobs"][0]` -- correct for a
one-Job fixture, wrong the moment a second Job exists. Under the stalling
submission it answered the BLOCKER Job's stages, so the driver never saw
`review` reach `waiting`, never took the turn, and the attempt ended
`exceptional`. The override selects by `REVIEW_JOB` and falls back to the
inherited positional answer for phase one, which has no review Job -- an
override that answered nothing there stopped the PRODUCER's turn being taken,
which is the same positional assumption failing from the other side.

MEASURED after the fix, on the stalling submission: `review: completed`,
`integration: blocked`, `outstanding_cleanup: []`, verdict `accepted`. THREE OF
THE DETECTOR'S FOUR CONDITIONS now hold -- an accountable attempt, no
outstanding cleanup, and a non-terminal Job.

## Next executable milestone

1. THE FOURTH CONDITION. `stalled_ticks` is still 0 over 241 serving ticks, so
   the observation is still changing -- exactly what review
   2026-09-23T13:41:04Z predicted: "final cleanup does not establish positive
   cleanup during six serving observations". The next step is to inspect WHEN
   during serving the cleanup actually commits and what else in
   `_observation(states, accountable, cleanup)` keeps moving, then hold
   advancement at the transition boundary and add the asserting regression.
2. Owner 247663 item 6: the complete packet, exact commands, provider question
   and honest evidence, distinguishing the `Deferring`-composition `main`
   startup proof from the successful real-coordination lifecycle. **No
   successful reviewer run through `main` is proved.**

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. Outside
the checkout: `/home/sl/baton-runs/independent-review-247947/manager-source`,
built once, read but never rewritten.

## Latest review, evidence and positions read

`review-2026-09-23T13-41-04Z.md`; receipt `verification-15.json`. Last
discussion position read: T239533 message 247805. Last event read: 248131.

## Blockers

None. NOT RUNNABLE until the remaining items are done and the whole
preparation is independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 248135

Review 2026-09-23T13:41:04Z found the fixture cause I had left as an open
question, and it was a positional assumption rather than anything about the
lifecycle.

### The selector

`ComposedOneJobCase.states` reads `projected["jobs"][0]`. That is correct for a
one-Job fixture and wrong the moment a second Job exists: under the stalling
submission it answered the BLOCKER Job's stages, so the driver never saw
`review` reach `waiting`, never took the turn, and the attempt ended
`exceptional`. The reviewer reproduced it with an instance-only public status
selector; the fixture now makes the same selection by `REVIEW_JOB`.

MY FIRST FIX BROKE PHASE ONE, which is worth recording because it is the same
mistake mirrored. Returning `{}` when no review Job is present meant the
PRODUCER's run -- a one-Job fixture with no review Job at all -- never had its
turn taken either. The override now falls back to the inherited positional
answer exactly where that answer is right.

### What the four conditions look like now

Measured on the stalling submission after the fix: `review: completed`,
`integration: blocked`, `outstanding_cleanup: []`, verdict `accepted`. THREE OF
FOUR hold -- an accountable attempt, no outstanding cleanup, and a Job that is
not terminal.

The fourth does not: `stalled_ticks` is 0 across 241 serving ticks, so the
observation is still changing. That is precisely what the review predicted --
"final cleanup does not establish positive cleanup during six serving
observations" -- and the next step is to find WHEN during serving the cleanup
commits and what else in `_observation(states, accountable, cleanup)` keeps
moving, rather than to assert a stall the run does not reach.

STILL NO ASSERTING NO-PROGRESS CASE. The `stalling` plumbing and the selector
are in the fixture; no test uses them. The eighteen lifecycle cases pass
unchanged, which is what says the selector fix did not disturb the accepted
proofs.

Verification: 108 focused deterministic checks, 0 failures, measured
21.342962219001492s, receipt `verification-15.json` with
`verification-15.log`. No case was added; the broad suite ran because the
selector touches the shared fixture every accepted lifecycle case uses, so
leaving it unrun would have been the reverse mistake.

Cumulative MEASURED (suite receipts only) for W239533: 261.869629151 +
21.342962219 = **283.212591370s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032. Unmeasured ad-hoc
driving remains UNKNOWN and is not estimated.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s, 4.183597788s) are theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 248135 -- the Job selector

Edited in this dossier: `test_review_lifecycle.py`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_248135.py`,
`verification-15.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** The inherited `states` helper in
`tests/tools/test_stage_execution.py` is UNCHANGED -- the selection is
overridden in this dossier's own fixture. The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` and its producer snapshot are unchanged, both images are
unchanged, no deployed store was opened, the disclosed `control.sqlite3-shm`
and zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 248135" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 248135" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
