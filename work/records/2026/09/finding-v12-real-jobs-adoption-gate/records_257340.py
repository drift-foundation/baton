"""Claim-257340: the hold, end to end, and no accepted rule superseded."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 257340; RETURNED INCOMPLETE

Review 2026-09-24T13:58:36Z resolved the design question I returned, and its
distinction turned out to make the supersession unnecessary. The hold is
implemented end to end.

## The line the review drew, and where it put the write

"The hold is for ACTUAL ENGINE UNCERTAINTY", and "same-act identity does not
authorize resubmission of unresolved daemon request". That places the
write-ahead **inside `custody_act`, immediately before the request crosses** —
not around the adapter call, where I had put it.

**That is why no accepted rule needed superseding after all.** Everything
before the submission — a capability that raises, a malformed operand, a root
that does not exist — is pre-submission and still commits nothing, so
`test_an_unaccountable_answer_commits_nothing` holds unchanged. The
interrupted-normalization resume cases interrupt with a fake custodian that
raises BEFORE any submission, so they resume exactly as before. I had the
authority to append a bounded supersession and to update those tests, and did
not need it: **966 accepted tests pass with no test edited.**

## What the hold is now

  * **written before the submission** and cleared when the engine answers at
    all — a refused or unaccountable ANSWER is this manager's judgement about
    a helper that ran and exited, which is a different fact from silence;
  * **classified structurally**, not by exception type or string: the
    uncertainty is `status is None`, no engine answer, which `custody_act`
    already mints;
  * **binding on a NEW act** — a standing episode refuses the next submission
    over that root, naming the helper it would have created and saying the
    root is frozen: not acted on, not reused, not deleted on the strength of
    that act;
  * **per root, not per attempt** — asserted;
  * **episode-bearing identities**, so a second uncertainty is its own fact
    and the clearance already written does not cover it;
  * **fail-closed reading**: the record's kind, state and document are each
    checked, an unreadable hold or clearance refuses rather than being read
    past, and overflow past `_MOST_HOLDS` refuses;
  * **an operator clearance requiring what was OBSERVED**, refusing a blank
    observation, an episode that does not exist, and one naming a different
    helper.

## Corrected: my "five of six" was overstated

The reviewer is right. Last claim's case covered empty, missing and blank
inputs only — no actual hold, clear, restart or guard. This claim's cases
drive a REAL external uncertainty through the composition's own adapter: the
episode is written, the next act refuses, a reconciliation lifts exactly one
episode, the act then proceeds, and a second uncertainty becomes episode two.

## REMAINING

  1. reuse and deletion guards — `workspaces.py` and the other paths that
     would reuse or delete a held root, to be enumerated and coordinated
     before edits, exactly as `oci.py` and `custody.py` were;
  2. store-wait accounting — the actual lock and I/O bounds;
  3. the supervisor timeout and replay proofs through `supervise` with a
     stranded attempt;
  4. first-call crash and launch-absent alternate recovery;
  5. the two operator grants documents with validation and readback;
  6. the executed-image fault diagnosis;
  7. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

No external blocker.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **49 cases, all passing,
2.842s**, clean under `-W error::ResourceWarning`.
Accepted suites over the changed product files — **966 tests, OK, 22.607s**,
with no accepted test edited.
`test_two_jobs` — **85 tests, OK, 69.194s**.

## Standing constraints

No deployed mutation, live rerun, cleanup execution or deletion. The preserved
instance and the snapshot are read-only. W44342 unchanged and still parked.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, `worker_manager/oci.py`,
`worker_manager/custody.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 257340

### Your distinction made the supersession unnecessary

I returned a design question: hold for every unaccountable answer or only the
unresolved one, and does it block a resume. You answered both — actual engine
uncertainty, and the same act may not resubmit — and that answer placed the
write-ahead somewhere I had not tried: INSIDE `custody_act`, immediately
before the request crosses.

With it there, everything pre-submission still commits nothing, so
`test_an_unaccountable_answer_commits_nothing` holds untouched; and the
interrupted-normalization resumes interrupt before any submission, so they
resume as they always did. You granted me authority to append a bounded
supersession and update those tests. I did not need it. 966 accepted tests
pass with no test edited, which is a better outcome than the one I was
authorized to take.

### And you were right that I overstated the last claim

"Five of six" was not true: that case covered empty, missing and blank inputs
and nothing else — no hold, no clearance, no restart. This claim's cases drive
a real external uncertainty through the composition's own adapter, then prove
the episode exists, the next act refuses, one reconciliation lifts exactly one
episode, the act proceeds afterwards, and a second uncertainty becomes its own
episode.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 49 cases, all passing,
**2.842s**, clean under `-W error::ResourceWarning`; 2.167s intermediate.
Accepted suites over the changed files — **966 tests, OK, 22.607s**, and
22.662s on the intermediate run that proved the placement.
`test_two_jobs` — 85 tests, **OK, 69.194s**.

Neither the 424-case stage-execution suite nor the daemon suites were
repeated. Everything prior stands: 966 OK 22.565/22.616/22.618/22.679/22.686/
22.750s and the 22.798s run with 6 failures that produced the last finding,
121 OK 3.152s, 986 in 38.505s with its 7 daemon failures and the 15.647s
pinned comparison, 899 OK 19.828s, 9.308s, 10.337s, 85 OK 68.787/68.953/
69.017/69.207/69.215/69.262/69.281s with the two red predecessors at 31.663s
and 31.822s, 159.910s plus its untimed repeat, 0.966s, 1.170s, 10.041s,
9.966s, 0.348s, 0.130s, 0.094s, 125 OK 4.803/4.805/4.875s, 329 OK 8.405s, the
combined focused runs in earlier entries, the untimed probes and diagnostic
reads, the unmeasured ~120s command-timeout run and the earlier unknowns,
alongside named **1047.869180986s**. No reviewer measurement this increment.

State: returned INCOMPLETE through baton.bug with the hold implemented end to
end, no accepted rule superseded, and seven items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 257340" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
