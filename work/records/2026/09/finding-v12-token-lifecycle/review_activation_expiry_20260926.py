"""Independent W275774 probe: expiry after binding, before adapter activation.
Controlled engine only; no Docker/provider processes.
"""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'activation_subject', Path(__file__).with_name('test_activation_boundary.py'))
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)

class ActivationExpiry(unittest.TestCase):
    def test_expiry_after_binding_must_not_activate(self):
        fixture = subject.ActivationBoundary()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        token = fixture.held(seconds=1)
        subject.tokens.journal_launch(fixture.store, token, 'runtime.start:1')
        adapter = fixture.adapter(fixture.acting())
        def binding(runtime_id):
            subject.tokens.bind_container(fixture.store, token, runtime_id,
                                          launch='runtime.start:1')
            self.assertTrue(subject.tokens.effects_permitted(fixture.store, token))
            # Deterministic suspension after successful bind and before activation.
            fixture.instant = '2026-09-26T15:00:00.000Z'
            self.assertFalse(subject.tokens.effects_permitted(fixture.store, token))
        try:
            adapter.start(fixture.request(), bind=binding)
        except subject.ContractRefusal:
            pass
        self.assertNotIn(['docker', 'start', 'runtime-1'], fixture.engine.vectors,
                         'expired bound permission must not admit a fresh activation')

if __name__ == '__main__':
    unittest.main()
