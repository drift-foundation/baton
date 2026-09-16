# Fence pre-attach assignments during explicit abandonment

Ledger Work: W63255

Follow-up to W55758,
`work/records/2026/08/finding-interrupted-dogfood-attempt-strands-runtime-credential/`.

## Observed — 2026-09-01

W61984 run3 committed and activated `baton.claude` generation 1, then refused
while reading a non-private credential-source registry. No credential bearer,
container or provider turn started. The documented dogfood `--abandon`
command returned exit 0 and wrote `resolved: true`, branch `pre-attach`, exact
runtime state `absent`, credentials `torn-down`, and no unresolved members.

The public v12 authority projection afterwards still reports the same Work
`active`, Handler `baton.claude`, live generation 1, and no fenced generation.
The recovery record's `authority_fence` is null. Evidence is retained under
`/tmp/w61984/run3/recovery.json` and the disposable authority beside it.

## Confirmed defect

A recovery cannot truthfully declare an activated attempt resolved while its
exact authority assignment remains live. Runtime absence and credential
teardown prove resources ended; they do not release assignment authority or
participant capacity.

This case is outside W61984's approved already-quiescent finalizer because the
worker disposition remains `none`. W61984 must continue to refuse that input.
The pre-attach abandonment path instead owns the explicit operator declaration
that this interrupted attempt is over.

## Direction

For a pre-attach attempt with a fixed live assignment, explicit abandonment
must fence/end that exact assignment through the public authority boundary and
record the fence before reporting `resolved`. A stale, mismatched or ambiguous
assignment refuses and remains unresolved. Exact retries replay; changed
attempt, assignment, generation or reason operands collide. The operation
still performs no output acceptance, retention, review or integration act.

Add a command-level regression that activates an assignment, fails before
runtime attachment, abandons it, then reads the public authority projection
and proves the Handler/live generation are gone and the exact generation is
fenced. A recovery that does not obtain that proof exits nonzero.

## Bounded workaround

Preserve run3. W61984 may continue with a new disposable authority and attempt
identity after correcting the credential-registry mode; never reuse run3 or
represent its still-live disposable assignment as recovered.

## Reviewer revalidation — 2026-09-01

**Confirmed root cause:** `_recovering` branches on the manager's atomic
`attempt_runtime_of` projection. When `runtime_id` is null it calls
`_pre_attach_recovered`, but that helper receives neither the authority port
nor the operator's abandonment reason. It proves runtime absence, tears down
credentials and launch material, and sets `resolved = True` solely from those
resource facts. No authority operation is reachable on that branch, so
`authority_fence` necessarily remains null.

The attached branch cannot simply be called instead. `abandon_attempt`
correctly requires a non-null attached runtime, an abandoned-runtime destroy
capability and directory custody; weakening those preconditions would turn a
no-runtime declaration into authorization for the W44716 runtime ending.
`request_cancellation` can fence an assignment with no runtime, but it requires
agent and runtime-stop capabilities and requests agent-session quiescence.
The documented pre-attach recovery owns none of those capabilities and must
not fabricate them.

**Confirmed reusable boundary:** the attached abandonment already has the
right declaration identity and authority crossing. `_abandon_intent` commits
or replays an intent keyed by the exact attempt and fixed assignment; its
signature carries runtime identity and reason, and `_abandon_fence_operation_id`
is distinct from ordinary cancellation. `AuthorityPort.cancel` proves the
authority fenced the exact four-member assignment. The correction should
factor and reuse these pieces, not call the session directly from the
deployment.

**Proposed correction:** add a public manager operation for pre-attach
abandonment fencing. It accepts only store, authority port, exact attempt and
the operator reason; requires the fixed assignment, matching participant,
`runtime_id is None`, `execution_runtime == not-started`, worker disposition
`none`, output `open` and nonterminal cleanup; commits the abandonment intent
and an in-flight no-start state atomically; then calls `AuthorityPort.cancel`
with the adopted intent's assignment, operation id and reason. Its closed
answer carries the intent and exact fence.

