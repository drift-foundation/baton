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

  THE PUBLICATION RUNS THROUGH THE ORDINARY WORKER LIFECYCLE. The publication
  worker is composed exactly as a deployment composes it --
  `tools.publication_worker.publication_operations`, which is
  `single_worker.worker_operations` with `PublicationStage` as its stage owner
  -- and driven by the real `manager.sweep`: a real offer, acceptance, claim
  and activation; the real input root, launch document, workspace token and
  journalled runtime start; the real command exchange; the real ending.

  THE WORKER IS THE REAL WORKER. `v12/worker/publication_entry.
  PublicationAgent`, served by the real `baton_worker.serve_exchange`, with its
  copy run as a real supervised child process. The staged root it reads is the
  exact directory the engine was told to bind read-only at `/input/source`.

  THE CUSTODY PATH IS THE ORDINARY ONE. `request_freeze`, `request_intake`,
  `decide_retention` and `authorize_cleanup` are the Worker Manager's own
  public operations, called by the publication worker's own ending over real
  files in a real directory.

  THE GATE IS THE PROJECTION'S. `projection.stage_states` is what reports the
  review stage `blocked` or `queued`, and `projection.owed_acts` is what
  counts the offers; no case opens a gate by writing one.

WHAT IS FAKED, AND ONLY AT ITS NORMAL BOUNDARY: the ENGINE -- the callable an
`OciAdapter` runs `docker` vectors through, which composes, starts, lists,
inspects, stops and removes a container that does not exist -- together with
the engine-side custody helper; the host's record of the ORIGINAL attempt's
runtime and workspace token; the DEPLOYMENT CONFIGURATION's binding and
selector (which is where a deployment states which worker it installed); the
instance guard; and the ENGINE the Git-aware consumer's commands run at. No
runtime observation, token state, receipt or exchange document is written by
a case: where a case needs an engine that will not stop a container, loses a
reply or cannot be reached, it interposes AT THE ENGINE. There is no provider,
no model and no image in this file, and what stands in for the container's
filesystem view is two worker module constants and one operand, named in
`turn`.

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

import sys

from baton_v12.contracts import ContractRefusal, digest, digest_of_bytes
from baton_v12.contracts.manifest import job_input_identity
from baton_v12.job_manager import (cancellation, creation, documents, episodes,
                                   job_control, manager, projection,
                                   publication_execution,
                                   publication_recovery, role_contract,
                                   scheduler, submission)
from baton_v12.worker_manager import (attempt_runtime_of, launch,
                                      source_boundary, workspaces)
from baton_v12.worker_manager.sealing import declared_outputs

from tests.job_manager import test_publication_recovery_admission as checkpoint1
from tests.job_manager.fixtures import NOW, WORK_A
from tools import publication_worker, single_worker, stage_execution

