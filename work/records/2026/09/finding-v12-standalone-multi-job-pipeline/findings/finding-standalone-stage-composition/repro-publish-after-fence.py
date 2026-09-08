"""Minimal W103068 reproduction: an ended producer cannot publish.

Run from the repository root with:

    PYTHONPATH=v12/python/src ./.venv/bin/python3 \
      work/records/2026/09/finding-v12-standalone-multi-job-pipeline/findings/finding-standalone-stage-composition/repro-publish-after-fence.py
"""

import os
import tempfile

from baton_v12.authority import Authority, Refusal, V12


UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W1"
PARTICIPANT = "baton.claude"


with tempfile.TemporaryDirectory(prefix="w103068-", dir="/tmp") as root:
    authority = Authority.create(
        os.path.join(root, "authority.sqlite3"), authority_uuid=UUID,
        clock=lambda: "2026-09-06T00:00:00.000Z")
    try:
        core = authority._core
        core.create_work(WORK, "impl", contract=V12, operation_id="create")
        core.add_route_handler("impl", PARTICIPANT)
        assignment = core.claim(
            WORK, PARTICIPANT, operation_id="claim")["assignment"]
        core.cancel(assignment, operation_id="checkpoint-fence",
                    reason="review checkpoint writer completed")
        try:
            core.publish(
                assignment, operation_id="publish", proposal_id="proposal-1",
                result_id="result-1", result_digest="sha256:result",
                candidate_digest="sha256:candidate",
                input_digest="sha256:input", policy_digest="sha256:policy")
        except Refusal as refused:
            print(f"{type(refused).__name__}: {refused}")
        else:
            raise AssertionError("publication after the producer fence succeeded")
    finally:
        authority.dispose()