The atomic no-start state is required. Without it, a runtime start can commit
after the pre-attach projection but before the authority fence, leaving a
newly attached runtime on a branch that owns no agent/stop capability. If a
start already won, the pre-attach operation refuses without fencing and a
fresh recovery observation selects the attached branch. If the abandonment
intent won, `request_runtime_start` can no longer pass its `not-started`
precondition.

Only after the exact fence answer is recorded may the existing positive-
absence and credential/launch cleanup continue. `resolved` additionally
requires `authority_fence == {fenced: true, generation: <fixed generation>}`.
Replay uses the same intent and authority operation; a changed reason collides,
and a changed attempt or fixed assignment is not the same operation. This does
not accept output, settle custody, make a retention decision or invoke
W61984's terminal-disposition finalizer.

Detailed code paths, ordering, and regression matrix are in
`evidence/research-2026-09-01/README.md`.

## Approved direction — 2026-09-02

Approve the distinct public pre-attach abandonment fence described above. It
must reuse the durable abandonment intent and exact `AuthorityPort.cancel`
crossing, atomically establish a no-start state before fencing, and require the
recorded exact fence before recovery may report `resolved`. A runtime start
that wins first makes this branch refuse and forces fresh recovery observation.

Do not weaken attached abandonment, ordinary cancellation, or W61984's
terminal-disposition finalizer. This operation makes no output, custody,
retention, review or integration decision.

Implementation remains an isolated v12 assignment; this approval does not
route the Work to the legacy v11 implementer.

## 2026-09-14T11:40:26Z — supported recovery retained; fix selected for v12

Slawomir confirms: "I agree, keep the cmd and put in the fix". Keep the public
`--abandon` command supported and implement the approved pre-attach assignment
fence before minimum v12 release. This supersedes the pending correction-or-
release-surface-exclusion choice in W165782's release checklist and M167960:
exclusion is not the selected outcome. The 2026-09-02 technical direction stands.

Prompt revalidated the current dogfood_operator `_recovering` branch: it still
calls `_pre_attach_recovered` without the Authority port or abandonment reason.
The documented correction remains applicable; the implementing Handler must
revalidate the manager intent/start/fence composition against its current tree.
Use the existing W63255 identity and dossier. Implement through baton.impl,
then pass to baton.feat for independent review. Preserve W161230's active
assignment and serialize shared paths; this queues subsequent work rather than
interrupting the current implementation.

Use focused deterministic public-Authority/manager/command tests for the exact
fence, no-start race, replay/collision, crash recovery and truthful unresolved
results. Preserve attached abandonment, cancellation and W61984 finalizer
semantics. No broad suite, live model or engine execution is selected by this
ruling. Standing test-change authority and current per-run verification policy
apply. Record actual changed source/test paths in the implementation handoff.

The required W2-on-W63255 dependency and unpark act remain owner operations;
recorded selection alone does not claim either transition has occurred.

## 2026-09-15 — owner selects Claude implementation now

Slawomir agreed to start W63255 with Claude after the completed pre-work and file-overlap check, then prepare W61599's activity-source/transport design. This supersedes pending implementation scheduling above. W2 now canonically depends on W63255. The configured baton.impl Handler is authorized to unpark this Work and claim it before implementation; prompt neither claims it nor impersonates the operator. No unpark or claim is asserted by this text.

Use accepted advisory W174050, baton:work/records/2026/09/finding-v12-abandon-fence-prework/PREWORK.md SHA256 eb543aca3d5bb7604b978aedb3e3c3752309686ba7640b71074969b79888d6a3, together with this dossier's full evidence/research-2026-09-01/README.md and approved 2026-09-02 direction. Preserve the advisory closure correction: a winning start requires fresh observation and reconciliation or attached abandonment as actually applicable, never assumed attachment.

Selected source ownership: v12/python/src/baton_v12/worker_manager/intake.py and v12/python/tools/dogfood_operator.py. Selected test ownership: v12/python/tests/manager/test_attempts.py and v12/python/tests/tools/test_dogfood_operator.py. These four paths are absent from W170385's selected path set, including its preparation-output and scheduler amendments. Tuner retains that Work and its entire dossier. Revalidate current bytes and other active ownership at claim start. Factor shared intent/fence helpers without weakening attached abandonment, ordinary cancellation or W61984 finalization; do not expand into other owners without a concrete scoped finding.

