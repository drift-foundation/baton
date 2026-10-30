"""The reviewer's own probe, re-aimed at candidate-362249.

`../review-362222/probe.py` is the counterexample that refused candidate-361943.
This is the same three constructions against the corrected bytes, so the two
outputs can be read side by side. The only differences are the ones the
corrections make necessary:

  * the request's `scope` is now the two members R3 separates, so the third
    construction sets `scope["work"]` where the original set `scope`;
  * the first construction asks `submission_for_admission` for the document
    instead of handing `before["submission"]` straight to `submit`, because
    that verb is the consumption contract R1 required;
  * the second construction expects the assignment itself to fail, because R2
    is answered by freezing the registry rather than by refusing a later
    resolve.

Nothing here writes outside a temporary directory, moves an installed default
or touches a live instance: the generation is moved with `patch` in this
process only, exactly as the reviewer's probe did.
"""

import json
from unittest.mock import patch

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import templates, execution_limits
from baton_v12.job_manager.submission import submit, boundary_seconds
from tests.job_manager.test_templates import (JOB, WORK_SCOPE, configuration,
                                              request)
from tests.job_manager.fixtures import JobManagerCase


def refusal(call):
    try:
        return {"refused": False, "answer": call()}
    except ContractRefusal as caught:
        return {"refused": True, "message": caught.message}


case = JobManagerCase()
case.setUp()
try:
    held = request(template=templates.IMPLEMENTATION_REVIEW)
    before = templates.resolve(held, configuration=configuration())

    newer = dict(execution_limits.GENERATIONS[1])
    newer["provider_turn"] = 7200
    result = {}
    with patch.dict(execution_limits.GENERATIONS, {2: newer}), \
            patch.object(execution_limits, "CURRENT_GENERATION", 2):
        after = templates.resolve(held, configuration=configuration())
        store = case.store()
        result["same_template"] = before["template"] == after["template"]
        result["same_submission"] = (before["submission"]
                                     == after["submission"])
        result["before_provider_seconds"] = (
            before["execution_limits"]["boundaries"]["provider_turn"]
            ["seconds"])
        result["after_provider_seconds"] = (
            after["execution_limits"]["boundaries"]["provider_turn"]
            ["seconds"])
        # R1: the saved resolution is no longer spendable.
        result["saved_resolution_consumption"] = refusal(
            lambda: templates.submission_for_admission(before))
        # And a re-resolved one is, and it tells the truth about the Job.
        taken = templates.submission_for_admission(after)
        submit(store, taken)
        result["re_resolved_submitted_provider_seconds"] = boundary_seconds(
            store, JOB, "provider_turn")
        result["re_resolved_reported_provider_seconds"] = (
            after["execution_limits"]["boundaries"]["provider_turn"]
            ["seconds"])

    # R2: the public lookup cannot be written to, at the exact member the
    # reviewer's probe used.
    definition = templates.template_of(templates.IMPLEMENTATION_REVIEW)
    try:
        definition["completion"]["delivers"] = "not-the-reviewed-proposal"
        result["public_template_lookup_assignment"] = "SUCCEEDED"
    except TypeError as caught:
        result["public_template_lookup_assignment"] = f"TypeError: {caught}"
    result["delivers_after_attempted_mutation"] = templates.resolve(
        held, configuration=configuration())["rules"]["completion"]["delivers"]

    # R3: a product path in the selected work scope is not test_scope.
    held["scope"] = {"work": list(WORK_SCOPE), "tests": []}
    scoped = templates.resolve(held, configuration=configuration())
    result["work_scope"] = scoped["scope"]["work"]
    result["test_scope_in_submission"] = (
        scoped["submission"]["jobs"][0]["test_scope"])

    print(json.dumps(result, indent=2))
finally:
    case.tearDown()
