"""W103525: the scripted scenario driver, its trace artifact and an INDEPENDENT
causal validator.

WHAT THIS IS AND WHAT IT DELIBERATELY IS NOT. It drives REAL owners -- a real Job
store, the real pool activation and the real `scheduler.reserve` -- over a fixed,
scripted scenario on LOGICAL ticks, and records what those owners actually
answered. It is a test-only observation surface: nothing here is a product
contract, nothing here is a TUI presentation, and nothing here decides an
outcome. `PLAN.md` fixes that boundary and this module stays inside it.

THE VALIDATOR DOES NOT TRUST THE DRIVER. Its whole value is being a second
opinion, so it re-derives every invariant from the exported records alone --
never from the driver's own bookkeeping, and never from the live stores. That is
why `validate` takes an artifact rather than a run: a validator that could ask
the scheduler would be asking the thing it is checking.

AND AN EXPECTED GAP IS NEVER A PASS. Reviewer revalidation 2026-09-12T15:54:16Z
records three confirmed contract mismatches which the owner retained as OPEN.
Where a scenario distinguishes them, this module records a `gap` -- a first-class
artifact member with its own reason -- and the tests assert the gap is present.
A gap that quietly became a pass would be the one outcome this Work exists to
prevent.

NO CREDENTIALS TRAVEL. The artifact carries identities, digests, operation ids
and evidence locators; bearer strings, credential material and session
transcripts are never read into it.
"""

import hashlib
import json
import os
import platform
import sys

# THE ARTIFACT IS VERSIONED because a later reader must be able to tell which
# shape it is holding. A trace whose schema it does not know is not one it may
# validate by guessing.
SCENARIO_SCHEMA = "baton.v12.scheduler-trace-scenario/1"
TRACE_SCHEMA = "baton.v12.scheduler-trace/1"

# WHAT ONE RECORDED ACT NAMES. Every member is either a durable identity this
# run really observed or an explicit absence; `None` means "this owner reported
# none", which is a different statement from "this driver did not look".
RECORD_MEMBERS = ("tick", "job_id", "stage_id", "episode", "attempt_id",
                  "act", "outcome", "worker_id", "participant", "principal",
                  "operation_id", "runtime_id", "session_id", "evidence",
                  "cause",
                  # D1: THE OWNER'S OWN INSTANT, when the owner recorded one.
                  # It is carried so a reader -- and the validator -- can check
                  # the record order against the owners' order instead of
                  # trusting the extractor's.
                  "recorded_at",
                  # Review 2026-09-13T00:47:10Z R6: AND THE COMPLETION'S OWN
                  # OWNER BINDING. Checking a Job LABEL is not checking a
                  # subject: swapping the Job and stage labels of two intact
                  # receipt chains validated clean, so A's direct chain
                  # purported to authorize B's derived import. The integrator's
                  # own `observe` answers which proposal, result, receipt and
                  # runtime this completion is, and that answer travels here.
                  "completion",
                  # Review 2026-09-12T23:32:26Z R1: AND THE CORRECTION'S OWN
                  # JUDGMENT. The first correction rule treated ANY performed
                  # record on a review stage as the judgment behind a
                  # correction, so a trace with the review RESERVED and nothing
                  # else validated -- a reservation proves no verdict. The
                  # verdict travels with the act now.
                  "correction",
                  # Owner155646: AND THE SESSION'S OWN CONTEXT, for the same
                  # reason the authorization context exists. `session_id` is an
                  # identity and an identity is not evidence about itself: the
                  # posture a session was opened in, the epoch the owner
                  # allocated, the provider id it was later bound to and the
                  # state it is in are what let a reader -- and the rules below
                  # -- tell a consent session from an execution one without
                  # parsing the reference string.
                  "session",
                  # Review 2026-09-12T17:30:56Z: THE DECISION'S OWN CONTEXT.
                  # The first authorization records dropped the disposition, the
                  # candidate digest, the target, the effective scope and the
                  # policy generation -- and my comment claiming scope and policy
                  # "travel with it" was simply false: the test asserted the
                  # scope and then threw it away. They travel now, in one member,
                  # because the receipt already carries every one of them.
                  "authorization")

# THE ACTS THIS DRIVER CAN RECORD, closed so a typo cannot become a new act.
ACTS = ("submit", "activate-pool", "reserve", "offer", "accept", "claim",
        "start", "complete", "release", "reopen", "observe",
        # C1: THESE THREE ARE RECORDABLE AND DELIBERATELY NOT VALIDATED. They
        # stay in the vocabulary because a driver may legitimately observe them,
        # and `VALIDATED_ACTS` below deliberately excludes them -- so a trace
        # carrying one is reported `unvalidated-act` rather than passing. Naming
        # an act is not implementing its contract, and the honest answer while
        # the rule is missing is to say the act is unproved.
        "correct", "verify", "review", "approve", "integrate")

# R3, review 2026-09-12T16:18:34Z: A STAGE COMPLETION AND AN ALLOCATION RELEASE
# ARE DIFFERENT FACTS and only the second frees capacity. The first draft treated
# `complete` -- and, worse, `reopen` -- as freeing a worker, so a restart looked
# like a release and a completed-but-unreleased allocation looked idle. Restart
# does not release custody; only the owner's own release/settlement evidence does.
RELEASING_ACTS = ("release",)

# AND THE ORDER THE VALIDATOR REQUIRES WITHIN ONE ATTEMPT. Reserve happens
# before the offer side effect, the offer before the claim, the claim before any
# start. `scheduler.reserve`'s own contract is the first half of this and the
# manager's offer/claim settlement is the second; the validator re-checks it
# from the record stream rather than trusting either.
ATTEMPT_ORDER = ("reserve", "offer", "accept", "claim", "start", "complete")

# A CORRECTION OF MY OWN EARLIER CLAIM, kept here because the reasoning matters.
#
# I first emitted an `accept` and a `claim` from the single `offer.settle`
# receipt, and the exactly-once invariant correctly refused it: one operation
# identity cannot be two performed acts. I concluded from that refusal that the
# build journals no separate acceptance, and recorded a gap saying so. THAT
# CONCLUSION WAS WRONG. The offer is its own owner: `OFFER_STATES` contains
# `accepted`, the offer row carries `accepted_at`, and `offers._require_accepted`
# guards the claim. My mistake was reading one receipt's shape as the whole
# build's, and the lesson -- the same one review 2026-09-12T17:15:58Z taught
# about team capability grants -- is that a refusal encountered while extracting
# says something about the extraction, not about what the system can do.
#
# Session identity is likewise a real owner fact: `agent_sessions_of` is public
# and `AGENT_SESSION_COLUMNS` carries posture, epoch, participant and provider
# session id, distinct from worker and runtime identity.
UNREPRESENTED_EVIDENCE = ()

# C1, review 2026-09-12T16:35:09Z: WHICH ACTS THIS VALIDATOR ACTUALLY CHECKS.
#
# `review`, `integrate` and `correct` were added to `ACTS` and then checked by
# nothing, so a trace carrying a solitary performed review or integration
# validated clean -- the validator silently accepted an event it had no rule for.
# Naming an act is not implementing its contract. Anything outside this set is
# now reported as `unvalidated-act` instead of passing, which is the honest
# answer until its own predecessor rule exists.
VALIDATED_ACTS = ATTEMPT_ORDER + ("submit", "activate-pool", "observe",
                                  "reopen", "release",
                                  # Owner155646: `correct` HAS ITS RULE NOW.
                                  # It stayed unvalidated through every earlier
                                  # claim because saying so was the honest
                                  # answer while the rule was missing;
                                  # `_corrections_name_their_cause` is that
                                  # rule, and the act joins the checked set the
                                  # moment it exists rather than before.
                                  "correct",
                                  "verify", "review", "approve", "integrate")

# THE AUTHORIZATION ACTS AND WHAT EACH REQUIRES, keyed by SUBJECT rather than by
# attempt. A review and an integration are decisions about a proposal or a
# candidate, not steps of one worker attempt, so their predecessor relation is
# over the thing being judged: nothing may be integrated that was not reviewed.
#
# `correct` is deliberately still absent from `VALIDATED_ACTS`: this module has
# no rule for it, and saying so is the honest answer.
SUBJECT_AUTHORIZATION = {"verify": (), "review": (), "approve": (),
                         # AN IMPORT NEEDS ALL THREE JUDGMENTS, not a review
                         # alone: the first rule required only `review`, so a
                         # candidate with no verification and no approval
                         # validated clean.
                         "integrate": ("verify", "review", "approve")}

# AND WHAT EACH KIND'S OWN POSITIVE DECISION IS. Review 2026-09-12T17:30:56Z: the
# first extractor discarded the disposition entirely, so a review recorded
# `changes-requested` emitted a performed authorization and validated clean. A
# decision word is the whole content of a judgment; dropping it turns a refusal
# into an approval.
POSITIVE_DISPOSITION = {"verify": "passed", "review": "accepted",
                        "approve": "approved", "integrate": "integrated"}

# AND WHAT AN AUTHORIZATION RECORD MUST NAME. A receipt that does not say WHO
# decided, under which principal and with which operation identity is not
# evidence that anyone authorized anything -- which is the whole point of asking
# the Authority rather than asserting the outcome.
AUTHORIZATION_MEMBERS = ("participant", "principal", "operation_id",
                         "evidence")

