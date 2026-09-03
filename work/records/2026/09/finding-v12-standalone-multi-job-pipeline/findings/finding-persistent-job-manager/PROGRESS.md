# Progress

## 2026-09-02 — `baton.claude` (`impl`), W71875 implemented

Implemented the persistent host-side control plane as a new bounded package,
one tool entry point and a focused test directory. The verification vector

    env PYTHONPATH=v12/python/src PYTHONDONTWRITEBYTECODE=1 python3 -B \
      -m unittest discover -s v12/python/tests/job_manager -p test_*.py -v

passes: 123 cases, no failures or errors.

### Revalidation before editing

- **PLAN item 1 is settled and item 3 is deliberately narrowed.** The plan
  said "extend the manager store with only the scheduler-owned relations".
  Against the current tree that would mean adding tables to
  `worker_manager/schema.py` and moving `SCHEMA_VERSION` off 14, which is a
  store-format change for every existing manager deployment and for the
  manager's own regressions, for relations the manager itself never reads.
  `baton_v12/__init__.py` already rules that this distribution's products keep
  separate modules, files, connections, schemas and transactions, so the
  scheduler was given its OWN SQLite store
  (`baton.v12.python.job-manager`, schema 1). The manager's schema, version and
  tables are unchanged. This is the smaller honest reading of the same plan
  item; it is recorded here rather than in PLAN/FINDING because this Work's
  scope permits changing only PROGRESS among dossier files.
- **The composed surface was re-checked name by name** against the current
  `worker_manager` and `authority` exports rather than against the reviewer
  map: `issue_offer`, `submit_claim`, `recover_on_restart`,
  `claimed_offers_for`, `attempt_runtime_of`, `attempt_activity_of`,
  `frozen_output_of`, `ControlStore.operation_record`, `AuthorityPort`,
  `certify_profile`, and the `boundaries` / `documents` / `store` component
  modules. All exist and are public; none was reimplemented.
- **Path ownership.** Only new paths were created, plus one additive entry in
  an existing exhaustive registry (below). No file owned by another live
  proposal — `worker_manager/offers.py` and the manager tests named in
  `review-2026-09-02T21-41-35Z.md` — was touched.

### What was built

- `v12/python/src/baton_v12/job_manager/` — `documents.py` (versioned
  submission and status documents, closed vocabularies, stage-scoped
  dependency resolution and cycle refusal), `schema.py`, `store.py`
  (`JobStore`: ownership-before-adoption, one transaction boundary, byte-stable
  replay, durable/ordinary refusal split), `submission.py` (atomic,
  idempotent recording), `delegation.py` (the closed seam onto the public v12
  operations), `projection.py` (derived stage state, gates, status),
  `manager.py` (`reconcile`, `sweep`, `serve`).
- `v12/python/tools/job_manager.py` — `submit`, `status`, `serve`.
- `v12/python/tests/job_manager/` — `fixtures.py` and eight test modules.

### How the acceptance bullets are met

- **One documented JSON submission, atomically recorded.** `submit` writes the
  submission, its Jobs and its stages in one transaction under one derived
  operation identity. The document carries immutable input/policy digests,
  stage-scoped dependencies, requested runtime profiles, the bounded
  test-change scope and the terminal policy. The shape is written out in
  `documents.py`'s module docstring.
- **Idempotence and conflict.** An exact or differently-spelled resubmission
  replays the first outcome (the normalized document is what is signed);
  reusing a submission id for another intent collides at the journal; a Job
  identity already held by another submission refuses DURABLY, and the check
  runs before the first insert so the refusal keeps no partial pipeline.
- **Derived eligibility and dependencies.** No stage state is stored. It is
  computed from this store's receipts plus the manager's public reads, and a
  gate opens only on a `completed` predecessor.
- **Restart reconciliation.** Acts are delegated outside this store's
  transaction and the receipt is written afterwards from the manager's own
  journal row, keyed by an operation identity this build derives
  (`offer.issue:<offer_id>`, `offer.settle:<offer_id>`). A sweep adopts any
  committed act with no receipt before deriving anything, so a resumed process
  neither repeats a committed act nor skips an owed one.
  `test_delegation.CanonicalIdentities` drives the REAL operations and pins
  those spellings, and `_delegate` refuses if a performed act leaves no row
  under the derived name — so a future spelling change fails loudly instead of
  re-issuing offers forever.
