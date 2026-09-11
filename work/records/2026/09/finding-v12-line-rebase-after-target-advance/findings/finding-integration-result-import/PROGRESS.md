# Progress

No implementation started. Reviewer133108 created this dossier with Work133120.
Actual change authors append attributable entries under their claims.

## claim136712 — design pinned before any source edit

IN FLIGHT when written, so the state is resumable from the record rather than
from a context. Baseline revalidated first: all eleven accepted P paths and all
23 Q paths in `evidence/dispatch-136680.json` match by SHA-256, size and mode,
zero mismatches, zero missing. **0.011s.**

### What is actually missing, read from the tree

P leaves an AUTHORIZED result whose `resolve_import_account` re-proves source,
assignment, receipts, policy, storage, isolation and exact target. Nothing
consumes it. `reconciliation._expected_signature` answers `None` for
`IMPORT_KIND`, so `result_of` refuses every imported row -- which is the
scope omission owner136677 approved adding reconciliation.py and
test_reconciliation.py to Q for.

The ordinary pipeline is built around the DIRECT-IMPORT account: `enqueue`
stores a closed fifteen-member eligibility account, `grant_lease` burns a
fence on the smallest queued rank, `execution._current` re-resolves through
`admission.resolved_account`, a container runtime asks a MODEL to compose the
import, and `driver` writes the Authority integration receipt before
`execution.complete_integrated` settles and releases.

### The design, smallest that reaches the milestone

**1. The result IS an ordinary queue candidate, and its account says so.**
`driver.authorized_result_eligibility` composes the fifteen-member account from
two accepted readers rather than inventing one: `admission.source_account`
supplies the eight members that are the producer's own (authority, Work,
assignment generation, line, checkpoint, verdict, checkpoint digest, scope
digest) and P's `resolve_import_account` supplies the seven that are the
RESULT's (derived proposal, derived result identity and digest, the prepared
head as the candidate, the pinned snapshot as the expected target, the content
digest as the path-set digest). Both are cross-checked member for member where
they overlap. That is "preserve both source and derived identities" as one
document, and it needs no schema column: `entries.checkpoint_id` still names
the producer's checkpoint, so the queue's one-candidate-one-place rule holds
across the direct and reconciled branches.

**2. A result entry is recognised by the coordinator's own custody record.**
`execution._current` must re-resolve a result entry through
`reconciliation.resolve_import_account`, not `admission.resolved_account`.
NOT by a new column: the coordinator already holds the `integration_results`
row, so an entry whose `proposal_id` is some row's `derived_proposal_id` IS a
reconciled result, answered by that row. A caller supplies nothing.

**3. The importer for this branch is the standalone profile, and there is no
model in it.** The combined bytes were composed, observed, published and
independently approved in P. Importing them is `fetch` the prepared head into
the dedicated target and `advance` its configured reference by compare-and-swap
from the exact reviewed revision -- both already owned by
`git_profile`. Post-import verification re-reads the target's content AT THE
NEW REVISION through the profile and compares it path-for-path and mode-for-mode
with the authorized content set, so the physical bytes and the account agree
before anything settles.

**EXPLICIT NARROWING, FLAGGED RATHER THAN SILENT.** Q's FINDING also names a
"bundle version". The bundle exists to give a MODEL the material to compose an
import; this branch has no model, because the bytes are already prepared,
observed and approved. Building a bundle for a path with nothing to read it
would be inventing work, so it is not built. Said here so the reviewer owns
that judgement rather than discovering it.

**4. Terminal custody, the approved amendment.**
`reconciliation.record_imported(store, authority, *, result_id, entry_id)`
requires an AUTHORIZED result, and re-proves three things from their owners:
the coordinator's entry exists, is on this result's target, is `integrated` and
retains an eligibility naming this result's derived proposal, result, digest
and candidate; the Authority holds an `integration` receipt on the DERIVED
proposal, by the integrating actor, disposition `integrated`, naming this
candidate and this target; and the row's own publication/authorization chain
still stands. `_expected_signature(IMPORT_KIND)` re-derives that act's
signature from the row alone, so an imported row reads back and a fabricated
one still does not.

