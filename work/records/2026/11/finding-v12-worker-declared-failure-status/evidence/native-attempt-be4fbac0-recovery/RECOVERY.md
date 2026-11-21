# W385424 — native attempt be4fbac0 recovery and diagnosis (K, read-only)

K (`baton.prompt`, no claim) on M385448 (T321608), 2026-11-21: preserve the native Job's exact candidate, base, changed-path inventory, custody digests and ending evidence in this dossier; diagnose the two required viewer compatibility failures; distinguish them from W385427's isolated-copy failure. Supported views and retained files only; no store opened; no rerun, fresh attempt, live change, import or Git mutation. The instance `native-handoffs-2` was read, not changed (its manager and publisher are still serving; `just status`).

## Identity

| | |
|---|---|
| Job / Work | `w385424-status-cause-1` / `b5f5d37f-W1` (authority `b5f5d37f149d42e093dfbcb545605f33`), created by incarnation `slaw-create-status-cause-1` at `2026-11-21T03:43:18.946Z`; template `/3`, profile `native-handoff/1` (Job deadline 9960 s) |
| Binding | `deployment.json` / `bootstrap.json`: line base and canonical target `7ac02c7f01cc59b43ade0c98b55be59ea750af41`, source worker `impl-a` (`views/deployment-binding.json`, `views/bootstrap.json`) |
| Implementation attempt | `attempt-be4fbac026ac440c21aef3779bdbb9deee18cc204335e8700a66a36b687c5f66`, participant `baton.claude-native`, offer issued `03:44:46Z`, claimed `03:44:51Z`, runtime `d07676d4…` (destroyed, cleanup retained) |
| Review attempt | `attempt-38f044ce…`: never admitted (`retired-before-admission`); review stage `blocked` throughout |
| Ending | provider turn ended status 0 (`logs/provider.stdout.status.json`, `provider.stderr.status.json`: "finished"); mandatory verification ended 1 (`logs/verification.stderr.status.json`; 268 tests, 2 failures); worker disposition `verification-failed`; sealed `unable` at `04:24:03.415Z` (`sealed.json`, manifest `sha256:59388997…`, completion manifest `sha256:b43486bc…`); last activity `04:23:47.950Z`, 2 482 458 bytes |
| Cancellation | `job-deadline reached at 2026-11-21T06:29:18.946Z`; shutdown complete; implementation target `ended-before-request`, review `retired-before-admission` (`views/status-*.json`) |
| Operator view | `exceptional; cause unknown` on `just status` and the viewer (`views/just-status.txt`, `views/view-job.txt`): the installed bundle (`25330714…`, built from `7ac02c7f`) predates this very correction, so the retained `verification-failed` declaration is not surfaced — the defect W385424 exists to fix |
| Handoff | `handoff/handoff.json` = `{"kind": "final-submission", "schema": "baton.native-handoff/1"}` (69 bytes, `sha256:54cc11b4…`): no clarification request was made; no live handoff branch is claimed |

## Candidate (frozen bytes)

