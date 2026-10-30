# W371076 — joined ordinary workflow proof proposal

Prepared by baton.codxpc under claim E383351, 2026-10-29. **Planning only;
awaiting independent review and selection of future proof implementation.**
The deliverable is one reusable deterministic test architecture, with an explicit
release-artifact extension. No executable proof, product change, build, install,
engine operation or provider invocation is claimed by this document.

## Selected inputs and revalidation

Current authority is this dossier's FINDING and PLAN after W383239, handoff
E383348 and discussion M383349. W371076's original whole-implementation waits
were removed for planning; they were not implementation acceptances. Parent
W370747 remains the joined delivery consumer. W370268/W321608 retain operational
adoption; this plan creates neither another authority nor an operational retry.

The following paths are relative to `baton:work/records/2026/10/` unless stated
otherwise. `evidence/claim-383351/SOURCES.json` binds current reference/source
bytes. Historical review digests remain evidence of their own candidates, not
automatic certification of today's shared working tree.

| Input | Current contract and evidence consumed |
| --- | --- |
| W371072 | `finding-v12-workflow-fragility-assessment/findings/finding-template-adapter-admission-plan/{FINDING,PROPOSAL,PLAN}.md`; E371253 selects template implementation-review/2, exact development-role-contract/1, capability/1, deployment/3, derivation/1 and resolution/2. Fresh-context task/2, git-line and the exact optional shared proposal/findings/logs declarations; role success remains mandatory. |
| W371073 | Sibling `finding-safe-adapter-failure-plan/AMENDMENT-376531.md`, E376465, supersedes the old compatibility/qualification platform. One current matched launch/5, terminal/2, diagnostic/2, status/8 and attempt-diagnostics/2 pair. Four safe declaration codes only; no new qualification ledger or legacy execution requirement. |
| W371075 | Sibling `finding-routine-startup-prerequisites-plan/JOINED-PROPOSAL.md`, its FINDING E375491 amendment and incorporated `finding-v12-queued-admission-contract-plan/PROPOSAL.md`. Fresh supported schemas, no migration/backward-compatibility gate. Shared direct/queued admission ledger, immutable selection, permanent retirement, publication fence, install prerequisites and instance-addressed observation. |
| W371074 | Sibling `finding-stopped-failed-settlement-plan/review-2026-10-28T21-40-29Z.md`: accepted source and 37 deterministic joined/core cases, 3.066790823s subprocess wall. Post-cessation settlement preserves output and Authority disposition; it is not a stop supervisor. |
| W370555 | `finding-v12-template-job-observation-identity/review-2026-10-28T02-38-50Z.md`: accepted source composition correction and independent stronger probe. No current packaged identity or whole workflow certification. |
| W370688 | `finding-v12-shared-output-template-preparation/review-2026-10-28T03-35-08Z.md`, inventory `INVENTORY-371277.json` SHA256 `00add5d1b3fba1ca655abbdff9640f4a20134bd05cb00803c9acb5e1b55bec38`: accepted f36bcd75 successor preparation. Actual role branches/collection were exercised with simulated provider/Git responses and deliberately invalid bundle bytes. operational_ready=false remains meaningful. |

**Observed current source, not a new acceptance:** role_contract.py and the
template/2 registry exist. creation.create_template_job still resolves inside
instance ownership and calls `_owned`; creation_ports.DeploymentDerivation._for_task
still requires whole installed-manifest agreement. No creation_admissions ledger
was found in the inspected creation/store files. The admission/queue integration
is therefore not established by the validator's presence. bootstrap.install now
calls prepare_prerequisites before selector publication and initializes the control
store through its owner: the older assessment's claim that none of this exists is
stale. Typed terminal/2 and launch/5 exist in worker/exchange; current Job documents
still name status/7, so complete typed public propagation remains pending.

**Observed harness gap:** tests/tools/test_joined_workflow.py uses scripted role
agents, synthetic transport, a fake checkpoint profile and fake creation ports.
test_connected_startup.py improves admission ownership but retains scripted agents,
fake checkpoint semantics and a stand-in package. test_packaged_creation.py reaches
the actual frozen command but explicitly never serves a Job. Reuse these focused
tests without promoting their union into a proof of the missing joins.

