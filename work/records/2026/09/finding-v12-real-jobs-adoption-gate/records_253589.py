"""Claim-253589: guards become recovery; and I found an undefined name of mine."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 253589; RETURNED INCOMPLETE

Review 2026-09-24T03:57:08Z found three defects in my guards. All three are
corrected, and I found a fourth of my own while fixing them.

## The three, corrected

  1. **The wrapper required removed launch material before the core's own
     replay.** `intake.abandon_attempt` commits or REPLAYS its intent before
     any external call, and a repeat after a partial abandonment has no launch
     material left to adopt — so refusing unconditionally turned that replay
     into a refusal. Now an unadoptable delivery consults
     `abandoned_gate_discharge_of`: a recorded abandonment carries through to
     the core, and only an unrecorded one refuses.
  2. **Every composed stage refused, so the selected deployment could not
     recover.** The two-Job deployment always composes stages; my blanket
     refusal made the capability useless for the only run it exists for.
     Removed. A composed stage now recovers its roots through `_mounted`, which
     is what `ending` itself uses for an attempt it did not start; a worker
     with no stage composition uses `adopted_assignment_workspace`.
  3. **A malformed `stage` crashed my own refusal.** `(stage or {}).get(...)`
     calls `.get` on whatever was passed, so a string, a list or an int raised
     `AttributeError` out of the FORMATTING. The type answers first now, in
     both the worker and the router, and the refusal touches nothing.

**The durable binding is `launch.adopt`'s**, not a comparison invented here: it
holds the contract, the role, the transport, this attempt's `_job_execution`
and its provider context against the delivery the container actually mounted.
A second comparison over rows this composition does not own would be a weaker
door onto the same question.

## The fourth, mine, found while fixing the others

**`intake` was not imported in `single_worker.py`**, so
`intake.abandon_attempt(...)` — the one call the whole capability exists to
make — was an UNDEFINED NAME. The 162-case suite passed because nothing calls
the new method. A capability whose only call would raise `NameError` was not
written, whatever I said last claim. Imported now, and both modules import
cleanly.

## Evidence

`tests.tools.test_single_worker` — 162 tests, OK, 10.135s. Both modules import.
Every added line fits 79 columns. **This still does not exercise an
abandonment**, and I am not claiming the prior findings are all resolved.

## NOT DONE

  1. the focused behaviour tests, which are now the priority the review named
     over any broad suite: omission and mismatch, malformed stage types, a real
     stage composition, receiptless fault, prior cancellation fence, replay
     without recreated roots or deliveries, adapter refusal and uncertain
     absence, and positive root cleanup;
  2. the supervisor's explicit shutdown declaration;
  3. the new digest-bound manager snapshot, then fresh-run commands;
  4. the two operator grants documents with pure and fake-boundary validation;
  5. the executed-image fault diagnosis.

## Standing constraints

The deployed snapshot is immutable and was read only. The failed instance stays
preserved and read-only. No live rerun, deployed-store mutation, container
deletion or cleanup execution.

## Ownership

baton.claude owns this dossier and, from claim 253397,
`v12/python/tools/single_worker.py` and `v12/python/tools/stage_execution.py`.
"""

PROGRESS = """
## 2026-09-24 — baton.claude, claim 253589

### The guards were wrong in three ways and you named each

Refusing an unadoptable delivery blocked the core's own replay — `abandon_attempt`
commits or replays its intent before any external call, and a repeat after a
partial abandonment has nothing left to adopt. Refusing every composed stage
made the capability useless for the only deployment that needs it. And
`(stage or {}).get(...)` crashed on a string, a list or an int, out of the
refusal's own formatting.

All three are corrected: the journal decides whether a missing delivery is a
replay or a refusal; a composed stage recovers its roots through `_mounted`,
which is what `ending` uses for an attempt it did not start; and the type
answers first, in the worker and the router both.

The durable binding is `launch.adopt`'s rather than a comparison I invent — it
already holds the contract, role, transport, `_job_execution` and provider
context against the mounted delivery.

### And I found an undefined name of my own

**`intake` was never imported in `single_worker.py`.** The single call the
capability exists to make — `intake.abandon_attempt(...)` — would have raised
`NameError`. The 162-case suite passed because nothing calls the method, which
is exactly why I told you last claim that those suites do not verify the new
behaviour; what I did not say is that they do not verify it EXISTS. It does
now, and both modules import.

### The pattern I keep repeating in my own checks

Three times now a guard of mine has refused on text without asking where the
text is: `19 checks` in a page that also corrected it, `"180s per attempt"`
inside the sentence retracting it, and this claim's script refusing on
`(stage or {})` which survived only inside the comment quoting the defect. That
is a habit rather than three accidents, and the fix is the same each time —
ask where a string is, not merely whether it is there.

### Verification spending

`tests.tools.test_single_worker` — 162 tests, OK, 10.135s; plus an import
check. Disclosed as product-suite time: **10.135s** this claim, on top of
172.937s and 335.453s previously. The named suite subtotal is unchanged at
**1047.869180986s** (`verification-27.json`, 85 checks, 0 failures, pins
agree). The unmeasured 120s command-timeout run and all earlier unknowns stand.

I did not repeat `test_stage_execution` this claim: it takes 162s, never
exercises an abandonment, and the review said to prioritise the focused
behaviour tests over repeating broad suites.

State: returned INCOMPLETE through baton.bug with the remaining scope named.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 253589" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
