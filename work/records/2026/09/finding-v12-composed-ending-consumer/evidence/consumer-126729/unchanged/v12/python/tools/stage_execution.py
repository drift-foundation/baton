"""The standalone stage deployment: one Job, three roles, one composition.

W103083, `work/records/2026/09/finding-v12-standalone-multi-job-pipeline/
findings/finding-standalone-stage-composition/findings/
finding-shared-stage-assembly/`.

WHAT WAS MISSING, AND IT WAS NOT A COMPONENT. Every operation this module
composes is accepted and independently reviewed: `single_worker` owns the OCI,
credential, source/workspace, exchange and ending composition for ONE worker;
`PooledManagerOperations` owns selecting a participant per allocation and
proving independence; `job_manager.review_driver` owns an implementation ending
and a review round; `integration.driver` owns publication and serialized
integration; `integration.retain_proposal` owns the proposal manifest those two
meet over. What did not exist is anything that CONFIGURES them together. This
is that, and it is deliberately nothing else.

WHY IT IS NOT A SECOND `single_worker`. That module is closed around one
implementation Work and hard-codes a v11 review pass. Copying it for reviewers
and integrators would put three deployment opinions over one security boundary
-- three places to keep a credential rule, a mount posture and an Authority
comparison true. So its worker-launch half is PARAMETERIZED and called three
times here, and the two halves it was split into are the seam: the half that
configures a control store and certifies a profile is called separately from
the half that needs an Authority, so this module decides where each one falls
relative to its own checks.

WHAT THIS MODULE REFUSES BEFORE ANY DURABLE ACT, because a configuration that
could not be true is worth catching while nothing has been written:

  the implementation and review stages naming different Work;
  a participant or principal shared where independence forbids it;
  a configured participant that resolves to another principal;
  a receipt actor that holds no grant for the receipt it is configured to
    write, in the target Work's OWN effective scope;
  a pool generation the next activation would not answer;
  and mutable deployment state placed inside the checkout.

AND IT CARRIES NO BEARER. Credential material reaches a worker through the
already-accepted provider registry; this document names a registry path and
slots, and a configuration carrying bytes is refused as one.
"""

import json
import os
import re

from baton_v12 import checkpoint_profiles
from baton_v12.authority import MAX_SAFE_INTEGER, Authority, Refusal
from baton_v12.contracts import ContractRefusal, digest
from baton_v12.integration import (IntegrationStore, admit_accepted,
                                   continue_accepted, integration_profile,
                                   publication_for_attempt, publish_candidate,
                                   retain_proposal, runtime)
from baton_v12.job_manager import ending, review_driver, scheduler
from baton_v12.job_manager.scheduler import PooledManagerOperations
from baton_v12.worker_manager import (assignment_of,
                                      attempt_runtime_of, claimed_offers_for,
                                      configured_workspace_group,
                                      discharge_quiescence_gate,
                                      gate_discharge_of, load_manifest,
                                      review_cycles)

from . import single_worker

__all__ = ["CONFIG_ENV", "CONFIG_SCHEMA", "ROLES", "StageExecution",
           "factory", "observation_from", "observing_factory",
           "operations_from"]

CONFIG_ENV = "BATON_V12_STAGE_EXECUTION_CONFIG"

# `/1`, and the version is in the name for `single_worker`'s reason: a closed
# document from another generation is refused by an equality test rather than
# read as a compatible subset of this one.
CONFIG_SCHEMA = "baton.v12.stage-execution-deployment/1"
MAX_CONFIG_BYTES = 4 * 1024 * 1024

# THE THREE ROLES ONE JOB NEEDS, and they are a closed set rather than free
# text. Each one selects which accepted driver a worker is composed under, and
# a fourth word would be a stage nobody has a driver for.
ROLES = ("implementation", "review", "integration")

# WHICH ROLES MAY NOT SHARE A PARTICIPANT OR A PRINCIPAL. Independence is the
# whole reason a review exists, and `attach_review` already refuses a reviewer
# that is the checkpoint's own writer -- but it refuses at the attachment,
# which is after this deployment started containers. Naming the rule here means
# a configuration that could never produce an independent review is refused
# before anything is opened.
INDEPENDENT = (("implementation", "review"),)

_MEMBERS = ("schema", "authority_store", "authority_uuid", "integration_store",
            "state_root", "pool_generation", "workers", "checkpoint_profile",
            "canonical_target_id", "integration_profile", "job_work_id",
            "review_work_id", "retention_policy_digest",
            "retention_disposition", "line_declared_base",
            "receipt_participants", "policy_generation")
_WORKER_MEMBERS = ("worker_id", "role", "deployment")
# THE THREE PARTICIPANTS WHOSE RECEIPTS AN ACCEPTED INTEGRATION NEEDS. They are
# configured because they are DEPLOYMENT identities rather than stage ones: a
# verification, a review and an approval receipt are written by whoever this
# deployment is authorized to write them as, and none of them is a worker.
#
# THE OTHER TWO ARE DERIVED AND DELIBERATELY NOT CONFIGURED. The integrator is
# the integration profile's own `integrator_participant`, which `admit_accepted`
# compares against the session it is handed -- so configuring it twice would be
# two places for one fact. And the PUBLISHER is the implementation worker's
# participant, because `Authority.publish` takes the producer's live assignment
# as its compare-and-swap operand and a session refuses to act on an assignment
# naming somebody else. A deployment that named a publisher would be naming one
# that can only be right by accident.
_RECEIPT_MEMBERS = ("verification", "review", "approval")
_PROFILE_MEMBERS = ("profile_kind", "profile_version",
                    "integrator_participant", "instructions_digest")
_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")

# The receipt sessions an accepted integration needs, and the one act each is
# for. Named here because `integration.driver` reaches every one of them AFTER
# a proposal is published, and a deployment missing one would discover it with
# somebody's candidate already on the Authority.
RECEIPT_SESSIONS = ("verification", "review", "approval", "integrator")

# AND THE ONE THAT IS NOT A RECEIPT. Publication happens while the producer
# assignment is still live, before the checkpoint fences it, so the session
# that performs it is reached EARLIER than any of the four above -- and a
# deployment missing it would discover that with a frozen result it can never
# publish. Its three capabilities are named because `retain_proposal` reads the
# canonical target and `publish_candidate` performs the act and reads back what
# the Authority recorded.
PUBLISHER_CAPABILITIES = ("publish", "proposal", "canonical_target")

# WHICH SESSION METHODS EACH ACTOR IS REACHED THROUGH. A SHAPE, not an
# authorization: `session.py` installs the whole transition table on the class,
# so every minted session answers every one of these names. Kept because an
# object that is not a session at all should be refused as that.
_SESSION_METHODS = {"verification": ("verify",), "review": ("review",),
                    "approval": ("approve",),
                    "integrator": ("integrate", "receipt"),
                    "publisher": PUBLISHER_CAPABILITIES}

# AND THE GRANT EACH RECEIPT ACTUALLY REQUIRES, in the Work's own scope.
# REVIEW 2026-09-07T14-12-42Z [P1]: this deployment proved neither, so a
# receipt participant holding no grant composed successfully and refused at
# `_write_receipt` -- after publication, which is the one place a deployment
# cannot recover from. The four words are the Authority's own capability
# vocabulary and are compared through its own reader.
#
# `publisher` IS ABSENT ON PURPOSE: publication is authorized by the producer's
# live assignment, not by a grant. See `_sessions`.
RECEIPT_CAPABILITIES = {"verification": "verify", "review": "review",
                        "approval": "approve", "integrator": "integrate"}

# What a credential must never be: bytes in a configuration document. The
# member names are the ones the contracts layer already refuses on a durable
# surface, mirrored here so a deployment document is refused at read time.
SECRET_MEMBERS = ("bearer", "token", "password", "authorization",
                  "access_token", "claim_token", "secret")

# WHERE THIS DEPLOYMENT KEEPS THE INTEGRATION DELIVERY, under the configured
# state root and therefore already proved outside the checkout. Named rather
# than configured because it is this composition's own layout: an operator who
# could point it somewhere else would be choosing a second mutable root for
# the one rule `_outside` already keeps.
INTEGRATION_HOME = "integration"

# The pool's separation class. `provider-diverse` is the honest word for three
# separately configured deployments with their own images, credentials and
# participants, and it is the strongest of the three the scheduler names.
SEPARATION_CLASS = "provider-diverse"

# How long the production Git runner waits for one bounded command. A profile
# command that never returns is a serving loop that never ticks again.
GIT_SECONDS = 300


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _document(value, what, members):
    if type(value) is not dict:
        _refuse(f"{what} is one object")
    if sorted(value) != sorted(members):
        _refuse(f"{what} carries exactly {', '.join(sorted(members))}")
    return value


def _text(value, what):
    if type(value) is not str or not value:
        _refuse(f"{what} is non-empty text")
    return value


def _path(value, what):
    _text(value, what)
    if not os.path.isabs(value) or os.path.normpath(value) != value:
        _refuse(f"{what} is one canonical absolute path")
    return value


def _digest(value, what):
    _text(value, what)
    if not _DIGEST.match(value):
        _refuse(f"{what} is a sha256 digest")
    return value


def _no_secret(value, where):
    """A deployment document carrying credential bytes is refused as one.

    WALKED RATHER THAN SPOT-CHECKED, because the member that matters is
    whichever one somebody added last. This is the same rule the contracts
    layer applies to a durable surface, applied to the document that CONFIGURES
    the surface -- a bearer never has to reach a manifest to have leaked.
    """
    if isinstance(value, dict):
        for name, below in value.items():
            if str(name).lower() in SECRET_MEMBERS:
                _refuse(f"the deployment configuration carries {name!r} at "
                        f"{where or 'its root'}; credential material reaches "
                        f"a worker through the provider registry and never "
                        f"through this document", category="policy",
                        code="denied")
            _no_secret(below, f"{where}.{name}" if where else str(name))
    elif isinstance(value, list):
        for index, below in enumerate(value):
            _no_secret(below, f"{where}[{index}]")
    return value


def _outside(place, checkout, what):
    """Mutable deployment state never lives inside the checkout.

    A run that wrote its stores, workspaces or launch material into the working
    tree would make an ordinary status or diff report the manager's own runtime
    as somebody's change -- and a cleanup that removed it would be removing
    repository content. The rule is stated once and applied to every mutable
    root this deployment names.
    """
    resolved = os.path.realpath(place)
    if resolved == checkout or resolved.startswith(checkout.rstrip("/") + "/"):
        _refuse(f"{what} at {place!r} is inside the checkout at {checkout!r}; "
                f"mutable deployment state belongs outside the working tree",
                category="policy", code="denied")
    return place


