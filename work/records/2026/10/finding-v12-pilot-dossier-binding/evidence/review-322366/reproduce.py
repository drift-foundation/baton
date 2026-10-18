import json,shutil
from pathlib import Path
from tests.tools.test_dossier_recovery import TheClosedRecoverySet
report={}
for mode in ("missing-selector","changed-selector-uuid","null-selector"):
 f=TheClosedRecoverySet();f.setUp()
 try:
  f.manifested();f.restore();shutil.rmtree(f.destination)
  selector=Path(f.restored_at("instance"))
  if mode=="missing-selector":selector.unlink()
  elif mode=="null-selector":selector.write_text("null\n")
  else:
   doc=json.loads(selector.read_text());doc["authority_uuid"]="f"*32;selector.write_text(json.dumps(doc))
  try:
   code,out,err=f.checked();report[mode]={"exit":code,"faults":json.loads(out)["faults"],"selector":json.loads(out).get("restored_selector")}
  except Exception as error:report[mode]={"exception":type(error).__name__,"message":str(error)}
 finally:f.doCleanups()
print(json.dumps(report,indent=2))
