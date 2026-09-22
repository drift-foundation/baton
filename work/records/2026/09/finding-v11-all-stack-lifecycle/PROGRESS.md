# Progress

Implementation not started. Owner decision and bounded scope recorded by baton.prompt; implementation author will append evidence under a successful Work claim.

## 2026-09-22 — baton.prompt assisting owner claim235256

Implemented explicit all-stack wrapper without changing `tools/infra.py`. Required registry validates labels, relative paths, canonical duplicates and mandatory main membership. Separate safe deployment lock plus existing member locks; start preflights manifests, retains previous successes on partial failure, reports unattempted members; stop/status aggregate all members. Just recipes use the wrapper; docs preserve immediate stop and explicit single-stack/drain controls. Current deployment packet names main/rview-pc/codx-pc. No live service actions or Git mutations.

Focused new suite: 15 passed in 4.07s, command `.venv/bin/python3 -m pytest -q tests/work/test_infra_deployment.py`. Includes actual stand-in three-stack lifecycle, missing reviewer status, partial start and existing-main PID preservation, malformed-manifest owned stop, registry refusal, alias-lock serialization, stale-start refusal/explicit recovery, aggregate stop refusal and no resume invocation. Existing lifecycle compatibility subset follows. `git diff --check` clean. No live model calls; registry not yet installed.

Compatibility subset: 6 passed, 40 deselected in 1.81s, selecting `complete_start_status_stop or stop_uses_owned_state or partial_state_refuses or stop_refuses_pid_reuse or child_crash_is_visible` from tests/work/test_w20_infrastructure_lifecycle.py. Total measured pytest time5.88s. `just --show start/stop/status` confirms all three recipes call the wrapper. Awaiting independent source review and then registration install; no existing test expectations changed.

## 2026-09-22 — prompt-assisted installation, owner claim235316

Review235291 accepted exact candidate and independently checked six additional
no-service cases (reviewer measured0.002326763999008108s). Rechecked matching
candidate hashes and destination absence; installed exact reviewed registry,
hash0407fdd42db431a5149e377c8d9e6d737f38c72c08b6569fdd4df5a78dd1b301.
Host `just status /home/sl/baton-v11` reports all three stacks: main9 healthy,
reviewer3 healthy, coder3 stopped/partial-or-stale. Correct aggregate failure,
not a claim that every service is healthy. No restart, provider call or Git
mutation; source change, independent review and registration installation done.
