"""W10265 — the two ruled assertion sites keep rendering in a fixed order.

`work/records/2026/08/finding-v12-deterministic-assertion-rendering/`.

A failing `unittest` assertion puts `repr()` of its operands in the failure
text. When an operand is a SET of strings or tuples of strings, that text comes
out in hash order, which is per-process — so two runs of the same failing test
on the same tree disagree, and "did my change alter the failures?" stops being
answerable by `diff`. The failing test id, the count and the verdict were
always stable; only the diagnostic moved.

WHY THIS IS A SOURCE-SHAPE TEST AND NOT AN OUTPUT COMPARISON. Proving the real
property needs two interpreters with different `PYTHONHASHSEED` values, and
the assertions it would compare only render while those tests are FAILING —
so the check would evaporate the moment the underlying gaps are closed, which
is exactly when a regression would slip back in unnoticed. The shape of the
assertion is the durable thing, so that is what is pinned here. The two-seed
output comparison is recorded as evidence in the record above.

SCOPE IS THE RULED BOUNDARY AND NOTHING ELSE. Slawomir's approval (T10265,
message 10719) covers exactly two existing assertions in
`test_boundary_inventory.py`. Three other sites in the tree use the same
`assertEqual(..., set())` idiom — one in `tests/authority/test_boundary.py` and
two in `tests/authority/test_session.py` — and they are deliberately NOT
checked here: those tests pass today, so nothing renders, and editing them was
not approved. They are recorded as latent in the finding rather than quietly
swept in.
"""

import ast
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest

INVENTORY = pathlib.Path(__file__).resolve().parent / "test_boundary_inventory.py"


def function_named(name):
    """The `ast` node for one test function, found by name."""
    tree = ast.parse(INVENTORY.read_text(encoding="utf-8"), filename=str(INVENTORY))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    raise AssertionError(f"{name} is no longer in {INVENTORY.name}; "
                         "W10265's ruling names it explicitly, so a rename needs "
                         "the finding updated rather than this test deleted")


def calls_to(node, attribute):
    for inner in ast.walk(node):
        if (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Attribute)
                and inner.func.attr == attribute):
            yield inner


def is_sorted_call(node):
    return (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == "sorted")


class TheRuledAssertionsRenderThroughSortedCollections(unittest.TestCase):

    def test_the_stale_owner_check_asserts_membership_against_a_sorted_container(self):
        """`assertIn` prints the WHOLE container when membership fails."""
        found = list(calls_to(function_named("test_no_declared_owner_is_stale"), "assertIn"))
        self.assertEqual(len(found), 1, "the ruling names exactly one assertIn here")
        container = found[0].args[1]
        self.assertTrue(is_sorted_call(container),
                        "W10265 ruled this container sorted so the failure text is "
                        "stable; a bare set here reorders it every run")

    def test_the_missing_probe_check_compares_a_sorted_list_with_an_empty_list(self):
        """The empty-difference verdict is unchanged; its rendering is pinned."""
        found = list(calls_to(function_named("test_the_missing_probe_check_can_actually_fail"),
                              "assertEqual"))
        self.assertGreaterEqual(len(found), 1)
        first = found[0]
        self.assertTrue(is_sorted_call(first.args[0]),
                        "the difference must be sorted before it is compared")
        self.assertIsInstance(first.args[1], ast.List,
                              "compare against [] rather than set(): comparing two sets "
                              "is what made unittest render the difference in hash order")
        self.assertEqual(first.args[1].elts, [], "the verdict is still emptiness")

    def test_neither_ruled_site_compares_against_a_bare_set_call(self):
        """The exact idiom the ruling replaced, kept out of both functions."""
        for name in ("test_no_declared_owner_is_stale",
                     "test_the_missing_probe_check_can_actually_fail"):
            with self.subTest(function=name):
                for call in calls_to(function_named(name), "assertEqual"):
                    for side in call.args[:2]:
                        bare_set = (isinstance(side, ast.Call)
                                    and isinstance(side.func, ast.Name)
                                    and side.func.id == "set"
                                    and not side.args)
                        self.assertFalse(bare_set,
                                         "assertEqual(..., set()) renders a nonempty "
                                         "difference in hash order")


