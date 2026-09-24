"""Claim-247870 dossier entries: item 3's exact gaps, less the no-progress one."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CHECKPOINT = """# Checkpoint -- W239533

Kept concise per AGENTS.md "Delivery continuity and bounded context".
FINDING keeps the history; this is the working state.

## Accepted

  * the attachment arrangement and its supported read-only survey
  * the `review_supervisor` specialization's source and the R1/R2 fixes
  * the `correction_policy` product change's source branch
  * the twelve pre-existing product errors, corroborated focally (item 5)
  * owner 247663 ITEMS 1 AND 2: deterministic real-coordination success and
    the `changes-requested` zero-round path (2026-09-23T13:04:00Z)

## Done under claim 247870 -- item 3, less one case

Added to `test_review_lifecycle.py`, all over an ADMITTED attempt:

  * the gate stamps its own `stopped` state onto every act, so "admission
    closed before cancellation" is read off a trace rather than inferred from
    final counts; cancellation is watched on the COMPOSITION, because
    `_cancel_active` is handed that rather than the gate;
  * a closed gate is OFFERED an admission and refuses it;
  * the total bound is arithmetic on a controlled clock: serving stops at
    `total - cleanup` and `served_seconds` never exceeds `total`;
  * the outstanding attempt is named EXACTLY -- identity, `cleanup: None`, and
    that identity present in `held_because`;
  * an interruption with that attempt outstanding still runs the accounting,
    names it, and publishes the outcome before re-raising.

## Next executable milestone

1. THE ADMITTED NO-PROGRESS CASE, which is item 3's one remaining property.
   Its preconditions are known and are why it has not been reached: the
   detector requires an accountable attempt AND no outstanding cleanup AND a
   non-terminal stage AND an unchanged observation for six ticks. A settled
   review has a terminal stage; a failed one leaves cleanup outstanding. The
   state that satisfies all four is a committed cleanup under a stage that
   cannot advance -- W239528's real stall -- and reaching it deterministically
   needs the ending to settle while the stage is held short of `completed`.
2. Then owner 247663 items 4 and 6: the distinct digest-bound successor
   manager-source carrying the `correction_policy` change (built as
   `../finding-v12-single-implementation-proof/snapshot_242687.py` builds one,
   producer snapshot untouched), `SELECTIONS-239533.json` pointing at it
   instead of `single-implementation-242687/manager-source` which predates the
   change, the documented preparation and startup against those exact bytes,
   and the complete packet with commands, provider question and evidence.

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`.

## Latest review, evidence and positions read

`review-2026-09-23T13-04-00Z.md`; this claim's receipt is
`verification-9.json`. Last discussion position read: T239533 message 247805.
Last event read: 247859.

## Blockers

None. The packet remains NOT RUNNABLE until the remaining items are done and
the whole preparation is independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247870

Review 2026-09-23T13:04:00Z accepted items 1 and 2 and called item 3 PARTIAL,
naming four gaps. **Three of the four are now closed; the fourth is the
admitted no-progress case and its exact preconditions are recorded rather than
approximated.** Read current canonical detail, the handoff since 247847 and
the review; positions are in the checkpoint.

### The gate-order objection was right

"Gate-order test checks only final counts; that cannot establish gate closed
before cancellation in a single-stage Job." It cannot -- a count is the end of
a run and the question is about an instant during it. The gate now stamps its
own `stopped` state onto every act it performs, and the cancellation is watched
on the COMPOSITION rather than on the gate, because `_cancel_active` is handed
the composition. So the order is read off a trace: every admitting act happened
with the gate open, every cancellation with it closed, and nothing admitting
follows the first cancellation. A closed gate is also OFFERED an admission and
refuses it, which is a stronger statement than "none arrived".

THE SEAM IS `review_supervisor.AdmissionGate`, NOT `baseline`'s. The recording
gate is a subclass of the real imported one and the patch is on the name this
module under test resolves; W239528's module is untouched and
`test_review_supervisor` still parses this program to hold it to that.

### The other two gaps

The total bound is now arithmetic on the controlled clock: `serving_bound_seconds`
equals `total - cleanup` and `served_seconds` never exceeds `total`. And the
outstanding attempt is named EXACTLY -- its identity, its `cleanup: None`, and
that identity appearing in `held_because` -- rather than counted.

### What is NOT done, and why it is not approximated

The admitted NO-PROGRESS case. The detector requires four things at once: an
accountable attempt, NO outstanding cleanup, a non-terminal stage, and an
unchanged observation for six ticks. A settled review has a terminal stage; a
failed one leaves cleanup outstanding. The state that satisfies all four is a
committed cleanup under a stage that cannot advance -- which is W239528's real
stall -- and reaching it deterministically needs the ending to settle while the
stage is held short of `completed`. I would rather record that precondition
than assert no-progress from a state that does not have it.

The cleanup-WINDOW interruption is in the same category and is stated in the
case that replaced it: a settled run leaves nothing outstanding, so the window
breaks before it sleeps and an interrupt injected through `sleep` never reaches
it. What is reachable -- and is the property that matters -- is an interruption
while an admitted attempt is still outstanding, which is covered.

### The probe estimate, withdrawn

Review 2026-09-23T13:04:00Z: "Historical ~20s probe estimate is not an
established upper bound; actual unknown". Correct -- I derived it from a later
suite's cost, which is not a measurement of those runs. The record now says
**unknown and unmeasured** rather than carrying a number that reads like one.

Verification: 103 focused deterministic checks, 0 failures, measured
9.069514465998509s, receipt `verification-9.json` with `verification-9.log`;
7 are new.

Cumulative MEASURED for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 + 1.295056363 + 5.328163941
+ 9.069514466 = **180.887560686s**. Unmeasured ad-hoc driving across claims
247757, 247823 and 247870 is UNKNOWN and is not estimated. The reviewers'
independent measurements (0.571337769s, 0.596305013s, 1.152729417s,
1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s, 4.056475030s) are
theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 247870 -- item 3's gate order, bounds and exact outstanding identity

Edited in this dossier: `test_review_lifecycle.py`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_247870.py`,
`verification-9.json/.log`.

**No file under `v12/` was edited under this claim.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. W239528's
`baseline.py` is unchanged at its accepted digest: the recording gate
SUBCLASSES `baseline.AdmissionGate` and the patch is on
`review_supervisor.AdmissionGate`, the name this module under test resolves.
No deployed store was opened, both images are unchanged, the disclosed
`control.sqlite3-shm` and zero-length `control.sqlite3-wal` are preserved, and
every reviewer file in this dossier is append-only history that was not
modified.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247870" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247870" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