def _checkout():
    """This distribution's own working tree, resolved once."""
    return os.path.realpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "..", "..", ".."))


def held_configuration(document, *, checkout=None):
    """One closed deployment document, proved before anything is opened.

    EVERY REFUSAL HERE IS ONE A LATER OPERATION WOULD ALSO MAKE, and that is
    the point rather than a redundancy: the later ones happen after an
    Authority is open, a workspace group is configured and a container may be
    running, and their message describes the wrong moment.
    """
    # THE SECRET SWEEP RUNS FIRST, which is the contracts layer's own rule
    # applied here: a document carrying a bearer is refused AS THAT rather
    # than as whatever structural fault is also in it, because the two answers
    # send a caller to different places -- one to a schema, one to a leak.
    _no_secret(document, "")
    # OWNED AS A COPY, because this reading REPLACES members with the owned
    # forms of them -- each worker's deployment becomes the document
    # `single_worker._held` derived rather than the one that was written. A
    # validator that rewrote its caller's operand would leave that caller
    # holding something it never wrote, and the observation surface below
    # reads the original for exactly that reason.
    given = dict(_document(document, "a stage-execution configuration",
                           _MEMBERS))
    if given["schema"] != CONFIG_SCHEMA:
        _refuse(f"this deployment reads {CONFIG_SCHEMA} and this document is "
                f"{given['schema']!r}")
    _text(given["authority_uuid"], "the configured Authority")
    _text(given["job_work_id"], "the implementation Work")
    _text(given["review_work_id"], "the review Work")
    _text(given["canonical_target_id"], "the canonical target")
    _text(given["checkpoint_profile"], "the checkpoint profile name")
    _text(given["retention_disposition"], "the retention disposition")
    _text(given["line_declared_base"], "the line's declared base revision")
    _digest(given["retention_policy_digest"], "the retention policy digest")
    _document(given["receipt_participants"], "the receipt participants",
              _RECEIPT_MEMBERS)
    for name in _RECEIPT_MEMBERS:
        _text(given["receipt_participants"][name],
              f"the {name} receipt participant")
    for name in ("pool_generation", "policy_generation"):
        if type(given[name]) is not int or type(given[name]) is bool \
                or given[name] < 1:
            _refuse(f"a {name.replace('_', ' ')} counts from one")
        # AND IT IS BOUNDED ABOVE BY THE AUTHORITY'S OWN INTEROPERABLE RANGE.
        # REVIEW 2026-09-07T14-44-03Z [P2]: this checked only that the value
        # counted from one, so `policy_generation=9007199254740992` composed
        # successfully -- creating the integration store, configuring the
        # workspace group and activating a pool -- and the approval Session
        # refused the same operand later, with a frozen candidate already
        # published and nothing to do about it. The bound is the Authority's
        # published constant rather than a number spelled here, because a
        # second copy of a range is a second thing to keep equal.
        #
        # BOTH MEMBERS, because they are one rule read once: each is an
        # integer this deployment carries into a document somebody else
        # validates, and leaving one of the pair unbounded would be an
        # exemption with no reason behind it. This is the existing range, not
        # a new policy: no equality with `Authority.policy_generation()` is
        # required or implied, and the same review resolved that question
        # explicitly.
        if given[name] > MAX_SAFE_INTEGER:
            _refuse(f"a {name.replace('_', ' ')} is bounded by the "
                    f"interoperable integer range and {given[name]} is above "
                    f"{MAX_SAFE_INTEGER}", category="integrity", code="limit")

    here = os.path.realpath(checkout or _checkout())
    for name in ("authority_store", "integration_store", "state_root"):
        _path(given[name], f"the configured {name}")
    for name in ("integration_store", "state_root"):
        _outside(given[name], here, f"the configured {name}")

    # THE ONE WORK COMPARISON THIS DEPLOYMENT OWNS. A review stage pointed at
    # another Work would attach a reviewer to a checkpoint from a line this Job
    # never wrote, and the lifecycle would be perfectly happy about it: both
    # sides are valid, they are simply not the same Work.
    if given["job_work_id"] != given["review_work_id"]:
        _refuse(f"the implementation stage names Work "
                f"{given['job_work_id']!r} and the review stage names "
                f"{given['review_work_id']!r}; one Job's review is over its "
                f"own implementation", category="refused",
                code="precondition")

    _document(given["integration_profile"], "the integration profile",
              _PROFILE_MEMBERS)
    given["workers"] = _held_workers(given["workers"], here,
                                     given["authority_uuid"])
    return given


def _held_workers(workers, checkout, authority_uuid):
    """The pool, one worker per role, each with its own launch document."""
    if type(workers) is not list or not workers:
        _refuse("a stage-execution configuration names its workers as a list")
    held = []
    seen_roles, participants, principals = {}, {}, {}
    for one in workers:
        worker = _document(one, "a configured worker", _WORKER_MEMBERS)
        _text(worker["worker_id"], "a worker id")
        role = _text(worker["role"], "a worker role")
        if role not in ROLES:
            _refuse(f"{role!r} is not a stage role; this deployment composes "
                    f"{', '.join(ROLES)}")
        if role in seen_roles:
            _refuse(f"two workers are configured for the {role} stage; each "
                    f"stage is served by exactly one")
        # THE AUTHORITY COMPARISON COMES FIRST, before the launch validator,
        # so a worker configured for another Authority is refused as THAT.
        # `_held` would also refuse it, through whichever of its own rules the
        # mismatch happens to break first -- and a message about a bootstrap
        # manifest sends a reader to the wrong document.
        named = worker["deployment"]
        if type(named) is dict \
                and named.get("authority_uuid") != authority_uuid:
            _refuse(f"the {role} worker names Authority "
                    f"{named.get('authority_uuid')!r} and this deployment is "
                    f"configured for {authority_uuid!r}", category="refused",
                    code="capability")
        # THE LAUNCH HALF IS `single_worker`'S OWN DOCUMENT, held by its own
        # validator. A second copy of those rules here is a second place for
        # them to drift from the composition that actually uses them.
        deployment = single_worker._held(named, roles=ROLES)
        # THE WORKER'S OWN ROLE AND THE STAGE IT IS CONFIGURED FOR ARE ONE
        # FACT. `_SingleWorker` holds every stage it is offered to its
        # configured `launch_role`, so a worker composed under this
        # deployment's `review` role while its own document says
        # `implementation` would refuse every review stage it was ever
        # allocated -- at the offer, one tick at a time, forever.
        if deployment["launch_role"] != role:
            _refuse(f"the {role} worker's own deployment launches the "
                    f"{deployment['launch_role']!r} role; a stage is served "
                    f"by a worker configured for it", category="refused",
                    code="precondition")
        for name in ("workspace_storage", "launch_home", "credential_home"):
            _outside(deployment[name], checkout,
                     f"the {role} worker's {name}")
        seen_roles[role] = worker["worker_id"]
        participants.setdefault(deployment["participant"], []).append(role)
        principals.setdefault(deployment["principal"], []).append(role)
        held.append({"worker_id": worker["worker_id"], "role": role,
                     "deployment": deployment})
    missing = [role for role in ROLES if role not in seen_roles]
    if missing:
        _refuse(f"this deployment serves {', '.join(ROLES)} and names no "
                f"worker for {', '.join(missing)}")
    _independent(participants, "participant")
    _independent(principals, "principal")
    return held


def _independent(holder, what):
    """No identity may serve two roles independence forbids sharing."""
    for value, roles in holder.items():
        for left, right in INDEPENDENT:
            if left in roles and right in roles:
                _refuse(f"{value!r} is configured as the {what} of both the "
                        f"{left} and {right} stages; an independent review is "
                        f"not one the implementer performs", category="policy",
                        code="denied")


def _sessions(sessions, authority, scope):
    """Every receipt session, proved to be AUTHORIZED before publication.

    `integration.driver` reaches all four AFTER a proposal is on the Authority.
    A deployment that discovered a missing one there would have published
    somebody's candidate and then been unable to accept it.

    REVIEW 2026-09-07T14-12-42Z [P1]: THIS ASKED THE WRONG QUESTION. It checked
    that each session object had a callable method of the right name -- and
    every minted session has every one of them, because `session.py` installs
    the whole table on the class. So a deployment naming a receipt participant
    that holds no grant at all passed this gate, and `_write_receipt` refused
    it later with a frozen candidate already published and unacceptable.
    Presence of a method is the object's SHAPE; whether that actor may write
    the receipt is the Authority's DECISION, and only the Authority has it.

    So both are asked, and they are separate sentences. The shape check stays
    because a fixture or a future mint that answered a different object should
    be refused as that rather than through an attribute error three steps on;
    it is deliberately no longer worded as a capability. The authorization is
    `holds_capability` in the SCOPE THE RECEIPT WILL BE WRITTEN IN, which is
    the target Work's own -- see `_work_scope`.

    THE PUBLISHER IS DELIBERATELY NOT AUTHORIZED HERE, and that is not an
    omission. `Authority.publish` takes the producer's LIVE ASSIGNMENT as its
    compare-and-swap operand rather than a capability grant, so there is no
    grant to prove and inventing one to check would be asserting a rule the
    authority does not keep. Its identity is still proved: it is derived from
    the implementation worker, and `_minted` refuses a malformed one.
    """
    if type(sessions) is not dict:
        _refuse("the accepted-integration sessions are one object")
    for name in RECEIPT_SESSIONS + ("publisher",):
        session = sessions.get(name)
        if session is None:
            _refuse(f"this deployment has no {name} session; publication and "
                    f"the receipts that accept it are reached with somebody's "
                    f"candidate already frozen", category="refused",
                    code="capability")
        for verb in _SESSION_METHODS[name]:
            if not callable(getattr(session, verb, None)):
                _refuse(f"the {name} session has no {verb} method; this is "
                        f"not the runtime face this deployment mints",
                        category="refused", code="capability")
        who = getattr(session, "participant", None)
        if who is None:
            _refuse(f"the {name} session names no participant",
                    category="refused", code="capability")
        capability = RECEIPT_CAPABILITIES.get(name)
        if capability is not None \
                and not authority.holds_capability(who, capability,
                                                   scope=scope):
            _refuse(f"{who!r} writes this deployment's {name} receipt and "
                    f"holds no {capability} capability in {scope}; a receipt "
                    f"is written by the configured actor and the actor is "
                    f"authorized here rather than with somebody's candidate "
                    f"already published", category="policy", code="denied")
    return sessions


