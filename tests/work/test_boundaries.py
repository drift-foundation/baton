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
	# W24755 added `dot.py`: a pure renderer over an already-built envelope.
	# It holds no store handle at all, so it is even further from the write
	# side than the other three -- which is exactly why it belongs on this
	# list rather than being the one read-side module nothing checks.
	for name in ("projection.py", "jsonapi.py", "config.py", "dot.py"):
		text = (SRC / name).read_text()
		for needle in ("INSERT", "UPDATE", "DELETE", "_write", "commit(",
		               "COMMIT"):
			assert needle not in text, \
				f"{name} contains {needle!r}; the read side is pure"
		assert text.count('execute("BEGIN")') == text.count(
			'execute("ROLLBACK")'), \
			f"{name} opens a snapshot it does not roll back"


def test_no_module_defines_one_top_level_name_twice():
	"""A second definition of a module-scope name silently replaces the first.

	W24755 appended a `work_graph` projection whose helper was called
	`_graph_node` -- a name `projection.py` had already used for the bounded
	dependency neighbourhood. Python does not complain; it just rebinds. The
	export's own suite passed while every dependency-graph case failed with a
	TypeError, because the two helpers take different arguments.

	Nothing caught the CLASS of defect, only the instance: a focused run of
	the new module cannot see it at all, and the full gate reports it as
	eighty-eight failures somewhere else entirely. So the rule is checked
	directly, over every module, by AST.

	Deliberately module-scope only. A method shadowing another method inside a
	class, a name rebound inside a function, and a conditional re-import are
	all ordinary Python; what this forbids is two top-level definitions of one
	name in one file, which is never intentional here.
	"""
	import collections
	for source in SRC.rglob("*.py"):
		defined = collections.defaultdict(list)
		for node in ast.parse(source.read_text()).body:
			if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
			                     ast.ClassDef)):
				defined[node.name].append(node.lineno)
			elif isinstance(node, ast.Assign):
				for target in node.targets:
					if isinstance(target, ast.Name):
						defined[target.id].append(node.lineno)
		repeated = {name: lines for name, lines in defined.items()
		            if len(lines) > 1}
		assert not repeated, \
			f"{source.name} defines {repeated} more than once at module " \
			f"scope; the later definition silently replaces the earlier"


def test_the_read_side_imports_only_vocabulary_from_transitions():
	"""The read side may borrow the authority's closed VALUES, never its acts.

	W24755's export has to refuse a forged `status` or `phase`, and a
	renderer-only copy of those vocabularies would be a second opinion about
	the authority's own axes -- so `projection` imports the canonical tuples
	from `transitions`. That is a one-way dependency from the read side onto
	the write module, and `test_the_read_side_never_commits` is a source-TEXT
	check that would not notice if it ever grew into importing a mutation.

	So the import is held to what it is for: every name `projection` takes from
	`transitions` must resolve to a tuple of strings. A function, a class or a
	module fails here, which is the moment to ask whether the read side should
	be reaching for it at all.
	"""
	import ast
	from baton_work import transitions
	taken = []
	for node in ast.parse((SRC / "projection.py").read_text()).body:
		if isinstance(node, ast.ImportFrom) and \
				(node.module or "").endswith("transitions"):
			taken += [alias.name for alias in node.names]
		elif isinstance(node, ast.Import):
			for alias in node.names:
				assert not alias.name.endswith("transitions"), \
					"projection imports the transitions MODULE; take the " \
					"exact vocabulary names instead"
	assert taken, "this rule is about an import that no longer exists"
	for name in taken:
		value = getattr(transitions, name)
		assert isinstance(value, (str, tuple)), \
			f"projection takes {name} from transitions, which is a " \
			f"{type(value).__name__}; the read side borrows closed " \
			f"vocabulary and nothing else"
		if isinstance(value, tuple):
			assert all(isinstance(one, str) for one in value), name
