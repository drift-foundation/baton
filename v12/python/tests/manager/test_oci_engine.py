"""W6632 — the OCI adapter core against a REAL engine.

`work/records/2026/08/finding-v12-oci-adapter-core/`.

`test_oci.py` proves the argv this adapter composes and the answers it makes of
a fake engine. Neither can tell you that a real daemon accepts the vector: a
flag one engine spells differently, a restriction a kernel refuses, a mount the
daemon rejects and a name no engine will take all pass an argv assertion and
fail at the socket. Those are facts about somebody else's daemon and the only
way to have them is to run it.

SKIPPED WHEN THE ENGINE IS ABSENT, and this is deliberately the opposite policy
from W6633's image gate. That one builds THIS repository's own artefact and a
missing daemon is a failed prerequisite for it. This one exercises a THIRD
PARTY's runtime — Docker and Podman, two engines the adapter claims to speak —
and a developer machine with one of them is the ordinary case. A required gate
that cannot run without both would be a gate people learn to ignore.

The skip is per engine and it is NARROW: it fires only when the binary is
absent or its daemon cannot be reached. Anything the engine actually answers is
a result, never a reason to stop.

EVERY CONTAINER IS REGISTERED FOR REMOVAL THE INSTANT IT CAN EXIST, and a final
case asks the engine — rather than a bookkeeping list — whether anything this
module made survived it.
"""

import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import unittest
import uuid
from unittest import mock

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager.oci import (ENGINES, LABEL_PREFIX, EnginePort,
                                          OciAdapter, ROOT_NAMES)

# The pinned base the reference worker is built from, already named by digest
# in `v12/worker/Dockerfile`. Reused rather than re-resolved so this module and
# that recipe cannot drift into two opinions about which image they mean.
WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
# THE MARK IS A LABEL AND NEVER A NAME, and the distinction is the whole of
# review [P1]'s second half. A runtime's NAME is derived from the manager's
# `runtime.start:<digest>` operation identity, so nothing this module creates
# is named for this Work -- and a cleanup proof that filtered on the name
# selected none of them. Every created runtime does carry this Work's label,
# so the label namespace is the selector, and `WORK` is the exact value the
# final query asks for.
MARK = "baton-w6632-engine"
WORK = "2b077949-W6632"

LABELS = {"runtime_attempt_id": "attempt-w6632",
          "authority_uuid": "2b077949c86e8bef24304f59c28ec398",
          "work_id": WORK, "participant": "baton.claude",
          "generation": 1,
          "profile_digest": "sha256:" + "b" * 64,
          "policy_digest": "sha256:" + "d" * 64,
          "adapter_digest": "sha256:" + "c" * 64}


def pinned_base():
    """The `FROM ...@sha256:...` reference the worker recipe pins."""
    recipe = (WORKER / "Dockerfile").read_text(encoding="utf-8")
    for line in recipe.splitlines():
        if line.startswith("FROM "):
            return line[len("FROM "):].strip()
    raise AssertionError("the worker recipe names no base image")


def reachable(engine):
    """`(usable, why)` for one engine, deciding ONLY availability."""
    if shutil.which(engine) is None:
        return False, f"{engine} is not on PATH"
    found = subprocess.run([engine, "version", "--format", "{{.Server.Version}}"],
                           capture_output=True, timeout=60)
    if found.returncode != 0:
        return False, (f"{engine} is installed and its daemon is not "
                       f"reachable: "
                       f"{found.stderr.decode('utf-8', 'replace')[:200]}")
    return True, found.stdout.decode("utf-8").strip()


