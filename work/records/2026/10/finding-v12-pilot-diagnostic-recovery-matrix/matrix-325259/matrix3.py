"""W325035 — the finite matrix completed on the seam the review named.

Review 2026-10-18T18-17-05Z accepted the assertion and live-cancellation
corrections, refused completion, and named the seam I had wrongly called
absent. Its instructions, and where each one landed:

  * `ComposedOneJobCase.quiescing` already models stop and POSITIVE,
    exactly-identified runtime absence; `serving` replaces the engine on every
    call, so a restart must be composed by calling
    `stage_execution.operations_from` directly with the SAME engine object.
    `composing()` below does that, and my previous claim that this fixture
    exposes no absence seam is WITHDRAWN -- it exposes it at the `engine_run`
    boundary, which is where these scenarios drive it.
  * the self-check must fail for its OWN intended reason: `main` now requires
    a `CheckFailed` naming the exact expected check, and a setup or cleanup
    error is an unexpected failure rather than a satisfied expectation.
  * a committed operation whose REPLY is dropped, at the selected boundary --
    not merely a committed worker turn awaiting processing. Scenario 1 drops
    the launch reply after the engine really started the container.
  * absence of projection keys does not establish absence of a supported
    diagnostic assignment operation. Scenario 5 asks the Authority's own
    route, handler, claim, label and creation surfaces instead, and the broad
    product-gap claim in `../matrix-325138/` is WITHDRAWN: an explicit
    eligible diagnostic owner IS reachable through supported coordination.
  * the proposal inventory is read from the Authority (`proposals_of`), not
    inferred from a missing projection member.

Boundaries, labelled per scenario: the composed native Job world is imported
from `tests.tools.test_stage_execution` (the parent W321690 lineage) and NOT
modified; the ENGINE answers without a daemon; the PROVIDER is injected at the
adapter's own process seam; the engine's absence and confusion sentences are
injected at `engine_run` and are the engine's own prose. No product edit, no
forged receipt, no raw SQL, no live model, no live credential, no deployment.

PROVENANCE, CORRECTED. My earlier blanket "no Git command" was imprecise:
`ComposedOneJobCase.vcs` runs `git` against the FIXTURE's own disposable
source tree to build its history, under `GIT_CONFIG_GLOBAL=/dev/null` inside a
temporary root. The accurate statement is the one used from here on: nothing
in this run mutates this repository's history, index or working tree.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --evidence <directory>
"""
import argparse
import json
import pathlib
import time
import traceback


class CheckFailed(AssertionError):
    """A named expectation that did not hold."""

    def __init__(self, label, detail=None):
        super().__init__(f"{label} (detail: {detail!r})")
        self.label = label


class Checks:
    def __init__(self):
        self.held = []

    def expect(self, label, condition, detail=None):
        passed = bool(condition)
        self.held.append({"check": label, "passed": passed, "detail": detail})
        if not passed:
            raise CheckFailed(label, detail)
        return passed

    def note(self, label, value):
        self.held.append({"observation": label, "value": value})
        return value

    def document(self):
        return self.held

    def passed(self):
        return sum(1 for one in self.held if one.get("passed"))


def say(place, name, answer):
    (place / name).write_text(
        json.dumps(answer, indent=2, sort_keys=True, default=str) + "\n")


def world():
    from tests.tools.test_stage_execution import (
        TheComposedJobTraversesReviewAndAcceptance as Composed)

    case = Composed()
    case.setUp()
    return case


def composing(case, incarnation, engine_run):
    """One manager composition over this world's stores, ENGINE SUPPLIED.

    This is `ComposedOneJobCase.serving` with the one difference the review
    named: `serving` calls `self.quiescing()` and therefore installs a NEW
    engine world on every call, so a "restart" composed through it would be
    reconciling against a second engine that has never heard of the container
    the first one started. Here the caller owns the engine, so a restart sees
    the same runtime state -- minted identities, removals and all.
    """
    from tests.job_manager import fixtures
    from tools import stage_execution

    job, control = case.stores(incarnation)
    composed = stage_execution.operations_from(
        case.composed_document(line_declared_base=case.base), job, control,
        engine_run=engine_run,
        credential_provider=lambda provider, reference: case.secret,
        clock=lambda: fixtures.NOW, checkout=case.checkout)
    case.addCleanup(composed.close)
    # THE FIXTURE'S OWN HOLD, set for the same reason `serving` sets it
    # (W122060): `turn` asks this role's composition what it mounted, and the
    # fixture reads that from here.
    case._composed = composed
    return job, control, composed


# THE DEDICATED DIAGNOSTIC WORK'S identity, in the canonical shape the
# Authority requires: a local selector like `0000000a-WDIAG` is refused, which
# is how this constant came to exist.
DIAGNOSTIC_WORK = "0000000a-W2"


def identities(case):
    held = case.submission["jobs"][0]
    return {"work_id": held["stages"][0]["work_id"],
            "job_id": held["job_id"],
            "submission_id": case.submission["submission_id"],
            "authority_uuid": case.config["authority_uuid"]}


def _now():
    from tests.job_manager import fixtures

    return fixtures.NOW


def sweeps(case, job, composed, ticks=12):
    from baton_v12.job_manager import sweep as tick

    for _ in range(ticks):
        tick(job, composed, now=_now())
    return case.states(job, composed)


def stage_of(case, job, composed, kind="implementation"):
    from baton_v12.job_manager import status as projected_status

    projected = projected_status(job, composed, observed_at=_now())
    return [one for one in projected["jobs"][0]["stages"]
            if one["kind"] == kind][0]


def launches(engine):
    return [one for one in engine.vectors if one[1] in ("run", "create")]


def published_candidates(case):
    """The AUTHORITATIVE proposal inventory, from the Authority itself."""
    from baton_v12.authority import Authority

    reader = Authority.open_readonly(
        case.authority_path,
        expected_authority_uuid=case.config["authority_uuid"])
    try:
        return [one["proposal_id"] for one in reader.proposals_of(case.work)]
    finally:
        reader.dispose()


# -- scenario 0 --------------------------------------------------------------

SELF_CHECK = ("implementation is completed immediately after submission "
              "(INTENTIONALLY FALSE)")


def harness_self_check(case, checks):
    """DELIBERATELY WRONG, and it must fail for THIS reason.

    Review 2026-10-18T18-17-05Z: the previous harness compared only
    `outcome == failed` against `expected_failure`, so a setup exception or a
    cleanup failure satisfied the self-check and the run still reported the
    checks as checking. `main` now requires a `CheckFailed` whose label is
    exactly `SELF_CHECK`.
    """
    from baton_v12.job_manager import submit as submit_jobs

    job, _control, composed = case.serving()
    submit_jobs(job, case.submission)
    states = case.states(job, composed)
    checks.note("actual stage states", states)
    checks.expect(SELF_CHECK, states.get("implementation") == "completed",
                  states)
    return {}


# -- scenario 1 --------------------------------------------------------------