**Observed lifecycle seam to revalidate before execution:**
job_manager/review_driver._ended_review still invokes authorize_cleanup and gates
its successful return on cleanup, while stopped_settlement settles validated
faulted exchange after exact cessation independently of output. The selected
primary lifecycle forbids inventing mandatory helper/normalization/destruction
gates. The future proof must inspect the accepted final lifecycle candidate and
report any remaining mismatch to its owner; it must not patch the fixture to say
cleanup succeeded. W325695's existing runtime/source boundary ownership is not
transferred here. This source observation is not a claim that every caller executes
an unwanted destruction or that W371074 failed its narrower acceptance.

The current DESIGN also contains the newer W321608 LIM-5 selection: the first
documentation profile has zero corrections, 4800s stage, 9960s Job, 3600s provider
and 900s verification limits, plus separately reported bounded shutdown. This plan
does not override that profile to run a correction. The general one-correction
test below needs an explicitly selected test contract permitting one round. The
documentation-profile negative must instead retain changes-requested with no
successor. Aggregate-control execution is consumed from its accepted owner when
available, not newly assigned by this proof plan. No task/3, reuse or migration
expansion follows from the joined baseline.

## One reusable fixture, real owners

Propose a new focused test module and reusable fixture under v12/python/tests/tools
(working names test_ordinary_template_workflow.py and ordinary_workflow_fixture.py).
Names are suggestions, not an exclusive edit list. Keep tests outside this dossier;
retain execution evidence here or in the future bound proof Work. The fixture
accepts scenario data, an isolated installation root, the selected artifact tuple,
a bounded deterministic provider program, engine response schedule and fault cuts.
It must not implement admission, collection, review or settlement itself.

1. Prepare an immutable, small, **valid** source repository/object fixture with a
   known original base B, selected task/2, ordinary scope/acceptance and a harmless
   deterministic verification command. Use retained valid fixture bytes, not
   invented 40-character IDs or an invalid objects.bundle. Verify transport and
   object relationships with the actual source/profile consumers. Never run
   agent-issued mutating Git operations. If the real git-line product path requires
   private Git writes, the future execution selection must explicitly resolve that
   boundary under repository policy; this planning turn grants no exception. An
   existing certified isolated-worker selection may supply it only within its
   scope. In its absence, mark that proof blocked, not simulated-as-valid.
2. Use the supported bootstrap command into a new disposable destination. Real
   instance layout, prerequisite preparation, store initialization and selectors
   must run. No fixture-created control DB, root repair, patch of identity, direct
   table insertion or start-stop-create-start workaround may fill a missing product
   prerequisite. One-time fixture/package preparation is separate from routine
   input handling and is disclosed.
3. Start one instance manager using its normal guard and serve path. Submit the
   ordinary create argv with explicit template/2, task, source, scope, acceptance
   and allowed limits. Also cover first create before any serve. Real derivation,
   WorkAuthorization, NewJobBinding, creation ledger and publisher run; the CLI
   requests the operation rather than performing a duplicate precheck. Use exact
   final supported argument spelling once W375518 is accepted.
4. The engine boundary models create/start/inspect/stop replies for exact named
   objects and can delay or lose replies. It cannot write attempts, activation,
   cessation, token returns or cleanup records. The normal manager consumes those
   replies and owns its records. Dispatch runs the real file worker
   baton_worker.serve_exchange with the actual ClaudeAgent.work/_review role
   branches and current matched launch wrapper, in separate private role roots.
5. Substitute only the provider process invocation inside ClaudeAgent's normal
   subprocess boundary. Classify argv strictly: deterministic provider commands
   use the fake; source-driver and verification commands use their real authorized
   implementations, never canned Git answers. The provider may make a small
   candidate edit or write its review report in its own workspace because those
   are provider outputs, not Authority facts. Real adapter code observes the
   source, interprets the report, constructs role claims and measures output.
   Separate producer/reviewer principals and roots are mandatory even if both
   adapters use the same provider implementation.
6. Let normal serve/reconcile/sweep advance each stage. Real sealing/output
   validation/intake, retain_proposal, publish_candidate, checkpoint freeze,
   review attachment, review_verdict_from_result/record_verdict and open_correction
   must execute as selected. No fixture calls an ending with a supplied accepted
   verdict to skip result consumption. Stop at report-and-hold, without approval
   or integration. Invoke supported settlement separately for a fault after
   exact simulated engine cessation and after releasing the serve invocation
   guard through its normal lifecycle; do not bypass installed exclusion.

