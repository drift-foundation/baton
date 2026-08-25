"""W4 cut A — the frozen schemas as package data, and the taxonomy they type.

The manager carries its contract instead of reaching for a checkout, so these
cases prove the copy is the SAME DOCUMENT and that the semantic rules derived
from it were derived rather than retyped.
"""

import hashlib
import json
import pathlib
import unittest

import baton_v12.contracts as contracts
from baton_v12.contracts import (AGENT_SESSION_BYTES, CAPABILITIES,
                                 ERROR_CODES, OPAQUE_ID_LIMIT, PROTOCOL,
                                 VERSION, WORKER_CONTROL, WORKER_CONTROL_BYTES)
from baton_v12.contracts import frozen

HERE = pathlib.Path(__file__).resolve()
DISTRIBUTION = HERE.parents[2]
REPOSITORY = DISTRIBUTION.parents[1]

# The canonical dossier assets: the documents these copies are copies OF.
CANONICAL = {
    "worker-control-1.0.schema.json":
        REPOSITORY / "work" / "records" / "2026" / "08"
        / "finding-v12-isolated-agent-workers" / "findings"
        / "finding-v12-worker-contract" / "findings"
        / "finding-worker-control-api-manifests" / "schema"
        / "worker-control-1.0.schema.json",
    "agent-session-1.0.schema.json":
        REPOSITORY / "work" / "records" / "2026" / "08"
        / "finding-v12-isolated-agent-workers" / "findings"
        / "finding-v12-worker-contract" / "findings"
        / "finding-acp-agent-boundary" / "schema"
        / "agent-session-1.0.schema.json",
}

# The frozen Node host's copies, which are the same documents again. Three
# copies of one contract is what the campaign chose; what must never happen is
# the three drifting, so all three are compared rather than two.
NODE_COPIES = {
    name: REPOSITORY / "v12" / "src" / "worker_manager" / "schema" / name
    for name in CANONICAL
}


class TheSchemaTravelsWithTheDistribution(unittest.TestCase):

    def test_the_packaged_copy_is_byte_identical_to_the_canonical_asset(self):
        # BYTES, not a parsed comparison: a parse-then-dump round trip would
        # accept a reformatted document, and the digest recorded in the dossier
        # is over the bytes.
        packaged = {"worker-control-1.0.schema.json": WORKER_CONTROL_BYTES,
                    "agent-session-1.0.schema.json": AGENT_SESSION_BYTES}
        for name, path in CANONICAL.items():
            with self.subTest(schema=name):
                # The role instruction is to report a file I cannot read as an
                # operational finding rather than proceeding without it. This is
                # that check, standing rather than done once.
                self.assertTrue(path.is_file(), f"canonical asset missing: {path}")
                self.assertEqual(packaged[name], path.read_bytes())
                self.assertTrue(NODE_COPIES[name].is_file())
                self.assertEqual(packaged[name], NODE_COPIES[name].read_bytes())

    def test_the_recorded_digests_still_hold(self):
        # The numbers the boundary review measured, re-measured rather than
        # quoted: a digest in a document and a digest in a tree are different
        # facts.
        for name, expected in [
                ("worker-control-1.0.schema.json",
                 "be1a536bc9aa2d7e23749cf54ceb98906f8dceeb8de9d72e2abc17b9baf18658"),
                ("agent-session-1.0.schema.json",
                 "22e6e61c8fbe4b4312b0bc5e33e5be23dff7ba944e213a2855106dc06b55202c")]:
            with self.subTest(schema=name):
                self.assertEqual(
                    hashlib.sha256(frozen.schema_bytes(name)).hexdigest(),
                    expected)

    def test_the_schema_is_read_from_wherever_the_package_was_imported(self):
        # The installed gate imports this package out of site-packages, so the
        # asset has to be found BESIDE THE MODULE rather than relative to a
        # source tree. This case passes in both layouts, which is the point:
        # the source run and the wheel run assert the same thing.
        origin = pathlib.Path(contracts.__file__).parent
        self.assertTrue((origin / "schema" /
                         "worker-control-1.0.schema.json").is_file())
        self.assertEqual(json.loads(WORKER_CONTROL_BYTES.decode("utf-8")),
                         WORKER_CONTROL)

    def test_both_documents_declare_draft_2020_12(self):
        for name, document in [("worker-control", WORKER_CONTROL),
                               ("agent-session", frozen.AGENT_SESSION)]:
            with self.subTest(schema=name):
                self.assertEqual(document["$schema"],
                                 "https://json-schema.org/draft/2020-12/schema")


