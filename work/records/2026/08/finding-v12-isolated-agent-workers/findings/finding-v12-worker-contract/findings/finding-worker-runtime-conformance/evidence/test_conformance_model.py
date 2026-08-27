"""Design-level tests for baton.worker-conformance 1.0.

Provider-free.  Run with "python3 -B -m unittest -q test_conformance_model"
from this directory.

Observations here are SYNTHESIZED from each case's executable expectation, so
a passing run is one whose facts actually satisfy the contract rather than one
that declared itself passing.  Several tests exist purely to show that a
declared pass, unrelated evidence or absent facts cannot certify.
"""

from __future__ import annotations

import copy
import json
import sys
import unittest

from jsonschema import Draft202012Validator

import conformance_model as m

sys.path.insert(0, str(m.SIBLINGS / "finding-acp-agent-boundary" / "evidence"))
import acp_boundary_model as ab  # noqa: E402

# W4487 re-review 2026-08-22: the two contracts that share the claim-token
# verifier are compared HERE, because this is the package whose job is
# cross-contract agreement — it already asserts the shared schema definitions
# are byte-identical rather than trusting two copies to stay in step.
sys.path.insert(0, str(m.SIBLINGS / "finding-worker-control-api-manifests"
                       / "evidence"))
import contract_model as wc  # noqa: E402
sys.path.insert(0, str(m.SIBLINGS.parent.parent
                       / "finding-v12-assignment-state-machine" / "evidence"))
import assignment_state_model as w151  # noqa: E402

WORKER_CONTROL_SCHEMA = json.loads(m.WORKER_CONTROL_SCHEMA_PATH.read_text())
VALIDATOR = Draft202012Validator(m.SCHEMA)

CONTROL_KINDS = set(
    WORKER_CONTROL_SCHEMA["$defs"]["controlEnvelope"]["properties"]["kind"]["enum"])
MANIFEST_SCHEMAS = {
    "baton.worker-manifest/input", "baton.worker-manifest/assignment",
    "baton.worker-manifest/runtime-attempt", "baton.worker-manifest/result",
    # W14251 second review, 2026-08-26: the worker's completion envelope. It is
    # a family in its own right because it has its own AUTHOR -- the frozen
    # result is the manager's receipt, and identifying the two was the defect.
    "baton.worker-manifest/completion",
    "baton.worker-manifest/proposal", "baton.worker-manifest/verification",
    "baton.worker-manifest/verification-assessment",
    "baton.worker-manifest/technical-review", "baton.worker-manifest/approval",
    "baton.worker-manifest/integration",
}
ERROR_PAIRS = {(c, x) for c, xs in ab.WORKER_CONTROL_ERRORS.items() for x in xs}
WORK_REF = {"authority_uuid": "43c55d4b00ee85c84ae4ed134de36df5",
            "work_id": "43c55d4b-W1441"}
def supplemental_case(**overrides):
    base = {
        "suite_family": "baton.worker-conformance", "version": {"major": 1, "minor": 0},
        "document": "case", "case_id": "G-vendor-extra", "family": "G",
        "scope": "runtime-supplemental", "applies_to": ["local-oci", "remote"],
        # No register obligation: this proves an ADDITIONAL property, and the
        # register cannot backlink a case it has never seen.
        "obligations": [], "supplemental_source": "com.example.runtime/1",
        "required_faults": [],
        "stimulus": {"kind": "control-operation", "control_kinds": [], "faults": [],
                     "detail": "Verify the vendor isolation attestation."},
        "expectation": {"kind": "invariant",
                        "requires": [{"fact": "vendor_attestation_verified", "op": "is-true"}]},
        "required_facts": ["vendor_attestation_verified"],
        "deciding_evidence": ["attestation"],
        "statement": "A runtime-specific attestation this vendor also proves."}
    base.update(overrides)
    return m.seal_document(base)


SUPPLEMENTAL = supplemental_case()


def D(pair):
    return "sha256:" + pair * 32


def fixture(profile="local-oci", **overrides):
    remote = profile == "remote"
    base = {
        "suite_family": "baton.worker-conformance",
        "version": {"major": 1, "minor": 0},
        "document": "fixture",
        "fixture_id": "fixture-1",
        "created_at": "2026-08-22T03:50:00.000Z",
        "profile": profile,
        "locality": "remote" if remote else "local",
        "host_identity": {"manager_host_id": "manager-host",
                          "runtime_host_id": "runtime-host" if remote else "manager-host",
                          "workspace_path_resolves_on_manager": not remote},
        "work_ref": copy.deepcopy(WORK_REF),
        "input_manifest_digest": D("a1"),
        "policy_digest": D("a2"),
        "runtime_profile_digest": D("a3"),
        "agent_session_profile_digest": D("a4"),
        "adapter_build_digest": D("a6"),
        "scripted_agent": {"script_digest": D("a5"), "speaks": "acp",
                           "model_provider_required": False},
        "fault_capabilities": sorted(m.FAULT_CAPABILITIES),
        "canaries": [{"surface": s, "canary_id": "canary-" + s, "value_digest": D("b1")}
                     for s in sorted(m.CANARY_SURFACES)],
    }
    base.update(overrides)
    return m.seal_document(base)


# Two clauses can constrain one fact ("equals private-clone" and "not-equals
# canonical"), so the exact operators are applied first and the permissive ones
# only fill facts nobody has pinned.
PINNING = ("equals", "is-true", "is-false", "empty", "subset-of", "disjoint-from")


