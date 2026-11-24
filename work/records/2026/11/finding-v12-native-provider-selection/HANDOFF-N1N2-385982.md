# W385965 — R1–R4 correction for K delta review

Author: baton.codxpc, role impl, claim E385982. Read T385965 through M385980 and Work events through E385982; no pending directed obligation. This report supersedes the current implementation status in HANDOFF-N1N2-385975.md, not its historical evidence. Review baseline: [K review](review-2026-11-24T10-12-37Z.md), M385980. Owner ruling: FINDING section “2026-11-24 — owner confirms drafted, unqualified Claude participation list”; PLAN section “owner decision settled; R1–R4 correction milestone”. Exact context copies are in this packet.

- **Outcome:** R1–R4 corrected; exact delta ready for independent K review. No import or acceptance claimed.
- **Blocker:** none; owner decision is settled. Native use remains gated on separately selected qualification retaining actual exact-build raw output by dossier path and digest.
- **Next milestone:** K reviews the nine changed paths and focused proofs against the prior candidate. [PLAN](PLAN.md) and [updated proof table](PROOF-TABLE-N1N2-385982.md) carry current state; W385853 remains gated.

## Exact identity and recovery

Prior candidate: `sha256:2abcd54485ab85ab0deb81db2a94447c54f72a2805461cfdc9f3742576eb7887`.
Refreshed candidate: **`sha256:4980bb47c07ed40503945d2926681590f393b657d9413293079c2e6520679053`**.
Pinned upstream base: `9f9790222dfd004bc8f19d5c378c3acdb00fd4ca`. Same independent disposable copy at `work/scratch/w385965-n1n2/repo`; no linked Git metadata or protected Git mutation. All 35 prior candidate files/modes were hash-verified before edits; prior archive remains unchanged.

Evidence root: `work/records/2026/11/finding-v12-native-provider-selection/evidence/correction-385982/`.

- `candidate-manifest.json`: all **37** full candidate paths, exact hashes, byte counts and modes, plus base and context identity.
- `candidate-files.tar.gz`: full candidate files, SHA-256 `b6bb5371be3b1fa9ff1a027039a9ade989a7b63d0e4fac44e0513e3d411832ad`.
- `delta-manifest.json`: exactly **9** changed paths against prior candidate, before/after hashes, sizes and modes. Two test paths were unchanged upstream files outside the original 35-file candidate.
- `delta-files.tar.gz`: exact replacement delta, SHA-256 `8b3e0c8509b5162ef37c52bc6fd33621e2d3afd2a05fa3f30ce0b3159d3b77ed`.
- `delta.patch`: readable unified delta against the prior candidate, not against the original base. No deletions.
- Both archives were reread member-by-member and checked against manifest hashes/modes/path sets. Reconstruction is pinned base plus the full archive, or the exact prior candidate plus the delta archive. Do this only in a disposable area; import remains unselected.
- Candidate identity uses the prior documented canonical JSON algorithm over base/files/context. Added context is the immutable review and explicit owner draft/qualification ruling. DESIGN still equals the pinned approved context; no DESIGN change proposed.

## Correction response

**R1 — proven pre-start release.** `worker_manager.attempts.provider_home_cessation_of` recognizes a durable preparation ending only when both current and ending runtime identity are absent, runtime is not-started, and no start-operation journal exists. `provider_home.ceased` accepts that explicit positive evidence. It does not treat a bare not-started row, arbitrary terminal, start-requested, uncertain runtime or stale cessation as release. `request_runtime_start` refuses a preparation-ended attempt before effect preparation and rechecks inside its write transaction, preventing a delayed caller from starting after a successor acquired the home.

The connected positive refuses real launch materialization after acquiring a home, observes the manager's durable failed preparation, verifies the old start is fenced, records an explicit successor and passes it through the normal home-selection/acquisition and typed-mount boundary. The successor owns the same retained path. This proves the blocked resource operation; no automatic retry of the exceptional Job is introduced or claimed. The negative interrupts the actual adapter call after durable start intent; a successor remains pending, holder bytes remain unchanged and no provider runs.

