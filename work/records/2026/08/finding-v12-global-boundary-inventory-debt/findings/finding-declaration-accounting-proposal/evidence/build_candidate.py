"""Build a review artifact; never writes the live inventory file."""
from pathlib import Path
import ast
import difflib
import hashlib
import json
import re

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
LIVE = ROOT / "v12/python/tests/manager/test_boundary_inventory.py"
baseline = LIVE.read_text()
assert hashlib.sha256(baseline.encode()).hexdigest() == "3973301e09e27a4cb724969c158a0441a629037718d755dae1ada594a2a24b5c"
proposal = (HERE / "proposal.py").read_text()
helper = proposal[proposal.index("class Occurrence"):]
helper = helper.replace("def calls(b, ", "def _boundary_calls(").replace("def occurrences(b):", "@functools.cache\ndef boundary_occurrences():")
helper = helper.replace("def claims(b, ", "def _boundary_claims(").replace("def account(", "def _account_boundary_calls(")
helper = helper.replace("calls(b, ", "_boundary_calls(").replace("Occurrence", "_BoundaryOccurrence").replace("b.", "")
research = (HERE / "research.py").read_text()
fragment = research[research.index("FRAGMENT ="):research.index("\n\ndef clear")]
fragment = fragment.replace("FRAGMENT", "_ACCOUNTING_FRAGMENT")
controls = research[research.index("def clear"):research.index("\n\ndef main")]
controls = re.sub(r"\bclear\(\)", "_clear_boundary_projections()", controls)
controls = controls.replace("self.addCleanup(clear)", "self.addCleanup(_clear_boundary_projections)")
controls = controls.replace("ExactCallAccounting", "HelperDeclarationsHaveExactAccounting").replace("FRAGMENT", "_ACCOUNTING_FRAGMENT").replace('Path("sample.py")', 'pathlib.Path("sample.py")')
controls = controls.replace("p.occurrences(b)", "boundary_occurrences()").replace("p.claims(b, ", "_boundary_claims(").replace("p.account(", "_account_boundary_calls(")
controls = re.sub(r"\bb\.", "", controls.replace("patch.object(b,", "patch.object(sys.modules[__name__],"))
replacement = '''    def test_every_boundary_call_belongs_to_an_entry_or_is_declared(self):
        """Every exact source call has an entry claim or a named exception.

        Declaration templates link to actual claimed propagation of that call.
        Repeated read/session projections share only the same call, kind, label
        and origin. Another source call or receiving context cannot borrow it.
        """
        records = boundary_occurrences()
        claimed = _boundary_claims(records, receiving_entries(), DELEGATED)
        _, residual = _account_boundary_calls(records, claimed, NOT_AN_ENTRY)
        orphans = sorted({(r.site, r.kind, r.label) for r in residual})
        self.assertEqual(orphans, [], "boundary calls attributed to no entry")
'''
tree = ast.parse(baseline)
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "EveryReceivingEntryHasOneOwner")
method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == "test_every_boundary_call_belongs_to_an_entry_or_is_declared")
lines = baseline.splitlines(keepends=True)
candidate = "".join(lines[:method.lineno - 1]) + replacement + "".join(lines[method.end_lineno:])
candidate = candidate.replace("import types\n", "import types\nimport sys\nfrom typing import NamedTuple\nfrom unittest.mock import patch\n", 1)
candidate = candidate.replace("# EVERY MEMOISED PROJECTION", helper + "\n\n# EVERY MEMOISED PROJECTION", 1)
candidate = candidate.replace("columns_read, owning_validators, propagated_owners)\n", "columns_read, owning_validators, propagated_owners, boundary_occurrences)\n", 1)
candidate += "\n\n" + fragment + "\n\n" + controls
compile(candidate, str(HERE / "candidate.py"), "exec")
(HERE / "candidate.py").write_text(candidate)
(HERE / "candidate.patch").write_text("".join(difflib.unified_diff(baseline.splitlines(keepends=True), candidate.splitlines(keepends=True), fromfile="a/v12/python/tests/manager/test_boundary_inventory.py", tofile="b/v12/python/tests/manager/test_boundary_inventory.py")))
old, new = ast.parse(baseline), ast.parse(candidate)
changed = []
for node in old.body:
    if isinstance(node, (ast.ClassDef, ast.FunctionDef)):
        other = next(n for n in new.body if type(n) is type(node) and n.name == node.name)
        if ast.dump(node) != ast.dump(other):
            changed.append(node.name)
assert changed == ["EveryReceivingEntryHasOneOwner"], changed
new_cls = next(n for n in new.body if isinstance(n, ast.ClassDef) and n.name == cls.name)
changed_methods = [n.name for n in cls.body if isinstance(n, ast.FunctionDef) and ast.dump(n) != ast.dump(next(m for m in new_cls.body if isinstance(m, ast.FunctionDef) and m.name == n.name))]
assert changed_methods == [method.name], changed_methods
audit = {"baseline_sha256": hashlib.sha256(baseline.encode()).hexdigest(), "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(), "changed_existing_classes": changed, "changed_existing_methods": changed_methods, "live_unchanged": LIVE.read_text() == baseline, "candidate_compiles": True}
(HERE / "candidate-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
print(json.dumps(audit, indent=2))
