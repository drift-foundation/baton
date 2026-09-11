import json
from pathlib import Path
import unittest
from tests.tools.test_stage_execution import UnfinishedWorkIsFencedBeforeAnythingRepeatsIt as Case
from baton_v12.worker_manager import attempt_runtime_of, frozen_output_of

case = Case()
case.setUp()
try:
    saved = []
    recover = case.recover
    def capture(held, **options):
        saved.append(held)
        return recover(held, **options)
    case.recover = capture
    case.test_the_recovered_correction_reaches_a_fresh_assignment()
    held = saved[-1]
    result = {'states': case.states(held.job, held.composed),
              'fresh_attempt': held.fresh,
              'fresh_runtime': attempt_runtime_of(held.control, held.fresh),
              'fresh_frozen_output': frozen_output_of(held.control, held.fresh),
              'recovery': case.recovered}
finally:
    case.doCleanups()
controls = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite([
    Case('test_the_discarded_scratch_is_gone_and_the_checkpoint_bytes_are_back'),
    Case('test_the_recovery_replays_and_committed_effects_are_unchanged'),
]))
result['controls_pass'] = controls.wasSuccessful()
Path(__file__).with_suffix('.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({key: result[key] for key in ('states', 'fresh_attempt', 'fresh_frozen_output', 'controls_pass')}, indent=2))
raise SystemExit(0 if controls.wasSuccessful() else 1)
