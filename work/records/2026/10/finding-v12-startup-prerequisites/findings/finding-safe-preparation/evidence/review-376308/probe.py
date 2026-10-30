import tempfile,pathlib,io,json,os
from unittest.mock import patch
from tools import bootstrap as b
out={}
def doc(p):return {"workers":[{"worker_id":"probe","deployment":{"workspace_storage":str(p)}}]}
with tempfile.TemporaryDirectory() as tmp:
 base=pathlib.Path(tmp);root=base/"raced";made={};original=b._components
 def race_components(place):
  pathlib.Path(place).write_text("foreign")
  return original(place)
 with patch.object(b,"_components",side_effect=race_components):
  b.prepare_prerequisites(doc(root),{},made=made,stream=io.StringIO())
 out["between_precheck_and_components"]={"success":True,"kind":"file","owned":made}
 root=base/"replaced";target=base/"foreign";target.mkdir(mode=0o755);before=target.stat().st_mode & 0o777;made={};mkdir=os.mkdir
 def swap(place,mode):
  mkdir(place,mode);os.rmdir(place);os.symlink(target,place)
 with patch.object(b.os,"mkdir",side_effect=swap):
  b.prepare_prerequisites(doc(root),{},made=made,stream=io.StringIO())
 out["replacement_chmod"]={"success":True,"foreign_mode_before":oct(before),"foreign_mode_after":oct(target.stat().st_mode & 0o777),"replacement_link_recorded_owned":str(root) in made}
 root=base/"failed_chmod";made={}
 with patch.object(b.os,"chmod",side_effect=PermissionError("probe")):
  b.prepare_prerequisites(doc(root),{},made=made,stream=io.StringIO())
 out["postcreate_error"]={"success":True,"created_root_left":root.exists(),"owned":made}
print(json.dumps(out,indent=2))