def satisfying_facts(case):
    """Facts a CONFORMING runtime would produce for this case."""
    facts = {}
    expectation = case["expectation"]
    if expectation["kind"] == "control-refusal":
        facts["refusal"] = copy.deepcopy(expectation["expected_refusal"])

    for pinning in (True, False):
        for predicate in expectation["requires"]:
            name, op = predicate["fact"], predicate["op"]
            if (op in PINNING) != pinning:
                continue
            if not pinning and name in facts:
                continue
            value = predicate.get("value")
            if op == "equals":
                facts[name] = copy.deepcopy(value)
            elif op == "not-equals":
                facts[name] = "something-else" if value != "something-else" else "another-thing"
            elif op == "is-true":
                facts[name] = True
            elif op == "is-false":
                facts[name] = False
            elif op == "present":
                facts[name] = "observed"
            elif op == "absent":
                facts.pop(name, None)
            elif op == "empty":
                facts[name] = []
            elif op == "non-empty":
                facts[name] = ["observed"]
            elif op in ("subset-of", "disjoint-from"):
                facts[name] = []
            else:
                raise AssertionError("unhandled operator " + op)
    return facts


def observation(case, fix, **overrides):
    base = {
        "suite_family": "baton.worker-conformance",
        "version": {"major": 1, "minor": 0},
        "document": "observation",
        "observation_id": "obs-" + case["case_id"],
        "case_id": case["case_id"],
        "fixture_digest": fix["document_digest"],
        "case_digest": case["document_digest"],
        "status": "observed",
        "facts": satisfying_facts(case),
        "blocked_by": None,
        "reason": "scripted conforming runtime",
        "evidence": [{"purpose": purpose,
                      "artifact": {"artifact_id": "art-" + case["case_id"] + "-" + purpose,
                                   "media_type": "application/json",
                                   "bytes": 12, "content_digest": D("cd"),
                                   "locator": "artifact:conformance/1"}}
                     for purpose in case["deciding_evidence"]],
        "observed_at": "2026-08-22T03:55:00.000Z",
    }
    base.update(overrides)
    return m.seal_document(base)


def run(observations, fix, **overrides):
    base = {
        "suite_family": "baton.worker-conformance",
        "version": {"major": 1, "minor": 0},
        "document": "run",
        "run_id": "run-1",
        "created_at": "2026-08-22T03:59:00.000Z",
        "profile": fix["profile"],
        "fixture_digest": fix["document_digest"],
        "obligations_digest": m.OBLIGATIONS_DIGEST,
        "observations": observations,
        "supplemental_cases": [],
    }
    base.update(overrides)
    return m.seal_document(base)


def core_cases(fix):
    core = m.core_for(fix["profile"])
    return [c for c in m.CASES["cases"] if c["case_id"] in core]


def conforming_run(fix, replace=None, **overrides):
    replace = replace or {}
    observations = [replace.get(case["case_id"]) or observation(case, fix)
                    for case in core_cases(fix)]
    return run(observations, fix, **overrides)


# ==========================================================================
# The register composes with the approved contracts
# ==========================================================================