def lost_launch_reply_across_restart(case, checks):
    """A COMMITTED start whose REPLY is dropped, then a restart.

    The exact boundary the review asked for. The engine really starts the
    container -- the identity is minted and running -- and the process is
    stopped before the manager can reconcile that reply, which leaves
    `start-requested` with NO attached runtime and a stage the control plane
    still owns. A restart then has to find the container the lost reply named
    without starting a second one.
    """
    from baton_v12.job_manager import submit as submit_jobs
    from baton_v12.job_manager import sweep as tick
    from baton_v12.worker_manager import attempt_runtime_of
    from baton_v12.worker_manager.attempts import (
        attempt_preparation_failure_of, attempt_start_failure_of)
    from tests.tools.test_single_worker import running_now

    engine = case.quiescing()
    case.engine = engine
    armed = {"on": False}

    def dropping(argv, *, seconds=None):
        # THE REPLY IS LOST, not the act: the engine has already run and the
        # container is already up when this raises.
        if argv[1] == "ps" and armed["on"]:
            armed["on"] = False
            raise KeyboardInterrupt("the launch reply is lost")
        answer = engine(argv, seconds=seconds)
        if running_now(argv):
            armed["on"] = True
        return answer

    job, control, composed = composing(case, "stage-lost", dropping)
    submit_jobs(job, case.submission)
    stopped = False
    try:
        for _ in range(8):
            tick(job, composed, now=_now())
    except KeyboardInterrupt:
        stopped = True
    checks.expect("the manager process stopped inside the launch reply",
                  stopped)
    attempt = stage_of(case, job, composed)["attempt_id"]
    interrupted = attempt_runtime_of(control, attempt)
    checks.expect("the start is COMMITTED",
                  interrupted["execution_runtime"] == "start-requested",
                  interrupted["execution_runtime"])
    checks.expect("and its reply is LOST: no runtime is attached",
                  interrupted["runtime_id"] is None, interrupted)
    checks.expect("the engine nevertheless really started one container",
                  len(launches(engine)) == 1
                  and engine.runtime_id is not None,
                  {"launches": len(launches(engine)),
                   "engine_runtime": engine.runtime_id})
    checks.expect("so the stage is still the control plane's to drive",
                  stage_of(case, job, composed)["state"] == "claimed",
                  stage_of(case, job, composed)["state"])
    orphan = engine.runtime_id

    # THE RESTART, over the same stores and the SAME engine state.
    fresh_job, fresh_control, fresh = composing(case, "stage-lost-again",
                                                engine)
    recovered = fresh.recover(now=_now())
    checks.note("the manager's own restart recovery", recovered)
    asked = len(engine.vectors)
    settled = sweeps(case, fresh_job, fresh, ticks=10)
    verbs = [one[1] for one in engine.vectors[asked:]]
    checks.expect("the restart ASKED the engine",
                  "ps" in verbs and "inspect" in verbs, sorted(set(verbs)))
    adopted = attempt_runtime_of(fresh_control, attempt)
    checks.expect("the restart adopted the EXACT runtime the lost reply named",
                  adopted["runtime_id"] == orphan, adopted)
    checks.expect("on the same attempt identity",
                  adopted["attempt_id"] == attempt, adopted["attempt_id"])
    checks.expect("the assignment is unchanged by the recovery",
                  adopted["assignment"] == interrupted["assignment"],
                  adopted["assignment"])
    checks.expect("NO second container was started",
                  len(launches(engine)) == 1, len(launches(engine)))
    prepared = sorted(case.worker_of(fresh, "implementation").stage._prepared)
    checks.expect("no duplicate attempt was prepared", prepared == [attempt],
                  prepared)
    checks.expect("nothing falsely finished",
                  settled.get("implementation") != "completed", settled)
    checks.expect("the successors stay blocked",
                  settled.get("review") == "blocked"
                  and settled.get("integration") == "blocked", settled)
    checks.expect("no start failure and no preparation failure were invented",
                  attempt_start_failure_of(fresh_control, attempt) is None
                  and attempt_preparation_failure_of(fresh_control, attempt)
                  is None)
    checks.expect("and the recovered stage is serving again",
                  settled.get("implementation") == "waiting", settled)
    checks.expect("no candidate was published by any of it",
                  published_candidates(case) == [], published_candidates(case))
    return {"identities": dict(identities(case),
                               implementation_attempt=attempt),
            "lost_reply_window": interrupted,
            "orphan_runtime": orphan,
            "recover_answer": recovered,
            "engine_verbs_after_restart": sorted(set(verbs)),
            "adopted": adopted, "settled": settled,
            "corrects": "../matrix-325138/ said this fixture exposes no "
                        "engine-absence seam and that the lost-reply vector "
                        "could not be demonstrated here. Both are withdrawn: "
                        "the seam is the `engine_run` boundary, and the "
                        "vector is driven above."}


# -- scenario 2 --------------------------------------------------------------

