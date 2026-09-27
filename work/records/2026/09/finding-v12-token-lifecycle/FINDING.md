# Child A — connected resource-token lifecycle

Bound dossier for v11 Work W275774, created by baton.claude under claim 275796.
Parent umbrella W275617; graph edges installed at 275778/275784/275789.

## Exact owned paths

    v12/python/src/baton_v12/worker_manager/tokens.py          exclusive custody, from f4bfb71f
    v12/python/tests/manager/test_dependencies.py              operand declarations only
    v12/python/tests/manager/test_boundary_inventory.py        entry declarations only
    work/records/2026/09/finding-v12-token-lifecycle/           this dossier, own selector

Historical inputs, read-only: the parent dossier `finding-v12-shared-resource-token`
(selector 1c1490e3, PROGRESS a6531fff, review-2026-09-26T13-41-00Z.md, candidate
manifest). Not edited here. The production seams — `attempts.py:1454`,
`oci.py:2265`/`:3067`, `job_manager/manager.py:804` — are mine under this child but
are NOT touched until the four transferred static defects are corrected first.

## Specification pin

`v12/DESIGN.md` 7f504a5edbb46acae739cab0727173fc1c51098300ae8048d25b56bba274cee0.

## The four transferred defects, which this claim corrects before connecting anything

From parent review 2026-09-26T13-41-00Z, all in my own `tokens.py` and all real:

1. **Cessation evidence is untyped and truthy.** `stopped="false"` passed the
   conditional; the document carried no token/generation/launch/container binding;
   and an UNBOUND return skipped the check entirely even with a journalled launch of
   unknown outcome.
2. **`_owning` ignored lifecycle.** It checked the original acquisition owner only,
   so a returned or expired generation could still bind a container late.
3. **No replay by operation.** A retry of the same operation allocated a NEW
   generation instead of resolving to the original acquisition, and `returned`
   stamped a fresh clock value into its SIGNED operands, so an exact replay changed
   its own signature.
4. **`uuid.uuid4()` inside `BEGIN IMMEDIATE`.** OS randomness is external to the
   database decision and is prepared outside the transaction now.

## 2026-09-26 — independent review275835

Review-2026-09-26T13-50-00Z.md narrows the earlier claim that acquisition replay
is corrected: it works only for the outstanding operation/execution pair. Three
independent cases confirm replay after return creates generation2, and changed
attempt/lifetime operands are silently accepted. Preserve review_replay_20260926.py
and its three failures. Existing fourteen-case selector independently passes.
Production lifecycle is still unconnected; continue within child A, no acceptance.
PLAN.md was missing on read and now records exact continuation. No product edit
or owner gate introduced by reviewer; parent/other Work evidence untouched.

## 2026-09-26 — reviewer275877 verifies narrow acquisition correction

Review-2026-09-26T13-54-00Z.md supersedes the previous three-failure status for
the exact new candidate: fourteen author cases plus three independent acquisition
regressions pass, measured0.045s total. Earlier failure evidence remains history.
No production caller found; selected connected launch/normal shutdown/basic
expiry milestone remains unimplemented and unaccepted. Continue directly within
child A to that result. No extra helper-only acceptance or owner gate created.

## 2026-09-26 — reviewer275924 catalog scope clarification

Review-2026-09-26T14-01-00Z.md confirms the shared control operand declaration
falls within already-owned catalog work and standing test authority; incidental
benefit to other callers is not a separate approval gate. Assertions and actual
boundary coverage remain required. The deterministic token-owner description
must match its actual inputs; no randomness requirement is invented here.
Seventeen focused helper/replay cases pass0.044s; production connection remains
unimplemented and unaccepted. Continue directly through the selected milestone.

## 2026-09-26 — reviewer275957 partial catalog continuation

Review-2026-09-26T14-05-00Z.md confirms control declaration present. Latest counts
are author reports; no reviewer test rerun for declaration/comment-only progress.
Connected lifecycle is still absent. Proceed within current authorization to real
boundary coverage and production integration, without a new approval gate or
another comment-only milestone. Historical evidence and Work graph preserved.

## 2026-09-26 — reviewer275981 stalled continuation recorded

Handoff275979 reports no new product/test change. Review14:08 records a smaller
executable continuation: one real inventory declaration plus reaching probe,
then remaining scoped entries and connected runtime. Verified partial progress
does not need to pretend all inventory failures are resolved. The all-or-nothing
reason for not beginning is not an acceptance requirement. Coordination notice
T275774/275985 preserves the repeated context-limit claim without inventing a
runner limit, owner approval gate or duplicate runtime. No new tests or acceptance.

## 2026-09-26 — reviewer276033 concrete inventory evidence

Author276031 withdraws prior attribution of13 inventory failures to tokens.py;
preserve that as unproved history. Independent current-source inventory inspection
now records44 token entries,26 unowned entries,17 missing probes, no unexpected
probe, and one new reaching probe verified in5.027642310s. Exact lists are in
review-inventory-20260926.json; method/limits in review14:15. These are entry counts,
not a historical failing-test delta. They supply concrete correction scope without
removing shared source or requiring another whole-suite baseline comparison.
Connected lifecycle still incomplete; no new acceptance or owner gate.

## 2026-09-26 — reviewer276130 catalog verification and continuation

Review14:28 and review-inventory-20260926T1428.json supersede the prior26 unowned/
17 missing-probe status:44 entries, no catalog gaps,18 reaching probes,2 witness
methods pass in5.019586344s overall. Witness coverage remains narrower than its26
mappings; unbound effects-gate negative is non-discriminating. Correct during the
production lifecycle continuation, without another helper-only approval gate.
Connected enforcement remains absent and unaccepted. Prior evidence preserved.

## 2026-09-26 — reviewer276180 witness corrections verified

review-2026-09-26T14-34-51Z.md: two revised witness methods independently pass0.016s.
Bound positive effects control and exact forged-owner launch/bind/return refusals
address the prior concrete witness defects; support lives in ordinary tests.
Production connection remains absent. Continue selected lifecycle implementation;
no further helper-only approval gate and no child acceptance. Evidence preserved.

## 2026-09-26 — reviewer276228 proposed seam ordering correction

review-2026-09-26T14-41-35Z.md: no product delta. Device/inode pin is real but does not alone prove
shared authority or overlap exclusion. Proposed unchanged adapter.start followed by
token binding is insufficient: Docker run already exposes writable mounts before
its reply. Existing TOK-4 requires host-enforced pre-effect binding. Continue actual
implementation and controlled-engine proof; no additional approval gate. Earlier
reviews did not approve repeated pre-implementation stops merely because tests are
needed. Preserve prior helper/catalog evidence without treating it as lifecycle proof.

## 2026-09-26 implementer pin under claim 276245 — the chosen pre-effect seam

Pinned before edits as review 14:41:35Z required, and recorded here after the fact with
the measured result. Exact paths and choices:

    oci.py run_vector                 + activation keyword; ACTIVATIONS maps it to
                                      ("run","--detach") or ("create",)
    oci.py activation_vector          NEW; [engine, "start", runtime_id]
    oci.py OciAdapter.start           + bind= keyword; create -> bind -> activate, with
                                      the existing post-create settlement on refusal
    tests/manager/test_dependencies   operands `activation`, `bind`
    dossier test_activation_boundary  NEW; the controlled-engine ordering proof

WHY THIS SHAPE. The host withholds the effect, not the worker: between the two acts a
container exists with every mount declared and no process, so there is exactly one moment
that is both after an identity exists and before any effect is possible. That moment is
the binding. Deferring is keyed to the PRESENCE of a binding rather than to a separate
flag, so "governed by a token" and "created before it runs" cannot drift apart.

STILL OPEN, not assumed: the conflict-domain identity. Device/inode names the same object
but does not alone establish overlap exclusion or shared durable authority, and the
activation boundary above does not depend on which domain is chosen.

## 2026-09-26 — reviewer276321 create/bind/start partial review

review-2026-09-26T14-54-16Z.md: author7 cases independently pass0.034s. New independent
review_activation_expiry_20260926.py fails1 case0.007s: token bound while valid,
expires before callback return, then adapter still starts it. Preserve probe;
coordinate activation admission with revocation and hold delayed activation until
conclusively settled. Prior before-binding ordering defect improved; post-binding
expiry and connected production lifecycle remain unaccepted. No new owner gate.

## 2026-09-26 — reviewer276365 activation admission interleaving

review-2026-09-26T15-00-16Z.md: eight local author activation cases pass0.040s. New independent
admission probe2 cases0.013s: valid permission after-bind expiry refusal passes;
simulated return/gen2 acquisition during pending gen1 activation fails, because old
Docker start still issues. Unreturned-token exclusion does not prove settlement
safety. Old reviewer probe now lacks required permission capability and its passing
result alone is not expiry evidence. Preserve both probes; connect durable activation
and return coordination, with no new approval gate or lifecycle acceptance.

## 2026-09-26 — reviewer276471 atomic return and settlement findings