class RegisterTests(unittest.TestCase):
    def test_schema_is_valid_draft_2020_12(self) -> None:
        Draft202012Validator.check_schema(m.SCHEMA)

    def test_shared_definitions_are_byte_identical_to_worker_control(self) -> None:
        for name in m.SHARED_WORKER_CONTROL_DEFS:
            with self.subTest(definition=name):
                self.assertEqual(m.SCHEMA["$defs"][name],
                                 WORKER_CONTROL_SCHEMA["$defs"][name])

    def test_the_claim_token_verifier_is_ONE_value_across_the_contracts(self) -> None:
        """W4487 re-review [P1]. W151 owns the offer record and stored
        SHA-256 over the bearer's raw UTF-8 bytes as bare hex; worker-control's
        operation-signature payload hashed the bearer's JCS JSON encoding and
        prefixed it. Both called the result "the verifier the manager already
        stores", and for one bearer they were different hashed byte sequences
        — so two conforming peers computed different operation signatures for
        the same acceptance.

        Neither package could catch it: each asserted only its own
        self-consistency. This is the case that compares them."""
        self.assertEqual(w151.GOLDEN_BEARER, wc.GOLDEN_BEARER)
        self.assertEqual(w151.GOLDEN_VERIFIER, wc.GOLDEN_VERIFIER)
        # The two DERIVATIONS, not just the two constants.
        self.assertEqual(w151.token_verifier(w151.GOLDEN_BEARER),
                         wc.token_verifier(wc.GOLDEN_BEARER))
        # Over bearers neither package pins, including the shapes where a
        # JSON encoding and the raw bytes come apart.
        for token in [w151.GOLDEN_BEARER, "y" * 32, 'a"b' + "c" * 29,
                      "a\\b" + "c" * 29, "\u00e9\u00fc" + "c" * 30, "z" * 4096]:
            with self.subTest(token=token):
                self.assertEqual(w151.token_verifier(token),
                                 wc.token_verifier(token))
        # And the value the OFFER RECORD holds is that same value, so the
        # agreement is about stored state rather than about two helpers.
        deployment = w151.Deployment(certified_contracts={w151.V11, w151.V12})
        authority = w151.Authority(work_id="cross-W1", deployment=deployment,
                                   contract=w151.V12)
        manager = w151.Manager(authority, w151.ControlStore(), lambda: 10)
        offer = manager.offer("cross-offer", "baton.codex", "attempt-cross",
                              w151.GOLDEN_BEARER, 99)
        payload = wc.operation_signature_payload("offer.decide", {
            "offer_id": "cross-offer", "runtime_attempt_id": "attempt-cross",
            "work_ref": WORK_REF, "decision": "accept",
            "reason": "Contract accepted.", "claim_token": wc.GOLDEN_BEARER})
        self.assertEqual(offer.verifier,
                         payload["operands"]["claim_token_verifier"])

    def test_every_frozen_control_kind_is_covered(self) -> None:
        self.assertEqual(m.covered("control_kinds"), CONTROL_KINDS)

    def test_every_closed_error_pair_is_covered(self) -> None:
        self.assertEqual(m.covered("error_codes"), ERROR_PAIRS)

    def test_every_manifest_and_receipt_family_is_covered(self) -> None:
        self.assertEqual(m.covered("manifests"), MANIFEST_SCHEMAS)

    def test_every_agent_session_vocabulary_is_covered(self) -> None:
        self.assertEqual(m.covered("turn_outcomes"), set(ab.TURN_OUTCOMES))
        self.assertEqual(m.covered("session_states"), set(ab.SESSION_STATES))
        self.assertEqual(m.covered("event_kinds"), set(ab.EVENT_KINDS))
        self.assertEqual(m.covered("approval_families"), set(ab.CODEX_APPROVAL_FAMILIES))

    def test_every_w151_gate_kind_is_covered(self) -> None:
        self.assertEqual(m.covered("gates"),
                         {"runtime-quiescence", "contract-runtime", "plan-revision"})

    def test_every_obligation_names_its_evidence_and_all_three_verdicts(self) -> None:
        for oid, obligation in sorted(m.OBLIGATION_BY_ID.items()):
            with self.subTest(obligation=oid):
                self.assertTrue(obligation["observable"].strip())
                self.assertTrue(obligation["source"].strip())
                for value in ("passed", "failed", "unable"):
                    self.assertTrue(obligation["verdict"][value].strip())
                self.assertTrue(obligation["cases"])

    def test_register_and_matrix_agree_in_both_directions(self) -> None:
        from_register = {c for o in m.OBLIGATIONS["obligations"] for c in o["cases"]}
        self.assertEqual(from_register, set(m.CASE_BY_ID))
        for case in m.CASES["cases"]:
            with self.subTest(case=case["case_id"]):
                self.assertEqual(sorted(case["obligations"]),
                                 m.obligations_covering(case["case_id"]))

    def test_every_case_document_validates_and_reseals(self) -> None:
        # W4487 amended the register on 2026-08-22: 107 + the three
        # decline-authorization cases the ruled supersession needs.
        #
        # W14251 amended it again on 2026-08-26. The artifact-neutral ruling
        # removed the two acquisition cases family A opened with -- a case for
        # a rule that no longer exists asserts nothing -- and added eight for
        # the rules the ruling introduces: no acquisition, publication last and
        # atomic, identifier-only output refused, persistent output workspaces,
        # ephemeral export, and frozen output chaining into read-only input.
        # 112 - 2 + 8.
        #
        # And 119 after that Work's second review added
        # `A-manager-receipt-is-not-the-worker-envelope`: the split between the
        # worker's completion envelope and the manager's frozen-result receipt
        # is a rule this suite can observe, and an unobservable rule is prose.
        #
        # And 123 after that Work's third review: publication order and the
        # two-author split were covered, but whether the envelope actually
        # ANSWERS the assignment was not. §12 rule 15's four identity
        # relations are comparisons no single-document validator can make,
        # which is exactly why the suite has to carry them.
        #
        # And 132 after W19784, 2026-08-26. The contract those 123 certified
        # was UNSATISFIABLE and not one of them failed: §8.7 requires the
        # completion envelope to carry the authority generation and §8.1 gives
        # `input.json` none, because it is minted before any claim exists.
        # Every case above reads one document at a time, so the gap between
        # two documents was exactly the shape this suite could not see. The
        # nine new cases make the second input document, its mount mode, its
        # bindings to the first and the identity it delivers into the envelope
        # observable -- delivery, missing, malformed, wrong input, wrong Work,
        # consent visibility, the positive copy, stale generation, wrong
        # attempt.
        #
        # And 135 after W19784's own review, 2026-08-27. The three cases that
        # certified stale-generation and wrong-attempt refusal all operated at
        # `output.freeze` -- AFTER the agent has run. So a root nothing had
        # authorized could be mounted, an agent could work against it, and this
        # suite called that conformant because the freeze refused afterwards.
        # Certifying the right rule at the wrong moment is a hole of exactly
        # the shape this register exists to close. The three added here are the
        # pre-mount moment the approved lifecycle actually requires; the freeze
        # cases stay as defence in depth.
        #
        # And 136 after that review's second round. Authorizing a root and
        # mounting one were TWO OPERATIONS: the manager proved a directory and
        # the runtime's mount plan was independent of it, free to name the
        # sibling workspace or land somewhere other than the fixed path. A
        # proof about one value says nothing about another, and the suite had
        # no case that asked what was actually mounted.
        self.assertEqual(len(m.CASES["cases"]), 136)
        for case in m.CASES["cases"]:
            with self.subTest(case=case["case_id"]):
                VALIDATOR.validate(case)
                m.verify_document_digest(case)
                self.assertEqual(m.validate_case(case), case)

    def test_every_case_expectation_is_executable(self) -> None:
        """A case with no machine-readable expectation cannot decide anything."""
        for case in m.CASES["cases"]:
            with self.subTest(case=case["case_id"]):
                expectation = case["expectation"]
                self.assertIn(expectation["kind"],
                              {"control-refusal", "control-success", "invariant"})
                self.assertTrue(case["required_facts"])
                names = {p["fact"] for p in expectation["requires"]}
                if expectation["kind"] == "control-refusal":
                    names.add("refusal")
                self.assertEqual(set(case["required_facts"]), names)
                self.assertTrue(case["stimulus"]["detail"].strip())

    def test_only_control_refusal_cases_name_an_error_pair(self) -> None:
        """A probe or authority invariant synthesizes no control frame."""
        for case in m.CASES["cases"]:
            with self.subTest(case=case["case_id"]):
                expectation = case["expectation"]
                if expectation["kind"] == "control-refusal":
                    pair = expectation["expected_refusal"]
                    self.assertIn((pair["category"], pair["code"]), ERROR_PAIRS)
                    self.assertIn(case["stimulus"]["kind"],
                                  {"control-operation", "agent-script", "workflow-receipt"},
                                  "only something that produces a protocol reply can be "
                                  "refused with a control frame")
                else:
                    self.assertNotIn("expected_refusal", expectation)
                    self.assertNotIn("refusal", case["required_facts"])

    def test_in_runtime_probes_are_never_required_to_produce_a_control_error(self) -> None:
        for case in m.CASES["cases"]:
            if case["stimulus"]["kind"] in ("in-runtime-probe", "authority-read"):
                with self.subTest(case=case["case_id"]):
                    self.assertNotEqual(
                        case["expectation"]["kind"], "control-refusal",
                        "no upstream contract requires a filesystem denial or a negative "
                        "authority read to synthesize a control frame")

    def test_all_eight_families_are_represented(self) -> None:
        self.assertEqual({c["family"] for c in m.CASES["cases"]}, set("ABCDEFGH"))

    def test_the_mandatory_faults_the_review_named_are_exercised(self) -> None:
        used = {f for c in m.CASES["cases"] for f in c["required_faults"]}
        for fault in ("adapter-restart", "host-restart", "credential-expire",
                      "credential-reuse", "profile-decertify"):
            with self.subTest(fault=fault):
                self.assertIn(fault, used)
        self.assertTrue(used <= m.FAULT_CAPABILITIES)

    def test_the_assignment_required_areas_have_cases(self) -> None:
        cases = set(m.CASE_BY_ID)
        for required in ("E-adapter-restart-reconciles", "E-remote-host-restart",
                         "F-credential-scoped-to-assignment",
                         "F-credential-not-reusable-cross-assignment",
                         "F-credential-expiry-mid-run", "G-profile-failure-signal"):
            with self.subTest(case=required):
                self.assertIn(required, cases)

    def test_both_profiles_are_defined_and_remote_is_asserted_from_facts(self) -> None:
        self.assertEqual(set(m.PROFILE_BY_ID), {"local-oci", "remote"})
        remote = m.PROFILE_BY_ID["remote"]
        self.assertEqual(remote["locality"], "remote")
        self.assertTrue(any("host_identity" in a for a in remote["asserted_by"]))
        self.assertTrue(any("partition" in a for a in remote["asserted_by"]))
        self.assertTrue(any("restart" in a for a in remote["asserted_by"]))


