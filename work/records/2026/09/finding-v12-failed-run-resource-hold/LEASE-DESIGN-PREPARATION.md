# Bounded lease-design preparation — owner 265058, corrected under owner 266005

PLAN ONLY, revision 4 (claim 266248). Nothing here is implemented, tested or executed.
Every factual line is a source reading taken in claim 266009, 266130 or 266248; everything else is
a labelled proposal.

Governing ruling: FINDING.md "2026-09-25 — owner selects short transactions and fenced
workspace leases". Deciding sentences: no filesystem, engine, network or worker I/O while a
DB transaction is held; completion/release tied to the exact lease generation; expiry
triggers REVOCATION and does not free the workspace; every writer INCLUDING MANAGER-OWNED
ones must be stopped and confirmed before a replacement generation; uncertain termination
leaves the resource held; stale-generation results are not accepted; a token checked before
a filesystem write alone is not enforcement.

## 0. Superseded claims, preserved rather than erased

Revision 1, corrected in revision 2 (review 2026-09-25T10-58-36Z):

| revision 1 claim | the source | status |
| --- | --- | --- |
| "no durable REVOCATION state for a writer generation" | `review_cycles.py:1209` writes `state='revoked', revoked_at, revocation_reason='checkpoint'`; `:2489` the same with `'abandoned'` | **FALSE.** State, timestamp and cause all exist. |
| require the writer still `active` in freeze's final transaction | freeze revokes its own writer at `:1209` before the external fence | **WOULD BREAK NORMAL COMPLETION.** Withdrawn. |
| `writer_boundary` should refuse a revoked generation | `:2741` already does | **ALREADY PRESENT.** |
| reuse the custody overlap reader as the line's all-writer exclusion | `line_assignment_workspace:2850` — the line namespace is disjoint from every custody root | **WRONG RESOURCE.** |
| "`workspaces.py:1673` is THE ONE violation" | `grant_writer.act:1099` stats the filesystem under its transaction; `restore_abandoned_correction:2461` restores the checkout under its transaction | **FALSE, inside modules I claimed to have read.** |
| "thirteen cases" | eleven were listed | **COUNT WRONG.** |

Revision 2, corrected here (review 2026-09-25T13-24-26Z):

| revision 2 claim | the source | status |
| --- | --- | --- |
| §2 item 4: the line must already name this checkpoint | the FINAL transaction SETS `current_checkpoint_id` at `:1305`; it is null before a first freeze and names the PRIOR checkpoint before a correction freeze | **REJECTS BOTH NORMAL PATHS.** Replaced by §2. |
| §2: replay "admitted by matching the terminal state" while also returning the committed result | `:1185-1189` replays on the FROZEN row before any current-line predicate | **AMBIGUOUS AND WRONG.** Replay is a separate earlier branch; §2 now says so once. |
| §1: the trace may end at "returns boundary to its caller, which launches" | `stage_execution._LineEnding.mount:1289` returns a PROCESS-CACHED `_prepared` boundary without re-entering `writer_boundary` | **STOPS INSIDE THE INTERVAL UNDER STUDY.** Replaced by §1b. |
| §4: `revoke_writer(..., reached_id)` validating only generation and state | `deadlines` `action` is `report-only` or `cancel` (`:60`), and its own docstring says "a deadline is an observation; advancing a cancel policy is a separate act" | **WOULD SILENTLY CONVERT A REPORT-ONLY DEADLINE INTO A LEASE ACTION.** Replaced by §4. |
| §4 recommended leaving the line `'writing'` while §4/§8 still used a `'revoking'` state | — | **INCONSISTENT.** One representation is chosen in §4. |
| §6: adoption's returned value participates in reciprocity | adoption returns a capability and records nothing | **NOT A DURABLE RESERVATION.** Replaced by §6. |

Revision 3, corrected here (review 2026-09-25T13-39-40Z):