**5. Order of the durable acts.** Authority integration receipt, then
`settle_integrated`, then `release_lease` (both through the accepted
`execution.complete_integrated`), then `record_imported`. Terminal custody is
LAST and re-proves its facts from the entry and the Authority rather than from
the caller, so an interruption before it leaves a state the same call settles
on replay -- and it cannot double-import, because the target reference has
already advanced and `resolve_import_account` refuses a moved target. The
exhaustive crash ordering matrix is parked W136578 and is not claimed here.

### Exact changed paths and why

- `v12/python/src/baton_v12/integration/reconciliation.py` (approved
  amendment): `record_imported`, `IMPORT_KIND` signature/reader.
- `v12/python/src/baton_v12/integration/execution.py`: the result-entry
  re-resolution branch and `import_authorized_result`.
- `v12/python/src/baton_v12/integration/driver.py`: the eligibility
  composition and the `admit_authorized_result` tick.
- `v12/python/tests/integration/test_reconciliation.py` (approved amendment):
  the bounded expectation change and the terminal-custody controls.
- `v12/python/tests/integration/test_execution.py`: the real end-to-end import
  and settlement, reusing the accepted P fixture rather than duplicating it.

Q's other accepted paths are left untouched; narrower behaviour permits that
under DELIVERY-SCOPE-2026-09-10.md.

### Focused selectors pinned before running

`test_reconciliation.TheImportedStateIsUnproved` keeps all four refusals
unchanged -- they remain true, because no `IMPORT_KIND` act is journalled for a
corrupted row -- and only its docstring's temporary claim changes. New
`test_reconciliation.TheTerminalImportIsRecordedAndProved`: real terminal
success and readback, exact retry replay, missing receipt, foreign receipt on
the producer's proposal, an entry that is not integrated, an entry on another
target, and an unauthorized result. New
`test_execution.TheAuthorizedResultIsImportedAndSettled`: one successful real
import with BOTH Jobs' changes on the target, the reference advanced by CAS,
the post-import check, the Authority receipt, terminal custody and capacity
release; a stale target refusing before any write; and an unauthorized result
refusing before any write.

## claim136712 — Q implemented; the result is ON the target

The design above was implemented as pinned, with two corrections the tree
forced and one omission it exposed. Manifest, ledger and every retained log are
`evidence/result-136712.json`, `evidence/ledger-136712.json` and
`evidence/run-136712-step-*.log`.

### Changed, 0o664, and all six are inside Q's accepted allowlist

- `integration/reconciliation.py` `c575077386c81c135b337b5e5a940aeabfe2d142c15
  edcbade6e905bbc36af6d`, 102329
- `integration/execution.py` `646f0b7182db5427e32dfdfcfebb2637eb64b4f52838e695
  974f384d403ba988`, 35658
- `integration/driver.py` `a0f62c5aa0eb4d8cf55770600d4a55fa38692df902b22b4c039
  05ea5684ac450`, 102544
- `integration/queue.py` `18ced502ebcff18946c1c72914223166c995484ce2baccd6423b
  3f7ca0b23a0`, 117048
- `tests/integration/test_reconciliation.py` `213520989b628f414d3f0ad27fce2d1f4
  131cf48435f2ed6af1c5f4c29b77a72`, 101604
- `tests/integration/test_execution.py` `de18f1aef57a565080c2cc95914d0b7c21eebe
  f1566da2fae8c2e99015a27882`, 59834

`git_profile.py`, `schema.py`, `admission.py`, `store.py`, `__init__.py`,
`test_admission.py`, `test_driver.py` and `test_coordinator.py` are BYTE-
IDENTICAL to the independently accepted P candidate136400 and to the Q
baseline. No schema, Authority or Manager source was touched, and no Q path
outside the six was edited.

### THE MILESTONE TRANSITION, and it is real

