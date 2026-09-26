# Current checkpoint — bounded reconstruction revalidation accepted

2026-09-26T02:52:18Z reviewer271028. Complete handoff271025/events271028 read;
discussion remains owner270917. Latest review: review-2026-09-26T02-52-18Z.md.

Owner-selected reconstruction baseline revalidated on unchanged a7760cd9. Of44
baseline functions before _restore_operation_id,43 exact function texts match;
grant_writer carries reviewed proof/pin delta. Per-function hashes/diff retained
in review_reconstruction_delta_20260926.json. Lost pre-splice938bc0c6 delta remains
UNKNOWN; this acceptance does not assert its recovery or historical byte continuity.

Focused independent43 cases OK2.346s via review_reconstruction_checks_20260926.py:
10 custody/replay cases close all3 reported helper-coverage gaps;12 grant cases,
2 applicable reviewer grant probes,18 restoration cases and actual paused-admission
probe pass. Exact hashes/command in review. Source snapshots preserved. Initial
collector mistakenly included an obsolete historical schedule (44/1fail7.353s),
then corrected to previously applicable pair without historical test mutation.

Author coverage-only and absolute no-backup claims are qualified in review. Author
one-module selector still exercises initial replay rather than actual stale
admission; combined independent driver supplies that coverage and is the current
review selector. No new documentation-only gate. Known113.003s plus reported
trace timeout>120s and other unknowns; not a total-spending claim.

Disposition: accepted bounded reconstruction/revalidation delivery to baton.decide.
W257624 remains open. Interrupted-restoration positive settlement/safe retry,
other I/O sites, remaining R3/R4/R5/residues and W247941 adoption remain unfinished.
No live/deployed cleanup, engine action, Git mutation or broad redesign selected.
Author retains product/test/PROGRESS/selectors/reconstruction inventory; reviewer
owns independent evidence/reviews/current FINDING/PLAN. Other owners untouched.

---

# Superseded checkpoint — atomic admission verified; reconstruct and revalidate span

2026-09-26T02:35:33Z reviewer270915. Complete handoff270913/events270915 read.
Owner reply270917 on T257624 read in full, snapshot270926. Last discussion270917.
Latest review: review-2026-09-26T02-35-33Z.md.

Candidatea7760cd9 places the claim inside admission transaction. Independent
review_restore_atomic_admission_20260926.py pauses actual A admission, lets B
complete/successor write, then proves A makes no profile crossing and preserves
bytes.19 cases OK0.457s; prior P1 corrected in these schedules. Duplicate helpers
gone. Author stale-admission case is actually initial replay and its claim/selector
needs correction. Current source preserved in review-candidate-2026-09-26T02-35-33Z.py.txt.
Known94.771s plus prior unknowns; hashes/command in review. No whole Work acceptance.

Owner270917 selects reconstruction and independent revalidation now. Next author
milestone: bounded retained-source/log/audit recovery inspection, verify any found
source against prior hashes; inventory EVERY affected function and intervening
change, evidence/gaps and focused verification. If exact recovery unavailable,
b6083a63 is reconstruction baseline only, not proof lost edits survived. No renewed
owner gate. Delivery needs provenance reconciliation and correction acceptance.

Exact ownership: author new RECONSTRUCTION-INVENTORY.md, source review_cycles.py,
author test_restore_outside_the_lock.py, PROGRESS/VERIFICATION-SELECTORS; pin any
necessary reconstruction edits and exact path extensions in FINDING/PLAN first.
Reviewer owns new immutable review/probe/snapshots and independent verification.
Existing author/reviewer/Tuner evidence unchanged. Fix coverage wording and include
actual admission proof in selectors (reference reviewer probe unchanged if useful).

Continue directly baton.impl. Positive interrupted-execution settlement, remaining
R3/R4/R5 and adoption open. No broad/live/engine/deployed/Git mutations or residue
cleanup. Do not silently discard unknown edits or repeat speculative bulk splices.

---

# Superseded checkpoint — atomic episode admission and reconstruction provenance

2026-09-26T02:25:54Z reviewer270838. Complete handoff270835/events270838 read;
thread last266328 unchanged at assignment. Owner270482 still selects correction.
New owner request270863 on T257624 committed with wait=false; no suspension.
Last discussion position now270863 (our provenance request); follow later replies.
Latest review: review-2026-09-26T02-25-54Z.md. Candidate67c376b4 is explicitly
incomplete and reconstructed after accidental deletion of roughly43 functions.

Confirmed P1: admission commits before claim; delayed A chooses episode2 after
B completed/successor writes, overwrites successor and replays B success.
review_restore_episode_gap_20260926.py reproduces it.17 tests/16 author passes,
1 independent failure0.236s. Known83.372s plus historical unknowns. Exact hashes
and command in review. Current candidate preserved byte-for-byte in
review-candidate-2026-09-26T02-25-54Z.py.txt; historical evidence unchanged.

Next executable milestone: one atomic completion/eligibility/exclusive-claim
decision at execution admission; exact completion ownership; safe stale-caller
and actual-process counterpart tests, selectors/checkpoint completion. No external
I/O under DB lock; unknown effects held; interrupted execution settlement remains
unfinished recovery scope. Continue correction directly at baton.impl.

Separate operational provenance issue: no matching pre-splice copy found in
HEAD/index or two available older source copies; duplicate helper definitions
confirmed. Owner attention requested asynchronously for trustworthy source or
explicit reconstruction/revalidation baseline. This prevents accepting the
reconstructed module as an unchanged continuation, not continued selected fixes.
Author enumerates reconstructed functions/known changes and reconciles copies;
reviewer does not repair product. Historical accepted slices retain their original
evidence, but reconstructed current bytes require renewed verification.

Ownership: author source/test/PROGRESS/selectors and reconstruction inventory;
reviewer new probe/candidate evidence/review/current FINDING/PLAN. No Git mutation,
live/engine/deployed execution or residue cleanup. Remaining R3/R4/R5/adoption open.

---

# Superseded checkpoint — durable restoration admission still required

2026-09-26T02:11:12Z reviewer270735. Owner270482 unchanged. Complete handoff270733
and events270735 snapshot270740 read; thread remains266328, no obligations.
Latest review: review-2026-09-26T02-11-12Z.md.

Confirmed P1s: stale caller paused before registry acquisition resumes after B
completes/successor writes, then overwrites; separate OS process also bypasses
registry with same incarnation. Both return prior success via completion replay.
New immutable review_restore_registry_edges_20260926.py measures real disposable
successor-byte loss. Combined18 tests:16 author pass,2 failures0.488s. Full hashes
in review (source3efca9df, test9ab0e2f0). Known72.221s plus historical unknowns.

Next executable milestone: enforce store-bound external execution ownership and
make completed/replay/eligibility decisions atomic with admission. Reject or
safely replay stale contenders before any profile effect, including across OS
processes. Completion/release bound to exact execution; uncertain effects held
until positively settled. Preserve safe retry, no-I/O-under-lock and unrelated
DB progress; add safe counterpart cases for both schedules. Record minimal exact
helper/path extensions; existing owner selection suffices, no broad lease system.

Disposition: directly baton.impl for the same selected correction. Reviewer owns
new probe/review and current FINDING/PLAN; author source/test/PROGRESS/selectors
unchanged. Historical evidence, residues and Tuner preparation preserved. Accepted
grant_writer and micro-stages remain accepted. Wider R3/R4/R5/adoption open;
no live/engine/deployed/broad action or new owner gate.

---

# Superseded checkpoint — same-manager restoration overlap

2026-09-26T02:01:41Z reviewer270671. Owner270482 unchanged. Complete handoff270668
and events270671 snapshot270673 read; thread remains266328, no obligations.
Latest review: review-2026-09-26T02-01-41Z.md.

Confirmed: different incarnations are held, but two handles sharing one incarnation
both enter restoration. Same successor-byte loss and success replay as previous P1.
ControlStore.open permits this; manager identity is not exclusive call ownership.
New immutable review_restore_same_incarnation_20260926.py reproduces it. Combined
15 tests:14 author pass,1 independent failure0.204s. Source4dfe05da/test24b6eaca;
full hashes and command in review. Known enumerated60.317s plus prior unknowns.

Next: enforce exact ownership of the external restoration, including calls within
one manager, before profile entry. Bind completion/release to that execution;
keep uncertain prior execution held. Add same-manager contention/successor-byte
cases; preserve cross-incarnation holding, retry/replay and unrelated DB progress.
Record minimal necessary helper/path extensions before editing; existing owner
selection suffices. No global lease redesign or DB lock over filesystem I/O.

Disposition: directly baton.impl for the same P1 correction. Author retains source,
author test/PROGRESS/selectors; reviewer owns new probe/review and current records.
Historical evidence, residues and Tuner preparation unchanged. Prior grant_writer
and stages1/2/3 remain accepted; wider R3/R4/R5/adoption and unresolved recovery
requirements remain open. No live/deployed/broad action or new owner gate.

