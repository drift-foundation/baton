"""Claim-256145: one decreasing allowance, enforced where it can be."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 256145; RETURNED INCOMPLETE

Owner reroute 256143 selected the qualified deadline correction, superseding
`BOUND-256097.md`'s per-step sketch, and granted `oci.py` and `custody.py` on
the condition that the required paths be enumerated first.

## The enumeration came first — `PATHS-256145.md`

Every step one abandonment crosses, in order, with its file and whether it was
owned; the four boundaries that needed the two new files; and every other file
in the chain together with the reason it needs no edit — `launch.py` and
`workspaces.py` have no wait, the Authority is a local store, `documents.py` is
deliberately untouched so execution control never enters a signed document, and
`deadlines.py` is a different owner's bound for a different ending.

**One enumeration answer was wrong and is corrected on the page.** I wrote that
no accepted test needs a change. Two do: `tests/manager/test_custody.py` pins
`custody_act`'s parameter list twice as a signature guard. So the operand was
NOT added there — the allowance reaches the custody act through the engine
PORT, which clamps every vector the act issues, and the accepted guard stays
true with no unowned test edited.

## The allowance

`custody.allowed(seconds, most)` is the whole rule: `None` is today, a bounded
caller may only ask for LESS than the package's own maximum, and the result is
a whole number rounded UP so a fraction left is a second rather than none.

Threaded: the adapter clamps its removal and its observation;
`oci.normalize_directory` wraps the engine port when bounded;
`intake.abandon_attempt` carries it to the removal and BOTH custody acts —
read at each boundary, so the second root gets what the first left rather than
a fresh half; both compositions forward it; the supervisor supplies
`total - elapsed` as ONE callable, so the admission check and every boundary
read the same decreasing budget.

## Two things measuring it found

**A regression I introduced and corrected in the same claim.** Applying the two
new ceilings unconditionally made an UNBOUNDED observation carry 120 seconds
where it had carried `None`. That is a changed existing caller, which the
owner's constraint forbids. Unbounded now passes `None` exactly as before, and
a case asserts it instead of a comment claiming it.

**Three vectors still run unbounded inside a bounded ending.** With a costing
boundary a bounded ending asks `[60, None, None, 57, None, 55, 54, 53, 52]`.
The `None`s are the pre-core credential recovery and adapter internals. Stated
as a failing expectation — `test_every_vector_of_a_bounded_ending_carries_the_allowance`
— so it reports an unexpected success the day it closes.

What IS proved: the allowance decreases across the boundaries that carry it,
never rises, never exceeds the package's ceiling, and an unbounded ending is
byte for byte what it was.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **41 cases, 40 passing and 1
expected failure, 2.394s**, clean under `-W error::ResourceWarning`.

Accepted suites over the five changed product files — `test_custody`,
`test_abandoned_attempt_engine`, `test_intake`, `test_attempts`,
`test_runtime_deadlines`, `tests.tools.test_single_worker`,
`test_credentials_engine`, `test_custody_engine` — **986 tests, 38.505s**, with
7 failures ALL in the daemon-dependent `DockerCustody` and
`ARealDaemonNeverHoldsTheBearer` cases. **Reproduced identically against the
PINNED unmodified product** (20 tests, same 2 failures / 5 errors / 1 skip,
`custody` resolving to the pinned copy), so they are environmental and
pre-existing.

## REMAINING

  1. close the three unbounded vectors — pre-core credential recovery and the
     adapter internals;
  2. the owner's remaining acceptance cases: timeout after a durable commit,
     no continuing background effects, replay without duplicate effects, and
     all of it through `supervise` with a stranded attempt;
  3. first-call crash and launch-absent alternate recovery;
  4. the two operator grants documents with validation and readback;
  5. the executed-image fault diagnosis;
  6. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

No external blocker.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the snapshot are read-only.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, and from owner 256143 `worker_manager/oci.py` and
`worker_manager/custody.py`, plus this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 256145

### Enumerate, then edit — and the enumeration was wrong in one place

The owner made the enumeration a precondition, so `PATHS-256145.md` came
first: every step of the chain, the four boundaries needing the two new files,
and every other file with the reason it needs none.

I got one answer wrong there and the tests told me: I claimed no accepted test
needs changing because the operand defaults to `None`. Two accepted cases pin
`custody_act`'s parameter list as a signature guard. So the operand does not go
there at all — the allowance reaches the custody act through the engine PORT,
which clamps every vector the act issues. The guard stays true and no unowned
test was edited. That is a better design than the one I set out to build, and I
would not have found it by reading.

### The allowance, and what measuring it cost me

One rule: `None` is today, a bounded caller may only ask for less, and the
result is a whole number rounded up. Threaded from the supervisor's
`total - elapsed` through both compositions and the core to the removal and
both custody acts, read at each boundary so the second root gets what the first
left.

Then I wrote the case that MEASURES it, and it found two things immediately.
Applying my new ceilings unconditionally made an unbounded observation carry
120 seconds where it had carried nothing — a changed existing caller, which is
exactly what the owner forbade; corrected in the same claim, with a case that
asserts the unbounded path rather than a comment claiming it. And three vectors
still run unbounded inside a bounded ending. I have written that as a failing
expectation with the measured list in its docstring rather than a plan entry.

The pattern I keep relearning: the assertion I write to prove a thing is what
tells me the thing is not yet true.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 41 cases, 40 passing and 1
expected failure, **2.394s**, clean under `-W error::ResourceWarning`;
intermediates 1.597s, 1.658s, 1.686s, 2.178s, 2.191s, 2.197s.
Accepted suites over the five changed files — **986 tests, 38.505s**, 7
failures all daemon-dependent and reproduced identically against the pinned
product (**15.647s**). Earlier in the claim: 125 OK 4.803s/4.805s/4.875s, 329
OK 8.405s.

The 424-case stage-execution suite was NOT repeated. Everything prior stands:
899 OK 19.828s, 9.308s, 10.337s, 85 OK 68.787s and 85 OK 69.207s with its two
red predecessors at 31.663s and 31.822s, 159.910s plus its untimed repeat,
0.966s, 1.170s, 10.041s, 9.966s, 0.348s, 0.130s, 0.094s, the combined runs
listed in earlier entries, the untimed probes and diagnostic reads, the
unmeasured ~120s command-timeout run and the earlier unknowns, alongside named
**1047.869180986s**. The reviewer's 1.549s/1.580386877s is additional.

State: returned INCOMPLETE through baton.bug with the allowance built and
enforced where it reaches, one regression caught and corrected, and the
remaining vectors stated as a failing expectation.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 256145" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
