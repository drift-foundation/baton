"""W376586 — what the supported recipes actually carry, and whether it imports.

WHY THIS FILE EXISTS. Review 2026-10-28T20-07-16Z found `claude_agent.py:467`
importing `adapter_refusal` unconditionally while no line of `Dockerfile.claude`
carried the module: the supported fresh image would have died
`ModuleNotFoundError` before the worker started. That is the second time this
distribution has shipped exactly that defect -- W39357's entry point opened
with an unconditional `from scripted_agent import ScriptedAgent` and the same
failure was found by a build gate, not by reading the recipe.

SO THE RULE IS DERIVED FROM THE RECIPES AND THE SOURCE, never listed by hand.
These cases parse each recipe's `COPY` directives, materialize exactly what
they name into a temporary root, and import the programs THERE -- with the
repository nowhere on `sys.path`. A hand-written list of expected modules would
have agreed with the defect, because the defect was that a list did not mention
a module.

WHAT THIS IS NOT. No image is built, pulled, inspected or run. A recipe is a
source artefact and this is source analysis of it: these cases prove that the
files a recipe names are sufficient to import the programs it installs, which
is a necessary condition for a working image and not a claim that one exists.
`test_dogfood_image` and the container gates own the built artefact.
"""

import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
CONTEXT = {"Dockerfile": WORKER,
           "Dockerfile.claude": WORKER.parent,
           "Dockerfile.integration": WORKER.parent,
           "Dockerfile.reconciliation": WORKER.parent}

# The one target directory every recipe installs into, and the only one these
# cases reproduce. A `COPY` to anywhere else is not part of the import path and
# is reported rather than staged.
INSTALL = "/opt/baton/"

# W376586: THE SHARED TYPED REFUSAL, by file name. It is named once, here, as
# the SUBJECT of these cases; which recipes must carry it is derived below from
# which recipes carry the programs that import it.
SHARED = "adapter_refusal.py"

# WHAT COUNTS AS REQUIRING THE MODULE, and the anchor is the point: an
# UNINDENTED import must succeed for the program to load at all, so the recipe
# that installs that program must carry it. `baton_worker`'s import is guarded
# inside a `try` and is therefore indented -- it does not require the layer,
# because an image with no role adapter has nothing that can raise a typed
# refusal and its clause is unreachable rather than wrong. Both spellings are
# admitted because the two programs use different ones.
REQUIRED = r"^(?:import adapter_refusal\b|from adapter_refusal import)"


def _directives(recipe):
    """Every `COPY` in one recipe, as `(source, target)`, continuations joined.

    A SMALL PARSER ON PURPOSE. It understands the two forms these recipes use
    -- one line, and a line ending in a backslash -- and nothing else, because
    a parser that guessed at `--from`, globs or JSON form would be a parser
    whose silence meant "no such layer" for a reason nobody could see. An
    unparsable `COPY` is reported as a failure rather than skipped.
    """
    text = recipe.read_text(encoding="utf-8")
    joined = re.sub(r"\\\s*\n\s*", " ", text)
    found = []
    for line in joined.splitlines():
        stripped = line.strip()
        if not stripped.upper().startswith("COPY "):
            continue
        parts = stripped.split()[1:]
        if len(parts) != 2 or parts[0].startswith("--"):
            raise AssertionError(f"{recipe.name} carries a COPY this case "
                                 f"cannot read: {stripped!r}")
        found.append((parts[0], parts[1]))
    return found


