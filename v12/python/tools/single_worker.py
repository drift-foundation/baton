"""One trusted production composition for one v12 implementation worker.

W76207.  The persistent Job Manager intentionally knows how to derive WHEN an
offer, claim or launch is owed and knows nothing about HOW a deployment opens
an Authority, stages input, delivers credentials or starts an OCI runtime.
This module is that missing deployment half for the bootstrap worker only.

The public factory is ``tools.single_worker:factory``.  It reads one closed
configuration document from the absolute path named by
``BATON_V12_SINGLE_WORKER_CONFIG``.  The environment carries only that path:
the offer bearer is fresh process memory and provider credential bytes are
read lazily through ``tools.user_credentials`` from the private registry path
the document names.

This is deliberately not a pool.  One configuration fixes one Authority,
participant/principal, implementation Work input, profile, OCI adapter and
workspace policy.  Anything else refuses; worker choice and capacity belong
to W71877.
"""

import json
import os
import re
import stat
import subprocess
from datetime import datetime, timezone

from baton_v12.authority import Authority, claim_signature
from baton_v12.contracts import (ContractRefusal, check_manifest_structure,
                                 check_no_durable_secret, digest,
                                 digest_of_bytes)
from baton_v12.job_manager import ManagerOperations, RefreshUnavailable
from baton_v12.worker_manager import (AuthorityPort, DISPOSITIONS,
                                      RETENTION_DISPOSITIONS, accept_offer,
                                      activate_assignment,
                                      attempt_preparation_failure_of,
                                      attempt_runtime_of,
                                      attempt_start_failure_of,
                                      authorize_cleanup, certify_profile,
                                      claimed_offers_for,
                                      configure_workspace_group,
                                      configured_workspace_group,
                                      decide_retention, label_context,
                                      load_manifest, observe,
                                      pin_boundary_identity,
                                      reconcile_runtime, record_attempt,
                                      refuse_runtime_preparation,
                                      request_freeze, request_intake,
                                      request_runtime_start, retain_manifest,
                                      boundary_identity_of)
from baton_v12.worker_manager import (credentials, exchange, launch,
                                      source_boundary, workspaces)
from baton_v12.worker_manager.oci import ENGINES, EnginePort, OciAdapter

from tools.user_credentials import SourceRefusal, UserCredentialSources

__all__ = ["CONFIG_ENV", "CONFIG_SCHEMA", "factory", "operations_from"]

CONFIG_ENV = "BATON_V12_SINGLE_WORKER_CONFIG"
# W81115 MOVED THIS TO `/2`, and its reason is kept because the rule is the
# same one applied twice. `/2` added one required member -- the frozen task
# document -- and adding a required member to a closed, version-named document
# is a NEW CONTRACT rather than a compatible reading of the old one. A `/1`
# document is refused by the equality test below rather than accepted with a
# task nobody named.
#
# W81857: SCHEMA `/3`, AND THE VERSION MOVED BECAUSE THE DOCUMENT DID AGAIN.
#
# `/3` carries three required members `/2` never had, and every one of them is
# a decision this deployment could not previously make because it had nothing
# to make it about: until now the composition started a container and stopped.
# `review_route` is where an answered, frozen, taken-into-custody result is
# handed on; `retention_policy_digest` and `retention_disposition` are what is
# decided about the untrusted bytes before that handoff. There is deliberately
# no fallback and no default for any of them -- a deployment that could end an
# attempt without saying where the result goes would be choosing a destination
# nobody named.
#
# W71917: SCHEMA `/4`, AND THE SOURCE MEMBER MEANS SOMETHING ELSE NOW.
#
# `/3`'s `input_source` was an ALREADY-STAGED directory this deployment
# measured and COPIED into the input root. `/4` replaces it with
# `nominated_source`: a directory this deployment validates and MOUNTS
# read-only, and never walks, copies, snapshots, enumerates or hashes.
#
# THE MEMBER IS RENAMED RATHER THAN REDEFINED, and that is the point of doing
# it at a version boundary. The two mean different things about the same host
# path -- one is material this manager took custody of, the other is material
# it agreed not to touch -- and a member that quietly changed meaning under one
# name is exactly how a deployment ends up believing a copy happened. A `/3`
# document naming `input_source` is refused by the member set below rather than
# read as a nomination.
#
# `workspace_capacity` ARRIVES WITH IT because the two are one decision. Once
# the source is not copied in, the writable workspace is the only place a
# checkout, a build cache, test artifacts, the output and the logs can live --
# so how large it needs to be stops being incidental and becomes something the
# deployment has to say. There is no default: a size inherited from whatever
# the host happened to have is not a deployment's decision.
#
# IT DECLARES A NEED AND DOES NOT IMPOSE A CEILING, and W71917 rules that the
# member says so. This factory proves the workspace's filesystem currently has
# the declared bytes free before it starts anything; the bind it then composes
# is ordinary and writable, so a worker can fill that filesystem afterwards.
# Naming the member `workspace_quota` over that mechanism is the defect the
# run7 review found, and a deployment reading its own configuration is exactly
# who the wrong name misleads.
CONFIG_SCHEMA = "baton.v12.single-worker-deployment/4"
MAX_CONFIG_BYTES = 1024 * 1024

# W81115: THE TWO NAMES THE CERTIFIED WORKLOAD FIXES, mirrored here rather than
# imported. `claude_agent` runs INSIDE the image, on its own interpreter and
# import path; a host composer that imported it would be reaching across the
# boundary the whole delivery exists to cross, and would take its
# provider-specific task parser with it. What keeps the two copies honest is
# not an import but a test: the receiving-end fixture drives the real worker
# entry over the root this deployment composes and asserts these names against
# the workload's own constants.
TASK_DOCUMENT = "task.json"
SOURCE_DESTINATION = "source"
# THE WORKER'S OWN READ CEILING. `claude_agent._task` reads at most 1 MiB and
# a document wider than that is one it will never see whole, so this refuses it
# at configuration time rather than delivering material the receiving end
# cannot accept.
MAX_TASK_BYTES = 1024 * 1024

_MEMBERS = (
    "schema", "authority_store", "authority_uuid", "participant",
    "principal", "profile_name", "profile_digest", "policy_digest",
    "adapter_name", "adapter_digest", "engine", "image_digest", "network",
    "workspace_storage", "workspace_group", "launch_home",
    "credential_home", "credential_sources", "credential_slots",
    "credential_profile", "nominated_source", "workspace_capacity",
    "input_manifest", "task_document",
    "launch_contract", "launch_role", "review_route",
    "retention_policy_digest", "retention_disposition")
_DIGEST = re.compile(r"\Asha256:[0-9a-f]{64}\Z")
_NETWORK = re.compile(r"\A[a-zA-Z0-9][a-zA-Z0-9_.-]{0,127}\Z")


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _text(value, what):
    if type(value) is not str or not value:
        _refuse(f"{what} is non-empty text; this is {type(value).__name__}")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        _refuse(f"{what} is text this deployment can encode")
    return value


def _path(value, what):
    held = _text(value, what)
    if "\x00" in held or held.startswith("//") or not os.path.isabs(held) \
            or os.path.normpath(held) != held:
        _refuse(f"{what} is one absolute canonical path", code="path")
    return held


def _digest(value, what):
    held = _text(value, what)
    if not _DIGEST.match(held):
        _refuse(f"{what} is one lower-case sha256 digest", code="digest")
    return held


def _document(value, what, members):
    if type(value) is not dict:
        _refuse(f"{what} is one JSON object; this is {type(value).__name__}")
    missing = sorted(one for one in members if one not in value)
    extra = sorted(one for one in value if one not in members)
    if missing or extra:
        _refuse(f"{what} has exactly {', '.join(members)}"
                + (f"; missing {', '.join(missing)}" if missing else "")
                + (f"; unexpected {', '.join(extra)}" if extra else ""))
    return value


def _read(path):
    """Read one ordinary no-follow configuration file, bounded at the read."""
    place = _path(path, "the single-worker configuration path")
    try:
        handle = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as failure:
        _refuse(f"the single-worker configuration could not be opened "
                f"({type(failure).__name__})", code="path")
    try:
        found = os.fstat(handle)
        if not stat.S_ISREG(found.st_mode):
            _refuse("the single-worker configuration is one ordinary file",
                    code="path")
        pieces = []
        remaining = MAX_CONFIG_BYTES + 1
        while remaining:
            part = os.read(handle, remaining)
            if not part:
                break
            pieces.append(part)
            remaining -= len(part)
    finally:
        os.close(handle)
    raw = b"".join(pieces)
    if len(raw) > MAX_CONFIG_BYTES:
        _refuse(f"the single-worker configuration is wider than "
                f"{MAX_CONFIG_BYTES} bytes", code="limit")
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as failure:
        _refuse(f"the single-worker configuration is one UTF-8 JSON "
                f"document ({type(failure).__name__})")


