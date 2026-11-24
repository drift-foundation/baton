"""W385695 internal checkpoint 2 — the deterministic publication of one
retained output, its read-only staging, its absolute deadline, the custody it
enters and the review gate that stays shut until the handoff is valid.

WHAT THESE CASES ARE ABOUT. Checkpoint 1 ended at a HELD admission: an owner
could inspect the original output of an implementation that completed and then
failed to publish, record an exact decision about it, and be told truthfully
that this build could not serve a publication stage. These cases are
everything after that -- the `/4` submission, the publication lane, the
schema-10 store and the enforced finite profile are installed, so the
admission is real; the prior assignment on the reused Work is ENDED through
the Authority's own transition and the publication worker CLAIMS it fresh; the
approved original is staged read-only and published byte-for-byte under that
fresh assignment with a separately bounded provenance beside it; the ordinary
freeze and intake take custody of it; and the review gate opens on exactly one
record and on nothing weaker.

WHAT IS REAL HERE, and the list is what makes this evidence rather than a
demonstration.

  THE ASSIGNMENT ENDING AND THE FRESH CLAIM ARE THE AUTHORITY'S OWN. A real
  Authority store, a real route, real endpoint bindings, the producer's real
  claim at generation 1, `Session.end` through the production
  `tools.publication_ports.PriorAssignment` adapter over the producer's own
  participant-bound session, and then the publication worker's real
  `issue_offer`/`accept_offer`/`submit_claim`/`activate_assignment` at
  generation 2. No factory mints an arbitrary session anywhere in this file
  and no raw SQL makes a Work available.

  THE ORIGINAL BYTES ARE REAL, MEASURED AND NEVER WRITTEN. The failed
  attempt's proposal tree is checkpoint 1's own real fixture on disk-backed
  storage, read back through `workspaces.retained_output_of`; the staging copy
  goes through `workspaces.copied_manifest`, and every case that publishes
  compares the original's tree digest before and after.

  THE WRITER IS THE PRODUCTION ADAPTER. `tools.publication_worker.
  PublicationWriter` is what adopts the bytes and publishes the completion
  envelope in every case below, including the negative ones; nothing here
  stands in for it.

  THE CUSTODY PATH IS THE ORDINARY ONE. `request_freeze` and `request_intake`
  are the Worker Manager's own public operations, over a real sealed result
  measured off real files.

  THE GATE IS THE PROJECTION'S. `projection.stage_states` is what reports the
  review stage `blocked` or `queued`, and `projection.owed_acts` is what
  counts the offers; no case opens a gate by writing one.

WHAT IS FAKED, AND ONLY AT ITS NORMAL BOUNDARY: the host's record of the
original attempt's runtime and workspace token, the DEPLOYMENT CONFIGURATION's
binding and selector (which is where a deployment states which worker it
installed), the instance guard, the ENGINE the Git-aware consumer's commands
run at, and the ENGINE/CUSTODIAN the freeze and intake reach the host through.
There is no provider, no model, no image and no container in this file.

AND ONE CASE USES NO SUBSTITUTE AT ALL for the owner ports: the joined case
installs a disposable instance with `tools.bootstrap` and runs the installed
owner commands with NO `--owners` operand, so the seven ports are
`tools.publication_decision.owners`' own over that instance's emitted
configuration -- which answers, truthfully, that it has installed no
publication worker, and holds the admission with that named.

WHAT IS DELIBERATELY ABSENT. No reviewer is invoked and no verdict is written:
the production review binding, the reviewer's own tests and the packaged CLI
acceptance are checkpoint 3. What is asserted instead is that the gate OPENS,
that exactly one review offer becomes owed when it does, that ZERO become owed
in every incomplete state, and that this manager writes no verdict.
"""

import copy
import json
import os

from baton_v12.job_manager import (cancellation, documents, episodes,
                                   job_control, projection,
                                   publication_execution,
                                   publication_recovery, role_contract,
                                   scheduler, submission)
from baton_v12.worker_manager import workspaces
from baton_v12.worker_manager.sealing import declared_outputs

from tests.job_manager import test_publication_recovery_admission as checkpoint1
from tests.job_manager.fixtures import NOW, WORK_A
from tools import publication_worker

# THE AUTHORITY THIS SUITE'S FIXTURE BELONGS TO, derived from the Work it
# runs. §4 relates the two: "a Work id carries its authority's prefix", and a
# reference that does not is a reference to somebody else's Work wearing this
# one's name. Checkpoint 1 never has to satisfy that relation -- it composes
# no assignment manifest and publishes no completion envelope -- and these
# cases do both, through the frozen validator, so the fixture's Authority is
# the one its Work really names.
AUTHORITY = WORK_A.split("-", 1)[0] + "0" * 24

OWNER = checkpoint1.OWNER
# THE PRODUCER'S REAL AUTHORITY ADDRESS, in the grammar the Authority keeps.
# Checkpoint 1 writes its producer onto the ATTEMPT ROW by hand and never at
# the Authority, so its own spelling never had to be an address; these cases
# make the producer really CLAIM the Work, so it must be one.
PRODUCER = "baton.implementer"
PRODUCER_PRINCIPAL = "principal:implementer"
ROUTE = checkpoint1.ROUTE
WORK_SCOPE = checkpoint1.WORK_SCOPE
HEAD = checkpoint1.HEAD
BASE = checkpoint1.BASE

# THE DETERMINISTIC PUBLICATION WORKER THIS DEPLOYMENT INSTALLED, as a
# deployment states one: a participant, a principal and the profile a
# publication stage must name to be selectable in the publication lane.
PUBLISHER = "baton.publisher"
PUBLISHER_PRINCIPAL = "principal:publisher"
PUBLISHER_WORKER_ID = "publication-1"
PUBLISHER_PROFILE = "publication-reference"
PUBLISHER_DIGEST = "sha256:" + "7" * 64
REVIEWER = "baton.reviewer"
POLICY = "sha256:" + "2" * 64

# The instants this suite steps through. The publication stage's absolute
# 900-second bound runs from its own execution admission, so a case about the
# deadline moves the clock rather than editing a record.
ADMITTED = "2026-09-02T00:10:00.000Z"
CLAIMED = "2026-09-02T00:11:00.000Z"
PUBLISHED = "2026-09-02T00:12:00.000Z"
LATE = "2026-09-02T00:30:00.000Z"


class PublishingBinding(checkpoint1.FakeBinding):
    """The deployment configuration, with a publication worker installed.

    THIS IS THE ONE BOUNDARY A DEPLOYMENT REALLY DECIDES AT. Which workers an
    instance installed, which lanes they are in and which profiles they carry
    are configuration facts, and checkpoint 1 already stands this port in for
    the same reason. What is NOT faked is what the manager does with the
    answer: `_installed_worker` proves the lane and the eligible kinds, the
    composed `/4` document names this worker's own profile, and `_bound`
    refuses unless the selector really answers this participant for the
    publication stage.
    """

    def __init__(self, identity=None, worker=..., serving=True,
                 input_digest=None):
        super().__init__(identity)
        self.worker = ({"worker_id": PUBLISHER_WORKER_ID,
                        "participant": PUBLISHER,
                        "lane": scheduler.PUBLICATION_LANE,
                        "profile_name": PUBLISHER_PROFILE,
                        "profile_digest": PUBLISHER_DIGEST,
                        "eligible_kinds": [scheduler.PUBLICATION_LANE],
                        # THE INSTALLED WORKER'S OWN INPUT MANIFEST IDENTITY,
                        # which is what a recovery Job is submitted under and
                        # what its offer is made against.
                        "input_digest": input_digest}
                       if worker is ... else worker)
        self.serves = serving

    def publication_worker(self):
        self.asked.append("publication_worker")
        return None if self.worker is None else dict(self.worker)

    def serving(self, job_id, *, stage, job, task=None):
        self.asked.append((job_id, dict(stage)))
        if not self.serves:
            return []
        if stage["kind"] == documents.PUBLICATION_STAGE:
            return [PUBLISHER]
        return [REVIEWER]


class PublicationCustodian:
    """THE ENGINE AND CUSTODIAN BOUNDARY, and the actual file sealing above it.

    `test_review_driver._ReviewFileCustodian`'s shape and its reason: the
    public manager owners create every output, intake and cleanup record, the
    external engine has no container, and the seal and the collection are the
    SHIPPED `sealing.sealed_result` and `sealing.collected_result` over real
    files in a real directory. What this stands in for is the engine that would
    have run the container and the custodian helper that would have copied the
    tree -- which is the normal boundary for both.
    """

    custodian_image_digest = "sha256:" + "c" * 64

    def __init__(self, roots, declaration, custody):
        from baton_v12.worker_manager.sealing import declared_outputs as owned

        self.roots = roots
        self.declaration = declaration
        self.declared = owned(declaration["outputs"])
        self.input_digest = declaration["manifest_digest"]
        self.custody = custody
        os.makedirs(custody, exist_ok=True)
        self.seals = []
        self.collected_with = []
        self.destroyed_with = []
        self.retained_with = []
        self.listed = []
        self.surviving = []
        self.normalized = []

    # -- the engine side ---------------------------------------------------

    def surviving_helpers(self, store, *, assignment_id, seconds=None,
                          reclaim=None):
        self.listed.append(assignment_id)
        return list(self.surviving)

    def normalize_directory(self, store, *, assignment_id, which):
        from baton_v12.worker_manager import custody as owner

        self.normalized.append((assignment_id, which))
        return owner._answered(
            "normalize", 0,
            {"custody": "normalize", "submission": "0" * 32, "entries": 0,
             "not_ours": 0, "running_as": [0, 0]}, None)

    # -- the two acts the freeze and the intake reach the host through -----

    def seal(self, operands):
        from baton_v12.worker_manager.sealing import sealed_result

        self.seals.append(dict(operands))
        return sealed_result(operands, roots=self.roots,
                             declared=self.declared,
                             identity={"policy_digest": POLICY},
                             custody=self.custody,
                             input_manifest_digest=self.input_digest)

    def collect(self, operands):
        from baton_v12.worker_manager.sealing import collected_result

        self.collected_with.append(dict(operands))
        return collected_result(operands, custody=self.custody,
                                declared=self.declared)

    # -- the two the ORDINARY ending reaches afterwards --------------------

    def retain(self, operands):
        self.retained_with.append(dict(operands))
        return True

    def destroy(self, command):
        """THE ENGINE HAS NO CONTAINER, so the destroy is the absence it is.

        `tests.manager.test_intake.Custodian.destroy`'s answer shape: every
        provider answers on every destroy and an attempt with no such provider
        says `not-delivered` explicitly, which is what a deterministic
        publication worker that ran no provider session really is.
        """
        self.destroyed_with.append(dict(command))
        return {"runtime_id": command["runtime_id"], "state": "absent",
                "why": "deterministic engine destroyed",
                "providers": {"claude-code": "not-delivered"},
                "mounts": None}


