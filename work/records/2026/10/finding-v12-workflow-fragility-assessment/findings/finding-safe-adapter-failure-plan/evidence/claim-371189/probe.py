"""Inert proposal example checks; no worker/provider execution or product coverage."""
from pathlib import Path
import hashlib,json,sys,time
started=time.monotonic()
root=Path(__file__).resolve().parents[9]
sys.path.insert(0,str(root/"v12/python/src"))
from baton_v12.worker_manager import exchange
here=Path(__file__).parent
attempt="attempt-synthetic-371189"
command={"schema":exchange.COMMAND_SCHEMA,"session":"session-synthetic-371189","attempt_id":attempt,"sequence_id":exchange.sequence_of(attempt),"operations":[{"operation":x,"operation_id":exchange.worker_operation_id(attempt,x)} for x in exchange.OPERATIONS]}
raw=(json.dumps(command,sort_keys=True,separators=(",",":"))+"\n").encode()
terminal={"schema":"baton.worker-exchange.terminal/2",**{k:command[k] for k in ("session","attempt_id","sequence_id")},"command_digest":"sha256:"+hashlib.sha256(raw).hexdigest(),"ending":"faulted","answered":["describe"],"disposition":None,"fault_code":"agent","manifest_digest":None,"adapter_failure":{"component":"role-adapter","code":"other-role-output-required","role":"implementation","operation":"work","operation_id":exchange.worker_operation_id(attempt,"work")}}
terminal_raw=(json.dumps(terminal,sort_keys=True,indent=2)+"\n").encode()
assert set(terminal)==set(exchange.TERMINAL_MEMBERS)|{"adapter_failure"}
assert exchange.TERMINAL_SCHEMA=="baton.worker-exchange.terminal/1"
assert "other-role-output-required" not in exchange.FAULT_CODES
assert len(json.dumps(terminal["adapter_failure"]).encode())<=1024
facts={k:{"known":True,"value":v,"source":"worker-exchange.terminal"} for k,v in terminal["adapter_failure"].items()}
for k in ("operation_id","session","sequence_id","command_digest"):
    value=terminal["adapter_failure"][k] if k=="operation_id" else terminal[k]
    facts[k]={"known":True,"value":value,"source":"worker-exchange.command"}
facts["terminal_digest"]={"known":True,"value":"sha256:"+hashlib.sha256(terminal_raw).hexdigest(),"source":"worker-exchange.terminal-bytes"}
facts["observed_at"]={"known":True,"value":"2026-10-28T03:20:00.000Z","source":"job-status.observed_at"}
branch={"state":"known","facts":facts}
assert set(facts)==set("component code role operation operation_id session sequence_id command_digest terminal_digest observed_at".split())
for name,data in (("COMMAND.synthetic.json",raw),("TERMINAL.proposed.json",terminal_raw),("ADAPTER-FAILURE.proposed.json",(json.dumps(branch,sort_keys=True,indent=2)+"\n").encode())):
    (here/name).write_bytes(data)
print(json.dumps({"kind":"inert-proposal-example-check","checks":5,"elapsed_seconds":round(time.monotonic()-started,6),"product_tests":0,"live_calls":0,"note":"Examples are synthetic; proposed readers are not implemented."},sort_keys=True))
