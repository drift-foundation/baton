import tempfile,pathlib,io,json,os
from unittest.mock import patch
from tools import bootstrap as b
out={}
def doc(p):return {"workers":[{"worker_id":"probe","deployment":{"workspace_storage":str(p)}}]}
with tempfile.TemporaryDirectory() as tmp:
 base=pathlib.Path(tmp);root=base/"root";foreign=base/"foreign";foreign.mkdir(mode=0o755);identity=(foreign.stat().st_dev,foreign.stat().st_ino);made={};mkdir=os.mkdir
 def swap(place,mode):
  mkdir(place,mode);os.rmdir(place);os.rename(foreign,place)
 with patch.object(b.os,"mkdir",side_effect=swap):
  b.prepare_prerequisites(doc(root),{},made=made,stream=io.StringIO())
 out["ordinary_directory_replacement"]={"returned_success":True,"foreign_mode_after":oct(root.stat().st_mode & 0o777),"foreign_identity_adopted":made[str(root)]==identity}
 root2=base/"unopened";made={}
 with patch.object(b.os,"open",side_effect=PermissionError("injected open refusal")):
  try:b.prepare_prerequisites(doc(root2),{},made=made,stream=io.StringIO())
  except b.BootstrapRefusal as err:out["open_refusal"]={"message":str(err),"created_root_left":root2.exists(),"owned":made}
print(json.dumps(out,indent=2))
