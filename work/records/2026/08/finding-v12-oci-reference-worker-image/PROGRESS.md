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

## Fifth review correction — 2026-08-25

The review's [P1] is corrected by satisfying the acceptance rather than by
superseding it. It offered two ways out — a deterministic image-output path, or
an approver ruling that weakens the confirmed contract — and **the first one
works on this deployment**, so no ruling is asked for.

**The measurement I inherited was wrong, and finding that out is most of this
correction.** The record said two `--no-cache` builds differ only in the
config's wall clock, with all six layers identical. They differ in four places,
and the fourth is the one nobody had seen: `COPY x /opt/baton/x` writes a tar
carrying the DIRECTORY entries the copy created, and their mtime is the build
clock.

    build a   'opt' mtime=1787702374   'opt/baton' mtime=1787702374
    build b   'opt' mtime=1787702375   'opt/baton' mtime=1787702375

The copied FILE keeps its source mtime; the directories do not, and the
resolution is one second. **So the earlier reading was an accident of timing**
— two builds inside one second agree, two that straddle a second do not.

That also explains the interaction the previous correction reported and
explicitly declined to guess at: two container cases passing alone, passing
beside the engine gate, passing in the locked build, and failing in a full
source run. A full run is slower, so the two builds straddle a second more
often. It was never an interaction between modules; it was a clock.

**The correction is an output step.** `v12/python/tools/worker_image.py`: the
engine builds under a staging tag, the saved OCI layout has its receipt
metadata normalized, the result is loaded back, and the identity of THAT image
is the digest the manager pins. Two independent executions reach it exactly —
measured across five separate runs during this correction, all
`sha256:55335c89…`, with the engine's own `image inspect` agreeing with the
digest the tool computed before loading.

**Only this recipe's own work is touched, and the boundary is derived rather
than counted.** A layer is the recipe's when its diff id is not one of the
base's; a history entry is the recipe's when it is newer than the base's
`Created`. The base image's layers and provenance travel byte for byte —
a normalizer that rewrote them would describe a different base from the one the
recipe pins. Inside a rewritten layer only DIRECTORY mtimes move, because a
regular file's mtime came out of the build context and is content.

**The weakening is withdrawn; the fact underneath it is not.**
`test_the_image_id_is_a_receipt_and_not_the_artefact` required the two
identities to stay DIFFERENT, which is exactly what the review refused. It is
replaced by `test_a_bare_engine_build_is_why_the_output_step_exists`: two bare
builds deliberately more than a second apart must differ in both id and layers,
and then the output step must make one identity of it. If a future engine makes
bare builds reproducible, that case fails and says so — which is the right way
round. The review's own additive regression is kept untouched and passes.

## One defect of this correction's own

Moving the build into the tool left
`test_the_reproducibility_build_does_not_reuse_builder_cache` patching this
module's `engine` helper and calling `ContainerCase.build` — a patch that now
reached nothing. So a daemon-free case ran a REAL build and left
`baton-w6633-test:cache-probe` behind. **The suite's own residual sweep caught
it**, which is the sweep working exactly as the record says it should. The case
reads a golden `build_vector` now: no daemon, nothing created.

## Verification

`evidence/gate-after-fifth-correction-2026-08-25.txt`.

- `test_worker_image` **58**; the new daemon-free
  `tests/tools/test_worker_image_build` **18**; daemon-backed
  `test_worker_container` **31** against docker 29.1.3 on linux/amd64 with the
  engine holding nothing afterwards.
- `test_parallel_runner` **36**: the new module is registered in
  `PARALLEL_MODULES`, which is exhaustive and fails on an unregistered one. It
  is daemon-free and writes only temporary directories.
- Full source suite **1210, ten failures**; locked installed-layout build
  **1210, the same ten**. Seven are the boundary inventory's pre-existing
  seven. **W6633's own daemon-backed failure is gone and nothing was added.**

## Reported and not fixed

Three failures belong to Work this claim does not hold, all reviewer
regressions posted after this participant passed that Work back.

- **W6632**, `tests.manager.test_oci`:
  `test_a_target_traversal_is_not_normalized_into_another_location` and
  `test_a_stale_policy_runtime_is_not_filtered_into_a_duplicate_start`, posted
  with `review-2026-08-26T00-03-30Z.md` while this correction was in progress.
  The second is about the identity comparison I added under W6632 and looks
  right on its face: the candidate listing query has to be broader than the
  identity comparison, or a stale-policy runtime is filtered out of the
  duplicate-start check instead of refusing it.
