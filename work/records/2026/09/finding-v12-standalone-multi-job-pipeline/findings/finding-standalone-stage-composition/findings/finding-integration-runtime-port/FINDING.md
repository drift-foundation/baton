# Production integration runtime port

Ledger Work: W110774. Created 2026-09-07 by baton.codex from W103083
handoff M110672. Parent: standalone stage composition.

**Confirmed:** `v12/python/tools/stage_execution.py` constructs
`Integration(deployment, integration_port)` with a default None; the public
factory supplies no port. `Integration.run` therefore refuses every integration
stage. The accepted `integration.execution.integrate_next` types and invokes
`port.run(delivery, assignment)` after lease, assignment and delivery proofs.
`integration.runtime` supplies immutable assignment/delivery/result boundaries,
not a production process that consumes them. Only focused-test fixtures supply
the run operation. A fake port would not complete the required deployment.

**Proposed, pending interface/path review:** provide a small deployment-side
module (candidate `v12/python/tools/integration_worker.py` plus a focused new
test module) that composes the accepted OCI, credential, launch and runtime
observation APIs over IntegrationDelivery and its exact fenced assignment.
Revalidate existing worker capabilities before choosing the final path set;
report any absent lower interface separately. Reuse the established boundaries
instead of cloning single_worker or weakening the serialized integration driver.
Shared stage_execution wiring remains the assembly author's path.

**Required result:** start exactly the assigned integrator over its accepted
delivery, with correct read-only candidate inputs and bounded writable target
posture, distinct identity/credentials and durable runtime observations.
Recover an already-started delivery without launching a duplicate. The
integrator's claimed result remains untrusted until the existing driver reads
it and checks positive runtime quiescence and the live grant. Preserve an
uncertain/interrupted integration as operator-held; do not add automatic
recovery, Git mutation authority for agents, or a success-reporting stub.

**Verification proposal:** deterministic runtime evidence at the actual run
boundary, exact assignment/delivery correlation, duplicate-start refusal/adoption,
wrong-fence refusal before writable exposure, and one uncertain outcome left
held. New focused tests are additive; pin any existing-test mutation explicitly
before implementation. The full one-Job lifecycle and final two-Job proof stay
with their existing owners.

Discovery evidence: `../finding-shared-stage-assembly/PROGRESS.md` (M110672),
`../finding-shared-stage-assembly/review-2026-09-07T14-12-42Z.md`, and its
`evidence/review-110736/candidate/` snapshots. Generic runtime-boundary Work
W101490 is closed satisfying; this is its missing deployment consumer, not a
reopening or rejection of that accepted boundary.

## 2026-09-07 — concrete runtime research, claim 110914

**Observed:** the retained executable baseline at
`evidence/research-110914/baseline.py` calls the public OCI `run_vector` against
a disposable ControlStore and configured workspace group. Both separate target
and integration-result writable mounts refuse `policy/denied` because they are
outside the ordinary inputs/workspace roots. No engine executes. The same probe
shows that `prior_runtime_witness` refuses an absent integration attempt.
`baseline.json` captures those outcomes and SHA-256s of eleven inspected files.
The probe establishes current boundary behavior, not the impossibility of an
explicitly reviewed extension. Its first two invocations failed due to reviewer
fixture mistakes (missing clock operand, then missing milliseconds); both were
corrected before collecting the successful result. Neither was a product defect.

**Confirmed:** W101490's accepted finding explicitly separates integration
assignment/result from the immutable input pair, mutable workspace and ordinary
command/events protocol. Current `OciAdapter` and `run_vector` accept credential,
launch/exchange and nominated-source deliveries, but no integration delivery.
Their ordinary root and mount rules cannot simply be widened by this deployment
composer. Appending raw mounts after validation or assigning a common host
ancestor as workspace would evade the boundary rather than implement it.

**Confirmed:** no program in `v12/worker/` consumes the integration assignment
schema or produces its result schema. The selected recipe runs
`dogfood_entry.py` with `ClaudeAgent`, whose current work is implementation;
W110772 independently owns its planned review extension. A callable host port
and a container start cannot by themselves make an integrator workload exist.
The accepted integration execution fixtures perform real disposable filesystem
changes but deliberately start neither a runtime nor a provider.

These missing lower capabilities are now separately recorded:

* W110934, `work/records/2026/09/finding-v12-integration-oci-delivery/`:
  research and deliver the typed OCI integration delivery/target-access boundary.
