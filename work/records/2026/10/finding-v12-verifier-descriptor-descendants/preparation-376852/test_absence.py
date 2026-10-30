"""Focused deterministic cases for the corrected absence classification.

NO ENGINE IS INVOKED. Every case hands `classify` an answer shape, including
the two real shapes the old parser refused, which are recorded here as
OBSERVED rather than imagined: a direct inspect of an absent object answers
exit 1 with `[]` on stdout and a lowercase `error: no such object` on stderr,
and the same call through a child process answers returncode 1 with that same
stderr.
"""

import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import absence                                                   # noqa: E402

NAME = "w325695-proof-376414"
LOWER = "error: no such object: " + NAME


class TheSupportedAbsenceAnswersAreAccepted(unittest.TestCase):

    def test_the_admitted_absence_shape(self):
        """The shape the old parser refused. CORRECTED LABEL: I called this
        "the observed shape", but what I observed was a shell and a child
        process rather than this runner, so this is a shape the classifier
        ADMITS, not one it has seen a runner receive."""
        held = absence.classify(NAME, status=1, stdout="[]", stderr=LOWER)
        self.assertEqual(held["state"], absence.ABSENT)
        self.assertTrue(absence.proved_absent(held))

    def test_empty_stdout_and_uppercase_reason(self):
        """CORRECTED: my third variant named ANOTHER object (`x`) and I
        asserted ABSENT for it. That expectation was wrong -- review
        2026-10-28T19-55-29Z counterexampled exactly it -- so the variants
        here all name THIS object and the foreign one is refused below."""
        for text in ("", "[]", "[ ]"):
            for said in (LOWER, LOWER.upper(),
                         "Error: No Such Object: " + NAME):
                with self.subTest(stdout=text, stderr=said):
                    self.assertEqual(
                        absence.classify(NAME, status=1, stdout=text,
                                         stderr=said)["state"],
                        absence.ABSENT)

    def test_the_no_such_container_spelling(self):
        self.assertEqual(
            absence.classify(
                NAME, status=1, stdout="",
                stderr="Error: No such container: " + NAME)["state"],
            absence.ABSENT)

    def test_the_empty_array_with_zero_status(self):
        self.assertEqual(
            absence.classify(NAME, status=0, stdout="[]",
                             stderr="")["state"], absence.ABSENT)

    def test_both_streams_are_retained(self):
        """So a receipt written from this cannot leave the question the last
        one left open."""
        held = absence.classify(NAME, status=1, stdout="[]", stderr=LOWER)
        self.assertEqual(held["stdout"], "[]")
        self.assertEqual(held["stderr"], LOWER)
        self.assertEqual(held["status"], 1)
        self.assertEqual(held["name"], NAME)


    def test_a_no_such_object_for_another_name_is_uncertain(self):
        """COUNTEREXAMPLE 1. An answer about another object proves nothing
        about this one, and the old substring test accepted it."""
        held = absence.classify(NAME, status=1, stdout="[]",
                                stderr="error: no such object: somebody-else")
        self.assertEqual(held["state"], absence.UNCERTAIN)
        self.assertIn("not this one", held["why"])
        self.assertFalse(absence.proved_absent(held))

    def test_a_mixed_denial_and_no_such_object_is_uncertain(self):
        """COUNTEREXAMPLE 2, and the dangerous direction: a message carrying
        both was read as absence."""
        for said in ("permission denied; error: no such object: " + NAME,
                     "error: no such object: " + NAME
                     + "; cannot connect to the docker daemon"):
            with self.subTest(stderr=said):
                held = absence.classify(NAME, status=1, stdout="[]",
                                        stderr=said)
                self.assertEqual(held["state"], absence.UNCERTAIN)
                self.assertFalse(absence.proved_absent(held))

    def test_zero_status_empty_array_beside_a_denial_is_uncertain(self):
        """COUNTEREXAMPLE 3: the status said 0 and stderr said the caller
        could not reach the daemon; that became ABSENT."""
        held = absence.classify(NAME, status=0, stdout="[]",
                                stderr="permission denied while connecting")
        self.assertEqual(held["state"], absence.UNCERTAIN)
        self.assertFalse(absence.proved_absent(held))

    def test_an_empty_document_is_not_this_object(self):
        """COUNTEREXAMPLE 4: `[{}]` was PRESENT because a missing `Name` was
        tolerated. A document that does not say which object it describes
        describes none."""
        for text in ("[{}]", '[{"Name": null}]', '[{"Id": ""}]'):
            with self.subTest(stdout=text):
                held = absence.classify(NAME, status=0, stdout=text,
                                        stderr="")
                self.assertEqual(held["state"], absence.UNCERTAIN)
                self.assertIn("without this object's identity", held["why"])

    def test_an_identity_match_is_accepted_either_way(self):
        for text in ('[{"Name": "/' + NAME + '"}]',
                     '[{"Name": "' + NAME + '"}]',
                     '[{"Id": "' + NAME + '"}]'):
            with self.subTest(stdout=text):
                self.assertEqual(
                    absence.classify(NAME, status=0, stdout=text,
                                     stderr="")["state"], absence.PRESENT)

