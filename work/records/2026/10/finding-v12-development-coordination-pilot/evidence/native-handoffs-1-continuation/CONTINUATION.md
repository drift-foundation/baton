# W385331 slice 1 — digest-bound continuation proposal from the retained `w385331-handoffs-1` candidate

K (`baton.prompt`), 2026-11-20, under the owner-held W321608 arrangement (no claim held), on the owner's instruction: "finish the candidate in isolation, verify the required behavior, and return a digest-bound proposal". This is an ordinary current-runtime source candidate for independent review (`baton.rvpc`) and human integration. It is not acceptance, not an integration, and nothing live was run.

## Identities

| | |
|---|---|
| Base | `3d05430f97ca9d4a516b51d15eb940840a6f0eff` (the Job's declared base, the installed instance's stamp commit) |
| Retained parent | `a743edebacf5c744020083ee68549f2bd1fa91f7` — the native Job's own frozen candidate (24 paths), custody-verified in `evidence/native-handoffs-1-recovery/` |
| This candidate | 33 paths (27 modified, 6 added); tree digest **`sha256:ce757322b59fbd5ca14f6ec1cd1ecec14c2781fc10c1d53c235392aeb674b866`** over `candidate.sha256` |
| `manifest.json` | sha256 `1286fbc7b9295c453ae4353fb70d4ff937d8affd4d37d7d6a40821474cf55210` |
| `candidate-from-3d05430f.patch` | sha256 `f65372fda33ae1336e1f52624a32b523d481690ba8757ef543d08581d15f4b51`; `patch -p1` onto an archive of `3d05430f` reproduces all 33 paths byte for byte (`provenance.json`) |
| `delta-from-a743edeb.patch` | sha256 `da6ee98025adf877910c0b7082cb0445b32311c6de6a959c9ab19ce2d00ba9d8`; `patch -p1` onto `3d05430f` + the frozen `change.patch` reproduces the same |

`candidate/` holds the 33 files at their repository paths. Host Git was used read-only (`archive`, `hash-object`); the host working tree stayed at `3d05430f` with `v12/` clean before, during and after.

## Path inventory (33 paths; exact base/retained/candidate digests in `manifest.json`)

- **Retained from `a743edeb` unchanged (18):** `src/baton_v12/authority/{api,core,schema,session,messages}.py`, `src/baton_v12/job_manager/{documents,job_control,role_capability,role_contract,templates}.py`, `src/baton_v12/native_handoff.py`, `tests/authority/{test_boundary,test_dossier,test_session,test_work_messages}.py`, `tests/job_manager/{test_review_driver,test_role_contract,test_templates}.py`.
- **Retained from `a743edeb` and modified by K (6):** `src/baton_v12/job_manager/{native_handoffs,review_driver,projection}.py`, `src/baton_v12/worker_manager/review_cycles.py`, `tools/stage_execution.py`, `tests/job_manager/test_native_handoffs.py`.
- **Not in `a743edeb` (9):** added `tests/tools/test_native_handoffs.py`; changed against the base `v12/worker/claude_agent.py`, `tools/single_worker.py`, `tools/parallel_test.py`, `v12/STACK.md`, `tests/authority/test_catalog.py`, `tests/manager/{test_boundary_inventory,test_dependencies,test_secrets}.py` (inventory declarations for the new public entries).

Against the base: 6 added, 27 modified. All 33 paths are under the Job's work scope (`v12/python`, `v12/worker`, `v12/STACK.md`) and test scope.

## What was finished

1. `tests/job_manager/test_native_handoffs.py`: repaired the rewrite the 3600 s bound cut off (quadruple-quoted docstrings, a missing fake-profile head helper, a wrong cancellation operand) and extended with the review-side answer record, historical re-entry and delivered-context cases. **60 OK**.
2. `tests/tools/test_native_handoffs.py` (new): one native handoff end to end over the composed stage deployment, the real worker adapter through `baton_worker.serve_exchange` with a scripted provider, real stores and a real git line. Cases: yield retained and nothing published; reviewer answers and the same task resumes on the retained checkpoint with the reply delivered; zero human acts through the ordinary final review to an integration claim; finding variant; one owner escalation held and reread, nothing scheduled; malformed request refused, not published; restart between the cuts duplicates no message, attempt or continuation. **7 OK**.
3. Registration (`tools/parallel_test.py`, one registry each) and `v12/STACK.md` section "Native handoffs — a question is not a candidate".

## Defects in the retained candidate, found by the end-to-end run and fixed

