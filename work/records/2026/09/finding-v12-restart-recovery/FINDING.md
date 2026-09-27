# Child C — restart recovery and integrated G1 acceptance

Bound dossier for v11 Work W275776, "V12 G1: Restart recovery and integrated acceptance".
Created by baton.claude on first execution, 2026-09-27, because owner 275776 requires a flat
permanent dossier bound and the paths pinned BEFORE any edit.

Parent umbrella W275617, which stays open and unaccepted until this integrated child is
accepted (graph edge 275789). Predecessors: W275774 (Child A, connected lifecycle) and
W275775 (Child B, renewal and expiry arbitration) are both CLOSED satisfying -- Child A at
seq 281287, Child B accepted by its final review 2026-09-27T03-31-52Z -- so their token
owner, their renewal/expiry arbitration and their accepted evidence are the input here and
are not reopened. Edge 275784 cleared at 284785.

## Authority and exact selection

Owner brief T275776 (seq 275776), read in full on claim 284804:

> Use accepted lifecycle and renewal; persisted overdue/uncertain-token reconciliation,
> delayed launch after restart, lost adapter replies, engine failure/recovery and unknown
> holds. Preserve effects and exact attribution; verify complete G1 lifecycle on actual
> connected path with controlled engine/fake provider, not isolated helper callbacks.

Excluded by the owner: consumer migrations, new scope, broad suites, live provider or engine,
deployment, cleanup, Git mutation.

## The governing specification, pinned by digest

    v12/DESIGN.md   239151a039b8a609347cdd73e97d181213fede1f2821a5d01ee5a9768c975934   61178 bytes

The requirements this Work must satisfy, read at that digest:

* **HOST-2.** "Host orchestration is persistent and recoverable. A restart reconciles the
  recorded attempt, token, launch operation, engine object, command receipt and custody
  state. It does not redispatch because its process-local map is empty. A healthy execution
  may be reattached only with exact matching evidence and current permission; an expired
  execution must follow TOK-6."
* **TOK-10.** Failed or unavailable Docker control leaves an actionable held state; the
  manager keeps trying the supported path and reports the exact unresolved execution.
  "Restart recovery processes overdue and uncertain tokens before admitting conflicts."
* **REC-3.** Every external-effect boundary has durable before/after intent and a defined
  recovery observation -- "before launch, after possible launch with lost reply, before
  dispatch, after receipt with unknown provider outcome, during freeze, during retention,
  after verdict, during handoff, and during cleanup" -- and the plan must show how restart
  resumes or HOLDS each cut without repeating an uncertain effect.
* **REC-4/REC-5.** Unknown is an actionable state with exact references, never a synonym for
  safe to retry; reattach only supported exact executions, and lost transport does not
  authorize a second provider turn.
* **Section 17 Recovery row.** "Manager restart at each selected external-effect cut
  preserves identities, unknowns and custody, with no duplicate container/provider dispatch."
* **DB-1 … DB-7** continue to apply.

If DESIGN.md changes this digest is stale and the pin must be re-read rather than assumed.

## Exact owned paths, pinned before editing

    v12/python/src/baton_v12/worker_manager/tokens.py        exclusive custody, from 73079b182348
    v12/python/tests/manager/test_boundary_inventory.py      entry declarations only
    v12/python/tests/manager/test_dependencies.py            operand declarations only
    work/records/2026/09/finding-v12-restart-recovery/       this dossier and its selectors

`tokens.py` custody passes from closed Child B with this pin. Everything else --
`attempts.py`, `intake.py`, `workspaces.py`, `oci.py`, `tools/job_manager.py`,
`tools/single_worker.py`, the job manager -- is READ-ONLY here unless a concrete gap is
found, reported and pinned first. No consumer migration is authorized. Child A's and Child
B's dossiers are read-only historical inputs; W270664 evidence is untouched.

## What the tree already has, measured before any edit

* **The connected path exists and is accepted.** Child A's `test_connected_lifecycle.py`
  drives `attempts.request_runtime_start` with control-bound governance over real rows and a
  real allocation, and Child A's final review accepted it. This Work reuses that shape for
  its own restart fixture rather than inventing a second composition; that file itself is
  historical and is not edited.
* **`attempts.reconcile_runtime`/`_identify`/`_reconciled` are the recovery observation** for
  a launch whose outcome this manager does not know, and `_identify`'s plans
  (`attached`/`cancel`/`uncertain`/`not-submitted`) are Child A's accepted work.
* **`intake.reclaim_expired_resource` and `intake.settle_revoked_resource`** are the expiry
  reclaim and its ending, and `tools/job_manager.py`'s tick drives them.
* **`tools/single_worker.py` has a real restart branch**: `Worker.start` settles from both
  live axes and `_recovered` adopts a published delivery only through the adapter's own live
  proof, with absence taking the orphan-teardown branch.