def unknown_runtime_then_positive_absence(case, checks):
    """Two engine answers that are NOT the same fact, in the order that
    matters.

    An engine that cannot describe a container has said nothing about whether
    it is there; only the engine's own absence sentence NAMING THIS IDENTITY
    is absence. A manager that treated confusion as death would release an
    assignment whose worker is still running, so the unknown answer must leave
    the axis and the identity exactly as they were.
    """
    from baton_v12.job_manager import submit as submit_jobs
    from baton_v12.worker_manager import attempt_runtime_of

    engine = case.quiescing()
    case.engine = engine
    job, control, composed = composing(case, "stage-runtime", engine)
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    attempt = stage_of(case, job, composed)["attempt_id"]
    live = attempt_runtime_of(control, attempt)
    checks.expect("a runtime is attached and running before either answer",
                  live["execution_runtime"] == "running"
                  and live["runtime_id"] is not None, live)
    runtime = live["runtime_id"]

    # (1) HELD UNKNOWN: a non-zero answer whose prose names no absence.
    confused = {"on": True}

    def confusing(argv, *, seconds=None):
        if confused["on"] and argv[1] in ("ps", "inspect"):
            engine.vectors.append(list(argv))
            return {"status": 1, "stdout": "",
                    "stderr": "Error response from daemon: i/o timeout "
                              "talking to the socket"}
        return engine(argv, seconds=seconds)

    u_job, u_control, u_composed = composing(case, "stage-runtime-unknown",
                                             confusing)
    unknown_settled = sweeps(case, u_job, u_composed, ticks=6)
    held = attempt_runtime_of(u_control, attempt)
    checks.expect("an UNKNOWN runtime does not advance the axis",
                  held["execution_runtime"] == "running",
                  held["execution_runtime"])
    checks.expect("and does not erase the identity",
                  held["runtime_id"] == runtime, held["runtime_id"])
    checks.expect("the stage stays gated rather than finishing",
                  unknown_settled.get("implementation") == "waiting",
                  unknown_settled)
    checks.expect("no second container was started on the strength of "
                  "confusion", len(launches(engine)) == 1,
                  len(launches(engine)))
    checks.expect("and still no candidate", published_candidates(case) == [],
                  published_candidates(case))

    # (2) POSITIVE ABSENCE: the engine's own sentence, naming THIS identity.
    confused["on"] = False
    engine.__dict__.setdefault("gone", set()).add(runtime)
    engine.runtime_id = None
    a_job, a_control, a_composed = composing(case, "stage-runtime-gone",
                                             engine)
    absent_settled = sweeps(case, a_job, a_composed, ticks=12)
    gone = attempt_runtime_of(a_control, attempt)
    checks.expect("POSITIVE ABSENCE reaches the end of the runtime axis",
                  gone["execution_runtime"] == "destroyed",
                  gone["execution_runtime"])
    checks.expect("attributed to the EXACT runtime identity, which is not "
                  "erased", gone["runtime_id"] == runtime, gone)
    checks.expect("and to the exact attempt", gone["attempt_id"] == attempt,
                  gone["attempt_id"])
    checks.expect("the assignment is still this attempt's own",
                  gone["assignment"] == live["assignment"],
                  gone["assignment"])
    checks.expect("the stage cannot falsely complete: it is exceptional",
                  absent_settled.get("implementation") == "exceptional",
                  absent_settled)
    checks.expect("the successors stay blocked",
                  absent_settled.get("review") == "blocked"
                  and absent_settled.get("integration") == "blocked",
                  absent_settled)
    checks.expect("no replacement container was started for the dead one",
                  len(launches(engine)) == 1, len(launches(engine)))
    checks.expect("and the authoritative proposal inventory is still empty",
                  published_candidates(case) == [], published_candidates(case))
    return {"identities": dict(identities(case),
                               implementation_attempt=attempt,
                               runtime_id=runtime),
            "live_before": live, "unknown": {"axis": held,
                                             "states": unknown_settled},
            "absence": {"axis": gone, "states": absent_settled},
            "injected": "one engine, two answers: `status 1` with prose that "
                        "names no container (unknown), then the engine's own "
                        "`No such container: <id>` for this exact identity "
                        "(absence), both at the `engine_run` boundary"}


# -- scenario 3 --------------------------------------------------------------

def same_authority_recovery_retains_ownership(case, checks):
    """A restart on the same disposable instance keeps ONE authority and the
    EXACT ownership.

    The review was right that two writable handles plus one refused claim prove
    claim exclusivity and not this. What is asserted here instead: the
    authority identity gate, ownership identical member by member across the
    recomposition, the committed assignment history unextended by the
    recovery, and -- the property two live compositions actually have -- that
    sweeping the OLD composition after the restart produces no duplicate
    effect, because every act is journalled under an identity its owner
    derives.
    """
    from baton_v12.authority import Authority
    from baton_v12.authority.errors import Refusal
    from baton_v12.job_manager import submit as submit_jobs
    from baton_v12.worker_manager import attempt_runtime_of
    from tools.dossier_command import AUTHORITY_STORE_KIND

    engine = case.quiescing()
    case.engine = engine
    job, control, composed = composing(case, "stage-own", engine)
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    attempt = stage_of(case, job, composed)["attempt_id"]
    store, uuid = case.authority_path, case.config["authority_uuid"]

    reader = Authority.open_readonly(store, expected_authority_uuid=uuid)
    try:
        before = {"assignment": reader.assignment_of(case.work),
                  "events": reader.assignment_events(case.work),
                  "work": reader.project_work(case.work)}
    finally:
        reader.dispose()
    runtime_before = attempt_runtime_of(control, attempt)
    checks.expect("one live assignment is held before the recovery",
                  before["assignment"] is not None, before["assignment"])

    # THE AUTHORITY IDENTITY GATE, which is what "same authority" is checked
    # by -- and it is a read refusing, not a file lock.
    wrong = None
    try:
        Authority.open_readonly(store,
                                expected_authority_uuid="f" * 32).dispose()
    except (Refusal, Exception) as refusal:            # noqa: BLE001
        wrong = f"{type(refusal).__name__}: {refusal}"
    checks.expect("a composition naming another authority is refused",
                  wrong is not None and "f" * 32 in wrong, wrong)

    # THE RESTART.
    fresh_job, fresh_control, fresh = composing(case, "stage-own-again",
                                               engine)
    recovered = fresh.recover(now=_now())
    settled = sweeps(case, fresh_job, fresh, ticks=8)
    reader = Authority.open_readonly(store, expected_authority_uuid=uuid)
    try:
        after = {"assignment": reader.assignment_of(case.work),
                 "events": reader.assignment_events(case.work),
                 "work": reader.project_work(case.work)}
        stored = Authority.stored_identity(store)
    finally:
        reader.dispose()
    checks.expect("the recovery kept the EXACT assignment",
                  after["assignment"] == before["assignment"],
                  {"before": before["assignment"],
                   "after": after["assignment"]})
    checks.expect("including the participant and generation",
                  (after["assignment"] or {}).get("participant")
                  == (before["assignment"] or {}).get("participant")
                  and (after["assignment"] or {}).get("generation")
                  == (before["assignment"] or {}).get("generation"),
                  after["assignment"])
    checks.expect("the committed assignment history is not extended by the "
                  "recovery", after["events"] == before["events"],
                  {"before": len(before["events"]),
                   "after": len(after["events"])})
    checks.expect("the Work's route and handler are unchanged",
                  (after["work"]["route"], after["work"]["handler"])
                  == (before["work"]["route"], before["work"]["handler"]),
                  {"before": before["work"]["route"],
                   "after": after["work"]["route"]})
    checks.expect("the runtime ownership is unchanged",
                  attempt_runtime_of(fresh_control, attempt)
                  == runtime_before, attempt_runtime_of(fresh_control,
                                                        attempt))
    checks.note("the manager's own restart recovery", recovered)

    # TWO LIVE COMPOSITIONS, ONE SET OF DURABLE ACTS. The old object is swept
    # again AFTER the restart: a second active manager must not duplicate.
    old_launches = len(launches(engine))
    old_settled = sweeps(case, job, composed, ticks=6)
    checks.expect("sweeping the OLD composition after the restart starts no "
                  "second container", len(launches(engine)) == old_launches,
                  len(launches(engine)))
    checks.expect("and prepares no second attempt",
                  sorted(case.worker_of(composed, "implementation")
                         .stage._prepared) == [attempt])
    checks.expect("both compositions agree on the stage state",
                  old_settled.get("implementation")
                  == settled.get("implementation"),
                  {"old": old_settled, "fresh": settled})
    reader = Authority.open_readonly(store, expected_authority_uuid=uuid)
    try:
        checks.expect("and the ownership is STILL the same one assignment",
                      reader.assignment_of(case.work) == before["assignment"],
                      reader.assignment_of(case.work))
    finally:
        reader.dispose()

    # THE CONNECTION TO W321688'S ACCEPTED RECOVERY SET, proved rather than
    # cited: the two members `dossier recovery-manifest`/`recovery-check`
    # certify about a restored authority store are read here, through the same
    # supported probe those verbs use, from THIS fixture's own store.
    checks.expect("this instance's store answers the kind the accepted "
                  "recovery check requires",
                  (stored or {}).get("store_kind") == AUTHORITY_STORE_KIND,
                  stored)
    checks.expect("and this deployment's own authority UUID",
                  (stored or {}).get("authority_uuid") == uuid, stored)
    return {"identities": dict(identities(case),
                               implementation_attempt=attempt),
            "ownership_before": before["assignment"],
            "ownership_after": after["assignment"],
            "assignment_events": len(after["events"]),
            "wrong_authority_refusal": wrong,
            "stored_identity": stored,
            "recover_answer": recovered,
            "not_claimed": "This is not a proof that the operating system or "
                           "SQLite prevents a second writer. The enforcement "
                           "measured here is the authority identity gate, the "
                           "owner-derived operation identities that make a "
                           "second live composition idempotent, and the claim "
                           "compare-and-swap recorded in matrix-325037 "
                           "scenario 6. Accounting positively for a previous "
                           "instance's runtimes remains an operator act, as "
                           "W321688's own recovery check says."}


