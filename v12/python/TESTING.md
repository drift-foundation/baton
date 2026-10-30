# Testing the v12 Python distribution

This is the durable guide to running, selecting and accounting the v12 Python
test suite. Following it is required for anyone doing v12 test work (see the
repository `AGENTS.md`, "V12 test execution policy"). It describes what the
runner and the `justfile` actually do today; limitations are named as such.
Transient Work ids, current failure counts and run history live in the owning
Work dossier, not here.

## 1. Where to run

Every command below is run from this directory, `v12/python`, or names this
`justfile` explicitly from anywhere:

```sh
cd /path/to/baton/v12/python
just test-group authority
# or, from anywhere in the checkout:
just --justfile v12/python/justfile test-group authority
```

The recipes `cd` to the justfile's directory themselves; the working directory
matters only for the relative paths you type.

## 2. Prepared environment and prerequisites

All three test entries run on the PREPARED interpreter, never the ambient one.
Prepare it once from `v12/` with `just setup` (see `v12/justfile`); the
recipes resolve it through `python3 -m tools.environment interpreter` and
refuse when it is missing. The prepared environment installs the exact
hash-locked `requirements.lock`, so the validator the tests exercise is the one
the distribution pins (an ambient `jsonschema` of another version is exactly
the kind of silent drift this avoids).

Prerequisites by what you run:

| need | for | how it is checked |
|---|---|---|
| Python ≥ 3.13 | everything | the prepared environment refuses otherwise |
| `just`, `git` | tools groups | tests that drive them resolve them on `PATH` |
| Docker daemon reachable by this user | `manager-engine` group, supervised group | engine fixtures ask the daemon; a required engine gate FAILS when it cannot run, it does not skip |
| a built bundle (`just build` from `v12/`) | `tools-packaged` group | `test-all` builds one unless `BATON_V12_STACK_DISTRO` names one, and sets `BATON_V12_STACK_PACKAGING_REQUIRED=1` so absence fails |
| `BATON_W32577_IMAGE_DIGEST=sha256:…` the reviewed, preloaded reference-worker image | supervised group, `test-all` | refused when unset |
| `BATON_V12_INITIAL_ACCESS_ENGINE=1`, `BATON_V12_PRIVATE_LINE_IMAGE=sha256:…`, `BATON_V12_WORKSPACE_GROUP=<gid>` | the four initial-access engine cases (`tests.manager.test_private_line_access_engine`) | the cases skip when the first is unset and assert the other two; they are REQUIRED coverage, so a skip there fails an accounted run |
| real (non-tmpfs) storage | workspace fixtures | `BATON_V12_DISK_ROOT` names it; otherwise `$TMPDIR`, then `/var/tmp`, then this checkout are tried |

Limitation: `test-all` does not set the initial-access variables for you. Until
the operator-prepared image and workspace group exist, an accounted full run
reports those four cases as required skips and fails; that is the intended
truthful outcome, not a harness bug.

## 3. The three entries

Argument order is positional as shown; `JOBS` always comes last and may be
omitted (every available CPU) or lowered, never raised above the host's count.

```sh
# one or more exact unittest ids (package.module[.Class[.method]])
just test-one tests.manager.test_launch
just test-one tests.manager.test_launch.TheContextLaunchIsClosed.test_owner_launch_and_worker_reader_agree

# one logical group, with exact accounting
just test-group manager-pure
just test-group manager-pure 8          # lower the worker count to 8

# THE full supported run, with a retained log (absolute path, not under /tmp)
BATON_W32577_IMAGE_DIGEST=sha256:… just test-all /abs/path/evidence/test-all.log
BATON_W32577_IMAGE_DIGEST=sha256:… just test-all /abs/path/evidence/test-all.log 16
```

`test-one` is plain `unittest -v` on the prepared interpreter: no accounting,
no registry check, useful while editing one module. `test-group` and `test-all`
go through `tools/parallel_test.py` with `--account`.

The older recipes remain: `just test` is the reference serial
`unittest discover` (no accounting, no partition; it is NOT the gate), and
`just parallel-test` is the unaccounted parallel runner.

## 4. Logical groups versus execution shards

Groups are what you SELECT and declare; shards are how the runner EXECUTES.

The nine groups form an exact partition of the test modules, encoded once in
`tools/parallel_test.py` (`GROUP_MODULES`, `GROUP_PACKAGES`, `GROUPS`) and
checked mechanically before every run:

