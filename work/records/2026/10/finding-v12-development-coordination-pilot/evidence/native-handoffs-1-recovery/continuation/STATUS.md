# W385331 slice 1 — continuation of the retained `w385331-handoffs-1` candidate (interim status, 2026-11-20 18:05Z)

K (`baton.prompt`, no claim held) under the owner-held W321608 arrangement, on the owner's instruction "finish the candidate in isolation, verify the required behavior, and return a digest-bound proposal". Everything below is in the isolated copy `work/scratch/w383217/handoffs-recovery/candidate/` (archive of `3d05430f` + the frozen `a743edeb` patch + K's edits). Host tree, instance `native-handoffs-1`, stores and Git untouched. Independent review and human integration still required.

## Where things are

| What | Where |
|---|---|
| Diagnosis of the timed-out Job and custody proof of `a743edeb` | `evidence/native-handoffs-1-recovery/DIAGNOSIS.md` (T321608 seq 385352) |
| Frozen retained proposal (byte copies + sha256) | `evidence/native-handoffs-1-recovery/proposal/`, `proposal.sha256` |
| Separate finding for codexpc (status prints "cause unknown") | `evidence/native-handoffs-1-recovery/FINDING-status-cause-unknown.md` |
| This continuation's run logs | `evidence/native-handoffs-1-recovery/continuation/*.log` |
| The working candidate (disposable until the packet is cut) | `work/scratch/w383217/handoffs-recovery/candidate/` |
| Digest-bound packet (patches, manifest, tree digest, candidate files) | `evidence/native-handoffs-1-continuation/` — **not yet cut**; built by `work/scratch/w383217/handoffs-recovery/build_packet.py` once the regression below finishes |

## What was finished (against NATIVE-TASK.txt)

- `tests/job_manager/test_native_handoffs.py` repaired (the rewrite the 3600 s bound cut off: quadruple-quoted docstrings, a missing fake-profile helper, a wrong cancellation operand) and extended: **60 tests OK** (`continuation/jm-final.log`).
- `tests/tools/test_native_handoffs.py` written: one native handoff end to end over the composed stage deployment with the real worker adapter through `serve_exchange` and a scripted provider — clarification yield → reviewer answer → same-task continuation on the retained checkpoint → ordinary final review → integration claim, with zero human acts; finding variant; one escalation to the owner that stays held and is reread, never re-raised; a malformed request refused not published; restart between the cuts duplicates no message, attempt or continuation. **7 tests OK** (`continuation/tools-module-run.log`, `tools-malformed.log`).
- The three modules registered once in `tools/parallel_test.py`; `v12/STACK.md` section "Native handoffs — a question is not a candidate".

## Defects in the retained candidate found by the end-to-end run, and fixed

