"""Claim-248032 dossier entries: main really invoked; item 4 complete."""
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
  * the successor-only subprocess composition and the 106-file packet
    manifest (2026-09-23T13:25:28Z)

## Done under claim 248032 -- item 4's startup, actually through `main`

`review_supervisor.main` is now INVOKED with the documented `--packet` and
`--incarnation`, under successor-only imports, with two of its own seams
supplied so nothing starts: `image_inspect` (no engine) and `compose` (no
container). Everything else is real -- packet validation, the imported-source
check, the Job and control stores, the pre-submission survey, and the
supervised run that publishes an outcome. `main` returns 1 and the outcome on
disk is `held` with "no runtime was ever admitted", which is the honest answer
for a composition that starts nothing.

The previous case called the three startup checks individually and the page,
the handoff and PLAN all said `main` had run. It had not. Corrected, and the
correction is recorded rather than quietly replaced.

## Next executable milestone

1. THE ADMITTED NO-PROGRESS CASE: positive cleanup COMMITTED under a stage
   still short of terminal, held at its real transition boundary, six
   unchanged observations, no false timeout attribution, no raw store edits
   and no fabricated receipts.
2. Owner 247663 item 6: the complete packet, exact commands, provider question
   and execution evidence.

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. Outside
the checkout: `/home/sl/baton-runs/independent-review-247947/manager-source`,
built once, read but never rewritten.

## Latest review, evidence and positions read

`review-2026-09-23T13-25-28Z.md`; receipt `verification-13.json`. Last
discussion position read: T239533 message 247805. Last event read: 248021.

## Blockers

None. NOT RUNNABLE until the remaining items are done and the whole
preparation is independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 248032

Review 2026-09-23T13:25:28Z accepted the successor-only composition and the
exact packet manifest, and refused a claim of mine that was simply false.

### The startup case never called `main`, and three documents said it did

It called `held_packet`, `verify_imported_sources` and `verify_worker_image`
individually and then printed success. The case name, its docstring, the
handoff comment and PLAN all said `main` had run. Naming a check after an entry
point it never enters is worse than no claim at all, and the reviewer was right
to refuse it.

`main` is now invoked with the documented `--packet` and `--incarnation`, under
successor-only imports, with two of ITS OWN seams supplied so that nothing can
start: `image_inspect`, so no engine is reached, and `compose`, so no container
can be. Everything else is real -- the packet validation, the imported-source
check, the Job and control stores, `survey`, and the supervised run that
publishes an outcome. `main` returns 1; the outcome on disk is `held` with "no
runtime was ever admitted", which is the honest answer for a composition that
starts nothing, and the case asserts exactly that rather than accepting any
non-refusal.

The case also asserts it did NOT exit 2, because 2 is "refused before anything
opened" -- and a startup proof that only showed the program refusing early
would be the same empty claim in a different shape.

### One thing the first working version got wrong about cost

At the packet's own 300/60 bounds, `main` served on the REAL wall clock for
242 seconds to prove a startup path. There is no injected monotonic through the
documented entry point and there should not be, so the case now composes 12/4
bounds and proves the same path in seconds. The ARITHMETIC of the bounds is
proved separately on a controlled clock in
`test_review_lifecycle.TheTotalBoundHoldsWhenTheRunCannotFinish`; this case is
about the entry point, not the numbers.

`OPERATOR-239533.md` now states what has been executed at its real width, and
records that an earlier version of the page claimed `main` had run when it had
not.

Verification: 108 focused deterministic checks, 0 failures, measured
21.35032132201013s, receipt `verification-13.json` with
`verification-13.log`. The count is unchanged because the case was REPLACED
rather than added; the measured time rose because it now really runs the
supervisor.

Cumulative MEASURED for W239533: 219.173626730 + 21.350321322 =
**240.523948052s**. Unmeasured ad-hoc driving remains UNKNOWN and is not
estimated. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s,
3.324525589s, 4.056475030s, 8.306612300s, 4.491119177s, 0.008175629s,
0.770625345s) are theirs and are preserved separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 248032 -- the startup, through `main`

Edited in this dossier: `test_review_bindings.py`, `OPERATOR-239533.md`,
`verify.py`, `PLAN.md`, `PROGRESS.md`, this file. Added:
`records_248032.py`, `verification-13.json/.log`.

**No file under `v12/` was edited under this claim and the successor snapshot
was not modified.** It was READ, with `PYTHONPATH` bound to it. The product
path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, W239528's
`baseline.py` and its producer snapshot are unchanged, both images are
unchanged, no deployed store was opened -- the Job and control stores `main`
opened are the disposable fixture's -- the disclosed `control.sqlite3-shm` and
zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 248032" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 248032" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
