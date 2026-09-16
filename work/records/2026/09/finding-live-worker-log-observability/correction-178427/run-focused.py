"""W61599 deterministic correction checks; no discovery or live runtime."""
import importlib
import json
from pathlib import Path
import sys
import threading
import time
import unittest

ROOT = Path(__file__).resolve().parents[6]
PACKET = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src"), str(ROOT / "v12/worker"), str(ROOT / "v12/python/src/baton_v12")]
mode = sys.argv[1]
REGRESSIONS = [
    "tests.manager.test_claude_agent.TheNativeSessionActivityObservation.test_a_replaced_root_link_never_counts_foreign_activity",
    "tests.manager.test_claude_agent.TheNativeSessionActivityObservation.test_a_directory_replaced_before_scanning_cannot_redirect_the_scan",
    "tests.manager.test_claude_agent.TheNativeSessionActivityObservation.test_directory_acquisition_rejects_replacement_and_closes_descriptors",
    "tests.manager.test_exchange.TheWorkerPublishesTheOptionalCount.test_a_blocked_publisher_is_abandoned_within_its_bound",
    "tests.tools.test_single_worker.TheActivityAdmissionExcludesASecondHelperPerStore.test_repeated_stops_keep_the_live_thread_handle_and_store",
    "tests.tools.test_single_worker.TheBootstrapCompositionOwnsOneIngestionHelper.test_the_serving_loops_runtime_read_enqueues_and_reads_no_file",
]
FOCUSED = [
    "tests.manager.test_claude_agent.TheNativeSessionActivityObservation",
    "tests.manager.test_exchange.TheOptionalActivityDocument",
    "tests.manager.test_exchange.TheWorkerPublishesTheOptionalCount",
    "tests.tools.test_single_worker.TheActivityAdmissionExcludesASecondHelperPerStore",
    "tests.tools.test_single_worker.TheActivityHelperIngestsOffTheServingLoop",
    "tests.tools.test_single_worker.TheBootstrapCompositionOwnsOneIngestionHelper",
    "tests.tools.test_stage_execution.TheStagedDeploymentOwnsOneIngestionHelper",
]
if mode == "baseline":
    # Bind the exact retained starting product bytes in memory. Never swap
    # working-tree files or associate old aggregate runs with these tests.
    for name, relative in [
        ("claude_agent", "v12/worker/claude_agent.py"),
        ("baton_worker", "v12/worker/baton_worker.py"),
        ("tools.single_worker", "v12/python/tools/single_worker.py"),
    ]:
        module = importlib.import_module(name)
        source = PACKET / "base" / relative
        exec(compile(source.read_bytes(), str(source), "exec"), module.__dict__)
started = time.monotonic()
suite = unittest.defaultTestLoader.loadTestsFromNames(FOCUSED if mode == "focused" else REGRESSIONS)
result = unittest.TextTestRunner(verbosity=2).run(suite)
# All selected fixtures must release their blockers and join their owned
# threads. Wait a short grace only to observe already-requested finalization.
deadline = time.monotonic() + 5
while time.monotonic() < deadline:
    live = [t for t in threading.enumerate() if t is not threading.main_thread()]
    if not live:
        break
    for thread in live:
        thread.join(0.05)
receipt = {"mode": mode, "tests": result.testsRun,
           "failures": [t.id() for t, _ in result.failures],
           "errors": [t.id() for t, _ in result.errors],
           "elapsed_seconds": time.monotonic() - started,
           "live_threads": [{"name": t.name, "ident": t.ident} for t in live]}
print(json.dumps(receipt, sort_keys=True), flush=True)
raise SystemExit(0 if result.wasSuccessful() and not live else 1)