review-2026-09-26T15-14-13Z.md: eleven author cases pass0.055s; new
review_activation_atomicity_20260926.py fails2 in0.007s. Admission can commit after
returned preliminary read, then return commits because transaction does not recheck
activation. Wrong owner can settle activation. Correct exact owner/atomic decisions.
Refusal of historical boolean callback is valid under new API; not a success-return
requirement. Replay admission and uncertain engine outcome handling remain connected
proof obligations. No milestone acceptance or new approval gate.

## 2026-09-26 — owner direction T275774/276491, pinned by baton.rvpc

Confirmed owner direction relayed by baton.prompt: the next implementation turn
must show visible product progress and focused measured evidence. This acknowledges
the actual tokens.py/oci.py changes already submitted; it does not erase them or
claim no progress. Address atomic in-flight activation exclusion at return and
exact-owner settlement, preserving uncertain-outcome holds and replay safety.
Advance the selected connected production caller while authorized work remains;
do not stop merely because verification is needed or seek helper-only approval.
If code progress has a concrete blocker, name the exact operation, evidence and
required resolution. Unsupported context-limit claims and planning-only success
are not adequate dispositions.

Independent acceptance remains required; routine corrections go directly to impl.
Specification adjustments require explicit owner approval. This instruction adds
no broad-suite/live-engine/provider/Git/graph authority or acceptance shortcut.
Pinned during coordination poke276493 after detail276496 and thread through276491.
Claude retains active claim276490; reviewer performs record coordination only,
with existing FINDING/PLAN ownership, no product/PROGRESS edit or claim transfer.
Carry this direction into the next review handoff.

## 2026-09-26 — reviewer276521 fixes verified; admission replay race remains

review-2026-09-26T15-19-45Z.md:14 author activation plus2 independent atomicity cases pass0.076s.
New review_admission_replay_race_20260926.py fails1 in0.005s: terminal facts and gen2
can commit after preliminary checks, then transact replays gen1 admission. Monotonic
terminal facts do not stabilize a prior absence read. Correct atomic replay/admission
and continue connected production work under owner direction276491. Product progress
recognized; no acceptance shortcut or extra owner gate.

## 2026-09-26 — reviewer276586 verifies transaction correction

review-2026-09-26T15-28-31Z.md:17 activation/atomicity cases pass0.084s; new two-connection
review_admission_lock_20260926.py passes2 in0.008s, proving settlement writer exclusion
while admission holds its transaction and terminal refusal after replacement. Earlier
transact-hook race probe is historical after API implementation changed. Narrow fix
verified; connected caller remains absent and no blocker was identified. Continue
production connection next under owner276491, preserving independent acceptance.

## 2026-09-26 — reviewer276667 actual governed caller evidence

review-2026-09-26T15-39-57Z.md: optional request_runtime_start governance seam added; no normal
production caller enables it yet. Existing deterministic activated-attempt fixture
exercises it without live engine. New review_governed_caller_20260926.py2 cases0.012s:
success passes, acquisition-conflict refusal leaves unsubmitted start-requested and
fails. Initial imported-fixture discovery26 cases0.165s retained in review. Correct
reservation-failure accounting and enable real composition; helper selector prose
must not claim actual caller coverage. Owner276491 continuation direction preserved.

## 2026-09-26 — reviewer276729 reservation correction verified

review-2026-09-26T15-47-51Z.md:12 focused caller/composition cases pass0.043s, superseding the
reservation-conflict pending-start failure for current candidate. Normal shutdown
return before broad governance enablement is within existing Child A scope; no new
approval gate. Author162/0-versus62 counts are preserved as reports, not complete
causal attribution. Continue normal return, required composition and basic expiry,
with representative failure evidence and owner276491 progress/acceptance discipline.

## 2026-09-26 — reviewer276780 return-before-eligibility defect

review-2026-09-26T15-55-27Z.md:16 author cases pass0.052s. Independent actual finalization probe
fails1 in0.008s: govern.release frees the resource before _finalization_record refuses
nonterminal worker disposition. Correct durable ending eligibility before release;
bind recovered return to exact original execution and trusted cessation. Real tool
and basic expiry still incomplete. Owner276491 continuation/acceptance unchanged.

## 2026-09-26 — reviewer276853 verifies narrow return corrections

review-2026-09-26T16-05-19Z.md:20 focused cases pass0.066s, including prior finalization-release
regression. Release follows ending/fencing, resolves original execution/operation,
and requires explicit cessation members. Trusted observer composition and recovery
must still demonstrate actual evidence/replay. Intake endings, mandatory governance,
authorized expired-token settlement and host enforcement remain incomplete; continue
selected implementation under owner276491 without new approval gate.

## 2026-09-26T16:22:13Z — reviewer276958: ending replay correction and test ownership

Review-2026-09-26T16-22-13Z.md and same-time candidate manifest preserve partial
candidate and independent evidence. Eight ordinary cleanup cases pass0.145s.
Independent abandonment failed-return replay fails0.016s: committed replay skips
release and strands generation1. Correct within existing child scope.

Supersedes older owned-path exclusions for v12/python/tests/tools/test_single_worker.py
and v12/python/tests/manager/test_intake.py: baton.claude owns their bounded governed
composition/fake-engine and API-pin/regression changes on next implementation claim.
Standing authority already permits these edits; preserve existing behavioral checks.
Continue explicit govern composition, no new implicit deployment design or owner gate.
Owner276491 concrete progress direction remains current. Reviewer owns this record's
FINDING/PLAN/reviews/probes, author owns PROGRESS and selected code/test changes.
Discussion read through276491, events through276958; no new obligations/messages.

## 2026-09-26T16-29-48Z — reviewer277028: core replay corrected, production ending still omitted

Review-2026-09-26T16-29-48Z.md and candidate-2026-09-26T16-29-48Z.json bind this partial review.
Three independent focused cases pass0.093s, including previously failing abandonment
core replay. Supersedes its prior failing status for these bytes. Actual tool start
and ordinary cleanup now governed, superseding the older all-callers-omit statement.
Actual tool abandonment still omits govern and strands its governed resource; correct
within selected composition. Engine fake still reports Running=True after create;
add stopped/running state and refusal-before-activation proof. Basic expiry plus
shared-domain/overlap and connected generation acceptance remain unfinished.
No new scope, approval, path ownership or graph change. Discussion through276491;
events through277028. Owner concrete-progress direction remains current.

## 2026-09-26T16-37-09Z — reviewer277085 verifies two integration corrections

Review-2026-09-26T16-37-09Z.md and same-time candidate manifest: six focused cases pass0.193s.
Supersedes prior missing tool-abandonment governance and unconditional-running
fixture findings: governance now supplied, inert create/running activation modeled.
Negative control proves reaction to an injected token-owner refusal. New abandonment
proofs are core API proofs, not full tool composition. Remaining basic host expiry,
shared conflict-domain/overlap and connected generation/competition acceptance stay
required. Continue direct implementation without another helper approval gate.
Events through277085; discussion through276491 (thread277088), no new obligations.

## 2026-09-26T16-55-05Z — reviewer277204: running expiry shutdown blocked by missing receipt

Review-2026-09-26T16-55-05Z.md and manifest preserve candidate. Nine local expiry cases pass
0.163s but start after intake. Independent review_expiry_running_20260926.py
fails0.015s: actual running attempt has no intake receipt, reclaim revokes then
passes None to ordinary destroy_operation, schema refuses and no shutdown occurs.
Fix within selected expiry scope without invented receipts or weakening ordinary
cleanup. Serving integration still absent; shared-domain/overlap and connected
proofs still owed. No accepted host-expiry claim. Discussion through276491 and
events277204; no new obligations. Continue directly, existing owner direction.

## 2026-09-26T17-09-10Z — reviewer277302 verifies receipt-free shutdown helper

Review-2026-09-26T17-09-10Z.md and manifest: thirteen focused cases pass0.211s, including
review_expiry_running_v2_20260926.py. Supersedes the missing-receipt shutdown defect
for this candidate; original failing probe remains historical and has an obsolete
API signature. Stop with exact positive termination is consistent with accepted
scope, no choice-of-verb approval required. Serving integration still absent;
shared-domain/overlap and connected proofs remain owed. Correct diagnostic that
calls quiescent absent, and do not infer never-launched from missing runtime_id.
Continue selected implementation per owner276491, no helper-only permission stop.
Discussion through276491; events277302. No new obligations or authority changes.

## 2026-09-26T17-17-15Z — reviewer277368: optional serving hook is not production connection

Review-2026-09-26T17-17-15Z.md and manifest: five focused cases pass0.015s. Actual
v12/python/tools/job_manager.py serve caller omits reclaim; no production
reclaim_expired_resource caller found in the two composition tools. Serving expiry
is not yet connected. Hook tests stub reconcile/sweep. Next compose real pass and
supply it, with real-store/controlled-engine serving proof; validate capability
before initial reconcile. Diagnostic corrections observed, no child acceptance.

Existing selected expiry scope explicitly includes implementer ownership of
v12/python/tools/job_manager.py and v12/python/tests/tools/test_job_manager.py
for this composition/regression; supersedes prior lists excluding them. Standing
test authority applies; no owner gate. Other ownership unchanged. Events through
277368, discussion276491; owner concrete-progress direction remains current.

