# Correction, provider-context adoption and counted reopen

2026-09-13T14:52:20Z — baton.codex, W161234 claim161434.
Research and proposed bounded plan only. No implementation or test authority.

## Confirmed scope and evidence reuse

Owner M161245 makes healthy same-line provider-context reuse REQUIRED. It
supersedes M161234's initial exclusion and any suggestion that fresh attempt
identities make provider conversation reuse impossible. M161269 requires final
project-pinned dependencies and actual-version recording. Dedicated capacities
are selected; operator substitution, shared slots, priority/random/TUI and live
cache benchmarking are outside this Work. Final managed import uses W161230.

Predecessor evidence remains at
baton:work/records/2026/09/finding-v12-deterministic-scheduler-stress/:
CONSOLIDATION-2026-09-13T14-10-03Z.md, matching independent review and
SELECTED-PLAN-161345.md. Reuse the independently accepted four imports in each
order, causal verifier/authorization records and18 valid exported schedules.
They contain no combined requested correction/reopen/provider-counter proof.
The accepted oracle is a starting point, not a reason to repeat all18 schedules.

Reuse W106673, baton:work/records/2026/09/finding-v12-live-session-workspace-detach/
review-2026-09-07T20-20-41Z.md: actual CLI conversation/workspace restoration
after confirmed old-container shutdown, useful multiply-by2→multiply-by3
correction, explicit --resume and changed process identity. That independent
review separately accepts retained-session evidence and explicitly excludes
production manager adoption/restart recovery and generalized cache/cost claims.
No new live experiment is needed to re-establish the value of reuse.

Canonical W105982 detail161437 is CLOSED satisfying. Its ruling accepts line
custody and retained-result/cleanup evidence but explicitly says production
confirmed shutdown remains and production detach is not adopted. Its PLAN has
older open-status wording; the canonical closure and dated ruling control.
This plan therefore proposes RESTORED conversation after positive shutdown,
not a live-process detach mechanism or a change to the consumption boundary.

## Current source baseline: observed, not newly executed

Paths below are under v12/python unless prefixed v12/worker.

| Source/helper | Confirmed behavior and consequence |
| --- | --- |
| tools/single_worker.py:_session_of, _adopted, _launch_document | Container exchange session is derived from attempt_id; current launch is adopted against manager-held facts and missing launch after start refuses. Preserve this fresh identity and refusal; it is not the provider conversation ID |
| worker_manager/sessions.py:open_agent_session, adopt_provider_session | Fresh attempt/posture/epoch binds an actual fixed live assignment. Provider ID is adopted once on that epoch, not rewritten. These owners can represent a new attempt referring to a continuing provider conversation, but do not implement its retention/delivery by themselves |
| sessions.py:handle_transport_loss | Unknown session plus recovery-required posture, resume=false/reprompt=false. Preserve this rule: healthy, completed correction is different from replaying an uncertain turn after lost transport |
| v12/worker/claude_agent.py:_provider, _prepared_home, _child_environments | Current closed argv is --print/--dangerously-skip-permissions/--output-format json; it has no --resume or --session-id. Home is prepared beneath per-turn scratch and points to the separately delivered credential. Successful provider output does not retain a conversation ID. This serving path has no production continuity contract |
| ClaudeAgent.work | The Git-line profile uses the mounted durable private repository as candidate at OUTPUT_ROOT; other profiles copy a candidate. Limit first adoption to this existing private-line profile with stable in-container cwd, rather than moving arbitrary workspaces |
| worker_manager/oci.py mount and delivery owners | Generic execution roots allow inputs/workspace and writable workspace only; specialized credential/launch delivery has its own checks. A new private context root is an explicit mount/custody extension, not an arbitrary third generic root or an existing capability assumed to work |
| tests/tools/test_stage_execution.py:turn, provider | turn invokes real baton_worker.serve_exchange and ClaudeAgent with a subprocess seam; the fake provider writes code, while real verifier subprocesses run. Use this normal provider boundary and count calls there, not a synthetic session row |
| test_scheduler_trace.py:test_a_correction_opens_a_second_episode_on_the_same_line | Real changes-requested verdict, settled review and routed new attempt are already correlated. The case stops at revised-attempt preparation; extend outcome proof in new cases |
| test_a_same_line_correction_keeps_its_worker_and_not_its_session | Records existing worker continuity and absent session adoption. Its claim of universal impossibility from attempt-keyed rows is too broad; preserve it as legacy-path evidence, not the new contract |
| test_the_composed_deployment_reopens_and_continues, launches_naming | Fresh composition over existing stores and nonzero engine launches keyed by input attempt, with duplicate-launch negative. Provider counts are absent. The boundary is manager recomposition, not host/power-loss recovery |

