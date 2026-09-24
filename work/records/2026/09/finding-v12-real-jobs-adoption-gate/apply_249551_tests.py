"""Claim-249551 witness corrections: bound imports, invalid policy, disk root."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

BOUND = '''    def bound_environment(self):
        """The import path ADOPTION-247941.md step 3 prints, exactly.

        THE PINNED SOURCE ALONE, not the checkout. Review
        2026-09-23T17:25:40Z: the subprocess imported the checkout while the
        pin helper checked the snapshot, so a passing pin check said nothing
        about the bytes that actually composed. `two_jobs.imported_from` now
        refuses that, and this is the environment that satisfies it.
        """
        import verify_247941
        return dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                    PYTHONPATH=os.pathsep.join(
                        [str(verify_247941.SNAPSHOT), HERE]))
'''

CASES = '''    def test_a_composition_bound_to_the_CHECKOUT_is_refused(self):
        """The pin check and the composition must be about the same bytes."""
        place, _ = self.resolved()
        into = os.path.join(self.packet_root(), "unbound")
        import subprocess
        answer = subprocess.run(
            [sys.executable, "-B", os.path.join(HERE, "two_jobs.py"),
             "--selections", place, "--into", into],
            capture_output=True, text=True, timeout=300, cwd=os.sep,
            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                     PYTHONPATH=os.pathsep.join(
                         [os.path.join(CHECKOUT, "v12/python/src"),
                          os.path.join(CHECKOUT, "v12/python"), HERE])))
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("bound to the pinned manager source",
                      answer.stderr + answer.stdout)
        self.assertFalse(os.path.exists(into))

    def test_an_invalid_terminal_policy_is_refused_at_composition(self):
        """Not at submission, where an operator would meet it instead."""
        place, document = self.resolved()
        for one in document["arrangement"]["jobs"]:
            one["terminal_policy"] = "carry-on-regardless"
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle, indent=2, sort_keys=True)
        into = os.path.join(self.packet_root(), "invalid-policy")
        answer = self.composing(place, into)
        self.assertNotEqual(answer.returncode, 0)
        self.assertIn("public reader refuses", answer.stderr + answer.stdout)
        self.assertFalse(os.path.exists(into))

'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    start = body.index("    def bound_environment(self):")
    end = body.index("    def composing(self, selections, into):")
    body = body[:start] + BOUND + "\n" + body[end:]
    if "test_a_composition_bound_to_the_CHECKOUT_is_refused" not in body:
        anchor = "    def test_an_unresolved_template_is_refused_by_name(self):"
        body = body.replace(anchor, CASES + anchor, 1)
    place.write_text(body, encoding="utf-8")
    print("test_two_jobs.py corrected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
