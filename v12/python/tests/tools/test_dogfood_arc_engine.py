"""W39358 — the whole arc, against a REAL engine and the REAL dogfood image.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/
finding-minimal-supervised-operator/`.

THE ACCEPTANCE SENTENCE THIS ANSWERS: *a real Docker dry run reaches the
worker entrypoint without relying on the spike lifecycle.*

WHAT ONLY A DAEMON SUPPLIES. Every other case for this operator supplies the
engine, the channel and the image. This one supplies none of them: the image
is built from W39357's recipe, the adapter is the real `OciAdapter` over a
real `EnginePort`, the channel is the launcher's own `docker exec` pipe, and
the container the transport talks to is one the manager's own operations
started. Composition cases prove the arc is written correctly; this proves it
RUNS.

WHAT IT DELIBERATELY DOES NOT DO. It makes no provider call and mounts no
credential: live provider authorization is W39364's operator gate, and every
container here runs `--network none`. So the worker entrypoint starts, the
Claude agent inside it has no authorization, and the conversation ends without
a usable result -- which is exactly the DRY RUN the acceptance names. The
attempt is then ended through W44716's public abandonment, and the daemon is
asked separately whether the container is gone.

Approver ruling M46497 is what this reflects rather than freezes: an exact
same-attempt rerun REFUSES before another runtime or provider turn, and retry
uses a fresh attempt identity. The rerun case below asserts that refusal
rather than a resumption.

IT FAILS RATHER THAN SKIPS WITHOUT DOCKER, inheriting the rule every engine
gate in this campaign is under.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "tools"))

import dogfood_operator                                    # noqa: E402
from dogfood_operator import OperatorRefusal               # noqa: E402

WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
MARK = "baton-w39358-arc"
ENGINE = "docker"
NOW = "2026-08-30T00:00:00.000Z"
WORK_REF = {"authority_uuid": "43c55d4b1234567890abcdef12345678",
            "work_id": "43c55d4b-W1439"}
PROFILE = "sha256:" + "6" * 64
ROLE = "sha256:" + "2" * 64
TOOLCHAIN = "sha256:" + "4" * 64
ADAPTER = "sha256:" + "5" * 64
POLICIES = {one: "sha256:" + f"{index}" * 64
            for index, one in enumerate(dogfood_operator.POLICY_DIGESTS,
                                        start=1)}
POLICY = POLICIES["policy_digest"]
BINDING = {"root": "baton-repository",
           "path": "work/records/2026/08/finding-v12-first-useful-dogfood-task",
           "finding_digest": "sha256:" + "d" * 64,
           "plan_digest": "sha256:" + "e" * 64}
HUMAN = {"artifact_id": "human-contract-1", "media_type": "text/markdown",
         "bytes": 1200, "content_digest": "sha256:" + "b" * 64,
         "locator": "artifact://contracts/human-contract-1"}


def reachable(engine):
    if shutil.which(engine) is None:
        return False, f"{engine} is not on PATH"
    found = subprocess.run([engine, "version", "--format",
                            "{{.Server.Version}}"],
                           capture_output=True, timeout=120)
    if found.returncode != 0:
        return False, (f"{engine} is installed and its daemon is not "
                       f"reachable: "
                       f"{found.stderr.decode('utf-8', 'replace')[:200]}")
    return True, found.stdout.decode("utf-8").strip()


class TheArcRunsAgainstARealDaemon(unittest.TestCase):
    """One built image, and the composed arc run over it for real."""

    @classmethod
    def setUpClass(cls):
        usable, why = reachable(ENGINE)
        if not usable:
            raise AssertionError(
                f"W39358's acceptance requires a real Docker dry run and "
                f"{why}. That is a failed prerequisite for a required gate, "
                f"not a reason to pass without running it.")
        cls.image = f"{MARK}:{uuid.uuid4().hex[:12]}"
        cls.addClassCleanup(
            lambda: subprocess.run(
                [ENGINE, "image", "rm", "--force", cls.image],
                capture_output=True, timeout=300))
        built = subprocess.run(
            [ENGINE, "build", "-f", str(WORKER / "Dockerfile.claude"),
             # W71917: THE CONTEXT IS `v12`, because the recipe now
             # copies the distribution's profile package beside the
             # worker modules and a context cannot reach above itself.
             "-t", cls.image, str(WORKER.parent)],
            capture_output=True, timeout=2400)
        # W71917: BOTH STREAMS, because the legacy builder writes its steps
        # AND its failures to STDOUT. Showing only stderr reported a build
        # failure as the daemon's `DEPRECATED: The legacy builder...` banner
        # and nothing else, which named neither the step that failed nor why --
        # a diagnostic that turns a real failure into an unreadable one.
        assert built.returncode == 0, (
            f"the dogfood image did not build (exit {built.returncode})\n"
            f"stdout: {built.stdout.decode('utf-8', 'replace')[-3000:]}\n"
            f"stderr: {built.stderr.decode('utf-8', 'replace')[-2000:]}")
        found = subprocess.run(
            [ENGINE, "image", "inspect", cls.image, "--format", "{{.Id}}"],
            capture_output=True, timeout=120)
        assert found.returncode == 0, found.stderr.decode("utf-8", "replace")
        resolved = found.stdout.decode("utf-8").strip()
        cls.image_digest = (resolved if resolved.startswith("sha256:")
                            else f"sha256:{resolved}")


    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w39358-arc-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.made = []
        self.addCleanup(self.remove_everything)
        for name in ("storage", "launch", "source"):
            os.makedirs(os.path.join(self.home, name))
        with open(os.path.join(self.home, "source", "harness.py"), "w",
                  encoding="utf-8") as writing:
            writing.write("print('the staged harness')\n")
        self.task_path = os.path.join(self.home, "task.json")
        with open(self.task_path, "w", encoding="utf-8") as writing:
            # W71917 moved the workload contract to `/2`. This staged tree is
            # an ordinary directory read in place, so the profile is `generic`
            # and no base is declared.
            json.dump({"schema": "baton.dogfood-task/2",
                       "task_id": "w39358-real-docker-dry-run",
                       "instructions": "This dry run authorizes no provider.",
                       "verification": ["python3", "harness.py"],
                       "source_root": "source",
                       "source_profile": "generic",
                       "declared_base": None}, writing)

    def remove_everything(self):
        """Remove what this case made, and SURFACE one that survived."""
        survived = []
        for name in self.made:
            removed = subprocess.run([ENGINE, "rm", "--force", name],
                                     capture_output=True, timeout=120)
            found = subprocess.run(
                [ENGINE, "ps", "--all", "--filter", f"name={name}",
                 "--format", "{{.Names}}"], capture_output=True, timeout=120)
            if removed.returncode != 0 and (
                    found.returncode != 0
                    or found.stdout.decode("utf-8", "replace").strip()):
                survived.append(name)
        assert not survived, f"{ENGINE} did not remove {survived}"

    # -- the deployment's own half, real ------------------------------------

    def spawn(self, argv):
        """The engine port's run operation, registering every container name
        for removal BEFORE the process runs -- so a start that creates one and
        then fails on its way back still has it cleaned up."""
        for index, value in enumerate(argv):
            if value == "--name" and index + 1 < len(argv):
                self.made.append(argv[index + 1])
        return dogfood_operator._engine_run(argv)

    def adapter_of(self, group, **operands):
        from baton_v12.worker_manager.oci import EnginePort, OciAdapter

        roots = operands["roots"]
        return OciAdapter(
            ENGINE, EnginePort(self.spawn),
            identity={"image_digest": self.image_digest,
                      "profile_digest": PROFILE, "policy_digest": POLICY,
                      "adapter_digest": ADAPTER},
            assignment_roots=dict(roots), posture="execution",
            mounts=[{"source": roots["inputs"], "target": "/input",
                     "writable": False},
                    {"source": roots["workspace"], "target": "/output",
                     "writable": True}],
            workspace_group=group,
            launch_delivery=operands["launch"],
            network=operands["network"],
            interactive=True)

    def arc(self, attempt_id, *, seconds=90):
        from baton_v12.worker_manager import AuthorityPort, ControlStore
        from baton_v12.authority import claim_signature
        from tests.manager.input_roots import configured_group
        from tests.tools.test_dogfood_operator import ArcSession

        store = ControlStore.open(
            os.path.join(self.home, "control.sqlite3"),
            incarnation="arc-engine-1", clock=lambda: NOW)
        self.addCleanup(store.close)
        from baton_v12.worker_manager import certify_profile
        certify_profile(store, "runtime", "dogfood", PROFILE)
        group = configured_group(store)
        session = ArcSession()
        return dogfood_operator.run_dogfood_task(
            engine=ENGINE, run=self.spawn,
            open_channel=lambda argv, *, sec=None, seconds=None: (
                dogfood_operator._Channel(argv, seconds=seconds)),
            store=store, port=AuthorityPort(session, claim_signature),
            session=session, review_route="rview",
            adapter_of=lambda **operands: self.adapter_of(group, **operands),
            attempt_id=attempt_id, offer_id=f"offer-{attempt_id}",
            source=os.path.join(self.home, "source"),
            task_path=self.task_path,
            storage=os.path.join(self.home, "storage"),
            launch_home=os.path.join(self.home, "launch"),
            credential_delivery=None, image_digest=self.image_digest,
            network="none", work_ref=WORK_REF,
            participant="baton.claude", generation=1, now=NOW,
            policies=POLICIES, record_binding=BINDING,
            assignment_contract="v12-assignment-1", human_contract=HUMAN,
            role_instructions_digest=ROLE, runtime_profile_digest=PROFILE,
            toolchain_digest=TOOLCHAIN, adapter_digest=ADAPTER,
            adapter_name="oci", labels={"attempt": attempt_id},
            retention_policy_digest=POLICIES["retention_policy_digest"],
            # W51473 made retention an operator grant. This gate proves the
            # ordinary arc, whose established behaviour is the discard, so it
            # names the disposition it was always asking for.
            retention_disposition="discard-after-intake",
            bearer="one-use-bearer", seconds=seconds)

    def present(self, runtime_id):
        found = subprocess.run([ENGINE, "container", "inspect", runtime_id],
                               capture_output=True, timeout=120)
        return found.returncode == 0

    # -- the acceptance ------------------------------------------------------

    def test_a_real_dry_run_reaches_the_worker_entrypoint_and_ends(self):
        """THE ACCEPTANCE, in one case.

        The container is real, started by the manager's own operation over the
        image W39357's recipe builds. The worker entrypoint runs inside it and
        ANSWERS this deployment's transport -- `describe` needs no provider,
        so an answer to it is proof the program started and is speaking the
        protocol, which is the whole of what a dry run can honestly claim.

        No provider is authorized and no credential is mounted, so the work
        turn cannot produce a result. The attempt is therefore unresolved and
        ends through W44716's public abandonment -- and the daemon is asked
        separately whether the container is gone, because the adapter's own
        answer is under test and cannot also be the evidence for it.
        """
        attempt_id = f"attempt-{uuid.uuid4().hex[:10]}"

        evidence = self.arc(attempt_id)

        self.assertEqual(evidence["attempt_id"], attempt_id)
        self.assertIsNotNone(evidence["runtime_id"],
                             "no runtime was ever started")
        self.assertIsNotNone(evidence["conversation"],
                             "the transport never spoke to the container")
        self.assertIn("describe", evidence["conversation"]["answered"],
                      "the worker entrypoint never answered this transport")
        self.assertFalse(evidence["resolved"],
                         "an unauthorized dry run reported a clean result")
        self.assertFalse(self.present(evidence["runtime_id"]),
                         "the ending left a real container running")

    def test_an_exact_rerun_refuses_before_a_second_runtime(self):
        """Approver ruling M46497, against the daemon rather than a fixture.

        The pilot's rule is that an exact same-attempt rerun refuses BEFORE
        another runtime or provider turn, and that retry uses a fresh attempt
        identity. Reflected here rather than frozen silently: what this
        asserts is the refusal the ruling decided on.
        """
        attempt_id = f"attempt-{uuid.uuid4().hex[:10]}"
        self.arc(attempt_id)
        containers = len(self.made)

        with self.assertRaises(OperatorRefusal) as caught:
            self.arc(attempt_id)

        self.assertIn("stages its source once", str(caught.exception))
        self.assertEqual(len(self.made), containers,
                         "an exact rerun started a second real container")


if __name__ == "__main__":                                 # pragma: no cover
    unittest.main()
