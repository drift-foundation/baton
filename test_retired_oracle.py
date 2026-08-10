"""`baton_v6.py` after retirement: evidence, not a measurement.

Protocol 10 ended active differential parity. `test_core_parity.py` is gone
and the corpus it bridged now runs directly against the shipping core in
`test_core_conformance.py`.

The file itself STAYS, and stays byte-identical. It is the record of what
protocol 9 actually did — the thing every earlier claim of parity was made
against — and a record that can be edited is not a record. That is also why
nothing was added to it on retirement, not even a header saying it is retired:
a header would change the hash that makes it evidence, which is the one edit
that destroys the thing it documents. The retirement is documented HERE and in
`work/finding-protocol-10-umbrella/`, adjacent to the file rather than in it.
"""

from __future__ import annotations

import ast
import hashlib
import os
import pathlib

FROZEN = "6d9ffe8c8021bc692b3b474a8dc18cb468c5ce3b7a67d16e3cb838124e0f2671"


def test_the_retired_oracle_is_still_byte_identical():
	"""The same hash it has carried throughout, and for a new reason.

	While parity was active this guarded the MEASUREMENT: an edited oracle
	would have made every parity assertion meaningless. Now it guards the
	EVIDENCE. The assertion is unchanged; what it protects is not."""
	here = os.path.dirname(os.path.abspath(__file__))
	with open(os.path.join(here, "baton_v6.py"), "rb") as handle:
		digest = hashlib.sha256(handle.read()).hexdigest()
	assert digest == FROZEN, \
		"baton_v6.py changed; it is retained as protocol-9 evidence and is frozen"


def test_nothing_imports_the_retired_oracle():
	"""Retired means UNUSED, not merely unreferenced by the parity suite.

	An import that survived the retirement would leave the shipping code
	depending on a module nobody maintains, and the first divergence would
	surface as a behaviour nobody could explain -- exactly the confusion
	retirement was meant to end.

	Checked across the whole tree rather than a list of files, because the
	next import would arrive in a file this test does not know about.

	PARSED, not text-matched. The first version compared line prefixes, which
	an indented import inside a function, a combined `import a, baton_v6`, or a
	reformatted line would all have walked past -- and it was three imports
	inside multiprocessing entry points that this test was written to catch in
	the first place. `ast` sees them wherever they are."""
	root = pathlib.Path(__file__).resolve().parent
	offenders = []
	for path in sorted(root.rglob("*.py")):
		if path.name in ("baton_v6.py", pathlib.Path(__file__).name):
			continue
		if ".venv" in path.parts or "__pycache__" in path.parts:
			continue
		try:
			tree = ast.parse(path.read_text(encoding="utf-8"))
		except SyntaxError as error:          # not this test's business
			raise AssertionError(f"{path.relative_to(root)}: {error}") from None
		for node in ast.walk(tree):
			if isinstance(node, ast.Import):
				for alias in node.names:
					if alias.name.split(".")[0] == "baton_v6":
						offenders.append(f"{path.relative_to(root)}:{node.lineno}")
			elif isinstance(node, ast.ImportFrom):
				if (node.module or "").split(".")[0] == "baton_v6":
					offenders.append(f"{path.relative_to(root)}:{node.lineno}")
	assert offenders == [], f"the retired oracle is still imported: {offenders}"


def test_the_conformance_corpus_runs_against_the_shipping_core():
	"""The other half of the retirement, and the half that would fail
	silently.

	Removing parity is only safe because the corpus moved onto the core. If
	someone re-pointed it back at the oracle -- or at anything else -- the
	suite would still pass 432 tests while testing a module that is no longer
	shipped, and nothing else would notice."""
	root = pathlib.Path(__file__).resolve().parent
	corpus = (root / "test_core_conformance.py").read_text()
	assert "import baton_core._impl as b6" in corpus
	assert "import baton_v6" not in corpus
