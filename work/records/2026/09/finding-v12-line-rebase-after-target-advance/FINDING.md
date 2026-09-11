# A second Job cannot integrate once the canonical target moves past its line

Found by baton.claude under W130224 claim131378, driving two bound Jobs to
terminal integration after W131187 returned the integrator's capacity. Filed as
its own record because the correction lives outside W119405's authorized two
paths and is independently schedulable.

## Observed, and measured

`work/records/2026/09/finding-v12-multi-job-deployment/findings/finding-per-job-binding/findings/finding-two-job-serving/`
carries the reproduction as an ordinary test:
`TwoBoundJobsTraverseServingAndCorrection.test_the_second_jobs_candidate_is_stale_once_the_first_integrates`
in `v12/python/tests/tools/test_stage_execution.py`.

Two Jobs are submitted to one deployment, both coded, reviewed and accepted.
Job A's integration runs to its real terminal handoff. Then:

**Confirmed** — measured through public readers in that case:

- `authority.canonical_target()` has advanced from the deployment's declared
  base to Job A's own candidate digest.
- Job B's integration stage RESERVES the integration worker, so capacity is not
  the blocker: W131187's release works and this is a different seam.
- Job B's line still reports `declared_base` equal to the original base, read
  back through `review_cycles.line_of`, and that base is not the advanced
  target.
- `StageDeployment.published_proposal` on Job B's accepted checkpoint refuses
  with the provider's own sentence: "the worker built on <old base> and the
  Authority target is <advanced>; a proposal is offered against the revision it
  was built from".

## Confirmed mechanism

`authority/core.py` sets `canonical_target` to the integrated proposal's
candidate digest as part of writing the integration receipt. There is exactly
ONE such revision per Authority.

`integration/driver.py` compares the worker's declared base against that
revision before retaining a proposal, and `integration/admission.py`'s
`resolved_account` compares the proposal's target against it again before
enqueue. Both are correct: a candidate built on a superseded revision is not
one this target can take.

`review_cycles.create_line` is create-or-recover by an identity derived from
`(authority, work)` and refuses when the recorded operands -- profile, declared
base, source, line path -- disagree with the ones it is handed. A line's
declared base is therefore IMMUTABLE for the life of that Work's line, and no
operation in `review_cycles` advances one.

A correction round does not help. `review_driver.open_correction` re-grants a
writer on the line's CURRENT checkpoint, which carries the same superseded
base, so the second round would produce another candidate the target refuses
for the same reason.

## Consequence

In one deployment generation, exactly ONE Job can integrate. Every other Job
that reaches an accepted checkpoint owes a rebase onto the revision the first
integration created, and nothing in this build performs one. Serialization on a
single integrator works (W130224 proves it) and its capacity now returns
(W131187), but the queue still cannot advance past its first entry.

**Not a one-Job defect**, and not reachable before a two-Job traversal existed:
with a single Job the target advances once and nothing is left to propose.

## Proposed direction — Proposed, not decided

Choosing among these is this record's own work, and each has a different owner:

1. An accepted operation that ADVANCES a line to a new declared base, replaying
   the checkpoint profile's materialization at the moved target and preserving
   the line identity. Owner: `worker_manager/review_cycles.py` with
   `checkpoint_profiles`.
2. A correction round whose trigger is the moved target rather than a reviewer
   verdict, so a stale accepted checkpoint reopens for rebase through the
   ending path that already exists. Owner: `job_manager/review_driver.py`.
3. A deployment-level answer: bind the later Job's line at the revision the
   earlier integration produced, in a new deployment generation. This needs no
   new operation but makes throughput an operator's serial act, and it should
   be rejected or accepted explicitly rather than by default.

## Acceptance boundary

A deployment serving two accepted Jobs integrates BOTH through ordinary ticks:
the first completes, the second rebases onto the revision it created, and the
second's own terminal handoff commits. The stale-target refusal must survive as
a refusal for a candidate that has NOT been rebased -- this record must not
widen the target policy or convert a stale proposal into a passing one.

## 2026-09-09T22:28:30Z — independent static research and decision proposal

