"""K review probes: synthetic event transformations only; no live evidence claimed."""
import json,sys
sys.path[:0]=[sys.argv[1]+'/v12/python/src/baton_v12',sys.argv[1]+'/v12/worker']
from provider_policy.codex import stream_outcome
import codex_agent
U={"input_tokens":1,"cached_input_tokens":0,"cache_write_input_tokens":0,"output_tokens":1,"reasoning_output_tokens":0}
H=[{"type":"thread.started","thread_id":"t"},{"type":"turn.started"}];T=[{"type":"turn.completed","usage":U}]
enc=lambda ev:("\n".join(json.dumps(e) for e in ev)+"\n").encode()
msg={"type":"item.completed","item":{"id":"m","type":"agent_message","text":"done"}}
rr="model rerouted: a -> b (HighRiskCyberActivity)"
cmd=lambda code,status:[{"type":"item.started","item":{"id":"c","type":"command_execution","command":"x","aggregated_output":"","exit_code":None,"status":"in_progress"}},{"type":"item.completed","item":{"id":"c","type":"command_execution","command":"x","aggregated_output":"{\"type\":\"turn.failed\"}","exit_code":code,"status":status}}]
cases={
 "zero activity":H+T,
 "message only":H+[msg]+T,
 "tool exit 1 then message":H+cmd(1,"failed")+[msg]+T,
 "unpaired started item":H+cmd(0,"completed")[:1]+T,
 "file_change item":H+[{"type":"item.completed","item":{"id":"f","type":"file_change","changes":[]}}]+T,
 "unknown top-level activity":H+[{"type":"future.thing","x":1}]+T,
 "prose quoting reroute text":H+[{"type":"item.completed","item":{"id":"m","type":"agent_message","text":rr}}]+T,
 "prose claiming success, tool failed":H+cmd(2,"failed")+[{"type":"item.completed","item":{"id":"m","type":"agent_message","text":"All tests pass."}}]+T,
 "top-level error":H+[{"type":"error","message":"x"}]+T,
 "turn.failed mid":H+[{"type":"turn.failed","error":{}}]+T,
 "error item (non-reroute)":H+[{"type":"item.completed","item":{"id":"e","type":"error","message":"warn"}}]+T,
 "reroute item":H+[msg,{"type":"item.completed","item":{"id":"e","type":"error","message":rr}}]+T,
 "reroute as item.started":H+[{"type":"item.started","item":{"id":"e","type":"error","message":rr}}]+T,
 "reroute plus fault":H+[{"type":"error","message":"x"},{"type":"item.completed","item":{"id":"e","type":"error","message":rr}}]+T,
 "error item without message":H+[{"type":"item.completed","item":{"id":"e","type":"error"}}]+T,
 "second turn.started":H+[{"type":"turn.started"}]+T,
 "second turn.completed":H+T+T,
 "turn.aborted":H+[{"type":"turn.aborted"}]+T,
 "no turn.completed":H+[msg],
 "ends with turn.failed":H+[msg,{"type":"turn.failed","error":{}}],
 "item without id":H+[{"type":"item.completed","item":{"type":"agent_message","text":"x"}}]+T,
 "item event without item":H+[{"type":"item.completed"}]+T,
 "event without type":H+[{"item":{}}]+T,
 "extra member on final":H+[{"type":"turn.completed","usage":U,"model":"m"}],
}
out={}
for k,ev in cases.items():out[k]=stream_outcome(enc(ev))
raw=enc(H+[msg]+T)
out["truncated (no final LF)"]=stream_outcome(raw[:-1]);out["partial=True"]=stream_outcome(raw,partial=True)
out["duplicate JSON key"]=stream_outcome(raw.replace(b'{"type": "turn.started"}',b'{"type": "turn.started", "type": "turn.started"}'))
out["over 64 KiB"]=stream_outcome(enc(H+[{"type":"item.completed","item":{"id":"m","type":"agent_message","text":"x"*70000}}]+T))
a=codex_agent.CodexAgent.__new__(codex_agent.CodexAgent)
for label,status,ev in (("exit0 complete",0,H+[msg]+T),("exit1 complete stream",1,H+[msg]+T),("exit0 tool failed",0,H+cmd(1,"failed")+[msg]+T),("exit0 fault",0,H+[{"type":"error","message":"x"}]+T),("exit0 reroute",0,H+[{"type":"item.completed","item":{"id":"e","type":"error","message":rr}}]+T)):
    t=a.provider_terminal(status,enc(ev),partial=False);out["terminal: "+label]=[t["ok"],t["why"]]
json.dump(out,sys.stdout,indent=1)
