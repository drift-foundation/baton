"""Claim-257126: the reserve is spendable by what it was reserved for."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 257126; RETURNED INCOMPLETE

Review 2026-09-24T13:29:10Z found two things. R2 is corrected and proved. R1
is scoped precisely rather than half-built, with the exact shape a durable
freeze needs.

## R2 — the reserve was unusable by the thing it was reserved for

"Custody recovery uses same reduced allowance, so zero work allowance also
prevents reclamation from spending reserve." Exactly so, and that made the
margin time NOBODY could use rather than time held for the reclamation.

**Two budgets now, told apart by the verb.** The ACT is the `run` vector;
every other vector `custody_act` issues is reconciliation or reclamation. The
act and the removal spend the WORK allowance (`remaining - margin`); the
reclamation spends the TOTAL. So an ending that exhausts its work budget still
leaves the reclamation able to run, which is what a reserve is for.

**And the margin is DERIVED, not stated.** `_reclamation_margin()` reads this
package's own bounds — `2 × (CUSTODY_RECLAIM_SECONDS + CUSTODY_STOP_SECONDS)`
= 250 — because an abandonment performs two custody acts, one per root, and
either may owe a reconciliation and a stop. Read from the package so the
margin moves when the bounds move rather than drifting away from what it
covers.

Proved at the vectors: the work vectors never exceed `whole − margin`, no
vector anywhere exceeds `whole`, the work allowance falls monotonically, and
the reclamation stays inside the package's own ceiling.

## R1 — the warning is not a freeze, and I am not pretending otherwise

The review is right: `normalize_directory` records NOTHING on the unresolved
path, so the text I added names the affected resources to whoever reads that
one refusal and stops there. A later `custody_act` can retry, reclaim and
start again, across a restart, with nothing to consult. And three branches
never reach the new diagnostic at all: `_recovered`'s own refusal, a malformed
engine answer, and an interrupt.

**What a durable freeze actually needs** — written down rather than guessed at
next claim:

  1. a committed record at the act's own identity — kind
     `directory-custody.unresolved`, signed over the attempt, the root, the
     verb, the custodian image and the derived helper identity — written on
     the unresolved path BEFORE the refusal is raised, so a crash between them
     leaves the freeze rather than losing it;
  2. a precondition at the TOP of `normalize_directory` that refuses when such
     a record exists and no reconciliation clears it — which is what makes the
     freeze bind a later act rather than a later reader;
  3. an operator reconciliation surface: one explicit operation naming the
     attempt, the root and what the operator observed, committed under its own
     identity, which is the only thing that lifts (1);
  4. the same write on the three bypass branches, since a freeze that depends
     on which failure occurred is not a freeze.

That is a new journal kind, a new precondition and a new public operation, and
it belongs in `custody.py` which is owned. It is NOT done, and the diagnostic
text stays meanwhile as a diagnostic — useful, and not evidence of a freeze.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **44 cases, all passing,
2.504s**, clean under `-W error::ResourceWarning`.
Accepted suites over the changed product files — **966 tests, OK, 22.616s**.
`test_two_jobs` — **85 tests, OK, 69.017s**.

## REMAINING

  1. the durable freeze above, in its four parts;
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
instance and the snapshot are read-only. Positive cleanup remains required for
adoption; W44342 stays parked.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, `worker_manager/oci.py`,
`worker_manager/custody.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 257126

### The reserve was time nobody could spend

You caught the thing that made my "fix" hollow: the reclamation read the same
reduced allowance, so a work budget of zero left the reclamation zero too. A
margin its own beneficiary cannot use is not a reserve.

Two budgets now, and the verb tells them apart — the act is the `run` vector,
everything else `custody_act` issues is reconciliation or reclamation. Work
spends `remaining − margin`; reclamation spends the total.

And the margin is derived instead of asserted: two custody acts, each possibly
owing a reconciliation and a stop, read from this package's own constants. If
those bounds move, the margin moves with them rather than becoming a number
that used to be right.

### The warning is not a freeze and I will not call it one

`normalize_directory` records nothing on the unresolved path, so what I added
tells whoever reads that one refusal and no one else. A later act can retry
and start again with nothing to consult, and three branches — `_recovered`'s
refusal, a malformed answer, an interrupt — never reach the text at all.

I have written down what a durable freeze actually needs: a committed record
at the act's identity written BEFORE the refusal, a precondition at the top of
the act that refuses while it stands, an explicit operator reconciliation that
is the only thing lifting it, and the same write on the bypass branches. Four
parts, a new journal kind and a new public operation. Not done — and named at
that size rather than approximated with more prose.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 44 cases, all passing,
**2.504s**, clean under `-W error::ResourceWarning`; intermediates 1.798s,
1.829s, 2.581s.
Accepted suites over the changed files — **966 tests, OK, 22.616s**.
`test_two_jobs` — 85 tests, **OK, 69.017s**.

Neither the 424-case stage-execution suite nor the daemon suites were
repeated. Everything prior stands: 966 OK 22.618s and 22.679s, 121 OK 3.152s,
986 in 38.505s with its 7 daemon failures and the 15.647s pinned comparison,
899 OK 19.828s, 9.308s, 10.337s, 85 OK 68.787/69.207/69.262s with the two red
predecessors at 31.663s and 31.822s, 159.910s plus its untimed repeat, 0.966s,
1.170s, 10.041s, 9.966s, 0.348s, 0.130s, 0.094s, 125 OK 4.803/4.805/4.875s,
329 OK 8.405s, the combined focused runs in earlier entries, the untimed
probes and diagnostic reads, the unmeasured ~120s command-timeout run and the
earlier unknowns, alongside named **1047.869180986s**. The reviewer's
1.835s/1.890487521s is additional.

State: returned INCOMPLETE through baton.bug with R2 corrected and proved, R1
scoped at its real size, and seven items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 257126" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
