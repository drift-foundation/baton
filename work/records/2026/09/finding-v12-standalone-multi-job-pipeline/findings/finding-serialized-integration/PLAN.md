# Plan

1. [review-ahead complete 2026-09-04] Review the scheduler-owned target queue
   against current Authority proposal/verification/review/approval/integration
   receipts, the accepted Job Manager stage boundary, W62098's Git lineage,
   the settled `baton.merge` contract, and W71459's test-change/mode policy.
   Record the ownership, identity, eligibility, ordering, fencing, refusal,
   crash and evidence requirements. This approves the contract and plan only;
   it creates or approves no implementation bytes.
2. [targeted review complete 2026-09-05] Revalidate the reviewed
   contract against the accepted persistent checkpoint and correction-line
   implementation. A material mismatch in checkpoint identity, verdict binding,
   immutable custody, path-set evidence, or integration eligibility returns the
   affected contract for targeted review before production edits.

   The gate ran against W71918 as committed at `b37446a`. No axis mismatches;
   verdict binding, immutable custody and path-set evidence are stronger than
   this record assumed, and the retained checkpoint ref is the concrete durable
   object transport. Targeted review confirmed TWO eligibility surfaces whose
   corresponding operands must be cross-bound while their differently defined
   aggregate digests remain distinct; corrected the claim that an accepted
   checkpoint can be revoked by ordinary W71918 line advancement; and confirmed
   that target identity is never derived from line identity. No production byte
   was written. FINDING.md records the binding and refusal semantics, while
   PROGRESS.md preserves the implementation gate's original evidence.
3. [bounded implementation accepted 2026-09-06 after the eighth correction;
   both P1 boundaries of the seventh correction's review passed independent
   re-review. W71878 returned to baton.ops under the owner disposition. The
   later W101714 producer-account correction received bounded independent
   sign-off in `review-2026-09-06T13-37-51Z.md`]
   Introduce a stable canonical-target identity
   separate from the mutable expected/current revision. Define immutable,
   Authority-namespaced queue entries, transactionally allocated enqueue rank,
   one-live-lease-per-target uniqueness, monotonic lease fencing and explicit
   terminal/recovery states. Ensure all Authorities permitted to address one
   checkout share its lock, while distinct targets do not serialize each
   other. Obtain the key from trusted target configuration; never derive it
   from the Authority/Work-scoped development-line identity.
   Keep this coordinator and its persisted contract VCS-neutral. Replace the
   current Git-shaped `base_object`, `head_object`, `tree_object`,
   `transport_ref`, and `checkout` vocabulary with a generic candidate/artifact,
   target-revision and scope boundary plus a generic runtime-profile identity.
   Git-specific instructions and evidence remain generic input/output artifacts
   interpreted by the model, not a coordinator-owned or required adapter
   document.
3a. [owner ruling complete 2026-09-05] Use a target-global integration
   coordinator/store independent of every Authority-bound Job store. It owns
   target identity, global ordering and the unique live target lease while
   entries retain their Authority namespace and evidence. The alternative
   single-Authority-per-target deployment restriction is rejected.
3b. [pending implementation] Keep Worker Manager `AuthorityPort` unchanged and
   specify a separate closed integration boundary with fixed integrator actor,
   Authority and target bindings. Treat one composite profile as deployment
   wiring, not transaction atomicity. Make its scheduler-owned live-lease check
   and its durable preflight/import/verification/Authority-completion recovery
   cutpoints explicit; a repeated lease/fence value alone is not a capability.
