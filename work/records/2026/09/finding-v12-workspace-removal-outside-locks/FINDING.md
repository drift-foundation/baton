# F2 — workspace removal and intake cleanup delete files under a database write lock

Bound dossier for v11 Work W270664, "V12: Remove workspace-deletion I/O from database
transactions". Created by baton.claude under claim 272502, 2026-09-26, because owner
270664 requires a dedicated dossier bound BEFORE implementation.

## Authority and exact selection

Owner 270664 (thread T270664) selects **F2 only** from
`baton:work/records/2026/09/finding-v12-db-lock-io-audit/AUDIT.md`, with these words:
"Correct standalone workspace removal and the enclosing intake cleanup transaction so all
external I/O occurs outside DB locks. Preserve hold-versus-removal exclusion,
aliases/object identity, both-root protection, delayed-submitter exclusion, exact cleanup
attribution and replay. Interrupted or uncertain removal must remain held." No other audit
finding, no broad suite, no live engine or provider, no deployed recovery or cleanup, and
no version-control mutation is selected.

The audit is DECISION SUPPORT, not implementation authority — owner disposition
2026-09-26 says so explicitly — and its own text ends "This report does not authorize their
implementation or transfer files." This dossier is where the implementation authority
granted by W270664 is recorded.

## Source identity at the start of this work

Measured 2026-09-26 under claim 272502:

    worker_manager/workspaces.py   6e8aade216538a91c6a355bdc4a8af42b0bb677259378a0d96b193767e78bf3d   3483 lines
    worker_manager/intake.py       9a7bded4121ba6f0406db1e5aface00ed1c725cf507483b6460b27abc2e914f2   4561 lines
    worker_manager/custody.py      3e977dfb0e12f58f05d85e5fc1e4dbe96b3e356db19dc60f9fe326e463c19022

**THE AUDIT'S LINE NUMBERS ARE STALE AGAINST THESE BYTES, and that is the first thing a
reader needs.** The audit cites `_serialized_removal:1673`, `refuse_if_held:1688`,
`_real:1782`, `discard_workspace:2790`, `discard_execution_roots:2958`,
`_execution_roots_removed:2964`, `_remove:3169` and the endorsing comments at
`1573ff/2788/2946`. W257624's accepted restoration-lock additions to the same file have
shifted every one. The CURRENT locations, verified by name rather than by number:

    _serialized_removal          workspaces.py:1730
    refuse_if_held               workspaces.py:1846
    _real                        workspaces.py:1940
    discard_workspace            workspaces.py:2922   (endorsing comment 2945-2947)
    discard_execution_roots      workspaces.py:3065   (endorsing comment ~3104)
    _execution_roots_removed     workspaces.py:3122
    _remove                      workspaces.py:3327
    intake.authorize_cleanup     intake.py:1120
    intake._settle               intake.py:4459  -> discard_execution_roots at 4556

Any correction must be re-anchored by NAME. A patch driven by the audit's numbers would
land in the wrong place in these bytes.

## What is actually wrong, re-verified against the current source

**THE STANDALONE PATH.** `_serialized_removal` (1730) deliberately performs the hold read
AND the removal inside one `control.transact`, which takes `BEGIN IMMEDIATE`. Its own
docstring says so — "Check the holds and remove UNDER THE SAME WRITE LOCK R1's claim
takes" — and explains why that was chosen: between an unprotected `refuse_if_held` and the
tree coming off the disk, a concurrent `custody_act` could commit a hold for exactly that
root. The serialization is real. What is not permitted any more is the mechanism: owner
ruling 2026-09-25/26 forbids holding a database lock across external I/O, and the removal
callback reaches `_remove` (3327) — mount-table and tree inspection, permission changes,
`unlink`/`rmdir` — while `refuse_if_held` (1846) reaches `_real` (1940) and therefore
`os.path.realpath`, which is itself filesystem I/O.

**THE ENCLOSING PATH.** `intake._settle` (4459) calls `discard_execution_roots` (3065) at
4556 from inside the cleanup's own write transaction. `_serialized_removal`'s nested branch
at 1793 sees `connection.in_transaction`, rechecks the holds and calls `removing()`
directly — so correcting only the standalone `transact` would leave this path deleting
under the intake lock, and the outer `realpath` in `discard_execution_roots` would run
there too.