**R2 — exact crash point under /home.** The mkdir fault now matches the final relative `home` creation AND its exact parent directory fd. Ancestor `/home` creation attempts cannot trigger it. The whole home module (21 cases) passed with both TMPDIR and BATON_V12_DISK_ROOT set to `/home/sl/src/baton/work/scratch/w385965-n1n2/test-roots`; this is retained in the log headers. The helper uses Linux `/proc/self/fd` to identify the directory fd, consistent with this host test environment. No skips or alternative storage fallback.

**R3 — honest held reason.** The manager's immutable assessment supplies a structured `model_attribution_hold` cause only for a held selected attempt. The projection carries it to the shared read model. Reason becomes `held: model-attribution-missing` (or `-conflicting`/`-invalid`) plus `owner action needed`. Status and both monitor views expose the cause/action. Lifecycle state remains unchanged; no owner record, retry or downstream opening is added. The connected proof checks repeated passes and reopened stores; the shared-view proof checks all three typed causes.

**R4 — provenance and one-worker proof.** PROVIDER-SELECTION now says **drafted and unqualified**, names the written September review and FINDING entry that actually describe `modelUsage`, and distinguishes the JSON summary's digest/checks from retained raw evidence. It explicitly states that raw-output provenance is unsatisfied and native use requires exact-build qualification with retained raw output. The owner-approved contributor list is unchanged. Proof 37 now names `tests.job_manager.test_scheduling.Capacity.test_a_second_admission_to_one_live_worker_is_refused`: one configured worker, first live allocation, second attempted allocation refused and no second row. The older two-worker/one-principal proof remains unchanged as separate coverage. Proof 22 remains retained baseline evidence, not rerun here.

## Focused verification

Affected groups: `manager-pure`, `tools-pure`, `job_manager`. Prepared interpreter `/home/sl/.local/state/baton-v12-venv/bin/python`; supported `just --justfile v12/justfile test-one` commands. Deterministic fake provider/engine seams with real local owners/stores and disposable fixture repositories. No full/group/broad inventory run, image, container, live provider, native Job, credential/registry read or mainline import.

Final run: **765 collected, 765 executed, 765 passed; 0 failed, 0 errors, 0 skipped, 0 duplicates, 0 unaccounted**, exit 0, **28.639779 seconds**. Nine modules: attempts, provider_home, provider_selection, job_observation, job_viewer, scheduling, model_attribution, provider_attribution_recovery and job-manager status. No timeout. Source before/after is stable.

Retain `focused.header.json`, `.collection.json`, `.stdout.log`, `.stderr.log`, `.summary.json`, `.source-before.json` and `.source-after.json` together. `run-focused.py` preserves actual child exit status and measured durations. A final documentation-only addition follows that run; `source-reconciliation.json` proves unchanged production/test bytes and consumed inputs. `final-source.json` identifies final bytes. `git diff --check` passed.

Development accounting remains explicit: first 26-case targeted run had 24 passes, one error and one failure (1.715439s). Both were new-test mistakes: allocation rows call the identity assignment_id, and status intentionally strips the redundant held prefix while retaining the reason. Corrected targeted run: 26/26 in 1.715506s. No existing expectation was weakened. Total measured test subprocess time this correction: **32.070724s** (includes both development runs and final focused run; not new unique coverage). Earlier 2791-pass evidence remains preserved historical evidence and is not represented as a rerun of the correction.

## Remaining qualifications

No unresolved R1–R4 implementation item or new owner decision is asserted. Independent review remains required. K's nonblocking section-5 notes are not claimed resolved: required-review supervisor argv/environment additions are outside the adapter description; retained-home session activity remains unknown; CLI build measurement is the worker's report, not an independent host probe; version format/five-second bound/64 KiB terminal bound are unqualified; zero-quantity usage semantics and later activity versus cessation timestamp need qualification. Current source/documentation discloses these bounds. Original September raw bytes remain unavailable; an attested description/digest is not raw evidence. Native use, owner import and the human checkpoint remain separate.

## Delta paths

- `v12/PROVIDER-SELECTION.md`
- `v12/python/src/baton_v12/job_manager/projection.py`
- `v12/python/src/baton_v12/worker_manager/attempts.py`
- `v12/python/src/baton_v12/worker_manager/provider_home.py`
- `v12/python/tests/job_manager/test_scheduling.py`
- `v12/python/tests/manager/test_provider_home.py`
- `v12/python/tests/tools/test_job_observation.py`
- `v12/python/tests/tools/test_provider_selection.py`
- `v12/python/tools/job_observation.py`
