# Isolated submissions and separately authorized integration results

Proposed by baton.codex under W131409 claim133017. Direction: owner M132985,
pinned in FINDING2026-09-10T03:05:47Z. This document and INTEGRATION-SCOPE-v1.md
require owner approval before replacement implementation. No runtime spent.

## 1. Two immutable objects and one target writer

An eligible submission is the producer's original proposal, original-base
checkpoint, frozen result, ordinary test evidence, independent accepted review,
policy approval and exact Job/Work/assignment identity. A checkpoint alone is
insufficient. None of those facts is rewritten because another Job integrated.
The producer's line, declared base, checkout, episodes and receipts remain
unchanged. No automatic target-driven producer/reviewer restart is introduced.

An integration result is a DIFFERENT immutable candidate: the selected eligible
submission reconciled with one exact current target snapshot, prepared in a
separate integration-owned workspace. It has its own content, provenance,
required tests, independent review, approval and publication. An old submission
base is allowed at this preparation boundary. A stale RESULT target is still
refused before import. Removing the final stale-target guard is not this design.

The integration role owns preparation through a configured capability. The
generic manager selects and coordinates owners; it does not run Git commands.
Only the existing target-global coordinator grants target write authority.
Preparation can read a pinned target snapshot without a target write lease;
import cannot begin without the exact live lease/fence and final target check.

## 2. Minimal first capability

Propose deterministic three-way reconciliation of one selected submission per
result. Import old base/candidate and current target into private integration
storage, apply the submission's net change against its original base, and retain
the combined commit/tree and target-relative path/mode set. Use configured Git
object operations; never reset or edit the producer line. Preparing several
submissions in one result and automatic semantic conflict resolution are outside
this first capability. Serial results still integrate both Jobs.

A clean textual merge establishes only prepared content. Every combined result
gets actual required tests and an independent technical review of its complete
target-relative changes before approval/import. Reconciliation that needs a
substantive human/model correction returns a specific held question, with the
original submission and attempted merge evidence. The responsible worker may
produce an explicitly requested correction; no manager invents acceptance or
silently resolves an ambiguous semantic conflict. Any corrected integration
candidate is a new identity and needs fresh independent review.

Missing target content, unproved source identity, unsupported path kinds, dirty
or replaced storage, conflict, missing evidence or policy mismatch holds/refuses
before target writes. Preserve the precise reason and all earlier evidence.

## 3. Integration-owned custody and replay

New owner module `baton_v12.integration.reconciliation`, backed by the existing
IntegrationStore journal and a new typed relation. Proposed schema5 fresh-store
boundary: old schema4 stores refuse; no migration/reset of live stores.

The public operations are conceptually:

- prepare_result(..., submission_proposal_id, line_id, attempt_id, target_id,
  target_source, profile): prove original eligibility and current fixed
  integration assignment, pin the target and intent, prepare/recover content.
- result_of(store, result_id): pure typed, journal-bound custody reader.
- record_result_evidence(..., result_id, verification, review, approval): consume
  actual independent owner evidence for the exact prepared result; no boolean
  approval supplied by a caller and no copied producer receipt.
- publish_result(..., result_id, publisher): publish/recover the separately
  authorized result using the existing Authority publication mechanism.
- resolve_import_account(..., result_id): revalidate original eligibility,
  result evidence, current policy and target for queue/import admission.

Exact signatures must pin injected owners and cannot omit the following fields:
schema/kind; result_id/operation_id; source Authority/Work/Job/line/checkpoint/
verdict/proposal/frozen-output identities and digests; original base and candidate;
integration fixed assignment/attempt; target_id, target revision and nominated
source path/device/inode; private workspace identity; profile identity/version;
prepared commit/tree, reference, target-relative path/mode set and digest;
original causal observation references; combined verification/review/approval
identities; derived Authority proposal; and terminal import/receipt linkage.

States distinguish preparing, prepared, awaiting-evidence, authorized, published,
held and imported. A preparing record is not a completed operation. Immutable
intent is committed before profile effects. Resume from the original recorded
target/operands after interruption; only settled outcomes replay. Validate a
retained prepared reference instead of applying twice. Readers validate closed
shapes and cross-bind row, intent signature, outcome and owner records. Record
existence or agreement between two caller-controlled documents is insufficient.

A later target advance may require a new result from the SAME original
submission. It never mutates the previous result or reuses its tests/review.
The selector changes only after an explicit stale-result disposition and proof
that its attempt never acquired unresolved target mutation authority. A live or
uncertain runtime/lease uses existing exclusion/recovery, not a fresh writer.

## 4. Preserve causal observations

For the retained B defect witness, preserve three distinct observations:

1. The defect reproduction fails on B's original base.
2. The same reproduction passes with B's isolated fix.
3. It passes OR fails on the combined result after reconciliation with A.

