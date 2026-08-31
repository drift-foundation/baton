# No public ending for a started runtime whose worker never answered

Work: W44716
Discovery: W39358 composition review

## Observed

A runtime can start successfully and remain attached while the subsequent
worker-entry conversation is lost or answers without a worker disposition.
The attempt then has a named live runtime, no worker disposition, no frozen
output, no intake receipt, no `runtime.start-failed` record and no refused
agent-session record.

The W39358 operator must not invent a deployment-owned destroy beside the
Worker Manager's existing removal boundaries. It currently preserves this
state as unresolved and names the runtime.

The current public operations divide the ending into four incompatible
authorizations:

- `authorize_cleanup` in `worker_manager/intake.py` spends an intake receipt.
  With no receipt it records `cleanup = blocked-on-intake` and never calls the
  adapter.
- `authorize_failed_start_cleanup` spends a committed
  `runtime.start-failed` record naming the exact attached runtime. A start
  which succeeded has no such record.
- `authorize_refused_session_cleanup` spends a committed
  `session.unsupported-version` record naming the exact attached runtime and
  session. A worker-entry conversation is not an ACP handshake refusal and
  has no such record.
- `request_cancellation` in `worker_manager/attempts.py` commits an
  `attempt.cancel` intent, fences the exact authority assignment, asks an
  agent to cancel, then asks the adapter to stop. Its own docstring is
  explicit that this is an order, not positive runtime absence and not
  satisfaction of the authority's quiescence gate. No public cleanup spends
  this record.

The result is observable elsewhere: `test_runtime_lane.py` proves a cancelled
attempt keeps its runtime lane until cleanup ends, but there is no general
cancelled-attempt cleanup which can produce that ending without an intake
receipt.

## Confirmed boundary facts

- **Confirmed:** `attempt.cancel-intent` contains `attempt_id`, `assignment`,
  `authority_operation_id` and `reason`, but not `runtime_id`. A later cleanup
  must not combine this record with a separately read current runtime. The
  failed-start and refused-session P0 corrections already established that a
  manager-owned record authorizing removal must itself name the exact runtime.
- **Confirmed:** `request_cancellation` requires both `agent.cancel` and
  `adapter.stop` before it records anything. `worker_entry.ChannelPort` carries
  only an opened framed conversation, and `baton.worker-entry/1` speaks only
  `describe`, `consider` and `work`; it exposes no honest agent-cancel
  capability. A no-op adapter would fabricate a boundary act.
- **Confirmed:** the worker-entry transport's `lost` ending deliberately says
  only that the manager cannot know what the worker did. It is not a worker
  disposition and must not be translated into one.
- **Confirmed:** the three destroy adapter commands have closed sibling member
  sets and share only the force-removal core. W34998's ruling forbids widening
  one command into a union accepting another authorization digest.
- **Confirmed:** the M33800 custody ruling already covers crash, timeout,
  forced stop, unknown ending and missing trustworthy envelope. The existing
  unique result directory remains in place and untrusted; receiptless cleanup
  therefore ends `retained`, not `complete`, and creates no second result or
  custody copy.
- **Confirmed:** positive `absent` observation owns credential and launch
  teardown and releases the runtime lane. A stop settlement, a conversation
  ending, or an `uncertain` observation is not a substitute.

## Minimal reproduction

1. Record and activate an assignment, then let `request_runtime_start` attach
   a named runtime.
2. Receive `worker_entry.converse(...)["ending"] == "lost"`; record no worker
   disposition, frozen output or intake receipt.
3. `authorize_cleanup` returns `blocked-on-intake` without invoking destroy.
4. `authorize_failed_start_cleanup` refuses because no
   `runtime.start-failed` record exists.
5. `authorize_refused_session_cleanup` refuses because no matching refused
   session record exists.
6. A cancellation can fence and order stop only if the caller owns a real
   `agent.cancel`, and even then leaves cleanup pending and the lane held.

The W39358 regression
`EveryPostStartBranchEntersTheEnding.test_transport_and_disposition_failures_do_not_return_around_ending`
drives the deployment-facing state. The manager-side baselines are
`BlockedOnIntakeIsAStateAndNotARetry.test_cleanup_without_custody_is_recorded_as_blocked`,
`CancellationFencesBeforeItStops`, and
`ASuccessorWaitsForItsPredecessor.test_a_cancelled_attempt_keeps_the_lane_until_cleanup_ends`.

