"""Claim-250107: the diagnostic runs, and it named the 2/0 cause."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250107

## Done under claim 250107

  * **The diagnostic is runnable.** What I kept last claim did not parse — a
    method body at module scope under a hyphenated filename nothing can
    import. `diagnostic_main_admissions.py` is a real module with a real
    case: it runs the documented command and prints ONE receipt — admissions,
    verdicts, stopped reason, state, `held_because`, uncertainty and stage
    states. It asserts nothing; it measures.
  * **It named the `2/0` cause on its first run, and the cause is MINE.** The
    turn called `self.mounted_at(...)`, which reads `self._composed` — a
    handle the fixture's own `serving` sets and `main`'s composition does not.
    Through the command every turn raised `AttributeError`, was recorded as
    uncertainty, and the implementations never completed. Nothing about the
    product was wrong; the witness could not write into the workspace.
  * The turn now sets that handle from the runtime context.

47 focused checks, 0 failures (`verification-17.json`, unchanged this claim).

## HONEST LIMIT ON THE LAST STEP

After supplying the handle, the diagnostic rerun still printed the OLD
`_composed` uncertainty and `{implementation: 2, review: 0}`. I did not clear
`__pycache__` before that rerun, so **I cannot say whether the fix took
effect** — the observation may be a stale module. The next claim's first act
is one clean rerun: clear caches, run `diagnostic_main_admissions`, read the
receipt.

Also still open: the `main` success case, its four negatives, lifecycle
protection, the generation regression through `main`, and the tested operator
recipe replacing steps 4 and 7.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250107

### The diagnostic I kept did not parse

A method body pasted at module scope, under a hyphenated filename nothing can
import. Keeping a broken artifact is worse than keeping none, because it reads
as evidence. `diagnostic_main_admissions.py` is a real module with a real case
and a pinned command in its docstring; it prints one receipt and asserts
nothing.

### It named the cause on its first run, and the cause was mine

The turn called `self.mounted_at(...)`, which reads `self._composed` — a handle
the fixture's own `serving` sets and `main`'s composition does not. Through the
command EVERY turn raised `AttributeError`, `_guarded` recorded it as
uncertainty, and the implementations never completed — so the review stages,
gated on completion, never opened. `{implementation: 2, review: 0}` was my
witness failing to write into the workspace, not a product question. Three
claims of narrowing ended at a handle I never passed.

The turn now takes that handle from the runtime context.

### What I could NOT confirm, and am not claiming

The rerun after that fix still printed the OLD uncertainty and the same
`2/0` — and I had not cleared `__pycache__` before it. So the observation may
be a stale module and **I cannot say whether the fix worked.** The next claim
begins with one clean rerun rather than another theory.

### Verification spending

No new suite run this claim; `verification-17.json` (47 checks, 0 failures,
26.044478883006377s) stands. The diagnostic's two runs are measurements, not
receipts: 1.539s and one rerun whose elapsed time the runner printed as part
of its own output rather than a receipt.

Cumulative MEASURED for W247941 stands at **237.934033529s**, plus the
previously recorded ~120s timeout execution whose overlap remains UNKNOWN.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250107" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
