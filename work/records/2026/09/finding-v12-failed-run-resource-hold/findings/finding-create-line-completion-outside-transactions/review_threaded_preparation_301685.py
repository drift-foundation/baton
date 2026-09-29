"""Actual second-thread/store-handle exclusion with independent-line progress."""
import threading
import unittest
from unittest import mock
from tests.manager.test_review_cycles import StableLineLifecycle, NOW, BASE, AUTHORITY, WORK, nominate_source
from baton_v12.worker_manager import ControlStore, review_cycles
from baton_v12.contracts import ContractRefusal

class ThreadedPreparation(StableLineLifecycle):
    def test_other_thread_refuses_same_line_and_completes_independent_line(self):
        materialize = self.profile.materialize
        entered = False
        results, failures = [], []
        def competitor():
            try:
                with ControlStore.open(self.control_path, incarnation="threaded-review", clock=lambda: NOW) as store:
                    operands=dict(source=nominate_source(self.source), declared_base=BASE, profile=self.profile, authority_uuid=AUTHORITY)
                    try:
                        review_cycles.create_line(store,work_id=WORK,**operands)
                    except ContractRefusal:
                        results.append("same-refused")
                    else:
                        results.append("same-admitted")
                    results.append(review_cycles.create_line(store,work_id="independent-review-work",**operands)["state"])
            except BaseException as error:
                failures.append(repr(error))
        def pause(source, path, base):
            nonlocal entered
            if not entered:
                entered=True
                thread=threading.Thread(target=competitor)
                thread.start()
                thread.join(5)
                self.assertFalse(thread.is_alive(), "independent database/line work blocked behind preparation")
                self.assertEqual(failures, [])
                self.assertEqual(results, ["same-refused", "idle"])
            return materialize(source,path,base)
        with mock.patch.object(self.profile,"materialize",side_effect=pause):
            self.assertEqual(self.line()["state"],"idle")
        self.assertEqual(self.profile.materialize_calls,2)
        self.assertEqual(self.line()["state"],"idle")
        self.assertEqual(self.profile.materialize_calls,2)

if __name__ == "__main__":
    result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([ThreadedPreparation("test_other_thread_refuses_same_line_and_completes_independent_line")]))
    raise SystemExit(not result.wasSuccessful())
