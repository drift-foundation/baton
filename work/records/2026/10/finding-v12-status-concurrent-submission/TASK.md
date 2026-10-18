# W319114: make Job status safe across concurrent submission

Work only in your private candidate checkout at declared base
9055843b5d258f5bfbb523815d034ee0c14075d6. Deliver a small code-and-regression-test
proposal. Do not edit the mounted source or host records. No live providers,
Docker operations, deployment changes or broad suite cleanup inside this task.

Observed failure: baton_v12.job_manager.projection.status calls stage_states,
then job_rows and stages_of; a concurrent public submit can commit new stages
between those reads, and held[row['stage_id']] raises KeyError. Reproduce with
real separate writer/read-only connections and a deterministic interleaving.
An empty store, stage_states returning its real empty result, then public
submit(writer, tests.job_manager.fixtures.submission()), then the remaining
status code is a minimal baseline. No raw SQL is needed for the race.

Required: coherent Job-store materialization or explicit bounded safe
retry/refusal under concurrent submission and advancement. Preserve status
shape, readonly capability, authority/schema validation and ordinary serving
callers. Do not silently omit new stages or mix impossible episode/receipt/
allocation combinations. No cross-store atomicity claim is required.

Read DESIGN DB-1/DB-4 and OBS-1 before changing code. Never hold a Job-store
transaction while calling operations, another store, filesystem/engine observers,
or arbitrary callbacks. A read transaction around the whole status function is
not acceptable. Suggested approach: materialize the Job-owned rows coherently,
release that boundary, then acquire external observations and compose the result.
An alternate bounded safe retry/refusal is permitted. Avoid broad refactoring.

Relevant starting locations: job_manager/projection.py status, stage_states,
_stage_status; submission.py row readers; JobStore read capabilities; existing
tests/job_manager/test_status.py and tests proving DB transaction exclusion.
These identify evidence, not an exclusive edit list. Record all changed paths.

Verification must demonstrate the original race is resolved, ordinary empty and
populated reads still work, state stays unchanged, and external/cross-store
observation happens outside Job transactions, including failures. Exercise a
concurrent advancement or equivalent materialized-row coherence case as well as
submission. Use deterministic fixtures only. Add relevant regression cases to
the existing status suite so the frozen verification command runs them.

The complete repository at the declared base contains the Python sources, tests
and canonical fixture paths. From candidate root use Python3.13+; change cwd to
v12/python and set import paths to that directory and its src only. Installed
jsonschema is required. Do not use host PYTHONPATH, network installation or a
partial copied fixture tree. Report missing context separately from test failure.

Return the retained Git proposal with exact base/head/tree, binary patch,
complete changed-path list, verification outcome and known limitations. Never
self-approve it. A separate baton.rvpc review judges the immutable checkpoint
and reruns focused verification before owner acceptance/integration. No automatic
correction/retry is selected; a failed/changes-requested result returns for
coordination with retained evidence.
