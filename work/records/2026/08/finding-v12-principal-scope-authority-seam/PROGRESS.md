# Implementer progress — the principal/scope authority seam

Created 2026-08-26 by `baton.claude` on claiming W16821, as the record
requires.

## Not started, and the reason is the assignment's own second message

The thread says it plainly:

> Preserve the current serial item W5; intended order is
> W5 -> W16821 -> W16823 -> W6, with W16830 after W3. Do not treat readiness
> before those dependency edges as authorization to interrupt the current
> implementation.

**Readiness surfaced this Work anyway, because the edge it names did not
exist.** W16821 had no blocker, so `wait` reported it ready and unclaimed for
`baton.impl` — exactly the situation the message anticipates. Checked rather
than assumed: W5 is open and in `block`, with five open children (W6633,
W6634, W6636, W14251, W15232), four of which are with the reviewer now.

So the correction is not to start implementing and not to hand the Work back
with a note. It is to put the stated order **on the ledger**, where a later
wake cannot walk past it:

    block work=W16821 on=W5

That moved the Work to `block` and released the claim in the same act, which is
the protocol behaving exactly as it should. Reviewer authority cannot mutate
impl-routed Work — the same reason W6629 and W6634 asked their route handler to
install edges before implementation — so installing it is the route handler's
job and this is it.

## What was deliberately NOT done

**No revalidation of W9901 or the W16793 matrix.** PLAN item 1 asks for it, and
doing it now would produce an answer that is stale before it is used: the
authority tree is exactly what W5's five open children are changing, and this
Work's own FINDING is specific about which files it depends on
(`authority/schema.py`, `identity.py`, `api.py`, `session.py`, `core.py`,
`store.py`). A revalidation is worth having when the tree it revalidates
against has stopped moving.

**No dependency edges for W16823, W6 or W16830.** The thread names them, but
those Works are not routed to me and this handler's authority is over the Work
it holds. The edge installed here is the one that gates W16821 itself.

**Provider sequencing remains the approver's.** The thread records it as
pending under W16793 obligation 16832, and nothing here pre-empts it: a
dependency on W5 is about order, not about which provider implements what.

## State

**Blocked on W5, unclaimed, and implementation-ready when that gate clears.**
The acceptance and the correction boundary in `FINDING.md` are the reviewer's
and are untouched. No repository state was mutated.

## 2026-08-28 — the gate cleared, and PLAN 1 is done

Reclaimed W16821 at seq 32469. No repository state was mutated.

### The block I installed cleared legitimately

`W5` is **closed**, seven children of seven closed. So this wake is the
intended order — W5 → W16821 — arriving as an edge rather than as a
coincidence, which is what installing it was for. Nothing here walked past a
gate; the gate opened.

### PLAN 1: revalidated against the tree, and every claim in the FINDING holds

Deferred deliberately last time because the authority tree was exactly what
W5's open children were changing. It has stopped moving, so it is worth having
now, and it was measured rather than transcribed:

- **one participant string carries every role.** `authority/schema.py` names
  `participant` in fourteen places, including `claim_slot.participant` as the
  PRIMARY KEY, `capability.participant`, and the assignment/fence rows.
- **`claim_slot` is participant-keyed.** `core.py:_take_slot` inserts by
  participant and `_release_slot` deletes by `(participant, work_id)`; the
  capacity invariant is therefore per endpoint spelling, which is exactly the
  incompatibility with one principal holding two of them.
- **capability authorization is direct `(participant, capability)`
  membership**, through `core.py:_require_capability(actor, ...)`.
- **Work carries no scope.** The `work` table has route and handler columns
  and nothing an effective scope could be derived from.
- **the schema is version 1 with no migration.** `SCHEMA_VERSION = 1` and
  `store.py:_check_compatibility` refuses every other version outright —
  kind, then version, then UUID, in that order and for stated reasons. So item
  6 is not optional housekeeping: any shape change here needs an explicit
  disposition for existing stores before it can land.

### Implementation is NOT started, and that is a scope report rather than a deferral

