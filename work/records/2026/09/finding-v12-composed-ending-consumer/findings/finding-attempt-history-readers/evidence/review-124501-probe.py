"""Question: do new historical readers refuse malformed/correlated committed acts?
Budget: five seconds for review124501, including previous controls plus new result-field mutations; no inventory suite.
"""
import json,time,sqlite3,hashlib
from pathlib import Path
from unittest import mock
from tests.manager.test_review_cycles import HistoryIsReachableFromTheAttemptThatMadeIt as Case
from baton_v12.worker_manager import review_cycles as rc
from baton_v12.worker_manager import ControlStore
start=time.monotonic(); results={}
f=Case();f.setUp()
try:
    _,first,_,_=f.round(1,"changes-requested")
    f.round(2,"accepted",based=first["checkpoint_id"])
    readers={"writer":(rc.writer_for_attempt,"writer-attempt-1","writer_id",rc.GRANT_KIND),"review":(rc.review_for_attempt,"review-attempt-1","attachment_id",rc.ATTACH_KIND)}
    honest={k:fn(f.store,attempt_id=attempt,generation=1) for k,(fn,attempt,_,_) in readers.items()}
    def read(kind):
        fn,attempt,_,_=readers[kind]
        denied={sqlite3.SQLITE_INSERT,sqlite3.SQLITE_UPDATE,sqlite3.SQLITE_DELETE,sqlite3.SQLITE_TRANSACTION,sqlite3.SQLITE_SAVEPOINT}
        f.store._connection.set_authorizer(lambda action,*rest:sqlite3.SQLITE_DENY if action in denied else sqlite3.SQLITE_OK)
        try:
            answer=fn(f.store,attempt_id=attempt,generation=1)
            return {"returned":True,"equals_honest":answer==honest[kind]}
        except Exception as e:
            return {"exception":type(e).__name__,"category":getattr(e,"category",None),"message":str(e)}
        finally:f.store._connection.set_authorizer(None)
    for kind in readers:
        _,_,identity,opkind=readers[kind];op=opkind+":"+honest[kind][identity]
        record=f.store.operation_record(op)
        for name,column,value in [("malformed_signature","signature","{"),("null_result","result","null"),("foreign_result","result",json.dumps({"foreign":True}))]:
            f.store._connection.execute(f"UPDATE operations SET {column}=? WHERE operation_id=?",(value,op))
            results[kind+"_"+name]=read(kind)
            f.store._connection.execute(f"UPDATE operations SET {column}=? WHERE operation_id=?",(record[column],op))
        for name,field,value in [("null_result_state","state",None),("list_result_state","state",[]),("revoked_result_state","state","revoked")]+([("bool_result_generation","generation",True)] if kind=="writer" else []):
            changed=json.loads(record["result"]);changed[field]=value
            f.store._connection.execute("UPDATE operations SET result=? WHERE operation_id=?",(json.dumps(changed),op))
            results[kind+"_"+name]=read(kind)
            f.store._connection.execute("UPDATE operations SET result=? WHERE operation_id=?",(record["result"],op))
        signature=json.loads(record["signature"])
        signature["operands"]["generation"]=True
        f.store._connection.execute("UPDATE operations SET signature=? WHERE operation_id=?",(json.dumps(signature),op))
        results[kind+"_bool_committed_generation"]=read(kind)
        f.store._connection.execute("UPDATE operations SET signature=? WHERE operation_id=?",(record["signature"],op))
    record=f.store._connection.execute("SELECT assignment_generation FROM attempts WHERE runtime_attempt_id='writer-attempt-1'").fetchone()
    f.store._connection.execute("UPDATE attempts SET assignment_generation=99 WHERE runtime_attempt_id='writer-attempt-1'")
    results["writer_changed_fixed_generation"]=read("writer")
    f.store._connection.execute("UPDATE attempts SET assignment_generation=? WHERE runtime_attempt_id='writer-attempt-1'",(record[0],))
    f.store.close();f.store=ControlStore.open(f.control_path,incarnation="independent-reopen",clock=lambda: "2026-09-09T03:00:00.000Z")
    with mock.patch.object(rc,"_profile",side_effect=AssertionError("profile access forbidden")),mock.patch.object(rc,"_validate_line_object",side_effect=AssertionError("physical access forbidden")):
        results["writer_cold_earlier_round"]=read("writer")
        results["review_cold_earlier_round"]=read("review")
finally:
    f.tearDown();f.doCleanups()
    out={"work":"W124331","claim":124501,"seconds":time.monotonic()-start,"results":results,"sha256":{}}
    for rel in ("src/baton_v12/worker_manager/review_cycles.py","tests/manager/test_review_cycles.py"):
        out["sha256"][rel]=hashlib.sha256((Path("v12/python")/rel).read_bytes()).hexdigest()
    Path(__file__).with_suffix(".json").write_text(json.dumps(out,indent=2)+"\n");print(json.dumps(out,indent=2))
