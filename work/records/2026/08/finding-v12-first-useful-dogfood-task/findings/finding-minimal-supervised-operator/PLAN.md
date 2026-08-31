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

## 2026-08-30 — approver ruling on M44657

1. [decided] Preserve the v11 lifecycle in v12: after successful intake,
   independent verification and retention, explicitly `pass_work` for the
   exact assignment generation to an operator-supplied review Route.
2. [next] Add `pass_work` to `DeploymentSession`, hold the review Route as an
   explicit operand, and permit cleanup only after the pass commits.
3. [still blocked on W44716] The unanswered-worker failure path remains a
   separate ending decision; it does not change the approved success pass.

## 2026-08-30 — W44716 abandonment ruling

1. [decided] An unanswered or unusable worker result is ended through one
   manager-owned composite abandonment operation: exact durable identity,
   assignment fence, exact-runtime stop/removal, positive absence, retained
   untrusted output, delivery teardown and lane release.
2. [required after W44716 implementation] Replace direct `adapter.stop` on
   those failure paths with the public manager ending. A timer alone does not
   abandon; the successful path remains unchanged.

## 2026-08-30 — ninth implementation and re-review

1. [confirmed] The committed receipt is remembered before fallible custody
   work, and the receiptless ending consumes W44716 without pre-fence runtime
   control.
2. [confirmed] The success arc explicitly calls the deployment session's
   `pass_work` for the expected generation and requested review Route before
   manager cleanup.
3. [required P0] Hold the authority's complete pass result and require its
   ended assignment to equal the exact expected generation; a matching Route
   alone proves no pass of this assignment.
4. [required P1] Require the underlying minted session's `pass_work`
   capability when constructing `DeploymentSession`, so the facade cannot
   pass preflight while delegating to no operation.
5. [authorized P2] Replace the reviewer-owned impossible describe-only
   `answered` fixture with the reachable unusable work-disposition shape,
   preserving its assertions.
6. [still required] Build the whole-arc replay/fresh-attempt matrix, registered
   real-Docker gate, documented reusable command and durable redacted evidence
   writer before W39358 can close.

## 2026-08-30 — tenth implementation and re-review

1. [confirmed] The facade now holds the underlying pass capability; the pass
   result names the exact assignment; the stale transport fixture is corrected;
   and the real composer writes `task.json` before sealing its root.
2. [required P0] Make the documented shell invocation enter a real launcher.
   It currently loads definitions and exits 0 without reading grants or writing
   evidence; the launcher must honestly receive the seven non-file capabilities.
3. [required P1] Hold `phase == "queued"` and `gate is None` in the pass result,
   not only the presence of those members.
4. [required P1] Extend the fresh-attempt matrix to observe distinct credential
   deliveries reaching each adapter, not only distinct workspace roots.
5. [decided M46497] For the pilot, exact rerun refuses before another runtime
   or provider turn and retry uses a fresh attempt identity and assignment
   generation; same-attempt resumption is later hardening.
6. [decided M46497] After a committed intake receipt, always request manager
   settlement even when `pass_work` refuses or is uncertain. A live assignment
   makes the manager refuse destructive cleanup and leaves an explicit
   unresolved attempt for pass retry or W44716 abandonment. Actual successful
   cleanup remains ordered after a committed pass.
7. [decided clarification] Distinguish a successful worker with a frozen,
   verified result from failed post-worker machinery. Preserve the trusted
   result, stop the cleanly quiescent runtime, and retry only the failed
   manager/handoff/external step idempotently. Do not abandon, reassign or open
   another provider turn. Keep external services outside Baton's local pass.
8. [still required] Add and register the real-Docker gate over the real dogfood
   image, reflecting the approver ruling; verify durable unresolved evidence
   survives a post-start unexpected fault at the launcher boundary.

## 2026-08-30 — critical-path scope freeze

1. [current, final parent round] Correct the latest review's one-root URI
   handling and complete the real-Docker failed-handoff/fresh-retry settlement
   gate.
