"""The reviewer's four counterexamples, re-asked of the corrected owners.

`review-133787-probe.py` is preserved unchanged; this deliberately keeps its
four scenario NAMES so the two answers can be read side by side. Where that
probe recorded a success that should not have been possible, this records the
refusal that now happens and the sentence it happens with.

Bounded, disposable real Git repositories, a real IntegrationStore and a real
Authority. No live coordination database. No application or test file is
changed by this script.
"""
import json
import sys

sys.path.insert(0, "/home/sl/src/baton/v12/python/src")
sys.path.insert(0, "/home/sl/src/baton/v12/python")

from baton_v12.contracts import ContractRefusal  # noqa: E402
from baton_v12.integration import reconciliation as r  # noqa: E402
from tests.integration.test_reconciliation import (  # noqa: E402
    INTEGRATOR, RESULT_OWNERS, Owner, ResultCase)

results = {}


def run(name, probe):
    case = ResultCase()
    try:
        case.setUp()
        results[name] = probe(case)
    finally:
        case.doCleanups()


def refusal(action):
    try:
        answer = action()
    except ContractRefusal as caught:
        return {"refused": True, "category": caught.category,
                "code": caught.code, "message": caught.message}
    except Exception as caught:           # the store's own integrity refusal
        return {"refused": True, "category": type(caught).__name__,
                "code": "store", "message": str(caught)}
    return {"refused": False, "accepted": repr(answer)[:200]}


def unproved_sources_and_owner_evidence(case):
    """WAS: proposal `never-published`, a checkpoint and verdict nobody made,
    unconfigured verifier/approver and the PREPARER as its own reviewer, all
    the way to a real derived publication and a resolved import account."""
    answers = {"forged_proposal": refusal(
        lambda: case.prepare(proposal_id="never-published"))}
    held = case.prepare()
    itself = dict(case.owners)
    itself["review"] = Owner(INTEGRATOR, "review")
    answers["preparer_reviews_itself"] = refusal(
        lambda: case.authorize(held, owners=itself))
    unconfigured = dict(case.owners)
    unconfigured["verification"] = type("Unconfigured", (), {
        "participant": "unconfigured.verifier"})()
    answers["unconfigured_owner"] = refusal(
        lambda: case.authorize(held, owners=unconfigured))
    answers["honest_owners_authorize"] = case.authorize(held)["state"]
    answers["recorded_actors"] = {
        kind: one["actor"] for kind, one in
        r.result_of(case.store, held["result_id"])["evidence"].items()}
    return answers


def different_bytes_reuse_passed_evidence(case):
    """WAS: two combined trees over the same four paths shared one content
    digest, so the first result's passing judgements authorized the second,
    failing one."""
    first = case.prepare()
    passed = case.observations(first)
    case.authorize(first, observations=passed)
    case.advance("scale.py", "SCALE = 2\n")
    second = case.prepare()
    failed = case.observations(second)
    stale = {kind: Owner(RESULT_OWNERS[kind], kind, about={
        "content_digest": first["content_digest"],
        "candidate": first["prepared"]["head"]}) for kind in RESULT_OWNERS}
    return {
        "first_tree": first["prepared"]["tree"],
        "second_tree": second["prepared"]["tree"],
        "first_content_digest": first["content_digest"],
        "second_content_digest": second["content_digest"],
        "digests_differ": first["content_digest"] != second["content_digest"],
        "first_observation_status": passed["combined"]["status"],
        "second_observation_status": failed["combined"]["status"],
        "reusing_the_first_results_evidence": refusal(
            lambda: case.authorize(second, owners=stale,
                                   observations=failed)),
        "honest_owners_on_a_failing_combination": refusal(
            lambda: case.authorize(second, observations=failed)),
        "second_state": r.result_of(case.store, second["result_id"])["state"],
    }


def later_state_journal_binding(case):
    """WAS: an authorized row accepted a prepared head/tree nothing holds, a
    published row accepted emptied evidence, and `imported` with no entry
    read back as a terminal record."""
    held = case.authorize(case.prepare())
    result_id = held["result_id"]
    raw = case.row(result_id, "prepared")
    edited = json.loads(raw)
    edited["head"] = "f" * 40
    edited["tree"] = "e" * 40
    case.edit(result_id, "prepared", json.dumps(edited))
    answers = {"prepared_edited_under_authorized": refusal(
        lambda: r.result_of(case.store, result_id))}
    case.edit(result_id, "prepared", raw)
    published = case.publish(held)
    case.edit(result_id, "evidence", "{}")
    answers["evidence_emptied_under_published"] = refusal(
        lambda: r.result_of(case.store, result_id))
    answers["import_account_on_emptied_evidence"] = refusal(
        lambda: case.import_account(published))
    case.edit(result_id, "evidence",
              json.dumps(published["evidence"], sort_keys=True))
    answers["restored_row_reads_again"] = (
        r.result_of(case.store, result_id)["state"] == "published")
    answers["invented_imported_state"] = refusal(
        lambda: case.edit(result_id, "state", "imported"))
    answers["state_after_the_attempt"] = case.row(result_id, "state")
    return answers


def exact_retries_after_progress(case):
    """WAS: an exact `prepare_result` retry and an identical evidence retry
    both refused once the record had been authorized."""
    held = case.prepare()
    authorized = case.authorize(held)
    answers = {
        "prepare_after_authorize":
            "replayed" if case.prepare() == authorized else "DIFFERENT",
        "same_evidence_retry":
            "replayed" if case.authorize(authorized) == authorized
            else "DIFFERENT",
    }
    published = case.publish(authorized)
    answers["prepare_after_publish"] = (
        "replayed" if case.prepare() == published else "DIFFERENT")
    answers["evidence_retry_after_publish"] = (
        "replayed" if case.authorize(published) == published else "DIFFERENT")
    different = dict(case.owners)
    different["review"] = Owner("baton.another-reviewer", "review")
    answers["a_CHANGED_retry_still_collides"] = refusal(
        lambda: case.authorize(published, owners=different))
    return answers


run("unproved_sources_and_owner_evidence", unproved_sources_and_owner_evidence)
run("different_bytes_reuse_passed_evidence", different_bytes_reuse_passed_evidence)
run("later_state_journal_binding", later_state_journal_binding)
run("exact_retries_after_progress", exact_retries_after_progress)

print(json.dumps(results, indent=2))
one = results["unproved_sources_and_owner_evidence"]
two = results["different_bytes_reuse_passed_evidence"]
three = results["later_state_journal_binding"]
four = results["exact_retries_after_progress"]
ok = (one["forged_proposal"]["refused"]
      and one["preparer_reviews_itself"]["refused"]
      and one["unconfigured_owner"]["refused"]
      and one["honest_owners_authorize"] == "authorized"
      and two["digests_differ"]
      and two["reusing_the_first_results_evidence"]["refused"]
      and two["honest_owners_on_a_failing_combination"]["refused"]
      and two["second_state"] == "prepared"
      and three["prepared_edited_under_authorized"]["refused"]
      and three["evidence_emptied_under_published"]["refused"]
      and three["import_account_on_emptied_evidence"]["refused"]
      and three["restored_row_reads_again"]
      and three["invented_imported_state"]["refused"]
      and three["state_after_the_attempt"] == "published"
      and all(four[name] == "replayed" for name in
              ("prepare_after_authorize", "same_evidence_retry",
               "prepare_after_publish", "evidence_retry_after_publish"))
      and four["a_CHANGED_retry_still_collides"]["refused"])
print("\nCORRECTIONS:", "OK" if ok else "NOT OK")
sys.exit(0 if ok else 1)
