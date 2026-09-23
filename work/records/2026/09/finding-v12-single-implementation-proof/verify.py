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
SOURCE = HERE.parent / "finding-v12-managed-session-resume"
MODULES = ("test_baseline", "test_baseline_bindings",
           "test_entrypoints", "test_failure_path",
           "test_successor_snapshot", "test_no_progress",
           "test_successor_packet", "test_preparation")
OWNED = ("baseline.py", "baseline_bindings.py", "test_baseline.py",
         "test_baseline_bindings.py", "test_entrypoints.py",
         "test_failure_path.py", "test_successor_snapshot.py",
         "snapshot_242687.py", "test_no_progress.py",
         "prepare_instance.py", "test_preparation.py",
         "test_successor_packet.py", "verify.py")
# THE ANCESTOR BYTES. `baseline.py` and `baseline_bindings.py` are W236087's
# programs reduced to one stage; recording the digests they were taken from is
# what makes "derived from" checkable instead of asserted.
ANCESTORS = ("supervisor.py", "packet_bindings.py", "test_supervisor.py",
             "test_packet_bindings.py", "test_generated_packet.py")


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
    body = stream.getvalue()
    (HERE / "verification-11.log").write_text(body, encoding="utf-8")
    receipt = {
        "schema": "baton.single-implementation-verification/1",
        "work": "W239528", "claim": 244389, "participant": "baton.claude",
        "modules": list(MODULES),
        "checks": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "measured_seconds": elapsed,
        "python": os.sys.version.split()[0],
        "owned": {name: sha(str(HERE / name)) for name in OWNED},
        "derived_from": {name: sha(str(SOURCE / name)) for name in ANCESTORS},
        "log": "verification-11.log",
        "note": "focused deterministic verification; engine and provider "
                "subprocess are the two accepted seams. No container, image, "
                "live provider, network, credential or operator deployment.",
    }
    (HERE / "verification-11.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({one: receipt[one] for one in
                      ("checks", "failures", "errors", "skipped",
                       "measured_seconds")}, indent=2))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
