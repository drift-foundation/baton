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
                                 check_no_durable_secret, digest)
from baton_v12.job_manager import ManagerOperations
from baton_v12.worker_manager import (AuthorityPort, accept_offer,
                                      activate_assignment,
                                      attempt_runtime_of, certify_profile,
                                      claimed_offers_for,
                                      configure_workspace_group,
                                      configured_workspace_group,
                                      attempt_preparation_failure_of,
                                      attempt_start_failure_of,
                                      label_context, record_attempt,
                                      reconcile_runtime,
                                      refuse_runtime_preparation,
                                      request_runtime_start, retain_manifest)
from baton_v12.worker_manager import credentials, launch, workspaces
from baton_v12.worker_manager.oci import ENGINES, EnginePort, OciAdapter

from tools.user_credentials import SourceRefusal, UserCredentialSources

__all__ = ["CONFIG_ENV", "CONFIG_SCHEMA", "factory", "operations_from"]

CONFIG_ENV = "BATON_V12_SINGLE_WORKER_CONFIG"
CONFIG_SCHEMA = "baton.v12.single-worker-deployment/1"
MAX_CONFIG_BYTES = 1024 * 1024

_MEMBERS = (
    "schema", "authority_store", "authority_uuid", "participant",
    "principal", "profile_name", "profile_digest", "policy_digest",
    "adapter_name", "adapter_digest", "engine", "image_digest", "network",
    "workspace_storage", "workspace_group", "launch_home",
    "credential_home", "credential_sources", "credential_slots",
    "credential_profile", "input_source", "input_manifest",
    "launch_contract", "launch_role")
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
                   "credential_home", "input_source"):
        given[member] = _path(given[member], f"the configuration's {member}")
    if given["credential_sources"] is not None:
        given["credential_sources"] = _path(
            given["credential_sources"],
            "the configuration's credential_sources")
    for member in ("authority_uuid", "participant", "principal",
                   "profile_name", "adapter_name", "engine", "network",
                   "launch_contract", "launch_role"):
        given[member] = _text(given[member],
                              f"the configuration's {member}")
    for member in ("profile_digest", "policy_digest", "adapter_digest",
                   "image_digest"):
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
    if given["launch_role"] != "implementation":
        _refuse("the single-worker deployment launches only the "
                "implementation role", category="policy", code="denied")
    if len(manifest["sources"]) != 1:
        _refuse("the bootstrap deployment accepts exactly one staged source",
                category="policy", code="denied")
    if type(given["credential_slots"]) is not list:
        _refuse("the configuration's credential_slots is one list")
    if type(given["credential_profile"]) is not dict:
        _refuse("the configuration's credential_profile is one object")
    given["credential_resolution"] = credentials.resolved_delivery(
        given["credential_slots"], profile=given["credential_profile"])
    launch.launch_document(session="single-worker-preflight",
                           contract=given["launch_contract"],
                           role=given["launch_role"])
    measured = workspaces.directory_manifest(given["input_source"])
    if measured != manifest["sources"][0]["content_manifest"]:
        _refuse("the configured bootstrap source does not match the input "
                "manifest's content identity", code="digest")
    return given


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


class _SingleWorker:
    """The launch capability; it receives no Authority bootstrap or path."""

    def __init__(self, given, control, port, *, credential_provider,
                 engine_run, clock=None, checkpoint=None):
        self.given = given
        self.control = control
        self.port = port
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

    def _input(self, roots, assignment):
        given = self.given
        manifest = given["input_manifest"]
        try:
            held_input, held_assignment = workspaces.read_input_root(
                roots["inputs"])
        except ContractRefusal:
            if os.listdir(roots["inputs"]):
                # Review 2026-09-03T17:23:00Z [P1]: this raised
                # `refused/path`, which is not one of §9's closed pairs -- so
                # the one branch that finds incomplete material rejected its
                # own raising site with an `AssertionError` instead of the
                # typed refusal it meant.  `integrity/path` is the pair this
                # is: a root whose bytes this manager cannot account for.
                _refuse("the bootstrap input root is partial; restart refuses "
                        "rather than completing material whose provenance it "
                        "cannot prove", code="path")
            source = manifest["sources"][0]
            target = os.path.join(roots["inputs"], source["destination"])
            copied = workspaces.copied_manifest(
                given["input_source"], target,
                max_entries=source["content_manifest"]["entry_count"],
                max_bytes=source["content_manifest"]["total_bytes"])
            if copied != source["content_manifest"]:
                _refuse("the staged bootstrap source changed after preflight",
                        code="digest")
            workspaces.compose_input_root(
                roots["inputs"], manifest, assignment,
                assignment=dict(assignment["assignment_ref"]),
                runtime_attempt_id=assignment["runtime_attempt_id"])
            return manifest
        if held_input != manifest or held_assignment != assignment:
            _refuse("the existing bootstrap input root is another delivery",
                    category="refused", code="precondition")
        return held_input

    def _adapter(self, roots, delivery, orphan, launched):
        given = self.given
        manifest = given["input_manifest"]
        return OciAdapter(
            given["engine"], self.engine,
            identity={"image_digest": given["image_digest"],
                      "profile_digest": given["profile_digest"],
                      "policy_digest": given["policy_digest"],
                      "adapter_digest": given["adapter_digest"]},
            assignment_roots=roots, posture="execution",
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}],
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
        assignment = _assignment_manifest(given, row, attempt_id,
                                          stage["offer_id"])
        manifest = self._input(roots, assignment)
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
            adapter = self._adapter(roots, delivery, orphan, launched)
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
        session = "session-" + digest(attempt_id)[7:31]
        launched = launch.adopt(
            given["launch_home"], attempt_id=attempt_id, session=session,
            contract=given["launch_contract"], role=given["launch_role"])
        if launched is not None:
            return launched
        if state["execution_runtime"] != "not-started":
            _refuse("this attempt's start was already requested and its launch "
                    "delivery is absent; a replacement authored now would be "
                    "mounted by nothing that exists and would claim evidence "
                    "this deployment does not have",
                    category="refused", code="precondition")
        return launch.materialize(
            given["launch_home"], attempt_id=attempt_id, session=session,
            contract=given["launch_contract"], role=given["launch_role"])

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

    ``job_store`` is accepted because every factory has the same public shape;
    this deployment needs no private Job-store read and deliberately drops it.
    The two injectable capabilities are for focused verification.  The public
    ``factory`` supplies the real subprocess runner and private source reader.
    """
    del job_store
    given = _held(document)
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
            engine_run=engine_run or _engine_run, clock=clock,
            checkpoint=checkpoint)
        return _Operations(
            control_store, port, mint_bearer=_bearer,
            deliver_bearer=worker.delivered, start_runtime=worker.start,
            worker=worker, dispose=authority.dispose)
    except BaseException:
        authority.dispose()
        raise


def factory(job_store, control_store):
    place = os.environ.get(CONFIG_ENV)
    if place is None:
        _refuse(f"{CONFIG_ENV} names the required absolute deployment "
                "configuration path", category="refused", code="capability")
    return operations_from(_read(place), job_store, control_store)