class PublicationExecutionCase(checkpoint1.PublicationCase):
    """One admitted recovery of checkpoint 1's own failed publication.

    THE FAILED JOB IS CHECKPOINT 1'S, UNCHANGED. Its fixture is inherited
    rather than rebuilt, which is the point: these cases publish the exact
    bytes that suite inspects, through the exact decision it records, so a
    drift between the two slices is a failing case here rather than two
    fixtures that agree with themselves.
    """

    maxDiff = None

    def prepared_attempt(self, attempt_id, participant=None):
        """The failed attempt, under the producer's REAL Authority address.

        Checkpoint 1's fixture defaults to a bare worker name because nothing
        in that slice reaches the Authority with it. These cases end the
        producer's real claim, and an assignment is ended by its own holder --
        so the participant on the attempt row and the participant that claimed
        the Work have to be one address, in the grammar the Authority keeps.
        """
        return super().prepared_attempt(
            attempt_id, participant=participant or PRODUCER)

    def setUp(self):
        from unittest import mock

        # THE FIXTURE'S AUTHORITY, RELATED TO ITS OWN WORK, for the whole of
        # this case. Checkpoint 1's own constant is left exactly as it is: the
        # patch is scoped to this case and restored, so running both suites in
        # one process leaves neither reading the other's.
        patched = mock.patch.object(checkpoint1, "UUID", AUTHORITY)
        patched.start()
        self.addCleanup(patched.stop)
        super().setUp()
        # THE PRODUCER REALLY HOLDS THE WORK AT THE AUTHORITY. Checkpoint 1's
        # fixture records the assignment on the ATTEMPT row, which is the
        # Worker Manager's half; the Authority's half is a real claim, and
        # without it there would be no assignment for a recovery to end.
        self.authority.bind_endpoint(PRODUCER, PRODUCER_PRINCIPAL)
        self.authority.add_route_handler(ROUTE, PRODUCER)
        self.authority.bind_endpoint(PUBLISHER, PUBLISHER_PRINCIPAL)
        self.authority.add_route_handler(ROUTE, PUBLISHER)
        self.producer_session = self.authority.session(PRODUCER)
        self.producer_session.claim({"work_id": WORK_A,
                                     "operation_id": "claim-producer"})
        self.held_assignment = self.authority.assignment_of(WORK_A)
        self.staging = publication_worker.staging_root(
            checkpoint1.CURRENT["identity"]["root"])

    # -- the owner ports, with a deployment that installed a publisher -----

    def ported(self, **changed):
        held = super().ported()
        binding = checkpoint1.CURRENT.setdefault("ports", {}).get("publishing")
        if binding is None:
            binding = PublishingBinding(
                identity=checkpoint1.CURRENT["identity"],
                input_digest=self.publication_declaration()[
                    "manifest_digest"])
            checkpoint1.CURRENT["ports"]["publishing"] = binding
        held["binding"] = binding
        held["ending"] = self.ending_port()
        held.update(changed)
        return held

    def ending_port(self, sessions=None):
        """THE PRODUCTION ENDING ADAPTER over this case's real Authority.

        The fixture supplies the producer session that actually claimed Work.
        """
        from tools.publication_ports import PriorAssignment

        return PriorAssignment(self.authority,
                               checkpoint1.CURRENT["identity"],
                               sessions=sessions if sessions is not None else
                               lambda who: self.producer_session if who == PRODUCER else None)

    def admit(self, *, decision_id="D1", now=ADMITTED, **changed):
        held = self.ported()
        held.update(changed)
        return publication_recovery.admit_publication(
            self.jobs, self.control, decision_id=decision_id,
            exclusion=held["exclusion"], authorization=held["authorization"],
            binding=held["binding"], ownership=held["ownership"],
            host=held["host"], source=held["source"],
            ending=held.get("ending"), now=now)

    def approve_and_admit(self, *, decision_id="D1", **changed):
        self.approved(decision_id=decision_id)
        return self.admit(decision_id=decision_id, **changed)

    # -- the four acts, driven in order ------------------------------------

    def ready(self, **changed):
        """Admitted, claimed and durably started: everything act one needs."""
        self.approve_and_admit(**changed)
        held = self.claim_publication()
        self.admit_stage()
        return held

    def staged(self, *, now=PUBLISHED, **changed):
        return publication_execution.stage_input(
            self.jobs, self.seam(**changed), decision_id="D1", now=now)

    def published_once(self, *, now=PUBLISHED, **changed):
        return publication_execution.publish(
            self.jobs, self.seam(**changed), decision_id="D1", now=now)

    def collected(self, *, now=PUBLISHED, **changed):
        return publication_execution.take_custody(
            self.jobs, self.seam(**changed), decision_id="D1", now=now)

    def handed_off(self, *, now=PUBLISHED, **changed):
        return publication_execution.hand_off(
            self.jobs, self.seam(**changed), decision_id="D1", now=now)

    def quiescent(self, attempt_id=None):
        """The runtime observations the ordinary freeze requires.

        THE ENGINE IS THE FAKED BOUNDARY AND THESE ARE ITS OBSERVATIONS. A
        freeze describes a tree the writer has stopped changing, and only a
        positive quiescent observation says that -- `output._provable`'s rule,
        unchanged for the publication lane. Recorded through the Worker
        Manager's own `observe`, so the transition map is the product's.
        """
        from baton_v12.worker_manager import observe

        attempt_id = attempt_id or self.publication_attempt
        for axis, value in (("execution_runtime", "start-requested"),
                            ("execution_runtime", "running"),
                            ("execution_runtime", "quiescent"),
                            ("worker_disposition", "completed")):
            observe(self.control, attempt_id=attempt_id, axis=axis,
                    value=value)
        return attempt_id

    def settle_ending(self):
        """THE REST OF THE ORDINARY COMPOSED ENDING, through its own owners.

        THE FREEZE IS THE THIRD OF SEVEN STEPS and `projection._ending_owed`
        is explicit that a frozen output with an unsettled cleanup axis is an
        ending in progress -- so a stage is `completed`, and its dependent's
        gate open, only once the ending finishes. Those remaining steps are
        the SERVING manager's, not this capability's: REC-9's own sentence is
        that "ART-7 execution release remains independent of result
        acceptance". They are driven here through the Worker Manager's own
        public operations so the gate assertions below are about a real
        completed stage rather than about a half-finished one.
        """
        from baton_v12.worker_manager import frozen_output_of, observe

        # THE PUBLICATION'S OWN ASSIGNMENT IS RELEASED, through the publisher's
        # own session, which is ART-7 from the other side: the execution ends
        # because it FINISHED, and not because anybody accepted its result.
        self.authority.session(PUBLISHER).end(
            {"expect": self.authority.assignment_of(WORK_A),
             "operation_id": "publication-release"})
        # AND THE CLEANUP AXIS SETTLES, which is the engine's own act and is
        # the faked boundary here: there is no container in this file, so
        # there is no runtime identity to destroy and no absence to prove.
        # `intake.authorize_cleanup` says exactly that and refuses, correctly;
        # what the projection needs for the stage to be `completed` is the
        # settled axis, and it is recorded through the Worker Manager's own
        # `observe` so the transition map is the product's.
        observe(self.control, attempt_id=self.publication_attempt,
                axis="cleanup", value="retained")
        return frozen_output_of(self.control, self.publication_attempt)

    def whole_path(self, *, now=PUBLISHED):
        """ADMIT, CLAIM, START, STAGE, PUBLISH, SETTLE, COLLECT, END, HAND OFF."""
        self.ready()
        self.staged(now=now)
        self.published_once(now=now)
        self.quiescent()
        self.collected(now=now)
        self.settle_ending()
        return self.handed_off(now=now)

    # -- the publication worker's own FRESH CLAIM --------------------------

    def publication_declaration(self):
        """The input manifest the publication attempt is claimed against.

        IT DECLARES THE TWO OUTPUTS A RECOVERY PUBLISHES, and they are the
        product's own: W385694's exact selected proposal revision, read from
        the descriptor owner, and `publication_recovery.PROVENANCE_OUTPUT`
        composed from the owner-selected provenance descriptor. A manifest
        assembled out of this fixture's own numbers would be testing the
        fixture.
        """
        from tests.manager.test_output import OutputCase, sealed

        declaration = publication_recovery.corrective_declaration()
        # THE VECTOR'S OWN `work_ref` IS LEFT ALONE. `check_manifest_structure`
        # relates a manifest's Work to the Authority that names it, and this
        # fixture's Work id predates that relation; what these cases are about
        # is the two DECLARED OUTPUTS, so only those are replaced.
        document = dict(OutputCase.published(),
                        outputs=[copy.deepcopy(declaration["output"]),
                                 copy.deepcopy(
                                     publication_recovery.PROVENANCE_OUTPUT)],
                        policy_digest=POLICY,
                        runtime_profile_digest=PUBLISHER_DIGEST)
        return sealed(document)

    def claim_publication(self, *, now=CLAIMED, participant=PUBLISHER):
        """ISSUE, ACCEPT, RECORD, CLAIM, ACTIVATE -- the ordinary path.

        THE CLAIM IS THE AUTHORITY'S OWN and the generation is whatever it
        mints. Nothing here writes an assignment row by hand: the Work was
        released by the ending this admission performed, so this is the fresh
        claim the contract requires rather than a second account of the
        producer's.
        """
        from baton_v12.worker_manager import (accept_offer,
                                              activate_assignment,
                                              issue_offer, record_attempt,
                                              retain_manifest, submit_claim)
        # THE PRODUCTION COMPOSITION of a Worker Manager capability over a
        # REAL participant-bound Authority session: one minted session, this
        # deployment's own narrow adapter over it, and the Authority's own
        # claim signature. A bare `authority.Session` cannot back the port --
        # it carries no `publish_answer`, and the deployment already decided
        # that capability is a typed refusal -- so composing one here would be
        # a second account of that decision.
        from tools.integration_worker import authority_port

        self.instants.append(now)
        stage_id = documents.stage_id(self.recovery_job_id,
                                     documents.PUBLICATION_STAGE)
        live = episodes.live_of(self.jobs, stage_id)
        attempt_id, offer_id = live["attempt_id"], live["offer_id"]
        declaration = self.publication_declaration()
        input_digest = retain_manifest(self.control, declaration,
                                       "inputManifest")["digest"]
        port = authority_port(self.authority, participant)
        # THE PROFILE IS CERTIFIED FOR THIS MANAGER, through the owner that
        # certifies one. An offer promises an execution shape and this manager
        # refuses to promise one nothing agreed to -- which is the ordinary
        # rule for every lane and is not relaxed for the publication lane.
        from baton_v12.worker_manager import certify_profile

        certify_profile(self.control, "runtime", PUBLISHER_PROFILE,
                        PUBLISHER_DIGEST)
        issue_offer(self.control, port, offer_id=offer_id, work_id=WORK_A,
                    runtime_attempt_id=attempt_id, input_digest=input_digest,
                    policy_digest=POLICY, profile_digest=PUBLISHER_DIGEST,
                    profile_name=PUBLISHER_PROFILE,
                    mint_bearer=lambda: "publication-bearer")
        accept_offer(self.control, port, offer_id=offer_id, decision="accept",
                     bearer="publication-bearer", now=now,
                     runtime_attempt_id=attempt_id,
                     work_ref={"authority_uuid": AUTHORITY, "work_id": WORK_A})
        record_attempt(self.control, attempt_id=attempt_id,
                       adapter_name="publication", adapter_digest="sha256:"
                       + "6" * 64, profile_digest=PUBLISHER_DIGEST,
                       input_digest=input_digest, policy_digest=POLICY)
        submit_claim(self.control, port, offer_id=offer_id)
        assignment = self.authority.assignment_of(WORK_A)
        activate_assignment(self.control, port, attempt_id=attempt_id,
                            expect=assignment)
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                attempt_id)
        workspaces.record_preparation(self.control, attempt_id, roots,
                                      ["task", "inputs"])
        self.publication_roots = roots
        self.publication_attempt = attempt_id
        self.publication_port = port
        self.publication_declared = declaration
        self.custodian = PublicationCustodian(
            roots, declaration, os.path.join(self.root, "publication-custody"))
        return {"attempt_id": attempt_id, "assignment": assignment,
                "roots": roots, "input_digest": input_digest}

    def admit_stage(self):
        """Adopt the real owner admission through the manager's receipt path."""
        from baton_v12.job_manager import manager

        manager.sweep(self.jobs, self.acts(), now=CLAIMED)
        stage_id = documents.stage_id(self.recovery_job_id,
                                      documents.PUBLICATION_STAGE)
        origin = job_control.stage_origin_in(self.jobs._connection, stage_id)
        self.assertIsNotNone(origin)
        return origin

    # -- the publication seam ----------------------------------------------

    def workspace_of(self, attempt_id):
        return os.path.join(self.storage, attempt_id, "workspace")

    def seam(self, **changed):
        held = self.ported()
        composed = {
            "control": self.control, "host": held["host"],
            "exclusion": held["exclusion"], "workspaces": self.staging,
            "writer": publication_worker.PublicationWriter(
                checkpoint1.CURRENT["identity"], clock=self.clock,
                workspace_of=self.workspace_of),
            # A DEPLOYMENT COMPOSES ONE SEAM AND HOLDS IT, so both custody
            # owners are present from the start even in the cases that stop
            # before custody -- which is also why `check_publication_seam`
            # requires them. Acts one and two never ask either of them
            # anything, and the cases that assert about custody use the ones
            # bound to the real publication attempt.
            "authority": getattr(self, "publication_port", None)
            or self.deployment_port(),
            "adapter": getattr(self, "custodian", None)
            or self.placeholder_custodian()}
        composed.update(changed)
        return publication_worker.PublicationSeam(**composed)

    def deployment_port(self):
        """The publication worker's own Worker Manager capability.

        Composed by `tools.integration_worker.authority_port`, which is this
        deployment's production composition over a real participant-bound
        Authority session.
        """
        from tools.integration_worker import authority_port

        if getattr(self, "_deployment_port", None) is None:
            self._deployment_port = authority_port(self.authority, PUBLISHER)
        return self._deployment_port

    def placeholder_custodian(self):
        """A custody adapter for the cases that never reach custody.

        NAMED AS A PLACEHOLDER AND ASSERTED NEVER TO BE ASKED ANYTHING: it
        exists so a seam is complete before a claim exists, which is what a
        deployment's own seam is. Every case that asserts about custody uses
        the adapter bound to the real publication attempt's own roots.
        """
        if getattr(self, "_placeholder", None) is None:
            self._placeholder = PublicationCustodian(
                self.roots, self.publication_declaration(),
                os.path.join(self.root, "unused-custody"))
        return self._placeholder

    # -- readers -----------------------------------------------------------

    @property
    def recovery_job_id(self):
        return publication_recovery.recovery_job_id("D1")

    def gate(self, job_id=None):
        return publication_execution.execution_gate(
            self.jobs, job_id or self.recovery_job_id)

    def review_offers(self):
        """How many review offers this control plane owes RIGHT NOW.

        Through `projection.owed_acts`, which is what the ordinary tick reads,
        so a case asserting zero is asserting about the thing that would
        issue one.
        """
        held = projection.stage_states(self.jobs, self.acts())
        owed = projection.owed_acts(self.jobs, self.acts(), held)
        review = documents.stage_id(self.recovery_job_id, "review")
        return [one for one in owed
                if one["stage_id"] == review and one["act"] == "admit"]

    def states(self):
        held = projection.stage_states(self.jobs, self.acts())
        return {one: held[one]["state"] for one in held}

    def acts(self):
        """THE REAL pooled manager operations over this case's own stores.

        `FakeOperations` stands in for the rest of the pipeline, which is
        exactly wrong for these cases: what they assert is that the ORDINARY
        projection reads this execution's real offer, real claim and real
        frozen output and reports the stage states that decide whether a
        review offer is owed. So the operations object is the product's own,
        composed over the real control store and the publication worker's own
        Authority capability.
        """
        from baton_v12.job_manager import ManagerOperations

        if getattr(self, "_acts", None) is None:
            self._acts = ManagerOperations(
                self.control, self.deployment_port(),
                mint_bearer=lambda: "projection-bearer",
                deliver_bearer=lambda issued: None)
        return self._acts

    def original_identity(self):
        found = os.stat(self.roots["workspace"], follow_symlinks=False)
        return f"{found.st_dev}:{found.st_ino}"

    def original_bytes(self):
        return workspaces.directory_manifest(
            self.roots["workspace"])["tree_digest"]


