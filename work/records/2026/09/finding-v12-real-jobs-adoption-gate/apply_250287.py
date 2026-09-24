"""Claim-250287: remove the REINTRODUCED `answering` shadow, once and checked.

Review 2026-09-23T19:04:38Z: `test_two_jobs.py` defines `answering` at 724
(which sets `self._composed`) and AGAIN at 763 (which does not). Python binds
the later one, so every `main` turn reaches `mounted_at` ->
`job_execution_for` -> `composed_for` and finds no handle. That is the whole
`{implementation: 2, review: 0}` observation, in current source, and no
disposable-root hypothesis is needed for it.

This deletes the SECOND definition -- the one without the handle -- and then
reads the file back and REFUSES unless exactly one survives and it is the one
that sets the handle. A script that reports its own success is the thing that
failed before.
"""
import ast
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "test_two_jobs.py"

# THE SHADOW, verbatim. Matching on the body rather than on line numbers means
# a file that has already been corrected fails loudly instead of cutting
# something else out of it.
SHADOW = '''    def answering(self):
        """The deterministic turn, driven from the RUNTIME CONTEXT.

        The supervisor hands each tick's callback the composed operations, so
        the turn can reach the attempt's mounted workspace -- which is what a
        container would be writing into. Without that context the callback
        could do no work, which is exactly why the first entry-point case
        proved nothing.
        """
        answered = set()

        def turns(gate, context):
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


def shadowed(source):
    """Every (class, method) this module defines more than once."""
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.ClassDef):
            continue
        seen = {}
        for one in node.body:
            if isinstance(one, (ast.FunctionDef, ast.AsyncFunctionDef)):
                seen.setdefault(one.name, []).append(one.lineno)
        for name, lines in seen.items():
            if len(lines) > 1:
                found.append((node.name, name, lines))
    return found


def main():
    body = PLACE.read_text(encoding="utf-8")
    before = shadowed(body)
    if not before:
        raise SystemExit("REFUSED: nothing is shadowed; this has already run")
    count = body.count(SHADOW)
    if count != 1:
        raise SystemExit(
            f"REFUSED: the shadow text appears {count} times, not once; "
            f"the file is not the one this correction was written against")
    PLACE.write_text(body.replace(SHADOW, "", 1), encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    after = shadowed(written)
    if after:
        raise SystemExit(f"REFUSED: still shadowed after the edit: {after}")
    # AND THE SURVIVOR IS THE ONE WITH THE HANDLE, not merely a survivor.
    for node in ast.walk(ast.parse(written)):
        if isinstance(node, ast.ClassDef):
            for one in node.body:
                if (isinstance(one, ast.FunctionDef)
                        and one.name == "answering"):
                    kept = ast.get_source_segment(written, one) or ""
                    if 'self._composed = context["operations"]' not in kept:
                        raise SystemExit(
                            f"REFUSED: {node.name}.answering survives without "
                            f"setting the composed handle")
    print(f"removed the shadow; was {before}, now none, "
          f"and the survivor sets the handle")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
