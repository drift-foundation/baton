# W266337 implementer progress

## Claim 269137 — stage 3 proved on the real round machinery; NO product change

ONE bounded command, five cases, 0.092s. `attempts.py` and `intake.py` are
UNCHANGED at stage 2's accepted hashes: the failed-Job-to-fresh-attempt path
needed no fix, and that is the finding.

### The schedule, through supported interfaces

1. **The failure.** Round 1 runs the real writer/checkpoint/reviewer sequence --
   `review_driver.prepare_implementation`, `freeze_checkpoint`,
   `prepare_review`, `record_verdict` -- and the verdict is
   `changes-requested`: a Job round that was REVIEWED AND SENT BACK, which is a
   decided failure rather than an abandoned offer.
2. **The settlement.** `episodes.advance_correction` is the supported interface.
   Both episodes end with the correction's own ending
   (`superseded-by-correction`), and both successors open at episode 2 with
   offer and attempt identities that differ from the failed round's.
3. **The fresh attempt.** Round 2 runs on those fresh identities, based on the
   failed round's checkpoint, to an `accepted` verdict and its own checkpoint.
4. **Attribution.** The accepted verdict names round 2's checkpoint, not round
   1's; every writer, attachment and verdict identity differs; and each round
   keeps its OWN frozen result, read through `frozen_output_of` -- round 1's is
   still readable and unchanged after round 2 exists.
5. **The settlement is one act.** Asking twice returns the same answer and opens
   no third episode. And a correction is not available on demand: asking with the
   ACCEPTED round's verdict is refused `refused/precondition` with "only
   'changes-requested' asks for another round", so a fresh attempt is never a way
   around a review.

### What is real, and what is controlled

REAL: `JobStore` and `ControlStore` on a disposable temporary root, a real
development line, the real driver entries above, the real
`episodes.advance_correction`, and the real Job-store and output readers.
CONTROLLED AND DETERMINISTIC: the accepted `DriverCase` fixture's `Profile`
provider and `Port` authority -- no model, no daemon, no network.

### What this does NOT prove, stated rather than left to inference

`DriverCase.attempt()` and `completed()` record attempt rows and worker outcomes
directly -- that fixture's own documented shortcut -- so NO runtime is started on
this path. Stage 1's reservation ordering and stage 2's release gate are therefore
NOT re-exercised here; they are preconditions this stage leaves intact. Nothing
here is a two-Job adoption claim, a preserved-run recovery, or evidence about a
real provider or daemon.

### Two things I caught in my own work

- **A VACUOUS CASE, found before delivery.** My first isolation case compared
  `receipts_of` before and after the correction. I probed it: that reader answers
  an EMPTY mapping for every episode in this fixture, so the assertion was
  `{} == {}` and proved nothing. It is replaced by one that reads content the
  fixture really writes -- each round's own frozen result -- and the module says
  why, because "it passed" was the wrong reason to keep it.
- **A shape I assumed instead of checking.** I first wrote `== []` against that
  same mapping reader. Corrected, and the case now asserts emptiness without
  presuming the container.
- **A refusal asserted only by type.** The last case accepted any
  `ContractRefusal`; it now asserts `refused/precondition` and the exact sentence,
  because a case that accepts any refusal would pass on an unrelated
  precondition.

### Verification

    cd /home/sl/src/baton/v12/python
    mkdir -p /var/tmp/baton-w266337
    BATON_V12_DISK_ROOT=/var/tmp/baton-w266337 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-fresh-attempt-recovery \
    timeout --signal=TERM --kill-after=5s 300s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_fresh_attempt_after_failure

5 cases OK, 0.092s. SELECTOR: this module only; its `load_tests` collects just the
cases defined here, so `DriverCase`'s own accepted cases are neither re-run nor
counted as this stage's evidence. NO accepted suite was run beyond it, and the
reason is that NO product file changed -- there is no owner to re-check. The
`BATON_V12_DISK_ROOT` directory must exist; the fixture refuses a root it cannot
write, which is how I learned to create it.

Earlier in the claim: five red or diagnostic runs (0.002s fixture-root refusal,
0.084s with the shape mismatch, 0.014s and 0.021s in-memory probes, 0.084s) and
the green 0.092s/0.094s. All listed; none rerun to improve a number.

### Hashes

- `test_fresh_attempt_after_failure.py` sha256
  `288b66eb25b82a5aa64b6b65bf7af5bf67a48d371d2382dbd6d350b7d2b080c0`
- `attempts.py` sha256
  `7f4aa5489177fb10237953a3a51e0775edb389855685fc69375faf3c8dfadd56` UNCHANGED
- `intake.py` sha256
  `9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2` UNCHANGED

## Claim 269211 — the composed run-level schedule, which the first delivery lacked

Review 2026-09-25T21-28-53Z is right: `DriverCase` INSERTS completed attempts and
frozen outputs, so my five cases prove the Job layer's correction bookkeeping and
NOT an actual failed run, its settlement, or a fresh successful run. Those cases
are preserved as supplementary evidence and a new class supplies the missing half.

**EXACT ADDITIONAL EDIT PATHS, as required:** only
`work/records/2026/09/finding-v12-fresh-attempt-recovery/test_fresh_attempt_after_failure.py`
and this PROGRESS.md. NO product file was edited this claim -- `attempts.py` and
`intake.py` remain at stage 2's accepted hashes.

