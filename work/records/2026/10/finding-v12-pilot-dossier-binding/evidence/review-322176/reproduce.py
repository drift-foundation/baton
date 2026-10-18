import json,shutil
from pathlib import Path
from tests.tools.test_dossier_recovery import TheClosedRecoverySet
from tools import dossier_command as d, instance
report={}
f=TheClosedRecoverySet();f.setUp()
try:
 for name in d.RETAINED:f.described.pop(name)
 f.rewrite();manifest,_=f.manifested()
 report["missing_required_roots"]={"real_instance_validator":instance.malformed(f.described,f.instance),"manifest_retained":manifest["retained"],"manifest_missing":manifest["missing_members"]}
 f.restore();shutil.rmtree(f.destination)
 for name in d.RETAINED:shutil.rmtree(Path(f.restored)/name)
 code,out,err=f.checked();report["restore_without_required_roots"]={"code":code,"faults":json.loads(out)["faults"]};assert code==0
finally:f.doCleanups()
f=TheClosedRecoverySet();f.setUp()
try:
 doc=instance.emit(f.destination,authority_uuid=f.described["authority_uuid"],identity=f.described["identity"],runtime=f.described["runtime"])
 # Place selected fixture bytes where the real emitter declares its members.
 for key in ("job_store","control_store","deployment"):
  target=Path(doc[key]);target.parent.mkdir(parents=True,exist_ok=True)
  if target!=Path(f.described[key]):shutil.copyfile(f.described[key],target)
 for key in d.RETAINED:
  if Path(doc[key])!=Path(f.described[key]):shutil.copytree(f.described[key],doc[key])
 Path(f.instance).write_text(json.dumps(doc))
 code,out,err=f.record("recovery-manifest","--instance",f.instance)
 report["real_instance_document"]={"validator":instance.malformed(doc,f.instance),"has_authority_store":"authority_store" in doc,"code":code,"missing_members":json.loads(out)["missing_members"],"error":err};assert code==2 and instance.malformed(doc,f.instance) is None
finally:f.doCleanups()
print(json.dumps(report,indent=2))
