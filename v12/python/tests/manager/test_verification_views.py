"""The WORKER's fresh private verification view, and the named gate in it.

W321776, `work/records/2026/09/finding-v12-complete-verification-context/
findings/finding-paired-context-delivery/`, against the accepted packet in
`findings/finding-context-packet/` -- `VERIFICATION.md`'s obligation table and
`CONTEXT-CONTRACTS.md`'s two preflight stages.

WHAT THIS SUITE IS ABOUT. DESIGN VER-3 requires the worker to materialize a
FRESH PRIVATE view from the exact candidate and the sealed declared inputs, and
until this Work the adapter ran the task's command with `cwd` set to the
candidate itself -- which for a line profile is the retained worktree. The
cases here are the half of the paired obligation that belongs to the worker:
the view exists, the command runs in it, Stage A and Stage B refuse what the
packet says they refuse, the retained candidate and the seal survive every
ending, and the NAMED 102-test gate passes in that view with no skips and no
context errors.

WHAT IT IS NOT ABOUT. The independent operator's view is
`tests/tools/test_operator_verification_view.py`, deliberately a separate suite
driving separate product code: the whole point of two holders is that their
MEASUREMENTS can disagree, and one suite exercising one materializer twice
would prove nothing about that.

NO ENGINE, NO IMAGE, NO PROVIDER. The adapter's process capability is injected,
so the "provider" is a recorded fake and the verification command is a real
child -- which is the right split, because the command is the thing under test
and the provider is not.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

WORKER = (pathlib.Path(__file__).resolve().parents[3] / "worker")
if str(WORKER) not in sys.path:
    sys.path.insert(0, str(WORKER))
# THE IMAGE'S LAYOUT, REPRODUCED. `Dockerfile.claude` copies
# `source_profiles` and `verification_context.py` to `/opt/baton` as top-level
# names, so the adapter imports them as ones; putting that directory here
# reproduces the layout rather than relaxing the rule that the adapter can
# never spell `baton_v12`.
_SHARED = str(WORKER.parent / "python" / "src" / "baton_v12")
if _SHARED not in sys.path:
    sys.path.insert(0, _SHARED)

import claude_agent                                           # noqa: E402
from claude_agent import ClaudeAgent, TaskRefusal              # noqa: E402
import verification_context as contract                       # noqa: E402

from tests.manager import verification_fixtures as fixtures    # noqa: E402

DECLARED = [{"name": "proposal", "type": "directory-result",
             "path": "proposal", "required": True,
             "content_type": "application/x-directory"}]


class ViewCase(unittest.TestCase):
    """A staged `/input` carrying a `/3` task AND its seal, and a writable
    `/output`.

    THE SEAL IS STAGED THROUGH THE OPERATOR'S OWN COMPOSER, so the bytes this
    adapter reads are bytes the deployment actually produces. A hand-built seal
    would agree with this file by construction.
    """

    def setUp(self):
        home = tempfile.mkdtemp(prefix="v12-w321776-")
        self.addCleanup(shutil.rmtree, home, True)
        self.home = home
        self.inputs = os.path.join(home, "input")
        self.outputs = os.path.join(home, "output")
        self.scratch = os.path.join(home, "scratch")
        self.credentials = os.path.join(home, "credentials")
        for place in (self.inputs, self.outputs, self.scratch,
                      self.credentials):
            os.makedirs(place)
        self.source = os.path.join(self.inputs, "source")
        with open(os.path.join(self.credentials, "claude"), "w",
                  encoding="utf-8") as writing:
            writing.write("not-a-credential\n")
        for name, value in (("INPUT_ROOT", self.inputs),
                            ("OUTPUT_ROOT", self.outputs),
                            ("CREDENTIAL_ROOT", self.credentials)):
            held = getattr(claude_agent, name)
            setattr(claude_agent, name, value)
            self.addCleanup(setattr, claude_agent, name, held)
        self.pin_digest = fixtures.digest_of(
            fixtures.REPOSITORY / fixtures.VECTORS)

    # -- staging -------------------------------------------------------------

    def tiny_source(self):
        fixtures.tiny_candidate(self.inputs, place="source")
        landing = os.path.join(self.source, fixtures.VECTORS)
        os.makedirs(os.path.dirname(landing), exist_ok=True)
        shutil.copyfile(fixtures.REPOSITORY / fixtures.VECTORS, landing)
        return self.source

    def gate_source(self):
        return fixtures.gate_candidate(self.inputs, name="source")

    def seal(self):
        self.sealed = fixtures.gate_seal(self.inputs,
                                         pin_digest=self.pin_digest)
        return self.sealed

    def task(self, document):
        with open(os.path.join(self.inputs, claude_agent.TASK_DOCUMENT), "w",
                  encoding="utf-8") as writing:
            json.dump(document, writing)
        return document

    def tiny_task(self, **operands):
        """A `/3` task whose command is one trivial child in the view."""
        context = fixtures.gate_context(pin_digest=self.pin_digest)
        context["working_directory"] = "candidate"
        context["import_roots"] = []
        context["required_paths"] = ["harness.py"]
        operands.setdefault("context", context)
        return self.task(fixtures.gate_task(
            pin_digest=self.pin_digest,
            argv=["python3", "-c", "print('ran in the view')"], **operands))

    def gate_task(self, **operands):
        return self.task(fixtures.gate_task(pin_digest=self.pin_digest,
                                            **operands))

    # -- the injected capability --------------------------------------------

    def runner(self, *, edits=None, deletes=(), status=0, verify=None,
               timeout=False, missing=False, writes=None, record=None):
        """The provider is a fake; the verification command is a REAL child.

        That split is the point rather than a convenience: the command running
        in a view is what these cases are about, and a fake command could not
        write into a candidate, overrun a bound or fail to start for the
        reasons a real one does.
        """
        self.calls = record if record is not None else []

        def run(argv, **options):
            self.calls.append((list(argv), dict(options)))
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                if timeout:
                    raise subprocess.TimeoutExpired(argv, 1)
                if missing:
                    raise OSError("no such file")
                for name, body in (edits or {}).items():
                    place = os.path.join(options["cwd"], name)
                    os.makedirs(os.path.dirname(place), exist_ok=True)
                    with open(place, "w", encoding="utf-8") as writing:
                        writing.write(body)
                for name in deletes:
                    os.unlink(os.path.join(options["cwd"], name))
                return subprocess.CompletedProcess(argv, status, None, None)
            if verify is not None:
                return subprocess.CompletedProcess(argv, verify, None, None)
            if writes is not None:
                writes(options["cwd"])
            return subprocess.run(argv, **options)

        return run

    def worked(self, **operands):
        agent = ClaudeAgent(run=self.runner(**operands), home=self.scratch)
        return agent.work({"contract": "the frozen task"}, list(DECLARED))

    # -- reading the result --------------------------------------------------

    def proposal(self, *parts):
        return os.path.join(self.outputs, "proposal", *parts)

    def result(self):
        with open(self.proposal("result.json"), encoding="utf-8") as handle:
            return json.load(handle)

    def verifier_call(self):
        return next((argv, options) for argv, options in self.calls
                    if argv[0] != claude_agent.PROVIDER_PROGRAM)


class TheNamedGatePassesInTheWorkersOwnView(ViewCase):
    """VER-5's acceptance obligation, at this holder.

    "The selected historical 102-test credential gate must pass in both
    independently materialized views with no skips or context errors; a
    different passing subset does not substitute for that obligation." This is
    one of the two views, and the other one is the operator suite's.
    """

    def test_the_gate_passes_in_the_view_with_no_skips_and_no_errors(self):
        self.gate_source()
        self.seal()
        self.gate_task()
        answered = self.worked(edits={"v12/python/w321776-marker.py":
                                      "MARKER = 'the provider edited this'\n"})
        record = self.result()
        self.assertEqual(record["schema"], contract.PROPOSAL_SCHEMA, record)
        self.assertEqual(record["context"], contract.ready(), record)
        self.assertEqual(record["command"], contract.PASSED, record)
        self.assertEqual(record["exit_status"], 0, record)
        self.assertEqual(
            contract.verdict(record["context"], record["command"],
                             record["exit_status"]),
            contract.PASSED)
        self.assertEqual(answered["disposition"], "completed", answered)

    def test_the_command_ran_in_a_private_view_and_not_in_the_candidate(self):
        """THE WHOLE DIFFERENCE, asserted rather than described."""
        self.gate_source()
        self.seal()
        self.gate_task()
        self.worked(edits={"v12/python/w321776-marker.py": "MARKER = 1\n"})
        _argv, options = self.verifier_call()
        where = os.path.realpath(options["cwd"])
        candidate = os.path.realpath(os.path.join(self.outputs,
                                                  claude_agent.CANDIDATE_NAME))
        self.assertTrue(
            os.path.relpath(where, candidate).startswith(os.pardir),
            f"the command ran inside the retained candidate: {where}")
        self.assertTrue(
            os.path.relpath(where, os.path.realpath(self.outputs))
            .startswith(os.pardir),
            f"the command ran inside the declared output: {where}")

    def test_the_gate_still_passes_with_a_hostile_ambient_import_path(self):
        """Ambient independence. The adapter composes the whole environment
        from nothing, so a hostile `PYTHONPATH` exported here cannot reach the
        child -- and the derived value is the only one that does."""
        hostile = os.path.join(self.home, "hostile")
        os.makedirs(hostile)
        with open(os.path.join(hostile, "unittest.py"), "w",
                  encoding="utf-8") as writing:
            writing.write("raise SystemExit('the hostile entry was used')\n")
        held = os.environ.get("PYTHONPATH")
        os.environ["PYTHONPATH"] = hostile
        self.addCleanup(lambda: (os.environ.__setitem__("PYTHONPATH", held)
                                 if held is not None
                                 else os.environ.pop("PYTHONPATH", None)))
        self.gate_source()
        self.seal()
        self.gate_task()
        self.worked(edits={"v12/python/w321776-marker.py": "MARKER = 1\n"})
        _argv, options = self.verifier_call()
        self.assertNotIn(hostile, options["env"]["PYTHONPATH"])
        self.assertEqual(self.result()["command"], contract.PASSED,
                         self.result())


class TheImportPathIsDerivedAndClosed(ViewCase):

    def test_the_derived_path_is_the_roots_joined_to_the_working_directory(self):
        self.gate_source()
        self.seal()
        task = self.gate_task()
        self.worked(edits={"v12/python/w321776-marker.py": "MARKER = 1\n"})
        _argv, options = self.verifier_call()
        view = os.path.dirname(os.path.dirname(os.path.dirname(
            options["cwd"])))
        self.assertEqual(
            options["env"]["PYTHONPATH"],
            os.path.join(view, "candidate", "v12", "python", "src"))
        self.assertEqual(
            contract.import_path(task["verification_context"]),
            ["candidate/v12/python/src"])

    def test_the_argv_carries_no_environment_assignment(self):
        """An argv carrying one would be a second, disagreeing source of the
        same fact."""
        for one in fixtures.GATE_ARGV:
            self.assertNotIn("=", one.split(".")[0])
            self.assertFalse(one.startswith("PYTHONPATH"), one)


class TheGenerationsRefuseEachOthersSemantics(ViewCase):
    """VER-1's refusal direction, at the worker, in both directions."""

    def test_a_legacy_task_carrying_the_new_member_refuses(self):
        self.tiny_source()
        self.seal()
        self.task({**fixtures.gate_task(pin_digest=self.pin_digest),
                   "schema": contract.LEGACY_TASK_SCHEMA})
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("verification_context", str(refused.exception))

    def test_a_new_task_without_the_member_refuses(self):
        self.tiny_source()
        self.seal()
        document = fixtures.gate_task(pin_digest=self.pin_digest)
        document.pop("verification_context")
        self.task(document)
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("verification_context", str(refused.exception))

    def test_a_task_from_another_generation_still_refuses_by_equality(self):
        self.tiny_source()
        self.task({**fixtures.gate_task(pin_digest=self.pin_digest),
                   "schema": "baton.dogfood-task/9"})
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("baton.dogfood-task/9", str(refused.exception))

    def test_the_two_generations_are_the_pair_the_contract_names(self):
        self.assertEqual(claude_agent.TASK_GENERATIONS,
                         (contract.LEGACY_TASK_SCHEMA, contract.TASK_SCHEMA))
        self.assertEqual(claude_agent.CONTEXT_TASK_MEMBERS,
                         claude_agent.TASK_MEMBERS + ("verification_context",))

    def test_a_legacy_task_is_still_staged_exactly_as_it_was(self):
        """`/2` IS FROZEN. The frozen generation still produces the record it
        always did, with none of the new members."""
        self.tiny_source()
        self.task({"schema": contract.LEGACY_TASK_SCHEMA,
                   "task_id": "w321776-legacy",
                   "instructions": "unchanged",
                   "verification": ["python3", "-c", "print(1)"],
                   "source_root": "source", "source_profile": "generic",
                   "declared_base": None})
        self.worked(edits={"harness.py": "print('changed')\n"})
        record = self.result()
        self.assertEqual(record["schema"], "baton.dogfood-proposal/1")
        for name in contract.PROPOSAL_CONTEXT_MEMBERS:
            self.assertNotIn(name, record)