- **W6630**, `tests.manager.test_secrets`:
  `test_the_substitute_cannot_quote_a_live_bearer_substring`, already reported
  on that thread.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Sixth review correction — 2026-08-26

Both findings are trust-boundary defects in the transformer I added last
round, and both docstrings claimed the property the code lacked. That is the
part worth recording: "so two builds running at once do not stage over each
other" was written directly above the code that made them share one tag, and a
comment asserting a guarantee is exactly what stops a reader looking for it.

**Ancestry is an ordered prefix, not set membership.** `_base_facts` returned a
`frozenset` and the normalizer called every diff id found in it a base layer,
so a layout carrying one of two claimed base layers and not the other was
accepted, rewritten and certified as descending from the pinned base. An image
descends from a base by carrying that base's layers, in that base's order, at
the FRONT. The engine already reports them in order; keeping that order is the
whole of the fix. The recipe's layers are the suffix taken by POSITION, which
is stricter than membership in a way membership could never be — a recipe layer
whose digest happened to equal a base layer's is still the recipe's, because of
where it is.

**The stage is an allocation, not a derivation.** One mutable
`<target>-unnormalized` meant two simultaneous builds for one destination could
save each other's un-normalized image or delete the tag the other was still
using. It is unique per invocation now, with the destination in the readable
prefix, and it is THREADED: `build_vector` takes it as an operand, because a
vector that allocated its own would name a reference its caller could not save,
remove or read back — the same defect wearing a different hat.

## A measurement I had to redo, honestly

My first can-actually-fail revert of the ancestry check left the two degenerate
guards in place, so the reviewer's case still raised — for the WRONG reason —
and the measurement said nothing. Reverted faithfully to the original
set-membership shape it fails, as it should. Recording it because a
can-actually-fail check that passes for the wrong reason is worse than none:
it reports confidence it has not earned.

## Verification

`evidence/gate-after-sixth-correction-2026-08-26.txt`.

- `test_worker_image_build` **22** (18 before); focused daemon-free cut
  **83, OK**.
- Both corrections **measured to fail without them**, restored byte for byte.
- **Daemon-backed 31/31** against docker 29.1.3, including the two-independent
  -builds identity case — so the ordered-prefix check accepts the real base and
  the allocated stage still builds, saves, loads and is removed. No staging
  image survived the run, which is the property the unique reference could most
  easily have broken.
- `test_parallel_runner` **36 OK**.
- Source suite and locked build both **1232, eleven failures**, and
  `tests.tools.test_worker_image_build` is not among them.

## Reported and not fixed

- **W6632**, two `test_oci` regressions posted mid-correction. Both are real
  defects in that Work's own last correction — mine: it moved the three
  resolved digests out of the engine filters and stopped, leaving the attempt
  id, authority, work, participant and generation as exact filters, and it
  compares only the image and the three digests after the read. Reported on
  T6632 with the direction I would take.
- **W6630**, the pair-assertion pair, already reported on T6630.

Both are routed to `baton.feat`. The remaining seven are the long-standing
boundary-inventory failures.

## Still the operator's

PLAN item 6: drain, deploy, fresh contexts, and W12181. Nothing here was
verified against the running deployment.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Seventh review correction — 2026-08-26

**The mtime finding is about a decision I wrote and defended**, and the review
is right. The rule said only directory mtimes move, because a regular file's
mtime "came out of the build context and is content". The build context is a
CHECKOUT, and a checkout does not pin mtimes — the version-control source
carries bytes and the executable bit and nothing about when a working tree was
populated. So two fresh checkouts of one revision produced two identities: the
exact ambient-clock dependency this output step exists to remove.

I drew the line between "the copy created it" and "the context supplied it".
The line that matters is **what the source of truth actually pins**, and it
pins neither. The old rule is marked superseded in `FINDING.md` with its
reasoning, because the wrong distinction is the instructive part.

**And the real-engine case could not have caught it.** It builds twice from ONE
context, so both builds see one set of source mtimes. Worth recording on its
own: a daemon-backed gate is not automatically the stronger evidence, and here
only a daemon-free fixture can vary a checkout.

**The cleanup finding is the second time in this Work a comment has asserted a
property the code did not have** — the first was the shared staging tag, one
correction ago. The removal ran in `finally` and discarded its result, so a
refused `image rm` left the mutable un-normalized image under a readable tag
while the function returned a pinnable identity. It is checked now, and the
raise sits after the `finally` so an earlier failure stays primary: a build
that failed and then could not clean up is reported as the build failure it is.

