import json, tempfile
from pathlib import Path
from unittest.mock import patch
from baton_v12.authority import Authority
from baton_v12.authority import store
UUID = "0123456789abcdef0123456789abcdef"
results = []
for case in ("only-wal", "only-shm", "serving-close-after-guard"):
    with tempfile.TemporaryDirectory(prefix="review-126983-") as root:
        path = str(Path(root) / "authority.sqlite3")
        serving = Authority.create(path, authority_uuid=UUID)
        if case != "serving-close-after-guard":
            serving.dispose()
            Path(path + ("-wal" if case == "only-wal" else "-shm")).touch()
        before = sorted(p.name for p in Path(root).iterdir())
        real_connect = store.sqlite3.connect
        def connect(*args, **kwargs):
            if case == "serving-close-after-guard":
                serving.dispose()
            return real_connect(*args, **kwargs)
        result = {"case": case, "before": before}
        try:
            with patch.object(store.sqlite3, "connect", side_effect=connect):
                reader = Authority.open_readonly(path, expected_authority_uuid=UUID)
            result["opened"] = reader.authority_uuid
            reader.dispose()
        except Exception as exc:
            result["exception"] = type(exc).__name__ + ": " + str(exc)
        result["after"] = sorted(p.name for p in Path(root).iterdir())
        result["sizes"] = {p.name: p.stat().st_size for p in Path(root).iterdir()}
        results.append(result)
print(json.dumps(results, indent=2))