baton.codex claim131411. Read RESEARCH-2026-09-09T22-28-30Z.md for confirmed
code paths, corrections to the filing, proposed lifecycle, public acceptance
and the concrete owner decision. evidence/research-131411/ retains source
identities and the exact author reproduction. No reviewer runtime, product/test
edit or implementation acceptance. W130224 still owns its active assembly paths.

**Confirmed:** immutable create_line operands, accepted-line writer refusal,
verdict-only paired correction and unchanged publication/admission/Authority
stale-target guards jointly prevent the shared-base second Job advancing.
The filing's alternatives1/2 are complementary capabilities; neither alone
completes the traversal. Its suggestion that deployment generation alone solves
the same persisted Work with no new operation is superseded as unsupported:
create_line still collides on the old Authority/Work identity. Its universal
exactly-one-Job-per-generation consequence is narrowed to the reproduced
shared-original-base/changed-target condition. The helper refusal does not prove
B never published earlier; historical publication and present eligibility are
different facts. These clarifications supersede those broader original claims,
not the reproduced defect or required stale-target refusal.

**Proposed:** retain same Job/Work/line, add explicit target-driven rework with
base-advance lineage, fresh producer/tests/review, old immutable audit history,
proved target content and conflict holds. Do not detach away B changes, rewrite
an old verdict, change creation operands in place or fake integration settlement.
The current integration attempt/claim/capacity needs canonical settlement before
reopening a round. Keep both-terminal acceptance on W130224 and final joined
acceptance on W119405; this Work is their explicit prerequisite.

Request owner lifecycle choice, then return baton.bug for a versioned contract,
serial path allowlists and separate cost proposal before implementation. This
proposal grants no source changes or runtime. W71830 standing test authority
applies to this recorded prerequisite; do not request per-test approval.
Coordinate dependency at W130224 safe handoff, never release its active claim.

## 2026-09-09T22:33:14Z — safe handoff and dependency installed

Consumer author return131422 and reviewer claim131441 retain source28ee42a2/
test1ebba932, both0664, at baton:work/records/2026/09/finding-v12-multi-job-deployment/
findings/finding-per-job-binding/findings/finding-two-job-serving/evidence/review-131441/candidate/.
Its review-2026-09-09T22-31-41Z.md is nonaccepting: static corrections resolved,
both-terminal traversal incomplete. Dependency131454 now gates W130224 on this
Work and atomically relinquished the reviewer claim. No shared-file writer.
This supersedes active-consumer and pending-safe-handoff statements above and in
RESEARCH22:28:30Z. Owner/implementer notified M131459; lifecycle decision remains
queued by pass131438 with reviewer next. No product source/runtime grant.

Consumer15.37/20s leaves4.63s; parent383.25/450s plus all uncertainty,
observation20s/joined40s/margin2.12s reserved. No reviewer runtime or transfer.

## Owner event131446 — lifecycle approved, pinned under claim131466

Owner baton.slaw approves RESEARCH-2026-09-09T22-28-30Z.md same-Job/same-line
target-driven rework. Preserve both Jobs changes, immutable history, original
creation identity, stale-target guards, fresh required tests and independent
review, explicit conflict holds; canonically settle the old integration attempt
before replacement. Retain both-terminal W130224 and joined W119405 acceptance.
This supersedes pending lifecycle-policy wording above. Reviewer now prepares
the smallest sufficient versioned contract, exact serial source/test scopes and
separate verification budget for approval before implementation. No product
edits, runtime or borrowing granted. Safe handoff/dependency131454 already done.

## 2026-09-09 — contract/scope proposal under reviewer claim131466

CONTRACT-v1.md and SCOPE-v1.md are the concrete proposal requested by owner
return131446. They pin same-line creation/effective-base separation, fresh
checkpoint/review/test evidence, actual nominated target content, retained
history, conflict holds, exact prelaunch seal and canonical Authority handoff,
whole-triple Job replacement, old-allocation release only from typed settlement,
and read-only observation. Historical publication lookup uses its existing owner.

