"""Read-only Git object export; never consumes dirty product files."""
from pathlib import Path
import hashlib,json,os,subprocess,tempfile
COMMIT="f36bcd75ed22430355efe1b274b8f236cb591f6b"
REPO=next(p for p in Path(__file__).resolve().parents if (p/".git").exists())
PREFIX="work/records/2026/10/finding-v12-useful-template-job-monitor"
PATHS=["v12",PREFIX,"work/records/2026/10/finding-v12-native-pilot-instance-packet","work/records/2026/08/finding-v12-isolated-agent-workers/findings/finding-v12-worker-contract/findings/finding-worker-control-api-manifests/evidence/vectors.json","work/records/2026/10/finding-v12-template-job-creation/findings/finding-packaged-template-creation/evidence/review-366382"]
def git(*args):
    return subprocess.check_output(["git","-C",str(REPO),*args],timeout=60)
def entries():
    rows=[]
    for entry in git("ls-tree","-r","-z",COMMIT,"--",*PATHS).split(b"\0"):
        if not entry: continue
        meta,name=entry.split(b"\t",1);mode,kind,oid=meta.decode().split();name=name.decode()
        if kind!="blob" or mode not in ("100644","100755"): raise ValueError("unsupported selected entry: "+name)
        rows.append((name,oid,mode))
    return rows
INPUT_PIN="5e0d8ffbfea9279dcc4b2c70532145f7ea006fed77b2792095ebc326b1d3234e"
def retained():
    raw=(Path(__file__).parent/"RETAINED-INPUTS.json").read_bytes()
    if hashlib.sha256(raw).hexdigest()!=INPUT_PIN: raise ValueError("retained input selection drift")
    return json.loads(raw)
def verify(root):
    root=Path(root)
    for name,oid,mode in entries():
        f=root/name
        if f.is_symlink() or not f.is_file(): raise ValueError("source type drift: "+name)
        raw=f.read_bytes()
        actual=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
        if actual!=oid: raise ValueError("selected source drift: "+name)
    # Refuse injected Python modules rather than importing an untracked shadow.
    expected={n for n,_,_ in entries()}
    for one in retained():
        f=root/one["path"]
        if f.is_symlink() or hashlib.sha256(f.read_bytes()).hexdigest()!=one["sha256"]: raise ValueError("retained input drift: "+one["path"])
        expected.add(one["path"])
    for f in root.rglob("*"):
        if f.is_symlink(): raise ValueError("unselected symlink")
        if f.is_file() and str(f.relative_to(root)) not in expected: raise ValueError("unselected export file")
    return root

def materialize():
    root=Path(tempfile.mkdtemp(prefix="w370688-f36bcd75-",dir="/tmp"))
    rows=entries()
    proc=subprocess.Popen(["git","-C",str(REPO),"cat-file","--batch"],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    for name,oid,mode in rows:
        proc.stdin.write((oid+"\n").encode());proc.stdin.flush()
        actual,kind,size=proc.stdout.readline().decode().split();raw=proc.stdout.read(int(size));assert proc.stdout.read(1)==b"\n" and actual==oid and kind=="blob"
        f=root/name;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw);f.chmod(0o755 if mode=="100755" else 0o644)
    proc.stdin.close();assert proc.wait(timeout=60)==0
    for one in retained():
        raw=(REPO/one["path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=one["sha256"]: raise ValueError("historical input drift")
        f=root/one["path"];f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(raw)
    verify(root)
    print(json.dumps({"root":str(root),"commit":COMMIT,"files":len(rows),"method":"git ls-tree + cat-file; verified Git blob identities; no Git mutation"}))

def root():
    return verify(os.environ["W370688_SOURCE_ROOT"])
def identity():
    p=root()
    return {"root":str(p),"commit":COMMIT,"selected":COMMIT,"at_selected_commit":True,"verification":"every selected blob independently checked against committed tree"}
if __name__=="__main__": materialize()
