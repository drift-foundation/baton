"""Observe whether the supposedly unknown start has already been reconciled."""
import json,unittest
from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
from baton_v12.job_manager.integration_capacity import integration_capacity_of
from baton_v12.worker_manager import attempt_runtime_of
from baton_v12.worker_manager.attempts import attempt_start_failure_of
class Research(OneManagedPreparationCompletes):
    def held_after_uncertainty(self, held, preparation, processes, uncertainty, orchestration, *args):
        capacity=integration_capacity_of(held.job,orchestration)
        attempt=next(m['execution_attempt_id'] for m in capacity['members'] if m['phase']=='prepare')
        current=attempt_runtime_of(held.control,attempt)
        failure=attempt_start_failure_of(held.control,attempt)
        start_record=held.control.operation_record(failure['start_operation_id']) if failure else None
        print(json.dumps({'proof':'start-state-after-fault','at_fault':uncertainty,'current':current,'failure':failure,'start_journal':None if start_record is None else {'kind':start_record['kind'],'state':start_record['state']},'process_poll':[p.poll() for p in processes]},sort_keys=True),flush=True)
        return super().held_after_uncertainty(held,preparation,processes,uncertainty,orchestration,*args)
result=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([Research('test_a_committed_start_with_an_uncertain_adapter_answer_stays_held')]))
raise SystemExit(not result.wasSuccessful())
