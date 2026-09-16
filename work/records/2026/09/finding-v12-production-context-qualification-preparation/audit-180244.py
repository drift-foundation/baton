"""Read only published evidence and accepted source; no fixture imports or runs."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
expected = {
    "qualification-fixture.py": "72875394cb4b958919db48a019a99de076ee5cab526b51a1c2278ae0c7e49e94",
    "qualification_contract.py": "0efe61f528ce4c691b85fa336967d1f85bd32241ffd686c73305f7d36e3281d1",
    "qualification_worker.py": "6d9d0a0b5260b4e180a18672c58ae5ec7274bf0f3170a3b62f140bf2f1c92a28",
    "test_qualification.py": "108a7b67474e427ff4e76b635811e73ceb0487a692de88ac8ab69f7866ba0f22",
    "qualification-manifest.json": "5e789f4e3115b5eb9a7623772adf0a17aac3e45135afaa65bc11a35eb30e951f",
    "verify-offline.py": "bc579ae14bb9ef6d369af5bc0cee2c87b1e33d3e0b04069535acb9e0253cd3d8",
    "OPERATOR-178579.md": "fe63a4f11a3a3b7ea480d70e2a72793ed8f90cc9fab1bee62214ede80c4d6589",
}
checks = []
for parent in ("evidence", "candidate-180078"):
    for name, digest in expected.items():
        path = root / name if parent == "evidence" and name == "OPERATOR-178579.md" else root / parent / name
        actual = hashlib.sha256(path.read_bytes()).hexdigest()
        checks.append({"path": str(path.relative_to(root)), "sha256": actual, "matches": actual == digest})
public = root / "operator-result-2026-09-15T18-29-34Z"
for name, digest in {
    "qualification.json": "7cdfea126a0f80654fa569c8e7964ec5a0810712f096cca0e374c178578ea981",
    "PROVENANCE.json": "b6dcdcc92a5d06398f4d69b248f0ad3d3e43e94ec39634d4566a63643803aa51",
}.items():
    path = public / name
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    checks.append({"path": str(path.relative_to(root)), "sha256": actual, "matches": actual == digest})
provenance = json.loads((public / "PROVENANCE.json").read_bytes())
result = {
    "claim": 180244,
    "method": "read-only public-evidence and source-byte inventory; no fixture imports, tests, private paths or engine operations",
    "checks": checks,
    "all_match": all(row["matches"] for row in checks),
    "provenance_manifest_matches": provenance["fixture_manifest_sha256"] == expected["qualification-manifest.json"],
    "provenance_qualification_matches": provenance["qualification_sha256"] == checks[-2]["sha256"],
    "new_test_runtime_seconds": 0,
    "reviewer_cumulative_test_runtime_seconds": 1.969647156976862,
}
print(json.dumps(result, indent=2, sort_keys=True))
