"""W110774: the deployment's production integration runtime port.

`work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/
finding-standalone-stage-composition/findings/finding-integration-runtime-port/`
and its approved `HANDOFF-CONTRACT-2026-09-08.md`.

WHAT WAS MISSING, IN ONE SENTENCE. `execution.integrate_next` types a
deployment's runtime port and calls `port.run(delivery, assignment)`; the only
implementations in this tree were focused-test fixtures, so
`stage_execution.Integration.run` refused every integration stage for want of
one. This is that port, and it is a COMPOSER: every act it performs belongs to
an accepted operation of the Worker Manager, the integration coordinator, the
OCI boundary or the evidence-bundle producer, and what this module adds is the
order they go in and the configuration they are given.

WHAT IT IS NOT. It decides nothing about an integration's outcome. It writes no
result, records no Authority receipt, releases no lease, repairs no target byte
and reads no candidate. It cannot: the result is written by the container's own
workload over the delivery's namespaces, and everything after that belongs to
`settle_observed`, `continue_accepted` and the coordinator. A port that could
declare success from a process status would be the success-reporting stub this
record's finding forbids by name.

THE THREE VERBS, AND WHY THEY ARE THREE. `prepare` records and activates the
manager attempt through its own public owners, BEFORE admission asks for a
runtime -- `integrate_next` requires an attempt whose runtime is `not-started`,
and preparing it inside `run` would be too late by one call. `run` is the
accepted port seam and the only one that starts anything. `refresh` observes an
existing runtime through `reconcile_runtime` and starts nothing, mints no
credential and infers no quiescence. `observed` is read-only status and is not
a fourth act: it performs none of the three.

THE LIVE MARKER IS BOOKKEEPING AND NEVER AUTHORITY. `run` remembers the exact
assignment and delivery root it started, so an assembly can tell a NORMAL later
tick of this same execution -- which may continue -- from a reconstructed
serving incarnation, which may not. It lives in memory, so a restart loses it
by construction; an uncertain runtime drops it; and nothing anywhere reads it
in place of the coordinator's own live grant or the manager's own runtime axis.
"""

import os

from baton_v12.contracts import ContractRefusal
from baton_v12.contracts.errors import name_value
from baton_v12.integration import oci_delivery, runtime
from baton_v12.worker_manager import boundaries, launch as launch_module
from baton_v12.worker_manager import source_boundary
from baton_v12.worker_manager.attempts import (activate_assignment,
                                               reconcile_runtime,
                                               record_attempt,
                                               request_runtime_start)
from baton_v12.worker_manager.offers import claimed_offers_for
from baton_v12.worker_manager.manifests import check_manifest_structure
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 compose_input_root)
from baton_v12.worker_manager.oci import ENGINES, OciAdapter

from . import integration_bundle

__all__ = ["INTEGRATION_STAGE_KIND", "IntegrationRuntimePort", "LAUNCH_ROLE"]


# THE ROLE THIS DEPLOYMENT LAUNCHES ITS INTEGRATOR UNDER, and the stage kind
# the scheduler names it by. They are deliberately DIFFERENT words and both are
# fixed here rather than configured: the workload refuses a container launched
# under any role but `integrator` -- it is the one role that integrates a
# canonical target -- while the scheduler's stage kind is `integration`. A
# deployment that could spell either differently is one whose container and
# whose scheduler disagree about what is running.
LAUNCH_ROLE = "integrator"
INTEGRATION_STAGE_KIND = "integration"

# WHAT `record_attempt` NEEDS BEYOND THE CERTIFIED IDENTITY.
IDENTITY_MEMBERS = ("image_digest", "profile_digest", "policy_digest",
                    "adapter_digest")


def _refuse(message, *, category="integrity", code="schema"):
    raise ContractRefusal(category, code, message)


def _denied(message):
    raise ContractRefusal("policy", "denied", message)


