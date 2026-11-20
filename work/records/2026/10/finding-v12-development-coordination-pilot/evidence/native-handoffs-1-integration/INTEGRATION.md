# W385331 slice 1 — integration of the accepted candidate `f62bbaab…` into the working tree (K, owner-held arrangement)

K (`baton.prompt`, no claim held), 2026-11-20, on the owner's instruction after the acceptance (M385371, `review-2026-11-20T21-32-47Z.md`, E385370): prepare integration of the accepted 36-path candidate bound by manifest `4925897d…`; preflight every target for base-byte agreement, type, writable mode and overlap; import only the accepted bytes; refuse drift; run bounded integration checks and the packaging gate avoiding the hazardous `checkpoint_profiles` path; return exact post-import hashes, evidence and selective Git commands. No Git mutation, image rebuild, instance update or live launch. This is the human-plus-agent integration default (AGENTS.md, owner 2026-09-21): the working tree now carries the accepted bytes; staging, commit and history are Slawomir's.

## What was integrated

| | |
|---|---|
| Candidate | tree `sha256:f62bbaab53c7d6a7f9730b726d68fac8cefe48a92130cdc176924acd1ec64028`, 36 paths (30 modified, 6 added) over `3d05430f` |
| Manifest | `evidence/native-handoffs-1-correction-2/manifest.json`, sha256 `4925897d2bdf6e343d6eac229544b7c2c308f31fbf59ce01ec8b70b9c2aafd24` (re-digested before import) |
| Acceptance | `work/records/2026/11/finding-v12-native-agent-handoffs-discovery/review-2026-11-20T21-32-47Z.md` (codexpc, E385370): "accepted for the first native handoff source slice"; R1–R3 accepted in `review-2026-11-20T20-53-37Z.md`, R4a resolved; W385331 passed to `baton.decide` |
| Source of bytes | `evidence/native-handoffs-1-correction-2/candidate/<path>` — each file re-digested against the manifest's `candidate` sha256 before copying |

## Preflight (`PREFLIGHT.json`) — all 36 targets, before any write

- Packet: manifest sha256 equals the accepted one; `candidate.sha256` re-digests to the accepted tree; every `candidate/` file equals its manifest digest.
- Host: `HEAD` = `3d05430f` (the candidate's base); `git status --porcelain -- v12` empty (no overlap with any pending change; no untracked file under `v12/`).
- Each of the 30 modified targets: a regular file (not a link), owner-writable, bytes equal to the manifest's `base_3d05430f` digest, `git hash-object` equal to the manifest's `base_blob` AND to `HEAD:<path>`.
- Each of the 6 added targets: absent; parent a plain directory.
- Verdict: `PREFLIGHT OK`, zero faults.

## Import (`POST-IMPORT.json`, `post-import.sha256`, `imported-paths.txt`)

Ordinary file writes only: each target written from the packet copy through a sibling temporary and `os.replace`, keeping the existing mode for modified files and `0644` for added ones (no custody mode copied; no `install`/`chmod` workaround). After import every path's sha256 and `git hash-object` equal the manifest's `candidate` and `candidate_blob`; the tree digest recomputed over the host files is **`sha256:f62bbaab53c7d6a7f9730b726d68fac8cefe48a92130cdc176924acd1ec64028`**; `git status --porcelain -- v12` lists exactly the 36 paths (30 ` M`, 6 `??`) and nothing else; no `.git/index.lock`; Git index and history untouched.

## Bounded integration checks on the HOST tree (21:49–22:00Z)

| Run (host checkout `/home/sl/src/baton`, prepared interpreter 3.13.7, `BATON_V12_STACK_TEST_ROOT=/var/tmp/baton-v12-handoffs-1/integration`, `TMPDIR=/var/tmp/baton-v12-handoffs-1/integration-tmp`) | Result |
|---|---|
| The Job's exact six-module argv (`host-six-module.log`) | **Ran 342, OK** |
| `just test-group authority` (`host-group-authority.log`) | collected 509, passed 509 |
| `just test-group scans` (`host-group-scans.log`) | collected 494, passed 492 + 2 optional skips; 0 failures |
| `just test-group job_manager` (`host-group-job_manager.log`) | collected 1718, passed 1715, failed 3 — the same three identities as every earlier run and the pre-import host baseline (`test_store_readonly` ×1, `test_tool` ×2; `native-handoffs-1-recovery/continuation/modules-store-readonly-tool-HOST-BASE.log`) |
| `just test-group tools-pure` (`host-group-tools-pure.log`) | collected 3520, **passed 3520**, 0 failures — on the real checkout the two `test_source_identity` cases (declared inputs present) and `test_live_ab` pass; round 1's transient PR-seed case passed (attributes nothing) |
| manager-pure, run as its 59 modules MINUS `tests.manager.test_checkpoint_profiles` (`host-manager-pure-minus-hazard.log`; `python -m unittest`, NOT the accounted group runner) | Ran 4391, **failed 1** — `test_store.ReadonlyAcquisition.test_a_failed_read_NAMES_THE_STORE…`, the one identity previously reproduced on the untouched host tree (`host-baseline-suspects.log`); the five others that failed on the outside copy (`test_integration_worker` ×2, `test_custody`, `test_frozen`, `test_w197661_verifier`) pass on the real checkout with its declared inputs and `build/` |
| Packaging gate `just --justfile v12/justfile test-packaging` (`host-packaging-gate.log`; roots `/var/tmp/baton-v12-handoffs-1/packaging`, `TMPDIR=/var/tmp/baton-v12-handoffs-1/packaging-tmp`) | built once from the imported source and gated: **Ran 24, OK**, exit 0, 22 s; bundle executable `build/out/distro/baton-v12-stack` sha256 `5edf013eb3f69d0fded3928428078df5210689c0cb8e25531f4d592e6ff0274a` (ignored `build/`, not part of the 36 paths) |

Not run: `tests.manager.test_checkpoint_profiles` (hazard: nominates the owner's live checkout; its three classes remain unverified on these bytes). Measured wall: six-module 19 s; authority 3 s; scans 102 s; job_manager 16 s; tools-pure 170 s; manager-pure-minus-hazard 239 s; packaging 22 s.


**Withdrawn first run (`logs/withdrawn-tmpdir-inside-checkout/`).** The first host run used `TMPDIR=work/scratch/w383217/handoffs-recovery/tmp`, which is INSIDE the checkout; on the real checkout every test that composes a deployment or instance under `TMPDIR` refuses "inside the checkout" (81 occurrences in its tools-pure log; one `test_native_permission` error in job_manager). That is my environment choice, not a property of the imported bytes — the same tests passed on the outside-checkout copy and pass on the host once `TMPDIR` is outside (`/var/tmp/baton-v12-handoffs-1/integration-tmp`). The run was stopped before its packaging step and its logs are kept as evidence, not as a result.

## Selective Git commands

`GIT-COMMANDS.md` (preflight reads, `git add` of exactly the 36 paths from `imported-paths.txt`, optional dossier records, `git commit -F commit-message.txt`). Proposed message: `commit-message.txt`. Not run.

## Not done, by instruction

No `git add`/`commit`; no worker image rebuild (`v12/worker/claude_agent.py` is a Dockerfile input, so the current image `baton-v12-worker:e670e624` does not carry this adapter); no instance update (`native-handoffs-1` and the retained `native-labels-*` instances untouched); no live launch; `tests.manager.test_checkpoint_profiles` not run (hazard: it nominates the owner's live checkout); the schema-7 Authority is a fresh-store step (a retained store at 6 is refused, not migrated).
