"""Claim-255433: READ the typed CustodyAnswer instead of guessing at it.

Review 2026-09-24T08:59:44Z: "Root cause not established: inspect typed
CustodyAnswer/rendered diagnostic and fake helper invocation. OCI
normalize_directory delegates store/attempt to custody_act, not
assignment_roots; ROOT_NAMES alone is not diagnosis."

So this drives the SAME fixture case that refuses, wraps the adapter's own
`normalize_directory` so the answer is observed rather than inferred, and
prints what the act was asked, what the engine was asked, and what the answer
said about itself. It asserts nothing and changes nothing: it is a read.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import test_abandonment                                        # noqa: E402
from baton_v12.worker_manager import custody, oci              # noqa: E402


def main():
    seen = []
    original = oci.OciAdapter.normalize_directory

    def watched(self, store, *, assignment_id, which):
        answered = original(self, store, assignment_id=assignment_id,
                            which=which)
        seen.append({
            "which": which,
            "assignment_id": assignment_id,
            "ok": bool(getattr(answered, "ok", None)),
            "status": getattr(answered, "status", None),
            "unaccounted": getattr(answered, "unaccounted", None),
            "diagnostic": getattr(answered, "diagnostic", None),
            "rendered": getattr(answered, "rendered", None),
        })
        return answered

    oci.OciAdapter.normalize_directory = watched

    # THE HELPER INVOCATION, CAPTURED WHERE IT IS COMPOSED. The engine the
    # fixture drives is local to `faulted`, so reading `case.engine` answers
    # about nothing; `_custody_vector` is the one place the argv exists.
    composed = []
    vector_original = custody._custody_vector

    def composing(engine, **operands):
        argv, name = vector_original(engine, **operands)
        composed.append({"argv": list(argv), "name": name,
                         "operation": operands.get("operation"),
                         "which": operands.get("which")})
        return argv, name

    custody._custody_vector = composing

    answers = []
    port_original = custody.custody_act

    def acting(engine, run, **operands):
        def recording(argv, *arguments, **named):
            answer = run(argv, *arguments, **named)
            answers.append({"argv": list(argv), "answer": answer})
            return answer

        return port_original(engine, recording, **operands)

    custody.custody_act = acting

    case = test_abandonment.TheComposedAbandonmentIsCalled(
        "test_a_faulted_attempt_reaches_a_positive_cleanup")
    outcome = case.run()
    oci.OciAdapter.normalize_directory = original
    custody._custody_vector = vector_original
    custody.custody_act = port_original

    print(json.dumps({
        "composed_vectors": composed,
        "engine_answers": answers,
        "custody_acts": seen,
        "custody_root": custody.CUSTODY_ROOT,
        "custody_name": custody.CUSTODY_NAME,
        "normalize_result_shape": {
            one: kind.__name__ for one, kind
            in custody._CUSTODY_RESULT["normalize"].items()},
        "errors": [text for _case, text in outcome.errors],
        "failures": [text for _case, text in outcome.failures],
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
