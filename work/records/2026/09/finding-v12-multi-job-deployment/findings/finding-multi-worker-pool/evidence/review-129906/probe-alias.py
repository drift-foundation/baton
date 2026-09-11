from pathlib import Path
import copy,json,time,traceback
from tests.tools.test_stage_execution import TheMultiWorkerPoolComposesWithoutASecondAllocator as Fixture
from tests.job_manager import fixtures
from baton_v12.job_manager import scheduler,submit
from baton_v12.contracts import ContractRefusal
out=Path(__file__).parent
results=[]
start=time.monotonic()
for aliases in (True,):
 f=Fixture("runTest")
 try:
  f.setUp()
  members=f.multi()
  if aliases:
   from baton_v12.authority import Authority
   authority=Authority.open(f.authority_path,expected_authority_uuid=f.config["authority_uuid"])
   try: authority.bind_endpoint(f.SECOND_PRODUCER,members["workers"][0]["deployment"]["principal"])
   finally: authority.dispose()
   members["workers"][1]["deployment"]["principal"]=members["workers"][0]["deployment"]["principal"]
  jobs,control,composed=f.serving(**members)
  work=[]
  for i,role in enumerate(("implementation","implementation","implementation","review","review")):
   stage=fixtures.stage(role, f.work, profile_name=f.config["profile_name"],profile_digest=f.config["profile_digest"])
   work.append(fixtures.job("capacity-"+str(i),stages=[stage]))
  submit(jobs,fixtures.submission(jobs=work))
  attempts=[fixtures.JobManagerCase.attempting(f,jobs,j["job_id"]+"/"+j["stages"][0]["kind"]) for j in work]
  allocated=[]; refused=[]
  for i,a in enumerate(attempts):
   try:
    row=scheduler.reserve(jobs,a)
    allocated.append({k:row[k] for k in ("stage_id","worker_id","participant","canonical_principal","allocation_state","lane")})
   except ContractRefusal as e:refused.append({"i":i,"category":e.category,"code":e.code})
  expected=[1,2] if aliases else [2]
  f.assertEqual([r["i"] for r in refused],expected)
  f.assertEqual(len(allocated),3 if aliases else 4)
  f.assertEqual(len({r["canonical_principal"] for r in allocated}),len(allocated))
  f.assertEqual(sum(r["lane"]=="review" for r in allocated),2)
  f.assertTrue(all(r["allocation_state"]=="reserved" for r in allocated))
  first=scheduler.reserve(jobs,attempts[0]);again=scheduler.reserve(jobs,attempts[0]);f.assertEqual(first,again)
  results.append({"aliases":aliases,"allocated":allocated,"refused":refused,"exact_replay":True})
 except Exception:
  results.append({"aliases":aliases,"error":traceback.format_exc()})
 finally:f.doCleanups()
report={"cap_seconds":5,"wall_seconds":time.monotonic()-start,"results":results,"passed":all("error" not in r for r in results)}
(out/"verification-alias.json").write_text(json.dumps(report,indent=2)+"\n")
print(json.dumps(report,indent=2))
raise SystemExit(0 if report["passed"] else 1)