**IMPACT.** Deletion and its preflight block every unrelated manager write for as long as
the filesystem takes, and a rollback cannot restore removed data — the journal can only
ever be behind the filesystem for a removal, never ahead of it.

## What must be preserved, not traded away

Each of these is an accepted property of the current code and none of them is negotiable
in the correction:

* **Hold-versus-removal exclusion (R1).** A `custody_act` hold committed for either root
  must still refuse the removal, with no window between the decision and the effect.
* **BOTH ROOTS, ALWAYS.** `custody._derived_root` puts the result root INSIDE the
  workspace, so the two roots of one attempt overlap; a hold on either covers the other.
* **Object and alias identity.** `_real` exists because lexical containment is not
  containment; a symlink component looks ordinary until it is followed.
* **Delayed-submitter exclusion** and **exact cleanup attribution**.
* **Exact per-call answers.** `discard_execution_roots` answers WHICH roots this act
  removed and `()` when there were none; `_serialized_removal` carries a nonce precisely so
  a second removal is not a replay of the first's answer. Replay semantics must not be
  reintroduced by accident.
* **UNCERTAINTY IS HELD.** An interrupted or unresolved removal must leave the act held,
  not presumed done — the same rule W257624's recovery follows.

## Ownership coordination with W257624

W257624 ("Bounded failed-run recovery and durable resource hold") is a live correction in
the same file. Its narrow ownership in `workspaces.py` is exactly:

    RESTORATION_LOCK, restoration_lock_path, RESTORATION_LOCK_KIND,
    _restoration_lock_identity, hold_restoration_lock

W270664's region in the same file is disjoint from those five:

    _serialized_removal, refuse_if_held, discard_workspace,
    discard_execution_roots, _execution_roots_removed, _remove, _summary

plus `intake._settle`'s removal call site. Neither region calls the other. W257624 also
owns `review_cycles.py`, `checkpoint_profiles.py`, `tools/stage_execution.py` and
`work/records/2026/09/finding-v12-failed-run-resource-hold/test_restore_outside_the_lock.py`;
this Work touches none of them. `intake.py` was named in W257624's handoffs as a PENDING
`_settle` operand item that it never claimed and never edited; W270664 is where that site
is now owned. If both Works are ever active at once, this paragraph is the boundary to
check.

## 2026-09-26T06:21:32Z — reviewer planning checkpoint; reciprocal admission required

Reviewer272543 confirms the current standalone/nested deletion-under-transaction diagnosis.
No implementation has been offered, and no acceptance of F2 correction is given. Continue
directly to implementation under owner270664/routing272500. Latest review is
review-2026-09-26T06-21-32Z.md; complete discussion position270664/events272543.

Confirmed custody._claim_episode.claiming currently checks custody overlap, not proposed
removal ownership. Therefore the initial seven-function ownership list is insufficient for
its promised mutual exclusion: pin minimal reciprocal hold/reuse/adoption admission hooks
before editing and coordinate any live ownership. This is necessary selected F2 scope.
The plan's completion hold recheck cannot substitute for pre-effect exclusion. Moving the
intake effect must also preserve its submitter/provider/custody/retention preconditions and
lane ownership before deletion, not discover refusal after destructive work.

This environment does not authorize the proposed /var/tmp/baton-w270664 test root; use a
unique /tmp root here without disturbing W257624 residues. No tests run or source changed
by reviewer. Voluntary planning-only return is continuation, not a new owner decision gate.

## 2026-09-26T06:34:57Z — partial implementation; cleared-history regression

Reviewer272635: workspacesb1e2d3a/custody162978f3 now separate standalone deletion from
SQL and reciprocally exclude custody admission. Eight author cases pass0.046s. Independent
review_cleared_hold_20260926.py errors1/0.005s: _journal_holds includes cleared episodes,
unlike existing refuse_if_held, blocking removal after reconciliation. Reader-output
simulation, not operator-clearance evidence. Correct and prove actual cleared/mixed histories.
No standalone safety acceptance: object identity pinning, reuse/adoption exclusion,
absent-but-unresolved distinction, enclosing intake and remaining race proofs unfinished.
Latest review review-2026-09-26T06-34-57Z.md; thread270664/events272635 consumed. Continue
implementation under existing authority, no new owner gate. W257624 region preserved.

