"""Independent bounded verification; passing counterexamples confirm defects."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE), str(ROOT / 'v12/python/src'), str(ROOT / 'v12/python')]
import supervisor
import test_generated_packet
import test_supervisor
from tests.job_manager import fixtures
from tests.tools import test_single_worker, test_stage_execution


class Counterexamples(test_generated_packet.TheGeneratedPacketDrivesTheRealEntrypoint):
    def test_interrupt_in_runtime_read_escapes_without_outcome(self):
        packet = dict(self.packet_for(), bounds=dict(self.packet['bounds'],
                      total_seconds=8, cleanup_seconds=3))
        job, control, composed = self.serving()
        ticks = iter(range(10000))
        with mock.patch.object(supervisor, '_runtime_facts', side_effect=KeyboardInterrupt('SIGTERM during runtime read')):
            with self.assertRaises(KeyboardInterrupt):
                supervisor.supervise(job, control, composed, packet,
                    clock=lambda: fixtures.NOW, sleep=lambda seconds: None,
                    monotonic=lambda: float(next(ticks)))
        self.assertFalse(Path(packet['outcome_path']).exists())
        self.assertTrue(self.engine.starts)
        self.assertFalse([argv for argv in self.engine.vectors if argv[1] == 'stop'])

    def test_generated_fixture_packet_refuses_at_actual_main(self):
        self.packet_for()
        stream = io.StringIO()
        inspect = mock.Mock(side_effect=AssertionError('No real engine allowed'))
        result = supervisor.main(['--packet', self.generated_packet_path,
                                  '--incarnation', 'review-238615'],
                                 stream=stream, image_inspect=inspect)
        self.assertEqual(result, 2, stream.getvalue())
        inspect.assert_not_called()
        self.assertIn('refused before anything opened', stream.getvalue())
        print('ACTUAL MAIN:', stream.getvalue().strip())


if __name__ == '__main__':
    suite = unittest.TestSuite()
    for cls in (Counterexamples,
                test_generated_packet.TheGeneratedPacketDrivesTheRealEntrypoint,
                test_supervisor.TheSupervisorShutsDownWhatItStarted,
                test_single_worker.TheDeploymentCanStopWhatItStarted,
                test_stage_execution.TheDeploymentRoutesACancellationToItsOwner):
        for name in sorted(name for name in vars(cls) if name.startswith('test_')):
            suite.addTest(cls(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