* W110935, `work/records/2026/09/finding-v12-integration-worker-workload/`:
  research and deliver the concrete integrator workload, evidence/instruction
  input and image-entry contract, with disjoint ownership from W110772.

They are ledger children with top-level dossier paths to avoid a third record
nesting level. Neither reopens the accepted W101490/W101492 Work. No workaround
was applied and no protocol/application source changed during this research.

### Assembly preparation and continuation obligations

**Confirmed:** `StageExecution.launch` sends integration directly to
`Integration.run`, which calls `admit_accepted`. It bypasses `_SingleWorker.start`,
where attempt creation and Authority assignment activation normally occur.
`ManagerOperations.launch` delegates preparation rather than creating it, and
`integrate_next` calls `_unstarted` before invoking the runtime port. Therefore
preparing the attempt inside `port.run` is too late: the accepted driver needs
that durable not-started attempt before calling the port. The current assembly
must add this preparation explicitly using the manager's public owners.

**Confirmed:** `run` is documented to return after asking, not after completion.
`settle_observed` handles a normal still-running attempt; however,
`admit_accepted` re-entry with an existing delivery and a runtime other than
not-started calls `hold_interrupted`. Blindly re-entering admission on each tick
is not a normal asynchronous completion path. The shared serving layer also
must project integration delivery observations rather than require an ordinary
worker-exchange terminal which that workload does not produce.

**Open serving decision, owned by W103083:** bind an explicit normal live
observation/settlement path to the current serving execution, preserving the
accepted manual-hold path on process restart or uncertain runtime state. Do
not silently make every model invocation synchronously block the multi-Job
scheduler or reinterpret every running attempt as interrupted. The required
behavior is concrete even though shared factory/observer changes remain that
author's: ordinary progress can finish, a restart cannot launch or resume a
second writer, and independent stages remain schedulable. Record the chosen
boundary before implementing it.

### Proposed port contract after the prerequisite interfaces are accepted

This section supersedes the initial assumption that a two-file composer could
already be implemented entirely over available runtime capabilities. It pins
the deployment responsibilities without inventing missing lower APIs.

Keep `IntegrationRuntimePort.run(delivery, assignment)` as the accepted core
seam. A deployment-side `prepare(stage, job)` operation must first read the
exact claimed integrator assignment and record/activate its manager attempt
using `record_attempt` and `activate_assignment`; it starts no runtime and
does not grant a coordinator lease. The shared assembly calls this before
`admit_accepted`. Port construction receives already-resolved stores, restricted
Authority port, certified identity/profile, credential provider/home, configured
workspace group/storage, selected engine/image/network and the accepted typed
target/evidence/instruction bindings. Do not infer ambient identity or host
paths from the assignment's opaque target id or profile word.

At `run`, adopt the exact typed delivery with `runtime.adopt_delivery`, compare
its published assignment, and recompute the current assignment with
`runtime.compose_assignment`. Compare the whole assignment, including attempt,
lease, entry, fence, participant, profile/version and instructions digest.
The lower OCI boundary must preserve this proof through final writable exposure.
Resolve read-only approved candidate evidence from accepted custody; instruction
bytes must match the profile digest. Expose only those inputs, the fixed
read-only assignment, fixed writable result and exact granted target, plus the
existing isolated credential/scratch/launch surfaces. Reuse owner-journalled
start and reconciliation operations rather than a second runtime ledger.

Runtime refresh is an explicit deployment observation operation using the
accepted OCI evidence and `reconcile_runtime`. It starts nothing, mints no
credentials and never infers quiescence from a result file, provider exit code,
silence or a failed engine lookup. A pre-mutation refusal which never started
a runtime still needs positive manager reconciliation to destroyed before a
successor grant can pass its predecessor gate; W101492 explicitly records this.

The original phrase "recover an already-started delivery" means inspect/adopt
identity and preserve evidence without another start; it does not authorize
automatic recovery of an interrupted writer. Normal result adoption uses
`runtime.observed_delivery` and the accepted settlement driver. The port never
authors an integrated result, records an Authority receipt, releases a lease,
repairs target bytes or declares success from process status. Missing, partial,
foreign and uncertain results retain the exclusion for operator action.

