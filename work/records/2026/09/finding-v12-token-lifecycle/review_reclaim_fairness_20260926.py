"""A capped expiry pass must not starve a later overdue runtime behind holds."""
import unittest
from unittest.mock import patch
from tools import job_manager as tool

class FairExpiry(unittest.TestCase):
    def test_next_tick_reaches_runtime_after_held_first_batch(self):
        rows = [{'runtime_attempt_id': str(n)} for n in range(tool._RECLAIM_CANDIDATES + 1)]
        class Governance:
            def identity(self, row): return row['runtime_attempt_id']
            def overdue(self, *args, **kwargs): return {'generation': 1}
        seen = []
        def reclaim(*args, attempt_id, **kwargs):
            seen.append(attempt_id)
            return {'reclaimed': 'held', 'attempt_id': attempt_id}
        with patch.object(tool.tokens, 'workspace_governance', return_value=Governance()), patch.object(tool.attempts, '_attempts', return_value=rows), patch.object(tool.attempts, '_start_operation_id', side_effect=lambda row: row['runtime_attempt_id']), patch.object(tool.intake, 'reclaim_expired_resource', side_effect=reclaim):
            sweep = tool._reclaiming(None, 'docker', None)
            sweep(now='tick-1')
            sweep(now='tick-2')
        self.assertIn(str(tool._RECLAIM_CANDIDATES), seen, 'later overdue runtime never reached while first batch remains held')

if __name__ == '__main__':
    unittest.main()