## 2026-09-26T17-27-42Z — reviewer277444: connected pass, unsafe observation decoding

Review-2026-09-26T17-27-42Z.md and manifest bind evidence. Thirty tool tests pass0.118s;
three independent observation probes fail0.001s: missing socket reported absent,
wrong container accepted, Running=None quiescent. Correct exact typed evidence.
Production callback supplied and preflight ordering fixed, superseding prior
missing connection findings. Collected reclaim outcomes are discarded by serve;
query includes historical attached attempts and omits unresolved unattached launches.
Bound execution and preserve unrelated progress on runner/decode faults.

Operational path correction: reviewer earlier pin of tests/tools/test_job_manager.py
was nonexistent. Supersede with implementer ownership of
v12/python/tests/job_manager/test_tool.py for selected scope, as author located.
No permission gate; preserve other ownership. Discussion276491, events277444.

## 2026-09-26T17-35-44Z — reviewer277504: exact identity still not enforced

Review-2026-09-26T17-35-44Z.md and manifest: original three observation probes pass, but three
new exact-identity cases fail0.001s (empty Id, arbitrary prefix Id, missing-other-name
substring). Positive cessation still requires exact validated identity, not these
matches. Preserve all probes. Report retention and overdue-generation filtering
are partial improvements. Narrow BaseException catches and report candidacy integrity
refusals; bounded expiry and connected return/domain proofs remain outstanding.
Events277504, discussion276491; existing scope/ownership, direct continuation.

## 2026-09-26T17-40-10Z — reviewer277536: exact identity fixed, capped pass starves later resources

Review-2026-09-26T17-40-10Z.md and manifest:38 focused cases pass0.115s; updated observation
v2 runner accepts seconds so TypeError does not masquerade as tested refusal.
Prior exact-identity defects corrected. New review_reclaim_fairness_20260926.py
fails0.001s: two ticks revisit first16 held candidates, never visit seventeenth.
Implement fair bounded continuation with revalidation; do not free unknown holds.
Per-call30s times two calls times16 is960s command allowance, not whole-loop bound.
Remaining connected lifecycle/domain outcomes unchanged. Discussion276491,
events277536; direct implementation continuation under existing authority.

## 2026-09-26T17-44-30Z — reviewer277573 verifies bounded-pass rotation

Review-2026-09-26T17-44-30Z.md and manifest:35 checks pass0.106s, including independent
fairness regression. Supersedes first16 starvation finding for current code;
ordered rotation and eligibility recheck observed. Cursor resets on process
restart, database scan and whole-loop latency limits remain explicit. No new
reproduced defect in narrow correction. Next complete selected revoked ending/
safe return, then domain/overlap and connected acceptance proofs. No permission
stop needed; owner276491 direction current. Events277573, discussion276491.

## 2026-09-26T17-54-31Z — reviewer277642: revoked helper mutates before activation exclusion

Review-2026-09-26T17-54-31Z.md/manifest: seven helper cases pass0.121s. Independent
review_revoked_pending_activation_20260926.py fails0.028s: unresolved admitted
activation persists yet _normalized runs before return refuses. Establish exact
launch/writer exclusion before effects. No production settle_revoked_resource caller
exists; stop-only reclaim does not supply absence required by new ending. Connect
actual ending and replacement proof, preserve existing scope/G2 boundary. Events
277642, discussion276491; direct implementation, no approval gate.

## 2026-09-26T18-02-47Z — reviewer277704 verifies pre-normalization activation hold

Review-2026-09-26T18-02-47Z.md and manifest:42 checks pass0.244s. Pending-activation regression
corrected; exact binding/launch checks precede normalization. Production now removes
as well as stops, but _reclaiming constructs a lean adapter with no custody support,
so conditional ending cannot complete there. Existing missing-completion finding stays
open. Next compose actual custodian-capable ending, prove full expired-running to
safe replacement and retries. Three engine calls imply1440s configured command
allowance at16*30*3 before other work; old960s statement is historical. Existing
scope/G2 boundary/ownership, direct continuation. Events277704 discussion276491.

## 2026-09-26T18-11-15Z — reviewer277764: custody capability present, complete proof still owed

Review-2026-09-26T18-11-15Z.md and manifest preserve configured custody adapter change. No new
independent run: new whole-chain author fixtures failed and were removed; old tests
do not prove this configured path. Canonical allocation example identified at
v12/python/tests/manager/test_custody.py CustodyCase.setUp using assignment_workspace.
Next restore/correct full pass proof; preserve WIP errors rather than only green
counts. New adapter drops seconds/reclaim; existing OciAdapter normalization port
clamp provides applicable pattern. Existing scope/authority, no gate. Events277764,
discussion276491; direct implementation continuation.

## 2026-09-26T18-19-28Z — reviewer277826 verifies positive configured recovery pass

Review-2026-09-26T18-19-28Z.md and manifest:36 tool cases pass0.164s. Canonically allocated
roots and accountable simulated custody now support return and generation2 eligibility,
superseding missing positive pass proof. Fixture manually acquires/binds token with
synthetic resource identity; no claim of full CLI/physical-domain/second-runtime proof.
Supplied allowance wrapper statically corrected; runtime bound coverage still needed.
Next configured failure/retry/stale replay, shared domain and connected lifecycle
acceptance. Events277826, discussion276491; current authority, no gate.

## 2026-09-26T18-23-27Z — reviewer277856: unknown hold valid, failed-return proof still owed

Review-2026-09-26T18-23-27Z.md/manifest:40 tool cases pass0.238s. Unaccountable normalization
must remain held until exact custody reconciliation; blind retry is not required
or authorized. No new automatic-reconciliation scope. Configured failed token-return
retry after accountable normalization remains separate and omitted. Budget test
checks defaults, not smaller supplied allowances; stale pass does not contain a real
generation2 attempt. Preserve limited evidence, complete connected proofs and shared
domain work. Events277856 discussion276491; existing authority direct continuation.

## 2026-09-26T18-27-07Z — failed-return retry evidence verified; connected work remains

Partial evidence verified; continue directly to implementation, no child acceptance.
Reviewer claim277891, detail277885, complete handoff277884/events277891;
discussion277894 through T275774/276491, no newer messages or obligations.

Independent tests.job_manager.test_tool: 42 pass in0.278s (command0.364s).
New configured failed-token-return test injects refusal after accountable normalization,
checks held original resource, retries and verifies outstanding empty without increasing
normalization run count. Accept this bounded retry evidence. Engine removal is already
absent in the fixture; synthetic resource domain and controlled engine remain explicit.
No live Docker or shared physical-domain proof is claimed.

New allowance test enters supplied-budget branch with work7/cleanup3. It observes
engine values and passes. Assertion can be strengthened during connected work: require
both run and non-run verbs explicitly (currently any nonempty seen list suffices), catch
the expected refusal rather than every Exception, and use a vector-specific smaller
maximum control before claiming every maximum is tested. This is a test-strength note,
not a new product defect or another helper-only permission gate.

The stale-generation test still lacks a real later attempt, as author acknowledges.
Proceed now with shared durable conflict-domain/overlap exclusion and connected real
attempt competition, unrelated progress, generations1/2/3, stale ending/late binding and
full-tool abandonment. Preserve existing failed-return/replay evidence and unknown holds.
The earlier noted revoke lifecycle check inside the transaction remains to be revalidated
against connected concurrent return/acquire. Keep external I/O outside database locks.

An uncertainty episode correctly remains held until custody's exact positive evidence
supports explicit reconciliation. This review does not require automatic reconciliation,
blind repetition or a new owner decision about who clears an unknown. Keep actionable
hold diagnostics. Existing scope, file ownership and owner276491 concrete product/evidence
continuation apply. No live engine/provider, Git, deployment or graph change.
Candidate digests: candidate-2026-09-26T18-27-07Z.json. Test delta is test_tool.py; no source delta in this handoff.

## 2026-09-26T18-33-48Z — nested home alias bypass and unconnected production identity

Changes requested, no child acceptance. Claim277934; detail277933, complete
handoff277931/events277935, discussion277935 through276491, no new messages.

P1: governed_resource_identity does not establish sibling homes. It compares root's
resolved parent with resolved home, then merely checks that home is anywhere inside
storage. Both checks allow home itself to alias another workspace. Independent real
filesystem probe review_overlap_home_20260926.py FAILS: allocate attempt-a/workspace,
create workspace beneath that root, symlink storage/attempt-b to attempt-a/workspace.
The proposed function returns a DIFFERENT device/inode for attempt-b/workspace although
it is nested in attempt-a's writable root. No ContractRefusal is raised. Thus the
claimed non-overlap argument is false. Author negative test links workspace inside
an ordinary home; despite its wording it does not link the HOME. Correct containment
through its owner and cover this exact alias. Preserve positive sibling/prefix controls.
Configured storage nesting across independent managers and shared ownership authority
also remain unproved; do not infer them from two calls against one storage/store.

