"""W197661 — the fixture agent that produces a REAL candidate.

THE BLOCKER THIS COVERS. Every earlier fixture wrote `result_metadata: {}` for
its `git-change-proposal`, so it carried no `baton.git-proposal/1` claim,
nothing could be published, and independent review and report-and-hold were
unreachable by construction. The lifecycle exercise kept stopping at the same
wall for a reason that was the FIXTURE's rather than the deployment's.

NO CONTAINER AND NO MODEL. The agent's whole job is to commit in the tree it was
handed and describe what it did, and on the `git-line` profile that tree is
`/output` -- so a temporary repository here is the same arrangement the
container gets, and the case can be deterministic.
"""

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

REPO = "/home/sl/src/baton"
CONTEXT = os.path.join(
    REPO, "work/records/2026/09/finding-v12-worker-launch-version-mismatch",
    "instance-200564/context/worker")


def _vcs(place, *arguments):
    return subprocess.run(
        ["git", "-c", f"safe.directory={place}", "-c", "user.name=Fixture",
         "-c", "user.email=fixture@baton.invalid", "-C", place, *arguments],
        capture_output=True, text=True, timeout=120, check=True).stdout


class FixtureCase(unittest.TestCase):

    DECLARED = [{"name": "proposal", "type": "git-change-proposal",
                 "path": "proposal"},
                {"name": "findings", "type": "directory-result",
                 "path": "findings"},
                {"name": "logs", "type": "directory-result", "path": "logs"}]

    def setUp(self):
        if CONTEXT not in sys.path:
            sys.path.insert(0, CONTEXT)
            self.addCleanup(sys.path.remove, CONTEXT)
        import proposing_agent

        self.module = proposing_agent
        self.home = tempfile.mkdtemp(prefix="v12-w197661-fixture-")
        self.addCleanup(shutil.rmtree, self.home, True)
        # THE PRIVATE LINE, laid out the way the manager lays one out: a
        # detached worktree the worker is handed, with a base commit already on
        # it. `/output` IS this directory in a container.
        self.line = os.path.join(self.home, "line")
        os.makedirs(self.line)
        _vcs(self.line, "init", "--quiet", "-b", "main")
        with open(os.path.join(self.line, "README"), "w") as handle:
            handle.write("the base of this line\n")
        _vcs(self.line, "add", "--", "README")
        _vcs(self.line, "commit", "--quiet", "--no-gpg-sign", "-m", "base")
        self.base = _vcs(self.line, "rev-parse", "HEAD").strip()

    def agent(self):
        return self.module.ProposingAgent(root=self.line)

    def worked(self, seen=None):
        return self.agent().work(seen or {}, self.DECLARED)

    def claim(self, answered, name="proposal"):
        one = [entry for entry in answered["outputs"]
               if entry["name"] == name][0]
        return one["result_metadata"]


