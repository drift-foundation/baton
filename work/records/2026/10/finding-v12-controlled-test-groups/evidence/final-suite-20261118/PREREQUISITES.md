# Final accounted full suite — owner-run command and prerequisites (M385110)

Prepared by K (copilot, no claim) on 2026-11-18 after owner checkpoint `e80f2c8e`. PREPARATION ONLY: nothing
here was executed except the read-only `preflight.sh` (`preflight-20261118T07.txt`: 8 ok, 0 failing). Slawomir
runs the suite; it is the integration checkpoint W384870 selects (TESTING.md §3, §9, §10; AGENTS "V12 test
execution policy").

## What the run is

`just test-all LOG [JOBS]` from `v12/` (forwards to `v12/python/justfile` `test-all`): `tools/parallel_test.py
--phase all --with-supervised --account --keep-going --summary LOG.summary.json --retain <dir of LOG>` on the
prepared interpreter, with the content-bound source identity taken before and after. It writes beside LOG:
`test-all.summary.json` (ledger: every id by outcome), `test-all.source.json`, `test-all.source-after.json`, and
the supervised run directory. Exit 0 only when `passed + optional skipped = collected` with zero
failed/errors/fixture/duplicate/unaccounted/uncollected ids and no source drift. It BUILDS a fresh bundle first
(PyInstaller, `just build`) unless `BATON_V12_STACK_DISTRO` names one; B0 (2026-10-29) did the same.

## Prerequisites (all verified present by `preflight.sh` on 2026-11-18T07Z)

| need | value on this host | source |
|---|---|---|
| committed candidate, clean `v12/` | HEAD `e80f2c8e`, 0 status lines under v12 | owner checkpoint |
| prepared interpreter | `/home/sl/.local/state/baton-v12-venv/bin/python` (3.13.7, jsonschema 4.26.0) | `python3 -m tools.environment interpreter` |
| `just`, `git`, Docker daemon | present; Docker 29.1.3 | TESTING §2 |
| `BATON_W32577_IMAGE_DIGEST` reference worker image, preloaded | `sha256:9b8c98820877e33d38d33352d86cc3810e5b72d4935a181b82b512b4d3291de8` (present; B0 and B4 used it) | TESTING §2; supervised gate never pulls |
| `BATON_V12_INITIAL_ACCESS_ENGINE=1`, `BATON_V12_PRIVATE_LINE_IMAGE`, `BATON_V12_WORKSPACE_GROUP` | `1`, `sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4` (present), `1001` (`baton-workspace`, caller is a member) | accepted B4 joined run `findings/finding-b4-docker-readiness/evidence/joined-b4-resume-20261118/05/invocation.json` |
| disk-backed storage | `TMPDIR=/var/tmp BATON_V12_DISK_ROOT=/var/tmp` (ext4, 577 G free; `/tmp` is tmpfs) | TESTING §2; every K run used this |
| bundle | none selected: fresh build (default) | TESTING §2, §5 |
| optional engine image selection (`BATON_V12_{INPUT_DELIVERY,WORKER_ENTRY,CUSTODY,LIFECYCLE}_IMAGE`) | LEAVE UNSET: B4's `sha256:4da24074…` is no longer present locally; unset means the engine modules build their own, as designed | B4 evidence; `docker image inspect` 2026-11-18 |
| `BATON_V12_LARGE_WORKSPACE_PROOF` | unset: the >64 MiB workspace proof stays an OPTIONAL registry skip, as in the accepted scans run | `OPTIONAL_SKIPS` |

Without the three initial-access variables the four `test_private_line_access_engine` cases are REQUIRED skips and
the accounted run fails truthfully (TESTING §2 limitation); the wrapper exports them.

## Exact commands

Read-only preflight (repeatable):
```sh
/home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118/preflight.sh
```

The run (one command; `JOBS` optional, e.g. `16`; omitted = all 32 CPUs as B0 did):
```sh
/home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118/run-final-suite.sh
```
It is exactly, after the exports above and `/var/tmp` + `docker ps -a` + `docker images` listings before:
```sh
cd /home/sl/src/baton/v12 && just test-all /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118/test-all.log
```
then the same listings after and `residue.txt`. The bare recipe can be run instead; the wrapper adds only the
residue accounting and `invocation-environment.txt`.

Accounting afterwards (reads the ledger only):
```sh
python3 -I /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118/summarize.py /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118/test-all.summary.json > /home/sl/src/baton/work/records/2026/10/finding-v12-controlled-test-groups/evidence/final-suite-20261118/ACCOUNTING.md
```

## Expectations and boundaries

- Duration: B0 ran 11 136 tests in 1 335 s at 32 workers plus the bundle build and serial engine phase (whole
  recipe 2026-10-29 23:39Z to 23:45Z was the FAILED attempt; the five non-engine groups alone took 271 s at 8
  workers on 2026-11-18; B4's engine selections took minutes). Expect roughly 15-40 minutes; the recipe has no
  timeout of its own, and a retry after any fix is a NEW selected checkpoint (TESTING §10), not an automatic rerun.
- Do not change `HEAD` or any file under `v12/` while it runs: the identity is re-taken afterwards and drift fails the
  run. Work records (this directory) are outside the identity by construction.
- Current optional skips in the registry (expected to appear as `optional skipped 2`): the same-filesystem bind-mount
  case (no user namespace on this host) and the large-workspace proof.
- Residue: `/var/tmp` 376 entries and 70 pre-existing containers (1 running: `mdb114-a`, unrelated) are the
  baselines the wrapper records; the repaired fixtures leave nothing, the engine gates own their containers and
  images.
- Hand back: `test-all.log`, `test-all.summary.json`, both `.source*.json`, the supervised run directory,
  `residue.txt`, `invocation-environment.txt`, `ACCOUNTING.md`; independent final accounting and review follow.

## Coordinator preparation review

Checkpoint e80f2c8e confirmed. Wrapper now refuses existing run evidence, invokes preflight before execution, records only an explicit test-setting allowlist, and quotes the optional worker argument. Preflight now enforces the selected clean checkpoint, workspace group membership and unset optional image/bundle/large-proof overrides. No tests were executed during this review. Run the wrapper once; do not delete evidence to retry.
