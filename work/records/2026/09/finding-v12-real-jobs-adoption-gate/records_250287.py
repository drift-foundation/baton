"""Claim-250287: the shadow was the cause; the command is asserted and green."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

PLAN = """# Current action — after claim 250287

## The cause, and it was in my source rather than in any root

Review 2026-09-23T19:04:38Z read `test_two_jobs.py` and found `answering`
defined at 724 and AGAIN at 763, with the later one — the one Python binds —
missing `self._composed = context["operations"]`. Every `main` turn therefore
reached `mounted_at` -> `job_execution_for` -> `composed_for` with no handle,
`_guarded` recorded it, and no implementation completed. That is the whole of
`{implementation: 2, review: 0}`. **No disposable-root hypothesis was needed,
and I should not have been writing one down while a source regression was
visible.**

## Done under claim 250287

  * **The shadow is removed, and it is now a FAILING check rather than a
    reading.** `NoCallbackInThisDossierIsSilentlyShadowed` refuses any class in
    any of this dossier's modules that defines one method twice, and asserts
    that the callback the class actually binds sets the composed handle.
    `SHADOW-GUARD-NEGATIVE-250287.log` is the proof it works: a copy with the
    shadow reintroduced fails both checks.
  * **Production now resolves to the SELECTED SNAPSHOT.** What I pinned last
    claim was cwd independence, which is a different property; the diagnostic
    now puts `/home/sl/baton-runs/independent-review-247947/manager-source`
    ahead of everything, takes only `tests` from the checkout, refuses if the
    snapshot is absent, and PRINTS every `baton_v12`/`tools`/`tests` module's
    `__file__` and SHA256 with `production_not_from_snapshot: []`.
  * **`status` is read with a LIVE composition**, from inside the turn. Four
    claims of receipts printed `AttributeError: 'NoneType' object has no
    attribute 'canonical'` because they asked after `main` had closed
    everything. ADOPTION step 6 was right all along; the diagnostic was wrong.
  * **The success through the command is ASSERTED**, with its negatives, its
    lifecycle protection and the assignment-generation distinction — four new
    cases on the class that owns `main`.
  * **The operator recipe is the tested command.** Steps 4, 5 and 7 collapse
    into the one `two_job_supervisor.py` invocation the suite drives; the old
    step 7 handed `job`, `control` and `composed` to the supervisor without
    ever defining them.

## The evidence

**53 checks, 0 failures, 47.112162907s** — `verification-18.json`. Four
separately retained diagnostic receipts, each on its OWN fresh disposable root:
`DIAGNOSTIC-250287-run1..4.log`, all reporting
`{implementation: 2, review: 2}`, both verdicts and `state: settled`.

So the single unexplained success of claim 250210 is explained: it ran before
the shadow was reintroduced.

## REMAINING

Nothing named by the reviewer is outstanding. What stands unproved is what the
packet says is unproved: the container boundary and the live provider under
concurrency, both of which are a separately selected runnable packet.

## Ownership

Reviewer-owned and immutable: ASSESSMENT-249338.md, every `review-*.md` and
`review-*.json`/`.log`. baton.claude owns the rest of this dossier.
"""

PROGRESS = """
## 2026-09-23 — baton.claude, claim 250287

### The cause was the regression the reviewer pointed at

`answering` was defined twice again — 724 and 763 — and the later one, the one
Python binds, never set `self._composed`. Every turn through `main` raised,
`_guarded` recorded it as one line of uncertainty, no implementation completed,
and the review stages stayed gated. That is `{implementation: 2, review: 0}`,
entirely, in current source.

I had been writing down a shared-root comparison while that was visible. The
reviewer was right to say so.

### What makes it stay fixed

`NoCallbackInThisDossierIsSilentlyShadowed`:

  * STRUCTURAL — no class in any module of this dossier defines one method
    twice. It reads the SOURCE, because by the time a class object exists the
    shadowed definition is already gone and nothing importable can see it.
  * BEHAVIOURAL — the callback the class actually binds sets the composed
    handle.

`SHADOW-GUARD-NEGATIVE-250287.log` retains a run against a copy with the shadow
put back: both checks fail. A guard nobody has seen fail is not a guard.

### Provenance, which is what was actually asked for

Last claim I pinned the diagnostic's imports so it ran from any directory and
reported that as the fix. The requirement was that production resolve to the
SELECTED SNAPSHOT. It now does: the snapshot goes ahead of everything, only
`tests` comes from the checkout, an absent snapshot is a refusal rather than a
silent fallback, and each receipt prints every module's `__file__` and SHA256
with `production_not_from_snapshot: []`. `tools/stage_execution.py` reads
`6a212c3a2edc5ddb7059e86350d95924aca4b059c059855939e4fd9771ab5801`, the pin.

### The live status read

Every earlier receipt answered "what are the stages doing" with
`AttributeError: 'NoneType' object has no attribute 'canonical'`, because it
called `status(store, None)` after `main` had closed the composition. The
supervisor already hands each tick `operations`, `job` and `control`, so the
read is taken there. First tick: both implementations `offered`, both reviews
`blocked`. Last tick: all four `completed`, `canonical: true`.

ADOPTION step 6 was correct; my diagnostic was not, and the page now says which
was which.

### The command, asserted

Four cases on the class that owns `main`: the success (four admissions, two
verdicts derived from their own frozen results, no outstanding cleanup, no
uncertainty, `settled`, exit 0); the supported live `status` at both ends of
the run; the REAL assignment generations, read back out of the control store
the command left behind and compared attempt by attempt; and the lifecycle —
an interruption inside a turn still publishes, still records itself, still
closes admission before cancelling and still raises.

The no-turn case is kept as the negative and now asserts `held` and exit 1
rather than accepting either.

One of those four was written against the shape I expected rather than the one
the accepted machinery documents: I asserted `stopped == "interrupted"`, and
`_guarded` deliberately catches `BaseException` so the shutdown is not
abandoned — `stopped` names how SERVING ended. The case now asserts the
guarantee that matters. The suite caught it before I reported it.

### The operator recipe

Steps 4, 5 and 7 are one command now — the `two_job_supervisor.py` invocation
the suite drives end to end. The old step 7 could not be typed: it handed
`job`, `control` and `composed` to the supervisor without defining them.
"What is deterministically witnessed" and "Remaining limitations" are corrected
too; they still claimed 19 checks and "no two-Job bounded supervisor exists".

### Verification spending

**`verification-18.json` — 53 checks, 0 failures, 47.112162907s.**

Named suite subtotal, adopting the reviewer's arithmetic: 368.174033529s +
47.112162907s = **415.286196436s**.

Also measured this claim, and NOT part of that subtotal: one suite run of
46.939s that FAILED two cases (the `pathlib` import and the interruption
assertion) — retained in this account only, no receipt; four separately
retained diagnostic runs at 4.693s, 4.681s, 4.657s and 5.590s, each on its own
fresh root; one earlier pinned diagnostic run at 4.714s that was not retained
as a log; and the shadow-guard negative proof at 0.016s. The earlier ~120s
timeout overlap remains UNKNOWN.

State: passed for independent review.
"""


def main():
    (HERE / "PLAN.md").write_text(PLAN, encoding="utf-8")
    progress = HERE / "PROGRESS.md"
    body = progress.read_text(encoding="utf-8")
    if "claim 250287" not in body:
        progress.write_text(body.rstrip("\n") + "\n" + PROGRESS,
                            encoding="utf-8")
    print("records written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
