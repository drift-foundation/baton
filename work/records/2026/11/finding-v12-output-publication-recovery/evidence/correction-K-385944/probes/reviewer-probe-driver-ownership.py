import os,sys,subprocess,importlib.util,unittest,json
from pathlib import Path
p=Path('/home/sl/src/baton/work/scratch/w385695-K-385944/cli-in-image-driver.py')
spec=importlib.util.spec_from_file_location('reviewed_driver',p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Driver(unittest.TestCase):
 def test_survivor_cleanup_does_not_select_a_process_outside_the_driver(self):
  # We own this sentinel and reap it. Driver main/finally is NOT run: no broad kill occurs.
  child=subprocess.Popen(['sleep','303'])
  try:
   got=m.survivors(); print('FOREIGN_SELECTION',json.dumps({'sentinel':child.pid,'selected':child.pid in got,'driver_started':False}))
   self.assertNotIn(child.pid,got,'driver finally would SIGKILL this unrelated process without ownership proof')
  finally:child.terminate();child.wait(timeout=5)
if __name__=='__main__':unittest.main(verbosity=2)
