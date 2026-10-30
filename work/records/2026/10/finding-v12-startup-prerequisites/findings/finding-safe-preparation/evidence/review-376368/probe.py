import tempfile,pathlib,shutil,json,os
from tools import bootstrap as b
with tempfile.TemporaryDirectory() as tmp:
 base=pathlib.Path(tmp);source=base/"source";source.mkdir();(source/"owned").write_text("runtime")
 target=base/"runtime";shutil.copytree(source,target);held=target.stat();identity=(held.st_dev,held.st_ino)
 (target/"foreign-later").write_text("not copied by this install")
 result=b._remove_if_still_ours(str(target),identity,"runtime",whole=True)
 print(json.dumps({"cleanup":result,"foreign_file_survives":(target/"foreign-later").exists(),"root_survives":target.exists()}))
