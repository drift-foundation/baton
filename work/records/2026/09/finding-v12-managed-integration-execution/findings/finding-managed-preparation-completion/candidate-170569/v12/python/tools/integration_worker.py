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
import json

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

__all__ = ["INTEGRATION_STAGE_KIND", "IntegrationRuntimePort", "LAUNCH_ROLE",
           "PreparationExecution", "PreparationAdmission",
           "ManagedPreparation", "ChildAcceptance",
           "CAUSAL_COMMANDS",
           "preparation_identities", "preparation_operands",
           "preparation_child_work",
           "authority_port", "manager_session"]


# THE ROLE THIS DEPLOYMENT LAUNCHES ITS INTEGRATOR UNDER, and the stage kind
# the scheduler names it by. They are deliberately DIFFERENT words and both are
# fixed here rather than configured: the workload refuses a container launched
# under any role but `integrator` -- it is the one role that integrates a
# canonical target -- while the scheduler's stage kind is `integration`. A
# deployment that could spell either differently is one whose container and
# whose scheduler disagree about what is running.
LAUNCH_ROLE = "integrator"
INTEGRATION_STAGE_KIND = "integration"

# THE SLOT THE SELECTED WORKLOAD ASKS FOR, and it is the image's request rather
# than this module's choice: `claude_agent.CREDENTIAL_SLOT` is `claude`, linked
# from the provider's own credential path to `/run/baton/credentials/claude`.
# The port cannot import that module -- it is the container's, not the
# manager's -- so the name is stated here and a resolution that does not carry
# it is refused before anything is composed. Review 2026-09-08T02:29:59Z [P1]:
# an unavailable credential reached a real engine start, because this operand
# defaulted to `None` and was passed through untouched.
REQUIRED_CREDENTIAL_SLOT = "claude"

