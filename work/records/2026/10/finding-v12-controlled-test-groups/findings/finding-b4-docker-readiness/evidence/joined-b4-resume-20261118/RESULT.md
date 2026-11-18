# Joined B4 continuation — 242/242 pass

M385061; claim E385063; baton.codxpc / impl. Decisions: child FINDING/PLAN and `review-2026-11-18T01-59-25Z.md`. Exact source `438eefa68f592e159f42cf1d190c7d7de4afde12` plus its declared consumed inputs, same 1,134-file snapshot. No product or test edits; no K working-tree bytes imported.

The 143 independently accepted passes were preserved without rerunning them. This continuation ran exactly the other99 IDs:99 passed,26 successful subtests, zero failed/errors/skips/unaccounted/duplicates. Exact disjoint union is242 passed and114 successful subtests. `combined-ledger.json` records both ID sets and the complete expected set; `finalize.py` asserts equality and all outcome/cleanup predicates. Earlier interrupted attempt and its archived fixture remain unchanged, with prior evidence hashes reverified. This establishes the selected combined B4 result, not parent B5/full-suite acceptance.

## Evidence wrapper correction

`docker-shim.py` now uses `os.execv` for `docker exec`, passing stdin/stdout/stderr descriptors directly and preserving process exit and signal behavior. Other run calls retain exact container attribution via unique labels and creation-time cidfiles. Build/pull calls are refused and run calls add `--pull=never`.

Before Docker execution, `prove-streaming.py` used a deterministic local fake executable to prove two alternating input/response frames arrive before stdin closes, stderr remains separate, exit23 is preserved and SIGTERM returns-15. Three-second bounded reads/waits; evidence `streaming-proof.json` and `fake-engine.jsonl`. Temporary fake fixture removed. This changes evidence tooling only.

## Test results

| Selection | Passed | Seconds | Evidence |
|---|---:|---:|---|
| tests.manager.test_integration_worker | 83 | 18.432 | prior accepted |
| tests.manager.test_private_line_access_engine | 4 | 2.466 | prior accepted |
| tests.manager.test_input_delivery | 56 | 6.271 | prior accepted |
| tests.manager.test_worker_entry_engine | 5 | 1.615 | continuation |
| tests.manager.test_custody_engine | 12 | 16.730 | continuation |
| tests.manager.test_credentials_engine | 9 | 1.666 | continuation |
| tests.manager.test_lifecycle_composition | 32 | 6.772 | continuation |
| tests.manager.test_ended_runtime_adoption | 8 | 3.868 | continuation |
| tests.manager.test_negative_race_endings | 5 | 32.995 | continuation |
| tests.manager.test_integration_image.TheRecipeSaysWhatItWasReviewedToSay | 7 | 0.314 | continuation |
| tests.manager.test_integration_image.TheCopiedLayoutIsEnoughToStartTheEntry | 5 | 0.414 | continuation |
| tests.manager.test_worker_image.ABootstrapFaultIsLatchedAndCorrelated | 9 | 0.314 | continuation |
| tests.integration.test_driver.TheOrdinaryCommandTraversesPublicAdmission | 7 | 2.065 | continuation |

Continuation test processes total66.753s. Per-selection600s timeout, failfast, process-group TERM/KILL escalation; no timeout or emergency container cleanup occurred. `invocation.json` records exact arguments, cwd, image/flag environment and unique disk roots. `audit-tests.py` is standard unittest execution with explicit outcome ledgers. `recollected.json` independently matches the99 selected expected IDs before running. No live provider, supervised runtime-deadline, broad/full suite, or network pulls.

## Source, image and resource provenance

Prior source-after equals continuation before/after and every manifest content digest. Worker context unchanged. `image-reuse-probe.json` proves recorded worker image was absent. M385061-authorized one additional offline build used the same exact context and installed pinned base with `--pull=false --network=none`;0.114s. `build-plan.json`, `build.log`, `build-result.json` record provenance. New image ID `sha256:4da24074d73c8bdeb7ad676ca646287f356f84fbccf517f1f6052686b020ef83`; build metadata may change image identity despite identical source/context. Fresh daemon/group/private-image checks recorded in `fresh-preflight.json`; historical selected Git-capable initial-access image was retained.

All78 continuation-created container IDs absent, all task roots removed, no emergency cleanup; task worker tag removed. Pre-existing image/container ID sets preserved, independently checked in finalize.py. Prior38-container cleanup remains preserved evidence; historical resources were not pruned. Ordinary deterministic/fake provider execution only.

## Reproduction and handoff

Helpers, commands, logs, per-selection ledgers, stable source manifest and consumed-input list are durable here. Run sequence was `python3 prove-streaming.py`, image inspection and selected `python3 build-worker.py`, read-only current collection, `python3 run-joined.py`, then `python3 finalize.py`. Helpers are one-shot evidence producers (output directories/logs intentionally refuse overwriting). Prior snapshot can be reconstructed through its preserved materialize.py and source-manifest.json from the exact commit; no required evidence exists only in scratch. `SHA256.json` hashes every current evidence file except itself.

Pass W384944 to baton.decide for independent review of this combined result. No further tests or source changes proposed in this episode; parent B5/final acceptance remain separate.