- **Composition, not a shadow machine.** Every act is one public operation and
  every projected fact is one public read. There is no offer, claim, attempt,
  runtime or output column in this store.
- **Status.** `status` answers a versioned document projecting queued,
  blocked, offered, claimed, running, reviewing, changes-requested,
  integrating, completed and exceptional states with dependency gates, runtime
  identity, the manager's own artifact locators, the activity projection and
  the recorded receipts. Without a control store it reports `canonical: false`
  rather than an empty pipeline.
- **Containment.** One Job's durable refusal is recorded and does not stop an
  unrelated Job in the same sweep.

### Deliberate boundaries

- Two acts only, `admit` and `claim`. Runtime start, workspace and source
  delivery, review verdicts and integration are W71877/W71917/W71918/W71878;
  a stage waiting on one of those is projected honestly and owes nothing here.
- The bearer `issue_offer` answers with is minted, handed once to an injected
  delivery capability and dropped. A case asserts no row in either store
  contains it.
- No Git operation, no source walk or copy, no container, no TUI, no worker
  selection, no acceptance or integration decision.
- `serve` takes its clock, wait and stop predicate as capabilities; the tool
  imports the deployment's operations factory by an explicit
  `module:attribute` and constructs no authority session and mints no bearer.
- `changes-requested` is terminal for this leaf. Reopening the line is
  W71918's, and this leaf reports the closed gate rather than acting on it.

### Test-change authority used, and what was not touched

Within the scope this Work grants, only ADDITIONS were made under
`v12/python/tests`: the new `tests/job_manager/` directory. No existing test
was edited, deleted or weakened. One additive entry was appended to the
exhaustive registry in `v12/python/tools/parallel_test.py` — the eight new
modules in `PARALLEL_MODULES`, appended so no existing member moves — because
`tests/tools/test_parallel_runner.py` fails on any unregistered module.

### Observed, not caused, not repaired

Running existing suites while developing surfaced two conditions that predate
this change and belong to other Work:

- `tests.tools.test_quiescent_assignment_finalization` is in the tree and in
  neither registry, so `test_parallel_runner`'s completeness case fails. Its
  module is another live proposal's; registering it here would edit that
  proposal's path set.
- `tests.manager.test_attempts` (155 errors) and
  `tests.manager.test_boundary_inventory` (76 failures, 6 errors) abort on a
  missing dossier evidence file,
  `work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json`,
  which is absent from this working copy.

`tests.manager.test_dependencies`, `test_text_sweep`,
`test_diagnostic_rendering`, `test_offers` and `test_store` were run and pass;
they are the existing suites that scan or exercise the packages this leaf
composes.

Docker builds, `pip`, package installation, broad discovery and every Git
mutation were not run.

### State

Awaiting independent review.

## 2026-09-02 — `baton.claude` (`impl`), W71875 correction pass 1

`review-2026-09-02T22-58-43Z.md` accepted the sanitation and refused the
implementation on two fail-open identity/authority boundaries. Both are
corrected in the persistent run1 candidate line rather than by rerunning the
bootstrap: the workspace at `/tmp/w71875/run2/source` was seeded from the
retained run1 candidate (`prior-paths.txt`, byte-identical to the reviewed
sanitized candidate) over the same baseline
`23e1c5d771380bbaf9b16632f9dea03cdd7d3558`. No source was recloned, no
container was run, and no complete candidate tree was archived again.

### Revalidation before editing

- The two refused contracts were re-read against the candidate as it stands,
  not against the review's prose. `submission._stage` does derive
  `offer:{stage_id}` from the Job id and the stage kind alone;
  `manager._adopt`/`_delegate` did take any row under the derived id as this
  stage's act; `documents._paths` did apply `boundaries.text` only.
- `contracts.check_relative_path` is public, exported from
  `baton_v12.contracts`, and already refuses every spelling the review
  measured. It was reused rather than restated.
- `worker_manager.store.manager_signature` and `ControlStore.operation_record`
  are public, and `issue_offer` signs `offer_id`, `work_id`,
  `runtime_attempt_id`, `input_digest`, `policy_digest` and `profile_digest`
  among its operands — so the intent this store persists is comparable against
  the act the manager journalled without recomputing anybody else's facts.

### P1 — restart adoption could bind one store's offer to another's intent