Complete the exact fence/no-start/replay/positive-absence outcome and focused deterministic public-Authority/manager/command coverage, preserving existing evidence and recording actual changes and measured runs. No live engine/model or broad discovery is selected. Current standing test-change authority applies without per-test permission. Return a complete digest-bound candidate to baton.feat with set-next=baton.feat for independent review. No self-acceptance or release closure. After this implementation handoff, Claude may prepare W61599 design while review proceeds, without editing its product files until a design is selected.

Operational scheduling observation: prompt's asynchronous @ request on W63255 was refused because baton.prompt is not a resolved handler of baton.impl. No request or unpark was committed by that attempt. This is an authority-boundary refusal, not evidence of a Baton defect. The exact pending human operation is phase work=W63255 to=queued with the owner selection as reason. Plain discussion and the recorded selection do not themselves wake parked Work. No duplicate Work or alternate identity is used to bypass this boundary.

Scheduling correction: the suggested baton.slaw phase operation was also refused because phase requires the current baton.impl Route Handler. The preceding statement that an owner unpark command suffices is superseded. Claude is the configured Handler and can perform the selected scheduling transition under its own identity before claiming. Prompt will use the conversational participant poke to ask Claude about this parked authorized assignment; the poke conveys no new workflow authority. The authority is the existing owner selection and configured Route, and no successful transition is claimed until canonical state confirms it. This was prompt's incorrect command recommendation, not a product defect.

## 2026-09-15T03:05:11Z — independent review174362 requests completion

Candidate174231's four file hashes match;828 focused attempts/operator/finalizer
tests pass in8.220771550986683s, group ended without timeout/signals. This is
not acceptance of the required successful real-public-Authority pre-attach
command or crash/replay/race matrix. review-2026-09-15T03-05-11Z.md records the
exact gaps after inspecting bodies: ArcSession manufactures the fence, the new
command case expects unresolved/status1, equal fake retry replies do not prove
one durable Authority effect, and the new race covers only a seeded start state.
No reproduced new runtime defect is asserted from those missing tests.

The author-disclosed export at worker_manager/__init__.py lies outside the
explicit selected source paths. EXPORT-AMENDMENT-174362.md proposes only the
two import/__all__ entries; removing them in memory reproduces the accepted
W32577 base hashcd783420d73f237b9c8a01d63fbb1783a697efb3d87d211ed970a9994f0d5834.
Owner selection is the next action, then baton.impl completes already-selected
acceptance/provenance and returns baton.feat. No new per-test permission gate.
This supersedes awaiting-review/scheduling next actions, not the approved fence
direction. W63255/W2 remain open; PROGRESS remains the author's account.

## 2026-09-15 — owner selects the bounded export amendment (M174440)

Slawomir selected `EXPORT-AMENDMENT-174362.md`
(SHA-256 `a521e1fb53d3698d081570c4b6bfc13e619f42eac1e21c85082129b5c5800027`),
**limited to the two import/`__all__` entries** in
`v12/python/src/baton_v12/worker_manager/__init__.py` that export
`fence_pre_attach_abandonment` from `.intake`. All other bytes of that file
remain unchanged, and the pre-existing deadline imports/exports are inherited
from the accepted W32577 candidate rather than added here.

Accepted W32577 baseline: `cd783420d73f237b9c8a01d63fbb1783a697efb3d87d211ed970a9994f0d5834`,
14457 bytes, mode `0644`. Proposed:
`cce4b68650b5f73c0fa1b17f8ddb16f354c45c35df8e6f983594834307b36f29`,
14551 bytes, mode `0644`.

The selected source paths are therefore `worker_manager/intake.py`,
`tools/dogfood_operator.py` and — for those two entries only —
`worker_manager/__init__.py`. **No broader source expansion is selected.**
Per the amendment, `tests/manager/test_attempts.py` need not change merely to
fill a path list where equivalent substantive coverage lives in the selected
operator tests. No live engine or model execution is selected.

Remaining acceptance and provenance corrections are those in
`review-2026-09-15T03-05-11Z.md`; the corrected candidate returns to
`baton.feat` for independent review.

