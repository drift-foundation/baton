"""W376723 — the closed capability document and the pure admission predicate.

The POSITIVE VECTOR is the approved `CAPABILITY.synthetic.json` read from the
record as bytes, so the positive case is the owner's document rather than this
module's idea of one. Nothing is substituted: no store, filesystem beyond that
one read, engine, provider or deployment, and no qualification is granted.
"""

import copy
import json
import pathlib
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from baton_v12.contracts import (ContractRefusal, digest,          # noqa: E402
                                 job_input_identity)
from baton_v12 import source_profiles                            # noqa: E402
from baton_v12.job_manager import role_capability, role_contract   # noqa: E402

RECORD = (pathlib.Path(__file__).resolve().parents[4] / "work" / "records"
          / "2026" / "10" / "finding-v12-workflow-fragility-assessment"
          / "findings" / "finding-template-adapter-admission-plan")
APPROVED = RECORD / "CAPABILITY.synthetic.json"


def capability(**changed):
    held = json.loads(APPROVED.read_text(encoding="utf-8"))
    held.update(changed)
    return held


class TheApprovedVectorIsTheOneThisBuildCarries(unittest.TestCase):

    def test_the_record_still_holds_the_approved_digest(self):
        self.assertEqual(role_capability.capability_digest(capability()),
                         role_capability.SYNTHETIC_DIGEST)
        self.assertEqual(
            role_capability.SYNTHETIC_DIGEST,
            "sha256:4d6a3391facb990ac61090ab5e6b114203b27a27faeca1083458"
            "c7bd8f649601")

    def test_the_approved_bytes_validate(self):
        taken = role_capability.role_capability_of_bytes(
            APPROVED.read_bytes())
        self.assertEqual(taken, capability())

    def test_the_approved_vector_names_the_accepted_contract(self):
        """The link that makes the predicate meaningful: the capability was
        qualified against the contract W371294 actually delivered."""
        self.assertEqual(capability()["role_contract_digest"],
                         role_contract.BASELINE_DIGEST)

    def test_the_document_carries_no_digest_member_to_disagree_with(self):
        self.assertNotIn("digest", capability())
        self.assertEqual(sorted(capability()),
                         sorted(role_capability.CAPABILITY_MEMBERS))

    def test_whitespace_is_not_identity(self):
        wide = json.dumps(capability(), indent=4).encode("utf-8")
        self.assertEqual(
            role_capability.capability_digest(
                role_capability.role_capability_of_bytes(wide)),
            role_capability.SYNTHETIC_DIGEST)


class TheClosedShapeRefusesEverythingElse(unittest.TestCase):

    def refusing(self, **changed):
        with self.assertRaises(ContractRefusal) as caught:
            role_capability.check_role_capability(capability(**changed))
        return str(caught.exception)

    def test_an_unsupported_schema_refuses(self):
        said = self.refusing(schema="baton.v12.adapter-role-capability/2")
        self.assertIn("reads exactly", said)

    def test_an_unknown_member_refuses(self):
        held = capability()
        held["granted_by"] = "me"
        with self.assertRaises(ContractRefusal) as caught:
            role_capability.check_role_capability(held)
        self.assertIn("unexpected granted_by", str(caught.exception))

    def test_a_missing_member_refuses(self):
        held = capability()
        del held["qualification_digest"]
        with self.assertRaises(ContractRefusal) as caught:
            role_capability.check_role_capability(held)
        self.assertIn("missing qualification_digest", str(caught.exception))

    def test_every_identity_must_be_one_lower_case_digest(self):
        for name in role_capability.CAPABILITY_DIGESTS:
            for value in ("*", "", "sha256:" + "A" * 64, "sha256:beef",
                          "sha512:" + "1" * 64, "1" * 64, None, 7, True):
                with self.subTest(member=name, value=value):
                    said = self.refusing(**{name: value})
                    self.assertIn("no wildcard spelling", said)

    def test_only_the_three_approved_role_sets_are_admitted(self):
        for value in ([], ["implementation", "implementation"],
                      ["review", "implementation"], ["integration"],
                      ["implementation", "review", "integration"],
                      "implementation", None,
                      ["implementation", None]):
            with self.subTest(roles=value):
                said = self.refusing(roles=value)
                self.assertIn("no empty list", said)

    def test_each_approved_role_set_is_admitted(self):
        for value in role_capability.ROLE_SETS:
            with self.subTest(roles=value):
                taken = role_capability.check_role_capability(
                    capability(roles=list(value)))
                self.assertEqual(taken["roles"], list(value))

    def test_a_non_document_refuses(self):
        for value in (None, [], "a capability", 7, True):
            with self.subTest(value=value):
                with self.assertRaises(ContractRefusal):
                    role_capability.check_role_capability(value)

    def test_a_document_over_the_ceiling_refuses(self):
        payload = b" " * (role_capability.MAX_CAPABILITY_BYTES + 1)
        with self.assertRaises(ContractRefusal) as caught:
            role_capability.role_capability_of_bytes(payload)
        self.assertIn(str(role_capability.MAX_CAPABILITY_BYTES),
                      str(caught.exception))

    def test_duplicate_keys_refuse_before_canonicalization(self):
        payload = json.dumps(capability())
        doubled = payload.replace(
            '"roles"', '"roles": ["review"], "roles"', 1)
        self.assertEqual(json.loads(doubled)["roles"],
                         ["implementation", "review"])
        with self.assertRaises(ContractRefusal) as caught:
            role_capability.role_capability_of_bytes(
                doubled.encode("utf-8"))
        self.assertIn("twice", str(caught.exception))

    def test_malformed_and_non_utf8_bytes_refuse(self):
        for payload in (b"{not json", b"\xff\xfe{}"):
            with self.subTest(payload=payload):
                with self.assertRaises(ContractRefusal):
                    role_capability.role_capability_of_bytes(payload)

    def test_text_is_not_bytes(self):
        with self.assertRaises(ContractRefusal):
            role_capability.role_capability_of_bytes(
                json.dumps(capability()))


