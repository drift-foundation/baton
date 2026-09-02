# W63255 reviewer research — 2026-09-01

## Result

The pre-attach recovery has no path to the authority. It can prove resources
absent and report `resolved`, but it neither commits an assignment-ending
declaration nor fences the exact generation. The correction is a distinct
public manager operation that reuses abandonment's durable intent and
`AuthorityPort.cancel` crossing without pretending a runtime exists.

No protocol or application code was changed by this research.

## Retained observation

`/tmp/w61984/run3/recovery.json` records:

- exact fixed assignment: `baton.claude`, generation 1;
- `attempt_state.execution_runtime`: `not-started`;
- `attempt_state.runtime_id`: null;
- runtime: absent;
- credentials and launch: torn down;
- `authority_fence`: null;
- `resolved`: true.

The public authority projection retained by the dossier still showed the Work
active with that Handler and generation and no fenced generation. The SQLite
stores were not read directly; the public projection recorded by the
discovering operator is the coordination evidence.

## Exact control flow

1. `recover_abandoned` reads one manager projection with
   `attempt_runtime_of` and passes it privately to `_recovering`.
2. `_assignment_disagrees` compares all fixed-assignment members with editable
   grants before capabilities act.
3. If `runtime_id is None`, `_recovering` calls `_pre_attach_recovered` with
   store, adapter, grants, orphan and launch home. It does not pass `port` or
   `reason`.
4. `_pre_attach_recovered` obtains manager label context, calls
   `adapter.recover_credentials` for positive runtime absence, tears down the
   deployment-owned credential/launch roots, and sets `resolved` when its
   resource account has no unresolved member.
5. The attached branch alone calls `abandon_attempt`, receives its exact fence
   answer and fills `authority_fence`.

The defect is therefore structural, not a missing final comparison: the
pre-attach branch has no fence evidence it could compare.

## Existing operations and why they differ

### `request_cancellation`

It commits `attempt.cancel`, calls `AuthorityPort.cancel`, requests agent-
session quiescence, then asks an agent and runtime adapter to stop. Although its
no-runtime tail answers `quiescence.not-ordered`, the public operation validates
both capabilities before it knows that. Recovery has no live agent capability,
and a dummy one would be invented authority.

### `abandon_attempt`

It is the correct owner for an operator's explicit abandonment declaration and
already provides:

- fixed attempt/assignment operation identity;
- reason collision under effectively-once replay;
- intent committed before the external fence;
- a distinct authority fence operation;
- exact four-member answer binding through `AuthorityPort.cancel`.

It also deliberately requires a non-null runtime, `destroy_abandoned`,
directory custody and terminal runtime settlement. Those belong to attached
W44716 abandonment and must remain strict.

## Recommended patch boundary

Add one exported manager operation, colocated with abandonment so it can share
the private intent/fence primitives. A descriptive name such as
`fence_pre_attach_abandonment` is preferable to widening `abandon_attempt` into
two result shapes.

The operation should:

1. own attempt id and nonblank bounded reason;
2. load the fixed assignment and require the authority session participant;
3. require `runtime_id is None`, execution `not-started`, worker disposition
   `none`, output `open`, and cleanup pending/blocked-on-intake;
4. in one manager transaction, commit/replay the abandonment intent and move
   execution away from `not-started` to an explicit cancellation/abandonment-
   in-flight state so a concurrent runtime start cannot become eligible;
5. adopt the committed intent and call `AuthorityPort.cancel` with its exact
   assignment, authority operation id and reason; and
6. return a closed `{intent, fenced}` document whose fence is exact.

The operator's pre-attach branch invokes this before
`adapter.recover_credentials`. It copies the exact answer into
`record.authority_fence`; every partial-account path preserves or re-observes
that fact. Existing positive absence, credential teardown, launch teardown and
orphan checks then run unchanged. `resolved` requires all of them plus
`fenced is true` and the fixed generation.

Do not call the underlying authority session from `dogfood_operator`; the
manager port is the boundary that owns and relates the fence answer. Do not
mark a no-runtime attempt terminal merely from a null manager field. Any later
manager-axis settlement or quiescence-gate discharge needs its own positive
absence evidence and remains separate from this assignment fence.

## Race and retry boundaries

- **Start already won:** if execution is `start-requested` or a runtime is
  attached before the intent transaction, refuse pre-attach without fencing;
  a fresh projection selects reconciliation/attached abandonment.
- **Abandonment won:** once intent plus in-flight state commits,
  `request_runtime_start` must fail before calling the adapter.
- **Crash after intent, before fence:** retry adopts the same intent and
  reissues the same authority operation.
- **Crash after fence, before resource cleanup:** retry replays the fence and
  resumes cleanup; the recovery record remains unresolved until all proofs
  are present.
- **Changed reason:** same manager operation identity, different signature,
  so collision and unresolved.
- **Changed attempt/assignment:** a different identity or an exact fixed-
  assignment hold refusal, never replay of this ending.

## Regression matrix

Positive:

- command over a real activated/no-runtime attempt exits 0 only after the
  public authority projection has no Handler/live generation and generation 1
  is fenced;
- recovery records the exact fence, absent runtime, and torn-down or
  not-delivered credential/launch states;
- exact same-reason retry replays without a second authority act.

Negative:

- stale generation, participant, Work, authority or attempt refuses before a
  fence or cleanup;
- missing fixed assignment, wrong authority session, blank reason, worker
  disposition other than `none`, non-open output or terminal cleanup refuses;
- a fence answer for another assignment or `fenced != true` stays unresolved;
- absent fence evidence can never coexist with `resolved == true`.

Race/fault:

- start-request versus pre-attach intent in both winning orders;
- authority faults before and after committing the fence;
- resource cleanup fault after the fence leaves the exact fence in the
  durable recovery record and exits nonzero;
- restart from each boundary converges under the original reason.

Non-effects:

- no output freeze, intake, retention choice, custody acceptance, review,
  integration or Baton pass;
- no invocation or relaxation of W61984's quiescent-finalization requirement
  for a recorded terminal worker disposition.