## 2026-09-26T06:39:23Z — cleared-history predicate correction verified

Reviewer272675 accepts narrow _journal_holds correction using _standing_overlap on
workspaces1e70c528. Author9 plus independent probe1 pass0.058s. This supersedes previous
predicate defect, not remaining F2 requirements. New history coverage mocks custody_holds;
actual recorded clearance/mixed histories remain unproved. Exact limits and next executable
scope in review-2026-09-26T06-39-23Z.md/current PLAN. Continue baton.impl directly; no new
owner gate, no standalone safety/full acceptance. Known114.346s plus separate approximations.

## 2026-09-26T06:44:15Z — clearance precedent and root location clarified

Reviewer272713 corrects claim272688's absent-precedent assertion: sibling W257624
test_hold_clearance.py contains actual clear_custody_hold calls, with deterministic
answered/clearing helpers at102/129 and invocation145. Its evidence is outside tests/.
Reuse applicable design after revalidation; do not edit sibling evidence or claim live
operator receipts. custody_holds wraps the root inside held; standing['held']['root'] is
the exact location already requested, not the top-level key still being read.
Latest review06:44:15/current PLAN preserve remaining substantive F2 work. Continue
implementation directly, no further labeling-only checkpoint requested. No new tests run,
known130.280s plus approximations, no full acceptance or scope expansion.

## 2026-09-26T06:48:32Z — absent-but-unresolved refusal accepted narrowly

Reviewer272744 verifies workspacesba1599e6/testf7a985cf:11 focused tests0.062s all pass.
Missing-home branch now holds outstanding removal instead of returning ordinary absence;
root diagnostic uses held.root. These bounded corrections are accepted, superseding their
remaining status in prior checkpoints. Actual-object/reuse/adoption/intake/race/clearance
work remains open. Latest review06:48:32 and current PLAN give next executable milestone.
Known138.398s plus separate approximations; no full acceptance or new owner gate.

## 2026-09-26T06:54:02Z — post-check replacement still deleted

Reviewer272784 rejects claim272758's completed actual-object binding: on workspacesb7abace8,
independent review_after_pin_swap_20260926.py permits the identity check then swaps home
before path-based removal; replacement directory and marker are deleted.13 tests0.072s:
12pass/1failure. Pre/post stat is detection across one interval, not retained object authority.
Continue selected correction through effect/final deletion, preserve unknown observation
errors and complete reciprocal admission/intake/evidence work. Latest review06:54:02 and
current PLAN own next scope. Known146.602s plus approximations, no new owner gate or acceptance.

## 2026-09-26T06:57:08Z — overclaim withdrawn; behavioral correction still owed

Reviewer272813 confirms claim272806 is documentation-only and preserves the P1 replacement
failure. Descriptor-relative traversal must also address final parent/name replacement and
mount/preflight guarantees; no-follow opening alone is not complete identity preservation.
No observed runner limit supplied for repeated voluntary stopping rationale. Continue
implementation under existing F2 authority, not another documentation-only handoff.
Latest review06:57:08/current PLAN retain exact remaining work. Known146.667s plus prior
approximations, no new tests/behavioral acceptance, ownership and W257624 protection intact.

## 2026-09-26T07:01:39Z — failed shortcut is implementation evidence, not acceptance

Reviewer272850 verified unchanged vulnerable workspacesec97b942 after author-reported
revert. Proc-fd/lstat experiment failures guide the authorized explicit descriptor work;
they are not a new authority gate. Correct claim272826's attribution: review06:57:08 did
not accept parent-fd + child-stat + rmdir as final-child authority; it warned of precisely
that remaining name-replacement window. Preserve exact admitted object/exclusion through
effects and prove late swaps. Latest review07:01:39/current PLAN retain remaining scope.
Known164.686s plus prior approximations, no new reviewer tests or behavioral acceptance.

## 2026-09-26T07:07:30Z — descendant swap deletes material outside admitted tree

Reviewer272890 verifies whole-home swap now passes on workspaces53e5a03b, but rejects
claim272864's broader object-safety conclusion. New review_descendant_swap_20260926.py
replaces workspace with a symlink after preflight; outside fixture marker is deleted by
the pathname-based second pass.14 checks0.078s:13pass/1failure. Root descriptor does not
pin descendants. Final-name empty-directory loss is also within selected preservation
scope, not optional reviewer preference. Latest review07:07:30/current PLAN require
completion under existing authority. Known192.943s plus approximate/unspecified costs.

