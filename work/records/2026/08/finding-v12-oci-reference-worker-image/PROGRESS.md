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


## Re-review correction — 2026-08-25

### [P0] The approved envelope, implemented in full

`baton.worker-entry/1` is now the whole contract rather than a name. Every
request carries `protocol`, `session`, `operation_id` and `operation`; the
session is the manager-minted identity of THIS posture-specific container and
arrives as `BATON_WORKER_SESSION`; the operation id is consumed once within it.

The order of the checks is the content. A frame that is not for this session is
refused before any question about entitlement, because answering "you are not
asked to work" would be answering a question somebody else was asked. Consent
and execution therefore hold different identities and each refuses the other's
frames — the topology's own rule, now enforced per message rather than per
container.

**There is exactly one response shape and it is correlated.** Every response
echoes the request's own three identity members; a success adds `ok` and
`answer`, a fault adds `ok`, `code` and a bounded `message`. That includes the
bounds fault, which used to drop the correlation — an uncorrelated shape
arriving by the back door.

**A frame with no readable identity gets no frame at all**, and a non-zero
exit. The ruling forbids inventing an uncorrelated response, and the manager
already owns the launched session; `Uncorrelated` is a separate exception from
`WorkerFault` precisely so the two cannot be confused at a call site.

### [P0] The image, container and cancellation evidence

`tests/manager/test_worker_container.py` — **21 cases**. It builds the pinned
image, inspects the CONFIG the engine actually applied rather than the recipe
text, reads the layer filesystem from inside a container (only the two program
files; the manager package is not importable; uid/gid are 65532), drives real
consent and execution containers through the framed channel, and proves the
container-level negatives the acceptance names.

**Cancellation is now the manager's real path.** A container is started
detached and holding its channel, confirmed to be RUNNING, stopped through the
engine, and its settlement recorded — and a separate case asserts that a clean
end of input exits zero, which is exactly why it could never stand in for a
stop. The superseded fixture is renamed to say what it actually observes.

**It fails rather than skips without a daemon**, and it removes every resource
it creates on every path — registered for cleanup before it can exist, so a
build that dies part way still has its tag removed. Two cases ask the ENGINE
whether anything survived, rather than a bookkeeping list of what somebody
remembered making.

### [P1] Closure is per operation, and the answer is a boundary

`REQUEST_MEMBERS` is keyed by OPERATION now. An execution `describe` carrying
`task` is refused: closure one level coarser than the contract is closure over
the wrong thing. And `check_answer` validates the whole agent answer against
the pinned closed set before it is framed — the agent is the least trusted
thing in the container and the answer is what crosses out of it. The scripted
`work` answer drops `task_digest`, which the pinned set does not name.

### [Open] Startup faults, on the approved ruling

A bootstrap fault is LATCHED while the framing loop stays operable, one bounded
identity envelope is read, and the pending failure returns through the ordinary
correlated shape before a non-zero exit. It never reaches the agent — a case
drives it with an agent that raises if it is ever called. If the session
identity itself is missing, nothing this program says could be correlated, so
it exits 2 with no frame and the manager settles from the engine.

## Verification

    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_image
    # Ran 54 tests -- OK
    PYTHONPATH=src python3 -m unittest tests.manager.test_worker_container
    # Ran 21 tests in 21.9s -- OK
    just build   # Ran 997 tests -- FAILED (failures=15, skipped=1)

**Fifteen, and three are not this Work's.** Twelve are the pre-existing
`oci.py` and `workspaces.py` failures. The other three are the reviewer's
additive cases on W6630, which landed in this tree while W6633 was being
corrected; all three are in `tests/manager/test_secrets.py`, that Work's file,
and W6630 is queued at `baton.impl` and was not held by this claim.

Evidence: `evidence/gate-after-2026-08-25.txt`.

## State

**Awaiting final review.**

## Final re-review correction — 2026-08-25

All three [P1]s are corrected, and the daemon-backed gate is recorded green
rather than described.

**The binding holds on every path.** `bind` is the protocol and
expected-session pair, lifted out of `handle` — which the latched bootstrap
path never reaches, so a container that had failed to start echoed an
arbitrary peer's session and disclosed its own posture failure to whoever
asked. `serve` establishes the correlation immediately after the one bounded
identity envelope, before it decides whether to answer with the latched fault
or dispatch. The three properties the correction had to keep are pinned by
their own cases now instead of being inferred: exactly one frame and a
non-zero exit from a latched container whichever fault it names, no agent
method reachable on that path, and — the other half of the same move — a
healthy container's ordinary wrong-session refusal still not ending the
channel.

**The platform is named and the identity is reproduced.** The build selected
no platform and the identity case proved only digest syntax. It builds with an
explicit `--platform` taken from the engine's own server, so the gate runs on
arm64 without emulation and what was asked for and what was applied are two
facts that can disagree; then it builds the same context again under its own
tag and requires one immutable identity. The claim is made narrowly on
purpose — a pinned base plus two `COPY`s and metadata is what makes it
available, and a recipe that installed anything could not make it.

**The residual assertion can fail.** It discarded exactly the prefix every
container this suite creates, so the list was empty whatever survived. It
asserts over every non-empty match now, and a companion case creates a real
container and requires the sweep to name it. Both image tags are registered
for removal before either build can create one.

## Verification

`evidence/gate-after-final-correction-2026-08-25.txt`. Focused 58/58;
daemon-backed 23/23 against docker 29.1.3 on linux/amd64, with the engine
asked afterwards and holding nothing. Full suite and locked installed-layout
build agree byte for byte. Nothing was added to the pre-existing failure set
by this correction; the reviewer's case is gone; five failures belong to
W6627's and W6630's in-flight reviews and are reported rather than fixed.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.

## Fourth review correction — 2026-08-25

Both [P1]s are fixed and both additive regressions are green and kept as
written.

**The gate launches what the manager launches.** The launches carried
`--network none` and nothing else, so twenty-three green cases ran containers
with the default capability bounding set, a writable root and no CPU, PID or
memory bound — the acceptance's filesystem, user and capability half was never
established by an artefact. One shared builder derives every unconditional
restriction from the adapter's own table and applies it everywhere. And since
argv says only what was asked for, three cases read the applied posture from
inside a running container.

**The rebuild is an execution.** `--no-cache` is unconditional rather than a
keyword a caller may relax.

**One disagreement, measured rather than argued.** The review asked to compare
immutable identities. The image ID digests a config carrying a wall-clock
timestamp, so two independent builds have two ids by construction — measured
twice on docker 29.1.3, with all six RootFS layers identical and
`SOURCE_DATE_EPOCH` changing nothing on an engine with no `buildx`. The case
compares the artefact instead: every layer digest and the applied
configuration. A companion case holds the measurement, so a future engine that
does make ids reproducible fails it rather than letting the weaker comparison
stand.

## Verification

`evidence/gate-after-fourth-correction-2026-08-25.txt`. Focused 58/58;
daemon-backed 29/29 against docker 29.1.3 on linux/amd64, with the engine
afterwards holding nothing. Full suite 1095, and the installed-layout run's
failure list compared line by line against the source run's: identical.
Nothing added by this correction; the review's two removed; three remaining
failures belong to W6627's and W6630's in-flight reviews.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.
