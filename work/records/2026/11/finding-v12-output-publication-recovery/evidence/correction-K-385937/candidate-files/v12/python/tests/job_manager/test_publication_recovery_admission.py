"""W385695 internal checkpoint 1 — the owner's inspection of a retained OUTPUT
PUBLICATION failure, their exact decision, and the closed admission boundary.

WHAT THESE CASES ARE ABOUT. A Job whose implementation really completed --
provider exit 0, its own required verifier exit 0 -- and whose output
publication then failed, so nothing was frozen, nothing entered custody and
the proposal is still sitting in the attempt's own writable root on the host.
The supported command an owner inspects that with, the supported command they
decide it with, and the admission boundary an approval reaches: a HELD
PREREQUISITE, a CLOSED gate, and no Job, no binding, no reservation and no
offer anywhere.

WHAT IS REAL HERE, and the list is what makes this evidence rather than a
demonstration. The owner commands are the installed ones, reached through
`tools.job_manager.main` with an operator's own argv, so the parsing, the
operand checks, the store roles, the owner-port composition and the printed
answer are the deployment's. The failed Job is created by the REAL template
creation operation against the REAL `implementation-review/4` revision, so its
stages, its episodes, its derived attempt identity and its admitted task
document are the product's own. The AUTHORIZATION IS PRODUCTION: a real
Authority store holding a real Work with its own effective scope and a real
`approve` grant made in that scope. The control store, the configured
workspace group and storage, the attempt's allocated roots, the completed
preparation record and the proposal tree on disk-backed storage are real, and
the ORIGINAL output is read back through
`workspaces.retained_output_of` -- the owner API this slice adds -- which
proves the storage, the preparation, the settled writers and the object
identity before it measures a byte. The host output port and the
source-correspondence port are the PRODUCTION adapters from
`tools.publication_ports`.

WHAT IS FAKED, AND ONLY WHERE A DEPLOYMENT WOULD SUPPLY ONE: the host's record
of the prior attempt's runtime and workspace token, the deployment
configuration's binding and selector, the instance guard, and the ENGINE the
Git-aware consumer's commands run at. The correspondence VECTORS are
`baton_v12.integration.git_profile`'s own and are asserted word for word; what
the fake answers is what a container would have printed. There is no provider,
no model, no image and no container in this file.

WHAT IS DELIBERATELY ABSENT, AND PROVED ABSENT. No publication worker, no
staging, no deadline enforcement, no custody, no intake receipt, no review
handoff and no verdict: those are checkpoints 2 and 3, and a case here that
produced one would be implementing them. What is asserted instead is that the
boundary SAYS SO -- `readiness` names the acts still owed and who owns them --
and that the whole path issues ZERO offers, reserves ZERO Job identities and
leaves the original Job, its rows and the original bytes byte-identical.
"""

import copy
import hashlib
import io
import json
import os
import tempfile
import threading
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.contracts.manifest import job_input_identity
from baton_v12.job_manager import (JobStore, cancellation, creation,
                                   documents, episodes, job_control,
                                   publication_recovery, role_contract,
                                   scheduler, submission, submit)
from baton_v12.integration import git_profile
from baton_v12.worker_manager import ControlStore, workspaces

from tests.job_manager import test_creation as creation_case
from tests.job_manager import test_role_capability as capability_case
from tests.job_manager.fixtures import NOW, UUID, WORK_A
from tests.manager import disk_roots, input_roots

OWNER = "baton.slaw"
OWNER_PRINCIPAL = "principal:slawomir"
INTRUDER = "baton.claude"
ROUTE = "baton.impl"
WORK_SCOPE = "scope:w385695-publication"
PRODUCER_PARTICIPANT = "implementation-worker"
LATER = "2026-09-02T01:00:00.000Z"

# The producer's own required command, as the words it actually was. It is the
# command the ADMITTED TASK declares, which is the whole of what makes the
# adapter's account attributable rather than merely present.
PRODUCER_ARGV = ["bash", "-c", "exec python3 -m unittest -v x"]
BASE = "c" * 40
HEAD = "5bc260b6dcbe970c8729424fa826b88dbc1a9d0f"
CHANGED = ["v12/python/src/baton_v12/job_manager/publication_recovery.py",
           "v12/python/tools/publication_decision.py"]
UNCHANGED = "v12/DESIGN.md"

# WHICH DISPOSABLE INSTANCE THE STAND-IN PORTS ANSWER FOR, set by each case to
# its own temporary root and its own real store paths. W359719 R17/R18 made
# the instance part of what every owner port declares, so a fixture naming a
# fictional deployment would be declaring another one.
CURRENT = {}


def proposal_result(**changed):
    """The adapter's own `result.json`, as a real document in real bytes.

    `baton.dogfood-proposal/3` is one of the two generations
    `failure_cause.RETAINED_RESULT_SCHEMAS` reads. The members this suite
    cares about are the declared ending, the provider's account of itself, the
    verification's own exit status and argv, and the candidate the whole
    recovery is about; the rest is the record's own shape.
    """
    held = {"schema": "baton.dogfood-proposal/3",
            "task_id": None, "disposition": "candidate",
            "why": "the candidate changed the source and its own "
                   "verification passed",
            "changed_paths": list(CHANGED), "source_entries": 2,
            "collection": None, "base": BASE, "entry_head": BASE,
            "head": HEAD,
            "provider": {"failure_reason": None, "seconds_bound": 7200,
                         "seconds_bound_source": "job-selected", "status": 0},
            "verification": {"argv": list(PRODUCER_ARGV), "status": 0},
            "context": None, "command": None, "exit_status": 0,
            "candidate_changed": [], "candidate_removed": []}
    held.update(changed)
    return held


class FakeExclusion:
    """The host's answer about the prior attempt, one fact at a time."""

    def __init__(self, answer=None, identity=None):
        self.answer = answer
        self.asked = []
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity")

    def evidence_of(self, attempt_ids):
        self.asked.append(tuple(attempt_ids))
        held = {one: (self.answer if self.answer is not ... else None)
                for one in attempt_ids} if self.answer is not None else {
            one: {"runtime": {"attempt_id": None, "runtime_id": "runtime-1",
                              "execution_runtime": "destroyed",
                              "cleanup": "retained", "assignment": None},
                  "token": {"returned": True}} for one in attempt_ids}
        held = dict(held)
        held["host"] = CURRENT.get("identity", {}).get("control_store")
        return held


class FakeBinding:
    """The deployment, with every question recorded rather than answered for."""

    def __init__(self, identity=None):
        self.bound = {}
        self.added = []
        self.asked = []
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity")

    def binding_of(self, job_id):
        self.asked.append(job_id)
        return self.bound.get(job_id)

    def bind(self, job_id, *, like, work_id):
        self.added.append((job_id, like, work_id))
        self.bound[job_id] = {"job_id": job_id, "job_work_id": work_id}
        return self.bound[job_id]

    def serving(self, job_id, *, stage, job, task=None):
        self.asked.append((job_id, dict(stage)))
        return []


class FakeOwnership:
    """The instance guard and this boundary's invocation lock, in memory.

    REAL ENOUGH TO DECIDE A RACE. `invocation` is a genuine per-identity lock,
    so a case about two concurrent boundaries is about one rather than about
    which thread happened to finish first.
    """

    def __init__(self, identity=None, locks=None):
        self.held_count = 0
        self.released = 0
        self.locks = {} if locks is None else locks
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity")

    def held(self):
        import contextlib

        @contextlib.contextmanager
        def holding():
            self.held_count += 1
            try:
                yield self
            finally:
                self.released += 1

        return holding()

    def invocation(self, job_id):
        import contextlib

        lock = self.locks.setdefault(job_id, threading.Lock())

        @contextlib.contextmanager
        def owning():
            if not lock.acquire(timeout=30):             # pragma: no cover
                raise ContractRefusal(
                    "refused", "precondition",
                    f"another admission of {job_id!r} is in flight")
            try:
                yield
            finally:
                lock.release()

        return owning()


class WorkPort:
    """The Authority's own answer about the Work this recovery reuses.

    THE REAL AUTHORITY BEHIND IT. This is the production
    `fresh_attempt_ports.WorkAuthorization` reduced to the one read the
    boundary makes -- it never creates a Work -- so the handle it wraps is the
    case's real Authority and the answer is that store's own projection.
    """

    def __init__(self, authority, identity=None):
        self._authority = authority
        self._identity = identity

    def instance(self):
        return self._identity or CURRENT.get("identity")

    def work_of(self, work_id):
        from baton_v12.authority import Refusal

        try:
            return self._authority.project_work(work_id)
        except Refusal:
            if self._authority.work_creation(work_id) is None:
                return None
            raise


