"""Claim-248209 dossier entries: a swallowed interrupt I reintroduced."""
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
  * the unallocated accounting correction and the actual six-tick stall
    (2026-09-23T13:52:06Z)

## Done under claim 248209 -- the R1 regression I introduced

`_serving_origin` used `_guarded(..., interrupted=[])`. `_guarded` catches
`BaseException` and appends the interruption to the list it is handed, and a
DISPOSABLE list discards it -- so a `KeyboardInterrupt` raised while
classifying an origin was swallowed and `should_continue` could keep serving
after an operator had asked the run to stop. This is the same shape W239528's
review 2026-09-23T00:50:59Z R1 found in the progress read, reintroduced by me
in a new place.

It now catches ordinary `Exception` only -- naming the failure as uncertainty
and answering `FOREIGN`, which is not excluded, so the identity keeps its
cleanup obligation -- and lets `BaseException` travel into the shutdown handler
that closes admission, cancels, accounts and publishes.

Two regressions, both injected INSIDE the origin read rather than at `sleep`:
an interrupt there stops the run, publishes the outcome and raises
`SupervisorInterrupted`; and an ordinary failure there keeps the identity
accountable, records the uncertainty and does NOT report no-progress. The
interrupt case asserts at least one admitted attempt rather than exactly one,
because with classification broken the blocked stage's identity is no longer
droppable -- that is the fail-closed rule visible, and asserting exactly one
would have asserted that uncertainty silently shrinks the accountable set.

## Next executable milestone

Owner 247663 item 6, the last one: the complete packet, exact commands,
provider question and honest evidence, distinguishing the
`Deferring`-composition `main` startup proof from the successful
real-coordination lifecycle. **No successful reviewer run through `main` is
proved.**

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. Outside
the checkout: `/home/sl/baton-runs/independent-review-247947/manager-source`,
built once, read but never rewritten.

## Latest review, evidence and positions read

`review-2026-09-23T13-52-06Z.md`; receipt `verification-17.json`. Last
discussion position read: T239533 message 247805. Last event read: 248206.

## Blockers

None. NOT RUNNABLE until item 6 is done and the whole preparation is
independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 248209

Review 2026-09-23T13:52:06Z accepted the unallocated accounting correction and
the six-tick stall, and found a regression in the fix itself. It is the same
defect this project has already been corrected for once, and I put it back.

### The swallowed interrupt

`_serving_origin` used `_guarded(..., interrupted=[])`. `_guarded` catches
`BaseException` and appends the interruption to the list it is given; a
DISPOSABLE list discards it. So a `KeyboardInterrupt` raised while classifying
an origin was swallowed, the predicate returned normally, and serving could
continue after an operator had asked the run to stop.

W239528's review 2026-09-23T00:50:59Z R1 found exactly that shape in the
progress read, and the comment explaining it is a few lines above the one I
wrote. Reaching for `_guarded` because it was the local idiom is how the same
mistake gets a second home.

It now catches ordinary `Exception` only: the failure is named as uncertainty
and the answer is `FOREIGN`, which is not excluded, so the identity keeps its
cleanup obligation. A `BaseException` travels out of the predicate, out of
`serve`, and into the shutdown handler that already closes admission, cancels,
accounts and publishes.

### Two regressions, in the right branch

Both are injected INSIDE the origin read, which the review correctly noted is
a different branch from the `sleep` the other interruption cases use.

An interrupt there stops the run, publishes the outcome and raises
`SupervisorInterrupted` -- asserted on the PUBLISHED file, not only the
exception. An ordinary failure there keeps the identity accountable, records
the uncertainty, and does NOT report no-progress.

The interrupt case asserts AT LEAST one admitted attempt rather than exactly
one. With the classification broken the blocked stage's identity can no longer
be shown `unallocated`, so it is not dropped -- that is the fail-closed rule
visible, and asserting exactly one would have been asserting that uncertainty
silently shrinks the accountable set, which is the thing the rule exists to
prevent.

Verification: 113 focused deterministic checks, 0 failures, measured
36.40780342000653s, receipt `verification-17.json` with
`verification-17.log`; 2 are new. The suite is slower because the two new
cases drive whole runs whose origin reads fail.

Cumulative MEASURED (suite receipts only) for W239533: 306.861458471 +
36.407803420 = **343.269261891s**. Separately and not folded in: the
preliminary 242-second `main` run under claim 248032. Unmeasured ad-hoc driving
remains UNKNOWN and is not estimated.

The reviewers' independent measurements (0.571337769s, 0.596305013s,
1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s, 3.324525589s,
4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s, 0.770625345s,
8.602200050s, 4.183597788s, 2.115041870s, 2.201875895s) are theirs and are
preserved separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 248209 -- the origin read, corrected

Edited in this dossier: `review_supervisor.py`, `test_review_lifecycle.py`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added:
`records_248209.py`, `verification-17.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** The change is in this dossier's own supervisor.
`baseline._guarded` is UNCHANGED and still imported for the places where
catching `BaseException` into a real `interrupted` list is what is wanted; what
changed is that this one call no longer uses it. The product path stays at
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
    if "claim 248209" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 248209" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