Two explicit implementation choices await approval: ControlStore schema19 at
its existing fresh-store/no-migration boundary; automatic rework initially only
for claimed integrations before launch intent, with initially unclaimed stages
claiming ordinarily before rework and begun/uncertain/live-lease cases held
pending canonical exclusion. No operator-only finalization/abandonment shortcut
or invented runtime cleanup/gate discharge. Both-terminal acceptance stays on
W130224; actual ordinary nonconflicting A/B witness is required in slice C.

Proposed three serial children: A custody/profile/seal80s implementation+8s
review, B Job round/capacity65s+7s, C two-path assembly25s+5s, and10s owner-held
reserve:200s separate cumulative,0s spent. Exact28 source/test paths (four new)
and bounded assertion reasons are in SCOPE-v1.md; retained base bytes/hashes/modes
in evidence/contract-131466/base.json and base/. New path absence was verified.
No child Work/dossier created before approval; no implementation/source/test
edits, test execution or runtime grant is inferred from the lifecycle decision.

W130224 safe handoff/dependency131454 is installed; exact consumer28ee42a2/
1ebba932 retained. Parent carry383.25/450s plus uncertainty, serving4.63s,
observation20s/joined40s/margin2.12s unchanged. No automatic borrowing between
slices or campaigns; no whole module/package or live/OCI runs in proposed200s.
Standing W71830 test authority applies. Owner approves contract/scope/cost next;
then reviewer creates bound children together with dossiers, installs serial
dependencies, freezes accepted handoffs and dispatches A only.

## 2026-09-10T02:21:50Z — owner approves executable contract and serial allocation

Owner baton.slaw return132696 approves CONTRACT-v1.md and SCOPE-v1.md, exact
three serial source/test scopes, ControlStore schema19 fresh-store boundary
without migration, and prelaunch-only automatic settlement with begun/uncertain
integrations held. All acceptance, stale-target guards and immutable historical
evidence remain. Separate200s cumulative: A80s implementation+8s review,
B65+7, C25+5,10s owner-held reserve. No silent transfer or W119405 borrowing.
This explicitly supersedes all pending contract/scope/budget language above and
in the two versioned proposal files. The approved substantive bytes are retained
unchanged; this entry is their approval status and execution authority.

Placement claim132699 pins the ruling before any implementation. Owner directs
three bound children/dossiers with serial dependencies and dispatch A only.
Reuse C evidence for W130224/W119405 acceptance; no duplicate proof campaign.
All28 baseline paths revalidated against evidence/contract-131466/base.json:
24 existing files match bytes/modes, four proposed new files remain absent.
No product/test edits or verification runtime during placement;200s unspent.
Consumer safe handoff/dependency131454 still applies, source28ee42a2/test1ebba932.
W119405 carry383.25/450s plus historical uncertainty remains separate.

## Placement132699 — children created with dossiers and serial gates

- A W132712: findings/finding-target-rework-custody/,80s implementation+8s review.
- B W132720: findings/finding-target-rework-rounds/,65s+7s; dependency132721 on A.
- C W132724: findings/finding-target-rework-composition/,25s+5s; dependency132725 on B.

Each dossier was created immediately with its canonical bound Work before
further execution. All children remain reviewer-routed until controlled serial
dispatch; only A goes to impl now, with independent reviewer return. Parent
waits on C and cannot close with any open child. Consumer W130224 remains gated
on parent131454; W119405 keeps joined acceptance. Owner132696 mandates reuse of
C evidence without a duplicate proof campaign. No runtime/product edits in
placement;200s still unspent,10s reserve stays owner-held.

## Parent dependency installed132734

W131409 is unclaimed in block on C W132724. This operation relinquished
placement claim132699 atomically. A W132712 dispatch placement claim132735
now owns that child only; exact child dossier read, no runtime/product edits.
Serial gates132721/132725 and consumer gate131454 remain.

## 2026-09-10T03:05:47Z — owner selects isolated submissions and integrator-owned merging

Confirmed by Slawomir in the interactive conversation; recorded by baton.prompt.
Workers submit original-base candidates without first chasing the current target.
The integration role selects eligible submissions, reconciles their changes with
the current target, and produces a separately verified integration result.