# WHAT A CORRECTION RECORD MUST CARRY, and every member is on the owners' own
# answers: `job_manager.ending.settlement_of` for the settled review episode and
# `worker_manager.review_cycles.verdict_of` for the committed judgment it names.
#
# I CLAIMED THIS SEAM DID NOT EXIST AND I WAS WRONG. My last handoff recorded a
# gap saying no public reader answers a verdict from its attachment, and asked for
# a new API. The reviewer disproved it with the build's own readers in a real
# composed run: the settlement carries `evidence.verdict_id`, the outcome and the
# ROUTED next attempt, and `verdict_of` proves and answers the committed
# disposition with its attachment, checkpoint, line and reviewer identity. The
# gap is withdrawn, not softened, and no product change was needed.
# WHAT A COMPLETED INTEGRATION MUST CARRY, and every member is on the document
# `stage_execution.Integration.observe` already answers for a completed stage.
# `result_id` and `runtime_id` are legitimately null on one branch each -- that
# difference IS the branch -- so what is required is the MEMBER, not a value.
COMPLETION_CONTEXT = ("proposal_id", "source_proposal_id", "result_id",
                      "integration_receipt_id", "runtime_id",
                      "execution_runtime")

# AND THE OWNER'S OWN WORDS FOR THE TWO COMPLETED BRANCHES.
#
# Review 2026-09-13T01:00:50Z R6c: the first form checked that the six members
# EXISTED and compared three of them, so changing only a direct completion's
# runtime to another attempt's -- while its own start still named the real one --
# validated clean, and so did claiming `running` execution on a completed
# account. Existence is not agreement, which is the third time this Work has had
# to learn it in a different place.
#
# `stage_execution.Integration.account` emits a DIRECT completed context with
# the owned runtime id, `quiescent` execution, a null result and one proposal
# that is its own source; `_reconciled_account` emits no runtime, `absent`
# execution, the derived result and a derived proposal distinct from its source.
# Both carry a source proposal. Those are the two shapes an owner can return, and
# anything else is a context no owner wrote.
ABSENT_RUNTIME = "absent"
QUIESCENT_RUNTIME = "quiescent"
DIRECT = "direct"
RECONCILED = "reconciled"

# AND WHAT AN OWNER-DECLARED RECONCILIATION RESULT CARRIES. The same doctrine as
# `assignment_references` and `authorization_references`: what an OWNER says,
# read independently of the record being judged, so the validator COMPARES
# rather than checks for a value -- and so a foreign result id is caught by
# evidence rather than by a string-prefix rule this oracle would have invented.
RESULT_CONTEXT = ("derived_proposal_id", "source_proposal_id", "state")

# AND THE STATE A TERMINAL RECONCILIATION RESULT IS IN. Review
# 2026-09-13T01:18:16Z R6d: the reference carried `source_proposal_id` and
# `state` and the validator compared neither, so B's completion could name a
# source its own referenced result never used, and the FINAL reference -- read
# after the fixture reached `completed`, with the fixture itself asserting
# `imported` before export -- could be presented as `published` and still
# discharge a completion. A snapshot taken before the import finished is not
# proof that it did.
#
# THIS ORACLE ASKS FOR THE TERMINAL STATE AND NOTHING WEAKER. If a future
# artifact wants to retain historical, pre-completion references as well, it
# owes an observation time on them: that is a different fact, and until one
# exists a reference offered as final proof must be the terminal one.
IMPORTED_STATE = "imported"

CORRECTION_CONTEXT = ("outcome", "disposition", "verdict_id", "attachment_id",
                      "checkpoint_id", "subject_attempt_id",
                      # Review 2026-09-12T23:45:06Z: AND WHICH STAGE, EPISODE
                      # AND SUPERSEDED ATTEMPT THE JUDGMENT WAS ABOUT. The first
                      # form indexed claimed reviews by attempt id and tick
                      # alone, so relabelling the retained review attempt's
                      # records from job-a/review to job-b/review -- while the
                      # correction stayed on job-a -- still validated: the rule
                      # asserted the attempt belonged to THIS Job's review stage
                      # and never checked it.
                      "subject_stage_id", "subject_episode",
                      "superseded_attempt_id",
                      "routed_attempt_id", "reviewer_participant",
                      "reviewer_principal", "review_assignment_generation")

# AND THE ONLY JUDGMENT THAT ASKS FOR A CORRECTION. `DISPOSITIONS` is
# ("accepted", "changes-requested", "rejected"); an accepted review authorizes no
# correction and neither does a rejection, and the settlement's own outcome word
# for this routing is `correction`.
CORRECTING_DISPOSITION = "changes-requested"
CORRECTION_OUTCOME = "correction"

# AND WHAT AN OWNER-DERIVED ASSIGNMENT REFERENCE CARRIES. Review
# 2026-09-12T23:32:26Z R2: the session rule required a NONEMPTY participant and
# never compared it with the owner's actual assignment, so changing a real
# reviewer session's participant to `other.unassigned` validated clean. This is
# the same doctrine `authorization_references` already follows -- what an OWNER
# says, read independently of the row being judged, so the validator COMPARES
# rather than merely checks for a value.
ASSIGNMENT_CONTEXT = ("participant", "generation", "work_id", "authority_uuid",
                      "principal")

# AND WHAT A SESSION RECORD MUST CARRY. Owner155646 asked for nonempty sessions
# and independent roles, and the first thing actually opening one showed is that
# the identity alone proves nothing: two different attempts each opened execution
# epoch 1, so a reference spelled `posture:epoch` named BOTH of them. Every member
# below is on the session row `agent_sessions_of` answers.
SESSION_CONTEXT = ("posture", "session_epoch", "provider_session_id",
                   "work_id", "state", "generation", "pinned_policy")

# AND THE TWO POSTURES, which are not interchangeable. The pinned acceptance:
# "Consent has no assignment/workspace/output, execution has the exact
# assignment and pinned workspace role". The assignment is what puts a
# participant and a generation on the row, so an execution session with no
# participant has not proved it has an assignment, and a consent session WITH
# one contradicts the separation the two postures exist for.
POSTURES = ("consent", "execution")

# AND WHAT THE DECISION CONTEXT MUST CARRY. Each is on the receipt already.
AUTHORIZATION_CONTEXT = ("disposition", "candidate_digest", "target",
                         "effective_scope", "role", "policy_generation")

# AND WHICH ROLE EACH ACT'S DECISION MUST HAVE BEEN MADE IN. Review
# 2026-09-12T17:37:27Z: a review whose decision role was `integrate` validated
# clean, because nothing compared the role to the act. A decision made in another
# role is another decision.
EXPECTED_ROLE = {"verify": "verify", "review": "review",
                 "approve": "approve", "integrate": "integrate"}

# A CONFLATION OF MINE, CORRECTED. I wrote that "only the approval binds a policy
# generation", reading the RECEIPT's top-level `policy_generation` -- which is
# legitimately null for the other kinds. That is not the field the exporter reads.
# `decision.policy_generation` is required and positive on EVERY
# `AuthorizationDecision`, and a decision missing it validated clean because my
# context check only asked for truthiness on a field I had mislabelled.
#
# AND NO ALL-GENERATIONS-EQUAL RULE IS INVENTED: policy legitimately changes
# between decisions, so each is required to name a positive generation of its own
# and none is required to match another's.

# AND WHAT EACH ACT REQUIRES BEFORE IT, for the SAME attempt, EARLIER in the
# stream. Review 2026-09-12T16:18:34Z R2: the first draft required only
# increasing rank among whichever acts happened to be present, so a trace
# carrying `claim` then `complete` and NEITHER a reservation nor an offer
# validated clean. A prerequisite that is absent is unproved, and a truncated
# trace must say so rather than pass. A reserve-only trace is still legal:
# these are requirements OF an act, not obligations to reach one.
REQUIRED_BEFORE = {"reserve": (),
                   "offer": ("reserve",),
                   # OFFER ACCEPTANCE IS ITS OWN OBSERVABLE ACT, and I was
                   # wrong twice about this. `OFFER_STATES` contains `accepted`,
                   # the offer row carries its own `accepted_at`, and
                   # `offers._require_accepted` guards the claim -- so the
                   # approved "offer acceptance before claim" invariant is
                   # readable from the owner rather than absent from the build.
                   "accept": ("reserve", "offer"),
                   "claim": ("reserve", "offer", "accept"),
                   "start": ("reserve", "offer", "accept", "claim"),
                   # AND A COMPLETION REQUIRES THE START. C1: the independent
                   # probe deleted `start` from an otherwise legal chain and the
                   # first draft reported nothing, because completion listed only
                   # reserve/offer/claim.
                   "complete": ("reserve", "offer", "accept", "claim",
                                "start")}

# THE ENVIRONMENT CONDITION THIS WORK MUST REPORT RATHER THAN PAPER OVER.
# `v12/python/pyproject.toml` pins jsonschema 4.26.0; a run under any other
# resolution is exploratory evidence and says so in its own manifest.
PINNED_JSONSCHEMA = "4.26.0"

# R5, review 2026-09-12T16:18:34Z: THE SOURCES THAT ACTUALLY SUPPLY THE ASSERTED
# BEHAVIOUR. The first draft fingerprinted only the two new helper files, so an
# artifact said nothing about the scheduler, projection or fixtures whose answers
# it recorded -- and a later reader could not tell which product bytes produced
# it. These are repository-relative so the manifest is portable.
EXECUTED_SOURCES = (
    "v12/python/src/baton_v12/job_manager/scheduler.py",
    "v12/python/src/baton_v12/job_manager/projection.py",
    "v12/python/src/baton_v12/job_manager/manager.py",
    "v12/python/src/baton_v12/job_manager/submission.py",
    "v12/python/tests/job_manager/fixtures.py",
    "v12/python/tests/job_manager/test_scheduling.py",
    "v12/python/tests/tools/scheduler_trace.py",
    "v12/python/tests/tools/test_scheduler_trace.py",
    # C3, review 2026-09-12T16:35:09Z: THE COMPOSED OWNERS THAT SUPPLY THE
    # AUTHORIZED TRANSITIONS. The eight-entry manifest excluded even the reused
    # composed fixture, so an artifact recording its offers, claims and
    # completions bound none of the bytes that produced them.
    "v12/python/tools/stage_execution.py",
    "v12/python/tools/single_worker.py",
    "v12/python/tests/tools/test_stage_execution.py",
    "v12/python/src/baton_v12/worker_manager/attempts.py",
    "v12/python/src/baton_v12/worker_manager/review_cycles.py")

