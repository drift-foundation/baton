# W361910 — Versioned ordinary Job template resolution

## 2026-10-26 — bounded allocation from W321608

Owner authority: ../finding-v12-development-coordination-pilot/FINDING.md,
2026-10-24T00:36:47Z; accepted pilot closure E361852. DESIGN SCH-1a records
that approved contract. W321608 retains joined acceptance; this is no new live
execution or cutover selection.

Deliver one reusable implementation-to-independent-review template, with explicit
version selection and a deterministic manager-owned resolver. The request supplies
task, source, scope, acceptance and permitted overrides. The resolved result shows
and pins template version, stages/roles/dependencies/consumed results, candidate/
verification/review contracts, completion/correction/failure rules and effective
execution/verification limits. Deployment supplies workers/credentials/capacity.
No template language, arbitrary workflow editor or additional stage family is
selected. Wire schema and API spelling are implementation choices within this
contract; unknown versions/members and forbidden overrides must refuse.

Acceptance: resolve explicit and configured-default selections with visible exact
version; preserve task/source/scope/acceptance and override origins; reject invalid
versions, missing required input, dependency/result mismatch and disallowed limits;
prove normalized output is compatible with the actual submission/consumer contract.
Changing a template/default cannot reinterpret a previously resolved/submitted Job.
Preserve old submission contracts and fresh-attempt behavior. Focused tests must
exercise real normalization and consumer boundaries, not only expected dictionaries.
This slice does not claim admission, launch timing or complete workflow acceptance.

## Evidence and boundaries

Observed current code: job_manager/documents.py closed submission contracts;
submission.py:submit atomic intent/identity ownership; fresh_attempt.py:admit
existing retry owner composition; tools/job_manager.py document submit/fresh-attempt
CLI; tools/bootstrap.py:_compose Work and grant binding. Paths are relative to
v12/python/src/baton_v12 or v12/python as appropriate, evidence locations rather
than an exclusive edit list. Implementer revalidates against current source.

No broad refactor, template framework, live provider/engine execution, deployment,
migration, installed-instance mutation or Git mutation. Use deterministic focused
verification under current direct-development policy. Ordinary test changes within
scope are authorized; record actual changed test paths/reasons. Preserve genuine
defect coverage and exact candidate provenance.

## 2026-10-26T17-46-15Z — candidate361943 needs resolver contract correction

Independent review review-2026-10-26T17-46-15Z.md confirms all candidate/base hashes and137 focused
passing tests. Targeted real-consumer probe shows saved3600 limit resolution
admitted as7200 after a default-generation change; public template_of leaks
mutable definitions; scope is narrowed to test_scope. Exact evidence and required
behaviors in that review and evidence/review-362222/. No product acceptance.
Keep one bounded resolver correction; W361912 remains gated. No new owner scope
choice or decomposition is needed. Prior implementation-readiness acceptance
remains historical and does not constitute acceptance of candidate361943.

## 2026-10-26T18-08-59Z — earlier findings resolved; consumption validation remains

Review review-2026-10-26T18-08-59Z.md accepts the R1–R3 corrections as observed behaviors, not
the candidate overall. Candidate362249 hashes match and167 focused tests pass.
New submission_for_admission leaves seven malformed nested JSON cases as raw
AttributeError/KeyError/TypeError instead of ContractRefusal. R4 requires bounded
nested input validation before reconstruction; evidence/review-362383 retains
the independent probe. Keep W361912 gated. No extra scope or schema bump selected.

## 2026-10-26T18-18-45Z — resolver candidate accepted

Independent review review-2026-10-26T18-18-45Z.md accepts candidate362407 manifest
cdb05010acc18113d78f1197f3370d6b770bb7e3ee1beb016f6f3968ca7116e3.
All three hashes/base match;181 focused tests pass and unchanged reviewer probe
confirms R4 typed refusals with R1–R3 preserved. Exact evidence/review-362455.
This supersedes current changes-requested status, not historical findings.
Owner disposition/import/Git checkpoint remain; W361912 must consume the full
digest-bound resolution through real manager admission, not only its legacy
submission signature. No deployment or runtime acceptance asserted.
