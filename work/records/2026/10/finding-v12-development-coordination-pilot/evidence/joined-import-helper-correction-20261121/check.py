import importlib.util, json, pathlib, unittest
from unittest.mock import patch
HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("helper", HERE / "integrate.py")
h = importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)
PACKET = HERE.parent / "joined-composition-20261121"
class Checks(unittest.TestCase):
    def test_missing_malformed_pins_refuse_before_io(self):
        for name, values in (("MANIFEST_SHA", [None, "", "<set-after-review>", "g"*64]), ("TREE", [None, "", "<set-after-review>", "a"*64, "sha256:"+"g"*64])):
            for value in values:
                with self.subTest(name=name, value=value), patch.object(h, name, value), patch("builtins.open", side_effect=AssertionError("IO before refusal")), patch.object(h.tempfile, "mkstemp", side_effect=AssertionError("write")):
                    self.assertEqual(h.main(["preflight", "absent", "absent"]), 2)
                    self.assertEqual(h.main(["import", "absent", "absent"]), 2)
    def test_wrong_pins_refuse_before_target_access(self):
        for name, value in (("MANIFEST_SHA", "0"*64), ("TREE", "sha256:"+"0"*64)):
            with self.subTest(name=name), patch.object(h, name, value), patch.object(h, "git", side_effect=AssertionError("target access")), patch.object(h.os, "makedirs", side_effect=AssertionError("write")), patch.object(h.tempfile, "mkstemp", side_effect=AssertionError("write")):
                self.assertEqual(h.main(["import", str(PACKET), "absent"]), 2)
    def test_invalid_dispatch_never_calls_operations(self):
        for args in ([], ["prefight", "p", "o"], ["--help", "p", "o"], ["import"], ["import", "p", "o", "extra"], ["preflight", "p"], ["IMPORT", "p", "o"]):
            with self.subTest(args=args), patch.object(h, "preflight", side_effect=AssertionError("dispatch")), patch.object(h, "do_import", side_effect=AssertionError("dispatch")):
                self.assertEqual(h.main(args), 2)
    def test_help_is_inert(self):
        with patch.object(h, "preflight", side_effect=AssertionError("dispatch")), patch.object(h, "do_import", side_effect=AssertionError("dispatch")):
            self.assertEqual(h.main(["--help"]), 0)
    def test_only_explicit_import_dispatches(self):
        with patch.object(h, "preflight", return_value=({}, [])) as check, patch.object(h, "do_import", return_value=0) as write:
            self.assertEqual(h.main(["preflight", "p", "o"]), 0)
            check.assert_called_once_with("p", "o")
            write.assert_not_called()
            self.assertEqual(h.main(["import", "p", "o"]), 0)
            write.assert_called_once_with("p", "o")
if __name__ == "__main__":
    unittest.main(verbosity=2)
