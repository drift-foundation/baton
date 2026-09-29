"""The four-admission gate this arrangement's bounded run needs.

ASSESSMENT-249338.md R4 asks for a bounded supervisor over FOUR admissions --
two implementations and two reviews -- with stop, positive cleanup for every
admitted attempt and a published outcome. This module is the part of it that
decides what may be admitted at all, and it is deliberately the smallest thing
that can be that: everything else a bounded run needs (termination handling,
discovery, cancellation, cleanup accounting and publication) is W239528's
accepted `baseline` machinery, which this reuses rather than reimplements.

WHY A SUBCLASS AND NOT A SECOND GATE. `baseline.AdmissionGate` already counts
admissions by KIND, records every launched runtime at the call, refuses the
three admitting acts once stopped, and forwards everything else untouched. The
ONE thing it cannot do is serve two Jobs: `_ours` scopes every act to a single
`job_id`, because the single-Job packets it was written for must not spend
their cap on somebody else's stage. A two-Job run needs exactly that rule with
two identities instead of one, so that is the only thing changed here.

WHAT IS HERE NOW. `supervise` is the bounded run itself: it serves through the
gate, stops at `total_seconds - cleanup_seconds`, closes admission BEFORE
cancelling, cancels through `baseline._cancel_active`, drives bounded ending
sweeps inside what is left of the total, reads the cleanup journal after the
last one, derives each Job's verdict from its own frozen result, and publishes
an outcome on every path. `main` is the one command that opens the stores,
composes, submits and runs it.

WHAT IS STILL SIMULATED, at the boundary where a container would be: the
worker turn. `turns` is a seam a caller supplies; in a real deployment the
runtime IS the turn. A caller that supplies none gets a run that starts
nothing, and the outcome says so rather than calling it a success.
"""
import hashlib
import os
import pathlib
import stat
import sys

SIBLING = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "finding-v12-single-implementation-proof")
if SIBLING not in sys.path:                                  # pragma: no cover
    sys.path.insert(0, SIBLING)

import baseline                                              # noqa: E402

# THE ACCEPTED BYTES THIS SPECIALIZATION EXTENDS, bound by digest exactly as
# W239533's supervisor binds them: a machinery change underneath a
# specialization is a different proof, and it should be visible as a refusal
# rather than as a passing run over bytes nobody accepted.
#
# ADVANCED AT W247941 claim 305010, and the pin did its job first: it REFUSED,
# because the machinery underneath had moved on to the bytes the accepted
# single-Job run actually used. The new value is not "current file" -- it is
# `work/records/.../finding-v12-single-implementation-proof/baseline.py` as
# recorded in FINAL-PACKET-302142.json, the candidate whose execution
# EXECUTION-REVIEW-304782.json accepted. Before advancing it I checked the
# dependency surface rather than assuming it: all eleven `baseline.` symbols
# this module uses are present in those bytes, and `_cancel_active` still takes
# the operands the call below passes. The previous value is kept beside it so a
# reader can see which generation each earlier result was measured against.
BASELINE_SHA256 = \
    "248e570d8f9d459550b0aa5e92d1674c3226fe540ba987cae916a4a334606771"
BASELINE_SHA256_BEFORE_302142 = \
    "f27f3cd766f9271c4b3eddb6c657bca4770d18c11a74f377e717bef23df18fd5"

# THE FOUR ADMISSIONS THIS GATE ALLOWS, and no fifth of any kind.
CAPS = {"implementation": 2, "review": 2}

# THE DOCUMENT THIS RUN PUBLISHES, whatever happened to it.
OUTCOME_SCHEMA = "baton.v12.two-job-outcome/1"

# HOW MANY ENDING SWEEPS THE RESERVED WINDOW MAY DRIVE. A bound on
# the window alone would let a fast clock spin; this bounds the acts.
CLEANUP_SWEEPS = 12


def _abandonment_eligible(control, attempt_id):
    """Whether an abandonment may end this attempt, read from its own state.

    W247941, review 2026-09-24T10:23:12Z: "outstanding alone is not
    eligibility". An attempt this supervisor could not settle may be
    outstanding for reasons an abandonment must not paper over, so each one is
    asked about SEPARATELY and the answer is a sentence rather than a boolean
    nobody can act on.

    THE FOUR THINGS THAT DISQUALIFY IT, and each is somebody else's ending:

      * no attached runtime -- abandonment ends a runtime that STARTED, and
        an unstarted cancellation has its own proof;
      * a terminal cleanup axis -- an ending is not revisited;
      * `uncertain` execution -- this manager cannot say what exists, and
        cleanup waits for a reconciliation that observes what is true;
      * a committed intake receipt -- the WORKER ANSWERED, and the ordinary
        ending owns that result. Declaring it abandoned would relabel a
        completed turn.
    """
    from baton_v12.worker_manager import attempt_runtime_of, intake

    state = attempt_runtime_of(control, attempt_id)
    if state is None:
        return False, "this store holds no such attempt"
    if state["runtime_id"] is None:
        return False, "no runtime was ever attached"
    if state["cleanup"] not in ("pending", "blocked-on-intake"):
        return False, f"cleanup is already {state['cleanup']}"
    if state["execution_runtime"] == "uncertain":
        return False, ("the runtime observation is uncertain and cleanup "
                       "waits for a reconciliation that observes what is true")
    if intake.intake_receipt_of(control, attempt_id) is not None:
        return False, ("the worker answered and its ordinary ending owns "
                       "this result")
    return True, None


def _declare_abandonment(operations, control, gate, attempts, *, reason,
                         policy, remaining=None):
    """Declare each ELIGIBLE outstanding attempt abandoned, and say so.

    W247941. The run stopped, the cancellation fenced what was executing, and
    the bounded sweeps could not settle a runtime whose worker never answered:
    that attempt has no ordinary ending anywhere in its future. This is the
    supervisor's explicit shutdown declaration, and calling it IS the
    declaration -- there is no clock, no retry count and no silence threshold
    here.

    ADMISSION IS BOUNDED; EXECUTION IS NOT, AND THAT DISTINCTION IS THE POINT.
    Review 2026-09-24T10:35:28Z [R1]: this step may fence, remove, normalize
    custody and discharge, and it used to begin AFTER the reserved window had
    already expired -- "a finite attempt count does not preserve the selected
    run time bound". `remaining` is a callable answering the seconds left;
    when it answers nothing is left, every attempt from that point on is
    recorded UNRESOLVED and no new ending work is started.

    WHAT THIS DOES NOT DO, said plainly because the earlier docstring implied
    otherwise. Once an attempt IS admitted, nothing here bounds how long its
    ending takes: no signature between this call and the engine carries a
    deadline, and the per-operation limits are the worker-manager package's
    own constants rather than caller operands. So a small positive remainder
    still admits a sequence that may outlast it. `BOUND-256097.md` documents
    the exact interface gap and proposes the bounded correction; until that is
    ruled on, this function bounds ADMISSION and says so.

    An attempt already begun is never interrupted from here, because the
    sequence commits durable records between its external calls so that an
    interruption is RESUMABLE -- stopping it from outside would replace the
    product's own recovery semantics with a supervisor's impatience.

    EVERY OUTCOME IS REPORTED AND NO FAILURE DISCARDS THE REST. Review [R2]:
    an eligibility or read-back failure used to escape to the caller's single
    guard, which replaced the whole map with `{}` and skipped every later
    attempt. Each attempt is now wrapped on its own, and what has already been
    established stays established.
    """
    declared = {}
    held = list(sorted(attempts))
    for index, attempt_id in enumerate(held):
        work = _work_allowance(remaining)
        left = None if work is None else work()
        if left is not None and left <= 0:
            # THE BOUND, CHECKED BEFORE ANY NEW ENDING WORK, WITH A RESERVE.
            # Everything from here on is unresolved and says so by name.
            for later in held[index:]:
                declared[later] = {
                    "declared": False,
                    "why": f"fewer than "
                           f"{ABANDONMENT_RESERVE_SECONDS}s of the selected "
                           f"run bound remained, which is the reserve this "
                           f"shutdown keeps for reclamation; its ending was "
                           f"not started, it is unresolved, and its runtime "
                           f"was not touched"}
            break
        declared[attempt_id] = _declared_one(
            operations, control, gate, attempt_id, reason=reason,
            policy=policy, remaining=work, reclaim=remaining)
    return declared


