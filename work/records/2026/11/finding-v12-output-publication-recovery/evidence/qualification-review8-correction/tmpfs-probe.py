import os, json, time, shutil, tempfile, subprocess
import claude_agent
os.mkdir('/tmp/source')
with open('/tmp/source/big', 'wb') as f: f.write(b'x'*(20*1024*1024))
scratch=tempfile.mkdtemp(dir='/tmp')
a=claude_agent.ClaudeAgent(run=subprocess.run, home=scratch)
a._seen=None
errors=[]
copy=shutil.copytree
def observed(*args, **kwargs):
    try: return copy(*args, **kwargs)
    except BaseException as e:
        errors.append(str(e)); raise
shutil.copytree=observed
r=a._reviewer_check({'verification':['/bin/true']}, '/tmp/source', scratch, {'PATH':os.environ['PATH']}, invocation=60, command=30)
print(json.dumps({'check':r,'copy_errors':errors,'free':shutil.disk_usage('/tmp').free}),flush=True)