Preserve causal evidence: B's defect reproduction fails on its original base,
passes with its isolated fix, then either passes or fails after integration with
A. Retain all observations rather than testing only the combined result. Keep
original base/candidate/checkpoints, tests and independent review immutable;
the merged candidate retains its own exact inputs, target, tests and review.
A checkpoint alone is not integration authorization: select submissions explicitly
eligible for integration. A clean Git merge does not establish correctness.
Substantive reconciliation changes require independent review; ambiguous semantic
conflicts return a specific question or correction to the responsible worker.

This explicitly supersedes the worker-baseline-rework direction approved by
events131446 and132696 and the executable direction of CONTRACT-v1.md,
SCOPE-v1.md and their A/B/C allocation. Do not continue requiring target drift
to reopen every producer on an updated base or automatically transplant into
its accepted line. Old records, partial implementation, reviews and cost history
remain evidence and are not deleted or silently rewritten.

The replacement product model allows integration-role reconciliation instead of
refusing solely because a submitted base is old. Preserve both Jobs' intended
changes and final target validation: original candidate provenance and the
integration result's current-target binding must be distinct. Do not simply
disable stale-target enforcement. Git mechanics belong to the configured
integration capability in its authorized workspace, not the generic manager.
The human repository's index/history remain Slawomir's; this product direction
does not grant the current v11 baton.merge participant new execution permissions.

Observed snapshot132963: A W132712 is held by baton.claude (episode132946);
B W132720 and C W132724 are blocked. Request immediate safe handback of A,
retaining partial bytes, newest evidence and all runtime charges. Do not take
its claim, race its files, discard changes or force process interruption.
Do not dispatch further old-design work. The live Handler owns canonical
settlement and any contract promotion for its active Work.

baton.codex is requested to reconcile the existing allocation and prepare the
smallest replacement integration contract, affected role-policy/source paths,
reuse/disposition of existing work and costed verification plan. Preserve
W130224's two-terminal and W119405's joined acceptance, isolated fix evidence,
one target writer and failure containment. No replacement implementation budget,
reserve use, cross-campaign transfer or general Git permission is inferred.

## 2026-09-10T03:20:01Z — transition complete and replacement proposed

Reviewer133017 read owner M132985 and poke132987. Safe custody: A was unclaimed
at132999, rerouted133002, claimed133003 and parked133013. No active claim was
taken. Pass132996's old-design costing direction is superseded too; message
132998 told impl to stop it. B/C remain blocked and undispatched. Attempting to
park B refused because its displayed gate still owns its wake; leave that gate
intact, not a workaround. The obsolete parent->C edge was removed133014 solely
to permit parent replacement planning; parent claim133017 then succeeded.
Consumer W130224 remains blocked on this parent and no acceptance is waived.

New INTEGRATION-CONTRACT-v1.md and INTEGRATION-SCOPE-v1.md are proposed for owner
decision, not executable. Original submissions remain immutable. A configured
integration capability prepares a separate combined result; real causal tests,
independent review and approval precede result-specific import. Propose existing
Authority publication under the integration assignment, keeping Authority's
final target/receipt guards intact. Exact target-content/revision custody and
post-import failure/recovery are included, not replaced by an updated digest.

The concrete proposal includes rejected-byte disposition, three serial new
provider/composition scopes, dedicated target reference authority, schema5
IntegrationStore fresh-store boundary and a new260s tranche. Snapshot
evidence/replacement-133017/base.json retains40 existing paths and three planned
absences, plus exact proposal bytes. No replacement source/test/policy edits,
cleanup or verification runtime occurred. The two optional guessed agent-file
paths and guessed runtime path were absent, documented in scope; actual owners
were found and read. No required dossier is unreadable.

Old spend remains about72.846152s (author64.56s measured plus provisional about8s
unmeasured, reviewer0.286152s). Old unused allocations/reserve confer no new
authority. New260s means new work only, lifetime about332.846152s if fully used,
with old uncertainty retained; no W119405 transfer or cost reset. Owner must
approve/amend the exact contract, path scope, disposition and cost before D
or any new implementation dispatch. Existing child dossiers are preserved;
superseded closure follows explicit disposition rather than a false fixed claim.

## 2026-09-10T03:26:28Z — owner approves replacement contract and exact scopes