No source or test was edited or run to establish this baseline. Hashes:

| File | SHA256 |
| --- | --- |
| tools/single_worker.py | 3b78842c59a46b30a2a542cac6e7ed860e32c5e5645baed643c478a4eddd3c49 |
| tools/stage_execution.py | 02d83d92b6f9b0d44f42813239fb591b5d11fc13b35514665d5b4d36f6571d81 |
| src/baton_v12/worker_manager/sessions.py | bbbae52e65a99268c54b891578f4e9e9a731c337f0845c7b6c988aef5b0300dd |
| src/baton_v12/worker_manager/launch.py | d89159a36a40c383ba3e838b70e31eaa836b4e2d37b919e2020ef7b41e70e508 |
| src/baton_v12/worker_manager/oci.py | 68bb8831331ec1ac07b7b6bdb8a559573be348fe80ba796e50607d4b94af7b2f |
| src/baton_v12/worker_manager/schema.py | 56c54054b5170b49a77ef4af0b13dd7f8ff8ee14564785c449e726df48ed7df1 |
| v12/worker/claude_agent.py | c7a2b746fbefc088a7670c6f1a3c6363d0faeadcb08d27c56c8f6819ae0f979c |
| v12/worker/baton_worker.py | 85b48a2461e259f345ea9f984db4f2c522f83be943b40837882ce5c8241278dd |
| tests/tools/scheduler_trace.py | fa9e69f2df32b11cd2a830dc962900796e5aeb89398c50c5175d8e8e87ccf0d5 |
| tests/tools/test_scheduler_trace.py | a57c0a71e52629ee6008f054dccb1ef2d563bb886453b6bd8317daefe2437e17 |

## Proposed production adoption boundary

This is the exact missing product scope, not approved code and not a fixture
substitute. Independent design review must resolve the gates below before owner
selection of the first slice. The required outcome is already selected.

1. **One private provider context per healthy development line and actual actor.**
   New ControlStore context ownership binds Authority/Work/line/repository pin,
   participant/canonical principal, execution role, provider/model and certified
   context policy. Immutable context ID and provider conversation ID are separate
   from attempt, exchange session and AgentSession epoch. Bind each admitted use
   to the actual claim, writer generation, attempt, input and profile digest.
   One active or recovery-required use per context; concurrent admission refuses.
   Reviewer/other-Job/other-principal contexts cannot inherit this context.
2. **Durable custody and ending.** A trusted context owner creates a private
   provider-state root outside source/checkpoint/declared-output/verification
   roots. Retain opaque provider state through confirmed shutdown; no transcript
   is copied into ordinary result artifacts or public traces. Runtime credentials
   remain freshly delivered through the existing credential owner and never
   become retained context content or a copied home credential. Session-home
   layout, credential-link exclusion and cleanup ownership need exact review.
   Same-line correction admits the retained context only after the prior turn is
   complete, output collected and actual old execution positively excluded.
   Unknown turn/stop/custody state holds the context; missing state refuses reuse
   rather than silently starting fresh. Final line ending uses explicit retention
   policy and existing positive exclusion, never timeout-as-release.
3. **Existing lifecycle plus a specific context delivery.** Propose a manager-owned
   ContextDelivery capability with a fixed in-container target, admitted-use
   identity and type/ownership/mount validation. It is an explicit OCI exception
   only for the selected certified execution profile, not a widening of generic
   ROOT_NAMES or a reviewer mount. Ordinary workspace/credential/launch behavior
   still applies. A context-free legacy delivery stays its old schema; the selected
   reuse configuration requires context delivery and cannot omit it to opt out.
4. **Versioned binding and actual provider invocation.** Current launch versions
   are1/2/3. Propose a closed version4 for a Job launch with context-use identity,
   opening versus restoring mode and expected conversation identity. Preserve
   per-Job limit fields and all old-version readers; compare manager-held context
   facts during adopt, not values read from the delivery itself. Worker validates
   the fixed private mount and supplies --session-id for first use or --resume
   for later healthy use through ClaudeAgent's existing run boundary. Read only
   the bounded structured conversation identity/terminal status needed for this
   contract; do not expand diagnostic prose. A collected closed context receipt
   binds actual invocation identity to the admitted use. The manager records a
   fresh AgentSession through its real owner and adopts the observed provider ID.
   A profile certified only for a different adapter is not a valid shortcut.
