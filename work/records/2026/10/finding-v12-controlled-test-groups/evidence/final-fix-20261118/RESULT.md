# Full-run remainder: fixture identity under a dedicated workspace group + two Docker cleanup sites (M385113, review 2026-11-18T07-13-25Z)

K, copilot under owner claim E384905, no claim held. Test-side only; no product byte changed. Candidate over
committed e80f2c8e: 4 files (+111/-5; `candidate.diff`, `CANDIDATE-SHA256.txt`): `tests/manager/test_maintenance.py`,
`tests/manager/test_attempts.py`, `tests/manager/test_worker_container.py`, `tests/tools/test_dogfood_arc_engine.py`.
Source identity (`tools.source_identity --declared v12`): HEAD e80f2c8e, changed 4, consumed 41, digest
`ae7eb489fe43b719949dbf5348735909a0e57c566903d78fb24c955a09b8c474`, identical before and after the batch
(`source.json`, `source-after.json`). Groups: manager-pure (maintenance, attempts), manager-engine
(worker_container, dogfood_arc_engine — focused Docker cases, as the review released; no group/full/scans/live).

## Cause, confirmed (24 maintenance ids + 2 attempts ids)

`MaintenanceCase.executed()` is the double for the maintenance CONTAINER: it runs the manager's own program as a host
subprocess. The product composes the container with `--user <uid>:<configured gid>` and validates the program's
truthful `running_as` against that declared identity (`maintenance._mismatch`). Under the full-run environment the
deployment configures `BATON_V12_WORKSPACE_GROUP=1001` while the process's primary gid is 1000, so the host child
truthfully reported `(1000, 1000)` against declared `[1000, 1001]`, and the manager correctly held every resource
("UNRESOLVED ... did not run as the identity that owns the worker's objects"); 22 failures and 2 maintenance errors
are that one effect and its consequences (no settlement row, `None` settlement). The two `test_attempts` errors:
`test_the_record_must_name_the_runtime_being_destroyed` re-ran `configure_workspace_group(store, os.getgid())` on a
store `AttemptCase.setUp` had already configured through `input_roots.configured_group` (1001), a reconfiguration the
product correctly refuses ("already configured with workspace group 1001 and is being told to use 1000"). Both are
environment-composition defects of the fixtures; the identity guards and the reconfiguration refusal are untouched.

## Changes

- `test_maintenance.py`: `MaintenanceCase.under_composed_identity(command, gid=None)`; `executed()` runs the program
  through it. When the configured gid is the process's primary gid (default) the command is unchanged; when it is a
  supplementary group of the process, the command is `sg <group> -c <shlex-joined command>` so the child's primary
  group IS the configured one and its `running_as` is the real program's own under the composed identity; a group
  the process cannot adopt is an `AssertionError` naming the gid and the fix (set the variable to a provisioned group
  the process belongs to, or unset it) — never a faked `running_as`. New class `TheDoubleRunsTheProgramAsTheDeclaredIdentity`
  (4 cases): the real program's account equals `self.identity()` and its gid equals the configured group under whatever
  group this run selects; unchanged command for the primary group; a member group is adopted through `sg` and a
  child really reports that gid; a non-member gid is refused. The existing wrong-identity witness
  (`running_as` mutated → UNRESOLVED) is unchanged.
- `test_attempts.py`: the redundant `configure_workspace_group(self.store, os.getgid())` line is removed with a comment;
  the case still proves the sibling-runtime refusal. The product's no-reconfiguration refusal keeps its own coverage.
- `test_worker_container.py`: `ContainerCase.remove_roots(home, outputs)` replaces `rmtree(ignore_errors)` in `roots()`:
  if anything under the world-writable `/output` is owned by another uid (the image runs as 65532), the SAME image, under
  the gate's `restricted(...)` posture and identity, removes what it wrote (`--entrypoint /bin/sh -c 'rm -rf /output/* ...'`
  over the same bind mount); then `disk_roots.remove_owned_root(home)` removes the fixture's root and may not fail quietly.
- `test_dogfood_arc_engine.py`: `remove_owned_root(self.home)` for the frozen `storage/attempt-*` tree (sl-owned).

## Verification (`summary.tsv`, `per-run-listings/`: `/var/tmp`, container ids and image ids before/after each run)

| run | environment | result | time | new /var/tmp | new containers | new images |
|---|---|---|---|---|---|---|
| the 26 adverse ids | full-run (W32577 image, INITIAL_ACCESS_ENGINE=1, PRIVATE_LINE_IMAGE, WORKSPACE_GROUP=1001) | 26/26 OK | 0.7 s | 0 | 0 | 0 |
| tests.manager.test_maintenance (153 = 149 + 4 new) | full-run | OK | 4.0 s | 0 | 0 | 0 |
| tests.manager.test_attempts (431) | full-run | OK | 7.1 s | 0 | 0 | 0 |
| tests.manager.test_maintenance | default (group variables unset → gid 1000) | 153/153 OK | 3.9 s | 0 | 0 | 0 |
| tests.manager.test_attempts | default | 431/431 OK | 7.1 s | 0 | 0 | 0 |
| tests.manager.test_worker_container.RealContainersHoldTheTopology (real Docker, the class using `roots()`) | full-run | 27/27 OK | 6.1 s | 0 | 0 | 0 |
| tests.tools.test_dogfood_arc_engine (real Docker) | full-run | 2/2 OK | 1.0 s | 0 | 0 | 0 |

In the owner's full run the same two Docker classes left five `v12-worker-roots-*` and two `v12-w39358-arc-*` roots;
here both leave none. `/var/tmp` stayed at 383 (the 376 baseline + the seven full-run leftovers, see below) across every
run. Note: 27 tests with 22 `... ok` lines in the verbose log is unittest's rendering of docstring-bearing cases, not
a shortfall; `Ran 27 ... OK`.

## The seven leftover roots: inventoried, NOT removed by K

`evidence/final-suite-20261118/leftover-roots/inventory-before-removal.txt` preserves every entry's mode, uid:gid, size
and mtime (55 lines, 7 roots). Attribution: all seven are sl-owned `mkdtemp` roots with mtimes 07:08:10–07:09:31Z inside
the full run; the five worker roots hold `output/out` owned by uid 65532 (the worker image's user) with `result.txt`
or a symlink; the two arc roots hold sl-owned frozen `storage/attempt-*` trees. K's removal attempt was BLOCKED by the
agent harness's safety check (a container `sh -c 'rm -rf /output/*'`), and the check is not to be worked around; the
host user cannot unlink the 65532-owned content directly. Prepared instead: `leftover-roots/remove-leftover-roots.sh`
(check mode by default — run once: `check-mode-20261118T07.txt`; `--remove` acts on exactly those seven names: the
five `output/out` trees through `alpine:3.20 --user 65532:65532 --network none rm -rf /output/out`, then
`disk_roots.remove_owned_root` for all seven). `/var/tmp` is 383 until the owner runs it; the preserved full-run
directory is unchanged.

## Not done, per the ruling

No group/full retry; the next full run needs the owner checkpoint and a fresh evidence directory
(`run-final-suite.sh` refuses existing run evidence). Known remaining items: none from this batch.
