import sys,json,re,hashlib,unittest,platform
from pathlib import Path
root=Path.cwd();sys.path[:0]=[str(root),str(root/'src')];out=Path(__file__).parent
identity=json.loads((out/'identity.json').read_text());tree=Path(identity['reconstruction']);rows=[]
for p in identity['paths']:
 f=tree/p['path'];h=hashlib.sha256(f.read_bytes()).hexdigest();assert h==p['sha256'],p['path'];rows.append({'path':p['path'],'sha256':h,'mode':oct(f.stat().st_mode&0o777)})
(out/'source-after.json').write_text(json.dumps(rows,indent=2)+'\n')
def ids(s):
 for t in s:
  if isinstance(t,unittest.TestSuite):yield from ids(t)
  else:yield t.id()
ledger={};runs={}
for name in ('required','delta','late-exit','qualification','setup','cleanup-cuts','driver-ownership'):
 runs[name]=json.loads((out/(name+'.json')).read_text())
 if name=='registry':continue
 log=(out/(name+'.log')).read_text();matches=list(re.finditer(r'^test_\w+ \(([^)]+)\)',log,re.M));items=[]
 for i,m in enumerate(matches):
  block=log[m.start():matches[i+1].start() if i+1<len(matches) else len(log)]
  block=block.split('\n===',1)[0].split('\n---',1)[0].rstrip()
  status='passed' if re.search(r'\bok$',block) else 'failed' if re.search(r'\bFAIL$',block) else 'error' if re.search(r'\bERROR$',block) else 'unknown'
  items.append({'id':m.group(1),'outcome':status})
 assert len(items)==int(runs[name]['unittest_summary'][0]),name
 assert all(t['outcome']!='unknown' for t in items),name
 if name in ('required','registry-witnesses'):
  expected=sorted(ids(unittest.defaultTestLoader.loadTestsFromNames(runs[name]['argv'][2:])))
  assert sorted(t['id'] for t in items)==expected,name
 else:expected=[t['id'] for t in items]
 ledger[name]={'collected':expected,'results':items,'unaccounted':[]}
(out/'execution-ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
items=[t for x in ledger.values() for t in x['results']]
summary={'source':identity['manifest_sha256'],'interpreter':sys.executable,'python':sys.version,'platform':platform.platform(),'groups':['job_manager','tools-pure (connected setup fixture); standalone qualification probes'],'collected':len(items),'executed':len(items),'passed':sum(t['outcome']=='passed' for t in items),'failed':sum(t['outcome']=='failed' for t in items),'errors':sum(t['outcome']=='error' for t in items),'skips':0,'timeouts':0,'runs':runs,'wall_seconds':sum(r['wall_seconds'] for r in runs.values()),'unittest_seconds':sum(float(r['unittest_summary'][1]) for r in runs.values() if r['unittest_summary']),'diagnostic_member_probes':0}
(out/'accounting.json').write_text(json.dumps(summary,indent=2)+'\n');print({k:v for k,v in summary.items() if k not in ('runs','python','platform')})