class TheFixtureProducesARealCandidate(FixtureCase):

    def test_it_COMMITS_and_the_head_is_a_new_revision(self):
        answered = self.worked()
        self.assertEqual(answered["disposition"], "completed")
        head = _vcs(self.line, "rev-parse", "HEAD").strip()
        self.assertNotEqual(head, self.base)
        self.assertEqual(
            _vcs(self.line, "show", "--name-only", "--format=", "HEAD"
                 ).split(), ["w197661-fixture.txt"])

    def test_the_PROPOSAL_CLAIM_is_present_and_is_this_turns_own(self):
        """The four facts a proposal claim is made of, and no fifth."""
        answered = self.worked()
        held = self.claim(answered)[self.module.CLAIM_NAMESPACE]
        self.assertEqual(sorted(held),
                         ["base", "head", "recap", "transport"])
        self.assertEqual(held["base"], self.base)
        self.assertEqual(held["head"],
                         _vcs(self.line, "rev-parse", "HEAD").strip())
        self.assertEqual(held["transport"], self.module.BUNDLE)
        self.assertIn("w197661-fixture.txt", held["recap"])

    def test_it_names_NO_manager_identity(self):
        """An artifact id, a content digest, a byte count or a custody locator
        would be this container certifying its own output."""
        held = self.claim(self.worked())[self.module.CLAIM_NAMESPACE]
        for forbidden in ("artifact_id", "content_digest", "bytes",
                          "custody_locator", "manifest_digest", "result_id"):
            self.assertNotIn(forbidden, held)

    def test_the_declared_PROPOSAL_TREE_is_written(self):
        self.worked()
        place = os.path.join(self.line, "proposal")
        self.assertEqual(sorted(os.listdir(place)),
                         sorted([self.module.PATCH, self.module.VERIFICATION,
                                 self.module.RESULT, self.module.BUNDLE]))
        with open(os.path.join(place, self.module.PATCH)) as handle:
            self.assertIn("w197661-fixture.txt", handle.read())
        self.assertGreater(
            os.stat(os.path.join(place, self.module.BUNDLE)).st_size, 0)

    def test_the_OBJECTS_carry_the_commit_the_claim_names(self):
        """A transport that did not carry the head would be a proposal nobody
        can apply."""
        held = self.claim(self.worked())[self.module.CLAIM_NAMESPACE]
        objects = os.path.join(self.line, "proposal", self.module.BUNDLE)
        listed = subprocess.run(["git", "bundle", "list-heads", objects],
                                capture_output=True, text=True, timeout=60,
                                check=True).stdout
        self.assertIn(held["head"], listed)

    def test_the_OTHER_outputs_carry_no_claim(self):
        answered = self.worked()
        for name in ("findings", "logs"):
            self.assertEqual(self.claim(answered, name), {})

    def test_a_STALE_transport_from_an_earlier_turn_is_removed_first(self):
        """On a persistent line the declared directory SURVIVES the turn that
        wrote it, so a previous attempt's objects sitting here would be
        collected as though this turn had claimed them."""
        os.makedirs(os.path.join(self.line, "proposal"), exist_ok=True)
        stale = os.path.join(self.line, "proposal", self.module.BUNDLE)
        with open(stale, "wb") as handle:
            handle.write(b"AN EARLIER TURN'S OBJECTS")
        self.worked()
        with open(stale, "rb") as handle:
            self.assertNotEqual(handle.read(), b"AN EARLIER TURN'S OBJECTS")

    def test_it_is_DETERMINISTIC_about_the_bytes_it_writes(self):
        self.worked()
        with open(os.path.join(self.line, "w197661-fixture.txt")) as handle:
            self.assertEqual(handle.read(),
                             "w197661 deterministic fixture candidate\n")

    def test_a_declaration_that_is_not_a_list_is_REFUSED(self):
        with self.assertRaises(self.module.WorkloadRefusal):
            self.agent().work({}, "not a list")


