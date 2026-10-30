import json

R = "/home/sl/src/baton/work/records/2026/10/"
delta = json.load(open("/tmp/w325959-355012-delta.json"))["delta"]

d486 = json.load(open(R + "finding-v12-attempt-failure-diagnostics/evidence/review-354068/CANDIDATE.json"))
s486 = {f["path"]: f.get("sha256") or f.get("digest") for f in d486["files"]}
d485 = json.load(open(R + "finding-v12-serving-token-renewal/bootstrap-347778/CANDIDATE.json"))
s485 = {f["path"]: f["candidate_sha256"] for f in d485["paths"]}

PARENT_NATIVE = {
    "v12/python/src/baton_v12/job_manager/execution_limits.py",
    "v12/python/src/baton_v12/worker_manager/workspaces.py",
    "v12/python/tools/single_worker.py",
    "v12/python/tools/stage_execution.py",
    "v12/python/tests/job_manager/test_native_permission.py",
}
CHILD = {"v12/python/tests/job_manager/test_native_stop_restart.py"}
TOKENS = "v12/python/src/baton_v12/worker_manager/tokens.py"

out, counts = {}, {}
for path, facts in sorted(delta.items()):
    here = facts["candidate"]
    if path in CHILD:
        origin = "W354630 child, ACCEPTED bytes imported UNCHANGED"
    elif path == TOKENS:
        origin = ("W333485 supplier base 389ea0ff -> parent revoked-gate "
                  "correction c341c2a5 -> parent PROSE-ONLY correction "
                  "adb773a8 (AST with docstrings stripped is identical)")
    elif path in PARENT_NATIVE and path in s485 and s485[path] != here:
        origin = ("W333485 supplier, then CHANGED BY PARENT for the native "
                  f"lifetime (supplier had {s485[path][:16]})")
    elif path in PARENT_NATIVE:
        origin = "parent-owned native lifetime work"
    elif path in s486 and s486[path] == here:
        origin = "W333486 supplier, BYTE-IDENTICAL to the accepted candidate"
    elif path in s486:
        origin = ("W333486 supplier, THREE-WAY MERGED by parent at claim354165 "
                  f"(supplier had {s486[path][:16]})")
    elif path in s485 and s485[path] == here:
        origin = "W333485 supplier, BYTE-IDENTICAL to the accepted candidate"
    elif path in s485:
        origin = ("W333485 supplier, then changed by parent "
                  f"(supplier had {s485[path][:16]})")
    else:
        origin = "UNATTRIBUTED -- investigate"
    out[path] = {**facts, "origin": origin}
    key = origin.split(",")[0].split(" (")[0]
    counts[key] = counts.get(key, 0) + 1

print(json.dumps(counts, indent=1))
unattributed = [p for p, v in out.items() if v["origin"].startswith("UNATTRIB")]
print("UNATTRIBUTED:", unattributed)
json.dump({"schema": "baton.w325959-combined-delta/1",
           "base_commit": "d6881d8adbd567b6e92a4a2a1d0cb68ee781f70a",
           "suppliers": {
               "W333486": {"accepted": R + "finding-v12-attempt-failure-diagnostics/evidence/review-354068/CANDIDATE.json",
                           "base": d486["base"], "paths": len(s486)},
               "W333485": {"accepted": R + "finding-v12-serving-token-renewal/bootstrap-347778/CANDIDATE.json",
                           "base": d485.get("base"), "paths": len(s485)}},
           "delta_count": len(out), "by_origin": counts, "delta": out},
          open("/tmp/w325959-355012-DELTA.json", "w"), indent=1, sort_keys=True)
