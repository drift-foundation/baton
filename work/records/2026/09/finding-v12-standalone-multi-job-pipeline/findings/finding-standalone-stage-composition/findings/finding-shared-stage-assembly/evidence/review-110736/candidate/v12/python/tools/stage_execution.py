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
times here, and the two halves it was split into are the seam: everything the
engine and workspace group can refuse happens before an Authority is opened,
and the half that needs one takes an Authority this module owns.

WHAT THIS MODULE REFUSES BEFORE ANY DURABLE ACT, because a configuration that
could not be true is worth catching while nothing has been opened:

  the implementation and review stages naming different Work;
  a participant or principal shared where independence forbids it;
  a missing receipt or integration capability;
  and mutable deployment state placed inside the checkout.

AND IT CARRIES NO BEARER. Credential material reaches a worker through the
already-accepted provider registry; this document names a registry path and
slots, and a configuration carrying bytes is refused as one.
"""

import json
import os
import re

from baton_v12 import checkpoint_profiles
from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import (IntegrationStore, admit_accepted,
                                   integration_profile, publish_candidate,
                                   retain_proposal)
from baton_v12.job_manager import review_driver, scheduler
from baton_v12.job_manager.scheduler import PooledManagerOperations
from baton_v12.worker_manager import (assignment_of,
                                      configured_workspace_group,
                                      load_manifest, review_cycles)

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


def _sessions(sessions):
    """Every receipt and integration capability, proved before publication.

    `integration.driver` reaches all four AFTER a proposal is on the Authority.
    A deployment that discovered a missing one there would have published
    somebody's candidate and then been unable to accept it.
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
        for verb in ({"verification": ("verify",), "review": ("review",),
                      "approval": ("approve",),
                      "integrator": ("integrate", "receipt"),
                      "publisher": PUBLISHER_CAPABILITIES}[name]):
            if not callable(getattr(session, verb, None)):
                _refuse(f"the {name} session has no {verb} capability",
                        category="refused", code="capability")
        if getattr(session, "participant", None) is None:
            _refuse(f"the {name} session names no participant",
                    category="refused", code="capability")
    return sessions


def _minted(authority, given):
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
    """
    participants = dict(given["receipt_participants"])
    participants["integrator"] = \
        given["integration_profile"]["integrator_participant"]
    participants["publisher"] = {one["role"]: one for one in given["workers"]
                                 }["implementation"]["deployment"]["participant"]
    return _sessions({name: authority.session(who)
                      for name, who in sorted(participants.items())})


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
        return self._prepare(stage["attempt_id"])["boundary"]

    def _prepare(self, attempt_id):
        deployment = self.deployment
        control = deployment.control
        generation = deployment.generation_of(attempt_id)
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

    # -- the ending ----------------------------------------------------------

    def end(self, worker, stage, job, context):
        """This role's accepted ending, and the routing its answer earns."""
        deployment = self.deployment
        attempt_id = context["attempt_id"]
        prepared = self._prepared.get(attempt_id) or self._prepare(attempt_id)
        if self.role == "implementation":
            return review_driver.end_implementation(
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
        answered = review_driver.end_review(
            deployment.control, worker.port, context["adapter"],
            attachment_id=prepared["attachment_id"],
            disposition=context["disposition"],
            verdict=deployment.verdict(deployment.control, attempt_id),
            profile=deployment.profile,
            retention_disposition=deployment.retention_disposition,
            retention_policy_digest=deployment.retention_policy_digest)
        return deployment.routed(stage, answered)


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

    def run(self, stage, job):
        del job
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
        return admit_accepted(
            deployment.integration, control, deployment.jobs,
            deployment.authority, deployment.sessions["verification"],
            deployment.sessions["review"], deployment.sessions["approval"],
            deployment.sessions["integrator"], self.port,
            canonical_target_id=deployment.given["canonical_target_id"],
            line_id=line["line_id"],
            proposal_id=deployment.published_proposal(accepted),
            policy_generation=deployment.given["policy_generation"],
            profile=deployment.integration_profile,
            attempt_id=stage["attempt_id"],
            launch_root=deployment.integration_root,
            workspace_group=deployment.workspace_group)


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
        self.workspace_group = configured_workspace_group(control).gid
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
    """Compose the whole stage deployment, or open nothing at all.

    THE ORDER IS THE CONTRACT. Everything a document can be wrong about is
    refused first, while no handle exists; then the Job store's Authority
    binding is compared, for `single_worker`'s reason -- a store's episode
    identities are derived in its own Authority's namespace; then each worker's
    engine and workspace preflight runs, still before anything is opened; and
    only then are the Authority, its sessions, the integration store and the
    three workers' operations constructed.

    CONSTRUCTION FAILURE RELEASES WHAT IT ALREADY OPENED. A composer that
    leaked an Authority on the fourth of five steps would leave a lock nobody
    holds a reference to, so every partial state is unwound through the same
    `release` the serving loop uses.
    """
    given = held_configuration(document, checkout=checkout)
    held = getattr(job_store, "authority_uuid", None)
    if held != given["authority_uuid"]:
        _refuse(f"this Job store is bound to Authority {held!r} and this "
                f"configuration names {given['authority_uuid']!r}",
                category="refused", code="operation-collision")
    profile = _profile_of(given, checkpoint_profile)

    # STILL NOTHING IS OPEN. `worker_preflight` is the half of a worker
    # deployment that the engine, image, network and workspace group can
    # refuse, and running all three now means a misconfigured pool refuses
    # with no handle to release.
    providers = [single_worker.worker_preflight(
        one["deployment"], control_store,
        credential_provider=credential_provider, engine_run=engine_run)
        for one in given["workers"]]

    composed = StageExecution(None, authority=None, integration=None,
                              workers=[], given=given)
    try:
        composed.authority = Authority.open(
            given["authority_store"],
            expected_authority_uuid=given["authority_uuid"])
        # THE SESSIONS ARE MINTED AND PROVED BEFORE THE STORE THEY ACT OVER
        # IS OPENED, because a deployment missing one discovers it with
        # somebody's candidate already frozen.
        composed.sessions = _minted(composed.authority, given)
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
        resolved = _resolved(composed)
        generation = scheduler.activate_pool(job_store, _pool(given, resolved),
                                             resolved)["generation"]
        if generation != given["pool_generation"]:
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


def _resolved(composed):
    """Every configured participant's principal, resolved from the Authority.

    NOT FROM THE DOCUMENT. A deployment that answered this from its own
    configuration would be proving the pool against the thing it is trying to
    check, and `PooledManagerOperations` takes this precisely so an endpoint
    that has come to mean another principal refuses at attachment rather than
    at the first operation that happens to compare.
    """
    return {one["deployment"]["participant"]:
            composed.authority.principal_of(one["deployment"]["participant"])
            for one in composed.workers}


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