| revision 3 claim | the source | status |
| --- | --- | --- |
| §1b: a start admission keyed to (`writer_id`, `generation`, `runtime_id`) committed "immediately before the engine start" | `attempts.request_runtime_start` ALREADY commits `runtime.start` — labels, `_start_operation_id`, lane occupation and `start-requested` — in one short pure transaction (`:1482-1518`); `adapter.start` runs after it (`:1541`) and only then mints `runtime_id` (`:1567`) | **THE KEY CANNOT EXIST YET, AND THE ADMISSION ALREADY EXISTS.** Replaced by §1b. |
| §1b/§3: confirmed runtime termination discharges the start admission | nothing there prevents a paused submitter or a delayed daemon request from starting a runtime AFTER the observation | **DOES NOT FOLLOW.** Replaced by §3. |
| §3: `finalize_quiescent_assignment` is "necessary" release evidence | `attempts._quiescent:3448` ALSO requires `worker_disposition in schema.DISPOSITIONS` — "finalization ends the assignment of a worker that has ALREADY answered" | **NOT UNIVERSAL.** A deadline-cancelled worker that never answered cannot use it. Replaced by §3. |
| §4: a cancel-intent record "whose pin, policy action, assignment and runtime_attempt_id" match | `documents.py:238` defines `attempt.cancel-intent` as exactly `attempt_id`, `assignment`, `authority_operation_id`, `reason` | **THOSE FIELDS DO NOT EXIST.** Replaced by §4. |
| §4: "refused durably" for mismatched evidence | `ContractRefusal(..., durable=False)` — durability is an explicit flag at the RAISING SITE (`contracts/errors.py:235,318`) | **NO NEW BEHAVIOUR NEEDED**; §4 now says which refusals set it and why. |
| §7: `attempts.py` needed only "if the quiescence evidence contract is touched" | start admission lives in `attempts.request_runtime_start` | **UNDERSTATED.** Replaced by §7. |

Surviving unchanged from revision 1: `_serialized_removal` holds `BEGIN IMMEDIATE` across a
recursive filesystem removal, and my two accepted race orderings pause inside that
transaction, so they are evidence about a design this ruling supersedes.

## 1. The selected path, with its exact callers

    review_driver.prepare_implementation(...)        job_manager/review_driver.py:556
        review_cycles.grant_writer(...)   -> line_writers row state='active';
                                             review_lines.state='writing'
        review_cycles.writer_boundary(...) -> refuses unless state='active' AND the
                                             generation matches (:2741)
            workspaces.line_assignment_workspace(..., control=store)  [R3 adoption guard]
            workspaces._granted_roots(roots, _writer_grant, line_proof=_writer_access)
            source_boundary.compose_runtime_storage_boundary(nominated, roots)
        returns {"boundary": ...}

## 1b. Through the mount consumer to the runtime start — the interval itself

    tools/stage_execution.py, _LineEnding:
      self._prepared = {}                                                   (:1273)
      mount(worker, stage, roots):
          held = self._prepared.get(attempt_id) or self._prepare(stage)     (:1289)
          if held["boundary"] is None: refuse "mounts nothing"              (:1291-1300)
          -> the two roots the container is STARTED over
      two further cache consumers at :1310 and :1539
      _prepare stores at :1386; _recovered stores at :1362

THE GAP, EXACTLY. `mount` is documented "before a runtime starts", and on a cache hit it
does NOT re-enter `writer_boundary`, so no writer state or generation is re-read between
composition and the start. The `boundary is None` refusal only covers a RECOVERED ending
whose writer was already revoked when `_recovered` read it (`:1362`); a cached non-None
boundary composed before a revocation is handed to the start unchanged. A revocation that
commits in that interval is invisible here, and a start already in flight cannot be undone
by any later read. This is precisely what "a token checked before a filesystem write alone
is not enforcement" names.

THE ACTUAL START PATH, TRACED TO ITS OWNER. Revision 3 said "immediately before the
engine start" without naming who that is. It is:

    single_worker._roots -> stage.mount                              single_worker.py:1936
    single_worker._prepared -> attempts.request_runtime_start        (:2059, fresh start)
                            -> attempts.reconcile_runtime            (:2063, otherwise)
    attempts.request_runtime_start                                   attempts.py:1394
        labels = _runtime_labels(attempt); operation_id = _start_operation_id(attempt)
        act(connection):  lanes._occupy_lane(connection, now, attempt_id=...)
                          state <- 'start-requested'
                          returns documents.runtime_start_requested(...)   (:1482-1518)
        -- COMMIT --
        started = _started(adapter.start({"labels": labels, ...}))          (:1541)
        return reconcile_runtime(store, adapter, attempt_id=...,
                                 minted=started["runtime_id"], ...)        (:1567)

