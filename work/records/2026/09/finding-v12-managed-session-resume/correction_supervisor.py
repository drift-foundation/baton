"""ONE managed correction, BOUNDED -- then a real stop, then accounting.

W236087 item 3, answering review 2026-09-29T21-08-40Z R2. `PACKET-309306.md`
declared a 900-second total with 60 reserved inside it, two implementer and two
independent review invocations and exactly one restore, and then told an
operator to run a bare `tools.job_manager ... serve --interval 1` and press
Ctrl-C. That loop has no timer, no reserve, no invocation cap and no stop: the
numbers were prose. This program is the numbers.

WHAT IT REUSES RATHER THAN REWRITES. The accepted single-implementation
supervisor already owns the hard parts -- the deferred termination handler, the
admission gate that counts invocations and refuses another Job's stages, the
guarded shutdown steps, the cleanup journal read, the effective provider-turn
check and the atomic outcome publication. Those are ACCEPTED bytes and this
imports them; it does not copy them and it does not modify that file. What is
NOT reusable is its packet and its stop condition, and the reason is written
into it: `baseline.held_packet` refuses `implementer_invocations != 1` by name,
saying "A correction round belongs to the resume Job." This is that Job, so the
packet, the caps, the restore accounting and the four outcomes are here.

WHY THE REUSE IS PINNED. Importing another dossier's module means this program's
behaviour depends on bytes it does not own, so `BASELINE_SHA256` is the accepted
digest and a drifted `baseline.py` is refused at startup rather than silently
supervising with different rules.

WHAT DECIDES THE RESULT. Not the loop's ending. The loop produces a STOP; the
outcome is decided by what the run PRODUCED -- the reviewer's own disposition,
whether a correction round actually happened, and whether the restored use
continued the saved conversation. An unreadable disposition is UNKNOWN and the
run is HELD; it is never rounded up to acceptance.

WHAT IT NEVER DOES. It requests no cancellation it cannot attribute, manufactures
no verdict, performs no version-control act, reads no credential byte and never
retries. `bounds.retry` is `false` and there is no code path that would use it.
"""
import argparse
import hashlib
import json
import os
import sys
import time

_HERE = os.path.dirname(os.path.realpath(__file__))
_BASELINE_DIR = os.path.realpath(
    os.path.join(_HERE, "..", "finding-v12-single-implementation-proof"))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
if _BASELINE_DIR not in sys.path:
    sys.path.insert(0, _BASELINE_DIR)

import baseline                                             # noqa: E402
import correction_packet                                    # noqa: E402
from correction_packet import PacketRefusal, held_packet     # noqa: E402

# The accepted single-implementation supervisor, as reviewed and accepted under
# W239528. Measured, not copied forward from a note.
BASELINE_SHA256 = \
    "248e570d8f9d459550b0aa5e92d1674c3226fe540ba987cae916a4a334606771"

OUTCOME_SCHEMA = "baton.managed-correction-outcome/1"

# THE TWO STAGE KINDS THIS PACKET SERVES, closed and capped separately. A cap
# per kind is not a total: two implementer turns and two review turns are
# different permissions, and a run that spent both implementer invocations on
# reviews would be inside a shared budget and outside this Job.
KINDS = ("implementation", "review")

# THE DISPOSITIONS A REVIEWER MAY REACH. All three are valid results and none is
# preferred; `PREPARATION-307667.md`: "all verdicts are valid... Do not omit
# requirements to induce correction."
ACCEPTED = "accepted"
CHANGES_REQUESTED = "changes-requested"
REJECTED = "rejected"
DISPOSITIONS = (ACCEPTED, CHANGES_REQUESTED, REJECTED)

# THE OUTCOMES, kept SEPARATE. `PACKET-309306.md` section 7 stated these four
# and nothing enforced them; these are the values this program can publish, and
# the classification below is total -- there is no fall-through that becomes
# acceptance.
ACCEPTED_NO_CORRECTION = "accepted-without-correction"
CORRECTED_AND_ACCEPTED = "corrected-and-accepted"
REVIEW_REJECTED = "rejected"
UNANSWERED = "changes-requested-unanswered"
FAILED = "failed-or-unknown"


class SupervisorRefusal(PacketRefusal):
    """Refusal in this program's own words. Never a partial run's excuse."""


def _refuse(message):
    raise SupervisorRefusal(message)


def verify_baseline(*, path=None, expected=None):
    """The reused accepted machinery is the accepted machinery.

    Called before a store is opened, which is the only moment at which
    refusing is free.
    """
    whole = os.path.realpath(baseline.__file__ if path is None else path)
    held = hashlib.sha256()
    with open(whole, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 16), b""):
            held.update(block)
    found = held.hexdigest()
    want = BASELINE_SHA256 if expected is None else expected
    if found != want:
        _refuse(f"the reused single-implementation supervisor at {whole!r} is "
                f"{found} and this program is bound to {want}; its admission "
                f"gate, termination handling and cleanup read are this run's "
                f"bounds, so a changed copy is a changed bound")
    return found


# -- the restore, read from the manager's own journal ----------------------

