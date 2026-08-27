# Finding: deliver assignment identity to the artifact-neutral worker

Follow-up to closed Work W14251, discovered while W6633 implemented the
artifact-neutral OCI reference worker.

## Observed contradiction — 2026-08-26

The frozen version-1.0 documents require the execution worker to publish a
`baton.worker-manifest/completion` carrying the exact full `assignment_ref`.
That value contains the Work reference, participant and authority generation.

No frozen input surface delivers that value to the OCI worker:

- `/input/input.json` is `baton.worker-manifest/input`. Its schema and §8.1
  carry `work_ref` and explicitly carry no generation before claim; they do
  not carry `assignment_ref`.
- The separate `baton.worker-manifest/assignment` owns the post-claim full
  assignment identity, but §7.0 exposes no fixed path for that document inside
  the execution container.
- The revised `work` frame carries only the common worker-entry identity and
  no assignment member.
- The revised execution environment deliberately removed
  `BATON_WORKER_ASSIGNMENT`, and the remaining role/session values cannot
  derive participant plus authority generation.

Therefore a worker that consumes the valid frozen `inputManifest` cannot
author the required valid completion envelope. The current W6633 prototype
works around the contradiction only in its direct fixture: its test-only
`input.json` contains `assignment_ref` instead of the schema's required input
manifest members. A new additive test feeds the canonical valid W14251 vector;
the worker refuses it as `input` before agent dispatch.

This is a confirmed cross-contract defect. W6633 must not choose a third
unrecorded delivery shape to make its fixture pass.

## Decision boundary

Choose and pin exactly one post-claim assignment-identity delivery that the
execution worker can validate before dispatch and can copy into
`completionManifest.assignment_ref`. Align the normative specification,
schema, contract model, conformance vectors, worker-entry contract, manager
launch/composition boundary, W6633 direct and built-image suites, and W6634's
completion-to-receipt validation.

Candidate directions requiring an explicit ruling include:

1. a post-claim execution input manifest that carries the full
   `assignment_ref` (superseding the current no-generation input shape for
   that phase);
2. a fixed read-only path for the already-defined assignment manifest; or
3. an exact assignment identity member on the execution `work` request.

Do not revive opaque assignment environment strings or allow multiple
equivalent live sources. The chosen source must bind to the manager-minted
session/attempt and have one validator/ownership path.

## Acceptance

- One canonical contract-valid execution input reaches the agent and yields a
  completion envelope carrying the exact live assignment identity.
- A missing, stale, cross-session or cross-generation assignment identity
  refuses before agent dispatch or output publication.
- Input, assignment and completion documents remain closed and digest-bound;
  no compatibility alias or second identity source survives.
- All frozen schema copies, executable contract/conformance models, W6633
  direct/built-image tests and W6634 completion validation agree.

## Reviewer recommendation — 2026-08-26

**Proposed, awaiting approver ruling:** deliver the already-defined, complete
`assignmentManifest` to execution workers at the second fixed read-only input
name `/input/assignment.json`. Keep `/input/input.json` as the immutable
pre-claim input declaration and keep the `work` frame as the common identity
envelope only.

This changes §7.0 from two manifests to three protocol documents in the same
two filesystem roles; it does not create a third filesystem role. The manager
authors both read-only input documents at their proper lifecycle moments:
`input.json` before claim and `assignment.json` only after claim commits and
before the execution root is mounted. The worker authors only
`/output/output.json`.

The recommendation follows the existing ownership and chronology rather than
inventing a new identity shape:

- `assignmentManifest` already contains the exact `assignment_ref`,
  `runtime_attempt_id`, input-manifest digest, policy/profile digests, and the
  authority claim receipt binding. Its normative text already calls it the
  only manifest that unlocks writable execution and publication.
- Keeping `inputManifest` unchanged preserves its pre-claim immutability and
  its digest. Adding post-claim identity to it would either mutate the evidence
  after claim or require two documents with the same schema and different
  lifecycle meaning.
- Keeping assignment state out of the framed `work` operation preserves the
  worker-entry replay/session boundary and avoids making a filesystem-stable
  execution identity depend on one transport request.
- The execution posture already mounts the complete input root read-only while
  consent mounts nothing. No new mount authority or writable surface is
  introduced, and the assignment manifest contains no bearer secret.

The worker must validate both complete closed manifests and their digests
before dispatch, then cross-check at least: identical `work_ref` and
`assignment_contract`; the assignment's `input_manifest_digest` against the
exact `input.json`; and identical policy and runtime-profile digests. The
manager's launch/composition boundary must hold the same assignment document
against the runtime attempt and labels before mounting it. Completion copies
the one exact `assignment_ref` from `assignment.json`; the manager later
compares it with its owned assignment before custody mutation.

`assignment.json` and every descendant spelling become reserved under
`/input/`, exactly as `input.json` already is. A source descriptor cannot
replace or nest beneath either manager-authored document.

**Rejected alternatives in this proposal:**

1. Adding `assignment_ref` to `inputManifest` collapses pre-claim input
   evidence and post-claim authority into one mutable lifecycle.
2. Adding assignment identity to the `work` frame creates a second delivery
   surface and makes durable completion identity depend on transport replay;
   the canonical assignment manifest would still exist elsewhere.
3. Restoring an environment string is unstructured, opaque, and recreates the
   alias W14251 explicitly removed.