class EngineCycle:
    """One real engine, one resolved image, and nothing left behind.

    A MIXIN rather than a base `TestCase`, so unittest collects the two
    concrete engines and not an abstract class with no engine to run against —
    which would report five errors that say nothing about either daemon.
    """

    engine = None

    def setUp(self):
        usable, why = reachable(self.engine)
        if not usable:
            self.skipTest(why)
        self.server = why
        self.made = []
        self.addCleanup(self.remove_everything)
        self.port = EnginePort(self.spawn)
        self.image = self.resolved_image()
        self.root = tempfile.TemporaryDirectory(prefix="v12-oci-engine-")
        self.addCleanup(self.root.cleanup)
        self.roots = {name: os.path.join(self.root.name, name)
                      for name in ROOT_NAMES}
        for place in self.roots.values():
            os.mkdir(place)

    # -- the one thing this suite does to the world --------------------------

    def spawn(self, argv):
        """The engine port's run operation, over a real process."""
        finished = subprocess.run(argv, capture_output=True, timeout=300)
        return {"status": finished.returncode,
                "stdout": finished.stdout.decode("utf-8", "replace"),
                "stderr": finished.stderr.decode("utf-8", "replace")}

    def remove_everything(self):
        """Remove what this case made, and SURFACE a removal that did not.

        Review [P1]: the return code was discarded here as well as in the
        final proof, so a removal the daemon refused was indistinguishable
        from one it performed. A cleanup that cannot fail is a cleanup whose
        success is an assumption.

        A refused `rm` is not by itself a failure: a name is registered the
        instant it CAN exist, so some were never created and the engine
        rightly says so. What makes it a failure is the container still being
        there afterwards, which is a question for the engine rather than for
        its prose.
        """
        survived = []
        for name in self.made:
            removed = subprocess.run([self.engine, "rm", "--force", name],
                                     capture_output=True, timeout=120)
            if removed.returncode == 0:
                continue
            found = subprocess.run(
                [self.engine, "ps", "--all", "--filter", f"name={name}",
                 "--format", "{{.Names}}"],
                capture_output=True, timeout=120)
            if found.returncode != 0 or found.stdout.decode(
                    "utf-8", "replace").strip():
                survived.append(
                    (name, removed.stderr.decode("utf-8", "replace")[:200]))
        assert not survived, (
            f"{self.engine} did not remove {survived}")

    def resolved_image(self):
        """The pinned base, PULLED and then named by its local image id.

        The adapter names an image by `sha256:` digest and hands that to the
        engine as the last argument, so the reference has to be one the engine
        can run locally — which is the image ID, not the registry manifest
        digest the recipe pins.
        """
        base = pinned_base()
        found = subprocess.run([self.engine, "image", "inspect", base,
                                "--format", "{{.Id}}"],
                               capture_output=True, timeout=120)
        if found.returncode != 0:
            # PULLED ONLY WHEN IT IS ABSENT. A test module that mutates the
            # shared image store decides other modules' outcomes: pulling
            # unconditionally changed what W6633's build gate resolved between
            # its two builds, and two suites disagreeing about an artefact
            # because one of them fetched something is not a result about
            # either. Observed in a full run and corrected here rather than
            # explained afterwards.
            pulled = subprocess.run([self.engine, "pull", base],
                                    capture_output=True, timeout=900)
            if pulled.returncode != 0:
                self.skipTest(
                    f"{self.engine} cannot pull the pinned base: "
                    f"{pulled.stderr.decode('utf-8', 'replace')[:200]}")
            found = subprocess.run([self.engine, "image", "inspect", base,
                                    "--format", "{{.Id}}"],
                                   capture_output=True, timeout=120)
        self.assertEqual(found.returncode, 0,
                         found.stderr.decode("utf-8", "replace")[:400])
        return found.stdout.decode("utf-8").strip()

    def identity(self):
        return {"image_digest": self.image,
                "profile_digest": LABELS["profile_digest"],
                "policy_digest": LABELS["policy_digest"],
                "adapter_digest": LABELS["adapter_digest"]}

    def adapter(self, mounts=()):
        return OciAdapter(self.engine, self.port, identity=self.identity(),
                          assignment_roots=dict(self.roots),
                          posture="execution", mounts=mounts)

    def labels(self, **overrides):
        return dict(LABELS, runtime_attempt_id=f"{MARK}-{uuid.uuid4().hex[:8]}",
                    **overrides)

    def started(self, adapter, labels):
        """Start one runtime and register it for removal by NAME first.

        Registered before the start rather than after, so a start that creates
        a container and then fails on its way back still has it removed.
        """
        operation_id = f"runtime.start:{uuid.uuid4().hex[:12]}"
        self.made.append("baton-" + operation_id.replace(":", "-"))
        return adapter.start({"labels": labels, "operation_id": operation_id})

    # -- the cycle -----------------------------------------------------------

    def test_a_runtime_starts_is_found_stops_and_is_destroyed(self):
        """The positive cycle, end to end, against the real daemon.

        Every step is what the MANAGER would do: start under one resolved
        identity, find it again by its reconciliation labels, stop it and prove
        what became of it, then destroy it and prove absence.
        """
        adapter = self.adapter()
        labels = self.labels()
        answer = self.started(adapter, labels)
        self.assertIsNotNone(answer["runtime_id"],
                             "the engine started something it would not name")

        found = adapter.list({"labels": labels})
        self.assertEqual([entry["runtime_id"] for entry in found],
                         [answer["runtime_id"]],
                         "reconciliation could not find what it started")
        self.assertEqual(found[0]["labels"]["profile_digest"],
                         adapter.identity["profile_digest"])

        settled = adapter.stop({"runtime_id": answer["runtime_id"],
                                "operation_id": "runtime.stop:1"})
        self.assertTrue(settled["ordered"])
        self.assertIn(settled["state"], ("quiescent", "absent"), settled)

        # W6629 review [P1]: the seam receives `runtimeDestroyBody` now, so
        # the manager's authorization travels with the command instead of
        # stopping at the boundary. Against a REAL engine the only member that
        # changes behaviour is still the identity; the rest is carried.
        gone = adapter.destroy({
            "assignment_ref": {
                "work_ref": {"authority_uuid": "u" * 32,
                             "work_id": "u" * 32 + "-W1"},
                "participant": "baton.claude", "generation": 1},
            "runtime_attempt_id": "attempt-1",
            "runtime_id": answer["runtime_id"],
            "intake_receipt_digest": "sha256:" + "6" * 64,
            "retention_policy_digest": "sha256:" + "7" * 64})
        self.assertEqual(gone["state"], "absent", gone)

    def test_a_second_start_under_one_identity_is_refused(self):
        """The duplicate the manager can never undo, refused by asking the
        engine what already carries these labels."""
        adapter = self.adapter()
        labels = self.labels()
        self.started(adapter, labels)
        with self.assertRaises(ContractRefusal) as caught:
            self.started(adapter, labels)
        self.assertIn("already carry these assignment labels",
                      caught.exception.message)

    def test_the_engine_applied_the_restrictions_the_adapter_asked_for(self):
        """The vector is accepted AND the posture is what was asked for, read
        back from the engine's own record rather than from the argv."""
        adapter = self.adapter()
        answer = self.started(adapter, self.labels())
        found = subprocess.run(
            [self.engine, "container", "inspect", answer["runtime_id"],
             "--format", "{{json .HostConfig}}"],
            capture_output=True, timeout=120)
        self.assertEqual(found.returncode, 0,
                         found.stderr.decode("utf-8", "replace")[:400])
        config = json.loads(found.stdout.decode("utf-8"))
        self.assertIs(config["ReadonlyRootfs"], True)
        self.assertIn("ALL", [name.upper()
                              for name in config.get("CapDrop") or ()])
        self.assertEqual(config.get("NetworkMode"), "none")
        self.assertEqual(config.get("PidsLimit"), 512)

    def test_a_workspace_mount_reaches_the_container(self):
        """A mount the adapter proved is one the engine accepts and resolves
        to the place this manager named."""
        tree = os.path.join(self.roots["workspace"], "tree")
        os.mkdir(tree)
        with open(os.path.join(tree, "witness"), "w", encoding="utf-8") as out:
            out.write("present")
        adapter = self.adapter(mounts=[{"source": tree,
                                        "target": "/workspace",
                                        "writable": True}])
        answer = self.started(adapter, self.labels())
        found = subprocess.run(
            [self.engine, "container", "inspect", answer["runtime_id"],
             "--format", "{{json .Mounts}}"],
            capture_output=True, timeout=120)
        mounts = json.loads(found.stdout.decode("utf-8"))
        landed = {entry["Destination"]: entry for entry in mounts}
        self.assertIn("/workspace", landed, mounts)
        self.assertEqual(os.path.realpath(landed["/workspace"]["Source"]),
                         os.path.realpath(tree))

    def test_an_absent_identity_is_absence_and_not_confusion(self):
        """The one answer that releases an assignment, asked of a real engine
        about an identity that never existed."""
        adapter = self.adapter()
        seen = adapter.observe("baton-w6632-no-such-runtime")
        self.assertEqual(seen["state"], "absent", seen)