def context_continuity(control, *, opening, restored):
    """Did the restored use CONTINUE the saved conversation, or start one?

    Read through `provider_context.context_use_of`, which is the manager's own
    journal answer -- the same reader the deterministic trace validates against.
    Two facts and no inference: one context across both uses, and a later
    generation on the restored one.

    ABSENCE IS NOT CONTINUITY. A use this cannot read leaves `continued` false
    with the reason named, because "the journal did not answer" and "the
    conversation was restored" are not the same sentence.
    """
    from baton_v12.worker_manager import provider_context

    found = {"opening": None, "restored": None, "continued": False,
             "why": None}
    try:
        found["opening"] = provider_context.context_use_of(control, opening)
        found["restored"] = provider_context.context_use_of(control, restored)
    except Exception as failure:                             # noqa: BLE001
        found["why"] = f"{type(failure).__name__}: {failure}"
        return found
    first, second = found["opening"], found["restored"]
    if first["context_id"] != second["context_id"]:
        found["why"] = (f"the restored use names context "
                        f"{second['context_id']!r} and the opening use named "
                        f"{first['context_id']!r}; a fresh conversation is not "
                        f"a restored one")
        return found
    if second["generation"] <= first["generation"]:
        found["why"] = (f"the restored use claims generation "
                        f"{second['generation']!r} and the opening use held "
                        f"{first['generation']!r}; a restore consumes a SAVED "
                        f"generation, so its own is later")
        return found
    if first["status"] not in ("ready", "retired"):
        found["why"] = (f"the opening use ended {first['status']!r}, so its "
                        f"conversation was not saved; a failed save is not "
                        f"successful reuse")
        return found
    found["continued"] = True
    return found


def stage_episodes(job, operations, job_id):
    """Every stage's episodes, IN THE ORDER THE STORE RECORDED THEM.

    Review 2026-09-29T21-41-08Z R3: my first version sorted attempt identities
    lexically and called the first one the opening attempt. "Random identity
    spelling is not time" -- the identities are not ordered and a restored
    attempt can sort before the attempt it corrects, which would have made the
    continuity check compare the wrong pair and answer confidently.

    The projection's `episodes` list carries each record's own `episode`
    number, which IS the chronology the store recorded, so ordering is read
    rather than inferred.
    """
    from baton_v12.job_manager import status

    document = status(job, operations, observed_at=baseline._moment())
    found = {}
    for entry in document["jobs"]:
        if entry["job_id"] != job_id:
            continue
        for stage in entry["stages"]:
            held = []
            for record in stage.get("episodes") or []:
                if record.get("attempt_id") is not None:
                    held.append((record.get("episode"),
                                 record["attempt_id"]))
            # THE LIVE ATTEMPT IS ALSO AN EPISODE. A stage executing its
            # correction right now has it in `attempt_id`/`episode` and not yet
            # in the history, and leaving it out would lose the very attempt
            # this run exists to account for.
            if stage.get("attempt_id") is not None \
                    and stage["attempt_id"] not in [one for _, one in held]:
                held.append((stage.get("episode"), stage["attempt_id"]))
            found[stage["kind"]] = [one for _, one in sorted(
                held, key=lambda pair: (pair[0] is None, pair[0]))]
    return found


def _ordered(recorded, admitted, kind):
    """This kind's attempts in RECORDED order, with nothing this run started lost.

    The chronology is the authority on ORDER; `admitted` is the authority on
    WHAT this run is accountable for. An attempt the projection did not answer
    for -- one that faulted before it reached the store's history -- is appended
    rather than dropped, because a runtime this process launched is this
    process's to account for either way.
    """
    order = [one for one in (recorded or []) if one in admitted]
    for attempt, held in admitted.items():
        if held == kind and attempt not in order:
            order.append(attempt)
    return order


def review_disposition(control, job, operations, job_id):
    """The reviewer's OWN verdict, through the SUPPORTED owner readers.

    Review R3, and the finding was exact: this searched
    `stage.disposition/verdict/result`, and the real projection's
    `_stage_status` emits none of them -- it emits state, episodes, exchange,
    artifacts and receipts. So a genuinely successful review answered `None`
    and every real run would have been classified `failed-or-unknown`. My
    positive test supplied a `disposition` field of my own invention, which is
    how a wrong reader passed a green test.

    THE CANONICAL VERDICT LIVES IN THE REVIEW LINE. `review_cycles` records it:
    `review_for_attempt(control, attempt_id=, generation=)` answers the
    attachment that review attempt was given, bound to the act that attached
    it, and `verdict_of(control, verdict_id)` answers the recorded disposition
    bound to all of its immutable checkpoint and reviewer evidence. Both prove
    every member against the committed act before answering, which is why they
    are the readers to use rather than a projection field.

    FAILS CLOSED, and that is the whole honesty rule in code: anything this
    cannot read answers `None`, `classify` reaches `failed-or-unknown`, and the
    run is HELD. There is no branch in which an unread verdict becomes an
    acceptance and none in which this program supplies one.
    """
    from baton_v12.worker_manager import review_cycles

    attempts = stage_episodes(job, operations, job_id).get("review") or []
    if not attempts:
        return None
    # THE LATEST REVIEW IS THE ONE THAT COUNTS, and an unread one is UNKNOWN.
    # Review 2026-09-29T22-02-59Z item 2: "do not borrow an earlier verdict to
    # characterize a later unread review." My first version walked backwards
    # through every review attempt and returned the first verdict it found, so a
    # SECOND review still executing would have been reported with the FIRST
    # review's disposition -- which is the correction round's own verdict being
    # attributed to work nobody had judged yet. Only the last recorded review
    # attempt is asked, and if it has no committed verdict the answer is
    # nothing.
    latest = attempts[-1]
    generation = assignment_generation(control, latest)
    if generation is None:
        return None
    try:
        attachment = review_cycles.review_for_attempt(
            control, attempt_id=latest, generation=generation)
    except Exception:                                        # noqa: BLE001
        return None
    if attachment is None:
        return None
    verdict = _verdict_for(control, attachment)
    return verdict if verdict in review_cycles.DISPOSITIONS else None


