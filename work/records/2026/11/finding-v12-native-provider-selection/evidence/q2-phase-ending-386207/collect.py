"""After positive cessation only: bounded private inventory and fixed byte verification."""
import hashlib,json,os,stat
from pathlib import Path
MAX_FILES=4096
MAX_TOTAL=128*1024*1024
MAX_FILE=32*1024*1024

def inventory(root):
    root=Path(root);answer={};total=0
    if not root.exists():return answer
    assert root.is_dir() and not root.is_symlink()
    for here,dirs,files in os.walk(root,followlinks=False):
        for name in dirs:
            assert not (Path(here)/name).is_symlink(),'linked evidence directory refused'
        for name in files:
            path=Path(here)/name;info=path.lstat()
            assert stat.S_ISREG(info.st_mode) and info.st_size<=MAX_FILE
            total+=info.st_size;assert total<=MAX_TOTAL and len(answer)<MAX_FILES
            fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW)
            try:
                h=hashlib.sha256();count=0
                with os.fdopen(fd,'rb') as stream:
                    while raw:=stream.read(65536):
                        count+=len(raw);assert count<=MAX_FILE;h.update(raw)
                assert count==info.st_size
            except BaseException:raise
            answer[str(path.relative_to(root))]=dict(bytes=count,sha256=h.hexdigest())
    return answer

def collect(root,attempt):
    root=Path(root);native=root/'native'
    source=inventory(native/'fixture')
    workspace=native/'workspaces'/attempt/'workspace'
    candidate=inventory(workspace/'candidate')
    changed=sorted(k for k in source.keys()|candidate.keys() if source.get(k)!=candidate.get(k))
    expected=hashlib.sha256(b'after\n').hexdigest()
    verified=changed==['message.txt'] and candidate.get('message.txt')==dict(bytes=6,sha256=expected)
    result=dict(verification='pass' if verified else 'missing-or-mismatch',changed_paths=changed,expected_changed_paths=['message.txt'],verification_method='trusted post-cessation byte and complete tree comparison; no candidate code executed',candidate=candidate,workspace=inventory(workspace),logs=inventory(native/'launch/logs'/attempt),exchange=inventory(native/'launch'/attempt))
    (root/'capture-inventory.json').write_text(json.dumps(result,indent=2)+'\n')
    return dict(edit_verified=verified,private_inventory='capture-inventory.json',candidate_present=bool(candidate))
