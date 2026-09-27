import unittest
from unittest import mock
from test_worker_resume import TheWorkerResumesItsOwnLaunchWithoutDispatchingAgain as WorkerCase
from tools import job_manager


class MismatchPremise(WorkerCase):
    def test_claimed_worker_mismatch_is_actually_observed(self):
        original = job_manager._reclaiming
        reports = []
        def recording(*args, **kwargs):
            run = original(*args, **kwargs)
            def once(**named):
                result = run(**named)
                reports.extend(result['unresolved'])
                return result
            return once
        with mock.patch.object(job_manager, '_reclaiming', recording):
            self.test_an_ATTACHED_BOUND_MISMATCH_is_reported_and_never_dispatched_around()
        self.assertTrue(reports)
        self.assertTrue(any(r.get('contradicts_binding') == 'another-runtime' for r in reports),
                        'the claimed mismatch scenario never reported the changed attached runtime: '+repr(reports))


if __name__ == '__main__':
    suite = unittest.TestSuite([MismatchPremise('test_claimed_worker_mismatch_is_actually_observed')])
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
