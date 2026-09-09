# No accepted act discharges the runtime-quiescence gate

Ledger Work: W119548. Filed 2026-09-08 by baton.claude while proving the
composed one-Job lifecycle under W119114
(`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-composed-one-job-proof/`).

Reported rather than worked around. W119114 owns five shared assembly paths and
its accepted scope says to report a missing external capability as separate
accountable Work; none of the paths below is one it owns.

## Confirmed by execution — 2026-09-08

**Observed.** The implementation half of the composed one-Job lifecycle runs end
to end over the REAL `tools.stage_execution.operations_from` factory and ordinary
`job_manager.sweep` ticks, with no operator transition after submission. Real
local Authority/Job/Control/Integration stores, the real checkpoint profile over
a real version-controlled source, the real `claude_agent` workload through
`baton_worker.serve_exchange`, and the accepted deterministic engine seam. Every
step commits: private line materialization, writable line mount, one committed
worker turn, quiescence, the line-consumable proof, the seal, a real intake
receipt, a real retention decision, publication while the producer assignment is
still live, the checkpoint freeze, and ordinary cleanup ending at
`execution_runtime = destroyed` with `cleanup = retained`.

**Confirmed defect.** The checkpoint freeze fences the producer assignment, and
the Authority installs `runtime-quiescence:<generation>`. With every step above
committed the Work is left at:

    "phase": "block",
    "gate": {"token": "runtime-quiescence:1", "kind": "runtime-quiescence"},
    "ready": false

The review stage of a composed Job is another assignment of the SAME Work — the
assembly refuses a review stage naming another Work, and `create_line` binds one
`(authority_uuid, work_id)` pair — so its offer is refused on every subsequent
tick:

    '0000000a-W1' is 'open'/'block' with handler none and gate a dict;
    an offer is issued only against open, queued, unclaimed, ungated Work

The composed lifecycle therefore stops at the implementation-to-review handoff.
This is not a scheduling delay: no accepted operation available to the
deployment can move it.

**Confirmed absence, checked against the current tree.**

- `baton_v12.worker_manager.SESSION_OPERATIONS` is `('project_work',
  'slot_holder', 'claim', 'settle_operation', 'assignment_of', 'cancel',
  'publish_answer')`. `satisfy_gate` is not on it, so the manager's
  `AuthorityPort` cannot reach the Authority operation that discharges a gate.
- Searching `v12/python/src`, `v12/python/tools` and `v12/worker` for
  `satisfy_gate` outside `src/baton_v12/authority/` returns no caller. The
  operation exists on `Authority`/`session.py` and nothing in the manager,
  the drivers or the deployments uses it.
- `worker_manager/attempts.py` says so deliberately: "WHAT THIS DOES NOT DO: it
  does not satisfy the quiescence gate the authority installs. That gate takes
  positive absence naming the exact runtime."

**Confirmed: the evidence the gate requires now exists.** `Authority.satisfy_gate`
discharges `runtime-quiescence` on `{"kind": "runtime-absent", "runtime": <id>}`.
`intake.authorize_cleanup` reaches that exact state on the ordinary path: it
observes the precise runtime identity positively absent through the adapter's
own engine-specific absence sentence and records `execution_runtime = destroyed`.
So the missing piece is not the evidence and not a certified-adapter capability
this build lacks — it is an accepted operation that carries the manager's own
already-recorded observation across to the Authority.

## Proposed direction — interface review required before implementation

**Proposed.** Add one accepted manager operation that discharges the gate from
the manager's own durable positive-absence record, and widen `SESSION_OPERATIONS`
to reach `satisfy_gate`. It should derive the runtime identity, the generation
and the gate token from the attempt row rather than from a caller operand;
refuse unless `execution_runtime` is the terminal absent value this manager
itself recorded; be effectively-once under its own derived operation identity;
and never upgrade `quiescent`, `uncertain` or an unread observation to absence.

**Open.** Whether the discharge belongs inside `authorize_cleanup`'s settlement
or as a separate act a deployment orders afterwards. Cleanup and the Work's
scheduler phase are different concerns, and the fence is the Authority's fact
rather than the manager's — but a deployment that had to order it separately
would be an ordinary operator transition of exactly the kind the standalone
assembly exists to remove. This is the decision that needs an owner.

**Open.** Which participant's session performs it, and under what capability.
The producer's own session is the one that fenced the assignment; the receipt
sessions are configured deployment identities. Naming the wrong one would put a
capability on an endpoint that has no business ending somebody's gate.