---

# Superseded checkpoint — exclusive restoration correction required

2026-09-26T01:49:21Z, baton.rvpc claim270580. Owner270482 remains the selection.
Complete handoff270572/events270580 snapshot270581 and thread266328 read; no new
obligations. Latest review: review-2026-09-26T01-49-21Z.md.

Confirmed P1: shared intent/revocation admits multiple external restorers. B
finishes and releases to a successor while A is still in its profile; A then
clobbers successor bytes and returns B's completion by journal replay. Independent
review_restore_overlap_20260926.py reproduces this with two real handles and a
controlled profile writing real disposable bytes.11 author cases pass; combined
12 cases/1failure0.189s. This slice is not accepted.

Next executable milestone: make ownership of the external restoration exclusive,
separate from recovery identity/replay. Prevent competing profile entry, condition
completion/release on the exact executor episode, and hold unresolved execution
until prior ownership is positively settled. Preserve no-I/O-under-lock, unrelated
DB progress, safe retry/replay and successor-byte protection. Strengthen focused
contention/reopen tests. Owner270482 already requires this; no new owner gate for
meeting that requirement. Record exact necessary helper/path extensions before
editing; no global second lease system or restoration under a DB lock.

Ownership: author review_cycles.py, author restore test, PROGRESS/selectors and
selected pinning; reviewer current FINDING/PLAN and new immutable probe/review.
Keep historical probes unchanged; they describe candidate-specific unsafe states.
Exact source/test/probe hashes in review. Known enumerated sequence48.877s plus
prior unknowns. One bounded deterministic command; no broad/live/deployed actions.

Disposition: directly baton.impl for routine correction under270482. Accepted
grant_writer and stages1/2/3 preserved. Other I/O sites, unknown holds, remaining
R3/R4/R5, residues, preserved-run recovery and adoption remain outstanding.

---

# Accepted prior slice — bounded grant_writer correction

2026-09-26T01:32:28Z, baton.rvpc claim270458. Latest review:
review-2026-09-26T01-32-28Z.md. Owner270290 selection unchanged. Complete
handoff270455/events270458 read; thread remains266328 with no new discussion or
pending obligation. Next: accepted delivery to baton.decide for owner disposition.

Accepted slice: grant_writer filesystem proof outside its transaction, exclusive
generation/checkpoint/object-bound admission inside it, deterministic post-proof
contention and distinct late-entry refusal. Replay wording corrected. Independent
14 cases OK0.072s includes12 author cases and2 applicable reviewer probes. No
remaining correction within this selected slice; W257624 itself remains open.

Source SHA2560f994874aef4dea2d5f2bc665d1ec1b305ec3b4c94dc3bba6d15d9476a72101b;
author test640c5079b6cf17242521b10c7264e5415e795db7a0f1513a4786b201e0c6cc06.
Exact bounded command and hashes in latest review. Known enumerated correction
subtotal26.596s plus unreported single-case/probe durations; historical totals
preserved. No broader test run or new execution selection.

Outstanding beyond this slice: create_line and other I/O-under-lock sites,
never-created-helper release, assignment_workspace/callers, alias/object matrix,
dogfood_operator.py:4489, pending intake._settle operand, remaining R3 coverage,
R4 composed recovery, final R5 packet and W247941 adoption. Unknown holds and both
residue inventories preserved; stages1/2/3 retain their bounded acceptance.

Ownership unchanged: author source/test/PROGRESS/selectors; reviewer current
checkpoint/FINDING and append-only reviews/probes; Tuner preparation untouched.
No live provider/engine, deployed-store access/recovery/cleanup or Git mutation.

---

# Superseded checkpoint — grant_writer focused correction requested

2026-09-26T01:23:34Z, reviewer baton.rvpc claim270384. Owner270290 remains the
selection. Complete handoff270381/events270384 snapshot270387 and thread266328
read; no pending obligation. Latest review: review-2026-09-26T01-23-34Z.md.

Accepted progress: filesystem proof moved outside grant transaction; ownership,
assignment/checkpoint and recorded-object binding retained inside. Eleven author
cases pass. Independent forced post-proof overlap admits one writer; cached-root
access change is refused. No new product defect established.

Next executable milestone: correct test_grant_writer_admission.py contention
schedule to synchronize both completed proofs before either transaction, with
bounded thread waits and failure propagation. Its current entry barrier permits
an early-refusal schedule that fails its message assertion. Preserve exact
post-proof assertions. Correct replay comment and matching planning claim:
initial object proof still runs before journal replay; only the relocated access
proof is skipped. No broader product redesign or planning loop.

Ownership: author retains review_cycles.py, author test, PROGRESS/selectors and
selected record pinning authority; reviewer owns this checkpoint, FINDING append,
new review and review_grant_writer_schedule_20260926.py. Historical evidence and
Tuner preparation remain untouched. Source89141512 and test5d660897 hashes plus
probe hash are recorded in review. New review spending0.096s, this correction
known subtotal9.439s; all historical costs retained.

Disposition: directly baton.impl for routine correction under270290; accepted
delivery later returns owner. Stages1/2/3 accepted; wider I/O-under-lock sites,
unknown holds, unfinished R3/R4/R5, preserved-run recovery and adoption remain
outside this correction. No live/engine/deployed/broad execution selected.

---

# Superseded checkpoint — micro-stages accepted; grant_writer correction selected

2026-09-26T01:04:01Z, baton.prompt: owner reaffirmed the existing no-external-I/O
under DB locks rule and confirmed the current grant_writer violation. See the
dated FINDING entry. Database/library internal I/O is the exception; application
filesystem reads and validation inside transaction callbacks are not exceptions.

W266329/W266336/W266337 are closed satisfying. This supersedes the pending
micro-stage sequencing below, not its safety constraints or wider R3/R4/R5 gaps.
Proposed next executable milestone: minimally correct grant_writer in
worker_manager/review_cycles.py and necessary helpers; focused disposable-store
tests must prove external I/O occurs outside transactions and preserve ordinary,
competing and stale-generation admission plus resource/checkpoint refusal.
Record exact ownership before implementation; one bounded deterministic command,
independent review, routine corrections directly to implementation and accepted
delivery to owner. No broad design loop, live/deployed recovery or R4/R5 expansion.

Canonical read snapshot270257: W257624 unclaimed at baton.decide, latest handoff
266352 and thread through266328. Proposed reroute command was supplied to owner;
its execution is not asserted. Prompt edits only this checkpoint and FINDING;
author test/PROGRESS, reviewer journals and Tuner preparation remain untouched.

## Superseded sequencing — finish correction, then executable micro-stages

2026-09-25T13:52:41Z reviewer266335: revision4 preserved, [review checkpoint](review-2026-09-25T13-52-41Z.md)
recorded after owner message266328. Return baton.decide now, no further broad
plan handback. Preserve two proof caveats: runtime.start journal replay is not
public request_runtime_start replay, and reconciliation alone is not proof an old
submitter cannot act. Next is the separately owned stage1 executable proof below,
not the proposed unwired expiry slice. No tests/product edits, spending0;
events266335/thread266328 read, no obligations. Reviewer journal/FINDING/PLAN only;
author/Tuner ownership, residues and incomplete R3/R4/R5 remain unchanged.

Ledger sequence: W266329 reserve-before-launch, W266336 safe release, W266337 fresh-attempt recovery. All created at baton.decide; owner must install dependency edges before routing. W266337 creation typo W266330 is superseded by M266343. Stop-after-correction instruction delivered to impl and bug in M266328. No overlapping execution is selected.

2026-09-25: owner selects the three-step split in FINDING's latest entry. Claude finishes/preserves the current correction and passes W257624 to baton.decide with an exact handoff; stop the comprehensive plan-revision loop. Separate serial Work: reserve-before-launch proof, delayed-submitter safe-release proof, then failed-Job/fresh-attempt recovery proof. Do not start overlapping product edits before current custody is released. Each deliverable has one bounded executable command and independent evidence. Older current-action checkpoints below are superseded as sequencing instructions; safety requirements and incomplete R3/R4/R5 acceptance remain in force.

# Current design constraint — owner workspace-lease ruling, 2026-09-25

See FINDING: short DB transactions, no external I/O under DB locks, expiry enters revocation, and confirmed termination of all writers before same-workspace reassignment. This supersedes contrary earlier serialization guidance; accepted historical proofs remain evidence, not compliance with the new rule. W257624 is at owner disposition. Next bounded selection should map one review adoption-to-first-write path to existing lifecycle capabilities and name minimal changes/tests; no broad implementation or live recovery selected by this ruling.

## Superseded: continue plan-only lease correction at implementation

