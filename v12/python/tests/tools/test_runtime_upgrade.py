"""W386447: the owner-run in-place runtime upgrade of a STOPPED instance.

DETERMINISTIC AND OFFLINE, like `test_instance`: a one-folder runtime is stood in for by a directory of files, the
built command's `identity` answer is substituted, and the durable status read is substituted where a case is about
what the upgrade does with its answer. What is proved is the contract: what is replaced, what is kept, what is
refused before any effect, and how an interrupted upgrade is finished.
"""
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
sys.path.insert(1, str(_DISTRIBUTION / "src"))
from tools import instance, runtime_upgrade, stack, stack_command  # noqa: E402


def stage(name, state, *, episode=1, runtime="destroyed"):
    # THE MEMBERS THE DURABLE STAGE DOCUMENT PUBLISHES (`baton.v12.job-status/9`), not a projection of them: there is
    # no top-level live attempt, only the state, the episode/attempt and the recorded runtime's execution axis.
    return {"stage_id": "job-a/" + name, "state": state, "episode": episode, "attempt_id": "attempt-" + name + str(episode),
            "episodes": [{"episode": n, "attempt_id": "attempt-" + name + str(n), "ended_state": None, "ended_at": None}
                         for n in range(1, episode + 1)],
            "runtime": None if runtime is None else {"runtime_id": "runtime-" + name, "execution_runtime": runtime}}


def document(*stages):
    return {"schema": "baton.v12.job-status/9", "canonical": True, "observed_at": "2026-11-26T00:00:00.000Z",
            "jobs": [{"job_id": "job-a", "stages": list(stages)}]}


def quiet(_settings):
    # M386446's shape: implementation held for the owner, review answered, both runtimes destroyed.
    return document(stage("implementation", "awaiting-answer"), stage("review", "answered"),
                    stage("integration", "blocked", episode=0, runtime=None))


def said(command, runtime, distro):
    return {"frozen": True, "build_stamp": {"commit": "c" * 40}, "sha256": "e" * 64, "command": "baton-v12-stack"}


class Fixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v12-runtime-upgrade-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.destination = str(self.root / "instance")
        self.places = instance.layout(self.destination)
        self.write_runtime(Path(self.places["distro"]), "old")
        for key in ("stores", "repository", "logs", "state"):
            Path(self.places[key]).mkdir(parents=True, exist_ok=True)
        # THE STORES ARE NOT THE RUNTIME'S: a sentinel stands for every byte the upgrade must not touch.
        self.sentinel = Path(self.places["job_store"])
        self.sentinel.write_bytes(b"the held Job's store")
        self.old = instance.manifest(self.places["distro"])
        document = instance.emit(self.destination, authority_uuid="0" * 31 + "a",
                                 identity={"frozen": True, "build_stamp": {"commit": "a" * 40}},
                                 runtime=self.old, now=1.0)
        instance.publish(self.places["instance"], document)
        self.source = self.root / "built" / "distro"
        self.write_runtime(self.source, "new")
        self.new = instance.manifest(self.source)

    def write_runtime(self, distro, which):
        for name in ("baton-v12-stack", "_internal/lib.so"):
            place = distro / name
            place.parent.mkdir(parents=True, exist_ok=True)
            place.write_text("bytes of " + which + " " + name)

    def upgrade(self, **operands):
        stream = io.StringIO()
        operands.setdefault("reader", quiet)
        operands.setdefault("identity_of", said)
        code = runtime_upgrade.upgrade(self.places["instance"], str(self.source), stream=stream,
                                       now=lambda: "2026-11-26T00:00:00.000Z", **operands)
        return code, stream.getvalue()

    def refused(self, **operands):
        with self.assertRaises(runtime_upgrade.UpgradeRefusal) as raised:
            self.upgrade(**operands)
        return str(raised.exception)

    def assertUnchanged(self):
        self.assertEqual(instance.manifest(self.places["distro"])["digest"], self.old["digest"])
        self.assertEqual(instance.read(self.places["instance"])["runtime"]["digest"], self.old["digest"])
        self.assertFalse((Path(self.destination) / runtime_upgrade.INTENT).exists())
        self.assertFalse((Path(self.destination) / runtime_upgrade.HISTORY).exists())
        self.assertEqual([one.name for one in Path(self.destination).iterdir() if one.name.startswith("distro")],
                         ["distro"])
        self.assertEqual(self.sentinel.read_bytes(), b"the held Job's store")

    def retired(self):
        return Path(self.destination) / ("distro.retired-" + self.old["digest"][:16])