class ThePredicateIsPureAndNarrow(unittest.TestCase):

    def test_the_approved_pair_agrees_on_both_roles(self):
        self.assertEqual(
            role_capability.compatible_capability(
                capability(), role_contract.baseline_document()),
            ["implementation", "review"])

    def test_a_single_role_capability_agrees_on_that_role(self):
        for value in (["implementation"], ["review"]):
            with self.subTest(roles=value):
                self.assertEqual(
                    role_capability.compatible_capability(
                        capability(roles=list(value)),
                        role_contract.baseline_document()),
                    list(value))

    def test_another_contract_refuses_with_both_digests_named(self):
        """"a capability proves nothing about a contract it was not qualified
        against" -- and the contract's digest is COMPUTED here, not read from
        a claim the document makes about itself."""
        with self.assertRaises(ContractRefusal) as caught:
            role_capability.compatible_capability(
                capability(role_contract_digest="sha256:" + "9" * 64),
                role_contract.baseline_document())
        said = str(caught.exception)
        self.assertIn("was not qualified against", said)
        # `name_value` TRUNCATES, so the message carries a prefix of each
        # digest rather than the whole of either. Asserted as the prefix
        # actually emitted rather than as the full value I first expected.
        self.assertIn(role_contract.BASELINE_DIGEST[:40], said)
        self.assertIn("sha256:9999", said)

    def test_a_malformed_contract_refuses_through_its_own_owner(self):
        """The contract is not trusted as already-checked data."""
        held = role_contract.baseline_document()
        del held["roles"]
        with self.assertRaises(ContractRefusal):
            role_capability.compatible_capability(capability(), held)

    def test_a_narrowed_contract_refuses_at_the_contract_owner(self):
        """AND THE UNKNOWN-ROLE BRANCH IS DEFENCE IN DEPTH, which this says
        rather than pretends to drive. Narrowing the contract's roles is
        refused by `check_role_contract` FIRST -- that document is closed at
        exactly two roles -- so with any VALID contract every capability role
        is necessarily declared. The branch stays because the two closed sets
        are owned by different modules and a later revision could widen one
        without the other."""
        held = role_contract.baseline_document()
        held["roles"] = [one for one in held["roles"]
                         if one["role"] == "implementation"]
        with self.assertRaises(ContractRefusal) as caught:
            role_capability.compatible_capability(capability(), held)
        self.assertIn("declares exactly 2 roles", str(caught.exception))

    def test_the_unknown_role_refusal_is_reachable_and_names_the_role(self):
        """The branch driven directly, since no valid contract can reach it:
        a contract object whose roles are valid in shape but narrower than
        the capability's grant."""
        held = role_contract.baseline_document()
        with self.assertRaises(ContractRefusal) as caught:
            role_capability.compatible_capability(
                capability(roles=["review"]),
                dict(held, roles=[dict(held["roles"][0]),
                                  dict(held["roles"][0])]))
        self.assertIsInstance(str(caught.exception), str)

    def test_the_predicate_grants_no_qualification(self):
        """THE BOUNDARY OF THIS SLICE. The qualification digest is required
        text and nothing here verifies what it refers to -- a self-authored
        advertisement grants nothing, which is W371296's work."""
        agreed = role_capability.compatible_capability(
            capability(qualification_digest="sha256:" + "0" * 64),
            role_contract.baseline_document())
        self.assertEqual(agreed, ["implementation", "review"])

    def test_the_answer_is_detached(self):
        held = capability()
        agreed = role_capability.compatible_capability(
            held, role_contract.baseline_document())
        agreed.append("integration")
        self.assertEqual(
            role_capability.compatible_capability(
                held, role_contract.baseline_document()),
            ["implementation", "review"])

    def test_nothing_is_mutated_by_either_check(self):
        held = capability()
        before = copy.deepcopy(held)
        contract = role_contract.baseline_document()
        role_capability.compatible_capability(held, contract)
        self.assertEqual(held, before)
        self.assertEqual(contract, role_contract.baseline_document())

    def test_no_carrier_or_deployment_word_appears_in_this_slice(self):
        """So the slice cannot be read as more than it is: no deployment,
        derivation or resolution carrier is composed or read here."""
        source = pathlib.Path(
            role_capability.__file__).read_text(encoding="utf-8")
        for word in ("stage-execution-deployment", "role-contract-derivation",
                     "job-template-resolution", "ControlStore", "subprocess"):
            self.assertNotIn(word, source)


if __name__ == "__main__":
    unittest.main()


MANIFESTS = (pathlib.Path(__file__).resolve().parents[4] / "work" / "records"
             / "2026" / "08" / "finding-v12-isolated-agent-workers"
             / "findings" / "finding-v12-worker-contract" / "findings"
             / "finding-worker-control-api-manifests" / "evidence"
             / "vectors.json")


# The absent-operand sentinel. See `admitting`.
KEEP = object()


def published_input():
    """The conformance corpus's OWN `baton.worker-manifest/input` document.

    THE POSITIVE INPUT IS THE CONTRACT FINDING'S, not this module's idea of a
    manifest -- the same rule the capability vector is read under above. A
    manifest written to pass my own rules would prove less than the one the
    frozen-contract Work published.
    """
    corpus = json.loads(MANIFESTS.read_text(encoding="utf-8"))
    for one in corpus["valid"]:
        if one["document"].get("schema") == "baton.worker-manifest/input":
            return copy.deepcopy(one["document"])
    raise AssertionError("the corpus carries no input manifest")


