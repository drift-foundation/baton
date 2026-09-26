# W266336 implementer progress

## Claim 267642 — stage 2 proved on reachable paths; NO product change needed

ONE bounded command, six cases, 0.038s, real disposable stores and a controlled
adapter. `intake.py` and `attempts.py` are UNCHANGED, and that is the finding: on
every path reachable here the resource is already held while a submission's
outcome is unsettled.

### What was forced, and what it measured

1. **Cancellation DURING the launch.** The public `abandon_attempt` ending runs
   from inside `adapter.start` — reservation committed, no runtime yet, submitter
   genuinely mid-flight. It REFUSES ("no attached runtime"), the lane row still
   holds `attempt-1`, and the late submission then completes and is ACCOUNTED
   FOR: one runtime, named `runtime-1`, axis `running`, lane still held. Nothing
   was removed.
2. **An unknown outcome stays held.** The submit faults and the fake lists
   nothing. The manager records `uncertain` — never `destroyed` — leaves cleanup
   `pending` and KEEPS the lane.
3. **No ending talks past that state.** From `uncertain`, `abandon_attempt`
   refuses again: reconciliation's silence is not discharge evidence.
4. **The second public entry releases nothing here either.**
   `authorize_failed_start_cleanup` refuses, and the case asserts THE BOUNDARY IT
   ACTUALLY STOPS AT rather than the one I first expected.
5. **The replacement is refused.** An activated successor of the same Work meets
   the lane's predecessor interlock — "still holds this Work's runtime lane" — and
   its own adapter is never asked to start anything.
6. **POSITIVE RELEASE, so the pair discriminates.** Once the start settles (a
   runtime attached and named) and the ending observes absence, the ending
   releases: axis `destroyed`, cleanup `retained`, lane EMPTY, and the successor is
   admitted and reaches its adapter. Without this case the held ones would be
   satisfied by a lane that is simply never returned.

### Simulated boundaries, named as the thread requires

The engine is the accepted FAKE adapter. "The launcher was killed mid-submit" is a
fault this module raises, not an observed process death; "nothing is listed" is the
fake's answer; and the absence in case 6 is the fake's too. A fake cannot attest
that a real engine terminated or that a real submission cannot continue. Nothing
here claims it does.

### Two honest limits

- **The typed guard I did not reach.** `authorize_failed_start_cleanup` carries a
  `runtime-observation` / `quiescence-unknown` refusal for an `uncertain` attempt
  (intake.py:2175), whose message says there is "nothing to prove absent". I READ
  it; I did not execute it, because an earlier boundary refuses first — the failed
  start must be fenced at the authority before anything is destroyed. Reaching it
  needs generation fencing, which is setup this stage does not add. Recorded as a
  source reading, not as evidence.
- **`request_cancellation` / deadline expiry were not driven.** The ending path was.
  The cancellation-proper entry and the deadline-to-cancel wiring remain
  unexercised here.

### THE GAP THIS EXPOSES, and it is the useful one

`uncertain` is held correctly — and I found NO demonstrated path OUT of it. Both
public endings refuse it, so the lane stays occupied and the Work admits no
successor, indefinitely, with no operator mechanism demonstrated to resolve it. The
conservative half of the owner's requirement is met exactly; the recovery half has
no supported evidence path, which is the same shape as W257624's unresolved
never-created-helper release gap. That belongs to whoever selects stage 3 or an
operator-recovery Work; it is NOT fixed here and not silently deferred.

### Verification

    cd /home/sl/src/baton/v12/python
    BATON_V12_DISK_ROOT=/var/tmp/baton-w266336 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-delayed-launch-cancellation \
    timeout --signal=TERM --kill-after=5s 200s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_delayed_launch_release

6 cases OK in 0.038s. Selector: this module only; its `load_tests` collects just the
cases defined here, so the accepted fixture's own cases are not re-run or counted.
`tests.manager.test_attempts` carries no live class. Earlier in the claim: four
in-memory diagnostics (0.005s, 0.008s, 0.007s, 0.007s, 0.006s) and three failing
intermediate runs (0.025s, 0.038s, 0.038s) recorded honestly rather than hidden.

