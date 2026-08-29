# Compose post-create start failure into manager-owned cleanup

## Discovery and parent

Discovered during W32382 correction re-review under
`work/records/2026/08/finding-v12-local-oci-negative-race-endings/`.

## Confirmed gap

`attempts.request_runtime_start` now reconciles a start call that faults after
the engine created a container and attaches the exact runtime. That closes the
identity leak but does not create an authorized cleanup ending. Intake requires
a frozen result and receipt, while output freeze requires a terminal
`worker_disposition` already proved on the attempt.

The current real-engine regression works around that gap by calling
`observe(... worker_disposition="unable")`, manufacturing declared output,
freezing it, and taking intake. This is not a production composition from the
transport fault. `output.py` explicitly says the handled turn outcome gates
worker disposition and that a proof the caller can write is not proof. A
container created before a transport failure may also have run code, so the
manager cannot infer that the worker was `unable`.

## Required boundary

- Define one manager-owned post-create failure record distinct from worker
  disposition and preserve the original typed adapter/transport fault.
- Reconcile and attach any exact created runtime without inventing what the
  worker did or whether output is valid.
- Order authority fencing/ending before destruction. Define the applicable
  custody rule for potentially written workspace/output when no trustworthy
  worker envelope/disposition exists; fail closed or quarantine rather than
  synthesize a successful result.
- Reuse exact runtime removal, positive absence, credential/launch teardown,
  and retryable cleanup owners. Duplicate no provider internals.
- Bind retry to exact attempt, assignment, start operation, attached runtime
  and failure identity; changed facts collide and sibling state is untouched.

## Acceptance

- A real Docker `run` creates one container and the engine call then faults.
- No test or production caller writes a worker disposition or fabricated
  output to authorize cleanup.
- The manager durably records the start failure, attaches the exact runtime,
  starts no duplicate on retry, applies the ruled custody policy, force-removes
  the exact container, observes absence and settles delivery roots.
- Restart between creation, reconciliation, custody, removal, absence and
  provider settlement converges effectively once.
- Unknown identity, multiple candidates, uncertain observation, custody
  failure and sibling attempts fail closed.

## 2026-08-28 — reviewer revalidation of the proposed custody rule

**Observed:** the existing intake quarantine is reachable only after a normal
output freeze. `request_intake` calls `_collectable`, which requires
`attempt.output == frozen` plus a persisted frozen result. `record_intake`
then compares every collected artifact against that frozen result before
`_seal` may choose `custody=quarantined` because the assignment ended or
changed.

**Confirmed:** this existing rule cannot authorize the no-envelope ending.
The post-create fault has no trustworthy worker disposition, cannot request a
freeze, and has no frozen result or declared artifact set for intake to
compare. Reusing current `record_intake` would require manufacturing exactly
the evidence this Work forbids.

**Proposed:** quarantine is the safer product direction because it preserves
potentially written evidence without presenting it as a valid result. It must
be a new explicit no-envelope custody path, with identity derived from the
exact attempt, assignment, start operation, attached runtime, and typed
failure. Its material can never become accepted result custody, and cleanup
must end retained until the quarantine's own custody and retention facts are
positive.

**Open — approver ruling required:** choose whether the manager may create
that explicit no-envelope quarantine record, or must instead remain blocked
with potentially written material retained for operator disposition. The
existing `quarantined` value does not itself decide that extension.

## 2026-08-28 — approver custody ruling

**Confirmed by approver response M33800:** the existing unique result
directory for one assignment generation and one attempt is the custody
boundary. It begins untrusted and remains untrusted after a start fault, crash,
timeout, forced stop, unknown ending, or missing trustworthy result envelope.

**Superseded proposal:** the explicit copied no-envelope quarantine record
proposed above is not authorized. Preserve that text as decision history, but
do not create a second result or copy, invent a worker disposition, or admit
any untrusted contents to the proposal pipeline.

**Required ending:** fence the exact attempt before destructive cleanup, remove
the exact attached container, positively observe its absence, and settle the
existing delivery roots without deleting the result directory. Retain that
directory for optional human inspection until later explicit retention cleanup
owns its deletion.

**Trust boundary:** a clean container exit is necessary before result trust is
even possible. Trust then still requires the normal trustworthy result
envelope and artifact validation; clean exit alone never admits output.

## 2026-08-28 — independent review of the failed-start journal unit

**Confirmed useful boundary:** refusals retain their closed category/code pair,
ordinary faults remain faults, reconciliation precedes the record, and neither
path writes worker disposition or advances output. The journal is a suitable
durable owner for this manager-authored fact.

**Observed [P0]: changed failure facts do not collide.**
`_start_failure_operation_id` derives the operation id from the attached
runtime and the entire typed failure. A different failure or runtime therefore
selects a different operation row before `store.transact` can compare its
signature. The submitted
`test_a_different_failure_is_its_own_act_and_rewrites_nothing` explicitly
expects two rows and two operation ids. That is the opposite of this finding's
required boundary: retry is bound to the one exact attempt/assignment/start
operation and changed runtime or failure facts collide.

**Confirmed correction boundary:** the journal operation identity must be
stable for the one start act — derived from the attempt and its fixed start
operation — while the signature/result carries attached runtime, settled axis,
and typed failure. An exact repetition then replays; a changed runtime,
failure, assignment, or settled state reaches the same operation identity with
a different signature and fails closed as a collision. The existing
two-record test must be corrected to assert that collision and preservation of
the first durable record.

