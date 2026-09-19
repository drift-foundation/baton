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
import sys
import re
import stat
from types import SimpleNamespace

from baton_v12 import checkpoint_profiles
from baton_v12.authority import MAX_SAFE_INTEGER, Authority, Refusal
from baton_v12.contracts import ContractRefusal, digest, job_input_identity
from baton_v12.integration import (IntegrationStore, admit_accepted,
                                   continue_accepted, entries_of, lease_of, integration_profile,
                                   publication_for_attempt, publish_candidate,
                                   reconciliation, retain_proposal, runtime)
# W133129: FROM THEIR OWN MODULES, because `integration/__init__.py` is an
# accepted predecessor path this Work does not own. The reconciled tick reaches
# the driver's own entry point and the standalone profile directly rather than
# widening somebody else's export list.
from baton_v12.integration import git_profile
from baton_v12.integration import admission, driver
from baton_v12.integration.driver import admit_authorized_result
from baton_v12.integration.git_profile import GitIntegrationProfile
from baton_v12.job_manager import (ending, execution_limits, review_driver,
                                   scheduler)
from baton_v12.job_manager.delegation import INTEGRATION_OBSERVATION_SCHEMA
from baton_v12.job_manager.scheduler import allocation_of
from baton_v12.job_manager.submission import job_of
from baton_v12.source_profiles.checkout import clone_vector
from baton_v12.job_manager.scheduler import PooledManagerOperations
from baton_v12.worker_manager import (assignment_of,
                                      attempt_runtime_of, claimed_offers_for,
                                      configured_workspace_group,
                                      discharge_quiescence_gate,
                                      gate_discharge_of, load_manifest,
                                      review_cycles)

from . import single_worker

__all__ = ["CONFIG_ENV", "CONFIG_SCHEMA", "CONFIG_SCHEMAS",
           "MULTI_CONFIG_SCHEMA", "ROLES", "StageExecution",
           "factory", "observation_from", "observing_factory",
           "operations_from"]

CONFIG_ENV = "BATON_V12_STAGE_EXECUTION_CONFIG"

# `/1`, and the version is in the name for `single_worker`'s reason: a closed
# document from another generation is refused by an equality test rather than
# read as a compatible subset of this one.
CONFIG_SCHEMA = "baton.v12.stage-execution-deployment/1"
# W119403: THE MULTI-WORKER VARIANT, and it is a SECOND SCHEMA rather than a
# flag on the first.
#
# The one-Job document is closed and stays closed: it serves exactly one worker
# per role and refuses a second, and nothing here loosens that. A deployment
# that wants several producers says so by naming a different document, which is
# the difference between a configuration this build can serve two Jobs from and
# one that was written for a single Job and happens to parse.
#
# WHAT IT CHANGES IS THE POOL AND NOTHING ELSE. Per-Job source, task, line,
# checkpoint and target binding belong to the next cut, so the consumers that
# genuinely need one producer today refuse under this variant with a sentence
# that says so rather than quietly choosing the first worker.
MULTI_CONFIG_SCHEMA = "baton.v12.stage-execution-deployment/2"
# How a per-producer publisher session is named when there is more than one.
PUBLISHER_PREFIX = "publisher:"
CONFIG_SCHEMAS = (CONFIG_SCHEMA, MULTI_CONFIG_SCHEMA)
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

# W133129: THE THREE FACTS A RECONCILED IMPORT NEEDS AND A DIRECT ONE DOES
# NOT. They are OPTIONAL because a deployment that never reconciles never needs
# them, and because every accepted document in this tree predates them -- the
# direct path and the no-drift checks read exactly what they always did.
#
# WHY THEY LIVE HERE. `IntegrationRuntimePort` already resolves a canonical
# target directory and a workspace storage root, but it holds them privately
# and `tools/integration_worker.py` is outside this Work's scope; reading
# another module's private attributes is not a composition. Where the target
# lives is deployment wiring, and this branch has no container for that wiring
# to reach through, so the deployment says it here in its own document.
#
# `integration_observer` is a PARTICIPANT and not a capability: W133117 refuses
# a result whose causal observations were produced by one of its three judges
# or by the integrator, so the owner that RUNS the harness is configured
# separately from the three that judge what it produced.
# W103068: THE INTEGRATOR'S OWN TWO HOMES AND ITS LAUNCH SESSION, named here
# for the reason `INTEGRATION_HOME` already is: where the integration role's
# durable material lives under this deployment's `state_root` is this assembly's
# wiring, and deriving them beside the delivery home keeps one deployment's
# integration state in one place instead of asking the operator for three paths
# that may not agree. `IntegrationRuntimePort` requires a bundle home and a
# launch home as CONFIGURATION, so a composition that could not name them could
# not construct the port at all.
INTEGRATION_BUNDLE_HOME = "integration-bundles"
INTEGRATION_LAUNCH_HOME = "integration-launch"
# AND THE SESSION LABEL the launch contract is recorded under. It is one word
# about this assembly's own integration launches, not a per-Job or per-attempt
# fact, so it is named rather than configured.
INTEGRATION_LAUNCH_SESSION = "integration-session"

# THE ROUTE A MANAGED PREPARATION'S CHILD WORK IS CREATED ON.
PREPARATION_ROUTE = "integration-preparation"

_OPTIONAL_MEMBERS = ("job_bindings", "integration_target",
                     "integration_workspace", "integration_observer",
                     "integration_target_reference",
                     "integration_instructions",
                     "integration_preparation",
                     "result_judgment_workers")

# W103068, DESIGN-2026-09-11T02-27-46Z: THE EXECUTION CONFIGURATION OF THE THREE
# OWNERS THAT JUDGE A DERIVED RESULT, and it is deliberately SEPARATE from the
# three-stage pool.
#
# WHY IT IS NOT A FOURTH ROLE. `ROLES` names the three stages a Job HAS, the pool
# gives one worker per role and `scheduler.own_pool` counts capacity over them; a
# judge of a merged candidate is none of those -- it serves no Job stage and takes
# no stage allocation. Adding it to `ROLES` would have made every accepted
# deployment refuse for want of a fourth worker and would have put these actors
# in the pool that serializes integration capacity.
#
# WHY EACH ENTRY IS A COMPLETE DEPLOYMENT. The alternative was to borrow the
# review worker's image, credentials, storage and Work -- which would make the
# judgment attributable to THAT participant, and independence is the whole reason
# a judgment exists. `receipt_participants` already names WHO must judge; this
# names what each of them EXECUTES with, and the two are matched here so a
# deployment cannot configure an execution for somebody who is not a judge.
#
# KEYED BY BOUND JOB, because a derived result belongs to one Job's line and
# target. A Job with no entry has no consumer: its derived branch stays pending
# honestly rather than inventing one.
# Spelled here rather than aliased: `_RECEIPT_MEMBERS` is defined below this
# point, and one tuple read before it exists is a module that cannot import.
# `_held_judgments` compares the two sets so they cannot drift apart.
_JUDGMENT_KINDS = ("verification", "review", "approval")
_JUDGMENT_MEMBERS = ("worker_id", "deployment")
# AND THE LAUNCH CONTRACT THEY REUSE. A judgment IS a review -- of a different
# subject -- so these executions are configured under the accepted `review`
# launch role rather than a new protocol word nothing else reads.
JUDGMENT_LAUNCH_ROLE = "review"
_MEMBERS = ("schema", "authority_store", "authority_uuid", "integration_store",
            "state_root", "pool_generation", "workers", "checkpoint_profile",
            "canonical_target_id", "integration_profile", "job_work_id",
            "review_work_id", "retention_policy_digest",
            "retention_disposition", "line_declared_base",
            "receipt_participants", "policy_generation")
# WHAT A DOCUMENT SAYS ABOUT THE ONE JOB IT BINDS GLOBALLY, named apart from
# the rest because an INSTANCE that binds no Job has none of them.
#
# OWNER-FRESH-INSTALL-20260916.md: "installation starts with zero Jobs", and
# a Work, a declared base and a canonical target are facts about a Job rather
# than about a deployment -- which is why a fresh install cannot invent them
# and must not carry placeholders in their place. A `/2` document whose
# `job_bindings` is the EMPTY list is that instance: it configures the pool,
# the profiles, the stores and the receipt participants, and binds nothing.
# Every other document carries all four exactly as it did.
_JOB_MEMBERS = ("job_work_id", "review_work_id", "line_declared_base",
                "canonical_target_id")
_INSTANCE_MEMBERS = tuple(one for one in _MEMBERS if one not in _JOB_MEMBERS)


def unconfigured_work(job_store, control_store):
    """Durable state this deployment configures NOBODY to serve. READ ONLY.

    W183883, review 2026-09-16T22-58-33Z [P1]. An instance with no execution
    capacity attaches no worker, so `PooledManagerOperations.recover` loops
    over nothing and a real accepted offer in the control store was invisible:
    the manager reported an ordinary idle tick while the control store's own
    recovery called that offer recoverable. An empty report about work that
    exists is worse than a refusal, because it reads as "there is nothing
    here".

    EVERY READ, AND NOTHING ELSE. Nothing here expires, abandons, repairs,
    authorizes or executes anything: foreign state is left exactly as it is and
    NAMED, which is the only honest thing an instance that cannot serve it can
    do with it.

    WHAT COUNTS. A Job row, an active pool generation, a live stage allocation
    and a live control offer each describe work or capacity that needs a worker
    this deployment does not configure -- including, as the review required,
    control work with no matching Job row, which is why the offers are asked
    about separately rather than derived from the Jobs.
    """
    from baton_v12.job_manager import scheduler, submission
    from baton_v12.worker_manager import outstanding_offers

    found = []
    jobs = submission.job_rows(job_store)
    if jobs:
        found.append(f"{len(jobs)} Job(s) in the Job store "
                     f"({', '.join(sorted(one['job_id'] for one in jobs))})")
    active = scheduler.active_generation(job_store)
    if active is not None:
        found.append(f"an active pool generation {active['generation']}, which "
                     f"names workers this deployment does not configure")
    live = [one for one in scheduler.allocation_rows(job_store)
            if one["allocation_state"] in ("reserved", "recovery-required")]
    if live:
        found.append(f"{len(live)} live stage allocation(s) "
                     f"({', '.join(sorted(one['worker_id'] for one in live))})")
    offers = outstanding_offers(control_store)
    if offers:
        found.append(f"{len(offers)} live control offer(s) "
                     f"({', '.join(sorted(one['offer_id'] for one in offers))})")
    return found


def _refuse_unconfigured(found, when):
    _refuse(f"this deployment configures no execution capacity and this "
            f"instance holds work it could not serve, so it refuses {when} "
            f"rather than reporting an idle stack: {'; '.join(found)}. Nothing "
            f"was expired, abandoned, repaired or executed -- configure the "
            f"workers this work needs, or point this instance at its own "
            f"stores.", category="refused", code="precondition")


def _serves_nothing(given):
    """Has this deployment no configured execution capacity at all?

    OWNER-FRESH-INSTALL-20260916.md: an installation initializes an instance
    and binds no Job, so it configures no worker either -- a worker is
    configured with the Job it serves. This is the one predicate the
    composition branches on, so "empty" means the same thing everywhere.
    """
    return not given["workers"] and not given["job_bindings"]


def _binds_nothing(document):
    """Is this the instance-only form -- a /2 document binding no Job?

    THE EMPTY LIST IS SAID, NOT INFERRED FROM ABSENCE. A `/2` document that
    omits `job_bindings` has always been refused for omitting them, and that
    refusal is the right answer to a deployment that meant to name some; an
    instance that binds nothing says so.
    """
    return (type(document) is dict
            and document.get("schema") == MULTI_CONFIG_SCHEMA
            and document.get("job_bindings") == [])
_WORKER_MEMBERS = ("worker_id", "role", "deployment")
# W119405: WHAT ONE JOB BINDS, and it is closed.
#
# The one-Job document says these things once, globally. A deployment serving
# several Jobs says them per Job, because a source, a declared base, a Work, a
# line and an integration target are facts ABOUT A JOB rather than about a
# deployment -- which is exactly why the one-Job composition could not carry a
# second one.
#
# `source_worker_id` NAMES A CONFIGURED WORKER RATHER THAN A SOURCE DOCUMENT.
# The nomination that worker carries is already held by `single_worker`'s own
# validator, so binding by identity reuses that proof instead of keeping a
# second copy of those rules here -- and an identity is not a list position,
# which is the thing this cut may not use as a binding.
_BINDING_MEMBERS = ("job_id", "job_work_id", "review_work_id",
                    "line_declared_base", "canonical_target_id",
                    "source_worker_id")
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


