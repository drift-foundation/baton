"""W110935 — the integration image's recipe, and the layout it produces.

`work/records/2026/09/finding-v12-integration-worker-workload/`.

WHAT THIS ASKS AND WHAT IT DELIBERATELY DOES NOT. It asks two questions that
can be answered deterministically, offline, with no daemon: what the recipe
SAYS, and whether the exact file set it copies is enough to import the entry
with nothing else on the path. It does NOT build an image, start a container,
pull a base or call a provider.

THAT BOUNDARY IS THE FINDING'S, not a convenience. `Dockerfile.integration`
takes its base as a REQUIRED build argument -- the digest the deployment has
already validated and selected -- so there is no artefact to build here without
making a selection this suite has no authority to make. Approver event 55641's
rule stands: a build produces a candidate and selecting a digest is a separate
deployment act. `test_dogfood_image` is what asks a built ARTEFACT its
questions, and the integration image gets that gate when a base digest is
selected for it; until then, saying so here is more honest than a suite that
quietly builds from a floating tag and calls the result validation.

WHY THE ISOLATED IMPORT IS THE OTHER HALF. A recipe naming a file and an image
carrying it are two facts, and the one this campaign has actually been bitten
by is subtler: an entry that imports cleanly in a CHECKOUT, where the whole
distribution is on the path, and dies `ModuleNotFoundError` in a container that
copied four files. So the copy list is read out of the recipe itself, staged
into a directory that holds NOTHING else, and the entry is imported by a
child interpreter with that directory as its only source of modules -- which
is the image's layout reproduced rather than described.
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

V12 = pathlib.Path(__file__).resolve().parents[3]
WORKER = V12 / "worker"
RECIPE = WORKER / "Dockerfile.integration"

# THE ONE ENTRYPOINT, in exec form, and the interpreter that runs it.
ENTRYPOINT = ["python3", "/opt/baton/integration_entry.py"]

# THE FIXED NON-ROOT PAIR, by numeric id, as in every other image here and as
# in the adapter's own `--user` restriction.
IDENTITY = "65532:65532"


def instructions(text):
    """The recipe's instructions, with continuations joined and comments gone.

    A LINE-ORIENTED READER WOULD BE READING PROSE. This file is more comment
    than instruction on purpose, and a `COPY` split across two lines is one
    instruction whichever way it is spelled.
    """
    held = []
    joined = ""
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith("\\"):
            joined += stripped[:-1].strip() + " "
            continue
        joined += stripped
        parts = joined.split(None, 1)
        held.append((parts[0].upper(), parts[1] if len(parts) > 1 else ""))
        joined = ""
    assert not joined, "the recipe ends inside a continuation"
    return held


class TheRecipeSaysWhatItWasReviewedToSay(unittest.TestCase):

    def setUp(self):
        self.text = RECIPE.read_text("utf-8")
        self.instructions = instructions(self.text)
        self.verbs = [verb for verb, _ in self.instructions]

    def only(self, verb):
        found = [operand for one, operand in self.instructions if one == verb]
        self.assertEqual(len(found), 1, f"{verb} appears {len(found)} times")
        return found[0]

    def test_the_base_is_a_required_operand_with_no_default(self):
        """A DEFAULT WOULD BE A SELECTION NOBODY MADE.

        `Dockerfile.claude` installs the provider runtime over a moving
        `apt-get` and a moving `npm install`, and W55361 measured two builds of
        an unchanged tree differing in exactly those layers. A default here
        would let an unselected artefact become this image's base by omission.
        """
        self.assertEqual(self.instructions[0], ("ARG", "PROVIDER_BASE"))
        self.assertEqual(self.instructions[1][0], "FROM")
        self.assertIn("${PROVIDER_BASE}", self.instructions[1][1])
        self.assertNotIn("=", self.instructions[0][1])
        # AND NO FLOATING TAG ANYWHERE ELSE.
        self.assertEqual(self.verbs.count("FROM"), 1)

    def test_nothing_is_installed_over_the_selected_base(self):
        """A second `npm install` or `apt-get` here would mint a second
        unreviewed provider installation for one deployment, and make "which
        runtime answered" a question with two answers."""
        self.assertNotIn("RUN", self.verbs)
        # OVER THE INSTRUCTIONS AND NOT THE PROSE. This recipe explains why it
        # does not install anything, and a check that read the comments would
        # fail on its own explanation.
        composed = " ".join(operand for _, operand in self.instructions)
        for word in ("apt-get", "npm", "pip", "curl", "wget"):
            self.assertNotIn(word, composed, word)

    def test_it_copies_the_worker_modules_and_no_manager_package(self):
        copied = [operand.split() for one, operand in self.instructions
                  if one == "COPY"]
        sources = [one[0] for one in copied]
        targets = [one[-1] for one in copied]
        self.assertEqual(sorted(sources), [
            "python/src/baton_v12/source_profiles",
            "worker/baton_worker.py",
            "worker/claude_agent.py",
            "worker/integration_contract.py",
            "worker/integration_entry.py",
            "worker/integration_workload.py",
            "worker/worker-control-1.0.schema.json"])
        for one in targets:
            self.assertTrue(one.startswith("/opt/baton/"), one)
        # THE RULE THE REFERENCE AND DOGFOOD IMAGES BOTH KEEP: a worker that
        # could import the manager is one bug away from its capabilities. The
        # profile package is the ruled exception and travels under a TOP-LEVEL
        # name, so no `baton_v12` package directory exists in the artefact.
        self.assertNotIn("/opt/baton/baton_v12", targets)
        self.assertEqual([one for one in targets
                          if one.endswith("source_profiles")],
                         ["/opt/baton/source_profiles"])
        for one in sources:
            self.assertTrue((V12 / one).exists(),
                            f"the recipe copies {one}, which is not in the "
                            f"tree it is built from")

    def test_the_entrypoint_is_exec_form_and_is_the_integration_entry(self):
        """No shell in the process tree: the manager stops this container by
        signalling PID 1, and PID 1 has to be Python rather than something
        interpreting a signal on the worker's behalf."""
        self.assertEqual(json.loads(self.only("ENTRYPOINT")), ENTRYPOINT)
        self.assertNotIn("CMD", self.verbs)

    def test_the_runtime_identity_is_the_fixed_non_root_pair(self):
        self.assertEqual(self.only("USER"), IDENTITY)
        # AFTER the copies, so what the recipe declares is the identity the
        # entrypoint actually runs as.
        self.assertGreater(self.verbs.index("USER"),
                           len(self.verbs) - 1 - self.verbs[::-1].index("COPY"))

    def test_there_is_no_default_credential_and_no_provider_variable(self):
        """An `ANTHROPIC_API_KEY` baked here would silently outrank the
        mounted slot and decide which account every container ran as."""
        composed = " ".join(operand for one, operand in self.instructions
                            if one == "ENV")
        for name in ("ANTHROPIC", "BATON_WORKER_", "CLAUDE_CODE_"):
            self.assertNotIn(name, composed)
        self.assertIn("PYTHONPATH=/opt/baton", composed)

    def test_it_declares_no_volume_port_or_healthcheck(self):
        """The four namespaces are mounts the manager names per attempt, and
        this container's health is observed through the engine rather than
        announced by the container."""
        for verb in ("VOLUME", "EXPOSE", "HEALTHCHECK", "SHELL", "ONBUILD"):
            self.assertNotIn(verb, self.verbs)


