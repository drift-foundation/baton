"""Adapted from the reviewer's probe-adoption-168621.py after claim168686.

THE SECOND CASE CHANGED SHAPE BECAUSE THE DEFECT DID. `submission` is no
longer an operand of `adopt_prepared_candidate`, so a caller cannot substitute
`source_candidate` at all -- there is nothing left to pass. The probe therefore
asks the two questions that remain askable: that the operand is gone, and that
the substitution path it used to open now goes through the committed request,
which is pinned to the digest the intent fixed before the child Work existed.
"""
import inspect
import unittest

from baton_v12.integration import entries_of, reconciliation as adoption
from tests.integration import test_managed_storage as cases


class AdoptionBindings(unittest.TestCase):
    def setUp(self):
        self.fixture = cases.ThePreparationIsAdoptedFromWhatItCollected()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.addCleanup(self.fixture.tearDown)
        self.store = self.fixture.ended()

    def test_unchanged_collected_preparation_adopts(self):
        held = self.fixture.adopt(self.store)
        self.assertEqual(held["source"], self.fixture.request()["source"])

    def test_foreign_task_digest_refuses(self):
        task = self.fixture.task(self.store, task_digest="sha256:" + "f" * 64)
        with self.assertRaises(cases.ContractRefusal):
            self.fixture.adopt(self.store, task=task)
        self.assertNoWrite()

    def test_the_submission_operand_is_gone(self):
        self.assertNotIn(
            "submission",
            inspect.signature(adoption.adopt_prepared_candidate).parameters)

    def test_a_substituted_candidate_now_refuses_at_the_intent(self):
        request = self.fixture.request()
        other = dict(request, source=dict(request["source"],
                                          candidate="f" * 40))
        with self.assertRaises(cases.ContractRefusal) as caught:
            self.fixture.adopt(self.store, request=other)
        self.assertIn("the committed intent decided", str(caught.exception))
        self.assertNoWrite()

    def test_every_unrequested_member_comes_from_the_accepted_entry(self):
        held = self.fixture.adopt(self.store)
        recorded = cases.managed_result_of(self.fixture.coordinated(),
                                           held["managed_result_id"])
        request = self.fixture.request()
        [entry] = [one for one in entries_of(self.fixture.coordinated(),
                                             self.fixture.TARGET)
                   if one["proposal_id"] == request["source_proposal_id"]]
        for stored, owned in (("source_checkpoint_id", "checkpoint_id"),
                              ("source_verdict_id", "verdict_id"),
                              ("source_result_id", "result_id"),
                              ("source_result_digest", "result_digest"),
                              ("source_checkpoint_digest",
                               "checkpoint_digest"),
                              ("work_id", "work_id")):
            self.assertEqual(recorded[stored], entry[owned], stored)
        self.assertNotEqual(recorded["work_id"], self.fixture.EXECUTION_WORK)

    def assertNoWrite(self):
        held = self.fixture.coordinated()
        for table in ("managed_integration_results",
                      "managed_integration_phases"):
            self.assertEqual(held._connection.execute(
                "SELECT COUNT(*) FROM " + table).fetchone()[0], 0, table)


if __name__ == "__main__":
    unittest.main(verbosity=2)