class StageARefusesBeforeAnythingHappens(ViewCase):
    """"A Stage-A refusal is `refused` with its cause, `command: not-run`, and
    NOTHING materialized" -- and before any provider work."""

    def refused_statically(self, context):
        self.tiny_source()
        self.seal()
        self.tiny_task(context=context)
        answered = self.worked()
        return answered, self.result()

    def declaration(self, **changes):
        context = fixtures.gate_context(pin_digest=self.pin_digest)
        context["working_directory"] = "candidate"
        context["import_roots"] = []
        context["required_paths"] = ["harness.py"]
        context.update(changes)
        return context

    def test_an_absolute_path_refuses_and_no_provider_ran(self):
        answered, record = self.refused_statically(
            self.declaration(working_directory="/etc"))
        self.assertEqual(record["context"]["outcome"], contract.REFUSED)
        self.assertEqual(record["context"]["stage"], contract.STATIC_STAGE)
        self.assertEqual(record["context"]["cause"], contract.INVALID_LAYOUT)
        self.assertEqual(record["command"], contract.NOT_RUN)
        self.assertEqual(record["exit_status"], None)
        self.assertIsNone(contract.verdict(record["context"],
                                           record["command"],
                                           record["exit_status"]))
        self.assertEqual(answered["disposition"], "unable")
        self.assertEqual(self.calls, [],
                         "a declaration refusal spent a provider turn")

    def test_nothing_was_materialized(self):
        self.refused_statically(self.declaration(working_directory="/etc"))
        self.assertFalse(
            os.path.exists(os.path.join(self.scratch, claude_agent.VIEW_NAME)),
            "a Stage-A refusal left a view behind")

    def test_an_input_destination_inside_the_candidate_refuses(self):
        _answered, record = self.refused_statically(self.declaration(
            inputs=[{"name": fixtures.INPUT_NAME,
                     "destination": "candidate/sealed/vectors.json",
                     "content_digest": self.pin_digest,
                     "bytes": (fixtures.REPOSITORY
                               / fixtures.VECTORS).stat().st_size}]))
        self.assertEqual(record["context"]["cause"], contract.INVALID_LAYOUT)
        self.assertIn("inputs[0].destination", record["context"]["detail"])

    def test_a_declared_input_the_seal_does_not_hold_refuses(self):
        _answered, record = self.refused_statically(self.declaration(
            inputs=[{"name": "nobody-sealed-this",
                     "destination": "sealed/other.json",
                     "content_digest": self.pin_digest, "bytes": 1}]))
        self.assertEqual(record["context"]["cause"], contract.MISSING_INPUT)

    def test_an_observation_in_the_sealed_task_refuses(self):
        """"A sealed task cannot carry what the turn has not done yet."""
        declaration = self.declaration()
        declaration["candidate"]["entry_head"] = "0" * 40
        _answered, record = self.refused_statically(declaration)
        self.assertEqual(record["context"]["cause"], contract.INVALID_LAYOUT)
        self.assertIn("entry_head", record["context"]["detail"])

    def test_the_detail_names_a_member_and_never_a_value(self):
        _answered, record = self.refused_statically(
            self.declaration(working_directory="/etc/shadow"))
        self.assertNotIn("/etc", record["context"]["detail"])
        self.assertEqual(record["context"]["detail"],
                         "verification_context.working_directory")

    def test_a_three_task_with_no_seal_at_all_refuses_the_assignment(self):
        self.tiny_source()
        self.tiny_task()
        with self.assertRaises(TaskRefusal) as refused:
            self.worked()
        self.assertIn("seal", str(refused.exception))


