"""Repository tooling for the v12 Python distribution.

A package only so the tools' own regressions can import them from the source
tree's top-level directory, which is `unittest discover`'s `-t .` and therefore
already on `sys.path` for the gate. Nothing here is part of the distribution:
`pyproject.toml` finds packages under `src/` only, so none of this travels into
the wheel.
"""
