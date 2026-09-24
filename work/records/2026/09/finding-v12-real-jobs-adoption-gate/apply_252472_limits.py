"""Claim-252472: the packet declares 180s and the submission never asked for it.

Owner 2026-09-24T00:58Z, from the live run: "It reported provider turn limits
of 3600 seconds from compatibility defaults, rather than the selected 180
seconds."

The launch document this run actually delivered says why, in one member:

    "execution_limits": {"requested": {}, "compatibility_generation": 1,
                         "boundaries": {"provider_turn": {
                             "default_seconds": 3600, "origin": "compatibility",
                             "seconds": 3600}}}

`requested` is EMPTY. `submission.stage_rows` reads each Job's optional
`execution_limits` member and stores it; with none, every boundary resolves to
this build's compatibility defaults. So `two_jobs.LIMITS` declared 180 seconds
per attempt, ADOPTION-247941.md printed it in the limits table, and the
submission I composed asked the manager for nothing at all. The number was a
claim in a document rather than an operand in the packet.

THIS IS THE ONE BOUNDARY THE PACKET OWNS. The other three findings in the
owner's entry -- the agent fault, the settlement failure and the preparation
directory gap -- are separate and are recorded rather than guessed at.
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
PLACE = HERE / "two_jobs.py"

OLD_LIMITS = '''def submission(jobs, *, submission_id, policy_digest):
    from baton_v12.contracts import job_input_identity
'''

NEW_LIMITS = '''# THE CEILINGS THIS PACKET ASKS FOR, in the product's own setting names.
# `documents.JOB_LIMIT_MEMBER` is `execution_limits`, optional on this
# submission schema, and `execution_limits.LIMIT_MEMBERS` names exactly these
# two. A Job that omits it gets the compatibility defaults -- 3600 seconds for
# a provider turn -- which is what the live run of 2026-09-24T00:53Z was
# given while this packet's own table said 180.
def requested_limits():
    """What each Job asks the manager for, derived from `LIMITS`.

    ONE SOURCE. The declared bound and the submitted operand are the same
    number by construction; the defect this corrects is precisely that they
    were two.
    """
    return {"provider_turn_seconds": LIMITS["per_attempt_seconds"],
            "verification_command_seconds": LIMITS["per_attempt_seconds"]}


def submission(jobs, *, submission_id, policy_digest):
    from baton_v12.contracts import job_input_identity
'''

OLD_JOB = '''            "jobs": [{"job_id": one["job_id"],'''

NEW_JOB = '''            "jobs": [{"job_id": one["job_id"],
                      # THE SELECTED CEILINGS, ASKED FOR. Owner
                      # 2026-09-24T00:58Z observed 3600 from compatibility
                      # defaults on a run this packet said was bounded at
                      # 180, and the launch document's `requested: {}` is why.
                      "execution_limits": requested_limits(),'''


def swap(body, old, new, what):
    if body.count(old) != 1:
        raise SystemExit(
            f"REFUSED: {what} appears {body.count(old)} times, not once")
    return body.replace(old, new, 1)


def main():
    body = PLACE.read_text(encoding="utf-8")
    if "def requested_limits(" in body:
        raise SystemExit("REFUSED: the limits are already asked for")
    body = swap(body, OLD_LIMITS, NEW_LIMITS, "the submission head")
    body = swap(body, OLD_JOB, NEW_JOB, "the per-Job document")
    PLACE.write_text(body, encoding="utf-8")

    written = PLACE.read_text(encoding="utf-8")
    for present in ("def requested_limits(", '"execution_limits": '
                    "requested_limits(),", "provider_turn_seconds"):
        if present not in written:
            raise SystemExit(f"REFUSED: {present!r} is not in the file")
    compile(written, str(PLACE), "exec")
    print("the submission asks for the ceilings the packet declares")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