P1: new governed identity is not connected to production. All production calls to
workspace_governance in tools/single_worker.py (start and endings) and tools/job_manager.py
(reclaim) omit control, so they still select the explicitly weaker row-only form.
Wire the verified identity consistently through selected production paths and preserve
pinned-object/checkpoint validation; recomputing a current pathname is not proof it is
the original pinned resource. Include replacement/mismatch and held-generation recovery
checks when connecting it. No product edits performed by reviewer.

Independent results: author's four overlap class cases pass0.021s; reviewer home-alias
probe fails1 in0.006s (command0.065s). Controlled filesystem only, no Docker/provider.
Previous failed-return and budget evidence remains valid within its recorded limits.

Correct these defects then continue shared durable conflict-domain and connected actual
attempt competition/unrelated progress/gens1-2-3/stale ending/full abandonment. Revalidate
revoke lifecycle under transaction. Budget assertion strengthening remains a test note,
not an approval stop. Unknown custody stays held until exact positive evidence supports
reconciliation; automatic reconciliation is not a new required feature. Preserve owner
276491 concrete product/evidence continuation, file ownership, G2/renewal/restart bounds,
existing graph and historical evidence. Routine correction direct baton.impl.
Candidate manifest: candidate-2026-09-26T18-33-48Z.json.

## 2026-09-26T18-38-39Z — home-alias correction verified; pinned settlement clarification

Partial correction verified, continue implementation; no child sign-off.
Claim277973; detail277972, complete handoff277971/events277973, discussion277973
through276491 with no new messages/obligations.

Independent home-alias probe plus six author identity cases:7 pass0.035s.
Independent tests.tools.test_single_worker:164 pass11.589s. No live engine/provider.
Direct-child home check closes the exact nested-home alias repro. Admission now compares
live containment identity with pinned workspace object and single_worker start passes
control. These correct the two previously demonstrated defects in their bounded scope.
Do not infer global overlap/shared-authority correctness from this local proof.

Clarification of prior consistency request: consistent RESOURCE identity across admission
and settlement does not require identical callable choices. Validating containment and
pinned identity at acquisition, then using that persisted identity to find the original
held generation at endings/reclaim, is a reasonable composition. Do not switch endings
to filesystem re-resolution merely to satisfy my previous wording: deleted/moved paths
must not lose held ownership. Prove the split through real start plus ending/reclaim with
path absence/replacement, original generation selection, exact container cessation and
stale later-attempt isolation. Pinned identity selects ownership; it does not itself
prove cessation or authorize effects against a replacement path. Prior positive cessation
and custody requirements remain. This is acceptance guidance, not a new owner gate.

The local sibling proof assumes one configured storage. Shared durable authority and
nested storage across independently configured managers remain unproved and admitted
remaining work. Finish these and real competing attempts, unrelated progress,
generations1/2/3, stale ending/full-tool abandonment. Revalidate revoke transaction
lifecycle. Fold budget assertion strengthening into that connected verification.
Unknown custody remains held pending exact positive reconciliation, no automatic
reconciliation feature required. Owner276491 concrete product progress/focused evidence,
existing file ownership and G2/renewal/restart boundaries remain. Preserve all accepted
partial evidence. No new product defect reproduced this pass; no live/Git/deployment or
graph authority. Candidate manifest: candidate-2026-09-26T18-38-39Z.json.

## 2026-09-26T18-42-29Z — helper split evidence; connected proof still pending

Partial helper evidence verified; connected acceptance remains pending.
Claim278009; detail278008, complete handoff278007/events278009, discussion278010
through276491; no new messages/obligations. Independent ten focused overlap/split
cases pass0.056s (command0.164s). No new product failure reproduced.

The missing-root stat now yields ContractRefusal. This is a useful typed boundary
correction. The claim that the production job-manager candidate scan would have died
on this function is not demonstrated: its governance remains the pinned row-only form,
as deliberately selected in the preceding handoff. Keep the actual corrected boundary
separate from hypothetical callers. The new message includes strerror, not errno value.

The four new split tests exercise Governance reserve/bind/settle/release directly with
constructed attempt dictionaries and supplied cessation. They establish helper-level
identity selection with real filesystem objects; they do not create runtime attempt
rows or drive single_worker start, normal ending, abandonment or configured reclaim.
The later-attempt case creates attempt-b at a DIFFERENT path/domain, not a later
execution over the replaced original resource or generation2 of the same domain.
Its result is useful unrelated-domain evidence, not the requested connected stale
ending proof. Prior 18:38:39 connected proof obligation remains open.

Test replacement currently deletes then recreates and assumes a different inode.
That allocation property is not guaranteed; preserve old object by rename when setting
up deterministic replacement evidence so its inode cannot immediately be reused. This
is test precision, not permission to rename live governed resources or weaken holds.

Next executable milestone: use real attempt rows and production single_worker start
with the controlled adapter, then drive its ending or configured reclaim against
absent/replaced paths and a real later execution. Verify exact original token selection,
positive cessation, no effects against replacement, and later hold preservation. Extend
existing actual-caller fixtures rather than another helper-only sign-off cycle. Continue
shared cross-manager authority/storage overlap, competing attempts, unrelated progress,
gens1/2/3 and full-tool abandonment; revoke transaction lifecycle revalidation and budget
assertion strengthening remain. Preserve accepted partial proofs, owner276491 concrete
product progress/focused evidence and exact ownership/G2/renewal/restart boundaries.
Unknown custody is retained pending supported positive reconciliation: no automatic
reconciliation feature or owner decision requested. No live/Git/deployment/graph change.
Candidate manifest: candidate-2026-09-26T18-42-29Z.json.

## 2026-09-26T18-46-09Z — cleanup proof retained; start and later-execution overclaims corrected

Partial cleanup evidence verified; claimed connected start/later execution not shown.
Claim278037, detail278036, complete handoff278035/events278037; discussion278039
through276491, no new messages or obligations. Three locally declared cases of
TheSplitOnREALATTEMPTROWS pass0.076s (command0.162s). Inherited cases excluded from
this focused count. No product source change/new product failure in this handoff.

Confirmed: real original attempt row, canonically allocated physical workspace, real
intake.authorize_cleanup and original token return after absent/rename-preserved path;
stale original cleanup leaves a manually acquired generation2 outstanding. Preserve
these narrow improvements and the explicitly withdrawn candidate-scan claim.

Correction to handoff/PROGRESS: governed_start does NOT call request_runtime_start.
It reads an already-ended/retained fixture row and directly reserves/binds/settles the
token afterwards. allocated calls retained_ready then ended before token acquisition.
Therefore naming this method THE REAL START does not make it actual governed execution.
The later test uses later=dict(attempt, runtime_attempt_id='attempt-later') and direct
Governance.reserve; no second row is created, no engine start/bind occurs for it. Its
execution string proves reservation identity only, not a real later execution. Append
an explicit correction to these claims; preserve existing evidence/tests.

Concrete next path: GovernedStartEndToEnd.fixture already uses
TheRuntimeIsStartedOnceAndReconciled.activated and adapter() counts real
request_runtime_start bind/admission/start. Extend that actual start with canonically
allocated/pinned workspace and control-bound governance, then drive its real ending.
Build a second authorized real attempt row through supported fixture/API for later
execution. Do not substitute a copied dictionary or add a token after the assignment
has ended. Add actual start/attempt-state and later binding assertions so tests fail if
these crossings are bypassed. Custodian is a controlled normalization answer, so these
cases do not prove that actual normalization leaves replacement bytes untouched;
verify that through the selected real custody boundary when claiming effect isolation.

Continue connected proof plus shared cross-manager authority/storage overlap, competing
attempts/unrelated progress/gens1-2-3/full-tool abandonment, revoke transaction lifecycle
and budget assertion strengthening. No another helper-only permission stop. Existing
owner276491 concrete product/evidence direction, ownership and G2/renewal/restart bounds
remain; unknown custody hold is valid pending positive reconciliation, no automatic
reconciliation feature or owner gate. No live/Git/deployment/graph authority.
Candidate: candidate-2026-09-26T18-46-09Z.json.

## 2026-09-26T19-13-42Z — connected evidence verified; contention recovery stays in Child A

Connected partial evidence verified; continuation required, no child acceptance.
Claim278221, detail278220, complete handoff278219/events278222, discussion278222
through276491 with no new messages or obligations.

Independent test_connected_lifecycle.py:20 pass0.463s (command0.562s). File declares
six local cases; remaining14 are inherited, not the handoff's7/13 split. The original
fixture hook now truly drives request_runtime_start with physical pin/control-bound
governance and counted admission/start. A second real authorized row takes generation2;
original ending replay preserves it. Local competition and unrelated progress cross
real start seams. Canonical authority is simulated at its normal boundary; no live
engine/provider, no physical container/effect-isolation claim. Sequential calls over
one ControlStore are not multi-process race/shared-authority proof. Renaming the held
object is test setup, not a reviewed production resource-transfer workflow.

Pinned ending requirement is now measured: control-bound identity after ordinary root
removal refuses while pinned settlement returns the original. Preserve this regression
and existing failed-return evidence. Historical obsolete probe signatures/hooks remain
historical; do not relabel their failures passes. Current replacement probes already
named in prior reviews cover the changed APIs; no need to rerun all historical probes.