# -- scenario 4 --------------------------------------------------------------

def correction_lineage_through_public_readers(case, checks):
    """A changes-requested round, resolved through the HISTORICAL readers.

    `_prepared` is a private inventory and the review was right that it is not
    a lineage proof. `writer_for_attempt`, `review_for_attempt`,
    `checkpoint_of` and `line_of` answer from the attempt and its generation,
    which do not move -- so the predecessor candidate, the review that ended
    it and the successor's base can each be read back and compared.
    """
    from baton_v12.worker_manager import assignment_of, review_cycles

    held = case.reviewed(verdict="changes-requested")
    case.drive(held.job, held.composed, "implementation", "waiting", ticks=16)
    control = held.control
    first, review = held.attempt_id, held.review
    prepared = sorted(case.worker_of(held.composed,
                                     "implementation").stage._prepared)
    successors = [one for one in prepared if one != first]
    checks.expect("the correction round prepared exactly one successor "
                  "attempt and retained the first", len(successors) == 1
                  and first in prepared, prepared)
    successor = successors[0]

    generations = {name: assignment_of(control, one)["generation"]
                   for name, one in (("first", first), ("review", review),
                                     ("successor", successor))}
    checks.note("the three assignment generations", generations)
    checks.expect("each round is its own generation of the SAME Work",
                  sorted(generations.values()) == [1, 2, 3]
                  and {assignment_of(control, one)["work_id"]
                       for one in (first, review, successor)}
                  == {case.work}, generations)
    checks.expect("the reviewer is not the implementer",
                  assignment_of(control, review)["participant"]
                  != assignment_of(control, first)["participant"],
                  {"review": assignment_of(control, review)["participant"],
                   "first": assignment_of(control, first)["participant"]})

    writer = review_cycles.writer_for_attempt(control, attempt_id=first,
                                              generation=generations["first"])
    attached = review_cycles.review_for_attempt(
        control, attempt_id=review, generation=generations["review"])
    successor_writer = review_cycles.writer_for_attempt(
        control, attempt_id=successor, generation=generations["successor"])
    checks.expect("the first attempt's line writer is readable from the "
                  "attempt alone", writer is not None, writer)
    checks.expect("the review attachment is readable from the review attempt "
                  "alone", attached is not None, attached)
    checks.expect("the successor's writer is readable too",
                  successor_writer is not None, successor_writer)

    named = held.composed.deployment.line()
    line = review_cycles.line_of(control, named["line_id"])
    checks.expect("all three are on the deployment's own ONE line",
                  {writer["line_id"], attached["line_id"],
                   successor_writer["line_id"]} == {line["line_id"]},
                  {"line": line["line_id"],
                   "writer": writer["line_id"],
                   "review": attached["line_id"],
                   "successor": successor_writer["line_id"]})
    checks.expect("the line is bound to this Work",
                  line["work_id"] == case.work, line["work_id"])

    checkpoint = review_cycles.checkpoint_of(control,
                                             attached["checkpoint_id"])
    checks.expect("the REVIEWED candidate was written by the FIRST attempt's "
                  "writer", checkpoint["writer_id"] == writer["writer_id"],
                  {"checkpoint_writer": checkpoint["writer_id"],
                   "first_writer": writer["writer_id"]})
    checks.expect("it is frozen", checkpoint["state"] == "frozen",
                  checkpoint["state"])
    checks.expect("and it is the first revision of this line",
                  checkpoint["revision"] == 1
                  and checkpoint["line_id"] == line["line_id"], checkpoint)
    checks.expect("the SUCCESSOR attempt is based on exactly that reviewed "
                  "candidate",
                  successor_writer["based_checkpoint_id"]
                  == attached["checkpoint_id"],
                  {"successor_base":
                   successor_writer["based_checkpoint_id"],
                   "reviewed": attached["checkpoint_id"]})
    checks.expect("the review attachment is ENDED by the verdict rather than "
                  "still open", attached["state"] == "ended",
                  attached["state"])
    checks.expect("the reviewer's own identity is on the attachment",
                  attached["reviewer_participant"]
                  == assignment_of(control, review)["participant"],
                  attached["reviewer_participant"])
    checks.expect("the first writer was revoked when its round ended",
                  writer["state"] != "active", writer["state"])
    checks.expect("and the successor's writer is the active one",
                  successor_writer["state"] == "active",
                  successor_writer["state"])
    candidates = published_candidates(case)
    checks.expect("the first round's candidate still stands in the "
                  "AUTHORITATIVE inventory, and no second one was published",
                  len(candidates) == 1, candidates)
    states = case.states(held.job, held.composed)
    checks.expect("the correction reopened the implementation stage and "
                  "blocked the review rather than completing it",
                  states.get("review") == "blocked"
                  and states.get("implementation") in ("claimed", "waiting"),
                  states)
    return {"identities": dict(identities(case), first_attempt=first,
                               review_attempt=review,
                               successor_attempt=successor),
            "generations": generations,
            "lineage": {"first_writer": writer, "review_attachment": attached,
                        "reviewed_checkpoint": checkpoint,
                        "successor_writer": successor_writer,
                        "line": {k: line[k] for k in
                                 ("line_id", "work_id", "profile_name",
                                  "declared_base")}},
            "proposals": candidates, "states": states}


# -- scenario 5 --------------------------------------------------------------