`test_execution.TheAuthorizedResultIsImportedAndSettled` runs the whole thing
on a real Git target, a real producer line, a real `Authority` with real
sessions and receipts, and a real `IntegrationStore`. Job A integrated and
moved both the dedicated reference and the canonical cursor; Job B's accepted
submission was behind it; P reconciled B into its own observed and
independently approved candidate; and this tick puts that candidate on the
target. Afterwards, all four proved together: the dedicated reference holds
the reconciled commit and its tree carries BOTH Jobs' changes; the entry is
`integrated` with a settlement naming the imported paths and the readback; the
Authority's integration receipt is on the DERIVED proposal and its canonical
cursor is the imported candidate; and the result row is `imported`, bound to
the entry it went through. Job B's line and the producer's proposal are
untouched.

### Two corrections the tree forced

**1. THE QUEUE COULD NOT READ A STORE THAT HAD EVER PREPARED A RESULT.**
`queue._history` proves the WHOLE journal and refuses any kind it does not own
-- deliberately, because "a store carrying acts this process cannot reason
about is not one it can prove anything about". W133117's six result-custody
acts commit into that same `operations` table. So before Q connected them, the
first `enqueue` on a store that had prepared a result refused its own journal.
This was invisible in P because P never called a queue function. `queue.py`
now NAMES the six kinds, re-derives each identity, and includes `result_id` in
the duplicate-subject key -- and deliberately does NOT re-own their operand
shapes, because `reconciliation.result_of` re-derives every one of those
signatures from the row as it stands now, which is the stronger binding.
Stated plainly in the source: for the INTENT act alone this reader is weaker
than that one, because its identity is derived from the whole closed fixed
operand set by an owner `queue` cannot import without a cycle.

**2. `result_of` SELECTED A COLUMN THAT DOES NOT EXIST.** P's imported-state
branch read `eligibility` from `entries`; that is a derived member, not a
column, so the statement raised `sqlite3.OperationalError` out of a typed
reader. Nothing ever reached it, because P wrote no terminal act and every
imported row refused earlier. The first legitimate terminal readback is what
ran it. It now asks for the three members the check actually uses.

### The omission this exposed, and how it is closed

`_witness` refused `result.imported`, so the terminal act could not be
replayed. It is in the witnessed set now: the act that has an owner is the act
that can be witnessed.

### Deliberate narrowings, flagged rather than silent

- **No bundle version.** Q's FINDING names one. The bundle exists to give a
  MODEL the material to compose an import; this branch has no model, because
  the bytes were composed, observed and approved in P. `execution._current`
  refuses a reconciled entry that reaches the runtime path at all, as an
  INTEGRITY statement so the target blocks rather than a legitimate candidate
  being terminally refused. Building a bundle for a path with nothing to read
  it would be inventing work.
- **The injected runner is named at `import_authorized_result`.** The
  dedicated target must hold the prepared commit before a reference can name
  it, and `git_profile.import_vector` is the exported composition for exactly
  that -- but `git_profile.py` is NOT in Q's allowlist, so no verb was added
  to it. The deployment's own runner, which built the profile, is passed
  beside it. P's accepted profile bytes stay untouched.
- **Terminal custody is the LAST durable act**, after the Authority receipt,
  the settlement and the release. It re-proves the integrated entry and the
  Authority receipt from their owners rather than from the caller, so an
  interruption before it leaves a state the same call settles on replay -- and
  it cannot import twice, because the reference has already advanced and the
  account refuses a moved target. W136578 owns the exhaustive crash ordering
  and nothing here claims it.

### Controls, against DELIVERY-SCOPE-2026-09-10's required minimum

One successful real import/settlement with both changes; an unapproved result
importing nothing and taking no rank; a stale target refusing before any write
at composition AND, separately, under the grant where the entry is refused and
the queue moves on; a blocked combination never reaching the target; a
reconciled entry never handed to a runtime. Terminal custody adds: real entry
and real receipt settle it and it reads back; exact retry replays; another
entry collides; no receipt refuses; the producer's own integration receipt is
not this result's; an entry that is not integrated, and one admitted for
another candidate, supply no authority; an unauthorized result records nothing;
and moving the entry a settled import named breaks that act's own signature.
`TheImportedStateIsUnproved` keeps all four fabricated-terminal refusals
unchanged -- they were always about a row with no committed act, which is still
refused -- and only its docstring's temporary claim changed.