def _declared_one(operations, control, gate, attempt_id, *, reason, policy,
                  remaining=None, reclaim=None):
    """ONE attempt's declaration, whose every failure belongs to it alone."""
    from baton_v12.worker_manager import intake

    try:
        eligible, why = _abandonment_eligible(control, attempt_id)
    except BaseException as failure:                         # noqa: BLE001
        # UNKNOWN, not false: nothing was attempted, and a read that failed
        # says nothing about what may already exist.
        return {"declared": None,
                "why": f"its eligibility could not be read: "
                       f"{type(failure).__name__}: {failure}"}
    if not eligible:
        return {"declared": False, "why": why}
    stage = gate.launched_stage.get(attempt_id)
    if stage is None:
        return {"declared": False,
                "why": "no launch stage document was recorded for it"}
    try:
        # THE ALLOWANCE IS THE SAME CALLABLE THE ADMISSION CHECK READS, so the
        # observation, the fence, the removal, both custody acts, the
        # discharge and the read-back all spend ONE decreasing budget. It is
        # `None` for an unbounded caller, which is byte for byte today.
        # THE WORK ALLOWANCE IS NET OF THE MARGIN; the RECLAMATION spends the
        # whole remaining time, which is what makes the margin a reserve for
        # something rather than time nobody may use.
        operations.abandon_attempt(attempt_id=attempt_id, reason=reason,
                                   stage=dict(stage), seconds=remaining,
                                   reclaim=reclaim)
    except BaseException as failure:                         # noqa: BLE001
        # THE CALL FAILED AND THAT IS NOT THE SAME FACT AS "NOTHING WAS
        # DECLARED". Review 2026-09-24T10:42:09Z [R2]: the exception can
        # arrive AFTER the declaration and even after the cleanup committed --
        # the lost-discharge and severed-read-back histories are exactly that
        # shape -- so asserting `declared=False` from an exception would deny
        # an ending that really happened.
        #
        # SO IT IS READ, AND UNREADABLE IS `None` RATHER THAN `False`. The
        # invocation failure is reported as its own member either way, and
        # `_settled_by_abandonment` counts neither, so an uncertain attempt
        # stays unresolved.
        invocation = f"{type(failure).__name__}: {failure}"
        try:
            settled = intake.abandonment_cleanup_of(
                control, attempt_id=attempt_id,
                retention_policy_digest=policy)
            discharge = intake.abandoned_gate_discharge_of(
                control, attempt_id)
        except BaseException as reading:                     # noqa: BLE001
            return {"declared": None, "cleanup": None,
                    "gate_discharged": False,
                    "why": f"its declaration failed with {invocation}, and "
                           f"what it committed could not be read: "
                           f"{type(reading).__name__}: {reading}"}
        return {
            "declared": None if settled is None else True,
            "cleanup": (settled or {}).get("cleanup", {}).get("cleanup"),
            "gate_discharged": discharge is not None,
            "why": f"its declaration failed with {invocation}; what it had "
                   f"already committed is reported beside this",
        }
    # READ BACK, never taken from the answer in hand -- and a read that fails
    # leaves the declaration TRUE and the settlement UNKNOWN, which is the
    # honest pair. The act happened; what this manager can say about it did
    # not.
    try:
        settled = intake.abandonment_cleanup_of(
            control, attempt_id=attempt_id, retention_policy_digest=policy)
        discharge = intake.abandoned_gate_discharge_of(control, attempt_id)
    except BaseException as failure:                         # noqa: BLE001
        return {"declared": True, "cleanup": None,
                "gate_discharged": False,
                "why": f"its ending could not be read back: "
                       f"{type(failure).__name__}: {failure}"}
    return {"declared": True,
            "cleanup": (settled or {}).get("cleanup", {}).get("cleanup"),
            "gate_discharged": discharge is not None}


def _settled_by_abandonment(declared):
    """The attempts a declaration FINISHED, and finishing takes both facts.

    Review 2026-09-24T10:35:28Z [R2]: "do not treat `declared=True` alone as a
    completed ending". A declaration that was made is not an ending that
    settled; the cleanup has to be positive AND the gate it fenced has to be
    discharged, because an undischarged gate leaves the Work stopped.
    """
    return sorted(attempt for attempt, held in (declared or {}).items()
                  if held.get("declared")
                  and held.get("cleanup") == "retained"
                  and held.get("gate_discharged"))


# W247941: THE RECLAMATION RESERVE, AND IT IS ACTUALLY WITHHELD.
#
# Review 2026-09-24T11:10:32Z: my first version refused admission below 30
# seconds and then handed the operation the UNCHANGED remaining callable, so
# "an admitted act can therefore spend ALL the remaining allowance, including
# the purported reserve". It was an admission floor wearing a reserve's name.
#
# NOW THE MARGIN IS SUBTRACTED FROM WHAT THE WORK MAY SPEND. The work
# allowance is `remaining() - ABANDONMENT_RESERVE_SECONDS`, so an act that
# consumes its whole budget still leaves the margin behind it; admission uses
# the same subtraction, which is what makes the two agree by construction
# rather than by two numbers that have to be kept in step.
#
# THE RECLAMATION RESERVE: A BOUNDED ALLOCATION, NOT A WORST-CASE SUM.
#
# Two reviews shaped this and I got it wrong in both directions. First I made
# it an admission floor that the work could then spend. Then I derived it from
# the worst case and made it 1200 seconds -- which is larger than an ordinary
# two-Job run's whole 600-second budget, so abandonment became impossible and
# my new cases proved only that it refuses. Review 2026-09-24T13:43:14Z:
# "maxima are ceilings not minimum grants", and what was asked for was
# truthful accounting rather than guaranteed completion.
#
# SO THE RESERVE IS AN ALLOCATION THIS SUPERVISOR MAKES, stated as such: time
# held back so that when the work allowance is gone there is still some left
# for the reclamation to try in, and for the outcome to be recorded. It does
# NOT promise the reclamation finishes. When it runs out, the attempt is
# recorded held and unresolved with its frozen resources named -- which is the
# fallback owner 257086 selected and is honest in a way a guarantee would not
# be.
ABANDONMENT_RESERVE_SECONDS = 60


def _reclamation_worst_case():
    """What a FULLY completed reclamation could need, for the record.

    Counted from the source rather than estimated: one reclamation of one
    custody act is five sequential engine calls, each waiting up to
    `CUSTODY_RECLAIM_SECONDS` -- `_reconciled`'s listing and its inspection,
    `_reclaimed`'s stop and removal orders, and `_proved_absent`'s inspection
    -- and an abandonment performs two custody acts, one per root.

    THIS IS NOT THE RESERVE and deliberately is not used as one. It is the
    number an operator needs in order to understand what "unresolved" means
    here: the ceiling this run did not buy. Every one of those five is a
    CEILING, so a reclamation ordinarily costs far less, which is exactly why
    a bounded allocation is worth making and a worst-case one is not.
    """
    from baton_v12.worker_manager import custody

    return 2 * _RECLAIM_CALLS * custody.CUSTODY_RECLAIM_SECONDS


# HOW MANY SEQUENTIAL ENGINE CALLS ONE RECLAMATION MAKES. Named so a reader
# can check it against `custody._reconciled`, `_reclaimed` and
# `_proved_absent` rather than trusting an arithmetic constant.
_RECLAIM_CALLS = 5


def _work_allowance(remaining):
    """What the ENDING may spend: everything but the reclamation margin.

    `None` stays `None` -- an unbounded caller is unchanged. A bounded one
    gets a callable, because the budget is read at each boundary rather than
    divided in advance.
    """
    if remaining is None:
        return None
    return lambda: remaining() - ABANDONMENT_RESERVE_SECONDS


class SupervisorRefusal(Exception):
    """This run cannot be supervised as configured."""