# ==========================================================================
# Fixtures, cases and observations
# ==========================================================================

class DocumentTests(unittest.TestCase):
    def test_a_clean_fixture_is_accepted_for_both_profiles(self) -> None:
        for profile in ("local-oci", "remote"):
            with self.subTest(profile=profile):
                self.assertEqual(m.validate_fixture(fixture(profile)), fixture(profile))

    def test_a_local_fixture_cannot_call_itself_remote(self) -> None:
        """SPEC 8.2's remoteness is decided from facts, not from the label."""
        lying = m.seal_document(dict(
            {k: v for k, v in fixture("remote").items() if k != "document_digest"},
            host_identity={"manager_host_id": "manager-host",
                           "runtime_host_id": "manager-host",
                           "workspace_path_resolves_on_manager": False}))
        VALIDATOR.validate(lying)
        with self.assertRaises(m.ConformanceError):
            m.validate_fixture(lying)

    def test_a_remote_fixture_whose_workspace_resolves_locally_is_refused(self) -> None:
        resolving = m.seal_document(dict(
            {k: v for k, v in fixture("remote").items() if k != "document_digest"},
            host_identity={"manager_host_id": "manager-host",
                           "runtime_host_id": "runtime-host",
                           "workspace_path_resolves_on_manager": True}))
        self.assertFalse(VALIDATOR.is_valid(resolving))

    def test_a_remote_fixture_must_be_able_to_partition_and_restart_its_host(self) -> None:
        for fault in ("transport-partition", "host-restart"):
            with self.subTest(fault=fault):
                without = m.seal_document(dict(
                    {k: v for k, v in fixture("remote").items() if k != "document_digest"},
                    fault_capabilities=sorted(m.FAULT_CAPABILITIES - {fault})))
                self.assertFalse(VALIDATOR.is_valid(without))

    def test_a_fixture_missing_a_core_fault_is_refused(self) -> None:
        crippled = m.seal_document(dict(
            {k: v for k, v in fixture().items() if k != "document_digest"},
            fault_capabilities=sorted(m.FAULT_CAPABILITIES - {"transport-partition"})))
        with self.assertRaises(m.ConformanceError):
            m.validate_fixture(crippled)

    def test_the_core_gate_refuses_to_depend_on_a_model_provider(self) -> None:
        needy = dict({k: v for k, v in fixture().items() if k != "document_digest"})
        needy["scripted_agent"] = dict(needy["scripted_agent"], model_provider_required=True)
        self.assertFalse(VALIDATOR.is_valid(m.seal_document(needy)))

    def test_a_fixture_plants_a_canary_in_every_named_surface(self) -> None:
        partial = m.seal_document(dict(
            {k: v for k, v in fixture().items() if k != "document_digest"},
            canaries=[{"surface": "workspace", "canary_id": "c", "value_digest": D("b1")}]))
        with self.assertRaises(m.ConformanceError):
            m.validate_fixture(partial)

    def test_a_tampered_fixture_is_refused_before_any_field_is_read(self) -> None:
        tampered = dict(fixture(), fixture_id="tampered-after-sealing")
        with self.assertRaises(m.ConformanceError):
            m.validate_fixture(tampered)

    def test_a_case_cannot_disagree_with_the_register(self) -> None:
        case = copy.deepcopy(m.CASE_BY_ID["A-staged-tree-matches-its-manifest"])
        orphan = m.seal_document(dict(
            {k: v for k, v in case.items() if k != "document_digest"},
            obligations=["B-01"]))
        with self.assertRaises(m.ConformanceError):
            m.validate_case(orphan)