## 2026-09-26T07:14:23Z — reverted pathname recheck does not resolve binding

Reviewer272949 verifies unchanged53e5a03b, descendant escape remains. Reported experiment
rechecking pathname+stat would still retain post-check race even after fixing its errors.
Latest review07:14:23 supplies a bounded retained-directory-handle implementation sequence,
fd API clarification, and focused failure isolation with preserved exact evidence. Continue
authorized implementation; no new owner gate or observed runner limit. Known221.015s plus
ambiguous/ranged/unspecified costs; no reviewer rerun or behavioral acceptance.

## 2026-09-26T07:21:42Z — retained-handle traversal passes adapted descendant proof

Reviewer273000: workspaces50dd358c/test95b6e9f7 passes14 focused checks0.076s. New walk
retains verified directory handles across preflight/effects; adapted _thaw_handle swap
triggers and outside marker survives. Narrow discard_workspace descendant escape corrected,
superseding prior failing status for that schedule. Old _thaw probe is no longer applicable,
not counted green. Final-entry/reuse/adoption/intake/clearance/uncertainty/race work remains.
Latest review07:21:42/current PLAN specify boundaries. Known229.027s plus prior costs;
no full F2/standalone safety acceptance or new owner gate.

## 2026-09-26T07:25:48Z — early guard is not reciprocal admission

Reviewer273030 rejects claim273016's final-entry/mutual-exclusion completion. On
workspaces04823522, review_adoption_admission_20260926.py admits removal after adoption's
guard returns and adoption still succeeds.16 checks0.086s:15pass/1failure. Also actual
assignment_workspace lacks the alleged common guard/control operand. Implement atomic
mutual admission and lifetime, with both ordering proofs, under existing F2 selection.
Latest review07:25:48/current PLAN preserve other remaining scope. Known237.175s plus
unspecified/approximate costs, no new owner gate or full acceptance.

## 2026-09-26T07:31:02Z — documentation correction; continue existing implementation

Reviewer273077 read complete handoff273056 and verified source/test hashes unchanged.
Author withdraws mutual-exclusion claim; independent adoption race remains open. Latest
review-2026-09-26T07-31-02Z.md records caller audit starting points and required admission
lifetime beyond an early read or premature release. No new reviewer tests; author0.072s
brings known sum to237.247s with unknown costs preserved separately. Direct continuation
to baton.impl under current scope; no owner gate or full acceptance. Personal context
concern is not verified runner exhaustion; supported maintenance only, no live reset.

## 2026-09-26T07:35:55Z — adoption admission fixed narrowly; premature release reproduced

Reviewer273108 on ce7d5c59:18 checks0.106s,17pass/1new failure. Previous admission
probe now passes, but new review_adoption_lifetime_20260926.py runs real removal after
honest settlement and before adoption returns; caller receives deleted roots. Narrow
admission accepted, lifetime/final-entry completion rejected. Continue existing scope
with actual-use lifetime or gap-free authority transfer and safe release/recovery, then
allocation and remaining intake scope. Latest review07:35:55/current PLAN pin continuation.
Known245.569s plus separate unknown/estimated costs; no full acceptance or new owner gate.

## 2026-09-26T07:39:12Z — narrow caller ownership coordinated; test authority clarified

Reviewer273142 verified W257624 unclaimed/queued to owner at canonical snapshot273142,
restoration milestone accepted and review_cycles.py unchanged edfe46fe. This supersedes
the original blanket no-touch statement for that file ONLY for necessary F2 lifetime
wiring in _writer_access, writer_boundary, review_boundary and associated grant callbacks.
baton.claude owns those narrow changes under W270664; restoration regions and sibling
artifacts stay protected. Recheck live state before editing and coordinate actual overlap.
Latest review07:39:12 names omitted tool callers, exact affected test paths and standing
test-change authority. No separate accepted-suite gate, broad redesign or sibling scope
transfer. Implementer chooses and proves lifecycle shape under existing F2 requirements.
Product unchanged and lifetime defect remains; no new behavioral acceptance/test rerun.

## 2026-09-26T07:45:20Z — mount regression diagnosis corrected at actual observation

