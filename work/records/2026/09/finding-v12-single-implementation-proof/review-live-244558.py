import hashlib,json,os,pathlib,stat,subprocess,sys,time
D=pathlib.Path(__file__).resolve().parent
R=pathlib.Path("/home/sl/baton-runs/single-implementation-244216/run")
start=time.monotonic()
sys.path.insert(0,"/home/sl/baton-runs/single-implementation-242687/manager-source")
from baton_v12.worker_manager import context_delivery
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((D/"live-success-244216/manifest.json").read_text())
for name,digest in manifest["sha256"].items():
 assert sha(R/name)==digest==sha(D/"live-success-244216"/name)
out=json.loads((R/"outcome.json").read_text())
a=out["workload"]["attribution"][0]
checkout=pathlib.Path(a["line_path"])
custody=checkout.parent/"custody"/a["attempt_id"]
commands=[]
def run(args):
 p=subprocess.run(args,text=True,capture_output=True,timeout=20)
 commands.append({"argv":args,"code":p.returncode,"stdout":p.stdout,"stderr":p.stderr})
 return p
base=a["base"]; head=a["head"]
parent=run(["git","-C",str(checkout),"show","-s","--format=%P%n%an <%ae>%n%cn <%ce>",head])
assert parent.returncode==0 and parent.stdout.splitlines()==[base,"Baton worker <worker@baton.invalid>","Baton worker <worker@baton.invalid>"]
diff=run(["git","-C",str(checkout),"diff","--name-only",base,head]);assert diff.stdout=="harness.py\n"
content=run(["git","-C",str(checkout),"show",head+":harness.py"]);assert content.stdout=="print('READY')\n"
bundle=run(["git","-C",str(checkout),"bundle","verify",str(custody/"proposal/objects.bundle")]);assert bundle.returncode==0
heads=run(["git","-C",str(checkout),"bundle","list-heads",str(custody/"proposal/objects.bundle")]);assert head in heads.stdout
receipt=json.loads((custody/"provider-context-receipt/receipt.json").read_text())
assert receipt["attempt_id"]==a["attempt_id"] and receipt["complete"] and receipt["terminal"]=="success"
context=R/"private-contexts"/receipt["context_id"]
generation=context/"generations/1"
profile=json.loads((R/"context-profile.json").read_text())
profile["state_paths"]=[s.replace("{conversation_id}",receipt["conversation_id"]) for s in profile["state_paths"]]
fd=os.open(generation/"state",os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW)
try: actual=context_delivery._manifest(context_delivery._state(fd,profile,snapshot=True,immutable=True))
finally:os.close(fd)
assert actual==json.loads((generation/"manifest").read_text())
mode_entries=[]
for root in [generation,context/"uses"/receipt["use_id"]/"home"]:
 for q in [root,*root.rglob("*")]:
  info=q.lstat()
  mode_entries.append({"path":str(q.relative_to(context)),"mode":oct(stat.S_IMODE(info.st_mode)),"symlink":stat.S_ISLNK(info.st_mode)})
  if stat.S_ISDIR(info.st_mode):assert stat.S_IMODE(info.st_mode)&0o077==0
provider=json.loads(next(R.glob("launch/implementation/logs/*/provider.stdout.log")).read_text())
assert provider["session_id"]==receipt["conversation_id"] and provider["subtype"]=="success" and not provider["is_error"]
runtime=next(iter(out["cancellation"].values()))["runtime_id"]
commands.append({"argv":["docker","inspect","--type","container",runtime],"source":"standalone tools.exec_command observation before this script", "code":1,"stdout":"[]\n","stderr":"Error response from daemon: No such container: "+runtime+"\n"})
files=[*custody.rglob("*"),generation/"manifest",generation/"identity",R/"task.json",R/"context-profile.json"]
hashes={str(p.relative_to(R)):sha(p) for p in files if p.is_file() and not p.is_symlink()}
evidence={"claim":244558,"manifest_matches_original":True,"proposal_parent_and_attribution_verified":True,"bundle_verified":True,"only_change":"harness.py: print(READY), newline", "context_manifest_verified":actual,"context_modes":mode_entries,"provider":{"duration_ms":provider["duration_ms"],"num_turns":provider["num_turns"],"session_id":provider["session_id"],"subtype":provider["subtype"]},"commands":commands,"sha256":hashes,"elapsed_seconds":time.monotonic()-start,"limits":"No database opened; canonical Job state is retained supervisor evidence. Context inspected via read-only filesystem traversal; no resume. No live provider or rerun."}
(D/"review-live-244558.json").write_text(json.dumps(evidence,indent=2)+"\n")
print(json.dumps({"verified":True,"elapsed_seconds":evidence["elapsed_seconds"],"files":len(hashes),"context_entries":len(mode_entries),"provider":evidence["provider"]},indent=2))