def assignment_generation(control, attempt_id):
    """The assignment generation THIS ATTEMPT ACTUALLY ACTIVATED.

    Review 2026-09-29T22-02-59Z item 2: my first version tried `(2, 1)` and
    took whichever answered. That guessed on an axis this packet's invocation
    caps say nothing about -- the caps bound how many ATTEMPTS are admitted,
    not which assignment generation any of them activated -- so a review
    attempt on generation 3 would have answered `None` and a run with a real
    verdict would have been reported `failed-or-unknown`. Worse, trying two
    values in order could read a DIFFERENT generation's attachment than the one
    the attempt holds.

    `attempts.assignment_of` is the durable fact: it refuses an attempt that
    never activated an assignment, and otherwise answers the generation fixed
    to it. Derived, not guessed -- and an attempt with no activated assignment
    answers nothing rather than a default.
    """
    from baton_v12.worker_manager import attempts as attempt_facts

    try:
        held = attempt_facts.assignment_of(control, attempt_id)
    except Exception:                                        # noqa: BLE001
        return None
    generation = held.get("generation") if type(held) is dict else None
    if type(generation) is not int or type(generation) is bool \
            or generation < 1:
        return None
    return generation


def _verdict_for(control, attachment):
    """The disposition recorded against one attachment, or nothing.

    The verdict identity is DERIVED from the attachment the act was named by --
    `record_verdict` journals under `VERDICT_KIND:<attachment_id>` -- so this
    asks the journal for that act and then re-reads the verdict through the
    owner's own binding rather than trusting either alone.
    """
    from baton_v12.worker_manager import review_cycles

    record = control.operation_record(
        f"{review_cycles.VERDICT_KIND}:{attachment['attachment_id']}")
    if record is None or record.get("state") != "committed":
        return None
    try:
        held = json.loads(record["result"])
    except (KeyError, TypeError, ValueError):
        return None
    verdict_id = held.get("verdict_id") if type(held) is dict else None
    if type(verdict_id) is not str or not verdict_id:
        return None
    try:
        return review_cycles.verdict_of(control, verdict_id)["disposition"]
    except Exception:                                        # noqa: BLE001
        return None


def refusal_fingerprint(refused):
    """The IDENTITY of a refusal, which is what has to repeat.

    Stage, act, attempt, code and `since` -- not the message, which carries
    timestamps, and not `observed`, which advances on every tick by design. Two
    ticks showing the same fingerprint are the same condition being met twice;
    a moved `since` is a NEW condition and starts the count again.
    """
    return sorted((one.get("stage"), one.get("act"), one.get("attempt_id"),
                   one.get("code"), one.get("since"))
                  for one in (refused or []))


def blocked_by(refused, blocked):
    """Has the SAME refusal now stood for `STALLED_TICKS` ticks?

    REVIEW 314636 R2 asked for this to be the code that runs rather than a
    shape a test rebuilds, so the counter lives here and the serving loop calls
    it. `blocked` is the caller's memory and is mutated: `at` is the last
    fingerprint seen and `count` how many ticks it has held.

    A TRANSIENT REFUSAL CLEARS. The product calls a deferral RE-ENTERABLE -- an
    ending that finishes next tick, an offer not yet accepted -- so one tick's
    reason is not a verdict on the run. A refusal that does not move is a
    different thing, and it is the only thing that stops it.
    """
    fingerprint = refusal_fingerprint(refused)
    if fingerprint and fingerprint == blocked.get("at"):
        blocked["count"] = blocked.get("count", 0) + 1
    else:
        blocked["count"] = 0
    blocked["at"] = fingerprint
    return blocked["count"] >= baseline.STALLED_TICKS


def refused_acts(job, job_id):
    """Every owed act this run's stages cannot complete, and why.

    READ THROUGH THE PRODUCT'S OWN EVIDENCE SURFACE. `projection.deferral_of`
    is the reader that answers "which act, for which attempt, why, since when,
    and whether it is still happening" -- the sentence the manager retained
    when it refused, rather than an inference from a state. Only `refused`
    entries are returned: `unavailable` says the reason could not be read,
    which is not a reason, and every other category is a condition that can
    still settle.
    """
    from baton_v12.job_manager.projection import deferral_of

    held = []
    for kind in ("implementation", "review"):
        for one in deferral_of(job, f"{job_id}/{kind}") or ():
            if (one or {}).get("category") == "refused":
                held.append(dict(one, stage=kind))
    return held


