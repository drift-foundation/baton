# Deliver each created Job task through owned worker inputs

2026-10-26 — bounded prerequisite discovered under W361912 R3, handoff E363053.
Parent: baton:work/records/2026/10/finding-v12-template-job-creation.

**Confirmed:** candidate362931 retains caller statement/acceptance/work scope in
creation provenance, but derives input identity and Work from installed workers.
single_worker.py:338 reads task_document at static preflight;
stage_execution.py:1315 forwards worker.given task_bytes. human_contract remains
inside job_input_identity. Changing only the Job digest makes the selector refuse.
The five diagnostic cases in candidate362931 test_creation_ports establish static
source facts and selector refusal; they are NOT a connected execution rehearsal.

**Existing authority:** DESIGN SCH-1a requires ordinary task/source/scope/acceptance
creation with manager-owned admission, no operator-authored manifests or bespoke
packets; deployment supplies workers/credentials/capacity. Parent FINDING already
requires requested inputs to reach substantive simulated work. AGENTS Sep28 says
necessary file selection is an implementation choice, not an extra permission gate.
Moving task composition behind the owning API implements this accepted outcome.
No spec adjustment is selected. E363053's claim that choosing task-document storage
necessarily needs an owner ruling is not established by a conflicting requirement.
If an actual normative conflict appears, identify both exact clauses and the
proposed change before proceeding with that change. Do not weaken digest checks.

**Bounded outcome:** an owned per-Job input/task composition path delivers the
selected task, acceptance and scope with truthful source/input provenance to its
serving implementation/review stages, without rewriting another Job's installed
inputs. Reuse existing source, manifest validation, workspace and stage ownership.
Storage location and necessary internal interfaces are implementer choices.
No general workflow framework or deployment redesign beyond this outcome.

**Acceptance:** two distinct requested tasks on one configured worker pool receive
their own immutable task bytes and matching input identity, including after restart;
no cross-Job contamination. Drive the real owning composition/selection/context
boundary with deterministic provider/engine substitutes; inspect delivered task
content, not source strings alone. Tampered/missing/mismatched task/input refuses
before launch; caller cannot supply an unvalidated internal manifest. Preserve
source/result attribution, review isolation and existing supported installed-task
behavior. No live provider/engine, deployed-instance mutation or Git mutation.

**Ownership and provenance:** parent candidate362931 manifest
02090c1c505a055722e15de6c3e06f3e9ed0b940619055a69253549a0169fc9b is an
unintegrated working baseline, NOT accepted delivery. Start a separate immutable
child candidate over that exact overlay and base19f02ce1295b4517a85f0822d48754efc982f388;
record inherited versus changed bytes. Sole implementer owns child candidate/tests/
PROGRESS and necessary product changes in isolation. Parent execution is gated;
there is no parallel shared-file writer. Reviewer owns FINDING/PLAN/reviews/evidence.
Implementer chooses actual paths and records them; bootstrap/single_worker/
stage_execution/manifest are evidence locations, not an exclusive edit list.

W361912 consumes independently reviewed child delivery and owns the joined actual
create-command, replay/interruption/binding, review/correction/held and OBS-0 proof.
W321608 retains final workflow acceptance. Child success alone closes neither parent.

## 2026-10-26T20-10-02Z — composition partial; delivery continuation

**Confirmed:** review-2026-10-26T20-10-02Z.md verifies candidate363069 member hashes and
104 focused passing tests. Actual implementation/review input-root and context
delivery remains installed-task based at the code points in the review. No child
acceptance or integration approval. **Required:** connect the same per-Job task/
manifest through claim, input publication/proof and context; verify two-Job
isolation, restart and refusal behavior at the actual delivered-byte boundary.

**Decomposition:** retain this bounded consumer wiring in W363066, rather than
splitting a helper from its first meaningful consumer. Parent W361912 stays gated.
No new owner decision or broader execution selected. Sole implementer owns isolated
candidate/tests/PROGRESS; reviewer records/evidence. Prior queued plan status is
superseded by implementation-continuation after partial review.

## 2026-10-26T20-28-59Z — completion claim disproved at connected boundaries

**Confirmed:** review-2026-10-26T20-28-59Z.md records R1 _matches refusing new Job input and
R2 real assignment/_input pair validation failing with different input digests.
Independent probe and 147 passing focused cases are in evidence/review-363353.
Attempt, adapter and launch-context installed-manifest reads also remain. This
supersedes E363350 blocker-closed status; candidate363241 is not accepted.

