"""W26284 — credential delivery, against a REAL engine.

`work/records/2026/08/finding-v12-oci-fresh-run-credentials/`.

The acceptance says *"Tests prove secrets are absent from argv, environment,
labels, durable documents, diagnostics, and output"* and asks for real-engine
coverage of delivery and cleanup. `test_credentials.py` proves the manager's
half against a fake engine, which is the right way to cover the refusal paths
and is not the same claim: it asks what this manager COMPOSED, and this asks
what the daemon actually HOLDS.

The difference matters for exactly one reason. Everything the manager builds
passes through its own §13 sweep before it leaves; what the engine ends up
storing about a container — its argv, its environment, its labels, its mount
table — is the daemon's record, and a bearer that reached it is a bearer in a
place no sweep of this manager's documents will ever look.

IT FAILS RATHER THAN SKIPS WITHOUT A DAEMON, inheriting `ContainerCase`, for
the reason W6633's gate gives.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile

from baton_v12.contracts import (ContractRefusal, forget_secret,
                                 live_secret)
from baton_v12.worker_manager import (credentials, launch, oci,
                                      workspaces)

from baton_v12.worker_manager import ControlStore

from . import input_roots
from .test_worker_container import ENGINE, ContainerCase

BEARER = "w26284-live-bearer-value-that-must-not-escape"
PROFILE = {"api": {"provider": "vault", "reference": "kv/one"}}
IDENTITY = {"image_digest": None,  # filled from the built image per case
            "profile_digest": "sha256:" + "c" * 64,
            "policy_digest": "sha256:" + "d" * 64,
            "adapter_digest": "sha256:" + "e" * 64}
LABELS = {"runtime_attempt_id": "attempt-1",
          "authority_uuid": "0123456789abcdef0123456789abcdef",
          "work_id": "01234567-W1", "participant": "baton.claude",
          "generation": 1,
          # W16823: the principal and effective scope the claim was authorized
          # for, beside the four-part fence.
          "principal": "principal:org-a",
          "effective_scope": "scope:deployment",
          "profile_digest": IDENTITY["profile_digest"],
          "policy_digest": IDENTITY["policy_digest"],
          "adapter_digest": IDENTITY["adapter_digest"]}


class ARealDaemonNeverHoldsTheBearer(ContainerCase):

    def setUp(self):
        self.home_place = tempfile.mkdtemp(prefix="v12-w26284-engine-")
        self.addCleanup(self._release)
        self.inputs = os.path.join(self.home_place, "inputs")
        self.workspace = os.path.join(self.home_place, "workspace")
        self.store = ControlStore.open(
            os.path.join(self.home_place, "control.sqlite3"),
            incarnation="cred-engine-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.group = input_roots.configured_group(self.store)
        for place in (self.inputs, self.workspace):
            os.makedirs(place)
        # W33936: the workspace root carries the configured group at exactly
        # the mode an execution start proves before the engine.
        os.chown(self.workspace, -1, self.group.gid)
        os.chmod(self.workspace, workspaces.WORKSPACE_DIR)
        self.made = []
        self.spawned = []
        self.addCleanup(self._reap)
        # NOTHING LEAKS INTO THE PROCESS REGISTRY. A live value left behind
        # would arm every later case's §13 walk against a string this one
        # invented.
        self.addCleanup(self._quiet)
        self.digest = json.loads(subprocess.run(
            [ENGINE, "image", "inspect", self.image],
            capture_output=True, timeout=120).stdout.decode("utf-8"))[0]["Id"]

    def _release(self):
        """Take the tree away, and PROVE it is gone.

        Review [P2]: this changed modes and then stopped, so every case left a
        `v12-w26284-engine-*` tree behind while the suite's own docstring
        claimed cleanup. A cleanup that only widens permissions is a cleanup
        that did nothing — and this suite is about proving absence, so leaving
        its own resources behind is the exact shape it exists to refuse.
        """
        for base, directories, files in os.walk(self.home_place,
                                                topdown=False):
            for one in directories:
                os.chmod(os.path.join(base, one), 0o700)
            for one in files:
                full = os.path.join(base, one)
                if not os.path.islink(full):
                    os.chmod(full, 0o600)
        os.chmod(self.home_place, 0o700)
        for base, directories, files in os.walk(self.home_place,
                                                topdown=False):
            for one in files:
                os.remove(os.path.join(base, one))
            for one in directories:
                os.rmdir(os.path.join(base, one))
        os.rmdir(self.home_place)
        assert not os.path.lexists(self.home_place), self.home_place

    def _quiet(self):
        while live_secret(BEARER):
            forget_secret(BEARER)

    def _reap(self):
        for name in self.made:
            subprocess.run([ENGINE, "rm", "--force", name],
                           capture_output=True, timeout=120)

    def spawn(self, argv):
        for index, value in enumerate(argv):
            if value == "--name" and index + 1 < len(argv):
                self.made.append(argv[index + 1])
        self.argv = list(argv)
        self.spawned.append(list(argv))
        finished = subprocess.run(argv, capture_output=True, timeout=300)
        return {"status": finished.returncode,
                "stdout": finished.stdout.decode("utf-8", "replace"),
                "stderr": finished.stderr.decode("utf-8", "replace")}

    def delivered(self):
        home = credentials.CredentialHome(self.home_place)
        return home, home.materialize(
            credentials.resolved_delivery(("api",), profile=PROFILE),
            attempt_id="attempt-1",
            credential_provider=lambda provider, reference: BEARER)

    def started(self, delivery):
        built = oci.OciAdapter(
            ENGINE, oci.EnginePort(self.spawn),
            identity=dict(IDENTITY, image_digest=self.digest),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group,
            credential_delivery=delivery,
            launch_delivery=self.launched())
        return built, built.start({"labels": dict(LABELS),
                                   "operation_id": "runtime.start:w26284"})

    def launched(self, attempt_id="attempt-1"):
        """One materialized launch document per start. W26291 re-review [P1]:
        the canonical start requires one, and a settled delivery is
        discarded."""
        home = tempfile.mkdtemp(prefix="v12-w26284-launch-")
        self.addCleanup(self.take_launch_away, home)
        return launch.materialize(home, attempt_id=attempt_id,
                                  session="session-1",
                                  contract="do the thing",
                                  role="implementer")

    def take_launch_away(self, home):
        for current, directories, files in os.walk(home, topdown=False):
            os.chmod(current, 0o700)
            for name in files:
                os.remove(os.path.join(current, name))
            for name in directories:
                os.rmdir(os.path.join(current, name))
        if os.path.lexists(home):
            os.rmdir(home)

    def inspected(self, runtime_id):
        found = subprocess.run([ENGINE, "container", "inspect", runtime_id],
                               capture_output=True, timeout=120)
        self.assertEqual(found.returncode, 0,
                         found.stderr.decode("utf-8", "replace"))
        return json.loads(found.stdout.decode("utf-8"))[0]

    # -- the acceptance's leak clause, asked of the daemon --------------------

    def test_the_daemon_holds_no_bearer_anywhere_it_records(self):
        """Argv, environment, labels and the mount table, from `inspect`.

        Every one of these is a place the DAEMON stores, not a document this
        manager composed — so a §13 sweep of the manager's own output cannot
        answer for any of them.
        """
        _home, delivery = self.delivered()
        _built, started = self.started(delivery)
        held = self.inspected(started["runtime_id"])

        # THE WHOLE RECORD, searched as text. Naming the four members and
        # checking each would pass for a bearer the daemon stored somewhere
        # this case did not think to look.
        self.assertNotIn(BEARER, json.dumps(held))
        # ...and the four the acceptance names, individually, so a failure
        # says WHICH.
        self.assertNotIn(BEARER, json.dumps(held["Args"]))
        self.assertNotIn(BEARER, json.dumps(held["Config"]["Env"] or []))
        self.assertNotIn(BEARER, json.dumps(held["Config"]["Labels"] or {}))
        self.assertNotIn(BEARER, json.dumps(held["Mounts"]))
        # And the argv this manager actually executed.
        self.assertNotIn(BEARER, " ".join(self.argv))

    def test_a_bearer_in_a_label_never_reaches_the_daemon_at_all(self):
        """The leak assertions above must be FALSIFIABLE, or they pass for a
        manager with no sweep at all.

        Nothing in the ordinary path puts a bearer where the daemon could
        store it -- the credential is a file, not an argument -- so asserting
        its absence proves only that the ordinary path is ordinary. A
        caller-supplied LABEL is the one member that would be spelled into the
        command line, which is how `test_no_bearer_reaches_the_argv` makes the
        §13 walk reachable. This does the same and then asks the daemon
        whether anything was created.
        """
        _home, delivery = self.delivered()
        built = oci.OciAdapter(
            ENGINE, oci.EnginePort(self.spawn),
            identity=dict(IDENTITY, image_digest=self.digest),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group,
            credential_delivery=delivery,
            launch_delivery=self.launched())
        self.spawned = []
        with self.assertRaises(ContractRefusal) as caught:
            built.start({"labels": dict(LABELS, participant=BEARER),
                         "operation_id": "runtime.start:w26284-leak"})
        # `policy/denied` rather than `integrity/secret-leak`: `start` owns
        # its own lifecycle refusal and reports one, and the §13 walk's
        # message rides inside it. Asserted as observed rather than as
        # expected -- the pairing is the adapter's to choose, and this case is
        # about what reached the daemon.
        self.assertEqual(caught.exception.category, "policy")
        self.assertEqual(caught.exception.code, "denied")
        # REFUSED BEFORE THE ENGINE WAS ASKED TO CREATE ANYTHING. A refusal
        # after the run would be a bearer already in the daemon's record.
        #
        # `start` DOES reach the engine first, for its duplicate probe, so the
        # assertion is that no `run` was issued rather than that nothing was.
        # Checked: that probe's argv does not carry the bearer either, because
        # `participant` is not one of the candidate label filters -- verified
        # rather than assumed, and asserted here so it stays true.
        # TWO `ps` calls, and both belong: the duplicate probe before the
        # vector is composed, and `_refused_start`'s own listing, which asks
        # the engine what exists after a refusal so the lifecycle is settled
        # rather than assumed. Neither is a `run`.
        self.assertEqual(sorted({one[1] for one in self.spawned}), ["ps"])
        self.assertTrue(self.spawned, "the engine was never reached at all")
        for argv in self.spawned:
            self.assertNotIn(BEARER, " ".join(argv))
        found = subprocess.run(
            [ENGINE, "ps", "--all", "--filter",
             f"label=baton.v12.participant={BEARER}", "--format",
             "{{.Names}}"], capture_output=True, timeout=120)
        self.assertEqual(found.stdout.decode("utf-8").split(), [])

    def test_the_credential_is_mounted_read_only_at_the_fixed_path(self):
        """The daemon's own mount table, not the plan this manager composed."""
        _home, delivery = self.delivered()
        _built, started = self.started(delivery)
        held = self.inspected(started["runtime_id"])
        binds = {one["Destination"]: one for one in held["Mounts"]}
        target = f"{credentials.CREDENTIAL_ROOT}/api"
        self.assertIn(target, binds, sorted(binds))
        self.assertFalse(binds[target]["RW"], "the credential is writable")
        self.assertEqual(os.path.realpath(binds[target]["Source"]),
                         os.path.realpath(os.path.join(delivery.root, "api")))

    def test_the_bearer_stays_live_while_the_container_exists(self):
        """The registry is armed THROUGH the container's life.

        The finding says the registry remains armed through quiescence, output
        scanning, removal and root deletion, and forgets only after positive
        absence. This is the first half, over a container that really exists.
        """
        _home, delivery = self.delivered()
        _built, started = self.started(delivery)
        self.assertTrue(live_secret(BEARER))
        self.assertEqual(self.inspected(started["runtime_id"])["Id"],
                         started["runtime_id"])

    def test_teardown_forgets_only_after_the_bytes_are_proved_gone(self):
        """Cleanup, over a real delivery, in the ruled order — and over a
        delivery THIS PROVIDER'S SCOPE actually covers.

        Review [P1 test gap]: this case used to start a real container and
        then call `tear_down` directly, without removing the container or
        establishing positive runtime absence. Removing a host pathname is not
        proof that a bind-mounted runtime cannot still hold the inode, so what
        it demonstrated was not the lifecycle ordering it claimed.

        The review offered two ways out and the finding chooses between them:
        the shared quiescence/removal/settlement crossing is EXPLICITLY
        outside this provider, so this suite stays inside fresh-run delivery
        and failure. The delivery here therefore never launches a runtime,
        which is a real ending this provider owns — and the ordering it proves
        is the one it can: the bytes are gone before the registry is released.

        The post-runtime crossing is W6636's, and
        `test_a_delivery_that_launched_nothing_settles_through_the_adapter`
        below is as far into it as this provider reaches.
        """
        home, delivery = self.delivered()
        place = os.path.join(delivery.root, "api")
        self.assertTrue(os.path.isfile(place))
        self.assertTrue(live_secret(BEARER))
        answered = home.tear_down(delivery)
        self.assertEqual(answered["lifecycle_state"], "torn-down")
        self.assertFalse(os.path.lexists(place))
        self.assertFalse(os.path.lexists(delivery.root))
        self.assertFalse(live_secret(BEARER))

    def test_a_delivery_that_launched_nothing_settles_through_the_adapter(
            self):
        """The one runtime-absence question this provider owns, asked of a
        REAL daemon.

        A start the engine never completed leaves a volatile root and a live
        registration that the single destroy path cannot reach, because there
        is no runtime id to name them by. So the adapter asks: if no runtime
        carries this attempt's labels, none can be holding the mount, and the
        delivery settles. That is a real `ps` against a real daemon, and it is
        this provider's boundary rather than W6636's crossing — nothing here
        stops, removes or reconciles a container, because no container exists.
        """
        _home, delivery = self.delivered()
        built = oci.OciAdapter(
            ENGINE, oci.EnginePort(self.spawn),
            # A digest no image has: the engine refuses the run, so the start
            # fails AFTER the duplicate probe and BEFORE anything exists.
            identity=dict(IDENTITY, image_digest="sha256:" + "0" * 64),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group,
            credential_delivery=delivery,
            launch_delivery=self.launched())
        with self.assertRaises(ContractRefusal) as caught:
            built.start({"labels": dict(LABELS),
                         "operation_id": "runtime.start:w26284-absent"})
        # THE ENDING NAMES THE CREDENTIAL, which is the whole point of routing
        # every refusing exit through the settlement.
        self.assertEqual(caught.exception.category, "policy")
        self.assertIn("credential delivery is", caught.exception.message)
        # W26291 re-review [P1]: and the launch document is settled beside it,
        # on the same absence evidence — two manager-owned mounts, two named
        # endings, one listing.
        self.assertIn("launch document is torn-down", caught.exception.message)
        # AND THE DAEMON WAS ASKED. The settlement is a real listing, not an
        # assumption that a failed start created nothing.
        self.assertTrue(any("ps" in argv for argv in self.spawned),
                        "the engine was never asked what exists")
        self.assertFalse(os.path.lexists(delivery.root))
        self.assertFalse(live_secret(BEARER))

    def test_nothing_this_module_made_survives_it(self):
        found = subprocess.run(
            [ENGINE, "ps", "--all", "--filter", "name=baton-runtime.start",
             "--format", "{{.Names}}"], capture_output=True, timeout=120)
        self.assertEqual(found.returncode, 0,
                         found.stderr.decode("utf-8", "replace"))
        self.assertEqual(found.stdout.decode("utf-8").split(), [])
