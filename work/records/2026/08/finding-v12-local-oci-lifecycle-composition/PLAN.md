# Plan: local OCI lifecycle composition

1. [blocked on component and manager Jobs] Revalidate every dependency's final
   public contract before integration.
2. [pending] Compose consent teardown, activation and fresh execution creation.
3. [pending] Compose cancel, quiescence, freeze, collect, destroy and positive
   absence with effectively-once operation identities.
4. [pending] Run Docker restart/race/failure evidence and compatible Podman
   evidence where available.
5. [pending] Return for independent integration review; do not claim W6's
   portable conformance result.

## 2026-08-27 — first implementer round

- [done] 1. Every dependency's final public contract revalidated. Ten closed,
  **W6634 non-satisfying**; the provisional reach mapped call by call, and the
  acceptance clause on satisfying dependencies recorded as unmet.
- [done] 2. Consent teardown, activation and fresh execution creation composed
  against a real engine, including consent proved absent BEFORE the execution
  container is created, and the input-root authorization measured at both
  manager boundaries and at the adapter's own seam.
- [partial] 3. Cancel and quiescence composed with effectively-once identities;
  fence-then-stop established off one ordering trace. **Freeze, collect, destroy
  and positive absence are NOT composed** — all four are reachable only through
  W6634's provisional code, and that reachability fact is itself established by
  a case rather than asserted.
- [partial] 4. Docker restart, race, partition and failure evidence composed.
  Podman is absent on this host; the cases are written and skip narrowly.
- [done] 5. Returned for independent integration review. No portable
  conformance result is claimed and nothing is closed.

### Open, and none of them mine to settle

- [review, blocking] May integration proceed across a non-satisfying
  dependency, or does W6634's half need a successor Work before W6636 can reach
  terminal signoff? The acceptance says it may not; only review can rule.
- [needs an owner] `run_vector` composes no `--env`, so no worker the adapter
  starts can run. Component defect, surfaced by composition.
- [needs an owner] No manager operation calls `adapter.observe`, so an exited
  worker is recorded `running`. Component defect, surfaced by composition.
- [needs an owner] No operation joins the `consent_runtime` axis to the consent
  posture; the composition drives the adapter directly meanwhile.
- [needs an owner] W19784 left `check_input_pair`'s three receiving parameters
  unregistered in the contracts inventory's `OWNERS` table, so the full-tree
  gate carries a seventh failure beyond the accepted six. Mine originally, and
  that Work is closed satisfying — not mine to edit now.

## 2026-08-27 — independent review disposition

- [done] Preserve the 24-case module and 18-mutation harness as diagnostic
  integration evidence. Do not describe any tested arc as certified: the
  shared `start` and `destroy` paths include W6634's provisional changes even
  with empty output and credential operands.
- [decision required] Approve two successor Work items to W6634: one for output
  custody and one for credential delivery, with the shared start/destroy
  settlement crossing assigned explicitly. Neither successor inherits
  acceptance from the retained provisional tree.
- [queued after decision] File bounded correction Work for (a) delivery of the
  four non-secret worker launch values through the OCI seam, (b) exact
  `adapter.observe` use during reconciliation, and (c) a manager-owned consent
  runtime operation. Each needs a positive real-engine regression replacing
  the current expected-failure reproduction.
- [queued after decision] File a follow-up to W19784 for the three missing
  `check_input_pair` inventory owners, add the closed W19784 dependency and its
  correction as W6636 gates, and restore the aggregate gate to only its
  explicitly accepted baseline.
- [blocked] Resume lifecycle composition only after those component/correction
  Works close satisfying. Then run independent Docker review across success,
  refusal, cancellation, retry, restart, uncertainty, freeze, collect,
  destroy, positive absence and cleanup recovery; run the same Podman contract
  when the daemon is available.

## 2026-08-27 — approver decomposition ruling

- [approved] Split W6634's required surface into independently reviewed output
  custody and fresh-run credential-delivery successors; keep W6634 terminal
  non-satisfying and treat its tree only as provisional input.
- [approved] W6636 owns the successors' shared start/destroy settlement
  crossing plus restart adoption, reconciliation and orphan convergence.
- [next reviewer] Create and bind those two successor Works plus bounded
  correction Works for launch environment, exact observation, manager-owned
  consent and W19784 inventory ownership. Add W19784 as historical dependency
  and all six new Works as live W6636 blockers; index them in this plan.
