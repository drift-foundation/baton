"""W197661 — the one fixture image's delivery dispatch.

WHY ONE IMAGE. `tools/single_worker.py:267` refuses a worker whose
`image_digest` differs from its Job input manifest's `worker_image_digest`, and
a Job names exactly one input manifest -- so a deployment cannot give its
integrator a different artefact. claim201324 built a second image and three
validators refused the composition.

WHAT THIS SUITE IS FOR. The proposing recipe removed a second agent because
"two agents in one image, one selected by a branch nobody reads" had silently
run the wrong one. That was a FALLBACK reached by omission. This dispatch has no
default: a delivery it cannot classify refuses both workloads, and the case that
says so is here with the implementation rather than promised for later.

NO CONTAINER, NO ENGINE, NO MODEL, AND NO EXTERNAL STATE. Every case is a
temporary directory.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

REPO = "/home/sl/src/baton"
CONTEXT = os.path.join(
    REPO, "work/records/2026/09/finding-v12-worker-launch-version-mismatch",
    "instance-201492/context/worker")


def _as_the_image_lays_it_out(case):
    """The image's own import namespace: one directory, top-level names."""
    if CONTEXT not in sys.path:
        sys.path.insert(0, CONTEXT)
        case.addCleanup(sys.path.remove, CONTEXT)