class TheFixtureAlsoREVIEWSDeterministically(FixtureCase):
    """W197661 review200179 [R1]. These three cases USED TO HIDE A DEFECT: they
    handed the implementation repository in as the review OUTPUT root, so a
    review turn asking `self.root` for head, tree and parent looked correct.

    The real contract has TWO roots. `review_cycles.review_boundary` nominates
    the frozen line and `source_boundary` binds it READ-ONLY at
    `/input/<task.source_root>`, beside a separate writable result directory --
    which is what `claude_agent`'s own review turn reads. These drive that
    arrangement: a read-only checkpoint mount, an empty writable output root,
    and a frozen task between them.
    """

    def reviewing(self, *, base=None, source_root="source", task=True,
                  checkpoint=True):
        """The review container's arrangement, laid out as the manager lays it.

        The checkpoint is a SEPARATE clone, made read-only, so a turn that
        tried to write into it would fail the way the container would rather
        than quietly succeeding.
        """
        self.worked()
        room = os.path.join(self.home, "review")
        inputs = os.path.join(room, "input")
        output = os.path.join(room, "output")
        os.makedirs(inputs)
        os.makedirs(output)
        if checkpoint:
            frozen = os.path.join(inputs, source_root)
            _vcs(self.home, "clone", "--quiet", self.line, frozen)
            self.frozen = frozen
        self.task_place = os.path.join(inputs, "task.json")
        if task:
            declared = base if base is not None else _vcs(
                self.line, "rev-parse", "HEAD~1").strip()
            with open(self.task_place, "w") as handle:
                json.dump({"schema": "baton.dogfood-task/2",
                           "task_id": "w197661-lifecycle",
                           "source_profile": "git-line",
                           "source_root": source_root,
                           "declared_base": declared,
                           "instructions": "review it",
                           "verification": []}, handle)
        return self.module.ProposingAgent(root=output, inputs=inputs), output

    def rewrite_base(self, revision):
        """The frozen task, with one member replaced, before the turn runs."""
        with open(self.task_place) as handle:
            found = json.load(handle)
        found["declared_base"] = revision
        with open(self.task_place, "w") as handle:
            json.dump(found, handle)

    def reviewed(self, **named):
        agent, output = self.reviewing(**named)
        return agent.work({"role": "review"}, self.DECLARED), output

    def test_a_review_turn_answers_a_VERDICT_CLAIM_over_THE_MOUNTED_LINE(self):
        answered, _ = self.reviewed()
        held = self.claim(answered, "findings")[
            self.module.REVIEW_CLAIM_NAMESPACE]
        self.assertEqual(sorted(held), ["base", "head", "tree", "verdict"])
        self.assertEqual(held["verdict"], "accepted")
        # READ OFF THE CHECKPOINT, not off the output root.
        self.assertEqual(held["head"],
                         _vcs(self.frozen, "rev-parse", "HEAD").strip())
        self.assertEqual(held["tree"],
                         _vcs(self.frozen, "rev-parse", "HEAD^{tree}").strip())
        self.assertEqual(held["base"],
                         _vcs(self.line, "rev-parse", "HEAD~1").strip())

    def test_the_base_is_THE_TASKS_and_never_guessed_from_the_shape(self):
        """`HEAD~1` was this fixture assuming the shape of a line. The verdict
        is about the revision the frozen task nominates -- so a task naming a
        DIFFERENT valid revision gets that one, which `HEAD~1` cannot
        produce."""
        agent, _ = self.reviewing(base="")
        named = _vcs(self.frozen, "rev-parse", "HEAD").strip()
        self.rewrite_base(named)
        answered = agent.work({"role": "review"}, self.DECLARED)
        held = self.claim(answered, "findings")[
            self.module.REVIEW_CLAIM_NAMESPACE]
        self.assertEqual(held["base"], named)
        self.assertNotEqual(
            named, _vcs(self.frozen, "rev-parse", "HEAD~1").strip())

    def test_a_base_THE_LINE_HAS_NEVER_SEEN_is_refused(self):
        """`rev-parse --verify` accepts a well-formed name as SYNTAX, so a base
        nobody nominated would otherwise verify itself."""
        with self.assertRaises(self.module.WorkloadRefusal):
            self.reviewed(base="0" * 40)

    def test_a_review_turn_WRITES_NOTHING_into_the_checkpoint(self):
        """The arrangement says it rather than the intention: every observation
        comes from a mount the container cannot write to."""
        answered, output = self.reviewed()
        os.chmod(self.frozen, 0o555)
        self.addCleanup(os.chmod, self.frozen, 0o755)
        head = _vcs(self.frozen, "rev-parse", "HEAD").strip()
        self.assertEqual(
            _vcs(self.frozen, "status", "--porcelain",
                 "--untracked-files=all").strip(), "")
        self.assertEqual(_vcs(self.frozen, "rev-parse", "HEAD").strip(), head)

    def test_the_findings_and_logs_go_to_THE_OUTPUT_ROOT_only(self):
        _, output = self.reviewed()
        for one in self.DECLARED:
            self.assertTrue(
                os.path.exists(os.path.join(output, one["path"], "result.txt")),
                one["path"])
            self.assertFalse(
                os.path.exists(os.path.join(self.frozen, one["path"])),
                one["path"])

    def test_a_MISSING_TASK_refuses_and_never_reviews_the_output_root(self):
        """Falling back is exactly how the defect read correct."""
        with self.assertRaises(self.module.WorkloadRefusal) as raised:
            self.reviewed(task=False)
        self.assertIn("will not review its own output root",
                      str(raised.exception))

    def test_a_MISSING_CHECKPOINT_refuses_rather_than_falling_back(self):
        with self.assertRaises(self.module.WorkloadRefusal) as raised:
            self.reviewed(checkpoint=False)
        self.assertIn("no directory there", str(raised.exception))

    def test_a_source_root_THAT_LEAVES_the_input_root_is_refused(self):
        with self.assertRaises(self.module.WorkloadRefusal):
            self.reviewed(source_root="../elsewhere")

    def test_the_review_claim_names_NO_manager_identity_either(self):
        answered, _ = self.reviewed()
        held = self.claim(answered, "findings")[
            self.module.REVIEW_CLAIM_NAMESPACE]
        for forbidden in ("attachment_id", "checkpoint_id", "verdict_id",
                          "result_id", "manifest_digest"):
            self.assertNotIn(forbidden, held)

    def test_the_two_roots_are_NOT_the_same_directory_by_default(self):
        """The container's own constants, which is what the defect conflated."""
        agent = self.module.ProposingAgent()
        self.assertEqual(agent.root, self.module.OUTPUT_ROOT)
        self.assertEqual(agent.inputs, self.module.INPUT_ROOT)
        self.assertNotEqual(agent.root, agent.inputs)


