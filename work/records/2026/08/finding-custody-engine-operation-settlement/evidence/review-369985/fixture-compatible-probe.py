from tests.manager.test_authoring_enforcement import LateBindingCancellation
x=LateBindingCancellation('test_late_bind_and_later_activation_are_stopped_under_the_original_fence')
x.setUp()
try:
 worker=x.operations.workers[0]['operations']
 worker._adapter=lambda *args, **kwargs: x.runtime_adapter
 x.test_late_bind_and_later_activation_are_stopped_under_the_original_fence()
 print('PASS: unchanged test assertions with only fixture adapter keyword compatibility restored; not an unmodified-suite pass')
finally:
 x.doCleanups();x.tearDown()
