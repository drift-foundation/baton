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
import os

__all__ = ["ScriptedAgent"]

MAX_RECAP = 4000

# The writable root of the two W14251 fixes. Named here as well as in the
# worker because this file writes into it, and a path it took from an operand
# would be a path a payload could redirect.
OUTPUT_ROOT = "/output"


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
        # W26291: THE LAUNCH DOCUMENT'S OWN MEMBER NAME. `seen` used to be the
        # four `BATON_WORKER_*` values; it is now the validated launch
        # document without its schema, so what an agent reads is a member of a
        # versioned contract rather than a variable somebody set.
        contract = seen.get("contract", "")
        decision = "decline" if "decline" in contract.lower() else "accept"
        return {"decision": decision,
                "contract_digest": _digest(contract),
                "reason": ("the contract asks for a decline"
                           if decision == "decline"
                           else "the contract is acceptable")}

    def work(self, seen, declared):
        """Write the declared outputs and say WHICH of them were produced.

        W14251, closed. The agent no longer receives an inline task and no
        longer reports a workspace: it is handed the DECLARATIONS the manager
        wrote, it writes its material under each declared path below
        `/output/`, and it answers which outputs exist.

        IT SAYS NOTHING ABOUT THE BYTES. The worker measures them, because a
        content manifest is a claim about a tree and this file is the least
        trusted thing inside the container. So an agent cannot describe
        material it did not write, and cannot rename or move an output either
        -- everything but `name`, `status` and the opaque `result_metadata`
        comes from the declaration.

        DETERMINISTIC MEANS DERIVED, still. The bytes come from the
        declaration, so two runs of the same assignment produce the same tree
        and a reproducibility case is possible at all.
        """
        answers = []
        produced = []
        for one in declared:
            place = os.path.join(OUTPUT_ROOT, one["path"])
            os.makedirs(place, exist_ok=True)
            body = f"scripted worker produced {one['name']}\n"
            with open(os.path.join(place, "result.txt"), "w",
                      encoding="utf-8") as handle:
                handle.write(body)
            produced.append(one["name"])
            answers.append({
                "name": one["name"], "status": "present",
                # OPAQUE, and empty is the honest value. A worker with nothing
                # format-specific to say says nothing; the manager carries this
                # and never reads it either way.
                "result_metadata": {}})
        recap = ("scripted worker produced "
                 + ", ".join(produced))[:MAX_RECAP]
        return {"disposition": "completed", "outputs": answers,
                "recap": recap}