4. [pending implementation] Admit an entry only from one exact final checkpoint
   whose W71918 custody eligibility and Authority proposal/verification/review/
   approval eligibility both validate and whose corresponding Authority, Work,
   assignment, candidate/artifact, target-revision and path/scope operands
   describe one candidate. Re-resolve every member of the FIFTEEN-member
   account from its named accepted producer -- the attempt's assignment;
   W71918's checkpoint verdict and the `profile` member of its evidence, which
   the account copies as `profile_kind`; Authority's `publish` operation and
   `proposal` row; and the accepted Job's `test_scope` -- and never from a
   caller operand. Retain each surface's exact identities and differently
   defined digests; do not equate `checkpoint_digest` with `candidate_digest`
   or `result_digest`. Exact replay returns the same rank; stale checkpoint,
   changed operands, incomplete authority or mismatched scope refuses before
   enqueue.
5. [pending implementation] Compose the live lease with the sole trusted
   target-integration runtime. Revalidate both eligibility surfaces and target
   revision. Before mutation, an ordinary policy/scope/target failure
   terminally refuses that immutable entry; an integrity/digest/ambiguous-custody
   failure retains the fenced target for repair. For the Baton repository, the
   model receives Git-specific Work instructions and ordinary Git tools, then
   performs `baton.merge`'s whole-path provenance/authority/type/base/mode/
   overlap preflight, imports only reviewed bytes without custody modes, and
   runs bounded final-byte/mode and Work verification. Other Work may carry
   non-Git instructions through the same profile contract. The coordinator and
   generic managers neither name nor interpret Git operands; a deterministic
   VCS adapter is optional future deployment machinery, not a v12 requirement.
6. [pending implementation; manual recovery scope ruled 2026-09-06] Record the
   Authority integration receipt and target-revision advance only after an
   uninterrupted real import and verification. Make direct integration without
   the live lease/fence impossible. Persist enough evidence to detect and
   explain interruption or inconsistent target/account state, then hold the
   target for an explicit operator decision. Do not automatically retry,
   complete, accept, clean up, release or reassign interrupted integration.
7. [pending verification] Prove same-target FIFO/rank and two-ready races,
   independent-target concurrency, stable locking across target revisions and
   any shared-target Authorities, enqueue/lease replay collisions, stale fence
   refusal, prior-holder recovery, cross-surface operand/digest mismatch, an
   accepted line's refusal to advance, moved target, missing Git objects,
   stale/mismatched review or approval, old correction checkpoint, path-scope
   mismatch, overlap/conflict, symlink/non-regular/read-only/base-drifted target,
   crash before/during/after import and Authority completion producing an
   inspectable operator-held condition, one scheduled
   existing-test change, and one out-of-scope test refusal. Assert every
   negative case mutates neither target bytes/modes nor Authority target state.
8. [pending integration verification] Run the complete Authority, Job Manager,
   integration-policy and provider checkpoint suites plus focused real Git/
   working-tree restart and race gates. Verify schema/document regeneration if
   touched, full v12 Python tests, and `git diff --check`.
9. [pending independent implementation review] Bind the exact proposal digest,
   base, production paths, and every changed existing test path. Evaluate all
   assertion/expected-behaviour changes under the scheduled scope and approve
   only the presented bytes and their retained verification evidence.

Contract review runs ahead of component completion. Before handoff to
implementation, restore the component dependency that supplies accepted
checkpoints and correction lines, allowing that gate to release the review
claim, then reroute the blocked Work to implementation. Implementation remains
blocked until that provider is accepted.

The seam decision's two implementer-level defects are corrected in FINDING.md:
colocation on one capability is a wiring unit and not atomicity across the
scheduler store, the target filesystem and the Authority store, so the durable
cutpoints and their reconciliation stand; and a lease id with a fence is a
replayable value rather than a live grant, so the target store's owner
re-evaluates the live grant before canonical mutation and again before
Authority completion, with uncertain work preventing release. `AuthorityPort`
is unchanged and the integration Session is separate, narrow and
document-validating.

Item 3 proceeds under the recorded owner ruling: a target-global coordinator
independent of every Authority-bound `JobStore` owns the shared target lock.
An Authority-local integration lock and a single-Authority-per-target
deployment restriction are not accepted substitutes.