**Proposed W110774 path set:** new `v12/python/tools/integration_worker.py`,
new `v12/python/tests/tools/test_integration_worker.py`, and only the additive
test-registration entry in `v12/python/tools/parallel_test.py`. Revalidate these
paths once W110934/W110935 name their accepted interfaces. Core OCI changes
belong to W110934, worker/recipe changes to W110935, and shared
stage_execution/factory/observer tests to W103083. No concurrent shared-path
edits or existing-assertion changes are granted by this inventory.

Acceptance must use the real port, accepted OCI start/reconciliation and real
worker/result boundary with deterministic engine/provider seams. Prove actual
candidate bytes imported to a disposable target, measured post-import bytes
and modes, the exact correlated result, positive post-write runtime quiescence
and live grant before settlement. A fake result writer alone is insufficient.
Focus on wrong fence/attempt/profile before exposure, independent credential
identity, duplicate-start refusal/adoption, normal asynchronous completion,
restart/uncertain hold and pre-mutation refusal preserving every target path.
Keep exhaustive later races in the existing hardening record. Run the focused
module and canonical Python subtree gate for the implementation candidate;
this research ran only the baseline and whitespace checks.

Implementation is gated on W110934/W110935, with the explicit serving
preparation/continuation decision coordinated to W103083. No production runtime,
image selection, live model invocation or canonical-target mutation is proved
or authorized by the research result.

**Operational lookup note:** guessed `job_manager/pooled.py` and
`job_manager/operations.py` paths did not exist. Discovery located the classes
in `job_manager/delegation.py`; all conclusions use that actual owner. Every
required policy and bound dossier file was readable.

## 2026-09-08 — approved normal-continuation extension and handoff

Slawomir approved the public normal-continuation operation, working name
continue_accepted, within W110774 after discussing the exact operation and its
distinction from initial admission and restart recovery. This supersedes the
earlier three-path-only composer inventory and the assumption that deployment
can finish normal observation/settlement entirely through already public APIs.
The source revalidation and required port/assembly contract are recorded in
HANDOFF-CONTRACT-2026-09-08.md; that file is part of this accepted scope.

The additional paths under v12/python are src/baton_v12/integration/driver.py,
src/baton_v12/integration/__init__.py and additive regressions in
tests/integration/test_driver.py. Preserve every existing assertion and existing
restart/uncertainty behavior. The operation never launches or retries a worker:
it advances only an integration already started by this live serving execution,
revalidates assignment/delivery/account/live grant, waits for valid completion
and positive quiescence, then reuses the driver's Authority receipt/read-back
and settlement/release ordering. No private-helper copying or second ledger.

W103083 owns the shared factory/tick/status wiring; W110774 owns the port and
public completion operation. The shared parallel_test.py registry path is serial:
W110774's additive entry precedes W103083 edits. Independent review and all live
provider gates remain required. This coordination adds no new Work or test run.

## 2026-09-08 — provider acceptance revalidated, claim 115095

**Confirmed:** owner close112242 accepted W110934's bounded OCI capability at
`baton:work/records/2026/09/finding-v12-integration-oci-delivery/review-2026-09-07T17-17-06Z.md`.
Owner close115092 accepted W110935's final workload at
`baton:work/records/2026/09/finding-v12-integration-worker-workload/review-2026-09-08T01-17-01Z.md`,
including its joined technical review `review-2026-09-08T01-11-08Z.md`.
These acceptances satisfy the earlier research prerequisite gate. They do not
waive historical broad-test failures or authorize a live image/model/target run.

**Observed:** `evidence/research-115095/audit.json` measures all sixteen unique
provider paths against their accepted hashes; all match. The shared registry
uses W110935's later accepted hash, explicitly superseding W110934's historical
registry baseline for this handoff. The same evidence captures all six approved
implementation paths: the two proposed port/test files remain absent and the
four existing files have measured baselines. No production code or existing
test was edited and no suite was run in this handoff revalidation.

**Confirmed interface map:** `integration/oci_delivery.py:compose_mount_boundary`
accepts store, manager, profile, delivery, assignment, typed target and group;
it re-adopts delivery, compares the complete published/fresh assignment and
proves target posture. `worker_manager/oci.py:OciAdapter` accepts that capability
as `integration_delivery`, alongside accepted source, launch and isolated
credential deliveries. `worker_manager/attempts.py` owns `record_attempt`,
`activate_assignment`, `request_runtime_start` and `reconcile_runtime`.
`tools/integration_bundle.py:compose_bundle` consumes the accepted owners,
checkpoint/integration profiles, assignment, launch, instructions, line/proposal
and read-only object runner; it returns the nominated source, measured manifest,
bundle/envelope digests and eligibility. Use its accepted schema /2 authority
evidence rather than reconstructing an older schema /1 bundle.