# -- 1. the admission that is real now ---------------------------------------


class TheApprovalNowReachesARealAdmission(PublicationExecutionCase):
    """The four capabilities checkpoint 1 could only name are installed."""

    def test_every_prerequisite_is_available_and_the_job_is_admitted(self):
        answer = self.approve_and_admit()
        self.assertEqual(answer["state"], "admitted")
        owed = {one["name"]: one for one in
                publication_recovery.prerequisites(
                    self.jobs, worker=self.ported()["binding"]
                    .publication_worker())}
        self.assertTrue(all(one["available"] for one in owed.values()), owed)
        self.assertEqual(self.jobs.schema_version,
                         publication_recovery.RECOVERY_STORE_GENERATION)
        self.assertEqual(answer["job_id"], self.recovery_job_id)
        self.assertEqual(answer["work_id"], WORK_A)
        self.assertEqual(answer["work"], {"work_id": WORK_A,
                                          "disposition": "reused",
                                          "status": "open"})

    def test_the_submitted_document_is_one_publication_and_one_review(self):
        self.approve_and_admit()
        rows = submission.stages_of(self.jobs, self.recovery_job_id)
        self.assertEqual([one["kind"] for one in rows],
                         list(documents.RECOVERY_STAGES))
        recorded = submission.submission_of(
            self.jobs, publication_recovery.recovery_submission_id("D1"))
        document = json.loads(recorded["document"])
        self.assertEqual(document["schema"],
                         documents.SUBMISSION_RECOVERY_SCHEMA)
        entry = document["jobs"][0]
        self.assertEqual(entry["control"],
                         {"profile": publication_recovery.PUBLICATION_PROFILE})
        publication, review = entry["stages"]
        self.assertEqual(publication["profile_name"], PUBLISHER_PROFILE)
        self.assertEqual(publication["profile_digest"], PUBLISHER_DIGEST)
        self.assertEqual(publication["depends_on"], [])
        self.assertEqual(review["depends_on"],
                         [{"job_id": self.recovery_job_id,
                           "kind": documents.PUBLICATION_STAGE}])
        # NO IMPLEMENTATION, NO VERIFICATION, NO INTEGRATION, by name.
        for kind in publication_recovery.FORBIDDEN_STAGES:
            self.assertNotIn(kind, [one["kind"] for one in entry["stages"]])

    def test_the_publication_stage_is_allocated_in_its_own_lane(self):
        self.approve_and_admit()
        rows = {one["kind"]: one for one in
                submission.stages_of(self.jobs, self.recovery_job_id)}
        self.assertEqual(
            scheduler.lane_of(rows[documents.PUBLICATION_STAGE]["kind"]),
            scheduler.PUBLICATION_LANE)
        self.assertEqual(scheduler.lane_of(rows["review"]["kind"]), "review")
        self.assertEqual(scheduler.POOL_SCHEMA,
                         publication_recovery.RECOVERY_POOL)

    def test_the_recovery_input_is_the_approved_original_and_not_the_task(self):
        answer = self.approve_and_admit()
        declaration = answer["input_declaration"]
        self.assertEqual(declaration["schema"],
                         publication_recovery.RECOVERY_INPUT_SCHEMA)
        self.assertEqual(declaration["tree_digest"],
                         self.original["tree_digest"])
        self.assertEqual(declaration["attempt_id"], self.attempt_id)
        self.assertEqual(declaration["candidate"], {"base": BASE,
                                                    "head": HEAD})
        self.assertEqual(declaration["delivery"], "read-only")
        self.assertFalse(declaration["producer"]["independent_acceptance"])
        self.assertEqual(declaration["producer"]["qualification"],
                         "producer-evidence")
        # THE RECOVERY INPUT DECLARATION HAS ITS OWN DIGEST, bound beside the
        # Job's submitted input rather than as it: the Job is submitted under
        # the INSTALLED PUBLICATION WORKER's own input manifest identity,
        # because that is what `delegation.stage_intent` carries into the
        # offer and what `check_binding` refuses an offer for disagreeing with.
        self.assertEqual(
            answer["recovery_input_digest"],
            publication_recovery.recovery_input_digest(declaration))
        self.assertEqual(answer["input_digest"],
                         self.publication_declaration()["manifest_digest"])
        self.assertNotEqual(answer["input_digest"],
                            answer["recovery_input_digest"])
        # AND IT IS NOT THE ORIGINAL JOB'S INPUT, which is the task the
        # producer was given rather than the output this publication reads.
        original = submission.job_of(self.jobs, self.job_id)
        self.assertNotEqual(answer["input_digest"], original["input_digest"])

    def test_the_admission_published_nothing_and_says_so(self):
        answer = self.approve_and_admit()
        self.assertEqual(answer["readiness"]["publication"], "queued")
        self.assertEqual(answer["readiness"]["review"], "blocked")
        self.assertEqual(answer["readiness"]["offers"], 0)
        self.assertIn("NOTHING HAS BEEN PUBLISHED",
                      answer["readiness"]["detail"])
        self.assertFalse(answer["gate"]["open"])
        self.assertIsNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])

    def test_an_exact_repeat_replays_and_admits_nothing_twice(self):
        first = self.approve_and_admit()
        second = self.admit()
        self.assertEqual(first, second)
        self.assertEqual(
            [one for one in self.jobs._connection.execute(
                "SELECT count(*) FROM jobs WHERE job_id = ?",
                (self.recovery_job_id,))][0][0], 1)


# -- 2. the prior assignment, ended, and the fresh claim ---------------------


class ThePriorAssignmentIsEndedThroughTheAuthority(PublicationExecutionCase):
    """The supported ending, and the fresh claim it makes possible.

    EVERY FACT HERE IS THE AUTHORITY'S OWN. The producer's claim, the release,
    the appended assignment events and the publication worker's new generation
    all come out of a real Authority store; nothing in this suite writes an
    assignment row or makes a Work available by hand.
    """

    def test_the_producer_holds_the_work_before_a_recovery_is_admitted(self):
        self.assertEqual(self.held_assignment["participant"], PRODUCER)
        self.assertEqual(
            self.authority.project_work(WORK_A)["handler"], PRODUCER)

    def test_the_admission_ends_exactly_that_assignment_and_queues_the_work(self):
        answer = self.approve_and_admit()
        ending = answer["ending"]
        self.assertEqual(ending["disposition"], "ended")
        self.assertEqual(ending["expect"]["participant"], PRODUCER)
        self.assertEqual(ending["expect"]["generation"],
                         self.held_assignment["generation"])
        self.assertEqual(ending["answer"]["cause"],
                         publication_recovery.ENDING_DISPOSITION)
        self.assertEqual(ending["answer"]["phase"], "queued")
        self.assertIsNone(self.authority.assignment_of(WORK_A))
        self.assertEqual(
            self.authority.project_work(WORK_A)["status"], "open")
        # AND THE EARLIER EVENTS ARE PRESERVED: the claim and the release are
        # both in the Authority's own append-only history.
        causes = [one["cause"] for one in
                  self.authority.assignment_events(WORK_A)]
        self.assertEqual(causes[-1], publication_recovery.ENDING_DISPOSITION)
        self.assertIn("claimed", causes)

    def test_missing_held_session_does_not_mint_authority(self):
        from tools.publication_ports import PriorAssignment
        from unittest.mock import patch
        port = PriorAssignment(self.authority, checkpoint1.CURRENT["identity"])
        with patch.object(self.authority, "session", side_effect=AssertionError("must not mint")):
            caught = self.refusal(port.end, self.held_assignment,
                                  operation_id="missing-held-session")
        self.assertEqual(caught.code, "capability")
        self.assertEqual(self.authority.assignment_of(WORK_A), self.held_assignment)

    def test_the_ending_is_journalled_once_and_replays(self):
        self.approve_and_admit()
        held = publication_recovery.ending_of(self.jobs, "D1")
        self.assertEqual(held["disposition"], "ended")
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (publication_recovery.ENDING_KIND,)).fetchone()[0], 1)
        # A REPLAY OF THE WHOLE ADMISSION ENDS NOTHING A SECOND TIME.
        self.admit()
        self.assertEqual(
            len([one for one in self.authority.assignment_events(WORK_A)
                 if one["cause"] == publication_recovery.ENDING_DISPOSITION]),
            1)

    def test_an_assignment_another_handler_holds_is_reported_and_not_taken(self):
        """NO TAKEOVER POWER WAS SELECTED AND NONE IS USED.

        The Work is passed to a third participant, so the live assignment is
        no longer the failed execution's. The admission must report the exact
        held assignment and stop BEFORE any publication effect.
        """
        self.authority.bind_endpoint("baton.other", "principal:other")
        self.authority.add_route_handler(ROUTE, "baton.other")
        self.producer_session.end({"expect": self.held_assignment,
                                   "operation_id": "producer-hands-back"})
        other = self.authority.session("baton.other")
        other.claim({"work_id": WORK_A, "operation_id": "claim-other"})
        self.approved()
        caught = self.refusal(self.admit)
        self.assertIn("another handler owns this Work", caught.message)
        self.assertIn("baton.other", caught.message)
        self.assertIsNone(publication_recovery.ending_of(self.jobs, "D1"))
        self.assertIsNone(publication_recovery.admission_of(self.jobs, "D1"))
        self.assertEqual(
            self.authority.assignment_of(WORK_A)["participant"],
            "baton.other")

    def test_an_already_released_work_has_nothing_to_end(self):
        self.producer_session.end({"expect": self.held_assignment,
                                   "operation_id": "producer-hands-back"})
        answer = self.approve_and_admit()
        self.assertEqual(answer["ending"]["disposition"], "none")
        self.assertIsNone(answer["ending"]["answer"])
        self.assertEqual(answer["state"], "admitted")

    def test_an_uncertain_host_refuses_the_ending_before_it_happens(self):
        """A HOST-ONLY STOPPED SETTLEMENT DOES NOT RELEASE AN AUTHORITY CLAIM,
        and an uncertain one does not either. The attempt's runtime is reported
        `running`, so cessation is not positive and the assignment stays."""
        self.approved()
        self.ports()["exclusion"].answer = {
            "runtime": {"attempt_id": None, "runtime_id": "runtime-1",
                        "execution_runtime": "running", "cleanup": "pending",
                        "assignment": None},
            "token": {"returned": False}}
        caught = self.refusal(self.admit)
        self.assertIn("quiescence-unknown", f"{caught.category}/{caught.code}")
        self.assertIsNone(publication_recovery.ending_of(self.jobs, "D1"))
        self.assertEqual(
            self.authority.assignment_of(WORK_A)["participant"], PRODUCER)

    def test_a_deployment_with_no_session_for_the_holder_cannot_end_it(self):
        """AND IT CANNOT IMPERSONATE ONE. The ending adapter asks the
        deployment for the session of the participant the Authority reports as
        the holder; a deployment that answers somebody else's is refused by the
        adapter rather than allowed to end a claim it does not hold."""
        self.approved()
        wrong = self.authority.session(OWNER)
        caught = self.refusal(
            self.admit, ending=self.ending_port(sessions=lambda who: wrong))
        self.assertIn("does not impersonate", caught.message)
        self.assertEqual(
            self.authority.assignment_of(WORK_A)["participant"], PRODUCER)

    def test_the_publication_worker_claims_a_fresh_generation(self):
        self.approve_and_admit()
        held = self.claim_publication()
        self.assertEqual(held["assignment"]["participant"], PUBLISHER)
        self.assertNotEqual(held["assignment"]["generation"],
                            self.held_assignment["generation"])
        fresh = publication_execution.fresh_assignment_of(
            self.jobs, self.control,
            publication_recovery.admission_of(self.jobs, "D1"))
        self.assertEqual(fresh["participant"], PUBLISHER)
        self.assertEqual(fresh["attempt_id"], held["attempt_id"])
        self.assertNotEqual(fresh["attempt_id"], self.attempt_id)
        self.assertEqual(fresh["work_id"], WORK_A)


# -- 3. act one: the read-only staging ---------------------------------------