## Verification

`evidence/gate-after-seventh-correction-2026-08-26.txt`.

- `test_worker_image_build` **27** (22 before): the review's two kept as
  written, one assertion revised under its explicit confirmation with its
  class renamed, and four added — two checkouts reaching one identity, the
  content surviving the clock normalization, and a refused cleanup not
  replacing an earlier failure.
- **Both corrections measured to fail without them**, restored byte for byte.
- **Daemon-backed 31/31** against docker 29.1.3 including the
  two-independent-builds identity case, with no staging image surviving;
  `test_worker_image` and `test_parallel_runner` 94 OK.
- Source suite and locked build both **1253, seven failures**, taken back to
  back over a tree hashed identical before and after.
- **The seven are the long-standing boundary-inventory failures and nothing
  else.** For the first time in this campaign there is no reported-not-fixed
  section here: every failure the suite carries belongs to the one other Work
  that has held them throughout.

## Still the operator's

PLAN item 6: drain, deploy, fresh contexts, W12181 through `pc.ops`, and
W10198 returned. Nothing here was verified against the running deployment.

## State

**Awaiting independent re-review.** The claim is not released and no Git
operation was performed.


## Ninth round — the [P1] corrected, and the blocker revalidated as lifted

### [P1] Cleanup could erase or replace its evidence

Both branches the review named were real and both are corrected.

The removal ran in `finally` and its result was only inspected AFTER the
protected body succeeded. So on the failing path the answer was discarded while
the exception unwound — the "cleanup evidence in the log" the comment promised
did not exist — and a removal that RAISED replaced the build failure outright,
which is the worse half: an operator reading a timeout has no idea the build
failed first. **That is the third time in this Work a comment has asserted a
property the code did not have**, and the shape is the same each time: the
guarantee was written where the happy path could see it.

`_cleaned_up` ANSWERS rather than raises, and its caller decides what the
answer is. A helper that raised could only ever be the primary failure, which
is the defect it exists to correct.

- an earlier failure stays primary and the cleanup outcome travels with it via
  `add_note`;
- a cleanup that could not RUN is the same kind of fact as one that ran and
  refused — the staging image may still be there, and the operator needs to
  know which engine and which tag to look at;
- with no earlier failure either outcome is the primary failure, because a run
  that built, saved, normalized and loaded and then could not clean up is one
  whose success would otherwise be a lie;
- the scratch tree goes whatever happens: it carries no evidence anybody can
  act on, and leaving it behind on an engine's bad day turns one failure into a
  disk that fills.

Both cleanup prose paths are bounded by `MAX_CLEANUP_PROSE`, for the reason
every diagnostic here is: the text is an engine's, the destination is a log,
and an unbounded operand makes the size of a durable line somebody else's
decision.

Measured — each of the three guards fails a case when removed:

    the earlier failure loses its cleanup evidence
        -> test_a_refused_cleanup_is_attached_to_the_earlier_failure
    a cleanup exception replaces the primary failure
        -> test_a_cleanup_exception_cannot_replace_an_earlier_failure
    a refused cleanup on the successful path is ignored
        -> test_a_failed_stage_removal_cannot_report_a_successful_build

`tests.tools.test_worker_image_build` **29/29**, including both additive
regressions.

## The BLOCKER is lifted, and here is the revalidation

The review said this Work stays blocked until W14251's revision is pinned, then
is revalidated against it before implementation resumes. **W14251 is closed**,
and the ledger agrees: W6633 reports `open_blockers = 0` and
`first_open_blocker = null`.

So this is the revalidation, done by reading the pinned schema and MEASURING
this image against it rather than by re-reading the review.

**What the contract now pins.**

    completionManifest  schema, assignment_ref, disposition, outputs
    workerOutput        name, type, path, status, content_manifest,
                        result_metadata
    outputDescriptor    name, type, path, required, constraints
    sourceDescriptor    name, destination, required, content_manifest,
                        consumption

`/input/` is read-only and carries the manager-authored `input.json`;
`/output/` is writable until quiescence and carries the WORKER-authored
`output.json`, published LAST and atomically. Both paths are CONSTANTS of the
contract rather than operands. The manager's frozen-result receipt is a
different document in a different place and the worker never writes or reads
it.

**What this image is, measured.**

    work request members   COMMON_MEMBERS + ("task",)
    work answer members    ("disposition", "workspace", "recap")
    execution environment  ... BATON_WORKER_ASSIGNMENT, _WORKSPACE, _OUTPUT
    "input.json"           0 occurrences in the worker and the agent
    "output.json"          0 occurrences in the worker and the agent
    the agent reads the inline task   yes

