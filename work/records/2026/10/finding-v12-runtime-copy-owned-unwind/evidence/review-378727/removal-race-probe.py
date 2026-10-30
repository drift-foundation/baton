import os,sys,json,tempfile,time
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path.cwd()/'v12/python'),str(Path.cwd()/'v12/python/src')]
from tools import bootstrap as b
start=time.monotonic()
with tempfile.TemporaryDirectory(prefix='w376956-review-') as temporary:
    root=Path(temporary); src=root/'source'; src.mkdir(); (src/'a').write_text('owned a'); (src/'b').write_text('owned b'); dest=root/'dest'; made={}; b.copy_runtime(src,str(dest),made=made)
    unlink=os.unlink; injected=[]
    def replace_before_unlink(name,*args,**kw):
        if name=='a' and 'dir_fd' in kw and not injected:
            injected.append(True)
            os.rename(dest/'a',root/'original-a')
            (dest/'a').write_text('FOREIGN CONTENT')
        return unlink(name,*args,**kw)
    with patch.object(b.os,'unlink',side_effect=replace_before_unlink):
        answers=[b._remove_if_still_ours(str(dest/n),made[str(dest/n)],'runtime object') for n in ('a','b')]
    result={'injected':bool(injected),'foreign_replacement_survives':(dest/'a').exists(),'original_survives':(root/'original-a').exists(),'subsequent_owned_file_survives':(dest/'b').exists(),'answers':answers}
print(json.dumps({'seconds':time.monotonic()-start,'result':result},indent=2))
