"""Claim-249641: R4 complete. The preparation is finished."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 249641

**R1, R2, R3 and R4 are all done. The preparation is complete and returned for
independent review.**

## Done under claim 249641 — R4's bounded run

`two_job_supervisor.supervise` serves the real composed `/2` deployment
through the four-admission gate and then, in this order: stops at
`total_seconds - cleanup_seconds` (600 − 60 = 540, so the reserve is INSIDE
the total); **closes admission BEFORE cancelling anything**; cancels every
attempt this run launched; reads the manager's own cleanup journal for each,
bound to this deployment's retention policy; and publishes an outcome **on
every path**. An interruption still raises after the outcome is retained and
carries it, as the accepted exception does.

Six whole-path checks over the real deployment and stores with an injected
clock: the bound and the published schema; admission closed before
cancellation; the cleanup window inside the total; a serving failure that
still publishes and holds; an interruption that publishes and still raises;
and a reserve outside the total refused before anything serves.

`ADOPTION-247941.md` step 7 now prints the command, and its limitation list
says what this evidence is: deterministic, with an injected clock and no
container started.

41 focused checks, 0 failures, measured 10.885859361005714s,
`verification-6.json`; 6 are new.

## The packet's standing recommendation

**NOT READY as a resolved current deployment; READY IN ARRANGEMENT.** What
remains is owner operand selection — every `<OWNER: ...>` in
SELECTIONS-247941.json — and, if an owner wants host concurrency proved
against the real engine, a separately selected live packet with its own
question. Neither is an implementation gap.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns two_jobs.py, two_job_supervisor.py,
test_two_jobs.py, ADOPTION-247941.md, CONTINUITY-247941.md,
SELECTIONS-247941.json, verify_247941.py, the `align_template.py`,
`add_roundtrip.py` and `apply_*.py` edit records, verification-*.json/.log,
PROGRESS.md, records_*.py and PLAN.md.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 249641

R4 is finished, so the preparation is.

### The bounded two-Job run

`supervise` is deliberately thin: the phases are separate, as they are in the
accepted single-Job supervisor, and every step that can be W239528's is.
Serving ends at `total - cleanup`, admission closes BEFORE cancellation --
which is what makes the cleanup window unable to start a runtime while it
settles the ones already launched -- cancellation runs per attempt, the
cleanup journal is read through `baseline._cleanups` bound to this
deployment's retention policy, and `baseline._publish` writes the outcome
atomically on every path.

Two things the accepted code corrected as I wrote it. `_cleanups` reads the
retention policy out of the DEPLOYMENT DOCUMENT rather than a restated copy,
because the destroy identity binds that digest -- so the supervisor takes the
deployment path rather than inventing a packet. And `SupervisorInterrupted`
carries the retained outcome as its second operand; raising it with only a
message would have thrown away the thing an interrupted operator most needs.

One test-side correction worth recording: my helper was called `run`, which
shadows `TestCase.run`, so every case in the class tried to execute the
supervisor instead of itself. Renamed to `driven`.

### What this evidence is, and is not

Deterministic, with an injected clock: a 600-second bound proved in
milliseconds. No container was started and no engine was asked to destroy one;
what the cleanup journal is asked about is what this run actually launched.
The packet's limitation list says exactly that rather than letting "positive
cleanup" read as a live claim.

### Verification spending

41 focused deterministic checks, 0 failures, measured 10.885859361005714s,
receipt `verification-6.json` with `verification-6.log`; 6 are new.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 = **36.848521004s**.
Pin checks are separate and were not measured. The reviewers' runs stay in
their evidence.

State: returned for independent review as a COMPLETE preparation.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 249641" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
