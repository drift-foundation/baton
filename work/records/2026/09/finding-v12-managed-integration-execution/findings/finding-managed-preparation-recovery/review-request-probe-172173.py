"""Diagnose the dropped request_digest perturbation without changing tests."""
import pathlib, unittest
from tools import integration_worker
from tests.tools.test_managed_preparation import OneManagedPreparationCompletes
path=pathlib.Path('/home/sl/src/baton/v12/python/tests/tools/test_managed_preparation.py')
source=path.read_text()
needle='with mock.patch.object(\n                            preparation, "_operands",\n                            self.disagreeing(preparation, perturb)):'
replacement='with mock.patch.object(\n                            preparation, "_operands",\n                            self.disagreeing(preparation, perturb)), mock.patch.object(\n                            integration_worker.ManagedPreparation, "_published", changed_publication):'
assert source.count(needle)==1
original_published=integration_worker.ManagedPreparation._published
def changed_publication(instance, place):
    request=original_published(instance, place)
    # Valid request member changed at the normal publication reader boundary.
    # This is simulated reader corruption, not on-disk tamper evidence.
    return dict(request, harness_digest='sha256:'+'0'*64)
namespace={'__name__':'request_probe_candidate','__file__':str(path),'changed_publication':changed_publication}
exec(compile(source.replace(needle,replacement),str(path),'exec'),namespace)
Changed=namespace['OneManagedPreparationCompletes']
Changed.DENIAL=dict(Changed.DENIAL,request_digest='must name one request')
class Research(unittest.TestCase):
    def run_case(self, cls, cut):
        held=cls('test_ordinary_sweeps_retain_and_adopt_one_real_preparation')
        self.addCleanup(held.doCleanups)
        held.complete(cut,perturb='request_digest')
    def test_unused_resolver_digest_does_not_change_authoritative_request(self):
        with self.assertRaisesRegex(AssertionError, 'ordinary deferral'):
            self.run_case(OneManagedPreparationCompletes,'child_admit')
    def test_actual_request_disagreement_refuses_at_window_3(self):
        self.run_case(Changed,'create')
    def test_actual_request_disagreement_refuses_at_window_4(self):
        self.run_case(Changed,'child_admit')
result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Research))
raise SystemExit(not result.wasSuccessful())