class TheRuntimeIsReplacedAndEverythingElseIsKept(Fixture):

    def test_the_new_runtime_is_installed_and_the_old_one_retired(self):
        code, said_out = self.upgrade()
        self.assertEqual(code, 0, said_out)
        self.assertEqual(instance.manifest(self.places["distro"])["digest"], self.new["digest"])
        self.assertEqual(instance.manifest(self.retired())["digest"], self.old["digest"])
        selector = instance.read(self.places["instance"])
        self.assertEqual(selector["runtime"], {"files": self.new["files"], "digest": self.new["digest"]})
        self.assertEqual(selector["identity"]["build_stamp"]["commit"], "c" * 40)
        # The selector's other members, the stores and the configuration places are exactly as they were.
        self.assertEqual({k: v for k, v in selector.items() if k not in ("identity", "runtime")},
                         {k: v for k, v in instance.emit(self.destination, authority_uuid="0" * 31 + "a",
                                                         identity={}, runtime=self.old, now=1.0).items()
                          if k not in ("identity", "runtime")})
        self.assertEqual(self.sentinel.read_bytes(), b"the held Job's store")
        instance.verify(selector)
        [record] = (Path(self.destination) / runtime_upgrade.HISTORY).read_text().splitlines()
        record = json.loads(record)
        self.assertEqual((record["from"]["runtime"]["digest"], record["to"]["runtime"]["digest"]),
                         (self.old["digest"], self.new["digest"]))
        self.assertFalse((Path(self.destination) / runtime_upgrade.INTENT).exists())
        self.assertIn("retired runtime kept at", said_out)

    def test_a_repeat_is_an_ordinary_unchanged_answer(self):
        self.upgrade()
        code, said_out = self.upgrade()
        self.assertEqual(code, 0)
        self.assertIn("already runs runtime", said_out)
        self.assertEqual(len((Path(self.destination) / runtime_upgrade.HISTORY).read_text().splitlines()), 1)

    def test_the_installed_command_reaches_it(self):
        self.assertIn("upgrade-runtime", stack_command.COMMANDS)
        stream = io.StringIO()
        with mock.patch("tools.job_status.read", quiet), mock.patch("tools.bootstrap._identity_of", said):
            code = stack.main(["--instance", self.places["instance"], "upgrade-runtime", "--distro",
                               str(self.source)], stream=stream)
        self.assertEqual(code, 0, stream.getvalue())
        self.assertEqual(instance.read(self.places["instance"])["runtime"]["digest"], self.new["digest"])

    def test_a_refusal_through_the_command_is_said_and_changes_nothing(self):
        stream = io.StringIO()
        with mock.patch("tools.job_status.read", side_effect=RuntimeError("no such table")), \
                mock.patch("tools.bootstrap._identity_of", said):
            code = stack.main(["--instance", self.places["instance"], "upgrade-runtime", "--distro",
                               str(self.source)], stream=stream)
        self.assertEqual(code, 2)
        self.assertIn("refused: this runtime cannot read the instance's stores", stream.getvalue())
        self.assertUnchanged()


class NothingIsReplacedUnderSomethingRunning(Fixture):

    def test_a_live_supervisor_refuses(self):
        for answer in (stack.LIVE, stack.UNKNOWN):
            with self.subTest(answer=answer), mock.patch.object(
                    stack, "ownership", side_effect=lambda record, a=answer: a):
                self.assertIn("is " + answer, self.refused())
                self.assertUnchanged()

    def test_a_held_and_quiescent_job_is_settled(self):
        self.assertEqual(runtime_upgrade.unresolved(quiet(None)), [])

    def test_a_waiting_attempt_refuses(self):
        # Review 2026-11-27 [1]: the resumed implementation waiting with a named attempt and no runtime yet -- the
        # interrupted fixture's real document -- carries no `live_attempt` member and was accepted.
        def waiting(_settings):
            return document(stage("implementation", "waiting", episode=2, runtime=None), stage("review", "answered"))
        said_out = self.refused(reader=waiting)
        self.assertIn("job-a/implementation is waiting", said_out)
        self.assertUnchanged()

    def test_every_executing_or_unknown_phase_refuses(self):
        cases = {"running": document(stage("implementation", "running", episode=2, runtime="running")),
                 "starting": document(stage("implementation", "starting", episode=2, runtime=None)),
                 "offered": document(stage("review", "offered", episode=2, runtime=None)),
                 "a state this code does not know": document(stage("implementation", "resuming")),
                 "a held phase whose runtime still runs": document(stage("implementation", "awaiting-answer",
                                                                         runtime="running")),
                 "a held phase whose container is still there": document(stage("review", "answered",
                                                                               runtime="quiescent")),
                 "an uncertain runtime": document(stage("implementation", "awaiting-answer", runtime="uncertain")),
                 "a runtime with no execution axis": document(dict(stage("implementation", "awaiting-answer"),
                                                                   runtime={"runtime_id": "r"})),
                 "a partial document": dict(quiet(None), canonical=False),
                 "no Jobs member": {"canonical": True}}
        for name, answer in cases.items():
            with self.subTest(name):
                self.assertNotEqual(runtime_upgrade.unresolved(answer), [])
                self.assertIn("not settled", self.refused(reader=lambda _s, a=answer: a))
                self.assertUnchanged()

    def test_stores_this_runtime_cannot_read_refuse(self):
        def unreadable(_settings):
            raise ValueError("unknown schema version 99")
        self.assertIn("unknown schema version 99", self.refused(reader=unreadable))
        self.assertUnchanged()

    def test_the_lifecycle_lock_is_held_throughout(self):
        held = []

        def reading(settings):
            # A start racing the upgrade meets the same exclusive lock and is refused.
            with self.assertRaises(stack.StackRefusal):
                with stack.admission(Path(self.places["state"]), wait=0.1):
                    pass
            held.append(True)
            return quiet(settings)
        self.assertEqual(self.upgrade(reader=reading)[0], 0)
        self.assertEqual(held, [True])