Retained proposal (`proposal/`, copied byte-for-byte from the review line's custody for this attempt; `sealed.json` content digest of the proposal directory `sha256:30509303ad49fd0ce8a91b2624b8f7be5051de0ae02bc1755b6eaebaa94d4002`, 165 593 bytes): `result.json` (sha256 `aaab90fa…`; schema `baton.dogfood-proposal/2`, base and entry head `7ac02c7f`, candidate head `4c528624da567548ec0f229b1ab8d546072ae7b9`, provider status 0, verification status 1, disposition `verification-failed`, `why: the task's own command ended 1`), `change.patch` (sha256 `efa33fd8…`, 1729 lines, 10 files), `objects.bundle` (71 168 bytes; `git bundle list-heads` → `4c528624… HEAD`), `verification.txt` (the argv and `exit: 1`; output deliberately not reproduced by the worker). The checkout copy of the review line carries identical `change.patch`/`result.json` bytes.

Changed paths (10, all modified over `7ac02c7f`; `candidate-inventory/inventory.json`, `candidate.sha256`; K applied `change.patch` with `patch -p1` to a pristine `git archive 7ac02c7f` tree under `/var/tmp` — dry run and apply clean, no fuzz/offset/rejects, `patch-apply.log`; the listing's SHA-256 is **`e686d8c271b97dc65af65f3266c75a9c374df000dd08db22a099bb014a452e12`**):

| path | candidate | base `7ac02c7f` |
|---|---|---|
| `v12/python/JOB-VIEWER.md` | `7b0ac7c8…` | `b4704b93…` |
| `v12/python/src/baton_v12/job_manager/projection.py` | `432e4b8f…` | `211eb4cf…` |
| `v12/python/src/baton_v12/worker_manager/failure_cause.py` | `05f49b4a…` | `776f5932…` |
| `v12/python/tests/manager/test_attempt_failure_cause.py` | `62b690e9…` | `8371cbb8…` |
| `v12/python/tests/manager/test_boundary_inventory.py` | `24c12076…` | `7da1a601…` |
| `v12/python/tests/tools/test_attempt_diagnostics.py` | `714c8524…` | `212b946c…` |
| `v12/python/tests/tools/test_job_observation.py` | `813d9a37…` | `1c8c635b…` |
| `v12/python/tests/tools/test_job_viewer.py` | `fa940bbc…` | `1e83ed50…` |
| `v12/python/tools/attempt_diagnostics.py` | `a89ee121…` | `6e02e22e…` |
| `v12/python/tools/job_observation.py` | `7631c749…` | `2fa916f2…` |

Full digests in `candidate-inventory/`. These bytes are the native candidate; nothing here accepts them.

## The two verification failures — diagnosis

**Confirmed (retained log `logs/verification.stderr.log`, 63 325 bytes; `verification.stdout.log` empty).** The mandatory argv (`tests.manager.test_attempt_failure_cause`, `tests.tools.test_attempt_diagnostics`, `tests.tools.test_job_observation`, `tests.tools.test_job_viewer`; `PYTHONPATH=v12/python/src:v12/python`, both roots and `TMPDIR=/scratch`) ran 268 tests in 14.9 s: 266 ok, 2 FAIL — `tests.tools.test_job_viewer.TheRealObservationReaderReachesTheView.test_a_foreign_job_still_refuses_against_the_real_reader` and `.test_the_view_renders_the_real_model_free_completion`. Both fail identically in `pending_judgments → integrating → drive_job`: `job-a's integration stage never reached 'integrating': {'implementation': 'completed', 'review': 'completed', 'integration': 'claimed'}` (14 sweep ticks). No worker fault, no Git error, no refusal text in the retained stderr; the stage simply never left `claimed`.

**Inferred (strong; from the provider's own report plus source, not reproduced by K — no rerun was authorized).** The provider's final recap (`logs/provider.stdout.log`, `result` member) states: "Under the sandbox's `umask 0077`, `tests.tools.test_job_viewer` fails two tests (`TheRealObservationReaderReachesTheView`): the integration target is created `0o700`, the deployment denies it ('an integration runtime holds that group as its only share in the target'), the attempt's launch root is left behind, and the stage never leaves `claimed`. Both fail identically on the unmodified tree at `HEAD` and at `3d05430f`, and both pass with my changes under `umask 002`." Source agrees: `baton_v12/integration/oci_delivery.prove_target_posture` refuses the canonical target unless its directory is the configured workspace group AND carries group write and group traversal (`S_IWGRP|S_IXGRP`); the fixtures under `tests/tools/test_stage_execution.py` create their directories with default modes (`os.makedirs` without mode; no `chmod` to a group-writable mode anywhere in that module), so the target's mode is `mode & ~umask`. The provider child is spawned with `PROVIDER_UMASK = 0o077` (`claude_agent.py`) → `0o700`; the worker's `_verify` spawns the mandatory command WITHOUT a umask operand, so it inherits the container process default (Docker's `022`, user `65532`) → `0o755` — group write absent either way, so the posture check denies the integration runtime and the fixture's sweep leaves `integration` at `claimed`. On a developer host with `umask 002` the same directory is `0o775` and the check passes — which is why W385427's confined host run of exactly these two cases passed. The denial text itself is written to the fixture's disposable launch root, which the test harness removed, so it is not in the retained stderr; that is why this remains inferred rather than confirmed.

**Distinct from W385427's failures of the same two tests.** W385427's first isolated-copy failure was a `WorkerFault` input error — the isolated copy lacked the unchanged `v12/worker/worker-control-1.0.schema.json` — before any viewer assertion; its later stops were omissions of its own Git guard (`check-attr`, `--no-optional-locks`, local `archive`). Same test names, different causes; W385427's packet says so and this recovery confirms it.

## What this means

- The native candidate's mandatory verification is **not passed** (exit 1), and the failing cases are the environment's, not the candidate's: the same cases fail on the unmodified tree inside the worker (provider's reproduction) and need `umask 002` to pass. The candidate's own additions (test_attempt_failure_cause 93→113, test_attempt_diagnostics 42→51, test_job_observation 7→18, test_job_viewer 81→86 per the provider's recap) all passed inside the worker (266 ok).
- The installed bundle shows `cause unknown` for an attempt whose retained `result.json` says `verification-failed` with provider status 0 — the W385424 defect, observed live, exactly as the FINDING describes.

## Overlap with W385427 (composition, not assessed here)

W385427's accepted isolated candidate (tree `5348d4b3…`, 13 paths) and this candidate share FOUR paths: `job_manager/projection.py`, `tools/job_observation.py`, `tests/tools/test_job_observation.py`, `tests/tools/test_job_viewer.py`. The other six W385424 paths (`JOB-VIEWER.md`, `failure_cause.py`, `attempt_diagnostics.py`, `test_attempt_failure_cause.py`, `test_boundary_inventory.py`, `test_attempt_diagnostics.py`) and the other nine W385427 paths are disjoint. Both candidates are frozen; composition is serial and needs its own joined review.

## Bounded recommendation

1. **Finding to file before any workaround (AGENTS rule):** the deep real-reader fixture's integration target mode depends on the ambient umask; inside the worker image (umask 022/077) `prove_target_posture` denies it and the two cases cannot pass, so any native Job whose mandatory verification includes `tests.tools.test_job_viewer` will record `verification-failed` regardless of its change. Bounded correction options, for the owner to select: (a) the fixture establishes the target's mode explicitly (group write + traversal under the configured group) instead of inheriting it; or (b) the worker's `_verify` spawns the verification with an explicit umask of `002`. (a) is the narrower, test-only correction; (b) changes the worker image. Either is a separate Work, not folded into W385424's or W385427's candidates.
2. **W385424 candidate review:** independently review the frozen bytes (`e686d8c2…`) from this dossier — never from the live instance — and verify the mandatory argv on an isolated copy outside the worker; the two deep cases need either a confined fixture-Git exception like W385427's (owner's call) or the fixture correction above. Until then the candidate's verification evidence is the retained 266/268 plus the environment diagnosis, not a pass.
3. **Composition:** after that review, compose W385424's four shared paths serially with W385427's accepted bytes and obtain an independent joined review before any host import. W385427's non-blocking observations stay recorded separately.
4. **Instance:** nothing to do; the Job is cancelled by deadline and its attempt retained. No fresh attempt was selected.

