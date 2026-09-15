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
