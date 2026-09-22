# Implementer progress

## 2026-09-22 — baton.codxpc, claim236092

Read current Work/events/T236087 and bound FINDING/PLAN, revalidated source and prior accepted recall review. Operational finding: PROGRESS.md did not exist (ENOENT), reported in M236105; initialized here without replacing another writer. Owner clarification M236120 received and pinned before edits. Exact source/test ownership and baseline recorded. No live, engine, deployment or Git mutations. Verification spending so far: 0 seconds; previous W177936 evidence/costs remain in its closed dossier.

Implementation in progress; independent review still required.

## 2026-09-22 — implementation prepared for independent review

Implemented M236120 in both contextual modes; non-contextual path untouched. Receipt `/3` retains requested model/session/status/provenance and carries actual optional model diagnostics plus exact provider bytes digest; historical `/1` and `/2` remain strict. Certification compares retained terminal bytes/diagnostics with the sealed `/3` receipt and rejects malformed/duplicate/nonfinite records. Profile `/2` resolves only the committed conversation UUID filename; `/1` remains literal. All prior stop/fence/cleanup/state checks stay intact. Documentation updated in the owned deployment manual section.

Focused deterministic proof uses the real candidate grant guard and ordinary manager/worker, review, custody and revised proposal paths with a simulated engine and provider subprocess. It establishes immutable first and second state generations, distinct use/HOME/attempt/invocation identities, original runtime removal before the next starts, revoked writers, delivered independent feedback, distinct retained proposal heads and final independent fixture acceptance. Missing/changed reported model labels succeed as diagnostics. Wrong session, foreign state filename, substituted result bytes, unsuccessful/incomplete terminal and uncertain cleanup refuse. Original stale-state/receipt, crash recovery and feedback-negative coverage remains passing.

Verification (process wall seconds including test-runner startup):
- verification-1: 6 tests, 3 harness capture errors, 2.991735890s. The worker streamed stdout to a file, so CompletedProcess.stdout was None; fixed fixture capture to retain exactly the emitted bytes. No product defect hidden or test expectation waived.
- verification-2: all 123 tests defined in the two affected manager modules passed, 30.201804568s; unrelated inherited test families excluded explicitly.
- verification-3: 34 final focused checks passed after profile compatibility refinement and additional managed proposal/state assertions, 16.668392159s.
- Total measured verification spending this Work: 49.861932617s. git diff --check clean; no broad suite/build/live provider/actual engine run. Existing W177936 costs remain in that dossier; they are not reset or absorbed here.

Candidate bytes/base hashes and exact six product/test/doc paths: CANDIDATE.json, BASELINE.json, candidate.diff. Repository base at packaging: 1e576ff2186db69e8b44da9d38874ff7e99ebbe3. No Git mutation. Review is requested through baton.bug, then baton.decide. Implementation is prepared; not independently accepted yet.

LIVE-CORRECTION-PROPOSAL.md gives the concrete next one-Job/one-correction workload, proposed bounds, existing serving command surface and exact acceptance evidence. The final executable live packet remains a post-review preparation step: refreshed artifact digests, selected deployment/authority/source/credential reference and bounded owner supervisor are not fabricated or claimed ready. No live run, installation, automatic production certification/enabling or broad rollout occurred. W177936 remains closed.

## 2026-09-22 — baton.claude, claim 236349, packet preparation (partial)

Owner transferred preparation from Codx (credits exhausted) to Claude at seq 236345. Claimed 236349 after reading current Work state, the complete work-events handoff and all four T236087 messages. Codx's released claim 236300 left no durable artifact; the only dossier changes from that interval are prompt's own FINDING/PLAN executor entries. Codx history is not rewritten.

Revalidated first: all six accepted candidate paths are byte-identical to CANDIDATE.json (manifest SHA256 3a2bf756…5cae, patch 574c32c0…5d38 both re-derived), and the working tree at handoff is exactly those six modified files plus this untracked dossier. Re-ran 30 of the accepted focused tests under this claim: passed, 16.724974359s.

