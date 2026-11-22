# W385694 implemented candidate — E385742 / M385740

Ready for K independent review, not accepted/imported/packaged/live. Candidate identity is SHA256 of candidate-manifest.json:
`775fcfe42f02f26df96cd7de3b07bf17e033c16fd0949182949d2d72a2ff6a29`.
Base `2578aa70a44cc1e639b32cee9680b2151ed5a1c3`;11 paths. Exact replacement bytes in files/, old bytes in base/ (new test has no base), review diff candidate.patch. Manifest enumerates every path, old/new hashes and ordinary0644 modes. Reconstruct in a separate base checkout, verify all old hashes/types/modes before replacing with files/; no main import authorized here. Scratch development tree work/scratch/w385694-385742 is optional; packet retains all required candidate bytes.

## Change and authority

M385740 and owning FINDING/PLAN select descriptor baton.v12.development-role-contract.native-handoff.proposal100m/1 and template baton.v12.job-template.implementation-review/4. Decision-inputs/ preserves exact current owner records and normative DESIGN read for this assignment, including owner REC-9 pin. Source base predates that separate coordinator spec edit; it is not included/reverted by this candidate. W385695 publication-resume/schema10/worker remain outside scope. No shared product edits occurred in main checkout.

The new opt-in revision changes only proposal max_bytes to104857600. Existing descriptor/template bytes are pinned in tests; default /1 and /2,/3 behavior remain unchanged. Producer and validator share per-output approved expectations. Existing generic compose/create machinery carries the exact new declaration and refuses old-lane mismatch before creation effects. Both revisions remain handoff-capable. Docs explain both required selections and that this does not repair prior failed publications.

Product paths: role_contract.py and templates.py under v12/python/src/baton_v12/job_manager/, plus v12/STACK.md. Test paths: new tests/job_manager/test_proposal_output_limit.py, existing tests/job_manager/{test_creation,test_role_contract,test_templates}.py, tests/manager/test_output.py, tests/tools/{test_connected_creation,test_pool}.py, and tools/parallel_test.py registration. Existing exhaustive registry expectations extend to /4; connected creation extracts the unchanged /3 proof into a helper also run for /4 and adds exact declaration equality. Existing tests are preserved; new cases exercise revision selection, replay/refusal, measurement and limits. No assertion weakening.

Descriptor canonical digest: sha256:cf29ab07e507089520ba0c165b0661df0054f17fe35b986b4cf63c9ac713792e.
Template canonical digest: sha256:53ddac5c23e3b8065ff1579f65e6240978e608b59b2c853418b514262d51ed35.

## Verification and accounting

Final passing evidence: focused-final.log510/510 in20.826s; final-identity-regression.log180/180 in19.467s; manager-limit-final.log6/6 in0.061s. Zero failures/errors/skips in these final runs.696 executions,683 distinct IDs (deduplicated in test-accounting.json);40.354s summed unittest measured duration. Final new module8/8 includes pinned old/new identities. Registry partition/source-input checks pass. Scoped git diff --check passes. Commands and individual IDs are retained in logs/accounting. Commands use supported just test-one on prepared Python3.13 environment. This is focused per-ID accounting, not a full-suite/accounted-group claim.

Real worker measured() and manager sealing._staged() read/copy actual disk-backed payloads above1MiB and exactly100MiB; both refuse100MiB+1, old1MiB+1, unchanged other-output limits,101 entries and links. Manager result validation separately proves media denial and artifact overflow by exact refusal codes. Native handoff/capability regressions pass. Real bootstrap/compose-worker/create commands exercise stores, production creation/binding and readback; fixture runtime identity and repository command results are substituted as documented in test_connected_creation. No Docker/model/serving-loop or installed-image claim is made.

Earlier iterations preserved: focused-initial216 tests,3 registry-expectation failures+3 fixture helper errors,0.758s; focused-second218/218,1.102s. Initial identity check11 tests,1 failure+1 error,0.358s because a Git-less archive resolved parent metadata; corrected by initializing an independent disposable Git repository and fetching/resetting its index to pinned base, without altering candidate files/main metadata. Final identity checks pass. During self-review the new manager negative probe was strengthened to use matching output type and assert exact media/limit refusal codes; final6/6 above proves actual intended failures. All six measured runs total42.572s; preparation/tool overhead not included. No full suite/build/live test run.

## Limitations and next action

No unresolved product decision or implementation blocker. Independent exact-candidate review required, followed by owner import/checkpoint and packaging/worker qualification before native selection. New descriptor identity requires qualification for selected deployment; existing /3 admissions remain1MiB and the failed Stage1-B Job is unchanged. This resolves the selectable proposal ceiling, not missing publication-resume. No live instance, main index/history or main product path mutation. Required packet is in the canonical dossier; owner checkpoint/backup remains necessary for off-host recovery.
