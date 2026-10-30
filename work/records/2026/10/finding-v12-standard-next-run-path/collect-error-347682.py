"""Read one already-collected report field; operator runs as sl, not sudo."""
import os,sys,subprocess
from pathlib import Path
BODY = 'import os,stat,json,hashlib,re\nfrom pathlib import Path\nassert os.geteuid()==0\np=Path(\'/var/lib/baton-next-run/w339626-live-345599/packet/outcome.json\')\nfor x in (p.parent.parent,p.parent,p):\n assert not stat.S_ISLNK(x.lstat().st_mode)\nfd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)\nwith os.fdopen(fd,\'rb\') as f:\n s=os.fstat(f.fileno());assert stat.S_ISREG(s.st_mode) and s.st_size==6221\n raw=f.read(6222)\nassert hashlib.sha256(raw).hexdigest()==\'4d093c99c582c48af392077ca3b1ab5218170a7ba04da0f3e26ae12b7e215484\',\'Report drift; do not collect a different execution\'\nd=json.loads(raw)\nassert d[\'run_id\']==\'w339626-live-345599\' and d[\'stopped\']==\'serving-failed\'\nv=d[\'serving_failure\']\nassert isinstance(v,str) and len(v)==125 and v.startswith(\'ProfileRefusal:\')\n# Only this bounded diagnostic field. Remove arbitrary quoted operands, paths,\n# URLs, key/value credentials and long opaque strings before export.\nv=re.sub(r\'https?://\\S+\',\'<url>\',v)\nv=re.sub(r"([\'\\"`])[^\'\\"`\\n]*\\1",\'<operand>\',v)\nv=re.sub(r\'(?i)\\b(?:token|password|secret|authorization|api[_-]?key)\\s*[:=]\\s*\\S+\',\'<redacted>\',v)\nv=re.sub(r\'(?<!\\w)/[^\\s,;)]*\',\'<path>\',v)\nv=re.sub(r\'\\b[A-Za-z0-9_+=-]{32,}\\b\',\'<opaque>\',v)\nv=\'\'.join(c if c.isprintable() or c==\'\\n\' else \'?\' for c in v)\nprint(json.dumps({\'schema\':\'w339626-serving-failure/1\',\'run\':d[\'run_id\'],\'source_sha256\':hashlib.sha256(raw).hexdigest(),\'field\':\'serving_failure\',\'original_characters\':125,\'sanitized_diagnostic\':v},indent=2))\n'
def main():
    if sys.argv[1:]==['--check']:
        compile(BODY,'<fixed-field-collector>','exec')
        print('syntax valid; no privileged read performed')
        return
    if sys.argv[1:]:raise SystemExit('Only --check is supported')
    if os.geteuid()!=1000:raise SystemExit('Run as sl/uid1000, never sudo the outer helper')
    out=Path(__file__).resolve().parent/'operator-error-347682'
    out.mkdir(mode=0o700)
    with (out/'diagnostic.json').open('xb') as stdout,(out/'stderr.txt').open('xb') as stderr:
        result=subprocess.run(['sudo','/usr/bin/python3','-I','-B','-c',BODY],stdout=stdout,stderr=stderr)
    (out/'exit.status').write_text(str(result.returncode)+'\n')
    print(str(out)+' exit '+str(result.returncode))
    raise SystemExit(result.returncode)
if __name__=='__main__':main()
