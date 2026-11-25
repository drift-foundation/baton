#!/usr/bin/env python3
"""Owner-selected build/offline checks only; default --check never calls Docker."""
import argparse, hashlib, io, json, os, pathlib, subprocess, sys, tarfile, time
P = pathlib.Path
REPO = P('/home/sl/src/baton')
COMMIT = 'ad6dcad0aa38f8ccc17fd6a50bd92bf6f2d8c402'
PYTHON = '/home/sl/.local/state/baton-v12-venv/bin/python'
PACKET = REPO/'work/records/2026/11/finding-v12-native-provider-selection/evidence/product-image-preparation-r2'
ROOT = P('/home/sl/baton-qualification/w385830-codex-product-ad6dcad0-2')
TAG = 'baton-v12-codex:ad6dcad0-offline-2'
NAME = 'w385830-codex-product-ad6dcad0-offline-2'
BASE = 'node@sha256:f0960f8dc047f358e3fb428f36ccba21732194fa5f0cac849f401e63e62fb9e6'
RECIPE_BASE = 'node:22-trixie-slim'

def git(*args):
    return subprocess.check_output(['git','-C',str(REPO),*args],env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'})
def sha(raw): return hashlib.sha256(raw).hexdigest()
def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')
def preflight():
    expected=json.loads((PACKET/'source-identity.json').read_text())
    assert git('rev-parse',COMMIT).decode().strip()==COMMIT
    assert sha(git('archive',COMMIT,'v12'))==expected['archive_sha256'], 'committed source archive differs'
    assert P(PYTHON).is_file(), 'prepared interpreter absent'
    assert not ROOT.exists(), 'run root already exists; no automatic retry or deletion'
    assert not any(os.environ.get(k) for k in ('GIT_DIR','GIT_WORK_TREE','GIT_COMMON_DIR','DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS_VERIFY')), 'repository/engine override present'
    for parent in (ROOT.parent,*ROOT.parent.parents):
        assert not parent.is_symlink(), 'symlink in run root ancestry'
        assert not (parent/'.git').exists(), 'run root inside a repository'
    print('Committed source verified; no build or engine query in preflight.',flush=True)
    return expected

PROBE = r'''
import hashlib,json,os,pathlib,shutil,subprocess
p=pathlib.Path('/run/baton/provider-home'); p.mkdir(exist_ok=True)
os.environ.update(HOME=str(p),CODEX_HOME=str(p/'codex'))
checks={}
for name in ('git','sha256sum','python3','codex'):
    checks[name]=shutil.which(name)
    assert checks[name], 'required tool absent: '+name
checks['strace']=shutil.which('strace')
r=subprocess.run(['codex','--version'],capture_output=True,text=True,timeout=10)
assert r.returncode==0 and r.stdout.strip()=='codex-cli 0.169.0', (r.returncode,r.stdout,r.stderr)
checks['version']=r.stdout.strip()
r=subprocess.run(['git','--version'],capture_output=True,text=True,timeout=10)
assert r.returncode==0; checks['git_version']=r.stdout.strip()
checks['files']={str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in pathlib.Path('/opt/baton').rglob('*') if f.is_file()}
checks['uid']=os.getuid(); checks['gid']=os.getgid()
print(json.dumps(checks,sort_keys=True))
'''

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true')
    ap.add_argument('--run',action='store_true',help='select public pull/build and one offline container, no authentication/model')
    a=ap.parse_args()
    if a.check and a.run: ap.error('choose one mode')
    expected=preflight()
    if not a.run:
        print('Ready. --run selects public pull/build plus one offline tool/version/source check.'); return
    ROOT.mkdir(parents=True,mode=0o700)
    env={k:v for k,v in os.environ.items() if k in ('PATH','LANG','LC_ALL','HOME')}
    (ROOT/'docker-config').mkdir(mode=0o700)
    env['DOCKER_CONFIG']=str(ROOT/'docker-config')
    env['TMPDIR']=str(ROOT/'tmp'); (ROOT/'tmp').mkdir()
    seq=0
    def run(label,argv,bound=30,ok=(0,),extra=None):
        nonlocal seq
        seq+=1; stem=ROOT/f'{seq:02d}-{label}'
        print(f'{label}: running; log {stem}.stdout',flush=True)
        start=time.monotonic(); rec={'argv':argv,'bound_seconds':bound}
        try:
            with P(str(stem)+'.stdout').open('xb') as out, P(str(stem)+'.stderr').open('xb') as err:
                r=subprocess.run(argv,env={**env,**(extra or {})},stdout=out,stderr=err,timeout=bound)
            rec['status']=r.returncode
        except BaseException as e:
            rec['error']=repr(e); raise
        finally:
            rec['seconds']=time.monotonic()-start; write(P(str(stem)+'.json'),rec)
        assert r.returncode in ok, f'{label} failed; inspect logs, no automatic retry'
        return P(str(stem)+'.stdout').read_bytes()
    raw=git('archive',COMMIT,'v12'); (ROOT/'source.tar').write_bytes(raw)
    source=ROOT/'source'; source.mkdir()
    with tarfile.open(fileobj=io.BytesIO(raw)) as archive: archive.extractall(source,filter='data')
    assert run('tag-preflight',['docker','image','ls','--quiet','--filter','reference='+TAG]).strip()==b'', 'output tag exists; no overwrite or automatic retry'
    # Explicit one-line build-context correction; protected source is unchanged.
    ignore=source/'v12/.dockerignore'
    original_ignore=ignore.read_bytes()
    assert sha(original_ignore)==expected['dockerignore_sha256'], 'unexpected ignore file'
    anchor=b'!python/src/baton_v12/source_profiles\n'
    assert original_ignore.count(anchor)==1
    corrected_ignore=original_ignore.replace(anchor,anchor+b'!python/src/baton_v12/provider_policy\n',1)
    ignore.write_bytes(corrected_ignore)
    write(ROOT/'context-correction.json',{'path':'v12/.dockerignore','before':sha(original_ignore),'after':sha(corrected_ignore),'change':'include provider_policy only; cache exclusions unchanged','product_imported':False})
    # Reuse prior successful pull by its exact retained digest; no second pull.
    base=json.loads(run('base-inspect',['docker','image','inspect',BASE]))[0]
    pins=base.get('RepoDigests',[]); assert pins, 'base has no repository digest'
    pin=pins[0]; assert '@sha256:' in pin
    original=(source/'v12/worker/Dockerfile.codex').read_text()
    assert original.count('FROM '+RECIPE_BASE+'\n')==1
    recipe=source/'v12/worker/Dockerfile.codex.qualified'
    recipe.write_text(original.replace('FROM '+RECIPE_BASE+'\n','FROM '+pin+'\n',1))
    write(ROOT/'build-inputs.json',{'commit':COMMIT,'source':expected,'base':pin,'original_recipe_sha256':sha(original.encode()),'derived_recipe_sha256':sha(recipe.read_bytes()),'change':'FROM pinned to observed pulled digest only','mutable_inputs':'apt/npm dependencies remain unlocked; not reproducible-build qualification'})
    # Existing supported normalization path, with disk-backed TMPDIR.
    run('build',['/home/sl/.local/state/baton-v12-venv/bin/python','-m','tools.worker_image','--context',str(source/'v12'),'--dockerfile',str(recipe),'--tag',TAG,'--platform','linux/amd64'],2400,extra={'PYTHONPATH':str(source/'v12/python')})
    built=json.loads(run('image-inspect',['docker','image','inspect',TAG]))[0]
    identity=built['Id']; assert identity.startswith('sha256:')
    assert built['Config']['Entrypoint']==['python3','/opt/baton/codex_entry.py']
    assert built['Config']['User']=='65532:65532'
    write(ROOT/'image.json',{'id':identity,'tag':TAG,'commit':COMMIT})
    assert run('probe-name-preflight',['docker','ps','-aq','--filter','name=^/'+NAME+'$']).strip()==b'', 'probe name already owned; refusing before any container mutation'
    created=False; gone=False
    try:
        run('probe-create',['docker','create','--name',NAME,'--label','baton.qualification=w385830-product-ad6dcad0-2','--network','none','--read-only','--cap-drop=ALL','--security-opt=no-new-privileges','--user','65532:65532','--pids-limit','128','--memory','512m','--cpus','1','--tmpfs','/tmp:rw,nosuid,nodev,size=128m','--tmpfs','/run/baton/provider-home:rw,nosuid,nodev,uid=65532,gid=65532,mode=0700,size=64m','--entrypoint','python3',identity,'-c',PROBE])
        created=True
        run('probe-start',['docker','start',NAME])
        waited=run('probe-wait',['docker','wait',NAME],60).decode().strip()
        assert waited=='0', 'offline probe failed; logs retained in cleanup'
        info=json.loads(run('probe-inspect',['docker','inspect',NAME]))[0]
        assert not info['State']['Running'] and not info['State']['OOMKilled']
        output=run('probe-logs',['docker','logs',NAME])
        checks=json.loads(output)
        assert checks['uid']==65532 and checks['gid']==65532
        mapping={}
        for f in (source/'v12/worker').glob('*.py'):
            if '/opt/baton/'+f.name in checks['files']: mapping['/opt/baton/'+f.name]=sha(f.read_bytes())
        for name in ('attempt_log_format.py','verification_context.py'):
            mapping['/opt/baton/'+name]=sha((source/'v12/python/src/baton_v12'/name).read_bytes())
        for dirname in ('provider_policy','source_profiles'):
            folder=source/'v12/python/src/baton_v12'/dirname
            for f in folder.rglob('*'):
                if f.is_file(): mapping['/opt/baton/'+dirname+'/'+str(f.relative_to(folder))]=sha(f.read_bytes())
        for name in ('worker-control-1.0.schema.json','verifier-layout-marker.json'):
            mapping['/opt/baton/'+name]=sha((source/'v12/worker'/name).read_bytes())
        assert all(checks['files'].get(k)==v for k,v in mapping.items()), 'image/source mismatch'
        assert '/opt/baton/codex_agent.py' in mapping and '/opt/baton/provider_policy/worker_instructions.md' in mapping
        write(ROOT/'offline-checks.json',checks)
    finally:
        # Inspect by the exact owned name even if create/start failed or timed out.
        try:
            raw=run('cleanup-inspect',['docker','inspect',NAME],30,ok=(0,1))
            if raw.strip() and json.loads(raw):
                state=json.loads(raw)[0]['State']
                if state['Running']:
                    run('cleanup-stop',['docker','stop','--time','15',NAME],30)
                state=json.loads(run('cleanup-settled',['docker','inspect',NAME]))[0]['State']
                assert not state['Running'], 'runtime cessation unresolved'
                run('cleanup-logs',['docker','logs',NAME],30)
                run('cleanup-remove',['docker','rm',NAME])
                assert run('cleanup-absence',['docker','ps','-aq','--filter','name=^/'+NAME+'$']).strip()==b''
                gone=True
            elif not created:
                raise RuntimeError('create outcome uncertain; inspect command stderr before cleanup claim')
        except BaseException:
            print('UNRESOLVED cleanup: inspect exact container '+NAME+'; do not retry.',file=sys.stderr)
            raise
    assert gone
    result={'image':identity,'commit':COMMIT,'offline':'passed','container_removed':gone,'native_qualification':False,'authentication':'not attempted','N4b':'still gated','strace_available':bool(checks['strace'])}
    write(ROOT/'RESULT.json',result)
    durable=PACKET/'results'; durable.mkdir(exist_ok=False)
    import shutil
    for f in ROOT.iterdir():
        if f.is_file() and f.suffix in ('.json','.stdout','.stderr'): shutil.copyfile(f,durable/f.name)
    print(json.dumps(result,indent=2)); print('Evidence:',ROOT,'; durable logs:',durable)

if __name__=='__main__':
    try: main()
    except BaseException:
        print('Stopped. No automatic retries. A build/control timeout does not prove daemon work ended. Preserve the run root.',file=sys.stderr)
        raise