# THE ONE RUNTIME STATE THAT MEANS NO START WAS EVER REQUESTED, spelled here
# rather than imported from `execution`, whose own constant is about which
# state a PORT may be asked in.
UNSTARTED = "not-started"

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
                 network, credential_resolution, credential_home,
                 credential_provider, execution_context=None):
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
        # THE CREDENTIAL CONFIGURATION IS REQUIRED, NOT OPTIONAL. The selected
        # entry runs a provider that reads a bearer from its slot, so a
        # deployment that has not resolved one has not configured this port --
        # and finding that out at the engine is finding it out too late.
        for one in ("materialize",):
            boundaries.capability(getattr(credential_home, one, None),
                                  f"the credential home's {one}")
        boundaries.capability(credential_provider,
                              "the configured credential provider")
        if type(credential_resolution) not in (tuple, list) \
                or not credential_resolution:
            _refuse("the credential resolution is this deployment's own "
                    "resolved delivery for the slots it authorizes")
        held = [one.get("slot") if type(one) is dict else None
                for one in credential_resolution]
        if REQUIRED_CREDENTIAL_SLOT not in held:
            _denied(f"the selected integrator reads its bearer from slot "
                    f"{name_value(REQUIRED_CREDENTIAL_SLOT)} and this "
                    f"deployment's credential resolution carries "
                    f"{name_value(sorted(one for one in held if one))}")
        self.credential_resolution = tuple(credential_resolution)
        self.credential_home = credential_home
        self.credential_provider = credential_provider
        # THE LIVE MARKER, and it is deliberately in-memory only.
        self._live = {}
        # AND THE PREPARED CREDENTIAL DELIVERIES, one per attempt this
        # execution prepared. In memory for the same reason: a delivery a
        # later incarnation did not mint is an orphan its own preparation
        # discards, not a capability it inherits.
        self._credentials = {}
        # W156162: THE NARROW READER THIS PORT COMPOSES ITS LAUNCH THROUGH, and
        # the Job binding each prepared attempt carries. The reader is the same
        # one-question closure the single-worker factory injects -- it answers a
        # Job's execution context and nothing else -- and it is OPTIONAL because
        # a deployment with no Job owner composes exactly the `/1` document it
        # always did. What it may not do is be configured and then quietly
        # produce a `/1`: an integrator whose Job configured a ceiling and whose
        # container was told nothing would run under a default nobody chose.
        if execution_context is not None:
            boundaries.capability(execution_context,
                                  "the Job execution context reader")
        self._execution_context = execution_context
        self._jobs_bound = {}

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
        # AND THE CREDENTIAL IS MINTED HERE, BEFORE ADMISSION TAKES A LEASE.
        # Review 2026-09-08T02:53:32Z [P1]: materializing it inside `run` put
        # the one FALLIBLE EXTERNAL dependency in this whole composition --
        # somebody else's secret source -- after the coordinator had already
        # granted a lease and published a delivery. A provider that refused
        # there left the entry leased with the runtime `not-started`.
        #
        # WHAT THIS ORDERING DOES AND DOES NOT ESTABLISH, precisely. It means a
        # failed preparation creates NO PREDECESSOR at all: no lease, no
        # delivery, no requested start. It does NOT mean a `not-started`
        # attempt satisfies some already-leased predecessor's quiescence gate
        # -- that gate is about a runtime that WAS started, and nothing here
        # answers it.
        self._credentials[attempt_id] = self._materialized(attempt_id)
        # AND THE JOB THIS ATTEMPT SERVES, retained beside the credential and
        # for the same reason: `run` is handed a delivery and an assignment,
        # neither of which names a Job, and the stage that does is here. Only
        # the IDENTITY is kept -- the configuration itself is re-resolved
        # through the Job's own owner at the launch, so a document is never
        # composed from a remembered answer.
        if stage.get("job_id") is not None:
            self._jobs_bound[attempt_id] = stage["job_id"]
        return {"attempt_id": attempt_id, "assignment": expect,
                "inputs": roots["inputs"]}

    def _materialized(self, attempt_id):
        """This attempt's private credential delivery, through its owner.

        THE ELIGIBILITY IS PROVED, NOT ASSUMED. Review 2026-09-08T02:29:59Z
        [P1]: this discarded whatever credential record or root it found and
        minted a new bearer, on the strength of a COMMENT saying the attempt
        was not started -- and nothing checked. `record_attempt` and
        `activate_assignment` replay their own acts and establish no runtime
        precondition, so repeating `prepare` against a RUNNING attempt asked
        the provider again and destroyed the custody its live runtime holds.
        `discard_orphan` requires its caller to prove the root stale, and a
        process's lack of an in-memory delivery is not that proof.

        So there are exactly three answers, and the manager's own axis decides
        which:

          an identical in-process replay REUSES the exact capability it
          already prepared, whatever the runtime is doing -- reminting for a
          delivery this execution still holds is neither a replay nor safe;

          an attempt whose runtime this execution did not prepare and whose
          axis is anything but `not-started` is REFUSED, with nothing
          discarded: its credential custody belongs to that runtime;

          and only a `not-started` attempt with no delivery here may discard a
          previous incarnation's orphan -- which the axis is what proves stale
          -- and mint a new one.
        """
        held = self._credentials.get(attempt_id)
        if held is not None:
            return held
        observed = runtime.prior_runtime_witness(
            self.manager, attempt_id)["execution_runtime"]
        if observed != UNSTARTED:
            _refuse(f"attempt {name_value(attempt_id)}'s runtime is "
                    f"{name_value(observed)} and this execution prepared no "
                    f"credential for it; preparation mints a bearer only for "
                    f"an attempt whose runtime has not started, and the "
                    f"custody of a runtime this process did not start is not "
                    f"this process's to discard",
                    category="refused", code="precondition")
        if self.credential_home.read_state(attempt_id) is not None \
                or os.path.lexists(
                    self.credential_home.volatile_root(attempt_id)):
            # PROVED STALE BY THE AXIS ABOVE: `not-started` says no runtime
            # ever received this delivery, so it belongs to an incarnation
            # that is gone.
            self.credential_home.discard_orphan(attempt_id)
        return self.credential_home.materialize(
            self.credential_resolution, attempt_id=attempt_id,
            workspace_group=self.workspace_group,
            credential_provider=self.credential_provider)

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

        execution = self._job_execution(attempt_id)
        launched = launch_module.materialize(
            self._launch_home, attempt_id=attempt_id,
            session=self.launch_session, contract=self.launch_contract,
            role=LAUNCH_ROLE, job_execution=execution)
        document = launch_module.launch_document(
            session=self.launch_session, contract=self.launch_contract,
            role=LAUNCH_ROLE, job_execution=execution)
        published = integration_bundle.compose_bundle(
            os.path.join(self._bundle_home, attempt_id),
            manager=self.manager, jobs=self.jobs, authority=self.authority,
            checkpoint_profile=self.checkpoint_profile,
            integration_profile=self._profile, assignment=assignment,
            launch=document, instructions=self.instructions,
            line_id=self.line_id, proposal_id=self.proposal_id,
            runner=self.object_runner)
        # W156162 [P1], review 2026-09-13T03:27:43Z. THE CARRIER'S JOB IS THE
        # ACCEPTED PROPOSAL'S OWNER, OR THIS START DOES NOT HAPPEN. `prepare`
        # takes the Job identity from the stage its CALLER handed it; the bundle
        # resolves the owning Job from the account admission actually accepted,
        # through the Job store's own rows. Those are two different questions
        # and nothing compared them, so a launch could state one Job's ceilings
        # over another Job's proposal, evidence and test scope -- with the
        # launch digest sealed into the bundle, which proves byte identity and
        # says nothing about ownership.
        #
        # COMPARED HERE, BEFORE ANY RUNTIME EXISTS. The bundle is published and
        # the mount plan, the source boundary and the start are all still ahead.
        if execution is not None:
            owner = published.get("job_id")
            if not owner:
                _refuse("this bundle names no accepted owning Job and this "
                        "deployment resolves a Job's configured ceilings; "
                        "there is nothing here to compare a carrier against",
                        category="refused", code="precondition")
            if owner != execution["job_id"]:
                _refuse(f"this attempt's launch carries Job "
                        f"{name_value(execution['job_id'])} and the accepted "
                        f"proposal this bundle was composed from belongs to "
                        f"{name_value(owner)}; a launch sealed into a bundle "
                        f"proves the bytes travelled together, not that its "
                        f"Job owns the work",
                        category="refused", code="precondition")
        target = self._configured_target()
        boundary = oci_delivery.compose_mount_boundary(
            self.coordinator, self.manager, profile=self._profile,
            delivery=delivery, assignment=assignment, target=target,
            workspace_group=self.workspace_group)
        roots = assignment_workspace(self.workspace_group, self._storage,
                                     attempt_id)
        # THE ATTEMPT-PRIVATE CREDENTIAL DELIVERY THIS EXECUTION PREPARED.
        # It is not minted here: by the time a port is asked to run, a lease is
        # held and a delivery is published, and that is not where a deployment
        # may discover that its secret source is unavailable.
        credential = self._credentials.get(attempt_id)
        if credential is None:
            _refuse(f"attempt {name_value(attempt_id)} has no credential "
                    f"delivery from this execution's own preparation; the "
                    f"bearer is minted before admission takes a lease and a "
                    f"start is never the place to find out it cannot be",
                    category="refused", code="precondition")
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
            credential_delivery=credential, credential_home=self.credential_home,
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

    def _job_execution(self, attempt_id):
        """This attempt's Job execution context, or `None` for no Job owner.

        W156162, and the half the reader-level proof did not reach. The
        container reads its ceilings out of the launch document, and until this
        composed one the direct integration path authored a `/1` -- so an
        integration verification could only ever run under the image default no
        matter what its Job configured.

        RE-RESOLVED, NOT REMEMBERED. `prepare` retains the Job IDENTITY; the
        settings and the generation they are read under come from the Job's own
        owner at this call, which is what keeps one account of a Job's
        configuration rather than a second one aging in this process.

        A CONFIGURED READER AND AN UNBOUND ATTEMPT IS A REFUSAL. This port is
        composed with the reader exactly when the deployment has a Job owner,
        and an attempt that reached a start without the preparation that binds
        it has skipped the call `run` already requires for its credential;
        answering `None` here would hand it the defaults under the name of a
        Job that configured something else.
        """
        if self._execution_context is None:
            return None
        job_id = self._jobs_bound.get(attempt_id)
        if job_id is None:
            _refuse(f"attempt {name_value(attempt_id)} names no Job from this "
                    f"execution's own preparation and this port resolves a "
                    f"Job's configured ceilings; a launch composed now would "
                    f"state defaults this deployment never chose",
                    category="refused", code="precondition")
        return self._execution_context(
            job_id=job_id, attempt_id=attempt_id,
            runtime_input_digest=self._input_manifest["manifest_digest"],
            runtime_policy_digest=self.identity["policy_digest"])

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
        try:
            # A NEVER-STARTED ATTEMPT IS NOT RECONCILED, and this check is
            # INSIDE the boundary. Review 2026-09-08T02:29:59Z [P1]: it was
            # added in front of the try, so a witness read that raised left the
            # marker standing -- the very leak the boundary exists to close.
            # Reconciliation asked about an attempt no start was ever
            # requested for answers that it can name no runtime and records
            # `uncertain`; the axis already says `not-started`, and replacing
            # an accountable state with an unaccountable one is a write this
            # observation has no reason to make. No `reconcile_runtime` call
            # is reached on this path.
            if runtime.prior_runtime_witness(
                    self.manager, held)["execution_runtime"] == UNSTARTED:
                _refuse(f"attempt {name_value(held)} has no requested runtime "
                        f"to reconcile; its accepted axis already says "
                        f"{name_value(UNSTARTED)} and reconciling would "
                        f"replace that with an unaccountable one",
                        category="refused", code="precondition")
            # THE WHOLE OBSERVATION IS INSIDE THE BOUNDARY. Review
            # 2026-09-08T02:29:59Z [P1]: the adapter was CONSTRUCTED before the
            # try, so adopting the delivery, nominating the target or composing
            # the plan could fail -- moving the nominated directory does it --
            # and the marker survived the failure. Anything that stops this
            # observation from completing leaves this execution unable to say
            # the runtime is still accountable, which is the whole condition.
            adapter = self._observing_adapter(held)
            answer = reconcile_runtime(self.manager, adapter, attempt_id=held)
            # AND THE SECOND WITNESS READ IS INSIDE IT TOO, because a
            # reconciliation whose durable effect cannot then be read
            # establishes no more than one that never ran.
            accountable = self._accountable(held)
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
                or not accountable:
            # THE DURABLE WITNESS IS ASKED TOO, because it is the state every
            # later owner will decide on and it does not depend on this module
            # reading somebody else's document correctly.
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