The review offered two acceptable mechanisms; the one taken is **proving the
intent**, not pairing the stores. Pairing would have to be configured, an
operator can still point `--store` and `--control` anywhere, and a namespace
made unambiguous by construction would still collide when two stores choose
the same submission and Job identities. Proving the act is the property that
holds however the two paths were selected.

- `delegation.stage_intent` assembles the six offer operands this leaf owns
  from the two persisted rows, and `delegation.check_binding` compares them
  against the `offer.issue` record's signed operands. The other operands —
  participant, authority, the Work's frozen scope and route, the expiry — are
  deliberately not compared: this leaf neither supplies nor persists them.
- **The offer is the binding, so one check covers every act.** Both derived
  identities are keyed by the offer id, the settlement can only be journalled
  by settling that one offer row, and the canonical observation is keyed by the
  attempt id the offer froze.
- `projection.stage_states` performs the proof, which is the one pass the
  sweep's adoption, the derivation of what is owed and the status document all
  come through — so a mismatch is neither adopted as a receipt nor projected
  beside this store's Job. `manager._delegate` re-proves before adopting
  instead of performing, closing the window between the derivation read and
  the delegation decision.
- A mismatch refuses `refused/operation-collision` and names both accounts. A
  journal row whose signature this build cannot read refuses
  `integrity/schema` rather than being read as agreement.
- `submission.job_of` is the one public read of a Job row a stage names;
  `manager._job_of` is gone rather than duplicated.

### P1 — bounded test-change authority accepted paths outside its grammar

`documents._paths` now applies `check_relative_path` to every entry and
refuses duplicates through the existing `_unique` helper, so one scope set has
one durable spelling of each repository-relative path.

### Test-change authority used

Within this Work's granted scope, under `v12/python/tests/job_manager/` only:

- `test_documents.py`, `test_delegation.py`, `test_restart.py` — cases ADDED.
- `fixtures.py` — `FakeOperations` now signs its journal rows the way
  `offers.py` does, because a fake that signed `{}` would let every adoption
  case pass without the intent ever being compared. This is a fixture becoming
  more faithful, not an assertion being weakened; no existing case's expected
  behaviour changed and none was deleted.

No test outside `tests/job_manager/` was touched.

### Verification

Focused vector, unchanged from the reviewed one:

    env PYTHONPATH=v12/python/src PYTHONDONTWRITEBYTECODE=1 python3 -B \
      -m unittest discover -s v12/python/tests/job_manager -p test_*.py -v

136 tests, exit 0 (123 reviewed cases plus 13 new).

**Both corrections are mutation-proven.** Neutralizing `check_binding` fails 9
cases; restoring the old `_paths` fails 12. The regressions fail without the
fix rather than merely passing beside it.

Broad sweep, `PYTHONPATH=src python3 -m unittest discover -s tests -t .` from
`v12/python`, run twice: once on the candidate (2855 tests) and once on a
baseline tree with the candidate's 21 paths reverted to
`23e1c5d771380bbaf9b16632f9dea03cdd7d3558` (2719 tests). Both report 81
failures and 585 errors, and the 355 distinct failing test identities are the
SAME SET — the empty delta is the evidence, not the counts. Those failures are
this bounded source mount's, not the candidate's: it carries no
`v12/worker/` and none of the `work/records/2026/08/...` schema and vector
assets `tests.manager.test_frozen`, `test_attempts` and
`test_boundary_inventory` load. Evidence: `/tmp/w71875/run2/broad-sweep.txt`,
`/tmp/w71875/run2/broad-baseline.txt`, and the reverted tree at
`/tmp/w71875/run2/baseline-check` for the operator to re-derive.

Docker builds, `pip`, package installation and every Git mutation were not run.

### State

Awaiting independent re-review of the corrected immutable candidate.

## 2026-09-03 — `baton.claude` (`impl`), W71875 correction pass 2

`review-2026-09-03T00-22-09Z.md` accepted correction pass 1's provenance,
21-path reconstruction, sequential cross-store intent proof, normalized unique
test scope and recorded verification, and refused the candidate on one
remaining P1: a foreign offer that commits AFTER this store's proof read is
recorded as this Job's performed act. Corrected in the same persistent
candidate line at `/tmp/w71875/run2/source` over the same baseline
`23e1c5d771380bbaf9b16632f9dea03cdd7d3558`. No bootstrap rerun, no container,
no source reclone, no complete candidate archive. Two files changed.

