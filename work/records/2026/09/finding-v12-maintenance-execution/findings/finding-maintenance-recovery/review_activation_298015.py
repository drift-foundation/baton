import copy
from tests.tools.test_correction_restart import artifact
from tests.tools.correction_restart_trace import validate
a=artifact(counted_reopen=True)
assert validate(a,counted_reopen=True)==[]
for name in ("inert","unmatched","duplicate"):
    b=copy.deepcopy(a); events=b["final_counters"]["engine"]
    target=next(x for x in events if x["argv"][1]=="create")
    if name=="inert": target.pop("activation")
    elif name=="unmatched": target["activation"][1]="another-runtime"
    else: events.append(copy.deepcopy(target))
    codes={x["code"] for x in validate(b,counted_reopen=True)}
    expected={"inert":"C2-incomplete-evidence","unmatched":"C2-engine-activation","duplicate":"C2-engine-duplicate"}[name]
    assert expected in codes,(name,codes)
    print(name,expected)
print("positive plus three activation negatives PASS")
