# W385965 completed N1/N2 candidate — independent K review

Author: baton.codxpc, implementation claim E385975. 2026-11-24.

- **Outcome:** complete bounded N2, N1 and owner-B implementation candidate, ready for independent review; not source acceptance, import or container qualification. Reconstructed from pinned base and independently rechecked the prior E385969 archive/manifest before resuming. Temporary incomplete-runtime guard is removed only with connected enforcement in place.
- **Confirmed blocker:** none. Historical partial checkpoint CHECKPOINT-N1N2-385969.md is superseded for current implementation state; its evidence remains unchanged.
- **Required next milestone:** K reviews this exact candidate against the approved contract/addendum and owner-B decision, using [PLAN](PLAN.md) and [proof table](PROOF-TABLE-N1N2-385975.md). Any required correction returns to implementation through the configured route. No native execution selected.

## Identity and recovery

Candidate: `sha256:2abcd54485ab85ab0deb81db2a94447c54f72a2805461cfdc9f3742576eb7887`. Upstream base: `9f9790222dfd004bc8f19d5c378c3acdb00fd4ca`.

Exact full files/modes/hashes: `evidence/implementation-385975/candidate-manifest.json`.
Archive: `evidence/implementation-385975/candidate-files.tar.gz`, SHA-256 `d33f9ef228331ff276bb816ad751d26936ecf8415204aebb6e86a96045f621b0`. Every member was reread and verified against the manifest, including mode and exact path set. `tracked.patch` is supplemental and omits newly added files; the archive/manifest are authoritative.

Working copy: `work/scratch/w385965-n1n2/repo` (independent disposable Git metadata, no linked worktree). Reconstruct on any machine by exporting the pinned upstream base into a new disposable repository and applying only manifest-listed archive files. Never extract onto the protected checkout as part of review. No local commit is required for recovery. The synthetic disposable Git HEAD in test headers is not the upstream base identity.

Read-only approved task context is copied in `evidence/implementation-385975/context/`; its per-file hashes are part of the candidate identity. In particular DESIGN SHA-256 is `d2c71e534b3d3f92d7f81b445ed7ba911984e568addfb1b5c59c73e02dbbd914`. No DESIGN changes are proposed. Owner checkpoint of the approved DESIGN amendment remains pending before/with eventual source import.

## What changed

N2 introduces the standard-library shared policy/adapter contract, explicit deployment/launch selection, normal worker hooks, disconnected stdin and bounded process-group termination, manager-derived private Job/worker homes, durable holder records and positive cessation checks. Typed mounts are revalidated; unknown/stale holders defer until an ordinary manager pass can settle them. Credential delivery remains a reference; seeded mode copies once and preserves provider refresh. Managed-entry support is bounded and the production list remains empty. Legacy versions retain their prior identities, argv and mounts.

N1 selects provider/model/mapped identity/build explicitly, measures CLI build without reporting the probe as a model invocation, and records normalized contributors only from declared terminal sources. Host-owned checks bind exact retained output and immutable selection to frozen result, checkpoint and verdict. Missing/conflicting/foreign/tampered evidence holds before acceptance and opens no dependent stage. Diagnostics remain available after cleanup. Provider/model separation follows composed identities.

Owner B qualifies the ORIGINAL producer at recovery inspection/admission and revalidates it at custody/handoff. Candidate/tree/result/log bindings cannot be substituted on replay. The provider-free publisher carries a digest reference and never becomes the model producer. Legacy recovery behavior is preserved.

## Verification and accounting

Affected logical groups: `manager-pure`, `tools-pure`, `job_manager`. Supported `just --justfile v12/justfile test-one` with prepared interpreter `/home/sl/.local/state/baton-v12-venv/bin/python`; fake providers and engines, real disposable fixture Git and local product owners.

**2791 unique collected, 2791 executed, 2791 passed; 0 failed, 0 errors, 0 skips, 0 unaccounted.** The 20-module compatibility selection is 2783/2783; eight additional completion proofs bring unique coverage to 2791. There are 2828 pass events, including 37 intentional repeats of existing home/connected cases after adding proofs. `joined-accounting.json` enumerates every id and its evidence run. `proof-table.json` expands every required proof to exact test ids.

Measured sum of subprocess run durations including the interrupted run: **613.174061 seconds**. This is accumulated duration, not wall time: later independent batches ran two at once. Earlier development runs remain separately retained and are not added to that final-verification total.