On 2026-08-30 the focused source-layout run passed all 10 cancellation cases,
the no-receipt blocked cleanup, the missing refused-session authorization, the
cancelled lane hold, and both W39358 post-start conversation branches (15
tests total). This proves the individually intended behaviours which compose
into the gap; it is not a passing end-to-end ending for this state.

## Research questions

- Confirm whether any current public operation can end this exact state while
  preserving authority fencing, positive runtime absence and credential/launch
  delivery teardown.
- Determine whether the state is an existing cancellation/refused-session
  authorization used incorrectly by W39358 or a genuinely missing manager
  authorization and outcome.
- If a surface is missing, identify the minimal durable evidence that
  authorizes it and the correct terminal vocabulary when no output was frozen
  or taken into custody.

## Inference

This is a genuinely missing receiptless ending, not misuse of one of the
three existing authorizations. The safe shape is a fourth closed sibling:

1. a manager-owned durable record binds the exact attempt, fixed assignment,
   exact attached runtime and typed reason before authority or engine calls;
2. the authority fences that assignment before anything destructive;
3. a distinct adapter command carries the digest of that record and force
   removes only the named runtime;
4. positive absence settles the provider roots, records cleanup `retained`
   and releases the lane.

This follows the refused-session ordering without pretending that a lost
worker-entry conversation is a refused ACP session. The shared implementation
boundary should remain `_removed` in `oci.py` and
`_settle_recordless_cleanup` in `intake.py`; the new authorization, record
reader and closed command stay separate.

## Open decision for the approver

The repository has no ruling for what the new record should assert or which
public call owns the missing agent boundary. Two materially different designs
remain:

1. **Recommended: explicit abandonment ending.** Add one public operation for
   an assigned, started runtime whose supervised conversation cannot produce a
   worker disposition. It records an `attempt.abandoned`-style document naming
   the exact runtime, fences the authority, and drives a fourth receiptless
   destroy authorization. It does not require or fabricate `agent.cancel`,
   because this topology has no persistent agent-session cancellation port.
2. **General cancelled-attempt cleanup.** Extend the cancellation intent to
   name the exact runtime and add a cleanup that spends it. This is broader,
   but it still leaves W39358 unable to enter `request_cancellation` honestly
   unless that operation also gains an explicit no-agent-session variant.

The decision must also pin whether the public API is one composite call or a
record/fence call followed by an independently retryable cleanup call. The
durable operations may remain separate internally either way.

## 2026-08-30 — approver ruling: minimal explicit abandonment

The first worker deployment should be used before longer-term cancellation
and timeout policy is tuned. A timer, missed heartbeat or slow answer does not
automatically abandon an attempt. Once an operator or explicit Route policy
decides the attempt is abandoned, the Worker Manager performs one composite
public ending:

1. durably identify the exact attempt, assignment generation, runtime and
   typed abandonment reason;
2. fence and end that exact assignment generation before runtime control;
3. stop/remove only the exact runtime the manager started;
4. positively observe runtime absence;
5. retain the existing output/result root as untrusted, tear down the exact
   credential and launch deliveries, and release the runtime lane.

This adopts the explicit-abandonment direction and rejects widening general
cancellation for this pilot. The worker-entry topology has no honest
`agent.cancel`, and no such act is fabricated. The public surface is one
composite operation so a caller cannot stop after only the record, fence or
runtime-control half; its manager-owned internal steps remain durable and
replayable across interruption.

Stopping and proving the worker absent is a necessary precondition for
trusting any candidate bytes, not sufficient evidence that they are correct.
An unanswered/abandoned attempt's bytes remain untrusted even after shutdown
and may be inspected later. If the fence, stop or absence proof is uncertain,
the operation remains unresolved and does not release the lane or claim a
completed ending.

No long-lived engine provider, automatic timeout action or generalized
cancel/cleanup architecture is added by this ruling. Those decisions follow
operational evidence from real workers rather than precede it.

## Implementation contract

The one public operation is `abandon_attempt(store, port, adapter, *,
attempt_id, reason, retention_policy_digest)`, exported from
`baton_v12.worker_manager`. It lives with the receiptless cleanup siblings in
`worker_manager/intake.py`; no new module or general cancellation abstraction
is needed for the pilot.

### Caller declaration and eligibility