class StageBRefusesInTheView(ViewCase):
    """The view preflight, after materialization and immediately before the
    command starts -- with `command: not-run` and the view cleaned up."""

    def refused_in_view(self, **changes):
        self.tiny_source()
        self.seal()
        context = fixtures.gate_context(pin_digest=self.pin_digest)
        context["working_directory"] = "candidate"
        context["import_roots"] = []
        context["required_paths"] = ["harness.py"]
        context.update(changes)
        self.tiny_task(context=context)
        self.worked(edits={"harness.py": "print('changed')\n"})
        return self.result()

    def test_an_absent_required_path_is_missing_input(self):
        record = self.refused_in_view(required_paths=["harness.py",
                                                      "not-there.py"])
        self.assertEqual(record["context"]["stage"], contract.VIEW_STAGE)
        self.assertEqual(record["context"]["cause"], contract.MISSING_INPUT)
        self.assertEqual(record["command"], contract.NOT_RUN)
        self.assertEqual(self.calls and
                         [one for one, _o in self.calls
                          if one[0] != claude_agent.PROVIDER_PROGRAM], [],
                         "the command started in a refused context")

    def test_an_absent_import_root_is_invalid_layout(self):
        record = self.refused_in_view(import_roots=["no-such-root"])
        self.assertEqual(record["context"]["cause"], contract.INVALID_LAYOUT)
        self.assertEqual(record["command"], contract.NOT_RUN)

    def test_an_absent_working_directory_is_invalid_layout(self):
        record = self.refused_in_view(working_directory="candidate/nowhere")
        self.assertEqual(record["context"]["cause"], contract.INVALID_LAYOUT)

    def test_a_drifted_in_candidate_pin_is_materialization(self):
        """The pinned fixture, drifted in the candidate, refuses rather than
        passing the gate."""
        self.tiny_source()
        self.seal()
        self.tiny_task()
        self.worked(edits={"harness.py": "print('changed')\n",
                           fixtures.VECTORS: "{\"drifted\": true}\n"})
        record = self.result()
        self.assertEqual(record["context"]["stage"], contract.VIEW_STAGE)
        self.assertEqual(record["context"]["cause"], contract.MATERIALIZATION)
        self.assertIn("candidate.pins[0]", record["context"]["detail"])
        self.assertEqual(record["command"], contract.NOT_RUN)

    def test_the_view_is_gone_after_a_view_refusal(self):
        self.refused_in_view(required_paths=["not-there.py"])
        self.assertFalse(
            os.path.exists(os.path.join(self.scratch, claude_agent.VIEW_NAME)),
            "a Stage-B refusal left its view behind")

    def test_the_retained_candidate_and_the_seal_survive_a_refusal(self):
        before = self.sealed_digests_after(
            lambda: self.refused_in_view(required_paths=["not-there.py"]))
        self.assertEqual(before[0], before[1])

    def sealed_digests_after(self, act):
        self.tiny_source()
        self.seal()
        root = os.path.join(self.inputs, claude_agent.SEAL_ROOT)
        before = {one: fixtures.digest_of(os.path.join(root, one))
                  for one in sorted(os.listdir(root))}
        act()
        after = {one: fixtures.digest_of(os.path.join(root, one))
                 for one in sorted(os.listdir(root))}
        return before, after


