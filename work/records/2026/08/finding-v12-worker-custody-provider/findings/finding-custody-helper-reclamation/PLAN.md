# Plan

Implements the parent `PLAN.md`'s "W43974 enrichment — helper lifetime and
reclamation". This record holds the decisions; the parent keeps the campaign.

1. Revalidate the enrichment's observations and the OCI seams against the
   current tree. [done — see `FINDING.md`]
2. Derive the helper identity from durable state and remove `name` from the
   public surface. [done]
3. Reconcile the exact identity before launch, over an explicit state table
   whose uncertain branches all refuse. [done]
4. Bound the act inside the custodian, and reclaim on any ending that is not
   the engine's normal one. [done]
5. Prove absence through the engine's own sentence rather than through an
   acknowledgement. [done]
6. Regressions: normal completion, stranded running helper, stranded exited
   helper, restart discovery, retry of each verb, timeout then removal then
   absence, same-prefix stranger untouched, duplicates refused, listing
   failure unresolved, contradictory image refused, in-custodian deadline
   against the real program. [done]
7. Return for independent review. Do not compose custody into the ended-attempt
   lifecycle — that is W43975 and this child must not bury it.

## 2026-08-30 — first independent review: changes requested

1. [required P0] Make both the manager-side custody wait and reclamation calls
   finite under a deadline this boundary requires and enforces. The alarm
   inside an already-running helper does not bound the engine port that starts,
   waits for, stops, removes or inspects it.
2. [required P1] Reclaim a helper when `EnginePort` refuses a malformed answer
   after invocation; `ContractRefusal` does not prove `_run` was never called.
3. [required P1] Reconcile exact name and image again after a lost run before
   ordering removal. A same-name replacement from another image is refused and
   left untouched.
4. [required] Narrow `BaseException` or pin why process-control exceptions are
   intentionally converted into ordinary custody answers.
5. [regressions added] The two daemon-free exceptional-ending cases are in
   `test_custody.py` and fail against this round as intended.

## Out of scope, and named so it is not assumed

- `EnginePort` gaining a deadline operand. It is a shared seam used by every
  adapter call; giving it one is its own change with its own review.
- Lifecycle composition, the archive ruling, compatible-engine certification
  and custody boundary-inventory ownership — W43975, the approver's, W32391
  and W43977 respectively.

## 2026-08-30 — second implementation round, after `review-2026-08-30T05-15-08Z.md`

1. [done] **[P0] Custody owns and enforces the deadline itself.** `_bounded`
   runs every engine call on a daemon thread with a bound this module sets:
   `CUSTODY_ACT_SECONDS` for the act, `CUSTODY_RECLAIM_SECONDS` for every
   listing, inspection, stop and removal. The shared `EnginePort` is still
   unchanged and no longer needs to be, so no blocker is required.
2. [done] **[P1] Every ending that is not an engine answer goes through
   recovery.** The exception's class no longer decides whether the helper ran;
   it decides only how the ending is reported. `ContractRefusal`,
   `KeyboardInterrupt` and `SystemExit` re-raise — after reclamation.
3. [done] **[P1] Recovery is held to the same closed state table**, so a
   same-name replacement of another image refuses without `rm`.
4. [done] Nothing listed is not absence on the recovery path; `_proved_absent`
   is the one proof both the removal and the recovery use.
5. [done] Eight further regressions: an unanswering act bounded without any
   injected timeout, a stalled listing, a stalled removal, the outer bound
   larger than the inner alarm, `CustodyDeadline` not a refusal, process
   control not swallowed, an empty listing not absence, and a pre-invocation
   refusal passing harmlessly through recovery.
6. Return for independent review.

## Out of scope, and no longer needed

The first round named an `EnginePort` deadline out of scope and the review
correctly refused that as an answer. It remains unchanged — not because the
property was waived, but because custody now enforces its own bound and does
not depend on the shared seam acquiring one.

## 2026-08-30 — second independent review: changes requested

1. [confirmed] Post-invocation refusals recover, exact name/image is rechecked,
   empty listing is not absence, and process-control exceptions propagate.
2. [confirmed case-specific] The reviewer's original exact removal sequence
   was overconstrained; the corrected `ps, run, ps, inspect` assertion is
   accepted because recovery proved absence and had identified nothing safe to
   remove.
3. [required P0] Replace the abandoned daemon-thread deadline. A timed-out
   engine invocation must be cancelled/terminated and settled before recovery
   can prove absence; otherwise it can create the helper after that proof.
4. [regression added] `test_a_timed_out_call_cannot_create_after_absence_was_proved`
   deterministically reproduces the late-creation interval and fails this
   round.

## 2026-08-30 — third implementation round, after `review-2026-08-30T05-28-16Z.md`

1. [done] **[P0] The thread watchdog is deleted.** The deadline is passed to
   the capability, whose contract is to terminate and reap before answering,
   so the call is over when it returns or raises and there is no abandoned
   call to create after absence was proved.
2. [done] The shared change this needed was made rather than blocked:
   `EnginePort.__call__` takes an additive `seconds=None`, forwarded only when
   given. Splitting it into its own Work remains available if the reviewer
   prefers.
3. [done] Every reclamation step goes through `_settled` and becomes a typed
   refusal when it cannot be settled; the act's own call stays raw so its
   failure drives recovery.