## 2026-09-15T03:24:46Z — partial correction and reviewer attribution correction

Claim174551 reviewed candidate174442; all four hashes/modes match, source bytes
unchanged from prior review, only operator-test assertions/comments changed.
The focused revised command case passes0.18554194798343815s, process group gone
without timeout/signals. Exact evidence in review-after-174551.json and
`review-2026-09-15T03-24-46Z.md`; no reviewer product/test edits.

**Explicit correction superseding03:05:11Z's fixture attribution:** the
documented command opens the disposable real v12 Authority through
_for_abandonment; ArcSession belongs to the separate direct-refusal helper,
not that cancellation crossing. The same-reason command retry also reopens
real owners. My previous review's fixed-reply attribution for these cases was
wrong. Existing records remain historical; this is the corrected interpretation.

New assertions prove a live Handler/participant slot becomes fenced/released
while an unresolved resource account retains the exact fence. They still expect
status1/resolved=false; the full defining successful pre-attach ending remains
unproved. The already-selected durable-effect/reason-collision, public race,
crash/fault/retry and non-effect matrix and full base/candidate/patch provenance
remain due. Extend the existing real fixtures rather than rebuilding them on a
false fake-Authority premise. No new reproduced product defect is asserted.

Owner174440 resolves the export path gate; no repeat approval is needed.
Return directly baton.impl for completion, then baton.feat. W63255 is unfinished
and W2 remains blocked. Author85.43121199202142s and prior reviewer8.220771550986683s
are preserved separately; this claim adds only the measured focused run above.

## 2026-09-15 — owner selects direct completion to reduce reviewer queue

Slawomir accepted the reviewer-throughput plan. Return W63255 directly to Claude
to finish the explicitly remaining selected work from handoff174630 and the
controlling reviews. The author reports real-Authority successful recovery,
positive fence validation and durable replay/collision in candidate174593; these
claims still need final independent acceptance. Complete both public start/fence
orders, intent/fence/cleanup interruption cuts, resource-refusal original-reason
retry, and wrong identity/participant/eligibility refusals with retained non-effects.
Keep exact base/candidate/patch provenance and reuse applicable existing evidence.
Return the complete selected outcome to baton.feat, or a concrete blocker that
requires a decision; known remaining authorized work is not a reason for another
partial review cycle. Existing source scope, export amendment and deterministic
verification authority stand. This changes scheduling, not acceptance or scope.

## 2026-09-15T04:00:41Z — review174815 verifies improvements; exact remainder

Candidate174768 hashes/sizes/modes match. Independent12 focused tests pass,
0.41381605999777094s, pinned Python3.13.7/jsonschema4.26.0, exit0/group gone.
Review `review-2026-09-15T04-00-41Z.md` verifies successful real-Authority command,
positive/exact fence guard, manager declaration replay, reason collision and
handled resource-refusal retry. These supersede their missing status only to
the extent stated in that review.

**Confirmed:** the reported public start-wins test still seeds its runtime axis;
the post-fence case handles a resource refusal rather than crashing immediately
after fence. One manager declaration does not count external Authority effects.
The complete-matrix claim is not accepted. Finish those selected proofs and map
internal eligibility/non-effects under existing authority. The shared fixed-
assignment guard already rejects changed generation/Authority/Work/participant
before either branch and passes independently; reuse it rather than duplicate it.

Retained checkpoint3700408c.../candidate snapshots and exact delta are current
reproducibility evidence, not invented original bases or import authority.
review-evidence-174815.json binds them. Reviewer measured8.820129558967892s;
author19 measured rows126.55034891501418s retained separately, unmeasured failed
attempts left unknown. No new product defect is inferred from missing coverage.
No reviewer product/test/PROGRESS/Git edits or live execution. Return directly
baton.impl for full authorized completion, then baton.feat; W63255 stays a W2 gate.

## 2026-09-15T04:13:11Z — review174914: two boundaries still need correction

Candidate174869 matches all four manifest paths; three sources unchanged.
Independent14 focused tests pass in0.46403919998556376s, group gone, bytes
unchanged. Exact review `review-2026-09-15T04-13-11Z.md` and
review-evidence-174914.json preserve provenance and scoped evidence.