# WHERE THE CONTAINER WORKER'S OWN MODULES LIVE. They are not importable from
# the manager distribution, exactly as in an image; a case that runs the real
# worker entry puts this directory on its path for its own duration.
WORKER = os.path.normpath(os.path.join(os.path.dirname(__file__),
                                       "..", "..", "..", "worker"))

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
# Later than the launch and still inside the 900-second bound.
LATE_IN_BOUND = "2026-09-02T00:20:00.000Z"


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

    def publication_input(self, job_id, *, work_id, task=None):
        """THE DEPLOYMENT'S OWN DERIVATION, called and not stood in for.

        `stage_execution.publication_input_identity` over the publication
        worker document this case installs -- the function the shipped
        `DeploymentBinding` calls -- so what a recovery is submitted under
        here is what the real selector and the real delivery derive.
        """
        self.asked.append(("publication_input", job_id, work_id))
        return None if self.derive is None else self.derive(
            job_id, work_id, task)

    derive = None

    def serving(self, job_id, *, stage, job, task=None):
        self.asked.append((job_id, dict(stage)))
        if not self.serves:
            return []
        # WORKER IDENTITIES, which is what the shipped
        # `DeploymentBinding.serving` answers.
        if stage["kind"] == documents.PUBLICATION_STAGE:
            return [PUBLISHER_WORKER_ID]
        return [REVIEWER]


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
        if WORKER not in sys.path:
            sys.path.insert(0, WORKER)
            self.addCleanup(sys.path.remove, WORKER)

    # -- the owner ports, with a deployment that installed a publisher -----

    def ported(self, **changed):
        held = super().ported()
        binding = checkpoint1.CURRENT.setdefault("ports", {}).get("publishing")
        if binding is None:
            # THE JOB-SCOPED IDENTITY, which is what a deployment's own
            # binding answers and what the worker lifecycle holds a Job to.
            binding = PublishingBinding(
                identity=checkpoint1.CURRENT["identity"],
                input_digest=job_input_identity(
                    self.publication_declaration()))
            checkpoint1.CURRENT["ports"]["publishing"] = binding
        if binding.derive is None:
            binding.derive = self.derived_input
        held["binding"] = binding
        held["ending"] = self.ending_port()
        held.update(changed)
        return held

    def installed_pool(self):
        """The one-worker pool document this case's publisher is installed
        in, in the shape `stage_execution` reads one."""
        if getattr(self, "_installed", None) is None:
            self._installed = {"workers": [{
                "worker_id": PUBLISHER_WORKER_ID, "role": "publication",
                "deployment": single_worker._held(
                    self.publication_deployment(), roles=("publication",))}]}
        return self._installed

    def derived_input(self, job_id, work_id, task=None):
        return stage_execution.publication_input_identity(
            self.installed_pool(),
            {"job_id": job_id, "job_work_id": work_id}, task)

    def served_deployment(self, job_id=None, work_id=None):
        """The document THIS recovery's publication stage is served under:
        the installed one as `stage_execution._served_deployment` derives it
        for the recovery's Work and the ORIGINAL Job's task."""
        pool = self.installed_pool()
        return stage_execution._served_deployment(
            pool, pool["workers"][0],
            {"job_id": job_id or publication_recovery.recovery_job_id("D1"),
             "job_work_id": work_id or WORK_A},
            creation.job_task_of(self.jobs, self.job_id))

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
        """Admitted, offered, claimed and ACTIVATED: everything act one needs,
        and nothing started.

        THROUGH THE COMPOSED WORKER'S OWN OPERATIONS. The offer, its
        acceptance and the claim are the sweep's ordinary owed acts performed
        by the real publication worker composition; the activation is the
        product's own `prepare_managed_parent`, which is exactly "activate the
        existing offer, starting nothing". No row is written by hand.
        """
        from tools.integration_worker import prepare_managed_parent

        self.approve_and_admit(**changed)
        operations, _stage = self.composed()
        self.instants.append(CLAIMED)
        for _ in range(4):
            held = projection.stage_states(self.jobs, operations)
            entry = held[self.publication_stage_id]
            if entry["state"] == "claimed":
                break
            for owed in projection.owed_acts(self.jobs, operations, held):
                if owed["stage_id"] != self.publication_stage_id:
                    continue
                manager._delegate(
                    self.jobs, operations, owed, entry["attempt"],
                    submission.job_of(self.jobs, self.recovery_job_id))
        else:
            self.fail("the publication stage was not offered and claimed")
        entry = projection.stage_states(self.jobs, operations)[
            self.publication_stage_id]
        prepare_managed_parent(
            operations, entry["attempt"],
            submission.job_of(self.jobs, self.recovery_job_id))
        self.publication_attempt = entry["attempt"]["attempt_id"]
        return {"attempt_id": self.publication_attempt,
                "assignment": self.authority.assignment_of(WORK_A)}

    def staged(self, *, now=PUBLISHED, **changed):
        return publication_execution.stage_input(
            self.jobs, self.seam(**changed), decision_id="D1", now=now)

    def tick(self, now=None):
        """One ordinary manager sweep over the composed publication worker."""
        operations, _stage = self.composed()
        if now is not None:
            self.instants.append(now)
        return manager.sweep(self.jobs, operations, now=self.clock())

    def launched(self, *, now=PUBLISHED):
        """Drive the ordinary sweep until the confined worker holds its
        command: mounted, intent committed, runtime started, command
        published. Nothing inside the container has run."""
        for _ in range(4):
            self.tick(now)
            view = self.exchange_view()
            if view is not None and view.get("command") is not None:
                return view
        self.fail("the publication worker was never given its command")

    def exchange_view(self):
        operations, stage = self.composed()
        row = stage._stage_of(self.publication_attempt)
        return None if row is None else operations.observe(row).get(
            "exchange")

    def epoch(self):
        from datetime import datetime

        return datetime.fromisoformat(
            self.clock().replace("Z", "+00:00")).timestamp()

    def turn(self, agent_type=None, **agent):
        """THE CONFINED WORKER'S ONE TURN, and it is the real worker.

        `v12/worker/publication_entry.PublicationAgent`, served by the real
        `baton_worker.serve_exchange` over the launch document and the
        command and event namespaces this deployment published, with its copy
        run as a real supervised child process. What stands in for the
        container is two module constants and one operand: `/input` and
        `/output` are this attempt's own roots, and the read-only staged root
        is the exact directory the ENGINE was told to bind at
        `/input/source` -- read out of the composed mount vector rather than
        chosen here.
        """
        import baton_worker
        import publication_entry

        operations, stage = self.composed()
        row = stage._stage_of(self.publication_attempt)
        delivered = operations._worker._adopted(row)
        home = os.path.join(self.storage, self.publication_attempt)
        mounts = {one["Destination"]: one for one in self.oci.mounts}
        for name, value in (("INPUT_ROOT", os.path.join(home, "inputs")),
                            ("OUTPUT_ROOT", os.path.join(home, "workspace"))):
            held = getattr(baton_worker, name)
            setattr(baton_worker, name, value)
            self.addCleanup(setattr, baton_worker, name, held)
        composed = dict(input_root=os.path.join(home, "inputs"),
                        output_root=os.path.join(home, "workspace"),
                        source_root=mounts["/input/source"]["Source"],
                        clock=self.epoch,
                        # THE WATCH THREAD IS OFF BY DEFAULT IN THIS PROCESS.
                        # It ends the process it runs in, which here is the
                        # test runner; the cases that are about it either
                        # hand it an `abort` that records the decision or run
                        # the worker as a real child process.
                        watch=False)
        composed.update(agent)
        serving = (agent_type or publication_entry.PublicationAgent)(
            **composed)
        self.served_agent = serving
        try:
            return baton_worker.serve_exchange(
                serving, delivered.document,
                launch.payload_of(delivered.document)["session"],
                delivered.exchange.command_root,
                delivered.exchange.event_root)
        finally:
            serving.stand_down()

    def published_once(self, *, now=PUBLISHED):
        """LAUNCH, RUN THE WORKER, AND LET THE ORDINARY ENDING CONCLUDE.

        Idempotent like the act it stands for: a recorded adoption is read
        back and nothing is launched or run again.
        """
        recorded = publication_execution.result_of(self.jobs,
                                                   self.recovery_job_id)
        if recorded is not None:
            return recorded
        self.launched(now=now)
        self.assertEqual(self.turn(), 0)
        self.tick(now)
        recorded = publication_execution.result_of(self.jobs,
                                                   self.recovery_job_id)
        if recorded is None:
            self.fail(f"the ordinary ending recorded no adoption: "
                      f"{self.last_spoken}")
        return recorded

    @property
    def last_spoken(self):
        return self.tick()["spoken"]

    def collected(self, *, now=PUBLISHED, **changed):
        return publication_execution.take_custody(
            self.jobs, self.seam(**changed), decision_id="D1", now=now)

    def handed_off(self, *, now=PUBLISHED, **changed):
        return publication_execution.hand_off(
            self.jobs, self.seam(**changed), decision_id="D1", now=now)

    def whole_path(self, *, now=PUBLISHED):
        """ADMIT, OFFER, CLAIM, STAGE, LAUNCH, ADOPT, STOP, MEASURE, FREEZE,
        COLLECT, RELEASE, CLEAN UP, BIND CUSTODY, HAND OFF."""
        self.ready()
        self.published_once(now=now)
        self.collected(now=now)
        return self.handed_off(now=now)

    # -- the publication worker's own deployment -----------------------------

    def publication_declaration(self):
        """The input manifest the installed publication worker is configured
        with.

        IT DECLARES THE TWO OUTPUTS A RECOVERY PUBLISHES, and they are the
        product's own: W385694's exact selected proposal revision, read from
        the descriptor owner, and `publication_recovery.PROVENANCE_OUTPUT`
        composed from the owner-selected provenance descriptor. Its one
        source is the nominated, read-only mountpoint the staged original is
        bound at, declared empty exactly as every nominated source is.
        """
        from tests.manager.test_output import OutputCase

        held = getattr(self, "_declaration", None)
        if held is not None:
            return held
        declaration = publication_recovery.corrective_declaration()
        self.task_bytes = json.dumps(
            {"schema": "baton.v12.output-publication-task/1",
             "instructions": "adopt the approved retained output"},
            sort_keys=True).encode("utf-8")
        document = dict(OutputCase.published(),
                        outputs=[copy.deepcopy(declaration["output"]),
                                 copy.deepcopy(
                                     publication_recovery.PROVENANCE_OUTPUT)],
                        policy_digest=POLICY,
                        runtime_profile_digest=PUBLISHER_DIGEST,
                        work_ref={"authority_uuid": AUTHORITY,
                                  "work_id": WORK_A})
        document["sources"] = copy.deepcopy(document["sources"])[:1]
        document["sources"][0]["destination"] = (
            single_worker.SOURCE_DESTINATION)
        document["sources"][0]["content_manifest"] = {
            "entries": [], "entry_count": 0, "total_bytes": 0,
            "tree_digest": single_worker.EMPTY_TREE_DIGEST}
        document["sources"][0]["consumption"] = (
            source_boundary.source_consumption("generic"))
        document["human_contract"] = {
            "artifact_id": "publication-task-1",
            "media_type": "application/json",
            "bytes": len(self.task_bytes),
            "content_digest": digest_of_bytes(self.task_bytes),
            "locator": "artifact://contracts/publication-task-1"}
        document.pop("manifest_digest", None)
        document["manifest_digest"] = digest(document)
        self._declaration = document
        return document

    def publication_deployment(self, **changed):
        """The publication worker's own single-worker deployment document.

        NO CREDENTIAL SLOT AND NO PROVIDER, which is the contract's own
        description of this worker and is what `single_worker._held` now
        REQUIRES of the publication role.
        """
        manifest = self.publication_declaration()
        task = os.path.join(self.root, "publication-task.json")
        with open(task, "wb") as writing:
            writing.write(self.task_bytes)
        held = {
            "schema": single_worker.CONFIG_SCHEMA,
            "authority_store": self.authority_path,
            "authority_uuid": AUTHORITY,
            "participant": PUBLISHER,
            "principal": PUBLISHER_PRINCIPAL,
            "profile_name": PUBLISHER_PROFILE,
            "profile_digest": PUBLISHER_DIGEST,
            "policy_digest": POLICY,
            "adapter_name": "docker-publication-worker",
            "adapter_digest": "sha256:" + "6" * 64,
            "engine": "docker",
            "image_digest": manifest["worker_image_digest"],
            "network": "none",
            "workspace_storage": self.storage,
            "workspace_group": os.getgid(),
            "launch_home": os.path.join(self.root, "launch"),
            "credential_home": os.path.join(self.root, "credentials"),
            "credential_sources": None,
            "credential_slots": [],
            "credential_profile": {},
            "nominated_source": self.staging,
            "workspace_capacity": {
                "max_bytes": source_boundary.MIN_WORKSPACE_BYTES + 1},
            "input_manifest": manifest,
            "task_document": task,
            "launch_contract": "v12-assignment-1",
            "launch_role": "publication",
            "review_route": "rview",
            "retention_policy_digest": "sha256:" + "5" * 64,
            "retention_disposition": "retain"}
        held.update(changed)
        return held

    def composed(self, **ports):
        """THE PRODUCTION COMPOSITION of one publication worker: the ordinary
        `single_worker` lifecycle with `tools.publication_worker.
        PublicationStage` as its stage owner, over this case's real Authority
        and stores. ONLY THE ENGINE IS A DOUBLE.
        """
        if getattr(self, "_composed", None) is None:
            from baton_v12.worker_manager import certify_profile
            from tests.tools.test_stage_execution import ComposedOneJobCase

            held = self.ported()
            held.update(ports)
            if getattr(self, "oci", None) is None:
                self.oci = ComposedOneJobCase.quiescing(self)
                self.engine_hook = None
            # THE PROFILE IS CERTIFIED FOR THIS MANAGER, through the owner
            # that certifies one, as a deployment does once at installation.
            certify_profile(self.control, "runtime", PUBLISHER_PROFILE,
                            PUBLISHER_DIGEST)
            given = self.served_deployment()
            self._composed = publication_worker.publication_operations(
                given, jobs=self.jobs, control=self.control,
                authority=self.authority,
                provider=self.refused_provider,
                host=held["host"], exclusion=held["exclusion"],
                identity=checkpoint1.CURRENT["identity"],
                workspaces=self.staging, engine_run=self._engine,
                clock=self.clock)
            # THE PASS IS TAKEN OFF THE SWEEP BY DEFAULT IN THIS SUITE, and
            # only so a case can STAND BETWEEN two of its acts: most cases
            # here are about one act and what is true just before or after
            # it, and a sweep that also ran the pass would have bound custody
            # and handed off before the case could look. The cases that are
            # about the sweep doing it all call `serving()` and get the
            # composition exactly as a deployment composes it.
            self._seam = self._composed[0].recovery_publication
            self._composed[0].recovery_publication = None
        return self._composed

    def serving(self):
        """The composition AS A DEPLOYMENT COMPOSES IT: the publication seam
        on the operations, so `manager.sweep` runs the pass itself."""
        operations, stage = self.composed()
        operations.recovery_publication = stage.seam
        return operations, stage

    def restarted(self):
        """A NEW MANAGER INCARNATION over the same stores and the same
        engine: the composition is rebuilt from nothing, exactly as a
        restarted process rebuilds it, and holds no memory of the last one."""
        self._composed = None
        return self.composed()

    def _engine(self, argv, **options):
        """THE ENGINE BOUNDARY, with one place a case may interpose.

        `engine_hook` is asked first and answers an engine reply, raises, or
        answers `None` to let the ordinary double answer. That is how a case
        models an engine that will not stop a container, loses a reply or
        cannot be reached -- at the engine, which is where those things
        happen, and never by writing a runtime observation.
        """
        hook = getattr(self, "engine_hook", None)
        if hook is not None:
            answer = hook(argv)
            if answer is not None:
                return answer
        return self.oci(argv, **options)

    def refused_provider(self, provider, reference):
        """A publication worker declares no credential slot, so the
        credential provider is never asked. Asking it is a failing case."""
        self.fail(f"a deterministic publication asked for credential "
                  f"{provider}/{reference}")

    def workspace_of(self, attempt_id):
        return os.path.join(self.storage, attempt_id, "workspace")

    def seam(self, **changed):
        """This deployment's own seam, or the same seam with ONE owner
        replaced -- which is how a case states which owner it is about."""
        _operations, stage = self.composed()
        if not changed:
            return stage.seam
        composed = {one: getattr(stage.seam, one)
                    for one in publication_execution.PUBLICATION_SEAM}
        composed.update(changed)
        return publication_worker.PublicationSeam(**composed)

    @property
    def publication_stage_id(self):
        return documents.stage_id(self.recovery_job_id,
                                  documents.PUBLICATION_STAGE)

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
        """THE REAL composed publication worker operations over this case's
        own stores, which is what the ordinary projection reads."""
        return self.composed()[0]

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
        self.assertEqual(
            answer["recovery_input_digest"],
            publication_recovery.recovery_input_digest(declaration))
        # THE JOB-SCOPED IDENTITY OF THE DOCUMENT THIS RECOVERY IS SERVED
        # UNDER (review 2026-11-23T18-55-03Z R3): the installed publication
        # worker's declarations, bound to this recovery's Work and to the
        # ORIGINAL Job's task. Not the whole runtime manifest digest, under
        # which no Job could be served, and not the installed worker's own
        # identity, which names the task and Work it was installed with.
        served = self.served_deployment()["input_manifest"]
        installed = self.publication_declaration()
        self.assertEqual(answer["input_digest"], job_input_identity(served))
        self.assertNotEqual(answer["input_digest"],
                            served["manifest_digest"])
        self.assertNotEqual(answer["input_digest"],
                            job_input_identity(installed))
        original_task = creation.job_task_of(self.jobs, self.job_id)
        self.assertEqual(served["human_contract"]["content_digest"],
                         digest_of_bytes(original_task.encode("utf-8")))
        self.assertEqual(served["work_ref"]["work_id"], WORK_A)
        # WHAT DID NOT MOVE: the selected publication declarations.
        self.assertEqual(served["outputs"], installed["outputs"])
        self.assertEqual(served["policy_digest"], installed["policy_digest"])
        self.assertEqual(answer["worker"]["input_digest"],
                         job_input_identity(installed))
        self.assertNotEqual(answer["input_digest"],
                            answer["recovery_input_digest"])
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

    # -- the SERVING manager ends what the owner command cannot ------------

    def sessionless(self):
        """THE OWNER COMMAND'S OWN ENDING PORT: a read of the Authority and
        no participant session, which is what `publication_decision.owners`
        composes and all it may compose."""
        from tools.publication_ports import PriorAssignment

        return PriorAssignment(self.authority,
                               checkpoint1.CURRENT["identity"])

    def test_the_owner_commands_admission_stops_at_the_held_assignment(self):
        """The owner approves and the admission begins: the recovery identity
        is reserved, and then the prior assignment cannot be ended by a
        process holding no session for its holder. The refusal names the
        capability; the producer still holds the Work; nothing is admitted."""
        self.approved()
        caught = self.refusal(self.admit, ending=self.sessionless())
        self.assertEqual(caught.code, "capability")
        self.assertIsNotNone(publication_recovery.intent_of(self.jobs, "D1"))
        self.assertIsNone(publication_recovery.ending_of(self.jobs, "D1"))
        self.assertIsNone(publication_recovery.admission_of(self.jobs, "D1"))
        self.assertEqual(self.authority.assignment_of(WORK_A),
                         self.held_assignment)

    def test_the_serving_manager_ends_it_and_the_admission_then_replays(self):
        """THE SUPPORTED ENDING, THROUGH THE PROCESS THAT HOLDS THE SESSION.

        The serving manager's pass finds the reserved, approved recovery and
        ends exactly the failed execution's assignment through the PRODUCER's
        own already-held session and the Authority's exact-expect transition.
        The owner's repeated admission then replays that journalled ending --
        with a port that could not have performed it -- and admits. The
        publication worker claims a fresh generation.
        """
        self.approved()
        self.refusal(self.admit, ending=self.sessionless())
        held = self.ported()
        acts = publication_recovery.advance_endings(
            self.jobs, self.control, ending=self.ending_port(),
            exclusion=held["exclusion"], now=ADMITTED)
        self.assertEqual([(one["act"], one["outcome"], one["detail"])
                          for one in acts],
                         [("end-prior-assignment", "performed",
                           {"disposition": "ended"})])
        self.assertIsNone(self.authority.assignment_of(WORK_A))
        ended = publication_recovery.ending_of(self.jobs, "D1")
        self.assertEqual(ended["expect"], self.held_assignment)
        self.assertEqual(ended["answer"]["phase"], "queued")
        # A SECOND TICK FINDS THE RECORD AND ASKS NOBODY.
        self.assertEqual(publication_recovery.advance_endings(
            self.jobs, self.control, ending=self.ending_port(),
            exclusion=held["exclusion"], now=ADMITTED), [])
        answer = self.admit(ending=self.sessionless())
        self.assertEqual(answer["state"], "admitted")
        self.assertEqual(publication_recovery.ending_of(self.jobs, "D1"),
                         ended)
        fresh = self.ready()
        self.assertEqual(fresh["assignment"]["participant"], PUBLISHER)
        self.assertNotEqual(fresh["assignment"]["generation"],
                            self.held_assignment["generation"])

    def test_the_sweep_reaches_that_ending_through_the_publication_seam(self):
        """AND IT IS THE ORDINARY SWEEP THAT DOES IT. The composed publication
        seam carries the serving deployment's ending port, and
        `manager.sweep`'s publication pass performs the ending on its tick --
        nobody drives the pass by hand."""
        self.approved()
        self.refusal(self.admit, ending=self.sessionless())
        operations, stage = self.serving()
        stage.seam.ending = self.ending_port()
        self.assertIs(operations.recovery_publication, stage.seam)
        self.tick(ADMITTED)
        self.assertIsNone(self.authority.assignment_of(WORK_A))
        self.assertEqual(
            publication_recovery.ending_of(self.jobs, "D1")["disposition"],
            "ended")
        self.assertEqual(self.admit(ending=self.sessionless())["state"],
                         "admitted")

    def test_the_serving_pass_ends_nothing_no_admission_reserved(self):
        """AN APPROVAL ALONE ENDS NOTHING. Until an admission has begun and
        reserved the recovery, the pass has nothing to act for, and the
        direct entry refuses rather than ending ahead of one."""
        self.approved()
        held = self.ported()
        self.assertEqual(publication_recovery.advance_endings(
            self.jobs, self.control, ending=self.ending_port(),
            exclusion=held["exclusion"], now=ADMITTED), [])
        caught = self.refusal(
            publication_recovery.end_prior_assignment, self.jobs,
            self.control, decision_id="D1", ending=self.ending_port(),
            exclusion=held["exclusion"], now=ADMITTED)
        self.assertIn("no admission reservation", caught.message)
        self.assertEqual(self.authority.assignment_of(WORK_A),
                         self.held_assignment)

    def test_a_serving_deployment_without_the_holders_session_only_reports(self):
        """A serving deployment that does not serve the holder as a producer
        holds no session for it. The pass reports the typed refusal, ends
        nothing, and mints nothing."""
        from unittest import mock

        self.approved()
        self.refusal(self.admit, ending=self.sessionless())
        held = self.ported()
        with mock.patch.object(self.authority, "session",
                               side_effect=AssertionError("minted")):
            acts = publication_recovery.advance_endings(
                self.jobs, self.control,
                ending=self.ending_port(sessions=lambda who: None),
                exclusion=held["exclusion"], now=ADMITTED)
        self.assertEqual([(one["outcome"], one["detail"]["code"])
                          for one in acts], [("refused", "capability")])
        self.assertEqual(self.authority.assignment_of(WORK_A),
                         self.held_assignment)

    def test_the_deployments_lookup_answers_only_sessions_it_already_holds(self):
        """`stage_execution._held_producer_sessions` is the lookup the pooled
        deployment hands the ending port: it answers the producer session the
        deployment already minted, by participant, and `None` for anybody
        else. It never calls the Authority."""
        from tools import stage_execution

        class Deployment:
            sessions = {"publisher": self.producer_session,
                        "review": self.authority.session(OWNER)}

        held = stage_execution._held_producer_sessions(Deployment())
        self.assertIs(held(PRODUCER), self.producer_session)
        self.assertIsNone(held(OWNER))
        self.assertIsNone(held(PUBLISHER))
        several = type("Several", (), {"sessions": {
            stage_execution.PUBLISHER_PREFIX + PRODUCER:
                self.producer_session}})()
        self.assertIs(
            stage_execution._held_producer_sessions(several)(PRODUCER),
            self.producer_session)
        nothing = type("Idle", (), {"sessions": None})()
        self.assertIsNone(
            stage_execution._held_producer_sessions(nothing)(PRODUCER))

    def test_the_publication_worker_claims_a_fresh_generation(self):
        held = self.ready()
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
        clock that has not started.

        The worker is offered, claims and is activated through its own
        composed operations, and the Job manager has NOT yet adopted that
        admission -- so the stage has a live claimed execution and no durable
        start.
        """
        from tools.integration_worker import prepare_managed_parent

        self.approve_and_admit()
        operations, _stage = self.composed()
        entry = projection.stage_states(self.jobs, operations)[
            self.publication_stage_id]
        job = submission.job_of(self.jobs, self.recovery_job_id)
        operations.admit(entry["attempt"], job)
        operations.claim(entry["attempt"])
        prepare_managed_parent(operations, entry["attempt"], job)
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
        """COUNTED FROM THE WORKER'S OWN ENVELOPE, and nothing it was
        delivered could have named a command.

        The counts are the confined worker's own statement in its completion
        envelope, held to zero by the manager. And the request it was
        delivered is closed: no argv, no command, no environment, no
        credential slot, no provider and no task -- a worker handed one that
        names any of them refuses it.
        """
        import publication_entry
        import baton_worker

        self.ready()
        held = self.published_once()
        self.assertEqual(held["invocations"],
                         {"provider": 0, "verifier": 0, "commands": 0})
        request = publication_execution.publication_request(self.jobs, "D1")
        self.assertEqual(sorted(request),
                         sorted(publication_execution.REQUEST_MEMBERS))
        spelled = json.dumps(request)
        for forbidden in ("argv", "command", "environment", "credential",
                          "provider", "task"):
            self.assertNotIn(forbidden, spelled)
        # NO CREDENTIAL WAS MATERIALIZED OR MOUNTED. `refused_provider` fails
        # the case if the credential provider is ever asked; the composed
        # mount vector carries no credential target either.
        targets = [one["Destination"] for one in self.oci.mounts]
        self.assertFalse([one for one in targets if "credential" in one],
                         targets)
        # AND THE WORKER REFUSES A REQUEST THAT NAMES A COMMAND.
        place = os.path.join(self.root, "widened-request")
        os.mkdir(place)
        with open(os.path.join(place, publication_entry.PUBLICATION_DOCUMENT),
                  "w", encoding="utf-8") as writing:
            json.dump(dict(request, argv=["python3", "-m", "unittest"]),
                      writing)
        with self.assertRaises(baton_worker.WorkerFault) as caught:
            publication_entry.request_document(place)
        self.assertEqual(caught.exception.code, "input")

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
        caught = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertIn("staged no approved original", caught.message)
        self.assertIsNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))

    def test_a_worker_answer_does_not_make_other_bytes_the_approved_ones(self):
        """THE MANAGER MEASURES AFTER THE RUNTIME STOPPED, AND REFUSES.

        The confined worker adopts faithfully and answers `completed`. Then
        the proposal in this attempt's own output root is changed, BEFORE the
        ending -- which is what a worker that kept writing after it answered,
        or one that published an envelope describing other bytes, leaves. The
        ending stops the runtime, this manager measures the tree itself, and
        the adoption is refused with NOTHING frozen.
        """
        from baton_v12.worker_manager import frozen_output_of

        self.ready()
        self.launched()
        self.assertEqual(self.turn(), 0)
        place = os.path.join(self.workspace_of(self.publication_attempt),
                             role_contract.CANDIDATE_OUTPUT, "result.json")
        with open(place, "ab") as handle:
            handle.write(b"x")
        report = self.tick(PUBLISHED)
        spoken = [one for one in report["spoken"]
                  if one["act"] == "conclude"]
        self.assertEqual([one["outcome"] for one in spoken], ["deferred"],
                         report["spoken"])
        self.assertEqual(spoken[0]["detail"]["code"], "digest")
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNotNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNone(frozen_output_of(self.control,
                                           self.publication_attempt))
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])
        self.assertEqual(self.review_offers(), [])

    def test_a_staged_tree_that_changed_is_not_published_by_the_worker(self):
        """AND THE WORKER REFUSES FIRST, WHEN IT CAN SEE IT.

        The staged tree is tampered with between the staging and the launch.
        The confined worker copies what it was delivered, measures its own
        copy against the digest its request bound, and FAULTS rather than
        publish an envelope: there is no completion, the exchange ends
        faulted, and the pass journals the adoption UNCERTAIN.
        """
        self.ready()
        held = self.staged()
        root = held["staged"]["locator"][len("file://"):]
        place = os.path.join(root, role_contract.CANDIDATE_OUTPUT)
        with self.assertRaises(PermissionError):
            open(os.path.join(place, "result.json"), "ab")
        os.chmod(os.path.dirname(root), 0o700)
        os.chmod(root, 0o700)
        os.chmod(place, 0o700)
        os.chmod(os.path.join(place, "result.json"), 0o600)
        with open(os.path.join(place, "result.json"), "ab") as handle:
            handle.write(b"x")
        self.launched()
        self.turn()
        self.assertEqual(self.exchange_view()["terminal"]["ending"],
                         "faulted")
        self.assertFalse(os.path.lexists(os.path.join(
            self.workspace_of(self.publication_attempt), "output.json")))
        caught = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNotNone(publication_execution.hold_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.review_offers(), [])


# -- 5. act three: normal completion, custody and intake ---------------------


class ThePublishedCandidateEntersOrdinaryCustody(PublicationExecutionCase):
    """The Worker Manager's own freeze and intake, over real sealed files."""

    def test_the_frozen_candidate_is_the_approved_original_in_custody(self):
        self.ready()
        self.published_once()
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
        self.assertEqual(len(held["intake"]["artifacts"]), 2)
        self.assertFalse(held["provenance"]["alters_proposal_tree"])
        self.assertNotEqual(held["provenance"]["content_digest"],
                            held["adopted"]["content_digest"])

    def test_the_custody_record_replays_and_freezes_once(self):
        from baton_v12.worker_manager import frozen_output_of

        self.ready()
        self.published_once()
        first = self.collected()
        second = self.collected()
        self.assertEqual(first, second)
        # ONE RUNTIME WAS EVER STARTED, and the one frozen result is the one
        # this record names: the ordinary ending froze it and this act read
        # it, twice, without asking anybody to freeze anything.
        self.assertEqual(len(self.oci.starts), 1)
        self.assertEqual(
            frozen_output_of(self.control,
                             self.publication_attempt)["result_id"],
            first["frozen"]["result_id"])
        before = len(self.oci.vectors)
        self.collected()
        self.assertEqual(len(self.oci.vectors), before)

    def test_a_runtime_nobody_says_stopped_is_not_frozen(self):
        """A freeze describes a tree the writer has stopped changing, and
        only a POSITIVE quiescent observation of the exact runtime says that.

        The worker answers. The ENGINE then accepts the stop order and goes
        on reporting the container running -- so the ending observes no
        quiescence, and nothing is measured, recorded, frozen or collected.
        An answer is not an observation of the writer having stopped.
        """
        from baton_v12.worker_manager import frozen_output_of

        self.ready()
        self.launched()
        self.assertEqual(self.turn(), 0)
        self.engine_hook = lambda argv: (
            self.oci.answer() if argv[1] == "stop" else None)
        report = self.tick(PUBLISHED)
        spoken = [one for one in report["spoken"]
                  if one["act"] == "conclude"]
        self.assertEqual([one["outcome"] for one in spoken], ["deferred"],
                         report["spoken"])
        self.assertEqual(spoken[0]["detail"]["code"], "quiescence-unknown")
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNone(frozen_output_of(self.control,
                                           self.publication_attempt))
        caught = self.refusal(self.collected)
        self.assertIn("adopted nothing", caught.message)
        self.assertIsNone(publication_execution.custody_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.review_offers(), [])

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
        self.ready()
        steps.append(("claimed", self.gate()))
        self.staged()
        steps.append(("staged", self.gate()))
        self.launched()
        steps.append(("launched", self.gate()))
        self.assertEqual(self.turn(), 0)
        steps.append(("answered", self.gate()))
        self.tick(PUBLISHED)
        self.assertIsNotNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        steps.append(("published", self.gate()))
        self.collected()
        steps.append(("custody", self.gate()))
        for where, gate in steps:
            with self.subTest(where=where):
                self.assertFalse(gate["open"], where)
                self.assertFalse(gate["runnable"], where)
                self.assertEqual(gate["reason"],
                                 publication_execution.GATE_UNAVAILABLE)
                self.assertEqual(self.review_offers(), [], where)
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

    def test_no_launch_is_committed_without_a_placeable_deadline_ahead(self):
        """MISSING OR INVALID FAILS CLOSED ON THE HOST, before a container
        exists. A bound with no instant, an instant this manager cannot
        place, or one that is not still ahead commits no intent and starts
        nothing -- there is no default bound to launch under."""
        from unittest import mock

        self.ready()
        self.staged()
        honest = publication_execution.deadline_of(self.jobs, "D1",
                                                   now=PUBLISHED)
        for wrong in (None, "", "soon", "2026-09-02T00:26:00", PUBLISHED,
                      CLAIMED):
            with self.subTest(deadline_at=wrong):
                with mock.patch.object(
                        publication_execution, "_within_deadline",
                        return_value=dict(honest, deadline_at=wrong)):
                    caught = self.refusal(
                        publication_execution.prepare_launch, self.jobs,
                        self.seam(), decision_id="D1", now=PUBLISHED)
                self.assertEqual((caught.category, caught.code),
                                 ("policy", "denied"))
                self.assertIn("no default bound", caught.message)
                self.assertIsNone(publication_execution.launch_of(
                    self.jobs, self.recovery_job_id))
        self.assertEqual(len(self.oci.starts), 0)
        self.assertIsNone(publication_execution.publication_request(
            self.jobs, "D1"))

    def test_the_worker_is_delivered_the_absolute_instant_and_stops_at_it(self):
        """THE WORKER'S OWN ENFORCEMENT, at its own boundary.

        The pinned request carries the ABSOLUTE instant the persisted stage
        admission derives and no remaining number. A worker whose clock is
        already past it starts no copy, publishes no envelope and ends its
        command FAULTED -- which nothing can read a publication out of.
        """
        from datetime import datetime

        self.ready()
        self.launched()
        request = publication_execution.publication_request(self.jobs, "D1")
        deadline = publication_execution.deadline_of(self.jobs, "D1",
                                                     now=PUBLISHED)
        self.assertEqual(request["deadline"]["deadline_at"],
                         deadline["deadline_at"])
        self.assertEqual(request["deadline"]["origin"], deadline["origin"])
        self.assertIs(request["deadline"]["restart_resets"], False)
        self.assertNotIn("remaining", json.dumps(request))
        late = datetime.fromisoformat(LATE.replace("Z", "+00:00")).timestamp()
        self.turn(clock=lambda: late)
        self.assertEqual(self.exchange_view()["terminal"]["ending"],
                         "faulted")
        place = self.workspace_of(self.publication_attempt)
        self.assertFalse(os.path.lexists(os.path.join(place, "output.json")))
        self.assertFalse(os.path.lexists(
            os.path.join(place, role_contract.CANDIDATE_OUTPUT)))
        caught = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))

    def test_a_hung_adoption_is_ended_at_the_instant_and_observed_gone(self):
        """A BLOCKED COPY IS INTERRUPTED, NOT POLLED BETWEEN STEPS.

        The adoption child is replaced by a real process that never finishes,
        ignores SIGTERM and starts a second process that also ignores it.
        With one real second left of the absolute bound, the worker's
        supervisor ends the WHOLE process group, observes it empty, and
        faults. The command ends; nothing is published; no process survives.
        """
        import subprocess
        import time
        from datetime import datetime

        self.ready()
        self.launched()
        marker = "publication-hang-" + os.path.basename(self.root)
        script = os.path.join(self.root, "hang.py")
        with open(script, "w", encoding="utf-8") as writing:
            writing.write(
                "import signal, subprocess, sys, time\n"
                "signal.signal(signal.SIGTERM, signal.SIG_IGN)\n"
                "subprocess.Popen([sys.executable, '-c', 'import signal,"
                "time\\nsignal.signal(signal.SIGTERM, signal.SIG_IGN)"
                "\\ntime.sleep(300)', '" + marker + "'])\n"
                "time.sleep(300)\n")
        hang = os.path.join(self.root, "hang")
        with open(hang, "w", encoding="utf-8") as writing:
            writing.write("#!/bin/sh\nexec " + sys.executable + " "
                          + script + " " + marker + "\n")
        os.chmod(hang, 0o755)
        request = publication_execution.publication_request(self.jobs, "D1")
        bound = datetime.fromisoformat(request["deadline"]["deadline_at"]
                                       .replace("Z", "+00:00")).timestamp()
        begun = time.monotonic()
        self.turn(executable=hang,
                  clock=lambda: bound - 1.0 + (time.monotonic() - begun))
        elapsed = time.monotonic() - begun
        self.assertGreaterEqual(elapsed, 1.0)
        self.assertLess(elapsed, 15.0)
        self.assertEqual(self.exchange_view()["terminal"]["ending"],
                         "faulted")
        self.assertFalse(os.path.lexists(os.path.join(
            self.workspace_of(self.publication_attempt), "output.json")))
        survivors = subprocess.run(["pgrep", "-f", marker],
                                   capture_output=True, text=True)
        self.assertEqual(survivors.stdout.strip(), "", survivors.stdout)
        caught = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIsNotNone(publication_execution.hold_of(
            self.jobs, self.recovery_job_id))

    def test_a_request_without_a_placeable_deadline_starts_no_child(self):
        """MISSING OR INVALID FAILS CLOSED, at the worker too. There is no
        default bound: a request naming no instant, a zone-less wall time or
        text that is not a time is refused before any child exists."""
        import baton_worker
        import publication_entry

        self.ready()
        self.launched()
        request = publication_execution.publication_request(self.jobs, "D1")
        for index, wrong in enumerate((None, "", "2026-09-02T00:26:00",
                                       "soon", 900)):
            with self.subTest(deadline=wrong):
                place = os.path.join(self.root, f"request-{index}")
                os.mkdir(place)
                widened = dict(request, deadline=dict(request["deadline"],
                                                      deadline_at=wrong))
                with open(os.path.join(
                        place, publication_entry.PUBLICATION_DOCUMENT),
                        "w", encoding="utf-8") as writing:
                    json.dump(widened, writing)
                with self.assertRaises(baton_worker.WorkerFault) as caught:
                    publication_entry.request_document(place)
                self.assertEqual(caught.exception.code, "input")
                self.assertIn("deadline", caught.exception.message)
        place = os.path.join(self.root, "request-resetting")
        os.mkdir(place)
        with open(os.path.join(place, publication_entry.PUBLICATION_DOCUMENT),
                  "w", encoding="utf-8") as writing:
            json.dump(dict(request, deadline=dict(request["deadline"],
                                                  restart_resets=True)),
                      writing)
        with self.assertRaises(baton_worker.WorkerFault) as caught:
            publication_entry.request_document(place)
        self.assertEqual(caught.exception.code, "input")
        self.assertIn("absolute", caught.exception.message)




