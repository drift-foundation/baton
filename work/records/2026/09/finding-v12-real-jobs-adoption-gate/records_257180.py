"""Claim-257180: the margin counted from the source, and it is 1200s."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 257180; RETURNED INCOMPLETE

Review 2026-09-24T13:36:43Z accepted the reserve routing and found two things.
The margin is corrected and proved; the write-ahead hold is scoped exactly.

## The margin was far too small, and the real number is uncomfortable

"Reclaim has separate stop/remove 120s calls plus inspect/identification."
I had counted one reclaim plus one stop — 125 per act. Counted from the source
instead, ONE reclamation of ONE custody act is **five sequential engine
calls**, each bounded by `CUSTODY_RECLAIM_SECONDS`:

  1. `_reconciled`'s listing (`_list_vector`);
  2. `_reconciled`'s inspection of the candidate it found;
  3. `_reclaimed`'s stop order — its inner `stop_vector` carries
     `CUSTODY_STOP_SECONDS`, but the WAIT is `CUSTODY_RECLAIM_SECONDS`;
  4. `_reclaimed`'s removal order;
  5. `_proved_absent`'s inspection.

An abandonment performs two custody acts, so the margin is
`2 × 5 × CUSTODY_RECLAIM_SECONDS` = **1200 seconds**, derived in
`_reclamation_margin()` and pinned by a case that also proves it MOVES when
the package's bound moves.

**And 1200 is larger than an ordinary two-Job run's whole 600-second budget.**
That is stated rather than tuned away: this supervisor will usually admit
nothing, and the attempt is recorded UNRESOLVED with its runtime untouched and
the operator told why. A shutdown that started an ending it could not finish
would leave exactly the stranded runtime this Work exists to stop leaving.
What would make the number smaller is a supported engine-side settlement,
which W44342 carries and which stays PARKED.

**A second assertion of mine was testing the wrong thing.** I asserted the
allowances fall monotonically. They do not, and should not: each vector is
`min(what is left, ITS OWN ceiling)`, and the ceilings differ — a removal's is
300, a custody act's 2100. The invariant is the PAIR: no vector was ever
allowed more than the budget standing when it was composed, and the budget
itself fell. That is what the case asserts now.

## The write-ahead hold — scoped, not built

Review: a hold written only after a failed call "misses engine-accepted /
process-death-before-record window". Correct: the engine can accept the
request and this process can die before anything is written, and then there is
no hold at all.

What it needs, beyond the four parts recorded last claim:

  1. **PRE-EFFECT**: the uncertainty record is committed BEFORE the engine
     call, not after the failure — a write-ahead intent naming the act about
     to be attempted;
  2. **NONCOLLIDING IMMUTABLE IDENTITIES**: one identity per (attempt, root,
     verb, custodian image, derived helper name), never reused, so two acts
     cannot share a hold and a replay cannot clear another's;
  3. **ATOMIC CHECK AND ACT**: the hold is read and the act authorized in one
     transaction, or a concurrent caller passes the check and acts anyway;
  4. **REUSE AND DELETION GUARDS**: while a hold stands, the root may not be
     reused and nothing may delete it — the guard belongs at the operations
     that would, not only at the custody act;
  5. **STALE-CLEARANCE REJECTION**: a clearance naming a different act, image
     or helper identity is refused rather than accepted as "close enough";
  6. **EXPLICIT OPERATOR EVIDENCE**: the clearance records what the operator
     OBSERVED, not merely that they ran a command.

That is a write-ahead journal kind, a precondition, guards at two other
operations and a new public reconciliation. It is NOT built, and it is named
at that size rather than approximated with more prose.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **46 cases, all passing,
2.529s**, clean under `-W error::ResourceWarning`.
Accepted suites over the changed product files — **966 tests, OK, 22.686s**.
`test_two_jobs` — **85 tests, OK, 69.281s**.

## REMAINING

  1. the write-ahead hold, in its six parts;
  2. store-wait accounting — the actual lock and I/O bounds;
  3. the supervisor timeout and replay proofs through `supervise` with a
     stranded attempt;
  4. first-call crash and launch-absent alternate recovery;
  5. the two operator grants documents with validation and readback;
  6. the executed-image fault diagnosis;
  7. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

No external blocker.

## Standing constraints

No deployed mutation, live rerun, cleanup execution or deletion. The preserved
instance and the snapshot are read-only. W44342 stays parked. Positive cleanup
remains required for adoption.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, `worker_manager/oci.py`,
`worker_manager/custody.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 257180

### I counted the reclamation wrong, and the real number is awkward

You said it plainly: separate stop and remove calls, plus the inspection and
the identification. I had counted 125 seconds per act. Counted from
`_reconciled`, `_reclaimed` and `_proved_absent` instead, one reclamation is
five sequential engine calls each waiting up to `CUSTODY_RECLAIM_SECONDS`, and
an abandonment does two custody acts. The margin is 1200 seconds.

That is larger than an ordinary two-Job run's entire 600-second budget, which
means this supervisor will usually admit nothing. I am not shrinking the
number to make that go away. The fallback is the truthful outcome — unresolved,
runtime untouched, operator told why — because a shutdown that starts an
ending it cannot finish leaves precisely the stranded runtime this Work exists
to stop leaving.

### And an assertion of mine was measuring the wrong thing

I had asserted the allowances fall monotonically. They do not and should not:
each vector is `min(what is left, its own ceiling)`, and a removal's ceiling
is 300 where a custody act's is 2100, so a later vector can legitimately be
larger. The invariant is the pair — allowance plus what had been spent never
exceeds the whole — and the budget itself falls. Fixed, and it caught the
distinction rather than me noticing it.

### The hold needs to be written before the effect

Your window is real: the engine accepts the request, this process dies, and a
hold written only on the failure path never exists. So the six parts are
recorded — write-ahead intent, noncolliding immutable identities, atomic check
and act, reuse and deletion guards at the operations that would do either,
stale-clearance rejection, and operator evidence of what was OBSERVED rather
than what was run. Not built. Named at its real size.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 46 cases, all passing,
**2.529s**, clean under `-W error::ResourceWarning`; 2.540s intermediate.
Accepted suites over the changed files — **966 tests, OK, 22.686s**.
`test_two_jobs` — 85 tests, **OK, 69.281s**.

Neither the 424-case stage-execution suite nor the daemon suites were
repeated. Everything prior stands: 966 OK 22.616s / 22.618s / 22.679s, 121 OK
3.152s, 986 in 38.505s with its 7 daemon failures and the 15.647s pinned
comparison, 899 OK 19.828s, 9.308s, 10.337s, 85 OK 68.787 / 69.017 / 69.207 /
69.262s with the two red predecessors at 31.663s and 31.822s, 159.910s plus
its untimed repeat, 0.966s, 1.170s, 10.041s, 9.966s, 0.348s, 0.130s, 0.094s,
125 OK 4.803/4.805/4.875s, 329 OK 8.405s, the combined focused runs in earlier
entries, the untimed probes and diagnostic reads, the unmeasured ~120s
command-timeout run and the earlier unknowns, alongside named
**1047.869180986s**. The reviewer's 1.869s/1.923110115s is additional.

State: returned INCOMPLETE through baton.bug with the margin counted from the
source, the fallback stated rather than tuned, and seven items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 257180" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