Item 3 is implemented as `baton_v12.integration` -- `schema.py`, `store.py`
and `queue.py` -- with `tests/integration/test_coordinator.py` and one
`tools/parallel_test.py` registry entry. The coordinator store carries no
Authority binding, target identity is configuration's and is never derived,
rank is allocated in the enqueue transaction, one live lease per target is
decided by a partial unique index, the fence increases in the granting
transaction, and `live_grant` is proved before canonical mutation and again
before Authority completion. `refuse_entry` demands that grant and
`block_target` deliberately does not, which is what keeps a crashed holder's
target recoverable through `abandon_lease`. PROGRESS.md records the four
defects corrected during implementation and the baseline-failure measurement.

Item 3 returns to implementation before 3b. Normal lease release must refuse
unless the exact entry is terminal/reconciled; it cannot leave an unresolved
entry behind and advance the queue. Blocking and abandonment must persist and
cross-check one exact target/entry/lease/fence/account relationship, including
explicit semantics for any permitted block without a live lease. Persisted
target, entry and lease reads must validate complete document shape and every
redundant identity/digest/relationship. Store adoption must validate the full
owned schema, including the partial live-lease index and predicate. Authority
namespace identity must use the repository UUID predicate at admission and
read boundaries. Add negative regressions for premature release, cross-entry
blocking/abandonment and replay, split evidence, malformed Authority identity,
and schema/index corruption; every rejected transition must leave state
unchanged. `review-2026-09-06T02-15-48Z.md` is the binding correction review.

Item 3 does NOT cover the integration boundary, the Git-aware profile, real
import, the Authority receipt or restart reconciliation; those remain 3b and
5-6. This package's receiving entries have no boundary inventory, because
`test_boundary_inventory` walks `worker_manager` alone. Item 7 must add either
a dedicated integration receiving-boundary inventory or equivalent exhaustive
focused coverage for owned schema, documents, redundant relationships, and
identity members.

All five findings of `review-2026-09-06T02-15-48Z.md` are corrected. An
ordinary release ends only a lease whose entry is `integrated` and whose
ending agrees; the refusal ending is fused into the transaction that refuses
the entry, so no public ending leaves an unresolved entry behind a dead lease.
The one exception is named rather than hidden: `abandon_lease` ends a lease
over a `held` entry, and what makes that safe is the TARGET's state -- it is
reachable only on a blocked target, which offers nothing to anybody.
`block_target` takes the whole live grant as operands, refuses unless exactly
that grant is live, persists it as `targets.blocked_account`, and refuses a
second block; `abandon_lease` cross-checks that account rather than
re-deriving one. A block with no live lease is REFUSED rather than defined,
because item 3 has no unreconcilable account without an import. The duplicated
eligibility document is REMOVED rather than cross-validated -- the account is
assembled from the columns that are it -- while target, lease and settlement
reads now prove every redundancy that genuinely remains. Adoption compares the
complete owned schema, including the partial live-lease index and its
predicate, against an expectation measured by running `SCHEMA` itself.
`authority_uuid` uses the Authority package's own predicate at admission and
at every persisted read.

The item 7 coverage obligation is discharged for this slice by the second of
the review's two options -- exhaustive focused cases for the owned schema,
documents, redundant relationships and identity members -- rather than by
extending `test_boundary_inventory`, whose static walk is another record's
over `worker_manager`. Extending that universe remains a coordination question
between the two records if a dedicated inventory is wanted instead.

Item 3 returns again before 3b for the persisted-account and ownership
corrections in `review-2026-09-06T02-39-45Z.md`. `target_of` must cross-bind a
blocked account to its target reason, held entry/settlement, and named
lease/fence/integrator/attempt, allowing only the defined live or properly
abandoned recovery state. Entry settlements and lease endings must be closed,
state-specific, member-typed variants; an abandoned lease cannot carry an
integrated ending. `settle_integrated` and `refuse_entry` must retain and use
the fresh snapshot returned by `boundaries.document` instead of validating it
and later signing/persisting the caller's mutable original. Audit the other
item-3 document operands and add relationship-corruption, wrong-variant/type,
and deterministic post-validation mutation regressions.