Each names command/test identity, input commit/tree, test/fixture digest,
environment/profile, actual exit/result, output artifact and producing execution.
Pin a newly added regression harness once and run that same harness against the
three content states; do not pretend a test absent from the old base ran there.
An unrelated setup/import failure is not the defect's baseline failure. The
combined failure stays visible and blocks integration; it does not invalidate
or erase the isolated positive. Other required tests retain their independent
meaning. This is a concrete regression witness, not a rule that every unrelated
feature must manufacture a failing test on its base.

The input bundle carries both source and integration-result evidence, separately
typed. Old producer verification/review proves the submission, never the new
combined bytes. Post-import verification observes actual imported bytes and is
retained in addition to pre-import combined verification. Test execution that
changes content invalidates the measured candidate. No pass word from a model
or clean Git exit replaces test/review custody.

## 5. Reuse Authority publication without weakening Authority integration

Propose a NEW ordinary Authority proposal under the current integration-role
fixed assignment, with a distinct frozen result_id/result_digest owned by the
reconciliation record. Its candidate_digest is the combined result and its
target is the snapshot used to prepare it. The original producer proposal stays
immutable. The configured integration publisher needs existing scoped publish
authority; verifier/reviewer/approver remain independent, scoped participants.
Factory preflight proves those capabilities before durable setup.

No Authority/core/schema/API change is proposed. Authority.integrate still
requires passed verification, accepted review, explicit approval and an exact
current target match on the DERIVED proposal. The integration owner's typed
link proves which eligible original submission that proposal satisfies.
Publish retry reads back the exact proposal and fixed result, before selecting
a later target or assignment. A failure to express this through the existing
scoped publication/session API is a concrete return-for-amendment gate, not
permission to edit Authority or to publish under a historical producer claim.

## 6. Queue, runtime and target revision

Separate source eligibility from the import account in admission/driver.
Existing direct imports retain their old exact-target path. The explicit new
result branch must prove custody and separate receipts before enqueue; an old
submission cannot enter that branch by relabelling its original proposal.
Version the closed account/bundle where their fields change. Queue rank and
lease ownership stay target-global; result identity and source identity both
ride the account and replay signature.

The configured integration profile binds one dedicated target repository and
its authoritative revision reference. For the new Git capability, propose a
reserved target reference and compare-and-swap advance from the reviewed target
revision to the combined commit after exact import and post-import verification.
The physical target content and the Authority cursor must name the same result;
advancing only the Authority digest while leaving an old HEAD/content witness
is not acceptable. The profile verifies objects, full result content and its
configured revision reference, rather than trusting a caller's target pathname.

All profile Git writes are confined to nominated private preparation storage
and the dedicated target's explicitly configured reference/object namespace.
No human repository index, branch or history mutation is authorized. The current
v11 baton.merge agent keeps its exact-byte import-only policy. Proposed product
policy makes this distinction explicit; it grants no agent a new shell command.

Immediately before import, re-prove source eligibility, exact authorized result,
current target revision/content, complete path/mode authority, target object,
live lease/fence and fixed runtime assignment. The existing importer applies
approved result bytes, not a new unreviewed merge. No chmod/type repair, scope
expansion or opportunistic change. After import, verify bytes/modes and tests,
advance the dedicated profile reference with its expected old value, then
commit/read back Authority integration and settle/release through existing
owners. Preserve the entire result/publication/entry/lease/fence/attempt chain.

Crashes between content import, profile revision advance, Authority receipt and
coordinator release remain held until exact readback/recovery proves a single
outcome. Never start a second target writer or manufacture rollback/cleanup.
No failed post-import test is reported as a clean pre-mutation refusal.
Assembly completion names the derived integration receipt AND original source
submission, and releases only the actual finished stage's capacity through the
accepted completion owner. Ordinary status never prepares, publishes or retries.

## 7. Acceptance and scope gates

The public configured witness completes A then B on one target, preserving both
changes and B's original line/base/producer/review evidence. It records B's
base-fail/isolated-pass/combined-pass and a separate combined-fail control.
Replay/reopen at preparation, publication, import and final settlement never
changes selected operands, duplicates a target writer or loses capacity.
Unaccepted submissions, forged custody, missing tests/review, target races,
conflicts, out-of-scope changes and unknown runtime states refuse or hold.
W130224 retains two-terminal serving acceptance and W119405 joined acceptance.
Reuse exact accepted evidence; no duplicate proof campaign or implied closure.

INTEGRATION-SCOPE-v1.md names proposed files, retained-byte disposition, serial
verification and new runtime allocation. Approval of direction M132985 alone
does not authorize those changes. If the public owner boundaries above require
another file or a different protocol, return the exact amendment before edits.
