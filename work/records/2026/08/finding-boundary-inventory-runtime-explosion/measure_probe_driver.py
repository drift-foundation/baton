"""Bounded measurement of the boundary-inventory probe driver.

Run from `v12/python` with `PYTHONPATH=src`:

    cd v12/python && PYTHONPATH=src python3 \
      ../../work/records/2026/08/finding-boundary-inventory-runtime-explosion/measure_probe_driver.py [PROBES]

It never runs the whole 549-probe driver. It times the pure discovery
projections, times one catalog construction, then runs the FIRST `PROBES` keys
through the driver's own loop shape and reports per-probe wall time, the
enclosing cleanup stack depth and the process file-descriptor count. The
549-probe figure it prints is an extrapolation of the measured per-probe cost,
labelled as such -- the point of this record is that the unbounded shape must
not be run to completion merely to time it.

THE LOOP HERE MIRRORS THE SHIPPED DRIVER, including the pre-loop release of the
framework fixture and the `finally` that reclaims each probe's own. The
pre-correction figures it produced against the pre-correction loop are recorded
in `PROGRESS.md`; `run_inventory.py` is what compares whole-module verdicts,
wall time and peak resource use between the two.
"""

import ast
import os
import sys
import time
import unittest

sys.path.insert(0, "tests/..")

from tests.manager import test_boundary_inventory as inventory  # noqa: E402

PROBES = int(sys.argv[1]) if len(sys.argv) > 1 else 20


def descriptors():
    try:
        return len(os.listdir("/proc/self/fd"))
    except OSError:
        return -1


def timed(what, run):
    started = time.perf_counter()
    answer = run()
    spent = time.perf_counter() - started
    print(f"{what:<34} {spent:9.3f}s")
    return answer, spent


def main():
    parses = [0]
    real_parse = ast.parse

    def counting(*operands, **named):
        parses[0] += 1
        return real_parse(*operands, **named)

    ast.parse = counting
    entries, _ = timed("receiving_entries()", inventory.receiving_entries)
    print(f"{'  entries':<34} {len(entries):>9}")
    timed("receiving_entries() again", inventory.receiving_entries)
    timed("owning_validators()", inventory.owning_validators)
    timed("propagated_owners()", inventory.propagated_owners)
    timed("columns_read()", inventory.columns_read)
    timed("_crossings()", inventory._crossings)
    print(f"{'ast.parse calls so far':<34} {parses[0]:>9}")

    case = inventory.EveryProbeProvesItArrived(
        "test_every_declared_probe_reaches_its_named_boundary")
    case._outcome = unittest.case._Outcome(result=None)
    before = descriptors()
    _, setup = timed("setUp()", case.setUp)
    catalog, build = timed("all_probes()", case.all_probes)
    keys = sorted(catalog)
    print(f"{'  probes':<34} {len(keys):>9}")
    print(f"{'ast.parse calls after catalog':<34} {parses[0]:>9}")
    ast.parse = real_parse

    case.doCleanups()
    taken = keys[:PROBES]
    started = time.perf_counter()
    for entry, fragment in taken:
        with case.subTest(entry=entry, label=fragment):
            try:
                case.setUp()
                full, probe = case.all_probes()[(entry, fragment)]
                case.assertIn(fragment, full)
                case.refusing(full, probe)
            finally:
                case.doCleanups()
    spent = time.perf_counter() - started
    after = descriptors()
    print(f"{'-' * 44}")
    print(f"{PROBES} probes in the driver's own shape  {spent:9.3f}s")
    print(f"{'  per probe':<34} {spent / PROBES:9.3f}s")
    print(f"{'  cleanup stack depth':<34} {len(case._cleanups):>9}")
    print(f"{'  file descriptors':<34} {before:>4} -> {after}")
    print(f"{'  extrapolated 549 probes':<34} "
          f"{spent / PROBES * len(keys):9.3f}s")


if __name__ == "__main__":
    main()