The correction boundary is six items over a 3,759-line authority: a principal
identity separate from the endpoint, an authority-owned Work scope, one
authorization decision seam returning principal/scope/role/provenance,
principal-keyed claim capacity, decision provenance on every attributable act,
and a deliberate persistence/projection version with a disposition for schema-1
stores. Each of the six touches the same five files, and item 6 means none of
them can land incrementally without a store-compatibility answer first.

I am reporting that rather than starting it, because a half-applied schema and
capacity change is worse for the next implementer than an unstarted one: the
store refuses every version it does not recognise, so a partial edit leaves
a tree whose stores cannot be opened by either the old build or the new one.

## State

PLAN 1 done and evidenced. PLAN 2–7 not started. Passed back rather than held.

### For the route handler and the reviewer

- **The one decision that unblocks everything else is item 6.** Whether
  existing schema-1 stores get an upgrade, a rebuild, or an explicit
  "disposable proof, delete and re-init" disposition decides whether items 1–5
  land as one versioned change or as a sequence. That is a ruling rather than
  an implementation choice, and every other item waits behind it.
- **The acceptance's positive case is the cheapest thing to pin next**: two
  endpoint addresses mapping to one principal, and the second concurrent claim
  refused by the shared slot. It states the whole capacity change in one
  sentence and would make item 4 measurable before any of it is written.

## 2026-08-28 — the ruling landed, and PLAN 2–6 are implemented

Claimed W16821 at seq 33924. **No Git history or index was mutated.** The
mutation harness rewrote three source files in place and restored each one;
the digest check is below.

### The ruling, revalidated before acting on it

Approver M33752 approved the schema-1 disposition and widened it: v12 remains
early development, so **schema 2 and later versions may freely establish clean
initialization boundaries**; an incompatible store is refused without being
interpreted or modified and the operator is directed to initialize a fresh one;
migration becomes separate product Work only when retained user state requires
it.

That ruling is what makes an incremental correction safe, and it changed the
previous round's own reasoning: "items 1–5 land as one versioned change or as a
sequence" was written when a second schema bump would have been a second
unmigratable break. It no longer is. What landed here is therefore the whole
seam in one schema version, and a later cut may add another.

### PLAN 2 — the three shapes, pinned and versioned

New module `authority/principals.py`.

- a **principal** is `principal:<opaque>` and a **scope** is `scope:<opaque>`.
  The grammars are deliberately disjoint from `team.member`: a participant
  string handed to a boundary expecting a principal is REFUSED rather than
  silently accepted as one, and that substitution is the entire defect W16793
  found. A grammar is the only guard that catches it at every site at once.
- an **`AuthorizationDecision`** names the endpoint AND the principal as
  separate members, plus the effective scope, the role or capability decided,
  the grant provenance and the policy generation. It is immutable — a decision
  a caller could edit after receiving it is provenance the caller wrote.
- **`GRANTS` and `M2_GRANTS` are two names on purpose.** The durable column
  admits `direct`, `inherited` and `masked` so a resolver can land without a
  migration; this cut may only *produce* `direct`. "The shape admits it" and
  "this cut may write it" are different claims and one constant could only have
  made one of them.

### PLAN 3 — schema 2 as a clean initialization boundary

- `principal` and `endpoint` tables: the canonical identity, and the
  authority-owned many-addresses-to-one-person mapping.
- `work.scope`, NOT NULL, supplied at creation through the trusted bootstrap.
  Nullable would have been a standing invitation to derive it later for the
  rows that were missing it, and deriving it is what §2 forbids.
- `capability` re-keyed to `(principal_id, capability, scope)` with a
  `provenance` column.
- `claim_slot` re-keyed to `principal_id`, keeping the endpoint beside it
  because the Handler, the fence and the assignment identity are all still
  endpoint-addressed.
- `policy_generation`, one row by primary-key check. Kept OUT of `policy`,
  which `set_policy` lets a deployment write freely: a generation a caller
  could set is a generation a caller could rewind, and an act's recorded
  provenance would then name a configuration that never existed.