def classify(*, stop, disposition, implementations, reviews, continuity,
             cleanup_outstanding, interrupted):
    """The result, from what the run PRODUCED. Total, with no fall-through.

    THE ORDER MATTERS AND IS ARGUED. A failure or an interruption is decided
    FIRST, because a run that could not finish has no verdict to report even
    if a reviewer had already spoken; then the reviewer's own disposition; and
    acceptance-with-a-correction last, because it is the only outcome that
    makes a restore claim and therefore the only one that has to prove one.
    """
    # WHICH STOPS MEAN THE RUN CANNOT BE BELIEVED, and which are just how a
    # finished Job stops. The connected run found this: a REJECTED verdict was
    # recorded canonically and the loop then stopped `no-progress` -- correctly,
    # because a rejected Job has nothing left to advance -- and this classifier
    # turned that into `failed-or-unknown`, erasing a valid result. A rejection
    # and an acceptance are TERMINAL VERDICTS; the reviewer has spoken and the
    # loop's own stopping is not evidence against them.
    #
    # THE STOPS THAT STILL FORCE A HOLD are the ones that say the run did not
    # get to finish: the bound elapsed, an operator interrupted it, or the
    # serving loop faulted. Those are unaffected below.
    UNFINISHED = ("timed-out", "overall-bound-exceeded", "interrupted",
                  "serving-failed", "invocation-cap-refused",
                  # OWNER REROUTE 314549: an owed act the manager is being
                  # refused, tick after tick, for a reason asking again cannot
                  # satisfy. The run did not finish; it stopped because it
                  # could not proceed.
                  "conclusion-refused", "unknown")
    reasons = []
    if interrupted is not None:
        reasons.append(f"the run was interrupted: {interrupted}")
    if stop in UNFINISHED:
        reasons.append(f"the run stopped {stop!r} rather than completing its "
                       f"stages")
    elif stop not in ("completed",):
        # `exceptional` and `no-progress` are recorded as FACTS rather than as
        # failures: with a verdict in hand they describe how a decided Job
        # stopped, and without one the missing verdict below is what holds it.
        reasons.append(f"the run stopped {stop!r}; the stages were not all "
                       f"completed")
    if cleanup_outstanding:
        reasons.append("this manager cannot prove positive cleanup for "
                       + ", ".join(sorted(cleanup_outstanding)))
    if implementations < 1:
        reasons.append("no implementation runtime was ever admitted, so this "
                       "run answered nothing about the provider")
    if reviews < 1:
        reasons.append("no review invocation happened, so no independent "
                       "verdict exists")

    # AN UNREAD VERDICT IS ALWAYS UNKNOWN, and an unfinished run is always held.
    # A DECIDED one is reported as what the reviewer decided, with how it stopped
    # recorded beside it.
    if disposition is None:
        reasons.append("the reviewer's disposition could not be read, so "
                       "this run has no verdict; an unread verdict is "
                       "never an acceptance")
        return FAILED, reasons
    if interrupted is not None or stop in UNFINISHED \
            or cleanup_outstanding or implementations < 1 or reviews < 1:
        return FAILED, reasons

    if disposition == REJECTED:
        # A VALID RESULT, AND NOT A CORRECTION. `PREPARATION-307667.md`: "all
        # verdicts are valid". Nothing is manufactured from it and nothing
        # reruns.
        return REVIEW_REJECTED, reasons
    if disposition == CHANGES_REQUESTED:
        reasons.append("the reviewer requested changes and the run ended "
                       "before a second accepted implementation; the "
                       "correction was not completed")
        return UNANSWERED, reasons
    if implementations == 1:
        # ACCEPTED WITH NO CORRECTION: complete, honest, and NOT a restore
        # claim. It must not be rerun to obtain one.
        return ACCEPTED_NO_CORRECTION, reasons
    if not continuity.get("continued"):
        reasons.append(
            "a second implementation was accepted, but the restored use did "
            "not demonstrably continue the saved conversation: "
            + (continuity.get("why") or "no continuity evidence was read"))
        return FAILED, reasons
    return CORRECTED_AND_ACCEPTED, reasons


# -- the bounded run -------------------------------------------------------

def supervise(job, control, operations, packet, *, clock=None, sleep=None,
              monotonic=None, disposition=None, surveyed=None):
    """The termination handler is installed HERE, around everything.

    The shutdown is the part of a run that most needs it, so it is the part
    that keeps it. Not a SIGKILL claim: `SIGKILL` cannot be caught and nothing
    here pretends otherwise.
    """
    termination = baseline.Termination().install()
    try:
        return _supervise(job, control, operations, packet, clock=clock,
                          sleep=sleep, monotonic=monotonic,
                          termination=termination, disposition=disposition,
                          surveyed=surveyed)
    finally:
        termination.restore()