# -- 8. uncertainty, lost replies and the restart cuts -----------------------


class UncertaintyHoldsAndNeverPublishesTwice(PublicationExecutionCase):
    """A lost or unanswered adoption is reconciled, not retried."""

    def test_a_sweep_while_the_adoption_is_in_flight_starts_nothing(self):
        """ONE LAUNCH. Every later tick finds the journalled runtime start
        and the attached runtime, and starts nothing; the pass reports the
        adoption in flight and journals no uncertainty about a runtime that
        is simply still running."""
        self.ready()
        self.launched()
        for _ in range(3):
            self.tick(PUBLISHED)
        self.assertEqual(len(self.oci.starts), 1)
        self.assertEqual(len(self.oci.activations), 1)
        caught = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(caught.code, "precondition")
        self.assertIn("in flight", caught.message)
        self.assertIsNone(publication_execution.hold_of(
            self.jobs, self.recovery_job_id))
        held = publication_execution.publication_readiness(self.jobs, "D1")
        self.assertTrue(held["launched"])
        self.assertFalse(held["uncertain"])
        self.assertEqual(held["owed"], "publish")

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

    def test_a_lost_start_reply_is_reconciled_and_never_started_twice(self):
        """THE MANAGER DIES AFTER THE ENGINE STARTED THE CONTAINER and before
        it could record the reply. The intent is durable, the runtime start
        is journalled, and the next incarnation asks the ENGINE for the exact
        runtime by its labels and attaches to it. No second container is
        composed and none is activated; the adoption then completes once."""
        self.ready()
        fired = []

        def lose(argv):
            if argv[1] == "start" and not fired:
                fired.append(list(argv))
                self.oci(argv)
                raise KeyboardInterrupt("the manager stopped after the "
                                        "engine acted")
            return None

        self.engine_hook = lose
        with self.assertRaises(KeyboardInterrupt):
            for _ in range(4):
                self.tick(PUBLISHED)
        self.engine_hook = None
        self.assertIsNotNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.restarted()
        self.launched()
        self.assertEqual(len(self.oci.starts), 1)
        self.assertEqual(len(self.oci.activations), 1)
        state = attempt_runtime_of(self.control, self.publication_attempt)
        self.assertEqual(state["runtime_id"], self.oci.runtime_id)
        self.assertEqual(self.turn(), 0)
        self.tick(PUBLISHED)
        self.assertEqual(
            publication_execution.result_of(
                self.jobs, self.recovery_job_id)["outcome"], "published")
        self.assertEqual(len(self.oci.starts), 1)

    def test_a_death_between_the_intent_and_the_start_launches_once(self):
        """AND THE EARLIER CUT: the intent committed, the manager died before
        any runtime start was requested. The next incarnation replays the
        SAME intent -- same attempt, same absolute deadline -- and performs
        the one start that never happened."""
        self.ready()
        prepared = publication_execution.prepare_launch(
            self.jobs, self.seam(), decision_id="D1", now=PUBLISHED)
        self.assertEqual(len(self.oci.starts), 0)
        self.restarted()
        self.launched(now=LATE_IN_BOUND)
        self.assertEqual(len(self.oci.starts), 1)
        self.assertEqual(
            publication_execution.launch_of(self.jobs, self.recovery_job_id),
            prepared["intent"])
        request = publication_execution.publication_request(self.jobs, "D1")
        self.assertEqual(request["deadline"]["deadline_at"],
                         prepared["intent"]["deadline"]["deadline_at"])

    def test_a_runtime_the_host_lost_is_journalled_uncertain_and_holds(self):
        """HOST LOSS. The container is gone -- removed underneath the manager
        -- and the worker never answered. The runtime owner observes the
        exact identity ABSENT; nothing was published and nothing says the
        writer finished, so the adoption is journalled UNCERTAIN, with the
        staged input, the original and the intent all retained."""
        self.ready()
        self.launched()
        self.oci(["docker", "rm", "--force", self.oci.runtime_id])
        self.tick(PUBLISHED)
        state = attempt_runtime_of(self.control, self.publication_attempt)
        self.assertEqual(state["execution_runtime"], "destroyed")
        caught = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIn("UNCERTAIN", caught.message)
        self.assertIsNotNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))
        held = publication_execution.hold_of(self.jobs, self.recovery_job_id)
        self.assertEqual(held["outcome"], "unknown")
        self.assertEqual(held["attempt_id"], self.publication_attempt)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])

    def test_an_engine_that_cannot_be_asked_is_not_a_runtime_that_ended(self):
        """AND THE OTHER HALF OF HOST LOSS: the engine cannot be reached, so
        nobody can say whether the launched runtime exists. That is not
        cessation and it is not a failure: nothing is recorded as published,
        nothing is relaunched, and no deadline or silence is read as an
        ending."""
        self.ready()
        self.launched()
        self.engine_hook = lambda argv: (
            {"status": 125, "stdout": "",
             "stderr": "Cannot connect to the Docker daemon"}
            if argv[1] in ("ps", "inspect") else None)
        for _ in range(2):
            self.tick(PUBLISHED)
        self.assertEqual(len(self.oci.starts), 1)
        state = attempt_runtime_of(self.control, self.publication_attempt)
        self.assertNotIn(state["execution_runtime"],
                         ("quiescent", "destroyed"))
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertFalse(self.gate()["open"])
        self.assertEqual(self.review_offers(), [])

    def test_no_second_adoption_is_started_while_the_first_is_unaccounted(self):
        self.ready()
        self.launched()
        self.oci(["docker", "rm", "--force", self.oci.runtime_id])
        self.tick(PUBLISHED)
        self.refusal(publication_execution.publish, self.jobs, self.seam(),
                     decision_id="D1", now=PUBLISHED)
        again = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(again.code, "quiescence-unknown")
        self.assertIn("No second adoption is started", again.message)
        relaunch = self.refusal(
            publication_execution.prepare_launch, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(relaunch.code, "quiescence-unknown")
        self.assertIn("no second launch", relaunch.message)
        for _ in range(3):
            self.tick(PUBLISHED)
        self.assertEqual(len(self.oci.starts), 1)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNotNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])

    def test_a_worker_whose_copy_failed_publishes_nothing_and_holds(self):
        """The adoption child ends nonzero. The worker faults rather than
        publish, and the pass journals exactly what the exchange said."""
        self.ready()
        self.launched()
        self.turn(executable="/bin/false")
        self.assertEqual(self.exchange_view()["terminal"]["ending"],
                         "faulted")
        caught = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertEqual(
            publication_execution.hold_of(
                self.jobs, self.recovery_job_id)["observed"],
            "the confined worker's exchange ended faulted and published "
            "nothing")

    def test_an_uncertain_adoption_opens_no_gate_and_offers_no_review(self):
        self.ready()
        self.launched()
        self.turn(executable="/bin/false")
        self.refusal(publication_execution.publish, self.jobs, self.seam(),
                     decision_id="D1", now=PUBLISHED)
        gate = self.gate()
        self.assertFalse(gate["open"])
        self.assertEqual(self.review_offers(), [])
        held = publication_execution.publication_readiness(self.jobs, "D1")
        self.assertTrue(held["uncertain"])
        self.assertIsNone(held["owed"])
        self.assertEqual(held["review"], "blocked")
        self.assertEqual(
            publication_execution.advance_publication(
                self.jobs, self.seam(), now=PUBLISHED)["acts"], [])

    def test_a_worker_that_claims_a_model_or_a_verifier_is_denied(self):
        """THE COUNT IS A CHECKED FACT. A worker whose own envelope declares
        one provider invocation is not the no-provider worker this recovery
        reserved capacity for: its adoption is denied and nothing is frozen,
        even though the bytes it wrote are the approved ones."""
        import publication_entry
        from baton_v12.worker_manager import frozen_output_of

        class Lying(publication_entry.PublicationAgent):
            def work(self, seen, declared):
                answer = super().work(seen, declared)
                for one in answer["outputs"]:
                    one["result_metadata"][publication_entry.METADATA_KEY][
                        "provider_invocations"] = 1
                return answer

        self.ready()
        self.launched()
        self.assertEqual(self.turn(agent_type=Lying), 0)
        report = self.tick(PUBLISHED)
        spoken = [one for one in report["spoken"]
                  if one["act"] == "conclude"]
        self.assertEqual([one["outcome"] for one in spoken], ["deferred"],
                         report["spoken"])
        self.assertEqual(spoken[0]["detail"]["category"], "policy")
        self.assertIn("ZERO models", spoken[0]["detail"]["message"])
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNone(frozen_output_of(self.control,
                                           self.publication_attempt))

    def test_every_act_replays_across_a_restart_without_a_second_effect(self):
        """THE WHOLE PATH, RE-ENTERED ON A SECOND INCARNATION. Each act finds
        its own committed record and answers with it, so nothing is staged,
        launched, published, frozen or handed off twice."""
        from baton_v12.job_manager import JobStore

        first = self.whole_path()
        vectors = len(self.oci.vectors)
        reopened = JobStore.open(self.jobs.database, authority_uuid=AUTHORITY,
                                 incarnation="publication-restart",
                                 clock=self.clock)
        self.addCleanup(reopened.close)
        _operations, stage = self.restarted()
        seam = stage.seam
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
        for _ in range(2):
            self.tick(LATE)
        self.assertEqual(len(self.oci.starts), 1)
        self.assertEqual(
            self.jobs._connection.execute(
                "SELECT count(*) FROM operations WHERE kind = ?",
                (publication_execution.LAUNCH_KIND,)).fetchone()[0], 1)
        self.assertEqual(
            publication_execution.handoff_of(
                reopened, self.recovery_job_id), first)
        del vectors