- [blocked implementation] Resume W6636 only after all six close satisfying.
  Preserve the diagnostic suite, convert its expected failures into positive
  real-engine regressions, complete the remaining lifecycle matrix and return
  for independent Docker review.

## 2026-08-27 — decomposition recorded

- [live blocker] W26283, “Build OCI output custody provider,” bound to
  `work/records/2026/08/finding-v12-oci-output-custody/`.
- [live blocker] W26284, “Build OCI fresh-run credential delivery provider,”
  bound to `work/records/2026/08/finding-v12-oci-fresh-run-credentials/`.
- [live blocker] W26291, “Deliver reference-worker launch environment through
  OCI,” bound to
  `work/records/2026/08/finding-v12-oci-worker-launch-environment/`.
- [live blocker] W26294, “Reconcile exact OCI runtime state through adapter
  observation,” bound to
  `work/records/2026/08/finding-v12-oci-runtime-observation/`.
- [live blocker] W26295, “Compose manager-owned consent runtime lifecycle,”
  bound to `work/records/2026/08/finding-v12-manager-consent-runtime/`.
- [live blocker] W26296, “Register check_input_pair receiver ownership,” bound
  to `work/records/2026/08/finding-check-input-pair-inventory-follow-up/` and
  recorded as a follow-up to W19784.
- [historical provenance, ledger edge refused] W19784 supplies assignment
  identity and remains a closed satisfying prerequisite rather than a live
  implementation gate. The canonical CLI refused `block work=W6636
  on=W19784`: WS-2 permits blocker edges only to open Work. W26296's atomic
  `follow-up-of=W19784` relation and these records preserve the authorized
  history without bypassing the ledger rule.
- [blocked implementation] W6636 owns the shared crossing and later lifecycle
  matrix. It resumes only after W26283, W26284, W26291, W26294, W26295, and
  W26296 all close satisfying.

## 2026-08-27 — direct claim-to-execution supersession

- [superseded] Do not compose or certify a separate consent runtime; W26295
  closes cancelled and its dependency is historical rather than satisfying.
- [pending] Compose reservation → atomic claim → one execution-runtime launch,
  including expiry/race with no launch and typed post-claim launch failure.
- [pending] Preserve agent refusal through `plan-rejected` and `unsupported`
  results and retain all output, credential, cancellation, recovery,
  reconciliation and orphan-convergence gates that do not depend on consent.
- [pending] Replace consent-posture cases in the retained diagnostic suite
  rather than weakening unrelated isolation, identity, or fencing assertions.

## 2026-08-28 — attempt-domain prerequisite from W28681

- [pending implementation] On success, failure, cancellation, deadline,
  restart reconciliation and orphan recovery, force-remove the exact execution
  container and observe positive absence before clean settlement, credential
  removal, lane reuse or replacement.
- [pending regression] Prove an `exited` but still-present container does not
  satisfy cleanup, observation uncertainty fails closed, and the container
  cannot launch host or sibling-container processes outside its runtime
  boundary.

## 2026-08-28 — unblocked implementation sequence

- [done, reviewer revalidation] All live prerequisites are terminal in their
  intended outcomes: W26283, W26284, W26291, W26294, W26296 and W28681 are
  satisfying; W26295 is cancelled by the recorded topology supersession.
  W6634 remains non-satisfying history and is not an accepted provider.
- [implement first] Replace the consent-runtime fixtures and the
  `destroy-is-unreachable` expectation with the direct reservation → atomic
  claim → activation → single execution launch arc. Preserve the existing
  input authorization, generation, identity, fencing, duplicate-start and
  exact-observation regressions.
- [implementation] Construct the composition adapter with W26283 output
  declarations, a W26284 materialized credential delivery when the assignment
  requires one, and the W26291 launch delivery. Exercise the reference worker
  through those production providers rather than empty operands.
- [implementation, P0] Make post-claim start refusal a typed, recoverable
  manager ending. Reconcile exact engine state, force-remove and prove absence
  for any possibly created container, settle launch and credential roots, and
  leave uncertainty cleanup-required. Do not start a replacement until that
  ending is proved.
- [implementation, P0] At `authorize_cleanup`, consume and validate the
  adapter's separate credential and launch endings. Positive runtime absence
  alone cannot record clean settlement when an applicable provider reports
  unresolved teardown.
- [integration] Drive completed, unable/fault, plan-rejected,
  unsupported-version, cancellation and deadline outcomes through quiescence,
  freeze, intake, retention, force-removal, exact absence and provider
  teardown. Assert cleanup and posture-slot/lane reuse only after every
  required ending is positive.