class TheChangedCandidateIsWhatRuns(ViewCase):
    """"An edit made at stage 4 -- unknown when the task was sealed -- is read
    at its edited bytes by the command", proved by an edit that changes the
    gate's outcome."""

    def edited(self, body):
        self.tiny_source()
        self.seal()
        context = fixtures.gate_context(pin_digest=self.pin_digest)
        context["working_directory"] = "candidate"
        context["import_roots"] = []
        context["required_paths"] = ["harness.py"]
        self.task(fixtures.gate_task(
            pin_digest=self.pin_digest, context=context,
            argv=["python3", "harness.py"]))
        self.worked(edits={"harness.py": body})
        return self.result()

    def test_an_edit_that_passes_is_read_as_passing(self):
        record = self.edited("raise SystemExit(0)\n")
        self.assertEqual(record["command"], contract.PASSED)
        self.assertEqual(record["exit_status"], 0)

    def test_an_edit_that_fails_is_read_as_failing(self):
        record = self.edited("raise SystemExit(3)\n")
        self.assertEqual(record["command"], contract.FAILED)
        self.assertEqual(record["exit_status"], 3)
        self.assertEqual(
            contract.verdict(record["context"], record["command"],
                             record["exit_status"]), contract.FAILED)

    def test_the_turns_measured_changes_travel_with_the_result(self):
        record = self.edited("raise SystemExit(0)\n")
        changed = {one["path"]: one["content_digest"]
                   for one in record["candidate_changed"]}
        self.assertIn("harness.py", changed)
        self.assertEqual(
            changed["harness.py"],
            fixtures.digest_of(os.path.join(
                self.outputs, claude_agent.CANDIDATE_NAME, "harness.py")))

    def test_a_deletion_is_reported_and_stays_absent_in_the_view(self):
        self.tiny_source()
        self.seal()
        with open(os.path.join(self.source, "doomed.py"), "w",
                  encoding="utf-8") as writing:
            writing.write("# removed by the turn\n")
        context = fixtures.gate_context(pin_digest=self.pin_digest)
        context["working_directory"] = "candidate"
        context["import_roots"] = []
        context["required_paths"] = ["harness.py"]
        self.task(fixtures.gate_task(
            pin_digest=self.pin_digest, context=context,
            argv=["python3", "-c",
                  "import os,sys; sys.exit(0 if not "
                  "os.path.exists('doomed.py') else 9)"]))
        self.worked(edits={"harness.py": "print('changed')\n"},
                    deletes=("doomed.py",))
        record = self.result()
        self.assertIn("doomed.py", record["candidate_removed"])
        self.assertEqual(record["command"], contract.PASSED, record)