class ObservationTests(unittest.TestCase):
    def test_an_observation_carries_no_verdict(self) -> None:
        """The observer reports facts; deciding is the assessor's job."""
        properties = m.SCHEMA["$defs"]["conformanceObservation"]["properties"]
        self.assertNotIn("observed", properties)
        self.assertNotIn("assessment", properties)
        self.assertNotIn("verdict", properties)
        self.assertIn("facts", properties)

    def test_a_run_carries_no_verdict_and_no_counts(self) -> None:
        properties = m.SCHEMA["$defs"]["conformanceRun"]["properties"]
        for absent in ("verdict", "counts", "verdict_rationale"):
            self.assertNotIn(absent, properties)

    def test_an_observation_with_no_facts_is_not_a_document(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["A-staged-tree-matches-its-manifest"]
        empty = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            facts={}))
        self.assertFalse(VALIDATOR.is_valid(empty))

    def test_unrelated_evidence_cannot_support_an_observation(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["A-staged-tree-matches-its-manifest"]
        unrelated = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            evidence=[{"purpose": "dossier",
                       "artifact": {"artifact_id": "unrelated", "media_type": "text/plain",
                                    "bytes": 0, "content_digest": D("00"),
                                    "locator": "artifact:nothing"}}]))
        with self.assertRaises(m.ConformanceError):
            m.accept_observation(unrelated, case, fix)

    def test_absent_deciding_facts_are_inadmissible(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["A-freeze-after-quiescence"]
        facts = satisfying_facts(case)
        facts.pop("runtime_state_at_freeze")
        thin = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            facts=facts))
        with self.assertRaises(m.ConformanceError):
            m.accept_observation(thin, case, fix)

    def test_an_observation_is_bound_to_the_exact_case_and_fixture(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["A-staged-tree-matches-its-manifest"]
        other = m.CASE_BY_ID["A-input-is-read-only"]
        with self.assertRaises(m.ConformanceError):
            m.accept_observation(observation(case, fix), other, fix)
        with self.assertRaises(m.ConformanceError):
            m.accept_observation(observation(case, fix), case, fixture("remote"))
        with self.assertRaises(m.ConformanceError):
            m.accept_observation(observation(case, fix, case_digest=D("ff")), case, fix)


# ==========================================================================
# The assessor derives the verdict
# ==========================================================================

class AssessorTests(unittest.TestCase):
    def test_conforming_facts_pass_and_contrary_facts_fail(self) -> None:
        for case in m.CASES["cases"]:
            with self.subTest(case=case["case_id"]):
                good = {"status": "observed", "facts": satisfying_facts(case),
                        "blocked_by": None}
                self.assertEqual(m.assess(good, case)[0], "passed")

    def test_a_negative_case_fails_on_silence_and_on_the_wrong_refusal(self) -> None:
        case = m.CASE_BY_ID["C-token-replayed"]
        for label, refusal in (
            ("silence", None),
            ("wrong code", {"category": "refused", "code": "capability"}),
            ("wrong category", {"category": "policy", "code": "precondition"}),
        ):
            with self.subTest(refusal=label):
                facts = dict(satisfying_facts(case), refusal=refusal)
                assessment, rationale = m.assess({"status": "observed", "facts": facts,
                                                  "blocked_by": None}, case)
                self.assertEqual(assessment, "failed")
                self.assertIn("refusal", rationale)

    def test_a_positive_case_that_observed_a_refusal_fails(self) -> None:
        case = m.CASE_BY_ID["A-staged-tree-matches-its-manifest"]
        facts = dict(satisfying_facts(case),
                     refusal={"category": "refused", "code": "precondition"})
        self.assertEqual(m.assess({"status": "observed", "facts": facts,
                                   "blocked_by": None}, case)[0], "failed")

    def test_an_invariant_fails_when_the_probe_reports_reachability(self) -> None:
        case = m.CASE_BY_ID["B-no-authority-capability"]
        facts = dict(satisfying_facts(case), authority_home_reachable=True)
        assessment, rationale = m.assess({"status": "observed", "facts": facts,
                                          "blocked_by": None}, case)
        self.assertEqual(assessment, "failed")
        self.assertIn("authority_home_reachable", rationale)

    def test_a_blocked_observation_is_unable_and_names_its_cause(self) -> None:
        case = m.CASE_BY_ID["E-remote-host-restart"]
        assessment, rationale = m.assess(
            {"status": "blocked", "facts": {}, "blocked_by": "host-restart"}, case)
        self.assertEqual(assessment, "unable")
        self.assertIn("host-restart", rationale)


# ==========================================================================
# Certification
# ==========================================================================

class VerdictTests(unittest.TestCase):
    def test_a_conforming_run_certifies_on_both_profiles(self) -> None:
        for profile in ("local-oci", "remote"):
            with self.subTest(profile=profile):
                fix = fixture(profile)
                report = m.certify(conforming_run(fix), fix)
                self.assertEqual(report.verdict, "certified")
                self.assertEqual(len(report.passed), len(m.core_for(profile)))
                self.assertEqual((report.failed, report.unable, report.missing), ([], [], []))
                self.assertEqual(report.signal["signal"], "none")

    def test_a_declared_pass_without_observed_facts_cannot_certify(self) -> None:
        """The finding that mattered most: a sealed claim is not an observation."""
        fix = fixture()
        fabricated = {}
        for case in core_cases(fix):
            fabricated[case["case_id"]] = m.seal_document(dict(
                {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
                facts={name: "declared without observing" for name in case["required_facts"]},
                reason="declared without observed facts"))
        report = m.certify(conforming_run(fix, fabricated), fix)
        self.assertEqual(report.verdict, "not-certified")
        self.assertEqual(len(report.failed), len(m.core_for(fix["profile"])))

    def test_one_contrary_fact_denies_certification(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["D-fence-before-stop"]
        broken = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            facts=dict(satisfying_facts(case), fence_precedes_runtime_stop=False)))
        report = m.certify(conforming_run(fix, {case["case_id"]: broken}), fix)
        self.assertEqual(report.verdict, "not-certified")
        self.assertEqual(report.failed, ["D-fence-before-stop"])

    def test_a_blocked_case_denies_certification(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["E-partition-reattach-proof"]
        blocked = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            status="blocked", facts={}, blocked_by="transport-partition"))
        report = m.certify(conforming_run(fix, {case["case_id"]: blocked}), fix)
        self.assertEqual(report.verdict, "not-certified")
        self.assertEqual(report.unable, ["E-partition-reattach-proof"])

    def test_an_unobserved_core_case_denies_certification(self) -> None:
        fix = fixture()
        target = m.CASE_BY_ID["F-leak-refuses-publication"]
        observations = [observation(c, fix) for c in core_cases(fix) if c is not target]
        report = m.certify(run(observations, fix), fix)
        self.assertEqual(report.verdict, "not-certified")
        self.assertEqual(report.missing, ["F-leak-refuses-publication"])

    def test_certification_refuses_an_unaccepted_fixture(self) -> None:
        broken = dict(fixture(), fixture_id="tampered-after-sealing")
        with self.assertRaises(m.ConformanceError):
            m.certify(run([observation(m.CASE_BY_ID["A-staged-tree-matches-its-manifest"], broken)], broken),
                      broken)

    def test_certification_refuses_profile_substitution(self) -> None:
        fix = fixture()
        substituted = run([observation(c, fix) for c in core_cases(fix)], fix,
                          profile="remote")
        with self.assertRaises(m.ConformanceError):
            m.certify(substituted, fix)

    def test_certification_refuses_a_run_bound_to_a_different_fixture(self) -> None:
        fix = fixture()
        with self.assertRaises(m.ConformanceError):
            m.certify(conforming_run(fix), fixture("remote"))

    def test_certification_refuses_a_run_against_a_different_register(self) -> None:
        fix = fixture()
        drifted = run([observation(c, fix) for c in core_cases(fix)], fix,
                      obligations_digest=D("ee"))
        with self.assertRaises(m.ConformanceError):
            m.certify(drifted, fix)

    def test_a_case_cannot_be_observed_twice_in_one_run(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["A-staged-tree-matches-its-manifest"]
        doubled = [observation(c, fix) for c in core_cases(fix)]
        doubled.append(observation(case, fix, observation_id="obs-second"))
        with self.assertRaises(m.ConformanceError):
            m.certify(run(doubled, fix), fix)

    def test_a_supplemental_pass_cannot_offset_a_core_failure(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["G-proposal-integrity"]
        broken = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            facts=dict(satisfying_facts(case), input_digest_matches=False)))
        report = m.certify(conforming_run(fix, {case["case_id"]: broken}), fix)
        self.assertEqual(report.verdict, "not-certified")
        self.assertTrue(m.supplemental_cannot_compensate(
            conforming_run(fix, {case["case_id"]: broken}), fix))

    def test_the_report_is_derived_and_emits_a_profile_signal(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["B-cross-worker-isolation"]
        broken = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            facts=dict(satisfying_facts(case), peer_workspace_readable=True)))
        failing = conforming_run(fix, {case["case_id"]: broken})
        report = m.build_report(failing, fix, "report-1", "2026-08-22T04:00:00.000Z")
        VALIDATOR.validate(report)
        m.verify_document_digest(report)
        self.assertEqual(report["verdict"], "not-certified")
        signal = report["profile_signal"]
        self.assertEqual(signal["signal"], "probation")
        self.assertEqual(signal["failed_cases"], ["B-cross-worker-isolation"])
        self.assertEqual(signal["consumer"], "route-policy")
        self.assertEqual(signal["runtime_profile_digest"], fix["runtime_profile_digest"])
        self.assertEqual(signal["adapter_build_digest"], fix["adapter_build_digest"])

    def test_a_certified_run_emits_no_signal(self) -> None:
        fix = fixture()
        report = m.build_report(conforming_run(fix), fix, "report-2",
                                "2026-08-22T04:00:00.000Z")
        VALIDATOR.validate(report)
        self.assertEqual(report["verdict"], "certified")
        self.assertEqual(report["profile_signal"]["signal"], "none")
        self.assertEqual(report["profile_signal"]["failed_cases"], [])

    def test_more_than_one_core_failure_escalates_the_signal(self) -> None:
        fix = fixture()
        replace = {}
        for cid in ("B-cross-worker-isolation", "D-fence-before-stop"):
            case = m.CASE_BY_ID[cid]
            facts = satisfying_facts(case)
            facts[case["expectation"]["requires"][0]["fact"]] = "contradiction"
            replace[cid] = m.seal_document(dict(
                {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
                facts=facts))
        report = m.certify(conforming_run(fix, replace), fix)
        self.assertEqual(report.verdict, "not-certified")
        self.assertEqual(report.signal["signal"], "disablement")
        self.assertEqual(len(report.signal["failed_cases"]), 2)

    def test_certification_hands_back_copies(self) -> None:
        fix = fixture()
        submitted = copy.deepcopy(fix)
        accepted = m.validate_fixture(submitted)
        self.assertEqual(accepted, fix)
        self.assertIsNot(accepted, submitted)
        submitted["profile"] = "remote"
        self.assertEqual(accepted["profile"], "local-oci")

    def test_both_profiles_run_the_same_normative_core(self) -> None:
        self.assertEqual(
            {c["case_id"] for c in m.CASES["cases"] if c["scope"] == "portable-core"},
            set(m.CASE_BY_ID))


# ==========================================================================
# Profile applicability, derived residual risk, supplemental cases
# ==========================================================================

class ProfileApplicabilityTests(unittest.TestCase):
    def test_the_two_cores_differ_only_by_a_fault_one_profile_cannot_have(self) -> None:
        local, remote = m.core_for("local-oci"), m.core_for("remote")
        self.assertTrue(local <= remote)
        difference = remote - local
        self.assertEqual(difference, {"E-remote-host-restart"})
        for case_id in difference:
            required = set(m.CASE_BY_ID[case_id]["required_faults"])
            self.assertTrue(required & m.PROFILE_ONLY_FAULTS["remote"],
                            "a profile does not get a smaller contract for free")

    def test_the_admitted_minimal_local_fixture_certifies(self) -> None:
        """The contradiction the review found: admitted, then necessarily unable."""
        minimal = fixture(fault_capabilities=sorted(m.MANDATORY_FAULTS_BY_PROFILE["local-oci"]))
        self.assertNotIn("host-restart", minimal["fault_capabilities"])
        m.validate_fixture(minimal)
        report = m.certify(conforming_run(minimal), minimal)
        self.assertEqual(report.verdict, "certified")
        self.assertEqual((report.failed, report.unable, report.missing), ([], [], []))

    def test_mandatory_faults_are_derived_from_the_core_each_profile_runs(self) -> None:
        for profile in ("local-oci", "remote"):
            with self.subTest(profile=profile):
                needed = {f for cid in m.core_for(profile)
                          for f in m.CASE_BY_ID[cid]["required_faults"]}
                self.assertEqual(m.MANDATORY_FAULTS_BY_PROFILE[profile], needed)
        crippled = fixture(fault_capabilities=sorted(
            m.MANDATORY_FAULTS_BY_PROFILE["local-oci"] - {"process-kill"}))
        with self.assertRaises(m.ConformanceError):
            m.validate_fixture(crippled)

    def test_a_case_cannot_exclude_a_profile_without_a_profile_only_fault(self) -> None:
        case = copy.deepcopy(m.CASE_BY_ID["A-staged-tree-matches-its-manifest"])
        narrowed = m.seal_document(dict(
            {k: v for k, v in case.items() if k != "document_digest"},
            applies_to=["remote"]))
        VALIDATOR.validate(narrowed)
        with self.assertRaises(m.ConformanceError):
            m.validate_case(narrowed)

    def test_a_remote_only_case_is_refused_in_a_local_run(self) -> None:
        fix = fixture("local-oci")
        remote_only = m.CASE_BY_ID["E-remote-host-restart"]
        observations = [observation(c, fix) for c in core_cases(fix)]
        observations.append(observation(remote_only, fix))
        with self.assertRaises(m.ConformanceError):
            m.certify(run(observations, fix), fix)


class ResidualRiskTests(unittest.TestCase):
    def test_residual_risk_is_derived_and_partitions_the_surfaces(self) -> None:
        fix = fixture()
        report = m.build_report(conforming_run(fix), fix, "report-r",
                                "2026-08-22T04:00:00.000Z")
        VALIDATOR.validate(report)
        risk = report["residual_risk"]
        scanned, unscanned = set(risk["surfaces_scanned"]), set(risk["surfaces_not_scanned"])
        self.assertEqual(scanned | unscanned, m.CANARY_SURFACES)
        self.assertFalse(scanned & unscanned)
        self.assertEqual(scanned, m.CANARY_SURFACES)
        self.assertTrue(any("redaction is not proof of absence" in u
                            for u in risk["unproven"]))

    def test_a_report_cannot_contradict_the_facts_it_certified(self) -> None:
        """build_report takes no caller-supplied residual risk at all."""
        import inspect
        parameters = set(inspect.signature(m.build_report).parameters)
        self.assertNotIn("residual_risk", parameters)
        fix = fixture()
        report = m.build_report(conforming_run(fix), fix, "report-c",
                                "2026-08-22T04:00:00.000Z")
        canary = next(o for o in conforming_run(fix)["observations"]
                      if o["case_id"] == m.CANARY_CASE_ID)
        self.assertEqual(sorted(report["residual_risk"]["surfaces_scanned"]),
                         sorted(canary["facts"]["surfaces_scanned"]))

    def test_an_unscanned_run_reports_every_surface_as_unscanned(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID[m.CANARY_CASE_ID]
        blocked = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            status="blocked", facts={}, blocked_by="canary-plant"))
        report = m.build_report(conforming_run(fix, {case["case_id"]: blocked}), fix,
                                "report-b", "2026-08-22T04:00:00.000Z")
        VALIDATOR.validate(report)
        risk = report["residual_risk"]
        self.assertEqual(risk["surfaces_scanned"], [])
        self.assertEqual(set(risk["surfaces_not_scanned"]), m.CANARY_SURFACES)
        self.assertEqual(report["verdict"], "not-certified")
        self.assertTrue(any("did not pass" in u for u in risk["unproven"]))

    def test_a_partial_scan_is_reported_as_partial(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID[m.CANARY_CASE_ID]
        partial = sorted(m.CANARY_SURFACES - {"caches", "retained-runtime-layers"})
        facts = dict(satisfying_facts(case), surfaces_scanned=partial,
                     planted_canaries_found=8)
        weakened = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            facts=facts))
        report = m.build_report(conforming_run(fix, {case["case_id"]: weakened}), fix,
                                "report-p", "2026-08-22T04:00:00.000Z")
        risk = report["residual_risk"]
        # The case itself fails, because the expectation pins all ten.
        self.assertEqual(report["verdict"], "not-certified")
        self.assertEqual(risk["surfaces_scanned"], [])
        self.assertEqual(set(risk["surfaces_not_scanned"]), m.CANARY_SURFACES)