SO THE ADMISSION ALREADY EXISTS AND IS ALREADY THE RULING'S SHAPE: a short pure transaction
that occupies the lane and journals `start-requested`, the engine call strictly after the
COMMIT, and the minted `runtime_id` bound afterwards by `reconcile_runtime`. Two consequences
for revision 3's proposal:

1. A key containing `runtime_id` is IMPOSSIBLE at that point — the identity does not exist
   until `adapter.start` returns. Withdrawn.
2. A PARALLEL admission record would be a second lane. The correct proposal is to carry the
   writer/line exclusion INSIDE this existing transaction: `act` additionally reads the line
   writer in-lock and refuses unless its `assignment_generation` is this attempt's and its
   `state='active'`, and records the line reservation (§6) in the same commit. The pre-start
   identity is therefore the one that already exists — the attempt and
   `_start_operation_id(attempt)` — not a new one.

WHERE THE RUNTIME LATER BINDS: `reconcile_runtime(..., minted=...)`, which is also where a
replay lands, so the reservation is keyed by attempt/operation and the runtime identity is
attached to it afterwards rather than being part of its key. A replay of
`request_runtime_start` returns the committed `runtime_start_requested` document and must NOT
re-run the guard as if it were a fresh admission; it is the same act.

WHAT THE LANE ALREADY GIVES, stated so the plan does not duplicate it: `lanes._occupy_lane`
carries a predecessor check and is what produced the refusal "attempt X still holds this
Work's runtime lane". It excludes a second runtime over one Work's material. It does NOT
speak for `line_path` as an object, which is why the line reservation is additional rather
than a re-implementation.

## 2. The completion predicate, with replay kept separate

Read from source: preparation (`:1198-1220`) revokes the writer with cause `'checkpoint'`,
inserts `line_checkpoints` (`checkpoint_id`, `writer_id`, `line_id`, `revision`,
`state='preparing'`) and sets `review_lines.state='freezing'`. The FINAL transaction
(`:1295-1312`) is itself conditional on `state == 'preparing'` and is what sets the
checkpoint frozen and writes `review_lines.state='review-ready'`, `revision`,
`current_checkpoint_id`.

REPLAY IS A SEPARATE, EARLIER BRANCH AND CARRIES NO PHASE PREDICATE. At `:1178-1189`, when
the existing checkpoint is already `frozen`, `store.replay("review-line.freeze:"+id, ...)`
returns the historical committed result. Requiring today's `'freezing'` phase there would
reject legitimate replay after the line has advanced. Revision 2 said both things at once;
this is the single statement: replay answers from the journal, full stop.

PREPARATION OWNERSHIP, for a completion that is NOT a replay, read inside its own lock:

1. `line_checkpoints[checkpoint_id]` exists with `state='preparing'`, `writer_id` = this
   writer, `line_id` = this line, and `revision` = the revision this act prepared; AND
2. the writer row is `state='active'` OR `state='revoked'` with
   `revocation_reason='checkpoint'` — its OWN revocation — and never `'abandoned'` or
   `'expired'`; AND
3. `line_writers.assignment_generation` still equals this act's generation; AND
4. `review_lines.state='freezing'` and `review_lines.current_checkpoint_id` is the PRIOR
   pointer this act prepared against — null for a first freeze, the previous checkpoint for
   a correction freeze — never the checkpoint being completed, because the final
   transaction is what assigns that.

Interrupted preparation is the same predicate: the `'preparing'` row is found and the final
transaction re-enters. `record_progress` (`:1139`) already performs the (2)-style in-lock
read; the narrow gap there is that it does not re-read the GENERATION in-lock.

## 3. The line's writers, and the producer trace that was deferred

`line_path` is a persistent directory in the reserved `_REVIEW_LINE_HOME` namespace, proved
by device+inode. It is disjoint from every custody root, so no custody episode names it.