# AND WHERE THE REPOSITORY ROOT IS, derived from this file's own location rather
# than from a caller's guess.
REPOSITORY_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)),
                 os.pardir, os.pardir, os.pardir, os.pardir))

# R5: AND THE FIELDS A DRIVER DOES NOT ASK ANY OWNER ABOUT. A null here means
# "unobserved by this driver", which is NOT the same statement as "the owner
# reported none" -- the first draft documented them as the latter, which claimed
# an observation nobody made.
#
# THIS IS THE DEFAULT AND NOT A FACT ABOUT EVERY TRACE, which is a correction of
# my own. It was a module constant copied into every artifact, so the composed
# artifacts declared `runtime_id` unobserved WHILE CARRYING runtime ids read from
# the manager's own rows -- an artifact contradicting its own manifest, and
# nothing compared the two. A trace now declares what IT looked at, and
# `_observed_fields_agree` refuses any artifact whose records contradict its own
# declaration.
UNOBSERVED_FIELDS = ("runtime_id", "session_id")

# AND THE FIELDS A DECLARATION MAY SPEAK ABOUT, closed so a typo cannot quietly
# excuse a field nobody checks.
OBSERVABLE_FIELDS = ("runtime_id", "session_id", "principal", "participant",
                     "operation_id", "recorded_at")


def session_reference(row):
    """The §3.1 four-part reference for one session row, as ONE string.

    ALL FOUR COMPONENTS, because the first driver spelled a session
    `posture:epoch` and that is not an identity. Both composed attempts -- a
    producer's and a reviewer's -- opened execution epoch 1, so under the old
    spelling the two sessions of two different principals were one name, and a
    rule asking whether the reviewer's session differed from the producer's
    would have compared a string with itself. The attempt is part of the
    reference, and so is the provider id once the provider has been adopted.
    """
    return "/".join((row["runtime_attempt_id"], row["posture"],
                     str(row["session_epoch"]),
                     row["provider_session_id"] or "-"))


def _digest(value):
    """One canonical digest of a document, stable across runs."""
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"))
        .encode("utf-8")).hexdigest()


def _jsonschema_version():
    try:
        import importlib.metadata as metadata

        return metadata.version("jsonschema")
    except Exception:                      # pragma: no cover - absent is data
        return None


def environment_manifest(sources=(), unobserved=UNOBSERVED_FIELDS):
    """The source and environment manifest an artifact carries.

    THE DEPENDENCY GAP IS A MEMBER AND NOT A FOOTNOTE. The reviewer's baseline
    recorded that the available interpreter resolves jsonschema 4.19.2 against a
    4.26.0 pin; an artifact that did not carry that fact could be read later as
    dependency-conformant certification, which it is not.
    """
    resolved = _jsonschema_version()
    held = {"python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "jsonschema_resolved": resolved,
            "jsonschema_pinned": PINNED_JSONSCHEMA,
            "jsonschema_conformant": resolved == PINNED_JSONSCHEMA,
            "unobserved_fields": list(unobserved),
            "sources": {}}
    for path in tuple(sources) + EXECUTED_SOURCES:
        relative = path if not os.path.isabs(path) else os.path.relpath(
            path, REPOSITORY_ROOT)
        place = path if os.path.isabs(path) else os.path.join(
            REPOSITORY_ROOT, path)
        try:
            with open(place, "rb") as reading:
                held["sources"][relative] = \
                    "sha256:" + hashlib.sha256(reading.read()).hexdigest()
        except OSError:
            held["sources"][relative] = None
    return held


class Scenario:
    """One fixed, scripted scenario. It decides nothing and scripts no outcome.

    WHAT A SCENARIO MAY SAY: which Jobs exist, which stages they carry, which
    dependency edges hold, which worker slots the pool offers, how many logical
    ticks to run, and at which tick a declared durable reopen boundary falls.

    WHAT IT MAY NOT SAY: whether an act succeeded. Every outcome in a trace is
    an owner's own answer. A scenario that could script a successful claim would
    make the trace worthless as evidence, which is `PLAN.md`'s rule: "Fixed
    scripts alone are not evidence that those acts ran."
    """

    def __init__(self, *, name, jobs, workers, ticks=100, reopen_at=None,
                 order=None, completions=None, resolved_principals=None,
                 note=None):
        if ticks < 1 or ticks > 100:
            raise ValueError("a scenario runs between 1 and 100 logical ticks; "
                             "the approved cap is 100 per trace")
        self.name = name
        self.jobs = jobs
        self.workers = workers
        self.ticks = ticks
        self.reopen_at = reopen_at
        self.order = list(order or [])
        self.completions = dict(completions or {})
        self.resolved_principals = dict(resolved_principals or {})
        self.note = note

    def document(self):
        """The closed document this scenario IS, for its own digest.

        R5: THE EXECUTED INPUTS ARE PART OF IT. The first draft omitted the
        schedule order, the completions and the resolved principal mapping, so
        three different runs shared one scenario digest -- which made the digest
        useless for telling them apart. Everything that changes what the run
        does is inside the document that is digested.
        """
        return {"schema": SCENARIO_SCHEMA, "name": self.name,
                "jobs": self.jobs, "workers": self.workers,
                "ticks": self.ticks, "reopen_at": self.reopen_at,
                "order": self.order, "completions": self.completions,
                "resolved_principals": self.resolved_principals,
                "note": self.note}

    def digest(self):
        return _digest(self.document())


class Trace:
    """The records one run produced, and the gaps it deliberately recorded."""

    def __init__(self, scenario, unobserved=UNOBSERVED_FIELDS):
        self.scenario = scenario
        # WHAT THIS DRIVER DID NOT LOOK AT. The default is the unit pool's
        # answer; a driver that really asks an owner about a field narrows it,
        # and `validate` refuses an artifact whose records contradict it.
        self.unobserved = tuple(unobserved)
        self.records = []
        self.gaps = []
        # THE OWNER-DERIVED CONTEXT ONE SUBJECT IS GOVERNED BY. It is read from
        # the deployment independently of the receipts, so the validator can
        # COMPARE a decision's scope against it rather than merely check that
        # the decision carried some scope.
        self.references = {}
        # AND THE ASSIGNMENT AN OWNER FIXED TO ONE ATTEMPT, read the same way --
        # from `assignment_of`, independently of the session row being judged.
        self.assignments = {}
        # AND THE RECONCILIATION RESULT AN OWNER PUBLISHED, read from
        # `reconciliation.result_of` independently of the completion that names
        # it. Without this a reconciled completion's result id is a string this
        # oracle can only look at, and looking at a string is not evidence.
        self.results = {}

    def record(self, tick, act, *, outcome, stage_id=None, job_id=None,
               episode=None, attempt_id=None, worker_id=None, participant=None,
               principal=None, operation_id=None, runtime_id=None,
               session_id=None, evidence=None, cause=None, recorded_at=None,
               session=None, correction=None, completion=None,
               authorization=None):
        if act not in ACTS:
            raise ValueError(f"{act!r} is not one of {ACTS}")
        self.records.append({
            "tick": tick, "job_id": job_id, "stage_id": stage_id,
            "episode": episode, "attempt_id": attempt_id, "act": act,
            "outcome": outcome, "worker_id": worker_id,
            "participant": participant, "principal": principal,
            "operation_id": operation_id, "runtime_id": runtime_id,
            "session_id": session_id, "evidence": evidence, "cause": cause,
            "recorded_at": recorded_at, "session": session,
            "correction": correction, "completion": completion,
            "authorization": authorization})
        return self.records[-1]

    def reference(self, subject, **context):
        """Record what an owner says one subject is governed by."""
        self.references[subject] = dict(context)
        return self.references[subject]

    def assignment(self, attempt_id, **context):
        """Record the assignment an owner fixed to one attempt."""
        self.assignments[attempt_id] = dict(context)
        return self.assignments[attempt_id]

    def result(self, result_id, **context):
        """Record what an owner says one reconciliation result is."""
        self.results[result_id] = dict(context)
        return self.results[result_id]

    def gap(self, *, name, reason, observed, required):
        """One EXPECTED, UNRESOLVED contract mismatch, recorded as itself.

        Reviewer revalidation 2026-09-12T15:54:16Z retained three of these as
        open. A gap is not a failure of this run and it is not a pass either:
        it is the distinguishing observation from which the missing behaviour
        can later be scoped.
        """
        self.gaps.append({"name": name, "reason": reason,
                          "observed": observed, "required": required})
        return self.gaps[-1]

    def artifact(self, sources=()):
        """The versioned, exportable test artifact."""
        return {"schema": TRACE_SCHEMA,
                "scenario": self.scenario.document(),
                "scenario_digest": self.scenario.digest(),
                "environment": environment_manifest(sources,
                                                    self.unobserved),
                "records": [dict(one) for one in self.records],
                "authorization_references": {name: dict(one) for name, one
                                             in self.references.items()},
                "assignment_references": {name: dict(one) for name, one
                                          in self.assignments.items()},
                "result_references": {name: dict(one) for name, one
                                      in self.results.items()},
                "gaps": [dict(one) for one in self.gaps]}


# -- the independent validator ----------------------------------------------


def _violation(code, detail, record=None):
    return {"code": code, "detail": detail,
            "record": dict(record) if record is not None else None}


