# Progress

Not started. This leaf follows the persistent Job manager contract and may be
reviewed ahead, but implementation must not invent a second submission or
stage-state owner.

## 2026-09-05 — `baton.tuner`

Implemented the accepted W71877 scheduler boundary after revalidating the
current store and recording the schema-4 supersession in `FINDING.md` and
`PLAN.md`. The candidate adds transactional immutable pool generations,
durable virtual workers and stage allocations, cross-generation live capacity
constraints, principal-aware selection, reserve-before-offer ordering, hard
identity exclusions, soft lane affinity, participant-bound offer adoption,
claim-principal verification, generation-preserving worker routing, canonical
settlement/recovery, and job-status allocation evidence. It composes existing
participant-bound Worker Manager operations and persists no `AgentSession`.

Changed production and operator paths are `v12/python/DEPLOYMENT.md` and
`v12/python/src/baton_v12/job_manager/{__init__,delegation,documents,manager,
projection,scheduler,schema,store}.py`. Focused coverage is in
`v12/python/tests/job_manager/{fixtures,test_exchange,test_scheduling,
test_store,test_tool}.py`; `v12/python/tools/parallel_test.py` registers the new
module.

Verification is green for all 313 Job-manager tests and all 92 single-worker
deployment tests; direct bytecode compilation and `git diff --check` also pass.
The broader boundary-inventory baseline remains red in five existing
Worker-Manager inventory cases (58 missing probes, 162 unowned entries, 38
orphan calls, and two untracked columns), with no reported scheduler path. The
Authority catalog baseline independently sees `test_work_label_exposure.py`,
which its expected list does not yet name. Neither
out-of-scope aggregate failure was modified here.

State: implementation complete; awaiting digest-bound independent review.

## 2026-09-05 — baton.claude — the seven reviewed gaps (PLAN items 9 and 10)

All seven findings in `review-2026-09-05T11-17-00Z.md` are corrected, each with
the regression the review asked for. Every one was real; three of them were
about a fallback that looked like tolerance and turned out to be a decision
nobody made.

### [P1] Attachment revalidates every worker it attaches, not one generation

`activate_pool` revalidates the ONE generation whose document it is handed, and
`_required_workers` then attaches workers from older generations that still
hold live allocations. Nothing revalidated those. A claimed allocation from an
old generation could be launched, dispatched, concluded or observed after its
endpoint came to mean another principal — and the claim-answer comparison is no
help, because that claim was taken before the restart.

`PooledManagerOperations.__init__` now REQUIRES `resolved_principals` and holds
every required worker to it, active or not, refusing before any stage operation
rather than at the first one that happens to compare. The regression keeps a
live old-generation allocation while the deployment resolves its participant
elsewhere, and also attaches successfully with the honest resolution — so the
refusal is about the mismatch rather than about prior generations existing.

### [P1] No allocation is a refusal, and the migrated case is why

`_worker` returned whichever worker sorted first when no allocation existed,
and `launch`, `dispatch`, `conclude`, `observe` and `refresh_runtime` all used
it. That erased reserve-before-offer and the participant/generation binding at
the one seam that decides which endpoint acts.

It is not an academic caller error, and the review is right about which case
matters: the 3 → 4 migration deliberately creates EMPTY scheduler relations, so
a store carrying an already admitted schema-3 stage arrives with an offer and
no allocation. The refusal names that case and says a migrated in-flight stage
is recovered or stopped through the operations that hold its offer.

**`observe` and `refresh_runtime` needed a distinction the review did not have
to make, and it is stated rather than smuggled.** One tick observes every live
stage, including one not yet admitted — that is how the manager learns it owes
an `admit` — so a blanket refusal broke the ordinary sweep. A stage with NO
OFFER has no runtime for any worker to hold, so every attached store answers
the same not-started document and choosing one decides nothing; the moment an
offer exists without an allocation that stops being true, and `_reader` refuses
with the same words. Both halves are covered.

