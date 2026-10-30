import sys, json, io, contextlib, time
from pathlib import Path
from unittest.mock import patch
root=Path.cwd()
sys.path[:0]=[str(root/'v12/worker'),str(root/'v12/python/src'),str(root/'v12/python/src/baton_v12')]
import baton_worker as w
import dogfood_entry as entry
from baton_v12.worker_manager import launch, exchange
valid=launch.launch_document(session='session-one',contract='c',role='implementation',transport=exchange.EXCHANGE_TRANSPORT)
variants={'unwrapped':launch.payload_of(valid),'wrong_profile':dict(valid,wire_profile='unsupported'),'unknown_outer_member':dict(valid,unexpected=True)}
results={}; start=time.monotonic()
for name,document in variants.items():
    built=[]
    def construct():
        built.append('constructed')
        raise AssertionError('must not construct')
    direct_error=io.StringIO()
    with patch.object(w,'read_launch',return_value=document):
        direct=w.serve(io.BytesIO(),io.BytesIO(),None,stderr=direct_error)
    entry_error=io.StringIO(); capture=[]
    with patch.object(w,'read_launch',return_value=document), patch.object(w,'_WorkerCapture',side_effect=lambda: capture.append('entered')), contextlib.redirect_stderr(entry_error):
        production=entry._production(build=construct)
    results[name]={'serve_exit':direct,'serve_stderr':direct_error.getvalue(),'production_exit':production,'production_stderr':entry_error.getvalue(),'adapter_constructions':built,'worker_capture_entries':capture}
print(json.dumps({'seconds':time.monotonic()-start,'results':results},indent=2))
