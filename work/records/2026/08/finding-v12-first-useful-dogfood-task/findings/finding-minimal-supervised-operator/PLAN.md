# Plan

1. [blocked on W39356 and W39357] Read both accepted child records and
   revalidate their public surfaces.
2. Implement the smallest documented operator command and deployment session
   facade under the owned tool/test files.
3. Compose bounded source staging, explicit credential/network delivery,
   public lifecycle operations, correlated conversation and proposal custody.
4. Prove the positive composition and only the negative/retry/cleanup cases
   necessary to keep this slice honest; file broader hardening into W39366.
5. Run a no-live-secret Docker dry run, retain bounded evidence and return for
   independent review.

## 2026-08-30 — first implementation round under W39358

1. [done] Revalidated W39356's and W39357's accepted public surfaces; both
   hold and are recorded in `FINDING.md`.
2. [done, partial] `v12/python/tools/dogfood_operator.py` — the deployment
   session facade, bounded source staging, the frozen task read on the way in,
   and the two protocol documents with every policy identity as an operand.
3. [NOT DONE] The composed arc: offer, accept, record, claim, activate, input
   root, launch and credential deliveries, runtime start, the worker-entry
   conversation, freeze, intake, retention, destroy, positive absence and
   credential teardown.
4. [NOT DONE] The retained evidence record and the independent diff and
   verification derivation.
5. [done for what exists] `v12/python/tests/tools/test_dogfood_operator.py` —
   27 cases, no daemon and no credential, registered in the parallel phase.
6. [NOT DONE] The real Docker dry run to the worker entrypoint.
7. Return this partial foundation for review BEFORE building the arc on it,
   because two of its decisions were only settled by running the manager's own
   composer and a third reader should see them before more rests on them.

## 2026-08-30 — first independent foundation review: changes requested

1. [required P1] Correct manifest-relative paths to `source` below `/input`
   and `proposal` below `/output`; supersede the claim that destination is
   wholly unconsumed, because manifest validation and retained evidence read
   it even though materialization does not.
2. [required P1] Hold every frozen-task field at the operator boundary so the
   same malformed task the worker rejects cannot survive until container
   start.
3. [required P1] Add a pure preflight over all explicit identities and grants
   before source staging. Validate policy values as digests, not only the key
   set, and compose later steps only from the held result.
4. [required before public command] Do not allow `stage_source`'s test-bound
   operands to widen the operator's fixed entry or byte ceilings.
5. [regressions added] Three additive methods cover fixed-root paths, complete
   task validation and malformed policy identity; the original 27 foundation
   cases remain green.

## 2026-08-30 — second implementation round, after `review-2026-08-30T05-53-19Z.md`

1. [done] **[P1] Both manifest paths are relative to their fixed root**:
   `source` below `/input`, `proposal` below `/output`, with
   `PROPOSAL_TARGET` a named constant. The "consumed by nothing" claim is
   superseded in `FINDING.md` rather than left live beside its correction.
2. [done] **[P1] `frozen_task` holds the worker's whole task contract**, and
   a regression holds the operator's copy against the worker's — member set,
   schema, staged source name and identity grammar.
3. [done] **[P1] `preflight` is a pure hold over the explicit operands**, run
   before anything is staged, validating digest VALUES rather than key names
   and collecting its faults into one refusal.
4. [done] `stage_source` refuses a widened ceiling and still accepts a
   narrowed one.