### Revalidation before editing

- The reported window was re-read in the candidate as it stands rather than
  from the review's prose. `_delegate` did prove only the row its FIRST
  `receipt_of` returned; both post-call reads — the one after a refusal and
  the one after a returning call — assigned `record` and fell straight through
  to `_record`.
- **The same window was found one pass earlier, in `_adopt`.** Its docstring
  rested the proof on `stage_states`, which "built `held` immediately above".
  A stage whose offer is absent when that pass looks is answered `None` there,
  so a foreign row committing before `_adopt`'s own read was written as this
  store's `adopted` receipt on the strength of a check that ran before the row
  existed. This is the same fail-open and is inside the review's stated
  acceptance — a foreign winner must never be "reported as `performed`,
  `adopted`, or `refused` for this Job" — so it is corrected in this pass.
- `check_binding` was re-read and needed no change. It re-reads the
  `offer.issue` row itself, so calling it at a later instant proves the row as
  it stands at that instant; the defect was the set of call sites, not the
  check.
- The pinned ruling was re-checked and still holds: the offer is the binding,
  the proof lives in `projection.stage_states`, and store pairing stays
  rejected. This pass narrows nothing and reverses nothing in it.

### P1 — a foreign offer winning the read/call window was recorded as performed

Obtaining a canonical row and proving it are now ONE act. `manager._proved`
reads the journal and proves what it returns, absence stays absence, and every
read in `manager.py` goes through it — `_delegate`'s pre-call read, its single
post-call read, and `_adopt`'s adoption read.

- `_delegate` now makes ONE acquisition after the delegated call, whichever
  way the call answered. The two post-call read sites were what let one of
  them go unproved, so the call now decides only whether a missing row is
  `deferred` or a derived-identity fault, and the row itself is obtained and
  proved once. This also removes the exception-chained refusal the old shape
  would have raised from inside its own `except` block.
- `_adopt` proves each row at the read and no longer inherits the projection
  pass's proof.
- A foreign winner therefore raises `refused/operation-collision` naming both
  accounts, writes no Job-store receipt, and is reported as neither
  `performed`, `adopted` nor `refused` for this Job.

### Test-change authority used

Within this Work's granted scope, under `v12/python/tests/job_manager/` only,
and ADDITIVE: `test_restart.py` gains two deterministic seams (`WindowLoser`,
`LateWinner`) and one class of four cases. No existing case, assertion or
expected behaviour was changed, weakened or deleted, and `fixtures.py` is
untouched this pass. The seams are deterministic on purpose: the window is
microseconds wide, and a regression that fails only sometimes is not one.

The four cases are the foreign winner in a refused call, the foreign winner in
a RETURNING call (a build that proved only the refusal path would pass the
first and still record the second), the foreign winner before the adoption
read, and the negative control — this store's OWN offer arriving in the same
window is still recorded as `performed`, so the proof is about intent and not
about the window.

### Verification

Focused vector, unchanged in command from the reviewed one:

    env PYTHONPATH=v12/python/src PYTHONDONTWRITEBYTECODE=1 python3 -B \
      -m unittest discover -s v12/python/tests/job_manager -p 'test_*.py'

140 tests, exit 0 (136 reviewed cases plus 4 new).

**Mutation-proven, each half independently.** Restoring `_adopt`'s unproved
read fails 1 case; restoring `_delegate`'s unproved post-call read fails 2;
restoring both — the reviewed candidate's exact behaviour — fails exactly the
3 new race cases and nothing else. The negative control passes under every
mutation, which is what shows the cases fail for the intent and not for the
timing. Pass 1's corrections remain proven at the new count: neutralizing
`check_binding` fails 11 cases and errors 1.

Broad sweep rerun on the corrected candidate with the same command from
`v12/python`: 2859 tests, 81 failures, 585 errors, 14 skipped. The 355
distinct failing test identities are byte-identical to BOTH the recorded
baseline set (`broad-baseline.ids`, the tree with these 21 paths reverted to
the named base) and pass 1's candidate set (`broad-sweep.ids`) — the delta is
empty in both directions. Evidence: `/tmp/w71875/run2/broad-sweep2.txt` and
`/tmp/w71875/run2/broad-sweep2.ids`.

Docker builds, `pip`, package installation and every Git mutation were not run.

### Raised, not taken: the projection's own read window

