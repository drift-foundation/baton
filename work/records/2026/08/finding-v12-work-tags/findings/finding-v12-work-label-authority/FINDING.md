# Build the v12 Work-label authority model

## Status

Approved implementation cut, ready for implementation on delivered W16823.

## Parent and decision authority

This child was decomposed from W28880. The approved product contract and chronological decision history remain owned by `work/records/2026/08/finding-v12-work-tags/FINDING.md`; this record narrows that contract to the core authority model. Revalidate both records and current code before implementation.

## Confirmed boundary

- Work labels are opaque normalized lowercase identifiers matching `[A-Za-z0-9][A-Za-z0-9._-]{0,63}` on input, with at most 32 distinct live labels per Work and deterministic sorted projection.
- Label mutation requires the scope-resolved `manage-work-labels` grant supplied through W16821. Route membership and participant identity are not authorization substitutes.
- Add and remove are audited Work mutations, including after terminal closure. Exact operation replay returns the recorded outcome; convergent add/remove is a successful `changed:false` no-op and emits no new event.
- The live label set, append-only mutation evidence, snapshot reads, and list/search predicates belong to the v12 authority model. Repeated positive predicates are all-of; repeated exclusions are none-of; no OR grammar is introduced.
- Labels do not affect route eligibility, claims, dependencies, readiness, scheduling, runtime publication, Thread labels, or OCI labels.

## Implementation surface to revalidate

The implementation should identify the current schema/versioning mechanism and then add the narrowest authoritative representation for live Work labels and their mutation evidence. It must integrate with the canonical Work create/mutate/read/session/replay paths rather than create a second state machine. W16821 owns the canonical principal and scope seam and is a hard prerequisite.

If the current v12 tree still lacks a complete Work product/list host, record that observed boundary and implement only authority surfaces that have a canonical owner; do not invent a parallel product layer.

## Acceptance and regression matrix

- Grammar boundaries: valid mixed-case input normalizes; invalid first characters, punctuation, empty input, 64/65-character boundaries, and 32/33-label cardinality are covered.
- Authorization covers allowed and denied principals through the W16821 seam, including terminal Work.
- Replay covers exact retry, convergent no-op, conflicting reuse, event count, and returned `changed` state.
- Concurrent add/add, remove/remove, and add/remove retain one coherent live set and audit history.
- Snapshot/projection and positive/exclusion predicates are deterministic and preserve existing unlabeled Work behavior.
- Existing scheduler, claim, dependency, runtime, Thread-label, and OCI-label behavior is unchanged.

## Open implementation fact

The schema migration or rebuild disposition must be derived from the current v12 authority at implementation time and documented in the handoff. It is not decided by this decomposition record.

## 2026-08-28 — independent review findings

**Confirmed schema disposition:** schema 3 as a clean initialization boundary
is consistent with approver ruling M33752 and the current disposable proof
store. No migration finding remains in this cut.

**Observed [P0]: exact replay re-authorizes against current policy.**
`_label_transition` loads the Work and calls `_require_capability` before
entering `_replay`. An exact retry after the recorded grant is revoked is
therefore refused instead of returning its committed outcome. Authorization
also occurs outside the `BEGIN IMMEDIATE` write transaction, so a competing
revocation can commit between the decision and label mutation. Existing
authorized transitions resolve their target and capability inside the replay
body for exactly these reasons. The additive
`test_an_exact_retry_does_not_reauthorize_after_revocation` fails.

**Observed [P0]: Work and label reads are not one authority snapshot.**
`project_work` reads the Work row and later calls `labels_of` through separate
autocommit reads. It can return an open Work with a label added only after that
Work closed — a state that never existed. `works_with_labels` likewise reads
all label rows and then all Work rows separately; a Work atomically created
with an excluded label between those reads is returned as if unlabelled. The
two additive snapshot regressions reproduce both hybrids. A comment saying
"ONE SNAPSHOT" does not open a read transaction.

**Observed [P0]: create-time labels have no attributable creation authority.**
The approved parent contract requires labels supplied at creation to use the
same authorization decision that permits Work creation and requires creation
attribution. The current tree still has only `Core.create_work`, an
unattributed trusted-bootstrap operation with no actor, operation identity or
authorization decision. This cut adds labels only to that internal method;
the public `Authority.create_work` does not accept or forward them.
`work_label_events` omits the stored `act_id` and returns `decision: None`, and
the submitted test explicitly expects that absence. Thus the event is neither
publicly reachable through the canonical creation face nor attributable as the
approved contract defines it.