def validate(artifact):
    """Re-derive every invariant FROM THE ARTIFACT ALONE.

    It never reads a store, never calls the scheduler and never consults the
    driver that produced the records. Anything it cannot see in the artifact it
    reports as unprovable rather than assuming.

    Returns a list of violations; an empty list means the trace satisfies the
    invariants this oracle can check, which is NOT the same as certifying the
    scheduler contract.
    """
    violations = []
    if artifact.get("schema") != TRACE_SCHEMA:
        return [_violation("unknown-schema",
                           f"this validator reads {TRACE_SCHEMA} and the "
                           f"artifact says {artifact.get('schema')!r}")]
    # R5: THE DIGEST IS CHECKED RATHER THAN CARRIED. An artifact whose recorded
    # digest does not match the scenario beside it is one whose inputs and
    # records may describe different runs, and that is the first thing a reader
    # of somebody else's trace needs to know.
    scenario = artifact.get("scenario")
    if scenario is not None:
        recomputed = _digest(scenario)
        if artifact.get("scenario_digest") != recomputed:
            violations.append(_violation(
                "scenario-digest-mismatch",
                f"the artifact names {artifact.get('scenario_digest')!r} and "
                f"its scenario digests to {recomputed!r}"))
    records = artifact.get("records") or []
    for one in records:
        missing = [name for name in RECORD_MEMBERS if name not in one]
        if missing:
            violations.append(_violation(
                "incomplete-record", f"missing {sorted(missing)}", one))
    violations.extend(_unvalidated_acts(records))
    violations.extend(_authorized_subjects(
        records, artifact.get("authorization_references")))
    violations.extend(_monotonic_time(records))
    violations.extend(_instants_agree_with_order(records))
    violations.extend(_ordered_within_attempt(
        records, artifact.get("result_references")))
    violations.extend(_dependencies_before_successors(artifact, records))
    violations.extend(_no_overlapping_occupancy(records))
    violations.extend(_distinct_review_principal(records))
    violations.extend(_role_sessions(
        records, artifact.get("assignment_references")))
    violations.extend(_completed_integration_is_authorized(
        records, artifact.get("result_references")))
    violations.extend(_corrections_name_their_cause(
        records, artifact.get("assignment_references")))
    violations.extend(_observed_fields_agree(artifact, records))
    violations.extend(_exactly_once(records))
    violations.extend(_refusals_name_a_cause(records))
    return violations


def _authorized_subjects(records, references=None):
    """Every authorization act names its decider, and follows what it must.

    The review asked for actual review/test/import authorization bound to the
    exact subject. So each performed `review` or `integrate` must carry the
    Authority's own actor, principal and receipt identity, and an integration
    must follow a review OF THE SAME SUBJECT -- not merely of something.

    A missing member is `unattributed-authorization`; a missing predecessor is
    `unauthorized-subject`. Neither is inferred from an outcome word.
    """
    held = []
    references = references or {}
    positive = {}
    for one in records:
        act = one.get("act")
        if act not in SUBJECT_AUTHORIZATION or one.get("outcome") != "performed":
            continue
        missing = [name for name in AUTHORIZATION_MEMBERS if not one.get(name)]
        if missing:
            held.append(_violation(
                "unattributed-authorization",
                f"{act} names no {sorted(missing)}; a receipt that does not say "
                f"who decided is not an authorization", one))
        context = one.get("authorization") or {}
        absent = [name for name in AUTHORIZATION_CONTEXT if not context.get(name)]
        if absent:
            held.append(_violation(
                "unattributed-authorization",
                f"{act}'s decision names no {sorted(absent)}; scope, target, "
                f"candidate, role, generation and disposition are the decision, "
                f"not decoration", one))
        # THE DECISION'S OWN GENERATION IS A POSITIVE COUNT.
        generation = context.get("policy_generation")
        if generation is not None and (type(generation) is not int
                                       or type(generation) is bool
                                       or generation < 1):
            held.append(_violation(
                "unattributed-authorization",
                f"{act}'s decision names policy generation "
                f"{generation!r}; every AuthorizationDecision binds a positive "
                f"one", one))
        # AND IT WAS MADE IN THIS ACT'S OWN ROLE.
        wanted_role = EXPECTED_ROLE.get(act)
        if context.get("role") and context["role"] != wanted_role:
            held.append(_violation(
                "mismatched-authorization",
                f"{act} was decided in role {context['role']!r} and this act's "
                f"role is {wanted_role!r}; a decision made in another role is "
                f"another decision", one))
        # AND IN THE SCOPE THE SUBJECT IS ACTUALLY GOVERNED BY, compared against
        # an owner-derived reference rather than merely required to be non-empty.
        # Review 2026-09-12T17:37:27Z: a foreign `effective_scope` validated
        # clean because the check only asked whether the field had a value.
        # AND THE OWNER REFERENCE IS REQUIRED, NOT OPTIONAL. Review
        # 2026-09-12T17:42:54Z: deleting `authorization_references` disabled the
        # comparison entirely, so a missing map -- or a foreign scope WITH a
        # missing map -- validated clean. A comparison that silently becomes a
        # no-op when its reference is absent is not a check; an authorization
        # whose subject has no owner-declared scope is UNPROVED.
        #
        # A trace carrying no authorization acts needs no references at all:
        # this runs only for the acts that make a claim.
        expected = (references.get(one.get("evidence")) or {}).get(
            "effective_scope")
        if not expected:
            held.append(_violation(
                "unreferenced-authorization",
                f"{act} of {one.get('evidence')!r} has no owner-declared scope "
                f"to be compared against; without it this decision's scope is "
                f"unproved rather than acceptable", one))
        elif context.get("effective_scope") \
                and context["effective_scope"] != expected:
            held.append(_violation(
                "mismatched-authorization",
                f"{act} was decided in scope {context['effective_scope']!r} and "
                f"{one.get('evidence')!r} is governed by {expected!r}", one))
        # THE DISPOSITION DECIDES WHETHER THIS AUTHORIZES ANYTHING.
        wanted = POSITIVE_DISPOSITION.get(act)
        if context.get("disposition") and context["disposition"] != wanted:
            held.append(_violation(
                "nonaccepting-authorization",
                f"{act} of {one.get('evidence')!r} is "
                f"{context['disposition']!r} and a positive one is {wanted!r}; "
                f"it authorizes nothing", one))
            continue
        subject = one.get("evidence")
        if subject is not None:
            positive.setdefault((subject, act),
                                (one.get("tick"), one.get("recorded_at"),
                                 context))
    for one in records:
        act = one.get("act")
        if act not in SUBJECT_AUTHORIZATION or one.get("outcome") != "performed":
            continue
        subject, context = one.get("evidence"), one.get("authorization") or {}
        for required in SUBJECT_AUTHORIZATION[act]:
            standing = positive.get((subject, required))
            if standing is None:
                held.append(_violation(
                    "unauthorized-subject",
                    f"{act} of {subject!r} has no positive {required} of that "
                    f"same subject", one))
                continue
            prior_tick, prior_when, prior_context = standing
            # THE SAME CANDIDATE AND TARGET, not merely the same subject id.
            for name in ("candidate_digest", "target"):
                if context.get(name) and prior_context.get(name) \
                        and context[name] != prior_context[name]:
                    held.append(_violation(
                        "mismatched-authorization",
                        f"{act} names {name} {context[name]!r} and its "
                        f"{required} named {prior_context[name]!r}", one))
            # AND THE OWNERS' INSTANTS DECIDE THE ORDER WHEN BOTH EXIST, the
            # same rule the attempt chain follows. Review 2026-09-12T17:30:56Z:
            # a review at 00:00:02 after an integration at 00:00:01 validated
            # clean, because this compared only ticks and both were tick 1.
            when = one.get("recorded_at")
            if prior_when is not None and when is not None:
                if prior_when > when:
                    held.append(_violation(
                        "out-of-order",
                        f"{act} of {subject!r} was recorded at {when} and its "
                        f"{required} only at {prior_when}", one))
            elif prior_tick is not None and one.get("tick") is not None \
                    and prior_tick > one["tick"]:
                held.append(_violation(
                    "out-of-order",
                    f"{act} of {subject!r} is observed at tick {one['tick']} "
                    f"and its {required} only at tick {prior_tick}", one))
    return held


def _unvalidated_acts(records):
    """Any performed act this validator has no rule for is REPORTED.

    C1, review 2026-09-12T16:35:09Z. The alternative -- passing an act nobody
    checks -- is the exact silence this Work exists to remove, and it is worse
    than a missing feature because it reads as a validated one.
    """
    return [_violation(
        "unvalidated-act",
        f"{one.get('act')!r} is recorded as {one.get('outcome')!r} and this "
        f"validator implements no predecessor rule for it; it is unproved "
        f"rather than accepted", one)
        for one in records
        if one.get("act") not in VALIDATED_ACTS]


def _instants_agree_with_order(records):
    """Where the owners recorded instants, the record order must match them.

    D1, review 2026-09-12T16:51:07Z: an extractor that reorders an owner's own
    unequal timestamps is contradicting the owner, and the first validator could
    not see it because it read only the logical tick. A trace whose recorded
    instants run backwards against its own record order is refused -- so no
    extractor can quietly reorder receipts to suit this oracle.
    """
    held = []
    highest = None
    for one in records:
        when = one.get("recorded_at")
        if when is None:
            continue
        if highest is not None and when < highest:
            held.append(_violation(
                "instants-disagree-with-order",
                f"{one.get('act')} carries instant {when} after {highest}; the "
                f"owners' own order is not this trace's", one))
        else:
            highest = when
    return held


