import json
from tests.manager.test_authoring_enforcement import LateBindingCancellation
x=LateBindingCancellation('test_late_bind_and_later_activation_are_stopped_under_the_original_fence')
x.setUp()
try:
 lane=x.lane();x.clock.advance(240);r=lane.tick();print(json.dumps({'report':r,'calls':x.session.calls,'token':x.current()},default=str,indent=2))
finally:
 x.doCleanups();x.tearDown()
