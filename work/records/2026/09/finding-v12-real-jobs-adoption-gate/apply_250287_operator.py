"""Claim-250287: the operator recipe becomes the command the suite drives.

Review 2026-09-23T17:44:56Z first said it: step 4 served UNBOUNDED and step 7
named `job`, `control` and `composed` without defining them, so the stop
instruction could not be typed. `main` was written for that and has been
asserted end to end only now -- four admissions, two derived verdicts, positive
cleanup, `settled`, exit 0 -- so the page can finally print the thing that is
tested instead of a sketch.

Steps 4, 5 and 7 collapse into ONE command, because that command is the whole
bounded run: it opens both stores, composes, submits, serves through the
four-admission gate, stops at the bound, closes admission before cancelling,
cancels, drives bounded cleanup and publishes on every path. Step 6 is
unchanged and was already right -- `status --control` supplies the manager's
own read-only composition, which is precisely the operand my diagnostic was
missing when it printed an AttributeError instead of stage states.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "ADOPTION-247941.md"

START = "## Step 4 — start the manager"
END = "## Step 6 — watch, read-only"

STEPS = """## Step 4 — serve the bounded run, as ONE command

```sh
BATON_V12_STAGE_EXECUTION_CONFIG="<run root>/deployment.json" \\
PYTHONPATH="$BOUND:$DOSSIER" "$PY" -B "$DOSSIER/two_job_supervisor.py" \\
    --deployment "<run root>/deployment.json" \\
    --submission "<run root>/submission.json" \\
    --job-store "<run root>/jobs.sqlite3" \\
    --control-store "<run root>/control.sqlite3" \\
    --incarnation "<a fresh incarnation for this process>" \\
    --outcome "<run root>/outcome.json" \\
    --total-seconds 600 --cleanup-seconds 60
```

**This is the whole run.** It opens both stores, composes the deployment
`two_jobs.py` wrote, submits the one submission carrying both Jobs, serves
through the four-admission gate, stops at `total_seconds - cleanup_seconds`
(600 − 60 = **540**, so the reserve is INSIDE the total rather than an
extension), **closes admission BEFORE cancelling anything**, cancels every
attempt this run launched, drives bounded cleanup sweeps inside what is left of
the total, derives each Job's verdict from its own frozen result and publishes
`outcome.json` **on every path** — the bounded stop, a serving failure, a cap
refusal and an interruption alike.

It exits **0** when `state: settled` and **1** when `state: held`, so the exit
status is readable before any document is.

**What it does NOT do, and what an operator must supply for a real run.** In
this build there is no daemon, so nothing answers on the worker's behalf; the
command takes a turn seam and an operator typing it passes none. With a real
engine the runtime IS the turn and no seam is involved. The witness supplies a
deterministic turn at exactly that boundary and the packet says so rather than
implying the command has run workers for real.

The three earlier steps this replaces were not typeable: step 4 served
UNBOUNDED through `tools.job_manager serve`, and step 7 handed `job`, `control`
and `composed` to the supervisor without ever defining them. The submission
step is inside this command now, so a Job cannot be submitted twice by a
retyped line.

### Its predecessors, for a deployment that wants them separately

`tools.job_manager` remains the supported surface for submitting and reading,
and `--store`, `--incarnation` and `--authority-uuid` are REQUIRED ON EVERY
COMMAND — deliberately not defaulted, because the store namespaces every
episode identity in that Authority and restart recovery distinguishes managers
by the incarnation. An earlier version of this page omitted all three and the
reviewer reproduced `exit 2` from it.

```sh
PYTHONPATH="$BOUND" "$PY" -m tools.job_manager \\
    --store "<run root>/jobs.sqlite3" \\
    --incarnation "<a fresh incarnation for this process>" \\
    --authority-uuid "<the 32-hex Authority this Job store belongs to>" \\
    submit --document "<run root>/submission.json"
```

One submission carries both Jobs, each gated ordinarily: review behind
implementation. **No integration stage is submitted**, which is what keeps the
no-integration limit — not the absence of an integrator in the pool.

`tools/stage_execution.py` reads its configuration from
`BATON_V12_STAGE_EXECUTION_CONFIG` (`CONFIG_ENV`), which carries a path only —
never credential bytes. The source of these surfaces is
`v12/python/DEPLOYMENT.md` and `tools/stage_execution.py`'s `CONFIG_ENV` and
`factory`.

## Step 5 — read the outcome

`state: settled` means every admitted runtime has positive cleanup, both Jobs
produced an attributed verdict, and nothing was refused or uncertain.
`state: held` names every reason in `held_because`. Positive cleanup vocabulary
is the accepted one: `complete` or `retained`; missing, failed or uncertain
cleanup is outstanding, not success.

`admissions`, `admitted_attempts`, `generations`, `verdicts`, `cleanup`,
`outstanding_cleanup`, `uncertainty` and `interruptions` are all in the
document. An interruption still raises after the outcome is retained, carrying
it — a `SIGTERM` mid-run is owed a readable record.

**A process exit or `SIGTERM` alone is not proof that worker runtimes
stopped.** The stop is `two_job_supervisor.supervise`, which reuses W239528's
accepted termination, cleanup-journal and publication machinery — bound by
digest, so a change underneath it is a refusal rather than a passing run.

"""

WATCH_OLD = """Both Jobs' stages, allocations, workers, participants and runtime identities
are in `baton.v12.job-status/4`. **Overlap is read here**, as both Jobs'
implementation stages `waiting` at one observed instant — not inferred from two
submissions.
"""

WATCH_NEW = """Both Jobs' stages, allocations, workers, participants and runtime identities
are in `baton.v12.job-status/4`. **Overlap is read here**, as both Jobs'
implementation stages `waiting` at one observed instant — not inferred from two
submissions.

**`--control` is what makes this read say anything**, and it is not optional in
practice. Without it the projection reports `canonical: false`, which means
"nobody looked" rather than "nothing is running". My own diagnostic asked
`status` for stage states with no composition at all and printed
`AttributeError: 'NoneType' object has no attribute 'canonical'` on every
receipt for four claims; the recipe on this page was right and the diagnostic
was wrong. It now takes the read from inside the run, where the composition is
open, and the suite asserts both ends of it: every stage `offered` before any
turn answers, every stage `completed` at the last tick.
"""


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "## Step 4 — serve the bounded run" in body:
        raise SystemExit("REFUSED: the recipe is already replaced")
    start, end = body.index(START), body.index(END)
    if not 0 < start < end:
        raise SystemExit("REFUSED: steps 4 and 6 are not where expected")
    body = body[:start] + STEPS + body[end:]
    body = swap(body, WATCH_OLD, WATCH_NEW, "the watch note")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ("## Step 7 — stop, and prove the runtimes stopped",
                   "import sys, two_job_supervisor",
                   "--operations tools.stage_execution:factory"):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the page")
    for present in ("## Step 4 — serve the bounded run, as ONE command",
                    "two_job_supervisor.py", "--cleanup-seconds 60",
                    "## Step 5 — read the outcome",
                    "## Step 6 — watch, read-only"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the page")
    print("the operator recipe is the tested command, verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
