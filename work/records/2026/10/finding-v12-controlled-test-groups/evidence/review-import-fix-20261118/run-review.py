import json,os,pathlib,subprocess,tempfile,time,hashlib
repo=pathlib.Path(__file__).resolve().parents[7]
e=pathlib.Path(__file__).resolve().parent
py='/home/sl/.local/state/baton-v12-venv/bin/python'
def identity():
 return json.loads(subprocess.check_output([py,'-m','tools.source_identity','--repo',str(repo),'--declared','v12'],cwd=repo/'v12/python',text=True))
before=identity(); (e/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
reports=[]
for name,prefix,ids in [('focused','rv-', ['tests.tools.test_managed_preparation.ThePublishedInputIsMeasuredTheSameWayAtBothEnds'])]:
 with tempfile.TemporaryDirectory(prefix=prefix,dir='/var/tmp') as root:
  start=time.monotonic()
  with (e/(name+'.log')).open('w') as out:
   result=subprocess.run(['timeout','--kill-after=30s','180s','just','test-one',*ids],cwd=repo/'v12',env=dict(os.environ,TMPDIR=root,BATON_V12_DISK_ROOT=root),stdout=out,stderr=subprocess.STDOUT)
  report={'name':name,'root':root,'root_length':len(root),'ids':ids,'exit':result.returncode,'seconds':time.monotonic()-start,'leftovers':list(map(str,pathlib.Path(root).iterdir()))}
 report['root_removed']=not pathlib.Path(root).exists();reports.append(report)
after=identity();(e/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
report={'runs':reports,'source_stable':before['content_digest']==after['content_digest']}
(e/'result.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