class NothingRetainedIsReachableFromTheCommand(ViewCase):
    """"A command that WRITES a source path cannot reach the candidate", and
    the same for a deletion -- in the view, because the view is a copy."""

    def ran_writing(self, act):
        self.tiny_source()
        self.seal()
        self.tiny_task()
        candidate = os.path.join(self.outputs, claude_agent.CANDIDATE_NAME)
        root = os.path.join(self.inputs, claude_agent.SEAL_ROOT)
        self.worked(edits={"harness.py": "print('changed')\n"}, writes=act)
        return candidate, root

    def test_a_command_that_writes_a_source_path_cannot_reach_the_candidate(self):
        def writes(where):
            with open(os.path.join(where, "harness.py"), "w",
                      encoding="utf-8") as writing:
                writing.write("print('the command overwrote this')\n")

        candidate, _root = self.ran_writing(writes)
        with open(os.path.join(candidate, "harness.py"),
                  encoding="utf-8") as handle:
            self.assertEqual(handle.read(), "print('changed')\n")

    def test_a_command_that_deletes_a_source_path_cannot_reach_the_candidate(self):
        def deletes(where):
            os.unlink(os.path.join(where, "harness.py"))

        candidate, _root = self.ran_writing(deletes)
        self.assertTrue(os.path.exists(os.path.join(candidate, "harness.py")))

    def test_the_sealed_inputs_are_byte_unchanged_afterwards(self):
        def writes(where):
            place = os.path.join(where, "..", fixtures.INPUT_DESTINATION)
            with open(place, "w", encoding="utf-8") as writing:
                writing.write("{}\n")

        self.tiny_source()
        self.seal()
        root = os.path.join(self.inputs, claude_agent.SEAL_ROOT)
        before = fixtures.digest_of(os.path.join(root, fixtures.INPUT_NAME))
        self.tiny_task()
        self.worked(edits={"harness.py": "print('changed')\n"}, writes=writes)
        self.assertEqual(
            fixtures.digest_of(os.path.join(root, fixtures.INPUT_NAME)),
            before)

    def test_the_view_is_removed_and_the_candidate_is_not(self):
        self.tiny_source()
        self.seal()
        self.tiny_task()
        self.worked(edits={"harness.py": "print('changed')\n"})
        self.assertFalse(
            os.path.exists(os.path.join(self.scratch, claude_agent.VIEW_NAME)))
        self.assertTrue(os.path.exists(
            os.path.join(self.outputs, claude_agent.CANDIDATE_NAME,
                         "harness.py")))


