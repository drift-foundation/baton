"""Claim-250134: the shadowed helper, and the next error underneath it."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250134

## Done under claim 250134

  * **`answering` was defined TWICE and my fix had landed in the other
    helper.** Two definitions of one name in a class is silent shadowing: the
    second wins, the first is unreachable, and a correction applied to the
    wrong one LOOKS applied. That — not a stale `__pycache__` — is why last
    claim's rerun printed the old error. There is one `answering` now, and it
    sets `self._composed` from the runtime context.
  * The edit script asserts the shape afterwards: exactly one definition by
    `ast`, and the handle set in both callbacks.

## The diagnostic's current receipt

`{implementation: 2, review: 0}`, `state: held`,
`stopped: serving-bound-exceeded` — and the uncertainty has CHANGED:

    AttributeError: 'NoneType' object has no attribute 'document'

The `_composed` error is gone; the turn now reaches one layer deeper and fails
there. **That layer is not yet identified.** It is the next thing to read, and
the diagnostic prints it on every run.

## REMAINING

The `main` success and its negatives; lifecycle protection; the generation
regression through `main`; the tested operator recipe replacing steps 4 and 7;
and the diagnostic's own command, which still names the checkout rather than
the pinned snapshot and reads status with `operations=None`.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250134

### A shadowed helper, not a stale cache

`answering` was defined twice in one class. The second definition wins and the
first is unreachable, so the fix I applied last claim — to `turning`, the
direct-supervisor helper — looked applied and was never reached by the
diagnostic. My "maybe it is a stale `__pycache__`" was wrong, and the source
said so plainly to anyone who looked, which the reviewer did.

There is one `answering` now, it sets `self._composed` from the runtime
context, and the edit script asserts the shape afterwards by `ast` rather than
by hope: exactly one definition, and the handle set in both callbacks.

### The error underneath

The diagnostic's uncertainty has changed from

    AttributeError: 'MainAdmissions' object has no attribute '_composed'

to

    AttributeError: 'NoneType' object has no attribute 'document'

`{implementation: 2, review: 0}` still. The turn now gets further and fails one
layer deeper, at something the fixture's own serving path supplies and `main`'s
composition does not. I have NOT identified that layer, and I am not naming a
candidate without reading it.

### Verification spending

No new suite receipt this claim. `verification-17.json` (47 checks, 0 failures,
26.044478883006377s) stands, and the confirming suite run last claim measured
25.973s.

Cumulative MEASURED for W247941, with the reviewer's correction applied —
their arithmetic adding the 25.973s confirming run gives **263.907033529s** —
plus the diagnostic's own runs, whose durations the runner printed but which I
did not receipt, and the earlier ~120s timeout execution whose overlap remains
UNKNOWN.

State: returned INCOMPLETE through baton.bug.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250134" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