2026-09-25T13:39:40Z, baton.rvpc claim266219: [latest review](review-2026-09-25T13-39-40Z.md)
finds revision3 not implementation-ready. Freeze prior-pointer/replay and policy
distinctions improved. Remaining bounded corrections: use actual pre-start
operation identity/existing runtime.start transaction (runtime_id is minted later);
account for delayed submitter separately from runtime termination; distinguish
terminal-answer finalization from unanswered cancellation; bind revocation through
actual pin/reached/cancel records and exact replay signature. Next: §§1b/3/4/7 and
focused matrix correction in author preparation, no implementation/tests. Direct
baton.impl iteration under266005; owner return once ready or concrete decision.
Events266219/thread264904 unchanged, no obligations; spending0, prior costs retained.
Reviewer journal/FINDING/PLAN ownership; author/Tuner files untouched. Existing
residue/no-live/no-inspection/no-cleanup restrictions and unfinished stages preserved.

## Superseded revision2 correction checkpoint

2026-09-25T13:24:26Z, baton.rvpc claim266108. Owner266005 explicitly permits
same-scope preparation corrections to iterate without renewed owner permission,
superseding the prior owner-return checkpoint below. [Latest review](review-2026-09-25T13-24-26Z.md)
finds revision2 not implementation-ready: proposed freeze pointer/phase predicate
still breaks normal completion/replay; mount-to-start and termination traces remain
incomplete; expiry evidence/policy/state predicates and reciprocal removal race/
crash matrix need exact definitions. Next executable milestone is correcting
LEASE-DESIGN-PREPARATION.md only and returning for review. No implementation or
tests selected. Return baton.impl; owner return once implementation-ready or for
a concrete new decision. Reviewer owns journal/FINDING/PLAN; author preparation/
PROGRESS/selectors and Tuner R5 ownership preserved. Events266108/thread264904,
no obligations; spending0, prior costs retained. No live/inspection/cleanup;
residues preserved, R3 incomplete, R4/finalR5 and existing gaps unchanged.

## Superseded owner checkpoint — lease preparation needs correction

2026-09-25T10:58:36Z, baton.rvpc claim265204. Owner265058 selected plan only.
[Latest review](review-2026-09-25T10-58-36Z.md) rejects preparation as implementation-ready:
durable revocation/progress guard already exist; proposed active-at-freeze-commit
predicate contradicts normal freeze; attempt custody holds do not cover line
writers; removal intent lacks reciprocal exclusion; relevant grant/restore
filesystem-under-lock sites omitted. Proposed next step is corrected bounded
preparation with exact physical-resource/writer mapping and crash/replay predicates,
not implementation1/3/5. Return baton.decide per selection. No tests or product
edits; spending0, historical costs preserved. Events265204/thread264904, no
obligations. Reviewer owns journal/checkpoint; author/Tuner files unchanged.
Residue/no-live/no-inspection/no-cleanup restrictions remain; R3 incomplete,
R4/finalR5 unselected and intake operand ownership/release gaps still pending.

## Superseded overlap-correction checkpoint

2026-09-25T09:20:16Z, baton.rvpc claim264559: owner264494 selects correction of
the SAME abandonment milestone then return baton.decide. [Latest review](review-2026-09-25T09-20-16Z.md)
verifies the prior P1 overlap fault corrected; 25 focused tests OK4.561s,
tool4.667750751s, including unchanged regression and new immutable
review_r3_overlap_orderings.py proving both stale-read orders and reopen refusal.
R3 remains incomplete. Proposed next milestone: review-mount adoption/first-write
path, not yet selected. intake.py:_settle operand ownership still pending.
Author broader1296/1221 batches conflict with no-broad-sweep direction; selector
record does not enumerate claimed expansion. Record exact focused selectors
before further execution. No live/inspection/cleanup/deployed recovery; residue
inventories preserved, unknown engine state. Reviewer owns journal/regressions/
FINDING/PLAN; author/Tuner ownership unchanged. Events264559/thread262065,
no obligations. R4/finalR5 unselected, no adoption acceptance; prior costs retained.

## Superseded failed-milestone checkpoint

2026-09-25T04:25:17Z, baton.rvpc claim262771: owner262703 SUPERSEDES the broad
R3 continuation with one adoption-to-use milestone and requires return to
baton.decide after independent review, before another milestone. Recorded here
from author262767's PROGRESS/handoff; reviewer retains FINDING/PLAN ownership.
[Latest review](review-2026-09-25T04-25-17Z.md) independently passes the author's
two explicit cases but fails new review_r3_adoption_overlap.py: workspace hold
after lookup permits a nested result helper submission/settlement before refusal.
The selected milestone is NOT accepted. Proposed next executable step: correct
overlap admission on this same abandonment path and prove exact competing
outcomes before selecting the proposed review-mount path. No broad continuation.
intake.py:_settle exact operand extension still pending; other ownership unchanged.
No live/engine inspection/cleanup/deployed operations; both residue inventories
preserved, unknown engine state. Audited deterministic selectors only. One run:
3 cases/1failure0.199s, tool0.365481702s; prior costs preserved. Events262771,
thread262065 unchanged/no obligations. R3 incomplete, R4/final R5 unselected.

## Superseded incident-disposition checkpoint

2026-09-25T04:06:46Z, baton.rvpc claim262667: [latest review](review-2026-09-25T04-06-46Z.md)
passes15 focused cases with tightened races. R3 remains incomplete: adoption's
use-after-answer window, allocation, path/copy/alias coverage and introduced
inventory failures remain. Author reports SECOND out-of-scope live batch/rerun,
eleven roots in LIVE-RUN-RESIDUE-262516.json, engine state unknown; preserve both
residue inventories. Return baton.decide for execution-boundary disposition and
exact intake.py:_settle control-operand extension. Recommend audited deterministic
selectors and separately selected daemon-access denial if available; no live
inspection/cleanup/rerun authorized. Routine product/fixture corrections remain
within selected R3; proposed adoption lifetime is not yet a chosen mechanism.
Ownership otherwise unchanged. Events262667/thread262065, no obligations.
Independent tests3.932s/tool4.06748528s; historical costs preserved. R4 unselected,
final R5 pendingR4, Work/adoption not complete.

## Superseded caller-continuation checkpoint

2026-09-25T03:40:38Z, baton.rvpc claim262503: [latest review](review-2026-09-25T03-40-38Z.md)
independently passes15 focused cases with both new race schedules. Tighten
claimant outcomes, contender readiness and failure-path joins; then complete
allocation/adoption/line and path/alias coverage plus boundary attribution.
Owner262043 ALREADY grants store/guard propagation in both disputed tools files
and requires preserving allocation concurrency. Historical W33936 thread-affinity
comment is an invariant, not a new owner gate. Continue directly at baton.impl.
intake extension remains pending/no further edits there. Other ownership unchanged.
Events262503/thread262065 no obligations. New tests3.905s/tool3.967285392s;
prior costs preserved. R3 unaccepted, R4 unselected/finalR5 pendingR4; execution
and residue boundaries unchanged.

## Superseded race-milestone checkpoint

2026-09-25T03:28:01Z, baton.rvpc claim262418: [latest review](review-2026-09-25T03-28-01Z.md)
independently passes149 cases: all three reviewer regressions, guards and workspace
suite. Replay/fixture corrections verified; R3 not accepted. Next executable
milestone: both write-lock race orderings using two real independently owned
handles and bounded scheduling events, then remaining entries/callers, path/alias
coverage and boundary-inventory attribution. Direct implementation continuation;
no intermediate owner/review gate. intake extension pending, no further edits
there; all other ownership unchanged. Events262418/thread262065, no obligations.
New tests1.425s/tool1.566771428s, previous costs preserved. R4 unselected/final R5
pending R4; no-live/no-cleanup and residue boundaries unchanged.

## Superseded replay-correction checkpoint

2026-09-25T03:23:28Z, baton.rvpc claim262389: [latest review](review-2026-09-25T03-23-28Z.md)
passes12 focused cases including snapshot regression, but new immutable
review_r3_removal_replay.py reproduces KeyError on repeated execution-root
removal. Next: preserve result/retry/reopen semantics, correct foreign-owner
fixture scope without weakening assertions, prove race orderings, then finish
remaining entries/callers/alias/path coverage and boundary attribution.
Continue directly under current authority; no routine owner or test gate.
intake extension pending; other ownership unchanged. Events262389/thread262065;
no obligations. Independent13 cases/1error0.789s, tool1.029268552s. R3 unaccepted,
R4 unselected/finalR5 pendingR4, live residue and execution boundaries preserved.

## Superseded snapshot-correction checkpoint