| writer | reaches `line_path` via | accounting required |
| --- | --- | --- |
| the worker runtime | the writable mount a container is started over | start admission (§1b) discharged by confirmed termination |
| `restore_abandoned_correction` | `profile.restore_checkpoint(line_path, evidence)` (`:2461`) | a manager effect; must itself be admitted and completed, see below |
| `create_line` materialization | line state `'materializing'` | admitted only from a line with no writer |
| `freeze_checkpoint`'s profile step | the profile is handed `line_path` after the object is re-proved | treated as a writer until proved read-only |
| custody helpers | NOT AT ALL — the attempt home only | none; revision 1 wrongly enlisted them |

THE EVIDENCE TAXONOMY, CORRECTED. Revision 3 called
`finalize_quiescent_assignment` necessary release evidence. It is not universal:

- `attempts._quiescent` refuses unless `execution_runtime == 'quiescent'` (`:3455`) AND
  `worker_disposition in schema.DISPOSITIONS` (`:3448`) — "finalization ends the assignment
  of a worker that has ALREADY answered, and this one has not". So it fits SUCCESSFUL
  CHECKPOINT FINALIZATION, where the worker answered, and cannot serve a deadline-cancelled
  worker that never answered.
- UNANSWERED CANCELLATION is `attempts.request_cancellation` (`:2757`): it journals the
  manager's intent BEFORE asking the authority, fences the generation, then ORDERS
  quiescence. Its own docstring is explicit that this is not positive absence — "That gate
  takes positive absence naming the exact runtime... Agent-side quiescence is not that
  evidence and never becomes it" — and `documents` says the same of `quiescence.ordered`:
  "ORDERED, NOT DONE. Reaching a boundary is not evidence of its effect."
- UNKNOWN START is the state this plan must treat most conservatively: `start-requested`
  committed with no minted runtime. Nothing observed, nothing excluded.

So each release path names its own evidence owner: finalization for an answered worker, the
authority's quiescence gate discharge for positive absence of an exact runtime, and NOTHING
for an unknown start — which stays HELD.

AND A RUNTIME OBSERVATION DOES NOT DISCHARGE ITS LAUNCHER. This is the correction that
matters most. An absence or termination observation says something about a runtime that
existed; it says nothing about a submitter paused before `adapter.start`, or a daemon request
still in flight, either of which can produce a runtime AFTER the observation. Revision 3
inferred the launcher was finished from the runtime being gone; that does not follow. So the
reservation is released ONLY when both hold:

1. the submitting effect CANNOT continue — the committed `start-requested` act is either
   settled by `reconcile_runtime` or positively established as unable to proceed; and
2. every runtime it produced is positively accounted for by the evidence owner above.

If either is unknown the outcome is HELD, recorded as such, and not converted into release by
elapsed time. There is no supported evidence today for (1) in the paused-submitter case, so
this plan states it as an unresolved held outcome rather than inventing one.

MANAGER-EFFECT ACCOUNTING, unchanged from revision 3 and still required: each manager effect
over `line_path` commits a short effect admission before it runs and a short settlement after
it completes; an admitted-but-unsettled effect leaves the line HELD, exactly as an unsettled
custody episode does.

## 4. Expiry to revocation, with exact evidence and ONE representation

THE POLICY CONTRACT FIRST, because revision 2 would have broken it. `deadlines` validates
`action` into `("report-only", "cancel")` (`:60`) and its module docstring states "a
deadline is an observation; advancing a cancel policy is a separate act". `observe_deadline`
records `runtime.deadline-reached` for EITHER action. Therefore:

- ONLY a pin whose policy action is `'cancel'` may drive lease revocation, and the driver is
  the cancel path (`advance_deadline` / `_cancel_intent`, `:227`), NOT the bare reached
  record. Mapping any reached record to revocation would convert a reporting deadline into
  a workspace action, which is a contract change.
- IF the owner wants report-only deadlines to revoke leases, that is a concrete owner
  decision to make explicitly, and I am not assuming it.

`revoke_writer(store, *, writer_id, generation, cause, reached_operation_id)` — one short
PURE transaction, identity `review-line.revoke-writer:<writer_id>:<generation>`, operands
(and therefore signature) `{writer_id, generation, cause, reached_operation_id}`. Its
callback reads, all in-lock and all pure DB:

1. the writer row with this exact `writer_id`, `assignment_generation` = this generation and
   `state='active'`; a revoked row is not re-revoked;
2. the deadline row and its IMMUTABLE PIN for `writer["runtime_attempt_id"]`, via
   `deadlines._pin_of`, with its policy action `'cancel'` via `deadlines._policy` — a
   `'report-only'` pin revokes nothing;
3. the committed REACHED observation for that pin, via `deadlines._reached`, whose operation
   id equals `reached_operation_id` and whose digest matches the pin;
4. the deadline CANCEL INTENT, via `deadlines._cancel_intent(store, row, reached_id)` —
   which is a READER: it computes `reason = "runtime deadline reached: " + reached_id`,
   builds the expected `documents.cancel_intent(attempt_id=row["runtime_attempt_id"],
   assignment=_fixed_assignment(row), authority_operation_id=..., reason=reason)`, reads the
   committed `attempt.cancel` record and refuses if it differs. `request_cancellation` is
   the PRODUCER; this transaction never creates the record.

How each wrong case refuses: ABSENT intent — `_cancel_intent` answers no record, so the
revocation refuses NON-DURABLY and stays retryable once cancellation is actually requested.
FOREIGN intent — a record for another attempt or assignment fails (4)'s equality.
ORDINARY NON-DEADLINE CANCELLATION — its `reason` is not
`"runtime deadline reached: " + reached_id`, so it fails (4) too; that is exactly how an
operator cancellation is kept from masquerading as lease expiry. MISMATCHED pin or reached
digest — fails (2) or (3). The `attempt.cancel-intent` schema is used as it exists
(`attempt_id`, `assignment`, `authority_operation_id`, `reason`); nothing here proposes a
richer record.

DURABILITY IS NOT A NEW BEHAVIOUR. `ContractRefusal(category, code, message, *,
durable=False)` makes durability an explicit flag at the raising site, and existing failed
callbacks roll back. So: shape errors that can never become true — a foreign assignment, a
`report-only` pin, a digest mismatch — are raised `durable=True` so the refusal is recorded;
"cancellation has not been requested yet" is raised with the default, so it rolls back and
stays retryable. No journal change is proposed.

REPLAY IS IDENTITY PLUS SIGNATURE, WHICH DECIDES THE COLLISION RULE. `ControlStore.replay`
matches on the operation identity AND the signature, so a repeat of the same
(writer, generation, cause, reached_operation_id) is one act answering the committed result,
while the SAME identity presented with a different cause or a different
`reached_operation_id` has a different signature and must COLLIDE by the store's own
one-identity-one-act rule rather than inherit the earlier success. A COMPETING cause — a
`'checkpoint'` revocation from `freeze_checkpoint` or an `'abandoned'` one from the recovery
— wins or loses by (1): whichever commits first leaves `state='revoked'`, and the other
refuses because the row is no longer `active`. The refusal must name the cause already
recorded so an operator sees which lifecycle claimed it.

ONE LINE-STATE REPRESENTATION, CHOSEN: the line stays in `'writing'`. No `'revoking'` state
is added. `grant_writer` admits only from `('idle','correction-ready')` (`:1088`), so a line
in `'writing'` already admits no replacement, and the revocation lives entirely in
`line_writers`. Everything downstream in this document uses that representation.

THE CRASH-RECOVERY READER, NAMED. Revision 2 said "any caller before anything else", which
is not a plan. The reader is `review_cycles.writer_for_attempt` — already the function
`stage_execution._prepare`/`_recovered` and `review_driver` use to find a writer — extended
to answer, in addition, whether a committed cancel-intent record exists for that attempt
while the writer is still `active`. The call site that must act on it is
`stage_execution._LineEnding._recovered` (`:1362`), because that is where a process that did
not start the attempt decides what it may mount: finding evidence-without-revocation there
must perform `revoke_writer` before composing anything, and the fixed identity makes a
concurrent second attempt one act.