### Receipt and artifact ownership

| Fact/artifact | Sole producer in proof; fixture's permitted role |
| --- | --- |
| Request, source fixture, deterministic provider program | Fixture inputs, explicitly synthetic workload; no native receipt claim |
| Selected resolution/snapshot, admission/retirement and CREATE result | Job manager/creation owner through supported commands; read back using owner APIs |
| Authority Work/assignment/generation and candidate publication | Actual Authority API reached through authorization/publication ports; fixture never writes or substitutes receipts |
| Attempt/start/activation/token generation and runtime observation | Host/control owners interpreting engine replies; fake engine owns only its object response history |
| Command receipt, work history, terminal/2 and completion manifest | Real worker/exchange and adapter, correlated to real command; provider does not author these files |
| Candidate transport and verification evidence | Actual role adapter/source/verification drivers; source B, produced H1/H2 and bytes must be resolvable |
| Sealed result, intake receipt and retained proposal | Output/sealing/intake/integration owners, from actual files, not a manually constructed accepted digest |
| Frozen checkpoint and review attachment/verdict | review_cycles and review_driver from consumed candidate and measured review output; provider report is an untrusted input |
| Stopped failure intent, fence, outcome, exact token return and receipt | stopped_settlement.settle_stopped via installed command; fake must not set returned, cleanup or settled |
| Observation/report | observation_from, projection and attempt_diagnostics readers; no reconcile/renewal on reads |

Do not conflate native checkpoint verdicts, worker verification evidence and
Authority verification/review receipts. Report exactly which owning operation
produced each. Report-and-hold must expose the valid technical verdict and retained
proposal without minting owner approval, accepted-integration receipts or a changed
canonical target. If an Authority receipt is absent on this selected path, retain
and assert that absence; do not add a fixture receipt to satisfy an imagined gate.

## Identity and result oracle

Each scenario records authority UUID/full Work/assignment generation and principal;
Job/submission/request/snapshot/resolution/template identities; stage/round/episode;
attempt, launch operation, runtime, token domain/generation and command digest;
source base, candidate transport digest/head/tree, checkpoint, review attachment,
result and verdict IDs; exact image/adapter/profile/package provenance. Compare
typed owner reads, not equal local Job labels or trusted contents of launch.json.

Original B remains the admitted source. Implementation I1 produces H1 and
checkpoint C1; review R1 consumes C1 read-only with separately writable output.
For changes-requested, I2 receives the exact verdict plus retained correction
checkpoint, produces H2/C2 in the authorized serial line, and R2 independently
reviews C2. I1/I2/R1/R2, their runtime and token identities are fresh and distinct;
C1 and its verdict remain readable and byte-stable. R1 can never certify H2.
Compare common Job input projections across roles while preserving legitimate
different runtime manifests/capabilities. No writer may overlap review of its
mutable line. Fresh contexts are labelled fresh; no session-reuse claim is made.

The tuple of outcomes is always explicit: execution ceased or unknown; resource
returned or held; output valid/invalid/unavailable; technical verdict or absent;
Authority disposition; cleanup owed; owner acceptance; integration. A zero process
exit, returned token or optional generic output flag cannot substitute for any
other axis. Failure leaves the source/candidate/logs intact under retained ownership.

## Finite scenario matrix

Each row names a test family, not a cross-product or a broad stress campaign.
Component matrices remain owned by their existing Works; this adds the joins.