class TheApprovedOriginalIsStagedReadOnly(PublicationExecutionCase):
    """ONE no-follow copy out of the original, and the original is untouched."""

    def test_the_staged_copy_is_the_approved_bytes_and_is_read_only(self):
        self.ready()
        before = self.original_bytes()
        held = self.staged()
        self.assertEqual(held["staged"]["tree_digest"],
                         self.original["tree_digest"])
        self.assertEqual(held["original"]["tree_digest"],
                         self.original["tree_digest"])
        self.assertFalse(held["original"]["mutated"])
        self.assertEqual(held["delivery"], "read-only")
        place = held["staged"]["locator"][len("file://"):]
        self.assertEqual(
            workspaces.directory_manifest(place)["tree_digest"],
            self.original["tree_digest"])
        # THE MODE SAYS IT ON DISK, both halves: unlink and rename are
        # permissions of the DIRECTORY, so a read-only file in a writable one
        # is not protected.
        self.assertEqual(os.stat(place).st_mode & 0o777, 0o555)
        self.assertEqual(
            os.stat(os.path.dirname(place)).st_mode & 0o777, 0o555)
        entry = os.path.join(place, role_contract.CANDIDATE_OUTPUT,
                             "result.json")
        self.assertEqual(os.stat(entry).st_mode & 0o777, 0o444)
        with self.assertRaises(PermissionError):
            open(entry, "wb")
        # AND THE ORIGINAL IS BYTE-IDENTICAL AFTERWARDS.
        self.assertEqual(self.original_bytes(), before)
        self.assertFalse(os.path.exists(os.path.join(
            self.roots["workspace"], "output.json")))

    def test_the_staged_manifest_binds_the_original_and_the_decision(self):
        self.ready()
        held = self.staged()
        self.assertEqual(held["original"]["attempt_id"], self.attempt_id)
        self.assertEqual(held["decision_id"], "D1")
        self.assertEqual(held["prior_job_id"], self.job_id)
        self.assertEqual(held["attempt_id"], self.publication_attempt)
        self.assertEqual(
            held["input_digest"],
            publication_recovery.admission_of(self.jobs, "D1")["input_digest"])
        self.assertTrue(held["cessation"]["ceased"])
        self.assertEqual(held["original"]["root_identity"],
                         self.original_identity())

    def test_the_provenance_is_separate_bounded_and_outside_the_proposal(self):
        self.ready()
        held = self.staged()
        self.assertNotEqual(held["provenance"]["locator"],
                            held["staged"]["locator"])
        self.assertEqual(held["provenance"]["entry_count"], 1)
        self.assertLessEqual(held["provenance"]["total_bytes"],
                             publication_recovery.PROVENANCE["max_bytes"])
        document = held["provenance"]["document"]
        self.assertEqual(document["schema"],
                         publication_execution.PROVENANCE_SCHEMA)
        self.assertEqual(document["producer"]["participant"], PRODUCER)
        self.assertEqual(document["publisher"]["participant"], PUBLISHER)
        self.assertEqual(document["publisher"]["provider_invocations"], 0)
        self.assertEqual(document["publisher"]["verifier_invocations"], 0)
        self.assertFalse(
            document["producer"]["verification"]["independent_acceptance"])
        self.assertIn("owed", document["reviewer"][
            "independent_verification"])
        # AND IT IS NOT IN THE STAGED PROPOSAL TREE, which is the whole point.
        staged = held["staged"]["locator"][len("file://"):]
        self.assertNotIn(publication_execution.PROVENANCE_FILE,
                         os.listdir(os.path.join(
                             staged, role_contract.CANDIDATE_OUTPUT)))

    def test_staging_replays_and_copies_once(self):
        self.ready()
        first = self.staged()
        second = self.staged()
        self.assertEqual(first, second)
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (publication_execution.STAGING_KIND,)).fetchone()[0], 1)

    def test_nothing_is_staged_before_a_fresh_claim_exists(self):
        self.approve_and_admit()
        caught = self.refusal(self.staged)
        self.assertIn("holds no claimed execution", caught.message)
        self.assertIn("nobody claimed", caught.message)
        self.assertIsNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))

    def test_nothing_is_staged_before_the_stage_durably_starts(self):
        """QUEUE TIME IS CHARGED TO THE JOB, not to this stage: a copy made
        before the stage's own execution admission would be work charged to a
        clock that has not started."""
        self.approve_and_admit()
        self.claim_publication()
        caught = self.refusal(self.staged)
        self.assertIn("no persisted execution admission", caught.message)

    def test_a_missing_original_holds_and_stages_nothing(self):
        import shutil

        self.ready()
        shutil.rmtree(os.path.join(self.roots["workspace"],
                                   role_contract.CANDIDATE_OUTPUT))
        caught = self.refusal(self.staged)
        self.assertEqual(caught.category, "integrity")
        self.assertIsNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))

    def test_a_substituted_original_root_refuses_as_a_substitution(self):
        """THE OBJECT IDENTITY IS WHAT DECIDES, not the path. The workspace is
        moved aside and an identical tree is put at the same name, so every
        byte matches and the `device:inode` the preparation recorded does
        not."""
        import shutil

        self.ready()
        place = self.roots["workspace"]
        shutil.move(place, place + ".aside")
        shutil.copytree(place + ".aside", place)
        caught = self.refusal(self.staged)
        self.assertEqual(caught.code, "identity-mismatch")
        self.assertIn("replaced object", caught.message)

    def test_a_tampered_original_refuses_before_anything_is_staged(self):
        self.ready()
        with open(os.path.join(self.roots["workspace"],
                               role_contract.CANDIDATE_OUTPUT,
                               "change.patch"), "ab") as handle:
            handle.write(b"tampered\n")
        caught = self.refusal(self.staged)
        self.assertEqual(caught.code, "digest")
        self.assertIn("bytes that moved under an owner decision",
                      caught.message)
        self.assertIsNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))

    def test_an_uncertain_writer_holds_the_staging(self):
        self.ready()
        self.ports()["exclusion"].answer = {
            "runtime": {"attempt_id": None, "runtime_id": "runtime-1",
                        "execution_runtime": "running", "cleanup": "pending",
                        "assignment": None},
            "token": {"returned": False}}
        caught = self.refusal(self.staged)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIn("an uncertain writer is a writer", caught.message)


# -- 4. act two: the deterministic adoption ----------------------------------


class TheRetainedBytesAreAdoptedDeterministically(PublicationExecutionCase):
    """ONE copy, the exact bytes, zero models and zero verifier commands."""

    def test_the_adopted_proposal_is_the_approved_original_byte_for_byte(self):
        self.ready()
        self.staged()
        held = self.published_once()
        self.assertEqual(held["outcome"], "published")
        self.assertEqual(held["adopted"]["tree_digest"],
                         self.original["tree_digest"])
        self.assertEqual(held["adopted"]["total_bytes"],
                         self.original["total_bytes"])
        self.assertTrue(held["adopted"]["equals_original"])
        self.assertEqual(held["attempt_id"], self.publication_attempt)
        self.assertEqual(held["assignment"]["participant"], PUBLISHER)
        # MEASURED OFF THE ATTEMPT'S OWN OUTPUT ROOT, by this manager.
        place = os.path.join(self.workspace_of(self.publication_attempt),
                             role_contract.CANDIDATE_OUTPUT)
        self.assertEqual(
            workspaces.directory_manifest(place)["tree_digest"],
            self.original["tree_digest"])
        # AND THE ORIGINAL IS UNCHANGED.
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])

    def test_zero_providers_and_zero_verifier_commands_are_counted(self):
        self.ready()
        self.staged()
        held = self.published_once()
        self.assertEqual(held["invocations"],
                         {"provider": 0, "verifier": 0, "commands": 0})
        # AND THE REQUEST CARRIED NOTHING THAT COULD INVOKE EITHER. The
        # adapter refuses a request naming a command, a credential or a
        # provider, which is asserted by driving one at it.
        writer = publication_worker.PublicationWriter(
            checkpoint1.CURRENT["identity"], clock=self.clock,
            workspace_of=self.workspace_of)
        caught = self.refusal(
            writer.adopt,
            {"attempt_id": self.publication_attempt, "assignment": {},
             "staged": {}, "provenance": {}, "outputs": {}, "deadline": {},
             "argv": ["python3", "-m", "unittest"]})
        self.assertEqual(caught.category, "policy")
        self.assertIn("runs no command", caught.message)

    def test_the_provenance_is_a_separate_output_that_changes_no_digest(self):
        self.ready()
        self.staged()
        held = self.published_once()
        self.assertEqual(held["provenance"]["name"],
                         publication_recovery.PROVENANCE["name"])
        self.assertEqual(held["provenance"]["entry_count"], 1)
        self.assertFalse(held["provenance"]["alters_proposal_tree"])
        self.assertNotEqual(held["provenance"]["tree_digest"],
                            held["adopted"]["tree_digest"])
        place = self.workspace_of(self.publication_attempt)
        held = os.listdir(place)
        for name in (role_contract.CANDIDATE_OUTPUT,
                     publication_recovery.PROVENANCE_PATH, "output.json"):
            self.assertIn(name, held)
        # AND THE RECOVERY'S ACCOUNT IS NOWHERE INSIDE THE PROPOSAL TREE,
        # which is what "it never alters the original proposal tree digest"
        # means on disk.
        inside = []
        for base, _directories, files in os.walk(
                os.path.join(place, role_contract.CANDIDATE_OUTPUT)):
            inside.extend(files)
        self.assertNotIn(publication_execution.PROVENANCE_FILE, inside)

    def test_the_completion_envelope_is_the_worker_contracts_own(self):
        from baton_v12.contracts import check_manifest_structure

        self.ready()
        self.staged()
        self.published_once()
        with open(os.path.join(self.workspace_of(self.publication_attempt),
                               "output.json"), "rb") as handle:
            document = json.loads(handle.read().decode("utf-8"))
        owned = check_manifest_structure(document, "completionManifest",
                                         what="the published envelope")
        self.assertEqual(owned["disposition"], "completed")
        self.assertEqual(owned["assignment_ref"]["participant"], PUBLISHER)
        self.assertEqual(
            sorted(one["name"] for one in owned["outputs"]),
            sorted([role_contract.CANDIDATE_OUTPUT,
                    publication_recovery.PROVENANCE["name"]]))

    def test_the_adoption_replays_and_publishes_once(self):
        self.ready()
        self.staged()
        first = self.published_once()
        second = self.published_once()
        self.assertEqual(first, second)
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (publication_execution.RESULT_KIND,)).fetchone()[0], 1)

    def test_nothing_is_adopted_before_the_original_is_staged(self):
        self.ready()
        caught = self.refusal(self.published_once)
        self.assertIn("staged no approved original", caught.message)
        self.assertIsNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))

    def test_a_writer_that_wrote_other_bytes_is_refused_after_the_fact(self):
        """A WRITER'S ANSWER DOES NOT MAKE OTHER BYTES THE APPROVED ONES.

        The staged tree is tampered with between the staging and the adoption,
        so the writer faithfully copies what is there and this manager's own
        measurement refuses it.
        """
        self.ready()
        held = self.staged()
        root = held["staged"]["locator"][len("file://"):]
        place = os.path.join(root, role_contract.CANDIDATE_OUTPUT)
        # THE STAGED TREE REALLY IS READ-ONLY, so tampering with it needs the
        # modes relaxed first -- which is itself the assertion that the
        # delivery is read-only rather than merely called that.
        with self.assertRaises(PermissionError):
            open(os.path.join(place, "result.json"), "ab")
        os.chmod(root, 0o700)
        os.chmod(place, 0o700)
        os.chmod(os.path.join(place, "result.json"), 0o600)
        with open(os.path.join(place, "result.json"), "ab") as handle:
            handle.write(b"x")
        caught = self.refusal(self.published_once)
        self.assertEqual(caught.code, "digest")
        self.assertIn("publishes the exact retained bytes", caught.message)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        # THE INTENT IS DURABLE, which is what makes this a reconcilable cut
        # rather than a silent nothing.
        self.assertIsNotNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))


# -- 5. act three: normal completion, custody and intake ---------------------


class ThePublishedCandidateEntersOrdinaryCustody(PublicationExecutionCase):
    """The Worker Manager's own freeze and intake, over real sealed files."""

    def test_the_frozen_candidate_is_the_approved_original_in_custody(self):
        self.ready()
        self.staged()
        self.published_once()
        self.quiescent()
        held = self.collected()
        self.assertEqual(held["frozen"]["disposition"], "completed")
        self.assertEqual(held["adopted"]["content_digest"],
                         self.original["tree_digest"])
        self.assertTrue(held["adopted"]["equals_original"])
        self.assertIn(role_contract.CANDIDATE_OUTPUT, held["artifacts"])
        self.assertIn(publication_recovery.PROVENANCE["name"],
                      held["artifacts"])
        self.assertIsNotNone(held["intake"]["result_id"])
        self.assertEqual(held["intake"]["result_id"],
                         held["frozen"]["result_id"])
        self.assertEqual(sorted(held["intake"]["artifacts"]),
                         sorted(one["artifact_id"] for one in
                                self.collected()["intake"]["artifacts"]
                                if isinstance(one, dict)) or
                         held["intake"]["artifacts"])
        self.assertFalse(held["provenance"]["alters_proposal_tree"])
        self.assertNotEqual(held["provenance"]["content_digest"],
                            held["adopted"]["content_digest"])

    def test_the_custody_record_replays_and_freezes_once(self):
        self.ready()
        self.staged()
        self.published_once()
        self.quiescent()
        first = self.collected()
        second = self.collected()
        self.assertEqual(first, second)
        self.assertEqual(len(self.custodian.seals), 1)

    def test_a_runtime_nobody_says_stopped_is_not_frozen(self):
        """`output._provable`'s rule, unchanged for this lane: a freeze
        describes a tree the writer has stopped changing, and only a positive
        quiescent observation says that."""
        self.ready()
        self.staged()
        self.published_once()
        caught = self.refusal(self.collected)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIsNone(publication_execution.custody_of(
            self.jobs, self.recovery_job_id))

    def test_nothing_is_collected_before_anything_is_adopted(self):
        self.ready()
        self.staged()
        caught = self.refusal(self.collected)
        self.assertIn("adopted nothing", caught.message)