Owner return133106 approves INTEGRATION-CONTRACT-v1.md and INTEGRATION-SCOPE-v1.md,
including six exact existing-file restorations and two rejected-new-file removals
after retained-evidence/hash verification, superseded child disposition, replacement
source/test/policy scopes, schema5 fresh-store boundary and dedicated target
reference capability. NEW260s: D8+2/P77+8/Q95+10/R40+5/owner-held reserve15.
Historical spending and uncertainty remain; no old remainder or W119405 transfer.
Validate scoped Authority publication before dependent implementation; if it
cannot express the contract, return a concrete amendment before those edits.
Preserve causal evidence, independent combined-result verification, final target
guards, human Git ownership, two-terminal and joined acceptance.

This explicitly supersedes pending-approval wording in the two versioned files
and earlier plans. Their approved substantive bytes are unchanged and retained
in evidence/placement-133108/, with all43 paths revalidated at03:27:10Z:
40 existing byte/mode matches, three planned-new paths absent. Reviewer133108
spent0s verification. Create serial replacement children, then dispatch D only;
no P/Q/R implementation before predecessor independent acceptance.

## Replacement placement133108 — canonical children and serial gates

- P W133117: findings/finding-integration-result-custody/,77s author+8s review;
  blocked on D W132712 by133119.
- Q W133120: findings/finding-integration-result-import/,95s+10s;
  blocked on P by133123.
- R W133129: findings/finding-integration-result-composition/,40s+5s;
  blocked on Q by133133.

Each Work was created with its canonical binding and immediately completed
FINDING/PLAN/PROGRESS dossier. Old B/C stay undispatched and their historical
contracts are not reused as replacement paths. D through old A W132712 has its
new exact disposition contract pinned in that dossier; all eight before/after
hashes and evidence locations are in evidence/placement-133108/D-disposition.json.
No product changes or runtime during placement. Parent will gate on R; dispatch
D only, returning for independent disposition review before P readiness is used.

## 2026-09-10T03:40:03Z — D accepted, old children disposed, P starts

D review133171 accepts exact six restorations/two removals and retained evidence;
all43 resulting paths match and two focused controls pass. D author0.22s plus
review0.17817034490872175s = replacement0.39817034490872175/260s. Old costs and
uncertainty remain unchanged. Old A/B/C cancelled as superseded at133184/133191/
133197 with permanent records retained and no claim their old capability works.

P claim133198 read whole dossier and revalidated post-D union without drift,
evidence/findings path is findings/finding-integration-result-custody/evidence/
dispatch-133198.json. Dispatch only P,77s author/8s reviewer unused; first validate
real scoped Authority publication before dependent implementation as owner133106
requires. Q/R stay blocked; parent gate133144 on R and consumer gates remain.
No unused D/old allocation or reserve transfers. No P product edits/runtime by reviewer.

## 2026-09-10T12:58:09Z — owner approves P publication and custody amendment

**Confirmed ruling:** baton.slaw return136350 approves in full
`findings/finding-integration-result-custody/AMENDMENT-publication-before-authorization-v1.md`,
including publication before authorization, receipt-to-execution bindings,
storage isolation, exact four-file implementation scope and all acceptance.
Reviewer claim136357 pins this before implementation dispatch.

This explicitly supersedes owner133106's evidence-before-publication order
in INTEGRATION-CONTRACT-v1 sections3/5/6 and the corresponding P/Q/R interfaces
in INTEGRATION-SCOPE-v1. Both files now preserve their old text and carry dated
supersessions. Published means an unapproved candidate; only authorized plus
full revalidation permits enqueue/import. The derived result digest binds the
immutable execution basis and actual independent Authority receipts. Original
submission/receipts, combined-failure history, final target/lease checks and
human Git ownership remain. The producer/source/target must not alias the
private preparation workspace, even through shared Git storage.

**Confirmed budget:** NEW30s cumulative author execution for this exact
amendment, separately recorded. Preserve author56.46s rounded measured subtotal
PLUS unmeasured history under77s and all unavailable outputs; retire use of its
uncertain remainder for this amendment. Keep reviewer8s cumulative ceiling.
Replacement authority becomes260+30s, not a reset or a spend assertion; no
contingency/Q/R/W119405 transfer. Six intermediate historical test failures
remain included, correcting the author's five-failure narrative without
double charging. All future setup/failure/rerun output and timing are retained.