class TheCleanupBoundaryHoldsOnEveryEnding(ViewCase):

    def test_a_timed_out_command_leaves_no_view_and_no_verdict(self):
        self.tiny_source()
        self.seal()
        self.tiny_task()
        held = claude_agent.ClaudeAgent._ran

        def timing_out(self_agent, argv, **options):
            raise subprocess.TimeoutExpired(argv, options["seconds"])

        claude_agent.ClaudeAgent._ran = timing_out
        self.addCleanup(setattr, claude_agent.ClaudeAgent, "_ran", held)
        self.worked(edits={"harness.py": "print('changed')\n"})
        record = self.result()
        self.assertEqual(record["context"], contract.ready())
        self.assertEqual(record["command"], contract.TIMED_OUT)
        self.assertEqual(record["exit_status"], None)
        self.assertIsNone(contract.verdict(record["context"],
                                           record["command"],
                                           record["exit_status"]))
        self.assertFalse(
            os.path.exists(os.path.join(self.scratch, claude_agent.VIEW_NAME)))
        self.assertTrue(os.path.exists(
            os.path.join(self.outputs, claude_agent.CANDIDATE_NAME,
                         "harness.py")))

    def test_a_command_that_cannot_start_is_a_start_failure(self):
        self.tiny_source()
        self.seal()
        self.tiny_task()
        held = claude_agent.ClaudeAgent._ran

        def failing(self_agent, argv, **options):
            raise OSError("no such executable")

        claude_agent.ClaudeAgent._ran = failing
        self.addCleanup(setattr, claude_agent.ClaudeAgent, "_ran", held)
        self.worked(edits={"harness.py": "print('changed')\n"})
        record = self.result()
        self.assertEqual(record["context"]["outcome"], contract.REFUSED)
        self.assertEqual(record["context"]["cause"], contract.START_FAILURE)
        self.assertEqual(record["command"], contract.NOT_RUN)
        self.assertFalse(
            os.path.exists(os.path.join(self.scratch, claude_agent.VIEW_NAME)))

    def test_a_partial_materialization_leaves_no_half_built_view(self):
        self.tiny_source()
        self.seal()
        self.tiny_task()
        held = claude_agent._copy_view_tree

        def half(candidate, into, *, skip=None):
            os.makedirs(into, exist_ok=True)
            with open(os.path.join(into, "half.py"), "w",
                      encoding="utf-8") as writing:
                writing.write("# half a view\n")
            raise OSError("the filesystem gave out half way")

        claude_agent._copy_view_tree = half
        self.addCleanup(setattr, claude_agent, "_copy_view_tree", held)
        with self.assertRaises(OSError):
            self.worked(edits={"harness.py": "print('changed')\n"})
        self.assertFalse(
            os.path.exists(os.path.join(self.scratch, claude_agent.VIEW_NAME)),
            "a partial materialization left a half-built view")


