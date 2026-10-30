# R2 remainder — consumed-input provenance (2026-10-30)

Author: K (interactive copilot `baton.prompt`), under owner-held arrangement B;
owner claim at `baton.decide` held by `baton.slaw` (episode E384905, read back
through `detail` before editing). Review answered:
`review-2026-10-30T03-09-45Z.md`, "R2 remaining — required out-of-scope
executable inputs are omitted (P2)". HEAD `afc71d71`. No Git mutation, no
engine, no live model, no full-suite run, no other agents.

## What was wrong

`test-all` identified a run by `HEAD` plus the bytes of changed files under
`v12/` only. The suite also executes, imports and reads files in Work records:
HEAD binds their committed versions, but an edited or untracked input at one
of those paths changed what a run tested without changing its identity. Two of
the seventeen are UNTRACKED today (`CAPABILITY.synthetic.json`,
`ROLE-CONTRACT.proposed.json` under the admission-plan dossier): HEAD bound
nothing of them at all.

## Correction

1. `tools/parallel_test.py`: `CONSUMED_INPUTS`, the declared files and import
   directories outside `v12/` the run consumes, each with its consumers;
   `consumed_inputs()` adds every supervised module's supervisor from
   `SUPERVISED_MODULES` (derived, not repeated). Declared as the smallest path
   actually consumed, never a whole dossier, so the evidence runs produce
   stays out.
2. `tools/source_identity.py`: `identity(repo, scopes, inputs)`; each declared
   input is enumerated with `git ls-files --cached` and `--others
   --exclude-standard` (tracked, modified and untracked files alike; ignored
   `__pycache__` beside an input excluded), every file hashed by content and
   rolled into `content_digest`. A declared input with no file, or a tracked
   file absent from the checkout, raises `MissingInput`; the CLI prints
   `source identity refused: …` on stderr, nothing on stdout, exit 2. CLI:
   `--input PATH` (repeatable) and `--declared`.
3. `justfile` `test-all`: both identity calls pass `--declared`; the pre-run
   refusal ends the recipe before any test (errexit + pipefail inside the
   header group, checked on a toy script); a post-run refusal fails the run
   with its own line. Header names `consumed-input-files`.
4. Tests. `tests/tools/test_source_identity.py` (+7 disposable-repository
   cases, +3 real-tree cases): a declared input is identified although git
   sees no change; editing it outside the scope changes the identity while
   the undeclared identity stays blind (the defect, asserted); a declared
   directory lists untracked files and not ignored ones; absent, wholly
   ignored, and tracked-but-deleted inputs refuse (library and CLI exit 2);
   `--declared` CLI agrees with the library on the real checkout and every
   declared input exists. `tests/tools/test_parallel_runner.py` (+3): an AST
   sweep of every record path spelled in `tests/` and `tools/` (string
   constants, `pathlib` `/` chains, `os.path.join`; docstrings skipped; paths
   shorter than `work/records/YYYY/MM/finding-x` are roots, not inputs)
   requires each to be declared or listed in `SYNTHETIC_RECORD_PATHS` with a
   reason; stale synthetic entries fail; the sweep's three spellings and
   prose-skipping are tested on a probe file; each declared entry names
   consumers, exists, and is not a whole dossier.
5. `TESTING.md` §6 (declare what you read outside `v12/`) and §9 (the two-part
   boundary, the refusal, the limitations).

## The declaration (17 paths → 32 files; 30 tracked, 2 untracked)

See `source-identity-declared.json` (`inputs`, `consumed`). Summary:

| consumed | by |
|---|---|
| `…/finding-v12-runtime-deadline-cleanup/engine-gate.py` (derived) | supervisor; test_runtime_deadline_engine |
| `…/instance-201492/context/worker/` (12 files), `…/context/Dockerfile.fixture` | test_importing_fixture, test_fixture_dispatch |
| `…/instance-201492/verify_lifecycle.py`, `compose_lifecycle.py` | test_w197661_verifier |
| `…/instance-200564/context/worker/` (5 files), `bootstrap_inputs.json`, `install_inputs.json`, `task.json` | test_proposing_fixture, test_importing_fixture |
| `…/finding-v12-single-implementation-proof/baseline.py` | shutdown_fixture, test_authoring_enforcement, test_authoring_manager_guard |
| `…/finding-template-adapter-admission-plan/CAPABILITY.synthetic.json`, `ROLE-CONTRACT.proposed.json` (untracked) | test_role_capability, test_role_contract |
| `…/finding-worker-control-api-manifests/evidence/vectors.json` | verification_fixtures and ~15 manifest/workspace/secrets/image/container/output/driver cases |
| `…/finding-worker-control-api-manifests/schema/worker-control-1.0.schema.json`, `…/finding-acp-agent-boundary/schema/agent-session-1.0.schema.json` | test_frozen |
| `…/finding-v12-assignment-state-machine/evidence/test_assignment_state_model.py` | test_catalog |
| `…/finding-v12-deterministic-scheduler-stress/trace-160959-composed.json` | test_correction_restart |

The review named two inputs; the sweep found the rest. Synthetic literals
(not read from this checkout): the runner's locator grammar; the dossier
cases' reference created in their own temporary repository; the disposition
cases' `finding-pilot` temporary repository (5 paths); the dogfood operator's
synthetic contract (2); this module's fake supervisor entries (2).

## Verification (measured)

`just test-one tests.tools.test_source_identity tests.tools.test_parallel_runner`
→ 88 tests OK in 16.4 s (log: `test-one-source-identity-parallel-runner.log`;
75 before this correction, 13 added). Authoring took four focused iterations
(~16.5 s each): the first found the sweep reading its own probe literal, the
second my own new prefix assertions (`"work/records/"`), which produced the
depth rule, the third dropped the three synthetic entries that rule made
stale. Groups affected: `tools-pure` only.

Refusal demonstrated on the real checkout with one absent declared input:
`refusal.stdout` is empty, `refusal.stderr` carries the refusal, exit 2.
Current declared identity of this checkout: `source-identity-declared.json`
(`changed` 48 files under `v12/`, `consumed` 32). Candidate bytes:
`CANDIDATE-SHA256.txt` (six paths).

## Observations outside this correction (not changed)

- `test_importing_fixture`, `test_fixture_dispatch`, `test_proposing_fixture`
  and `test_w197661_verifier` name the checkout by the absolute path
  `/home/sl/src/baton`, not relative to themselves. The identity hashes the
  repository-relative inputs; the two coincide only while this checkout is
  the one they name. Recorded as a TESTING.md limitation; fixing the fixtures
  is outside R2.
- The sweep reads paths spelled in code; a record reached through a computed
  path would have to be declared by hand (TESTING.md §9).
- `test_proposing_fixture` skips a case when `instance-200564/task.json` is
  absent; the file is present and now declared, so its absence would refuse
  the run before producing a required skip.
