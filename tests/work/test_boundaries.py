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
	for source in SRC.rglob("*.py"):
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


def test_the_tui_imports_only_the_shared_surfaces():
	"""B1's boundary: the renderer reaches the authority only through
	projection and transitions — no SQL, no _write, no baton_core."""
	import ast
	# `cli` joined the allowlist with the Gate B command bar: the console
	# routes typed ACTIONS through the ONE public CLI entry (same grammar,
	# same refusals) — going through the boundary, not around it. SQL,
	# _write, and baton_core stay banned below.
	allowed = ("authority", "projection", "transitions", "cli", "tui")
	for source in (SRC / "tui").rglob("*.py"):
		tree = ast.parse(source.read_text())
		for node in ast.walk(tree):
			touched = []
			if isinstance(node, ast.Import):
				touched = [alias.name for alias in node.names
				           if alias.name.startswith("baton_work")]
			elif isinstance(node, ast.ImportFrom):
				module = node.module or ""
				if module == "baton_work":
					# `from baton_work import X`: X is the surface named.
					touched = [f"baton_work.{alias.name}"
					           for alias in node.names]
				elif module.startswith("baton_work"):
					touched = [module]
			for module in touched:
				parts = module.split(".")
				assert len(parts) >= 2 and parts[1] in allowed, \
					f"{source.name} imports {module}"
		text = source.read_text()
		for needle in ("SELECT", "INSERT", "UPDATE", "conn.execute", "_write"):
			assert needle not in text, f"{source.name} contains {needle!r}"


def test_the_read_side_never_commits():
	"""The read side is PURE — it inserts, updates, deletes and commits
	nothing. A read-only snapshot transaction (BEGIN … ROLLBACK, WS-1 R3:
	home's rows/summary/seq describe one database snapshot) is a read,
	so BEGIN alone is permitted — but every BEGIN must be matched by a
	ROLLBACK path and nothing on this side may ever COMMIT."""
	for name in ("projection.py", "jsonapi.py", "config.py"):
		text = (SRC / name).read_text()
		for needle in ("INSERT", "UPDATE", "DELETE", "_write", "commit(",
		               "COMMIT"):
			assert needle not in text, \
				f"{name} contains {needle!r}; the read side is pure"
		assert text.count('execute("BEGIN")') == text.count(
			'execute("ROLLBACK")'), \
			f"{name} opens a snapshot it does not roll back"