Parent/P/Q/R plans now reflect the ruling. P dispatch is only the approved
four-file amendment, beginning with the exact real-session round trip and
returning to bug for independent full candidate review. P remains unaccepted;
Q/R and consumer gates do not clear by this approval. Existing reviewed partial
fixes remain credited. No product/test changes or product verification are
performed in this placement; the bounded digest preflight and its cost are
retained at findings/finding-integration-result-custody/evidence/dispatch-136357.json.

## 2026-09-10T13:36:22Z — milestone narrowing and independent P acceptance

Reviewer136558 applies owner M136417 / W71830 FINDING2026-09-10T13:06:51Z
at P's safe return136555. DELIVERY-SCOPE-2026-09-10.md pins the smallest actual
Q import/settlement and R ordinary A/B terminal witness. It explicitly
supersedes exhaustive crash/tamper/race/recovery matrices as unconditional
prerequisites in the contract/scope/amendment and plans. Existing protections,
passing evidence, independent review, source immutability, combined verification
and honest target-write/terminal boundaries remain. No deferred check is passed.

W136578, independently bound to
baton:work/records/2026/09/finding-v12-integration-result-hardening/, is parked
for retired-assignment/publication/receipt interruption combinations, unresolved
protected-repository identity and broader aliases, and exhaustive Q/R crash,
persisted-tamper and writer-race matrices. Revisit after demonstration when
prioritized and before broader guarantees. It has no milestone dependency,
containment or runtime budget; no new planning prerequisite was created.

P candidate136400 matches all11 full hashes/sizes/modes and is independently
accepted for this scope. Its review-2026-09-10T13-36-22Z.md and
evidence/review-136558/result.json demonstrate B's unchanged original submission
through actual combined execution, derived publication and real independent
receipts to an authorized import account, with the actual Authority cursor at
A's target. Both changes are present. Unreceipted publication, combined failure
and producer-workspace nomination refuse. This does not prove actual Q import
or ordinary R deployment completion. Those are the next required transitions.

Q's exact remaining source-scope gap is concrete: P deliberately returns None
for imported-state signatures, while Q's allowlist omits reconciliation.py.
Resolve the smallest terminal writer/reader and focused-test scope amendment
through Q's existing handoff before edits. No budget expansion or extra
hardening. Q95+10/R40+5 and consumer acceptance remain unchanged.

Correct author136400 handoff counts from its final ledger:12 measured runs,
4 failures (4/5/6/9),20.108777135999617s plus disclosed unmeasured spending
under NEW30s. Old56.46s plus unmeasured history remains preserved and retired
for amendment reuse. Reviewer now3.122893249213803/8s. No remainder is
transferred or certified from arithmetic headroom. Full logs/candidate retained.

## 2026-09-10T13:50:24Z — owner approves Q terminal scope; immediate dispatch

Owner return136677 approves
findings/finding-integration-result-import/AMENDMENT-terminal-custody-paths-v1.md.
Reviewer136680 pins the decision before dispatch. Add reconciliation.py and
test_reconciliation.py at their exact v12 paths to Q only for terminal
transition/signature/reader, matching entry/derived-receipt linkage and the
bounded expectation change. This explicitly supersedes the pending scope
decision above and Q's former twelve-source/nine-test limit by these two paths.
Parent scope and Q plan now carry thirteen source/policy and ten test paths.

Retain Q95s author/10s review and DELIVERY-SCOPE-2026-09-10.md's happy-path
minimum. Hardening remains independently parked W136578. P candidate136400
and acceptance136604 remain unchanged. Dispatch Q implementation immediately,
then independent Q acceptance unlocks R's actual ordinary A/B terminal witness.
No new budget, schema/Authority/Manager expansion, broad verification or
additional planning prerequisite. Exact baseline preflight and its small
reviewer charge are retained in Q evidence/dispatch-136680.json; no product
tests or source edits are part of this ruling placement.