def _held(document):
    """Own and relate every static deployment choice before an offer exists."""
    given = dict(_document(document, "a single-worker configuration", _MEMBERS))
    if given["schema"] != CONFIG_SCHEMA:
        _refuse(f"a single-worker configuration says {given['schema']!r}; "
                f"this deployment reads {CONFIG_SCHEMA!r}")
    for member in ("authority_store", "workspace_storage", "launch_home",
                   "credential_home", "nominated_source", "task_document"):
        given[member] = _path(given[member], f"the configuration's {member}")
    if given["credential_sources"] is not None:
        given["credential_sources"] = _path(
            given["credential_sources"],
            "the configuration's credential_sources")
    for member in ("authority_uuid", "participant", "principal",
                   "profile_name", "adapter_name", "engine", "network",
                   "launch_contract", "launch_role", "review_route",
                   "retention_disposition"):
        given[member] = _text(given[member],
                              f"the configuration's {member}")
    for member in ("profile_digest", "policy_digest", "adapter_digest",
                   "image_digest", "retention_policy_digest"):
        given[member] = _digest(given[member],
                                f"the configuration's {member}")
    if len(given["authority_uuid"]) != 32:
        _refuse("the configuration's authority_uuid is 32 characters")
    if given["engine"] not in ENGINES:
        _refuse(f"the configured engine is one of {', '.join(ENGINES)}",
                category="policy", code="denied")
    if not _NETWORK.match(given["network"]):
        _refuse("the configured network is one bounded OCI network name",
                category="policy", code="denied")
    group = given["workspace_group"]
    if type(group) is not int or type(group) is bool or group <= 0:
        _refuse("the configured workspace_group is one positive group id")
    manifest = check_manifest_structure(
        given["input_manifest"], "inputManifest",
        what="the configured bootstrap input manifest")
    given["input_manifest"] = manifest
    if manifest["runtime_profile_digest"] != given["profile_digest"]:
        _refuse("the bootstrap input manifest names another runtime profile",
                category="refused", code="precondition")
    if manifest["policy_digest"] != given["policy_digest"]:
        _refuse("the bootstrap input manifest names another policy",
                category="refused", code="precondition")
    if manifest["worker_image_digest"] != given["image_digest"]:
        _refuse("the bootstrap input manifest names another worker image",
                category="refused", code="precondition")
    if manifest["work_ref"]["authority_uuid"] != given["authority_uuid"]:
        _refuse("the bootstrap input manifest names another Authority",
                category="refused", code="precondition")
    if manifest["assignment_contract"] != given["launch_contract"]:
        _refuse("the bootstrap input manifest names another assignment "
                "contract", category="refused", code="precondition")
    # W81857: THE RETENTION DISPOSITION IS THE MANAGER'S OWN CLOSED
    # VOCABULARY, checked here rather than at the act. A configuration naming a
    # word `decide_retention` refuses would start a container, run a provider,
    # freeze and collect its result, and only then discover that nothing may be
    # decided about it -- which is the whole class of failure this preflight
    # exists to move to startup.
    if given["retention_disposition"] not in RETENTION_DISPOSITIONS:
        _refuse(f"the configured retention_disposition is one of "
                f"{', '.join(RETENTION_DISPOSITIONS)}",
                category="policy", code="denied")
    if given["launch_role"] != "implementation":
        _refuse("the single-worker deployment launches only the "
                "implementation role", category="policy", code="denied")
    if len(manifest["sources"]) != 1:
        _refuse("the bootstrap deployment accepts exactly one staged source",
                category="policy", code="denied")
    # W81115: AND ITS DESTINATION IS THE ONE THE WORKLOAD STAGES.
    #
    # The certified task contract fixes `source_root` to `source` and the
    # adapter copies exactly `/input/source`, so a manifest naming any other
    # destination composes a root the worker cannot use -- which is how this
    # deployment reached `running` with both fixed worker paths absent. The
    # check also reserves the task document's name from a source directory
    # that would collide with it.
    #
    # W71917 REPLACES THE COPY, NOT THIS RULE. Its ruled direct read-only mount
    # lands the same fixed path; what this pins is the path, which is the part
    # the worker fixes.
    if manifest["sources"][0]["destination"] != SOURCE_DESTINATION:
        _refuse(f"the bootstrap input manifest stages its source at "
                f"{manifest['sources'][0]['destination']!r} and the certified "
                f"workload reads exactly {SOURCE_DESTINATION!r}",
                category="policy", code="denied")
    # W71917: THE SOURCE IS NOMINATED, NOT STAGED, and the descriptor beside
    # it has to say so. `declared_profile` refuses a descriptor carrying no
    # boundary declaration, which is what a `/3` manifest for a COPIED source
    # is -- so a deployment that moved its configuration to `/4` and left its
    # frozen manifest describing a staging is refused here rather than
    # delivering a mount the manifest does not describe. The profile it
    # answers is bounded opaque text; this deployment carries it and reads
    # nothing into it, exactly as the manager does.
    given["source_profile"] = source_boundary.declared_profile(
        manifest["sources"][0])
    # AND THE NOMINATION IS PROVED BEFORE THE AUTHORITY IS OPENED, which is
    # where every other static check in this preflight already happens: a
    # source that is a link, is not a directory, or has a linked ancestor is a
    # configuration mistake, and finding it here means no attempt root exists
    # to leave partial. What it costs is one `lstat` and one `fstat` whatever
    # is inside the tree.
    given["source_nomination"] = source_boundary.nominate_source(
        given["nominated_source"])
    given["workspace_capacity"] = _capacity(given["workspace_capacity"])
    given["task_bytes"] = _task_bytes(given["task_document"],
                                      manifest["human_contract"])
    if type(given["credential_slots"]) is not list:
        _refuse("the configuration's credential_slots is one list")
    if type(given["credential_profile"]) is not dict:
        _refuse("the configuration's credential_profile is one object")
    given["credential_resolution"] = credentials.resolved_delivery(
        given["credential_slots"], profile=given["credential_profile"])
    # W81857: THE PRODUCTION LAUNCH IS `/2`, and the preflight authors the
    # exact version this deployment will write. Proving `/1` and then writing
    # `/2` would be proving a document nothing composes.
    launch.launch_document(session="single-worker-preflight",
                           contract=given["launch_contract"],
                           role=given["launch_role"],
                           transport=exchange.EXCHANGE_TRANSPORT)
    # W71917 RETIRED THE MEASUREMENT THAT STOOD HERE, and its absence is the
    # Work rather than a dropped check.
    #
    # `/3` called `workspaces.directory_manifest(input_source)` and compared it
    # with the manifest's declared `contentManifest`. That is a full no-follow
    # walk of the nominated tree -- every file opened, read whole and digested
    # -- performed by a manager that is ruled not to walk, copy, snapshot,
    # enumerate or hash the source at all. It also could not have kept its
    # promise: the tree it measured was measured before the container started,
    # and nothing bound the bytes the engine later mounted to the bytes this
    # walk read.
    #
    # WHAT REPLACES IT IS NOT A WEAKER VERSION OF IT. The declared
    # `contentManifest` for a nominated destination describes the empty
    # MOUNTPOINT this manager stages, which is a statement this manager can
    # keep; `_source_manifest` below holds the configuration to exactly that,
    # so a manifest still claiming to have measured somebody else's tree is
    # refused. Which revision the material actually is, is the worker's
    # question, answered against the base its own profile declares -- and it is
    # answered inside the container, over the tree that is really mounted.
    _source_manifest(manifest["sources"][0])
    return given


# The `contentManifest` of an empty tree, which is what this deployment stages
# at a nominated destination. Written as the four members rather than measured,
# because measuring an empty directory this deployment created to compare
# against a constant would be a walk performed to learn something already
# known.
EMPTY_TREE_DIGEST = digest([])


def _source_manifest(source):
    """Hold a nominated source descriptor to the empty tree it really stages.

    W71917. A nominated source is MOUNTED, so what this deployment puts in the
    input root at that destination is an empty mountpoint -- and the frozen
    manifest's `contentManifest` for it must describe exactly that. A manifest
    declaring 353 entries and eleven megabytes at a destination this manager
    stages nothing into is not a smaller mistake than a wrong digest: it is
    the whole staged-versus-nominated confusion, written into the document a
    result is later measured against.

    THIS IS NOT A MEASUREMENT OF THE NOMINATED TREE and cannot become one. It
    reads four numbers out of the configuration and compares them with
    constants; nothing under the nominated path is opened, and the check costs
    the same whatever is behind the mount.
    """
    content = source["content_manifest"]
    expected = {"entries": [], "entry_count": 0, "total_bytes": 0,
                "tree_digest": EMPTY_TREE_DIGEST}
    if content != expected:
        _refuse("the bootstrap input manifest declares content at a NOMINATED "
                "source destination; this deployment mounts that directory "
                "read-only and stages an empty mountpoint, so the declared "
                "contentManifest is the empty tree's or it describes material "
                "nobody staged", code="digest")
    return content


def _capacity(capacity):
    """The deployment's declared workspace capacity, owned then composed.

    ONE MEMBER AND NO MORE, read here so the refusal names the configuration
    member a deployment can fix, and then handed to the manager's own
    `workspace_capacity` -- which is what holds it to the floor above bounded
    scratch and to this build's ceiling. One rule, at its owner.

    THE ENTRY COUNT IS GONE RATHER THAN CARRIED, because W71917 rules that this
    document may not declare what nothing applies. `max_entries` was validated
    here, passed down, and then reached no mount, no runtime and no sweep; a
    deployment that set it was answering a question this delivery never asked.
    A closed member set makes the removal a refusal rather than a silent
    ignore, which is the point of removing it from the set rather than merely
    from the docstring.
    """
    given = _document(capacity, "the configuration's workspace_capacity",
                      ("max_bytes",))
    return source_boundary.workspace_capacity(given["max_bytes"])


def _task_bytes(place, contract):
    """The frozen workload document, READ ONCE and held as exact bytes.

    W81115. `single_worker` composed an input root carrying the two protocol
    manifests and the staged source and nothing else, while the certified
    worker opens `/input/task.json` before it does any provider work. The Job
    projection therefore reached `running` over a root the worker refuses, and
    no later operation could make the document appear.

    READ HERE, WHICH IS BEFORE ANYTHING EXISTS TO UNDO. This runs inside static
    configuration validation -- before the Authority is opened, before an offer
    is made, before an attempt or a workspace exists -- so every refusal below
    happens with no attempt root to leave partial and nothing to settle.

    HELD AS BYTES, AND THE PATH IS NEVER REOPENED. What this deployment
    delivers is decided once, here; a change to the configured path afterwards
    cannot change what a later composition publishes. That is also why the
    bytes rather than the path are what the constructed deployment carries.

    NO-FOLLOW, ORDINARY, BOUNDED, in that order and for three different
    reasons. A final symlink is a path this deployment did not choose;
    a directory, FIFO or device is not a document; and one byte past the
    worker's own ceiling is material the receiving end will never see whole.
    `O_NONBLOCK` so that opening a FIFO nobody has opened for writing answers
    rather than hanging the whole deployment before it starts.

    AND IT IS THE MANIFEST'S HUMAN CONTRACT, which is the approved decision
    this rests on. For THIS production profile the task document IS the input
    manifest's `human_contract` artifact, so the frozen manifest already
    carries its media type, its width and its digest -- and holding the bytes
    to them is what makes the delivery digest-bound rather than
    path-trusting. The locator stays provenance and is never read as a host
    path.

    WHAT IS DELIBERATELY NOT DONE HERE. The document's provider-specific
    schema is not parsed. `claude_agent` owns that vocabulary at the receiving
    end, and a host-side copy of it would be a second reader of one contract --
    which is exactly what the retired dogfood helpers were, and why they could
    not be reused: they follow the final symlink, parse on the host, and
    reserialize the object instead of delivering the bytes.
    """
    if type(contract) is not dict:
        _refuse("the bootstrap input manifest carries no human contract")
    if contract["media_type"] != "application/json":
        _refuse(f"this profile's task document is the input manifest's "
                f"human contract and that artifact is "
                f"{contract['media_type']!r} rather than 'application/json'",
                category="refused", code="precondition")
    if type(contract["bytes"]) is not int or type(contract["bytes"]) is bool \
            or contract["bytes"] > MAX_TASK_BYTES:
        _refuse(f"this profile's human-contract artifact is wider than the "
                f"{MAX_TASK_BYTES}-byte ceiling the workload reads",
                code="limit")
    try:
        handle = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
                         | os.O_NONBLOCK)
    except OSError as failure:
        _refuse(f"the configured task document could not be opened "
                f"({type(failure).__name__})", code="path")
    try:
        found = os.fstat(handle)
        if not stat.S_ISREG(found.st_mode):
            _refuse("the configured task document is one ordinary file",
                    code="path")
        pieces = []
        remaining = MAX_TASK_BYTES + 1
        while remaining:
            part = os.read(handle, remaining)
            if not part:
                break
            pieces.append(part)
            remaining -= len(part)
    finally:
        os.close(handle)
    raw = b"".join(pieces)
    if len(raw) > MAX_TASK_BYTES:
        _refuse(f"the configured task document is wider than "
                f"{MAX_TASK_BYTES} bytes", code="limit")
    if len(raw) != contract["bytes"]:
        _refuse(f"the configured task document is {len(raw)} bytes and this "
                f"profile's human-contract artifact declares "
                f"{contract['bytes']}", code="digest")
    if digest_of_bytes(raw) != contract["content_digest"]:
        _refuse("the configured task document is not the content this "
                "profile's human-contract artifact names", code="digest")
    return raw


def _sayable(message, instead):
    """Own another component's diagnostic before it becomes a refusal's.

    Re-review 2026-09-03T18:49:20Z [P1]. `ContractRefusal` refuses to be
    CONSTRUCTED around a live bearer, so quoting a credential source's own
    text raised `integrity/secret-leak` out of this deployment's handler --
    which left the stage with no ending and the provider called again on every
    tick. The secret never reached a durable surface and the accepted ending
    was lost, which is its own defect.

    The shipped §13 rule decides, rather than a second copy of it here, and
    what replaces an unsayable diagnostic says why it was replaced.
    """
    try:
        check_no_durable_secret(message,
                                what="a credential source's own diagnostic")
    except ContractRefusal:
        return instead
    return message