Reviewer273184 verified ce7d5c59 already checks retained handles with fstat and mount-table
membership, including root. Three new simulated handle-boundary probes pass0.016s before
effects. Exact legacy cross-device test fails because its lstat mock no longer injects at
the active boundary; existing same-device table case passes (combined2cases0.027s).
This supersedes handoff273181's inferred missing-current-guard diagnosis, not the old red
test evidence. Adapt test with assertions preserved and fired-injection proof; no real
mount evidence/full mount safety claim. Implement previously coordinated actual-use
lifetime with caller wiring next. Latest review07:45:20/PLAN preserve remaining F2 scope,
ownership, honest baseline limits and costs. No new owner gate or full acceptance.

## 2026-09-26T07:51:15Z — mount-test adaptation independently accepted

Reviewer273234 verified test_source_boundary28776c75: injected foreign device now reaches
current fstat observation; original refusal/marker assertions retained and fired assertion
added. Focused10checks0.075s:9pass/1real-mount skip. No actual mount proof, no inference
of both-entry coverage from mocking both observers. Sourcece7d5c59 unchanged; lifetime
defect still open. Latest review07:51:15/PLAN direct implementation through actual-use
lifetime and caller wiring under coordinated ownership, then remaining F2 scope. No new
owner gate/full acceptance; known259.188s plus separately preserved discrepancy/unknowns.

## 2026-09-26T07:58:05Z — bare lifetime improved; grant/line transfers still unsafe

Reviewer273282 on workspaces0b37aa50:18checks0.117s,16pass/2new failures. Bare adoption
retains exclusion until explicit release, narrowly accepted. New immutable transfer probe
shows real removal succeeds after _granted_roots and line_assignment_workspace: neither
provides a removal-visible target exclusion after releasing adoption, and the line roots
still expose attempt inputs. Supersedes handoff273278's complete-lifetime/gap-free claims.
Tool release endpoints/retryable settlement remain unproved; local token clears before
commit. Latest review07:58:05/current PLAN carry exact correction under existing ownership.
Known276.326s plus reported ranges/discrepancy/unknowns; no full acceptance/new owner gate.

## 2026-09-26T08:02:18Z — transfer success/release retry accepted; validation orphan found

Reviewer273314 on73679b1b:19tests0.121s,17pass/2fail. Successful line transfer now retains
exclusion and settlement failure leaves retry token, narrowly accepted. Grant gap persists.
New review_adoption_release_20260926.py proves invalid line rejection leaves durable
adoption with no returned token. Correct pre-handover failure cleanup and grant/caller
lifetime under existing authority. Current review08:02:18/PLAN clarify control already
reaches removal and missing release wiring is not an authority gate. Known281.594s plus
separate ranges/discrepancy/unknowns; no full adoption/F2 acceptance.

## 2026-09-26T08:09:45Z — real writer SQL verified; reverse admission fails

Reviewer273367 on0389b407:22tests0.138s,20pass/2fail. Rejected-composition cleanup
accepted. New real ReviewCycles fixture probe verifies writer row blocks removal, but
writer admission succeeds after removal ownership commits. Generic grant transfer still
fails; one-sided SQL read is not full mutual exclusion. Latest review08:09:45 pins exact
proof and minimal additional grant_writer.act/attach_review.act/helper ownership plus
focused test_review_cycles cases. W257624 rechecked273376 unclaimed/queued owner; this
refines prior caller-only coordination without touching restoration or sibling artifacts.
Continue reciprocal admission/actual target and remaining F2 scope, no new owner gate.
Known291.856s plus preserved ranges/discrepancy/unknowns; no full acceptance.

## 2026-09-26T08:14:20Z — reciprocal lifecycle admission independently verified

Reviewer273405 on workspaces1b52ecca/review_cycles45174179:24checks0.157s all pass.
Real writer and review attachment admission exclude removal in both orders; generic
grant binding without durable target retains its token. Prior transfer/cleanup/retry remain
green. New real-attachment probe complements immutable writer proof. Narrow acceptance
of these corrections; lifecycle/tool release/cessation, allocation, enclosing intake and
remaining identity/clearance/uncertainty/race obligations remain. Latest review08:14:20/
PLAN pin continuation and reuse of existing regression probes without duplicate-work gate.
Known303.950s plus separate ranges/discrepancy/unknowns; no full F2 acceptance/new owner gate.