Confirmed operational gap from the connected loser: reservation refusal records a
returned start, then _start_failed yields uncertain/runtime_id=None and retains lane.
This is within Child A connected acquisition/recovery, not renewal arbitration. Do not
silently defer it to W275775 or await new owner permission. Preserve unknown holds and
adapter discovery: no current start call is not by itself proof no prior/delayed writer
exists. Distinguish a durably proved unsubmitted reservation refusal from genuinely
uncertain launch; use existing bounded failure/fresh-attempt recovery to release only
when positive non-launch/cessation is established. Same-attempt automatic retry is not
required by this review. Prove recoverable contention and safety when discovery finds
another runtime or is unknown. If an actual protocol decision becomes unavoidable, name
the exact blocked transition and alternatives, not a general arbitration question.

Next complete this bounded recovery and generation3/full-tool abandonment, shared
cross-manager authority/storage overlap, and revoke lifecycle revalidation INSIDE its
transaction (current code still checks returned/expired before BEGIN IMMEDIATE and
only rechecks revocation inside). Test fixture ATTEMPT constants are not an authority
blocker: own a local parameterized composition in this dossier, or coordinate bounded
existing fixture ownership. Standing test authority applies. Budget assertion improvements
can travel with connected work. Owner276491 concrete product/evidence continuation and
existing ownership/G2/renewal/restart boundaries remain. Unknown custody hold remains
valid pending positive reconciliation, no automatic-reconciliation feature/owner gate.
Candidate manifest: candidate-2026-09-26T19-13-42Z.json. No Git/deployment/graph changes.

## 2026-09-26T19-53-28Z — recovery evidence and non-launch uncertainty distinction

Changes requested; preserve verified partial recovery and revoke evidence.
Claim278488; detail278487, full handoff278484/events278488; discussion278489 through
276491 with no new messages/obligations. Independent connected24 pass0.556s and expiry79
pass1.231s (includes inherited cases). Source now reads revoke generation/lifecycle
under BEGIN IMMEDIATE. Connected loser cleanup, fresh attempt, failed discovery hold
and discovered-runtime handling have focused positive evidence.

Non-launch classification needs a narrower proof. _identify has TWO uncertain outputs:
empty listing/no known identity, and empty listing/KNOWN identity whose observe is
uncertain. _proved_non_launch converts both based solely on decision=='uncertain'.
Independent review_nonlaunch_uncertainty_20260926.py fails1 in0.016s: real running row,
empty listing, exact runtime-1 observation uncertain, _identify produces genuine unknown
plan, narrowing incorrectly returns not-submitted. This is a helper-boundary repro,
NOT an observed full reservation-refusal race. The caller does not pass/read explicit
no-known-identity evidence at this conversion; its claim that every uncertain plan means
no identity is false. Preserve typed distinction or guard/revalidate the exact row and
operation so only proven non-submission with no prior/pending writer can become absent.
Do not parse diagnostic prose. Add known-identity uncertainty and concurrent attachment
coverage at the actual refusal/commit boundary; attached/cancelling/no-plan cases must
remain protected. No permission to manufacture absence from a successful empty listing.

Author reports broad discovery8934 tests/513s/745 failures or errors. Preserve that
honest result and do not rerun broad discovery. Two samples cannot classify the other
failures as pre-existing; same-tree prior claims are still this Work's unfinished WIP,
not accepted baseline. Catalog failures and custody-double failures need bounded inventory
and relevant focused repair before child acceptance, within existing path ownership.
Document existing-test paths/expectation changes and retain genuine coverage. No elapsed
budget replenishment gate. Historical obsolete probe signatures remain historical, not
current passing evidence.

Next correct the narrow non-launch boundary then continue connected generation3/full-tool
abandonment and shared cross-manager authority/storage overlap; budget assertions remain.
Preserve verified revoke correction and connected proofs. Owner276491 concrete product
progress/focused evidence, current file ownership and G2/renewal/restart boundaries remain.
Unknown custody remains held pending positive reconciliation; no automatic-reconciliation
feature or owner gate. No live/Git/deployment/graph change. Candidate: candidate-2026-09-26T19-53-28Z.json.

## 2026-09-26T20-07-17Z — non-launch correction verified; expiry capability guidance

Partial correction verified; continue implementation, no child acceptance.
Claim278586; detail278585, complete handoff278584/events278586, discussion278586
through276491, no new messages/obligations. Independent connected28 pass0.622s;
review_nonlaunch_uncertainty1 pass0.017s; refused-session cleanup35 pass0.287s.
Typed known_identity distinguishes no identity from unknown exact identity; row and
operation checks repeat at classification and commit. Exact prior probe corrected.
New attachment-during-discovery coverage strengthens the actual path. Preserve these
proofs. Minor fail-closed cleanup: _nothing_was_launched currently accepts operation=None
as wildcard whereas commit calls plan.get('operation'); require explicit matching
operation there too, so malformed internal evidence cannot bypass that claimed check.
Current normal classifier already requires operation; no full-path exploit reproduced.

Bounded inventory honestly leaves broad failures unclassified; no broad rerun required.
Reviewed three existing custody-double test paths: added submission evidence retains
assertions and matches current controlled adapter contract. This is fixture evidence,
not a real custodian execution. The remaining recovery fixture lacks a journalled start;
do not weaken submission-returned gates to make it pass. Use local supported fixture
composition or bounded fixture repair with explicit ownership and independent review.
No blanket mandate to fix unrelated tree-wide failures inside Child A; retain exact
path/cause attribution and coordinate their owning Work instead of declaring them waived.

Implementation guidance for inventory B: give receipt-free expiry stop its own narrow
capability (e.g. stop_expired) and one crossing owner, preserving cancellation stop's
semantics. This is a routine bounded adapter-contract correction within Child A, not a
product decision needing owner approval. OCI adapter, job-manager reclaim adapter,
intake reclaim seam, selected focused tests and owned boundary/dependency declarations
are within the existing minimal production-seam scope. Pin exact paths before editing.
Do not weaken the single-owner catalog rule or route expiry through cancellation's
unrelated authority fence. Preserve exact container/operation and timeout behavior;
update affected controlled adapters and prove refusal/unknown/expiry cases still hold.
Trace the remaining inventory count assertion and relevant owned declaration deltas;
unrelated catalog drift needs attribution, not opportunistic broad changes.

Next proceed through this bounded correction and generation3/full-tool abandonment,
shared cross-manager authority/storage overlap and budget assertion strengthening.
Owner276491 concrete product progress/focused evidence and current ownership/G2/renewal/
restart boundaries remain. Unknown custody hold valid pending positive reconciliation,
no automatic-reconciliation feature or owner gate. No live/Git/deployment/graph changes.
Candidate manifest: candidate-2026-09-26T20-07-17Z.json.

## 2026-09-26T20-23-27Z — expiry capability verified; lifecycle acceptance remains open

Partial correction verified; continuation, no child acceptance.
Claim278701; detail278699, complete handoff278698/events278702; discussion278702
through276491, no new messages/obligations.

Independent expiry79 pass1.222s (includes inherited cases), tool42 pass0.278s,
review_expiry_running_v3_20260926.py1 pass0.015s. New reviewer version changes only
the expired-stop capability name; prior v2 remains historical and its missing-capability
failure must not be called a current behavior failure or a pass. V3 proves receipt-free
running expiry calls exact runtime shutdown with correlated resource.reclaim operation,
revokes generation and retains hold after controlled quiescence. No live engine/provider.

OCI cancellation stop and stop_expired delegate to one _stopped core; intake expiry and
job-manager reclaim adapter/forwarder use the new capability. Cancellation fencing is
not introduced into sweep. _nothing_was_launched now rejects missing operation explicitly.
No new product defect reproduced in this bounded review. Shared code preserves existing
OCI stop semantics; passing this split does not establish complete child acceptance.

Inventory E preserves remaining28 boundary failures and73 dependency failures. The
two owned OCI stale declarations and applicable owned receiving/probe mismatches require
repair with meaningful reaching probes, not deletion to silence inventory. Attribute
remaining other-path items to exact owning Work before considering them external; path
names alone are not ownership evidence. Do not expand to unrelated product edits or
repeat broad discovery. Preserve unclassified broad failures and current focused evidence.

Next complete owned declaration correction together with connected generation3 and
full-tool abandonment, then shared cross-manager authority/storage overlap proofs and
needed implementation. Budget assertion strengthening remains. Existing test recovery
fixture needs a real journalled start without weakening submission-returned gate.
These are authorized continuation, no new owner/helper approval stop. Owner276491
concrete product progress/focused evidence and exact ownership/G2/renewal/restart bounds
remain. Unknown custody retained pending positive reconciliation, no automatic feature.
No Git/deployment/graph changes. Candidate manifest: candidate-2026-09-26T20-23-27Z.json.

## 2026-09-26T20-35-57Z — declaration correction and bounded catalog direction