class TheObjectMustBePresentForThisExactName(unittest.TestCase):

    def test_a_document_for_this_name_is_present(self):
        held = absence.classify(
            NAME, status=0, stdout='[{"Name": "/' + NAME + '"}]', stderr="")
        self.assertEqual(held["state"], absence.PRESENT)
        self.assertFalse(absence.proved_absent(held))

    def test_a_document_for_another_name_is_uncertain(self):
        held = absence.classify(
            NAME, status=0, stdout='[{"Name": "/somebody-else"}]', stderr="")
        self.assertEqual(held["state"], absence.UNCERTAIN)
        self.assertIn("without this object's identity", held["why"])


class EverythingElseIsUncertainAndProvesNothing(unittest.TestCase):

    def refusing(self, **named):
        held = absence.classify(NAME, **named)
        self.assertEqual(held["state"], absence.UNCERTAIN, held)
        self.assertFalse(absence.proved_absent(held))
        return held["why"]

    def test_permission_denied(self):
        self.refusing(status=1, stdout="",
                      stderr="permission denied while trying to connect")

    def test_daemon_unreachable(self):
        self.refusing(status=1, stdout="",
                      stderr="Cannot connect to the Docker daemon")

    def test_malformed_output(self):
        self.refusing(status=0, stdout="{not json", stderr="")
        self.refusing(status=0, stdout='{"Name": "x"}', stderr="")

    def test_mixed_output_beside_a_no_such_object(self):
        self.refusing(status=1, stdout='[{"Name": "/' + NAME + '"}]',
                      stderr=LOWER)

    def test_more_than_one_object(self):
        self.refusing(status=0, stdout='[{"Name": "/a"}, {"Name": "/b"}]',
                      stderr="")

    def test_an_unrecognised_exit_status(self):
        for status in (2, 125, 126, 137, -9, None, "1"):
            with self.subTest(status=status):
                self.refusing(status=status, stdout="", stderr=LOWER)

    def test_exit_zero_with_nothing(self):
        self.refusing(status=0, stdout="", stderr="")

    def test_a_lost_create_answer_stays_uncertain(self):
        """The property the original design got right and must keep: an
        unreadable answer never proves the object is not there, so nothing may
        be removed or declared clean on it."""
        for said in ("", "i/o timeout", "context deadline exceeded"):
            with self.subTest(stderr=said):
                self.refusing(status=1, stdout="", stderr=said)

    def test_proved_absent_refuses_anything_that_is_not_an_answer(self):
        for value in (None, {}, {"state": "absent-ish"}, "absent", []):
            with self.subTest(value=value):
                self.assertFalse(absence.proved_absent(value))


if __name__ == "__main__":
    unittest.main()
