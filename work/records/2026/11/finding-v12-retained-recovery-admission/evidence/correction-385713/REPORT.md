# W385624 F1/F2/F3 correction — baton.codxpc E385713

Ready for independent **source delta review**, under M385710. No native custody, native Job success, output-limit recovery or independent acceptance is claimed.

## Exact candidate

Cumulative candidate identity `sha256:82e1cd871d73b0ee3724105516231a4d08b39903a06b74779bb4e5bdacf18cfc` is the SHA256 of `cumulative-manifest.json`. Pinned base `ce6e1b2bf12519a84a3792f06562b7727dfe3021`; preserved reviewed candidate `5bc260b6dcbe970c8729424fa826b88dbc1a9d0f`. This correction is filesystem bytes on that candidate, not a new commit. Delta manifest SHA256 `b19a51139c20fab3060ceead48bd8c5ba7ac8b48cdbc9a98b8d84cc59d36b21a`.

`delta.patch`/`delta-manifest.json` describe only this correction over5bc260b6; `cumulative.patch`/`cumulative-manifest.json` describe the full candidate overce6e1b2b. Each manifest lists all paths and before/after hashes, with exact files in its sibling before/after directory. `IDENTITY.json` fixes interpretation. Original bundle/archive/native logs remain unchanged in ../output-limit-recovery-20261122/. Reconstruct without Git from that full candidate.tar plus delta/after overlay; verify all delta before hashes first. For repository comparison use independent scratch `work/scratch/w385624-correction-385713`, real detached HEAD5bc260b6, no shared Git metadata or linked worktree. Main checkout product paths and Git state untouched. No Git commit, mainline import, live instance/store edit, provider execution or cleanup.

Delta:9 v12 paths plus3 owning records. Cumulative:16 v12 paths plus18 original/updated record paths. The cumulative dossier files carry original native history plus this author's append-only correction entry. They are review evidence, **not instructions to overwrite the main dossier**, which has additional coordinator/reviewer history. Import only independently approved product bytes; preserve/append dossier history separately.

## Corrections

- **F1:** `retained_recovery.execution_gate` derives a closed `stage.recovery-gate` from the admitted recovery-only profile and durable reservation. It exposes exact decision/candidate/lineage. `projection` includes that gate in its same-store snapshot, so real `sweep` never owes an offer. Pooled scheduler admission also refuses before allocating a worker. This Stage1-B build has no supported candidate execution handoff, so even passed accounts and valid review-only lineage remain blocked; no switch or fabricated positive handoff was added. Readiness says blocked. W385625 must supply supported custody/execution binding and release conditions. Original normal dependency semantics remain unchanged.
- **F2:** public `submission.submit` refuses the recovery-only profile before writing; ordinary template resolution refuses before Work/binding effects; fresh-attempt refuses the inherited profile before reservation/external effects. The intended recovery path validates its exact decision/reservation/candidate/composed document and calls the shared internal atomic submission writer. Existing approved bounds and profile bytes unchanged; there is no CLI bypass flag.
- **F3:** new fixture uses actual bootstrap configuration, real disposable stores, the shipped default owners factory and real manager recovery-item dispatch with participant, without `--owners` replacement. It reaches the real owner-item reader (explicit unknown-failure response for the fresh instance), and rejects each mismatched Job/control/Authority store. This proves composition, not a successful recovery approval against a real failed live instance. Existing CLI acceptance cases exercise valid item/approval with production Authority and explicit normal-boundary stand-ins.
- **N1:** T385625 M385714 records that Stage1-C owns candidate handoff/review release and the post-verification-expiry held owner item. No Stage1-C implementation or graph change here.

Product delta paths: job_manager/documents.py, fresh_attempt.py, job_control.py, projection.py, retained_recovery.py, scheduler.py, submission.py, templates.py; tests/job_manager/test_retained_recovery_admission.py. Full paths are in the manifest. Test changes:11 additive cases plus two prior readiness expectations changed from owed to blocked to match the scheduler-enforced boundary. No identity, authorization, replay, cancellation, candidate or lineage assertion removed.

## Focused evidence and accounting

Prepared interpreter `/home/sl/.local/state/baton-v12-venv/bin/python`; PYTHONPATH=src, disk-backed scratch for TMPDIR/BATON_V12_DISK_ROOT, disposable installed fixture outside checkout through existing fixture selection. No full group/suite repetition or live model/engine run.

| Retained log | Tests | Passed | Failures | Errors | Skips | unittest elapsed |
|---|---:|---:|---:|---:|---:|---:|
| final-focused.log |149|149|0|0|0|7.468s|
| compatibility.log |615|615|0|0|0|21.430s|

Final distinct selected tests **764/764**, zero failures/errors/skips, summed unittest elapsed **28.898s**. Separate external wall timing was not recorded. Final-focused covers recovery admission74 cases, status and public job-control command. Compatibility covers documents, submission, templates, creation, fresh-attempt, sweep, scheduling, job-control and real-tree source identity. All5 source-identity checks pass with actual isolated Git metadata, resolving K's two archive-only unproved checks. Earlier broad group counts remain inherited review evidence; they were not rerun or reclassified here.

Real tick cases: unknown verification; restart with a fresh JobStore connection; failed verification; passed account without handoff; valid review-only lineage after predecessor expiry; cancelled and expired successor. All record zero successor offers/effects and expose exact closed gate. Profile probes cover ordinary create, direct submit including exact recovery-document replay, public submit CLI, and generic fresh-attempt; valid successor admission still passes existing tests.615 compatibility cases include normal scheduling/gating and ordinary admission behavior.

Intermediate logs retained honestly: initial.log63 tests/2 old readiness-expectation failures in4.990s; new-tests.log10 tests/2 fixture coding errors in0.784s (wrong cancellation method and absent test-port dictionary key); focused.log73/73 in5.329s. Those four intermediate failures/errors were corrected; no product defect was hidden. Total recorded test invocations910, summed unittest elapsed40.001s; final evidence above supersedes intermediate results. Post-run edits were comments/readiness explanation/formatting and dossier entries; all changed Python parsed successfully and `git diff --check` passed.

Reproduction from isolated candidate `v12/python`:

```bash
PYTHONPATH=src BATON_V12_DISK_ROOT=/home/sl/src/baton/work/scratch/w385624-test-385713 TMPDIR=/home/sl/src/baton/work/scratch/w385624-test-385713 /home/sl/.local/state/baton-v12-venv/bin/python -m unittest -v tests.job_manager.test_retained_recovery_admission tests.job_manager.test_status tests.tools.test_job_control_command
```

Compatibility used the same environment/interpreter with tests.job_manager.test_documents, test_submission, test_templates, test_creation, test_fresh_attempt, test_sweep, test_scheduling, test_job_control, and tests.tools.test_source_identity.TheRealTreesDeclaredInputsExist.

## Remaining boundary

Stage1-C execution and positive review dispatch are intentionally unavailable. This correction establishes **no premature dispatch**, not successful verifier/candidate delivery. No migration/repair of any previously offered live recovery stage was attempted. Real output-publication recovery remains separate W385695 and cap revision W385694. No unresolved product choice is required for this correction; independent delta review is next. Preserve all native bytes and logs and keep the original failed Job unchanged.