def explicit_diagnostic_ownership(case, checks):
    """WHO owns a failed turn -- asked of the Authority, not of a projection.

    My previous handoff and `../matrix-325138/` concluded that nothing creates
    an eligible diagnostic assignment or names a diagnostic principal, and
    called that a bounded product gap. The review refused that inference from
    missing projection keys, and it was right: THE PATH EXISTS. Asked of the
    Authority's own route, handler, claim and creation surfaces, a failed
    stage's Work can be given an explicit diagnostic handler and CLAIMED by
    it, which is an eligible assignment naming a diagnostic principal. The gap
    claim is withdrawn; what remains true is narrower and is a deployment
    policy rather than a missing operation.
    """
    from baton_v12.authority import Authority
    from baton_v12.job_manager import submit as submit_jobs
    from baton_v12.job_manager.ending import pending_endings

    engine = case.quiescing()
    case.engine = engine
    job, control, composed = composing(case, "stage-diag", engine)
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    attempt = stage_of(case, job, composed)["attempt_id"]
    roots = case.mounted(composed, "implementation", attempt)
    # THE PROVIDER FAILS, which is the deployment's own seam and is labelled.
    turned = case.turn(control, "implementation", attempt, roots, edits={},
                       status=1)
    checks.expect("the worker turn itself completed its exchange",
                  turned == 0, turned)
    settled = sweeps(case, job, composed, ticks=12)
    stage = stage_of(case, job, composed)
    checks.expect("the stage is exceptional and cannot falsely complete",
                  stage["state"] == "exceptional", stage["state"])
    checks.expect("the AUTHORITATIVE proposal inventory is empty, which is "
                  "the inventory and not a missing projection member",
                  published_candidates(case) == [], published_candidates(case))
    checks.expect("the successors stay blocked",
                  settled.get("review") == "blocked", settled)
    checks.expect("pending_endings offers nothing for it either",
                  list(pending_endings(job)) == [],
                  list(pending_endings(job)))
    members = sorted(stage)
    checks.note("every member the status projection gives this stage", members)
    checks.expect("the projection itself names no diagnostic owner -- which "
                  "is a fact about the PROJECTION and proves nothing about "
                  "the Authority's surfaces",
                  not [one for one in members
                       if one in ("owner", "diagnostic_owner", "assignee",
                                  "principal", "eligible_for", "awaiting")],
                  members)

    store, uuid = case.authority_path, case.config["authority_uuid"]
    authority = Authority.open(store, expected_authority_uuid=uuid)
    answer = {}
    try:
        work = authority.project_work(case.work)
        answer["work_after_failure"] = {k: work.get(k) for k in
                                        ("status", "phase", "route",
                                         "handler", "gate", "outcome",
                                         "scope")}
        checks.expect("the Work is open with no handler after the failed "
                      "turn", work["status"] == "open"
                      and work["handler"] is None, answer["work_after_failure"])
        checks.expect("no outcome was invented for it",
                      work["outcome"] is None, work["outcome"])
        checks.expect("and no live assignment is left behind",
                      authority.assignment_of(case.work) is None,
                      authority.assignment_of(case.work))

        # THE SUPPORTED PATH, (a): the Work's own route gains an explicit
        # diagnostic handler, and the diagnostician claims it.
        route = work["route"]
        authority.add_route_handler(route, "baton.diagnostician")
        session = authority.session("baton.diagnostician")
        claimed = session.claim({"work_id": case.work,
                                 "operation_id": "w325035-diagnostic-claim"})
        answer["diagnostic_claim"] = claimed
        assignment = authority.assignment_of(case.work)
        answer["diagnostic_assignment"] = assignment
        checks.expect("an ELIGIBLE DIAGNOSTIC ASSIGNMENT exists and names the "
                      "diagnostic participant",
                      assignment is not None
                      and assignment["participant"] == "baton.diagnostician",
                      assignment)
        checks.expect("the assignment is this Work's own",
                      assignment["work_ref"]["work_id"] == case.work
                      and assignment["work_ref"]["authority_uuid"] == uuid,
                      assignment["work_ref"])
        checks.expect("the decision names the diagnostic PRINCIPAL",
                      claimed["decision"]["principal"]
                      == "principal:baton.diagnostician",
                      claimed["decision"])
        held = authority.project_work(case.work)
        answer["work_after_diagnostic_claim"] = {
            k: held.get(k) for k in ("status", "phase", "route", "handler")}
        checks.expect("and the Work is now actively held by the diagnostic "
                      "owner", held["handler"] == "baton.diagnostician"
                      and held["phase"] == "active",
                      answer["work_after_diagnostic_claim"])
        checks.expect("an identical claim replays rather than taking a second "
                      "one",
                      session.claim({"work_id": case.work,
                                     "operation_id":
                                     "w325035-diagnostic-claim"})
                      == claimed)

        # AND THE CAPABILITY BOUNDARY IS REAL: naming the failure on the Work
        # is a configured actor's act, not the holder's.
        refused = None
        try:
            session.label_work({"work_id": case.work,
                                "label": "diagnosis-needed",
                                "operation_id": "w325035-diagnostic-label"})
        except Exception as refusal:                     # noqa: BLE001
            refused = f"{type(refusal).__name__}: {refusal}"
        answer["label_without_capability"] = refused
        checks.expect("labelling the Work without the capability is refused",
                      refused is not None
                      and "manage-work-labels" in refused, refused)
        authority.grant_capability("baton.diagnostician", "manage-work-labels",
                                   scope=work["scope"])
        session.label_work({"work_id": case.work, "label": "diagnosis-needed",
                            "operation_id": "w325035-diagnostic-label"})
        labels = authority.labels_of(case.work)
        answer["labels"] = labels
        checks.expect("and accepted once the capability is granted",
                      "diagnosis-needed" in labels, labels)
        checks.expect("so the failed Work is DISCOVERABLE by label",
                      case.work in [one if isinstance(one, str)
                                    else one.get("work_id")
                                    for one in authority.works_with_labels(
                                        all_of=("diagnosis-needed",))],
                      authority.works_with_labels(
                          all_of=("diagnosis-needed",)))

        # THE SUPPORTED PATH, (b): a separate diagnostic Work on its own
        # route, for a deployment that must leave the failed Work where it is.
        authority.add_route_handler("diagnosis", "baton.diagnostician")
        created = authority.create_work(
            DIAGNOSTIC_WORK, "diagnosis",
            operation_id="w325035-diagnostic-work",
            labels=("diagnosis-needed",))
        answer["diagnostic_work"] = created
        checks.expect("its creation is attributable",
                      authority.work_creation(DIAGNOSTIC_WORK) is not None,
                      authority.work_creation(DIAGNOSTIC_WORK))
        # AND ONE PRINCIPAL STILL HOLDS ONE CLAIM. The diagnostician is
        # already holding the failed Work, so it may not also hold the
        # dedicated diagnostic one -- which is the serial-allocation rule
        # rather than anything about diagnosis, and it is why a deployment
        # choosing path (b) staffs it with its own participant.
        serial = None
        try:
            session.claim({"work_id": DIAGNOSTIC_WORK,
                           "operation_id": "w325035-diagnostic-work-claim"})
        except Exception as refusal:                     # noqa: BLE001
            serial = f"{type(refusal).__name__}: {refusal}"
        answer["second_claim_by_one_principal"] = serial
        checks.expect("one principal still holds ONE active claim",
                      serial is not None
                      and "ONE active claim" in serial, serial)
        authority.add_route_handler("diagnosis", "baton.diagnostician-standby")
        standby = authority.session("baton.diagnostician-standby")
        standby.claim({"work_id": DIAGNOSTIC_WORK,
                       "operation_id": "w325035-diagnostic-standby-claim"})
        answer["diagnostic_work_assignment"] = \
            authority.assignment_of(DIAGNOSTIC_WORK)
        checks.expect("a dedicated diagnostic Work on its own route is "
                      "created and claimed by its own diagnostic owner",
                      answer["diagnostic_work_assignment"]["participant"]
                      == "baton.diagnostician-standby",
                      answer["diagnostic_work_assignment"])
        checks.expect("while the failed Work stays with the first diagnostic "
                      "owner", authority.assignment_of(case.work)
                      ["participant"] == "baton.diagnostician",
                      authority.assignment_of(case.work))
    finally:
        authority.dispose()

    answer.update({
        "identities": dict(identities(case), implementation_attempt=attempt),
        "stage": stage, "stage_members": members, "states": settled,
        "withdrawn": "The claim in ../matrix-325138/scenario-2 and in my "
                     "18:16 handoff -- that nothing creates an eligible "
                     "diagnostic assignment or names a diagnostic principal, "
                     "and that this is a bounded product gap -- is WITHDRAWN. "
                     "It was inferred from missing projection keys, which the "
                     "review correctly refused as a basis. Asked of the "
                     "Authority's own surfaces, the path exists and is driven "
                     "above.",
        "established": "An explicit diagnostic owner is reached by supported "
                       "native coordination: the operator names a diagnostic "
                       "handler for the Work's route (or creates a diagnostic "
                       "Work on its own route), the diagnostic participant "
                       "CLAIMS it, and the resulting assignment names that "
                       "participant and its principal. Capability-bounded "
                       "labelling makes the failure discoverable.",
        "remains_true": "What the projection does NOT do is route this "
                        "automatically: an exceptional stage is a terminal "
                        "state an operator must notice, and nothing offers it "
                        "to a diagnostician on its own. That is the selected "
                        "owner policy -- a deployment act -- and NOT a "
                        "missing product operation. No product defect is "
                        "claimed from this scenario."})
    return answer


