import json,os,pathlib,subprocess,tempfile,time,hashlib
repo=pathlib.Path(__file__).resolve().parents[7]
e=pathlib.Path(__file__).resolve().parent
py='/home/sl/.local/state/baton-v12-venv/bin/python'
def identity():
 return json.loads(subprocess.check_output([py,'-m','tools.source_identity','--repo',str(repo),'--declared','v12'],cwd=repo/'v12/python',text=True))
before=identity(); (e/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
reports=[]
for name,prefix,ids in [('focused','rv-', ['tests.manager.test_stopped_settlement.RevokedGenerationReplay.test_a_bound_generations_activation_still_refuses_after_revocation', 'tests.manager.test_stopped_settlement.RevokedGenerationReplay.test_a_committed_renewal_is_not_replayed_after_revocation_and_nothing_extends', 'tests.manager.test_stopped_settlement.RevokedGenerationReplay.test_a_new_act_changed_operands_or_a_foreign_owner_still_refuse_after_revocation', 'tests.manager.test_stopped_settlement.RevokedGenerationReplay.test_an_exact_launch_replay_after_revocation_answers_the_committed_record_and_changes_nothing', 'tests.manager.test_stopped_settlement.RevokedGenerationReplay.test_expiry_of_the_revoked_generation_grants_nothing_and_a_competitor_still_waits', 'tests.manager.test_stopped_settlement.RevokedGenerationReplay.test_the_settlement_fence_still_refuses_an_exact_replay', 'tests.job_manager.test_native_stop_restart.NativeStopRestart.test_reopened_store_preserves_deadline_and_generation_without_revival', 'tests.job_manager.test_serving_renewal.ServingPermission.test_expiry_is_not_revival_or_reuse_and_unknown_cessation_holds'])]:
 with tempfile.TemporaryDirectory(prefix=prefix,dir='/var/tmp') as root:
  start=time.monotonic()
  with (e/(name+'.log')).open('w') as out:
   result=subprocess.run(['timeout','--kill-after=30s','180s','just','test-one',*ids],cwd=repo/'v12',env=dict(os.environ,TMPDIR=root,BATON_V12_DISK_ROOT=root),stdout=out,stderr=subprocess.STDOUT)
  report={'name':name,'root':root,'root_length':len(root),'ids':ids,'exit':result.returncode,'seconds':time.monotonic()-start,'leftovers':list(map(str,pathlib.Path(root).iterdir()))}
 report['root_removed']=not pathlib.Path(root).exists();reports.append(report)
after=identity();(e/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
report={'runs':reports,'source_stable':before['content_digest']==after['content_digest']}
(e/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