Every finding of the re-review is corrected. `target_of` adopts the blocked
account as ONE relationship -- reason against the row, entry present on this
target and `held` with a matching settlement, lease present and agreeing on
entry, fence, integrator and attempt, and live or properly abandoned with a
recovery for that same attempt. Settlements and lease endings are owned as
closed state-specific variants rather than member sets: imported paths are a
collection of durable text, a verification is a document whose members remain
item 5's to name, refusal and held reasons are text, and
`boundaries.alternative` discriminates the three endings so a released lease
cannot end abandoned and an abandoned one cannot end integrated. Every public
document operand now binds the owned snapshot `boundaries` returns, and the
audit covering all seven is recorded in the module docstring.

Both reviews found the same underlying shape, which 3b should carry forward:
the write transition was correct and the READ, the retry or the restart
trusted what the write had left behind. The store is a receiving domain on the
way out as much as on the way in.

Item 3 returns again before 3b for the complete state-graph correction in
`review-2026-09-06T02-53-42Z.md`. Public target and lease reads, and lease
selection itself, must reject an open target that still has a held entry or an
abandoned lease from a block. An abandoned lease must cross-check the target's
still-present exact blocked account rather than validate only its own ending.
Centralize raw-row adoption and one relationship pass if needed to avoid
recursive partial checks. Add erased-block and fabricated-state regressions at
the `target_of`, `lease_of`, and `grant_lease` doors and prove refusal changes
no target, entry, lease, fence, or queued rank.

The third review's [P0] is corrected. Every public read of the coordinator
store goes through ONE relationship pass: `_relationship` adopts the target,
all its entries and all its leases together and `_prove` checks the whole
graph before anything is returned, so `target_of`, `entries_of`, `lease_of`
and `_entry` are projections of one opinion rather than four readers with
four. `grant_lease` reaches it before selection. The pass is not recursive --
raw rows are adopted in one place and no invariant calls a public reader.

The invariant the finding was about: an open target has no held entry and no
abandonment, because held work exists only where an import could not be
reconciled and an abandonment exists only where a block was recovered. Also
proved: every lease's entry is this target's, at most one live lease, a live
lease is over `leased`/`integrated`/`held` work, and a `leased` entry has a
live lease holding it.

ITEM 3 DEFINES NO REPAIR, and this is now a constraint on 3b and item 6: any
operation that reopens a blocked target must reconcile the held entry and the
recovery account in the SAME transaction that reopens it, or the invariant
above is false the moment it runs.

Known property, recorded rather than optimized away: every public read now
adopts and proves a target's whole graph, which is O(queue) per call and
happens inside `grant_lease`'s write transaction. Making it cheaper means a
narrower pass with an explicit argument for what it may skip, not a return to
per-reader opinions.

Item 3 returns again before 3b for the full lifecycle matrix in
`review-2026-09-06T03-06-14Z.md`. `_prove` must bind queued, leased,
integrated, refused, and held entries to the exact absence or single lease
history and ending each state permits, and bind target fence to the greatest
granted fence. No queued entry may carry an ended lease and no entry may
acquire a second lease in item 3. Add table-driven same-target corruption
cases through every read and selection door, including an integrated/released
entry reset to queued, and prove refusal changes nothing.

The fourth review's [P0] is corrected. `_prove_entry` states every entry's
whole lifecycle against every lease it has ever had: `queued` has no lease at
all, `leased` exactly one live one, `integrated` exactly one -- live between
the two cutpoints or released with the `integrated` ending -- `refused` either
none or exactly the released lease its refusal fused, and `held` exactly the
lease the blocked account names, live before the recovery or abandoned after.
The target's fence is the greatest it has ever granted. No entry returns to
`queued` and no entry acquires a second lease; a later repair or retry design
that needs either must introduce its own reviewed state and account rather
than weakening these.