5. [done] 45 cases, up from 30 (the original 27 plus the reviewer's 3).
6. [NOT DONE, unchanged] The composed arc, the retained evidence record, the
   independent diff and verification derivation, and the Docker dry run.
7. Return for review. The arc is the next round and rests on a foundation
   whose three boundaries now match the contracts it will use.

## 2026-08-30 — second independent foundation review: changes requested

1. [confirmed] Fixed-root manifest paths, full first task read, digest-valued
   policies and non-widenable source ceilings are corrected.
2. [required P1] Close the mutable-task interval: preflight and the eventual
   copy must consume the same fully held task, not a writable dict whose
   second check is schema-only.
3. [required P1] Hold record-binding values and the engine-network grammar
   before staging, not only the binding's key set and the network's presence.
4. [required P1] Refuse a non-document policy collection as an
   `OperatorRefusal` before iterating or coercing it.
5. [required P2] Validate caller-narrowed source ceilings as positive exact
   integers before calling the copier.
6. [follow-up outside this child's file ownership] W39357's receiver accepts
   numeric `task_id` through `str(...)`; file that semantic mismatch against
   the closed receiver Work rather than editing it through W39358.
7. [regressions added] Five additive methods fail with 15 subcases while the
   prior 45 methods and 202 adjacent tests (1 skip) remain green.

## 2026-08-30 — third implementation round, after `review-2026-08-30T06-05-02Z.md`

1. [done] **[P1] `held_task` is one pure hold**, applied at the first read, at
   the preflight and immediately before the copy.
2. [done] **[P1] The record binding and the network are held by value before
   staging**, the network through `oci._network` rather than a second grammar.
3. [done] **[P1] A malformed policy container is a typed refusal**, held
   before its contents are iterated.
4. [done] **[P2] A narrowed ceiling is a positive exact integer.**
5. [done] **[P2] The agreement test says what it compares**, and a case
   asserts the sender/receiver asymmetry from both sides. W44424 owns the
   receiver correction; this Work does not touch W39357's file.
6. [done] 56 cases, up from 50 (45 plus the reviewer's 5).
7. [NOT DONE, unchanged] The composed arc, the retained evidence record, the
   independent diff and verification derivation, and the Docker dry run.

## 2026-08-30 — third independent foundation review: changes requested

1. [confirmed] The mutable-task interval, network grammar, malformed policy
   container, narrowed-ceiling contract and inaccurate sender/receiver claim
   from the prior review are corrected.
2. [required P1] Hold `record_binding.root` and `record_binding.path` against
   the frozen manifest's exact `opaqueId` and `relativePath` definitions before
   staging. Do not preserve a weaker handwritten approximation of those
   contracts in the deployment tool.
3. [regression added] One additive method fails with six schema-defined locator
   cases while the prior 56 operator tests and 228 adjacent tests (1 skip)
   remain green.
4. [NOT DONE, unchanged] The composed arc, retained evidence, independent
   diff/verification derivation and Docker dry run remain the next substantive
   implementation round after the foundation correction.

## 2026-08-30 — fourth implementation round, after `review-2026-08-30T06-13-35Z.md`

1. [done] **[P1] The record-binding locators go through the frozen contract's
   own owner** — `validate_fragment(..., "opaqueId")` and
   `validate_fragment(..., "relativePath")` — at preflight and again at the
   composer, with the validator's own sentence in the collected fault. The
   `posixpath` approximation is deleted and the record supersedes the claim it
   supported.
2. [done] 62 cases, up from 57 (56 plus the reviewer's 1).
3. [NOT DONE, unchanged] The composed arc, the retained evidence record, the
   independent diff and verification derivation, and the Docker dry run.

## 2026-08-30 — fourth independent foundation review: changes requested

1. [confirmed] Record-binding root and path now use the frozen contract's own
   definitions before staging and at the composer; all six prior locator
   regressions pass and the handwritten approximation is removed.
2. [required P2] Catch only `ContractRefusal` from the frozen-fragment and
   engine-network grammar owners. Unexpected owner failures are defects and
   must not be relabelled as bad operator grants.
3. [required P2] Supersede the sender/receiver numeric-task asymmetry in the
   test and chronological record now that W44424 makes both predicates require
   exact text. Do not use the receiver's regex alone as a substitute for asking
   its predicate.
4. [regression added] One additive method errors in two owner-failure subcases
   while the prior 62 operator tests and 295 adjacent tests (1 skip) pass.
5. [NOT DONE, unchanged] Build the lifecycle arc, retained evidence,
   independent diff/verification derivation and Docker dry run after these
   foundation corrections.

## 2026-08-30 — fifth implementation round, after `review-2026-08-30T06-20-54Z.md`

1. [done] **[P2] Only `ContractRefusal` is caught at both grammar owners**, so
   an owner's implementation defect propagates instead of being relabelled as
   malformed operator input.
2. [done] **[P2] The W44424 supersession is recorded** in `FINDING.md`,
   `PLAN.md` and `PROGRESS.md`, and the case asks the receiver's actual
   predicate rather than its pattern.
3. [done] 66 cases, up from 63 (62 plus the reviewer's 1).
4. [NOT DONE, unchanged] The composed arc, the retained evidence record, the
   independent diff and verification derivation, and the Docker dry run. The
   foundation is now clear of findings and the arc is next.

## 2026-08-30 — fifth independent foundation review: accepted

1. [confirmed] Both grammar-owner boundaries catch only typed
   `ContractRefusal`; unexpected failures propagate and the additive owner
   regression passes.
2. [confirmed] W44424's predicate correction is reflected in the current test
   and chronological record; both actual predicates refuse numeric task IDs.
3. [verified] 66 focused tests and 295 adjacent tests pass (1 skip); whitespace
   check is clean.
4. [required next] Build and return the composed lifecycle, retained evidence,
   independent diff/verification derivation and real Docker dry run. The
   foundation is accepted, but W39358 is not complete without this arc.

## 2026-08-30 — sixth round

1. [written, NOT EXERCISED] `run_dogfood_task` composes the accepted order end
   to end through public operations only, with the runtime identity taken from
   `request_runtime_start`'s own answer and the diff and verification
   recomputed by this operator before retention discards the source.
2. [NOT DONE] Any case that drives it. The real Docker gate was started and
   stopped this round rather than finished badly; `PROGRESS.md` says so.
3. [NOT DONE] The unresolved branches, and the serial registration a Docker
   gate needs.

## 2026-08-30 — sixth independent review: composition changes requested

1. [required P0] Bind the assignment manifest to the claim result that
   `submit_claim` actually returned. Do not discard that result and do not
   substitute a zero digest or event `1` when the accepted-offer document
   carries neither fact.
2. [required P0] Add the positive quiescence transition between the
   worker-entry conversation and `request_freeze`. The interactive container
   deliberately keeps PID 1 running; `reconcile_runtime` observes it and does
   not stop it, while the freeze contract accepts only `quiescent`.
3. [required P0, decision needed] End the exact live assignment after intake
   and before cleanup through an explicitly authorized authority transition.
   `authorize_cleanup` refuses a still-live assignment, and this deployment
   currently carries no success transition that can make its cleanup call
   reachable. Pin whether the supervised result passes to review or uses a
   different ending before implementing it.
4. [required P0] Put every post-start outcome through one ending path. Lost or
   faulted conversation, absent disposition, uncertain start reconciliation,
   verification failure/timeout and later typed refusals currently return or
   raise before runtime/credential/launch cleanup is attempted.
5. [required P1] Derive the candidate from the public intake receipt's
   `custody_locator`; do not reach through the OCI adapter's private
   `_custody` method. Bind the explicit engine/image/network/run/label operands
   to the adapter the operator constructs rather than leaving them unused or
   dependent on an unchecked factory closure.
6. [required] Add an injected composition suite that drives the whole function
   and its unresolved/replay/fresh-attempt endings, then a registered serial
   real-Docker gate over `Dockerfile.claude`. Add the documented command and
   durable redacted transcript writer; a returned in-memory dictionary is not
   the recorded operator evidence required by this Work.

## 2026-08-30 — seventh independent review: post-start ending still open

1. [confirmed] The assignment manifest now derives its receipt digest and
   event from `submit_claim`'s closed result with no placeholder branch; the
   public intake locator is used; and the adapter factory is handed the
   engine/image/network/run/label grants recorded by the evidence.
2. [required P0] Move the worker-entry conversation and disposition handling
   inside the guarded ending. Both named failure branches still return before
   `_custody_and_ending`, so neither orders quiescence nor attempts cleanup.
3. [required P0] Make the guard actually own cleanup on every path. Its
   non-quiescent and empty-intake branches return from inside the guard and the
   `finally` performs only `adapter.observe`; observation cannot destroy the
   runtime or tear down credential/launch delivery.
4. [required P1] Treat `absent` after the stop as unresolved for freeze rather
   than proceeding: `request_freeze` accepts only `quiescent`. Preserve
   unexpected implementation defects after the ending instead of converting
   every `Exception` into an ordinary unresolved operator outcome.
5. [regression added] One additive injected method fails in two subcases —
   lost conversation and answered-without-disposition — because the named
   runtime receives zero stop requests. The prior 123 tests remain otherwise
   green (1 skip).
6. [still required] Await and pin M44657's authority-ending ruling, then build
   the whole injected composition matrix, registered real-Docker gate,
   documented command and durable redacted evidence writer.

## 2026-08-30 — eighth independent review: receipt interval and W44716 gate

1. [confirmed] Conversation/disposition handling is now structurally inside
   `_after_start`; the two prior branches enter `finally`, `absent` does not
   freeze, and unexpected faults from the guarded body propagate afterwards.
2. [required P0] Mark the durable intake receipt present immediately after
   `request_intake` returns. Empty custody, independent verification failure
   or timeout, and retention refusal currently occur before the flag, so the
   common ending falsely says no receipt exists and skips `authorize_cleanup`.
3. [required P0, blocked on W44716] Replace direct stop-before-fence on lost or
   unusable worker answers with the manager-owned ending W44716 will pin. A
   conversation the manager cannot conclude from does not permit stopping the
   still-live authority generation before it is fenced.
4. [required P2] Drive the no-disposition regression with a possible
   `converse` result: an answered `work` operation whose disposition is not
   usable, not an `answered` conversation which contains only `describe`.
5. [regression added] Empty committed intake currently invokes manager cleanup
   zero times. The focused aggregate runs 125 tests with that one failure and
   one skip; the other 124 pass.
6. [still required] Await M44657 and W44716, then finish the whole injected
   matrix, serial real-Docker gate, documented command, durable redacted
   evidence writer, and replay/fresh-attempt proofs.
