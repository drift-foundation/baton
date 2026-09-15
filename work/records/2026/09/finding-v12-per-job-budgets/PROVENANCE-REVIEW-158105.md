# W156162 provenance correction and independent validation

Reviewer claim158105,2026-09-13T05:44:15Z. This addendum supersedes the incorrect
counts, unnamed foreign ownership and generic five-test summary in
PROVENANCE-158092.md. Preserve that original packet as submitted evidence.

audit-158105.py/review-158105.json independently verifies all27 candidate hashes
against both provenance-158092.json and review158071, and all recorded existing
base bytes/hashes against f3fc9e12cc89bebf9524cd173103df7af67d5212. The named base
is supporting provenance; this dossier remains the canonical locator. No product
or test bytes changed. The supplied JSON's byte/hash inventory is accepted.

## Correct inventory

There are **six new paths**, not seven; **fourteen modified product/document
paths**, including stage_execution.py; and **seven modified existing tests**,
five Job tests plus two tools tests. Total27. The six new paths are the limit
owner, three limit test modules, schema4 golden SQLite fixture and its provenance
document. The modified product/document paths are DEPLOYMENT.md, five existing
job_manager sources, worker_manager/launch.py, four tools and three worker files.
Every full repository-relative path/base/candidate hash is in review-158105.json.
W156162 owns this finite scope except the retained W71879 changes below.

The source heading claiming all18 hunks belong to W156162 contradicted its own
foreign-hunk paragraph. The independently saved `git diff <named-base> -- <path>`
has16 source hunks (15 W156162,1 W71879) and6 test hunks (5 W156162,1 W71879).
Hunk grouping depends on diff options; use the exact saved diffs and per-hunk
headers/digests in review-158105.json rather than the author's18/7 counts.
The two snapshots are overlap-158105-stage_execution.py.diff and
overlap-158105-test_stage_execution.py.diff. Existing assertions in the test
file were not changed by W156162: its one changed call gains a Job context,
and the other additions are setup helpers/checks. Its foreign addition is a
whole regression method.

## Exact foreign provenance and integration boundary

The foreign Work is **W71879**, bound to
baton:work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof.
Its COMPLETION-OBSERVATION-153138.md and
evidence/completion-observation-153138/{change.patch,base,candidate} preserve the
localized owner153133/tuner153138 change. Canonical detail at snapshot158113
reports W71879 closed/satisfying, last_change_seq153653; calling it an unnamed
in-flight Work is stale. This does not itself authorize a new integration import.

Both saved foreign BASE files exactly equal today's named HEAD base files.
Both foreign CANDIDATE methods exactly match the corresponding current methods:

| Path/method | Foreign candidate whole-file SHA256 | Current matching method SHA256 |
| --- | --- | --- |
| tools/stage_execution.py: StageObservation.observe_integration | 44de0f895df8d8c0fcd80c6e244d28cd9ed130d34b737447dd98532d42428776 | edace97b4ff4ab1566cf70df63cfa6d59faa881e28fef314a5cdd028c31dfc69 |
| tests/tools/test_stage_execution.py: test_readonly_reconciled_completion_without_runtime_reaches_outer_observer | 908dca6c11c452a54b224dec421aae2e420229a4cbee85dd358c910a98cb4e28 | aa23adc2757f95a6812115a3896bd61b132826e512e4db3db119e3d2a3055d7d |

Both paths have prefix v12/python/. The first delegates account selection before
runtime prerequisites; the second is its additive61-line regression. These are
textually distinct from W156162's Job-context and budget hunks. All current
verification used the combined tree, so semantic independence or a passing tree
with both foreign hunks excised is not certified. No foreign bytes were excised,
imported or absorbed here. Integrator must preserve/validate this base dependency
or prepare a separately reviewed separated candidate; this is not import approval.

The13 stage-module errors are a retained unresolved comparison against earlier
W156162 candidates, not a demonstrated unchanged-HEAD baseline. This explicitly
corrects the packet's misleading `long-standing` shorthand; no new run is needed
to relabel the existing evidence honestly.

## Exact five-test authority request

The following current changes remain pending M157653. Each is consistent with
the accepted feature behavior, but this content evaluation does not grant the
missing case-specific authority. The old W71830 standing exception has ended.
All paths below have prefix v12/python/tests/job_manager/.

| Path | Exact existing expectation/fixture change |
| --- | --- |
| test_documents.py | Preserve submitted /1 explicitly instead of comparing to current SUBMISSION_SCHEMA /2; move unsupported-version negative input from now-supported /2 to /9, retaining schema refusal assertions. |
| test_exchange.py | One status-schema assertion moves /4 to /5. |
| test_tool.py | Two status-schema assertions move /4 to /5. |
| test_scheduling.py | Import SCHEMA_VERSION; remove job_execution_limits in both schema3 reconstruction helpers; three migrated-version expectations move literal4 to current SCHEMA_VERSION5. Other scheduler assertions remain. |
| test_store.py | Remove job_execution_limits when reconstructing schema2, alongside the existing removal of later scheduler tables; no existing assertion is changed. |

Existing tools/test_single_worker.py and W156162's tools/test_stage_execution.py
changes are setup-only under PLAN/review-2026-09-13T02:19:56Z and later bounded
context clarifications. New tests and product/document paths retain their accepted
finite Work scope. Any integration candidate still requires exact digest-bound
independent review and the owner's pending five-test disposition.

No runtime tests were repeated. The read-only audit cost0.035886002999177435s is
charged: reviewer cumulative58.29267580300984s. Author remains155 measured runs,
1308.9765907300025s plus the same four unknown-duration activities.
