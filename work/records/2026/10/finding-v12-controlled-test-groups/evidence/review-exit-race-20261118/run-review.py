import json,os,pathlib,subprocess,tempfile,time,hashlib
repo=pathlib.Path(__file__).resolve().parents[7]
e=pathlib.Path(__file__).resolve().parent
py='/home/sl/.local/state/baton-v12-venv/bin/python'
def identity():
 return json.loads(subprocess.check_output([py,'-m','tools.source_identity','--repo',str(repo),'--declared','v12'],cwd=repo/'v12/python',text=True))
before=identity(); (e/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
reports=[]
for name,prefix,ids in [('focused','rv-', ['tests.tools.test_next_run_flow','tests.manager.test_authoring_enforcement','tests.manager.test_authoring_manager_guard'])]:
 with tempfile.TemporaryDirectory(prefix=prefix,dir='/var/tmp') as root:
  start=time.monotonic()
  with (e/(name+'.log')).open('w') as out:
   result=subprocess.run(['timeout','--kill-after=30s','180s','just','test-one',*ids],cwd=repo/'v12',env=dict(os.environ,TMPDIR=root,BATON_V12_DISK_ROOT=root,BATON_V12_WORKSPACE_GROUP="1001",BATON_V12_INITIAL_ACCESS_ENGINE="1",BATON_V12_PRIVATE_LINE_IMAGE="sha256:0697b6595aff0af2a39a81d492223bf33cf69877426ec859fe1abb90abd617e4"),stdout=out,stderr=subprocess.STDOUT)
  report={'name':name,'root':root,'root_length':len(root),'ids':ids,'exit':result.returncode,'seconds':time.monotonic()-start,'leftovers':list(map(str,pathlib.Path(root).iterdir()))}
 report['root_removed']=not pathlib.Path(root).exists();reports.append(report)
after=identity();(e/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
report={'runs':reports,'source_stable':before['content_digest']==after['content_digest']}
(e/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