**Confirmed source correction:** the new interruption at `_launch_after` occurs
after adapter.recover_credentials and orphan.tear_down. The author's claim of
interruption before any resource act is superseded; retain the actual later
cleanup/retry and real Authority operation-record evidence. Complete the
already-selected pre-resource cut with explicit zero-call assertions.

**Confirmed source map:** the ordinary fixture arc composes the input root and
passes it to the patched public start before the interruption. Capture/reuse
that operand for a genuine public start-wins transaction. The inputs=None
refusal is a fixture invocation issue, not a product defect or missing scope
authority. No owner decision to waive coverage or authorize fixture extension
is required. This supersedes the handoff's asserted decision blocker.

Step25's actual failing test is the Authority record check in the interruption
case, not the new intent-shape test. Keep step23 as disclosed no-op evidence.
Shared eligibility and retained non-effects are mapped in this review and need
no branch-only duplication. Return directly baton.impl under owner174746 for
the two concrete corrections, then complete independent review at baton.feat.
No new product defect or full outcome acceptance is asserted. W63255 gates W2.

Reviewer measured total9.284168758953456s; author23 measured rows
151.62043231201824s retained separately, historical unknowns preserved.
No reviewer source/test/PROGRESS/Git mutation or live execution.

## 2026-09-15T04:21:09Z — review174974 accepts crash proof; pending-start cut remains

Candidate174943 matches; only the selected operator test changed. Independent14
focused cases pass in0.4638527100032661s with unchanged bytes and group gone.
The post-fence interruption now precedes real resource recovery; orphan/launch
effects are excluded, the real Authority record and released slot are checked,
and retry succeeds. That acceptance gap is closed. Input-root capture and
step25 attribution correction are also accepted.

**Observed:** at the existing start case's fence call, public projections report
execution_runtime=uncertain, runtime_id=null and a failed-start record present.
review-start-state-174974.json records it. Ordinary RuntimeError runs the
manager's failed-start settlement before fencing, so a committed start operation
alone does not prove the required pending-start cut. The author's claim that
both remaining boundaries are closed is superseded to that exact extent.

Review `review-2026-09-15T04-21-09Z.md` specifies a direct BaseException cut at
the fake adapter entry and exact pending-state/no-failure-record assertions.
No new source scope, test permission or broad matrix is needed. Return directly
baton.impl under owner174746 for this one correction, then baton.feat. All
other accepted partial evidence and eligibility/non-effect mapping stand.
No new product defect is inferred. W63255 remains open and gates W2.

Reviewer measured total9.748021468956722s; author25 measured rows
164.13770943402778s remain separate, older unknowns retained. Evidence and
snapshots174974 bind this review. No reviewer product/test/PROGRESS/Git edits
or live provider/engine execution.

## 2026-09-15T04:26:43Z — review175026 accepts the selected technical outcome

Candidate175002 manifest SHA256b5da335d1bb98a27261cca1849b93e69e7d239675539b9b689861591843cd780
matches all four reviewed paths. The final test correction preserves the real
public start commit without ordinary failed-start settlement. Independent
public-state observation at the fence call confirms start-requested, runtime_id
null and no failed-start record;14 focused checks pass. The final pending-start
acceptance gap is closed. This explicitly supersedes prior changes-requested
statuses for this exact candidate, retaining all historical evidence/corrections.

Review `review-2026-09-15T04-26-43Z.md` binds the selected intent/axis/fence/
positive-resource outcome, current source/test hashes, source amendment and
reused focused acceptance. Step29's exact failure is the axis assertion before
the no-failure assertion; step23 remains no-op/non-evidence. No new product
change or broad/live certification is implied.

Pass baton.ops for owner disposition. Technical acceptance is not a canonical
Work close, W2 release, Git mutation or import over an unchecked target.
review-evidence-175026.json and snapshots/patch175026 preserve provenance.
New reviewer run0.46394639401114546s, measured reviewer total10.211967862967867s;
author28 measured rows185.04290029604454s separate, historical unknowns retained.
Exit0/group gone/candidate unchanged. No reviewer product/test/PROGRESS/Git edits.