# -- 6. act four: the one record that opens review ---------------------------


class TheReviewGateOpensOnTheHandoffAndOnNothingWeaker(
        PublicationExecutionCase):
    """ZERO review offers in every incomplete state, and exactly one after."""

    def test_the_gate_is_shut_at_every_step_before_the_handoff(self):
        self.approve_and_admit()
        steps = []
        steps.append(("admitted", self.gate()))
        self.claim_publication()
        self.admit_stage()
        steps.append(("claimed", self.gate()))
        self.staged()
        steps.append(("staged", self.gate()))
        self.published_once()
        steps.append(("published", self.gate()))
        self.quiescent()
        self.collected()
        steps.append(("custody", self.gate()))
        for where, gate in steps:
            with self.subTest(where=where):
                self.assertFalse(gate["open"], where)
                self.assertFalse(gate["runnable"], where)
                self.assertEqual(gate["reason"],
                                 publication_execution.GATE_UNAVAILABLE)
                self.assertEqual(self.review_offers(), [], where)
        # AND THE BINDINGS SAY WHICH ONE IS MISSING at the last step.
        missing = [one["name"] for one in steps[-1][1]["bindings"]
                   if not one["present"]]
        self.assertEqual(missing, ["reviewer-servability"])

    def test_the_handoff_opens_the_gate_and_earns_exactly_one_review_offer(self):
        held = self.whole_path()
        self.assertEqual(held["review_stage_id"],
                         publication_recovery.review_stage_id("D1"))
        self.assertEqual(held["publication_attempt_id"],
                         self.publication_attempt)
        self.assertEqual(held["failed_attempt_id"], self.attempt_id)
        self.assertEqual(held["candidate"]["head"], HEAD)
        self.assertEqual(held["candidate"]["content_digest"],
                         self.original["tree_digest"])
        self.assertTrue(held["candidate"]["equals_approved_original"])
        self.assertFalse(held["output"]["original_mutated"])
        gate = self.gate()
        self.assertTrue(gate["open"])
        self.assertTrue(gate["runnable"])
        self.assertEqual(gate["reason"], publication_execution.GATE_VALIDATED)
        self.assertTrue(all(one["present"] for one in gate["bindings"]))
        self.assertEqual(len(self.review_offers()), 1)
        states = self.states()
        self.assertEqual(states[publication_recovery.review_stage_id("D1")],
                         "queued")

    def test_the_handoff_names_what_the_reviewer_still_owes(self):
        held = self.whole_path()
        reviewer = held["reviewer"]
        self.assertEqual(reviewer["producer_stage_kind"],
                         documents.PUBLICATION_STAGE)
        self.assertEqual(reviewer["producer_stage_id"],
                         documents.stage_id(self.recovery_job_id,
                                            documents.PUBLICATION_STAGE))
        self.assertEqual(reviewer["invocation_seconds"], 3600)
        self.assertEqual(reviewer["each_command_seconds"], 900)
        self.assertIn("owed", reviewer["independent_verification"])
        self.assertIn("never acceptance", reviewer["producer_evidence"])
        # BOTH PRODUCERS ARE EXCLUDED, which is "a new Job must not erase the
        # original producer exclusion".
        self.assertIn(PRODUCER, reviewer["excluded_participants"])
        self.assertIn(PUBLISHER, reviewer["excluded_participants"])

    def test_no_verdict_is_written_anywhere_on_this_path(self):
        self.whole_path()
        for axis in ("technical_review", "approval", "verification"):
            held = self.control._connection.execute(
                f"SELECT {axis} FROM attempts WHERE runtime_attempt_id = ?",
                (self.publication_attempt,)).fetchone()[0]
            self.assertEqual(held, "none")

    def test_the_handoff_replays_and_opens_one_gate(self):
        first = self.whole_path()
        second = self.handed_off()
        self.assertEqual(first, second)
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (publication_execution.HANDOFF_KIND,)).fetchone()[0], 1)

    def test_an_ordinary_job_has_no_publication_gate_at_all(self):
        self.assertIsNone(publication_execution.execution_gate(
            self.jobs, self.job_id))
        held = projection.stage_states(self.jobs, self.acts())
        self.assertIsNone(held[self.stage_id]["publication_gate"])


# -- 7. the absolute publication bound ---------------------------------------


class TheNineHundredSecondBoundIsAbsoluteAndEnforcedTwice(
        PublicationExecutionCase):
    """FROM THE PERSISTED STAGE ADMISSION, and never a restart-reset timer."""

    def test_the_bound_is_derived_from_the_persisted_stage_admission(self):
        self.ready()
        held = publication_execution.deadline_of(self.jobs, "D1", now=PUBLISHED)
        self.assertEqual(held["seconds"], 900)
        self.assertEqual(held["profile"],
                         publication_recovery.PUBLICATION_PROFILE)
        self.assertEqual(held["origin"], CLAIMED)
        self.assertIn("persisted stage execution admission",
                      held["origin_is"])
        self.assertFalse(held["restart_resets"])
        self.assertFalse(held["reached"])
        # AND IT IS THE NARROWEST OF THE THREE, with the other two beside it.
        self.assertLess(held["deadline_at"], held["stage_deadline_at"])
        self.assertLess(held["deadline_at"], held["job_deadline_at"])
        self.assertEqual(held["enforced_deadline_at"], held["deadline_at"])
        self.assertEqual(held["remaining_seconds"], 840)

    def test_the_bound_is_the_one_the_control_owner_enforces(self):
        """THE HOST'S OWN ENFORCEMENT, not a second account of it. The stage
        view the control evaluation derives carries the sub-bound, and the
        stage deadline it fences on is the EARLIEST of the two."""
        self.ready()
        held = job_control.evaluate(self.jobs._connection,
                                    self.recovery_job_id, PUBLISHED)
        view = [one for one in held["stages"]
                if one["stage_id"] == documents.stage_id(
                    self.recovery_job_id, documents.PUBLICATION_STAGE)][0]
        self.assertEqual(view["sub_bound"]["seconds"], 900)
        self.assertEqual(view["sub_bound"]["origin"], CLAIMED)
        self.assertFalse(view["sub_bound"]["restart_resets"])
        self.assertEqual(view["deadline_at"],
                         view["sub_bound"]["deadline_at"])
        # AND NO OTHER PROFILE BOUNDS ANY STAGE KIND FURTHER, which is what
        # keeps every ordinary Job's stage wall exactly what it has always
        # been.
        for profile in sorted(job_control.PROFILES):
            for kind in documents.STAGE_KINDS:
                found = job_control.sub_bound_of(profile, kind)
                if profile == publication_recovery.PUBLICATION_PROFILE \
                        and kind == documents.PUBLICATION_STAGE:
                    self.assertEqual(found, 900)
                else:
                    self.assertIsNone(found, (profile, kind))

    def test_a_restart_re_derives_the_same_instant_and_not_a_fresh_budget(self):
        """THE ONE PROPERTY THE CONTRACT STATES TWICE. A second incarnation
        opens the same store, derives the same absolute instant, and is handed
        what is LEFT of it rather than another 900 seconds."""
        from baton_v12.job_manager import JobStore

        self.ready()
        first = publication_execution.deadline_of(self.jobs, "D1",
                                                  now=PUBLISHED)
        self.instants.append("2026-09-02T00:23:00.000Z")
        reopened = JobStore.open(self.jobs.database, authority_uuid=AUTHORITY,
                                 incarnation="publication-2",
                                 clock=self.clock)
        self.addCleanup(reopened.close)
        second = publication_execution.deadline_of(
            reopened, "D1", now="2026-09-02T00:23:00.000Z")
        self.assertEqual(second["deadline_at"], first["deadline_at"])
        self.assertEqual(second["origin"], first["origin"])
        self.assertEqual(first["remaining_seconds"], 840)
        self.assertEqual(second["remaining_seconds"], 180)

    def test_a_reached_bound_starts_no_new_effect_and_proves_no_cessation(self):
        self.ready()
        caught = self.refusal(self.staged, now=LATE)
        self.assertEqual(caught.category, "policy")
        self.assertIn("900-second bound", caught.message)
        self.assertIn("not evidence that anything ceased", caught.message)
        self.assertIsNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))
        # AND THE HOST'S OWN FENCE IS WHAT CLOSES THE JOB, derived from the
        # same durable origin rather than from this refusal.
        closed = job_control.closed_of(self.jobs, self.recovery_job_id,
                                       LATE, any_stage=True)
        self.assertEqual(closed["cause"], "deadline")
        self.assertEqual(closed["first"]["stage_id"],
                         documents.stage_id(self.recovery_job_id,
                                            documents.PUBLICATION_STAGE))

    def test_the_writer_is_handed_the_absolute_instant_and_stops_at_it(self):
        """THE WORKER'S OWN ENFORCEMENT, at its own boundary. The adapter is
        handed the absolute instant and recomputes the remainder against this
        host's clock on every check -- so a clock that has passed the wall
        stops it, and it answers `unknown` with `timed_out` rather than
        anything a publication could be read out of."""
        self.ready()
        self.staged()
        writer = publication_worker.PublicationWriter(
            checkpoint1.CURRENT["identity"], clock=lambda: LATE,
            workspace_of=self.workspace_of)
        held = publication_execution.staging_of(self.jobs,
                                                self.recovery_job_id)
        admitted = publication_recovery.admission_of(self.jobs, "D1")
        answer = writer.adopt({
            "attempt_id": self.publication_attempt,
            "assignment": {"work_ref": {"authority_uuid": AUTHORITY,
                                        "work_id": WORK_A},
                           "participant": PUBLISHER, "generation": 2},
            "staged": held["staged"], "provenance": held["provenance"],
            "outputs": {"candidate": publication_recovery
                        .corrective_declaration()["output"],
                        "provenance":
                            publication_recovery.PROVENANCE_OUTPUT},
            "deadline": {"deadline_at": "2026-09-02T00:26:00.000Z",
                         "remaining_seconds": 900, "origin": CLAIMED,
                         "restart_resets": False},
            "input_digest": admitted["input_digest"]})
        self.assertEqual(answer["outcome"], "unknown")
        self.assertTrue(answer["timed_out"])
        self.assertEqual(answer["provider_invocations"], 0)
        self.assertNotIn("manifest", answer)
        # AND NOTHING WAS WRITTEN, so a ceiling that stopped the work cannot
        # read as a publication.
        self.assertFalse(os.path.exists(os.path.join(
            self.workspace_of(self.publication_attempt), "output.json")))


class LostWriter:
    """A deterministic writer that does not answer, or answers `unknown`."""

    def __init__(self, identity, *, outcome=None, raises=None, clock=None):
        self._identity = identity
        self._outcome = outcome
        self._raises = raises
        self._clock = clock or (lambda: PUBLISHED)
        self.calls = []

    def instance(self):
        return self._identity

    def adopt(self, request):
        self.calls.append(request)
        if self._raises is not None:
            raise self._raises
        return {"outcome": self._outcome, "provider_invocations": 0,
                "verifier_invocations": 0, "started_at": self._clock(),
                "ended_at": self._clock(), "timed_out": False}


# -- 8. uncertainty, lost replies and the restart cuts -----------------------