**The exact change, and it is a protocol change rather than a rename.**

1. `work` takes no `task`. The assignment is read from `/input/input.json`;
   an inline task is the superseded shape.
2. The `work` answer becomes `disposition`, `outputs`, `recap`. `workspace`
   goes entirely — a workspace path is a host fact and this manager is
   artifact-neutral.
3. The three environment members go. This is a REMOVAL rather than a rename:
   with two fixed paths there is nothing left for them to say, and
   `ENVIRONMENT["execution"]` becoming the consent set is what proves it.
4. The worker measures each declared output's content manifest ITSELF and
   composes the completion envelope. The agent is the least trusted thing in
   the container, so it says which outputs it produced and nothing about the
   bytes — the same rule `check_answer` already applies to everything else.
5. `output.json` is published LAST and ATOMICALLY: written under a private
   name and renamed, so an interrupted publish leaves no envelope rather than
   an empty one. Its presence under its final name is the completion signal.
6. Ephemeral space is capacity: material becomes a result only by being
   written under a declared output path before the worker answers.

`check_answer`'s value rule needs one deliberate widening for `outputs`, and it
should be a rule of its own rather than a relaxation — "bounded text or a list
of text" is the boundary that keeps an agent from handing the manager a shape
it would have to interpret, and loosening it generally to admit one member
would give that up everywhere.

**Not started this round, and that is a scope statement rather than an
estimate.** The change above is the worker protocol, the scripted agent, and
both image suites; it is a full slice rather than a correction, and starting it
in the same round as the cleanup fix would have produced a half-rewritten
protocol. The revalidation the review asked for is complete and the instruction
above is exact.

## State

**Awaiting independent review**, with the [P1] corrected and the blocker
revalidated as lifted. No repository state was mutated.


## Tenth round — the slice is implemented and its suite is NOT migrated

**Read this first: I am handing back a RED direct suite, and that is a failure
of my own scoping rather than a property of the change.**
`tests.manager.test_worker_image` runs 58 cases with **6 failing**. Everything
below is true and none of it changes that.

### What is implemented

`v12/worker/baton_worker.py` and `v12/worker/scripted_agent.py` carry the
closed W14251 contract, with no compatibility aliases:

- `work` takes no `task`. `REQUEST_MEMBERS["work"]` is `COMMON_MEMBERS`, and
  the leftover `request["task"]` type check is gone -- it was still there after
  the member was removed, which is what a `KeyError` on the happy path turned
  out to be.
- The work answer is `disposition`, `outputs`, `recap`. `workspace` is gone
  entirely: a workspace path is a host fact and this manager is
  artifact-neutral.
- `BATON_WORKER_ASSIGNMENT`, `_WORKSPACE` and `_OUTPUT` are removed, so both
  postures see the same four members. The posture difference did not go with
  them -- it moved to where it belonged, which is the two roots a consent
  container does not have.
- `input_manifest()` reads `/input/input.json`, bounded, and takes the two
  things a worker acts on. It does NOT validate the manager's document; that
  boundary is the manager's.
- `measured()` computes each declared output's content manifest by §3.3's own
  rules. **The worker measures and the agent does not**: a content manifest is
  a claim about bytes and the agent is the least trusted thing in the
  container.
- `answered()` holds the agent's per-output answers against the declarations --
  it cannot rename, move, invent or drop an output, and a required output
  answered missing refuses.
- `publish_completion()` writes `/output/output.json` LAST and ATOMICALLY,
  under a private name and renamed, so an interrupted publish leaves no
  envelope rather than an empty one.
- `check_answer` gained a RULE for `outputs` rather than a relaxation. "Bounded
  text or a list of it" is what stops an agent handing the manager a shape it
  would have to interpret, and loosening it for one member would give that up
  everywhere.

### What is not done, exactly

`tests/manager/test_worker_image.py` is PARTLY migrated: the environment
fixture, the closed member sets, the answer sets and a new declaration-holding
case are done, and a `staged()` helper patches the two roots onto the modules
-- which is the contract's own shape showing through, since a constant has no
operand for a fixture to supply.

Six cases still fail. They are the ones that drive `work` end to end and need
`staged()` placed correctly; my insertion put it in the wrong position in
several of them. `tests/manager/test_worker_container.py`, the daemon-backed
suite, is UNTOUCHED and unrun.

