import copy,json,unittest
from pathlib import Path
from tests.manager.test_intake import TheAbandonedGateIsDischargedFromItsOwnCommittedEvidence as Case, OTHER_POLICY
from tests.tools.test_stage_execution import UnfinishedWorkIsFencedBeforeAnythingRepeatsIt as Composed
from baton_v12.worker_manager import intake
from baton_v12.contracts import ContractRefusal
out={}
def fake_probe(name,fn):
 c=Case("test_the_committed_abandonment_discharges_its_own_gate")
 try:
  c.setUp(); c.abandoned(); c.gated(); out[name]=fn(c)
 finally:c.doCleanups()
def changed_policy(c):
 first=c.discharge(); calls=len(c.satisfied())
 try:
  second=c.discharge(retention_policy_digest=OTHER_POLICY)
  return {"refused":False,"same_receipt":second==first,"returned_policy":second["retention_policy_digest"],"requested_policy":OTHER_POLICY,"new_remote_calls":len(c.satisfied())-calls}
 except ContractRefusal as e:return {"refused":True,"category":e.category,"code":e.code}
fake_probe("changed_policy_replay",changed_policy)
def changed_fence(c,field,value):
 op=c.destroy_operation_id(); original=json.loads(c.store._connection.execute("SELECT result FROM operations WHERE operation_id=?",(op,)).fetchone()["result"])
 spoiled=copy.deepcopy(original); spoiled["fenced"][field]=value;c.rewrite_operation(op,result=json.dumps(spoiled))
 try:
  proof=c.read(); receipt=c.discharge()
  return {"refused":False,"accepted_fence":proof["fence"],"authority_phase":receipt["authority_receipt"]["phase"],"remote_calls":len(c.satisfied())}
 except ContractRefusal as e:return {"refused":True,"category":e.category,"code":e.code}
for field,value in [("cause","pass"),("phase","queued"),("fenced","false")]:
 fake_probe("fence_"+field,lambda c,f=field,v=value:changed_fence(c,f,v))
c=Composed("test_no_fresh_assignment_follows_the_declaration_and_why")
try:
 c.setUp(); held=c.started_correction(c.committed_handoff()); c.declare_abandoned(held)
 deployment=c.deployment_of(held); worker=c.worker_of(held.composed,"implementation")
 proof=intake.abandonment_cleanup_of(held.control,attempt_id=held.abandoned,retention_policy_digest=deployment.retention_policy_digest)
 before=c.projected()["gate"]
 receipt=intake.discharge_abandoned_quiescence_gate(held.control,worker.port,attempt_id=held.abandoned,retention_policy_digest=deployment.retention_policy_digest)
 assert c.projected()["gate"] is None
 assert intake.abandoned_gate_discharge_of(held.control,held.abandoned)==receipt
 out["real_authority_positive"]={"gate_before":before,"gate_after":None,"proof":proof,"receipt":receipt}
finally:c.doCleanups()
Path(__file__).with_name("probe.json").write_text(json.dumps(out,indent=2)+"\n")
result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(Case))
print(json.dumps({k:v for k,v in out.items() if k!="real_authority_positive"},indent=2));print("real_authority_positive: passed")
raise SystemExit(not result.wasSuccessful())