| group | contents |
|---|---|
| `authority` | `tests/authority` |
| `job_manager` | `tests/job_manager` |
| `integration` | `tests/integration` |
| `manager-pure` | `tests/manager` except the three carved groups below |
| `manager-engine` | the serial Docker engine gates (builds images, starts containers) |
| `scans` | the whole-universe inventories: boundary_inventory, dependencies, contracts_inventory, text_sweep, source_boundary |
| `tools-pure` | `tests/tools` except `tools-packaged` and the two dogfood engine gates (which are in `manager-engine`) |
| `tools-packaged` | test_packaging, test_packaged_creation: examine a BUILT bundle |
| `supervised` | test_runtime_deadline_engine, run only through its reviewed supervisor |

Execution registries are separate and also complete: every module is in exactly
one of PARALLEL_MODULES, SERIAL_MODULES or SUPERVISED_MODULES. A module in no
registry, in two, or in no group refuses the whole run before any test starts.

Shards: a parallel module is split one shard per concrete `TestCase` class
(two inventory classes are split one method per shard, `METHOD_SPLIT`); every
shard is a fresh interpreter. A serial module is one shard, run alone after the
parallel phase, in registry order. The supervised module is run by its
supervisor script as one step. Shard results are presented in sorted order, so
stdout does not depend on completion order.

## 5. Parallel, serial, packaged and supervised behaviour

- Parallel modules must own nothing shared: no daemon, no image build, no
  fixed port, no shared name. Class fixtures stay within their class shard.
- Serial modules own the Docker daemon, built images and suite-global names;
  they run one at a time and never beside the parallel phase. If the parallel
  phase fails, the serial phase does not run unless `--keep-going` is passed
  (`test-all` and `test-group` pass it, so the accounting is complete).
- Packaged cases examine the bundle at `build/out/distro` or
  `BATON_V12_STACK_DISTRO`. With `BATON_V12_STACK_PACKAGING_REQUIRED=1` an
  absent bundle fails instead of skipping; `test-all` sets it.
- The supervised module is never selected as an ordinary shard. `test-all`
  (and `test-group supervised`) run its reviewed supervisor with the prepared
  interpreter; the supervisor owns the body and the container cleanup, and the
  module's ids count as executed only when the supervisor exits 0 and its body
  ran every one of them to OK. The run directory is kept beside the log.
- Isolation: a shard's stderr goes to its own file; children run in their own
  session so an interrupt reaps what they started; the result root is
  disposable and removed at the end.

## 6. Adding tests and keeping coverage complete

A new test module must be added to exactly one execution registry in
`tools/parallel_test.py` (parallel unless it owns an engine or a shared
resource) and will then fall into its group by package, unless you also carve
it into `GROUP_MODULES`. The runner refuses an unregistered module; the
regressions in `tests/tools/test_parallel_runner.py` check the real tree.

Do not bind another module's `TestCase` classes in your module's namespace
(`from tests.x.test_y import SomeCase`): `unittest` would collect them twice
and the collector refuses the binding module by name. Import the module and
reach the class as an attribute.

Fixtures that need real storage use `tests/manager/disk_roots.py`, which never
puts a workspace on a tmpfs. Clean up what you create; a case interrupted
mid-run leaves its root behind under the first disk-backed candidate.

A test that executes, imports or reads a file OUTSIDE `v12/` (a captured image
context in a Work record, a proposed contract, a manifest vector) declares that
file or import directory in `CONSUMED_INPUTS` in `tools/parallel_test.py`,
with its consumers. The declaration is part of the run's source identity
(section 9). `tests/tools/test_parallel_runner.py` sweeps the tree for record
paths spelled in code and fails when one is neither declared nor listed as
synthetic there; declare the smallest path actually consumed, never a whole
dossier, because dossiers also hold the evidence runs produce.

## 7. Required versus optional skips

Every test is REQUIRED unless its exact id (or, for a class-level skip, the
fixture event id `setUpClass (pkg.module.Class)`) is listed in
`OPTIONAL_SKIPS` in `tools/parallel_test.py` with the owner's reason. An
accounted run prints every skip: `[optional skip]` for the registry's entries
and `[REQUIRED SKIP]` / `[FIXTURE SKIP]` for everything else, and the latter
fail the run. Do not add entries to `OPTIONAL_SKIPS` without an owner ruling
recorded in the owning Work.

