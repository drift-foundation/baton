"""W2845 cut 5 — the portable catalog, compared against the frozen reference.

The boundary calls the 64 W151 design cases and the 75 frozen Node reference
tests a MIGRATION CHECKLIST.  A checklist nobody compares is a list, so this
file does the comparison: it reads the frozen sources and reports what this
Python suite carries.

WHAT IT DOES NOT DO, said plainly so nobody reads more into a green run:

  * It asserts no name-for-name equality.  The port is by OBLIGATION -- the same
    rule reads differently in a language without getters -- so an equality
    assertion would either be false or force a bad transliteration.
  * The area check below catches an obligation area DISAPPEARING from the suite.
    It says nothing about how well that area is covered; independent review and
    mutation runs are what measure that, and a word in a test name is not
    evidence of a guard.

What it does assert: the frozen reference is present and READ, its size is
re-measured rather than quoted, every frozen file has a named counterpart, and
no obligation area has silently gone missing.
"""

import ast
import pathlib
import re
import unittest

HERE = pathlib.Path(__file__).resolve()
DISTRIBUTION = HERE.parents[2]
SUITE = DISTRIBUTION / "tests" / "authority"
REPOSITORY = DISTRIBUTION.parents[1]
NODE_AUTHORITY_TESTS = REPOSITORY / "v12" / "test"
DESIGN_MODEL = (REPOSITORY / "work" / "records" / "2026" / "08"
                / "finding-v12-isolated-agent-workers" / "findings"
                / "finding-v12-assignment-state-machine" / "evidence"
                / "test_assignment_state_model.py")

FROZEN_FILES = ("authority_assignment.test.mjs", "authority_boundary.test.mjs",
                "authority_contract.test.mjs", "authority_operations.test.mjs",
                "authority_race.test.mjs", "authority_restart.test.mjs")

# Which Python file carries each frozen reference file's obligations.  Written
# out, because "somewhere in the suite" is not a mapping.
COUNTERPARTS = {
    "authority_assignment.test.mjs": "test_assignment.py",
    "authority_boundary.test.mjs": "test_boundary.py",
    "authority_contract.test.mjs": "test_contract.py",
    "authority_operations.test.mjs": "test_operations.py",
    "authority_race.test.mjs": "test_operations.py",
    "authority_restart.test.mjs": "test_operations.py",
}

# Each area lists the ALTERNATIVE fragments that would show it is still here.
# Alternatives rather than one word, because a single fragment fails for the
# wrong reason -- it fails when a case is RENAMED, which is not a defect, and
# writing `policy_generation` when the case reads "binds the generation it was
# granted under" measures my guess at the name rather than the coverage.
AREAS = {
    "the generation counter": ("generation",),
    "the deployment-wide slot": ("slot",),
    "every Handler-clear path": ("handler_clear",),
    "fencing": ("fence",),
    "typed gates": ("gate",),
    "the operation journal": ("journal", "replay"),
    "both kinds of refusal": ("durabl", "ordinary_refusal"),
    "retirement": ("retirement",),
    "settlement": ("settle",),
    "restart": ("restart", "reopen", "survive"),
    "real-process races": ("across_processes", "competing_claims"),
    "contract progression": ("contract",),
    "the proposal": ("proposal",),
    "the four receipts": ("receipt",),
    "configured capabilities": ("capabilit", "capability"),
    "the policy generation": ("granted_under", "policy_generation"),
    "authorized close": ("close",),
    "non-adopting create and open": ("requires_absence", "recognized_store",
                                     "adopt"),
    "exact built-in operands": ("built_ins", "exact_json"),
    "hostile values": ("runs_what_it_is_given", "never_runs_the_value"),
    "the two faces": ("faces", "bootstrap_face"),
    "the session binding": ("binding", "bound_to_one"),
}


def python_case_names():
    names = set()
    for source in sorted(SUITE.glob("*.py")):
        tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test"):
                names.add(node.name)
    return names


class TheMigrationChecklistIsRead(unittest.TestCase):
    """A checklist nobody compares is a list."""

    def test_the_frozen_reference_is_present_and_readable(self):
        # Standing rather than done once: the port's whole basis is these files,
        # and a silently absent one would make every "carried forward" claim
        # unverifiable.  Reporting it is the instruction; this is the report.
        missing = [name for name in FROZEN_FILES
                   if not (NODE_AUTHORITY_TESTS / name).is_file()]
        self.assertEqual(missing, [], "frozen reference evidence is missing")
        self.assertTrue(DESIGN_MODEL.is_file(), str(DESIGN_MODEL))

    def test_every_frozen_reference_file_has_a_named_counterpart(self):
        for frozen, counterpart in sorted(COUNTERPARTS.items()):
            with self.subTest(frozen=frozen):
                self.assertIn(frozen, FROZEN_FILES)
                self.assertTrue((SUITE / counterpart).is_file(), counterpart)

    def test_the_frozen_catalog_is_measured_rather_than_remembered(self):
        # A number in a document and a number in a tree are different facts.
        counted = 0
        for name in FROZEN_FILES:
            text = (NODE_AUTHORITY_TESTS / name).read_text(encoding="utf-8")
            counted += len(re.findall(r"^test\(", text, re.M))
        self.assertGreaterEqual(counted, 75,
                                f"the frozen catalog now measures {counted}")
        model = ast.parse(DESIGN_MODEL.read_text(encoding="utf-8"))
        design = sum(1 for node in ast.walk(model)
                     if isinstance(node, ast.FunctionDef)
                     and node.name.startswith("test_"))
        self.assertGreaterEqual(design, 64,
                                f"the design model now measures {design}")

    def test_no_obligation_area_has_vanished_from_the_suite(self):
        joined = " ".join(sorted(python_case_names()))
        for area, alternatives in sorted(AREAS.items()):
            with self.subTest(area=area):
                # An empty alternative list would pass vacuously, which is the
                # failure mode of every table-driven check.
                self.assertTrue(alternatives, area)
                self.assertTrue(any(fragment in joined
                                    for fragment in alternatives), area)

    def test_the_suite_is_one_gate_and_not_a_pile_of_files(self):
        # Every case lives under tests/authority, so `just gate` runs all of
        # them and nothing sits outside the gate claiming to cover something.
        files = sorted(path.name for path in SUITE.glob("test_*.py"))
        self.assertEqual(files, ["test_assignment.py", "test_boundary.py",
                                 "test_catalog.py", "test_contract.py",
                                 "test_identity.py", "test_operations.py",
                                 "test_session.py", "test_store.py"])
        self.assertEqual([path.name for path in
                          DISTRIBUTION.glob("tests/test_*.py")], [])


if __name__ == "__main__":
    unittest.main()