5. **Provider environment is deliberately changed within this scope.** The current
   scratch-only provider-home validator cannot be bypassed by passing a new path.
   Add validation for the specific trusted context delivery, while keeping provider
   temporaries/cache and verifier HOME/temporaries freshly isolated. Review the
   exact provider-state layout and credential slot mapping before implementation.
   Fixed private-line OUTPUT_ROOT preserves the provider cwd contract. First
   adoption does not transfer a conversation across machines/providers or grant
   new access to a reviewer's snapshot.
6. **Reopen adopts, never repeats.** Persist use intent before delivery/start,
   invocation/result identity before scheduling a successor, and custody ending
   before reuse. Resume reads original operations and collected facts. No claim
   of an atomic transaction spanning ControlStore, Authority, engine and provider.
   An uncertain external turn is held for existing recovery, not re-prompted.
   W106673 proves provider restoration capability; deterministic testing here
   proves the production composition and decision boundaries, not cache savings.

The proposed new ContextStore relations belong in ControlStore's next additive
schema migration (current18; revalidate before selecting19). One context row plus
per-attempt uses avoids rewriting old session rows or making worker/principal
aliases. This is design scope; no migration number is reserved by this document.

## Finite slices, proposed paths and review gates

Each row is separately reviewable. Owner approval of one row is not authority
for the others. No path ownership starts now. Serialize shared source paths
against W161230 and revalidate its final candidate before dependent edits.

| Slice | Exact proposed product/test paths | Bounded finish |
| --- | --- | --- |
| A: context owner and custody contract | NEW src/baton_v12/worker_manager/provider_context.py; src/baton_v12/worker_manager/schema.py, store.py, documents.py; NEW tests/manager/test_provider_context.py | Journalled identity/use ownership, single-use/recovery exclusion, exact replay, coherent public observation, strict old/new compatibility; closed proposed delivery/receipt contracts with no runtime claim |
| B: normal serving restoration | NEW src/baton_v12/worker_manager/context_delivery.py; src/baton_v12/worker_manager/launch.py, oci.py; tools/single_worker.py, stage_execution.py; v12/worker/baton_worker.py, claude_agent.py; NEW tests/manager/test_provider_context_delivery.py, tests/manager/test_claude_context.py; DEPLOYMENT.md | Actual certified private-line configuration reaches versioned launch, validated private mount, provider open/resume argv and collected receipt; fresh session rows through existing public sessions owners; real correction reuse after positive stop, wrong-identity/role/missing-custody refusals |
| C: useful correction and counted reopen | NEW tests/tools/correction_restart_trace.py, tests/tools/test_correction_restart.py; dossier evidence | Two focused composed scenarios below, using existing scheduler_trace and test_stage_execution helpers. One coherent bundle with exact code/source/env hashes, owner evidence and provider/engine counters. Final managed imports through W161230 |

No sessions.py transition change, credentials.py credential-policy change, generic
exchange rewrite, production detach, source-boundary algorithm change or image
build/pull is proposed. If B cannot satisfy the selected contract without one,
return the exact missing boundary for scope review rather than hiding it in a
helper. No old test assertion is scheduled to change. All listed test files are
new additions; existing helpers/tests are imported unchanged, with new context-
aware fixture composition in the new tests. Historical gap cases remain accurately
legacy. If an old test actually needs mutation, name its exact method and changed
expectation in an amended plan before execution; the expired campaign exception
is not authority.

**Independent design gates before A/B:** choose exact bounded provider-state
layout/credential exclusion, certified profile and version4 member validation;
show one-use admission and stop-before-reuse across crash windows; map collection
of the closed context receipt through ordinary declared output without exporting
private state; preserve session transport-loss refusal; ensure integration and
review workers receive no producer context. Confirm the proposed paths suffice.
These are open implementation design questions, not permission to drop reuse.
Do not implement only the trace while leaving this adoption requirement unmet.

## Two proof scenarios and negative coverage