**THE COMPOSED SCHEDULE, every step a supported call and nothing inserted:**

1. `request_runtime_start` for the first attempt -- the real reservation from
   stage 1 -- which attaches its own runtime and occupies the lane.
2. The successor's `request_runtime_start` is REFUSED by the real lane interlock
   while the failed run still holds it, and its adapter records no submission.
   That is stage 2's property, reused here rather than restated.
3. `abandon_attempt` -- the supported settlement -- ends the failed run: it
   removes THAT runtime by name, answers `retained`/`absent`, moves the axis to
   `destroyed` and releases the lane.
4. `request_runtime_start` for the fresh attempt, which attaches ITS OWN runtime.
5. `reconcile_runtime` records a positive quiescent observation, and the worker
   outcome is recorded through the manager's own axis recorder.
6. EFFECTS ATTRIBUTION: the fresh run owns `runtime-fresh` with a `completed`
   disposition and holds the reservation; the failed run still shows
   `runtime-failed`, `retained` cleanup and a `none` disposition, so it stays
   auditable and nothing of it was reused.

**A BOUNDARY I MEASURED AND COULD NOT USE, reported rather than worked around.**
`output.request_freeze` is the supported result-acceptance entry, and I drove the
composed schedule all the way into it. It refuses on this fixture with "a sealed
result assignment reference names Work '0000000a-W1', which does not carry the
prefix of authority '0000000000000000000000000000000a'": the fixture's Work and
authority identities cannot satisfy the freeze's own prefix rule. Reaching it
would mean a different identity set, which is a fixture change this stage does not
need -- so RESULT attribution stays proved at the Job layer by the preserved
class, and the composed class proves EFFECTS attribution. Both halves are labelled
in the module so neither is read as the other.

**WHAT IS STILL SIMULATED:** the engine is the accepted fake adapter and the
authority is the fixture's deterministic session. No fake attests that a real
container ran or stopped, and unknown-outcome holds are preserved exactly as
stage 2 left them.

**RESULTS:** 6 cases OK, 0.101s, one command, same selector plus the new class in
the same module. Earlier in the claim: four in-memory probes into the freeze
boundary (0.007s, 0.008s, 0.008s, 0.007s), each recorded above for what it taught.

**HASHES:** `test_fresh_attempt_after_failure.py` sha256
`becc2e070433a38be57ec4b8bebc2c82e14da1d814447a99e8075f83a6edfb4c`;
`attempts.py` sha256 `7f4aa5489177fb10237953a3a51e0775edb389855685fc69375faf3c8dfadd56` UNCHANGED;
`intake.py` sha256 `9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2` UNCHANGED.

## Claim 269262 — the composed schedule now ends in a REAL accepted output

Review 2026-09-25T21-36-31Z: the composed case still set `worker_disposition`
through `observe` and never accepted generated output. It now runs to
`output.request_freeze` over bytes that are on disk. 6 cases OK, 0.113s, clean
under `-W error::ResourceWarning`.

**EXACT ADDED EDIT PATHS:** only
`work/records/2026/09/finding-v12-fresh-attempt-recovery/test_fresh_attempt_after_failure.py`
and this PROGRESS.md. NO product file was edited -- `attempts.py`, `intake.py` and
`output.py` are unchanged.

**THE SCHEDULE NOW ENDS IN ACCEPTANCE.** After the failed run is settled and the
fresh run reaches a positive quiescent observation, this module writes the bytes a
worker would have produced into that attempt's own workspace, and the controlled
sealing adapter DERIVES its manifest by reading them -- entry path, byte count and
content digest all computed from the file, so what the manager accepts describes
what is on disk rather than numbers a fixture asserted. `request_freeze` then
accepts it: the attempt's `output` axis reaches `frozen` and `frozen_output_of`
answers a result named for the fresh attempt, while the failed attempt has NO
result at all and keeps its own auditable record.

**NO IDENTITY CORRECTION WAS NEEDED, AND I BUILT ONE FIRST.** The freeze reaches
§4's rule that a Work id carries its authority's 8-character prefix, and
`tests.manager.test_offers`' pair (`0*31+"a"` with `0000000a-W1`) does not satisfy
it -- so I wrote a fixture correction that rewrote the Work id and the session's
answers. Then I read further: `delivered()` builds its assignment from
`VALID_WORK` = `43c55d4b...` with `43c55d4b-W1439`, which DOES satisfy it. The fix
was to use the delivered path; the correction apparatus was removed and the
validator was never touched. The observation about the `claimed()` pair stands as
a finding, not as something this stage had to repair.

**THREE PIECES OF FIXTURE SETUP, each labelled in the module as setup rather than
evidence.** `delivered_as` mirrors the accepted `delivered()` with the offer id
parameterised, because that helper hard-codes `offer-1` and a second call collides
at §4.2. The deterministic session's FENCE ANSWER is pointed at the assignment this
schedule holds, because the accepted session builds it from the other fixture's
identities and the port correctly refuses a fence naming another authority's
assignment. And the input manifest is RETAINED through `manifests.retain_manifest`,
because the freeze compares declared outputs against it and `delivered()` composes
the root without retaining -- its own cases never reach that comparison.