### [P1] A durable admission refusal no longer releases on its own

Durability says a refusal is a recorded outcome; it does not say no offer
exists. `ManagerOperations.admit` commits `issue_offer` before it invokes the
injected bearer delivery, so a durable delivery refusal arrives with the
canonical offer already there, and releasing then lets unrelated work reserve
the same logical worker and principal while that offer may still be accepted.

Release now happens only on the settlement table's own evidence: the canonical
admit receipt, read at its owner — the same question `binding_intent` already
asks. Absent, no offer was issued and the reservation is safe to return;
present, the allocation is quarantined instead. The regression drives a real
`ManagerOperations` whose bearer delivery refuses durably, and then requires a
second stage to be REFUSED the same worker — because the point is the capacity,
not the row.

### [P1] The 3 → 4 migration proves the schema it migrates from

The finished-shape check asked only that the v4 table names existed afterwards.
The reviewer stamped a store as schema 3 with `episodes_one_live_per_stage`
removed and it opened as schema 4 with that index still missing.

`_exactly_schema_three` now runs under the migration lock, before the step that
depends on the old shape. The expectation is DERIVED — this build's v4 schema
minus exactly what the 3 → 4 step creates, both read from `schema.py` — because
a second hand-written list of schema-3 objects would be a copy to drift from,
and drift is the class of defect this check exists for. `_created_name` refuses
an `ALTER` in that step rather than silently subtracting nothing, since the
subtraction is only valid while the step creates.

**It compares the SHAPE, not the `sql` text, and that is a correction to my own
first attempt.** I wrote the text comparison first and nineteen existing tests
failed: `MIGRATIONS[1]` rebuilds `stages` and `receipts` through `_2` tables and
a rename, so a store that arrived at schema 3 by migrating carries that step's
DDL while one installed at 3 carries the install's. Both are legitimate, and
comparing text would refuse a good store for its punctuation. What must agree
is every object's name and type, every table's columns with their declared
types, null-ness, defaults and primary-key positions, every index with its
uniqueness and exact column list, and every foreign key.

What that does NOT cover is said in the code rather than implied: SQLite
exposes no pragma for CHECK constraints, so a CHECK edited in place is not
caught. The reviewed defect and the ones asked for beside it — a missing index,
a changed column — are.

Six regressions: the positive migration, the reviewer's exact missing index, a
changed column, an extra object, a missing table, and two concurrent openers
that must leave one store at schema 4. Each refusal asserts the store is
untouched: still schema 3, still without the scheduler relations.

### [P2] A historical variant activates again as a new generation

The pool digest identifies the immutable CONFIGURATION; it was also the
operation identity and a UNIQUE column, so activating the primary document
after a fallback answered generation 1 while generation 2 stayed active — which
reads as "the primary is back" while every new reservation still went to the
fallback.

The two questions are separated. `pool_generations.digest` is no longer unique,
and the operation identity counts how many generations already carry this
digest, minus the live one when the live one IS this document. An exact retry
of the activation that is currently active replays; a deliberate return to a
configuration that is not active is a new act with a new identity and a new
generation. Covered primary → fallback → primary, with the retry, and across a
reopen.

### [P2] A settled allocation still checks its operands

`_move` returned early whenever the allocation was already in the requested
state or already released, BEFORE it built the signature — so releasing twice
with two different reasons answered the first row instead of refusing the
changed operand, though `reason` is part of the signature by construction. A
settled allocation is exactly where a replay must be told from a second,
different act, and short-circuiting in front of the journal removed the only
thing that could tell them apart.

Absence is still absence; everything else goes through `JobStore.transact`.
Covered: same-operand replay, changed-reason refusal with the recorded reason
intact, recovery-then-release, and release-then-recovery.

