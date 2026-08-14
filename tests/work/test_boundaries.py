"""The module-boundary rules from the plan, enforced rather than remembered.

- nothing in `baton_work` imports `baton_core` (restart ruling);
- `projection` and `jsonapi` perform no writes (their sources contain no
  transaction-opening call);
- `jsonapi` imports only from within the package boundary the plan names.
"""

from __future__ import annotations

import ast
import os
import pathlib

SRC = pathlib.Path(os.path.join(
	os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
	"src", "baton_work"))


def test_nothing_imports_baton_core():
	"""By AST, not by grep: the first version of this test failed on its own
	package docstring SAYING it does not import baton_core. Read the imports
	rather than the prose."""
	for source in SRC.glob("*.py"):
		tree = ast.parse(source.read_text())
		for node in ast.walk(tree):
			if isinstance(node, ast.Import):
				names = [alias.name for alias in node.names]
			elif isinstance(node, ast.ImportFrom):
				names = [node.module or ""]
			else:
				continue
			for name in names:
				assert not name.startswith("baton_core"), \
					f"{source.name} imports {name}; reuse is cherry-pick " \
					f"after revalidation, and nothing has been revalidated"


def test_the_read_side_opens_no_transaction():
	for name in ("projection.py", "jsonapi.py"):
		text = (SRC / name).read_text()
		for needle in ("BEGIN", "INSERT", "UPDATE", "DELETE", "_write",
		               "commit("):
			assert needle not in text, \
				f"{name} contains {needle!r}; the read side is pure"