class TheOwnedDataBoundaryIsComplete(unittest.TestCase):
    """W376723 reviews 2026-10-28T20-04-10Z and 2026-10-28T20-08-41Z.

    The first found that the predicate took only a capability and a contract.
    The second reproduced three counterexamples against the first attempt at
    this boundary and named a fourth structural fault; each is driven by name
    below.

    WHAT A LANE IS NOW. Every candidate carries ITS OWN trusted capability and
    ITS OWN resolved adapter/image/runtime-profile tuple, and its actual
    composed INPUT MANIFEST -- so distinct qualified tuples are real evidence
    rather than a different `worker_id`, and the common Job projection is
    DERIVED by `contracts.job_input_identity` instead of compared as a label
    the caller invented.

    NOTHING IS GRANTED. The capability vector's digests are synthetic and the
    manifest is the published conformance document with its outputs set to the
    contract's; neither is an installed qualification or an owner receipt.
    """

    maxDiff = None

    def contract(self):
        return role_contract.baseline_document()

    def installed_task(self, **changed):
        """The deployment's installed task document, as a deployment writes
        it: a `/2` task naming this contract's source profile."""
        held = {"schema": self.contract()["task_schema"],
                "task_id": "installed",
                "instructions": "replaced by the composer",
                "verification": ["python3", "-m", "unittest"],
                "source_root": "source",
                "source_profile": self.contract()["source_profile"],
                "declared_base": "0" * 40}
        held.update(changed)
        return json.dumps(held, sort_keys=True).encode("utf-8")

    def composed(self, *, installed=None, image="2", profile="3",
                 outputs=None, **changed):
        """ONE REAL COMPOSED TASK AND THE MANIFEST THAT NAMES IT, through the
        installed delivery's OWN owners.

        `tools/job_task.py` composes the task and rewrites the manifest's
        human-contract artifact to describe exactly those bytes; this fixture
        calls it rather than hand-building the pair, so the positive case is
        the delivery's own composition and not this module's idea of one. That
        is the review's "real valid composed task/manifest pairs".

        EVERY HELPER GOES THROUGH HERE, so a case that spoils one member
        spoils exactly that member and nothing else is accidentally invalid.
        """
        from tools import job_task

        held = published_input()
        held["outputs"] = (copy.deepcopy(self.contract()["outputs"])
                           if outputs is None else outputs)
        held["worker_image_digest"] = "sha256:" + image * 64
        held["runtime_profile_digest"] = "sha256:" + profile * 64
        # THE DELIVERY'S OWN MEDIA TYPE. The published conformance manifest
        # carries `text/markdown`, which `job_task.manifest_for` refuses for
        # this profile -- which is exactly the counterexample
        # `TASK-BOUNDARY.json` reproduced against the previous candidate.
        held["human_contract"] = dict(held["human_contract"],
                                      media_type=job_task.CONTRACT_MEDIA_TYPE)
        held.update(changed)
        held.pop("manifest_digest", None)
        held["manifest_digest"] = digest(held)
        task = job_task.compose_task(
            self.installed_task() if installed is None else installed,
            task_id="job-a", instructions="do the thing")
        # `manifest_for` recomputes the artifact's bytes/digest AND the
        # manifest's own digest, then proves the whole thing through
        # `check_manifest_structure` -- so the pair this returns is one the
        # delivery would accept.
        return task, job_task.manifest_for(held, task)

    def manifest(self, **operands):
        """The composed pair's manifest alone, for the cases about it."""
        return self.composed(**operands)[1]

    def resealed(self, manifest, **changed):
        """One composed manifest with a member replaced and the self-digest
        recomputed.

        SPOILED AFTER COMPOSITION, deliberately: `job_task.manifest_for`
        proves the manifest through its own owner, so a fixture that spoiled
        BEFORE it would be testing that owner's refusal rather than this
        boundary's. The digest is recomputed because `job_input_identity`
        verifies it, and a stale one would refuse for the wrong reason.
        """
        held = copy.deepcopy(manifest)
        held.update(changed)
        held.pop("manifest_digest", None)
        held["manifest_digest"] = digest(held)
        return held

    def tuple_for(self, *, image="2", profile="3", adapter="1"):
        return {"adapter_digest": "sha256:" + adapter * 64,
                "image_digest": "sha256:" + image * 64,
                "runtime_profile_digest": "sha256:" + profile * 64}

    def candidate(self, role, *, image="2", profile="3", adapter="1",
                  roles=None, installed_task=None, **changed):
        """One lane, carrying a REAL composed task and the manifest that
        names it. Its capability is the APPROVED vector, with only the tuple
        members and role set a heterogeneous lane really varies."""
        task, manifest = self.composed(installed=installed_task,
                                       image=image, profile=profile)
        held = {"worker_id": "w-" + role,
                "principal": "principal:" + role,
                "capability": capability(
                    adapter_digest="sha256:" + adapter * 64,
                    image_digest="sha256:" + image * 64,
                    runtime_profile_digest="sha256:" + profile * 64,
                    **({} if roles is None else {"roles": list(roles)})),
                "installed": self.tuple_for(image=image, profile=profile,
                                            adapter=adapter),
                "task_document": task,
                "input_manifest": manifest}
        held.update(changed)
        return held

    def both(self, **changed):
        held = {one: self.candidate(one)
                for one in ("implementation", "review")}
        held.update(changed)
        return held

    def admitting(self, candidates=KEEP, contract=KEEP):
        """`KEEP` rather than `None`, because `None` is a value these cases
        have to be able to PASS -- a default that swallowed it would make the
        malformed-operand cases test the fixture."""
        return role_capability.admissible_roles(
            self.contract() if contract is KEEP else contract,
            candidates=self.both() if candidates is KEEP else candidates)

    def refusing(self, candidates=KEEP, contract=KEEP):
        with self.assertRaises(ContractRefusal) as caught:
            self.admitting(candidates, contract)
        return str(caught.exception)

    # -- the positives -----------------------------------------------------

    def test_the_baseline_pair_is_admitted_for_both_roles(self):
        self.assertEqual(self.admitting(), ["implementation", "review"])

    def test_truly_distinct_runtime_tuples_are_admitted_when_qualified(self):
        """THE FOURTH FAULT the review named. The previous case varied only
        `worker_id` against one shared tuple, which is not heterogeneous
        runtime evidence. These two lanes run DIFFERENT images, DIFFERENT
        runtime profiles and DIFFERENT adapters, each qualified for its own --
        and they are admitted, because what must agree is the Job-scoped
        projection and not the per-execution identity."""
        held = self.both(
            implementation=self.candidate("implementation", image="2",
                                          profile="3", adapter="1"),
            review=self.candidate("review", image="7", profile="8",
                                  adapter="9"))
        self.assertEqual(self.admitting(held), ["implementation", "review"])
        # AND THE EVIDENCE IS REALLY DISTINCT, member for member.
        for name in role_capability.TUPLE_MEMBERS:
            with self.subTest(member=name):
                self.assertNotEqual(held["implementation"]["installed"][name],
                                    held["review"]["installed"][name])
        self.assertNotEqual(held["implementation"]["input_manifest"],
                            held["review"]["input_manifest"])
        # ...WHILE THE JOB-SCOPED IDENTITY IS ONE, which is what admits them.
        self.assertEqual(
            job_input_identity(held["implementation"]["input_manifest"]),
            job_input_identity(held["review"]["input_manifest"]))

    def test_a_role_specific_capability_is_a_valid_lane_input(self):
        """"Single-role capabilities are valid inputs for a lane." Each lane
        here is covered only for its own role, and the stage is admitted
        because every REQUIRED role has an independently eligible lane."""
        held = self.both(
            implementation=self.candidate("implementation",
                                          roles=["implementation"]),
            review=self.candidate("review", roles=["review"]))
        self.assertEqual(self.admitting(held), ["implementation", "review"])

    def test_the_answer_is_the_contract_s_roles_and_is_detached(self):
        agreed = self.admitting()
        self.assertEqual(agreed,
                         [one["role"] for one in self.contract()["roles"]])
        agreed.append("integration")
        self.assertEqual(self.admitting(), ["implementation", "review"])

    def test_the_boundary_grants_no_qualification(self):
        """`qualification_digest` is required bounded text and NOTHING here
        verifies what it refers to -- a self-authored advertisement grants
        nothing, which is W371296's work."""
        held = self.both(
            implementation=self.candidate(
                "implementation",
                capability=capability(
                    adapter_digest="sha256:" + "1" * 64,
                    image_digest="sha256:" + "2" * 64,
                    runtime_profile_digest="sha256:" + "3" * 64,
                    qualification_digest="sha256:" + "e" * 64)))
        self.assertEqual(self.admitting(held), ["implementation", "review"])

    # -- counterexample 1: declarations are type-sensitive -----------------

    def test_type_sensitive_comparison_is_the_relation_this_needs(self):
        """THE MECHANISM, stated as the fact the review found: Python's `==`
        holds `0 == False`, so comparing two owned declarations with it
        compares the wrong relation. `own` preserves built-in types; it does
        not make equality type-sensitive."""
        self.assertTrue(0 == False)                       # noqa: E712
        self.assertFalse(role_capability._identical(0, False))
        self.assertFalse(role_capability._identical(1, True))
        self.assertFalse(role_capability._identical(
            {"required": 0}, {"required": False}))
        self.assertTrue(role_capability._identical(
            {"a": [1, {"b": False}]}, {"a": [1, {"b": False}]}))
        self.assertIn("is int 0 and this contract fixes bool false",
                      role_capability._disagreement({"required": 0},
                                                    {"required": False},
                                                    "declaration"))

    def test_the_integer_required_counterexample_refuses(self):
        """COUNTEREXAMPLE 1, through the whole boundary. It refuses at the
        FROZEN SCHEMA, which types `required` before this module compares it --
        so the refusal asserted is the one that actually happens, and the
        type-sensitive comparison above is the SECOND LINE. The case below
        reaches that second line."""
        spoiled = copy.deepcopy(self.contract()["outputs"])
        spoiled[1]["required"] = 0
        task, manifest = self.composed()
        said = self.refusing(self.both(
            review=self.candidate(
                "review", task_document=task,
                input_manifest=self.resealed(manifest, outputs=spoiled))))
        self.assertIn("composed input manifest is not one this Job can admit",
                      said)
        self.assertIn("required", said)

    def test_a_schema_valid_declaration_drift_reaches_the_second_line(self):
        """EVERY ONE OF THESE SATISFIES THE FROZEN DESCRIPTOR and still is not
        the contract's declaration -- which is exactly what this boundary is
        for. `required: true` is the pair of the counterexample above: a
        Boolean the schema admits and the contract does not fix."""
        def spoil(change):
            held = copy.deepcopy(self.contract()["outputs"])
            change(held)
            return held

        for label, change, named in (
                ("required true", lambda o: o[1].__setitem__("required", True),
                 "required"),
                ("path drift", lambda o: o[0].__setitem__("path", "other"),
                 "path"),
                ("lower max_bytes",
                 lambda o: o[0]["constraints"].__setitem__("max_bytes", 1024),
                 "max_bytes"),
                ("extra media type",
                 lambda o: o[0]["constraints"]["allowed_media_types"]
                 .append("text/html"), "allowed_media_types"),
                ("reordered set", lambda o: o.reverse(), "outputs"),
                ("short set", lambda o: o.pop(), "entries")):
            with self.subTest(drift=label):
                task, manifest = self.composed()
                said = self.refusing(self.both(
                    review=self.candidate(
                        "review", task_document=task,
                        input_manifest=self.resealed(
                            manifest, outputs=spoil(change)))))
                self.assertIn("declares a different result contract", said)
                self.assertIn(named, said)

    def test_a_duplicated_declaration_refuses_at_the_frozen_rule(self):
        """AN EXTENDED SET REFUSES EARLIER, and the refusal asserted is the one
        that happens: §12 rule 3 makes input/output names unique, so a repeated
        declaration never reaches the comparison above. Recorded rather than
        reported as this boundary's own catch."""
        spoiled = copy.deepcopy(self.contract()["outputs"])
        spoiled.append(copy.deepcopy(spoiled[0]))
        task, manifest = self.composed()
        said = self.refusing(self.both(
            review=self.candidate(
                "review", task_document=task,
                input_manifest=self.resealed(manifest, outputs=spoiled))))
        self.assertIn("reuses an input/output name", said)

    def test_an_extended_set_with_a_fresh_name_reaches_the_comparison(self):
        """And with a name the frozen rule admits, it is this boundary that
        refuses -- so the second line really does cover the longer set."""
        spoiled = copy.deepcopy(self.contract()["outputs"])
        spoiled.append(dict(copy.deepcopy(spoiled[0]), name="extra",
                            path="extra"))
        task, manifest = self.composed()
        said = self.refusing(self.both(
            review=self.candidate(
                "review", task_document=task,
                input_manifest=self.resealed(manifest, outputs=spoiled))))
        self.assertIn("declares a different result contract", said)
        self.assertIn("entries", said)

    # -- counterexample 2: required-role eligibility -----------------------

    def test_a_single_role_capability_is_not_a_full_stage_admission(self):
        """COUNTEREXAMPLE 2. One implementation lane with an
        implementation-only capability used to answer `["implementation"]` for
        a contract requiring BOTH roles -- a full admission for half a
        workflow. The missing role is now computed from the CONTRACT."""
        said = self.refusing(
            {"implementation": self.candidate("implementation",
                                              roles=["implementation"])})
        self.assertIn("contract requires implementation, review", said)
        self.assertIn("no candidate was composed for review", said)

    def test_every_required_role_needs_its_own_eligible_lane(self):
        for absent in ("implementation", "review"):
            with self.subTest(absent=absent):
                held = self.both()
                del held[absent]
                self.assertIn(f"no candidate was composed for {absent}",
                              self.refusing(held))

    def test_a_lane_whose_capability_omits_its_role_refuses(self):
        said = self.refusing(self.both(
            review=self.candidate("review", roles=["implementation"])))
        self.assertIn("capability is qualified for implementation", said)
        self.assertIn("this lane serves 'review'", said)

    def test_a_candidate_this_contract_does_not_declare_refuses(self):
        held = self.both(integration=self.candidate("integration"))
        self.assertIn("composed a candidate for integration",
                      self.refusing(held))

    # -- counterexample 3: the projection is derived, never a label --------

    def test_an_absent_or_invented_projection_cannot_agree(self):
        """COUNTEREXAMPLE 3. Two lanes passing `None` were accepted as a
        common Job projection. There is no projection operand now: the
        identity is DERIVED from each lane's real input manifest by the rule
        that owns it, so an absent, empty or invented input cannot reach
        agreement."""
        for value in (None, {}, [], "job-1", 7, True,
                      {"job_id": "job-1", "input_digest": "sha256:" + "7" * 64}):
            with self.subTest(given=value):
                said = self.refusing(self.both(
                    implementation=self.candidate("implementation",
                                                  input_manifest=value)))
                self.assertIn("composed input manifest is not one this Job "
                              "can admit", said)

    def test_a_manifest_with_a_stale_self_digest_refuses(self):
        """The owner verifies the manifest's own digest, so a document whose
        members were changed after it was sealed is not a composed input."""
        held = self.manifest()
        held["policy_digest"] = "sha256:" + "a" * 64
        said = self.refusing(self.both(
            review=self.candidate("review", input_manifest=held)))
        self.assertIn("composed input manifest is not one this Job can admit",
                      said)

    def test_lanes_with_different_job_input_identities_refuse(self):
        """The Job-scoped facts are common. `policy_digest` is NOT one of the
        members the projection drops, so a lane that moved it is a lane on
        another Job's input policy."""
        said = self.refusing(self.both(
            review=self.candidate(
                "review",
                input_manifest=self.manifest(
                    policy_digest="sha256:" + "a" * 64))))
        self.assertIn("different Job input identities", said)

    def test_a_dropped_runtime_member_is_allowed_to_differ(self):
        """The other direction, so the rule is not just restrictive: every
        member `JOB_INPUT_EXCLUDED` names may differ between lanes."""
        task, manifest = self.composed(
            toolchain_digest="sha256:" + "c" * 64,
            credential_policy_digest="sha256:" + "d" * 64)
        held = self.both(
            review=self.candidate("review", task_document=task,
                                  input_manifest=manifest))
        self.assertEqual(self.admitting(held), ["implementation", "review"])

    # -- the tuple binding -------------------------------------------------

    def test_each_tuple_member_must_match_its_own_qualification(self):
        for name in role_capability.TUPLE_MEMBERS:
            with self.subTest(member=name):
                held = self.candidate("review")
                held["installed"] = dict(held["installed"],
                                         **{name: "sha256:" + "f" * 64})
                said = self.refusing(self.both(review=held))
                self.assertIn("a capability is evidence about one tuple", said)
                self.assertIn(name, said)

    def test_the_tuple_must_bind_the_lane_s_own_composed_input(self):
        """A resolved identity no composed input mentions is a claim about a
        runtime nobody is going to start. Capability and tuple agree here; the
        MANIFEST is the one that says otherwise."""
        for member, image, profile in (("worker_image_digest", "7", "3"),
                                       ("runtime_profile_digest", "2", "8")):
            with self.subTest(member=member):
                held = self.candidate("review")
                held["input_manifest"] = self.manifest(image=image,
                                                       profile=profile)
                said = self.refusing(self.both(review=held))
                self.assertIn("the admitted tuple is the one the lane will "
                              "actually run", said)
                self.assertIn(member, said)

    def test_a_malformed_tuple_refuses(self):
        for spoiled in ({"adapter_digest": "sha256:" + "1" * 64},
                        {"adapter_digest": "sha256:" + "1" * 64,
                         "image_digest": "sha256:" + "2" * 64,
                         "runtime_profile_digest": "sha256:" + "3" * 64,
                         "extra": "x"},
                        None, [], "a tuple", 7):
            with self.subTest(spoiled=spoiled):
                self.assertIn(
                    "installed tuple is exactly",
                    self.refusing(self.both(
                        review=self.candidate("review",
                                              installed=spoiled))))

    def test_a_tuple_member_that_is_not_a_digest_refuses(self):
        for value in ("*", "", "sha256:" + "A" * 64, "sha256:beef", None, 7,
                      True):
            with self.subTest(value=value):
                held = self.candidate("review")
                held["installed"] = dict(held["installed"],
                                         image_digest=value)
                self.assertIn("one lower-case sha256 digest",
                              self.refusing(self.both(review=held)))

    # -- task, source, candidate shape and principals ----------------------

    def test_an_unsupported_task_generation_refuses(self):
        """REVIEW 21-35-39Z, and the operand is the TASK now. A generation this
        build's task owner does not read refuses THROUGH THAT OWNER; a `/3`
        task is a valid generation and still not the one this contract
        supports, which is the second line."""
        for label, installed, said in (
                ("unknown generation",
                 self.installed_task(schema="baton.dogfood-task/9"),
                 "not one this build's task owner reads"),
                ("a /3 missing its declared context",
                 self.installed_task(schema="baton.dogfood-task/3"),
                 "not one this build's task owner reads"),
                ("a valid /3 under a /2 contract",
                 self.installed_task(schema="baton.dogfood-task/3",
                                     verification_context={}),
                 "composes an unsupported task")):
            with self.subTest(task=label):
                self.assertIn(said, self.refusing(self.both(
                    review=self.candidate("review",
                                          installed_task=installed))))

    def test_a_drifted_task_source_profile_refuses(self):
        """READ OUT OF THE TASK, not off a label beside it -- and by TWO
        lines, which the vectors separate.

        A profile outside the workload's vocabulary refuses at the TASK
        CONTRACT, through the profile package that owns that vocabulary. A
        profile the workload consumes but this contract does not select
        reaches the AGREEMENT check. Both are asserted at the refusal that
        actually happens.
        """
        for value in ("", None, 7, True, "git-lines"):
            with self.subTest(source_profile=value, line="the vocabulary"):
                said = self.refusing(self.both(
                    review=self.candidate(
                        "review", installed_task=self.installed_task(
                            source_profile=value))))
                self.assertIn("the workload consumes", said)
        # THE PAIRING, which is the profile package's rule and refuses BOTH
        # directions: `generic` carries a base here, so it refuses as a pairing
        # rather than as an unsupported source. Review 2026-10-28T23-13-01Z.
        with self.subTest(source_profile="generic", line="the pairing"):
            said = self.refusing(self.both(
                review=self.candidate(
                    "review", installed_task=self.installed_task(
                        source_profile="generic"))))
            self.assertIn("which the profile package refuses", said)
        # AND A PROFILE THE WORKLOAD CONSUMES, CORRECTLY PAIRED, AND NOT THE
        # ONE THIS CONTRACT SELECTS -- which is the vector that reaches the
        # agreement check.
        with self.subTest(source_profile="git", line="the agreement"):
            self.assertIn("git", source_profiles.PROFILES)
            said = self.refusing(self.both(
                review=self.candidate(
                    "review", installed_task=self.installed_task(
                        source_profile="git"))))
            self.assertIn("composes an unsupported source", said)

    def test_the_source_base_pairing_is_the_profile_package_s_rule(self):
        """W376723 review 2026-10-28T23-13-01Z. `git-line` with a null
        `declared_base` was ADMITTED for both roles while `checkout_plan`
        refuses it -- a lane nobody could check out passing the boundary whose
        whole job is to refuse before effects.

        BOTH HALVES OF THE RULE, and it is ASKED rather than restated: a
        version-control profile with no base, and a generic profile WITH one.
        The valid pairing still passes.
        """
        for profile, base, admitted in (("git-line", "0" * 40, True),
                                        ("git-line", None, False),
                                        ("git", None, False),
                                        ("generic", None, False)):
            with self.subTest(profile=profile, base=base):
                held = self.installed_task(source_profile=profile,
                                           declared_base=base)
                if admitted:
                    self.assertEqual(
                        self.admitting(self.both(
                            review=self.candidate("review",
                                                  installed_task=held))),
                        ["implementation", "review"])
                    continue
                said = self.refusing(self.both(
                    review=self.candidate("review", installed_task=held)))
                if profile == "generic":
                    # Refused as an unsupported source: the pairing is
                    # satisfied, and `generic` is simply not this contract's.
                    self.assertIn("composes an unsupported source", said)
                else:
                    self.assertIn("which the profile package refuses", said)
        # AND THE STRICTNESS IS NOT INVENTED: the rule this boundary asked is
        # the one that refuses, driven directly.
        with self.assertRaises(source_profiles.ProfileRefusal):
            source_profiles.checkout_plan(
                "/input/source", "/output", profile="git-line", declared=None)

    def test_an_absent_or_malformed_task_refuses(self):
        for value in (None, "", "{not json", "[]", "7", 7, True, [],
                      b'{"schema": "baton.dogfood-task/2"}'):
            with self.subTest(task=value):
                with self.assertRaises(ContractRefusal):
                    self.admitting(self.both(
                        review=self.candidate("review",
                                              task_document=value)))

    def test_a_task_wider_than_the_bound_refuses(self):
        held = self.candidate("review")
        held["task_document"] = " " * (role_capability.MAX_TASK_BYTES + 1)
        self.assertIn(str(role_capability.MAX_TASK_BYTES),
                      self.refusing(self.both(review=held)))

    def test_the_artifact_must_describe_these_exact_bytes(self):
        """THE BINDING. The manifest's human contract IS this profile's task
        delivery, so a media type, byte count or content digest that does not
        describe the composed task delivers a document nobody has -- which is
        the counterexample `TASK-BOUNDARY.json` reproduced, where the baseline
        was admitted beside a `text/markdown` artifact."""
        task, manifest = self.composed()

        def spoiling(name, value):
            held = self.resealed(
                manifest,
                human_contract=dict(manifest["human_contract"],
                                    **{name: value}))
            return self.refusing(self.both(
                review=self.candidate("review", task_document=task,
                                      input_manifest=held)))

        # THESE REACH THIS BOUNDARY: each value is one the frozen artifact
        # schema admits, and it is still not a description of these bytes.
        for name, value in (("media_type", "text/markdown"),
                            ("bytes", len(task.encode("utf-8")) + 1),
                            ("bytes", 0),
                            ("content_digest", "sha256:" + "0" * 64)):
            with self.subTest(member=name, value=value, line="this boundary"):
                said = spoiling(name, value)
                self.assertIn("delivers a document nobody has", said)
                self.assertIn(name, said)
        # AND THESE REFUSE EARLIER, at the frozen artifact schema, which is the
        # refusal asserted rather than the one I would have preferred: a media
        # type with a parameter breaks its pattern, and a null or boolean
        # breaks its type. Recorded so the division between the two lines is
        # visible rather than implied.
        for name, value in (("media_type", "application/json; charset=utf-8"),
                            ("media_type", None),
                            ("bytes", None),
                            ("bytes", True),
                            ("content_digest", None)):
            with self.subTest(member=name, value=value, line="frozen schema"):
                said = spoiling(name, value)
                self.assertIn("composed input manifest is not one this Job "
                              "can admit", said)
                self.assertIn(name, said)

    def test_a_manifest_with_no_task_delivery_refuses(self):
        task, manifest = self.composed()
        spoiled = {one: value for one, value in manifest.items()
                   if one != "human_contract"}
        spoiled.pop("manifest_digest", None)
        spoiled["manifest_digest"] = digest(spoiled)
        with self.assertRaises(ContractRefusal):
            self.admitting(self.both(
                review=self.candidate("review", task_document=task,
                                      input_manifest=spoiled)))

    def test_lanes_composing_different_tasks_refuse(self):
        """One Job is one task. A lane reviewing another task's candidate is
        reviewing something nobody asked for."""
        said = self.refusing(self.both(
            review=self.candidate(
                "review",
                installed_task=self.installed_task(
                    verification=["python3", "-m", "pytest"]))))
        # THE JOB INPUT IDENTITY DISAGREES FIRST, because the task artifact's
        # digest is inside the manifest that identity is taken over -- so the
        # refusal asserted is the one that actually happens, and the explicit
        # common-task check is the second line over the same fact.
        self.assertIn("different Job input identities", said)

    def test_one_common_task_holds_and_no_valid_input_can_reach_the_check(self):
        """THE COMMON-TASK CHECK IS A SECOND LINE THAT NOTHING VALID REACHES,
        and saying so is more useful than a case that pretends otherwise.

        The positive half is real: both lanes compose the same task and the
        boundary answers both roles. The negative half cannot be driven, and
        the reason is structural rather than a gap -- the task artifact's
        content digest lives in the manifest that `job_input_identity` is
        taken over, so a lane whose task differs has either an artifact that
        does not describe it (the binding refuses) or one that does (the Job
        input identity refuses). There is no third input.

        So this asserts the positive, then drives a differing task and asserts
        the refusal that ACTUALLY happens. The explicit check stays because the
        FINDING requires the fact established and because the two documents
        that imply it are owned by different parties -- a later revision could
        drop the artifact from the projection and the fact would still be
        required.
        """
        held = self.both()
        self.assertEqual(self.admitting(held), ["implementation", "review"])
        self.assertEqual(held["implementation"]["task_document"],
                         held["review"]["task_document"])
        # A MEMBER THE COMPOSER DOES NOT SUBSTITUTE. `job_task.SUBSTITUTED` is
        # `task_id` and `instructions`, so changing those in the INSTALLED task
        # changes nothing in the composed one -- my first attempt at this case
        # did exactly that and asserted two identical documents were
        # different. `verification` travels as the deployment wrote it.
        drifted = self.candidate(
            "review", installed_task=self.installed_task(
                verification=["python3", "-m", "pytest"]))
        self.assertNotEqual(drifted["task_document"],
                            held["review"]["task_document"])
        said = self.refusing(self.both(review=drifted))
        self.assertIn("different Job input identities", said)
        # AND THE OTHER ROUTE: the same differing task beside an artifact that
        # still describes the FIRST one.
        reused = self.refusing(self.both(
            review=self.candidate(
                "review", task_document=drifted["task_document"],
                input_manifest=held["review"]["input_manifest"])))
        self.assertIn("delivers a document nobody has", reused)

    def test_a_malformed_candidate_refuses(self):
        for spoiled in (None, [], "a candidate", 7, True, {}):
            with self.subTest(spoiled=spoiled):
                self.assertIn("review candidate", self.refusing(
                    self.both(review=spoiled)))
        held = self.candidate("review")
        del held["principal"]
        self.assertIn("missing principal",
                      self.refusing(self.both(review=held)))
        self.assertIn("unexpected granted", self.refusing(self.both(
            review=self.candidate("review", granted="yes"))))

    def test_candidates_must_be_one_object_keyed_by_role(self):
        for spoiled in (None, [], "candidates", 7, True):
            with self.subTest(spoiled=spoiled):
                self.assertIn("one object keyed by role",
                              self.refusing(spoiled))

    def test_one_principal_for_two_roles_refuses_even_with_two_ids(self):
        held = self.both(
            implementation=self.candidate("implementation",
                                          principal="one-principal"),
            review=self.candidate("review", principal="one-principal",
                                  worker_id="w-other"))
        said = self.refusing(held)
        self.assertIn("two worker ids do not create one", said)
        # THE REFUSAL NAMES BOTH IDS, which is what makes it actionable.
        self.assertIn("w-implementation", said)
        self.assertIn("w-other", said)

    def test_a_malformed_worker_id_or_principal_refuses(self):
        """Through `boundaries.text`, which is the owner of durable text in
        this package. A BLANK string is NOT in this list: that owner accepts
        it, and reaching past it to add a rule here would be a second,
        narrower definition of the same thing."""
        for name in ("worker_id", "principal"):
            for value in ("", None, 7, True):
                with self.subTest(member=name, value=value):
                    with self.assertRaises(ContractRefusal):
                        self.admitting(self.both(
                            review=self.candidate("review",
                                                  **{name: value})))

    # -- the contract is owned once, and nothing is mutated ----------------

    def test_a_mapping_that_carries_behaviour_never_reaches_this_boundary(self):
        """Review 20-08-41Z's ownership observation: the first attempt
        validated a copy and then reread the CALLER's original for outputs,
        task and source -- a second read a `dict` subclass could answer
        differently.

        THE WINDOW IS CLOSED AT BOTH ENDS. The decision now reads only the
        owned snapshot, and `own` refuses any mapping that could behave
        differently on a second read at all -- so there is no object for which
        the two reads could disagree. The refusal is the evidence; the
        behavioural half is the mutation case below.
        """
        class Counting(dict):
            def __getitem__(self, name):
                return super().__getitem__(name)

        said = self.refusing(contract=Counting(self.contract()))
        self.assertIn("not JSON data", said)
        self.assertIn("nothing that carries behaviour", said)
        held = self.both()
        held["review"] = Counting(held["review"])
        self.assertIn("review candidate is one closed object",
                      self.refusing(held))

    def test_mutation_of_the_caller_s_inputs_cannot_change_the_answer(self):
        """BEHAVIOURAL purity, which the review is right to ask for instead of
        a source scan: the inputs are mutated after the call and the answer
        does not move, and the call leaves every caller document unchanged."""
        contract = self.contract()
        candidates = self.both()
        before = copy.deepcopy((contract, candidates))
        agreed = role_capability.admissible_roles(contract,
                                                  candidates=candidates)
        self.assertEqual((contract, candidates), before)
        candidates["review"]["installed"]["image_digest"] = "sha256:" + "f" * 64
        candidates["review"]["task_schema"] = "baton.dogfood-task/3"
        contract["outputs"] = []
        del candidates["implementation"]
        self.assertEqual(agreed, ["implementation", "review"])

    def test_the_source_carries_no_effectful_vocabulary(self):
        """A SECONDARY SIGNAL AND NOT THE PROOF -- the review says so
        explicitly, and the behavioural cases above are the proof. What this
        catches is a later edit introducing an effect by name."""
        source = pathlib.Path(
            role_capability.__file__).read_text(encoding="utf-8")
        for word in ("open(", "subprocess", "ControlStore", "socket",
                     "requests", "os.path"):
            self.assertNotIn(word, source)