**One asymmetry is worth naming because my first test got it wrong.** Repeating
`require_recovery` after a release does NOT refuse: it is an exact replay of an
act that did happen, so it answers what was recorded. What refuses is a recovery
on an allocation that was never quarantined and is already released — its
capacity is back in circulation, and quarantining it again would be
quarantining whatever took it. The case now drives both, plus a third
reservation proving the freed capacity really is usable.

### [P1 acceptance gap] Four effective claims, at the boundary that decides

`fixtures.FakeSession.claim_slots` mimics Authority's one-live-claim-per-
principal rule and nothing constructed a session with it, so the four-capacity
proof stopped at `reserve` — the scheduler's own answer about capacity, not
Authority's.

`FourEffectiveClaimsAreLiveTogether` drives two implementation and two review
stages through real `ManagerOperations` for four participants sharing ONE
control store and ONE claim-slot map, because both are what four workers
actually share in a deployment. It sweeps to admit, accepts each offer as its
own worker by its own bearer, sweeps again to claim, and then requires four
distinct principals each holding one work — and each claim recorded by the
session of the worker its allocation names, which is the routing half.

Beside it: the alias collapse asked at the Authority-like boundary itself
rather than at the scheduler's uniqueness index, and a failure-isolation case
where one worker's claim refuses durably while the other three stay reserved.

### Measured

- `tests/job_manager` (discovered): 313 → **330, all passing**.
- `tests.tools.test_single_worker`: **92, all passing** (the suite finds its own
  disk-backed root; naming a nonexistent one is what makes it refuse).
- The canonical parallel gate: 528 shards, **3,686 tests, 6 failures, 0 errors,
  3 skipped** — the six being the same separately attributable baseline this
  campaign has named at every round: the Authority catalog's own file registry,
  and the five `test_boundary_inventory` failures on `operation_id` and
  `settled_at`.
- `git diff --check -- v12`: no output.

### The working tree gained another leaf's candidate mid-turn

Reported rather than absorbed, because it changes what a measurement means.