def _monotonic_time(records):
    """Logical time does not run backwards.

    Review 2026-09-12T16:18:34Z R2: a legal-looking reserve/offer/claim/complete
    chain whose ticks regressed 9 -> 2 -> 1 -> 0 validated clean, because nothing
    read the tick at all. A trace is a chronological record; a later record at an
    earlier logical tick is a contradiction about when things happened.
    """
    held = []
    highest = None
    for one in records:
        tick = one.get("tick")
        if tick is None:
            held.append(_violation("untimed-act",
                                   f"{one.get('act')} names no tick", one))
            continue
        if not isinstance(tick, int) or isinstance(tick, bool):
            held.append(_violation("untimed-act",
                                   f"{one.get('act')} names tick {tick!r}, "
                                   f"which is not a logical tick", one))
            continue
        if highest is not None and tick < highest:
            held.append(_violation(
                "regressing-time",
                f"{one.get('act')} is recorded at tick {tick} after tick "
                f"{highest}", one))
        else:
            highest = tick
    return held


def _ordered_within_attempt(records, results=None):
    """Every act's REQUIRED PRIOR EVIDENCE, for its own attempt and episode.

    This is the difference R2 asks for: not "no act regressed among those
    present" but "each act's prerequisites are present, earlier, and about the
    same attempt". An absent prerequisite leaves the act unproved, which is what
    a truncated trace must say instead of validating clean.
    """
    held = []
    performed = {}
    episodes = {}
    # EVERY PERFORMED ACT'S INDEX, GATHERED FIRST, so the two failures stay
    # distinguishable: a prerequisite that is ABSENT is `missing-prerequisite`,
    # and one that exists but comes LATER is `out-of-order`. Deciding both from
    # a single forward pass would collapse them into one message and lose the
    # difference between "you never did it" and "you did it too late".
    # KEYED ON THE LOGICAL TICK, NOT THE STREAM POSITION. D1, review
    # 2026-09-12T16:51:07Z: the observer records what each tick newly showed, and
    # several facts can already be true at the first observation -- a producer's
    # turn runs before the first sweep, so its start and its completion are both
    # visible at once. The owners give no order within a tick, so requiring one
    # would be the extractor inventing a sequence again, from the other side.
    # A prerequisite observed AT OR BEFORE an act's tick is satisfied; only a
    # prerequisite observed strictly LATER is out of order.
    imports = _imports(records)
    whole = {}
    for one in records:
        if one.get("act") in ATTEMPT_ORDER and one.get("outcome") == "performed":
            standing = whole.setdefault(
                (one.get("attempt_id"), one.get("episode")), {})
            if one.get("act") not in standing:
                standing[one.get("act")] = (one.get("tick"),
                                            one.get("recorded_at"))
    for index, one in enumerate(records):
        act = one.get("act")
        if act not in ATTEMPT_ORDER or one.get("outcome") != "performed":
            continue
        attempt = one.get("attempt_id")
        if attempt is None:
            held.append(_violation("unattributed-act",
                                   f"a performed {act} names no attempt", one))
            continue
        # THE EPISODE IS PART OF THE BINDING. Two episodes of one stage are two
        # attempts; an act whose episode disagrees with the reservation's is
        # about a different attempt of the same stage.
        standing = episodes.setdefault(attempt, one.get("episode"))
        if standing != one.get("episode"):
            held.append(_violation(
                "episode-mismatch",
                f"{act} names episode {one.get('episode')!r} and attempt "
                f"{attempt} was recorded under {standing!r}", one))
        seen = performed.setdefault(attempt, {})
        for required in REQUIRED_BEFORE.get(act, ()):
            # AN IMPORT THAT NEVER RAN A CONTAINER IS STILL A COMPLETION, and
            # its evidence is its RECEIPT CHAIN rather than a runtime.
            #
            # Measured, not assumed: when Job A moves the canonical target the
            # two Jobs share, `stage_execution.Integration._run` takes the
            # `reconciled` branch -- it publishes a derived candidate and waits
            # for independent judgments, and that branch completes WITHOUT an
            # integration runtime. Requiring a `start` there would be requiring
            # evidence of something that did not happen, which is a demand for
            # a fabrication.
            #
            # NARROW ON PURPOSE. Only `complete`, only its `start`, only an
            # `*/integration` stage, and only when this trace carries a
            # PERFORMED `integrate` for that Job -- which `_authorized_subjects`
            # in turn refuses unless the same subject's verification, review and
            # approval are present. Every other stage still owes its start, and
            # an unauthorized integration owes one too.
            if act == "complete" and required == "start" \
                    and _reconciled_without_runtime(one, records, imports,
                                                    results):
                continue
            anywhere = whole.get((attempt, one.get("episode")), {}).get(required)
            if anywhere is None:
                held.append(_violation(
                    "missing-prerequisite",
                    f"{act} for attempt {attempt} has no recorded {required}",
                    one))
                continue
            prior_tick, prior_when = anywhere
            when = one.get("recorded_at")
            # D1, review 2026-09-12T17:01:19Z: THE OWNERS' INSTANTS DECIDE WHEN
            # BOTH EXIST, whatever the observation tick says.
            #
            # The previous rule compared observation ticks alone, so a claim the
            # owner recorded at 00:00:01 and an offer it recorded at 00:00:02 --
            # both first seen in the same sweep -- were treated as concurrent and
            # the KNOWN contradiction was erased. Equal ticks mean this observer
            # could not separate them; they do not mean the owners could not.
            # Where both instants exist they are compared; where they do not, the
            # coarse tick is still used, because a coarse observation is better
            # than an invented order.
            if prior_when is not None and when is not None:
                if prior_when > when:
                    held.append(_violation(
                        "out-of-order",
                        f"{act} for attempt {attempt} was recorded by its owner "
                        f"at {when} and its {required} only at {prior_when}",
                        one))
            elif prior_tick is not None and one.get("tick") is not None \
                    and prior_tick > one["tick"]:
                held.append(_violation(
                    "out-of-order",
                    f"{act} for attempt {attempt} is observed at tick "
                    f"{one['tick']} and its {required} only at tick "
                    f"{prior_tick}", one))
        if act in seen:
            held.append(_violation(
                "duplicate-act",
                f"{act} was performed twice for attempt {attempt}", one))
        else:
            seen[act] = one.get("tick")
    return held


def _imports(records):
    """Every performed import authorization, keyed by the SUBJECT it names.

    Keyed by subject rather than by Job, which is review 2026-09-13T00:47:10Z
    R6a: the first form recorded `imported[job_id]` and checked membership, so
    swapping the Job and stage labels of two intact chains left both traces
    valid while each purported to authorize the other's import.
    """
    return {one.get("evidence"): one for one in records
            if one.get("act") == "integrate"
            and one.get("outcome") == "performed"}


def _completion_branch(one, records, results):
    """WHICH BRANCH this completion reports, and whether the trace agrees.

    R6c. Two shapes exist and an owner can return no third one. A DIRECT import
    ran a container: it names that runtime, reports it `quiescent`, carries no
    reconciliation result, and its proposal IS its source. A RECONCILED import
    ran none: it names no runtime, reports execution `absent`, carries the
    derived result, and its proposal differs from the source it was derived
    from. Both name a source proposal -- a completion that names none has not
    said what it imported from.

    AND A DIRECT COMPLETION'S RUNTIME IS COMPARED WITH ITS OWN ATTEMPT'S START,
    which is the mutation that validated clean: the completion said one runtime
    and the start of the very same attempt said another, and nothing looked.

    THE RESULT IS BOUND THROUGH AN OWNER, NOT A STRING. A foreign result id also
    validated clean, and the honest fix is not a prefix rule this oracle invents
    -- it is `result_references`, what `reconciliation.result_of` answered for
    that result, read independently of the completion that names it.
    """
    context = one.get("completion")
    if not context.get("source_proposal_id"):
        return None, ("names no source proposal; a completion that cannot say "
                      "what it imported from has not identified its import")
    reconciled = context.get("result_id") is not None
    if not reconciled:
        if context.get("runtime_id") is None \
                or context.get("execution_runtime") != QUIESCENT_RUNTIME:
            return None, (f"carries no reconciliation result, which is a "
                          f"direct import, and reports runtime "
                          f"{context.get('runtime_id')!r} execution "
                          f"{context.get('execution_runtime')!r}; a completed "
                          f"direct import names the runtime it ran on and "
                          f"reports it {QUIESCENT_RUNTIME!r}")
        if context.get("proposal_id") != context.get("source_proposal_id"):
            return None, (f"is a direct import whose proposal "
                          f"{context.get('proposal_id')!r} is not its own "
                          f"source {context.get('source_proposal_id')!r}")
        started = [other for other in records
                   if other.get("act") == "start"
                   and other.get("outcome") == "performed"
                   and other.get("attempt_id") == one.get("attempt_id")]
        if not started:
            return None, (f"names runtime {context.get('runtime_id')!r} and "
                          f"this trace records no start for its own attempt")
        disagreeing = [other.get("runtime_id") for other in started
                       if other.get("runtime_id") != context.get("runtime_id")]
        if disagreeing:
            return None, (f"names runtime {context.get('runtime_id')!r} and "
                          f"its own attempt's start names "
                          f"{sorted(set(str(one) for one in disagreeing))}")
        return DIRECT, None
    if context.get("runtime_id") is not None \
            or context.get("execution_runtime") != ABSENT_RUNTIME:
        return None, (f"carries a reconciliation result, which is a reconciled "
                      f"import, and reports runtime "
                      f"{context.get('runtime_id')!r} execution "
                      f"{context.get('execution_runtime')!r}; that branch runs "
                      f"no container and reports {ABSENT_RUNTIME!r}")
    if context.get("proposal_id") == context.get("source_proposal_id"):
        return None, (f"is a reconciled import whose derived proposal "
                      f"{context.get('proposal_id')!r} is its own source")
    reference = (results or {}).get(context.get("result_id"))
    if reference is None:
        return None, (f"names reconciliation result "
                      f"{context.get('result_id')!r} and no owner-declared "
                      f"result for it is in this artifact; a result nothing "
                      f"independently reports is a string, not evidence")
    if reference.get("derived_proposal_id") != context.get("proposal_id"):
        return None, (f"names result {context.get('result_id')!r}, whose owner "
                      f"reports derived proposal "
                      f"{reference.get('derived_proposal_id')!r}, and imports "
                      f"{context.get('proposal_id')!r}")
    # R6d. THE REST OF THE BINDING THIS ARTIFACT ALREADY CARRIED. Nonempty and
    # different from the derived proposal was all the source had to be, so a
    # completion could name a source its own referenced result never derived
    # from -- a second, unchecked account of which proposal was reconciled.
    if reference.get("source_proposal_id") != context.get("source_proposal_id"):
        return None, (f"names result {context.get('result_id')!r}, which its "
                      f"owner derived from "
                      f"{reference.get('source_proposal_id')!r}, and says it "
                      f"imported from "
                      f"{context.get('source_proposal_id')!r}")
    if reference.get("state") != IMPORTED_STATE:
        return None, (f"discharges a completed import with result "
                      f"{context.get('result_id')!r}, whose owner reports it "
                      f"{reference.get('state')!r}; a reference offered as "
                      f"final proof of an import is the one that says "
                      f"{IMPORTED_STATE!r}")
    return RECONCILED, None


