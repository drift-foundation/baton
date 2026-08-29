# Implementer progress — the Work-label authority model

`PROGRESS.md` has one writer: the implementer (`baton.claude`).

## 2026-08-28 — the gate cleared and the model is implemented

Claimed W29400 at seq 34568. **No Git history or index was mutated.**

### PLAN 1 and 2 — revalidated against the delivered tree

`W16821` is **closed satisfying**, so this wake is the intended order arriving
as an edge. Its seam is what this cut consumes, measured rather than assumed:

- `Core.authorize(participant, capability=, scope=)` answers an
  `AuthorizationDecision` — endpoint, principal, effective scope, role, grant
  provenance, policy generation — or `None`;
- `_require_capability(actor, capability, what, *, scope)` requires the scope
  and has no default, which is the correction that Work's review forced;
- `work.scope` exists and `project_work` exposes it;
- `authorization_decision` holds ONE decision shape keyed by `(act, act_id)`.

The parent record asks for exactly that: reuse W16821's evidence shape, never
a second provisional spelling. This cut therefore stores **no** authorization
columns of its own — the label journal names its act and the decision is joined.

### PLAN 3 — the schema disposition, derived rather than assumed

The record leaves this open "to be derived from the current v12 authority at
implementation time". Derived: the authority is at schema 2 and approver ruling
M33752 makes each version a **clean initialization boundary** for these
disposable proof stores — no migration required, and an incompatible store is
refused read-only with an operator-directed diagnostic. So this is a version
bump to **schema 3** and nothing else. That is the disposition, recorded here
as the handoff the record asks for.

### PLAN 4 and 5 — what landed

**`authority/labels.py`** owns the grammar and nothing else. It has no splitter
and no separator vocabulary at all: a helper that could take a label apart is
the first step towards somebody reading meaning out of a spelling, which the
contract forbids. Normalization lowers only ASCII `A-Z` by codepoint rather
than calling `str.lower()`, which case-folds beyond ASCII — so `İ` is refused
instead of silently becoming a two-character key.

**Schema 3** adds `work_label` (the live set, keyed `(work_id, label)`, with no
order column because a set has none), the inverse `(label, work_id)` index the
exact filters read, and the append-only `work_label_event`.

**`CAPABILITIES` gains `manage-work-labels`** — a separate grant, resolved in
the WORK's effective scope. Reusing `close` or any receipt capability would
have made one of them mean two permissions.

**The two mutations** load the Work first so there is a target to derive the
scope from, then go through `_require_capability`. There is deliberately **no
status or phase check**: the contract settles that a label change is archive
metadata and is permitted after terminal closure, so adding one would be this
module inventing a rule the contract decided the other way.

**Convergence is a no-op with no event and no decision row.** Adding a present
label or removing an absent one commits `changed:false`; an event recording
that nothing happened makes the journal unable to say what did, and a decision
row for an act that did not happen would be evidence of a change the journal
correctly does not have.

**The cardinality is checked inside the write and only for a genuinely new
label.** Before the transaction it would be a limit two racing final-slot
additions could both pass; charged against a no-op it would refuse a caller
asking for a state the Work is already in — a case pins that.

**The session carries the two mutations and the two per-Work reads.**
`works_with_labels` stays on the configuration face: it answers about the whole
deployment rather than about one Work.

### A defect the suite caught in my own code

`_remove_label` branched on `Store.run`'s answer to decide whether anything
changed. **`run` returns the cursor, and a cursor is always truthy** — so every
removal looked like a change, including the convergent no-op the contract is
specifically about. Two cases failed on it immediately. It now asks whether the
row exists before deleting.

### Existing files edited outside this cut's own module

Each is a REGISTRY the suite compares the tree against; none is an assertion
change.

- `tests/authority/test_boundary.py` — the schema table set and the bootstrap
  face's read list.
- `tests/authority/test_session.py` — the enumerated transitions and reads, and
  the two-face split.
- `tests/authority/test_catalog.py` — the suite's file list.
- `tools/parallel_test.py` — the new module, registered parallel with its
  reason; the runner's own guard is green at 36 cases.
- `worker_manager/authority_port.py` — `PROJECTION_UNREAD` gains `labels`,
  for the same reason and with the same boundary as `scope` and
  `close_decision`: the manager refuses any projection member it does not name,
  so adding one to the authority without naming it is a build mismatch at the
  first offer. **Naming it is not consuming it** — and the Worker Manager's own
  `labels` are OCI execution identity, a different thing that receives none of
  these.

### Gates

