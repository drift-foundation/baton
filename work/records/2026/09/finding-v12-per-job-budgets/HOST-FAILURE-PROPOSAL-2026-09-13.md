# Proposed host no-status outcome extension

Prepared by baton.codex under claim157602 at2026-09-13T04:31:29Z.
**Proposed, awaiting owner disposition; this document grants no new source scope.**
The accepted per-invocation settings, defaults, signed delivery and deferred
cumulative/role pools remain unchanged. This is a correction to required host
verification failure handling, not a new retry policy or a live-provider question.

## Confirmed need and rejected shortcuts

Current `_ConfiguredExecution._run` cannot honestly return an integer child
status after TimeoutExpired or OSError. Returning null through the existing
observation shape is rejected before causal retention. Raising instead preserves
the diagnostic, but only a deployment-local memo prevents another child call.
That memo forgets on reopen, omits harness/result identity, and is checked after
scratch creation and materialization. The post-import owner call is outside
`execution._owned_post_import`'s hold handler, deliberately: a generic refusal
must not be reclassified or blocked a second time.

The causal owner executes combined, base, isolated in that order. A timeout in
the first or second step supplies no observations for the remaining steps. Merely
allowing null status in all three old records does not specify that partial
execution, and a nullable base status must never become the required nonzero
causal witness. Completed legacy integer observations must retain their exact
meaning and operation signatures.

## Recommended bounded behavior

1. Give the configured observation and post-import owners a separately tagged,
   closed failure answer for a test that produced no exit status. Keep the
   successful integer answer shape unchanged. Bind the failure to the owner
   participant, result/content/target basis, Job and integration attempt through
   the owner-held result, phase (combined/base/isolated/post-import), revision
   and tree, command, task/harness identity and digest, execution environment,
   applied host_verification seconds and a closed reason (timeout/start-failed).
   Retain safe textual detail; no guessed return code. Validate the boundary and
   bound against the owning Job where composed, not solely the incoming claim.
2. A causal failure answer records the completed prefix with its actual integer
   statuses, the one failed phase, and the phases not run. A not-run phase has
   no pretend execution/exit-status evidence. Validate the expected phase order,
   the same pinned harness and original/isolated/combined content bindings.
   Persist the answer and a reason under the existing integration result owner
   and settle blocked. Never publish, judge or authorize this failed result.
   The intended storage is the existing JSON observation custody plus its
   operation journal; any required store/schema expansion returns for explicit
   scope correction first. Existing successful observation signatures stay
   byte-compatible; failure signature and readback must agree on the new branch.
3. A post-import failure answer uses the same closed failure semantics with the
   imported content binding. Adopt it inside the current verification ownership
   boundary and persist a target hold through the existing queue capability,
   before any target-reference advance or integrated receipt. Preserve the
   generic owner-exception behavior and the protection against double blocking.
   A recorded failure replays its hold; it does not rerun a command on poll or
   reopening. Do not manufacture a runtime interruption for this host command.
4. Consult durable terminal failure custody before materialization or command
   execution on unchanged poll/reopen. Scope retention to the actual result and
   phase; two Jobs/results, different added harnesses on a shared base, and
   causal versus post-import execution do not reuse one another's outcome.
   Changes that need a new execution use existing explicit recovery/new-result
   mechanisms. The proposal does not promise crash-before-record exactly-once
   execution or introduce implicit retries.
5. State and test scratch ownership: dispose of temporary materialization after
   retained diagnostics no longer need it, or retain one explicitly owned path
   with an existing cleanup lifecycle. Repeated polls must not accumulate new
   paths. Whole-fixture teardown is not evidence of this runtime obligation.

Wire member spelling is an implementation detail to revalidate; the closed
variants, bindings, state effects, replay and legacy compatibility above are the
proposed acceptance contract. A broad nullable-status relaxation is not proposed.

## Exact scope requested

Add only these existing product paths to W156162's finite source ownership:

- `v12/python/src/baton_v12/integration/reconciliation.py`: observation answer
  validation, atomic failure custody/state and signature/readback/replay.
- `v12/python/src/baton_v12/integration/execution.py`: adopted post-import failure
  answer, existing target-hold account and repeat handling.

Compose the answer and cleanup in already-authorized
`v12/python/tools/stage_execution.py`; document it in already-authorized
`v12/python/DEPLOYMENT.md`. Add deterministic regression cases in the Work's
already-authorized new `v12/python/tests/tools/test_execution_limits.py`; reuse
real result/queue/store fixtures without weakening existing assertions. No other
product source, integration store migration or existing integration test edit
is included. If these paths cannot implement the contract, record the exact
additional seam before proposing another extension.

Focused acceptance: timeout and start-failed at each causal phase and
post-import; actual bound and failed/no-status identity; completed prefix and
not-run remainder; blocked/unpublished versus held/unadvanced target; repeated
tick and genuine closed/reopened owners cause zero new command/materialization;
different Job/result/harness/phase isolation; malformed/mismatched failure
refuses; recovery/cleanup; unchanged successful integer evidence and publication
authorization. Use injected subprocess faults with real coordination; no sleeps,
live providers or dependency installation. Preserve cumulative spending, including
unknown activities. No numeric verification-budget extension is requested.

## Independent work while disposition is pending

Finish composed read-only opening/observation/adoption/no-write/absent-artifact
coverage, distinct configured A/B serving/observation/reopen coverage, direct
and derived passing evidence reconciliation, and candidate provenance within
existing scope. The transient memo collision and scratch-repeat handling are
also within existing stage_execution scope. Do not repeat an unchanged broad
suite or present a limitation assertion as a completed durable failure test.

## 2026-09-13T05:32:04Z — current evidence clarification, proposal still pending

The opening paragraph's statements that the current memo omits harness/result
identity and checks after scratch creation are superseded as corrected by
review-2026-09-13T04-48-28Z.md. Its remaining lack of durable failure custody
still holds. No requested scope or recommended durable behavior changes here.

review-2026-09-13T05-32-04Z.md/repro-158025.py now measures original scratch at
BOTH real host boundaries with timeout and start failure: one invocation and
one scratch across four ticks, but the original path remains after composition
close. The memo stores only a diagnostic string, not an owned scratch locator.
Whole-fixture cleanup happens later and does not discharge recommended step5.
Both current post-import failures leave the result authorized and stage claimed,
with unchanged target reference. This is not the old status=None target-hold
candidate. M157653 remains pending; the observations grant no dependent scope.

## Disposition2026-09-13T09:19:44Z — approved

Owner159347 on T156162 approves this proposal and the exact five test updates in
PROVENANCE-REVIEW-158105.md, preserving bounded scope, independent review, W71879
provenance and spending, with no acceptance waiver. This explicitly supersedes
all pending/not-authorized wording above. FINDING pins the exact ruling and PLAN
tracks remaining implementation and review. The earlier baseline descriptions
remain historical observations, not claims about the current candidate.
