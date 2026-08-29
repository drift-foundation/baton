# Progress

## 2026-08-29 — `baton.claude`, implementation claim on W38956

State: **plan item 3 delivered and awaiting review.** Items 4 to 8 are not
started. The Work is passed back rather than closed, and this entry is the
account of what a reviewer is being handed.

### What was revalidated first, and what it changed

The whole record was read fresh and every pinned claim re-checked against the
tree before anything was written. Items 1 and 2 hold exactly as recorded. Three
facts the earlier revalidation had not reached were found, and all three are
written into `FINDING.md` under *Implementation revalidation — 2026-08-29*
rather than being acted on from this file:

1. **The accepted start vector cannot carry a worker-entry conversation, and
   `docker attach` cannot repair it.** Measured against the development host's
   daemon rather than reasoned about:
   `evidence/w38956-transport-probe.py` and its recorded
   `evidence/w38956-transport-probe.txt`. With `run --detach --interactive`,
   the attaching client closing its stdin does not close the worker's — the
   probe records the container still running after the transport gave up — so
   a conversation driven that way could only ever be ended by killing the
   container, and a session ended by a signal is not a worker that finished.
   `docker exec --interactive` propagates EOF, ends with the worker's own
   status, keeps stdout and stderr apart, and inherits the container's
   `--group-add` (measured: `uid=65532 gid=65532 groups=65532,<workspace
   gid>`, and it wrote the bound `/output`). That is the pinned transport; the
   rejected `create` + `start --attach` alternative is recorded with its
   reason.
2. **`--network none` is unconditional, so no runtime this manager starts can
   reach a provider.** W17110 ran a real Claude CLI with network through the
   SPIKE's own Docker lifecycle, never through this adapter. This is a blocker
   of the kind the finding says stays in W38956: with the restriction as
   written, the milestone's own positive case cannot happen. The posture is now
   one explicit operand, defaulted closed. **Which value the first live trial
   names is an approver decision and is not taken here.**
3. **The v12 authority `Session` carries six of `AuthorityPort`'s seven
   operations.** `publish_answer` publishes into Baton, which is a different
   system, so the deployment composes it. Not a defect and no Baton finding is
   owed; recorded as a pinned decision for the operator entry point.

### What was implemented

- `v12/python/src/baton_v12/worker_manager/worker_entry.py` — the transport.
  A closed three-valued ending (`answered`, `faulted`, `lost`), correlation
  checked before any payload is read, closed answer member sets, bounded frames
  and header, bounded worker stderr, and the channel as an injected capability
  like every other outward act in this package. Transport loss never becomes an
  agent answer, and complete answers followed by an unclean session ending are
  `lost` rather than `answered`.
- `v12/python/src/baton_v12/worker_manager/oci.py` — `exec_vector`; the
  `interactive` start operand (default off, so every accepted case over the
  detached reference worker keeps its exact meaning); and the `network` operand
  substituted at the one `RESTRICTIONS` entry rather than appended beside it,
  so there is exactly one `--network` in any vector and a caller that names
  nothing still gets `none`.
- `v12/python/tests/manager/test_worker_entry.py` — 45 cases, registered in
  `tools/parallel_test.py`'s parallel phase.

### Why the positive cases do not use a fake worker

They run `baton_worker.serve` in a thread over a real pipe pair, so the green
cases are the manager's transport and the image's own program actually meeting
— two implementations of one contract, one of which cannot import the other.
W6636's recorded defect was precisely two closed components that turned out not
to be able to meet, and a hand-written fake peer would have agreed with
whatever the transport did. One case additionally holds the manager's copy of
the worker's closed answer sets, ceilings and protocol name against the
worker's own literals, because two copies of one contract agree until they
don't. The negatives use a composed peer, since a healthy worker cannot produce
a truncated frame or a foreign session.

### Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_entry
    -> 45 tests, OK

    PYTHONPATH=src python3 -m unittest tests.manager.test_oci \
        tests.manager.test_attempts tests.manager.test_worker_image \
        tests.manager.test_launch tests.manager.test_credentials \
        tests.manager.test_intake tests.manager.test_sealing \
        tests.manager.test_output tests.manager.test_workspaces \
        tests.manager.test_offers tests.manager.test_sessions
    -> 927 tests, OK

    PYTHONPATH=src python3 -m unittest tests.tools.test_parallel_runner
    -> 36 tests, OK

**The daemon gates were NOT run.** `test_worker_container` and
`test_lifecycle_composition` build images and drive a real engine, and the
parallel runner stops before its serial phase when the parallel phase fails —
which it does, on failures that are not this Work's (below). They are owed
before item 3 can be called proved against an engine as well as against the
image's program.

### Pre-existing failures in this tree, and they are not this Work's

`python3 tools/parallel_test.py` on the tree as claimed, BEFORE any change
here: 1992 tests, **6 failures**, in
`tests.manager.test_boundary_inventory` (5) and
`tests.manager.test_custody.OneMountAndNothingElse` (1). They belong to the
in-flight custody, workspace and authority edits already present in the working
tree — `finding-v12-worker-custody-provider` and the W29400 label work — and
the finding's own patch boundary says to avoid those files. They are reported,
not touched.

### Owed, and named rather than quietly left

Three boundary entries this change introduces have no owner in
`tests/manager/test_boundary_inventory.py`. They are listed in `PLAN.md` with
the reason they were not added: that registry is already failing on 29 entries
that predate this Work, and the file carries another participant's uncommitted
edit. Establishing ownership before editing it is `AGENTS.md`'s own rule.

### State

Awaiting review. Not signed off, not closed. The Work is passed back with items
4 to 8 open, and with the network posture and the exact credential operand
named as operator/approver grants that gate the live trial regardless of how
far items 4 to 6 get.
