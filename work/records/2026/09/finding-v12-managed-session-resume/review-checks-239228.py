"""Copied-source imports and production composition; simulated effects only."""
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BOUND = Path('/home/sl/baton-runs/managed-correction-236087/manager-source')
sys.path[:0] = [str(HERE), str(BOUND), str(ROOT / 'v12/python')]
import baton_v12
from tools import stage_execution
from tests.job_manager import fixtures
import supervisor
import test_generated_packet


class CopiedSource(test_generated_packet.TheGeneratedPacketRunsThroughMain):
    def imported_source(self):
        manifest = json.loads((HERE / 'MANAGER-SOURCE-238462.json').read_text())
        return {key: manifest[key] for key in ('path', 'files', 'file_count', 'packages')}

    def main_packet(self, **bounds):
        packet = super().main_packet(**bounds)
        packet['code_boundary'] = str(BOUND)
        Path(self.main_packet_path).write_text(json.dumps(packet))
        self.assertTrue(str(Path(baton_v12.__file__).resolve()).startswith(str(BOUND)))
        self.assertEqual(Path(stage_execution.__file__).resolve(), BOUND / 'tools/stage_execution.py')
        return packet

    def composing(self, driven):
        def compose(packet, job, control, stream):
            ordinary = stage_execution.operations_from
            def effects(configuration, jobs, controls, **named):
                self.assertEqual(named, {'checkout': str(BOUND)})
                return ordinary(configuration, jobs, controls, **named,
                    engine_run=self.engine,
                    credential_provider=lambda provider, reference: self.secret,
                    clock=lambda: fixtures.NOW)
            with mock.patch.object(stage_execution, 'operations_from', side_effect=effects):
                composed = supervisor._compose(packet, job, control, stream)
            self._composed = composed
            self.addCleanup(composed.close)
            driven.append((job, control, composed))
            return composed
        return compose


if __name__ == '__main__':
    suite = unittest.TestSuite(CopiedSource(name) for name in (
        'test_main_completes_the_correction_and_exits_zero',
        'test_main_holds_and_exits_one_when_the_bound_elapses'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
