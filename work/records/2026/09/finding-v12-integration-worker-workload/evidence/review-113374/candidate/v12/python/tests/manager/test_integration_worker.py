"""W110935: the integration worker, and what exists of it so far.

`work/records/2026/09/finding-v12-integration-worker-workload/`.

WHAT THIS FILE OWNS TODAY, AND IT IS NOT THE WORKLOAD. `ClaudeAgent` gained one
additive public name, `invoke_provider`, so the integration workload can take a
provider turn without growing a second copy of the credential, environment,
drain and failure rules this adapter already owns. These cases drive that
wrapper through the REAL adapter with the accepted injected-process seam --
the same seam `test_claude_agent` uses, imported from its own suite and never
edited -- and prove that the wrapper reaches the same composed argv, the same
composed environment and the same closed answer as the private turn beneath it.

WHAT IT DOES NOT CONTAIN, said here rather than left to be inferred: the
workload, the entry, the recipe and the joined proof of an accepted bundle
carried through a real entry into a provider-driven import of a disposable
target. Those are W110935's remaining paths and none of them is started. No
case in this file imports a target, edits a path or composes an integration
result, and nothing here should be read as evidence that any of that works.
"""

import os
import pathlib
import subprocess
import sys
import unittest

WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
if str(WORKER) not in sys.path:
    sys.path.insert(0, str(WORKER))
# AND THE PROFILE PACKAGE UNDER THE NAME THE IMAGE GIVES IT, which is the
# layout `test_claude_agent` reproduces for the same reason: inside the
# container `source_profiles` is a top-level package and this module can never
# spell `baton_v12`.
_NAMESPACE = str(WORKER.parent / "python" / "src" / "baton_v12")
if _NAMESPACE not in sys.path:
    sys.path.insert(0, _NAMESPACE)

import claude_agent                                    # noqa: E402


PROMPT = "import only the approved candidate bytes"


class ProviderTurnCase(unittest.TestCase):
    """One real adapter over the accepted fixture's process seam.

    COMPOSED, NOT SUBCLASSED, and the import is inside the method: a
    module-level `TestCase` binding is collected by the loader and a subclass
    re-runs every one of its parent's cases under a second name. Both
    inflations happened in this campaign and both are avoided deliberately.
    """

    def setUp(self):
        from tests.manager.test_claude_agent import AdapterCase

        self.owner = AdapterCase("run")
        self.owner.setUp()
        self.addCleanup(self.owner.doCleanups)
        self.commands = []
        self.status = 0
        self.agent = claude_agent.ClaudeAgent(run=self.runner)
        self.room = os.path.join(self.owner.home, "provider-room")
        os.makedirs(self.room)

    def runner(self, argv, **options):
        """The one process seam, recording what the adapter composed.

        NOTHING IS EXECUTED. What these cases are about is the argv, the
        environment and the working directory the adapter hands a provider, and
        a real child would establish none of that more firmly than the recorded
        operands do -- which is the decision `test_claude_agent` already made
        for the same seam.
        """
        self.commands.append({"argv": list(argv), "cwd": options.get("cwd"),
                              "env": dict(options.get("env") or {})})
        return subprocess.CompletedProcess(list(argv), self.status, None, None)

    def refused(self, **changed):
        operands = {"prompt": PROMPT, "room": self.room}
        operands.update(changed)
        with self.assertRaises(claude_agent.TaskRefusal) as caught:
            self.agent.invoke_provider(**operands)
        return caught.exception


