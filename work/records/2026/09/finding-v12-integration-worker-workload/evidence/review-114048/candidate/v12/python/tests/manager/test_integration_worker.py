"""W110935: the integration worker, from the provider wrapper to the ending.

`work/records/2026/09/finding-v12-integration-worker-workload/`.

WHAT THIS FILE OWNS. Two things, and they are stages of one capability.

FIRST, the additive provider wrapper. `ClaudeAgent` gained one public name,
`invoke_provider`, so the integration workload can take a provider turn without
growing a second copy of the credential, environment, drain and failure rules
this adapter already owns. Those cases drive the wrapper through the REAL
adapter with the accepted injected-process seam -- the same seam
`test_claude_agent` uses, imported from its own suite and never edited -- and
prove that it reaches the same composed argv, the same composed environment and
the same closed answer as the private turn beneath it.

SECOND, THE JOINED PROOF, which is what this Work is actually for. An ACCEPTED
PRODUCER BUNDLE -- composed by `tools/integration_bundle.compose_bundle` from
the real admission world, not a fixture shaped like one -- is carried through
the real `integration_entry` into a provider-driven import of a DISPOSABLE
target, with an injected provider PROCESS that performs actual filesystem
edits, this module's own independent read-back of bytes and modes, and the
manager's own `runtime.observed_delivery` parsing the published result. The
negatives are here for the same reason the positive is: a whole-path preflight
refusal that starts no provider at all, and the conservative held endings a
failure after writable work produces.

WHERE A DERIVED BUNDLE IS USED AND WHY IT IS SAID OUT LOUD. The accepted
world's checkpoint carries ONE reviewed path, so a case about a SECOND row --
a late invalid member that must not follow an earlier valid one -- cannot be
composed from it. Those cases republish a bundle DERIVED from the real one
with exactly one declared difference, through the same contract readers. Every
positive import, every identity comparison and every evidence case runs against
the producer's own published bytes.

WHAT IS STILL NOT PROVED HERE, said rather than left to be inferred: no image
is built, no container is started, no credential is mounted and no live
provider is called. `test_integration_image` asks the recipe and the packaged
layout, and building or selecting an artefact remains a deployment act this
suite does not perform.
"""

import hashlib
import json
import os
import pathlib
import shutil
import stat
import subprocess
import sys
import tempfile
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

import baton_worker                                     # noqa: E402
import claude_agent                                    # noqa: E402
import integration_contract as contract                 # noqa: E402
import integration_entry                                # noqa: E402
import integration_workload as workload                 # noqa: E402


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


# -- the two spellings of one canonical form ---------------------------------


class TheTwoSpellingsOfCanonicalJsonAgree(unittest.TestCase):
    """The worker cannot import `contracts.canonical`, so it agrees with it.

    THE MANIFEST DIGEST AND THE ACCEPTED PATH-SET DIGEST ARE BOTH TAKEN OVER
    THIS FORM, on two sides of a boundary a container cannot cross. A
    conformance case is the mechanism this campaign already uses for exactly
    that problem, and it fails the moment either side moves -- which a comment
    saying "the same rules" would not.
    """

    def agreed(self, value):
        from baton_v12.contracts import digest
        from baton_v12.contracts.canonical import canonical_text

        self.assertEqual(workload.canonical_text(value),
                         canonical_text(value))
        self.assertEqual(workload.canonical_digest(value), digest(value))

    def test_a_publication_manifest_digests_identically(self):
        self.agreed([{"path": "blobs/" + "a" * 64, "bytes": 23,
                      "digest": "sha256:" + "b" * 64},
                     {"path": "integration.json", "bytes": 4096,
                      "digest": "sha256:" + "c" * 64}])

    def test_an_assignment_a_launch_and_a_path_list_digest_identically(self):
        self.agreed({"schema": contract.ASSIGNMENT_SCHEMA, "fence": 1,
                     "attempt_id": "attempt-1", "target_access": "writable"})
        self.agreed({"schema": workload.LAUNCH_SCHEMA, "session": "token",
                     "contract": "baton.worker-control/1",
                     "role": "integrator"})
        self.agreed(["src/a.py", "src/b.py", "z.txt"])

    def test_member_order_nesting_and_unicode_agree(self):
        self.agreed({"z": 1, "a": {"nested": [True, False, None, 0]},
                     "é": "café", "\U0001f600": "above the bmp",
                     "tab\t": "line\nbreak"})

    def test_the_worker_and_the_manager_name_one_target_mount(self):
        """The fourth fixed container path, held equal across the boundary.

        The worker cannot import the manager, so the constant is spelled twice
        and this is the mechanism that keeps the two spellings one decision --
        the same one the child's suite uses for the assignment and result
        namespaces.
        """
        from baton_v12.integration import oci_delivery

        self.assertEqual(integration_entry.TARGET_TARGET,
                         oci_delivery.TARGET_TARGET)
        self.assertEqual(workload.INTEGRATION_ROLE, "integrator")
        self.assertEqual(workload.LAUNCH_SCHEMA, baton_worker.LAUNCH_SCHEMA)
        self.assertEqual(list(workload.LAUNCH_MEMBERS),
                         list(baton_worker.LAUNCH_MEMBERS))

    def test_what_neither_spelling_will_digest(self):
        for value in (1.5, -1, {1: "a numeric member name"}, {"a", "set"}):
            with self.subTest(value=repr(value)):
                with self.assertRaises(workload.WorkloadRefusal):
                    workload.canonical_digest(value)


# -- the injected provider, which is a real process --------------------------