**Confirmed continuation boundary:** current `driver.admit_accepted` still
dispatches a previously started runtime to `hold_interrupted`, and its receipt
read-back plus `complete_integrated` ordering remains inside the driver. There
is no exported continuation operation. The approved extension is therefore
still required. A live local marker binds the whole assignment and delivery,
is established only by the validated start path and is lost on restart or
uncertain start; it is bookkeeping, never a substitute for owner revalidation.

**Assembly handoff:** W103083 must call preparation before admission, select
normal continuation only for that live marker, and preserve observation-only
status. Its current `Integration.run` also omits the driver's required
`required_tests` operand; supply the accepted configured requirements in that
existing assembly call site. This is an observed assembly obligation, not an
expansion of W110774's six-path inventory. Keep the unrelated-stage/tick proof
split at the contract's W103083 ownership boundary.

**Disposition:** implementation-ready under the approved
`HANDOFF-CONTRACT-2026-09-08.md`, with bounded deterministic composed evidence
and the required canonical gate for the assembled candidate. Claim and
revalidate before editing; return to independent review with exact signatures,
configuration/refusal rules, candidate hashes, verification and consumer call
sites. No further prerequisite or research campaign is needed.

**Operational lookup note:** guessed `worker_manager/lifecycle.py` and
`worker_manager/runtime.py` were absent; actual lifecycle owners were located
in `worker_manager/attempts.py`. This was reviewer lookup misuse, not a missing
provider. Required policy, dossier, contract and accepted evidence were readable.

## 2026-09-08 — composed port review, claim 115316

**Observed:** implementation claim115239 supplies all six approved paths,
superseding the prior observation that the port module is absent. The required
real start/worker/target/receipt/settlement proof remains undelivered, explicitly
acknowledged by return115313. No provider acceptance follows from file presence
or the reported 21 configuration/preparation/refusal cases.

**Confirmed findings:** `review-2026-09-08T02-07-47Z.md` records the missing
configured target identity check, uncertainty invalidation using a nonexistent
reconciliation-result field, and observation locators incorrectly dependent on
the live continuation marker. `evidence/review-115316/audit.json` pins candidate
hashes and two bounded public-document consumer probes; both uncertain shapes
leave the marker live. Observation without the marker refuses before any
retained owner read. The target-binding finding is source analysis, not an
executed foreign-target import.

**Required correction:** preserve an independently configured typed target and
stable observation locators, invalidate continuation using accepted current
owner evidence, and finish the originally approved composed acceptance proof.
These clarify enforcement of the existing handoff contract within its six
paths; no new recovery/start/target-selection authority or existing-test
assertion mutation is granted. PLAN names this review as currently actionable.

## 2026-09-08 — composed proof and remaining gaps, claim 115440

**Confirmed progress:** claim115345 corrects the configured target-id check and
stable observation locators. The real composed fixture now starts through the
port and OCI boundary, runs the worker through deterministic seams, observes
quiescence and completes an integrated settlement/release. This supersedes the
earlier observation that no composed positive proof exists. The nominal public
uncertainty-document branches now invalidate the marker as required.

**Confirmed remaining findings:** review-2026-09-08T02-29-59Z.md and
evidence/review-115440/ retain the exact candidate and bounded probes. Missing
credentials still reach engine start; failure while constructing the observing
adapter retains continuation permission. Real repeated continuation refuses at
an immutable approval receipt. An injected interruption after settlement and
before release demonstrates that both continuation and restart then refuse
before terminal dispatch, stranding the live exclusion on an integrated entry.
No real engine/provider or repository target was used in these reproductions.

**Test-scope finding:** the author interprets the preceding PLAN source
correction as authority to change existing test expectations, despite the
explicit restriction in its owning review and FINDING. Three existing port
test expectation/interface replacements, an additive case and the driver's
shared fixture capability addition are enumerated in the newest review. The
83 driver test method ASTs are unchanged. No assertion was changed by review.

**Proposed, pending owner ruling:** schedule the exact three test replacements
named in that review, tighten the named repeated-tick test to require the
accepted terminal result, and adapt the composed fixture to supply valid
synthetic credentials. Accepting those bounded changes would permit the
existing-scope technical corrections to proceed without weakening unrelated
tests. This is not a confirmed ruling, candidate sign-off or live-run authority.

