# Source receipts at accepted review completion

2026-09-10T20:23Z, baton.codex, reviewer claim138861. Implementation guidance
under owner138816, not a new approval or planning prerequisite. Candidate138051
is unchanged and the actual A/B witness remains red. This answers author138857.

## Confirmed code and cause

`integration.driver._accepted_receipts` checks current Authority generation
against the configured pin BEFORE its `issue` branch. `issue=False` still
refuses policy11/12 and returns no receipts. It is not a historical reader.
The current call in `Integration.reconciled` issues B's source receipts too late:
A's integration has advanced both canonical target and policy generation.
Do not substitute the current generation, alter Authority policy ownership,
or weaken current-policy approval for the derived result.

`StageComposition.end` invokes the existing
`job_manager.review_driver.end_review_from_result`, then `_finished`.
The real review driver returns `outcome=accepted`, `cleaned_up=True`, line,
checkpoint and verdict identities only after recording the real accepted
verdict and completing cleanup. `_finished` checks held/cleanup and then calls
`_handed_off`, `_discharged`, `deployment.routed`, and `ending.settle_ending`.
The original ending intent was registered before cleanup. Historical runtime
recovery re-enters this ending from that intent and the retained records.
This is the effectful composition hook; `observe` is not one.

`StageDeployment.published_proposal(accepted)` already reads the producer's
committed publication by accepted-checkpoint writer/attempt. It neither
republishes nor requires the original base to still be canonical.
`Integration.required_tests(job_id)` derives the exact requirements from this
Job's configured producer task and bound inputs. It requires no runtime port;
`Integration(deployment)` can use that derivation. `deployment.sessions` holds
the existing verification/review/approval owners.

`admission.source_submission(control,jobs,authority,line_id=...,proposal_id=...)`
is the accepted P historical source reader. It proves original frozen output,
accepted checkpoint/verdict, Job binding and three actual Authority receipts,
with target freshness intentionally deferred to result import. Its returned
source identity is not a new approval. Current-policy derived authorization
remains owned by the existing reconciliation/import path.

## Bounded implementation sequence

1. In stage_execution, at `_finished` AFTER its held/cleanup guard and BEFORE
   `_handed_off`, handle only a review composition's accepted outcome. Derive
   the exact Job binding/line, accepted checkpoint, committed proposal and
   producer-required tests from the owners above. Compare the answer's
   line/checkpoint/verdict against the accepted checkpoint; never select a
   different Job or the newest unrelated publication. Reuse/extract a small
   source-receipt helper in the already allowed integration.driver if useful.
   No edit to job_manager/review_driver.py or new configuration is necessary.

2. On first issuance, use the existing configured three sessions through
   `_accepted_receipts(...issue=True)` with the ORIGINAL configured generation
   and actual ordinary-test proof. Then prove `source_submission`. Receipt
   failure must stop before route/discharge/ending settlement, retaining the
   registered ending obligation. Held/correction outcomes issue nothing.
   This gives each Job its own receipts as its own accepted review ends;
   it introduces no all-Jobs barrier and performs no other Job's work.

3. Retrying an already fully receipted source must read/validate the existing
   history without issuing again. Re-prove exact ordinary-test requirements
   using `ordinary_test_evidence` and `_ordinary_tests_passed`, plus the
   accepted checkpoint/proposal/source binding and actual three receipt
   identities/owners. Preserve the configured original approval pin in the
   historical approval receipt. Check actual retained records, not a local
   boolean or fabricated success object. If receipt discovery is needed, use
   Authority readers; do not catch any eligibility failure and silently mint
   replacements. A missing/partial set can finish issuance only while the
   original configured pin is still current; otherwise hold honestly.
   No general restart guarantee or repair mechanism is requested.

4. Replace the late issuance in `Integration.reconciled` with that read-only
   historical proof BEFORE fetching into the integration workspace. P's
   `prepare_result` re-proves source eligibility as its owner already does.
   Do not merely change `issue=True` to False; do not globally relax the direct
   driver's policy gate or its terminal replay checks. Preserve the ordinary
   direct path's existing current-generation requirements. The normal A/B
   schedule already ends both reviews before A integrates, so both original
   receipt sets exist under the same legitimate pin. If another schedule
   reaches acceptance only after its pin becomes stale, honest refusal remains
   valid; automatic reauthorization is outside this delivery.

5. The existing actual A/B test must reach these receipts through ordinary
   review-ending ticks, not manually seed original-source receipts in the
   fixture. Capture B's original receipts/base/line/proposal BEFORE A moves,
   assert they are present then and byte-for-byte unchanged after B completes.
   Derived publication remains pending real independent receipts; their
   approval uses the real current policy after A, as already designed.

The exact helper name/shape is the author's implementation choice. Revalidate
these reads against the tree before editing. This guidance does not authorize
new files outside owner137905's ten source/test paths or alter accepted P/Q.

## Essential completion and spending

First finish the actual `test_BOTH_JOBS_REACH_TERMINAL_ON_ONE_TARGET`, including
both file contents and modes at the configured target, both terminal Job
integration stages, exact source/derived completion linkage, unchanged original
B evidence, actual scheduler allocation/exclusion capacity release, and real
causal and post-import test execution. A changed commit hash or an imported
result row alone is not this acceptance. Use target object/tree reads; a ref
CAS does not update a checkout index.

Preserve the newest independent review's remaining finalization requirements:
prove exact custody for already-at-candidate adoption or hold conservatively;
recheck the exact live grant immediately before the separate Authority
integration effect. After actual A/B, exercise the single configured-alias
branch with no fetch/write effects and focused stale-target/ended-grant controls.
The identity-only alias test is insufficient. No repeated P/Q collections.

Affected tests/reasons: tests/tools/test_stage_execution.py for ordinary receipt
timing, actual A/B completion and configured-alias refusal; tests/integration/
test_driver.py and test_execution.py only as needed for the remaining bounded
receipt/finalization controls. Standing W71830 authority covers these changes;
record exact methods and changed expectations in the author handoff. Other
allowed paths remain those enumerated by owner137905. W136578 stays parked.

Author remains 47.12894061299539/65s,39 timed runs,13 nonzero exits, plus all
previously disclosed unmeasured history. Claim138839 added no timed execution.
Reviewer now 3.6051185639982584/10s, including a conservative0.1s charge for
unchanged43-entry preflight (measured0.0021296079976309557s), no product tests.
Retained manifest: evidence/dispatch-138861/result.json; ten immutable base
copies remain in evidence/dispatch-138824/. No reset, transfer or cost waiver.

Operational lookup note: reviewer initially searched the nonexistent
worker_manager/review_driver.py; the actual readable owner is
job_manager/review_driver.py. This was a path lookup error, not a missing
repository capability; the real owner was read before this design was pinned.
