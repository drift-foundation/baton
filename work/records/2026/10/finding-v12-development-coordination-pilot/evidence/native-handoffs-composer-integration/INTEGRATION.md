# W385331 composer — integration of the accepted candidate `bb5fa705…` into the working tree (K, owner-held arrangement)

K (`baton.prompt`, no claim held), 2026-11-21, on the owner's instruction after the acceptance (M385397, `review-2026-11-21T02-04-24Z.md`, E385396; C1/C2 resolved in `review-2026-11-21T00-55-22Z.md`, product unchanged through `review-2026-11-21T01-49-15Z.md`): prepare integration of the accepted 12-path composer candidate bound by manifest `fa01b73d…` over `331dd737`; verify every target against the reviewed base; import only the accepted bytes; run bounded integration checks; preserve the qualification helpers, packet history and reviews; return post-import hashes and selective Git commands. No Git mutation, image build, installation or live launch. Human-plus-agent integration default (AGENTS.md, owner 2026-09-21): the working tree now carries the accepted bytes; staging, commit and history are Slawomir's.

## What was integrated

| | |
|---|---|
| Candidate | tree `sha256:bb5fa7050da82902b87d07b6a21447fe1fc14963cddebf879b0456794375e365`, 12 paths (all modified, none added) over `331dd7379b492ac0ad6c742ded032643ad17ce9c` |
| Manifest | `evidence/native-handoffs-composer/manifest.json`, sha256 `fa01b73d811ffabee510d333f18a97153ab197a21bf16ea32f92736be8ce1e77` (re-digested before import); `candidate.sha256` re-digests to the tree |
| Acceptance | `work/records/2026/11/finding-v12-native-agent-handoffs-discovery/review-2026-11-21T02-04-24Z.md` (codexpc, E385396): product tree/manifest "unchanged … all 12 candidate hashes unchanged", "Accepted"; C1/C2 resolved in `review-2026-11-21T00-55-22Z.md` |
| Source of bytes | `evidence/native-handoffs-composer/candidate/<path>` — each file re-digested against the manifest's `candidate` sha256 and `candidate_blob` before copying |
| Tool | `integrate.py` (this directory; `preflight` then `import`, Git read-only) |

## Preflight (`PREFLIGHT.json`) — all 12 targets, before any write

