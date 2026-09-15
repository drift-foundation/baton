"""Independently assert the public missing-delivery answer discarded by the test."""
from unittest.mock import patch
from tests.tools import test_execution_limits as tests
from tools import stage_execution
answers=[]
class Observed(tests.TheComposedObservationAdoptsTwoJobsConfiguredLaunches):
    def _guarded(self,held,stack,captured,*,present=True):
        super()._guarded(held,stack,captured,present=present)
        original=stage_execution.StageObservation.observe_exchange
        def reading(reader,stage):
            answer=original(reader,stage)
            answers.append({'job_id':stage['job_id'],'answer':answer})
            return answer
        stack.enter_context(patch.object(stage_execution.StageObservation,'observe_exchange',reading))
case=Observed('test_an_absent_delivery_is_answered_and_never_repaired')
try:
    case.setUp();case.test_an_absent_delivery_is_answered_and_never_repaired()
    assert answers==[{'job_id':'job-a','answer':None}],answers
    print({'public_missing_delivery_answers':answers,'owner_discard_and_no_recreation_assertions':'passed'})
finally:
    case.doCleanups()