class SupplementalTests(unittest.TestCase):
    def supplemental_observation(self, fix, verified=True, case=None):
        case = case or SUPPLEMENTAL
        return m.seal_document({
            "suite_family": "baton.worker-conformance",
            "version": {"major": 1, "minor": 0},
            "document": "observation",
            "observation_id": "obs-vendor",
            "case_id": case["case_id"],
            "fixture_digest": fix["document_digest"],
            "case_digest": case["document_digest"],
            "status": "observed",
            "facts": {"vendor_attestation_verified": verified},
            "blocked_by": None,
            "reason": "vendor attestation",
            "evidence": [{"purpose": "attestation",
                          "artifact": {"artifact_id": "vendor-att",
                                       "media_type": "application/json", "bytes": 4,
                                       "content_digest": D("cd"),
                                       "locator": "artifact:vendor/1"}}],
            "observed_at": "2026-08-22T03:56:00.000Z"})

    def test_a_supplemental_case_is_assessed_and_reported_separately(self) -> None:
        fix = fixture()
        observations = [observation(c, fix) for c in core_cases(fix)]
        observations.append(self.supplemental_observation(fix))
        report = m.build_report(
            run(observations, fix, supplemental_cases=[SUPPLEMENTAL]), fix,
            "report-s", "2026-08-22T04:00:00.000Z")
        VALIDATOR.validate(report)
        self.assertEqual(report["verdict"], "certified")
        self.assertEqual([e["case_id"] for e in report["supplemental"]], ["G-vendor-extra"])
        self.assertEqual(report["supplemental"][0]["assessment"], "passed")
        self.assertNotIn("G-vendor-extra", [e["case_id"] for e in report["assessed"]])

    def test_a_failed_supplemental_does_not_deny_a_clean_core(self) -> None:
        fix = fixture()
        observations = [observation(c, fix) for c in core_cases(fix)]
        observations.append(self.supplemental_observation(fix, verified=False))
        report = m.certify(run(observations, fix, supplemental_cases=[SUPPLEMENTAL]), fix)
        self.assertEqual(report.verdict, "certified")
        self.assertEqual(report.supplemental[0]["assessment"], "failed")
        self.assertEqual(report.failed, [])

    def test_a_supplemental_pass_cannot_offset_a_core_failure(self) -> None:
        fix = fixture()
        case = m.CASE_BY_ID["G-proposal-integrity"]
        broken = m.seal_document(dict(
            {k: v for k, v in observation(case, fix).items() if k != "document_digest"},
            facts=dict(satisfying_facts(case), input_digest_matches=False)))
        observations = [broken if c is case else observation(c, fix) for c in core_cases(fix)]
        observations.append(self.supplemental_observation(fix))
        report = m.certify(run(observations, fix, supplemental_cases=[SUPPLEMENTAL]), fix)
        self.assertEqual(report.verdict, "not-certified")
        self.assertEqual(report.failed, ["G-proposal-integrity"])
        self.assertEqual(report.supplemental[0]["assessment"], "passed")

    def test_a_run_cannot_redefine_a_portable_core_case(self) -> None:
        fix = fixture()
        impostor = m.seal_document(dict(
            {k: v for k, v in SUPPLEMENTAL.items() if k != "document_digest"},
            case_id="A-staged-tree-matches-its-manifest"))
        with self.assertRaises(m.ConformanceError):
            m.certify(run([observation(c, fix) for c in core_cases(fix)], fix,
                          supplemental_cases=[impostor]), fix)

    def test_a_run_cannot_smuggle_in_a_portable_core_scope(self) -> None:
        fix = fixture()
        promoted = m.seal_document(dict(
            {k: v for k, v in SUPPLEMENTAL.items() if k != "document_digest"},
            scope="portable-core"))
        with self.assertRaises(m.ConformanceError):
            m.certify(run([observation(c, fix) for c in core_cases(fix)], fix,
                          supplemental_cases=[promoted]), fix)


    def test_a_supplemental_case_never_claims_a_register_obligation(self) -> None:
        """The example itself had to cite an unrelated obligation to validate."""
        self.assertEqual(SUPPLEMENTAL["obligations"], [])
        self.assertEqual(SUPPLEMENTAL["supplemental_source"], "com.example.runtime/1")
        VALIDATOR.validate(SUPPLEMENTAL)

        borrowing = supplemental_case(obligations=["G-04"])
        self.assertFalse(VALIDATOR.is_valid(borrowing),
                         "a supplemental case has nowhere to put a core obligation")

        sourceless = supplemental_case(supplemental_source=None)
        self.assertFalse(VALIDATOR.is_valid(sourceless),
                         "it declares where it comes from instead")

    def test_a_portable_core_case_cannot_carry_a_supplemental_source(self) -> None:
        for case in m.CASES["cases"]:
            self.assertIsNone(case["supplemental_source"])
        case = copy.deepcopy(m.CASE_BY_ID["A-staged-tree-matches-its-manifest"])
        disguised = m.seal_document(dict(
            {k: v for k, v in case.items() if k != "document_digest"},
            supplemental_source="com.example.runtime/1"))
        self.assertFalse(VALIDATOR.is_valid(disguised))

    def test_a_supplemental_source_cannot_look_like_an_obligation(self) -> None:
        for impostor in ("G-04", "A-01", "core", "vendor"):
            with self.subTest(source=impostor):
                self.assertFalse(VALIDATOR.is_valid(
                    supplemental_case(supplemental_source=impostor)))

    def test_a_bound_supplemental_definition_is_never_silently_dropped(self) -> None:
        """Binding an extension and suppressing its execution is not reporting."""
        fix = fixture()
        observations = [observation(c, fix) for c in core_cases(fix)]
        report = m.certify(run(observations, fix, supplemental_cases=[SUPPLEMENTAL]), fix)
        self.assertEqual(report.verdict, "certified")
        self.assertEqual(len(report.supplemental), 1)
        self.assertEqual(report.supplemental[0]["case_id"], "G-vendor-extra")
        self.assertEqual(report.supplemental[0]["assessment"], "unable")
        self.assertIn("never observed", report.supplemental[0]["rationale"])

    def test_a_supplemental_definition_must_apply_to_the_fixture_profile(self) -> None:
        fix = fixture("local-oci")
        remote_only = supplemental_case(applies_to=["remote"])
        observations = [observation(c, fix) for c in core_cases(fix)]
        observations.append(self.supplemental_observation(fix, case=remote_only))
        with self.assertRaises(m.ConformanceError):
            m.certify(run(observations, fix, supplemental_cases=[remote_only]), fix)

    def test_a_supplemental_case_cannot_be_observed_twice(self) -> None:
        fix = fixture()
        observations = [observation(c, fix) for c in core_cases(fix)]
        observations.append(self.supplemental_observation(fix))
        observations.append(m.seal_document(dict(
            {k: v for k, v in self.supplemental_observation(fix).items()
             if k != "document_digest"}, observation_id="obs-vendor-2")))
        with self.assertRaises(m.ConformanceError):
            m.certify(run(observations, fix, supplemental_cases=[SUPPLEMENTAL]), fix)


if __name__ == "__main__":
    unittest.main()