## 2026-09-26T08:20:11Z — additional author writer regression accepted

Reviewer273456 independently ran new test_real_rows_exclude_removal:2tests0.012s pass.
Source unchanged1b52ecca/45174179; prior independent acceptance remains. Additional
author coverage is accepted, not a new product milestone or review-attachment test.
Continue remaining lifecycle/tool/allocation/intake implementation per latest review08:20:11
and PLAN, reusing existing proofs without duplicate-test gate. Known306.188s plus prior
ranges/discrepancy/unknowns; no full F2 acceptance/new owner gate.

## 2026-09-26T08:28:42Z — intake hoist violates eligibility-before-delete

Reviewer273513 on intake4f8544ae/workspaces1da84358:real cleanup with simulated pending
submitter answer deletes actual execution-root marker before _settle raises the expected
refusal. Immutable review_intake_order_20260926.py decisive1test0.022s fails; preliminary
fixture setup failure recorded separately. Reject handoff273511's complete intake/order
claim; exact eligible admission must precede effects, completion/lane release follow them.
Completed standalone removal before runtime.destroy commit also contradicts blanket claim
that this crash gap always leaves unresolved removal. Latest review08:28:42/PLAN pin
correction/proofs and existing remaining scope. Known322.701s plus previous ranges and
unknowns; no full acceptance/new owner gate.

## 2026-09-26T08:33:54Z — submitter fixed; enclosing and nested I/O still inside lock

Reviewer273552 on intake625e1029/workspaces1da84358:3checks0.056s,1pass/2fail.
Pending-submitter roots survive, narrow correction accepted. New review_cleanup_io probe
observes six lstat calls under normal cleanup transaction through adopted custody and
configured-store validation; nested removal performs11lstat/1stat before its refusal.
This rejects handoff273550's no-lock-I/O claim. Preserve identity checks while moving
observation outside and binding exact evidence inside; reject nested entries before I/O.
Latest review08:33:54/PLAN preserve cleanup-gap/retry and remaining scope. Known336.791s
plus prior ranges/discrepancy/unknowns; no full F2 acceptance/new owner gate.

## 2026-09-26T08:38:33Z — nested refusal fixed; enclosing six lstats remain

Reviewer273594 on0226bf93/98d93613:cleanup_io2tests0.039s,1pass/1fail. Nested workspace
refusal observes no I/O; second public removal's first guard inspected. Accept narrow
fix; enclosing receipt/configured-store validation still performs6lstat under transaction.
Latest review08:38:33/PLAN direct prepared physical identity outside/exact DB provenance
inside, then measured cleanup-gap/retry and remaining scope. No full F2 acceptance/new
owner gate. Known337.758s plus new ranges and preserved unknown/discrepant costs.

## 2026-09-26T08:43:12Z — dynamic trace pins all six calls to custody adoption

Reviewer273629 verifies unchanged intake98d93613 after author revert. New immutable
review_cleanup_trace probe1test0.023s captures all six locked lstats through _settle /
_adopted_custody / adopted_directory_custody / _recorded_store / configured_workspace_storage,
three validators per receipt. Supersedes handoff273627's current-code inference that
custody is not their source. Temporary failed experiment remains unverified history.
Current direct-call search yields one shared _settle invocation;32 failed tests alone
do not establish multiple caller shapes. Latest review08:43:12/PLAN pin exact tracing,
caller audit and prepared-evidence continuation. Known345.753s plus approx0.04s/prior
ranges/discrepancy/unknowns; no full acceptance/new owner gate.

## 2026-09-26T09:15:26Z — prepared storage accepted; cleanup gap independently reproduced

Reviewer273826 on80cf382f/3191571e/2630e188:23tests0.186s pass. Accept narrow
prepared-storage correction removing the six locked lstats while rechecking DB
provenance. New immutable review_cleanup_gap_20260926.py interrupts actual cleanup
before runtime.destroy commit after execution-root removal: allocation succeeds,
then exact retry deletes a fresh inputs marker.2decisive failures0.048s; preliminary
fixture assertion failures0.041s separately recorded in review09:15:26.
Allocation/exact retry exclusion is already-authorized next implementation, not
an owner gate. Place rebinding alone is not retained physical identity. Adjacent
non-deleting recordless cleanup readers still need DB-I/O audit classification;
do not silently widen F2. PLAN/new review pin continuation and unchanged ownership.
Known536.423s plus separate estimates/ranges/unknowns; whole F2 remains unaccepted.

