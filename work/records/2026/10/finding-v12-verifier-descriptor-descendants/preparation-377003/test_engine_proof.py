"""Fault injection only; never calls Docker or sleeps."""
import importlib.util,json,pathlib,subprocess,tempfile,time,unittest
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('proof',P/'engine-proof.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
CID='a'*64;IMAGE='sha256:'+'b'*64
LAYOUT=(P/'LAYOUT.json').read_bytes();PAYLOAD=(P/'kernel-payload.py').read_bytes();RUNNER=(P/'engine-proof.py').read_bytes()
SELECTION=dict(schema='baton.verifier-engine-proof-selection/1',image=IMAGE,uid=1234,gid=5678,proof_id='w325695-proof-test',layout_sha256=m.digest(LAYOUT),payload_sha256=m.digest(PAYLOAD),runner_sha256=m.digest(RUNNER))
RESULTS=[]
class Fake:
 def __init__(self,case,receipt):self.case=case;self.receipt=receipt;self.now=0.;self.created=False;self.removed=False;self.calls=[];self.logs=0
 def clock(self):return self.now
 def sleep(self,n):self.now+=n
 def __call__(self,argv,**kw):
  args=argv[1:];op=args[0];self.calls.append((op,kw['timeout']))
  state=json.loads((self.receipt/'state.json').read_text())
  def reply(code=0,out='',err=''):return subprocess.CompletedProcess(argv,code,out,err)
  if op=='create':
   assert state['create_intent'];self.created=True
   assert args[args.index('--user')+1]=='1234:5678'
   if self.case=='create-loss':raise subprocess.TimeoutExpired(argv,kw['timeout'])
   if self.case=='create-unobserved':self.created=False;raise OSError('lost')
   return reply(out=CID+'\n')
  if op=='inspect':
   if not self.created or self.removed:return reply(1,err='Error: No such object: '+args[1])
   if self.case=='unknown-inspect':return reply(1,err='daemon unavailable')
   if self.case=='invalid-inspect':return reply(out='{}')
   if self.case=='invalid-json':return reply(out='not json')
   if state['container_id'] is not None:assert state['container_id']==CID
   obj={'Name':'/'+SELECTION['proof_id'],'Id':CID,'Image':IMAGE,'Config':{'Labels':{'baton.proof':SELECTION['proof_id']},'User':'1234:5678'},'State':{'Running':True}}
   if self.case=='identity-mismatch':obj['Config']['User']='1111:2222'
   return reply(out=json.dumps([obj]))
  if op=='start':
   assert state['container_id']==CID and state['owned']
   if self.case=='start-error':raise OSError('start')
   return reply()
  if op=='logs':
   self.logs+=1
   if self.case=='logs-error':return reply(1,err='logs')
   if self.case=='slow-logs':self.now+=kw['timeout'];return reply()
   if self.case=='hung-logs':self.now+=kw['timeout'];raise subprocess.TimeoutExpired(argv,kw['timeout'])
   if self.case=='bad-receipt':return reply(out='[]')
   if self.case=='missing-capacity':return reply(out=json.dumps(dict(mount_binding='passed',ordinary_grandchild='passed',nested_validator='passed',image_bytes='passed',product_mount_checks='passed')))
   return reply(out=json.dumps(dict(mount_binding='passed',ordinary_grandchild='passed',nested_validator='passed',image_bytes='passed',product_mount_checks='passed',capacity_enospc='passed',descendant_started=10)))
  if op=='rm':
   assert state['container_id']==CID and state['owned']
   if self.case=='rm-timeout':self.now+=kw['timeout'];raise subprocess.TimeoutExpired(argv,kw['timeout'])
   if self.case=='rm-oserror':raise OSError('rm')
   if self.case=='cleanup-inspect-invalid':self.case='invalid-inspect';return reply()
   if self.case=='cleanup-inspect-unknown':self.case='unknown-inspect';return reply()
   self.removed=True;return reply()
  raise AssertionError(args)
class Runner(unittest.TestCase):
 def case(self,name):
  with tempfile.TemporaryDirectory(prefix='w325695-runner-test-') as temp:
   receipt=pathlib.Path(temp)/'receipt';fake=Fake(name,receipt)
   with patch.object(m.os,'getuid',side_effect=AssertionError('ambient uid')),patch.object(m.os,'getgid',side_effect=AssertionError('ambient gid')):
    proof=m.Proof(dict(SELECTION),json.loads(LAYOUT),PAYLOAD.decode(),receipt,run=fake,clock=fake.clock,sleep=fake.sleep);r=proof.execute()
   durable=json.loads((receipt/'state.json').read_text());self.assertEqual(durable,r)
   with self.assertRaises(FileExistsError):m.Proof(dict(SELECTION),json.loads(LAYOUT),'',receipt,run=fake,clock=fake.clock,sleep=fake.sleep)
   RESULTS.append(dict(case=name,success=r['success'],id=r['container_id'],owned=r['owned'],exact_absence=r['exact_absence'],errors=r['errors'],elapsed=fake.now,calls=fake.calls))
   return r,fake
 def test_success_and_no_ambient_identity(self):
  r,f=self.case('success');self.assertTrue(r['success']);self.assertTrue(r['exact_absence'])
 def test_faults_preserve_durable_identity(self):
  for name in ['create-loss','start-error','logs-error','rm-timeout','rm-oserror','invalid-inspect','invalid-json','unknown-inspect','identity-mismatch','cleanup-inspect-invalid','cleanup-inspect-unknown','bad-receipt','missing-capacity']:
   with self.subTest(name=name):
    r,f=self.case(name);self.assertFalse(r['success']);self.assertEqual(r['container_id'],CID)
    if name in ['invalid-inspect','invalid-json','unknown-inspect','identity-mismatch']:self.assertFalse(any(c[0]=='rm' for c in f.calls))
    if name in ['rm-timeout','rm-oserror','cleanup-inspect-invalid','cleanup-inspect-unknown']:self.assertFalse(r['exact_absence']);self.assertIn('cleanup_uncertainty',r)
 def test_create_unobserved_retains_name_not_false_absence(self):
  r,f=self.case('create-unobserved');self.assertIsNone(r['container_id']);self.assertFalse(r['exact_absence']);self.assertIn('creation_uncertainty',r)
 def test_receipt_deadline_and_cleanup_reserve(self):
  for name in ['slow-logs','hung-logs']:
   r,f=self.case(name);self.assertFalse(r['success']);self.assertLessEqual(f.now,20);self.assertTrue(r['exact_absence'])
   self.assertLessEqual(sum(timeout for op,timeout in f.calls if op=='logs'),20)
 def test_selection_refuses_mismatch_before_engine(self):
  m.validate(SELECTION,LAYOUT,PAYLOAD,RUNNER)
  for key,value in [('uid',0),('gid',False),('image','latest'),('layout_sha256','0'*64),('payload_sha256','0'*64),('runner_sha256','0'*64)]:
   s=dict(SELECTION);s[key]=value
   with self.assertRaises(ValueError):m.validate(s,LAYOUT,PAYLOAD,RUNNER)
if __name__=='__main__':
 start=time.monotonic();result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Runner))
 (P/'RUNNER-CHECK.json').write_text(json.dumps(dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),seconds=time.monotonic()-start,engine_invoked=False,cases=RESULTS),indent=2)+'\n')
 raise SystemExit(not result.wasSuccessful())
