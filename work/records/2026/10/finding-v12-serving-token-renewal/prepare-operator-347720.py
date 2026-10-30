"""Operator-only reviewed preparation; never launches a Job."""
import os,sys,json,hashlib,subprocess,time
from pathlib import Path
BASE=Path('/home/sl/src/baton/work/records/2026/10/finding-v12-serving-token-renewal')
ROOT=Path('/home/sl/baton-instances/serving-renewal-w333485-339444')
AMEND=BASE/'findings/finding-lease-policy-amendment/amendment-345734'
CHECK=BASE/'findings/finding-renewal-executor-access/preflight-347199.py'
CHECK_SHA='373a8b3378b6406f7a3a539f3eead6580a01a894a5fdb20c43708d32188abd24'
def main():
    if sys.argv[1:]==['--syntax-check']:
        print('syntax loaded; no preparation or launch')
        return
    if sys.argv[1:] not in ([],['--prepare-authorized']):raise SystemExit('Use default read-only check or --prepare-authorized after explicit preparation selection')
    if os.geteuid()!=1000:raise SystemExit('Run as sl, never sudo')
    if hashlib.sha256(CHECK.read_bytes()).hexdigest()!=CHECK_SHA:raise SystemExit('checker drift')
    if hashlib.sha256((AMEND/'AMENDMENT.json').read_bytes()).hexdigest()!='8a46facba604ad3c5e2c1c1b7d76eaf91b84ea1e2aad5e904f296c301a7c7394':raise SystemExit('amendment drift')
    result=subprocess.run([sys.executable,'-B',str(CHECK)],capture_output=True,text=True,timeout=40)
    print(result.stdout,end='')
    if result.returncode:raise SystemExit('Preflight refused; nothing staged')
    if not sys.argv[1:]:return
    out=BASE/'operator-preparation-347720';out.mkdir(mode=0o700)
    (out/'preflight.json').write_text(result.stdout)
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT/'code/v12/python/src')+':'+str(ROOT/'code/v12/python')+':'+str(ROOT/'supervisor'))
    steps=[('stage',[sys.executable,'-B',str(AMEND/'prepare.py'),'stage','--root',str(ROOT)]),('bootstrap',[sys.executable,'-B','-m','tools.bootstrap','--inputs',str(ROOT/'bootstrap-inputs.json'),'--destination',str(ROOT/'instance'),'--distro','/home/sl/baton-runs/managed-correction-236087/build/stack/out/distro','--no-repositories']),('bind',[sys.executable,'-B',str(AMEND/'prepare.py'),'bind','--root',str(ROOT)])]
    for name,argv in steps:
        started=time.monotonic()
        with (out/(name+'.stdout')).open('xb') as stdout,(out/(name+'.stderr')).open('xb') as stderr:
            r=subprocess.run(argv,env=env,stdout=stdout,stderr=stderr)
        (out/(name+'.result.json')).write_text(json.dumps({'exit':r.returncode,'elapsed_seconds':time.monotonic()-started,'argv':argv},indent=2)+'\n')
        if r.returncode:raise SystemExit(name+' failed; preserve root, no retry')
    for name,src in [('PREPARED.json',ROOT/'PREPARED.json'),('commands.json',ROOT/'packet/commands.json'),('PACKET.json',ROOT/'packet/PACKET.json')]:
        (out/name).write_bytes(src.read_bytes())
    (out/'MANIFEST.json').write_text(json.dumps({x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in sorted(out.iterdir()) if x.is_file()},indent=2)+'\n')
    print(str(out)+' prepared only; no launch. Effective host permission remains900 until accepted correction.')
if __name__=='__main__':main()