- decision provenance columns on `assignment_event` and `receipt`, NULLABLE —
  a fence, a release and an expiry are the authority acting on its own behalf,
  and NOT NULL would have forced one of them to invent a principal.

`store._check_compatibility` now refuses an older or newer store of this kind
with the operator-directed diagnostic the ruling names. **The refusal is the
whole handling**: nothing opens the file for writing, reads a row, deletes,
renames, upgrades, or applies any part of the new schema to it, and deletion is
the operator's act rather than this build's.

### PLAN 4 and 5 — the seam, and whose capacity it is

`Core.authorize(participant, capability=|route=, scope=)` answers an
`AuthorizationDecision` or `None`. Route membership and capability membership
used to be two ad-hoc `SELECT 1` existence checks answering yes or no — and a
boolean cannot be recorded beside the act it authorized, which is why the acts
recorded the endpoint spelling and nothing else. `claim` and
`_require_capability` both go through it, and both now write what it answered.

`_take_slot` keys capacity by **principal**. Two endpoint addresses bound to
one principal share one slot; before this they had one each, so §10.2's
deployment-wide limit was one the person it limits could escape by being
addressed differently.

**The default mapping is one principal per address**, which is exactly the
behaviour that existed before. What changed is that the mapping now EXISTS and
is durable, so binding two addresses to one person is a configuration act
rather than an impossibility — and every existing case in the suite still
measures what it measured.

### PLAN 6 — the cases, and they are measured by removal

New module `tests/authority/test_principal_scope.py`, **30 cases**, covering
the acceptance's positive case, its negative case, the evidence case, direct
grants with the deferred vocabulary, and the schema-2 boundary.

    caught 14 of 14

Every rule this correction adds was removed from production source and the case
that claims to establish it was required to fail. The harness is retained as
`evidence/w16821-mutation-harness.py` so the measurement is repeatable rather
than asserted; the transcript is `evidence/w16821-mutation-2026-08-28.txt`.

### A [P0] IN MY OWN CODE, caught by the authority's boundary suite

The first cut of `check_principal` capped a principal at the frozen `opaqueId`
length of 160. `check_participant` caps nothing, and the store already keeps
unbounded participant text in `work.handler` and `claim_slot.participant` — so
a wide but perfectly valid endpoint produced a default principal **the
authority then refused**, and a legitimate participant became unclaimable with
a refusal naming a value the caller never supplied.

`test_boundary`'s caller-text family suite found it in the first run. The bound
is gone, the reason is written at the site, and
`test_a_principal_is_bounded_by_whatever_bounds_its_endpoint` keeps it: a
5,000-character address claims and holds its slot.

### Existing test modules I edited, and exactly what changed in each

None of these is an assertion change. Each is a REGISTRY the suite compares
the tree against, and a new module, table or public method has to be entered in
it or the comparison is the thing that fails. They are listed individually
because editing another Work's accepted deliverable is the reviewer's call and
not mine to make quietly.

