from pathlib import Path
import json,os,subprocess,time,sys
repo=Path('/home/sl/src/baton'); scratch=repo/'work/scratch/w385517-385529'; cwd=scratch/'candidate/v12/python'; evidence=Path(__file__).resolve().parent
name=sys.argv[1]; ids=sys.argv[2:]
env=dict(os.environ,TMPDIR=str(scratch/'tmp'),BATON_V12_DISK_ROOT=str(scratch/'tmp'),BATON_V12_STACK_TEST_ROOT=str(scratch/'tmp'),GIT_CEILING_DIRECTORIES=str(scratch),PYTHONDONTWRITEBYTECODE='1')
argv=['just','test-one',*ids]
start=time.monotonic()
with (evidence/(name+'.log')).open('w') as f:
 result=subprocess.run(argv,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=240)
record={'argv':argv,'cwd':str(cwd),'seconds':time.monotonic()-start,'returncode':result.returncode}
(evidence/(name+'.json')).write_text(json.dumps(record,indent=2)+'\n'); print(json.dumps(record))
