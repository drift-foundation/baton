import os, sys, tempfile, subprocess, json, hashlib
from pathlib import Path
from baton_v12.authority import Authority, Refusal
UUID="0123456789abcdef0123456789abcdef"
OTHER="fedcba9876543210fedcba9876543210"
WORK="0000000a-W1"
if len(sys.argv)>1:
    serving=Authority.create(sys.argv[1],authority_uuid=UUID)
    serving.create_work(WORK,"baton.impl",operation_id="op-wal")
    os._exit(0)
with tempfile.TemporaryDirectory(prefix="review-128304-") as root:
    path=str(Path(root)/"authority.sqlite3")
    subprocess.run([sys.executable,__file__,path],check=True,timeout=0.5)
    def snapshot():
        return {s:hashlib.sha256(Path(path+s).read_bytes()).hexdigest() for s in ("","-wal")}
    before=snapshot()
    assert Path(path+"-wal").stat().st_size>0
    try:
        Authority.open_readonly(path,expected_authority_uuid=OTHER)
    except Refusal:
        pass
    else:
        raise AssertionError("wrong UUID opened")
    reading=Authority.open_readonly(path,expected_authority_uuid=UUID)
    try:
        assert reading.project_work(WORK)["status"]=="open"
        record=reading.operation_result("op-wal")
        assert record is not None
        try:
            reading.create_work("0000000a-W2","baton.impl",operation_id="op-forbidden")
        except Refusal:
            pass
        else:
            raise AssertionError("mutation succeeded")
        assert reading.operation_result("op-forbidden") is None
    finally:
        reading.dispose()
    assert snapshot()==before
    print(json.dumps({"committed_wal_read":True,"operation_result_read":True,"uuid_refusal":True,"mutation_refused_without_record":True,"main_and_wal_bytes_unchanged":True},indent=2))