# ---------------------------------------------------------------------------
# W161230 slice2, CHECKPOINT A.3: the preparation's own child Work.
#
# THIS IS ORDINARY WORKER COORDINATION AND NOTHING NEW. Every step below is an
# existing owned operation -- `record_preparation_intent`, `Authority.create_work`,
# `issue_offer`, `submit_claim`, `assignment_of`, `admit_integration_execution`.
# What this class contributes is the ORDER, and the refusals that hold it.

from baton_v12.job_manager.integration_capacity import (       # noqa: E402
    admit_integration_execution, integration_capacity_of,
    preparation_intent_of, record_preparation_intent)
from baton_v12.worker_manager.attempts import (                 # noqa: E402
    activate_assignment, assignment_of)
from baton_v12.worker_manager.offers import (                  # noqa: E402
    claimed_offers_for, issue_offer, submit_claim)

PREPARATION_PHASE = "prepare"


def _admissible(assignment):
    """The Worker Manager\'s fixed assignment, in the shape ADMISSION reads.

    REVIEW claim168292 corrected my diagnosis, and the correction matters:
    activation SUCCEEDS. What refused was capacity admission, because
    `assignment_of` answers a FLAT row -- `authority_uuid`, `work_id`,
    `participant`, `generation` -- while `admit_integration_execution` reads a
    nested `work_ref`. Two owned readers describing one assignment in two
    shapes is an ordinary impedance mismatch, not a missing capability, and
    `CapacityCase.claim_of` already maps it exactly this way.

    IT IS A LOSSLESS RENAME AND NOTHING ELSE. Every value comes from the
    manager\'s own answer; nothing here defaults, derives or fills in a member
    the manager did not fix. That is the whole reason this is safe to do in
    the composition: it is not deciding anything.
    """
    return {"work_ref": {"authority_uuid": assignment["authority_uuid"],
                         "work_id": assignment["work_id"]},
            "participant": assignment["participant"],
            "generation": assignment["generation"]}


# W161230 A.4: THE CAUSAL SEQUENCE A PREPARATION IS ASKED FOR, in its order.
# Stated here rather than imported from `stage_execution._CausalObserver`: that
# owner RUNS the sequence on the coordinator host and this composition exists to
# move it to the worker, so importing its order would tie the request to the
# module the managed branch must not reach. The two are held equal by the
# worker's own conformance cases rather than by this comment.
CAUSAL_COMMANDS = ("combined", "base", "isolated")


def preparation_identities(orchestration_id):
    """The child's attempt, Work and offer identities, DERIVED from the one
    orchestration rather than minted.

    A RESTART MUST REACH THE SAME THREE. `record_preparation_intent` already
    derives the Work operation id so an interrupted creation resumes; identities
    minted fresh on a second sweep would make that protection pointless by
    naming a different child each time. So they are a pure function of the
    orchestration, and two sweeps of one orchestration ask for one child.
    """
    boundaries.identity(orchestration_id, "an orchestration id")
    from baton_v12.contracts import digest

    identity = "prepare-" + digest(orchestration_id)[7:]
    return {"execution_attempt_id": identity,
            "execution_offer_id": identity + "-offer"}


def _accepted_paths(accepted):
    """The accepted checkpoint's path set, read WHERE ITS OWNER KEEPS IT.

    `review_cycles.integration_checkpoint` nests it under `evidence`, beside
    the base and the head this request already reads from there. Reading it at
    the top level -- as the first form did -- is a field that owner never
    answers with.
    """
    held = boundaries.document(accepted, "an accepted integration checkpoint")
    evidence = held.get("evidence")
    if type(evidence) is not dict or "path_set_digest" not in evidence:
        _refuse(f"this accepted checkpoint carries no evidence path set; a "
                f"preparation runs the paths an accepted verdict authorized "
                f"and there is none to name",
                category="integrity", code="schema")
    return evidence["path_set_digest"]


def preparation_child_work(authority_uuid, orchestration_id):
    """The child Work identity a FIRST sweep composes.

    DERIVED SO A CRASH BEFORE THE INTENT COMMITS STILL REACHES ONE NAME. Once
    the intent exists it is authoritative and this is not consulted again --
    `_preserved` refuses operands naming any other child -- but the window
    before that commit is real, and a minted identity would make two sweeps in
    it ask for two children.

    IT CARRIES THE AUTHORITY'S OWN PREFIX because a Work id that does not is
    refused by the manifest rules a frozen result is held to.
    """
    from baton_v12.contracts import digest

    boundaries.text(authority_uuid, "an authority uuid")
    boundaries.identity(orchestration_id, "an orchestration id")
    # THE AUTHORITY'S OWN GRAMMAR, not a readable one of mine. Measured on the
    # real traversal: `create_work` refused
    # `0000000a-integration-attempt-…` because "a Work id is the full
    # canonical <8 hex>-W<positive> identity and a local selector is not one".
    # So the orchestration is carried as a DERIVED POSITIVE NUMBER rather than
    # spelled into the id -- still a pure function of the orchestration, so a
    # resumed sweep reaches the same child, and still inside the grammar its
    # owner enforces.
    held = int(digest(orchestration_id)[len("sha256:"):][:12], 16)
    return boundaries.identity(
        f"{authority_uuid[:8]}-W{held + 1}", "a preparation child Work id")


