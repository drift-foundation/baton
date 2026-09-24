# Do 1, 2, 3 — preserve the stop and make each result testable

2026-09-24, baton.tuner claim257612; owner257608 following M257333/M257341.
**Planning complete; adoption NOT READY. No implementation cycle restarted.**

1. **W257624: protect and recover failed-run resources.** Select R1 exclusive
   pre-effect submission first, then independently accept R2 exact clearance,
   R3 cross-entry protection, R4 bounded recovery and R5 validated grants and
   recovery command. [Stage contracts](../finding-v12-failed-run-resource-hold/PLAN.md)
   name commands, inputs, paths, evidence, failures and stop points.
2. **W257627: diagnose the original agent fault, then prepare a fresh packet.**
   D1 read-only diagnosis can start alongside R1 on disjoint files; D2 packet
   sealing waits for accepted diagnosis/correction and W257624. [Stage contracts](../finding-v12-startup-failure-fresh-packet/PLAN.md).
3. **W247941: prove the joined independent parallel behavior and return the
   adoption decision.** Reuse accepted evidence where it applies; run only the
   missing bounded deterministic witness, then separately select any actual
   engine/provider question. No new broad recovery or diagnosis work here.

## Ownership and scheduling

| Work/stage | Proposed handler | Writable boundary after assignment | Stop |
| --- | --- | --- | --- |
| W257624 R1–R5, one stage at a time | baton.claude via baton.impl | Existing five product files and old focused fixtures remain Claude's; per-stage edits narrowed in provider PLAN; new provider tests/docs | Independent stage acceptance; no auto-expansion |
| W257627 D1 | baton.codxpc via baton.codx | New diagnosis/evidence/test files in its own dossier only | Causal diagnosis or exact missing diagnostic; no product correction |
| W257627 D2 | baton.tuner via baton.tune after serial handoff | New packet docs/fixtures in its dossier; no takeover of Claude's composer/helpers | Accepted literal packet and remaining execution selection |
| W247941 A1 | baton.claude, retaining original test/composer ownership | Exact parent proof fixtures and adoption report; product read-only | Independent combined evidence assessment |
| W247941 A2 | Owner-selected operator; baton.rvpc reviews | Fresh selected execution evidence only | READY/NOT READY within exact configuration |

Both new Work records are at **baton.decide**, not implementation queues.
The owner may select R1 and D1 independently; this plan proposes assignments,
it does not transfer file ownership. Reviewer route remains baton.bug → rvpc.
Do not launch a second reviewer/implementer under an existing participant.

The **first executable action** is D1's bounded file-only retained-outcome read.
The first implementation action is R1's existing two-selector baseline followed
by the late-helper/concurrent-submit regression. Those baseline tests are not
R1 acceptance; planned new test modules are clearly labelled as undelivered.
No test, child process, image, provider or deployed store was run for this plan.

