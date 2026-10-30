import sys,json,io,tempfile,os
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path.cwd()/'v12/python'),str(Path.cwd()/'v12/python/src')]
from tools import bootstrap as b
with tempfile.TemporaryDirectory(prefix='w376956-account-') as tmp:
 p=Path(tmp);own=p/'own';own.write_text('owned');foreign=p/'foreign';foreign.write_text('foreign');held=os.lstat(own);identity=(held.st_dev,held.st_ino)
 entries=[(str(own),identity,'copied object'),(str(foreign),identity,'replaced object'),(str(p/'uncertain'),b._UncertainPrerequisite('creation outcome unknown'),'uncertain object'),(str(p/'none'),None,'not attempted'),(str(p/'gone'),identity,'gone object')]
 with patch.object(b,'_remove_if_still_ours',side_effect=AssertionError('destructive helper reached')),patch.object(b.os,'unlink',side_effect=AssertionError('unlink reached')),patch.object(b.os,'rmdir',side_effect=AssertionError('rmdir reached')):
  u=b._Unwind().run(entries);s=io.StringIO();u.report(s)
 result={'retained':u.retained,'report':s.getvalue(),'own':own.read_text(),'foreign':foreign.read_text(),'destructive_calls':0}
print(json.dumps(result,indent=2))
