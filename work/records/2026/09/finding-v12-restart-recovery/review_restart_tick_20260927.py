import unittest
from test_restart_recovery import RestartCase, Killed
from baton_v12.worker_manager import tokens
from tests.manager.test_offers import NOW
from tools import job_manager


class RestartTick(RestartCase):
    def test_production_pass_visits_unsettled_unexpired_launch(self):
        inputs = self.prepared()
        runtime = Killed()
        self.assertIsInstance(self.starting(runtime, inputs), KeyboardInterrupt)
        fresh = self.restarted()
        held = tokens.unresolved(fresh, self.domain)
        self.assertEqual(len(held), 1)
        self.assertFalse(held[0]['expired'])
        calls = []

        def unavailable(argv, **kwargs):
            calls.append(list(argv))
            raise OSError('controlled engine unavailable after manager restart')

        answer = job_manager._reclaiming(fresh, 'docker', unavailable)(now=NOW)
        self.assertTrue(calls, 'production pass never attempted observation of the unresolved launch: '+repr(answer))
        self.assertEqual(len(tokens.outstanding(fresh, self.domain)), 1)
        self.assertEqual(len(runtime.started), 1)


if __name__ == '__main__':
    suite = unittest.TestSuite([RestartTick('test_production_pass_visits_unsettled_unexpired_launch')])
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