class DockerRunsWhatTheAdapterComposes(EngineCycle, unittest.TestCase):
    engine = "docker"


class PodmanRunsWhatTheAdapterComposes(EngineCycle, unittest.TestCase):
    engine = "podman"


class TheEngineGateLeavesNothingBehind(unittest.TestCase):

    def test_cleanup_queries_the_label_namespace_the_tests_create(self):
        """The final proof must select the runtimes this module actually made.

        Runtime names are derived from `runtime.start:<digest>` and do not
        contain MARK.  Every runtime does carry this Work label, so that is the
        stable selector a positive cleanup query can use.
        """
        finished = subprocess.CompletedProcess([], 0, stdout=b"", stderr=b"")
        with mock.patch(__name__ + ".reachable", return_value=(True, "ok")):
            with mock.patch(__name__ + ".subprocess.run",
                            return_value=finished) as run:
                case = TheEngineGateLeavesNothingBehind(
                    "test_no_runtime_of_this_module_survives_it")
                case.test_no_runtime_of_this_module_survives_it()
        filters = [call.args[0][call.args[0].index("--filter") + 1]
                   for call in run.call_args_list]
        self.assertEqual(filters,
                         [f"label=baton.v12.work_id={LABELS['work_id']}"] *
                         len(ENGINES))

    def test_a_failed_cleanup_query_is_not_positive_absence(self):
        """Empty stdout from a refused engine query proves nothing."""
        refused = subprocess.CompletedProcess(
            [], 1, stdout=b"", stderr=b"daemon query failed")
        with mock.patch(__name__ + ".reachable", return_value=(True, "ok")):
            with mock.patch(__name__ + ".subprocess.run",
                            return_value=refused):
                case = TheEngineGateLeavesNothingBehind(
                    "test_no_runtime_of_this_module_survives_it")
                with self.assertRaises(AssertionError):
                    case.test_no_runtime_of_this_module_survives_it()

    def test_no_runtime_of_this_module_survives_it(self):
        """Asked of every engine that is present, and of the ENGINE rather
        than of a bookkeeping list.

        Review [P1], twice over. It filtered on `name=baton-w6632-engine`, and
        NO runtime this module creates carries that in its name: every name is
        derived from `runtime.start:<digest>`, so the query selected nothing
        this suite had ever made and reported an empty list whatever survived.
        MARK lives in a LABEL, and the label namespace is the one selector the
        created runtimes actually share.

        And the query's own return code was ignored, so a refused `ps` — a
        daemon that went away between the cycle and this proof — produced
        empty stdout and passed as absence. A query that did not run is not
        evidence that nothing is there.
        """
        asked = 0
        for engine in ENGINES:
            usable, _why = reachable(engine)
            if not usable:
                continue
            asked += 1
            found = subprocess.run(
                [engine, "ps", "--all",
                 "--filter", f"label={LABEL_PREFIX}work_id={WORK}",
                 "--format", "{{.Names}}"],
                capture_output=True, timeout=120)
            self.assertEqual(
                found.returncode, 0,
                f"{engine} could not be asked what this module left: "
                f"{found.stderr.decode('utf-8', 'replace')[:200]}")
            left = [line.strip()
                    for line in found.stdout.decode("utf-8").splitlines()
                    if line.strip()]
            self.assertEqual(left, [], f"{engine} still holds {left}")
        if not asked:
            self.skipTest("neither engine is reachable")

    def test_both_engines_this_adapter_claims_are_covered(self):
        """The claim and the coverage are the same list. An engine added to
        `ENGINES` without a case here would be an engine this adapter says it
        speaks and nobody ever ran."""
        covered = {case.engine for case in
                   (DockerRunsWhatTheAdapterComposes,
                    PodmanRunsWhatTheAdapterComposes)}
        self.assertEqual(covered, set(ENGINES))


if __name__ == "__main__":
    unittest.main()