class GitEngine:
    """The boundary a Git-aware consumer's commands actually run at.

    FAKED HERE AND NOWHERE ELSE IN THIS FILE. What is NOT faked is which
    commands run: `SourceCorrespondence` composes them out of
    `integration.git_profile`'s own vectors, and the cases below assert those
    argv word for word. This answers what a container would have printed --
    a resolved commit, a resolved tree, a tree listing -- so the correspondence
    is the product's own reading of a real answer shape.

    A REVISION THIS ENGINE DOES NOT HOLD FAILS THE FETCH, which is what a
    bundle that does not carry the candidate really does.
    """

    def __init__(self, trees=None, holds=None):
        self.trees = trees if trees is not None else {
            BASE: {UNCHANGED: "a" * 40,
                   CHANGED[0]: "b" * 40, CHANGED[1]: "c" * 40},
            HEAD: {UNCHANGED: "a" * 40,
                   CHANGED[0]: "d" * 40, CHANGED[1]: "e" * 40}}
        self.holds = set(self.trees if holds is None else holds)
        self.argv = []

    def __call__(self, argv, input=None):
        held = list(argv)
        self.argv.append(held)
        if held[:2] == ["git", "init"]:
            os.makedirs(held[-1], exist_ok=True)
            return self._said(0, "")
        revision = held[-1]
        if "fetch" in held:
            return self._said(0 if revision in self.holds else 128, "",
                              "" if revision in self.holds
                              else "error: no such ref")
        if "rev-parse" in held:
            name = revision.split("^{")[0]
            if name not in self.trees:
                return self._said(128, "", "unknown revision")
            if revision.endswith("^{tree}"):
                return self._said(0, self.tree_name(name) + "\n")
            return self._said(0, name + "\n")
        if "ls-tree" in held:
            entries = self.trees.get(revision, {})
            return self._said(0, "".join(
                f"100644 blob {oid}\t{path}\x00"
                for path, oid in sorted(entries.items())))
        return self._said(127, "", "unsupported")         # pragma: no cover

    @staticmethod
    def tree_name(revision):
        """One full lowercase object name for a revision's tree.

        DERIVED FROM THE REVISION so two revisions never share a tree name by
        accident, which is the only property the correspondence read actually
        depends on.
        """
        return hashlib.sha1(revision.encode("utf-8")).hexdigest()

    @staticmethod
    def _said(code, out, err=""):
        return {"returncode": code, "stdout": out, "stderr": err}


def owners(request):
    """The owner-port factory the installed command is pointed at.

    THE PRODUCTION SHAPE, with the host's cessation record, the deployment
    binding, the instance guard and the Git ENGINE stood in for. `owner` is
    the real `tools.recovery_decision.OwnerAuthorization` over the case's real
    Authority store; `host` and `source` are the real
    `tools.publication_ports` adapters, so the trust root is read through the
    product's own owner and the correspondence runs the product's own vectors.
    """
    from baton_v12.authority import Authority
    from tools.publication_ports import HostOutput, SourceCorrespondence
    from tools.recovery_decision import OwnerAuthorization

    authority = Authority.open_readonly(
        request["authority"],
        expected_authority_uuid=request["authority_uuid"])
    held = CURRENT.setdefault("ports", {})
    identity = CURRENT["identity"]
    return {
        "owner": OwnerAuthorization(authority,
                                    participant=request["participant"]),
        "host": HostOutput(request["control_handle"], identity),
        "source": held.setdefault("source", SourceCorrespondence(
            identity, scratch=CURRENT["scratch"],
            engine=CURRENT.setdefault("engine", GitEngine()))),
        "authorization": WorkPort(authority, identity=identity),
        "exclusion": held.setdefault("exclusion",
                                     FakeExclusion(identity=identity)),
        "binding": held.setdefault("binding", FakeBinding(identity=identity)),
        "ownership": held.setdefault("ownership",
                                     FakeOwnership(identity=identity)),
        "release": authority.dispose,
    }