def _minted(authority, given, scope):
    """The five actor sessions, minted from the ONE Authority this deployment
    opened and validated before a single stage is served.

    REVIEW 2026-09-07T13-29-13Z [P1]: the public factory called the composer
    with no sessions at all, so `_sessions` was skipped, no `Publication` was
    created, and the serving object had no path to the receipts an accepted
    integration needs. Nothing was missing except a way to GET them -- so this
    is that, and it is a mint rather than a new operand because a deployment
    document carrying session material would be carrying capability bytes,
    which the secret sweep exists to refuse.

    THREE ARE CONFIGURED AND TWO ARE DERIVED, and `_RECEIPT_MEMBERS` records
    why each is which.

    REVIEW 2026-09-07T14-12-42Z [P1]: the mint's own refusal escaped this
    boundary raw. `_mint_session` checks participant grammar and raises the
    Authority's `Refusal`, so a deployment naming `not-an-address` received an
    exception from a package it never asked about -- and the serving loop,
    which handles this module's `ContractRefusal`, did not recognise it as a
    configuration fault at all.
    """
    participants = dict(given["receipt_participants"])
    participants["integrator"] = \
        given["integration_profile"]["integrator_participant"]
    participants["publisher"] = {one["role"]: one for one in given["workers"]
                                 }["implementation"]["deployment"]["participant"]
    minted = {}
    for name, who in sorted(participants.items()):
        minted[name] = _authority_read(
            f"this deployment's {name} actor {who!r} is not one this "
            f"Authority mints a session for",
            lambda who=who: authority.session(who))
    return _sessions(minted, authority, scope)


def _authority_read(what, read):
    """One Authority read, answered in THIS boundary's vocabulary.

    REVIEW 2026-09-07T14-12-42Z [P1]: a raw `Refusal` escaped the configuration
    boundary. Every other fault a composition can have is a `ContractRefusal`
    carrying a category and a code, which is what the serving loop and this
    module's own callers branch on; one that arrives as another package's
    exception type is a configuration fault nobody can classify.

    The original message is kept, because the Authority's own words are the
    exact reason and this layer has nothing better to say about it.
    """
    try:
        return read()
    except Refusal as refusal:
        _refuse(f"{what}: {refusal}", category="refused", code="capability")


def _work_scope(authority, work_id):
    """The effective scope this Job's receipts will actually be authorized in.

    NOT THE DEPLOYMENT'S, and the difference is the whole point.
    `_write_receipt` derives the scope from the Work the proposal belongs to
    precisely so a grant cannot widen on the way to a receipt -- so a
    configuration proved against `scope:deployment` would accept an actor whose
    grant does not reach this Work, and refuse an actor granted exactly here.
    Read from the Work this deployment is configured for, once, before
    anything durable happens.
    """
    projected = _authority_read(
        f"the configured Work {work_id!r} is not one this Authority holds",
        lambda: authority.project_work(work_id))
    if projected is None:
        _refuse(f"the configured Work {work_id!r} is absent from this "
                f"Authority; a deployment's receipts are authorized in that "
                f"Work's own effective scope and there is none to read",
                category="refused", code="precondition")
    return projected["scope"]

class Publication:
    """W103874's producer and W103077's publication, in the order that works.

    THE SEAM `review_driver.end_implementation` CALLS, and it is two accepted
    operations rather than one act this module invents. `retain_proposal`
    composes the manifest from the frozen result and the worker's own claim and
    answers its retained digest; `publish_candidate` takes that digest as a
    SELECTOR and re-reads every publication member out of the retained document
    before calling the Authority. Neither is re-implemented here and no member
    of either is supplied from this deployment's configuration -- if it were,
    the deployment would be asserting something the frozen result is supposed
    to prove.

    IT RUNS WHILE THE PRODUCER IS STILL LIVE. That ordering belongs to the
    ending, which calls this before it fences the writer; this object only has
    to not get in the way of it.
    """

    def __init__(self, control, publisher):
        self.control = control
        self.publisher = publisher
        self.published = []

    def publish(self, *, attempt_id, result_id, manifest_digest, artifacts,
                proposal):
        retained = retain_proposal(self.control, self.publisher,
                                   attempt_id=attempt_id)
        answer = publish_candidate(self.control, self.publisher,
                                   attempt_id=attempt_id,
                                   proposal_manifest_digest=retained)
        self.published.append({"attempt_id": attempt_id,
                               "result_id": result_id,
                               "manifest_digest": manifest_digest,
                               "artifacts": list(artifacts),
                               "proposal_manifest_digest": retained})
        return answer

    def published_of(self, *, attempt_id):
        """THE REPLAY HALF `review_driver.PUBLICATION_HISTORY` NAMES.

        W119114, consuming W120763's record and W121793's reader. A resumed
        implementation ending may not publish again -- `publish_candidate`
        needs the live producer assignment its own checkpoint already fenced --
        so it reads what publication COMMITTED instead.

        `publication_for_attempt` and nothing else. It takes no publisher, so
        this cannot reach the Authority; it needs no remembered selector, so a
        process that published nothing answers exactly what the publishing one
        would; and `self.published` above is deliberately not consulted, because
        an in-memory list says nothing about a process that has since died.
        """
        return publication_for_attempt(self.control, attempt_id=attempt_id)


# -- the three stage compositions --------------------------------------------


def _no_verdict(control, attempt_id):
    """The reviewer's own decision, and this build has no channel for it.

    REPORTED RATHER THAN INVENTED, which is the rule this leaf has already
    applied once: the missing retained proposal manifest became W103874 rather
    than a document this deployment composed. This is the same shape one layer
    over. `end_review` takes the manager's `disposition` -- what the review
    ATTEMPT ended as -- and the reviewer's `verdict` about the checkpoint as
    two separate facts, and it is right to: a crashed reviewer must not become
    a rejection. But nothing carries the second one out of the container.

    WHAT WAS LOOKED AT AND DOES NOT ANSWER IT. The exchange terminal's ten
    members are the manager's own vocabulary (`ending`, `disposition`,
    `fault_code`, `manifest_digest`) and none is the reviewer's. The frozen
    review result WOULD carry it -- a namespaced worker claim in
    `result_metadata` is exactly how the proposal claim travels -- but the
    freeze that retains it happens INSIDE `end_review`, three steps after the
    verdict operand is needed, and a deployment that froze first to read it
    would be performing the driver's own ordered step out of order.

    So a deployment either supplies the verdict from outside or refuses, and
    refusing is what this does. The composed lifecycle proof supplies one
    explicitly, which is a fixture standing in for the missing capability and
    is named as one rather than being read as evidence that a reviewer decided
    anything.
    """
    _refuse(f"attempt {attempt_id!r} is a completed review and nothing in "
            f"this build carries the reviewer's verdict out of its container: "
            f"the exchange terminal has no member for it and the frozen review "
            f"result that could is retained inside the ending that needs it. "
            f"A deployment supplies one explicitly or this stage stops here",
            category="refused", code="capability")


