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

## Proposed patch boundary after ruling

- `worker_manager/documents.py`: the manager record and one new closed destroy
  command; no union with receipt, failed-start or refused-session commands.
- `worker_manager/attempts.py` or a narrowly named ending module: record before
  the fence and own exact retry across the authority boundary.
- `worker_manager/intake.py`: read back and validate the record, build the
  exact-runtime destroy operation, and reuse `_settle_recordless_cleanup`.
- `worker_manager/oci.py`: add the typed sibling capability and reuse
  `_removed`; do not duplicate provider teardown.
- `worker_manager/__init__.py`: export only the decided public operation(s).
- `tools/dogfood_operator.py`: replace the W44716 unresolved branch with the
  public manager ending. It must not read manager storage or call an OCI
  destroy capability directly.

## Required regression matrix

- positive lost-conversation and correlated-fault/no-disposition endings;
- live authority assignment is fenced before the adapter is called;
- no worker disposition, frozen output, intake or proposal admission is
  manufactured;
- the authorizing record and destroy command name the same exact runtime;
- missing record, wrong kind, changed assignment/runtime, wrong typed verdict
  and cross-called sibling command all refuse before engine access;
- exact replay before/after fence and before/after engine removal is stable;
  changed reason, policy, runtime or generation collides or forms a distinct
  operation exactly as the ruling specifies;
- unreachable authority, failed stop/removal, positive survivor, uncertain
  observation and mismatched adapter identity retain the lane and do not claim
  an ending;
- positive absence tears down credential and launch deliveries, leaves the
  untrusted result directory in place, ends `retained`, and only then releases
  the lane;
- restart reads the committed authorization rather than recomposing it;
- real OCI composition proves force-removal and positive absence using the
  same `_removed` core.

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