class TheLINEIsSTILLCLEANAfterTheTurn(FixtureCase):
    """W197661 c200000, found by running the installed lifecycle.

    `checkpoint_profiles.freeze` refuses a line with "tracked or untracked
    worktree changes", and on the `git-line` profile the DECLARED OUTPUTS are
    written into the worktree -- so writing them is exactly what made the line
    dirty. The whole lifecycle stopped at `freeze_checkpoint` with the
    candidate already committed and nothing wrong with it.

    Every earlier case here asserted what the agent PRODUCED. None asserted
    what it LEFT BEHIND, which is the half the manager reads next.
    """

    def status(self):
        return _vcs(self.line, "status", "--porcelain",
                    "--untracked-files=all")

    def test_the_worktree_is_CLEAN_when_the_turn_ends(self):
        self.worked()
        self.assertEqual(self.status(), "")

    def test_the_declared_OUTPUTS_are_still_there_and_unstaged(self):
        """Reserved, not deleted: the manager collects them from this very
        tree after the turn."""
        self.worked()
        for one in self.DECLARED:
            self.assertTrue(
                os.path.exists(os.path.join(self.line, one["path"])),
                one["path"])
        self.assertEqual(self.status(), "")

    def test_the_WORKERS_OWN_envelope_would_not_dirty_it_either(self):
        """The wrapper writes `output.json` into this same workspace after the
        turn returns, so a line clean only until then is not clean."""
        self.worked()
        with open(os.path.join(self.line, "output.json"), "w") as handle:
            handle.write("{}\n")
        self.assertEqual(self.status(), "")

    def test_the_exclusion_is_LOCAL_and_never_committed(self):
        """A committed ignore file would be this turn proposing a change to
        somebody else's tree."""
        self.worked()
        self.assertTrue(os.path.exists(
            os.path.join(self.line, ".git", "info", "exclude")))
        named = _vcs(self.line, "show", "--name-only", "--format=", "HEAD")
        self.assertEqual(named.split(), ["w197661-fixture.txt"])

    def test_a_declared_output_with_NO_PATH_is_refused(self):
        """The reservation is derived from the declarations, so a declaration
        this agent cannot read is one it must not write past."""
        with self.assertRaises(self.module.WorkloadRefusal):
            self.agent().work({}, [{"name": "proposal",
                                    "type": "git-change-proposal"}])

    def test_the_reserved_set_is_REPLACED_rather_than_appended(self):
        """A persistent line survives the turn that wrote it, so a resumed
        turn must reserve exactly its own set: an appended file would keep an
        earlier turn's names excluded forever."""
        agent = self.agent()
        agent._reserve([{"name": "a", "path": "earlier"}])
        agent._reserve(list(self.DECLARED))
        with open(os.path.join(self.line, ".git", "info", "exclude")) as one:
            found = one.read().split()
        self.assertNotIn("/earlier", found)
        self.assertEqual(sorted(found),
                         ["/findings", "/logs", "/output.json", "/proposal"])


