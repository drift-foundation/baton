"""Static editorial and instruction-file inventory checks; no provider execution."""
import hashlib,json,re,sys,time
from pathlib import Path
started=time.monotonic()
evidence=Path(__file__).resolve().parent
candidate=Path(sys.argv[1]).resolve()
repository=Path(sys.argv[2]).resolve()
root=(candidate/'AGENTS.md').read_text()
worker=(candidate/'docs/V12-WORKER-INSTRUCTIONS.md').read_text()
checks=[]
def check(name,condition):
 checks.append({'name':name,'passed':bool(condition)})
check('host root fits required 32768-byte loader budget',len(root.encode())<32768)
check('no concrete work/job/message identity or dated ruling in instruction documents',all(not re.search(r'\b[WMET]\d{3,}\b|20\d\d-\d\d-\d\d|work/records/20',p.read_text()) for p in candidate.rglob('*.md')))
check('no source-directory context selector',not (candidate/'v12/AGENTS.md').exists() and not list(candidate.rglob('AGENTS.override.md')))
check('R1 exception scope lifetime revalidation and relocation present',all(x in root for x in ['scope and lifetime','Revalidate it before acting','sibling\nor successor Work','neither revokes it nor revives an expired one']))
check('R2 ordinary builds not subject to image-build selection', 'engines, image builds, deployment changes' in worker and 'engines, builds, deployment changes' not in worker)
links=[]
for p in candidate.rglob('*.md'):
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if '://' in link:continue
  path=(p.parent/link.split('#')[0]).resolve()
  rel=path.relative_to(candidate)
  links.append((str(p.relative_to(candidate)),link,path.exists() or (repository/rel).exists()))
check('all local Markdown links resolve in candidate plus base',all(x[2] for x in links))
check('protected-main and disposable Git scopes both explicit','Slawomir alone owns' in root and 'Git mutations are permitted' in root and 'shared Git metadata' in root)
check('native context explicit and protected main retained','only when delivered' in worker and 'protected main development repository remains protected' in worker and 'Do not\ninvoke host v11 claims' in worker)
check('managed detailed procedure mandatory before writes','read and follow the complete' in root and 'before any write' in root and (candidate/'docs/HOST-INTEGRATION.md').is_file())
check('baseline preserved unchanged from main source',(evidence/'base/AGENTS.md').read_bytes()==(repository/'AGENTS.md').read_bytes())
rows=json.loads((evidence/'rule-matrix.json').read_text())
old=(evidence/'base/AGENTS.md').read_text().splitlines()
covered=set()
for r in rows:
 covered.update(range(r['start'],r['end']+1))
check('every nonblank baseline line represented in rule matrix',all(i in covered for i,line in enumerate(old,1) if line.strip()))
check('matrix quoted source agrees with retained baseline',all(r['source']=='\n'.join(old[r['start']-1:r['end']]).strip() for r in rows))
# Inventory only known host paths; explicitly not a proprietary loader reimplementation.
chain=[]
for directory in ['', 'v12','v12/python','v12/worker','docs','tools']:
 for name in ['AGENTS.override.md','AGENTS.md']:
  p=repository/directory/name
  if p.is_file():chain.append({'path':str(p.relative_to(repository)),'bytes':p.stat().st_size,'candidate_bytes':len(root.encode()) if not directory and name=='AGENTS.md' else p.stat().st_size})
check('known host source paths have only root automatic instruction file',len(chain)==1 and chain[0]['path']=='AGENTS.md')
check('known project chain within default 32768-byte budget',sum(r['candidate_bytes'] for r in chain)<32768)
result={'kind':'static-policy-audit-not-product-or-vendor-loader-tests','checks':checks,'collected':len(checks),'passed':sum(x['passed'] for x in checks),'failed':sum(not x['passed'] for x in checks),'skipped':0,'duration_seconds':time.monotonic()-started,'candidate_bytes':{str(p.relative_to(candidate)):p.stat().st_size for p in candidate.rglob('*.md')},'known_source_chain':chain,'links':links,'limitations':['No real provider invocation or exact-image discovery check','No claim about unseen harness or managed/user auto-memory content','Semantic rule preservation requires independent review; line coverage is only structural']}
print(json.dumps(result,indent=2))
sys.exit(bool(result['failed']))
