from pathlib import Path
import ast
import hashlib
import io
import json
import sys
import time
import unittest
from unittest.mock import patch

ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
from tests.manager import test_boundary_inventory as b
import proposal as p

BASELINE = "3973301e09e27a4cb724969c158a0441a629037718d755dae1ada594a2a24b5c"
LIVE = ROOT / "v12/python/tests/manager/test_boundary_inventory.py"
FRAGMENT = '''
def _view(row, what):
    return boundaries.text(row["state"], f"{what} state")
def public(connection):
    row = connection.execute("SELECT * FROM runtime_lanes").fetchone()
    return _view(row, "owned")
'''


def clear():
    for projection in b.MEMOISED:
        if hasattr(projection, "cache_clear"):
            projection.cache_clear()


class ExactCallAccounting(unittest.TestCase):
    def model(self, text=FRAGMENT):
        clear()
        self.addCleanup(clear)
        sources = ((Path("sample.py"), ast.parse(text)),)
        patched = patch.object(b, "_sources", lambda: sources)
        patched.start()
        self.addCleanup(patched.stop)
        entries = b.receiving_entries()
        records = p.occurrences(b)
        claimed = p.claims(b, records, entries, {})
        return entries, records, claimed

    def test_exact_declaration_links_to_real_adopted_owner(self):
        entries, records, claimed = self.model()
        expected = ("adopted", "sample.py:public", "runtime_lanes.state")
        self.assertIn(expected, entries)
        resolved, residual = p.account(records, claimed, {})
        self.assertEqual(residual, frozenset())
        self.assertEqual(len(resolved), 1)
        declaration, actuals = next(iter(resolved.items()))
        self.assertEqual((declaration.call, declaration.label), (("sample.py:_view", 3, 11, 3, 57), "{what} state"))
        self.assertEqual({(r.site, r.label, r.subject) for r in actuals}, {
            ("sample.py:public", "owned state", "read:sample.py:public|runtime_lanes[state]")})
        self.assertTrue(all(expected in claimed[r] for r in actuals))

    def test_no_entry_claim_means_no_declaration_exemption(self):
        _, records, _ = self.model()
        resolved, residual = p.account(records, {}, {})
        self.assertEqual(resolved, {})
        self.assertEqual(residual, records)

    def test_deleting_validator_preserves_independent_entry_and_missing_owner_failure(self):
        text = FRAGMENT.replace('boundaries.text(row["state"], f"{what} state")', 'row["state"]')
        entries, records, _ = self.model(text)
        self.assertIn(("adopted", "sample.py:public", "runtime_lanes.state"), entries)
        self.assertEqual(records, frozenset())
        case = b.EveryReceivingEntryHasOneOwner()
        with self.assertRaisesRegex(AssertionError, "receiving entries with no owner"):
            case.test_every_receiving_entry_has_an_owning_validator()

    def test_same_label_at_unrelated_helper_is_still_orphan(self):
        _, records, claimed = self.model(FRAGMENT + '''
def _unrelated(value):
    return boundaries.text(value, "owned state")
''')
        _, residual = p.account(records, claimed, {})
        self.assertEqual({r.call[0] for r in residual}, {"sample.py:_unrelated"})
        # The current global-label algorithm would lose this unrelated call.
        old_claimed = {(r.kind, r.label) for r in claimed}
        self.assertTrue(all((r.kind, r.label) in old_claimed for r in residual))

    def test_same_site_and_label_do_not_claim_an_unrelated_subject(self):
        text = FRAGMENT.replace('return _view(row, "owned")', 'boundaries.text(row["state"], "same"); boundaries.text("internal", "same")')
        _, records, claimed = self.model(text)
        _, residual = p.account(records, claimed, {})
        found = [r for r in residual if r.site == "sample.py:public"]
        self.assertEqual(len(found), 1)
        self.assertEqual((found[0].label, found[0].subject), ("same", "?"))
        same_line = [r for r in records if r.site == "sample.py:public"]
        self.assertEqual(len({r.call[1] for r in same_line}), 1)
        self.assertEqual(len({r.call[2] for r in same_line}), 2)

    def test_one_claimed_context_cannot_hide_an_unclaimed_context(self):
        text = FRAGMENT + '''
def second(connection):
    row = connection.execute("SELECT * FROM runtime_lanes").fetchone()
    return _view(row, "second")
'''
        entries, records, _ = self.model(text)
        claimed = p.claims(b, records, {entry for entry in entries if entry[1] != "sample.py:second"}, {})
        resolved, residual = p.account(records, claimed, {})
        self.assertEqual(len(resolved), 1)
        self.assertEqual({(r.site, r.label) for r in residual}, {("sample.py:second", "second state")})

    def test_unreachable_helper_call_does_not_supply_a_link(self):
        text = FRAGMENT.replace('return _view(row, "owned")', 'return row["state"]\n    _view(row, "owned")')
        _, records, claimed = self.model(text)
        resolved, residual = p.account(records, claimed, {})
        self.assertEqual(resolved, {})
        self.assertEqual({r.call[0] for r in residual}, {"sample.py:_view"})

    def test_double_ownership_assertion_still_rejects_second_owner(self):
        entries, _, _ = self.model()
        entry = ("adopted", "sample.py:public", "runtime_lanes.state")
        self.assertIn(entry, entries)
        self.assertEqual(b.layer_labels(entry), ["owned state"])
        with patch.object(b, "STATED_OWNERS", {entry: "independent second claim"}):
            with self.assertRaisesRegex(AssertionError, "owned more than once"):
                b.EveryReceivingEntryHasOneOwner().test_no_entry_is_owned_twice()

    def test_projection_keeps_existing_owner_triples(self):
        _, records, _ = self.model()
        actual = {(r.site, r.kind, r.label, r.subject) for r in records}
        expected = {(site, kind, label, subject) for site, rows in b.owning_validators().items() for kind, label, subject in rows}
        self.assertEqual(actual, expected)

    def test_same_adopted_call_and_origin_can_be_projected_at_several_sites(self):
        _, records, claimed = self.model('''
def _read(connection):
    row = connection.execute("SELECT * FROM runtime_lanes").fetchone()
    boundaries.text(row["state"], "a lane state")
    return row
def public(connection):
    return _read(connection)
''')
        resolved, residual = p.account(records, claimed, {})
        self.assertEqual(residual, frozenset())
        self.assertEqual(len(resolved), 1)
        copy, owners = next(iter(resolved.items()))
        self.assertEqual(copy.site, "sample.py:public")
        self.assertEqual({r.site for r in owners}, {"sample.py:_read"})
        self.assertTrue(all((r.call, r.label, r.subject) == (copy.call, copy.label, copy.subject) for r in owners))

    def test_same_call_and_origin_with_another_label_cannot_borrow_claim(self):
        _, records, claimed = self.model()
        owner = next(r for r in records if r.propagated)
        other = owner._replace(label="another label")
        _, residual = p.account(records | {other}, claimed, {})
        self.assertEqual(residual, frozenset({other}))


