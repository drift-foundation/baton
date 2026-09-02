# Fence pre-attach assignments during explicit abandonment

Ledger Work: W63255

Follow-up to W55758,
`work/records/2026/08/finding-interrupted-dogfood-attempt-strands-runtime-credential/`.

## Observed — 2026-09-01

W61984 run3 committed and activated `baton.claude` generation 1, then refused
while reading a non-private credential-source registry. No credential bearer,
container or provider turn started. The documented dogfood `--abandon`
command returned exit 0 and wrote `resolved: true`, branch `pre-attach`, exact
runtime state `absent`, credentials `torn-down`, and no unresolved members.

The public v12 authority projection afterwards still reports the same Work
`active`, Handler `baton.claude`, live generation 1, and no fenced generation.
The recovery record's `authority_fence` is null. Evidence is retained under
`/tmp/w61984/run3/recovery.json` and the disposable authority beside it.

## Confirmed defect

A recovery cannot truthfully declare an activated attempt resolved while its
exact authority assignment remains live. Runtime absence and credential
teardown prove resources ended; they do not release assignment authority or
participant capacity.

This case is outside W61984's approved already-quiescent finalizer because the
worker disposition remains `none`. W61984 must continue to refuse that input.
The pre-attach abandonment path instead owns the explicit operator declaration
that this interrupted attempt is over.

## Direction

For a pre-attach attempt with a fixed live assignment, explicit abandonment
must fence/end that exact assignment through the public authority boundary and
record the fence before reporting `resolved`. A stale, mismatched or ambiguous
assignment refuses and remains unresolved. Exact retries replay; changed
attempt, assignment, generation or reason operands collide. The operation
still performs no output acceptance, retention, review or integration act.

Add a command-level regression that activates an assignment, fails before
runtime attachment, abandons it, then reads the public authority projection
and proves the Handler/live generation are gone and the exact generation is
fenced. A recovery that does not obtain that proof exits nonzero.

## Bounded workaround

Preserve run3. W61984 may continue with a new disposable authority and attempt
identity after correcting the credential-registry mode; never reuse run3 or
represent its still-live disposable assignment as recovered.

## Reviewer revalidation — 2026-09-01

**Confirmed root cause:** `_recovering` branches on the manager's atomic
`attempt_runtime_of` projection. When `runtime_id` is null it calls
`_pre_attach_recovered`, but that helper receives neither the authority port
nor the operator's abandonment reason. It proves runtime absence, tears down
credentials and launch material, and sets `resolved = True` solely from those
resource facts. No authority operation is reachable on that branch, so
`authority_fence` necessarily remains null.

The attached branch cannot simply be called instead. `abandon_attempt`
correctly requires a non-null attached runtime, an abandoned-runtime destroy
capability and directory custody; weakening those preconditions would turn a
no-runtime declaration into authorization for the W44716 runtime ending.
`request_cancellation` can fence an assignment with no runtime, but it requires
agent and runtime-stop capabilities and requests agent-session quiescence.
The documented pre-attach recovery owns none of those capabilities and must
not fabricate them.

**Confirmed reusable boundary:** the attached abandonment already has the
right declaration identity and authority crossing. `_abandon_intent` commits
or replays an intent keyed by the exact attempt and fixed assignment; its
signature carries runtime identity and reason, and `_abandon_fence_operation_id`
is distinct from ordinary cancellation. `AuthorityPort.cancel` proves the
authority fenced the exact four-member assignment. The correction should
factor and reuse these pieces, not call the session directly from the
deployment.

**Proposed correction:** add a public manager operation for pre-attach
abandonment fencing. It accepts only store, authority port, exact attempt and
the operator reason; requires the fixed assignment, matching participant,
`runtime_id is None`, `execution_runtime == not-started`, worker disposition
`none`, output `open` and nonterminal cleanup; commits the abandonment intent
and an in-flight no-start state atomically; then calls `AuthorityPort.cancel`
with the adopted intent's assignment, operation id and reason. Its closed
answer carries the intent and exact fence.

The atomic no-start state is required. Without it, a runtime start can commit
after the pre-attach projection but before the authority fence, leaving a
newly attached runtime on a branch that owns no agent/stop capability. If a
start already won, the pre-attach operation refuses without fencing and a
fresh recovery observation selects the attached branch. If the abandonment
intent won, `request_runtime_start` can no longer pass its `not-started`
precondition.

Only after the exact fence answer is recorded may the existing positive-
absence and credential/launch cleanup continue. `resolved` additionally
requires `authority_fence == {fenced: true, generation: <fixed generation>}`.
Replay uses the same intent and authority operation; a changed reason collides,
and a changed attempt or fixed assignment is not the same operation. This does
not accept output, settle custody, make a retention decision or invoke
W61984's terminal-disposition finalizer.

Detailed code paths, ordering, and regression matrix are in
`evidence/research-2026-09-01/README.md`.

## Approved direction — 2026-09-02

Approve the distinct public pre-attach abandonment fence described above. It
must reuse the durable abandonment intent and exact `AuthorityPort.cancel`
crossing, atomically establish a no-start state before fencing, and require the
recorded exact fence before recovery may report `resolved`. A runtime start
that wins first makes this branch refuse and forces fresh recovery observation.

Do not weaken attached abandonment, ordinary cancellation, or W61984's
terminal-disposition finalizer. This operation makes no output, custody,
retention, review or integration decision.

Implementation remains an isolated v12 assignment; this approval does not
route the Work to the legacy v11 implementer.