The ruled cleanup crossing remains wholly open: this review neither authorizes
cleanup from the partial record nor changes the approver's retained-untrusted
result-directory decision.

## 2026-08-28 — provider contract split

**Confirmed by approver messages M34998/M34999:** W34998 separately owns the
explicit no-envelope failed-start destroy command and adapter crossing. It
preserves the receipt-authorized destroy command unchanged and never puts the
failed-start record digest in `intake_receipt_digest`. This Work remains the
consumer: after W34998 closes satisfying, W32648 composes the exact journal
record, fence-before-destroy ordering, operation replay/collision, provider
settlement, retained untrusted result directory and cleanup-axis ending.

## 2026-08-29 — the ruled ending, implemented

**Revalidated before acting.** W34998 is closed satisfying, so the sibling
command and adapter capability exist and this Work consumes them rather than
redefining them. `_start_failure_operation_id` is already corrected to the one
stable identity the [P0] required, and its case asserts the collision.

**The ending.** `authorize_failed_start_cleanup` is the sibling of
`authorize_cleanup`, and it is a sibling for the same reason W34998's command
is one: what authorizes it is the manager's own durable `runtime.start-failed`
record, read back from the journal it was written to, never an intake receipt.
`failed_start_destroy_operation` carries that digest in the identity exactly as
the receipt's does on the other path.

**The order is the ruling's, and each part is measured by removal.** Fence at
the AUTHORITY -- asked of it rather than inferred from an axis -- then remove
the exact attached runtime through W34998's capability, positively observe
absence, settle the delivery roots on that absence and nothing else, and end at
`retained`.

**`retained` unconditionally, and not by counting.** `_settle` chooses between
`complete` and `retained` from what retention kept. There is nothing to count
here -- no intake happened and no artifact was decided -- and M33800 makes the
untrusted result directory itself the material that stays. Reporting it as
`complete` would erase the reason the directory still exists.

**Nothing is fabricated.** No worker disposition is written, no output is
frozen, no second result is created, no byte is admitted to the proposal
pipeline, and the result directory is left exactly where it is. Cases prove
each of those rather than the code asserting them.

## 2026-08-29 — independent review of the composed ending

**Observed [P0]: the failed-start record is not bound back to the runtime being
destroyed.** `_failed_start_record` derives the journal operation id and accepts
any committed non-null result at that id. It does not prove the row is a
`runtime.start-failed` operation or that the retained result names the current
attempt's fixed assignment, start operation, attached runtime and settled
execution axis. `authorize_failed_start_cleanup` then combines the digest of
that old result with `attempt["runtime_id"]` from a separate adopted row.

The additive regression
`test_the_record_must_name_the_runtime_being_destroyed` records a failed start
for `runtime-1`, changes only the persisted attempt's runtime identity to
`runtime-sibling`, and asks for cleanup. The current implementation does not
refuse: it crosses the adapter with the old authorization digest and the new
target identity. This violates the exact-runtime authorization boundary and
can direct destructive cleanup at a runtime the cited failed-start record does
not name.

**Confirmed correction boundary:** before the adapter is called, adopt and
verify the committed journal row as `runtime.start-failed` and prove its exact
result agrees with the current attempt, fixed assignment, start operation,
attached runtime and settled execution state. A mismatch is durable integrity
failure, not a new authorization. Preserve the journal result as the source of
the failure identity and digest rather than recomposing it.

**Observed [P1]: the required real-engine composition is still the old
workaround.** `NegativeEndings.test_a_post_create_failure_leaves_no_duplicate_and_no_container`
still writes `worker_disposition="unable"`, freezes fabricated output, takes
intake, decides retention and calls receipt-authorized `authorize_cleanup`.
Its own comment says that sequence does not prove the W32648 ending. The only
new manager composition cases use a fake custodian; W34998's Docker suite proves
the provider command independently, not the manager-to-provider composition.

**Required proof:** the real Docker create-then-fault case must proceed from the
durable failed-start record directly through `authorize_failed_start_cleanup`,
with no worker disposition, frozen result or intake receipt, and must prove the
exact container absent, delivery roots settled and the existing result
directory retained untrusted.

## 2026-08-29 — independent re-review: corrections satisfy the boundary

**Resolved [P0].** `_failed_start_record` now verifies the journal row kind,
decodes the committed result through the journal reader, owns its closed shape,
and compares its attempt, fixed assignment, start operation and runtime
identity with the exact current attempt before the adapter can be called. The
reviewer's changed-runtime regression and the added wrong-kind regression both
pass and prove no destroy capability is crossed on disagreement.

The retained `execution_runtime` value is deliberately not required to equal
the current axis: it records the state at failure settlement, while later exact
observation may legitimately move the same attached runtime from running to
quiescent before cleanup. Current uncertainty and missing identity still
refuse directly. That distinction preserves the record's historical fact
without turning truthful later observation into a cleanup blocker.

**Resolved [P1].** The real Docker post-create-fault regression now reaches
`authorize_failed_start_cleanup` from the manager-owned journal record. It no
longer writes a worker disposition, freezes output, takes intake or decides
retention. The case proves one created runtime, no replacement, retained
cleanup, destroyed execution runtime, no intake row, exact daemon absence,
launch teardown and survival of the untrusted result-directory sentinel.

**Verification:** the independent daemon-free run passed all 228 attempt tests
and 21 dependency tests with one established skip. The managed reviewer could
not open `/var/run/docker.sock` and therefore did not independently execute the
required daemon case; the retained serial transcript records all four Docker
negative-ending cases passing and the source was reviewed against the exact
composition. Scoped diff checking is clean.