### Hashes

- `work/records/2026/09/finding-v12-delayed-launch-cancellation/test_delayed_launch_release.py`
  sha256 `b2bddc13e82e86e5cfcaa40a4b65bff3d941a248f0ef48b3ca32b76f283886d4`
- `v12/python/src/baton_v12/worker_manager/intake.py` sha256
  `b8b6ae30d8fc99fec2fd63f1977b7e093e3fd610cd4ac14470fae45c3f2532c5` UNCHANGED
- `v12/python/src/baton_v12/worker_manager/attempts.py` sha256
  `85a7d1953425782ed76961ab24859ee6fb6171c47266415a6e28cf2a52fc978d` UNCHANGED —
  stage 1's accepted state, preserved as owner 267612 requires

## Claim 267926 — R1 and R2 corrected; the real cancellation is now crossed

Review 2026-09-25T18-00-11Z was right on both counts, and the corrections found
more than they fixed. Eleven cases, one command, 0.073s. STILL NO PRODUCT CHANGE:
no case demonstrates the code violating the predicate.

### R1 — the schedule now crosses an ACTUAL cancellation

My earlier case called `abandon_attempt`, which refuses at its
no-attached-runtime precondition BEFORE any fence; it proved a precondition, not
a cancellation. `attempts.request_cancellation` now runs from INSIDE
`adapter.start`, and the fence is MEASURED rather than assumed: the session's
cancel was called (`order == ["fence"]`), the answer carries
`fenced.fenced is True`, its intent names this attempt, and the axis moves
`start-requested` -> `cancel-requested` with the lane still holding.

THREE FACTS THE CROSSING EXPOSED, all asserted:

1. The late submission still crosses — the fake creates `runtime-1` carrying this
   attempt's exact labels.
2. `adapter.stopped == []`: the ordered quiescence CANNOT have covered that
   runtime, because it was ordered before the runtime existed.
3. The manager then REFUSES to record it: `runtime-observation` /
   `state-regression`, "'running' does not follow it", for the post-start
   reconciliation AND for `reconcile_runtime` called directly with and without
   the minted identity. So `runtime_id` stays NULL.

That third fact is the stale-generation acceptance boundary the thread asked for,
measured at its real refusal rather than described.

### R2 — both sides, and the concrete missing mechanism

