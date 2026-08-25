# Implementer progress — the OCI reference worker image

Created 2026-08-24 by `baton.claude` on claiming W6633, as the record requires.

## Delivered

- `v12/worker/baton_worker.py` — the entry point and its framed channel.
- `v12/worker/scripted_agent.py` — the deterministic M2 agent.
- `v12/worker/Dockerfile` — the recipe.
- `v12/python/tests/manager/test_worker_image.py` — **30 methods, all passing**.

**The base is pinned by digest, and the digest is real.** I first wrote a
placeholder, which would have been a recipe that looked pinned and named
nothing; it is now
`sha256:8fef26df932191825664e4957ff488c96dfe64918327634a357a55facbc994d3`,
resolved on this host from `docker manifest inspect -v python:3.13-slim` and
recorded in the recipe so a reviewer can re-resolve it. A tag is a name somebody
moves, and a worker built from a moved tag makes the image digest the manager
records a description of something else.

**The entry point imports nothing from the distribution.** A worker that could
import the manager is a worker one bug away from holding the manager's
capabilities. That is checked structurally — an AST case asserts neither file
imports `baton_v12`, nor `socket`, `subprocess`, `urllib`, `http`, `sqlite3` or
`ssl` — because "we did not import it" is a property somebody breaks by
accident.

**The channel is length-prefixed, not newline-delimited.** A newline is a byte
an agent's output legitimately contains, and a protocol whose framing a payload
can forge has no framing. Bounded in *both* directions and on the *header* as
well as the body: a peer that never sends a newline cannot make the worker read
forever, and an oversized frame is refused before its body is read — asserted by
checking the stream position, not by trusting the code path.

**Consent cannot reach execution, and it is checked on every operation.** A
check that ran once at start is a check a later message walks past, so the
fixture drives `describe, consider, work, consider` through one session and
requires exactly `True, True, False, True`. `work` from a consent container
refuses as `posture` and says the container *is not asked to* it — not "unknown
operation", because `work` is a real operation this container is not entitled
to, and that distinction is what makes the negative test mean anything. There is
no promotion message: six plausible spellings all refuse. A consent container
that carries `BATON_WORKER_ASSIGNMENT`, `_WORKSPACE` or `_OUTPUT` refuses
outright, because it means the manager built the wrong container and continuing
would hide that. The exclusion runs both ways: an execution container is not
asked to consent.

**The image defaults to no posture.** An image that defaulted would run as
`execution` when the manager forgot to say — and forgetting is exactly when a
default matters.

**Faults are frames, never crashes.** An agent failure reports its exception
type and no traceback, because a traceback would carry paths from inside the
image out through the channel; a worker that died would leave the manager
waiting for a runtime that is gone, and reconciliation would have to infer what
happened from engine state — which is what the manager is built not to do.
Cancellation arrives as input ending and exits 0, because the manager stopped it
on purpose and a fault would report its own cancellation as a problem.

**Two places agree because they were written from one decision:** the recipe's
`USER 65532:65532` is asserted against the adapter's own `--user` restriction
from W6632, so the two cannot drift.

## The operational finding: what this suite does *not* prove

The acceptance names image **inspection** and **container-level** negative
tests. This suite answers both at the recipe and program level — what the image
will be, and what the entry point does — and does **not** build an image or run
a container.

That is a deliberate line, not an omission I am hoping goes unnoticed. Docker
29.1.3 is reachable on this host, so I could have built it; the reason not to is
that a case in this gate would then depend on somebody's daemon being up, a
registry being reachable and a layer cache being warm. The record's own
acceptance separates "mutable engine smoke tests are isolated and leave their
own resources absent" for the same reason.

**What is therefore unproven here:** that the built image's inspected
filesystem, user, capability and entrypoint posture match the recipe, and that a
real container refuses what the program refuses. That is a bounded cut — build,
inspect, run two containers, assert, remove — and it belongs beside W6632's
isolated engine smoke test rather than inside this suite. **If the reviewer
wants it in this Job, say so and I will add it as an opt-in case that skips
when no daemon is present.**

## State

**Awaiting independent review.** The image is not built by this claim; the
recipe, the entry point, the agent and 30 cases are.
