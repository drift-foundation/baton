# Target-driven line rework — proposed contract revision 1

Status: proposed under reviewer claim131466; lifecycle direction approved by
owner event131446. This file plus SCOPE-v1.md is the concrete implementation
proposal, not permission to edit product files. No runtime spent drafting it.

## 1. Identity and accepted behavior

One Authority/Work keeps one line_id, nominated source identity, private checkout
identity and immutable creation declared_base. Advancing the Authority target
does not alter those creation operands. An effective round base is separate,
owned by a committed target-rework record. A replay of original create_line
still recovers the same line; a new caller supplying different creation operands
still refuses. Historical checkpoint evidence, verdicts, publications and refs
are immutable and independently auditable.

For two nonconflicting Jobs started on one base, A may finish first. B's old
candidate remains stale. Ordinary configured ticks prepare B's changes atop A's
actual target revision on B's same line, give B a fresh producer round and
independent review/required tests, then integrate B through the existing owners.
The final content must contain both Jobs' intended changes. No old acceptance,
test receipt, approval or proposal authorizes newly prepared bytes.

Conflict, missing content, uncertainty or ownership mismatch answers a durable
hold with its reason. It never discards B's immutable candidate, treats a target
digest as available content, silently substitutes another Work, or weakens any
publication/admission/Authority stale-target guard.

## 2. Closed public records

New worker owner module: baton_v12.worker_manager.target_rework. Proposed public
operations: prepare_rework, rework_of, effective_base, seal_unstarted,
settle_unstarted and settlement_of.
New Job owner module: baton_v12.job_manager.target_rework, with advance_rework
and rework_round_of. Exact signatures may use keyword-only injected owners, but
the following identity and outcome fields are required, not optional metadata.

The proposed selector signatures are:

- seal_unstarted(control, *, attempt_id): derive and seal the owner's exact
  fixed assignment; refuse unresolved ownership/start state.
- settle_unstarted(control, session, *, seal_id, to_route): consume that seal,
  perform/replay the exact bound Authority pass, return its typed settlement.
- settlement_of(control, settlement_id): read and cross-bind that record.
- prepare_rework(control, authority, *, line_id, checkpoint_id, target_id,
  target_source, profile, settlement_id): resolve target revision/receipt through
  Authority, prove selected settlement and prepare the exact current checkpoint.
- rework_of(control, operation_id) and effective_base(control, line_id):
  pure typed reads, with no lazy preparation.
- advance_rework(jobs, control, *, job_id, rework_id) and
  rework_round_of(jobs, operation_id): consume/read the exact custody outcome.

An initially unclaimed integration follows ordinary admission/claim first,
while launch is gated on the rework check. v1 does not invent an unclaimed
Authority handoff or accept an arbitrary null settlement_id. The round driver
composes these public acts and retains its intent before the first cross-owner
mutation. Mutable revision selection is frozen into that intent for retries.

A custody record uses schema baton.v12.target-rework/1:

- operation_id, authority_uuid, work_id, line_id;
- old_checkpoint_id, old_checkpoint_digest, old_base;
- target_id, target_revision, target_receipt_id, target_proposal_id;
- target_source: nominated path, device and inode, plus verified commit/tree;
- profile_name, line_object: path/device/inode;
- state: preparing, ready or held; reason is null only when ready;
- prepared: null until ready, then base/head/tree/reference/path-set evidence;
- superseded_eligibility: exact old checkpoint/verdict identities, retained;
- integration_settlement: selected old stage/episode/attempt/allocation and
  fixed assignment, launch-exclusion record, Authority handoff operation and
  exact returned account.

Operation identity derives from Authority/Work/line, old immutable checkpoint
digest and intended target revision; the complete signature also binds every
other fixed operand. Conflicting signature under that identity refuses. A
committed ready/held record replays before checking facts which it already
changed; replay must not transplant twice, create another round or release a
different allocation. Public readers cross-bind materialized records against
their own committed journal operations and refuse tampering.

A Job round uses schema baton.v12.target-rework-round/1:

- operation_id, job_id, authority_uuid, work_id, custody_operation_id;
- old_checkpoint_id, target_revision;
- exact ended implementation/review/integration episode and attempt identities;
- exact successor episode/offer/attempt identities for all three stages;
- settled integration allocation identity/reason, and recorded_at.

It references custody evidence through the typed owner reader, not a caller's
unverified copy. It must not reuse the changes-requested verdict schema.

## 3. Storage and compatibility

Propose ControlStore schema19 using its existing fresh-store boundary: refuse
schema18 rather than migrating or resetting an existing store. This is an
explicit deployment boundary for approval. Tests/reproductions use freshly
initialized stores; no live store upgrade or source checkout Git action.

Add target_reworks and exact attempt launch-seal records to the worker-owned
schema, with unique operation identities and one pending rework per line.
review_lines retains declared_base and adds nullable current_rework_id;
line state additionally permits reworking, rework-ready and rework-held.
Writer grants capture the effective base and rework identity they were granted
under so a later line transition cannot silently change a writer's base.
Original lines without rework keep their current behavior.

effective_base returns creation declared_base before any rework, and the target
revision of the validated current ready record afterward. Preparing/held does
not authorize a writer or a checkpoint. No historical checkpoint base is changed.
Current integration_eligibility is retired only with a journalled rework intent
which preserves its old identity; old accepted verdict remains historical fact.

The Job owner's existing operation journal stores the new round and stage
endings. Add a distinct target-rework ending/document vocabulary, not generic
completed and not a forged ordinary review correction. No Job schema migration
is proposed; if an additional structural change proves necessary, return the
exact gap before editing outside SCOPE-v1.md.

## 4. Safe old-integration settlement

The first automatic slice supports a stale integration which has not crossed
the runtime launch-intent boundary. This covers the retained two-Job witness:
B acquires capacity/claim while no B integration runtime port has launched.
It is an explicitly proposed bound, not a claim that every runtime is stoppable.

seal_unstarted is a durable worker-owner operation, keyed to the exact integration
attempt and fixed assignment. It atomically excludes an existing launch intent
and prevents future activation/start under that attempt. The competing launch
path checks this seal under the same transaction that commits launch intent.
If launch wins, sealing refuses/holds; if sealing wins, no adapter start may
follow. A null runtime_id or an in-memory observation alone is not absence proof.
Unresolved claim/settlement operations must first be reconciled through their
existing owners; do not interpret an unknown remote result as unclaimed.

Once sealed, an already claimed integration is passed through the exact bound
Authority session using pass_work to the configured implementation route,
stable operation_id and exact assignment expectation. Retain/re-read that
canonical account before releasing logical scheduler capacity. This is a
target-rework handoff, never an integration-completed account, and creates no
integration receipt or cleanup claim. An unclaimed stage goes through ordinary
claim before this act; another live assignment refuses.
Route/generation drift or mismatched replay stops before capacity release.

For a launch intent, attached/running/uncertain runtime, live integration lease,
or unresolved target mutation, v1 holds and does not automatically replace it.
Existing canonical cancellation/exclusion/cleanup may resolve that case under
their own authority; v1 does not fabricate an ordinary worker result, repurpose
operator-only abandonment, clear a quiescence gate, or invent resource cleanup.
An already integrated attempt is historical completion and never reworked.

This bounded prelaunch settlement policy requires explicit approval with the
contract. General started-integrator recovery is not secretly included in the
three slices or silently counted as accepted.

## 5. Target content and profile act

The configured factory accepts a read-only nominated target-content capability
per bound canonical target_id. It returns a stable content source; it does not
write the target or mint new credentials. Validate capability shape and target
keys before durable setup. Absence preserves existing no-rework behavior until
drift, where it produces a specific capability hold. No global source fallback.

Preparation binds the target revision to the Authority's actual integrated
receipt/proposal and rechecks current target through the owner. Verify the
nominated repository really contains that exact commit/tree. The immutable
object may be exported/read without treating a mutable pathname as its identity.
A later target advance is still subject to all existing stale-target refusals.