2026-09-25T03:13:33Z, baton.rvpc claim262318: [latest review](review-2026-09-25T03-13-33Z.md)
reproduces stale read-only snapshot permitting deletion after a second handle
commits a hold. review_r3_snapshot_lock.py is immutable reviewer evidence.
11 other focused cases pass; R3 not accepted. Next: distinguish authorized write
transactions from snapshots/read-only contexts, preserve removal result values,
prove replay and both race orderings; fix five known workspace fixture reds
under standing test authority, then remaining entry/caller/alias coverage and
boundary-inventory attribution. Direct implementation continuation, no routine
owner gate. intake extension remains pending; no further unowned edits.
Ownership otherwise unchanged. Events262318/thread262065; no obligations.
Independent12 cases/1failure0.687s, tool0.765083198s; historical costs preserved.
R4 unselected/final R5 pending R4; residue/no-live/no-cleanup boundaries unchanged.

## Superseded initial serialization checkpoint

2026-09-25T03:01:27Z, baton.rvpc claim262239: [latest review](review-2026-09-25T03-01-27Z.md)
independently passes213 focused cases including original wrong-store regression
and repaired review-cycle fixtures. Precise unconfigured-store bypass resolved;
R3 still unaccepted. Next: serialize both deletion entries against R1 holds and
prove two-handle races/reopen, then remaining entries/callers, alias/provenance,
discard_tree/copy tracing and focused boundary-inventory attribution. No new
routine owner/review gate; continue directly in implementation. intake.py operand
edit lacks prior recorded extension: preserve it, record and coordinate that
exact extension before further edits there; owned serialization work continues.
Claude/reviewer/Tuner ownership otherwise unchanged. Events262239, thread262065;
no obligations. Independent tests4.415s, tool4.564746481s. R1/R2 history preserved,
R4 unselected, final R5 awaits R4. No-live/no-cleanup/residue boundaries unchanged.

## Superseded first-guard correction checkpoint

2026-09-25T02:49:44Z, baton.rvpc claim262157: supersedes documentation-only
checkpoint below. Author262151 adds discard_workspace guard and eight passing
focused cases. [Latest review](review-2026-09-25T02-49-44Z.md) independently
passes eight, reproduces unrelated-store bypass in review_r3_store_binding.py.
Next: bind store/resource authority, serialize hold versus deletion, complete
remaining entries/callers and trace additional discard paths/copy destinations.
Then fix token-aware review-cycle fixtures and attribute boundary inventory
failures with focused selectors. All current implementation authority remains;
return directly to baton.impl. No R3 acceptance. Reviewer owns new regression
and review/checkpoints; Claude retains product/author-tests/PROGRESS. Tuner R5
draft separately accepted, final validation requires accepted R4; R4 unselected.
Events262157; thread262065 unchanged; no obligations. New tests0.574s;
all prior costs preserved. No-live/no-cleanup and residue boundaries unchanged.

## Superseded documentation-only continuation

2026-09-25T02:39:02Z, baton.rvpc claim262077: owner262043 grants all four
caller files requested below for store/guard operand propagation and directs
implementation. This supersedes the ownership gate. Author262073 delivered
documentation only; no R3 guard/test yet. [Latest review](review-2026-09-25T02-39-02Z.md)
corrects result-root layout (nested inside workspace), requires overlapping
hold protection and a tested alias boundary, and returns directly to baton.impl.
Next: record serialization/failure window, implement focused guarded entry,
complete four-entry/caller matrix and necessary test migration. Existing grant
and standing test authority suffice; no intermediate owner/review gate.
Claude retains product/author-test/PROGRESS/enumeration ownership. Reviewer owns
reviews/FINDING/PLAN. Tuner W262061 owns ONLY R5-PREPARATION.md; preserve parallel
draft preparation. R4 unselected; final R5 needs accepted R4. Live residue and
no-engine/no-cleanup boundaries unchanged. Events262077; T257624 through262065;
no obligations; zero new test spending. R1/R2 accepted, R3 not accepted.

## Superseded caller-ownership checkpoint

2026-09-24T23:35:12Z, baton.rvpc claim260956: owner260900 accepted R2 and
selected R3 only, superseding the checkpoint below. Author260953 delivered
R3-ENUMERATION.md but no guard. [Latest review](review-2026-09-24T23-35-12Z.md)
recommends explicit store-backed guards and requests Claude ownership limited
to operand propagation in single_worker.py, integration_worker.py,
dogfood_operator.py and review_cycles.py, in addition to selected workspaces.py
and existing custody.py ownership. All four entries lack store operands;
assignment-only keys do not prove cross-attempt physical-line alias protection.
Next after ownership coordination: correct enumeration, establish resource
mapping and hold/reuse serialization, trace copying destinations, implement
and prove focused test_resource_guards. No R3 acceptance; R4/R5 unselected.
Reviewer owns reviews/FINDING/PLAN; author owns PROGRESS/enumeration/tests.
Events through260956, T257624 through257624, no obligations. No tests run in
this research review. Live residue and no-engine/no-cleanup boundary preserved.

## Superseded R2 acceptance checkpoint

2026-09-24T23:18:46Z, baton.rvpc claim260836: supersedes the R2 correction
checkpoint below. [Latest review](review-2026-09-24T23-18-46Z.md) accepts R2
on independently verified current hashes: 43 focused and121 custody cases pass.
R1/R2 accepted; R3–R5 unselected and W257624/adoption dependency remain open.
Next: owner selects the next bounded stage and dispositions the unselected-live-run
residue recorded in LIVE-RUN-RESIDUE-260767.json (nine roots,108 derived possible
helpers, daemon state unknown). No cleanup or live execution authorized here.
test_two_jobs is pinned-snapshot evidence only; standalone stage fixtures remain
red with author-reported matching baseline failures. Claude retains product,
author-test and PROGRESS ownership; reviewer owns reviews/research/checkpoints.
Events read through260836, T257624 through257624; no obligations. Pass to
baton.decide; no Work closure or adoption acceptance.

## Superseded R2 correction checkpoint

2026-09-24T23:02:34Z, baton.rvpc claim260740: supersedes migration checkpoint
below. [Latest review](review-2026-09-24T23-02-34Z.md): 39 focused cases pass
independently, new review_r2_token_readback.py fails because direct receipt
readback does not compare submission token with the hold. Next: correct that,
prove token-aware reopen/legacy refusal and real fixture-root no-effects/echo,
and attribute the 12 standalone stage fixture failures with a bounded comparison.
Record pinned-snapshot test_two_jobs provenance correction. Author also disclosed
an unselected live-engine run with six failures/errors; preserve exact command,
resource identities and cleanup/residual evidence, no live rerun or unselected
cleanup. Claude retains product/author-test ownership; reviewer owns reviews,
research and four immutable reviewer modules. R2 unaccepted; R3–R5 unselected.
Events through260740; T257624 unchanged through257624; no obligations.

## Superseded migration checkpoint

2026-09-24T22:33:14Z, baton.rvpc claim260564: current continuation checkpoint
supersedes the fixture-position checkpoint below. Author reports 28 clearance
and 11 admission cases green; accepted test_custody.py migration remains ~51
red. [Review clarification](review-2026-09-24T22-33-14Z.md) resolves the argv
question: require exactly -c PROGRAM verb committed-submission-token, retaining
all containment/command restrictions. Existing R2 scope and standing test
authority suffice; no new product or test gate. Next: migrate literal response
fixtures/program arguments, diagnose remaining code mismatches, pin changed
composition ordering, finish focused acceptance, then relevant deterministic
regression verification. Claude retains product/author-test ownership; reviewer
modules remain immutable. No independent tests this partial checkpoint. Events
through260564; T257624 unchanged through257624; no obligations. R2 unaccepted;
R3–R5 unselected.

## Superseded fixture checkpoint

2026-09-24T22:22:09Z, baton.rvpc claim260491: current continuation checkpoint
supersedes the pending implementation checkpoint below. Author260488 returned
token implementation explicitly unfinished, with no green run against current
bytes. [Review/checkpoint](review-2026-09-24T22-22-09Z.md) confirms the known
fixture bug: parent test_abandonment.py Removing.custodian reads argv[-1] as
verb, but argv now ends operation,submission. Next: fix that author-owned
fixture; pass the focused token acceptance matrix from ATTRIBUTION-PLAN; then
adapt deterministic closed-result fixtures and run one relevant regression set.
Historical reviewer modules stay immutable; author equivalents may adapt old
positive setups while preserving assertions. Claude retains custody.py and
author-test ownership; reviewer owns reviews/research/checkpoints. No independent
tests this partial-review turn; no acceptance. Events through260491; T257624
unchanged through257624; no pending obligations. Existing authority suffices;
no owner gate, live execution or R3–R5 selection.

## Superseded implementation checkpoint

