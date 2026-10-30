import json,os,tempfile
from tests.manager.test_claude_context import ServingContextCase
from tests.manager import test_verifier_topology as topology
from tools import single_worker as s
from baton_v12.worker_manager import ControlStore,configure_workspace_group,configured_workspace_group
from baton_v12.worker_manager import source_boundary,oci
case=ServingContextCase();case.setUp()
try:
 with tempfile.TemporaryDirectory() as tmp:
  doc=case.worker("implementation")["deployment"];doc.update(schema=s.LAYOUT_CONFIG_SCHEMA,verifier_layout=source_boundary.image_layout_marker(),launch_home=tmp)
  held=s._held(doc)
  store=ControlStore.open(os.path.join(tmp,"control.sqlite3"),incarnation="review",clock=lambda:"2026-10-28T00:00:00.000Z")
  try:
   configure_workspace_group(store,os.getgid());delivery=s.layout_delivery(held,configured_workspace_group(store))
   agent=topology.AGENT.__new__(topology.AGENT);agent._seen={};agent.LAYOUT_DOCUMENT=delivery.place;agent.LAYOUT_MARKER=os.path.join(tmp,"marker.json")
   with open(agent.LAYOUT_MARKER,"w") as f:json.dump(source_boundary.image_layout_marker(),f)
   assert agent._selected_layout()==delivery.document
   roots={}
   for name in ("inputs","workspace"):
    roots[name]=os.path.join(tmp,name);os.mkdir(roots[name])
   adapter=oci.OciAdapter("podman",lambda *a,**k:None,identity={key:held[key] for key in ("image_digest","profile_digest","policy_digest","adapter_digest")},assignment_roots=roots,posture="execution",layout_delivery=delivery)
   assert adapter.layout_delivery is delivery
   print(json.dumps({"context_mode":held["provider_context"]["mode"],"complete_configuration_admitted":True,"delivery_materialized":True,"adapter_accepted":True,"worker_reader_accepted":True,"engine_called":False}))
  finally:store.close()
finally:case.doCleanups()