# -- 9. cancellation, expiry and the evidence they retain --------------------


class CancellationStopsNewEffectsAndRetainsEverything(
        PublicationExecutionCase):
    """A fence stops the next act; nothing already recorded is undone."""

    def test_a_cancelled_recovery_stops_the_next_act_and_keeps_the_rest(self):
        self.ready()
        staged = self.staged()
        cancellation.request(self.jobs, job_id=self.recovery_job_id,
                             reason="the owner stops this recovery")
        caught = self.refusal(
            publication_execution.prepare_launch, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertIn("admits nothing more", caught.message)
        self.assertIn("retained", caught.message)
        for _ in range(3):
            self.tick(PUBLISHED)
        self.assertEqual(len(self.oci.starts), 0)
        self.assertIsNone(publication_execution.launch_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(
            publication_execution.staging_of(self.jobs,
                                             self.recovery_job_id), staged)
        self.assertIsNotNone(publication_recovery.admission_of(self.jobs,
                                                               "D1"))
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])
        self.assertFalse(self.gate()["open"])
        self.assertEqual(self.review_offers(), [])

    def test_a_cancellation_in_flight_stops_the_runtime_through_its_owner(self):
        """CANCELLED WHILE THE CONFINED WORKER IS RUNNING. The fence is
        journalled, the ordinary cancellation pass orders the exact runtime
        to stop through the engine owner, and the stop is OBSERVED. Nothing
        is published; what the worker had written stays where it is."""
        self.ready()
        self.launched()
        cancellation.request(self.jobs, job_id=self.recovery_job_id,
                             reason="the owner stops this recovery")
        for _ in range(3):
            self.tick(PUBLISHED)
        stops = [one for one in self.oci.vectors if one[1] == "stop"]
        self.assertTrue(stops, self.oci.vectors[-6:])
        state = attempt_runtime_of(self.control, self.publication_attempt)
        self.assertEqual(state["execution_runtime"], "quiescent")
        self.assertEqual(len(self.oci.starts), 1)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNotNone(publication_execution.staging_of(
            self.jobs, self.recovery_job_id))
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
        closed = job_control.closed_of(self.jobs, self.recovery_job_id, LATE,
                                       any_stage=True)
        first = closed["first"]
        job_control.expire(self.jobs, job_id=self.recovery_job_id,
                           trigger=first["trigger"],
                           stage_id=first["stage_id"],
                           deadline_at=first["deadline_at"], observed_at=LATE)
        caught = self.refusal(
            publication_execution.prepare_launch, self.jobs, self.seam(),
            decision_id="D1", now=LATE)
        self.assertIn("admits nothing more", caught.message)
        for _ in range(3):
            self.tick(LATE)
        self.assertEqual(len(self.oci.starts), 0)
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.review_offers(), [])

    def test_the_host_stops_a_running_adoption_at_the_absolute_bound(self):
        """HOST ENFORCEMENT, COVERING WORKER LOSS. The confined worker is
        given its command and never answers -- hung, lost or lying about the
        time. When the clock reaches the publication stage's absolute bound,
        the manager's own control evaluation journals the expiry and the
        ordinary cancellation pass orders the exact runtime to stop through
        the engine owner. The stop is observed; nothing is published."""
        self.ready()
        self.launched()
        deadline = publication_execution.deadline_of(self.jobs, "D1",
                                                     now=PUBLISHED)
        self.assertFalse(deadline["reached"])
        for _ in range(3):
            self.tick(LATE)
        self.assertTrue(publication_execution.deadline_of(
            self.jobs, "D1", now=LATE)["reached"])
        self.assertTrue(cancellation.fence_of(self.jobs,
                                              self.recovery_job_id))
        stops = [one for one in self.oci.vectors if one[1] == "stop"]
        self.assertTrue(stops, self.oci.vectors[-6:])
        state = attempt_runtime_of(self.control, self.publication_attempt)
        self.assertEqual(state["execution_runtime"], "quiescent")
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertEqual(self.review_offers(), [])

    def test_a_reached_bound_is_not_read_as_cessation(self):
        """THE DEADLINE PASSING IS NOT EVIDENCE THAT ANYTHING STOPPED. The
        engine accepts the stop order and goes on reporting the container
        running: the runtime is not recorded stopped, the adoption is not
        recorded at all, and review stays shut."""
        self.ready()
        self.launched()
        self.engine_hook = lambda argv: (
            self.oci.answer() if argv[1] == "stop" else None)
        for _ in range(3):
            self.tick(LATE)
        state = attempt_runtime_of(self.control, self.publication_attempt)
        self.assertNotIn(state["execution_runtime"],
                         ("quiescent", "destroyed"))
        self.assertNotIn(state["cleanup"], ("complete", "retained"))
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertFalse(self.gate()["open"])
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
        """THE SEPARATE BOUND IS ENFORCED ON REAL BYTES, by this manager's
        own measurement after the runtime stopped. The provenance output
        holds more than the approved 16384-byte descriptor allows when the
        ending measures it, and the adoption is refused."""
        from baton_v12.worker_manager import frozen_output_of

        self.ready()
        self.launched()
        self.assertEqual(self.turn(), 0)
        bound = publication_recovery.PROVENANCE_OUTPUT
        into = os.path.join(self.workspace_of(self.publication_attempt),
                            bound["path"])
        with open(os.path.join(into, "big.json"), "wb") as handle:
            handle.write(b"{}" + b" " * (bound["constraints"]["max_bytes"]
                                         + 1))
        report = self.tick(PUBLISHED)
        spoken = [one for one in report["spoken"]
                  if one["act"] == "conclude"]
        self.assertEqual([one["outcome"] for one in spoken], ["deferred"],
                         report["spoken"])
        self.assertEqual(spoken[0]["detail"]["code"], "limit")
        self.assertIn("bounded output is bounded",
                      spoken[0]["detail"]["message"])
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertIsNone(frozen_output_of(self.control,
                                           self.publication_attempt))


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


