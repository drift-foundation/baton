"""W376586 — the shared typed declaration refusal and the four-code producer.

PRE-PROVIDER BY CONSTRUCTION: every case calls the role selector directly, so
no provider, engine or launch is reached. The identity case imports the SHARED
module and the workload independently, which is the amendment's requirement
that "actual package imports" share the exception type -- a duplicate class
would make the catcher's `except` test the wrong object.
"""

import pathlib
import shutil
import sys
import unittest

WORKER = pathlib.Path(__file__).resolve().parents[3] / "worker"
sys.path.insert(0, str(WORKER))
# The workload resolves a few package-side names on its own import path, the
# way `test_claude_agent` already arranges it.
sys.path.insert(0, str(WORKER.parent / "python" / "src" / "baton_v12"))
sys.path.insert(0, str(WORKER.parent / "python" / "src"))
shutil.rmtree(WORKER / "__pycache__", ignore_errors=True)

import adapter_refusal                                           # noqa: E402
import claude_agent                                              # noqa: E402

PRODUCE = {"implementation": claude_agent.IMPLEMENTATION_OUTPUTS,
           "review": claude_agent.REVIEW_OUTPUTS}


def declaration(name, required=False):
    return {"name": name, "required": required}


def every(**changed):
    held = {one: declaration(one) for one in claude_agent.COMMON_OUTPUTS}
    held.update(changed)
    return list(held.values())


class TheExceptionTypeIsSharedAndClosed(unittest.TestCase):

    def test_the_workloads_refusal_is_the_shared_one(self):
        """ACTUAL PACKAGE IMPORTS, independently resolved."""
        self.assertTrue(issubclass(claude_agent.DeclarationRefusal,
                                   adapter_refusal.AdapterDeclarationRefusal))
        self.assertTrue(issubclass(claude_agent.DeclarationRefusal,
                                   claude_agent.TaskRefusal))

    def test_the_four_codes_and_two_roles_are_the_closed_sets(self):
        self.assertEqual(adapter_refusal.CODES,
                         ("declaration-set-invalid",
                          "declaration-name-unsupported",
                          "role-output-missing",
                          "other-role-output-required"))
        self.assertEqual(adapter_refusal.ROLES,
                         ("implementation", "review"))
        self.assertEqual(adapter_refusal.COMPONENT, "role-adapter")

    def test_an_invented_code_or_role_is_a_programming_fault(self):
        """It raises `ValueError`, not a task refusal, so it can never be
        reported as a cause."""
        for code, role in (("made-up", "review"),
                           ("role-output-missing", "integration"),
                           (None, "review"), ("role-output-missing", None)):
            with self.subTest(code=code, role=role):
                with self.assertRaises(ValueError):
                    adapter_refusal.AdapterDeclarationRefusal(
                        "x", code=code, role=role)

    def test_the_facts_carry_three_members_and_nothing_else(self):
        held = adapter_refusal.AdapterDeclarationRefusal(
            "a secret-shaped message sk-012345", code="role-output-missing",
            role="review")
        self.assertEqual(held.facts(), {"component": "role-adapter",
                                        "code": "role-output-missing",
                                        "role": "review"})
        self.assertNotIn("sk-", repr(sorted(held.facts().items())))


class TheFourCodesComeFromTheRealSelector(unittest.TestCase):

    def refusing(self, declared, role):
        with self.assertRaises(claude_agent.DeclarationRefusal) as caught:
            claude_agent._selected(declared, PRODUCE[role], role)
        held = caught.exception
        self.assertEqual(held.component, "role-adapter")
        self.assertEqual(held.role, role)
        return held.code

    def test_valid_declarations_still_proceed_for_both_roles(self):
        for role in adapter_refusal.ROLES:
            with self.subTest(role=role):
                produce, absent = claude_agent._selected(
                    every(), PRODUCE[role], role)
                self.assertEqual([one["name"] for one in produce],
                                 list(PRODUCE[role]))
                self.assertEqual(
                    sorted(one["name"] for one in absent),
                    sorted(one for one in claude_agent.COMMON_OUTPUTS
                           if one not in PRODUCE[role]))

    def test_an_unusable_declaration_set(self):
        for role in adapter_refusal.ROLES:
            for declared in ([], None, "proposal",
                             [declaration("logs"), declaration("logs")]):
                with self.subTest(role=role, declared=declared):
                    self.assertEqual(self.refusing(declared, role),
                                     adapter_refusal.SET_INVALID)

    def test_an_unsupported_declared_name(self):
        for role in adapter_refusal.ROLES:
            with self.subTest(role=role):
                self.assertEqual(
                    self.refusing(every() + [declaration("receipts")], role),
                    adapter_refusal.NAME_UNSUPPORTED)

    def test_a_missing_output_this_role_writes(self):
        for role in adapter_refusal.ROLES:
            with self.subTest(role=role):
                held = [one for one in every()
                        if one["name"] not in PRODUCE[role]]
                self.assertEqual(self.refusing(held, role),
                                 adapter_refusal.ROLE_OUTPUT_MISSING)

    def test_the_other_roles_output_declared_required(self):
        for role in adapter_refusal.ROLES:
            other = [one for one in claude_agent.COMMON_OUTPUTS
                     if one not in PRODUCE[role]][0]
            with self.subTest(role=role, other=other):
                self.assertEqual(
                    self.refusing(
                        every(**{other: declaration(other, True)}), role),
                    adapter_refusal.OTHER_ROLE_OUTPUT_REQUIRED)

    def test_the_check_order_is_preserved(self):
        """A set fault and a name fault together still report the SET fault,
        because the existing order asks that question first."""
        self.assertEqual(
            self.refusing([declaration("receipts"),
                           declaration("receipts")], "review"),
            adapter_refusal.SET_INVALID)


class EverythingElseStaysGeneric(unittest.TestCase):

    def test_a_generic_refusal_is_not_typed(self):
        held = claude_agent.TaskRefusal("something else went wrong")
        self.assertFalse(isinstance(
            held, adapter_refusal.AdapterDeclarationRefusal))

    def test_a_malformed_declaration_entry_is_not_one_of_the_four(self):
        """A declaration whose ENTRY is malformed is a general fault; it must
        not acquire a code by resembling one."""
        for declared in ([None], [{"required": False}], [7],
                         [{"name": None, "required": False}]):
            with self.subTest(declared=declared):
                with self.assertRaises(Exception) as caught:
                    claude_agent._selected(declared, PRODUCE["review"],
                                           "review")
                self.assertFalse(
                    isinstance(caught.exception,
                               adapter_refusal.AdapterDeclarationRefusal),
                    caught.exception)


if __name__ == "__main__":
    unittest.main()