**WHICH SUCCESS IS PROVED WHERE.** At this layer the applicable success is the
attempt's own: a positive quiescent observation, a recorded completion and an
ACCEPTED frozen result with attributed bytes. The Job-layer success -- an accepted
verdict closing a corrected round -- stays proved by the preserved class above. The
module says which is which so neither is read as the other.

**STILL SIMULATED:** the fake adapter, the deterministic session, and the worker's
output bytes written by this module as a stand-in for a worker. No fake attests
that a real container ran, stopped, or produced anything.

**HASHES:** `test_fresh_attempt_after_failure.py` sha256
`08b4789251309af73d0c76fd26a147c54a6387f8c60c7430ebea3ae62db3485d`;
`attempts.py` `7f4aa5489177fb10237953a3a51e0775edb389855685fc69375faf3c8dfadd56`,
`intake.py` `9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2` and
`output.py` `434182ab922729aaa3af5d53b0539a0fa8d6b5d34b4cad5b3a7454da594c2e1d` all UNCHANGED.

**VERIFICATION:** 6 OK 0.113s. Earlier in the claim, seven in-memory probes and
five red runs walked the freeze's preconditions in order -- the sealed-schema type,
the Work/authority prefix, the claim answer's Work, the absent input digest, the
schema's requirement of that digest, the fence answer's authority, and the retained
declaration -- each listed here for what it taught rather than hidden.

## Claim 269338 — the fenced generation is really ended, and recovery is real

Review 2026-09-25T21-48-53Z found a real proof defect: both attempts bound
generation 1, and the accepted session's `cancel` reports an assignment fenced
while still answering it as LIVE. So my fresh run was executing on the very
generation the abandonment had just fenced. Their immutable
`review_fenced_generation_20260925.py` (verified sha256 `d159fc9a…`, never edited)
showed that ending it for real turns my case into `stale-assignment`/`ended` with
no frozen output. The product was right; my fixture was not.

**EXACT ADDED EDIT PATHS:** only this dossier's
`test_fresh_attempt_after_failure.py` and PROGRESS.md. No product file edited --
`attempts.py`, `intake.py` and `output.py` unchanged.

**THE CORRECTED SCHEDULE.** The failed run holds the lane and blocks a successor;
`abandon_attempt` settles it; the authority's live assignment is then ENDED for
real (`live_assignment = None`), and the fresh live generation is obtained the way
a recovery does -- the authority answers a NEW assignment at generation 2, and the
fresh attempt is delivered, claimed and activated against THAT. `delivered_as` now
carries the generation (and sets the session's Work record, which it needed for
standalone use). The fresh run then starts, reaches a positive quiescent
observation, records its completion, and its output is ACCEPTED.

**ARTIFACT BYTES READ FROM THE STORE, not from my helper.** The accepted result's
artifact row is read back through `frozen_output_of` and its `bytes` and
`content_digest` are compared against the real file's -- and, separately, against
the helper's values, so the two agree rather than the helper being the only
witness. That was the review's exact distinction.

**OLD-GENERATION REJECTION, in its own case.** The recovered attempt completes on
the live generation and then its sealed result declares the SUPERSEDED one: same
bytes, stale assignment reference. The acceptance boundary refuses
`stale-assignment`, and nothing is published. Two things I measured rather than
guessed there: the category is `stale-assignment` (I had written `integrity`), and
the refusal leaves the axis at `freeze-requested` (I had written `open`) because
the freeze REQUEST is journalled before the sealed result is validated -- the
attempt is left asking, not published.

**AND THE IMMUTABLE PROBE NOW FAILS BY CONSTRUCTION, which I am reporting rather
than editing.** `review_fenced_generation_20260925.FenceProbe` wraps my case in
`assertRaises(ContractRefusal)`: it asserts the PRE-correction behaviour, that my
schedule refuses once the generation is ended. The correction the same review
required is that my schedule now ends that generation ITSELF and then recovers a
fresh one, so it completes successfully and raises nothing -- the probe reports
"ContractRefusal not raised". Its finding is fully incorporated; the probe as
written cannot hold against the corrected behaviour and needs superseding by its
owner. I did not touch it.

**RESULTS:** 7 cases OK, 0.130s, clean under `-W error::ResourceWarning`. The
immutable probe: 1 failure, 0.029s, for the reason above.

**HASHES:** `test_fresh_attempt_after_failure.py` sha256
`93a4d8bd0c7ed08ec3ff3a745f31c5dd52e807c2a7895db9de9a2c9e1d5a4c90`;
`output.py` sha256
`434182ab922729aaa3af5d53b0539a0fa8d6b5d34b4cad5b3a7454da594c2e1d` UNCHANGED, as
are `attempts.py` and `intake.py` at stage 2's accepted hashes.

## 2026-09-25T22:00Z — claim 269404: the gate the fence installed is now settled

**WHAT THE REVIEW FOUND AND I FIXED.** Review `review-2026-09-25T21-56-23Z.md`
probed my previous schedule: after it "succeeded",
`intake.abandoned_gate_discharge_of(store, ATTEMPT)` answered `None`. The
abandonment fenced the generation and removed the runtime, and NOTHING carried
its absence proof to the `runtime-quiescence:1` gate that fence installed. My
`delivered_as` then wrote the Work projection back to queued/gate=None, which
ERASED the gate instead of settling it — "setting the projection is not proof the
gate was settled". No product defect; the fixture was faking the authority's
release.