# IT PERFORMS ACTUAL EDITS AND IT IS NOT THE WORKLOAD. A canned host-side
# copier inside the test process would prove the read-back and nothing about
# the turn: this is a separate program, started through the adapter's own
# process seam with the adapter's own composed environment and working
# directory, and everything it knows about what to import it reads out of the
# PROMPT. That is deliberate -- a prompt that failed to carry the bundle root,
# the report path or the path table would fail these cases here rather than in
# a live turn nobody can reproduce.
PROVIDER_SOURCE = '''"""The injected provider for W110935's joined proof."""

import json
import os
import sys


def rows_and_facts(prompt):
    facts, rows = {}, []
    for line in prompt.splitlines():
        if line.startswith("The approved evidence bundle is mounted"):
            facts["bundle"] = line.rsplit(" at ", 1)[1].rstrip(".")
        elif line.startswith("Its measured identity is "):
            facts["bundle_digest"] = line.rsplit(" is ", 1)[1].rstrip(".")
        elif line.startswith("The assignment it answers is "):
            facts["assignment_digest"] = line.rsplit(" is ", 1)[1].rstrip(".")
        elif line.startswith("Write your bounded "):
            facts["report"] = line.split(" report to ", 1)[1].split(" and ")[0]
        elif line[:2] == "  " and line.split(" ")[2:]:
            head = line[2:]
            operation, rest = head.split(" ", 1)
            if operation not in ("add", "edit", "delete"):
                continue
            candidate = base = None
            if " to candidate " in rest:
                rest, tail = rest.split(" to candidate ", 1)
                address, mode = tail.split(" mode ")
                candidate = {"blob": address, "mode": mode}
            if " from base " in rest:
                rest, tail = rest.split(" from base ", 1)
                address, mode = tail.split(" mode ")
                base = {"blob": address, "mode": mode}
            rows.append({"operation": operation, "path": rest, "base": base,
                         "candidate": candidate})
    return facts, rows


def imported(facts, row):
    """One reviewed path, imported into the working directory this runs in."""
    if row["candidate"] is None:
        os.unlink(row["path"])
        return
    with open(os.path.join(facts["bundle"], "blobs",
                           row["candidate"]["blob"]), "rb") as handle:
        payload = handle.read()
    if os.path.dirname(row["path"]):
        os.makedirs(os.path.dirname(row["path"]), exist_ok=True)
    with open(row["path"], "wb") as handle:
        handle.write(payload)
    os.chmod(row["path"],
             0o755 if row["candidate"]["mode"] == "100755" else 0o644)


def main():
    behaviour, prompt = sys.argv[1], sys.argv[2]
    facts, rows = rows_and_facts(prompt)
    done = []
    if behaviour != "refuse":
        for row in rows if behaviour != "partial" else rows[:1]:
            imported(facts, row)
            done.append(row["path"])
    if behaviour == "index":
        with open(os.path.join(".git", "index"), "ab") as handle:
            handle.write(b"a provider does not write here")
    if behaviour == "silent":
        return 0
    if behaviour == "malformed":
        with open(facts["report"], "wb") as handle:
            handle.write(b"{this is not one readable document")
        return 0
    report = {"schema": "baton.integration-report/1",
              "assignment_digest": facts["assignment_digest"],
              "bundle_digest": facts["bundle_digest"],
              "outcome": "imported", "phase": "verification",
              "paths": sorted(row["path"] for row in rows),
              "verification": {"argv": ["python3", "-m", "compileall", "-q",
                                        "."], "status": 0},
              "code": None}
    if behaviour == "foreign":
        report["bundle_digest"] = "sha256:" + "f" * 64
    if behaviour == "outside":
        report["paths"] = sorted(report["paths"] + ["somebody/elses.py"])
    if behaviour == "refuse":
        report.update({"outcome": "refused", "phase": "preflight",
                       "paths": [], "verification": None,
                       "code": "target-drift"})
    if behaviour == "unclaimed":
        report.update({"outcome": "held", "phase": "import",
                       "code": "provider-unable"})
    with open(facts["report"], "w", encoding="utf-8") as handle:
        json.dump(report, handle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


class WorldCase(unittest.TestCase):
    """The real admission world, one published bundle, a disposable target.

    COMPOSED, NOT SUBCLASSED, and the imports are inside the method: a
    module-level `TestCase` binding is collected by the loader and a subclass
    re-runs every one of its parent's cases under a second name. Both
    inflations happened in this campaign and both are avoided deliberately.
    """

    def setUp(self):
        from baton_v12.integration import runtime
        from tests.manager.test_claude_agent import AdapterCase
        from tests.tools.test_integration_bundle import ProducerCase

        self.runtime = runtime
        self.owner = AdapterCase("run")
        self.owner.setUp()
        self.addCleanup(self.owner.doCleanups)
        self.producer = ProducerCase("run")
        self.producer.setUp()
        self.addCleanup(self.producer.doCleanups)

        self.root = tempfile.mkdtemp(prefix="v12-w110935-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.commands = []
        self.behaviour = "import"
        self.status = 0
        self.timeout = False
        self.script = os.path.join(self.root, "provider.py")
        with open(self.script, "w", encoding="utf-8") as handle:
            handle.write(PROVIDER_SOURCE)
        self.agent = claude_agent.ClaudeAgent(run=self.runner,
                                              home=self.place("agent"))
        self.scratch = self.place("scratch")

        self.assignment = self.producer.assignment
        self.launch = self.producer.launch
        self.launch_place = os.path.join(self.place("run"), "launch.json")
        with open(self.launch_place, "w", encoding="utf-8") as handle:
            json.dump(self.launch, handle)
        # READ-ONLY FOR THIS PROCESS'S OWN VIEW, which is what `read_launch`
        # proves by attempting a write-open. A launch document the worker could
        # rewrite is one it could change between reading it and being held to
        # it, and the real deployment mounts it read-only.
        os.chmod(self.launch_place, 0o444)
        self.delivery = runtime.IntegrationDelivery(
            attempt_id=self.assignment["attempt_id"],
            root=self.place("delivery"))
        os.makedirs(self.delivery.assignment_root)
        os.makedirs(self.delivery.result_root)
        runtime.publish_assignment(self.delivery, self.assignment)

    # -- the world's own material -------------------------------------------

    def place(self, *parts):
        made = os.path.join(self.root, *parts)
        os.makedirs(made, exist_ok=True)
        return made

    def reviewed(self):
        """The one path the accepted checkpoint actually carries."""
        return self.producer.evidence()["paths"][0]

    def bundle(self, *, operation="add", mode="100644", name="bundle"):
        """One REAL published bundle, whose single row is this operation.

        The accepted checkpoint's path list is the world's and is not composed
        here; what these choose is which retained trees the producer reads it
        out of, which is what makes the row an add, an edit or a delete.
        """
        from tests.tools.test_integration_bundle import BASE_TREE

        held = self.producer.world.owner.observed
        path = self.reviewed()
        base = ({path: ("100644", self.ORIGINAL)}
                if operation in ("edit", "delete") else {})
        head = ({path: (mode, self.CANDIDATE)}
                if operation in ("edit", "add") else {})
        self.producer.objects.tree(BASE_TREE, base)
        self.producer.objects.tree(held["tree"], head)
        answer = self.producer.compose(
            destination=os.path.join(self.root, name))
        self.published = answer
        return answer["root"]

    ORIGINAL = b"the reviewed base\n"
    CANDIDATE = b"the reviewed candidate\n"

    def target(self, *, entries=(), repository=True, name="target"):
        """One disposable tree, optionally a real version-controlled one."""
        place = self.place(name)
        for relative, payload, mode in entries:
            whole = os.path.join(place, relative)
            os.makedirs(os.path.dirname(whole), exist_ok=True)
            with open(whole, "wb") as handle:
                handle.write(payload)
            os.chmod(whole, mode)
        if repository:
            self.initialized(place)
        return place

    def initialized(self, place):
        """A real repository, so `.git` is a thing this proof can watch."""
        home = self.place("version-control-home")
        environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                       "HOME": home, "GIT_CONFIG_GLOBAL": "/dev/null",
                       "GIT_CONFIG_SYSTEM": "/dev/null"}
        for arguments in (["init", "-q", "-b", "main"],
                          ["add", "-A"],
                          ["-c", "user.email=w110935@example.invalid",
                           "-c", "user.name=W110935", "commit", "-q",
                           "--allow-empty", "-m", "the reviewed base"]):
            done = subprocess.run(["git", "-C", place, *arguments],
                                  capture_output=True, timeout=300,
                                  env=environment)
            self.assertEqual(done.returncode, 0, done.stderr)
        return place

    def expected(self):
        """The revision the accepted eligibility account names."""
        taken = contract.read_bundle(self.published["root"])
        return taken["envelope"]["eligibility"]["expected_target_revision"]

    # -- the injected provider ----------------------------------------------

    def runner(self, argv, **options):
        """The adapter's one process seam, running a REAL provider child."""
        self.commands.append({"argv": list(argv), "cwd": options.get("cwd"),
                              "env": dict(options.get("env") or {})})
        if self.timeout:
            raise subprocess.TimeoutExpired(list(argv), 1)
        if self.behaviour is None:
            return subprocess.CompletedProcess(list(argv), self.status, None,
                                               None)
        done = subprocess.run(
            [sys.executable, "-I", "-B", self.script, self.behaviour,
             argv[-1]],
            cwd=options.get("cwd"), env=dict(options.get("env") or {}),
            stdout=options.get("stdout"), stderr=options.get("stderr"),
            timeout=options.get("timeout"))
        return subprocess.CompletedProcess(
            list(argv), self.status or done.returncode, None, None)

    # -- driving the real entry ---------------------------------------------

    def entry(self, *, bundle=None, target=None, revision=None,
              result_root=None, agent=None):
        return integration_entry.main(
            agent=self.agent if agent is None else agent,
            launch_place=self.launch_place,
            assignment_root=self.delivery.assignment_root,
            result_root=(self.delivery.result_root if result_root is None
                         else result_root),
            bundle_root=self.published["root"] if bundle is None else bundle,
            target_root=target, scratch=self.scratch,
            revision=revision if revision is not None
            else (lambda place: self.expected()))

    def observed(self):
        """The manager's OWN reader, over the bytes this worker published."""
        return self.runtime.observed_delivery(self.delivery, self.assignment)

    def ending(self, status, outcome, reason=None):
        self.assertEqual(status, 0)
        observed = self.observed()
        self.assertEqual(observed["state"], "answered", observed)
        result = observed["result"]
        self.assertEqual(result["outcome"], outcome, result["detail"])
        if reason is not None:
            self.assertEqual(result["detail"]["reason"], reason,
                             result["detail"])
        return result

    def contents(self, place, relative):
        whole = os.path.join(place, relative)
        with open(whole, "rb") as handle:
            return handle.read(), stat.S_IMODE(os.stat(whole).st_mode)

    # -- a bundle DERIVED from the real one ---------------------------------

    def derived(self, *, paths=None, documents=None, eligibility=None,
                envelope=None, blobs=None, extra=None, name="derived"):
        """Republish the real bundle with exactly the declared difference.

        USED ONLY WHERE THE ACCEPTED WORLD CANNOT COMPOSE THE CASE -- a second
        path row, an evidence document that contradicts its account, a file the
        envelope never named. Everything else in this suite runs against the
        producer's own published bytes, and each case that uses this says so.
        """
        from baton_v12.contracts import digest
        from baton_v12.contracts.canonical import canonical_bytes

        source = self.published["root"]
        taken = contract.read_bundle(source)
        composed = dict(taken["envelope"])
        held = dict(taken["evidence"])
        held.update(documents or {})
        rows = composed["paths"] if paths is None else paths
        if paths is not None:
            names = [one["path"] for one in rows]
            account = dict(composed["eligibility"],
                           path_set_digest=digest(names))
            checkpoint = dict(composed["checkpoint"])
            checkpoint["evidence"] = dict(checkpoint["evidence"],
                                          paths=names,
                                          path_set_digest=digest(names))
            composed["eligibility"] = account
            composed["checkpoint"] = checkpoint
            held["checkpoint.json"] = dict(
                held["checkpoint.json"], path_set_digest=digest(names),
                evidence=checkpoint["evidence"])
        composed["paths"] = rows
        if eligibility is not None:
            composed["eligibility"] = dict(composed["eligibility"],
                                           **eligibility)
        composed.update(envelope or {})

        place = os.path.join(self.root, name)
        os.makedirs(os.path.join(place, contract.EVIDENCE_DIRECTORY))
        os.makedirs(os.path.join(place, contract.BLOB_DIRECTORY))
        references = []
        for one in contract.EVIDENCE_DOCUMENTS:
            body = canonical_bytes(held[one])
            references.append({"name": one, "bytes": len(body),
                               "digest": hashlib.sha256(body).hexdigest()})
            self.wrote(place, (contract.EVIDENCE_DIRECTORY, one), body)
        composed["evidence"] = references
        for row in rows:
            for side in (row["base"], row["candidate"]):
                if side is None:
                    continue
                payload = (blobs or {}).get(side["blob"])
                if payload is None:
                    with open(os.path.join(source, contract.BLOB_DIRECTORY,
                                           side["blob"]), "rb") as handle:
                        payload = handle.read()
                self.wrote(place, (contract.BLOB_DIRECTORY, side["blob"]),
                           payload)
        self.wrote(place, (contract.INSTRUCTIONS_DOCUMENT,),
                   taken["instructions"])
        self.wrote(place, (contract.ENVELOPE_DOCUMENT,),
                   canonical_bytes(composed))
        if extra is not None:
            self.wrote(place, extra[0], extra[1])
        return place

    @staticmethod
    def wrote(place, parts, payload):
        whole = os.path.join(place, *parts)
        with open(whole, "wb") as handle:
            handle.write(payload)
        return whole

    ROW_BASE = b"one synthetic reviewed base\n"
    ROW_CANDIDATE = b"one synthetic reviewed candidate\n"

    def row(self, path, *, operation="add", mode="100644"):
        """One synthetic path row and the blobs it names.

        THE TWO SIDES ARE DIFFERENT CONTENT, because an edit whose sides agree
        is a row the producer refuses to compose and would make a case about
        importing prove nothing.
        """
        blobs, sides = {}, {}
        for name, payload in (("base", self.ROW_BASE),
                              ("candidate", self.ROW_CANDIDATE)):
            address = hashlib.sha256(payload).hexdigest()
            blobs[address] = payload
            sides[name] = {"object": "0" * 40, "blob": address,
                           "bytes": len(payload), "mode": mode}
        return ({"path": path, "operation": operation,
                 "base": (sides["base"]
                          if operation in ("edit", "delete") else None),
                 "candidate": (sides["candidate"]
                               if operation in ("edit", "add") else None)},
                blobs)


class TheAcceptedBundleIsCarriedThroughTheRealEntry(WorldCase):
    """The positive path, end to end, over the producer's own bytes."""

    def test_an_addition_is_imported_verified_and_published(self):
        self.bundle(operation="add")
        target = self.target()
        status = self.entry(target=target)
        result = self.ending(status, "integrated")
        # THE MANAGER'S OWN READER PARSED IT, and its identities are the
        # assignment's rather than anything the provider supplied.
        for name in ("attempt_id", "lease_id", "canonical_target_id",
                     "entry_id", "fence"):
            self.assertEqual(result[name], self.assignment[name])
        self.assertEqual(result["detail"]["imported_paths"],
                         [self.reviewed()])
        self.assertEqual(result["detail"]["verification"]["status"], 0)
        # AND THE TARGET REALLY CARRIES THE CANDIDATE, read back here rather
        # than taken from the result this same run composed.
        self.assertEqual(self.contents(target, self.reviewed()),
                         (self.CANDIDATE, 0o644))

    def test_an_edit_preserves_the_reviewed_mode_and_an_executable_one(self):
        for mode, expected in (("100644", 0o644), ("100755", 0o755)):
            with self.subTest(mode=mode):
                self.setUp()
                self.bundle(operation="edit", mode=mode)
                target = self.target(entries=[(self.reviewed(),
                                               self.ORIGINAL, 0o644)])
                self.ending(self.entry(target=target), "integrated")
                self.assertEqual(self.contents(target, self.reviewed()),
                                 (self.CANDIDATE, expected))

    def test_a_deletion_is_imported_as_an_absence(self):
        self.bundle(operation="delete")
        target = self.target(entries=[(self.reviewed(), self.ORIGINAL,
                                       0o644)])
        self.ending(self.entry(target=target), "integrated")
        self.assertFalse(os.path.exists(os.path.join(target,
                                                     self.reviewed())))

    def test_the_version_control_metadata_is_untouched(self):
        """`.git/index` and `HEAD` are exactly what they were.

        The candidate cannot name a path inside `.git` -- `check_bundle_path`
        refuses one -- and this asks the FILESYSTEM whether the turn kept that
        promise rather than asking the report.
        """
        self.bundle(operation="add")
        target = self.target()
        before = {name: pathlib.Path(target, ".git", name).read_bytes()
                  for name in ("HEAD",)}
        index = pathlib.Path(target, ".git", "index")
        held = index.read_bytes() if index.exists() else None
        self.ending(self.entry(target=target), "integrated")
        for name, payload in before.items():
            self.assertEqual(pathlib.Path(target, ".git", name).read_bytes(),
                             payload)
        self.assertEqual(index.read_bytes() if index.exists() else None, held)

    def test_the_provider_ran_in_the_target_with_the_composed_environment(self):
        self.bundle(operation="add")
        self.ending(self.entry(target=self.target()), "integrated")
        self.assertEqual(len(self.commands), 1)
        composed = self.commands[0]
        self.assertEqual(composed["cwd"], os.path.join(self.root, "target"))
        self.assertEqual(composed["argv"][0], claude_agent.PROVIDER_PROGRAM)
        for name in ("ANTHROPIC_API_KEY", "PYTHONPATH", "GIT_CONFIG_GLOBAL"):
            self.assertNotIn(name, composed["env"])
        # THE PROMPT CARRIES THE INSTRUCTION BYTES AND THE TABLE, and NEVER
        # this container's launch session, which is a live credential.
        prompt = composed["argv"][-1]
        self.assertIn(self.reviewed(), prompt)
        self.assertIn(self.published["bundle_digest"], prompt)
        self.assertNotIn(self.launch["session"], prompt)

    def test_a_terminal_result_never_earns_a_second_provider_turn(self):
        self.bundle(operation="add")
        target = self.target()
        self.ending(self.entry(target=target), "integrated")
        published = workload.existing_result(self.delivery.result_root)
        self.assertEqual(len(self.commands), 1)
        # A SECOND RUN OF THE SAME DELIVERY, which finds the answer already
        # there and does not start anything.
        self.assertEqual(self.entry(target=target), 0)
        self.assertEqual(len(self.commands), 1)
        self.assertEqual(workload.existing_result(self.delivery.result_root),
                         published)


class TheBundleIdentityIsMeasuredAndNotRead(WorldCase):
    """`bundle_digest` is the producer's whole-file manifest, recomputed."""

    def test_the_measured_identity_is_the_producers_own_answer(self):
        root = self.bundle(operation="edit")
        measured = workload.measure_bundle(root)
        self.assertEqual(measured["bundle_digest"],
                         self.published["bundle_digest"])
        self.assertEqual([one["path"] for one in measured["manifest"]],
                         [one["path"] for one in self.published["manifest"]])
        # AND IT IS NOT THE ENVELOPE'S, which covers one file out of eleven.
        self.assertNotEqual(measured["bundle_digest"],
                            self.published["envelope_digest"])

    def test_a_file_the_envelope_never_named_changes_the_identity(self):
        """DERIVED: the producer will not publish one, which is the point."""
        self.bundle(operation="add")
        place = self.derived(extra=(("blobs", "a" * 64), b"unnamed\n"))
        self.assertNotEqual(workload.measure_bundle(place)["bundle_digest"],
                            self.published["bundle_digest"])
        # AND `read_bundle` IS HAPPY WITH IT, which is exactly why the
        # measurement exists: internal consistency is not identity.
        contract.read_bundle(place)

    def test_a_link_or_a_device_in_the_bundle_refuses_the_measurement(self):
        self.bundle(operation="add")
        place = self.derived(name="linked")
        os.symlink("/etc/hostname", os.path.join(place, "elsewhere.txt"))
        with self.assertRaises(workload.WorkloadRefusal):
            workload.measure_bundle(place)

    def test_a_report_naming_another_bundle_is_held(self):
        self.behaviour = "foreign"
        self.bundle(operation="add")
        self.ending(self.entry(target=self.target()), "held", "report-foreign")


class TheWholePathSetIsProvedBeforeAnyImport(WorldCase):
    """The preflight, and the writes that never happened because of it."""

    def refused_before_the_provider(self, reason, **operands):
        result = self.ending(self.entry(**operands), "refused", reason)
        # THE POSITIVE FACT A REFUSAL CARRIES: no provider was started at all,
        # which is the only thing this workload can establish about a
        # mutation-free ending.
        self.assertEqual(self.commands, [])
        return result

    def test_a_late_invalid_row_stops_the_whole_import(self):
        """DERIVED: the accepted world carries one path and this needs two.

        The first row is valid and the second is not, so a preflight that
        checked as it went would have imported the first before refusing.
        """
        self.bundle(operation="add")
        late, blobs = self.row("zz-late.py")
        first = contract.read_bundle(self.published["root"])["envelope"]
        place = self.derived(paths=[*first["paths"], late], blobs=blobs)
        target = self.target(entries=[("zz-late.py", b"already here\n",
                                       0o644)])
        self.refused_before_the_provider("target-drift", bundle=place,
                                         target=target)
        self.assertEqual(self.contents(target, "zz-late.py"),
                         (b"already here\n", 0o644))
        self.assertFalse(os.path.exists(os.path.join(target,
                                                     self.reviewed())))

    def test_a_target_that_is_not_at_the_reviewed_base_bytes_refuses(self):
        self.bundle(operation="edit")
        target = self.target(entries=[(self.reviewed(), b"somebody else's\n",
                                       0o644)])
        self.refused_before_the_provider("target-drift", target=target)
        self.assertEqual(self.contents(target, self.reviewed()),
                         (b"somebody else's\n", 0o644))

    def test_a_target_at_another_mode_than_the_reviewed_base_refuses(self):
        self.bundle(operation="edit")
        target = self.target(entries=[(self.reviewed(), self.ORIGINAL,
                                       0o755)])
        self.refused_before_the_provider("target-drift", target=target)

    def test_a_read_only_target_refuses_and_is_never_repaired(self):
        """The DIRECTORY is read-only, which an edit still needs.

        The file's own mode is the reviewed one, so this is not the drift case
        above: what is missing is write on the directory a replacement lands
        in, and repository policy hands that to an operator rather than to a
        `chmod` here.
        """
        self.bundle(operation="edit")
        target = self.target(entries=[(self.reviewed(), self.ORIGINAL,
                                       0o644)])
        self.addCleanup(os.chmod, target, 0o755)
        os.chmod(target, 0o555)
        self.refused_before_the_provider("target-unwritable", target=target)
        self.assertEqual(self.contents(target, self.reviewed()),
                         (self.ORIGINAL, 0o644))
        self.assertEqual(stat.S_IMODE(os.stat(target).st_mode), 0o555)

    def test_a_link_or_a_directory_at_a_scheduled_path_refuses(self):
        self.bundle(operation="edit")
        target = self.target()
        os.symlink("/etc/hostname", os.path.join(target, self.reviewed()))
        self.refused_before_the_provider("path-unsupported", target=target)

    def test_an_addition_over_an_existing_path_refuses(self):
        self.bundle(operation="add")
        target = self.target(entries=[(self.reviewed(), b"already here\n",
                                       0o644)])
        self.refused_before_the_provider("target-drift", target=target)

    def test_a_target_at_another_revision_refuses(self):
        self.bundle(operation="add")
        self.refused_before_the_provider(
            "target-drift", target=self.target(),
            revision=lambda place: "0" * 40)

    def test_an_unreadable_target_revision_refuses(self):
        """THROUGH THE DEFAULT READER, which is the one production uses."""
        self.bundle(operation="add")
        self.refused_before_the_provider(
            "target-unavailable", target=self.target(repository=False),
            revision=workload.git_revision)

    def test_a_result_published_before_the_turn_stops_it(self):
        self.bundle(operation="add")
        workload.publish_result(
            self.delivery.result_root,
            workload.held_result(self.assignment, "provider-uncertain",
                                 "somebody else answered first"))
        # THE ENTRY'S OWN CHECK ANSWERS FIRST and starts nothing.
        self.assertEqual(self.entry(target=self.target()), 0)
        self.assertEqual(self.commands, [])
        self.assertEqual(self.observed()["result"]["outcome"], "held")


class TheEvidenceMustBeThisCandidatesOwn(WorldCase):
    """Correlation: an internally consistent bundle is not this bundle."""

    def refused_before_the_provider(self, reason, **operands):
        result = self.ending(self.entry(**operands), "refused", reason)
        self.assertEqual(self.commands, [])
        return result

    def test_a_bundle_composed_for_another_assignment_refuses(self):
        """DERIVED: the producer refuses to compose one, which is correct."""
        self.bundle(operation="add")
        place = self.derived(envelope={"assignment_digest":
                                       "sha256:" + "e" * 64})
        self.refused_before_the_provider("assignment-uncorrelated",
                                         bundle=place, target=self.target())

    def test_a_bundle_naming_another_launch_refuses(self):
        self.bundle(operation="add")
        first = contract.read_bundle(self.published["root"])["envelope"]
        place = self.derived(envelope={
            "launch": dict(first["launch"], digest="sha256:" + "d" * 64)})
        self.refused_before_the_provider("launch-uncorrelated", bundle=place,
                                         target=self.target())

    def test_a_container_launched_under_another_role_refuses(self):
        self.bundle(operation="add")
        with open(self.launch_place, "rb") as handle:
            held = json.loads(handle.read())
        os.chmod(self.launch_place, 0o644)
        with open(self.launch_place, "w", encoding="utf-8") as handle:
            json.dump(dict(held, role="reviewer"), handle)
        os.chmod(self.launch_place, 0o444)
        self.refused_before_the_provider("launch-uncorrelated",
                                         target=self.target())

    def test_evidence_about_another_checkpoint_refuses(self):
        """DERIVED: one projection is replaced with a valid, unrelated one."""
        self.bundle(operation="add")
        taken = contract.read_bundle(self.published["root"])
        place = self.derived(documents={
            "review.json": dict(taken["evidence"]["review.json"],
                                verdict_id="verdict-somebody-elses")})
        self.refused_before_the_provider("evidence-uncorrelated",
                                         bundle=place, target=self.target())

    def test_a_review_that_did_not_accept_refuses(self):
        self.bundle(operation="add")
        taken = contract.read_bundle(self.published["root"])
        place = self.derived(documents={
            "review.json": dict(taken["evidence"]["review.json"],
                                disposition="changes-requested")})
        self.refused_before_the_provider("review-unaccepted", bundle=place,
                                         target=self.target())

    def test_changing_an_existing_test_outside_the_scheduled_scope_refuses(
            self):
        """The semantic scope evaluation, over a real accepted Job's scope."""
        self.bundle(operation="add")
        taken = contract.read_bundle(self.published["root"])
        scoped = taken["evidence"]["job.json"]["test_scope"][0]
        outside, blobs = self.row("v12/python/tests/manager/test_elsewhere.py",
                                  operation="edit")
        place = self.derived(paths=[outside], blobs=blobs)
        self.refused_before_the_provider("scope-unauthorized", bundle=place,
                                         target=self.target())
        self.assertTrue(outside["path"].startswith("v12/python/tests/"))
        self.assertFalse(outside["path"].startswith(scoped))

    def test_the_same_change_inside_the_scheduled_scope_is_admitted(self):
        """What makes the refusal above about AUTHORITY rather than about the
        word "test": the accepted Job's own scope names this directory."""
        self.bundle(operation="add")
        taken = contract.read_bundle(self.published["root"])
        scoped = taken["evidence"]["job.json"]["test_scope"][0]
        inside, blobs = self.row(f"{scoped}/test_scheduled.py",
                                 operation="edit")
        place = self.derived(paths=[inside], blobs=blobs, name="scoped")
        target = self.target(entries=[(inside["path"], self.ROW_BASE, 0o644)])
        self.ending(self.entry(bundle=place, target=target), "integrated")

    def test_a_bundle_with_no_accepted_test_scope_refuses(self):
        """ABSENT AND EMPTY ARE NOT ONE CLAIM, and neither is permission.

        A bundle whose Job projection carries no scheduled scope at all cannot
        authorize an existing-test change, and reading that absence as consent
        is the exact failure the semantic evaluation exists for.
        """
        self.bundle(operation="add")
        taken = contract.read_bundle(self.published["root"])
        job = {name: value
               for name, value in taken["evidence"]["job.json"].items()
               if name != "test_scope"}
        place = self.derived(documents={"job.json": job}, name="unscoped")
        self.refused_before_the_provider("scope-unauthorized", bundle=place,
                                         target=self.target())

    def test_an_added_test_needs_no_scheduled_scope(self):
        """Repository policy: adding tests never needs case-specific consent,
        and only an EXISTING test's mutation does."""
        self.bundle(operation="add")
        added, blobs = self.row("tests/test_brand_new.py", operation="add")
        place = self.derived(paths=[added], blobs=blobs)
        self.ending(self.entry(bundle=place, target=self.target()),
                    "integrated")

    def test_a_bundle_with_no_readable_envelope_refuses(self):
        self.bundle(operation="add")
        place = self.derived(name="unreadable")
        with open(os.path.join(place, contract.ENVELOPE_DOCUMENT), "wb") as h:
            h.write(b"{not one document")
        self.refused_before_the_provider("bundle-unreadable", bundle=place,
                                         target=self.target())

    def test_instructions_the_profile_does_not_name_refuse(self):
        """DERIVED: the producer proves this equality before it publishes."""
        self.bundle(operation="add")
        from baton_v12.contracts.canonical import canonical_bytes

        place = self.derived(name="instructed")
        replacement = b"a different instruction document\n"
        self.wrote(place, (contract.INSTRUCTIONS_DOCUMENT,), replacement)
        taken = contract.read_bundle(self.published["root"])
        composed = dict(taken["envelope"])
        composed["instructions"] = {
            "digest": hashlib.sha256(replacement).hexdigest(),
            "bytes": len(replacement)}
        self.wrote(place, (contract.ENVELOPE_DOCUMENT,),
                   canonical_bytes(composed))
        self.refused_before_the_provider("instructions-uncorrelated",
                                         bundle=place, target=self.target())


class TheEndingIsConservative(WorldCase):
    """Every way a turn that HAD writable work can end, and each is held."""

    def held(self, reason, **operands):
        self.bundle(operation="add")
        result = self.ending(self.entry(target=self.target(), **operands),
                             "held", reason)
        self.assertEqual(len(self.commands), 1)
        return result

    def test_a_provider_that_did_not_complete_is_held(self):
        self.behaviour = None
        self.status = 1
        self.held("provider-failed")

    def test_a_provider_that_timed_out_is_held(self):
        self.timeout = True
        self.held("provider-failed")

    def test_a_turn_with_no_report_is_held(self):
        self.behaviour = "silent"
        self.held("report-missing")

    def test_an_unreadable_report_is_held(self):
        self.behaviour = "malformed"
        self.held("report-unreadable")

    def test_a_report_claiming_a_path_outside_the_table_is_held(self):
        self.behaviour = "outside"
        self.held("report-outside-scope")

    def test_a_partial_import_is_held(self):
        """DERIVED: two rows, of which the provider imports one."""
        self.behaviour = "partial"
        self.bundle(operation="add")
        second, blobs = self.row("zz-second.py")
        first = contract.read_bundle(self.published["root"])["envelope"]
        place = self.derived(paths=[*first["paths"], second], blobs=blobs)
        target = self.target()
        result = self.ending(self.entry(bundle=place, target=target), "held",
                             "import-incomplete")
        self.assertEqual(result["detail"]["detail"]["missing"], 1)
        # AND THE ACCOUNT SEPARATES THE TWO NUMBERS an operator needs: how
        # many scheduled paths are not the candidate, and how many actually
        # moved off the state the preflight recorded.
        self.assertEqual(result["detail"]["detail"]["imported"], 1)
        self.assertEqual(result["detail"]["detail"]["moved"], 1)
        # AND THE PART THAT LANDED IS STILL THERE. A hold is an account of an
        # ambiguous world, not a rollback: this workload never writes to the
        # target and never undoes what a provider did.
        self.assertEqual(self.contents(target, self.reviewed())[0],
                         self.CANDIDATE)

    def test_a_clean_provider_refusal_after_writable_work_is_still_held(self):
        """THE PINNED RULE, and the case that would catch its loss.

        The provider wrote nothing and says so, its report is well formed, and
        every scheduled path is exactly as it was. That is not a refusal here:
        restoration of bytes is not absence of mutation, and `refused` is
        reserved for a turn that started no provider at all.
        """
        self.behaviour = "refuse"
        self.bundle(operation="add")
        target = self.target()
        result = self.ending(self.entry(target=target), "held",
                             "import-incomplete")
        self.assertFalse(os.path.exists(os.path.join(target,
                                                     self.reviewed())))
        # NOTHING MOVED, AND IT IS STILL HELD. That is the whole rule in one
        # assertion: an unchanged target after a provider had writable work is
        # not evidence that no mutation occurred.
        self.assertEqual(result["detail"]["detail"]["moved"], 0)
        self.assertEqual(result["detail"]["detail"]["imported"], 0)

    def test_a_report_that_does_not_claim_an_import_is_held(self):
        self.behaviour = "unclaimed"
        self.held("provider-uncertain")

    def test_version_control_metadata_that_moved_is_held(self):
        self.behaviour = "index"
        self.bundle(operation="add")
        target = self.target()
        self.initialized(target)
        # A REAL INDEX HAS TO EXIST for a case about it changing to mean
        # anything, so one path is staged before the turn.
        self.ending(self.entry(target=target), "held", "repository-mutated")

    def test_an_agent_that_answers_something_else_is_held(self):
        class Elsewhere:
            def invoke_provider(self, *, prompt, room):
                return "not this deployment's document"

        self.bundle(operation="add")
        self.ending(self.entry(target=self.target(), agent=Elsewhere()),
                    "held", "provider-uncertain")


class TheEntryIsTheOneShotComposition(WorldCase):
    """What the entry answers when there is nothing to answer under."""

    def test_no_launch_document_writes_nothing_and_exits_two(self):
        self.bundle(operation="add")
        os.unlink(self.launch_place)
        self.assertEqual(self.entry(target=self.target()), 2)
        self.assertIsNone(workload.existing_result(
            self.delivery.result_root))
        self.assertEqual(self.commands, [])

    def test_a_writable_launch_document_is_refused(self):
        """`read_launch`'s proof: a launch this worker could rewrite is not
        one the manager can hold it to."""
        self.bundle(operation="add")
        os.chmod(self.launch_place, 0o644)
        self.assertEqual(self.entry(target=self.target()), 2)
        self.assertIsNone(workload.existing_result(
            self.delivery.result_root))

    def test_no_assignment_writes_nothing_and_exits_two(self):
        self.bundle(operation="add")
        os.unlink(os.path.join(self.delivery.assignment_root,
                               contract.ASSIGNMENT_DOCUMENT))
        self.assertEqual(self.entry(target=self.target()), 2)
        self.assertEqual(self.commands, [])

    def test_the_published_result_is_read_only_and_never_clobbered(self):
        self.bundle(operation="add")
        self.ending(self.entry(target=self.target()), "integrated")
        place = os.path.join(self.delivery.result_root,
                             contract.RESULT_DOCUMENT)
        self.assertEqual(stat.S_IMODE(os.stat(place).st_mode), 0o444)
        held = workload.existing_result(self.delivery.result_root)
        answer = workload.publish_result(
            self.delivery.result_root,
            workload.held_result(self.assignment, "provider-uncertain",
                                 "a second publication"))
        self.assertFalse(answer["published"])
        self.assertEqual(workload.existing_result(self.delivery.result_root),
                         held)

    def test_a_result_above_the_delivery_bound_is_refused_not_truncated(self):
        long = ["x" * 900 + f"/{index}.py" for index in range(100)]
        document = workload.held_result(self.assignment, "import-incomplete",
                                        "an oversized account",
                                        {"paths": long})
        with self.assertRaises(workload.WorkloadRefusal):
            workload.publish_result(self.delivery.result_root, document)
        self.assertIsNone(workload.existing_result(
            self.delivery.result_root))


class TheRevisionReaderIsReadOnly(unittest.TestCase):
    """The default target-revision reader, against a REAL repository."""

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="v12-w110935-revision-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.place = os.path.join(self.root, "target")
        os.makedirs(self.place)
        self.environment = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                            "HOME": self.root,
                            "GIT_CONFIG_GLOBAL": "/dev/null",
                            "GIT_CONFIG_SYSTEM": "/dev/null"}
        for arguments in (["init", "-q", "-b", "main"],
                          ["-c", "user.email=w110935@example.invalid",
                           "-c", "user.name=W110935", "commit", "-q",
                           "--allow-empty", "-m", "one"]):
            done = subprocess.run(["git", "-C", self.place, *arguments],
                                  capture_output=True, timeout=300,
                                  env=self.environment)
            self.assertEqual(done.returncode, 0, done.stderr)

    def head(self):
        done = subprocess.run(["git", "-C", self.place, "rev-parse", "HEAD"],
                              capture_output=True, timeout=300,
                              env=self.environment)
        return done.stdout.decode("utf-8").strip()

    def test_it_answers_the_repositorys_own_revision(self):
        self.assertEqual(workload.git_revision(self.place), self.head())

    def test_the_query_is_read_only_and_lock_free(self):
        argv = workload.revision_argv(self.place)
        self.assertEqual(argv[:2], ["git", "--no-optional-locks"])
        self.assertEqual(argv[-2:], ["rev-parse", "HEAD"])
        environment = workload.revision_environment()
        self.assertEqual(environment["GIT_OPTIONAL_LOCKS"], "0")
        for name in ("GIT_CONFIG_GLOBAL", "GIT_CONFIG_SYSTEM"):
            self.assertEqual(environment[name], "/dev/null")
        for name in ("ANTHROPIC_API_KEY", "GIT_DIR", "GIT_WORK_TREE"):
            self.assertNotIn(name, environment)

    def test_a_tree_with_no_history_refuses_rather_than_inventing_one(self):
        elsewhere = os.path.join(self.root, "not-a-repository")
        os.makedirs(elsewhere)
        with self.assertRaises(Exception):
            workload.git_revision(elsewhere)


if __name__ == "__main__":
    unittest.main()
