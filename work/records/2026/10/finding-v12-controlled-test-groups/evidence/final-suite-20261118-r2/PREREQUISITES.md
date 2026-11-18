# Final accounted full suite, second selected run — owner-run command and prerequisites (M385115/M385116)

Prepared by K (copilot, no claim) on 2026-11-18 after owner checkpoint
`5b9659f0b44cbabdc3b8ef1b242375b911f071c7` ("fix(v12): honor workspace group in fixtures and clean engine
outputs", the accepted M385114 four-file fixture candidate over e80f2c8e). PREPARATION ONLY: nothing here was
executed except the read-only `preflight.sh` (`preflight-20261118T15.txt`: 11 ok, 0 failing). No test, build,
pull, source edit or Git mutation by K. Slawomir runs the suite after review of this packet; it is the integration
checkpoint W384870 selects (TESTING.md §3, §9, §10; AGENTS "V12 test execution policy"). The first selected run's
FAILED evidence in `../final-suite-20261118/` is preserved unchanged; this directory is the fresh one the wrapper
owns and it refuses to run if run evidence already exists here.

## What changed since the first packet

- Pinned checkpoint: `5b9659f0` (was `e80f2c8e`). Preflight fails closed on any other HEAD or a dirty `v12/`.
- `sg` is now a prerequisite of the selected dedicated-group fixture path (review 15-06-05Z): with
  `BATON_V12_WORKSPACE_GROUP=1001` and primary gid 1000, `MaintenanceCase.under_composed_identity` runs the real
  maintenance program as `sg baton-workspace -c <command>`. Preflight checks `sg` exists, that `sg baton-workspace -c
  'id -g'` really reports 1001 and that the uid stays 1000 (running_as remains the program's own account; nothing is
  rewritten). Verified on this host 2026-11-18T15Z.
- Historical residue is gone: the seven leftover roots are absent and `/var/tmp` is back at the 376 baseline
  (`../final-suite-20261118/leftover-roots/owner-cleanup-confirmed.json`); the wrapper records fresh before/after
  listings here.
- Everything else is byte-identical to the reviewed first packet (same environment, same recipe, same residue
  accounting, same `summarize.py`). `diff` the two directories to confirm.

## What the run is

`just test-all LOG [JOBS]` from `v12/` (forwards to `v12/python/justfile` `test-all`): `tools/parallel_test.py
--phase all --with-supervised --account --keep-going --summary LOG.summary.json --retain <dir of LOG>` on the
prepared interpreter, with the content-bound source identity taken before and after. It writes beside LOG:
`test-all.summary.json` (ledger: every id by outcome), `test-all.source.json`, `test-all.source-after.json`, and
the supervised run directory. Exit 0 only when `passed + optional skipped = collected` with zero
failed/errors/fixture/duplicate/unaccounted/uncollected ids and no source drift. It BUILDS a fresh bundle first
(PyInstaller, `just build`) unless `BATON_V12_STACK_DISTRO` names one; the current `build/out/distro` is from
e80f2c8e and will be replaced by a 5b9659f0 build.

## Prerequisites (all verified present by `preflight.sh` on 2026-11-18T15Z)

| need | value on this host | source |
|---|---|---|
| committed candidate, clean `v12/` | HEAD `5b9659f0b44cbabdc3b8ef1b242375b911f071c7`, 0 status lines under v12 | owner checkpoint (M385116) |
| prepared interpreter | `/home/sl/.local/state/baton-v12-venv/bin/python` (3.13.7) | `python3 -m tools.environment interpreter` |
| `just`, `git`, Docker daemon | present; 70 pre-existing containers, 1 running (`mdb114-a`, unrelated) | TESTING §2 |
| `BATON_W32577_IMAGE_DIGEST` reference worker image, preloaded | `sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8` (present) | TESTING §2; supervised gate never pulls |
| `BATON_V12_INITIAL_ACCESS_ENGINE=1`, `BATON_V12_PRIVATE_LINE_IMAGE`, `BATON_V12_WORKSPACE_GROUP` | `1`, `sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4` (present), `1001` (`baton-workspace`, caller is a member) | accepted B4 joined run; first-run invocation-environment.txt |
| `sg` adoption of the selected group | `/usr/bin/sg`; `sg baton-workspace -c 'id -g'` -> 1001; uid stays 1000 | review 15-06-05Z prerequisite; `tests/manager/test_maintenance.py` |
| disk-backed storage | `TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp` (ext4, 577 G free; `/tmp` is tmpfs); 376 entries = baseline | TESTING §2 |
| bundle | none selected: fresh build (default) | TESTING §2, §5 |
| optional engine image selection (`BATON_V12_{INPUT_DELIVERY,WORKER_ENTRY,CUSTODY,LIFECYCLE}_IMAGE`) | LEAVE UNSET (preflight fails if set): B4's `sha256:4da24074…` is absent locally; unset means the engine modules build their own | B4 evidence |
| `BATON_V12_LARGE_WORKSPACE_PROOF`, `BATON_V12_STACK_DISTRO` | unset (preflight fails if set) | `OPTIONAL_SKIPS`; TESTING §2 |

Without the three initial-access variables the four `test_private_line_access_engine` cases are REQUIRED skips and
the accounted run fails truthfully (TESTING §2 limitation); the wrapper exports them. The new supplementary-group
witness in `test_maintenance` is NOT an optional skip: on this host it runs (sl has other groups); on a host without
another group it would skip and fail an accounted run, which is the intended truthful outcome (review 15-06-05Z).

## Exact commands

Read-only preflight (repeatable; already recorded once):
```sh
/home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r2/preflight.sh
```

The run (one command; `JOBS` optional, e.g. `16`; omitted = all 32 CPUs as the first run did):
```sh
/home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r2/run-final-suite.sh
```
It is exactly, after the exports above and `/var/tmp` + `docker ps -a` + `docker images` listings before:
```sh
cd /home/sl/src/baton/v12 && just test-all /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r2/test-all.log
```
then the same listings after and `residue.txt`. The bare recipe can be run instead; the wrapper adds only the
preflight gate, the residue accounting and `invocation-environment.txt`.

Accounting afterwards (reads the ledger only):
```sh
python3 -I /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r2/summarize.py /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r2/test-all.summary.json > /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118-r2/ACCOUNTING.md
```

## Expectations and boundaries

- Duration: the first run executed 11 265 tests; expect roughly 15-40 minutes including the bundle build and the
  serial engine phase. The recipe has no timeout of its own. A retry after any fix is a NEW selected checkpoint
  (TESTING §10), not an automatic rerun, and never overwrites this directory.
- Expected ledger if the repair holds: collected = passed + 2 optional skips (same-filesystem bind mount: no user
  namespace on this host; large-workspace proof), 0 failed/errors/fixture/unaccounted; the 26 ids adverse in the
  first run (`../final-fix-20261118/RESULT.md`) pass under the composed group.
- Do not change `HEAD` or any file under `v12/` while it runs: the identity is re-taken afterwards and drift fails the
  run. Work records (this directory) are outside the identity by construction.
- Residue: `/var/tmp` 376 entries, 70 containers, current image list are the baselines the wrapper records; the
  repaired fixtures leave nothing (the worker-container fixture now removes its 65532-owned output through the same
  image, then its root), the engine gates own their containers and images.
- Hand back: `test-all.log`, `test-all.summary.json`, both `.source*.json`, the supervised run directory,
  `residue.txt`, `invocation-environment.txt`, `ACCOUNTING.md`; independent final accounting and review follow,
  then child/parent closure and the final check-in.
