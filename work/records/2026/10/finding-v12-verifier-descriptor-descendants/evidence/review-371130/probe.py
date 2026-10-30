import json,os,tempfile
from pathlib import Path
from unittest.mock import patch
from tests.manager.test_claude_agent import TheVerifierRootsReachDescendants,claude_agent
c=TheVerifierRootsReachDescendants();c.setUp()
try:
 held,scratch,env=c.roots()
 with tempfile.TemporaryDirectory(prefix='w325695-review-table-') as root:
  table=Path(root)/'mountinfo'
  names=['HOME','TMPDIR','XDG_CACHE_HOME','PYTHONPYCACHEPREFIX']
  # Deliberately incompatible simulated mounts: ext4 and rw, no required options.
  table.write_text(''.join(f'{100+i} 1 8:1 / {env[n]} rw - ext4 /dev/fake rw\n' for i,n in enumerate(names)))
  with patch.object(claude_agent.ClaudeAgent,'MOUNTINFO',str(table)):
   pinned,fds=held._pinned_environment(scratch,env)
   try:
    assert all(pinned[n]==env[n] for n in names)
    print(json.dumps({'accepted_without_explicit_layout_selection':True,'accepted_simulated_wrong_filesystem_and_options':True,'roots_are_under_mutable_test_scratch':True,'kind':'source admission counterexample with simulated mount table, not real kernel proof'}))
   finally:
    for _,fd in fds:os.close(fd)
finally:c.doCleanups()