class UncertaintyHoldsAndNeverPublishesTwice(PublicationExecutionCase):
    """A lost or unanswered adoption is reconciled, not retried."""

    def test_overlapping_publication_cannot_invoke_another_writer(self):
        self.ready()
        self.staged()
        outer = self
        class ReentrantWriter(LostWriter):
            def adopt(self, request):
                self.calls.append(request)
                caught = outer.refusal(outer.published_once, writer=self)
                outer.assertEqual(caught.code, "quiescence-unknown")
                raise OSError("lost answer")
        writer = ReentrantWriter(checkpoint1.CURRENT["identity"])
        self.refusal(self.published_once, writer=writer)
        self.assertEqual(len(writer.calls), 1)

    def test_interrupted_staging_bytes_are_preserved_on_retry(self):
        from pathlib import Path
        from unittest.mock import patch
        self.ready()
        def interrupted(source, destination, **limits):
            Path(destination, "partial-evidence").write_bytes(b"retained partial bytes")
            raise OSError("copy interrupted")
        with patch.object(publication_execution, "copied_manifest", interrupted):
            with self.assertRaises(OSError):
                self.staged()
        staged = self.staged()
        retained = list(Path(self.staging).rglob("partial-evidence"))
        self.assertEqual(len(retained), 1)
        self.assertEqual(retained[0].read_bytes(), b"retained partial bytes")
        self.assertIn("interrupted-", str(retained[0]))
        self.assertEqual(staged["staged"]["tree_digest"], self.original["tree_digest"])

    def test_overlapping_stager_cannot_replace_input_before_commit(self):
        from unittest.mock import patch
        self.ready()
        copy_original = publication_execution.copied_manifest
        calls = []
        def competing_copy(*args, **kwargs):
            calls.append(args)
            caught = self.refusal(self.staged)
            self.assertEqual(caught.code, "quiescence-unknown")
            return copy_original(*args, **kwargs)
        with patch.object(publication_execution, "copied_manifest", competing_copy):
            staged = self.staged()
        self.assertEqual(len(calls), 1)
        self.assertEqual(self.staged(), staged)
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])

    def test_process_loss_after_intent_never_repeats_the_writer(self):
        self.ready()
        self.staged()
        lost = LostWriter(checkpoint1.CURRENT["identity"],
                          raises=KeyboardInterrupt("process stopped"))
        with self.assertRaises(KeyboardInterrupt):
            self.published_once(writer=lost)
        self.assertIsNotNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNone(publication_execution.hold_of(
            self.jobs, self.recovery_job_id))
        again = self.refusal(self.published_once, writer=lost)
        self.assertEqual(again.code, "quiescence-unknown")
        self.assertEqual(len(lost.calls), 1)
        readiness = publication_execution.publication_readiness(
            self.jobs, "D1")
        self.assertTrue(readiness["uncertain"])
        self.assertIsNone(readiness["owed"])

    def test_a_lost_reply_is_journalled_as_uncertain_and_holds(self):
        self.ready()
        self.staged()
        lost = LostWriter(checkpoint1.CURRENT["identity"],
                          raises=OSError("connection lost"))
        caught = self.refusal(self.published_once, writer=lost)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIn("UNCERTAIN", caught.message)
        self.assertEqual(len(lost.calls), 1)
        # THE INTENT IS DURABLE AND SO IS THE UNCERTAINTY.
        self.assertIsNotNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))
        held = publication_execution.hold_of(self.jobs, self.recovery_job_id)
        self.assertEqual(held["outcome"], "unknown")
        self.assertEqual(held["attempt_id"], self.publication_attempt)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))

    def test_no_second_adoption_is_started_while_the_first_is_unaccounted(self):
        self.ready()
        self.staged()
        lost = LostWriter(checkpoint1.CURRENT["identity"],
                          raises=OSError("connection lost"))
        self.refusal(self.published_once, writer=lost)
        # A SECOND PASS, WITH A PERFECTLY GOOD WRITER, STILL REFUSES.
        again = self.refusal(self.published_once)
        self.assertEqual(again.code, "quiescence-unknown")
        self.assertIn("No second adoption is started", again.message)
        self.assertEqual(len(lost.calls), 1)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        # AND THE EVIDENCE IS RETAINED: the staged input and the original are
        # both exactly as they were.
        self.assertIsNotNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])

    def test_a_writer_that_cannot_say_it_finished_holds(self):
        self.ready()
        self.staged()
        unknown = LostWriter(checkpoint1.CURRENT["identity"],
                             outcome="unknown")
        caught = self.refusal(self.published_once, writer=unknown)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIn("answers 'unknown'", caught.message)
        self.assertEqual(
            publication_execution.hold_of(
                self.jobs, self.recovery_job_id)["observed"],
            "the writer answered unknown")

    def test_an_uncertain_adoption_opens_no_gate_and_offers_no_review(self):
        self.ready()
        self.staged()
        self.refusal(self.published_once,
                     writer=LostWriter(checkpoint1.CURRENT["identity"],
                                       outcome="unknown"))
        gate = self.gate()
        self.assertFalse(gate["open"])
        self.assertEqual(self.review_offers(), [])
        held = publication_execution.publication_readiness(self.jobs, "D1")
        self.assertTrue(held["uncertain"])
        self.assertIsNone(held["owed"])
        self.assertEqual(held["review"], "blocked")

    def test_a_writer_that_claims_a_model_or_a_verifier_is_denied(self):
        self.ready()
        self.staged()

        class Lying(LostWriter):
            def adopt(self, request):
                return {"outcome": "published", "provider_invocations": 1,
                        "verifier_invocations": 0, "started_at": PUBLISHED,
                        "ended_at": PUBLISHED}

        caught = self.refusal(
            self.published_once,
            writer=Lying(checkpoint1.CURRENT["identity"]))
        self.assertEqual(caught.category, "policy")
        self.assertIn("ZERO models", caught.message)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))

    def test_every_act_replays_across_a_restart_without_a_second_effect(self):
        """THE WHOLE PATH, RE-ENTERED ON A SECOND INCARNATION. Each act finds
        its own committed record and answers with it, so nothing is staged,
        published, frozen or handed off twice."""
        from baton_v12.job_manager import JobStore

        first = self.whole_path()
        reopened = JobStore.open(self.jobs.database, authority_uuid=AUTHORITY,
                                 incarnation="publication-restart",
                                 clock=self.clock)
        self.addCleanup(reopened.close)
        seam = self.seam()
        for act, held in (
                (publication_execution.stage_input,
                 publication_execution.STAGING_KIND),
                (publication_execution.publish,
                 publication_execution.RESULT_KIND),
                (publication_execution.take_custody,
                 publication_execution.CUSTODY_KIND),
                (publication_execution.hand_off,
                 publication_execution.HANDOFF_KIND)):
            act(reopened, seam, decision_id="D1", now=LATE)
            self.assertEqual(
                self.jobs._connection.execute(
                    "SELECT count(*) FROM operations WHERE kind = ?",
                    (held,)).fetchone()[0], 1, held)
        self.assertEqual(len(self.custodian.seals), 1)
        self.assertEqual(
            publication_execution.handoff_of(
                reopened, self.recovery_job_id), first)


# -- 9. cancellation, expiry and the evidence they retain --------------------


class CancellationStopsNewEffectsAndRetainsEverything(
        PublicationExecutionCase):
    """A fence stops the next act; nothing already recorded is undone."""

    def test_a_cancelled_recovery_stops_the_next_act_and_keeps_the_rest(self):
        self.ready()
        staged = self.staged()
        cancellation.request(self.jobs, job_id=self.recovery_job_id,
                             reason="the owner stops this recovery")
        caught = self.refusal(self.published_once)
        self.assertIn("admits nothing more", caught.message)
        self.assertIn("retained", caught.message)
        # EVERY RECORD ALREADY TAKEN IS STILL THERE, and so are the bytes.
        self.assertEqual(
            publication_execution.staging_of(self.jobs,
                                             self.recovery_job_id), staged)
        self.assertIsNotNone(publication_recovery.admission_of(self.jobs,
                                                               "D1"))
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])
        self.assertFalse(self.gate()["open"])
        self.assertEqual(self.review_offers(), [])

    def test_a_cancelled_original_is_never_published_under_a_new_identity(self):
        self.ready()
        cancellation.request(self.jobs, job_id=self.job_id,
                             reason="the owner cancels the original")
        caught = self.refusal(self.staged)
        self.assertIn("cancelled at", caught.message)
        self.assertIn("never revived", caught.message)
        self.assertIsNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))

    def test_an_expired_recovery_stops_new_effects_through_the_same_fence(self):
        self.ready()
        self.staged()
        # THE HOST'S OWN FENCE, journalled from the durable deadline the
        # control evaluation derived rather than from a clock this case picked.
        closed = job_control.closed_of(self.jobs, self.recovery_job_id, LATE,
                                       any_stage=True)
        first = closed["first"]
        job_control.expire(self.jobs, job_id=self.recovery_job_id,
                           trigger=first["trigger"],
                           stage_id=first["stage_id"],
                           deadline_at=first["deadline_at"], observed_at=LATE)
        caught = self.refusal(self.published_once, now=LATE)
        self.assertIn("admits nothing more", caught.message)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.review_offers(), [])


# -- 10. malicious originals and genuine overflow ----------------------------


class AMaliciousOrOversizedOriginalIsRefusedByItsOwner(
        PublicationExecutionCase):
    """Links, special files, escaping paths and real ceilings."""

    def test_a_symbolic_link_in_the_original_is_refused_on_sight(self):
        self.ready()
        place = os.path.join(self.roots["workspace"],
                             role_contract.CANDIDATE_OUTPUT)
        os.symlink("/etc/passwd", os.path.join(place, "escape.txt"))
        caught = self.refusal(self.staged)
        self.assertIn("link", caught.message.lower())
        self.assertIsNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))

    def test_a_linked_directory_in_the_original_is_refused_too(self):
        self.ready()
        os.symlink(self.storage, os.path.join(
            self.roots["workspace"], role_contract.CANDIDATE_OUTPUT,
            "linked-directory"))
        caught = self.refusal(self.staged)
        self.assertIn("link", caught.message.lower())

    def test_a_special_file_in_the_original_is_refused_rather_than_read(self):
        """A FIFO AT A MEASURED NAME WOULD BLOCK A COPY FOREVER, which is the
        defect `workspaces._walk` records having fixed. The refusal arrives
        before anything is opened."""
        self.ready()
        os.mkfifo(os.path.join(self.roots["workspace"],
                               role_contract.CANDIDATE_OUTPUT, "waiting"))
        caught = self.refusal(self.staged)
        self.assertEqual(caught.category, "integrity")
        self.assertIsNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))

    def test_an_original_over_the_selected_entry_ceiling_holds(self):
        """GENUINE OVERFLOW, with real files. The selected declaration allows
        100 entries; this original carries more, so the inspection HOLDS and
        no decision can be taken about it."""
        place = os.path.join(self.roots["workspace"],
                             role_contract.CANDIDATE_OUTPUT)
        for number in range(role_contract.MAX_OUTPUT_ENTRIES + 1):
            with open(os.path.join(place, f"extra-{number:03d}.txt"),
                      "wb") as handle:
                handle.write(b"x")
        read = self.inspected()
        self.assertFalse(read["eligible"])
        held = [one for one in read["holds"] if one["code"] == "limit"]
        self.assertTrue(held, read["holds"])
        self.assertIn(str(role_contract.MAX_OUTPUT_ENTRIES),
                      held[0]["message"])
        caught = self.refusal(self.approved)
        self.assertEqual(caught.code, "limit")
        self.assertIsNone(publication_recovery.decision_of(self.jobs, "D1"))

    def test_a_declared_output_path_that_escapes_is_refused_by_its_owner(self):
        """THE DECLARATION OWNER REFUSES THE PATH, which is why neither this
        module nor the writer has to: a path that leaves the output root is
        not a declaration a freeze would ever admit."""
        held = dict(publication_recovery.PROVENANCE_OUTPUT,
                    path="../outside")
        caught = self.refusal(declared_outputs, [held])
        self.assertEqual(caught.category, "integrity")

    def test_an_oversized_provenance_is_refused_on_the_measurement(self):
        """THE SEPARATE BOUND IS ENFORCED ON REAL BYTES. A writer that wrote
        more than the approved 16384-byte descriptor allows is refused by this
        manager's own measurement rather than by its own claim."""
        self.ready()
        self.staged()

        class Oversized:
            def __init__(self, place, clock):
                self._place = place
                self._clock = clock

            def instance(self):
                return checkpoint1.CURRENT["identity"]

            def adopt(self, request):
                candidate = request["outputs"]["candidate"]
                provenance = request["outputs"]["provenance"]
                from baton_v12.worker_manager.workspaces import copied_manifest

                source = request["staged"]["locator"][len("file://"):]
                copied_manifest(source,
                                os.path.join(self._place, candidate["path"]))
                into = os.path.join(self._place, provenance["path"])
                os.makedirs(into)
                with open(os.path.join(into, "big.json"), "wb") as handle:
                    handle.write(b"{}" + b" " * (
                        provenance["constraints"]["max_bytes"] + 1))
                return {"outcome": "published", "provider_invocations": 0,
                        "verifier_invocations": 0, "started_at": PUBLISHED,
                        "ended_at": PUBLISHED}

        caught = self.refusal(
            self.published_once,
            writer=Oversized(self.workspace_of(self.publication_attempt),
                             self.clock))
        self.assertEqual(caught.code, "limit")
        self.assertIn("bounded output is bounded", caught.message)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))


# -- 11. conflicting and replayed decisions ----------------------------------


class OneFailedPublicationHasOneApprovedRecovery(PublicationExecutionCase):
    """A second approval, a changed operand and a replayed admission."""

    def test_a_second_approval_of_one_attempt_is_denied_at_the_decision(self):
        self.approved(decision_id="D1")
        caught = self.refusal(self.approved, decision_id="D2")
        self.assertEqual(caught.category, "policy")
        self.assertIn("already approved for publication", caught.message)
        self.assertIsNone(publication_recovery.decision_of(self.jobs, "D2"))

    def test_a_replayed_admission_returns_the_committed_answer(self):
        first = self.approve_and_admit()
        for _ in range(3):
            self.assertEqual(self.admit(), first)
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (publication_recovery.ADMITTED_KIND,)).fetchone()[0], 1)
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (publication_recovery.INTENT_KIND,)).fetchone()[0], 1)

    def test_a_held_decision_admits_nothing_and_publishes_nothing(self):
        read = self.inspected()
        held = self.ported()
        from tools.recovery_decision import OwnerAuthorization

        publication_recovery.decide(
            self.jobs, self.control, job_id=self.job_id,
            stage_id=self.stage_id, episode=self.episode,
            decision_id="H1", disposition="held",
            authorization=OwnerAuthorization(self.authority,
                                             participant=OWNER),
            expected=publication_recovery.expected_facts(read),
            profile=read["profile"]["profile"],
            profile_digest=read["profile"]["digest"],
            stages=list(publication_recovery.SELECTED_STAGES),
            declaration_digest=read["declaration"]["digest"],
            host=held["host"], exclusion=held["exclusion"],
            source=held["source"], now=NOW)
        caught = self.refusal(self.admit, decision_id="H1")
        self.assertEqual(caught.category, "policy")
        self.assertIn("launches nothing", caught.message)
        self.assertEqual(self.job_rows(), [self.job_id])

    def test_an_admission_against_bytes_that_moved_is_refused(self):
        self.approved()
        with open(os.path.join(self.roots["workspace"],
                               role_contract.CANDIDATE_OUTPUT,
                               "change.patch"), "ab") as handle:
            handle.write(b"moved\n")
        caught = self.refusal(self.admit)
        self.assertEqual(caught.code, "digest")
        self.assertIsNone(publication_recovery.admission_of(self.jobs, "D1"))
        self.assertEqual(self.job_rows(), [self.job_id])


