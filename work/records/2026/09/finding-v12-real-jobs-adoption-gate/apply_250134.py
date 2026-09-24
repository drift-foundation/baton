"""Claim-250134: one `answering`, and it sets the handle the mount needs."""
import ast
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

FIXED = '''    def answering(self):
        """The deterministic turn, driven from the RUNTIME CONTEXT.

        THE HANDLE IS SET HERE. `mounted_at` reads `self._composed`, which the
        fixture's own `serving` sets and `main`'s composition does not -- so
        through the command every turn raised `AttributeError`, `_guarded`
        recorded it as uncertainty, and no implementation ever completed.

        Review 2026-09-23T18:47:09Z also found that this helper was defined
        TWICE and my fix had landed in the OTHER one, `turning`. Two
        definitions of one name in a class is a silent shadowing: the second
        wins and the first is unreachable, so a correction applied to the
        wrong one looks applied. There is one now.
        """
        answered = set()

        def turns(gate, context):
            self._composed = context["operations"]
            for attempt_id, kind in sorted(gate.launched.items()):
                if attempt_id in answered:
                    continue
                mounted = self.mounted_at(context["operations"], attempt_id)
                if not mounted:
                    continue
                if kind == "implementation":
                    edits = {"harness.py": "print('answered')\\n"}
                    if gate.job_of(attempt_id) == "job-b":
                        edits = {"feature.py": self.B_FEATURE,
                                 "feature_check.py": self.B_CHECK}
                else:
                    report = copy.deepcopy(self.REPORT)
                    report["verdict"] = "accepted"
                    edits = {"review-report.json": json.dumps(report)}
                self.turn(context["control"], kind, attempt_id, mounted,
                          edits=edits)
                answered.add(attempt_id)

        return turns

'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    lines = body.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines)
              if line.strip() == "def answering(self):"]
    if len(starts) != 2:
        raise SystemExit(f"REFUSED: expected two `answering` definitions, "
                         f"found {len(starts)}")

    def ends_at(start):
        for index in range(start + 1, len(lines)):
            stripped = lines[index].strip()
            if stripped.startswith("def ") and \
                    lines[index].startswith("    def "):
                return index
        raise SystemExit("REFUSED: no following method found")

    first, second = starts
    body = "".join(lines[:first] + [FIXED] + lines[ends_at(second):])
    place.write_text(body, encoding="utf-8")
    written = place.read_text(encoding="utf-8")
    tree = ast.parse(written)
    names = [node.name for node in ast.walk(tree)
             if isinstance(node, ast.FunctionDef) and node.name == "answering"]
    if len(names) != 1:
        raise SystemExit(f"REFUSED: {len(names)} `answering` definitions "
                         f"survive")
    if written.count("self._composed = context[\"operations\"]") < 2:
        raise SystemExit("REFUSED: the handle is not set in both callbacks")
    print("one answering, handle set, verified on disk")
    return 0


if __name__ == "__main__":
    sys.exit(main())
