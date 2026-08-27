# Assignment-delivery boundary research — 2026-08-26

## Existing normative facts

- Worker-control `SPEC.md` §7.0 fixes two filesystem roles: read-only
  `/input/` and writable-then-frozen `/output/`. It currently names only
  `input.json` and `output.json`.
- §8.1 defines `inputManifest` as pre-claim input evidence carrying `work_ref`
  and explicitly no assignment generation.
- §8.2 defines `assignmentManifest` as post-claim, carrying the full
  `assignment_ref`, `runtime_attempt_id`, exact input/policy/profile digests,
  claim receipt digest/sequence, and activation time. It says this is the only
  manifest that unlocks writable execution and publication.
- §8.7 and the schema require the worker-authored `completionManifest` to carry
  the exact full `assignment_ref`.
- W6633's artifact-neutral worker-entry revision leaves `work` with only the
  common frame envelope and removes the former assignment environment value.
- The OCI execution posture mounts the complete manager-owned input root
  read-only; consent mounts no assignment input. Therefore another fixed file
  inside the same input root needs no new mount capability.

## Recommended ownership sequence

1. The input stager and manager freeze `/input/input.json` before claim and
   retain its exact manifest digest.
2. Claim commits and the authority/manager mints the existing canonical
   `assignmentManifest`.
3. The manager materializes those exact bytes as
   `/input/assignment.json`, verifies that the document binds the retained
   input digest and the selected attempt/delivery identity, and only then
   mounts the input root read-only into the execution posture.
4. The worker validates both closed documents, their self-digests and their
   cross-document equality before any agent dispatch.
5. The worker copies the one assignment manifest's `assignment_ref` into the
   completion envelope. The manager validates that envelope against the same
   owned assignment before freeze/custody.

The materialized file is a delivery of the canonical manifest, not a new
identity source. No environment alias or request-level fallback is accepted.

## Contract and evidence updates if approved

- Worker-control `SPEC.md`: explicitly supersede §7.0's "two manifests" text;
  name `/input/assignment.json`, its author/lifecycle, and the two-document
  validation rules. Reserve `assignment.json` and descendants in §7.1.
- Every `worker-control-1.0.schema.json` copy: the assignment manifest shape
  need not change, but all copies and equality checks remain part of the gate.
- Contract model/vectors: add a canonical valid assignment manifest and paired
  input/assignment validation; add missing/malformed/digest/work/policy/profile/
  attempt/generation negatives.
- Runtime-conformance SPEC, builder, cases and obligations: prove consent sees
  neither input document; execution sees both read-only; the assignment file
  appears only after claim; a stale or mismatched file never reaches the agent
  or completion publication.
- Manager composition: materialize the exact document before execution mount,
  hold it against the runtime attempt and OCI labels, and never edit either
  input document after mount.
- W6633: read and validate both files; remove the invented `assignment_ref`
  member from its input fixture; copy identity only from assignment.json.
- W6634: keep comparing completion identity with the manager-owned assignment
  before custody mutation; add wrong-file/cross-generation integration cases.

## Alternatives and their costs

### Mutate or replace inputManifest after claim

This conflates a pre-claim declaration with post-claim authority and breaks the
meaning of `input_manifest_digest` in the assignment manifest. Preserving both
versions would create two lifecycle meanings under one schema name.

### Put identity in the framed work request

This makes the same assignment identity live both in the canonical assignment
manifest and in a transport operation. It also couples completion authorship to
the replay/session behavior of one request even though the execution input and
result survive that request.

### Environment delivery

The removed environment member was an opaque string with no manifest digest or
cross-document validation. Restoring it would be a compatibility alias and a
second source of truth.
