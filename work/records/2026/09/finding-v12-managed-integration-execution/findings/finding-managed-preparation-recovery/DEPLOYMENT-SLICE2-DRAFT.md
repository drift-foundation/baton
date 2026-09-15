# Managed preparation: slice2 documentation draft

Draft for serial integration by the owner of `baton:v12/python/DEPLOYMENT.md`.
This is review material, not a second shipped manual or deployment certification.
The main manual remains untouched. Current decisions: this record's FINDING
22:18:02Z,22:25:29Z,22:32:06Z,22:33:45Z and the parent SLICE2-SCOPE-165724.md amendments.

## Selecting the local preparation path

The stage-serving document selects this path with the boolean
`"integration_preparation": true`; omission or `false` keeps the existing direct
path. A string such as `"false"` is rejected. Selection requires the serving
deployment, integrator and configured integration worker, with its actual
Authority route/handler and ordinary runtime/input/output configuration.
Configuration selects behavior; it does not prove a runnable image is installed.
An already-claimed legacy parent cannot be converted into a concurrent child.

`v12/worker/Dockerfile.reconciliation` is the preparation recipe. It requires an
explicit selected `PROVIDER_BASE`, copies the ordinary worker and preparation
entry/workload, and selects UID/GID65532 and an exec-form Python entrypoint.
The base must supply compatible Python and Git tooling. This qualification used
no image build, pull, actual engine operation or live model. The recipe has no
certified production digest from this work; provisioning and OCI certification
must not be inferred from deterministic process tests.

## What a successful preparation means

The existing scheduler reserves one integration actor. The composition registers
one root and planned prepare/apply memberships, commits the immutable preparation
intent, then creates the child Work with its replay identity. The child uses its
own ordinary offer, claim, attempt, fixed assignment and committed admission
before runtime start. The parent apply stays planned and unclaimed.

Read-only accepted objects and a measured immutable request travel through the
ordinary worker input boundary. The preparation worker derives combined/base/
isolated trees and runs the configured causal harness in its own execution
context. The coordinator does not perform that merge or harness execution.
Commands retain the original Job's `host_verification` boundary: default300s,
with an explicit `verification_command_seconds` override taken from the sealed
Job-owned launch. Moving the workload does not select the imported verification
default1800s or change the provider default3600s. These are per-command limits.

The ordinary worker measures outputs. The manager positively quiesces the runtime,
freezes output, accepts intake, retains local custody, hands off the child and
completes cleanup. Adoption checks the retained report/candidate, request, task,
assignment, source and harness bindings; it can recover after execution roots
are gone. A worker answer, frozen output alone or a directly assembled report is
not accepted collection. A missing status is not exit0.

A successful slice2 finish is a retained, measured preparation account with the
prepare member ended, one root still held, apply planned and parent queued.
It is not an independent verdict, target update or whole-Job completion. Derived
judgment, apply and final root/failure settlement remain later delivery work.

## Failure and restart

Committed identities are replayed from owners after restart. Mismatching request,
child or owner evidence refuses; the composition does not mint replacement
identities to get past a failed replay.

When the failed-start receipt already identifies a runtime, the composition uses
the existing Authority cancellation/fence and failed-start cleanup owners. It
ends membership only after ordinary cleanup reports retained/complete. An
unfinished delivery teardown leaves membership available for retry, with the
root held and apply planned. This does not certify a generalized partial-delivery
recovery protocol.

When the failed start initially identified no runtime, automatic cleanup remains
unresolved. The ordinary sweep's action detail reports that a worker may still
exist and that **human inspection and cleanup are required**. It includes the
known Job, Work, attempt and start-operation identifiers, and identifies the
current runtime or says it is unknown. Inspect those exact identities through
the deployment's authorized owner/runtime surfaces and preserve the report for
manual recovery; an unknown runtime must not be treated as absent.

Restart preserves this report and the unresolved holds. No automatic late-runtime
attachment, cleanup convergence, abandonment or capacity-release procedure is
provided by this change. Later runtime visibility is new evidence; it does not
rewrite the original failure receipt or authorize a second launch. Human cleanup
execution and any subsequent release require their own existing operational
authority; this draft supplies no fabricated completion command.

## Qualification and deferred coverage

Evidence uses deterministic provider/engine simulation at normal boundaries,
real disposable Authority/Job/Control owners and actual separate worker/harness
processes. See ACCEPTANCE-172672.md for exact evidence scope and limitations.
It does not establish actual OCI behavior or model/provider-specific behavior.

The owner deferred unfinished partial-delivery protocol/recovery work and expanded
adversarial identity/artifact/custody, causal/timeout/limit and two-Job permutations
to v13. Existing checks and completed evidence remain; omitted cases are unproved,
not passed. Automatic late-identity design is superseded by the visible manual
recovery boundary. Existing direct/legacy tests retain their direct/legacy meaning.

Expanded uncertain-ending, leader-first and TERM-resistant cancellation/cleanup
scenarios are also v13/unproved under M172741/FINDING22:33:45Z. Existing shutdown
mechanisms/tests are retained; no additional shutdown campaign ran in this claim.