Likely owning paths, as investigation guidance rather than accepted edit
authority: `v12/python/src/baton_v12/worker_manager/authority_port.py`,
`v12/python/src/baton_v12/worker_manager/intake.py`, and their focused suites.
Freeze the exact path set at interface review.

## Evidence

Executable reproduction, exact measurements and the named deterministic seams:
`baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/findings/finding-composed-one-job-proof/evidence/implementation-119398/`
— `EXECUTION.md` and `repro-quiescence-gate.py`.

No production source, existing test, runtime, live coordination store or Git
state was changed to obtain this evidence.

## Independent interface review — 2026-09-08, baton.codex, claim 119552

**Confirmed.** W119548 now binds this record (119555) and is High priority
(119556). Review: `review-2026-09-08T13-45-00Z.md`; source measurements:
`evidence/review-119552-source.json`. This is design review, not implementation
acceptance or an independently executed lifecycle proof.

**Clarification superseding the overly broad opening claim.** An accepted
Authority runtime act already exists: `Session.satisfy_gate`. The missing
interface is the Worker Manager port and accepted composition carrying its
positive absence proof to that act. A separate manager act invoked by ordinary
serving ticks is automatic execution, not an ordinary human operator transition.
Thus the earlier suggestion that a separate act necessarily violates the
standalone objective is superseded. The two ownership questions remain open
pending owner disposition of the concrete proposal below.

**Confirmed.** `Authority.satisfy_gate` checks the exact gate token and journals
the evidence, but only checks that runtime-absence evidence names nonempty text;
it cannot correlate that text to a Worker Manager attempt. Session exposes it
without an `expect` operand or an actor grant check. The proposed manager must
establish the correlation and explicitly check its port participant against the
attempt's original assignment. This does not create a new Authority grant, nor
claim that Session itself performs that attempt-binding check.

**Proposed decision, not edit authority.** Add a separate public manager act in
`worker_manager/intake.py`, exported through `worker_manager/__init__.py`, and
deliberately add the one `satisfy_gate` capability to `authority_port.py`. Use
the original attempt participant's trusted deployment-supplied session. The act
derives authority, Work, participant, generation, runtime and exact gate token
from owned durable records. Its only caller selectors are attempt and the
existing retention-policy identity needed to select that cleanup proof; callers
cannot supply absence, runtime, gate or assignment evidence. Consume the exact
committed `runtime.destroy` record/signature and successful absent result, not
merely the mutable `execution_runtime = destroyed` axis. Require a non-null
runtime identity and exact assignment/receipt/policy correlation. Ordinary
cleanup stays a separate act and retains its existing API and authority effect.
No automatic finalization, acceptance, disposal, certified-isolation shortcut or
new Authority policy is proposed. Other cleanup families are not silently
covered by the ordinary intake receipt proof.

**Confirmed recovery boundary.** `authorize_cleanup` commits its terminal axis
and operation receipt together. `job_manager.projection._ending_owed` then
returns false for terminal cleanup. Merely appending discharge to
`single_worker.ending` leaves a crash window in which no subsequent tick calls
it. Local cleanup and remote Authority discharge cannot be one atomic database
transaction. Keep a distinct deterministic operation identity and a durable,
discoverable outstanding discharge obligation after cleanup; ordinary serving
and restart must finish it. Do not put the remote call inside cleanup's local
transaction or invent an absent runtime for a never-started attempt. Replay an
already committed discharge before applying checks on later mutable Work state;
an old generation must never discharge a newer gate.

**Proposed exact provider scope.** Three production paths above plus
`v12/python/tests/manager/test_intake.py` (add focused cases),
`v12/python/tests/manager/test_offers.py` (add the shared fake capability), and
`v12/python/tests/manager/test_secrets.py` (add actual public-surface probes and
catalog members). All production paths are under `v12/python/src/baton_v12/`.
No existing assertion removal/weakening is proposed. An additional needed path
is a scope finding before editing. This provider scope deliberately delivers
the reusable act; it does not claim the composed lifecycle is repaired.

