"""One retained turn, positive field selection; never opens credential files."""
import hashlib
import json
from pathlib import Path
REPO=Path('/home/sl/src/baton')
RECORD=REPO/'work/records/2026/11/finding-v12-native-provider-selection'
PRIVATE=Path('/var/tmp/baton-codex-q1-live-386097')
DEST=REPO/'work/scratch/n4b-386105/v12/python/tests/manager/fixtures/codex-0.169.0'
raw=(PRIVATE/'live/private-output/turn.stdout').read_bytes()
assert len(raw)<65536
out=[]; ids={}
for line in raw.splitlines():
 v=json.loads(line); t=v['type']
 if t=='thread.started':
  assert set(v)=={'type','thread_id'}
  x=dict(type=t,thread_id='sanitized-thread')
 elif t=='turn.started':
  assert set(v)=={'type'};x=v
 elif t=='turn.completed':
  assert set(v)=={'type','usage'}
  assert set(v['usage'])=={'input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens'}
  assert all(type(n)is int and n>=0 for n in v['usage'].values());x=v
 elif t in ('item.started','item.completed'):
  assert set(v)=={'type','item'};i=v['item']; ident=ids.setdefault(i['id'],'sanitized-item-'+str(len(ids)))
  if i['type']=='agent_message':
   assert set(i)=={'id','type','text'}
   item=dict(id=ident,type=i['type'],text='[private agent text removed]')
  else:
   assert i['type']=='command_execution' and set(i)=={'id','type','command','aggregated_output','exit_code','status'}
   assert i['status'] in ('in_progress','completed') and (i['exit_code'] is None or type(i['exit_code'])is int)
   item=dict(id=ident,type=i['type'],command='[private command removed]',aggregated_output='[private output removed]',exit_code=i['exit_code'],status=i['status'])
  x=dict(type=t,item=item)
 else:raise ValueError('unexpected event; classify privately')
 out.append(x)
safe=('\n'.join(json.dumps(v,separators=(',',':')) for v in out)+'\n').encode()
(DEST/'turn-success.sanitized.jsonl').write_bytes(safe)
result=json.loads((RECORD/'evidence/live-probe-prompt/RESULT.json').read_text())
ref=result['model_evidence'][0]
session=PRIVATE/ref['source']
assert session.is_relative_to(PRIVATE/'live/home/codex/sessions') and not session.is_symlink()
with session.open() as f:
 for number,line in enumerate(f,1):
  if number==ref['line']:
   event=json.loads(line);break
assert event['type']=='turn_context' and event['payload']['model']=='gpt-6-astra'
projection=dict(type='turn_context',payload=dict(model=event['payload']['model']))
context=(json.dumps(projection,separators=(',',':'))+'\n').encode()
(DEST/'turn-context.projection.json').write_bytes(context)
meta=dict(cli_build='0.169.0',image=result['image'],source_checkpoint=result['source_checkpoint'],exit_status=result['turn_exit'],source_report='work/records/2026/11/finding-v12-native-provider-selection/evidence/live-probe-prompt/REPORT.md',source_raw_private=True,raw_sha256=hashlib.sha256(raw).hexdigest(),sanitization='All thread/item identifiers replaced consistently; agent text, command and aggregated output replaced by fixed markers. Observed event order, field sets, status, exit and usage numbers preserved. Session fixture is ONLY a type/model projection from the reported turn_context line, not a full session or participation evidence.',files={ 'turn-success.sanitized.jsonl':hashlib.sha256(safe).hexdigest(),'turn-context.projection.json':hashlib.sha256(context).hexdigest()},participation_evidence=False,backend_identity_attested=False)
(DEST/'turn-provenance.json').write_text(json.dumps(meta,indent=2)+'\n')
print(json.dumps(dict(events=len(out),sanitized_sha256=hashlib.sha256(safe).hexdigest(),credentials_opened=False)))
