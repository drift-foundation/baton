"""Independent application and partition audit; no suite or runtime execution."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import stat

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
PROPOSAL = HERE.parent.parent / "finding-declaration-accounting-proposal/evidence"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text())
packet = read(HERE / "handoff-hashes.json")
assert sha(HERE / "handoff-hashes.json") == "dfb793939bd76bea93e8bc10a84ca517c00ed89d68248449a63b12e512077982"
for name, expected in packet["hashes"].items():
    assert sha(ROOT / name) == expected, name
source = ROOT / packet["product_target"]
assert not source.is_symlink() and stat.S_ISREG(source.lstat().st_mode)
assert stat.S_IMODE(source.stat().st_mode) == 0o644
assert source.read_bytes() == (PROPOSAL / "candidate.py").read_bytes()
proposal_packet = read(PROPOSAL / "packet-hashes.json")
for name, expected in proposal_packet["runtime_hashes_unchanged"].items():
    assert sha(ROOT / name) == expected, name
base, candidate = ast.parse((HERE / "base.py").read_text()), ast.parse(source.read_text())
def functions(tree):
    result = {}
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            result[node.name] = ast.dump(node)
        if isinstance(node, ast.ClassDef):
            for method in node.body:
                if isinstance(method, ast.FunctionDef):
                    result[node.name + "." + method.name] = ast.dump(method)
    return result
old, new = functions(base), functions(candidate)
changed = [name for name, value in old.items() if new.get(name) != value]
assert changed == ["EveryReceivingEntryHasOneOwner.test_every_boundary_call_belongs_to_an_entry_or_is_declared"]
research = read(PROPOSAL / "research.json")
live = read(HERE / "live-accounting.json")
assert live["orphan_rows"] == research["candidate_orphan_rows"]
assert live["residuals"] == research["residuals"]
assert live["resolved"] == research["resolved"]
residuals = {tuple(row) for row in live["orphan_rows"]}
assert len(residuals) == len(live["orphan_rows"]) == 77
assert len(live["residuals"]) == live["residual_occurrences"] == 79
assignments = live["residual_assignments"]
assert Counter(tuple(a["row"]) for a in assignments) == Counter({r:1 for r in residuals})
deltas = read(HERE / "module-deltas.json")
assert len(deltas) == 10
by_module = {d["module"]:d for d in deltas}
removed, added = [], []
for d in deltas:
    folder = ROOT / d["dossier"]
    original = read(folder / "evidence/inputs.json")
    assert sha(folder / "evidence/inputs.json") == d["prior_inputs_sha256"]
    assert read(folder / "evidence/declaration-accounting-119093.json") == d
    old_rows = {tuple(r) for r in original["orphan_calls"]}
    new_rows = {r for r in residuals if r[0].split(".py:")[0] == d["module"]}
    assert old_rows == {tuple(r) for r in d["prior_orphan_calls"]}
    assert new_rows == {tuple(r) for r in d["current_orphan_calls"]}
    assert new_rows-old_rows == {tuple(r) for r in d["added_rows"]}
    assert old_rows-new_rows == {tuple(r) for r in d["removed_rows"]}
    assert d["unchanged_input_counts"] == {k:len(original[k]) for k in d["unchanged_input_counts"]}
    assert sha(ROOT / d["runtime_source"]) == d["runtime_sha256"]
    for name in ("FINDING.md", "PLAN.md"):
        assert "declaration-accounting-119093.json" in (folder / name).read_text()
    removed.extend(d["removed_rows"])
    added.extend(d["added_rows"])
assert len(removed) == 13 and len(added) == 18
for a in assignments:
    folder = ROOT / a["dossier"]
    original = read(folder / "evidence/inputs.json")
    module = a["row"][0].split(".py:")[0]
    assert a["work"] == original["work"] and module == original["module"]
    if module not in by_module:
        assert a["row"] in original["orphan_calls"]
    else:
        assert a["dossier"] == by_module[module]["dossier"]
for name in ("focused.txt", "cache.txt"):
    assert "\nOK\n" in (HERE / name).read_text()
assert "boundary calls attributed to no entry" in (HERE / "expected-aggregate-failure.txt").read_text()
facts = {"handoff_hash":sha(HERE/"handoff-hashes.json"),"verified_handoff_paths":len(packet["hashes"]),"candidate_sha256":sha(source),"mode":"0644","runtime_hashes":len(proposal_packet["runtime_hashes_unchanged"]),"changed_existing_methods":changed,"module_appendices":len(deltas),"removed_rows":len(removed),"added_rows":len(added),"residual_rows_assigned_once":len(assignments),"residual_occurrences":79,"retained_test_evidence":{"focused":11,"cache":6},"tests_rerun":False}
(HERE / "review-119189.json").write_text(json.dumps(facts,indent=2)+"\n")
(HERE / "review-119189-candidate.py").write_bytes(source.read_bytes())
print(json.dumps(facts,indent=2))
