import ast,difflib,hashlib,json,time
from pathlib import Path
from tests.manager import test_boundary_inventory as b
start=time.monotonic()
evidence=Path(__file__).resolve().parent
base=(evidence/"base-120897.py").read_text()
path=Path(b.__file__)
current=path.read_text()
oldtree=ast.parse(base);newtree=ast.parse(current)
changed={"_owned_here","_boundary_claims","_account_boundary_calls"}
oldglobals=dict(vars(b))
for node in oldtree.body:
    if isinstance(node,ast.FunctionDef) and node.name in changed:
        exec(compile(ast.Module(body=[node],type_ignores=[]),"<accepted-baseline>","exec"),oldglobals)
# All existing nodes except the three approved shared helpers retain exact AST.
def identity(n):
    if isinstance(n,(ast.FunctionDef,ast.ClassDef)):return n.name
    return None
new_by_name={identity(n):n for n in newtree.body if identity(n)}
for node in oldtree.body:
    name=identity(node)
    if name in changed:continue
    if name:assert ast.dump(node)==ast.dump(new_by_name[name]),name
    else:assert any(ast.dump(node)==ast.dump(n) for n in newtree.body),ast.dump(node)[:100]
entries=b.receiving_entries();records=b.boundary_occurrences()
relations=b._column_check_relations(records,entries)
before_claims=oldglobals["_boundary_claims"](records,entries,b.DELEGATED)
after_claims=b._boundary_claims(records,entries,b.DELEGATED)
before_resolved,before_residual=oldglobals["_account_boundary_calls"](records,before_claims,b.NOT_AN_ENTRY)
after_resolved,after_residual=b._account_boundary_calls(records,after_claims,b.NOT_AN_ENTRY)
changed_claims=[]
for entry in entries:
    before={r for r,owners in before_claims.items() if entry in owners}
    after={r for r,owners in after_claims.items() if entry in owners}
    if before!=after:changed_claims.append(entry)
assert set(changed_claims)==set(relations),changed_claims
old_owned=oldglobals["_owned_here"]
before=set()
for entry in entries:
    if entry in b.NO_PROBE:continue
    labels=set(old_owned(entry[1],b._claims(entry),covering=entry[0]!="injected"))
    if entry in b.DELEGATED:labels.update(old_owned(*b.DELEGATED[entry]))
    before.update((entry,label) for label in labels)
case=b.EveryProbeProvesItArrived();case.setUp()
try:
    after=case.expected()
    declared=set(case.all_probes())
finally:case.doCleanups()
removed={(entry,pair[1].label) for entry,pair in relations.items()}
added={(entry,pair[0].label) for entry,pair in relations.items()}
assert before-after==removed,(before-after,removed)
assert after-before==added,(after-before,added)
module=lambda pairs:sorted(p for p in pairs if p[0][1].startswith("review_cycles.py:"))
assert len(module(before-declared))==7
assert len(module(after-declared))==5
assert len(module(declared-before))==2
assert module(declared-after)==[]
links=[]
for entry,(row,repeat) in relations.items():
    assert after_resolved[repeat]=={row}
    assert entry in after_claims[row]
    links.append(dict(entry=entry,row=row._asdict(),repeat=repeat._asdict(),row_claims=sorted(after_claims[row])))
research=json.loads((evidence/"research-120810.json").read_text())
for name,sha in research["hashes"].items():
    if not name.endswith("test_boundary_inventory.py"):assert hashlib.sha256(Path(name).read_bytes()).hexdigest()==sha,name
report=dict(candidate_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),base_sha256=hashlib.sha256(base.encode()).hexdigest(),preserved_existing_AST_except=sorted(changed),entries=len(entries),occurrences=len(records),changed_claim_entries=sorted(changed_claims),removed_pairs=sorted(removed),added_pairs=sorted(added),module_missing_after=module(after-declared),module_orphan_after=module(declared-after),explicit_links=links,residual_occurrences_before=len(before_residual),residual_occurrences_after=len(after_residual),removed_residuals=[r._asdict() for r in sorted(before_residual-after_residual)],added_residuals=[r._asdict() for r in sorted(after_residual-before_residual)],runtime_hashes_unchanged=True,seconds=time.monotonic()-start)
(evidence/"candidate-120897.py").write_text(current)
(evidence/"candidate-120897.patch").write_text("".join(difflib.unified_diff(base.splitlines(True),current.splitlines(True),fromfile="a/v12/python/tests/manager/test_boundary_inventory.py",tofile="b/v12/python/tests/manager/test_boundary_inventory.py")))
with (evidence/"verification-120897.json").open("x") as out:json.dump(report,out,indent=2)
print(json.dumps(report,indent=2))
