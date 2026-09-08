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
from baton_v12.worker_manager.oci import ENGINES, OciAdapter

from . import integration_bundle

__all__ = ["INTEGRATION_STAGE_KIND", "IntegrationRuntimePort", "LAUNCH_ROLE"]


# THE ROLE THIS DEPLOYMENT LAUNCHES ITS INTEGRATOR UNDER, and the stage kind
# the scheduler names it by. Both are fixed here rather than configured: the
# image's own entry is composed for exactly one role, and a deployment that
# could spell them differently is a deployment whose container and whose
# scheduler disagree about what is running.
LAUNCH_ROLE = "integration"
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
                 line_id, proposal_id, canonical_target, instructions,
                 identity, adapter_name, input_digest, toolchain_digest,
                 engine, engine_run, roots, workspace_group, capacity,
                 bundle_home, launch_home, launch_session, launch_contract,
                 network=None, credential_delivery=None,
                 credential_home=None):
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
        if type(roots) is not dict or sorted(roots) != ["inputs", "workspace"]:
            _refuse("the assignment roots are this deployment's own `inputs` "
                    "and `workspace` directories")
        self._roots = {name: _directory(place, f"the {name} assignment root")
                       for name, place in sorted(roots.items())}
        self._target_place = _directory(canonical_target,
                                        "the canonical target")
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
        self.input_digest = boundaries.text(input_digest,
                                            "the input manifest digest")
        self.toolchain_digest = boundaries.text(toolchain_digest,
                                                "the toolchain digest")
        self.engine, self.engine_run = engine, engine_run
        self.workspace_group = workspace_group
        self.capacity = capacity
        self.launch_session = boundaries.text(launch_session,
                                              "the launch session")
        self.launch_contract = boundaries.text(launch_contract,
                                               "the launch contract")
        self.network = network
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
        record_attempt(self.manager, attempt_id=attempt_id,
                       adapter_name=self.adapter_name,
                       adapter_digest=self.identity["adapter_digest"],
                       profile_digest=self.identity["profile_digest"],
                       input_digest=self.input_digest,
                       policy_digest=self.identity["policy_digest"],
                       image_digest=self.identity["image_digest"],
                       toolchain_digest=self.toolchain_digest)
        expect = {"work_ref": {"authority_uuid": row["authority_uuid"],
                               "work_id": row["work_id"]},
                  "participant": row["participant"],
                  "generation": row["claim_generation"]}
        activate_assignment(self.manager, self.assignment_port,
                            attempt_id=attempt_id, expect=expect)
        return {"attempt_id": attempt_id, "assignment": expect}

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
        target = oci_delivery.integration_target(
            assignment["canonical_target_id"],
            source_boundary.nominate_source(self._target_place))
        boundary = oci_delivery.compose_mount_boundary(
            self.coordinator, self.manager, profile=self._profile,
            delivery=delivery, assignment=assignment, target=target,
            workspace_group=self.workspace_group)
        source = source_boundary.compose_source_boundary(
            published["source"], self._roots, self.capacity)
        adapter = OciAdapter(
            self.engine, self.engine_run,
            identity=dict(self.identity),
            assignment_roots=dict(self._roots), posture="execution",
            source_delivery=source, launch_delivery=launched,
            credential_delivery=self.credential_delivery,
            credential_home=self.credential_home,
            workspace_group=self.workspace_group, network=self.network,
            integration_delivery=boundary)
        answer = request_runtime_start(self.manager, adapter,
                                       attempt_id=attempt_id,
                                       inputs=self._roots["inputs"])
        # THE MARKER IS TAKEN HERE AND NOWHERE ELSE: after a start this
        # process journalled and the adapter completed, bound to the WHOLE
        # assignment and to the delivery it was started over.
        self._live[attempt_id] = {
            "assignment": dict(assignment),
            "delivery_root": os.path.dirname(delivery.root),
            "bundle_digest": published["bundle_digest"]}
        return answer

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
        answer = reconcile_runtime(self.manager, adapter, attempt_id=held)
        if answer.get("execution_runtime") == "uncertain":
            # A RUNTIME NOBODY CAN ACCOUNT FOR ENDS THIS EXECUTION'S CLAIM to
            # be continuing anything normally. The durable state is unchanged;
            # what is dropped is this process's own permission to treat the
            # next tick as ordinary.
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
            self._delivery_root(held), attempt_id=held,
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

    def _delivery_root(self, attempt_id):
        held = self._live.get(attempt_id)
        if held is not None:
            return held["delivery_root"]
        _refuse(f"this execution holds no delivery root for attempt "
                f"{name_value(attempt_id)}; a status read names the launch "
                f"root its own deployment materialized",
                category="refused", code="precondition")

    def _observing_adapter(self, attempt_id):
        """One adapter over the ADOPTED plan, for observation only."""
        delivery = runtime.adopt_delivery(
            self._delivery_root(attempt_id), attempt_id=attempt_id,
            workspace_group=self.workspace_group)
        if delivery is None:
            _refuse(f"attempt {name_value(attempt_id)} has no integration "
                    f"delivery to observe", category="refused",
                    code="precondition")
        target = oci_delivery.integration_target(
            self._live[attempt_id]["assignment"]["canonical_target_id"],
            source_boundary.nominate_source(self._target_place))
        recovered = oci_delivery.adopt_mount_boundary(
            self.manager, delivery=delivery, target=target,
            workspace_group=self.workspace_group)
        return OciAdapter(
            self.engine, self.engine_run, identity=dict(self.identity),
            assignment_roots=dict(self._roots), posture="execution",
            workspace_group=self.workspace_group, network=self.network,
            integration_delivery=recovered)