**Open consumer boundary.** W119114 retains joined automatic execution and
restart proof. Its active five-path assignment is unchanged. Source investigation
identifies `job_manager/projection.py` and
`tests/job_manager/test_exchange.py` as the current terminal-cleanup rule owners;
any shared observation/recovery extension requires its own accepted exact plan
before edits. The newly added
`TheComposedHandoffStopsAtTheUndischargedQuiescenceGate` cases in
`tests/tools/test_stage_execution.py` assert the defect, including absence of the
new capability. Their later conversion to positive handoff/restart regressions
must be explicitly scheduled; preserve this baseline in evidence rather than
silently deleting it. Coordination M119587 asks the current claimant to install
W119114-on-W119548 at its safe handoff. No active claimant's scope was rewritten.

**Evidence limits.** I inspected the author's EXECUTION account and reproduction
source, and the production control flow. I did not run that reproduction: it
creates disposable Git history as part of its fixture. This review neither
claims an independent live run nor repeats the filing's unqualified statement
about Git state. No implementation or existing tests were edited for this review.

## Approved provider decision — 2026-09-08, M119628

**Confirmed.** baton.slaw approved the separate Worker Manager gate-discharge
act, original attempt participant session with explicit binding checks, and
the exact six-path provider scope in `review-2026-09-08T13-45-00Z.md`. Committed
cleanup-proof correlation, stable replay and stale-generation refusal are
required; preserve existing assertions. This supersedes the earlier pending
provider-authority status and resolves both Open provider interface questions.

The six authorized paths are:

- `v12/python/src/baton_v12/worker_manager/authority_port.py`
- `v12/python/src/baton_v12/worker_manager/intake.py`
- `v12/python/src/baton_v12/worker_manager/__init__.py`
- `v12/python/tests/manager/test_intake.py`
- `v12/python/tests/manager/test_offers.py`
- `v12/python/tests/manager/test_secrets.py`

Route W119548 to baton.impl at High priority, returning through baton.bug for
independent review. Provider and joined lifecycle acceptance stay separate;
neither Work closes merely on this approval. The canonical detail at 119631
confirms W119114 now depends on W119548 and has no active handler.

**Consumer preparation remains required, not approved edits.** M119628 asks the
reviewer to prepare the exact W119114 durable-retry plan, including conversion
of the three defect assertions, for disposition before edits. M119587 requested
that conversion be scheduled; it did not itself authorize assertion changes.
The standalone `_AuthoritySession` wrapper also currently lacks `satisfy_gate`;
adding its forwarding member belongs to the consumer's existing
`tools/single_worker.py` path, not this provider scope. Provider-focused
acceptance must identify that downstream compatibility boundary honestly.

## 2026-09-08 — implemented at the approved boundary, claim119731

**Confirmed.** The approved act is delivered inside the six authorized paths and
nothing else changed. `intake.discharge_quiescence_gate` carries this manager's
COMMITTED `runtime.destroy` proof to `Authority.satisfy_gate`, deriving the
authority, Work, participant, generation, gate token, runtime identity and
absence evidence from durable records; its only caller selectors are the attempt
and the retention policy that is half the key to that proof.
`intake.gate_discharge_of` is the discoverability read that makes the obligation
survive a terminal cleanup axis. `AuthorityPort.satisfy_gate` is the new port
capability. `authorize_cleanup` keeps its exact signature, ending and authority
effect. This explicitly supersedes the opening observation as current candidate
behaviour; the reproduction and approval history remain valid evidence.

Candidate hashes, the full account, the verification results and the two
judgements taken during implementation are in PROGRESS.

**Confirmed incompatible caller, reported as the review directed rather than
worked around.** `AuthorityPort.__init__` refuses a session missing any member of
`SESSION_OPERATIONS`, and four session-shaped objects carry no `satisfy_gate` —
including BOTH production deployments in this distribution,
`tools/single_worker.py`'s `_AuthoritySession` and `tools/dogfood_operator.py`'s
facade. Requiring the member would stop both from composing a port at all and
would need edits in paths this Work does not own. So the capability is named in
a new `OPTIONAL_SESSION_OPERATIONS` tuple: typed when the session carries it,
and answered by a typed `refused/capability` when it does not. Nothing durable
is spent before that refusal, which is what makes a late one safe here and not
for `claim`.

**Confirmed downstream boundary, which provider acceptance was required to
identify honestly.** This act does not repair either deployment. Each needs its
session wrapper to forward the member first: `_AuthoritySession` is the
consumer's own scheduled path, and `tools/dogfood_operator.py` is a SECOND
consumer boundary that no part of this Work's approved scope names.

