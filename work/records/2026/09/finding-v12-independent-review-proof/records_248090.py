"""Claim-248090 dossier entries: the no-progress structure, half measured."""
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
  * `main` actually invoked, and the bounded successor-source
    argument/store/survey/submission/outcome proof (2026-09-23T13:35:00Z)

## Done under claim 248090 -- half of the no-progress case, measured

The detector needs four things AT ONCE: an accountable attempt, NO outstanding
cleanup, a non-terminal stage, and an unchanged observation for six ticks. A
single-stage review Job cannot have the third once the review completes.

`stalling_submission` supplies the structure: the review Job gains an
`integration` stage depending on a stage in a SECOND Job that never runs.
MEASURED: `integration` really is `blocked`, the Job is therefore NOT terminal,
and the gate records 240 FOREIGN admissions and ZERO cap refusals -- so the
blocked stage never reaches admission and no cap refusal ends the run for a
different reason. That is the structural half, and it holds.

WHAT DOES NOT YET HOLD: under this two-Job submission the review attempt ends
`exceptional` with `cleanup: None, why: "no committed cleanup"`, so the
cleanup is OUTSTANDING and the detector is correctly suppressed. The remaining
question is narrow and named: why the review attempt fails here when the
same turn settles under the one-Job submission.

No case asserts no-progress, because none can yet. The `stalling` plumbing is
present and unused by any case.

## Next executable milestone

1. Find why the review attempt ends `exceptional` under the two-Job stalling
   submission, and get the same settled turn there; then the four conditions
   are met and the no-progress case can assert them.
2. Owner 247663 item 6: the complete packet, exact commands, provider question
   and honest evidence. It must distinguish the `main` startup proof -- which
   runs a `Deferring` composition with stub image metadata and honestly holds
   with "no runtime was ever admitted" -- from the separate successful
   real-coordination lifecycle. **No successful reviewer run through `main` is
   proved**, and the packet must say so.

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. Outside
the checkout: `/home/sl/baton-runs/independent-review-247947/manager-source`,
built once, read but never rewritten.

## Latest review, evidence and positions read

`review-2026-09-23T13-35-00Z.md`; receipt `verification-14.json`. Last
discussion position read: T239533 message 247805. Last event read: 248086.

## Blockers

None. NOT RUNNABLE until the remaining items are done and the whole
preparation is independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 248090

Review 2026-09-23T13:35:00Z accepted the `main` startup proof and the closure
of the main-never-called finding. Two things remain and this claim advanced the
harder one by half, with the half that does not hold stated plainly.

### The no-progress structure, and what it measured

The detector needs four conditions at once: an accountable attempt, NO
outstanding cleanup, a non-terminal stage, and an unchanged observation for six
ticks. Earlier claims kept reaching three of four -- a settled review has a
terminal stage; a failed one leaves cleanup outstanding -- which is why the
case has stayed open rather than been faked.

`stalling_submission` supplies the missing structure: the review Job gains an
`integration` stage that depends on a stage in a SECOND Job which never runs.
Measured, it does exactly what it should: `integration` is `blocked`, the Job
is therefore not terminal, and the gate records 240 FOREIGN admissions and ZERO
cap refusals -- so the blocked stage never reaches admission and no cap refusal
ends the run for a different reason. A cap refusal would have stopped the run
for something other than the detector and proved nothing.

WHAT DOES NOT HOLD YET, and it is one thing: under this two-Job submission the
review attempt ends `exceptional`, with `cleanup: None, why: "no committed
cleanup"` -- so the cleanup is outstanding and the detector is correctly
suppressed. The same turn settles under the one-Job submission, so the question
is narrow: what about the two-Job shape makes the review attempt fail.

NO CASE ASSERTS NO-PROGRESS, because none can yet. The `stalling` plumbing is
in the fixture and no test uses it. I would rather leave a named half-result
than an assertion about a state the run does not reach.

### The packet's honest distinction, carried forward

The reviewer's note is recorded in the checkpoint as part of item 6: the final
packet must distinguish the `main` startup proof -- a `Deferring` composition
with stub image metadata, honestly holding with "no runtime was ever admitted"
-- from the separate successful real-coordination lifecycle. **No successful
reviewer run through `main` is proved.**

### Spending

Verification: 108 focused deterministic checks, 0 failures, measured
21.34568109900283s, receipt `verification-14.json` with
`verification-14.log`. No case was added.

Cumulative MEASURED (suite receipts only) for W239533: 240.523948052 +
21.345681099 = **261.869629151s**.

SEPARATELY, and not folded into that subtotal: the preliminary 242-second
`main` run recorded under claim 248032, before that case was bounded to 12/4.
It was a real measured run and it is preserved as its own figure rather than
absorbed. Unmeasured ad-hoc driving remains UNKNOWN and is not estimated.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s) are theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 248090 -- the no-progress structure

Edited in this dossier: `test_review_lifecycle.py`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_248090.py`,
`verification-14.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** The product path stays at
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
    if "claim 248090" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 248090" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
