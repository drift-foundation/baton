import sys,os,json
sys.path[:0]=['v12/python','v12/python/src','work/records/2026/09/finding-v12-single-implementation-proof']
import test_candidates
c=test_candidates.Collector();c.setUp()
try:
 before=c.one(); parent=os.path.dirname(c.place);os.chmod(parent,0)
 try:
  try:os.stat(c.place);stat_error=None
  except OSError as e:stat_error={'type':type(e).__name__,'errno':e.errno}
  after=c.one()
 finally:os.chmod(parent,0o755)
 print(json.dumps({'uid':os.getuid(),'before':before,'stat_error':stat_error,'after':after},indent=2))
finally:c.doCleanups()
