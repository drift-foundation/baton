"""Show what the submitted lost-claim fixture actually drives."""

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import submit_claim
from tests.manager.test_offers import TheClaimAndItsSettlement


case = TheClaimAndItsSettlement(
    "test_the_injected_claim_answer_is_owned_before_recording")
case.setUp()
try:
    case.issue()
    case.accept()
    case.session.claim_answer = None
    try:
        submit_claim(case.store, case.port, offer_id="offer-1")
    except ContractRefusal as refusal:
        print("None claim answer ->", refusal.category, refusal.code)
        print("reason:", refusal.message)
        assert (refusal.category, refusal.code) == ("integrity", "schema")
    else:
        raise AssertionError("None was accepted as a claim answer")
    print("offer state after malformed answer:", case.row()["state"])
    assert case.row()["state"] == "accepted"
finally:
    case.doCleanups()
