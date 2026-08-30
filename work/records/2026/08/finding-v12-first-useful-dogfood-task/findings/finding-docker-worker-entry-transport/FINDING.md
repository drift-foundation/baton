# Prove reusable Docker worker-entry control transport

Work: W39356
Parent: W38956
Discovery: the W38956 implementation episode returned a coherent transport
seed that must be reviewed and completed as its own checkpoint.

## Purpose

Provide one reusable, provider-neutral channel from the Python Worker Manager
to the worker-entry program in the exact already-started Docker runtime. This
checkpoint owns transport and framing only. It does not choose source, task,
provider, scheduling, settlement or operator policy.

## Seed delivered by the parent episode

The current working tree contains:

- `v12/python/src/baton_v12/worker_manager/worker_entry.py`;
- additions in `v12/python/src/baton_v12/worker_manager/oci.py` for
  `exec_vector`, an opt-in interactive start and a default-closed explicit
  network name;
- `v12/python/tests/manager/test_worker_entry.py`; and
- registration in `v12/python/tools/parallel_test.py`.

The parent evidence at
`../../evidence/w38956-transport-probe.{py,txt}` measured Docker 29.1.3:
`docker attach` did not propagate client EOF, while `docker exec
--interactive` did, kept stderr separate and inherited the configured
workspace supplementary group. The parent pins exec transport and records why
create/start-attach was rejected.

## Confirmed boundary

- The exec vector names the exact journalled runtime id and an image-owned
  closed program vector. It never starts, mounts, labels or schedules a second
  runtime.
- Frames and identities are bounded and correlated before payload use.
- Endings are closed: `answered`, `faulted`, or `lost`. Transport loss never
  becomes a worker answer or proof of runtime absence.
- The container start remains non-interactive and `--network none` by default.
  Interactive stdin and any other bounded engine network name are explicit
  deployment operands.
- Provider, source, proposal and operator decisions belong to later children.

## Independent-review questions

These are review targets, not accepted implementation facts:

- Confirm every new external operand refuses malformed container types rather
  than allowing Python iteration to reinterpret a scalar. In particular, a
  program supplied as one string must not become one argv word per character.
- Confirm surplus stdout after the final requested answer cannot escape the
  claimed closed-session rule merely because it was not already buffered when
  `trailing()` ran.
- Add direct coverage for explicit/default network composition, opt-in
  interactive start and their refusals; the delivered 45 cases exercise the
  conversation and exec vector but do not cover those new start operands.
- Establish ownership before adding the three owed boundary-inventory entries;
  that registry contains another participant's active changes.
- Run the real-engine worker-container and lifecycle composition gates after
  the shared baseline is green. Unit pipes do not prove Docker applies the
  vector.

## Acceptance

- The focused transport suite and existing OCI/manager regressions pass.
- Default construction preserves the accepted detached/no-network vector.
- Explicit interactive and network operands are bounded and regression-held.
- One real container completes a correlated worker-entry conversation through
  exec, returns its own status, preserves stderr separation and writes through
  the inherited workspace group.
- EOF, timeout, malformed/cross-session frames, unclean exit and channel-open
  failure remain non-success and do not imply runtime absence.
- The three new receiving boundaries are inventoried after file ownership is
  resolved, or a separately owned blocking Work is linked before acceptance.
