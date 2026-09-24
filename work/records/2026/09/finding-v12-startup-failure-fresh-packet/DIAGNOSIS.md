# D1 — implementation rejected a review-only output declaration

2026-09-24, baton.tuner, W257627 claim257715. Awaiting independent review.

**Confirmed by deterministic reproduction:** both retained implementation
attempts are given only `findings` and `logs`, both required. The executed
image's adapter requires `proposal` for a multi-output implementation turn.
It raises `TaskRefusal` with this exact message before reading the task,
creating provider scratch, checking out source, reading credentials or starting
a provider:

> a implementation turn writes proposal and this assignment declares no proposal

The real image-matched worker exchange catches that exception and publishes
`fault_code=agent`, `answered=[describe]`, `ending=faulted`, null disposition
and manifest digest, then returns 1. The reproducer matches the entire retained
terminal and both operation-state documents for **each** attempt, including
command digest and correlation fields. The original exception text was not
retained; this is a causal reproduction from the retained operands and matched
source, not a recovered traceback or a newly executed container.

## Evidence and provenance

Retained instance: `/home/sl/baton-instances/two-jobs-251156`. EVIDENCE.json
records exact attempts, file hashes, declarations, terminal documents, log
capture states and source/image correspondence. Each staged `inputs/input.json`
agrees with its deployment input manifest. Both launches select implementation,
`baton.worker-launch/3`, with no provider context. Outcome remains held,
interrupted, with both attempts in outstanding_cleanup. D1 makes no cleanup or
current global runtime-quiescence claim.

Image is `sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2`,
reference `baton-v12-claude-worker:w239528-244216`. Read-only image inspection
still resolves that identity and the dogfood entrypoint. Existing
[IMAGE-ARTIFACT-244216.json](../finding-v12-single-implementation-proof/IMAGE-ARTIFACT-244216.json)
records file hashes measured inside that image; D1 reuses this historical
measurement rather than starting a container. All seven recorded worker files
match available source bytes now, including the adapter, worker harness,
entrypoint, schema and source-profile package. The test stages only those
hash-checked source bytes into a fresh temporary import tree, avoiding old pyc
loads. No reliance on a mutable tag alone or on unmatched current source.

The supported file-only attempt-log reader reports worker stdout/stderr and
provider stdout/stderr **absent**, with declaration `none`, for both attempts.
These are not completed empty captures. Source `baton_worker.serve_exchange`
intentionally suppresses exception text/type in its generic exception branch;
`_faulted` records only the closed fault code. That explains the lost diagnostic
without treating missing logs as proof of an authentication failure.

## First failing boundary and controls

`ClaudeAgent.work` selects `_selected(..., IMPLEMENTATION_OUTPUTS,
"implementation")` before `_read_task`. `IMPLEMENTATION_OUTPUTS=(proposal,)`;
`_selected` accepts the two known review names but finds no proposal and raises.
The actual `serve_exchange → handle → input_manifest/assignment_manifest →
agent.work` path is exercised with temporary copies of both retained deliveries.
No input/assignment validation fails before this refusal in either reproduction.

`test_startup_boundary.py` has four focused tests:

- Original declarations: exact TaskRefusal for both attempts; task reader and
  injected provider process seam never called.
- Real exchange replay: exact terminal/describe/work documents for both attempts,
  exit 1 and zero provider calls.
- Proposal added alone: still refuses required `findings`, which implementation
  does not produce. This rules out an incomplete one-field correction.
- Common proposal/findings/logs union with other-stage outputs optional: both
  implementation calls reach a sentinel at `_read_task`, with zero provider calls.
  This control proves passage past output selection only, not task, provider,
  reviewer, intake or Job success.

Command is the PLAN.md D1 unittest invocation, with a 30-second timeout and
5-second termination grace. Result: **4 tests passed, 0.022 seconds reported by
unittest**. No live provider, container start, store open, product edit or deployed
mutation. Image-inspect's initial optional Labels template failed because that
key is absent; a read-only full inspect succeeded. This is invocation misuse,
not a Baton incident or an unavailable-image finding.

## Origin and bounded next selection

Current `prepare_two_jobs.py:input_manifest` emits only required findings/logs;
its preparation uses that same manifest for implementation and review.
`two_jobs.py:_worker` deliberately carries the shared implementation manifest
into both stage deployments. The retained manifests establish the original bad
operands independently of those current files. Their correspondence identifies
the preparation boundary for correction; D1 does not modify either file.

Select a separate, owned correction to prepare a shared declaration union that
both stage adapters accept, with stage-specific production enforced by stage
results. Validate emitted manifests through **both** real adapter boundaries and
the relevant final-result/intake contracts before blessing packet bytes. Do not
merely make required outputs optional without checking those later obligations.
Preserve old manifests, consumed identities and evidence. A fresh packet must
bind its changed manifests/digests and the accepted limits/root-preparation
corrections. No new image is implied solely by this declaration mismatch.

Independent reviewer should assess this D1 result and pass to the owner before
selecting any correction or D2. W257624 still owns resource-hold recovery.
Authentication, task correctness, provider success and parallel acceptance are
not proved by this pre-provider reproduction. The observed mismatch is already
sufficient to explain these two failures; no live auth probe is needed for D1.