class TheSemanticRulesAreDerivedFromTheSchema(unittest.TestCase):

    def test_the_category_code_pairing_covers_the_schema_exactly(self):
        """§12's semantic pairing, checked against the frozen vocabularies.

        The schema carries `category` and `code` as flat enums and does not pair
        them. So the pairing is written out in `errors.py` -- and if a code were
        added to the frozen schema without a category, or a category invented
        here that the schema does not carry, this fails loudly instead of the
        code quietly becoming unmappable.
        """
        # BOTH sides are computed here, from their own sources: the pairing
        # from `errors.ERROR_CODES` and the vocabularies from the parsed
        # schema. A helper in the product that returned "the schema's codes"
        # would make this agree with itself -- measured, that mutation had NO
        # WITNESS until the derivation moved into the case.
        paired = [code for codes in ERROR_CODES.values() for code in codes]
        self.assertEqual(sorted(ERROR_CODES),
                         sorted(frozen.schema_error_categories()))
        self.assertEqual(sorted(paired), sorted(frozen.schema_error_codes()))

    def test_no_code_is_paired_with_two_categories(self):
        # A code in two categories is a code whose wire meaning depends on which
        # site raised it, which is exactly what a closed pairing is for.
        codes = [code for codes in ERROR_CODES.values() for code in codes]
        self.assertEqual(len(codes), len(set(codes)))

    def test_the_opaque_id_bound_is_taken_from_the_schema(self):
        # A limit written twice is a limit that holds in one of the two places.
        # The frozen host produced a FALSE DIAGNOSTIC from exactly this -- "is
        # 162 characters" about an 81-character string -- because two sites
        # measured in different units.
        self.assertEqual(OPAQUE_ID_LIMIT,
                         WORKER_CONTROL["$defs"]["opaqueId"]["maxLength"])
        self.assertEqual(frozen.OPAQUE_ID_PATTERN,
                         WORKER_CONTROL["$defs"]["opaqueId"]["pattern"])

    def test_the_protocol_and_capabilities_are_the_frozen_ones(self):
        self.assertEqual(PROTOCOL, "baton.worker-control")
        self.assertEqual(VERSION, {"major": 1, "minor": 0})
        self.assertIn("core.errors", CAPABILITIES)
        self.assertEqual(len(CAPABILITIES), len(set(CAPABILITIES)))