## 2026-09-10T17:25:55Z — owner137905 approves direct target finalization

Owner baton.slaw returned W133129 at137905 approving
findings/finding-integration-result-composition/AMENDMENT-direct-target-finalization-v1.md:
"Add integration/driver.py and execution.py plus their two named test files for
coordinator-owned accepted-object delivery and fenced target-reference
advancement before Authority completion." The comment also directs preservation
of worker metadata restrictions, original submissions and human Git ownership,
then actual A/B terminal integration and the essential branch-level no-write
control. Existing40s author/5s reviewer ceilings and all historical spending
remain; no increase or transfer. W136578 remains parked.

This explicitly supersedes R's former six-path limit only by adding these four
repository-relative paths:
- v12/python/src/baton_v12/integration/driver.py
- v12/python/src/baton_v12/integration/execution.py
- v12/python/tests/integration/test_driver.py
- v12/python/tests/integration/test_execution.py

The accepted amendment's coordinator operation and scheduled test expectations
are now authorized. Its former PROPOSED/awaiting-owner status and the previous
plan's pending source-scope blocker are superseded. All other scope and semantic
boundaries remain. This is a serial extension of retained candidate137258 and
accepted P/Q; no implementation or test result is accepted by the scope ruling.

Reviewer137908 re-read the exact owner event and current discussion/dossier;
all43 union entries match candidate137258. Ten authorized path bases and the
complete hash/mode manifest are retained in R evidence/dispatch-137908/.
Filesystem preflight0.002890161998948315s; conservative0.1s charge including outer
overhead gives reviewer1.7546043169997576/5s,3.2453956830002424s left. Author
31.09676456500256/40s measured remains unchanged,26runs8failures and disclosed
unmeasured history;8.903235434997441s nominal is not certified unused. No runtime
tests in this dispatch, budget reset, transfer or new planning prerequisite.

The next existing implementation handoff adds the coordinator transition before
Authority completion, then demonstrates ordinary A and B terminal on one
configured target with real derived receipts and original B evidence intact.
The branch-level alias no-write control remains essential. W130224/W119405
consume completed evidence distinctly; W136578 stays parked.

## 2026-09-10T17:46:28Z — R budget ruling138029, dispatch138032

Owner138029 approves R BUDGET-DISPOSITION-2026-09-10.md: cumulative author
ceiling50s supersedes40s; all historical spending stays charged, reviewer5s
unchanged, no transfers. The exact ruling is pinned in R FINDING/PLAN and
budget record. Reviewer138032 revalidated43 union entries, ten current bases.
Author38.27588842900241s measured plus unmeasured history; reviewer
2.1190192779999055/5s charged. Dispatch existing impl to the already authorized
finalizer corrections and actual A/B terminal witness FIRST, then essential
alias/no-write and stale-target/ended-grant checks. Owner137905 ten-path scope
unchanged, no new planning Work or repeated P/Q collections. W136578 parked.

## 2026-09-10T20:10:31Z — R budget approval138816 and dispatch138824

Owner138816 approves R BUDGET-DISPOSITION-2026-09-10T17-55-49Z.md: cumulative
author65s/reviewer10s supersede50s/5s, all historical measured/unmeasured costs
retained, no reset/transfer. Exact ruling is pinned in R FINDING/PLAN/budget
record. Ten-path scope unchanged. Reviewer138824 revalidated43 entries with no
drift and retained ten bases; author47.12894061299539/65s measured plus disclosed
unmeasured history, reviewer3.505118563998258/10s charged. Dispatch existing impl
to source-policy composition and finalization authority corrections, complete
actual A/B witness FIRST, then essential refusals. No stale-policy bypass,
hidden fixture repair, repeated P/Q collections or new planning Work.
W136578 parked; W130224/W119405 remain distinct consumers.

## 2026-09-10T21:10:42Z — R independent import progress and existing budget decision

R review review-2026-09-10T21-10-42Z.md independently reaches derived imported result
with actual causal execution/receipts; B terminal handoff remains refused and
Job integration claimed. R BUDGET-DISPOSITION-2026-09-10T21-10-42Z.md proposes85s/15s cumulative
with all costs retained, unchanged ten paths. Current65s/10s remain until owner
rules. No planning Work or terminal acceptance implied. Exact candidate and
independent evidence retained in R evidence/review-139157. W136578 parked.