### One fixture change beyond the amendment's letter, named here

`ResultCase` now sets the Authority's canonical target to `self.advanced` and
grants the integrator its `integrate` capability in `setUp`.
`Authority.integrate` refuses unless its own canonical target is the one the
proposal names, so without the first there is no real integration receipt to
adopt; and `grant_capability` bumps the policy generation, so every grant must
precede every receipt. The first is also more truthful about W131409: Job A
INTEGRATED, which moves the reference and the cursor together. All 82 P
acceptance cases pass unchanged under it.

### Verification and ledger

318 tests OK, 11.418s, focused CLASS selectors only -- no module, package,
broad, live or OCI run, no image build and no historical rerun. Final log
`evidence/run-136712-step-15.log`. Coverage is the twelve reconciliation
groups, ten execution groups, nine coordinator groups centred on the journal
proof this claim changed, three driver groups, two recovery, four runtime and
three admission.

LEDGER on the 95s ceiling, starting at 0: measured
**31.260087/95s** across sixteen timed invocations, **SIX OF WHICH FAILED**
and are each retained in full with its failure -- steps 3 to 7 (the terminal
group converging: a missing `line_id`, the queue journal refusing P's kinds
twice, the absent `eligibility` column, an unwitnessed kind) and step 9 (one
end-to-end expectation of mine that was wrong, not the code's). Remaining
**63.739913s**. Unmeasured: file reads, greps, editor round trips, the
design-pin and manifest scripts; no product test ran outside the measured
invocations. No P remainder, contingency, W119405 or reviewer transfer.

R W133129 remains gated on independent Q acceptance.

## claim136862 — R1 and R2 corrected; both findings were real

`review-2026-09-10T14:20:24Z.md` is right on both counts and I reproduced both
against the tree before changing anything. Neither is parked hardening: R1 is
an essential contract requirement and R2 is a pre-write authority hole that the
reviewer's own probe drove to a real target write.

Retained candidate136712 revalidated at this claim's start; the corrections are
serial extensions of exactly those bytes.

### R1 — the required post-import tests now actually run

**Confirmed.** `import_authorized_result` fetched the candidate, advanced the
reference, read the tree back and LABELLED that readback `verification`. No
test executed against the imported bytes at any point, and the driver then
wrote the Authority receipt, settled, released and recorded imported. Object
equality is a statement about which objects are present; INTEGRATION-CONTRACT-v1
sections 4 and 6 require retained post-import TESTS, and
DELIVERY-SCOPE-2026-09-10 keeps that check and its failed-test hold as
essential minimums.

`POST_IMPORT_VERB`/`POST_IMPORT_MEMBERS` name a configured verification owner
asked through a capability, exactly the shape W133117 settled on for the causal
observations -- and deliberately the same closed member set, so an import's
evidence and the combined observation it was approved on are one document to
read. The question is derived here; the answer must name back the commit and
tree that were actually delivered, and attest its own participant.

THE ORDERING IS THE APPROVED ONE. The tests run on the imported candidate
BEFORE the reference names it. A failing execution -- or one this coordinator
cannot read -- blocks the target with the retained evidence and reaches no
reference advance, no Authority receipt, no settlement and no release. The
readback is kept BESIDE the executed tests in the settlement rather than
instead of them.

`test_a_FAILED_post_import_test_holds_and_never_advances` runs a REAL
deployment check that really exits 1 on the correct combined content -- a
suite the result was never approved against, which is the honest shape of this
case rather than a stub. Afterwards the reference is exactly where Job A left
it, no integration receipt exists, the result is still `authorized`, and the
target is blocked at `post-import-tests-failed` with the failing execution in
its account and the lease kept live for the explicit recovery.

The hold account is composed in `execution` rather than through
`runtime.hold_account`, whose four reasons are about a RUNTIME's interruption
and this branch has no runtime. `_stale` already composes a block account the
same way.

### R2 — the grant is now bound to the result before any effect

**Confirmed, and worse than it reads.** The importer granted the requested
entry, resolved `result_id` independently, compared only the target identity
and then wrote. A live grant admitted for ANOTHER proposal on the same target
therefore authorized this result's fetch and its reference advance; the
reviewer's probe drove exactly that to a real target write. `record_imported`
catches it afterwards, and afterwards is too late.

TWO CHECKS, because they answer different moments. `_admitted_for` proves the
NAMED entry is this result's from the entry's own admitted account BEFORE
`grant_lease` is called -- `result_of` is a pure read, so a wrong entry never
receives a grant and no fence is burned. `_granted_for` then compares the FULL
freshly derived fifteen-member account against the account the entry the store
actually leased was admitted with, and binds the configured integrating
participant to both the live grant and this result's own live integration
assignment, before the first object or reference write.

`authorized_result_eligibility` moved from `driver` to `execution` so the
composition the importer must re-prove and the composition the tick admits are
ONE owner; `driver` re-exports it and the public name is unchanged.

`test_a_GRANT_FOR_ANOTHER_PROPOSAL_writes_nothing` enqueues an account naming
the producer's own `proposal-b1` and asks the public importer to import the
derived result under that entry. It refuses, the reference has not moved, no
lease exists, the target's fence is still zero, the entry is still queued and
the verification owner was never asked.

### Changed, 0o664, and still only inside Q's allowlist

- `integration/execution.py` `f3949a5914261fe879a2af7491aad90be30da9672ce5449c
  c8510b99b0e1c371`, 51811
- `integration/driver.py` `3b170070fade29bb0600814eeca4e40787bb8864e4d8a65bf54
  ac355f2322649`, 98947
- `tests/integration/test_execution.py` `cd039544c5c7141e9010958a3a134d9746cff6
  77ce9ef382d75587b0823ec9bb`, 67932

`integration/queue.py` `18ced502ebcff18946c1c72914223166c995484ce2baccd6423bb3
f7ca0b23a0`, `integration/reconciliation.py` `c575077386c81c135b337b5e5a940aea
bfe2d142c15edcbade6e905bbc36af6d` and
`tests/integration/test_reconciliation.py` `213520989b628f414d3f0ad27fce2d1f41
31cf48435f2ed6af1c5f4c29b77a72` are UNCHANGED from candidate136712, and every
accepted P path remains at its accepted bytes.

### Verification

Named methods for the corrections, as the review directed, and no repeat of the
318-case sweep. Final run `evidence/run-136712-step-21.log`: eleven named
methods OK in 1.506s -- the two new corrections, the wrong-entry refusal, and
the eight cases they could have broken including the normal positive, the
replay, both stale-target windows, the unapproved refusal, the blocked
combination, the runtime-path refusal and the terminal custody positive. A
bounded class regression at `evidence/run-136712-step-20.log` covered 98 cases
across reconciliation, execution, driver and the coordinator journal proof.

### Ledger

`evidence/ledger-136712.json` IS AUTHORITATIVE and the manifest now says so.
The reviewer was right that the previous handoff quoted 31.260086887000398s
while the ledger held 31.271264928000164s: a manifest written BY a measured run
can only embed the subtotal current at its own start. That is stated in
`result-136712.json` rather than repeated.

Cumulative author **39.216578/95s** across TWENTY-THREE timed invocations,
**SEVEN OF WHICH FAILED** and are each retained in full with its failure --
steps 3-7 and 9 from the first pass, and step 18 here (the hold account went
through `runtime.hold_account`, whose closed reason set does not contain a
post-import test failure, and the driver did not yet propagate the execution).
Remaining **55.783422s**, nominal arithmetic and not certified unused: my
unmeasured reads, greps, editor round trips and the correction scripts stay
disclosed and unmeasured. No P remainder, contingency, W119405 or reviewer
transfer.

R W133129 remains gated on independent Q acceptance.

## claim136939 — R3 corrected; the grant is re-proved after the tests run

`review-2026-09-10T14:33:43Z.md` is right, and the correction it asked for
exposed a second defect of my own making in the R1 code. Both are fixed.

### R3 — a grant recovered while the tests ran still advanced everything

**Confirmed.** R1 introduced the longest interval this branch has -- running
the configured post-import tests -- and I proved the grant live BEFORE the
fetch and then never again. So a holder recovered during that interval, through
the ordinary public `block_target`/`abandon_lease` pair the direct path's own
accepted control already uses, still reached the compare-and-swap. The
reviewer's probe advanced the real reference and wrote a real integration
receipt on the derived proposal before anything refused. The driver made it
worse: it created the Authority receipt BEFORE `complete_reconciled` re-read
the lease, and an integration receipt is a durable Authority act that a later
coordinator refusal cannot take back.

Two cutpoints added, one in each owner. `execution.import_authorized_result`
re-proves the exact live target, entry, lease and fence through `live_grant`
after the verification returns and immediately before the CAS.
`driver.admit_authorized_result` proves the same grant before it asks the
Authority for anything. A recovered grant now refuses at the first of those,
with the reference untouched, no receipt, no settlement, no release -- and the
recovering owner's blocked target, abandoned lease and held entry exactly as
that owner left them.

### The second defect, which was mine and which R3's probe surfaced

The R1 code wrapped BOTH the ask and the answer-validation in one `try`, so any
`ContractRefusal` the verification owner's own work provoked became a
`post-import-verification-unreadable` block. When that work recovered THIS
grant, the resulting `block_target` collided with the recovering owner's own
block on the same target and entry -- and the collision message replaced the
real refusal. Diagnosed at `evidence/run-136712-step-26.log`.

The two are separated now: `_post_import_execution` asks the owner and returns
what it said; `_owned_post_import` adopts the SHAPE under the caller's hold.
A configured owner that explodes is not answering, and its refusal is not this
module's to relabel -- which is exactly how W133117 asks its observation owner.

### Changed under this claim, 0o664, all inside Q's allowlist

- `integration/execution.py` `4a3aa4da6dcc0c94e303278da2e0f8f415f88709c157aeff
  8399661b383b121a`, 54092
- `integration/driver.py` `fa0cf3dd1404528e5573a736dc99fa841da1feeeb4a760f6be9
  05f0e755b6ba5`, 99513
- `tests/integration/test_execution.py` `3210cc2569b0c6edcda77db6b63ef7b9ed3e98
  2f3a726bb531d58bfb53b3d9c8`, 71377

`queue.py`, `reconciliation.py` and `test_reconciliation.py` keep their
candidate136712 bytes, and every accepted P path is at its accepted bytes.

### The focused regression

`test_a_grant_RECOVERED_WHILE_THE_TESTS_RAN_advances_nothing` reproduces the
reviewer's exact boundary: the harness really runs, and while it runs another
owner recovers the holder through the public operations only. The tick refuses
with "a grant is proved live at the moment it is used"; the verifier WAS asked,
so this is the boundary after the tests rather than before them; the reference
is where Job A left it; the Authority holds no integration receipt; the result
is still `authorized`; and the target is blocked at `operator` with an
abandoned lease and a held entry -- the recovering owner's own state, untouched.

### Verification

Named methods only, as directed, with no 98- or 318-case collection. Final run
`evidence/run-136712-step-31.log`: thirteen named methods OK in 1.568s -- the
R3 regression, the R1/R2 controls, the corrected positives and failure
controls, the direct path's own two accepted grant-ended cases (this changed
`execution` and they are the neighbours most likely to feel it), and the
terminal custody positive.

### Ledger

`evidence/ledger-136712.json` remains authoritative. Cumulative author
**49.840108044000772/95s** across THIRTY-THREE timed invocations, **TWELVE OF
WHICH FAILED** and are each retained in full with its failure: steps 3-7, 9 and
18 from earlier passes, and 24, 25, 27, 28 and 30 here -- the block-collision
that buried the real refusal and its diagnostic, a malformed recovery document
in my own test, an entry-state expectation of mine that was wrong, and one
mistyped selector. Remaining **45.159891955999228s**, nominal arithmetic and
not certified unused; my unmeasured reads, greps, editor round trips and
correction scripts stay disclosed and unmeasured. Any number quoted inside
`result-136712.json` is current as of its producing run's start, which that
file now states. No P remainder, contingency, W119405 or reviewer transfer.

R W133129 remains gated on independent Q acceptance; W136578 stays parked.