1. The request was committed to the Authority **after** the checkpoint freeze, which had already fenced the producer assignment (`assignment generation was fenced and ended`). Moved before the freeze under the live assignment; the worker-claimed head is cross-bound against the frozen checkpoint right after it (`native_handoffs.cross_bound`); the message's `checkpoint_ref` is the retained head object.
2. The response branch was dispatched from the frozen result, which the ending itself creates, so the verdict branch ran first. Dispatch is now the fact the deployment holds: this review attempt was delivered a pending request (plus the completion envelope as a fallback).
3. A review episode that ended in a reply projected `completed` and opened the integration gate on a question. Added the Job-store record `native.answer` and the review state `answered` (not `completed`, not a verdict).
4. The response ending was not re-enterable behind a destroyed runtime (the continuation is asked while the reviewer's allocation is still reserved, so the conclude defers once by design). `record_response` now replays its committed response historically, like `record_verdict`.

## What the candidate did not have at all, now added

- Worker adapter (`v12/worker/claude_agent.py`): `handoff`/`response` declared outputs; provider-authored `handoff/request.json` and `response.json` bound into `baton.native-handoff/1` documents; a yield skips verification; a final submission declares itself; malformed requests refused.
- Delivery (`tools/single_worker.py`, `tools/stage_execution.py`, `native_handoffs.delivered_context`): one read-only `handoff.json` beside `task.json` carrying the configured recipient, the pending request for a reviewer, or the exact question and reply for a continuation.

## Verification state

| Run | Result |
|---|---|
| `tests.job_manager.test_native_handoffs` | 60 OK |
| `tests.tools.test_native_handoffs` | 7 OK |
| `tests.authority.test_work_messages` | 63 OK (unchanged from the retained candidate) |
| Quick regression (role_contract, output, job_control, role_capability, templates, adapter_declaration, single_worker + the above) | 689 OK (`continuation/quick-regression-1.log`, before the last four fixes) |
| Broad regression (review_driver, claude_agent, parallel_runner registry, contracts/boundary/text/dependency scans, job_observation, worker_packaging, stage_execution) | **running** since 17:57Z (`continuation/regression-2.log`) |
| Group accounting via `just test-group` (authority, job_manager, tools-pure, manager-pure) and the Job's exact six-module argv on the final candidate | **not yet run**; scheduled after the broad regression |

Nothing here is acceptance. The worker image must be rebuilt for the adapter change before any live use; Authority schema version is 7 (owner ruling owed for the number, as the candidate's own note says).

## Still open

- Finish verification (above), cut the packet, append PROGRESS.md, post to T321608.
- Independent review by `baton.rvpc`; human integration and Git checkpoint (owner).
- No-edit yield (a question with zero changes) is allowed by the worker but not exercised end to end.
- Next slice (nonblocking Work filing / blocking prerequisite) untouched, per FIRST-NATIVE-SLICE.md.

## Final (18:33Z) — packet cut

- Digest-bound proposal: `evidence/native-handoffs-1-continuation/` — `CONTINUATION.md` (report), `manifest.json` (sha256 `1286fbc7…`), tree digest `sha256:ce757322b59fbd5ca14f6ec1cd1ecec14c2781fc10c1d53c235392aeb674b866` over 33 paths, `candidate-from-3d05430f.patch` (`f65372fd…`), `delta-from-a743edeb.patch` (`da6ee980…`), `candidate/` files, `provenance.json` (both reproductions verified byte for byte), `logs/`.
- Verification on the final bytes (outside-checkout copy): six-module argv 310 OK; authority 506/506; scans 494/494; job_manager 1693/1696, tools-pure 3492/3495, manager-pure 4424/4433 — every remaining failure reproduced on the untouched host tree under the same roots or is a copy artifact (no `build/`, no declared inputs, no git repository); none is a candidate regression. Fifth fix after the groups: `response_satisfies_dependency` on partial stage documents; plus the inventory declarations.
- Hazard noted in CONTINUATION.md: `tests.manager.test_checkpoint_profiles` attempts a `git checkout` against the owner's live checkout; refused by local changes; host tree verified unchanged (v12 clean, HEAD 3d05430f).
- Next: independent review (`baton.rvpc`) of the packet; owner image rebuild/qualification and Git checkpoint after acceptance; schema-7 ruling.

## Correction round 1 (20:50Z) — review 2026-11-20T19-39-15Z R1–R4 answered

- Refreshed digest-bound packet for independent DELTA review: `evidence/native-handoffs-1-correction/` — `CORRECTION.md` (report), `manifest.json` (sha256 `97eb669f…`), tree digest `sha256:766f97f2e49809c5a2ebedece65d3ebd6f6d4d933b795efd2490b4726368345a` over 35 paths (13 changed against the reviewed `ce757322`), patches from `3d05430f` (`8595210c…`), from `a743edeb` (`551e3bf7…`) and from `ce757322` (`4d65056c…`, the review delta), `candidate/`, `provenance.json` (three reproductions byte for byte), `logs/`.
- R1 continuation bytes delivered (custody → yield record → delivery, read-only in the resumed working copy and in the prompt; tamper refuses); R2 retry replays the committed continuation from the original yield before any guard; R3 reply bound to the attempt's fixed assignment and the exact delivered request, Authority binds Work/Job; R4 bootstrap `native_handoff_routing` installs the policy and the reviewer's `answer-handoff` grant; schema-7 wording settled. Exact proofs and accounting in `CORRECTION.md`.
- Verification on the final bytes: six-module argv 342 OK; authority 509/509; scans 492+2 optional/494; job_manager 1715/1718 (same 3 identities); tools-pure 3508/3512 first run with one new non-reproduced shard failure (module 477 OK serially, class 58 OK, second run 3509/3512 = the three known identities only); manager-pure minus the hazardous `test_checkpoint_profiles` 4391 ran / 6 failures (same six identities); the hazardous module's three classes remain unverified on this candidate.
- Next: independent delta review (`baton.codx`); owner image rebuild/qualification and Git checkpoint after acceptance.

## Correction round 2 (21:30Z) — delta review 2026-11-20T20-53-37Z R4a answered

- Refreshed digest-bound packet for independent DELTA review: `evidence/native-handoffs-1-correction-2/` — `CORRECTION.md`, `manifest.json` (sha256 `4925897d…`), tree digest `sha256:f62bbaab53c7d6a7f9730b726d68fac8cefe48a92130cdc176924acd1ec64028` over 36 paths (4 changed against the reviewed `766f97f2`: `tools/bootstrap.py`, `tests/tools/test_bootstrap.py`, `tests/tools/test_connected_creation.py`, `v12/STACK.md`; no `src/baton_v12` or worker byte changed), patches from `3d05430f` (`265f6d3e…`), `a743edeb` (`8f0395da…`) and `766f97f2` (`9a50ac60…`, the review delta), `candidate/`, `provenance.json`, `logs/`.
- R4a: both routing addresses held to `authority.messages.check_routing` in bootstrap preflight (one grammar); the selection proved in `bootstrap.main` before the runtime is admitted, repositories cloned or roots made, in both forms. Proofs: 14 bootstrap cases (nine malformed spellings per address, nothing composed; refused repeat keeps policy and grant) and 4 real-installer cases through `bootstrap.main` + `job_manager.main` (install → `/3` creation → scoped grant; the reviewer's malformed-recipient probe refused with exit 2 and nothing durable; malformed reviewer; refused repeat keeps `install-inputs.json` and policy). No existing test expectation changed.
- Verification: six-module 342 OK; installer-related modules 538 OK; authority 509/509; scans 492+2/494; job_manager 1715/1718 (same 3); tools-pure 3517/3520 (same 3); manager-pure minus the hazard 4391/6 (same 6). A withdrawn whole-document-preflight cut is retained under `logs/withdrawn-whole-document-preflight/`.
- Next: independent delta review (`baton.codx`); owner image rebuild/qualification and Git checkpoint after acceptance.

## Integration (22:05Z) — accepted candidate `f62bbaab…` imported into the working tree; owner checkpoint pending

- Acceptance: codexpc `review-2026-11-20T21-32-47Z.md` (E385370, M385371). Record: `evidence/native-handoffs-1-integration/` (INTEGRATION.md, PREFLIGHT.json, POST-IMPORT.json, post-import.sha256, imported-paths.txt, GIT-COMMANDS.md, commit-message.txt, logs/).
- Preflight OK on all 36 targets (packet digests, HEAD = 3d05430f, v12 clean, base bytes/blobs, types, owner-writable modes, added paths absent); imported by ordinary file writes; post-import every path equals the manifest's candidate sha256/blob, host tree digest `sha256:f62bbaab53c7d6a7f9730b726d68fac8cefe48a92130cdc176924acd1ec64028`, `git status -- v12` exactly the 36 paths; Git index/history untouched.
- Host checks (TMPDIR outside the checkout): six-module 342 OK; authority 509/509; scans 492+2/494; job_manager 1715/1718 (same 3); tools-pure 3520/3520; manager-pure minus the hazard 4391/1 (store-readonly baseline); packaging gate 24 OK (bundle exe sha256 `5edf013eb3f69d0fded3928428078df5210689c0cb8e25531f4d592e6ff0274a`). A first run with TMPDIR inside the checkout was withdrawn (logs kept).
- Next: owner stages the 36 paths and commits (`GIT-COMMANDS.md`, `commit-message.txt`); then image rebuild/qualification and any instance update as separate selections.