class StageComposition:
    """One role's MOUNT and ENDING, over the accepted stage drivers.

    W103083 review [P1]: three `single_worker` operations wrapped in
    `PooledManagerOperations` is not a composition of the stage drivers -- the
    real `launch` and `conclude` forward to the bootstrap worker's own
    callbacks, which refuse every kind but `implementation` and end an
    implementation through the v11 pass. Driver-facing attributes hanging off
    the serving object are reached by nothing.

    THIS IS WHAT THE SERVING PATH ACTUALLY REACHES. `single_worker` calls
    `mount` where it used to compose its own roots and boundary, and `end`
    where it used to run its own ordered ending; everything between the two --
    the offer, the claim, the attempt, the activation, the input root, the
    manifest, the launch document, the credential delivery, the pre-start
    re-proof, the start and the command -- is the accepted composition,
    unchanged and called once.

    AND IT DECIDES NOTHING. `prepare_implementation`, `prepare_review`,
    `end_implementation`, `end_review` and `open_correction` are the accepted
    driver's; the line is the accepted provider's; the publication is the two
    accepted integration operations. What this adds is which of them a role
    reaches and where its operands come from.
    """

    def __init__(self, deployment, *, role, worker_id):
        self.deployment = deployment
        self.role = role
        self.worker_id = worker_id
        # WHAT THE MOUNT ANSWERED, FOR THE ENDING IN THE SAME CALL. It is a
        # cache of a REPLAY and never a memory the composition depends on:
        # `_SingleWorker.ending` calls `mount` before it reaches `end`, so a
        # restarted manager repopulates this from the durable grant on the
        # tick that ends the attempt.
        self._prepared = {}

    # -- before a runtime starts ---------------------------------------------

    def mount(self, worker, stage, roots):
        """The two roots this role's container is started over.

        THE ACCEPTED BOUNDARY COMPOSES BOTH, and neither is this module's
        idea of a path. An implementation attempt mounts the persistent line
        writable, which is `writer_boundary` behind the grant `grant_writer`
        made; a review attempt mounts the frozen checkpoint read-only beside
        its own writable output, which is `review_boundary` behind the
        attachment. `roots` is the ordinary allocated pair both of them adopt.
        """
        del roots
        attempt_id = stage["attempt_id"]
        held = self._prepared.get(attempt_id) or self._prepare(attempt_id)
        if held["boundary"] is None:
            # W122060: AND THAT IS A REFUSAL RATHER THAN A NULL HANDED ON.
            # A recovered ending whose writer is already revoked has no mount
            # -- a boundary is what a container is STARTED over, and there is
            # no container. The caller subscripts what this returns, so
            # answering `None` turned a knowable condition into a `TypeError`
            # inside somebody else's root composition.
            _refuse(f"attempt {attempt_id!r}'s {self.role} record is "
                    f"historical and mounts nothing; an ending after the "
                    f"custody it earned is resumed from committed evidence "
                    f"rather than started over a boundary",
                    category="refused", code="precondition")
        return held["boundary"]

    def _prepare(self, attempt_id):
        """Grant this role's boundary, or recover the one already granted.

        W119114 FINDING, 2026-09-08: `mount` called this UNCONDITIONALLY, and
        `_SingleWorker.ending` calls `mount` before it reaches `end` -- so a
        second `conclude` for the same attempt re-ran `grant_writer`, which
        refuses once the checkpoint has frozen and the line has left `writing`:

            operation 'review-line.grant-writer:writer-...' is already recorded
            with a different kind or signature

        That is reachable whenever any step after the freeze defers, because
        the manager keeps the stage `answering` until its cleanup axis is
        terminal and asks `conclude` again every tick. `end_implementation`'s
        own contract says a process death between any two steps re-enters and
        finishes, and this was the one place that could not.

        THE RECOVERY READS THE RECORD BACK RATHER THAN RE-GRANTING ONE, which
        is what the FINDING said the right fix would do.

        W122060, correcting the first attempt at it. That branch asked whether
        the RUNTIME was destroyed and then read the LINE'S CURRENT CHECKPOINT
        to find the writer, and both were wrong. The runtime test excluded the
        window this exists for -- a freeze that has happened with the cleanup
        still deferred, where the grant can no longer replay and the runtime is
        still there -- and the line pointer is moved by every later round, so
        the recovery reached a new preparation exactly when the history it was
        looking for had been overtaken. W124331's accepted
        `writer_for_attempt`/`review_for_attempt` answer from the ATTEMPT and
        its generation, which do not move, and prove the row against the
        committed act that wrote it.
        """
        deployment = self.deployment
        control = deployment.control
        generation = deployment.generation_of(attempt_id)
        recovered = self._recovered(attempt_id, generation)
        if recovered is not None:
            self._prepared[attempt_id] = recovered
            return recovered
        line = deployment.line()
        if self.role == "implementation":
            # THE BASED CHECKPOINT IS THE LINE'S CURRENT ONE, WHATEVER IT IS,
            # and that is what makes a correction round the SAME line. On the
            # first round the line is `idle` and holds none, and the provider
            # refuses a first writer that names one; on every later round it
            # holds the rejected checkpoint, and the provider refuses a
            # correction writer that names any other. The deployment therefore
            # states the line's own fact rather than deciding which round this
            # is -- and states it identically on the launch tick and the
            # ending tick, which is what makes the grant replay.
            prepared = review_driver.prepare_implementation(
                control, line_id=line["line_id"], attempt_id=attempt_id,
                generation=generation, worker_id=self.worker_id,
                profile=deployment.profile,
                based_checkpoint_id=line["current_checkpoint_id"])
        else:
            prepared = review_driver.prepare_review(
                control, checkpoint_id=line["current_checkpoint_id"],
                attempt_id=attempt_id, generation=generation,
                reviewer_worker_id=self.worker_id, profile=deployment.profile)
        held = dict(prepared, generation=generation)
        self._prepared[attempt_id] = held
        return held

    def _recovered(self, attempt_id, generation):
        """This attempt's already-granted record, or absence before there is
        one.

        ABSENCE IS THE ORDINARY ANSWER ONCE, on the launch tick that has no
        record yet. Every tick after it recovers, so the mutable operands the
        first preparation is composed from -- the line's current checkpoint --
        are read exactly once for one attempt, and a second `conclude` cannot
        derive different ones.

        THE BOUNDARY IS COMPOSED ONLY WHILE THE RECORD IS LIVE. `state` is the
        row's own, and the accepted composers refuse anything else in as many
        words: "only the active writer generation mounts the line writable".
        A revoked writer or an ended attachment is history, and history is
        mounted by nobody -- so this answers the selectors with no boundary and
        `mount` refuses rather than passing a null along.
        """
        control = self.deployment.control
        if self.role == "implementation":
            writer = review_cycles.writer_for_attempt(
                control, attempt_id=attempt_id, generation=generation)
            if writer is None:
                return None
            boundary = None
            if writer["state"] == "active":
                boundary = review_cycles.writer_boundary(
                    control, writer_id=writer["writer_id"],
                    generation=generation)
            return {"writer_id": writer["writer_id"],
                    "line_id": writer["line_id"], "generation": generation,
                    "based_checkpoint_id": writer["based_checkpoint_id"],
                    "boundary": boundary}
        attachment = review_cycles.review_for_attempt(
            control, attempt_id=attempt_id, generation=generation)
        if attachment is None:
            return None
        boundary = None
        if attachment["state"] == "active":
            boundary = review_cycles.review_boundary(
                control, attachment_id=attachment["attachment_id"],
                profile=self.deployment.profile)
        return {"attachment_id": attachment["attachment_id"],
                "checkpoint_id": attachment["checkpoint_id"],
                "generation": generation, "boundary": boundary}

    # -- the obligation this ending is under ---------------------------------

    def registered(self, stage, assignment, context):
        """Commit the obligation to finish this ending, BEFORE it can start.

        W119733's provider, consumed. The intent is what makes the rest of
        this ending discoverable after a crash: cleanup is not the last act of
        a composed stage -- the gate discharge and the routing come after it --
        so between the cleanup committing and the settlement there is a window
        in which every live projection says the attempt is over and the ending
        is not.

        BEFORE THE FIRST STEP THAT CAN REACH CLEANUP, which is why this is
        called from the ending's own entry rather than from anywhere later. It
        certifies nothing: the disposition and the terminal digest are the
        WORKER's claims and the retention operands are this deployment's
        configured facts, kept only so the same ending can be re-entered from
        them. Every one of them is proved again by its own owner.
        """
        deployment = self.deployment
        terminal = context["terminal"] or {}
        return ending.register_ending(
            deployment.jobs, stage, assignment=assignment,
            disposition=context["disposition"],
            terminal_manifest_digest=terminal.get("manifest_digest"),
            retention_disposition=deployment.retention_disposition,
            retention_policy_digest=deployment.retention_policy_digest)

    def historical(self, stage, assignment):
        """The recorded obligation of an attempt whose runtime is already gone.

        W122060. THE ENTRY POINT THE ORDINARY ENDING CANNOT BE. Everything
        `_SingleWorker.ending` does before it reaches this composition is about
        a live attempt: it adopts the exchange delivery, reads the terminal the
        container wrote, mounts the roots that container was started over and
        materializes its credential. After the cleanup none of those is
        evidence any more -- the delivery may be collected, the runtime is
        destroyed and the writer that made the mount is revoked -- and the
        acts still owed are the discharge and the routing, which need none of
        them.

        SO THE OPERANDS COME FROM THE REGISTERED OBLIGATION rather than from a
        live exchange, and they are the same operands the first pass used: it
        is one ending re-entered, not a second one composed out of whatever
        can still be read. `None` means there is nothing historical here, and
        the ordinary path answers.

        IT ADOPTS NOTHING. An attempt with no registered intent is not
        migrated, defaulted or assumed; it takes the ordinary path and refuses
        there if its runtime is gone, because an obligation this store never
        recorded is not one this deployment may invent on its behalf.
        """
        attempt_id = stage["attempt_id"]
        intent = ending.intent_of(self.deployment.jobs, stage["stage_id"],
                                  stage["episode"])
        if intent is None:
            return None
        state = attempt_runtime_of(self.deployment.control, attempt_id)
        if (state or {}).get("execution_runtime") != "destroyed":
            return None
        # THE WORKER'S OWN ENVELOPE, AS RECORDED. `_correlated` compares this
        # against the manifest the manager validated over the bytes it read,
        # so a recorded digest that does not describe the frozen result
        # refuses there -- persisting the claim never promoted it to evidence.
        terminal = {"ending": "answered",
                    "disposition": intent["disposition"],
                    "manifest_digest": intent["terminal_manifest_digest"]}
        return {"attempt_id": attempt_id,
                "disposition": intent["disposition"], "terminal": terminal,
                "assignment": assignment, "intent": intent}

    # -- the ending ----------------------------------------------------------

    # -- the ending ----------------------------------------------------------

    def end(self, worker, stage, job, context):
        """This role's accepted ending, in the ORDER its obligation requires.

        W122060. THE WHOLE OF THIS FUNCTION IS THE ORDER, and every step in it
        is somebody else's accepted act:

          1. REGISTER the obligation, before the driver can reach cleanup;
          2. run the accepted ending -- ordinary or resumed, the driver
             decides which from the runtime's own axis;
          3. DISCHARGE the quiescence gate the ending's own fence installed,
             through the port of the participant that held the assignment;
          4. route what the answer earned; and only then
          5. SETTLE the obligation, naming the records of all four.

        FIVE IS LAST BECAUSE THREE AND FOUR ARE NOT THE DRIVER'S. Cleanup is
        the ending's last act and not the composed stage's, so a settlement
        written when the driver returned would close an obligation with the
        gate still holding the Work and the correction never opened -- and the
        retry that is the only thing left to perform them would be gone with
        it. Every step replays, so a death between any two re-enters here.

        A HELD REVIEW SETTLES NOTHING. An unresolved reviewer claim is not an
        ending that finished; the obligation stays owed, the operator has the
        frozen evidence named in the answer, and no correction is opened on a
        verdict nobody gave.
        """
        deployment = self.deployment
        attempt_id = context["attempt_id"]
        assignment = context["assignment"]
        self.registered(stage, assignment, context)
        prepared = self._prepared.get(attempt_id) or self._prepare(attempt_id)
        if self.role == "implementation":
            answered = review_driver.end_implementation(
                deployment.control, worker.port, context["adapter"],
                deployment.publication, attempt_id=attempt_id,
                disposition=context["disposition"],
                terminal=context["terminal"],
                writer_id=prepared["writer_id"],
                generation=prepared["generation"],
                profile=deployment.profile,
                retention_disposition=deployment.retention_disposition,
                retention_policy_digest=deployment.retention_policy_digest,
                # THE PROPOSAL OPERAND IS THE DRIVER'S, NOT A DOCUMENT THIS
                # DEPLOYMENT COMPOSES. `retain_proposal` reads the worker's own
                # opaque claim out of the frozen result and every other member
                # from its manager/Authority owner, so anything supplied here
                # would be the deployment asserting what the result proves.
                proposal=None)
        else:
            # THE VERDICT IS THE REVIEWER'S AND IS READ OUT OF ITS OWN FROZEN
            # RESULT. W110772's accepted channel, and the reason this replaced
            # `deployment.verdict`: that seam took a verdict as an operand, so
            # the only deployment that could supply one was a deployment
            # deciding the review. `_no_verdict` refused honestly and made the
            # composed review stage unreachable; supplying one would have been
            # worse.
            answered = review_driver.end_review_from_result(
                deployment.control, worker.port, context["adapter"],
                attachment_id=prepared["attachment_id"],
                disposition=context["disposition"],
                terminal=context["terminal"],
                profile=deployment.profile,
                retention_disposition=deployment.retention_disposition,
                retention_policy_digest=deployment.retention_policy_digest)
        return self._finished(worker, stage, assignment, answered)

    def _finished(self, worker, stage, assignment, answered):
        """Everything after the driver, in the order the fence requires.

        W122060, consuming W125189. THE ROUTE MOVES BEFORE THE GATE CLEARS,
        and the ordering is the whole of the correction: discharging first
        returns the Work to `queued` on the route the FINISHED role is served
        on, so the participant that just ended can reclaim it before the next
        role is offered anything -- the reclaim race the routing record
        measured. `route_fenced` changes only the route and leaves the phase,
        the gate and the generation exactly as the fence left them, so the
        handoff is committed while nothing can yet write.

        This explicitly replaces owner119712's discharge-before-route ordering
        for the composed fenced handoff.

        A CORRECTION IS OPENED ONLY AFTER ITS HANDOFF IS COMMITTED, for the
        same reason, and a held outcome selects no route at all: nobody is
        scheduled on a verdict nobody gave.
        """
        if answered.get("outcome") == "held" \
                or answered.get("cleaned_up") is False:
            return answered
        # THE HANDOFF'S OWN RECEIPT IS THE AUTHORITY'S, at an identity this
        # deployment derives deterministically, so the settlement does not
        # carry a copy of it -- `ending.EVIDENCE_OPTIONAL` is a closed set this
        # Work does not own, and a member it does not name is not one to
        # invent here.
        self._handed_off(worker, stage, assignment, answered)
        discharge = self._discharged(worker, answered)
        routed = self.deployment.routed(stage, answered)
        if self._fenced_gate(answered) and discharge is None:
            # REVIEW [2]: AN ACKNOWLEDGEMENT IS NOT A SUBSTITUTE FOR THE
            # RECEIPT. The Job settlement is this manager's local record that
            # the ending finished; closing it while the act that cleared the
            # gate has no owned receipt would end the only retry that can
            # still obtain one.
            _refuse(f"attempt {answered['attempt_id']!r} fenced a runtime "
                    f"gate and this manager holds no committed discharge "
                    f"receipt for it; an ending is acknowledged after its "
                    f"gate is discharged, not instead of it",
                    category="refused", code="precondition")
        ending.settle_ending(self.deployment.jobs, stage,
                             assignment=assignment,
                             evidence=self._evidence(answered, routed,
                                                     discharge))
        return routed

    def _handed_off(self, worker, stage, assignment, answered):
        """Move the Work to the route its next role is served on.

        THE OPERANDS ARE ALL COMMITTED RECORDS, and none of them is a guess
        about who acts next:

          * the original assignment, as this ending was given it;
          * the cancellation THIS ending's own checkpoint fenced under, read
            off that checkpoint's fence rather than re-derived;
          * `from_route`, the route this attempt's own committed claim was
            authorized on -- `claimed_offers_for` answers exactly one; and
          * `to_route`, this worker's existing configured `review_route`.

        NO ROUTE MAP AND NO ROLE GUESS. The routing record is explicit that the
        existing per-worker operand is the source, so a deployment that named a
        second one would be keeping two accounts of one configured fact.
        """
        deployment = self.deployment
        attempt_id = answered["attempt_id"]
        fence = self._fence_operation(answered)
        if fence is None:
            return None
        return worker.handoff(
            expect=assignment, attempt_id=attempt_id,
            fence_operation_id=fence,
            from_route=self._claim_route(attempt_id),
            to_route=self._next_route(worker, answered))

    def _claim_route(self, attempt_id):
        """The one route this attempt's own committed claim was authorized on.

        `claimed_offers_for` is attempt-keyed and answers the offers this
        manager recorded as claimed. Exactly one, because a fenced handoff
        moves the Work OFF the route its claim named, and two claims would
        leave which one ambiguous.
        """
        claimed = claimed_offers_for(self.deployment.control, attempt_id)
        if len(claimed) != 1:
            _refuse(f"attempt {attempt_id!r} carries {len(claimed)} committed "
                    f"claimed offers and a fenced handoff moves the Work off "
                    f"the one route its own claim was authorized on",
                    category="refused", code="precondition")
        return claimed[0]["work_route"]

    def _next_route(self, worker, answered):
        """Where this answer sends the Work, and a correction is not forward.

        REVIEW 2026-09-09T05:33Z [1]. This used the ending worker's own
        outgoing route for every answer, so a changes-requested review sent the
        Work to INTEGRATION and the correction round's implementation claim
        then refused against it. The approved contract is explicit: a
        correction's target is the reviewed checkpoint PRODUCER's own committed
        claim route, and the reviewed checkpoint is what names that producer --
        the checkpoint names its writer and the writer names its attempt.

        SO THE TARGET IS DERIVED FROM THE CORRELATED RECORD rather than from a
        role-to-route mapping this deployment would otherwise have to keep. The
        forward direction stays the worker's own configured `review_route`,
        which is the operand this deployment already had.
        """
        if answered.get("outcome") != "correction":
            return worker.given["review_route"]
        control = self.deployment.control
        checkpoint = review_cycles.checkpoint_of(control,
                                                 answered["checkpoint_id"])
        writer = review_cycles.writer_of(control, checkpoint["writer_id"])
        return self._claim_route(writer["runtime_attempt_id"])

    @staticmethod
    def _fence_operation(answered):
        """The committed cancellation THIS ending recorded, whichever it was.

        READ OFF THE RECORD rather than re-derived from the attempt: the fence
        is the act that installed the gate this handoff must not disturb, and
        each ending keeps its own. An implementation ending fences at the
        checkpoint freeze and the checkpoint carries it; a review ending
        fences when its verdict is recorded and the verdict carries it. Both
        are the same document, so one reader answers both, and an answer
        carrying neither is one no handoff can be about.
        """
        for record, member in (("checkpoint", "fence"),
                               ("verdict_record", "review_fence")):
            fence = (answered.get(record) or {}).get(member) or {}
            intent = fence.get("intent") or {}
            held = intent.get("authority_operation_id")
            if held is not None:
                return held
        return None

    def _discharged(self, worker, answered):
        """W119548's act, when the fence THIS ending committed installed a gate.

        THE MANAGER HOLDS THE EVIDENCE AND HELD NO WAY TO CARRY IT. The
        checkpoint freeze and the verdict's cancellation each end an
        assignment, and the Authority installs `runtime-quiescence:<generation>`
        in the same transaction -- deliberately, because ending an assignment
        is not evidence that the container is gone. Only a positive
        observation of the exact runtime is, and `authorize_cleanup` makes
        exactly that observation. The accepted act carries it across.

        WHETHER ONE IS OWED IS THE AUTHORITY'S FACT, and it is asked rather
        than assumed: a deployment whose Work is not gated at all must not
        fabricate a quiescence obligation, and this composition cannot tell
        from its own records which of those it is in. A committed discharge
        replays before the question is asked, so a lost local answer does not
        depend on a gate that has since been cleared.

        THE ACT ITSELF SELECTS NOTHING ELSE. Its two operands are the attempt
        and the retention policy identity; the authority, the Work, the
        participant, the generation, the gate token, the runtime identity and
        the absence evidence are all derived inside it from durable records
        this manager owns.
        """
        control = self.deployment.control
        attempt_id = answered["attempt_id"]
        held = gate_discharge_of(control, attempt_id)
        if held is not None:
            return held
        if not self._fenced_gate(answered):
            return None
        return discharge_quiescence_gate(
            control, worker.port, attempt_id=attempt_id,
            retention_policy_digest=self.deployment.retention_policy_digest)

    @staticmethod
    def _fenced_gate(answered):
        """The gate THIS ending's own fence installed, if it installed one.

        REVIEW 2026-09-09T05:33Z [2]. Owedness used to be decided from TODAY'S
        Work projection, and that is exactly wrong for the case it has to
        answer: when the remote discharge committed and its local receipt was
        lost, the gate is already gone -- so the projection says nothing is
        owed and the ending settles carrying no reference to the act that
        cleared it. The obligation is a fact about what this ending FENCED,
        which is committed and cannot disappear, and the accepted provider's
        step two replays the Authority's own answer for exactly this shape.
        """
        for record, member in (("checkpoint", "fence"),
                               ("verdict_record", "review_fence")):
            fence = (answered.get(record) or {}).get(member) or {}
            gate = (fence.get("fenced") or {}).get("gate")
            if gate:
                return gate
        return None

    @staticmethod
    def _evidence(answered, routed, discharge):
        """The correlated owner references a settlement records.

        NOT A SUMMARY AND NOT A CLAIM. Each member is an identity an operator
        can go and look up in the record of the owner that produced it, which
        is the whole reason the settlement carries any: the three required
        ones name the frozen result, the manifest this manager validated and
        the intake receipt, and each optional one is OMITTED when there was
        nothing of that kind to name rather than present and empty.
        """
        evidence = {"result_id": answered["result_id"],
                    "manifest_digest": answered["manifest_digest"],
                    "receipt_digest": answered["receipt_digest"]}
        if answered.get("checkpoint_id") is not None:
            evidence["checkpoint_id"] = answered["checkpoint_id"]
        if answered.get("verdict_id") is not None:
            evidence["verdict_id"] = answered["verdict_id"]
        if answered.get("outcome") is not None:
            evidence["outcome"] = answered["outcome"]
        if discharge is not None:
            evidence["gate_discharge"] = discharge["gate"]
        opened = (routed or {}).get("correction")
        if opened is not None:
            # THE ATTEMPT THE ROUTING ACT OPENED, because that is the durable
            # thing an operator follows from here: a correction's whole effect
            # is the next round it starts.
            evidence["routed"] = opened["implementation"]["attempt_id"]
        return evidence