- Packet: manifest sha256 equals the accepted one; base and tree digest as accepted; every `candidate/` file equals its manifest sha256 and blob.
- Host: `HEAD` = `331dd737` (the candidate's base); `git status --porcelain -- v12` empty; no `.git/index.lock`.
- Each of the 12 targets: a regular file (not a link), owner-writable (modes `0644`/`0664`), bytes equal to the manifest's `base_331dd737` digest, `git hash-object` equal to the manifest's `base_blob` AND to `HEAD:<path>`.
- Verdict: `PREFLIGHT OK`, zero faults (02:0x Z; the preflight was run twice, once alone and once inside `import`).

## Import (`POST-IMPORT.json`, `post-import.sha256`, `imported-paths.txt`)

Ordinary file writes only: each target written from the packet copy through a sibling temporary and `os.replace`, keeping the existing mode (no custody mode copied; no `install`/`chmod` workaround). After import every path's sha256 and blob equal the manifest's `candidate`/`candidate_blob`; the tree digest recomputed over the host files is **`sha256:bb5fa7050da82902b87d07b6a21447fe1fc14963cddebf879b0456794375e365`**; `git status --porcelain -- v12` lists exactly the 12 paths, all ` M`, and nothing else; no `.git/index.lock`; Git index and history untouched. (`POST-IMPORT.json` carries `status_check_note`: the tool's first status comparison stripped the leading space of the first porcelain line and reported `false`; it was recomputed from unstripped output after the import, no file changed, and the tool was corrected.)

## Bounded integration checks on the HOST tree (02:07:57Z–02:11:28Z, 211 s for the chain)

Groups declared (TESTING.md): `job_manager` (creation.py, role_capability.py, test_creation.py), `tools-pure` (the seven `tools/` and `tests/tools/` paths), plus the packaging gate (pool.py is bundle content; the qualification `bundle` step expects `--template` in the packaged help). Prepared interpreter via the recipes; `BATON_V12_STACK_TEST_ROOT`/`BATON_V12_DISK_ROOT` under `/var/tmp/baton-v12-handoffs-2/`, `TMPDIR` outside the checkout.

| Run | Result |
|---|---|
| `just test-group job_manager` (`logs/host-group-job_manager.log`) | collected 1722 (+4 over the pre-import 1718: the new `test_creation` cases), executed 1722, passed 1719, **failed 3 — the same three identities as the pre-import host baseline and every earlier run** (`test_store_readonly…test_a_failed_read_reports_SQLITES_WORDS…`, `test_tool…test_a_TWO_STORE_status_refusal…`, `test_tool…test_the_CONTROL_STORE_refusal…`; cf. `native-handoffs-1-integration/logs/host-group-job_manager.log` lines 733–745); the accounted recipe therefore exits 1 |
| `just test-group tools-pure` (`logs/host-group-tools-pure.log`) | collected 3531 (+11 over 3520: the new `test_pool`/`test_connected_creation` cases), executed 3531, passed 3530, **failed 1 — `tests.tools.test_next_run_flow.JoinedFlow.test_initial_partial_preparation_continues_to_real_work`**: `child_status -15` at 3.25 s under parallel load (the continuation's provider child killed at its 3 s turn bound; stand-in runtime "absent"). This is the known cause-unknown transient of that class under 32-way load (`reusable-kickoff-20261119/RESULT.md` row "group tools-pure": sibling `test_a_pre_runtime_source_refusal…` failed the same way twice, the class alone 5 OK). Not a composer path: `test_next_run_flow` passed in the candidate's focused run (`native-handoffs-composer/logs/c123-focused.log:2488`) and on this imported host tree **alone three times, OK in 4.66 s each** (`logs/rerun-next_run_flow-{1,2,3}.log`). Retained as observed, attributed to the harness's turn bound under load, not explained |
| Packaging gate `just --justfile v12/justfile test-packaging` (`logs/host-packaging-gate.log`) | built once from the imported source and gated: **Ran 24, OK**, exit 0; bundle `v12/python/build/out/distro/baton-v12-stack` sha256 `25330714ee073a5c190f6c6135698f23c3bb8e366ff9a755888efc28b7791880`; its `pool compose-worker --help` carries `--template` (2 mentions); stamp `commit 331dd737, dirty: true, changed_entries 32` (built from the pre-commit tree, as expected — the qualification `bundle` step rebuilds from the owner's checkpoint and asserts `dirty: false`) |

Not run: `manager-pure` (no path of this candidate is under `src/baton_v12/manager` or `tests/manager`; the hazardous `tests.manager.test_checkpoint_profiles` stays excluded), `authority`, `scans`, engine/integration/supervised/packaged groups; no ceremonial full run. The composer's own focused proofs on these exact bytes are the candidate's (`native-handoffs-composer/logs/`) and the reviewer's (`review-385384/`, `review-385396/`).

## Preserved, by instruction

`config/native-handoffs-2-bind.py` (4cc1469e…), `config/native-handoffs-2-qualify.sh` (d2404e16…), `evidence/native-handoffs-2-qualification/` (PACKET 0e4c8c94…, `history/`, `checks/`), `evidence/native-handoffs-composer/` (immutable at round 2, `HISTORY.md`) and every review under the W385331 dossier are untouched by this integration. Once the owner commits, that commit is the checkpoint `qualify.sh bind` consumes: it proves all 43 joined paths at `HEAD` (the 12 composer paths at these bytes, the 31 slice-only paths at `331dd737`'s) and refuses anything else.

## Selective Git commands

`GIT-COMMANDS.md` (preflight reads, `git add` of exactly the 12 paths from `imported-paths.txt`, optional dossier records, `git commit -F commit-message.txt`). Proposed message: `commit-message.txt`. Not run.

## Not done, by instruction

No `git add`/`commit`; no worker image build (the adapter `claude_agent.py` is unchanged by this candidate; the image rebuild is still due for the slice-1 adapter, step D of the qualification packet); no bundle installed; no instance touched (`native-handoffs-1`, `native-labels-{1..5}` untouched); no live launch; no store opened.