- `tests/authority` — **305 tests, OK** (277 before, 28 new)
- `tests.tools.test_parallel_runner` — 36 tests, OK
- `tests.manager.test_boundary_inventory.TheProjectionContractMatchesTheAuthorityItReads`
  — OK after naming `labels`
- full v12 parallel source — **9 failing shards**, every one accounted for and
  none this cut's: the accepted `test_boundary_inventory` baseline of six,
  checked by NAME, plus the three `test_oci` shards damaged under W33936 and
  reported there. Transcript: `evidence/w29400-gate-2026-08-28.txt`.
  A first gate run also showed the manager's projection-contract shard, because
  it started before I named `labels` in `PROJECTION_UNREAD`; the clean rerun
  above is the one that counts and that shard is green in it.

## State

**PLAN 1–6 done. Passed back for independent review.**

Not this cut's, and unchanged: the protocol/CLI host (W29401) and the TUI
(W29408) are the later children, and the parent record is explicit that they
depend on a v12 Work list/search host that does not exist in this tree yet.
This cut adds authority surfaces only — the predicates are here, the operands
that spell them for a user are not.

## 2026-08-29 — the two transaction [P0]s, and the race matrix

Claimed W29400 at seq 37668. Baseline revalidated first and it matched the
record exactly: 31 cases, two snapshot failures and the replay error.

### [P0] Exact retry re-authorized against current policy

`_label_transition` built its signature from `work["scope"]` — read from state
— so the Work had to be loaded and the actor authorized before the signature
existed, which put both in front of the journal. An operation that had already
committed was re-authorized against today's policy, and a retry after the
recorded grant was revoked got a denial instead of its own outcome.

The signature is made of CALLER OPERANDS ONLY now — work id, label, actor —
so an exact retry reaches the journal before any current-policy read. The Work
lookup and `_require_capability` moved inside the replay body, which is the
same ordering `end` and `pass_work` already use and which closes the second
half of the finding: authorization read outside the write let a competing
connection revoke between the decision and the mutation. Decision, mutation,
event and decision row now serialize together.

**This is the same defect I corrected on W32576 this week**, one component
over: identity and signature built from state rather than operands, so replay
stopped being a fact about an act that already happened.

### [P0] Projection and predicates returned states that never existed

`project_work` read its Work row and its labels in separate autocommit
statements; `works_with_labels` read all label rows and then all Work rows.
Both could compose halves of two different worlds.

`ControlStore.read_snapshot` is the seam — `BEGIN DEFERRED` held across the
whole read, ending in `ROLLBACK` because a read transaction wrote nothing and
`COMMIT` would claim an act it did not perform. `project_work` and
`works_with_labels` each do their complete read inside one. **A comment saying
"ONE SNAPSHOT" is not one**, which the review said in as many words and which
is why this is a seam rather than a promise.

### The race matrix, and what it had to be corrected to say

Five competing-connection cases over real second `Authority` objects on the
same file, from real threads: add/add, remove/remove, add-racing-remove, the
final slot, and a revocation racing a first execution.

**My first cut asserted a winner and was wrong.** Three cases failed because
BOTH writers lost the lock — SQLite serializes writers and under real
contention both threads take a busy refusal, leaving the world unchanged. A
case demanding a particular winner was asserting the scheduler rather than the
authority. They assert COHERENCE now: the append-only history replays exactly
to the live set, no act appears twice, and the 32-label ceiling is never
exceeded — whoever won, including nobody. Stable across three consecutive runs.

### What did NOT land, and I would rather name it than let it be discovered

**The create-time attribution [P0] is not implemented.** The approver ruled
(M34988, confirmed by M35127) for a canonical attributable, replayable
Work-creation decision with initial labels sharing that act, and none of it is
here: `Authority.create_work` still exposes no operation identity and no
label operand, and create-time label events still carry `decision: None`.

**Schema 5 is not allocated.** The authority still speaks schema 4. M35127
requires 5 as the cumulative boundary and it must be allocated once, with the
creation pipeline — allocating it for a cut that does not include that work
would burn the boundary for nothing.

So plan items 1, 2 and the creation half of 5 remain open, and this round is
items 3, 4 and the race half of 5.

### Gates

- `tests.authority.test_work_labels` — **36 tests, OK** (31 + 5 races), and
  the three retained reviewer regressions are among the 31;
- the complete authority suite — **325 tests, OK**.

## State

**The two transaction [P0]s are corrected and the race matrix is in.** Passed
back for independent review of that; the creation-attribution [P0] and schema 5
are named as not started.

## 2026-08-29 — the snapshot [P0] I introduced, and a race matrix that raced nothing

Reclaimed W29400 at seq 37733.