HELD SIDE: with the engine holding that runtime and the manager unable to name
it, every supported operation refuses and the lane stays held —
`reconcile_runtime` (`state-regression`), `abandon_attempt` ("no attached
runtime"), `authorize_failed_start_cleanup` ("no committed failed-start record").
A replacement is refused by the lane interlock and never reaches its adapter.

THE MISSING MECHANISM, STATED AS THE REVIEW REQUIRES: I attempted those three
supported operations and none accounts for a runtime created AFTER its generation
was fenced. Held is the correct outcome, and the limit of the claim is that THIS
SUITE demonstrated no such resolution — not that none can exist. I am not
assigning that to stage 3 and not declaring it resolved.

RELEASE SIDE, on a cancelled path rather than an ordinary abandonment: when the
runtime is attached BEFORE the cancellation, the ordered quiescence has an
identity to act on — `adapter.stopped == ["runtime-1"]` — the ending then
observes absence, the axis reaches `destroyed`, cleanup `retained`, the lane is
RELEASED, and only then is the successor admitted and reaches its adapter. The
predicate is live, and its evidence order is what the case measures.

### The quiescence-unknown guard, reached — and why the obvious setup fails

Driving the local cancellation makes that guard UNREACHABLE: it moves the axis off
`uncertain`, so the ending refuses for a missing runtime identity instead. The
case therefore models the other real ordering — the authority has moved on while
this manager's start outcome is unknown — by advancing the accepted fake's
`live_assignment`. That projection change is FIXTURE SETUP, labelled as such in
the case, not evidence about a real authority. With it, the ending answers
`runtime-observation` / `quiescence-unknown`: "nothing to prove absent", lane
retained, cleanup pending.

### Corrections to my own previous record

- The prior entry said "four in-memory diagnostics" and enumerated five durations.
  The review preserved that as an accounting discrepancy; it was five, and the
  count was wrong, not the list.
- The prior entry's "no demonstrated path OUT of uncertain" was stated as a gap to
  hand onward. That overreached: two precondition refusals do not establish that
  no supported path can exist. The claim is now limited to what this suite
  measured, and stays inside stage 2.
- PLAN.md was absent when I received this Work and I did not notice; the reviewer
  supplied it. I read it this claim.

### Verification

Same single-module selector and command as before; 11 cases OK in 0.073s. This
claim also ran five in-memory diagnostics (0.007s, 0.008s, 0.008s, 0.007s, 0.007s)
while tracing which guards are reachable, and four red intermediate runs (0.064s
three times and 0.058s) as the fencing setup was corrected. Nothing rerun to
improve a number.

### Hashes after this claim

- `test_delayed_launch_release.py` sha256 `8e1d4a5ddf19fec461d47dc5dd4fb7d6b8f347d30d64bb6580818bf8bc516752`
  (previously `b2bddc13e82e86e5cfcaa40a4b65bff3d941a248f0ef48b3ca32b76f283886d4`).
  I first wrote a placeholder here instead of the measured digest and corrected it
  in the same claim; a hash nobody computed is worse than no hash.
- `attempts.py` and `intake.py` UNCHANGED — stage 1's accepted state preserved

## Claim 268035 — the pinned correction, recorded BEFORE any edit

Review 2026-09-25T18-19-46Z requires the design and exact product ownership pinned
before editing. This section is that pin, written first.

**THE FAILING BOUNDARY, as the review pinpointed and I confirmed by reading:**
`attempts._attach` (attempts.py:2649) performs the identity compare-and-swap and
then, INSIDE THE SAME ACT, `observe(... axis="execution_runtime", value=value)`.
The coupling is deliberate — its own comment explains that an effect outside the
transaction is not part of the act — but it means a value the axis cannot accept
aborts the whole act, so the identity is never attached. On a cancelled attempt
`value` is `running`, and `TRANSITIONS["execution_runtime"]["cancel-requested"]`
is `["stopping", "quiescent", "uncertain", "destroyed"]`: `running` is correctly
absent, because eligibility must not revive.

**THE CHOSEN CORRECTION, minimal and inside the existing act:** when the
observation cannot follow the current axis because the attempt is already
`cancel-requested`, attach the identity and record `stopping` instead of
`running`, carrying a `why` that names it. Reasons this is the right shape:

- `stopping` IS a legal successor of `cancel-requested`, so no transition rule is
  weakened and no new state value is introduced.
- It does not revive eligibility: from `stopping` only `quiescent`, `uncertain`
  and `destroyed` follow — never `running`.
- It is not an invented observation about the world. The cancellation this manager
  performed ALREADY ordered quiescence; `stopping` states the manager's own act,
  which is precisely what distinguishes it from inferring destruction.
- The attachment stays atomic with its axis move, preserving the effectively-once
  property `_attach` exists to protect.
- Nothing else changes: any value that legally follows the axis is recorded as
  today, and any other regression still refuses.

**WHAT I WILL NOT DO:** no journal bypass, no raw product-state SQL, no clearing
an unknown by assertion, no relaxation of the fence, the lane interlock or the
hold requirements, and no change to `intake.py`.

**EXACT PRODUCT OWNERSHIP:** `v12/python/src/baton_v12/worker_manager/attempts.py`,
function `_attach` only. Authorized as owner 267612's "minimal fixes" for this
demonstrated path, at the boundary review 2026-09-25T18-19-46Z named. Stage 1's
accepted behaviour in `request_runtime_start` is untouched, and its immutable
regression is expected to keep passing.

### Selector for this claim, recorded BEFORE execution

    test_delayed_launch_release          (mine, stage 2)
    test_reserve_before_launch           (stage 1, accepted — must not regress)
    review_stage1_stale_start            (reviewer's immutable regression)
    tests.manager.test_attempts          (the accepted suite that OWNS the changed code)

The fourth is new this claim and needs its justification: I changed
`attempts._settled`, and `tests.manager.test_attempts` is that function's own
accepted suite. Running the module I edited is the narrowest check that a product
correction did not break its owner; skipping it would be leaving the obvious
question unasked. It is one module, fake-adapter only, and carries no live class.

### What the correction actually landed as — and a correction to my own pin

I pinned `_attach`, and the first attempt put the mapping there. THE RUN
DISAGREED: `_settled` records the observation a SECOND time outside the
attachment ("RECORDED ON EVERY PASS", by its own comment) and builds the answer
from the same value, so mapping inside `_attach` left the attachment succeeding
and the next record refusing `state-regression` on `stopping`. `_settled` is the
ONE OWNER of what an identification means -- attachment, the on-every-pass
record and the answer -- so the mapping belongs there and nowhere else. The pin
above is left as written and this paragraph is the correction to it, because a
pin quietly edited after the fact is not a pin.

### Results

- stage 2 `test_delayed_launch_release`: 10 cases OK.
- with stage 1 `test_reserve_before_launch` and the reviewer's immutable
  `review_stage1_stale_start`: 20 cases OK, 0.166s — stage 1's accepted behaviour
  and the immutable regression both unaffected.
- `tests.manager.test_attempts`, the accepted suite that OWNS the changed
  function: 429 cases OK, 3.994s.
- NON-VACUITY: with the mapping removed in place, the two safe-outcome cases fail
  `None != 'runtime-1'` — the late runtime is unnamed again. Revert and restore in
  one act, verified by re-hashing.

### The safe release now proved on the SELECTED schedule

The cancelled-mid-launch schedule now runs through settlement: the late runtime is
named (`runtime_id = runtime-1`, axis `stopping`, never `running`), the ending
removes THAT exact runtime (`adapter.abandoned == ["runtime-1"]`), absence is
observed, the axis reaches `destroyed` with cleanup `retained`, the lane is
released and only then is a successor admitted. The normal-start-then-cancel case
remains as a control and is labelled as one.

### R2 at the real boundary, with its gate chain

`output.request_freeze` is the supported result-acceptance entry. On this schedule
it refuses three times for three different reasons, and the case asserts the chain
rather than only the last: not quiescent ("only a positive quiescent
observation"), then no recorded turn outcome, then declared-vs-recorded mismatch,
and finally — once those are satisfied — THE GENERATION: "the live assignment is
... and this attempt is fixed to ...", with the output axis still `open`.

### Hashes

- `test_delayed_launch_release.py` sha256 `3cdedbfd0007044521338e5310999516b2141d4dfaa29ec60bbf1c1be6c40fba`
- `v12/python/src/baton_v12/worker_manager/attempts.py` sha256 `365cddca243ea4d88fbf4a1ae4b8097a6edd32341e37daa5894e069399903f81`
  (was `85a7d1953425782ed76961ab24859ee6fb6171c47266415a6e28cf2a52fc978d`; the
  ONLY product change, confined to `_settled`)
- `intake.py` UNCHANGED at
  `b8b6ae30d8fc99fec2fd63f1977b7e093e3fd610cd4ac14470fae45c3f2532c5`

## Claim 268146 — the pinned correction for the pending-submitter release

Pinned BEFORE editing, as review 2026-09-25T18-36-24Z requires.

**THE DEFECT, and it is mine.** My accounting correction made the late runtime
nameable, and that turned out to ENABLE a premature release: the reviewer's
immutable `review_pending_submitter_release.py` shows a second real handle
cancelling, reconciling and abandoning while the ORIGINAL submitter is still
inside `adapter.start`, emptying `runtime_lanes` before that call returns. Runtime
visibility plus a fake's absence was accepted as release evidence. Another
manager's reconciliation is not proof that the old submitter cannot continue.

**WHAT EVIDENCE IS MISSING, exactly.** Nothing durable said "the submitting call
has returned from the external start". Every fact the endings consult -- the
attached identity, the axis, the adapter's listing, the absence observation -- can
be produced by a DIFFERENT manager. So the gate must rest on a fact only the
submitter can write.

**THE CHOSEN CORRECTION, two small edits.**

1. `attempts.request_runtime_start` writes a SUBMITTER-ONLY fact. After
   `adapter.start` returns -- on the success path AND on the refusal and fault
   branches, because in all three the submitting call has come back -- commit one
   short pure transaction under identity `_start_operation_id(attempt) +
   ":returned"`, kind `runtime.start-requested`, whose declared members are
   exactly `(attempt_id, operation_id)`. No new document kind is introduced.
   It is submitter-only because `request_runtime_start` is the only writer and it
   refuses any caller whose axis is not `not-started`, so a second manager cannot
   be inside it.
2. `intake.py` gates BOTH lane releases on that record. Immediately before each
   `_release_lane(...)` the ending asks whether this attempt's start submission
   has returned; if a start was requested and has not, it raises a NON-DURABLE
   refusal, so the whole settlement rolls back and the reservation, the axis and
   the cleanup state all stay exactly as they were. An attempt that never
   requested a start has nothing pending and is unaffected.

**WHY THIS IS THE RIGHT SHAPE.** It adds no state value, no document kind and no
new lifetime; it cannot be manufactured by another manager; it keeps the
conservative outcome (pending or unknown stays held through cancellation,
reconciliation and absence); and it releases on the SAME schedule once the
submitter has demonstrably returned and its runtime is accounted for.

**WHAT I WILL NOT DO:** no raw-state mutation, no permanently disabled release,
no skipped cancellation, no stage-3 broadening, and no touching W257624's pending
`intake.py:_settle` control operand -- that question is separate and stays open.

**EXACT PRODUCT OWNERSHIP:** `v12/python/src/baton_v12/worker_manager/attempts.py`
(`request_runtime_start`, plus one small reader) and
`v12/python/src/baton_v12/worker_manager/intake.py` (the two `_release_lane` call
sites only). Both are the demonstrated path owner 267612 authorizes minimal fixes
on. `documents.py` and `schema.py` are NOT touched.

**AND TWO REPORTING CORRECTIONS I OWE (R2).** My `stopping` prose said "the
ordered quiescence stands", but in this schedule cancellation answers
`quiescence.ordered=False` with no stop command, so intent, order and discharge
are three different facts and my text conflated them. And my previous handoff
claimed the publication case asserts intermediate missing-outcome and
disposition-mismatch refusals; the final test asserts the non-quiescence refusal
and the generation refusal, and satisfies the other gates through setup. Both are
corrected in this claim.

### Selector for claim 268146, recorded BEFORE execution

    review_pending_submitter_release     (reviewer's new immutable regression)
    test_delayed_launch_release          (mine, stage 2)
    test_reserve_before_launch           (stage 1, accepted — must not regress)
    review_stage1_stale_start            (reviewer's immutable stage-1 regression)
    tests.manager.test_attempts          (owns `request_runtime_start`/`_settled`)
    tests.manager.test_intake            (owns the two gated release sites)

The last two are the accepted suites that own the two files this claim changes.
`intake.py` is edited for the first time in this Work, so its suite joins for the
same reason `test_attempts` did: running the module I edited is the narrowest
check that a product correction did not break its owner. Both are single modules,
fake-adapter only, and neither carries a live Docker or Podman class.

### Results for claim 268146

- The reviewer's immutable `review_pending_submitter_release.py` passes UNCHANGED.
- 22 cases OK in 0.184s across that regression, my stage-2 module, stage 1 and the
  stage-1 immutable regression.
- `tests.manager.test_attempts` + `tests.manager.test_intake`, the accepted suites
  owning the two changed files: 633 cases OK, 7.770s.
- NON-VACUITY: with both gates removed in place, the reviewer's regression fails
  `[] != ['attempt-1']` and my positive counterpart fails because the early ending
  ANSWERS instead of refusing. Revert and restore in one act, verified by
  re-hashing.

### The positive counterpart, and one thing it taught me

It mirrors the reviewer's two-handle shape: the second manager cancels, reconciles
and tries to end while the original `adapter.start` has not returned -- refused,
reservation untouched -- and then, once the original call returns, THE SAME ending
settles, releases and admits a successor. Writing it, I first retried the ending
with a DIFFERENT reason and the store refused by §4.2: the first call had already
fenced and journalled its intent before my gate refused the settlement, so the
ending is RETRYABLE but not RE-DESCRIBABLE. The case now retries as the same act
and says why.

### Hashes

- `test_delayed_launch_release.py` sha256 `e9ded990075d0554c18dece22375d2c7d84de03cdea1bcde36c00b01a60d09da`
- `attempts.py` sha256 `0e84241ad4315ae6b5f6a064d6f704ae1c42063f65e6016d81a274d0ebabc95e`
- `intake.py` sha256 `9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2`
  (was `b8b6ae30d8fc99fec2fd63f1977b7e093e3fd610cd4ac14470fae45c3f2532c5`; the two
  gated release sites are the only change, and W257624's pending `_settle` control
  operand is untouched)

## Claim 268217 — the fault path really records the marker now

**MY COMMENT AND MY HANDOFF BOTH CLAIMED SOMETHING THE CODE DID NOT DO.** I said
the submitter marker was written "on the success, refusal AND fault paths alike".
The call sat AFTER the try/except, so only the success path reached it, and the
`ContractRefusal` branch had its own call -- the generic `Exception` branch had a
COMMENT saying it was recorded "below" and nothing else. Review
2026-09-25T18-48-10Z found it with `review_fault_return_release.py` (verified
sha256 `8e586f99…` before running, never edited): after an exact fault whose
runtime IS known, the release gate correctly refused for a missing marker and the
cleanup was blocked FOREVER.

**THE CORRECTION:** `_record_start_returned` is now called in the fault branch
too, BEFORE `_settled_and_recorded`, so the marker survives even a settlement that
raises in its turn, and the original fault is still re-raised unchanged by the
bare `raise`. Nothing else moved: no gate removed, no raw-state workaround, no
change to the pending/unknown hold, and stage 1 untouched.

**AND THE MARKER'S MEANING IS NOW BOUNDED IN THE SOURCE.** Its docstring says
plainly that a local return is NOT proof a real engine finished anything -- it
means only that the manager's own submitting call is no longer in flight, which is
the fact the gate was missing. Runtime accounting and absence remain separate
conditions that the gate also requires.

**AND ASSERTED FROM BOTH SIDES.** The reviewer's case settles a fault whose
runtime is known. My new
`test_the_return_marker_alone_does_not_release_the_resource` takes the fault where
NOTHING is listed: the marker IS present, and the resource still stays held with
the ending refusing, because accounting is absent. Necessary, and not sufficient.

**RESULTS.** 24 cases OK 0.196s across both reviewer regressions, my stage-2
module, stage 1 and the stage-1 regression. `tests.manager.test_attempts` +
`tests.manager.test_intake`: 633 OK 7.813s. NON-VACUITY: with the fault-branch
marker removed in place, the reviewer's case fails -- the ending refuses
`precondition` instead of settling. Revert and restore in one act, verified by
re-hashing.

**HASHES:** `test_delayed_launch_release.py` sha256
`9449c56f0308626fee08dd79b2ed78277e94b6aedec516df1ebc74a2de4a1a20`;
`attempts.py` sha256 `7f4aa5489177fb10237953a3a51e0775edb389855685fc69375faf3c8dfadd56`;
`intake.py` sha256 `9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2` UNCHANGED
this claim.