- `reason` is required, non-empty durable text. There is deliberately no
  deadline, elapsed-time, retry-count or heartbeat operand and the operation
  reads no clock to decide whether abandonment is permitted. Calling the
  operation is the explicit operator/Route-policy declaration.
- Before recording a new declaration, the attempt must have one fixed
  assignment, one exact attached runtime, `worker_disposition == "none"`,
  `output == "open"`, and cleanup still `pending` or `blocked-on-intake`.
  The participant-bound authority port must act for that assignment.
- The adapter must carry the new exact capability before anything is recorded
  or fenced. A missing deployment capability must not leave an abandoned
  assignment half-recorded.
- Exact replay is checked before mutable terminal-axis preconditions, so a
  successfully retained ending remains replayable. A different reason under
  the same attempt/generation is an operation collision, not a second
  abandonment declaration.

### Durable identities and documents

The manager declaration journal kind is `attempt.abandon`; its fixed identity
is `attempt.abandon:<digest>` derived from the attempt and its fixed assignment
generation, not from the reason or runtime. Its signature additionally binds
the exact `runtime_id`, required `reason`, and the distinct authority operation
identity. Thus a changed reason or attached runtime collides instead of
committing a second declaration.

The committed `attempt.abandon-intent` document has this closed required set:

```text
attempt_id
assignment
runtime_id
decision = "abandoned"
authority_operation_id
reason
```

The authority operation identity is derived from the same attempt/generation
and is deliberately distinct from both `attempt.abandon:*` and
`attempt.cancel:*`. The composite reissues `AuthorityPort.cancel` with that
exact identity on every retry. `AuthorityPort.cancel` already owns the closed
fence answer and proves that this exact generation was fenced; no liveness
pre-read or post-fence inference substitutes for that answer.

The adapter sibling is `destroy_abandoned(command)`. Its closed
`destroy.abandoned-command` contains:

```text
assignment_ref
runtime_attempt_id
runtime_id
abandonment_record_digest
retention_policy_digest
```

The destroy journal kind/identity is `runtime.destroy-abandoned`. The record
digest and retention-policy digest participate in that operation identity as
they do for the failed-start and refused-session siblings. A different
retention policy is a distinct cleanup act and, after a terminal ending, is
refused without another engine call; it does not rewrite the abandonment
declaration.

The composite answer is a closed `attempt.abandonment` document containing
the nested `intent`, authoritative `fenced` answer, and `cleanup` answer. An
unsettled destroy remains explicitly unsettled; the document never converts a
stop order or uncertain observation into an ending.

### Exact order and restart behavior

1. Own operands, participant, exact assignment/runtime, adapter capability and
   new-operation eligibility.
2. Commit or replay `attempt.abandon-intent` before any external call.
3. Fence the exact authority generation through the distinct effectively-once
   authority operation. Nothing calls `adapter.stop` before this proof.
4. Read and validate the committed intent as the authorization, including its
   exact attempt, assignment, runtime and `decision == "abandoned"`.
5. Call only `adapter.destroy_abandoned`, carrying the intent digest and the
   exact runtime. OCI reuses `_removed`, whose force-removal is the combined
   stop/remove act and whose observation owns positive absence.
6. Reuse `_settle_recordless_cleanup`: only positive absence plus settled
   credential and launch endings records runtime `destroyed`, cleanup
   `retained`, and releases the lane. The unique untrusted result directory is
   left in place and no disposition, freeze, intake or retention row is
   invented.

A crash after the intent, fence, engine removal or terminal journal is resumed
by the same public call: replay the intent, replay the exact authority fence,
and retry/replay the force-removal. Force-removal of an already absent exact
identity is safe; claiming absence without the adapter observation is not.

`execution_runtime == "uncertain"` may still be fenced, because stopping
further authorized execution is the purpose of abandonment, but cleanup stays
unresolved until reconciliation restores a positive observation. The lane is
not released. A positive survivor, mismatched runtime identity, unresolved
provider ending or adapter failure likewise claims no terminal ending.

## Exact patch boundary after ruling

- `worker_manager/documents.py`: `attempt.abandon-intent`,
  `attempt.abandonment` and `destroy.abandoned-command`; no union with receipt,
  failed-start or refused-session commands.
- `worker_manager/intake.py`: the public `abandon_attempt`, private declaration
  and destroy identities/readers, exact fence composition, exact-runtime
  destroy crossing, and `_settle_recordless_cleanup` reuse.
