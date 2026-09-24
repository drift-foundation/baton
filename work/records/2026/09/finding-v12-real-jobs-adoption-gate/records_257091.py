"""Claim-257091: the reserve actually withheld; the stopgap named and frozen."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 257091; RETURNED INCOMPLETE

Owner reroute 257086 selected the bounded unresolved-custody stopgap and
required the reserve accounting corrected. Both are done.

## The reserve is WITHHELD now, not merely a floor

Review 2026-09-24T11:10:32Z: `_declare_abandonment` refused below 30 seconds
and then passed the UNCHANGED remaining callable on, "so an admitted act can
therefore spend ALL the remaining allowance, including the purported reserve".
It was an admission floor wearing a reserve's name, and that was mine.

`_work_allowance(remaining)` answers `remaining() - reserve`, and BOTH the
admission check and the operation read it. One subtraction decides both, so
they cannot drift apart. Measured at the vectors rather than read off the
code: with `reserve + 60` left, no boundary is handed more than 60, and with
exactly the reserve left nothing starts and the world is unchanged.

**The margin's sufficiency is NOT claimed, and the page says so.** A timed-out
custody act may owe `CUSTODY_RECLAIM_SECONDS` (120) plus `CUSTODY_STOP_SECONDS`
(5) in the worst case, which 30 does not cover. What it is: a floor for
recording the outcome honestly. Deriving a sufficient value from the supported
cleanup bounds is owed work.

## The stopgap, as the owner qualified it

Owner 257086: "report held/unresolved, identify and freeze every potentially
affected resource, prohibit reuse and success claims, and require explicit
operator reconciliation. This does not assert engine-side settlement or
authorize deletion."

`custody_act`'s UNRESOLVED answer now names both — the derived helper identity
and the exact root of the exact attempt — and says plainly that neither may be
reused, reported settled, or deleted on the strength of that answer. And the
accountability refusal CARRIES that diagnostic, so the operator who is told an
ending did not happen is told in the same sentence what is frozen pending
their reconciliation. Nothing asserts settlement; nothing deletes.

## W44342 stays parked

I named it as a prerequisite from a source comment. The reviewer read the
canonical record: W44342 is open, PARKED, routed baton.decide, and its own
Aug 30 and Sep 5 rulings accept fail-closed UNRESOLVED for the pilot and
supersede the durable provider as the default next solution. **A source comment
does not select a dependency**, and my citation did not establish one. The
owner directs preserving that parking with no generic provider prerequisite,
and `PATHS-256145.md` will carry that correction rather than my original
claim.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **44 cases, all passing,
2.478s**, clean under `-W error::ResourceWarning`, including the two new
reserve cases measured at the vectors.
Accepted suites over the changed product files — **966 tests, OK, 22.679s**.

## REMAINING

  1. store-wait accounting — the actual lock and I/O bounds;
  2. a margin derived from the supported cleanup bounds rather than stated;
  3. the supervisor timeout and replay proofs through `supervise` with a
     stranded attempt;
  4. first-call crash and launch-absent alternate recovery;
  5. the two operator grants documents with validation and readback;
  6. the executed-image fault diagnosis;
  7. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

No external blocker.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the snapshot are read-only. Positive cleanup remains required for adoption.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, `worker_manager/oci.py`,
`worker_manager/custody.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 257091

### The reserve was a floor with a reserve's name

You put it exactly: the check refused below 30 seconds and then handed the
operation the unchanged remaining callable, so an admitted act could spend the
margin too. One subtraction fixes it and keeps both halves honest —
`_work_allowance` answers `remaining - reserve`, and the admission check and
the boundaries read the SAME callable, so they cannot drift.

I measured it at the vectors rather than asserting it from the code: with
`reserve + 60` left, nothing is handed more than 60.

And I am not claiming the number is sufficient. A timed-out custody act may
owe 120 + 5 seconds of reclamation, which 30 does not cover. It is a floor for
recording the outcome honestly, and that sentence is in the code beside the
constant so the next reader does not have to infer it.

### The stopgap says what it freezes

The owner qualified the no-background-effects condition for exactly this case,
so the UNRESOLVED answer now names the helper identity and the exact root, and
says neither may be reused, reported settled, or deleted on its strength. The
accountability refusal carries that diagnostic too — otherwise an operator is
told an ending did not happen without being told what is still live.

### W44342: a source comment is not a dependency

I cited `custody._recovered`'s note as a prerequisite. You read the canonical
record: W44342 is PARKED and its own rulings accept fail-closed UNRESOLVED for
the pilot and supersede the durable provider as the default next solution. My
citation revived something the Work had already decided not to depend on. The
parking stands.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 44 cases, all passing,
**2.478s**, clean under `-W error::ResourceWarning`; intermediates 1.818s,
1.909s.
Accepted suites over the changed files — **966 tests, OK, 22.679s**; 121 OK
3.152s for `test_custody` alone.

Neither the 424-case stage-execution suite nor the daemon suites were
repeated. Everything prior stands: 966 OK 22.618s, 986 in 38.505s with its 7
daemon failures and the 15.647s pinned comparison, 899 OK 19.828s, 9.308s,
10.337s, 85 OK 68.787s / 69.207s / 69.262s with the two red predecessors at
31.663s and 31.822s, 159.910s plus its untimed repeat, 0.966s, 1.170s,
10.041s, 9.966s, 0.348s, 0.130s, 0.094s, 125 OK 4.803/4.805/4.875s, 329 OK
8.405s, the combined focused runs in earlier entries, the untimed probes and
diagnostic reads, the unmeasured ~120s command-timeout run and the earlier
unknowns, alongside named **1047.869180986s**. The reviewer's
1.717s/1.771985183s is additional.

State: returned INCOMPLETE through baton.bug with the reserve corrected, the
stopgap implemented as the owner qualified it, my W44342 citation withdrawn,
and seven items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 257091" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