def _now():
    moment = datetime.now(timezone.utc)
    return (moment.strftime("%Y-%m-%dT%H:%M:%S.")
            + f"{moment.microsecond // 1000:03d}Z")


def _bearer():
    import secrets
    return secrets.token_urlsafe(32)


def _engine_run(argv, *, seconds=None):
    finished = subprocess.run(argv, capture_output=True,
                              timeout=600 if seconds is None else seconds)
    return {"status": finished.returncode,
            "stdout": finished.stdout.decode("utf-8", "replace"),
            "stderr": finished.stderr.decode("utf-8", "replace")}


def _assignment(row):
    return {"work_ref": {"authority_uuid": row["authority_uuid"],
                         "work_id": row["work_id"]},
            "participant": row["participant"],
            "generation": row["claim_generation"]}


def _claim_facts(row):
    assignment = _assignment(row)
    decision = {"endpoint": row["participant"],
                "principal": row["claim_principal"],
                "effective_scope": row["claim_scope"],
                "role": row["claim_role"], "grant": row["claim_grant"],
                "policy_generation": row["claim_policy_generation"]}
    return {"assignment": assignment, "claim_event": row["claim_event_seq"],
            "decision": decision}


def _assignment_manifest(given, row, attempt_id, offer_id):
    manifest = given["input_manifest"]
    document = {
        "version": {"major": 1, "minor": 0},
        "manifest_id": "assignment-" + digest(attempt_id)[7:31],
        "created_at": row["accepted_at"], "extensions": {},
        "schema": "baton.worker-manifest/assignment",
        "assignment_ref": _assignment(row),
        "assignment_contract": manifest["assignment_contract"],
        "offer_id": offer_id, "runtime_attempt_id": attempt_id,
        "input_manifest_digest": manifest["manifest_digest"],
        "policy_digest": manifest["policy_digest"],
        "runtime_profile_digest": manifest["runtime_profile_digest"],
        "claim_receipt_digest": digest(_claim_facts(row)),
        "claim_event_seq": row["claim_event_seq"],
        "activated_at": row["decided_at"]}
    document["manifest_digest"] = digest(document)
    return check_manifest_structure(
        document, "assignmentManifest",
        what="the bootstrap assignment manifest")


class _AuthoritySession:
    """The exact Authority surface this implementation deployment carries.

    The core Session owns the six lifecycle operations this worker needs.
    ``AuthorityPort`` also names conversational publication; this bootstrap
    does not run inquiry sessions, so that seventh capability is an explicit
    typed refusal rather than a successful-looking no-op.
    """

    __slots__ = ("_session",)

    def __init__(self, session):
        self._session = session

    @property
    def participant(self):
        return self._session.participant

    def project_work(self, *arguments):
        return self._session.project_work(*arguments)

    def slot_holder(self, *arguments):
        return self._session.slot_holder(*arguments)

    def assignment_of(self, *arguments):
        return self._session.assignment_of(*arguments)

    def cancel(self, *arguments):
        return self._session.cancel(*arguments)

    def claim(self, *arguments):
        return self._session.claim(*arguments)

    def settle_operation(self, *arguments):
        return self._session.settle_operation(*arguments)

    def publish_answer(self, *arguments):
        del arguments
        _refuse("the bootstrap implementation deployment carries no inquiry "
                "publication capability", category="refused",
                code="capability")

    def pass_work(self, *arguments):
        """W81857: the ONE lifecycle transition this deployment's ending makes.

        ADDED HERE RATHER THAN REACHED THROUGH THE PORT. `AuthorityPort` is the
        narrow capability the Worker Manager holds, and every operation on it
        is one that manager performs; a pass is the DEPLOYMENT's act -- it ends
        the assignment and moves the Work's Route in one authority
        transaction -- and widening the manager's port to carry it would give
        the manager an authority it has no operation for.

        The wrapper stays a wrapper: it forwards one exact operand document to
        the real session, exactly as the six lifecycle operations above do,
        and the answer is held to its shape at the one caller that reads it.
        """
        return self._session.pass_work(*arguments)


def _more_than_the_mountpoint(inputs, boundary):
    """Whether an uncomposed input root holds anything this deployment did not
    just establish.

    W71917 MADE "EMPTY" THE WRONG QUESTION. Before this Work, a root with no
    protocol pair and any entry at all was partial, and the test was one
    `os.listdir`. The boundary is now composed BEFORE the root is frozen --
    it has to be, because freezing closes the directory the mountpoint lives
    in -- so the ordinary pre-composition state is a root holding exactly one
    entry: the empty mountpoint. A rule that called that partial would refuse
    every first composition.

    SO THE QUESTION IS "ANYTHING ELSE", and the mountpoint is excluded by the
    name the composed boundary answers rather than by a constant, so a root
    holding a directory called `source` that this composition did not
    establish is not quietly forgiven.

    AND THE MOUNTPOINT ITSELF IS PROVED WITHOUT ENUMERATING IT. A directory on
    another filesystem than its parent is a live bind, and reading it would be
    reading the nominated source -- the one thing this deployment does not do.
    That case is refused on the DEVICE, before anything is listed. Only once
    it is provably this manager's own directory is it peeked at, and then for
    one entry rather than a walk: leftovers from the retired copied bootstrap
    are material whose provenance this composition cannot prove, and adopting
    them is exactly what the partial-root rule exists to stop.
    """
    for name in os.listdir(inputs):
        if name != os.path.basename(boundary.mountpoint):
            return True
    place = boundary.mountpoint
    if not os.path.isdir(place):
        return True
    if os.lstat(place).st_dev != os.lstat(inputs).st_dev:
        # A LIVE BIND, and this is where it is refused rather than read. It is
        # not an ordinary state -- the engine binds inside the container's own
        # mount namespace -- so a host-side one is somebody else's mount over
        # this manager's mountpoint.
        return True
    with os.scandir(place) as reading:
        for _entry in reading:
            return True
    return False


