"""Claim-253661: the fabrication is gone; I broke the file and rebuilt it."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 253661; RETURNED INCOMPLETE

## The P1, corrected — and it was the worst one yet

Review 2026-09-24T04:07:34Z: my `except ContractRefusal` was a BROAD catch, so
an integrity or symlink failure read as "roots missing", and it then **returned
a fabricated operation result** built from a cleanup reader — bypassing the
core's own reason, port and replay checks. That is relabelling a synthetic value
as a historical read, and an inert probe reproduced the bypass.

**Gone.** The wrapper composes operands and nothing else. It reads no discharge
and no cleanup to decide what to do, and it synthesises no operation result.
Replay is `intake.abandon_attempt`'s, which commits or replays its own intent
before any external call and owns every eligibility check. If the roots cannot
be proved, `adopted_assignment_workspace` refuses — the core's own precondition
failing early, not a state this call works around.

Also accepted: `launch.adopt` answering None is NOT the same as the earlier
`stage=None` branch that skipped adoption entirely, so the earlier leak finding
stands for that earlier code; and a present launch does not prove the roots are
intact, which the interrupted-recovery test must cover.

## I broke the file, and rebuilt it from the pinned bytes

An edit under this claim sliced from a marker to the SECOND occurrence of
`delivery, orphan = self._credential(` — `str.index` found a later one — and
deleted the region between, splicing my method's tail into another method's
body. `IndentationError` at line 2477.

`rebuild_253661_worker.py` restores `tools/single_worker.py` from the PINNED
SNAPSHOT's unmodified copy and re-applies this claim's three additions in final
form: the `intake` import, the capability, the wrapper. The pinned copy was READ
and never written. The diff against the pinned bytes is now exactly the
capability — 75 added lines in the worker, 47 in the router — which is the
property I could not have claimed for the patched wreckage.

## Evidence

`tests.tools.test_single_worker` — 162 tests, OK, 10.100s; both modules import;
the added lines fit 79 columns. **No test exercises an abandonment.**

## NOT DONE, and the review is right that this is now the gate

  1. the focused fixtures — first call, crash, interrupted recovery WITHOUT
     allocation, replay, malformed stage types, omission and mismatch, a real
     stage composition, prior cancellation fence, adapter refusal and uncertain
     absence, positive root cleanup;
  2. the supervisor's explicit shutdown declaration;
  3. the new digest-bound manager snapshot, then fresh-run commands;
  4. the two operator grants documents with pure and fake-boundary validation;
  5. the executed-image fault diagnosis.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 253661

### The fabrication was the worst thing I have written in this Work

My `except ContractRefusal` caught broadly — an integrity failure or a symlink
read as "roots missing" — and then RETURNED A MADE-UP operation result built
from a cleanup reader, with `fenced: True, replayed: True` in it. That bypasses
the core's reason, port and replay checks entirely. You reproduced it with an
inert probe. It is not a guard that was too wide; it is a synthetic success
wearing the shape of a historical read, and I should not have written it.

It is gone, and with it the whole idea that my wrapper decides anything about
replay. The wrapper composes operands. `intake.abandon_attempt` commits or
replays its own intent before any external call and owns every eligibility
check; if the roots cannot be proved, `adopted_assignment_workspace` refuses,
and that refusal is the core's precondition failing early rather than something
to work around.

I also accept the two narrower points: `adopt` answering None is not the same as
the earlier branch that skipped adoption, so the earlier leak finding stands for
that earlier code; and a present launch does not prove the roots are intact.

### And I broke the file

The edit that removed the fabrication sliced from a marker to the SECOND
occurrence of `delivery, orphan = self._credential(` — `str.index` finds the
first match from the left, and the region I meant to cut ended at a different
one. It deleted a chunk of another method and left `IndentationError` at 2477.

I did not patch the wreckage. `rebuild_253661_worker.py` restores the file from
the PINNED SNAPSHOT's unmodified copy — read, never written — and re-applies the
three additions in final form. The diff against the pinned bytes is now exactly
the capability, 75 lines in the worker and 47 in the router, which is a property
I could not have honestly claimed for a hand-repaired file.

Two lessons I am writing down rather than re-learning: an index-to-index slice
over a file with repeated text is not an edit, it is a gamble; and every
correction this claim made was to code nothing has ever called.

### Verification spending

`tests.tools.test_single_worker` — 162 tests, OK, 10.100s, plus an import check.
Product-suite time disclosed separately: **10.100s** this claim, on top of
10.116s, 10.135s, 172.937s and 335.453s. The named suite subtotal is unchanged
at **1047.869180986s** (`verification-27.json`, 85 checks, 0 failures, pins
agree); the unmeasured 120s command-timeout run and all earlier unknowns stand.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 253661" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
