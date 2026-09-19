"""W197661 — the deterministic fixture INTEGRATOR.

THE BLOCKER THIS COVERS. The fixture image carried a proposing agent and no
integrating one, so the integration container entered `proposing_entry.py` and
proposed instead of importing; the stage went `exceptional` and report-and-hold
was unreachable by construction.

NO CONTAINER, NO ENGINE, NO MODEL. The agent's whole job is to write the rows an
approved bundle carries into the tree it was handed and report what it did, so a
bundle laid out here is the same arrangement the container gets -- and the
shapes come from `integration_contract` itself, which is what keeps a fixture
from drifting from the document the manager validates.
"""

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest

REPO = "/home/sl/src/baton"
CONTEXT = os.path.join(
    REPO, "work/records/2026/09/finding-v12-worker-launch-version-mismatch",
    "instance-201492/context/worker")
WORKER = os.path.join(REPO, "v12/worker")


def _as_the_image_lays_it_out(case):
    """The integration image's own import namespace, top-level names only."""
    for place in (CONTEXT, WORKER):
        if place not in sys.path:
            sys.path.insert(0, place)
            case.addCleanup(sys.path.remove, place)


class ImportingCase(unittest.TestCase):

    ASSIGNMENT_DIGEST = "sha256:" + "a" * 64
    BUNDLE_DIGEST = "sha256:" + "b" * 64

    def setUp(self):
        _as_the_image_lays_it_out(self)
        import importing_agent
        import integration_contract

        self.module = importing_agent
        self.contract = integration_contract
        self.home = tempfile.mkdtemp(prefix="v12-w197661-import-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.bundle = os.path.join(self.home, "bundle")
        self.blobs = os.path.join(self.bundle, self.contract.BLOB_DIRECTORY)
        os.makedirs(self.blobs)
        self.target = os.path.join(self.home, "target")
        os.makedirs(self.target)
        self.scratch = os.path.join(self.home, "scratch")
        os.makedirs(self.scratch)
        self.report = os.path.join(self.scratch,
                                   self.contract.REPORT_DOCUMENT)

    # -- the bundle, in the contract's own shape ----------------------------

    def blob(self, payload):
        """One content-addressed blob, named the way the contract names it."""
        held = hashlib.sha256(payload).hexdigest()
        with open(os.path.join(self.blobs, held), "wb") as handle:
            handle.write(payload)
        return held

    def side(self, payload, mode="100644"):
        held = self.blob(payload)
        return {"object": "0" * 40, "blob": held, "bytes": len(payload),
                "mode": mode}

    def row(self, path, candidate=b"", operation="add", base=None,
            mode="100644"):
        return {"path": path, "operation": operation, "base": base,
                "candidate": None if candidate is None
                else self.side(candidate, mode)}

    def agent(self):
        return self.module.ImportingAgent(bundle_root=self.bundle)

    def prompt(self, place=None, identity=None):
        """The lines this agent reads out of the workload's own prompt.

        BOTH OPERANDS ARE THE PROMPT'S, and the second one is why: the live
        run of claim201492 ended in a `KeyError` because this agent read
        `bundle_digest` from `read_bundle`, which does not answer one -- the
        workload MEASURES the bundle itself and states the measured identity
        here. `compose_prompt` writes both of these lines.
        """
        return ("some instructions\n\n"
                f"Its measured identity is "
                f"{self.BUNDLE_DIGEST if identity is None else identity}.\n"
                f"Write your bounded {self.contract.REPORT_SCHEMA} report to "
                f"{place or self.report} and write no other file outside the "
                f"target.\n")

    def invoked(self, rows, prompt=None):
        """The provider turn, with `read_bundle` answering these rows.

        The bundle READER is the contract's and is exercised by its own suite;
        what this case is about is what the agent does with the table, so the
        table is supplied here and every blob is read through the real
        `bundle_blob`.
        """
        from unittest import mock

        # THE KEY SET THE REAL READER ANSWERS, measured from the retained
        # bundle of claim201492's run: envelope, evidence, instructions,
        # review, root -- and NO `bundle_digest`. The earlier double carried
        # one, which is why a mocked suite passed while the live turn raised.
        held = {"envelope": {"paths": rows,
                             "assignment_digest": self.ASSIGNMENT_DIGEST},
                "evidence": {}, "instructions": b"", "review": {},
                "root": self.bundle}
        with mock.patch.object(self.contract, "read_bundle",
                               lambda root: held):
            return self.agent().invoke_provider(
                prompt=prompt or self.prompt(), room=self.target)

    def at(self, path):
        with open(os.path.join(self.target, path), "rb") as handle:
            return handle.read()

    def reported(self):
        with open(self.report) as handle:
            return json.load(handle)


class TheFixtureIMPORTSTheApprovedRows(ImportingCase):

    def test_an_ADDED_path_carries_the_candidate_bytes(self):
        answered = self.invoked([self.row("w197661-fixture.txt",
                                          b"the candidate\n")])
        self.assertTrue(answered["ok"], answered)
        self.assertEqual(self.at("w197661-fixture.txt"), b"the candidate\n")

    def test_a_NESTED_path_is_created_a_component_at_a_time(self):
        self.invoked([self.row("a/b/c.txt", b"nested\n")])
        self.assertEqual(self.at("a/b/c.txt"), b"nested\n")

    def test_an_EDITED_path_is_REPLACED_and_not_appended(self):
        with open(os.path.join(self.target, "x.txt"), "wb") as handle:
            handle.write(b"the old bytes\n")
        self.invoked([self.row("x.txt", b"the new bytes\n",
                               operation="edit",
                               base=self.side(b"the old bytes\n"))])
        self.assertEqual(self.at("x.txt"), b"the new bytes\n")

    def test_a_DELETED_path_is_ABSENT_afterwards(self):
        """Absence is exactly what the workload's read-back looks for."""
        with open(os.path.join(self.target, "gone.txt"), "wb") as handle:
            handle.write(b"to be removed\n")
        self.invoked([self.row("gone.txt", None, operation="delete",
                               base=self.side(b"to be removed\n"))])
        self.assertFalse(os.path.exists(os.path.join(self.target,
                                                     "gone.txt")))

    def test_a_DELETE_of_something_already_absent_is_not_a_failure(self):
        answered = self.invoked([self.row("never-there.txt", None,
                                          operation="delete")])
        self.assertTrue(answered["ok"], answered)

    def test_the_REVIEWED_MODE_is_what_the_file_gets(self):
        """The workload compares the mode it approved, so the umask must not
        decide it."""
        self.invoked([self.row("run.sh", b"#!/bin/sh\n", mode="100755")])
        held = os.stat(os.path.join(self.target, "run.sh"))
        self.assertEqual(held.st_mode & 0o777, 0o755)

    def test_NOTHING_outside_the_scheduled_table_is_written(self):
        self.invoked([self.row("one.txt", b"one\n")])
        self.assertEqual(sorted(os.listdir(self.target)), ["one.txt"])

    def test_a_STAGING_entry_is_never_left_behind(self):
        self.invoked([self.row("one.txt", b"one\n")])
        self.assertEqual([one for one in os.listdir(self.target)
                          if one.startswith(".")], [])

    def test_a_blob_that_is_not_its_own_ADDRESS_is_refused(self):
        """`bundle_blob` proves the content against the name the row declares;
        a fixture that wrote whatever was there would import bytes nobody
        approved."""
        row = self.row("one.txt", b"one\n")
        with open(os.path.join(self.blobs, row["candidate"]["blob"]),
                  "wb") as handle:
            handle.write(b"SOMETHING ELSE ENTIRELY")
        answered = self.invoked([row])
        self.assertFalse(answered["ok"])
        self.assertIn("bundle", answered["failure_reason"])

    def test_a_TURN_THAT_CANNOT_COMPLETE_answers_rather_than_raising(self):
        """The workload's vocabulary for a failed turn is a HOLD; an exception
        would be a fault."""
        answered = self.module.ImportingAgent(
            bundle_root=os.path.join(self.home, "not-there")
        ).invoke_provider(prompt=self.prompt(), room=self.target)
        self.assertFalse(answered["ok"])
        self.assertIn("failure_reason", answered)


class TheREPORTIsTheContractsOwnDocument(ImportingCase):

    def test_it_is_written_WHERE_THE_PROMPT_ASKED(self):
        """The workload composes the prompt with `report_place` and reads back
        exactly that file; a guessed path answers a different question."""
        place = os.path.join(self.scratch, "elsewhere.json")
        self.invoked([self.row("one.txt", b"one\n")],
                     prompt=self.prompt(place))
        self.assertTrue(os.path.exists(place))

    def test_a_prompt_naming_NO_report_place_is_refused(self):
        answered = self.invoked([self.row("one.txt", b"one\n")],
                                prompt="no operands at all\n")
        self.assertFalse(answered["ok"])
        self.assertIn("report place", answered["failure_reason"])

    def test_the_report_PASSES_the_contracts_own_checker(self):
        """Which is the thing that makes this a report rather than a shape
        this fixture invented."""
        self.invoked([self.row("b.txt", b"b\n"), self.row("a.txt", b"a\n")])
        with open(self.report, "rb") as handle:
            taken = self.contract.check_report(handle.read())
        self.assertEqual(taken["outcome"], "imported")
        # `verification` AND NOT `import`: the workload holds an imported
        # report whose phase says the turn stopped earlier, which the live run
        # of claim201492 measured.
        self.assertEqual(taken["phase"], "verification")
        self.assertIsNone(taken["code"])

    def test_the_reported_paths_are_SORTED_and_UNIQUE(self):
        """`check_report` refuses anything else."""
        self.invoked([self.row("b.txt", b"b\n"), self.row("a.txt", b"a\n")])
        self.assertEqual(self.reported()["paths"], ["a.txt", "b.txt"])

    def test_it_names_THIS_assignment_and_THIS_bundle(self):
        """The workload holds a report that names another of either."""
        self.invoked([self.row("one.txt", b"one\n")])
        held = self.reported()
        self.assertEqual(held["assignment_digest"], self.ASSIGNMENT_DIGEST)
        self.assertEqual(held["bundle_digest"], self.BUNDLE_DIGEST)

    def test_it_claims_NO_verification_it_did_not_run(self):
        """The required test is the integrator's to run after the import, and
        a provider claiming one it did not perform is what this vocabulary
        exists to refuse."""
        self.invoked([self.row("one.txt", b"one\n")])
        self.assertIsNone(self.reported()["verification"])

    def test_a_SECOND_turn_does_not_overwrite_the_first_report(self):
        """One integration answers once."""
        self.invoked([self.row("one.txt", b"one\n")])
        answered = self.invoked([self.row("one.txt", b"one\n")])
        self.assertFalse(answered["ok"])


class TheENTRYInjectsThroughTheDocumentedSeam(unittest.TestCase):
    """The defect review199914 found in the proposing fixture, not repeated:
    copying a module is not composing with it.

    THIS PROVES PLUMBING AND NOTHING MORE, which review 2026-09-18T07-34-10Z
    said plainly and correctly: mocking `integration_entry.main` shows what
    the entry HANDS it, not which branch that function then takes.
    `TheDISPATCHIsDecidedByTheDELIVERY` below drives the real one.
    """

    def setUp(self):
        _as_the_image_lays_it_out(self)

    def test_the_entry_hands_the_REAL_entry_this_agent(self):
        from unittest import mock

        import importing_agent
        import importing_entry
        import integration_entry

        seen = {}

        def watched(*, agent=None, **named):
            seen["agent"] = agent
            return 0

        with mock.patch.object(integration_entry, "main", watched):
            self.assertEqual(importing_entry.main(), 0)
        self.assertIsInstance(seen["agent"], importing_agent.ImportingAgent)

    def test_the_agent_imports_NOTHING_from_the_manager(self):
        """A worker that could import the manager is a worker one bug away
        from holding the manager's capabilities."""
        with open(os.path.join(CONTEXT, "importing_agent.py")) as handle:
            body = handle.read()
        self.assertNotIn("baton_v12", body)
        self.assertNotIn("from baton", body)


class TheDISPATCHIsDecidedByTheDELIVERY(unittest.TestCase):
    """Review 2026-09-18T07-34-10Z, and the reviewer is right about the gap.

    `integration_entry.main` checks for `APPLY_REQUEST_DOCUMENT` FIRST: when it
    is there the entry constructs `ManagedApplyAgent` and IGNORES its `agent=`
    operand entirely, reaching `workload.managed_apply` through
    `baton_worker.main`. Only the ordinary branch passes an injected agent into
    `workload.integrate`. My earlier case mocked `main` and therefore proved
    which agent was HANDED OVER, not which branch would run it.

    These drive the real `main` over both deliveries. No container, no manager
    and no workload: the two owners it dispatches to are replaced so the branch
    itself is what is observed.
    """

    def setUp(self):
        _as_the_image_lays_it_out(self)
        import importing_agent
        import integration_contract
        import integration_entry

        self.module = importing_agent
        self.contract = integration_contract
        self.entry = integration_entry
        self.home = tempfile.mkdtemp(prefix="v12-w197661-dispatch-")
        self.addCleanup(shutil.rmtree, self.home, True)
        self.bundle = os.path.join(self.home, "bundle")
        os.makedirs(self.bundle)

    def apply_request(self):
        with open(os.path.join(self.bundle,
                               self.contract.APPLY_REQUEST_DOCUMENT),
                  "w") as handle:
            handle.write("{}")

    def dispatched(self, agent):
        """Which owner the real `main` reaches, and with what agent."""
        from unittest import mock

        import baton_worker

        seen = {}

        def worker_main(*, agent=None, place=None, **named):
            seen["owner"] = "baton_worker.main"
            seen["agent"] = agent
            return 0

        def delivered(**named):
            seen["owner"] = "_delivered"
            seen["agent"] = named.get("agent")
            return 0

        with mock.patch.object(baton_worker, "main", worker_main), \
                mock.patch.object(self.entry, "_delivered", delivered):
            self.entry.main(agent=agent, bundle_root=self.bundle)
        return seen

    def test_an_APPLY_REQUEST_reaches_the_MANAGED_owner_and_IGNORES_the_agent(self):
        """The reviewer's point, as a regression: claiming ImportingAgent runs
        on a managed apply would be claiming something this code does not do."""
        from importing_agent import ImportingAgent

        self.apply_request()
        held = ImportingAgent()
        seen = self.dispatched(held)
        self.assertEqual(seen["owner"], "baton_worker.main")
        self.assertIsNot(seen["agent"], held)
        self.assertEqual(type(seen["agent"]).__name__, "ManagedApplyAgent")

    def test_an_ORDINARY_delivery_reaches_the_workload_WITH_this_agent(self):
        from importing_agent import ImportingAgent

        held = ImportingAgent()
        seen = self.dispatched(held)
        self.assertEqual(seen["owner"], "_delivered")
        self.assertIs(seen["agent"], held)

    def test_THIS_DEPLOYMENT_selects_the_ORDINARY_delivery(self):
        """Measured from the composed documents rather than assumed.

        `stage_execution._prepares` reads `integration_preparation` and
        defaults to False, and only the managed path composes an apply
        request. This episode's bootstrap input, install input and emitted
        configuration all omit that member, so the delivery its integrator
        receives is the ordinary one -- which is the branch that runs an
        injected agent.
        """
        instance = os.path.join(
            REPO, "work/records/2026/09",
            "finding-v12-worker-launch-version-mismatch", "instance-200564")
        for name in ("bootstrap_inputs.json", "install_inputs.json"):
            with open(os.path.join(instance, name)) as handle:
                self.assertNotIn("integration_preparation", json.load(handle))

    def test_and_the_RETAINED_RUN_composed_no_apply_input(self):
        """The same answer from the other side: the destination this Work's
        clean episode left behind holds no managed-apply material at all."""
        destination = "/home/sl/baton-v12-lifecycle-200564-clean"
        if not os.path.isdir(destination):
            self.skipTest("the retained destination is not present")
        found = []
        for where, directories, names in os.walk(destination):
            if "managed-results" in directories:
                found.append(os.path.join(where, "managed-results"))
            found.extend(os.path.join(where, one) for one in names
                         if one == self.contract.APPLY_REQUEST_DOCUMENT)
        self.assertEqual(found, [])

    def test_an_UNREADABLE_delivery_REFUSES_rather_than_proposing(self):
        """The fallback a one-image fixture must never have: an integration
        container that cannot read its delivery says so and exits, rather than
        quietly becoming a proposer."""
        answered = self.entry.main(
            agent=self.module.ImportingAgent(),
            launch_place=os.path.join(self.home, "no-launch.json"),
            bundle_root=self.bundle,
            assignment_root=os.path.join(self.home, "no-assignment"),
            result_root=os.path.join(self.home, "no-result"),
            target_root=os.path.join(self.home, "no-target"))
        # 2 IS THIS ENTRY'S ACCEPTED CONTRACT for "nothing correlatable"; what
        # matters here is that it is a refusal rather than another workload.
        self.assertEqual(answered, 2)


class TheAGENTReadsOnlyWhatItsOWNERSAnswer(ImportingCase):
    """The live run of claim201492 held with "an unexpected KeyError ended this
    turn after the provider had writable work".

    `read_bundle` answers `envelope`, `evidence`, `instructions`, `review` and
    `root`. It does NOT answer `bundle_digest`: `integration_workload` measures
    the bundle itself, because "a number a bundle states about itself is a
    claim and this comparison exists to test claims", and tells the provider
    the measured identity in the prompt. My double carried a `bundle_digest`,
    so a green suite sat on top of a turn that could not run.
    """

    def test_the_BUNDLE_DIGEST_comes_from_the_PROMPT(self):
        self.invoked([self.row("one.txt", b"one\n")])
        self.assertEqual(self.reported()["bundle_digest"], self.BUNDLE_DIGEST)

    def test_a_DIFFERENT_identity_in_the_prompt_is_what_is_reported(self):
        """Proving it is read rather than remembered."""
        other = "sha256:" + "e" * 64
        self.invoked([self.row("one.txt", b"one\n")],
                     prompt=self.prompt(identity=other))
        self.assertEqual(self.reported()["bundle_digest"], other)

    def test_a_prompt_that_states_NO_identity_is_refused(self):
        answered = self.invoked(
            [self.row("one.txt", b"one\n")],
            prompt=(f"Write your bounded {self.contract.REPORT_SCHEMA} report "
                    f"to {self.report}.\n"))
        self.assertFalse(answered["ok"])
        self.assertIn("measured identity", answered["failure_reason"])

    def test_a_MISSING_member_is_a_HOLD_and_not_a_FAULT(self):
        """The workload has words for a turn that could not complete; an
        unexpected exception is not one of them."""
        from unittest import mock

        with mock.patch.object(self.contract, "read_bundle",
                               lambda root: {"envelope": {}}):
            answered = self.agent().invoke_provider(prompt=self.prompt(),
                                                    room=self.target)
        self.assertFalse(answered["ok"])
        self.assertIn("does not answer", answered["failure_reason"])

    def test_the_REAL_reader_is_what_the_double_must_match(self):
        """The calibration that was missing: the double's key set is the real
        one, so a reader that reaches for anything else fails here."""
        import inspect

        source = inspect.getsource(self.module.ImportingAgent)
        self.assertNotIn('held["bundle_digest"]', source)


class TheREPORTDescribesACompletedTurn(ImportingCase):
    """The live run of claim201492 held with "its phase or its changed-path
    list is not the completed turn the target shows".

    `integration_workload` requires an `imported` report to carry
    `phase == "verification"` AND a changed-path list equal to the WHOLE
    scheduled table -- "a provider that claims an import while describing a
    turn that never reached one is not corroborating anything".
    """

    def test_the_PHASE_of_an_imported_report_is_verification(self):
        self.invoked([self.row("one.txt", b"one\n")])
        self.assertEqual(self.reported()["phase"], "verification")

    def test_the_PATHS_are_the_WHOLE_scheduled_table(self):
        rows = [self.row("b.txt", b"b\n"), self.row("a.txt", b"a\n"),
                self.row("gone.txt", None, operation="delete")]
        self.invoked(rows)
        self.assertEqual(self.reported()["paths"],
                         sorted(row["path"] for row in rows))

    def test_the_workloads_OWN_condition_holds_over_what_is_written(self):
        """The assertion the workload makes, made here over this report."""
        rows = [self.row("b.txt", b"b\n"), self.row("a.txt", b"a\n")]
        self.invoked(rows)
        held = self.reported()
        self.assertFalse(
            held["phase"] != "verification"
            or held["paths"] != sorted(row["path"] for row in rows),
            "this report would be held as inconsistent by the workload")


if __name__ == "__main__":
    unittest.main()
