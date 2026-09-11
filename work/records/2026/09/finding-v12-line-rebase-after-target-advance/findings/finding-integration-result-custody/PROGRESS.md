# Progress

No implementation started. Reviewer133108 created this dossier with Work133117.
Actual change authors append attributable entries under their claims.

## claim133218 — the gate is proved and the standalone profile is real

IN FLIGHT. This entry exists so the state is resumable from the record rather
than from a context: the claim is held and the remaining P scope is listed at
the end.

**Baseline revalidated first.** All 43 post-D paths in
`../finding-target-rework-custody/evidence/review-133171/result.json` agree by
digest and mode, including the five recorded absences, and the three planned-new
P files were absent.

**1. The mandatory Authority-publication gate: EXPRESSIBLE.** Recorded in
FINDING at 2026-09-10T03:44:36Z with the probe retained at
`evidence/gate-133218-probe.py` and its answers at
`evidence/gate-133218-authority-publication.json`. Static: `publish` is in the
session's closed transition table with `target` OPTIONAL, sits in
`_ASSIGNMENT_FIRST`, and carries no `actor` flag, so it is authorized by the
assignment compare-and-swap rather than a capability grant. Against a REAL
Authority: the integrator publishes a derived proposal under its OWN live
assignment, with a new frozen result identity, the combined candidate and an
explicitly pinned target snapshot; it reads back through the ordinary reader,
an exact retry replays it, the producer's original proposal is untouched, and
borrowing the producer's result identity refuses. No amendment is needed and no
Authority edit is proposed. **0.05s.**

**2. `src/baton_v12/integration/git_profile.py` (new, 0o664),**
sha256 `97f90ab9c573da4cd578062320736b0f3bdbe77bbbb4ee64ffc3d4397b027864`.

Standalone by construction: it imports only the standard library and its own
refusal, so the same primitives can be copied into an integration worker image
without carrying a manager, Authority, store or coordinator capability across
that boundary. It writes in exactly two places — objects and prepared
references under the nominated private storage, and the dedicated target at one
explicitly configured reference through a compare-and-swap. `merge-tree
--write-tree` reads three commits and writes one tree, so no index, worktree or
HEAD is an operand and the producer's line cannot be one. Symlinks and
submodules refuse at the content reader rather than at the import.

Proved by a focused real-repository probe, retained at
`evidence/profile-133218-probe.py`: Job B's ORIGINAL submission — never rebased
— reconciles with the snapshot Job A's integration produced; the prepared
result carries BOTH changes; the submission is untouched; an exact replay
answers the identical evidence rather than merging twice; the configured
reference advances by compare-and-swap and a STALE swap refuses with Git's own
words; and a real conflict HOLDS with its exact path while retaining nothing.
**0.23s.**

**Cost so far: 0.33s of the 77s author allocation**, every run wall-timed.

**Remaining P scope, in dependency order:** integration `schema.py` schema-5
fresh-store boundary and the typed reconciliation relation; `store.py` reader
support; `reconciliation.py` with `prepare_result`, `result_of`,
`record_result_evidence`, `publish_result` and `resolve_import_account`;
`admission.py`/`driver.py` separation of source eligibility from the import
account; `__init__.py` exports; and `tests/integration/test_reconciliation.py`
with the six required named groups plus the causal base-fail / isolated-pass /
combined-pass and combined-fail observations, with `test_admission`,
`test_driver` and `test_coordinator` compatibility selectors.

## claim133275 — schema 5 and the typed result relation

STILL IN FLIGHT. The previous claim133218 was released by the owner at
2026-09-10T03:50:43Z as Incident47, "ACP turn ended and no execution remains",
preserving partial work, evidence and budget history. It did: the baseline
revalidated clean at this claim's start and `git_profile.py` survived intact.
The lesson is a cadence one and I am applying it -- each increment ends with a
durable record here, so an orphaned claim costs a redelivery and nothing else.

**Baseline revalidated at claim start.** All 43 post-D paths agree by digest and
mode. `git_profile.py` is present as this Work's own new file; the other two
planned-new P paths remain absent.

**3. `src/baton_v12/integration/schema.py` -> `5316631cbba56ba941040612c692021a8f029cee5ec5f660755b7ab0d4b9e4c9` (0o664).**

Schema 5 with the `integration_results` relation. It reaches the fresh-store
boundary the same way version 4 already does -- a database at another version
is refused rather than guessed across, and no migration is invented -- because
a schema-4 store has no relation these facts could live in and no way to tell a
direct import from a reconciled one after the fact.