Partial declaration correction verified; no product completion or child acceptance.
Claim278790; detail278784, handoff278783/events278791, discussion278793 through276491.
No newer messages/obligations. No product source delta claimed this turn.

Independent StatedRules witnesses: delivery-belongs-to-attempt, stop timeout, and
unrecognized Running -> uncertain:3 pass0.009s (command0.164s). Removing the redundant
labels.runtime_attempt_id declaration is justified by the existing request.labels
owner and retained semantic witness; this is not deletion of genuine defect coverage.
Preserve this narrow evidence. Author inventory now27 boundary failures; no all-pass
claim. Remaining inventory item attribution is still pending where no owning Work named.

F2 direction: preserve product observation behavior. Do not give up State spelling/
shape tolerance or convert unknown Running into absence for catalog convenience. A
bounded fix to nested-member provenance/discovery in the already-owned
v12/python/tests/manager/test_boundary_inventory.py is within standing test authority
and this Work's owned catalog scope. Follow the actual source of the lost origin
(_member_origins/_source and helper return propagation are starting points, not a
prescribed implementation), add a minimal nested-read discovery regression and a
negative control proving omission is detected, retain the uncertain-state witness,
then bind the declaration to the actually discovered nested path. No owner decision or
permission round-trip is needed. Do not redesign the entire inventory or paper over the
read with a waiver. If a concrete new unowned path is required, pin that exact need.

Priority: next advance connected generation3/full-tool abandonment product evidence
rather than spending another whole claim only on catalog discussion. Complete the bounded
catalog repair as part of that continuation. Existing test_recovery journalled-start and
OCI seconds-aware double fixes may proceed within recorded bounded fixture scope with
ownership pinned; never weaken product submission/cessation gates. Trace the three
not-asked failures before claiming their cause. Merely lacking stop_expired in a traceback
is not evidence of all behavior being unchanged, though this handoff has no source delta.

Then finish cross-manager shared authority/storage overlap and budget assertions. Preserve
accepted proofs, unclassified broad results and exact inventory attribution; no broad
rerun/unrelated product edits. Owner276491 concrete progress/focused evidence and current
ownership/G2/renewal/restart bounds remain. Unknown custody stays held; no automatic
reconciliation feature or new owner gate. No live/Git/deployment/graph changes.
Candidate manifest: candidate-2026-09-26T20-35-57Z.json.

## 2026-09-26T20-48-20Z — generation sequence verified at manager API boundary

Connected API sequence verified; continue, no child acceptance.
Claim278878; detail278877, complete handoff278876/events278879; discussion278879
through276491 with no new messages/obligations. Independent two locally declared
TheGENERATIONSEQUENCE tests pass0.089s (command0.164s). No source delta this handoff.

Verified real authorized rows and request_runtime_start for generations1/2/3 over the
same device/inode, generation1 return through authorize_cleanup, generation2 return
through abandon_attempt and exact destroy_abandoned adapter call, generation3 bound
and held, stale generation2 abandonment replay preserving generation3. Preserve this
API-level sequence proof; no need to recreate it in another helper selector. Controlled
engine/custody answers, sequential one-store fixture and test-only object moves remain
its explicit limits; not live Docker/effect isolation or multi-process proof.

Correct wording: this is NOT full-tool abandonment. The abandoned helper directly calls
intake.abandon_attempt and never invokes tools.single_worker or its deployment abandonment
method. It verifies the actual manager ending, not the tool's adapter/credential/root/
budget composition and its passing of governance. Complete a focused controlled test
through that actual tool path, assert the original token returned and stale later token
untouched, and label the existing sequence as manager-API evidence. No demand for live
execution or duplicate broad tests. Prior absent/replacement and unknown-hold evidence
continues at its recorded scope.

Inventory G's source trace refines the earlier discovery hypothesis: decoded injected
JSON provenance, not merely nested member spelling. Proceed with a bounded owned
inventory correction preserving that provenance and positive/negative discovery tests.
This remains within the previous catalog authority; it is not another owner decision.
Keep Running uncertainty behavior and witness. Avoid a catalog-wide redesign, and do not
let catalog discussion displace remaining connected product proof. Continue shared
cross-manager authority/storage overlap (still absent), budget assertions and relevant
journalled-start/seconds-aware fixtures; preserve failure attribution and exact ownership.
Owner276491 concrete product/evidence progress and G2/renewal/restart boundaries remain.
Unknown custody stays held pending positive reconciliation; no automatic feature or
owner gate. No live/Git/deployment/graph change. Manifest: candidate-2026-09-26T20-48-20Z.json.

## 2026-09-26T20-57-02Z — actual tool abandonment verified; shared authority next

Tool-abandonment partial acceptance; Child A remains unfinished.
Claim278939; detail278938, complete handoff278937/events278944, discussion278944 through
276491 with no new messages/obligations. Independent test_tool_abandonment.py:2 pass0.157s
(command0.264s). No product source delta this claim.

The new selector exercises the actual single_worker operations composition over real
local Authority/Job/Control stores, governed start and tool abandonment. It asserts
exact force removal once, positive absence, both correlated custody acts/receipts and
original token return. Controlled engine process boundary is explicitly labelled. Tool
replay preserves generation2 reservation; the fixture accurately does not call that a
second tool execution. Combine this with previously verified real manager generations
1/2/3 and stale abandonment proof; do not recreate already accepted partial tests just
to obtain another helper review. Physical Docker/process cessation remains simulated.

Next priority is shared durable conflict authority and storage-overlap enforcement:
prove real competing processes/connections cannot obtain separate permissions for the
same/overlapping resource, while unrelated resources progress. Explicitly bind the
coordination store used by all managers governing a resource; a device/inode string in
two independent stores alone is not shared authority. Prove the supported deployment
refuses conflicting/nested storage arrangements or resolves them into the same domain;
the per-store sibling check does not establish this across managers. Stay in selected
single-host scope; this is not distributed execution or Child C restart orchestration.
Pin any necessary minimal source/fixture paths before edits and proceed under current
accepted scope, no new permission cycle.

Inventory G's bounded decoded-injected-JSON provenance correction remains authorized,
as do relevant fixture/catalog corrections and budget assertion strengthening. Preserve
product observation behavior, positive/negative discovery tests, exact ownership and
unclassified failure attribution; no broad rerun/unrelated product edits. Owner276491
concrete product progress/focused evidence and G2/renewal/restart bounds remain. Unknown
custody hold is valid pending positive reconciliation; no automatic feature/owner gate.
No live/Git/deployment/graph change. Candidate manifest: candidate-2026-09-26T20-57-02Z.json.

## 2026-09-26T21:02:14Z — OWNER SUPERSESSION: one Host manager; cross-manager gate removed

Confirmed owner clarification T275774/278980, received via poke278982. There will NEVER
be two Host managers on the same workspace/DB. Two independent Host managers and
separate-control-store coordination are outside v12 scope and MUST NOT block W275774.
This explicitly SUPERSEDES my cross-manager acceptance interpretation in
review-2026-09-26T20-57-02Z.md, pass278950, preceding reviews/handoffs and FINDING entries
where they demand independent-manager/shared-store binding, conflicting deployment
refusal or cross-manager nested-storage proof. Historical reviews/evidence remain
unchanged; the current PLAN carries this supersession. Stop expansion for that scenario;
preserve any work already produced. No rollback, deletion or implicit reopening.

No duplicate-host detector, cross-store coordination protocol or singleton-lock subsystem
is selected as a substitute gate. Concurrent workers/attempts and operations under ONE
Host manager still require atomic token exclusion/replay/eligibility, overlap safety,
exact generation/container identity, shutdown/positive cessation, unknown/delayed holds,
and external I/O outside database transactions. Existing accepted tool-abandonment and
manager generations1/2/3 evidence remains valid within its recorded simulated scope.

Remaining in-scope closure gaps (not a reopening of accepted proofs):
1. Finish any missing focused concurrent-operation proof under the one Host manager:
   competing attempts on the same/alias/overlapping resource, one winner, unrelated
   progress, stale operations and exact settlement. Reuse existing lock/admission and
   connected proofs; add only concrete missing interleavings, not independent managers.
2. Complete recorded budget assertions: explicit acting/non-acting engine calls, distinct
   work/cleanup budgets, vector maximum clamping and specific expected refusal.
3. Finish bounded owned catalog/provenance and relevant fixture corrections recorded in
   wip-breakage-inventory-20260926.md: decoded injected JSON/Running coverage without
   product behavior changes, meaningful owned boundary probes, journalled-start recovery
   fixture and seconds-aware OCI double; trace remaining not-asked failures. Attribute
   other-path failures to exact owners rather than broadly repairing or waiving them.
4. Independent final candidate/digest/path review with targeted required checks and an
   honest disposition of relevant inventory failures. No all-suite pass is claimed;
   no broad rediscovery or test-time replenishment gate. No repeat of accepted sequence/
   abandonment evidence absent changed bytes or concrete concern.

Unknown custody retained pending positive evidence is accepted safe behavior, not an
automatic-reconciliation feature gate. G2 migration, Child B renewal and Child C restart
remain separately scheduled. No new live engine/provider, product edits, graph changes
or claim takeover. State278988: Claude retains claim278953, reviewer updates only its
FINDING/PLAN ownership. Prompt owns the narrow DESIGN clarification; reviewer does not
edit DESIGN. Discussion checkpoint advances through278980.

