"""Claim-250036: the context seam lands; a main success does not, and why."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250036

## Done under claim 250036

  * **The turn gets its runtime context.** `supervise` now hands each tick's
    callback `{"operations", "job", "control"}`, so a turn can reach the
    attempt's mounted workspace — which is what a container would write into.
    A callback given only the gate could do no work, which is why the first
    entry-point case proved nothing.
  * **`main` takes `monotonic` and `sleep`**, with PRODUCTION DEFAULTS
    unchanged, so a deterministic witness need not spend eight real seconds on
    arithmetic proved elsewhere and an operator's invocation is untouched.
  * The supervisor success case uses the context rather than a captured
    fixture handle, and still passes.

47 focused checks, 0 failures, measured 25.86033196898643s,
`verification-16.json`.

## A CONCRETE FINDING, not yet explained

A success THROUGH `main` was written and **withdrawn rather than left
failing**: driven with the shipped-template documents, the disposable provider
and engine, an answering turn and an injected clock, `main` admitted
**nothing** — `{"implementation": 0, "review": 0}` — where the same turn
through `supervise` admits four. The seams are in place; something between
`main`'s composition of the shipped documents and the first admission is
different from the fixture's own `serving_two`, and I did not diagnose it
before my working budget ran out. I am not guessing at it in prose.

That is the next thing to do, and it is the last substantive gap before the
`main` negatives and the operator recipe.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250036

### The seams you authorised

`supervise` hands each tick's callback the runtime context —
`{"operations", "job", "control"}` — so a turn can reach the attempt's mounted
workspace. Without it a callback could do no work, which is precisely why the
first entry-point case proved nothing. And `main` now takes `monotonic` and
`sleep` with production defaults unchanged, so a deterministic witness does not
spend eight real seconds on arithmetic that a controlled clock already proves.

The supervisor success case now takes its mount from the context rather than a
captured fixture handle, and still passes.

### The finding I am handing over rather than guessing at

I wrote the `main` success — shipped-template documents, disposable provider
and engine, an answering turn, injected clock — and it admitted NOTHING:
`{"implementation": 0, "review": 0}`, where the identical turn through
`supervise` admits four. **I withdrew the case rather than leave a failing
suite or weaken its assertions to pass.**

Something between `main`'s composition of the shipped documents and the first
admission differs from the fixture's own `serving_two`. I did not find it
before my budget ran out, and I am not putting a guess in the dossier as if it
were a diagnosis. The seams are in place; the next claim starts by comparing
those two compositions.

### Verification spending

47 focused deterministic checks, 0 failures, measured 25.86033196898643s,
receipt `verification-16.json` with `verification-16.log`. No new checks: the
one written this claim was withdrawn.

An earlier run in this claim hit the 120-second command timeout because `main`
was serving on the real wall clock at 600/60 before I bounded it; that
invocation produced no receipt and its duration is recorded here as
approximately 120 seconds of process time, not as verification spending.

Cumulative MEASURED for W247941, every retained invocation preserved:
1.678180975 + 2.122556141 + 2.145897528 + 2.868183810 + 2.876618006 +
3.646601886 + 3.682941216 + 6.941682081 + 10.885859361 + 10.943187142 +
10.857 + 11.135997740 + 11.183168619 + 11.520278754 + 11.597300884 +
11.682510099 + 14.049334683 + 13.071588666 + 17.320021491 + 25.820313595 +
25.860331969 = **211.889554646s**.

State: returned INCOMPLETE through baton.bug with a concrete finding.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250036" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