class _SingleWorker:
    """The launch capability; it receives no Authority bootstrap or path."""

    def __init__(self, given, control, port, *, credential_provider,
                 engine_run, session=None, clock=None, checkpoint=None):
        self.given = given
        self.control = control
        self.port = port
        # W81857: THE SESSION, FOR THE ONE ACT THE PORT DOES NOT CARRY. It is
        # optional only so focused verification can compose a worker that
        # never reaches an ending; `_passed` refuses without it rather than
        # skipping the handoff, because an attempt whose result is frozen,
        # collected and retained and whose Work never moves is a stage that
        # looks finished and has not been handed to anybody.
        self.session = session
        self.group = configured_workspace_group(control)
        self.credential_home = credentials.CredentialHome(
            given["credential_home"])
        self.credential_provider = credential_provider
        self.engine = EnginePort(engine_run)
        self.clock = clock or _now
        self.checkpoint = checkpoint or (lambda _name: None)
        self.expected_offer = None

    def admit(self, perform, stage, job):
        """Bind the one admissible intent before its bearer can be minted."""
        self._matches(stage, job)
        if self.expected_offer is not None:
            _refuse("one single-worker offer delivery is already in progress",
                    category="refused", code="precondition")
        self.expected_offer = {
            "offer_id": stage["offer_id"],
            "runtime_attempt_id": stage["attempt_id"],
            "work_id": stage["work_id"],
            "participant": self.given["participant"]}
        try:
            return perform(stage, job)
        finally:
            self.expected_offer = None

    def delivered(self, issued):
        given = self.given
        manifest = given["input_manifest"]
        expected = self.expected_offer
        if expected is None:
            _refuse("an offer bearer arrived outside its one admission call",
                    category="refused", code="capability")
        for member, value in expected.items():
            if issued.get(member) != value:
                _refuse(f"the issued offer's {member} does not match this "
                        "single-worker deployment",
                        category="refused", code="precondition")
        accept_offer(
            self.control, self.port, offer_id=issued["offer_id"],
            decision="accept", bearer=issued["bearer"], now=self.clock(),
            runtime_attempt_id=issued["runtime_attempt_id"],
            work_ref=dict(manifest["work_ref"]))

    def _matches(self, stage, job):
        given = self.given
        manifest = given["input_manifest"]
        expected = {"kind": "implementation",
                    "work_id": manifest["work_ref"]["work_id"],
                    "profile_name": given["profile_name"],
                    "profile_digest": given["profile_digest"]}
        for member, value in expected.items():
            if stage.get(member) != value:
                _refuse(f"stage {stage.get('stage_id')!r} names {member} "
                        f"{stage.get(member)!r}; this single worker accepts "
                        f"only {value!r}", category="refused",
                        code="precondition")
        if job.get("input_digest") != manifest["manifest_digest"]:
            _refuse("the Job names another bootstrap input",
                    category="refused", code="precondition")
        if job.get("policy_digest") != given["policy_digest"]:
            _refuse("the Job names another bootstrap policy",
                    category="refused", code="precondition")

    def _claim(self, stage):
        found = claimed_offers_for(self.control, stage["attempt_id"])
        if len(found) != 1:
            _refuse(f"attempt {stage['attempt_id']!r} has {len(found)} "
                    "claimed offers; one launch requires exactly one",
                    category="refused", code="precondition")
        row = found[0]
        expected = {"offer_id": stage["offer_id"],
                    "authority_uuid": self.given["authority_uuid"],
                    "work_id": stage["work_id"],
                    "participant": self.given["participant"],
                    "profile_digest": self.given["profile_digest"],
                    "input_digest": self.given["input_manifest"]
                    ["manifest_digest"],
                    "policy_digest": self.given["policy_digest"]}
        for member, value in expected.items():
            if row.get(member) != value:
                _refuse(f"the claimed offer's {member} does not match this "
                        "stage", category="refused",
                        code="operation-collision")
        return row

    def _input(self, roots, assignment, boundary):
        given = self.given
        manifest = given["input_manifest"]
        try:
            held_input, held_assignment = workspaces.read_input_root(
                roots["inputs"])
        except ContractRefusal:
            if _more_than_the_mountpoint(roots["inputs"], boundary):
                # Review 2026-09-03T17:23:00Z [P1]: this raised
                # `refused/path`, which is not one of §9's closed pairs -- so
                # the one branch that finds incomplete material rejected its
                # own raising site with an `AssertionError` instead of the
                # typed refusal it meant.  `integrity/path` is the pair this
                # is: a root whose bytes this manager cannot account for.
                _refuse("the bootstrap input root is partial; restart refuses "
                        "rather than completing material whose provenance it "
                        "cannot prove", code="path")
            # W81115: THE WORKLOAD DOCUMENT FIRST, and the order is the
            # content. `compose_input_root` FREEZES the root when it finishes
            # -- 0555 on the directory -- so nothing can be added afterwards,
            # and the source copy walks a tree this deployment does not want
            # deciding whether the task name is still free. Publishing here
            # means the whole root is composed before the protocol pair
            # completes it, which is also W76207's rule: a death anywhere in
            # between leaves a partial root the next process refuses above
            # rather than repairs.
            self._published_task(roots["inputs"])
            # W71917: THE MOUNTPOINT, NOT A COPY. What stood here walked the
            # nominated tree a second time and wrote every file into the input
            # root -- the ordinary copied bootstrap this Work retires. The
            # boundary was already composed before this method was reached, so
            # the empty directory the engine binds over exists; nothing is read
            # from the nominated source and nothing is written into the root
            # except the two protocol documents and the task.
            #
            # THE DESTINATION IS STILL PINNED, by the same rule the preflight
            # pins it with: the certified workload reads exactly one relative
            # path, and a manifest naming another would compose a root the
            # worker cannot use.
            if manifest["sources"][0]["destination"] \
                    != os.path.basename(boundary.mountpoint):
                _refuse("the bootstrap input manifest stages its source "
                        "somewhere other than the mountpoint this deployment "
                        "established")
            workspaces.compose_input_root(
                roots["inputs"], manifest, assignment,
                assignment=dict(assignment["assignment_ref"]),
                runtime_attempt_id=assignment["runtime_attempt_id"])
            return manifest
        if held_input != manifest or held_assignment != assignment:
            _refuse("the existing bootstrap input root is another delivery",
                    category="refused", code="precondition")
        # W81115: AND THE WORKLOAD DOCUMENT IS PROVED TOO, on every restart.
        #
        # `read_input_root` deliberately reads exactly the two PROTOCOL
        # documents -- that is the generic component's whole contract -- so a
        # matching manifest pair says nothing at all about the workload
        # material beside it. Inferring the task from `input.json` would be
        # this deployment concluding something the reader it called never
        # looked at.
        self._proved_task(roots["inputs"])
        return held_input

    def _published_task(self, inputs):
        """Install the held task bytes as the read-only workload document.

        NEVER FROM THE CONFIGURED PATH. The bytes were read once, at
        construction, and are what this publishes; reopening the path here
        would let material change between the proof and the delivery, which is
        the whole reason `_task_bytes` holds them.

        REFUSED RATHER THAN REPLACED when the name is taken, AND THE
        EXCLUSIVE CREATION IS BOTH DECISIONS AT ONCE. An input root carrying a
        task this composition did not write is material whose provenance it
        cannot prove, and W76207's rule for exactly that is to refuse and
        record one preparation ending rather than repair in place.

        THERE IS NO SECOND PATHNAME, and two reviews are why. The first cut
        checked the final name and finished with `os.replace`, which CLOBBERS,
        so a creator that won the interval between the check and the rename had
        its document silently replaced (review 2026-09-04T00:56:36Z [P1]). The
        second made that transition a no-clobber `os.link` -- and left the
        STAGING NAME as a mutable pathname between the proof and the
        publication, so a creator that unlinked it and put a symlink there had
        that symlink hard-linked at the final name, published, and reported as
        success (review 2026-09-04T01:06:30Z [P1]).

        Both defects are one defect: a name proved at one moment and used at
        another. Defending the interval a third time would be the same bet
        again, so the interval is GONE. The document is created directly at its
        final name with `O_CREAT | O_EXCL | O_NOFOLLOW`, which IS the
        no-clobber decision -- an existing file, directory or symlink at that
        name fails `EEXIST` and nothing is written -- and every act after it is
        on THE DESCRIPTOR THAT CREATION RETURNED. The bytes, the readback and
        the mode all reach the same inode, and there is no other pathname for
        anything to substitute.

        UNREADABLE UNTIL PROVED. Mode 0 at creation, and `fchmod` on that same
        descriptor only after the bytes have been read back and compared -- so
        the document becomes readable exactly when it becomes both complete and
        proved. What an interrupted composition leaves is an unreadable file
        inside a root with no protocol pair, which the partial-root rule
        refuses above and `_proved_task` would refuse for its mode.

        NOT `workspaces._write_read_only`, which is the same shape one
        component over. That one is the private owner of the two protocol
        documents, and publishing this through it would mean making a generic
        Worker Manager operation public to carry workload material -- the
        vocabulary boundary this Work is explicitly held to. It also stages,
        for a reason that is real where it lives: those documents are composed
        into a root a container may already be mounting. This one is written
        before the root is frozen and before any runtime exists, so nothing can
        observe the incomplete name, and removing the second pathname is worth
        more here than atomic appearance is.
        """
        held = self.given["task_bytes"]
        place = os.path.join(inputs, TASK_DOCUMENT)
        try:
            handle = os.open(place, os.O_RDWR | os.O_CREAT | os.O_EXCL
                             | os.O_NOFOLLOW | os.O_CLOEXEC, 0o000)
        except FileExistsError:
            _refuse(f"the bootstrap input root already carries "
                    f"{TASK_DOCUMENT!r}; a workload document this composition "
                    f"did not write is material whose provenance it cannot "
                    f"prove", code="path")
        except OSError as failure:
            _refuse(f"the bootstrap task document could not be created "
                    f"({type(failure).__name__})", code="path")
        try:
            written = 0
            while written < len(held):
                moved = os.write(handle, held[written:])
                if moved <= 0:
                    _refuse("the bootstrap task document could not be written "
                            "whole", code="limit")
                written += moved
            os.fsync(handle)
            os.lseek(handle, 0, os.SEEK_SET)
            if os.read(handle, len(held) + 1) != held:
                _refuse("the published bootstrap task document is not the "
                        "content this deployment holds", code="digest")
            os.fchmod(handle, 0o444)
        except BaseException:
            # THE NAME THIS OPERATION EXCLUSIVELY CREATED IS ITS OWN TO REMOVE,
            # and it is removed by name rather than proved first because the
            # exclusive creation is what established that the name was free:
            # nothing else has published under it in between without this
            # having already failed.
            os.close(handle)
            os.unlink(place)
            raise
        os.close(handle)
        return place

    def _proved_task(self, inputs):
        """The installed workload document, re-proved against the held bytes.

        The same three questions the configuration asked, asked again of what
        is actually on disk: a no-follow ordinary file, the exact bytes this
        deployment holds, and the read-only mode that says on disk what the
        delivery says in prose. A root whose protocol pair matches while its
        task has moved is a root the worker would read something else out of.
        """
        held = self.given["task_bytes"]
        place = os.path.join(inputs, TASK_DOCUMENT)
        try:
            handle = os.open(place, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC
                             | os.O_NONBLOCK)
        except OSError as failure:
            _refuse(f"the existing bootstrap input root carries no readable "
                    f"{TASK_DOCUMENT!r} ({type(failure).__name__})",
                    code="path")
        try:
            found = os.fstat(handle)
            if not stat.S_ISREG(found.st_mode):
                _refuse(f"the existing {TASK_DOCUMENT!r} is one ordinary file",
                        code="path")
            if stat.S_IMODE(found.st_mode) != 0o444:
                _refuse(f"the existing {TASK_DOCUMENT!r} is not the read-only "
                        f"document this deployment published", code="path")
            raw = os.read(handle, len(held) + 1)
        finally:
            os.close(handle)
        if raw != held:
            _refuse("the existing bootstrap input root carries another task "
                    "document", category="refused", code="precondition")
        return place

    def _adapter(self, roots, delivery, orphan, launched, boundary=None):
        given = self.given
        manifest = given["input_manifest"]
        return OciAdapter(
            given["engine"], self.engine,
            identity={"image_digest": given["image_digest"],
                      "profile_digest": given["profile_digest"],
                      "policy_digest": given["policy_digest"],
                      "adapter_digest": given["adapter_digest"]},
            assignment_roots=roots, posture="execution",
            # THE TWO ROOTS THIS MANAGER CREATED, unchanged by W71917. The
            # input root is still read-only at `/input` and the workspace
            # still writable at `/output`; what the nominated source adds is a
            # THIRD bind, composed by `oci` out of the typed boundary below
            # rather than named here, because a source this deployment could
            # name as a path would be the caller-selected locator the proof
            # exists to remove.
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}],
            # W71917: `None` FOR THE ADAPTERS THAT ONLY IDENTIFY OR RECOVER.
            # `_naming` and `_recovered` build an adapter to ask the engine
            # what is already there; neither starts anything, so neither needs
            # -- or should hold -- a delivery over somebody else's tree.
            source_delivery=boundary,
            outputs=[dict(one) for one in manifest["outputs"]],
            input_manifest_digest=manifest["manifest_digest"],
            credential_delivery=delivery,
            credential_home=self.credential_home,
            credential_orphan=orphan,
            launch_delivery=launched, workspace_group=self.group,
            network=given["network"], interactive=True)

    def _credential(self, attempt_id, state, roots):
        given = self.given
        if not given["credential_resolution"]:
            return None, None
        if state["execution_runtime"] == "not-started":
            root = self.credential_home.volatile_root(attempt_id)
            if self.credential_home.read_state(attempt_id) is not None \
                    or os.path.lexists(root):
                self.credential_home.discard_orphan(attempt_id)
            return (self.credential_home.materialize(
                given["credential_resolution"], attempt_id=attempt_id,
                workspace_group=self.group,
                credential_provider=self.credential_provider), None)
        recovered = self._recovered(attempt_id, state, roots)
        if recovered is not None:
            return recovered, None
        # THE START OPERATION MAY HAVE COMMITTED BEFORE ITS ENGINE CALL. The
        # materializing process and its Delivery capability are then gone,
        # and no runtime id exists yet with which `adopt` could rebuild one.
        # The public orphan capability carries exactly that durable
        # uncertainty into reconciliation without opening bearer bytes or
        # pretending the delivery never existed.
        return None, credentials.OrphanTeardown(
            attempt_id, homes=[self.credential_home])

    def _recovered(self, attempt_id, state, roots):
        """Adopt a published delivery only through the public LIVE proof.

        Review 2026-09-03T17:23:00Z [P1]: this read the lifecycle record and
        called `CredentialHome.adopt` with the runtime id taken OUT OF THAT
        SAME RECORD, so the one comparison it made was the record against
        itself. Bearer bytes were re-registered before anything proved the
        live container was the one the record names or that it holds the
        mount the record describes -- which is the exact boundary the
        credential recovery contract says must fail closed.

        `OciAdapter.recover_credentials` IS THAT BOUNDARY and it is composed
        rather than paraphrased: it derives this attempt's whole label set,
        identifies exactly one live runtime, compares the record's runtime id
        with the engine's answer, inspects what that runtime actually has
        mounted, and only then calls `adopt` itself. Ordinary
        `reconcile_runtime` performs none of those checks, which is why
        reaching it first was not the same thing.

        THE ADAPTER THAT ASKS CARRIES NO DELIVERY, because it has none yet --
        the delivery is what this returns. A disagreement raises, and the
        recovery operation's own bounded stop and cleanup ride out with the
        refusal untouched: nothing here re-registers a bearer, accepts output
        or repairs what disagreed.

        ABSENCE IS THE CALLER'S OTHER BRANCH rather than an ending here. The
        lifecycle record is written only once there is a runtime to name, so
        an attempt interrupted between the start journal and that publication
        has none, and the orphan teardown is what stands in for a delivery
        this process cannot hold.
        """
        if self.credential_home.read_state(attempt_id) is None:
            return None
        answered = self._adapter(roots, None, None, None).recover_credentials({
            "attempt_id": attempt_id,
            # THE ASSIGNMENT ACTIVATION FIXED, out of the same atomic read the
            # branch above turns on -- not the claim row, which is where this
            # attempt came from rather than what its runtime labels were
            # composed out of.
            "assignment": state["assignment"],
            "context": label_context(self.control, attempt_id)})
        return answered.get("delivery")

    def start(self, stage, job):
        """Drive one claimed stage to a live runtime, or to ONE recorded end.

        THE ATTEMPT AND ITS ACTIVATION COME FIRST AND STAND ALONE. They are
        what makes an ending recordable at all -- the record is held against
        the assignment activation fixed -- so a refusal from either is the one
        preparation refusal this composition cannot settle, and it travels out
        as itself rather than being dressed as an ending nobody wrote.

        EVERY BOUNDARY AFTER THEM SETTLES THE SAME WAY, and re-review [P1] is
        why "the same way" now means every one of them. The first correction
        settled only from `not-started` and re-raised from `start-requested`,
        so a credential recovery that failed closed in the restart window left
        the stage claimed and was asked again on every tick -- an ordinary
        refusal is neither an ending nor a safe wait state, and the recovery's
        bounded stop had already changed the host by the time the next tick
        repeated it. `refuse_runtime_preparation` records from both live axes,
        and the refusal it raises carries the recovery's whole account.
        """
        self._matches(stage, job)
        row = self._claim(stage)
        given = self.given
        attempt_id = stage["attempt_id"]
        self.checkpoint("claimed")
        record_attempt(
            self.control, attempt_id=attempt_id,
            adapter_name=given["adapter_name"],
            adapter_digest=given["adapter_digest"],
            profile_digest=given["profile_digest"],
            input_digest=given["input_manifest"]["manifest_digest"],
            policy_digest=given["policy_digest"],
            image_digest=given["image_digest"],
            toolchain_digest=given["input_manifest"]["toolchain_digest"])
        self.checkpoint("attempt")
        activate_assignment(self.control, self.port, attempt_id=attempt_id,
                            expect=_assignment(row))
        self.checkpoint("activation")
        try:
            return self._prepared(stage, row, attempt_id)
        except SourceRefusal as failure:
            refusal = ContractRefusal("policy", "denied", _sayable(
                str(failure),
                "the configured credential source refused, and its own "
                "diagnostic quoted a value the secret registry holds live, "
                "so it is not carried"))
        except ContractRefusal as failure:
            refusal = failure
        # A START THAT ALREADY FAILED HAS ITS OWN ACCOUNT.
        # `request_runtime_start` journals the failed start, settles the axis
        # and re-raises -- so sending that refusal on to the preparation writer
        # got `already-terminal` back, and the sweep report then carried this
        # deployment's note about why it could not write a record instead of
        # the engine's reason for refusing. The owner's record already exists;
        # the original refusal is what an operator reads.
        if attempt_start_failure_of(self.control, attempt_id) is not None \
                or attempt_preparation_failure_of(self.control,
                                                  attempt_id) is not None:
            raise refusal
        # ONE OWNER-RECORDED ENDING, and the raise is the report. The Worker
        # Manager identifies the runtime, journals the failed preparation and
        # re-raises this refusal with its own account appended, so the next
        # projection reads that record and the stage is exceptional rather than
        # claimed and polled.
        #
        # THE IDENTIFICATION RIDES THE SAME CALL, and re-review [P1] is why.
        # Doing it after the record had no second chance: the record makes the
        # stage exceptional and the control plane stops asking, so a crash or a
        # naming refusal in between orphaned the runtime permanently. Asking
        # the owner to reconcile before it records makes a crash leave the
        # stage CLAIMED, which the next tick drives through the same path
        # again -- and it covers every boundary that refuses after a start was
        # requested rather than only the one branch that noticed.
        refuse_runtime_preparation(self.control, attempt_id=attempt_id,
                                   refusal=refusal,
                                   adapter=self._naming(attempt_id))

    def _naming(self, attempt_id):
        """An adapter that can only IDENTIFY, for an attempt that may have one.

        A runtime can exist only where a start was requested, so nothing is
        asked of the engine for an attempt that never reached one. The adapter
        carries no credential delivery and no launch delivery -- what the owner
        does with it is `list` and `observe` -- so no bearer is reread and no
        launch bytes are needed to build it.

        WHY THE ROOTS ARE COMPOSED RATHER THAN ALLOCATED. This runs while a
        failure is already on its way out, and `assignment_workspace` is one of
        the boundaries that may have been what refused. The reconciliation
        needs an adapter, not a workspace; the paths are the deployment's own
        derivation, exactly as the preflight adapter's are.

        ANSWERS `None` RATHER THAN RAISING, for the same reason: an ending
        nobody could write because an adapter could not be built is the retry
        loop this whole path exists to stop.
        """
        try:
            if attempt_runtime_of(self.control,
                                  attempt_id)["execution_runtime"] \
                    == "not-started":
                return None
            home = os.path.join(self.given["workspace_storage"], attempt_id)
            return self._adapter({"inputs": os.path.join(home, "inputs"),
                                  "workspace": os.path.join(home, "workspace")},
                                 None, None, None)
        except ContractRefusal:
            return None

    def _prepared(self, stage, row, attempt_id):
        """Compose the assignment's material and start or reconcile its runtime.

        Every refusal here has one recorded ending at the caller, so nothing in
        it repairs, completes or works around material it cannot account for.

        THE LAUNCH DELIVERY IS PROVED BEFORE ANY BEARER IS TOUCHED. Credential
        recovery rereads and REGISTERS bearer bytes; a launch document that
        refused afterwards left those registrations live with nothing holding
        the delivery, and the next tick registered them again. Proving the
        launch first means the only thing a launch refusal can unwind is a
        launch.

        AND THE UNWIND COVERS THE START ITSELF. Re-review 2026-09-03T19:24:19Z
        [P1]: the cleanup `try` used to end before `request_runtime_start`, and
        the provider's answer is UNTRUSTED -- one equal to this attempt's own
        durable identity is registered live and then makes every §13 walk over
        a row containing that identity refuse. The manager could no longer read
        its own attempt, so nothing could be settled, recorded or reported, and
        the delivery stayed on the host. The delivery's owner stays live across
        every pre-start boundary that follows materialization, so the colliding
        value is released -- after its bytes are proved gone -- before any
        durable state is read again.
        """
        given = self.given
        roots = workspaces.assignment_workspace(
            self.group, given["workspace_storage"], attempt_id)
        self.checkpoint("workspace")
        # W71917: THE BOUNDARY IS COMPOSED BEFORE THE INPUT ROOT IS FROZEN,
        # and the order is the content. `compose_source_boundary` establishes
        # the empty mountpoint inside `inputs`, and `compose_input_root` closes
        # that directory read-only when it finishes -- so a boundary composed
        # afterwards would have nowhere to put the mountpoint, and a deployment
        # that created it later would be writing into evidence a claim was
        # already made against.
        #
        # IT ALSO PROVES THE WORKSPACE HERE, which is before anything exists to
        # undo: a workspace on a memory filesystem, or one whose storage cannot
        # currently meet the declared capacity, is a preparation refusal with
        # no container started rather than a worker discovering it halfway
        # through a turn.
        boundary = source_boundary.compose_source_boundary(
            given["source_nomination"], roots, given["workspace_capacity"])
        # W71917: AND THE OBJECT IT PROVED IS PINNED DURABLY, immediately.
        #
        # The composition above pins the source's (device, inode) IN MEMORY,
        # which is enough for this incarnation and nothing at all for the next
        # one: a restarted manager recomposes the boundary from configuration,
        # so the pre-start comparison would compare a fresh reading with
        # itself. Run7 review [P1] is exactly that hole -- a directory replaced
        # while the manager was down is re-nominated and accepted.
        #
        # WRITE-ONCE, AND AN EXACT REPEAT IS NOT A WRITE, so every later
        # incarnation reaching this line for the same attempt either re-observes
        # the same object or is refused here rather than silently re-pinning
        # the replacement over the evidence that would have caught it.
        pin_boundary_identity(
            self.control, attempt_id=attempt_id,
            source=(boundary.device, boundary.inode),
            # W71917 THIRD REVIEW [P1]: BOTH ROOTS. The source was pinned and
            # the workspace was not, so a real directory created at the
            # workspace's pathname was adopted with nothing to compare it
            # against -- and the workspace is the half this assignment's answer
            # is collected out of.
            workspace=(boundary.workspace_device, boundary.workspace_inode))
        self.checkpoint("boundary")
        assignment = _assignment_manifest(given, row, attempt_id,
                                          stage["offer_id"])
        manifest = self._input(roots, assignment, boundary)
        self.checkpoint("input")
        retain_manifest(self.control, manifest, "inputManifest")
        self.checkpoint("manifest")
        state = attempt_runtime_of(self.control, attempt_id)
        fresh = state["execution_runtime"] == "not-started"
        launched = self._launch_document(attempt_id, state)
        self.checkpoint("launch")
        delivery = None
        adapter = None
        try:
            delivery, orphan = self._credential(attempt_id, state, roots)
            self.checkpoint("credential")
            # W71917: RE-PROVED IMMEDIATELY BEFORE THE START, and this is the
            # gate the ruling asks for. Everything between composition and here
            # -- the input root, the retained manifest, the launch document,
            # the credential delivery -- takes time a host is free to change
            # things in, and the two paths this delivery rests on are the two
            # a change would be worst at. A source re-pointed at another tree
            # resolves to the same characters and a different inode; a
            # workspace replaced with a link or moved aside is no longer the
            # one this manager holds custody of. Both refuse here, with no
            # runtime started.
            #
            # A RESTART REACHES THIS LINE THROUGH THE SAME PATH, which is why
            # there is one gate rather than two: `assignment_workspace`
            # answered the adopted roots, the boundary was composed over them
            # again, and this proves the topology a second incarnation is about
            # to start over is the one it just proved.
            boundary = source_boundary.adopt_source_boundary(
                boundary, roots,
                # READ UNCONDITIONALLY. A caller that has a pinned identity and
                # does not pass it gets the weaker in-memory gate, which after a
                # restart compares a fresh reading with another fresh reading.
                pinned=boundary_identity_of(self.control, attempt_id))
            self.checkpoint("adopted-boundary")
            adapter = self._adapter(roots, delivery, orphan, launched,
                                    boundary)
            if fresh:
                answer = request_runtime_start(
                    self.control, adapter, attempt_id=attempt_id,
                    inputs=roots["inputs"])
            else:
                answer = reconcile_runtime(self.control, adapter,
                                           attempt_id=attempt_id)
        except (SourceRefusal, ContractRefusal):
            self._unwound(adapter, delivery, launched, fresh)
            raise
        self.checkpoint("runtime")
        return answer

    def _unwound(self, adapter, delivery, launched, fresh):
        """End what THIS attempt's pre-start composition still holds.

        BEFORE A START IS THE WHOLE CONDITION, and re-review [P1] corrected
        what it used to be. Ownership was read as "did this invocation author
        it", which left a launch document published by a process that crashed
        before its credential, adopted by the next one and then stranded by an
        ordinary provider refusal -- present forever, with no runtime that
        could ever have mounted it. What decides is the state the manager
        already proved: `not-started` says no runtime received either
        delivery, so both are this composition's to end. After a start was
        requested neither is: a container may hold the mount, and removing a
        mount source out from under one is the act the credential contract
        calls worse than leaving it.

        AN OWNER THAT ALREADY DECIDED IS NOT SECOND-GUESSED, and re-review
        2026-09-03T22:20:58Z [P1] is why this comes first. `fresh` is the axis
        as it stood BEFORE the start was requested, so a start that reached the
        engine, CREATED a container and then reported failure arrived here
        still called fresh -- and this removed the very mounts that container
        holds. `OciAdapter._undelivered` had already asked the engine, seen the
        live runtime and left both roots `unresolved` on purpose; it said so
        only in refusal prose, so nothing here could tell. It keeps that answer
        now, and an adapter carrying one has settled both mounts by whatever
        rule its own evidence supports. There is nothing left here to end.

        TWO CONDITIONS THIS IS NOT, because both were tried and each broke a
        rule pinned above. The execution AXIS skips the settled-`uncertain`
        path, where nothing was established and a colliding bearer must still
        be released. The attached runtime IDENTITY cannot even be read on that
        same path, because the attempt row carries the very value §13 is
        refusing over -- the read that would decide is blocked by the condition
        this teardown exists to clear. Neither is a fact about who decided;
        the settlement is.

        `None` IS THE ORDINARY CASE and keeps `fresh` as the whole rule: a
        refusal raised before the adapter existed, or before `start` reached
        the settlement, is one where no runtime owner decided anything and the
        deliveries are this composition's as before.

        THE CREDENTIAL FIRST, because its teardown is what proves the bytes
        gone and only then releases the registered value -- which is what lets
        the caller read durable state again when the provider's answer
        collided with it.
        """
        if adapter is not None and adapter.settlement is not None:
            return
        if not fresh:
            return
        if delivery is not None:
            self.credential_home.tear_down(delivery)
        if launched is not None:
            launch.discard(launched.root)

    # -- W81857: the durable file exchange -----------------------------------
    #
    # THREE ENTRY POINTS AND ONE RECONSTRUCTION. Every pass rebuilds this
    # attempt's launch and exchange delivery from durable state -- nothing is
    # carried in a field, and the process that started the container has no
    # standing the next one lacks. That is the whole point of the transport:
    # the manager's lifetime is not the container's, so a restarted manager
    # reaches exactly the same delivery by rereading exactly the same files.

    def observed_exchange(self, stage):
        """This attempt's exchange, as an observation that never raises.

        THE PROJECTION READS THIS FOR EVERY STAGE ON EVERY TICK, which is why
        a refusal here is caught and reported rather than propagated. The
        acceptance requires a faulted stage to leave every other stage
        observable; an adoption refusal that escaped would make one damaged
        launch root stop the sweep from observing anything at all.

        WHAT COMES BACK IS SAFE. The category and the code and nothing else --
        a refusal's prose is composed from values this deployment read,
        including values a worker wrote, and the exchange's durable-evidence
        rule does not stop applying because the value is on its way to a
        status document.
        """
        try:
            launched = self._adopted(stage["attempt_id"])
            if launched is None or launched.exchange is None:
                return None
            return exchange.observation(launched.exchange)
        except ContractRefusal as refusal:
            return {"transport": exchange.EXCHANGE_TRANSPORT,
                    "sequence_id": None, "command": None, "receipt": None,
                    "states": [], "terminal": None, "foreign": [],
                    "state": "unreadable",
                    "unreadable": {"category": refusal.category,
                                   "code": refusal.code}}

    def refresh_runtime(self, stage):
        """Ask the ENGINE what this attempt's attached runtime is now.

        W85500. THE SERVING LOOP'S ONE RUNTIME READ, and until this existed
        there was none after the start. `request_runtime_start` attaches a
        runtime and records it; `_prepared` reconciles only while a stage
        still projects `claimed`; and `ending` reconciles only after an
        `answered` terminal -- which an exceptional stage never reaches,
        correctly, because it owes no act. So a worker that wrote a faulted
        terminal and exited was projected `running` for as long as anybody
        looked, while the engine independently reported the exact runtime
        exited.

        WHAT IT MAY NOT DO is the whole boundary. `reconcile_runtime` lists by
        the complete immutable assignment labels, observes the exact attached
        identity even when the listing is empty, and records the answer. It
        starts nothing. This composition gives it a NAMING-ONLY adapter: no
        credential is read, resolved or registered, no launch document is
        authored or adopted, no command is published, no provider is invoked,
        and no workspace material is written.

        NOTHING TO REFRESH IS AN ANSWER, not a refusal. An attempt that never
        attached a runtime has nothing for an engine to be asked about, and
        asking would be this deployment inventing a question about a container
        that does not exist. `None` is what the sweep reports as `not-asked`.

        AND IT NEVER MANUFACTURES QUIESCENCE. What comes back is whatever the
        reconciliation recorded. A stopped container is `quiescent` on the
        RUNTIME axis and says nothing whatever about the worker's answer; the
        ending stays gated on a correlated `answered` terminal.
        """
        attempt_id = stage["attempt_id"]
        state = attempt_runtime_of(self.control, attempt_id)
        if state is None or state["runtime_id"] is None:
            return None
        # A RUNTIME ALREADY AT THE END OF ITS AXIS IS NOT ASKED ABOUT AGAIN.
        # The transition table names nothing after `destroyed`, so an engine
        # answer could only be refused by the recorder -- and every sweep after
        # a cleanup would become a refusal this pass then has to contain.
        if state["execution_runtime"] == "destroyed":
            return None
        roots = workspaces.assignment_workspace(
            self.group, self.given["workspace_storage"], attempt_id)
        # NO CREDENTIAL, NO LAUNCH DELIVERY, NO ORPHAN. All three are absent on
        # purpose: this call identifies and observes, and every one of those
        # operands exists for a START.
        adapter = self._adapter(roots, None, None, None)
        # THE ENGINE'S OWN FAILURES, NAMED BY THE DEPLOYMENT THAT OWNS THEM.
        # Review 2026-09-04T19:08:40Z [P1]: the manager caught `OSError` and
        # then caught `Exception`, so it was deciding what an engine failure
        # is on behalf of every deployment -- and turning everything else into
        # report data `serve` discards on the next tick.
        #
        # THESE TWO ARE ONE OPERATIONAL FACT AND TWO PYTHON TYPES. The runner
        # is `subprocess.run`: an invocation that could not be made at all --
        # a missing engine binary -- arrives as `OSError`, and one that hit
        # its deadline arrives as `TimeoutExpired`, which is not an `OSError`
        # and used to reach the blanket branch. Both mean the question could
        # not be put, and neither says anything about whether the container is
        # still there.
        #
        # A DEAD DAEMON IS NOT ONE OF THEM, and review 2026-09-04T21:52:30Z
        # measured that through this exact composition. The CLI runs perfectly
        # well and answers NON-ZERO, so `OciAdapter.list` refuses it `policy /
        # denied` and the manager reports that category and code. It is
        # contained per stage like any other refusal and it records nothing on
        # the runtime axis, so the accepted boundary holds -- but it is not
        # `uncertain / engine-unreachable`, and this comment used to say it
        # was. Telling an unreachable daemon apart from an ordinary policy or
        # integrity refusal needs a typed adapter failure that does not exist
        # yet; wrapping every OCI `ContractRefusal` instead would report a
        # mislabelled runtime or a hand-edited listing as an unreachable
        # engine, which is a different fact entirely.
        #
        # NOTHING WIDER. A defect in this composition is not an unreachable
        # engine and must not be dressed as one; it escapes, and the manager
        # lets it.
        try:
            reconcile_runtime(self.control, adapter, attempt_id=attempt_id)
        except (OSError, subprocess.TimeoutExpired) as unreachable:
            raise RefreshUnavailable(unreachable) from unreachable
        # THE RECORDED AXIS, READ BACK, and not the reconciliation's own
        # answer document. That document reports what this call OBSERVED, in
        # one of several shapes depending on which branch it took; what the
        # sweep reports is the durable runtime axis, which is the same fact
        # every other reader sees and the one a restart reaches too. Reading
        # it back also means this answer cannot disagree with the projection
        # taken a moment later in the same tick.
        return {"execution_runtime":
                attempt_runtime_of(self.control,
                                   attempt_id)["execution_runtime"]}

    def command(self, stage, job):
        """Publish THE ONE command sequence into this attempt's exchange.

        THIS IS THE ACT THE WHOLE WORK EXISTS FOR. Before it the container is
        up and has been asked for nothing -- which is the state W81857
        reproduced and which every health and elapsed-time signal reports as
        indistinguishable from useful execution. After it the command is a
        durable file, and neither this process nor the manager that restarts
        after it is needed for the container to act on it.

        IT IS SAFE TO CALL TWICE AND THAT IS NOT AN ACCIDENT. The document is
        authored from the attempt alone, so two managers compose identical
        bytes under an identical derived name; the publisher adopts an
        identical existing command and refuses a different one rather than
        replacing a command the worker may already have receipted.
        """
        self._matches(stage, job)
        attempt_id = stage["attempt_id"]
        launched = self._adopted(attempt_id)
        if launched is None or launched.exchange is None:
            _refuse(f"attempt {attempt_id!r} has no exchange delivery to "
                    f"publish a command into; a command nothing mounts is a "
                    f"file no container will ever read",
                    category="refused", code="precondition")
        published = exchange.publish_command(
            launched.exchange,
            exchange.command_document(session=self._session_of(attempt_id),
                                      attempt_id=attempt_id))
        # THE HOST PATH STAYS HERE. What the control plane reports is whether
        # this call published the sequence and which command it is; where this
        # deployment keeps its launch home is a fact about the machine and not
        # about the stage, and a sweep report is read by whoever is watching
        # the service rather than by whoever provisioned it.
        return {"published": published["published"],
                "command_digest": published["command_digest"]}

    def ending(self, stage, job):
        """Drive ONE answered attempt through the already-ruled ending.

        THE ORDER IS THE RULING'S AND IS NOT AN IMPLEMENTATION CHOICE:

          1. positively quiesce and reconcile the exact runtime;
          2. record the worker's returned disposition;
          3. freeze the declared output for that disposition;
          4. collect it and record the intake receipt;
          5. decide every artifact's retention under the configured policy;
          6. end the exact Authority assignment by passing it to the
             configured review Route; and only then
          7. authorize runtime cleanup.

        `authorize_cleanup` REFUSES WHILE THE ASSIGNMENT IS LIVE, so cleaning
        up before the pass is not an implementation option. Conversely, ending
        the assignment before intake can quarantine the result if the
        collection races that ending. The pass therefore follows intake and
        retention and precedes cleanup, which is where W44657 put it.

        AND IT IS ASKED AGAIN UNTIL IT IS FINISHED. Review
        2026-09-04T03-43-45Z [P1]: the projection used to call a stage
        `completed` the moment its output was frozen, which is the THIRD of
        those seven steps -- so a process death after `request_freeze` left
        intake, retention, the Authority pass and cleanup owed forever while
        the board reported the Work done and its assignment stayed live. The
        stage now stays `answering` until the manager's own cleanup axis is
        terminal, and every step above replays: `stop` re-observes an already
        quiescent runtime, `observe` of the same disposition is a no-op, the
        freeze replays its immutable record, intake and retention replay their
        journalled operations, and the pass is effectively-once by identity. So
        this whole function is safe to re-enter at any boundary a crash can
        land on.

        THE WORKER'S TERMINAL IS A CLAIM AND NOT A SETTLEMENT. What it decides
        here is only that the ending is owed and which disposition to ask the
        freeze about; the freeze validates `/output/output.json` itself, the
        quiescence is a positive observation of the exact runtime, and intake
        measures the bytes rather than believing them. A container that
        published `answered` over an empty output root reaches a refusal from
        those owners, not a completed stage. Its `manifest_digest` is compared
        with the digest the freeze produced, below, so a terminal naming
        another envelope cannot ride a separately valid one.

        NO ABANDONMENT AND NO RETRY. A faulted, lost or incomplete exchange is
        REPORTED -- the projection reads it as `exceptional` -- and this
        composition does not end it. W44716's abandonment is the owner for a
        started attempt policy decides to end, and deciding that is not this
        vertical slice's.
        """
        self._matches(stage, job)
        row = self._claim(stage)
        attempt_id = stage["attempt_id"]
        launched = self._adopted(attempt_id)
        if launched is None or launched.exchange is None:
            _refuse(f"attempt {attempt_id!r} has no exchange delivery to end",
                    category="refused", code="precondition")
        view = exchange.observation(launched.exchange)
        terminal = view["terminal"]
        if terminal is None or terminal["ending"] != "answered":
            _refuse(f"attempt {attempt_id!r}'s exchange reports "
                    f"{view['state']!r}; only a correlated answered terminal "
                    f"authorizes the successful ending",
                    category="refused", code="precondition")
        disposition = terminal["disposition"]
        if disposition not in DISPOSITIONS:
            _refuse(f"attempt {attempt_id!r}'s worker answered disposition "
                    f"{disposition!r} and this manager knows "
                    f"{', '.join(DISPOSITIONS)}; a disposition nobody can name "
                    f"is not one to freeze an output under",
                    category="refused", code="precondition")
        state = attempt_runtime_of(self.control, attempt_id)
        runtime_id = state["runtime_id"]
        if runtime_id is None:
            _refuse(f"attempt {attempt_id!r} answered its command and this "
                    f"manager holds no runtime identity for it; a freeze takes "
                    f"a positively quiescent runtime and there is nothing here "
                    f"to observe", category="refused", code="precondition")
        roots = workspaces.assignment_workspace(
            self.group, self.given["workspace_storage"], attempt_id)
        delivery, orphan = self._credential(attempt_id, state, roots)
        adapter = self._adapter(roots, delivery, orphan, launched)
        # QUIESCENCE IS ORDERED, NOT WAITED FOR. The container is started
        # INTERACTIVE so its idle PID 1 outlives the provider it ran, and
        # `reconcile_runtime` observes rather than stops.
        #
        # ONLY `quiescent`, AND `absent` IS NOT THE SAME PROOF: a runtime that
        # is merely GONE was never observed to have finished writing, so
        # freezing its output would seal bytes nobody watched the end of.
        stopped = adapter.stop({"runtime_id": runtime_id,
                               "operation_id": f"quiesce:{attempt_id}"})
        if stopped.get("state") != "quiescent":
            _refuse(f"attempt {attempt_id!r}'s runtime was ordered to stop and "
                    f"observed {stopped.get('state')!r}; a freeze takes a "
                    f"positively quiescent runtime, and an absent one is not "
                    f"the same proof because its writer was never seen to "
                    f"finish", category="refused", code="precondition")
        reconcile_runtime(self.control, adapter, attempt_id=attempt_id)
        observe(self.control, attempt_id=attempt_id, axis="worker_disposition",
                value=disposition)
        frozen = request_freeze(self.control, self.port, adapter,
                                attempt_id=attempt_id,
                                disposition=disposition)
        # W81857 review 2026-09-04T03-43-45Z [P1]: THE TERMINAL'S DIGEST IS
        # COMPARED, AND THIS IS THE VALUE TO COMPARE IT WITH.
        #
        # `manifest_digest` was carried and never enforced, so an answered
        # terminal naming another envelope drove the whole success ending
        # whenever a separately valid `/output/output.json` happened to exist --
        # which defeats the correlation the member was added to provide.
        #
        # IT IS THE SEALED RESULT'S `completion_manifest_digest`, NOT THE
        # FROZEN RESULT'S OWN `manifest_digest`. Those are two documents:
        # `manifest_digest` names the MANAGER's result manifest, and the
        # worker's terminal names the WORKER's completion envelope. Comparing
        # the terminal against the result manifest would refuse every honest
        # attempt, which the real-composition regression caught. `sealing`
        # opens `/output/output.json` itself, validates its shape against the
        # declarations and recomputes its digest over the bytes it read, and
        # records that digest in the sealed result -- so this compares the
        # worker's claim with this manager's own independent answer about the
        # same file.
        #
        # THE COMPARISON CANNOT HAPPEN EARLIER, because that answer does not
        # exist until the freeze commits.
        #
        # A MISMATCH REFUSES AND SETTLES NOTHING FURTHER. The freeze is durable
        # and replays; intake, retention, the Authority pass and cleanup do not
        # happen, so no result reaches review and no runtime is removed on the
        # strength of a correlation that failed. The stage stays `answering`
        # and the sweep reports the refusal every tick, which is an operator's
        # problem to look at rather than a silence.
        sealed = load_manifest(self.control, frozen["manifest_digest"],
                               "resultManifest")
        validated = (sealed or {}).get("completion_manifest_digest")
        if terminal["manifest_digest"] != validated:
            _refuse(f"attempt {attempt_id!r}'s worker answered completion "
                    f"manifest {terminal['manifest_digest']!r} and this "
                    f"manager validated {validated!r}; a terminal that names "
                    f"another envelope is not evidence about the output this "
                    f"manager froze",
                    category="refused", code="operation-collision")
        receipt = request_intake(self.control, self.port, adapter,
                                 attempt_id=attempt_id)
        held = list(receipt["artifacts"])
        decided = decide_retention(
            self.control, self.port, adapter, attempt_id=attempt_id,
            artifact_ids=[one["artifact_id"] for one in held],
            disposition=self.given["retention_disposition"],
            retention_policy_digest=self.given["retention_policy_digest"])
        passed = self._passed(attempt_id, _assignment(row))
        authorize_cleanup(
            self.control, self.port, adapter, attempt_id=attempt_id,
            retention_policy_digest=self.given["retention_policy_digest"])
        return {"disposition": disposition,
                "manifest_digest": frozen["manifest_digest"],
                "result_id": frozen["result_id"],
                "receipt_digest": receipt["receipt_digest"],
                "artifacts": sorted(one["artifact_id"] for one in held),
                "retention": decided["disposition"],
                "review_route": passed["route"]}

    def _passed(self, attempt_id, expect):
        """The authority's own answer to this deployment's pass, held to shape.

        WHAT IS KEPT IS WHAT THE AUTHORITY SAID, not what this deployment asked
        for. A route echo is not the proof and taking one as proof was a
        measured defect in the supervised composition: an answer ABOUT ANOTHER
        GENERATION that happened to echo the route was accepted as this
        attempt's pass, and cleanup then ran on the strength of a transition
        that ended somebody else's assignment. The ASSIGNMENT the authority
        says it ended is what is compared, and the route is checked beside it
        rather than instead of it.

        EFFECTIVELY ONCE BY IDENTITY. The operation id is derived from this
        attempt, so an exact replay replays the authority's own committed
        answer instead of passing a second time; a different generation carries
        a different signature and collides rather than silently reusing this
        one's pass.
        """
        if self.session is None:
            _refuse("this deployment holds no Authority pass capability, so "
                    "an ended attempt's Work cannot reach its review Route",
                    category="refused", code="capability")
        route = self.given["review_route"]
        answered = self.session.pass_work({
            "expect": dict(expect), "operation_id": f"pass:{attempt_id}",
            "to_route": route, "comment": PASS_COMMENT})
        if type(answered) is not dict:
            _refuse(f"the authority answered the review pass with "
                    f"{type(answered).__name__} and this deployment reads a "
                    f"document", category="refused", code="precondition")
        missing = sorted(one for one in PASS_MEMBERS if one not in answered)
        if missing:
            _refuse(f"the review pass answered without {', '.join(missing)}; "
                    f"a document missing either the ended assignment or the "
                    f"route it moved the Work to is not evidence this "
                    f"assignment ended", category="refused",
                    code="precondition")
        if answered["assignment"] != expect:
            _refuse(f"the review pass ended {answered['assignment']!r} and "
                    f"this attempt holds {expect!r}; an answer about another "
                    f"assignment is not evidence that this one ended",
                    category="refused", code="operation-collision")
        if answered["route"] != route:
            _refuse(f"the assignment was passed to {answered['route']!r} and "
                    f"this deployment asked for {route!r}",
                    category="refused", code="precondition")
        if answered["cause"] != "pass" or answered["fenced"]:
            _refuse(f"the assignment ended {answered['cause']!r} with fenced "
                    f"{answered['fenced']!r}; the approved transition is an "
                    f"unfenced pass and nothing else is one",
                    category="refused", code="precondition")
        if answered["phase"] != "queued" or answered["gate"] is not None:
            _refuse(f"the assignment was passed into phase "
                    f"{answered['phase']!r} behind gate {answered['gate']!r}; "
                    f"the approved handoff leaves the Work queued and ungated "
                    f"for its review route to claim",
                    category="refused", code="precondition")
        return {"route": answered["route"], "cause": answered["cause"],
                "phase": answered["phase"], "gate": answered["gate"]}

    def _session_of(self, attempt_id):
        """The one container session identity this attempt's launch carries.

        DERIVED FROM THE ATTEMPT, so the process that publishes the command and
        the process that authored the launch document reach the same value
        without either remembering anything.
        """
        return "session-" + digest(attempt_id)[7:31]

    def _adopted(self, attempt_id):
        """This attempt's launch and exchange delivery, from durable state.

        ADOPTION AND NOT MATERIALIZATION. A delivery that is absent here is one
        no container ever mounted, and authoring a replacement under a running
        container would turn lost durable evidence into state that looks valid
        -- which is the correction `_launch_document` records for the launch
        document and which applies with more force to a namespace the worker
        writes.
        """
        return launch.adopt(
            self.given["launch_home"], attempt_id=attempt_id,
            session=self._session_of(attempt_id),
            contract=self.given["launch_contract"],
            role=self.given["launch_role"],
            transport=exchange.EXCHANGE_TRANSPORT, workspace_group=self.group)

    def _launch_document(self, attempt_id, state):
        """Adopt this attempt's exact launch delivery; author one ONLY before
        a start.

        Review 2026-09-03T18:16:57Z [P1]: this materialized whenever `adopt`
        answered absence, including after the start operation had committed.
        The launch owner says absence is ordinary only until a caller knows a
        runtime started, and that caller must then refuse -- and the pinned
        finding says contradictory or partial material refuses rather than
        being repaired. Authoring a fresh document under a container that may
        already hold the mount turns lost durable evidence into state that
        looks valid.

        AND EVERY REFUSAL FROM HERE IS SETTLED THE SAME WAY. Re-review
        2026-09-03T19:24:19Z [P1]: only the ABSENCE branch used to reach the
        identification, so contradictory or partial launch material -- which
        `adopt` refuses rather than answering `None` for -- ended the stage
        with the runtime still unnamed. Nothing is settled here at all now:
        the caller's one handler identifies the runtime and records the
        ending for every boundary alike.
        """
        given = self.given
        launched = self._adopted(attempt_id)
        if launched is not None:
            return launched
        if state["execution_runtime"] != "not-started":
            _refuse("this attempt's start was already requested and its launch "
                    "delivery is absent; a replacement authored now would be "
                    "mounted by nothing that exists and would claim evidence "
                    "this deployment does not have",
                    category="refused", code="precondition")
        # W81857: THE PRODUCTION LAUNCH SELECTS THE FILE EXCHANGE, and its two
        # namespaces are created here -- before the start, inside the same
        # attempt-private root, under a parent this manager closes read-only
        # once every entry exists. A namespace created after the start is one
        # nothing mounts, and there is no second chance at a mount table.
        return launch.materialize(
            given["launch_home"], attempt_id=attempt_id,
            session=self._session_of(attempt_id),
            contract=given["launch_contract"], role=given["launch_role"],
            transport=exchange.EXCHANGE_TRANSPORT, workspace_group=self.group)

