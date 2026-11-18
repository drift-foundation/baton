import json,os,pathlib,subprocess,tempfile,time,hashlib
repo=pathlib.Path(__file__).resolve().parents[7]
e=pathlib.Path(__file__).resolve().parent
py='/home/sl/.local/state/baton-v12-venv/bin/python'
def identity():
 return json.loads(subprocess.check_output([py,'-m','tools.source_identity','--repo',str(repo),'--declared','v12'],cwd=repo/'v12/python',text=True))
before=identity(); (e/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
reports=[]
for name,prefix,ids in [('focused','rv-', ['tests.manager.test_launch.TheContextLaunchIsClosed.test_owner_launch_and_worker_reader_agree', 'tests.manager.test_launch.TheContextLaunchIsClosed.test_closed_version_refuses_omission_extra_and_downgrade', 'tests.manager.test_launch.TheContextLaunchIsClosed.test_wrong_role_uuid_attempt_and_binding_refuse_both_readers', 'tests.manager.test_execution_limits.TheVersionMovesWithTheMember.test_a_document_with_a_transport_alone_is_still_version_two', 'tests.manager.test_execution_limits.TheVersionMovesWithTheMember.test_a_job_context_keeps_a_real_transport', 'tests.tools.test_execution_limits.AFreshProcessAdoptsBothJobsConfiguredLaunches.test_the_child_answers_each_jobs_own_numbers', 'tests.tools.test_execution_limits.TheDerivedJudgmentCarriesItsOwningResultsJob.test_the_retained_intent_is_what_the_launch_states', 'tests.tools.test_execution_limits.TheTwoReadersResolveOneJobIdentically.test_a_foreign_job_is_refused_on_the_read_only_path_too', 'tests.tools.test_execution_limits.TheTwoReadersResolveOneJobIdentically.test_both_compositions_resolve_the_same_bytes'])]:
 with tempfile.TemporaryDirectory(prefix=prefix,dir='/var/tmp') as root:
  start=time.monotonic()
  with (e/(name+'.log')).open('w') as out:
   result=subprocess.run(['timeout','--kill-after=30s','180s','just','test-one',*ids],cwd=repo/'v12',env=dict(os.environ,TMPDIR=root,BATON_V12_DISK_ROOT=root),stdout=out,stderr=subprocess.STDOUT)
  report={'name':name,'root':root,'root_length':len(root),'ids':ids,'exit':result.returncode,'seconds':time.monotonic()-start,'leftovers':list(map(str,pathlib.Path(root).iterdir()))}
 report['root_removed']=not pathlib.Path(root).exists();reports.append(report)
after=identity();(e/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
report={'runs':reports,'source_stable':before['content_digest']==after['content_digest']}
(e/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
