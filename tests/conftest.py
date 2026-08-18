"""Test discovery for the `src/` layout.

`src/` is not on `sys.path` by default, so the packages under test are
invisible to a bare `pytest` invocation. Adding it here rather than through a
`PYTHONPATH` in the justfile means the suite runs the same way however it is
started -- `just test-v11`, `pytest`, `pytest tests/work/test_phase.py`, or an
IDE runner -- instead of only through the one entry point that happened to
export the variable.

A conftest rather than a root configuration file: Slawomir's root rule allows
five files and this is not one of them, and there is nothing to configure
beyond the path. Discovery stays pytest's ordinary recursive scan, so a new
test file is picked up by existing, not by being added to a list.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    # FRONT of the path: an installed copy of a same-named package must not
    # shadow the tree under test, which is the failure that makes a green
    # suite meaningless.
    sys.path.insert(0, str(SRC))


sys.path.insert(0, str(Path(__file__).resolve().parent))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "serial: run without xdist because the test manages its own process pool",
    )


# W4 (finding-v10-runtime-removal): the candidate-build explanation that
# stood here described `tests/candidate.py` and the v10 `just build` /
# `just test` sequence, both of which are gone. The v11 deployer is a
# separate operator-facing recipe and no part of this suite invokes it,
# so there is nothing left to warn about.