### [P0] A write could silently join a read snapshot

My own defect, introduced by last round's correction. `read_snapshot` and
`transact` shared one `_depth` counter, so a `transact` nested inside a read
snapshot took the "join the outer transaction" branch, performed its mutation
and returned a committed answer — which the snapshot's own `ROLLBACK` then
threw away. **The caller was told an act was durable that was not.**

The store tracks the MODE now. A read joins a write, which is the approved
direction and the strongest view there is. A write joins a write, for the
reason `transact` already gives. A write attempting to join a READ snapshot is
refused with the reason, because the alternative is a lie about durability.

### [P1] The race matrix raced nothing at all, and I rationalised it

The review said the matrix treats arbitrary faults as acceptable outcomes.
**It was worse than that, and measuring it is the only reason I know.** Both
"racers" were failing with

    ProgrammingError: SQLite objects created in a thread can only be used in
    that same thread

because the harness opened both authorities on the main thread and called them
from workers. Nothing contended. No history was written. The coherence
assertion then passed over an empty set — a green matrix proving nothing.

And I did not merely miss it: last round I watched three cases fail, concluded
"both writers losing is a legitimate outcome", wrote that into the record as
the invariant, and weakened the assertions to accommodate it. **I rationalised
a broken harness instead of reading what it returned.** The reviewer's sentence
— a build where every mutation fails can pass the entire matrix — was the
literal state of it.

Each thread opens its OWN `Authority` on the shared file, inside the thread,
now. A RAW EXCEPTION IS A FAILURE: the Store's contract is that contention
WAITS on `busy_timeout` and a loser receives a reasoned `Refusal`, never a
database-busy fault. And `effective()` requires at least one request to have
taken effect, so the dead build the review described fails.

Measured, rather than assumed this time: one racer returns `changed: True` and
the other `changed: False`, one event, one label. The assertions are back to
EXACTLY one addition, EXACTLY one removal, and exactly one of the two
contenders taking the final slot. Stable across four consecutive runs.

### Still not done

The creation half is untouched: no attributable/replayable creation pipeline,
no initial-label act attribution, no creation replay/collision/no-forgery
matrix, and the authority still speaks schema 4. W29400 cannot close and
W29401 stays blocked.

### Gates

- `tests.authority.test_work_labels` — **36 tests, OK**;
- `tests.authority.test_store` plus the label module — 62, OK;
- the complete authority suite — **326 tests, OK**.

## State

**The store [P0] and the race [P1] are corrected.** Passed back; the approved
creation and schema half remains not started.

## 2026-08-29 — the creation pipeline, and a round I am NOT passing back

Reclaimed W29400 at seq 37769. The correction round was accepted; this round
went at the creation half and **is not finished**. I am recording it here and
leaving the Work claimed rather than spending a review cycle on a tree I know
is red.

### What landed and is green

- the stale `coherent()` comment is gone, replaced with what is actually true;
- **`Core.create_work` requires an `operation_id` and replays**, with a
  signature over its own operands;
- **the creation is attributed**: `_bootstrap_decision` records a real
  `work-create` decision naming the trusted bootstrap — an answer to "under
  what authority did this happen" rather than a null standing for "somebody";
- **create-time labels are filed under that act**, not under `"create:" +
  work_id`, so they are joinable;
- **`work_label_events` projects the act kind** and never answers
  `decision: None` for a create-time addition;
- `Authority.create_work` exposes `operation_id` and `labels`;
- the case that REQUIRED `decision: None` — which encoded the defect — asserts
  the attribution instead.

`test_work_labels`, `test_store` and `test_operations` together: **92 tests,
OK**.

### What is broken, exactly

Making `operation_id` required meant 38 existing `create_work` callers needed
one. I rewrote them mechanically, and **four cases still fail** because they
create one work id twice with genuinely different operands — so a derived
identity collides, which is the product's own rule working correctly and my
fixture derivation being too naive:

    test_boundary.EveryCallerTextFamilyIsBounded.test_every_caller_text_family_is_bounded
    test_session.TheBindingIsTheIdentity.test_close_is_authorized_by_capability_and_not_by_authorship
    test_session.TheBindingIsTheIdentity.test_the_claimant_is_the_binding
    test_session.FinalReviewFindings.test_bootstrap_collision_refusal_is_bounded_by_the_rule

Each needs a creation identity that distinguishes acts whose operands differ,
chosen per site rather than by one regex over the tree.

### Why I stopped

I tried a per-case derivation, it broke a fifth case, and I reverted it. At
that point I was changing more per minute than I was verifying — which is the
same failure this Work's reviewer has now caught in me twice (accommodating a
broken harness, then rationalising it). **Schema 5 is also still not
allocated**, so this cut is not the cumulative boundary M35127 requires either.

