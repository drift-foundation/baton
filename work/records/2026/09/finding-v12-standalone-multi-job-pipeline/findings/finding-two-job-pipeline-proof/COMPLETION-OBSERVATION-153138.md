# W71879 — outer reconciled completion observation, tuner153138

Owner153133 and parent FINDING/PLAN 2026-09-12T14:17:40Z assign this localized fix and direct operator feedback. StageObservation now lets the existing Integration.account select reconciled evidence before direct-runtime prerequisites. A completed model-free B import is visible through the public observer and status projection with runtime_id=null and execution_runtime=absent. Generic stages still return no integration observation; integration attempts without runtime or reconciled evidence remain unstarted. Read-only Authority/coordinator owners and all account identity, receipt, lease and handoff checks remain in control.

## Exact operator test

From `/home/sl/src/baton/v12/python`, run this one command (six deterministic tests, no live provider or Docker runtime):

```sh
/usr/bin/env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:. /usr/bin/python3 -m unittest tests.tools.test_stage_execution.TwoBoundJobsTraverseServingAndCorrection.test_readonly_reconciled_completion_without_runtime_reaches_outer_observer tests.tools.test_stage_execution.TwoBoundJobsTraverseServingAndCorrection.test_readonly_integration_observation_keeps_the_bound_job tests.tools.test_stage_execution.OrdinaryTerminalLifecycle.test_fresh_process_observes_owned_completion_after_serving_closes tests.tools.test_stage_execution.TheObservationSurfaceIsSeparateAndReadOnly -v
```

Return the result directly through ops under the accepted localized fix/test loop. No intervening reviewer-model turn is scheduled. The new regression uses the existing disposable-store/two-Job fixture and simulated engine/provider turns; it is not the queued full real-container fake-provider coordination deliverable, nor live-provider acceptance.

## Changes and verification

- `v12/python/tools/stage_execution.py`: remove the premature runtime guard and clarify account selection (three executable lines removed).
- `v12/python/tests/tools/test_stage_execution.py`: one additive regression completes a real fixture reconciliation, invokes the outer observer and ordinary status projection, and checks both Jobs completed without inventing a B runtime. It also checks unstarted/generic behavior, foreign Job/offer refusal, missing handoff staying answered, missing receipt refusing, no serving acts, and no additional runtime launch. Existing assertions are unchanged.
- Before the fix, the new test failed at outer observation (`None` versus the owned completed account); `evidence/completion-observation-153138/red.log`. After the fix, both new and direct-runtime bound-Job tests passed; `green.log`. Four existing read-only controls passed, including a fresh process after serving handles close, unchanged store bytes/modes, missing/foreign owner refusal and handle disposal; `readonly-controls.log`. Six tests pass overall; scoped `git diff --check` passes.

Exact base/candidate bytes, SHA256 manifests and the localized `change.patch` are in `evidence/completion-observation-153138/`. The old358-entry run10 manifest verifies when its two authorized source paths resolve to their saved pre-fix bytes; all other entries match directly. Original run10 result and both genuine old execution markers match their preserved hashes. Old bindings describe the old candidate; they do not approve this changed source or authorize a rerun.

## Evidence and cost

Run10 remains an interrupted unsuccessful live proof: KeyboardInterrupt after943.8339926240151s, terminal_both=false, exceptional_stops empty. The parent's recorded B pass at14:07:15.580Z and allocation release at14:07:16.626Z diagnose the completion-observation stall; these timestamps are attributed to the parent, while the exact run result was independently copied and hashed here. No rerun, repair, rebuild or acceptance marker was made.

Measured checks this claim: 5.786528437980s (including the expected red reproduction), cumulative recorded preparation/checks 117.561877902916s plus retained uncertainty. Nine earlier failed walls plus this interrupted wall total 2945.872874202047s. Managed claim wall at this record is 507.734s since14:19:10Z; this includes reading/reasoning/context compaction/editing/checks and is not model billing time. Final pass latency is separately recoverable from canonical events. `cost-and-marker-check.json` retains the sample and precise values.

Implementation and local verification complete; awaiting operator test feedback through baton.ops. Run10 success is not claimed. The full deterministic provider A/B scenario remains queued after this localized feedback step.