## 8. Accounting: what "passed" means

`--account` (always on in `test-group` and `test-all`) proves the run against
the ids the tree declares:

1. Collection in child interpreters produces the expected set E over the
   selected registries (parallel, serial and supervised alike).
2. Every shard reports the ids that actually STARTED (recorded by the test
   result as each test begins), plus its failures, errors, skips, expected
   failures and unexpected successes. A class whose `setUpClass` skips or
   errors starts none of its tests; those appear as `[FIXTURE SKIP]` /
   `[FIXTURE ERROR]` and their tests as `[UNACCOUNTED]`.
3. `passed` is DERIVED: started ids minus every id with another outcome.
4. The run is OK only when
   `passed + optional skipped = collected` with zero failures, errors,
   fixture skips, fixture errors, duplicates, unaccounted or uncollected ids.

The last two lines of an accounted run are the counts and the verdict:

```
collected N, executed X, passed P, optional skipped K, required skipped R, failed F, errors E, fixture skips S, fixture errors G, duplicates D, unaccounted U
[accounting] passed P + optional skipped K = P+K of collected N -> OK|FAILED
```

Non-zero exit: 1 for any failing condition above or a failed phase, 2 for a
refusal (registry, group or collection problem; nothing ran), 128+signal when
interrupted.

Limitation: subtests report under their test's id; a test with one failing
subtest counts as one failed id.

## 9. Retained evidence and source identity

`test-all` writes the log you name (refusing a path under `/tmp`), a JSON
ledger beside it (`<log without .log>.summary.json`: every id by outcome, the
per-group counts and the phase summaries), the supervised run directory in the
same folder, and two source-identity documents.

The source identity is CONTENT-BOUND (`tools/source_identity.py`) and has two
parts, both rolled into one `content-digest` with `HEAD`:

- The SCOPE `v12/`: the SHA-256 of the bytes of every modified, added,
  deleted, renamed or untracked file under it. Two candidates with identical
  `git status` text and different bytes have different digests. Gitignored
  paths (so `v12/python/build/` and other generated outputs) are excluded.
- The DECLARED CONSUMED INPUTS (`--declared`: `CONSUMED_INPUTS` in
  `tools/parallel_test.py` plus each supervised module's supervisor): the
  files outside `v12/` that the run executes, imports or reads — the reviewed
  `engine-gate.py` supervisor, the captured image contexts a fixture puts on
  its import path, the proposed role contracts, the manifest vectors and
  schemas, a pinned scheduler trace. Every non-ignored file of each declared
  path is hashed WHETHER OR NOT git considers it changed, because `HEAD` binds
  only the committed version and an edited or untracked input would otherwise
  change what the run tested without changing its identity. A declared input
  that is absent in the checkout, or wholly gitignored, REFUSES the identity
  (exit 2) and so refuses the run before any test starts; after the run the
  same refusal fails it.

Everything else outside `v12/` — the Work records where a run's own evidence
lands, build outputs, `__pycache__` beside an input — is outside the identity
by construction. The per-file lists (`changed` and `consumed`, each file with
its digest and whether git tracks it) are in `<log>.source.json`; the identity
is taken again after the run into `<log>.source-after.json`, and a run whose
tested bytes changed under it reports `SOURCE DRIFT` and fails, because it no
longer identifies one candidate.

The log header also records the interpreter and validator versions, the Docker
server version, uid, CPU count, user-namespace capability, whether `/tmp` is
tmpfs, and the selected image and bundle. Keep the log, the ledger, the two
source documents and the header together; a passed count without its collected
count and content-bound source identity is not evidence.

Limitations: the identity covers files git can see under `v12/` and the
declared inputs; a dependency installed in the prepared environment is
identified by the lock the environment was installed from (`just setup`
records it), not by this digest. The declaration is checked against record
paths spelled in test code (section 6); a test that reaches a record through
a computed path would need to declare it by hand. Several fixture modules
name this checkout by its absolute path rather than relative to themselves;
the identity hashes the repository-relative paths, which coincide only while
the checkout is the one those modules name.

## 10. When a full run needs a selected checkpoint

Routine work verifies with `test-one` and `test-group` on the groups it
declares. A full `test-all` is an integration checkpoint: it is run when the
owning Work explicitly selects one, its log is retained in that Work's
evidence, and a retry after a fix is a NEW selected checkpoint, not an
automatic rerun. Declare the affected groups in the handoff and run only those.