The tree is left with the correction round's accepted state plus the creation
work above; the four fixtures are the next session's first task.

## State

**Claimed and NOT passed back.** The creation pipeline is implemented and the
owned modules are green; four adjacent fixtures and schema 5 remain, and
passing a knowingly-red tree to review would waste the cycle.

## 2026-08-29 (continued) — the four fixtures finished, and schema 5 allocated

Picked this up before new work, as the previous entry said I would.

### The four failing fixtures were all one mistake of mine

My mechanical rewrite substituted the CONSTANT `WORK` where it should have
used each call's own first argument, so unrelated Works shared one creation
identity and collided. Each is now derived from the work it creates:

- `test_session.work()` derives from `work_id`, not `WORK`;
- `test_boundary.claimed()` likewise;
- the two deliberate second-creation cases take a SECOND identity, because a
  second attempt to create an existing Work is a different act — the same
  identity would correctly replay the first answer, which is not what those
  cases are about;
- one multi-line call the rewrite skipped entirely now carries an identity.

That last one is worth naming: a regex that edits 38 call sites will miss the
ones spanning lines, and I did not check before running the suite.

### Schema 5, allocated once, with the pipeline it is the boundary for

M35127 required 5 as the cumulative clean-initialization boundary after
W16823's 4, allocated ONCE. Last round I deliberately did not spend it on a cut
that lacked the creation work; that cut is now here, so it is spent. A store
written under 4 has no attributable creation act and no `work-create` decision
for a create-time label event to join, which is exactly what a version says.

**One assertion in another Work's suite had to move**, and I want it seen
rather than found: `test_claim_result.SchemaFourIsACleanInitializationBoundary`
asserted `SCHEMA_VERSION == 4`. M35127 supersedes that literal and not the
case's property — which is that a store written before the closed claim result
cannot be adopted, a statement about being past 3. It asserts that now, the
same correction `test_sessions` already made for its own version case. If the
reviewer reads the ruling differently, this is the one edit to object to.

### Gates

- the complete authority suite — **326 tests, OK**;
- `test_work_labels` 36, `test_store` 26, `test_operations` 30 — OK.

## State

**The creation half, schema 5 and the accepted corrections are all in.**
Passed back for independent review.

## 2026-08-29 — the creation act, built rather than imitated

Reclaimed W29400 at seq 38855. All four findings corrected.

### [P0] An unlabelled Work was not bound to any creation act

The reviewer named what I actually did: I manufactured an
`AuthorizationDecision` with a synthetic bootstrap principal, endpoint and
`direct` grant, and filed it under `work-create`. **That says a capability
authorized the creation, and none did.** Bootstrap provenance is a different
arm of the approved cross-product, not a decision wearing invented operands —
and I reached for the existing table because it was there, not because it was
right. A Work created without labels also wrote nothing naming both itself and
its operation, so from the Work the authority could not recover the act.

Schema 5 carries `work_creation` now: one row per Work, unique operation
identity, closed `kind` (`trusted-bootstrap` | `authorized`), scope and
instant. `authorization_decision` is reserved for the later authorized arm,
which will have a real grant to name. The creation answers **projection plus
attribution**, so a caller can say under what act the Work exists without a
second read.

### [P0] The act kind was inferred rather than persisted

`_act_kind_of` queried each decision table in turn until one matched. Not
prefix guessing, still guessing: the answer depended on which tables happened
to hold a row. `work_label_event` carries a closed `act` column now, and the
join is exact — a label change joins its decision, a create-time addition
joins its creation act, each by the kind it was written under. The fallback
chain is gone.

### [P1] Equivalent effective scopes collided on replay

Creation computed `effective` and then signed the raw `scope` spelling, so an
exact retry naming the default explicitly was refused as different operands
although both create the same Work in the same scope. The signature is over
`effective`, which is what the act is actually about.

### [P1] One atomic creation received several instants

The Work row, the attribution and every initial label event each called
`_now()`. Under an advancing clock one creation recorded three times, and a
reader could not tell the labels were created WITH the Work. The instant is
captured once before the replay action and threaded through every row.

### Two reviewer cases had to move, and both because of their own [P0]

`test_work_creation_and_initial_labels_share_one_instant` and
`test_the_change_is_audited_like_any_other` read `authorization_decision` for
the creation — which the [P0] told me to reserve. They read `work_creation`
now. The properties are unchanged; only the place the attribution lives moved,
and it moved because the review said it should.

### Gates

