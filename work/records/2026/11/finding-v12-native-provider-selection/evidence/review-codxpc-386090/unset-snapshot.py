import json, sys
from pathlib import Path
repo=Path(sys.argv[1])
sys.path[:0]=[str(repo/'v12/python'),str(repo/'v12/python/src'),str(repo/'v12/worker'),str(repo/'v12/python/src/baton_v12')]
from baton_v12 import provider_policy as p
from baton_v12.provider_policy import attribution
from tests.manager import codex_fixtures as f
from tools import pool
from tests.tools import test_pool
from contextlib import nullcontext
result={}
for provider in ('claude','codex'):
 with (f.simulated(p) if provider=='codex' else nullcontext()):
  s=dict(provider=provider,requested_model='fixture-selector',reported_identity='fixture-reported',cli_build='0.169.0' if provider=='codex' else '2.1.247')
  adapter=p.adapter(s,network='bridge')
  profile={'schema':'baton.single-implementation-runtime-profile/2','provider':provider,'model':s['requested_model'],'reported_identity':s['reported_identity'],'cli_build':s['cli_build']}
  d=p.delivery({'selection':s,'adapter':adapter,'runtime_profile':profile},adapter_digest=p.digest(adapter),profile_digest=p.digest(profile),tool_policy_digest=p.digest(p.POLICY),authority_uuid='fixture-authority',job_id='fixture-job',worker_id='fixture-worker',attempt_id='fixture-attempt')
  record=attribution.record(d,phase='implementation',evidenced_build=None,raw=None)
  result[provider]=dict(selection=p.selection(s),adapter=adapter,adapter_digest=p.digest(adapter),argv=p.argv(adapter,s,'work'),profile=profile,delivery=d,attribution=record,diagnostic=attribution.diagnostic(record))
from codex_agent import CodexAgent
result['detached_codex_argv']=CodexAgent.__new__(CodexAgent).provider_argv('work',model='fixture-selector')
print(json.dumps(result,sort_keys=True,indent=2))