2026-09-24T22:13:36Z, baton.rvpc claim260433: supersedes the pending direct/
reader corrections below. [Review](review-2026-09-24T22-13-36Z.md) verifies
those corrections and 43 focused tests pass. Remaining milestone is submission
attribution. [ATTRIBUTION-PLAN.md](ATTRIBUTION-PLAN.md) recommends author option
(a): committed submission token echoed by the manager-supplied embedded program,
with stable helper naming retained. The program is passed by python3 -c from
custody.py; no image rebuild is needed. Continue under owner260109 R2 authority;
no new owner choice or test approval required. Author revalidates the bounded
plan, coordinates any actual oci.py extension, records the contract and executes
the focused milestone. Claude keeps product/author-test ownership; reviewer
keeps reviews, attribution research and three historical review modules.
Events through260433; T257624 unchanged through257624; no pending obligations.
R2 remains incomplete; R3–R5 unselected.

## Superseded correction checkpoint

2026-09-24T22:06:47Z, baton.rvpc claim260381: supersedes the preceding
pending-evidence checkpoint below. Partial corrections verified: 163 focused
tests pass, including existing product-test changes with assertions preserved.
[Latest review](review-2026-09-24T22-06-47Z.md) records the remaining milestone:
implement submission-specific evidence binding (author explicitly left it open),
complete semantic validation of hold/direct receipt records, and make direct
clearance require the complete successful settlement condition. New immutable
review_r2_direct_clearance.py proves status1 plus an accountable document still
clears; one test fails. Next is bounded implementation, not another owner gate
or broad-suite cycle. Coordinate any needed oci.py change; retain hold on
unattributable evidence. Claude retains product/author-test ownership; reviewer
owns three review modules and append-only reviews. R3–R5 unselected. Events
through260381; T257624 unchanged through257624; no pending obligations.

## Superseded checkpoint

2026-09-24T21:55:12Z, baton.rvpc claim260302: handoff260299 independently
reviewed. 39 existing focused tests pass, including the unchanged first reviewer
module. Three new counterexamples in reviewer-owned review_r2_evidence_binding.py
fail; see [review-2026-09-24T21-55-12Z.md](review-2026-09-24T21-55-12Z.md).
Next: bind clearance to evidence for the actual submission (unused older direct
output must refuse), validate retained settlement and hold semantics on read,
and preserve a hold on unaccountable output despite status0. These remain R2
requirements under owner260109; the author's provenance deferral and status-only
rule are not accepted contract changes. Update bounded affected tests using
standing authority, retain defect coverage, and coordinate any needed oci.py
change. Claude retains product/author-test ownership; reviewer owns the two
review modules and append-only reviews. No R3–R5 selection. Events read
through260302; T257624 unchanged through257624; no pending obligations.

## Superseded delivery checkpoint

2026-09-24, baton.claude claim 260228: the three P1 counterexamples in
review-2026-09-24T21-39-09Z are fixed and the reviewer's module passes
unchanged. `custody_act` clears only on a **status-0** engine answer; a
settlement is **spent** once it has reconciled an episode; and `custody_holds`
validates each clearance's own binding and provenance. Gap coverage now uses a
genuine absence and a gap **refuses** instead of shortening the scan; the
overflow bound is reached for the first time, which exposed that all three
bound refusals in this module carried an invalid `refused`/`limit` pairing and
could never have been raised. The corrected contract is recorded in
[FINDING.md](FINDING.md) as the review required, ahead of the source edits.
Evidence and the provenance limitation this stage does **not** close are in
[PROGRESS.md](PROGRESS.md). R3–R5 remain unselected.

# Superseded action: correct R2 settlement and reader validation

2026-09-24T21:39:09Z, baton.rvpc claim260196: owner260109 accepted R1 and
selected R2 only, superseding the R1-only/unselected-R2 checkpoint below.
Author260194 delivered R2; independent review requests corrections in
[review-2026-09-24T21-39-09Z.md](review-2026-09-24T21-39-09Z.md).
22 supplied cases pass; three reviewer counterexamples fail: nonzero client
answers clear automatically, old settlement clears a new episode, and a signed
wrong-binding clearance is accepted by the reader. Next: implement those R2
corrections, complete real gap/overflow coverage, rerun focused R2 and R1 tests,
and hand back for independent review. No R3–R5 expansion or live execution.
Claude owns custody.py, test_hold_clearance.py and the documented R2 update to
the existing parent test_abandonment.py; coordinate any bounded oci.py change
before editing. Reviewer owns append-only reviews and review_r2_counterexamples.py;
use that module as immutable regression evidence or add author-owned equivalents.
Standing test-change authority covers the parent test update; no new approval
gate. FINDING/PLAN remain reviewer coordination paths at this handoff; append
the implementation contract clarification there before changing source.
Events read through260196; T257624 through257624, unchanged; no pending obligations.

2026-09-24T21:19:32Z, baton.rvpc, claim260080: owner260075 repaired reviewer
scratch access and selected the exact focused rerun. Candidate hashes match
before/after; all 11 tests passed independently in 0.528s (tool wall0.66562133s).
[review-2026-09-24T21-19-32Z.md](review-2026-09-24T21-19-32Z.md) accepts R1
only and supersedes the pending-runner checkpoint below. Return to baton.decide;
R2 remains unselected and R2–R5 unfinished. No current R1 blocker. Product/test
ownership remains Claude's; reviewer owns review/FINDING/PLAN only. Last events
read through260080; T257624 through257624; no pending obligations. Next executable
milestone requires owner selection of the next bounded stage, as the current
handoff expressly directs. No live execution or deployed recovery is selected.

2026-09-24T21:08:41Z, baton.rvpc, claim260000: this checkpoint supersedes
the pending-evidence checkpoint below. Owner258324 selected the scratch root
and author258371 supplied the missing cases. Hashes match; inspection supports
the corrections. Independent repetition failed in all 11 setups because the
reviewer cannot write `/var/tmp/baton-w257624`. See
[review-2026-09-24T21-08-41Z.md](review-2026-09-24T21-08-41Z.md).
Next: operationally enable the selected root for the managed reviewer, then
rerun the exact focused command in that review and return R1 result to owner.
No product/test edits requested; Claude ownership remains. Reviewer owns only
review/FINDING/PLAN. R2 is not selected. Events read through260000; thread
T257624 through257624. No pending obligations in canonical detail.

2026-09-24T15:03:35Z, baton.rvpc: R1 delivered and independently inspected;
acceptance pending the bounded evidence and runner prerequisite in
[review-2026-09-24T15-03-35Z.md](review-2026-09-24T15-03-35Z.md).
Return to owner under selection257693. No R2 execution or automatic correction
cycle is selected by this review. This updates the planning-only status below;
existing product/test ownership remains with Claude.

W257624 is placed at baton.decide. Proposed implementation: baton.claude;
independent review: baton.rvpc. Review each stage before beginning its successor.
Each handoff says stage/result/evidence/next stage. A red regression remains red
evidence; do not make a new invariant optional to make the stage pass.

Shared inputs: stopped review/checkpoint linked from FINDING; parent
OWNERSHIP-255823.md, PATHS-256145.md, test_abandonment.py and
test_routed_abandonment.py. Five product paths remain Claude-owned: tools/
single_worker.py and stage_execution.py under v12/python; intake.py, oci.py,
custody.py under v12/python/src/baton_v12/worker_manager. No ownership transfers
by this plan. Historical tests stay in their original dossier; add the following
small test modules here after assignment. Names below are planned deliverables,
not files asserted to exist today.

## Commands and repetition contract

Use an authorized isolated test runner, the current source candidate and a fresh
per-test temporary root; never the preserved deployment. Every module below must
exercise real manager/store code with fake engine/provider at the normal port,
close its handles and account for its own scratch resources. Coordinate any
fixture Git creation with the existing repository policy; no Git mutation in
the shared checkout. Set BATON_V12_DISK_ROOT to an operator-provisioned writable
disk-backed scratch parent outside the checkout and snapshots when the fixture
needs one. The old recorded /var/tmp/baton-w247941 is not a permission grant.
Missing suitable storage is an actionable runner prerequisite, not a test pass.

```sh
cd /home/sl/src/baton
export PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-real-jobs-adoption-gate:$PWD/work/records/2026/09/finding-v12-failed-run-resource-hold"
export PYTHONDONTWRITEBYTECODE=1
PY=/home/sl/.local/state/baton-v12-venv/bin/python
```

Current baseline command (two existing selectors; reviewed previously, not rerun
by tuner) is executable before writing R1 tests:

```sh
timeout --signal=TERM --kill-after=5s 30s "$PY" -B -W error::ResourceWarning -m unittest test_abandonment.TheComposedAbandonmentIsCalled.test_an_unresolved_submission_holds_the_root test_abandonment.TheComposedAbandonmentIsCalled.test_a_reconciliation_lifts_one_episode_and_the_act_proceeds
```