class TheWorkerAndTheManagerSpellOneContract(PublicationExecutionCase):
    """A worker in a container cannot import the manager's package, so the
    request's schema, its members, its fixed name and the metadata key are
    spelled twice. These hold the two spellings equal."""

    def test_the_request_contract_is_spelled_the_same_on_both_sides(self):
        import publication_entry

        self.assertEqual(publication_entry.REQUEST_SCHEMA,
                         publication_execution.REQUEST_SCHEMA)
        self.assertEqual(publication_entry.REQUEST_MEMBERS,
                         publication_execution.REQUEST_MEMBERS)
        self.assertEqual(publication_entry.PUBLICATION_DOCUMENT,
                         publication_execution.REQUEST_DOCUMENT)
        self.assertEqual(publication_entry.PUBLICATION_DOCUMENT,
                         single_worker.PUBLICATION_DOCUMENT)
        self.assertEqual(publication_entry.METADATA_KEY,
                         publication_execution.METADATA_KEY)
        self.assertEqual(publication_entry.SOURCE_DESTINATION,
                         single_worker.SOURCE_DESTINATION)
        self.assertEqual(single_worker.PUBLICATION_ROLE,
                         documents.PUBLICATION_STAGE)

    def test_the_delivered_request_is_exactly_what_the_worker_accepts(self):
        """The document the lifecycle pinned into the read-only input root is
        read back by the worker's own reader, byte for byte the canonical
        composition of the committed records."""
        import publication_entry

        self.ready()
        self.launched()
        inputs = os.path.join(self.storage, self.publication_attempt,
                              "inputs")
        place = os.path.join(inputs, publication_entry.PUBLICATION_DOCUMENT)
        with open(place, "rb") as reading:
            delivered = reading.read()
        request = publication_execution.publication_request(self.jobs, "D1")
        self.assertEqual(delivered, json.dumps(
            request, sort_keys=True, separators=(",", ":")).encode("utf-8"))
        self.assertEqual(os.stat(place).st_mode & 0o222, 0)
        self.assertEqual(publication_entry.request_document(inputs), request)
        self.assertEqual(request["attempt_id"], self.publication_attempt)

    def test_the_staged_root_is_bound_read_only_and_the_original_never_is(self):
        """THE CONTAINMENT, read off the composed mount vector: the staged
        root is the nominated source at `/input/source`, read-only; the
        attempt's own output is the one writable root; and the ORIGINAL
        attempt's output root is mounted nowhere."""
        self.ready()
        self.launched()
        mounts = {one["Destination"]: one for one in self.oci.mounts}
        staging = publication_execution.staging_of(self.jobs,
                                                   self.recovery_job_id)
        staged = staging["staged"]["locator"][len("file://"):]
        self.assertEqual(mounts["/input/source"]["Source"],
                         os.path.dirname(staged))
        self.assertFalse(mounts["/input/source"]["RW"])
        self.assertFalse(mounts["/input"]["RW"])
        self.assertTrue(mounts["/output"]["RW"])
        self.assertEqual(mounts["/output"]["Source"],
                         self.workspace_of(self.publication_attempt))
        original = os.path.realpath(self.roots["workspace"])
        for one in self.oci.mounts:
            source = os.path.realpath(one["Source"])
            self.assertFalse(source == original
                             or source.startswith(original + os.sep)
                             or original.startswith(source + os.sep),
                             one)
        # AND THE STAGED TREE IS NOT WRITABLE ON THE HOST EITHER.
        with self.assertRaises(PermissionError):
            open(os.path.join(staged, "intruder"), "wb")


class OneTickOwesOneActAndDerivesItFromRows(PublicationExecutionCase):
    """`advance_publication`, driven to completion one act at a time."""

    def test_the_ordinary_sweep_alone_carries_a_recovery_to_one_review_offer(self):
        """THE CONNECTED PATH, DRIVEN BY NOTHING BUT TICKS.

        The owner's admission stops at the held assignment. From there the
        ONLY things that happen are ordinary `manager.sweep` ticks over the
        composed deployment, the owner's repeated admission, and the confined
        worker's own turn: the serving manager ends the producer's assignment
        through its held session; the publication worker is offered, claims a
        fresh generation, stages the original read-only, commits its intent,
        starts, adopts, is stopped and measured, frozen, collected and
        cleaned up; the pass binds custody and hands off; and exactly one
        review offer becomes owed. No act is called by hand.
        """
        from tools.publication_ports import PriorAssignment

        sessionless = PriorAssignment(self.authority,
                                      checkpoint1.CURRENT["identity"])
        self.approved()
        self.refusal(self.admit, ending=sessionless)
        operations, stage = self.serving()
        stage.seam.ending = self.ending_port()
        self.tick(ADMITTED)
        self.assertIsNone(self.authority.assignment_of(WORK_A))
        self.assertEqual(self.admit(ending=sessionless)["state"], "admitted")
        self.assertEqual(self.review_offers(), [])
        for _ in range(4):
            self.tick(CLAIMED)
            entry = projection.stage_states(self.jobs, operations)[
                self.publication_stage_id]
            if (entry.get("exchange") or {}).get("command") is not None:
                break
        self.publication_attempt = entry["attempt"]["attempt_id"]
        self.assertIsNotNone(self.exchange_view()["command"])
        self.assertEqual(self.review_offers(), [])
        self.assertEqual(self.turn(), 0)
        for _ in range(3):
            self.tick(PUBLISHED)
        held = publication_execution.publication_readiness(self.jobs, "D1")
        self.assertEqual(
            {one: held[one] for one in ("staged", "launched", "published",
                                        "custody", "handed_off",
                                        "uncertain", "owed")},
            {"staged": True, "launched": True, "published": True,
             "custody": True, "handed_off": True, "uncertain": False,
             "owed": None})
        self.assertEqual(len(self.oci.starts), 1)
        state = attempt_runtime_of(self.control, self.publication_attempt)
        self.assertEqual(state["execution_runtime"], "destroyed")
        self.assertIn(state["cleanup"], ("complete", "retained"))
        self.assertTrue(self.gate()["open"])
        self.assertEqual(len(self.review_offers()), 1)
        self.assertEqual(self.original_bytes(), self.original["tree_digest"])

    def test_the_pass_performs_its_acts_in_order_and_never_launches(self):
        """ONE TICK, ONE ACT, AND THE LAUNCH IS NOT ONE OF THEM. The pass
        stages, accounts for the adoption, binds custody and hands off; the
        confined worker itself is started by its own lifecycle. While that
        launch is in flight the pass says so and performs nothing."""
        self.ready()

        def advance():
            held = publication_execution.advance_publication(
                self.jobs, self.seam(), now=PUBLISHED)
            self.assertLessEqual(len(held["acts"]), 1)
            return [(one["act"], one["outcome"]) for one in held["acts"]]

        self.assertEqual(advance(), [("stage", "performed")])
        self.assertEqual(advance(), [("publish", "held")])
        self.assertEqual(len(self.oci.starts), 0)
        self.launched()
        self.assertEqual(advance(), [("publish", "held")])
        self.assertEqual(self.turn(), 0)
        self.tick(PUBLISHED)
        self.assertEqual(advance(), [("custody", "performed")])
        self.assertEqual(advance(), [("hand-off", "performed")])
        self.assertEqual(advance(), [])
        self.assertEqual(len(self.oci.starts), 1)
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
        """The publication really completed -- adopted, frozen, collected,
        released and cleaned up by the ordinary ending -- and this manager
        has bound no custody RECORD to it. The gate is shut, the binding says
        which ones are missing, and the sweep owes no review offer."""
        from baton_v12.worker_manager import frozen_output_of
        from baton_v12.worker_manager.intake import intake_receipt_of

        self.ready()
        self.published_once()
        self.assertIsNotNone(frozen_output_of(self.control,
                                              self.publication_attempt))
        self.assertIsNotNone(intake_receipt_of(self.control,
                                               self.publication_attempt))
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
        self.published_once()
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
# the first sweep after approval issues ZERO review offers. An instance that
# HAS installed one -- through `tools.pool` and the bootstrap repeat -- is
# section 15b's.

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


# -- 15a. the bound covers the whole publication ------------------------------
#
# REVIEW 2026-11-23T18-55-03Z R2. The worker checked its absolute deadline
# only while the copy child was running: a copy observed finished AFTER the
# instant was reported on time, and the measurement and the completion
# envelope -- which are the ordinary worker's and run after `work` returns --
# were bounded by nothing. A real worker-exchange probe answered `completed`
# four minutes past its delivered bound.
#
# THE FIXTURE CLOCK IS THE WORKER'S CLOCK HERE, moved from inside the step a
# case is about, so "the instant passed during the measurement" is a fact
# about where the clock was read and not about a sleep. The one case that is
# about a BLOCKED step runs the worker as a real child process on the real
# clock, because that is the only place the watch's ending of its own process
# can be observed.


