"""Cumulative-record invalid-type containment; synthetic local room only."""
import sys,os,json,pathlib,tempfile,time
sys.path[:0]=['/home/sl/src/baton/v12/worker','/home/sl/src/baton/v12/python/src/baton_v12']
import claude_agent as a
import attempt_log_format as f
root=pathlib.Path(tempfile.mkdtemp(prefix='w198667-review201318-'));results={};start=time.monotonic()
for name,value in [('list',[]),('object',{}),('string','failed')]:
 room=root/name;room.mkdir();(room/f.carried_name('provider.stdout')).write_text(json.dumps({'declared':value}))
 fd=f.open_room(room)
 try:
  c=a._Captured(fd,f,'provider.stdout');c.wrote(b'output');c.declare('finished');results[name]={'declared':f.read_declaration(fd,'provider.stdout')}
 except Exception as e:results[name]={'exception':type(e).__name__,'message':str(e)}
 finally:os.close(fd)
results['seconds']=time.monotonic()-start;results['scratch']=str(root)
(root/'results.json').write_text(json.dumps(results,indent=2)+'\n');print(json.dumps(results,indent=2))