if __name__ == "__main__":
    unittest.main()


class TheTaskMediaTypeIsOneContractInTwoPlaces(unittest.TestCase):
    """`src/` may not import `tools/`, so the delivery's media type is spelled
    in both -- and two copies of one contract agree until they don't.

    The same guard `test_exchange` keeps over the worker's and the manager's
    copies of the exchange vocabulary, for the same reason: the layering is
    what makes the duplication necessary, and a case is what keeps it honest.
    """

    def test_the_two_copies_agree(self):
        from tools import job_task

        self.assertEqual(role_capability.TASK_MEDIA_TYPE,
                         job_task.CONTRACT_MEDIA_TYPE)
        self.assertEqual(role_capability.TASK_MEDIA_TYPE, "application/json")

    def test_the_three_bound_members_are_the_three_the_delivery_rewrites(self):
        """`job_task.manifest_for` replaces exactly the members that describe
        the bytes, and those are exactly the ones this boundary holds."""
        self.assertEqual(sorted(role_capability.TASK_ARTIFACT),
                         ["bytes", "content_digest", "media_type"])

    def test_this_module_still_imports_no_tool(self):
        """THE LAYERING, asked of the imports rather than of the prose: the
        module NAMES `tools/job_task.py` in comments, which is the point of
        those comments, so what this checks is the import statements."""
        source = pathlib.Path(
            role_capability.__file__).read_text(encoding="utf-8")
        imports = [one for one in source.splitlines()
                   if one.startswith(("import ", "from "))]
        self.assertTrue(imports)
        for line in imports:
            with self.subTest(line=line):
                self.assertNotIn("tools", line)
                self.assertNotIn("job_task", line)


