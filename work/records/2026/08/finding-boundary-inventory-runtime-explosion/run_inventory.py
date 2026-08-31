"""Run one boundary-inventory module and report its verdict, time and peak use.

Run from `v12/python` with `PYTHONPATH=src`:

    PYTHONPATH=src python3 <this> tests.manager.test_boundary_inventory
    PYTHONPATH=src python3 <this> /path/to/a/copy.py

A dotted name is imported as usual. A PATH is loaded as a module of the
`tests.manager` package, so a copy kept outside the tree -- the pre-correction
baseline, for instance -- runs with the same relative imports and the same
fixtures as the shipped file. Both forms report the same three things, so a
before and an after are comparable: the failure/error verdict by test id, the
wall time, and the peak resident size and file-descriptor high-water mark.
"""

import importlib
import importlib.util
import os
import pathlib
import resource
import sys
import threading
import time
import unittest

sys.path.insert(0, ".")

WATCHED = "/proc/self/fd"


def descriptors():
    try:
        return len(os.listdir(WATCHED))
    except OSError:
        return -1


def load(name):
    if not name.endswith(".py"):
        return importlib.import_module(name)
    path = pathlib.Path(name).resolve()
    import tests.manager  # noqa: F401  -- the package the copy belongs to
    dotted = f"tests.manager.{path.stem}"
    spec = importlib.util.spec_from_file_location(dotted, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[dotted] = module
    spec.loader.exec_module(module)
    return module


def main():
    module = load(sys.argv[1])
    high = [descriptors()]
    watching = True

    def watch():
        while watching:
            high[0] = max(high[0], descriptors())
            time.sleep(0.25)

    watcher = threading.Thread(target=watch, daemon=True)
    watcher.start()
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    result = unittest.TextTestRunner(verbosity=0, stream=sys.stderr).run(suite)
    watching = False
    watcher.join(timeout=1)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    print(f"module              {module.__name__}")
    print(f"tests               {result.testsRun}")
    print(f"failures            {len(result.failures)}")
    print(f"errors              {len(result.errors)}")
    print(f"peak resident KiB   {peak}")
    print(f"descriptor peak     {high[0]}")
    print("-- failing ids --")
    for case, _ in sorted(result.failures + result.errors, key=lambda p: str(p[0])):
        print(f"  {case}")


if __name__ == "__main__":
    started = time.perf_counter()
    try:
        main()
    finally:
        print(f"wall seconds        {time.perf_counter() - started:.3f}")
