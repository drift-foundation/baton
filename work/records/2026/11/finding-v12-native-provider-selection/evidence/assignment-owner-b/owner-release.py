#!/usr/bin/env python3
import hashlib,json,re,subprocess,sys
from pathlib import Path
R=Path('/home/sl/src/baton')
D=R/'work/records/2026/11/finding-v12-native-provider-selection'
P=D/'evidence/assignment-owner-b'
B=['/home/sl/opt/baton/v11/0650c61/bin/baton','--config','/home/sl/baton-v11.14aecfb/baton.json','--participant','baton.slaw']
HASHES={'work/records/2026/11/finding-v12-native-provider-selection/ASSIGNMENT-N1N2-OWNER-B-2026-11-24.md': 'be732f8f991e4e6c0ef4e696527ed389b709d58ce35e21179dec587ae740707e', 'work/records/2026/11/finding-v12-native-provider-selection/ASSIGNMENT-N1N2-2026-11-24.md': 'ae9dfac38ba3bd61d628c23c98637e9a8eb2e68ac50b8592b0717063992d3b22', 'work/records/2026/11/finding-v12-native-provider-selection/ASSIGNMENT-N1N2-WORK-BODY-OWNER-B.txt': 'b675e436741ccd1040ab614a5a71583722b522551911e276e5108d03931ddcd5', 'work/records/2026/11/finding-v12-native-provider-selection/IMPLEMENTATION-CONTRACT-CONSOLIDATED-REV2-2026-11-23.md': 'dc3245c0c5594f15d22c87cd9b9a19352c633c3e4ef9a52f070f24d87960bd87', 'work/records/2026/11/finding-v12-native-provider-selection/IMPLEMENTATION-CONTRACT-N1N2-ADDENDUM-2026-11-23.md': 'c4d2c4b7ebe4c60b6e5eb9543ff4664d2fd86511c6b8a4f538c2b58e27d07117', 'v12/DESIGN.md': 'd2c71e534b3d3f92d7f81b445ed7ba911984e568addfb1b5c59c73e02dbbd914'}
for name,digest in HASHES.items():
 if hashlib.sha256((R/name).read_bytes()).hexdigest()!=digest:raise SystemExit('Input changed: '+name)
if sys.argv[1:]==['--check']:
 print('Assignment and approved specification hashes verified. No Baton mutation.');sys.exit(0)
if sys.argv[1:]:raise SystemExit('Use no arguments or --check')
def call(*args):
 p=subprocess.run(B+list(args),capture_output=True,text=True)
 with (P/'receipts.jsonl').open('a') as f:f.write(json.dumps({'argv':args,'status':p.returncode,'stdout':p.stdout,'stderr':p.stderr})+'\n')
 if p.returncode:raise SystemExit(p.stderr or p.stdout)
 return json.loads(p.stdout)['result']
def detail(w):return call('detail','work='+w)
old=detail('W385695')
if old['status']!='closed' or old['outcome']!='satisfying':raise SystemExit('Recovery prerequisite is not satisfied.')
parent=detail('W385830')
if parent['status']!='open' or parent['handler'] is not None:raise SystemExit('Umbrella state changed.')
created=call('create','team=baton','kind=decide','origin=decomposition','classification=limitation','parent=2b077949-W385830','title=W385830 N1/N2: model attribution, provider hooks, policy, retained home','body='+(D/'ASSIGNMENT-N1N2-WORK-BODY-OWNER-B.txt').read_text(),'op-id=w385830-n1n2-owner-b-20261124')
def ids(v):
 if isinstance(v,dict):return set().union(*(ids(x) for x in v.values())) if v else set()
 if isinstance(v,list):return set().union(*(ids(x) for x in v)) if v else set()
 return {v} if isinstance(v,str) and re.fullmatch(r'(?:[0-9a-f]{8}-)?W[0-9]+',v) else set()
found={x.split('-')[-1] for x in ids(created)}-{'W385830'}
if len(found)!=1:raise SystemExit('Cannot uniquely identify child; see create receipt. No routing performed.')
w=found.pop(); (P/'child-id.txt').write_text(w+'\n')
call('block','work=W385853','on='+w,'rationale=Native instruction delivery follows accepted N2 interface; serialize overlapping worker edits.','op-id=w385830-n1n2-gate-delivery-20261124')
call('block','work=W385263','on=W385830','rationale=Owner-selected A1 hold until native provider preparation completes.','op-id=w385830-n1n2-gate-a1-20261124')
c=call('links','work='+w); p=call('links','work=W385830')
if 'W385853' not in {x.split('-')[-1] for x in ids(c.get('blocks',[]))} or 'W385263' not in {x.split('-')[-1] for x in ids(p.get('blocks',[]))} or w not in {x.split('-')[-1] for x in ids(p.get('contains',[]))}:raise SystemExit('Graph readback mismatch; child not released.')
call('reroute','work='+w,'to=baton.codx','reason=N1/N2 approved; recovery prerequisite closed at 9f979022; owner selected B in ASSIGNMENT-N1N2-OWNER-B-2026-11-24.md. Claim and implement through focused verification; independent K review follows.','op-id=w385830-n1n2-release-20261124')
d=detail(w)
print(w,d['phase'],d['route']['endpoint'],'handler',d['handler'],'blockers',d['open_blockers'])
print('Give codexpc the child id and assignment plus owner-B addendum. No live Job, provider, build or Git mutation.')
