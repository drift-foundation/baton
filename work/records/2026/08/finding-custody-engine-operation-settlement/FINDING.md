# Settle or cancel the engine-side custody operation

Work: W44342
Discovery: W43974 third independent review,
`work/records/2026/08/finding-v12-worker-custody-provider/findings/finding-custody-helper-reclamation/review-2026-08-30T05-44-32Z.md`.

## Purpose

Provide the engine-provider boundary W43974 needs before recovery may prove a
derived custody helper absent: no accepted engine-side operation may remain
capable of acquiring that name after the provider reports timeout or failure.

## Observed defect

Docker is a client/server engine. `subprocess.run(argv, timeout=seconds)`
terminates and reaps the local CLI process; that alone is not evidence that an
already-submitted daemon request has been cancelled or settled. A timed-out
create can therefore finish after recovery's absence proof.

The additive daemon-free regression remains in
`v12/python/tests/manager/test_custody.py` as
`test_reaping_the_cli_does_not_settle_a_daemon_mutation`.

## Required boundary

Recovery and absence proof begin only after the provider can establish that no
pending operation may later acquire the derived helper name. A local process
ending, an engine acknowledgement, and a point-in-time absence observation are
each insufficient on their own.

## Open design directions

- submit/create through a boundary whose accepted mutation is known before the
  deadline window opens;
- use an engine API operation that can cancel and settle an accepted request;
- durably journal a pending engine operation and reconcile that operation,
  rather than only the resulting container name, after restart.

These are research directions, not accepted design decisions.

## 2026-08-30 — reviewer enrichment

### Confirmed: there is no production provider to repair in place yet

`custody_act` currently wraps an injected callable in `EnginePort` and treats
an answer or exception from that callable as the only provider state. The
real-shaped gate in `v12/python/tests/manager/test_custody_engine.py` supplies
that callable with `subprocess.run(..., timeout=seconds)`. No production
deployment below `v12/python/src/` or `v12/python/tools/` yet supplies the
custody callable; W39358, the minimal dogfood operator, is the first deployment
that will have to do so.

This makes W44342 a provider-contract and deployment-composition decision,
not a correction that can be hidden inside the existing generic `EnginePort`.
The generic port can say that its local child ended. It has no operation
identity, pending state, replay or settlement query with which to say what the
daemon did after accepting the child's request.

### Confirmed: the Docker API does not expose the missing acknowledgement

Docker documents `run` as a composition of several Engine API calls rather
than one daemon operation. Its own CLI performs create, attach, start and wait
as separate acts:

