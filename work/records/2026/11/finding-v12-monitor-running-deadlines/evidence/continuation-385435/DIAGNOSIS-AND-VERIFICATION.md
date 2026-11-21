# Retained diagnosis and proposed verification — E385435

Confirmed: focused-4.log shows both failures at test_stage_execution.py:9701: first implementation serve_exchange returned1, before viewer assertions. focused-3 had missing baton_worker imports and focused-2 missing vectors.json; these are earlier, distinct failures. serve_exchange catches WorkerFault, AdapterFailure and arbitrary Exception, returning a faulted exchange. The retained log contains neither fault code nor underlying exception. tests.manager.disk_roots.disk_backed_under registers forced root removal. Actual exception and exact past Git trace are UNKNOWN; no evidence attributes the failures to Git. No rerun during this continuation.

## Static Git inventory — not a fabricated execution trace

T is per-case /home/sl/src/baton/work/scratch/v12-w71917-<random> (prior TMPDIR); suffix was not logged and root is cleaned. Proposed new roots explicitly live under /home/sl/src/baton/work/scratch/w385427/verification-git.

- test_stage_execution.py:4304–4308,4381: git -C T/source init -q -b main; add --all; commit -q --message base; rev-parse HEAD. Setup passed these assertions before the retained failure.
- test_stage_execution.py:9504: git -C T/integration-workspace init -q --bare.
- source_profiles/checkout.py:156,180,202: clone --no-hardlinks --no-local SOURCE DEST; -C DEST checkout --detach BASE^{commit}; rev-parse --verify HEAD^{commit}. Review-line target is T/storage/<LINE_HOME>/<line id>/checkout (review_cycles._line_place); source T/source. Worker git-line consumes this delivered line; git profile clones into its workspace/checkout.
- claude_agent.py:2781 onward: git -c safe.directory=REPOSITORY -C REPOSITORY at delivered fixture line. Reads include rev-parse, status, ls-files, diff, merge-base, ls-tree, cat-file, policy config reads. Candidate mutations: add --all -- .; commit --no-gpg-sign --allow-empty-message --message; bundle create into fixture candidate output. Fixture provider passes Git through to real subprocess.run. Reachability before return1 is unknown.
- checkpoint_profiles.py:82,364,386: update-ref and fetch in fixture checkpoint/review repositories.
- integration/git_profile.py:135,185,192,212,570,578: fetch, merge-tree, commit-tree, update-ref, hash-object -w and update-ref --stdin in T/integration-workspace or target T/source. These are later successful-pipeline operations, not claims the failed first implementation reached integration.
- Inherited fixture source also contains clone/fetch at test_stage_execution.py:11928/12301; presence is not proof these two cases execute them. Actual exhaustive operations and randomized targets require a guarded trace.

No known target is the owner checkout. Historical exact target suffixes cannot be recovered from the retained assertion-only log. This inventory distinguishes confirmed setup operations from possible later operations.

## Proposed owner exception — NOT yet authorized

Only the two TheRealObservationReaderReachesTheView tests: test_a_foreign_job_still_refuses_against_the_real_reader and test_the_view_renders_the_real_model_free_completion. Preserve real pipeline/viewer assertions; existing fake provider and fake engine, no live calls. New disk roots beneath work/scratch/w385427/verification-git; finite timeout. Before cleanup retain actual Git argv/cwd/real targets, per-case roots, worker fault code and test-only exception capture around agent.work/consider. No interpretation of a suppressed exception as a Git fault.

Required Git exception: init/clone/checkout/add/commit/fetch/update-ref/hash-object/commit-tree/bundle and read-only operations, only in NEW disposable fixture repositories. Guard every Git process before execution: cwd/-C/gitdir/worktree, local clone/fetch inputs and output endpoints must resolve within one declared fixture root; no external symlinks, linked gitdir or alternates; no ambient GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR escapes; no remote/network/push, global/system config, credential, hook or signing effects. Guard children too. A rejected verb/target stops the run, never widens authority. Reading isolated candidate Python source is allowed; its repository is not a Git mutation target. Prepare guard and review exact plan before execution; owner ruling still required under AGENTS strict Git policy.

If no exception is granted, retain both cases unresolved and use permitted focused tests for new timing behavior; do not weaken or replace genuine pipeline assertions to claim compatibility. Shared Python edits await M385436 overlap coordination. Nonoverlapping worker producer work and no-Git tests may proceed.
