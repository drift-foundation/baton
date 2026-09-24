"""Claim-250569: the failure contract goes on the PAGE, where I said it was.

Review 2026-09-23T19:48:52Z: "Handoff 250536 and current PLAN say ADOPTION
explains pre-execution refusal versus an owed outcome. The current
ADOPTION-247941.md does not."

That is my error and it is a plain one: I wrote the distinction into a test
docstring and then reported that the page carried it. It did not. The page
still said the command publishes "on every path", which my own renamed case
contradicts -- it asserts NO file exists when the composition refuses -- and
which the publication-failure case contradicts too, since that one deliberately
leaves nothing on disk.

This writes the contract the page owes an operator:

  * before supervised execution, a refusal may leave no document;
  * once the protected run starts, finalization ATTEMPTS to publish;
  * a write failure propagates and may leave no file;
  * and a missing file or a process exit is not evidence that anything
    stopped or was cleaned up.

The positive-cleanup requirement is unchanged, and no code or test is touched
to make the old unconditional prose true.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "ADOPTION-247941.md"

OLD_PUBLISH = """the total, derives each Job's verdict from its own frozen result and publishes
`outcome.json` **on every path** — the bounded stop, a serving failure, a cap
refusal and an interruption alike.

It exits **0** when `state: settled` and **1** when `state: held`, so the exit
status is readable before any document is.
"""

NEW_PUBLISH = """the total, derives each Job's verdict from its own frozen result and attempts
`outcome.json`.

It exits **0** when `state: settled` and **1** when `state: held`, so the exit
status is readable before any document is.

### When there is a document, and when there is not

An earlier version of this page said the command publishes "on every path".
That was wrong in both directions, and this dossier's own cases say so.

  * **Before the supervised run begins there is no outcome to owe.** Reading
    the two documents, opening the stores, composing the deployment and
    submitting all happen before `supervise` is entered. A refusal there —
    an unresolved operand, a credential registry the production factory will
    not accept, a store it cannot open — **leaves no `outcome.json`**, and
    should: nothing was admitted, no runtime exists and there is no account to
    render. The command reports the refusal itself.
  * **Once the protected run starts, finalization ATTEMPTS the document on
    every path** — the bounded stop, a serving failure, a cap refusal, an
    interruption, and a fault in the accounting itself, which is named in the
    document as `finalization_failure` and re-raised after it is written.
  * **An attempt is not a guarantee.** If the write itself fails — a full or
    unwritable run root — that failure propagates to the operator and **may
    leave no file at all**. That is the one ending an operator cannot read
    about afterwards, and the command raises rather than exiting quietly.

**So a missing `outcome.json` is not an answer about the run.** It means
either that the command refused before starting or that it could not write;
neither is evidence that anything stopped, and neither is positive cleanup. The
same goes for a process exit: see step 5.
"""

OLD_STEP5 = """`state: settled` means every admitted runtime has positive cleanup, both Jobs
produced an attributed verdict, and nothing was refused or uncertain.
`state: held` names every reason in `held_because`. Positive cleanup vocabulary
is the accepted one: `complete` or `retained`; missing, failed or uncertain
cleanup is outstanding, not success.
"""

NEW_STEP5 = """**Read the document, not the absence of one.** If `outcome.json` is not there,
step 4 says what that means and what it does not: it is never a report that the
run ended cleanly.

`state: settled` means every admitted runtime has positive cleanup, both Jobs
produced an attributed verdict, and nothing was refused or uncertain.
`state: held` names every reason in `held_because`. Positive cleanup vocabulary
is the accepted one: `complete` or `retained`; missing, failed or uncertain
cleanup is outstanding, not success.

`finalization_failure` is null on a run that finished accounting for itself. A
value there names a fault that arrived after serving: the run published what it
had, forced itself to `held`, restored its signal handler and re-raised.
"""

OLD_EXIT = """**A process exit or `SIGTERM` alone is not proof that worker runtimes
stopped.**"""

NEW_EXIT = """**Neither a process exit, a `SIGTERM`, nor a missing document is proof that
worker runtimes stopped.** Only the cleanup account in `outcome.json` is."""

COUNTS = (
    ("""  * The deterministic witness (`test_two_jobs.py`, 53 checks) drives **that""",
     """  * The deterministic witness (`test_two_jobs.py`, 60 checks) drives **that"""),
    ("""`test_two_jobs.py`, **53 checks**, over W130224's accepted two-Job fixture with""",
     """`test_two_jobs.py`, **60 checks**, over W130224's accepted two-Job fixture with"""),
)


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "When there is a document, and when there is not" in body:
        raise SystemExit("REFUSED: the failure contract is already on the page")
    body = swap(body, OLD_PUBLISH, NEW_PUBLISH, "the publication paragraph")
    body = swap(body, OLD_STEP5, NEW_STEP5, "the step 5 opening")
    body = swap(body, OLD_EXIT, NEW_EXIT, "the process-exit warning")
    for old, new in COUNTS:
        body = swap(body, old, new, "a check count")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for absent in ("`outcome.json` **on every path**", "53 checks",
                   "**53 checks**"):
        if absent in written:
            raise SystemExit(f"REFUSED: {absent!r} survives in the page")
    for present in ("When there is a document, and when there is not",
                    "leaves no `outcome.json`", "may\n    leave no file at all",
                    "is not an answer about the run",
                    "60 checks", "**60 checks**",
                    "finalization_failure` is null"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the page")
    print("the failure contract is on the page, and the counts are current")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