The first compatibility command hit its 180-second aggregate bound, actual child exit -9, after 1028 accepted passes; the unfinished case passed alone in 3.816903 seconds. The 1754 other unfinished cases then passed in 34 finite batches. No broad rerun occurred. Original wrapper mistakenly returned shell 0 after recording -9; corrected wrappers propagate exits/timeouts, record PID/PGID and split stdout/stderr. One JSON witness interleaved with `ok`, and expected CLI refusal messages left standalone `ok` lines in two batches; corrected ledgers retain the originals and reconcile each exact id. These were accounting defects, not product test failures. See `timeout-diagnosis.json` and `*.accounting-corrected.json`.

All final production bytes are identical to the compatibility-tested production bytes. Only two test modules gained completion proofs and `v12/PROVIDER-SELECTION.md` was added between batches; their tests passed under final source headers. `verification-source-reconciliation.json` proves the finite delta and unchanged consumed inputs. `git diff --check` passed. Source before/after, logs, collection and ledger are retained together for every accounted run.

Development fixes recorded in retained logs included stage binding owner access, projection diagnostics after exchange cleanup, and nested recovery provenance exceeding the existing document depth. The final design uses a digest reference rather than weakening depth validation. Fixture setup corrections supplied required image/profile/deployment identity and exact retained entry reads. No required test expectation was removed or waived.

Existing test expectation changes: worker packaging now requires the shared standard-library policy package; unsupported next launch-version probe moves from `/6` to `/7` because `/6` is explicitly supported; added `/6` roundtrip. Existing stage/recovery fixtures gain optional provider-delivery/selection hooks while unchanged legacy cases retain their original path. Full old Claude (287), OCI (143), launch (37), stage execution (517), worker entry (66), pool (68), recovery admission/execution (274) and the remaining selected modules passed.

## Limitations and decisions

No full suite, checkpoint-profile module, actual engine module, image build/container run, live provider, registry/credential read, native launch, mainline import or protected Git mutation was performed. Tests record some existing resource warnings; they are retained, with zero test errors/skips. Exact engine/image qualification remains separately selected.

The simulated Codex row proves policy/lane behavior, not a real Codex adapter or authentication protocol. N3/N4 remain separate. Proof 17 simulates legacy output, not an old container. Home failure/new-Job proofs include the explicit runtime-owner seam, while correction/removal/restart and recovery run through connected local owners. The proof table qualifies these boundaries rather than claiming live coverage.

The Claude participation-source shape is traced to retained review `REVIEW-EVIDENCE-235117.json`, copied/hash-pinned here. Its original temporary raw file is absent on this host; no fresh raw-output or live qualification is claimed. No new owner product decision is required for review. K must independently assess the source and evidence; owner import/checkpoint and any native qualification remain separate.

## Exact changed paths (35)

- `v12/PROVIDER-SELECTION.md`
- `v12/python/src/baton_v12/job_manager/projection.py`
- `v12/python/src/baton_v12/job_manager/publication_execution.py`
- `v12/python/src/baton_v12/job_manager/publication_recovery.py`
- `v12/python/src/baton_v12/job_manager/review_driver.py`
- `v12/python/src/baton_v12/provider_policy/__init__.py`
- `v12/python/src/baton_v12/provider_policy/attribution.py`
- `v12/python/src/baton_v12/provider_policy/home.py`
- `v12/python/src/baton_v12/worker_manager/attempt_logs.py`
- `v12/python/src/baton_v12/worker_manager/attempts.py`
- `v12/python/src/baton_v12/worker_manager/launch.py`
- `v12/python/src/baton_v12/worker_manager/model_attribution.py`
- `v12/python/src/baton_v12/worker_manager/oci.py`
- `v12/python/src/baton_v12/worker_manager/provider_home.py`
- `v12/python/tests/job_manager/test_provider_attribution_recovery.py`
- `v12/python/tests/job_manager/test_publication_recovery_admission.py`
- `v12/python/tests/manager/provider_fixtures.py`
- `v12/python/tests/manager/test_claude_agent.py`
- `v12/python/tests/manager/test_model_attribution.py`
- `v12/python/tests/manager/test_provider_home.py`
- `v12/python/tests/manager/test_worker_entry.py`
- `v12/python/tests/tools/test_pool.py`
- `v12/python/tests/tools/test_provider_selection.py`
- `v12/python/tests/tools/test_stage_execution.py`
- `v12/python/tools/job_observation.py`
- `v12/python/tools/job_viewer.py`
- `v12/python/tools/next_run_bindings.py`
- `v12/python/tools/parallel_test.py`
- `v12/python/tools/pool.py`
- `v12/python/tools/single_worker.py`
- `v12/python/tools/stage_execution.py`
- `v12/worker/Dockerfile.claude`
- `v12/worker/Dockerfile.integration`
- `v12/worker/baton_worker.py`
- `v12/worker/claude_agent.py`