**THE FAKE AUTHORITY NOW FENCES THE WAY A REAL ONE FENCES.** `fences_faithfully`
models `authority/core.py:_end_assignment` in one act: the assignment ends
(`live_assignment = None`), the Work moves to `block`, and
`runtime-quiescence:<generation>` is installed. The fence answer is DERIVED from
the cancellation's own `expect`, which also retires the hand-patched
`fence_answer` hack the previous candidate carried. Labelled as fixture setup: a
fake cannot attest that a real authority fenced anything.

**AND THE PROJECTION IS NOW MOVED BY EXACTLY TWO THINGS.** The fence installs the
gate; the accepted `FakeSession.satisfy_gate` clears it. `delivered_as` carries
`status`, `phase`, `handler` and `gate` over rather than writing them — it only
says WHICH Work the projection is about (the authority, scope and route of
`VALID_WORK`, which the accepted session is not constructed around). So a held
gate now survives that helper, and a successor can only be delivered into a Work
the authority really released.

**ONE THING I MEASURED RATHER THAN ASSUMED, from a red run.** The accepted
session's `discharge_answer` carries the GATE's kind (`runtime-quiescence`), and
the real authority answers the kind of the EVIDENCE it accepted
(`authority/core.py:1746`). The act refused: "the authority answered evidence kind
'runtime-quiescence' for attempt 'attempt-1' and this act requires
'runtime-absent'" — the product holding a fake to the authority's own contract.
The wrapper now answers `operands["evidence"]["kind"]` and leaves the accepted
token-equality and replay rules doing their own work.

**THE NEW EVIDENCE, two cases.**

`test_the_abandonment_discharges_the_gate_it_installed` — the reader the review
probed is asserted `None` BEFORE the act, then the real
`discharge_abandoned_quiescence_gate` runs and its committed receipt is measured
whole: the attempt, `runtime-quiescence:1`, generation 1, the Work reference,
`runtime-failed`, the `runtime-absent` evidence naming that exact runtime, and the
retention policy. It is cross-bound to the abandonment: the receipt's
`cleanup_operation` equals `abandonment_cleanup_of`'s committed operation AND the
operation the abandonment itself answered, so the discharge is earned behind THIS
removal rather than any removal. The authority's journalled answer says `queued`,
the projection really moves to queued/gate=None, the absence evidence is in the
authority's gate journal exactly once, `abandoned_gate_discharge_of` now answers
the same receipt, and asking a second time replays it without asking the authority
again (§4.2).

`test_no_successor_is_admitted_before_the_gate_is_discharged` — the negative, at
the PRODUCT's own admission boundary rather than at a fixture's. While the gate
holds, `issue_offer` refuses `refused/precondition`: "an offer is issued only
against open, queued, unclaimed, ungated Work", naming `runtime-quiescence:1`, and
no attempt row exists for the successor. The same delivery, after the supported
discharge, is admitted at generation 2 — so what refused was the gate and not the
delivery.

The composed schedule now reads fail → settle → DISCHARGE → fresh run → accepted
output, with the generation-2 and stored-artifact assertions the review confirmed
preserved unchanged.

**WHAT I COULD NOT COMPOSE, AND EXACTLY WHY — measured, not assumed.** The review
also carried forward "compose the applicable Job recovery/success path with this
identity chain". The consumer of this receipt is
`review_cycles._abandoned_evidence`, reached through
`restore_abandoned_correction`. I probed it on this chain (probe kept in
`/tmp/probe_restore_applicability.py`, not in the dossier, because it measures
applicability rather than proving a stage): a real line created with THIS chain's
authority and Work, and a real writer granted to the abandoned attempt, both
succeed. The recovery then refuses, twice and for its own reasons:

- with no writer: "was granted no line writer at that generation; there is no
  correction here to restore";
- with a first writer: "its writer is based on no checkpoint; this recovery
  restores a CORRECTION to the checkpoint it was based on, and a first writer has
  none to return to".

So that recovery is applicable only to a correction — a writer based on a frozen
checkpoint. Composing it here means a COMPLETED PRIOR ROUND on the same line
before the failed generation exists: a first writer that runs and freezes a
checkpoint (whose `freeze_checkpoint` fences that generation and installs its own
quiescence gate, which then needs the ORDINARY cleanup-and-discharge chain before
the next generation can be claimed at all), a review attachment and a
changes-requested verdict, and only then the abandoned correction writer. That is
a multi-round lifecycle composition, not a minimal demonstrated fix, and the
review side would still be fixture-inserted rows. I am reporting it for deliberate
selection instead of improvising it.

**RESULTS:** 9 cases OK, 0.168s, clean under `-W error::ResourceWarning`. Reds and
probes this claim: one red run at 0.152s (3 errors, the evidence-kind mismatch
above), and the applicability probe, 2 cases OK in 0.038s. Nothing rerun to
improve a number. No accepted suite beyond this module, because no product file
changed. The historical `FenceProbe` was not run: the current review records that
its candidate-specific expected refusal is superseded and is not a current
acceptance gate.