- [negative/race] Prove decline, expiry and a lost claim start nothing; retry
  after a post-create failure cannot duplicate; exited-but-present and
  uncertain observation do not clean or release; restart adoption, mismatched
  identity, multiplicity and per-attempt orphan recovery converge without
  deleting sibling material.
- [security] Inspect the live execution container for exact read-only `/input`,
  the one writable private workspace, separate read-only credential and launch
  mounts, and absence of the authority store, integration credentials,
  unrelated host paths and writable canonical checkout. Prove the runtime
  boundary cannot create host or sibling-container processes.
- [verification] Run required Docker evidence and the focused Python manager
  suite, preserve the mutation checks for ordering/identity guards, and run the
  same Podman contract when available with only an availability skip. Return
  for independent real-engine review before closing W6636 or unblocking W5.

## 2026-08-28 — first resumed implementer round

- [done] The shared settlement crossing at `authorize_cleanup`. The destroy
  answer's member contract is named once (`_DESTROY_MEMBERS`) and includes the
  two provider endings; `_provider_ending` owns each where it arrives;
  `_unsettled_providers` reports every root that did not reach a terminal
  ending; and a clean settlement requires all of them.
- [done] Nothing that fails to settle is journalled. `_not_an_ending` decides
  the non-endings before the transaction opens, so an unsettled cleanup can
  actually be retried — which the previous shape made impossible for the new
  provider case AND for the pre-existing `uncertain` one.
- [done] The post-claim start refusal is settled at `request_runtime_start`
  through `_start_failed`: reconcile, attach what exists, record `uncertain`
  when nothing can be established, start no replacement, and re-raise the
  original refusal with its own closed pair and an account of the settlement.
- [done] Regressions: `TheDeliveryProvidersMustEndBeforeCleanupIsClean` and
  `test_an_uncertain_destroy_can_actually_be_tried_again` in
  `tests/manager/test_intake.py`; `ARefusedStartIsSettledRatherThanStranded`
  in `tests/manager/test_attempts.py`.
- [done] Real-engine evidence for the crossing:
  `evidence/w6636-settlement-crossing-probe.py`.

### Still open, and explicitly NOT done this round

- [next] Replace the three consent-runtime cases and
  `test_destroy_is_unreachable_without_the_provisional_path` in
  `tests/manager/test_lifecycle_composition.py` with the direct one-container
  arc. They still pass and still assert the superseded boundary; they were
  left rather than half-migrated, because deleting them without the
  replacement arc would only reduce coverage.
- [next] Compose the adapter with W26283 output declarations and a W26284
  credential delivery, and drive the complete arc — quiescence, freeze,
  intake, retention, force-removal, exact absence, provider teardown, clean
  settlement, slot reuse — through the production providers against a real
  engine.
- [next] The negative/race, restart-adoption, orphan-convergence and security
  (mount inspection, no host or sibling process creation) matrices.
- [next] Podman as the additive contract with a narrow availability skip.

## 2026-08-28 — independent review of the resumed P0 round

- [verified partial] The destroy document admits and reads provider endings,
  unsettled answers are not journalled, and ordinary refused-start
  reconciliation attaches or records uncertainty without replacing the
  original refusal pair.
- [required, P0] Preserve provider applicability and outstanding teardown
  independently of the runtime axis. A retry after runtime absence must call
  provider teardown again, must remain pending while the provider remains
  unresolved, and may settle only after a terminal provider ending.
- [required, P0] Make every `_start_failed` exit durably leave a state other
  than `start-requested`; reconciliation refusal or fault must record
  `uncertain` before the original start failure crosses back to the caller.
- [still required] Complete the one-container production-provider integration,
  negative/race and restart/orphan matrices, security assertions, real-engine
  evidence, and additive Podman contract already listed above.

## 2026-08-28 — second resumed round, the re-reviewed [P0]s

- [done] A pending cleanup re-enters provider teardown. The
  `execution_runtime == "destroyed"` short-circuit is gone for an attached
  identity, so every retry asks the adapter and reads its current endings.
- [done] Every exit from refused-start settlement leaves an ending.
  `_settle_unknown_start` records `uncertain` from `start-requested` only, and
  covers a failed reconciliation, an absent `list` capability, and an adapter
  that faults rather than refuses.
- [done] Regressions: the three-round call-count case and the
  already-destroyed case in `tests/manager/test_intake.py`; the failed
  reconciliation, narrow capability, fault, and never-overwrite cases in
  `tests/manager/test_attempts.py`.
