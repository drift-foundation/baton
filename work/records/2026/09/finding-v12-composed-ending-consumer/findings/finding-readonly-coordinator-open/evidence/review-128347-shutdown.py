import sys, subprocess, tempfile, json, hashlib
from pathlib import Path
from unittest.mock import patch
from baton_v12.integration import IntegrationStore, target_of
from tests.integration.fixtures import TARGET
from baton_v12.integration import store
from baton_v12.contracts import ContractRefusal
NOW="2026-09-05T00:00:00.000Z"
if len(sys.argv)>1:
    from baton_v12.integration import activate_target
    from tests.integration.fixtures import target
    serving=IntegrationStore.open(sys.argv[1],incarnation="serving",clock=lambda:NOW)
    activate_target(serving,target())
    print("ready",flush=True)
    sys.stdin.readline()
    serving.close()
    sys.exit(0)
with tempfile.TemporaryDirectory(prefix="review-127103-") as root:
    path=str(Path(root)/"coordinator.sqlite3")
    child=subprocess.Popen([sys.executable,__file__,path],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert child.stdout.readline().strip()=="ready"
        result={"before":sorted(p.name for p in Path(root).iterdir())}
        real_connect=store.sqlite3.connect
        def connect(*args,**kwargs):
            if child.poll() is None:
                child.stdin.write("close\n");child.stdin.flush()
                child.wait(timeout=0.5)
            result.setdefault("after_serving_exit", sorted(p.name for p in Path(root).iterdir()))
            result.setdefault("database_after_exit", hashlib.sha256(Path(path).read_bytes()).hexdigest())
            return real_connect(*args,**kwargs)
        try:
            with patch.object(store.sqlite3,"connect",side_effect=connect):
                reader=IntegrationStore.open_readonly(path,incarnation="reader",clock=lambda:NOW)
            result["opened"]=True
            assert target_of(reader,TARGET)["canonical_target_id"]==TARGET
            result["committed_target_read"]=True
            reader.close()
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==result["database_after_exit"]
            result["database_unchanged"]=True
        except Exception as exc:
            result["exception"]=type(exc).__name__+": "+str(exc)
            result["contract_refusal"]=isinstance(exc,ContractRefusal)
        result["after_open"]={p.name:p.stat().st_size for p in Path(root).iterdir()}
        assert result.get("opened") and result.get("committed_target_read") and result.get("database_unchanged"), result
        print(json.dumps(result,indent=2))
    finally:
        if child.poll() is None:
            child.kill();child.wait()
        child.stdin.close();child.stdout.close();child.stderr.close()