class PublicationCase(unittest.TestCase):
    """One completed implementation whose output publication really failed.

    THE JOB IS CREATED BY THE PRODUCT. `creation.create_template_job` admits
    it against the owner-selected `implementation-review/4` revision, so the
    Job id, the stage ids, the episode identities, the submitted input digest
    and the admitted task document are all the creation operation's own -- and
    the attempt this recovery is about is the one episode 1 of the
    implementation stage already names, rather than one this fixture invented.
    """

    maxDiff = None

    def setUp(self):
        from baton_v12.authority import Authority

        self._root = tempfile.TemporaryDirectory(
            prefix="v12-publication-", dir=disk_roots.disk_backed_root())
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.storage = os.path.join(self.root, "storage")
        os.mkdir(self.storage)
        self.scratch = os.path.join(self.root, "scratch")
        os.mkdir(self.scratch)
        self.instants = [NOW]
        self.control = ControlStore.open(
            os.path.join(self.root, "control.sqlite3"),
            incarnation="manager-1", clock=self.clock)
        self.addCleanup(self.control.close)
        self.group = input_roots.configured_group(self.control)
        workspaces.configure_workspace_storage(self.control, self.storage)
        self.jobs = JobStore.open(os.path.join(self.root, "jobs.sqlite3"),
                                  authority_uuid=UUID, incarnation="jobs-1",
                                  clock=self.clock)
        self.addCleanup(self.jobs.close)

        self.authority_path = os.path.join(self.root, "authority.sqlite3")
        authority = Authority.create(self.authority_path, authority_uuid=UUID)
        self.addCleanup(authority.dispose)
        # THE WORK'S OWN EFFECTIVE SCOPE, deliberately NOT the deployment's,
        # so "the grant is in the WORK's scope" is falsifiable.
        authority.create_work(WORK_A, ROUTE, operation_id="bootstrap-job-a",
                              contract="v12-assignment-1", scope=WORK_SCOPE)
        self.work_row = authority.project_work(WORK_A)
        authority.bind_endpoint(OWNER, OWNER_PRINCIPAL)
        for capability in ("approve", "integrate", "close"):
            authority.grant_capability(OWNER, capability,
                                       scope=self.work_row["scope"])
        # AND THE IMPLEMENTER IS A REAL PARTICIPANT WITH REAL GRANTS THAT ARE
        # NOT THIS ONE: `review` in the same scope, so a case about the wrong
        # capability is about a capability rather than about membership.
        authority.add_route_handler(ROUTE, INTRUDER)
        authority.grant_capability(INTRUDER, "review",
                                   scope=self.work_row["scope"])
        self.authority = authority

        CURRENT.clear()
        self.addCleanup(CURRENT.clear)
        CURRENT["identity"] = {
            "root": os.path.join(self.root, "instance"),
            "job_store": os.path.realpath(self.jobs.database),
            "control_store": os.path.realpath(self.control.database),
            "authority_store": os.path.realpath(self.authority_path),
            "authority_uuid": UUID}
        CURRENT["scratch"] = self.scratch
        os.makedirs(CURRENT["identity"]["root"], exist_ok=True)
        held = creation_case.CURRENT.get("identity")
        creation_case.CURRENT["identity"] = CURRENT["identity"]
        self.addCleanup(creation_case.CURRENT.__setitem__, "identity", held)

        self.created = self.create_job()
        self.job_id = self.created["job_id"]
        self.stage_id = documents.stage_id(self.job_id, "implementation")
        self.episode = 1
        self.attempt_id = episodes.episode_of(
            self.jobs, self.stage_id, 1)["attempt_id"]
        self.roots = self.prepared_attempt(self.attempt_id)
        self.original = self.write_output()

    def clock(self):
        return self.instants[-1]

    # -- the failed Job, through the product's own creation -----------------

    def create_job(self, **changed):
        """One real `/4` Job, admitted by the real creation operation."""
        outputs = role_contract.contract_for(
            role_contract.PROPOSAL100M_TEMPLATE)["outputs"]
        derivation = creation_case.FakeDerivation(task=self.composed_task)
        derivation.answer["declarations"] = {
            "implementation": {PRODUCER_PARTICIPANT:
                               [dict(one) for one in outputs]},
            "review": {"review-worker": [dict(one) for one in outputs]}}
        held = {"request": creation_case.request(
            template=role_contract.PROPOSAL100M_TEMPLATE),
            "derivation": derivation,
            "authorization": creation_case.FakeAuthorization(),
            "binding": creation_case.FakeBinding(),
            "ownership": creation_case.FakeOwnership()}
        held.update(changed)
        return creation.create_template_job(
            self.jobs, creation_case.FakeOperations(), **held)

    def composed_task(self, selection, verification=None):
        """The per-Job task this deployment delivers, through its own owner.

        `tools/job_task.py` composes the document and rewrites the input
        manifest's human-contract artifact to describe exactly those bytes, so
        the admitted task the producer's argv is compared against is the
        delivery's own composition rather than this module's idea of one.
        """
        from tools import job_task

        manifest = capability_case.published_input()
        manifest["outputs"] = copy.deepcopy(role_contract.contract_for(
            role_contract.PROPOSAL100M_TEMPLATE)["outputs"])
        manifest["worker_image_digest"] = "sha256:" + "2" * 64
        manifest["runtime_profile_digest"] = "sha256:" + "3" * 64
        manifest["human_contract"] = dict(
            manifest["human_contract"],
            media_type=job_task.CONTRACT_MEDIA_TYPE)
        manifest.pop("manifest_digest", None)
        manifest["manifest_digest"] = digest(manifest)
        installed = json.dumps(
            {"schema": "baton.dogfood-task/2", "task_id": "installed",
             "instructions": "the installed delivery template",
             "declared_base": BASE, "source_profile": "git-line",
             "source_root": "source",
             "verification": ["bash", "-c", "true"]},
            sort_keys=True).encode("utf-8")
        task = job_task.compose_task(
            installed, task_id=selection["job_id"],
            instructions="publish the proposal",
            verification=list(PRODUCER_ARGV if verification is None
                              else verification))
        composed = job_task.manifest_for(manifest, task)
        return {"task_document": task, "input_manifest": composed,
                "input_digest": job_input_identity(composed)}

    # -- the host rows and roots a real ending would have left --------------

    def prepared_attempt(self, attempt_id, participant=PRODUCER_PARTICIPANT):
        """The attempt row, its allocated roots and its COMPLETED preparation.

        The preparation record is what makes the original's object identity
        provable later: `retained_output_of` compares the `device:inode` the
        preparation finished over against the entry that is there now, so a
        root replaced since the attempt ran refuses rather than being measured.
        """
        self.control._connection.execute(
            "INSERT INTO attempts (runtime_attempt_id, adapter_name, "
            "adapter_digest, profile_digest, created_at, work_id, "
            "authority_uuid, assignment_participant, assignment_generation, "
            "assignment_claim_event_seq, assignment_principal, "
            "assignment_scope, assignment_role, assignment_grant, "
            "assignment_policy_generation) VALUES (?, 'adapter', "
            "'adapter-digest', 'profile-digest', ?, ?, ?, ?, 1, 1, ?, ?, "
            "'role', 'grant', 1)",
            (attempt_id, NOW, WORK_A, UUID, participant,
             "principal:" + participant, WORK_SCOPE))
        self.control._connection.execute(
            "UPDATE attempts SET runtime_id = ?, execution_runtime = "
            "'destroyed', cleanup = 'retained' WHERE runtime_attempt_id = ?",
            ("runtime-" + attempt_id, attempt_id))
        roots = workspaces.assignment_workspace(self.group, self.storage,
                                                attempt_id)
        workspaces.record_preparation(self.control, attempt_id, roots,
                                      ["task", "inputs"])
        return roots

    def write_output(self, *, result=None, extra=None, pad=None,
                     envelope=False, roots=None):
        """The ORIGINAL proposal tree, really on disk, really over the ceiling.

        The producer measured this tree, found it wider than the 1048576 bytes
        its declaration allowed, refused it and published no completion
        envelope -- so there is no `output.json` here and nothing was ever
        frozen. The padding is what makes the overflow real rather than
        asserted.
        """
        place = os.path.join(
            (roots or self.roots)["workspace"], role_contract.CANDIDATE_OUTPUT)
        os.makedirs(place, exist_ok=True)
        document = proposal_result() if result is None else result
        if isinstance(document, dict) and document.get("task_id") is None:
            document = dict(document, task_id=self.job_id)
        payload = (json.dumps(document, indent=1, sort_keys=True).encode(
            "utf-8") if isinstance(document, dict) else document)
        files = {"result.json": payload,
                 "objects.bundle": b"BUNDLE\n",
                 "verification.txt": b"$ bash -c ...\nexit: 0\n",
                 "change.patch": b"P" * (1048577 if pad is None else pad)}
        files.update(extra or {})
        if envelope:
            files = dict(files)
        for name, content in files.items():
            with open(os.path.join(place, name), "wb") as handle:
                handle.write(content)
        if envelope:
            with open(os.path.join((roots or self.roots)["workspace"],
                                   "output.json"), "wb") as handle:
                handle.write(b"{}")
        # THE ORIGINAL IS THE DECLARED OUTPUT DIRECTORY, which is what the
        # host owner proves and measures (review 2026-11-23T20-28-00Z F1).
        return workspaces.directory_manifest(place)

    # -- the installed command ----------------------------------------------

    def argv(self, command, *extra):
        return [command,
                "--store", self.jobs.database,
                "--authority-uuid", UUID,
                "--incarnation", "publication-1",
                "--control", self.control.database,
                "--authority", self.authority_path,
                "--instance", CURRENT["identity"]["root"],
                "--owners", "tests.job_manager."
                            "test_publication_recovery_admission:owners",
                "--job", self.job_id,
                "--stage", self.stage_id,
                "--episode", str(self.episode),
                *extra]

    def command(self, *argv, clock=None):
        """Run the installed owner command and return `(code, document)`."""
        from tools import job_manager

        said = io.StringIO()
        code = job_manager.main(list(argv), clock=clock or (lambda: NOW),
                                stream=said)
        text = said.getvalue()
        return code, (json.loads(text) if text.strip() else None)

    def read(self, *extra):
        code, document = self.command(*self.argv("publication-inspect",
                                                 *extra))
        self.assertEqual(code, 0)
        return document

    def decide_argv(self, selection, *, decision_id="D1",
                    disposition="--approve", participant=OWNER,
                    producer=None, stages=None, **changed):
        """The operands an owner copies out of what they were just shown.

        EVERY VALUE DEFAULTS TO THE INSPECTION'S OWN, which is what makes a
        negative case a one-operand change: `expect_output_digest=...` is the
        only thing that differs between the positive path and the wrong-digest
        refusal, so the refusal cannot be passing for another reason.
        """
        held = {"decision-id": decision_id, "participant": participant,
                "expect-attempt": selection["selector"]["attempt_id"],
                "expect-selection-digest": selection["selection_digest"],
                "expect-candidate-base": selection["producer"]["base"],
                "expect-candidate-head": selection["producer"]["head"],
                "expect-output-digest": selection["output"]["tree_digest"],
                "expect-output-bytes": selection["output"]["total_bytes"],
                "expect-producer-status": selection["producer"]["status"],
                "context-digest": selection["producer"]["context_digest"],
                "declaration-digest": selection["declaration"]["digest"],
                "profile": selection["profile"]["profile"],
                "profile-digest": selection["profile"]["digest"]}
        held.update({one.replace("_", "-"): value
                     for one, value in changed.items()})
        flat = [f"--{one}={value}" for one, value in held.items()
                if value is not None]
        for word in (selection["producer"]["argv"] if producer is None
                     else producer):
            flat.append(f"--producer-verification={word}")
        for word in (list(publication_recovery.SELECTED_STAGES)
                     if stages is None else stages):
            flat.append(f"--stage-word={word}")
        return self.argv("publication-decide", disposition, *flat)

    def decide(self, selection, *, clock=None, **changed):
        return self.command(*self.decide_argv(selection, **changed),
                            clock=clock)

    # -- readers a case asserts against -------------------------------------

    def ports(self):
        return CURRENT.setdefault("ports", {})

    def engine(self):
        return CURRENT.setdefault("engine", GitEngine())

    def refusal(self, call, *operands, **named):
        with self.assertRaises(ContractRefusal) as caught:
            call(*operands, **named)
        return caught.exception

    def job_rows(self):
        return [row[0] for row in self.jobs._connection.execute(
            "SELECT job_id FROM jobs ORDER BY job_id")]

    def stage_rows(self):
        return [tuple(row) for row in self.jobs._connection.execute(
            "SELECT stage_id, job_id, kind FROM stages ORDER BY stage_id")]

    def allocation_rows(self):
        return [tuple(row) for row in self.jobs._connection.execute(
            "SELECT assignment_id, stage_id, lane, allocation_state FROM "
            "stage_allocations ORDER BY assignment_id")]

    def episode_rows(self):
        return [tuple(row) for row in self.jobs._connection.execute(
            "SELECT stage_id, episode, attempt_id, ended_state FROM episodes "
            "ORDER BY stage_id, episode")]

    def journal(self, kind):
        return [row[0] for row in self.jobs._connection.execute(
            "SELECT operation_id FROM operations WHERE kind = ? ORDER BY "
            "operation_id", (kind,))]

    def control_bytes(self):
        with open(self.control.database, "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()

    def original_digest(self):
        return workspaces.directory_manifest(os.path.join(
            self.roots["workspace"],
            role_contract.CANDIDATE_OUTPUT))["tree_digest"]

    def ported(self):
        """The product's own ports, composed exactly as the command does."""
        from tools.publication_ports import HostOutput, SourceCorrespondence

        held = self.ports()
        return {
            "host": HostOutput(self.control, CURRENT["identity"]),
            "source": held.setdefault("source", SourceCorrespondence(
                CURRENT["identity"], scratch=self.scratch,
                engine=self.engine())),
            "exclusion": held.setdefault(
                "exclusion", FakeExclusion(identity=CURRENT["identity"])),
            "binding": held.setdefault(
                "binding", FakeBinding(identity=CURRENT["identity"])),
            "ownership": held.setdefault(
                "ownership", FakeOwnership(identity=CURRENT["identity"])),
            "authorization": WorkPort(self.authority,
                                      identity=CURRENT["identity"])}

    def inspected(self, **changed):
        held = self.ported()
        return publication_recovery.inspect(
            self.jobs, self.control, job_id=changed.pop("job_id", self.job_id),
            stage_id=changed.pop("stage_id", self.stage_id),
            episode=changed.pop("episode", self.episode),
            host=held["host"], exclusion=held["exclusion"],
            source=held["source"], **changed)

    def approved(self, selection=None, *, decision_id="D1", now=NOW,
                 participant=OWNER, **changed):
        """One APPROVED decision through the operation, for the cases that are
        about the ADMISSION rather than about the decision."""
        from tools.recovery_decision import OwnerAuthorization

        selection = self.inspected() if selection is None else selection
        held = self.ported()
        expected = publication_recovery.expected_facts(selection)
        expected.update(changed.pop("expected", {}))
        return publication_recovery.decide(
            self.jobs, self.control, job_id=self.job_id,
            stage_id=self.stage_id, episode=self.episode,
            decision_id=decision_id, disposition="approved",
            authorization=OwnerAuthorization(self.authority,
                                             participant=participant),
            expected=expected,
            profile=selection["profile"]["profile"],
            profile_digest=selection["profile"]["digest"],
            stages=list(publication_recovery.SELECTED_STAGES),
            declaration_digest=selection["declaration"]["digest"],
            host=held["host"], exclusion=held["exclusion"],
            source=held["source"], now=now, **changed)

    def admitted(self, *, decision_id="D1", now=NOW, store=None, **changed):
        held = self.ported()
        held.update(changed)
        return publication_recovery.admit_publication(
            store if store is not None else self.jobs, self.control,
            decision_id=decision_id, exclusion=held["exclusion"],
            authorization=held["authorization"], binding=held["binding"],
            ownership=held["ownership"], host=held["host"],
            source=held["source"], now=now)


# -- 1. the ordinary outcome -------------------------------------------------


class TheOwnerInspectsTheOriginalAndDecidesIt(PublicationCase):
    """The first usable result of checkpoint 1, through the installed command."""

    def test_the_inspection_presents_every_fact_a_decision_must_bind(self):
        read = self.read()
        self.assertEqual(read["schema"], publication_recovery.READ_SCHEMA)
        self.assertEqual(read["holds"], [])
        self.assertTrue(read["eligible"])
        # THE EXACT FAILED EXECUTION, resolved from the Job's own rows.
        self.assertEqual(read["selector"]["job_id"], self.job_id)
        self.assertEqual(read["selector"]["stage_id"], self.stage_id)
        self.assertEqual(read["selector"]["attempt_id"], self.attempt_id)
        self.assertEqual(read["selector"]["work_id"], WORK_A)
        self.assertEqual(read["selector"]["participant"],
                         PRODUCER_PARTICIPANT)
        # NOTHING WAS PUBLISHED, which is what makes this the trigger.
        self.assertIsNone(read["job"]["published_result"])
        self.assertFalse(read["output"]["completion_envelope"])
        # THE ORIGINAL, MEASURED, bound to bytes rather than to a path.
        self.assertEqual(read["output"]["tree_digest"],
                         self.original["tree_digest"])
        self.assertEqual(read["output"]["total_bytes"],
                         self.original["total_bytes"])
        self.assertTrue(read["output"]["exceeded"])
        self.assertTrue(read["output"]["fits_corrective"])
        # PATHS INSIDE THE DECLARED OUTPUT DIRECTORY, which is the original.
        self.assertIn("result.json", read["output"]["paths"])
        self.assertNotIn("proposal/result.json", read["output"]["paths"])

    def test_the_producer_account_is_qualified_and_is_not_acceptance(self):
        read = self.read()
        producer = read["producer"]
        self.assertEqual(producer["argv"], PRODUCER_ARGV)
        self.assertEqual(producer["status"], 0)
        self.assertEqual(producer["declared_ending"], "candidate")
        self.assertEqual(producer["task_id"], self.job_id)
        self.assertEqual(producer["base"], BASE)
        self.assertEqual(producer["head"], HEAD)
        self.assertEqual(producer["changed_paths"], sorted(CHANGED))
        self.assertEqual(producer["attributed_to"], "role-adapter")
        # THE TWO SENTENCES THAT KEEP THIS EVIDENCE WHAT IT IS.
        self.assertEqual(producer["qualification"], "producer-evidence")
        self.assertFalse(producer["independent_acceptance"])
        self.assertIn("still owes its own required verification",
                      producer["reuse"])
        # AND WHAT THE REVIEWER OWES, in the selection the owner approves.
        self.assertEqual(read["reviewer"]["independent_verification"],
                         "required")
        self.assertEqual(read["reviewer"]["investigation_and_tests"],
                         "required")
        self.assertEqual(read["reviewer"]["invocation_seconds"], 3600)
        self.assertEqual(read["reviewer"]["each_command_seconds"], 900)

    def test_the_correspondence_runs_the_source_owners_own_vectors(self):
        """THE COMMANDS ARE THE PRODUCT'S, word for word.

        What a focused case fakes is the ENGINE those vectors are handed to.
        Asserting the argv is what makes this the real source composition
        rather than a port that answered a dictionary.
        """
        read = self.read()
        held = read["correspondence"]
        self.assertEqual(held["base"], BASE)
        self.assertEqual(held["candidate"], HEAD)
        self.assertEqual(held["changed_paths"], sorted(CHANGED))
        repository = self.engine().argv[0][-1]
        bundle = os.path.join(self.roots["workspace"],
                              role_contract.CANDIDATE_OUTPUT,
                              "objects.bundle")
        self.assertEqual(self.engine().argv[0][:4],
                         ["git", "init", "--bare", "--quiet"])
        self.assertIn(git_profile.import_vector(repository, bundle, HEAD),
                      self.engine().argv)
        self.assertIn(git_profile.verify_vector(repository, HEAD),
                      self.engine().argv)
        self.assertIn(git_profile.tree_entries_vector(repository, HEAD),
                      self.engine().argv)
        # AND THE SCRATCH IS GONE: a private object store left behind by a
        # read is host state nothing owns.
        self.assertFalse(os.path.exists(repository))

    def test_the_selected_identities_and_profile_are_the_owners_exact_ones(self):
        read = self.read()
        self.assertEqual(read["declaration"]["descriptor"],
                         role_contract.PROPOSAL100M_CONTRACT_SCHEMA)
        self.assertEqual(read["declaration"]["template"],
                         role_contract.PROPOSAL100M_TEMPLATE)
        self.assertEqual(read["declaration"]["output"]["constraints"],
                         {"max_bytes": 104857600, "max_entries": 100,
                          "allowed_media_types": read["declaration"]["output"][
                              "constraints"]["allowed_media_types"],
                          "link_policy": "forbid", "validator_digest": None})
        profile = read["profile"]
        self.assertEqual(profile["profile"], "output-publication-review/1")
        self.assertEqual(profile["overall_job_seconds"], 9960)
        self.assertTrue(profile["overall_job_includes_queue"])
        self.assertEqual(profile["each_stage_seconds"], 4800)
        self.assertEqual(profile["publication_stage_seconds"], 900)
        self.assertEqual(profile["publication_stage_origin"],
                         "stage_admission")
        self.assertFalse(profile["publication_stage_restart_resets"])
        self.assertEqual(profile["review_provider_invocation_seconds"], 3600)
        self.assertTrue(profile["review_provider_invocation_covers_tests"])
        self.assertEqual(profile["verification_command_seconds"], 900)
        self.assertEqual(profile["verification_command_applies_to"],
                         "each_reviewer_command")
        self.assertEqual((profile["automatic_retries"],
                          profile["automatic_corrections"],
                          profile["automatic_continuations"]), (0, 0, 0))
        self.assertEqual(read["stages"], [["publication", "review"]])
        self.assertEqual(read["provenance"],
                         {"name": "recovery-provenance", "max_bytes": 16384,
                          "max_entries": 1, "regular_files_only": True,
                          "link_policy": "forbid"})

    def test_the_inspection_says_whether_the_asker_may_decide_at_all(self):
        mine = self.read("--participant", OWNER)
        self.assertTrue(mine["authorization"]["holds"])
        self.assertEqual(mine["authorization"]["principal"], OWNER_PRINCIPAL)
        self.assertEqual(mine["authorization"]["work_scope"], WORK_SCOPE)
        theirs = self.read("--participant", INTRUDER)
        self.assertFalse(theirs["authorization"]["holds"])
        self.assertEqual(theirs["authorization"]["why"]["code"], "denied")
        self.assertIn("approve", theirs["authorization"]["why"]["message"])

    def test_the_inspection_writes_nothing_anywhere(self):
        """READ-ONLY, proved by comparing the bytes on both sides.

        The Job store's rows, the control store's whole file and the measured
        original are compared across two inspections and an authorization
        probe, which is the strongest statement this fixture can make about a
        surface whose entire promise is that it changes nothing.
        """
        before = (self.job_rows(), self.stage_rows(), self.episode_rows(),
                  self.allocation_rows(), self.control_bytes(),
                  self.original_digest())
        first = self.read()
        self.read("--participant", OWNER)
        second = self.read()
        after = (self.job_rows(), self.stage_rows(), self.episode_rows(),
                 self.allocation_rows(), self.control_bytes(),
                 self.original_digest())
        self.assertEqual(before, after)
        self.assertEqual(first["selection_digest"],
                         second["selection_digest"])
        self.assertEqual(self.journal(publication_recovery.DECISION_KIND), [])
        self.assertEqual(self.journal(publication_recovery.HELD_KIND), [])


class TheApprovalReachesAClosedAdmissionBoundary(PublicationCase):
    """What an approval actually gets, and what it truthfully does not."""

    def test_the_decision_binds_the_exact_selection_and_admits_nothing(self):
        read = self.read()
        code, answer = self.decide(read)
        self.assertEqual(code, 0)
        decision = answer["decision"]
        self.assertEqual(decision["disposition"], "approved")
        self.assertEqual(decision["attempt_id"], self.attempt_id)
        self.assertEqual(decision["expected"]["selection_digest"],
                         read["selection_digest"])
        self.assertEqual(decision["expected"]["output_tree_digest"],
                         self.original["tree_digest"])
        self.assertEqual(decision["expected"]["producer_argv"], PRODUCER_ARGV)
        self.assertEqual(decision["owner"]["endpoint"], OWNER)
        self.assertEqual(decision["owner"]["effective_scope"], WORK_SCOPE)
        self.assertEqual(decision["stages"], ["publication", "review"])
        # AND THE BOUNDARY'S OWN ANSWER.
        self.assertFalse(answer["admitted"])
        admission = answer["admission"]
        self.assertEqual(admission["state"], "held")
        self.assertFalse(admission["reserved"])
        self.assertEqual(admission["job_id"], "publication-D1")
        self.assertEqual(admission["work_id"], WORK_A)
        self.assertEqual(admission["owners"]["work"],
                         {"work_id": WORK_A, "disposition": "reused",
                          "status": "open"})
        self.assertEqual(admission["readiness"]["offers"], 0)
        self.assertEqual(admission["readiness"]["review"], "blocked")
        self.assertIn("reserved no Job identity",
                      admission["readiness"]["detail"])

    def test_every_missing_prerequisite_is_named_with_the_owner_that_holds_it(self):
        """WHAT THIS INSTANCE CANNOT SERVE, named by the owner that holds it.

        W385695 checkpoint 2 INSTALLED THIS BUILD'S FOUR -- the `/4`
        generation, the publication lane under `baton.v12.worker-pool/2`,
        store generation 10 and the enforced control profile -- so this case
        no longer asserts their absence. What it asserts instead is the
        property that outlives them: the answer is read from the owner that
        holds each fact, so the ONE this fixture's deployment does not hold
        is the one reported missing. THIS FIXTURE'S BINDING PORT ANSWERS FOR
        NO PUBLICATION WORKER, which is a real deployment state -- an
        instance that has not installed the reusable worker -- and it is
        exactly what must keep an admission held.
        """
        read = self.read()
        _code, answer = self.decide(read)
        owed = {one["name"]: one for one in
                answer["admission"]["prerequisites"]}
        self.assertEqual(sorted(owed),
                         ["job-store-generation", "publication-control-profile",
                          "publication-lane", "publication-stage-vocabulary",
                          "publication-worker"])
        self.assertEqual(sorted(name for name, one in owed.items()
                                if not one["available"]),
                         ["publication-worker"])
        self.assertTrue(all(one["checkpoint"] == 2 for one in owed.values()))
        # THE LANE IS THE ONE THAT MATTERS, and the fact behind it is still
        # read from the scheduler rather than asserted: the stage-to-lane map
        # now sends a publication stage to its OWN lane, which is what
        # "never map publication to implementation" requires.
        self.assertIn("publication", scheduler.LANES)
        self.assertEqual(scheduler.lane_of("publication"), "publication")
        self.assertIn("'publication'", owed["publication-lane"]["observed"])
        self.assertIn("publication", documents.STAGE_KINDS)
        self.assertNotIn("publication", documents.ORDINARY_STAGE_KINDS)
        self.assertIn(publication_recovery.RECOVERY_SUBMISSION,
                      documents.SUBMISSION_SCHEMAS)
        self.assertEqual(
            owed["publication-worker"]["observed"][:9], "not asked")

    def test_the_review_gate_is_closed_and_nothing_is_runnable(self):
        read = self.read()
        _code, answer = self.decide(read)
        gate = answer["gate"]
        self.assertFalse(gate["open"])
        self.assertFalse(gate["runnable"])
        self.assertEqual(gate["reason"],
                         publication_recovery.GATE_UNAVAILABLE)
        self.assertEqual(gate["decision_id"], "D1")
        self.assertEqual(gate["prior_job_id"], self.job_id)
        self.assertEqual(gate["candidate"]["head"], HEAD)
        # ONE PREREQUISITE, because this fixture's deployment installs no
        # publication worker; the other four are this build's and checkpoint 2
        # installed them. The gate is shut either way, and `runnable` is False
        # either way, which is the property this case is about.
        self.assertEqual(sorted(gate["prerequisites"]),
                         ["publication-worker"])

    def test_the_whole_path_starts_nothing_and_reserves_no_identity(self):
        """ZERO publication, reviewer and provider starts, proved by absence.

        Every row that could become an execution is compared across the whole
        path -- Jobs, stages, episodes and scheduler allocations -- and the
        derived recovery identity is looked for by name. The original Job's
        own rows are included, so an admission that quietly advanced the
        failed Job would be caught here too.
        """
        before = (self.job_rows(), self.stage_rows(), self.episode_rows(),
                  self.allocation_rows())
        read = self.read()
        self.decide(read)
        self.assertEqual((self.job_rows(), self.stage_rows(),
                          self.episode_rows(), self.allocation_rows()),
                         before)
        self.assertNotIn("publication-D1", self.job_rows())
        self.assertEqual(self.jobs._connection.execute(
            "SELECT count(*) FROM jobs WHERE job_id LIKE 'publication-%'"
        ).fetchone()[0], 0)
        self.assertEqual(self.jobs._connection.execute(
            "SELECT count(*) FROM submissions WHERE submission_id LIKE "
            "'sub-publication-%'").fetchone()[0], 0)
        # AND NO DEPLOYMENT WAS ASKED TO BIND OR SERVE ANYTHING.
        self.assertEqual(self.ports()["binding"].added, [])
        self.assertEqual(self.ports()["binding"].asked, [])

    def test_the_original_job_and_its_bytes_are_untouched(self):
        job = submission.job_of(self.jobs, self.job_id)
        stages = submission.stages_of(self.jobs, self.job_id)
        control = self.control_bytes()
        original = self.original_digest()
        read = self.read()
        self.decide(read)
        self.assertEqual(submission.job_of(self.jobs, self.job_id), job)
        self.assertEqual(submission.stages_of(self.jobs, self.job_id), stages)
        self.assertEqual(self.control_bytes(), control)
        self.assertEqual(self.original_digest(), original)
        self.assertEqual(self.original_digest(),
                         read["output"]["tree_digest"])

    def test_a_hold_and_a_denial_are_recorded_and_launch_nothing(self):
        read = self.read()
        code, answer = self.decide(read, disposition="--hold",
                                   decision_id="D-hold")
        self.assertEqual(code, 0)
        self.assertEqual(answer["decision"]["disposition"], "held")
        self.assertIsNone(answer["admission"])
        code, answer = self.decide(read, disposition="--deny",
                                   decision_id="D-deny")
        self.assertEqual(code, 0)
        self.assertEqual(answer["decision"]["disposition"], "denied")
        self.assertIsNone(answer["admission"])
        self.assertEqual(self.journal(publication_recovery.HELD_KIND), [])
        # AND NEITHER ONE MAY BE CARRIED OUT BY THE BOUNDARY.
        for decision_id in ("D-hold", "D-deny"):
            caught = self.refusal(self.admitted, decision_id=decision_id)
            self.assertEqual((caught.category, caught.code),
                             ("policy", "denied"))
            self.assertIn("launches nothing", caught.message)


# -- 2. the trust root, and every way it is not one --------------------------


class TheOriginalIsTheTrustRootAndNothingElseIs(PublicationCase):
    """REC-9's first rule, driven one absence at a time."""

    def test_a_missing_original_holds_and_decides_nothing(self):
        import shutil

        shutil.rmtree(os.path.join(self.storage, self.attempt_id))
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertIsNone(read["output"])
        self.assertIsNone(read["producer"])
        self.assertIsNone(read["correspondence"])
        self.assertTrue(read["holds"])
        # AND NO DECISION IS TAKEN ABOUT IT. The inspection has no exact
        # facts to offer -- there is nothing to approve -- and the operation
        # refuses rather than recording a disposition about an absence.
        caught = self.refusal(publication_recovery.expected_facts, read)
        self.assertIn("no exact facts", caught.message)
        from tools.recovery_decision import OwnerAuthorization

        held = self.ported()
        caught = self.refusal(
            publication_recovery.decide, self.jobs, self.control,
            job_id=self.job_id, stage_id=self.stage_id,
            episode=self.episode, decision_id="D1", disposition="approved",
            authorization=OwnerAuthorization(self.authority,
                                             participant=OWNER),
            expected={"attempt_id": self.attempt_id,
                      "producer_argv": list(PRODUCER_ARGV),
                      "producer_status": 0, "candidate_base": BASE,
                      "candidate_head": HEAD,
                      "output_tree_digest": "sha256:" + "0" * 64,
                      "output_total_bytes": 1,
                      "verification_context_digest": "sha256:" + "0" * 64,
                      "selection_digest": "sha256:" + "0" * 64},
            profile=publication_recovery.PUBLICATION_PROFILE,
            profile_digest=publication_recovery.PUBLICATION_PROFILE_DIGEST,
            stages=list(publication_recovery.SELECTED_STAGES),
            declaration_digest=publication_recovery.corrective_declaration()[
                "digest"],
            host=held["host"], exclusion=held["exclusion"],
            source=held["source"], now=NOW)
        self.assertIn("is held and is not decided about", caught.message)
        self.assertEqual(self.journal(publication_recovery.DECISION_KIND), [])

    def test_a_replaced_output_root_is_a_substituted_original(self):
        """A directory of the right shape at the right path is not the same
        object, and the completed preparation's `device:inode` is what says so."""
        import shutil

        place = self.roots["workspace"]
        # MOVED ASIDE RATHER THAN REMOVED, so the original object stays
        # allocated and the replacement cannot inherit its inode -- which is
        # the one way a case about object identity can accidentally pass.
        os.rename(place, place + "-moved-aside")
        os.makedirs(os.path.join(place, role_contract.CANDIDATE_OUTPUT))
        read = self.read()
        self.assertFalse(read["eligible"])
        held = read["holds"][0]
        self.assertEqual((held["category"], held["code"]),
                         ("runtime-observation", "identity-mismatch"))
        self.assertIn("replaced object", held["message"])

    def test_an_unsettled_writer_holds_before_anything_is_measured(self):
        """`settlement_preparation` refuses while any governed writer of this
        attempt's roots has been admitted and not completed."""
        workspaces.admit_cleanup(
            self.control, self.attempt_id,
            {"operation": "cleanup-" + self.attempt_id,
             "signature": "sha256:" + "7" * 64, "incarnation": "manager-1"},
            "a fixture's unfinished cleanup")
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertIsNone(read["output"])
        self.assertIn("unsettled cleanup",
                      " ".join(one["message"] for one in read["holds"]))

    def test_an_uncertain_host_runtime_holds_the_whole_recovery(self):
        self.ports()["exclusion"] = FakeExclusion(
            answer={"runtime": {"attempt_id": None, "runtime_id": "r",
                                "execution_runtime": "running",
                                "cleanup": "pending", "assignment": None},
                    "token": {"returned": False}},
            identity=CURRENT["identity"])
        read = self.read()
        self.assertFalse(read["eligible"])
        held = [one for one in read["holds"]
                if one["code"] == "quiescence-unknown"]
        self.assertTrue(held)
        self.assertFalse(read["exclusion"][self.attempt_id]["ceased"])

    def test_a_host_that_has_never_heard_of_the_attempt_holds(self):
        class Silent(FakeExclusion):
            def evidence_of(self, attempt_ids):
                return {"host": CURRENT["identity"]["control_store"]}

        self.ports()["exclusion"] = Silent(identity=CURRENT["identity"])
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertIn("unknown is not permission",
                      " ".join(one["message"] for one in read["holds"]))

    def test_a_published_result_is_not_this_trigger_and_is_not_reclassified(self):
        """An attempt that FROZE a result published its output; whatever went
        wrong afterwards is the ordinary collection path's."""
        document = {"schema": "baton.worker-manifest/result",
                    "result_id": "result-" + self.attempt_id,
                    "assignment_ref": {
                        "work_ref": {"authority_uuid": UUID,
                                     "work_id": WORK_A},
                        "participant": PRODUCER_PARTICIPANT, "generation": 1},
                    "disposition": "completed", "outputs": [],
                    "input_manifest_digest": "sha256:" + "4" * 64}
        self.control._connection.execute(
            "INSERT INTO outputs (runtime_attempt_id, result_id, disposition, "
            "manifest_digest, freeze_operation_id, frozen_at) VALUES "
            "(?, ?, 'completed', ?, ?, ?)",
            (self.attempt_id, document["result_id"], "sha256:" + "5" * 64,
             "freeze-" + self.attempt_id, NOW))
        caught = self.refusal(self.inspected)
        self.assertIn("FROZE result", caught.message)

    def test_a_completion_envelope_means_the_producer_signalled_completion(self):
        self.write_output(envelope=True)
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertTrue(read["output"]["completion_envelope"])
        self.assertIn("completion signal",
                      " ".join(one["message"] for one in read["holds"]))


class TheBytesAreJudgedAgainstTheExactDeclarations(PublicationCase):
    """W385694's selected declaration, enforced on a real measurement."""

    def test_an_output_inside_the_original_ceiling_is_another_cause(self):
        self.write_output(pad=16)
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertFalse(read["output"]["exceeded"])
        self.assertIn(str(role_contract.MAX_OUTPUT_BYTES),
                      " ".join(one["message"] for one in read["holds"]))

    def test_an_output_past_the_selected_ceiling_is_not_published_either(self):
        """THE MEASUREMENT DECIDES IT, and the measurement is the workspace
        owner's. Nothing here widens a declaration to make an original fit."""
        read = self.inspected()
        self.assertTrue(read["output"]["fits_corrective"])
        self.assertLessEqual(read["output"]["total_bytes"],
                             role_contract.MAX_PROPOSAL_BYTES)
        # The ceiling itself is W385694's exact selected value, read from its
        # owner rather than restated here.
        self.assertEqual(
            read["declaration"]["output"]["constraints"]["max_bytes"],
            role_contract.MAX_PROPOSAL_BYTES)
        self.assertEqual(role_contract.MAX_PROPOSAL_BYTES, 104857600)

    def test_more_entries_than_the_declaration_allows_holds(self):
        self.write_output(extra={str(one): b"x" for one in range(100)})
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertGreater(read["output"]["entry_count"], 100)
        self.assertIn("entry ceiling",
                      " ".join(one["message"] for one in read["holds"]))


class TheProducerAttributionIsQualifiedOrItHolds(PublicationCase):
    """REC-9's reuse clause, clause by clause, one operand at a time."""

    def held(self, **changed):
        self.write_output(result=proposal_result(**changed))
        read = self.read()
        self.assertFalse(read["eligible"])
        return " ".join(one["message"] for one in read["holds"])

    def test_a_non_zero_producer_status_is_rec_8s_trigger_and_not_this_one(self):
        self.assertIn("exit 0", self.held(
            verification={"argv": list(PRODUCER_ARGV), "status": 1}))

    def test_an_absent_verification_record_is_unknown_and_unknown_holds(self):
        self.assertIn("UNKNOWN", self.held(verification=None))

    def test_a_command_the_admitted_task_did_not_declare_is_not_attributable(self):
        self.assertIn(
            "attributable only when it is the task's own",
            self.held(verification={"argv": ["bash", "-c", "true"],
                                    "status": 0}))

    def test_a_record_about_another_task_is_not_evidence_about_this_one(self):
        self.assertIn("another task", self.held(task_id="job-somebody-else"))

    def test_a_producer_that_did_not_complete_has_nothing_to_publish(self):
        self.assertIn("recovery follows a producer that declared",
                      self.held(disposition="no-candidate"))

    def test_a_provider_failure_is_a_different_ending(self):
        self.assertIn("provider failure", self.held(
            provider={"failure_reason": "timeout", "seconds_bound": 7200,
                      "seconds_bound_source": "job-selected", "status": 1}))

    def test_a_changed_input_identity_cannot_hide_behind_a_command(self):
        self.assertIn("changed input identity", self.held(base="d" * 40))

    def test_a_generation_this_build_cannot_read_is_not_part_read(self):
        self.assertIn("does not read",
                      self.held(schema="baton.dogfood-proposal/9"))

    def test_an_unreadable_attribution_holds_rather_than_being_interpreted(self):
        self.write_output(result=b"{ this is not a document")
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertIn("not a readable document",
                      " ".join(one["message"] for one in read["holds"]))

    def test_an_absent_result_json_binds_nothing(self):
        place = os.path.join(self.roots["workspace"],
                             role_contract.CANDIDATE_OUTPUT, "result.json")
        os.unlink(place)
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertIn("measured no such entry",
                      " ".join(one["message"] for one in read["holds"]))


class TheCandidateMustCorrespondThroughTheSourceOwner(PublicationCase):
    """The Git-aware consumer's answer, and what happens when it refuses."""

    def test_a_bundle_that_does_not_carry_the_candidate_holds(self):
        CURRENT["engine"] = GitEngine(holds=[BASE])
        self.ports().pop("source", None)
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertIsNone(read["correspondence"])
        self.assertIn("does not carry",
                      " ".join(one["message"] for one in read["holds"]))

    def test_two_accounts_of_one_candidates_paths_are_not_half_resolved(self):
        engine = GitEngine()
        engine.trees[HEAD] = dict(engine.trees[HEAD],
                                  **{"v12/extra.py": "9" * 40})
        CURRENT["engine"] = engine
        self.ports().pop("source", None)
        read = self.read()
        self.assertFalse(read["eligible"])
        held = read["holds"][0]
        self.assertEqual((held["category"], held["code"]),
                         ("ambiguous", "collection"))
        self.assertIn("picking a half", held["message"])

    def test_the_measured_original_must_carry_exactly_one_bundle(self):
        self.write_output(extra={"second.bundle": b"B"})
        os.rename(os.path.join(self.roots["workspace"],
                               role_contract.CANDIDATE_OUTPUT,
                               "second.bundle"),
                  os.path.join(self.roots["workspace"],
                               role_contract.CANDIDATE_OUTPUT,
                               "objects.bundle.keep"))
        import shutil

        # A SECOND BUNDLE OF THE SAME NAME INSIDE THE ORIGINAL, one level
        # down. It used to be placed at the writable root beside the declared
        # output, which is no longer part of what is measured.
        os.mkdir(os.path.join(self.roots["workspace"],
                              role_contract.CANDIDATE_OUTPUT, "second"))
        shutil.copyfile(
            os.path.join(self.roots["workspace"],
                         role_contract.CANDIDATE_OUTPUT, "objects.bundle"),
            os.path.join(self.roots["workspace"],
                         role_contract.CANDIDATE_OUTPUT, "second",
                         "objects.bundle"))
        read = self.read()
        self.assertFalse(read["eligible"])
        self.assertIn("exactly one measured file",
                      " ".join(one["message"] for one in read["holds"]))


# -- 3. authority, scope and the exact selectors -----------------------------


class OnlyTheAuthorizedOwnerDecidesAndOnlyInTheWorksScope(PublicationCase):
    """The Authority's own seam, with a real grant and a real absence."""

    def test_a_participant_holding_another_capability_is_denied(self):
        read = self.read()
        code, answer = self.decide(read, participant=INTRUDER)
        self.assertEqual(code, 1)
        self.assertIsNone(answer)
        self.assertEqual(self.journal(publication_recovery.DECISION_KIND), [])

    def test_an_address_this_authority_does_not_know_is_denied(self):
        read = self.read()
        code, _answer = self.decide(read, participant="baton.nobody")
        self.assertEqual(code, 1)
        self.assertEqual(self.journal(publication_recovery.DECISION_KIND), [])

    def test_a_terminal_work_is_not_reopened_by_a_recovery(self):
        # CLOSED THROUGH THE AUTHORITY'S OWN TERMINAL ACT, so the status the
        # recovery reads is a real one rather than a port's claim about one.
        self.authority._core.close(
            WORK_A, operation_id="close-job-a", outcome="satisfying",
            rationale="the owner closed it", actor=OWNER)
        self.assertEqual(
            self.authority.project_work(WORK_A)["status"], "closed")
        caught = self.refusal(self.approved)
        self.assertIn("publication recovery reuses the ORIGINAL OPEN Work",
                      caught.message)

    def test_the_scope_is_the_works_own_and_is_not_an_operand(self):
        """There is no `--scope` and no `--actor` on this surface at all.

        W385695 checkpoint 2 CORRECTED THIS CASE, and the correction is the
        point of reading it. The loop below used to search
        `publication_decision.main.__module__`, which is the string
        `'tools.publication_decision'` -- a module NAME. Every assertion in it
        was vacuously true: `'--scope '` is not a substring of a dotted module
        path and never could be, so a surface that really did grow an
        `--actor` operand would have passed unchanged. The native reviewer
        named it and it is fixed here rather than carried forward.

        WHAT IT SEARCHES NOW IS THE SOURCE, read through `inspect.getsource`
        so the bytes examined are the ones the interpreter loaded. And the
        search is over the ARGUMENT PARSER's own operands rather than over the
        whole file: this module's prose names `--scope` and `--actor` in order
        to say it has neither, so a naive substring search over the source
        would fail on the documentation that promises the property.
        """
        import inspect

        from tools import publication_decision

        self.assertIn("THERE IS NO `--actor`, NO `--scope` AND NO "
                      "`--output-path`", publication_decision.__doc__)
        source = inspect.getsource(publication_decision)
        self.assertIn("def main", source)          # the real source, not a name
        declared = set()
        for line in source.split("\n"):
            for word in line.split('"'):
                if word.startswith("--"):
                    declared.add(word.split()[0])
        self.assertIn("--participant", declared)
        self.assertIn("--job", declared)
        for word in ("--actor", "--scope", "--output-path", "--attempt",
                     "--candidate", "--digest"):
            self.assertNotIn(word, declared)
        read = self.read("--participant", OWNER)
        self.assertEqual(read["authorization"]["effective_scope"], WORK_SCOPE)
        self.assertNotEqual(WORK_SCOPE, "scope:deployment")


class TheSelectorsNameTheExactExecutionOrNothing(PublicationCase):
    """A Job, a stage and an episode -- and the attempt is resolved FROM them."""

    def test_another_stage_of_this_job_is_another_ending(self):
        caught = self.refusal(
            self.inspected,
            stage_id=documents.stage_id(self.job_id, "review"))
        self.assertIn("follows the IMPLEMENTATION", caught.message)

    def test_an_episode_this_stage_never_opened_is_refused(self):
        caught = self.refusal(self.inspected, episode=2)
        self.assertIn("has no episode 2", caught.message)

    def test_a_job_this_store_does_not_hold_is_refused(self):
        caught = self.refusal(self.inspected, job_id="job-nowhere")
        self.assertIn("job-nowhere", caught.message)
        self.assertIn("no such Job", caught.message)

    def test_an_attempt_under_another_work_is_not_evidence_about_this_one(self):
        self.control._connection.execute(
            "UPDATE attempts SET work_id = ? WHERE runtime_attempt_id = ?",
            ("0000000a-W9", self.attempt_id))
        caught = self.refusal(self.inspected)
        self.assertEqual((caught.category, caught.code),
                         ("integrity", "schema"))
        self.assertIn("is not evidence about another", caught.message)


# -- 4. the decision's own exactness -----------------------------------------


class TheDecisionBindsExactlyWhatTheOwnerRead(PublicationCase):

    def test_an_inspection_that_changed_under_the_owner_collides(self):
        read = self.read()
        self.write_output(extra={"late.txt": b"a worker that was not done"})
        code, _answer = self.decide(read)
        self.assertEqual(code, 1)
        self.assertEqual(self.journal(publication_recovery.DECISION_KIND), [])

    def test_each_bound_operand_is_compared_on_its_own(self):
        read = self.read()
        for operand, value in (
                ("expect_output_digest", "sha256:" + "0" * 64),
                ("expect_output_bytes", read["output"]["total_bytes"] + 1),
                ("expect_candidate_head", "a" * 40),
                ("expect_candidate_base", "b" * 40),
                ("expect_attempt", "attempt-" + "f" * 64),
                ("context_digest", "sha256:" + "1" * 64),
                ("expect_selection_digest", "sha256:" + "2" * 64)):
            with self.subTest(operand=operand):
                code, _answer = self.decide(read, decision_id="D-" + operand,
                                            **{operand: value})
                self.assertEqual(code, 1)
        self.assertEqual(self.journal(publication_recovery.DECISION_KIND), [])

    def test_a_producer_status_other_than_zero_is_denied_outright(self):
        read = self.read()
        code, _answer = self.decide(read, expect_producer_status=1)
        self.assertEqual(code, 1)

    def test_an_unapproved_profile_or_declaration_digest_is_refused(self):
        read = self.read()
        for operand in ("profile_digest", "declaration_digest"):
            with self.subTest(operand=operand):
                code, _answer = self.decide(read, decision_id="D-" + operand,
                                            **{operand: "sha256:" + "3" * 64})
                self.assertEqual(code, 1)
        code, _answer = self.decide(read, decision_id="D-profile",
                                    profile="documentation/1")
        self.assertEqual(code, 1)

    def test_a_stage_set_naming_implementation_is_denied_by_name(self):
        read = self.read()
        for words in (["implementation", "review"], ["publication"],
                      ["review", "publication"], ["verification", "review"]):
            with self.subTest(stages=words):
                code, _answer = self.decide(
                    read, decision_id="D-" + "-".join(words), stages=words)
                self.assertEqual(code, 1)
        caught = self.refusal(publication_recovery.owned_stages,
                              ["implementation", "review"])
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))

    def test_a_cancelled_job_is_never_revived(self):
        read = self.read()
        cancellation.request(self.jobs, job_id=self.job_id,
                             reason="the owner stopped it")
        code, _answer = self.decide(read)
        self.assertEqual(code, 1)
        self.assertEqual(self.journal(publication_recovery.DECISION_KIND), [])
        # AND THE CANCELLATION IS VISIBLE IN THE INSPECTION ITSELF.
        held = self.read()
        self.assertFalse(held["eligible"])
        self.assertIn("never revived",
                      " ".join(one["message"] for one in held["holds"]))

    def test_one_failed_publication_has_one_approved_recovery(self):
        read = self.read()
        self.assertEqual(self.decide(read)[0], 0)
        code, _answer = self.decide(self.read(), decision_id="D2")
        self.assertEqual(code, 1)
        self.assertEqual(len(self.journal(publication_recovery.DECISION_KIND)),
                         1)
        # A HOLD OR A DENIAL IS STILL A SECOND ATTRIBUTABLE ACT.
        self.assertEqual(self.decide(self.read(), decision_id="D3",
                                     disposition="--hold")[0], 0)
        self.assertEqual(len(self.journal(publication_recovery.DECISION_KIND)),
                         2)


