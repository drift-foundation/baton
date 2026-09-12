# Run9 reconciliation and proposed accounting correction

Owner150381; tuner claim150384; 2026-09-12. This completes the requested
reconciliation/proposal. It does not authorize implementation or another attempt.

## Actual outcome

Run9 remains an incomplete proof. A integration completed; B reached its real
derived judges. Review and approval accepted the merged candidate. Verification
was interrupted by the enclosing integration deadline, with no retained terminal
answer or frozen verification report. No provider failure is established, and no
eventual verification success is inferred. Both-terminal/final-target acceptance
was not reached. No ordinary operator transition occurred.

The exact retained root is `/home/sl/.local/state/baton/v12/w71879-run9`, Authority
`c71879b3000000000000000000000001`. The evidence directory
`evidence/run9-budget-150384/` retains result bytes, source hashes, public Authority
assignments, stage transitions, last status, bound judgment documents/reports,
verification exchange states, Docker observations and timing calculations.

| Fact | Evidence |
|---|---|
| A integration claim/pass | 05:56:29.042Z / 05:57:50.118Z, 81.076s; Authority events9/10 |
| A stage completed | samples.jsonl:117, wall285.0841938230151s |
| B integration claim | 05:57:52.183Z, event11, W2 generation3 |
| B's old 120s deadline | 05:59:52.183Z, computed from that claim |
| Verification claim | 05:57:52.341Z, event12, W3 generation1 |
| Verification's own 180s deadline | 06:00:52.341Z; 60.158s remained at B's deadline |
| Approval frozen/pass | 05:59:45.122Z / 05:59:45.143Z; claim-to-pass112.567s |
| Review frozen/pass | 05:59:52.168Z / 05:59:52.189Z; claim-to-pass119.729s |
| Last sample | number154, wall401.79450912901666s; verification and review then running |
| Verification container stopped | `3fbd01bf2553e7605c056fa17709a89acfbfb2b56137de68770fc7cd93ca731c`; finished05:59:54.534110797Z |
| Recorded final wall | 408.2074813900108s, including containment/cleanup |

Review passed 6ms after the calculated enclosing deadline, during the end-of-run
window; the last sample predates that pass. Its retained frozen report and fresh
public Authority event16 supply the later evidence. Do not rewrite the last sample
to imply it already observed this.

Both retained report.json files match their sealed content-manifest byte counts
and digests, assignments, and the candidate/base/tree claims. They accept candidate
`440e36b8583936f6598ac1dc4cab6431be4d11e1`, tree
`868e5bd99c1f6da8f9fbda966772ea46fe6f7e95`, original base
`2fbb2d456638e5706218020aebfa47f0a82c8920`. The derived subject identifies job-b,
policy25, target revision `a2a6c8d5116458c6d5721766f5c1633d64552afb` and result
`result-86e13c1fe716246a07ea5ecd03f061713ca1e6a14ed73be4cddfead00e978ded`.
These checks establish retained report consistency, not a new canonical intake
receipt. The reports describe their own tests and limitations; their reported
test executions were not rerun or counted as tuner verification.

Verification's delivered judgment exactly matches that subject plus
`kind=verification`. Its retained exchange receipt and describe/work states match
the attempt, sequence and command digest: describe answered, work dispatched.
The output directories contain no files; no sealed result or terminal.json is
present. Public Authority still holds W3's original verification assignment.
Docker labels match that attempt/Work/generation/Authority, and the runner's exact
exceptional stop identifies its container. Exit137 with OOMKilled=false follows
the recorded stop-with-two-second-grace containment. It is not a provider verdict,
an OOM finding, or permission to retry. No credential payload, provider stream,
Docker log, or serve log was accessed.

Direct `docker ps -a` and label-bound inspection find **zero running and two
retained exited containers**: verification exit137 and A integrator exit0. Thus
the owner's “no remaining containers” means no remaining running containers;
retained exited containers still exist and were left intact.

## Why the old accounting stopped the attempt

`prepared-150007/run.py:32` sets integrator120 and each judge180. Lines175–198
charge every current/completed Authority claim from its claim timestamp and arm
one alarm to the smallest remaining allowance. B's integration claim therefore
keeps spending120 while three other Works execute their own180-second judgments.

`v12/python/tools/stage_execution.py:2465` dispatches/adopts judgments while the
derived result is published, then records all required evidence before calling
`admit_authorized_result`. `judge_result` at3249 and
`v12/python/tools/single_worker.py:2455` execute real independent workers; B's
reconciled import has no integration model runtime to time instead. This is an
enclosing proof-budget policy mismatch, not evidence that these judges violated
their180-second budgets. The run complied with the old approved guard. The
generic TimeoutError does not itself identify the winning clock; the bound claim
times and guard source establish which budget was earliest.

## Proposed smallest correction — not yet effective

Keep implementation240, original-review180, each derived-judge180,
integration120, and whole-run1200. Change only integration accounting in a new
proof package: charge its claim interval minus the **union** of intervals spent
by its exact configured derived judges. Preparation/reconciliation before the
first judge claim, gaps when no judge is active, evidence adoption, import,
post-import verification and settlement all continue spending the same cumulative
120-second integration allowance. Do not reset120 after judging or add three180
allowances to it. A's direct path receives no exclusion.