- [Docker Engine API v1.52](https://docs.docker.com/reference/api/engine/version/v1.52/)
  says running a container is the notable CLI operation made from several API
  calls; `POST /containers/create` answers `201` only when creation succeeds.
- [Docker `container create`](https://docs.docker.com/reference/cli/docker/container/create/)
  creates but does not start the container, prints the container ID only after
  creation, and documents that `docker run` performs this create before start.
- [Docker CLI `start.go`](https://github.com/docker/cli/blob/master/cli/command/container/start.go)
  attaches and installs a wait before it calls `ContainerStart` on the known
  container ID.
- [Moby `daemon/create.go`](https://github.com/moby/moby/blob/master/daemon/create.go)
  passes the HTTP request context into create and has deferred cleanup when
  create returns an error. That is useful cancellation cooperation inside the
  daemon, but it is not a caller-visible wait for that handler to finish.
- Go's [HTTP package contract](https://pkg.go.dev/net/http) cancels an incoming
  request context when the client connection closes. Cancellation is a signal;
  closing the client does not answer that the server handler has observed the
  signal, finished cleanup, or returned.

The Engine API lists create, start, wait, inspect and remove operations, but no
operation resource or cancel-and-join endpoint for an accepted container
create. **Inferred from those primary surfaces:** replacing the CLI with a
direct HTTP client would close one process boundary, but a client context
ending would still not be positive evidence that the daemon handler has
finished. It is not the missing settlement proof.

### Confirmed: split create/start narrows the race but does not close it

Creating first and then starting the returned container ID is valuable. Once
create has answered successfully, the derived name belongs to one exact
container and a late start cannot create a second container under that name.
It also lets cleanup target the ID rather than rediscovering by name.

It is not sufficient by itself. A client can be interrupted before create's
answer, which is the same unknown interval one step earlier. Calling create
without a deadline merely trades the late-create race for an unbounded
manager. Applying a client deadline recreates the original uncertainty.

### Proposed provider boundary: durable acceptance, then asynchronous settlement

The smallest boundary that supplies the missing fact is an independently
supervised local provider with a durable, idempotent operation queue. This is
a proposal requiring an approver ruling because it introduces a long-lived
deployment component; it is not silently pinned by this research.

1. The manager derives one custody engine operation ID from the complete
   immutable request: engine kind, derived helper name, image digest, mount
   identity, restrictions and custody verb. An exact retry names the same
   operation; changed operands collide.
2. The provider acknowledges acceptance only after the request is durable.
   Losing the client reply is harmless because resubmitting the same ID reads
   the same row. The provider, not the manager call, owns the Docker client
   lifetime after acceptance.
3. The provider first performs `create --pull=never --rm` and records the
   returned container ID. Only after that terminal create answer does it
   attach/start/wait by exact ID. This removes image pull from the mutation
   window and makes every post-create operation about a known object.
4. The manager's deadline bounds its WAIT for provider settlement. Reaching
   it returns `pending(operation_id)`; it does not kill the provider's Docker
   client and does not start recovery, inspect for absence or submit another
   operation. A later manager asks the provider for the same operation.
5. `settled(answer)` is terminal and replayable. Only then may `custody_act`
   consume the answer or reconcile the exact recorded container ID. If the
   provider itself crashes while Docker's answer is unknown, the row remains
   pending and fails closed; name inspection alone cannot promote it to
   settled. Operator intervention or an independently proved daemon-generation
   fence is required before that row can be retired.

This boundary chooses safety over availability deliberately. A permanently
pending row is an operational problem; a second custody act beside an
unsettled daemon mutation is silent workspace overlap.

### Required public states

| provider state | manager action |
| --- | --- |
| no durable request | submit once |
| accepted/pending | wait or report unresolved; no engine recovery and no retry |
| create settled with exact ID, execution pending | wait; cleanup may target only that ID after provider settlement |
| settled with engine answer | validate and record the custody answer |
| settled failure with exact ID | identify, remove, prove the ID absent, then retry only under a new recorded operation generation |
| provider crash with daemon outcome unknown | remain pending; no absence claim |
| signature collision | refuse |

### Regressions the implementation owes

- client timeout after provider acceptance while daemon create finishes later:
  the manager returns pending and neither inspects for absence nor retries;
- manager process interruption after acceptance: the provider reaches one
  terminal durable answer, and a restarted manager replays it;
- reply loss after durable acceptance: exact retry does not submit twice;
- provider crash during create: the row remains pending and no point-in-time
  empty listing settles it;
- create success records exact ID before start; start timeout cannot acquire a
  second name;
- changed vector under the same operation ID collides;
- terminal failure plus identified container removes by ID, proves absence and
  only then permits a new generation;
- the existing
  `test_reaping_the_cli_does_not_settle_a_daemon_mutation` remains unchanged
  and must fail any provider that equates local CLI exit with settlement.

### Open ruling and coordination finding

**Open:** approve the durable local provider boundary above, including its
fail-closed permanently-pending state, or explicitly narrow the dogfood pilot
to W43974's current `UNRESOLVED` stopgap. A direct Docker API client is not a
third answer unless it supplies a positive join/settlement proof absent from
the documented API.

W43974 calls W44342 its explicit blocker, but the ledger had no dependency
edge. The reviewer attempted `block work=W43974 on=W44342`; Baton correctly
refused because `baton.codex` is not a handler of W43974's `baton.impl` Route.
The implementer or approver must add that edge rather than relying on prose.

## 2026-08-30 — approver ruling: retain the stopgap and park the provider

The dogfood deployment does **not** acquire the independently supervised
durable provider in this pass. The accepted pilot boundary is W43974's
fail-closed `UNRESOLVED` result: after a lost or timed-out engine mutation it
does not claim absence, does not begin another custody act, and leaves the
attempt untrusted for later operator reconciliation. The ordinary settled
engine path remains usable.

This ruling deliberately chooses the positive vertical slice before this
hardening component. The provider proposed above remains the recommended
long-term direction if operational evidence shows that unresolved Docker
mutations need automatic settlement. W44342 is parked rather than discarded;
it is not a gate on W43974 or the first useful dogfood run.

The earlier coordination direction to add a W43974-on-W44342 dependency is
**superseded**. No such edge is added under this ruling.

### Research verification

`PYTHONPATH=src python3 -m unittest tests.manager.test_custody` runs 102 tests
and passes after the authorized W43974 stopgap assertion update. That green
baseline does not close W44342: the daemon-side regression asserts that the
stopgap reports `UNRESOLVED`, not that the engine operation settled.