**Open — approver ruling required:** either extend the authority with one
canonical attributable, replayable Work-creation decision and let create-time
labels share it, or defer create-time labels until a separately owned complete
Work creation host exists. Reviewer recommendation is deferral: this child's
record explicitly says not to invent a parallel product layer when the current
v12 tree lacks one. W29401 must then expose no create-time label operand until
that provider lands, and W28880 remains open on the missing requirement.

**Observed coverage gap:** the submitted 28 cases contain no concurrent
add/add, remove/remove, add/remove or final-slot race despite the required
matrix claiming those regressions. Correctness is plausible under
`BEGIN IMMEDIATE`, but it is not independently demonstrated and the snapshot
defects show why concurrency cannot be inferred from transaction comments.

## 2026-08-28 — approver chose bounded attributable creation

**Confirmed by approver response M34988:** implement one generic, attributable
and replayable Work-creation pipeline in this Work. The initial kind is
authority-generated `trusted-bootstrap`, not a caller operand. Creation has a
required operation identity, immutable act, effective scope and explicit
bootstrap provenance. Initial label additions commit in the same transaction
and reference that creation act. A later authorized kind must be able to carry
the real endpoint, principal, grant provenance and policy generation through
the same pipeline. Existing bootstrap records, if retained, are never
reclassified or backfilled.

The preceding **Open — approver ruling required** alternatives are superseded
by this response: bounded option A is now authoritative and deferral is not.

**Proposed implementation boundary, derived from the current tree:**

- Make `operation_id` required at `Authority.create_work`; the bootstrap face
  privately supplies the attribution kind/provenance. Neither `Core.create_work`
  nor any public caller accepts an attribution, principal, endpoint, grant or
  policy-generation operand.
- Put canonical Work operands, canonical sorted labels and effective scope in
  the creation operation signature. Enter `Store.replay` before checking for
  an existing Work. Exact retry returns the original projection/attribution;
  another effective operand collides; a different operation attempting the
  same Work id refuses ordinarily.
- Persist one immutable `work_creation` act keyed by Work and unique operation
  identity. Its closed kind cross-product distinguishes honest bootstrap
  provenance from a future authorized attribution. The authorized arm reuses
  `authorization_decision` for endpoint/principal/grant/policy evidence rather
  than copying W16821's shape into new nullable columns.
- Give each `work_label_event` an explicit act kind as well as act id. Initial
  additions name `work-create` and the creation operation id; later additions
  and removals name `work-label`/`work-unlabel`. Event projection resolves the
  named immutable attribution instead of guessing among tables or returning
  `None` for creation.
- Capture the creation instant once and use it for the Work, creation act and
  initial additions. Insert Work, attribution, complete initial live set and
  events inside the replay action so the operation-result commit is the same
  transaction.
- Add a read-only Store snapshot boundary. It joins an existing write
  transaction, opens one deferred read transaction at top level, returns fresh
  built-ins, and does not permit a write transaction to be silently nested
  inside a read snapshot. Use it around all reads composing `project_work` and
  `works_with_labels`.
- Move Work lookup, scope resolution and `manage-work-labels` authorization
  into the label replay action. The caller-owned signature is Work id,
  canonical label, action and bound endpoint; current scope and policy are
  authority state read only on first execution. Thus exact replay bypasses
  changed policy, while first execution serializes authorization and mutation.

**Observed schema allocation conflict:** W16823 is actively implementing the
already-approved cumulative authority schema 4 boundary (M35002) after this
Work's schema 3. M35002 explicitly forbids later Work from independently
reusing schema 4. The new creation attribution and explicit label-event act
kind change durable meaning, so they cannot remain schema 3 or reuse 4.

**Proposed, pending approver confirmation:** W29400 becomes cumulative
authority schema 5 after W16823's schema 4. Rebase the creation/label work on
the delivered schema-4 tree; do not race or overwrite W16823's active edit.

**Revalidated baseline:** the 31-case Work-label module currently has 28
passes, two snapshot failures and the replay-after-revocation error recorded by
the first review. No implementation correction has landed yet.