def _supervise(job, control, operations, packet, *, clock, sleep, monotonic,
               termination, disposition=None, surveyed=None):
    clock = baseline._moment if clock is None else clock
    sleep = time.sleep if sleep is None else sleep
    monotonic = time.monotonic if monotonic is None else monotonic
    disposition = review_disposition if disposition is None else disposition
    from baton_v12.job_manager import read_submission, serve, submit, sweep

    bounds = packet["bounds"]
    job_id = packet["submission"]["job_id"]
    # THE CAPS, PER KIND. Two implementer invocations is the opening and
    # EXACTLY ONE correction; two review invocations is one independent review
    # of each. The gate counts committed admissions, so a refused one does not
    # retire a permission nobody used.
    gate = baseline.AdmissionGate(
        operations, job_id=job_id,
        caps={"implementation": bounds["implementer_invocations"],
              "review": bounds["review_invocations"]})
    started = monotonic()
    # THE RESERVE IS INSIDE THE TOTAL. Serving gets the total MINUS the
    # cleanup reserve, so the manager-owned stop and absence collection happen
    # within the 900 seconds rather than after them. `held_packet` already
    # refused a reserve that is not smaller than the total.
    serving_seconds = bounds["total_seconds"] - bounds["cleanup_seconds"]
    deadline = started + serving_seconds
    uncertainty, caught = [], []
    # THE SAME REFUSAL, TICK AFTER TICK, is what makes an owed act hopeless
    # rather than pending; `blocked` remembers it the way `unchanged` remembers
    # an unmoving projection.
    blocked = {"at": None, "count": 0}
    measured = {"submitted_at": clock(), "job_id": job_id,
                "serving_seconds": serving_seconds,
                "reserved_seconds": bounds["cleanup_seconds"]}

    if surveyed is None:
        surveyed = baseline._guarded(
            lambda: baseline.survey(job, packet), None,
            what="the pre-submission Job survey", uncertainty=uncertainty,
            interrupted=caught)
    measured["preexisting_jobs"] = (
        [] if surveyed is None else surveyed["preexisting_jobs"])
    measured["accounting_scope"] = (
        surveyed["accounting_scope"] if surveyed is not None else
        f"this run accounts for Job {job_id!r} and for nothing else; the "
        f"store could not be surveyed, so what else it holds is unknown.")

    # -- 1. ONE SUBMISSION, AND A REPEAT REPLAYS IT ------------------------
    with open(packet["submission"]["path"], "r", encoding="utf-8") as handle:
        recorded = submit(job, read_submission(handle.read()))
    measured["submission_id"] = recorded["submission_id"]

    # -- 2. THE DECLARED PER-TURN CEILING IS THE JOB'S, BEFORE SERVING -----
    _seen, _states, limits = baseline._attempts_of(job, gate, job_id)
    measured["provider_turn"] = baseline._turn_ceiling(limits, packet)

    # -- 3. BOUNDED SERVING ------------------------------------------------
    held = {"stop": None, "states": {}, "kinds": {}}
    unchanged = {"count": 0, "at": None}

    def should_continue():
        """The stop conditions, in the order they are cheapest to be sure of.

        AN INTERRUPTION IS NOT AN UNREADABLE JOURNAL, and this predicate is
        where the accepted baseline learned that the hard way: a `_guarded`
        call here catches `BaseException`, so the `KeyboardInterrupt` the
        installed handler raises would be swallowed, the predicate would answer
        True and ORDINARY SERVING WOULD RESUME. Only `Exception` is caught, so
        a Ctrl-C travels out of `serve` and into the shutdown around it.
        """
        seen, states, _limits = baseline._attempts_of(job, gate, job_id)
        held["kinds"].update(seen)
        held["states"] = states
        if states and any(one == "exceptional" for one in states.values()):
            held["stop"] = "exceptional"
            return False
        if set(states) == set(KINDS) \
                and all(one == "completed" for one in states.values()):
            held["stop"] = "completed"
            return False
        # A RUN THAT HAS STOPPED MOVING SAYS SO rather than spending its bound
        # discovering it. An unreadable journal is PROGRESS-NEUTRAL: it is not
        # evidence that nothing is happening, so it resets the counter rather
        # than advancing it -- failing towards keeping the run alive, which is
        # the direction that cannot invent a stall.
        accountable = dict(gate.launched)
        accountable.update(seen)
        try:
            settled = baseline._cleanups(control, packet, sorted(accountable))
        except Exception as failure:                         # noqa: BLE001
            uncertainty.append(
                f"the progress read did not complete: "
                f"{type(failure).__name__}: {failure}. A failed read is not "
                f"evidence that nothing is happening, so this tick counts as "
                f"progress.")
            settled = None
        now = (None if settled is None
               else baseline._observation(states, sorted(accountable),
                                          settled["cleanup"]))
        # AND A RUN THAT HAS ADMITTED NOTHING IS NOT STALLED. `accountable` has
        # to be non-empty: an unchanged projection before the first admission
        # is a manager about to admit, not a run that cannot finish.
        if now is not None and accountable and not settled["outstanding"] \
                and now == unchanged["at"]:
            unchanged["count"] += 1
            if unchanged["count"] >= baseline.STALLED_TICKS:
                held["stop"] = "no-progress"
                return False
        else:
            unchanged["count"] = 0
        unchanged["at"] = now
        # AN OWED ACT THAT IS BEING REFUSED IS NOT A CONDITION TO WAIT OUT.
        #
        # OWNER REROUTE 314549, and this is what the second live experiment
        # spent its last 104 seconds on. The review provider timed out, its
        # output was frozen `unable`, and the manager then tried to CONCLUDE
        # the review episode every tick. The product refused every time, with
        # the reason it retained as a deferral: "attempt ...'s output is
        # 'sealed' and its cleanup ended 'pending', so the worker's own
        # material stands preserved and offered for inspection. A preparation
        # is a WRITER inside these roots and the material is evidence while it
        # is offered, so the offer is ENDED ... rather than written beside".
        #
        # The stall detector could not see it: it requires
        # `not settled["outstanding"]`, and the whole point of this condition
        # is that a cleanup IS outstanding. So the loop swept 58 times and
        # stopped only when an operator pressed Ctrl-C. A precondition refusal
        # does not become satisfiable by asking again, so it ends the run --
        # after `STALLED_TICKS` of the SAME refusal, because the product calls
        # a deferral re-enterable and a single tick's reason may still settle.
        refused = baseline._guarded(
            lambda: refused_acts(job, job_id), [],
            what="the outstanding-act read", uncertainty=uncertainty,
            interrupted=caught)
        if blocked_by(refused, blocked):
            held["stop"] = "conclusion-refused"
            held["refused_acts"] = list(refused or [])
            return False

        if gate.refusals:
            # A CAP REFUSAL IS THE END OF THIS RUN, not a condition to wait
            # out. The invocations this packet declares are spent, so spinning
            # to the overall bound would be the same answer 800 seconds later.
            held["stop"] = "invocation-cap-refused"
            return False
        if monotonic() - started >= serving_seconds:
            held["stop"] = "overall-bound-exceeded"
            return False
        return True

    serving_failure, interrupted = None, None
    # AN INTERRUPTION IS A SHUTDOWN, NOT AN ESCAPE. `KeyboardInterrupt` and
    # `SystemExit` are not `Exception`, so an unqualified handler would let a
    # Ctrl-C leave every started runtime unaccounted for. A serving FAULT is
    # not re-raised either: the runtimes this run started are the manager's to
    # account for whether or not the loop ended politely.
    try:
        serve(job, gate, clock=clock, sleep=sleep,
              should_continue=should_continue, interval=1)
    except Exception as failure:                             # noqa: BLE001
        serving_failure = f"{type(failure).__name__}: {failure}"
        held["stop"] = held["stop"] or "serving-failed"
    except BaseException as failure:                         # noqa: BLE001
        said = f"{type(failure).__name__}: {failure}"
        caught.append(said)
        interrupted = said
        held["stop"] = held["stop"] or "interrupted"
    # THE SERVING FAULT IS RECORDED WHATEVER THE OUTCOME. A first version only
    # appended it to `held_because` when the result was not already FAILED, so
    # the one line naming WHY the loop stopped was dropped exactly when a reader
    # needed it most -- a connected run reported `serving-failed` with no reason
    # anywhere in the outcome.
    measured["serving_failure"] = serving_failure
    measured["stopped"] = held["stop"] or "unknown"
    measured["serving_seconds_spent"] = round(monotonic() - started, 3)
    measured["stage_states"] = dict(held["states"])
    measured["admissions"] = dict(gate.admissions)

    # -- 4. ADMISSION CLOSES, AND THE SHUTDOWN IS THE ACCEPTED ONE ---------
    # Review 2026-09-29T21-41-08Z R2 listed exactly what my first version had
    # dropped from the accepted baseline's shutdown, and every item was real:
    # no deferred interrupts, no post-stop canonical discovery, no union with
    # `gate.launched`, no manager-owned cancellation, and an unguarded `sleep`
    # a second Ctrl-C could escape through. All five are restored here.
    #
    # THE INTERRUPTS ARE DEFERRED FIRST. From this point the shutdown must
    # complete: a signal arriving during discovery, cancellation, the cleanup
    # window or publication is REMEMBERED and re-raised after the outcome is on
    # disk, rather than killing the process with nothing retained.
    termination.defer()
    gate.stop()

    # 4a. WHAT THIS RUN REALLY STARTED, re-read rather than taken from the last
    # predicate. An attempt admitted and then faulted before the next tick was
    # invisible to `held["kinds"]`, so it was omitted from cleanup accounting
    # entirely -- the union with `gate.launched` is what makes a launch this
    # process performed impossible to lose.
    admitted = dict(held["kinds"])
    for attempt, kind in gate.launched.items():
        admitted.setdefault(attempt, kind)
    refreshed, states, _limits, _read = baseline._guarded(
        lambda: baseline._refresh(job, gate, job_id, uncertainty,
                                  "after the serving loop stopped"),
        ({}, {}, None, False), what="the post-stop canonical read",
        uncertainty=uncertainty, interrupted=caught)
    held["states"] = states or held["states"]
    held["kinds"].update(refreshed)
    for attempt, kind in refreshed.items():
        admitted.setdefault(attempt, kind)

    # 4b. ASK THE COMPOSITION TO STOP WHAT IS STILL EXECUTING. Closing the gate
    # stops the NEXT runtime and does nothing about one already waiting on a
    # provider turn; an ordinary sweep has nothing to finish while it waits. So
    # a timeout without this is reported `held` with the container still
    # running and the engine never asked to stop it -- which is exactly what my
    # first version did. The stop belongs to the deployment that started it.
    measured["cancellation"] = baseline._guarded(
        lambda: baseline._cancel_active(operations, control, packet, admitted,
                                        held["states"], uncertainty,
                                        reason=measured["stopped"],
                                        launched=set(gate.launched),
                                        interrupted=caught),
        {}, what="the cancellation of what was still executing",
        uncertainty=uncertainty, interrupted=caught)

    # 4c. THE CLEANUP WINDOW, WHICH CANNOT ADMIT ANYTHING. Bounded by the
    # reserve AND by the total, so the reserve cannot extend the run. Every
    # step inside it is guarded, INCLUDING the sleep: a second interrupt ends
    # the window and is reported rather than escaping with the accounting half
    # done.
    cleanup_deadline = min(monotonic() + bounds["cleanup_seconds"],
                           started + bounds["total_seconds"])
    sweeps, intruders = 0, []
    while monotonic() < cleanup_deadline:
        accounting = baseline._guarded(
            lambda: baseline._cleanups(control, packet, sorted(admitted)),
            None, what="the cleanup journal read in the reserve",
            uncertainty=uncertainty, interrupted=caught)
        if accounting is not None and not accounting["outstanding"]:
            break
        try:
            sweep(job, gate, now=clock())
            sweeps += 1
        except BaseException as failure:                     # noqa: BLE001
            said = f"{type(failure).__name__}: {failure}"
            uncertainty.append(f"a cleanup sweep did not complete: {said}")
            if not isinstance(failure, Exception):
                caught.append(said)
                interrupted = interrupted or said
            break
        finally:
            fresh, states, _limits, _held = baseline._guarded(
                lambda: baseline._refresh(job, gate, job_id, uncertainty,
                                          "during the cleanup window"),
                ({}, {}, None, False),
                what="a cleanup-window canonical read",
                uncertainty=uncertainty, interrupted=caught)
            held["states"] = states or held["states"]
            held["kinds"].update(fresh)
            for attempt, kind in list(gate.launched.items()) + list(
                    fresh.items()):
                if attempt not in admitted:
                    # AN ATTEMPT THAT APPEARED AFTER ADMISSION CLOSED IS A
                    # FAULT **AND** IS ACCOUNTED FOR. Reporting it without
                    # adding it to the cleanup set would name a runtime nobody
                    # then asked to stop.
                    intruders.append(attempt)
                    admitted[attempt] = kind
        stopped_early = baseline._guarded(
            lambda: sleep(1), "interrupted",
            what="the cleanup window's own wait", uncertainty=uncertainty,
            interrupted=caught)
        if stopped_early == "interrupted":
            break
    measured["cleanup_sweeps"] = sweeps

    # 4d. THE FINAL CANONICAL READ IS A PRECONDITION OF HONEST ACCOUNTING,
    # not a courtesy: without it the accounting rests on this process's own
    # launch record, which cannot answer what else the store holds.
    final, states, _limits, final_read = baseline._guarded(
        lambda: baseline._refresh(job, gate, job_id, uncertainty,
                                  "for the final accounting"),
        ({}, {}, None, False), what="the final canonical read",
        uncertainty=uncertainty, interrupted=caught)
    held["states"] = states or held["states"]
    held["kinds"].update(final)
    for attempt, kind in final.items():
        if attempt not in admitted:
            intruders.append(attempt)
            admitted[attempt] = kind
    measured["final_canonical_read"] = final_read
    measured["stage_states"] = dict(held["states"])
    measured["intruders"] = sorted(set(intruders))
    # WHAT THE RUN WAS BEING REFUSED WHEN IT STOPPED, retained in the outcome
    # rather than only in the store: an operator reading this document is owed
    # the sentence the manager was given, not just the word for it.
    measured["refused_acts"] = list(held.get("refused_acts") or [])

    # THE ATTEMPTS, IN RECORDED ORDER AND NOT IN SPELLING ORDER. R3: the
    # opening and restored uses are selected from the store's own episode
    # chronology; `admitted` is keyed in the order this process observed
    # launches, and the projection's episodes are the authority when it answers.
    chronology = baseline._guarded(
        lambda: stage_episodes(job, gate, job_id), {},
        what="the recorded episode chronology", uncertainty=uncertainty,
        interrupted=caught)
    implementations = _ordered(chronology.get("implementation"), admitted,
                              "implementation")
    reviews = _ordered(chronology.get("review"), admitted, "review")
    measured["implementation_attempts"] = implementations
    measured["review_attempts"] = reviews
    measured["episode_chronology"] = {
        kind: list(order) for kind, order in sorted(chronology.items())}
    accounting = baseline._guarded(
        lambda: baseline._cleanups(control, packet, sorted(admitted)),
        {"cleanup": {}, "outstanding": sorted(admitted)},
        what="the final cleanup accounting", uncertainty=uncertainty,
        interrupted=caught)
    measured["cleanup"] = accounting["cleanup"]
    measured["observed_attempts"] = sorted(admitted)

    # -- 5. WHAT THE RUN PRODUCED ------------------------------------------
    verdict = baseline._guarded(
        lambda: disposition(control, job, gate, job_id), None,
        what="the reviewer's disposition", uncertainty=uncertainty,
        interrupted=caught)
    measured["review_disposition"] = verdict
    continuity = {"continued": False, "why": "no correction round happened"}
    if len(implementations) >= 2:
        continuity = baseline._guarded(
            lambda: context_continuity(control, opening=implementations[0],
                                       restored=implementations[-1]),
            {"continued": False, "why": "the continuity read did not answer"},
            what="the restored conversation's continuity",
            uncertainty=uncertainty, interrupted=caught)
    measured["context_continuity"] = continuity

    # -- 6. THE OUTCOME, AND IT FAILS CLOSED -------------------------------
    for one in termination.received:
        if one not in caught:
            caught.append(one)
    if interrupted is None and caught:
        interrupted = caught[0]
    result, reasons = classify(
        stop=held["stop"], disposition=verdict,
        implementations=len(implementations), reviews=len(reviews),
        continuity=continuity,
        cleanup_outstanding=accounting["outstanding"], interrupted=interrupted)
    reasons = list(reasons)
    reasons.extend(uncertainty)
    if intruders:
        reasons.append("a runtime was admitted after admission closed: "
                       + ", ".join(sorted(intruders)))
    if gate.refusals:
        reasons.append("the admission gate refused: "
                       + "; ".join(one["why"] for one in gate.refusals))
    if serving_failure is not None:
        reasons.append(f"the serving loop did not end cleanly: "
                       f"{serving_failure}")
    measured["interrupted"] = interrupted
    measured["interruptions"] = list(caught)
    outcome = {"schema": OUTCOME_SCHEMA, "run_id": packet["run_id"],
               "work": packet["work"], "claim": packet["claim"],
               "outcome": result,
               "state": "settled" if not reasons else "held",
               "held_because": reasons, "retry": False,
               "finished_at": clock(), "uncertainty": uncertainty, **measured}
    baseline._publish(packet["outcome_path"], outcome)

    # A SIGNAL THAT ARRIVED WHILE THE OUTCOME WAS BEING WRITTEN IS STILL A
    # SIGNAL. Found by this file's own publication case: `termination.received`
    # was read BEFORE the publication and never again, so a deferred signal
    # delivered during the write was recorded and then silently dropped -- the
    # retained outcome said the run was uninterrupted while an operator had
    # asked it to stop. The publication is atomic and repeating it is cheap, so
    # the honest answer is to record what arrived and publish again.
    late = [one for one in termination.received if one not in caught]
    if late:
        caught.extend(late)
        interrupted = interrupted or caught[0]
        outcome["interrupted"] = interrupted
        outcome["interruptions"] = list(caught)
        outcome["held_because"] = list(outcome["held_because"]) + [
            f"the run was interrupted while its outcome was being written: "
            f"{interrupted}"]
        outcome["state"] = "held"
        baseline._publish(packet["outcome_path"], outcome)

    if interrupted is not None:
        # THE OUTCOME IS ON DISK AND THE INTERRUPT IS NOT SWALLOWED. An
        # operator who pressed Ctrl-C is owed both.
        raise baseline.SupervisorInterrupted(interrupted, outcome)
    return outcome