class ThePairIsCheckedWhereItIsRaised(unittest.TestCase):
    """A guard for a pair nobody has spelled wrong YET.

    Found by a mutation with no witness: every raising site in this cut uses a
    valid pair, so removing the check changed nothing. That is what a guard
    against a future mistake looks like from inside a suite, and the answer is a
    case that makes the future mistake on purpose.

    It is an `AssertionError` rather than a `ContractRefusal` deliberately: a
    caller sending a bad document is an ordinary refusal, and THIS PACKAGE
    spelling its own wire vocabulary wrong is a defect in this package.
    """

    def test_an_unpaired_category_or_code_is_a_defect_not_a_refusal(self):
        from baton_v12.contracts import ContractRefusal as Refusal
        for what, category, code in [
                ("an invented category", "made-up", "precondition"),
                ("a code from another category", "policy", "precondition"),
                ("an invented code", "policy", "made-up"),
                ("an empty pair", "", "")]:
            with self.subTest(what=what):
                with self.assertRaises(AssertionError):
                    Refusal(category, code, "message")

    def test_a_caller_cannot_add_a_whole_category_either(self):
        # The reviewer's regression opens a CODE. This opens a CATEGORY, which
        # is the other half of the same pair -- and it was a mutation with no
        # witness, because a check that reads the public value for categories
        # and the private one for codes passes every case that only opens a
        # code.
        from baton_v12.contracts import ContractRefusal as Refusal
        ERROR_CODES["caller-invented"] = ("precondition",)
        try:
            with self.assertRaises(AssertionError):
                Refusal("caller-invented", "precondition", "message")
        finally:
            del ERROR_CODES["caller-invented"]

    def test_the_readable_vocabulary_agrees_with_what_is_enforced(self):
        # The residual risk of the two-value shape the review's regression
        # requires: the readable `ERROR_CODES` and the private value the check
        # actually consults can drift, and a caller reading the public one would
        # believe something the boundary does not enforce. Same discipline as
        # the pairing-versus-schema agreement: two sources, compared.
        from baton_v12.contracts import errors
        self.assertEqual(sorted(ERROR_CODES), sorted(errors._PAIRING))
        for category, codes in ERROR_CODES.items():
            with self.subTest(category=category):
                self.assertEqual(sorted(codes),
                                 sorted(errors._PAIRING[category]))

    def test_every_frozen_pair_is_accepted(self):
        # A guard that refused everything would satisfy the case above and no
        # contract at all.
        from baton_v12.contracts import ContractRefusal as Refusal
        for category, codes in ERROR_CODES.items():
            for code in codes:
                with self.subTest(pair=f"{category}/{code}"):
                    refusal = Refusal(category, code, "message")
                    self.assertEqual((refusal.category, refusal.code),
                                     (category, code))
                    self.assertFalse(refusal.durable)

    def test_a_caller_cannot_open_the_frozen_pairing(self):
        from baton_v12.contracts import ContractRefusal as Refusal
        original = ERROR_CODES["policy"]
        try:
            ERROR_CODES["policy"] = original + ("caller-invented",)
            with self.assertRaises(AssertionError):
                Refusal("policy", "caller-invented", "message")
        finally:
            ERROR_CODES["policy"] = original

    def test_the_authoritative_pairing_is_actually_frozen(self):
        from baton_v12.contracts import ContractRefusal as Refusal
        from baton_v12.contracts import errors
        original = errors._PAIRING["policy"]
        mutation_refused = False
        try:
            try:
                errors._PAIRING["policy"] = original | {"caller-invented"}
            except TypeError:
                mutation_refused = True
            with self.assertRaises(AssertionError):
                Refusal("policy", "caller-invented", "message")
            self.assertTrue(mutation_refused)
        finally:
            try:
                errors._PAIRING["policy"] = original
            except TypeError:
                pass


class TheValidatorIsTheRuledOne(unittest.TestCase):
    """SUPERSEDED by PLAN item 4bh, and replaced rather than deleted.

    This class used to assert the seam was ABSENT and that the distribution
    pinned no validator. That was the honest state while the question was open;
    it stopped being true the moment Slawomir ruled, and a case that asserts a
    superseded state is worse than no case -- it argues for the old answer every
    time the suite runs.

    What is worth keeping from it is the shape: the seam is scoped, and the
    scoping is measured. The dependency claims moved to
    `tests/manager/test_dependencies.py`, where the manager's allowlist lives.
    """

    def test_the_validator_is_reachable_from_the_exported_surface(self):
        for name in ("validate_worker_control", "validate_agent_session",
                     "validate_against"):
            with self.subTest(name=name):
                self.assertIn(name, contracts.__all__)
                self.assertTrue(callable(getattr(contracts, name)))

    def test_the_schemas_are_proved_valid_at_import_rather_than_trusted(self):
        # A schema this package SHIPS that is not a valid Draft 2020-12 schema
        # is a defect in this package, and finding it at import is better than
        # finding it on the first document. Re-run here so the property is a
        # case rather than a side effect of importing.
        import jsonschema
        for name, document in [("worker-control", WORKER_CONTROL),
                               ("agent-session", frozen.AGENT_SESSION)]:
            with self.subTest(schema=name):
                jsonschema.Draft202012Validator.check_schema(document)


if __name__ == "__main__":
    unittest.main()
