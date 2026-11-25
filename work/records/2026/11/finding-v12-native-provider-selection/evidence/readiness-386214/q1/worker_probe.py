"""Credential-free offline process INSIDE the selected manager-launched image."""
import hashlib,json,os,stat,subprocess,shutil
from pathlib import Path

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()
def main():
    assert (os.getuid(),os.getgid())==(1000,1000)
    identity=json.loads(Path('/opt/baton/q1-build.json').read_text())
    for path,expected in identity['image_files'].items(): assert sha(path)==expected,path
    import provider_policy as policy
    import provider_policy.codex, codex_entry, codex_agent
    from provider_policy.home import credential_state
    home=Path('/run/baton/provider-home')
    assert os.environ['HOME']==str(home) and os.environ['CODEX_HOME']==str(home/'codex')
    assert home.resolve()==home and (home/'codex').resolve()==home/'codex'
    login=home/'codex/auth.json';info=login.lstat()
    assert stat.S_ISREG(info.st_mode) and stat.S_IMODE(info.st_mode)==0o600 and info.st_uid==1000
    assert login.read_bytes()==b'{"q1_synthetic_only":true}\n'
    assert credential_state(str(home),'codex/auth.json')=='ready'
    instructions=home/'instructions/WORKER.md'
    assert instructions.read_bytes()==policy.worker_instructions()
    assert login.resolve()!=instructions.resolve()
    selected=dict(provider='codex',requested_model='gpt-6-astra',reported_identity='gpt-6-astra',cli_build='0.169.0')
    adapter=policy.adapter(selected,network='none')
    assert adapter['environment_policy']['CODEX_HOME']==str(home/'codex')
    assert adapter['managed_entries'][0]['path']=='instructions/WORKER.md'
    tools={}
    for name,args in [('git',['--version']),('python3',['--version']),('sha256sum',['--version']),('sh',['-c','exit 0']),('codex',['--version'])]:
        path=shutil.which(name);assert path,name
        result=subprocess.run([path,*args],stdin=subprocess.DEVNULL,capture_output=True,timeout=10,env=dict(os.environ))
        assert result.returncode==0,(name,result.returncode)
        assert len(result.stdout)+len(result.stderr)<=65536
        tools[name]=dict(path=path,realpath=os.path.realpath(path),stdout=result.stdout.decode(),stderr=result.stderr.decode(),exit_status=result.returncode)
    assert tools['codex']['stdout'].strip()==identity['cli_version']
    binary=Path('/usr/local/lib/node_modules/@openai/codex/node_modules/@openai/codex-linux-x64/vendor/x86_64-unknown-linux-musl/bin/codex')
    assert binary.stat().st_size==identity['codex_binary_bytes']
    binary_hash=sha(binary);assert binary_hash==identity['codex_binary_sha256']
    # Prove a real child writes through the mount with the selected UID, then
    # removes only its own synthetic marker; credential bytes are untouched.
    marker=home/'q1-write-check';fd=os.open(marker,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    os.write(fd,b'Q1 synthetic mount proof\n');os.fsync(fd);os.close(fd)
    assert marker.stat().st_uid==1000;marker.unlink()
    print(json.dumps(dict(schema='baton.q1-offline-observation/1',identity=identity,uid=os.getuid(),gid=os.getgid(),tools=tools,codex_binary_sha256=binary_hash,home=str(home),codex_home=os.environ['CODEX_HOME'],synthetic_login_mode='0600',instruction_sha256=sha(instructions),provider_called=False,image_identity_basis='baked source/packet label; actual image supplied separately by host engine receipt'),sort_keys=True))
if __name__=='__main__':main()
