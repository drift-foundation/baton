import unittest
from tests.authority import test_session as sessions
from tests.job_manager.test_managed_integration_capacity import ThePreparationIsCoordinatedEndToEnd as Preparation
from tools import single_worker
from baton_v12.contracts import ContractRefusal

class RealAdapter(sessions.SessionCase):
    def test_existing_adapter_claims_and_replays_against_real_authority(self):
        self.work()
        port = single_worker.AuthorityPort(single_worker._ManagerClaimSession(self.claude), single_worker.claim_signature)
        projected = self.claude.project_work(sessions.WORK)
        args = (sessions.WORK, "review-real-claim-168351", sessions.UUID, projected["scope"], projected["route"])
        answer = port.claim(*args)
        self.assertEqual(answer["assignment"], self.claude.assignment_of(sessions.WORK))
        self.assertEqual(answer, port.claim(*args))
        self.assertEqual(answer["assignment"]["participant"], sessions.CLAUDE)

    def test_inquiry_publication_is_an_explicit_refusal(self):
        wrapped = single_worker._ManagerClaimSession(self.claude)
        with self.assertRaises(ContractRefusal) as caught:
            wrapped.publish_answer({})
        self.assertEqual(caught.exception.code, "capability")

suite = unittest.TestSuite([
    unittest.defaultTestLoader.loadTestsFromTestCase(RealAdapter),
    Preparation("test_the_whole_sequence_runs_against_real_owners")])
r = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not r.wasSuccessful())
