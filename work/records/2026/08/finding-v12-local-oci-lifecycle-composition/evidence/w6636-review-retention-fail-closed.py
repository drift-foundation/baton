"""Reproduce two fail-open retention endings after the first P0 correction."""

import os

from tests.manager.test_sealing import RetentionEnactsTheDispositionOverCustody


def case():
    one = RetentionEnactsTheDispositionOverCustody(
        "test_discard_after_intake_removes_the_custody_bytes")
    one.setUp()
    return one


unknown = case()
try:
    adapter, command, _collected = unknown.held(
        disposition="not-a-retention-disposition")
    place = unknown.place(adapter)
    answer = adapter.retain(command)
    print("unknown disposition answer:", answer)
    print("unknown disposition destroyed custody:", not os.path.exists(place))
    assert not os.path.exists(place)
finally:
    unknown.doCleanups()


missing = case()
try:
    adapter, command, _collected = missing.held(disposition="retain")
    place = missing.place(adapter)
    from baton_v12.worker_manager import workspaces
    workspaces.discard_tree(place)
    assert not os.path.exists(place)
    answer = adapter.retain(command)
    print("retain over absent custody answer:", answer)
    print("retained custody exists:", os.path.exists(place))
    assert answer == {"delivered": True, "discarded": []}
finally:
    missing.doCleanups()
