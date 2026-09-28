import collections, sys, unittest
from tests.tools.test_managed_apply import AnOrdinaryManagedIntegration
counts = collections.Counter()
def trace(frame, event, arg):
    if event == "exception" and frame.f_code.co_filename.endswith(("stage_execution.py", "integration_worker.py")):
        typ, value, tb = arg
        if typ.__name__ == "ContractRefusal":
            counts[(frame.f_code.co_name, frame.f_lineno, str(value))] += 1
    return trace
sys.settrace(trace)
result = unittest.TextTestRunner().run(unittest.TestSuite([AnOrdinaryManagedIntegration("test_preparation_judgments_apply_and_target_settle")]))
sys.settrace(None)
for item, count in counts.most_common(12):
    print(count, item)
sys.exit(not result.wasSuccessful())