class WhatIsNotIdentifiedIsNotReplaced(Fixture):

    def test_an_installed_runtime_that_is_not_the_recorded_one_refuses(self):
        (Path(self.places["distro"]) / "_internal" / "lib.so").write_text("tampered")
        self.assertIn("is not the one this instance records", self.refused())

    def test_a_source_that_is_not_a_frozen_bundle_refuses(self):
        from tools import bootstrap

        def unfrozen(*_a):
            raise bootstrap.BootstrapRefusal("the command at x is not a frozen build")
        self.assertIn("not a frozen build", self.refused(identity_of=unfrozen))
        self.assertUnchanged()

    def test_a_frozen_command_must_be_the_runtime_it_installs(self):
        with mock.patch.object(stack_command, "frozen", return_value=True), \
                mock.patch.object(stack_command, "executable",
                                  return_value=os.path.join(self.places["distro"], "baton-v12-stack")):
            self.assertIn("installs itself", self.refused())
        self.assertUnchanged()

    def test_a_foreign_staging_directory_refuses(self):
        staging = Path(self.destination) / ("distro.upgrade-" + self.new["digest"][:16])
        self.write_runtime(staging, "somebody else's")
        self.assertIn("is not this runtime", self.refused())
        self.assertEqual(instance.manifest(self.places["distro"])["digest"], self.old["digest"])