class TheBoundCoversMeasurementAndCompletion(PublicationExecutionCase):
    """No successful completion after the instant, whichever step crossed it."""

    def late(self):
        self.instants.append(LATE)

    def crossing(self, name, *, after=0):
        """Move the worker's clock past the bound from inside the ordinary
        worker's `name`, on the call numbered `after` (from zero)."""
        import baton_worker

        real = getattr(baton_worker, name)
        calls = []

        def crossed(*operands, **named):
            calls.append(len(calls))
            if len(calls) - 1 == after:
                self.late()
            return real(*operands, **named)

        setattr(baton_worker, name, crossed)
        self.addCleanup(setattr, baton_worker, name, real)
        return calls

    def nothing_was_published(self):
        """THE MANAGER'S SIDE: a faulted exchange is held, never adopted."""
        terminal = self.exchange_view()["terminal"]
        self.assertEqual((terminal["ending"], terminal["fault_code"],
                          terminal["disposition"]),
                         ("faulted", "agent", None))
        self.assertEqual(terminal["answered"], ["describe"])
        caught = self.refusal(
            publication_execution.publish, self.jobs, self.seam(),
            decision_id="D1", now=PUBLISHED)
        self.assertEqual(caught.code, "quiescence-unknown")
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.serving()
        for _ in range(3):
            manager.sweep(self.jobs, self._composed[0], now=PUBLISHED)
        self.assertIsNone(publication_execution.custody_of(
            self.jobs, self.recovery_job_id))
        self.assertFalse(self.gate()["open"])
        self.assertEqual(self.review_offers(), [])

    # -- the supervisor ------------------------------------------------------

    def supervised_over(self, instants, status=0):
        """`supervised` over a child that has already finished, with the
        clock answering `instants` in order."""
        from types import SimpleNamespace
        from unittest import mock

        import publication_entry

        child = SimpleNamespace(pid=2 ** 30, returncode=status,
                                poll=lambda: status)
        clock = iter(instants)
        with mock.patch.object(publication_entry.subprocess, "Popen",
                               return_value=child), \
                mock.patch.object(publication_entry, "_excluded",
                                  return_value=True):
            return publication_entry.supervised(
                ["ignored"], "1970-01-01T00:00:01Z",
                clock=lambda: next(clock))

    def test_a_copy_that_finished_after_the_instant_did_not_finish_in_time(self):
        """THE COMPLETION-VERSUS-EXPIRY RACE. The child is already finished
        on the first look, so the loop that used to be the only place the
        clock was compared never runs; the instant its ending was observed
        is past the bound, and that is a timeout with no status to trust."""
        ran = self.supervised_over([0.0, 0.5, 2.0])
        self.assertEqual((ran["timed_out"], ran["status"], ran["started"],
                          ran["ended_at"]), (True, None, True, 2.0))
        # EXACTLY AT THE INSTANT IS NOT BEFORE IT.
        ran = self.supervised_over([0.0, 0.5, 1.0])
        self.assertTrue(ran["timed_out"])
        # AND THE CONTROL: finished inside the bound keeps its status.
        ran = self.supervised_over([0.0, 0.5, 0.75, 0.8])
        self.assertEqual((ran["timed_out"], ran["status"]), (False, 0))
        ran = self.supervised_over([0.0, 0.5, 0.75, 0.8], status=3)
        self.assertEqual((ran["timed_out"], ran["status"]), (False, 3))

    # -- the measurement and the envelope -------------------------------------

    def test_a_measurement_that_crosses_the_instant_publishes_nothing(self):
        """THE WORKER'S OWN MEASUREMENT, inside `work`."""
        self.ready()
        self.launched()
        calls = self.crossing("measured", after=0)
        self.assertEqual(self.turn(), 1)
        # THE COPY RAN AND COMPLETED IN TIME; what crossed is the measurement,
        # and nothing was measured a second time on the way to a completion.
        self.assertEqual(len(calls), 1)
        place = self.workspace_of(self.publication_attempt)
        self.assertTrue(os.path.isdir(
            os.path.join(place, role_contract.CANDIDATE_OUTPUT)))
        self.assertFalse(os.path.lexists(os.path.join(place, "output.json")))
        self.nothing_was_published()

    def test_the_ordinary_workers_measurement_is_bounded_too(self):
        """AFTER `work` RETURNED. The first measurement is this agent's and
        is in time; the second is the ordinary worker's own, over the same
        tree, and the instant passes inside it. The completion envelope is a
        commit point and is not written."""
        self.ready()
        self.launched()
        calls = self.crossing("measured", after=1)
        self.assertEqual(self.turn(), 1)
        self.assertGreaterEqual(len(calls), 2)
        place = self.workspace_of(self.publication_attempt)
        self.assertFalse(os.path.lexists(os.path.join(place, "output.json")))
        self.nothing_was_published()

    def test_an_envelope_alone_is_never_a_publication(self):
        """THE SECOND COMMIT POINT. The envelope is written in time and the
        instant passes while it is read back, before the `answered` state.
        The worker faults; the envelope is on disk; and the manager records
        no adoption from it, because what it adopts on is the terminal."""
        self.ready()
        self.launched()
        self.crossing("_published_manifest_digest", after=0)
        self.assertEqual(self.turn(), 1)
        place = self.workspace_of(self.publication_attempt)
        self.assertTrue(os.path.isfile(os.path.join(place, "output.json")))
        self.nothing_was_published()

    def test_the_gate_asks_nothing_of_an_agent_that_has_no_bound(self):
        """EVERY OTHER WORKER IS UNCHANGED: an agent that defines no
        `may_complete` is asked nothing at either commit point."""
        import baton_worker
        import publication_entry

        self.assertIsNone(baton_worker._permitted(object()))
        # AND THIS AGENT, BEFORE ITS `work` MADE A BOUND, MAY NOT COMPLETE:
        # there is no default bound and no completion without one.
        fresh = publication_entry.PublicationAgent(watch=False)
        self.assertFalse(fresh.may_complete())
        with self.assertRaises(baton_worker.WorkerFault) as caught:
            baton_worker._permitted(fresh)
        self.assertEqual(caught.exception.code, "agent")

    # -- the clock -------------------------------------------------------------

    def test_a_clock_set_back_does_not_extend_the_bound(self):
        """ROLLBACK. Ten seconds were left when the bound was first read.
        The wall clock is then set back an hour; the monotonic clock says
        eleven seconds passed. The bound is reached."""
        import publication_entry

        wall, steady = [990.0], [50.0]
        bound = publication_entry.Bound(
            "1970-01-01T00:16:40Z", clock=lambda: wall[0],
            monotonic=lambda: steady[0])
        self.assertEqual(bound.ends, 1000.0)
        self.assertFalse(bound.reached())
        wall[0] -= 3600.0
        steady[0] += 9.0
        self.assertFalse(bound.reached())
        self.assertLessEqual(bound.remaining(), 1.0)
        steady[0] += 2.0
        self.assertTrue(bound.reached())
        self.assertEqual(bound.remaining(), 0.0)
        # A SECOND BOUND, AS A RESTARTED WORKER WOULD MAKE ONE, is the same
        # instant and not a fresh budget: it reads the same document.
        again = publication_entry.Bound(
            "1970-01-01T00:16:40Z", clock=lambda: 995.0,
            monotonic=lambda: steady[0])
        self.assertEqual(again.ends, bound.ends)
        self.assertEqual(again.remaining(), 5.0)

    def test_a_clock_set_forward_reaches_the_bound_early(self):
        import publication_entry

        wall, steady = [990.0], [50.0]
        bound = publication_entry.Bound(
            "1970-01-01T00:16:40Z", clock=lambda: wall[0],
            monotonic=lambda: steady[0])
        wall[0] = 1000.0
        self.assertTrue(bound.reached())

    # -- the watch --------------------------------------------------------------

    def watched(self):
        """One agent whose watch decision can be read without its thread."""
        import publication_entry

        wall, steady, ended = [990.0], [50.0], []
        agent = publication_entry.PublicationAgent(
            clock=lambda: wall[0], monotonic=lambda: steady[0],
            abort=ended.append, watch=False)
        agent._bound = publication_entry.Bound(
            "1970-01-01T00:16:40Z", clock=lambda: wall[0],
            monotonic=lambda: steady[0])
        return agent, wall, steady, ended

    def test_the_watch_ends_the_process_only_where_nothing_else_can(self):
        import publication_entry

        agent, wall, steady, ended = self.watched()
        agent._enter("completing")
        self.assertFalse(agent._due())
        # MEASURING, AND THE INSTANT IS REACHED: the main thread cannot be
        # interrupted, so the process is ended -- at once.
        wall[0] = 1000.0
        self.assertTrue(agent._due())
        agent._expire()
        self.assertEqual(ended, [publication_entry.EXPIRED_STATUS])
        self.assertFalse(agent.may_complete())

        # COPYING: the supervisor ends the copy itself and reports a typed
        # fault, so the watch waits out its window first.
        agent, wall, steady, ended = self.watched()
        agent._enter("copy")
        wall[0] = 1000.0
        self.assertFalse(agent._due())
        steady[0] += publication_entry.SUPERVISOR_GRACE_SECONDS - 0.5
        self.assertFalse(agent._due())
        steady[0] += 1.0
        self.assertTrue(agent._due())

        # A FAULT IS ALREADY BEING REPORTED: the watch stands down, so the
        # typed fault is published rather than cut off into a lost execution.
        agent, wall, steady, ended = self.watched()
        agent._enter("completing")
        wall[0] = 1000.0
        self.assertFalse(agent.may_complete())
        self.assertFalse(agent._due())
        self.assertEqual(ended, [])

    def test_the_watch_ends_a_copy_it_outlives(self):
        """A COPY THIS PROCESS STARTED DOES NOT OUTLIVE IT: ending the
        process ends the copy's whole process group first."""
        import subprocess
        import time

        agent, wall, _steady, ended = self.watched()
        child = subprocess.Popen(["sleep", "60"], start_new_session=True)
        self.addCleanup(child.wait)
        agent._group = child.pid
        agent._enter("completing")
        wall[0] = 1000.0
        agent._expire()
        self.assertEqual(len(ended), 1)
        until = time.monotonic() + 5.0
        while child.poll() is None and time.monotonic() < until:
            time.sleep(0.02)
        self.assertIsNotNone(child.poll())

    def test_a_blocked_measurement_ends_the_real_process_at_the_instant(self):
        """INTERRUPTIBLE ENFORCEMENT, on the real clock, in a real process.

        The worker's own measurement never returns. Nothing raised from
        another thread could interrupt it, so the watch ends the process:
        it exits with the expiry status about a second after it started,
        having said nothing and written no completion envelope. The copy
        itself was real and finished in time.
        """
        import subprocess
        import tempfile
        import time

        root = tempfile.mkdtemp(prefix="v12-blocked-", dir=self.root)
        program = r"""
import json, os, sys, threading
from datetime import datetime, timedelta, timezone
import baton_worker, publication_entry
root = sys.argv[1]
inputs, outputs, staged = (os.path.join(root, one)
                           for one in ("inputs", "outputs", "staged"))
for place in (inputs, outputs, os.path.join(staged, "candidate"),
              os.path.join(staged, "provenance")):
    os.makedirs(place)
with open(os.path.join(staged, "candidate", "one.txt"), "w") as writing:
    writing.write("adopted\n")
with open(os.path.join(staged, "provenance", "provenance.json"), "w") as w:
    w.write("{}\n")
ends = datetime.now(timezone.utc) + timedelta(seconds=1.0)
request = {"schema": publication_entry.REQUEST_SCHEMA, "decision_id": "D1",
           "job_id": "job", "attempt_id": "attempt-1",
           "deadline": {"deadline_at": ends.isoformat(), "origin": "stage",
                        "seconds": 900, "restart_resets": False},
           "staged": {"root": "candidate", "tree_digest": "sha256:x",
                      "entry_count": 1, "total_bytes": 8},
           "provenance": {"root": "provenance", "file": "provenance.json",
                          "tree_digest": "sha256:y"},
           "outputs": {"candidate": "proposal",
                       "provenance": "recovery-provenance"}}
with open(os.path.join(inputs, "publication.json"), "w") as writing:
    json.dump(request, writing)
baton_worker.assignment_manifest = lambda: {"runtime_attempt_id": "attempt-1"}
blocked = threading.Event()
def never(*operands, **named):
    print("MEASURING", flush=True)
    blocked.wait()
baton_worker.measured = never
declared = [{"name": "proposal", "path": "proposal", "constraints": {}},
            {"name": "recovery-provenance", "path": "recovery-provenance",
             "constraints": {}}]
agent = publication_entry.PublicationAgent(
    input_root=inputs, output_root=outputs, source_root=staged)
agent.work({}, declared)
print("RETURNED", flush=True)
"""
        began = time.monotonic()
        ran = subprocess.run(
            [sys.executable, "-B", "-c", program, root],
            env={"PATH": "/usr/bin:/bin", "PYTHONPATH": WORKER},
            capture_output=True, text=True, timeout=60)
        elapsed = time.monotonic() - began
        import publication_entry

        self.assertEqual(ran.returncode, publication_entry.EXPIRED_STATUS,
                         ran.stdout + ran.stderr)
        # IT REACHED THE MEASUREMENT -- so the copy was real and in time --
        # and never came back from it.
        self.assertEqual(ran.stdout.split(), ["MEASURING"])
        self.assertLess(elapsed, 20.0)
        self.assertTrue(os.path.isfile(
            os.path.join(root, "outputs", "proposal", "one.txt")))
        self.assertFalse(os.path.lexists(
            os.path.join(root, "outputs", "output.json")))

    # -- restart ----------------------------------------------------------------

    def test_a_restarted_worker_starts_no_second_adoption(self):
        """RESTART. The first incarnation dies inside its measurement -- the
        receipt is published, no terminal is. A second incarnation finds the
        receipt and starts nothing: not with time left on the same absolute
        bound, and not after it. The manager is left with an exchange that
        never ended, which it holds as uncertain rather than as published.
        """
        import baton_worker

        self.ready()
        self.launched()

        class Died(BaseException):
            """The process ending, which no `except Exception` catches."""

        real = baton_worker.measured

        def dying(*operands, **named):
            raise Died()

        baton_worker.measured = dying
        self.addCleanup(setattr, baton_worker, "measured", real)
        with self.assertRaises(Died):
            self.turn()
        baton_worker.measured = real
        self.assertIsNone(self.exchange_view()["terminal"])
        place = self.workspace_of(self.publication_attempt)
        # WITH TIME LEFT: the replay fence, not a second budget.
        self.assertEqual(self.turn(), 4)
        self.assertIsNone(self.exchange_view()["terminal"])
        self.assertFalse(os.path.lexists(os.path.join(place, "output.json")))
        # AND AFTER THE INSTANT: still nothing.
        self.late()
        self.assertEqual(self.turn(), 4)
        self.assertIsNone(self.exchange_view()["terminal"])
        self.assertFalse(os.path.lexists(os.path.join(place, "output.json")))
        self.assertIsNone(publication_execution.result_of(
            self.jobs, self.recovery_job_id))
        self.assertFalse(self.gate()["open"])
        self.assertEqual(self.review_offers(), [])


# -- 15b. one installed publisher, two Works, the real pooled composition ----
#
# REVIEW 2026-11-23T18-55-03Z R1 AND R3, JOINED. Every case above this section
# composes ONE publication worker over the single-worker lifecycle and stands
# the deployment binding in. That is the right boundary for the manager's own
# decisions and it could not see three things the review found: the installer
# refused the role, the pooled `stage_execution.operations_from` branch was
# never executed, and a recovery on any Work but the one the publisher was
# installed against was refused by the selector.
#
# WHAT IS REAL HERE. The instance is prepared by `tools.bootstrap`. The
# publication worker document is composed by `tools.pool.composed` -- the
# installer's own composition -- named in the install document, its staging
# root prepared by `bootstrap.prepare_prerequisites`, and published by the
# ordinary repeat. The serving object is `stage_execution.operations_from`'s.
# The owner ports are `tools.publication_decision.owners`': the shipped
# `DeploymentBinding` (which really amends the configuration through
# `bootstrap.prepare`), `HostOutput`, `HostExclusion` over real token records,
# `WorkAuthorization`, `OwnerAuthorization`, `InstanceOwnership` and the
# no-session `PriorAssignment`. The Authority, the three stores, the claims,
# the launch documents, the workspace tokens, the worker entry, the copy, the
# measurement, the freeze, the intake and the cleanup are the product's.
#
# WHAT IS A DOUBLE, AND SAID SO.
#   THE ENGINE, at its normal boundary (`ComposedOneJobCase.quiescing`).
#   THE GIT CONSUMER'S PROCESS, checkpoint 1's own `GitEngine`.
#   THE TWO FAILED EXECUTIONS. Each failed Job is created by the product's
#     creation operation over stand-in creation ports, exactly as checkpoint
#     1's accepted fixture creates its one; its attempt row, its retained
#     over-ceiling output and its workspace token are then written through
#     the owners' own operations by this fixture rather than by running a
#     producer. THE REASON IS A FINDING AND NOT A CONVENIENCE: a producer run
#     through this same pooled composition prepares the persistent LINE
#     workspace layout, and the accepted owner read
#     `workspaces.retained_output_of` reconstructs the ATTEMPT layout only, so
#     the inspection of a really pooled producer's failed output refuses.
#     That limit is checkpoint 1's and is reported, not worked around.
#   THE REVIEW LANE'S DECLARATIONS. Each Work's reviewer is configured here
#     with the publication declarations, so that the recovery Job's one input
#     identity is one both of its stages can be served under. How a production
#     pool's reviewer comes to carry them is the review binding of checkpoint
#     3 and is NOT established here; `test_a_reviewer_that_...` below pins what
#     the selector does when it has not been.
#
# AND A RUNNING MANAGER SERVES THE BINDINGS IT STARTED WITH. The repeated
# admission amends the configuration; the serving object is then recomposed,
# which is what a restarted manager does and what the accepted retained-
# recovery joined case does after its own admission.

POOLED_OWNER = "baton.owner"
POOLED_WORK_B = "0000000a-W2"
POOLED_PUBLISHER = "baton.publisher"
POOLED_RECORD = "work/records/2026/11/finding-v12-output-publication-recovery"


