"""Log actual connected cleanup refusals; fake provider/engine fixture only."""
import runpy
from pathlib import Path
from unittest import mock
from baton_v12.job_manager import review_driver
original = review_driver.authorize_cleanup
seen = set()
def traced(*a, **kw):
    try:
        return original(*a, **kw)
    except Exception as failure:
        answer = repr(failure)
        if answer not in seen:
            print("CLEANUP REFUSAL:", answer)
            seen.add(answer)
        raise
with mock.patch.object(review_driver, "authorize_cleanup", traced):
    runpy.run_path(str(Path(__file__).with_name("review_fresh_diagnostic_20260928.py")))