| ID | Trigger and exact joined oracle |
| --- | --- |
| J1 | Fresh install, first create before serve, then ordinary create while one manager serves. Valid template/2 reaches actual implementation then independent review, retains exact transport/checkpoint/verdict and reports-and-holds. No custom per-Job packet, no owner approval or integration. |
| J2 | R1 requests changes under a selected one-round test policy. Exactly I2 and fresh R2 run to completion; C1 survives, H2 differs, R2 binds C2. Replay does not open a third round. Under the selected zero-round documentation profile, the same verdict opens none. |
| J3 | Incompatible declarations/capability at create and drift before dispatch. Refuse before new effects at the appropriate boundary; no provider/container call for fresh incompatibility. For a defensive worker fault, separately deliver invalid declarations through the real worker boundary and label it as injected corruption, never as successful ordinary admission. Four selected codes/both roles reuse W376588 coverage; one representative fault traverses the full installed report/settlement join. |
| J4 | Provider raises an arbitrary exception or fails without a report; real worker emits safe generic fault with no verdict. Typed declaration cause appears only for the closed matched fault. Malicious secret-shaped values never appear in public diagnostics. Unknown/unsupported evidence is unavailable, not known-none. |
| J5 | Missing proposal; missing findings/logs; malformed report/duplicate claim; foreign checkpoint/attempt; altered retained bytes/transport. Actual semantic consumers refuse success even though shared declarations are optional. No review or dependent acceptance is fabricated; retain failed evidence. These are destructive mutations only to scenario-owned test output, never accepted repository evidence. |
| J6 | Faulted exact runtime stopped, then settlement-preview/settle-stopped/status. Preserve files and independent active Authority disposition; release only matching token generation and record failed outcome with no verdict. Running/unknown, unresolved create/start/activation, foreign runtime or actual surviving writer uncertainty retains hold. No stop/destroy/normalization is hidden in settlement. |
| J7 | Two distinct Jobs A/B share installed immutable package/source/configuration and eligible workers, with disjoint writable roots/contexts and distinct task/acceptance inputs. Hold A on a fault and let B complete with correct attribution; swap A/B result/launch/checkpoint evidence and require refusal. A later additive B binding must not reinterpret A. Serial runs prove isolation/reuse only. For concurrency claim, use barriers to demonstrate overlapping admissions/executions on distinct eligible lanes; one-lane serialization is not throughput evidence. |
| J8 | Observe/report repeatedly before dispatch, at receipt, during running/unknown, at failed output and after settlement. Compare owner application-state snapshots/schema versions and operation/effect counters; no claim, reconcile, acknowledgement, initialization, token renewal or repair. SQLite normal sidecars are allowed. Explicit instance plus matching environment works; conflicting/wrong instance refuses. |
| J9 | Same request replay, changed request collision, pending retirement versus claimant, direct call after retirement, wait timeout and configuration publication interruption. Consume W375519's full queue matrix; carry at least timeout-then-restart and additive second-Job replay through real role completion here. Request files removed after durable insertion cannot lose the owned request. |
| J10 | Measure full ordinary startup as below; delayed input/queue/validation, refusal before substantive work and lost timing continuity cannot be relabelled fast startup. Missing endpoint stays unknown. |

### Selected crash/replay cuts

Use real commits then lost-reply injection; discard process-local objects and
reopen stores/compose owners afresh. At least launch, worker receipt and correction
handoff also need a disposable subprocess restart cut to distinguish durable
recovery from a mock exception. Do not call injected exceptions OS-kill evidence.

| Cut | Required recovery |
| --- | --- |
| Admission snapshot/intent, authorization, binding half-publication, CREATE reply | Original full request and selected snapshot, same stable operation IDs; no new default resolution, duplicate Work/Job or loss of another Job binding. Unknown effect remains recovering. |
| Launch intent; engine create/start took effect but reply lost | Reconcile the exact engine object/operation. No duplicate runtime or conflicting token; unresolved possibility holds. |
| Command published; receipt persisted before provider; provider outcome lost | Same command replay does not invoke provider twice. A receipt without a terminal remains uncertain, not permission for a second turn. Count provider invocations outside product state. |
| Output partly published; seal/intake/publication committed but reply lost | Incomplete output cannot become valid. Committed owner outcomes replay against exact bytes; no fixture repairs a partial completion or manufactures an intake receipt. |
| C1 frozen; R1 verdict committed; correction selected but reply lost | Reopen exact attachment/verdict and open only one successor. Preserve old evidence, enforce stopped outgoing execution and independent R2. |
| Settlement intent, failed outcome, token return, receipt committed | Resume the exact original request. Before confirmed cessation hold; after return do not return again or require another runtime observation solely for receipt replay. Independent Authority closure/replacement must not affect old committed settlement or release replacement generation. Reuse W371074 cuts, add ordinary command/result context. |

At each external callback use transaction probes: no filesystem/engine/provider or
cross-store call while a DB transaction is held, including refusal/recovery paths.
Use a second real owner connection/process for race assertions, not fixture SQL.
Absence assertions use public owner readers; a missing reader is an operational
finding to fix through its owner, not permission to inspect the live v11 store.

## Timing, artifact tiers and remaining cost