def main(argv=None, *, stream=None, compose=None, image_inspect=None):
    """Refuse everything refusable, then open exactly two stores, then run.

    THE ORDER IS THE WHOLE POINT and it is the accepted baseline's: the bytes,
    then the imports, then the engine, then the survey -- all before the owner
    acts -- because a candidate qualification grant is spent exactly once and
    discovering a collision after `prepare` would spend it on a run that can
    never submit.
    """
    stream = sys.stderr if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="correction_supervisor",
        description="Supervise ONE bounded managed correction from its packet. "
                    "Never retries, never manufactures a verdict.")
    parser.add_argument("--packet", required=True,
                        help="the packet `correction_packet.py bind` emitted")
    parser.add_argument("--incarnation", default=None,
                        help="this process's control incarnation; defaults to "
                             "the packet's own run_id")
    taken = parser.parse_args(argv)

    try:
        verify_baseline()
        packet = held_packet(taken.packet, supervisor=__file__)
        baseline.verify_imported_sources(packet, program=__file__)
        baseline.verify_worker_image(
            packet,
            image_inspect=baseline._engine_inspect if image_inspect is None
            else image_inspect)
    except (PacketRefusal, baseline.SupervisorRefusal) as refusal:
        print(f"refused before anything opened: {refusal}", file=stream)
        return 2

    from baton_v12.job_manager import JobStore
    from baton_v12.worker_manager import ControlStore

    deployment = packet["deployment"]
    incarnation = taken.incarnation or packet["run_id"]
    with JobStore.open(deployment["job_store"],
                       authority_uuid=deployment["authority_uuid"],
                       incarnation=incarnation,
                       clock=baseline._moment) as job:
        try:
            surveyed = baseline.survey(job, packet)
        except baseline.SupervisorRefusal as refusal:
            print(f"refused before any owner act: {refusal}", file=stream)
            return 2
        if surveyed["preexisting_jobs"]:
            print(f"this Job store also holds "
                  f"{', '.join(surveyed['preexisting_jobs'])}; "
                  f"{surveyed['accounting_scope']}", file=stream, flush=True)
        with ControlStore.open(deployment["control_store"],
                               incarnation=incarnation,
                               clock=baseline._moment) as control:
            baseline.prepare(control, packet)
            operations = (compose or baseline._compose)(packet, job, control,
                                                        stream)
            try:
                outcome = supervise(job, control, operations, packet,
                                    surveyed=surveyed)
            finally:
                closing = getattr(operations, "close", None)
                if closing is not None:
                    closing()
    print(json.dumps(outcome, indent=2, sort_keys=True), file=stream)
    print(f"outcome {outcome['outcome']!r}, state {outcome['state']!r}; the "
          f"result is retained at {packet['outcome_path']}", file=stream)
    return 0 if outcome["state"] == "settled" else 1


