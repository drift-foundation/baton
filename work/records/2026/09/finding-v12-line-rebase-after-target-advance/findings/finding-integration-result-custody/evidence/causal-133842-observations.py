"""The causal observations AND the corrected authorization, dumped.

Supersedes `causal-133645-observations.py`, which cannot run against the
corrected owners (that script and its retained JSON are kept as the original
history the review asked to preserve, not replaced).

What this shows that the earlier one could not:

1. the same four real harness runs -- base FAIL, isolated PASS, combined PASS,
   and the separate combined-FAIL control;
2. that the two combined trees now have DIFFERENT content digests, which is
   the P1 the review reproduced (they collided before, so one result's passing
   evidence authorized the other's failing bytes);
3. that the combined-fail result cannot be authorized at all -- the failure
   BLOCKS instead of being verified away; and
4. that the observations are retained in the record's own custody and reach
   the import account.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PYTHON = "/home/sl/src/baton/v12/python"
sys.path.insert(0, os.path.join(PYTHON, "src"))
sys.path.insert(0, PYTHON)

from baton_v12.contracts import ContractRefusal  # noqa: E402
from baton_v12.integration import reconciliation  # noqa: E402
from tests.integration.test_reconciliation import (  # noqa: E402
    HARNESS, CausalEvidenceSurvivesComposition)


class Dump(CausalEvidenceSurvivesComposition):
    def runTest(self):
        pass


case = Dump()
case.setUp()
try:
    first = case.prepare()
    observed = case.observations(first)
    authorized = case.authorize(first, observations=observed)
    published = case.publish(authorized)
    account = case.import_account(published)
    answers = {
        "pinned_harness_digest": observed["base"]["test_digest"],
        "submission_base": case.base,
        "target_after_the_first_job": case.advanced,
        "result": {"result_id": first["result_id"],
                   "state": published["state"],
                   "target_revision": first["target_revision"],
                   "prepared_head": first["prepared"]["head"],
                   "prepared_tree": first["prepared"]["tree"],
                   "content": first["prepared"]["content"],
                   "content_digest": first["content_digest"]},
        "observations": observed,
        "evidence_actors": {kind: one["actor"]
                            for kind, one in published["evidence"].items()},
        "derived_proposal": case.authority.proposal(
            published["derived_proposal_id"]),
        "observations_reach_the_import_account":
            account["causal_observations"] == observed,
    }
    # THE SEPARATE COMBINED-FAIL CONTROL. A third Job changes `scale.py`,
    # which Job B never touched, so the merge is clean and the combined
    # result is still wrong.
    moved = case.advance("scale.py", "SCALE = 2\n")
    again = case.prepare()
    failing = case.observations(again)
    try:
        case.authorize(again, observations=failing)
        blocked = "AUTHORIZED -- unexpected"
    except ContractRefusal as refusal:
        blocked = f"refused: {refusal.message}"
    answers["combined_fail"] = {
        "target_after_the_third_job": moved,
        "result_id": again["result_id"],
        "state_after_the_attempt": reconciliation.result_of(
            case.store, again["result_id"])["state"],
        "prepared_head": again["prepared"]["head"],
        "prepared_tree": again["prepared"]["tree"],
        "content_digest": again["content_digest"],
        "observation": failing["combined"],
        "authorization": blocked,
    }
    answers["the_two_trees_no_longer_collide"] = {
        "first_tree": first["prepared"]["tree"],
        "second_tree": again["prepared"]["tree"],
        "first_content_digest": first["content_digest"],
        "second_content_digest": again["content_digest"],
        "digests_differ": first["content_digest"] != again["content_digest"],
    }
finally:
    case.doCleanups()

print(json.dumps(answers, indent=2))
ok = (answers["observations"]["base"]["status"] != 0
      and answers["observations"]["base"]["harness_added"] is True
      and answers["observations"]["isolated"]["status"] == 0
      and answers["observations"]["combined"]["status"] == 0
      and answers["result"]["state"] == "published"
      and answers["observations_reach_the_import_account"]
      and answers["combined_fail"]["observation"]["status"] != 0
      and answers["combined_fail"]["authorization"].startswith("refused")
      and answers["combined_fail"]["state_after_the_attempt"] == "prepared"
      and answers["the_two_trees_no_longer_collide"]["digests_differ"]
      and len({one["test_digest"] for one in
               list(answers["observations"].values())
               + [answers["combined_fail"]["observation"]]}) == 1)
print("\nCAUSAL:", "OK" if ok else "NOT OK")
sys.exit(0 if ok else 1)