# -- the property itself, proved rather than described ------------------------

# The seeds the rendering is compared under. More than two, because two could
# agree by accident over a small collection and a control that passes by luck
# is the failure mode this whole record is about.
SEEDS = ("1", "2", "3", "5", "7", "11")

# The elapsed-time line, which varies for reasons that are nobody's defect. It
# is filtered rather than made stable: the approval excludes elapsed-time
# output explicitly, and a record promising byte-identical whole output would
# be promising something it cannot keep.
ELAPSED = re.compile(r"^Ran \d+ tests? in .*$", re.M)

# The failing operands. Tuples of strings, because that is what both ruled
# sites hold and because string hashing is what is salted per process -- a set
# of small integers would render in a stable order and prove nothing.
OPERANDS = [(kind, f"module_{at}.py:function_{at}", f"subject.member_{at}")
            for at, kind in enumerate(
                ("caller", "adopted", "injected") * 6)]

RULED = """
        self.maxDiff = None
        self.assertEqual(sorted(MISSING), [])
"""

OLD = """
        self.assertEqual(MISSING, set())
"""

PROGRAM = """
import unittest

MISSING = set({operands})


class Rendering(unittest.TestCase):

    def test_the_difference_is_reported(self):
{body}


if __name__ == "__main__":
    unittest.main()
"""


class TheRuledFormRendersCompletelyAndIdentically(unittest.TestCase):
    """The two-interpreter proof, over a failing assertion this file OWNS.

    The module above pins the SHAPE of the two ruled sites, and says why: the
    diagnostics they render only exist while those tests are failing, so an
    output comparison against them would evaporate the moment the underlying
    gaps close. That argument is right about THOSE sites and it does not
    excuse never proving the property.

    So this proves it over a failure of its own making. The assertion here is
    the ruled form, character for character, over operands shaped like the
    real ones -- and it will still be failing, and still be comparable, long
    after the boundary inventory is green.
    """

    def setUp(self):
        # ONE PATH FOR EVERY SEED, and this is not tidiness. The first version
        # made a fresh temporary directory per run, and a traceback names the
        # file it came from -- so six runs disagreed on the path and the
        # determinism check failed for a reason that had nothing to do with
        # what it is about. The harness has to hold everything but the seed
        # still, or it measures itself.
        self.root = tempfile.TemporaryDirectory(prefix="v12-w10265-")
        self.addCleanup(self.root.cleanup)

    def rendered(self, body, seed):
        """One run of a synthetic failing assertion, under one hash seed."""
        source = pathlib.Path(self.root.name) / "rendering_probe.py"
        source.write_text(PROGRAM.format(operands=repr(sorted(OPERANDS)),
                                         body=textwrap.indent(
                                             textwrap.dedent(body).strip("\n"),
                                             "        ")),
                          encoding="utf-8")
        finished = subprocess.run([sys.executable, str(source)],
                                  capture_output=True, timeout=120,
                                  env=dict(os.environ, PYTHONHASHSEED=seed),
                                  cwd=self.root.name)
        return ELAPSED.sub("", finished.stderr.decode("utf-8", "replace"))

    def test_the_ruled_form_renders_identically_under_every_seed(self):
        """DETERMINISM. One rendering, whatever the process decided its hash
        salt would be."""
        seen = {self.rendered(RULED, seed) for seed in SEEDS}
        self.assertEqual(len(seen), 1,
                         f"{len(seen)} renderings across {len(SEEDS)} seeds")

    def test_the_ruled_form_renders_every_missing_entry(self):
        """COMPLETENESS -- review R1's half, and the reason the ruling added
        `maxDiff`. Determinism bought by printing one entry and a truncation
        notice would be a diagnostic that agrees with itself and says
        nothing."""
        text = self.rendered(RULED, SEEDS[0])
        self.assertNotIn("Set self.maxDiff to None", text,
                         "the diagnostic is truncated")
        missing = [entry for entry in OPERANDS
                   if entry[1] not in text or entry[2] not in text]
        self.assertEqual(missing, [],
                         f"{len(missing)} of {len(OPERANDS)} entries are not "
                         f"in the failure text")

    def test_the_ruled_form_renders_in_sorted_order(self):
        """The fixed order is the SORTED one rather than merely a repeatable
        one: two people reading two runs have to be able to find an entry."""
        text = self.rendered(RULED, SEEDS[0])
        at = [text.index(entry[2]) for entry in sorted(OPERANDS)]
        self.assertEqual(at, sorted(at), "the entries are not in sorted order")

    def test_the_form_the_ruling_replaced_still_reorders(self):
        """THE CONTROL. A determinism check whose subject cannot vary is a
        check that passes for the wrong reason, so the same harness is pointed
        at the idiom this Work removed and required to catch it.

        If a future interpreter renders set differences in a stable order this
        fails, and the ruled form becomes belt and braces rather than the fix
        -- which is the right way round for a claim about somebody else's
        implementation.
        """
        seen = {self.rendered(OLD, seed) for seed in SEEDS}
        self.assertGreater(len(seen), 1,
                           "the replaced idiom rendered identically under "
                           f"all {len(SEEDS)} seeds, so this harness cannot "
                           "detect the defect it is here to prevent")

    def test_the_control_and_the_ruled_form_report_the_same_verdict(self):
        """Neither form changes what is TRUE. The whole ruling turned on
        rendering, and a correction that had altered the verdict would be a
        different change wearing this one's approval."""
        for what, body in (("ruled", RULED), ("replaced", OLD)):
            with self.subTest(form=what):
                text = self.rendered(body, SEEDS[0])
                self.assertIn("FAILED (failures=1)", text)