def main():
    start = time.monotonic()
    assert hashlib.sha256(LIVE.read_bytes()).hexdigest() == BASELINE
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(ExactCallAccounting))
    (HERE / "controls.txt").write_text(stream.getvalue())
    print(stream.getvalue())
    if not result.wasSuccessful():
        (HERE / "execution.json").write_text(json.dumps({"elapsed_seconds": time.monotonic() - start, "controls_passed": False}, indent=2) + "\n")
        raise SystemExit(1)
    clear()
    entries = b.receiving_entries()
    records = p.occurrences(b)
    projected = {(r.site, r.kind, r.label, r.subject) for r in records}
    expected = {(site, kind, label, subject) for site, rows in b.owning_validators().items() for kind, label, subject in rows}
    assert projected == expected, (sorted(projected - expected), sorted(expected - projected))
    claimed = p.claims(b, records, entries, b.DELEGATED)
    resolved, residual = p.account(records, claimed, b.NOT_AN_ENTRY)
    inputs = json.loads((HERE / "inputs.json").read_text())
    symbolic = []
    for site, kind, label in inputs["symbolic_declarations"]:
        declarations = sorted(r for r in records if not r.propagated and (r.site, r.kind, r.label) == (site, kind, label))
        symbolic.append({"row": [site, kind, label], "declarations": [r._asdict() for r in declarations],
                         "links": [{"declaration": r._asdict(), "owners": [{"occurrence": owner._asdict(), "entries": sorted(claimed[owner])} for owner in sorted(resolved[r])]} for r in declarations if r in resolved],
                         "unresolved": [r._asdict() for r in declarations if r in residual]})
    old_claimed = set()
    for entry in entries:
        places = [(entry[1], b._claims(entry))]
        if entry in b.DELEGATED:
            places.append(b.DELEGATED[entry])
        for site, stem in places:
            for label in b._owned_here(site, stem, covering=entry[0] != "injected"):
                old_claimed.update((kind, label) for kind, found, _ in b.owning_validators().get(site, ()) if found == label)
    old_orphans = sorted({(r.site, r.kind, r.label) for r in records if (r.kind, r.label) not in old_claimed and (r.site, r.kind, r.label) not in b.NOT_AN_ENTRY})
    new_orphans = sorted({(r.site, r.kind, r.label) for r in residual})
    report = {"baseline_sha256": BASELINE, "controls_run": result.testsRun, "controls_passed": True,
              "same_owner_triples": True, "entries": len(entries), "occurrences": len(records),
              "claimed_occurrences": len(claimed), "resolved_occurrences": len(resolved),
              "resolved_declarations": sum(not r.propagated and r.subject.startswith("caller:") for r in resolved),
              "residual_occurrences": len(residual), "old_orphan_rows": old_orphans, "candidate_orphan_rows": new_orphans,
              "removed_rows": sorted(set(old_orphans) - set(new_orphans)), "added_rows": sorted(set(new_orphans) - set(old_orphans)),
              "symbolic_declarations": symbolic, "residuals": [r._asdict() for r in sorted(residual)],
              "resolved": [{"occurrence": r._asdict(), "owners": [{"occurrence": owner._asdict(), "entries": sorted(claimed[owner])} for owner in sorted(resolved[r])]} for r in sorted(resolved)],
              "elapsed_seconds": time.monotonic() - start}
    assert hashlib.sha256(LIVE.read_bytes()).hexdigest() == BASELINE
    (HERE / "research.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ("old_orphan_rows", "candidate_orphan_rows", "removed_rows", "added_rows", "symbolic_declarations", "residuals", "resolved")}, indent=2))


if __name__ == "__main__":
    main()
