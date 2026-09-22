"""Independent packet review. The missing-setup check confirms a defect."""
import json
from pathlib import Path
import signal
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path[:0] = [str(HERE), str(ROOT / 'v12/python/src'), str(ROOT / 'v12/python')]
from baton_v12.contracts import ContractRefusal
import supervisor
import test_generated_packet
import test_supervisor


class Independent(test_generated_packet.TheGeneratedPacketRunsThroughMain):
    def test_main_without_undocumented_workspace_setup_refuses(self):
        packet = self.main_packet()
        with mock.patch.object(self, 'prepared_stores', return_value=None):
            with self.assertRaises(ContractRefusal) as caught:
                self.run_main(packet, drive=True)
        print('FRESH MAIN REFUSAL:', caught.exception)
        self.assertIn('workspace', str(caught.exception).lower())
        self.assertFalse(Path(packet['outcome_path']).exists())
        self.assertFalse(self.engine.starts)


class SignalProof(test_supervisor.TheSupervisorShutsDownWhatItStarted):
    def test_sigterm_at_runtime_read_is_deferred_and_retained(self):
        original = supervisor._runtime_facts
        sent = []
        def read(*args, **kwargs):
            if not sent:
                sent.append(True)
                signal.raise_signal(signal.SIGTERM)
            return original(*args, **kwargs)
        with mock.patch.object(supervisor, '_runtime_facts', side_effect=read):
            with self.assertRaises(supervisor.SupervisorInterrupted) as caught:
                self.timed_out()
        self.assertTrue(sent)
        retained = json.loads(Path(self.packet['outcome_path']).read_text())
        self.assertEqual(retained, caught.exception.outcome)
        self.assertEqual(retained['state'], 'held')
        self.assertIn('signal 15', retained['interruptions'])
        self.assertTrue([argv for argv in self.engine.vectors if argv[1] == 'stop'])


if __name__ == '__main__':
    suite = unittest.TestSuite()
    for cls in (Independent, SignalProof,
                test_generated_packet.TheGeneratedPacketRunsThroughMain,
                test_supervisor.TheSupervisorShutsDownWhatItStarted):
        for name in sorted(n for n in vars(cls) if n.startswith('test_')):
            suite.addTest(cls(name))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