def _document(value, what, members, optional=()):
    """Exactly these members, and the few a variant may add.

    W119405: `optional` is how the multi-Job variant carries `job_bindings`
    without the one-Job document growing a member. Absence is still absence and
    an unknown member is still refused; what an optional name buys is a
    document that can be REFUSED FOR ITS OWN REASON -- a `/1` deployment
    carrying bindings is told that it binds one Job through its own members,
    rather than being told it has an unknown field.
    """
    if type(value) is not dict:
        _refuse(f"{what} is one object")
    held = sorted(one for one in value if one not in optional)
    if held != sorted(members):
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
    """This distribution's own working tree -- or, FROZEN, the bundle itself.

    W183883, OWNER-PYINSTALLER-20260916.md. In a one-folder bundle there is no
    working tree: `__file__` sits inside the bundle's own directory, so walking
    three parents up answered the INSTANCE DESTINATION and refused that
    destination's own `db/` for being "inside the checkout". The rule this
    serves is that mutable deployment state must never be written into the
    CODE'S OWN TREE -- and frozen, that tree is the bundle. So the bundle is
    what is answered, which keeps the rule exactly as strong: a store inside
    `distro/` is still refused, and the destination beside it is not.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # THE WHOLE DISTRO, not just `_MEIPASS`. W183883 review [K4]: for a
        # one-folder build `_MEIPASS` is `<distro>/_internal`, so answering it
        # protected the libraries and left `<distro>/` itself open -- a store
        # written beside the executable passed. The folder that holds the code
        # is the folder the code must not be asked to write into, and the
        # instance's own mutable siblings are OUTSIDE it.
        return os.path.dirname(os.path.realpath(sys._MEIPASS))
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
    binds_nothing = _binds_nothing(document)
    given = dict(_document(document, "a stage-execution configuration",
                           _INSTANCE_MEMBERS if binds_nothing else _MEMBERS,
                           optional=_OPTIONAL_MEMBERS))
    if given["schema"] not in CONFIG_SCHEMAS:
        _refuse(f"this deployment reads {' or '.join(CONFIG_SCHEMAS)} and this "
                f"document is {given['schema']!r}")
    # W161230 A.4: THE MANAGED PREPARATION SELECTION, PROVED HERE.
    #
    # Review claim169721 [P1]: I validated it in `_integration_operations`,
    # which runs long after this document was accepted -- so seven malformed
    # values were admitted by preflight and refused only once workers and
    # resources were being composed. `held_configuration`'s own docstring says
    # why that is the wrong moment: the later refusal happens with an Authority
    # open and a workspace group configured, and it describes a different
    # failure than the one the operator actually made.
    _prepares(given)
    _text(given["authority_uuid"], "the configured Authority")
    if not binds_nothing:
        _text(given["job_work_id"], "the implementation Work")
        _text(given["review_work_id"], "the review Work")
        _text(given["canonical_target_id"], "the canonical target")
        _text(given["line_declared_base"], "the line's declared base revision")
    _text(given["checkpoint_profile"], "the checkpoint profile name")
    _text(given["retention_disposition"], "the retention disposition")
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
    if not binds_nothing and given["job_work_id"] != given["review_work_id"]:
        _refuse(f"the implementation stage names Work "
                f"{given['job_work_id']!r} and the review stage names "
                f"{given['review_work_id']!r}; one Job's review is over its "
                f"own implementation", category="refused",
                code="precondition")

    _document(given["integration_profile"], "the integration profile",
              _PROFILE_MEMBERS)
    given["workers"] = _held_workers(
        given["workers"], here, given["authority_uuid"],
        many=given["schema"] == MULTI_CONFIG_SCHEMA,
        empty_ok=binds_nothing)
    given["job_bindings"] = _held_bindings(given)
    given["result_judgment_workers"] = _held_judgments(given, here)
    return given


def _held_judgments(given, checkout):
    """Every configured derived-result judgment execution, held before use.

    W103068. WHAT THIS PROVES, and each one is a fault a later moment would
    describe from the wrong place: the member is a mapping keyed by a Job this
    deployment actually binds; each Job names EXACTLY the three judgment kinds,
    because two of three judgments is not an authorization; each value carries a
    worker id and a complete deployment, held by `single_worker`'s own validator
    rather than by a second copy of its rules here; each deployment launches the
    accepted review role; each participant IS the `receipt_participants` member
    of its own kind, so an execution cannot be configured for somebody who is not
    that judgment's owner; no judgment identity collides with a stage worker or
    with another judgment; and every judgment path lies outside the checkout,
    exactly as a stage worker's must.

    ABSENT IS AN ANSWER. A deployment that never reconciles needs no consumer,
    and every accepted document in this tree predates this member.
    """
    configured = given.get("result_judgment_workers")
    if configured is None:
        return None
    if type(configured) is not dict or not configured:
        _refuse("result_judgment_workers is a non-empty mapping from a bound "
                "Job id to that Job's three configured judgment executions")
    bound = {one["job_id"] for one in given["job_bindings"]}
    unknown = sorted(one for one in configured if one not in bound)
    if unknown:
        _refuse(f"result_judgment_workers names Jobs {unknown} that this "
                f"deployment binds nothing for; a derived result belongs to one "
                f"Job's line and target", category="refused",
                code="precondition")
    identities = {one["worker_id"] for one in given["workers"]}
    judges = dict(given["receipt_participants"])
    if sorted(_JUDGMENT_KINDS) != sorted(_RECEIPT_MEMBERS):
        _refuse(f"this build reads judgment kinds {_JUDGMENT_KINDS} and receipt "
                f"participants {_RECEIPT_MEMBERS}; an execution configured for "
                f"a kind nobody records is one nothing can adopt")
    held = {}
    for job_id in sorted(configured, key=lambda one: str(one)):
        entry = _document(configured[job_id],
                          f"Job {job_id!r}'s judgment executions",
                          _JUDGMENT_KINDS)
        held[job_id] = {}
        for kind in _JUDGMENT_KINDS:
            what = f"Job {job_id!r}'s {kind} judgment execution"
            one = _document(entry[kind], what, _JUDGMENT_MEMBERS)
            worker_id = _text(one["worker_id"], f"{what}'s worker id")
            if worker_id in identities:
                _refuse(f"{what} names worker {worker_id!r}, which this "
                        f"deployment already configures; a judgment execution "
                        f"is its own identity and not a stage worker's",
                        category="refused", code="precondition")
            identities.add(worker_id)
            deployment = single_worker._held(one["deployment"],
                                             roles=(JUDGMENT_LAUNCH_ROLE,))
            if deployment["authority_uuid"] != given["authority_uuid"]:
                _refuse(f"{what} names Authority "
                        f"{deployment['authority_uuid']!r} and this deployment "
                        f"is configured for {given['authority_uuid']!r}",
                        category="refused", code="capability")
            if deployment["launch_role"] != JUDGMENT_LAUNCH_ROLE:
                _refuse(f"{what} launches the "
                        f"{deployment['launch_role']!r} role; a judgment reuses "
                        f"the accepted {JUDGMENT_LAUNCH_ROLE!r} launch contract",
                        category="refused", code="precondition")
            # THE EXECUTION AND THE JUDGE ARE ONE FACT. `receipt_participants`
            # already says who records this kind of judgment; an execution
            # configured for anybody else would produce a report this
            # deployment could never turn into that owner's receipt.
            if deployment["participant"] != judges[kind]:
                _refuse(f"{what} executes as {deployment['participant']!r} and "
                        f"this deployment's {kind} judgment belongs to "
                        f"{judges[kind]!r}", category="policy", code="denied")
            if deployment["workspace_storage"] != given["workers"][0]["deployment"]["workspace_storage"]:
                _refuse("judgment workers use the manager's one configured workspace storage",
                        category="refused", code="precondition")
            if deployment["retention_disposition"] != "retain":
                _refuse("judgment reports must be retained for receipt adoption",
                        category="refused", code="precondition")
            for name in ("workspace_storage", "launch_home",
                         "credential_home"):
                _outside(deployment[name], checkout, f"{what}'s {name}")
            held[job_id][kind] = {"worker_id": worker_id,
                                  "deployment": deployment}
    return held


def _held_bindings(given):
    """Every Job's own binding, or the one the one-Job document already is.

    W119405. THE ONE-JOB DOCUMENT IS NOT ASKED FOR A NEW MEMBER. It already
    names a Work, a review Work, a declared base and a canonical target, and
    its single implementation worker already carries the source -- so its
    binding is DERIVED from what it says rather than duplicated beside it, and
    every existing assertion about those members stands untouched. Carrying
    `job_bindings` in a `/1` document is refused, because two places for one
    fact is how they drift.

    THE MULTI-JOB DOCUMENT SAYS THEM PER JOB, and each entry is held here
    before anything durable is set up: one entry per Job, `source_worker_id`
    naming a configured implementation worker, and the implementation and
    review Works equal -- the accepted review-cycle provider keys one line by
    one `(authority, work)` pair and `attach_review` binds the reviewer to the
    writer's own Work, so a review Work that differed could never attach.
    """
    producers = {one["worker_id"] for one in given["workers"]
                 if one["role"] == "implementation"}
    if given["schema"] != MULTI_CONFIG_SCHEMA:
        if "job_bindings" in given:
            _refuse(f"a {CONFIG_SCHEMA} deployment binds one Job through its "
                    f"own members and names no job_bindings; two places for "
                    f"one fact is how they drift")
        return [{"job_id": None, "job_work_id": given["job_work_id"],
                 "review_work_id": given["review_work_id"],
                 "line_declared_base": given["line_declared_base"],
                 "canonical_target_id": given["canonical_target_id"],
                 "source_worker_id": sorted(producers)[0]}]
    bindings = given.get("job_bindings")
    # AN INSTANCE BINDS NOTHING, AND SAYS SO. OWNER-FRESH-INSTALL-20260916.md:
    # a fresh installation has zero Jobs and starts a real idle scheduler over
    # empty stores. `_document` has already refused such a document if it also
    # carried a global Work, base or target, so the two forms cannot be mixed.
    if bindings == []:
        return []
    if type(bindings) is not list or not bindings:
        _refuse(f"a {MULTI_CONFIG_SCHEMA} deployment names its job_bindings as "
                f"a list -- the empty one when it binds no Job at all, and "
                f"otherwise one entry per Job; a Job this deployment cannot "
                f"bind is one it cannot serve")
    held, seen = [], set()
    for one in bindings:
        binding = _document(one, "a configured Job binding", _BINDING_MEMBERS)
        job_id = _text(binding["job_id"], "a bound Job identity")
        if job_id in seen:
            _refuse(f"two bindings are configured for Job {job_id!r}; a Job "
                    f"binds one source, base, Work and target")
        _text(binding["job_work_id"], f"Job {job_id}'s implementation Work")
        _text(binding["review_work_id"], f"Job {job_id}'s review Work")
        _text(binding["line_declared_base"], f"Job {job_id}'s declared base")
        _text(binding["canonical_target_id"], f"Job {job_id}'s target")
        _text(binding["source_worker_id"], f"Job {job_id}'s source worker")
        if binding["source_worker_id"] not in producers:
            _refuse(f"Job {job_id!r} binds its source to worker "
                    f"{binding['source_worker_id']!r}, which this deployment "
                    f"does not configure as an implementation worker",
                    category="refused", code="precondition")
        if binding["job_work_id"] != binding["review_work_id"]:
            _refuse(f"Job {job_id!r} implements {binding['job_work_id']!r} and "
                    f"reviews {binding['review_work_id']!r}; one development "
                    f"line carries one Work, so those stages could never be "
                    f"attached", category="refused", code="precondition")
        seen.add(job_id)
        held.append(binding)
    return held


def _held_workers(workers, checkout, authority_uuid, *, many=False,
                  empty_ok=False):
    """The pool, and every rule that decides whether it could serve.

    W119403 ADDS ONE ADMISSION AND NOTHING ELSE. `many` is the multi-worker
    variant, and the only rule it relaxes is "one worker per role". Every other
    rule below applies to every worker exactly as it did: the Authority
    comparison first, `single_worker`'s own launch validation, the launch-role
    agreement, the outside-the-checkout paths, every role served, and the
    participant/principal independence an honest review depends on.

    AND IT ADDS ONE RULE `/1` GOT FOR FREE. With one worker per role, worker
    identities were unique because roles were; with several, two workers could
    be configured under one identity and the pool would then have two entries
    the scheduler cannot tell apart. So identity uniqueness is stated here.
    """
    if type(workers) is not list:
        _refuse("a stage-execution configuration names its workers as a list")
    if not workers:
        # NO CAPACITY, AND ONLY FOR THE INSTANCE THAT BINDS NOTHING.
        # A deployment that binds a Job and configures nobody to serve it is
        # still refused below, by the every-role-served rule it has always
        # had; `empty_ok` is the instance-only document, which binds no Job.
        if not empty_ok:
            _refuse("a stage-execution configuration names its workers as a "
                    "non-empty list; a deployment that binds a Job and "
                    "configures nobody to serve it could never serve it")
        return []
    held = []
    seen_roles, participants, principals = {}, {}, {}
    identities = set()
    for one in workers:
        worker = _document(one, "a configured worker", _WORKER_MEMBERS)
        _text(worker["worker_id"], "a worker id")
        role = _text(worker["role"], "a worker role")
        if role not in ROLES:
            _refuse(f"{role!r} is not a stage role; this deployment composes "
                    f"{', '.join(ROLES)}")
        # THE ROLE RULE FIRST, so the one-Job variant's refusal is the exact
        # sentence it has always been rather than one about identities.
        if role in seen_roles and not many:
            _refuse(f"two workers are configured for the {role} stage; each "
                    f"stage is served by exactly one")
        if one["worker_id"] in identities:
            _refuse(f"two workers are configured under the identity "
                    f"{one['worker_id']!r}; the pool tells its workers apart "
                    f"by that identity and cannot hold it twice")
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
        identities.add(worker["worker_id"])
        seen_roles.setdefault(role, []).append(worker["worker_id"])
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
    # W119403: EVERY PUBLISHER, AND THERE IS AT LEAST ONE. With one producer
    # that is the single `publisher` session this deployment has always minted;
    # with several it is one per producer participant, because
    # `Authority.publish` takes the PRODUCER's live assignment and a session
    # refuses to act on an assignment naming somebody else. Each is held to
    # exactly the publisher's own verb table.
    publishers = tuple(sorted(one for one in sessions
                              if one == "publisher"
                              or one.startswith(PUBLISHER_PREFIX)))
    if not publishers:
        _refuse("this deployment has no publisher session; publication and "
                "the receipts that accept it are reached with somebody's "
                "candidate already frozen", category="refused",
                code="capability")
    for name in RECEIPT_SESSIONS + publishers:
        session = sessions.get(name)
        if session is None:
            _refuse(f"this deployment has no {name} session; publication and "
                    f"the receipts that accept it are reached with somebody's "
                    f"candidate already frozen", category="refused",
                    code="capability")
        for verb in _SESSION_METHODS["publisher" if name in publishers
                                     else name]:
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
    if _serves_nothing(given):
        # NOTHING TO MINT FOR. A session is an actor's authority to write a
        # receipt in a bound Work's own scope, and this deployment binds none.
        # Minting deployment-scoped ones instead would be granting capability
        # nobody configured -- see `_bound_scope`, which answers None here.
        return None
    participants = dict(given["receipt_participants"])
    participants["integrator"] = \
        given["integration_profile"]["integrator_participant"]
    # W119403: ONE PUBLISHER SESSION PER DISTINCT PRODUCER PARTICIPANT.
    # `Authority.publish` takes the PRODUCER's live assignment as its
    # compare-and-swap operand and a session refuses to act on an assignment
    # naming somebody else -- so a pool with several producers needs several
    # publisher sessions, one for each. Under the one-Job variant this is
    # exactly the single session it has always been.
    producers = sorted({one["deployment"]["participant"]
                        for one in given["workers"]
                        if one["role"] == "implementation"})
    if len(producers) == 1:
        # UNCHANGED UNDER THE ONE-JOB VARIANT, down to the key: `publisher` is
        # the name every existing consumer and control knows this session by.
        participants["publisher"] = producers[0]
    else:
        for who in producers:
            participants[PUBLISHER_PREFIX + who] = who
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

def _bound_scope(authority, given):
    """The one effective scope EVERY bound Work is actually authorized in.

    W119405 review 2026-09-09T18:35Z [P1]: the scope was derived solely from
    the global `job_work_id`, so a second Job's receipts would have been
    written by sessions minted for the FIRST Job's Work. `_write_receipt`
    derives the receipt's scope from the proposal's own Work, so that
    disagreement surfaces with somebody's candidate already frozen.

    EACH BOUND WORK IS AUDITED, and a difference is REFUSED rather than
    widened. Minting one session set per Work is the honest answer to bound
    Works whose grants genuinely differ, and it is a larger cut than this one:
    inventing a grant that reaches both would be the one thing this must never
    do, so the disagreement is named here instead.
    """
    held = {}
    if not given["job_bindings"]:
        # NO BOUND WORK, SO NO SCOPE -- and no receipt session is minted for
        # one. Review 2026-09-16T22-36-58Z: "no bound Work/no capacity means no
        # stage-execution sessions or per-Work grants; do not invent
        # deployment-scoped receipt capability." A scope invented here would be
        # exactly that invention.
        return None
    for binding in given["job_bindings"]:
        work_id = binding["job_work_id"]
        if work_id not in held:
            held[work_id] = _work_scope(authority, work_id)
    if len(set(held.values())) != 1:
        _refuse(f"the bound Works {sorted(held)} are authorized in different "
                f"effective scopes {sorted(set(held.values()))}; receipts are "
                f"authorized in their own Work's scope, and one session set "
                f"cannot act for both without granting more than either Work "
                f"holds", category="policy", code="denied")
    return next(iter(held.values()))


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


def _global(deployment, name, what):
    """A document's own global answer, or a refusal when it binds no Job.

    The `job_id is None` paths below are for stages that carry no Job and for
    legacy doubles without binding readers: both fall back to what the document
    says globally. An INSTANCE-ONLY deployment says none of it, because it binds
    no Job -- so this is a refusal naming that, rather than a KeyError from the
    middle of a serving tick.
    """
    held = deployment.given.get(name)
    if not held:
        _refuse(f"this deployment binds no Job, so it has no {what}; a Work, a "
                f"declared base and a canonical target are configured when a "
                f"Job is, and an instance that binds none serves none",
                category="refused", code="precondition")
    return held


def _bound_id(deployment, stage, job=None):
    """This stage's Job id, or None when the answer is the global one.

    Legacy integration doubles without binding readers and stages carrying no
    Job keep their global answer. Serving and read-only observation both carry
    the binding readers and select the actual Job.
    """
    if not hasattr(deployment, "binding_for"):
        return None
    return (job or {}).get("job_id") or stage.get("job_id")


def _bound(deployment, stage):
    """This stage's integrator, bound Work and bound target.

    Legacy deployment doubles without per-Job readers retain their global
    operands. Both production serving and observation use the binding readers.
    """
    job_id = _bound_id(deployment, stage)
    if job_id is None:
        return (next(one["deployment"] for one in deployment.given["workers"]
                     if one["role"] == "integration"),
                _global(deployment, "job_work_id", "implementation Work"),
                _global(deployment, "canonical_target_id", "canonical target"))
    return (deployment.worker_for(stage)["deployment"],
            deployment.works_for(job_id)[0],
            deployment.target_for(job_id))


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
        held = self._prepared.get(attempt_id) or self._prepare(stage)
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

    def prepare_context(self, worker, stage):
        from baton_v12.worker_manager import provider_context, context_delivery
        if self.role != "implementation":
            _refuse("provider context is implementation only")
        selected = worker.given["provider_context"]
        single_worker._context_preflight(worker.given, self.deployment.control)
        prepared = self._prepared.get(stage["attempt_id"]) or self._prepare(stage)
        provider_context.admit_context_use(self.deployment.control, self.deployment.jobs, worker.port, attempt_id=stage["attempt_id"], writer_id=prepared["writer_id"], profile_digest=selected["profile_digest"])
        storage = context_delivery.configured_context_storage(self.deployment.control)
        context_delivery.materialize_context_use(self.deployment.control, storage, attempt_id=stage["attempt_id"])
        return provider_context.bind_context_invocation(self.deployment.control, self.deployment.jobs, worker.port, attempt_id=stage["attempt_id"], writer_id=prepared["writer_id"], profile_digest=selected["profile_digest"], task_bytes=worker.given["task_bytes"])

    def revalidate_context(self, worker, stage):
        from baton_v12.worker_manager import provider_context
        return provider_context.revalidate_context_start(self.deployment.control, self.deployment.jobs, worker.port, attempt_id=stage["attempt_id"])

    def _prepare(self, stage):
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
        # W119405: THE STAGE RATHER THAN A BARE ATTEMPT, because the line a
        # preparation grants on belongs to the STAGE'S JOB. Reaching one global
        # line from an attempt alone is exactly why a second submitted Job
        # could only ever share the first one's checkout.
        attempt_id = stage["attempt_id"]
        deployment = self.deployment
        control = deployment.control
        generation = deployment.generation_of(attempt_id)
        recovered = self._recovered(attempt_id, generation)
        if recovered is not None:
            self._prepared[attempt_id] = recovered
            return recovered
        line = deployment.line_for(stage["job_id"])
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
        prepared = self._prepared.get(attempt_id) or self._prepare(stage)
        if self.role == "implementation":
            answered = review_driver.end_implementation(
                deployment.control, worker.port, context["adapter"],
                deployment.publication_for(assignment["participant"]),
                attempt_id=attempt_id,
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
        from baton_v12.worker_manager import provider_context, context_delivery
        binding = provider_context.context_invocation_of(deployment.control, attempt_id)
        if self.role == "implementation" and (worker.given.get("provider_context") is not None or binding is not None):
            if answered.get("outcome") == "held" or answered.get("cleaned_up") is False:
                return answered
            if binding is None:
                return dict(answered, outcome="held", reason="provider-context-binding-missing")
            if context["disposition"] != "completed":
                provider_context.hold_context_use(deployment.control, attempt_id=attempt_id, reason="invocation-unknown", evidence_refs=[])
                return dict(answered, outcome="held", reason="provider-context-unknown")
            def checkpoint_reader(original, writer_id):
                writer = review_cycles.writer_for_attempt(deployment.control, attempt_id=original, generation=deployment.generation_of(original))
                if writer is None or writer["writer_id"] != writer_id or answered.get("checkpoint_id") is None:
                    _refuse("historical context checkpoint is missing")
                return answered["checkpoint_id"]
            try:
                provider_context.finalize_context_use(deployment.control, deployment.jobs, worker.port, attempt_id=attempt_id, storage=context_delivery.configured_context_storage(deployment.control), receipt_reader=lambda original, artifact: context_delivery.read_context_receipt(deployment.control, attempt_id=original, artifact_id=artifact, workspace_storage=worker.given["workspace_storage"]), checkpoint_reader=checkpoint_reader)
            except ContractRefusal:
                return dict(answered, outcome="held", reason="provider-context-unproved")
        return self._finished(worker, stage, assignment, answered)

    def _source_receipts(self, worker, stage, answered):
        """Issue this Job's own three source receipts, once, at its accepted
        review's ending.

        EVERY SELECTOR IS THE ANSWER'S OR THE ACCEPTED CHECKPOINT'S. The line,
        checkpoint and verdict the real review driver recorded are compared
        with the line's own accepted integration checkpoint, so this can never
        select another Job or a newer unrelated publication. The proposal is
        `published_proposal`'s historical committed publication, which neither
        republishes nor requires the original base to still be canonical.
        """
        if stage.get("kind") != "review" \
                or answered.get("outcome") != "accepted":
            return answered
        deployment = self.deployment
        if not deployment.reconciles() and not _prepares(deployment.given):
            # A deployment that never reconciles keeps its accepted behaviour
            # exactly: the direct path issues these at admission as it always
            # has, and nothing here runs.
            return answered
        job_id = _bound_id(deployment, stage, None)
        line = (deployment.line() if job_id is None
                else deployment.line_for(job_id))
        accepted = review_cycles.integration_checkpoint(deployment.control,
                                                        line["line_id"])
        if accepted is None:
            # REFUSED RATHER THAN SKIPPED. Review 2026-09-10T20:30:00Z: an
            # accepted review whose line holds no accepted integration
            # checkpoint is a state this composition cannot account for, and
            # returning quietly would let the ending settle with the receipts
            # it owes still unwritten.
            _refuse(f"line {line['line_id']!r} ended an accepted review and "
                    f"holds no accepted integration checkpoint",
                    category="refused", code="precondition")
        for member, key in (("line_id", "line_id"),
                            ("checkpoint_id", "checkpoint_id"),
                            ("verdict_id", "verdict_id")):
            said = answered.get(key)
            if said is None:
                _refuse(f"the accepted review answered no {key}; this "
                        f"composition selects a Job's receipts by the "
                        f"identities its own review recorded",
                        category="refused", code="precondition")
            if said != accepted[member]:
                _refuse(f"the accepted review answered {key} {said!r} and this "
                        f"line's accepted integration checkpoint names "
                        f"{accepted[member]!r}",
                        category="refused", code="precondition")

        proposal_id = deployment.published_proposal(accepted)
        # A HISTORICAL RETRY VALIDATES; IT DOES NOT ISSUE AGAIN. Review
        # 2026-09-10T20:30:00Z: this always issued, so an ending re-entered
        # after the policy generation advanced -- which is exactly what the
        # recovery path does -- refused on a pin that was correct when the
        # receipts were actually written. Complete originals are proved
        # against their configured owners and answered as they stand.
        held = {kind: _authority_read(
            f"the source {kind} receipt",
            lambda kind=kind: deployment.authority.receipt(proposal_id, kind))
            for kind in ("verification", "review", "approval")}
        if all(one is not None for one in held.values()):
            configured = deployment.given["receipt_participants"]
            for kind, one in held.items():
                if one["actor"] != configured[kind]:
                    _refuse(f"this line's source {kind} receipt was written by "
                            f"{one['actor']!r} and this deployment configures "
                            f"{configured[kind]!r}",
                            category="refused", code="precondition")
            approval = held["approval"]["policy_generation"]
            if approval != deployment.given["policy_generation"]:
                _refuse(f"this line's source approval binds policy generation "
                        f"{approval!r} and this deployment is configured for "
                        f"{deployment.given['policy_generation']!r}",
                        category="refused", code="precondition")
            # AND THE SUBMISSION IS STILL ELIGIBLE, WITH ITS REQUIRED TESTS
            # ACTUALLY PASSED. Review 2026-09-10T20:36:08Z: returning after the
            # actors and the pin proved only that three receipts exist and who
            # wrote them. `source_submission` re-reads the accepted checkpoint,
            # the writer's assignment and frozen output, the committed proposal
            # and the owning Job; `_ordinary_tests_passed` judges the configured
            # required tests. Neither issues anything, so a historical retry
            # still writes nothing.
            admission.source_submission(
                deployment.control, deployment.jobs, deployment.authority,
                line_id=line["line_id"], proposal_id=proposal_id)
            driver._ordinary_tests_passed(
                driver.ordinary_test_evidence(
                    deployment.control, deployment.authority,
                    line_id=line["line_id"], proposal_id=proposal_id),
                Integration(deployment).required_tests(job_id))
            return answered
        # PARTIAL OR ABSENT, so issuance is attempted -- but ONLY while the
        # configured pin is still current. Otherwise this ending holds rather
        # than writing an approval under a generation nobody configured.
        current = _authority_read(
            "the approval policy generation",
            deployment.authority.policy_generation)
        if current != deployment.given["policy_generation"]:
            _refuse(f"this line's source receipts are incomplete and the "
                    f"Authority has moved to policy generation {current!r} "
                    f"from the configured {deployment.given['policy_generation']!r}; "
                    f"a submission's own receipts are not written under a "
                    f"policy this deployment was never configured for",
                    category="policy", code="denied")
        driver._accepted_receipts(
            deployment.control, deployment.authority,
            deployment.sessions["verification"], deployment.sessions["review"],
            deployment.sessions["approval"],
            line_id=line["line_id"],
            proposal_id=proposal_id,
            policy_generation=deployment.given["policy_generation"],
            required_tests=Integration(deployment).required_tests(job_id),
            issue=True)
        return answered

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
        # W133129: THE SUBMISSION'S OWN THREE RECEIPTS ARE ISSUED WHERE ITS
        # REVIEW IS ACCEPTED, and reviewer138861's guidance is why the hook is
        # here rather than at the integration stage.
        #
        # `driver._accepted_receipts` compares the deployment's configured
        # policy pin against the Authority's CURRENT generation before it
        # issues anything -- correctly, because the pin is what this
        # deployment was configured to approve under. But the FIRST Job's
        # integration calls `set_policy("canonical_target")`, which bumps that
        # generation, so a second Job whose receipts were still unwritten
        # could never issue them: it arrived one generation stale through no
        # fault of its own. Substituting the current generation would defeat
        # the check, and relaxing it is Authority scope.
        #
        # A SUBMISSION'S RECEIPTS BELONG TO ITS OWN ACCEPTED REVIEW, not to
        # whatever the target's policy has done since. Issued here, each Job
        # gets its own three while the pin it was configured with is still
        # current -- no all-Jobs barrier, no other Job's work performed, and
        # nothing issued for a held or correction outcome. A failure stops
        # before the route moves, the gate clears or the ending settles, so
        # the registered ending obligation is retained and the historical
        # recovery path re-enters exactly as it always did.
        self._source_receipts(worker, stage, answered)
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


# -- W133129: the reconciled import's own configured owners -----------------


def _materialize(runner, repository, revision, into):
    """One revision's content on disk, so a configured test can actually run.

    `git archive` and nothing else: no checkout, no index, no working tree in
    the repository being read. The same primitive W133117's own causal witness
    uses, composed here because the argv a deployment configures runs against
    FILES rather than against an object name.
    """
    import os as _os
    import tarfile

    archive = _os.path.join(into, "content.tar")
    answered = runner(("git", "-C", repository, "archive", "--format=tar",
                       "-o", archive, revision))
    if answered["returncode"] != 0:
        _refuse(f"the configured Git runner could not archive {revision!r}: "
                f"{answered['stderr'].strip()[:240]}",
                category="refused", code="precondition")
    with tarfile.open(archive) as held:
        held.extractall(into, filter="data")
    _os.remove(archive)
    return into


# W156162. WHAT THE HOST FAILURE PATH DOES, AND THE ONE THING IT STILL DOES
# NOT. This explanation is rewritten as a whole because its first form said the
# contract was missing, proposed a `status: null` variant and called the two
# owners out of scope -- and every one of those statements has been overtaken.
# Adding a paragraph under them left a live explanation that contradicted
# itself, which review 2026-09-13T12:12:03Z named.
#
# THE CONTRACT EXISTS AND BOTH OWNERS CARRY IT. Owner ruling M157653 approved
# the tagged closed answer: `reconciliation` admits a
# `baton.v12.host-verification-failure/1` observation naming the phase, the
# closed reason -- `timeout` or `start-failed` -- the bound actually applied,
# the command, the pinned harness and the content it ran against, validates it
# against the configured owner's own expectations, settles the result BLOCKED
# and never authorizes it; `execution` adopts the post-import form of the same
# answer and holds the TARGET through the queue. No exit status is invented
# anywhere, and neither owner needs one to record what happened.
#
# SO THE OUTCOME IS DURABLE, and that is what makes a reopen quiet: a reopened
# deployment reads the blocked result or the held target and runs nothing. The
# in-process retention below is an ADDITIONAL cache. What it is for is the
# measured twelve-runs-in-four-ticks repeat WITHIN one composition, where the
# owners are rebuilt every tick and no durable record has been written yet.
#
# WHAT IS STILL MISSING is narrower than durability, and it is two halves of
# one gap. No owner records the ATTEMPT ITSELF, so a process that dies between
# the command's failure and its owner's record leaves nothing to read and the
# next composition tries once more -- crash-before-record, not an exactly-once
# guarantee. And a host failure leaves no owner-validated TERMINAL account for
# the stage: the reconciled branch answers `held` with no runtime, the
# scheduler settles capacity from episode endings and completions rather than
# from anything here, so the stage stays exceptional and the capacity it holds
# is never settled. Both are written down for disposition rather than worked
# around; neither is changed by this Work.
HOST_OBSERVATION_CONTRACT = (
    "an owner-recorded account of a host verification ATTEMPT that ended "
    "before reaching its owner, and the terminal settlement of the stage and "
    "capacity such a failure leaves behind")


def _host_retention(deployment):
    """The deployment's own memory of host observations that could not be made.

    NOT WHAT MAKES THE OUTCOME DURABLE -- the owners do that, and the comment
    above says how. This is composed lazily on the deployment because the
    owners are built fresh every tick, and what it prevents is the repeat
    inside one composition, before and between the owner records.
    """
    held = getattr(deployment, "_host_observation_failures", None)
    if held is None:
        held = {}
        setattr(deployment, "_host_observation_failures", held)
    return held


def _host_scratch(deployment):
    """The paths a failed host observation could NOT dispose of.

    W156162, step 5 of the accepted host-failure proposal, and review
    2026-09-13T11:08:02Z is what says the earlier form did not discharge it.
    `_no_status` attempts the removal and, when the tree is still there, names
    it in the retained diagnostic -- so it was REPORTED and still owned by
    nobody. A deployment released its workers, its integration store and its
    Authority and walked past the bytes.

    THE REGISTRY IS THE DEPLOYMENT'S, for the same reason the retention is:
    these owners are composed fresh every tick, so a per-instance list would
    forget the moment the tick ended. What is held is the path AND the
    diagnosis that named it, because the release below has to be able to say
    what the surviving tree was.
    """
    held = getattr(deployment, "_host_surviving_scratch", None)
    if held is None:
        held = {}
        setattr(deployment, "_host_surviving_scratch", held)
    return held


def _dispose_surviving(surviving):
    """Try again to remove what a failed observation left, and report it.

    RETURNS THE PATHS THAT ARE STILL THERE. Removing a path that has since
    gone is not an error; a path that survives this attempt too is named to
    the caller rather than dropped, which is the whole point of the registry.
    A path is forgotten only once it is actually gone, so nothing accumulates
    and nothing is silently abandoned.
    """
    import shutil

    left = []
    for where in sorted(surviving):
        shutil.rmtree(where, ignore_errors=True)
        if os.path.exists(where):
            left.append(where)
        else:
            surviving.pop(where, None)
    return left


def _host_seconds(deployment, stage):
    """This stage's Job's host-verification ceiling, or the boundary default.

    W156162. Asked of the JOB OWNER, which is what resolves a Job's admitted
    settings under the generation it was admitted under; this assembly holds no
    table of its own. A stage with no Job -- the one-binding deployments whose
    stages carry a name nothing bound -- gets the boundary's own default, which
    is the number this line already ran under.
    """
    from baton_v12.job_manager import submission as job_submission

    job_id = stage.get("job_id") if type(stage) is dict else None
    if job_id is None or getattr(deployment, "jobs", None) is None:
        return execution_limits.boundary_default("host_verification")
    return job_submission.boundary_seconds(deployment.jobs, job_id,
                                           "host_verification")


class _ConfiguredExecution:
    """What both reconciled owners do: run THE DEPLOYMENT'S OWN required test.

    Neither owner invents a command. `Integration.required_tests` derives the
    argv from the configured implementation task and its bound input manifest --
    W103083's derivation, which the direct path already admits behind -- and
    these run exactly that against content materialized from a real repository.
    """

    def __init__(self, participant, argv, runner, root, *, seconds=None,
                 retention=None, scope=None, surviving=None):
        self.participant = participant
        self._argv = list(argv)
        self._runner = runner
        self._root = root
        # W156162: THE JOB'S `host_verification` CEILING, and the reason it is
        # not `GIT_SECONDS`. These owners do two different things with a clock:
        # `_materialize` asks GIT for content, which is this deployment's own
        # tooling over its own repository, and then CANDIDATE CODE RUNS. Only
        # the second is a Job's to bound, and binding them to one number would
        # mean a Job that shortened its own tests had also shortened this
        # deployment's archive. The default is the boundary's own, which is the
        # same 300 this line has always used.
        self._seconds = (execution_limits.boundary_default("host_verification")
                         if seconds is None else seconds)
        # WHERE A FAILED OBSERVATION IS REMEMBERED. These owners are composed
        # fresh on every tick, so the retention belongs to the DEPLOYMENT and is
        # handed in; a per-instance memo would forget between ticks, which is
        # precisely the repeat this exists to stop.
        self._retention = {} if retention is None else retention
        # AND WHERE A TREE THAT COULD NOT BE REMOVED IS HANDED ON. Same
        # ownership as the retention and for the same reason: see
        # `_host_scratch`. A composition given none keeps its own, which is a
        # standalone owner whose caller holds it.
        self._surviving = {} if surviving is None else surviving
        # AND WHOSE WORK THIS IS. A retention shared by a deployment must not
        # let one result's failure speak for another's, so the owning scope --
        # the Job, the result and the phase this owner was composed for -- is
        # part of every key. `None` is a composition with no owning scope, and
        # it keys under that rather than under somebody else's.
        self._scope = scope
        # THE HARNESS THIS OWNER LAST READ, pinned at the content boundary. See
        # `expectations`: `None` until a run has read one.
        self._pinned = None

    def _failure_key(self, revision, adding):
        """WHAT MAKES ONE RETAINED FAILURE THE SAME WORK AS ANOTHER.

        Review 2026-09-13T04:31:29Z [P1]: the first key was
        `(argv, revision, seconds)`, and the causal owner runs the SAME command
        at the SAME revision with a DIFFERENT harness -- that is what `adding`
        is for, and `harness_added` is the observation member that exists to
        keep it honest. So a memo from one harness refused another harness's
        run without ever attempting it.
        
        EVERY VARYING OPERAND IS IN THE KEY NOW: the owning scope this observer
        was composed for -- its Job, its result and which phase it is -- the
        command, the revision, the bound, and a digest of the harness content
        that would be added. Two runs that differ in any of those are different
        work and neither speaks for the other.
        """
        import hashlib

        harness = "" if adding is None else hashlib.sha256(
            adding.encode("utf-8")).hexdigest()
        return (self._scope, tuple(self._argv), revision, self._seconds,
                harness)

    def _retain(self, revision, adding, message):
        """Record why this command cannot be observed, and refuse with it."""
        self._retention[self._failure_key(revision, adding)] = message
        _refuse(message, category="refused", code="precondition")

    def _no_status(self, where, body, added, revision, adding, *, reason,
                   detail):
        """The closed failure answer, and the scratch that is DISPOSED OF.

        W156162, owner ruling M157653 steps 1 and 5. The answer is the owner's
        own closed shape, so every diagnostic this run can honestly supply is
        IN it: the phase, the reason, the bound actually applied, the command,
        the pinned harness and its digest, and the content it ran against.

        THE TEMPORARY TREE GOES WITH IT. Once the diagnostic is in the answer
        nothing needs those bytes, and leaving them meant a failed run owned a
        path with no lifecycle -- which repeated polls did not add to, and
        which nothing ever removed. The successful branch's tree is untouched:
        its caller still reads `where`.
        """
        import hashlib
        import shutil

        self._retention[self._failure_key(revision, adding)] = detail
        # AND A DISPOSAL THAT FAILS SAYS SO. Review 2026-09-13T09:34:47Z:
        # `ignore_errors=True` alone would report a clean disposal for a tree
        # that is still there, which is the same class of silence this Work
        # keeps refusing. What remains is named in the retained diagnostic; it
        # is not raised, because the FAILURE is the fact being reported and
        # losing it to a cleanup problem would be worse.
        shutil.rmtree(where, ignore_errors=True)
        if os.path.exists(where):
            detail = (f"{detail}. Its temporary materialization at {where!r} "
                      f"could not be disposed of and remains")
            self._retention[self._failure_key(revision, adding)] = detail
            # AND IT IS HANDED TO THE RUNTIME THAT OWNS IT. Naming a surviving
            # tree in a diagnostic tells an operator it is there and leaves
            # nobody responsible for it; the deployment releases it with its
            # other handles. The diagnosis is unchanged either way -- it is
            # what this answer reports, and a later cleanup does not edit it.
            self._surviving[where] = detail
        return reconciliation.failed_observation(
            phase=self._phase(), reason=reason, detail=detail,
            seconds=self._seconds, command=list(self._argv),
            # THE HARNESS THIS OWNER PINNED. The base class does not name one --
            # its two subclasses do -- and a composition without one says so
            # rather than inventing an identity it was never given.
            test_identity=getattr(self, "_identity", None) or "unidentified",
            test_digest="sha256:" + hashlib.sha256(
                body.encode("utf-8")).hexdigest(),
            environment="configured-required-test",
            execution=self.participant, input_commit=revision,
            input_tree=revision, completed={}, not_run=[])

    @property
    def expectations(self):
        """WHAT THIS OWNER WAS CONFIGURED WITH, published for its owner to ask.

        W156162, review 2026-09-13T09:48:11Z [P1]. A failure answer cannot
        vouch for its own command, task or bound -- a probe changed only the
        seconds and both host custodies took it. These are the deployment's own
        operands, held on this object before anything ran, and the integration
        owner compares the answer against them rather than against itself.

        AND THE HARNESS DIGEST IS HERE TOO, pinned per RESULT AND PHASE rather
        than per configuration. `_run` reads the harness at the content
        boundary before it starts anything and holds that digest; publishing it
        is what lets the integration owner compare the answer's digest against
        a value the answer did not supply. It is never a stale global: it is
        whatever this owner last read, which is the phase the failure is about.
        """
        held = {"command": list(self._argv),
                "test_identity": getattr(self, "_identity", None)
                or "unidentified",
                "seconds": self._seconds}
        pinned = getattr(self, "_pinned", None)
        if pinned is not None:
            held["test_digest"] = pinned
        return held

    def _phase(self):
        """Which host boundary this owner is; its subclasses say."""
        return (self._scope or (None, None, None))[2]

    def _run(self, repository, revision, *, adding=None):
        import hashlib
        import os as _os
        import subprocess
        import tempfile

        # THE RETAINED FAILURE IS CHECKED FIRST, BEFORE ANYTHING IS
        # MATERIALIZED. Review 2026-09-13T04:31:29Z [P2]: the first form
        # checked after `mkdtemp` and `_materialize`, so three memo hits made
        # three scratch trees for one child that never ran. A run this
        # composition already knows it cannot observe costs nothing now.
        held_failure = self._retention.get(self._failure_key(revision, adding))
        if held_failure is not None:
            _refuse(held_failure, category="refused", code="precondition")
        where = tempfile.mkdtemp(dir=self._root)
        _materialize(self._runner, repository, revision, where)
        named = self._argv[-1]
        added = False
        if adding is not None and not _os.path.exists(_os.path.join(where,
                                                                    named)):
            # THE HARNESS THE BASE NEVER CARRIED. W133117 section 4's rule:
            # pin ONE harness and run that same harness against all three
            # content states, rather than pretending a test absent from the
            # base ever ran there. `harness_added` is what keeps the base
            # observation honest about it.
            with open(_os.path.join(where, named), "w") as handle:
                handle.write(adding)
            added = True
        try:
            with open(_os.path.join(where, named)) as handle:
                body = handle.read()
            # W156162, review 2026-09-13T09:56:51Z [P1]: THE HARNESS IS PINNED
            # HERE, at the content-read boundary and BEFORE the subprocess.
            #
            # I had argued this owner could not publish a digest because it
            # does not know one until it reads the content. That is true of a
            # CONFIGURATION-time digest and it does not waive the per-result
            # binding: the harness for THIS phase is in hand at exactly this
            # line, and holding it here is what lets the integration owner
            # compare the answer against something the answer did not supply.
            # A probe that changed only `test_digest` was otherwise retained
            # durably.
            self._pinned = "sha256:" + hashlib.sha256(
                body.encode("utf-8")).hexdigest()
        except OSError:
            _refuse(f"the configured required test {named!r} is not in the "
                    f"content at {revision!r}",
                    category="refused", code="precondition")
        # W156162: A COMMAND THAT OUTLASTS ITS CEILING, and this is the second
        # form of the handling. Review 2026-09-13T04:18:41Z [P1]: the first one
        # answered `status: None`, and `reconciliation._observation` REQUIRES an
        # actual integer exit status -- it refuses the document before retaining
        # anything -- so every ordinary tick re-ran the timed-out command and
        # the public cause was a schema diagnostic instead of the timeout. The
        # measured shape was three host commands per tick, twelve over four,
        # forever.
        #
        # SO NOTHING IS FABRICATED AND NOTHING IS REPEATED. A child that
        # supplied no exit status does not get one invented for it; the refusal
        # carries the bound and the actual reason, and it is RETAINED so a later
        # tick re-refuses from the record rather than running the command again.
        #
        # AND THE DURABLE PART IS THE OWNER'S, not this cache's. The failure
        # this branch answers with is settled by the result owner -- blocked --
        # or held on the target by the queue, and that is what a reopened
        # deployment reads. This retention only stops the repeat inside one
        # composition. What no owner has is a record of an ATTEMPT that ended
        # before reaching it, or a terminal account for the stage such a
        # failure leaves behind; both are `HOST_OBSERVATION_CONTRACT`, written
        # down for disposition.
        try:
            answered = subprocess.run(self._argv, cwd=where,
                                      capture_output=True, text=True,
                                      timeout=self._seconds)
        except subprocess.TimeoutExpired:
            return self._no_status(
                where, body, added, revision, adding, reason="timeout",
                detail=f"the configured required test {named!r} did not "
                       f"finish within this Job's {self._seconds}s "
                       f"host_verification ceiling at {revision!r}; no exit "
                       f"status was observed and none is invented")
        except OSError as failed:
            return self._no_status(
                where, body, added, revision, adding, reason="start-failed",
                detail=f"the configured required test {named!r} could not be "
                       f"started at {revision!r} ({type(failed).__name__}); no "
                       f"exit status was observed and none is invented")
        tail = answered.stderr.strip().splitlines()[-1:]
        # W133129, measured at step55: the causal owner refused every tick with
        # "the base causal observation names the command that produced it"
        # because this handed it the JOINED text. `reconciliation._observation`
        # requires a non-empty LIST of command words and
        # `execution._owned_post_import` requires TEXT -- two accepted contracts
        # that type this member differently. Both are answered here and each
        # owner below is given the shape its own contract names; nothing
        # reformats a contract to suit the other.
        return {"command": " ".join(self._argv), "argv": list(self._argv),
                "test_digest": "sha256:" + hashlib.sha256(
                    body.encode("utf-8")).hexdigest(),
                "status": answered.returncode,
                "output": answered.stdout.strip() or (tail[0] if tail else ""),
                "harness_added": added, "body": body, "where": where}


class _CausalObserver(_ConfiguredExecution):
    """The configured owner that RUNS the harness against all three states.

    IT IS ASKED AND IT ANSWERS, and what it answers is what actually happened:
    the required test really runs against the target snapshot the result was
    prepared onto, against the producer's own untouched candidate, and against
    the combined content -- three real exit statuses. This assembly does not
    decide what they mean; `record_causal_observations` retains them either
    way, and a failing combination settles `blocked` and can never be
    authorized.
    """

    def __init__(self, participant, argv, runner, root, *, workspace,
                 line_root, base, candidate, identity, seconds=None,
                 retention=None, scope=None, surviving=None):
        super().__init__(participant, argv, runner, root, seconds=seconds,
                         retention=retention, scope=scope,
                         surviving=surviving)
        self._workspace = workspace
        # BOTH SOURCE OBSERVATIONS COME OUT OF THE PRODUCER'S OWN LINE, and
        # review 2026-09-10T15:07:43Z is why that is stated rather than
        # assumed. The base this harness must run against is the SUBMISSION's
        # immutable declared base -- `reconciliation._causal` compares it to
        # `source_base` and refuses anything else -- not the advanced snapshot
        # the result was reconciled ONTO. The line holds both objects: it was
        # created at that base and its checkpoint is the candidate. Reading
        # the base from the dedicated target would name A's revision and
        # refuse for every drifted result there has ever been.
        self._line_root = line_root
        self._base = base
        self._candidate = candidate
        self._identity = identity
        self.asked = []

    def _tree(self, repository, revision):
        """The tree this revision names, asked of Git rather than assumed."""
        answered = self._runner(("git", "-C", repository, "rev-parse",
                                 revision + "^{tree}"))
        if answered["returncode"] != 0:
            _refuse(f"the configured Git runner could not read the tree of "
                    f"{revision!r}", category="refused", code="precondition")
        return answered["stdout"].strip()

    def _observation(self, repository, revision, *, adding=None):
        answered = self._run(repository, revision, adding=adding)
        # THE FAILURE ANSWER TRAVELS AS ITSELF. It carries no exit status, so
        # there is no observation to compose from it and nothing here invents
        # one; `observe` completes its prefix and remainder.
        #
        # ITS TREE IS READ HERE, AND THAT IS A CORRECTION. Review
        # 2026-09-13T09:34:47Z [P1]: `_run` knows only the revision, so the
        # first form recorded `input_tree` as the COMMIT -- which is not the
        # tree, and for the combined phase is not `prepared.tree` either. The
        # owner that can ask Git is this one, so it asks before the answer
        # leaves.
        if reconciliation.is_failed_observation(answered):
            return dict(answered,
                        input_tree=self._tree(repository, revision))
        tree = self._runner(("git", "-C", repository, "rev-parse",
                             revision + "^{tree}"))
        if tree["returncode"] != 0:
            _refuse(f"the configured Git runner could not read the tree of "
                    f"{revision!r}", category="refused", code="precondition")
        return answered["body"], {
            # THE CAUSAL OWNER'S OWN SHAPE: the command WORDS, not the line.
            "command": answered["argv"],
            "test_identity": self._identity,
            "input_commit": revision,
            "input_tree": tree["stdout"].strip(),
            "test_digest": answered["test_digest"],
            "environment": "configured-required-test",
            "status": answered["status"], "output": answered["output"],
            "execution": self.participant,
            "harness_added": answered["harness_added"]}

    def observe(self, basis):
        """THE COMBINED STATE IS OBSERVED FIRST, and that ordering is the
        harness rule rather than a convenience. The base predates the test the
        producer brought with its fix, so the ONE harness pinned and run
        against all three states is the combined content's own -- read here and
        carried into the base run, which then says `harness_added` about
        itself."""
        self.asked.append(dict(basis))
        # W156162, owner ruling M157653 step 2: THE COMPLETED PREFIX IS CARRIED
        # AND THE REMAINDER IS NOT INVENTED. The three phases run in this
        # order, so a failure in one has exactly the phases before it as its
        # completed prefix and exactly the phases after it as not run. Each is
        # collected as it finishes rather than reconstructed afterwards.
        completed, order = {}, list(reconciliation.CAUSAL_PHASES)
        harness = None
        for phase in order:
            if phase == "combined":
                answered = self._observation(self._workspace,
                                             basis["candidate"])
            elif phase == "base":
                answered = self._observation(self._line_root, self._base,
                                             adding=harness)
            else:
                answered = self._observation(self._line_root, self._candidate)
            if reconciliation.is_failed_observation(answered):
                where = order.index(phase)
                return {"result_id": basis["result_id"],
                        "content_digest": basis["content_digest"],
                        "candidate": basis["candidate"],
                        "tree": basis["tree"], "target": basis["target"],
                        "execution": self.participant,
                        "observations": dict(
                            answered, phase=phase, completed=dict(completed),
                            not_run=list(order[where + 1:]))}
            body, one = answered
            if phase == "combined":
                harness = body
            completed[phase] = one
        base, isolated = completed["base"], completed["isolated"]
        combined = completed["combined"]
        return {"result_id": basis["result_id"],
                "content_digest": basis["content_digest"],
                "candidate": basis["candidate"], "tree": basis["tree"],
                "target": basis["target"], "execution": self.participant,
                "observations": {"base": base, "isolated": isolated,
                                 "combined": combined}}


class _ImportedVerifier(_ConfiguredExecution):
    """The configured post-import owner W133120's importer requires.

    IT RUNS THE DEPLOYMENT'S OWN REQUIRED TEST AGAINST THE IMPORTED COMMIT,
    read out of the dedicated target repository itself, and answers the closed
    document `execution.POST_IMPORT_MEMBERS` names. Q holds the ordering: this
    runs before the reference CAS and a non-zero status holds the target.
    """

    def __init__(self, participant, argv, runner, root, *, identity,
                 seconds=None, retention=None, scope=None, surviving=None):
        super().__init__(participant, argv, runner, root, seconds=seconds,
                         retention=retention, scope=scope,
                         surviving=surviving)
        self._identity = identity
        self.asked = []

    def verify_imported(self, basis):
        self.asked.append(dict(basis))
        answered = self._run(basis["target_root"], basis["input_commit"])
        # W156162, step 3: ONE COMMAND, SO NO PREFIX AND NO REMAINDER. The
        # bindings are the imported content's, which is what this owner ran
        # against.
        if reconciliation.is_failed_observation(answered):
            return dict(answered, input_commit=basis["input_commit"],
                        input_tree=basis["input_tree"])
        return {"command": answered["command"],
                "test_identity": self._identity,
                "input_commit": basis["input_commit"],
                "input_tree": basis["input_tree"],
                "test_digest": answered["test_digest"],
                "environment": "configured-required-test",
                "status": answered["status"], "output": answered["output"],
                "execution": self.participant}


class Integration:
    """The accepted serialized integration, driven from the Job's own stage.

    EVERY OPERAND IS RE-READ FROM DURABLE STATE, which is what makes this
    re-enterable rather than a handoff from the tick that accepted the review.
    The line answers which checkpoint was accepted; the checkpoint names its
    writer; the writer names the attempt whose proposal was published; and
    `retain_proposal` replays that attempt's retained manifest, out of which
    the published proposal's own identity is read. Nothing is carried in a
    variable across a tick, and nothing is carried across a restart.

    THE DRIVER OWNS THE INTEGRATION OUTCOME. `admit_accepted` writes the accepted
    receipts, admits the candidate, leases it and drives or adopts one
    serialized integration; an interrupted one comes back `held` and stays
    held, which is the operator's to look at. This deployment then proves the
    committed receipt, released lease and worker exclusion before passing the
    integrator's own fixed assignment to its configured outgoing route.
    """

    def __init__(self, deployment, ports=None):
        self.deployment = deployment
        # W130224: ONE PORT PER BOUND JOB, keyed by the Job's own id. See
        # `_integration_ports`. A BARE PORT IS STILL THE ONE-JOB SPELLING and
        # is the shape every accepted caller of this constructor hands it:
        # `/1` binds one Job and answers for every Job it is asked about, so
        # one port under that binding's own absent key is exactly what it has
        # always been.
        self.ports = ports if type(ports) is dict else {None: ports}

    @property
    def port(self):
        """The one-Job spelling, kept for the accepted one-binding callers."""
        held = sorted(self.ports)
        if len(held) != 1:
            _refuse(f"this deployment binds {len(held)} Jobs and an "
                    f"integration runtime port is composed over ONE accepted "
                    f"line, proposal and canonical target; the port belongs "
                    f"to a Job and its Job is named",
                    category="refused", code="precondition")
        return self.ports[held[0]]

    def port_for(self, stage, job=None):
        """The runtime port this stage's own Job's integration is started by.

        W130224. `IntegrationRuntimePort` is constructed over one accepted
        `line_id`, one `proposal_id` and one `canonical_target_id`, and all
        three are facts about a Job. A deployment that ran a second Job's
        integration through the first Job's port would materialize the first
        Job's line against the first Job's target under this Job's assignment
        -- a cross-wire reached with a candidate already published, and one
        the port itself cannot detect because it was told about it.
        """
        # THE ONE-JOB DOCUMENT ANSWERS FOR EVERY JOB IT IS ASKED ABOUT, which
        # is exactly what `StageDeployment.binding_for` does with the binding
        # this key comes from: `/1` names one Work, one base and one target
        # and was written for the one Job that submits against them, so the
        # Job id on its stages is a name this deployment never bound and never
        # needed to. A port keyed under a REAL Job id is selected by that id.
        if len(self.ports) == 1 and None in self.ports:
            return self.ports[None]
        job_id = _bound_id(self.deployment, stage, job)
        if job_id not in self.ports:
            _refuse(f"stage {stage.get('stage_id')!r} names Job {job_id!r} and "
                    f"this deployment composes integration runtime ports for "
                    f"{sorted(one for one in self.ports)}; a port is bound to "
                    f"one Job's accepted line, proposal and target",
                    category="refused", code="precondition")
        return self.ports[job_id]

    def _constructed(self, stage, job, *, line_id, proposal_id,
                     canonical_target_id):
        """This Job's own constructed port, built once and kept.

        THE MEMO IS PER JOB AND IT IS THE CAPACITY RULE, not a cache for speed.
        `IntegrationRuntimePort` resolves a bundle home, a launch home and a
        credential home, and one Job's integration is one capacity; a second
        port for the same Job would be a second set of those homes for one
        serialized integration. A port already SUPPLIED for a Job is never
        replaced -- an operator's injected capability stays the one in use.
        """
        job_id = _bound_id(self.deployment, stage, job)
        held = self.ports.get(job_id)
        if held is not None:
            return held
        built = self.deployment.integration_port_for(
            job_id, line_id=line_id, proposal_id=proposal_id,
            canonical_target_id=canonical_target_id)
        self.ports[job_id] = built
        return built

    def required_tests(self, job_id=None):
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

        # W119405 review [P1]: THE PRODUCING WORKER OF THIS JOB, and not the
        # integration worker allocated for the current stage. The Job's own
        # binding names its producer by identity, so a deployment serving
        # several selects the right task instead of refusing for having more
        # than one. Without a stage -- which is how the accepted integration
        # cases reach this through a deployment double -- the old rule stands
        # exactly as it was.
        deployment = self.deployment
        if job_id is not None:
            bound = deployment.binding_for(job_id)["source_worker_id"]
            named = [one for one in deployment.given["workers"]
                     if one["worker_id"] == bound]
        else:
            named = [one for one in deployment.given["workers"]
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
        # W202663: BOTH IDENTITIES, BECAUSE TWO CALLERS WANT DIFFERENT ONES.
        # `input_manifest_digest` stays the PRODUCER's own runtime manifest
        # digest, which is what the harness identity below is composed from and
        # what every attribution of this producer already names. The Job-scoped
        # projection is added beside it for `_correspondent`, which asks a
        # different question -- whether this Job and this producer are about one
        # input -- and must not be answered with a digest that now legitimately
        # differs per worker.
        return {"task_id": task["task_id"],
                "task_digest": "sha256:" + hashlib.sha256(payload).hexdigest(),
                "argv": list(argv),
                "input_manifest_digest": manifest["manifest_digest"],
                "job_input_identity": job_input_identity(
                    manifest, what="the configured producer's input")}

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
        # W202663: THE JOB-SCOPED PROJECTION, because a Job names one input
        # identity and its workers now legitimately carry different runtime
        # manifests. Comparing the producer's WHOLE manifest digest here made
        # the Job's input identity a statement about one worker's image, which
        # is the coupling the owner ruling of 2026-09-18T22:01:51Z corrects.
        # The question this asks is unchanged -- is this Job about the input
        # this configured producer ran -- and it is now asked of the part of
        # the manifest that answers it.
        wanted = requirement["job_input_identity"]
        if held is not None and held != wanted:
            _refuse(f"this Job names input {held!r} and the configured "
                    f"producer's Job input identity is {wanted!r}; a required "
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
        answered = self._run(stage, job)
        if answered.get("outcome") == "integrated" and not _prepares(self.deployment.given):
            self.finish(stage)
        return answered

    def managed(self, stage, job):
        from . import integration_worker, integration_placement

        deployment = self.deployment
        result_id = "integration:" + stage["attempt_id"]
        preparation = reconciliation.retained_managed_preparation(deployment.integration, result_id)
        operations = deployment._integration_operations
        if isinstance(operations, _PerJobIntegration):
            operations = operations._serving(stage)
        if attempt_runtime_of(deployment.control, stage["attempt_id"]) is None:
            integration_worker.prepare_managed_parent(operations, stage, job)
        repository = os.path.join(deployment.given["state_root"], "managed-results", digest(result_id)[7:], "objects")
        integration_placement.managed_storage(deployment, job["job_id"], repository, deployment._place("integration_target")["path"])
        integration_placement.materialize_prepared_objects(deployment.control, preparation, repository=repository,
                                                          profile=deployment.reconciliation_profile, reader=deployment.integration_object_runner)
        result = reconciliation.managed_result_of(deployment.integration, result_id)
        if result["state"] == "awaiting-evidence":
            result = reconciliation.publish_managed_result(deployment.integration, deployment.control, deployment.jobs,
                                                           deployment.sessions["integrator"], managed_result_id=result_id, attempt_id=stage["attempt_id"])
        if result["state"] == "published":
            deployment.judge_managed_result(result_id, repository)
            result = reconciliation.record_managed_evidence(deployment.integration, deployment.authority,
                                                            deployment.sessions["verification"], deployment.sessions["review"], deployment.sessions["approval"],
                                                            managed_result_id=result_id)
        return self.apply_managed(stage, job, result, repository, operations)

    def apply_managed(self, stage, job, result, repository, operations):
        from baton_v12.integration import managed_execution, execution, queue
        from baton_v12.job_manager.integration_capacity import integration_capacity_of, admit_integration_execution
        from . import integration_bundle, integration_worker, integration_placement

        deployment, attempt = self.deployment, stage["attempt_id"]
        result_id = result["managed_result_id"]
        if result["state"] == "imported":
            self.finish_managed(stage, operations)
            return {"outcome": "integrated"}
        if result["state"] != "authorized":
            _refuse("the managed apply awaits independent acceptance")
        capacity = integration_capacity_of(deployment.jobs, result_id)
        planned = next(one for one in capacity["members"] if one["phase"] == "apply")
        fixed = attempt_runtime_of(deployment.control, attempt)["assignment"]
        preparation = reconciliation.retained_managed_preparation(deployment.integration, result_id)
        before = result["phases"]["prepare"]["task"]
        task = managed_execution.managed_task(
            phase="apply", orchestration_id=result_id, canonical_target_id=result["canonical_target_id"],
            execution_attempt_id=attempt, assignment=fixed, task_digest=planned["task_digest"], input_digest=planned["input_digest"],
            harness_digest=before["harness_digest"], execution_limits=before["execution_limits"], commands=["post-import"],
            parent={"execution_attempt_id": before["execution_attempt_id"], "collected_digest": preparation["collected"]["manifest_digest"]})
        manifest = operations._worker.given["input_manifest"]
        outputs = [one for one in manifest["outputs"] if one["type"] == "directory-result"]
        if not outputs:
            _refuse("managed apply requires a declared directory-result for its measured report")
        published = integration_bundle.compose_managed_apply_input(
            os.path.join(deployment.given["state_root"], "managed-results", digest(result_id)[7:], "apply-input"),
            manager=deployment.control, result=result, task=task, output_name=outputs[0]["name"])
        runtimes = self.__dict__.setdefault("managed_runtimes", {})
        if attempt not in runtimes:
            runtimes[attempt] = integration_worker.ManagedApplyRuntime(deployment, operations, published["request"], published["source"])
        active = runtimes[attempt]
        authorization = integration_placement.ManagedAuthorization(deployment, result_id, published["request"])
        entry_id, lease_id = "managed-entry:" + attempt, "managed-lease:" + attempt
        target_id = result["canonical_target_id"]
        profile = deployment.reconciliation_profile
        target = deployment._place("integration_target")["path"]
        reference = deployment.given["integration_target_reference"]
        granted = queue.lease_of(deployment.integration, lease_id)
        if granted is None:
            eligibility = execution.managed_result_eligibility(deployment.integration, deployment.control, deployment.jobs,
                                                              deployment.authority, authorization, managed_result_id=result_id)
            if profile.revision(target, reference) != result["target_revision"]:
                _refuse("the dedicated target changed before managed apply admission")
            queue.enqueue(deployment.integration, canonical_target_id=target_id, entry_id=entry_id, eligibility=eligibility)
            answer = queue.grant_lease(deployment.integration, canonical_target_id=target_id, entry_id=entry_id, lease_id=lease_id,
                                       integrator_participant=fixed["participant"], attempt_id=attempt)
            if answer is None:
                return {"outcome": "pending"}
            granted = answer["lease"]
        grant = {name: granted[name] for name in ("canonical_target_id", "entry_id", "lease_id", "fence")}
        publication = reconciliation.publication_of(deployment.integration, result_id, "apply")
        if publication is not None and publication["state"] == "settled" and deployment.authority.receipt(result["derived_proposal_id"], "integration") is not None:
            historical = reconciliation.managed_publication_view(deployment.integration, result_id)
            reconciliation._integrated_entry(deployment.integration, historical, entry_id)
            reconciliation._integration_receipt(deployment.authority, historical)
            queue.release_lease(deployment.integration, **grant, ending={"outcome": "integrated"})
            reconciliation.record_managed_imported(deployment.integration, deployment.authority, managed_result_id=result_id, entry_id=entry_id)
            self.finish_managed(stage, operations)
            return {"outcome": "integrated"}
        if planned["state"] == "planned":
            admit_integration_execution(deployment.jobs, deployment.control, orchestration_id=result_id, phase="apply",
                                        execution_attempt_id=attempt, assignment=fixed, coordinator=deployment.integration,
                                        authorization=authorization, grant=grant)
        if attempt_runtime_of(deployment.control, attempt)["runtime_id"] is None:
            queue.live_grant(deployment.integration, **grant)
            authorization.authorized({"managed_result_id": result_id, "canonical_target_id": target_id,
                                      "content_digest": preparation["collected"]["manifest_digest"]})
            if profile.revision(target, reference) != result["target_revision"]:
                _refuse("the dedicated target changed before the managed apply start")
        answered = active.poll(stage, job)
        if answered is None:
            return {"outcome": "pending"}
        if not answered["succeeded"]:
            from baton_v12.job_manager.integration_capacity import settle_failed_integration
            if publication is not None:
                _refuse("the failed apply has a target publication requiring manual inspection")
            queue.refuse_entry(deployment.integration, **grant, settlement={"reason": "managed apply failed", "detail": answered["report"]})
            settle_failed_integration(deployment.jobs, deployment.control, orchestration_id=result_id, phase="apply", coordinator=deployment.integration)
            return {"outcome": "failed"}
        exclusion = integration_placement.ManagedExclusion(active)
        target_owner = integration_placement.LocalGitTargetOwner(
            coordinator=deployment.integration, manager=deployment.control, profile=profile, execution_owner=exclusion,
            authorization=authorization, repository=target, reference=reference, managed_result_id=result_id)
        placement = integration_placement.LocalTargetPlacement(
            coordinator=deployment.integration, manager=deployment.control, profile=profile, execution_owner=exclusion,
            authorization=authorization, repository=target, reference=reference, target_owner=target_owner,
            materializer=integration_placement.ManagedMaterializer(deployment, published["request"], repository, target))
        integration_placement.publish_collected_integration(
            placement, **grant, admitted_old_revision=result["target_revision"], managed_result_id=result_id,
            settlement={"imported_paths": [], "verification": answered["report"]})
        deployment.sessions["integrator"].integrate({"proposal_id": result["derived_proposal_id"],
            "integration_id": "managed-integration:" + attempt, "operation_id": "managed-integrate:" + attempt})
        queue.release_lease(deployment.integration, **grant, ending={"outcome": "integrated"})
        reconciliation.record_managed_imported(deployment.integration, deployment.authority, managed_result_id=result_id, entry_id=entry_id)
        self.finish_managed(stage, operations)
        return {"outcome": "integrated"}

    def finish_managed(self, stage, operations):
        from baton_v12.job_manager.integration_capacity import begin_integration_ending

        worker, attempt = operations._worker, stage["attempt_id"]
        fixed = attempt_runtime_of(self.deployment.control, attempt)["assignment"]
        worker.session.route_fenced({"expect": fixed, "operation_id": "managed-integration-handoff:" + attempt,
                                     "fence_operation_id": "managed-apply-fence:" + attempt,
                                     "from_route": worker._claim(stage)["work_route"], "to_route": worker.given["review_route"]})
        discharge_quiescence_gate(self.deployment.control, worker.port, attempt_id=attempt,
                                  retention_policy_digest=worker.given["retention_policy_digest"])
        begin_integration_ending(self.deployment.jobs, orchestration_id="integration:" + attempt, reason="managed integration settled")

    def _run(self, stage, job):
        deployment = self.deployment
        if _prepares(deployment.given):
            return self.managed(stage, job)
        port = self.port_for(stage, job)
        # W133129: THE PORT REFUSAL IS DEFERRED UNTIL THE BRANCH IS KNOWN.
        # It used to fire here, before anything had asked WHICH integration
        # this is -- and the reconciled branch composes no model at all, so a
        # deployment with no runtime port refused the one path that does not
        # need one. The direct path still refuses exactly as it always did,
        # a few lines below, once the branch decision has chosen it.
        # W103068: AND AN ABSENT ONE IS NOT A REFUSAL ANY MORE. The direct
        # branch below CONSTRUCTS the port it needs once its operands are
        # resolved, so absence here means "not supplied by an operator" rather
        # than "this deployment cannot integrate". The dead refusal this
        # deferral left behind is removed with the capability gap it described.
        _direct_port = port
        control = deployment.control
        # W119405 review [P1]: THIS JOB'S LINE. `line()` is the one-Job
        # spelling and refuses a deployment binding several, so an integration
        # stage that asked it could never run for a second Job.
        job_id = _bound_id(deployment, stage, job)
        line = (deployment.line() if job_id is None
                else deployment.line_for(job_id))
        accepted = review_cycles.integration_checkpoint(control,
                                                        line["line_id"])
        if accepted is None:
            _refuse(f"development line {line['line_id']!r} holds no accepted "
                    f"integration checkpoint; an integration stage runs "
                    f"behind an accepted verdict and never ahead of one",
                    category="refused", code="precondition")
        operands = {
            "canonical_target_id": (_global(deployment, "canonical_target_id",
                                            "canonical target")
                                    if job_id is None
                                    else deployment.target_for(job_id)),
            "line_id": line["line_id"],
            "proposal_id": deployment.published_proposal(accepted),
            "policy_generation": deployment.given["policy_generation"],
            "profile": deployment.integration_profile,
            "attempt_id": stage["attempt_id"],
            "launch_root": deployment.integration_root,
            "workspace_group": deployment.workspace_group,
            "required_tests": self.required_tests(job_id)}
        self._correspondent(job, operands["required_tests"])

        # W133129: WHICH BRANCH THIS JOB'S CANDIDATE BELONGS TO, decided from
        # the Authority's own answer rather than from a refusal.
        #
        # A proposal is offered against the revision it was built from, and an
        # Authority holds ONE canonical target revision. So a candidate whose
        # published proposal names the revision that is still canonical is the
        # DIRECT import this deployment has always driven, and one whose
        # proposal names a revision the target has moved past is exactly the
        # case W131409 filed: the submission is as accepted as it ever was and
        # cannot be offered as it stands. That second candidate is reconciled
        # -- composed with the snapshot the earlier Job left, observed,
        # published as its own candidate and independently judged -- and never
        # admitted by relaxing the freshness rule the direct path keeps.
        published = _authority_read(
            "the producer's proposal",
            lambda: deployment.authority.proposal(operands["proposal_id"]))
        canonical = _authority_read(
            "the canonical target",
            lambda: deployment.authority.canonical_target())
        if published["target"] != canonical:
            if not deployment.reconciles():
                _refuse(
                    f"proposal {operands['proposal_id']!r} was built on "
                    f"{published['target']!r} and the canonical target is now "
                    f"{canonical!r}; this candidate is reconciled onto the "
                    f"snapshot that moved past it, and this deployment "
                    f"configures no integration target, workspace or observer "
                    f"to reconcile it with",
                    category="refused", code="capability")
            return self.reconciled(
                stage, job, operands,
                review_cycles.line_of(control, line["line_id"]))

        # W133129, owner return137905: THE EXPLICIT OPERANDS THE COORDINATOR
        # FINALIZES THE DEDICATED TARGET WITH. This assembly resolves the
        # configuration and the accepted source and hands them over; the target
        # write itself belongs to `execution` under the live grant, and no
        # private runtime-port field is read to get any of it.
        if _direct_port is None:
            # W103068 review 2026-09-11T01-22-35Z [P1]: THIS IS WHERE THE
            # PRODUCTION PORT IS CONSTRUCTED, and this branch used to refuse
            # `capability` here instead. The refusal was accurate about the
            # accepted composition of the time and it was also the whole reason
            # the public `factory` could not perform an ordinary direct
            # integration: it supplied no port, so every direct candidate
            # stopped one call before preparation.
            #
            # AND IT IS CONSTRUCTED HERE RATHER THAN ANYWHERE EARLIER because
            # here is the first place all three of its dynamic operands exist
            # and are read from their own owners: `line` came from the Job's own
            # binding through `line_for`, `accepted` is that line's integration
            # checkpoint, `operands["proposal_id"]` is the proposal the
            # producer actually published for it, and the target is the Job's
            # own. Two of the three do not exist until a review is accepted,
            # which is why no configuration document could carry them and why
            # the component fixture had to recompose the deployment after the
            # fact. Nothing is recomposed here and no serving object is rebuilt.
            #
            # ONE PORT PER JOB, MEMOIZED, so a stage re-entered on a later tick
            # is started through the same capacity rather than a second one.
            port = self._constructed(
                stage, job, line_id=line["line_id"],
                proposal_id=operands["proposal_id"],
                canonical_target_id=operands["canonical_target_id"])
        finalize = None
        if deployment.reconciles():
            finalize = {
                "profile": deployment.reconciliation_profile,
                "runner": _git_run,
                "target_root": deployment._place(
                    "integration_target")["path"],
                "reference": deployment.given[
                    "integration_target_reference"],
                "source": review_cycles.line_of(
                    control, line["line_id"])["line_path"]
                or review_cycles.line_of(
                    control, line["line_id"])["source_path"]}
        operands["finalize"] = finalize
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
            port.prepare(stage, job)
            return admit_accepted(
                deployment.integration, control, deployment.jobs,
                deployment.authority, *sessions, port, **operands)

        # A LATER TICK OVER A DELIVERY THIS DEPLOYMENT ALREADY PUBLISHED.
        # Owner ruling M115946: refresh FIRST, then continue only when the
        # port's own marker confirms this live execution started exactly this
        # assignment. Reading a persisted assignment grants no permission --
        # a fresh serving incarnation has no marker and falls through to
        # admission, which owns the restart hold it has always owned.
        seen = port.observed(stage["attempt_id"], assignment)
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
            port.prepare(stage, job)
        else:
            # AND A STARTED OR UNCERTAIN RUNTIME IS NOT PREPARED HERE. Its
            # credential custody belongs to the runtime that holds it, and the
            # hold `admit_accepted` has always owned is what answers a marker
            # this execution does not have.
            port.refresh(stage["attempt_id"])
            if port.may_continue(assignment, delivery):
                return continue_accepted(
                    deployment.integration, control, deployment.jobs,
                    deployment.authority, *sessions, **operands)
        return admit_accepted(
            deployment.integration, control, deployment.jobs,
            deployment.authority, *sessions, port, **operands)

    # -- W133129: the reconciled branch ------------------------------------

    def reconciled(self, stage, job, operands, line_row):
        """Take one Job whose target moved past its line all the way through.

        THE BRANCH EXISTS BECAUSE THE DIRECT PATH CORRECTLY REFUSES. An
        Authority holds ONE canonical target revision and a proposal is offered
        against the revision it was built from; the first Job's integration
        advances that revision, and the second Job's line was declared at the
        one it moved past. W133117 answers by composing the second submission
        with the snapshot the first left -- a NEW immutable candidate with its
        own content, causal observations, derived proposal and independent
        receipts -- and W133120 imports THAT.

        IT IS RE-ENTRANT, LIKE EVERY OTHER STAGE HERE. Each act is idempotent
        under its own operation identity, so a tick that dies anywhere resumes
        by asking the same questions again.

        AND IT WAITS FOR REAL RECEIPTS. Publication creates the candidate the
        three configured participants record their ordinary Authority receipts
        on; this assembly writes none of them and mints no accepting decision
        from the fact that a merge and a test succeeded. Until those receipts
        exist the result stays `published`, this stage stays PENDING, and no
        byte of the target moves.
        """
        deployment = self.deployment
        profile = deployment.reconciliation_profile
        workspace = deployment._place("integration_workspace")
        target_source = deployment._place("integration_target")
        reference = deployment.given.get("integration_target_reference")
        if reference is None:
            _refuse("this deployment configures no integration target "
                    "reference; a reconciled result is imported at exactly "
                    "one explicitly configured reference",
                    category="refused", code="capability")
        # THE ACCEPTED JOB'S OWN INPUT AND POLICY, read from the producer's
        # proposal rather than re-derived: `admission` already refuses unless
        # that proposal and the owning Job agree on both members, so this is
        # the Job's answer through the reader that proved it.
        original = _authority_read(
            "the producer's proposal",
            lambda: deployment.authority.proposal(operands["proposal_id"]))
        accepted_head = review_cycles.integration_checkpoint(
            deployment.control, line_row["line_id"])["evidence"]["head"]
        work_id = _bound(deployment, stage)[1]
        assignment = _authority_read(
            "the live integration assignment",
            lambda: deployment.authority.assignment_of(work_id))
        if assignment is None:
            _refuse(f"Work {work_id!r} has no live assignment; a result is "
                    f"composed under an assignment this role actually holds",
                    category="refused", code="precondition")
        # AND ITS ISOLATION IS PROVED BEFORE THE FIRST OBJECT IS WRITTEN.
        # Review 2026-09-10T15:18:28Z: the fetch below is this branch's FIRST
        # write, and `_place` only stats a path -- W133117's own isolation
        # proof runs inside `prepare_result`, which is one write too late. A
        # workspace that is really the dedicated target or the producer's line
        # would take candidate objects before anything refused, and without
        # holding any lease over the target.
        #
        # The profile's own public `storage` reader answers which REPOSITORY a
        # path is, through its resolved Git common directory, so an alias, a
        # symlink or a linked worktree answers the identity it shares rather
        # than the path it was named by. P's later check is unchanged and still
        # runs; this one exists so nothing is written before it.
        line_place = line_row["line_path"] or line_row["source_path"]
        mine = profile.storage(workspace["path"])
        # TWO ARE REQUIRED AND ONE IS OPTIONAL, and review 2026-09-10T15:26:50Z
        # is why that distinction is written out. A blanket `except: continue`
        # turned a FAILED identity read on the dedicated target or the
        # producer's line into permission to fetch anyway -- the same "writes
        # without proof" this guard exists to stop, reached through the error
        # path instead of the success path. Those two must resolve or nothing
        # is written. The protected source is genuinely optional: `line_of`
        # may answer a path this host cannot reach, and it is already covered
        # by the line's own identity, so an unresolvable one is skipped
        # deliberately rather than silently.
        for what, place, required in (
                ("the dedicated target", target_source["path"], True),
                ("the producer's development line", line_place, True),
                ("the producer's protected source", line_row["source_path"],
                 False)):
            if place is None:
                if required:
                    _refuse(f"{what} names no storage this deployment can "
                            f"identify; a reconciled result is not composed "
                            f"until its workspace is proved separate from it",
                            category="refused", code="capability")
                continue
            try:
                theirs = profile.storage(place)
            except Exception as failure:
                if required:
                    _refuse(f"{what} ({place!r}) does not resolve to a "
                            f"repository this profile can identify "
                            f"({type(failure).__name__}); isolation is proved "
                            f"before anything is fetched, not assumed",
                            category="refused", code="capability")
                continue
            if (theirs["device"], theirs["inode"]) == (mine["device"],
                                                       mine["inode"]):
                _refuse(f"the configured integration workspace "
                        f"{workspace['path']!r} is the same repository as "
                        f"{what} ({place!r}); a reconciled result is composed "
                        f"in storage the integration role owns, and nothing "
                        f"is fetched into shared storage",
                        category="refused", code="capability")

        # THE SUBMISSION'S RECEIPTS ARE READ HERE, NEVER ISSUED. Reviewer
        # 138861: `driver._accepted_receipts` checks the deployment pin against
        # the Authority's CURRENT generation before it issues anything, so
        # issuing at reconciliation time -- after the first Job's integration
        # bumped that generation -- can only ever refuse.
        # `StageComposition._source_receipts` issues each Job's own three where
        # its accepted review ends, while its configured pin is still current,
        # and this branch PROVES them historically before it fetches anything.
        #
        # AND IT PROVES THEM BEFORE THE FETCH RATHER THAN AFTER. Review
        # 2026-09-10T20:30:00Z: `prepare_result` re-proves the source, but that
        # is one write too late for the delivery below, so
        # `admission.source_submission` is asked HERE -- the accepted
        # checkpoint, the writer's assignment and frozen output, the committed
        # proposal with its three actual receipts and the owning Job -- and the
        # deployment's own required-test evidence is proved with it. Neither is
        # a new approval: the derived result's authorization stays under
        # current policy, in `record_result_evidence`.
        admission.source_submission(
            deployment.control, deployment.jobs, deployment.authority,
            line_id=operands["line_id"], proposal_id=operands["proposal_id"])
        # AND THE ORDINARY TEST EVIDENCE IS PROVED, NOT MERELY READ. Review
        # 2026-09-10T20:36:08Z: this called `ordinary_test_evidence` and threw
        # the answer away, so a submission whose configured required tests did
        # not actually pass would have reconciled anyway. `_ordinary_tests_
        # passed` is the owner of that judgement and the same one the direct
        # path admits behind.
        driver._ordinary_tests_passed(
            driver.ordinary_test_evidence(
                deployment.control, deployment.authority,
                line_id=operands["line_id"],
                proposal_id=operands["proposal_id"]),
            operands["required_tests"])

        # THE CANDIDATE MUST BE IN THIS ROLE'S OWN STORAGE BEFORE IT IS
        # COMPOSED. `prepare_result` is handed the workspace as its own
        # candidate source -- W133117 composes only out of storage the
        # integration role owns -- so the producer's accepted head is fetched
        # in first, by object name, from the line that holds it. `fetch` writes
        # objects and moves no reference the producer keeps.
        fetched = _git_run(tuple(git_profile.import_vector(
            workspace["path"], line_place, accepted_head)))
        if fetched["returncode"] != 0:
            _refuse(f"the accepted candidate could not be brought into the "
                    f"integration workspace: "
                    f"{fetched['stderr'].strip()[:240]}",
                    category="refused", code="precondition")
        held = reconciliation.prepare_result(
            deployment.integration, profile, deployment.control,
            deployment.jobs, deployment.authority,
            line_id=operands["line_id"],
            proposal_id=operands["proposal_id"],
            workspace=workspace, target_source=target_source,
            target_reference=reference,
            integration_attempt_id=stage["attempt_id"],
            integration_assignment=assignment,
            canonical_target_id=operands["canonical_target_id"])
        if held["state"] == "held":
            return {"outcome": "held", "entry": None, "assignment": None,
                    "observed": {"reason": held["reason"]}}

        if held["causal_observations"] is None:
            observer = _CausalObserver(
                deployment.observer_participant(),
                operands["required_tests"]["argv"], _git_run,
                deployment.integration_root,
                workspace=workspace["path"],
                line_root=line_place,
                base=held["source_base"],
                candidate=held["source_candidate"],
                identity=operands["required_tests"]["task_id"],
                seconds=_host_seconds(deployment, stage),
                retention=_host_retention(deployment),
                surviving=_host_scratch(deployment),
                scope=(stage.get("job_id"), held["result_id"], "causal"))
            held = reconciliation.record_causal_observations(
                deployment.integration, observer,
                result_id=held["result_id"])
        if held["state"] == "blocked":
            # THE COMBINED RESULT FAILED ITS OWN CAUSAL OBSERVATION. It is
            # retained, it blocks, and it is never verified away.
            return {"outcome": "held", "entry": None, "assignment": None,
                    "observed": {"reason": held["reason"]}}

        if held["state"] == "awaiting-evidence":
            held = reconciliation.publish_result(
                deployment.integration, deployment.sessions["integrator"],
                result_id=held["result_id"],
                input_digest=original["input_digest"],
                policy_digest=original["policy_digest"])

        if held["state"] == "published":
            # PENDING REAL RECEIPTS. The candidate exists and its three
            # configured owners have not judged it yet; nothing here judges it
            # for them.
            try:
                deployment.judge_result(held["result_id"])
                held = reconciliation.record_result_evidence(
                    deployment.integration, deployment.authority,
                    deployment.sessions["verification"],
                    deployment.sessions["review"],
                    deployment.sessions["approval"],
                    result_id=held["result_id"])
            except ContractRefusal as pending:
                return {"outcome": "pending", "entry": None,
                        "assignment": None,
                        "observed": {"result_id": held["result_id"],
                                     "derived_proposal_id":
                                         held["derived_proposal_id"],
                                     "awaiting": str(pending)}}

        verifier = _ImportedVerifier(
            deployment.observer_participant(),
            operands["required_tests"]["argv"], _git_run,
            deployment.integration_root,
            identity=operands["required_tests"]["task_id"],
            seconds=_host_seconds(deployment, stage),
            retention=_host_retention(deployment),
            surviving=_host_scratch(deployment),
            scope=(stage.get("job_id"), held["result_id"], "post-import"))
        return admit_authorized_result(
            deployment.integration, profile, _git_run, deployment.control,
            deployment.jobs, deployment.authority,
            deployment.sessions["integrator"], verifier,
            result_id=held["result_id"], attempt_id=stage["attempt_id"])

    def account(self, stage):
        """Cross-bind public owners without starting, refreshing or settling.

        The coordinator's producer generation is proposal provenance. Only the
        manager's fixed assignment identifies the integrator this stage ends.
        This reader uses existing handles; opening a separate status process
        remains the independently allocated read-only opener work.
        """
        if stage.get("kind") != "integration":
            return None
        deployment = self.deployment
        row = attempt_runtime_of(deployment.control, stage["attempt_id"])
        if _prepares(deployment.given):
            return None if row is None else self.managed_account(stage, row)
        # W133129 review 2026-09-10T21:10:42Z [P1]: WHICH BRANCH THIS IS, ASKED
        # BEFORE ANY RUNTIME-ONLY PREREQUISITE. The reconciled branch composes
        # no model, so `port.prepare` is never called for it and the manager
        # attempt is never activated -- `attempt_runtime_of` therefore answers
        # `None`, and this reader returned `None` right here, before it could
        # ever select the result. The measured consequence was the generic
        # "terminal integration handoff requires owned committed integration
        # and lease release" with the import already durable.
        #
        # THE SELECTOR IS AN IMMUTABLE OPERAND AND NOT A GUESS. W133117 records
        # `integration_attempt_id` on the result and nothing rewrites it, so
        # this stage's attempt names its own result and no other attempt's.
        reconciled = deployment.integration._connection.execute(
            "SELECT result_id FROM integration_results "
            "WHERE integration_attempt_id = ?",
            (stage["attempt_id"],)).fetchone()
        if reconciled is not None:
            return self._reconciled_account(stage, row,
                                            reconciled["result_id"])
        if row is None or row["assignment"] is None:
            return None
        fixed = row["assignment"]
        claims = claimed_offers_for(deployment.control, stage["attempt_id"])
        if len(claims) != 1 or claims[0]["offer_id"] != stage["offer_id"]:
            _refuse("integration observation has no exact claimed offer", category="refused", code="operation-collision")
        # W119405 review [P1]: THE ALLOCATED INTEGRATOR AND THIS JOB'S WORK.
        # Selecting the first integration-role worker answered with this
        # composition's configuration order, and comparing the global Work
        # would have refused the second Job's own fixed assignment as another
        # one. Both are read from committed records; the observation's handle
        # and context contract is untouched.
        worker, work_id, target_id = _bound(deployment, stage)
        if fixed["participant"] != worker["participant"] or fixed["work_ref"] != {
                "authority_uuid": deployment.given["authority_uuid"], "work_id": work_id}:
            _refuse("integration observation names another fixed assignment", category="refused", code="operation-collision")
        document = {"schema": INTEGRATION_OBSERVATION_SCHEMA,
                    **{name: stage[name] for name in ("stage_id", "episode", "attempt_id", "offer_id")},
                    "assignment": fixed, "state": "unstarted", "completion": None}
        operation_id = "integration-pass:" + stage["attempt_id"]
        account = {"document": document, "runtime": row, "operation_id": operation_id,
                   "to_route": worker["review_route"], "committed": False}
        delivery, assignment = self._published(stage)
        if assignment is None:
            # NOTHING HAS BEEN PUBLISHED FOR THIS ATTEMPT YET, and that is the
            # DIRECT branch's own first-tick answer. A reconciled import also
            # has no delivery, which is why the two are told apart above by the
            # coordinator's own custody record rather than by this absence.
            return account
        profile = deployment.integration_profile
        expected = {"canonical_target_id": target_id,
                    "attempt_id": stage["attempt_id"], "integrator_participant": fixed["participant"],
                    **{name: profile[name] for name in ("profile_kind", "profile_version", "instructions_digest")}}
        if any(assignment[name] != value for name, value in expected.items()):
            _refuse("integration delivery disagrees with the configured fixed attempt", category="refused", code="operation-collision")
        with deployment.integration.snapshot():
            lease = lease_of(deployment.integration, assignment["lease_id"])
            entries = [one for one in entries_of(deployment.integration, assignment["canonical_target_id"])
                       if one["entry_id"] == assignment["entry_id"]]
        if lease is None or len(entries) != 1 or any(lease[name] != assignment[name] for name in
                ("lease_id", "entry_id", "canonical_target_id", "attempt_id", "fence", "integrator_participant")):
            _refuse("integration delivery has no matching owned lease and entry", category="refused", code="operation-collision")
        entry = entries[0]
        if entry["authority_uuid"] != fixed["work_ref"]["authority_uuid"] or entry["work_id"] != fixed["work_ref"]["work_id"]:
            _refuse("integration entry belongs to another Work", category="refused", code="operation-collision")
        seen = runtime.observed_delivery(delivery, assignment)
        document["state"] = ("unstarted" if row["execution_runtime"] == _UNSTARTED else
                             "answered" if seen["state"] == "answered" else
                             "held" if seen["state"] == "held" else "pending")
        if entry["state"] in ("held", "refused") or lease["state"] == "abandoned":
            document["state"] = "held"
            return account
        if entry["state"] != "integrated":
            return account
        document["state"] = "answered"
        authority = deployment.authority
        proposal = _authority_read("integration proposal", lambda: authority.proposal(entry["proposal_id"]))
        receipt = _authority_read("integration receipt", lambda: authority.receipt(entry["proposal_id"], "integration"))
        producer = proposal["assignment_ref"]
        if producer["work_ref"] != fixed["work_ref"] or producer["generation"] != entry["assignment_generation"] or any(
                proposal[name] != entry[name] for name in ("proposal_id", "candidate_digest", "result_id", "result_digest")) or proposal["target"] != entry["expected_target_revision"]:
            _refuse("committed integration proposal disagrees with entry provenance", category="refused", code="operation-collision")
        expected_receipt = {"kind": "integration", "proposal_id": proposal["proposal_id"],
                            "actor": fixed["participant"], "disposition": "integrated",
                            "candidate_digest": proposal["candidate_digest"], "target": proposal["target"]}
        if receipt is None or any(receipt[name] != value for name, value in expected_receipt.items()):
            _refuse("integrated entry lacks its exact Authority receipt", category="refused", code="operation-collision")
        # W130224: THIS JOB'S OWN REQUIRED TEST. `required_tests()` with no Job
        # selects "the one implementation worker" and refuses a deployment
        # configuring several, so this one call site would have failed the
        # terminal completion check of EITHER Job under a `/2` document. The
        # binding's `source_worker_id` is the same selector the two operand
        # lines above already use.
        verification = entry["settlement"]["verification"]
        if verification["status"] != 0 or verification["argv"] != self.required_tests(
                _bound_id(deployment, stage))["argv"]:
            _refuse("integration settlement does not prove the configured required test")
        if lease["state"] != "released":
            return account
        if lease["ending"]["outcome"] != "integrated" or row["runtime_id"] is None:
            _refuse("integration completion lacks its released runtime grant")
        # The committed coordinator settlement required this exact attempt's
        # exclusion. It remains historical evidence after a later observation;
        # before a NEW pass, finish also requires current proved exclusion.
        account["committed"] = True
        passed = _authority_read("integration handoff", lambda: authority.operation_result(operation_id))
        if passed is None:
            return account
        expected_pass = {"assignment": fixed, "route": account["to_route"], "cause": "pass",
                         "fenced": False, "phase": "queued", "gate": None}
        if any(passed.get(name) != value for name, value in expected_pass.items()):
            _refuse("integration handoff does not end the exact fixed assignment on its outgoing route", category="refused", code="operation-collision")
        document["state"] = "completed"
        # W133129: A DIRECT IMPORT'S SOURCE AND DERIVED PROPOSAL ARE ONE
        # PROPOSAL, and it carries no reconciliation result. Saying both
        # explicitly is what lets a consumer read either completion without
        # guessing which branch produced it.
        document["completion"] = {"proposal_id": proposal["proposal_id"],
                                  "source_proposal_id": proposal["proposal_id"],
                                  "result_id": None,
                                  "integration_receipt_id": receipt["receipt_id"],
                                  "entry_id": entry["entry_id"], "lease_id": lease["lease_id"], "fence": lease["fence"],
                                  "handoff_operation_id": operation_id, "to_route": account["to_route"],
                                  "runtime_id": row["runtime_id"], "execution_runtime": "quiescent"}
        return account

    def _reconciled_account(self, stage, row, result_id):
        """The read-only completion account of a reconciled import.

        NOTHING IS FABRICATED TO SATISFY THE DIRECT PATH'S READER, which is
        review 2026-09-10T14:56:15Z's rule and 2026-09-10T15:07:43Z's
        restatement. There is no model delivery, so none is invented; there is
        no runtime, so `runtime_id` stays absent rather than borrowed; and the
        derived proposal belongs to the INTEGRATOR, so the producer-generation
        comparison the direct path makes is not asked here -- it would be a
        different claim about a different proposal.

        WHAT IS PROVED INSTEAD IS WHAT REALLY EXISTS: this stage's own result
        read back through `result_of`, its terminal `imported` state, the
        coordinator entry it was imported through, that entry's integrated
        settlement carrying the post-import execution, the Authority's own
        integration receipt on the derived proposal, and the released lease
        whose fence excluded every other writer. A present `result_id` is not
        completion authority by itself and this never treats it as one.

        AND NO RUNTIME MEMBER IS BORROWED TO GET HERE, which is review
        2026-09-10T21:10:42Z [P1]'s rule. This account is composed from the
        coordinator's result, the Job's own stage/attempt/offer, the Authority
        and the configured deployment -- never from a manager runtime row,
        because this branch activates none. `row` is passed in exactly as the
        manager holds it, INCLUDING absent, and the absence of a competing
        runtime is proved below as its own positive fact rather than skipped.
        """
        deployment = self.deployment
        held = reconciliation.result_of(deployment.integration, result_id)
        # THE JOB'S OWN STAGE, ATTEMPT AND OFFER, cross-bound exactly as the
        # direct branch binds them.
        claims = claimed_offers_for(deployment.control, stage["attempt_id"])
        if len(claims) != 1 or claims[0]["offer_id"] != stage["offer_id"]:
            _refuse("integration observation has no exact claimed offer",
                    category="refused", code="operation-collision")
        worker, work_id, target_id = _bound(deployment, stage)
        # THE FIXED ASSIGNMENT IS THE RESULT'S OWN IMMUTABLE OPERAND. W133117
        # stores the assignment this result was composed under and
        # `_live_assignment` proved it live at that moment; it is read back here
        # and cross-bound to the configured integrator and the bound Work --
        # the same two comparisons the direct branch makes against the runtime
        # row's copy. Nothing invents an assignment the manager never fixed.
        fixed = held["integration_assignment"]
        if fixed["participant"] != worker["participant"] or fixed["work_ref"] \
                != {"authority_uuid": deployment.given["authority_uuid"],
                    "work_id": work_id}:
            _refuse("the reconciled result was composed under another fixed "
                    "assignment", category="refused",
                    code="operation-collision")
        operation_id = "integration-pass:" + stage["attempt_id"]
        document = {"schema": INTEGRATION_OBSERVATION_SCHEMA,
                    **{name: stage[name] for name in
                       ("stage_id", "episode", "attempt_id", "offer_id")},
                    "assignment": fixed, "state": "unstarted",
                    "completion": None}
        account = {"document": document, "runtime": row,
                   "operation_id": operation_id,
                   "to_route": worker["review_route"], "committed": False,
                   "model_free": True}
        if held["state"] in ("held", "blocked"):
            document["state"] = "held"
            return account
        if held["state"] != "imported":
            # prepared, awaiting-evidence, published or authorized: real work
            # is in flight and no completion is claimable.
            return account
        if held["canonical_target_id"] != target_id:
            _refuse("the reconciled result belongs to another canonical target",
                    category="refused", code="operation-collision")
        document["state"] = "answered"
        authority = deployment.authority
        with deployment.integration.snapshot():
            entries = [one for one in
                       entries_of(deployment.integration, target_id)
                       if one["entry_id"] == held["entry_id"]]
            leases = [one for one in
                      deployment.integration._connection.execute(
                          "SELECT lease_id FROM leases WHERE entry_id = ?",
                          (held["entry_id"],)).fetchall()]
        if len(entries) != 1 or len(leases) != 1:
            _refuse("the reconciled result names no exact entry and lease",
                    category="refused", code="operation-collision")
        entry = entries[0]
        lease = lease_of(deployment.integration, leases[0]["lease_id"])
        if entry["state"] != "integrated" or lease is None:
            _refuse("the reconciled result is imported through an entry the "
                    "coordinator did not integrate",
                    category="refused", code="operation-collision")
        if entry["work_id"] != fixed["work_ref"]["work_id"] \
                or entry["authority_uuid"] != fixed["work_ref"]["authority_uuid"]:
            _refuse("integration entry belongs to another Work",
                    category="refused", code="operation-collision")
        receipt = _authority_read(
            "integration receipt",
            lambda: authority.receipt(held["derived_proposal_id"],
                                      "integration"))
        expected_receipt = {"kind": "integration",
                            "proposal_id": held["derived_proposal_id"],
                            "actor": fixed["participant"],
                            "disposition": "integrated",
                            "candidate_digest": held["prepared"]["head"],
                            "target": held["target_revision"]}
        if receipt is None or any(receipt[name] != value
                                  for name, value in expected_receipt.items()):
            _refuse("imported result lacks its exact Authority receipt",
                    category="refused", code="operation-collision")
        executed = entry["settlement"]["verification"].get("post_import_tests")
        if executed is None or executed["status"] != 0 \
                or executed["command"] != " ".join(self.required_tests(
                    _bound_id(deployment, stage))["argv"]):
            _refuse("reconciled settlement does not prove the configured "
                    "required test")
        if lease["state"] != "released":
            return account
        if lease["ending"]["outcome"] != "integrated":
            _refuse("reconciled completion lacks its released grant")
        # AND NO RUNTIME EVER RAN UNDER THIS ATTEMPT'S IDENTITY, which is a
        # fact to PROVE rather than a gap to excuse: the exclusion that
        # protected this import is the coordinator's released fence above, and
        # the manager must agree that nothing else ran. TWO SHAPES SATISFY THAT
        # and both are honest. Either the manager holds no attempt at all --
        # this branch never calls `port.prepare`, so nothing activated one,
        # which is the ordinary case -- or it holds one that was activated and
        # never started. What is refused is a row that names a runtime.
        if row is not None and (row["execution_runtime"] != _UNSTARTED
                                or row["runtime_id"] is not None):
            _refuse("a reconciled import composes no runtime and this "
                    "attempt's manager row names one",
                    category="refused", code="operation-collision")
        account["committed"] = True
        passed = _authority_read("integration handoff",
                                 lambda: authority.operation_result(operation_id))
        if passed is None:
            return account
        expected_pass = {"assignment": fixed, "route": account["to_route"],
                         "cause": "pass", "fenced": False, "phase": "queued",
                         "gate": None}
        if any(passed.get(name) != value
               for name, value in expected_pass.items()):
            _refuse("integration handoff does not end the exact fixed "
                    "assignment on its outgoing route",
                    category="refused", code="operation-collision")
        document["state"] = "completed"
        document["completion"] = {
            "proposal_id": held["derived_proposal_id"],
            "source_proposal_id": held["source_proposal_id"],
            "result_id": held["result_id"],
            "integration_receipt_id": receipt["receipt_id"],
            "entry_id": entry["entry_id"], "lease_id": lease["lease_id"],
            "fence": lease["fence"], "handoff_operation_id": operation_id,
            "to_route": account["to_route"], "runtime_id": None,
            "execution_runtime": "absent"}
        return account

    def observe(self, stage):
        account = self.account(stage)
        return None if account is None else account["document"]

    def managed_account(self, stage, row):
        from baton_v12.job_manager.integration_capacity import integration_capacity_of

        deployment, attempt = self.deployment, stage["attempt_id"]
        result_id = "integration:" + attempt
        held = reconciliation.managed_publication_view(deployment.integration, result_id)
        worker, work_id, target_id = _bound(deployment, stage)
        fixed = row["assignment"]
        claims = claimed_offers_for(deployment.control, attempt)
        if fixed is None or len(claims) != 1 or claims[0]["offer_id"] != stage["offer_id"] or fixed["participant"] != worker["participant"] or fixed["work_ref"] != {"authority_uuid": deployment.given["authority_uuid"], "work_id": work_id} or held["canonical_target_id"] != target_id:
            _refuse("the managed integration observation has no exact parent claim and target")
        document = {"schema": INTEGRATION_OBSERVATION_SCHEMA, **{name: stage[name] for name in ("stage_id", "episode", "attempt_id", "offer_id")},
                    "assignment": fixed, "state": "unstarted" if row["runtime_id"] is None else "pending", "completion": None}
        account = {"document": document, "runtime": row, "committed": False}
        from baton_v12.integration.queue import entries_of
        entry = next((one for one in entries_of(deployment.integration, target_id) if one["entry_id"] == "managed-entry:" + attempt), None)
        if entry is not None and entry["state"] == "held":
            document["state"] = "held"
            return account
        operations = deployment._integration_operations
        if isinstance(operations, _PerJobIntegration):
            operations = operations._serving(stage)
        exchanged = operations._worker.observed_exchange(stage)
        if exchanged is not None and exchanged.get("terminal") is not None:
            document["state"] = "answered" if exchanged["terminal"]["ending"] == "answered" else "held"
        if held["state"] != "imported":
            return account
        reconciliation.managed_import_account(deployment.integration, deployment.authority, managed_result_id=result_id, entry_id=held["entry_id"])
        publication = reconciliation.publication_of(deployment.integration, result_id, "apply")
        capacity = integration_capacity_of(deployment.jobs, result_id)
        if row["execution_runtime"] != "destroyed" or row["cleanup"] not in ("complete", "retained") or any(one["state"] != "ended" or one["outcome"] != "succeeded" for one in capacity["members"]):
            _refuse("the managed completion has not settled both actual executions")
        document["state"] = "answered"
        if capacity["root"]["lifecycle"] == "open":
            return account
        operation_id = "managed-integration-handoff:" + attempt
        passed = deployment.authority.operation_result(operation_id)
        discharged = gate_discharge_of(deployment.control, attempt)
        if passed is None or discharged is None:
            return account
        if passed != {"assignment": fixed, "fence_operation_id": "managed-apply-fence:" + attempt,
                      "from_route": claims[0]["work_route"], "to_route": worker["review_route"],
                      "phase": "block", "gate": "runtime-quiescence:" + str(fixed["generation"])}:
            _refuse("the managed parent handoff differs from its fixed assignment and route")
        receipt = reconciliation._integration_receipt(deployment.authority, held)
        document["state"] = "completed"
        document["completion"] = {"proposal_id": held["derived_proposal_id"], "source_proposal_id": held["source_proposal_id"],
                                  "result_id": result_id, "managed_result_id": result_id, "integration_receipt_id": receipt["receipt_id"],
                                  "entry_id": held["entry_id"], "lease_id": publication["lease_id"], "fence": publication["fence"],
                                  "handoff_operation_id": operation_id, "to_route": worker["review_route"],
                                  "runtime_id": row["runtime_id"], "execution_runtime": "destroyed"}
        account["committed"] = True
        return account

    def finish(self, stage):
        account = self.account(stage)
        if account is None or not account["committed"]:
            _refuse("terminal integration handoff requires owned committed integration and lease release", category="refused", code="precondition")
        if account["document"]["state"] == "completed":
            return account["document"]
        # W133129 review 2026-09-10T21:10:42Z [P1]: THE SECOND HALF OF THE SAME
        # MISMATCH. `QUIESCENT_STATES` is exactly `quiescent`/`destroyed` -- the
        # two words a container that RAN and stopped earns -- while the
        # model-free account proves the opposite fact, that no runtime ever ran.
        # So even a `not-started` row could not pass here, and a branch with no
        # row at all certainly could not. The direct branch's requirement is
        # unchanged; the reconciled one is not skipped but answered by its own
        # proof, which `_reconciled_account` has already established: the
        # coordinator's released grant on the exact fence, and the absence of
        # any runtime under this attempt's identity.
        if not account.get("model_free") and \
                account["runtime"]["execution_runtime"] \
                not in runtime.QUIESCENT_STATES:
            _refuse("terminal integration handoff requires proved worker exclusion", category="refused", code="precondition")
        _authority_read("integration terminal pass", lambda: self.deployment.sessions["integrator"].pass_work({
            "expect": account["document"]["assignment"], "operation_id": account["operation_id"],
            "to_route": account["to_route"], "comment": "Accepted integration completed after worker exclusion."}))
        observed = self.observe(stage)
        if observed["state"] != "completed":
            _refuse("terminal integration pass has no committed readback", category="refused", code="precondition")
        return observed


def _sole_producer(given):
    """The one implementation participant, where there is exactly one."""
    producers = sorted({one["deployment"]["participant"]
                        for one in given["workers"]
                        if one["role"] == "implementation"})
    return producers[0]


class _PerJobPublication:
    """The publication seam a multi-producer pool cannot choose for a caller.

    W119403. `Publication` publishes ONE producer's candidate under that
    producer's own session. With several producers configured, which one
    publishes is a per-Job fact, and this cut owns the pool rather than the
    binding -- so the seam refuses with a sentence naming the cut that answers
    it instead of quietly picking the first.
    """

    def _refuse_selection(self, *arguments, **operands):
        _refuse("this deployment configures several implementation workers "
                "and publication is one producer's act; selecting among them "
                "is the per-Job binding cut's, not this pool's",
                category="refused", code="precondition")

    publish = _refuse_selection
    published_of = _refuse_selection


class StageDeployment:
    """Everything the three compositions above share, resolved once.

    IT HOLDS OPERANDS AND NOT DECISIONS. Which line, which profile, which
    retention policy, which Authority sessions -- each is one configured or
    durably derived fact, and every act performed with them belongs to an
    accepted operation.
    """

    def __init__(self, given, *, control, jobs, authority, integration,
                 profile, sessions, verdict=None, engine_run=None,
                 credential_provider=None, clock=None):
        self.given = given
        # W103068: THE TWO CAPABILITIES AN INTEGRATION RUNTIME PORT IS
        # CONSTRUCTED WITH, retained because the port cannot be constructed
        # until a review has been accepted and this composition is the only
        # thing that will still be holding them then. They are the SAME objects
        # this composition was handed; nothing is defaulted or rebuilt.
        self._engine_run = engine_run
        self._credential_provider = credential_provider
        # AND THE COMPOSED INTEGRATION CAPACITY, attached after the workers are
        # built because the operations object does not exist yet here.
        self._integration_operations = None
        self.judges = {}
        self.judgment_clock = clock
        self.judgment_providers = {}
        self.control = control
        self.jobs = jobs
        self.authority = authority
        self.integration = integration
        self.profile = profile
        self.sessions = sessions
        # W119403: ONE PUBLICATION SEAM PER PRODUCER. `Authority.publish`
        # takes the producer's live assignment, so the seam belongs to the
        # participant whose worker produced the candidate. With one producer
        # this is the single seam it has always been; with several, choosing
        # among them is the per-Job binding cut's and this refuses instead.
        self.publications = {
            who[len(PUBLISHER_PREFIX):] if who.startswith(PUBLISHER_PREFIX)
            else _sole_producer(given): Publication(control, session)
            for who, session in (sessions or {}).items()
            if who == "publisher" or who.startswith(PUBLISHER_PREFIX)}
        self.publication = (list(self.publications.values())[0]
                            if len(self.publications) == 1
                            else _PerJobPublication())
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
        # NO CAPACITY, NO WORKSPACE GROUP -- and none is inferred.
        # W183883, OWNER-FRESH-INSTALL-20260916.md: the group is provisioned by
        # `worker_preflight`, which an instance configuring no worker never
        # runs, and it is needed only to allocate an EXECUTION workspace. An
        # instance that serves no stage allocates none. Asking for one here
        # would make a fresh installation refuse to start over a grant nothing
        # was going to use; inferring one is what `configured_workspace_group`
        # itself refuses to do, and this does not do it either.
        self.workspace_group = (None if _serves_nothing(given)
                                else configured_workspace_group(control))
        # W119403: ROLE TO WORKERS, NOT ROLE TO WORKER. The seam the next cut
        # selects an eligible worker on; `sole_worker` is what the consumers
        # that genuinely need one producer today ask instead.
        self._roles = {}
        for one in given["workers"]:
            self._roles.setdefault(one["role"], []).append(one)
        # THE PRODUCER PARTICIPANT TO ITS OWN PUBLISHER SESSION. With one
        # producer that is the single `publisher` session this deployment has
        # always minted, under its own participant's name.
        self.publishers = {who[len(PUBLISHER_PREFIX):]: session
                           for who, session in (sessions or {}).items()
                           if who.startswith(PUBLISHER_PREFIX)}
        producers = sorted({one["deployment"]["participant"]
                            for one in given["workers"]
                            if one["role"] == "implementation"})
        if len(producers) == 1 and "publisher" in (sessions or {}):
            self.publishers[producers[0]] = sessions["publisher"]

    def binding_for(self, job_id):
        """This Job's own binding, or a refusal naming the Job.

        W119405. An unknown Job is refused HERE, before anything durable is
        prepared for it -- a deployment that materialized a line for a Job it
        cannot bind would have created a checkout nobody can account for.

        THE ONE-JOB DOCUMENT BINDS EVERY JOB IT IS ASKED ABOUT, which is what
        it has always done: it names one Work, one base and one target, and it
        was written for the one Job that submits against them.
        """
        held = self.given["job_bindings"]
        if len(held) == 1 and held[0]["job_id"] is None:
            return held[0]
        for one in held:
            if one["job_id"] == job_id:
                return one
        _refuse(f"this deployment binds no Job {job_id!r}; a source, a base, a "
                f"Work and a target are facts about a Job, and one it cannot "
                f"bind is one it cannot serve", category="refused",
                code="precondition")

    def works_for(self, job_id):
        """The implementation and review Work this Job is bound to."""
        binding = self.binding_for(job_id)
        return binding["job_work_id"], binding["review_work_id"]

    def target_for(self, job_id):
        """The canonical target this Job's integration acts on."""
        return self.binding_for(job_id)["canonical_target_id"]

    def source_for(self, job_id):
        """The nominated source this Job's line is materialized from.

        NAMED BY WORKER IDENTITY AND READ FROM THAT WORKER'S OWN HELD
        DEPLOYMENT, so the nomination is the one `single_worker`'s validator
        already proved rather than a second copy of those rules here.
        """
        binding = self.binding_for(job_id)
        for one in self.given["workers"]:
            if one["worker_id"] == binding["source_worker_id"]:
                return one["deployment"]["source_nomination"]
        _refuse(f"Job {job_id!r} binds its source to worker "
                f"{binding['source_worker_id']!r}, which this deployment does "
                f"not configure", category="refused", code="precondition")

    def line_for(self, job_id):
        """THIS JOB'S persistent line, created or recovered.

        W119405. `line()` reached one global source, base and Work, so a second
        submitted Job could only ever share the first one's checkout. Here the
        source, the base and the Work are the JOB'S OWN, and `create_line`'s
        identity is derived from `(authority, work)` -- so distinct Works give
        distinct lines, and every tick and every incarnation reaches the same
        one for the same Job with no manual choice anywhere.
        """
        binding = self.binding_for(job_id)
        created = review_cycles.create_line(
            self.control, source=self.source_for(job_id),
            declared_base=binding["line_declared_base"],
            profile=self.profile, authority_uuid=self.given["authority_uuid"],
            work_id=binding["job_work_id"])
        return review_cycles.line_of(self.control, created["line_id"])

    def worker_for(self, stage):
        """The worker the SCHEDULER allocated to this stage's attempt.

        W119405, and the FINDING says it in as many words: actual allocation
        evidence selects a worker and list order is never a binding. The
        allocation is the manager's own durable record of which worker holds
        this attempt, so a composition that picked the first configured worker
        of a role would be answering with its own configuration order instead.
        """
        held = allocation_of(self.jobs, stage["attempt_id"])
        if held is None:
            _refuse(f"stage {stage.get('stage_id')!r} has no recorded worker "
                    f"allocation; which worker serves an attempt is the "
                    f"scheduler's record and not this composition's order",
                    category="refused", code="precondition")
        for one in self.given["workers"]:
            if one["worker_id"] == held["worker_id"]:
                return one
        _refuse(f"stage {stage.get('stage_id')!r} is allocated to worker "
                f"{held['worker_id']!r}, which this deployment does not "
                f"configure", category="refused", code="precondition")

    def publication_for(self, participant):
        """The publication seam belonging to THIS producer.

        W119405 review 2026-09-09T18:35Z [P1]: the ending passed
        `self.publication`, which under several producers is the seam that
        refuses -- so a second Job could not reach its ending at all. The
        producer is the ending attempt's own assignment participant, and
        `Authority.publish` takes that producer's live assignment, so this is
        the one session that could act for it.
        """
        held = self.publications.get(participant)
        if held is None:
            _refuse(f"this deployment composes no publication seam for "
                    f"{participant!r}, which is the participant this ending's "
                    f"attempt was assigned to", category="refused",
                    code="capability")
        return held

    def workers_for(self, role):
        """Every worker this deployment configured for a role, in order.

        THE SEAM, and it never reduces a role to a singleton. A caller that
        needs to choose among them chooses; a caller that cannot yet says so
        through `sole_worker`.
        """
        return list(self._roles.get(role, ()))

    def sole_worker(self, role):
        """The one worker for a role, or a refusal naming what is missing.

        WHAT THIS REFUSAL IS FOR. Under the multi-worker variant a source, a
        task, a line or a target is a PER-JOB fact, and choosing the first
        configured producer would be this cut inventing the binding the next
        one owns. So the question is refused where it is asked, with a sentence
        that says which cut answers it.
        """
        held = self.workers_for(role)
        if len(held) != 1:
            _refuse(f"this deployment configures {len(held)} {role} workers "
                    f"and this question is about one; selecting among several "
                    f"is the per-Job binding cut's, not this pool's",
                    category="refused", code="precondition")
        return held[0]

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
        held = self.given["job_bindings"]
        if len(held) != 1:
            _refuse(f"this deployment binds {len(held)} Jobs and this question "
                    f"is about one line; a line belongs to a Job, so its Job "
                    f"is named", category="refused", code="precondition")
        return self.line_for(held[0]["job_id"])

    # -- W133129: the reconciled import's own configured operands ----------

    def _place(self, name):
        """One configured directory, as the closed place W133117 nominates.

        THE DEVICE AND INODE ARE READ HERE AND PROVED THERE. `reconciliation`
        stats what it is handed and refuses replaced or misidentified storage;
        what this composes is the nomination, from a path the deployment
        configured rather than one derived from an opaque identity.
        """
        import os as _os

        configured = self.given.get(name)
        if configured is None:
            _refuse(f"this deployment configures no {name!r}; a reconciled "
                    f"integration composes a result in the integration role's "
                    f"own storage and imports it into the dedicated target, "
                    f"and both are deployment wiring",
                    category="refused", code="capability")
        _text(configured, f"the configured {name}")
        try:
            held = _os.stat(configured)
        except OSError as failure:
            _refuse(f"the configured {name} {configured!r} cannot be stat-ed "
                    f"({type(failure).__name__})",
                    category="refused", code="capability")
        return {"path": configured, "device": held.st_dev,
                "inode": held.st_ino}

    @property
    def integration_object_runner(self):
        """The read-only Git object runner `integration_bundle` requires.

        THAT MODULE NAMES THE CONTRACT AND SAYS WHOSE IT IS: `runner(argv, *,
        directory) -> {"returncode", "stdout", "stderr"}` over BYTES, with the
        descriptor valid for the call only, and "what this module cannot do is
        audit an injected runner: the contract above is what a deployment
        supplies". This assembly is that deployment, so it supplies one -- the
        same production shape it already owns for the checkpoint profile, in the
        second closed shape the bundle reader requires.

        THE DIRECTORY IS A DESCRIPTOR AND NOT A PATH, which is the whole reason
        the contract is separate: the caller has already opened the repository
        and hands this the open handle, so nothing here re-resolves a path that
        could have been replaced between the open and the read. It is passed
        through to the child rather than retained.
        """
        import subprocess as _subprocess

        def runner(argv, *, directory):
            answer = _subprocess.run(
                list(argv), cwd=f"/proc/self/fd/{directory}",
                pass_fds=(directory,), capture_output=True,
                timeout=GIT_SECONDS)
            return {"returncode": answer.returncode,
                    "stdout": answer.stdout, "stderr": answer.stderr}

        return runner

    def integration_instructions(self):
        """The integrator's configured instruction bytes, read and PROVED.

        W103068: `IntegrationRuntimePort` seals these into the bundle it
        composes, and until now no accepted configuration said where they are.
        The integration profile has always pinned their DIGEST -- that is what
        `integration_bundle` and the coordinator's own profile compare against
        -- so this member names the file and the pin is what makes reading it
        safe: bytes that do not digest to the configured pin are refused before
        any container is started, rather than producing a bundle that could
        never match the profile it was sealed under.

        IT IS NOT THE WORKER'S TASK DOCUMENT. The integration worker's task
        document is the JOB's task -- the same document its producer and
        reviewer are configured with -- and its digest is the input manifest's
        business. The integrator's instructions are a different artifact about a
        different act, so they are configured separately instead of being
        recovered from a member that means something else.
        """
        configured = self.given.get("integration_instructions")
        if configured is None:
            _refuse("this deployment configures no integration_instructions; "
                    "the integrator's instruction bytes are sealed into the "
                    "bundle it runs and where they live is deployment wiring",
                    category="refused", code="capability")
        _text(configured, "the configured integration instructions")
        _path(configured, "the configured integration instructions")
        try:
            with open(configured, "rb") as reading:
                held = reading.read(MAX_CONFIG_BYTES + 1)
        except OSError as failure:
            _refuse(f"the configured integration instructions {configured!r} "
                    f"cannot be read ({type(failure).__name__})",
                    category="refused", code="capability")
        if len(held) > MAX_CONFIG_BYTES:
            _refuse(f"the integrator's instructions are at most "
                    f"{MAX_CONFIG_BYTES} bytes", code="limit")
        if not held:
            _refuse("the integrator's instruction bytes are a non-empty byte "
                    "string this deployment configured",
                    category="refused", code="capability")
        return held

    def integration_home(self, name):
        """One of this deployment's integration homes, made once."""
        import os as _os

        place = _os.path.join(self.given["state_root"], name)
        _os.makedirs(place, exist_ok=True)
        return place

    def integration_operations_for(self, job_id):
        """The composed integration worker's operations for one Job.

        ONE CAPACITY, ONE OPERAND SET PER JOB. `_integration_operations`
        answers a single object under one binding and a `_PerJobIntegration`
        under several; both are the same worker, and what differs is the held
        operands. This selects among them exactly as the provider does, so the
        port a Job's integration is started by is composed over that Job's own
        configured Work, input, profile and policy.
        """
        held = self._integration_operations
        if held is None:
            _refuse("this deployment has composed no integration worker "
                    "operations; an integration runtime port is constructed "
                    "over the capacity that serves the stage",
                    category="refused", code="precondition")
        selected = getattr(held, "held", None)
        if type(selected) is dict:
            if job_id not in selected:
                _refuse(f"this deployment composes integration operands for "
                        f"{sorted(selected)} and this stage names Job "
                        f"{job_id!r}", category="refused", code="precondition")
            return selected[job_id]
        return held

    def activate_targets(self):
        """Adopt every canonical target this deployment configures.

        W103068: THE SECOND OPERATOR STEP THE PRODUCTION COMPOSITION DID NOT
        PERFORM. `enqueue` refuses an entry whose target "is not activated; an
        entry belongs to a configured target", and nothing in the public factory
        ever activated one -- the accepted component fixture called
        `activate_target` by hand before every integration. A deployment that
        configures a target and cannot adopt it is a deployment whose ordinary
        integration refuses `policy/denied` on its first entry.

        IT IS THE DOCUMENT'S OWN KEY AND A DERIVED DESCRIPTION. `activate_target`
        makes an exact repeat one act -- the operation identity carries the
        document's digest -- so this composes the same document from the same
        configuration on every restart and replays instead of colliding. The key
        is the configured `canonical_target_id` and is never derived from a
        line, a proposal or a revision, which is that function's own rule.
        """
        from baton_v12.integration import TARGET_SCHEMA, activate_target

        for target_id in sorted({one["canonical_target_id"] for one in
                                 self.given["job_bindings"]}):
            activate_target(self.integration, {
                "schema": TARGET_SCHEMA, "canonical_target_id": target_id,
                "description": f"configured by stage-execution deployment "
                               f"{self.given['authority_uuid']} at pool "
                               f"generation {self.given['pool_generation']}"})

    def judgment_executions(self, job_id):
        """This Job's three configured derived-result judgment executions.

        W103068. ABSENCE IS AN ANSWER AND IT IS NOT A POSITIVE ONE: a Job whose
        derived branch has no configured consumer has no way to obtain
        independent judgments of the merged candidate, so this says so and the
        caller leaves the result PUBLISHED. It never invents an execution, and
        it never lets a successful merge stand in for a judgment.
        """
        configured = self.given.get("result_judgment_workers")
        if configured is None or job_id not in configured:
            return None
        return configured[job_id]

    def judge_managed_result(self, result_id, repository):
        return self.judge_result(result_id, _managed_repository=repository)

    def judge_result(self, result_id, *, _managed_repository=None):
        """Dispatch and adopt real judgments before current-policy receipts."""
        subject = self.judgment_subject(result_id, managed=_managed_repository is not None)
        configured = self.judgment_executions(subject["job_id"])
        if configured is None:
            return None
        subject["policy_generation"] = self.authority.policy_generation()
        home = os.path.join(self.given["state_root"], "result-judgments", digest(result_id)[7:])
        os.makedirs(home, exist_ok=True)
        document = json.dumps(subject, sort_keys=True, separators=(",", ":")).encode()
        dispatch = os.path.join(home, "subject.json")
        # The first dispatch pins policy. Drift cannot silently start a new
        # set of judges or reuse their reports under a newer generation.
        try:
            descriptor = os.open(dispatch, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
        except FileExistsError:
            descriptor = os.open(dispatch, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            try:
                if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                    _refuse("the retained judgment dispatch is not a regular file")
                if os.read(descriptor, len(document) + 1) != document:
                    _refuse("the derived judgment dispatch changed, including its policy generation",
                            category="refused", code="precondition")
            finally:
                os.close(descriptor)
        else:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(document)
                stream.flush()
                os.fsync(stream.fileno())
        source = os.path.join(home, "source")
        if not os.path.lexists(source):
            origin = (_managed_repository if _managed_repository is not None
                      else reconciliation.result_of(self.integration, result_id)["workspace"]["path"])
            cloned = _git_run(tuple(clone_vector(origin, source)))
            if cloned["returncode"] != 0:
                _refuse("the derived judgment snapshot could not be cloned",
                        category="refused", code="precondition")
            imported = _git_run(tuple(git_profile.import_vector(source, origin, subject["candidate"])))
            if imported["returncode"] != 0:
                _refuse("the derived judgment snapshot could not import its candidate",
                        category="refused", code="precondition")
            try:
                self.profile.materialize(source, source, subject["candidate"])
            except checkpoint_profiles.ProfileRefusal as failure:
                _refuse(f"the derived judgment snapshot could not be materialized: {failure}",
                        category="refused", code="precondition")
        if not os.path.isdir(source) or os.path.islink(source):
            _refuse("the judgment snapshot must be its own directory")
        for expression, expected in (("HEAD", subject["candidate"]), ("HEAD^{tree}", subject["tree"])):
            observed = _git_run(("git", "-C", source, "rev-parse", "--verify", expression))
            if observed["returncode"] != 0 or observed["stdout"].strip() != expected:
                _refuse("the retained judgment snapshot is not the derived candidate")
        clean = _git_run(("git", "-C", source, "status", "--porcelain", "--untracked-files=all"))
        if clean["returncode"] != 0 or clean["stdout"]:
            _refuse("the retained judgment snapshot is not clean")
        answers = {}
        for kind, one in configured.items():
            key = (result_id, kind)
            if key not in self.judges:
                self.judges[key] = single_worker.JudgmentExecution(
                    one["deployment"], self.control, self.authority,
                    self.judgment_providers[one["worker_id"]], worker_id=one["worker_id"],
                    subject=dict(subject, kind=kind), source=source, engine_run=self._engine_run, clock=self.judgment_clock,
                    # W156162: THE SAME NARROW READER the pooled workers and the
                    # integration port are composed with. A derived judgment
                    # runs a real container over a real candidate, and it was
                    # the one execution in this deployment that received no Job
                    # context at all.
                    execution_context=single_worker.job_execution_reader(self.jobs))
            answers[kind] = self.judges[key].poll()
        if any(answer is None for answer in answers.values()):
            _refuse("the derived candidate awaits its configured judges' frozen reports",
                    category="refused", code="precondition")
        if any(answer["verdict"] != "accepted" for answer in answers.values()):
            _refuse("a derived candidate judgment did not accept the result",
                    category="refused", code="precondition")
        if self.authority.policy_generation() != subject["policy_generation"]:
            _refuse("policy changed while the derived candidate was judged",
                    category="refused", code="precondition")
        for kind, answer in answers.items():
            evidence_id = "judgment-" + digest(answer)[7:]
            operands = {"proposal_id": subject["derived_proposal_id"],
                        "operation_id": evidence_id}
            if kind == "verification":
                self.sessions[kind].verify(dict(operands, verification_id=evidence_id, observation="passed"))
            elif kind == "review":
                self.sessions[kind].review(dict(operands, review_id=evidence_id, disposition="accepted"))
            else:
                self.sessions[kind].approve(dict(operands, approval_id=evidence_id, disposition="approved",
                                                 policy_generation=subject["policy_generation"]))
        return answers

    def judgment_subject(self, result_id, *, managed=False):
        """The exact immutable subject a judgment is dispatched about.

        EVERY MEMBER IS READ FROM THE COORDINATOR'S OWN CUSTODY RECORD, through
        the public reader that re-derives that record's identity and re-proves
        every act it passed through. Nothing here is composed from a caller
        value, and nothing names the producer's ORIGINAL candidate: the subject
        of this judgment is the DERIVED one -- its own proposal, its own content
        and head, and the target revision it was reconciled onto.

        THE CAUSAL EVIDENCE TRAVELS WITH IT, retained and unmodified, because a
        judge must be able to read what the harness actually observed rather
        than be told it passed. It is evidence for a judgment and never a
        substitute for one: `record_result_evidence` still requires three real
        receipts, and W133117 keeps a failing combined observation `blocked`.
        """
        held = (reconciliation.managed_publication_view(self.integration, result_id) if managed
                else reconciliation.result_of(self.integration, result_id))
        if held["state"] != "published":
            _refuse(f"result {result_id!r} is {held['state']!r}; a judgment is "
                    f"dispatched about a published derived candidate",
                    category="refused", code="precondition")
        return {"result_id": held["result_id"],
                "job_id": held["job_id"],
                "canonical_target_id": held["canonical_target_id"],
                "derived_proposal_id": held["derived_proposal_id"],
                "derived_result_id": held["derived_result_id"],
                "derived_result_digest": held["derived_result_digest"],
                "content_digest": held["content_digest"],
                "candidate": held["prepared"]["head"],
                "tree": held["prepared"]["tree"],
                "target_revision": held["target_revision"],
                "source_proposal_id": held["source_proposal_id"],
                "source_base": held["source_base"],
                "source_candidate": held["source_candidate"],
                "causal_observations": held["causal_observations"],
                "observed_by": held["observed_by"]}

    def integration_served(self, job_id):
        """The held document this deployment's integrator serves a Job under.

        THIS MODULE'S OWN ANSWER, not another module's private state.
        `_served_deployment` is the same derivation `_integration_operations`
        composed the capacity with and `_job_workers` reads for compatibility,
        so the operands a constructed port is given are the ones the provider
        itself holds the stage to -- one derivation, asked again, rather than a
        second opinion about the same Job.
        """
        named = [one for one in self.given["workers"]
                 if one["role"] == "integration"]
        if len(named) != 1:
            _refuse(f"this deployment names {len(named)} integration workers; "
                    f"one deployment names one integrator",
                    category="refused", code="precondition")
        binding = self.binding_for(job_id)
        return _served_deployment(self.given, named[0], binding)

    def integration_port_for(self, job_id, *, line_id, proposal_id,
                             canonical_target_id):
        """CONSTRUCT this Job's real integration runtime port, here, now.

        W103068 review 2026-09-11T01-22-35Z [P1]. `factory` composed a
        deployment that supplied no port at all, `_integration_ports` mapped
        every bound Job to `None`, and the direct branch therefore refused
        `capability` before it ever reached preparation or admission -- so the
        advertised production entry point could not perform an ordinary
        integration. The concrete port class existed and every constructor call
        was in a test.

        WHY IT IS CONSTRUCTED HERE RATHER THAN AT CONFIGURATION. Two of its
        three dynamic operands do not exist when a deployment is composed: the
        accepted line's integration checkpoint and the proposal its producer
        published come into being when a review is ACCEPTED, which is after
        serving started. The component fixture answered that by recomposing the
        whole deployment with ports after the fact; a production provider cannot
        restart itself, so the fixed half is resolved at composition and the
        dynamic half is read from its own public owners at the moment the stage
        that needs it runs.

        EVERY OPERAND IS ALREADY CONFIGURED OR DURABLY DERIVED, and none is
        invented. The identity digests, adapter, engine, network, launch
        contract, credential resolution, workspace storage, capacity and
        retained input manifest are the integration worker's OWN held document;
        the toolchain digest is that manifest's own member, exactly as
        `single_worker` records it for every other role; the instruction bytes
        are the integrator's own configured task document, whose digest the
        integration profile already pins; the target directory, the delivery
        home and the two sibling homes are this deployment's wiring; and the
        engine and credential capabilities are the ones this composition was
        handed. Nothing reads another module's private attributes.
        """
        from baton_v12.contracts import digest_of_bytes

        from . import integration_worker

        from baton_v12.worker_manager import credentials

        operations = self.integration_operations_for(job_id)
        given = self.integration_served(job_id)
        instructions = self.integration_instructions()
        # AND THE PROFILE'S PINNED DIGEST IS WHAT PROVES THEY ARE THE RIGHT
        # BYTES. `integration_bundle` seals the instructions into the bundle and
        # the coordinator's profile carries their digest, so a deployment whose
        # configured instructions and integration profile disagree is one whose
        # bundle could never match the profile it was sealed under -- and
        # finding that out at the engine is finding it out too late.
        pinned = self.integration_profile["instructions_digest"]
        if digest_of_bytes(instructions) != pinned:
            _refuse(f"the configured integration instructions digest to "
                    f"{digest_of_bytes(instructions)!r} and this deployment's "
                    f"integration profile pins "
                    f"{pinned!r}", category="refused", code="capability")
        if self._engine_run is None:
            _refuse("this deployment was composed with no engine run "
                    "capability; an integration runtime port starts a real "
                    "container through one", category="refused",
                    code="capability")
        if self._credential_provider is None:
            _refuse("this deployment was composed with no credential "
                    "provider; the integrator's bearer is materialized through "
                    "one", category="refused", code="capability")
        manifest = given["input_manifest"]
        return integration_worker.IntegrationRuntimePort(
            coordinator=self.integration, manager=self.control, jobs=self.jobs,
            # THE ASSIGNMENT PORT IS `ManagerOperations.port` -- the public
            # restricted port this deployment's own composition was handed, and
            # the one that actually holds this attempt's claim. A port composed
            # here would be a second Authority view of the same participant.
            authority=self.authority, assignment_port=operations.port,
            profile=self.integration_profile, checkpoint_profile=self.profile,
            object_runner=self.integration_object_runner,
            line_id=line_id, proposal_id=proposal_id,
            canonical_target_id=canonical_target_id,
            canonical_target=self._place("integration_target")["path"],
            # AND THE DELIVERY HOME IS PROVISIONED LIKE ITS TWO SIBLINGS. The
            # port requires a directory that already exists, and where this
            # deployment's integration material lives is its own wiring -- the
            # accepted fixture made this one by hand, which is exactly the
            # operator step a production composition may not depend on.
            delivery_home=self.integration_home(INTEGRATION_HOME),
            instructions=instructions,
            identity={one: given[one] for one in
                      ("image_digest", "profile_digest", "policy_digest",
                       "adapter_digest")},
            adapter_name=given["adapter_name"],
            toolchain_digest=manifest["toolchain_digest"],
            input_manifest=manifest, engine=given["engine"],
            engine_run=self._engine_run,
            workspace_storage=given["workspace_storage"],
            workspace_group=self.workspace_group,
            # THE CAPACITY IS ALREADY THE HELD OBJECT. `single_worker._held`
            # replaces the configured integer with the capacity its own owner
            # composed, so wrapping it again would be this module composing a
            # second one over a number it did not configure.
            capacity=given["workspace_capacity"],
            bundle_home=self.integration_home(INTEGRATION_BUNDLE_HOME),
            launch_home=self.integration_home(INTEGRATION_LAUNCH_HOME),
            launch_session=INTEGRATION_LAUNCH_SESSION,
            launch_contract=given["launch_contract"],
            network=given["network"],
            credential_resolution=given["credential_resolution"],
            # THE CREDENTIAL HOME IS COMPOSED OVER THE CONFIGURED ROOT, which is
            # what that class is: "assignment-scoped, fixed, and proved when the
            # thing that holds it is built". The worker's own view is private to
            # `single_worker` and reading it from here would be this module
            # reaching into another's state; the ROOT is configuration, so the
            # view over it is composed rather than borrowed.
            credential_home=credentials.CredentialHome(
                given["credential_home"]),
            credential_provider=self._credential_provider,
            # W156162: THE SAME NARROW READER THE POOLED WORKERS ARE COMPOSED
            # WITH, over the Job store this deployment already holds. It answers
            # one Job's execution context and carries no way back to the store,
            # which is why an integration port -- a composition that opens
            # containers over somebody else's writable target -- may hold it.
            execution_context=single_worker.job_execution_reader(self.jobs))

    @property
    def reconciliation_profile(self):
        """The standalone Git profile W133117 composes results with.

        The SAME production runner this module already owns for the checkpoint
        profile, in the closed command-result shape both require.
        """
        return GitIntegrationProfile(_git_run)

    def reconciles(self):
        """Whether this deployment is wired to reconcile at all."""
        return all(self.given.get(name) is not None for name in
                   ("integration_target", "integration_workspace",
                    "integration_observer"))

    def observer_participant(self):
        configured = self.given.get("integration_observer")
        if configured is None:
            _refuse("this deployment configures no integration observer; the "
                    "owner that RUNS a reconciled result's causal harness is "
                    "not one of the three that judge what it produced",
                    category="refused", code="capability")
        return _text(configured, "the configured integration observer")

    def published_proposal(self, accepted):
        """The Authority proposal identity of an accepted checkpoint.

        DERIVED FROM THE CHECKPOINT'S OWN WRITER, so an integration reached
        after a restart names the same proposal the ending published. The
        checkpoint names its writer, the writer names its attempt, and the
        attempt's COMMITTED publication carries the proposal identity the
        Authority recorded.

        W133129: IT IS A HISTORICAL LOOKUP AND NOT A RE-COMPOSITION, and the
        two-Job traversal is what made the difference matter. `retain_proposal`
        composes the proposal manifest AGAIN, and composing one asks whether a
        proposal may be offered against the Authority's canonical target NOW --
        so once the first Job integrated and moved that target, this reader
        refused for the second Job with "a proposal is offered against the
        revision it was built from". The second Job's proposal was published
        long before, against the revision it really was built from, and asking
        for its identity is not asking to publish it again.
        `driver.publication_for_attempt` answers from the attempt alone, out of
        the journal, opening no write transaction and comparing against no
        later target -- which is the reader W121793 wrote for exactly this
        cold-selector case.

        A CHECKPOINT WHOSE ATTEMPT NEVER PUBLISHED still refuses, and says so
        as itself rather than as a stale-target complaint.
        """
        writer = review_cycles.writer_of(
            self.control,
            review_cycles.checkpoint_of(
                self.control, accepted["checkpoint_id"])["writer_id"])
        attempt_id = writer["runtime_attempt_id"]
        published = publication_for_attempt(self.control, attempt_id=attempt_id)
        if published is None:
            _refuse(f"attempt {attempt_id!r}, which wrote the accepted "
                    f"checkpoint, carries no committed publication; an "
                    f"integration names the proposal its producer actually "
                    f"published",
                    category="refused", code="precondition")
        return published["proposal_id"]

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
    carry driver-facing attributes nothing reached. The two driver methods and
    integration observation are spelled here; the rest still delegate, because the
    scheduler owns them and a member re-spelled would be a second answer to a
    question that already has one.
    """

    canonical = True

    def __init__(self, pooled, *, authority, integration, workers, given,
                 sessions=None, deployment=None, integrator=None):
        self.pooled = pooled
        # W61599: THE DEPLOYMENT'S ONE ACTIVITY INGESTION HELPER, or `None`
        # when this store already admitted one. BOUND IN `__init__` rather
        # than assigned later, because `__getattr__` delegates every unbound
        # name to the pooled surface and a partially constructed deployment
        # must be able to answer this one as its own.
        self.activity = None
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
        # THE TWO STORES A NO-CAPACITY DEPLOYMENT RE-ASKS ON EVERY RESUME.
        # [P1]: the constructor comparison in `PooledManagerOperations` is one
        # answer at one moment, and work that ARRIVES afterwards was ignored by
        # every later tick. `recover` runs on every resume, so that is where an
        # ongoing guard belongs.
        self.no_capacity_stores = None

    def __getattr__(self, name):
        # THE POOLED SURFACE IS STILL THE SURFACE for everything a stage does
        # not change: `recover`, `attach`, `drain`, `binding_intent`, `admit`,
        # `claim`, `dispatch`, `refresh_runtime`,
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

    def _nothing_unserved(self, when):
        """Ask, before anything this tick could act on. READ ONLY.

        [P1]: `PooledManagerOperations.recover` loops over the attached
        workers, so with none attached it answered an empty report no matter
        what the stores held.
        """
        if self.no_capacity_stores is None:
            return
        job_store, control_store = self.no_capacity_stores
        found = unconfigured_work(job_store, control_store)
        if found:
            _refuse_unconfigured(found, when)

    def recover(self, *, now):
        """The pooled recovery -- or a refusal, when this serves nothing.

        `reconcile` calls this ONCE, at the start of a run. That is a resume,
        and it is worth asking at, but it is not the ongoing guard -- see
        `drain`.
        """
        self._nothing_unserved("on resume")
        return self.pooled.recover(now=now)

    def drain(self, handlers, *, quiescent=()):
        """The transport drain -- and the EVERY-TICK boundary.

        REVIEW 2026-09-16T23-16-06Z [P1], and my own claim was the wrong one.
        I said `manager.reconcile` runs each tick; it does not.
        `manager.serve` calls `reconcile` ONCE and then `sweep` for every tick
        after it, so a guard that lived only in `recover` was asked once at
        startup and never again -- and an offer or a pool arriving during a
        run was met by an ordinary empty sweep.

        `sweep`'s FIRST act is `_observe`, and `_observe`'s call into these
        operations is this one. So this is the boundary every ordinary tick
        reaches, before anything that tick could observe, adopt, delegate,
        launch or converse. Asking here costs one read of two stores per tick
        and answers the question the empty report could not.

        NOT `recover` ON EVERY TICK. Recovery EXPIRES and ABANDONS, and doing
        that each tick to find out whether there is anything here would be
        settling durable state to observe it -- which is the thing this whole
        correction exists to avoid.
        """
        self._nothing_unserved("on this serving tick")
        return self.pooled.drain(handlers, quiescent=quiescent)

    # -- the owned observation and the two stage driver operations -----------

    def admit(self, stage, job=None):
        """Admit a stage, revalidating an allocation that already exists.

        W130216. `_allocation` consults the independence callback only when it
        CREATES a reservation, so on reconstruction -- a restart, a correction
        round, any tick after the first -- an allocation recorded earlier is
        used with nothing re-deriving whether that worker still serves this
        Job. The callback cannot answer for a reservation it was never asked
        about, so the recorded identity is checked HERE, where this assembly
        already owns the admission, and the scheduler keeps its own operation.

        A COMPATIBLE RECORD IS NOT RE-RESERVED. This adds no allocation and
        removes none; it refuses to admit against an allocation that disagrees
        with the Job, which is exactly the wrong-setup this boundary exists to
        precede.
        """
        deployment = self.deployment
        if deployment is not None and hasattr(deployment, "binding_for") \
                and stage.get("job_id") is not None:
            recorded = allocation_of(self.pooled.store, stage["attempt_id"])
            if recorded is not None:
                _binding, compatible = _job_workers(deployment, stage, job)
                if recorded["worker_id"] not in {one["worker_id"]
                                                 for one in compatible}:
                    _refuse(
                        f"stage {stage.get('stage_id')!r} already holds an "
                        f"allocation to worker {recorded['worker_id']!r}, "
                        f"which cannot serve Job {stage['job_id']!r}; a "
                        f"reservation made before this deployment bound the "
                        f"Job is not admitted merely because it exists",
                        category="refused", code="precondition")
        return (self.pooled.admit(stage) if job is None
                else self.pooled.admit(stage, job))

    def observe(self, stage):
        return dict(self.pooled.observe(stage), integration=self.integrator.observe(stage))

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
        # W61599: INGESTION STOPS FIRST. It is the one handle here that writes
        # to the control store from a thread of its own, and everything below
        # is a release; a helper still reading a delivery whose worker has been
        # torn down is a diagnostic outliving the thing it observes. An
        # over-bound stop leaves the helper's own store handle open and its
        # admission held, and `release` reports that through the same collected
        # refusal as any other failed closer -- an operator is told rather than
        # the fact being swallowed.
        if self.activity is not None:
            yield ("the activity ingestion helper",
                   lambda: single_worker.activity_release(self.activity))
        for active in getattr(self.integrator, "managed_runtimes", {}).values():
            yield "the managed apply worker", active.close
        # WHAT A FAILED OBSERVATION LEFT BEHIND, FIRST. It is this
        # deployment's own scratch under its own integration root, and it is
        # released before the handles because a store or Authority failure
        # must not be what decides whether the bytes are cleaned up. A path
        # that survives THIS attempt too is reported through the same failure
        # list as any other handle -- an operator is told, rather than the
        # tree being quietly abandoned a second time. See `_host_scratch`.
        # IT IS READ OFF THE DEPLOYMENT, which is where the owners that made
        # it registered it; this object is what opened that deployment and so
        # is what releases what it left.
        surviving = getattr(self.deployment, "_host_surviving_scratch", None)
        if surviving:
            def dispose():
                left = _dispose_surviving(surviving)
                if left:
                    _refuse("it could not be disposed of",
                            category="unavailable", code="transport")

            # THE PATHS ARE IN THE LABEL, because `release` reports a failed
            # closer by its NAME and the type of its error. A surviving tree
            # an operator cannot locate is the silence this Work refuses.
            yield ("the retained host scratch at "
                   + ", ".join(repr(one) for one in sorted(surviving))), \
                dispose
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


def _git_run(argv, *, input=None):
    """The production Git runner, in the closed shape the profile requires."""
    import subprocess

    answer = subprocess.run(list(argv), input=input, capture_output=True, check=False,
                            timeout=GIT_SECONDS)
    return {"returncode": answer.returncode,
            "stdout": answer.stdout.decode("utf-8", "replace"),
            "stderr": answer.stderr.decode("utf-8", "replace")}


def _export_run(argv, *, directory):
    """The runner the PREPARATION INPUT PRODUCER requires, which is not
    `_git_run`.

    TWO CONTRACTS, MEASURED APART. The checkpoint profile's runner takes no
    working directory and answers DECODED streams; `compose_preparation_input`
    runs a bounded read-only export in a directory it chose and needs EXACT
    BYTES, because candidate content is not text and a decoded stream has
    already lost it. I passed the profile's runner and the real traversal
    raised `TypeError: _git_run() got an unexpected keyword argument
    'directory'` at the first managed admission -- a mismatch no reading of
    either signature had caught.
    """
    import subprocess

    answer = subprocess.run(list(argv), cwd=directory, capture_output=True,
                            check=False, timeout=GIT_SECONDS)
    return {"returncode": answer.returncode, "stdout": answer.stdout,
            "stderr": answer.stderr}


def _producer_of(given, binding):
    """The configured worker this Job binds its source and its input to."""
    for one in given["workers"]:
        if one["worker_id"] == binding["source_worker_id"]:
            return one
    _refuse(f"Job {binding['job_id']!r} binds its source to worker "
            f"{binding['source_worker_id']!r}, which this deployment does not "
            f"configure", category="refused", code="precondition")


def _served_deployment(given, worker, binding):
    """The held deployment this worker actually serves THIS Job's stage under.

    W130216 review [P1]. THE INTEGRATION ROLE IS THE ONE THAT CANNOT BE
    CONFIGURED PER JOB, and that is a fact about the deployment rather than a
    gap in a fixture: one deployment names one `integrator_participant`, the
    integration profile, the delivery and all four receipt sessions belong to
    that actor, and `scheduler.own_pool` gives one participant one pool worker.
    So a second Job's integration stage can get neither a second configured
    worker nor a second actor.

    WHAT IS PER JOB IS THE OPERAND SET AND NOT THE CAPACITY. A Job's
    integration stage carries that Job's Work and that Job's submitted input,
    and both are already named by the producer the binding names -- the same
    `source_worker_id` `Integration.required_tests` derives its selection from,
    and the same manifest `_correspondent` compares the Job's own input digest
    against. So the integrator's manifest for a Job IS its producer's, derived
    here, read by `_job_workers` for compatibility and composed by
    `_integration_operations` into that Job's own operations -- one document,
    so admission and the provider cannot disagree about it.

    AND NOTHING ELSE IS DERIVED. The participant, the principal, the profile
    and the policy digest stay the one configured deployment fact: substituting
    a policy or a profile for a Job would be this assembly quietly choosing a
    security operand, which is the invisible choice `ManagerOperations.admit`
    names in as many words. A Job whose policy or profile the configured
    integrator does not carry is still refused before anything is reserved,
    naming which operand disagreed.

    THE ONE-JOB DOCUMENT DERIVES NOTHING. It says its Work, its base and its
    target once, globally, and its integration worker's own deployment is that
    fact rather than a second copy of it.
    """
    held = worker["deployment"]
    if worker["role"] != "integration" or binding["job_id"] is None:
        return held
    # W130224: THE MANIFEST AND THE TASK IT NAMES MOVE TOGETHER. `_held`
    # proves the configured task document's bytes against the manifest's own
    # human contract, so a derived document carrying this Job's manifest
    # beside another Job's task bytes would be one that validator would never
    # have accepted -- inert for a role that mounts nothing, and exactly the
    # kind of half-derived document a later reader is entitled to trust.
    producer = _producer_of(given, binding)["deployment"]
    return dict(held, input_manifest=producer["input_manifest"],
                task_document=producer["task_document"],
                task_bytes=producer["task_bytes"])


def _disagreements(given, stage, job, binding):
    """Every operand of this deployment that disagrees with this Job and stage.

    THESE ARE `single_worker._matches`'S OWN OPERANDS, in its own order, read
    from the held deployment the stage is actually SERVED under rather than
    restated. That provider still holds every one of them after allocation and
    is not weakened; assembly's part is to stop handing it a worker that must
    then refuse.
    """
    manifest = given["input_manifest"]
    named = {"the stage kind": (given["launch_role"], stage.get("kind")),
             "the Work": (manifest["work_ref"]["work_id"],
                          binding["job_work_id"]),
             "the workload profile": (given["profile_name"],
                                      stage.get("profile_name")),
             "the workload profile digest": (given["profile_digest"],
                                             stage.get("profile_digest")),
             # W202663: THE JOB-SCOPED PROJECTION. This is the rule that
             # decides WHICH configured workers may serve a Job's stage, so
             # comparing a worker's whole manifest digest here is what actually
             # excluded every heterogeneous pool: a review or integration
             # worker on its own image disagreed about "the submitted input"
             # and was filtered out before anything could refuse it out loud.
             # Everything else in this table still compares whole.
             "the submitted input": (job_input_identity(
                 manifest, what="a configured worker's input"),
                                     job["input_digest"]),
             "the submitted policy": (given["policy_digest"],
                                      job["policy_digest"])}
    return {what: pair for what, pair in named.items() if pair[0] != pair[1]}


def _job_workers(deployment, stage, job=None):
    """The configured workers this Job's stage could actually be served by.

    W130216. The predecessor derived compatibility ONLY for the implementation
    kind: review and integration got an empty exclusion list after a single
    Work comparison, so a review worker configured for Work A was reserved for
    a Job on Work B and `single_worker` refused it only afterwards -- leaving a
    RESERVED allocation holding capacity for a stage that can never be served.
    EVERY ROLE IS DERIVED HERE, by the one rule, and a Job with no compatible
    worker for its stage is refused before anything is reserved for it.
    """
    binding = deployment.binding_for(stage["job_id"])
    if job is None:
        job = job_of(deployment.jobs, stage["job_id"])
    # THE JOB'S OWN HELD IDENTITY, not the deployment's global one.
    if stage.get("work_id") not in (None, binding["job_work_id"]):
        _refuse(f"stage {stage.get('stage_id')!r} names Work "
                f"{stage.get('work_id')!r} and Job {stage['job_id']!r} is "
                f"bound to {binding['job_work_id']!r}; a Job's Work is a fact "
                f"about the Job and not about whichever worker is free",
                category="refused", code="precondition")
    lane = [one for one in deployment.given["workers"]
            if one["role"] == stage.get("kind")]
    # THE DOCUMENT EACH ONE WOULD ACTUALLY SERVE THIS JOB UNDER, which is its
    # configured deployment for every role but integration, and that role's
    # per-Job operand set for integration. `_integration_operations` composes
    # the provider from the same derivation, so a worker admitted here is one
    # whose own validator holds the operands this compared.
    served = {one["worker_id"]: _served_deployment(deployment.given, one,
                                                   binding) for one in lane}
    compatible = [one for one in lane
                  if not _disagreements(served[one["worker_id"]], stage, job,
                                        binding)]
    # THE IMPLEMENTATION KIND IS ALSO BOUND BY IDENTITY. A Job names its
    # producer, and another worker that merely agrees on every digest is still
    # some other Job's source.
    if stage.get("kind") == "implementation":
        compatible = [one for one in compatible
                      if one["worker_id"] == binding["source_worker_id"]]
    # AND THE INTEGRATION KIND IS SCOPED TO THE CONFIGURED ACTOR. One
    # deployment names one `integrator_participant`, and the integration
    # profile, the four receipt sessions and the delivery all belong to that
    # actor -- so an integration worker under any other participant could be
    # reserved and then have no session able to act for it. This constrains
    # eligibility to the actor already configured; it grants no second
    # integrator and no new profile or driver capability.
    if stage.get("kind") == "integration":
        actor = deployment.given["integration_profile"]["integrator_participant"]
        compatible = [one for one in compatible
                      if one["deployment"]["participant"] == actor]
    if not compatible:
        disagreeing = {one["worker_id"]:
                       sorted(_disagreements(served[one["worker_id"]], stage,
                                             job, binding))
                       for one in lane}
        _refuse(f"no worker this deployment configures for the "
                f"{stage.get('kind')!r} stage can serve Job "
                f"{stage['job_id']!r}: {disagreeing or 'none is configured'}. "
                f"Assembly supplies coherent operands rather than reserving a "
                f"worker that must then refuse them, which would hold that "
                f"worker's capacity for a stage nobody can serve",
                category="refused", code="precondition")
    return binding, compatible


def _job_eligibility(composed):
    """Job-compatible worker exclusions, derived BEFORE the reserve.

    The seam is the one already there: `PooledManagerOperations(...,
    independence=)` is called by `_allocation` with the stage BEFORE `reserve`,
    and `reserve` accepts excluded worker ids. So this is where a Job this
    deployment binds nothing for, and a role-compatible but JOB-incompatible
    worker, both stop being reservable -- ahead of any allocation, offer or
    setup, which is the accepted before-wrong-setup boundary.

    THE EXCLUSIONS COMBINE WITH the scheduler's own review independence,
    affinity and principal capacity rules rather than replacing them, and
    selection stays with its current owner.
    """
    def eligibility(stage):
        deployment = composed.deployment
        _binding, compatible = _job_workers(deployment, stage)
        keeping = {one["worker_id"] for one in compatible}
        return {"worker_ids": sorted(
            one["worker_id"] for one in deployment.given["workers"]
            if one["worker_id"] not in keeping)}

    return eligibility


class _PerJobIntegration:
    """ONE integration capacity identity, one held operand set per bound Job.

    W130216 review [P1]. The pool holds a single integration worker and this
    changes none of that: one worker id, one participant, one canonical
    principal, one reservation at a time, so two Jobs' integration stages
    serialize over the same capacity exactly as `scheduler.reserve` decides.
    What this selects among is the OPERANDS -- `single_worker` holds a stage
    to its deployment's own Work, input, profile and policy, and those are
    facts about the Job rather than about the actor -- so a stage reaches the
    operations composed for ITS Job and the provider's own validator is left
    holding every one of its six checks.

    THE SHARED HALF IS ASKED OF ONE OF THEM RATHER THAN OF ALL. The canonical
    operation identity, the journal read, the restart settlement, the offer
    republication and the transport pump are answers about one control store
    and one participant, and every entry here is that same pair. Asking each
    would run the manager's restart rules once per Job and pump a queue
    nothing ever published into, which is why `attach` and `drain` in
    particular must name the same entry.
    """

    canonical = True

    def __init__(self, held):
        self.held = dict(held)
        self.shared = self.held[sorted(self.held)[0]]
        self.port = self.shared.port

    @property
    def _worker(self):
        """The launch composition these per-Job operations share.

        Every entry is the same participant, principal, profile, launch role
        and control store; only the Job's own input manifest differs. A reader
        asking an operations object what it composes wants that shared answer,
        and one of them IS it rather than a sixth thing beside them.
        """
        return self.shared._worker

    def _serving(self, stage):
        job_id = stage.get("job_id")
        held = self.held.get(job_id)
        if held is None:
            _refuse(f"stage {stage.get('stage_id')!r} names Job {job_id!r} and "
                    f"this deployment composes integration operands for "
                    f"{sorted(self.held)}; an integration stage is served "
                    f"under its own Job's Work and submitted input, so one "
                    f"this deployment binds nothing for is refused rather "
                    f"than served under another Job's manifest",
                    category="refused", code="precondition")
        return held

    # -- the answers that are about this deployment, not about a stage -------

    def canonical_operation(self, act, offer_id):
        return self.shared.canonical_operation(act, offer_id)

    def receipt_of(self, operation_id):
        return self.shared.receipt_of(operation_id)

    def binding_intent(self, stage, job):
        return self.shared.binding_intent(stage, job)

    def recover(self, *, now):
        return self.shared.recover(now=now)

    def attach(self, offer_ids):
        return self.shared.attach(offer_ids)

    def drain(self, handlers, *, quiescent=()):
        return self.shared.drain(handlers, quiescent=quiescent)

    # -- and the ones that are about one Job's stage -------------------------

    def admit(self, stage, job):
        return self._serving(stage).admit(stage, job)

    def claim(self, stage):
        return self._serving(stage).claim(stage)

    def launch(self, stage, job):
        return self._serving(stage).launch(stage, job)

    def dispatch(self, stage, job):
        return self._serving(stage).dispatch(stage, job)

    def conclude(self, stage, job):
        return self._serving(stage).conclude(stage, job)

    def observe(self, stage):
        return self._serving(stage).observe(stage)

    def refresh_runtime(self, stage):
        return self._serving(stage).refresh_runtime(stage)

    def close(self):
        for _job_id, one in sorted(self.held.items()):
            one.close()


def _integration_ports(given, supplied):
    """The integration runtime port each bound Job's stage is started by.

    W130224. `integration_worker.IntegrationRuntimePort` is composed over ONE
    accepted development line, ONE published proposal and ONE canonical
    target, and every one of those is a fact about a JOB rather than about a
    deployment -- which is exactly why the one-Job composition could not carry
    a second one. So the injected capability is per Job here, in the one shape
    that keeps the operator supplying what it already supplies: one port,
    composed exactly as it is today, named by the Job it belongs to.

    A SINGLE BARE PORT IS STILL THE ONE-BINDING SPELLING and nothing about it
    changes. Under several bindings it is REFUSED rather than reused, because
    reusing it is the global fallback this campaign exists to remove: the
    second Job's integration would materialize the FIRST Job's line against
    the first Job's target under this Job's assignment, and the port cannot
    detect a cross-wire it was told about.

    THIS COMPOSES NO PORT AND GRANTS NO NEW CAPABILITY. It selects among
    objects the operator resolved, exactly as `_integration_operations`
    selects among held operand sets over one configured worker.
    """
    bound = [binding["job_id"] for binding in given["job_bindings"]]
    if supplied is None:
        return {job_id: None for job_id in bound}
    if type(supplied) is dict:
        unknown = sorted(one for one in supplied if one not in bound)
        if unknown:
            _refuse(f"integration runtime ports were supplied for Jobs "
                    f"{unknown} that this deployment binds nothing for; a "
                    f"port is bound to one Job's accepted line, proposal and "
                    f"target", category="refused", code="precondition")
        return {job_id: supplied.get(job_id) for job_id in bound}
    if len(bound) != 1:
        _refuse(f"this deployment binds {len(bound)} Jobs and one integration "
                f"runtime port was supplied for all of them; a port is "
                f"composed over one accepted line, one published proposal and "
                f"one canonical target, so a deployment serving several is "
                f"handed one per Job keyed by its Job id rather than running "
                f"a second Job's integration against the first Job's line",
                category="refused", code="precondition")
    return {bound[0]: supplied}


class PreparationResolver:
    """W161230 A.4: one Job's managed preparation operands, from THIS
    deployment's own readers.

    THE COMPOSER IS WHERE THE OWNERS LIVE. `integration_worker` composes the
    request and enforces its rules; what it cannot do is know which line this
    Job is on, which proposal its producer published, what the Authority's
    canonical target is now, or what the Job configured -- those are the
    deployment's readers, and a wrapper that reached for them would be a second
    resolver disagreeing with `Integration._run` about the same facts.

    IT IS RECOVERY-FIRST, which is review claim169347's correction made
    structural. The committed intent arrives as an operand: when there is one,
    this resolves NOTHING -- no canonical target, no publication -- and hands
    back the operands built from the child Work the intent already decided, so
    `ManagedPreparation` can recover the published request. Only a first sweep
    reads the Authority's current target and publishes, because only a first
    sweep is deciding anything.
    """

    __slots__ = ("_deployment", "_worker", "_required", "_clock")

    def __init__(self, deployment, *, worker, required_tests):
        self._deployment = deployment
        # THE INTEGRATION WORKER'S OWN CONFIGURED IDENTITIES. Review
        # claim169477: I had used the producer's input-manifest digest as the
        # worker profile, which is a different owner's answer to a different
        # question. The participant, the profile and the policy this child runs
        # under are the ones this deployment configured its integration worker
        # with, and they are read from that document.
        self._worker = worker
        # AND `required_tests` IS `Integration`'s, NOT the deployment's. I
        # called `deployment.required_tests` and it does not exist; the
        # integrator owns that derivation, so it is injected rather than
        # reached for.
        self._required = required_tests
        self._clock = getattr(deployment, "judgment_clock", None) or _now

    def orchestration(self, stage, job):
        """WHICH ORCHESTRATION, answered from the stage alone.

        Cheap on purpose: `ManagedPreparation` reads the committed intent
        before anything is resolved, so this may not resolve anything either.
        One integration stage attempt is one orchestration.
        """
        del job
        return "integration:" + stage["attempt_id"]

    def published_root(self, orchestration_id):
        """Where this orchestration's input is published, and its HOME.

        `compose_preparation_input` requires the destination NOT to exist -- a
        bundle is published once and never appended to -- but its parent must,
        and nothing else creates it. Measured on the real traversal: the first
        managed admission raised `FileNotFoundError` writing into an absent
        `integration-bundles`, so the home is established here and the
        destination is left for the producer to create.
        """
        home = os.path.join(self._deployment.integration_root,
                            INTEGRATION_BUNDLE_HOME)
        os.makedirs(home, exist_ok=True)
        return os.path.join(home, orchestration_id.replace(":", "-"))

    def identity(self, required):
        """What the child's runtime attempt is RECORDED under.

        `_SingleWorker.start` records an attempt from its own configured
        deployment -- adapter, image, profile, policy, input manifest and its
        toolchain -- and this is that same document for the child, read from
        the integration worker's own configuration. Nothing is derived: a
        composition that invented an adapter, an image or a toolchain would be
        recording an attempt about a runtime nobody configured.
        """
        held = self._worker
        manifest = held["input_manifest"]
        del required
        return {"adapter_name": held["adapter_name"],
                "adapter_digest": held["adapter_digest"],
                "profile_digest": held["profile_digest"],
                "input_digest": manifest["manifest_digest"],
                "policy_digest": held["policy_digest"],
                "image_digest": held["image_digest"],
                "toolchain_digest": manifest["toolchain_digest"]}

    def contract(self):
        """The assignment contract this deployment's child Work is created
        under, bound rather than defaulted.

        Review claim169999 measured what defaulting costs: operands omitted it,
        `create_work` took `contract=None`, and the Authority committed a claim
        WITH NO GENERATION. The manager's port owns a CLOSED claim result --
        assignment, the authority's immutable claim event, its authorization
        decision -- and a v11 assignment tuple mints no such event, so the
        operand exists precisely so a composition says which contract it means.

        IT IS THIS DEPLOYMENT'S CONFIGURED ONE and not a constant of mine:
        `baton_v12.authority.identity.V12` is the contract this build's own
        manager fences against, read from that owner rather than spelled here.
        """
        from baton_v12.authority.identity import V12

        return V12

    def apply_task_digest(self):
        """THE STABLE MATERIAL THE APPLY IS ASKED TO EXECUTE, measured.

        Review claim169546 answered the ownership question I returned: the
        digest names STABLE TASK MATERIAL, not the later self-containing
        envelope, so the absent collected digest never made it impossible --
        `managed_task` takes the two separately and capacity binds the
        collected content at admission, not at planning.

        THE MATERIAL IS THIS DEPLOYMENT'S OWN CONFIGURED INTEGRATION WORKLOAD
        DOCUMENT, held as exact immutable bytes. `single_worker._task_bytes`
        reads it once during static configuration -- before the Authority is
        opened, before an offer exists -- and the constructed deployment
        carries the BYTES rather than the path, so what a later apply is asked
        to obey cannot change underneath this measurement.

        AND IT IS THIS WORKER'S OWN, not the producer's. `_served_deployment`
        swaps the producer's manifest and task into the per-Job view so the
        integration role knows which implementation it is integrating; that is
        the material being integrated, not the instructions the apply executes.
        Hashing it here would name the wrong document with a plausible digest.

        ABSENCE REFUSES rather than defaulting: a phase label, a constant, the
        required-test digest or an invented future content digest are none of
        them the material the apply must later obey.
        """
        from baton_v12.contracts import digest_of_bytes

        held = self._worker.get("task_bytes")
        if not isinstance(held, bytes) or not held:
            _refuse("this deployment's integration worker holds no configured "
                    "task bytes; the apply phase is planned under the digest "
                    "of the material it will be asked to execute, and there "
                    "is none to measure",
                    category="refused", code="capability")
        return digest_of_bytes(held)

    def required(self, stage, job_id):
        """The required-test selection, from the INTEGRATOR's derivation."""
        del stage
        return self._required(job_id)

    def harness_digest(self, accepted, line):
        from baton_v12.contracts import digest_of_bytes

        answer = _export_run(["git", "show", accepted["evidence"]["head"] + ":harness.py"],
                             directory=line["line_path"] or line["source_path"])
        if answer["returncode"] != 0:
            _refuse("the accepted candidate has no preparation harness.py", category="refused", code="precondition")
        return digest_of_bytes(answer["stdout"])

    def request(self, orchestration_id, accepted, line, job_id, required,
                stage, job):
        """The request as it goes IN to publication -- with no input digest.

        That member is `compose_preparation_input`'s answer, not an operand:
        supplying one would assert a measurement this composition did not take.
        """
        from baton_v12.integration import managed_execution
        from . import integration_worker

        deployment = self._deployment
        return {
            "schema": managed_execution.REQUEST_SCHEMA,
            "orchestration_id": orchestration_id,
            "canonical_target_id": (
                _global(deployment, "canonical_target_id",
                        "canonical target") if job_id is None
                else deployment.target_for(job_id)),
            "job_id": job_id, "line_id": line["line_id"],
            "source_proposal_id": deployment.published_proposal(accepted),
            "source": {"base": accepted["evidence"]["base"],
                       "candidate": accepted["evidence"]["head"],
                       # PINNED HERE AND NEVER AGAIN. A first sweep reads the
                       # Authority's canonical target once; every later sweep
                       # recovers this document instead of asking again.
                       "target_revision": _authority_read(
                           "the canonical target",
                           lambda: deployment.authority.canonical_target())},
            "authority": {
                "path_set_digest": accepted["evidence"]["path_set_digest"],
                "test_scope_digest": required["task_digest"]},
            "harness_digest": self.harness_digest(accepted, line),
            # THE INTEGRATION WORKER'S OWN CONFIGURED PROFILE, not the
            # producer's input-manifest digest -- a different owner's answer
            # to a different question, which is what review claim169477
            # refused.
            "profile_digest": self._worker["profile_digest"],
            "execution_limits": self.limits(stage, job, job_id),
            "commands": list(integration_worker.CAUSAL_COMMANDS)}

    def limits(self, stage, job, job_id):
        """The Job's own admitted configuration, travelling with the work.

        EVERY OPERAND THE READER REQUIRES, and review claim169477 measured the
        alternative: I called it positionally and it takes four keyword-only
        operands, so it raised `TypeError` at the first real call. The attempt
        and the two runtime digests are the stage's and the Job's own, read
        here rather than defaulted.
        """
        from baton_v12.job_manager import execution_limits

        if job_id is None:
            return execution_limits.resolved({}, 1)
        reader = single_worker.job_execution_reader(self._deployment.jobs)
        context = reader(job_id=job_id, attempt_id=stage["attempt_id"],
                         runtime_input_digest=job["input_digest"],
                         runtime_policy_digest=job["policy_digest"])
        if context is None:
            return execution_limits.resolved({}, 1)
        return context.get("execution_limits") or execution_limits.resolved(
            {}, 1)

    def __call__(self, stage, job, intent):
        """THE BRANCH IS FIRST, and review claim169477 caught me claiming it
        was when it was not: `line`, the accepted checkpoint and the
        required-test selection all ran BEFORE the intent test, so "resolves
        nothing" was false of my own code. A resumed sweep now reads nothing
        but its own committed decision.
        """
        from . import integration_bundle, integration_worker

        orchestration_id = self.orchestration(stage, job)
        place = self.published_root(orchestration_id)
        if intent is not None:
            # RECOVERED, NOT RESOLVED. The plan the intent committed carries
            # this child's participant and digests, so nothing here asks the
            # line, the checkpoint, the Authority or the Job again.
            return self.resumed(intent, place)
        deployment = self._deployment
        job_id = _bound_id(deployment, stage, job)
        line = (deployment.line() if job_id is None
                else deployment.line_for(job_id))
        accepted = review_cycles.integration_checkpoint(deployment.control,
                                                        line["line_id"])
        if accepted is None:
            _refuse(f"development line {line['line_id']!r} holds no accepted "
                    f"integration checkpoint; a managed preparation runs "
                    f"behind an accepted verdict and never ahead of one",
                    category="refused", code="precondition")
        required = self.required(stage, job_id)
        # PUBLICATION BEFORE INTENT IS A RECOVERY CUT, NOT A COLLISION.
        #
        # Review claim169913 measured it: a sweep that published the immutable
        # input and then failed before committing the intent leaves a bundle
        # with no decision behind it, and the next sweep's
        # `compose_preparation_input` refuses -- correctly, since a bundle is
        # published once and never appended to. Deleting or rewriting it to get
        # past that would destroy the one durable record of what was asked. So
        # an existing publication is RECOVERED and reused.
        # AN ABSENT DESTINATION IS "NOTHING PUBLISHED", and it is asked for
        # separately because the reader deliberately does NOT say so: an absent
        # directory refuses at its reachability boundary, which is the right
        # answer when a committed intent expected a publication and the wrong
        # one on a first sweep that has published nothing yet. Measured: the
        # first managed admission refused "not reachable" on every tick.
        held = (integration_bundle.published_preparation_request(place)
                if os.path.isdir(place) else None)
        if held is None:
            published = integration_bundle.compose_preparation_input(
                place, request=self.request(orchestration_id, accepted, line,
                                            job_id, required, stage, job),
                runner=_export_run,
                repository=line["line_path"] or line["source_path"])
        else:
            published = {"request": held,
                         "input_digest": held["input_digest"]}
        return integration_worker.preparation_operands(
            orchestration_id=orchestration_id,
            execution_work_id=integration_worker.preparation_child_work(
                deployment.jobs.authority_uuid, orchestration_id),
            execution_route=PREPARATION_ROUTE,
            participant=self._worker["participant"], accepted=accepted,
            proposal_id=deployment.published_proposal(accepted),
            canonical_target_id=published["request"]["canonical_target_id"],
            job_id=job_id, line_id=line["line_id"],
            target_revision=published["request"]["source"]["target_revision"],
            test_scope_digest=required["task_digest"],
            harness_digest=published["request"]["harness_digest"],
            profile_digest=self._worker["profile_digest"],
            policy_digest=self._worker["policy_digest"],
            profile_name=self._worker["profile_name"],
            apply_task_digest=self.apply_task_digest(),
            limits=self.limits(stage, job, job_id), published=published,
            published_root=place,
            accept=None,
            identity=self.identity(required), contract=self.contract())

    def resumed(self, intent, place):
        """The operands a RESUMED sweep admits with, from the intent alone.

        Its committed plan already names this child's participant and digests,
        so they are read back rather than re-derived; the request, its digest
        and its input digest are left for `ManagedPreparation._recovered` to
        take from the durable publication.
        """
        from . import integration_worker

        planned = [one for one in intent["plan"]
                   if one["phase"] == integration_worker.PREPARATION_PHASE]
        if len(planned) != 1:
            _refuse(f"the committed intent for "
                    f"{intent['orchestration_id']!r} names "
                    f"{len(planned)} preparation phases; a resumed sweep "
                    f"recovers one decision",
                    category="integrity", code="schema")
        [held] = planned
        applying = [one for one in intent["plan"] if one["phase"] == "apply"]
        return {"orchestration_id": intent["orchestration_id"],
                "execution_work_id": intent["execution_work_id"],
                "execution_route": intent["execution_route"],
                "participant": held["participant"],
                "execution_attempt_id": held["execution_attempt_id"],
                "execution_offer_id": held["execution_offer_id"],
                "apply_task_digest": (applying[0]["task_digest"] if applying
                                      else self.apply_task_digest()),
                "profile_digest": held["profile_digest"],
                "policy_digest": self._worker["policy_digest"],
                "profile_name": self._worker["profile_name"],
                "published_root": place,
                "accept": None,
                "identity": self.identity(None),
                # AND ON RECOVERY TOO. A resumed sweep whose creation replays
                # must replay under the SAME contract; a differing one is an
                # operation collision, which is the protection working rather
                # than a nuisance.
                "contract": self.contract(),
                "request": None, "task_digest": None, "input_digest": None}


class PreparationRuntime:
    """Compose one ordinary child runtime; consume only its retained result."""

    def __init__(self, deployment, worker, authority, provider, engine_run, clock):
        self.deployment = deployment
        self.worker = worker
        self.authority = authority
        self.provider = provider
        self.engine_run = engine_run
        self.clock = clock
        self.operations = {}

    def configure(self, held):
        import copy
        from baton_v12.contracts import digest, digest_of_bytes
        from baton_v12.worker_manager import source_boundary

        manifest = copy.deepcopy(self.worker["input_manifest"])
        manifest["work_ref"]["work_id"] = held["execution_work_id"]
        body = json.dumps(held["request"], sort_keys=True).encode()
        manifest["human_contract"] = dict(
            manifest["human_contract"], artifact_id=held["execution_work_id"],
            locator="artifact://contracts/" + held["execution_work_id"],
            bytes=len(body), content_digest=digest_of_bytes(body))
        output = manifest["outputs"][0]
        manifest["outputs"] = [dict(output, name=name, path=name, type="directory-result", required=True)
                               for name in ("preparation-report", "prepared-candidate", "prepared-objects")]
        manifest["sources"][0]["consumption"] = source_boundary.source_consumption("generic")
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        given = dict(self.worker, input_manifest=manifest, task_bytes=body,
                     source_nomination=source_boundary.nominate_source(held["published_root"]))
        return dict(held, input_digest=manifest["manifest_digest"],
                    apply_input_digest=self.deployment.integration_served(held["request"]["job_id"])["input_manifest"]["manifest_digest"],
                    retention_policy_digest=given["retention_policy_digest"],
                    identity=dict(held["identity"], input_digest=manifest["manifest_digest"]),
                    runtime_configuration=given)

    def close(self):
        for operations in self.operations.values():
            operations.close()
        self.operations.clear()

    def parent_ready(self, held, stage, job):
        from baton_v12.integration.reconciliation import retained_managed_preparation, managed_result_of
        from baton_v12.job_manager.integration_capacity import integration_capacity_of

        result_id = held["orchestration_id"]
        preparation = retained_managed_preparation(self.deployment.integration, result_id)
        capacity = integration_capacity_of(self.deployment.jobs, result_id)
        members = {one["phase"]: one for one in capacity["members"]}
        if members["prepare"]["state"] != "ended" or members["prepare"]["outcome"] != "succeeded" or members["apply"]["execution_attempt_id"] != stage["attempt_id"]:
            _refuse("the parent cannot continue before its actual preparation ends")
        if self.authority.assignment_of(preparation["assignment"]["work_ref"]["work_id"]) is not None:
            _refuse("the preparation still holds its child assignment")
        result = managed_result_of(self.deployment.integration, result_id)
        if result["state"] == "blocked":
            from baton_v12.job_manager.integration_capacity import settle_failed_integration
            settle_failed_integration(self.deployment.jobs, self.deployment.control, orchestration_id=result_id, phase="prepare", coordinator=self.deployment.integration)
            _refuse("the preparation failed causal verification; the parent settled exceptionally", category="refused", code="precondition")
        return True

    def _operations(self, held):
        attempt = held["execution_attempt_id"]
        operations = self.operations.get(attempt)
        if operations is None:
            operations = single_worker.worker_operations(
                held["runtime_configuration"], self.deployment.control,
                self.authority, self.provider, engine_run=self.engine_run,
                clock=self.clock, dispose=lambda: None,
                execution_context=single_worker.job_execution_reader(self.deployment.jobs))
            self.operations[attempt] = operations
        return operations

    def _stage(self, held):
        attempt = held["execution_attempt_id"]
        return {"stage_id": attempt, "attempt_id": attempt,
                "offer_id": held["execution_offer_id"],
                "kind": held["runtime_configuration"]["launch_role"],
                "work_id": held["execution_work_id"],
                "profile_name": held["profile_name"],
                "profile_digest": held["profile_digest"],
                "job_id": held["request"]["job_id"]}

    def _inputs(self, held):
        return {"input_digest": held["input_digest"], "policy_digest": held["policy_digest"]}

    def admit(self, held):
        return self._operations(held).admit(self._stage(held), self._inputs(held))

    def adapter(self, held):
        """The CHILD WORKER'S OWN adapter, carrying THIS attempt's deliveries.

        I COMPOSED THIS AS AN OBSERVING ADAPTER AND THAT WAS WRONG. Review
        claim172346 measured the cost: `_adapter(roots, None, None, None)` made
        `OciAdapter._torn_down` and `_launch_ended` take their not-delivered
        branches, so `authorize_failed_start_cleanup` settled and the member
        was ended while the credential root and the launch root both remained
        on disk. My comment said deliveries exist for a start and an ending
        performs none; that omitted RECOVERY and TEARDOWN of the deliveries the
        start had already created. `cleanup=retained` is about result custody
        and authorizes retaining neither of these.

        SO IT IS COMPOSED THE WAY `_SingleWorker.ending` COMPOSES IT, through
        the same owners and nothing new: the roots the launch mounted,
        `_credential` for the delivery -- or the `OrphanTeardown` capability
        when the start committed before its engine call and the materializing
        process is gone -- and `_adopted` for the launch delivery, which ADOPTS
        durable state and never authors a replacement under a container that
        may already hold the mount.
        """
        worker = self._operations(held)._worker
        stage = self._stage(held)
        attempt = held["execution_attempt_id"]
        state = attempt_runtime_of(self.deployment.control, attempt)
        roots = worker._mounted(stage, attempt, checkpoint=False)[0]
        delivery, orphan = worker._credential(attempt, state, roots)
        return worker._adapter(roots, delivery, orphan, worker._adopted(stage))

    def poll(self, held, parent, job, execution):
        from baton_v12.integration import managed_execution, reconciliation
        from baton_v12.job_manager.integration_capacity import end_integration_execution
        from baton_v12.worker_manager import assignment_of
        from . import integration_worker

        attempt = held["execution_attempt_id"]
        operations = self._operations(held)
        stage, inputs = self._stage(held), self._inputs(held)
        view = operations.observe(stage)
        state = view["runtime"]
        if state is None or state["cleanup"] not in ("complete", "retained"):
            if view["start_failure"] is not None or view["preparation_failure"] is not None:
                _refuse("the managed preparation failed preparation or start", category="refused", code="precondition")
            if state is None or state["runtime_id"] is None:
                execution.start(held["orchestration_id"], attempt,
                                lambda: operations.launch(stage, inputs))
            operations.dispatch(stage, inputs)
            operations.refresh_runtime(stage)
            terminal = (operations.observe(stage)["exchange"] or {}).get("terminal")
            if terminal is None:
                return None
            if terminal["ending"] != "answered":
                _refuse("the managed preparation did not answer its command", category="refused", code="precondition")
            operations.conclude(stage, inputs)
        end_integration_execution(self.deployment.jobs, self.deployment.control,
                                  execution_attempt_id=attempt, outcome="succeeded",
                                  exclusion="runtime-destroyed")
        request = held["request"]
        task = managed_execution.managed_task(
            phase="prepare", orchestration_id=held["orchestration_id"],
            canonical_target_id=request["canonical_target_id"],
            execution_attempt_id=attempt,
            assignment=integration_worker._admissible(assignment_of(self.deployment.control, attempt)),
            task_digest=held["task_digest"], input_digest=request["input_digest"],
            harness_digest=request["harness_digest"], execution_limits=request["execution_limits"],
            commands=request["commands"])
        body = self.report(attempt)
        return reconciliation.adopt_prepared_candidate(
            self.deployment.integration, self.deployment.jobs, self.deployment.control,
            orchestration_id=held["orchestration_id"], request=request, task=task,
            report_body=body, authority=self.authority)

    def report(self, attempt):
        from urllib.parse import unquote, urlsplit
        from baton_v12.worker_manager import frozen_output_of
        from baton_v12.worker_manager.intake import intake_receipt_of
        from baton_v12.worker_manager.manifests import load_manifest
        from baton_v12.contracts import digest_of_bytes

        control = self.deployment.control
        frozen = frozen_output_of(control, attempt)
        receipt = intake_receipt_of(control, attempt)
        if frozen is None or receipt is None or receipt["custody"] != "accepted":
            _refuse("a preparation report needs frozen output in accepted custody")
        manifest = load_manifest(control, frozen["manifest_digest"], "resultManifest")
        output = next(one for one in manifest["outputs"] if one["name"] == "preparation-report")
        artifact = next(one for one in receipt["artifacts"] if one["artifact_id"] == output["artifact"]["artifact_id"])
        locator = urlsplit(artifact["custody_locator"])
        if locator.scheme != "file" or locator.netloc or locator.query or locator.fragment:
            _refuse("the preparation consumer requires local accepted report custody")
        entries = [one for one in output["content_manifest"]["entries"] if one["path"] == "report.json"]
        if len(entries) != 1 or entries[0]["bytes"] > single_worker.MAX_CONFIG_BYTES:
            _refuse("the retained preparation needs one bounded report.json")
        fd = os.open(os.path.join(unquote(locator.path), "report.json"), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                _refuse("the retained preparation report is not a regular file")
            body = os.read(fd, entries[0]["bytes"] + 1)
        finally:
            os.close(fd)
        if len(body) != entries[0]["bytes"] or digest_of_bytes(body) != entries[0]["content_digest"]:
            _refuse("the preparation report differs from frozen custody")
        return body


# W161230 A.4: THE CLOSED SELECTION VOCABULARY, and it is closed rather than
# truthy. Review claim169661 measured the alternative: `given.get(...)` accepted
# the STRING "false" as a selection, so a deployment spelling its refusal would
# have been opted in by the spelling. A configuration value is a decision and a
# decision this build cannot place is refused rather than guessed.
PREPARATION_SELECTIONS = (True, False)


def _prepares(given):
    """Whether this deployment selects managed integration preparation."""
    held = given.get("integration_preparation", False)
    if held not in PREPARATION_SELECTIONS or not isinstance(held, bool):
        _refuse(f"a managed preparation selection is one of "
                f"{PREPARATION_SELECTIONS}; this deployment configures "
                f"{held!r}, which this build cannot place",
                category="integrity", code="schema")
    return held


def _integration_operations(given, worker, provider, control_store, authority,
                            *, engine_run, clock, checkpoint, job_store,
                            integrator=None, deployment=None):
    """The integration worker's operations, one held operand set per Job.

    ONE BINDING COMPOSES EXACTLY WHAT IT ALWAYS DID. The one-Job document
    derives nothing and gets the single operations object it has always had,
    so every accepted case reaches the same composition byte for byte; a `/2`
    document binding one Job likewise gets one, because there is nothing to
    select among.

    A PARTIAL COMPOSITION RELEASES WHAT IT ALREADY BUILT, for
    `operations_from`'s own reason: a composer that leaked the first Job's
    operations while refusing the second would leave handles nobody holds a
    reference to.
    """
    composed = []
    try:
        for binding in given["job_bindings"]:
            composed.append((binding["job_id"], single_worker.worker_operations(
                _served_deployment(given, worker, binding), control_store,
                authority, provider, engine_run=engine_run, clock=clock,
                checkpoint=checkpoint, dispose=lambda: None,
                # W156162: EVERY JOB-BOUND FACTORY GETS THE READER. Review
                # 2026-09-13T02:10:47Z: a default of `None` is a composition
                # with no Job behind it, and reading that as "this Job
                # configured nothing" would be a silent legacy fallback for a
                # Job that configured a ceiling.
                execution_context=single_worker.job_execution_reader(
                    job_store))))
    except BaseException:
        for _job_id, one in composed:
            one.close()
        raise
    # W161230 A.4: AND THE SELECTED RESERVED-BEFORE-PARENT-OFFER WRAPPER.
    #
    # `PooledManagerOperations.admit` reserves the allocation and only then
    # calls the selected worker's `admit`, so wrapping the worker here is the
    # one place where the reservation exists and the parent offer does not.
    # Review claim168871 corrected my earlier proposal to do this at
    # `Integration.reconciled`: `manager._launch` drives only stages already
    # `claimed`, so by then the parent holds this principal's one Authority
    # slot and the child preparation could never be claimed beside it.
    #
    # IT IS TRANSPARENT UNTIL A DEPLOYMENT SELECTS PREPARATION. No managed
    # preparation is composed yet, so every existing deployment gets the
    # operations it always had, method for method -- the wrapper forwards.
    # That is what makes wiring the seam now safe rather than a migration.
    from . import integration_worker

    # W161230 A.4: THE MANAGED PREPARATION, when this deployment can supply
    # every owner it needs. `integrator` answers the required tests and
    # `deployment` holds the stores, the integration root and the readers;
    # without either there is nothing to resolve from, and the wrapper stays
    # transparent rather than half-composed.
    # AND IT IS SELECTED, NOT MERELY AVAILABLE. Measured: constructing it
    # whenever the owners existed made EVERY integration stage defer its
    # parent, breaking forty-four direct and legacy cases in one run. The
    # transparency I claimed for the wrapper is only true if nothing engages
    # until a deployment ASKS for managed preparation, so the selection is an
    # explicit configured member and its absence is the ordinary path.
    #
    # AND THE WHOLE OF THE REST RELEASES WHAT IT BUILT. Review claim169661: the
    # first form wrapped and returned OUTSIDE the guard above, so a refusal
    # while constructing the port left every ordinary operations object that
    # had already been composed with nobody holding a reference to close it.
    # `operations_from`'s rule applies to the whole composition, not to its
    # first half.
    try:
        preparation = None
        if _prepares(given):
            if integrator is None or deployment is None:
                _refuse("this deployment selects managed integration "
                        "preparation and supplies no integrator or serving "
                        "deployment to resolve it from; a selected path that "
                        "silently became the ordinary one would run the "
                        "unmanaged branch under a managed configuration",
                        category="refused", code="capability")
            resolver = PreparationResolver(
                deployment, worker=worker["deployment"],
                required_tests=integrator.required_tests)
            preparation = integration_worker.ManagedPreparation(
                jobs=deployment.jobs, control=control_store,
                authority=authority,
                port=integration_worker.authority_port(
                    authority, worker["deployment"]["participant"]),
                # THE DEPLOYMENT'S OWN BEARER MINT, not a second one.
                mint_bearer=single_worker._bearer,
                orchestration=resolver.orchestration, operands=resolver,
                runtime=PreparationRuntime(deployment, worker["deployment"],
                                           authority, provider, engine_run, clock))
        held = [(job_id,
                 integration_worker.PreparationAdmission(one, preparation))
                for job_id, one in composed]
    except BaseException:
        for _job_id, one in composed:
            one.close()
        raise
    if len(held) == 1:
        return held[0][1]
    return _PerJobIntegration(dict(held))


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
    _context_roots(given, control_store)
    profile = _profile_of(given, checkpoint_profile)
    # W130224 review 2026-09-09T21-58-10Z: THE PORT BINDING IS PROVED HERE,
    # WITH EVERYTHING ELSE THIS MODULE CAN ANSWER WITHOUT WRITING. It used to
    # be resolved beside the composition, which is after `worker_preflight`
    # configured the control store and after the integration store was opened
    # -- so a deployment handed one bare port for two Jobs, or a mapping naming
    # a Job it binds nothing for, refused with durable state already changed.
    # A refusal that has already changed durable state is not a refusal; this
    # function's own opening paragraph says so, and the shape of an injected
    # capability is exactly the kind of fault it can know for free.
    ports = _integration_ports(given, integration_port)

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
                                    _bound_scope(composed.authority, given))
        # NO CAPACITY MEANS NO POOL TO PREDICT OR ACTIVATE. A pool document
        # is a list of workers, and `scheduler.own_pool` refuses an empty one
        # for the good reason that a pool nobody serves from is not a pool.
        # An instance that configures no capacity does not have one at all --
        # so nothing is activated, and `PooledManagerOperations` attaches to
        # exactly what the STORE still requires, which for a fresh instance is
        # nothing and for a store holding live work is a refusal.
        empty = _serves_nothing(given)
        if empty:
            # AT ADMISSION, and before the first durable act below. An instance
            # that cannot serve what is already here must say so rather than
            # start and report nothing.
            found = unconfigured_work(job_store, control_store)
            if found:
                _refuse_unconfigured(found, "at startup")
        pool = None if empty else _pool_generation(job_store, given, resolved)
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
        # W61599: THE STAGED DEPLOYMENT'S HELPER, admitted through the SAME
        # module-level primitive the bootstrap factory uses. Neither factory
        # has a copy of the rule, which is what makes the exclusion hold when
        # two distinct compositions are built over one control store: the
        # second finds the slot occupied, starts no helper and ingests nothing.
        # It is admitted before the workers because they are handed its
        # enqueue, and `composed.release()` below unwinds it on any failure
        # after this line.
        composed.activity = single_worker.activity_ingestion(control_store,
                                                             clock=clock)
        composed.integration = IntegrationStore.open(
            given["integration_store"],
            incarnation=_incarnation(control_store),
            clock=clock or getattr(control_store, "_now", None) or _now)
        # W103068 review 2026-09-11T02-06-10Z [P1]: THE EFFECTIVE CAPABILITIES,
        # NOT THE RAW KEYWORDS. `factory` calls this with neither, so passing
        # the keywords straight through handed the deployment `None` twice and
        # the constructed port refused for want of an engine -- on the exact
        # entry point that must work by default. The engine runner is resolved
        # through `single_worker`'s own public boundary, so an injected override
        # and the ordinary default converge on one value; the credential
        # provider is the INTEGRATION WORKER'S OWN already-resolved provider,
        # which `worker_preflight` answered above and which is the same object
        # that worker serves its stages with. Neither reaches into private
        # state and neither builds a differently configured source.
        integrator_provider = None
        for one, provider in zip(given["workers"], providers):
            if one["role"] == "integration":
                integrator_provider = provider
        deployment = StageDeployment(
            given, control=control_store, jobs=job_store,
            authority=composed.authority, integration=composed.integration,
            profile=profile, sessions=composed.sessions,
            verdict=review_verdict,
            engine_run=single_worker.effective_engine_run(engine_run),
            credential_provider=integrator_provider, clock=clock)
        composed.deployment = deployment
        for judges in (given.get("result_judgment_workers") or {}).values():
            for one in judges.values():
                deployment.judgment_providers[one["worker_id"]] = single_worker.worker_preflight(
                    one["deployment"], control_store,
                    credential_provider=credential_provider, engine_run=engine_run)
        # W103068: AND THE CONFIGURED TARGETS ARE ADOPTED. This is the first
        # act after the coordinator is open, and it is here rather than in the
        # integration branch because a target is deployment configuration: a
        # composition that only adopted a target when some Job reached
        # integration would leave the operator's own `status` unable to name
        # what this deployment was configured to write to.
        deployment.activate_targets()
        composed.publication = deployment.publication
        composed.integration_profile = deployment.integration_profile
        composed.integrator = Integration(deployment, ports)
        for one, provider in zip(given["workers"], providers):
            if one["role"] == "integration":
                # W130216: THE INTEGRATION ROLE IS COMPOSED PER BOUND JOB.
                # One worker, one actor and one capacity; the Work and the
                # submitted input it holds a stage to are the Job's own. See
                # `_served_deployment`, which `_job_workers` reads for the
                # same answer so admission and this provider cannot disagree.
                operations = _integration_operations(
                    given, one, provider, control_store, composed.authority,
                    engine_run=engine_run, clock=clock, checkpoint=checkpoint,
                    job_store=job_store,
                    # W161230 A.4: THE RESOLVER IS COMPOSED HERE BECAUSE HERE
                    # IS WHERE ITS OWNERS EXIST. `composed.integrator` owns
                    # `required_tests`, and `one["deployment"]` is the
                    # INTEGRATION worker's own configuration -- its actual
                    # apply workload bytes, kept separate from the producer's
                    # per-Job material that `_served_deployment` swaps in.
                    integrator=composed.integrator, deployment=deployment)
                # W103068: AND THE DEPLOYMENT LEARNS ITS INTEGRATION CAPACITY.
                # An integration runtime port is composed over this worker's own
                # held operands, and it cannot be composed until an accepted
                # review exists -- so what the composition keeps is the capacity
                # itself rather than a port built too early.
                deployment._integration_operations = operations
            else:
                operations = single_worker.worker_operations(
                    one["deployment"], control_store, composed.authority,
                    provider, engine_run=engine_run, clock=clock,
                    checkpoint=checkpoint,
                    stage=StageComposition(deployment, role=one["role"],
                                           worker_id=one["worker_id"]),
                    # W156162: the same reader every Job-bound factory gets.
                    execution_context=single_worker.job_execution_reader(
                        job_store),
                    # W61599: ONE HELPER PER DEPLOYMENT, SHARED BY ITS WORKERS.
                    # Ownership is at the deployment rather than at the worker
                    # -- `worker_operations` is per pooled worker and could not
                    # own a per-deployment handle -- so what each worker gets is
                    # the enqueue and never the helper.
                    activity=None if composed.activity is None
                    else composed.activity.enqueue,
                    # ONE AUTHORITY, RELEASED ONCE. A worker that disposed the
                    # shared handle would take the other two down with it.
                    dispose=lambda: None)
            composed.workers.append(dict(one, operations=operations))
        generation = (None if empty else
                      scheduler.activate_pool(job_store, pool,
                                              resolved)["generation"])
        if not empty and generation != given["pool_generation"]:
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
        if empty:
            composed.no_capacity_stores = (job_store, control_store)
        composed.pooled = PooledManagerOperations(
            job_store,
            {} if empty else {(generation, one["worker_id"]): one["operations"]
                              for one in composed.workers},
            resolved_principals=resolved,
            independence=_job_eligibility(composed))
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
    # W103068 review 2026-09-11T02-41-03Z: AND EVERY CONFIGURED JUDGMENT
    # EXECUTION, for the same reason and at the same moment. This iterated the
    # stage workers only, so a judgment execution configured for a participant
    # this Authority resolves to another principal -- or for a Work it does not
    # hold -- would have been discovered by `worker_operations` at dispatch,
    # with a control store already configured and a container about to start.
    # Every question answerable from the document and the Authority alone is
    # answered here, while nothing has been written.
    for job_id, kinds in (given.get("result_judgment_workers") or {}).items():
        for kind, one in sorted(kinds.items()):
            deployment = one["deployment"]
            who = deployment["participant"]
            what = f"Job {job_id!r}'s {kind} judgment execution"
            principal = _authority_read(
                f"{what}'s participant {who!r} is not one this Authority "
                f"resolves",
                lambda who=who: authority.principal_of(who))
            if principal != deployment["principal"]:
                _refuse(f"{what}'s participant {who!r} resolves to "
                        f"{principal!r} and its deployment is configured for "
                        f"{deployment['principal']!r}", category="refused",
                        code="capability")
            # AND THE WORK IT EXECUTES UNDER IS THIS AUTHORITY'S OWN. A
            # judgment acquires its authorized assignment through that Work, so
            # a manifest naming a Work this Authority does not project could
            # never obtain one -- and `worker_operations` makes exactly this
            # refusal later, when the message is about a launch instead of a
            # configuration.
            work_id = deployment["input_manifest"]["work_ref"]["work_id"]
            projected = _authority_read(
                f"{what}'s configured Work {work_id!r} is not one this "
                f"Authority projects",
                lambda work_id=work_id: authority.project_work(work_id))
            if projected is None \
                    or projected["authority_uuid"] != given["authority_uuid"]:
                _refuse(f"{what} names Work {work_id!r}, which is absent from "
                        f"this Authority", category="refused",
                        code="precondition")
            # AND THE ANSWER STAYS THE POOL'S. `scheduler.activate_pool` takes
            # this map and requires its keys to be EXACTLY the configured pool
            # participants, so a judgment participant added here would refuse
            # every activation -- which is the right rule, because a judge is
            # not a pool worker and holds no stage capacity. What this loop
            # contributes is the PROOF, made while nothing has been written,
            # not a member of the pool's identity map.
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

    Integration reads open only the accepted read-only Authority/coordinator
    handles and release both within that read. No session, pool activation,
    workspace allocation or runtime refresh is constructed. SQLite-managed
    sidecars follow the owner-approved opener contract.
    """

    canonical = True

    # Reuse only the configuration/allocation readers, without constructing a
    # serving deployment. Integration.account needs the same per-Job operands.
    binding_for = StageDeployment.binding_for
    works_for = StageDeployment.works_for
    target_for = StageDeployment.target_for
    worker_for = StageDeployment.worker_for

    def __init__(self, given, workers, job_store, control_store):
        self.given = given
        self.control = control_store
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

    def observe_integration(self, stage):
        """Use the same owned completion account as serving, through ro handles.

        A generic stage needs neither owner opened. Integration.account selects
        reconciled completion before checking direct-runtime prerequisites.
        Handles are local to the read, including all refusal paths, so the
        observation object carries no serving capability or disposal obligation.
        """
        if stage.get("kind") != "integration":
            return None
        authority = _authority_read("read-only integration Authority", lambda: Authority.open_readonly(
            self.given["authority_store"], expected_authority_uuid=self.given["authority_uuid"]))
        with authority:
            with IntegrationStore.open_readonly(self.given["integration_store"],
                    incarnation=_incarnation(self.control), clock=_now) as coordinator:
                context = SimpleNamespace(given=self.given, control=self.control,
                    authority=authority, integration=coordinator,
                    binding_for=self.binding_for, works_for=self.works_for,
                    target_for=self.target_for, worker_for=self.worker_for,
                    integration_profile=integration_from(self.given),
                    integration_root=os.path.join(self.given["state_root"], INTEGRATION_HOME),
                    workspace_group=configured_workspace_group(self.control))
                return Integration(context).observe(stage)


def observation_from(document, job_store, control_store, *, checkout=None):
    """Build the observation-only surface from one already-read document."""
    return StageObservation(held_configuration(document, checkout=checkout),
                            document["workers"], job_store, control_store)


def observing_factory(job_store, control_store):
    """The `status --observe` entry point, named the way `factory` is."""
    return observation_from(_configuration(), job_store, control_store)


def _context_roots(given, control):
    configs = [one["deployment"] for one in given["workers"]]
    for config in configs:
        single_worker._context_preflight(config, control)
        selected = config.get("provider_context")
        if selected is None:
            continue
        storage = selected["storage"]
        def walk(value, key=None):
            if key == "provider_context":
                return
            if type(value) is dict:
                for name, child in value.items():
                    yield from walk(child, name)
            elif type(value) is list:
                for child in value:
                    yield from walk(child)
            elif type(value) is str and value.startswith("/"):
                yield value
        for other in walk(given):
            if os.path.commonpath([storage, other]) in (storage, other):
                _refuse("context storage overlaps another role or configured root")