`_agrees_with_the_journal` closes the one case the state graph cannot see: an
entry refused before any grant carries no lease, so the journal's record of
the act that settled it is the only surviving residue. It binds recorded
decisions to present state in ONE direction; the converse is false for the
duration of an act, because `transact` writes its row after the action
returns. It does not catch a deleted row, which is recorded as a known gap.

Both composite operation identities now digest their pair rather than joining
ids with ":", which does not compose uniquely when an id may contain one.

Item 3 returns again before 3b for the two-way durable-history correction in
`review-2026-09-06T03-22-15Z.md`. The relationship pass must adopt committed
activation, enqueue and grant evidence as well as materialized rows, and prove
the mapping in both directions. Every entry must match its originating target,
rank and complete immutable eligibility account; every lease must match its
originating target, entry, holder, attempt and fence; missing rows and fence
reuse must refuse when the journal retains their committed acts. The exact
internal interval before `transact` inserts the operation row may be handled as
a narrowly identified pending act or removed from public projection, but it is
not an external missing-journal state. Add corruption/replay cases for rewritten
entry accounts, deleted entries and leases, duplicate candidate admission and
fence reuse, with refusal leaving rows and journal untouched.

The fifth review's two [P0]s are corrected. The durable JOURNAL is now the
history the materialized rows are proved against, in both directions: every
committed activation, enqueue and grant relevant to a target has its row and
that row still matches what the act recorded (the target's identity, document,
digest and adoption instant; the entry's target, id, rank, enqueue instant and
all seventeen operands; the lease's target, entry, holder, attempt, fence and
grant instant), and every row has the act that made it -- against THIS target's
acts rather than the journal at large. The fence is the greatest in durable
history rather than the greatest surviving lease row. Journal rows are adopted
like any other persisted input, with a closed per-kind operand contract and a
refusal for a kind this build does not own. `lease_of` no longer answers None
for a lease this store recorded granting.

The in-transaction window is exact rather than a general allowance: the store
names the one act between its write and its record by operation identity, and
the proof excuses that identity only.

Known cost, accepted by the review for this slice: every public read scans the
whole `operations` table. An indexed target binding is the way to make it
cheaper and needs its own schema and adoption proof.

Item 3 returns again before 3b for exact operation-evidence binding in
`review-2026-09-06T03-39-13Z.md`. Each committed journal kind must own all
operand types, derive its canonical operation identity, own its exact result
variant, and cross-bind signed request, result and materialized effect. This
includes every terminal act and the exact pending act. Agreement between a
rewritten row and rewritten result cannot overrule the original signed enqueue
or grant. Add row-plus-result rewrite, wrong-type, operand/result mismatch,
noncanonical/duplicate operation identity, malformed/SQL-null result and
pending-act mismatch regressions, with refusal leaving the complete store
unchanged.

The sixth review's [P0] and [P1] are corrected. Each committed act is now
adopted whole through one owner: its operands are owned by the SAME functions
that own them at admission (`_owned_target`, `_owned_account`, `_settlement`,
`_ending`, `_recovery` -- `activate_target` and `enqueue` were rewritten to
call them, so "the same rules" is one function rather than a claim), its
identity is RE-DERIVED from those owned operands and compared to the id it is
filed under, and its result is adopted as that kind's exact variant and proved
to be the result OF that signed request before the materialized row is
compared to it. The generated members -- rank, fence, instants -- come from
the result, which is why the result must earn the right to be evidence first.

A committed act with a SQL NULL result is a typed refusal rather than a raw
`TypeError`; the only legitimately absent result is a grant over an empty
queue, which is the typed empty variant. Two committed acts for one logical
subject are refused, and only the activation case is reachable because the
derived identity makes the others impossible through the primary key. The
pending act is adopted the same way and excuses only a row that matches what
it asked for.