def _bound_import(one, imports):
    """The import authorization THIS completion is bound to, or why not.

    The binding is the owner's own: the integrator's completion document names
    the proposal this stage imported and the integration receipt that
    authorized it, and both must be the ones the chain in this trace carries.
    """
    context = one.get("completion")
    if not isinstance(context, dict):
        return None, "carries no completion binding"
    missing = [name for name in COMPLETION_CONTEXT if name not in context]
    if missing:
        return None, f"carries no {sorted(missing)} in its completion binding"
    subject = context.get("proposal_id")
    if not subject:
        return None, "names no imported proposal"
    held = imports.get("proposal:" + subject)
    if held is None:
        return None, (f"names imported proposal {subject!r} and this trace "
                      f"carries no performed integration authorization of it")
    # AND A LABEL THAT CONTRADICTS THE BINDING IS ITSELF A DEFECT. R6a's
    # mutation swapped the Job and stage labels of two intact chains; the
    # subject binding above survives that -- correctly, since the labels are not
    # what binds -- but a chain recorded under another Job's name while
    # authorizing this one's import is a record disagreeing with itself.
    if held.get("job_id") is not None and one.get("job_id") is not None \
            and held.get("job_id") != one.get("job_id"):
        return None, (f"names imported proposal {subject!r}, whose "
                      f"authorization in this trace is recorded for Job "
                      f"{held.get('job_id')!r} and this completion is of "
                      f"{one.get('job_id')!r}")
    if held.get("operation_id") != context.get("integration_receipt_id"):
        return None, (f"names integration receipt "
                      f"{context.get('integration_receipt_id')!r} and the "
                      f"authorization of {subject!r} is receipt "
                      f"{held.get('operation_id')!r}")
    return held, None


def _dependencies_before_successors(artifact, records):
    """No successor is admitted before the stage it depends on completed."""
    held = []
    edges = []
    for job in (artifact.get("scenario") or {}).get("jobs") or []:
        for stage in job.get("stages") or []:
            for edge in stage.get("depends_on") or []:
                edges.append((f"{job['job_id']}/{stage['kind']}",
                              f"{edge['job_id']}/{edge['kind']}"))
    completed = {}
    for index, one in enumerate(records):
        if one.get("act") == "complete" and one.get("outcome") == "performed":
            completed.setdefault(one.get("stage_id"), index)
    for index, one in enumerate(records):
        if one.get("act") != "reserve" or one.get("outcome") != "performed":
            continue
        for successor, prerequisite in edges:
            if one.get("stage_id") != successor:
                continue
            when = completed.get(prerequisite)
            if when is None or when > index:
                held.append(_violation(
                    "successor-before-prerequisite",
                    f"{successor} was reserved before {prerequisite} "
                    f"completed", one))
    return held


def _no_overlapping_occupancy(records):
    """One worker AND one effective principal hold one live allocation at a time.

    Review 2026-09-12T16:18:34Z R3, two corrections. First, occupancy is also a
    PRINCIPAL fact: two reservations on different workers that resolve to one
    canonical principal are one separation identity occupied twice, and the first
    draft reported nothing because it keyed on the worker alone. Second, only the
    owner's own release frees capacity -- the first draft freed it on `complete`
    and on `reopen`, so a restart read as a release and a completed-but-unsettled
    allocation read as idle. Restart does not release custody.
    """
    held = []
    workers, principals = {}, {}
    # WHEN EACH ATTEMPT'S OWN RELEASE WAS FIRST OBSERVED. Gathered before the
    # forward pass, because a release and the reserve it made possible can be
    # first seen in the SAME tick -- one sweep completes an integration, the
    # allocator returns the worker and the next eligible stage takes it -- and
    # this observer cannot order two facts inside one tick.
    #
    # THIS IS NOT AN ACT RANK AND IT DOES NOT WEAKEN THE RULE. Two reservations
    # with NO release between them still overlap at any tick, which is what the
    # retained negatives assert; a restart and a completion still free nothing,
    # because `RELEASING_ACTS` is ('release',). What it says is narrower: where
    # the owner's own release of the standing holder is observed at or before
    # the tick of the next reservation, the allocator's own invariant forces the
    # order, and reporting an overlap would be this driver contradicting the
    # store it read the release from.
    # KEYED BY THE HOLDER IT NAMES, NOT BY THE ATTEMPT ALONE, and carrying the
    # owner's instant. Review 2026-09-13T00:24:01Z reproduced two false
    # negatives in the first form of this shortcut: a release naming the right
    # attempt but a FOREIGN worker and principal freed the standing holder
    # anyway, and a release whose owner instant was LATER than the next
    # reservation's was still treated as preceding it because only ticks were
    # compared. A release frees the capacity it actually names, and where both
    # sides carry the owners' instants those decide.
    freed = {}
    for one in records:
        if one.get("outcome") != "performed" \
                or one.get("act") not in RELEASING_ACTS:
            continue
        attempt = one.get("attempt_id")
        when = one.get("tick")
        if attempt is None or when is None:
            continue
        for what in ("worker_id", "principal"):
            key = one.get(what)
            if key is None:
                continue
            standing = freed.get((what, key, attempt))
            if standing is None or when < standing[0]:
                freed[(what, key, attempt)] = (when, one.get("recorded_at"))
    for one in records:
        if one.get("outcome") != "performed":
            continue
        act = one.get("act")
        attempt = one.get("attempt_id")
        if act == "reserve":
            for holder, what in ((workers, "worker_id"),
                                 (principals, "principal")):
                key = one.get(what)
                if key is None:
                    continue
                standing = holder.get(key)
                released = freed.get((what, key, standing))
                handed = (released is not None
                          and one.get("tick") is not None
                          and released[0] <= one.get("tick"))
                # AND THE OWNERS' INSTANTS OVERRIDE THE COARSE TICK, exactly as
                # they do for the attempt chain: equal ticks mean this observer
                # could not separate two facts, not that the owners could not.
                # A release the owner timestamped AFTER the reservation did not
                # precede it, whatever tick both were first seen at.
                if handed and released[1] is not None \
                        and one.get("recorded_at") is not None \
                        and released[1] > one.get("recorded_at"):
                    handed = False
                if standing is not None and standing != attempt \
                        and not handed:
                    held.append(_violation(
                        "overlapping-occupancy",
                        f"{what} {key} was reserved for {attempt} while still "
                        f"holding {standing}", one))
                holder[key] = attempt
        elif act in RELEASING_ACTS:
            for holder, what in ((workers, "worker_id"),
                                 (principals, "principal")):
                key = one.get(what)
                if key is not None and holder.get(key) == attempt:
                    holder.pop(key, None)
    return held


def _distinct_review_principal(records):
    """A review is not performed by the principal that produced the work."""
    held = []
    produced = {}
    for one in records:
        if one.get("outcome") != "performed" or one.get("act") != "reserve":
            continue
        stage_id = one.get("stage_id") or ""
        job_id = one.get("job_id")
        if stage_id.endswith("/implementation"):
            produced[job_id] = one.get("principal")
        elif stage_id.endswith("/review"):
            if one.get("principal") is None:
                held.append(_violation(
                    "unattributed-review",
                    f"{stage_id} names no principal", one))
            elif produced.get(job_id) == one.get("principal"):
                held.append(_violation(
                    "review-by-producer",
                    f"{stage_id} was reserved for principal "
                    f"{one.get('principal')!r}, which produced {job_id}", one))
    return held


