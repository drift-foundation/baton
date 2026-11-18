"""Read-only collection and standard unittest execution with explicit accounting."""
import json,os,sys,unittest
from pathlib import Path
snapshot=Path(os.environ['W384944_SNAPSHOT'])
sys.path[:0]=[str(snapshot/'v12/python/src'),str(snapshot/'v12/python')]
def ids(suite):
 for item in suite:
  if isinstance(item,unittest.TestSuite):yield from ids(item)
  else:yield item.id()
loader=unittest.TestLoader()
if sys.argv[1]=='--collect':
 selections=json.loads(Path(sys.argv[2]).read_text());collected={name:list(ids(loader.loadTestsFromName(name))) for name in selections}
 allids=[i for group in collected.values() for i in group];assert not loader.errors,loader.errors;assert len(allids)==len(set(allids)), 'duplicate selected IDs'
 Path(os.environ['W384944_LEDGER']).write_text(json.dumps(collected,indent=2)+'\n');print('Collected',len(allids),'unique tests');sys.exit(0)
suite=loader.loadTestsFromNames(sys.argv[1:]);expected=list(ids(suite))
class LedgerResult(unittest.TextTestResult):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw);self.started_ids=[];self.passed_ids=[];self.subtests=[]
 def startTest(self,test):self.started_ids.append(test.id());super().startTest(test)
 def addSuccess(self,test):self.passed_ids.append(test.id());super().addSuccess(test)
 def addSubTest(self,test,subtest,err):
  self.subtests.append(dict(parent=test.id(),id=subtest.id(),outcome='passed' if err is None else 'failed' if issubclass(err[0],test.failureException) else 'error'));super().addSubTest(test,subtest,err)
result=unittest.TextTestRunner(verbosity=2,resultclass=LedgerResult,failfast=True).run(suite)
ledger=dict(collected=expected,started=result.started_ids,passed=result.passed_ids,failed=[t.id() for t,_ in result.failures],errors=[t.id() for t,_ in result.errors],skipped=[(t.id(),why) for t,why in result.skipped],expected_failures=[t.id() for t,_ in result.expectedFailures],unexpected_successes=[t.id() for t in result.unexpectedSuccesses],subtests=result.subtests,unaccounted=sorted(set(expected)-set(result.started_ids)),duplicates=len(result.started_ids)-len(set(result.started_ids)),loader_errors=loader.errors)
Path(os.environ['W384944_LEDGER']).write_text(json.dumps(ledger,indent=2)+'\n')
sys.exit(0 if result.wasSuccessful() and len(result.passed_ids)==len(expected) and not ledger['duplicates'] and not ledger['unaccounted'] and not ledger['skipped'] else 1)