def preparation_operands(*, orchestration_id, execution_work_id,
                         execution_route, participant, accepted, proposal_id,
                         canonical_target_id, job_id, line_id,
                         target_revision, test_scope_digest, harness_digest,
                         profile_digest, policy_digest, profile_name,
                         apply_task_digest, limits, published, published_root,
                         accept, identity, contract=None):
    """One managed preparation's operands, composed from OWNER ANSWERS.

    EVERY OPERAND HERE IS SOMEBODY ELSE'S ANSWER. `accepted` is the development
    line's own integration checkpoint, so the base and the candidate are the
    evidence that checkpoint carries rather than revisions this composition
    chose; `proposal_id` is what the producer actually published; the target
    revision is the Authority's canonical one at the moment the intent is
    committed, PINNED here because a preparation is about an immutable snapshot
    and a target that moves later does not retarget a run that started;
    `limits` is the Job's own resolved configuration; and `published` is the
    measurement `compose_preparation_input` took over the bundle it wrote --
    the one operand a caller must not supply, because supplying it would assert
    a measurement it did not take.

    THE TWO AUTHORITY DIGESTS COME FROM TWO DIFFERENT OWNERS, and review
    claim169146 is why that is written out. The first form read
    `accepted["path_set_digest"]` and `accepted["test_scope_digest"]` off the
    checkpoint, and my fixture invented both at the top level -- so the
    mismatch was invisible. The REAL `review_cycles.integration_checkpoint`
    answers `line_id`, `checkpoint_id`, `verdict_id`, `checkpoint_digest` and
    `evidence`: the path set is NESTED IN THE EVIDENCE, and there is no test
    scope on a checkpoint at all. So the path set is read where its owner keeps
    it, and the test scope is a SEPARATE OPERAND resolved from the selected
    configuration -- the required-test selection's own task digest. Inventing a
    checkpoint field, or widening that owner's generic answer to suit this
    composition, would have been the wrong repair in either direction.

    THE TASK DIGEST IS THE REQUEST'S OWN NAME. A membership's `task_digest` is
    what a later adoption compares the task against, and deriving it from the
    request means the plan and the request cannot disagree about what was asked
    for. The apply's is the caller's, because the apply is a different act this
    preparation does not describe.
    """
    from baton_v12.integration import managed_execution

    request = managed_execution.preparation_request(
        orchestration_id=orchestration_id,
        canonical_target_id=canonical_target_id, job_id=job_id,
        line_id=line_id, source_proposal_id=proposal_id,
        source={"base": accepted["evidence"]["base"],
                "candidate": accepted["evidence"]["head"],
                "target_revision": target_revision},
        authority={"path_set_digest": _accepted_paths(accepted),
                   "test_scope_digest": test_scope_digest},
        harness_digest=harness_digest, profile_digest=profile_digest,
        input_digest=published["input_digest"],
        execution_limits=limits, commands=list(CAUSAL_COMMANDS))
    if published["request"] != request:
        _refuse(f"the published input names a request this composition does "
                f"not produce; the bundle a worker reads and the request its "
                f"intent commits are one document",
                category="integrity", code="schema")
    held = preparation_identities(orchestration_id)
    return {"orchestration_id": orchestration_id,
            "execution_work_id": execution_work_id,
            "execution_route": execution_route,
            "participant": participant,
            "task_digest": managed_execution.request_digest(request),
            "apply_task_digest": apply_task_digest,
            "input_digest": published["input_digest"],
            "profile_digest": profile_digest,
            "policy_digest": policy_digest,
            "profile_name": profile_name,
            "contract": contract,
            # THE DURABLE ROOT THIS REQUEST WAS PUBLISHED TO, carried so a
            # later sweep can RECOVER it rather than compose a second one.
            # Review claim169347: the first form answered no root at all, so
            # `_recovered` had nothing to read and passed the recomposed
            # request straight through to a digest comparison it could only
            # fail once the target moved.
            "published_root": boundaries.text(published_root,
                                              "a published input root"),
            # THE WORKER'S OWN ACCEPTANCE, carried rather than performed here.
            "accept": accept,
            # AND THE IDENTITY ITS RUNTIME ATTEMPT IS RECORDED UNDER, which is
            # the configured child worker's and nothing this composition made.
            "identity": dict(identity),
            "request": request, **held}


class ChildAcceptance:
    """The WORKER's acceptance of the preparation offer, reusing the ordinary
    one.

    REVIEW claim169913 NAMED THE SHAPE AND IT IS `_SingleWorker`'s. That worker
    binds the one admissible intent before a bearer can be minted -- offer,
    attempt, Work and participant -- and `delivered` fences the ISSUED offer
    against exactly those four before calling the public `accept_offer` with
    the issued bearer and its own manifest's Work reference. This is that, for
    the child: an unconditional callback would accept whatever arrived, which
    is the fabricated half-handshake `PreparationExecution` refuses to produce
    itself.

    ACCEPTANCE IS A PARTICIPANT CAPABILITY BOUNDARY, NOT A PLACE. It does not
    have to originate inside the later workload process -- `JudgmentExecution`
    already drives a separate execution through these same operations -- and
    what makes it the worker's act is that it is fenced to the worker's own
    expected identities and carries the bearer only that worker was issued.

    IT IS NOT THE PARENT'S RECEIPT. Nothing here settles, reads or reuses the
    parent's offer; the child's acceptance is about the child's own four.
    """

    __slots__ = ("_control", "_port", "_expected", "_work_ref", "_now")

    def __init__(self, *, control, port, expected, work_ref, now):
        self._control = control
        self._port = port
        self._expected = dict(expected)
        self._work_ref = dict(work_ref)
        self._now = now

    def __call__(self, issued):
        from baton_v12.worker_manager import accept_offer

        held = boundaries.document(issued, "the issued preparation offer")
        for member, value in self._expected.items():
            if held.get(member) != value:
                _denied(f"the issued offer's {member} is "
                        f"{name_value(held.get(member))} and this preparation "
                        f"was admitted for {name_value(value)}; an acceptance "
                        f"is fenced to the offer its own admission bound")
        bearer = held.get("bearer")
        if not bearer:
            _denied("the issued preparation offer carries no bearer; an "
                    "acceptance delivers the credential that offer minted and "
                    "there is none to deliver")
        return accept_offer(
            self._control, self._port, offer_id=held["offer_id"],
            decision="accept", bearer=bearer, now=self._now(),
            runtime_attempt_id=held["runtime_attempt_id"],
            work_ref=dict(self._work_ref))


