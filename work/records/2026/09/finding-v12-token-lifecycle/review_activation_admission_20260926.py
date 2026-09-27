"""Independent admission probes using the current permission callback contract."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('activation_subject', Path(__file__).with_name('test_activation_boundary.py'))
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

class Admission(unittest.TestCase):
    def fixture(self):
        f = subject.ActivationBoundary()
        f.setUp()
        self.addCleanup(f.doCleanups)
        t = f.held()
        subject.tokens.journal_launch(f.store, t, 'runtime.start:1')
        return f, t, f.adapter(f.acting())

    def test_valid_permission_observes_post_bind_expiry(self):
        f, token, adapter = self.fixture()
        checked = []
        def bind(runtime_id):
            subject.tokens.bind_container(f.store, token, runtime_id, launch='runtime.start:1')
            f.instant = '2026-09-26T15:00:00.000Z'
            def permit():
                checked.append(True)
                return subject.tokens.effects_permitted(f.store, token)
            return permit
        with self.assertRaises(subject.ContractRefusal):
            adapter.start(f.request(), bind=bind)
        self.assertEqual(checked, [True], 'must reach valid permission, not reject its absence')
        self.assertNotIn(['docker', 'start', 'runtime-1'], f.engine.vectors)

    def test_inflight_activation_cannot_follow_return_and_replacement(self):
        f, token, adapter = self.fixture()
        replacements = []
        def bind(runtime_id):
            subject.tokens.bind_container(f.store, token, runtime_id, launch='runtime.start:1')
            def permit():
                admitted = subject.tokens.effects_permitted(f.store, token)
                self.assertTrue(admitted)
                # Suspend after the permission read. Another host sees the created
                # container inert, settles it, and attempts a new generation.
                subject.tokens.returned(f.store, token, cessation={
                    'domain':token['domain'], 'generation':token['generation'],
                    'launch':'runtime.start:1', 'container':runtime_id,
                    'stopped':True, 'helpers':[]})
                replacements.append(subject.tokens.acquire(f.store, f.domain,
                    operation='runtime.start:2', execution='attempt-2', attempt='attempt-2'))
                return admitted
            return permit
        adapter.start(f.request(), bind=bind)
        self.assertEqual(replacements[0]['generation'], 2)
        self.assertNotIn(['docker', 'start', 'runtime-1'], f.engine.vectors,
                         'a delayed generation-1 activation followed generation-2 acquisition')

if __name__ == '__main__':
    unittest.main()
