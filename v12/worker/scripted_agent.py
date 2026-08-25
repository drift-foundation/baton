"""The DETERMINISTIC scripted M2 agent.

Not a provider, and not a stand-in for one. M2 proves the isolation topology --
that a consent container cannot reach execution state, that teardown is
positive, that the channel is bounded -- and a live provider would make every
one of those proofs depend on somebody else's model. Provider-native code stays
opaque inside a worker image and live certification belongs to M4; the record
says so and this file is what that decision looks like.

DETERMINISTIC MEANS DERIVED, NOT RANDOM AND NOT FIXED. The answers come from
the request, so a fixture can assert an exact result without this pretending to
think, and two runs of the same assignment produce the same bytes -- which is
what makes a reproducibility case possible at all.
"""

import hashlib
import json

__all__ = ["ScriptedAgent"]

MAX_RECAP = 4000


def _digest(value):
    return "sha256:" + hashlib.sha256(
        json.dumps(value, sort_keys=True,
                   separators=(",", ":")).encode("utf-8")).hexdigest()


class ScriptedAgent:
    """Consent and execution, both decided from what was asked."""

    def consider(self, seen, request):
        """Answer `accept` or `decline` -- and NOTHING ELSE.

        A consent answer carries no workspace path, no output and no plan: the
        container it comes from has none of those, and an answer that named
        one would be describing something the worker cannot see.

        The decision is scripted on the contract's own text so a fixture can
        drive both outcomes without this file carrying a switch nobody can
        justify: a contract that says it is unacceptable is declined.
        """
        contract = seen.get("BATON_WORKER_CONTRACT", "")
        decision = "decline" if "decline" in contract.lower() else "accept"
        return {"decision": decision,
                "contract_digest": _digest(contract),
                "reason": ("the contract asks for a decline"
                           if decision == "decline"
                           else "the contract is acceptable")}

    def work(self, seen, request):
        """Do the scripted work and RECAP it, bounded.

        The recap is the only prose an execution worker emits, and it is
        truncated here rather than at the channel, so the worker reports what
        it did instead of the channel reporting that the worker said too much.
        """
        task = request.get("task")
        if type(task) is not str:
            raise ValueError("a work request names one task")
        # THE ANSWER IS EXACTLY WHAT THE CONTRACT PINS: `disposition`,
        # `workspace`, `recap`. Review [P1]: this also returned a
        # `task_digest`, which the closed answer set does not name -- a member
        # the worker boundary would have had to refuse, and which said nothing
        # a manager holding the task could not compute for itself.
        #
        # The task still DECIDES the answer, which is what deterministic
        # means here: the recap is derived from it, so two runs of the same
        # assignment produce the same bytes.
        recap = f"scripted worker completed {task}"[:MAX_RECAP]
        return {"disposition": "completed",
                "workspace": seen.get("BATON_WORKER_WORKSPACE"),
                "recap": recap}