- [done] `evidence/w6636-corrected-p0-retry.py` beside the reviewer's file, and
  the real-engine probe now prints the engine's own sentence when it cannot
  reach the daemon so a managed-shell boundary is distinguishable from an
  absent host.

### Still open, unchanged from the first resumed round

The one-container real-engine module replacement, the negative/race and orphan
matrices, the security inspection and Podman all remain ahead.

## 2026-08-28 — independent re-review of the second P0 round

- [verified partial] Cleanup retries now call the adapter after runtime
  destruction, and failed refused-start reconciliation leaves a durable
  `uncertain` ending without overwriting stronger evidence.
- [required, P0] Preserve provider applicability/outstanding teardown across
  restart and omission. Once a provider reports unresolved, a later missing
  optional member must not permit clean settlement; require an explicit
  terminal provider ending.
- [required, P0] Reconcile exact state after a non-`ContractRefusal` start
  fault before falling back to `uncertain`, while re-raising the original
  fault unchanged. Attach a matching runtime the failed call created.
- [still required] Complete the previously listed one-container real-engine,
  negative/race, orphan, security and Podman integration remainder.

## 2026-08-28 — third resumed round

- [done] The destroy-answer contract is closed: both provider endings are
  required, `not-delivered` is the explicit no-provider ending, and an
  omission is refused rather than read as absence. The manager's own synthetic
  answers satisfy the same contract.
- [done] `_settle_failed_start` is the one settlement boundary for a refused
  start and a faulting one; the fault re-raises unchanged and the `uncertain`
  fallback is retained.
- [done] Regressions: the omission refusal and the restart case in
  `tests/manager/test_intake.py`; the fault-after-creation, unanswerable-fault
  and one-boundary cases in `tests/manager/test_attempts.py`.
- [done] `evidence/w6636-corrected-omission-and-fault.py` beside the
  reviewer's two files. The shared `Custodian` double now answers verbatim.

### Still open, unchanged

The one-container real-engine module replacement, the negative/race and orphan
matrices, the security inspection and Podman all remain ahead.

## 2026-08-28 — independent third re-review

- [verified] The closed provider-ending contract refuses omission after
  restart and settles only explicit terminal endings; the shared failed-start
  boundary reconciles and attaches a fault-created runtime while retaining the
  `uncertain` fallback.
- [required, P2] Make
  `test_both_kinds_of_failed_start_take_one_settlement_boundary` execute its
  registered `TestCase` cleanups. The focused manager gate must not leak its
  temporary directories or SQLite connections.
- [still required] Complete the one-container real-engine replacement,
  negative/race and orphan matrix, security inspection and Podman contract.

## 2026-08-28 — independent P2 cleanup review

- [verified] The manual-case regression and four corrected evidence scripts
  execute registered cleanups; the focused 207-test gate and all four scripts
  pass with `ResourceWarning` promoted to an error.
- [still required] Complete the one-container real-engine replacement,
  negative/race and orphan matrix, security inspection and Podman contract.

## 2026-08-28 — independent review of the first one-container slice

- [verified partial] The production-provider arc reaches the adapter's retain
  and destroy seams, and `destroy` now admits the manager-delivered operation
  beside its already-authorized body.
- [required, P0] Make `OciAdapter.retain` enact `discard-after-intake` against
  the named adapter-owned custody artifacts and prove their absence before it
  returns. Preserve `retain`/`quarantine`, reject unowned identities, and make
  retry idempotent.
- [required regression] Cover discard, keep, subset, invalid/cross-attempt
  identity and retry in focused tests; make the real arc assert discarded
  custody bytes are gone before accepting `cleanup=complete`.
- [still required] Replace the remaining superseded consent/unreachable cases
  and complete the negative/race, restart/orphan, security, and Podman matrix.

## 2026-08-28 — independent re-review of the retention correction

- [verified partial] Selective discard is derived from declared,
  attempt-scoped identities, establishes absence, and is idempotent; the real
  arc now asserts custody before and after the decision.
- [required, P0] For `retain` and `quarantine`, positively establish every
  named adapter-owned custody tree is present before returning; missing custody
  must refuse before the manager journals a false retained ending.
- [required, P1] Validate the frozen three dispositions before any mutation;
  an unknown value must refuse and leave custody untouched.
- [required regression] Add absent-custody cases for both keep dispositions
  and a byte-preserving unknown-disposition case, then rerun focused and real
  arc gates.