## 2026-08-29 — schema 5 approved and provider dependency delivered

**Confirmed by approver response M35127:** authority schema 5 is W29400's
cumulative clean-initialization boundary after W16823 schema 4. W29400 must
consume the delivered W16823 tree and may neither reuse nor lower schema 4.
The bootstrap creation attribution, typed label-event act, replay, snapshot,
concurrency and projection boundaries remain as approved in M34988.

**Confirmed current-tree revalidation:** W16823 is closed satisfying and the
authority now speaks schema 4 with the closed claim-result contract. The
Work-label implementation remains at its earlier partial state: it has no
`work_creation` attribution, no typed label-event act kind, `Authority.create_work`
still lacks the required operation identity and initial-label surface,
authorization still precedes replay, and projection/predicate reads remain
separate autocommit statements.

**Observed baseline, rerun after W16823:** `tests.authority.test_work_labels`
runs 31 cases with the same three known failures: exact retry re-authorizes
after revocation, Work projection returns a hybrid snapshot, and label
predicates return a hybrid snapshot. No later correction has landed silently.

**Implementation-ready boundary:** rebase the complete M34988 design on
schema 4, allocate schema 5 once, implement the attributable/replayable
creation pipeline and exact event attribution, correct replay and snapshot
ordering, and add the required competing-connection race matrix before review.

## 2026-08-29 — the two transaction boundaries corrected

**Replay precedes current policy.** The label signature is built from caller
operands alone, and the Work lookup and capability check moved inside the
replay body — so an exact retry answers from the journal, and the decision,
mutation, event and decision row serialize inside one write.

**Both composed reads take one snapshot.** `read_snapshot` holds a deferred
read transaction across the whole of `project_work` and `works_with_labels`,
so neither can compose halves of two different worlds.

**The race matrix exists and asserts coherence rather than a winner.** Under
real contention both writers can lose the lock; what must hold either way is
that the history replays exactly to the live set, no act appears twice, and
the ceiling is never exceeded.

**Still open:** the create-time attribution [P0] and the schema 5 allocation,
neither started. The schema stays at 4 deliberately — 5 is allocated once, with
the creation pipeline it is the boundary for.

## 2026-08-29 — second independent review findings

**Confirmed corrected:** exact label replay now reaches the operation journal
before current policy, and first execution resolves authorization inside the
write. Projection and predicate composition now use one explicit read
snapshot. The retained regressions pass.

**Observed [P0]: a write silently joins and is discarded by a read snapshot.**
`read_snapshot` and `transact` use the same `_depth` flag. Once a read snapshot
sets depth to one, `transact` treats itself as a nested write transaction,
runs its body, and returns success. The outer snapshot then unconditionally
rolls the write back. This is precisely the nesting the approved M34988 design
says must be refused, and it lets an apparent successful mutation disappear.
The additive Store regression fails because no `Refusal` is raised.

**Observed [P1]: the race matrix accepts transport faults as success.** Its
helper catches every `Exception`, while the assertions intentionally permit
both operations to lose and make no assertion that an answer is a committed
result or a typed refusal. A matrix in which every label mutation raises
`sqlite3.OperationalError: database is locked` can therefore pass. That
contradicts the Store's established competing-operation contract: contention
waits, a winner commits, and losers converge or receive a reasoned contract
refusal rather than a database fault.

**Confirmed still incomplete:** the approved attributable/replayable Work
creation pipeline, typed creation label-event attribution, creation tests and
cumulative schema 5 allocation have not started. This Work cannot close or
unblock W29401 before those land.

## 2026-08-29 — third independent review findings

**Confirmed corrected:** transaction mode is now explicit. Reads join writes,
writes join writes, and a write inside a read snapshot is refused before its
body runs. The disappearing-success regression is green.

**Confirmed corrected:** each race thread now opens and disposes its own
authority connection. Raw faults fail the harness, both participants must
answer, and the mutation races require at least one effective transition plus
the exact live-set/event outcome. The five required contention shapes are
green repeatedly and in the complete authority suite.

**Confirmed still incomplete:** the M34988/M35127 creation pipeline, typed
initial-label attribution, creation replay/collision/no-forgery coverage and
cumulative schema 5 boundary remain unimplemented. No acceptance or close is
possible until that approved half lands.