* **AND ONE THING THAT IS NOT THERE, measured rather than assumed.**
  `tools/job_manager.py:_governed_candidates` selects candidates by
  `governance.overdue(...) is not None` -- that is, by the token being OVERDUE. An attempt
  whose token is outstanding and NOT overdue but whose LAUNCH outcome is unresolved is
  therefore not a candidate for that pass, and no other caller in the tree reconciles it
  after a restart: `grep -rn "outstanding\b"` over `src/` and `tools/` finds no other
  consumer of the token's own outstanding set. TOK-10's "restart recovery processes overdue
  AND UNCERTAIN tokens before admitting conflicts" is the requirement that names this, and
  whether the gap is real on the connected path is this Work's first question rather than an
  assertion. It is recorded here as the question, with the exact line, and the answer will be
  measured before anything is changed.

## Residual debt inherited, NOT accepted and NOT this Work's scope

Child A's recorded residuals stand unaccepted and untouched: H4's missing negative coverage
in `tests/integration/test_driver.py`; the four `test_execution_limits` cases whose capture
wrapper omits `scratch`/`umask`; the sixteen unregistered parallel-runner modules; W257624's
optional-runner prose; the 103 unowned `workspaces.py` boundary entries and the tree-wide
aggregate. Child B's recorded residual stands too: no supported reconciliation clears a
timing-ambiguity hold, and no production consumer calls `renew`.

## 2026-09-27T11-35-53Z — independent partial review and wiring pin

Confirmed under claim284929/handoff284927: author49 PASS1.052s (seven new restart cases;
42 inherited executions). Production-pass reproduction review_restart_tick_20260927.py
FAIL0.016s: unexpired admitted/unsettled launch never reaches engine observation or refusal
report. The uncertain-recovery gap is NOT closed by tokens.unresolved alone; this explicitly
supersedes any interpretation of PROGRESS's measured-then-closed heading as product closure.

Operational finding: required PLAN.md absent at first review; reviewer creates current finite
checkpoint. Pin tools/job_manager.py and tests/job_manager/test_tool.py beneath v12/python
for the minimal connected recovery wiring/test milestone. This is existing selected Child C
uncertain-token recovery, not migration of a new consumer/resource domain. The prior read-only
rule allowed a concrete gap to be reported/pinned first, which this entry does. Implementer
owns these added paths on its next claim, subject to checking overlap; reviewer owns records.
Existing other scope/execution exclusions remain. Review-2026-09-27T11-35-53Z.md and matching
manifest provide exact evidence, limitations and R1-R4 closure. Ordinary continuation goes
straight to implementation; no new owner approval gate or graph change.

## 2026-09-27T11-45-17Z — R1 observation/retry milestone independently accepted

Claim285000/handoff284997/thread275776. Tool48 PASS0.392s and former production-gap probe
1 PASS0.016s. Actual pass now reports/retries uncertain engine observations for unexpired
unsettled launches and retains holds. No reattachment or integrated recovery claim follows.
Previous advice to compose list/observe is narrowed explicitly: do not weaken delivery-aware
identity/credential proofs to attach from the lean reclaim pass; observation/hold here is
accepted, and connected worker resume/hold remains R2/R3. Review-2026-09-27T11-45-17Z.md
and matching candidate manifest bind this partial acceptance. R2-R4 remain; direct impl
continuation, no new scope or owner gate. Historical row scan may repeat a domain observation;
no unique-candidate efficiency claim or broad performance task is selected.

## 2026-09-27T11-52-29Z — R2 partial coverage and attribution defect

Claim285050/handoff285048/thread275776. Tool50 and dossier99 PASS2.586s; controlled
report-attribution probe1 FAIL0.019s. Historical row over the same domain falsely supplies
its attached runtime to the current token owner report. Compare against held.execution's
actual owner, not whichever row discovered the resource. Exact reproduction and limits in
review-2026-09-27T11-52-29Z.md and matching manifest. This is correctness, superseding the
prior efficiency-only treatment for the newly added contradiction field.

Author assertion that different-container attachment is accepted design is NOT ratified:
observed behavior is not normative permission. R2 actual worker safe-resume/hold proof remains
and must establish exact authority without substituting token binding or falsely releasing.
No predecessor acceptance reopened, no new spec/graph scope. R2-R4 continue directly impl.

## 2026-09-27 — coordination285076, finite continuation and split criterion

