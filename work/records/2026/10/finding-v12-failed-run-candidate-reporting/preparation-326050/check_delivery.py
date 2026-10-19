"""Supported source vector plus exact-file restoration; no engine/model/product correction."""
import hashlib,json,os,pathlib,subprocess,sys,tempfile,time
R=pathlib.Path('/home/sl/src/baton');P=pathlib.Path(__file__).resolve().parent;prov=json.loads((P/'PROVENANCE.json').read_text());started=time.monotonic()
sys.path[:0]=[str(R/'v12/python'),str(R/'v12/python/src')]
os.environ['BATON_V12_DISK_ROOT']=str(P)
from tests.manager import test_source_boundary as fixture
case=fixture.BoundaryCase();case.setUp()
try:
 # Disjoint disk-backed fixture source/manager roots; no production store mutation.
 for name in ['restore.py','retained.patch',*['candidate-input/'+n for n in prov['retained']['paths']]]:
  target=pathlib.Path(case.source)/(P/name).relative_to(R);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((P/name).read_bytes())
 roots,boundary=case.composed()
 mounts=fixture.boundary_mounts(boundary)
 argv=fixture.oci.run_vector('docker',image_digest=fixture.IMAGE,labels=fixture._labels(),assignment_roots=roots,posture='execution',mounts=[dict(source=roots['inputs'],target='/input',writable=False),dict(source=roots['workspace'],target='/output',writable=True)],source_delivered=boundary,name='runtime-326050',workspace_group=case.group)
 expected='type=bind,source='+case.source+',target=/input/source,readonly=true'
 assert expected in argv
 # Translate the selected read-only mapping, not an assumed candidate checkout file.
 locators={n:'/input/source/'+str((P/n).relative_to(R)) for n in ['restore.py','retained.patch',*['candidate-input/'+n for n in prov['retained']['paths']]]}
 readable={}
 for name,target in locators.items():
  host=pathlib.Path(case.source)/pathlib.Path(target).relative_to('/input/source');assert host.read_bytes()==(P/name).read_bytes()
  readable[name]=hashlib.sha256(host.read_bytes()).hexdigest()
 assert readable['retained.patch']==prov['patch_sha256'] and readable['restore.py']==prov['restore_sha256']
finally:case.doCleanups()
with tempfile.TemporaryDirectory(prefix='w321528-input326050-') as temp:
 dest=pathlib.Path(temp)
 for name,h in prov['compatibility'].items():
  if h['base_sha256'] is not None:
   data=subprocess.check_output(['git','show',prov['base']+':'+name],cwd=R);assert hashlib.sha256(data).hexdigest()==h['base_sha256'];q=dest/name;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(data)
 # Execute exactly the measured script bytes using the same loader semantics.
 raw=(P/'restore.py').read_bytes();assert hashlib.sha256(raw).hexdigest()==prov['restore_sha256']
 ns={'__name__':'delivery_preflight','__file__':str(P/'restore.py')};exec(compile(raw,str(P/'restore.py'),'exec'),ns);ns['restore'](dest)
 result={name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in prov['compatibility']}
 assert result==prov['retained']['paths']
 # Fail-closed existing restored tree cannot be overwritten on a second call.
 try:ns['restore'](dest);raise AssertionError('repeat should refuse')
 except ValueError as e:repeat=str(e)
 # Canonical source cannot be selected even if its bytes match.
 try:ns['restore'](R);raise AssertionError('source should refuse')
 except ValueError as e:protected=str(e)
 before=dict(result)
 fixture_input=dest/'one/two/three/four/five/six/seven';fixture_input.mkdir(parents=True);ns['HERE']=fixture_input
 try:ns['restore'](dest);raise AssertionError('missing input should refuse')
 except FileNotFoundError:missing=True
 (fixture_input/'retained.patch').write_bytes(b'corrupt input')
 try:ns['restore'](dest);raise AssertionError('corrupt input should refuse')
 except ValueError as e:corrupt=str(e)
 assert before=={name:hashlib.sha256((dest/name).read_bytes()).hexdigest() for name in before}
report=dict(base=prov['base'],fixture_source_mount=expected,production_source=str(R),container_paths=locators,input_sha256=readable,restored_paths=result,repeat_refusal=repeat,canonical_source_refusal=protected,missing_input_refused=missing,corrupt_input_refusal=corrupt,seconds=time.monotonic()-started,engine_invoked=False,model_invoked=False,scope='Real public nomination/boundary/OCI vector on disjoint disk fixture source containing exact input bytes; production source selected separately in packet. Plain-filesystem restoration. No engine mount inspection or provider execution claimed.')
(P/'DELIVERY-CHECK.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
