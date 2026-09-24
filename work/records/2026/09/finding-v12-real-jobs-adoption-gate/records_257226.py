"""Claim-257226: the reserve is an allocation, and the positive path is back."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 257226; RETURNED INCOMPLETE

Review 2026-09-24T13:43:14Z: my previous claim over-corrected. The reserve is
an allocation again, the positive path is proved in a run the size this
deployment actually uses, and the bounded failure is proved beside it.

## I over-corrected, and the new cases proved only refusal

Deriving the reserve from the worst case made it 1200 seconds — larger than an
ordinary two-Job run's whole 600-second budget — so abandonment became
impossible and every case I added showed it refusing. The review is exact:
"maxima are ceilings not minimum grants", and what had been asked for was
TRUTHFUL ACCOUNTING rather than guaranteed completion under the sum of every
maximum.

**`ABANDONMENT_RESERVE_SECONDS` is a bounded allocation** — 60 seconds held
back so that when the work allowance is gone there is still time for the
reclamation to try in and for the outcome to be recorded. It does not promise
the reclamation finishes, and the code says so where the number is.

**The worst case is kept, and kept apart.** `_reclamation_worst_case()` still
counts it from the source — five sequential engine calls per custody act, two
acts, each waiting up to `CUSTODY_RECLAIM_SECONDS` — because an operator
reading "unresolved" needs to know what this run did not buy. It is
deliberately not the reserve, and a case asserts that it is strictly larger.

## Both paths are proved now

  * **positive**, in a 600-second run — the budget this deployment actually
    uses rather than a number chosen to pass: the attempt is declared, settles
    `retained`, discharges its gate, and counts as settled. That case is the
    one that would have caught my over-correction;
  * **bounded failure** — a costing boundary spends the work allowance PART
    WAY THROUGH the ending, so a vector is refused mid-sequence. What comes
    out claims nothing: never settled, never `False` from an exception, a
    stated reason, and the reported cleanup equal to what the journal actually
    carries or `None` when it carries none.

## REMAINING

  1. the six-part write-ahead hold — authorized unfinished work, to be
     implemented after the exact added-path enumeration the reviewer asks
     for, and with the additional rule they named: **distinct uncertainty
     episodes must defeat a stale clearance even for the same tuple**, so the
     identity carries the episode and not only the act;
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

`test_abandonment` + `test_routed_abandonment` — **47 cases, all passing,
2.696s**, clean under `-W error::ResourceWarning`.
Accepted suites over the changed product files — **966 tests, OK, 22.565s**.
`test_two_jobs` — **85 tests, OK, 68.953s**.

## Standing constraints

No deployed mutation, live rerun, cleanup execution or deletion. The preserved
instance and the snapshot are read-only. W44342 stays parked and is not a
prerequisite. Positive cleanup remains required for adoption.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, `worker_manager/oci.py`,
`worker_manager/custody.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 257226

### I over-corrected, and my own new tests should have told me

Last claim I derived the reserve from the worst case and made it 1200 seconds.
An ordinary two-Job run has 600. So abandonment became impossible, and the two
cases I added proved only that it refuses — which I wrote up as "the honest
fallback" rather than noticing that I had disabled the feature.

Your sentence is the one that lands: maxima are ceilings, not minimum grants.
Truthful accounting was what had been asked for, not a guarantee bought by
reserving the sum of every maximum.

The reserve is a bounded allocation again — 60 seconds, held back so the
reclamation has somewhere to try and the outcome has time to be recorded, and
promising nothing beyond that. The worst case stays in the file as what an
operator needs to understand "unresolved", explicitly not as the reserve, with
a case asserting it is strictly larger.

### And both paths are proved, not just the refusal

The positive one runs in a 600-second budget — the size this deployment
actually uses, rather than a number chosen to make a case pass. That is the
test that would have caught last claim's mistake.

The bounded failure spends the work allowance part way through the ending and
checks that what comes out claims nothing: never settled, never `False` from
an exception, a stated reason, and a reported cleanup equal to what the
journal carries or `None` when it carries none.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 47 cases, all passing,
**2.696s**, clean under `-W error::ResourceWarning`; 2.535s intermediate.
Accepted suites over the changed files — **966 tests, OK, 22.565s**.
`test_two_jobs` — 85 tests, **OK, 68.953s**.

Neither the 424-case stage-execution suite nor the daemon suites were
repeated. Everything prior stands: 966 OK 22.616/22.618/22.679/22.686s, 121 OK
3.152s, 986 in 38.505s with its 7 daemon failures and the 15.647s pinned
comparison, 899 OK 19.828s, 9.308s, 10.337s, 85 OK 68.787/69.017/69.207/
69.262/69.281s with the two red predecessors at 31.663s and 31.822s, 159.910s
plus its untimed repeat, 0.966s, 1.170s, 10.041s, 9.966s, 0.348s, 0.130s,
0.094s, 125 OK 4.803/4.805/4.875s, 329 OK 8.405s, the combined focused runs in
earlier entries, the untimed probes and diagnostic reads, the unmeasured ~120s
command-timeout run and the earlier unknowns, alongside named
**1047.869180986s**. The reviewer's 0.074s/0.136655089s is additional.

State: returned INCOMPLETE through baton.bug with the over-correction reversed,
both paths proved, and seven items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 257226" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