These two passes are sequential baseline evidence only. They do not cover the
five open findings. The per-command limits below are proposed test backstops,
not product guarantees or cumulative spending gates. Capture exit status,
elapsed time, exact source hashes and counter/receipt output. A timeout kills
only this isolated fake-boundary test process; it proves no daemon settlement.

## R1 — one exclusive submission before any destructive helper act

Outcome: one caller owns a pre-effect uncertainty episode; all concurrent or
restarted callers refuse before submission **or reclamation** while it stands.
Inputs: stopped custody.py and the two baseline cases. Proposed edit boundary:
custody.py and new test_hold_admission.py only, using existing transactions;
any additional shared primitive needs an enumerated ownership amendment first.

Deliver a barrier-driven two-connection race (no sleep-based ordering), a late
visible helper behind a standing hold, and crash points before/after submission.
Expected evidence: exactly one engine submit vector; zero stop/remove vectors
on the held path; unchanged root bytes; durable held episode readable on reopen.
Replay of the record must not authorize a second caller to submit.

```sh
timeout --signal=TERM --kill-after=5s 30s "$PY" -B -W error::ResourceWarning -m unittest test_hold_admission
```

Command becomes runnable when R1 supplies that focused module. Failure stays
held/unresolved, with exact helper/root/episode identity. Stop after independent
R1 acceptance; do not add clearance, resource guards or supervisor edits here.

## R2 — only exact settlement evidence clears one hold

Depends on accepted R1. Outcome: clearance changes one exact episode's eligibility
and nothing else. Paths: custody.py and new test_hold_clearance.py; oci.py only
if its engine-answer contract needs a coordinated bounded change.
Validate hold and clearance kind/state/signature and full attempt, canonical
resource/root, helper, image and episode binding. Require a precise provider
observation proving settlement of that submitted mutation. Plain observation
text, local CLI exit, an empty helper listing after client timeout, or any
nonzero/unaccountable answer is not enough to exclude a delayed daemon request.
If that evidence cannot be supplied, the selected result is still held.

```sh
timeout --signal=TERM --kill-after=5s 30s "$PY" -B -W error::ResourceWarning -m unittest test_hold_clearance
```

Evidence: positive exact-episode clearance and immutable replay; forged/wrong
signature, root, helper, image, episode and malformed/overflow/gap records all
refuse; second uncertainty remains separate; ambiguous answers never clear.
Fake engine only. Stop at accepted reader/clearance contract, before resource
reuse is claimed safe. Do not invent a generic engine-service prerequisite.

## R3 — every route to a held physical resource refuses

Depends on R1/R2. Outcome: restart, reuse and deletion cannot bypass the hold
through a different entry or alias. First enumerate every path that can touch
the exact held resources, then record one writer and the smallest path set.
Proposed additional boundary: worker_manager/workspaces.py
(assignment_workspace, adopted_assignment_workspace, line_assignment_workspace,
discard_workspace) with custody.py/oci.py callers and test_resource_guards.py.
These workspace paths are **not yet transferred or authorized for edits** by
the existing ownership record; coordinate the exact extension before editing.
Do not assume this provisional list is exhaustive or scatter fixes into all
callers without a recorded call graph.

```sh
timeout --signal=TERM --kill-after=5s 60s "$PY" -B -W error::ResourceWarning -m unittest test_resource_guards
```

Evidence: guard matrix for all enumerated entries, physical-root aliases,
reopen/restart and competing hold/reuse; no mutation behind a hold; unaffected
root still usable; validated clearance permits only the selected resource.
Real files/stores, fake engine. Missing path coverage blocks this stage. Stop
after independent protection acceptance, not after printing FROZEN.

## R4 — a bounded supervisor reports recovery or hold truthfully

Depends on R3. Outcome: one stranded attempt leaves a retained outcome before
the selected overall bound, with exact positive cleanup or explicit unresolved
resource holds. Paths: existing single_worker.py, stage_execution.py, intake.py,
oci.py and the parent two_job_supervisor.py, with new test_bounded_recovery.py;
edit only the boundaries shown necessary, keeping one Claude writer.
Carry one decreasing allowance across engine calls, actual store waits and
readback; measure lock contention and account for filesystem uncertainty.
An unproved I/O ceiling must remain a limitation, not a hard deadline claim.

```sh
timeout --signal=TERM --kill-after=5s 120s "$PY" -B -W error::ResourceWarning -m unittest test_bounded_recovery
```

Expected evidence through actual supervise: first-call crash, launch-absent
recovery, prior cancellation before/after declaration, lost discharge receipt,
restart/replay, interrupted/expired budget, contended store and uncertain engine.
No duplicate effect, unchanged old intent, no success without committed cleanup
and discharge; ordinary success remains covered. Use real stores/clock for lock
checks and controlled fake engine timing; label each. Stop at reviewed lifecycle
behavior. Existing broad-suite pass counts cannot substitute for these cases.

## R5 — independently validated grants and recovery command

Depends on R4. Outcome: a complete operator packet binds the two failed attempts
and produces verifiable readback without trusting typed IDs or granting itself
authority. New owned docs RECOVERY.md and GRANTS.md here plus
test_recovery_packet.py; retain original evidence at its canonical location.
Name exact authority/manager privileges and separate grant issuance from use.
Use only supported interfaces; reject wrong scope/generation/identity and
missing rights before destructive effects. No raw SQLite or docker-rm shortcut.

```sh
timeout --signal=TERM --kill-after=5s 60s "$PY" -B -W error::ResourceWarning -m unittest test_recovery_packet
```

Exercise the literal packet command on disposable stores/fake engine, checking
receipt replay, custody/retention and post-operation readback. Deliver exact
production recovery and reconciliation commands for separate owner selection;
**do not run them**. Positive cleanup and held/unresolved exits must be distinct.
Close this prerequisite only on independently accepted stage evidence and owner
disposition; actual preserved-run recovery remains a separately selected act.

## Owner-selected parallel preparation — 2026-09-25

See the dated FINDING ruling. Tuner may prepare R5-PREPARATION.md under a separate child Work now. This supersedes R5-unselected wording only for draft preparation. Claude continues current R3; R4 remains the prerequisite for final R5 validation. No shared product/test/PROGRESS ownership changes. Draft review does not accept R5 or authorize execution.

### Coordination clarification — W262061

The proposed child attachment was refused by the supported CLI because baton.prompt is not the handler of active W257624. No claim was changed. W262061 was therefore created as separate lightweight preparation Work at baton.tune (thread T262061), superseding the child-Work wording above. It owns only R5-PREPARATION.md, not this dossier binding. Final R5 remains in W257624 after accepted R4; the preparation has no blocking dependency on unfinished implementation. This is expected route authority enforcement, not a product defect or bypass.

## Implementation checkpoint — superseded by current review disposition

Selected by owner reroute 270290 and pinned in the matching FINDING entry; that
entry carries the exact file ownership for this correction and the named
departure for writing these two records. Claim 270293 is this work's claim.

WHAT IS BEING CORRECTED. `grant_writer.act` performs filesystem I/O inside
`ControlStore.transact`: `_validate_line_object(current)` stats the line root, and
`workspaces._prove_line_access(...)` re-stats it and checks group and mode, also
reaching `check_workspace_group`'s `os.getgroups()`/`os.getgid()`. The September 25
short-transactions ruling, reaffirmed 2026-09-26T01:04:01Z, forbids this.

THE SHAPE OF THE CORRECTION, using existing machinery and adding no lease.

1. Prove the filesystem facts ONCE, before the transaction is opened, over the
   line row read outside it: the recorded object identity, then the group and
   mode. Pin the exact `(line_path, line_device, line_inode)` those proofs were
   taken over. This runs AFTER the journal replay check, so a replayed grant does
   not repeat it.

   CORRECTED at review 2026-09-26T01:23:34Z: the first wording here said a
   replayed grant performs no filesystem work AT ALL, and that is wrong.
   `grant_writer` has always validated the line object near the top of the
   function, before the journal lookup, and this correction neither moved that
   call nor has a mandate to. What a replay skips is the RELOCATED access proof
   only. The delivered test measures exactly that.
2. Inside the transaction, keep every existing pure-database check -- the state
   admits a writer, the assignment is this attempt's at this generation, and the
   assignment, line state and current checkpoint have not drifted since the
   checkpoint validation -- and ADD a pure comparison of the current row's
   recorded object triple against the pinned one. No filesystem call remains in
   the callback.
3. Change nothing else. `profile.validate` is already outside the transaction;
   `workspaces._prove_line_access` is reused unmodified.

