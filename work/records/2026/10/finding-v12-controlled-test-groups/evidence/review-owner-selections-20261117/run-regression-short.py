import hashlib,json,os,pathlib,subprocess,tempfile,time
repo=pathlib.Path(__file__).resolve().parents[7]
evidence=pathlib.Path(__file__).resolve().parent
manifest=json.loads((evidence/'source-manifest.json').read_text())
snapshot=repo/manifest['snapshot']
def drift():
 return [x['path'] for x in manifest['files'] if hashlib.sha256((snapshot/x['path']).read_bytes()).hexdigest()!=x['sha256']]
assert not drift()
with tempfile.TemporaryDirectory(prefix='rv-',dir='/var/tmp') as root:
 env=dict(os.environ,TMPDIR=root,BATON_V12_DISK_ROOT=root)
 command=['just','test-one','tests.manager.test_stopped_settlement','tests.manager.test_intake','tests.manager.test_workspaces']
 start=time.monotonic()
 with (evidence/'regression-short.log').open('w') as out:
  result=subprocess.run(['timeout','--kill-after=30s','180s',*command],cwd=snapshot/'v12',env=env,stdout=out,stderr=subprocess.STDOUT)
 report={'command':command,'root':root,'exit':result.returncode,'seconds':time.monotonic()-start,'source_drift':drift(),'leftovers':list(map(str,pathlib.Path(root).iterdir()))}
report['root_removed']=not pathlib.Path(root).exists()
(evidence/'regression-short.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