class TheAgentCarriesNoManagerImport(FixtureCase):

    def test_it_imports_nothing_from_baton_v12(self):
        """A worker that can import the manager is a worker one bug away from
        holding the manager's capabilities."""
        import ast

        with open(os.path.join(CONTEXT, "proposing_agent.py")) as handle:
            tree = ast.parse(handle.read())
        imported = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(one.name for one in node.names)
            elif isinstance(node, ast.ImportFrom):
                imported.add(node.module or "")
        self.assertEqual(sorted(one for one in imported
                                if not one.startswith("_")),
                         ["hashlib", "json", "os", "subprocess"])


class TheIMAGEActuallySELECTSThisAgent(unittest.TestCase):
    """Review199914, and it was a defect in what I shipped: the recipe COPIED
    `proposing_agent.py` and then entered `baton_worker.py` directly, so `main`
    saw `agent=None`, took `_scripted_default()` and imported the ORIGINAL
    `ScriptedAgent` -- the one that writes `result_metadata: {}`. The new agent
    travelled in the image and nothing selected it.

    COPYING A MODULE IS NOT COMPOSING WITH IT, and nothing here proved the
    composition because every case drove `ProposingAgent` directly. These read
    the recipe and the entry module as the artefacts they are.
    """

    RECIPE = os.path.join(os.path.dirname(CONTEXT), "Dockerfile.fixture")

    def recipe(self):
        with open(self.RECIPE) as handle:
            return handle.read()

    def entry(self):
        with open(os.path.join(CONTEXT, "proposing_entry.py")) as handle:
            return handle.read()

    def test_the_ENTRYPOINT_is_the_entry_module_and_not_the_worker(self):
        """The one line that decides which agent the built image runs."""
        found = [one for one in self.recipe().splitlines()
                 if one.startswith("ENTRYPOINT")]
        self.assertEqual(
            found, ['ENTRYPOINT ["python3", "/opt/baton/proposing_entry.py"]'])

    def test_the_entry_module_INJECTS_through_the_documented_seam(self):
        """`baton_worker.main(agent=...)`, not a second serve loop. A fixture
        image with its own worker entry would be an implementation nobody
        reviewed."""
        import ast

        tree = ast.parse(self.entry())
        imported = {node.module for node in ast.walk(tree)
                    if isinstance(node, ast.ImportFrom)}
        self.assertEqual(imported, {"baton_worker", "proposing_agent"})
        call = [node for node in ast.walk(tree)
                if isinstance(node, ast.Call)
                and getattr(node.func, "id", None) == "main"]
        self.assertEqual(len(call), 1)
        self.assertEqual([one.arg for one in call[0].keywords], ["agent"])
        self.assertEqual(one_named(call[0]), "ProposingAgent")

    def test_the_image_CARRIES_NO_second_agent_to_fall_back_to(self):
        """`_scripted_default` imports `scripted_agent`, and an image that
        carries both agents selects one of them by a branch nobody reads. With
        the module absent that branch cannot run at all, so a recipe that loses
        this entrypoint fails loudly rather than quietly running the old
        fixture."""
        # THE DIRECTIVES, not the prose: this recipe explains the defect in
        # its own comments, and a substring check over the whole file would
        # read that explanation as the thing it warns about.
        copied = [one for one in self.recipe().splitlines()
                  if one.startswith("COPY")]
        self.assertFalse([one for one in copied if "scripted_agent" in one],
                         copied)
        self.assertFalse(os.path.exists(os.path.join(CONTEXT,
                                                     "scripted_agent.py")))

    def test_every_COPIED_input_exists_and_nothing_else_is_in_the_context(self):
        """Provenance is a list of bytes that went in, so a copy naming a file
        that is not there -- or a file there that nothing names -- is a recipe
        nobody can reproduce."""
        named = sorted(one.split()[1] for one in self.recipe().splitlines()
                       if one.startswith("COPY"))
        root = os.path.dirname(CONTEXT)
        for one in named:
            self.assertTrue(os.path.exists(os.path.join(root, one)), one)
        present = sorted(
            os.path.relpath(os.path.join(where, name), root)
            for where, _, names in os.walk(root) for name in names
            if "__pycache__" not in where)
        covered = []
        for one in present:
            if one == "Dockerfile.fixture":
                continue
            self.assertTrue(any(one == two or one.startswith(two + "/")
                                for two in named), one)
            covered.append(one)
        self.assertTrue(covered)

    def test_the_default_BRANCH_is_what_would_have_run(self):
        """Not an assumption about the defect: the worker program in this very
        context still says so."""
        with open(os.path.join(CONTEXT, "baton_worker.py")) as handle:
            program = handle.read()
        self.assertIn("from scripted_agent import ScriptedAgent", program)
        self.assertIn("_scripted_default() if agent is None else agent",
                      program)


