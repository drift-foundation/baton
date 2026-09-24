"""Claim-250287: the coverage that makes the shadow a FAILURE, not a reading.

Review 2026-09-23T19:04:38Z: "Restore one correct active callback and add
focused structural/behavior coverage to prevent this repeated shadowing." The
removal alone has been done before and did not hold -- the same duplicate came
back, the suite stayed green, and only a human reading the source found it.
So this adds two checks that fail on the bytes:

  * STRUCTURAL -- no class in ANY of this dossier's own modules defines one
    method name twice. The defect is not specific to `answering`; the thing
    that let it survive is that nothing looked.
  * BEHAVIOURAL -- the callback the class actually binds sets the composed
    handle. A future duplicate that happens to be structurally tidy still
    fails here.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "test_two_jobs.py"

ANCHOR = "def baseline_interrupted():"

ADDED = '''class NoCallbackInThisDossierIsSilentlyShadowed(unittest.TestCase):
    """The defect that came back twice, made into a failing check.

    Review 2026-09-23T18:47:09Z found `answering` defined twice and my fix
    landed in the unreachable copy. I removed it. Review 2026-09-23T19:04:38Z
    found it AGAIN, at 724 and 763, with the later one missing the composed
    handle -- and the suite was green through both, because a second
    definition of a method is legal Python and nothing here ever looked.

    Two definitions of one name in one class is never intentional in this
    dossier: the second silently wins, so a correction applied to the first
    looks applied and does nothing. These two checks are what makes that a
    red suite instead of a reading.
    """

    def modules(self):
        """Every module this dossier owns, by path."""
        found = sorted(pathlib.Path(__file__).resolve().parent.glob("*.py"))
        self.assertIn("test_two_jobs.py", [one.name for one in found])
        return found

    def test_no_class_defines_one_method_twice(self):
        """STRUCTURAL, over the source rather than over the imported class.

        Importing cannot see this at all -- by the time a class object exists
        the shadowed definition has already been discarded. So this reads the
        text, which is the only place both definitions are still visible.
        """
        for place in self.modules():
            with self.subTest(module=place.name):
                parsed = ast.parse(place.read_text(encoding="utf-8"))
                for node in ast.walk(parsed):
                    if not isinstance(node, ast.ClassDef):
                        continue
                    seen = {}
                    for one in node.body:
                        if isinstance(one, (ast.FunctionDef,
                                            ast.AsyncFunctionDef)):
                            seen.setdefault(one.name, []).append(one.lineno)
                    repeated = {name: lines
                                for name, lines in seen.items()
                                if len(lines) > 1}
                    self.assertEqual(
                        repeated, {},
                        f"{place.name}:{node.name} defines a method more than "
                        f"once; the later definition silently wins")

    def test_the_bound_callback_sets_the_composed_handle(self):
        """BEHAVIOURAL, on the callback the class actually binds.

        `mounted_at` reads `self._composed`, which the fixture's own `serving`
        sets and `main`'s composition does not. A turn that does not set it
        raises `AttributeError` on every tick, `_guarded` records that as one
        line of uncertainty, no implementation ever completes, and the run
        reports two admissions and no verdict. That is exactly what
        `{implementation: 2, review: 0}` was.

        No fixture is started here: a gate with nothing launched makes the
        loop body unreachable, so this asserts the handle and nothing else.
        """
        held = SimpleNamespace()
        turns = TheSHIPPEDTemplateComposesThroughTheACTUALCLI.answering(held)
        operations = object()
        turns(SimpleNamespace(launched={}),
              {"operations": operations, "control": None})
        self.assertIs(getattr(held, "_composed", None), operations,
                      "the bound callback did not set the composed handle")


'''


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "NoCallbackInThisDossierIsSilentlyShadowed" in body:
        raise SystemExit("REFUSED: the coverage is already present")
    if body.count(ANCHOR) != 1:
        raise SystemExit(f"REFUSED: {ANCHOR!r} is not in the file exactly once")
    body = body.replace(ANCHOR, ADDED + ANCHOR, 1)
    if "\nimport ast\n" not in body:
        if body.count("\nimport copy\n") != 1:
            raise SystemExit("REFUSED: cannot place the `ast` import")
        body = body.replace("\nimport copy\n", "\nimport ast\nimport copy\n", 1)
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for present in ("import ast", "NoCallbackInThisDossierIsSilentlyShadowed",
                    "test_no_class_defines_one_method_twice",
                    "test_the_bound_callback_sets_the_composed_handle"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("shadow coverage added, parsed and verified on disk")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