WHY THE PIN IS SOUND, stated as claims that must be checked rather than assumed.
`line_path`, `line_device` and `line_inode` are written once at line creation and
never updated afterwards, so the in-lock comparison is a fail-closed binding
against an out-of-band row edit rather than a reachable state transition. The
configured workspace group cannot change on a live store -- `configure_workspace_group`
refuses a different group with "a changed group is a fresh store rather than a
reconfiguration" -- so pinning the gid outside the lock cannot be defeated by a
reconfiguration. And the launch boundary re-proves both filesystem facts through
`_writer_access` before any container receives the line.

WHAT THE PROOF MUST SHOW, and the owner names five things:

- transaction exit before filesystem calls -- measured by observing
  `store._connection.in_transaction` at every filesystem call the admission
  makes, through a controlled boundary around the proof helpers;
- normal admission -- a first writer and a correction writer both admitted, with
  the committed rows and the line state as before;
- competing admission -- two real handles racing for one line, exactly one winner;
- stale generation -- an assignment that is not this attempt's generation refused;
- changed resource or checkpoint refusal -- a line object that no longer matches
  its recorded identity, a correction naming a checkpoint the line has moved off,
  and a row whose recorded triple no longer matches the proved one.

Real disposable stores and real files throughout; the checkpoint profile and the
authority port are the accepted deterministic fixtures, labelled.

```sh
cd /home/sl/src/baton/v12/python
BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
timeout --signal=TERM --kill-after=5s 120s \
  /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
  -m unittest test_grant_writer_admission
```

OUT OF SCOPE for this checkpoint, retained and not waived: the other
I/O-under-lock sites, the never-created-helper release gap, `assignment_workspace`
and its callers, the alias/object matrix, `dogfood_operator.py:4489`, the pending
`intake.py` `_settle` operand, remaining R3 coverage, R4 composed recovery and the
final R5 packet, plus the W247941 adoption obligations. No broad planning loop,
broad suite, live provider or engine, deployed recovery, cleanup or Git mutation.
Accepted delivery returns to baton.decide; a routine correction may iterate
directly with the reviewer.

## Superseded implementation checkpoint — restoration exclusion incomplete

Selected by owner reroute 270482, which also accepted the `grant_writer`
correction. The matching FINDING entry carries the exact file ownership, the
revalidation and the three superseded source comments. Claim 270485 is this
work's claim.

WHAT IS BEING CORRECTED. `restore_abandoned_correction`'s completing transaction
runs `_validate_line_object` and then `profile.restore_checkpoint` -- a whole
checkout restoration -- while holding `BEGIN IMMEDIATE`.

THE SHAPE, which is the one this function's own docstring already describes and
which the code drifted from when the restoration was moved under one lock.

1. INTENT TRANSACTION, short and database-only: record the recovery intent AND
   revoke the abandoned writer in the same act. That is what TAKES the exclusion,
   and `_sole_attachment`'s existing `writer is None` branch -- currently
   unreachable -- is written for exactly the state it leaves.
2. OUTSIDE ANY TRANSACTION: prove the line object, pin it, ask the profile to
   restore, and compare the answered evidence against the checkpoint's.
3. COMPLETION TRANSACTION, short and database-only: re-prove that the writer is
   revoked as this recovery revoked it, that the line is still `writing` at the
   exact checkpoint, that nobody at all is attached, and that the line row still
   names the object the restoration was performed against. Only then release to
   `correction-ready`.

SUCCESSOR ADMISSION IS BLOCKED THROUGHOUT by existing machinery and by nothing
new: the line is deliberately left `writing` from the intent until the completion,
and `grant_writer` admits a writer only from `idle` or `correction-ready`. No
schema change and no second lease.

THE OWNERSHIP GENERATION the completion is conditioned on is the abandoned
attempt's own generation, carried in the committed intent and cross-bound by
`_intent_agrees`; the completion additionally requires that the revoked writer is
still the line's only history and that no new attachment exists.

WHAT THIS ACHIEVES AND THE WINDOW IT DOES NOT CLOSE, stated before implementation
rather than after review. A second caller that arrives before the intent commits
races on the intent identity, and `store.transact` replays -- so exactly one
revocation happens. A second caller that arrives after it takes the resumed path,
which is the same path a crashed restorer's retry takes. Both are then bounded by
the pre-write and post-write proofs: once the first completion commits the line is
`correction-ready`, so a late restorer's own proofs refuse, and once a successor is
granted `_sole_attachment` refuses. THE RESIDUAL is a second restorer whose
pre-write proof passes and whose write lands after the first completion committed
AND a successor was granted AND that successor began writing -- content-identical
to the restoration it repeats, but capable of discarding that successor's work.
A short database transaction cannot close that once the filesystem act is outside
it; doing so needs a restoration lease or a filesystem-level exclusion, neither of
which this selection authorizes. It is recorded, not claimed as solved.

UNCERTAIN EXECUTION STAYS HELD: a `ProfileRefusal` is not a `ContractRefusal`, so
an interrupted restoration leaves the committed intent with no completion, the
writer revoked, the line still `writing` and therefore nobody admitted -- which is
the retryable state, not a release.

WHAT THE PROOF MUST SHOW, the owner's seven named things:

- normal restoration end to end, with the committed records;
- concurrent calls, through two real handles;
- failure and interruption inside the profile, leaving nobody admitted;
- safe retry and replay after that interruption, and an exact replay of a
  completed recovery;
- stale completion, where the world moved under an adopted intent;
- NO external I/O under any transaction, measured at every filesystem call;
- unrelated database progress while a restoration is paused inside the profile --
  which is the property the old lock destroyed and the reason for this correction.

Real disposable stores, real directories and real checkouts through the accepted
profile fixture with a controlled barrier inside `restore_checkpoint`.

```sh
cd /home/sl/src/baton/v12/python
BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
timeout --signal=TERM --kill-after=5s 120s \
  /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
  -m unittest test_restore_outside_the_lock
```

OUT OF SCOPE and retained: the `create_line` I/O-under-lock site, the other
enumerated sites, the never-created-helper release gap, `assignment_workspace` and
its callers, the alias/object matrix, `dogfood_operator.py:4489`, the pending
`intake.py` `_settle` operand, remaining R3 coverage, R4, the final R5 packet and
the W247941 adoption obligations. No broad planning loop, broad suite, live
provider or engine, deployed recovery, cleanup or Git mutation. Accepted delivery
returns to baton.decide.

## Superseded implementation checkpoint — incarnation does not exclude calls

Review 270595's P1 is accepted in full and the previous checkpoint's residual
paragraph is WITHDRAWN: owner 270482 already required exclusive restoration
ownership, so no new owner gate is sought. Claim 270605 is this work's claim. The
matching FINDING entry carries the exact path extension and file ownership.

THE DEFECT, exactly as reproduced. The resumed-intent branch treated a revoked
writer plus a shared intent as permission for ANY caller to perform the external
act. Neither proves the previous executor stopped. `_restoring` guards one
connection only. And because the completion identity is the recovery's, a delayed
executor's `store.transact` replays a foreign completion and never runs its own
post-effect checks -- so it answers success after a destructive effect.

THE CORRECTION.

1. The intent records `executor_incarnation`, the incarnation that committed it.
2. ONE executor check, placed where the fresh and resumed branches converge on
   `fixed`, so a caller that replayed a just-committed intent is held by the same
   rule as one that adopted an older intent. A mismatch refuses NON-DURABLY: the
   execution is unresolved and held, not failed.
3. The completion callback is fenced to the same incarnation, so a release can only
   be written by the executor that performed the effect.
4. Nothing else changes: the restoration stays outside every transaction, the
   intent still takes the exclusion by revoking, and the line still stays `writing`
   so no successor is admitted for the whole window.

WHY THE OVERLAP IS NOW PREVENTED BEFORE THE PROFILE IS ENTERED, which is what the
review required: B is refused at step 2 of its own call, before it reaches the
profile, so there is no second external crossing and no foreign completion for a
delayed executor to replay. A post-effect check cannot recover overwritten bytes
and is not what this relies on.

WHAT REMAINS HELD AND WHY THAT IS THE REQUIRED OUTCOME. A restoration whose
executor incarnation is gone stays held. Presence of an intent or a revocation is
not evidence that its executor stopped, and presuming death is exactly the
substitution this dossier has refused since stage 2. REMAINING SCOPE, not solved
here: nothing in this build positively settles a dead incarnation's in-flight
external act. `offers.py` settles OFFERS as `abandoned-after-restart` on the same
incarnation comparison, and that is not evidence about a checkout mid-write.
Supplying a positive settling act is a separate bounded selection.

THE LIMIT OF THE IDENTITY, stated rather than left implicit: an incarnation names
one manager instance, so two live connections sharing one incarnation are not
distinguishable by it. `_restoring` still contains the one-connection case. A
deployment that opens two stores under one incarnation is outside what this
identity can separate, and that is a property of the identity rather than of this
correction.

