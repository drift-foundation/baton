import io,json
from pathlib import Path
from tests.tools.test_pool import ComposingAWorkerForThisInstance
from tools import pool
f=ComposingAWorkerForThisInstance('test_the_command_line_writes_one_fresh_file_and_refuses_a_second')
f.setUp()
try:
    target=Path(f.root)/'new-worker.json'
    outside=Path(f.root)/'elsewhere.json'
    target.symlink_to(outside)
    result=pool.compose(f.place,f.candidate(),into=str(target),stream=io.StringIO(),worker_id='impl-c',role='implementation',participant='baton.impl-c',image_digest=f.IMAGE,task_document=f.task_file())
    print(json.dumps({'existing_symlink_preserved':target.is_symlink(),'followed_symlink_and_created_target':outside.exists(),'returned_success':bool(result)}))
finally:
    f.tearDown()
    f.doCleanups()
