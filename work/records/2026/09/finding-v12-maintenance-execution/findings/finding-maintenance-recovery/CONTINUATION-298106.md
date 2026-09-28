# W285465 execution limits — claim 298106

Authority: current PLAN and review-2026-09-28T18-12-21Z.md; owner297991 tuner implementation reassignment. Read events through298106, T285465 through298051 (no newer discussion at298117). Reviewer owns FINDING/PLAN/reviews. Tuner owns this note, attributable PROGRESS, and tests/tools/test_execution_limits.py for this milestone.

Baseline: direct integration14 tests,2 failures,4.321s; third-Job composed2 tests,2 failures,0.607s. Deterministic fake provider subprocess only; no live engine/provider.

Confirmed inspection: direct watcher replaces ClaudeAgent._ran_provider with a signature lacking scratch/umask now passed by _provider. Python rejects that call before its capture executes; integration records an uncertain held answer, which the old helper never inspects. Measure the injected subprocess runner timeout instead, require a successful integrated result, and retain timeout/start-error/replay controls. The third Job submits manifest_digest (R), unlike its two peers' job_input_identity (J), causing no matching producer admission. Correct the fixture Job identity, preserving full runtime manifest and all three independent tasks/ceilings. Revalidate composed outcome after this correction; do not assume downstream behavior.

No product decision changed. Pinning this rationale precedes edits. Whole G2 remains unaccepted; historical restart discrepancy and later scheduler/dogfood/final audit remain open.

## Connected result

After fixture correction: direct15 plus the two formerly failing composed cases17PASS13.171s. Configured60/default3600 observed at ClaudeAgent's actual injected run callback, forwarded to the deterministic provider subprocess. Helper now also requires integrated output, so an exception converted into held output cannot masquerade as a successful measurement. Existing successful-import and start-refusal assertions retained. Added injected TimeoutExpired at the same callback: configured60 observed, held/provider-failed, no imported target, exact terminal bytes preserved and zero callback invocations on replay.

Third Job now submits J while retaining the same full runtime manifest R; existing composed expectations pass unchanged. Three distinct tasks/ceilings remain, Job B's causal timeout77 is durably blocked, Job C waits on reserved/recovery-required integrator capacity, recovery frees nothing, and no Job C timeout or duplicate host execution is observed. No product timeout/lifecycle correction was necessary for these four failures.

This explicitly supersedes the earlier PROGRESS inference that the provider path was simply not reached by a branch. Absence of ContractRefusal did not exclude a Python argument-binding TypeError in the measurement wrapper. It says nothing about the separate scheduler/dogfood families or the unresolved historical restart sample.

## Verification and handoff checkpoint

Full tests.tools.test_execution_limits:142PASS69.710s. Prior module had141 tests; one timeout/replay regression added. No existing acceptance assertion removed or weakened. git diff --check passed for the entire current tree. Candidate file hash: candidate-298106.json (one changed test file; earlier accepted files remain untouched).

All claim298106 unittest measurements:4.321+0.607+13.171+69.710=87.809s, including failed baselines. No cumulative allowance gate; prior claim spending remains in earlier notes. Runs used /home/sl/.local/state/baton-v12-venv/bin/python -B -m unittest, PYTHONPATH v12/python/src:v12/python:v12/python/tools (absolute), TMPDIR and BATON_V12_DISK_ROOT pointing to work/scratch/w285465-298033, no bytecode, bounded timeout45s direct/combined,30s two composed baseline,120s whole limits module. All processes exited naturally; no live model/engine or Git mutation. No temporary probe left by this claim.

Read work-events through298106 with no newer events at298137; thread through298051, no newer messages at298117. Return baton.bug for independent limits acceptance. Next selected milestone after review: scheduler_trace9, then dogfood_operator10 and final integrated/path/hash/expectation audit, subject to updated canonical handoff. Historical restart setup request T298051 remains unanswered and must remain an uncertainty rather than a waiting gate. G2/parent and W257627 dependency unchanged and not accepted.