- `tests/authority/test_boundary.py` — three inventory additions (the schema's
  table set, the bootstrap face's method list) and **one fixture constant**:
  the malformed-recorded-uuid case built a store recording `schema_version
  "1"`, which schema 2 now refuses for its VERSION before the uuid check is
  reached, so that case would have stopped exercising the site it is named for
  while still passing. It now uses `str(SCHEMA_VERSION)`. The assertion is
  unchanged.
- `tests/authority/test_session.py` — the two-face inventory gains the six new
  `Core` names. The case computes the configuration surface from `Core` so that
  "a method added there lands on exactly one side and the case says which";
  saying which is what the edit is.
- `tests/authority/test_catalog.py` — the suite's file list gains the new
  module.
- `tools/parallel_test.py` — the new module registered as parallel, with the
  reason. The runner's own guard (`tests.tools.test_parallel_runner`, 36 cases)
  is green.

### One Worker Manager line, and why it is not the deferred consumption

`worker_manager/authority_port.py`'s `PROJECTION_UNREAD` gains `"scope"`.

PLAN 7 defers the Worker Manager consuming the new projection, and this is not
that: the manager's contract refuses any projection member it does not name, so
adding a member to the authority without naming it here turns this correction
into a build mismatch at the first offer. **Naming it is not consuming it** —
`scope` stays in the UNREAD half, and
`tests.manager.test_boundary_inventory.TheProjectionContractMatchesTheAuthorityItReads`
is the case that reads the authority's own source and requires the two to
agree.

### Gates

- `tests/authority` — **257 tests, OK**, the whole existing suite plus the 30
  new cases
- `evidence/w16821-mutation-2026-08-28.txt` — 14 of 14 mutations caught
- full v12 parallel source — **6 failures, 0 errors**, every one in
  `test_boundary_inventory`: the accepted baseline unchanged, checked by NAME
  and not only by count —
  `test_the_universe_sees_every_persisted_column_that_is_read`,
  `test_every_declared_probe_reaches_its_named_boundary`,
  `test_the_missing_probe_check_can_actually_fail`,
  `test_every_owned_entry_has_exactly_one_probe`,
  `test_every_boundary_call_belongs_to_an_entry_or_is_declared`,
  `test_every_receiving_entry_has_an_owning_validator`.
  The first run of this gate was at **7 failures and 1 error**; the seventh and
  the error were both the manager's projection contract refusing the new
  `scope` member, which is that contract doing its job and is the one Worker
  Manager line described above. Transcript: `evidence/w16821-gate-2026-08-28.txt`
- `tests.tools.test_parallel_runner` — 36 tests, OK, after registering the new
  module

### The tree is as it was found

    core.py        98fe4aca5cda732c
    principals.py  16ee0a55752a5abf
    schema.py      21d72fd766c7baae
    store.py       630218d709b9a1ee
    api.py         4b3c0c0876519da2

The mutation harness prints each file's digest before and after and asserts the
restoration; the run above is clean.

## State

**PLAN 2–6 implemented and measured. Passed back for independent review.**

### What is left, and it is PLAN 7's boundary

- The Worker Manager consuming the new projection — reading `scope`, and
  carrying principal/scope/provenance through offer and claim — is the
  deferred correction and is not started.
- Grouping scopes, inheritance and masks remain W9901/M6 provider work. The
  durable column admits them and this cut refuses to produce them, which is
  measured by `GrantProvenance` and by two of the fourteen mutations.
- `activity`, `contract_event`, `proposal` and `integration_attempt` do not yet
  carry decision provenance. The two acts that go through the authorization
  seam — the claim and the four receipts — do. Saying so plainly: the FINDING's
  item 5 says "every attributable act", and this cut covers the two that are
  authorized rather than all six that are attributable. The remaining four are
  written under an assignment that was already authorized, so the decision they
  would carry is the claim's; whether to copy it forward or to join to it is a
  design question the reviewer should settle before it is written six times.

## 2026-08-28 — review 2026-08-28T20:54:18Z, answered

Reclaimed W16821 at seq 34139. **No Git history or index was mutated.** All
four findings are accepted; each was reproduced on the tree first, and the
reviewer's own script is retained beside a companion that re-runs the same
three scenarios against the corrected seam.

### Reproduced before fixing

`evidence/w16821-review-repro.py` is the reviewer's script, byte for byte. Run
unchanged it produced exactly what the review reports: a `scope:platform`
verifier refused, a deployment-wide grant accepted and the receipt recording
`scope:deployment`, `capabilities_of` answering `['verify', 'verify']`, a
`scope:platform` closer refused while a deployment-wide grant closed the Work,
and no close decision anywhere.

### [P0] Every capability door decides in the TARGET's scope

`_require_capability` took `scope` as a defaulted argument, and the default was
the deployment's. `close` ran the door before loading its Work and
`_write_receipt` ran it before loading its proposal, so neither had a target to
derive a scope from.

`scope` is now a **required keyword with no default**, `close` loads its Work
first, and both receipt doors derive from the proposal's own exact assignment
identity through `_scope_of`. A defaulted argument is what caused this, so the
correction is not another default — it is the absence of one.

**And a lexical guard, because a door added later could reintroduce it by
simply not passing a scope**, which no behavioural case would notice until
somebody wrote a cross-scope case for that particular door.
`test_every_capability_door_names_the_scope_it_decides_in` walks `core.py`'s
own AST and requires every `_require_capability` call site to name one.

Positive and negative cases for **every** door: verify, review, approve,
integrate and close. The negative ones pin the CAPABILITY refusal by name,
because `review` and `approve` also have ordering preconditions and a case
accepting any refusal would pass on those with the scope rule doing nothing.

### [P0] Every directly authorized act retains its decision

The first cut spread four nullable columns over `assignment_event` and three
more over `receipt`. That shape is why `close` persisted nothing: an unclaimed
close writes neither row.

**One table, one shape, one writer.** `authorization_decision` is keyed by
`(act, act_id)` — a claim by the assignment event it authorized (so a released
and re-claimed Work keeps both rather than colliding), a close by its Work,
each receipt by its own identity, and the durably journalled refused
integration attempt by the integration identity it was submitted under. That
last one needed a durable `attempt_id`: the autoincrement `seq` is an ordering,
not an identity another table can name.

`_record_decision` **refuses a second write** rather than overwriting. A second
decision for one act is a second answer to a question that was already decided.

Assignment-derived acts — activity, contract events, proposals — join to the
claim's decision through the full exact assignment identity rather than copying
it, which the review permits and which avoids two copies of one fact.

### [P1] The public projections carry it

`assignment_events`, `activities`, `contract_events`, `proposal`, `receipt`,
`receipts` and `integration_attempts` all expose the complete typed decision,
and `project_work` gains `close_decision`. **Every case in this module now
reads the projection rather than the column** — the previous cut's cases
reached into raw SQL, so they established the column and not the acceptance's
public evidence boundary.

`_decision` reads the stored row and never rebuilds it: rebuilding would
consult today's endpoint mapping and today's policy generation and answer what
the act *would* be authorized under now.
`test_history_survives_release_reconfiguration_and_close` releases the
assignment, rebinds the endpoint to another principal, moves the generation,
closes the Work and reopens the store — and the retained decision is unchanged.

### [P1] The grant projection

`grants_of` is the projection: one entry per grant with its scope and its
provenance. `capabilities_of` is kept as an explicit compatibility helper —
the DISTINCT capability names held in any scope — with its semantics written
down and a case pinning that a name held in some scope authorizes nothing by
itself. The duplicate the first cut projected was not information; it was the
scope column missing.

Kept rather than replaced because `test_assignment.py` asserts the flat list,
and the review permits a compatibility helper whose flattening semantics are
explicit and useful. If the reviewer would rather it were removed outright,
that is a one-line change plus one assertion in another Work's module, and I
would rather be told than assume.

### MEASURED BY REMOVAL

    caught 22 of 22

The six boundaries the review named are all covered — target-scope derivation
at the receipt doors and at close, close decision persistence, the public claim
projection, assignment-derived linkage, durable refused integration
attribution, and the scoped grant projection — plus one the review implied:
history re-derived from today's mapping instead of read.

**Two mutations from the previous pass reported `[ANCHOR]` rather than
passing**, because the column-based shape they targeted no longer exists.
They are re-anchored against the corrected shape. An anchor check reporting
stale is the harness doing its job; a harness that had silently counted them as
caught would have been the defect.

### One more Worker Manager line

`PROJECTION_UNREAD` gains `close_decision` alongside `scope`, for the same
reason and with the same boundary: naming a member is not consuming it.

### Gates

- `tests/authority` — **272 tests, OK** (257 before, 15 new)
- `evidence/w16821-mutation-2026-08-28.txt` — 22 of 22
- `evidence/w16821-review-repro-corrected-2026-08-28.txt` — every finding's
  measured outcome, now inverted
- full v12 parallel source — **6 failures, 0 errors**, every one in
  `test_boundary_inventory`: the accepted baseline unchanged, checked by NAME.
  Transcript: `evidence/w16821-gate-2026-08-28.txt`

## State

**All four review findings answered. Passed back for independent re-review.**

Still deferred and unchanged: the Worker Manager consuming the new projection
(PLAN 7), and grouping scopes, inheritance and masks (W9901/M6). One open
question for the reviewer: whether `capabilities_of` should be removed outright
rather than kept as the documented flattening helper.

## 2026-08-28 — re-review 2026-08-28T21:19:50Z: the v11 reclaim join

Reclaimed W16821 at seq 34236. **No Git history or index was mutated.** The
finding is accepted; it was reproduced with the reviewer's own script before
anything was changed.

### The defect, reproduced

`evidence/w16821-v11-reclaim-history-repro.py` run against the submitted cut
printed exactly what the review reports:

    claim-principals          ['principal:baton.claude', 'principal:one-person']
    first-before              principal:baton.claude
    activity-principals-after ['principal:one-person', 'principal:one-person']

`_claim_decision_for` searched for the claim at READ time by
`(work_id, participant, generation)`, newest first. A v11 assignment mints no
generation, so a release and a reclaim through the same endpoint are two
distinct claim acts with **identical join fields** — and the later claim became
the apparent authorization of the earlier act's history without that act or its
decision row being touched.

**The v12 case passed throughout**, because generations distinguish v12 claims.
A correction measured only on the contract that cannot express the defect
measures nothing, which is why the new regression is v11 and the v12 one is
kept beside it.

### The correction: an exact reference, captured at the act

`activity`, `contract_event` and `proposal` now carry `claim_seq NOT NULL` —
the `assignment_event.seq` of the claim the act was carried out under —
resolved by `_live_claim_seq` **at the moment of the act** and never searched
for afterwards. Right now there is one live assignment and one newest claim
event for it; a reference captured there cannot be re-pointed by anything that
happens later. A nullable tuple, an instant and a newest-row ordering are not
an identity.

`NOT NULL` rather than best-effort: an assignment-derived act whose claim this
authority never journalled is not attributable, and writing it with a null
reference would be the ambiguity coming back as an absence.
`_live_claim_seq` refuses instead, and a case drives that refusal.

### What the regression covers

`AV11ReclaimDoesNotRewriteEarlierHistory`, four cases:

- release, rebind to another principal, reclaim, second activity — **both**
  claim events and **both** activities checked, and the case asserts the two
  assignment identities are EQUAL, which is what made the old join ambiguous
  and what stops this case passing because the two acts happened to differ some
  other way;
- the same across a store reopen, so the answer is the rows;
- publication is v12-only — **measured, not assumed**, because it decides what
  this class can cover: under v11 the assignment-derived act that can exist is
  the activity. The proposal's own exact reference is covered under v12, where
  a proposal can exist and where the case measures the reference rather than
  the outcome;
- an act that cannot name its claim is refused.

### MEASURED BY REMOVAL

    caught 25 of 25

Three new mutations for the durable binding: the reference searched for at read
time instead (the exact prior behaviour, restored), the reference captured as a
constant rather than at the act, and the missing-claim refusal removed. One
mutation from the previous pass reported `[ANCHOR]` because the join it
targeted no longer exists; it is re-anchored on the projection refusing to read
the reference.

### Gates

- `tests/authority` — **277 tests, OK** (272 before, 5 new)
- `evidence/w16821-v11-reclaim-after-2026-08-28.txt` — the reviewer's script,
  now passing, with the two activities keeping their own claims' principals
- `evidence/w16821-mutation-2026-08-28.txt` — 25 of 25
- full v12 parallel source — **6 failures, 0 errors**, every one in
  `test_boundary_inventory`: the accepted baseline unchanged, checked by NAME.
  Transcript: `evidence/w16821-gate-2026-08-28.txt`

## State

**The re-review's [P0] is answered. Passed back for independent re-review.**

Unchanged and still deferred: the Worker Manager consuming the new projection
(PLAN 7), and grouping scopes, inheritance and masks (W9901/M6). Still open for
the reviewer: whether `capabilities_of` should be removed outright rather than
kept as the documented flattening helper — the previous pass asked and the
re-review did not rule on it, so it stays as it was.