# -- 5. replay, restart and concurrency --------------------------------------


class EveryEffectReplaysAndNothingHappensTwice(PublicationCase):

    def test_the_same_command_twice_replays_the_decision_and_the_boundary(self):
        read = self.read()
        first_code, first = self.decide(read)
        second_code, second = self.decide(self.read())
        self.assertEqual((first_code, second_code), (0, 0))
        self.assertEqual(first["decision"], second["decision"])
        self.assertEqual(first["admission"], second["admission"])
        self.assertEqual(len(self.journal(publication_recovery.DECISION_KIND)),
                         1)
        self.assertEqual(len(self.journal(publication_recovery.HELD_KIND)), 1)

    def test_the_same_decision_key_with_changed_operands_collides(self):
        read = self.read()
        self.assertEqual(self.decide(read)[0], 0)
        code, _answer = self.decide(read, disposition="--deny")
        self.assertEqual(code, 1)
        self.assertEqual(
            publication_recovery.decision_of(self.jobs, "D1")["disposition"],
            "approved")

    def test_a_restarted_manager_reconciles_rather_than_repeating(self):
        """ANOTHER INCARNATION ON THE SAME ROWS, which is what a restart is."""
        read = self.read()
        self.decide(read)
        before = publication_recovery.held_admission_of(self.jobs, "D1")
        reopened = JobStore.open(self.jobs.database, authority_uuid=UUID,
                                 incarnation="jobs-after-restart",
                                 clock=self.clock)
        self.addCleanup(reopened.close)
        self.instants.append(LATER)
        again = self.admitted(store=reopened, now=LATER)
        self.assertEqual(again, before)
        self.assertEqual(again["recorded_at"], NOW)
        self.assertEqual(len(self.journal(publication_recovery.HELD_KIND)), 1)
        self.assertFalse(again["reserved"])

    def test_two_concurrent_commands_under_one_key_produce_one_record(self):
        """THE INSTALLED COMMAND, TWICE, AT ONCE -- each opening its own store
        handle exactly as two operators running it would."""
        import concurrent.futures

        read = self.read()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            held = [pool.submit(self.decide, read) for _ in range(2)]
            answers = [one.result() for one in held]
        self.assertEqual(sorted(one[0] for one in answers), [0, 0])
        self.assertEqual(answers[0][1]["decision"], answers[1][1]["decision"])
        self.assertEqual(answers[0][1]["admission"],
                         answers[1][1]["admission"])
        self.assertEqual(len(self.journal(publication_recovery.DECISION_KIND)),
                         1)
        self.assertEqual(len(self.journal(publication_recovery.HELD_KIND)), 1)
        self.assertEqual(self.job_rows(), [self.job_id])

    def test_two_concurrent_decisions_of_one_failure_meet_at_the_fence(self):
        """One failed publication has ONE approved recovery, and two owners
        racing meet at a fence inside the write lock rather than at a read."""
        import concurrent.futures

        read = self.read()
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            held = [pool.submit(self.decide, read, decision_id=one)
                    for one in ("C1", "C2")]
            codes = sorted(one.result()[0] for one in held)
        self.assertEqual(codes, [0, 1])
        approved = [one for one in
                    publication_recovery.decisions_of(self.jobs)
                    if one["disposition"] == "approved"]
        self.assertEqual(len(approved), 1, approved)
        self.assertEqual(len(self.journal(publication_recovery.HELD_KIND)), 1)
        self.assertEqual(self.job_rows(), [self.job_id])

    def test_a_fault_between_the_decision_and_the_boundary_resumes(self):
        """THE CUT THE CONTRACT NAMES: the decision committed and the boundary
        did not. The next request resumes from the decision rather than
        starting again or recording a second one."""
        read = self.read()
        self.approved(read)
        self.ports()["exclusion"] = FakeExclusion(
            answer={"runtime": {"attempt_id": None, "runtime_id": "r",
                                "execution_runtime": "running",
                                "cleanup": "pending", "assignment": None},
                    "token": {"returned": False}},
            identity=CURRENT["identity"])
        caught = self.refusal(self.admitted)
        self.assertIn("is held and is not admitted", caught.message)
        self.assertEqual(self.journal(publication_recovery.HELD_KIND), [])
        self.ports()["exclusion"] = FakeExclusion(identity=CURRENT["identity"])
        held = self.admitted()
        self.assertEqual(held["state"], "held")
        self.assertEqual(len(self.journal(publication_recovery.DECISION_KIND)),
                         1)
        self.assertEqual(len(self.journal(publication_recovery.HELD_KIND)), 1)

    def test_an_identity_another_pipeline_owns_is_refused(self):
        read = self.read()
        self.approved(read)
        submit(self.jobs, {
            "schema": documents.SUBMISSION_SCHEMA,
            "submission_id": "sub-intruder",
            "jobs": [{"job_id": "publication-D1",
                      "input_digest": "sha256:" + "1" * 64,
                      "policy_digest": "sha256:" + "2" * 64,
                      "test_scope": [], "terminal_policy": "report-and-hold",
                      "stages": [{"kind": "implementation",
                                  "work_id": WORK_A,
                                  "profile_name": "reference",
                                  "profile_digest": "sha256:" + "b" * 64,
                                  "depends_on": []}]}]})
        caught = self.refusal(self.admitted)
        self.assertIn("names another pipeline", caught.message)
        self.assertEqual(self.journal(publication_recovery.HELD_KIND), [])