`stage_states` proves the binding and then calls `operations.observe(stage)`,
which reads the manager keyed by `attempt:{stage_id}` — derived the same way
the offer id is. A foreign attempt materializing between that proof and that
read would be projected once by `status`. It is narrower than the corrected
defect and durably harmless — nothing is recorded, and the next sweep's
proof-at-the-read refuses — but it is the same shape, and closing it means
re-proving after the observation, which changes the projection pass the
FINDING's ruling deliberately placed. It is recorded in FINDING.md as an open
concern for a named later pass rather than taken silently inside this bounded
correction.

### State

Awaiting independent re-review of the corrected immutable candidate.

## 2026-09-03 — `baton.claude` (`impl`), W71875 correction pass 3

`review-2026-09-03T01-29-26Z.md` accepted correction pass 2's proof-at-read
mechanism, its package provenance and its focused evidence, and refused the
candidate on a distinct real-store P1: a canonical offer issued for another
Work can reuse this stage's derived attempt id, win the Worker Manager's
unique claimed-attempt slot, and make `status` persistently report this Job's
stage as `claimed` while its Job store holds only the `admit` receipt.
Corrected in the same persistent candidate line at `/tmp/w71875/run2/source`
over the same baseline `23e1c5d771380bbaf9b16632f9dea03cdd7d3558`. No
bootstrap rerun, no container, no source reclone, no complete candidate
archive; the workspace was edited in place after every one of its 21 paths was
verified byte-identical to the reviewed pass-2 candidate manifest.

### Revalidation before editing

- The reviewer's retained reproduction,
  `/tmp/w71875/review-distinct-offer-attempt-collision.py`, was run against the
  candidate as it stood. It passed — that is, the defect reproduced exactly as
  described: `status` answered `claimed`, `receipt_rows` held only `admit`, and
  the next `sweep` returned no acts, so nothing was ever going to correct it.
- The two identities were re-read in the tree rather than from the review's
  prose. `submission._stage` derives BOTH `offer:{stage_id}` and
  `attempt:{stage_id}` from the Job id and the stage kind;
  `delegation.check_binding` is keyed by the OFFER id; the observation was read
  by the ATTEMPT id. Only the first of the two was proved, and the second was
  the one `observe` used.
- `worker_manager.claimed_offers_for` already answers WHICH offers hold an
  attempt's claim; `observe` was discarding that and answering a boolean. The
  fact needed was already public, so nothing new was reached for.
- `schema.py`'s `offers_one_claim_per_attempt` unique partial index was
  re-checked: at most one claimed offer per attempt, which is what makes
  "whose claim is this" answerable at all. `attempts._claim_of` asks the same
  question the same way and fails closed on a store written before the index.
- The pass-1 and pass-2 rulings were re-checked and neither is narrowed or
  reversed here. The offer is still the binding for every ACT; what this pass
  adds is that an attempt-keyed OBSERVATION is not covered by that proof,
  because it is reached by a different derived identity.

### P1 — a distinct offer holding this stage's derived attempt id

The observation is now acquired and bound in ONE operation, and the boolean
that hid the defect is gone.

- `delegation.OBSERVATION_MEMBERS` replaces `claimed` with `claimed_by`: the
  offer id holding this attempt's claim, or `None`. "Somebody claimed it" and
  "this stage claimed it" are different facts, and a flag cannot tell them
  apart. `ManagerOperations.observe` answers the manager's own identity for it
  through `_one_claim`, which refuses `integrity/schema` rather than letting
  row order choose between two claimed offers in a store written before the
  unique index.
- `delegation.observation_of` is the one operation the projection calls. It
  proves the offer binding and then binds what the reader returned to it: a
  holder that is not this stage's offer refuses `refused/operation-collision`
  naming both offers and the attempt.
- **An unclaimed attempt carries no facts for this stage.** The claim is the
  only thing the manager holds that ties an attempt id to an offer — the
  runtime, the activity and the frozen result carry the attempt id and no
  offer at all, and it is the manager's own `activate_assignment` that refuses
  to run an attempt for anything but that attempt's committed claim. So
  `_bound` answers absence for all four members when nothing claims it, rather
  than reporting attempt-keyed observations nothing has bound to this Job.
- `projection.stage_states` makes one call where it made two. There is no
  unqualified attempt read left in this leaf for a later caller to reach.