class PreparationAdmission:
    """W161230 A.4: the RESERVED-BEFORE-PARENT-OFFER interception.

    THE PLACEMENT IS THE CONTRACT, and review claim168871 corrected mine. I had
    proposed doing this in `stage_execution.Integration.reconciled`, which is
    too late on the ordinary Job path: `manager._launch` drives only stages
    whose state is already `claimed`, so by the time `reconciled` runs the
    parent has taken this actor's one Authority claim slot -- and a principal
    holds ONE live claim, so the child preparation could never be claimed
    beside it. `scheduler.PooledManagerOperations.admit` calls
    `_allocation(stage, create=True)` and only THEN the selected worker's
    `admit`, so wrapping that worker is the one place where the reservation
    exists and the parent offer does not.

    IT IS TRANSPARENT WHEN NOTHING SELECTS IT. A deployment that configures no
    managed preparation gets the operations it always had, method for method.
    That is deliberate rather than defensive: this wrapper sits on the path
    every integration stage takes, and a composition that changed behaviour for
    deployments that did not ask for it would be a migration nobody selected.

    THE PARENT IS DEFERRED, NEVER SETTLED. When preparation is selected and
    admitted, this raises a NONDURABLE `ContractRefusal` and issues no parent
    offer. `manager._delegate` reads exactly that -- an ordinary refusal with no
    canonical receipt -- as `deferred`, leaves the act owed and asks again on a
    later sweep. What this must never do is return normally without that
    receipt: `_delegate` treats a successful return with no journalled offer as
    an integrity fault, and it is right to.
    """

    __slots__ = ("_operations", "_preparation")

    def __init__(self, operations, preparation=None):
        self._operations = operations
        self._preparation = preparation

    def admit(self, stage, job):
        if self._preparation is None:
            return self._operations.admit(stage, job)
        return self._preparation.admit(self._operations, stage, job)

    def close(self):
        if self._preparation is not None:
            self._preparation.close()
        close = getattr(self._operations, "close", None)
        if close is not None:
            return close()
        return None

    def __getattr__(self, name):
        # EVERY OTHER ACT IS THE ORDINARY ONE. `claim`, `launch`, `dispatch`,
        # `conclude`, `observe` and `refresh_runtime` belong to the composed
        # worker and this adds nothing to them; forwarding by attribute rather
        # than by a written-out list is what keeps a member added there from
        # silently disappearing here.
        return getattr(self._operations, name)