class OneInstalledPublisherServesRecoveriesOnTwoWorks(_InstalledFixture):
    """Reservation, held-session ending, repeated admission, publication and
    custody -- twice, on two Works, through one installed publication worker
    and the real pooled composition."""

    maxDiff = None

    def clock(self):
        return self.instants[-1]

    def epoch(self):
        from datetime import datetime

        return datetime.fromisoformat(
            self.clock().replace("Z", "+00:00")).timestamp()

    # -- the instance ---------------------------------------------------------

    def setUp(self):
        import io
        import pathlib

        from baton_v12.authority import Authority
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore, workspaces as owner
        from tests.manager import input_roots
        from tools import bootstrap, instance, pool

        super().setUp()
        if WORKER not in sys.path:
            sys.path.insert(0, WORKER)
            self.addCleanup(sys.path.remove, WORKER)
        self.instants = [NOW]
        self.uuid = self.config["authority_uuid"]
        self.places = bootstrap.layout(self.state)
        self.layout = instance.layout(self.state)
        # ONE WORKSPACE ROOT PER INSTANCE, the installed layout's own, which
        # is also where `pool.composed` puts the publisher's.
        self.paths = {name: os.path.join(self.layout["state"], leaf)
                      for name, leaf in (("workspace_storage", "workspaces"),
                                         ("launch_home", "launch"),
                                         ("credential_home", "credentials"))}
        self.publisher = None
        # THE INSTANCE, FIRST WITH NO PUBLISHER AND NO JOB: an installed pool
        # an upgrade then grows.
        with open(os.devnull, "w") as quiet:
            first = bootstrap.prepare(self.document(
                owner_participant=POOLED_OWNER, workers=self.pool_workers(),
                jobs=[]), stream=quiet)
        # THE INSTALLER'S OWN COMPOSITION of the publication worker.
        record = pathlib.Path(self.checkout, POOLED_RECORD)
        record.mkdir(parents=True, exist_ok=True)
        (record / "FINDING.md").write_text("# Finding\n")
        (record / "PLAN.md").write_text("# Plan\n")
        self.publication_task = os.path.join(self.root,
                                             "publication-task.json")
        pathlib.Path(self.publication_task).write_text(json.dumps(
            {"schema": pool.PUBLICATION_TASK_SCHEMA,
             "task_id": "publication-idle",
             "instructions": "adopt the approved retained output"},
            sort_keys=True))
        self.composed_publisher = pool.composed(
            first["configuration"], worker_id="publisher",
            role="publication", participant=POOLED_PUBLISHER,
            image_reference="baton-v12-publication:candidate",
            image_digest=self.config["image_digest"], cli_build=None,
            network=None, credential_sources=None, credentials=None,
            workspace_group=self.config["workspace_group"],
            task_document=self.publication_task, record_path=POOLED_RECORD,
            checkout=self.checkout, now="2026-11-23T00:00:00.000Z")
        self.publisher = self.composed_publisher["worker"]
        self.policy = self.publisher["deployment"]["policy_digest"]

        self.jobs = JobStore.open(self.places["job_store"],
                                  authority_uuid=self.uuid,
                                  incarnation="pooled-1", clock=self.clock)
        self.addCleanup(self.jobs.close)
        self.control = ControlStore.open(self.places["control_store"],
                                         incarnation="pooled-1",
                                         clock=self.clock)
        self.addCleanup(self.control.close)
        self.group = input_roots.configured_group(self.control)
        self.storage = self.paths["workspace_storage"]
        for place in self.paths.values():
            os.makedirs(place, exist_ok=True)
        owner.configure_workspace_storage(self.control, self.storage)
        self.identity = {
            "root": os.path.realpath(self.state),
            "job_store": os.path.realpath(self.places["job_store"]),
            "control_store": os.path.realpath(self.places["control_store"]),
            "authority_store": os.path.realpath(
                self.places["authority_store"]),
            "authority_uuid": self.uuid}
        held = checkpoint1.creation_case.CURRENT.get("identity")
        checkpoint1.creation_case.CURRENT["identity"] = self.identity
        self.addCleanup(checkpoint1.creation_case.CURRENT.__setitem__,
                        "identity", held)

        # THE TWO FAILED JOBS, each on its own Work with its own producer.
        workers = {one["worker_id"]: one for one in self.pool_workers()}
        self.failed = {
            name: self.created_job(name, work, workers[producer],
                                   workers[reviewer])
            for name, work, producer, reviewer in (
                ("a", self.work, "impl-a", "review-a"),
                ("b", POOLED_WORK_B, "impl-b", "review-b"))}
        # THE UPGRADE: the same pool, the publisher, and the two Jobs bound.
        self.install_document = self.document(
            owner_participant=POOLED_OWNER,
            workers=self.pool_workers() + [self.publisher],
            jobs=[self.job(job_id=self.failed["a"]["job_id"],
                           work_id=self.work, producer="impl-a"),
                  self.job(job_id=self.failed["b"]["job_id"],
                           work_id=POOLED_WORK_B, producer="impl-b")])
        # THE STAGING ROOT IS PREPARED BY THE INSTALLATION'S OWN MACHINERY,
        # which is what the installed repeat runs before it publishes.
        self.prepared_roots = {}
        bootstrap.prepare_prerequisites(self.install_document, self.layout,
                                        made=self.prepared_roots,
                                        stream=io.StringIO())
        with open(os.devnull, "w") as quiet:
            self.installed = bootstrap.prepare(self.install_document,
                                               stream=quiet)
        pathlib.Path(self.places["install_inputs"]).write_text(
            json.dumps(self.install_document, indent=2, sort_keys=True),
            encoding="utf-8")
        self.authority = Authority.open(self.places["authority_store"],
                                        expected_authority_uuid=self.uuid)
        self.addCleanup(self.authority.dispose)
        for name, participant in (("a", "baton.impl-a"),
                                  ("b", "baton.impl-b")):
            self.failed_attempt(self.failed[name], participant)
        self.oci = None
        self.operations = None

    def on_work(self, manifest, work):
        held = copy.deepcopy(manifest)
        held["work_ref"] = dict(held["work_ref"], work_id=work)
        held.pop("manifest_digest")
        held["manifest_digest"] = digest(held)
        return held

    def pool_workers(self):
        return [
            self.stage_worker("impl-a", "implementation", "baton.impl-a",
                              **self.paths),
            self.reviewer("review-a", "baton.reviewer", self.work),
            self.stage_worker(
                "impl-b", "implementation", "baton.impl-b",
                input_manifest=self.on_work(self.config["input_manifest"],
                                            POOLED_WORK_B), **self.paths),
            self.reviewer("review-b", "baton.reviewer-b", POOLED_WORK_B)]

    # WHETHER THE REVIEW LANE CARRIES THE PUBLICATION DECLARATIONS. See the
    # section comment: this is a fixture selection standing in for checkpoint
    # 3's review binding, and the one case that is about its absence turns it
    # off.
    reviewers_agree = True

    def reviewer(self, worker_id, participant, work):
        if self.publisher is None or not self.reviewers_agree:
            return self.stage_worker(
                worker_id, "review", participant,
                review_route=self.INTEGRATION_ROUTE,
                input_manifest=self.on_work(self.config["input_manifest"],
                                            work), **self.paths)
        manifest = copy.deepcopy(self.publisher["deployment"]
                                 ["input_manifest"])
        manifest["work_ref"] = dict(manifest["work_ref"], work_id=work)
        # ITS OWN IMAGE AND PROFILE, which are not Job-scoped members.
        manifest["worker_image_digest"] = self.config["image_digest"]
        manifest["runtime_profile_digest"] = \
            self.config["input_manifest"]["runtime_profile_digest"]
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        return self.stage_worker(
            worker_id, "review", participant,
            review_route=self.INTEGRATION_ROUTE, input_manifest=manifest,
            policy_digest=self.policy, task_document=self.publication_task,
            **self.paths)

    # -- the two failed executions --------------------------------------------

    def created_job(self, name, work, producer, reviewer):
        """One real `/4` Job on `work`, admitted by the creation operation."""
        case = checkpoint1.creation_case
        outputs = role_contract.contract_for(
            role_contract.PROPOSAL100M_TEMPLATE)["outputs"]
        derivation = case.FakeDerivation(
            work_id=work, policy_digest=self.policy,
            profiles={
                "implementation": {
                    "profile_name": producer["deployment"]["profile_name"],
                    "profile_digest":
                        producer["deployment"]["profile_digest"]},
                "review": {
                    "profile_name": reviewer["deployment"]["profile_name"],
                    "profile_digest":
                        reviewer["deployment"]["profile_digest"]}},
            task=lambda selection, verification=None:
                checkpoint1.PublicationCase.composed_task(
                    self, selection, verification))
        derivation.answer["declarations"] = {
            "implementation": {producer["worker_id"]:
                               [dict(one) for one in outputs]},
            "review": {reviewer["worker_id"]:
                       [dict(one) for one in outputs]}}
        created = creation.create_template_job(
            self.jobs, case.FakeOperations(),
            request=case.request(
                template=role_contract.PROPOSAL100M_TEMPLATE,
                task={"task_id": "publish-" + name,
                      "statement": case.STATEMENT}),
            derivation=derivation, authorization=case.FakeAuthorization(),
            binding=case.FakeBinding(), ownership=case.FakeOwnership())
        stage_id = documents.stage_id(created["job_id"], "implementation")
        return {"name": name, "job_id": created["job_id"],
                "stage_id": stage_id, "work": work,
                "decision": "D-" + name,
                "attempt_id": episodes.episode_of(self.jobs, stage_id,
                                                  1)["attempt_id"]}

    def failed_attempt(self, failed, participant):
        """The failed execution's host state: a REAL claim on its Work, the
        attempt row under that exact assignment, a completed preparation, a
        returned workspace token and the retained over-ceiling output."""
        from baton_v12.worker_manager import attempts as held_attempts
        from baton_v12.worker_manager import tokens, workspaces as owner

        attempt_id, work = failed["attempt_id"], failed["work"]
        self.authority.session(participant).claim(
            {"work_id": work, "operation_id": "claim-" + failed["job_id"]})
        live = self.authority.assignment_of(work)
        self.control._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, "
            "assignment_scope, assignment_role, assignment_grant, "
            "assignment_policy_generation) VALUES (?, 'adapter', "
            "'adapter-digest', 'profile-digest', ?, ?, ?, ?, ?, 1, ?, ?, "
            "'role', 'grant', 1)",
            (attempt_id, NOW, work, self.uuid, participant,
             live["generation"], self.authority.principal_of(participant),
             self.authority.project_work(work)["scope"]))
        roots = owner.assignment_workspace(self.group, self.storage,
                                           attempt_id)
        owner.record_preparation(self.control, attempt_id, roots,
                                 ["task", "inputs"])
        measured, source = os.stat(roots["workspace"]), os.stat(self.state)
        self.control._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'destroyed', cleanup = 'retained', workspace_device = ?, "
            "workspace_inode = ?, source_device = ?, source_inode = ? "
            "WHERE runtime_attempt_id = ?",
            ("runtime-" + attempt_id[:24], measured.st_dev, measured.st_ino,
             source.st_dev, source.st_ino, attempt_id))
        row = dict(self.control._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (attempt_id,)).fetchone())
        # THE WORKSPACE TOKEN, THROUGH THE RESOURCE OWNER'S OWN OPERATIONS,
        # because the shipped `HostExclusion` reads exactly what they journal.
        start = held_attempts._start_operation_id(row)
        domain = tokens.domain_of("workspace", tokens.workspace_identity(row))
        token = tokens.acquire(self.control, domain, operation=start,
                               execution=attempt_id, attempt=attempt_id)
        tokens.journal_launch(self.control, token, start)
        tokens.bind_container(
            self.control,
            tokens.token_of(self.control, domain, token["generation"]),
            row["runtime_id"], launch=start)
        tokens.returned(
            self.control,
            tokens.token_of(self.control, domain, token["generation"]),
            cessation={"domain": domain, "generation": token["generation"],
                       "launch": start, "container": row["runtime_id"],
                       "stopped": True, "helpers": []})
        self.job_id = failed["job_id"]
        failed["roots"] = roots
        # A DIFFERENT TREE PER JOB, so "each recovery published ITS original"
        # is falsifiable.
        failed["original"] = checkpoint1.PublicationCase.write_output(
            self, roots=roots,
            extra={"note.txt": ("original of " + failed["name"]).encode()})
        failed["participant"] = participant
        failed["assignment"] = live

    # -- the shipped owner ports ----------------------------------------------

    def ports(self):
        import io

        from tools import publication_decision
        from tools.publication_ports import SourceCorrespondence

        held = publication_decision.owners({
            "instance": self.state, "job_store": self.places["job_store"],
            "control": self.places["control_store"],
            "authority": self.places["authority_store"],
            "authority_uuid": self.uuid, "participant": POOLED_OWNER,
            "stream": io.StringIO(), "control_handle": self.control})
        self.addCleanup(held["release"])
        scratch = os.path.join(self.root, "git-scratch")
        os.makedirs(scratch, exist_ok=True)
        # THE GIT PROCESS IS THE ONE DOUBLE AMONG THESE PORTS.
        held["source"] = SourceCorrespondence(
            self.identity, scratch=scratch, engine=checkpoint1.GitEngine())
        return held

    def decided(self, failed, held):
        selection = publication_recovery.inspect(
            self.jobs, self.control, job_id=failed["job_id"],
            stage_id=failed["stage_id"], episode=1, host=held["host"],
            exclusion=held["exclusion"], source=held["source"],
            authorization=held["owner"], now=NOW)
        self.assertTrue(selection["eligible"], selection.get("holds"))
        return publication_recovery.decide(
            self.jobs, self.control, job_id=failed["job_id"],
            stage_id=failed["stage_id"], episode=1,
            decision_id=failed["decision"], disposition="approved",
            authorization=held["owner"],
            expected=publication_recovery.expected_facts(selection),
            profile=selection["profile"]["profile"],
            profile_digest=selection["profile"]["digest"],
            stages=list(publication_recovery.SELECTED_STAGES),
            declaration_digest=selection["declaration"]["digest"],
            host=held["host"], exclusion=held["exclusion"],
            source=held["source"], now=NOW)

    def admit(self, failed, held):
        """The owner's admission, through the shipped ports. A refusal is
        returned rather than raised so a case can read both outcomes."""
        try:
            return publication_recovery.admit_publication(
                self.jobs, self.control, decision_id=failed["decision"],
                exclusion=held["exclusion"],
                authorization=held["authorization"],
                binding=held["binding"], ownership=held["ownership"],
                host=held["host"], source=held["source"],
                ending=held["ending"], now=NOW)
        except ContractRefusal as refusal:
            return refusal

    # -- the serving manager ---------------------------------------------------

    def configuration(self):
        import pathlib

        return json.loads(pathlib.Path(
            self.places["configuration"]).read_text())

    def serving(self):
        """`stage_execution.operations_from` over the instance's CURRENT
        configuration. A second call is a restarted manager."""
        from tests.tools.test_stage_execution import ComposedOneJobCase
        from tools import stage_execution as composition

        if self.operations is not None:
            self.operations.close()
        if self.oci is None:
            self.oci = ComposedOneJobCase.quiescing(self)
        self.operations = composition.operations_from(
            self.configuration(), self.jobs, self.control,
            engine_run=self.oci,
            credential_provider=lambda provider, reference: self.secret,
            clock=self.clock, checkout=self.checkout)
        self.addCleanup(self.operations.close)
        return self.operations

    def tick(self):
        return manager.sweep(self.jobs, self.operations, now=self.clock())

    def publication_worker_operations(self):
        return [one for one in self.operations.workers
                if one["role"] == "publication"][0]["operations"]

    def publication_stage(self, failed):
        stage_id = publication_recovery.publication_stage_id(
            failed["decision"])
        live = episodes.live_of(self.jobs, stage_id)
        if live is None:
            return None
        for one in submission.stages_of(
                self.jobs,
                publication_recovery.recovery_job_id(failed["decision"])):
            if one["stage_id"] == stage_id:
                return episodes.attempting(one, live)
        return None

    def bound_source(self, attempt_id):
        """The directory the ENGINE was told to bind read-only at
        `/input/source` for THIS attempt's container, read out of its own
        launch vector rather than chosen here."""
        for vector in reversed(self.oci.starts):
            if not any(attempt_id in str(word) for word in vector):
                continue
            for index, word in enumerate(vector[:-1]):
                if word != "--mount":
                    continue
                parts = dict(part.split("=", 1) for part in
                             vector[index + 1].split(",") if "=" in part)
                if parts.get("target") == "/input/source":
                    self.assertEqual(parts["readonly"], "true")
                    return parts["source"]
        self.fail(f"no container was started for {attempt_id}")

    def launched(self, failed, ticks=8):
        """Ordinary ticks until this recovery's publication runtime runs."""
        for _ in range(ticks):
            stage = self.publication_stage(failed)
            state = None if stage is None else attempt_runtime_of(
                self.control, stage["attempt_id"])
            if state is not None \
                    and state["execution_runtime"] == "running":
                return stage
            self.tick()
        self.fail(f"recovery {failed['decision']} never launched")

    def turn(self, failed, **agent):
        """THE CONFINED WORKER'S ONE TURN, the real worker entry served over
        the exchange this deployment published for this recovery."""
        import baton_worker
        import publication_entry

        stage = self.publication_stage(failed)
        worker = self.publication_worker_operations().worker_for(stage)
        delivered = worker._adopted(stage)
        home = os.path.join(self.storage, stage["attempt_id"])
        held = []
        for name, value in (("INPUT_ROOT", os.path.join(home, "inputs")),
                            ("OUTPUT_ROOT", os.path.join(home, "workspace"))):
            held.append((name, getattr(baton_worker, name)))
            setattr(baton_worker, name, value)
        composed = dict(input_root=os.path.join(home, "inputs"),
                        output_root=os.path.join(home, "workspace"),
                        source_root=self.bound_source(stage["attempt_id"]),
                        clock=self.epoch, watch=False)
        composed.update(agent)
        serving = publication_entry.PublicationAgent(**composed)
        try:
            return baton_worker.serve_exchange(
                serving, delivered.document,
                launch.payload_of(delivered.document)["session"],
                delivered.exchange.command_root,
                delivered.exchange.event_root), home
        finally:
            serving.stand_down()
            for name, value in held:
                setattr(baton_worker, name, value)

    def both_admitted(self):
        """Decide both, admit both (reserved and stopped at the held
        assignments), let the serving manager end them, admit both again."""
        held = self.ports()
        first, second = {}, {}
        for failed in self.failed.values():
            self.decided(failed, held)
        for name, failed in self.failed.items():
            first[name] = self.admit(failed, held)
        self.serving()
        ended = [self.tick() for _ in range(2)]
        for name, failed in self.failed.items():
            second[name] = self.admit(failed, held)
        return held, first, ended, second

    def published(self, failed):
        stage = self.launched(failed)
        code, home = self.turn(failed)
        self.assertEqual(code, 0)
        for _ in range(8):
            self.tick()
            if publication_execution.publication_readiness(
                    self.jobs, failed["decision"])["handed_off"]:
                break
        return stage, home

    # -- the joined proof ------------------------------------------------------

    def test_two_recoveries_on_two_works_through_one_installed_publisher(self):
        installed = copy.deepcopy(self.configuration())
        publisher = [one for one in installed["workers"]
                     if one["role"] == "publication"]
        self.assertEqual([one["worker_id"] for one in publisher],
                         ["publisher"])
        # INSTALLED AGAINST THE FIRST WORK, and that never changes.
        self.assertEqual(publisher[0]["deployment"]["input_manifest"]
                         ["work_ref"]["work_id"], self.work)
        self.assertEqual(publisher[0]["deployment"]["credential_slots"], [])

        held, first, ended, second = self.both_admitted()

        for name, failed in self.failed.items():
            with self.subTest(recovery=name):
                # 1. THE OWNER'S ADMISSION RESERVED AND STOPPED. It holds no
                #    producer session and ended nothing.
                self.assertIsInstance(first[name], ContractRefusal)
                self.assertEqual((first[name].category, first[name].code),
                                 ("refused", "capability"))
                self.assertIsNotNone(publication_recovery.intent_of(
                    self.jobs, failed["decision"]))
                # 2. THE SERVING MANAGER ENDED EXACTLY THAT ASSIGNMENT, through
                #    the producer session it already held.
                record = publication_recovery.ending_of(self.jobs,
                                                        failed["decision"])
                self.assertEqual(record["disposition"], "ended")
                self.assertEqual(record["expect"], failed["assignment"])
                # 3. THE SAME ADMISSION, REPEATED, ADMITTED.
                self.assertEqual(second[name]["state"], "admitted",
                                 second[name])
                self.assertEqual(second[name]["work_id"], failed["work"])

        # ONE DERIVATION: each recovery was submitted under the identity of
        # the document the installed publisher serves IT under, and the two
        # are different because the Works are.
        configured = self.configuration()
        bindings = {one["job_id"]: one for one in configured["job_bindings"]}
        worker = [one for one in configured["workers"]
                  if one["role"] == "publication"][0]
        identities = {}
        for name, failed in self.failed.items():
            job_id = publication_recovery.recovery_job_id(failed["decision"])
            self.assertEqual(bindings[job_id]["job_work_id"], failed["work"])
            served = stage_execution._served_deployment(
                configured, worker, bindings[job_id],
                creation.job_task_of(self.jobs, failed["job_id"]))
            identities[name] = job_input_identity(served["input_manifest"])
            self.assertEqual(second[name]["input_digest"], identities[name])
            self.assertEqual(
                submission.job_of(self.jobs, job_id)["input_digest"],
                identities[name])
        self.assertNotEqual(identities["a"], identities["b"])
        # AND THE INSTALLED DOCUMENT WAS NOT MOVED TO MAKE THAT TRUE.
        self.assertEqual(worker, publisher[0])

        # A RESTARTED MANAGER, over the amended configuration.
        self.serving()
        self.assertIsNotNone(self.operations.recovery_publication)
        self.assertEqual(
            sorted(self.publication_worker_operations().held),
            sorted(publication_recovery.recovery_job_id(one["decision"])
                   for one in self.failed.values()))
        homes = {}
        for name, failed in self.failed.items():
            with self.subTest(published=name):
                stage, home = self.published(failed)
                homes[name] = home
                # DELIVERED ITS OWN WORK AND THE ORIGINAL JOB'S TASK.
                with open(os.path.join(home, "inputs", "input.json"),
                          encoding="utf-8") as reading:
                    delivered = json.load(reading)
                self.assertEqual(delivered["work_ref"]["work_id"],
                                 failed["work"])
                self.assertEqual(job_input_identity(delivered),
                                 identities[name])
                with open(os.path.join(home, "inputs", "task.json"),
                          "rb") as reading:
                    self.assertEqual(
                        reading.read(),
                        creation.job_task_of(
                            self.jobs, failed["job_id"]).encode("utf-8"))
                # UNDER ITS OWN FRESH ASSIGNMENT ON THAT WORK.
                state = attempt_runtime_of(self.control, stage["attempt_id"])
                self.assertEqual(state["assignment"]["participant"],
                                 POOLED_PUBLISHER)
                self.assertEqual(state["assignment"]["work_ref"]["work_id"],
                                 failed["work"])
                self.assertNotEqual(state["assignment"]["generation"],
                                    failed["assignment"]["generation"])
                self.assertEqual((state["execution_runtime"],
                                  state["cleanup"]),
                                 ("destroyed", "retained"))
                # THE ADOPTED PROPOSAL IS THIS JOB'S ORIGINAL, byte for byte.
                job_id = publication_recovery.recovery_job_id(
                    failed["decision"])
                result = publication_execution.result_of(self.jobs, job_id)
                self.assertEqual(result["adopted"]["tree_digest"],
                                 failed["original"]["tree_digest"])
                self.assertIsNotNone(
                    publication_execution.custody_of(self.jobs, job_id))
                self.assertIsNotNone(
                    publication_execution.handoff_of(self.jobs, job_id))
                self.assertTrue(publication_execution.execution_gate(
                    self.jobs, job_id)["open"])
        self.assertNotEqual(self.failed["a"]["original"]["tree_digest"],
                            self.failed["b"]["original"]["tree_digest"])
        # ONE CAPACITY SERVED BOTH: the scheduler allocated both publication
        # stages to the one configured worker.
        allocated = [row[0] for row in self.jobs._connection.execute(
            "SELECT worker_id FROM stage_allocations WHERE stage_id IN (?, ?)",
            tuple(publication_recovery.publication_stage_id(one["decision"])
                  for one in self.failed.values()))]
        self.assertEqual(sorted(set(allocated)), ["publisher"])
        self.assertEqual(len(allocated), 2)
        # AND EACH ORIGINAL IS UNTOUCHED.
        from baton_v12.worker_manager import workspaces as owner
        for failed in self.failed.values():
            self.assertEqual(
                owner.directory_manifest(failed["roots"]["workspace"]),
                failed["original"])

    def test_a_stage_is_never_served_under_another_recoverys_operands(self):
        """WRONG WORK, AT THE SERVING BOUNDARY. One recovery's publication
        stage handed to the operations derived for the other is refused by
        the worker lifecycle's own validator, and a stage of a Job this
        deployment derived nothing for is refused before any of them."""
        self.both_admitted()
        self.serving()
        routed = self.publication_worker_operations()
        stage = self.launched(self.failed["a"], ticks=4)
        other = routed.held[publication_recovery.recovery_job_id(
            self.failed["b"]["decision"])]
        job = submission.job_of(self.jobs, stage["job_id"])
        with self.assertRaises(ContractRefusal) as caught:
            other.dispatch(stage, job)
        self.assertIn(POOLED_WORK_B, caught.exception.message)
        with self.assertRaises(ContractRefusal) as caught:
            routed.dispatch(dict(stage, job_id="some-other-job"), job)
        self.assertIn("refused rather than served under another recovery",
                      caught.exception.message)
        # AND THE INSTALLED COMPOSITION SERVES NO STAGE AT ALL.
        self.assertNotIn(routed.installed, list(routed.held.values()))

    def test_the_selector_refuses_a_wrong_work_task_or_input(self):
        """THE NEGATIVES OF THE ONE DERIVATION, through the shipped binding
        port's own `serving` -- which is `stage_execution.servable_workers`."""
        held, _first, _ended, second = self.both_admitted()
        failed = self.failed["b"]
        job_id = publication_recovery.recovery_job_id(failed["decision"])
        entry = second["b"]
        stage = {"kind": documents.PUBLICATION_STAGE,
                 "work_id": failed["work"],
                 "profile_name": entry["worker"]["profile_name"],
                 "profile_digest": entry["worker"]["profile_digest"]}
        job = {"input_digest": entry["input_digest"],
               "policy_digest": self.policy}
        task = creation.job_task_of(self.jobs, failed["job_id"])
        binding = held["binding"]
        # THE CONTROL: the real operands are served by the one publisher.
        self.assertEqual(binding.serving(job_id, stage=stage, job=job,
                                         task=task), ["publisher"])
        # ANOTHER RECOVERY'S INPUT: the other Work's identity.
        self.assertEqual(binding.serving(
            job_id, stage=stage,
            job=dict(job, input_digest=second["a"]["input_digest"]),
            task=task), [])
        # THE INSTALLED WORKER'S OWN IDENTITY, which is what the first cut
        # submitted every recovery under.
        self.assertEqual(binding.serving(
            job_id, stage=stage,
            job=dict(job, input_digest=entry["worker"]["input_digest"]),
            task=task), [])
        # ANOTHER TASK: the other Job's, and none at all.
        other = creation.job_task_of(self.jobs, self.failed["a"]["job_id"])
        self.assertNotEqual(other, task)
        self.assertEqual(binding.serving(job_id, stage=stage, job=job,
                                         task=other), [])
        self.assertEqual(binding.serving(job_id, stage=stage, job=job,
                                         task=None), [])
        # ANOTHER POLICY.
        self.assertEqual(binding.serving(
            job_id, stage=stage,
            job=dict(job, policy_digest="sha256:" + "9" * 64), task=task), [])
        # AND `_disagreements` STILL NAMES A WRONG WORK, unweakened: the
        # document derived for THIS recovery, compared against a binding on
        # the other Work.
        configured = self.configuration()
        bindings = {one["job_id"]: one for one in configured["job_bindings"]}
        worker = [one for one in configured["workers"]
                  if one["role"] == "publication"][0]
        served = stage_execution._served_deployment(
            configured, worker, bindings[job_id], task)
        found = stage_execution._disagreements(
            served, dict(stage, job_id=job_id), job,
            dict(bindings[job_id], job_work_id=self.work))
        self.assertEqual(found["the Work"], (POOLED_WORK_B, self.work))

    def test_the_review_stage_starts_nothing_before_the_handoff(self):
        """THE GATE, in the pooled composition: until a recovery's custody
        and hand-off exist its review stage is offered to nobody, whatever
        else the pool is doing."""
        self.both_admitted()
        self.serving()
        failed = self.failed["a"]
        job_id = publication_recovery.recovery_job_id(failed["decision"])
        review = documents.stage_id(job_id, "review")
        self.launched(failed)
        for _ in range(3):
            self.tick()
        self.assertFalse(publication_execution.execution_gate(
            self.jobs, job_id)["open"])
        self.assertEqual(self.jobs._connection.execute(
            "SELECT count(*) FROM stage_allocations WHERE stage_id = ?",
            (review,)).fetchone()[0], 0)
        # AND ONLY THE PUBLICATION CONTAINER WAS EVER STARTED.
        self.assertEqual(len(self.oci.starts), 1)
        # THE HAND-OFF IS WHAT RELEASES IT, and then it goes to THIS Work's
        # reviewer and to nobody else's. What that reviewer is delivered is
        # the review binding of checkpoint 3 and is not asserted here.
        code, _home = self.turn(failed)
        self.assertEqual(code, 0)
        for _ in range(8):
            self.tick()
        self.assertTrue(publication_execution.execution_gate(
            self.jobs, job_id)["open"])
        self.assertEqual(
            [row[0] for row in self.jobs._connection.execute(
                "SELECT worker_id FROM stage_allocations WHERE stage_id = ?",
                (review,))], ["review-a"])