When this turn began, `git status` over `v12/` listed the fifteen paths this
Work's review enumerated. It now lists twenty-eight: `worker_manager/
review_cycles.py`, `source_profiles/checkpoints.py`, `REVIEW-CYCLES.md`, two
new `tests/manager/` suites and edits to six further files have appeared —
W71918-shaped bytes that are not W71877's and are in nobody's manifest here.

Two consequences, both stated exactly:

1. **The broad-gate result above was taken before they landed.** 528 shards
   collected the modules that existed then. It is a true measurement of that
   tree and not of the one on disk now.
2. **The canonical runner currently REFUSES**, because
   `tests.manager.test_checkpoint_profiles` and `tests.manager.test_review_cycles`
   belong to no registry. That is the completeness gate working. Registering
   them is a classification claim about suites this Work does not own, so it is
   not done here — W71917 recorded exactly why such an entry is a decision
   rather than a line.

The focused job-manager and single-worker measurements above were re-run after
the intrusion and are unaffected.

### The frozen candidate

The manifest is the newest `candidate-*.manifest` in this record: eighteen
paths — the fifteen under `v12/` this Work's review enumerated plus this
dossier's three — against base `6532e6f`. **The path set is NAMED rather than
scanned**, precisely because "everything changed under v12" is no longer a
statement about W71877.

THE AGGREGATE LIVES IN THE MANIFEST AND IN THE HANDOFF, not here. This file is
one of the eighteen paths the digest covers, so writing the digest into it
would change the bytes it claims to describe. The manifest supersedes
`sha256:c65246632153bd23dd2ebbe991d70c7f7a5fa28df8d3338bc8d7b33c8d8796b5`,
which bound the bytes the review examined.

## 2026-09-05 — baton.claude — constraint semantics, the composed boundary, and a real proposal

All three findings in `review-2026-09-05T11-57-43Z.md` are corrected. Two of
them were my own corrections not going far enough, and the third was a category
error about what a "candidate" is.

### [P1] The prior-schema check compares the whole definition now

My first validator compared columns, foreign keys and index column lists
through pragmas, and explicitly gave up on `CHECK`. The reviewer's probe shows
exactly what that costs: an index recreated with the same name, the same
uniqueness and the same column list but the OPPOSITE partial predicate --
`WHERE ended_state IS NOT NULL` in place of `IS NULL` -- migrated cleanly.
That predicate is the whole of what `episodes_one_live_per_stage` enforces;
reversed, it permits any number of live episodes for one stage.

`_schema_shape` now compares `sqlite_schema.sql` itself, so partial predicates
and table `CHECK` constraints are in scope because they are in the text.

**What made the pragma version tempting was real, and `_definition` is the
answer to it rather than a weaker comparison.** Two spellings of one schema are
both legitimate, and I found three differences between them, each pure
typography:

- `MIGRATIONS[1]` builds `stages` and `receipts` as `_2` tables and renames
  them, so SQLite rewrites the stored header as `CREATE TABLE "stages"` —
  quoted, where an install writes it bare;
- the hand-written schema-1 fixture writes `meta (key TEXT` where `SCHEMA`
  writes `meta (\n  key TEXT`, which differ in spacing around punctuation;
- `SCHEMA`'s `episodes` carries a `--` comment explaining the all-three-or-none
  ending CHECK, and SQLite stores comments verbatim; `MIGRATIONS[1]`'s copy of
  the same table has none.

So `_definition` removes `--` comments (first, while the newlines that end them
are still there), removes identifier quoting, spaces out punctuation, and
collapses whitespace. Everything else — every column, every constraint, every
predicate — must match exactly. Each of those three normalisations is named in
the code with the spelling it reconciles.

Three regressions added: the reviewer's reversed predicate; a rebuilt
`episodes` whose ending CHECK is dropped while every column, foreign key and
index survives; and a positive case that renames `stages` the way
`MIGRATIONS[1]` does, asserts the recorded text really changed, and requires
the migration to accept it. Each refusal asserts the store is untouched.

### [P1] The four-claim fixture reaches the run, the seam and the settlement

**It runs now.** Each worker gets its OWN recording `start_runtime`, so the
launch pass is a statement about routing rather than about four stages
starting: each stage's start is recorded by the capability belonging to the
worker its allocation names. It is asserted on the CLAIM TICK's own report,
because the launch pass is last and reacquires state first — a stage this tick
claimed is a stage this tick starts, and asking for another sweep would only
prove that a started stage starts again.

**The alias case goes through the scheduler, and the premise it was written on
turned out to be false — which is the more useful result.** My first version
called two `FakeSession.claim` methods directly and proved only that the fake
refuses. Driving the intended two-generation shape shows the scheduler's
live-principal uniqueness is CROSS-GENERATION: the second alias is refused at
`reserve`, before any offer or claim exists. Two participants Authority maps to
one principal never become two capacities at all, and the collapse happens one
layer earlier than either of us assumed. The case asserts that, asserts one
allocation across two generations, and then requires the pooled surface to
refuse the unreserved stage by name rather than routing it to whichever alias
is in the active generation.

**The failed slot's settlement is asserted, and it is RETAINED.** My first
version would have passed while that capacity leaked. Advancing the durable
claim refusal through further sweeps shows what actually happens: a durable
claim refusal is not an ending. The offer stays live, the episode owes its
claim, every tick defers it, and the allocation stays `reserved` — which is
what the settlement table asks for when nothing has proved that no assignment
exists. The case drives three further ticks, requires each to defer, and then
requires that a NEW review stage cannot take that capacity — because "released"
and "leaked" look identical from a row and differ entirely from the next
stage's point of view.

### [P1] The candidate is a real immutable proposal again

The reviewer is right that a list of hashes over a shared mutable checkout is
evidence of one observation and not a candidate an integrator can preflight.
It has no sealed members, no base, no patch — and this review's own append-only
updates to FINDING and PLAN necessarily invalidated two of its named digests,
which is the argument made by the thing itself.

The correction is sealed in the same `baton.immutable-proposal/1` custody shape
the previous proposal used: read-only `base/` and `candidate/` copies of every
member, `candidate.manifest`, a `proposal.patch` that applies to the named
base, `manifest.json` carrying per-path base and candidate digests and sizes,
and `DIGESTS`. The proposal digest is recomputed by the recipe the manifest
states rather than asserted.

`ac11dbae…` is not reused and is not a proposal; it was a working-tree
observation and the record should read it as one.

### Measured

- `tests/job_manager` (discovered): **333, all passing** (313 at the reviewed
  proposal, 330 at the first correction).
- `tests.tools.test_single_worker`: **91 of 92**. The one error is the
  unrelated concurrent W71918 import the reviewer already attributed:
  `source_profiles/checkpoints.py` does `from ..contracts import digest`, and
  `source_profiles` is copied into the worker image as a TOP-LEVEL package, so
  the relative import reaches beyond it. That is W71918's boundary and W71917's
  image rule; it is not this Work's to correct and no byte of it is in this
  candidate.
- `git diff --check -- v12`: no output.

The canonical parallel gate is not rerunnable in this tree: the same concurrent
candidate adds `tests.manager.test_checkpoint_profiles` and
`tests.manager.test_review_cycles`, which belong to no registry, so the runner
refuses before executing. Registering another leaf's suites is a classification
claim about work this Work does not own. The last gate run over a tree without
them was 528 shards, 3,686 tests, 6 failures, 0 errors, and it is reported as
what it is: evidence about that tree.

## 2026-09-05 — baton.claude — custody, and a proposal that can actually be imported

Two rounds of the same lesson, both about the difference between a package
that is internally consistent and a package an integrator can act on.

### The custody freeze

Every candidate and base FILE was `0444` and every directory was `0775`, which
on this filesystem means a read-only member can be unlinked or replaced. The
modes were a claim about immutability rather than immutability. All 43
directories in the package are `0555` now — the root, the timestamp directory,
`proposal/`, `base/`, `candidate/` and every intermediate — with the 40
evidence files still `0444`.

No byte changed and I proved it rather than asserting it: the proposal digest
recomputed by the recipe its manifest states, all 18 candidate members
recomputed from `candidate/`, and the patch and candidate-manifest digests
recomputed from their own files. All three came back identical.

### The path set: fifteen members, and the dossier deliberately outside it

The 18-path proposal sealed this record's `FINDING.md`, `PLAN.md` and
`PROGRESS.md` as importable members. That cannot work, and the reason is worth
writing down because it is a property of this dossier's own rules rather than
an accident of timing.

**Review evidence is append-only and lands in FINDING and PLAN.** So between
sealing a proposal and reviewing it, two of its own members necessarily move —
which is exactly what happened: the live FINDING and PLAN now differ from the
sealed snapshots while PROGRESS still matches. I reported that divergence
rather than hiding it, and the reviewer is right that reporting it does not
resolve it. An integrator preflighting the whole path set finds two targets
that match neither the declared base nor the candidate, so `baton.merge` must
refuse; and importing the snapshots anyway would delete the later review
findings and the current plan state.

**So the proposal is the fifteen production, test and runner members and
nothing else.** The dossier is preserved evidence, not import material:
`FINDING.md`, `PLAN.md`, `PROGRESS.md`, every `candidate-*.manifest`, every
`repro-*.py` and every `review-*.md` are named explicitly in the package's
exclusions so their absence is a decision a reader can see rather than an
omission they have to notice.

**No accepted member byte changed.** The fifteen are byte-identical to the ones
`sha256:d4cfef92…` bound; only the manifest, its path list and the patch — all
of which describe the set — are new. That is checkable directly against the
retained package rather than taken on trust.

And it resolves last round's awkwardness: PROGRESS.md was a sealed member, so
writing the custody act into it would have moved the digest and defeated the
custody-only recheck. It is outside the proposal now, so this entry can say
what happened.
