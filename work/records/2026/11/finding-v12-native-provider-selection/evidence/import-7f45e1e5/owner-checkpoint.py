#!/usr/bin/env python3
"""Human-only selective checkpoint. --check does not mutate Git."""
import argparse,hashlib,json,pathlib,subprocess
R=pathlib.Path('/home/sl/src/baton')
O=R/'work/records/2026/11/finding-v12-native-provider-selection/evidence/import-7f45e1e5'
BASE='c1727ad68ffa0f5015b07f27202a66be00848143'
def git(*args,input=None):
    return subprocess.check_output(['git','-C',str(R),*args],input=input)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--check',action='store_true'); a=ap.parse_args()
    m=json.loads((O/'checkpoint-inputs.json').read_text())
    assert git('rev-parse','HEAD').decode().strip()==BASE,'HEAD changed; revalidate before checkpoint'
    assert not git('diff','--cached','--name-only').strip(),'index is not empty'
    for name,expected in m['files'].items():
        p=R/name; assert p.is_file() and not p.is_symlink() and digest(p.read_bytes())==expected,'drift: '+name
    design=R/'v12/DESIGN.md'
    assert digest(design.read_bytes())==m['design_worktree_sha256'],'DESIGN worktree changed'
    staged=(O/'design-for-index.md').read_bytes()
    assert digest(staged)==m['design_index_sha256']
    assert git('diff','--check','--',*m['product_paths'],'v12/DESIGN.md')==b''
    print('Verified seven accepted paths, narrow DESIGN staging and pinned dossier evidence. Other changes stay unstaged.',flush=True)
    if a.check:return
    names=list(m['files'])+[str((O/'checkpoint-inputs.json').relative_to(R))]
    git('add','--',*names)
    blob=git('hash-object','-w','--stdin',input=staged).decode().strip()
    git('update-index','--add','--cacheinfo','100644',blob,'v12/DESIGN.md')
    assert git('show',':v12/DESIGN.md')==staged
    changed=set(git('diff','--cached','--name-only').decode().splitlines())
    assert changed <= set(names)|{'v12/DESIGN.md'},'unexpected staged path'
    git('diff','--cached','--check')
    subprocess.run(['git','-C',str(R),'commit','-m','Preserve seeded credentials across Job-worker restarts'],check=True)
    assert digest(design.read_bytes())==m['design_worktree_sha256'],'working DESIGN was altered'
    print('Checkpoint:',git('rev-parse','HEAD').decode().strip())
    print('Other DESIGN edits and W386057 remain outside this commit. C2/C3 and native qualification remain open.')
if __name__=='__main__':main()
