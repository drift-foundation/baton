"""Claim-248173 dossier entries: the no-progress case, and the defect under it."""
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

## Done under claim 248173 -- owner 247663 item 3's last property

THE ADMITTED NO-PROGRESS CASE ASSERTS, and the obstacle was a defect in this
supervisor rather than in the fixture.

`should_continue` built its accountable set from the gate's launches and the
projection without classifying origins, while the shutdown's `classify()` drops
an identity whose origin is `UNALLOCATED`. So the blocked stage's projection
identity was counted OUTSTANDING every serving tick and EXCLUDED at shutdown --
two accounts of one set, and the outstanding condition could therefore never
empty, which suppressed the rule permanently. Review 2026-09-23T13:46:58Z
traced it over 42 real cleanup reads and was right that `stalled 0` did not
mean the observation kept changing.

Serving now classifies through the same `_origin` the shutdown uses, and FAILS
CLOSED: a read that does not complete answers `FOREIGN`, which is not excluded,
so an identity this run cannot classify keeps its cleanup obligation.

Measured: `stopped: no-progress`, `stalled_ticks: 6`, `outstanding_cleanup: []`,
`review: completed`, `integration: blocked`, and served 9 seconds of a
300-second bound instead of 241. Three cases assert it, including the negative
one: a genuinely outstanding runtime is never dropped and no-progress must NOT
fire there.

## Next executable milestone

Owner 247663 item 6: the complete packet, exact commands, provider question and
honest evidence, distinguishing the `Deferring`-composition `main` startup
proof from the successful real-coordination lifecycle. **No successful reviewer
run through `main` is proved.**

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. Outside
the checkout: `/home/sl/baton-runs/independent-review-247947/manager-source`,
built once, read but never rewritten.

## Latest review, evidence and positions read

`review-2026-09-23T13-46-58Z.md`; receipt `verification-16.json`. Last
discussion position read: T239533 message 247805. Last event read: 248170.

## Blockers

None. NOT RUNNABLE until item 6 is done and the whole preparation is
independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 248173

Review 2026-09-23T13:46:58Z diagnosed the suppression exactly, over 42 real
cleanup reads, and the cause was a defect in MY supervisor rather than in the
fixture. **The admitted no-progress case now asserts, and owner 247663 item 3
is complete.**

### Two accounts of one set

`should_continue` built its accountable set from the gate's launches and the
projection and classified nothing. The shutdown's `classify()` drops an
identity whose origin is `UNALLOCATED` -- "an identity the manager answers no
row for, that this run never launched, is not a runtime". So the blocked
stage's projection identity was counted OUTSTANDING on every serving tick and
EXCLUDED at shutdown. The outstanding condition could therefore never empty,
and the no-progress rule could never fire, no matter what the run did.

I had also inferred the wrong thing from the same evidence last claim:
`stalled_ticks 0` does NOT mean the observation kept changing. The reviewer
said so plainly and the trace shows it -- the review attempt was already
`retained`/`absent` DURING serving, and the extra identity alone held the set
open.

Serving now classifies through the same `_origin` the shutdown uses. IT FAILS
CLOSED: a read that does not complete answers `FOREIGN`, which is not excluded,
so an identity this run cannot classify keeps its cleanup obligation. Dropping
on uncertainty would invent the very quiet the detector then reports, which is
why the fix is not a filter.

### What it measures now

`stopped: no-progress`, `stalled_ticks: 6`, `outstanding_cleanup: []`,
`review: completed`, `integration: blocked`, every cleanup positive, and the
run served 9 seconds of a 300-second bound instead of 241. Reporting a stall
when it happens rather than waiting the backstop out is the whole purpose of
the rule, and the case asserts the elapsed time as well as the reason.

Three cases: the four conditions each asserted rather than assumed; the
excluded identity reported as `unallocated` and present in `observed_attempts`
but not in `admitted_attempts`, so it is excluded rather than ignored; and the
NEGATIVE case -- a run whose ending never settles keeps its real outstanding
runtime, and no-progress must not fire there.

Verification: 111 focused deterministic checks, 0 failures, measured
23.648867101001088s, receipt `verification-16.json` with
`verification-16.log`; 3 are new.

Cumulative MEASURED (suite receipts only) for W239533: 283.212591370 +
23.648867101 = **306.861458471s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032. Unmeasured ad-hoc driving
remains UNKNOWN and is not estimated.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s, 4.183597788s, 2.115041870s) are theirs and are preserved
separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 248173 -- the serving classification, aligned

Edited in this dossier: `review_supervisor.py`, `test_review_lifecycle.py`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added:
`records_248173.py`, `verification-16.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** The change is in this dossier's own supervisor: it now
calls the SAME `_origin` the shutdown path already used, which is W239528's
accepted helper imported unchanged. The product path stays at
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
    if "claim 248173" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 248173" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
