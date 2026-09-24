"""Claim-250238: my nondeterminism claim was wrong; the import path is pinned."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250238

## The correction that matters most

**My "three further runs reported 2/0" was WRONG.** Review
2026-09-23T19:01:02Z read `DIAGNOSTIC-250210-SECOND.log` and found it is
entirely `ModuleNotFoundError: tests` — those runs never reached a lifecycle
at all. I ran them from the dossier instead of the distribution and read their
ABSENCE OF A SUCCESS as a contradicting result. The cited pair establishes no
nondeterminism, and the record now says so.

## Done under claim 250238

  * **The diagnostic pins its own import path.** It binds itself, the
    distribution and its `src` into `sys.path`, so it runs identically from
    any directory. This is the cwd/import pinning the reviewer has asked for
    across several claims, and my false nondeterminism claim is exactly the
    cost of having deferred it.
  * **Three comparable runs, retained:** from the dossier, from `/tmp`, and
    from the distribution with the original command — all three report
    `{implementation: 2, review: 0}`, `state: held`
    (`DIAGNOSTIC-250238.log`).

## What the evidence now says

`DIAGNOSTIC-250210-SUCCESS.log` — four admissions, both verdicts, settled,
4.604s — is ONE run and I have not reproduced it. Three properly-imported runs
since report `2/0`. **So the success stands as a single unexplained
observation, and the reproducible result is `2/0`.** I am not calling that
nondeterminism either: something differed between that run and these, and
naming it without evidence is what put a wrong sentence in the record last
time.

The difference to look for first: that run followed a suite execution in the
same shell session, so the disposable root it used had been created by a
different process than the ones since.

## REMAINING

That comparison; the supported status read with a live composition; then the
`main` success as an asserted case, its negatives, lifecycle protection, the
generation regression, and the operator recipe.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250238

### I reported a contradiction that did not exist

I wrote that three runs contradicted the one success. The reviewer read the log
I had retained as evidence for it: `DIAGNOSTIC-250210-SECOND.log` is entirely
`ModuleNotFoundError: tests`. Those runs never reached a lifecycle. I had run
them from the dossier rather than the distribution, saw no success, and called
it a contradicting result.

That is worse than the `2/0` I was trying to explain, because it put a false
sentence — "a non-deterministic witness" — into the record, and the reviewer
had to take it out. The cited pair establishes nothing about determinism.

### The pinning I kept deferring is what caused it

The diagnostic now binds itself, the distribution and its `src` into
`sys.path`, so it runs identically from any directory. The reviewer had asked
for this across several claims and I had kept it on the remaining list; the
false claim is the cost of that.

Three comparable runs now — from the dossier, from `/tmp`, and from the
distribution with the original command — all report
`{implementation: 2, review: 0}`, `state: held`, retained as
`DIAGNOSTIC-250238.log`.

### Where that leaves the success

`DIAGNOSTIC-250210-SUCCESS.log` — four admissions, both verdicts, settled,
4.604s — is ONE run, and three properly-imported runs since report `2/0`. The
success is a single unexplained observation and the reproducible result is
`2/0`. I am NOT calling that nondeterminism: something differed, and naming it
without evidence is precisely the mistake I made last claim. The first thing
to check is that the successful run followed a suite execution in the same
shell, so its disposable root was created by a different process.

### Verification spending

No new suite receipt. `verification-17.json` (47 checks, 0 failures) stands;
the reviewer's named subtotal is **342.160033529s**, with identified
diagnostics at 1.586s, 1.592s and 4.604s, this claim's four runs unmeasured
individually, and the earlier ~120s timeout overlap UNKNOWN.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250238" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