class EveryRecipeCarriesWhatItsProgramsImport(unittest.TestCase):
    """The rule, derived from the source rather than restated beside it."""

    def copied(self, name):
        return {source: target for source, target in _directives(
            WORKER / name)}

    def test_the_recipes_this_suite_reads_are_the_ones_on_disk(self):
        """A recipe added without a case here would be invisible, so the set is
        held against the directory rather than taken from this module."""
        self.assertEqual(
            sorted(one.name for one in WORKER.iterdir()
                   if one.name.startswith("Dockerfile")),
            sorted(CONTEXT))

    def test_every_recipe_carrying_an_importer_carries_the_shared_module(self):
        """THE DERIVED RULE. For each recipe, the programs it installs are read
        for an import that REQUIRES the module -- unindented, so a guarded one
        does not count -- and the recipe must carry it iff one of them does.
        Both directions matter: a missing layer is the defect found, and a layer
        nothing requires is weight an image should not carry, which the
        reference image's own exhaustive-contents gate asserts about itself."""
        for name, context in sorted(CONTEXT.items()):
            with self.subTest(recipe=name):
                copied = self.copied(name)
                importers = sorted(
                    source for source in copied
                    if source.endswith(".py")
                    and re.search(REQUIRED, (context / source).read_text(
                        encoding="utf-8"), re.M))
                carried = [source for source in copied
                           if pathlib.PurePath(source).name == SHARED]
                self.assertEqual(
                    bool(importers), bool(carried),
                    f"{name} installs {importers} and carries {carried}")

    def test_the_shared_module_lands_under_the_name_the_image_gives_it(self):
        """A TOP-LEVEL NAME, like `attempt_log_format` and `source_profiles`:
        the programs spell `adapter_refusal`, so a layer that installed it
        inside a package directory would not satisfy the import."""
        for name in sorted(CONTEXT):
            with self.subTest(recipe=name):
                for source, target in _directives(WORKER / name):
                    if pathlib.PurePath(source).name != SHARED:
                        continue
                    self.assertEqual(target, INSTALL + SHARED)

    def test_the_shared_module_pulls_in_nothing(self):
        """It is the dependency every recipe now has, so what IT depends on is
        every recipe's problem. One class and seven literals, and no import at
        all -- including nothing from `baton_v12`, which is the isolation rule
        these images are built on."""
        text = (WORKER / SHARED).read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"^\s*(?:import|from)\s+\S+", text,
                                    re.M), [])
        self.assertNotIn("baton_v12", text)


