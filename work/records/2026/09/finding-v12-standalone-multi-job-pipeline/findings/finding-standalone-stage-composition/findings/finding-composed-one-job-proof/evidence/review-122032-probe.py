"""Question: does cold composed mount recover the real cleaned ending?
Budget: one real local component fixture, five seconds. No assembled rerun.
"""
import json,time,hashlib
from pathlib import Path
from unittest import mock
from tests.tools.test_stage_execution import ComposedOneJobCase, stage_execution
from baton_v12.worker_manager import attempt_runtime_of
started=time.monotonic()
fixture=ComposedOneJobCase()
result={"work":"W119114","claim":122032,"question":__doc__,"results":{}}
try:
    fixture.setUp()
    held=fixture.implemented()
    worker=fixture.worker_of(held.composed,"implementation")
    composition=worker.stage
    original=composition._prepared[held.attempt_id]
    result["results"]["ordinary_cleanup"]=attempt_runtime_of(held.control,held.attempt_id)
    composition._prepared.clear()
    recovered=composition._prepare(held.attempt_id)
    result["results"]["cold_preparation"]={"same_writer":recovered["writer_id"]==original["writer_id"],"boundary":recovered["boundary"]}
    try:
        worker._mounted({"attempt_id":held.attempt_id},held.attempt_id,checkpoint=False)
    except Exception as e:
        result["results"]["cold_mounted"]={"exception":type(e).__name__,"message":str(e)}
    else:
        result["results"]["cold_mounted"]={"unexpected":"succeeded"}
    composition._prepared.clear()
    line=dict(composition.deployment.line(),current_checkpoint_id=None)
    with mock.patch.object(composition.deployment,"line",return_value=line), mock.patch.object(stage_execution.review_driver,"prepare_implementation",side_effect=AssertionError("attempted a new writer preparation")):
        try:
            composition._prepare(held.attempt_id)
        except Exception as e:
            result["results"]["current_pointer_absent"]={"exception":type(e).__name__,"message":str(e)}
    composition._prepared.clear()
    state=dict(attempt_runtime_of(held.control,held.attempt_id),execution_runtime="quiescent")
    with mock.patch.object(stage_execution,"attempt_runtime_of",return_value=state), mock.patch.object(stage_execution.review_driver,"prepare_implementation",side_effect=AssertionError("attempted a new writer preparation")):
        try:
            composition._prepare(held.attempt_id)
        except Exception as e:
            result["results"]["frozen_before_cleanup_branch"]={"exception":type(e).__name__,"message":str(e)}
finally:
    fixture.doCleanups()
    result["seconds"]=time.monotonic()-started
    for rel in ("tools/stage_execution.py","tests/tools/test_stage_execution.py"):
        result.setdefault("sha256",{})[rel]=hashlib.sha256((Path("v12/python")/rel).read_bytes()).hexdigest()
    Path(__file__).with_suffix(".json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2))
