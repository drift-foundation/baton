import os, sys, time, json, tempfile, subprocess
from datetime import datetime, timezone, timedelta
sys.path.insert(0, sys.argv[1])
import publication_entry as pe
def iso(dt): return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]+"Z"
now=datetime.now(timezone.utc)
root=tempfile.mkdtemp(dir=sys.argv[2])
# 1 ordinary copy via the real child
src=os.path.join(root,"src"); os.makedirs(os.path.join(src,"a/b")); open(os.path.join(src,"a/b/f.txt"),"w").write("x"*10); open(os.path.join(src,"top"),"w").write("y")
r=pe.supervised([sys.executable,"-I",pe.__file__,"--adopt",src,os.path.join(root,"dst")], iso(now+timedelta(seconds=30)))
print("copy",r["status"],r["timed_out"],r["group_gone"],sorted(os.listdir(os.path.join(root,"dst"))),open(os.path.join(root,"dst/a/b/f.txt")).read())
# 2 symlink refused
os.symlink("/etc/passwd",os.path.join(src,"link"))
r=pe.supervised([sys.executable,"-I",pe.__file__,"--adopt",src,os.path.join(root,"dst2")], iso(now+timedelta(seconds=30)))
print("link",r["status"],r["timed_out"])
# 3 existing destination refused
r=pe.supervised([sys.executable,"-I",pe.__file__,"--adopt",src,os.path.join(root,"dst")], iso(now+timedelta(seconds=30)))
print("exists",r["status"])
# 4 hung child with a TERM-ignoring grandchild, ended at the absolute instant
code="import os,signal,subprocess,sys,time\nsubprocess.Popen([sys.executable,'-c','import signal,time\\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\\ntime.sleep(120)'])\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\ntime.sleep(120)"
t=time.time(); r=pe.supervised([sys.executable,"-c",code], iso(datetime.now(timezone.utc)+timedelta(seconds=1)))
print("hung",r["status"],r["timed_out"],r["group_gone"],round(time.time()-t,1))
# 5 already past
r=pe.supervised(["/bin/true"], iso(now-timedelta(seconds=5))); print("past",r["timed_out"],r["started"])
# 6 no deadline / naive time
for bad in (None,"","2026-01-01T00:00:00","soon"):
    try: pe.supervised(["/bin/true"],bad); print("BAD accepted",bad)
    except Exception as e: print("refused",repr(bad),e.code)