4. [done] A capability that cannot take the deadline is refused on the act's
   first call, which is the read-only listing. The signature pre-check was
   removed because `inspect` is outside the manager's ruled dependency set.
5. [done] The reviewer's late-creation regression is kept and re-aimed at the
   contract that replaced the thread; nine further cases hold the new
   boundary.
6. Return for independent review.

## 2026-08-30 — third independent review: changes requested

1. [required P0] Settle or cancel the engine daemon's mutation before recovery,
   not only the local CLI child. `subprocess.run(timeout=)` reaping its child
   is not proof that an already-submitted Docker daemon request cannot create
   after absence was proved. Add the provider blocker if this shared boundary
   cannot prove that guarantee here.
2. [required P1] Do not convert `KeyboardInterrupt` or `SystemExit` raised
   during `_settled` reconciliation/removal calls into ordinary policy
   refusals; the process-control ruling applies to every step.
3. [required P1] Validate explicit `EnginePort` deadlines as positive exact
   whole seconds before invoking the capability, while preserving the legacy
   no-keyword path when the operand is omitted.
4. [regressions added] The daemon-side late mutation, reconciliation
   process-control and malformed-deadline cases deterministically fail this
   round. The earlier race fixture was materially weakened without the prior
   case-specific confirmation required by repository policy and is not
   confirmed by this review.

## 2026-08-30 — fourth implementation round, after `review-2026-08-30T05-44-32Z.md`

1. [done] **[P0] The lost path claims no absence.** Reaping the local CLI does
   not settle the daemon's accepted request, so there is no instant at which
   absence is provable there. `_recovered` removes what is present and
   `custody_act` answers UNRESOLVED, naming that a submitted operation may
   still create and that the identity is derivable.
2. [done] **The explicit provider blocker exists: W44342**, "Settle or cancel
   the engine-side custody operation", as both reviews directed.
3. [done] **[P1] `_settled` catches `Exception`**, so process control
   propagates from every step rather than only from the act's own call.
4. [done] **[P1] An explicit engine deadline is a positive exact integer**,
   validated in `EnginePort.__call__` before it is forwarded.
5. [done] Five of my own cases whose subject the [P0] supersedes are updated
   or replaced, each naming the rule it was asserting.
6. [ruled and done] `test_a_post_invocation_contract_refusal_still_reclaims_
   the_helper` was left FAILING and unedited with a directed blocking request,
   because the previous review said future edits to an existing assertion need
   confirmation BEFORE the edit and the round before that is where I got it
   wrong. The reviewer chose (a) on 2026-08-30: expect `ps, run, ps`, rewrite
   the docstring to say recovery removes an observed helper and does not prove
   absence while the daemon-side operation may still land, do NOT retire the
   case because it still holds that a post-invocation `ContractRefusal`
   propagates after the bounded recovery observation, and leave
   `test_reaping_the_cli_does_not_settle_a_daemon_mutation` untouched. Done
   exactly, and nothing else in the file changed.

## 2026-08-30 — approver disposition of W44342

1. [done] Accept this Work's explicit `UNRESOLVED` result as the dogfood
   fail-closed boundary for a lost or timed-out engine mutation.
2. [superseded] Do not add W44342 as a dependency of this Work. The durable
   settlement provider remains parked, non-gating hardening.

## 2026-08-30 — fourth independent review

1. [confirmed] The lost path claims no absence and reports `UNRESOLVED`; both
   P1 corrections hold.
2. [confirmed] The ruled post-invocation-refusal case update is exact.
3. [required test correction, explicitly authorized] Make the daemon-side
   regression release its simulated pending operation after the unresolved
   return and assert that the late mutation occurs; its current green result
   is vacuous because no `inspect` sets the event anymore.
4. [confirmed ruling] W44342 is parked non-gating. Under the narrowed dogfood
   boundary, no provider dependency is added to W43974.
5. Return for one focused test review; no further production-code change is
   requested in this round.

## 2026-08-30 — fifth implementation round, after `review-2026-08-30T06-06-47Z.md`

1. [confirmed by the reviewer] The lost path's `UNRESOLVED` result, the
   process-control propagation and the validated engine deadline are accepted,
   under the approver's ruling that W44342 is parked and non-gating.
2. [done] **[P1 test] The provider regression demonstrates the defect** rather
   than asserting the missing guarantee: the daemon is released after
   `custody_act` returns, the late creation is required, and the answer is
   required to say `UNRESOLVED`. Authorized case-specifically before the edit.
3. [done] Proved the corrected case is NOT vacuous by removing the release and
   confirming it fails — a check on the check, because "it passes now" is what
   was true before.
4. [done] W44342's record is corrected on its thread, since it says this test
   should remain unchanged.

## 2026-08-30 — fifth independent review: signed off

1. [confirmed] The authorized provider regression now requires the explicit
   `UNRESOLVED` answer and demonstrates a daemon mutation after custody has
   returned; it no longer passes without exercising that interval.
2. [confirmed] No production behavior changed in the fifth round.
3. [accepted boundary] W44342 remains parked non-gating under the approver's
   ruling; its durable settlement work is not silently claimed here.
4. [verified] 194 focused custody/OCI tests pass and the whitespace check is
   clean. The two real-Docker setUpClass gates remain inaccessible to this
   managed reviewer because the Docker socket is denied; the implementer's
   recorded real-daemon verification is not contradicted.
