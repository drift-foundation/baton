# Bounded managed correction preparation — claim307667

Authority: owner E307633, E307644 and E307645; baton.rvpc preparation,
then baton.tuner implementation, independent baton.bug review, accepted delivery
to baton.decide. Routine corrections return to baton.tune for this Work.

## Selected milestone

Make one useful managed correction restore the qualified producer conversation
and matching retained workspace in a fresh execution after exact predecessor
termination. First deliver current-code deterministic proof and the minimum
concrete provider-specific packet; live execution remains a separate owner
selection. Do not resurrect the combined mega Job or repeat parallel adoption.

The next implementation is ready to start with the confirmed admission defect
below; missing live input does not block deterministic development. Preserve
W239528/W239533 acceptance and the accepted subject, consumed grants, historical
failures and W177936 qualification. None is a completed production restore.

## Confirmed current-code blocker and baseline

`v12/python/src/baton_v12/worker_manager/provider_context.py`:
- `_transition` executes its `check` inside `ControlStore.transact`.
- `_check_admission` calls `_facts` there; `_facts` calls Job-store and Authority
  readers and `context_delivery._open_absolute` on both workspace and source.
- `bind_context_invocation.commit` repeats `_facts` inside the same transaction.
`worker_manager/store.py:transact` uses BEGIN IMMEDIATE before invoking action.
This violates DESIGN DB-1/2/4. Merely moving the checks earlier loses freshness:
DB-3/5 require durable reservation, local conditional comparison, external
validation and a launch/publication fence for stale cross-store evidence.

RESEARCH-307667.json dynamically confirms two `_open_absolute` calls inside the
provider-context.transition action during a successful public admission.
A disposable `tests.manager.test_provider_context.ContextCase` supplied the real
ControlStore/JobStore and fake Authority; wrappers around `control.transact`'s
action and `context_delivery._open_absolute` recorded nesting, then `case.admit()`
ran. No raw SQL/read, deployed store, engine or provider was used. Elapsed
0.012545002973638475s excludes fixture cleanup; command wall0.049462389s. This
localizes the defect, not connected lifecycle compliance. Invocation defect is
source-confirmed, not independently executed this turn.

## Patch boundary and exclusive ownership at handoff

Tuner owns subsequent implementation in this dossier (new candidate/evidence,
packet/task files and append-only attributable PROGRESS) and these product paths:
- v12/python/src/baton_v12/worker_manager/provider_context.py
- v12/python/src/baton_v12/worker_manager/context_delivery.py
- v12/python/tests/manager/test_provider_context.py
- v12/python/tests/manager/test_provider_context_delivery.py
- v12/python/tests/manager/test_claude_context.py

For the connected seam only, Tuner may amend `v12/python/tools/stage_execution.py`
and `v12/python/tools/single_worker.py`, recording the exact symbols and baseline
hashes before editing. Current seams are prepare_context/revalidate_context/end
and SingleWorker context preparation before request_runtime_start. Coordinate
any new active overlap before editing; do not replace an entire changed file.
Reuse `v12/python/tests/tools/correction_restart_trace.py` and
`test_correction_restart.py`; extend narrowly if necessary, recording paths and
changed expectations. Those historical tests include simulated preparation
machinery: do not import that as authority to launch maintenance on the primary
path. No new general trace validator or broad suite campaign.

Reviewer retains FINDING, current PLAN, RESEARCH-307667.json, this preparation
and review journals. Historical author artifacts remain immutable evidence.
This ownership supersedes the obsolete blanket clause assigning this entire
dossier to baton.claude. No edits to W306614-owned supervisor/tests/diagnostics,
W247941 accepted packet, frozen manager snapshots, installed images or DESIGN.
W306614 is separately routed for review as of snapshot307685; no claim transfer.

## Finite acceptance and implementation order

1. Correct admission/binding transaction boundaries while preserving original
   operation IDs/replay, qualification consumption, sole context use, original
   request operands and same-store compare-and-swap. Test open and restore,
   interrupted request replay, changed authority/profile/checkpoint/resource,
   competing admission, and qualification consumed between selection/commit.
   Observe external readers outside actual transactions, including exceptions;
   prove unrelated DB progress. Do not substitute cached unchecked booleans.