class TheDurableOutcomesAreSafeAndClosed(ViewCase):

    def test_the_record_carries_no_child_output_and_no_host_path(self):
        self.tiny_source()
        self.seal()
        context = fixtures.gate_context(pin_digest=self.pin_digest)
        context["working_directory"] = "candidate"
        context["import_roots"] = []
        context["required_paths"] = ["harness.py"]
        self.task(fixtures.gate_task(
            pin_digest=self.pin_digest, context=context,
            argv=["python3", "harness.py"]))
        self.worked(edits={"harness.py":
                           "print('W321776-MARKER and sk-not-a-credential')\n"
                           "raise SystemExit(4)\n"})
        raw = json.dumps(self.result())
        self.assertNotIn("W321776-MARKER", raw)
        self.assertNotIn("sk-not-a-credential", raw)
        self.assertNotIn(self.home, raw)
        self.assertNotIn(self.scratch, raw)

    def test_the_record_is_exactly_the_fresh_generations_member_set(self):
        self.tiny_source()
        self.seal()
        self.tiny_task()
        self.worked(edits={"harness.py": "print('changed')\n"})
        self.assertEqual(sorted(self.result()),
                         sorted(claude_agent.CONTEXT_RESULT_MEMBERS))

    def test_a_clean_turn_reports_ready_and_not_run(self):
        """No command was attempted, which is not a refusal: the context was
        never the problem."""
        self.tiny_source()
        self.seal()
        self.tiny_task()
        self.worked()
        record = self.result()
        self.assertEqual(record["context"], contract.ready())
        self.assertEqual(record["command"], contract.NOT_RUN)
        self.assertEqual(record["exit_status"], None)

    def test_every_illegal_combination_is_refused_before_it_is_durable(self):
        """The publisher asks `check_outcome`, so a malformed combination
        cannot become a record at all."""
        for context, command, status in (
                (contract.ready(), contract.PASSED, None),
                (contract.ready(), contract.PASSED, 1),
                (contract.ready(), contract.FAILED, 0),
                (contract.ready(), contract.FAILED, None),
                (contract.ready(), contract.TIMED_OUT, 0),
                (contract.ready(), contract.NOT_RUN, 0),
                (contract.refused(contract.MISSING_INPUT, "x",
                                  stage=contract.VIEW_STAGE),
                 contract.PASSED, 0)):
            with self.assertRaises(contract.MalformedOutcome):
                claude_agent._context_result(
                    {"task_id": "w321776"},
                    {"context": context, "command": command,
                     "exit_status": status},
                    {"changed": [], "removed": []}, source_entries=None)

    def test_a_legacy_result_is_never_reinterpreted(self):
        self.assertIsNone(contract.reported_command(
            {"schema": contract.LEGACY_PROPOSAL, "task_id": "w321776"}))


