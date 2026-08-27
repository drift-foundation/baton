"""W6636 — the local OCI lifecycle, composed from the reviewed W5 components.

THIS JOB OWNS INTEGRATION, NOT IMPLEMENTATION. Nothing here re-implements a
component or re-tests one: every step calls the public operation that
component's own Work delivered, in the order the topology fixes, against a real
engine. What it establishes is the thing no component suite can -- that the
sequence holds when the pieces are put together, and that the manager's
operations and the adapter's engine calls are the SAME acts rather than two
adjacent ones.

WHAT IS COMPOSED, and each name is a closed Work:

    W6592/W6627  the store, the offer, the claim, the activation
    W6631        the assignment's two private roots
    W19784       the composed `/input` root and its authorization
    W6632        the constrained adapter: start, list, stop, destroy, observe
    W6633        the reference worker image the execution container runs

WHERE THE CERTIFIED SURFACE ENDS, and it is a finding rather than an omission.
`request_freeze` calls `adapter.seal` and `request_intake` calls
`adapter.collect`; both land in `sealing.py`, and credential delivery lands in
`credentials.py`. Both files are W6634's, and **W6634 closed
NON-SATISFYING** -- "its code remains provisional and cannot be treated as
certified."

That is not a corner of the lifecycle. `authorize_cleanup` refuses to destroy
anything without an intake receipt, `request_intake` refuses anything whose
output is not `frozen`, and only `request_freeze` freezes -- so **destroy and
positive absence for a runtime that ever started are reachable only through the
provisional path**. W6636's acceptance requires every component dependency
closed satisfying before terminal integration signoff, and one is not, so this
module composes the certified arc and stops where certification stops. The
consent posture is destroyed here because a consent runtime is torn down
directly by the adapter and never passes through intake.

The adapter is constructed with `outputs=()` and `credential_delivery=None`
throughout, which its own docstring names as the runtime half's supported
construction; under those operands `start`, `list`, `stop`, `destroy` and
`observe` do not enter either provisional module.

IT FAILS RATHER THAN SKIPS WHEN DOCKER IS ABSENT, for the reason W6633's gate
gives: a required integration that quietly passes because it could not run is
the failure mode this campaign is built against. Podman is additive and skips,
for the reason W6632's engine suite gives -- a second third-party daemon is not
a prerequisite for this repository's own integration.
"""

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time
import unittest
import uuid

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      accept_offer, activate_assignment,
                                      authorize_cleanup, certify_profile,
                                      issue_offer, observe, reconcile_runtime,
                                      record_attempt, request_cancellation,
                                      request_runtime_start, submit_claim)
from baton_v12.worker_manager.attempts import TRANSITIONS
from baton_v12.worker_manager import attempts
from baton_v12.worker_manager import documents as manager_documents
from baton_v12.worker_manager.oci import (LABEL_PREFIX, EnginePort,
                                          OciAdapter)
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 compose_input_root)

from . import input_roots
from .test_offers import NOW, PROFILE, FakeSession, fake_claim_signature

MARK = "baton-w6636-lifecycle"
WORK_ID = "43c55d4b-W6636"
UUID = "43c55d4b" + "0" * 24
WHO = "baton.claude"
WORK_REF = {"authority_uuid": UUID, "work_id": WORK_ID}
POLICY = "sha256:" + "d" * 64
ADAPTER = "sha256:" + "c" * 64
WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"


def reachable(engine):
    """`(usable, why)` for one engine, deciding ONLY availability."""
    if shutil.which(engine) is None:
        return False, f"{engine} is not on PATH"
    found = subprocess.run(
        [engine, "version", "--format", "{{.Server.Version}}"],
        capture_output=True, timeout=60)
    if found.returncode != 0:
        return False, (f"{engine} is installed and its daemon is not "
                       f"reachable: "
                       f"{found.stderr.decode('utf-8', 'replace')[:200]}")
    return True, found.stdout.decode("utf-8").strip()