class AnInterruptedUpgradeIsFinishedByTheNextOne(Fixture):

    def test_a_crash_between_retiring_and_installing_rolls_forward(self):
        renames = []
        real = os.rename

        def failing(source, target):
            renames.append((source, target))
            if len(renames) == 2:
                raise OSError("interrupted")
            return real(source, target)
        with mock.patch.object(os, "rename", failing):
            with self.assertRaises(OSError):
                self.upgrade()
        # The runtime is aside, the new one staged, the intent durable and the selector not yet republished.
        self.assertFalse(os.path.lexists(self.places["distro"]))
        self.assertTrue((Path(self.destination) / runtime_upgrade.INTENT).exists())
        self.assertEqual(instance.read(self.places["instance"])["runtime"]["digest"], self.old["digest"])
        reads = []
        code, said_out = self.upgrade(reader=lambda s: reads.append(s) or quiet(s))
        self.assertEqual(code, 0, said_out)
        self.assertEqual(len(reads), 1, "a resumed upgrade rereads the stores under the lock")
        self.assertIn("resuming", said_out)
        self.assertEqual(instance.manifest(self.places["distro"])["digest"], self.new["digest"])
        self.assertEqual(instance.read(self.places["instance"])["runtime"]["digest"], self.new["digest"])
        self.assertEqual(instance.manifest(self.retired())["digest"], self.old["digest"])
        self.assertFalse((Path(self.destination) / runtime_upgrade.INTENT).exists())

    def test_a_crash_after_the_selector_still_completes_once(self):
        real = instance.publish
        calls = []

        def publishing(place, document):
            real(place, document)
            calls.append(place)
            if str(place) == self.places["instance"]:
                raise OSError("interrupted after publishing")
        with mock.patch.object(instance, "publish", publishing):
            with self.assertRaises(OSError):
                self.upgrade()
        code, said_out = self.upgrade()
        self.assertEqual(code, 0, said_out)
        self.assertEqual(len((Path(self.destination) / runtime_upgrade.HISTORY).read_text().splitlines()), 1)
        self.assertEqual(instance.read(self.places["instance"])["runtime"]["digest"], self.new["digest"])

    def interrupt_after_retiring(self):
        renames = []
        real = os.rename

        def failing(source, target):
            renames.append(source)
            if len(renames) == 2:
                raise OSError("interrupted")
            return real(source, target)
        with mock.patch.object(os, "rename", failing), self.assertRaises(OSError):
            self.upgrade()
        self.assertTrue((Path(self.destination) / runtime_upgrade.INTENT).exists())

    def assertHeldPending(self):
        # Nothing more was done: the old runtime aside, the new one still staged, the intent kept, no history.
        self.assertFalse(os.path.lexists(self.places["distro"]))
        self.assertEqual(instance.read(self.places["instance"])["runtime"]["digest"], self.old["digest"])
        self.assertTrue((Path(self.destination) / runtime_upgrade.INTENT).exists())
        self.assertFalse((Path(self.destination) / runtime_upgrade.HISTORY).exists())

    def test_a_pending_intent_does_not_finish_under_a_supervisor_started_since(self):
        # Review 2026-11-27 [1]: the intent is not a licence; a stack running NOW refuses the remaining mutations.
        self.interrupt_after_retiring()
        for answer in (stack.LIVE, stack.UNKNOWN):
            with self.subTest(answer=answer), mock.patch.object(stack, "ownership", side_effect=lambda r, a=answer: a):
                self.assertIn("is " + answer, self.refused())
                self.assertHeldPending()

    def test_a_pending_intent_does_not_finish_over_an_executing_phase(self):
        self.interrupt_after_retiring()
        waiting = document(stage("implementation", "waiting", episode=2, runtime=None))
        self.assertIn("job-a/implementation is waiting", self.refused(reader=lambda _s: waiting))
        self.assertHeldPending()
        self.assertEqual(self.upgrade()[0], 0)

    def test_a_pending_intent_is_finished_only_by_the_runtime_it_installs(self):
        self.interrupt_after_retiring()
        self.write_runtime(self.source, "a third build")
        self.assertIn("is not that runtime", self.refused())
        self.assertHeldPending()

    def test_an_interruption_after_the_history_append_completes_once(self):
        # Review 2026-11-27 [2]: the cut at the intent's removal, after the record was committed.
        real = os.unlink

        def failing(place, *a, **k):
            if Path(place).name == runtime_upgrade.INTENT:
                raise OSError("interrupted before the intent was removed")
            return real(place, *a, **k)
        with mock.patch.object(os, "unlink", failing), self.assertRaises(OSError):
            self.upgrade()
        journal = Path(self.destination) / runtime_upgrade.HISTORY
        [committed] = journal.read_text().splitlines()
        self.assertTrue((Path(self.destination) / runtime_upgrade.INTENT).exists())
        code, said_out = self.upgrade()
        self.assertEqual(code, 0, said_out)
        self.assertEqual(journal.read_text().splitlines(), [committed], "the committed record is reused, not repeated")
        self.assertTrue(json.loads(committed)["upgrade_id"].startswith("runtime-upgrade:"))
        self.assertFalse((Path(self.destination) / runtime_upgrade.INTENT).exists())
        self.assertEqual(self.upgrade()[1].count("already runs runtime"), 1)
        self.assertEqual(len(journal.read_text().splitlines()), 1)

    def test_a_torn_history_line_is_not_a_completion(self):
        self.interrupt_after_retiring()
        journal = Path(self.destination) / runtime_upgrade.HISTORY
        journal.write_text('{"upgrade_id": "runtime-upgrade:tor')
        self.assertEqual(self.upgrade()[0], 0)
        lines = journal.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertEqual(json.loads(lines[1])["to"]["runtime"]["digest"], self.new["digest"])

    def test_a_staged_copy_left_by_an_earlier_attempt_is_reused(self):
        from tools import bootstrap

        staging = Path(self.destination) / ("distro.upgrade-" + self.new["digest"][:16])
        bootstrap.copy_runtime(str(self.source), str(staging), made={})
        self.assertEqual(self.upgrade()[0], 0)
        self.assertEqual(instance.manifest(self.places["distro"])["digest"], self.new["digest"])

    def test_an_intent_for_another_runtime_is_left_alone(self):
        (Path(self.destination) / runtime_upgrade.INTENT).write_text(json.dumps({
            "schema": runtime_upgrade.SCHEMA, "from": {"runtime": {"digest": "f" * 64}},
            "to": {"runtime": {"digest": "9" * 64}}}))
        self.assertIn("does not describe an upgrade of this selector's runtime", self.refused())
        self.assertEqual(instance.manifest(self.places["distro"])["digest"], self.old["digest"])


if __name__ == "__main__":
    unittest.main()