# -- 6. the recovery-only contracts cannot be reached by ordinary work -------


class OrdinaryAdmissionCannotNameTheRecoveryContracts(PublicationCase):
    """"Existing ordinary creation/submit/fresh-attempt cannot misuse the
    recovery profile or template." Driven through the owners that decide it."""

    def test_an_ordinary_submission_naming_the_recovery_profile_is_refused(self):
        caught = self.refusal(submit, self.jobs, {
            "schema": documents.SUBMISSION_CONTROL_SCHEMA,
            "submission_id": "sub-ordinary",
            "jobs": [{"job_id": "job-ordinary",
                      "input_digest": "sha256:" + "1" * 64,
                      "policy_digest": "sha256:" + "2" * 64,
                      "test_scope": [], "terminal_policy": "report-and-hold",
                      "control": {
                          "profile": publication_recovery.PUBLICATION_PROFILE},
                      "stages": [{"kind": "implementation",
                                  "work_id": WORK_A,
                                  "profile_name": "reference",
                                  "profile_digest": "sha256:" + "b" * 64,
                                  "depends_on": []}]}]})
        self.assertIn(publication_recovery.PUBLICATION_PROFILE,
                      caught.message)
        # AND THE GUARD THAT REFUSED IT IS THE CONTROL OWNER'S, over EVERY
        # recovery profile rather than over one. Checkpoint 1 asserted that
        # this build held no such profile at all, which was true then and is
        # the wrong property now: checkpoint 2 enforces it, so what must hold
        # is that an ordinary submission still cannot name it.
        self.assertIn(publication_recovery.PUBLICATION_PROFILE,
                      job_control.PROFILES)
        self.assertIn(publication_recovery.PUBLICATION_PROFILE,
                      job_control.RECOVERY_PROFILES)
        with self.assertRaises(ContractRefusal):
            job_control.require_ordinary_profile(
                {"profile": publication_recovery.PUBLICATION_PROFILE})

    def test_an_ordinary_creation_naming_the_recovery_template_is_refused(self):
        caught = self.refusal(
            self.create_job,
            request=creation_case.request(
                task={"task_id": "w385695-misuse",
                      "statement": "an ordinary creation that names the "
                                   "recovery template"},
                template=publication_recovery.RECOVERY_TEMPLATE))
        self.assertIn(publication_recovery.RECOVERY_TEMPLATE, caught.message)

    def test_the_recovery_role_descriptor_is_not_a_bound_template_contract(self):
        self.assertIsNone(role_contract.contract_for(
            publication_recovery.RECOVERY_TEMPLATE))
        self.assertNotIn(publication_recovery.RECOVERY_ROLE,
                         [role_contract.CONTRACT_SCHEMA,
                          role_contract.HANDOFF_CONTRACT_SCHEMA,
                          role_contract.PROPOSAL100M_CONTRACT_SCHEMA])

    def test_a_publication_stage_cannot_be_submitted_into_this_vocabulary(self):
        caught = self.refusal(submit, self.jobs, {
            "schema": documents.SUBMISSION_SCHEMA,
            "submission_id": "sub-publication-ordinary",
            "jobs": [{"job_id": "job-publication",
                      "input_digest": "sha256:" + "1" * 64,
                      "policy_digest": "sha256:" + "2" * 64,
                      "test_scope": [], "terminal_policy": "report-and-hold",
                      "stages": [{"kind": "publication", "work_id": WORK_A,
                                  "profile_name": "reference",
                                  "profile_digest": "sha256:" + "b" * 64,
                                  "depends_on": []}]}]})
        # THE REFUSAL IS THE GENERATION'S, not "unknown kind". Checkpoint 2
        # added `publication` to the one closed vocabulary and admitted it
        # ONLY through the `/4` recovery generation, so an ordinary `/2`
        # submission naming it is refused as the wrong GENERATION -- which is
        # a stronger statement than "this build has never heard of it".
        self.assertIn(documents.SUBMISSION_RECOVERY_SCHEMA, caught.message)
        self.assertIn("admitted only by", caught.message)
        self.assertIn("publication", documents.STAGE_KINDS)
        self.assertNotIn("publication", documents.ORDINARY_STAGE_KINDS)


