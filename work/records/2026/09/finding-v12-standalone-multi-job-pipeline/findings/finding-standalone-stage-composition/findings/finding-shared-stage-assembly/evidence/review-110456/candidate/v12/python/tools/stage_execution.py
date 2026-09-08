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

from baton_v12.authority import Authority
from baton_v12.contracts import ContractRefusal
from baton_v12.integration import (IntegrationStore, integration_profile,
                                   publish_candidate, retain_proposal)
from baton_v12.job_manager.scheduler import PooledManagerOperations

from . import single_worker

__all__ = ["CONFIG_ENV", "CONFIG_SCHEMA", "ROLES", "StageExecution",
           "factory", "operations_from"]

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
            "retention_disposition")
_WORKER_MEMBERS = ("worker_id", "role", "deployment")
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
    given = _document(document, "a stage-execution configuration", _MEMBERS)
    if given["schema"] != CONFIG_SCHEMA:
        _refuse(f"this deployment reads {CONFIG_SCHEMA} and this document is "
                f"{given['schema']!r}")
    _text(given["authority_uuid"], "the configured Authority")
    _text(given["job_work_id"], "the implementation Work")
    _text(given["review_work_id"], "the review Work")
    _text(given["canonical_target_id"], "the canonical target")
    _text(given["checkpoint_profile"], "the checkpoint profile name")
    _text(given["retention_disposition"], "the retention disposition")
    _digest(given["retention_policy_digest"], "the retention policy digest")
    if type(given["pool_generation"]) is not int \
            or type(given["pool_generation"]) is bool \
            or given["pool_generation"] < 1:
        _refuse("a pool generation counts from one")

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
        deployment = single_worker._held(named)
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


class StageExecution:
    """What the serving loop is handed, and what it gives back.

    IT OWNS ITS HANDLES AND NOTHING ELSE. The Authority, the integration store
    and the three workers' operations were opened here, so `release` closes
    them here -- once, in reverse order, and with a failure in one release
    never stopping the rest. `tools.job_manager` calls it exactly once.
    """

    canonical = True

    def __init__(self, pooled, *, authority, integration, workers, given,
                 sessions=None, publication=None):
        self.pooled = pooled
        self.authority = authority
        self.integration = integration
        self.workers = workers
        self.configuration = given
        self.sessions = sessions
        # THE TWO DRIVER-FACING MEMBERS. `review_driver` is handed the
        # publication seam and the checkpoint profile's name; `integration`
        # is handed the runtime profile. Both are composed from the
        # configuration and neither is a second copy of a driver's own rules.
        self.publication = publication
        self.integration_profile = (integration_from(given)
                                    if given.get("integration_profile")
                                    else None)

    def __getattr__(self, name):
        # THE POOLED SURFACE IS THE SURFACE. Delegation rather than
        # reimplementation, because every stage operation belongs to the
        # accepted scheduler and a member re-spelled here would be a second
        # answer to a question that already has one.
        return getattr(self.pooled, name)

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


def operations_from(document, job_store, control_store, *, engine_run=None,
                    credential_provider=None, clock=None, checkpoint=None,
                    sessions=None, checkout=None):
    """Compose the whole stage deployment, or open nothing at all.

    THE ORDER IS THE CONTRACT. Everything a document can be wrong about is
    refused first, while no handle exists; then the Job store's Authority
    binding is compared, for `single_worker`'s reason -- a store's episode
    identities are derived in its own Authority's namespace; then each worker's
    engine and workspace preflight runs, still before anything is opened; and
    only then are the Authority, the integration store and the three workers'
    operations constructed.

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
    if sessions is not None:
        _sessions(sessions)

    # STILL NOTHING IS OPEN. `worker_preflight` is the half of a worker
    # deployment that the engine, image, network and workspace group can
    # refuse, and running all three now means a misconfigured pool refuses
    # with no handle to release.
    providers = [single_worker.worker_preflight(
        one["deployment"], control_store,
        credential_provider=credential_provider, engine_run=engine_run)
        for one in given["workers"]]

    composed = StageExecution(None, authority=None, integration=None,
                              workers=[], given=given, sessions=sessions)
    try:
        composed.authority = Authority.open(
            given["authority_store"],
            expected_authority_uuid=given["authority_uuid"])
        composed.integration = IntegrationStore.open(
            given["integration_store"])
        for one, provider in zip(given["workers"], providers):
            operations = single_worker.worker_operations(
                one["deployment"], control_store, composed.authority, provider,
                engine_run=engine_run, clock=clock, checkpoint=checkpoint,
                # ONE AUTHORITY, RELEASED ONCE. A worker that disposed the
                # shared handle would take the other two down with it.
                dispose=lambda: None)
            composed.workers.append(dict(one, operations=operations))
        if sessions is not None:
            composed.publication = Publication(control_store,
                                               sessions["publisher"])
        composed.pooled = PooledManagerOperations(
            job_store,
            {(given["pool_generation"], one["worker_id"]): one["operations"]
             for one in composed.workers},
            resolved_principals=_resolved(composed))
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


def factory(job_store, control_store):
    """The `module:attribute` entry point `tools.job_manager` already loads."""
    place = os.environ.get(CONFIG_ENV)
    if not place:
        _refuse(f"this deployment reads its configuration from {CONFIG_ENV} "
                f"and it is unset", category="refused", code="capability")
    return operations_from(_read(place), job_store, control_store)
