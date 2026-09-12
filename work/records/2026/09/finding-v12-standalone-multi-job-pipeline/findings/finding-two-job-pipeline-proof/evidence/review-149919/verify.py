from pathlib import Path
import hashlib,json,stat,time
repo=Path('/home/sl/src/baton')
p=repo/"work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-two-job-pipeline-proof"
e=p/'evidence/review-149919'
start=time.monotonic()
def sha(f):return 'sha256:'+hashlib.sha256(f.read_bytes()).hexdigest()
manifest=p/'evidence/observation-correction-149854/candidate-manifest.json'
assert sha(manifest)=='sha256:f39eedf82d8b87c238bddca481c0aceb8c32f8966d4f71d588ae54eb1d57ca21'
files=json.loads(manifest.read_text())['files'];assert len(files)==79
for n,v in files.items():
 rel=Path(n);assert not rel.is_absolute() and '..' not in rel.parts
 assert n.startswith(str(p.relative_to(repo))+'/') or n in ('v12/python/tools/stage_execution.py','v12/python/tests/tools/test_stage_execution.py')
 assert rel.suffix not in ('.sqlite3','.db','.sqlite') and 'credentials' not in rel.parts
 f=repo/rel;s=f.lstat()
 assert stat.S_ISREG(s.st_mode) and s.st_size==v['bytes'] and oct(stat.S_IMODE(s.st_mode))==v['mode'] and sha(f)==v['sha256'],n
held=json.loads(Path('/tmp/w71879-149854-provenance-_11g53gz/provenance.json').read_text())
(e/'provenance.json').write_text(json.dumps(held,indent=2)+'\n')
for n in ('selected-images.json','execution-review.json','frozen-config','validation.json'):
 assert not (p/'prepared-149854'/n).exists() and not (p/'prepared-149854'/n).is_symlink(),n
r=json.loads((p/'evidence/observation-correction-149854/run8-run-result.json').read_text())
assert r['terminal_both'] is False and r['wall_seconds']==243.6142136999988 and r['ordinary_operator_transitions']==0
report={'claim':149919,'manifest':sha(manifest),'files':len(files),'source_and_test':held['source_and_test'],'helpers':held['four_helpers'],'unchanged_old_test_methods':held['unchanged_product_test_methods'],'retained_run8_wall':r['wall_seconds'],'terminal_both':False,'custody_seconds':time.monotonic()-start}
(e/'custody.json').write_text(json.dumps(report,indent=2)+'\n')
cost=2.078+0.34674481200636365+0.12612535001244396+report['custody_seconds']
spending={'product_seconds_rounded':2.078,'offline_seconds':0.34674481200636365,'provenance_seconds':0.12612535001244396,'custody_seconds':report['custody_seconds'],'current_listed_seconds':cost,'cumulative_listed_preparation_seconds':46.56144843188778+cost,'eight_failed_runtime_walls_seconds':1593.8314001880208,'uncertainty':'Product test time rounded; untimed review, commands, reads and host/billing costs remain additional; no double counting or reserve transfer.'}
(e/'spending.json').write_text(json.dumps(spending,indent=2)+'\n')
print(json.dumps({'custody':report,'spending':spending},indent=2))