### The judgement I got wrong

Last round I wrote that starting this slice alongside a correction "would have
produced a half-rewritten protocol". This round I produced a fully rewritten
protocol with a half-migrated suite. It is the same scoping error in a
different place: I estimated the implementation and not the migration, and the
migration is where the work was.

There was no clean undo either -- this role performs no mutating Git
operations, so once the edit was under way the only honest handling was this
note and an exact statement of where the tree stands.

## State

**Awaiting independent review with a RED direct suite: 52 of 58.** The
implementation is complete; the remaining work is fixture placement in six
cases plus the daemon-backed suite. No repository state was mutated.

## 2026-08-27 — the eleventh review's three output-boundary defects

Evidence: `evidence/w6633-2026-08-27-output-boundary.txt`.
No repository state was mutated.

All three findings were correct, and they are one slice because they are one
omission: **the worker consumed the manager's output declarations without
proving them.** It read four member names, joined `OUTPUT_ROOT` to whatever
`path` said, dispatched the agent, measured whatever appeared, and published.

### The declarations are proved before an agent is dispatched

New `_declarations()` runs before `agent.work`, so a declaration this worker
cannot honour never becomes bytes anywhere:

- the closed `outputDescriptor` shape, `constraints` included — the member set
  used to omit it, so the ceilings a declaration states were not merely
  unenforced, they were not *required to be present*;
- the closed `outputConstraints` shape and whole-number ceilings;
- the frozen `relativePath` **grammar**, on the spelling;
- **and** canonical containment under `/output/`, resolved;
- the reserved `output.json` name;
- unique names, and no two declarations naming one tree or nesting.

**The rules are derived from the shipped contract, not paraphrased.** The
descriptor and constraint member sets and the path pattern are read out of the
schema that already travels with the image. W19784's third review is the
standing lesson: a paraphrase agrees with its original until it doesn't, and
stops agreeing where it costs most. One case proves I did not invent a
*stricter* rule either — the frozen grammar accepts a trailing separator, so
`out/nested/` is deliberately absent from the refused list and the omission
says why.

### The ceilings are enforced while measuring

`max_entries` and `max_bytes` are checked as the bound is crossed, before the
next file is accumulated — so an oversized tree is never read into this process
and nothing is published.

**And every other frozen constraint member has an account**, which is what
"rather than silently dropping them" asks for:

- `link_policy` is enforced **by construction** — the measurement admits
  regular files only, so a link is refused whatever the policy said. It is a
  one-value const in 1.0, so a comparison could never fail and would be a guard
  no removal can measure.
- `allowed_media_types` is **carried and not enforced here**: a frozen
  `contentManifest` entry is a path, a byte count and a digest, so this worker
  has no media type for anything it measures. It is enforced where one exists,
  on the collected artifact in the manager's `output.py`.
- `validator_digest` **refuses the assignment when non-null** — fail-closed
  rather than unimplemented. §7.2 makes `type` opaque and says the manager
  never branches on it, so a worker running a type-specific validator would be
  branching on exactly that; nothing else in 1.0 runs one either, and
  publishing a result while ignoring a stated constraint is a result nobody
  checked.

### Two surfaces carrying different things

The completion envelope is the durable document and holds the whole record per
output. The framed answer is the correlated reply and carries the bounded
**names** of what was produced. `check_answer` no longer exempts `outputs` from
its own rule — the exemption was reasoned about the *other* document, and it
skipped the one member most able to carry a shape the manager would have to
interpret. Entries are bounded too: a list of unbounded strings is unbounded
text with extra steps.

### Measurement, and what it caught

Twelve guards, each measured by removal. **Eight came back vacuous on the first
pass** — I had built a boundary and driven a third of it. The grammar and the
containment rule were masking each other in particular: the review's own escape
case passes with *either* removed. They are now separated by cases that can
only fail one way each — spellings that stay inside the root once resolved, and
a canonical spelling that resolves out through a planted link.

### The built container

The handoff asked for it and this reviewer cannot run it. **41 of 41**,
including a real container answering with names while its envelope holds the
records, an oversized declared output producing **no completion signal**,
`../tmp/escaped` refused before the agent — the case the read-only input mount
does *not* cover, because that spelling targets the writable private ephemeral
space — and the reserved `output.json` name refused.

### An operational finding, recorded rather than acted on

Conformance covers two of these three. `A-03` certifies the path grammar, the
overlap rule and link refusal. **No case names a declared byte or entry
ceiling**, and none covers the worker-entry answer being names-only — frozen
rules the suite cannot currently observe, the same shape of gap W19784's
reviews found twice.