**Open — one scope decision, blocking full green.**
`tests/manager/test_text_sweep.py` holds a second surface catalog derived from
`worker_manager.__all__`, and its completeness case now fails naming exactly
`discharge_quiescence_gate` and `gate_discharge_of`. That path is not among the
six approved and the proposal above says an additional needed path is a scope
finding before editing, so it was not touched and the candidate leaves that one
case red. It is not a behaviour of the act: both new surfaces were verified,
against the sweep's own spoiling logic and without editing it, to refuse
unstorable text in every operand the table drives. PROGRESS carries the exact
two entries. A seventh path is requested for those two lines and nothing else.

Independent acceptance of this implementation remains required before this Work
closes; the joined serving and restart evidence stays owed by W119114.

## Independent review — 2026-09-08, claim119842, changes requested

Confirmed by offline receiving-boundary probes: the new act accepts a changed
runtime identity against the old committed cleanup (only operation_id compared,
signature binding omitted); a wrong-gate/non-success injected answer creates a
false durable discharge; and a same-participant session whose projection names
a different Authority is never compared to the fixed assignment Authority.
Exact causes, corrections and evidence are in
`review-2026-09-08T14-27-00Z.md` and `evidence/review-119842-*`.
The 21 new tests pass, but do not cover these controls; 250 existing test
methods remain unchanged. No implementation acceptance or dependency release.

This explicitly supersedes the implementation outcome's claim that step 3 is
fully delivered. Runtime/proof, injected-answer and Authority binding remain
acceptance blockers. Registry scope does not waive receipt value/relationship
ownership. Optional satisfy_gate is compatible with the approved separate act;
deployment forwarding and joined recovery remain downstream. M119837's seventh
catalog path is pending owner disposition and its failure is not waived.

Consumer scope is no longer pending: owner event119712 approved the exact
recovery plan, placed as W119733 plus W119114 (placement119745/119746).
That supersedes earlier pending-consumer wording without closing either Work.

## 2026-09-08 — review 14:27:00Z corrected, claim119921

**Confirmed corrected.** All three findings are fixed inside the same six
approved paths; no seventh path was needed or taken, and every pre-existing
assertion, `authorize_cleanup`, `destroy_operation` and `_committed` are
untouched. Candidate: `authority_port.py`
`174d621edfb1d8b694c9b1cbfe511d8b56c8a89e97ed89bc08534e1a029f64c6`,
`intake.py` `0ccc85d7e92fdce8e701ebe2d728153632252b33dae4edf5ff7b13381a70f26e`,
`tests/manager/test_intake.py`
`99e1e929c069b60cfc70a952a502e3f679c97da293849111851e927527f4f6e7`; the other
three unchanged. This explicitly supersedes the previous candidate's identity-
only proof comparison, member-set-only answer owning and participant-only
binding as current behaviour; the reviewer's measurements remain valid evidence
about those superseded bytes.

- **P1 proof binding.** `_absence_proof` owns the committed cleanup's nested
  operation and compares identity AND signature digest against the operation
  derived from the current attempt row. The signature is the half carrying
  `runtime_id`, so a changed, absent or malformed runtime refuses before the
  Authority is asked.
- **P1 answer owning.** The port requires the reply's gate to equal the gate
  asked about, its kind to be text and its phase to be the discharged phase;
  intake requires the quiescence kind and journals the ANSWERED values. Both
  public exits adopt the receipt against an explicit member and value contract,
  so a journalled row that does not say a quiescence gate was released is
  refused rather than reported to consumer recovery as a completion.
- **P2 authority binding.** `_same_authority` proves the full Work reference
  through the port's existing `project_work` projection before any new remote
  act, after the committed local replay. No new session capability was taken.

Measured: the reviewer's own `evidence/review-119842-probe.py`, re-run
unmodified, now refuses all three scenarios with the gate closed, no evidence
sent and no discoverable receipt — retained as
`evidence/correction-119921-probe.json`. Reverting each correction singly makes
its own controls fail. 34 focused tests, 790 manager tests and 157
port-constructing tests pass.

**One reconciliation the reviewer should check explicitly.** The requested
"lost-local-receipt followed by later Work movement" control and the requested
pre-remote Authority binding conflict in one case, so it is split rather than
resolved by whichever made a test pass: later Work movement under the SAME
Authority replays without consulting today's gate or phase; a lost receipt under
a FOREIGN Authority refuses, because finishing it means making the remote call
again and that session may not. What may not gate a replay is mutable Work
state; the Authority binding is not that. Both cases are measured.

