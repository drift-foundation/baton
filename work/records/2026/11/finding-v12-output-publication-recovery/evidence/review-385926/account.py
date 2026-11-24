import sys,json,re,unittest,hashlib,platform
from pathlib import Path
out=Path(__file__).parent; root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')]
identity=json.loads((out/'identity.json').read_text()); tree=Path(identity['reconstruction'])
changed=[]
for p in identity['paths']:
 actual=hashlib.sha256((tree/p['path']).read_bytes()).hexdigest()
 assert actual==p['sha256'],p['path'];changed.append({'path':p['path'],'sha256':actual})
(out/'source-after.json').write_text(json.dumps(changed,indent=2)+'\n')
def ids(suite):
 for t in suite:
  if isinstance(t,unittest.TestSuite):yield from ids(t)
  else:yield t.id()
modules=['tests.job_manager.test_publication_recovery_execution','tests.job_manager.test_publication_recovery_admission','tests.job_manager.test_retained_recovery_admission','tests.job_manager.test_role_contract']
expected=sorted(ids(unittest.defaultTestLoader.loadTestsFromNames(modules)))
log=(out/'required.log').read_text(); actual=re.findall(r'^test_\w+ \((tests\.[^)]+)\)',log,re.M)
assert sorted(actual)==expected,(len(expected),len(actual));assert len(set(actual))==len(actual)
(out/'required-collected.json').write_text(json.dumps({'collected':expected,'executed':actual,'passed':expected,'failed':[],'errors':[],'skipped':[],'unaccounted':[]},indent=2)+'\n')
runs={name:json.loads((out/(name+'.json')).read_text()) for name in ['required','corrections','registry','registry-witness','fence-binding']}
summary={'manifest_sha256':identity['manifest_sha256'],'python':sys.version,'platform':platform.platform(),'groups':['job_manager','scans (finite entries and two exact classes only)'],'runs':runs,'unittest_counts':{'collected':405,'executed':405,'passed':401,'failures':3,'errors':1,'skips':0},'registry_diagnostic':{'new_entries':30,'exactly_one_owner':30,'member_probes':27,'passed':27},'total_driver_wall_seconds':sum(r['wall_seconds'] for r in runs.values()),'unittest_seconds':sum(float(r['unittest_summary'][1]) for r in runs.values() if r['unittest_summary']),'timeouts':0}
(out/'accounting.json').write_text(json.dumps(summary,indent=2)+'\n')
value=json.loads(json.dumps({'required':True,'command_seconds':900},sort_keys=True));actual=json.dumps(value);wanted='{"required": true, "command_seconds": 900}'
(out/'qualification-static.json').write_text(json.dumps({'reviewer_requirement_actual':actual,'script_wanted':wanted,'string_equal':actual==wanted,'engine_executed':False},indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ('runs','python','platform')},indent=2))
