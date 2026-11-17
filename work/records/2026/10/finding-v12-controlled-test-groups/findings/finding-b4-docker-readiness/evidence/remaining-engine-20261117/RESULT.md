# Remaining historical engine failures — W384944 / E385031

Assignment M385029, review-2026-11-17T19-36-36Z.md and parent RESUME-DECISIONS-20261117.md. Seven selected historical IDs now pass; final four affected classes: **54 collected/started/passed, 3 successful subtests, zero failures/errors/skips/duplicates/unaccounted**. Independent review and final joined-current-source/full acceptance remain due.

## Changes and preserved behavior

Only the four allocated test files changed; exact base/candidate bytes, individual diffs and hashes are here. candidate.json SHA256 is 74f7f6e827dbbe2469bd7a6e7d832abcb3fb93ac9b2e06d0ad67a0c2a05301d3.

- test_credentials_engine.py and test_lifecycle_composition.py: cleanup checks intersect real daemon names with this class run's registered names, rather than claiming ownership of all historical names with the same prefix. Each cleanup regression first starts a real runtime and proves the sweep rejects its presence, then removes it and proves absence. No pre-existing container is adopted or removed. Lifecycle's existing per-case cleanup still verifies every attempted removal; exact post-run ID cleanup is separately established by the evidence runner.
- test_lifecycle_composition.py, test_ended_runtime_adoption.py and test_negative_race_endings.py: the five completed cleanup crossings retain the actual execution roots, as DESIGN primary lifecycle and isolated intake.authorize_cleanup (preserved=True) require. New before/after checks bind root and descendant device/inode, mode, UID/GID, regular-file SHA256 and symlink text. They assert retained+absent, no invented directory-custody receipt, empty kept-artifact list after explicit custody-copy discard, unchanged root trees and no additional adapter runtime launches. Existing exact removal/absence/provider-teardown ordering, siblings' runtime/credential survival, unresolved provider hold, real refused successor and successful reuse checks remain. The main arc still asserts discarded intake copies are actually gone; preserved workspace and retained intake copies are not conflated.
- Lifecycle adapter/prepared helpers now accept interactive=False, passed to the existing product option. Two additional failures surfaced in the affected-class check: running-runtime adoption and live deadline cleanup had depended on observing a worker before it exited on stdin EOF. Only these two tests select interactive=True, keeping the real worker waiting for input. They continue to require the daemon to observe running; deadline fencing, positive absence and lane release still execute. Ordinary EOF-ended cases retain interactive=False.
- The two fixture classes accept an explicit immutable BATON_V12_LIFECYCLE_IMAGE and verify exact installed identity and absence of implicit volumes. Unset selection retains prior build behavior. This batch performed one recorded offline build and reused its digest; no per-class implicit builds occurred.

No product/K/shared helper changes, live providers, broad engine/group/full run, Git mutation or specification change. Source adjustments beyond the seven IDs are documented in child PROGRESS and confined to the same allocated fixture classes.

## Restored prerequisites, source and image

preflight.json proves actual uid1000/group1001, prepared Python3.13.7/jsonschema4.26.0, Docker29.1.3 and disk-backed writable roots. All1133 files match the custody-final selected source before edits, including five accepted test overlays and exact cleanup-only workspaces.py. Recorded worker context matches byte-for-byte. Installed pinned base python@sha256:8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3 resolves to sha256:9351a9a0a697a69e156f8bd067dd5ef3f9fa9b110abbdbbda1f343c622c7adc0.

build-plan.json/build.log/build-result.json record the one --pull=false --network=none build (0.113619s), image sha256:e45807c1a9b07638fba9e25d33a6a6a101e35ef6ecd7d5e00cfbc72cb8d7a747. context.json binds every worker input. Each run hashes the1133-file source before/after with zero drift; final differences from restored source are exactly four allocated tests. Shared targets all matched recorded bases before any publish; exact candidate bytes copied with original0664 modes preserved. Focused git diff --check passes.

## Measured runs and accounting

| Run | Result | Command wall seconds |
| --- | --- | ---: |
| baseline | 7 tests, all7 historical failures reproduced | 3.718151 |
| affected | 7/7 pass | 4.469223 |
| classes | 54 tests,52 pass/2 live-worker fixture failures | 13.780359 |
| livefixtures | 2/2 pass after interactive correction | 31.191114 |
| complete | 54/54 pass;3/3 subtests | 44.109884 |

Total focused command wall97.268731s, plus build0.113619s. No timeouts. Earlier failing runs retained rather than overwritten. First four runs use version-level just test-one; final run uses the same prepared interpreter and unittest loader/runner with audit-tests.py to record successful subtests too (plain unittest -v does not enumerate those). That evidence-only recorder changes no test/product behavior; final complete/ledger.json lists exact collected, started, passed and subtest IDs. Earlier ledgers.json accounts top-level IDs from retained verbose logs; it does not invent successful subtest counts for runs without the recorder. Run caps600s, build1800s, with exact cleanup; the successful live deadline naturally uses the product's30-second stop grace.

## Cleanup and remaining work

resource-cleanup.json binds all104 exact task-created container IDs across all runs (creation-time cidfiles also cover auto-removed objects), positively absent from the final full daemon listing. Every task root is removed, all task labels empty, own image tag removed, and pre-existing container/image IDs preserved. No emergency container removal was needed. Completed run subprocesses exited; no owned background job remains.

remaining-historical-engine-ids.tsv is now header-only: all seven selected IDs have passing evidence, subject to independent acceptance. This is not full B4 completion. remaining-pure-driver-historical.tsv retains the two pure image fixture failures and three integration driver IDs from the prior inventory; none was rerun or changed here. They require revalidation against accepted current source before later allocation.

B5 remains parent-owned: C10 singleton triage (launch, execution_limits, correction_restart, secrets, authority boundary, parallel_runner, stage_execution_hardening, environment, single_worker, quiescent_finalization, runtime_lane, reconciliation_worker and job_manager items), with earlier parent work potentially superseding individual historical failures. Parent PLAN sections8–9 and current CLOSURE-CHECKLIST own this list; no fresh B5 failure count is asserted. Stage C acceptance, joined current-source verification, required supervised/final full accounting, independent final review and owner closure/check-in still gate W383215.

## Recovery

Scratch is disposable. Recover original a8cbc974 inputs using evidence/allocation-c4-20261031/snapshot-manifest.json, then the exact accepted overlays identified by evidence/custody-final-20261031/selected-source.json, then these four candidate files. Verify every hash in selected-source.json; do not substitute K's current product tree. Preserve original source modes from allocation, and0664 for these four existing targets. The recorded build context and pinned installed base must be revalidated before a separately selected rerun; run-focused.py reads build-result.json and does not assume its image is still installed. Durable evidence and all candidate bytes live in this dossier; no checkpoint depends solely on scratch.