class Lifecycle:
    """One engine, one built worker image, one store per case.

    A MIXIN, for the reason W6632's engine suite gives: unittest would
    otherwise collect an abstract class with no engine and report errors that
    say nothing about any daemon.
    """

    engine = None
    required = False
    image = None

    @classmethod
    def setUpClass(cls):
        usable, why = reachable(cls.engine)
        if not usable:
            if cls.required:
                raise AssertionError(
                    f"W6636 composes a REAL local OCI lifecycle and {why}. "
                    f"That is a failed prerequisite for a required gate, not "
                    f"a reason to pass without running it.")
            raise unittest.SkipTest(why)
        cls.server = why
        cls.image = f"{MARK}:{uuid.uuid4().hex[:12]}"
        cls.addClassCleanup(
            lambda: subprocess.run(
                [cls.engine, "image", "rm", "--force", cls.image],
                capture_output=True, timeout=180))
        # THE ARTEFACT UNDER COMPOSITION IS W6633's, built from its own recipe
        # rather than pulled: an integration that ran the wrong image would
        # prove the sequence over something no Work delivered.
        built = subprocess.run(
            [cls.engine, "build", "-f", str(WORKER / "Dockerfile"), "-t",
             cls.image, str(WORKER)], capture_output=True, timeout=1800)
        assert built.returncode == 0, (
            f"the reference worker image did not build under {cls.engine}: "
            f"{built.stderr.decode('utf-8', 'replace')[-1200:]}")
        found = subprocess.run(
            [cls.engine, "image", "inspect", cls.image, "--format", "{{.Id}}"],
            capture_output=True, timeout=120)
        assert found.returncode == 0, found.stderr.decode("utf-8", "replace")
        cls.image_digest = found.stdout.decode("utf-8").strip()

    def setUp(self):
        self.made = []
        self.addCleanup(self.remove_everything)
        self.home = tempfile.mkdtemp(prefix="v12-w6636-")
        self.addCleanup(forcibly_remove, self.home)
        self.storage = os.path.join(self.home, "storage")
        os.makedirs(self.storage)
        self.attempt = f"attempt-{uuid.uuid4().hex[:10]}"
        self.store = self.open_store()
        self.session = FakeSession(participant=WHO, work={
            "status": "open", "phase": "queued", "handler": None,
            "gate": None, "authority_uuid": UUID})
        live = {"work_ref": dict(WORK_REF), "participant": WHO,
                "generation": 1}
        self.session.claim_answer = dict(live)
        self.session.live_assignment = dict(live)
        self.session.fence_answer = {"cause": "cancelled",
                                     "assignment": dict(live),
                                     "phase": "block",
                                     "gate": "runtime-quiescence:1",
                                     "fenced": True}
        self.live = live
        self.port = AuthorityPort(self.session, fake_claim_signature)
        self.engine_calls = []
        # ONE TRACE, WRITTEN BY BOTH BOUNDARIES. The authority and the engine
        # are different objects, and two separate call lists cannot be compared
        # for order -- which is the one thing the cancellation case exists to
        # establish.
        self.trace = []
        authority_cancel = self.session.cancel

        def traced(operands):
            self.trace.append(("authority.cancel", dict(operands)))
            return authority_cancel(operands)

        self.session.cancel = traced

    def open_store(self, incarnation="manager-w6636"):
        """A store over THIS case's database file, under a named incarnation.

        Taken as an operand rather than fixed, because a second incarnation
        over the SAME file is exactly what the restart case needs and a
        second file would be a different manager's memory.
        """
        store = ControlStore.open(os.path.join(self.home, "control.sqlite3"),
                                  incarnation=incarnation, clock=lambda: NOW)
        self.addCleanup(store.close)
        certify_profile(store, "runtime", "reference", PROFILE)
        return store

    # -- the one thing this suite does to the world --------------------------

    def spawn(self, argv):
        """The engine port's run operation, over a real process.

        Every `--name` the adapter composes is registered for removal BEFORE
        the process runs, so a start that creates a container and then fails
        on its way back still has it removed.
        """
        for index, value in enumerate(argv):
            if value == "--name" and index + 1 < len(argv):
                self.made.append(argv[index + 1])
        self.engine_calls.append(list(argv))
        self.trace.append(("engine", list(argv)))
        finished = subprocess.run(argv, capture_output=True, timeout=600)
        return {"status": finished.returncode,
                "stdout": finished.stdout.decode("utf-8", "replace"),
                "stderr": finished.stderr.decode("utf-8", "replace")}

    def remove_everything(self):
        """Remove what this case made, and SURFACE a removal that did not."""
        survived = []
        for name in self.made:
            removed = subprocess.run([self.engine, "rm", "--force", name],
                                     capture_output=True, timeout=120)
            if removed.returncode == 0:
                continue
            found = subprocess.run(
                [self.engine, "ps", "--all", "--filter", f"name={name}",
                 "--format", "{{.Names}}"], capture_output=True, timeout=120)
            if found.returncode != 0 or found.stdout.decode(
                    "utf-8", "replace").strip():
                survived.append(
                    (name, removed.stderr.decode("utf-8", "replace")[:200]))
        assert not survived, f"{self.engine} did not remove {survived}"

    # -- the composed halves -------------------------------------------------

    def roots(self):
        return assignment_workspace(self.storage, self.attempt)

    def adapter(self, posture="execution", roots=None, mounts=(),
                image=None):
        """The reviewed adapter, under THIS assignment's resolved identity.

        `outputs` and `credential_delivery` are deliberately absent: both reach
        W6634's provisional code, and this composition does not stand on it.

        BOTH ROOTS ARE ALWAYS DECLARED, in both postures. `MOUNTABLE` -- not
        the constructor -- is what gives a consent container nothing to mount,
        and a consent adapter built without the roots would refuse before that
        rule was ever reached.
        """
        return OciAdapter(
            self.engine, EnginePort(self.spawn),
            identity={"image_digest": image or self.image_digest,
                      "profile_digest": PROFILE, "policy_digest": POLICY,
                      "adapter_digest": ADAPTER},
            assignment_roots=dict(roots if roots is not None
                                  else self.roots()),
            posture=posture, mounts=mounts)

    def plan(self, roots):
        """The execution mount plan a real delivery carries.

        THE MANAGER DOES NOT COMPOSE THIS, and that is worth saying: `mounts`
        is assignment-scoped adapter construction, so the party that builds the
        adapter decides what a worker sees, and `request_runtime_start` holds
        that decision to the root it proved. Composing it here is composing the
        caller's half.
        """
        return [{"source": roots["inputs"], "target": "/input",
                 "writable": False},
                {"source": roots["workspace"], "target": "/workspace",
                 "writable": True}]

    def claimed(self, store=None, given=None):
        """Offer, accept, record, claim -- the authority half, in order."""
        store = store if store is not None else self.store
        given, assignment = input_roots.documents(
            work_ref=dict(WORK_REF), participant=WHO, generation=1,
            runtime_attempt_id=self.attempt, given=given,
            policy_digest=POLICY, profile_digest=PROFILE)
        offer = f"offer-{self.attempt}"
        issue_offer(store, self.port, offer_id=offer, work_id=WORK_ID,
                    runtime_attempt_id=self.attempt,
                    input_digest=given["manifest_digest"],
                    policy_digest=POLICY, profile_digest=PROFILE,
                    profile_name="reference", mint_bearer=lambda: "bearer-1")
        accept_offer(store, self.port, offer_id=offer, decision="accept",
                     bearer="bearer-1", now=NOW,
                     runtime_attempt_id=self.attempt,
                     work_ref=dict(WORK_REF))
        record_attempt(store, attempt_id=self.attempt, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       input_digest=given["manifest_digest"],
                       policy_digest=POLICY)
        submit_claim(store, self.port, offer_id=offer)
        return given, assignment

    def activated(self, store=None, given=None):
        """...and then activation, which unlocks the first writable call."""
        store = store if store is not None else self.store
        given, assignment = self.claimed(store=store, given=given)
        activate_assignment(store, self.port, attempt_id=self.attempt,
                            expect=dict(self.live))
        return given, assignment

    def composed(self, roots, given, assignment):
        compose_input_root(roots["inputs"], given, assignment,
                           assignment=dict(assignment["assignment_ref"]),
                           runtime_attempt_id=self.attempt)
        return roots["inputs"]

    def prepared(self, store=None):
        """Everything the first writable adapter call needs, and nothing more.

        Answers `(adapter, roots, inputs)`. This is the composition's own
        setup: authority half, workspace half, input root, in that order,
        because each one's precondition is the one before it.
        """
        given, assignment = self.activated(store=store)
        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        return (self.adapter(roots=roots, mounts=self.plan(roots)),
                roots, inputs)

    # -- what the engine says ------------------------------------------------

    def labels(self):
        """The reconciliation labels this attempt derives.

        WRITTEN OUT RATHER THAN DERIVED, on purpose: a case that asked the
        manager what labels it uses and then checked the engine for those would
        agree with the manager whatever either of them did. This is the test's
        own statement of the set, and
        `test_the_manager_derives_exactly_these_labels` holds the manager to
        it.

        ONE COPY, though. Five cases had five copies, which is five chances for
        a case to agree with itself.
        """
        return {"runtime_attempt_id": self.attempt, "authority_uuid": UUID,
                "work_id": WORK_ID, "participant": WHO, "generation": 1,
                "profile_digest": PROFILE, "policy_digest": POLICY,
                "adapter_digest": ADAPTER}

    def operations(self, kind, store=None):
        """The journalled operations of one kind, for this attempt.

        The journal is what a restart replays, so "was anything committed" is a
        question about this table and not about a state column.
        """
        store = store if store is not None else self.store
        return [dict(one) for one in store._connection.execute(
            "SELECT * FROM operations WHERE kind = ?", (kind,)).fetchall()]

    def attempt_row(self, store=None):
        store = store if store is not None else self.store
        row = store._connection.execute(
            "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
            (self.attempt,)).fetchone()
        return dict(row) if row is not None else None

    def settled(self, runtime_id, seconds=30):
        """Wait, BOUNDED, until the engine stops calling this one running.

        A fixed sleep would decide the outcome on a slow host. The bound is
        what keeps a hang a failure rather than a wait.
        """
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if self.inspected(runtime_id)["State"]["Status"] != "running":
                return
            time.sleep(0.1)
        raise AssertionError(
            f"{runtime_id} was still running after {seconds}s")

    def inspected(self, runtime_id):
        found = subprocess.run(
            [self.engine, "container", "inspect", runtime_id],
            capture_output=True, timeout=120)
        assert found.returncode == 0, found.stderr.decode("utf-8", "replace")
        return json.loads(found.stdout.decode("utf-8"))[0]

    def carrying(self, labels):
        """Every container the engine holds for this exact label set."""
        argv = [self.engine, "ps", "--all"]
        for name, value in sorted(labels.items()):
            argv += ["--filter", f"label={LABEL_PREFIX}{name}={value}"]
        argv += ["--format", "{{.ID}}"]
        found = subprocess.run(argv, capture_output=True, timeout=120)
        assert found.returncode == 0, found.stderr.decode("utf-8", "replace")
        return [one for one in found.stdout.decode("utf-8").split() if one]