## 2026-09-26T10:07:07Z — serial gap corrected; two concurrent exclusion failures

Reviewer274184 on160deb19/029e2289 independently passes29tests0.278s for serial
gap and locked-I/O correction. New review_allocation_race_20260926.py confirms
allocation succeeds after its guard returns and cleanup admission commits. Also,
same-operation second cleanup settles while first is paused; first resumes deleting
material allocated after settlement.2tests0.050s fail; initial single race0.024s.
This supersedes handoff274182's broad completion-gap/fencing claim: matching operands
plus deletion idempotence does not fence still-live execution. Required reciprocal
admission and retry fencing remain within scope, without locks across external I/O.
Fail-open authority uncertainty also remains a source finding. Seven tool allocation
callers still exist; zero-callers inference omitted v12/python/tools. Latest review/PLAN
pin exact evidence, correction and unchanged ownership. Known1069.679s plus separately
retained ranges/estimates/unknowns. Whole F2 unaccepted; direct implementation return.

## 2026-09-26T10:26:51Z — prior race corrections accepted narrowly; authority observation bypass

Reviewer274330 on303a1344/f5b48b38 independently passes32tests0.368s. Reciprocal
allocation admission and cleanup owner checks fix the two earlier interleavings.
New review_allocation_uncertainty_20260926.py1test0.024s fails: real cleanup hold
exists, local connection closed, journal-only stat raises PermissionError, isfile
returns False, allocation proceeds. This supersedes handoff274328's claim that
the no-journal path established absence. Unknown authority must fail closed; even
pathname absence alone is not proof all prior execution/authority ended. Exact
evidence and next caller/lifetime continuation in latest review and PLAN. Seven-site
caller inventory correction accepted. Known1282.439s plus separate40s author report
and retained ranges/estimates/unknowns. Whole F2 remains unaccepted; no owner gate.

## 2026-09-26T10:40:33Z — uncertainty correction accepted; explicit authority lost on reopen

Reviewer274426 on4e3a9980 independently passes34tests0.398s. Prior permission-error
fix and seven explicit tool operands accepted narrowly. New immutable
review_explicit_control_20260926.py1test0.037s fails with two real disposable stores:
explicit store holds interrupted cleanup; group comes from another store configured
to same storage; close explicit connection; allocation reopens group minter and
bypasses the hold. _asking_control must preserve selected control identity/provenance
or refuse. Latest review/PLAN pin correction and remaining lifetime/clearance/identity
milestones under unchanged ownership. Known1419.740s plus separate reports/estimates/
ranges/unknowns; whole F2 unaccepted and direct implementation return, no owner gate.

## 2026-09-26T10:53:09Z — selected path fixed; replacement between check and open bypasses hold

Reviewer274516 onf73045bd/4dca4609:38tests0.447s pass. Narrow explicit-control
pathname fix accepted. New review_journal_open_race_20260926.py1test0.029s fails:
swap two actual fixture journals after stat/before connect, allocation proceeds
despite original journal hold. Initial EXDEV fixture error0.034s separately recorded.
This supersedes handoff274509's claim of proved opened-object identity. Bind actual
connection authority or refuse; inspect initial-open provenance and expected=None
skip against the same rule. Latest review/PLAN pin bounded store ownership and
remaining continuation. Known1511.058s plus retained estimates/ranges/unknowns.
Whole F2 unaccepted; direct implementation correction, no owner gate.

## 2026-09-26T11:04:20Z — process-wide descriptor scan falsely attributes connection identity

Reviewer274594 on c383f690/03553a35:40tests0.523s pass. New
review_connection_attribution_20260926.py1test0.029s fails: retain original fd,
swap/open/restore two real fixture journals; scan matches unrelated original fd,
allocation bypasses original hold through replacement SQLite connection. Helper
never uses connection argument. Supersedes handoff274592 connection-identity claim;
procfs portability is not the primary defect or new gate. Latest review/PLAN pin
actual attribution correction and unchanged remaining milestones/ownership.
Known1593.476s plus retained estimates/ranges/unknowns. Whole F2 remains open.

## 2026-09-26T11:19:15Z — descriptor delta still accepts an unrelated connection