## 2026-09-08 — owner test-scope ruling pinned by reviewer claim 115584

**Confirmed:** Slawomir approved the exact proposed owner disposition of
review-2026-09-08T02-29-59Z.md in reroute115487, before implementation claim115496,
and reiterated it in response M115526 to M115499. This explicitly supersedes the
preceding "Proposed, pending owner ruling" status. The three named port-test
replacements are accepted at the bytes retained by review115440; the driver's
fixture integrate capability, tightening the repeated-terminal-tick test and
valid synthetic credential fixture are authorized within the existing six paths.
All other existing assertions remain protected. No closure or live deployment
was authorized.

The owner instructed that this ruling be pinned before further test edits.
At review115584 it was still absent from FINDING/PLAN, and PROGRESS still said
the ruling was pending. This entry pins the already-issued authority and records
the late durable update explicitly; it does not invent a new approval or rewrite
the historical test-scope finding. The author's new strict repeated-tick case
is additive; retaining the older case does not remove that new strict coverage.

## 2026-09-08 — pre-start refusal ending, review claim 115584

**Confirmed:** review-2026-09-08T02-53-32Z.md verifies the corrected terminal
release-tail replay, required credential delivery and whole-observation marker
invalidation. It supersedes those three open findings from review115440 at the
exact candidate hashes in evidence/review-115584/audit.json.

**Observed remaining gap:** an unavailable credential provider refuses before
engine start, but after the target lease and delivery are created. The entry
remains leased and the manager runtime not-started. A subsequent public refresh
cannot prove absence from an empty engine listing and records uncertainty.
The retained probe shows zero starts, unchanged target and no positive
quiescence ending for the predecessor gate. This is the unimplemented ending
half of the original pre-mutation-refusal acceptance requirement. The owner
must not infer quiescence or automatic retry from those observations.

**Required:** complete the bounded public-owner preparation/refusal ending or
change the ordering so fallible preparation cannot strand the acquired target
lease. Investigate the existing preparation-failure owner without mistaking its
record for cleanup/absence authority; identify a missing lower capability
explicitly if the accepted owners cannot compose the required proof. PLAN names
the exact review, and unchanged positive/replay evidence remains reusable.

## 2026-09-08 — preparation ordering and replay, review claim 115669

**Confirmed:** moving credential retrieval into prepare avoids the unavailable
provider's leased-entry failure. The retained negative probe observes no
coordinator entry and runtime not-started. This supersedes that specific open
failure from review115584; no acquired target predecessor needs quiescence on
this path, and not-started must not be relabelled quiescent.

**Confirmed regressions:** review-2026-09-08T03-05-51Z.md records that repeated
prepare on an actually running fixture calls discard_orphan, remints credentials
and removes its live runtime-bound credential record. The owner requires stale
proof from its caller; the new helper assumes but never checks not-started.
The new refresh witness preflight also sits outside the invalidation boundary,
so a failed read preserves the marker. Evidence/review-115669/audit.json retains
both bounded probes and the exact candidate/log hashes.

**Required:** enforce public-owner preparation eligibility and exact replay
before any credential discard/materialization, and put every refresh witness
read inside the whole-observation invalidation boundary. Add bounded regressions
within the existing scope, preserve live credential custody and all established
restart/uncertainty exclusions. No new recovery authority or scope split is
proposed.

## 2026-09-08 — bounded provider approved, review claim 115739

**Confirmed:** review-2026-09-08T03-17-23Z.md independently approves the final
six-path candidate for owner acceptance. The exact hashes and retained files
are in evidence/review-115739/. The final probe demonstrates no discard/remint
or credential-record mutation on original-process running preparation replay,
safe refusal from a fresh port, and marker invalidation on witness-read failure.
This explicitly resolves the two open findings from review115669. The prior
composed import, quiescence, receipt/settlement/release and restart-tail evidence
remains applicable; all fifteen unchanged prerequisite hashes still match.

The owner test ruling remains exactly as pinned above. The final three test
additions preserve all previous 37 port and 83 driver test method ASTs.
No further implementation correction is requested. The review records the
constructor and W103083 consumption boundary plus the exact owner closure
operation. Required broad verification remains historically red (5082 tests,
11 failures, one error, 21 skips), explicitly unwaived. Approval is bounded
technical capability acceptance, not live image/provider or canonical-target
authorization. W103083 still owns serving assembly and its lifecycle proof.