1. **Request committed after the checkpoint freeze** (`review_driver.end_implementation` and both resumes): the freeze fences and ends the producer assignment, so the Authority refused the request (`assignment generation was fenced and ended`). Now committed under the live assignment before the freeze, naming the retained head object; the claimed head is cross-bound against the frozen checkpoint right after (`native_handoffs.cross_bound`); the continuation proves the reply's head against the frozen checkpoint.
2. **Response dispatch read the frozen result the ending itself creates** (`stage_execution`): the verdict branch ran first and held. Dispatch is now the fact the deployment holds — this review attempt was delivered a pending request — with the worker's completion envelope as the fallback (`declares_response(control, attempt_id, terminal)`).
3. **A replied review projected `completed`** and opened the integration gate on a question. Added the Job-store record `native.answer` (`record_answer`/`answer_of`) and the review state `answered`; `gates_of` opens only on `completed`.
4. **The response ending was not re-enterable behind a destroyed runtime** (the continuation is asked while the reviewer's allocation is still reserved, so the conclude defers once by design and re-enters historically): `record_response` now replays its committed response exactly as `record_verdict` does.
5. `response_satisfies_dependency` indexed `stage["kind"]` on partial stage documents (`KeyError` in managed-integration cases) — now `.get`.

## What the retained candidate lacked entirely, now added

- **Worker adapter** (`v12/worker/claude_agent.py`): `handoff` and `response` declared outputs; the provider writes `handoff/request.json` (kind, body, evidence, continuation) or `response.json` (disposition, body, rationale, escalation) and the adapter binds the retained head, cited evidence digests and the delivered request/checkpoint into `baton.native-handoff/1`; a yield skips verification; a final submission declares itself; malformed requests refuse; context serving and handoffs are not combined.
- **Delivery** (`tools/single_worker.py`, `tools/stage_execution.py`, `native_handoffs.delivered_context`): one read-only `handoff.json` (`baton.native-handoff-context/1`) beside `task.json`, composed from committed records: the configured recipient for an implementer, the pending request and checkpoint for a reviewer, the exact question and reply for a continuation. Refused at preparation when a handoff-capable Job has no configured routing.

## Verification (prepared interpreter 3.13.7; roots `/var/tmp/baton-v12-handoffs-1/recovery`; logs in `logs/`)

| Run | Result |
|---|---|
| The Job's exact six-module argv (`final-six-module.log`) | **Ran 310, OK**, 10.6 s |
| `just test-group authority` (`final-group-authority.log`) | 506/506 OK |
| `just test-group scans` | 494/494 OK (2 owner-registered optional skips) |
| `just test-group job_manager` | 1693/1696; the 3 failures (`test_store_readonly`, `test_tool`) fail identically on the untouched host tree under these roots (`modules-store-readonly-tool-HOST-BASE.log`: a store-path refusal text truncated with `…`) |
| `just test-group tools-pure` | 3492/3495; `test_live_ab` fails on the untouched host tree too (`host-baseline-suspects.log`); `test_source_identity` (2) needs the real checkout's declared inputs, which a copy lacks (passes on host) |
| `just test-group manager-pure` | 4424/4433; `test_custody.TheHelperIsShortLivedAndRestricted`, `test_integration_worker` (2 classes) and `test_store.ReadonlyAcquisition` fail on the untouched host tree too; `test_frozen` and `test_w197661_verifier` need `build/` outputs a copy lacks (pass on host); `test_checkpoint_profiles` (3 classes) — see the hazard note |
| `tests.manager.test_secrets`, `test_boundary_inventory`, `test_dependencies`, `test_catalog` | pass with the added declarations |
| Managed integration (`test_managed_apply`, `test_managed_preparation`, `test_job_task_delivery`) | pass after fix 5 and the delivery guard (`fixes-after-groups.log`, 482 OK) |

Every remaining failure is either reproduced on the untouched host tree under the same roots or is an artifact of running from a copy; none is a candidate regression. `tests.job_manager.test_review_driver` (163) and `tests.tools.test_stage_execution` (477) pass. Measured: group runs 18:24–18:31Z on the outside copy; earlier nested-copy runs 18:08–18:17Z.

**Hazard note for the reviewer and owner.** `tests.manager.test_checkpoint_profiles` (three classes, `test_a_fatal_presence_query_is_not_absence`) attempted a `git checkout` of a declared base against the owner's live checkout `/home/sl/src/baton` during these runs — from the nested copy and from the copy outside any checkout alike — and was refused only because the pilot dossier files are modified ("Your local changes … would be overwritten by checkout"). The host tree was verified unchanged after every run (`v12/` clean, HEAD `3d05430f`). This is not caused by the candidate; it is a property of those tests' source nomination that the reviewer should run only from the real checkout they intend to touch, and that the owner may want recorded separately.

## Schema, image and compatibility notes

- Authority `SCHEMA_VERSION` 6 → 7 (`work_message`, `work_message_transition`); a retained store at 6 is refused, not migrated. The number's owner ruling is still owed (the retained candidate's own note).
- Template `baton.v12.job-template.implementation-review/3` bound to `baton.v12.development-role-contract.native-handoff/1`; `/1` and `/2` byte-identical; `DEFAULT_TEMPLATE` unchanged; a capability qualified against one descriptor refuses the other (asserted at import).
- Control profile `native-handoff/1`: `documentation/1`'s ceilings, zero correction rounds, one resolved continuation; `documentation/1` bytes unchanged.
- **Worker image**: `v12/worker/claude_agent.py` is a Dockerfile input, so the current image (`baton-v12-worker:e670e624`) does not carry this adapter; a rebuild and qualification follow source acceptance. The job-status document gains the review state `answered` and the implementation state `awaiting-answer`; `job.control-report` gains the additive `continuations` member.

## Limitations and what is not claimed

- No live provider, engine, container or instance was used; the end-to-end proof is a scripted provider through the real adapter and real stores.
- A yield with zero edits is permitted by the adapter but not exercised end to end.
- The next slice (nonblocking Work filing, atomic blocking prerequisite, accepted-base-gated resume) is untouched, per FIRST-NATIVE-SLICE.md.
- The instance `native-handoffs-1` and its failed Job are unchanged; the separate "cause unknown" status finding stands (`evidence/native-handoffs-1-recovery/FINDING-status-cause-unknown.md`).
