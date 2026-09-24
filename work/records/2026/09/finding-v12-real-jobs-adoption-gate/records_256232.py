"""Claim-256232: rounding corrected, two claims withdrawn, the gap closed."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 256232; RETURNED INCOMPLETE

Review 2026-09-24T11:02:29Z found three things. All three were mine, and all
three are answered.

## R1 — the allowance could exceed what was left

Reproduced exactly: `allowed(lambda: 0.1, 120)` answered **1**. Rounding UP
hands a boundary more time than the caller has, which is the one direction an
allowance may never round. My reason for it — that rounding down turns a real
remainder into an immediate refusal — was solving the wrong problem: a caller
with a tenth of a second left should not be STARTING anything.

It rounds DOWN now and never exceeds what is left, asserted across the range
including the reviewer's own counterexample. And the "should not be starting"
half is where it belongs: **`ABANDONMENT_RESERVE_SECONDS = 30`** in the
supervisor. Below that, nothing new starts and the attempt is recorded
unresolved with its runtime untouched and the reserve named in its reason.

**The three unbounded vectors are closed.** They were the label listing and
the observation inside `recover_credentials`, and the observation `_removed`
takes after its removal. `test_every_vector_of_a_bounded_ending_carries_the_allowance`
was an expected failure; it is an ordinary passing case now.

## R2 — "reaped, therefore no background effects" is WITHDRAWN

I wrote that the engine port's contract ("terminated AND REAPED its child")
means a timeout leaves nothing running. This package says the opposite in as
many words, in `custody._recovered`: "Docker is client/server…
`subprocess.run(timeout=)` terminates and reaps the local CLI, which is all it
can do and all this module ever had a right to claim; the daemon's
already-accepted request is a different process and may still create the
derived name afterwards."

So reaping the client is not settling the request, which is exactly why
`custody_act` answers UNRESOLVED rather than absent. **The precise
prerequisite, for disposition:** a provider that can settle or CANCEL the
engine-side operation rather than merely reap its local client —
`custody._recovered` names it and assigns it to **W44342**. Until that exists,
a bounded ending reserves reclamation margin and reports the attempt
unresolved rather than claiming a quiet world. `PATHS-256145.md` carries the
withdrawal and the prerequisite.

## R3 — "local store, no wait" is WITHDRAWN

I wrote that `launch.py`, `workspaces.py` and the Authority/control stores have
"no wait to bound" because they are local. A local SQLite store blocks on a
lock another connection holds, and a directory proof blocks on I/O. The honest
statement is narrower and is now on the page: they take no `seconds` OPERAND
today, and what bounds them is the store's own busy handling. The allowance
covers them as ELAPSED time — it is read at each boundary, so time a lock
consumed is time the next vector does not get. Establishing their actual bounds
is owed work rather than something to assert away.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **42 cases, all passing,
2.436s**, clean under `-W error::ResourceWarning`, no expected failures left.
Accepted suites over the changed product files — `test_custody`,
`test_abandoned_attempt_engine`, `test_intake`, `test_attempts`,
`test_runtime_deadlines`, `tests.tools.test_single_worker` — **966 tests, OK,
22.618s**. `test_two_jobs` — **85 tests, OK, 69.262s**. Per the review, the
daemon-dependent suites were not repeated.

## REMAINING

  1. the owner's remaining acceptance cases: timeout after a durable commit,
     replay without duplicate effects, and all of it through `supervise` with
     a stranded attempt;
  2. actual lock and I/O bounds for the store steps (R3's second half);
  3. first-call crash and launch-absent alternate recovery;
  4. the two operator grants documents with validation and readback;
  5. the executed-image fault diagnosis;
  6. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

Plus the W44342 disposition from R2. No external blocker.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the snapshot are read-only.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, `worker_manager/oci.py`,
`worker_manager/custody.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 256232

### The rounding was wrong in the one direction that matters

`allowed(lambda: 0.1, 120) == 1`. You reproduced it and you were right: an
allowance may never hand a boundary more time than the caller has. I had
reasoned myself into ceil by worrying that a sub-second remainder would refuse
immediately — which is the correct behaviour, not a problem to solve. The fix
is floor plus a stated admission reserve of 30 seconds, so a shutdown does not
start an ending it cannot pay for and keeps margin for the reclamation.

And the three unbounded vectors are closed: the listing and the observation
inside credential recovery, and the observation after the removal. That case
was an expected failure last claim and is an ordinary passing one now.

### Two claims of mine that the source contradicts

**"Reaped, therefore no background effects."** `custody._recovered` says the
opposite, explicitly, and names W44342 as carrying the missing capability: the
CLI can reap its local client and nothing more, and the daemon's accepted
request may still create the helper afterwards. Withdrawn, with the
prerequisite stated for disposition rather than worked around. I should have
found that paragraph before writing the sentence — it is in a file I own.

**"Local store, no wait."** A SQLite lock and a filesystem read are waits. The
page says the narrower true thing now: no `seconds` operand today, bounded by
the store's own busy handling, covered by the allowance as elapsed time
because it is read at each boundary rather than divided in advance.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 42 cases, all passing,
**2.436s**, clean under `-W error::ResourceWarning`; intermediates 1.549s,
1.719s, 2.386s.
Accepted suites over the changed files — **966 tests, OK, 22.618s**.
`test_two_jobs` — 85 tests, **OK, 69.262s**. The daemon-dependent suites were
not repeated, as directed.

The 424-case stage-execution suite was NOT repeated either. Everything prior
stands: 986 in 38.505s with its 7 daemon failures and the 15.647s pinned
comparison, 899 OK 19.828s, 9.308s, 10.337s, 85 OK 68.787s and 69.207s with
the two red predecessors at 31.663s/31.822s, 159.910s plus its untimed repeat,
0.966s, 1.170s, 10.041s, 9.966s, 0.348s, 0.130s, 0.094s, 125 OK
4.803/4.805/4.875s, 329 OK 8.405s, the combined focused runs in earlier
entries, the untimed probes and diagnostic reads, the unmeasured ~120s
command-timeout run and the earlier unknowns, alongside named
**1047.869180986s**. The reviewer's 1.715s/1.774496116s and the 0.023185131s
clamp probe are additional.

State: returned INCOMPLETE through baton.bug with R1 corrected, R2 and R3
withdrawn with their prerequisites named, and six items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 256232" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