# -- 12. the level-triggered pass --------------------------------------------


class OneTickOwesOneActAndDerivesItFromRows(PublicationExecutionCase):
    """`advance_publication`, driven to completion one act at a time."""

    def test_the_pass_performs_the_four_acts_in_order_and_then_nothing(self):
        self.ready()
        performed = []
        for _ in range(6):
            if not performed or performed[-1] != "hand-off":
                if performed and performed[-1] == "custody":
                    self.settle_ending()
                if performed and performed[-1] == "publish":
                    self.quiescent()
            held = publication_execution.advance_publication(
                self.jobs, self.seam(), now=PUBLISHED)
            if not held["acts"]:
                break
            self.assertEqual(len(held["acts"]), 1)
            act = held["acts"][0]
            self.assertEqual(act["outcome"], "performed", act)
            performed.append(act["act"])
        self.assertEqual(performed, list(publication_execution.ACTS))
        self.assertTrue(self.gate()["open"])
        self.assertEqual(len(self.review_offers()), 1)

    def test_a_contained_refusal_is_reported_and_does_not_stop_the_pass(self):
        self.ready()
        self.ports()["exclusion"].answer = {
            "runtime": {"attempt_id": None, "runtime_id": "runtime-1",
                        "execution_runtime": "running", "cleanup": "pending",
                        "assignment": None},
            "token": {"returned": False}}
        held = publication_execution.advance_publication(
            self.jobs, self.seam(), now=PUBLISHED)
        self.assertEqual(len(held["acts"]), 1)
        act = held["acts"][0]
        self.assertEqual(act["act"], "stage")
        self.assertEqual(act["outcome"], "held")
        # THE REFUSAL'S TYPED CATEGORY AND CODE CROSS, AND ITS PROSE DOES NOT.
        self.assertEqual(act["detail"], {"category": "runtime-observation",
                                         "code": "quiescence-unknown"})
        self.assertEqual(act["job_id"], self.recovery_job_id)

    def test_a_held_admission_is_not_a_recovery_the_pass_advances(self):
        """A HELD ADMISSION PERFORMED NO EFFECT, so there is no Job to publish
        and the pass has nothing to do about it."""
        binding = PublishingBinding(
            identity=checkpoint1.CURRENT["identity"], worker=None)
        checkpoint1.CURRENT.setdefault("ports", {})["publishing"] = binding
        self.approved()
        answer = self.admit()
        self.assertEqual(answer["state"], "held")
        held = publication_execution.advance_publication(
            self.jobs, self.seam(), now=PUBLISHED)
        self.assertEqual(held["acts"], [])
        caught = self.refusal(self.staged)
        self.assertIn("reached a HELD admission", caught.message)


# -- 13. incomplete custody never offers a review ----------------------------


class IncompleteCustodyNeverOffersAReview(PublicationExecutionCase):
    """COMPLETION WITHOUT CUSTODY, AND AN UNATTACHED CANDIDATE."""

    def test_a_completion_with_no_custody_record_opens_nothing(self):
        """The publication really completed -- adopted, frozen, collected and
        settled -- and this manager has taken no custody RECORD of it. The
        gate is shut, the binding says which one is missing, and the sweep
        owes no review offer."""
        self.ready()
        self.staged()
        self.published_once()
        self.quiescent()
        from baton_v12.worker_manager import request_freeze, request_intake

        request_freeze(self.control, self.publication_port, self.custodian,
                       attempt_id=self.publication_attempt,
                       disposition="completed")
        request_intake(self.control, self.publication_port, self.custodian,
                       attempt_id=self.publication_attempt)
        self.settle_ending()
        # THE STAGE IS `completed` AND THE REVIEW IS STILL BLOCKED.
        self.assertEqual(
            self.states()[documents.stage_id(self.recovery_job_id,
                                             documents.PUBLICATION_STAGE)],
            "completed")
        self.assertEqual(
            self.states()[publication_recovery.review_stage_id("D1")],
            "blocked")
        gate = self.gate()
        self.assertFalse(gate["open"])
        self.assertEqual(
            [one["name"] for one in gate["bindings"] if not one["present"]],
            ["custody", "intake", "reviewer-servability"])
        self.assertEqual(self.review_offers(), [])

    def test_a_candidate_that_is_not_the_approved_original_is_not_handed_on(self):
        """AN UNATTACHED CANDIDATE: the frozen result in custody carries a
        content digest that is not the approved original's, so no handoff is
        composed and the gate stays shut."""
        self.ready()
        self.staged()
        self.published_once()
        self.quiescent()
        held = publication_recovery.admission_of(self.jobs, "D1")
        moved = dict(held, output=dict(held["output"],
                                       tree_digest="sha256:" + "f" * 64))
        from unittest import mock

        with mock.patch.object(publication_execution, "_admitted",
                               return_value=moved):
            caught = self.refusal(self.collected)
        self.assertEqual(caught.code, "digest")
        self.assertIn("not the retained bytes", caught.message)
        self.assertFalse(self.gate()["open"])
        self.assertEqual(self.review_offers(), [])

    def test_no_handoff_is_composed_without_custody(self):
        self.ready()
        self.staged()
        self.published_once()
        caught = self.refusal(self.handed_off)
        self.assertIn("holds no publication custody", caught.message)
        self.assertIsNone(publication_execution.handoff_of(
            self.jobs, self.recovery_job_id))
        self.assertFalse(self.gate()["open"])


# -- 14. the old vocabulary keeps its behaviour ------------------------------


class OrdinaryJobsAndOldProfilesAreUnchanged(PublicationExecutionCase):
    """THE COMPATIBILITY HALF, asserted rather than assumed."""

    def test_the_three_older_submission_generations_admit_no_publication(self):
        for schema in documents.SUBMISSION_SCHEMAS[:3]:
            with self.subTest(schema=schema):
                caught = self.refusal(documents.owned_submission, {
                    "schema": schema, "submission_id": "sub-old",
                    "jobs": [{"job_id": "job-old",
                              "input_digest": "sha256:" + "1" * 64,
                              "policy_digest": "sha256:" + "2" * 64,
                              "test_scope": [],
                              "terminal_policy": "report-and-hold",
                              "stages": [{
                                  "kind": documents.PUBLICATION_STAGE,
                                  "work_id": WORK_A,
                                  "profile_name": "reference",
                                  "profile_digest": "sha256:" + "b" * 64,
                                  "depends_on": []}]}]})
                self.assertIn(documents.SUBMISSION_RECOVERY_SCHEMA,
                              caught.message)

    def test_a_recovery_generation_admits_only_the_selected_stage_set(self):
        for stages in (["review", documents.PUBLICATION_STAGE],
                       [documents.PUBLICATION_STAGE],
                       ["implementation", "review"],
                       [documents.PUBLICATION_STAGE, "review",
                        "integration"]):
            with self.subTest(stages=stages):
                caught = self.refusal(documents.owned_submission, {
                    "schema": documents.SUBMISSION_RECOVERY_SCHEMA,
                    "submission_id": "sub-recovery",
                    "jobs": [{"job_id": "job-recovery",
                              "input_digest": "sha256:" + "1" * 64,
                              "policy_digest": "sha256:" + "2" * 64,
                              "test_scope": [],
                              "terminal_policy": "report-and-hold",
                              "control": {
                                  "profile": publication_recovery
                                  .PUBLICATION_PROFILE},
                              "stages": [{
                                  "kind": kind, "work_id": WORK_A,
                                  "profile_name": "reference",
                                  "profile_digest": "sha256:" + "b" * 64,
                                  "depends_on": []} for kind in stages]}]})
                self.assertEqual(caught.category, "integrity")


    def test_a_recovery_generation_carries_exactly_one_job(self):
        """ONE OWNER DECISION ADMITS ONE RECOVERY, which is the duplicate
        effect the admission fence exists to prevent, refused one layer
        earlier at the document."""
        entry = {"job_id": "job-one",
                 "input_digest": "sha256:" + "1" * 64,
                 "policy_digest": "sha256:" + "2" * 64,
                 "test_scope": [], "terminal_policy": "report-and-hold",
                 "control": {"profile":
                             publication_recovery.PUBLICATION_PROFILE},
                 "stages": [
                     {"kind": documents.PUBLICATION_STAGE,
                      "work_id": WORK_A, "profile_name": "reference",
                      "profile_digest": "sha256:" + "b" * 64,
                      "depends_on": []},
                     {"kind": "review", "work_id": WORK_A,
                      "profile_name": "reference",
                      "profile_digest": "sha256:" + "b" * 64,
                      "depends_on": [{"job_id": "job-one",
                                      "kind": documents.PUBLICATION_STAGE}]}]}
        other = json.loads(json.dumps(entry).replace("job-one", "job-two"))
        caught = self.refusal(documents.owned_submission, {
            "schema": documents.SUBMISSION_RECOVERY_SCHEMA,
            "submission_id": "sub-two", "jobs": [entry, other]})
        self.assertIn("exactly one Job", caught.message)
        held = documents.owned_submission({
            "schema": documents.SUBMISSION_RECOVERY_SCHEMA,
            "submission_id": "sub-one", "jobs": [entry]})
        self.assertEqual(len(held["jobs"]), 1)

    def test_an_ordinary_pool_generation_declares_no_publication_lane(self):
        document = {"schema": scheduler.ORDINARY_POOL_SCHEMA,
                    "variant": "primary",
                    "separation_class": "provider-diverse",
                    "workers": [{"worker_id": "w1",
                                 "lane": scheduler.PUBLICATION_LANE,
                                 "participant": PUBLISHER,
                                 "profile_name": PUBLISHER_PROFILE,
                                 "profile_digest": PUBLISHER_DIGEST,
                                 "eligible_kinds": [
                                     scheduler.PUBLICATION_LANE]}]}
        caught = self.refusal(scheduler.own_pool, document)
        self.assertIn(scheduler.ORDINARY_POOL_SCHEMA, caught.message)
        self.assertIn(scheduler.POOL_SCHEMA, caught.message)
        # AND THE SAME DOCUMENT UNDER `/2` IS OWNED, keeping its own
        # generation rather than being rewritten as the newest.
        owned = scheduler.own_pool(dict(document,
                                        schema=scheduler.POOL_SCHEMA))
        self.assertEqual(owned["schema"], scheduler.POOL_SCHEMA)
        self.assertEqual(owned["workers"][0]["lane"],
                         scheduler.PUBLICATION_LANE)
        ordinary = scheduler.own_pool({
            "schema": scheduler.ORDINARY_POOL_SCHEMA, "variant": "primary",
            "separation_class": "provider-diverse",
            "workers": [{"worker_id": "w1", "lane": "implementation",
                         "participant": PRODUCER,
                         "profile_name": "reference",
                         "profile_digest": PUBLISHER_DIGEST,
                         "eligible_kinds": ["implementation"]}]})
        self.assertEqual(ordinary["schema"], scheduler.ORDINARY_POOL_SCHEMA)

    def test_an_ordinary_template_cannot_name_the_publication_stage(self):
        from baton_v12.job_manager import templates

        held = templates.TEMPLATES[role_contract.PROPOSAL100M_TEMPLATE]
        definition = {one: held[one] for one in held}
        roles = [{name: role[name] for name in role}
                 for role in definition["roles"]]
        roles[0] = dict(roles[0], kind=documents.PUBLICATION_STAGE)
        caught = self.refusal(templates.check_template,
                              dict(definition, roles=tuple(roles)))
        self.assertIn(documents.SUBMISSION_RECOVERY_SCHEMA, caught.message)

    def test_an_ordinary_submission_still_cannot_name_the_profile(self):
        caught = self.refusal(
            job_control.require_ordinary_profile,
            {"profile": publication_recovery.PUBLICATION_PROFILE})
        self.assertIn("output-publication-recovery admission", caught.message)
        # AND REC-8'S IS STILL GUARDED TOO, by the same table.
        caught = self.refusal(
            job_control.require_ordinary_profile,
            {"profile": job_control.SUCCESSOR_RECOVERY_PROFILE})
        self.assertIn("retained-recovery", caught.message)
        self.assertIsNone(job_control.require_ordinary_profile(
            {"profile": "documentation/1"}))


# -- 15. the shipped owners, on a bootstrapped instance ----------------------
#
# WITH NO `--owners` OPERAND AT ALL. Every case above composes the deployment
# configuration's binding and the host's cessation record itself, which is the
# right boundary for a case about the manager's own decisions and the wrong one
# for a case about whether the INSTALLED command works. So this one installs a
# disposable instance with `tools.bootstrap` and runs `publication-inspect` and
# `publication-decide` through `tools.job_manager.main` with the default
# factory -- `tools.publication_decision:owners` -- over that instance's own
# emitted configuration, its own persisted identity and its own Authority.
#
# AND THE ANSWER IT GIVES IS A HELD ADMISSION, which is the truthful one: a
# bootstrapped instance installs the implementation, review and integration
# workers it always has, and it has installed NO deterministic publication
# worker. So the shipped `DeploymentBinding.publication_worker` answers None,
# the admission is held with that prerequisite named, no Job is reserved and
# the first sweep after approval issues ZERO review offers. Installing the
# reusable worker is a deployment upgrade and is checkpoint 3's.