**Correction scenario:** use dedicated configured producer/reviewer capacity and
real owner operations. Initial provider turn writes a useful but review-rejected
implementation; the real review owner records changes-requested and routes the
fresh correction attempt on the same line. That attempt resumes the retained
provider conversation and writes changed code satisfying an independently
specified requirement. Run genuine verifier commands over the resulting bytes,
complete independent review and authorized managed import. Preserve original and
revised code hashes, attempts, episodes, checkpoints, verdicts, session epochs,
provider-context uses and result/import receipts. Prove the reviewer receives
neither producer context nor writable producer roots. A trace-label edit is not
the correction; a fake provider can write deterministic code, but the owners,
worker protocol, runtime seam, workspace, verifier and final effect are real.

**Reopen scenario:** after at least one actual deterministic provider invocation
has completed and its command/result is durably recorded, close/reopen manager
handles over the same stores; retain fake engine state independently of those
handles and optionally one unrelated live dedicated attempt. Continue the revised
turn/review/import through the reopened composition. Explicitly record this as
durable manager recomposition; do not claim process/power-loss recovery unless
separately implemented and proved. No crash-before-record exactly-once expansion.

At the ClaudeAgent run seam, record each actual provider call before returning
scripted output: admitted use/attempt, command identity, prompt digest, open/resume
mode, conversation identity and result. Require a positive baseline count before
reopen. At the fake engine seam, independently count actual launch inputs by
attempt/operation, also with a positive baseline. Runtime/session rows and unique
operation IDs are not substitutes for either count. A legitimate revised prompt
increments its own new-use counter once; reopening must not increment the old
use's call count or create another runtime for it.

Inject a duplicate provider call and duplicate engine start separately and require
the same counter/oracle to reject each. Additional negatives: forged correction
verdict, wrong old/new attempt or checkpoint, foreign reviewer principal/context,
unknown prior turn, missing retained state, competing context use, mismatched
provider/model/profile, and changed context receipt. Label synthetic negative
inputs as such, never execution evidence. Fake-provider memory is a simulation
of the boundary; correlate actual open/resume operands and custody, and cite the
existing live evidence separately rather than claiming live cache behavior.

The new companion artifact binds the unchanged scheduler trace by digest and
contains versioned invocation/custody observations with an independent validator.
Preserve meaningful operation IDs/generations and exact source/environment hashes.
Do not export private transcript/home content, credentials or remembered test
secrets. Keep100 logical ticks per scenario. Full original W103525 certification,
shared-slot capacity and later hardening remain unclaimed.

## Proposed verification spending and dependency handoff

W161234 measured verification starts and remains **0** in this planning claim.
No predecessor costs are reset or transferred. Proposed cumulative approvals,
to be selected separately after independent design review:

| Through slice | Author cap | Reviewer cap | Basis |
| --- | --- | --- | --- |
| A only | 120s | 30s | Focused temporary owner/constraint/replay cases; no engine/provider process |
| B, if later selected | 300s | 75s | Additional180s/45s for exact delivery/worker/provider-boundary deterministic cases |
| C, if later selected | 420s | 105s | Additional120s/30s for the two final scenarios, negative counters and independent bundle audit |

These numbers are proposals, not installed authority or fresh allowances per
turn. Persist each pre-command cap, fresh cumulative spend/remainder, expected
cost, margin and timeout; refuse if expected+margin cannot fit. Charge failures
and timeouts, use focused selectors, and preserve cost when returning incomplete
work. All verification uses project-pinned dependencies and records actual
versions; resolve the old jsonschema mismatch before final selected checks.
No live model, image installation/build/pull, farm run or broad suite is selected.

Next: record the mandatory W161230 dependency after preserving this planning
packet. It owns still-changing managed lifecycle/delivery interfaces and shared
paths. When ready, revalidate its final interfaces, obtain focused independent
DESIGN review of this packet, and then owner exact-slice/budget selection before
implementation. The dependency does not mark this unreviewed plan approved or
this Work completed. The reviewer retains current planning ownership; implementer
owns only the eventual explicitly accepted slice and PROGRESS while implementing.

W103525 retains author289runs1063.5077970099796/1200s, reviewer
141.8669683800224/300s, separate research0.2879257239692379s and historical
0.8047997559610849s overrun. W156162 retains its own recorded spending. No live
resources or private provider directories were opened. A few guessed worker/test
paths were absent and corrected with rg --files; no mandatory policy or bound
dossier was unreadable. Planning records only changed; no product/test/PROGRESS/
Git or environment mutation, and no test/probe/runtime execution.