- `worker_manager/oci.py`: add the typed sibling capability and reuse
  `_removed`; do not duplicate provider teardown.
- `worker_manager/__init__.py`: export only `abandon_attempt`; operation
  builders and record readers remain internal.
- `tools/dogfood_operator.py`: replace the W44716 unresolved branch with the
  public manager ending. It must not read manager storage or call an OCI
  destroy capability directly.

## Required regression matrix

- positive lost-conversation and correlated-fault/no-disposition endings;
- no timer, elapsed time or missed-heartbeat condition invokes abandonment;
- missing reason/capability, no assignment/runtime, a recorded worker
  disposition, non-open output, wrong participant and another terminal cleanup
  all refuse before the declaration, authority and engine boundaries;
- live authority assignment is fenced before the adapter is called;
- no worker disposition, frozen output, intake or proposal admission is
  manufactured;
- the authorizing record and destroy command name the same exact runtime;
- missing record, wrong kind, changed assignment/runtime, wrong typed verdict
  and cross-called sibling command all refuse before engine access;
- exact replay before/after fence and before/after engine removal is stable;
  changed reason/runtime collides, while a changed policy forms a distinct
  cleanup act which cannot revisit a terminal ending;
- unreachable authority, failed stop/removal, positive survivor, uncertain
  observation and mismatched adapter identity retain the lane and do not claim
  an ending;
- positive absence tears down credential and launch deliveries, leaves the
  untrusted result directory in place, ends `retained`, and only then releases
  the lane;
- restart reads the committed authorization rather than recomposing it;
- real OCI composition proves force-removal and positive absence using the
  same `_removed` core.

The additive red acceptance
`ExplicitAbandonmentFencesBeforeItRemoves.test_the_public_ending_fences_then_removes_and_retains`
is in `tests/manager/test_attempts.py`. It constructs the exact attached,
unanswered state and requires the public call, fence-before-remove order,
closed abandonment digest command, positive absence, unchanged worker/output
axes and terminal retained cleanup. Before implementation it fails only at the
missing `abandon_attempt` public operation.

## Initial acceptance boundary

- One public manager operation owns the exact started-runtime/no-answer state;
- the exact live generation is ended or fenced before destructive runtime
  control;
- only the manager-created runtime and deliveries are removed;
- runtime absence and both provider endings are positively observed;
- exact replay is stable, changed operands collide, and restart resumes
  without manufacturing a worker disposition, frozen output or intake receipt;
- W39358 can consume the operation without opening manager storage or growing
  its own removal boundary.

## 2026-08-30 — implementation revalidation (`baton.claude`, W44716 impl claim)

### The dossier is implementation-ready and the spec checks out against the tree

Revalidated rather than assumed, because the contract names symbols in four
production files and a spec that has drifted is worse than none:

- `_settle_recordless_cleanup`, `refused_session_destroy_operation`,
  `_removed`, `destroy_refused_session`, `SESSION_UNSUPPORTED_VERSION`,
  `_require_participant` and `_fixed_assignment` all exist as the contract
  describes, so the sibling this mirrors is really there to mirror.
- Nothing in `worker_manager/` is named `abandon` yet, so
  `attempt.abandon-intent`, `attempt.abandonment`, `destroy.abandoned-command`
  and `runtime.destroy-abandoned` collide with no existing vocabulary. The
  nearby `recovery.report` member `abandoned` and the offers axis value
  `abandoned-after-restart` are different facts about different objects and
  are not overloaded by any of them.
- The additive red case is in `tests/manager/test_attempts.py:1667` and fails
  only for the operation's absence, which is exactly the shape the contract
  claims.

### Nothing else changed this round, and why

The implementation is ~300 lines across `documents.py`, `intake.py`, `oci.py`
and `__init__.py` plus the regression matrix, inside the manager's ending
core. On W43975 — the sibling ending Work, claimed minutes before this one — I
declined to start a change of exactly that shape at the end of a very long
session, and said so in terms. Starting a LARGER one here would contradict
that within the hour, and the reason has not changed: on W39358 the same
reviewer corrected me three rounds running for a record that outran its code,
each time on a large composition written at the end of a long stretch.

What this round adds is that the next one starts from a CHECKED spec rather
than an assumed one, which is the part that goes stale while a dossier waits.