AND THE COUPLING THAT BOUNDS SEQUENCING. `restore_abandoned_correction` requires
`current_writer["state"] == "active"` and `current_line["state"] == "writing"` both before
its effect (`:2444`) and after it (`:2478`). So an expiry revocation makes the one existing
recovery refuse, and the line would be non-admitting AND un-restorable. Options, with a
recommendation: (a) widen that recovery to accept cause `'expired'`; (b) keep the writer
`active` and carry revocation elsewhere — rejected, it splits revocation in two;
(c) RECOMMENDED — that recovery demands an active writer only because it holds the write
lock across the restore and treats the lock as its exclusion (its docstring calls that
tradeoff "THE REVIEWER'S TO HAVE ACCEPTED"), so under this ruling its precondition inverts
to "the writer is revoked AND its termination is confirmed", making the expiry revocation
and the §5 item 3 reorder ONE change. §8's slice is bounded so that nothing observable
changes before that change lands.

## 5. The corrected bounded I/O inventory

VIOLATIONS, to replace:
1. `workspaces.py:1673` `_serialized_removal.removal` — recursive filesystem removal inside
   `control.transact`'s `BEGIN IMMEDIATE`. Callers `discard_workspace`,
   `discard_execution_roots`.
2. `review_cycles.py:1099` `grant_writer.act` — `_validate_line_object` and
   `workspaces._prove_line_access` stat the filesystem inside the transaction.
3. `review_cycles.py:2461` `restore_abandoned_correction` — `profile.restore_checkpoint`
   runs the whole checkout restoration inside the serialized act, deliberately.

COMPLIANT, and the models: `freeze_checkpoint`'s preparation block (pure DB; the Authority
fence at `:1227` and the sealing follow the COMMIT — note it uses a raw `BEGIN IMMEDIATE`
rather than `transact`, so it carries no replay identity), `deadlines.observe_deadline`
(Authority call before; callback reads DB and clock), `record_fence` (one UPDATE), all five
`custody.py` transacts, both `workspaces` configure transacts.

NOT ASSESSED: every other `transact` site in the tree. No claim either way.

## 6. Reciprocity, in BOTH directions, with the old effect as the hard case

Revision 2 treated adoption as a participant in reciprocity. It is not: adoption returns a
capability and RECORDS NOTHING, so there is nothing for a remover to conflict with. Both
directions therefore need a durable record:

- REMOVAL-FIRST: one short transaction commits a removal intent bound to
  (`assignment_id`, BOTH overlapping roots, an intent generation), refused if any custody
  episode stands, any use reservation stands, or another intent is open. The effect runs
  with no transaction open. Settlement is a short conditional transaction keyed to the
  intent generation.
- ADOPTION-FIRST: adoption (and the start/effect admissions of §1b and §3) commits a
  durable USE RESERVATION over the same resource identity, refused while a removal intent
  is open. A removal intent is then refused while a reservation stands. The two records are
  one conflict domain, read by the same readers a custody episode is read by:
  `custody._claim_episode`, `adopted_assignment_workspace`, `grant_writer`.
- RESOURCE IDENTITY: the overlap rule is the R3 one for the attempt home — the two custody
  roots nest, so an intent or reservation on either covers both — and for `line_path` it is
  the line object (path plus device and inode), which is disjoint from the attempt roots.
- THE OLD EFFECT IS THE HARD CASE, and the review is right that a settlement-generation
  check cannot stop it. A crashed remover's `rm` may still be running in a process nobody
  can see. So: a committed intent with no settlement leaves the resource HELD, expiry of
  the intent is NOT release, and REUSE OR SUPERSESSION IS FORBIDDEN until that effect's
  termination is established by the same confirmation the writer path requires. Recovery
  answers "held, and here is the intent to reconcile", never "probably finished".

## 7. Ownership the implementation would need, named