t0 is one external monotonic reading before handing task text and selected file
paths/handles to the ordinary CLI, including process startup, file parsing, hashing,
configuration, queue and admission. t1 is the same harness clock receiving the
correlated signal from the deterministic provider's first actual task action, such
as opening the requested source; invocation, receipt, first stream byte or query
observed_at alone is insufficient. IPC delay is conservatively included. Record
Job/attempt/request correlation, clock continuity and raw endpoints. Do not reset
t0 at retry/manager restart. If continuity or t1 is missing, elapsed is unknown.
OBS-0 remains <=60s; it is not a new cancellation timeout. Injected delays must
appear in measured elapsed. Installation and pre-existing package/image assumptions
are separately itemized; request-specific preparation cannot move outside t0.

Source-level deterministic execution may use temporary selectors and a simulated
engine, but that evidence must say so. Final packaged deterministic proof must
select an actual independently reviewed matched frozen host/runtime and worker
artifact, check their hashes, run the installed argv with no source PYTHONPATH or
identity override, and reach the same real owners. A stand-in directory is not a
package. If ordinary packaged execution offers no safe deterministic seam, record
that concrete harness/release prerequisite; do not replace production owners with
monkeypatches and call it installed proof. New builds, operational installations,
real Docker and real models remain separately selected. Fake-engine results do
not establish kernel confinement or Docker latency, and fake providers do not
establish authentication, model quality or context reuse.

Reuse W371296 real-role qualification, W376588 matched diagnostic proof, W375519
startup/queue proof and W371074 settlement evidence after checking their final
candidate pins. Historical W370688 remains preparation only. No retained live
instance or prior packet is a test target. Pin exact commands, host/tool versions,
input/fixture/package/image hashes, provider/engine simulation, observed owner
states and effect counts, stdout/stderr redaction, per-run measured duration,
timeout and remaining limitations for each new run.

**Estimated future cost, not measured or an approval budget:** first focused
scenario runs should use 120s ceilings plus 30s termination/evidence reserve;
the finite source matrix can start with a 600s ceiling plus 60s reserve. Actual
package preparation is separately costed/selected. Tighten or revise per-run
timeouts from observed cost; do not silently repeat an entire suite after a
focused failure. Record every iteration and unknown historical totals honestly.
No runtime verification was spent by this planning Work (0s); an inert document
hash/link check is recorded separately. This plan does not claim a live <=60s
startup measurement or new 37-test execution.

## Proposed delivery order and handoff condition

1. Independently review this architecture and select the bounded future proof
   outcome. Keep the four existing delivery owners and canonical implementation
   gates; their approved proposals are enough for planning but not execution.
2. Revalidate accepted W371295/W371296, W376587/W376588, W375516–W375519 and
   W371074 candidates and the normal lifecycle consumer. Coordinate actual
   worker/tests/bootstrap/creation/stage overlap before any future edits. Do not
   duplicate their implementations here or infer permission from stale source pins.
3. One proof implementer owns the new reusable fixture and joined source cases;
   first deliver J1/J2/J5 with actual role/result boundaries, then J3/J4/J6 and
   replay cuts, then J7–J10 using the same fixture. These are finite milestones
   of one coupled harness, not parallel authors sharing it. Product defects go
   back to their owners; reviewer can decompose genuinely independent outcomes.
4. After source proof acceptance and separate artifact selection, extend the same
   evidence to the actual matched packaged command. Do not call source acceptance
   packaged qualification. W370747 consumes the joined result; W370268/W321608
   decide operational adoption separately. No graph changes are installed by prose.

No new product wire/schema or DESIGN change is proposed by this Work. The concrete
future selection must name valid Git-fixture execution authority, the one-correction
test policy distinct from the zero-correction documentation profile, and the exact
artifact tier. If those are not selected, preserve source planning without silently
substituting synthetic transport or relaxing the finite-control contract.

Planning acceptance requires complete owner/receipt mapping, this finite outcome
and replay matrix, honest current gaps and predecessor limits, and reviewed exact
document hashes. Future runtime acceptance requires every selected row to pass or
remain explicitly blocked with a concrete owner; skipping a missing package or
fabricating receipts cannot yield joined success. Independent review precedes any
completion disposition. Human Git checkpoint remains due after accepted planning;
suggested message: `docs: plan joined deterministic ordinary template workflow proof`.