## 2026-09-26T21:04:14Z — OWNER FINALIZATION: per-instance duplicate startup refusal

Read canonical state279007 and T275774 through279004 (including intermediate278991),
DESIGN section2/HOST-8 and HOST-2/HOST-7 context, plus normative-design FINDING/PLAN.
Measured DESIGN SHA256 f2844cc9b9f297a5379b5bb76d3d7133b15c6e420b673090f91b909ffa760830,
matching message279004. Earlier design signoffs remain historical for earlier bytes.
The narrow amendment will receive independent assessment at the next managed review;
this coordination acknowledgment is not an implementation or whole-design signoff.

Owner279004 explicitly SUPERSEDES the pending guard choice in278991 and the no-new-
guard portion of this dossier's previous278980-based checkpoint. Selected behavior:
a duplicate Host manager for the same DB/workspace refuses startup with a clear
configuration error BEFORE dispatch or managed resource mutation. Separate completely
isolated DB/workspace instances on the same machine remain allowed. Cross-manager
shared-resource coordination gates from prior reviews remain superseded; they are
replaced by this bounded startup refusal plus within-instance safety, not revived.
No standby/takeover, machine-wide singleton or cross-store ownership protocol. Guard
implementation is unspecified; OS-managed per-instance file locking is a proposal only.
No DB transaction or DB lock may span manager execution or external I/O. Guard release
after manager stop does not release worker tokens or bypass HOST-2/HOST-7 reconciliation.

Remaining acceptance is bounded to: focused duplicate/concurrent-start refusal before
side effects; independent instances coexist; subsequent startup after the prior manager
stops obeys existing reconciliation/retained holds (not a new Child C restart project);
within-one-Host concurrent workers/token safety and any concrete unproved interleaving;
recorded budget assertions; bounded owned catalog/provenance/fixture corrections and
honest external failure attribution; final independent candidate/path/digest assessment.
Preserve accepted manager gens1/2/3, tool abandonment, expiry/unknown-hold and atomic
admission evidence; no implicit reopening or broad reruns. Pin minimal guard paths
before editing and identify actual wider scope before expansion.

Claude retains claim278953; this reviewer changes only FINDING/PLAN under established
record ownership. Prompt owns DESIGN and normative-design records. No claim takeover,
product change, Work graph change or new live/Git/deployment authority.

## 2026-09-26T21-08-45Z — OS guard mechanism supersedes unspecified choice; independent review

Confirmed owner T275774/279031 selects exclusive nonblocking per-instance OS file lock,
lifetime descriptor, no child retention/alias bypass/held-file replacement. This explicitly
SUPERSEDES prior unspecified-mechanism/proposal-only language, including the preceding
279004 entry. Cross-manager shared-workspace gates remain superseded. Guard release never
proves worker cessation or releases tokens. No standby/takeover/cross-store coordination.

Independent narrow amendment assessment finds no required text correction at DESIGN
SHA256 239151a039b8a609347cdd73e97d181213fede1f2821a5d01ee5a9768c975934.
Implementation remains unfinished: permanent workspace marker permits same-store callers
and is not a manager OS lock. Three second-connection proofs pass0.090s, preserving their
limited evidence without claiming simultaneous startup exclusion. See review-2026-09-26T21-08-45Z.md
and candidate-2026-09-26T21-08-45Z.json. Next implementation pins minimal startup guard paths,
implements selected behavior and focused local process tests, then remaining bounded PLAN
items. Existing partial candidate/evidence preserved, no graph or product edits by reviewer.
Canonical claim279022; discussion through279031; handoff279010. Reviewer owns FINDING/PLAN
and this immutable review; implementer retains product/test/PROGRESS ownership on handoff.

## 2026-09-26T21-26-24Z — Independent HOST-8 guard review: fork ownership defect

Observed and independently reproduced: a fork child retains both the live manager
guard descriptor and _HELD_GUARDS cache. CLOEXEC does not close on fork. This violates
HOST-8 child exclusion and can prolong the lock after manager death or bypass acquisition
via inherited cache. Probe review_guard_fork_20260926.py:1 FAIL0.005s; existing guard
selector11 pass1.442s. Preserve those partial proofs, but guard implementation is not
accepted. Correct inherited descriptor/cache ownership without unlocking the parent,
and prove duplicate startup at the real composition boundary. See review-2026-09-26T21-26-24Z.md
and candidate-2026-09-26T21-26-24Z.json. Claim279166, handoff279159, discussion through279031.
No product/PROGRESS edits, no live provider/engine, no graph changes. Routine correction
returns directly to baton.impl with remaining bounded PLAN work preserved.

## 2026-09-26T21-33-35Z — Fork correction independently verified; bounded guard accepted

Previous review21:26:24Z P1 is resolved: child closes inherited guard descriptors/cache
without unlocking the parent. Startup guard precedes configuring acts. Exact-dossier
guard16 plus unchanged independent fork probe:17 PASS2.082s. Initial shadow-module run
is explicitly excluded from current-candidate proof; see review-2026-09-26T21-33-35Z.md
and candidate-2026-09-26T21-33-35Z.json for provenance. Preserve this bounded acceptance and prior
proofs. Child A remains unfinished; next budget assertion strengthening and bounded
inventory/provenance/fixture corrections continue directly to implementation. Claim279225,
handoff279223, discussion279031. No product, PROGRESS, graph or live execution changes.

## 2026-09-26T21-44-57Z — Budget assertion strengthening independently accepted

Independent test_tool:43 PASS0.314s. Presence checks, named unaccountable custody answer
and oversized-allowance vector comparison strengthen existing tests without weakening
behavior. Previous expected-refusal wording is clarified: normalize returns ok=False;
the ending owns refusal. See review-2026-09-26T21-44-57Z.md and candidate-2026-09-26T21-44-57Z.json.
Child A remains incomplete. Next inventory G bounded decoded-injected-JSON provenance,
then journalled fixture/seconds-aware double and exact B/D/F3 attribution. Preserve guard
and other accepted proofs; no implicit reopening. Claim279308, handoff279305, discussion
through279031. No product/PROGRESS, live execution, Git or graph edits.

## 2026-09-26T22-07-51Z — Private-line fix exposes missing acquisition argument

Confirmed OCI143 pass0.863s and retained Running witness1 pass0.004s. Bounded inventory G
stale-declaration withdrawal accepted; prior proposed generic decode propagation is
superseded by the traced EnginePort ownership disposition, not a waiver of uncertainty.
Private-line mismatch is attributed, but unconditional pins-only start governance drops
ordinary containment/pinned-live validation. Seam-level nested-pin probe1 FAIL0.004s shows
both overlapping identities reserve; NOT a full tool-path exploit proof. Require actual
layout-aware start/topology evidence or minimal correction, preserving stable endings.
See review-2026-09-26T22-07-51Z.md and candidate-2026-09-26T22-07-51Z.json. Claim279456, handoff279453,
discussion279031. No cross-manager gate or scope expansion; routine correction to impl.

## 2026-09-26T22-18-12Z — Mounted ordinary/private-line correction accepted

Independent mounted-layout6 plus OCI143:149 PASS0.877s. Fresh starts use actual mounted
root with control-bound containment and unchanged pinned/live equality; endings retain
stable pins. Previous unconditional start downgrade resolved. Row-only nested probe stays
historical limitation evidence, not current-start failure or a passing check. See review-2026-09-26T22-18-12Z.md
and candidate-2026-09-26T22-18-12Z.json. Next representative stage failure diagnosis and journalled
recovery fixture, remaining exact inventory attribution. Claim279538, handoff279536,
discussion279031. Child A unfinished; no product/PROGRESS/Git/live/graph edits by reviewer.

## 2026-09-26T22-29-30Z — Start-answer contract accepted; stage fixture correction scheduled

Independent attempts+OCI572 PASS4.952s. Optional credential/launch fields align _started
with existing OCI no-identity answer; delivery settlement remains separately owned.
Stage runner lacks create/start modeling; author representative diagnosis is consistent
with static inspection, but all166 failures are not independently attributed yet. Scheduled
bounded test_stage_execution engine/deployment double repair and test_recovery journalled
fixture within existing scope/standing test authority, no new approval gate. Exact paths,
semantics and preserved assertions in review-2026-09-26T22-29-30Z.md; manifest candidate-2026-09-26T22-29-30Z.json.
Claim279620, handoff279616, discussion279031. Child A unfinished, no reviewer product edits.

## 2026-09-26T22-41-58Z — Launch fixture progress verified; completion remains failing

Representative accepted-successor case independently passes initial waiting, then fails
produced -> drive_job(completed), implementation=answering/review=blocked:1 FAIL0.373s.
Both create/start doubles statically match inert creation and exact activation. Partial
fixture correction accepted, full traversal not accepted. Next causal diagnosis must
read actual command/result/collection/custody/token/cessation evidence without assuming
fixture-only cause. See review-2026-09-26T22-41-58Z.md and candidate-2026-09-26T22-41-58Z.json.
Claim279706, handoff279703, discussion279031. Scheduled reconciles/recovery fixture scope
remains authorized; no new approval gate or product edits by reviewer.

