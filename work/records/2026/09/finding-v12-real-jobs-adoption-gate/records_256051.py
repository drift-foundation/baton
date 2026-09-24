"""Claim-256051: the shutdown step bounded, its accounting made true."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 256051; RETURNED INCOMPLETE

Review 2026-09-24T10:35:28Z requested three changes. All three are made.

## R1 — the declaration is inside the selected total now

It could START destructive work after the reserved window had expired: the
sweep loop exits on the bound, and the declaration then ran unconditionally
over every outstanding attempt, and that step may fence, remove, normalize
custody and discharge. "A finite attempt count does not preserve the selected
run time bound" — exactly so.

`_declare_abandonment` now takes `remaining`, a callable answering the seconds
left, supplied from the supervisor as `total - (monotonic() - started)`. The
bound is checked BETWEEN attempts and never inside one, so an ending already
begun is never abandoned half-way. When nothing is left, every attempt from
that point is recorded unresolved by name, with its runtime untouched.

Proved: with `remaining` answering 0 the effect counts are unchanged and no
cleanup is committed; with time left the same attempt settles `retained`. So
the bound is what stopped it, not something else about that attempt.

## R2 — the final accounting no longer contradicts a successful abandonment

  * **`unresolved_cleanup`** is derived from BOTH ending journals, and
    `held_because` reports from it. `outstanding_cleanup` stays exactly what
    it was — the ordinary journal's answer — and each undeclared or unsettled
    attempt is named separately with its own reason.
  * **`_settled_by_abandonment`** requires positive cleanup AND the gate
    discharge. `declared=True` alone is not a completed ending; an
    undischarged quiescence gate leaves the Work stopped.
  * **Every failure is per attempt.** `_declared_one` wraps eligibility, the
    call and the read-back separately, so a failure no longer escapes to the
    single outer guard, replaces the whole map with `{}` and skips the rest.
    A read-back that fails leaves `declared` TRUE and the settlement UNKNOWN,
    which is the honest pair: the act happened; what this manager can say
    about it did not.

New cases: the expired bound; the read-back failure (severed exactly when the
operation returns, because the composition reads that same public reader twice
INSIDE the operation and failing every call fails the abandonment itself — a
different case); an eligible attempt with no recorded stage, which is the
missing-stage branch the two absent candidates never reached; one attempt's
eligibility failure not discarding the others; and the discharge requirement.

## R3 — the changed boundary is recorded rather than glossed

My "nothing is weakened" was too broad and the review is right. What
`source_files` attests is SOURCE identity — the same 106 files, still moving on
a changed byte, a rename or a swap. What it no longer attests is every byte
Python may EXECUTE from that directory, because the former all-file boundary
covered the caches. `-B` prevents WRITING byte-code, not LOADING it. That is
now written into the function itself, together with what is still owed: the new
reviewable snapshot needs a clean or separately verified import-cache boundary
with its own verifier cases. Nothing was deleted from the preserved snapshot.

## REMAINING

  1. a supervised run that actually STRANDS an attempt, and a supervise-level
     deadline-expired case — this claim proved both at the helper, not through
     `supervise`;
  2. first-call crash and launch-absent alternate recovery;
  3. the two operator grants documents with validation and readback;
  4. the executed-image fault diagnosis;
  5. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

No external blocker.

## Standing constraints

No deployed mutation, live rerun or cleanup execution. The preserved instance
and the snapshot are read-only; the snapshot's stray caches were left in place.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`src/baton_v12/worker_manager/intake.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 256051

### The step could start work after the window it was meant to fit inside

That is R1 and it was a real defect of mine: the sweep loop stops on the total,
and then the declaration ran over every outstanding attempt regardless — a step
that fences, removes, normalizes custody and discharges. A finite attempt count
is not a time bound.

It takes `remaining` now, checked between attempts and never inside one, so
nothing already begun is abandoned half-way and nothing new starts once the
total is gone. Everything from that point is recorded unresolved by name with
its runtime untouched, and the test proves the bound is what stopped it by
running the same attempt again with time left.

### The accounting said something false

`held_because` called every ordinary-journal outstanding attempt "no positive
cleanup", including ones an abandonment had settled. The journals stay separate
— that part was right — but the OVERALL unresolved set now comes from both, and
a settled abandonment takes the gate discharge as well as the retained cleanup.
A declaration that was made is not an ending that finished.

And one guard was doing too much: an eligibility or read-back failure escaped
to the outer `_guarded`, which replaced the whole map with `{}` and skipped
every later attempt. Each attempt carries its own failure now.

Writing the read-back test taught me something about my own composition: the
discharge reads `abandonment_cleanup_of` twice INSIDE the operation, so failing
every call fails the abandonment rather than the read-back. The sever is armed
exactly when the operation returns, which is the thing I actually meant to
model.

### And "nothing is weakened" was too broad

The source manifest attests source identity, not executed bytes, and `-B`
prevents writing byte-code rather than loading it. I have written that into the
function instead of leaving my broader claim standing, and the clean
import-cache boundary is recorded as owed by the snapshot item.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 36 cases, all passing,
**2.152s**, clean under `-W error::ResourceWarning`; 1.271s, 1.451s and 2.226s
intermediates, the last of which was the read-back case failing twice before I
modelled it correctly.
`test_two_jobs` — 85 tests, **OK, 68.787s**, pinned snapshot bound, byte-code
disabled.

The 424-case stage-execution suite was NOT repeated. Everything prior stands:
899 OK 19.828s, 9.308s, 10.337s, 85 OK 69.207s and its two red predecessors at
31.663s and 31.822s, 159.910s plus its untimed repeat, 0.966s, 1.170s, 10.041s,
9.966s, 0.348s, 0.130s, 0.094s, the combined 1.090/1.334/1.536/1.677/1.760/
1.805/1.870s, the focused runs in earlier entries, the untimed probes and
diagnostic reads, the unmeasured ~120s command-timeout run and the earlier
unknowns, alongside named **1047.869180986s**. The reviewer's 1.233s/
1.259930748s is additional.

State: returned INCOMPLETE through baton.bug with R1, R2 and R3 addressed and
five items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 256051" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