class TheViewCopierKeepsItsDiscipline(unittest.TestCase):
    """The copier's own rules, asked directly: no link, no special file, and a
    ceiling that is the VIEW's rather than the staged source's."""

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-w321776-copy-")
        self.addCleanup(shutil.rmtree, self.home, True)

    def test_a_link_in_the_candidate_refuses(self):
        candidate = os.path.join(self.home, "candidate")
        os.makedirs(candidate)
        with open(os.path.join(candidate, "real.py"), "w",
                  encoding="utf-8") as writing:
            writing.write("# real\n")
        os.symlink("/etc/passwd", os.path.join(candidate, "escape"))
        with self.assertRaises(TaskRefusal):
            claude_agent._copy_view_tree(candidate,
                                         os.path.join(self.home, "view"))

    def test_the_ceiling_is_the_views_own_and_is_larger(self):
        self.assertGreater(claude_agent.MAX_VIEW_ENTRIES,
                           claude_agent.MAX_SOURCE_ENTRIES)
        self.assertGreater(claude_agent.MAX_VIEW_BYTES,
                           claude_agent.MAX_SOURCE_BYTES)

    def test_an_empty_candidate_refuses_rather_than_producing_an_empty_view(self):
        candidate = os.path.join(self.home, "empty")
        os.makedirs(candidate)
        with self.assertRaises(TaskRefusal):
            claude_agent._copy_view_tree(candidate,
                                         os.path.join(self.home, "view2"))


class TheSharedPlanIsAskedRatherThanRespelled(unittest.TestCase):
    """Stage B's questions come from the shared contract, in its order."""

    def test_the_plan_asks_layout_then_missing_input_then_bytes(self):
        digest = "sha256:" + "0" * 64
        context = fixtures.gate_context(pin_digest=digest)
        plan = contract.view_plan(
            context, observation={"changed": [{"path": "a.py",
                                               "content_digest": digest}],
                                  "removed": ["b.py"]})
        self.assertEqual([one["cause"] for one in plan],
                         [contract.INVALID_LAYOUT] * (
                             1 + len(context["import_roots"]))
                         + [contract.MISSING_INPUT] * len(
                             context["required_paths"])
                         + [contract.MATERIALIZATION] * 4)
        self.assertEqual(plan[-1]["kind"], contract.ABSENT)
        self.assertEqual(plan[-1]["path"], "candidate/b.py")

    def test_an_absent_byte_path_answers_materialization(self):
        digest = "sha256:" + "0" * 64
        context = fixtures.gate_context(pin_digest=digest)
        plan = contract.view_plan(context,
                                  observation={"changed": [], "removed": []})
        with self.assertRaises(contract.ContextRefusal) as refused:
            contract.answered(plan, isdir=lambda one: True,
                              exists=lambda one: True,
                              digest=lambda one: None)
        self.assertEqual(refused.exception.cause, contract.MATERIALIZATION)
        self.assertEqual(refused.exception.stage, contract.VIEW_STAGE)


if __name__ == "__main__":
    unittest.main()
