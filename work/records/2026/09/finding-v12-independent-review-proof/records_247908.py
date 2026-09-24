"""Claim-247908 dossier entries: R1 and R2 closed; no-progress still open."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CHECKPOINT = """# Checkpoint -- W239533

Concise per AGENTS.md "Delivery continuity and bounded context". FINDING keeps
the history.

## Accepted

  * the attachment arrangement and its supported read-only survey
  * the `review_supervisor` specialization's source and the R1/R2 fixes
  * the `correction_policy` product change's source branch; item 5
  * owner 247663 ITEMS 1 AND 2 (2026-09-23T13:04:00Z)
  * the gate-state-at-cancellation observation and the exact outstanding
    attempt identity (2026-09-23T13:10:01Z)

## Done under claim 247908

  * **The total bound is now actually reached.** `withhold=True` admits the
    stage and never takes the turn, so the loop stops on its deadline:
    `stopped: overall-bound-exceeded`, one admitted attempt, stage not
    `completed`. Serving stops at `total - cleanup`; every read of the
    injected clock is recorded and the LAST one is inside `total`, which is
    the statement `served_seconds` cannot make because it is measured before
    cancellation and cleanup. A sensitivity case raises the total far above
    the tick budget and shows the run then does NOT stop on the deadline.
  * **The shutdown interruption is OBSERVED.** The interrupt is injected at
    the composition's cancellation, with the gate already closed and the
    attempt already outstanding; the case asserts the injected point fired
    (`shutdown_reached is True`) rather than inferring the phase, and that the
    published outcome carries the named attempt and its uncertainty before
    `SupervisorInterrupted` is raised.

## Next executable milestone

1. THE ADMITTED NO-PROGRESS CASE, still outstanding and correctly disclosed.
   The reviewer's seam: hold stage advancement at its real transition boundary
   AFTER positive cleanup commits, keep reads and records real, and verify six
   unchanged non-terminal observations with no false timeout attribution. No
   raw store edits, no fabricated cleanup receipts.
2. Owner 247663 items 4 and 6: the distinct digest-bound successor
   manager-source carrying the `correction_policy` change (as
   `../finding-v12-single-implementation-proof/snapshot_242687.py` builds one,
   producer snapshot untouched), `SELECTIONS-239533.json` repointed at it from
   `single-implementation-242687/manager-source` which predates the change,
   the documented preparation and startup against those exact bytes, and the
   complete packet with commands, provider question and evidence.

## Owned paths

This dossier in full, plus one product path under owner selection 247421:
`v12/python/tools/stage_execution.py`, currently
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`.

## Latest review, evidence and positions read

`review-2026-09-23T13-10-01Z.md`; receipt `verification-10.json`. Last
discussion position read: T239533 message 247805. Last event read: 247904.

## Blockers

None. NOT RUNNABLE until the remaining items are done and the whole
preparation is independently accepted.
"""

PROGRESS_ENTRY = """
## 2026-09-23 -- baton.claude, claim 247908

Review 2026-09-23T13:10:01Z accepted the gate-state observation and the exact
outstanding identity, and refused two things. **Both are closed. The admitted
no-progress case remains outstanding and is still disclosed as such.**

### R1 -- the bound cases were not reaching their own condition

The reviewer reproduced the exact operands independently and got
`state=settled, stopped=completed, served_seconds=3.0, cleanup_sweeps=0`. That
is right and the diagnosis is exact: `report=None` falls back to ACCEPTED in
the driver, and `expect=None` only disables the status assertion rather than
the turn -- so both "cannot finish" cases were successful early completions
and neither reached a deadline. `fail_at=10**9` never fired. I had written two
cases that asserted arithmetic about a run that finished normally.

`withhold=True` is the seam that actually withholds the turn after admission.
With it the run stops on its deadline: `overall-bound-exceeded`, ONE admitted
attempt, stage not `completed`. And the total is now checked on the clock
rather than on `served_seconds` -- which is measured BEFORE cancellation and
cleanup and cannot speak for them. Every read of the injected monotonic clock
is recorded, so the case asserts the LAST read of the whole run is inside
`total_seconds`.

A sensitivity case raises the total far above the tick budget and requires
that the run then does NOT stop on the deadline, so the deadline case is
measuring the deadline rather than something that would have held anyway.

### R2 -- the shutdown interruption is observed rather than inferred

"An interruption during serving ... does not substitute for a deliberately
observed interruption in shutdown", and the failure-before-ending path already
supplies the reachable state. The interrupt is now injected AT the
composition's cancellation -- gate already closed, attempt already outstanding
-- and the case asserts the injected point fired (`shutdown_reached is True`)
rather than reading the phase off the outcome. It then asserts that the
PUBLISHED outcome carries the named attempt and its uncertainty, which is the
ordering that matters: the accounting reaches disk before the interrupt is
re-raised.

### Still outstanding, and unchanged

The admitted NO-PROGRESS case. The reviewer's seam is recorded in the
checkpoint: hold stage advancement at its real transition boundary after
positive cleanup commits, keep reads and records real, verify six unchanged
non-terminal observations, and do not attribute a timeout falsely. No raw
store edits and no fabricated cleanup receipts.

Verification: 106 focused deterministic checks, 0 failures, measured
12.534635852993233s, receipt `verification-10.json` with
`verification-10.log`; 3 are new and 2 were replaced rather than added -- the
two bound cases the reviewer refused are gone, not kept beside their
replacements.

Cumulative MEASURED for W239533: 0.432753846 + 0.590057723 + 0.588589542 +
1.167917072 + 1.325346095 + 1.339161638 + 159.751 + 1.295056363 + 5.328163941
+ 9.069514466 + 12.534635853 = **193.422196539s**. Unmeasured ad-hoc driving
across claims 247757, 247823, 247870 and 247908 remains UNKNOWN and is not
estimated. The reviewers' independent measurements (0.571337769s,
0.596305013s, 1.152729417s, 1.311204790s, 1.302250807s, 2.361050477s,
3.324525589s, 4.056475030s, 8.306612300s) are theirs and are preserved
separately.

State: returned for independent review. Ordinary continuation per M247805.
"""

OWNERSHIP = """
## Claim 247908 -- the reached bound and the observed shutdown

Edited in this dossier: `test_review_lifecycle.py`, `verify.py`, `PLAN.md`,
`PROGRESS.md`, this file. Added: `records_247908.py`,
`verification-10.json/.log`.

**No file under `v12/` was edited under this claim.** The product path stays at
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`. W239528's
`baseline.py` is unchanged at its accepted digest. No deployed store was
opened, both images are unchanged, the disclosed `control.sqlite3-shm` and
zero-length `control.sqlite3-wal` are preserved, and every reviewer file in
this dossier is append-only history that was not modified.
"""


def main():
    (HERE / "PLAN.md").write_text(CHECKPOINT, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 247908" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS_ENTRY,
                            encoding="utf-8")
    owner = HERE / "OWNERSHIP-239533.md"
    body = owner.read_text(encoding="utf-8")
    if "Claim 247908" not in body:
        owner.write_text(body.rstrip("\n") + "\n" + OWNERSHIP, encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