**HASHES:** `test_fresh_attempt_after_failure.py` sha256
`39c7d102fb80371a558c0ca3f06cfbacbc5f98895a24366a23b3c54b5cbe423b` (was
`93a4d8bd0c7ed08ec3ff3a745f31c5dd52e807c2a7895db9de9a2c9e1d5a4c90`). UNCHANGED:
`attempts.py` `7f4aa5489177fb10237953a3a51e0775edb389855685fc69375faf3c8dfadd56`,
`intake.py` `9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2`,
`output.py` `434182ab922729aaa3af5d53b0539a0fa8d6b5d34b4cad5b3a7454da594c2e1d`,
`custody.py` `3e977dfb0e12f58f05d85e5fc1e4dbe96b3e356db19dc60f9fe326e463c19022`,
`workspaces.py` `dafd976790d3a081ee5f96bdf28ec363334bcdd888504e2fa5c1c06a9d21b779`,
`review_cycles.py`
`938bc0c6785ee8de51b85cf66406a1777a752f5cafdcee933de5ee0f090c59b4`, `offers.py`
`57a7bfe86b13951a2612b0e1f1e1ad9b139dfe38013a103b2b116b15a9494065`, and the
reviewer's probe `d159fc9a20258584f1961385a74d8c09726238e53addb82b023f92797eeb63e4`.
No product file edited, no validator weakened, no accepted test edited, no
reviewer-owned file touched.

**THE ONE BOUNDED COMMAND, unchanged:**

    cd /home/sl/src/baton/v12/python
    mkdir -p /var/tmp/baton-w266337
    BATON_V12_DISK_ROOT=/var/tmp/baton-w266337 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-fresh-attempt-recovery \
    timeout --signal=TERM --kill-after=5s 300s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_fresh_attempt_after_failure

## 2026-09-25T22:20Z — claim 269531: the gated Job recovers on one identity chain

**WHAT THE REVIEW ASKED AND WHAT THIS DELIVERS.** Review
`review-2026-09-25T22-18-41Z.md` accepted the gate-discharge correction and
enumerated a four-step Job composition, with the clarification that the prior
completed round MAY be explicit fixture setup and that no full prior-round runtime
replay is required. All four steps are now one case,
`AGatedJobRecoversAndItsSuccessorSucceeds.test_the_gated_job_recovers_and_its_successor_is_accepted`,
plus a negatives case. 11 cases OK, 0.246s, one bounded command. NO PRODUCT
CHANGE.

**THE SCHEDULE, every step a supported operation on real durable records.**

1. *Prior history, labelled setup.* One Job whose implementation and review stages
   name the SAME Work (which is what a line can attach at all), a real development
   line on THIS chain's authority and Work, and round 1 composed with the accepted
   driver fixture's own shortcuts: an inserted writer attempt row, its worker
   completion, `prepare_implementation`, a real `freeze_checkpoint`, an inserted
   reviewer attempt with a frozen output, `prepare_review`, and a real
   `record_verdict` of `changes-requested`. Then the Job's own real
   `advance_correction`, which is what SELECTS that checkpoint -- the replacement
   refuses a recovery from a checkpoint the Job's handoff never chose.
2. *The tested failure, bound to that episode.* The correction episode's attempt id
   is the one the Job MINTED, and it is delivered through the real offer, claim and
   activation path at generation 2, granted the line's correction writer based on
   the retained checkpoint, and really started: the lane is held, the adapter
   submits once. Then the real `abandon_attempt` -- retained/absent cleanup, the
   lane released, the generation fenced and the Work held at
   `runtime-quiescence:2`.