Item 3 returns again before 3b for the retry and generated-decision corrections
in `review-2026-09-06T11-10-42Z.md`. Every exact replay path must semantically
adopt the complete operation and cross-bind its result/refusal to the current
materialized effect before returning, without moving replay behind a now-ended
grant check. The coordinator must also retain independent durable evidence of
the rank and grant-selection/fence decisions it generated, and prove FIFO rank
allocation and smallest-ready selection against that evidence rather than
accepting agreement between a rewritten result and rewritten row. Add
corrupted/fabricated exact-retry and coordinated rank/selection/fence rewrite
regressions, with refusal leaving rows and journal untouched.

Owner disposition after `review-2026-09-06T11-45-47Z.md`: return item 3 for one
last bounded implementation round covering only the coherent-snapshot replay
proof and complete refused-operation adoption, then run one independent
re-review and return to operations. Do not begin item 3b or items 4-9 in that
episode. Once item 3 is accepted, retain W71878 as the umbrella and create
bounded child Work for the remaining runtime, admission, execution, settlement
and end-to-end verification slices.

K owns all shared interfaces, schemas, exports, registries and cross-component
assembly during that decomposition. Tuner Work is limited to explicitly
disjoint leaf paths behind a boundary already recorded by K; a required seam
change returns to K rather than being made independently by the tuner.

## Bounded continuation after the item-3 checkpoint

- [ledger created; ready for K] `findings/finding-generic-integration-runtime/`
  — K owns the shared generic integration runtime boundary.
- [ledger created; ready for tuner] `findings/finding-accepted-candidate-admission/`
  — tuner-suitable, disjoint admission behind K's boundary; may proceed beside
  the runtime leaf.
- [ledger created; waits for both leaves above]
  `findings/finding-fenced-model-integration/` — K owns the shared assembly and
  clean model-driven integration path.
- [ledger created; waits for fenced integration]
  `findings/finding-manual-integration-recovery/` — tuner-suitable,
  disjoint operator-held diagnostics behind K's boundary.
- The existing sibling `finding-two-job-pipeline-proof/` owns the final
  end-to-end proof after W71878 and its bounded children are accepted; do not
  create a duplicate verification leaf here.

The seventh review's two [P0]s are corrected, and the two owner clarifications
of 2026-09-06 are carried out in the same round because they change the same
schema.

`operations` gains `seq`, the position an act holds among every act this store
committed, allocated inside the act's own transaction and proved dense from
one. Rank, fence and grant selection are DERIVED from that order and compared
to the recorded result and the materialized row, so the coordinated
result-plus-row rewrite the review demonstrated contradicts a third surface
that neither of them touches. The bound is stated rather than implied: with no
durable secret available, a writer who also rewrites `seq` presents a
self-consistent alternative history this seam cannot distinguish.

`IntegrationStore.replay` takes a required `witness` and has no default. Every
public mutator, including the preflight retry the fenced verbs use, reaches one
semantic owner that adopts the act whole and binds it to the materialized
relationship before returning anything. The required ordering is unchanged: the
journal is asked before a now-ended live grant is checked.

The core vocabulary is VCS-neutral. `base_object`, `head_object`, `tree_object`
and `transport_ref` leave the eligibility account, and `checkout` leaves the
target document. `TARGET_SCHEMA` is `baton.v12.integration-target/2` and
`TheCoordinatorVocabularyIsVCSNEUTRAL` is a gate over the column and member
names rather than a comment, because the way that vocabulary arrived the first
time is that each operand looked locally reasonable.

