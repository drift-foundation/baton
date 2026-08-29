"""W16821 — the principal/scope seam, MEASURED BY REMOVAL.

Every rule this correction claims to add is removed from the production
source, the case that claims to establish it is re-run, and the case is
required to FAIL.  A guard nothing observes is not established, and a suite
that passes with the guard deleted is a suite that measured its own fixture.

It rewrites source files in place and restores each one before the next, and
prints the before/after digest of every file it touched so the restoration is
checked rather than asserted.  No Git history or index is touched.

Run from `v12/python`: `PYTHONPATH=src python3 <this file>`.
"""

import hashlib
import os
import pathlib
import subprocess
import sys

REPO = pathlib.Path("/home/sl/src/baton")
SRC = REPO / "v12/python/src/baton_v12/authority"
SUITE = "tests.authority.test_principal_scope"

MUTATIONS = [
    ("capacity: the claim slot is keyed by the ENDPOINT again",
     SRC / "core.py",
     '''        principal = self._register_principal(decision.principal)
        held = self.slot_holder_of_principal(principal)''',
     '''        principal = self._register_principal(
            principal_for_endpoint(decision.endpoint))
        held = self.slot_holder_of_principal(principal)''',
     "OnePrincipalTwoAddresses"),

    ("capacity: the slot READ answers by address instead of by principal",
     SRC / "core.py",
     '''            "SELECT work_id FROM claim_slot WHERE principal_id = ?",
            self.principal_of(participant))''',
     '''            "SELECT work_id FROM claim_slot WHERE participant = ?",
            participant)''',
     "OnePrincipalTwoAddresses.test_the_slot_is_visible_through_either_address"),

    ("mapping: an endpoint holding a live claim may be rebound",
     SRC / "core.py",
     '''            if held is not None:
                raise Refusal(
                    f"{name_of(participant)} holds a live claim on "''',
     '''            if False:
                raise Refusal(
                    f"{name_of(participant)} holds a live claim on "''',
     "OnePrincipalTwoAddresses.test_an_endpoint_holding_a_claim_cannot_be_rebound"),

    ("grants: a capability is held by the ENDPOINT again",
     SRC / "core.py",
     '''            row = self._store.get(
                "SELECT provenance FROM capability WHERE principal_id = ? AND "
                "capability = ? AND scope = ?",
                principal, capability, effective)''',
     '''            row = self._store.get(
                "SELECT provenance FROM capability WHERE principal_id = ? AND "
                "capability = ? AND scope = ?",
                principal_for_endpoint(participant), capability, effective)''',
     "OnePrincipalTwoAddresses.test_one_principal_grants_reach_every_address_it_holds"),

    ("scope: the claim decides in the deployment scope rather than the Work's",
     SRC / "core.py",
     '''            decision = self.authorize(participant, route=work["route"],
                                      scope=work["scope"])''',
     '''            decision = self.authorize(participant, route=work["route"])''',
     "NothingAnOperandSaysCanWidenIt.test_the_effective_scope_comes_off_the_work_and_not_the_caller"),

    ("scope: a grant in one scope authorizes every scope",
     SRC / "core.py",
     '''                "SELECT provenance FROM capability WHERE principal_id = ? AND "
                "capability = ? AND scope = ?",
                principal, capability, effective)''',
     '''                "SELECT provenance FROM capability WHERE principal_id = ? AND "
                "capability = ?", principal, capability)''',
     "NothingAnOperandSaysCanWidenIt.test_a_grant_in_one_scope_does_not_authorize_another"),

    ("provenance: this cut hands out a grant kind it cannot resolve",
     SRC / "principals.py",
     '''M2_GRANTS = (DIRECT,)''',
     '''M2_GRANTS = GRANTS''',
     "GrantProvenance"),

    # RE-ANCHORED.  The first cut wrote four nullable columns on the event
    # row; the corrected shape retains one decision keyed by the act, so the
    # mutation is the removal of that retention.  The harness reported the
    # old anchors as STALE rather than passing them, which is the point of
    # an anchor check.
    ("evidence: the claim retains no decision",
     SRC / "core.py",
     '''            self._record_decision(
                "claim",
                str(self._store.get("SELECT MAX(seq) AS seq FROM "
                                    "assignment_event")["seq"]),
                decision)''',
     '''            pass''',
     "TheDecisionRidesTheAct.test_a_claim_records_endpoint_principal_scope_grant_and_generation"),

    ("evidence: a receipt retains no decision",
     SRC / "core.py",
     '''            self._record_decision(kind, receipt_id, decision)''',
     '''            pass''',
     "GrantProvenance.test_a_receipt_carries_the_decision_beside_its_actor"),

    ("generation: a configuration act leaves the generation where it was",
     SRC / "core.py",
     '''    def _bump_policy_generation(self):''',
     '''    def _bump_policy_generation(self):
        return''',
     "TheDecisionRidesTheAct.test_every_configuration_act_advances_the_generation"),

    ("decision: a caller may edit the provenance it was handed",
     SRC / "principals.py",
     '''    def __setattr__(self, name, value):
        raise Refusal("an authorization decision is immutable")''',
     '''    def __setattr__(self, name, value):
        object.__setattr__(self, name, value)''',
     "TheDecisionRidesTheAct.test_a_decision_cannot_be_edited_after_it_is_answered"),

    ("boundary: a store of another schema version is adopted",
     SRC / "store.py",
     '''    version = recorded.get(META_SCHEMA_VERSION)
    if version != str(SCHEMA_VERSION):''',
     '''    version = recorded.get(META_SCHEMA_VERSION)
    if False:''',
     "SchemaTwoIsACleanInitializationBoundary"),

    ("boundary: the configuration generation is rewound on every open",
     SRC / "core.py",
     '''        row = self._store.get("SELECT generation FROM policy_generation")
        return 1 if row is None else row["generation"]''',
     '''        self._store.get("SELECT generation FROM policy_generation")
        return 1''',
     "SchemaTwoIsACleanInitializationBoundary.test_reopening_a_store_does_not_rewind_its_configuration_generation"),

    ("grammar: a participant address is accepted as a principal",
     SRC / "principals.py",
     '''    if not _well_formed(value, PRINCIPAL_PREFIX):''',
     '''    if False:''',
     "NothingAnOperandSaysCanWidenIt.test_a_participant_address_is_refused_where_a_principal_is_required"),

    # ---------------------------------------------------------------------
    # The six boundaries the first mutation pass did not cover, named by
    # review 2026-08-28T20:54:18Z.
    # ---------------------------------------------------------------------
    ("target scope: a receipt decides in the deployment scope again",
     SRC / "core.py",
     '''                scope=self._scope_of(proposal))''',
     '''                scope=None)''',
     "EveryCapabilityDoorDecidesInTheTargetsScope"),

    ("target scope: a close decides in the deployment scope again",
     SRC / "core.py",
     '''            decision = self._require_capability(actor, "close", "close",
                                                scope=work["scope"])''',
     '''            decision = self._require_capability(actor, "close", "close",
                                                scope=None)''',
     "EveryCapabilityDoorDecidesInTheTargetsScope.test_close_decides_in_the_works_own_scope"),

    ("close: the decision is not retained",
     SRC / "core.py",
     '''            self._record_decision("close", work_id, decision)''',
     '''            pass''',
     "TheDecisionIsRetainedForEveryAuthorizedAct.test_an_unclaimed_close_retains_and_projects_its_decision"),

    ("claim: the public projection discards the decision again",
     SRC / "core.py",
     '''                "decision": self._decision("claim", str(row["seq"])),''',
     '''''',
     "TheDecisionRidesTheAct.test_a_claim_records_endpoint_principal_scope_grant_and_generation"),

    # RE-ANCHORED: the join it targeted is gone, replaced by the row's own
    # exact reference.  The equivalent removal is the projection refusing to
    # read that reference at all.
    ("assignment-derived acts: the link to the claim is dropped",
     SRC / "core.py",
     '''        return self._decision("claim", str(row["claim_seq"]))''',
     '''        return None''',
     "TheDecisionIsRetainedForEveryAuthorizedAct.test_an_assignment_derived_act_exposes_the_claim_it_ran_under"),

    ("the durable refused integration attempt loses its attribution",
     SRC / "core.py",
     '''                self._record_decision("integration-attempt", integration_id,
                                      decision)''',
     '''                pass''',
     "TheDecisionIsRetainedForEveryAuthorizedAct.test_a_durably_refused_integration_attempt_carries_its_decision"),

    ("the grant projection collapses scope and provenance again",
     SRC / "core.py",
     '''        return [{"capability": row["capability"], "scope": row["scope"],
                 "provenance": row["provenance"]}''',
     '''        return [{"capability": row["capability"], "scope": "scope:deployment",
                 "provenance": row["provenance"]}''',
     "TheGrantProjectionCarriesScopeAndProvenance"),

    # ---------------------------------------------------------------------
    # Re-review [P0]: the durable binding between an assignment-derived act
    # and the EXACT claim it was carried out under.
    # ---------------------------------------------------------------------
    ("the exact claim reference is searched for at read time instead",
     SRC / "core.py",
     '''        return self._decision("claim", str(row["claim_seq"]))''',
     '''        found = self._store.get(
            "SELECT seq FROM assignment_event WHERE work_id = ? AND "
            "participant = ? AND IFNULL(generation, -1) = IFNULL(?, -1) AND "
            "cause = 'claimed' ORDER BY seq DESC",
            row["work_id"], row["participant"], row["generation"])
        return None if found is None else self._decision("claim",
                                                         str(found["seq"]))''',
     "AV11ReclaimDoesNotRewriteEarlierHistory"),

    ("the reference is captured at read time rather than at the act",
     SRC / "core.py",
     '''                self._live_claim_seq(expect), key, self._now())''',
     '''                0, key, self._now())''',
     "AV11ReclaimDoesNotRewriteEarlierHistory.test_two_v11_claims_keep_two_distinct_histories"),

    ("an act whose claim was never journalled is written anyway",
     SRC / "core.py",
     '''        if found is None:
            raise Refusal(''',
     '''        if False:
            raise Refusal(''',
     "AV11ReclaimDoesNotRewriteEarlierHistory.test_an_act_that_cannot_name_its_claim_is_refused"),

    ("history is re-derived from today's mapping instead of read",
     SRC / "core.py",
     '''        return {"endpoint": row["endpoint"], "principal": row["principal_id"],''',
     '''        return {"endpoint": row["endpoint"],
                "principal": self.principal_of(row["endpoint"]),''',
     "TheDecisionIsRetainedForEveryAuthorizedAct.test_history_survives_release_reconfiguration_and_close"),
]