Poke285078: canonical detail285079 shows Claude claim285064 active; thread read through
285076 at285080. Reviewer updates owned PLAN only, without taking Work execution or changing
claims. Next exact-owner report fix plus actual Worker.start persisted-cut proof; R3 selected
G1 evidence matrix alongside it. Prior REC-3 checklist is explicitly clarified as a mapping
reference, not new G2/consumer/provider scope. Preserve accepted slices and distinguish new
cases from inherited executions. No split now. Separable different ownership or an unbounded
milestone triggers a concrete child scope/paths/acceptance/graph proposal at a safe claim
boundary; no silent scope expansion or safety-defect deferral. Concrete spec decisions go
to owner; routine corrections need no new approval. PLAN records exact next steps and R4
umbrella checkpoint refresh under record ownership. No product or PROGRESS edits.

## 2026-09-27T12-00-40Z — attribution corrected; launched-unbound worker slice accepted

Claim285117/handoff285114/thread285076.57 checks PASS0.913s. Exact-owner report correction
accepted, and real composed-worker/fresh-store lost-create-reply path holds with one create,
zero activation, exceptional stage and no redispatch. R2 worker closure remains unaccepted
for bound-not-admitted/admitted-unsettled and conflicting-runtime worker response. The expiry
test accepts refusal without proving revocation or hold discharge; its non-permanent/reclaims
claim is not supported. Correct evidence precision, never force release of unknown custody.
Review-2026-09-27T12-00-40Z.md and matching manifest bind accepted slice and finite remaining
proofs. R3 selected-G1 matrix and R4 audit remain. No new ownership/split/spec gate.

## 2026-09-27T12-07-41Z — additional worker cuts accepted; mismatch premise unproved

Claim285170/handoff285168/thread285076. Worker7 PASS0.891s; new mismatch-premise wrapper
1 FAIL0.156s. Claimed connected mismatch report actually has only bound-ID absence and no
contradicts_binding; changed double ID has not been shown to reach the worker. This is an
evidence gap, not proof of unsafe product behavior. R2 requires actual conflicting-evidence
handling or exact safe pre-use refusal; do not force attachment. Bound/admitted restart cuts
and corrected expiry held outcome are accepted narrowly. MATRIX is inventory, not completed
R3: exact selectors/reviews and selected-G1 scope classification still required. Its proposed
B/C limitations are not assigned Work or newly selected clearing-API gates. See latest review
and matching manifest; R2/R3 then R4 continue within current scope, no split now.

## 2026-09-27T12-13-56Z — recorded-runtime mismatch safely refused; dispatch proof selected

Claim285220/handoff285217/thread285076. Worker8 executions PASS1.024s, seven distinct cases
because the old name aliases the repaired mismatch test. R2 exact recorded-runtime conflict
refusal independently accepted. Historical mismatch-premise probe expectation of an adopted
contradiction is explicitly superseded for this safe pre-use refusal scenario; never force
attachment to satisfy it. MATRIX's selected dispatch/unknown-reply row is next without another
approval gate, then R4 audit. Other REC-3 acts are not automatic G2 expansion. Exact matrix
reference/count corrections recorded in review-2026-09-27T12-13-56Z.md and manifest.

## 2026-09-27T12-20-22Z — publication boundary accepted; provider-effect cut remains

Claim285271/handoff285269/thread285076. Dispatch2 PASS0.244s. Both publication/reply-loss
cuts accepted, but they have no consumer/provider effect or receipt: zero republications is
not proof a consumer never repeats the one command. The previously selected unknown-provider-
outcome proof remains R3's one finite next milestone; exact applicable predecessor proof or
focused fake-provider effect/receipt interruption suffices. No product duplication asserted,
no live provider or new integration scope. Review-2026-09-27T12-20-22Z.md and manifest record
this acceptance limit; R1/R2 and publication slices preserved, R4 follows that remaining proof.

## 2026-09-27T12-28-08Z — receipt persistence accepted; effect-count claim rejected

Claim285335/handoff285333/thread285076. New selector2 PASS0.334s, but once-only case
manually consumes twice and asserts total effects==2. Fixture-induced repetition is not a
product defect; it is not one-effect acceptance evidence either. Receipt persistence and
working/no-terminal hold accepted narrowly. Connect a single recorder to actual invitation/
execution seam across resume, assert one effect/no reask or exact held unknown without false
success. Review-2026-09-27T12-28-08Z.md and manifest pin correction. Newly proposed terminal
while-manager-gone row is NOT added as a gate; complete this existing milestone then R4.

## 2026-09-27T12-37-13Z — bounded Child C accepted

Claim285386/handoff285377; discussion read through285076. R3 corrected recorder accepted;
reviewer exact pre-return receipt interruption passes. Author eight-tick pre-close case alone
does not prove receipt-unobserved timing; new reviewer probe supplies it. This explicitly
supersedes the outstanding R3 correction in prior checkpoint. R4 audit complete:24/28 latest
A/B paths unchanged, four reviewed C paths. See review-2026-09-27T12-37-13Z.md and matching manifest for evidence,
full limits and residual debt. Accepted G1 slices preserved; parent/G2 remain open.