2. [next review, closed scope] Verify only those two frozen acceptance items.
3. [mandatory decomposition] If either still fails, create a separately
   claimable leaf Work for each failure and block W39358 on those visible
   leaves; do not begin another monolithic W39358 implementation round.
4. [follow-up] File every newly discovered non-blocking robustness concern
   outside this critical path. Live provider authorization remains W39364.

## 2026-08-30 — eleventh implementation and re-review

1. [confirmed] The direct module invocation now enters a launcher; pass results
   are held queued and ungated; distinct fresh credential deliveries are
   observed; and a registered real-Docker arc case exists.
2. [required P0] Require the independently rerun verification command to exit
   zero before retention and review pass. A nonzero result remains unresolved
   and still requests manager settlement after its committed intake receipt.
3. [required P0] Expose the M46985 narrow handoff retry through the documented
   operator over retained evidence and original grants. Validate the real
   completed/verified state rather than truthy field presence, and prove the
   retry across a fresh capability construction with no worker-side action.
4. [required P1] Put `--credential-file` in the one public parser/help and
   update the command/grants documentation for every newly required authority
   and credential member. Exercise `_launched` on a positive boundary; the
   Docker case currently reconstructs its dependencies around it.
5. [regressions added] The focused suite now runs 107 tests: the prior 105 pass
   and the failed-verification and hidden-credential-help witnesses fail.
6. [verification condition] Re-run the registered Docker/aggregate gate after
   concurrent W43975 workspace edits settle and from an authorized Docker
   runner; this managed review context cannot access the daemon socket.

## 2026-08-30 — twelfth implementation and retry re-review

1. [confirmed] Failed independent verification no longer passes; retry trust
   requires real `completed` plus status zero; one parser/help and grants prose
   expose the credential and launcher inputs; `_launched` has a positive case.
2. [required P0] Give `--retry-handoff` a retry-specific capability build that
   adopts the existing credential delivery and existing roots. It must perform
   no materialization/allocation/provider callback or worker-side action.
3. [required P0] Make a successful exact pass plus settlement clear only the
   retry-owned current gates and converge to `resolved=True`/exit 0 while
   preserving unrelated uncertainty as current and old failures as history.
4. [required P0] Secret-sweep and size-bound retained evidence before use, and
   bind its attempt/result/assignment identities to the supplied grants and
   durable manager/authority facts before any capability is touched.
5. [regressions added] The focused suite now runs 112 tests: the prior 109 pass
   and three retry witnesses fail/error on convergence, secret read and
   cross-attempt evidence.
6. [required] Exercise the public retry from a real failed-handoff durable
   state across a fresh process/capability construction; the current suite has
   no `_retried` or `--retry-handoff` case.

## 2026-08-30 — thirteenth implementation re-review

1. [confirmed] Evidence read now secret-sweeps and refuses an over-ceiling
   record; credential state is adopted; record/grant disagreement is checked
   before capability construction; mocked pass/settlement convergence works.
2. [required P0] Record and require the committed retention decision before
   the pass or narrow retry. The current four-member trust check also accepts
   the state immediately before a refused retention act.
3. [required P0] Make retry root lookup preserve allocation's exact canonical,
   no-symlink containment proof without allocating or changing modes/groups.
4. [required P0; child W47225] Add the manager-owned launch-delivery adoption
   seam and compose it into fresh-process settlement so the existing launch
   root is proved removed rather than reported `not-delivered`.
5. [required P1] Bind the original review Route and retention policy digest
   before capability construction; enforce the evidence read ceiling with a
   bounded read rather than an unbounded read followed by a length check.
6. [still required] Exercise the public retry from a real failed-handoff
   durable state through fresh capabilities, exact pass and complete manager
   settlement. The current positive reaches only a mocked capability path.
7. [regressions] 116 focused tests: the prior 114 pass and the new retention
   and symlink witnesses are the two failures. The eight-module aggregate is
   776 tests with the same two failures and one skip.

## 2026-08-30 — fourteenth implementation re-review

