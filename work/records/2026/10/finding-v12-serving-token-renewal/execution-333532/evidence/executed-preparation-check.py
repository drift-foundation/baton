import os,sys,subprocess,time,json,tempfile,pathlib,shutil,hashlib
repo=pathlib.Path('/home/sl/src/baton'); packet=repo/'work/records/2026/10/finding-v12-serving-token-renewal/execution-333532'
evidence=packet/'evidence'; evidence.mkdir()
root=pathlib.Path(tempfile.mkdtemp(prefix='w333485-preflight-'))/'instance-root'
results=[]
def run(label,argv,*,env=None,cwd=None,success=True,contains=None):
 start=time.monotonic(); r=subprocess.run(argv,cwd=cwd or repo,env=env,capture_output=True,text=True,timeout=60); elapsed=time.monotonic()-start
 (evidence/(label+'.log')).write_text(r.stdout+r.stderr)
 results.append(dict(label=label,argv=argv,returncode=r.returncode,seconds=elapsed))
 (evidence/'CHECK.json').write_text(json.dumps(dict(root=str(root),runs=results,total_seconds=sum(x['seconds'] for x in results)),indent=2)+'\n')
 assert (r.returncode==0)==success,(label,r.stdout,r.stderr)
 if contains: assert contains in r.stdout+r.stderr,(label,r.stdout,r.stderr)
 return r
py=sys.executable
run('pins',[py,'-B',str(packet/'verify-inputs.py')])
run('stage',[py,'-B',str(packet/'prepare.py'),'stage','--root',str(root)])
run('reuse-refused',[py,'-B',str(packet/'prepare.py'),'stage','--root',str(root)],success=False,contains='FileExistsError')
f=root/'code/v12/python/src/baton_v12/__init__.py'; saved=f.read_bytes(); f.write_bytes(saved+b'\n# injected drift\n')
run('staged-drift-refused',[py,'-B',str(packet/'prepare.py'),'bind','--root',str(root)],success=False,contains='staged manager drifted')
f.write_bytes(saved)
copy=root.parent/'negative-packet'; copy.mkdir()
for name in ['prepare.py','verify-inputs.py','PREPARATION-PINS.json','SOURCE.json']: shutil.copyfile(packet/name,copy/name)
pins=json.loads((copy/'PREPARATION-PINS.json').read_text()); changed=json.loads(json.dumps(pins)); changed['base']='0'*40;(copy/'PREPARATION-PINS.json').write_text(json.dumps(changed))
run('base-refused',[py,'-B',str(copy/'verify-inputs.py')],success=False,contains='pins name another base')
changed=json.loads(json.dumps(pins)); name=str((packet/'TASK.md').relative_to(repo)); changed['files'][name]='0'*64;(copy/'PREPARATION-PINS.json').write_text(json.dumps(changed))
run('digest-refused',[py,'-B',str(copy/'verify-inputs.py')],success=False,contains='selected preparation input drifted')
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(root/'code/v12/python/src')+':'+str(root/'code/v12/python'))
run('bootstrap',[py,'-B','-m','tools.bootstrap','--inputs',str(root/'bootstrap-inputs.json'),'--destination',str(root/'instance'),'--distro','/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro','--no-repositories'],env=env,cwd=root/'code/v12/python')
run('bind',[py,'-B',str(packet/'prepare.py'),'bind','--root',str(root)])
run('rebind-refused',[py,'-B',str(packet/'prepare.py'),'bind','--root',str(root)],success=False,contains='refuse rebinding')
for name in ['PREPARED.json','stage.json','bootstrap-inputs.json']: shutil.copyfile(root/name,evidence/name)
shutil.copytree(root/'packet',evidence/'generated')
print(json.dumps(dict(root=str(root),total_seconds=sum(x['seconds'] for x in results),checks=len(results))))
