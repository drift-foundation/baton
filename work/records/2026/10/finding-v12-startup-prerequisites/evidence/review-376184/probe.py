import tempfile,pathlib,io,json,os
from unittest.mock import patch
from tools import bootstrap as b
out={}
def doc(p):return {"workers":[{"worker_id":"probe","deployment":{"workspace_storage":str(p)}}]}
with tempfile.TemporaryDirectory() as tmp:
 base=pathlib.Path(tmp);root=base/"raced";made={}
 def race(place):
  pathlib.Path(place).write_text("foreign")
  raise FileExistsError(place)
 with patch.object(b.os,"makedirs",side_effect=race):
  b.prepare_prerequisites(doc(root),{},made=made,stream=io.StringIO())
 out["raced_file"]={"returned_success":True,"foreign_bytes":root.read_text(),"owned":made}
 parent=base/"nested";root=parent/"root";made={}
 b.prepare_prerequisites(doc(root),{},made=made,stream=io.StringIO())
 for place,identity in made.items(): b._remove_if_still_ours(place,identity,"probe")
 out["intermediate"]={"parent_left":parent.exists(),"root_left":root.exists(),"tracked":list(made)}
 foreign=base/"foreign";foreign.mkdir();link=base/"link";link.symlink_to(foreign,target_is_directory=True);(foreign/"root").mkdir()
 out["report_link_ancestor"]=b.prerequisite_report(doc(link/"root"))
 root=base/"mode";made={};old=os.umask(0)
 try:b.prepare_prerequisites(doc(root),{},made=made,stream=io.StringIO())
 finally:os.umask(old)
 out["new_root_mode_under_umask_zero"]=oct(root.stat().st_mode & 0o777)
 (root/"foreign-child").write_text("foreign")
 b._remove_if_still_ours(str(root),made[str(root)],"probe")
 out["foreign_child_survives_cleanup"]=(root/"foreign-child").exists()
print(json.dumps(out,indent=2))