Exact affected contracts, validators, vectors, conformance cases, and
implementation consumers are mapped in
`evidence/assignment-delivery-boundary-2026-08-26.md`.

## Approver decision — 2026-08-26

Approved the reviewer recommendation. The manager delivers the existing
complete `assignmentManifest` at the fixed execution path
`/input/assignment.json`, alongside the unchanged pre-claim
`/input/input.json`. No environment value, framed-request member,
compatibility alias or alternate identity source is accepted.

The lifecycle clarification is normative: `input.json` is immutable before
claim and its bytes/digest never change. After claim commits, the manager
materializes `assignment.json` and validates its binding to that exact input,
the minted assignment generation, runtime attempt, policy and profile. No
container observes the input directory during this transition. Only after both
documents are complete does the manager expose the whole `/input` surface to
the execution container read-only. Consent sees neither document.

The worker validates both closed manifests and their cross-document bindings
before agent dispatch, and copies the exact assignment identity only from
`assignment.json` into the completion envelope. The manager compares that
identity with its owned assignment before custody mutation.

## Independent review — 2026-08-27

**Observed, changes requested:** the first implementation does not yet enforce
the approved boundary.

The shared `check_input_pair` validator proves both documents' schemas,
self-digests and cross-document bindings. The execution worker does not call
that validator or implement equivalent validation: its `_document`,
`input_manifest` and `assignment_manifest` path JSON-decodes and shallowly
selects members, then `one_delivery` checks only Work, input-manifest, policy
and profile equality. Four additive direct-worker regressions show that a
false self-digest or an extra top-level member in either document reaches the
agent. This violates the approved closed-and-digest-bound prerequisite.

The manager composition helper also has only the input directory and the two
documents as operands. It can prove that the documents agree with each other,
but cannot compare the assignment document with the manager-owned minted
assignment generation or runtime attempt. No production source caller of the
helper exists. Consequently a self-consistent assignment document naming a
stale generation or another runtime attempt can be mounted and dispatched;
the current conformance cases detect those identities only at
`output.freeze`, after agent execution. That is later than the approved
pre-mount and pre-dispatch refusal.

The exact reproductions and gate results are in
`evidence/review-2026-08-27T00-40-45Z.txt`; the append-only review is
`review-2026-08-27T00-40-45Z.md`.

## Second independent review — 2026-08-27

**Observed, changes requested:** the worker validation, manager-owned
assignment/attempt checks, conformance timing and ordinary-command bytecode
fix now satisfy the first review. The launch integration still does not prove
that the root it authenticated is the root it exposes.

`request_runtime_start` validates its `inputs` operand, then calls
`adapter.start` with only labels and an operation identity. The production
`OciAdapter` ignores that authenticated path because it owns an independent
constructor-time `mounts` tuple and passes that tuple to `run_vector`.
Consequently the manager may authenticate root A and start a runtime mounting
root B, no input root, or an input root at a target other than the normative
fixed `/input`. The manager's checks and the worker's checks can each be
correct while applying to different directories.

An additive manager regression configures the adapter to mount the sibling
workspace at `/input`, asks the launch path to authorize the valid composed
input root, and requires refusal before journalling or adapter invocation. The
current path starts successfully. Details are in
`evidence/review-2026-08-27T01-34-52Z.txt`; the append-only review is
`review-2026-08-27T01-34-52Z.md`.

## Third independent review — 2026-08-27

**Observed, changes requested:** the authenticated root now crosses the seam
and the OCI adapter requires its exact read-only `/input` bind. The early
pre-journal check still validates normalized results instead of canonical
spellings.

`_plan_agrees` calls `normpath` on the target before deciding that it is
`/input`, and `realpath` on the source before comparing it with the proved
root. Those operations erase `..`. A declared `/else/../input` target or an
`inputs/../inputs` source therefore passes the manager's early plan check, the
start operation is journalled, and the adapter is invoked. OCI's own boundary
correctly refuses both spellings later, but that is precisely the post-journal
refusal the second review required the declared-plan check to avoid.

Two additive regressions require both noncanonical spellings to refuse before
adapter invocation or journalling; both currently fail. Details are in
`evidence/review-2026-08-27T02-00-13Z.txt`; the append-only review is
`review-2026-08-27T02-00-13Z.md`.

## Fourth independent review — 2026-08-27

**Confirmed, signed off:** the canonical source and target rules now have one
owner and are called by the manager's pre-journal plan check, the adapter's
authorized-root check and the final OCI vector construction. Both traversal
regressions refuse before adapter invocation and leave the attempt
`not-started`.

The complete accumulated acceptance is now satisfied: the fixed
`/input/assignment.json` is delivered beside the immutable input manifest;
both documents are closed, self-digest-bound and cross-checked before agent
dispatch; manager composition and launch bind them to the live assignment,
runtime attempt and claimed input; the exact authenticated root is the one
mounted read-only at `/input`; and completion copies the delivered assignment
identity for the manager's existing custody check.

Independent verification is in
`evidence/review-2026-08-27T02-39-25Z.txt`; the append-only signed-off review is
`review-2026-08-27T02-39-25Z.md`. The daemon-backed gate remains unavailable
to this managed reviewer, but the implementer recorded 37/37 and the relevant
source-level, cross-component and exact-argv gates are independently green.
