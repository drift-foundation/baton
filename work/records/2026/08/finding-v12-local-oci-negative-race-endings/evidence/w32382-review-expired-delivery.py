"""Show that the expired-offer case materializes a launch delivery.

Run from ``v12/python`` with ``PYTHONPATH=src:.``. The start refusal occurs at
manager state before the engine, so no OCI daemon is needed.
"""

import os

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import request_runtime_start, settle_claim
from tests.manager.test_negative_race_endings import DockerNegativeEndings
from tests.manager.test_offers import MUCH_LATER


case = DockerNegativeEndings(
    "test_an_expired_offer_creates_no_container_and_no_delivery")
case.setUp()
case.image_digest = "sha256:" + "a" * 64
try:
    given, assignment = case.reserved()
    case.session.settle_answer = {"kind": "retired", "record": {
        "disposition": "settlement-expired",
        "reason": "the settlement deadline passed"}}
    settle_claim(case.store, case.port, offer_id=case.offer, now=MUCH_LATER)
    roots = case.roots()
    inputs = case.composed(roots, given, assignment)
    adapter = case.adapter(roots=roots, mounts=case.plan(roots))
    try:
        request_runtime_start(case.store, adapter, attempt_id=case.attempt,
                              inputs=inputs)
    except ContractRefusal:
        pass
    else:
        raise AssertionError("the expired offer unexpectedly started")
    assert os.path.exists(adapter.launch_delivery.root)
    print("launch delivery still exists:", adapter.launch_delivery.root)
finally:
    case.doCleanups()