1. [confirmed] Restart refuses the direct symlink witness; retained evidence
   requires output and retention; review Route and retention policy are bound;
   and the evidence read is bounded before parsing.
2. [required P0] Retain the exact closed freeze and retention answers without
   defaults, then replay-read and compare `frozen_output_of`,
   `intake_receipt_of`, and `retentions_of` before a retry can pass Work. The
   editable evidence file identifies durable facts; it cannot create them.
3. [required P0; child W47225] Complete strict launch-delivery adoption and
   refuse an absent adoption for the already-started attempt. W39358 remains
   open while its child remains open.
4. [required P1] Prefer a manager-owned read-only root adoption/proof boundary
   over the deployment-owned check-then-use implementation, preserving exact
   canonical containment without allocation or mode/group changes.
5. [still required] Exercise the public retry from a real failed-handoff
   durable state through fresh capabilities, exact pass and complete manager
   settlement.
6. [regression] The two prior focused witnesses pass; the new
   `test_editable_evidence_does_not_mint_durable_freeze_and_retention` fails
   because the authority pass occurs while every public manager fact reader
   reports absence.

## 2026-08-30 — fifteenth implementation re-review

1. [confirmed] Retry calls the three public manager readers and refuses
   absence before pass; the arc no longer invents frozen truth or a default
   retention disposition.
2. [required P0] Retain and compare the complete bounded projection the
   evidence claims: frozen result/manifest identity, intake receipt digest and
   artifact ID/content/bytes, and retention artifact set/disposition/policy
   taken from the manager answer. Remove any recorded member that is not held.
3. [required P0; child W47225] Complete and close strict launch adoption; an
   absent adoption for this started attempt remains a contradiction.
4. [required P1] Move restart root proof to the manager-owned read-only seam.
5. [still required] Exercise the public retry from a real failed-handoff
   durable state across fresh capabilities and complete settlement.
6. [regression] 119 focused tests: every prior case passes; the new table
   witness has four failing subcases for result identity, receipt identity,
   custody content and retention artifact-set disagreement.

## 2026-08-30 — sixteenth implementation re-review

1. [confirmed] Every manager fact retained by the ordinary arc is compared
   whole with the three public manager readers before retry can pass Work.
2. [confirmed] Child W47225 is closed satisfying; strict launch adoption is no
   longer an open child gate.
3. [required P1] Hold the complete nested shape and value contracts of editable
   retry evidence before calling `.get`, subscripting or sorting its members.
   Malformed allowed members currently leak raw Python faults.
4. [still required] Exercise the public retry from a real failed-handoff
   durable state through fresh capabilities, exact pass and complete manager
   settlement.
5. [required P1] Move restart root proof to the manager-owned read-only seam.
6. [regression] 120 focused tests: the prior 119 pass and the new malformed-
   evidence table errors in five subcases before the authority pass.

## 2026-08-30 — seventeenth implementation re-review

1. [confirmed] The five previously witnessed result/manager projections are
   shape-held and now refuse malformed editable values.
2. [required P0] Replay the exact effectively-once authority pass regardless
   of editable `review_pass`; hold any retained pass projection against the
   authority answer rather than letting the file suppress the call.
3. [required P1] Hold retry-owned `unresolved` history and every other nested
   value the retry consumes. A boolean history still leaks `TypeError`.
4. [accepted slice] Root grammar ownership moved into a read-only manager
   seam without allocation or permission changes.
5. [required P1] Preserve the proved root identity through adapter use. The
   manager seam still returns mutable path strings that are reopened later,
   so moving the check did not close the proof/use interval.
6. [required P0, unchanged] Exercise the public retry from a real failed-
   handoff durable state across fresh capabilities, exact pass and complete
   manager settlement with no worker-side act.
7. [regression] 121 focused tests: 119 pass; suppressed authority replay fails
   and malformed unresolved history errors.

## 2026-08-30 — eighteenth implementation re-review

1. [confirmed] Retry always replay-calls the exact authority pass and compares
   any recorded pass projection whole; editable evidence cannot suppress it.
2. [confirmed] Bounded durable-text unresolved history and the other consumed
   scalar/pass values are held before use; all six malformed subcases pass.