# -- scenario 6 --------------------------------------------------------------

def an_empty_turn_cannot_falsely_complete(case, checks):
    """A provider that EXITS ZERO and writes nothing.

    The other half of the no-candidate outcome, and the harder half: a failing
    provider announces itself, while one that succeeds and produces nothing is
    exactly what a falsely-completing pipeline would mistake for a result.
    matrix-325037 observed this without asserting it; it is asserted here.
    """
    from baton_v12.job_manager import submit as submit_jobs
    from baton_v12.worker_manager import frozen_output_of

    engine = case.quiescing()
    case.engine = engine
    job, control, composed = composing(case, "stage-empty", engine)
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    attempt = stage_of(case, job, composed)["attempt_id"]
    roots = case.mounted(composed, "implementation", attempt)
    # THE INJECTION: the provider is invoked, succeeds, and edits nothing.
    turned = case.turn(control, "implementation", attempt, roots, edits={},
                       status=0)
    checks.expect("the worker turn itself completed its exchange",
                  turned == 0, turned)
    settled = sweeps(case, job, composed, ticks=12)
    checks.expect("the stage is exceptional rather than completed",
                  settled.get("implementation") == "exceptional", settled)
    checks.expect("the successors stay blocked",
                  settled.get("review") == "blocked"
                  and settled.get("integration") == "blocked", settled)
    checks.expect("the AUTHORITATIVE proposal inventory holds no candidate",
                  published_candidates(case) == [], published_candidates(case))
    frozen = frozen_output_of(control, attempt)
    checks.note("the frozen output of the empty turn",
                None if frozen is None else frozen.get("disposition"))
    checks.expect("no completed result was frozen for it",
                  frozen is None or frozen.get("disposition") != "completed",
                  frozen)
    checks.expect("and no second attempt was offered",
                  sorted(case.worker_of(composed, "implementation")
                         .stage._prepared) == [attempt])
    return {"identities": dict(identities(case),
                               implementation_attempt=attempt),
            "states": settled,
            "frozen_output": frozen,
            "injected": "the provider exits 0 and writes no edit"}


# -- scenario 7 --------------------------------------------------------------

def stale_and_wrong_principal_refuse(case, checks):
    """Two refusals, driven while an assignment is LIVE, with the state
    checked afterwards.

    matrix-325037 recorded the refusal strings; what it never checked is that
    nothing moved. Both are checked here, because a refusal that had already
    changed something would be the worse defect.
    """
    from baton_v12.authority import Authority
    from baton_v12.job_manager import submit as submit_jobs

    engine = case.quiescing()
    case.engine = engine
    job, control, composed = composing(case, "stage-refusals", engine)
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    store, uuid = case.authority_path, case.config["authority_uuid"]
    authority = Authority.open(store, expected_authority_uuid=uuid)
    answer = {}
    try:
        live = authority.assignment_of(case.work)
        checks.expect("an assignment is LIVE, which is the only point at "
                      "which either question is meaningful",
                      live is not None, live)
        before = authority.project_work(case.work)
        events_before = authority.assignment_events(case.work)
        refusals = {}
        for what, participant, operands in (
                ("a stale episode", live["participant"],
                 {"expect": dict(live, generation=(live["generation"] or 1)
                                 + 7),
                  "operation_id": "w325035-stale", "reason": "stale"}),
                ("a wrong principal", "baton.gemini",
                 {"expect": live, "operation_id": "w325035-wrong-principal",
                  "reason": "not mine"})):
            caught = None
            try:
                authority.session(participant).cancel(operands)
            except Exception as refusal:                 # noqa: BLE001
                caught = f"{type(refusal).__name__}: {refusal}"
            refusals[what] = caught
            checks.expect(f"{what} is REFUSED", caught is not None, caught)
            held = authority.project_work(case.work)
            checks.expect(f"and nothing moved: the Work is unchanged after "
                          f"{what}",
                          {k: held.get(k) for k in ("status", "phase",
                                                    "route", "handler",
                                                    "outcome")}
                          == {k: before.get(k) for k in ("status", "phase",
                                                         "route", "handler",
                                                         "outcome")},
                          held)
            checks.expect(f"the live assignment is still the same one after "
                          f"{what}",
                          authority.assignment_of(case.work) == live,
                          authority.assignment_of(case.work))
            checks.expect(f"and no assignment event was written by {what}",
                          authority.assignment_events(case.work)
                          == events_before,
                          len(authority.assignment_events(case.work)))
        answer["refusals"] = refusals
        checks.expect("the stale refusal names the staleness",
                      "stale" in (refusals["a stale episode"] or "").lower(),
                      refusals["a stale episode"])
        checks.expect("the wrong-principal refusal names BOTH identities",
                      "baton.gemini" in (refusals["a wrong principal"] or "")
                      and live["participant"]
                      in (refusals["a wrong principal"] or ""),
                      refusals["a wrong principal"])
        answer["work_unchanged"] = {k: before.get(k) for k in
                                    ("status", "phase", "route", "handler",
                                     "outcome")}
        answer["live_assignment"] = live
    finally:
        authority.dispose()
    answer["identities"] = identities(case)
    return answer