class TheMaxDiffCorrectionIsTestLocal(unittest.TestCase):
    """T10265 message 11462 approved a TEST-LOCAL assignment.

    A module-level or class-level default would be the output normalization
    the same ruling excludes -- it would change every other diagnostic in that
    file, none of which was reviewed for it.
    """

    def test_the_ruled_function_sets_maxdiff_before_its_comparison(self):
        node = function_named("test_the_missing_probe_check_can_actually_fail")
        setters = [inner for inner in ast.walk(node)
                   if isinstance(inner, ast.Assign)
                   and any(isinstance(target, ast.Attribute)
                           and target.attr == "maxDiff"
                           for target in inner.targets)]
        self.assertEqual(len(setters), 1,
                         "the ruling names exactly one maxDiff assignment")
        self.assertIsInstance(setters[0].value, ast.Constant)
        self.assertIsNone(setters[0].value.value, "maxDiff = None restores "
                          "the whole list; any other value truncates again")
        comparison = list(calls_to(node, "assertEqual"))[0]
        self.assertLess(setters[0].lineno, comparison.lineno,
                        "the assignment has to precede the comparison it "
                        "un-truncates")

    def test_no_other_test_in_the_inventory_sets_maxdiff(self):
        """The boundary, checked rather than promised. Widening this to the
        module would have changed diagnostics nobody reviewed."""
        tree = ast.parse(INVENTORY.read_text(encoding="utf-8"),
                         filename=str(INVENTORY))
        owners = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Assign)
                        and any(isinstance(target, ast.Attribute)
                                and target.attr == "maxDiff"
                                for target in inner.targets)):
                    owners.append(node.name)
        self.assertEqual(owners,
                         ["test_the_missing_probe_check_can_actually_fail"])


if __name__ == "__main__":
    unittest.main()
