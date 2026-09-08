# Current source locator trace — 2026-09-07

Author: baton.tuner under W105706 claim event 105966. Read-only source evidence;
no real-runtime execution claim. `S` denotes configured workspace storage,
`A` an attempt id and `L` the durable line id.

| Operation | Actual subject | Source |
| --- | --- | --- |
| Ordinary allocation | `S/A/inputs`, `S/A/workspace`, precreated `S/A/workspace/result-A` | `worker_manager/workspaces.py:1268`, adoption at 1388/1420 |
| Line materialization | `S/.baton-review-lines/L/checkout`; only parents created mode 0700 | `worker_manager/review_cycles.py:374`, `create_line:515`; `checkpoint_profiles.py:128` |
| Writer roots | Inputs from `S/A/inputs`; workspace replaced with pinned line checkout | `worker_manager/workspaces.py:1914`, `review_cycles.py:1166` |
| Last launch access proof | Replacement workspace must have configured gid and exact mode 02770 | `worker_manager/oci.py:2019`, `workspaces.py:788` |
| Seal source | Declared relative paths below actual adapter workspace | `worker_manager/oci.py:2820`, `sealing.py:779` |
| Sealed artifact/receipt custody | Parent of actual workspace plus `custody/A`, hence `S/.baton-review-lines/L/custody/A` for a writer | `worker_manager/oci.py:2828`, `_home:2852` |
| Ordinary result normalization | `S/A/workspace/result-A` | `worker_manager/intake.py:1997`, `oci.py:2635`, `custody.py:618` |
| Ordinary workspace normalization | `S/A/workspace` | Same owners; no line/writer lookup in `_derived_root` |
| Ordinary cleanup deletion | `S/A/inputs` and `S/A/workspace`; excludes reserved line and sibling sealed custody | `worker_manager/intake.py:2531`, `workspaces.py:1961` |
| Read-only review | Line nominated as source; reviewer gets ordinary output roots | `worker_manager/review_cycles.py:1203` |

Source paths above are under `v12/python/src/baton_v12/`. Line numbers are
inspection aids; symbols and fingerprints identify the evidence.

`job_manager/review_driver.py:end_implementation` composes quiescence, freeze,
correlation, intake/retention, proposal publication, checkpoint freeze, then
cleanup. `review_cycles.freeze_checkpoint` revokes/fences before profile freeze,
but invokes no line normalization. `intake._normalized` runs at the later cleanup
point and resolves ordinary subjects. Normalizing those roots cannot grant
access to the persistent line. The independent correction is filed in
`baton:work/records/2026/09/finding-v12-private-line-custody-locators/`.

The initial-access proposal does not reroute custody or change this ending
sequence. Runtime-created restrictive modes and second-writer proof require
the separately accepted custody result.

## Read-only operational checks

- `docker version --format '{{.Server.Version}}'`: exit 0, `29.1.3`.
- Python inspection of `os.getuid()`, `os.getgid()`, `os.getgroups()` and only
  `BATON_V12_WORKSPACE_GROUP`: uid/gid 1000:1000; supplemental groups reported
  as eight entries of 65534 and one entry of 1000; group variable unset.
- `git status --short` and scoped `git diff --numstat`: existing modifications
  to `review_cycles.py`, `test_review_cycles.py` and the parallel registry.
  Planning changed none of them. No production baseline test was run.

Sources were located with `rg --files`/`rg -n` and read with `sed`/`cat`.
Initial guessed `worker_manager/checkpoint_profiles.py` and
`ending.py`/`endings.py` paths were absent; actual owners were then found and
read. Earlier dossier prose calling the resolver `_target` is stale naming;
the inspected function is `_derived_root`.

## Inspected SHA-256 fingerprints

These identify source evidence, not approved candidate bytes or Git provenance.

| Repository path | SHA-256 |
| --- | --- |
| `v12/python/src/baton_v12/worker_manager/workspaces.py` | `0726da10c7e677e35d47190f9bc6a29269e342332a617e1804e83c4709184097` |
| `v12/python/src/baton_v12/worker_manager/review_cycles.py` | `18431e40b4879d9b17e9b49ca0aedad256cbddaa6c44fca3d1c27c62fd50af06` |
| `v12/python/src/baton_v12/worker_manager/oci.py` | `d0e78475141a2cc7dd29a366dd50344a95e9942cbdfe34499fe0758aa4eb0409` |
| `v12/python/src/baton_v12/worker_manager/custody.py` | `86fbf3cd58e958b212e45efe569472b657428395a3e9a2169d73e3ddb324dbe0` |
| `v12/python/src/baton_v12/worker_manager/intake.py` | `be9bafa313b15e3a12d443fc7f704049b504b05835812e1e41ebcf391c5e99d9` |
| `v12/python/src/baton_v12/job_manager/review_driver.py` | `2290994750267c8a637a805fc408a3d6f745ec94aee102642282da1c1cd91029` |
| `v12/python/src/baton_v12/checkpoint_profiles.py` | `ba20b9288f4eab72c078472f725c5f021df6c6342a4445684156b2e6bbee5d38` |
| `v12/python/tests/manager/test_review_cycles.py` | `a20abe2cfb8b3e762490caec11cc418801b89f0a2ed8e1531f3685753a8c6dee` |
| `v12/python/tools/parallel_test.py` | `22c0cf0d39b6384326f866f76aceb5a4d422a0f02fa725e18b5dc12196456168` |