# -- scenario 8 --------------------------------------------------------------

def cancellation_closure_and_claim_exclusivity(case, checks):
    """A live cancellation, an honest non-satisfying ending, and what the one
    writable authority actually enforces.

    Ported from matrix-325037 (which recorded these without checking them) and
    from matrix-325138's corrected cancellation, into one asserting scenario
    so the finite matrix is complete in a single run.
    """
    import io
    from contextlib import redirect_stderr, redirect_stdout

    from baton_v12.authority import Authority
    from baton_v12.job_manager import submit as submit_jobs
    from tools import stack_command

    engine = case.quiescing()
    case.engine = engine
    job, control, composed = composing(case, "stage-ending", engine)
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    store, uuid = case.authority_path, case.config["authority_uuid"]
    authority = Authority.open(store, expected_authority_uuid=uuid)
    answer = {}
    try:
        live = authority.assignment_of(case.work)
        checks.expect("an assignment is LIVE for all of this", live is not None,
                      live)

        # TWO WRITABLE HANDLES, ONE CLAIM, asked while the claim is held. The
        # file is not the enforcement; the claim's compare-and-swap is, and
        # matrix-325037 recorded that without checking it.
        second = Authority.open(store, expected_authority_uuid=uuid)
        try:
            racing = None
            try:
                second.session("baton.reviewer").claim(
                    {"work_id": case.work, "operation_id": "w325035-race-2"})
            except Exception as refusal:                 # noqa: BLE001
                racing = f"{type(refusal).__name__}: {refusal}"
            answer["second_claim_through_a_second_writable_handle"] = racing
            checks.expect("a second live claim through a second WRITABLE "
                          "handle is refused", racing is not None
                          and "claimed" in racing, racing)
            checks.expect("and the holder is unchanged",
                          second.assignment_of(case.work) == live,
                          second.assignment_of(case.work))
        finally:
            second.dispose()

        # A READ-ONLY HANDLE PERFORMS NOTHING.
        reader = Authority.open_readonly(store, expected_authority_uuid=uuid)
        try:
            refused = None
            try:
                reader.session("baton.claude").close(
                    {"work_id": case.work, "operation_id": "w325035-readonly",
                     "outcome": "cancelled", "rationale": "must refuse"})
            except Exception as refusal:                 # noqa: BLE001
                refused = f"{type(refusal).__name__}: {refusal}"
            answer["read_only_transition"] = refused
            checks.expect("a read-only handle refuses every transition",
                          refused is not None, refused)
            checks.expect("and the Work is untouched by the attempt",
                          reader.assignment_of(case.work) == live,
                          reader.assignment_of(case.work))
        finally:
            reader.dispose()

        # THE CANCELLATION, driven while that same assignment is live.
        answer["live_before_cancel"] = live
        answer["cancelled"] = authority.session(live["participant"]).cancel(
            {"expect": live, "operation_id": "w325035-cancel",
             "reason": "W325035 matrix: live cancellation"})
        checks.expect("the cancellation answered a result",
                      bool(answer["cancelled"]), answer["cancelled"])
        after = authority.project_work(case.work)
        answer["work_after_cancel"] = {k: after.get(k) for k in
                                       ("status", "phase", "handler",
                                        "outcome", "gate")}
        checks.expect("the handler is gone", after["handler"] is None,
                      after["handler"])
        checks.expect("a cancelled ASSIGNMENT is not a cancelled WORK: it is "
                      "still open", after["status"] == "open",
                      after["status"])
        checks.expect("and no outcome was recorded by the cancellation",
                      after["outcome"] is None, after["outcome"])
        checks.expect("no live assignment remains",
                      authority.assignment_of(case.work) is None)
        checks.expect("the cancellation is in the assignment events",
                      any("cancel" in json.dumps(one, default=str)
                          for one in authority.assignment_events(case.work)))

        # AND THE RUNTIME GATE STILL STANDS, which is the part I had not
        # looked at: cancelling the assignment does not discharge the
        # quiescence gate, so the Work is not immediately re-claimable by
        # anybody. A matrix that asserted "cancel, then claim again" would
        # have been asserting the opposite of what this product does.
        blocked = None
        try:
            authority.session("baton.claude").claim(
                {"work_id": case.work,
                 "operation_id": "w325035-reclaim-after-cancel"})
        except Exception as refusal:                     # noqa: BLE001
            blocked = f"{type(refusal).__name__}: {refusal}"
        answer["reclaim_after_cancel"] = blocked
        answer["gate_after_cancel"] = after.get("gate")
        checks.expect("a re-claim after the cancellation is refused while the "
                      "runtime-quiescence gate stands",
                      blocked is not None and "blocked" in blocked, blocked)
        checks.expect("and the gate the refusal names is the runtime one",
                      "runtime-quiescence" in json.dumps(
                          [after.get("gate"), blocked], default=str),
                      after.get("gate"))

        scope = authority.project_work(case.work)["scope"]
        authority.grant_capability("baton.slaw", "close", scope=scope)
        live_now = authority.assignment_of(case.work)
    finally:
        authority.dispose()

    # THE OWNER'S OWN INSTALLED COMMAND, with the operator's rationale.
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = stack_command.main([
            "disposition", "close", "--authority-store", store,
            "--authority-uuid", uuid, "--participant", "baton.slaw",
            "--work", case.work, "--outcome", "non-satisfying",
            "--rationale", "W325035 matrix: honest non-satisfying ending",
            "--operation-id", "w325035-close",
            "--expect-assignment", json.dumps(live_now)]
            if live_now is not None else [
            "disposition", "close", "--authority-store", store,
            "--authority-uuid", uuid, "--participant", "baton.slaw",
            "--work", case.work, "--outcome", "non-satisfying",
            "--rationale", "W325035 matrix: honest non-satisfying ending",
            "--operation-id", "w325035-close"])
    answer["close"] = {"exit": code, "stderr": err.getvalue().strip(),
                       "answer": json.loads(out.getvalue())
                       if out.getvalue().strip() else None}
    checks.expect("the owner's installed non-satisfying closure is accepted",
                  code == 0, answer["close"])
    reader = Authority.open_readonly(store, expected_authority_uuid=uuid)
    try:
        closed = reader.project_work(case.work)
        answer["work_after_close"] = {k: closed.get(k) for k in
                                      ("status", "phase", "outcome",
                                       "rationale")}
        checks.expect("the Work is closed", closed["status"] == "closed",
                      closed["status"])
        checks.expect("its outcome is non-satisfying, which is not an "
                      "acceptance", closed["outcome"] == "non-satisfying",
                      closed["outcome"])
        checks.expect("and the operator's own rationale is what was recorded",
                      "honest non-satisfying ending"
                      in json.dumps(closed.get("rationale"), default=str),
                      closed.get("rationale"))
        checks.expect("no receipt was written by any of it",
                      published_candidates(case) == [],
                      published_candidates(case))
    finally:
        reader.dispose()
    answer["identities"] = identities(case)
    return answer