# What this deployment says when it hands an implementation result on. The
# authority records it beside the transition, so it is written once here rather
# than composed at the call site.
PASS_COMMENT = ("the implementation worker answered, its declared output is "
                "frozen, collected and retained, and the candidate is ready "
                "for independent review")

# THE CLOSED RESULT A PASS ANSWERS WITH. `AuthorityCore.pass_work` returns the
# ended assignment beside the new Route, and every member of it is read at
# `_passed` -- holding a document to the members it must carry is what makes
# that a comparison rather than a `get` that shrugs at an absence.
PASS_MEMBERS = ("assignment", "route", "cause", "phase", "gate", "fenced")


class _Operations(ManagerOperations):
    __slots__ = ("_dispose", "_worker")

    def __init__(self, *arguments, worker, dispose, **keywords):
        super().__init__(*arguments, **keywords)
        self._worker = worker
        self._dispose = dispose

    def admit(self, stage, job):
        return self._worker.admit(super().admit, stage, job)

    def close(self):
        dispose, self._dispose = self._dispose, None
        if dispose is not None:
            dispose()


def operations_from(document, job_store, control_store, *, engine_run=None,
                    credential_provider=None, clock=None, checkpoint=None):
    """Build the exact manager operations from one already-read document.

    ``job_store`` is accepted because every factory has the same public shape.
    W83781 gave it one thing this deployment must read: the Authority the
    store is bound to, which is compared with the configured Authority before
    any durable side effect.  The two injectable capabilities are for focused
    verification.  The public ``factory`` supplies the real subprocess runner
    and private source reader.
    """
    given = _held(document)
    # W83781: THE JOB STORE'S AUTHORITY BINDING IS COMPARED FIRST, before this
    # deployment configures anything.
    #
    # `job_store` used to be deleted here with a note that this deployment
    # needs no private Job-store read. That was true when a Job store knew
    # nothing about which Authority it belonged to; it is not true now. The
    # store's episode identities are derived in its Authority's namespace and
    # the containers those identities name carry that Authority as an
    # immutable label -- so a Job store bound to one Authority driven by a
    # configuration naming another would start runtimes labelled for an
    # Authority its own identities were never derived in.
    #
    # BEFORE ANY DURABLE SIDE EFFECT, and the ordering is the whole
    # correction. Everything below this line writes: the workspace group and
    # storage are configured on the control store, a profile is certified,
    # storage is allocated and an Authority is opened. A mismatch found after
    # any of those would have left this deployment half-configured against a
    # store it must not touch at all.
    held = getattr(job_store, "authority_uuid", None)
    if held != given["authority_uuid"]:
        _refuse(f"this Job store is bound to Authority {held!r} and this "
                f"configuration names {given['authority_uuid']!r}; a store's "
                f"episode identities are derived in its own Authority's "
                f"namespace, so driving it from another one would start "
                f"runtimes labelled for an Authority those identities were "
                f"never derived in", category="refused",
                code="operation-collision")
    provider = credential_provider
    if provider is None:
        if given["credential_sources"] is None:
            _refuse("the production credential provider requires an absolute "
                    "credential_sources registry path", category="refused",
                    code="capability")
        provider = UserCredentialSources(
            given["credential_sources"], max_bearer=credentials.MAX_BEARER)
    configure_workspace_group(control_store, given["workspace_group"])
    workspaces.configure_workspace_storage(control_store,
                                           given["workspace_storage"])
    certify_profile(control_store, "runtime", given["profile_name"],
                    given["profile_digest"])
    group = configured_workspace_group(control_store)
    credentials.CredentialHome(given["credential_home"])
    # Construct the adapter's static half now.  No runtime or assignment root
    # exists yet, so two distinct absent placeholders are used only to force
    # the engine, identity, network and workspace-group checks before admission.
    OciAdapter(
        given["engine"], EnginePort(engine_run or _engine_run),
        identity={"image_digest": given["image_digest"],
                  "profile_digest": given["profile_digest"],
                  "policy_digest": given["policy_digest"],
                  "adapter_digest": given["adapter_digest"]},
        assignment_roots={"inputs": os.path.join(given["workspace_storage"],
                                                  ".preflight-input"),
                          "workspace": os.path.join(
                              given["workspace_storage"],
                              ".preflight-workspace")},
        posture="execution", workspace_group=group,
        network=given["network"], interactive=True)
    authority = Authority.open(
        given["authority_store"],
        expected_authority_uuid=given["authority_uuid"])
    try:
        if authority.principal_of(given["participant"]) != given["principal"]:
            _refuse("the configured participant resolves to another principal",
                    category="refused", code="capability")
        projected = authority.project_work(
            given["input_manifest"]["work_ref"]["work_id"])
        if projected is None or projected["authority_uuid"] \
                != given["authority_uuid"]:
            _refuse("the configured bootstrap Work is absent from this "
                    "Authority", category="refused", code="precondition")
        session = _AuthoritySession(authority.session(given["participant"]))
        port = AuthorityPort(session, claim_signature)
        # Authority bootstrap and the provider registry are deployment-side
        # capabilities.  The runtime composer gets neither path; it receives
        # only the already-minted restricted port and provider callable.
        runtime = {member: value for member, value in given.items()
                   if member not in ("authority_store", "principal",
                                     "credential_sources")}
        worker = _SingleWorker(
            runtime, control_store, port, credential_provider=provider,
            engine_run=engine_run or _engine_run, session=session, clock=clock,
            checkpoint=checkpoint)
        return _Operations(
            control_store, port, mint_bearer=_bearer,
            deliver_bearer=worker.delivered, start_runtime=worker.start,
            # W81857: THE THREE EXCHANGE CAPABILITIES, supplied separately
            # because they are three different authorities. Reading is a pure
            # observation the projection performs on every tick for every
            # stage; publishing the command is the one act that commits this
            # attempt to a provider turn; ending it freezes, takes custody of
            # and hands on somebody's work.
            observe_exchange=worker.observed_exchange,
            dispatch_exchange=worker.command,
            conclude_attempt=worker.ending,
            # W85500: THE FOURTH, AND IT IS SERVING-ONLY. It records, so no
            # status surface gets it; the observation-only composition is
            # built without it for exactly that reason.
            refresh_runtime=worker.refresh_runtime,
            worker=worker, dispose=authority.dispose)
    except BaseException:
        authority.dispose()
        raise