2. Connect existing public stage/driver paths with deterministic provider and
   engine boundaries: open -> save and exact stop -> independent review result
   -> changes-requested correction -> new attempt/token with same qualified
   conversation and checkpoint -> useful changed output -> independent review.
   Commit verdicts and correction through owner APIs, never inserted receipts.
   A deliberately defective simulated candidate must be labelled as such.
   Show exact runtime/token/use/generation attribution and zero duplicate dispatch
   across one selected interruption/replay. Preserve generation0 on failed save;
   unknown predecessor/launch remains held, wrong profile/competing use refuse,
   reviewers receive neither private context nor writable producer workspace.
3. Prepare digest-bound executable packet using accepted source/launch/stage
   machinery, exact fresh roots and explicit finite limits. No live setup now.
   Provider question: does the actual qualified CLI restore the original
   conversation in a new container and use real reviewer feedback to improve
   its retained candidate? Deterministic evidence cannot prove that CLI behavior.
   Packet states accepted/no-correction, rejected, failed/unknown and one-restore
   outcomes separately; no scripted reviewer disposition or automatic rerun.

Current DESIGN sections1,5,6,8,9,17,19 govern the whole path. Host preparation
finishes before task launch; no automatic helper/maintenance normalization gate.
The Sep27 FINDING/PLAN sentence requiring shared maintenance for every context
mutation is superseded for this primary path by the Sep28 DESIGN. Context save
and later consumption must preserve protected generations and exact exclusion;
failed context save is not successful reuse and is not proof a stopped runtime
is still running. Do not gate physical execution release on an output scan.
Do not weaken existing profile/credential inclusion or fabricate context success.

## Useful development Job to prepare, not execute

Prepare one documentation Job producing `docs/v12-context-correction.md` in a
fresh private development line from an owner-nominated immutable source/base.
Its utility is an operator guide for the newly connected restore workflow:
required eligible context/checkpoint and actual review feedback; fresh execution
identity versus retained conversation; supported command sequence; accepted
(no correction), changes-requested, rejected and failed-save/unknown handling;
exact cessation and honest result acceptance; no private state/credentials.
Give implementer and reviewer the SAME complete acceptance requirements.
Reviewer independently checks every command against the pinned supported CLI
and every claim against DESIGN/current implementation; all verdicts are valid.
Do not omit requirements to induce correction. No hidden acceptance criterion.
A genuine changes-requested result plus eligible saved context selects the
bounded correction input; acceptance ends this Job honestly without a restore
claim. No currently retained accepted subject qualifies. Owner must select the
final live subject/packet; another genuine correction can replace this proposed
Job only with explicit input selection. No automatic integration or Git mutation.

## Dependencies and limits

Existing W236087 -> W239533 dependency is satisfied; no new prerequisite is
needed to perform this bounded implementation. W247941 is closed satisfying
(as observed through W306614 detail). W306614 completion-stop/presentation fix
is independently owned, not a correctness prerequisite to these deterministic
context changes. Do not consume its moving candidate or reproduce its edits.
If a final executable packet actually needs that result, record the exact
consumer need and install a real dependency before consuming it; no speculative
all-work gate now. No graph edge was added in this preparation.

Return candidate, exact changed paths/digests, commands/durations and the finite
acceptance results to baton.bug. A new specification decision goes to owner;
routine implementation gaps remain with Tuner. Keep production restore explicitly
unproved until an independently reviewed owner-selected real run proves it.

Read positions: current work-events250440..307667 complete, T236087 through239616
complete (no later discussion/pending obligation); latest prior review
review-2026-09-23T19-33-41Z.md. Historical costs remain, no cumulative gate.
Operational search misses: guessed `v12/python/tools/episodes.py`,
`v12/python/tools/correction*.py`, and `worker_manager/control.py` did not exist.
Resolved actual modules to job_manager/episodes.py and worker_manager/store.py;
no required current file remained unreadable. Initial broad event/policy outputs
truncated; reread current event slice and relevant policy/spec sections.