SCENARIOS = (
    ("0-harness-self-check", harness_self_check, SELF_CHECK,
     "a deliberately false expectation; this scenario MUST fail, and it must "
     "fail with THIS check's own CheckFailed"),
    ("1-lost-launch-reply-across-restart", lost_launch_reply_across_restart,
     None,
     "a committed start whose reply is dropped after the engine really "
     "started the container, then a restart over the SAME engine state"),
    ("2-unknown-runtime-then-positive-absence",
     unknown_runtime_then_positive_absence, None,
     "one engine answering `status 1` with prose naming no container, then "
     "its own absence sentence naming this exact identity"),
    ("3-same-authority-recovery-retains-ownership",
     same_authority_recovery_retains_ownership, None,
     "a restart on the same disposable instance, a wrong authority UUID, and "
     "the old composition swept again afterwards"),
    ("4-correction-lineage-through-public-readers",
     correction_lineage_through_public_readers, None,
     "a changes-requested verdict, resolved through writer_for_attempt / "
     "review_for_attempt / checkpoint_of / line_of"),
    ("5-explicit-diagnostic-ownership", explicit_diagnostic_ownership, None,
     "a provider turn exiting 1, then the Authority's own route, claim, label "
     "and creation surfaces asked who may own the diagnosis"),
    ("6-an-empty-turn-cannot-falsely-complete",
     an_empty_turn_cannot_falsely_complete, None,
     "a provider that exits 0 and writes nothing"),
    ("7-stale-and-wrong-principal-refuse", stale_and_wrong_principal_refuse,
     None,
     "a stale episode and a wrong principal, both driven against a live "
     "assignment, with the state checked after each refusal"),
    ("8-cancellation-closure-and-claim-exclusivity",
     cancellation_closure_and_claim_exclusivity, None,
     "a live cancellation, two writable handles racing one claim, a read-only "
     "handle, and the owner's installed non-satisfying closure"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    place.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    answers, unexpected, passed = [], 0, 0

    print("W325035 matrix, completed:")
    for name, body, intended, injected in SCENARIOS:
        at = time.monotonic()
        checks = Checks()
        record = {"scenario": name, "injected": injected,
                  "expected_failure": intended is not None,
                  "intended_failed_check": intended,
                  "simulated": ["engine: no daemon; its answers, including "
                                "absence and confusion, injected at the "
                                "engine_run boundary",
                                "provider: injected at the adapter's own "
                                "process seam"],
                  "not_called": ["_accepted_receipts", "admit_accepted",
                                 "continue_accepted", "raw SQL",
                                 "any product-source edit"]}
        case, failure = None, None
        try:
            case = world()
            record.update(body(case, checks) or {})
            record["outcome"] = "observed"
        except CheckFailed as caught:
            record["outcome"] = "failed"
            record["failed_check"] = caught.label
            failure = caught
        except Exception:                                    # noqa: BLE001
            record["outcome"] = "failed"
            record["failure"] = traceback.format_exc()[-2000:]
        finally:
            if case is not None:
                try:
                    case.doCleanups()
                except Exception:                            # noqa: BLE001
                    record["outcome"] = "failed"
                    record["cleanup_failure"] = \
                        traceback.format_exc()[-800:]
                    failure = None
        record["checks"] = checks.document()
        record["checks_passed"] = checks.passed()
        record["seconds"] = round(time.monotonic() - at, 3)
        passed += record["checks_passed"]
        # THE SELF-CHECK MUST FAIL FOR ITS OWN REASON. Review
        # 2026-10-18T18-17-05Z: comparing `outcome == failed` alone let a
        # setup exception or a cleanup failure satisfy the expectation, so a
        # harness that could not even reach its checks reported itself sound.
        if intended is None:
            wanted = record["outcome"] == "observed"
        else:
            wanted = (record["outcome"] == "failed"
                      and isinstance(failure, CheckFailed)
                      and failure.label == intended
                      and "cleanup_failure" not in record
                      and "failure" not in record)
            record["failed_for_intended_reason"] = wanted
        if not wanted:
            unexpected += 1
            record["unexpected"] = True
        answers.append(record)
        say(place, f"scenario-{name}.json", record)
        print(f"  {name}: {record['outcome']} "
              f"({record['checks_passed']} checks passed"
              f"{', as intended' if record.get('failed_for_intended_reason') else ''}"
              f"{', UNEXPECTED' if record.get('unexpected') else ''}) "
              f"{record['seconds']}s")

    self_check = [one for one in answers
                  if one["scenario"] == "0-harness-self-check"]
    sound = bool(self_check) and self_check[0].get(
        "failed_for_intended_reason") is True
    answer = {"schema": "baton.w325035.matrix/3",
              "supersedes": "matrix-325037 and matrix-325138; both are "
                            "preserved, and the claims this run withdraws are "
                            "named in their SUPERSESSION.md files and in each "
                            "scenario's own `withdrawn`/`corrects` member",
              "boundary": "composed native Job world imported from "
                          "tests.tools.test_stage_execution and not modified; "
                          "engine answers (including absence and confusion) "
                          "injected at the engine_run boundary; provider "
                          "injected at the adapter's process seam; no product "
                          "edit, forged receipt, raw SQL, live model, live "
                          "credential or deployment",
              "repository_provenance": "nothing here mutates this "
                                       "repository's history, index or "
                                       "working tree. The imported fixture's "
                                       "own `vcs` helper does run `git` "
                                       "against its disposable temporary "
                                       "source tree under "
                                       "GIT_CONFIG_GLOBAL=/dev/null, which "
                                       "my earlier blanket 'no Git command' "
                                       "line described imprecisely.",
              "scenarios": answers,
              "checks_passed": passed,
              "observed": sum(1 for one in answers
                              if one["outcome"] == "observed"),
              "failed_as_intended": sum(
                  1 for one in answers
                  if one.get("failed_for_intended_reason")),
              "unexpected": unexpected,
              "harness_self_check_failed_for_its_own_reason": sound,
              "seconds": round(time.monotonic() - started, 3)}
    say(place, "MATRIX3.json", answer)
    print(f"checks passed {passed}, observed {answer['observed']}, "
          f"failed-as-intended {answer['failed_as_intended']}, "
          f"unexpected {unexpected}, {answer['seconds']}s")
    if not sound:
        print("REFUSED: the self-check did not fail for its own intended "
              "reason, so these checks are not checking anything")
        return 2
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