class _Observation:
    """W85500: the durable exchange reader, composed from NOTHING ELSE.

    WHAT IT IS FOR. `tools.job_manager status` could never report a worker's
    terminal, because `_ReadOnly` has no exchange read at all -- so the
    run6 faulted terminal sat on disk, correlated and readable, while the one
    command an operator runs printed `exchange: null`. The parser was not the
    problem; nothing had been given a way to look.

    WHAT IT DELIBERATELY IS NOT. `operations_from` configures the workspace
    group and storage on the control store, certifies a profile, constructs a
    credential home, opens an Authority and mints a session -- and hands back
    an object carrying mint, delivery, start, dispatch, ending and pass. This
    class does none of that and carries none of it. It reads immutable
    configuration, it reads the already-open control store, and it adopts
    launch material from disk.

    IT HOLDS NO CONTROL STORE WRITE AND NO ENGINE. There is no runtime refresh
    here on purpose: reconciling RECORDS what it saw, and a status command
    that recorded would be a read that mutates. Runtime freshness belongs to
    the serving loop.
    """

    def __init__(self, document, control_store, *, job_store=None):
        given = _held(document)
        # THE JOB STORE IS ACCEPTED AND NOT READ, exactly as `operations_from`
        # accepts it: every factory has the same public shape.
        #
        # AN EARLIER DRAFT OF THIS CLASS COMPARED THE STORE'S AUTHORITY
        # BINDING against the configured one, and that check has been removed
        # rather than kept. It was written while W83781's candidate was in
        # this checkout, and it reads `JobStore.authority_uuid` -- an
        # attribute W83781 introduces and which this Work's declared base does
        # not have. On this base `getattr` answers `None`, so the comparison
        # would have refused EVERY observation, including every correct one.
        #
        # THE ORDERING IS THE REASON IT STAYS OUT. W83781 is ordered behind
        # this Work rather than integrated over it, so a candidate here must
        # not depend on it. The binding belongs to that Work's boundary and
        # is its to enforce, in `operations_from` and in the store itself.
        #
        # W83781 IS NOW INTEGRATED OVER W85500, WHICH SUPERSEDES THE ORDERING
        # SENTENCE ABOVE AND NOT THE DECISION. The check still stays out, for
        # a reason that is now measurable rather than provisional:
        # `JobStore.open` REQUIRES the Authority operand and refuses a store
        # bound to another one without touching it, so by the time a store
        # reaches this factory its binding has already been proved against
        # what the operator named. What `operations_from` compares is a second
        # question -- the CONFIGURATION's Authority against the store's -- and
        # it compares it because everything after that line WRITES. This one
        # reads. A configuration naming another Authority reaches another
        # Authority's launch home, where this store's namespaced attempt ids
        # do not exist, so the answer is `exchange: null` rather than a
        # stranger's terminal. Refusing here as well is a design decision that
        # belongs to a pinned ruling and an independent review, not to a
        # rebase.
        del job_store
        self.given = given
        self.control = control_store
        self.launch_home = given["launch_home"]
        # THE SAME GROUP THE SERVING DEPLOYMENT READS, from the same store.
        # `launch.adopt` validates the delivery against it, so an observation
        # that skipped it would either refuse every real launch or -- worse --
        # accept one belonging to another group's workspace.
        self.group = configured_workspace_group(control_store)

    @staticmethod
    def _session_of(attempt_id):
        """The same derivation `_SingleWorker` uses, for the same reason.

        Derived from the attempt, so a process that authored nothing reaches
        the value the authoring process used without remembering anything.
        """
        return "session-" + digest(attempt_id)[7:31]

    def observe_exchange(self, stage):
        """The same reconstruction the serving deployment performs.

        NEVER RAISES, for the reason the serving one does not: the projection
        reads this for every stage on every pass, and one damaged launch root
        must not stop a status run from reporting anything at all. What comes
        back on a refusal is the category and the code and nothing else --
        a refusal's prose is composed from values a worker wrote.
        """
        try:
            attempt_id = stage["attempt_id"]
            launched = launch.adopt(
                self.launch_home, attempt_id=attempt_id,
                session=self._session_of(attempt_id),
                contract=self.given["launch_contract"],
                role=self.given["launch_role"],
                transport=exchange.EXCHANGE_TRANSPORT,
                workspace_group=self.group)
            if launched is None or launched.exchange is None:
                return None
            return exchange.observation(launched.exchange)
        except ContractRefusal as refusal:
            return {"transport": exchange.EXCHANGE_TRANSPORT,
                    "sequence_id": None, "command": None, "receipt": None,
                    "states": [], "terminal": None, "foreign": [],
                    "state": "unreadable",
                    "unreadable": {"category": refusal.category,
                                   "code": refusal.code}}


def observation_from(document, job_store, control_store):
    """Build the observation-only surface from one already-read document."""
    return _Observation(document, control_store, job_store=job_store)


def observing_factory(job_store, control_store):
    """The `status --observe` entry point, named the same way `factory` is."""
    place = os.environ.get(CONFIG_ENV)
    if place is None:
        _refuse(f"{CONFIG_ENV} names the required absolute deployment "
                "configuration path", category="refused", code="capability")
    return observation_from(_read(place), job_store, control_store)


def factory(job_store, control_store):
    place = os.environ.get(CONFIG_ENV)
    if place is None:
        _refuse(f"{CONFIG_ENV} names the required absolute deployment "
                "configuration path", category="refused", code="capability")
    return operations_from(_read(place), job_store, control_store)