def forcibly_remove(place):
    # The composed input root is delivered READ-ONLY on purpose, so the case
    # has to be able to take it away again.
    for current, _directories, files in os.walk(place):
        os.chmod(current, 0o700)
        for name in files:
            try:
                os.chmod(os.path.join(current, name), 0o600)
            except OSError:
                pass
    shutil.rmtree(place, ignore_errors=True)


class Composition(Lifecycle):
    """The ordered lifecycle, over one real engine."""

    # -- PLAN 2: consent teardown, activation, fresh execution ---------------

    def test_the_consent_runtime_is_torn_down_before_execution_exists(self):
        """A consent container mounts nothing, and its destruction is proved.

        THE CONSENT HALF IS ADAPTER-DIRECT AND THAT IS A FINDING. The store
        carries a `consent_runtime` axis and the adapter carries a `consent`
        posture, and NO manager operation joins them: `request_runtime_start`
        writes `execution_runtime` and nothing writes the other. So an
        integration must drive the adapter itself and record the axis
        alongside -- which is what this does, and what a later slice should
        replace with one operation.
        """
        self.claimed()
        roots = self.roots()
        labels = self.labels()
        # THE RULE IS `MOUNTABLE`, AND IT IS ASKED. Constructing a consent
        # adapter with an empty plan would make "a consent container mounts
        # nothing" true by construction and prove nothing at all -- so a plan
        # is offered to a consent adapter first, and refused.
        #
        # THE WORKSPACE ALONE, deliberately. The full execution plan refuses
        # one step earlier, on the unauthorized `/input` bind, and that is a
        # different rule: a case that accepted THAT refusal would report
        # `MOUNTABLE` established while never reaching it. This plan carries no
        # `/input` target, so the earlier guard passes and the posture rule is
        # the one that answers.
        with self.assertRaises(ContractRefusal) as denied:
            self.adapter(posture="consent", roots=roots,
                         mounts=[{"source": roots["workspace"],
                                  "target": "/workspace",
                                  "writable": True}]).start(
                {"labels": labels,
                 "operation_id": f"runtime.start:{uuid.uuid4().hex[:12]}"})
        self.assertIn("mounts nothing", str(denied.exception))
        self.assertEqual(self.engine_calls[-1][1], "ps",
                         "a refused consent plan reached the engine's run")
        adapter = self.adapter(posture="consent", roots=roots)
        operation = f"runtime.start:{uuid.uuid4().hex[:12]}"
        started = adapter.start({"labels": labels, "operation_id": operation})
        observe(self.store, attempt_id=self.attempt, axis="consent_runtime",
                value="running")

        # IT SEES NEITHER ROOT. `MOUNTABLE` gives consent no mountable root,
        # and the engine is the one asked.
        binds = self.inspected(started["runtime_id"])["HostConfig"]["Binds"]
        self.assertEqual(binds or [], [],
                         "a consent container mounted assignment material")

        gone = adapter.destroy(manager_documents.destroy_command(
            assignment_ref=dict(self.live), runtime_attempt_id=self.attempt,
            runtime_id=started["runtime_id"],
            intake_receipt_digest="sha256:" + "0" * 64,
            retention_policy_digest="sha256:" + "0" * 64))
        self.assertEqual(gone["state"], "absent", gone["why"])
        # NO CREDENTIAL WAS DELIVERED, and the adapter says exactly that
        # rather than borrowing the runtime's word for it.
        self.assertEqual(gone["credentials"]["lifecycle_state"],
                         "not-delivered")
        observe(self.store, attempt_id=self.attempt, axis="consent_runtime",
                value="destroyed")
        self.assertEqual(self.attempt_row()["consent_runtime"], "destroyed")
        # AND THE ENGINE AGREES, asked about the identity rather than told.
        self.assertEqual(self.carrying(labels), [])

    def test_a_claimed_but_unactivated_attempt_starts_no_container(self):
        """Activation gates the first writable adapter call, and the refusal
        is BEFORE the engine, not inside it.

        Composed rather than assumed: W6592 fixes the assignment manifest at
        activation and W6632 mounts the writable workspace, so a start that
        reached the daemon first would have created a container for an
        assignment no generation was fixed for.
        """
        given, assignment = self.claimed()
        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        adapter = Watched(self.adapter(roots=roots, mounts=self.plan(roots)))
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
        self.assertEqual(refused.exception.category, "refused")
        self.assertEqual(refused.exception.code, "precondition")
        self.assertIn("not activated", str(refused.exception))
        self.assertEqual(self.engine_calls, [],
                         "the engine was reached before activation")
        self.assertEqual(self.attempt_row()["execution_runtime"],
                         "not-started")
        self.assertEqual(self.operations("runtime.start"), [])
        # AND NOTHING WAS ASKED OF THE ADAPTER AT ALL -- which is the only
        # thing that tells this guard from the second one.
        #
        # MEASURED, AND THE MEASUREMENT CHANGED THE CASE.
        # `authorize_input_root` refuses an unactivated attempt with the SAME
        # category, the SAME code and the SAME opening words, so every
        # assertion above passes with the precondition in
        # `request_runtime_start` removed: the wording proved nothing about
        # which boundary answered. `issue_offer` requires an input digest, so
        # every claimable attempt records one and the second guard always runs
        # -- there is no delivery where the first is the decisive refusal.
        #
        # What the first one alone buys is that the adapter's PLAN is never
        # read: remove it and `_plan_agrees` reaches for `mounts` on the way to
        # the second refusal. So the observation is the access itself.
        #
        # `start` is not the marker: `request_runtime_start` types the
        # capability before any precondition, so it is reached on every path
        # including this one, and asserting on the whole list would fail for a
        # reason that has nothing to do with activation.
        self.assertNotIn("mounts", adapter.consulted)
        self.assertIn("start", adapter.consulted)

    def test_the_ordered_arc_starts_one_runtime_over_the_proved_root(self):
        """Offer, accept, claim, activate, compose, start, reconcile.

        THE WHOLE POINT IS THAT IT IS ONE ACT. The manager journals a
        `runtime.start` operation, the adapter names the container from that
        same operation identity, and the reconciliation finds it by the labels
        the attempt row derives -- so the engine's container and the store's
        row are the same event rather than two that happen to agree.
        """
        adapter, roots, inputs = self.prepared()
        answer = request_runtime_start(self.store, adapter,
                                       attempt_id=self.attempt, inputs=inputs)
        row = self.attempt_row()
        self.assertEqual(row["execution_runtime"], "running", answer)
        self.assertIsNotNone(row["runtime_id"])

        held = self.inspected(row["runtime_id"])
        # ONE `/input`, READ-ONLY, AND IT IS THE PROVED SOURCE.
        binds = {one["Destination"]: one for one in held["Mounts"]}
        self.assertIn("/input", binds)
        self.assertFalse(binds["/input"]["RW"], "the input root is writable")
        self.assertEqual(os.path.realpath(binds["/input"]["Source"]),
                         os.path.realpath(inputs))
        # AND THE WORKSPACE IS THE ONLY WRITABLE TREE.
        self.assertIn("/workspace", binds)
        self.assertTrue(binds["/workspace"]["RW"])
        self.assertEqual(os.path.realpath(binds["/workspace"]["Source"]),
                         os.path.realpath(roots["workspace"]))

        # AND THE ROOT IT NAMES CARRIES EXACTLY THE TWO DOCUMENTS.
        #
        # Read from the source the ENGINE named, rather than from the path this
        # case composed: those are the same directory only if the bind is the
        # one the manager proved, which is what the comparison above is for and
        # what this would otherwise quietly assume.
        self.assertEqual(sorted(os.listdir(binds["/input"]["Source"])),
                         ["assignment.json", "input.json"])

    def test_reconciling_again_attaches_the_same_runtime(self):
        """A second reconciliation is not a second runtime.

        `reconcile_runtime` is what a restart calls, so calling it twice in one
        process must be the same act as calling it once -- and the engine, not
        the store, is what settles whether a second container exists.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        first = self.attempt_row()["runtime_id"]
        again = reconcile_runtime(self.store, adapter, attempt_id=self.attempt)
        self.assertEqual(self.attempt_row()["runtime_id"], first, again)
        labels = self.labels()
        self.assertEqual(len(self.carrying(labels)), 1)

    def test_a_second_start_is_refused_and_creates_no_second_container(self):
        """Effectively-once, measured at the engine.

        A store column saying `running` would refuse the second call whether or
        not the daemon had been reached; the container count is what makes the
        refusal a fact about the world.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        before = len(self.engine_calls)
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
        self.assertEqual(refused.exception.code, "already-terminal")
        self.assertEqual(len(self.engine_calls), before,
                         "the second start reached the engine")

    def test_a_root_composed_for_another_attempt_starts_nothing(self):
        """W19784's authorization holds at the composed boundary too.

        The root is real, correctly composed and internally consistent -- it
        is simply not THIS attempt's. The refusal must arrive before the
        journal and before the daemon, or the manager would be left settling a
        start operation it should never have written.
        """
        adapter, _roots, _inputs = self.prepared()
        other = f"{self.attempt}-other"
        given, assignment = input_roots.documents(
            work_ref=dict(WORK_REF), participant=WHO, generation=1,
            runtime_attempt_id=other, policy_digest=POLICY,
            profile_digest=PROFILE)
        stranger = assignment_workspace(self.storage, other)["inputs"]
        compose_input_root(stranger, given, assignment,
                           assignment=dict(assignment["assignment_ref"]),
                           runtime_attempt_id=other)
        with self.assertRaises(ContractRefusal):
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=stranger)
        self.assertEqual(self.engine_calls, [])
        self.assertEqual(self.attempt_row()["execution_runtime"],
                         "not-started")

    def test_a_plan_that_omits_the_input_root_is_refused_before_the_journal(
            self):
        """[MEASURED] `_plan_agrees` alone, with the authorization agreeing.

        The manager checks the adapter's declared plan BEFORE it journals, and
        the adapter checks it again at the seam. Both refuse the obvious case
        -- a stranger's root -- so a case built that way establishes NEITHER:
        remove either guard and the other still refuses.

        So the root here is this attempt's own, correctly composed and
        correctly authorized; only the PLAN is wrong, naming the workspace at
        `/input`. `authorize_input_root` has nothing to object to. What the
        earlier check buys is precisely that no operation is journalled, which
        is the thing this asserts.
        """
        given, assignment = self.activated()
        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        adapter = self.adapter(roots=roots, mounts=[
            {"source": roots["workspace"], "target": "/input",
             "writable": False},
            {"source": roots["workspace"], "target": "/workspace",
             "writable": True}])
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
        self.assertEqual(refused.exception.category, "policy")
        self.assertEqual(self.engine_calls, [])
        # NOTHING WAS JOURNALLED, which is the whole difference between the
        # early check and the adapter's own. A start operation committed for a
        # plan that could never be mounted is one this manager must settle.
        self.assertEqual(self.operations("runtime.start"), [])
        self.assertEqual(self.attempt_row()["execution_runtime"],
                         "not-started")

    def test_an_agreeing_plan_over_an_unauthorized_root_starts_nothing(self):
        """[MEASURED] `authorize_input_root` alone, with the plan agreeing.

        The mirror of the case above, and the reason it is needed is the same:
        an adapter whose plan names the stranger root AGREES with an `inputs`
        operand naming it, so `_plan_agrees` is satisfied and the only thing
        left between a worker and somebody else's assignment material is the
        authorization.
        """
        self.activated()
        other = f"{self.attempt}-stranger"
        given, assignment = input_roots.documents(
            work_ref=dict(WORK_REF), participant=WHO, generation=1,
            runtime_attempt_id=other, policy_digest=POLICY,
            profile_digest=PROFILE)
        strange_roots = assignment_workspace(self.storage, other)
        compose_input_root(strange_roots["inputs"], given, assignment,
                           assignment=dict(assignment["assignment_ref"]),
                           runtime_attempt_id=other)
        adapter = self.adapter(roots=strange_roots,
                               mounts=self.plan(strange_roots))
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt,
                                  inputs=strange_roots["inputs"])
        # `runtime-observation`/`identity-mismatch`: the root's own assignment
        # documents name another attempt, and that is what the authorization
        # compares. The exact pair is asserted so a later refusal for another
        # reason cannot stand in for this one.
        self.assertEqual(refused.exception.category, "runtime-observation")
        self.assertEqual(self.engine_calls, [])
        self.assertEqual(self.attempt_row()["execution_runtime"],
                         "not-started")

    def test_the_adapter_refuses_a_mismatched_root_at_its_own_seam(self):
        """[MEASURED] the adapter's own guard, reached directly.

        `_mounts_the_authorized_root` is the boundary that must hold when the
        manager's earlier check is bypassed -- an adapter reached by any other
        path, or a future caller. Through `request_runtime_start` the earlier
        check always answers first, so this asks the adapter itself, which is
        the only way to observe the guard that is actually load-bearing.

        NO CONTAINER IS CREATED, and the engine is asked rather than trusted:
        the refusal must precede the `run`, or a runtime exists over material
        nothing proved.
        """
        given, assignment = self.activated()
        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        with self.assertRaises(ContractRefusal) as denied:
            adapter.start({"labels": self.labels(),
                           "operation_id": f"runtime.start:{uuid.uuid4().hex}",
                           "input_root": roots["workspace"]})
        self.assertEqual(denied.exception.category, "policy")
        self.assertEqual([argv for argv in self.engine_calls
                          if "run" in argv], [])
        self.assertEqual(self.carrying(self.labels()), [])

    def test_a_credential_never_delivered_is_not_reported_torn_down(self):
        """[MEASURED] `not-delivered` is a different word from `absent`.

        The runtime's own state beside it is `absent`, and one word meaning two
        things in one document is how a reader concludes a credential was torn
        down because a container was. Nothing else in this module can tell the
        two apart, so the distinction is asserted where it is made.
        """
        self.claimed()
        adapter = self.adapter(posture="consent", roots=self.roots())
        started = adapter.start({
            "labels": self.labels(),
            "operation_id": f"runtime.start:{uuid.uuid4().hex[:12]}"})
        gone = adapter.destroy(manager_documents.destroy_command(
            assignment_ref=dict(self.live), runtime_attempt_id=self.attempt,
            runtime_id=started["runtime_id"],
            intake_receipt_digest="sha256:" + "0" * 64,
            retention_policy_digest="sha256:" + "0" * 64))
        self.assertEqual(gone["state"], "absent")
        self.assertEqual(gone["credentials"], {"lifecycle_state":
                                               "not-delivered"})

    def test_the_manager_derives_exactly_these_labels(self):
        """The label set this module states IS the one the manager derives.

        Every count this module takes from the engine filters on these eight
        pairs, so a set that drifted from the manager's would make each of
        those counts zero -- and `assertEqual(count, 0)` is exactly what
        several of the cleanliness assertions want to see. The comparison is
        made once, here, against the manager's own derivation.
        """
        self.activated()
        row = self.attempt_row()
        self.assertEqual(attempts._runtime_labels(row), self.labels())

    def test_a_declined_offer_reaches_neither_workspace_nor_engine(self):
        """DECLINE is a lifecycle ending, and it ends before anything exists.

        The acceptance names decline beside consent and activation. Nothing
        should be composable after it: no attempt to activate, no root to
        compose, no container to start.
        """
        given, _assignment = input_roots.documents(
            work_ref=dict(WORK_REF), participant=WHO, generation=1,
            runtime_attempt_id=self.attempt, policy_digest=POLICY,
            profile_digest=PROFILE)
        offer = f"offer-{self.attempt}"
        issue_offer(self.store, self.port, offer_id=offer, work_id=WORK_ID,
                    runtime_attempt_id=self.attempt,
                    input_digest=given["manifest_digest"],
                    policy_digest=POLICY, profile_digest=PROFILE,
                    profile_name="reference", mint_bearer=lambda: "bearer-1")
        accept_offer(self.store, self.port, offer_id=offer,
                     decision="decline", bearer="bearer-1", now=NOW,
                     runtime_attempt_id=self.attempt,
                     work_ref=dict(WORK_REF))
        with self.assertRaises(ContractRefusal):
            submit_claim(self.store, self.port, offer_id=offer)
        self.assertIsNone(self.attempt_row())
        self.assertEqual(self.engine_calls, [])

    def test_a_root_from_a_superseded_generation_starts_nothing(self):
        """STALE GENERATION, composed rather than described.

        The root is this attempt's, correctly composed, and names generation 1
        -- and the attempt activated generation 2. Nothing about the directory
        is malformed; what is wrong is that the assignment moved underneath it,
        which is the case a digest comparison alone would miss.
        """
        superseded = {"work_ref": dict(WORK_REF), "participant": WHO,
                      "generation": 1}
        given, assignment = input_roots.documents(
            work_ref=dict(WORK_REF), participant=WHO, generation=1,
            runtime_attempt_id=self.attempt, policy_digest=POLICY,
            profile_digest=PROFILE)
        # The authority moves on: this attempt is claimed and activated at
        # generation 2, while the root on disk names generation 1.
        live = dict(superseded, generation=2)
        self.session.claim_answer = dict(live)
        self.session.live_assignment = dict(live)
        self.live = live
        self.activated(given=given)
        roots = self.roots()
        compose_input_root(roots["inputs"], given, assignment,
                           assignment=dict(superseded),
                           runtime_attempt_id=self.attempt)
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt,
                                  inputs=roots["inputs"])
        self.assertEqual(refused.exception.category, "stale-assignment")
        self.assertEqual(refused.exception.code, "generation")
        self.assertEqual(self.engine_calls, [])
        self.assertEqual(self.operations("runtime.start"), [])

    def test_a_runtime_removed_underneath_the_manager_is_uncertain(self):
        """PARTITION, and the honest answer is `uncertain` -- never absence.

        The container is destroyed OUT OF BAND, which is what a partition or
        an operator looks like from here: the manager's row still names a
        runtime and the engine lists nothing. Absence would release an
        assignment whose worker might be running, so the axis must move to
        `uncertain` and the runtime id must stay attached.

        Composed against a real engine rather than a fake empty listing,
        because an empty listing is the one answer a fake gives for free.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        removed = subprocess.run([self.engine, "rm", "--force", runtime_id],
                                 capture_output=True, timeout=120)
        self.assertEqual(removed.returncode, 0,
                         removed.stderr.decode("utf-8", "replace"))

        # BOTH BRANCHES, because they are two different questions and
        # `reconcile_runtime` answers them separately. A caller that just
        # started something and cannot see it is not the same as a restart
        # that knows nothing -- and only one of the two is reached per call,
        # so a case that took either alone would leave the other unmeasured.
        minted = reconcile_runtime(self.store, adapter,
                                   attempt_id=self.attempt,
                                   minted=runtime_id,
                                   minted_labels=self.labels())
        self.assertEqual(minted["decision"], "uncertain", minted)
        self.assertIn("could leave two runtimes", minted["why"])

        decided = reconcile_runtime(self.store, adapter,
                                    attempt_id=self.attempt)
        self.assertEqual(decided["decision"], "uncertain", decided)
        self.assertIn("would risk two runtimes", decided["why"])
        row = self.attempt_row()
        self.assertEqual(row["execution_runtime"], "uncertain")
        # NOT `destroyed`, and the transition map is why: `uncertain` may
        # never become `destroyed`, because destruction is a fact about the
        # world and a failure to look is not one.
        self.assertNotIn("destroyed",
                         TRANSITIONS["execution_runtime"]["uncertain"])
        self.assertEqual(row["runtime_id"], runtime_id)

    def test_consent_is_absent_before_the_execution_container_is_created(self):
        """The ORDER the topology fixes, read off one trace.

        "No execution workspace exists in consent; consent is absent before
        execution creation" is an ordering claim, and the earlier case proved
        only the two halves separately. Both containers are driven here, in
        one case, and the trace decides.
        """
        given, assignment = self.claimed()
        roots = self.roots()
        consent = self.adapter(posture="consent", roots=roots)
        started = consent.start({
            "labels": self.labels(),
            "operation_id": f"runtime.start:{uuid.uuid4().hex[:12]}"})
        observe(self.store, attempt_id=self.attempt, axis="consent_runtime",
                value="running")
        gone = consent.destroy(manager_documents.destroy_command(
            assignment_ref=dict(self.live), runtime_attempt_id=self.attempt,
            runtime_id=started["runtime_id"],
            intake_receipt_digest="sha256:" + "0" * 64,
            retention_policy_digest="sha256:" + "0" * 64))
        self.assertEqual(gone["state"], "absent", gone["why"])
        observe(self.store, attempt_id=self.attempt, axis="consent_runtime",
                value="destroyed")
        absent_at = len(self.trace)

        activate_assignment(self.store, self.port, attempt_id=self.attempt,
                            expect=dict(self.live))
        inputs = self.composed(roots, given, assignment)
        request_runtime_start(
            self.store, self.adapter(roots=roots, mounts=self.plan(roots)),
            attempt_id=self.attempt, inputs=inputs)

        created = [index for index, (kind, argv) in enumerate(self.trace)
                   if kind == "engine" and "run" in argv]
        self.assertEqual(len(created), 2, self.trace)
        # The consent container's creation, then its proved absence, then the
        # execution container's creation -- strictly in that order.
        self.assertLess(created[0], absent_at)
        self.assertLess(absent_at, created[1])
        self.assertEqual(self.attempt_row()["consent_runtime"], "destroyed")
        self.assertEqual(self.attempt_row()["execution_runtime"], "running")

    # -- PLAN 3: cancel and quiescence ---------------------------------------

    def test_cancellation_fences_the_authority_before_it_stops_the_runtime(
            self):
        """FENCE, THEN STOP -- and the order is read from both sides at once.

        This is the composition's sharpest claim: the authority call and the
        engine call are made by two different components, and only an
        integration can say which happened first. A runtime stopped before the
        generation is fenced is a worker torn out from under an assignment the
        authority still believes is executing.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]

        agent = RecordingAgent(self.trace)
        answer = request_cancellation(self.store, self.port, agent, adapter,
                                      attempt_id=self.attempt,
                                      reason="composition")
        self.assertTrue(answer["fenced"]["fenced"])
        # THE ORDER, READ OFF ONE TRACE. Fence, then the agent, then the
        # engine's stop -- each index strictly before the next, so a
        # reordering fails here rather than passing two independent lists.
        order = [one[0] for one in self.trace]
        fenced_at = order.index("authority.cancel")
        asked_at = order.index("agent.cancel")
        stopped_at = next(
            index for index, (kind, argv) in enumerate(self.trace)
            if kind == "engine" and index > fenced_at
            and ("stop" in argv or "kill" in argv))
        self.assertLess(fenced_at, asked_at, self.trace)
        self.assertLess(asked_at, stopped_at, self.trace)
        self.assertEqual(agent.calls[0]["runtime_id"], runtime_id)
        # ORDERED, never claimed done.
        self.assertTrue(answer["quiescence"]["ordered"])
        self.assertNotIn("stopped", answer["quiescence"])
        # AND THE ENGINE AGREES THE CONTAINER IS NO LONGER RUNNING.
        self.assertNotEqual(self.inspected(runtime_id)["State"]["Status"],
                            "running")

    def test_destroy_is_unreachable_without_the_provisional_path(self):
        """The certified surface ends here, and the topology is why.

        `authorize_cleanup` destroys nothing without an intake receipt,
        `request_intake` takes custody only of a FROZEN result, and only
        `request_freeze` -- which calls `adapter.seal` -- freezes one. So for a
        runtime that ever started, destroy and positive absence sit entirely
        behind W6634's non-satisfying code.

        This case does not test W6634. It establishes the REACHABILITY fact
        this Job is obliged to report: the composition stops here because the
        manager refuses to go further, not because the integration chose not
        to. If a later slice makes destroy reachable on certified code, this
        case fails and says so.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        before = len(self.engine_calls)
        blocked = authorize_cleanup(self.store, self.port, adapter,
                                    attempt_id=self.attempt,
                                    retention_policy_digest="sha256:"
                                                            + "0" * 64)
        self.assertEqual(self.attempt_row()["cleanup"], "blocked-on-intake",
                         blocked)
        self.assertEqual(len(self.engine_calls), before,
                         "cleanup reached the engine without a receipt")

    # -- PLAN 4: restart and race --------------------------------------------

    def test_a_second_incarnation_adopts_the_running_runtime(self):
        """A restart reconciles onto what exists and starts nothing new.

        A SECOND `ControlStore` OVER THE SAME FILE is what a restart actually
        is. The new incarnation reads the attempt row it inherited, derives the
        same labels, asks the engine, and attaches -- and the engine is asked
        afterwards whether exactly one container carries them.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]

        restarted = self.open_store(incarnation="manager-w6636-restarted")
        adopted = reconcile_runtime(restarted, adapter,
                                    attempt_id=self.attempt)
        self.assertEqual(self.attempt_row(restarted)["runtime_id"],
                         runtime_id, adopted)
        self.assertEqual(self.attempt_row(restarted)["execution_runtime"],
                         "running")
        labels = self.labels()
        self.assertEqual(len(self.carrying(labels)), 1)

    def test_a_stranger_carrying_this_assignments_labels_cancels(self):
        """MULTIPLICITY IS A RACE, and the manager's answer is to cancel.

        A second container carrying the same labels is exactly what two
        managers racing would leave behind. Composed with a REAL one rather
        than a fake listing, because the thing under test is that the adapter's
        label filter and the manager's comparison agree about what "the same
        assignment" means.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        labels = self.labels()
        stranger = f"{MARK}-stranger-{uuid.uuid4().hex[:8]}"
        self.made.append(stranger)
        # `--entrypoint` because the worker image's entrypoint IS the worker,
        # and this container must be a STRANGER rather than a second worker:
        # the question is what the manager does about two containers wearing
        # one assignment's labels, not what a second worker would do.
        argv = [self.engine, "run", "--detach", "--name", stranger,
                "--entrypoint", "sleep"]
        for name, value in sorted(labels.items()):
            argv += ["--label", f"{LABEL_PREFIX}{name}={value}"]
        argv += [self.image_digest, "600"]
        made = subprocess.run(argv, capture_output=True, timeout=300)
        self.assertEqual(made.returncode, 0,
                         made.stderr.decode("utf-8", "replace"))

        decided = reconcile_runtime(self.store, adapter,
                                    attempt_id=self.attempt)
        self.assertEqual(decided["decision"], "cancel", decided)
        self.assertIn("2 runtimes", decided["why"])
        self.assertEqual(self.attempt_row()["execution_runtime"],
                         "cancel-requested")

    def test_an_engine_that_cannot_start_leaves_no_running_attempt(self):
        """A start the daemon refuses is a failure, never a silent success.

        The refusal is made real -- an image identity no engine holds -- rather
        than injected, because the question is what the DAEMON does with a
        vector the adapter composed, and a fake port answering "status 1" would
        be this suite deciding the outcome it is measuring.
        """
        given, assignment = self.activated()
        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               image="sha256:" + "e" * 64)
        with self.assertRaises(Exception):
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
        self.assertNotEqual(self.attempt_row()["execution_runtime"], "running")
        self.assertIsNone(self.attempt_row()["runtime_id"])

    def test_observe_tells_a_live_runtime_from_a_gone_one(self):
        """`absent` is the ONE answer that releases an assignment.

        Every other case in this module reads `observe` where the honest
        answer happens to be absence, so an adapter that answered `absent` to
        everything satisfied all of them -- measured, and it did. That is the
        exact failure the operation exists to prevent: a manager that treated
        confusion as death would release an assignment whose worker is still
        running.

        So a container that IS running is put in front of it. It is created
        directly rather than through `start`, because the adapter's execution
        containers exit at once (see
        `test_the_adapter_starts_no_worker_that_can_run`) and `observe` is a
        read-only question about an identity, not about who made it.
        """
        adapter = self.adapter(roots=self.roots())
        alive = f"{MARK}-alive-{uuid.uuid4().hex[:8]}"
        self.made.append(alive)
        made = subprocess.run(
            [self.engine, "run", "--detach", "--name", alive,
             "--entrypoint", "sleep", self.image_digest, "600"],
            capture_output=True, timeout=300)
        self.assertEqual(made.returncode, 0,
                         made.stderr.decode("utf-8", "replace"))
        # BY THE IDENTITY THE ADAPTER WOULD HOLD, which is the id the engine
        # minted rather than the name this case chose: `observe` refuses an
        # answer that is not about the exact identity it asked about, and a
        # name is a second handle on the same container.
        alive_id = made.stdout.decode("utf-8").strip()

        running = adapter.observe(alive_id)
        self.assertEqual(running["state"], "running", running["why"])

        subprocess.run([self.engine, "stop", "--time", "1", alive_id],
                       capture_output=True, timeout=120)
        self.settled(alive_id)
        stopped = adapter.observe(alive_id)
        self.assertEqual(stopped["state"], "quiescent", stopped["why"])
        # AND ONLY REMOVAL PRODUCES ABSENCE.
        self.assertNotEqual(stopped["state"], "absent")
        subprocess.run([self.engine, "rm", "--force", alive_id],
                       capture_output=True, timeout=120)
        self.assertEqual(adapter.observe(alive_id)["state"], "absent")

    # -- PLAN 4: what composition finds and no component suite could ----------

    def test_the_adapter_starts_no_worker_that_can_run(self):
        """[FINDING] W6632 composes no `--env`, and W6633 requires four.

        THE TWO CLOSED COMPONENTS DO NOT MEET. `run_vector` emits restrictions,
        labels, mounts, credential mounts and the image -- and no environment
        at all. The reference worker reads its posture, its session, its
        contract and its role from the environment and, finding none, exits at
        once without a frame. So EVERY execution container the reviewed adapter
        starts from the reviewed image is dead a fraction of a second later.

        NEITHER COMPONENT'S SUITE COULD SEE IT. W6632's engine suite runs the
        pinned BASE image, which has no such requirement; W6633's container
        suite composes its own `docker run` with `--env` for every variable and
        never calls the adapter. Each half is right about itself. The defect is
        only in the join, which is this Job's subject.

        MEASURED, not read off the source: the vector is inspected for an
        environment flag AND the container is asked what became of it.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        run = next(argv for argv in self.engine_calls if "run" in argv)
        self.assertEqual([one for one in run if one in ("--env", "-e")], [],
                         "the adapter now composes an environment; this "
                         "finding may be resolved and the case must be "
                         "rewritten rather than deleted")
        self.settled(runtime_id)
        held = self.inspected(runtime_id)
        self.assertEqual(held["State"]["Status"], "exited")
        self.assertNotEqual(held["State"]["ExitCode"], 0)
        # AND IT SAID NOTHING, which is the worker's own contract: a container
        # that cannot correlate what it says does not speak.
        logs = subprocess.run([self.engine, "logs", runtime_id],
                              capture_output=True, timeout=120)
        self.assertEqual(logs.stdout, b"")
        self.assertEqual(logs.stderr, b"")

    def test_the_manager_records_running_for_a_worker_that_is_gone(self):
        """[FINDING] `reconcile_runtime` never asks the engine for a state.

        `list_vector` is `ps --all`, and `_attach` observes `running` for
        anything the filter returns -- so an EXITED container satisfies the
        reconciliation exactly as a live one does. Composed with the finding
        above, the manager records `execution_runtime = running` for a worker
        that died before the call returned, and `observe` is the only thing
        that could ever correct it.

        The adapter HAS the operation that would settle this: `observe` answers
        `running`, `quiescent`, `absent` or `uncertain` about one exact
        identity. No manager operation calls it. That is the shape of the fix,
        and naming it is this Job's business; making it is not.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        self.settled(runtime_id)
        # The engine says it is gone.
        self.assertEqual(self.inspected(runtime_id)["State"]["Status"],
                         "exited")
        # The manager, asked again, still says it is running.
        again = reconcile_runtime(self.store, adapter,
                                  attempt_id=self.attempt)
        self.assertEqual(self.attempt_row()["execution_runtime"], "running",
                         again)
        # AND THE ADAPTER KNEW BETTER ALL ALONG, which is what makes this a
        # missing call rather than a missing capability.
        self.assertIn(adapter.observe(runtime_id)["state"],
                      ("quiescent", "absent"))

    def test_nothing_this_module_made_survives_it(self):
        """Asked of the engine, by this Work's own mark and by label."""
        found = subprocess.run(
            [self.engine, "ps", "--all", "--filter", f"name={MARK}",
             "--format", "{{.Names}}"], capture_output=True, timeout=120)
        self.assertEqual(found.returncode, 0,
                         found.stderr.decode("utf-8", "replace"))
        self.assertEqual(found.stdout.decode("utf-8").split(), [])


class Watched:
    """One adapter, recording which of its members a caller reached for.

    `_plan_agrees` reads `mounts` with `getattr`, so the access -- not a call
    -- is the event, and a plain wrapper with a method counter would see
    nothing. Every other member is forwarded unchanged, because the thing
    under observation is the manager's ORDER and not the adapter's behaviour.
    """

    def __init__(self, adapter):
        object.__setattr__(self, "_adapter", adapter)
        object.__setattr__(self, "consulted", [])

    def __getattr__(self, name):
        self.consulted.append(name)
        return getattr(self._adapter, name)


class RecordingAgent:
    """The agent boundary, writing into the case's ONE ordering trace."""

    def __init__(self, trace):
        self.calls = []
        self.trace = trace

    def cancel(self, request):
        self.calls.append(dict(request))
        self.trace.append(("agent.cancel", dict(request)))
        return {"acknowledged": True}


class DockerComposition(Composition, unittest.TestCase):
    engine = "docker"
    required = True


class PodmanComposition(Composition, unittest.TestCase):
    engine = "podman"
    required = False
