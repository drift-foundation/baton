import copy,json
from pathlib import Path
from tests.manager.test_intake import TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence as Case
from baton_v12.contracts import ContractRefusal
out={}
for field,value in [("directory_custody",None),("kept",["invented-artifact"]),("kind","foreign-cleanup")]:
 c=Case("test_the_committed_abandonment_discharges_its_own_gate")
 try:
  c.setUp(); c.abandoned(); c.gated(); op=c.destroy_operation_id()
  data=json.loads(c.store._connection.execute("SELECT result FROM operations WHERE operation_id=?",(op,)).fetchone()["result"])
  data["cleanup"][field]=value;c.rewrite_operation(op,result=json.dumps(data))
  try:
   proof=c.read(); receipt=c.discharge();out[field]={"refused":False,"accepted_value":proof["cleanup"][field],"remote_calls":len(c.satisfied())}
  except ContractRefusal as e:out[field]={"refused":True,"category":e.category,"code":e.code}
 finally:c.doCleanups()
Path(__file__).with_name("custody-probe.json").write_text(json.dumps(out,indent=2)+"\n")
print(json.dumps(out,indent=2))