class ManagedPreparation:
    """The act the wrapper performs when a deployment selects preparation.

    ADMISSION FIRST, IN THE ORDER THE ACCEPTED DESIGN FIXES: the reservation
    is read from its own owner, the capacity root and its two-phase plan are
    registered against that allocation, and `PreparationExecution` commits the
    intent, creates the child Work, issues and claims its offer, activates the
    assignment and admits the capacity -- all before anything starts and before
    the parent offer exists.

    THE APPLY MEMBER NAMES THE PARENT'S OWN IDENTITIES and invents none. The
    episode owner mints `offer_id` when it opens the episode, well before the
    Worker Manager issues that offer, so naming it here is reading a committed
    fact rather than predicting one. An apply planned under any other identity
    would be capacity nobody could match to the stage that spends it.

    AN ALREADY-CLAIMED PARENT REFUSES MANAGED CONVERSION. A stage whose parent
    already holds the claim has already taken this principal's one slot; the
    honest answer is that it stays on its recorded legacy path, not that this
    releases and reclaims it to make room.
    """

    __slots__ = ("_jobs", "_control", "_authority", "_port", "_mint",
                 "_orchestration", "_operands", "_runtime", "started", "adopted")

    def __init__(self, *, jobs, control, authority, port, mint_bearer,
                 orchestration, operands, runtime=None):
        self._jobs = jobs
        self._control = control
        self._authority = authority
        self._port = port
        self._mint = mint_bearer
        # WHICH ORCHESTRATION THIS STAGE IS, answered cheaply and WITHOUT
        # resolving anything. Review claim169347: the committed intent has to
        # be consulted BEFORE the resolver runs, and the resolver was what
        # answered the orchestration id -- so the branch could not happen
        # until after the very work it exists to skip.
        self._orchestration = orchestration
        # THE PER-STAGE OPERANDS ARE RESOLVED BY THE COMPOSER, not here. What
        # a preparation is ABOUT -- the accepted snapshot, the harness, the
        # Job's limits -- is the coordinator's to resolve from its own owners,
        # and a wrapper that reached for them would be a second resolver.
        self._operands = operands
        self.started = []
        self.adopted = {}
        self._runtime = runtime

    def close(self):
        if self._runtime is not None:
            self._runtime.close()

    def admit(self, operations, stage, job):
        from baton_v12.job_manager.integration_capacity import (
            preparation_intent_of, register_integration_capacity,
            recover_preparation_reservation)
        from baton_v12.job_manager.scheduler import allocation_of

        allocation = allocation_of(self._jobs, stage["attempt_id"])
        if allocation is None:
            _denied("this stage holds no scheduler allocation; a managed "
                    "preparation runs inside the reservation its parent "
                    "already owns, and there is none to run inside")
        if stage.get("state") == "claimed":
            _denied("this stage is already claimed, so its parent holds this "
                    "principal's one live Authority claim; a managed "
                    "preparation cannot be claimed beside it and this stage "
                    "stays on its recorded legacy path")
        # THE INTENT DECIDES WHICH WAY THIS GOES, and it is read FIRST so a
        # resumed sweep RECOVERS instead of resolving a fresh target it would
        # then be refused for.
        intent = preparation_intent_of(self._jobs,
                                       self._orchestration(stage, job))
        held = self._preserved(intent, self._operands(stage, job, intent))
        if self._runtime is not None:
            held = self._runtime.configure(held)
        plan = self.planned(stage, held)
        if intent is None and allocation["allocation_state"] == "recovery-required":
            recover_preparation_reservation(
                self._jobs, self._control, self._authority,
                orchestration_id=held["orchestration_id"])
        register_integration_capacity(
            self._jobs, orchestration_id=held["orchestration_id"],
            root_assignment_id=allocation["assignment_id"],
            authority_uuid=self._jobs.authority_uuid, plan=plan)
        execution = PreparationExecution(
            jobs=self._jobs, manager=self._control, control=self._control,
            authority=self._authority, port=self._port,
            mint_bearer=self._mint)
        answered = execution.prepare(
            orchestration_id=held["orchestration_id"],
            root_assignment_id=allocation["assignment_id"],
            request=held["request"], plan=plan,
            execution_work_id=held["execution_work_id"],
            execution_route=held["execution_route"],
            policy_digest=held["policy_digest"],
            profile_name=held["profile_name"],
            accept=held["accept"], identity=held["identity"],
            contract=held.get("contract"),
            admit=(None if self._runtime is None else
                   lambda: self._runtime.admit(held)))
        self.started.append(answered)
        if self._runtime is not None:
            result = self._runtime.poll(held, stage, job, execution)
            if result is not None:
                self.adopted[held["orchestration_id"]] = result
        # AND THE PARENT IS DEFERRED WITH NO RECEIPT. Nondurable on purpose:
        # nothing about the parent was journalled, so `_delegate` records this
        # as `deferred`, the admit stays owed, and a later sweep asks again
        # once the preparation has ended.
        raise ContractRefusal(
            "refused", "precondition",
            f"stage {name_value(stage['stage_id'])} is preparing under "
            f"orchestration {name_value(held['orchestration_id'])}; the parent "
            f"offer is not issued while the same actor holds this "
            f"reservation's preparation, and this admit stays owed")

    def _preserved(self, intent, held):
        """WHAT A LATER SWEEP MAY NOT QUIETLY CHANGE.

        Review claim169146 named this and it is the sharp edge of resuming at
        all: `preparation_identities` derives the attempt and the offer from
        the orchestration, but the CHILD WORK and the PINNED TARGET are not
        derived -- the Work is composed and the target is the Authority's
        canonical revision AT THE MOMENT THE INTENT WAS COMMITTED. A second
        sweep that re-resolved the canonical target after another Job
        integrated would compose a DIFFERENT request under the same
        orchestration: `Authority.create_work` would replay under the intent's
        operation id while the request it was decided for had silently moved,
        and the preparation would be running for a snapshot nobody decided on.

        SO THE COMMITTED INTENT IS AUTHORITATIVE ONCE IT EXISTS. Its
        `execution_work_id` is the child Work this orchestration already
        decided, and its `request_digest` is the request it decided. Operands
        that agree are used; operands that DISAGREE are refused rather than
        reconciled, because there is no honest way to pick between two answers
        about one committed decision, and picking the newer one is exactly the
        silent retarget this refuses.

        AND THE REQUEST IS RECOVERED RATHER THAN RECOMPOSED, which is review
        claim169283's correction of my first form. The intent persists the
        child Work and the request's DIGEST -- not the document and not the
        target it pinned -- so comparing a freshly composed request against
        that digest refuses a moved target forever and never resumes: the
        refusal is right and the orchestration is stuck behind it. The durable
        record of what was asked is the PUBLISHED INPUT this orchestration
        already wrote, so a sweep with a committed intent reads that request
        back, holds it to the intent's digest, and carries it forward --
        including the task digest derived from it, which is the request's own
        name and must not be left describing the recomposed one.

        A COMMITTED INTENT WITH NO PUBLISHED INPUT IS A MISSING DURABLE
        RECORD, not permission to compose a new one. It refuses.

        AN ABSENT INTENT IS THE FIRST SWEEP and carries no constraint: nothing
        has been decided yet, so there is nothing for these operands to
        contradict.
        """
        from baton_v12.integration import managed_execution

        if intent is None:
            return held
        held = self._recovered(intent, held)
        if intent["execution_work_id"] != held["execution_work_id"]:
            _denied(f"this orchestration already decided child Work "
                    f"{name_value(intent['execution_work_id'])} and these "
                    f"operands name "
                    f"{name_value(held['execution_work_id'])}; a resumed "
                    f"sweep runs the child its own intent committed, and a "
                    f"second one is the duplicate that intent exists to "
                    f"prevent")
        asked = managed_execution.request_digest(held["request"])
        if intent["request_digest"] != asked:
            _denied(f"this orchestration committed request "
                    f"{name_value(intent['request_digest'])} and these "
                    f"operands compose {name_value(asked)}; a preparation is "
                    f"about the snapshot its intent decided, so a sweep that "
                    f"resolved a moved target is refused rather than quietly "
                    f"preparing something else")
        return held

    def _recovered(self, intent, held):
        """The request this orchestration ALREADY PUBLISHED, read back.

        `published_root` is the destination `compose_preparation_input` wrote,
        and it is an operand rather than a derivation because the composer
        chooses where its bundles live. Without one there is nothing to
        recover from and the supplied request stands or falls on the digest
        comparison below -- which is the honest answer for a caller that kept
        no durable record.
        """
        from baton_v12.integration import managed_execution

        place = held.get("published_root")
        if place is None:
            _denied(f"orchestration {name_value(held['orchestration_id'])} "
                    f"committed an intent and these operands name no "
                    f"published input root; there is nothing to recover the "
                    f"decided request from, and comparing a recomposed one "
                    f"against the committed digest can only refuse")
        recovered = self._published(place)
        if recovered is None:
            _denied(f"orchestration {name_value(held['orchestration_id'])} "
                    f"committed an intent and this deployment holds no "
                    f"published preparation input for it; the request it "
                    f"decided is not recoverable, and composing a new one "
                    f"would be deciding it again")
        asked = managed_execution.request_digest(recovered)
        if intent["request_digest"] != asked:
            _denied(f"the published preparation input composes "
                    f"{name_value(asked)} and this orchestration's intent "
                    f"decided {name_value(intent['request_digest'])}; the "
                    f"durable record and the decision must name one request")
        return {**held, "request": recovered,
                "task_digest": asked,
                "input_digest": recovered["input_digest"]}

    def _published(self, place):
        from . import integration_bundle

        return integration_bundle.published_preparation_request(place)

    def planned(self, stage, held):
        """The two-phase plan, with the apply naming the PARENT'S OWN row."""
        return [{"phase": PREPARATION_PHASE,
                 "execution_attempt_id": held["execution_attempt_id"],
                 "execution_work_id": held["execution_work_id"],
                 "execution_offer_id": held["execution_offer_id"],
                 "participant": held["participant"],
                 "task_digest": held["task_digest"],
                 "input_digest": held["input_digest"],
                 "profile_digest": held["profile_digest"]},
                {"phase": "apply",
                 "execution_attempt_id": stage["attempt_id"],
                 "execution_work_id": stage["work_id"],
                 "execution_offer_id": stage["offer_id"],
                 "participant": held["participant"],
                 "task_digest": held["apply_task_digest"],
                 "input_digest": held["input_digest"],
                 "profile_digest": held["profile_digest"]}]