3. *Both supported recoveries, in the order their receipts require.* The real
   `discharge_abandoned_quiescence_gate`, then `restore_abandoned_correction`
   (measured: the line back to `correction-ready` at the SAME checkpoint, the old
   writer `revoked`, and the profile's restoration called over this line's own path
   with that checkpoint's own evidence), then
   `episodes.restart_abandoned_correction` (measured: the episode ends
   `abandoned-after-exclusion`, the receipt names the attempt, the episode, the
   line, the checkpoint and the restoration's own operation id, and NOTHING is
   opened by it). Then the ORDINARY `sweep` opens exactly one successor, at the
   next episode, with an attempt identity it derives itself.
4. *Ordinary successor admission and the applicable Job success.* The successor is
   delivered at generation 3 through the offer boundary the gate had been blocking,
   granted the line's writer from the restored checkpoint, and only then run to a
   positive quiescent observation and a recorded completion. The Job takes on the
   ending BEFORE any step that can reach cleanup (`register_ending`, which is that
   record's own contract), the output is accepted through the real
   `output.request_freeze` over bytes really on disk, custody is taken through the
   real `request_intake` with a collection DERIVED from the frozen artifacts, and
   `settle_ending` records it. The Job's own settlement then reads back the
   successor's result id, the manifest this manager froze, the intake receipt
   digest and generation 3.

**AND NOTHING IS CREDITED TO THE FAILED EPISODE.** The stage's history is exactly
`[superseded-by-correction, abandoned-after-exclusion, None]`, the middle one
naming the abandoned attempt; that attempt has NO frozen output, keeps its
`retained` cleanup and its `none` disposition, and the Job holds neither an ending
intent nor a settlement for its episode.

**THE NEGATIVES, in the order the receipts are earned.**
`restart_abandoned_correction` before any restoration refuses
`refused/precondition` -- "has no completed abandoned-correction recovery";
`restore_abandoned_correction` while the gate is held refuses "has not discharged
its runtime-quiescence gate". Measured in the same case: the episode is still live
on the abandoned attempt, the line is still `writing` and its writer still
`active` -- nothing was half-recovered. Then the recoveries in order answer.

**I PROVED THE NEW ASSERTIONS BITE RATHER THAN ASSUMING IT.** Two mutation probes
on copies of the module: expecting a foreign result id in the Job's settlement
fails with the real minted value (`result-attempt-df8b810c...`), and expecting a
foreign ending fails with `abandoned-after-exclusion`. Both copies were deleted;
the module is unchanged by them. I did this because a long composed case that
passes on the first run is exactly the kind of case that can be passing for the
wrong reason.

**ONE ENVIRONMENTAL BOUNDARY, measured.** The line boundaries refuse a workspace on
a memory filesystem -- "checkout, build-cache, test-artifacts, output, logs do not
rely on scratch" -- and the accepted runtime fixture configures its storage under
the system temporary directory, a tmpfs on this host. Reconfiguring afterwards is
correctly refused ("a changed store is a fresh store rather than a
reconfiguration"), so the composed class spells out the accepted fixture's own
setUp sequence with the DISK-BACKED root chosen first, through the accepted
`tests.manager.disk_roots` helper the line suites already use. No product change
and no fixture weakened; the reason is recorded in the class.

**WHAT IS PRIOR HISTORY AND WHAT IS NOT, stated in the module and again here.**
Fixture setup: round 1's writer and reviewer attempt rows, their worker outcomes,
that reviewer's frozen output, and the prior round's own fences (through the
accepted driver's port fake, deliberately NOT the tested authority projection, so
the history cannot move the state the recovery is measured against). NOT faked: the
failed attempt, its runtime, its lane, its abandonment, its cleanup, its gate
discharge, both recovery receipts, the successor's admission, its run, its accepted
result and the Job's observation of it.

**WHAT I DID NOT DRIVE, named rather than implied.** `review_driver.end_implementation`
is the fuller nine-step composed ending; it also publishes, fences the assignment
and freezes the next checkpoint, which is the following round's business rather
than this recovery's. What this case drives instead is the Job's own two ending
records with the real intake receipt inside them, which is where the Job observes
the result. The ordinary replacement is driven through `sweep` with the accepted
`FakeOperations` seam, as the accepted recovery suite drives it.

**RESULTS:** 11 cases OK, 0.246s, clean under `-W error::ResourceWarning`. Reds and
probes this claim: one red at 0.181s (two errors -- the tmpfs workspace refusal
above), one green at 0.645s before the successor's admission order was corrected to
deliver-then-grant-then-run, one at 0.248s after it, and the two mutation probes at
0.246s and 0.229s. Nothing rerun to improve a number. No accepted suite beyond this
module, because no product file changed.

**HASHES:** `test_fresh_attempt_after_failure.py` sha256
`0392e8e100c1b5809187ea3730d7d1845529e33dec1691eb284893ea5fdb476b` (was
`39c7d102fb80371a558c0ca3f06cfbacbc5f98895a24366a23b3c54b5cbe423b`). UNCHANGED, at
the values the last review verified where it recorded them:
`attempts.py 7f4aa5489177fb10237953a3a51e0775edb389855685fc69375faf3c8dfadd56`,
`intake.py 9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2`,
`output.py 434182ab922729aaa3af5d53b0539a0fa8d6b5d34b4cad5b3a7454da594c2e1d`,
`review_cycles.py 938bc0c6785ee8de51b85cf66406a1777a752f5cafdcee933de5ee0f090c59b4`,
`job_manager/episodes.py
32e46805540fb7aa4558a735d6d8a714e03c4b7c0e85c8695f929ca596077865`,
`job_manager/ending.py
3d9c4f1914806e2b38543642c483d74628da9e1cbd36a24fa4cc04bf75ea2b99`. No product file
edited, no validator weakened, no accepted test edited, no reviewer-owned file
touched. EXACT EDIT PATHS this claim: only this dossier's
`test_fresh_attempt_after_failure.py` and `PROGRESS.md`.

**THE ONE BOUNDED COMMAND, unchanged:**

    cd /home/sl/src/baton/v12/python
    mkdir -p /var/tmp/baton-w266337
    BATON_V12_DISK_ROOT=/var/tmp/baton-w266337 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-fresh-attempt-recovery \
    timeout --signal=TERM --kill-after=5s 300s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_fresh_attempt_after_failure

## 2026-09-26 — the successor's ending is now PERFORMED, not declared

**THE DEFECT WAS MINE AND THE REVIEW WAS RIGHT.** My previous candidate froze the
successor's output, took custody of it, and then called `ending.settle_ending`.
That journal operation records the caller's assertion that a composed ending
finished; it executes and certifies none of it, and its own contract at
`job_manager/ending.py:562` says so -- "the driver's evidence, W119548's gate
discharge where the recorded fence owes one, and whatever routing the answer
earned are each somebody else's journalled act". I had bypassed its documented
caller precondition, so the settlement was invalid completion evidence. No
product defect: the API did exactly what it says it does.

**AND MY OWN PREVIOUS PROGRESS NOTE IS SUPERSEDED BY THIS.** The section above
says the checkpoint and fence are "the following round's business rather than
this recovery's". That is wrong for the selected implementation ending:
`review_driver.end_implementation` IS this attempt's ending, and its checkpoint
freeze, its fence and its cleanup are steps eight and nine of it. I am striking
that claim rather than leaving two accounts in one record.

**WHAT THE SCHEDULE NOW DOES, in the order the ending requires.** After the
successor really runs, the worker's bytes are on disk and its completion envelope
is readable, `register_ending` takes on the obligation BEFORE any step that can
reach cleanup, and then:

    end_implementation        the real ten-step ending
    route_fenced              the handoff, while the gate still holds
    discharge_quiescence_gate the gate that ending's own fence installed
    settle_ending             and only now: the obligation is closed

**THE ENDING'S OWN ORDER, MEASURED from the engine double's record** rather than
from the module's prose: `['stop', 'consume', 'seal', 'collect', 'retain',
'destroy']` -- step one's quiescence, W105982's line-readable proof, the freeze,
the intake, the retention decision, and the cleanup LAST, after the checkpoint
fence. The publication was asked while the line was still `writing`, which is the
whole of step seven's position: a publication after the fence refuses.

**THE ACTS THE SHORTCUT LEFT OUTSTANDING ARE NOW DONE, each asserted as a fact
about the records.** Cleanup `retained` and runtime `destroyed`, with the destroy
naming `runtime-successor`; the lane empty; the successor's writer `revoked`; the
line at THIS attempt's new checkpoint rather than the restored one, and that
checkpoint's writer is the successor's own; generation 3 really ended at the
authority and the Work held at `runtime-quiescence:3`.

**THE ROUTING COMES BEFORE THE DISCHARGE**, which is W122060's ordering:
discharging first returns the Work to `queued` on the route the FINISHED role is
served on, so the participant that just ended could reclaim it before the next
role is offered anything. The handoff's operands are read off committed records
the way the accepted composition reads them -- the fence operation off this
ending's own checkpoint, `from_route` off the one committed claimed offer -- and
the answer is asserted to leave the Work at `block` with the gate untouched.

**THEN THE GATE, THROUGH THE SUPPORTED MANAGER ACT.** `discharge_quiescence_gate`
is the same obligation stage 2's abandonment owed, now owed by a SUCCESSFUL
ending. Its receipt names gate `runtime-quiescence:3`, runtime
`runtime-successor` and evidence kind `runtime-absent`; its
`cleanup_operation_id` equals the `runtime.destroy` operation `authorize_cleanup`
committed, so it is earned behind THIS ending's cleanup and not any cleanup; the
authority's gate journal receives the absence evidence exactly once; the
projection really moves to `queued`/gate `None`; and asking again replays.

**AND ONLY THEN THE SETTLEMENT**, every member read back out of a committed
record: the frozen result, the manifest the manager validated, the intake
receipt, this attempt's new checkpoint and the gate the discharge cleared.
`pending_endings` holds this obligation from registration until settlement and is
empty after it -- the same reader the review's probe found empty while the acts
were outstanding, now empty truthfully.

**TWO THINGS I MEASURED RATHER THAN ASSUMED, both from red runs.** First, the
output axis rests at `sealed` and not `frozen` after a complete ending, because
the intake moves it on (`intake.py:801`); `frozen` is where the runtime class's
bare freeze stops. Second, the ordinary discharge receipt carries the authority's
answered `kind` and no `evidence` member -- that member belongs to the ABANDONED
variant -- so the positive absence is asserted in the authority's own gate
journal instead. The stop also had to move the engine's observation: `reconcile_
runtime` refused "execution_runtime is 'quiescent'; 'running' does not follow it"
until it did, because a double answering `quiescent` to a stop and `running` to
the observation right after would be two engines.

**THE CORRELATION IS NOW MEASURED, which it was not.** The review asked for a
measured output identity at the terminal correlation, and my terminal digest and
my sealed result's `completion_manifest_digest` were the SAME fixture constant --
so `_correlated` was comparing a constant with itself. The sealed result now
derives that digest from the outputs it describes, which are derived from the
bytes on disk, and the worker's claimed terminal carries that derived value. One
new case proves the comparison bites: the same run, the same bytes, a terminal
naming a different envelope, and the ending refuses
`refused/operation-collision` naming both digests -- with the result sealed and
NOTHING after step four performed: no custody, no retention, no publication, no
checkpoint, no cleanup, the lane still held and the writer still active.

**I PROVED THE NEW ASSERTIONS BITE.** Two mutation probes on copies under /tmp,
both deleted afterwards and neither added to the dossier. Replacing the real
discharge with a hand-written receipt fails on the cleanup cross-binding (`None
!= 'runtime.destroy:24c89ea0...'`). Reverting the ending to the superseded
freeze-and-intake shortcut fails on the measured order (`['seal', 'collect'] !=
['stop', 'consume', 'seal', 'collect', 'retain', 'destroy']`) -- so this case
cannot pass the way the previous one did.

**THE REVIEWER'S PROBE NO LONGER PASSES, and the review authorized exactly that**
("preserve immutable historical probes rather than requiring corrected candidate
to retain fault"). It is preserved BYTE-IDENTICAL at sha256
`71b384ae4aa421c96111101505d2fd4a3c86b02e1504cc845332eca20ffbcfe0`. It stops at
its first faulty-state assertion: `'review-ready' != 'writing'`. Every other
particular it asserted is inverted too, measured through a throwaway author probe
at `/tmp/probe_corrected_ending_state.py` (deliberately NOT added to the dossier;
it proves no stage): line at the new checkpoint rather than the old one, cleanup
`retained` not `pending`, runtime `destroyed` not `quiescent`, lane `[]` not
`[fresh]`, live assignment `None` rather than generation 3 still assigned,
projection `queued`/`None` rather than gated, and `pending_endings` `[]` -- now
because the ending is finished.

**NEW FIXTURE SEAMS, AND WHAT EACH ONE DOES NOT MODEL.** `ending_surface` is one
adapter carrying the whole surface `_typed` proves before the first stop; its
`seal` and `collect` still answer what is really on disk and what the freeze
really recorded. `publishing` is the publication seam's shape, recording the line
state it was asked at; it publishes nothing anywhere and is not
`integration.driver.retain_proposal`. `routes_fenced` models `route_fenced`'s
observable rules -- change only the route, refuse unless the Work is at `block`
holding this generation's gate on the original claim's route, replay by operation
identity -- and it does NOT model the real act's journal provenance checks on the
committed cancellation record or the single original claim decision, because this
session keeps no such journal. Nothing here is evidence that a real authority
would admit this handoff.

**ONE READER I DELIBERATELY DO NOT ASSERT THROUGH, and why.**
`projection.stage_states` is the Job's status view and `_ending_owed` is the
settlement's consumer -- but it derives every observation through a canonical
OPERATIONS surface, and the only one available here is `FakeOperations`, whose
observations are values a case SETS rather than reads. Asserting a stage
`completed` through it would be asserting what this module had just written into
a fake. The Job-side completion is therefore measured through `pending_endings`
and `ending_of`, which read this store's own stage and episode rows.

**RESULTS:** 12 cases OK, 0.303s, clean under `-W error::ResourceWarning`. The
reviewer's combined selector: 13 ran, 12 OK and the preserved probe failing as
above, 0.361s. Reds and probes this claim: 0.253s (the reconcile refusal above),
0.258s and 0.255s (the order filter -- `IMPLEMENTATION_ENDING` names the driver's
STEPS, not the adapter's verbs, which I had assumed), 0.255s (`sealed` vs
`frozen`), 0.255s (the discharge receipt's shape), 0.304s twice (the elided digest
and the `pending` cleanup word), the two mutation probes at 0.057s and 0.050s, and
the state probe at 0.062s. Nothing rerun to improve a number. No accepted suite
beyond this module, because no product file changed.

**HASHES:** `test_fresh_attempt_after_failure.py` sha256
`164a06add6163a99b89f1389f40d85be941320404ae5f5dead7f0385c0d31d18` (was
`0392e8e100c1b5809187ea3730d7d1845529e33dec1691eb284893ea5fdb476b`). UNCHANGED:
`attempts.py 7f4aa5489177fb10237953a3a51e0775edb389855685fc69375faf3c8dfadd56`,
`intake.py 9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2`,
`output.py 434182ab922729aaa3af5d53b0539a0fa8d6b5d34b4cad5b3a7454da594c2e1d`,
`custody.py 3e977dfb0e12f58f05d85e5fc1e4dbe96b3e356db19dc60f9fe326e463c19022`,
`workspaces.py dafd976790d3a081ee5f96bdf28ec363334bcdd888504e2fa5c1c06a9d21b779`,
`review_cycles.py 938bc0c6785ee8de51b85cf66406a1777a752f5cafdcee933de5ee0f090c59b4`,
`offers.py 57a7bfe86b13951a2612b0e1f1e1ad9b139dfe38013a103b2b116b15a9494065`,
`job_manager/ending.py
3d9c4f1914806e2b38543642c483d74628da9e1cbd36a24fa4cc04bf75ea2b99`,
`job_manager/review_driver.py
9a8a4a8193ff7b1c709c184dee3ba43a1b1e16e60891dcf31277279d2c220ae4`,
`job_manager/episodes.py
32e46805540fb7aa4558a735d6d8a714e03c4b7c0e85c8695f929ca596077865`,
`job_manager/projection.py
595008b9ddb06d947c3720eb5bd8928a53b65f2e7458bbd151f4a77d52fc6742`. Both reviewer
probes and all six historical reviews are unchanged at the hashes recorded in the
latest review. No product file edited, no validator weakened, no accepted test
edited, no reviewer-owned file touched. EXACT EDIT PATHS this claim: only this
dossier's `test_fresh_attempt_after_failure.py` and `PROGRESS.md`.

**THE ONE BOUNDED COMMAND, unchanged:**

    cd /home/sl/src/baton/v12/python
    mkdir -p /var/tmp/baton-w266337
    BATON_V12_DISK_ROOT=/var/tmp/baton-w266337 PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-fresh-attempt-recovery \
    timeout --signal=TERM --kill-after=5s 300s \
      /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
      -m unittest test_fresh_attempt_after_failure

**WHAT REMAINS AND IS NOT CLAIMED:** no two-Job adoption, no preserved-run
recovery, no live provider or daemon evidence, deadline expiry still untested, the
`uncertain` runtime state's own resolution still held with no supported resolution
demonstrated, and W257624's final recovery packet with its unmet R3/R4/R5
requirements including the pending intake `_settle` control operand. Unknown-
outcome holds are untouched.