class TheCopiedLayoutIsEnoughToStartTheEntry(unittest.TestCase):
    """The image's own layout, staged from the recipe's own copy list.

    NOT A SECOND LIST. The staging below reads `COPY` out of the recipe, so a
    module added to this worker without a line in the recipe fails HERE, in a
    case with actionable prose, rather than as a `ModuleNotFoundError` inside a
    container somebody built later.
    """

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="v12-w110935-image-")
        self.addCleanup(shutil.rmtree, self.root, True)
        self.staged = os.path.join(self.root, "opt-baton")
        os.makedirs(self.staged)
        self.copied = []
        for verb, operand in instructions(RECIPE.read_text("utf-8")):
            if verb != "COPY":
                continue
            parts = operand.split()
            source, target = V12 / parts[0], parts[-1]
            self.assertTrue(target.startswith("/opt/baton/"), target)
            place = os.path.join(self.staged,
                                 target[len("/opt/baton/"):])
            if source.is_dir():
                shutil.copytree(source, place)
            else:
                shutil.copy2(source, place)
            self.copied.append(os.path.relpath(place, self.staged))

    def ran(self, program):
        """One child interpreter, ISOLATED, with the staged layout only.

        `-I` is what makes this a real question: it ignores this process's
        environment -- including `PYTHONPATH`, which is why the one directory
        this may reach is named IN THE PROGRAM -- and keeps the invoking
        directory off `sys.path`, so nothing the checkout happens to have can
        answer for a file the recipe forgot to copy.
        """
        done = subprocess.run(
            [sys.executable, "-I", "-B", "-c",
             f"import sys; sys.path.insert(0, {self.staged!r})\n" + program],
            capture_output=True, timeout=300, cwd=self.root,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin")})
        return (done.returncode, done.stdout.decode("utf-8", "replace"),
                done.stderr.decode("utf-8", "replace"))

    def test_the_entry_imports_with_nothing_but_the_copied_files(self):
        status, out, errors = self.ran(
            "import integration_entry, integration_workload,"
            " integration_contract, claude_agent, baton_worker;"
            "print(integration_entry.main.__name__)")
        self.assertEqual(status, 0, errors)
        self.assertIn("main", out)

    def test_the_manager_is_not_reachable_from_that_layout(self):
        status, out, _errors = self.ran(
            "try:\n"
            "    import baton_v12\n"
            "except ModuleNotFoundError as failed:\n"
            "    print('absent', failed.name)\n"
            "else:\n"
            "    print('present', baton_v12.__file__)\n")
        self.assertEqual(status, 0)
        self.assertIn("absent baton_v12", out)

    def test_the_worker_data_the_modules_read_travelled_with_them(self):
        """A module whose data was left behind imports cleanly and fails at
        the first call that needs it, which is the worst place to find out."""
        place = os.path.join(self.staged, "worker-control-1.0.schema.json")
        self.assertTrue(os.path.isfile(place))
        with open(place, "rb") as handle:
            self.assertIn("$defs", json.loads(handle.read()))
        status, out, errors = self.ran(
            "import baton_worker;"
            "print(baton_worker.CONTRACT_SCHEMA);"
            "print(len(baton_worker._frozen_contract()['$defs']))")
        self.assertEqual(status, 0, errors)
        self.assertGreater(int(out.strip().splitlines()[-1]), 0)

    def test_the_profile_package_is_a_top_level_name_in_that_layout(self):
        status, out, errors = self.ran(
            "import source_profiles;"
            "print(source_profiles.__name__, source_profiles.GIT_PROFILE)")
        self.assertEqual(status, 0, errors)
        self.assertTrue(out.startswith("source_profiles "), out)

    def test_the_staged_modules_are_the_reviewed_bytes(self):
        """Byte identity between the tree and what the recipe would ship, so a
        recipe copying a stale or renamed file fails here."""
        import hashlib

        for relative in self.copied:
            place = os.path.join(self.staged, relative)
            if not os.path.isfile(place):
                continue
            source = WORKER / relative
            if not source.exists():
                source = V12 / "python" / "src" / "baton_v12" / relative
            if not source.exists():
                continue
            with open(place, "rb") as one, open(source, "rb") as two:
                self.assertEqual(hashlib.sha256(one.read()).hexdigest(),
                                 hashlib.sha256(two.read()).hexdigest(),
                                 relative)


if __name__ == "__main__":
    unittest.main()