def _role_sessions(records, assignments=None):
    """Every recorded agent session, and the separation two roles must keep.

    Owner155646 asked for nonempty sessions and INDEPENDENT ROLES. `PLAN.md`'s
    oracle list has said "distinct producer/reviewer principals and sessions"
    since the first slice; the principals half was implemented and the sessions
    half was not, because until this claim no composed path had opened one. It
    is implemented here from the artifact alone.

    THE SIX THINGS A RECORDED SESSION MUST SURVIVE:

      1. it carries its own context -- posture, epoch, provider id, Work and
         state -- because an identity is not evidence about itself;
      2. its reference names the attempt the record is about, so a session
         cannot be filed under somebody else's attempt;
      3. no two attempts share one session reference, which is the defect the
         old `posture:epoch` spelling actually had;
      4. an EXECUTION session names the participant its assignment fixed, and a
         CONSENT session names none -- the separation the postures exist for;
      5. a review-stage session is not held by the participant that produced
         that Job;
      6. the attempt was CLAIMED first. A session is opened against an
         activated attempt, and activation follows the claim; a session with no
         claim behind it is an agent talking about Work nobody was granted.
    """
    held = []
    assignments = assignments or {}
    producers = {}
    claimed = {}
    for one in records:
        if one.get("outcome") == "performed" and one.get("act") == "claim":
            key = one.get("attempt_id")
            if key is not None and key not in claimed:
                claimed[key] = one.get("tick")
    for one in records:
        stage_id = one.get("stage_id") or ""
        if one.get("outcome") == "performed" and stage_id.endswith(
                "/implementation") and one.get("participant"):
            producers.setdefault(one.get("job_id"), one.get("participant"))
    for one in records:
        reference = one.get("session_id")
        if not reference:
            continue
        # ITS OWN STAGE, read here. Corrected after measurement: this loop read
        # the `stage_id` the PREVIOUS loop left standing, so the producer's own
        # implementation session was judged against the last stage the gathering
        # pass happened to see and reported as a review by its own producer.
        stage_id = one.get("stage_id") or ""
        context = one.get("session")
        missing = [] if isinstance(context, dict) else list(SESSION_CONTEXT)
        if isinstance(context, dict):
            missing = [name for name in SESSION_CONTEXT if name not in context]
        if missing:
            held.append(_violation(
                "unattributed-session",
                f"session {reference} carries no {sorted(missing)}; an "
                f"identity is not evidence about itself", one))
            continue
        posture = context.get("posture")
        if posture not in POSTURES:
            held.append(_violation(
                "unattributed-session",
                f"session {reference} names posture {posture!r}, which is not "
                f"one of {POSTURES}", one))
            continue
        # ALL FOUR COMPONENTS, and R2 is why the fourth is here. The first form
        # compared three and never looked at the provider component, so changing
        # only the fourth part of a real retained reference to
        # `foreign-provider-id` validated clean -- the reference could name a
        # provider session the row was never bound to. `-` is the owner's
        # legitimate representation of an epoch no provider id has been adopted
        # for, and it is compared as such rather than excused.
        parts = reference.split("/")
        if len(parts) != 4 or parts[0] != one.get("attempt_id") \
                or parts[1] != posture \
                or parts[2] != str(context.get("session_epoch")) \
                or parts[3] != (context.get("provider_session_id") or "-"):
            held.append(_violation(
                "session-attempt-mismatch",
                f"session {reference} is recorded about attempt "
                f"{one.get('attempt_id')!r}, posture {posture!r}, epoch "
                f"{context.get('session_epoch')!r} and provider "
                f"{context.get('provider_session_id')!r}", one))
            continue
        # NO SEPARATE "TWO ATTEMPTS SHARED ONE REFERENCE" RULE, and the reason
        # is worth keeping. I wrote one, and its negative case could not be
        # built: the comparison just above requires the reference's first
        # component to BE the record's attempt, so two different attempts can
        # never carry one well-formed reference. The rule could not fail, and a
        # rule that cannot fail is not a rule -- the four-part comparison is
        # what actually catches the old `posture:epoch` spelling.
        assigned = one.get("participant") or context.get("generation")
        if posture == "execution" and not (one.get("participant")
                                           and context.get("generation")):
            held.append(_violation(
                "unattributed-session",
                f"execution session {reference} names participant "
                f"{one.get('participant')!r} and generation "
                f"{context.get('generation')!r}; an execution session has the "
                f"exact assignment, and the assignment is what names both",
                one))
        # AND IT IS COMPARED WITH THE OWNER'S OWN ASSIGNMENT, not merely
        # present. R2: changing a real reviewer session's participant to
        # `other.unassigned` validated clean, because the rule asked only for a
        # nonempty identity. `assignment_references` is what `assignment_of`
        # answered for that attempt, read independently of the session row.
        reference_context = assignments.get(one.get("attempt_id"))
        if posture == "execution" and reference_context is None:
            held.append(_violation(
                "unreferenced-session",
                f"execution session {reference} names an assignment and no "
                f"owner-declared assignment for attempt "
                f"{one.get('attempt_id')!r} is in this artifact; an assignment "
                f"nothing independently reports is unproved", one))
        elif reference_context is not None:
            disagreeing = []
            if context.get("work_id") != reference_context.get("work_id"):
                disagreeing.append(
                    f"work {context.get('work_id')!r} against "
                    f"{reference_context.get('work_id')!r}")
            if posture == "execution":
                if one.get("participant") != reference_context.get(
                        "participant"):
                    disagreeing.append(
                        f"participant {one.get('participant')!r} against "
                        f"{reference_context.get('participant')!r}")
                if context.get("generation") != reference_context.get(
                        "generation"):
                    disagreeing.append(
                        f"generation {context.get('generation')!r} against "
                        f"{reference_context.get('generation')!r}")
            if disagreeing:
                held.append(_violation(
                    "session-contradicts-its-assignment",
                    f"session {reference} names " + "; ".join(disagreeing),
                    one))
        if posture == "consent" and assigned:
            held.append(_violation(
                "consent-session-carries-an-assignment",
                f"consent session {reference} names participant "
                f"{one.get('participant')!r} and generation "
                f"{context.get('generation')!r}; consent has no assignment",
                one))
        if stage_id.endswith("/review") \
                and producers.get(one.get("job_id")) is not None \
                and producers[one.get("job_id")] == one.get("participant"):
            held.append(_violation(
                "review-session-by-producer",
                f"session {reference} reviews {one.get('job_id')} under "
                f"participant {one.get('participant')!r}, which produced it",
                one))
        when = claimed.get(one.get("attempt_id"))
        if when is None:
            held.append(_violation(
                "session-without-its-claim",
                f"session {reference} names attempt "
                f"{one.get('attempt_id')!r} and no performed claim for it is "
                f"in this trace; a session is opened against an activated "
                f"attempt and activation follows the claim", one))
        elif one.get("tick") is not None and when > one.get("tick"):
            held.append(_violation(
                "session-without-its-claim",
                f"session {reference} is recorded at tick {one.get('tick')} "
                f"and its attempt was claimed at tick {when}", one))
    return held