class DispatchCase(unittest.TestCase):

    def setUp(self):
        _as_the_image_lays_it_out(self)
        import fixture_entry
        import integration_contract

        self.entry = fixture_entry
        self.contract = integration_contract
        self.home = tempfile.mkdtemp(prefix="v12-w197661-dispatch-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.assignment_root = os.path.join(self.home, "assignment")

    def assignment(self, payload=None):
        """The namespace an INTEGRATION attempt is delivered."""
        os.makedirs(self.assignment_root, exist_ok=True)
        held = {"schema": self.contract.ASSIGNMENT_SCHEMA,
                "canonical_target_id": "w197661-target",
                "entry_id": "integration-driver.entry:" + "a" * 64,
                "lease_id": "integration-driver.lease:" + "b" * 64,
                "fence": 1, "attempt_id": "attempt-" + "c" * 64,
                "integrator_participant": "baton.w197661-integrator",
                "profile_kind": "git", "profile_version": 1,
                "instructions_digest": "sha256:" + "d" * 64,
                "target_access": "writable"}
        with open(os.path.join(self.assignment_root,
                               self.contract.ASSIGNMENT_DOCUMENT),
                  "w") as handle:
            handle.write(json.dumps(held if payload is None else payload))

    def dispatched(self):
        """Which workload the real entry enters, without entering it."""
        import baton_worker
        import integration_entry

        seen = {}

        def integrating(*, agent=None, **named):
            seen["workload"] = "integration_entry.main"
            seen["agent"] = type(agent).__name__
            return 0

        def working(*, agent=None, **named):
            seen["workload"] = "baton_worker.main"
            seen["agent"] = type(agent).__name__
            return 0

        with mock.patch.object(integration_entry, "main", integrating), \
                mock.patch.object(baton_worker, "main", working):
            seen["status"] = self.entry.main(
                assignment_root=self.assignment_root)
        return seen


class TheDELIVERYSelectsTheWORKLOAD(DispatchCase):

    def test_an_INTEGRATION_assignment_enters_the_integration_entry(self):
        self.assignment()
        seen = self.dispatched()
        self.assertEqual(seen["workload"], "integration_entry.main")
        self.assertEqual(seen["agent"], "ImportingAgent")

    def test_NO_assignment_namespace_enters_the_worker(self):
        seen = self.dispatched()
        self.assertEqual(seen["workload"], "baton_worker.main")
        self.assertEqual(seen["agent"], "ProposingAgent")

    def test_the_two_answers_come_from_ONE_function(self):
        """`delivery` is the whole decision, so a case can ask it directly and
        a reader has one place to look."""
        self.assertEqual(self.entry.delivery(self.assignment_root),
                         self.entry.DELIVERY_WORKER)
        self.assignment()
        self.assertEqual(self.entry.delivery(self.assignment_root),
                         self.entry.DELIVERY_INTEGRATION)


class ADeliveryItCannotCLASSIFYRefusesBOTHWorkloads(DispatchCase):
    """The defect a two-workload image must never have, covered WITH the
    implementation rather than promised for later: a container that quietly
    proposes when it was asked to integrate."""

    def refuses(self):
        seen = self.dispatched()
        self.assertNotIn("workload", seen,
                         f"a delivery it cannot classify entered {seen}")
        self.assertEqual(seen["status"], 2)

    def test_an_EMPTY_assignment_namespace_refuses(self):
        os.makedirs(self.assignment_root)
        self.refuses()

    def test_an_assignment_that_is_NOT_A_DOCUMENT_refuses(self):
        os.makedirs(self.assignment_root)
        with open(os.path.join(self.assignment_root,
                               self.contract.ASSIGNMENT_DOCUMENT),
                  "w") as handle:
            handle.write("NOT JSON AT ALL")
        self.refuses()

    def test_an_assignment_with_ANOTHER_SCHEMA_refuses(self):
        self.assignment({"schema": "something.else/1"})
        self.refuses()

    def test_an_assignment_MISSING_ITS_MEMBERS_refuses(self):
        self.assignment({"schema": self.contract.ASSIGNMENT_SCHEMA})
        self.refuses()

    def test_a_namespace_that_is_a_FILE_refuses(self):
        with open(self.assignment_root, "w") as handle:
            handle.write("not a namespace")
        self.refuses()

    def test_a_namespace_that_is_a_DANGLING_LINK_refuses(self):
        """`lexists` is deliberate: the link is THERE, so this is not the
        ordinary absent case, and following it answers about whatever it
        points at."""
        os.symlink(os.path.join(self.home, "nowhere"), self.assignment_root)
        self.refuses()

    def test_the_refusal_SAYS_WHY_on_stderr(self):
        """W198667's whole lesson: a refusal nobody can read is the half of an
        incident that makes it expensive."""
        import io
        import contextlib

        os.makedirs(self.assignment_root)
        said = io.StringIO()
        with contextlib.redirect_stderr(said):
            answered = self.entry.main(assignment_root=self.assignment_root)
        self.assertEqual(answered, 2)
        self.assertIn("cannot read", said.getvalue())


class TheIMAGECarriesWhatBothWorkloadsNeed(unittest.TestCase):
    """One artefact, and the recipe is where a reviewer reads what is in it."""

    RECIPE = os.path.join(
        REPO, "work/records/2026/09/finding-v12-worker-launch-version-mismatch",
        "instance-201492/context/Dockerfile.fixture")

    def setUp(self):
        _as_the_image_lays_it_out(self)
        with open(self.RECIPE) as handle:
            self.recipe = handle.read()

    def copied(self):
        return [line.split()[1] for line in self.recipe.splitlines()
                if line.startswith("COPY")]

    def test_the_ENTRYPOINT_is_the_dispatching_entry(self):
        self.assertIn(
            'ENTRYPOINT ["python3", "/opt/baton/fixture_entry.py"]',
            self.recipe)

    def test_every_COPIED_input_exists(self):
        context = os.path.dirname(self.RECIPE)
        for one in self.copied():
            self.assertTrue(os.path.exists(os.path.join(context, one)), one)

    def test_BOTH_workloads_and_their_agents_travel(self):
        copied = " ".join(self.copied())
        for needed in ("proposing_agent.py", "importing_agent.py",
                       "integration_entry.py", "integration_workload.py",
                       "integration_contract.py", "baton_worker.py",
                       "fixture_entry.py"):
            self.assertIn(needed, copied)

    def test_the_REVIEWED_LOGGING_BYTES_are_named_with_their_digests(self):
        """Review 2026-09-18T07-45-26Z: snapshot W198667's reviewed inputs with
        explicit attribution rather than inheriting old acceptance by
        filename."""
        import hashlib

        context = os.path.dirname(self.RECIPE)
        for name in ("attempt_log_format.py", "baton_worker.py",
                     "claude_agent.py"):
            with open(os.path.join(context, "worker", name), "rb") as handle:
                held = hashlib.sha256(handle.read()).hexdigest()
            self.assertIn(held, self.recipe,
                          f"{name} is carried without its digest recorded")

    def test_there_is_NO_scripted_fallback_agent(self):
        """The module whose silent default ran the wrong agent."""
        self.assertNotIn("scripted_agent", self.recipe)


if __name__ == "__main__":
    unittest.main()