The owner can select the proposed starting assignments with standalone commands
using the supplied launcher as baton.slaw (tuner does not impersonate slaw):

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw reroute work=W257624 to=baton.impl reason='Select R1 only per PLAN.md: exclusive pre-effect hold, narrow custody.py and focused regression scope. Preserve ownership and stop for independent R1 review; no live or deployed operation.'
```

```sh
/home/sl/opt/baton/v11/0650c61/bin/baton --config /home/sl/baton-v11.14aecfb/baton.json --participant baton.slaw reroute work=W257627 to=baton.codx reason='Select D1 only per PLAN.md: read-only executed-image startup diagnosis; writes confined to new dossier. No product edits, live run or deployed recovery; stop with evidence-bound result for independent review.'
```

## Dependencies and why

W247941 keeps its satisfying W239533 dependency and requires W257624 and W257627.
These are separately schedulable prerequisites, not contained children or
duplicates. W239528/W239533 and W236087 are neither reopened nor reclassified.
W44342 remains parked and is not made a prerequisite. Reuse, broad hardening
and automatic integration remain outside this initial-adoption gate.

Do **not** block all of W257627 on W257624: that would prevent the independent
D1 diagnosis. D2 has a precise intra-Work stage gate on accepted W257624; the
owner/reviewer must enforce that gate when selecting D2. Actual ledger edges
and any authority refusal are recorded in CHECKPOINT-257612.md. No hidden
dependency or ownership transfer is implied by source imports.

## A1 — the selected packet demonstrates both Jobs, independently

Prerequisites: accepted W257624 recovery/protection machinery and W257627's
fresh packet; revalidate its immutable snapshot/image/source/task bindings.
Outcome: one deterministic run of that exact command records overlapping
active implementation, separate resources, two frozen attributed verdicts,
stopped runtimes and positive cleanup for all admitted attempts. Use a barrier
or actual interval evidence, never two submissions or total test count.

Existing baseline selectors below are verified by source inspection. Rebind
the proof's hard-coded historical SNAPSHOT and any imported helper provenance
to the **accepted successor** before treating it as A1 evidence; otherwise it
only tests historical inputs. Do not edit the preserved snapshot. Include a
focused new negative if a changed seam is not covered, rather than rerunning
the broad suite. Use fresh authorized disk-backed scratch outside the checkout
and snapshots, with fixture-owned cleanup and no live backend.

```sh
cd /home/sl/src/baton
export PYTHONPATH="$PWD/v12/python/src:$PWD/v12/python:$PWD/work/records/2026/09/finding-v12-real-jobs-adoption-gate"
timeout --signal=TERM --kill-after=5s 120s /home/sl/.local/state/baton-v12-venv/bin/python -B -W error::ResourceWarning -m unittest test_two_jobs.BothJobsAreActivelyExecutingAtOneObservedInstant.test_both_implementations_are_waiting_at_the_same_instant test_two_jobs.EachJobCollectsItsOwnFROZENAttributedVerdict.test_both_verdicts_are_derived_from_their_own_frozen_results test_two_jobs.TheSHIPPEDTemplateComposesThroughTheACTUALCLI.test_the_DOCUMENTED_COMMAND_reaches_four_attempts_and_two_verdicts
```

Real manager, stores, filesystem and attribution; simulated engine/provider.
Retain exact imports, hashes, admission/attempt/runtime/Job mapping, overlap,
result digests and cleanup/retention receipts. Forced held/timeout/zero-admission
paths must report NOT READY, never settled success. A1 does not establish the
actual daemon/provider behavior. Stop for independent evidence-continuity review.

## A2 — exact adoption recommendation, not a larger development campaign

Input: accepted A1 and the prior accepted live implementation/reviewer evidence,
plus historical parallel evidence with explicit configuration differences.
One outcome: READY FOR REAL V12 DEVELOPMENT JOBS within named limits, or
NOT READY with one exact unmet proof and next action. Reuse adequate evidence.
If a new real-engine/provider run is necessary, state its specific unresolved
question and obtain selection of D2's **literal reviewed command** first.

No live command is printed here: the current one uses an unaccepted candidate
and consumed run. The repeatable command is the future accepted D2 operator
packet's create-fresh/start/status/stop sequence, with immutable packet locator
and digest recorded in A2 before execution. Until supplied, A2 is not executable.
A real run is one selected attempt, not an automatic retry loop; failed evidence
is retained and recovery follows the independently reviewed procedure.

Acceptance requires overlapping execution, isolated workspaces, correct attempt
and result attribution, independent reviews, and **positive cleanup**. A durable
hold is safe failure behavior, not adoption success. Do not erase the preserved
run's outstanding resources: actual cleanup or explicit validated quarantine
and disjointness accounting must accompany any new run selection, and unknown
prior effects remain a blocker where they can reach the new resources.
Return to baton.decide; human plus agent integrates accepted results. No
automatic integration, session restore, W236087 completion or wider guarantee.

## Preservation and escalation rule

All nine stopped-checkpoint hashes matched at tuner pickup; the owner WIP commit
is a recovery checkpoint, not acceptance. Historical records and PROGRESS remain
unchanged. Partial accepted components stay accepted only within their cited
evidence; the five latest blockers are not erased by 966 passing tests.

If a stage reveals an unrelated capability or extra shared file requirement,
record the exact finding, proposed owner/path and dependency before expansion.
Do not scatter changes across the system or restart this old all-in-one loop.
The existing per-stage test authority is not an additional permission gate.
