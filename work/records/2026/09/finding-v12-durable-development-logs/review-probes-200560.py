import os,sys,tempfile,pathlib,json,hashlib,time
sys.path[:0]=['/home/sl/src/baton/v12/worker','/home/sl/src/baton/v12/python/src/baton_v12']
import claude_agent as a
import attempt_log_format as f
root=pathlib.Path(tempfile.mkdtemp(prefix='w198667-review200560-'))
results={}
start=time.monotonic()
for case in ['hardlink','reserved']:
 p=root/case; source=p/'scratch/home/.claude'; source.mkdir(parents=True); logs=p/'logs'; (logs/'native').mkdir(parents=True)
 name='s.jsonl' if case=='hardlink' else '.retention.json'
 (source/name).write_bytes(b'provider transcript')
 if case=='hardlink':
  outside=p/'sibling.log'; outside.write_bytes(b''); os.link(outside,logs/'native/s.jsonl')
  s=(source/name).stat(); (logs/'native/.retention.json').write_text(json.dumps({name:{'identity':[s.st_dev,s.st_ino],'destination':name,'retained':0,'head':''}}))
 fd=os.open(logs,os.O_RDONLY|os.O_DIRECTORY)
 try: answer=a._retain_native(str(p/'scratch'),fd,f)
 finally: os.close(fd)
 results[case]={'answer':answer,'native_files':{x.name:x.read_text() for x in (logs/'native').iterdir()},'outside':outside.read_text() if case=='hardlink' else None}
results['seconds']=time.monotonic()-start
results['root']=str(root)
print(json.dumps(results,indent=2))
(root/'results.json').write_text(json.dumps(results,indent=2))