For B, the historical first judge started0.158s after the integrator claim. At the
old deadline this proposal would charge0.158s to integration and119.842s to
verification, rather than aborting a still-within-budget judge. This arithmetic
only explains the interruption; it predicts neither the judge's eventual answer
nor successful import.

The bounded implementation must meet these conditions:

1. Bind the interval to Authority UUID, B Job/stage/attempt and integrator
   assignment, exact immutable derived result/subject/policy, and all three
   configured judge Works/participants/generations. Use public owner readers:
   Authority assignment events and `reconciliation.result_of` via the read-only
   coordinator opener, plus validated retained judgment/exchange material.
   A label, a directory name, pending prose, an absent integration runtime or an
   unrelated judge claim cannot earn an exclusion. Refuse unavailable or
   contradictory required accounting evidence; never silently grant extra time.
2. Start each judge's180 at its own claim; end its interval at its corresponding
   recorded ending after the ordinary lifecycle. Clip intervals to the enclosing
   integration claim and subtract their union once. Apply the same computation
   to completed claims, including starts/ends between samples. No double credit,
   reset after polling, or restart-derived fresh allowance.
3. While an eligible judge is pending, arm the alarm to the minimum of the
   whole-run remainder and all active required-attempt deadlines; preserve the
   paused integration balance. As soon as the last judge ends, resume its
   remaining balance. Unaccounted intervals consume integration time. Independent
   per-judge expiry still stops the run; slow/missing dispatch cannot pause it.
4. Retain all three real accepted judgments, current-policy Authority receipts,
   coordinator authorization/import/lease release, A/B terminal stages,
   required tests, final whole-target tests and clean source/target checks.
   Claim endings alone never supply a verdict. Definitive required-judge failure
   must remain primary and stop promptly, with exact assignment/exchange binding;
   pending, quiescence and telemetry absence are not failures. Extend the
   proof-side observation helper for these separate Works if needed; do not
   substitute them into unrelated Job stages or call a serving factory to read.
5. Record the winning budget, identity, start/end/excluded/charged durations and
   allowance in failure evidence. Preserve early required-failure precedence and
   exceptional containment as secondary. Keep the whole1200 deadline in force
   through required final success checks: the old runner disables its alarm
   before those checks. Bound the final-test timeout by both30s and remaining
   whole-run time; cleanup can be reported separately but cannot extend success
   eligibility past1200.

Proposed file ownership is tuner, proof-package runner/new accounting helper and
focused dossier tests only, with FINDING/PLAN/own PROGRESS and immutable handoff.
Copy the prior accepted package into a fresh proposal directory; never edit
prepared-150007, its markers, historical source inputs or run9 state. Product
source, worker adapters, images, credentials and protocol are outside this
proposal. If adequate read-only evidence requires a product surface change,
return its exact missing contract for explicit assignment instead of widening
tuner scope.

Required offline cases: replay run9 times without asserting hypothetical success;
A unchanged; overlapping judges counted once; staggered/nonoverlapping intervals
and dispatch gaps charged correctly;180 judge expiry;120 nonjudge expiry before
and after judging;1200 during judging/import/final checks; completed history
cannot bypass limits; wrong/stale Work/assignment/result/policy and missing reader
fail closed; terminal rejection/provider failure preserves primary cause; all
three accepted receipts and existing success predicates remain necessary. These
are planned new budget-helper tests, not changes to product expectations. Existing
accepted63 offline cases should remain green when the actual correction is
implemented. No new implementation tests were executed for this proposal.

## Operational limitation and next executable step

The coordinator's public `IntegrationStore.open_readonly` refused run9's
`integration.sqlite3` with ContractRefusal(refused, precondition), underlying
`OperationalError: unable to open database file`. Metadata:0644 uid1000/gid1000;
WAL/SHM absent. The cause is unconfirmed. No raw database read, copy, sidecar
creation, permission change or repair was attempted. Therefore current canonical
coordinator state is not independently confirmed here. This exact opener failure
is an operational finding, to inspect through its supported read-only boundary;
it must not be bypassed in the proposed helper.

Next: independent feat review of this concrete proposal, Next ops for a ruling on
the accounting change and explicit bounded implementation assignment. Upon that
assignment, create the new runner/helper and offline cases above, obtain review
of the exact bytes, and return them before any model execution. Any later fresh
attempt needs its own applicable execution authority and genuine input bindings;
run9's one attempt is consumed. The replay below is executable now and only
reconciles retained evidence; it neither implements the proposal nor retries:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=v12/python/src:v12/python python3 work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof/evidence/run9-budget-150384/reconcile.py
```

It uses retained standalone Docker observations because embedded Docker is
unavailable under this managed execution boundary. It writes only its evidence
directory. The successful reconciliation checks154 samples, report/delivered
subject bindings, exact timing,198 unchanged accepted files and both unchanged
execution markers. Its internally measured cost is0.0418271119997371s;
cumulative preparation/analysis50.18569579989499s. Three initial utility failures
(empty directory assumptions twice, then embedded Docker exit1), other untimed
reads, the failed coordinator read and prior host/billing/rounding uncertainty
remain additional unmeasured spending. All nine failed runtime walls now total
2002.0388815780316s; run9's408.2074813900108s is added exactly once.
