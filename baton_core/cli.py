"""The agent CLI's entry point into the core.

`baton_core` deliberately does NOT export `main`: a library that offers a
command line invites being run as one, and `__init__` pops both `main` and
`_build_parser` off the package surface for that reason. But the CLI has to
get in somewhere, and reaching into `_impl` from the executable's bootstrap
would make a private module part of the distribution contract by accident.

So this is the door, and it is a door rather than a window: importing
`baton_core.cli` is a deliberate act that says "I am the command line", and
there is exactly one such importer. `import baton_core` still gets a library
with no `main` on it.

Nothing is implemented here. `_impl` carries the adapter, because `_impl` is
the byte-copy the differential oracle is compared against and splitting the
adapter out of it would put a difference in the thing that measures
differences.
"""

from __future__ import annotations

from ._impl import _build_parser, main

__all__ = ("main", "_build_parser")