3. [required P1, unchanged] Preserve manager-proved root identity through
   adapter use rather than returning mutable path strings for later reopen.
4. [required P0, unchanged] Exercise the public retry from a real failed-
   handoff durable state through fresh capabilities, exact pass, complete
   settlement and no worker-side act.
5. [verified] 121 focused and 829 non-Docker aggregate tests pass (one
   aggregate skip); Docker is unavailable to this managed reviewer.

## 2026-08-30 — nineteenth implementation re-review

1. [research accepted] One real authority can serve both manager durable-state
   construction and the pass under test through `DeploymentSession` and
   `AuthorityPort`; use this to build the public retry fixture.
2. [required P0, unchanged] Implement the real durable failed-handoff → fresh
   public `--retry-handoff` → exact pass/settlement/no-worker-act gate.
3. [required P1, unchanged] Hold adopted root identity through every adapter
   use rather than checking then returning mutable path strings.
4. [no implementation] This round changed no W39358 code or tests, so the
   previous 121/829 independent baseline remains current.

## 2026-08-30 — twentieth independent re-review

1. [confirmed] The failed-handoff durable record is now produced through the
   ordinary public command, and the retry-specific authority/control handles
   are closed in a `finally`.
2. [required P0] Complete the fresh-capability public retry acceptance gate.
   Its current test ignores the retry status and never asserts resolved state
   or cleanup; the implementation record confirms settlement remains
   incomplete.
3. [required P1, unchanged] Preserve manager-proved root identity through
   ordinary and retry adapter use. Both paths still flatten roots to mutable
   path dictionaries which the adapter reopens.
4. [required P1] Close the authority and control-store handles opened by the
   ordinary launcher on success, unresolved return and exception. The focused
   suite's resource trace identifies the leaked authority allocation in
   `_launched`.
5. [verified] The exact new public-retry case and all 122 focused tests pass;
   the full focused run emits the ordinary-launcher resource warning, and
   whitespace passes.

## 2026-08-30 — twenty-first independent re-review

1. [confirmed] Ordinary `main` closes a successfully returned capability
   bundle on normal, unresolved and compose-fault paths.
2. [required P1] Unwind partially constructed ordinary capabilities inside
   `_launched`. An Authority opened before `ControlStore.open` fails is still
   leaked because no bundle reaches `main`.
3. [required P0, unchanged] Build the real-engine public retry gate and assert
   exact pass plus complete settlement, resolved evidence and positive absence.
4. [required P1, unchanged] Preserve manager-proved root identity through both
   adapter uses instead of flattening it to pathname dictionaries.
5. [regression added] The returned-bundle success/retry cases pass with
   resource warnings fatal; the new partial-build lifetime case fails with
   zero Authority disposals.

## 2026-08-30 — twenty-second independent re-review

1. [signed off] Ordinary and retry partial capability construction unwind
   every successfully opened durable handle locally.
2. [reviewer-test correction] Install the dispose recorder on the Authority
   instance; the unchanged lifetime assertion now passes.
3. [required P0, unchanged] Complete the real-engine public retry settlement
   acceptance gate.
4. [required P1, unchanged] Preserve manager-proved root identity through both
   adapter uses without flattening to pathname dictionaries.
5. [verified] All 124 focused tests pass with resource warnings fatal.

## 2026-08-30 — twenty-fifth independent re-review

1. [required P1, unchanged] Preserve the exact manager-minted
   `AllocatedRoots` through adapter construction and the later `run_vector`
   use. `_roots` currently copies it into a plain dictionary, so `start`
   re-enters the plain-mapping branch and canonicalizes both names again.
2. [regression added, failing] The adapter-retention witness asserts object
   identity and fails on the copied dictionary. The preceding equality-only
   witnesses did not detect the flattening they claimed to exclude.
3. [required P0, unchanged] Complete the real-engine public retry settlement
   gate: exact pass, complete settlement, resolved evidence, exit zero,
   cleanup, positive absence, and no second worker act.