def digest(place):
    return hashlib.sha256(place.read_bytes()).hexdigest()[:16]


def run(target):
    finished = subprocess.run(
        [sys.executable, "-m", "unittest",
         f"{SUITE}.{target}" if target else SUITE],
        capture_output=True, timeout=900,
        env={**os.environ, "PYTHONPATH": "src"},
        cwd=str(REPO / "v12/python"))
    return finished.returncode, (finished.stdout + finished.stderr).decode(
        "utf-8", "replace")


def main():
    print("W16821 — THE PRINCIPAL/SCOPE SEAM, MEASURED BY REMOVAL")
    print("=" * 74)
    print()

    code, output = run("")
    baseline = code == 0
    print(f"BASELINE  {'OK' if baseline else 'FAILED'}")
    if not baseline:
        print(output[-2000:])
        return 1
    print()

    caught, uncaught = [], []
    for title, place, old, new, target in MUTATIONS:
        original = place.read_text()
        if old not in original:
            print(f"[ANCHOR] {title}")
            print(f"         the anchor is no longer in {place.name}; this "
                  f"mutation measured NOTHING")
            uncaught.append((title, "stale anchor"))
            continue
        before = digest(place)
        place.write_text(original.replace(old, new, 1))
        try:
            code, output = run(target)
        finally:
            place.write_text(original)
        after = digest(place)
        assert before == after, f"{place} was not restored"
        if code != 0:
            print(f"[caught] {title}")
            print(f"         {target}")
            caught.append(title)
        else:
            print(f"[NOT CAUGHT] {title}")
            print(f"             {target} still passes")
            uncaught.append((title, target))
        print()

    print("=" * 74)
    print(f"caught {len(caught)} of {len(MUTATIONS)}")
    if uncaught:
        print("NOT CAUGHT — each of these is a rule nothing in the suite "
              "measures:")
        for title, why in uncaught:
            print(f"  {title} ({why})")
    return 0 if not uncaught else 1


if __name__ == "__main__":
    raise SystemExit(main())
