"""Independent bounded probes; isolated existing test fixtures, no live runtime."""
import copy,json,sys,tempfile,os,subprocess
from pathlib import Path
# Resolve by the checkout anchor rather than a guessed dossier depth.
ROOT=next(p for p in Path(__file__).resolve().parents if (p/"v12/python/src").is_dir())
sys.path[:0]=[str(ROOT/"v12/python/src"),str(ROOT/"v12/python"),str(ROOT/"v12/worker"),str(ROOT/"v12/python/src/baton_v12")]
from tests.job_manager import test_review_driver as t
from baton_v12.worker_manager import frozen_output_of,load_manifest
from baton_v12.contracts import ContractRefusal
import claude_agent as ca
out={}
c=t.TheReviewEndingTakesNoCallersVerdict(); c.setUp()
try:
 h=c.reviewed()
 a,steps,adapter=c.ending(h,terminal=None)
 out["no_terminal"]={k:a[k] for k in ("outcome","verdict","cleaned_up")}
 out["no_terminal"]["steps"]=steps
 try: c.ending(h,terminal="not-a-document")
 except Exception as e: out["malformed_terminal"]={"exception":type(e).__name__,"detail":str(e)}
 frozen=frozen_output_of(c.control,h["attempt_id"])
 result=load_manifest(c.control,frozen["manifest_digest"],"resultManifest")
 outputs=copy.deepcopy(result["outputs"])
 third=copy.deepcopy(outputs[0]);third["name"]="proposal";third["type"]="git-change-proposal"
 third["artifact"]["artifact_id"]="artifact-proposal-probe"
 third["result_metadata"][t.review_driver.REVIEW_CLAIM_NAMESPACE]["verdict"]="rejected"
 outputs.append(third)
 c.retained(h["attempt_id"],generation=1,observed=h["observed"],outputs=outputs)
 read=t.review_driver.review_verdict_from_result(c.control,attachment_id=h["attachment"]["attachment_id"])
 out["competing_proposal"]={"findings_claim":"accepted","proposal_claim":"rejected","reader_verdict":read["verdict"],"retained_manifest_valid":True}
finally: c.doCleanups()
with tempfile.TemporaryDirectory(prefix="w110772-report-probe-") as room:
 p=Path(room)/ca.REVIEW_REPORT
 bodies={"valid":json.dumps({"schema":ca.REVIEW_REPORT_SCHEMA,"verdict":"accepted","findings":"checked"}),"deeply_nested":"["*2000+"0"+"]"*2000,"surrogate":json.dumps({"schema":ca.REVIEW_REPORT_SCHEMA,"verdict":"accepted","findings":"\ud800"})}
 for name,body in bodies.items():
  p.write_text(body)
  try:
   answer=ca._review_report(room)
   observed={"adopted":answer is not None}
   if answer:
    try: answer["findings"].encode("utf-8")
    except Exception as e:observed["publication_exception"]=type(e).__name__
   out["report_"+name]=observed
  except Exception as e:out["report_"+name]={"exception":type(e).__name__}
with tempfile.TemporaryDirectory(prefix="w110772-fifo-probe-") as room:
 os.mkfifo(Path(room)/ca.REVIEW_REPORT)
 code="import sys;sys.path[:0]="+repr(sys.path[:4])+";import claude_agent; print(claude_agent._review_report("+repr(room)+"))"
 try:
  child=subprocess.run([sys.executable,"-c",code],capture_output=True,text=True,timeout=2)
  out["fifo_report"]={"returncode":child.returncode,"stdout":child.stdout,"stderr":child.stderr}
 except subprocess.TimeoutExpired:
  out["fifo_report"]={"timed_out_seconds":2,"conclusion":"report open blocked before regular-file validation; probe child killed and waited by subprocess.run"}
print(json.dumps(out,indent=2))
Path(__file__).with_suffix(".json").write_text(json.dumps(out,indent=2)+"\n")
