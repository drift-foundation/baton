# W385331 — recovery review preparation

Prepared by baton.codxpc, 2026-11-20T17:33Z. Planning only; no claim, candidate edits, tests, or acceptance verdict.

## Current authority and ownership

The owner's recovery instruction selects K to complete the retained candidate directly in an isolated copy, then codxpc to independently review the digest-bound result. This supersedes the unresolved recovery-choice wording and illustrative codxpc implementation assignment in the pilot recovery DIAGNOSIS.md §7–8 and M385352. It authorizes no blind retry, live launch, host import or Git mutation. K owns continuation edits; this checklist is reviewer-owned preparation only.

Canonical W385331 readback at snapshot385352: queued, route baton.decide, handler null, episode385343. No completed packet or claimable review assignment has arrived. Claim the assigned review Work only when routed, then read its complete current handoff and dossier before execution.

## Inputs and scope

- Normative v12/DESIGN.md, especially SCH-2a and LIM-5; this dossier's FINDING.md, PLAN.md, FIRST-NATIVE-SLICE.md and NATIVE-TASK.txt; accepted preparation M385344.
- Recovery evidence: work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-recovery/DIAGNOSIS.md and its indexed custody, reconstruction and test logs.
- Original candidate a743edebacf5c744020083ee68549f2bd1fa91f7, 24 changed paths over 3d05430f97ca9d4a516b51d15eb940840a6f0eff. Native Job w385331-handoffs-1 timed out; mandatory verification and native review did not run. These are recorded historical observations, not a fresh runtime inspection.
- First slice: durable clarification/in-scope finding, authorized reviewer response, exact retained continuation of the same admitted task. Work filing and dependency disposition are the following slice; W385331 is not complete merely because this source slice passes.

## Packet and provenance checks

1. Verify the completed packet's full manifest and hashes, selected base, retained-candidate identity, author delta and final changed-path inventory. Reconstruct without Git mutation and compare the exact reviewed bytes. Enumerate existing test changes and their behavioral justification. Do not substitute host files or alter frozen custody.
2. Account for the interrupted module, missing tools test module, module registrations and documentation. Verify every changed Python module loads and every new test module is registered exactly once. Confirm fixtures and all acceptance inputs are recoverable outside disposable scratch.
3. Bind each test result to the completed candidate and invocation/environment. Retain failures, skips and measured durations. Historical existing-module passes are regression evidence only; they establish neither completeness nor acceptance of the new behavior. Treat environmental explanations as established only to the extent demonstrated on a matched base.

## Behavioral acceptance checklist

- Exercise the real declared worker-output and serve_exchange boundary with deterministic providers: partial and unchanged checkpoints can yield clarification or an in-scope finding without final verification. A completed invocation yielding a question does not publish a successful production result, satisfy a stage dependency or mint technical-review/approval receipts. Missing, mixed, malformed, tampered and foreign envelopes fail closed.
- Check immutable versioned contracts/templates and qualification: old consumers retain their contract; new outputs require the new qualified capability. Unsupported deployed images must not silently acquire support.
- Bind attribution to the actual assignment, Authority, Work, Job, attempt, participant, generation, line/checkpoint and task digest. Worker-supplied identity cannot impersonate an author. Responses require the explicit scoped reviewer capability, exact pending request and checkpoint; route membership or receipt-actor identity alone grants nothing.
- Prove routine request → configured reviewer → producer continuation needs no owner messenger or acknowledgment. Unresolvable ambiguity emits one attributable escalation to the authorized higher decision recipient, with evidence/options/recommendation; no reviewer self-loop. Unsupported filing/dependency dispositions remain held.
- Prove source/checkpoint and continuation restoration are exact. The answer is separately digested input; admitted task/specification digest, scope and base remain unchanged. A clarification is neither reject_plan nor a forged changes-requested correction. A real scope change cannot enter through this path.
- Check positive cessation/fencing of the exact outgoing writer before transfer. Retention, message, route and Job episode reconciliation must leave admission inhibited at incomplete boundaries, with no overlapping writer or executable wrong-owner window.
- Exercise replay/restart cuts at freezing, message commit, route/fence transition, response and episode opening. Identical operations return the same durable effects; changed operands, stale request/generation/checkpoint and foreign replies refuse. No duplicate messages, response episodes or continuation spending.
- Exercise cancellation pending response, during response and before resume, including late output/admission replies and restart. Terminal/cancelled work cannot resurrect. Unknown cessation or timing retains the hold; cleanup does not erase evidence or stop a replacement generation.
- Check the new finite policy: one resolved continuation, separate from zero code-correction rounds; original stage/Job/provider/verification ceilings remain enforced. Restart and replay do not reset clocks or double-spend. Exhaustion visibly holds. Final submission still receives normal independent technical review; a zero-correction profile cannot admit a correction by relabelling it continuation.
- Confirm readback/status preserve awaiting-answer, escalation, stale/unknown runtime and retained checkpoint details, without reporting clarification as Job success or implementation failure. Existing CLI/shared read model and ordinary final-review behavior remain compatible.

## Focused verification plan

Run the completed candidate's six required modules with deterministic providers and sensible per-run timeouts, preserving exact commands, exit status, counts, failures/skips and measured duration:

    tests.authority.test_work_messages
    tests.job_manager.test_native_handoffs
    tests.tools.test_native_handoffs
    tests.job_manager.test_role_contract
    tests.manager.test_output
    tests.job_manager.test_job_control

Inspect test quality against the behavioral checklist: helper-only assertions cannot replace the joined request/response/continuation proof. Select additional focused regressions from the actual final delta (adapter declaration, capability, templates, session/boundary/dossier, review driver, stage execution, correction/restart and observation as affected). Reuse applicable retained evidence, but rerun where changed bytes invalidate it. Account separately for candidate/base failures and any unexecuted coverage. No live model, actual engine campaign, packaging deployment or host import is part of this preparation.

## Disposition and separate observation

Post the eventual verdict in the assigned Work's thread with exact decision/review/evidence paths, candidate identity, test accounting and limitations. Pass routine corrections directly to the configured implementation endpoint; escalate only a genuine unresolved scope/design/authority decision. Acceptance of this source candidate is not retrospective success of the failed native Job, runtime deployment qualification, or completion of the later discovery slice. After any claim, pass and verify canonical handler release before ending.

The separate status timeout observation remains at work/records/2026/10/finding-v12-development-coordination-pilot/evidence/native-handoffs-1-recovery/FINDING-status-cause-unknown.md. It is not an acceptance condition for this candidate. No overlapping status edits or new execution are started here.