class TheRecipeLayersAreEnoughToImportThePrograms(unittest.TestCase):
    """The packaged-import fixture, with NO REPOSITORY PATH TO RESCUE IT.

    Review 2026-10-28T20-07-16Z requires an "actual packaged-import fixture
    [showing] producer and catcher share the same exception identity with no
    repository-path rescue". The suites that drive these programs put the
    checkout's own directories on `sys.path` -- which reproduces the image's
    LAYOUT and is right for them, but means a missing `COPY` cannot fail them:
    the module is there either way. So these cases stage ONLY what a recipe
    names, into a directory that is not in the checkout, and run a child
    interpreter whose `sys.path` contains that directory and the standard
    library.
    """

    maxDiff = None

    def staged(self, name):
        """One recipe's `/opt/baton/` contents, and nothing else, on disk."""
        root = pathlib.Path(tempfile.mkdtemp(prefix="v12-packaged-"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        context = CONTEXT[name]
        for source, target in _directives(WORKER / name):
            if not target.startswith(INSTALL):
                continue
            place = root / target[len(INSTALL):]
            origin = context / source
            self.assertTrue(origin.exists(), f"{name} copies a missing "
                                             f"{source}")
            if origin.is_dir():
                shutil.copytree(origin, place)
            else:
                place.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(origin, place)
        return root

    def ran(self, root, program):
        """One child interpreter, isolated from this one and from the tree.

        THE ENVIRONMENT IS COMPOSED RATHER THAN INHERITED -- exactly `PATH` and
        `PYTHONPATH` -- so nothing this process holds can put the checkout back
        on the child's path. `-B` keeps the staged root free of bytecode, for
        `test_worker_image`'s reason: this directory is written repeatedly
        inside one filesystem timestamp tick. What the path actually is, the
        child proves about itself in `PROOF` before importing anything of ours,
        because an assertion made out here is an assertion about the wrong
        process.
        """
        return subprocess.run(
            [sys.executable, "-B", "-c", program], cwd=root,
            env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(root),
                 "PYTHONDONTWRITEBYTECODE": "1"},
            capture_output=True, text=True, timeout=120)

    def proving(self, root, body):
        answer = self.ran(root, PROOF + body)
        self.assertEqual((answer.returncode, answer.stderr.strip()),
                         (0, ""), answer.stdout + answer.stderr)
        return answer.stdout

    def test_the_fresh_recipe_s_layers_import_both_programs(self):
        root = self.staged("Dockerfile.claude")
        self.proving(root, '''
import baton_worker, claude_agent, adapter_refusal
assert baton_worker.adapter_refusal is adapter_refusal
assert claude_agent._SharedDeclarationRefusal is \\
    adapter_refusal.AdapterDeclarationRefusal
''')

    def test_the_producer_and_the_catcher_share_one_type_in_the_package(self):
        """THE PROPERTY THE SHARED MODULE EXISTS FOR, proved where it matters:
        a refusal raised by the installed adapter's own class is caught by the
        installed worker's `except`, with only the recipe's own files
        reachable. A duplicate definition in either program would make this
        child exit non-zero."""
        root = self.staged("Dockerfile.claude")
        out = self.proving(root, '''
import adapter_refusal, baton_worker, claude_agent

# THE SELECTED LANE IS `review` HERE AND THE REFUSAL NAMES THE SAME ONE:
# review 2026-10-28T21-25-27Z, the typed role is now bound to the launch's.
raised = claude_agent.DeclarationRefusal(
    "the declaration is unusable", code=adapter_refusal.SET_INVALID,
    role="review")
try:
    raise raised
except baton_worker.adapter_refusal.AdapterDeclarationRefusal as caught:
    held = baton_worker._adapter_failure(caught, "work", "work:attempt-1",
                                         "review")
else:
    raise SystemExit("the worker's except did not catch the adapter's class")
assert held == {"component": "role-adapter",
                "code": "declaration-set-invalid", "role": "review",
                "operation": "work", "operation_id": "work:attempt-1"}, held
print("caught")
''')
        self.assertEqual(out.strip().splitlines()[-1], "caught")

    def test_the_overlay_recipe_s_layers_import_the_adapter(self):
        """The integration overlay copies `claude_agent` too, and a dependency
        satisfied by whatever a provider base happens to carry is not a
        dependency the recipe states."""
        root = self.staged("Dockerfile.integration")
        self.proving(root, '''
import adapter_refusal, baton_worker, claude_agent
assert baton_worker.adapter_refusal is adapter_refusal
''')

    def test_the_two_recipes_without_an_adapter_import_the_worker_alone(self):
        """THE OTHER DIRECTION, and it is why the worker's import is guarded.

        The reference and preparation images ship no role adapter, so nothing
        in them can raise a typed refusal and the catch clause is unreachable
        rather than wrong. Both recipes keep the exhaustive layer contents
        their own gates assert, and the worker still loads -- with the inert
        stand-in in place of the shared module.
        """
        for name in ("Dockerfile", "Dockerfile.reconciliation"):
            with self.subTest(recipe=name):
                root = self.staged(name)
                self.assertFalse((root / SHARED).exists())
                self.proving(root, INERT)

    def test_an_adapter_without_its_module_fails_loudly_and_early(self):
        """THE CASE THAT GIVES THE GUARD ITS MEANING. The producer imports the
        shared module at its TOP LEVEL, so the recipe the review found could
        not have imported its own adapter -- the absence is fatal before this
        program starts, which is why a guarded import in the worker cannot
        quietly cost a catch. A fixture that passed either way would prove
        nothing about packaging, which is why the checkout-path suites could
        not catch this."""
        for name in ("Dockerfile.claude", "Dockerfile.integration"):
            with self.subTest(recipe=name):
                root = self.staged(name)
                (root / SHARED).unlink()
                answer = self.ran(root, PROOF + "import claude_agent\n")
                self.assertNotEqual(answer.returncode, 0)
                self.assertIn("No module named 'adapter_refusal'",
                              answer.stderr)
                # AND THE WORKER STILL STARTS, which is the whole asymmetry:
                # an image missing this layer loses its adapter loudly and
                # does not lose its transport.
                self.proving(root, INERT)


# WHAT THE WORKER LOOKS LIKE WITH NO SHARED MODULE REACHABLE. The stand-in is
# INERT -- a private type nothing in this distribution raises, constructs or
# exports -- so the catch clause is unreachable rather than a second definition
# of the shared class, which is what the amendment forbids.
INERT = '''
import baton_worker
assert baton_worker.TERMINAL_SCHEMA.endswith("/2")
held = baton_worker.adapter_refusal
assert held.__name__ == "_NoTypedRefusal", held
assert (held.CODES, held.ROLES, held.COMPONENT) == ((), (), None)
assert baton_worker._adapter_failure(
    held.AdapterDeclarationRefusal("x"), "work", "work:a",
    "implementation") is None
'''


# WHAT EVERY CHILD PROVES FIRST, before it imports anything of ours: that this
# repository is not reachable. A packaged-import fixture whose child could fall
# back to the checkout is a fixture that cannot fail, and the defect it is here
# to catch is precisely a module that the checkout has and the image does not.
PROOF = f'''
import os, sys
repository = {str(WORKER.parents[1])!r}
for place in sys.path:
    resolved = os.path.realpath(place) if place else os.path.realpath(os.getcwd())
    assert not resolved.startswith(repository), (place, "the checkout is reachable")
assert os.path.realpath(os.getcwd()) != repository
'''


if __name__ == "__main__":
    unittest.main()