- The refusal reaches `status`, `owed_acts` and `sweep` alike, because all
  three come through that pass. It is never recorded, never projected, and
  never answers an act this Job still owes — the empty owed set was what made
  the defect durable.

### Test-change authority used

Within this Work's granted scope and under `v12/python/tests/job_manager/`
only. Cases were ADDED and nothing was deleted; the edits to existing files
are the member rename following the corrected contract, and they are named
here individually rather than summarized:

- `test_restart.py` — ADDED `TwoOffersOneAttempt` (four cases, real stores,
  the reviewer's composition) and `AnUnclaimedAttempt` (two cases). No
  existing case in the file was touched.
- `fixtures.py` — `FakeOperations` answers the corrected observation shape.
  `observed(stage_id, claimed_by=True)` means "this stage's own offer holds
  the claim" and the fixture spells the identity, so no case carries the
  derivation. This is a fixture tracking the real reader, as pass 1's
  signature change was; a fake still answering a boolean would let every case
  pass without the holder ever being compared.
- `test_status.py` (3 sites), `test_sweep.py` (2 sites) — the keyword
  `claimed=True` becomes `claimed_by=True`. No assertion, expected state or
  case was changed.
- `test_delegation.py` (2 sites) — the two exact-equality assertions on the
  observation document now name `claimed_by: None` where they named
  `claimed: False`. Both remain exact-equality over the whole document; the
  contract they assert became stricter, not weaker.

No test outside `tests/job_manager/` was touched, and no existing case's
expected behaviour was weakened or removed.

### Verification

Focused vector, unchanged in command from the reviewed one:

    env PYTHONPATH=v12/python/src PYTHONDONTWRITEBYTECODE=1 python3 -B \
      -m unittest discover -s v12/python/tests/job_manager -p 'test_*.py'

146 tests, exit 0 (140 reviewed cases plus 6 new).

The reviewer's own retained reproduction now refuses at the projection instead
of answering `claimed`, with the collision naming
`offer:foreign-job/implementation`, `offer:job-a/implementation` and
`attempt:job-a/implementation`.

**Mutation-proven, each half independently**, against the candidate rather
than by hand-reading:

| mutation | result |
| --- | --- |
| holder comparison neutralized | failures=3 — exactly the three foreign-claim cases |
| unclaimed-attempt gating neutralized | failures=1 — the unbound-runtime case |
| both, i.e. the reviewed pass-2 observation | failures=4 — exactly the four new negative cases |
| pass-1 `check_binding` mismatch refusal neutralized | failures=6 |
| pass-2 `_adopt` unproved read restored | failures=1 |
| pass-2 `_delegate` unproved reads restored | failures=2 |

`test_this_stores_own_offer_taking_its_attempt_is_still_projected` — the
POSITIVE CONTROL, the same attempt id and the same claimed slot with this
store's own offer in it — passes under every mutation above. That is what
shows the negative cases fail for the identity and not for the presence of a
claim, and it is the case a correction that refused every claim would break.

Broad sweep rerun on the corrected candidate with the same command from
`v12/python`: 2865 tests, 81 failures, 585 errors, 14 skipped. The 355
distinct failing test identities are identical to BOTH the recorded reverted
baseline set (`broad-baseline.ids`) and pass 2's candidate set
(`broad-sweep2.ids`) — `comm -3` is empty in both directions. Evidence:
`/tmp/w71875/run2/broad-sweep3.txt` and `/tmp/w71875/run2/broad-sweep3.ids`.
The test count rose by exactly the 6 cases added here.

Docker builds, `pip`, package installation and every Git mutation were not run.

### Raised, not taken: the claim call's own window

`sweep` now refuses before deriving or delegating anything when a foreign
offer holds this stage's attempt, so `_delegate` cannot reach `submit_claim`
under a known collision. A foreign claim committing in the microseconds
BETWEEN that refusal-free projection and this store's own `submit_claim` is
not closed here: the manager's `offers_one_claim_per_attempt` unique index
rejects the second claim, so the outcome is a hard integrity error from the
manager's own boundary rather than a false projection or a shadow receipt.
Closing it means holding a lock across another package's transaction, which is
a redesign of the delegation seam this bounded correction was not asked to
make. Recorded in FINDING.md and PLAN.md for a named later pass; it cannot
falsify this pass's acceptance, because it produces no state at all.

### State

Awaiting independent re-review of the corrected immutable candidate.