def interruption_reason(stopped):
    """Why the run was interrupted, read from where the exception KEEPS it.

    OWNER REROUTE 314549, and it is a defect that cost an operator the report
    of a real run. `baseline.SupervisorInterrupted.__init__(why, outcome)` calls
    `super().__init__(why)` and sets `self.outcome`; IT SETS NO `self.why`. This
    module asked for `stopped.why`, so the very act of reporting an interruption
    raised `AttributeError` -- after the outcome had been printed and before the
    exit status was set. The accounting was on disk and correct, and the last
    thing the operator saw was a traceback from the reporter.

    So the reason comes from `args`, which is where `BaseException` puts what it
    was constructed with, and from the retained outcome as a cross-check. The
    accepted machinery is NOT changed: `baseline.py` is pinned by digest and its
    contract here is `args` plus `.outcome`.
    """
    said = stopped.args[0] if stopped.args else None
    if said is None or said == "":
        # THE OUTCOME IS THE SECOND WITNESS. `supervise` writes `interrupted`
        # into it before raising, so a reason is still available even if the
        # exception was constructed without one.
        held = getattr(stopped, "outcome", None) or {}
        said = held.get("interrupted") or "interrupted, with no reason recorded"
    return said


def unresolved_cleanup(outcome):
    """Every attempt whose cleanup this run could NOT prove, by identity.

    REPORTED SEPARATELY, on the reroute's own instruction. A run that ends
    interrupted can leave a runtime the engine reports quiescent and a cleanup
    that never committed, and those are two different facts: the operator needs
    the second one named, because a stopped runtime is not a proved cleanup.
    """
    held = []
    for attempt, one in sorted((outcome.get("cleanup") or {}).items()):
        if not isinstance(one, dict) or one.get("cleanup") is None:
            cancelled = (outcome.get("cancellation") or {}).get(attempt) or {}
            held.append({
                "attempt_id": attempt,
                "cleanup": None,
                "why": (one or {}).get("why", "no committed cleanup"),
                "execution_runtime": cancelled.get("execution_runtime"),
                "runtime_id": cancelled.get("runtime_id"),
                "stage_state": cancelled.get("stage_state"),
            })
    return held


