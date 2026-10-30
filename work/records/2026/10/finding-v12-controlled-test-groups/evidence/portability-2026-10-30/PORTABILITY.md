# Checkout portability correction (owner ruling 2026-10-30)

Author: K (interactive copilot `baton.prompt`), owner-held arrangement B; owner
claim E384905 (`baton.slaw`). HEAD `84f66f43`. Answers the owner's ruling
pinned in FINDING ("Owner requires checkout portability; personal home paths
are not prerequisites") and PLAN top. No Git mutation, engine, live model,
full-suite run or other agent.

## What was executable about `/home/sl`

Audit of every `/home/sl` literal under `v12/python/tests`, `tools`, `src`,
`v12/worker`, `v12/testing` and the declared consumed inputs, classified by
whether it is READ at run time:

| literal | classification |
|---|---|
| `REPO = "/home/sl/src/baton"` in test_proposing_fixture, test_fixture_dispatch, test_importing_fixture, test_w197661_verifier, test_attempt_logs | runtime: import paths and record reads resolved against it → FIXED |
| `pathlib.Path("/home/sl/src/baton/v12/python/src/baton_v12")` in test_claude_agent (import-boundary AST read) | runtime read → FIXED |
| `REPO = Path("/home/sl/src/baton")` in the consumed helpers instance-201492/verify_lifecycle.py and compose_lifecycle.py (sys.path inserts, oci.py digest) | runtime, consumed by test_w197661_verifier → FIXED (two lines each) |
| `DEST = Path("/home/sl/baton-v12-lifecycle-201492-run4")` in the same helpers | the retained live instance the episode verified: an external resource, guarded by `is_file()/is_dir()`, absent on this host, not read by any test → left, commented |
| `instance-200564/bootstrap_inputs.json`, `install_inputs.json` paths | historical captured documents; the test asserts a member's absence, never follows the paths → data |
| test_custody 526/1372, test_verification_context `HOSTILE` | deliberately hostile/wrong path literals → data |
| test_stage_execution:71, test_custody:75, test_worker_container:1122 | docstrings → prose |
| test_live_ab:45 and `v12/testing/live_ab/deployment.py` `REGISTRY = '/home/sl/.baton/credential-sources.json'` | the live A/B deployment composer's operator registry default; the test compares the composed document's text, nothing is read → not a fixture dependency. OBSERVATION for the owner: a live-tool default naming an operator's home, outside this correction (live tooling, no live run selected) |
| `os.environ['HOME']` uses in next_run_flow_fixture / correction_restart_trace | the process's own HOME (set per test), not the owner's → fine |

## The fix

- Six test modules: `REPO = str(pathlib.Path(__file__).resolve().parents[4])`
  (the checkout under test; `import pathlib` added where absent);
  test_claude_agent reads `parents[2] / "src" / "baton_v12"`.
- Two consumed helpers: `REPO = Path(__file__).resolve().parents[6]` (the
  checkout the record lives in); `DEST` unchanged and documented as external.
  These are two-line executable fixes in record files that the suite imports,
  not a rewrite of evidence; everything else in the dossier is untouched.
- `tools/parallel_test.py` CONSUMED_INPUTS, corrected by the relocation runs
  (below): the two captured image contexts are declared WHOLE
  (`instance-*/context`: Dockerfile.fixture, worker/, and the
  `python/src/baton_v12/source_profiles` COPY source the recipe checks), and
  the verifier's four beside-itself reads are declared
  (`CAPTURED-records.json`, `CAPTURED-terminal.json`, `EXPECTED.json`,
  `build/fixture.iid`). 17 → 20 declared paths, 32 → 41 files; the AST sweep,
  the real-tree check and the identity tests pass (88 OK,
  declaration-tests.log).
- `TESTING.md` §9: the host-path limitation replaced by the verified rule.

## Verification (measured)

Affected modules: tests.manager.{test_proposing_fixture, test_fixture_dispatch,
test_importing_fixture, test_w197661_verifier, test_attempt_logs,
test_claude_agent}; group `manager-pure`.

1. Original checkout: `just test-one <six>` → 727 OK, 18.3 s
   (original-checkout-focused.log).
2. Relocation, attempt 1 (attempt-1-partial-copy-focused.log): a copy at
   `/var/tmp/baton-portability-20261030/other-checkout` holding `v12/` and the
   whole launch-mismatch dossier (build/ excluded) → 723/727: two errors were
   `vectors.json` absent (a declared input I had not copied — the declaration
   predicted the need) and two failures were `instance-201492/build/fixture.iid`
   absent (an UNDECLARED read by `verify_lifecycle.classify_provenance`). One
   `stat` of `/home/sl/src/baton` in the trace, by the recipe's bash honouring
   the INHERITED `OLDPWD` of my shell, not by any test.
3. Relocation, strict (strict-checkout-focused.log, strict-copy-inputs.txt):
   a copy holding ONLY `v12/` (minus `python/build`, `__pycache__`) and the
   declared inputs (`rsync -aR -r --files-from=<consumed_inputs()>`), run with
   `env -u OLDPWD -u PWD` under `strace -f -e trace=%file`. Two intermediate
   strict runs found the two context gaps above (ModuleNotFoundError for the
   copied-but-not-recursed import path was my rsync mistake; the missing
   `source_profiles` COPY source was a real gap). Final: 727 OK, 31.4 s, and
   `grep -c /home/sl/src/baton` over the trace = 0. The only `/home/sl` paths
   touched are the prepared interpreter under `~/.local/state/baton-v12-venv`
   (XDG state, where `tools/environment.py` puts it), `~/.local/bin` and `~/.nvm` tool
   binaries on PATH, `~/.gitconfig` (the fixtures' own `git` on temp repos) and
   tool caches (strace-summary.txt).

Raw traces (~95 MB each) were summarised and removed as reproducible; the
scratch copy under `/var/tmp/baton-portability-20261030` was removed.

Reproduction: from `v12/python`, `python -c 'from tools.parallel_test import
consumed_inputs; print("\n".join(consumed_inputs()))' > inputs.txt`; `rsync -a
--exclude __pycache__ --exclude /python/build v12/ COPY/v12/`; `rsync -aR -r
--files-from=inputs.txt REPO/ COPY/`; then from `COPY/v12/python`:
`env -u OLDPWD -u PWD strace -f -qq -o trace -e trace=%file just test-one <six>`
and `grep -c REPO trace`.

## Not changed

The `unshare` bind-hide approach was unavailable inside this session's sandbox
(uid_map not permitted); strace observation stands in. `REGISTRY` in the live
A/B composer is reported, not changed. Candidate bytes: CANDIDATE-SHA256.txt.