Reviewer274699 on8a7e420b/635834c8:41tests0.543s pass. New immutable
review_descriptor_delta_20260926.py1test0.029s fails: open unrelated original fd
inside attribution window after replacement SQLite open and pathname restoration;
delta falsely approves replacement. Supersedes handoff274697 soundness claim.
Global mutex covers only cooperating opens. Require actual connection evidence or
explicit safe refusal/caller contract. Changed concurrency test is additional local-
handle coverage, not preservation of former shared-group behavior; retain old-path
coverage. Durable identity design not selected: clone ambiguity remains despite
pathname/reachability. Latest review/PLAN pin continuation, unchanged scope/protection.
Known1686.439s plus separate estimates/ranges/unknowns. Whole F2 remains unaccepted.

## 2026-09-26T11:28:13Z — safe refusal accepted; obsolete reopen probes retired

Reviewer274768 on8e4aaedc/3d449912:45tests0.653s pass. New immutable
review_control_refusal_20260926.py proves closed/off-thread control refusal before
creation and positive thread-local allocation. Accept bounded no-implicit-reopen
contract, including explicitly documented old shared-group compatibility change.
Four historical descriptor_delta/connection_attribution/journal_open_race/
allocation_uncertainty interception probes retired from current execution, unchanged,
not counted as passes; latest review names them and replacement evidence exactly.
This resolves selector ownership/disposition issue without new gate. Continue remaining
lifecycle/tool/clearance/uncertainty/identity/race milestones; whole F2 open.
Known1749.794s plus retained reports/ranges/estimates/unknowns. Ownership unchanged.

## 2026-09-26T11:36:52Z — pin owner-required token and Docker enforcement; supersede old sequence

Canonical decision: OWNER-TOKEN-BATON-20260926.md, including its appended Docker
clarification; T270664 messages274815 and274827. Owner requires atomic exclusive
durable resource token with eligibility/replay, exact operation/execution/generation/
expiry and running-container binding, reserve-before-launch/delayed-launch exclusion,
external I/O outside DB locks, exact conditional completion, expiry revocation,
shutdown of the exact bound Docker container and positive cessation of every writer
before reset/new generation. Unknown holds remain. Generic process-only tokens or
voluntary checks are insufficient; manager-owned effects outside the container fence
need enforceable ownership. Accepted no-implicit-reopen remains infrastructure.

This explicitly supersedes the older current next-step ordering in review11:28:13
and PLAN and any interpretation that earlier generic admissions alone meet delivery.
Preserve all historical accepted proofs. Owner allows a concrete minimal schema/API
extension with exact paths/compatibility recorded; earlier unselected generic identity-
row restrictions do not veto required token work. No broad architecture, live Docker,
deployed reset or Git expansion. First executable vertical slice on actual F2
removal/allocation with controlled adapter and real coordination/runtime evidence,
then remaining F2 paths. No plan-only loop or renewed routine approval gate.

Reviewer274856 preserves author partial review_boundary9ce03a44;36focused tests
0.316s pass helper/refusal regressions, not actual-boundary/token acceptance. Exact
remaining scope and ownership in review11:36:52/current PLAN. Known1762.543s plus
retained ranges/estimates/unknowns. Whole Work remains open, direct implementation.

## 2026-09-26T11:47:38Z — token candidate fails; owner specification alignment next

Owner sequencing in final OWNER-TOKEN-BATON-20260926.md section and T270664/274873
explicitly supersedes the preceding direct-implementation next route for this review:
return baton.decide, preserve candidate/evidence/gaps, align with prompt-authored
normative v12/DESIGN.md then Claude spec review/sign-off. No full acceptance implied.

Reviewer274939 on workspacesdac1ba4e:40tests0.344s pass; new immutable
review_token_generations_20260926.py3tests0.023s fail. Ceased generation1 masks live
generation2 so3 acquires; revoked/unbound old token binds late container after successor;
string false accepted as positive cessation. Bind/revoke helpers have no product
callers; container runtime enforcement and common allocation/cleanup token lifecycle
remain incomplete. Manifest and exact gaps in review11:47:38/current PLAN.
Operational finding: v12/DESIGN.md absent on read, no conformance asserted. Preserve
accepted no-reopen/W257624 and partial source. Known1776.111s plus retained unknowns.