**Required continuation:** carry one consistent stage manifest/task through all
owning preparation consumers, verify the connected path using deterministic normal
provider/engine boundaries. Helper-only delivery tests bypassed the observed defects.
Retain one serial Work because these are coupled identity consumers, not separable
parallel outcomes. Parent W361912 remains gated; no new owner approval is needed.

## 2026-10-26T20-45-45Z — specific input mismatches corrected; recovery open

**Confirmed:** review-2026-10-26T20-45-45Z.md verifies candidate363375 hashes and 130 focused
passes. Updated production-operand probe succeeds for match and input-pair creation.
Earlier two counterexamples are corrected. Adapter recovery callers still use
installed manifest when stage is absent; this remains child acceptance, not an
optional limitation. Tests manually compose part of preparation and do not yet
exercise actual runtime preparation/recovery entrypoints. No child acceptance.

**Continuation:** complete bounded recovery identity propagation and connected
deterministic verification in this same Work; splitting would separate consumers
of one identity invariant. W361912 remains gated, with its acceptance unchanged.

## 2026-10-26T21-26-14Z — recovery correction passes focused verification

**Confirmed:** review-2026-10-26T21-26-14Z.md verifies all 18 candidate363492 hashes and 137
focused passing cases, including deterministic production runtime cases. Child
acceptance still needs two Jobs in one loop, review-role runtime and crash/restart
adoption. These remain original scope. **Evidence correction:** claimed complete
substituted-pair test changes only input.json; establish the stronger case and
correct its narrative without erasing historical evidence. No integration approval.

Keep the finite remaining verification in this serial Work; W361912 remains
gated. No new owner decision or broader test campaign selected.

## 2026-10-26T21-47-24Z — restart and substituted-pair proof verified

**Confirmed:** review-2026-10-26T21-47-24Z.md verifies candidate363763 and 150 focused passes.
Whole-pair substitution and historical coverage corrections are satisfied; six
named crash/restart checkpoints now have independent passing evidence. Two-Job
pool and actual review runtime remain required. Bootstrap fixture limitations
do not waive them. Supported injected-checkout/pool seams are identified in the
review; no Git-mutation exception selected. No child acceptance. Keep remaining
pool proof serial and preserve W361912 dependency.

## 2026-10-26T22-08-43Z — runtime profile seam independently composed

**Confirmed:** review-2026-10-26T22-08-43Z.md verifies candidate363909 and 158 focused passes.
New tests prove mounts/checkpoints but do not start pool runtimes. Independent
probe composes three real pool workers with injected deterministic checkpoint
profile and a Git-process guard; evidence/review-364036/POOL-PROFILE.txt. This
is a concrete continuation route, not acceptance of either pending runtime case.
E364034 headline completion is not supported by its stated execution boundary.
Retain serial Work and parent dependency; no owner permission gate is required.

## 2026-10-26T22-34-25Z — pool guard fixed; two runtimes independently observed

**Confirmed:** review-2026-10-26T22-34-25Z.md verifies candidate364051 and 165 focused passes.
Real loop exposed /1 binding task suppression, now corrected. Reviewer independently
ran both created Jobs using existing _ConcurrentEngine: two distinct starts/runtimes,
each actual task file equals its own created Job task. Evidence/review-364216.
The assertion that no multi-container fixture exists is superseded by this evidence.
Remaining milestone: incorporate concurrent regression and prove started review
runtime through serving loop. Preserve earlier proofs; no child acceptance yet.

## 2026-10-26T22-48-40Z — concurrency verified; synthetic publication fixture authorized

**Confirmed:** review-2026-10-26T22-48-40Z.md verifies candidate364233 and 166 focused passes.
Concurrent success regression and prior coverage correction are satisfied. Review
probe defers because directory-result fixture does not meet git-change-proposal
publication contract. **Clarification:** labelled synthetic provider/publication
fixtures are within existing deterministic verification/test authority, not invented
live evidence. Necessary bounded test seams do not require a new owner decision.
No Git exception or spec change selected. Real review runtime remains required;
parent gate preserved. See review for existing publication seam and fixture examples.

## 2026-10-26T23:06:29Z — bounded child accepted independently

Claim364437 accepts candidate-364329 for parent joined acceptance; see review-2026-10-26T23-06-29Z.md.
169 focused tests pass in 7.672s, all 18 candidate hashes checked. Review runtime
now starts through the loop with requested task and durable matching identity.
This supersedes the outstanding final fixture correction, preserves prior history,
and does not approve inherited W361912 bytes for import or the parent workflow.
Passing accepted delivery to baton.decide; parent dependency remains until owner disposition.