Extend GitCheckpointProfile with a bounded prepare_rework/validate_rework
capability. Validate the old retained checkpoint before writes. Hold the line
directory as an object for every command, following existing restore custody.
Transplant the old checkpoint's net changes relative to its old effective base
onto the new target content, rather than merely detaching at target. Retain the
prepared result under a distinct rework ref; never move old checkpoint refs.
The profile may use private scratch under nominated storage to calculate the
result; scratch is not a second authoritative line or Work.

Only a proved clean transplant publishes ready prepared evidence. Conflicts
hold without deleting old refs/candidate or reporting success. Retain sufficient
conflict evidence for an explicit later decision; automatic conflict resolution
is outside v1. No command ever names the human repository's index/branch for
mutation. Product profile tests use their own nominated disposable repositories.

Intent commits before filesystem work. Recovery validates/reuses an already
prepared ref instead of applying the delta again; if preparation is ambiguous
or tampered, hold. A ready outcome commits only after rechecking the exact line,
checkpoint, seal/settlement and profile result. New writer admission validates
prepared evidence and rework identity instead of pretending current HEAD still
equals the old checkpoint. Freeze creates a NEW checkpoint under the effective
base, with fresh writer assignment/fence and ordinary new revision number.

## 6. New round and ordinary composition

advance_rework proves current custody ready, exact Job/Work/stages and the
settled old integration before moving any Job row. It guards the full triple
under the Job transaction, ends all old episodes and opens all successors
atomically. Keep old receipts/history on old attempts; do not transplant them.
The integration successor waits behind fresh implementation and fresh review.
Reconciliation releases only the exact retired integration allocation using
existing release and a distinct target-rework reason after typed settlement.

The manager drives an optional rework action before ordinary admission and
again before launch, then rederives projection. An unclaimed stale stage may
admit/claim ordinarily but must not launch before the post-claim rework check.
Stage observation/status remains read-only.
Admission/launch using a previously read old attempt must recheck its episode
and seal; do not let a stale sweep create a replacement race. Retried custody
success with no Job round yet completes that same round. Retried round returns
its recorded successors, even if their mutable states have since advanced.

The assembly derives a fresh per-Job task/input/manifest with effective base,
preserving original user intent, declared policy, source/Work and worker profile.
It never mutates a retained task/result/checkpoint. New publication and integration
port select the new checkpoint/proposal/target. Historical publication lookup
uses the public committed publication owner, not renewed retain_proposal against
today's target. This lookup correction does not waive current eligibility.

Original /1 and no-drift /2 behavior stays on the existing path. Read-only
observation, foreign handles and replay cannot prepare content or open rounds.
No new coordinator authority over Git history, Authority policy, runtime
cleanup, integration target leases or principal-capacity separation.

## 7. Required evidence, not a test-count gate

Provider: clean nonconflicting transplant preserves both changes; real conflict
holds; old refs/audit and create/recover survive; missing/tampered/foreign
checkpoint, target object, Work, profile, source or line object refuses before
publication. Replaying after filesystem/custody cutpoints is idempotent.

Settlement/round: exact prelaunch claim handoff and release; initially unclaimed
stage reaches that case through ordinary claim without premature launch;
seal-versus-start race in both orders; unknown claim stays held; already-started,
uncertain/live lease cases hold; changed route/generation refuses. Foreign
custody record and half-round race refuse atomically. Crash after remote pass,
after custody ready and after Job round each recovers through public readers.

Consumer: real A terminal completion advances target, stale B remains refused,
same B line acquires new effective base with both changes, new producer/task/
checkpoint, fresh independent review and required tests, then B real terminal
handoff through ordinary ticks. Retain all Job/attempt/allocation/assignment/
checkpoint/proposal/target/entry/receipt identities. No manual transitions or
synthetic lifecycle answers. Required /1, conflict and second-target-race controls
remain. W130224 and W119405 retain their separate acceptance obligations.
