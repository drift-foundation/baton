import json, os, subprocess, unittest, sys, collections
from unittest import mock
from tests.tools.test_managed_apply import AnOrdinaryManagedIntegration
errors=collections.Counter()
def trace(frame,event,arg):
    if event == "call":
        return trace if frame.f_code.co_filename.endswith(("integration_worker.py","stage_execution.py")) else None
    if event == "exception" and arg[0].__name__ == "ContractRefusal":
        errors[(frame.f_code.co_name,frame.f_lineno,str(arg[1]))]+=1
    return trace
original = subprocess.Popen
observed=[]
processes=[]
apply_mounts={}
from baton_v12.worker_manager import exchange
discard_original=exchange.discard
observe_original=exchange.observation
seen_states=set()
def observe(delivery):
    answer=observe_original(delivery)
    if apply_mounts and delivery.command_root == apply_mounts.get("/run/baton/exchange/command"):
        state=(answer.get("state"),bool(answer.get("receipt")),bool(answer.get("terminal")))
        if state not in seen_states:
            seen_states.add(state);print("EXCHANGE_STATE",state,flush=True)
    return answer
def discard(root):
    import traceback
    if apply_mounts and apply_mounts["/run/baton/exchange/command"].startswith(str(root)):
        print("DISCARD_CALL", "".join(traceback.format_stack(limit=7)),flush=True)
    return discard_original(root)
publish_original=exchange.publish_command
def publish(delivery,document):
    if apply_mounts:
        print("PUBLISH_MATCH", delivery.command_root == apply_mounts.get("/run/baton/exchange/command"),flush=True)
    return publish_original(delivery,document)
class Result(unittest.TextTestResult):
    def addFailure(self,test,err):
        for process in processes:
            print("BEFORE_CLEANUP_EXIT",process.poll(),flush=True)
        for target, source in apply_mounts.items():
            if target.endswith(("/command","/events")):
                print("BEFORE_CLEANUP",target,os.listdir(source) if os.path.isdir(source) else "ABSENT",flush=True)
        super().addFailure(test,err)
def popen(args,*a,**kw):
    if isinstance(args,(list,tuple)) and "-c" in args and "integration_entry.main" in args[args.index("-c")+1]:
        mounts=json.loads(args[4])
        facts={target: {"exists":os.path.exists(source), "directory":os.path.isdir(source)} for target,source in mounts.items()}
        print("AT_APPLY_POPEN",json.dumps(facts,sort_keys=True),flush=True)
        with open(mounts["/run/baton/launch.json"]) as stream:
            launch=json.load(stream)
        print("LAUNCH_SELECTION",json.dumps({k:launch.get(k) for k in ("schema","transport")}),flush=True)
        observed.append(facts)
        apply_mounts.update(mounts)
        process=original(args,*a,**kw)
        processes.append(process)
        return process
    return original(args,*a,**kw)
sys.settrace(trace)
with mock.patch.object(subprocess,"Popen",popen), mock.patch.object(exchange,"publish_command",publish), mock.patch.object(exchange,"discard",discard), mock.patch.object(exchange,"observation",observe):
    result=unittest.TextTestRunner(resultclass=Result).run(unittest.TestSuite([AnOrdinaryManagedIntegration("test_preparation_judgments_apply_and_target_settle")]))
sys.settrace(None)
print("APPLY_LAUNCH_COUNT",len(observed))
for key,count in errors.most_common(12):print("RAISED",count,key)
raise SystemExit(not result.wasSuccessful())