class TheWrapperTakesTheAdaptersOwnProviderTurn(ProviderTurnCase):

    def test_a_clean_turn_answers_the_closed_document(self):
        answer = self.agent.invoke_provider(prompt=PROMPT, room=self.room)
        self.assertEqual(set(answer),
                         {"ok", "status", "failure_reason", "why"})
        self.assertEqual((answer["ok"], answer["status"]), (True, 0))
        # A CLEAN TURN PUBLISHES NO REASON, which is the private turn's rule
        # and is not restated by the wrapper.
        self.assertIsNone(answer["failure_reason"])
        self.assertIsNone(answer["why"])

    def test_the_caller_s_prompt_is_the_one_the_provider_receives(self):
        self.agent.invoke_provider(prompt=PROMPT, room=self.room)
        argv = self.commands[-1]["argv"]
        self.assertEqual(argv[0], claude_agent.PROVIDER_PROGRAM)
        self.assertEqual(argv[-1], PROMPT)
        self.assertEqual(list(argv[1:-1]), list(claude_agent.PROVIDER_ARGUMENTS))

    def test_the_turn_runs_in_the_room_it_was_given(self):
        self.agent.invoke_provider(prompt=PROMPT, room=self.room)
        self.assertEqual(self.commands[-1]["cwd"], self.room)

    def test_the_environment_is_composed_and_never_inherited(self):
        """The credential rule this wrapper exists NOT to re-implement."""
        self.agent.invoke_provider(prompt=PROMPT, room=self.room)
        composed = self.commands[-1]["env"]
        self.assertIn("HOME", composed)
        self.assertIn("PATH", composed)
        # NOTHING AMBIENT. A credential variable present in this process would
        # silently outrank the prepared one, which is the rule the wrapper
        # exists not to re-implement.
        for name in ("ANTHROPIC_API_KEY", "AWS_ACCESS_KEY_ID", "CLAUDE_CODE",
                     "PYTHONPATH", "GIT_CONFIG_GLOBAL"):
            with self.subTest(name=name):
                self.assertNotIn(name, composed)
        # THE PREPARED HOME, NOT THIS PROCESS'S. Where the adapter puts it is
        # its own decision; what matters here is that the wrapper did not hand
        # the provider the ambient one.
        self.assertNotEqual(composed["HOME"], os.environ.get("HOME"))
        self.assertTrue(os.path.isabs(composed["HOME"]))
        self.assertTrue(os.path.isdir(composed["HOME"]), composed["HOME"])

    def test_a_failing_turn_publishes_this_modules_word_and_not_the_providers(self):
        self.status = 1
        answer = self.agent.invoke_provider(prompt=PROMPT, room=self.room)
        self.assertFalse(answer["ok"])
        self.assertEqual(answer["status"], 1)
        self.assertIsNotNone(answer["failure_reason"])
        # THE PROVIDER'S OWN PROSE NEVER CROSSES. `_ran_provider` keeps stderr
        # on DEVNULL and maps stdout through a closed table; the wrapper adds
        # no second path for it.
        self.assertNotIn("stderr", answer["why"])


class TheWrapperRefusesWhatItCannotRunIn(ProviderTurnCase):

    def test_a_turn_without_a_prompt_refuses(self):
        for supplied in (None, "", b"bytes", 7):
            with self.subTest(supplied=type(supplied).__name__):
                self.refused(prompt=supplied)

    def test_a_relative_or_absent_room_refuses(self):
        for supplied in ("relative/room", "", None,
                         os.path.join(self.owner.home, "absent")):
            with self.subTest(supplied=supplied):
                self.refused(room=supplied)

    def test_a_linked_or_noncanonical_room_refuses(self):
        linked = os.path.join(self.owner.home, "linked-room")
        os.symlink(self.room, linked)
        self.refused(room=linked)
        self.refused(room=self.room + "/.")
        place = os.path.join(self.owner.home, "ordinary-file")
        with open(place, "wb") as handle:
            handle.write(b"not a directory")
        self.refused(room=place)

    def test_a_refusal_starts_no_provider(self):
        before = len(self.commands)
        self.refused(prompt="")
        self.refused(room="relative/room")
        self.assertEqual(len(self.commands), before)


class TheRemainingWorkloadIsNotBuilt(unittest.TestCase):
    """The absence, asserted rather than described.

    A reviewer reading a green suite should not have to take a prose sentence
    for it: these are the four paths W110935 still owes and they are not on
    disk. When one of them lands this case fails, which is the point -- it is
    the reminder to bring its proof with it.
    """

    def test_the_workload_entry_recipe_and_image_suite_are_absent(self):
        for name in ("integration_workload.py", "integration_entry.py",
                     "Dockerfile.integration"):
            with self.subTest(name=name):
                self.assertFalse((WORKER / name).exists(),
                                 f"{name} exists and this suite does not "
                                 f"prove it")
        suite = (pathlib.Path(__file__).resolve().parent
                 / "test_integration_image.py")
        self.assertFalse(suite.exists(),
                         "the image suite exists and this file still claims "
                         "the joined proof is not built")


if __name__ == "__main__":
    unittest.main()