Owned by claim 236349 (new files only; no other claimant's file edited): supervisor.py, test_supervisor.py, fixture/, IMAGE-ARTIFACT-236349.json, MANAGER-ARTIFACT-236349.json, PACKET-INPUTS-236349.json, OPERATOR-236349.md, verification-4/5.json/.log, and this PROGRESS entry. The six candidate paths are read-only to this claim.

Built and bound, with real digests:

- Refreshed immutable worker artifact from v12/worker/Dockerfile.claude: `baton-v12-claude-worker:w236087-236349`, image config `sha256:2e9e84ff23319778760d5b22c70d543d4290931510a3ab3ecf40bcdaad7456bd`, CLI 2.1.247. Its effective `/opt/baton/claude_agent.py` is `abdf903d…54bb4d` — the accepted candidate byte-for-byte, which the old `sha256:e84a033c…` image cannot serve. Layer diff IDs and all effective worker bytes in IMAGE-ARTIFACT-236349.json, verified by engine inspection plus one throwaway `--network none --read-only` container. No model, credential, egress or registry push.
- Isolated manager runtime: `just build` → distro identity `sha256 04aa459a…a58a`, build stamp commit 1e576ff2, dirty, 7 changed entries (the six candidate paths plus this dossier), so the frozen runtime carries the candidate manager bytes.
- Isolated installation: `just bootstrap` fresh-install form → its OWN generated Authority `636a9493650b4efe9d03c684b5b9d904`, own stores, own repositories, 0 Jobs and 0 workers, under /home/sl/baton-runs/managed-correction-236087/install. No existing deployment, service, credential store or production instance was read, started, changed or enabled; nothing under /home/sl/src/baton was mutated and `git diff --check` is clean.
- Disposable fixture bytes pinned in fixture/ (harness.py prints `before`, corrected output `READY`), with the task, the selected review feedback and the acceptance criteria as separate digest-pinned documents.

Bounded owner supervisor implemented in supervisor.py against the supported owner/manager APIs only: it proves every bound artifact before a store opens (fail-closed), performs `configure_context_storage` / `certify_context_profile` / `authorize_qualification_run`, submits the one Job once, serves through `job_manager.serve` with a stop predicate that ends the run on a terminal or exceptional stage or the overall bound, **stops admission**, spends the reserved cleanup window settling endings while refusing any runtime admitted after the stop, requires a POSITIVE committed `runtime.destroy` (`complete` or `retained`) from `intake.cleanup_of` for every runtime it admitted, and atomically retains the outcome. It never retries, never certifies, fabricates no journal record or verdict, and refuses a production profile outright.

Deterministic supervisor/failure verification in test_supervisor.py: 20 focused checks passed, 46.255348787s (runner 46.066s). The real supervisor drives the accepted composition — real candidate grant guard, manager, worker launches, custody, review cycles, endings and the manager's own committed cleanup records — with the two accepted seams (simulated OCI engine, injected provider subprocess). It establishes: one settled correction with four admitted runtimes and positive cleanup for every one; the second turn really reaching the provider as a `--resume` carrying the review's findings; one grant carrying both generations; distinct revised proposal heads; the retained outcome document; and on the failure side a held run that names its outstanding cleanup, no runtime admitted after the stop, no third implementer invocation, the overall-bound stop, an unprovable cleanup never reported settled, and eight packet refusals (moved fixture byte, moved configuration, moved runtime, `retry: true`, two Jobs, cleanup reserve inside the overall bound, unknown member, absent/moved image). Inherited parent test methods are excluded from this file's suite so its measurement is not inflated with the implementation review's own evidence.

**Not delivered, and named rather than fabricated.** The packet is NOT runnable as handed off, so no file here is presented as one; PACKET-INPUTS-236349.json is explicitly inputs, not the packet. Two steps remain, both in OPERATOR-236349.md with exact commands:

1. The disposable fixture repository's first commit, which fixes `line_declared_base`. This deployment prohibits the implementer from performing Git mutations, so it is an operator act over bytes this packet pins and the supervisor re-proves.
2. The per-Job worker deployment document (`baton.v12.single-worker-deployment/5`) and its digest-sealed `inputManifest`. Seven policy identities, the certified runtime profile and the adapter identity are deployment selections; `dogfood_operator.input_manifest` refuses to fill any of them in because doing so would make a grant on the operator's behalf. Authoring them from a managed turn and calling the result reviewed is the fabrication the 2026-09-22T05:58:20Z review warned against, so this turn did not. Every value the packet can fix is fixed and listed beside the ones that remain.

Verification spending (process wall seconds including runner startup): verification-4 20 supervisor checks 46.255348787s; verification-5 30 accepted regression checks 16.724974359s; this claim's total 62.980323146s. Cumulative measured across the Work: author 49.861932617s + independent review 16.578126122s + this claim 62.980323146s = 129.420381885s. Build wall clock (image, distro, installation) was not separately instrumented; it is preparation, not verification, and is not counted as either. No broad suite, live provider, live model, actual engine execution, authentication operation, deployment change, production enabling, automatic retry or Git mutation. W177936 remains closed and its evidence and costs stay in its own dossier.

Returning through baton.bug: the built artifacts, the supervisor and its verification are for independent review, and the two remaining preparation steps are stated above as remaining scope rather than claimed complete.

## 2026-09-22 — baton.claude, claim 236529, R1–R3 corrections

Review 2026-09-22T06-36-24Z requested changes on the packet and supervisor; owner reroute 236525 selects bounded R1–R3 corrections and completion of the concrete packet bindings. The accepted six-path product candidate is untouched and was re-verified byte-identical under this claim; no `v12/` source, test or documentation file was edited. Claim 236529 owns only dossier files: supervisor.py, test_supervisor.py, packet_bindings.py, test_packet_bindings.py, MANAGER-SOURCE-236529.json, PACKET-INPUTS-236529.json, OPERATOR-236529.md, SELECTIONS-236529.json, verification-6/7.json/.log and this entry. PACKET-INPUTS-236349.json and OPERATOR-236349.md are superseded by their 236529 replacements; the reviewer's own files are untouched.

All four reproduced defects are accepted as real. Running `review-repro-236474.py` against the corrected code no longer confirms them: `test_accepting_first_review_settles_without_restore` now fails to reproduce because the run is held, and the other three error against the corrected closed packet document rather than passing. The reviewer's file was not modified; equivalents of all four are in test_supervisor.py asserting the corrected behaviour, named after the defect.

**R1 — caps, ceiling and the required sequence.** `AdmissionGate` refuses at `operations.admit` before an offer is issued once a declared cap is spent, and refuses an unknown stage kind by name. `held_packet` now requires the counts to be arithmetically possible: one correction is one extra implementer turn and one extra review turn, so `corrections` is a declared member and a packet that disagrees is refused. `turn_seconds` is bound into the Job's own `execution_limits.provider_turn_seconds` and `_turn_ceiling` refuses before serving unless the EFFECTIVE resolved ceiling is the declared one with origin `job`. A settled outcome now additionally requires, read back from the manager's own records: context modes `open` then `restore` on one conversation with distinct uses and one generation per invocation; two distinct retained proposal heads; and recorded dispositions `changes-requested` then `accepted`, reached through `review_cycles.VERDICT_KIND` and `verdict_of`. Nothing manufactures a verdict — an immediate acceptance, a second changes-requested and a rejection are each reported as the run they were and held.

**R2 — a real stop and complete accounting.** Admission is closed at the operations boundary (`gate.stop()`) BEFORE the cleanup window, so the window's sweeps drive endings through a gate whose `admit`, `claim` and `launch` all refuse; the refusal is an ordinary non-durable `ContractRefusal`, which `manager._delegate` records as a deferral and `_start` contains as `deferred`, so a gated tick does not end the sweep with endings unsettled. Every started runtime is recorded at the `launch` call before delegating, so a launch that then faults is still accounted for. The canonical history is re-read after the serving loop (including after a fault) and again inside the cleanup window, and any identity that appears after the stop is BOTH reported in `unexpected_attempts` and added to the cleanup accounting. The supervisor still does not call `authorize_cleanup` itself: the ending driver owns the seal/intake/retention/publication/freeze/cleanup composition, and the owner's instruction for this Work was to extend that path rather than add a second controller. That reasoning is stated in `_cleanups` so a reviewer can disagree with it explicitly.

**R3 — the code that runs is the code that was reviewed.** `MANAGER-SOURCE-236529.json` binds `/home/sl/baton-runs/managed-correction-236087/manager-source`: `baton_v12` and `tools` copied from the reviewed checkout, 106 files, read-only, zero files differing from origin, verified importable from that path alone. The packet binds it and the supervisor's own bytes; `verify_imported_sources` asks the imported module objects where they resolved and refuses anything outside the bound tree, before a store is opened. The operator command's `PYTHONPATH` now names that tree and nothing else. The frozen distro is still bound but is now described as the INSTALLATION artifact and is no longer claimed to be the supervising implementation.

**Concrete packet bindings.** The previous refusal to author the per-Job documents was too broad, as the review said. `packet_bindings.py` now drafts them: two worker deployments (implementation on `single-worker-deployment/5` with `provider_context`, review on `/4` without), the sealed `inputManifest` built from the PUBLISHED worker-contract conformance vector rather than a document written to pass the validator, the candidate context profile `/2`, the Job submission carrying the provider-turn ceiling, and `PACKET.json`. It holds the composition with `stage_execution.held_configuration` — the same validator the serving deployment and `tools.bootstrap` run — before anything reaches the disk. It opens no store, mints no session, reads no credential, starts nothing and grants nothing. The three identities the deployment is accountable for are emitted as readable documents (`runtime-profile.json`, `policy.json`, `adapter.json`) whose digests are used, so an owner approves text rather than a hash. `SELECTIONS-236529.json` marks the four remaining owner fields explicitly.

Still not runnable, and named rather than filled in: the fixture repository's first commit, which fixes `line_declared_base` and which this deployment prohibits the implementer from performing — `packet_bindings` refuses an unresolved base by name rather than writing a placeholder — and the two participants, their principals and the private credential registry path and slot reference. `OPERATOR-236529.md` now carries the exact `init`/`add`/`commit`/`rev-parse` commands instead of an ellipsis, and drops the `stops admission` and `stops by itself` claims the review did not accept, replacing them with what the program actually does at each step.

Accounting correction the review asked for: this Work DID execute the engine once — a throwaway `--network none --read-only` container that hashed `/opt/baton` and read `claude --version` during image verification. The earlier entry's blanket "no actual engine execution" was wrong about that and is corrected here rather than rewritten above. What remains unexecuted is the managed live run: no provider, no model call, no credential, no egress, no registry push, no deployment change and no production enabling.

Verification (process wall seconds including runner startup): verification-6, 37 supervisor checks, 13.505936879s; verification-7, 10 packet-binding checks, 0.277330839s. This claim 13.783267718s. Cumulative measured across the Work: author 49.861932617 + implementation review 16.578126122 + claim 236349 62.980323146 + packet review 1.686792790 + claim 236529 13.783267718 = 144.890442393s. Build wall clock is preparation rather than verification and is not counted as either. `git diff --check` clean; the checkout's working tree is still the accepted candidate's six modified files plus this untracked dossier. No broad suite, live provider, model call, authentication operation, deployment change, production enabling, automatic retry or version-control mutation. W177936 remains closed.

Returning through baton.bug for independent review of the corrections and the drafted bindings; the two owner-side steps above are stated as remaining scope rather than claimed complete.

## 2026-09-22 — baton.claude, claim 238310, R2b and R4 completed; R2a partial

Review 2026-09-22T07-03-13Z requested changes on R2a, R2b and R4; owner reroute 238308 selects their completion. Both reproduced counterexamples are accepted as real. The accepted six-path product candidate is untouched and re-verified byte-identical; **no file under `v12/` was edited**, and `git diff --check` is clean. Claim 238310 owns only dossier files: supervisor.py, test_supervisor.py, packet_bindings.py, test_packet_bindings.py, OPERATOR-238310.md, SELECTIONS-238310.json, PACKET-INPUTS-238310.json and verification-8/9.json/.log. OPERATOR-236529.md, SELECTIONS-236529.json and PACKET-INPUTS-236529.json are superseded by their 238310 replacements; reviewer-owned files are untouched.

**R2b — complete.** `_refresh` no longer swallows a failed canonical read. It answers a fourth value, `read`, records the failure as a named uncertainty and lets the accounting continue over the runtimes that ARE known; `supervise` now takes the final canonical read ONCE, before accounting, and refuses to call a run settled without it. Every uncertainty is a reason to hold and is reported in the outcome's own `uncertainty` member. Running the reviewer's `review-repro-236644.py` against the corrected code no longer confirms `test_refresh_failure_is_silently_settled`: the run is held, naming the unreadable read and stating that a failed read is not evidence of absence. The reviewer's file was not modified.

**R2a — partially complete, and the remainder is a pinned product seam.** Three parts are done. (1) Interruption: `KeyboardInterrupt` and `SystemExit` are not `Exception`, so the previous handler let Ctrl-C or SIGTERM leave every started runtime unaccounted for. SIGTERM is now routed into the same path (best effort — a non-main thread cannot install a handler), the shutdown accounting runs, the outcome is retained, and `SupervisorInterrupted` is raised carrying it so the interrupt is neither swallowed nor left without evidence. A second interrupt during the cleanup window is caught and reported rather than escaping mid-accounting. (2) The supervisor now asks the composed deployment to stop what is still executing, through a named `cancel_attempt` capability, for every admitted attempt whose stage is still in an active state; a refused cancellation is a reason to hold. (3) A composition that carries no such capability is REPORTED — each runtime left executing becomes a named reason to hold — instead of a leak being reported as a clean stop.

What is NOT done: no composition carries `cancel_attempt` yet, so the reviewer's `test_overall_timeout_does_not_stop_waiting_runtime` still reproduces — the engine receives no stop. The accepted path is `attempts.request_cancellation(store, port, agent, adapter, ...)`, which fences the generation at the Authority and only then orders the agent's cancel and the adapter's stop. Its port, cooperative agent and runtime adapter are per-attempt objects the deployment builds at launch (`_SingleWorker._adapter` over the attempt's mounted roots; `OciAdapter.stop` needs only the runtime id and an operation id). Reconstructing them from another module's private state would be a second controller composing a security boundary it does not own, so the seam belongs in the product: a `cancel_attempt` on `tools/single_worker`'s composed per-worker operations and a router for it on `tools/stage_execution.StageExecution`. That is a product-path change with its own ownership and amended candidate provenance; it is pinned in PLAN.md and NOT begun. The supervisor already drives it, so the seam landing is the whole of the remaining change on this side.