# THE RUNTIME STATE THAT SAYS NO START WAS EVER REQUESTED. A delivery can
# exist with no runtime behind it -- the namespaces are materialized before the
# container -- and that attempt is admission's to re-enter, not a continuation's
# to refresh.
_UNSTARTED = "not-started"


class Integration:
    """The accepted serialized integration, driven from the Job's own stage.

    EVERY OPERAND IS RE-READ FROM DURABLE STATE, which is what makes this
    re-enterable rather than a handoff from the tick that accepted the review.
    The line answers which checkpoint was accepted; the checkpoint names its
    writer; the writer names the attempt whose proposal was published; and
    `retain_proposal` replays that attempt's retained manifest, out of which
    the published proposal's own identity is read. Nothing is carried in a
    variable across a tick, and nothing is carried across a restart.

    IT DECIDES NOTHING ABOUT THE OUTCOME. `admit_accepted` writes the accepted
    receipts, admits the candidate, leases it and drives or adopts one
    serialized integration; an interrupted one comes back `held` and stays
    held, which is the operator's to look at.
    """

    def __init__(self, deployment, port=None):
        self.deployment = deployment
        self.port = port

    def required_tests(self):
        """The required-test selection, DERIVED from configured material.

        Owner ruling M115946, on this Work's obligation 115920: derive it from
        the configured implementation task and its bound input manifest, never
        from what the worker REPORTED. `driver._owned_requirements` already
        names this derivation as W103083's; the deployment document stays
        closed and gains no member for it, exactly as the integrator and
        publisher participants are derived rather than configured.

        THE PRODUCER'S OWN CONFIGURATION IS THE SOURCE, read through
        `single_worker`'s own validator rather than re-implemented here: it
        holds the task bytes once, no-follow and bounded, and a second reader
        with its own opinion about that file is the duplicate deployment
        opinion this assembly boundary exists to prevent.
        """
        import hashlib
        import json as _json

        named = [one for one in self.deployment.given["workers"]
                 if one["role"] == "implementation"]
        if len(named) != 1:
            _refuse(f"this deployment names {len(named)} implementation "
                    f"workers; the required-test selection is derived from "
                    f"exactly one producer's configured task",
                    category="refused", code="precondition")
        # THE HELD FORM, CONSUMED AS IT STANDS. Review 2026-09-08T04:06:54Z
        # [P1]: this re-validated the producer document through
        # `single_worker._held`, which the factory had ALREADY applied -- and
        # that validator correctly rejects its own derived members, so every
        # real integration tick stopped here. The bytes were read once at
        # configuration, no-follow and bounded; reopening the path would also
        # let a task file replaced after configuration substitute new expected
        # bytes, which is exactly what the held form prevents.
        held = named[0]["deployment"]
        payload = held.get("task_bytes")
        manifest = held.get("input_manifest")
        if type(payload) is not bytes or type(manifest) is not dict:
            _refuse("the configured producer carries no held task bytes and "
                    "input manifest; the required-test selection is derived "
                    "from the deployment the factory validated",
                    category="refused", code="precondition")
        task = _json.loads(payload)
        argv = task.get("verification")
        if type(argv) is not list or not argv:
            _refuse("the configured implementation task names no verification "
                    "command; an integration is admitted behind an ordinary "
                    "test run and never ahead of one",
                    category="refused", code="precondition")
        return {"task_id": task["task_id"],
                "task_digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
                "argv": list(argv),
                "input_manifest_digest": manifest["manifest_digest"]}

    def _correspondent(self, job, requirement):
        """The Job, the producer and the input this requirement names AGREE.

        M115946 requires the correspondence check, and it is here rather than
        inside the derivation because the derivation is about configured
        material and this is about the Job the tick arrived for -- including a
        correction attempt, which carries the same producer input.
        """
        if type(job) is not dict:
            return
        held = job.get("input_digest")
        if held is not None and held != requirement["input_manifest_digest"]:
            _refuse(f"this Job names input {held!r} and the configured "
                    f"producer's manifest is "
                    f"{requirement['input_manifest_digest']!r}; a required "
                    f"test selection describes the producer this Job ran",
                    category="refused", code="precondition")

    def _published(self, stage):
        """This attempt's delivery and the assignment it carries, or None.

        THE PUBLIC READERS AND NOTHING ELSE, at the configured delivery home,
        this stage's exact attempt and the deployment's workspace group. An
        absent or unpublished delivery answers `None` rather than inventing an
        assignment -- there is nothing to continue, and admission owns what
        happens next.
        """
        delivery = runtime.adopt_delivery(
            self.deployment.integration_root,
            attempt_id=stage["attempt_id"],
            workspace_group=self.deployment.workspace_group)
        if delivery is None:
            return None, None
        return delivery, runtime.published_assignment(delivery)

    def run(self, stage, job):
        deployment = self.deployment
        if self.port is None:
            # W103083: THE ONE CAPABILITY THIS BUILD DOES NOT HAVE. Every
            # other operand below is composed from an accepted operation. A
            # runtime port that starts an integration container over
            # `runtime.materialize_delivery`'s namespaces exists nowhere in
            # this tree -- `integrate_next` types the port and calls it, and
            # the only implementations are focused-test fixtures. Reported as
            # itself rather than stubbed, and contained to this stage: the
            # implementation and review stages of every Job go on running.
            _refuse("this deployment holds no integration runtime port; "
                    "`integrate_next` starts the integrator through one and "
                    "no accepted composition in this build builds one over "
                    "the integration delivery's namespaces",
                    category="refused", code="capability")
        control = deployment.control
        line = deployment.line()
        accepted = review_cycles.integration_checkpoint(control,
                                                        line["line_id"])
        if accepted is None:
            _refuse(f"development line {line['line_id']!r} holds no accepted "
                    f"integration checkpoint; an integration stage runs "
                    f"behind an accepted verdict and never ahead of one",
                    category="refused", code="precondition")
        operands = {
            "canonical_target_id": deployment.given["canonical_target_id"],
            "line_id": line["line_id"],
            "proposal_id": deployment.published_proposal(accepted),
            "policy_generation": deployment.given["policy_generation"],
            "profile": deployment.integration_profile,
            "attempt_id": stage["attempt_id"],
            "launch_root": deployment.integration_root,
            "workspace_group": deployment.workspace_group,
            "required_tests": self.required_tests()}
        self._correspondent(job, operands["required_tests"])
        sessions = (deployment.sessions["verification"],
                    deployment.sessions["review"],
                    deployment.sessions["approval"],
                    deployment.sessions["integrator"])

        delivery, assignment = self._published(stage)
        if assignment is None:
            # THE FIRST TICK FOR THIS ATTEMPT. Preparation records and
            # activates the manager attempt and mints its private credential,
            # and it must precede admission: `integrate_next` proves the
            # runtime `not-started` BEFORE it asks the port to run, so an
            # attempt prepared afterwards is prepared one call too late.
            self.port.prepare(stage, job)
            return admit_accepted(
                deployment.integration, control, deployment.jobs,
                deployment.authority, *sessions, self.port, **operands)

        # A LATER TICK OVER A DELIVERY THIS DEPLOYMENT ALREADY PUBLISHED.
        # Owner ruling M115946: refresh FIRST, then continue only when the
        # port's own marker confirms this live execution started exactly this
        # assignment. Reading a persisted assignment grants no permission --
        # a fresh serving incarnation has no marker and falls through to
        # admission, which owns the restart hold it has always owned.
        seen = self.port.observed(stage["attempt_id"], assignment)
        if seen["execution_runtime"] == _UNSTARTED:
            # A PUBLISHED DELIVERY WITH NO RUNTIME BEHIND IT IS STILL A FIRST
            # START, so it is prepared exactly like one. W103083 review
            # 2026-09-08T12:41:47Z [P1]: an interrupted first admission leaves
            # the namespaces and the published assignment durable while the
            # attempt's runtime stays `not-started`, and this branch went
            # straight to admission -- which proves the runtime `not-started`
            # and then asks the port to run with no execution-local credential
            # delivery to run it with. Preparation is the manager's own
            # effectively-once act and reuses the capability this execution
            # already prepared, so re-entering costs nothing and mints
            # nothing twice. No refresh is reached: reconciling an attempt no
            # start was ever requested for is the write that branch refuses.
            self.port.prepare(stage, job)
        else:
            # AND A STARTED OR UNCERTAIN RUNTIME IS NOT PREPARED HERE. Its
            # credential custody belongs to the runtime that holds it, and the
            # hold `admit_accepted` has always owned is what answers a marker
            # this execution does not have.
            self.port.refresh(stage["attempt_id"])
            if self.port.may_continue(assignment, delivery):
                return continue_accepted(
                    deployment.integration, control, deployment.jobs,
                    deployment.authority, *sessions, **operands)
        return admit_accepted(
            deployment.integration, control, deployment.jobs,
            deployment.authority, *sessions, self.port, **operands)


