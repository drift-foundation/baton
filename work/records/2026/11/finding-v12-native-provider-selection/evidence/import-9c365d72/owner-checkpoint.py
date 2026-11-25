#!/usr/bin/env python3
"""Human selective checkpoint; --check is read-only. Exact staged retry supported."""
import argparse,hashlib,json,pathlib,subprocess
R=pathlib.Path('/home/sl/src/baton');D='work/records/2026/11/finding-v12-native-provider-selection'
O=R/D/'evidence/import-9c365d72';BASE='1ed26970e74ea48013e3e533e057e6ace08d0058'
def git(*a):return subprocess.check_output(['git','-C',str(R),*a])
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
    m=json.loads((O/'checkpoint-inputs.json').read_text())
    assert git('rev-parse','HEAD').decode().strip()==BASE,'HEAD drift'
    expected=dict(m['files']);mp=str((O/'checkpoint-inputs.json').relative_to(R));expected[mp]=sha((O/'checkpoint-inputs.json').read_bytes())
    for name,digest in expected.items():
        f=R/name;assert f.is_file() and not f.is_symlink() and sha(f.read_bytes())==digest,'file drift: '+name
    staged=set(git('diff','--cached','--name-only').decode().splitlines())
    assert staged<=set(expected),'unrelated staged content'
    assert not git('ls-files','--unmerged').strip()
    if staged:
        for name in staged:assert sha(git('show',':'+name))==expected[name],'staged byte mismatch: '+name
    # Current source/prose only. Preserve immutable raw evidence and patch syntax.
    subprocess.run(['git','-C',str(R),'diff','HEAD','--check','--',*m['whitespace_paths']],check=True)
    print('Verified eight accepted product paths and exact evidence; unrelated edits excluded.',flush=True)
    if a.check:return
    git('add','--',*expected)
    assert set(git('diff','--cached','--name-only').decode().splitlines())<=set(expected)
    for name,digest in expected.items():assert sha(git('show',':'+name))==digest,'staged mismatch: '+name
    subprocess.run(['git','-C',str(R),'diff','--cached','--check','--',*m['whitespace_paths']],check=True)
    subprocess.run(['git','-C',str(R),'commit','-m','Add optional provider service tier to selection, Codex adapter and attribution'],check=True)
    print('Checkpoint:',git('rev-parse','HEAD').decode().strip())
    print('CLI tier recognition and native qualification remain unproved; unrelated edits remain unstaged.')
if __name__=='__main__':main()