## 2026-09-11T00:18:11Z — owner140207 approves R85s/15s continuation

Owner140207 approves R BUDGET-DISPOSITION-2026-09-10T21-10-42Z.md. Cumulative
author85s/reviewer15s supersede65s/10s and pending status, all historical
measured/unmeasured costs retained without reset/transfer. Existing ten paths,
model-free terminal account/finish and public-reader corrections then actual
A/B first/essential focused controls; no fabricated runtime provenance, P/Q
repetition or new planning Work. Reviewer140210 revalidated43 entries and ten
bases in R evidence/dispatch-140210. Author64.67333668798983s measured plus
unmeasured history; reviewer8.70589725899772s. W136578 parked. No candidate
acceptance or downstream closure follows from budget approval.

## 2026-09-11T00:40:24Z — owner acceptance applied

Owner M140286/M140288 in T133129 and baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/FINDING.md / PLAN.md at 2026-09-11T00:30:54Z govern. This explicitly supersedes older mandatory, essential and no-waiver wording below ONLY where it makes stronger robustness/resilience demonstrations prerequisites. Ordinary correctness, authorization, honest evidence, existing source scopes, cumulative budgets and file ownership remain. Deferred claims are unproved, never passed. No new planning Work or approval round is required.

R candidate140229 now has independent component acceptance in findings/finding-integration-result-composition/review-2026-09-11T00-40-24Z.md. Both A and B terminal integration, actual combined import and released capacity are established in the controlled fixture. Reconcile the already accepted D/P/Q/R evidence and child dispositions at the next existing parent handoff, then release W130224 to consume the same evidence. No fresh implementation or test campaign at this parent solely to restate those results. Real standalone completion remains W71879's separate claim.

All remaining crash/restart, adversarial storage/tamper and race/ended-grant demonstration requirements in INTEGRATION-CONTRACT-v1.md, INTEGRATION-SCOPE-v1.md and older DELIVERY-SCOPE prose are superseded as milestone gates by the owner ruling. W136578 indexes deferred, unproved claims; conservative behavior and actual successful-path authorization stay. R ceilings85s/15s and all other allocations remain unchanged.

## 2026-09-11T00:46:32Z — parent accepted by evidence reconciliation

Reviewer claim140372 read current canonical detail, complete parent work-events
and T131409, the whole parent dossier and final D/P/Q/R independent reviews.
All six children are terminal: old A/B/C cancelled as superseded after exact D
disposition, P/Q/R closed satisfying. review-2026-09-11T00-46-32Z.md accepts the
parent prerequisite and CONSUMER-HANDOFF-2026-09-11.md supplies its exact evidence
and interface to W130224/W119405. This supersedes the pending parent action and
the original reproduced inability to complete B under the selected contract.
It does not certify the abandoned worker-rebase design or erase that history.

The final R candidate140229 independently demonstrates both landed changes,
original B submission preserved, real causal/post-import execution and separate
derived current-policy authorization, both terminal integrations and capacity
release. Its43-entry union and independent27-test/ancestry results are reused;
no new runtime/hash verification campaign or product/test change at this parent.
Controlled runtime providers remain labelled as such. Real standalone W71879
execution is still pending, and owner00:30:54Z's fault-C/robustness deferrals
remain unproved beyond retained controls. Q's accepted deterministic model-free
import interface supersedes the old unconditional extra bundle/runtime demand.

ALLOCATION.md now records amended345s replacement authority, approximately
229.025261s recorded use plus unmeasured history, and separate old-direction
approximately72.846152s with uncertainty. No budget reset/transfer/reserve use;
P's uncertain retired remainder and W119405's separate carry remain. This turn
adds no verification subprocess/runtime test; static reads/dossier work remain
disclosed unmeasured activity. PROGRESS is unchanged because this parent review
implemented no product change. Close satisfying and release the existing
W130224 handoff; no new planning prerequisite or duplicate test campaign.