class StageDeployment:
    """Everything the three compositions above share, resolved once.

    IT HOLDS OPERANDS AND NOT DECISIONS. Which line, which profile, which
    retention policy, which Authority sessions -- each is one configured or
    durably derived fact, and every act performed with them belongs to an
    accepted operation.
    """

    def __init__(self, given, *, control, jobs, authority, integration,
                 profile, sessions, verdict=None):
        self.given = given
        self.control = control
        self.jobs = jobs
        self.authority = authority
        self.integration = integration
        self.profile = profile
        self.sessions = sessions
        self.publication = Publication(control, sessions["publisher"])
        self.integration_profile = integration_from(given)
        self.verdict = verdict or _no_verdict
        self.retention_disposition = given["retention_disposition"]
        self.retention_policy_digest = given["retention_policy_digest"]
        self.integration_root = os.path.join(given["state_root"],
                                             INTEGRATION_HOME)
        # THE NOMINAL GROUP, NOT ITS INTEGER. W103083 review
        # 2026-09-08T04:06:54Z [P1]: this held `.gid`, and the public delivery
        # readers and admission both require the `WorkspaceGroup` the manager
        # answers -- an integer is the identifier of a group, not the proof
        # that this manager configured it. No consumer in this five-path scope
        # needs the integer; one that did would take `.gid` at its own call.
        self.workspace_group = configured_workspace_group(control)
        self._roles = {one["role"]: one for one in given["workers"]}

    def generation_of(self, attempt_id):
        """This attempt's assignment generation, from its own owner."""
        return assignment_of(self.control, attempt_id)["generation"]

    def line(self):
        """THE ONE PERSISTENT LINE for this deployment's Authority and Work.

        `create_line` is create-or-recover by an identity derived from exactly
        that pair, so every tick and every incarnation reaches the same line
        and no second checkout is ever made. Read back through `line_of`
        because what the callers need is the line's state NOW rather than what
        it was when it was created.
        """
        source = self._roles["implementation"]["deployment"]
        created = review_cycles.create_line(
            self.control, source=source["source_nomination"],
            declared_base=self.given["line_declared_base"],
            profile=self.profile, authority_uuid=self.given["authority_uuid"],
            work_id=self.given["job_work_id"])
        return review_cycles.line_of(self.control, created["line_id"])

    def published_proposal(self, accepted):
        """The Authority proposal identity of an accepted checkpoint.

        DERIVED FROM THE CHECKPOINT'S OWN WRITER, so an integration reached
        after a restart names the same proposal the ending published. The
        checkpoint names its writer, the writer names its attempt, and
        `retain_proposal` replays that attempt's retained manifest -- which is
        the document `publish_candidate` selected on and which carries the
        proposal identity the Authority recorded.
        """
        writer = review_cycles.writer_of(
            self.control,
            review_cycles.checkpoint_of(
                self.control, accepted["checkpoint_id"])["writer_id"])
        retained = retain_proposal(self.control, self.sessions["publisher"],
                                   attempt_id=writer["runtime_attempt_id"])
        held = load_manifest(self.control, retained, "proposalManifest")
        if held is None:
            _refuse(f"the manager retains no proposal manifest at "
                    f"{retained!r} for the accepted checkpoint's writer",
                    category="refused", code="precondition")
        return held["proposal_id"]

    def routed(self, stage, answered):
        """What a recorded review verdict earns, and nothing it does not.

        ONE ACT AND ONE CONDITION. `correction` opens the next round in the
        Job store through the driver's own act, which cross-binds the verdict
        against the journal that recorded it rather than believing this
        answer. `accepted` earns nothing here: the Job's integration stage
        becomes eligible because its review stage ended, which is the control
        plane's derivation and not a transition this composition performs.
        And `held` is preserved exactly as it arrived -- the whole point of the
        outcome is that nobody schedules anything on it.
        """
        if answered.get("outcome") != "correction":
            return answered
        opened = review_driver.open_correction(
            self.jobs, self.control, job_id=stage["job_id"], answered=answered)
        return dict(answered, correction=opened)