def report_interruption(stopped, *, stream=None, out=None):
    """Print the retained outcome, the reason and any unresolved cleanup.

    A FUNCTION RATHER THAN A BLOCK UNDER `if __name__ == "__main__"`, and that
    is the second half of the correction. The defect above lived in a block
    marked `pragma: no cover` -- unreachable by every test in this dossier --
    which is exactly why a one-word attribute error survived to a live run. It
    is callable and covered now.
    """
    stream = sys.stderr if stream is None else stream
    out = sys.stdout if out is None else out
    outcome = getattr(stopped, "outcome", None)
    if outcome is not None:
        print(json.dumps(outcome, indent=2, sort_keys=True), file=out)
    print(f"interrupted: {interruption_reason(stopped)}", file=stream)
    if outcome is not None:
        print(f"outcome {outcome.get('outcome')!r}, state "
              f"{outcome.get('state')!r}; the result is retained",
              file=stream)
        pending = unresolved_cleanup(outcome)
        if pending:
            print(f"UNRESOLVED CLEANUP for {len(pending)} attempt(s); a "
                  f"quiescent runtime is not a proved cleanup:", file=stream)
            for one in pending:
                print(f"  {one['attempt_id']}: runtime "
                      f"{one['execution_runtime']!r} "
                      f"({one['runtime_id']}), stage "
                      f"{one['stage_state']!r} -- {one['why']}", file=stream)
    return 130


if __name__ == "__main__":                                   # pragma: no cover
    try:
        raise SystemExit(main())
    except baseline.SupervisorInterrupted as stopped:
        raise SystemExit(report_interruption(stopped))
    except PacketRefusal as refusal:
        print(f"refused: {refusal}", file=sys.stderr)
        raise SystemExit(2)