## 2026-08-30 — twenty-seventh independent re-review

1. [confirmed] The reference image cannot run the operator's exact
   `/opt/baton/dogfood_entry.py` program, and reverting the program to
   `baton_worker.py` would restore the corrected fixture-agent defect.
2. [rejected blocker] W39364 already depends on W39358, so the reverse ledger
   dependency would cycle. Live Claude authorization is not required to test
   manager settlement.
3. [required P0, implementation-ready] Build a test-owned real Docker image
   with the exact dogfood entry seam injecting a deterministic proposal-writing
   agent. Drive ordinary failure and fresh public retry through real authority,
   stores, OCI adapter, engine, transport, deliveries, custody settlement and
   positive absence; assert resolved evidence, exit zero and no second worker
   act.

## 2026-08-30 — twenty-eighth independent re-review

1. [signed off] `_Channel.finish` returns the exact status/stderr document the
   transport consumes; 178 focused operator and worker-entry tests pass with
   resource warnings fatal.
2. [operational verification limit] The managed reviewer cannot access the
   Docker daemon socket, so the new real-engine module could not run here.
3. [required P0] Replace the generic scripted agent with the declared
   proposal-writing fixture agent, withhold the review handler so the ordinary
   public command produces exit 1 and a real failed handoff, add the handler,
   then assert fresh public retry exit 0, complete settlement, resolved
   evidence, cleanup/positive absence, and no second worker act.
4. [required P1] Register class cleanup for the temporary Docker build context.

## 2026-08-30 — twenty-ninth independent re-review

1. [signed off] Forward declared outputs and the input-manifest digest into
   `OciAdapter`; withhold the review handler until retry; clean the temporary
   image context.
2. [required P1, regression added] Decode the manager's `file:///...` custody
   locator once to one absolute local proposal root and use it for candidate
   plus all member checks. The new witness fails because `members_present` is
   empty with every member present.
3. [required P0] Install and debug the proposal-writing fixture agent, then
   finish and assert ordinary authority-pass failure, committed retention,
   fresh public retry exit 0, complete settlement, resolved evidence,
   launch/credential cleanup, positive absence, and no second worker act.
4. [operational verification limit] Reviewer Docker access remains denied;
   non-daemon operator suite runs 125 tests with only the new URI witness
   failing.

## 2026-08-30 — thirtieth independent re-review

1. [signed off] Decode and validate the local receipt URI once and reuse its
   absolute proposal root for candidate and member reads; all 125 operator
   tests pass with resource warnings fatal.
2. [required P0, unchanged] Debug and install the deterministic
   proposal-writing agent, then implement the ordinary exit-1 failed pass and
   fresh public retry exit-0 settlement case with exact pass, committed
   retention, resolved evidence, delivery cleanup, positive absence and no
   second worker act.
3. [operational verification limit] Reviewer Docker access remains denied;
   no escalation requested.

## 2026-08-30 — twenty-sixth independent re-review

1. [signed off] The nominal `_roots` path returns the exact manager-minted
   `AllocatedRoots`; adapter construction and `run_vector` re-entry preserve
   it without second pathname canonicalization.
2. [verified] All 96 OCI tests and all 124 operator tests pass, including the
   reviewer identity regression and fatal resource warnings. Whitespace
   passes.
3. [required P0, unchanged] Complete the real-engine public retry settlement
   gate: exact pass, complete settlement, resolved evidence, exit zero,
   cleanup, positive absence, and no second worker act.

## 2026-08-30 — focused iteration, then one broad handoff gate

1. [current] Iterate on the deterministic proposal-writing and public retry
   settlement witness with only its focused operator/worker-entry dependencies.
2. [after focused green] Run one broader relevant regression sweep before
   handoff, using `just --justfile v12/python/justfile parallel-test` so
   isolated shards use the host's available CPUs and registered
   Docker/shared-daemon modules remain serial.
3. [classification] A broad failure that can falsify the supervised dogfood
   path remains blocking; ledger an unrelated failure separately without
   starting another monolithic W39358 correction round.