class StageExecution:
    """What the serving loop is handed, and what it gives back.

    IT OWNS ITS HANDLES AND NOTHING ELSE. The Authority, the integration store
    and the three workers' operations were opened here, so `release` closes
    them here -- once, in reverse order, and with a failure in one release
    never stopping the rest. `tools.job_manager` calls `close`, which is this.

    AND IT WRAPS THE POOLED SURFACE RATHER THAN BEING IT. Review [P1]:
    `__getattr__` delegation over `PooledManagerOperations` made every serving
    method the bootstrap worker's own, which is how a serving object came to
    carry driver-facing attributes nothing reached. The two methods a stage
    driver changes are spelled here; the rest still delegate, because the
    scheduler owns them and a member re-spelled would be a second answer to a
    question that already has one.
    """

    canonical = True

    def __init__(self, pooled, *, authority, integration, workers, given,
                 sessions=None, deployment=None, integrator=None):
        self.pooled = pooled
        self.authority = authority
        self.integration = integration
        self.workers = workers
        self.configuration = given
        self.sessions = sessions
        self.deployment = deployment
        self.integrator = integrator
        self.publication = None if deployment is None else deployment.publication
        self.integration_profile = (None if deployment is None
                                    else deployment.integration_profile)

    def __getattr__(self, name):
        # THE POOLED SURFACE IS STILL THE SURFACE for everything a stage does
        # not change: `recover`, `attach`, `drain`, `binding_intent`, `admit`,
        # `claim`, `dispatch`, `observe`, `refresh_runtime`,
        # `canonical_operation` and `receipt_of` are the scheduler's.
        #
        # A PARTIALLY CONSTRUCTED DEPLOYMENT HAS NO POOL, and this must say so
        # as an attribute error rather than recursing: `__getattr__` is reached
        # for `pooled` itself while `__init__` has not yet bound it, and
        # `getattr(composed, "close", None)` in the serving loop must not be
        # answered by a lookup on `None`.
        pooled = self.__dict__.get("pooled")
        if pooled is None:
            raise AttributeError(name)
        return getattr(pooled, name)

    # -- the two the stage drivers change ------------------------------------

    def launch(self, stage, job):
        """Drive one claimed stage into its own accepted composition."""
        if stage.get("kind") == "integration":
            return self.integrator.run(stage, job)
        return self.pooled.launch(stage, job)

    def conclude(self, stage, job):
        """End one answered stage through the driver its kind belongs to.

        The implementation and review kinds reach `end_implementation` and
        `end_review` through the worker's own ending seam, so the whole
        composition below the ending -- the terminal correlation, the
        disposition vocabulary, the runtime identity and the adapter -- is the
        accepted one. The integration kind has no exchange to answer with, so
        its progress is the same re-enterable admission the launch performed.
        """
        if stage.get("kind") == "integration":
            return self.integrator.run(stage, job)
        return self.pooled.conclude(stage, job)

    # -- handles -------------------------------------------------------------

    def close(self):
        """The name `tools.job_manager` releases a factory's object by."""
        return self.release()

    def release(self):
        failures = []
        for what, close in self._closers():
            try:
                close()
            except BaseException as failure:            # noqa: BLE001
                failures.append(f"{what}: {type(failure).__name__}")
        if failures:
            _refuse("this deployment did not release cleanly: "
                    + "; ".join(failures), category="unavailable",
                    code="transport")

    def _closers(self):
        for one in reversed(self.workers):
            operations = one.get("operations")
            if operations is not None and hasattr(operations, "release"):
                yield f"the {one['role']} worker", operations.release
        if self.integration is not None:
            yield "the integration store", self.integration.close
        if self.authority is not None:
            yield "the Authority", self.authority.dispose


def _incarnation(control_store):
    """This process's incarnation, named by the store the operator opened."""
    held = getattr(control_store, "incarnation", None)
    if type(held) is not str or not held:
        _refuse("this deployment takes its coordinator incarnation from the "
                "control store the operator opened, and that store names "
                "none", category="refused", code="capability")
    return held


def _now():
    """The one instant source this module builds, when a caller supplies none."""
    from datetime import datetime, timezone

    moment = datetime.now(timezone.utc)
    return (moment.strftime("%Y-%m-%dT%H:%M:%S.")
            + f"{moment.microsecond // 1000:03d}Z")


def _profile_of(given, checkpoint_profile):
    """The checkpoint profile this deployment's line is kept under.

    ONE NAME, ONE PROFILE, and the configured name is compared against the
    object's own rather than trusted: every custody operation compares them,
    and a deployment that composed a profile whose name disagreed with its
    configuration would discover it at the first freeze.
    """
    profile = checkpoint_profile
    if profile is None:
        if given["checkpoint_profile"] != checkpoint_profiles.GIT_PROFILE:
            _refuse(f"this deployment composes the "
                    f"{checkpoint_profiles.GIT_PROFILE!r} checkpoint profile "
                    f"and the configuration names "
                    f"{given['checkpoint_profile']!r}", category="refused",
                    code="capability")
        profile = checkpoint_profiles.GitCheckpointProfile(_git_run)
    if getattr(profile, "name", None) != given["checkpoint_profile"]:
        _refuse(f"the composed checkpoint profile is named "
                f"{getattr(profile, 'name', None)!r} and this deployment is "
                f"configured for {given['checkpoint_profile']!r}",
                category="refused", code="capability")
    return profile


def _git_run(argv):
    """The production Git runner, in the closed shape the profile requires."""
    import subprocess

    answer = subprocess.run(list(argv), capture_output=True, check=False,
                            timeout=GIT_SECONDS)
    return {"returncode": answer.returncode,
            "stdout": answer.stdout.decode("utf-8", "replace"),
            "stderr": answer.stderr.decode("utf-8", "replace")}


def _pool(given, resolved):
    """The immutable pool document this configuration IS.

    ACTIVATED RATHER THAN ASSUMED, and review [P1] is a symptom of not doing
    it: `PooledManagerOperations` refuses unless the operations it is handed
    are exactly the store's own configured `(generation, worker id)` pairs, so
    a composition that never activated a pool could only ever attach to one an
    operator had activated by hand -- which is the ordinary operator
    transition this assembly exists to remove.

    THE LANE IS DERIVED FROM THE ROLE by the scheduler's own rule, quoted
    rather than restated: a review kind is the review lane and everything else
    is the implementation lane, and a worker is eligible for exactly the one
    kind this deployment configured it for.
    """
    workers = []
    for one in given["workers"]:
        deployment = one["deployment"]
        workers.append({"worker_id": one["worker_id"],
                        "lane": "review" if one["role"] == "review"
                                else "implementation",
                        "participant": deployment["participant"],
                        "profile_name": deployment["profile_name"],
                        "profile_digest": deployment["profile_digest"],
                        "eligible_kinds": [one["role"]]})
    del resolved
    return {"schema": scheduler.POOL_SCHEMA, "variant": CONFIG_SCHEMA,
            "separation_class": SEPARATION_CLASS, "workers": workers}


