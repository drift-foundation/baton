"""Independent receipt-before-reply interruption proof; deterministic engine/provider."""
import unittest
from unittest.mock import patch
from test_provider_effect_cut import (
    TheProviderEffectIsPerformedOnceAcrossARestart as Fixture,
    Executor, Engine, exchange, fixtures, reconcile, submit, status, tokens,
)

class ReceiptCut(Fixture):
    def test_interruption_after_effect_before_publication_returns(self):
        engine = Engine()
        executors = {}
        seen = self.inviting(lambda delivery: executors.setdefault(delivery.attempt_id, Executor(delivery)))
        invited = exchange.publish_command
        cuts = []
        def interrupt(delivery, document):
            result = invited(delivery, document)
            if result['published'] and not cuts:
                cuts.append(result)
                raise KeyboardInterrupt('receipt persisted; publication has not returned')
            return result
        with patch.object(exchange, 'publish_command', interrupt):
            job, control = self.stores('review-receipt-cut')
            self.control = control
            submit(job, self.submission)
            operations = self.ticking(job, control, engine)
            with self.assertRaises(KeyboardInterrupt):
                for _ in range(8):
                    reconcile(job, operations, now=fixtures.NOW)
            self.assertEqual(len(cuts), 1)
            attempt_id = self.only_attempt(control)
            executor = executors[attempt_id]
            self.assertEqual(len(executor.effects), 1)
            domain = self.domain_of(control, attempt_id)
            operations.close()
            job.close()
            control.close()
            job, control = self.stores('review-receipt-cut')
            self.control = control
            resumed = self.ticking(job, control, engine)
            self.addCleanup(resumed.close)
            for _ in range(8):
                reconcile(job, resumed, now=fixtures.NOW)
            self.assertEqual(len(executor.effects), 1)
            self.assertEqual(len(seen['invitations']), 1)
            self.assertEqual(len(seen['publications']), 1)
            self.assertEqual(len(engine.starts), 1)
            self.assertEqual(len(engine.activations), 1)
            observed = exchange.observation(self._adopted(attempt_id))
            self.assertIsNotNone(observed['receipt'])
            self.assertIsNone(observed['terminal'])
            self.assertEqual(observed['state'], 'working')
            self.assertEqual(status(job, resumed, observed_at=fixtures.NOW)['jobs'][0]['stages'][0]['state'], 'running')
            self.assertEqual(len(tokens.outstanding(control, domain)), 1)

if __name__ == '__main__':
    suite = unittest.TestSuite([ReceiptCut('test_interruption_after_effect_before_publication_returns')])
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
