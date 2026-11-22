# W385649 implementation handoff — E385652 / M385650

Ready for independent source review, not integration or launch.

Candidate `sha256:5771ed8d538c7782ddb72902bc14835e618669475c59e6ff27524ece32e555d5` on base `72e1093dccb3ded9763fd2c42f0f713a7ff2c88f`. Exact three-path identity and before/after hashes in candidate-manifest.json; full before/after files retained under base/ and candidate/, plus candidate.patch. Scratch worktree is disposable and is not the only copy. No candidate commit was created and no main Git mutation/import occurred.

## Outcome

Adds native-handoff-heavy/1 through job_control.PROFILES and CONTINUATIONS, with exported HEAVY_NATIVE_HANDOFF_PROFILE constant: provider7200, stage9000, overall21600 including queue, ordinary verification900; zero correction rounds and one resolved clarification continuation. Existing profile definitions, execution-limit generations, admitted-clock/retry/shutdown owners are unchanged. DESIGN LIM-5 records the already approved M385638 policy and its owning finding.

Existing CLI usage after accepted integration/rebuild is `--control-profile native-handoff-heavy/1 --provider-turn-seconds 7200`. No verification override; other verification boundaries stay unchanged. No general editor/launcher, Stage1-A source import or live deployment.

## Focused evidence

85/85 passed,0 failures/errors/skips; unittest measured3.235s, subprocess wall3.448s. Exact argv/environment and exit in run.json, verbose per-test identities in focused.log. Seven additive cases in existing test_job_control.py; no registry/new module needed. Earlier test-authoring failure and loader misfire are recorded in ITERATIONS.md.

New tests establish exact old/new profile definitions and continuation policy; missing/mismatched overrides refuse before control write; real creation and exact replay; old and new admissions survive reopen with distinct clocks; queued21600 expiry and owner-origin9000 stage expiry with unchanged120s shutdown semantics; one real native clarification continuation and refusal of a second/zero corrections; preserved continuation deadlines. Connected limit proof uses actual create/JobStore -> SingleWorker job_execution_reader -> launch_document -> worker launched -> real ClaudeAgent provider and verifier methods, with an injected runner, for implementation and review. It observes7200/900 at the runner and preserves integration1800/host300. Authorization/binding in the creation fixture are fakes; this is connected owner/worker-boundary evidence, not a full installed deployment, real provider or physical deadline measurement.

Groups affected: job_manager (added cases); existing tools-pure command and adapter cases selected as focused regression. Existing assertions were not weakened or replaced. No full group or full suite claimed.

## Remaining qualification

Independent source review is next. Per PLAN step5, owner integration/checkpoint and one qualified rebuilt runtime/package gate follow acceptance; no bundle was built from this unreviewed candidate. The existing deployed runtime still lacks this profile. Heavy runtime/source compatibility for retained W385623 source and a separately selected correction Job remain later gates; this Work does not grant same-Job correction, reset old deadlines or launch it. No unresolved product choice found within the approved profile scope.
