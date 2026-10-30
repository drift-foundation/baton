import sys,json,tempfile,os,time
from pathlib import Path
from unittest.mock import patch
sys.path[:0]=[str(Path.cwd()/'v12/python'),str(Path.cwd()/'v12/python/src')]
from tools import bootstrap as b
results={}; start=time.monotonic()
with tempfile.TemporaryDirectory(prefix='w376956-review-') as temporary:
    root=Path(temporary); src=root/'source'; src.mkdir(); (src/'link').symlink_to('original-target'); dest=root/'dest'; made={}; symlink=os.symlink
    def replace_link(target,name,**kw):
        symlink(target,name,**kw)
        if name=='link':
            os.unlink(name,dir_fd=kw['dir_fd'])
            symlink('FOREIGN-TARGET',name,**kw)
    with patch.object(b.os,'symlink',side_effect=replace_link):
        b.copy_runtime(src,str(dest),made=made)
    link=str(dest/'link'); before=os.readlink(link); outcome=b._remove_if_still_ours(link,made[link],'copied runtime object')
    results['replacement_between_symlink_and_lstat']={'target_before_unwind':before,'ledger_type':type(made[link]).__name__,'outcome':outcome,'foreign_link_survives':os.path.lexists(link)}
with tempfile.TemporaryDirectory(prefix='w376956-review-') as temporary:
    root=Path(temporary); src=root/'source'; src.mkdir(); (src/'file').write_text('same bytes'); dest=root/'dest'; made={}; b.copy_runtime(src,str(dest),made=made)
    path=str(dest/'file'); moved=root/'original'; lstat=os.lstat; fired=[]
    def replace_after_stat(name,*args,**kw):
        result=lstat(name,*args,**kw)
        if str(name)==path and not fired:
            fired.append(True); os.rename(path,moved); Path(path).write_text('same bytes')
        return result
    with patch.object(b.os,'lstat',side_effect=replace_after_stat):
        outcome=b._remove_if_still_ours(path,made[path],'copied runtime object')
    results['replacement_after_identity_check']={'injected':bool(fired),'outcome':outcome,'foreign_replacement_survives':os.path.lexists(path),'original_retained':moved.exists()}
print(json.dumps({'seconds':time.monotonic()-start,'results':results},indent=2))
