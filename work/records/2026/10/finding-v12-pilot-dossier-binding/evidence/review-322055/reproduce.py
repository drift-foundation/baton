import hashlib,json,os,shutil,tempfile
from pathlib import Path
from unittest.mock import patch
from tools import dossier_command as d
from tests.tools.test_dossier_recovery import TheClosedRecoverySet
report={}
with tempfile.TemporaryDirectory(prefix="w322055-") as tmp:
 root=Path(tmp)/"root";root.mkdir();(root/"a").mkdir();(root/"a/f").write_text("inside")
 outside=Path(tmp)/"outside";outside.mkdir();(outside/"f").write_text("outside")
 real_open=os.open
 def swapped(path,flags,*args,**kwargs):
  if str(path)==str(root/"a/f"):
   (root/"a").rename(root/"old-a");(root/"a").symlink_to(outside,target_is_directory=True)
  return real_open(path,flags,*args,**kwargs)
 with patch.object(d.os,"open",side_effect=swapped): result=d._contained_read(str(root),"a/f")
 report["intermediate_replacement"]={"state":result[0],"digest":result[1],"outside_digest":"sha256:"+hashlib.sha256(b"outside").hexdigest()}
 assert result[0]=="present" and result[1]==report["intermediate_replacement"]["outside_digest"]
f=TheClosedRecoverySet();f.setUp()
try:
 manifest,_=f.manifested();f.restore();shutil.rmtree(f.destination)
 manifest.pop("retained");Path(f.manifest).write_text(json.dumps(manifest))
 for name in d.RETAINED:shutil.rmtree(Path(f.restored)/name)
 code,out,err=f.checked();report["missing_retained"]={"code":code,"answer":json.loads(out),"error":err};assert code==0
finally:f.doCleanups()
print(json.dumps(report,indent=2))
