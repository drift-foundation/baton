import types,json
from tests.tools.test_bootstrap import ARepeatProvisionsTheWorkerSourcesItNames
f=ARepeatProvisionsTheWorkerSourcesItNames('test_missing_worker_sources_are_cloned_from_the_target_and_proved');f.setUp()
try:
 issued=[];destination=f.fresh_instance(issued)
 workers=[f.composed_for(destination,'impl-a','implementation','baton.impl-a'),f.composed_for(destination,'review-a','review','baton.reviewer')]
 original=f.git
 def refusing(calls):
  run=original(calls)
  def execute(argv,**kw):
   if 'cat-file' in argv:
    calls.append(list(argv));return types.SimpleNamespace(returncode=1,stdout='',stderr='declared base missing')
   return run(argv,**kw)
  return execute
 f.git=refusing
 first,said,_=f.repeated(destination,issued,workers,'--repository-source',f.SOURCE)
 mark=len(issued)
 second,again,_=f.repeated(destination,issued,workers,'--repository-source',f.SOURCE)
 print(json.dumps({'first_code':first,'first_output':said,'retry_code':second,'retry_git_calls':issued[mark:],'retry_output':again}))
finally:
 f.tearDown();f.doCleanups()