def manager_session(minted):
    """THE DEPLOYMENT'S OWN narrow view of an already-minted session.

    REUSED, NOT RESTATED. `single_worker._ManagerClaimSession` is what this
    deployment hands the Worker Manager's port in production -- see
    `single_worker._compose_one` -- and it is the reason a real Authority
    session can back that port at all: it forwards the session's actual
    lifecycle acts, REFUSES inquiry publication explicitly rather than
    answering a successful-looking no-op, and translates a concrete Authority
    claim refusal into the manager's closed vocabulary.

    I REPORTED THE ABSENCE OF THAT ONE MEMBER AS A MISSING OWNER API. It is
    not: a bare `authority.Session` carries no `publish_answer` and a port over
    it does refuse, but the deployment already decided what this capability is
    -- a typed refusal -- and composing a second adapter here would be a second
    account of that decision. The first time the two disagreed, only one would
    be right and nothing would say which.

    THE UNDERSCORE IS `single_worker`'S OWN MARK and reaching for it is
    deliberate rather than careless: it says that adapter belongs to this
    deployment, and this composition IS the same deployment rather than a
    stranger reaching in. Nothing is minted here -- the caller's session is the
    one capability and this view is narrower than it, not wider.
    """
    from . import single_worker

    return single_worker._ManagerClaimSession(minted)


def authority_port(authority, participant):
    """The Worker Manager's capability over a REAL participant-bound session.

    One minted session, the deployment's adapter over it, and the AUTHORITY'S
    OWN claim signature. The signature is consumed rather than recomputed for
    the reason the port takes it by injection: a manager that derived claim
    identity itself would be a second authority on the one question -- are
    these two claims the same claim -- and the first disagreement would have no
    tiebreak.

    THE PARTICIPANT IS A BINDING AND NOT AN OPERAND ANYWHERE DOWNSTREAM. The
    session takes its claimant from this minting and refuses a supplied one, so
    every act the port performs is attributed to this identity and no caller
    can address another.
    """
    from baton_v12.authority import claim_signature
    from baton_v12.worker_manager import AuthorityPort

    return AuthorityPort(manager_session(authority.session(participant)),
                         claim_signature)