THE ACCOUNT AS IT NOW STANDS, after W101714 and the three findings of
`review-2026-09-06T12-59-53Z.md`, is FIFTEEN members, every one of them offered
by a named accepted producer: `authority_uuid`, `work_id`,
`assignment_generation` from the attempt's assignment; `line_id`,
`checkpoint_id`, `verdict_id`, `checkpoint_digest`, `path_set_digest` from
W71918's checkpoint verdict; `proposal_id`, `candidate_digest`, `result_id`,
`result_digest`, `expected_target_revision` from Authority's `publish`
operation and its `proposal` row; `profile_kind` from the accepted checkpoint
evidence's own `profile` member; and `scope_digest` from the accepted Job's
`test_scope`. `profile_version`, `profile_account_digest` and
`proposal_manifest_digest` are gone, all three for one reason: no accepted
Python operation produces them, so an entry could carry only a caller's claim.
The store shape is `SCHEMA_VERSION` 4, with no migration invented.
`EveryMemberOfTheAccountHasAProducer` asks each named surface whether it
actually offers the member, rather than counting the tuple -- which is how the
third one survived the first correction.

Three defects were found by the new matrices rather than by the review, and are
corrected here: a settlement carried on a `queued` or `leased` entry document
escaped as a raw `KeyError` instead of a refusal; `revive_refusal` was handed a
decoded document where it adopts persisted TEXT, so every replay of a durable
refusal would have reported corruption instead of the refusal it was replaying;
and a version counting from one accepted zero at the boundary and reached the
column's own CHECK as a raw `IntegrityError`, which was true of
`assignment_generation` from the first draft.

The eighth item-3 review confirms both preceding P0 corrections and the
VCS-neutral profile boundary, but leaves item 3 changes-requested for two P1s
in `review-2026-09-06T11-45-47Z.md`. First, a semantic replay proof must read
one transactionally coherent SQLite snapshot; the current preflight witness
runs before `BEGIN IMMEDIATE`, and a valid concurrent grant between its target
and history reads makes a sound exact retry report false corruption. Second,
refused operation rows must pass the same owned kind/operand/derived-identity/
dense-order adoption as committed rows before either ordinary reads or exact
refusal replay returns; currently both paths skip that proof. Add deterministic
two-connection replay interleaving, unknown/malformed/noncanonical refused act,
journal-hole refused replay and sound-refusal controls, then return item 3 for
independent re-review.

No automatic interruption recovery is added while making those corrections.
Under the later owner ruling, items 3b and 6 surface interrupted or inconsistent
integration as one typed operator-held condition, preserve the evidence and
target exclusion, and wait for explicit operator action. Item 3b and items 4-9
remain outside the bounded coordinator slice reviewed here.

Both P1s of `review-2026-09-06T11-45-47Z.md` are corrected under the owner
disposition authorizing one final implementation round for exactly those two.

Every semantic proof now observes one SQLite snapshot. `IntegrationStore`
gains a re-entrant `snapshot` -- a `BEGIN DEFERRED` read transaction, yielding
to the write transaction when one is already held -- and the relationship
pass, the lease and entry projections and the replay witness all run inside
one. The store also asks for WAL after the ownership decision, so a reader's
snapshot runs beside a concurrent writer instead of blocking it; coherence
belongs to the read transaction and holds without WAL, so a filesystem that
cannot provide it is not refused. The fenced verbs' ordering is unchanged: an
exact replay is still decided before a now-ended live grant is checked.

Refused operation rows are adopted exactly as committed ones are. `replay` no
longer branches on the recorded outcome; both reach the witness, which owns the
kind, typed operands, derived identity and dense position and proves the
surrounding relationship before the sealed refusal is revived. `_history`
adopts refused rows and keeps them out of the committed projection.

No automatic interruption recovery is added, no blocked target is reopened, and
item 3b and items 4-9 are untouched. Item 3 returns for independent re-review
only.

The independent review in `review-2026-09-06T12-05-52Z.md` accepts item 3's
bounded coordinator implementation. It confirms that the operation row and
relationship witnesses share one re-entrant SQLite snapshot, that refused acts
pass complete operation and dense-order adoption before replay or projection,
and that neither correction introduces automatic recovery. This accepts no
immutable proposal digest or integration candidate bytes. W71878 returns to
operations as the umbrella; item 3b and items 4-9 remain unimplemented and must
be scheduled as the ordered bounded children described above.
