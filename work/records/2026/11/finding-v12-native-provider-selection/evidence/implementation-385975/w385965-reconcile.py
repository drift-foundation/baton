import json,re
from pathlib import Path
p=Path('/home/sl/src/baton/work/records/2026/11/finding-v12-native-provider-selection/evidence/implementation-385975')
for q in sorted(p.glob('finite-*.summary.json')):
 s=json.loads(q.read_text());name=q.name.removesuffix('.summary.json');outcomes={};cur=None
 for line in (p/(name+'.stderr.log')).read_text().splitlines():
  m=re.match(r'^(test_\S+) \(([^)]+)\)',line)
  if m:
   cur=m.group(2) if m.group(2).endswith('.'+m.group(1)) else m.group(2)+'.'+m.group(1);outcomes[cur]='started'
  if cur and (line in ('ok','FAIL','ERROR') or re.search(r'\.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$',line)):
   outcomes[cur]=line.rsplit('... ',1)[-1];cur=None
 if outcomes!=s['outcomes']:
  s.update(outcomes=outcomes,passed=sum(v=='ok' for v in outcomes.values()),nonpassing={k:v for k,v in outcomes.items() if v!='ok'},correction='Reconcile standalone unittest status after expected CLI refusal diagnostics. Original summary/log retained; no test rerun or expectation change.')
  (p/(name+'.accounting-corrected.json')).write_text(json.dumps(s,indent=2,sort_keys=True)+'\n')
  print(name,s['passed'],s['nonpassing'])