class PreparationExecution:
    """One managed preparation's real child Work, offer, claim and admission.

    THE ORDER IS THE WHOLE CONTRACT, and each step exists because doing it
    later would be unsound:

      1. THE INTENT IS COMMITTED FIRST, before the Work it needs exists. It
         carries the `work_operation_id` that `Authority.create_work` is then
         called with, so an interrupted creation is RESUMED rather than
         repeated -- which is the difference between one child Work and two.

      2. THE CHILD WORK IS REAL. It is created at the Authority under that
         operation id; nothing here fabricates a Work id, a claim receipt or an
         assignment.

      3. THE OFFER AND THE CLAIM ARE THE ORDINARY ONES. `issue_offer` and
         `submit_claim` are the same operations every other attempt uses.

      4. THE ASSIGNMENT IS READ FROM THE WORKER MANAGER, never accepted from a
         caller. `assignment_of` answers what activation actually fixed; a
         well-formed dictionary is not evidence that a claim happened.

      5. CAPACITY IS ADMITTED BEFORE ANYTHING IS STARTED. `admit_integration_execution`
         is the gate a runtime start is behind: committed first, so a crash
         between the two leaves capacity held and a member to reconcile --
         never a runtime nobody accounted for.

    THE PARENT OFFER IS NOT TOUCHED. The same actor holds the parent while it
    prepares, so this issues no ending, no release and no second allocation for
    it: the preparation runs under the ONE reserved root the intent named. A
    composition that settled the parent here would hand the root back while its
    own preparation was still running on it.
    """

    def __init__(self, *, jobs, manager, control, authority, port,
                 mint_bearer):
        self._jobs = jobs
        self._manager = manager
        self._control = control
        self._authority = authority
        self._port = port
        self._mint = mint_bearer
        self.started = []

    def prepare(self, *, orchestration_id, root_assignment_id, request, plan,
                execution_work_id, execution_route, policy_digest,
                profile_name, accept, identity, contract=None, admit=None):
        """Decide, create, offer, claim, admit -- and answer what was fixed.

        THE ATTEMPT AND THE OFFER COME FROM THE REGISTERED PLAN, not from
        operands beside it. Admission compares the membership against that
        plan, so a composition that minted its own offer id -- as the first
        form of this did, deriving `"offer-" + work_operation_id` -- would
        issue one offer and be admitted against another.
        """
        planned = self.planned(plan)
        runtime_attempt_id = planned["execution_attempt_id"]
        intent = self.decide(
            orchestration_id=orchestration_id,
            root_assignment_id=root_assignment_id, request=request, plan=plan,
            execution_work_id=execution_work_id,
            execution_route=execution_route)
        self.create(intent, contract=contract)
        offer_id = planned["execution_offer_id"]
        # Read the committed claim before issuing or accepting again. An offer's
        # bearer is delivered once; a later sweep consumes its owner's receipt.
        settled = self._manager.operation_record("offer.settle:" + offer_id)
        if settled is not None:
            claimed = json.loads(settled["result"])
            if claimed["state"] != "claimed":
                _denied("the preparation offer ended without a claim")
        else:
            from baton_v12.worker_manager.events import publish_offer_states

            class States:
                def __init__(self):
                    self.answers = []

                def publish(self, answer):
                    self.answers.append(answer)

            states = States()
            publish_offer_states(self._manager, states, [offer_id])
            state = states.answers[0]["state"] if states.answers else None
            if state != "accepted":
                if state is not None:
                    _denied("the preparation offer has no recoverable acceptance; "
                            "its owner's recovery must settle the outstanding offer")
                if admit is not None:
                    # The configured child owns the expected-offer window and
                    # bearer delivery. Its ordinary admission issues/accepts.
                    admit()
                else:
                    issued = self.offer(intent, planned, policy_digest=policy_digest,
                                        profile_name=profile_name,
                                        runtime_attempt_id=runtime_attempt_id)
                    if accept is None:
                        _denied("an offer is claimed after the worker accepts it")
                    accept(issued)
            claimed = submit_claim(self._manager, self._port, offer_id=offer_id)
        # ACTIVATION IS WHAT FIXES THE ASSIGNMENT, and it is expected against
        # THE CLAIM'S OWN ANSWER rather than a document written here: a
        # composition that supplied its own `expect` would be activating
        # whatever it hoped the authority had said. `assignment_of` refuses an
        # attempt that only claimed, which is the right order -- a membership
        # is admitted against a FIXED assignment.
        # THE RUNTIME ATTEMPT, RECORDED BEFORE IT IS ACTIVATED.
        #
        # SLICE2-SCOPE-165724.md lines 66-73 already answered the ordering I
        # returned as an open question, and I should have re-read the pinned
        # selection instead of asking: "PreparationExecution may call the SAME
        # public record_attempt/activate_assignment operations with the exact
        # same operands after its claim, admit its capacity membership, then
        # call ordinary operations.launch. The launch's repeats replay those
        # owner acts." So this is `_SingleWorker.start`'s own sequence --
        # record, then activate against the claim's own answer -- and the
        # later ordinary launch replays both rather than repeating them.
        #
        # THE OPERANDS ARE THE CHILD WORKER'S OWN, supplied by the composer
        # that holds its configured identity. Nothing here derives an adapter,
        # an image or a toolchain: a composition that invented any of them
        # would be recording an attempt about a runtime nobody configured.
        # The ordinary child manifest is the offer/attempt/capacity identity.
        # The published source tree has its own digest in the request; it is
        # checked by the workload and adoption, not substituted for a manifest.
        record_attempt(self._manager, attempt_id=runtime_attempt_id,
                       **dict(identity,
                              input_digest=planned["input_digest"]))
        activate_assignment(self._manager, self._port,
                            attempt_id=runtime_attempt_id,
                            expect=claimed["assignment"])
        assignment = assignment_of(self._manager, runtime_attempt_id)
        capacity = integration_capacity_of(self._jobs, orchestration_id)
        member = next(one for one in capacity["members"]
                      if one["execution_attempt_id"] == runtime_attempt_id)
        admitted = (capacity if member["state"] == "ended" else
                    self.admit(intent, runtime_attempt_id=runtime_attempt_id,
                               assignment=_admissible(assignment)))
        return {"intent": intent, "offer_id": offer_id, "claim": claimed,
                "assignment": assignment, "admitted": admitted,
                "execution_attempt_id": runtime_attempt_id}

    def decide(self, **operands):
        """Step 1. Committed before the Work exists, and REPLAYABLE."""
        return record_preparation_intent(
            self._jobs, authority_uuid=self._jobs.authority_uuid, **operands)

    def create(self, intent, *, contract=None):
        """Step 2. Under the intent's own operation id, so a resumed run does
        not mint a second child Work for one decision."""
        return self._authority.create_work(
            intent["execution_work_id"], intent["execution_route"],
            operation_id=intent["work_operation_id"], contract=contract)

    def planned(self, plan):
        """The PREPARATION member of the registered plan, or a refusal.

        A plan with no preparation phase is a plan for something else, and
        picking the first member would quietly prepare under the apply's
        identities."""
        for one in plan:
            if one.get("phase") == PREPARATION_PHASE:
                return one
        _denied("this plan registers no " + PREPARATION_PHASE + " phase, so "
                "there is no preparation for this composition to run")

    def offer(self, intent, planned, *, policy_digest, profile_name,
              runtime_attempt_id):
        """Step 3. The ordinary offer, on the child Work, under the offer id
        the plan registered."""
        offer_id = planned["execution_offer_id"]
        return issue_offer(self._manager, self._port, offer_id=offer_id,
                           work_id=intent["execution_work_id"],
                           runtime_attempt_id=runtime_attempt_id,
                           input_digest=planned["input_digest"],
                           policy_digest=policy_digest,
                           profile_digest=planned["profile_digest"],
                           profile_name=profile_name,
                           mint_bearer=self._mint)

    def admit(self, intent, *, runtime_attempt_id, assignment):
        """Step 5. THE GATE. Nothing may start before this commits."""
        return admit_integration_execution(
            self._jobs, self._control,
            orchestration_id=intent["orchestration_id"],
            phase=PREPARATION_PHASE,
            execution_attempt_id=runtime_attempt_id, assignment=assignment)

    def start(self, orchestration_id, runtime_attempt_id, launch):
        """The ordinary launch, BEHIND the admission that authorises it.

        A start is not permitted on the strength of an intent: an intent
        decides, and capacity admits. So this re-reads the committed decision
        and refuses a launch for an orchestration that has not been admitted,
        rather than trusting the caller to have called `admit` first.
        """
        if preparation_intent_of(self._jobs, orchestration_id) is None:
            _denied("this orchestration decided no preparation, so there is "
                    "nothing a runtime would be starting")
        if not self._admitted(orchestration_id, runtime_attempt_id):
            _denied("this preparation has not been admitted; capacity is the "
                    "gate a runtime start is behind, and starting first would "
                    "leave a runtime nobody accounted for")
        self.started.append(runtime_attempt_id)
        return launch()

    def _admitted(self, orchestration_id, runtime_attempt_id):
        """Read through the capacity owner's OWN public reader, so this is
        what the store says rather than what this object remembers."""
        held_capacity = integration_capacity_of(self._jobs, orchestration_id)
        for held in held_capacity["members"]:
            if held.get("execution_attempt_id") != runtime_attempt_id \
                    or held.get("phase") != PREPARATION_PHASE:
                continue
            # A PLANNED MEMBER IS NOT AN ADMITTED ONE, and the first form of
            # this check accepted either. Registration PLANS the phases an
            # orchestration intends; admission is the separate act that takes
            # the capacity. Treating a plan as permission to start is exactly
            # the runtime-nobody-accounted-for this gate exists to prevent,
            # and a focused case caught it here rather than in a deployment.
            return held.get("state") == "admitted"
        return False

    def claimed_offer(self, runtime_attempt_id):
        """The offer the claim actually settled, from the Worker Manager's own
        reader -- not the one this composition thinks it issued."""
        return claimed_offers_for(self._manager, runtime_attempt_id)