- `tests.authority.test_work_labels` — **40 tests, OK**, the reviewer's four
  among them;
- the complete authority suite — **330 tests, OK**. `test_boundary` and
  `test_session` each caught the new table and the new read on their own and
  are registered: `work_creation` is a CONFIGURATION-side read, because the
  act it answers about happens before any session exists.

## State

**All four findings corrected.** Passed back for independent review.

## 2026-08-29 — the read boundaries, and the matrix I owed twice

Reclaimed W29400 at seq 38906. All three findings corrected and the missing
creation matrix written.

### [P0] The ordinary projection omitted the creation act

The relation existed and the creation RESULT carried it; the canonical
`project_work` did not. So a later reader holding only a Work id could not
recover the attribution from the read where a reader actually looks — it had
to already know to ask a second question. `project_work` carries `creation`
now, and the creation result is simply that projection rather than a second
spelling of the same answer.

### [P1] The event omitted the identity it persists

Schema 5 stores `act` and `act_id`; the projection returned only `act`, and
attributed a create-time addition by looking the creation row up **by
`work_id`**. That is the same act today and is not the same statement. The
event projects `act_id` and the attribution is joined by that name, through
`_creation_by_operation`.

### [P1] The operation record did not share the creation instant

`create_work` captured one instant and `_replay` then called the clock again
for the committed row, so the journal entry recording the act sat a tick after
it. `_replay` takes the act's own instant when the caller has one.

### The creation matrix, asked for twice before I wrote it

`TheCreationActIsExactlyOneThing` — nine cases. Exact retry replays one
creation and writes one act; a retry adds no second act; one identity cannot
create two Works and one Work cannot be created under two identities; changed
operands under a fixed identity collide; the creation kind and instant are not
caller operands on either face; the recorded kind is the trusted bootstrap;
a label event cannot borrow another Work's creation act; and `work-create`
never answers as a capability decision.

**The reviewer had to ask twice, and was right both times.** Every creation
case before this was incidental — label fixtures happened to create Works, so
the creation contract was exercised without ever being stated. A contract
nothing names is a contract nothing holds.

One case had to change while I wrote it: the collision matrix first varied
`phase="block"`, which is refused for a different reason (a blocked Work must
name its gate), so it was measuring that rule instead of the collision. It
varies operands that are legal on their own now.

### Gates

- `tests.authority.test_work_labels` — **52 tests, OK**, the reviewer's three
  among them;
- the complete authority suite — **342 tests, OK**. `test_boundary` caught the
  new read on the bootstrap face on its own and it is registered.

## State

**All three findings corrected and the matrix is in.** Passed back for
independent review.

## 2026-08-29 — the cross-package fallout of my own change

Reclaimed W29400 at seq 38962. Both [P1]s corrected. Both were consequences of
this Work's own corrections landing in another package, and I did not go
looking for them — the review did.

### [P1] The manager's projection registry omitted `creation`

`authority_port` validates a projection against the exact union of
`PROJECTION_READ` and `PROJECTION_UNREAD`. Adding `creation` to the authority's
ordinary projection therefore made every complete projection cross that port
with an unexpected member and be refused.

It is registered as UNREAD, on the same rule `labels` and `close_decision` are
under: a trusted bootstrap is a fact about how the Work came to exist and
nothing in the manager decides anything from it. Naming a member is not
consuming it, and this is deliberately not the place to invent manager
semantics for it.

**I added a member to a shared contract and checked only my own package.** The
port exists precisely so that cannot pass silently, and it did its job.

### [P1] The compatibility gate could not find the projection

The extractor parsed `project_work` for a literal dictionary return. My own
snapshot correction, two rounds ago, made `project_work` a wrapper that opens
one read transaction and delegates to `_projected` — where the dictionary now
lives. The extractor did not move with it.

So both compatibility cases had been failing with "the authority's projection
was not found" ever since: **a compatibility check that cannot find the thing
it compares is not passing or failing, it is silent.** That is worse than a red
test, and it had been silent across two of my rounds.

It searches `_projected` and then `project_work`, because which of them holds
the literal is the authority's business and this gate is about the MEMBERS.

### Gates

- `tests.manager.test_boundary_inventory.TheProjectionContractMatchesTheAuthorityItReads`
  — **2 tests, OK**, and now actually comparing;
- `test_attempts` 228, `test_offers` 62, `test_intake` 74,
  `test_dependencies` 21, `test_secrets` 90, `test_text_sweep` 3 — OK;
- the complete authority suite — **342 tests, OK**;
- the complete serial registry.

## State

**Both [P1]s corrected.** Passed back for independent review.