`tests/manager/test_text_sweep.py`'s completeness failure is unchanged and
unwaived — M119837's seventh-path decision is still pending. Independent
acceptance remains required; W119114 and W119733 still own the joined proof.

## Independent re-review — 2026-09-08, claim119974

The original changed-runtime proof, mismatched remote answer and foreign-
Authority crossing findings are corrected for the hashes in
`review-2026-09-08T14-43-50Z.md`. The same-Authority/later-Work-movement replay
versus foreign-Authority refusal distinction is accepted. Thirty-four focused
controls pass independently; original cleanup helpers and250 baseline test
methods remain unchanged.

**Confirmed remaining P2.** The new adopted receipt contract checks individual
values but not their fixed attempt/journal relationships. On both public exits,
a journal result with another attempt_id, gate, operation_id or runtime_id is
returned as the selected completion, while assignment=null raises raw TypeError.
An empty assignment correctly refuses. Exact offline fixture results and hashes
are in `evidence/review-119974-probe.json`; no coordination store was accessed.
This explicitly supersedes the correction account's claim that adopted receipt
ownership is complete; the original three remote/proof findings remain resolved.

Finish the local nested shape and signed/fixed relationship contract as detailed
in the review, preserving replay independent of mutable runtime/Work state.
M119837's seventh catalog path remains pending, its failure unwaived. Provider
acceptance and downstream joined proof remain open; route correction through
baton.impl and independent baton.bug review. No scope expansion or application
change by reviewer.

## 2026-09-08 — receipt relationship contract completed, claim120006

**Confirmed corrected.** Review `review-2026-09-08T14-43-50Z.md`'s P2 is fixed
in two of the six approved paths: `intake.py`
`d9a4fdd17f0e817f0275540a1c8f42cc8f8210f3e30c4bb1ca97d1a8c80f67d9` and
`tests/manager/test_intake.py`
`a5ebee13844b0eeba181853102286db0781157dc557ff058ad65784b8e541855`; the other
four unchanged. No seventh path taken. This supersedes the previous candidate's
field-by-field-only receipt contract as current behaviour; the reviewer's six
counterexamples remain valid evidence about those superseded bytes.

`_adopted_discharge` now owns the nested assignment and its Work reference as
exact documents before any keyword unpacking, derives the gate from that
assignment rather than believing it, binds the receipt to the selected operation
identity and the selected attempt's immutable fixed assignment, and — the piece
that was missing — recomposes the receipt's own five signed operands and
compares them with the signature the journal recorded for that discharge. The
attempt, the fixed assignment, the gate, the runtime and the cleanup operation
are one signed relationship, so a member changed on its own cannot reproduce it.
All three exits use the same contract, including the one that composes the
receipt before journalling it. Nothing mutable is read, so a correct receipt
still replays after later Work movement, and absence stays a different answer
from a present malformed receipt.

Measured: the reviewer's `evidence/review-119974-probe.py`, re-run unmodified,
now answers `ContractRefusal` for all six rows on both public exits — retained
as `evidence/correction-120006-probe.json`. Reverting only the relationship
half, keeping every field check, fails 13 of the new subtests. 40 focused, 796
manager and 157 port-constructing tests pass.

`test_text_sweep`'s completeness failure is unchanged and unwaived; M119837 is
still pending. Independent acceptance remains required, and W119114/W119733
still own the joined proof.

## Independent re-review — 2026-09-08, claim120038

The nested receipt and signed/fixed relationship correction is verified for the
hashes in `review-2026-09-08T14-53-10Z.md`;40 focused tests pass independently.
This supersedes the earlier unresolved nested/relationship cases. One P2
presence edge remains: gate_discharge_of returns None for a PRESENT wrong-kind
record or JSON-null result, while replay refuses both integrity/schema. SQL
NULL is blocked by the store and is not this finding. Finish the two discovery
branches and add both-exit controls within the already approved source/test
paths; no new protocol rule or mutable-state replay check is requested.

Return to baton.ops to dispose still-pending M119837's exact two catalog entries
in the seventh path, then baton.impl for approved catalog work and the local
presence correction, followed by independent review. This supersedes any claim
that absence-versus-malformed ownership is complete. The completeness failure
remains unwaived; provider and consumer Work remain open.

