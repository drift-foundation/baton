"""Run this dossier's focused verification and retain its measured receipt.

Not a test. It exists so the recorded seconds are a measurement rather than an
estimate, and so the receipt names the exact bytes that were run.
"""
import hashlib
import io
import json
import os
import pathlib
import time
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SIBLING = HERE.parent / "finding-v12-single-implementation-proof"
CHECKOUT = HERE.parents[4]
MODULES = ("test_attachment", "test_review_bindings",
           "test_review_supervisor")
OWNED = ("attachment.py", "review_bindings.py", "review_supervisor.py",
         "test_attachment.py", "test_review_bindings.py",
         "test_review_supervisor.py", "SELECTIONS-239533.json",
         "OPERATOR-239533.md", "OWNER-PRODUCT-CHANGE-247423.md",
         "PRODUCT-CHANGE-247423.json", "preexisting_errors.py",
         "verify.py")
# THE ACCEPTED BYTES THIS DOSSIER REUSES rather than copies. `review_bindings`
# imports W239528's helpers and `test_attachment` borrows the product suite's
# own fixture, so recording both digests is what makes "reuses" checkable: a
# later drift in either is visible in the next receipt instead of silent.
REUSED = {
    "baseline_bindings.py": SIBLING / "baseline_bindings.py",
    "baseline.py": SIBLING / "baseline.py",
    "tests/manager/test_review_cycles.py":
        CHECKOUT / "v12/python/tests/manager/test_review_cycles.py",
    "tests/manager/test_offers.py":
        CHECKOUT / "v12/python/tests/manager/test_offers.py",
    "tests/manager/input_roots.py":
        CHECKOUT / "v12/python/tests/manager/input_roots.py",
    "src/baton_v12/worker_manager/offers.py":
        CHECKOUT / "v12/python/src/baton_v12/worker_manager/offers.py",
    "src/baton_v12/worker_manager/review_cycles.py":
        CHECKOUT / "v12/python/src/baton_v12/worker_manager/review_cycles.py",
    "tools/stage_execution.py":
        CHECKOUT / "v12/python/tools/stage_execution.py",
    "src/baton_v12/worker_manager/store.py":
        CHECKOUT / "v12/python/src/baton_v12/worker_manager/store.py",
}


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def main():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(
        [loader.loadTestsFromName(one) for one in MODULES])
    stream = io.StringIO()
    started = time.perf_counter()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    elapsed = time.perf_counter() - started
    (HERE / "verification-7.log").write_text(stream.getvalue(),
                                             encoding="utf-8")
    receipt = {
        "schema": "baton.independent-review-verification/1",
        "work": "W239533", "claim": 247666, "participant": "baton.claude",
        "modules": list(MODULES),
        "checks": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "measured_seconds": elapsed,
        "python": os.sys.version.split()[0],
        "owned": {name: sha(str(HERE / name)) for name in OWNED},
        "reused": {name: sha(str(place)) for name, place in
                   sorted(REUSED.items())},
        "log": "verification-7.log",
        "note": "focused deterministic verification of the ATTACHMENT "
                "boundary and the review COMPOSITION, read through "
                "ControlStore.open_readonly and one coherent snapshot. No "
                "container, image, live provider, network, credential or "
                "operator deployment. The bounded review supervisor and the "
                "documented command is driven through write and "
                "held_configuration on disposable supported stores, and the "
                "packet it writes is held by the supervisor's own validator. "
                "The supervisor's imported machinery is W239528's, bound by "
                "digest and proved by that Job's suite rather than here.",
    }
    (HERE / "verification-7.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({one: receipt[one] for one in
                      ("checks", "failures", "errors", "skipped",
                       "measured_seconds")}, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
