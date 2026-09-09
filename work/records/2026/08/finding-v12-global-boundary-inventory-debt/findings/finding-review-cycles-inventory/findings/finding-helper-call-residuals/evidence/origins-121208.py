import ast
import hashlib
import json
import time
import traceback
from pathlib import Path

start = time.monotonic()
evidence = Path(__file__).resolve().parent
report = {}
try:
    from tests.manager import test_boundary_inventory as b
    trace = json.loads((evidence / "trace-121208.json").read_text())
    for name, sha in trace["hashes"].items():
        assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == sha, name
    tree = next(tree for path, tree in b._sources() if path.name == "review_cycles.py")
    functions = dict(b._functions(tree, "review_cycles.py"))
    returns = b._helper_returns()
    helpers = b._helpers(tree, "review_cycles.py")
    calls = []
    for site, node in functions.items():
        if site.split(":")[1] not in ("checkpoint_of", "create_line", "freeze_checkpoint", "record_verdict", "verdict_of", "integration_checkpoint"):
            continue
        origins = b._origins(node, site, returns)
        for call in b._scope_nodes(node):
            if not isinstance(call, ast.Call):
                continue
            text = ast.unparse(call.func)
            if text not in ("json.loads", "_evidence", "_review_result", "_profile", "_line_place", "_storage", "profile.materialize", "profile.freeze", "output.frozen_output_of"):
                continue
            for context in b._contexts_at(origins, call):
                calls.append({"site": site, "line": call.lineno, "call": ast.unparse(call), "result_origin": b._source(call, context, site, returns), "argument_origins": [b._source(arg, context, site, returns) for arg in call.args], "capability": sorted(b._discovered_capabilities(call, origins))})
    report["calls"] = calls
    profile_calls = []
    for site, node in functions.items():
        if site != "review_cycles.py:create_line":
            continue
        origins = b._origins(node, site, returns)
        for where, helper, inside in b._delegations(node, origins, helpers, site=site, returns=returns):
            if where == "review_cycles.py:_profile":
                profile_calls.append({"source": where, "unfiltered": sorted(b._calls_in(helper, inside, site, all_subjects=True)), "propagated_occurrences": [r._asdict() for r in b._boundary_calls(helper, inside, where, site, propagated=True)]})
    report["profile_helper"] = profile_calls
    # Diagnostic assertions bind actual losses, not a proposed replacement.
    decoded = [one for one in calls if one["site"] == "review_cycles.py:checkpoint_of" and one["call"] == "json.loads(taken['evidence'])"]
    assert decoded and all(one["result_origin"] is None and one["argument_origins"] == ["read:review_cycles.py:checkpoint_of|line_checkpoints[evidence]"] for one in decoded)
    assert profile_calls and all(one["unfiltered"] and not one["propagated_occurrences"] for one in profile_calls)
    materialized = [one for one in calls if one["call"].startswith("profile.materialize(")]
    assert materialized and all(one["result_origin"] is None and not one["capability"] for one in materialized)
    print(json.dumps(report, indent=2))
except BaseException:
    report["error"] = traceback.format_exc()
    raise
finally:
    report["seconds"] = time.monotonic() - start
    report["combined_seconds"] = report["seconds"] + trace["seconds"]
    with (evidence / "origins-121208.json").open("x") as out:
        json.dump(report, out, indent=2)
    print("Combined elapsed:", report["combined_seconds"])
