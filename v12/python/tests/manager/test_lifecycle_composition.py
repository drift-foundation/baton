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

import hashlib
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
from baton_v12.contracts import digest as contract_digest
from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                      accept_offer, activate_assignment,
                                      settle_claim,
                                      authorize_cleanup, certify_profile,
                                      decide_retention, issue_offer, observe,
                                      reconcile_runtime, record_attempt,
                                      request_cancellation, request_freeze,
                                      request_intake, request_runtime_start,
                                      submit_claim)
from baton_v12.worker_manager.attempts import TRANSITIONS
from baton_v12.worker_manager import attempts
from baton_v12.worker_manager import documents as manager_documents
from baton_v12.worker_manager import credentials, launch, oci
from baton_v12.worker_manager import retain_manifest
from baton_v12.worker_manager.oci import (LABEL_PREFIX, EnginePort,
                                          OciAdapter)
from baton_v12.worker_manager.workspaces import (assignment_workspace,
                                                 compose_input_root)

from . import input_roots
from .test_offers import (NOW, PRINCIPAL, PROFILE, ROUTE, SCOPE, FakeSession,
                          decision, fake_claim_signature)

MARK = "baton-w6636-lifecycle"
# The retention policy this composition binds by identity. A manager binds a
# policy by digest and never reads it; what matters is that the same one
# authorizes the decision and the destroy.
RETENTION = "sha256:" + "7" * 64
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
        # THE CANONICAL SPELLING, because the two engines do not agree on it.
        #
        # W33936: docker answers `sha256:<hex>` and podman answers the bare
        # hex. The manager tolerates either from an ENGINE -- `oci._image` says
        # so in as many words, "however the engine spells the prefix" -- but a
        # CONFIGURED identity is required to be the canonical form, which is
        # the asymmetry that lets a deployment's own record be exact while an
        # engine's answer is merely comparable. This fixture stands in for the
        # deployment, so it writes the canonical form; taking podman's spelling
        # verbatim made every Podman case in the matrix fail on the digest
        # rule before reaching the group it was about.
        resolved = found.stdout.decode("utf-8").strip()
        cls.image_digest = (resolved if resolved.startswith("sha256:")
                            else f"sha256:{resolved}")

    def setUp(self):
        self.made = []
        self._launches = 0
        self._credentials = 0
        # W6636 resumed: the input manifest digest the adapter seals against.
        # Set by `claimed`, which is where the manifest is actually minted.
        self.input_digest = None
        self.addCleanup(self.remove_everything)
        self.home = tempfile.mkdtemp(prefix="v12-w6636-")
        self.addCleanup(forcibly_remove, self.home)
        self.storage = os.path.join(self.home, "storage")
        os.makedirs(self.storage)
        self.attempt = f"attempt-{uuid.uuid4().hex[:10]}"
        self.store = self.open_store()
        # W33936 review [P1]: the configured workspace group, read from this
        # manager's own record rather than composed as an integer.
        self.group = input_roots.configured_group(self.store)
        self.session = FakeSession(participant=WHO, work={
            "status": "open", "phase": "queued", "handler": None,
            "gate": None, "authority_uuid": UUID,
            # W16823: what the offer freezes about the Work.
            "scope": SCOPE, "route": ROUTE})
        live = {"work_ref": dict(WORK_REF), "participant": WHO,
                "generation": 1}
        # W16823: the closed claim result.
        self.session.claim_answer = {"assignment": dict(live),
                                     "claim_event": 1,
                                     "decision": decision()}
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
        # W43975: every ending settles on a directory-custody receipt, and a
        # custody act reads the DEPLOYMENT's configured store.
        from baton_v12.worker_manager.workspaces import (
            configure_workspace_storage)
        configure_workspace_storage(store, self.storage)
        return store

    # -- the one thing this suite does to the world --------------------------

    def spawn(self, argv, *, seconds=None):
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
        return assignment_workspace(self.group, self.storage, self.attempt)

    def declarations(self, given):
        """The declared outputs, TAKEN FROM THE INPUT MANIFEST this attempt was
        claimed against.

        NOT WRITTEN OUT HERE, and that is the point. §12 rule 15 holds the
        worker's envelope against the manager's declarations and the
        declarations against the retained input manifest -- one answer per
        declaration, exact name, type and path. A suite that composed its own
        list would be testing whether it can copy the manifest it just read.
        """
        return [dict(one) for one in given["outputs"]]

    def produced(self, roots, declarations, name="result.txt",
                 body="the worker's answer"):
        """The declared output tree, on the host side of the workspace bind.

        WRITTEN HERE RATHER THAN BY THE WORKER, and the distinction is worth
        being exact about. W6633's reference worker speaks
        `baton.worker-entry/1` over stdin and authors no files; making it write
        one would be changing another Work's artefact to suit this suite. What
        W6636 owns is the CROSSING -- quiescence, freeze, collect, retention,
        removal, absence, provider teardown, settlement -- and every one of
        those acts on bytes in the workspace whoever put them there. So this
        composes the bytes at the same host path the container writes through,
        and the arc downstream of them is the real one.
        """
        made = []
        for one in declarations:
            tree = os.path.join(roots["workspace"], one["path"])
            os.makedirs(tree, exist_ok=True)
            with open(os.path.join(tree, name), "w",
                      encoding="utf-8") as handle:
                handle.write(body)
            made.append(tree)
        return made

    def published(self, roots, declarations, disposition="completed"):
        """The worker's `/output/output.json`, as a worker would leave it.

        THE ENVELOPE IS THE COMPLETION SIGNAL, so a completed freeze without
        one is a completion nothing signalled -- the manager opens it, owns it,
        holds it against the declarations and recomputes its digest. Composed
        here for the same reason the output tree is: W6633's reference worker
        publishes no envelope, and the crossing W6636 owns begins at the bytes
        rather than at their authorship.
        """
        answers = []
        for one in declarations:
            place = os.path.join(roots["workspace"], one["path"])
            answers.append({
                "name": one["name"], "type": one["type"], "path": one["path"],
                "status": ("present" if os.path.isdir(place)
                           else "missing-optional"),
                "content_manifest": (self.measured(place)
                                     if os.path.isdir(place) else None),
                "result_metadata": {}})
        body = {"version": {"major": 1, "minor": 0},
                "manifest_id": f"completion-{self.attempt}",
                "created_at": NOW, "extensions": {},
                "schema": "baton.worker-manifest/completion",
                "assignment_ref": {"work_ref": dict(WORK_REF),
                                   "participant": WHO, "generation": 1},
                "disposition": disposition, "outputs": answers}
        body["manifest_digest"] = contract_digest(body)
        place = os.path.join(roots["workspace"], "output.json")
        with open(place, "wb") as handle:
            handle.write(json.dumps(body, sort_keys=True).encode("utf-8"))
        return body

    @staticmethod
    def measured(place):
        """One tree's content manifest, by the frozen rules.

        Computed rather than asserted: a manifest whose aggregates disagree
        with its entries is refused, so a fixture that guessed would be turned
        away before it reached the crossing under test.
        """
        entries = []
        for base, _directories, files in os.walk(place):
            for one in sorted(files):
                full = os.path.join(base, one)
                with open(full, "rb") as reading:
                    content = reading.read()
                entries.append({
                    "path": os.path.relpath(full, place),
                    "bytes": len(content),
                    "content_digest": "sha256:" + hashlib.sha256(
                        content).hexdigest()})
        entries.sort(key=lambda entry: entry["path"].encode("utf-8"))
        return {"entries": entries, "entry_count": len(entries),
                "total_bytes": sum(one["bytes"] for one in entries),
                "tree_digest": contract_digest(entries)}

    def credential(self, slots=("registry",)):
        """One materialized fresh-run credential delivery. W26284.

        The bearer is minted here and registered live by the provider, exactly
        as a real profile provider's answer would be -- the manager never sees
        the bytes, and the §13 sweep at `EnginePort.__call__` is what proves it
        cannot.
        """
        home = credentials.CredentialHome(
            os.path.join(self.home, f"credentials-{self._credentials}"))
        self._credentials += 1
        # THROUGH THE TRUSTED PROFILE, like a real delivery: the assignment
        # authorizes slot NAMES and the profile maps them to opaque provider
        # references, so nothing here chooses what a bearer is.
        delivery = home.materialize(
            credentials.resolved_delivery(
                list(slots),
                profile={one: {"provider": "vault",
                               "reference": f"ref-{one}"}
                         for one in slots}),
            attempt_id=self.attempt,
            # W52800: the slot's reader group is a grant, minted from this
            # fixture's own manager store like every other capability here.
            workspace_group=self.group,
            credential_provider=lambda name, reference: f"bearer-{reference}")
        self.addCleanup(self._release_credential, home, delivery)
        return delivery

    def _release_credential(self, home, delivery):
        """Tear the delivery down if the case did not, and never fail for it.

        A composition case that reaches its own ending has already settled the
        delivery through the adapter; this is the net for the ones that refuse
        part way, so a live bearer never outlives the case that minted it.
        """
        try:
            if delivery.state != "torn-down":
                home.tear_down(delivery)
        except Exception:                                  # noqa: BLE001
            pass

    def adapter(self, posture="execution", roots=None, mounts=(),
                image=None, launch_delivery=False, outputs=None,
                credential_delivery=None):
        """The reviewed adapter, under THIS assignment's resolved identity.

        W6636 resumed: `outputs` and `credential_delivery` are REAL now. They
        were deliberately absent while W6634 was the only implementation of
        either, and this composition would not stand on it; W26283 and W26284
        replaced that surface and closed satisfying, so the arc runs through
        the production providers rather than around them.

        BOTH ROOTS ARE ALWAYS DECLARED, in both postures. `MOUNTABLE` -- not
        the constructor -- is what gives a consent container nothing to mount,
        and a consent adapter built without the roots would refuse before that
        rule was ever reached.

        W26291: THE LAUNCH DELIVERY IS ADAPTER-SCOPED, like the credential one
        and unlike the input root. `launch_delivery=False` means "make one",
        because every execution container in this composition needs one to
        start at all; `None` means deliberately none, which is the case that
        proves a worker without its document does not run.
        """
        return OciAdapter(
            self.engine, EnginePort(self.spawn),
            identity={"image_digest": image or self.image_digest,
                      "profile_digest": PROFILE, "policy_digest": POLICY,
                      "adapter_digest": ADAPTER},
            assignment_roots=dict(roots if roots is not None
                                  else self.roots()),
            posture=posture, mounts=mounts,
            # W33936: the deployment's configured workspace group. An execution
            # adapter without one refuses before the engine, which is the
            # correction -- so every execution fixture in this composition
            # names the group the allocation actually adopted. A consent
            # adapter is given none and refuses one, so this passes it only
            # where it belongs.
            workspace_group=(self.group if posture == "execution" else None),
            outputs=list(outputs or ()),
            credential_delivery=credential_delivery,
            input_manifest_digest=self.input_digest,
            launch_delivery=(self.launch() if launch_delivery is False
                             else launch_delivery))

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

    def reserved(self, store=None, given=None):
        """Offer, accept, record -- the reservation, and NOT the claim.

        Named apart from `claimed` because the supersession makes the boundary
        between them the thing under test: reservation launches nothing, and
        only a successful claim crosses into execution.
        """
        store = store if store is not None else self.store
        given, assignment = input_roots.documents(
            work_ref=dict(WORK_REF), participant=WHO, generation=1,
            runtime_attempt_id=self.attempt, given=given,
            policy_digest=POLICY, profile_digest=PROFILE)
        self.offer = f"offer-{self.attempt}"
        issue_offer(store, self.port, offer_id=self.offer, work_id=WORK_ID,
                    runtime_attempt_id=self.attempt,
                    input_digest=given["manifest_digest"],
                    policy_digest=POLICY, profile_digest=PROFILE,
                    profile_name="reference", mint_bearer=lambda: "bearer-1")
        accept_offer(store, self.port, offer_id=self.offer, decision="accept",
                     bearer="bearer-1", now=NOW,
                     runtime_attempt_id=self.attempt,
                     work_ref=dict(WORK_REF))
        record_attempt(store, attempt_id=self.attempt, adapter_name="acp",
                       adapter_digest=ADAPTER, profile_digest=PROFILE,
                       input_digest=given["manifest_digest"],
                       policy_digest=POLICY)
        self.input_digest = given["manifest_digest"]
        return given, assignment

    def offer_row(self, store=None):
        store = store if store is not None else self.store
        row = store._connection.execute(
            "SELECT * FROM offers WHERE offer_id = ?",
            (self.offer,)).fetchone()
        return dict(row) if row is not None else None

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
        self.input_digest = given["manifest_digest"]
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

    def launch(self, **overrides):
        """One materialized launch delivery for this attempt. W26291.

        AUTHORED BY THE MANAGER, not assembled here. This fixture supplies the
        three values a real caller supplies and `launch.materialize` decides
        the shape, writes the bytes and freezes the file -- so what crosses the
        seam in this composition is the same typed capability a real delivery
        crosses it with, rather than a dict this suite shaped to fit.
        """
        # ONE PER ADAPTER, NOT ONE PER ATTEMPT. W26291 re-review [P1] gave the
        # launch root an ending, so a refused start or a destroyed runtime
        # DISCARDS it — and a fixture that handed the same delivery to a
        # second adapter would be handing it a document the first one already
        # tore down. Each call mints its own under its own storage root, which
        # is what two real starts would each have.
        self._launches += 1
        home = os.path.join(self.home, f"launch-{self._launches}")
        os.makedirs(home, exist_ok=True)
        body = {"attempt_id": self.attempt,
                "session": f"session-{self.attempt}",
                "contract": "compose the local OCI lifecycle",
                "role": "implementer"}
        body.update(overrides)
        delivery = launch.materialize(home, **body)
        self.addCleanup(launch.discard, delivery.root)
        return delivery

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
                # W16823: the principal and effective scope the claim was
                # authorized for, beside the fence.
                "principal": PRINCIPAL, "effective_scope": SCOPE,
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
    #
    # W33936: AND SOME OF IT IS NOT THIS PROCESS'S TO CHMOD. Once the worker
    # can write its workspace it creates content it OWNS, and a fixture that
    # assumed every entry was its own faulted on the first worker-created
    # directory. Both `chmod` calls are attempts; `rmtree(ignore_errors=True)`
    # already says what happens to what cannot be removed, and a test fixture
    # is not the place to decide that -- `workspaces._remove` is, and it
    # refuses with the ownership named.
    for current, _directories, files in os.walk(place):
        try:
            os.chmod(current, 0o700)
        except OSError:
            pass
        for name in files:
            try:
                os.chmod(os.path.join(current, name), 0o600)
            except OSError:
                pass
    shutil.rmtree(place, ignore_errors=True)