Mine today: `custody.py`, `workspaces.py`, author tests, PROGRESS, this file, and owner
262043's caller propagation in `review_cycles.py`, `single_worker.py`,
`integration_worker.py`, `dogfood_operator.py`. NOT covered, each an exact extension to
request when a slice is selected: new lease/revocation transitions in `review_cycles.py`;
`deadlines.py` for the pin/reached/cancel-intent READERS reused inside the transaction;
`attempts.py` FOR THE START ADMISSION ITSELF, because `request_runtime_start`'s existing
transaction (`:1482-1518`) is where the writer/line guard and the reservation belong, and
`reconcile_runtime` (`:1567`) is where the runtime binds — revision 3 understated this as
"only if the quiescence evidence contract is touched"; and the consumers
`tools/stage_execution.py` (`_LineEnding`), `tools/single_worker.py` (`_roots` at `:1936`,
`_prepared` at `:2059`) and `job_manager/review_driver.py:556`. `intake.py` remains the pending `_settle` operand only.

## 8. The exact matrix — TWENTY-SEVEN cases — and the smallest slice

One new author module `test_lease_boundary.py`, real local stores and the accepted fake
engine only. Selectors recorded here BEFORE any execution, per the discipline in
VERIFICATION-SELECTORS.md.

    ExpiryRevokesAndDoesNotFree                                                   (6)
      test_a_cancel_policy_reached_record_with_its_intent_revokes_with_the_expired_cause
      test_a_report_only_pin_revokes_nothing
      test_an_absent_cancel_intent_refuses_without_recording
      test_a_foreign_assignment_or_mismatched_pin_digest_refuses_durably
      test_an_ordinary_operator_cancellation_is_not_deadline_expiry
      test_a_revoked_line_admits_no_replacement_writer
    RevocationReplayAndCompetingCauses                                            (3)
      test_the_same_writer_generation_cause_and_evidence_is_one_act
      test_the_same_identity_with_a_different_cause_or_evidence_collides
      test_a_checkpoint_revocation_and_an_expiry_revocation_yield_one_recorded_cause
    LegitimateCompletionSurvivesItsOwnRevocation                                  (4)
      test_a_first_freeze_completes_with_a_null_prior_pointer
      test_a_correction_freeze_completes_against_the_prior_checkpoint
      test_an_interrupted_preparation_completes_on_re_entry
      test_a_replay_after_the_line_advanced_answers_the_committed_result
    TheStartIsAdmittedInsideTheExistingStartTransaction                           (5)
      test_a_revoked_generation_refuses_the_existing_start_transaction
      test_a_cached_boundary_cannot_start_after_a_revocation_commits
      test_a_replayed_start_request_answers_its_committed_document_without_re_guarding
      test_a_paused_submitter_keeps_the_reservation_held_through_an_absence_observation
      test_the_reservation_releases_only_after_the_submitter_is_settled_and_its_runtime_accounted
    TheLineWritersAreExcludedByObject                                             (3)
      test_a_manager_owned_restore_is_refused_while_termination_is_unconfirmed
      test_the_authorized_recovery_writer_is_admitted_after_confirmed_termination
      test_an_admitted_but_unsettled_manager_effect_leaves_the_line_held
    TheReciprocityHoldsInBothOrders                                               (6)
      test_a_conflicting_claim_refuses_while_a_removal_intent_is_open
      test_a_removal_intent_refuses_while_a_use_reservation_stands
      test_a_crash_before_the_effect_leaves_the_resource_held_and_bytes_intact
      test_a_crash_after_the_effect_leaves_the_intent_reconcilable
      test_a_reopened_manager_refuses_reuse_while_the_old_effect_is_unestablished
      test_an_unrelated_attempt_progresses_throughout_with_its_bytes_preserved

The per-class counts above sum to the total in this heading; both were produced by counting
the file rather than asserted.

SMALLEST FIRST SLICE: `revoke_writer` with the exact §4 evidence join — pin, policy action,
reached digest and the `_cancel_intent` reader — plus the `ExpiryRevokesAndDoesNotFree` and
`RevocationReplayAndCompetingCauses` cases, NINE methods, LEFT UNWIRED, since `observe_deadline` has no production caller and wiring ahead of the
§4(c) reorder would strand lines. It adds one pure short transaction, no state value, and
changes no existing precondition. THE COMPLETE WIRING PLAN IS §1b PLUS §4's named reader and
call site; the slice defers its execution, it does not replace it. Explicitly NOT in the
slice: the three I/O violations, the start/effect admissions, the reciprocity protocol, the
recovery precondition inversion, and the retirement of my two race orderings, which belongs
with §5 item 1.
