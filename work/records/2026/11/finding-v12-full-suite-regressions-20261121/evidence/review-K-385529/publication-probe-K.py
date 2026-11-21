"""Force the reader's turn at actual Path.write_text open-before-write boundary."""
import ast,json,os,sys,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
repo=Path('/var/tmp/baton-v12-w385517b/base'); candidate=Path('/var/tmp/baton-v12-w385517b/cand/v12/python')
sys.path[:0]=[str(candidate),str(candidate/'src')]
from tests.manager import test_authoring_manager_guard as fixture
start=time.monotonic()
source=(repo/'v12/python/tests/manager/test_authoring_manager_guard.py').read_text()
node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.Expr) and "(root / 'action.json').write_text" in ast.get_source_segment(source,n))
statement=ast.get_source_segment(source,node)
# Select the innermost matching expression (the direct write call).
assert statement.startswith("(root / 'action.json').write_text")
with tempfile.TemporaryDirectory(dir='/var/tmp/baton-v12-w385517b/tmp') as tmp:
 root=Path(tmp); real_open=Path.open; observations=[]
 def reader_turn(path,*args,**kwargs):
  stream=real_open(path,*args,**kwargs)
  if path.name=='action.json' and (args[0] if args else kwargs.get('mode'))=='w':
   assert path.exists()
   data=path.read_text()
   try: json.loads(data)
   except json.JSONDecodeError as error:
    observations.append({'exists':True,'bytes':data,'error':str(error),'position':error.pos})
   else: raise AssertionError('legacy writer unexpectedly already complete')
  return stream
 with patch.object(Path,'open',reader_turn):
  exec(statement,{'root':root,'json':json,'os':os,'result':{'acts':[]},'guard':type('Guard',(),{'pid':123})()})
 assert observations and observations[0]['position']==0
 print(json.dumps({'original_statement':statement,'forced_read':observations,'after_write':json.loads((root/'action.json').read_text())},indent=2))
# Show the new readiness invariant rejects that legacy publication primitive.
def legacy(root,action):
 (root/'partial.txt').write_text('retained author output')
 (root/'action.json').write_text(json.dumps(action))
with patch.object(fixture,'publish_action',legacy):
 suite=unittest.defaultTestLoader.loadTestsFromTestCase(fixture.ActionPublication)
 result=unittest.TextTestRunner(verbosity=2).run(suite)
 assert len(result.failures)==1 and not result.errors and result.testsRun==1
print(json.dumps({'expected_negative_control_failures':1,'seconds':time.monotonic()-start}))
