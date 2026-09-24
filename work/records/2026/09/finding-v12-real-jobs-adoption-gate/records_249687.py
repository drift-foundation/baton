"""Claim-249687: three R4 defects closed; four remain, named exactly."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249687

**My "complete preparation" claim of claim 249641 is SUPERSEDED.** Review
2026-09-23T17:44:56Z found six defects in the supervisor; three are closed and
four remain.

## Closed under claim 249687

  * **Cancellation reached a port that does not exist.** It called
    `operations.cancel`; no composition exposes that — the port is
    `cancel_attempt`, and the supported way to reach it is
    `baseline._cancel_active`, which fences the exact participant and
    generation at the Authority before ordering quiescence. Reporting "no
    cancellation port" for every attempt was reporting a LEAK AS A CLEAN STOP.
  * **Success was "nothing to complain about".** An empty serve published
    `settled` with zero admissions and no verdicts. Success is now what the
    run PRODUCED: every configured admission spent and a launched runtime to
    account for; a case drives an empty serve and asserts `held`.
  * **The termination handler was constructed and never installed.** It is now
    installed around everything and restored only after the outcome is on
    disk.

42 focused checks, 0 failures, measured 10.943187141994713s,
`verification-7.json`; 1 is new.

## REMAINING, exactly, and none of it started

1. **Bounded cleanup EXECUTION.** The remaining deadline is recorded and
   nothing is driven inside it. The accepted path runs ending sweeps after the
   gate closes; this reads the journal and stops.
2. **An actual generated-document success**: four attempts, two frozen
   verdicts and positive cleanup, through the composed documents rather than
   the fixture's helpers.
3. **ONE runnable bounded entrypoint.** Operator step 7 names `job`, `control`
   and `composed` without defining them, and step 4 independently serves
   unbounded. One command must open the stores, compose the operations, serve
   bounded and stop.
4. **The affected checks against that entrypoint**: no-result, deadline,
   failure and interruption.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249687

I called the preparation complete last claim. It was not, and the review is
right about every one of the six defects it names. Three are closed here.

### The cancellation port did not exist

`supervise` called `operations.cancel`. No composition exposes that — the port
is `cancel_attempt` — so every attempt was recorded as "no cancellation port"
and the run still reported its stop. **That is reporting a leak as a clean
stop**, which is worse than reporting nothing. It now goes through
`baseline._cancel_active`, the accepted path, which fences the exact
participant and generation at the Authority before ordering quiescence.

I had written the phrase "reports honestly when the composition offers none"
into my own code while the composition did offer one, under a different name I
never checked.

### Success meant "nothing to complain about"

An empty serve published `settled` with zero admissions and no verdicts. The
reviewer drove exactly that. `state` is now decided by what the run PRODUCED:
every configured admission spent, and at least one launched runtime to account
for. A case drives an empty serve and asserts `held` with the reason named.

### The handler was constructed and never installed

`Termination()` was built and `defer()` called, but `install()` never was, so
the whole point -- a signal during cancellation, cleanup or publication not
killing the process with no outcome on disk -- was absent. It is now installed
around everything and restored only after the outcome is written.

### What I did NOT do, and am not implying

The remaining deadline is still only RECORDED: no ending sweeps are driven
inside it. There is still no success through the generated documents with four
attempts, two frozen verdicts and positive cleanup. There is still no single
runnable bounded entrypoint -- step 7 names `job`, `control` and `composed`
without defining them, and step 4 serves unbounded. And the no-result,
deadline, failure and interruption checks against that entrypoint do not
exist.

### Verification spending

42 focused deterministic checks, 0 failures, measured 10.943187141994713s,
receipt `verification-7.json` with `verification-7.log`; 1 is new.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 =
**47.791708146s**. Pin checks are separate and were not measured.

State: returned INCOMPLETE through baton.bug, superseding my previous
complete-preparation claim.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249687" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
