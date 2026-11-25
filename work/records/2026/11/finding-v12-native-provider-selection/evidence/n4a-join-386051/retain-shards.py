from pathlib import Path
import json,os,time,shutil
E=Path(__file__).resolve().parent
active=['manager-pure','tools-pure']
while active:
 for group in active[:]:
  root=Path('/var/tmp')/('baton-n4a-386051-'+group)
  dest=E/'isolated-shards'/group;dest.mkdir(parents=True,exist_ok=True)
  for path in root.glob('v12-parallel-test-*/*.report.json'):
   try:
    data=path.read_bytes();json.loads(data)
    (dest/(path.parent.name+'-'+path.name)).write_bytes(data)
   except (OSError,ValueError):pass
  if (E/(group+'.summary.json')).exists(): active.remove(group)
 time.sleep(.25)