class Composition(Lifecycle):
    """The ordered lifecycle, over one real engine."""

    # -- PLAN 2: consent teardown, activation, fresh execution ---------------

    def test_a_reservation_launches_no_runtime(self):
        """THE DIRECT CROSSING, and its first half.

        The supersession replaced the two-container consent/execution topology
        with one: the trusted adapter reserves an eligible slot WITHOUT
        launching a runtime, the manager atomically claims, and only a
        successful claim launches the single execution container. So an offer
        issued and accepted must reach no engine at all.

        This replaces `test_the_consent_runtime_is_torn_down_before_execution
        _exists`, which proved a consent container mounted nothing and was
        destroyed before execution. That container no longer exists in the
        topology; what survives from it is the ordering claim, and this is
        where the ordering now begins.
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
        accept_offer(self.store, self.port, offer_id=offer, decision="accept",
                     bearer="bearer-1", now=NOW,
                     runtime_attempt_id=self.attempt,
                     work_ref=dict(WORK_REF))
        # RESERVED, AND NOTHING RUNS. Asked of the engine rather than of the
        # store: no container carries this assignment's labels, and this
        # composition has spoken to the daemon not at all.
        self.assertEqual(self.engine_calls, [])
        # ASKED OF THE DAEMON DIRECTLY, by the assignment's own labels: no
        # attempt row exists yet, so this is the label set the manager WOULD
        # derive rather than one read back from a row.
        self.assertEqual(self.carrying(
            {"runtime_attempt_id": self.attempt, "authority_uuid": UUID,
             "work_id": WORK_ID, "participant": WHO, "generation": 1,
             "profile_digest": PROFILE, "policy_digest": POLICY,
             "adapter_digest": ADAPTER}), [])

    def test_only_a_successful_claim_launches_one_container(self):
        """...and its second half, read off ONE trace.

        The superseded ordering case drove two containers and compared their
        positions in the trace. There is one container now, so the ordering
        that matters is between the CLAIM and the launch: nothing before it,
        exactly one after.
        """
        given, assignment = self.claimed()
        self.assertEqual(self.engine_calls, [],
                         "the claim reached the engine")
        activate_assignment(self.store, self.port, attempt_id=self.attempt,
                            expect=dict(self.live))
        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        adapter = self.adapter(roots=roots, mounts=self.plan(roots))
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        self.assertEqual(len(self.carrying(self.labels())), 1)
        runs = [argv for argv in self.engine_calls if "run" in argv]
        self.assertEqual(len(runs), 1, runs)

    def test_a_lost_claim_cannot_cross_into_execution(self):
        """The race the atomic claim exists to arbitrate.

        REVIEW [P1] CORRECTED THIS CASE, and the correction is the difference
        between a malformed document and a competing claim. The first version
        set `claim_answer = None` and called that "the authority saying
        somebody else holds it". It is not: the port owns a claim answer as one
        exact assignment document, so `None` is refused `integrity/schema`, the
        offer stays `accepted`, and nothing is settled. Its closing assertion
        was then non-probative — `submit_claim` launches no runtime on ANY
        path, and the case never tried the step after it.

        The race is the claim capability's TYPED REFUSAL, settled through the
        `claim-refused` path the authority port already has. What the
        supersession actually requires is then asserted: a loser cannot cross
        from reservation into execution.
        """
        given, assignment = self.reserved()
        # THE AUTHORITY REFUSES: somebody else won this Work.
        self.session.claim_answer = ContractRefusal(
            "refused", "precondition",
            "this work is already claimed by another participant")
        with self.assertRaises(ContractRefusal) as lost:
            submit_claim(self.store, self.port, offer_id=self.offer)
        # THE CAPABILITY'S OWN REFUSAL CROSSES, rather than a boundary
        # complaining about a document. The first version could not tell those
        # apart, which is what made it non-probative.
        self.assertEqual(lost.exception.category, "refused")
        self.assertIn("already claimed by another participant",
                      str(lost.exception))

        # AND THE OFFER REACHES ITS DURABLE REFUSED ENDING, through the one
        # settlement path rather than by this case writing a row.
        self.session.settle_answer = {
            "kind": "refused",
            "detail": "this work is already claimed by another participant"}
        settle_claim(self.store, self.port, offer_id=self.offer, now=NOW,
                     refused_evidence="the authority refused the claim")
        self.assertEqual(self.offer_row()["state"], "claim-refused")

        # THE NEXT LIFECYCLE STEP IS REFUSED, which is the crossing that
        # matters: reservation does not become execution for a loser.
        with self.assertRaises(ContractRefusal) as denied:
            activate_assignment(self.store, self.port,
                                attempt_id=self.attempt,
                                expect=dict(self.live))
        # NO COMMITTED CLAIM. Each refusal's REASON is asserted, so a case that
        # passed for some unrelated precondition would say so.
        self.assertIn("has no committed claim", str(denied.exception))
        roots = self.roots()
        inputs = self.composed(roots, given, assignment)
        with self.assertRaises(ContractRefusal) as refused:
            request_runtime_start(
                self.store, self.adapter(roots=roots,
                                         mounts=self.plan(roots)),
                attempt_id=self.attempt, inputs=inputs)
        self.assertIn("is not activated", str(refused.exception))

        # AND NO ENGINE WAS EVER ASKED TO RUN ANYTHING. Asserted over the
        # trace and over the daemon, because a refusal that had already
        # created a container would satisfy the first alone.
        self.assertEqual([argv for argv in self.engine_calls
                          if "run" in argv], [])
        self.assertEqual(self.carrying(self.labels()), [])

    def test_a_delivery_that_was_never_made_is_not_reported_torn_down(self):
        """[MEASURED] `not-delivered` is a different word from `absent`.

        The runtime's own state beside it is `absent`, and one word meaning
        two things in one document is how a reader concludes a credential was
        torn down because a container was.

        This replaces the consent-posture case that established the same
        distinction. The distinction is not about consent -- it is about a
        provider that was never delivered -- so it is asserted here on the
        live one-container topology, where it now also has the OTHER half
        beside it: the full arc proves a delivery that WAS made ends
        `torn-down` and its root leaves the disk.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        self.settled(runtime_id)
        gone = adapter.destroy(manager_documents.destroy_command(
            assignment_ref=dict(self.live), runtime_attempt_id=self.attempt,
            runtime_id=runtime_id,
            intake_receipt_digest="sha256:" + "0" * 64,
            retention_policy_digest="sha256:" + "0" * 64))
        self.assertEqual(gone["state"], "absent", gone["why"])
        self.assertEqual(gone["credentials"],
                         {"lifecycle_state": "not-delivered"})
        # AND THE LAUNCH DOCUMENT, WHICH WAS delivered, ends differently in
        # the same answer -- which is the whole reason the two are separate
        # members rather than one word about "the mounts".
        self.assertEqual(gone["launch"]["lifecycle_state"], "torn-down")

    def test_cleanup_without_an_intake_receipt_is_blocked_rather_than_run(
            self):
        """Cleanup destroys nothing it has no receipt for.

        This is what survives `test_destroy_is_unreachable_without_the
        _provisional_path`. That case reported a REACHABILITY fact -- destroy
        sat behind provisional code -- and said it would fail and say so when
        a later slice made destroy reachable on certified code. It has: the
        full arc reaches destroy through the production providers. The rule
        underneath it is still true and still worth holding.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        before = len(self.engine_calls)
        self.session.live_assignment = None
        blocked = authorize_cleanup(self.store, self.port, adapter,
                                    attempt_id=self.attempt,
                                    retention_policy_digest=RETENTION)
        self.assertEqual(self.attempt_row()["cleanup"], "blocked-on-intake",
                         blocked)
        self.assertEqual(len(self.engine_calls), before,
                         "cleanup reached the engine without a receipt")

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
        stranger = assignment_workspace(
            self.group, self.storage, other)["inputs"]
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
        strange_roots = assignment_workspace(self.group, self.storage, other)
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
        self.session.claim_answer = {"assignment": dict(live),
                                     "claim_event": 2,
                                     "decision": decision()}
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

    def test_a_runtime_removed_underneath_the_manager_is_observed_absent(self):
        """W26294 review [P0] INVERTED THIS CASE, and the inversion is the
        whole correction.

        It used to require `uncertain` here, on the reasoning that a manager
        whose row names a runtime and whose engine lists nothing has failed to
        look rather than seen an absence. That reasoning was about the
        LISTING, and it stopped being true the moment the exact identity is
        asked about: the container really was removed, the adapter really can
        say so by name, and calling that a failure to look made positive
        absence unreachable in the ordinary post-removal shape -- which is the
        one this Work's acceptance is about.

        So the honest answer is what the ADAPTER says about the exact runtime,
        and the identity is never erased either way.

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
        # A REAL DAEMON, ASKED BY NAME about a container that really is gone.
        self.assertEqual(minted["observed"], "destroyed", minted)

        decided = reconcile_runtime(self.store, adapter,
                                    attempt_id=self.attempt)
        self.assertEqual(decided["observed"], "destroyed", decided)
        row = self.attempt_row()
        self.assertEqual(row["execution_runtime"], "destroyed")
        # AND THE IDENTITY IS NOT ERASED. Whatever the runtime turned out to
        # be, which runtime this attempt HAD is a fact the row keeps.
        self.assertEqual(row["runtime_id"], runtime_id)
        # THE TRANSITION MAP'S OWN RULE IS UNCHANGED and still says why the
        # two answers are not interchangeable: `uncertain` may never become
        # `destroyed`, because destruction is a fact about the world and a
        # failure to look is not one. What changed is that this case is no
        # longer a failure to look.
        self.assertNotIn("destroyed",
                         TRANSITIONS["execution_runtime"]["uncertain"])

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

    def test_the_whole_one_container_arc_reaches_a_clean_settlement(self):
        """THE ARC W6636 EXISTS TO COMPOSE, end to end, on a real engine.

        Offer reservation, accept, atomic claim, activation, exact input and
        private-root composition, ONE execution start, the agent's outcome,
        positive quiescence, freeze, intake, retention, force-removal, exact
        absence, both provider teardowns, and only then a clean settlement.

        IT RUNS THROUGH THE PRODUCTION PROVIDERS. W26283 declares the output,
        W26284 materializes the credential, W26291 delivers the launch
        document -- the three replacements for the surface W6634 left
        provisional, each closed satisfying. The previous rounds composed this
        arc with `outputs=()` and `credential_delivery=None` and could not
        reach an ending at all.
        """
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)
        delivery = self.credential()
        declared = self.declarations(given)
        # THE MANAGER HOLDS THE MANIFEST IT COMPARES AGAINST. A freeze refuses
        # an attempt whose input manifest this manager never retained, because
        # declared outputs cannot be held against a document nobody kept.
        retain_manifest(self.store, given, "inputManifest")
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               outputs=declared,
                               credential_delivery=delivery)

        # -- one start, and exactly one container ------------------------
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        self.assertIsNotNone(runtime_id)
        self.assertEqual(len(self.carrying(self.labels())), 1)
        # THE ENGINE REALLY RAN, said out loud. This arc completes in under a
        # second on a warm daemon -- the image layers are cached and the
        # reference worker starts, reads its launch document, finds EOF on a
        # closed stdin and exits -- which reads like a suite that mocked the
        # engine. It did not: a real `run` argv crossed the port, and every
        # `inspect` below would fail on a container that does not exist.
        self.assertTrue([argv for argv in self.engine_calls if "run" in argv],
                        self.engine_calls)
        # BY DIGEST, not by tag: the adapter runs the resolved identity it
        # was constructed with, which is what makes the container the artefact
        # this composition built rather than whatever the tag points at now.
        self.assertIn(self.image_digest,
                      next(argv for argv in self.engine_calls
                           if "run" in argv))

        # THE CREDENTIAL AND THE LAUNCH DOCUMENT ARE SEPARATE READ-ONLY
        # MOUNTS. Two manager-owned roots, neither of them assignment
        # material, each at its own fixed path.
        binds = {one["Destination"]: one
                 for one in self.inspected(runtime_id)["Mounts"]}
        for target in ("/run/baton/credentials/registry",
                       launch.LAUNCH_TARGET):
            self.assertIn(target, binds, sorted(binds))
            self.assertFalse(binds[target]["RW"],
                             f"{target} is writable")

        # -- the worker runs and stops ------------------------------------
        self.settled(runtime_id)
        reconcile_runtime(self.store, adapter, attempt_id=self.attempt)
        self.assertEqual(self.attempt_row()["execution_runtime"], "quiescent")

        # -- the outcome, then the freeze ---------------------------------
        self.produced(roots, declared)
        self.published(roots, declared)
        observe(self.store, attempt_id=self.attempt,
                axis="worker_disposition", value="completed")
        frozen = request_freeze(self.store, self.port, adapter,
                                attempt_id=self.attempt,
                                disposition="completed")
        self.assertEqual(self.attempt_row()["output"], "frozen", frozen)

        # -- custody, then a decision about what stays ---------------------
        receipt = request_intake(self.store, self.port, adapter,
                                 attempt_id=self.attempt)
        artifacts = [one["artifact_id"] for one in receipt["artifacts"]]
        self.assertTrue(artifacts, receipt)
        # THE CUSTODY BYTES ARE REALLY THERE BEFORE THE DECISION, so the
        # absence below is a removal rather than a tree that never existed.
        custodied = [os.path.join(adapter._custody(self.attempt),
                                  one["name"]) for one in declared]
        for place in custodied:
            self.assertTrue(os.path.isdir(place), place)
        decide_retention(self.store, self.port, adapter,
                         attempt_id=self.attempt, artifact_ids=artifacts,
                         disposition="discard-after-intake",
                         retention_policy_digest=RETENTION)
        # AND `discard-after-intake` DISCARDED THEM. Review [P0]: this arc
        # accepted `cleanup=complete` over surviving custody, which the
        # manager's own settlement rule calls "nothing was kept" -- a false
        # clean ending rather than an unspecified policy.
        for place in custodied:
            self.assertFalse(os.path.exists(place), place)

        # -- and only now the destroy crossing ----------------------------
        self.session.live_assignment = None
        settled = authorize_cleanup(
            self.store, self.port, adapter, attempt_id=self.attempt,
            retention_policy_digest=RETENTION)

        self.assertEqual(settled["cleanup"], "complete", settled)
        self.assertEqual(settled["state"], "absent")
        row = self.attempt_row()
        self.assertEqual(row["execution_runtime"], "destroyed")
        self.assertEqual(row["cleanup"], "complete")

        # THE ENGINE IS ASKED, not the store. Cleanup is not inferred from a
        # row or a zero exit status: the container is gone from the daemon.
        self.assertEqual(self.carrying(self.labels()), [])
        # AND BOTH DELIVERED ROOTS ARE GONE FROM DISK, which is the half a
        # runtime observation can never establish.
        self.assertEqual(delivery.state, "torn-down")
        self.assertFalse(os.path.exists(delivery.root), delivery.root)
        self.assertFalse(os.path.exists(adapter.launch_delivery.root),
                         adapter.launch_delivery.root)

    # -- what the live container can and cannot see -------------------------

    def test_the_live_container_sees_exactly_the_four_intended_mounts(self):
        """THE SECURITY INSPECTION, asked of the DAEMON about a live runtime.

        Not of the argv this suite watched the manager compose: an adapter
        that composed the right flags and an engine that applied them are two
        facts, and only the second one protects anything.

        FOUR MOUNTS AND NO OTHERS. The exact assignment source read-only at
        `/input`, the one writable private workspace, and the two
        manager-owned deliveries -- credential and launch -- each read-only at
        its own fixed path. Anything else is material this assignment never
        authorized.
        """
        roots = self.roots()
        given, assignment = self.activated()
        inputs = self.composed(roots, given, assignment)
        delivery = self.credential()
        adapter = self.adapter(roots=roots, mounts=self.plan(roots),
                               outputs=self.declarations(given),
                               credential_delivery=delivery)
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        held = self.inspected(self.attempt_row()["runtime_id"])
        binds = {one["Destination"]: one for one in held["Mounts"]}

        self.assertEqual(sorted(binds), sorted([
            "/input", "/workspace", "/run/baton/credentials/registry",
            launch.LAUNCH_TARGET]), sorted(binds))
        self.assertFalse(binds["/input"]["RW"])
        self.assertTrue(binds["/workspace"]["RW"])
        self.assertFalse(binds["/run/baton/credentials/registry"]["RW"])
        self.assertFalse(binds[launch.LAUNCH_TARGET]["RW"])
        # AND EACH SOURCE IS THE EXACT ONE THIS MANAGER PROVED.
        self.assertEqual(os.path.realpath(binds["/input"]["Source"]),
                         os.path.realpath(inputs))
        self.assertEqual(os.path.realpath(binds["/workspace"]["Source"]),
                         os.path.realpath(roots["workspace"]))
        self.assertEqual(os.path.realpath(binds[launch.LAUNCH_TARGET]
                                          ["Source"]),
                         os.path.realpath(adapter.launch_delivery.place))
        credential_source, credential_target = delivery.mounts()[0]
        self.assertEqual(credential_target,
                         "/run/baton/credentials/registry")
        self.assertEqual(
            os.path.realpath(binds[credential_target]["Source"]),
            os.path.realpath(credential_source))

    def test_the_live_container_cannot_reach_the_authority_or_the_host(self):
        """What is ABSENT, which is the half an inspection of what is present
        can never establish.

        The authority store, this repository's checkout, the engine's own
        socket and every unrelated host path are things a worker must not be
        able to read, and the mount set is where that is decided. The engine
        is asked about the live container rather than the manager about its
        intent.
        """
        adapter, roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        held = self.inspected(self.attempt_row()["runtime_id"])
        sources = [os.path.realpath(one["Source"]) for one in held["Mounts"]]
        allowed = [os.path.realpath(roots["inputs"]),
                   os.path.realpath(roots["workspace"]),
                   os.path.realpath(adapter.launch_delivery.place)]
        self.assertEqual(sorted(sources), sorted(allowed), sources)
        # NAMED EXPLICITLY, because "the list is short" is not the same
        # statement as "these exact things are not in it".
        forbidden = [
            # The authority store this manager keeps its own state in.
            os.path.realpath(os.path.join(self.home, "control.sqlite3")),
            # This repository's checkout, which a worker must never be able
            # to read let alone write.
            os.path.realpath(os.path.dirname(os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))))),
            # And the engine's own socket, which is the path from a container
            # to a sibling container.
            "/var/run/docker.sock", "/run/docker.sock"]
        for place in forbidden:
            self.assertNotIn(place, sources, place)
            for source in sources:
                self.assertFalse(source.startswith(place + os.sep),
                                 f"{source} is inside {place}")

    def test_the_runtime_boundary_is_the_one_the_launcher_composed(self):
        """The container-level equivalent of W28681's PID namespace.

        W28681 carried an invariant in: an execution container IS the
        attempt's process domain, and it must not be able to launch host or
        sibling-container processes outside that boundary. In a container the
        boundary is not a flag this suite can grep for -- it is the ENGINE's
        applied configuration, so the engine is asked.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        held = self.inspected(self.attempt_row()["runtime_id"])
        host = held["HostConfig"]

        # NO PATH TO THE DAEMON is what stops a sibling container: with no
        # socket mounted and no network at all, there is nothing to ask.
        self.assertEqual(host["NetworkMode"], "none")
        self.assertNotIn("/var/run/docker.sock",
                         [one["Source"] for one in held["Mounts"]])
        # AND NO PATH TO THE HOST: the process namespace is the container's
        # own, privileges cannot be gained, every capability is dropped, and
        # the process count is bounded.
        # THE ENGINE'S OWN PRIVATE-NAMESPACE ANSWER, pinned. Review [P1]:
        # this excluded only the literal `host`, and Docker also admits
        # `container:<runtime>` -- which JOINS a sibling's PID namespace and
        # is precisely not the attempt-owned process domain W28681 carried in.
        # Excluding one unsafe value is not the same as requiring the safe
        # one. Docker spells a private namespace as the empty string and
        # Podman as `private`; both are the default, and anything else names
        # somebody else's domain.
        self.assertIn(host.get("PidMode") or "", ("", "private"),
                      host.get("PidMode"))
        self.assertFalse(host.get("Privileged"))
        self.assertIn("no-new-privileges", " ".join(host.get("SecurityOpt")
                                                    or []))
        self.assertEqual(host.get("CapAdd") or [], [])
        self.assertEqual([one.upper() for one in (host.get("CapDrop") or [])],
                         ["ALL"])
        # EXACTLY the bound the launcher composes, since this case claims to
        # be about the boundary the launcher composed.
        self.assertEqual(host.get("PidsLimit"), 512)
        self.assertTrue(held["HostConfig"]["ReadonlyRootfs"])
        self.assertEqual(held["Config"]["User"], "65532:65532")

    # -- orphan recovery is bounded to the attempt that proved it stale ------

    def test_orphan_recovery_cannot_delete_a_siblings_delivery(self):
        """A `CredentialHome` is ASSIGNMENT-scoped and can hold several
        attempts' roots, so "no record for THIS attempt" is not evidence about
        any other.

        Composed here because the component's own suite proves the rule over
        one home it built; this drives two REAL deliveries through the seam
        the manager uses and then recovers exactly one.
        """
        # THE ADAPTER'S OWN CREDENTIAL HOME, because that is the one its
        # recovery acts on. Building a separate home and then calling the
        # adapter would have recovered an empty directory and proved nothing —
        # which it did, until this was corrected.
        adapter = self.adapter()
        home = adapter._credential_home()
        mine, theirs = self.attempt, f"{self.attempt}-sibling"
        deliveries = {}
        for attempt in (mine, theirs):
            deliveries[attempt] = home.materialize(
                credentials.resolved_delivery(
                    ["registry"],
                    profile={"registry": {"provider": "vault",
                                          "reference": "ref-registry"}}),
                attempt_id=attempt,
                workspace_group=self.group,
                credential_provider=lambda name, reference: f"bearer-{name}")
        for delivery in deliveries.values():
            self.addCleanup(self._release_credential, home, delivery)
        self.assertTrue(os.path.isdir(deliveries[mine].root))
        self.assertTrue(os.path.isdir(deliveries[theirs].root))

        # THROUGH THE PRODUCTION SEAM. Review [P1]: this called
        # `CredentialHome.discard_orphan` directly, so an adapter that reached
        # for the assignment-wide `discard_orphans` -- or applied evidence
        # about one attempt to its sibling -- would not have been caught. The
        # component suite drives that seam with a fake engine; a COMPOSITION
        # regression has to drive it with two real deliveries.
        #
        # ONE ATTEMPT IS THE ORPHAN, and what makes it one is that no
        # lifecycle record names it while its root is on disk -- which is
        # exactly the state a manager restarts into, and is already true of a
        # materialized delivery whose start never recorded one.
        self.assertIsNone(home.read_state(mine))
        recovered = adapter.recover_credentials(
            {"attempt_id": mine, "assignment": dict(self.live),
             # W16823: the recovery selects by the whole label set.
             "context": {"principal": PRINCIPAL, "effective_scope": SCOPE}})
        self.assertEqual(recovered["lifecycle_state"], "absent", recovered)

        self.assertFalse(os.path.exists(deliveries[mine].root))
        # THE SIBLING IS UNTOUCHED, root and live bearer both.
        self.assertTrue(os.path.isdir(deliveries[theirs].root),
                        "recovering one attempt removed another's material")
        self.assertEqual(deliveries[theirs].state, "live")

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

    def test_the_adapter_starts_a_worker_that_actually_runs(self):
        """W26291: REPLACES this suite's expected-failure case.

        W6636 recorded the defect here as a finding: the adapter delivered
        nothing the reference worker needed, so every execution container it
        started from the reviewed image exited 2 with empty stdout and stderr.
        Two closed components that could not meet.

        The correction Work's acceptance says a positive real-Docker
        regression REPLACES that expected failure and proves the worker becomes
        runnable, which is what this is. The old case asserted the vector
        carried no environment flag; asserting that now would be asserting the
        defect.

        AND THE CORRECTION ITSELF WAS SUPERSEDED before acceptance. The first
        one sent four `BATON_WORKER_*` values as `--env` arguments; what is
        composed now is ONE READ-ONLY MOUNT of a versioned document at a fixed
        path, with no environment at all. So this case asserts both halves: the
        document arrives, and the retired transport does not.

        EXIT 0 IS THE PROOF, and the difference from exit 2 is the whole
        finding: 2 was "I was started without a launch document and cannot
        correlate anything I say", 0 is a worker that started, read its
        document, found EOF on a closed stdin and shut down cleanly.
        """
        adapter, _roots, inputs = self.prepared()
        delivery = adapter.launch_delivery
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        run = next(argv for argv in self.engine_calls if "run" in argv)
        landed = [one for flag, one in zip(run, run[1:])
                  if flag == "--mount" and launch.LAUNCH_TARGET in one]
        self.assertEqual(len(landed), 1, landed)
        self.assertIn(f"source={delivery.place}", landed[0])
        self.assertIn("readonly=true", landed[0])
        # THE RETIRED TRANSPORT, ASSERTED ABSENT at the composition boundary.
        # The supersession keeps no compatibility path, so an `--env` here
        # would be the second live contract it exists to end.
        self.assertNotIn("--env", run)
        self.assertEqual([one for one in run if "BATON_WORKER_" in one], [])

        self.settled(runtime_id)
        held = self.inspected(runtime_id)
        self.assertEqual(held["State"]["Status"], "exited")
        self.assertEqual(held["State"]["ExitCode"], 0,
                         "the reference worker did not start cleanly")
        # AND IT SAID NOTHING, which is still its own contract: a worker handed
        # no frames has nothing to answer.
        logs = subprocess.run([self.engine, "logs", runtime_id],
                              capture_output=True, timeout=120)
        self.assertEqual(logs.stdout, b"")
        self.assertEqual(logs.stderr, b"")

    def test_reconciliation_records_what_the_engine_says_the_runtime_is(self):
        """W26294: CONVERTED from this suite's second diagnostic.

        W6636 recorded the defect here as a finding: `list_vector` is
        `ps --all`, `_attach` observed `running` for anything the label filter
        returned, and an EXITED container therefore satisfied reconciliation
        exactly as a live one did. The manager recorded a running worker for
        one that had already finished, and the adapter had `observe` all
        along with nothing calling it.

        The correction Work's acceptance says this diagnostic becomes a
        positive production-seam proof. The old case asserted the manager
        still said `running`; asserting that now would be asserting the
        defect.

        DRIVEN THROUGH THE PRODUCTION SEAM, not through `observe` directly:
        the question is what `reconcile_runtime` records, and the adapter
        knowing better was never in doubt.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        self.settled(runtime_id)
        self.assertEqual(self.inspected(runtime_id)["State"]["Status"],
                         "exited")

        again = reconcile_runtime(self.store, adapter,
                                  attempt_id=self.attempt)
        self.assertEqual(again["decision"], "attached", again)
        self.assertEqual(again["observed"], "quiescent", again)
        self.assertEqual(self.attempt_row()["execution_runtime"], "quiescent")
        # AND THE IDENTITY IS UNCHANGED. The attachment is settled once; only
        # the state moves.
        self.assertEqual(self.attempt_row()["runtime_id"], runtime_id)

    def test_a_second_reconciliation_re_reads_the_state(self):
        """The attachment is effectively-once; the OBSERVATION is not.

        MEASURED, and it changed the design. Recording the state inside the
        attachment's transaction -- where the axis move used to live, for a
        good reason while attachment implied `running` -- meant the second
        reconciliation REPLAYED the first answer without running the action,
        so a container that exited afterwards stayed `running` forever. The
        defect survived inside the fix for it until this case caught it.
        """
        adapter, _roots, inputs = self.prepared()
        # THE OBSERVATION IS SCRIPTED AND THE REST IS REAL. The reference
        # worker now exits in milliseconds -- W26291 gave it its launch
        # environment, so it starts, finds no frames and shuts down -- which
        # makes "still running at the first reconciliation" a race this case
        # would lose more often than not. What is under test is that the
        # SECOND pass re-reads rather than replaying the first answer, and
        # that is a fact about the manager, so the adapter's answer is the
        # thing to control. The container, the engine and the listing are
        # still real.
        answers = ["running", "quiescent"]
        real = adapter.observe
        adapter.observe = lambda runtime_id: {
            "state": answers.pop(0) if answers else "quiescent",
            "why": "scripted", "mounts": None}
        try:
            request_runtime_start(self.store, adapter,
                                  attempt_id=self.attempt, inputs=inputs)
            self.assertEqual(self.attempt_row()["execution_runtime"],
                             "running")
            again = reconcile_runtime(self.store, adapter,
                                      attempt_id=self.attempt)
        finally:
            adapter.observe = real
        self.assertEqual(again["observed"], "quiescent", again)
        self.assertEqual(self.attempt_row()["execution_runtime"], "quiescent")

    def test_an_observation_the_adapter_cannot_make_is_never_running(self):
        """FAIL CLOSED. A failed observation, an unknown engine state and a
        malformed answer are all reasons to say `uncertain` and none is a
        reason to say running.

        Driven at the real adapter by replacing its `observe` -- the engine
        cannot be made to answer nonsense on demand, and what is under test is
        the manager's reading of an answer rather than the daemon's phrasing.
        """
        adapter, _roots, inputs = self.prepared()
        request_runtime_start(self.store, adapter, attempt_id=self.attempt,
                              inputs=inputs)
        runtime_id = self.attempt_row()["runtime_id"]
        # W26294 review [P0]: THE ASSERTIONS WERE INVERTED. This required a
        # propagated refusal and then checked only that the row was not
        # `quiescent` -- which stale `running` satisfies, so the case admitted
        # exactly the outcome its own prose forbids. Every failed or
        # unrecognised observation is now a durable `uncertain`, and that is
        # what is asserted.
        for answer, why in (
                ({"state": "confused", "why": "n/a"}, "an unknown state"),
                ({"why": "no state at all"}, "a missing member"),
                ("not a document", "not a document")):
            with self.subTest(why=why):
                adapter.observe = lambda _id, answer=answer: answer
                decided = reconcile_runtime(self.store, adapter,
                                            attempt_id=self.attempt)
                self.assertEqual(decided["observed"], "uncertain", decided)
                row = self.attempt_row()
                self.assertEqual(row["execution_runtime"], "uncertain")
                self.assertNotEqual(row["execution_runtime"], "running")
                self.assertEqual(row["runtime_id"], runtime_id)
        # A raising observation is inconclusive too, and never a running one.
        adapter.observe = lambda _id: (_ for _ in ()).throw(
            ContractRefusal("unavailable", "transport", "the daemon is gone"))
        decided = reconcile_runtime(self.store, adapter,
                                    attempt_id=self.attempt)
        self.assertEqual(decided["observed"], "uncertain", decided)
        self.assertEqual(self.attempt_row()["execution_runtime"], "uncertain")
        self.assertEqual(self.attempt_row()["runtime_id"], runtime_id)

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