def _directory(place, what):
    """One absolute path this deployment already provisioned."""
    held = boundaries.text(place, what)
    if not os.path.isabs(held) or os.path.normpath(held) != held:
        _refuse(f"{what} is not one exact absolute path", code="path")
    if not os.path.isdir(held) or os.path.islink(held):
        _refuse(f"{what} is not a directory this deployment provisioned",
                category="refused", code="precondition")
    return held


class IntegrationRuntimePort:
    """The one runtime port `integrate_next` and `admit_accepted` accept.

    EVERY OPERAND IS RESOLVED BY THE DEPLOYMENT AND NONE IS INFERRED. There is
    no ambient identity here, no host path derived from the assignment's opaque
    target id, and no engine, image or group chosen from a profile word: a
    caller that has not resolved something cannot construct this, which is the
    difference between a composition and a lookup.
    """

    def __init__(self, *, coordinator, manager, jobs, authority,
                 assignment_port, profile, checkpoint_profile, object_runner,
                 line_id, proposal_id, canonical_target_id, canonical_target,
                 delivery_home, instructions,
                 identity, adapter_name, toolchain_digest, input_manifest,
                 engine, engine_run, workspace_storage, workspace_group,
                 capacity,
                 bundle_home, launch_home, launch_session, launch_contract,
                 network, credential_delivery=None, credential_home=None):
        for owner, name in ((coordinator, "the integration coordinator store"),
                            (manager, "the Worker Manager store"),
                            (jobs, "the Job store")):
            boundaries.capability(getattr(owner, "_connection", None), name)
        for verb in ("proposal", "policy_generation"):
            boundaries.capability(getattr(authority, verb, None),
                                  f"the Authority's {verb}")
        # THE ASSIGNMENT PORT'S OWN SURFACE, named as `activate_assignment`
        # uses it: the participant it acts for and the live assignment it
        # reads. A port that cannot answer both cannot bind an attempt to its
        # own claim, which is the whole of what preparation is for.
        boundaries.capability(getattr(assignment_port, "assignment_of", None),
                              "the assignment port's assignment_of")
        boundaries.text(getattr(assignment_port, "participant", None),
                        "the assignment port's participant")
        for method in ("freeze", "validate"):
            boundaries.capability(getattr(checkpoint_profile, method, None),
                                  f"the checkpoint profile's {method}")
        boundaries.capability(object_runner, "the read-only object runner") \
            if not hasattr(object_runner, "read") else None
        # THE PROFILE IS THE COORDINATOR'S OWN, taken through its owner so a
        # deployment cannot hand this a mapping that merely looks like one.
        self._profile = runtime.integration_profile(**{
            member: profile[member] for member in
            ("profile_kind", "profile_version", "integrator_participant",
             "instructions_digest")})
        boundaries.identity(line_id, "an accepted development line id")
        boundaries.identity(proposal_id, "an Authority proposal id")
        if type(instructions) is not bytes or not instructions:
            _refuse("the integrator's instruction bytes are a non-empty "
                    "byte string this deployment configured")
        if type(identity) is not dict \
                or sorted(identity) != sorted(IDENTITY_MEMBERS):
            _refuse(f"a runtime identity carries exactly {IDENTITY_MEMBERS}")
        for member in IDENTITY_MEMBERS:
            boundaries.text(identity[member], f"the runtime {member}")
        if engine not in ENGINES:
            _denied(f"engine {name_value(engine)} is not one this manager "
                    f"drives ({', '.join(sorted(ENGINES))})")
        boundaries.capability(engine_run, "the engine's run capability")
        # THE CONFIGURED WORKSPACE STORAGE, not a pair of paths. The two
        # assignment roots are ALLOCATED per attempt by their own owner, and
        # they carry the provenance `compose_source_boundary` requires: a
        # deployment that named two directories itself would be handing this
        # module roots nothing had proved were one assignment's.
        self._storage = _directory(workspace_storage,
                                   "the configured workspace storage")
        # THE CONFIGURED TARGET IS AN IDENTITY AND A DIRECTORY, BOTH GIVEN.
        # Review 2026-09-08T02:07:47Z [P1]: this held only the directory and
        # took the identity to bind it under from the assignment, so a valid
        # grant over target B rebound this deployment's directory for target A
        # and every lower check agreed -- because they compare against the
        # target this port had just constructed out of the assignment itself.
        # A boundary cannot detect a cross-wire it was told about.
        self._target_id = boundaries.identity(canonical_target_id,
                                              "the configured canonical "
                                              "target id")
        self._target_place = _directory(canonical_target,
                                        "the canonical target")
        # AND THE DELIVERY HOME IS CONFIGURATION TOO, so observation after a
        # restart does not depend on this process having started anything.
        self._delivery_home = _directory(delivery_home,
                                         "the integration delivery home")
        self._bundle_home = _directory(bundle_home, "the bundle home")
        self._launch_home = _directory(launch_home, "the launch home")
        self.coordinator, self.manager = coordinator, manager
        self.jobs, self.authority = jobs, authority
        self.assignment_port = assignment_port
        self.checkpoint_profile = checkpoint_profile
        self.object_runner = object_runner
        self.line_id, self.proposal_id = line_id, proposal_id
        self.instructions = instructions
        self.identity = dict(identity)
        self.adapter_name = boundaries.text(adapter_name, "the adapter name")
        # THE RETAINED INPUT MANIFEST this deployment claimed the attempt
        # against. The integrator reads its own assignment from the fixed
        # namespace, but the ordinary input root is still what the bundle's
        # read-only bind LANDS in -- `source_mountpoint` is a directory inside
        # it -- so the root is composed rather than skipped.
        if type(input_manifest) is not dict:
            _refuse("the retained input manifest is this deployment's own "
                    "published document")
        for member in ("manifest_digest", "assignment_contract",
                       "policy_digest", "runtime_profile_digest"):
            boundaries.text(input_manifest.get(member),
                            f"the input manifest's {member}")
        self._input_manifest = input_manifest
        self.toolchain_digest = boundaries.text(toolchain_digest,
                                                "the toolchain digest")
        self.engine, self.engine_run = engine, engine_run
        self.workspace_group = workspace_group
        self.capacity = capacity
        self.launch_session = boundaries.text(launch_session,
                                              "the launch session")
        self.launch_contract = boundaries.text(launch_contract,
                                               "the launch contract")
        # THE ENGINE NETWORK IS A DEPLOYMENT DECISION and the adapter requires
        # one; a port that defaulted it would be choosing an integrator's
        # network reachability on the deployment's behalf.
        self.network = boundaries.text(network, "the engine network")
        self.credential_delivery = credential_delivery
        self.credential_home = credential_home
        # THE LIVE MARKER, and it is deliberately in-memory only.
        self._live = {}

    # -- preparation, before admission asks for anything --------------------

    def prepare(self, stage, job):
        """Record and activate this integration stage's manager attempt.

        WHY IT CANNOT LIVE INSIDE `run`. `integrate_next` proves the attempt's
        runtime is `not-started` BEFORE it materializes a delivery or calls the
        port, and `prior_runtime_witness` refuses an attempt that was never
        recorded -- so an attempt prepared inside `run` would be prepared one
        call after the proof that needs it. `StageExecution.launch` sends
        integration straight to `Integration.run`, bypassing the ordinary
        worker path where this happens, which is why the assembly calls this
        explicitly and why it is the port that owns it: these are the same
        configured digests the runtime is started with.

        IT STARTS NOTHING. `record_attempt` and `activate_assignment` are the
        manager's own public owners; no runtime, credential, delivery or
        coordinator act is reached from here, and a replay of an identical
        preparation is the owners' own effectively-once answer.
        """
        attempt_id = boundaries.identity(stage.get("attempt_id"),
                                         "the integration stage's attempt id")
        if stage.get("kind") != INTEGRATION_STAGE_KIND:
            _refuse(f"stage {name_value(stage.get('stage_id'))} is "
                    f"{name_value(stage.get('kind'))} and this port prepares "
                    f"only {name_value(INTEGRATION_STAGE_KIND)} stages",
                    category="refused", code="precondition")
        # THE JOB IS COMPARED, NOT TRUSTED. A stage handed here with another
        # Job's identity would prepare this deployment's attempt against
        # somebody else's work.
        if job is not None and job.get("job_id") is not None \
                and stage.get("job_id") is not None \
                and job["job_id"] != stage["job_id"]:
            _refuse(f"stage {name_value(stage.get('stage_id'))} belongs to Job "
                    f"{name_value(stage.get('job_id'))} and was prepared with "
                    f"{name_value(job.get('job_id'))}",
                    category="refused", code="precondition")
        found = claimed_offers_for(self.manager, attempt_id)
        if len(found) != 1:
            _refuse(f"attempt {name_value(attempt_id)} has {len(found)} "
                    f"claimed offers; exactly one is what an activation binds",
                    category="refused", code="precondition")
        row = found[0]
        # NO ORDINARY INPUT MANIFEST, and that is the contract rather than an
        # omission. An ordinary worker reads its assignment from a composed
        # `/input` root carrying `input.json`; this integrator reads its
        # assignment from the fixed assignment namespace and its evidence from
        # the typed bundle bound at `/input/source`, and it never opens an
        # ordinary protocol document. Recording an input digest here would
        # oblige every start to expose a root nothing in this image reads --
        # `request_runtime_start` derives that requirement from the attempt
        # itself, which is exactly why it is decided here and once.
        record_attempt(self.manager, attempt_id=attempt_id,
                       adapter_name=self.adapter_name,
                       adapter_digest=self.identity["adapter_digest"],
                       profile_digest=self.identity["profile_digest"],
                       input_digest=self._input_manifest["manifest_digest"],
                       policy_digest=self.identity["policy_digest"],
                       image_digest=self.identity["image_digest"],
                       toolchain_digest=self.toolchain_digest)
        expect = {"work_ref": {"authority_uuid": row["authority_uuid"],
                               "work_id": row["work_id"]},
                  "participant": row["participant"],
                  "generation": row["claim_generation"]}
        activate_assignment(self.manager, self.assignment_port,
                            attempt_id=attempt_id, expect=expect)
        # THE INPUT ROOT IS COMPOSED AFTER THE CLAIM COMMITS, which is the
        # order §7.0 fixes: `input.json` is the pre-claim evidence and
        # `assignment.json` carries the live identity the claim just bound.
        # The bundle's own bind lands on `source_mountpoint` inside it.
        roots = assignment_workspace(self.workspace_group, self._storage,
                                     attempt_id)
        # THE MOUNTPOINT FIRST, THEN THE IMMUTABLE COMPOSITION, which is the
        # order a deployment must use: `compose_input_root` seals the root,
        # and a frozen input root cannot grow the directory the bundle's bind
        # has to land on afterwards.
        source_boundary.source_mountpoint(roots["inputs"])
        if not os.path.exists(os.path.join(roots["inputs"], "input.json")):
            compose_input_root(
                roots["inputs"], self._input_manifest,
                self._assignment_manifest(row, attempt_id),
                assignment=dict(expect), runtime_attempt_id=attempt_id)
        return {"attempt_id": attempt_id, "assignment": expect,
                "inputs": roots["inputs"]}

    def _assignment_manifest(self, row, attempt_id):
        """The attempt's own assignment manifest, minted from its claim.

        Composed exactly as the ordinary single-worker deployment composes
        one -- the claim's own facts, this deployment's retained input
        manifest, and nothing a caller supplies.
        """
        from baton_v12.contracts import digest

        given = self._input_manifest
        claim = {"assignment": {"work_ref": {
                     "authority_uuid": row["authority_uuid"],
                     "work_id": row["work_id"]},
                     "participant": row["participant"],
                     "generation": row["claim_generation"]},
                 "claim_event": row["claim_event_seq"],
                 "decision": {"endpoint": row["participant"],
                              "principal": row["claim_principal"],
                              "effective_scope": row["claim_scope"],
                              "role": row["claim_role"],
                              "grant": row["claim_grant"],
                              "policy_generation":
                                  row["claim_policy_generation"]}}
        document = {
            "version": {"major": 1, "minor": 0},
            "manifest_id": "assignment-" + digest(attempt_id)[7:31],
            "created_at": row["accepted_at"], "extensions": {},
            "schema": "baton.worker-manifest/assignment",
            "assignment_ref": dict(claim["assignment"]),
            "assignment_contract": given["assignment_contract"],
            "offer_id": row["offer_id"], "runtime_attempt_id": attempt_id,
            "input_manifest_digest": given["manifest_digest"],
            "policy_digest": given["policy_digest"],
            "runtime_profile_digest": given["runtime_profile_digest"],
            "claim_receipt_digest": digest(claim),
            "claim_event_seq": row["claim_event_seq"],
            "activated_at": row["decided_at"]}
        document["manifest_digest"] = digest(document)
        return check_manifest_structure(
            document, "assignmentManifest",
            what="the integrator's assignment manifest")

    # -- the accepted port seam --------------------------------------------

    def run(self, delivery, assignment):
        """Start the assigned integrator over its accepted delivery.

        THE ORDER IS THE CONTRACT, and every step is an accepted owner's:

          1. the assignment's own participant and instructions are compared
             with the configured profile, before anything is composed;
          2. the launch document is authored and materialized -- one document,
             composed once from the same three operands the bundle carries, so
             the container and the evidence cannot disagree about what it is;
          3. `compose_bundle` publishes the immutable evidence bundle from the
             accepted checkpoint, receipts and retained objects, and answers
             the manager's own NOMINATION of the directory to bind;
          4. `compose_mount_boundary` mints the fenced three-mount plan, which
             re-adopts the delivery, compares the published and freshly
             composed assignments and proves the target's posture;
          5. the source boundary binds the bundle read-only at `/input/source`;
          6. `request_runtime_start` journals the signed start and then asks
             the adapter, whose own final proof re-reads the grant, the
             published assignment and every bound directory.

        IT RETURNS WHEN THE MODEL HAS BEEN ASKED, which is what the port
        contract says and what `integrate_next` expects: the answer is on disk
        later, and `settle_observed` and `continue_accepted` are what read it.
        """
        attempt_id = boundaries.identity(assignment.get("attempt_id"),
                                         "the assignment's attempt id")
        if assignment.get("integrator_participant") \
                != self._profile["integrator_participant"]:
            _denied(f"this assignment is for integrator "
                    f"{name_value(assignment.get('integrator_participant'))} "
                    f"and this port is configured for "
                    f"{name_value(self._profile['integrator_participant'])}")
        if assignment.get("instructions_digest") \
                != self._profile["instructions_digest"]:
            _denied(f"this assignment names instructions "
                    f"{name_value(assignment.get('instructions_digest'))} and "
                    f"this port carries "
                    f"{name_value(self._profile['instructions_digest'])}")
        if assignment.get("canonical_target_id") != self._target_id:
            # THE LEASE IS OVER ONE TARGET AND THIS PORT SERVES ONE TARGET.
            # A grant for another identity is refused HERE, before a bundle,
            # a mount plan or a launch document exists -- the directory this
            # deployment would expose is not the one that grant authorizes.
            _denied(f"this assignment integrates target "
                    f"{name_value(assignment.get('canonical_target_id'))} and "
                    f"this port is configured for "
                    f"{name_value(self._target_id)}; a lease over one target "
                    f"never authorizes exposure of another's directory")
        if assignment.get("target_access") != "writable":
            _denied(f"an integration runtime is started only over a writable "
                    f"target access; this assignment carries "
                    f"{name_value(assignment.get('target_access'))}")

        launched = launch_module.materialize(
            self._launch_home, attempt_id=attempt_id,
            session=self.launch_session, contract=self.launch_contract,
            role=LAUNCH_ROLE)
        document = launch_module.launch_document(
            session=self.launch_session, contract=self.launch_contract,
            role=LAUNCH_ROLE)
        published = integration_bundle.compose_bundle(
            os.path.join(self._bundle_home, attempt_id),
            manager=self.manager, jobs=self.jobs, authority=self.authority,
            checkpoint_profile=self.checkpoint_profile,
            integration_profile=self._profile, assignment=assignment,
            launch=document, instructions=self.instructions,
            line_id=self.line_id, proposal_id=self.proposal_id,
            runner=self.object_runner)
        target = self._configured_target()
        boundary = oci_delivery.compose_mount_boundary(
            self.coordinator, self.manager, profile=self._profile,
            delivery=delivery, assignment=assignment, target=target,
            workspace_group=self.workspace_group)
        roots = assignment_workspace(self.workspace_group, self._storage,
                                     attempt_id)
        source = source_boundary.compose_source_boundary(
            published["source"], roots, self.capacity)
        adapter = OciAdapter(
            self.engine, self.engine_run,
            identity=dict(self.identity),
            assignment_roots=roots, posture="execution",
            # THE AUTHORIZED INPUT ROOT READ-ONLY AT `/input`, which is what
            # the bundle's own bind under `/input/source` lands inside, and
            # the one writable workspace at `/output`.
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}],
            source_delivery=source, launch_delivery=launched,
            credential_delivery=self.credential_delivery,
            credential_home=self.credential_home,
            workspace_group=self.workspace_group, network=self.network,
            integration_delivery=boundary)
        self._live.pop(attempt_id, None)
        answer = request_runtime_start(self.manager, adapter,
                                       attempt_id=attempt_id,
                                       inputs=roots["inputs"])
        # THE MARKER IS TAKEN HERE AND NOWHERE ELSE, and only for a start the
        # MANAGER'S OWN AXIS says happened. Review 2026-09-08T02:07:47Z [P1]:
        # a marker minted on the strength of returning from this call would
        # claim continuation permission for a start whose runtime nobody
        # established -- which is the one state that must never be continued
        # normally. The witness is public and durable; the answer document is
        # this call's own account of one act.
        if self._accountable(attempt_id):
            self._live[attempt_id] = {
                "assignment": dict(assignment),
                "delivery_root": os.path.dirname(delivery.root),
                "bundle_digest": published["bundle_digest"]}
        return answer

    def _accountable(self, attempt_id):
        """Whether the manager can account for this attempt's runtime.

        `uncertain` is the state the manager's own table refuses to let become
        `destroyed` because nobody looked successfully, and `not-started` says
        no runtime exists at all; neither is a start this execution may go on
        to continue normally.
        """
        observed = runtime.prior_runtime_witness(self.manager, attempt_id)
        return observed["execution_runtime"] not in ("uncertain",
                                                     "not-started")

    # -- observation, which starts nothing ---------------------------------

    def refresh(self, attempt_id):
        """Reconcile this attempt's runtime through the accepted owner.

        NO START, NO CREDENTIAL, NO GUESSED QUIESCENCE. `reconcile_runtime`
        decides by identity and by the full labels, and this composes the
        adapter it decides through -- over an ADOPTED mount plan, because a
        composition would mint a fresh binding for an attempt that already has
        one and would need a live grant this observation must not require.
        """
        held = boundaries.identity(attempt_id, "an integrator attempt id")
        adapter = self._observing_adapter(held)
        try:
            answer = reconcile_runtime(self.manager, adapter, attempt_id=held)
        except Exception:
            # A RECONCILIATION THAT DID NOT COMPLETE ESTABLISHED NOTHING, so
            # this execution's permission to continue normally goes with it.
            self._live.pop(held, None)
            raise
        # THE ANSWER IS READ IN ITS OWN VOCABULARY. Review
        # 2026-09-08T02:07:47Z [P1]: this tested `execution_runtime`, which no
        # public reconciliation document carries -- so BOTH uncertainty shapes
        # left the marker standing through the exact event meant to revoke it.
        # `_reconciled` answers `decision="uncertain"` when nothing could be
        # established, and an inconclusive attached observation answers
        # `decision="attached"` with `observed="uncertain"`.
        if answer.get("decision") == "uncertain" \
                or answer.get("observed") == "uncertain" \
                or not self._accountable(held):
            # AND THE DURABLE WITNESS IS ASKED TOO, because it is the state
            # every later owner will decide on and it does not depend on this
            # module reading somebody else's document correctly.
            self._live.pop(held, None)
        return answer

    def observed(self, attempt_id, assignment):
        """Read-only status: what the delivery says and what the runtime is.

        IT PERFORMS NONE OF THE THREE ACTS. No activation, no reconciliation
        write, no settlement, and no ordinary-worker exchange terminal is
        fabricated for a workload that publishes its own typed result.
        """
        held = boundaries.identity(attempt_id, "an integrator attempt id")
        delivery = runtime.adopt_delivery(
            self._delivery_home, attempt_id=held,
            workspace_group=self.workspace_group)
        witness = runtime.prior_runtime_witness(self.manager, held)
        seen = (None if delivery is None
                else runtime.observed_delivery(delivery, assignment))
        return {"attempt_id": held, "execution_runtime":
                witness["execution_runtime"],
                "delivery": None if delivery is None else {
                    "assignment_root": delivery.assignment_root,
                    "result_root": delivery.result_root},
                "observed": seen,
                "continuable": self.may_continue(assignment, delivery)}

    def may_continue(self, assignment, delivery=None):
        """Whether THIS execution started exactly this assignment's runtime.

        LOCAL BOOKKEEPING, AND THE WHOLE OF IT. It is true only for an
        assignment this process started, compared whole, over the same
        delivery root; it is false after a restart because the marker is in
        memory; and it is false once `refresh` has seen an uncertain runtime.
        A true answer authorizes a caller to select the NORMAL continuation
        operation, which then re-proves the grant, the assignment and the
        runtime for itself -- so this is never a substitute for any of them.
        """
        held = self._live.get(assignment.get("attempt_id"))
        if held is None or held["assignment"] != dict(assignment):
            return False
        if delivery is not None \
                and os.path.dirname(delivery.root) != held["delivery_root"]:
            return False
        return True

    def forget(self, attempt_id):
        """Drop this execution's marker without touching durable state."""
        self._live.pop(attempt_id, None)

    # -- composition helpers ------------------------------------------------

    def _configured_target(self):
        """This port's ONE target, from configuration and nothing else.

        The identity is the configured one and the directory is the configured
        one; what is read afresh each time is the directory's own identity, so
        a place re-pointed since construction refuses at the boundary instead
        of being bound because it was proved once.
        """
        return oci_delivery.integration_target(
            self._target_id,
            source_boundary.nominate_source(self._target_place))

    def _observing_adapter(self, attempt_id):
        """One adapter over the ADOPTED plan, for observation only.

        Review 2026-09-08T02:07:47Z [P1]: this resolved the delivery root and
        the target identity out of the live MARKER, so a port that had
        correctly lost its marker -- a restart, or an uncertain runtime -- also
        lost the ability to look at the runtime it most needed to look at.
        Observation is configured, continuation is earned, and they are not the
        same permission.
        """
        delivery = runtime.adopt_delivery(
            self._delivery_home, attempt_id=attempt_id,
            workspace_group=self.workspace_group)
        if delivery is None:
            _refuse(f"attempt {name_value(attempt_id)} has no integration "
                    f"delivery to observe", category="refused",
                    code="precondition")
        recovered = oci_delivery.adopt_mount_boundary(
            self.manager, delivery=delivery, target=self._configured_target(),
            workspace_group=self.workspace_group)
        return OciAdapter(
            self.engine, self.engine_run, identity=dict(self.identity),
            assignment_roots=assignment_workspace(
                self.workspace_group, self._storage, attempt_id),
            posture="execution",
            workspace_group=self.workspace_group, network=self.network,
            integration_delivery=recovered)