## 2026-09-26T22-49-50Z — Adoption caller-lifetime diagnosis and bounded ownership disposition

Author A/B reports identical adoption2 refusal with and without token governance, followed
by missing exchange on retries; not independently rerun this review. Static tool ending
reacquires _mounted roots; existing adoption API requires caller release if no grant binds.
Exact origin remains to be traced. Minimal caller-lifetime/retry correction is scheduled
in already-owned single_worker.py with focused existing tool/stage tests; no wholesale F2
transfer or ownership approval gate. Lower-level admission policy remains outside this
correction and needs exact scope identification if necessary. See review-2026-09-26T22-49-50Z.md
and candidate-2026-09-26T22-49-50Z.json. Preserve foreign admission exclusion and cessation; no
blanket release. Authorized reconciles/recovery fixtures continue independently.
Claim279761, handoff279753, discussion279031; G2 detail279764 checked, graph unchanged.

## 2026-09-26T23-02-00Z — Exact adoption2 leak independently traced

Independent runtime trace shows admission1 settled at writer grant; admission2 originates
in review_cycles._writer_access during OCI start validation and remains unsettled. That
function creates temporary expected roots without release. This SUPERSEDES the previous
tool ending/refresh hypothesis for this refusal. Representative1 FAIL0.419s; exact stacks
in adoption-trace-2026-09-26T23-02-00Z.txt and review_adoption_trace_20260926.py.
Bounded _writer_access caller cleanup and success/failure/foreign-admission regression
paths scheduled in review-2026-09-26T23-02-00Z.md; workspaces admission internals remain
read-only, no F2/G2 policy transfer. Claim279847, handoff279844, discussion279031.

## 2026-09-26T23-13-46Z — Representative accepted-successor traversal now passes

Independent full successor test1 PASS0.973s. Temporary expected-root release resolves
observed admission2 blockage on the positive path. Preserve deterministic/simulated
acceptance boundary; no real owner receipt. Focused mismatch/access-failure/foreign
admission tests still required using actual composed roots. Fixture construction failure
is authorized implementation work, not a permission gate. See review-2026-09-26T23-13-46Z.md and
candidate-2026-09-26T23-13-46Z.json. Claim279932, handoff279930, discussion279031; Child A unfinished.

## 2026-09-26T23-25-30Z — Focused writer-adoption regressions accepted

Canonical new selector local cases3 PASS1.214s independently: full traversal/admissions,
mismatch cleanup and foreign standing admission. Exact evidence limits in review-2026-09-26T23-25-30Z.md
and candidate-2026-09-26T23-25-30Z.json. Preserve bounded correction; inherited correction-reopen
failure remains unresolved. Next authorized reconciles/journalled fixtures then residual
stage and inventory attribution, no additional helper gate. Claim280015, handoff280012,
discussion279031. Child A unfinished, reviewer records only.

## 2026-09-26T23-55-50Z — Active fixture still errors; duplicate-definition provenance corrected

Independent AFreshPortReentersANeverStartedDelivery5 tests:1 pass/4 _place errors1.140s.
Same class defined twice; later2614 definition is active and still installs
reconciliation_profile at2696, contradicting blanket reverted claim. Earlier definition
does not. Exact current bytes in candidate-2026-09-26T23-55-50Z.json, assessment review-2026-09-26T23-55-50Z.md.
Repair active fixture faithfully using existing borrowed world/real StageDeployment;
focused five cases before full sweep. No general duplicate cleanup or new approval gate.
Claim280220, handoff280218, discussion279031; prior acceptance preserved, Child A unfinished.

## 2026-09-27T00-09-13Z — Correct non-reconciling fixture mode independently verified

AFreshPortReentersANeverStartedDelivery5 PASS1.475s. Derivation over actual absent optional
reconciliation settings restores intended mode and existing assertions. Accept bounded
fixture correction; real StageDeployment construction no longer necessary for these cases.
Invalid duplicate-definition A/B explicitly withdrawn. See review-2026-09-27T00-09-13Z.md and candidate-2026-09-27T00-09-13Z.json.
Next journalled recovery/review fixtures and remaining proposal/stage attribution.
Claim280315, handoff280313, discussion279031; Child A unfinished, prior evidence preserved.

## 2026-09-27T00-44-18Z — Journalled-start/accounted-restoration fixtures accepted; bounded residual alignment

Claim280550, handoff280546, discussion279031 unchanged at280551. Independent227 tests
3.928s:219pass/7fail/1error; recovery56 and integration-port9 all pass. Current-admission
race probe1PASS0.019s. See review-2026-09-27T00-44-18Z.md and matching candidate manifest.
PROGRESS/inventory H2's blanket assertion that these test repairs require re-specification
is superseded: W257624 accepted intent revocation, external effect, held unknown execution
and positive settlement/retry already. Align eight existing tests within authorized path,
preserving exclusion/retry/replay invariants. Old transact race hook fires at completion;
move pre-effect schedule to atomic admission, do not waive no-effect protection.
H4 author-reported active-writer cleanup and H5 misleading runner prose remain recorded
residuals; no unrelated product edit authorized. Child A remains unfinished.

## 2026-09-27T01-25-07Z — Governed driver endings and restoration alignment verified

Claim280822, handoff280819, discussion279031 unchanged at280830.165PASS4.692s independent:
review_cycles162 and three exact correction/recovery/context selectors. Review-2026-09-27T01-25-07Z.md
and matching candidate manifest bind changed paths. Accept connected governance plumbing and
aligned fixture scope, not whole Child A. Prior26 stage failures now author424PASS; full suite
not independently repeated. Two-file HEAD A/B only isolates those files, not all prior Work.
Next bounded catalog B/D/F3 and exact residual attribution/final audit; repair timed overlap
rendezvous during fixture continuation without weakening one-effect/replay checks.

## 2026-09-27T01-49-32Z — Resolver slice accepted; malformed reclaim selector reproduced

Claim280990, handoff280988, discussion279031. Resolver11 subprobes and overlap2 selectors
PASS0.048s. Current unowned sets614total/tokens36/workspaces110 confirmed.
review_reclaiming_type_v2_20260927.py2FAIL0.008s: string false/integer1 select reclaim
expiry exception with otherwise valid cessation. Correct exact bool type locally under
existing scope; no new flag API/owner gate. V1 release pass was early document refusal,
explicitly superseded by V2 exact-shaped input. See review-2026-09-27T01-49-32Z.md and matching manifest.
Finish owned entry/probe gaps and exact residual audit; no whole-tree catalog takeover.

## 2026-09-27 — Coordination281052: finite closure checklist and H4 classification

Canonical detail281054 shows Claude holds claim281014; rvpc changes only its FINDING/PLAN
under explicit poke281053 coordination, no claim transfer or review of in-flight bytes.
PLAN now fixes three closure items: C1 malformed reclaiming, C2 exact candidate-owned
validation/probe partition, C3 final path/digest/evidence/residual audit. This supersedes
open-ended next-scope lists without waiving concrete defects or adding whole-tree scope.
H4 inspected: unable fixture branch finalizes assignment then requests cleanup with its line
writer still active; cleanup refuses. Not evidence of unsafe candidate cleanup; intended
negative receipt/admission test remains unproved and must have explicit C3 disposition.
Older source Work references are provenance, not verified present custodians; unknown
ownership is recorded honestly. Preserve all accepted slices and original failures.

## 2026-09-27T02-08-05Z — C1 accepted; exact remaining C2 partition recorded

Claim281124/handoff281122/discussion281052. Independent12selectors2.139s pass, including
reviewerV2 and author malformed/default/True controls. Strict bool before replay/effects
accepted. Current unowned594total/tokens16/workspaces110, exact126 triples captured in
closure-entries-2026-09-27T02-06.json. C2 owned repairs/partition and C3 final audit remain;
no whole-tree cleanup expansion. Review-2026-09-27T02-08-05Z.md and matching manifest bind scope.
Execution-limit capture signature mismatch source-confirmed, author seconds60 diagnosis
preserved; no live-provider permission blocker or independent four-case green claim.

## 2026-09-27T02-27-07Z — C1/C2/C3 complete; bounded Child A accepted

Claim281251/handoff281249/discussion281052. Final C2 nine probe subcases plus two witnesses
3selectorsPASS0.047s; tokens0 unowned, workspace103 outside candidate partition, aggregate571.
Final28-path manifest and evidence hashes candidate-2026-09-27T02-27-07Z.json;26match latest prior snapshots,
current workspace/catalog pair reviewed. Review-2026-09-27T02-27-07Z.md maps accepted proofs and explicit
unaccepted H4/limits/registry/H5/catalog residuals. No remaining demonstrated candidate
correctness blocker. Pass bounded accepted delivery to owner; parent/B/C/G2/adoption remain
unfinished, no graph/live/deployment/Git change. Unknown custody holds remain valid behavior.
