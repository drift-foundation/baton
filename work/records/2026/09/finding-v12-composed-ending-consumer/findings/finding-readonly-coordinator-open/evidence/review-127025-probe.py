import json, tempfile
from pathlib import Path
from unittest.mock import patch
from baton_v12.integration.store import IntegrationStore
from baton_v12.integration import store
from baton_v12.contracts import ContractRefusal
NOW = "2026-09-05T00:00:00.000Z"
results = []
for case in ("only-wal", "only-shm", "serving-close-after-guard", "not-database"):
    with tempfile.TemporaryDirectory(prefix="review-127025-") as root:
        path = str(Path(root) / "coordinator.sqlite3")
        if case == "not-database":
            Path(path).write_bytes(b"this is not a database\n")
        else:
            serving = IntegrationStore.open(path, incarnation="serving", clock=lambda: NOW)
            if case != "serving-close-after-guard":
                serving.close()
                Path(path + ("-wal" if case == "only-wal" else "-shm")).touch()
        before = sorted(p.name for p in Path(root).iterdir())
        real_connect = store.sqlite3.connect
        result = {"case": case, "before": before}
        def connect(*args, **kwargs):
            if case == "serving-close-after-guard":
                serving.close()
                result["after_serving_close_before_connect"] = sorted(p.name for p in Path(root).iterdir())
            return real_connect(*args, **kwargs)
        try:
            with patch.object(store.sqlite3, "connect", side_effect=connect):
                reader = IntegrationStore.open_readonly(path, incarnation="reader", clock=lambda: NOW)
            result["opened"] = True
            reader.close()
        except Exception as exc:
            result["exception"] = type(exc).__name__ + ": " + str(exc)
            result["contract_refusal"] = isinstance(exc, ContractRefusal)
        result["after"] = sorted(p.name for p in Path(root).iterdir())
        result["sizes"] = {p.name: p.stat().st_size for p in Path(root).iterdir()}
        results.append(result)
print(json.dumps(results, indent=2))
