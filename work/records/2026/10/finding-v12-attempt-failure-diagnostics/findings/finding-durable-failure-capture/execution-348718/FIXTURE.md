# The gate passes. Two producer defects remain. This document is both.

**On the filename.** It says `FIXTURE.md` because `prepare.py`,
`verify-inputs.py` and two probes pin it by that name, and the review asked for
a *minimal* continuation reusing unchanged machinery — so renaming it would mean
editing exactly the machinery I was told to leave alone. **Its subject is now the
two producer defects**, plus the fixture work you must not break. Read it as
that.

Recorded by `baton.claude`, claim347396. Every citation was **read in the
candidate's own bytes**, not carried from the review.

## What is already won, and must survive

Run `durable-capture-w341357-345822` completed on its own at 733.29s and **its
sealed gate passed**:

```
Ran 864 tests in 12.631s
OK
```

exit 0, no skips — independently confirmed by the reviewer, who hashed the raw
stream in place. The worker's own in-turn run reported 864/0/0/0 in 11.398s;
that is a **separate measurement of the same argv**, not an independent
repetition.

The same-environment base comparison finally ran: the four modules both trees
share give **801 tests with 2 failures at the pinned base**, and the candidate
adds 63 tests and changes no other outcome. Those two were an **umask-dependent
fixture precondition** — the product read was right in both arms.

**Preserve all of this. It is the floor, not the ceiling:**

- `realpath` compatibility in the fixture roots;
- the **six** explicit cleanup-before-`setUp` sites in `test_intake`;
- the **three** `ExitStack`-scoped per-sub-case cleanup registrations in
  `test_maintenance`;
- the **two** explicit result-root ownership/mode preconditions;
- the existing empty-stdout child diagnostic;
- `W341357-VERIFICATION.json` as an **evidence-only** changed path, excluded
  from any later product import;
- the five-module gate passing with **no skips**.

The storage work stands as a **measured pressure reduction** — `/tmp` high-water
13303808 → 2437120 bytes, inodes 326 → 63 — and **not** as a retrospective proof
of which mount filled run345388. That cause did not reproduce and remains
unknown. No capacity operand is selected and none is needed.

## R1 — a fresh observation is conflated with a replay of an old one

**`failure_cause.py:524-545`.** `record_and_raise_cessation_outcome` walks the
chain and returns an existing revision whenever its facts match:

```python
for revision in range(OUTCOME_REVISIONS):
    operation_id = cessation_outcome_operation_id(attempt, component, generation, revision)
    held = _committed(store, attempt_id, operation_id, ...)
    if held is None:
        ...write and return...
    if _same_account(held, document):
        return operation_id, held
    previous = operation_id
```

**`_same_account` (line 461) compares the FACTS**, excluding only `revision` and
`supersedes` — deliberately, and its docstring says why. **Nothing in the
arriving document distinguishes a new sample from a redelivery.**

**`attempt_cessation_outcome_of` (line 841)** always answers the tip of the
chain.

**`intake.py:5966-5982`** re-samples the adapter on **every** settlement call
and records `ceased-quiescent` or `uncertain-observation` with the **same**
component, generation, runtime and correlation.

**The trace.** Same held revoked generation. Settlement sees `quiescent` →
revision 0. Sees `running`/uncertain → revision 1. Sees `quiescent` **again** —
a fresh adapter sample, not a redelivery. The recorder finds revision 0
fact-equal, returns it, writes nothing, and **the reader still reports revision
1, uncertain**. None of the three is `absent`, so all three stay held and the
path repeats. Reverse the order and a **stale positive** wins instead. No
generation change and no token release is needed.

**And the existing test does not cover this.**
`test_attempt_failure_cause.py:167-184`
(`test_a_REPLAY_of_a_SUPERSEDED_revision_writes_NOTHING_MORE`) supplies
identical input triples with **no identity that separates redelivery from a new
sample**. It proves value deduplication. It does not prove the thing that
matters.

**Required:** identify or sequence observations well enough that a fresh A→B→A
retains the third observation, while an **exact redelivery of the old A does not
supersede B**; the current read names the **newest accepted** observation, with
history preserved and bounded.

**Do not** solve it by changing the test to tip-only dedup and losing
old-replay correctness.

## R2 — recording failures are discarded on the acting paths

**The contract already exists and is honoured elsewhere.**
`record_cessation_outcome` (line 727) never raises; it returns `_reported(...)`,
and `recording_degraded()` (line 582) is the classifier. Three call sites do it
properly — `intake.py:5710-5711`, `intake.py:6058-6059` and
`attempts.py:3647`:

```python
if failure_cause.recording_degraded(reported):
    answer["diagnostic_degradation"] = reported
```

**These do not.** At `intake.py:5771-5775` (typed stop refusal) and
`:5788-5792` (uncertain observation) the call is a **bare statement** — the
return is dropped — and the function returns the ordinary dict:

```python
failure_cause.record_cessation_outcome(store, attempt_id, component="expiry-reclaim", ...)
return {"reclaimed": "held", "attempt_id": attempt_id, "state": "uncertain",
        "why": f"the stop was refused: {refusal.message}"}
```

The same shape appears at the unresolved-attachment branch, the positive-
cessation branch, the settlement non-absence path around `:5976`, and some
cancellation **exception** branches.

**The trace.** Intent commits. The reclaim stop raises a typed
`ContractRefusal`. Outcome recording then fails — a store write error. The
recorder returns **DEGRADED**; the caller discards it and returns exactly the
ordinary held/refusal result. The durable record stays **intent-only**, and
neither the returned account nor the durable reader tells an operator that the
known failure could not be captured. Symmetrically, an unrecorded later
observation can leave an older positive or unknown tip with no caller-visible
degradation.

**And one phrase is inconsistent.** `failure_cause.py:733-734`, the
malformed-fact branch, returns

```python
return f"; and the cessation outcome could not be recorded: {failed}"
```

which is **not** the `_reported` wording `recording_degraded` tests — so that
recording failure is invisible to the classifier. Keep the classification
consistent.

**Required:** propagate bounded, secret-safe recording degradation on **each**
affected result and exception path, using the existing structured channel or
another bounded compatible mechanism — **without masking the original engine
refusal**, and without weakening the uncertain holds, the fencing or the cleanup
semantics.

## What these two findings are, and are not

**Static traces, derived from the candidate's code.** Neither has been executed.
`TASK.md` asks you to make each one a **deterministic production-boundary
reproduction first**, because a passing gate that never injects an
outcome-write failure does not establish the behaviour either way.

## Where the evidence is

`../evidence/run-345822/` — the candidate patch, bundle, result, custody seal,
`W341357-VERIFICATION.json`, both preflights, my collection report and
`GATE-CLASSIFICATION.json`. The raw verification stream and the provider
transcript are **not** copied; their locator and sha256 are in the index, and
the reviewer hashed the stream in place at
`1031c25bca6d011d67b3d11e68ee27ff7f6df9cebecc2459bca5c76c05fac876`. Read them
in place:

```
baton-v12-stack logs --logs <launch-home>/logs --attempt <attempt-id> locators
```