- [still required] The previously pinned superseded-case replacement,
  negative/race, restart/orphan, security, and Podman remainder is unchanged.

## 2026-08-28 — independent retention fail-closed re-review

- [verified] Unknown dispositions refuse before mutation, both keep
  dispositions require present named custody, and the earlier selective,
  derived, absent-proved, idempotent discard remains intact.
- [verified] Corrected evidence and 231 focused sealing/OCI/intake tests pass
  with `ResourceWarning` promoted to an error.
- [still required] The previously pinned superseded-case replacement,
  negative/race, restart/orphan, security, and Podman remainder is unchanged.

## 2026-08-28 — independent superseded-case replacement review

- [verified] Reservation-before-claim, one post-claim execution container,
  provider-ending distinction, and no-receipt cleanup blocking preserve the
  applicable rules from the four retired cases.
- [required, P1] Replace the malformed-`None` lost-claim fixture with a typed
  competing-claim refusal, settle its durable `claim-refused` ending, and
  attempt the next manager lifecycle step. Prove that refusal prevents
  activation/start before any engine call.
- [still required] Complete the remaining offer-expiry, post-create retry,
  agent-ending, deadline, restart/orphan, security, and Podman matrix.

## 2026-08-28 — independent lost-claim re-review

- [verified] A typed competing-claim refusal reaches durable `claim-refused`;
  activation and start then refuse for their pinned reasons before any engine
  run, and the daemon carries no matching container.
- [verified] The focused 269-test offer/attempt/intake gate passes with
  `ResourceWarning` promoted to an error.
- [still required] Complete the remaining offer-expiry, post-create retry,
  agent-ending, deadline, restart/orphan, security, and Podman matrix.

## 2026-08-28 — independent security and orphan review

- [verified partial] Daemon-returned state pins the exact mount targets and
  sources and most of the applied runtime security boundary.
- [required, P1] Exercise `OciAdapter.recover_credentials` with two real
  sibling deliveries and prove recovery evidence for one attempt cannot remove
  the other. A direct call to `CredentialHome.discard_orphan` does not compose
  the production recovery seam.
- [required, P1] Pin the private/default applied PID namespace. Excluding only
  literal `host` admits `container:<sibling>`, which violates the attempt-owned
  process domain.
- [still required] Complete offer-expiry, post-create non-duplication,
  agent-ending/deadline cleanup, ended-runtime restart adoption, and Podman.

## 2026-08-28 — approver happy-path/decomposition ruling

- [in progress; do not disturb live claim] Finish the current independent
  review of the submitted one-container Docker arc and its already-submitted
  security/orphan evidence. Correct any defect that makes that positive arc
  falsely report success.
- [next handoff] Decide W6636 on that bounded happy-path acceptance instead of
  appending another unstarted robustness subsystem to this thread.
- [acceptance meaning] A satisfying W6636 outcome means the composed design is
  promising, not production-ready. It validates the architecture before the
  campaign spends heavily on protections that later phases may invalidate.
- [pass accounting] Preserve every deferred robustness outcome as a named
  later-pass Job. It is off the present critical path, not waived; promote it
  earlier only if its evidence shows the happy-path result would be false.
- [next handoff] Create separate M2 Jobs for the remaining negative/race
  endings, exact-ended restart adoption, and Podman certification. Carry
  forward their existing requirements and evidence references.
- [scheduling] Keep those hardening Jobs off the proof's dependency chain
  unless a precise invariant genuinely gates an honest next-stage result.
  Route non-overlapping leaves in parallel where worker capacity permits.

## 2026-08-28 — independent correction re-review and bounded decision

- [verified] The process-domain case now requires the private/default PID
  namespace and exact 512-process limit.
- [verified] The sibling-orphan case drives `OciAdapter.recover_credentials`
  over the adapter-owned home and rejects a successful no-op mutation.
- [terminal decision] Close W6636 satisfying in the approver's bounded sense:
  the positive one-container Docker capability pass is promising, not a
  production-readiness or hardening certification.
- [post-close coordination] Create separate M2 follow-up Work for the
  negative/race endings, exact-ended restart adoption and Podman certification,
  preserving the requirements and evidence recorded here.

## 2026-08-28 — terminal follow-up accounting

- [created] W32382 owns negative and race endings.
- [created] W32385 owns exact ended-runtime restart adoption before lane reuse.
- [created; park requested] W32391 owns real-engine Podman certification; its
  implementer Route must park it until a compatible engine is available.