def _corrections_name_their_cause(records, assignments=None):
    """A correction is a SECOND episode with a RECORDED JUDGMENT behind it, and
    the judgment is bound to the Job, the stage, the episode and the reviewer it
    actually names.

    TWO ROUNDS OF REVIEW BUILT THIS RULE, and both found the same class of hole:
    a member that is REQUIRED TO BE PRESENT but compared with nothing.

    Round one (2026-09-12T23:32:26Z): it treated any performed record on a review
    stage as the judgment, so the retained real correction artifact with every
    review-stage act except `reserve` deleted validated clean. A reviewer holding
    a slot has judged nothing.

    Round two (2026-09-12T23:45:06Z): it then indexed claimed reviews by attempt
    id and tick alone, so relabelling the retained review attempt's records to
    `job-b/review` while the correction stayed on `job-a` validated -- and
    changing the correction's `reviewer_participant`, `reviewer_principal` or
    `review_assignment_generation` one at a time validated too, because those
    members had to exist and were never compared with the owner's own answer.

    WHAT A CORRECTION MUST SURVIVE NOW:

      1. it names a stage, an attempt and an episode after the first, and the
         owner evidence locator it was read from;
      2. it carries the whole judgment context -- an absent member is unproved;
      3. the settlement's outcome is a correction and the disposition is
         `changes-requested`: an ACCEPTED review authorizes no correction, and
         neither does a rejection;
      4. the attempt the settlement ROUTED to is the attempt this record is
         about, and the attempt it SUPERSEDED is the one this trace recorded for
         the previous episode of this same stage;
      5. the judgment is about THIS Job's review stage at the episode it names,
         and that exact attempt was CLAIMED in this trace at or before the
         correction. Reserved is not claimed; another Job's review is not this
         Job's judgment;
      6. the reviewer it names is the one an OWNER fixed to that attempt --
         participant, principal and generation compared against
         `assignment_references`, with the trace's own allocation principal for
         the reviewing attempt, and with the correction record's own identity.
         A reviewer nothing independently reports is `unreferenced-correction`.
    """
    held = []
    assignments = assignments or {}
    latest = {}
    attempts = {}
    reviewed = {}
    allocated = {}
    for one in records:
        if one.get("outcome") != "performed":
            continue
        stage_id = one.get("stage_id") or ""
        tick = one.get("tick")
        # THE REVIEW ATTEMPTS THIS TRACE SAW CLAIMED, keyed by the whole
        # identity a judgment names: attempt, stage and episode. Not "some
        # record on a review stage", and not "some attempt somewhere".
        if one.get("act") == "claim" and tick is not None:
            key = (one.get("attempt_id"), stage_id, one.get("episode"))
            if key not in reviewed or tick < reviewed[key]:
                reviewed[key] = tick
        # AND THE PRINCIPAL THE ALLOCATION FIXED, which is the trace's own
        # second witness to who was reviewing.
        if one.get("act") == "reserve" and one.get("principal"):
            allocated.setdefault(one.get("attempt_id"), one.get("principal"))
        key = (stage_id, one.get("episode"))
        if tick is not None and (key not in latest or tick < latest[key]):
            latest[key] = tick
            attempts[key] = one.get("attempt_id")
        elif key in latest and latest[key] == tick and key not in attempts:
            attempts[key] = one.get("attempt_id")
    for one in records:
        if one.get("act") != "correct" or one.get("outcome") != "performed":
            continue
        episode = one.get("episode")
        if not isinstance(episode, int) or isinstance(episode, bool) \
                or episode < 2 or not one.get("attempt_id") \
                or not one.get("evidence"):
            held.append(_violation(
                "uncaused-correction",
                f"a correction names episode {episode!r}, attempt "
                f"{one.get('attempt_id')!r} and evidence "
                f"{one.get('evidence')!r}; a correction is a later episode of "
                f"a recorded attempt, read from an owner", one))
            continue
        judgment = one.get("correction")
        missing = ([] if isinstance(judgment, dict)
                   else list(CORRECTION_CONTEXT))
        if isinstance(judgment, dict):
            missing = [name for name in CORRECTION_CONTEXT
                       if judgment.get(name) in (None, "")]
        if missing:
            held.append(_violation(
                "uncaused-correction",
                f"a correction of {one.get('stage_id')} carries no "
                f"{sorted(missing)}; the judgment that asked for it is the "
                f"whole content of a correction", one))
            continue
        tick = one.get("tick")
        previous = (one.get("stage_id"), episode - 1)
        superseded = latest.get(previous)
        if superseded is None or (tick is not None and superseded > tick):
            held.append(_violation(
                "unsuperseded-correction",
                f"a correction opens episode {episode} of "
                f"{one.get('stage_id')} and this trace records no earlier "
                f"episode {episode - 1} for it", one))
        elif attempts.get(previous) != judgment["superseded_attempt_id"]:
            held.append(_violation(
                "unsuperseded-correction",
                f"the judgment supersedes attempt "
                f"{judgment['superseded_attempt_id']!r} and this trace records "
                f"{attempts.get(previous)!r} for episode {episode - 1} of "
                f"{one.get('stage_id')}", one))
        if judgment["disposition"] != CORRECTING_DISPOSITION \
                or judgment["outcome"] != CORRECTION_OUTCOME:
            held.append(_violation(
                "noncorrecting-judgment",
                f"a correction cites a {judgment['disposition']!r} judgment "
                f"settled as {judgment['outcome']!r}; only a "
                f"{CORRECTING_DISPOSITION!r} review settled as "
                f"{CORRECTION_OUTCOME!r} asks for one", one))
        if judgment["routed_attempt_id"] != one.get("attempt_id"):
            held.append(_violation(
                "mismatched-correction",
                f"the judgment routed attempt "
                f"{judgment['routed_attempt_id']!r} and this correction is "
                f"about {one.get('attempt_id')!r}", one))
        # THE JUDGMENT'S OWN SUBJECT: this Job, its review stage, that episode.
        subject = judgment["subject_stage_id"]
        if subject != f"{one.get('job_id')}/review":
            held.append(_violation(
                "mismatched-correction",
                f"the judgment is about {subject!r} and this correction is of "
                f"Job {one.get('job_id')!r}; another Job's review is not this "
                f"Job's judgment", one))
        elif reviewed.get((judgment["subject_attempt_id"], subject,
                           judgment["subject_episode"])) is None \
                or (tick is not None
                    and reviewed[(judgment["subject_attempt_id"], subject,
                                  judgment["subject_episode"])] > tick):
            held.append(_violation(
                "unreviewed-correction",
                f"a correction of {one.get('job_id')} cites a judgment of "
                f"attempt {judgment['subject_attempt_id']!r} at episode "
                f"{judgment['subject_episode']!r} of {subject} and this trace "
                f"records no earlier claim of exactly that; a reservation is "
                f"not a verdict, and a restart is not a requested correction",
                one))
        # AND THE REVIEWER IT NAMES IS THE ONE AN OWNER FIXED.
        reference = assignments.get(judgment["subject_attempt_id"])
        if reference is None:
            held.append(_violation(
                "unreferenced-correction",
                f"a correction names reviewer "
                f"{judgment['reviewer_participant']!r} for attempt "
                f"{judgment['subject_attempt_id']!r} and no owner-declared "
                f"assignment for it is in this artifact; a reviewer nothing "
                f"independently reports is unproved", one))
        else:
            disagreeing = []
            for member, name in (("reviewer_participant", "participant"),
                                 ("reviewer_principal", "principal"),
                                 ("review_assignment_generation",
                                  "generation")):
                if judgment[member] != reference.get(name):
                    disagreeing.append(
                        f"{name} {judgment[member]!r} against "
                        f"{reference.get(name)!r}")
            if disagreeing:
                held.append(_violation(
                    "misattributed-correction",
                    f"the judgment names " + "; ".join(disagreeing)
                    + "; the owner's own assignment for "
                    f"{judgment['subject_attempt_id']!r} says otherwise", one))
        standing = allocated.get(judgment["subject_attempt_id"])
        if standing is not None \
                and standing != judgment["reviewer_principal"]:
            held.append(_violation(
                "misattributed-correction",
                f"the judgment names reviewer principal "
                f"{judgment['reviewer_principal']!r} and the allocation this "
                f"trace recorded for {judgment['subject_attempt_id']!r} was "
                f"held by {standing!r}", one))
        if one.get("participant") != judgment["reviewer_participant"] \
                or one.get("principal") != judgment["reviewer_principal"]:
            held.append(_violation(
                "misattributed-correction",
                f"this correction record is attributed to "
                f"{one.get('participant')!r}/{one.get('principal')!r} and the "
                f"judgment it carries names "
                f"{judgment['reviewer_participant']!r}/"
                f"{judgment['reviewer_principal']!r}", one))
    return held


def _reconciled_without_runtime(one, records, imports, results):
    """Whether the OWNER says this completion ran no integration container.

    R6b: the first exception asked only for an `*/integration` stage and any
    import authorization for the Job, so deleting a DIRECT import's `start`
    validated clean even though its completion names a live runtime. The
    exception belongs to the branch the owner reports, not to the stage name:
    a reconciled import names its derived RESULT, reports `absent` execution
    and holds no runtime -- and it must still be bound to its authorization,
    because an unproved completion earns nothing.
    """
    if (one.get("stage_id") or "").endswith("/integration") is False:
        return False
    if not isinstance(one.get("completion"), dict):
        return False
    if _bound_import(one, imports)[0] is None:
        return False
    return _completion_branch(one, records, results)[0] == RECONCILED


def _completed_integration_is_authorized(records, results=None):
    """A COMPLETED integration is bound to the import that authorized IT.

    Two rounds of review built this rule, and both found the same shape of hole.

    Round one (2026-09-13T00:09:15Z): the contention artifact reported Job A's
    integration `complete` with an empty `authorization_references` and validated
    clean. Receipt coverage in some other artifact does not establish this
    completion's subject.

    Round two (2026-09-13T00:47:10Z): the first fix recorded the import by JOB
    and checked membership, so swapping the Job and stage labels of two intact
    chains -- leaving their proposals, candidates, targets, receipts and owner
    references untouched -- still validated, with A's direct chain purporting to
    authorize B's derived import and the other way round. A label is not a
    subject.

    So the binding is the owner's own answer. `Integration.observe` names the
    proposal this stage imported and the integration receipt that authorized it;
    both must be the ones the chain in this trace actually carries, and
    `SUBJECT_AUTHORIZATION` then refuses that import unless the same subject's
    verification, review and approval are present too.

    A trace that never completes an integration needs none of this: these are
    requirements OF a completion, not obligations to reach one.
    """
    imports = _imports(records)
    held = []
    for one in records:
        if one.get("act") != "complete" or one.get("outcome") != "performed":
            continue
        if not (one.get("stage_id") or "").endswith("/integration"):
            continue
        bound, why = _bound_import(one, imports)
        if bound is not None:
            # AND THE BRANCH IT REPORTS MUST BE ONE AN OWNER COULD RETURN,
            # agreeing with this trace's own record of the attempt.
            branch, contradiction = _completion_branch(one, records, results)
            if branch is None:
                held.append(_violation(
                    "completion-contradicts-its-evidence",
                    f"{one.get('stage_id')} is recorded completed and its "
                    f"completion {contradiction}", one))
            continue
        held.append(_violation(
            "unbound-completion" if (one.get("completion") is None
                                     or why.startswith("carries no"))
            else "unauthorized-integration",
            f"{one.get('stage_id')} is recorded completed and {why}; a "
            f"completed import proves its own subject or it proves nothing",
            one))
    return held


def _observed_fields_agree(artifact, records):
    """An artifact does not declare unobserved a field its records carry.

    A correction of my own. `unobserved_fields` was a module constant copied
    into every manifest, so the composed artifacts stated that this driver never
    asked any owner about `runtime_id` while carrying runtime ids read from the
    Worker Manager's own rows. Nothing compared the declaration against the
    records, so the manifest could say anything.
    """
    environment = artifact.get("environment") or {}
    declared = environment.get("unobserved_fields")
    if declared is None:
        return [_violation("undeclared-observation",
                           "the artifact's environment manifest names no "
                           "unobserved_fields; a reader cannot tell an absent "
                           "value from an unasked question")]
    unknown = [name for name in declared if name not in OBSERVABLE_FIELDS]
    if unknown:
        return [_violation(
            "undeclared-observation",
            f"the manifest declares {sorted(unknown)} unobserved and this "
            f"validator knows no such field")]
    held = []
    for name in declared:
        for one in records:
            if one.get(name) is not None:
                held.append(_violation(
                    "unobserved-field-recorded",
                    f"the manifest declares {name!r} unobserved and this "
                    f"record carries {one.get(name)!r}", one))
                break
    return held


def _exactly_once(records):
    """No operation identity is performed twice, across reopen included."""
    held = []
    seen = {}
    for one in records:
        if one.get("outcome") != "performed":
            continue
        operation = one.get("operation_id")
        if operation is None:
            continue
        if operation in seen:
            held.append(_violation(
                "duplicate-operation",
                f"operation {operation} was performed at ticks "
                f"{seen[operation]} and {one.get('tick')}", one))
        else:
            seen[operation] = one.get("tick")
    return held


def _refusals_name_a_cause(records):
    """Every refusal carries its exact public cause.

    `PLAN.md`: "a refusal must have its exact public cause". A refused act with
    no cause is exactly the silence this Work exists to remove.
    """
    return [_violation("uncaused-refusal",
                       f"{one.get('act')} was {one.get('outcome')!r} and names "
                       f"no cause", one)
            for one in records
            if one.get("outcome") in ("refused", "deferred")
            and not one.get("cause")]