**R4 — completed except the end-to-end composition run.** (a) Network: `packet_bindings` no longer hard-codes `none`. `provider_network` is a required operand reaching the runtime profile, the adapter identity and both worker deployments, and `none` is refused by name with the reason — `oci.py` passes the value straight to `--network` and the worker reaches an external Claude API, so that deployment could never answer the question the run exists to ask. Selecting the network authorizes no call. (b) Authority preparation: `packet_bindings.preflight` reads an open Authority and names every missing Work, principal and capability, writing nothing, and states explicitly that route-handler registration is NOT verifiable through the Authority's public readers rather than implying it checked. `OPERATOR-238310.md` gains step 5a with the exact `create_work` / `add_route_handler` / `grant_capability` calls, against the disposable isolated instance. (c) `evidence_digest` is no longer a sentinel: an all-zero digest is refused, and `SELECTIONS-238310.json` names the sha256 of W177936's independently accepted `REVIEW-EVIDENCE-235998.json`, which is what this candidate profile rests on. (d) Reviewer input: one Job carries one input manifest, so a second task document for the review role is one no stage could satisfy; the criteria therefore travel in the single task document AND in the fixture repository, whose step-4 commit now includes `TASK.md`, `REVIEW-FEEDBACK.md` and `ACCEPTANCE.md` beside `harness.py`, read-only at `/input/source`. The instructions tell the reviewer to judge what was actually published and not to return a verdict the document asked for if the proposal does not warrant it; no verdict is forced and a first acceptance remains an honest held outcome.