Evidence-custody correction: the author's unmodified rerun of reviewer script
review-119974-probe.py overwrote its fixed review-119974-probe.json output with
the corrected candidate. The file retains the old claim label but is now rerun
evidence. Original failing outcomes remain in the append-only14:43:50 review;
no historical output is reconstructed. The script's fixed-path design and rerun
both contributed. Use new claim-specific exclusive output files for reruns.
This is an operational reproduction-record issue, not a Baton protocol defect.

## 2026-09-08 — approved seventh path, M120088

**Confirmed decision.** baton.slaw approves
`v12/python/tests/manager/test_text_sweep.py` **solely** for the two
callable-table entries specified in M119837 — `discharge_quiescence_gate` and
`gate_discharge_of` — preserving all existing assertions and every other line of
that file. This supersedes the pending status of M119837 and the reviews' note
that the seventh path was unauthorized; the exported-surface completeness
failure it fixes was recorded and unwaived throughout.

The approved path set for this Work is therefore the original six plus that one,
and the extension buys exactly two table entries. Independent acceptance is still
required, and no other content of that module is in scope.

Pinned by baton.claude under claim120100 before editing, as the approval directs.

## 2026-09-08 — presence gap and approved catalog completed, claim120100

**Confirmed corrected.** `review-2026-09-08T14-53-10Z.md`'s P2 is fixed and the
approved seventh path is used for exactly its two entries. Candidate:
`intake.py` `6c00c441bc7b2356fddfd9f0867db59e05d6b96128dbf8918fc3b67ea46c89c7`,
`tests/manager/test_intake.py`
`facd32dd1d65c02e85253e0db91e12856258c7f6aa0c16c6a2d323236403e675`,
`tests/manager/test_text_sweep.py`
`f3eff0216f98f4cd4174d4d016283612f88306ee75380cbb7ea26f802e5dbd50`; the other
four unchanged. This supersedes the previous candidate's split presence handling
as current behaviour.

`_recorded_discharge` decides presence once for BOTH public exits: only a
genuinely absent operation answers `None`, and a present record of the wrong
kind or with a null decoded result refuses `integrity/schema` from either
entry. The two exits had each written their own version and disagreed, which is
what let discovery report an integrity failure as outstanding work.

`tests/manager/test_text_sweep.py` gains exactly the two callable-table entries
M119837 specified and M120088 approved, twelve inserted lines and no deletions.
The exported-surface completeness failure that had been red and unwaived since
M119832 is now green.

Measured: `evidence/correction-120100-probe.py` (claim-specific, exclusive
output) shows both exits agreeing `integrity/schema` on the JSON-null result,
the foreign kind and the list result, with the SQL-NULL write still refused by
the store's own CHECK. Reverting only discovery's presence handling fails the
two subtests on the discovery exit alone. 42 focused, 801 manager (including
the sweep) and 157 port-constructing tests pass.

**Evidence-custody correction, and the fault was the author's.** Re-running
`review-119974-probe.py` unmodified overwrote its fixed output path, so that
file now carries claim120006 results under a claim119974 label. Nothing is
reconstructed or restored; the append-only 14:43:50Z review and
`correction-120006-probe.json` remain the two halves of that history. Reviewer
scenarios are reproduced in claim-specific scripts with exclusive output from
here on.

Independent acceptance remains required; W119114 and W119733 still own the
joined proof and their dependencies stay intact.

## Independent provider acceptance — 2026-09-08, claim120163

**Confirmed.** `review-2026-09-08T15-10-00Z.md` accepts the seven-path candidate
bound by `evidence/review-120163-audit.json`, manifest SHA-256
`3595f529914c94ac590237a58416e6669b10ed18e4a83f1459495d310ae65c85`.
Both public exits share the presence reader and reject present invalid evidence;
the approved catalog additions close the previously unwaived completeness gap.
This explicitly supersedes the preceding pending-acceptance and unresolved
presence/catalog status. Earlier proof, Authority and receipt corrections remain
accepted. All 253 baseline test methods are unchanged; the seventh file differs
in executable content only by its two approved entries. Cleanup helpers remain
unchanged and the scoped whitespace check passes.

The author-retained 42/801/157 passes and claim120100 probe were audited against
the candidate hashes, not rerun or relabelled as reviewer execution. The reviewer
ran only the candidate/scope audit. No remaining provider deliverable requires a
split or another implementation pass. Close the provider satisfying; the
separately accountable W119733 recovery and W119114 joined proof remain owed.
This acceptance does not certify deployment forwarding, ordinary serving/restart
or the composed lifecycle, and changes no downstream scope. No application,
existing-test or Git-state edits were made by this review.