from tests.tools.test_bootstrap import ValidFixture as _InstalledFixture

INSTANCE_OWNER = "baton.owner"


class TheShippedOwnersRunOnABootstrappedInstance(_InstalledFixture):
    """The installed commands, the default ports, and the honest refusal."""

    maxDiff = None
    prepared_attempt = checkpoint1.PublicationCase.prepared_attempt
    write_output = checkpoint1.PublicationCase.write_output

    def setUp(self):
        from unittest import mock

        from baton_v12.job_manager import JobStore, submit
        from baton_v12.worker_manager import ControlStore, workspaces as owner
        from tools import bootstrap

        from tests.job_manager import fixtures
        from tests.manager import input_roots

        super().setUp()
        self.instants = [NOW]
        self.install_document = self.document(
            owner_participant=INSTANCE_OWNER,
            jobs=[self.job(work_id=self.work)])
        with open(os.devnull, "w") as quiet:
            self.installed = bootstrap.prepare(self.install_document,
                                               stream=quiet)
        self.places = bootstrap.layout(self.state)
        import pathlib

        pathlib.Path(self.places["install_inputs"]).write_text(
            json.dumps(self.install_document, indent=2, sort_keys=True),
            encoding="utf-8")
        self.uuid = self.installed["configuration"]["authority_uuid"]
        self.jobs = JobStore.open(self.places["job_store"],
                                  authority_uuid=self.uuid,
                                  incarnation="joined-1", clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.control = ControlStore.open(self.places["control_store"],
                                         incarnation="joined-1",
                                         clock=self.clock)
        self.addCleanup(self.control.close)
        self.group = input_roots.configured_group(self.control)
        self.storage = os.path.join(self.state, "workspaces")
        os.makedirs(self.storage, exist_ok=True)
        owner.configure_workspace_storage(self.control, self.storage)
        # THE FAILED JOB, submitted into the instance's own Job store with the
        # profiles the instance's own workers carry -- so the review stage the
        # recovery would reuse is one this deployment can really serve.
        reviewer = [one for one in
                    self.installed["configuration"]["workers"]
                    if one["role"] == "review"][0]["deployment"]
        from tools import stage_execution

        self.submitted = {
            "input_digest": stage_execution.job_input_identity(
                reviewer["input_manifest"]),
            "policy_digest": reviewer["policy_digest"],
            "profile_name": reviewer["profile_name"],
            "profile_digest": reviewer["profile_digest"]}
        held = fixtures.job(
            "job-a", input_digest=self.submitted["input_digest"],
            policy_digest=self.submitted["policy_digest"],
            stages=[fixtures.stage(
                "implementation", self.work,
                profile_name=self.submitted["profile_name"],
                profile_digest=self.submitted["profile_digest"]),
                fixtures.stage(
                    "review", self.work,
                    profile_name=self.submitted["profile_name"],
                    profile_digest=self.submitted["profile_digest"],
                    depends_on=[{"job_id": "job-a",
                                 "kind": "implementation"}])])
        submit(self.jobs, {"schema": documents.SUBMISSION_SCHEMA,
                           "submission_id": "sub-1", "jobs": [held]})
        self.job_id = "job-a"
        self.stage_id = documents.stage_id("job-a", "implementation")
        self.episode = 1
        self.attempt_id = episodes.episode_of(self.jobs, self.stage_id,
                                              1)["attempt_id"]
        # THE RETAINED OUTPUT, built by checkpoint 1's own fixture methods so
        # the bytes this instance's shipped ports read are the same bytes the
        # module-level cases read.
        patched = [mock.patch.object(checkpoint1, "WORK_A", self.work),
                   mock.patch.object(checkpoint1, "UUID", self.uuid),
                   mock.patch.object(checkpoint1, "PRODUCER_PARTICIPANT",
                                     PRODUCER)]
        for one in patched:
            one.start()
            self.addCleanup(one.stop)
        self.roots = self.prepared_attempt(self.attempt_id)
        self.original = self.write_output()

    def clock(self):
        return self.instants[-1]

    def argv(self, command, *extra):
        """THE INSTALLED ARGV, with NO `--owners` operand."""
        return [command,
                "--store", self.places["job_store"],
                "--authority-uuid", self.uuid,
                "--incarnation", "joined-1",
                "--control", self.places["control_store"],
                "--authority", self.places["authority_store"],
                "--instance", self.state,
                "--job", self.job_id,
                "--stage", self.stage_id,
                "--episode", str(self.episode),
                *extra]

    def command(self, *argv):
        import io

        from tools import job_manager

        said, failed = io.StringIO(), io.StringIO()
        code = job_manager.main(list(argv), clock=lambda: NOW, stream=said)
        del failed
        text = said.getvalue()
        return code, (json.loads(text) if text.strip() else None)

    def test_the_default_factory_composes_every_port_and_reads_the_original(self):
        code, read = self.command(self.argv(
            "publication-inspect", "--participant", INSTANCE_OWNER)[0],
            *self.argv("publication-inspect", "--participant",
                       INSTANCE_OWNER)[1:])
        self.assertEqual(code, 0, read)
        self.assertEqual(read["schema"], publication_recovery.READ_SCHEMA)
        self.assertEqual(read["selector"]["attempt_id"], self.attempt_id)
        self.assertEqual(read["output"]["tree_digest"],
                         self.original["tree_digest"])
        self.assertEqual(read["authorization"]["endpoint"], INSTANCE_OWNER)
        self.assertTrue(read["authorization"]["holds"])

    def test_the_shipped_binding_installs_no_publication_worker(self):
        from tools.fresh_attempt_ports import (DeploymentBinding,
                                               instance_identity)

        binding = DeploymentBinding(self.state,
                                    identity=instance_identity(self.state))
        self.assertIsNone(binding.publication_worker())
        roles = sorted(one["role"] for one in
                       self.installed["configuration"]["workers"])
        self.assertNotIn(scheduler.PUBLICATION_LANE, roles)

    def test_the_default_factory_reports_this_instances_real_holds(self):
        """WHAT A FRESH INSTANCE REALLY IS, read through the shipped ports.

        THE THREE HOLDS ARE FACTS AND NOT FIXTURE SHORTFALLS, and naming them
        is the point: this is an instance whose failed attempt never returned
        its workspace token, whose Job was submitted by hand rather than
        created from a template, and whose retained bundle does not carry the
        candidate commit. The real `HostExclusion`, the real
        `creation.job_task_of` and the real `SourceCorrespondence` each say so
        in their own words -- which is exactly the behaviour a deployment needs
        from them, and is what a stand-in port cannot establish.
        """
        code, read = self.command(*self.argv("publication-inspect",
                                             "--participant",
                                             INSTANCE_OWNER))
        self.assertEqual(code, 0)
        self.assertFalse(read["eligible"])
        self.assertEqual(
            sorted((one["category"], one["code"]) for one in read["holds"]),
            sorted([("runtime-observation", "quiescence-unknown"),
                    ("refused", "precondition"),
                    ("refused", "precondition")]))
        said = " ".join(one["message"] for one in read["holds"])
        self.assertIn("has not returned its workspace resource", said)
        self.assertIn("records no admitted task document", said)
        self.assertIn("does not carry", said)
        # AND THE SOURCE-AWARE OWNER REALLY RAN: the correspondence hold is
        # the Git consumer's own answer about a bundle it actually read.
        self.assertIsNone(read["correspondence"])

    def test_an_approval_on_held_evidence_is_refused_and_records_nothing(self):
        """THE DECISION PATH, THROUGH THE SHIPPED PORTS, and it refuses.

        An owner cannot approve evidence that is held: `decide` performs the
        same inspection again, finds the holds and refuses -- so no decision is
        committed, no admission is composed and the first sweep afterwards has
        nothing to offer.
        """
        code, read = self.command(*self.argv("publication-inspect",
                                             "--participant",
                                             INSTANCE_OWNER))
        self.assertEqual(code, 0)
        argv = self.argv(
            "publication-decide", "--approve",
            "--participant=" + INSTANCE_OWNER, "--decision-id=J1",
            "--expect-attempt=" + read["selector"]["attempt_id"],
            "--expect-selection-digest=" + read["selection_digest"],
            "--expect-candidate-base=" + BASE,
            "--expect-candidate-head=" + HEAD,
            "--expect-output-digest=" + read["output"]["tree_digest"],
            "--expect-output-bytes=" + str(read["output"]["total_bytes"]),
            "--expect-producer-status=0",
            "--context-digest=sha256:" + "0" * 64,
            "--declaration-digest=" + read["declaration"]["digest"],
            "--profile=" + read["profile"]["profile"],
            "--profile-digest=" + read["profile"]["digest"])
        for word in checkpoint1.PRODUCER_ARGV:
            argv.append("--producer-verification=" + word)
        for word in publication_recovery.SELECTED_STAGES:
            argv.append("--stage-word=" + word)
        code, answer = self.command(*argv)
        self.assertEqual(code, 1)
        self.assertIsNone(answer)
        self.assertIsNone(publication_recovery.decision_of(self.jobs, "J1"))
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (publication_recovery.DECISION_KIND,)).fetchone()[0], 0)
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM stage_allocations").fetchone()[0], 0)


# -- 16. what this checkpoint is, said out loud ------------------------------


class ThisCheckpointIsPartialEvidenceAndNeverResumeSupported(
        PublicationExecutionCase):
    """THE BOUNDARY, asserted so it cannot be read as more than it is."""

    def test_no_implementation_is_redispatched_anywhere_on_this_path(self):
        """ZERO implementation stages, counted across the whole path."""
        self.whole_path()
        kinds = [row[1] for row in self.jobs._connection.execute(
            "SELECT stage_id, kind FROM stages WHERE job_id = ?",
            (self.recovery_job_id,))]
        self.assertEqual(sorted(kinds), sorted(documents.RECOVERY_STAGES))
        self.assertNotIn("implementation", kinds)
        # AND THE ORIGINAL JOB IS STILL FAILED, with its own rows untouched:
        # no new episode, no new allocation and no frozen result.
        self.assertEqual(
            [row[0] for row in self.jobs._connection.execute(
                "SELECT episode FROM episodes WHERE stage_id = ?",
                (self.stage_id,))], [1])
        from baton_v12.worker_manager import frozen_output_of

        self.assertIsNone(frozen_output_of(self.control, self.attempt_id))

    def test_the_producers_verifier_is_never_repeated(self):
        """THE REUSED EVIDENCE IS CARRIED AND THE COMMAND IS NOT RUN. The
        producer's argv travels in the recovery input and in the provenance
        with `producer-evidence` and `independent_acceptance: false` beside
        it, and nothing on this path executes it: the adoption request names
        no command at all, and the adapter refuses one that does."""
        held = self.whole_path()
        declaration = publication_recovery.admission_of(
            self.jobs, "D1")["input_declaration"]
        self.assertEqual(declaration["producer"]["argv"],
                         list(checkpoint1.PRODUCER_ARGV))
        self.assertEqual(declaration["producer"]["qualification"],
                         "producer-evidence")
        self.assertFalse(declaration["producer"]["independent_acceptance"])
        self.assertEqual(
            publication_execution.result_of(
                self.jobs, self.recovery_job_id)["invocations"],
            {"provider": 0, "verifier": 0, "commands": 0})
        self.assertIn("never acceptance",
                      held["reviewer"]["producer_evidence"])

    def test_the_readiness_never_says_the_recovery_is_complete(self):
        held = publication_execution.publication_readiness(self.jobs, "D1") \
            if publication_recovery.admission_of(self.jobs, "D1") else None
        self.assertIsNone(held)
        self.whole_path()
        held = publication_execution.publication_readiness(self.jobs, "D1")
        self.assertTrue(held["handed_off"])
        self.assertIsNone(held["owed"])
        self.assertEqual(held["review"], "runnable")
        self.assertEqual(held["original_job"],
                         "failed; unchanged by this recovery")
        self.assertIn("nothing here has judged it", held["detail"])
        self.assertNotIn("resume", held["detail"].lower())

    def test_the_selected_identities_and_bounds_are_the_owners_own(self):
        self.assertEqual(documents.SUBMISSION_RECOVERY_SCHEMA,
                         "baton.v12.job-submission/4")
        self.assertEqual(scheduler.POOL_SCHEMA, "baton.v12.worker-pool/2")
        self.assertEqual(publication_recovery.RECOVERY_STORE_GENERATION, 10)
        self.assertEqual(publication_recovery.PUBLICATION_PROFILE,
                         "output-publication-review/1")
        self.assertEqual(
            job_control.sub_bound_of(
                publication_recovery.PUBLICATION_PROFILE,
                documents.PUBLICATION_STAGE), 900)
        self.assertEqual(publication_recovery.PROVENANCE["max_bytes"], 16384)
        self.assertEqual(publication_recovery.PROVENANCE["max_entries"], 1)
        self.assertEqual(publication_recovery.PROVENANCE["link_policy"],
                         "forbid")