Not done for R4: driving the generated documents through the actual entrypoint over a freshly composed instance. The supervisor checks still use the accepted pre-provisioned composition and the binding checks stop at document validation plus the manager's own `held_configuration`. That composition run depends on operator step 5a (an Authority mutation) and on the cancellation seam above, so it is stated as remaining scope rather than approximated.

Verification (process wall seconds including runner startup): verification-8, 42 supervisor checks, 15.583319475s; verification-9, 16 packet-binding checks, 0.335177029s. This claim 15.918496504s. Cumulative measured across the Work: 146.324112960 (prior, including the reviewer's 1.433670567s reproduction) + 15.918496504 = 162.242609464s. Build wall clock is preparation rather than verification and is counted as neither. No broad suite, live provider, model call, authentication operation, store or credential access, deployment change, production enabling, automatic retry or version-control mutation. The one engine execution this Work performed remains the claim-236349 image-inspection container, recorded above. W177936 remains closed.

Returning through baton.bug: R2b and R4(a–d) for independent review, and R2a's product seam plus the end-to-end composition run as exact remaining scope.


## 2026-09-22 -- baton.claude, claim 238462, R2a and executable R4 complete

Review 2026-09-22T11:53:11Z accepted R2b and held R2a and executable R4 open;
owner reroute 238460 continues the already-authorized scope of 238308. Both
remaining counterexamples are accepted as real. Product-path ownership was
pinned in PLAN.md with pre-edit bytes BEFORE the first edit, and `CANDIDATE.json`
is amended to carry the two product paths and their two focused test paths
beside the six originally accepted ones, which are unchanged and re-verified
byte-identical.

**The cancellation seam.** `tools/single_worker.py` gains
`_SingleWorker.cancel_attempt`, which derives the attempt's ordinary allocated
roots, builds the adapter the identify/observe path already builds
(`_adapter(roots, None, None, None)` -- `OciAdapter.stop` reads only a runtime
id and an operation id, so a stop has no credential delivery, launch document or
orphan to compose), supplies `_UncooperativeAgent`, and calls the accepted
`attempts.request_cancellation`, which fences the exact participant and
generation at the Authority BEFORE ordering quiescence. Nothing re-implements
any part of it. `_Operations.cancel_attempt` delegates.
`tools/stage_execution.StageExecution.cancel_attempt` routes an attempt to the
worker its RECORDED ALLOCATION names -- not a guessed role, because a correction
round is exactly the case where two attempts of one role exist -- and refuses by
name for an attempt with no allocation or a worker this deployment does not
compose.

`_UncooperativeAgent` reports rather than pretends. This deployment's worker
speaks through a durable file exchange and has no cooperative cancellation
channel, so its settlement says so and travels back un-summarized. Raising would
have been accurate and then unhelpful: a throwing agent still lets the stop
happen and is then re-raised, so every ordinary cancellation would have ended in
an exception meaning "as expected". A bare success would have been a deployment
telling the manager that a worker cooperated with an order it never received.

**R2a's two remaining edges.** `_cancel_active` now decides per ATTEMPT through
`attempts.attempt_runtime_of`, not through the stage-kind projection: a launched
attempt whose kind was unknown or whose stage state was unreadable used to be
passed over and reported as though nothing were executing, and a completed older
generation could be cancelled because its stage had a newer waiting attempt. An
unreadable fact is now a reason to ORDER the stop, named as an uncertainty --
a runtime this manager cannot describe is the one it must not leave running on a
guess. The termination handler is installed and restored around the WHOLE run
rather than released when `serve` returns, `_cancel_active` catches
`BaseException`, and an interrupt during cancellation is recorded, the remaining
runtimes are still ordered stopped, and the outcome is retained before
`SupervisorInterrupted` is raised. `SIGKILL` cannot be caught and no recovery
from it is claimed.

**Executable R4.** `test_generated_packet.py` drives the GENERATED packet
through the real entrypoint: `packet_bindings.compose`/`write` produce the
deployment, sealed input manifest, candidate profile, submission and
`PACKET.json`; `stage_execution.operations_from` composes those bytes; and
`supervisor.supervise` drives them through `held_packet`, the owner acts, the
admission gate, the correction and the cleanup accounting, over a fresh
disposable Authority built through public APIs. One path covers the initial
proposal, the real changes-requested feedback delivery, restoration, the revised
result and independent acceptance; a second covers the timeout, where the engine
really receives a stop for the exact runtime it started and the run is still
held because an ordered stop is not proof of absence. The engine and provider
subprocess remain the two accepted seams.

Operator corrections: `OPERATOR-238462.md` references `SELECTIONS-238462.json`
(the 238310 file predated `provider_network` and the evidence binding), moves
the preflight example onto a LIVE Authority handle before `dispose()` with its
`documents` and `participants` operands defined, and replaces the
"still missing" section with what the seam now does and what it still does not
prove. `SELECTIONS-238462.json` enumerates the six unresolved operands
explicitly. `MANAGER-SOURCE-238462.json` rebinds the imported tree, 106 files,
zero drift from the checkout, now carrying the changed product bytes, and was
re-verified importable from that path alone.

Pre-existing and NOT caused by this claim: twelve errors in
`tests.tools.test_stage_execution` (`AFreshPortReentersANeverStartedDelivery`
and `TheIntegrationStageConsumesTheAcceptedPort`, all
`AttributeError: 'types.SimpleNamespace' object has no attribute 'reconciles'`).
Confirmed by running those two classes against the PRE-EDIT
`tools/stage_execution.py` bytes retained in the bound manager-source tree: the
same twelve errors occur. They are a fixture/product drift in this checkout,
outside this claim's scope, and are reported rather than repaired.

Verification (process wall seconds including runner startup): verification-10,
67 checks over supervisor, packet bindings and the generated packet,
19.402149029s; verification-11, 169 checks over the two owned product test
modules including the new seam classes, 10.477690454s. This claim
29.879839483s. Cumulative measured across the Work: 164.250246394 (prior,
including the reviewer's 2.007636930s partial-review run) + 29.879839483 =
194.130085877s. Running the reviewer's `review-checks-238394.py` now reports
both remaining-defect counterexamples as NOT reproduced; the reviewer's file was
not modified. No broad suite, live provider, model call, authentication
operation, deployed store or credential access, deployment change, production
enabling, automatic retry or version-control mutation. The one engine execution
this Work performed remains the claim-236349 image-inspection container.

Returning through baton.bug for one complete independent review of the amended
candidate and the generated-packet proof.


## 2026-09-22 -- baton.claude, claim 238700, shutdown safety and the entrypoint

Review 2026-09-22T12:31:42Z accepted the cancellation seam and the generated
deployment's correction proof, kept R2b accepted, and held open R2a's
interruption safety, the R4 command-entrypoint proof and the stale operator
instructions. Owner reroute 238696 continues the existing 238460 authority.
All three findings are accepted as real.

Ownership: this claim edits the four product/test paths already pinned and owned
under claim 238462 (`v12/python/tools/single_worker.py`,
`v12/python/tools/stage_execution.py` and their two focused test modules) plus
the dossier's own files. Only `single_worker.py` is unchanged from 238462 in
behaviour; `stage_execution.py` is unchanged entirely. The six originally
accepted candidate paths remain READ-ONLY and byte-identical.

**R2a -- the shutdown is interruption-safe as a phase, not per call site.**
Adding another narrow `except` would have fixed the one read the reviewer
injected into and left the next one exposed, so the design changed instead.
`Termination` installs one handler for SIGTERM and SIGINT with two modes: while
the run is SERVING a signal raises and ends the loop, which is what an operator
asking it to stop means; once admission has closed it is DEFERRED -- recorded
and execution continues -- because everything after that point is the accounting
that exists to leave nothing unexplained. `supervise` raises
`SupervisorInterrupted` after the outcome is retained, carrying every
interruption it saw in `interruptions`. Separately, `_guarded` bounds each
shutdown step -- the post-stop read, the cancellation, each cleanup-window read,
the final canonical read, the cleanup accounting and the workload evidence --
and the per-attempt runtime read is bounded INSIDE the cancellation loop, so an
interruption at one attempt's read costs neither that attempt's stop nor any
later attempt's. A bounded step's failure is a named uncertainty and a reason to
hold; a non-`Exception` failure is also recorded as an interruption. No
`SIGKILL` recovery is claimed and none is possible.

Running the reviewer's `review-checks-238615.py` now reports
`test_interrupt_in_runtime_read_escapes_without_outcome` as NOT reproduced: the
engine is ordered to stop, the outcome is on disk, and `SupervisorInterrupted`
is raised rather than the bare `KeyboardInterrupt` that used to escape. The
reviewer's file was not modified; an equivalent positive case is in
`test_supervisor.py` beside a direct check of the handler's two modes.

**R4 -- the operator entrypoint is now executed.** `TheGeneratedPacketRunsThroughMain`
binds `manager_source` to `v12/python`, the tree this process really imports
`baton_v12` and `tools` from, so `verify_imported_sources` passes for the reason
it exists rather than over a synthetic package; then it runs `supervisor.main`
itself. Three paths: the correction completes and main exits 0 with the outcome
retained and both stores opened by main; the overall bound elapses and main
exits 1 with the engine ordered to stop the exact runtime and the cleanup still
outstanding; and a packet whose bound source is not the imported one is refused
with exit 2 before any store is opened or the engine is asked. `main`'s own
`prepare`, compose, store lifecycle and exit status are covered. The engine and
provider subprocess stay simulated at their normal boundaries, and `time.sleep`
is patched because the composed deployment has no daemon to run a container --
the same boundary every other case here drives from the loop's injected wait.

**That test found a real defect immediately.** `main` called
`JobStore.open(path, clock=...)` without `authority_uuid` or `incarnation`, both
of which are required keyword operands, so it raised `TypeError` before opening
anything. Fixed: the store is opened against the Authority the packet's
deployment names, which is `single_worker`'s own rule -- a store's episode
identities are derived in its own Authority's namespace. Nothing before this
claim could have observed it, because nothing ran `main`.

**Operator instructions.** `OPERATOR-238700.md` replaces the 238462 revision:
step 5 now names `SELECTIONS-238700.json` and its six unresolved operands rather
than the superseded four-field document, the header cites the current
packet-inputs and manager-source records, the shutdown bullet says the
deployment carries the capability and points at the section that describes it
rather than at a section that no longer exists, and the manager-source paragraph
names the refreshed record. Digests were restamped afterwards.

Verification (process wall seconds including runner startup): verification-12,
72 checks over supervisor, packet bindings and the generated packet including
the three entrypoint cases, 25.981316738s; verification-13, 165 checks over the
owned product test modules, 10.563196602s. This claim 36.544513340s. Cumulative
measured across the Work: 202.209270735 (prior, including the reviewer's
8.079184858s) + 36.544513340 = 238.753784075s. The twelve pre-existing
`test_stage_execution` fixture errors reported under claim 238462 are unchanged
and still out of scope. No broad suite, live provider, model call,
authentication operation, deployed store or credential access, deployment
change, production enabling, automatic retry or version-control mutation.

Returning through baton.bug for independent review.


## 2026-09-22 -- baton.claude, claim 238827, the workspace prerequisite and a loss

Review 2026-09-22T12:55:41Z accepted the R2a shutdown correction, kept R2b and
the product acceptance, narrowed R4 to one missing preparation step, and raised
a separate operational finding about deleted historical packet records. Owner
reroute 238822 continues the existing 238696 authority. Both are accepted as
real; the second is mine.

**R4 -- the prerequisite the test was supplying.** `configure_context_storage`
reads `configured_workspace_storage` immediately, because the context roots are
checked for containment against the workspace root, and the ordinary
composition records that fact later in its own preflight. So a fresh `main` had
nothing to read, and the entrypoint fixture was quietly calling
`configure_workspace_storage` beforehand -- an undocumented deployment act, not
one of the two accepted seams. `supervisor.prepare` now performs it as its
first owner act, and `_workspace_root` DERIVES the root from the deployment
configuration the packet is bound to rather than choosing one: every worker
must name the same absolute `workspace_storage`, and workers that disagree are
refused by name instead of one being picked. The existing boundary is untouched
-- `configure_workspace_storage` still refuses a manager already holding
attempts under a different root, and the context/workspace exclusion checks are
unchanged. `prepared_stores` is deleted from the fixture, so `run_main` now
supplies only the engine and the provider; two new checks cover the sequence
(the configured root read back after a successful `main`, and the two-store
refusal). The reviewer's counterexample no longer reproduces -- it patches out a
helper that no longer exists, because the act it stood for moved into `prepare`.

**The operational finding is mine and the loss is real.** From claim 236529
onward I superseded the operator packet by writing the new revision and
unlinking the old one, so each revision's evidence locator stopped resolving
the moment the next landed. `OPERATOR-238462.md`, `PACKET-INPUTS-238462.json`
and `SELECTIONS-238462.json` are gone, and so are the 236349, 236529 and 238310
revisions. The bytes are NOT recoverable: each was generated from dossier state
that has since moved, so regenerating would produce different bytes under an old
name -- an invented artifact presented as a retained one. I have not done that.
`LOST-ARTIFACTS-238827.md` records every superseded file, the authoritative
digest where the independent reviewer's own retained evidence holds one, and
what is and is not lost: no accepted product byte, candidate provenance,
verification receipt or reviewer artifact was affected. The practice is changed
from this claim: a new revision is added BESIDE its predecessor, the predecessor
is marked superseded in its own header, and nothing in this dossier is unlinked.
`OPERATOR-238700.md`, `SELECTIONS-238700.json` and `PACKET-INPUTS-238700.json`
are kept in place for that reason.

`OPERATOR-238827.md` also states that configuring the workspace store is no
longer an operator act, so nobody goes looking for a step that does not exist.

Verification (process wall seconds including runner startup): verification-14,
74 checks over supervisor, packet bindings and the generated packet including
the five entrypoint cases, 27.102115105s; verification-15, 165 checks over the
owned product test modules, 10.480146766s. This claim 37.582261871s. Cumulative
measured across the Work: 248.644322402 (prior, including the reviewer's
9.890538327s) + 37.582261871 = 286.226584273s. The twelve pre-existing
`test_stage_execution` fixture errors remain unchanged and out of scope. No
broad suite, live provider, model call, authentication operation, deployed store
or credential access, deployment change, production enabling, automatic retry or
version-control mutation. The ten candidate paths are unchanged.

Returning through baton.bug for independent review.