def operations_from(document, job_store, control_store, *, engine_run=None,
                    credential_provider=None, clock=None, checkpoint=None,
                    checkout=None, checkpoint_profile=None,
                    review_verdict=None, integration_port=None):
    """Compose the whole stage deployment, or change nothing at all.

    THE ORDER IS THE CONTRACT, AND REVIEW 2026-09-07T14-12-42Z [P1] IS WHY IT
    IS NOW THIS ONE. It used to run `worker_preflight` before the Authority
    opened, on the reading that preflight is cheap and read-only. It is not:
    it configures the control store's workspace group and storage, certifies a
    runtime profile and constructs a credential home. So a deployment whose
    RECEIPT PARTICIPANT was malformed -- a fault this module can see in the
    document it was handed -- refused only after having configured a control
    store that had never been configured before, and a configuration naming
    the wrong pool generation refused only after ACTIVATING a pool, having
    changed the very thing it then said it would not serve.

    A refusal that has already changed durable state is not a refusal. So
    every check whose answer this module can know without writing anything
    happens first, in one uninterrupted run:

      the document, closed and swept, and every path outside the checkout;
      the Job store's Authority binding, for `single_worker`'s reason -- a
        store's episode identities are derived in its own Authority's
        namespace;
      the checkpoint profile's name against the composed profile's own;
      each configured participant's principal, resolved from the Authority;
      the five sessions, minted and AUTHORIZED in the target Work's scope;
      and the pool generation activation would answer, compared before it is
        asked to answer it.

    ONLY THEN does anything change: the three preflights, the integration
    store, the workers' operations and the pool activation. Opening the
    Authority is deliberately on the early side of that line -- it is a handle
    over a store that must already exist, it writes nothing, and it is the
    only way to ask the identity and capability questions above at all.

    CONSTRUCTION FAILURE RELEASES WHAT IT ALREADY OPENED. A composer that
    leaked an Authority on the fourth of five steps would leave a lock nobody
    holds a reference to, so every partial state is unwound through the same
    `release` the serving loop uses.

    AND IT REPAIRS NOTHING. A refusal here leaves whatever another actor
    already put in these stores exactly as it found it; this module unwinds
    only the handles it opened itself.
    """
    given = held_configuration(document, checkout=checkout)
    held = getattr(job_store, "authority_uuid", None)
    if held != given["authority_uuid"]:
        _refuse(f"this Job store is bound to Authority {held!r} and this "
                f"configuration names {given['authority_uuid']!r}",
                category="refused", code="operation-collision")
    profile = _profile_of(given, checkpoint_profile)

    composed = StageExecution(None, authority=None, integration=None,
                              workers=[], given=given)
    try:
        composed.authority = Authority.open(
            given["authority_store"],
            expected_authority_uuid=given["authority_uuid"])
        # -- everything below this line still writes nothing ----------------
        resolved = _resolved(composed.authority, given)
        # THE SESSIONS ARE MINTED AND AUTHORIZED BEFORE ANY STORE THEY ACT
        # OVER IS TOUCHED, because a deployment missing a grant discovers it
        # with somebody's candidate already frozen and unacceptable.
        composed.sessions = _minted(composed.authority, given,
                                    _work_scope(composed.authority,
                                                given["job_work_id"]))
        pool = _pool_generation(job_store, given, resolved)
        # -- and everything below this line does ----------------------------
        #
        # `worker_preflight` is the half of a worker deployment the engine,
        # image, network and workspace group can refuse, and it CONFIGURES the
        # control store to do it.
        providers = [single_worker.worker_preflight(
            one["deployment"], control_store,
            credential_provider=credential_provider, engine_run=engine_run)
            for one in given["workers"]]
        # THE INCARNATION AND THE CLOCK ARE THE ONES DRIVING THIS RUN, taken
        # from the control store rather than invented. A coordinator opened
        # under a name no other store in this process shares would make its
        # recovery evidence uncorrelatable with the manager's own, and a
        # deployment that built a second clock would have two instant sources
        # a fixture could pin one of.
        composed.integration = IntegrationStore.open(
            given["integration_store"],
            incarnation=_incarnation(control_store),
            clock=clock or getattr(control_store, "_now", None) or _now)
        deployment = StageDeployment(
            given, control=control_store, jobs=job_store,
            authority=composed.authority, integration=composed.integration,
            profile=profile, sessions=composed.sessions,
            verdict=review_verdict)
        composed.deployment = deployment
        composed.publication = deployment.publication
        composed.integration_profile = deployment.integration_profile
        composed.integrator = Integration(deployment, integration_port)
        for one, provider in zip(given["workers"], providers):
            stage = (None if one["role"] == "integration"
                     else StageComposition(deployment, role=one["role"],
                                           worker_id=one["worker_id"]))
            operations = single_worker.worker_operations(
                one["deployment"], control_store, composed.authority, provider,
                engine_run=engine_run, clock=clock, checkpoint=checkpoint,
                stage=stage,
                # ONE AUTHORITY, RELEASED ONCE. A worker that disposed the
                # shared handle would take the other two down with it.
                dispose=lambda: None)
            composed.workers.append(dict(one, operations=operations))
        generation = scheduler.activate_pool(job_store, pool,
                                             resolved)["generation"]
        if generation != given["pool_generation"]:
            # THE ACCEPTED OPERATION'S OWN ANSWER, KEPT. `_pool_generation`
            # above predicts this from the same durable state and refuses
            # before the activation; this compares what actually happened, so
            # a prediction that ever drifts from the scheduler's rule is
            # caught here rather than trusted.
            _refuse(f"this store's active pool generation is {generation} and "
                    f"the configuration names {given['pool_generation']}; a "
                    f"deployment resuming against a pool that has moved on "
                    f"refuses rather than serving under a generation nobody "
                    f"configured", category="refused",
                    code="operation-collision")
        composed.pooled = PooledManagerOperations(
            job_store,
            {(generation, one["worker_id"]): one["operations"]
             for one in composed.workers},
            resolved_principals=resolved)
        return composed
    except BaseException:
        composed.release()
        raise


def _pool_generation(job_store, given, resolved):
    """Which generation `activate_pool` WOULD answer, decided before it acts.

    REVIEW 2026-09-07T14-12-42Z [P1]: the configured generation was compared
    against the activation's answer, so a store with a fresh Job database and
    a configuration naming generation 4 refused for the mismatch -- with the
    pool it claimed not to serve now activated at generation 1. The refusal
    had already changed the thing it refused over.

    The scheduler's rule is read from the store rather than restated: an
    absent pool means the next activation mints generation 1, the ACTIVE
    generation's digest matching this document means the activation is a
    revalidation of it, and any other document -- including a deliberate
    return to a historical one -- is the next generation. `own_pool` runs
    here too, so a malformed pool is refused while nothing has been written.

    ANSWERS THE OWNED DOCUMENT, so the activation below and this comparison
    are over the same bytes rather than over two constructions of them.
    """
    pool = scheduler.own_pool(_pool(given, resolved))
    active = scheduler.active_generation(job_store)
    if active is None:
        would = 1
    elif active["digest"] == digest(pool):
        would = active["generation"]
    else:
        would = active["generation"] + 1
    if would != given["pool_generation"]:
        _refuse(f"activating this deployment's pool would answer generation "
                f"{would} and the configuration names "
                f"{given['pool_generation']}; a deployment resuming against a "
                f"pool that has moved on refuses before it activates one "
                f"rather than after", category="refused",
                code="operation-collision")
    return pool


def _resolved(authority, given):
    """Every configured participant's principal, resolved from the Authority.

    NOT FROM THE DOCUMENT. A deployment that answered this from its own
    configuration would be proving the pool against the thing it is trying to
    check, and `PooledManagerOperations` takes this precisely so an endpoint
    that has come to mean another principal refuses at attachment rather than
    at the first operation that happens to compare.

    REVIEW 2026-09-07T14-12-42Z [P1]: this ran after the three preflights had
    configured a control store, because it read the constructed operations
    rather than the held configuration. It takes the document instead, so the
    identity questions are answered while nothing has been written -- and it
    compares each worker's CONFIGURED principal here, which is the same
    refusal `worker_operations` makes later, at the moment the message is
    still about a configuration rather than about a launch.
    """
    resolved = {}
    for one in given["workers"]:
        deployment = one["deployment"]
        who = deployment["participant"]
        principal = _authority_read(
            f"the {one['role']} worker's participant {who!r} is not one this "
            f"Authority resolves",
            lambda who=who: authority.principal_of(who))
        if principal != deployment["principal"]:
            _refuse(f"the {one['role']} worker's participant {who!r} resolves "
                    f"to {principal!r} and its deployment is configured for "
                    f"{deployment['principal']!r}", category="refused",
                    code="capability")
        resolved[who] = principal
    return resolved


def integration_from(given):
    """The runtime profile an accepted integration is driven under."""
    profile = given["integration_profile"]
    return integration_profile(
        profile_kind=profile["profile_kind"],
        profile_version=profile["profile_version"],
        integrator_participant=profile["integrator_participant"],
        instructions_digest=profile["instructions_digest"])


def _read(place):
    """The configuration document, bounded and read once."""
    _path(place, "the stage-execution configuration path")
    with open(place, "rb") as reading:
        raw = reading.read(MAX_CONFIG_BYTES + 1)
    if len(raw) > MAX_CONFIG_BYTES:
        _refuse(f"a stage-execution configuration is at most "
                f"{MAX_CONFIG_BYTES} bytes", code="limit")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        _refuse("the stage-execution configuration is not a readable document")


def _configuration():
    place = os.environ.get(CONFIG_ENV)
    if not place:
        _refuse(f"this deployment reads its configuration from {CONFIG_ENV} "
                f"and it is unset", category="refused", code="capability")
    return _read(place)


def factory(job_store, control_store):
    """The `module:attribute` entry point `tools.job_manager` already loads."""
    return operations_from(_configuration(), job_store, control_store)


# -- the observation-only surface --------------------------------------------


class StageObservation:
    """`status --observe`'s reader for a POOLED deployment.

    REVIEW [P2]: this module supplied no observation factory at all, so an
    operator asking `status --observe` for a stage deployment had to name the
    SERVING one -- which opens an Authority, mints five sessions, configures a
    control store, certifies profiles, activates a pool and carries every act
    a read must not hold. The separation the Job manager already keeps between
    its two loaders was available and unused.

    WHAT IT ADDS TO `single_worker`'S OWN READER IS THE ALLOCATION LOOKUP, and
    that is the only thing a pool changes about observing. Each worker's
    durable exchange is reconstructed by the accepted `_Observation`; which
    worker holds a given attempt is the scheduler's own recorded answer. A
    stage with no allocation is answered by no worker rather than by whichever
    one sorts first -- the same rule `PooledManagerOperations._reader` keeps,
    for the same reason: reporting one worker's silence as another's state is
    a false observation rather than a missing one.

    IT OPENS NOTHING AND RECORDS NOTHING. No Authority, no session, no pool
    activation, no workspace allocation, no runtime refresh.
    """

    canonical = True

    def __init__(self, given, workers, job_store, control_store):
        self.jobs = job_store
        self.readers = {}
        # THE RAW WORKER DOCUMENTS, NOT THE HELD ONES. `held_configuration`
        # answers each worker's deployment as `single_worker._held` OWNED it,
        # with the derived members that reading adds; the accepted observation
        # reader performs its own reading and refuses a document carrying
        # them. Holding the configuration is still what proves this
        # observation is over a deployment that could serve, so both happen.
        raw = {one["worker_id"]: one["deployment"] for one in workers}
        for one in given["workers"]:
            self.readers[one["worker_id"]] = single_worker._Observation(
                raw[one["worker_id"]], control_store, job_store=job_store,
                roles=ROLES)

    def observe_exchange(self, stage):
        """The durable exchange of whichever worker holds this stage.

        NEVER RAISES, for the reason the accepted reader does not: the
        projection reads this for every stage on every pass, and one stage
        nobody can answer for must not stop a status run from reporting
        anything at all.
        """
        try:
            allocation = scheduler.allocation_of(self.jobs,
                                                 stage["attempt_id"])
        except ContractRefusal:
            return None
        if allocation is None:
            return None
        reader = self.readers.get(allocation["worker_id"])
        if reader is None:
            return None
        return reader.observe_exchange(stage)


def observation_from(document, job_store, control_store, *, checkout=None):
    """Build the observation-only surface from one already-read document."""
    return StageObservation(held_configuration(document, checkout=checkout),
                            document["workers"], job_store, control_store)


def observing_factory(job_store, control_store):
    """The `status --observe` entry point, named the way `factory` is."""
    return observation_from(_configuration(), job_store, control_store)
