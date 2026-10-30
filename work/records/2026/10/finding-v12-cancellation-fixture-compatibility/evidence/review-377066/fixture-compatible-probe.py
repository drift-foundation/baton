import unittest
from tests.manager import test_authoring_enforcement as t
original=t.CancellationFixture.setUp
def compatible(self):
 original(self)
 self.operations.workers[0]['operations']._adapter=lambda *args, **kwargs: self.runtime_adapter
t.CancellationFixture.setUp=compatible
suite=unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(c) for c in (t.LateBindingCancellation,t.BeforeAttachmentCancellation))
r=unittest.TextTestRunner(verbosity=2).run(suite)
print("Diagnostic in-memory fixture-only adaptation; all original assertions retained. Not an unmodified-suite pass.")
raise SystemExit(0 if r.wasSuccessful() else 1)