Not extended here: the register belongs to `finding-worker-runtime-conformance`,
these are pre-existing frozen rules rather than anything this Work introduced,
and W6634's design checkpoint is a standing warning about a slice carrying more
Jobs than it was scoped for.

### Gates

- the reviewer's own command, verbatim — **156 tests, OK** (144 with three
  failures at the review)
- the whole focused manager gate, 18 modules — **905 tests, OK**. Every round
  of this campaign since 2026-08-26 reported two standing failures as "W6633's,
  not mine"; they were mine the moment I held this Work, and they are gone.
- `test_worker_container`, daemon-backed — **41, OK**
- `test_boundary_inventory` — **93 tests, 6 failures**, the accepted baseline
- whitespace check — clean

## State

**Ready for independent review.** The direct gate is green, the built-container
positives and negatives are recorded, and no repository state was mutated.

## 2026-08-27 — the twelfth review: value rules, and a claim of mine that was false

Evidence: `evidence/w6633-2026-08-27-value-rules-and-links.txt`.
No repository state was mutated.

Both findings correct, and the first is the **third time this campaign has
caught the same shape**: proving one thing and claiming another.

- Two documents agreeing *with each other* was not authorization (W19784).
- A *normalized* mount target was not a *canonical* one (W19784, third round).
- And now: a member **set** is not a member's **value**. I derived the names of
  `outputDescriptor` and `outputConstraints` from the contract, checked two
  integers, and called it validation. A numeric `name`, a textual `required`, a
  `link_policy` outside its const and a ceiling above the frozen maximum all
  went straight through — and those values are used for lookup, for control
  flow, and for authoring the completion envelope.

### Every consumed value, against the rule that describes it

New `_held` reads the frozen rule for each member and applies it: types,
patterns, lengths, `const`, `minimum`/`maximum`, `uniqueItems`, `items`, and
`oneOf`.

**It is not a JSON Schema engine and must not become one.** It is the closed,
bounded keyword set those two definitions actually use — and an **unrecognised
keyword is a fault**, not a value it passes over. Silently skipping one is
exactly how a derived check becomes a paraphrase again, so if a later version
of those definitions uses a keyword this does not implement, the worker refuses
and says so rather than validating less than it claims. A case drives that
directly.

Two subtleties worth naming:

- **Booleans are not integers.** `isinstance(True, int)` is true in Python and
  false in JSON, so a `required` flag arriving where a ceiling belongs would
  have passed `minimum: 0` as the number one.
- **The `oneOf` branch is exercised directly** rather than through a
  declaration, and the reason is a measurement: `_limits` refuses every
  non-null validator digest immediately afterwards, so a declaration carrying
  `7` is refused whether that branch fires or not. A case that cannot fail for
  the reason it names is not evidence about that reason.

### My own claim was false, and now it is true

I wrote that `link_policy: forbid` is enforced **by construction**. That is
only true when every entry the traversal meets takes part in the construction,
and one whole list of them did not: `os.walk(..., followlinks=False)` puts a
symlink to a *directory* in `directories`, where it was skipped in silence. A
declared tree containing `linked-directory -> /output` measured as **empty**,
and the worker published a completion manifest saying so.

Both halves are now separate lines, and each is measured on its own — the
review's directory case and a new regular-file-link case.

### Measurement

Seventeen guards, each measured by removal, and the finding's requirement that
each fail **independently** shaped the cases: every value is chosen so exactly
one keyword rejects it. A 161-character `name` still matches the `opaqueId`
pattern, so only `maxLength` sees it; a two-character media type has no pattern
at all, so only `minLength` does.

The first pass had three vacuous guards and one bad anchor. The cases that
separate them are new.

**And the directory-link guard is measured through the built image too** —
`os.walk`'s directory/file split is a property of the runtime the *artefact*
has, not of the recipe. Present: `OK`. Removed: `FAILED`.

### Gates

- the reviewer's own command, verbatim — **162 tests, OK** (158 with eight
  failures at the review)
- `test_worker_container`, daemon-backed — **43, OK**, including a
  contract-invalid consumed descriptor value refused before the agent and a
  directory symlink producing no completion signal
- the whole focused manager gate, 18 modules — **911 tests, OK**
- `test_boundary_inventory` — **93 tests, 6 failures**, the accepted baseline
- whitespace check — clean

## State

**Ready for independent review.** No repository state was mutated.