class AReviewerWithoutThePublicationDeclarationsHoldsTheAdmission(
        OneInstalledPublisherServesRecoveriesOnTwoWorks):
    """WHAT THE SELECTOR DOES WHEN THE REVIEW LANE WAS NOT GIVEN THEM.

    A recovery Job carries ONE input identity and both of its stages are held
    to it. Here each Work's reviewer is the ordinary one this fixture pool
    otherwise configures, so its Job-scoped manifest is not the recovery's.
    The repeated admission then stops at the review stage -- reserved,
    incomplete, nothing submitted, nothing published -- which is the
    fail-closed answer and is ALSO the open item this pins: how a production
    reviewer comes to be servable for a recovery is checkpoint 3's review
    binding.
    """

    reviewers_agree = False

    # ONLY THIS CASE: the inherited ones are the parent's and would be the
    # same cases run under another class name.
    test_two_recoveries_on_two_works_through_one_installed_publisher = None
    test_a_stage_is_never_served_under_another_recoverys_operands = None
    test_the_selector_refuses_a_wrong_work_task_or_input = None
    test_the_review_stage_starts_nothing_before_the_handoff = None

    def test_the_repeated_admission_stops_at_the_review_stage(self):
        held, _first, _ended, second = self.both_admitted()
        for name, failed in self.failed.items():
            with self.subTest(recovery=name):
                refused = second[name]
                self.assertIsInstance(refused, ContractRefusal)
                self.assertIn("'review' stage", refused.message)
                self.assertIn("RESERVED", refused.message)
                job_id = publication_recovery.recovery_job_id(
                    failed["decision"])
                self.assertEqual(self.jobs._connection.execute(
                    "SELECT count(*) FROM jobs WHERE job_id = ?",
                    (job_id,)).fetchone()[0], 0)
                self.assertIsNone(publication_recovery.admission_of(
                    self.jobs, failed["decision"]))
                # THE PUBLICATION STAGE ITSELF WAS SERVABLE: the refusal is
                # about the review lane and nothing else.
                intent = publication_recovery.intent_of(self.jobs,
                                                        failed["decision"])
                self.assertEqual(held["binding"].serving(
                    job_id,
                    stage={"kind": documents.PUBLICATION_STAGE,
                           "work_id": failed["work"],
                           "profile_name": intent["worker"]["profile_name"],
                           "profile_digest":
                               intent["worker"]["profile_digest"]},
                    job={"input_digest": intent["input_digest"],
                         "policy_digest": self.policy},
                    task=creation.job_task_of(self.jobs, failed["job_id"])),
                    ["publisher"])
        self.serving()
        for _ in range(4):
            self.tick()
        self.assertEqual(self.oci.starts, [])


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
