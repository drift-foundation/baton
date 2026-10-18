import json,shutil
from pathlib import Path
from tests.tools.test_dossier_recovery import TheClosedRecoverySet
report={}
for mode in ("missing-selector","changed-selector-uuid"):
 f=TheClosedRecoverySet();f.setUp()
 try:
  f.manifested();f.restore();shutil.rmtree(f.destination)
  selector=Path(f.restored_at("instance"))
  if mode=="missing-selector":selector.unlink()
  else:
   doc=json.loads(selector.read_text());doc["authority_uuid"]="f"*32;selector.write_text(json.dumps(doc))
  code,out,err=f.checked();report[mode]={"exit":code,"faults":json.loads(out)["faults"],"compatible":json.loads(out)["schema_compatible"]};assert code==0
 finally:f.doCleanups()
print(json.dumps(report,indent=2))
