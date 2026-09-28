import collections, subprocess, sys, unittest
from unittest import mock
from tests.tools.test_managed_apply import AnOrdinaryManagedIntegration
launches = collections.Counter()
verbs = collections.Counter()
original = subprocess.Popen
def popen(args, *a, **kw):
    if isinstance(args, (list, tuple)) and "-c" in args:
        code = args[args.index("-c")+1]
        if "integration_entry.main" in code: launches["apply_body"] += 1
        elif "reconciliation_entry.main" in code: launches["prepare_body"] += 1
    return original(args, *a, **kw)
def trace(frame, event, arg):
    if event == "call" and frame.f_code.co_filename.endswith("test_managed_apply.py") and frame.f_code.co_name == "engine":
        argv = frame.f_locals["argv"]
        if argv[1] in ("create", "start", "run"):
            verbs[argv[1]] += 1
    return None
sys.settrace(trace)
with mock.patch.object(subprocess, "Popen", popen):
    result = unittest.TextTestRunner().run(unittest.TestSuite([AnOrdinaryManagedIntegration("test_preparation_judgments_apply_and_target_settle")]))
sys.settrace(None)
print("APPLY_WRAPPER_VERBS", dict(verbs))
print("LAUNCHED_BODIES", dict(launches))
sys.exit(not result.wasSuccessful())