The relation is built around the contract's central distinction. It NAMES the
original submission -- line, checkpoint, verdict, proposal, frozen result,
base and candidate -- as immutable references it never rewrites, and owns only
what belongs to the RESULT: the prepared content, the pinned target snapshot,
its own verification/review/approval evidence and its own derived Authority
proposal. Its CHECK constraints make the contract structural rather than
advisory: a reason belongs to a hold and nothing else; prepared content is
absent until there is some; a result cannot be `authorized`, `published` or
`imported` without its OWN evidence recorded; a published result must name its
own derived proposal, never the producer's; and `UNIQUE (canonical_target_id,
source_proposal_id, target_revision)` is what makes a later target advance a
NEW result from the same submission rather than a mutation of this one.

Verified: the DDL executes, the table set matches `TABLES` exactly, and the 33
persisted columns match the `RESULT_COLUMNS` contract with no mismatch either
way. **0.14s.**

**4. `tests/integration/test_coordinator.py` -> `7fb6ec2c3af86b1ed7920aca57cdf348afa68bbab86101acda4fd2b4930243ea` (0o664).**

One test changed:
`test_the_expectation_is_measured_from_the_schema_it_checks` compared
`expected_shape()` against a RETYPED table literal, which is the second owner
of the shape its own docstring warns about. It now asserts against the module's
own `TABLES`, plus that the new relation is in it. The
`TheStoreIsAdoptedByOwnershipRatherThanResemblance` and `ReadOnlyOpening`
selectors pass at 27 tests. **0.22s** (plus 0.22s and 0.20s for the two
iterations that found the retyped literal and then the wrong import path).

**Cost so far: 1.11s of the 77s author allocation**, every run wall-timed.
Carried forward from claim133218: the Authority-publication gate (EXPRESSIBLE,
0.05s) and `git_profile.py` proved by real repositories (0.23s), both recorded
above with retained probes at `evidence/gate-133218-probe.py` and
`evidence/profile-133218-probe.py`.

**Remaining P scope, unchanged in order:** `store.py` reader support;
`reconciliation.py` with `prepare_result`, `result_of`,
`record_result_evidence`, `publish_result` and `resolve_import_account` --
built on this store's `replay(..., witness=)` seam, which already REQUIRES a
semantic owner to re-prove a materialized act and is exactly the discipline
slice A's R3 lacked; `admission.py`/`driver.py` separation of source
eligibility from the import account; `__init__.py` exports; and
`tests/integration/test_reconciliation.py` with the six required named groups
plus the causal base-fail / isolated-pass / combined-pass and combined-fail
observations.

## claim133318 — the custody owner's intent, outcome and reader binding

STILL IN FLIGHT. claim133275 was released as orphaned the same way claim133218
was; the durable record carried the state and the baseline revalidated clean
again at this claim's start.

**5. `src/baton_v12/integration/reconciliation.py` -> `544b220c30e8422b7ac60dfbc3817837a66d37f2745c9e69212c443dcaf46d72` (0o664).**

`prepare_result`, `result_of` and `result_identity`, with the three defects the
superseded slice's review found built in from the start rather than bolted on.

**Intent is not outcome (R2's correction).** A committed INTENT records that
this exact submission is being reconciled onto this exact pinned revision in
this exact workspace under this exact assignment. A retry finding an intent
with no outcome RESUMES -- it asks the profile again, with the ORIGINAL
recorded target, and the profile validates and reuses whatever it already
retained instead of reconciling twice. Only a settled OUTCOME replays. The
superseded slice answered "already done" and called the profile zero times.

**Operands are recovered, not recomputed (R4's correction).** The profile is
asked with the record's own operands read back from the row, so a resume cannot
select a later target; and because the pinned revision is part of the derived
identity, a target that HAS moved yields a different record and leaves the
earlier one exactly as it was -- which is the contract's own rule that a later
advance is a new result from the same submission.

**Readers bind by re-derivation (R3's correction).** `result_of` adopts the row
against its closed column contract, adopts each nested document against its
own, RE-DERIVES the result identity from the fixed operands the row itself
carries, and requires the journal operation the row names to be recorded under
the signature those same operands produce. Row existence proves neither.

**Proved by a focused real control**, retained at
`evidence/reconciliation-133318-probe.py`, over a real coordinator store, real
repositories and the real profile: an ordinary preparation pins the target and
carries BOTH changes with the submission untouched; an exact retry is
identical; a committed intent whose outcome was removed RESUMES to the same
target and the same content; an edited row is REFUSED and reads again once
restored; and a submission already based on the target refuses. **0.23s.**

One honest note for the test module rather than a claim here: the edited-row
control above was caught by the prepared-evidence target check, which fires
before the identity re-derivation. The required `ResultReadersRejectTampering`
group must alter a member that is NOT in prepared evidence -- a source verdict
or proposal identity -- so the identity binding itself is exercised rather than
assumed.

**Cost so far: 2.12s of the 77s author allocation**, every run wall-timed.

**Remaining P scope:** `record_result_evidence`, `publish_result` and
`resolve_import_account` in this module; `store.py` reader support if the
readers above need it; `admission.py`/`driver.py` separation of source
eligibility from the import account; `__init__.py` exports; and
`tests/integration/test_reconciliation.py` with its six required named groups
plus the causal base-fail / isolated-pass / combined-pass and combined-fail
observations.

## claim133353 — the custody owner's five public operations are complete

STILL IN FLIGHT. Same orphaned-claim cycle as before; the durable record
carried the state and the baseline revalidated clean at this claim's start.

**`src/baton_v12/integration/reconciliation.py` -> `4e5c9e2185f184d2e718e05309f143c76691767c64845b669ef23300147793f6` (0o664).**
`record_result_evidence`, `publish_result` and `resolve_import_account` join
`prepare_result`, `result_of` and `result_identity`. All five of
CONTRACT-v1 section 3's operations now exist.

**Evidence is about THESE bytes or it is not this result's.** Each of the three
documents names its own kind, identity, actor, disposition and the CONTENT
DIGEST it was given about, and that digest must be this result's prepared
content. No caller supplies an approval as a boolean and no producer receipt is
copied: the producer's verification, review and approval prove the SUBMISSION
and say nothing about bytes that did not exist when they were recorded. One
actor may not give two of the three, because independence is what they are for.

**The derived proposal is the result's own.** Published under the INTEGRATION
role's live assignment, with a frozen result identity this record derives, the
combined candidate and the pinned snapshot as its target -- exactly what the
gate proved expressible. Only an authorized result publishes.

**The import account re-proves rather than remembers.** Content is revalidated
against the workspace, evidence re-read, and the dedicated target's CURRENT
revision compared with the snapshot the result was prepared onto. The account
carries BOTH identities: the original submission's proposal and the derived
one.

**Proved against a REAL Authority**, which is the focused real-Authority path
the dossier requires, retained at `evidence/operations-133353-probe.py`.
Thirteen facts hold: publishing before evidence refuses; evidence about other
bytes refuses; one actor giving two judgements refuses; the authorized result
publishes; the derived proposal names the integration assignment, the pinned
snapshot, the combined candidate and its OWN result identity rather than the
producer's; the publish retry is identical; the import account keeps the source
proposal and names the derived one; and a target that moved AGAIN refuses the
import with the stale-result guard the contract keeps rather than removes.
**0.23s.**

**Cost so far: 2.54s of the 77s author allocation**, every run wall-timed.

**Remaining P scope:** `admission.py`/`driver.py` separation of source
eligibility from the import account; `__init__.py` exports; `store.py` reader
support if needed; and `tests/integration/test_reconciliation.py` with the six
required named groups -- OriginalSubmissionIsImmutable,
CausalEvidenceSurvivesComposition, PreparedResultReplaysItsIntent,
ResultReadersRejectTampering, DerivedPublicationUsesItsOwnAssignment and
ConflictsAndForeignSourcesHold -- plus the causal base-fail / isolated-pass /
combined-pass and combined-fail observations, with the named
`test_admission`/`test_driver` compatibility selectors.

## claim133645 — the separation, the exports and the required test module

STILL IN FLIGHT. claim133353 was released at 2026-09-10T04:40:02Z under
W133361/owner133489's reviewed preservation manifest, which binds 20 P
source/test/dossier entries. All of them survived.

**Baseline revalidated at claim start.** Every one of the 43 post-D paths in
`../finding-target-rework-custody/evidence/review-133171/result.json` agrees by
digest and mode EXCEPT two, and neither is drift into this scope:

- `AGENTS.md` moved `67cc573e…` -> `a7323bbc…` (0o664 both). That is
  W133361's independently reviewed policy correction, reviewed at
  `review-2026-09-10T04-32-48Z.md`, and it is not a P path.
- the four P paths this Work owns are exactly the recorded bytes:
  `git_profile.py` `97f90ab9…`, `schema.py` `5316631c…`,
  `reconciliation.py` `4e5c9e21…`, `test_coordinator.py` `7fb6ec2c…`.

The recorded absences (`worker_manager/target_rework.py`,
`tests/manager/test_target_rework.py`) are still absent; the one planned-new P
path still absent is `tests/integration/test_reconciliation.py`.

### DESIGN PINNED BEFORE EDITS — how the separation can and cannot be made

CONTRACT-v1 section 6 asks admission/driver to separate source eligibility
from the import account while "existing direct imports retain their old
exact-target path". Two facts in the tree decide the shape, and both were
checked rather than assumed:

1. `tests/tools/test_integration_bundle.py`'s
   `test_the_eligibility_members_are_the_admission_owners_own` reads
   `inspect.getsource(admission.resolved_account)` and requires all fifteen
   `ELIGIBILITY_MEMBERS` to appear there. The account's dict LITERAL must
   therefore stay lexically inside `resolved_account`.
2. `tests/integration/test_execution.py`'s
   `test_the_refusal_records_what_the_producers_said` moves the canonical
   target and asserts the settled detail says "expected target revision" --
   which is `resolved_account`'s own refusal. `resolved_account` must
   therefore KEEP proving freshness.

Both files are Q scope and neither may be edited here. So the separation is
ADDITIVE, and removing the guard from `resolved_account` -- the "one-line
guard removal" INTEGRATION-SCOPE-v1 warns about -- is exactly the thing the
tree already refuses.

- `_proved(...)` (new, private): the single resolver. Every producer read and
  every cross-binding, with the current-target comparison under a `freshness`
  flag. One reading of the sources, not two.
- `resolved_account(..., freshness=True)`: unchanged public name, unchanged
  default behaviour, unchanged fifteen-member literal. Documented for what it
  has always been -- the DIRECT IMPORT account, eligibility plus the exact
  current target.
- `source_account(...)` (new public): the same fifteen members with freshness
  NOT proved. This is the account a result branch consumes, and its
  `expected_target_revision` is the submission's own declared base rather
  than a claim about the present.
- `source_submission(...)` (new public): the twelve-member operand
  `reconciliation.prepare_result` takes, composed from `_proved`'s own
  documents -- `job_id` from the accepted Job and `source_base`/
  `source_candidate` from the accepted checkpoint evidence's `base`/`head`,
  which are the two objects the fifteen-member account does not carry and
  which cannot be added to it here (that closed account and its worker
  contract are versioned in Q).
- `driver._import_account(...)` (new private): the one seam where driver
  decides which account an import acts on -- the admitted one when the entry
  has already settled, otherwise `resolved_account`. Four call sites collapse
  onto it. No behaviour changes; Q's serial extension gets one place to add
  the result branch instead of four.
- `__init__.py`: export the new owners -- `reconciliation`'s five operations
  plus `result_identity` and its four operation kinds, `git_profile`'s
  profile/refusal/name/version, and admission's `admit_candidate`,
  `resolved_account`, `source_account`, `source_submission`.

### Test paths and reasons, pinned before edits

- `tests/integration/test_reconciliation.py` (new): the six required named
  groups, over a REAL coordinator store, REAL repositories, the REAL profile
  and a REAL Authority, plus the causal base-fail / isolated-pass /
  combined-pass and a separate combined-fail observation produced by actually
  running a harness against the three content states.
- `tests/integration/test_admission.py`: the named `AcceptedAccount` and
  `RefusalBeforeMutation` compatibility controls stay as they are --
  `test_stale_target_refuses` is the proof that the direct path kept its
  exact-target rule -- and gain the control that `source_account` answers the
  SAME account when the target has moved, which is the separation itself.
- `tests/integration/test_driver.py`: `TheOrdinaryCommandTraversesPublicAdmission`
  is the compatibility control and is not edited.
- `tests/integration/test_coordinator.py`: already changed at claim133275.

### What this claim actually did

**6. `src/baton_v12/integration/admission.py` -> `93b803004608b289dc43a65bba467ea280658896e7a4fbd777c6be816d000791` (0o664).**

`_proved` is now the one resolver; `resolved_account` keeps its name, its
default behaviour and its fifteen-member literal, and gains `freshness` as the
keyword that says WHICH of the two questions a caller is asking.
`source_account` is that same account proved as eligibility alone, and
`source_submission` is the twelve-member operand `prepare_result` reconciles.

The two Q-scope facts recorded in the design above are the reason it has this
shape rather than the obvious one, and both were re-run rather than assumed:
`TheThreeSpellingsOfOneProtocolAgree` still finds all fifteen members in
`resolved_account`'s own source, and `StaleEvidenceEarnsTheRULEDVerb` still
settles a moved target with "expected target revision" in its recorded detail.

**7. `src/baton_v12/integration/driver.py` -> `c5a86008a96f773c0fa884cb7b501197dc29d20eaa638f90957f47e17737bf3e` (0o664).**

`_import_account` is the one place driver decides which account an import acts
on: the admitted one when the entry has already settled, otherwise
`resolved_account`. Four call sites across `admit_accepted` and
`continue_accepted` collapse onto it. No behaviour changed -- this is the seam
Q's serial extension adds the result branch to, instead of four.

**8. `src/baton_v12/integration/__init__.py` -> `df626826ed4a6348da135229c12fb7e6a0fd01ecbcf5a2508f862a6f3b915e36` (0o664).**

The new owners are exported: admission's four names, the standalone profile
with its refusal and identity, and reconciliation's five operations plus
`result_identity` and the four operation kinds. `store.py` needed NO reader
support and is unchanged at `8117df2b43ed702d…` -- reconciliation reads through
the existing `replay(..., witness=)` seam and the store's own connection, which
is the discipline the superseded slice's R3 lacked.

**9. `tests/integration/test_reconciliation.py` (new, 0o664),**
sha256 `a103d95a2b537b64745cab32bbfc887f50b70615a6874ee2189243d04a80e058`.

Thirty-one cases in the six required named groups, over a real coordinator
store, real repositories, the real profile and a REAL `Authority` with an
actually claimed integration assignment.

- `OriginalSubmissionIsImmutable` -- the producer's line head, candidate tree,
  refs, worktree status and Authority proposal are compared before and after a
  full preparation/authorization/publication/import-account pass and are
  identical; the prepared content carries BOTH Jobs' changes; the old base is
  kept while the RESULT's target stays exact.
- `CausalEvidenceSurvivesComposition` -- one harness pinned once and actually
  RUN against three content states, plus the separate combined-fail control,
  plus the control that an unrelated setup failure is a different observation
  from the defect's baseline failure.
- `PreparedResultReplaysItsIntent` -- an exact retry asks the profile nothing
  and writes no second commit; a reopened intent RESUMES on the record's own
  target while the target moves underneath it; a moved target is a new result
  and the old one reads back byte-identical.
- `ResultReadersRejectTampering` -- the edited members are the ones prepared
  evidence never carries, which is the honest note claim133318 left for this
  module: `source_verdict_id`, `source_proposal_id`, `source_checkpoint_id`,
  `job_id` and `line_id` are caught by identity RE-DERIVATION rather than by
  the earlier target check. A row pointed at another committed act, a state its
  own operation never reached, an edited content digest, edited evidence and a
  row whose act is not in the journal at all are each caught too.
- `DerivedPublicationUsesItsOwnAssignment` -- against the real Authority.
- `ConflictsAndForeignSourcesHold` -- a real conflict, a held result that
  neither authorizes nor publishes and replays as the same hold, a submission
  already based on the target, an unreachable object, an assignment naming
  another Work, and an uncertified profile that is never asked anything.

**10. `tests/integration/test_admission.py` -> `c33ddf9f4aabcc8f9a34c714c3434e519602c4b3984e00b74c7f35df242e6cce` (0o664).**

`SourceEligibilityIsNotResultFreshness` is the separation itself: with the
target moved, `resolved_account` refuses with "expected target revision" and
`source_account` answers the SAME fifteen members it answered before. The
matrix beside it proves the source account is not a weaker proof -- a broken
frozen result, checkpoint, assignment, Job or any missing policy receipt
refuses it exactly as it refuses the import account. `AcceptedAccount` and
`RefusalBeforeMutation`, including `test_stale_target_refuses`, are untouched
and are the other half of the same rule.

### The causal witness, in its own words

`evidence/causal-133645-observations.json`, produced by
`evidence/causal-133645-observations.py`. One harness digest
`sha256:7c3bb835…` across all four runs:

- base, harness ADDED (it is not on the old base): exit 1,
  `AssertionError: total answered 5`
- isolated: exit 0, `the regression harness passed`
- combined with the first Job: exit 0, `the regression harness passed`
- combined-fail control, after a third Job changes `scale.py`: exit 1,
  `AssertionError: total answered 12`, and it is a DIFFERENT result id, with
  the earlier record reading back unchanged and the isolated positive intact.

### Verification

`evidence/result-133645.json` and `evidence/run-133645-final.log`. Consolidated
focused run: **125 tests, OK, 3.09s wall.** Selectors are the new module, the
three named `test_admission` classes, five `test_driver` classes that reach the
call sites this claim changed, two `test_coordinator` classes, and the two
Q-scope controls that bind to `resolved_account`. No whole-package, broad, live
or OCI run.

**Cost: 6.95s this claim, 9.49s cumulative of the 77s author allocation.**
Every setup, failing and rerun subprocess is inside those measured runs; each
one is listed individually in `result-133645.json`. Independent review 0/8s.

### P is complete and is returned for independent review

Every path in P's accepted allowlist is either changed and recorded above or
deliberately unchanged (`store.py`). All six required test groups exist with
their required names. The mandatory Authority-publication gate was proved
EXPRESSIBLE at claim133218 and needed no amendment. Q and R remain gated until
this exact candidate is independently accepted.

## claim133842 — the four review blockers, corrected

Candidate133645 was NOT accepted. `review-2026-09-10T05-14-36Z.md` reproduced
three P1 defects and one P2 with a real probe, and recorded a ledger and a
scope limitation. Everything below answers those and nothing else; the
reviewer's own probe and its output are preserved untouched.

**Baseline at claim start.** All eleven manifest paths matched the review's
`evidence/review-133787/result.json` before any edit.

### 1 (P1) — evidence did not bind result bytes

`git_profile.content` read each blob's object name and threw it away, so a
prepared result's "content" was a PATH AND MODE MAP. Two combined trees over
the same four file names therefore digested identically, and the first
result's passing verification/review/approval authorized the second, failing
one. The reviewer's two trees were `470da0d3…` and `e20369ea…`.

`content` now answers `{path: {"mode", "object"}}` -- the object name was
already on the same line of the tree listing -- and `_prepared` adopts that as
a closed shape. The same two trees now digest to
`sha256:853979c7…` and `sha256:c22a68f6…`; they no longer collide, and the
probe output is `evidence/correction-133842-probe.json`.

Evidence is bound four ways rather than one: each judgement names this
RESULT's identity, its content digest, the combined candidate and the pinned
target. Reusing the first result's judgements for the second now refuses with
`integrity/digest`.

### 2 (P1) — provenance and owner evidence were caller-written

`prepare_result` took a `submission` DOCUMENT, so the probe supplied proposal
`never-published`, a checkpoint and verdict nobody created, an unconfigured
verifier and the integration preparer as its own reviewer, and reached a real
derived publication.

- `prepare_result(store, profile, manager, jobs, authority, *, line_id,
  proposal_id, ...)`. The submission is RESOLVED through
  `admission.source_submission` -- which is what CONTRACT-v1 section 3's own
  conceptual signature says -- so the accepted checkpoint, its writer's
  assignment and frozen output, the Authority proposal with its three real
  policy receipts, and the Job that owns the input/policy/scope are all read
  and cross-bound. `never-published` now refuses with the Authority's own
  sentence, `the Authority refused the proposal read: no such proposal`.
- `record_result_evidence(store, verification, reviewer, approver, *,
  result_id, observations)`. The three are INJECTED OWNERS with a participant
  and a capability, asked with a question this record derives; the recorded
  actor is the owner's own participant. `driver._receipt` asks the
  submission's configured sessions the same way. An owner that answers for
  somebody else, one that has no capability, one that returns a non-accepting
  disposition, and the PREPARER offering its own review all refuse.
- The three causal observations are recorded IN THE ROW. Section 3 requires
  original causal observation references and the reviewer was right that a
  dossier JSON is not runtime custody. They are cross-bound to the
  submission's base, its candidate and this result's own prepared tree; one
  pinned harness is required across all three; `harness_added` must be true on
  the base and false on the other two; and a combined FAILURE blocks
  authorization rather than being verified away.
- `resolve_import_account(store, profile, manager, jobs, authority, *,
  result_id)` re-resolves the submission and refuses naming the member that
  moved.

### 3 (P1) — later readers discarded earlier custody

`result_of` compared only the NEWEST operation's signature, so everything an
earlier act settled was unguarded once the record moved on. `_KIND_FOR_STATE`
is replaced by `_CHAIN_FOR_STATE`: every act a record in a given state must
have passed through is re-derived from the row AS IT STANDS NOW. The reviewer's
three counterexamples all refuse:

- prepared head/tree replaced under an AUTHORIZED row -> the outcome act's
  signature no longer matches;
- evidence emptied to `{}` under a PUBLISHED row -> the evidence act's
  signature no longer matches, and the import account refuses with it;
- `imported` with no entry -> the schema will not hold the row at all
  (`CHECK constraint failed: (state = 'imported' AND entry_id IS NOT NULL)`),
  and the reader refuses it independently.

The schema also now requires evidence and causal observations to commit
together and the derived proposal members to be absent unless published, so a
published row cannot be quietly demoted either.

### 4 (P2) — exact retries refused after progression

`_outcome_signature` derived the outcome's signature from whatever state the
row had reached SINCE, so an identical `prepare_result` after authorization
compared against a signature nothing ever recorded. `_settled_state` recovers
the state the OUTCOME act actually settled. `record_result_evidence` asks the
owners first and compares the signature THEY just produced, so an identical
retry replays at every cutpoint while a call with a changed owner or
observation still collides. All four replay points and the changed-operand
collision are in `evidence/correction-133842-probe.json`.

### Candidate

Changed under this claim, 0o664: `git_profile.py`
`cba3f391405249f6df83985ff6c5d715ef3cec05efa85ce345cce929f90db1fb`,
`schema.py`
`8a6fa58b2be16f61d049179225784da9e4be6f9511198963b2bf5f1b2fe66c09`,
`reconciliation.py`
`83ea3fef7f9e273ba378a5592570224d37bb7783d60fafe1d605bb83764ca214`,
`tests/integration/test_reconciliation.py`
`9db74835bc9344d16626bcb00cd71eaccd823398cb29bca6f84a1a62267373d6`.
Unchanged from candidate133645: `admission.py` `93b80300…`, `driver.py`
`c5a86008…`, `__init__.py` `df626826…`, `store.py` `8117df2b…`,
`test_admission.py` `c33ddf9f…`, `test_driver.py` `ff064265…`,
`test_coordinator.py` `7fb6ec2c…`. Full digests, modes and sizes are in
`evidence/result-133842.json`.

The new test module keeps the six required group names and adds two:
`TheSubmissionIsResolvedFromItsOwners` and
`TheEvidenceIsItsOwnersAndBindsTheseBytes`, which are blockers 1 and 2's
regression controls.

**An honest boundary the reviewer should weigh.** The Worker Manager's
checkpoint/writer/frozen-output readers and the Job rows are patched in these
cases exactly as `test_admission` patches them; the Authority, its proposal,
its three policy receipts, the repositories, the profile and the coordinator
store are all real. Standing up a manager fixture is not in P's accepted
scope. Everything admission cross-binds BETWEEN those producers still runs.

### Verification

143 tests, OK, 5.72s wall, retained at `evidence/run-133842-final.log`. Every
selector names a CLASS. INTEGRATION-SCOPE-v1 prohibits whole-module selection
and the reviewer was right that claim133645 violated it twice; that is
acknowledged rather than cured by having passed, and it is not repeated here.

### Ledger

Measured this claim 14.96s across ten runs, three of which FAILED and are
listed individually with their failure in `evidence/result-133842.json`.
Measured earlier claims 9.49s. **Measured subtotal 24.45s of 77s.**

This is a rounded MEASURED SUBTOTAL PLUS UNMEASURED SPENDING, not a certified
exact total and not a grant of any exact remainder. Unmeasured, this claim:
greps and file reads, `ast.parse` syntax checks, the in-place edit scripts,
the hash/manifest commands. Unmeasured, earlier claims: the eleven
hash/preflight/manifest commands the reviewer indexed, and the failed pytest
launch at 2026-09-10T04:52:41.264Z whose displayed `ELAPSED` was 0.00 and
which `result-133645.json` omitted -- it is counted here as a real failure
with an unrecoverable duration. Several original outputs were piped to `tail`
and cannot be recovered; they are marked unavailable rather than re-run.
Nothing was reset, inferred, repeated to manufacture history, or borrowed.

## claim134000 — R1(a), R2, R3, R4 corrected; R1(b) returned as an amendment

`review-2026-09-10T05-41-11Z.md` verified the earlier collision and retry
corrections and requested four more. All four are real. Three are corrected in
full; R1's second half is a measured API gap and is returned as an exact
amendment rather than worked around.

**Baseline at claim start.** All eleven manifest paths matched the review's
`evidence/review-133951/result.json` before any edit.

### R1(a) — a combined failure is now RETAINED, and the observations are an owner's

The review was exactly right: `_causal` refused a failing combination before
anything was stored, so the row stayed `prepared` with `causal_observations`
NULL and the failed execution had no custody at all. That is the opposite of
section 4.

- `record_causal_observations(store, observer, *, result_id)` is a new act.
  The OBSERVER runs the harness and attests; the caller supplies nothing. Its
  attestation must name this result, its content digest, its candidate, its
  tree and its target, and the execution it attests must be the execution
  every observation names.
- The observations commit by that act **whether they passed or failed**. A
  passing combination settles the existing `awaiting-evidence` state; a
  failing one settles the new `blocked` state, with its reason and its
  retained runs. `blocked` can never be authorized or published, and an
  attempt to re-observe it into success collides rather than overwriting.
- Judgements now bind the observations too: `_evidence_basis` adds the digest
  of the retained causal record and the observing owner, so evidence given
  about one set of executions cannot be filed under another.
- The owner that RAN the harness may not also judge it.
- `record_result_evidence` no longer takes observations at all; it reads what
  is already in custody.

The reviewer's own counterexample -- relabel the failure, watch it authorize
-- has no door left: the relabelling happens inside an owner that must own it,
and the record refuses it as an operation collision against the settled block.

### R2 — the live assignment and the current policy are proved

- `prepare_result` asks the Authority `assignment_of` **before any effect**.
  Preparation under a released assignment now writes nothing: no row, no
  prepared reference. (The review's point that a later publication refusal
  "does not authorize the earlier preparation effects" was correct.)
- The evidence act binds the policy generation it was given under, and the
  schema requires it on every authorized row.
- `resolve_import_account` revalidates the live integration assignment, reads
  the derived proposal back from the Authority and compares it member by
  member, and refuses when the approval policy generation has advanced.

### R3 — an unproved `imported` row is refused

`IMPORT_KIND = "result.imported"` is named and **nothing in P writes it**, so
`_CHAIN_FOR_STATE` demands an act that cannot exist yet and every imported row
refuses until Q supplies the terminal transition. The reader additionally
requires the entry to exist in this coordinator, to be on this target and to
be `integrated`. The reviewer's exact row -- `entry-never-created` with
foreign keys disabled -- refuses, and so does one that also points at the
import act.

### R4 — nominated storage is proved against the filesystem

`_prove_storage` stats the nominated path and compares device and inode, at
preparation before the profile is asked and again at import admission. The
review's false-inode workspace now prepares nothing. Storage REPLACED between
publication and import -- the case an inode is recorded for -- refuses, and
restoring the nominated directory restores the account.

### R1(b) — AMENDMENT RETURNED: real result-owner evidence cannot precede publication

The review is right that `Owner` is a test fixture and that "an actual
accepted evidence owner/adapter must be made concrete and proved". I measured
whether the accepted owner API can express that in the order CONTRACT-v1
section 3 lists. `evidence/amendment-134000-probe.py`, answers in
`evidence/amendment-134000-probe.json`:

- every attributable evidence verb a configured session has -- `verify`,
  `review`, `approve` -- is keyed by `proposal_id`;
- `verify` against a proposal that does not exist yet refuses **"no such
  proposal"**;
- those verbs refuse result-shaped operands outright: *"verify does not take
  'result_id', 'content_digest', 'candidate' and 2 more; an operand supplied
  and ignored is one the caller believes it chose"*;
- and in section 3's order the DERIVED proposal does not exist when
  `record_result_evidence` runs.

So **evidence-before-publication is not expressible with real owners.** The
same probe shows the inverse IS: publish the derived proposal first, have the
same three real capability-granted sessions write receipts on it, and read
them back by `authority.receipt(derived_proposal_id, kind)` -- which is also
what CONTRACT-v1 section 5 says `Authority.integrate` will require on the
derived proposal, and it makes the evidence re-readable at import, which the
review notes the record currently cannot do.

The exact amendment is in FINDING.md. I did not implement it: it inverts an
order the owner pinned in section 3, and the dossier says to return the exact
amendment before edits rather than choose.

### Candidate

Changed under this claim, 0o664: `reconciliation.py`
`e99ee5e17bd7dc1b8c7d256ca6fadfa09b920ca689622392bad81ac47ee678e8`,
`schema.py`
`e5aa57a47667528143cb8c2507e7e6523aa6fd5a37b0140184ce4a7f015661d9`,
`__init__.py`
`ba149ff8763da631e395925fdc0f0140a494c3d295cb5d9a847254261c18d3f4`,
`tests/integration/test_reconciliation.py`
`1696fe7f5cb5a76dc3fd875442cb91115295f18c87586cd2995b7c0b81dea819`.
Unchanged: `git_profile.py` `cba3f391…`, `admission.py` `93b80300…`,
`driver.py` `c5a86008…`, `store.py` `8117df2b…`, `test_admission.py`
`c33ddf9f…`, `test_driver.py` `ff064265…`, `test_coordinator.py` `7fb6ec2c…`.
Exact digests, modes and sizes: `evidence/result-134000.json`.

Three new groups: `TheLiveAssignmentAndPolicyAreProved`,
`TheNominatedStorageIsProved`, `TheImportedStateIsUnproved`. The six required
groups keep their names.

### Verification and ledger

**167 tests, OK, 8.06s**, every selector naming a class,
`evidence/run-134000-final.log`.

**Output discipline, corrected.** Every run this claim wrote its full stdout
and stderr to a retained log; nothing was piped to `tail`. The nine
intermediate runs -- **five of which FAILED** -- are retained individually as
`evidence/run-134000-step-01..09.log` and itemized with their failures in
`evidence/result-134000.json`.

**Measured this claim 32.01s** across thirteen timed invocations including the
five failures, the two amendment-probe runs and the hash pass. With 24.45s
prior, the **measured subtotal is 56.46s of 77s**, and it remains a rounded
measured subtotal PLUS unmeasured spending: greps and file reads, `ast.parse`
checks and the in-place edit scripts are still untimed, and this manifest's
own composition is not measured. No exact remainder is certified. Nothing was
reset, inferred, re-run to manufacture history, or borrowed.

**A budget flag for the owner and reviewer.** 56.46s measured of 77s, with
unmeasured spending on top, leaves materially less than the arithmetic
difference. If the R1(b) amendment is accepted, implementing and verifying an
inverted publication/evidence order is unlikely to fit what remains.

## claim136400 — the approved amendment, implemented in its exact four paths

Owner return136350 approved `AMENDMENT-publication-before-authorization-v1.md`
IN FULL and reviewer136357 dispatched exactly four paths. Those four changed and
nothing else did: the other seven candidate134000 paths are byte-identical, and
`evidence/result-136400.json` records all eleven with sizes and modes.

**Baseline revalidated first, at this claim's own start.** All eleven
candidate134000 paths and all nine ruling/plan documents in
`evidence/dispatch-136357.json` matched by SHA-256, size and mode. Zero
mismatches. **0.011s.**

**1. THE REQUIRED FIRST PROOF, before any dependent implementation.**
`evidence/roundtrip-136400-probe.py`, answers in `evidence/roundtrip-136400
.json`, full output `evidence/run-136400-step-02.log`. **0.203s.** It imports no
`reconciliation`; it asks a REAL `Authority`, REAL scoped sessions and REAL Git
what the design intends to call. Every answer is YES, so no further amendment
is returned and no Authority edit is proposed. Six measured facts, four of which
changed the implementation:

- A derived proposal carries a result digest DERIVED FROM A CLOSED CUSTODY
  BASIS and reads back field-for-field, including `input_digest`/`policy_digest`.
- The input and policy digests need NO new reader and NO `admission` change:
  the publishing session's own `proposal` read reaches the producer's proposal,
  and `admission._proved` already refuses unless that proposal and the accepted
  Job agree on both members. So the producer's proposal IS the Job's answer.
- Three real configured sessions record ordinary receipts on the derived
  proposal, and `receipt(proposal_id, kind)` reads back actor, disposition,
  candidate digest, target and generation with its authorization decision.
- **Only the APPROVAL receipt carries `policy_generation`; verification and
  review carry NULL.** The implementation therefore reads the generation from
  the approval alone rather than from "the receipts".
- `published` with no receipts is directly observable: `receipts()` is `[]`.
  The Authority's own preconditions also refuse review before a passed
  verification and approval before an accepted review, and a receipt is
  immutable, so a nonaccepting decision is retained rather than overwritten.
- `rev-parse --path-format=absolute --git-common-dir`, realpath-ed and stat-ed,
  sees through a symlink alias AND a linked worktree's shared common directory,
  while target/line/workspace stay distinct. That is the isolation capability.

**2. `git_profile.py`** sha256 `ccd0b048ae039df779cbb2ae468c63b8c5f43f73346b46
43dd9cefdde89b7902`, 26640 bytes, 0o664. Adds `common_dir_vector` and the
read-only `GitIntegrationProfile.storage`, which answers a repository's
resolved common directory with its device and inode. It decides nothing about
isolation: this module owns Git mechanics and the record owns the rule.

**3. `schema.py`** sha256 `164de55dd44ab31f0e4a761dfa96eb1dddc893f0954d969730
6f4306e0d4523d`, 27668 bytes, 0o664. Reviewer134088 was right that reordering
two calls could not represent a published-but-unapproved result. The derived
proposal is now required from `published` onward, and evidence plus policy
generation from `authorized` onward. `RESULT_STATES` says what `published`
means now.

**4. `reconciliation.py`** sha256 `caa250d3bca47f713e9b49ed33646c9cdfad6f6a01f
a80c2fe01b9388612470a`, 92162 bytes, 0o664.

- ORDER: prepare, observe, publish from `awaiting-evidence` (UNAPPROVED),
  external receipts, adopt, resolve. `_CHAIN_FOR_STATE` swaps the two acts, so
  an `authorized` row must hold a committed PUBLISH act whose signature its own
  current contents still produce.
- `record_result_evidence(store, authority, verification, reviewer, approver,
  *, result_id)` ADOPTS the Authority's receipts and writes none. Each is
  cross-bound to proposal, kind, configured actor, accepting disposition,
  candidate digest and target; the caller-supplied generation is GONE and the
  approval receipt's own is compared with the Authority's current one.
- `_custody_basis` is the closed basis the frozen result digest is derived
  from: own and derived identity, source provenance, assignment, prepared
  head/tree/content digest, pinned target, accepted input/policy digests,
  observer and observations digest. Real receipts carry no `observations_digest`
  and no `observed_by`, so the executions ride the proposal instead — which is
  the amendment's binding, not an invented adapter field.
- `publish_result` proves both digests against the producer's proposal rather
  than accepting text, and proves the assignment live before the effect.
- `_prove_isolation` closes R4. It reads the Manager's own `line_of` for
  `line_path`/`source_path` and refuses a workspace that is the producer's
  line, its protected source or the dedicated target — by REPOSITORY identity,
  so a shared Git common directory counts, and by resolved DIRECTORY identity,
  so an alias does. It runs before any effect and again at admission.
- `resolve_import_account` requires `authorized`; `published` alone always
  refuses. It re-derives the custody digest, re-reads all three receipts and
  compares them with what was adopted, and re-proves storage and isolation.
- The profile certification moved ABOVE the first profile call, because
  isolation now asks the profile something before any effect and an
  uncertified profile must be turned away before it is asked anything.

**5. `test_reconciliation.py`** sha256 `55c25a07bc11993dad4afb6c1a622a90fe85f2
dd4a39ea2be6cbe982ded465fe`, 91387 bytes, 0o664. The only test path this
amendment touches. The three result owners are REAL `authority.session(...)`
objects now, so reviewer133787's objection has nothing left to apply to; the
`Owner` stand-in survives only for miswired-owner cases. The scheduled
expectation change is made: the old publication-before-evidence refusal is
replaced by `test_a_published_result_with_no_receipts_authorizes_nothing`,
which proves the real proposal exists, carries no receipts, authorizes nothing
and resolves no import account. New controls cover receipt adoption, foreign
and producer receipts, nonaccepting review, superseded policy, the custody
digest's bindings, and the four isolation counterexamples including
reviewer134088's exact one. All six required groups keep their names and every
earlier defect control is retained.

**HONEST BOUNDARY, unchanged and restated.** The Authority, its proposals, all
six real policy receipts, the repositories, the profile and the coordinator
store are real. The Worker Manager's checkpoint/writer/frozen-output readers and
the Job rows are patched exactly as `test_admission` patches them; the line row
now carries the REAL producer repository and source paths, because the isolation
proof reads them.

**VERIFICATION.** 109 tests OK, 7.392s, focused CLASS selectors only — no
module, package, broad, live or OCI run, and no historical evidence rerun.
Final log `evidence/run-136400-step-11.log`. The eleven test_reconciliation
groups plus three `test_admission` groups and `test_coordinator`'s store-shape
group, which are the unchanged existing paths this schema change could reach.

**LEDGER, NEW 30s ceiling, starting at 0.** Measured 20.098134173999597s across
eleven timed invocations, THREE OF WHICH FAILED and are each retained in full
with its failure: step 4 (the wrapper's own relative-path fault, which ran no
subprocess), step 5 (15 errors — `boundaries.document` requires the Authority's
EXACT proposal member set) and step 9 (two class selectors I had guessed
wrong). Remaining 9.901865826000403s. Unmeasured here: file reads and greps,
the three in-place edit scripts and this manifest command. No historical
remainder, contingency, Q/R or W119405 time was drawn on; the 56.46s measured
subtotal plus unmeasured history stands preserved and retired for this
amendment.

Q W133120 and R W133129 remain gated on independent full P acceptance.