# -- 7. what this checkpoint is, said out loud -------------------------------


class TheBuildHoldsTheOwnerSelectionsItClaimsTo(unittest.TestCase):
    """The selected identities and bounds, held against the owner's own words.

    READ FROM THE PRODUCT, so a drifted constant is a failing case rather than
    a recovery admitted under a policy nobody selected.
    """

    def test_the_selected_identities_are_the_consolidated_rulings(self):
        self.assertEqual(publication_recovery.RECOVERY_SELECTION,
                         "baton.v12.output-publication-recovery/1")
        self.assertEqual(publication_recovery.RECOVERY_DECISION,
                         "baton.v12.output-publication-decision/1")
        self.assertEqual(publication_recovery.RECOVERY_TEMPLATE,
                         "baton.v12.job-template.output-publication-review/1")
        self.assertEqual(
            publication_recovery.RECOVERY_ROLE,
            "baton.v12.development-role-contract.output-publication-review/1")
        self.assertEqual(publication_recovery.RECOVERY_SUBMISSION,
                         "baton.v12.job-submission/4")
        self.assertEqual(publication_recovery.RECOVERY_POOL,
                         "baton.v12.worker-pool/2")
        self.assertEqual(publication_recovery.RECOVERY_STORE_GENERATION, 10)

    def test_the_profile_digest_covers_the_definition_this_build_holds(self):
        definition = json.loads(
            publication_recovery.PUBLICATION_DEFINITION_BYTES.decode("utf-8"))
        self.assertEqual(definition,
                         publication_recovery.PUBLICATION_DEFINITION)
        self.assertEqual(
            publication_recovery.resolved_profile()["digest"],
            publication_recovery.PUBLICATION_PROFILE_DIGEST)
        self.assertEqual(definition["publication_stage"]["seconds"], 900)
        self.assertFalse(definition["publication_stage"]["restart_resets"])
        self.assertEqual(definition["overall_job"]["seconds"], 9960)
        self.assertEqual(definition["each_stage"]["seconds"], 4800)
        self.assertEqual(
            definition["review_provider_invocation"]["seconds"], 3600)
        self.assertEqual(definition["verification_command"]["seconds"], 900)

    def test_a_profile_this_build_does_not_hold_is_a_stale_selection(self):
        with self.assertRaises(ContractRefusal) as caught:
            publication_recovery.resolved_profile("output-publication-review/2")
        self.assertIn("a finite control it cannot enforce",
                      caught.exception.message)

    def test_the_corrective_declaration_is_w385694s_exact_revision(self):
        held = publication_recovery.corrective_declaration()
        self.assertEqual(held["digest"], role_contract.contract_digest(
            role_contract.contract_for(role_contract.PROPOSAL100M_TEMPLATE)))
        self.assertEqual(held["output"]["constraints"]["max_bytes"],
                         104857600)
        self.assertEqual(held["output"]["constraints"]["max_entries"], 100)
        self.assertEqual(held["output"]["constraints"]["link_policy"],
                         "forbid")

    def test_this_checkpoint_declares_every_prerequisite_it_is_missing(self):
        """A CHECKPOINT IS PARTIAL EVIDENCE AND NEVER "RESUME SUPPORTED"."""
        readiness = publication_recovery.admission_readiness(
            {"stages": list(publication_recovery.SELECTED_STAGES)})
        self.assertEqual(readiness["admission"], "held")
        self.assertEqual(readiness["publication"], "unavailable")
        self.assertEqual(readiness["review"], "blocked")
        self.assertEqual(readiness["offers"], 0)
        self.assertIn("prerequisites", readiness["owed_by"])
        self.assertIn("reserved no Job identity", readiness["detail"])
        # AND THE OTHER SHAPE SAYS THE OTHER TRUTH, which is the half this
        # case exists to keep honest: an ADMITTED recovery has published
        # nothing either, and its own readiness says so rather than letting a
        # Job id read as progress.
        admitted = publication_recovery.admission_readiness(
            {"state": "admitted"})
        self.assertEqual(admitted["admission"], "admitted")
        self.assertEqual(admitted["publication"], "queued")
        self.assertEqual(admitted["review"], "blocked")
        self.assertEqual(admitted["offers"], 0)
        self.assertIn("NOTHING HAS BEEN PUBLISHED", admitted["detail"])
