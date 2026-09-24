"""Claim-250287: remove the superseded step 7, and correct what is witnessed.

The first pass replaced steps 4, 5 and 7's CONTENT but cut only as far as step
6, so the old "Step 7 — stop, and prove the runtimes stopped" -- the one whose
snippet hands `job`, `control` and `composed` to the supervisor without ever
defining them -- was still on the page underneath the command that replaces it.
The refusal in that script is what caught it; that is what the refusal is for.

This also corrects the two sections that have been stale since the supervisor
and its witness existed: "19 checks" and "No two-Job bounded supervisor
exists".
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "ADOPTION-247941.md"

START = "## Step 7 — stop, and prove the runtimes stopped"
END = "## What is deterministically witnessed, and what is not"

OLD_WITNESS = """`test_two_jobs.py`, 19 checks, over W130224's accepted two-Job fixture with
this arrangement's document substituted. A guard case asserts the served
document is THIS arrangement's rather than the fixture's own, so these are not
W130224's evidence re-presented as this Job's."""

NEW_WITNESS = """`test_two_jobs.py`, **53 checks**, over W130224's accepted two-Job fixture with
this arrangement's document substituted. A guard case asserts the served
document is THIS arrangement's rather than the fixture's own, so these are not
W130224's evidence re-presented as this Job's."""

OLD_NOT = """NOT witnessed here: **two FROZEN attributed verdicts**. Both reviewers are
reached on their own attempts, which is not the same as two collected verdicts,
and the packet does not claim it is. Also not witnessed, and covered by named
accepted evidence instead: the
container boundary (the turn is the fixture's deterministic one), the live
provider (W239528 and W239533, one Job at a time), and positive stop/cleanup
for four admitted attempts. See [CONTINUITY-247941.md](CONTINUITY-247941.md)."""

NEW_NOT = """Also witnessed, through the step 4 command itself rather than through its
parts: four admissions and no fifth; **two FROZEN attributed verdicts**, each
derived from its own Job's frozen result by the manager's own
`review_verdict_from_result`; the REAL assignment generation of every admitted
attempt, read back out of the control store the command left behind and
compared attempt by attempt — the ASSIGNMENT axis, not the pool's; positive
cleanup for every admitted runtime; a supported `status` read taken while the
composition is open, `canonical: true`, every stage `offered` before any turn
answers and `completed` at the last tick; and `state: settled` with exit 0.

Its negatives are witnessed too: a run whose workers never answer is `held`
with "no attributed verdict" and exits 1, and an interruption inside a turn
still publishes the outcome, still records itself in `interruptions` and
`held_because`, still closes admission before cancelling, and still raises.

NOT witnessed, and covered by named accepted evidence instead: the container
boundary (the turn is the fixture's deterministic one) and the live provider
(W239528 and W239533, one Job at a time). See
[CONTINUITY-247941.md](CONTINUITY-247941.md)."""

OLD_LIMIT = """1. **No two-Job bounded supervisor exists.** Step 7 names accepted machinery
   but no command drives it for four admissions. This is the smallest concrete
   implementation gap left, and it is an implementation gap rather than a
   product defect."""

NEW_LIMIT = """1. **The worker turn is a seam, not a running container.** The step 4 command
   drives four admissions, two verdicts and positive cleanup, and it does so
   with a deterministic turn standing exactly where a container would. With a
   real engine the runtime IS the turn. Everything on this page is therefore a
   composition and lifecycle result; none of it is evidence about a real
   provider under concurrency."""


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    start, end = body.index(START), body.index(END)
    if not 0 < start < end:
        raise SystemExit("REFUSED: step 7 is not where expected")
    held = body[:start] + body[end:]
    held = swap(held, OLD_WITNESS, NEW_WITNESS, "the witness count")
    held = swap(held, OLD_NOT, NEW_NOT, "the not-witnessed paragraph")
    held = swap(held, OLD_LIMIT, NEW_LIMIT, "the first limitation")
    PLACE.write_text(held, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in (START, "import sys, two_job_supervisor",
                   "--operations tools.stage_execution:factory",
                   "19 checks", "No two-Job bounded supervisor exists"):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the page")
    for present in ("## Step 4 — serve the bounded run, as ONE command",
                    "## Step 5 — read the outcome",
                    "## Step 6 — watch, read-only", "**53 checks**"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the page")
    print("step 7 removed and the witnessed sections corrected on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
