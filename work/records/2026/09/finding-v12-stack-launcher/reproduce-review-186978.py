"""Independent retained-bundle smoke, candidate audit and bootstrap recipe."""
import hashlib,json,os,pathlib,subprocess,sys,tempfile,time
ROOT=pathlib.Path(__file__).resolve().parents[5];D=pathlib.Path(__file__).parent
sys.path[:0]=[str(ROOT/"v12/python"),str(ROOT/"v12/python/src")]
from tools import instance
candidate=json.loads((D/"EVIDENCE-186890.json").read_text())["candidates"]
artifact=json.loads((D/"ARTIFACT-MANIFEST-186890.json").read_text())
for p,h in dict(candidate,**artifact["source"]).items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p
assert hashlib.sha256((D/"BUILD-186890.log").read_bytes()).hexdigest()==artifact["build"]["log_sha256"]
started=time.monotonic();bundles={}
for path in (artifact["bundle"]["path"],"/var/tmp/w183883-live-186890/deployment/distro","/var/tmp/w183883-live-186890/deployment-b/distro"):
    held=instance.manifest(path);assert held["digest"]==artifact["bundle"]["manifest_digest"],path
    bundles[path]={"files":held["files"],"digest":held["digest"]}
scratch=pathlib.Path(tempfile.mkdtemp(prefix="w183883-review186978-"))
env=dict(os.environ,PYTHONPATH="src:.",PYTHONDONTWRITEBYTECODE="1",BATON_V12_STACK_DISTRO=artifact["bundle"]["path"],XDG_RUNTIME_DIR=str(scratch))
def execute(argv,env=env,cwd=ROOT/"v12/python",timeout=30):
    done=subprocess.run(argv,cwd=cwd,env=env,text=True,capture_output=True,timeout=timeout)
    return {"argv":argv,"returncode":done.returncode,"stdout":done.stdout,"stderr":done.stderr}
command=[sys.executable,"-B","-m","unittest","-v","tests.tools.test_instance","tests.tools.test_environment","tests.tools.test_packaging"]
tests=execute(command);assert tests["returncode"]==0,tests["stderr"]
assert "skipped" not in tests["stderr"].lower(),tests["stderr"]
# Only invalid JSON {} could reach bootstrap if its shell proceeds; no valid
# production fixture/Authority or deployment is supplied or created.
inputs=scratch/"inputs.json";inputs.write_text("{}")
recipe=execute(["just","--justfile",str(ROOT/"v12/justfile"),"bootstrap",str(inputs)],cwd=ROOT/"v12")
empty=execute(["realpath","-m",""])
assert empty["returncode"]!=0 and recipe["returncode"]!=0 and empty["stderr"].strip() in recipe["stderr"],(recipe,empty)
# Test runner at the end of test-packaging inherits this selector unchanged.
# No build is repeated: demonstrate the inherited override against an existing
# verified bundle and inspect the recipe's unchanged environment forwarding.
missing=execute([sys.executable,"-B","-m","unittest","-v","tests.tools.test_packaging"],env=dict(env,BATON_V12_STACK_DISTRO=str(scratch/"missing-bundle")))
assert missing["returncode"]==0 and "skipped=9" in missing["stderr"],missing
# Read only the retained fixture deployment paths, not credentials or databases.
configs={}
for name in ("deployment","deployment-b"):
    place=pathlib.Path("/var/tmp/w183883-live-186890")/name
    d=json.loads((place/"deployment.json").read_text())
    configs[name]={"repo_entries":[p.name for p in (place/"repo").iterdir()],"line_declared_base":d["line_declared_base"],"workers":[{"nominated_source":w["deployment"]["nominated_source"],"workspace_storage":w["deployment"]["workspace_storage"]} for w in d["workers"]]}
pids=execute(["ps","-o","pid=,stat=,args=","-p","3893575,3893576,3893580,3893581"],cwd=ROOT)
assert pids["returncode"]==1 and not pids["stdout"].strip(),pids
out={"prior_attempt":{"scratch":"/tmp/w183883-review186978-26wovo8p","result":"All133 focused tests passed and bundle hashes matched; reproduction assertion incorrectly expected GNU realpath wording. Actual host realpath reports invalid value for one of the arguments. Corrected to compare actual empty-operand stderr, not count a misnamed assertion as product evidence.","tool_wall_seconds":2.511310005,"verification_seconds":"unknown: no internal stopwatch persisted"},"empty_realpath_control":empty,"claim":186978,"candidate_hashes":candidate,"additional_artifact_source_hashes":artifact["source"],"bundles":bundles,"focused_tests":tests,"bootstrap_without_optional_distro":recipe,"missing_explicit_packaging_bundle_skips_green":missing,"retained_deployment_inspection":configs,"reported_lifecycle_pids_absent":pids,"verification_seconds":time.monotonic()-started,"retained_scratch":str(scratch),"scope":"133 focused tests including nine real retained-bundle checks, read-only artifact/config/pid audit and harmless invalid-input recipe. No rebuild, actual stack start/stop, Authority/store read, credentials read, provider/engine/Job, external-root write or Git mutation."}
(D/"REVIEW-EVIDENCE-186978.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps({k:v for k,v in out.items() if k not in ("candidate_hashes","additional_artifact_source_hashes","focused_tests","missing_explicit_packaging_bundle_skips_green")},indent=2));print(tests["stderr"][-200:]);print(missing["stderr"][-150:])
