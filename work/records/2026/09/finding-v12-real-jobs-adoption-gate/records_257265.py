"""Claim-257265: the hold machinery, and the two rules that stop its wiring."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 257265; RETURNED INCOMPLETE

The six-part hold was the selected next work. Five parts are built. The sixth
— writing the hold from the act — I built, ran, and REVERTED, because it
breaks two accepted invariants. That conflict is the finding.

## What is built, in `custody.py`

  * **`CUSTODY_HOLD_KIND` / `CUSTODY_CLEARED_KIND`** and
    **`_hold_identity(kind, attempt, root, EPISODE)`** — the episode is IN the
    identity, which is the rule review 2026-09-24T13:43:14Z added: "distinct
    uncertainty episodes must defeat stale clearance even for the same tuple".
    Two uncertainties over one root are two facts and a clearance for the
    first cannot lift the second;
  * **`custody_holds(store, attempt, root)`** — a reader that opens nothing
    and decides nothing, answering which episodes exist and which are cleared,
    bounded at `_MOST_HOLDS` so no caller can make it expensive;
  * **`clear_custody_hold(...)`** — an operator's reconciliation recording
    what was OBSERVED rather than that a command ran. A blank observation, an
    episode that does not exist, and a clearance naming a different helper are
    each refused by name.

## What is NOT wired, and the exact reason

Writing the hold from `normalize_directory` — write-ahead before the engine,
cleared by the custodian's own account on success — fails two ACCEPTED rules.
I found that by building it and running the suites, not by reasoning:

  1. **`test_an_unaccountable_answer_commits_nothing`**
     (`tests/manager/test_custody.py`). The accepted invariant is that an
     unaccountable answer commits NOTHING. A write-ahead hold is a commit, so
     the rule and the hold cannot both hold as stated.
  2. **The interrupted-normalization resume cases** in `test_custody`,
     `test_intake` and `test_attempts` (three suites). An interruption is the
     RESUMABLE case this build is designed around; with a hold in the act,
     every interrupted normalization froze its root and required an operator.
     The resumes stopped resuming.

Both are real conflicts with the semantics the reviewer and owner have been
protecting all along, so I reverted rather than weakening either rule. The
accepted suites are green again.

**The design question for disposition**, stated exactly:

  * is the hold written for EVERY unaccountable answer, or only for the
    UNRESOLVED shape — the one where `custody_act` got no engine answer and
    the daemon may still create the helper? The second is narrower, does not
    collide with "an unaccountable answer commits nothing" for the ordinary
    unaccountable cases, and is the case owner 257086's stopgap actually
    names;
  * does a hold block a RESUME of the same act, or only a NEW act over that
    root? Blocking the resume is what broke three suites; permitting it needs
    the hold to be keyed so that the resuming act recognises its own episode.

I have not chosen between these. Both change accepted behaviour, and choosing
silently is what the last several reviews have rightly stopped me doing.

## Evidence

`test_abandonment` + `test_routed_abandonment` — **48 cases, all passing,
2.658s**, clean under `-W error::ResourceWarning`, including a case proving
the hold machinery works on its own and saying why it is not in the act.
Accepted suites over the changed product files — **966 tests, OK, 22.750s**
after the revert.
`test_two_jobs` — **85 tests, OK, 69.215s**.

## REMAINING

  1. the hold's wiring, pending the disposition above;
  2. reuse and deletion guards, which need `workspaces.py` enumerated and
     likely owned — not taken, not edited;
  3. store-wait accounting — the actual lock and I/O bounds;
  4. the supervisor timeout and replay proofs through `supervise` with a
     stranded attempt;
  5. first-call crash and launch-absent alternate recovery;
  6. the two operator grants documents with validation and readback;
  7. the executed-image fault diagnosis;
  8. the reviewable snapshot with a verified import-cache boundary, then exact
     recovery and fresh-run commands.

## Standing constraints

No deployed mutation, live rerun, cleanup execution or deletion. The preserved
instance and the snapshot are read-only. W44342 stays parked.

## Ownership

`OWNERSHIP-255823.md`: `tools/single_worker.py`, `tools/stage_execution.py`,
`worker_manager/intake.py`, `worker_manager/oci.py`,
`worker_manager/custody.py`, and this dossier.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 257265

### I built the hold, ran it, and took it back out

Five parts are in: episode-bearing identities so a stale clearance cannot lift
a later uncertainty, a bounded reader, and an operator clearance that wants
what was OBSERVED and refuses a blank one, a missing episode, or a different
helper.

The sixth — writing it from the act — I wired up, and the accepted suites told
me it was wrong in two ways at once. `test_an_unaccountable_answer_commits_nothing`
says an unaccountable answer commits NOTHING, and a write-ahead hold is a
commit. And the interrupted-normalization resume cases across three suites
stopped resuming, because a hold turned every interruption into a frozen root
waiting on a person.

Those are the semantics this review line has been protecting for a dozen
claims. So I reverted the wiring instead of editing the rules, and the
question goes back as a question: is the hold for every unaccountable answer
or only the UNRESOLVED shape, and does it block a resume of the same act or
only a new act over that root? Both change accepted behaviour. Choosing
quietly is the habit these reviews have been correcting.

What I did NOT do is leave the accepted suites red, or weaken an assertion to
make my code fit.

### Verification spending

`test_abandonment` + `test_routed_abandonment` — 48 cases, all passing,
**2.658s**, clean under `-W error::ResourceWarning`; 2.834s with the wiring in
before the revert, plus 2.029s, 2.073s, 2.104s, 2.110s intermediates.
Accepted suites over the changed files — **966 tests, OK, 22.750s** after the
revert; **22.798s with 6 failures** before it, which is the measurement that
produced this finding.
`test_two_jobs` — 85 tests, **OK, 69.215s**.

Neither the 424-case stage-execution suite nor the daemon suites were
repeated. Everything prior stands: 966 OK 22.565/22.616/22.618/22.679/22.686s,
121 OK 3.152s, 986 in 38.505s with its 7 daemon failures and the 15.647s
pinned comparison, 899 OK 19.828s, 9.308s, 10.337s, 85 OK 68.953/68.787/
69.017/69.207/69.262/69.281s with the two red predecessors at 31.663s and
31.822s, 159.910s plus its untimed repeat, 0.966s, 1.170s, 10.041s, 9.966s,
0.348s, 0.130s, 0.094s, 125 OK 4.803/4.805/4.875s, 329 OK 8.405s, the combined
focused runs in earlier entries, the untimed probes and diagnostic reads, the
unmeasured ~120s command-timeout run and the earlier unknowns, alongside named
**1047.869180986s**. The reviewer's 0.132s/0.186334544s is additional.

State: returned INCOMPLETE through baton.bug with the hold machinery built,
its wiring reverted with the exact conflict named, and eight items open.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 257265" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