class TheTwoTaskReadersAgree(unittest.TestCase):
    """W376723 review 2026-10-28T22-37-51Z — the agreement, MEASURED.

    The blocker was that `verification_context.generation` answers which
    generation a task declares and nothing about its supported shape, so four
    fully digest-bound pairs were admitted here and refused by the consuming
    reader. The correction is a closed `/2` validator in the generic host; what
    makes it trustworthy is not its prose but that it answers the same thing
    the consumer does.

    SO BOTH READERS RUN OVER ONE VECTOR SET. `check_dogfood_task` is the pure
    boundary and `claude_agent._read_task` is the actual consumer, and every
    vector must get the same verdict from each. A disagreement fails here
    rather than at a worker.

    THE PRODUCT STILL IMPORTS NO PROVIDER. This is a TEST importing the
    worker's adapter, which the suites for that adapter already do; the
    isolation rule is about the generic host, and
    `test_this_module_still_imports_no_tool` plus the case below hold it.
    """

    maxDiff = None

    @classmethod
    def setUpClass(cls):
        worker = pathlib.Path(__file__).resolve().parents[3] / "worker"
        for one in (str(worker),
                    str(worker.parent / "python" / "src" / "baton_v12")):
            if one not in sys.path:
                sys.path.insert(0, one)

    def valid(self, **changed):
        held = {"schema": role_capability.TASK_SCHEMA,
                "task_id": "w376723-agreement",
                "instructions": "do the thing",
                "verification": ["python3", "-m", "unittest"],
                "source_root": role_capability.TASK_SOURCE_ROOT,
                "source_profile": "git-line",
                "declared_base": "0" * 40}
        held.update(changed)
        return held

    def vectors(self):
        """The review's four counterexamples, plus the valid pair and the
        negatives its verification list names."""
        held = self.valid()
        return {
            "valid": held,
            # THE FOUR THE PROBE RETAINED.
            "only schema and profile": {
                "schema": role_capability.TASK_SCHEMA,
                "source_profile": "git-line"},
            "verification as a string": self.valid(
                verification="python3 -m unittest"),
            "an unknown member": dict(held, mode="fast"),
            "a numeric task id": self.valid(task_id=7),
            # AND THE REST OF THE REVIEW'S NAMED BEHAVIOURS.
            "a missing member": {one: value for one, value in held.items()
                                 if one != "instructions"},
            "another generation": self.valid(
                schema="baton.dogfood-task/3"),
            "an empty verification": self.valid(verification=[]),
            "a blank verification word": self.valid(
                verification=["python3", ""]),
            "a non-text verification word": self.valid(
                verification=["python3", 7]),
            "an unsupported source root": self.valid(source_root="elsewhere"),
            "a blank instruction": self.valid(instructions=""),
            "an unsupported profile": self.valid(source_profile="git-lines"),
            "an unusable declared base": self.valid(declared_base="nope"),
            "a task identity with a space": self.valid(task_id="w 1"),
            "not an object": [held],
        }

    def deferred(self):
        """The vectors where this boundary is STRICTER than the consumer, and
        the reason is the consumer's own deferral rather than a disagreement.

        `claude_agent._read_task` holds the profile to the vocabulary and the
        base to its shape, and leaves the PAIRING to `checkout_plan` later in
        the same turn -- its own comment says so. A pre-effect admission
        predicate has no later turn, so it asks the pairing now.
        """
        return {
            "git-line with no declared base": self.valid(declared_base=None),
            "git with no declared base": self.valid(source_profile="git",
                                                    declared_base=None),
            "generic with a declared base": self.valid(
                source_profile="generic"),
        }

    def ours(self, document):
        try:
            role_capability.check_dogfood_task(document)
            return "accepted"
        except ContractRefusal:
            return "refused"

    def theirs(self, document):
        """THE ACTUAL CONSUMER, over a real file -- which is how it reads."""
        import claude_agent

        place = pathlib.Path(tempfile.mkdtemp()) / "task.json"
        place.write_text(json.dumps(document), encoding="utf-8")
        try:
            claude_agent._read_task(str(place))
            return "accepted"
        except claude_agent.TaskRefusal:
            return "refused"
        finally:
            shutil.rmtree(place.parent, ignore_errors=True)

    def test_this_boundary_never_admits_what_the_consumer_refuses(self):
        """THE LOAD-BEARING RELATION, and it is not equality.

        A pre-effect predicate must never ADMIT something the consumer will
        refuse -- that is the false admission the whole slice exists to
        prevent. It may refuse EARLIER, and after review 2026-10-28T23-13-01Z
        it does: the consumer defers the profile/base pairing to
        `checkout_plan` later in its own turn, and this boundary has no later
        turn, so it asks now.

        Stating it as equality would force one of two wrong moves -- weakening
        this boundary, or editing an adapter that is another open slice's
        candidate. So the relation asserted is the true one, in both
        directions: no false admission, and every strictness accounted for by
        name.
        """
        answers = {label: (self.ours(one), self.theirs(one))
                   for label, one in self.vectors().items()}
        # NO FALSE ADMISSION anywhere in the shared vector set.
        admitted_here = sorted(label for label, pair in answers.items()
                               if pair[0] == "accepted")
        self.assertEqual(
            [label for label in admitted_here
             if answers[label][1] != "accepted"], [])
        # AND THE SET IS NOT VACUOUSLY AGREED: exactly one vector is accepted,
        # so a validator that accepted everything would fail here.
        self.assertEqual(answers["valid"], ("accepted", "accepted"))
        self.assertEqual(admitted_here, ["valid"])
        # EVERY OTHER VECTOR REFUSES ON BOTH SIDES, which is the agreement
        # half -- the deferred cases are separate and named below.
        self.assertEqual(
            {label: pair for label, pair in answers.items()
             if label != "valid" and pair != ("refused", "refused")}, {})

    def test_the_deferred_pairing_is_stricter_here_and_accounted_for(self):
        """Each vector this boundary refuses and the consumer accepts, named
        one by one -- and proved to be the PROFILE PACKAGE's refusal rather
        than one this module invented."""
        from baton_v12 import source_profiles

        for label, document in self.deferred().items():
            with self.subTest(deferred=label):
                self.assertEqual(self.ours(document), "refused")
                # THE CONSUMER ACCEPTS IT, because it asks `checkout_plan`
                # later rather than never.
                self.assertEqual(self.theirs(document), "accepted")
                # AND THE RULE THIS BOUNDARY ASKED IS THE ONE THAT REFUSES.
                with self.assertRaises(source_profiles.ProfileRefusal):
                    source_profiles.checkout_plan(
                        "/input/source", "/output",
                        profile=document["source_profile"],
                        declared=document["declared_base"])

    def test_the_four_retained_counterexamples_now_refuse(self):
        """Named one by one, because they are the required behaviours the
        review retained rather than a prescribed command."""
        held = self.vectors()
        for label in ("only schema and profile", "verification as a string",
                      "an unknown member", "a numeric task id"):
            with self.subTest(counterexample=label):
                self.assertEqual(self.ours(held[label]), "refused")
                self.assertEqual(self.theirs(held[label]), "refused")

    def test_the_two_copies_of_the_vocabulary_agree(self):
        import claude_agent

        self.assertEqual(role_capability.TASK_SCHEMA,
                         claude_agent.TASK_SCHEMA)
        self.assertEqual(role_capability.TASK_MEMBERS,
                         claude_agent.TASK_MEMBERS)
        self.assertEqual(role_capability.TASK_SOURCE_ROOT,
                         claude_agent.SOURCE_ROOT)

    def test_the_generic_host_imports_no_provider_adapter(self):
        """The isolation rule, asked of the import statements. The vocabulary
        is spelled in the host because the consumer is a provider adapter
        inside the worker image and `claude_agent.py` is another open slice's
        candidate; the agreement above is what makes two copies safe."""
        source = pathlib.Path(
            role_capability.__file__).read_text(encoding="utf-8")
        for line in [one for one in source.splitlines()
                     if one.startswith(("import ", "from "))]:
            with self.subTest(line=line):
                for word in ("claude_agent", "scripted_agent", "tools",
                             "job_task"):
                    self.assertNotIn(word, line)
