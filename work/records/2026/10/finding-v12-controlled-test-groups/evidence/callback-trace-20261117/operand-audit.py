"""Per-operand audit: every STAGE_C_INTERNAL operand (and LayoutDelivery's three) traced at every call site."""
import time, traceback
from tests.manager import test_boundary_inventory as m
rule = "under the callback-tracing rule (review 2026-11-17T23:24:47Z): a lambda answers its traced body, a composing builtin that invokes a callback answers what the callback answers over the traced iterable, a non-lambda callback fails closed"
print("every STAGE_C_INTERNAL and STAGE_C_ADOPTED_ROW_DOORS operand traced at every call site " + rule)
case = m.EveryReceivingEntryHasOneOwner()
targets = [(site, parameter) for site, subjects in sorted(m.STAGE_C_INTERNAL.items()) for parameter in sorted({s.split(".")[0] for s in subjects})]
targets += [("source_boundary.py:LayoutDelivery.__init__", name) for name in ("root", "place", "document")]
targets += [(site, subjects[0]) for site, subjects in sorted(m.STAGE_C_ADOPTED_ROW_DOORS.items())]
failures = 0; started = time.time()
for site, parameter in targets:
    t = time.time()
    try:
        m.StageCProtections()._handed_owned(site, parameter, case, subtests=False)
        print(f"ok   {site} {parameter} {time.time()-t:.1f}s", flush=True)
    except AssertionError as x:
        failures += 1
        print(f"FAIL {site} {parameter} {time.time()-t:.1f}s\n     {str(x)[:600]}", flush=True)
print(f"failures {failures} of {len(targets)} total {time.time()-started:.0f}s")
