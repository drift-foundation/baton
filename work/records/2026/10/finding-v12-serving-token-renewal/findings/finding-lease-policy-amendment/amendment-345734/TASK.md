# W333485 — bounded permission supporting the selected execution envelope

Implement the smallest correct host permission policy in the isolated private
candidate at base bc925cf5c62d69426ed5862af4d41f4d2a967b0f. Read v12/DESIGN.md and
/input/source/work/records/2026/10/finding-v12-serving-token-renewal/findings/finding-lease-policy-amendment/amendment-345734/TOK-9.md,
the frozen owner-approved current TOK-9.
The latter supersedes the historical base's fixed-duration interpretation.
Owner345677 explicitly supersedes continuation-339444/TASK.md's no-duration-increase
rule, mandatory900/four-renewal restriction, and mandatory periodic-renewal design
for this prospective correction. It does not alter existing tokens or Job limits.

Permission must support populated Job execution limits and required cleanup
reserve without an incidental900-second ceiling. Choose the smallest correct
mechanism: a bounded initial duration derived from the selected execution/cleanup
envelope is a preferred investigation, not a mandated algorithm; actual timely
eligible renewal remains an alternative. No arbitrary larger replacement constant,
global unlimited permission, broad scheduler redesign or merely unused renewal API.

## Inputs and first working milestone

Three digest-bound UNACCEPTED partial buffers remain available through the original
continuation-339444/PARTIAL-INPUT.json and candidate-input paths under /input/source.
They are provenance and possible implementation inputs, not a mandatory algorithm
or accepted code. Inspect them before deciding whether they help the minimal fix.
If using them, use the unchanged hash-verified LOAD-COMMAND.txt/restore.py from
that continuation; validate every base/buffer before writing the private candidate.
Do not edit the mounted source, original instances or original buffers. You may
replace the partial design within the accepted outcome rather than preserve its
unresolved timing/cancellation races. Record which inputs were used or rejected.

First trace how populated invocation limits and cleanup reserve reach actual host
acquisition/serving. Observed starting points: PreparedGovernance.reserve in
worker_manager/workspaces.py calls tokens.acquire without explicit seconds;
tokens.acquire already accepts seconds. Revalidate these facts on the selected
base before implementation. A proposed longer duration needs an explicit bounded
derivation, acquisition/startup accounting, trusted-clock deadline semantics and
persisted inspectable policy/identity. Missing, invalid or ambiguous limits must
hold or use an explicitly justified bounded policy; never guess unlimited time.
Permission cannot reset or exceed Job execution deadlines. Explain separately
what execution time is allowed and what shutdown/cleanup reserve remains owed.

Build one integrated controlled-clock reproduction early: the real selected
production acquisition/serving path, populated3600-second execution limit and
cleanup reserve, substantive eligible execution beyond900 through3600, and prompt
cancellation/ending with unchanged Job limits. Exercise the public token owners,
not a mocked successful permission verdict. Fix ordinary demonstrated failures and
iterate in the same selected invocation while its unchanged limits permit. Then
complete the full safety matrix below. Do not spend another turn elaborating a
broad renewal design before obtaining this smallest useful proof.

If periodic renewal is chosen, prove timely decisions through blocking reconcile,
sweep and custom reclaim, plus authoritative eligibility serialization against
ending/cancellation/supersession; post-write ineligible reporting is insufficient.
The old120-second lead/30-second cadence is an unaccepted proposal, not a bound.
If initial-duration derivation avoids periodic renewal, prove its real producer
and consumer behavior, replay/restart deadline preservation and cancellation/
expiry enforcement; unnecessary new renewal races are not a delivery requirement.

## Full safety and verification acceptance

Use deterministic clocks and fake external engine/provider boundaries inside the
Job with real affected owners. Prove:

- Selected3600 execution plus required cleanup support; correct bounded derivation
  for differing populated limits, missing/invalid limits and acquisition/startup
  delay; no arbitrary constant substitution or extension of Job limits.
- Cancellation, end, supersession and stale/competing identity before/after the
  permission decision; same resource, assignment/generation, execution, operation
  and exact bound runtime. Activity alone grants nothing.
- Expiry/revocation and permission changes in both orders; expired permission is
  never revived. Existing/live tokens retain their original recorded policy.
- Effectively-once operation replay, lost reply, restart before/after commit,
  trusted-clock ambiguity and no cross-boot monotonic timestamp reuse. Restart
  cannot reacquire permission as a new full-duration budget for the same effect.
- Finite policy exhaustion, exact-runtime stop, required cleanup and unknown
  cessation holds; no reuse before positive cessation/fencing. Slow/unavailable
  engine control and unrelated attempts must not invalidate the chosen policy.
- Populated Job invocation limits remain unchanged throughout; no external I/O
  inside affected DB transactions. Preserve existing renewal API safety coverage
  even if the new production policy does not need periodic renewal.

Retain the complete formal gate unchanged: create
v12/python/tests/job_manager/test_serving_renewal.py for the chosen policy's
production-composition coverage, plus existing test_tool, test_sweep and
 test_execution_limits. The historical module name does not require a particular
algorithm. The sealed wrapper runs all four without skips and has a30-second
verification ceiling. Timeout is non-acceptance; never weaken tests or change
TMPDIR to conceal it. Supplemental focused tests inside this invocation are
allowed and must be reported with measured/unknown durations honestly.

## Execution, retained output and ownership

One selected authoring invocation, provider3600/verifier30 ceilings, outer4800 and
cleanup60, no retry, fresh context. These limits are unchanged. The unchanged
host at this base still acquires900-second permission and cannot hot-load its
candidate. This task does not promise a longer authoring run or authorize patching
that host. Parent must reconcile the changed manifest and honest effective host
policy with the owner before launch; access readiness alone is insufficient.
If interrupted, retain exact bytes, tests, unresolved seam and next finite step;
no second invocation, live-token mutation, old-instance recovery or self-acceptance.

No direct host implementation, live test provider, deployment, Git mutation or
sibling diagnostics implementation. Preserve accepted controller/shutdown/unknown-
hold behavior. Framework-owned private source preparation remains the runtime's.
Necessary bounded owner-side edits are allowed by outcome, not restricted to the
starting locations above. Record actual overlap with diagnostics' attempts/intake/
documents/delegation/projection/stack-command surfaces for serial integration;
never overwrite the independent diagnostic candidate. Return exact changed paths,
digests, actual Job/attempt/result/cessation evidence and limitations for independent
v11 review. W325959 retains joined acceptance and the human Git checkpoint.
