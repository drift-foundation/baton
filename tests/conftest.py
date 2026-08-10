"""Test discovery for the `src/` layout.

`src/` is not on `sys.path` by default, so the packages under test are
invisible to a bare `pytest` invocation. Adding it here rather than through a
`PYTHONPATH` in the justfile means the suite runs the same way however it is
started -- `just test`, `pytest`, `pytest tests/tui/test_tui_render.py`, or an
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

SRC = Path(__file__).resolve().parent.parent / "src"
if str(SRC) not in sys.path:
    # FRONT of the path: an installed copy of a same-named package must not
    # shadow the tree under test, which is the failure that makes a green
    # suite meaningless.
    sys.path.insert(0, str(SRC))
