"""Read-only prelaunch input check. Opens no store, submits no Job, starts no
engine or provider, and writes nothing.

Running this is how a reviewer confirms that every digest this packet binds is
still the bytes on disk -- the preserved buffers, the declared base's own files,
the selected deployment artifacts and the load command the task carries.
"""
import importlib.util
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('packet_prepare', HERE / 'prepare.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
doc = module.pins()
print(json.dumps({'state': 'prelaunch-input-pins-match', 'base': module.BASE,
                  'run': module.RUN, 'manager_files': len(doc['manager_files']),
                  'task_inputs': len(doc['task_inputs']),
                  'verification_names': len(module.GATE)}, sort_keys=True))