def held_baseline():
    """The imported machinery is the accepted bytes, or this refuses."""
    place = os.path.join(SIBLING, "baseline.py")
    reading = hashlib.sha256()
    with open(place, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    if reading.hexdigest() != BASELINE_SHA256:
        raise SupervisorRefusal(
            f"{place} hashes {reading.hexdigest()} and this specialization is "
            f"bound to {BASELINE_SHA256}; the machinery underneath it changed")
    return BASELINE_SHA256


class TwoJobGate(baseline.AdmissionGate):
    """The accepted gate, serving exactly the two Jobs it is given.

    EVERY OTHER RULE IS INHERITED UNCHANGED -- the caps, the counting after
    the act commits, the recording of launched runtimes, the refusal of all
    three admitting acts once stopped, and the forwarding of everything that
    settles work already started.
    """

    __slots__ = ("_job_ids", "_generations", "_stage_of", "_launched_stage")

    def __init__(self, operations, *, caps=None, job_ids):
        held = tuple(dict.fromkeys(job_ids))
        if len(held) != 2:
            raise SupervisorRefusal(
                f"this gate serves exactly two Jobs and was given {held!r}; "
                f"one Job named twice is one Job, and a third is a different "
                f"selection with its own capacity question")
        super().__init__(operations, caps=dict(caps or CAPS), job_id=held[0])
        self._job_ids = held
        # THE PROVENANCE `verdicts_of` READS, recorded where it exists.
        # Review 2026-09-23T18:06:35Z: these two were read through `getattr`
        # defaults and NOTHING EVER WROTE THEM, so the public attachment
        # reader was handed `generation=None` and refused, and `job_of`
        # answered None. A reader with a default for a fact nobody records is
        # a reader that always answers "unknown" quietly.
        self._generations = {}
        self._stage_of = {}
        # W247941: THE WHOLE LAUNCH DOCUMENT, because an abandonment takes the
        # attempt's own stage and there is nowhere else to get it once the run
        # is stopping. `stage_of` keeps the id it always kept; this is beside
        # it rather than a change to what that reader answers.
        self._launched_stage = {}

    @property
    def job_ids(self):
        return self._job_ids

    @property
    def generations(self):
        """The assignment generation each launched attempt was admitted at."""
        return self._generations

    @property
    def stage_of(self):
        """The stage each launched attempt belongs to."""
        return self._stage_of

    @property
    def launched_stage(self):
        """The stage DOCUMENT each launched attempt was admitted with."""
        return self._launched_stage

    def job_of(self, attempt_id):
        """Which bound Job an attempt this gate launched belongs to."""
        return self.stage_jobs.get(self._stage_of.get(attempt_id))

    def launch(self, attempt, job):
        """The inherited launch, plus the two facts a verdict read needs.

        RECORDED AT THE CALL, before delegating, exactly as the inherited gate
        records the launch itself: an attempt that then faults is still one
        this run must account for, and a fact reconstructed from a projection
        between ticks can be lost.
        """
        if type(attempt) is dict:
            attempt_id = attempt.get("attempt_id")
            if attempt_id is not None:
                stage_id = attempt.get("stage_id")
                if stage_id is not None:
                    self._stage_of[attempt_id] = stage_id
                # COPIED, not held: the manager owns the document it passed
                # and a supervisor that kept a reference would be reporting
                # whatever somebody later edited.
                self._launched_stage[attempt_id] = dict(attempt)
                # NO GENERATION IS READ HERE. The projection attempt the
                # manager passes carries none, and recording a default would
                # be inventing the fact `review_for_attempt` fences on.
                # `generations_from` reads it from the allocation instead.
                for name in ("assignment_generation", "generation"):
                    if attempt.get(name) is not None:        # pragma: no cover
                        self._generations[attempt_id] = attempt[name]
                        break
        return super().launch(attempt, job)

    def _ours(self, act, document, kind):
        """This run's two Jobs, rather than the inherited one.

        A stage naming neither is foreign: recorded in `foreign` and refused
        without reaching the composed deployment, exactly as the inherited
        rule does it for one Job. That is the boundary working rather than a
        reason to end the run.
        """
        if type(document) is not dict:
            return
        if act == "launch":
            held = document.get("stage_id")
            if held is not None and held in self.stage_kinds:
                return
        elif document.get("job_id") in self._job_ids:
            return
        said = (f"stage of Job {document.get('job_id')!r}"
                if act != "launch" else
                f"attempt of a stage this run never admitted")
        why = (f"this run serves Jobs {', '.join(self._job_ids)} and this is "
               f"a {said}. Admitting it would spend this run's capacity on a "
               f"workload it does not account for")
        from baton_v12.contracts import ContractRefusal
        self.foreign.append(f"{act}: {why}")
        # AN ORDINARY REFUSAL, not an exception that ends the sweep: the
        # manager records a non-durable refusal as a deferral, which is the
        # level-triggered condition it already knows how to report.
        raise ContractRefusal("refused", "precondition",
                              f"the two-Job supervisor refuses to {act}: "
                              f"{why}")




def generations_from(control, gate, uncertainty, caught):
    """Each admitted attempt's ASSIGNMENT generation, from the control store.

    Review 2026-09-23T18:16:47Z: the previous version read
    `allocation.generation` out of the status projection, and that is the POOL
    generation -- `projection._stage_status` gets it from
    `scheduler.allocation_of`, which joins `pool_generations`. The schema
    distinguishes the two axes on purpose, and my "it is not None" check could
    not tell coincident counters apart. Two axes that happen to both be 1 is
    the easiest possible false pass.

    `attempts.assignment_of` is the supported reader for the DURABLE
    assignment identity fixed to an attempt -- the accepted `baseline` uses it
    for exactly this -- and it REFUSES an attempt that has not activated one.
    That refusal is honest absence: it lands in `uncertainty` and the verdict
    for that attempt is simply not derived.
    """
    from baton_v12.worker_manager import attempts as attempt_rows

    held = {}
    for attempt_id in sorted(gate.launched):
        assignment = baseline._guarded(
            lambda one=attempt_id: attempt_rows.assignment_of(control, one),
            None, what=f"the fixed assignment of {attempt_id}",
            uncertainty=uncertainty, interrupted=caught)
        if assignment and assignment.get("generation") is not None:
            held[attempt_id] = assignment["generation"]
    return held


def verdicts_of(control, gate, uncertainty, caught):
    """Each bound Job's verdict, DERIVED from its own frozen result.

    `review_verdict_from_result` is the manager's own deriver: it refuses
    unless the frozen result belongs to that attachment's attempt, its
    retained manifest names the same result and the same assignment at the
    same generation, and the base, head and tree the reviewer reports are the
    ones the checkpoint's evidence records. Nothing here reads a disposition
    off a status row.

    A read that does not complete is UNCERTAINTY, not an absent verdict: this
    answers what it could derive and the caller holds the run for the rest.
    """
    from baton_v12.job_manager import review_driver
    from baton_v12.worker_manager import review_cycles

    held = {}
    for attempt_id, kind in sorted(gate.launched.items()):
        if kind != "review":
            continue
        attachment = baseline._guarded(
            lambda one=attempt_id: review_cycles.review_for_attempt(
                control, attempt_id=one,
                generation=gate.generations.get(one)),
            None, what=f"the review attachment for {attempt_id}",
            uncertainty=uncertainty, interrupted=caught)
        if not attachment:
            continue
        verdict = baseline._guarded(
            lambda one=attachment: review_driver.review_verdict_from_result(
                control, attachment_id=one["attachment_id"]),
            None, what=f"the verdict derived for {attempt_id}",
            uncertainty=uncertainty, interrupted=caught)
        if verdict:
            held[gate.stage_jobs.get(
                attachment.get("stage_id"), gate.job_of(attempt_id))] = verdict
    return held

# WHAT AN OUTCOME OWES A READER even when the run never reached the code that
# fills it. A half-written document that omits members reads like a finished
# run with nothing to report; these defaults make the absence explicit.
_OWED = (
    ("stopped", "stopped-without-a-reason"), ("serving_failure", None),
    ("admissions", dict), ("admitted_attempts", list),
    ("gate_refusals", list), ("foreign_admissions", list),
    ("admission_closed_before_cancellation", False),
    ("cleanup_window_seconds", None), ("cancellation", dict),
    ("cleanup_sweeps", 0), ("cleanup", dict), ("outstanding_cleanup", list),
    ("uncertainty", list), ("interruptions", list), ("generations", dict),
    ("verdicts", dict), ("held_because", list), ("finished_at", None),
    # W306614: WHAT EACH SELECTED PIPELINE REACHED, so a reader of the outcome
    # can tell a Job that failed from one that never started.
    ("pipelines", dict),
    # AND THE FIRST FAILURE EACH JOB WAS OBSERVED TO HAVE, kept separately
    # because `pipelines` is CURRENT ELIGIBILITY and a later unreadable status
    # legitimately empties it. Review 2026-09-29T17-20-22Z R2: a current unknown
    # must not erase a confirmed failure.
    ("failures", dict),
)


# THE REVIEWED PROVIDER-DIAGNOSTIC CONTRACT, closed. W306614 review R2.
#
# THIS IS NOT A PARSER OVER PROVIDER TEXT and it is deliberately not one. The
# accepted `v12/testing/standalone_ab/failure_observation._supported_detail`
# admits exactly two shapes -- the recognised OAuth constant, or an explicit
# unknown -- and refuses everything else including any prose it has not been
# told to expect. This is that rule, applied to what the canonical status
# projection carries, with no schema added anywhere and no new vocabulary.
#
# WHY A LOCAL COPY RATHER THAN THE HELPER. `PROPOSAL.md` and the review both say
# the helper is not drop-in: it hardcodes one packet's submission id, Job names,
# storage layout and task-id suffix, and it is now assigned elsewhere. A bounded
# packet-specific adaptation of its SAFE PARSING CONTRACT is the recorded
# choice; claiming the shared helper silently is the thing not to do.
_OAUTH_EXPLANATION = ("Failed to authenticate: OAuth session expired and could "
                      "not be refreshed")
_DIAGNOSTIC_KEYS = {"schema", "http_status", "classification", "explanation",
                    "explanation_status", "request_id", "request_id_status"}


def _supported_diagnostic(given):
    """The reviewed adapter contract, or None. Never trusts arbitrary prose."""
    if not isinstance(given, dict) or set(given) != _DIAGNOSTIC_KEYS:
        return None
    if given.get("schema") != "baton.provider-diagnostic/1":
        return None
    code = given["http_status"]
    if code is not None and (type(code) is not int or not 400 <= code <= 599):
        return None
    if given["request_id"] is not None \
            or given["request_id_status"] != "unavailable":
        return None
    recognised = (given["classification"] == "authentication_failed"
                  and given["explanation"] == _OAUTH_EXPLANATION
                  and given["explanation_status"] == "supported-constant")
    unknown = (given["classification"] == "unknown"
               and given["explanation"] is None
               and given["explanation_status"] in ("unavailable", "withheld"))
    if not (recognised or unknown):
        return None
    return {"schema": "baton.provider-diagnostic/1", "http_status": code,
            "classification": ("authentication_failed" if recognised
                               else "unknown"),
            "explanation": _OAUTH_EXPLANATION if recognised else None,
            "explanation_status": (
                "supported-constant" if recognised
                else ("withheld" if given["explanation_status"] == "withheld"
                      else "unavailable")),
            "request_id": None, "request_id_status": "unavailable"}


# THE RETAINED ADAPTER REPORT, read through the SAME rules the accepted helper uses.
# W306614 review 2026-09-29T17-33-48Z: my first version read `exchange["diagnostic"]`,
# which the exchange observation does not publish -- it carries state, command, receipt and
# terminal identity. The provider diagnostic is in the adapter's own retained report, and
# copying the validator without its data source meant a valid published OAuth failure could
# never reach the branch that recognises it.
#
# THIS IS A MINIMAL READER OWNED HERE, not the shared helper taken. It keeps the helper's
# identity rules exactly -- one artifact row whose `artifact_id` is `<attempt>:<output>`, a
# `file:` locator with no escaping or traversal, a path UNDER this deployment's own storage
# whose last three parts are `custody/<attempt>/<output>`, a bounded read, duplicate members
# refused, no JSON constants, and the report's own `schema`/`task_id` bound to THIS attempt's
# Job -- and it takes the storage root and task id as operands instead of hardcoding one
# packet's layout, which is why the helper is not drop-in.
_REPORT_OF = {"implementation": ("proposal", "result.json",
                                 "baton.dogfood-proposal/2"),
              "review": ("logs", "review.json", "baton.review-log/1")}
_PROVIDER_REASONS = ("api-error", "timeout", "start-error", "unclassified")
_REPORT_BYTES = 65536


def _unknown_report(why, locator=None):
    return {"availability": "unavailable", "provider_reason": "unknown",
            "provider_exit_status": None, "diagnostic": None,
            "locator": locator, "why": why}


def _bounded_document(place):
    """One small JSON report, with NO SYMLINK AT ANY COMPONENT.

    W306614 review 2026-09-29T17-44-50Z R2a, and the reviewer's fixture is a real escape
    rather than hardening: my first version opened the whole path with `O_NOFOLLOW`, which
    protects the FINAL NAME ONLY, and compared the declared path lexically -- so a symlink
    at `storage/custody` pointing at a sibling tree answered `available` with an
    `authentication_failed` cause attributed from OUTSIDE the selected root.

    THE ANCESTRY IS WALKED with directory descriptors, exactly as the reference
    `failure_observation._document` does, so every component is proved unfollowed. And the
    final open is `O_NONBLOCK` BEFORE the regular-file check, because a FIFO would
    otherwise block in `open` before `fstat` could refuse it.
    """
    import json as _json

    descriptor = os.open(os.sep, os.O_RDONLY | os.O_DIRECTORY)
    try:
        for part in place.parts[1:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        child = os.open(place.name,
                        os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                        dir_fd=descriptor)
        try:
            if not stat.S_ISREG(os.fstat(child).st_mode):
                raise ValueError("not a regular report")
            with os.fdopen(child, "rb", closefd=False) as stream:
                raw = stream.read(_REPORT_BYTES + 1)
        finally:
            os.close(child)
    finally:
        os.close(descriptor)
    if len(raw) > _REPORT_BYTES:
        raise ValueError("oversized report")

    def pairs(items):
        held = {}
        for key, value in items:
            if key in held:
                raise ValueError("duplicate report member")
            held[key] = value
        return held

    def refused(_value):
        raise ValueError("non-JSON constant")

    return _json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                       parse_constant=refused)


def _retained_report(stage, *, storage_root, task_id):
    """The adapter's own retained report for THIS attempt, or an explicit unknown.

    EVERY REFUSAL ANSWERS `unknown` WITH ITS REASON. Absent, foreign, malformed or
    unreadable evidence is a stated unknown -- never a guess, and never a reason to
    claim an authentication cause the report does not establish.
    """
    from urllib.parse import urlsplit

    attempt = stage.get("attempt_id")
    held = _REPORT_OF.get(stage.get("kind"))
    if not attempt or held is None:
        return _unknown_report("this stage names no attempt or no reported output")
    output, filename, schema = held
    rows = [one for one in (stage.get("artifacts") or ())
            if isinstance(one, dict)
            and one.get("output_name") == output
            and one.get("artifact_id") == f"{attempt}:{output}"]
    if len(rows) != 1:
        return _unknown_report(
            f"this attempt declares {len(rows)} retained {output} reports and a "
            f"report is identified by exactly one")
    locator = rows[0].get("locator")
    if not isinstance(locator, str):
        return _unknown_report("the retained report row carries no locator")
    try:
        url = urlsplit(locator)
        place = pathlib.Path(url.path)
        if url.scheme != "file" or url.netloc or url.query or url.fragment \
                or "%" in url.path or ".." in place.parts:
            return _unknown_report("the locator is not a plain local report path",
                                   locator)
        if storage_root is None:
            return _unknown_report(
                "this run knows no storage root to bind the report to", locator)
        place.relative_to(os.path.realpath(storage_root))
        if place.parts[-3:] != ("custody", attempt, output):
            return _unknown_report(
                "the locator is not this attempt's own custody path", locator)
        given = _bounded_document(place / filename)
        # THE SHAPES ARE VALIDATED INSIDE THE GUARD. Review R2a: a report whose root is
        # `[]`, or whose `provider` is `[1]`, raised `AttributeError` from the `.get`
        # calls BELOW this block -- and in `supervise` that became `serving-failed`,
        # ending healthy Jobs because a supplementary report was malformed.
        if not isinstance(given, dict):
            return _unknown_report(
                "the retained report is not an object", locator)
        if given.get("schema") != schema:
            return _unknown_report(
                "the retained report is not the expected contract", locator)
        if task_id is None or given.get("task_id") != task_id:
            return _unknown_report(
                "the retained report names a different task than this Job's",
                locator)
        provider = given.get("provider")
        if provider is None:
            provider = {}
        if not isinstance(provider, dict):
            return _unknown_report(
                "the retained report's provider record is not an object", locator)
    except (OSError, ValueError, TypeError, KeyError, AttributeError,
            RecursionError) as refused:
        return _unknown_report(
            f"the retained report could not be read: "
            f"{type(refused).__name__}: {refused}", locator)
    reason = provider.get("failure_reason")
    if reason not in _PROVIDER_REASONS:
        return _unknown_report(
            "the report carries no supported provider failure reason", locator)
    code = provider.get("status")
    if code is not None and (type(code) is not int or not -255 <= code <= 255):
        return _unknown_report("the report's provider status is out of contract",
                               locator)
    # THE DIAGNOSTIC IS ONLY EVEN LOOKED AT for an api-error with a nonzero status.
    # `api-error` alone does NOT establish authentication, which is the helper's own
    # rule and the reason this does not classify from a status code.
    diagnostic = (_supported_diagnostic(provider.get("diagnostic"))
                  if reason == "api-error" and type(code) is int and code != 0
                  else None)
    return {"availability": "available", "provider_reason": reason,
            "provider_exit_status": code, "diagnostic": diagnostic,
            "locator": locator,
            "why": None if diagnostic else
            "the report carries no validated provider diagnostic"}


def _locators_of(stage):
    """The manager's OWN artifact locators, as it recorded them. Reads nothing.

    A locator is safe to name and its contents are not read here: the whole
    point of reporting one is that a reader can go and look under their own
    authority.
    """
    held = []
    for one in stage.get("artifacts") or ():
        if isinstance(one, dict):
            found = one.get("locator") or one.get("artifact_id")
            if isinstance(found, str) and found:
                held.append(found)
        elif isinstance(one, str) and one:
            held.append(one)
    return sorted(set(held))


# THE CANONICAL TERMINAL FACTS the exchange observation ACTUALLY publishes.
#
# W306614 review 2026-09-29T17-44-50Z R2b: my first version copied scalar members of the
# exchange only, and the real `terminal` is a DICTIONARY -- `worker_manager/exchange.py`
# `_terminal` returns `ending`, `answered`, `disposition`, `fault_code` and
# `manifest_digest` -- so the whole cause was skipped and my flat `terminal_reason`
# mocks proved nothing about the publisher's shape. These are that shape's own closed
# members, read where they actually live.
_EXCHANGE_SCALARS = ("state", "sequence_id")
_TERMINAL_MEMBERS = ("ending", "disposition", "fault_code", "manifest_digest")
_STEP_MEMBERS = ("operation", "operation_id", "sequence_id", "state", "act",
                 "recorded_at", "digest")


def _closed(given, members):
    """The named members of one nested document, scalars only, copied as recorded."""
    if not isinstance(given, dict):
        return None
    held = {}
    for name in members:
        value = given.get(name)
        if isinstance(value, (str, int, bool)) or value is None:
            held[name] = value
    return held


def _terminal_facts(exchange):
    held = {name: exchange.get(name) for name in _EXCHANGE_SCALARS
            if isinstance(exchange.get(name), (str, int, bool))
            or exchange.get(name) is None}
    terminal = _closed(exchange.get("terminal"), _TERMINAL_MEMBERS)
    if terminal is not None:
        answered = exchange["terminal"].get("answered")
        if isinstance(answered, list) and all(isinstance(one, str)
                                              for one in answered):
            terminal["answered"] = list(answered)
        held["terminal"] = terminal
    for name in ("command", "receipt"):
        step = _closed(exchange.get(name), _STEP_MEMBERS)
        if step is not None:
            held[name] = step
    return held


# WHICH FIELDS MAKE TWO OBSERVATIONS THE SAME FAILURE. Review R2c: a later cause may only
# be attached to the first failure when it is the SAME failure -- same stage, same attempt,
# same episode, same assignment. Anything else is a different failure that happens to be in
# the same Job, and relabelling the first one with its cause would be a misattribution.
_IDENTITY = ("stage_id", "kind", "attempt_id", "episode", "assignment")


def _same_failure(first, later):
    return all(first.get(name) == later.get(name) for name in _IDENTITY)


def _failure_facts(job_id, stage, observed_at, *, storage_root=None,
                   task_id=None):
    """One IMMUTABLE attributed first-failure record, from canonical fields only.

    W306614 review R2: `_attempts_of` answers attempt ids and stage states and
    discards the exchange, the episode/assignment and the artifact locators --
    so a report built from it cannot explain the failure it is reporting. These
    are the identity fields the projection already publishes, plus a provider
    cause that is either the validated closed constant or an EXPLICIT unknown
    beside the locator where the evidence would be.
    """
    exchange = stage.get("exchange") if isinstance(stage.get("exchange"),
                                                   dict) else {}
    runtime = stage.get("runtime") if isinstance(stage.get("runtime"),
                                                 dict) else {}
    report = _retained_report(stage, storage_root=storage_root, task_id=task_id)
    diagnostic = report["diagnostic"]
    locators = _locators_of(stage)
    return {
        "job_id": job_id, "kind": stage.get("kind"),
        "stage_id": stage.get("stage_id"), "work_id": stage.get("work_id"),
        "state": stage.get("state"), "episode": stage.get("episode"),
        "attempt_id": stage.get("attempt_id"), "offer_id": stage.get("offer_id"),
        "assignment": runtime.get("assignment"),
        "runtime_id": runtime.get("runtime_id"),
        "execution_runtime": runtime.get("execution_runtime"),
        # THE CANONICAL EXCHANGE STATE, which is a closed vocabulary, and NOT
        # any message it may carry.
        "exchange_state": exchange.get("state"),
        # AND THE REST OF THE CANONICAL TERMINAL RECORD, whatever of it exists.
        "terminal": _terminal_facts(exchange),
        "observed_at": observed_at,
        # WHAT THE ADAPTER'S OWN RETAINED REPORT SAID, and where it was read from.
        "adapter_report": {name: report[name] for name in
                           ("availability", "provider_reason",
                            "provider_exit_status", "locator", "why")},
        # EITHER THE VALIDATED CONSTANT OR AN EXPLICIT UNKNOWN. Never prose.
        "provider_diagnostic": diagnostic or {
            "schema": "baton.provider-diagnostic/1", "http_status": None,
            "classification": "unknown", "explanation": None,
            "explanation_status": "unavailable",
            "request_id": None, "request_id_status": "unavailable"},
        "provider_cause": (
            "provider-reported-oauth-session-expired-refresh-failed"
            if diagnostic
            and diagnostic["classification"] == "authentication_failed"
            else "unknown"),
        "diagnostic_locators": locators,
    }


def _moment_of(clock):
    """The instant, or None -- because the injected fault WAS the clock.

    Review 2026-09-23T19:22:24Z made the final clock call raise. A finalizer
    that re-raises on the same call it exists to recover from protects
    nothing, so this one answers None and the document says the instant was
    never taken.
    """
    try:
        return clock()
    except BaseException:                                    # noqa: BLE001
        return None


def _completed(measured, gate, clock, *, finalization_failure, uncertainty,
               caught):
    """Make `measured` publishable, whatever the run reached.

    IT NEVER OVERWRITES what the run already recorded -- a default is for a
    member the run never got to, and replacing a real value with a default
    would be this function inventing the account it exists to complete.
    """
    for name, default in _OWED:
        if name not in measured:
            measured[name] = default() if callable(default) else default
    measured["finalization_failure"] = finalization_failure
    if finalization_failure is not None:
        measured["held_because"] = list(measured["held_because"]) + [
            f"this run faulted after serving and did not finish accounting "
            f"for itself: {finalization_failure}"]
    measured["uncertainty"] = list(uncertainty)
    measured["interruptions"] = [one for one in measured["interruptions"]
                                 if one] or [one for one in caught if one]
    if measured.get("finished_at") is None:
        measured["finished_at"] = _moment_of(clock)
    # THE STATE IS DECIDED LAST, from the reasons that exist at publication.
    measured["state"] = "settled" if not measured["held_because"] else "held"
    del gate
    return measured


def supervise(job, control, operations, *, job_ids, bounds, outcome_path,
              deployment_path, caps=None, clock=None, sleep=None,
              monotonic=None, termination=None, turns=None, report=None,
              storage_root=None, task_ids=None):
    """Two Jobs, four admissions, a real stop and an outcome on every path.

    THE PHASES ARE SEPARATE, as they are in `baseline._supervise`: serving is
    not stopping, stopping is not cleanup, cleanup is not the outcome, and the
    outcome is decided by what the run PRODUCED rather than by how the loop
    ended. What this adds over the accepted single-Job supervisor is only the
    two-Job scope: the gate above, and accounting that spans both Jobs.

    THE CLEANUP RESERVE IS INSIDE THE TOTAL. Serving stops at
    `total_seconds - cleanup_seconds` and the cleanup window is additionally
    bounded by what is left of the total, so the deadline is INCLUSIVE and a
    packet declaring a reserve gets one rather than an extension.
    """
    import time

    from baton_v12.job_manager import serve

    # WHERE A PROMPT FAILURE REPORT GOES. W306614, owner 306698: an operator
    # watching the foreground terminal is owed each failed Job as it is
    # observed, not at the end. The default writes to stdout and FLUSHES,
    # because a report an operator cannot see until the process exits is the
    # defect this exists to fix; a test supplies its own sink.
    if report is None:
        def report(line):
            print(line, file=sys.stdout, flush=True)
    held_baseline()
    clock = baseline._moment if clock is None else clock
    sleep = time.sleep if sleep is None else sleep
    monotonic = time.monotonic if monotonic is None else monotonic
    termination = baseline.Termination() if termination is None else termination

    total = int(bounds["total_seconds"])
    reserve = int(bounds["cleanup_seconds"])
    if not 0 < reserve < total:
        raise SupervisorRefusal(
            f"a cleanup reserve of {reserve}s is not inside a total of "
            f"{total}s; a reserve outside the bound is an extension")
    serving_bound = total - reserve

    gate = TwoJobGate(operations, caps=caps or CAPS, job_ids=job_ids)
    started = monotonic()
    uncertainty, caught = [], []
    measured = {"schema": OUTCOME_SCHEMA, "job_ids": list(gate.job_ids),
                "submitted_at": clock(), "bounds": dict(bounds),
                "serving_bound_seconds": serving_bound,
                "caps": dict(gate._caps)}                     # noqa: SLF001
    held = {"stop": None}
    # W306614 CAUSE A. `should_continue` recorded generations, optional turns,
    # caps and the serving deadline, and never looked at whether the selected
    # Jobs could still make progress -- so a run whose two implementations had
    # both failed sat in `serve`'s predicate loop until the bound or an
    # operator's Ctrl-C. `two-jobs-247941-01` spent 439.7 seconds that way.
    #
    # THE CLASSIFICATION IS PER JOB AND IT IS THE ACCEPTED ONE. `_attempts_of`
    # already filters the status projection to ONE Job and `_terminal` reads
    # that Job's own stage states; both are the single-Job supervisor's, used
    # here once per selected Job. They are NOT applied to a flattened map of
    # both Jobs' states -- `_terminal`'s any-exceptional rule would then end a
    # healthy Job because the other one failed, which is the opposite of what
    # this run has to prove.
    pipelines = {}
    failures = {}
    announced = set()
    unreadable = set()

    def _selected():
        """One canonical status read per tick, kept WHOLE.

        `baseline._attempts_of` is the accepted per-Job boundary and answers
        attempt ids and stage states -- and W306614 review R2 is right that it
        DISCARDS the exchange, the episode/assignment and the artifact locators,
        which are exactly the facts a failure report has to carry. So this asks
        the same canonical `status` projection once and keeps the stage entries;
        the per-Job classification below is still `baseline._terminal` over ONE
        Job's states, never a flattened map of both.

        AN INTERRUPTION IS NOT AN UNREADABLE STATUS. Review R1: this used to
        catch `BaseException`, record it and carry on, so a Ctrl-C arriving in
        the status read left admission open until the serving deadline. A
        non-`Exception` is RE-RAISED to the serving interruption handler
        `supervise` already installs, which closes admission and stops promptly.
        An ordinary failure is still UNKNOWN, recorded ONCE per distinct message
        rather than once per tick.
        """
        from baton_v12.job_manager import status

        try:
            document = status(job, gate, observed_at=baseline._moment())  # noqa: SLF001
        except Exception as failure:                         # noqa: BLE001
            said = f"{type(failure).__name__}: {failure}"
            note = f"reading the selected Jobs' status did not complete: {said}"
            if note not in unreadable:
                unreadable.add(note)
                uncertainty.append(note)
            return None
        held = {}
        for entry in document.get("jobs") or ():
            if entry.get("job_id") not in gate.job_ids:
                continue
            held[entry["job_id"]] = [one for one in entry.get("stages") or ()
                                     if isinstance(one, dict)]
        return held

    def _inspect():
        """Classify every selected pipeline, and report each failure ONCE."""
        document = _selected()
        if document is None:
            # UNKNOWN IS NOT REMEMBERED AS TERMINAL and it ERASES NOTHING.
            # `pipelines` is current eligibility, so it is cleared; `failures`
            # is what was observed, so it stands.
            pipelines.clear()
            return
        observed_at = _moment_of(clock)
        for job_id in gate.job_ids:
            stages = document.get(job_id)
            if stages is None:
                pipelines.pop(job_id, None)
                continue
            states = {one.get("kind"): one.get("state") for one in stages}
            seen = {}
            for one in stages:
                for attempt in [one.get("attempt_id")] + [
                        two.get("attempt_id")
                        for two in one.get("episodes") or ()]:
                    if attempt is not None:
                        seen[attempt] = one.get("kind")
            reached = baseline._terminal(states)              # noqa: SLF001
            pipelines[job_id] = {
                "reached": reached, "states": dict(states),
                "attempts": dict(seen), "observed_at": observed_at}
            if reached != "exceptional":
                continue
            # THE FIRST FAILURE IS RECORDED ONCE AND NEVER REWRITTEN. A later
            # tick that reads a different state does not get to restate what
            # this Job's original failure was.
            failed = [one for one in stages
                      if one.get("state") == "exceptional"]
            supplemented = False
            if failed:
                facts = _failure_facts(
                    job_id, failed[0], observed_at, storage_root=storage_root,
                    task_id=(task_ids or {}).get(job_id))
                if job_id not in failures:
                    failures[job_id] = facts
                elif (failures[job_id]["provider_cause"] == "unknown"
                        and facts["provider_cause"] != "unknown"
                        and _same_failure(failures[job_id], facts)):
                    # A PROVISIONAL UNKNOWN IS NOT FINAL, AND IT IS NOT A SLOT
                    # EITHER. The adapter's report may be retained AFTER the stage
                    # first projects exceptional, so a later validated cause must
                    # not be suppressed -- but review 2026-09-29T17-44-50Z R2c is
                    # right that keying on the Job alone would attach a DIFFERENT
                    # failure's cause to the first one. The identity has to match:
                    # same stage, attempt, episode and assignment. A changed
                    # failure keeps its own facts and supplements nothing.
                    failures[job_id] = dict(
                        failures[job_id],
                        provider_cause=facts["provider_cause"],
                        provider_diagnostic=facts["provider_diagnostic"],
                        adapter_report=facts["adapter_report"],
                        diagnostic_locators=facts["diagnostic_locators"],
                        cause_observed_at=facts["observed_at"],
                        cause_supplemented=True)
                    supplemented = True
            # DEDUPLICATED BY WHAT WAS ACTUALLY OBSERVED, so a repeat tick is
            # silent and a Job that fails differently later is not.
            #
            # AND THE CAUSE IS PART OF THE OBSERVATION. Review R2c: the key held
            # only stage states and attempt names, so a cause that became known
            # while the states stayed the same was retained in the outcome and
            # never reported promptly -- which is the whole point of reporting.
            mark = (job_id, tuple(sorted(states.items())),
                    tuple(sorted(seen)),
                    (failures.get(job_id) or {}).get("provider_cause"))
            if mark in announced:
                continue
            announced.add(mark)
            facts = failures.get(job_id) or {}
            report(
                f"Job {job_id} FAILED: "
                f"{', '.join(f'{kind} {state}' for kind, state in sorted(states.items()))}"
                f"; stage {facts.get('kind')} attempt {facts.get('attempt_id')}"
                f" episode {facts.get('episode')} work {facts.get('work_id')}"
                f" assignment {facts.get('assignment')}"
                f"; provider cause {facts.get('provider_cause')}"
                f"; diagnostic "
                f"{(facts.get('provider_diagnostic') or {}).get('classification')}"
                f"; evidence "
                f"{', '.join(facts.get('diagnostic_locators') or []) or 'no locator recorded'}"
                f"; observed {facts.get('observed_at')}"
                f"; this run has no retry, so its remaining stages cannot "
                f"progress. Other selected Jobs continue.")

    def should_continue():
        """One tick's decision, and every reason it can end the run.

        IT ALSO CAPTURES THE GENERATIONS WHILE THEY EXIST. An allocation is a
        live record: by the time the run has stopped, a released one may no
        longer answer, and a generation read only at the end came back empty.
        Reading each tick keeps the last value each attempt actually had.
        """
        gate.generations.update(
            generations_from(control, gate, uncertainty, caught))
        # THE WORKER-TURN SEAM, and it is a SEAM rather than a capability.
        # In a real deployment the runtime IS the turn: the manager starts a
        # container and the worker answers on its own. This build has no
        # daemon, so a deterministic driver stands exactly where the container
        # would, at the same boundary the accepted lifecycle fixtures use. A
        # caller that supplies none gets a run that starts nothing -- which is
        # what every case before this one measured.
        if turns is not None:
            # THE CONTEXT A TURN NEEDS, because a turn has to reach the
            # attempt's mounted workspace and that lives on the composition.
            # Review 2026-09-23T18:33:25Z: a callback given only the gate can
            # do no work, which is why the entry-point case proved nothing.
            baseline._guarded(
                lambda: turns(gate, {"operations": operations, "job": job,
                                     "control": control}),
                None, what="the deterministic worker turn",
                uncertainty=uncertainty, interrupted=caught)
        if gate.refusals:
            held["stop"] = "invocation-cap-refused"
            return False
        # W306614: EVERY SELECTED PIPELINE TERMINAL IS A STOP, and it is the
        # only new one. One Job failing does not end the run -- the other keeps
        # serving until it reaches its own ending -- and a Job whose status
        # could not be read is not counted, so an unreadable projection leaves
        # the deadline as the backstop it was always meant to be rather than
        # becoming a detector.
        _inspect()
        if (len(pipelines) == len(gate.job_ids)
                and all(one["reached"] is not None
                        for one in pipelines.values())):
            held["stop"] = "pipelines-terminal"
            return False
        if monotonic() - started >= serving_bound:
            held["stop"] = "serving-bound-exceeded"
            return False
        return True

    serving_failure = interrupted = None
    finalization_failure = faulted = None
    # THE HANDLER IS INSTALLED AROUND EVERYTHING AND RESTORED AT THE END --
    # and now it actually is. Review 2026-09-23T19:22:24Z injected a fault in
    # the FINAL CLOCK CALL, after serving and cleanup, and measured
    # `installed=True, restored=False, outcome_exists=False`: the `finally`
    # surrounded `_publish` alone, so every line between `gate.stop()` and the
    # publication ran outside the protection this comment claimed. A fault
    # there left this process holding a signal handler for a run that was over
    # with nothing on disk. The comment is part of why I did not look again.
    #
    # The outer `try` below spans from here to the end; its `finally` attempts
    # the outcome and restores the handler whatever happened in between.
    termination.install()
    try:
        try:
            serve(job, gate, clock=clock, sleep=sleep,
                  should_continue=should_continue, interval=1)
        except Exception as failure:                         # noqa: BLE001
            # A SERVING FAULT STOPS ADMISSION AND STILL OWES CLEANUP.
            serving_failure = f"{type(failure).__name__}: {failure}"
            held["stop"] = held["stop"] or "serving-failed"
        except BaseException as failure:                     # noqa: BLE001
            interrupted = f"{type(failure).__name__}: {failure}"
            held["stop"] = held["stop"] or "interrupted"

        # ADMISSION IS CLOSED BEFORE ANYTHING IS CANCELLED. That is
        # what makes the cleanup window unable to start a runtime while it
        # settles the ones this run already has.
        gate.stop()
        termination.defer()
        measured["stopped"] = held["stop"] or "stopped-without-a-reason"
        measured["serving_failure"] = serving_failure
        measured["admissions"] = dict(gate.admissions)
        measured["admitted_attempts"] = sorted(gate.launched)
        measured["gate_refusals"] = list(gate.refusals)
        measured["foreign_admissions"] = list(gate.foreign)
        measured["admission_closed_before_cancellation"] = True

        # CANCELLATION, then the journal's own word on every runtime this run
        # started. Both are the accepted helpers; neither is
        # reimplemented here.
        remaining = max(0.0, total - (monotonic() - started))
        measured["cleanup_window_seconds"] = remaining
        # THE ACCEPTED CANCELLATION PATH. This called
        # `operations.cancel`, which
        # NO composition exposes -- the port is `cancel_attempt` -- so every
        # attempt was recorded as "no cancellation port" while the run still
        # reported its stop. That is reporting a LEAK AS A CLEAN STOP.
        # `_cancel_active` fences the exact participant and generation at the
        # Authority before ordering quiescence, and reports honestly when a
        # composition really does offer no port.
        measured["cancellation"] = baseline._guarded(
            lambda: baseline._cancel_active(
                operations, control,
                {"deployment": {"config_path": deployment_path}},
                dict(gate.launched), dict(held.get("states") or {}),
                uncertainty, reason=measured["stopped"],
                launched=set(gate.launched),
                interrupted=caught),
            {}, what="the cancellation of what was still executing",
            uncertainty=uncertainty, interrupted=caught)
        # `_cleanups` asks the journal about a destroy bound to THIS
        # deployment's
        # retention policy, and it reads that policy out of the deployment
        # document rather than a second copy -- so the packet shape it wants is
        # the one member it actually uses.
        # THE RESERVED WINDOW IS DRIVEN, not merely recorded. Review
        # 2026-09-23T17:44:56Z: "remaining deadline only recorded, no bounded
        # cleanup execution". Closing the gate stops the NEXT runtime; what
        # settles the ones already started is the manager's ordinary sweep, and
        # with admission closed it can finish endings without being able
        # to admit anything. Each pass is inside what is left of the TOTAL,
        # so the reserve is a window rather than an extension.
        from baton_v12.job_manager import sweep

        measured["cleanup_sweeps"] = 0
        settled = None
        while monotonic() - started < total:
            settled = baseline._guarded(
                lambda: baseline._cleanups(
                    control, {"deployment": {"config_path": deployment_path}},
                    dict(gate.launched)),
                None, what="the cleanup journal", uncertainty=uncertainty,
                interrupted=caught)
            if settled is not None and not settled.get("outstanding"):
                break
            if not gate.launched:
                break
            baseline._guarded(lambda: sweep(job, gate, now=clock()), None,
                              what="a cleanup sweep", uncertainty=uncertainty,
                              interrupted=caught)
            measured["cleanup_sweeps"] += 1
            if measured["cleanup_sweeps"] >= CLEANUP_SWEEPS:
                break
        measured["cleanup"] = ({} if settled is None
                               else settled.get("cleanup", {}))
        measured["outstanding_cleanup"] = (
            sorted(gate.launched) if settled is None
            else sorted(settled.get("outstanding", ())))
        measured["uncertainty"] = uncertainty
        measured["interruptions"] = [one for one in ([interrupted] + caught)
                                     if one]

        # THE FINAL CLEANUP READ, after the last sweep rather than before it.
        # Review 2026-09-23T18:00:25Z. A cleanup that settled on the last sweep
        # would otherwise be reported as outstanding by a read taken before it.
        settled = baseline._guarded(
            lambda: baseline._cleanups(
                control, {"deployment": {"config_path": deployment_path}},
                dict(gate.launched)),
            settled, what="the final cleanup journal read",
            uncertainty=uncertainty, interrupted=caught)
        measured["cleanup"] = ({} if settled is None
                               else settled.get("cleanup", {}))
        measured["outstanding_cleanup"] = (
            sorted(gate.launched) if settled is None
            else sorted(settled.get("outstanding", ())))

        # THE EXPLICIT SHUTDOWN DECLARATION, for what the sweeps could not
        # settle. W247941: a runtime whose worker never answered has no
        # ordinary ending in its future -- the preserved two-Job run is two of
        # them -- and the abandonment is the ending that belongs to it.
        #
        # OUTSTANDING IS THE CANDIDATE LIST AND NOT THE ELIGIBILITY. Review
        # 2026-09-24T10:23:12Z. `_abandonment_eligible` asks each attempt's
        # own state, and an answered result, a terminal axis, an uncertain
        # observation or an unattached runtime each keeps its own ending.
        #
        # AND `outstanding_cleanup` ABOVE IS LEFT AS IT IS. `_cleanups` reads
        # the ORDINARY cleanup journal, which an abandonment does not write
        # to; rounding these up into it would report one ending's record under
        # another's name. What was declared is reported separately, failures
        # included.
        measured["abandonment"] = baseline._guarded(
            lambda: _declare_abandonment(
                operations, control, gate, measured["outstanding_cleanup"],
                reason=measured["stopped"],
                policy=baseline._retention_of(
                    {"deployment": {"config_path": deployment_path}}),
                # THE SELECTED TOTAL, NOT A SECOND BUDGET. Review [R1]: the
                # declaration may remove and discharge, so it is admitted
                # against what is left of the run rather than started after
                # the window it was supposed to fit inside.
                remaining=lambda: total - (monotonic() - started)),
            {}, what="the shutdown abandonment declaration",
            uncertainty=uncertainty, interrupted=caught)
        held_declarations = measured["abandonment"] or {}
        measured["abandoned_cleanup"] = _settled_by_abandonment(
            held_declarations)
        measured["undeclared_cleanup"] = sorted(
            attempt for attempt in held_declarations
            if attempt not in set(measured["abandoned_cleanup"]))
        # THE OVERALL UNRESOLVED SET, derived from BOTH ending journals.
        # Review [R2]: `outstanding_cleanup` is the ordinary journal's answer
        # and stays exactly that; saying an attempt has "no positive cleanup"
        # when an abandonment settled and discharged it is false reporting.
        measured["unresolved_cleanup"] = sorted(
            set(measured["outstanding_cleanup"])
            - set(measured["abandoned_cleanup"]))

        # AND THE VERDICTS, DERIVED FROM EACH JOB'S OWN FROZEN RESULT. Review
        # 2026-09-23T18:00:25Z: "success must require results not admission
        # counts". An admission is a run starting something; a verdict is the
        # thing a review Job exists to produce.
        # THE GENERATIONS COME FROM THE ALLOCATIONS, read once here, before any
        # verdict is derived: `review_for_attempt` fences an attachment to one
        # activated generation and refuses `None`.
        gate.generations.update(
            generations_from(control, gate, uncertainty, caught))
        measured["generations"] = dict(gate.generations)
        measured["verdicts"] = verdicts_of(control, gate, uncertainty, caught)

        # W306614: THE PER-JOB FACTS TRAVEL IN THE OUTCOME. `held_because` used
        # to name only the missing verdicts, so a reader could not tell a Job
        # that failed from one that never started.
        measured["pipelines"] = {one: dict(what)
                                 for one, what in sorted(pipelines.items())}
        # AND THE IMMUTABLE FIRST FAILURES, which survive a later unreadable
        # status. Review R2: the hold reasons are derived from THESE, not from
        # current eligibility, so a status that stops answering cannot quietly
        # turn a failed run into one that merely has no verdicts.
        measured["failures"] = {one: dict(what)
                                for one, what in sorted(failures.items())}

        held_because = []
        for one, what in sorted(failures.items()):
            held_because.append(
                f"Job {one} ended exceptionally at {what.get('kind')} "
                f"{what.get('state')} (attempt {what.get('attempt_id')}, "
                f"episode {what.get('episode')}, work {what.get('work_id')}); "
                f"provider cause {what.get('provider_cause')}, diagnostic "
                f"{(what.get('provider_diagnostic') or {}).get('classification')}"
                f"; this run has no retry, so its dependent stages could "
                f"not run")
        for one in gate.job_ids:
            if one not in measured["verdicts"]:
                held_because.append(
                    f"Job {one} produced no attributed verdict; a "
                    f"two-Job review run that collected fewer than two has "
                    f"not done its work")
        if not measured["admitted_attempts"]:
            held_because.append(
                "no runtime was ever launched, so there is nothing "
                "this run can claim to have stopped or cleaned up")
        if measured.get("unresolved_cleanup"):
            held_because.append(
                f"these admitted runtimes have no positive cleanup under "
                f"either ending: "
                f"{', '.join(measured['unresolved_cleanup'])}")
        # AND WHAT THE DECLARATION COULD NOT FINISH IS NAMED SEPARATELY, with
        # its own reason, because "unresolved" and "refused for this reason"
        # are different things to an operator holding a stopped Work.
        declarations = measured.get("abandonment") or {}
        for attempt, held in sorted(declarations.items()):
            if attempt in set(measured.get("abandoned_cleanup", ())):
                continue
            held_because.append(
                f"the shutdown declaration did not settle {attempt}: "
                f"{held.get('why') or 'cleanup ' + str(held.get('cleanup'))}"
                + ("" if held.get("gate_discharged", True)
                   else "; its quiescence gate is not discharged"))
        if serving_failure:
            held_because.append(f"serving failed: {serving_failure}")
        if gate.refusals:
            held_because.append("an admission was refused by the cap")
        if uncertainty:
            held_because.extend(uncertainty)
        measured["held_because"] = held_because
        measured["state"] = "settled" if not held_because else "held"
        measured["finished_at"] = _moment_of(clock)
    except BaseException as failure:                         # noqa: BLE001
        # A FAULT AFTER SERVING IS ACCOUNTED FOR, NOT LOST. It is named in the
        # document, forced into `held`, published by the `finally` below and
        # re-raised after the handler is restored -- a run that broke while
        # accounting for itself must not return as though it had finished.
        faulted = failure
        finalization_failure = f"{type(failure).__name__}: {failure}"
        if not isinstance(failure, Exception):
            caught.append(finalization_failure)
    finally:
        # THE OUTCOME IS ATTEMPTED ON EVERY PATH and the handler is restored on
        # every path, including the ones where the attempt itself fails.
        publication_failure = None
        try:
            _completed(measured, gate, clock,
                       finalization_failure=finalization_failure,
                       uncertainty=uncertainty, caught=caught)
            baseline._publish(outcome_path, measured)
        except BaseException as failure:                     # noqa: BLE001
            publication_failure = failure
        finally:
            termination.restore()

    if publication_failure is not None:
        # NOTHING IS ON DISK, which is the most serious ending this run has
        # and the only one an operator cannot read about afterwards.
        raise publication_failure
    if faulted is not None:
        raise faulted
    if measured["interruptions"]:
        # THE RETAINED OUTCOME TRAVELS WITH IT, as the accepted exception
        # carries it: an interruption is owed to the operator who sent it, and
        # a caller that wants to read what the run left behind still can.
        raise baseline.SupervisorInterrupted(measured["interruptions"][0],
                                             measured)
    return measured


def _storage_root(deployment):
    """Where THIS deployment says its workspaces live. One of its own members.

    Every configured worker carries `workspace_storage`, and a run whose workers
    disagree about it is not one this reader will bind a report to.
    """
    held = {(one.get("deployment") or {}).get("workspace_storage")
            for one in deployment.get("workers") or ()}
    held.discard(None)
    return held.pop() if len(held) == 1 else None


def _task_ids(deployment):
    """Each Job's OWN task id, read from the task document the deployment names.

    NOT RECONSTRUCTED FROM A CONVENTION. The accepted helper rebuilds this from
    `<incarnation>-<last character of the job id>`, which is one packet's naming
    rule; this reads the declaration instead, so a report is bound to the task
    this deployment actually configured.
    """
    import json

    # THROUGH `job_bindings`, which is the deployment's OWN statement of which worker
    # produces which Job. My first version matched the task document's FILE NAME against
    # the Job id, and the connected fixture measured it returning nothing at all: its
    # documents are `task.json` and `task-b.json`, and their ids are `w119114-...` and
    # `w130224-...`. A convention is not a binding.
    workers = {one.get("worker_id"): (one.get("deployment") or {})
               for one in deployment.get("workers") or ()}
    held = {}
    for binding in deployment.get("job_bindings") or ():
        job_id = binding.get("job_id")
        configured = workers.get(binding.get("source_worker_id")) or {}
        place = configured.get("task_document")
        if not job_id or not place:
            continue
        try:
            with open(place, encoding="utf-8") as handle:
                document = json.load(handle)
        except (OSError, ValueError):
            continue
        task_id = document.get("task_id")
        if isinstance(task_id, str):
            held[job_id] = task_id
    return held


def main(argv=None, *, stream=None, credential_provider=None,
         engine_run=None, clock=None, checkout=None, turns=None,
         monotonic=None, sleep=None):
    """ONE command: open the stores, compose, submit, serve bounded, stop.

    Review 2026-09-23T17:44:56Z: operator step 7 named `job`, `control` and
    `composed` without defining them, and step 4 independently served
    unbounded. A packet whose stop instruction cannot be typed is not an
    instruction. This is the whole bounded run behind one invocation, and it
    is the only supported way to serve this arrangement.

    IT STARTS NOTHING ITS DOCUMENTS DO NOT NAME. The deployment and the
    submission are the ones `two_jobs.py` composed; this opens their stores
    and hands the composed operations to `supervise`.
    """
    import argparse
    import json

    stream = sys.stdout if stream is None else stream
    parser = argparse.ArgumentParser(
        prog="two_job_supervisor",
        description="Serve one bounded two-Job run and stop it.")
    parser.add_argument("--deployment", required=True,
                        help="the deployment.json two_jobs.py wrote")
    parser.add_argument("--submission", required=True,
                        help="the submission.json two_jobs.py wrote")
    parser.add_argument("--job-store", required=True)
    parser.add_argument("--control-store", required=True)
    parser.add_argument("--incarnation", required=True)
    parser.add_argument("--outcome", required=True)
    parser.add_argument("--total-seconds", type=int, default=600)
    parser.add_argument("--cleanup-seconds", type=int, default=60)
    chosen = parser.parse_args(argv)

    held_baseline()
    from tools import stage_execution
    from baton_v12.job_manager import JobStore, submit
    from baton_v12.worker_manager import ControlStore

    with open(chosen.deployment, "r", encoding="utf-8") as handle:
        deployment = json.load(handle)
    with open(chosen.submission, "r", encoding="utf-8") as handle:
        submission = json.load(handle)
    job_ids = [one["job_id"] for one in deployment["job_bindings"]]

    # BOTH OPENERS REQUIRE A CLOCK, and neither was given one -- so this
    # command could not open a store at all. Review 2026-09-23T17:56:23Z
    # confirmed it against the pinned signatures. `baseline._moment` is the
    # instant source the accepted supervisor uses; there is no second clock.
    #
    # AND ACQUISITION IS INSIDE THE `try`. It was above it, so a failure
    # opening the control store or composing the operations leaked the handles
    # already taken. `opened` is appended to as each one succeeds, and the
    # `finally` closes exactly what exists.
    opened = []
    measured = None
    try:
        moment = baseline._moment if clock is None else clock
        job = JobStore.open(chosen.job_store,
                            authority_uuid=deployment["authority_uuid"],
                            incarnation=chosen.incarnation,
                            clock=moment)
        opened.append(job)
        control = ControlStore.open(chosen.control_store,
                                    incarnation=chosen.incarnation,
                                    clock=moment)
        opened.append(control)
        # THE SEAMS, and every one of them defaults to PRODUCTION. A caller
        # that supplies none gets the real provider, the real engine, the real
        # clock and no worker turn -- which is exactly what an operator typing
        # the documented command gets. Review 2026-09-23T18:26:13Z asked for
        # the entry point to be reachable by a deterministic witness with a
        # disposable provider and registry; these are where that witness
        # stands, at the same boundary the accepted lifecycle fixtures use.
        composing = {}
        if credential_provider is not None:
            composing["credential_provider"] = credential_provider
        if engine_run is not None:
            composing["engine_run"] = engine_run
        if clock is not None:
            composing["clock"] = clock
        if checkout is not None:
            composing["checkout"] = checkout
        composed = stage_execution.operations_from(deployment, job, control,
                                                   **composing)
        opened.append(composed)
        submit(job, submission)
        measured = supervise(
            job, control, composed, job_ids=job_ids,
            bounds={"total_seconds": chosen.total_seconds,
                    "cleanup_seconds": chosen.cleanup_seconds},
            outcome_path=chosen.outcome,
            deployment_path=chosen.deployment,
            turns=turns, monotonic=monotonic, sleep=sleep, clock=clock,
            storage_root=_storage_root(deployment),
            task_ids=_task_ids(deployment))
    except baseline.SupervisorInterrupted as stopped:
        # W306614 CAUSE B. `supervise` publishes the outcome, restores the
        # handler and THEN raises -- deliberately, and the lower-level contract
        # is preserved exactly. What was missing is the other half of it here:
        # an operator who pressed Ctrl-C got this exception's traceback out of
        # `main`, so the one thing they needed -- that the outcome was retained,
        # and where -- was the one thing not printed.
        #
        # THE INTERRUPT IS NOT SWALLOWED. The status is 130, the report says the
        # run did not finish, and the ORIGINAL per-Job failures are named before
        # the interruption so the first cause survives the last event. This is
        # the accepted single-Job presentation (`baseline.main`) at the two-Job
        # boundary, not a new one.
        interrupted = stopped.outcome or {}
        print(f"interrupted: {stopped}", file=stream)
        print(f"the outcome WAS retained at {chosen.outcome}", file=stream)
        # FROM `failures`, NOT `pipelines`. Review R2: `pipelines` is current
        # eligibility and an unreadable status empties it, so reporting the
        # original cause from it would lose exactly the fact the operator needs
        # after an interruption.
        for one, what in sorted((interrupted.get("failures") or {}).items()):
            print(f"Job {one} had already FAILED: {what.get('kind')} "
                  f"{what.get('state')}, attempt {what.get('attempt_id')}, "
                  f"provider cause {what.get('provider_cause')}, evidence "
                  f"{', '.join(what.get('diagnostic_locators') or []) or 'no locator recorded'}",
                  file=stream)
        print(f"state {interrupted.get('state')!r}, stopped "
              f"{interrupted.get('stopped')!r}; "
              f"{len(interrupted.get('held_because') or [])} held reason(s); "
              f"{len(interrupted.get('unresolved_cleanup') or [])} unresolved "
              f"cleanup", file=stream)
        return 130
    finally:
        # EVERY HANDLE THIS COMMAND OPENED IS CLOSED, on every path, newest
        # first: a composition closed after its stores would be closing over
        # handles that are already gone.
        for one in reversed(opened):
            try:
                one.close()
            except Exception:                                # noqa: BLE001
                pass
    if measured is None:                                     # pragma: no cover
        return 2
    print(json.dumps({"state": measured["state"],
                      "stopped": measured["stopped"],
                      "outcome": chosen.outcome}, indent=2), file=stream)
    return 0 if measured["state"] == "settled" else 1


if __name__ == "__main__":                                   # pragma: no cover
    sys.exit(main())
