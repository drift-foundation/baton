"""Independent control-flow probes; controlled Git/profile/grant doubles, no real target writes."""
import json
from unittest.mock import patch
from baton_v12.integration import execution

CANDIDATE = "c" * 40
ACCEPTED_BASE = "a" * 40
DRIFTED = "b" * 40

class Profile:
    def __init__(self, revision):
        self.current = revision
        self.swaps = []
    def revision(self, target, reference):
        return self.current
    def held(self, target, candidate, what):
        return {"commit": candidate, "tree": "d" * 40}
    def advance(self, target, *, reference, imported, reviewed):
        self.swaps.append({"reviewed": reviewed, "imported": imported})
        assert self.current == reviewed
        self.current = imported
        return imported

def run_case(name, initial, revoke_on_delivery=False):
    profile = Profile(initial)
    state = {"live": True, "grant_reads": 0, "deliveries": 0}
    def grant(*args, **kwargs):
        state["grant_reads"] += 1
        if not state["live"]:
            raise RuntimeError("the grant ended")
        return {"state": "live"}
    def runner(argv):
        state["deliveries"] += 1
        if revoke_on_delivery:
            state["live"] = False
        return {"returncode": 0, "stdout": "", "stderr": ""}
    with patch.object(execution, "live_grant", grant):
        answer = execution.finalize_direct_target(
            object(), profile, runner, canonical_target_id="target-a",
            entry_id="entry-a", lease_id="lease-a", fence=1,
            source="/controlled/source", candidate=CANDIDATE,
            target_root="/controlled/target", reference="refs/baton/target")
    return {"case": name, "accepted_base": ACCEPTED_BASE,
            "initial_reference": initial, "final_reference": profile.current,
            "state": state, "swaps": profile.swaps, "answer": answer}

answers = [run_case("reference-already-drifted-before-call", DRIFTED),
           run_case("grant-ended-during-delivery", ACCEPTED_BASE, True),
           run_case("candidate-reference-skips-grant-proof", CANDIDATE)]
assert answers[0]["swaps"][0]["reviewed"] == DRIFTED
assert answers[1]["state"]["live"] is False and answers[1]["final_reference"] == CANDIDATE
assert answers[1]["state"]["grant_reads"] == 1
assert answers[2]["state"]["grant_reads"] == 0
print(json.dumps({"boundary": "production finalizer with controlled profile, runner and grant reader; no real Git/Authority", "observations": answers}, indent=2))
