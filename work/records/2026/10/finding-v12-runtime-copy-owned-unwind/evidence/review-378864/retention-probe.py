import sys,os,json,io,tempfile,hashlib
from pathlib import Path
from unittest.mock import patch
root=Path.cwd();sys.path[:0]=[str(root/'v12/python'),str(root/'v12/python/src')]
from tools import bootstrap as b
results={}
for retain in (False,True):
 with tempfile.TemporaryDirectory(prefix='w376956-retain-') as temp:
  root=Path(temp); place=root/'justfile';place.write_text('owned'); fd=os.open(place,os.O_PATH|os.O_NOFOLLOW); identity=b._OwnedPrerequisite(b._identity_of_handle(fd),fd);os.close(fd); unlink=os.unlink;calls=[]
  def race(name,*args,**kw):
   if name=='justfile' and 'dir_fd' in kw:
    calls.append(name);os.rename(place,root/'original');place.write_text('FOREIGN')
   return unlink(name,*args,**kw)
  with patch.object(b.os,'unlink',side_effect=race):
   u=b._Unwind().run([(str(place),identity,'justfile',retain)])
  out=io.StringIO();u.report(out)
  results[str(retain)]={'unlink_calls':calls,'path_survives':place.exists(),'original_survives':(root/'original').exists(),'report':out.getvalue()}
print(json.dumps(results,indent=2))