## Retained files

`proposal/` (result.json, change.patch, objects.bundle, verification.txt), `sealed.json`, `handoff/handoff.json`, `logs/` (provider stdout/stderr and status, verification stderr/stdout and status; scanned for credential-like strings — none), `views/` (status snapshot, `just status`, viewer detail, log locators, bootstrap and deployment binding), `candidate-inventory/`. Digests in `evidence.sha256`.

## Clarification — 2026-11-21, append-only (K, M385451)

**Correction of the account above.** The section "What this means" says the two failures "are the environment's, not the candidate's" as though settled, while the diagnosis section labels the umask explanation *inferred*. At the time of writing it WAS only inferred (the provider's own report plus source reading; nothing reproduced by K). That sentence overstated the evidence. The attribution is now CONFIRMED by the probe below; the earlier text is left as written and superseded here.

**Independent probe (`umask-probe/`).** Exactly the two owner-approved compatibility cases (`TheRealObservationReaderReachesTheView.test_a_foreign_job_still_refuses_against_the_real_reader`, `.test_the_view_renders_the_real_model_free_completion`), run six times under the established confinement — bubblewrap with the whole host read-only except one fresh run directory, no network, PID namespace, all capabilities dropped; W385427's fixture Git guard (`guard/git`, sha256 in each `run.json`) first on `PATH`, logging every Git invocation and target; `TMPDIR` and both disk roots inside the run's fresh `fixtures/` directory; the prepared interpreter; bytecode off. The harness (`umask_fixture_runner.py`) is W385427's `fixture_runner.py` plus two things: it sets the process umask from `PROBE_UMASK` before anything is created, and it wraps `baton_v12.integration.oci_delivery.prove_target_posture` to RECORD what the product observed (`compatible_target`: place, gid, mode) and what it answered (accepted / the exact `ContractRefusal` text) before re-raising — a retention seam in the harness, no product byte changed. Trees held constant: `base-tree` = pristine `git archive 7ac02c7f`; `tree` = the frozen W385424 candidate (listing `e686d8c2…`, applied from the retained `change.patch`).

| run | tree | umask | tests | posture observed → answered | result |
|---|---|---|---|---|---|
| base-002 | 7ac02c7f | 002 | 2 | target `0o775`, gid 1000 → accepted (×4) | **OK**, 11.6 s; 442 Git invocations, 0 refused |
| base-022 | 7ac02c7f | 022 | 2 | target `0o755`, gid 1000 → **refused** (×2) | 2 FAIL (`integration` stays `claimed`), 14.0 s; 278 invocations, 0 refused |
| base-077 | 7ac02c7f | 077 | 2 | target `0o700`, gid 1000 → **refused** (×2) | 2 FAIL, 14.1 s; 278, 0 |
| cand-002 | candidate | 002 | 2 | `0o775` → accepted (×4) | **OK**, 12.5 s; 442, 0 |
| cand-022 | candidate | 022 | 2 | `0o755` → refused (×2) | 2 FAIL, 15.9 s; 278, 0 |
| cand-077 | candidate | 077 | 2 | `0o700` → refused (×2) | 2 FAIL, 16.1 s; 278, 0 |

The retained refusal (`posture.jsonl`, verbatim but for the fixture path): *"the canonical target at '…/fixtures/v12-w71917-…/…' is group 1000 mode 0o755 and this deployment configured group 1000; an integration runtime holds that group as its only share in the target, and a target it cannot work in is refused for operator provisioning rather than repaired here"*. Under umask 077 the same with `mode 0o700`. The failing assertion is byte-identical to the native attempt's: `job-a's integration stage never reached 'integrating': {'implementation': 'completed', 'review': 'completed', 'integration': 'claimed'}`. Every Git target of all six runs is under its own run's `fixtures/` (`SUMMARY.json`, `outside_fixture_roots: []`); no host, native or retained repository was touched. Per-run logs, Git logs, Trace2, diagnostics and posture records are under `umask-probe/<run>/`.

**Confirmed.** With candidate and base held constant, the only variable that flips the two cases between pass and fail is the ambient umask, through the mode of the fixture-created canonical target and the product's `prove_target_posture` (group write + traversal required). The W385424 candidate behaves exactly as the unmodified base under every umask. The native worker's verification (`_verify` without a umask operand → container default `022`) and the provider's own runs (`PROVIDER_UMASK 0o077`) therefore could not pass these two cases on any tree; the native `verification-failed` is attributable to the verification environment, not to the candidate's change. This supersedes the "inferred" qualification above; it does not accept the candidate (the mandatory argv still has not passed in the worker, and the candidate's other 266 cases are the worker's retained evidence plus the provider's recap, not an independent run).

**Recommendation, now on confirmed evidence.** Track separately a FIXTURE-ONLY correction: the deep real-reader fixture (and any fixture that creates the canonical target the integration runtime must work in) establishes the target's posture explicitly — configured group, group write and traversal — instead of inheriting it from the ambient umask, so the product's posture check is exercised as written and passes wherever the group is right. Preserve `prove_target_posture` and the integration runtime's refusal unchanged; do not set a worker-wide umask (a global policy change with effects far beyond these two tests). Until that correction lands, any native Job whose mandatory verification includes `tests.tools.test_job_viewer` will record `verification-failed` inside the worker regardless of its change — a fact for the operator's choice of mandatory modules, not for the candidate.