def one_named(call):
    """The name of the class the entry module constructs for `agent=`."""
    import ast

    value = call.keywords[0].value
    return getattr(value.func, "id", None) if isinstance(value, ast.Call) \
        else getattr(value, "id", None)


class AnINTEGRATIONIsAdmittedBehindAnOrdinaryTestRun(FixtureCase):
    """W197661 review 2026-09-18T05-14-53Z [R1], and the gap was the fixture's.

    The configured task declared an EMPTY verification list, so
    `Integration.required_tests` refused every integration tick -- "the
    configured implementation task names no verification command" -- while
    implementation and review sat completed. Fixing the task alone would not
    have been enough: `integration.driver._observation_of` requires the
    PRODUCER's own ordinary-test observation on the frozen proposal output,
    and this fixture carried none.

    THE COMMAND IS A REAL CHECK OF THE CANDIDATE, not one chosen to exit zero:
    the last case here corrupts the candidate and the same argv fails.
    """

    ARGV = ["python3", "-c",
            "import pathlib,sys;"
            "sys.exit(0 if pathlib.Path('w197661-fixture.txt').read_text()"
            " == 'w197661 deterministic fixture candidate\\n' else 1)"]

    def setUp(self):
        super().setUp()
        self.inputs = os.path.join(self.home, "input")
        os.makedirs(self.inputs)

    def frozen(self, **changed):
        """The frozen task, written as BYTES the digest is taken over."""
        task = {"schema": "baton.dogfood-task/2",
                "task_id": "w197661-lifecycle",
                "instructions": "add the fixture file",
                "source_root": "source", "source_profile": "git-line",
                "declared_base": self.base, "verification": list(self.ARGV)}
        task.update(changed)
        raw = json.dumps(task, sort_keys=True, separators=(",", ":")).encode()
        with open(os.path.join(self.inputs, "task.json"), "wb") as handle:
            handle.write(raw)
        return raw

    def agent(self):
        return self.module.ProposingAgent(root=self.line, inputs=self.inputs)

    def observed(self, answered=None):
        held = self.claim(answered or self.worked())
        return held.get(self.module.ORDINARY_TESTS_NAMESPACE)

    def test_the_OBSERVATION_is_carried_on_the_proposal_output(self):
        self.frozen()
        held = self.observed()
        self.assertIsNotNone(held)
        self.assertEqual(sorted(held), ["argv", "base", "head", "status",
                                        "task_digest", "task_id"])
        self.assertEqual(held["argv"], self.ARGV)
        self.assertEqual(held["status"], 0)

    def test_the_DIGEST_is_of_the_exact_task_bytes_it_read(self):
        """A digest over a re-serialization would measure this file's JSON
        style rather than the document the deployment holds."""
        raw = self.frozen()
        self.assertEqual(self.observed()["task_digest"],
                         "sha256:" + hashlib.sha256(raw).hexdigest())

    def test_it_names_THIS_turns_base_and_head(self):
        """An observation about another candidate is not this one's
        evidence, and the consumer compares both against the claim."""
        self.frozen()
        answered = self.worked()
        held = self.observed(answered)
        claimed = self.claim(answered)[self.module.CLAIM_NAMESPACE]
        self.assertEqual(held["base"], claimed["base"])
        self.assertEqual(held["head"], claimed["head"])
        self.assertEqual(held["head"],
                         _vcs(self.line, "rev-parse", "HEAD").strip())

    def test_the_command_runs_over_the_COMMITTED_candidate(self):
        """It runs after the commit, so what passed is the tree the candidate
        IS rather than an uncommitted worktree."""
        self.frozen(verification=["python3", "-c",
                                  "import subprocess,sys;"
                                  "sys.exit(0 if not subprocess.run("
                                  "['git','status','--porcelain'],"
                                  "capture_output=True,text=True"
                                  ").stdout.strip() else 1)"])
        self.assertEqual(self.observed()["status"], 0)

    def test_a_task_naming_NO_command_leaves_the_namespace_ABSENT(self):
        """Absent and empty are different answers: the consumer refuses an
        absent observation with the reason an operator needs, and an empty one
        would look like a producer that ran nothing and said so."""
        self.frozen(verification=[])
        self.assertIsNone(self.observed())
        with open(os.path.join(self.line, "proposal",
                               self.module.VERIFICATION)) as handle:
            self.assertIn("names none", handle.read())

    def test_a_command_that_CANNOT_START_is_UNRUN_and_not_a_failure(self):
        """Absence of evidence is not evidence of failure, and a status would
        tell a reader the command RAN."""
        self.frozen(verification=["/nonexistent/w197661-not-a-command"])
        held = self.observed()
        self.assertIsNotNone(held)
        self.assertIsNone(held["status"])

    def test_a_FAILING_command_is_reported_as_its_own_status(self):
        self.frozen(verification=["python3", "-c", "raise SystemExit(3)"])
        self.assertEqual(self.observed()["status"], 3)

    def test_the_DECLARED_FILE_says_what_ran_and_what_it_answered(self):
        self.frozen()
        self.worked()
        with open(os.path.join(self.line, "proposal",
                               self.module.VERIFICATION)) as handle:
            said = handle.read()
        self.assertIn("status: 0", said)
        self.assertIn("w197661-fixture.txt", said)

    def test_running_it_does_NOT_dirty_the_line(self):
        """The freeze refuses a line with tracked or untracked worktree
        changes, so a required command that wrote into it would stop the
        lifecycle exactly where the declared outputs once did."""
        self.frozen()
        self.worked()
        self.assertEqual(_vcs(self.line, "status", "--porcelain").strip(), "")

    def test_the_command_is_a_REAL_CHECK_and_not_a_rubber_stamp(self):
        """A required test that passes whatever the candidate contains proves
        nothing about it."""
        self.frozen()
        self.worked()
        with open(os.path.join(self.line, "w197661-fixture.txt"), "w") as one:
            one.write("the wrong bytes\n")
        answered = subprocess.run(self.ARGV, cwd=self.line,
                                  capture_output=True, timeout=120)
        self.assertEqual(answered.returncode, 1)

    def test_the_COMPOSED_task_really_names_this_command(self):
        """The argv these cases exercise is the one the episode composed, read
        from the composed document rather than restated here."""
        composed = os.path.join(
            REPO, "work/records/2026/09",
            "finding-v12-worker-launch-version-mismatch",
            "instance-200564/task.json")
        if not os.path.exists(composed):
            self.skipTest("this episode has not been composed yet")
        with open(composed) as handle:
            self.assertEqual(json.load(handle)["verification"], self.ARGV)
if __name__ == "__main__":
    unittest.main()