WHAT THE PROOF MUST ADD to the eleven cases already green, which the review
requires be retained: a deterministic paused-profile contention that measures
EXTERNAL CROSSINGS and SUCCESSOR BYTES -- the safe counterpart to the reviewer's
preserved unsafe reproduction; a competing caller already past its preliminary
reads; and unresolved execution on reopen under a new incarnation. The existing
no-I/O, unrelated-progress, normal, retry/replay, stale-completion and
successor-exclusion cases stay.

```sh
cd /home/sl/src/baton/v12/python
BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
timeout --signal=TERM --kill-after=5s 120s \
  /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
  -m unittest test_restore_outside_the_lock
```

OUT OF SCOPE and retained: the positive settling act above, the `create_line`
I/O-under-lock site, the other enumerated sites, the never-created-helper release
gap, `assignment_workspace` and its callers, the alias/object matrix,
`dogfood_operator.py:4489`, the pending `intake.py` `_settle` operand, remaining R3
coverage, R4, the final R5 packet and the W247941 adoption obligations.

## Superseded implementation checkpoint — process registry incomplete

Review 270696's P1 is accepted; the previous checkpoint's shared-incarnation
qualification is WITHDRAWN. Claim 270699 is this work's claim, and the matching
FINDING entry carries the exact path extension.

THE CORRECTION. `store._restoring` becomes a process-wide registry keyed by the
recovery's own operation identity, guarded by one lock, claimed before the
restoration and released as the call leaves. A second invocation -- any handle, any
incarnation -- that finds this recovery's external act in flight is HELD. The
executor-incarnation fence added last claim stays, as the review asks, and the
completion remains bound to it.

WHY BOTH OBLIGATIONS ARE MET. Exclusivity: a concurrent caller never reaches the
profile, so there is no second external crossing, no foreign completion to replay
and no successor whose bytes can be overwritten. Safe retry: an interrupted
restoration releases its entry as it unwinds, so the same executor's next call finds
nothing in flight and finishes through the existing resumed path. The
callback-execution-flag alternative would have met the first and destroyed the
second, which this review forbids.

WHAT THE PROOF ADDS to the fourteen cases already green, all of which are retained:
same-incarnation two-handle contention with external crossings and successor bytes
measured, and the same schedule with the competing caller already past its entry
reads. Cross-incarnation holding, reopen uncertainty, no-I/O, unrelated progress,
normal restoration, retry, replay, stale completion and successor exclusion stay.

```sh
cd /home/sl/src/baton/v12/python
BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
timeout --signal=TERM --kill-after=5s 120s \
  /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
  -m unittest test_restore_outside_the_lock
```

REMAINING SCOPE, unchanged and not waived: two distinct live processes restoring one
recovery need a durable claim with liveness, which is the same missing fact as
dead-executor settlement -- both turn on "has the prior executor stopped?". Plus the
`create_line` I/O-under-lock site, the other enumerated sites, the
never-created-helper release gap, `assignment_workspace` and its callers, the
alias/object matrix, `dogfood_operator.py:4489`, the pending `intake.py` `_settle`
operand, remaining R3 coverage, R4, the final R5 packet and W247941 adoption.

## Current checkpoint — 2026-09-26 store-bound execution claim

Review 270757's two reproductions are accepted; my in-process-closed and
cross-process-boundary statements are both WITHDRAWN. Claim 270760 is this work's
claim; the matching FINDING entry carries the exact path extension and the one
behaviour change.

THE CORRECTION, in the order it runs.

1. ADMISSION, one short raw transaction on the `create_line` precedent: read the
   completed recovery and return it if present -- so a stale caller observes the
   completion WITHOUT a second profile effect; re-prove eligibility from current
   rows rather than cached ones; read the latest execution episode and refuse held
   if it is unsettled.
2. THE EPISODE CLAIM, `store.transact` at the recovery plus episode+1 with a
   per-invocation executor token in its signature, so exactly one caller commits it
   and a loser's collision becomes the held refusal.
3. The restoration, outside every transaction, unchanged.
4. COMPLETION, fenced to that exact episode and token as well as to the executor
   incarnation, and its presence is what settles the episode.

The process-local registry is REPLACED rather than kept: two mechanisms that can
disagree are worse than one that cannot.

WHY EACH REPRODUCED SCHEDULE IS CLOSED. Stale in-process caller: its admission
re-reads the completion inside the lock and returns it with no crossing. Second
process: the parent's episode is claimed and unsettled, so the child is held --
enforced by a journalled row rather than by process memory or a reusable identity.

THE BEHAVIOUR CHANGE, and it is deliberate: a claimed episode whose profile raised
stays unsettled, so an interrupted restoration is held rather than resumed. The
review forbids inferring from a profile exception that external effects ended.
REMAINING SCOPE, unchanged and not waived: nothing positively settles an interrupted
external act, and supplying that act is a separate bounded selection. Until it
exists, an interrupted restoration needs operator attention -- which is the honest
state, not a regression disguised as safety.

WHAT THE PROOF MUST ADD, with the sixteen existing cases retained except where the
behaviour change requires them to be restated: safe counterparts for both reproduced
schedules, each measuring ACTUAL profile crossings and preserved successor bytes --
the stale in-process caller paused at admission, and a real second process. Plus the
interruption case restated as held.

```sh
cd /home/sl/src/baton/v12/python
BATON_V12_DISK_ROOT=/var/tmp/baton-w257624 PYTHONDONTWRITEBYTECODE=1 \
PYTHONPATH=/home/sl/src/baton/v12/python/src:/home/sl/src/baton/v12/python:/home/sl/src/baton/work/records/2026/09/finding-v12-failed-run-resource-hold \
timeout --signal=TERM --kill-after=5s 120s \
  /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning \
  -m unittest test_restore_outside_the_lock
```

OUT OF SCOPE and retained: the positive settling act, the `create_line`
I/O-under-lock site, the other enumerated sites, the never-created-helper release
gap, `assignment_workspace` and its callers, the alias/object matrix,
`dogfood_operator.py:4489`, the pending `intake.py` `_settle` operand, remaining R3
coverage, R4, the final R5 packet and W247941 adoption.

## Current checkpoint — 2026-09-26 documented reconstruction and revalidation

Owner 270917 selects documented reconstruction plus independent revalidation. Pinned
in the matching FINDING entry with exact ownership before the work proceeded. Claim
270942 is this work's claim.

DONE THIS CLAIM.

1. The current candidate is preserved byte-for-byte as
   `RECONSTRUCTION-CANDIDATE-2026-09-26T02-40-00Z.py.txt` (`a7760cd9…`), so the delta
   under review cannot move while it is reviewed. The reviewer's own preserved
   candidates are untouched.
2. BOUNDED RECOVERY INSPECTION, and it found nothing usable: 1,629 `review_cycles.py`
   copies hashed across `/tmp`, `/var/tmp` and `/home/sl`; none matches any of the
   five hashes this dossier has recorded for the file. Session captures, `__pycache__`
   and preserved dossier candidates were examined and rejected for stated reasons.
   The lost delta `b6083a63…` → `938bc0c6…` is UNATTRIBUTED: no Work record dated
   2026-09-18 or later claims to have edited this file.
3. The committed `b6083a63…` is therefore used as a reconstruction BASELINE ONLY, per
   the owner's wording, and never as proof that prior uncommitted changes survived.
4. `RECONSTRUCTION-2026-09-26.md` inventories all 44 deleted definitions with
   MEASURED evidence per function — a `settrace` collector recorded which of them
   actually execute under the accepted selectors. 41 are observed executing; THREE
   are not and are recorded as unresolved gaps: `_cleaned_review`, `_committed_act`,
   `_custodied_review`.
5. Duplicate definitions reconciled, with both pairs compared byte-for-byte before
   removal so no choice was made between diverging versions.

WHAT REVALIDATION STILL NEEDS, and it is the reviewer's to perform: the span read as
a delta against the baseline rather than trusted; the three uncovered functions, which
have no evidence either way; the re-typed corrections in section 3a, whose bytes are
mine rather than the reviewed candidate's; and the unattributed delta, which nobody
can produce. I claim no transfer of historical acceptance to any reconstructed byte.

THE RESTORATION CORRECTION continues in parallel and is unchanged this claim: the
store-bound execution episode, admission and claim in one transaction, 18 cases green.
Delivery requires BOTH this provenance reconciliation and that correction's
acceptance, as the owner states.

REMAINING SCOPE, unchanged: the positive settling act for an interrupted external act;
the `create_line` I/O-under-lock site; the other enumerated sites; the
never-created-helper release gap; `assignment_workspace` and its callers; the
alias/object matrix; `dogfood_operator.py:4489`; the pending `intake.py` `_settle`
operand; remaining R3 coverage; R4; the final R5 packet; W247941 adoption.
