"""W321688 — the canonical dossier binding, and what it refuses.

The pilot assessment's finding was that this authority has identities and
history and NO canonical dossier binding at all: an operator standing a new v12
Work up had no supported way to say where its record lives, and labels are not
that binding because the label model is a mutable set.

These cases drive the whole accepted contract: one record per Work and one Work
per record, exact replay, refusal of a changed retry, of a rebinding, of a
collision from both sides, of an escape, of a wrong authority and of evidence
rewritten underneath a citation -- and the property the flat-set direction exists
for, that relationship changes move nothing.

Every store is this fixture's own temporary file. No deployment, no engine, no
provider, no network.
"""

import os
import sqlite3
import tempfile
import unittest

from baton_v12.authority import Authority, Refusal
from baton_v12.authority.dossier import (EVIDENCE_LIMIT, LOCATOR_LIMIT,
                                         SUFFIX_LENGTH)
from baton_v12.authority.schema import META_SCHEMA_VERSION, SCHEMA_VERSION

UUID = "0123456789abcdef0123456789abcdef"
OTHER_UUID = "fedcba9876543210fedcba9876543210"
LOCATOR = "operator-quickstart-7f3a91c2"
OTHER_LOCATOR = "operator-quickstart-0b1c2d3e"
DIGEST = "sha256:" + "a" * 64
OTHER_DIGEST = "sha256:" + "b" * 64
REFERENCE = "work/records/2026/10/finding-v12-pilot-dossier-binding/FINDING.md"


class DossierCase(unittest.TestCase):

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-dossier-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID)
        self.addCleanup(self.authority.dispose)
        self.work = UUID[:8] + "-W1"
        self.authority.create_work(self.work, "impl", operation_id="op-create")

    def second_work(self):
        held = UUID[:8] + "-W2"
        self.authority.create_work(held, "impl", operation_id="op-create-2")
        return held

    def bound(self, locator=LOCATOR, work=None, operation_id="op-bind"):
        return self.authority.bind_dossier(work or self.work, locator,
                                           operation_id=operation_id)


class ItBindsOneRecordToOneWork(DossierCase):

    def test_an_exact_authority_and_work_resolve_to_one_dossier(self):
        """The read the acceptance asks for. The authority is the store's own
        identity, so the pair is complete without an operand naming it."""
        self.bound()
        held = self.authority.dossier_of(self.work)
        self.assertEqual(held["work_id"], self.work)
        self.assertEqual(held["locator"], LOCATOR)
        self.assertEqual(held["operation_id"], "op-bind")
        self.assertEqual(self.authority.authority_uuid, UUID)

    def test_the_locator_resolves_BACK_to_its_work(self):
        """A human holding a directory name needs the authority, and a
        materializer must be able to ask before writing into a name."""
        self.bound()
        self.assertEqual(self.authority.dossier_work(LOCATOR)["work_id"],
                         self.work)

    def test_an_unbound_work_reads_as_NONE_rather_than_failing(self):
        """"This Work has no canonical record yet" is an answer."""
        self.assertIsNone(self.authority.dossier_of(self.work))
        self.assertIsNone(self.authority.dossier_work(LOCATOR))

    def test_the_binding_names_the_act_that_made_it(self):
        """Attribution, on `work_creation`'s own rule: from the record a reader
        recovers the operation that bound it."""
        self.assertEqual(self.bound()["operation_id"], "op-bind")


class ItReplaysAndRefusesExactly(DossierCase):

    def test_an_EXACT_RETRY_replays_the_first_answer(self):
        first = self.bound()
        again = self.bound()
        self.assertEqual(again, first)
        # AND WROTE NOTHING SECOND: one row, one bound instant.
        self.assertEqual(self.authority.dossier_of(self.work)["bound_at"],
                         first["bound_at"])

    def test_a_CHANGED_RETRY_is_refused_as_reused_operands(self):
        """The journal decides this on the full effective operands, so one
        operation identity cannot mean two different bindings."""
        self.bound()
        with self.assertRaises(Refusal) as caught:
            self.bound(locator=OTHER_LOCATOR)
        self.assertIn("different operands", str(caught.exception))
        self.assertEqual(self.authority.dossier_of(self.work)["locator"],
                         LOCATOR)

    def test_REBINDING_under_a_new_operation_is_refused(self):
        """One canonical address for the record's whole life: rebinding would
        break every review that cited the old one."""
        self.bound()
        with self.assertRaises(Refusal) as caught:
            self.bound(locator=OTHER_LOCATOR, operation_id="op-bind-2")
        said = str(caught.exception)
        self.assertIn("keeps one address", said)
        self.assertIn("Nothing was changed", said)
        self.assertEqual(self.authority.dossier_of(self.work)["locator"],
                         LOCATOR)

    def test_rebinding_to_the_SAME_locator_is_convergent(self):
        """A different operation id asking for the binding that already exists
        is agreement, not a collision with itself."""
        first = self.bound()
        again = self.bound(operation_id="op-bind-converge")
        self.assertEqual(again["locator"], first["locator"])
        self.assertEqual(again["operation_id"], "op-bind")

    def test_a_COLLISION_is_refused_and_names_the_holder(self):
        """In a flat set no parent disambiguates two records with one name."""
        self.bound()
        other = self.second_work()
        with self.assertRaises(Refusal) as caught:
            self.bound(work=other, operation_id="op-bind-3")
        said = str(caught.exception)
        self.assertIn(self.work, said)
        self.assertIn("Nothing was changed", said)
        self.assertIsNone(self.authority.dossier_of(other))

    def test_a_work_this_authority_does_not_have_is_refused(self):
        with self.assertRaises(Refusal) as caught:
            self.bound(work=UUID[:8] + "-W99")
        self.assertIn("no such Work", str(caught.exception))

    def test_ANOTHER_AUTHORITYS_work_id_is_not_in_this_store(self):
        """The wrong-authority refusal is the store's own doing: this Core holds
        one opened store whose UUID was established at open, so a Work id minted
        under another authority simply is not here."""
        with self.assertRaises(Refusal) as caught:
            self.bound(work=OTHER_UUID[:8] + "-W1")
        self.assertIn("no such Work", str(caught.exception))

    def test_a_store_opened_under_the_WRONG_EXPECTED_UUID_refuses(self):
        self.authority.dispose()
        with self.assertRaises(Refusal):
            Authority.open(self.path, expected_authority_uuid=OTHER_UUID)


class TheLocatorGrammarRefusesPathsAndEscapes(DossierCase):

    def refused(self, locator):
        with self.assertRaises(Refusal) as caught:
            self.bound(locator=locator)
        # NO PARTIAL EFFECT: an operand fault never reaches the store.
        self.assertIsNone(self.authority.dossier_of(self.work))
        return str(caught.exception)

    def test_a_SEPARATOR_is_refused_as_not_one_flat_segment(self):
        for one in ("nested/record-7f3a91c2", "a\\b-7f3a91c2",
                    "a:b-7f3a91c2"):
            with self.subTest(locator=one):
                self.assertIn("ONE FLAT SEGMENT", self.refused(one))

    def test_a_RELATIVE_ESCAPE_is_refused(self):
        for one in ("..", ".", "../etc-7f3a91c2", ".hidden-7f3a91c2"):
            with self.subTest(locator=one):
                self.refused(one)

    def test_a_LEADING_HYPHEN_is_refused_as_an_option_escape(self):
        self.refused("-rf-7f3a91c2")

    def test_a_MISSING_COLLISION_SUFFIX_is_refused(self):
        """The suffix is what makes two deployments choosing one deliverable
        name not collide, so a bare name is not a canonical locator."""
        said = self.refused("operator-quickstart")
        self.assertIn(str(SUFFIX_LENGTH), said)

    def test_an_OVERLONG_locator_is_refused(self):
        self.refused("a" * (LOCATOR_LIMIT + 1))

    def test_UPPERCASE_and_underscores_are_refused(self):
        for one in ("Operator-7f3a91c2", "operator_quickstart-7f3a91c2"):
            with self.subTest(locator=one):
                self.refused(one)

    def test_a_non_text_locator_is_refused(self):
        for one in (None, 7, b"x-7f3a91c2", ["x-7f3a91c2"]):
            with self.subTest(locator=one):
                with self.assertRaises(Refusal):
                    self.bound(locator=one)


class RelationshipChangesMoveNothing(DossierCase):
    """W39435's whole direction, driven rather than asserted.

    The v11 records nest under campaign and parent directories, so a reparent
    or a dependency change wanted to MOVE a durable record. These cases change
    everything about the Work that this authority can change and then read the
    locator back.
    """

    def test_LABELLING_the_work_does_not_rename_its_record(self):
        """Labels in particular. The assessment is explicit that a label is not
        a dossier binding, so the one mutable set a Work carries must not be
        able to behave like its address -- in either direction."""
        self.bound()
        self.authority.grant_capability("baton.impl", "manage-work-labels")
        session = self.authority.session("baton.impl")
        session.label_work({"work_id": self.work, "label": "pilot",
                            "operation_id": "op-label"})
        self.assertEqual(self.authority.labels_of(self.work), ["pilot"])
        self.assertEqual(self.authority.dossier_of(self.work)["locator"],
                         LOCATOR)
        session.unlabel_work({"work_id": self.work, "label": "pilot",
                              "operation_id": "op-unlabel"})
        self.assertEqual(self.authority.labels_of(self.work), [])
        self.assertEqual(self.authority.dossier_of(self.work)["locator"],
                         LOCATOR)

    def test_ROUTING_changes_do_not_rename_the_record(self):
        """Routing is the other thing the v11 layout encoded in a path."""
        self.bound()
        self.authority.add_route_handler("impl", "baton.impl")
        self.authority.add_route_handler("rview", "baton.rvpc")
        self.assertEqual(self.authority.dossier_of(self.work)["locator"],
                         LOCATOR)
        # And the locator is not derivable from the route: nothing in it names
        # one, which is what keeps the route from becoming the address.
        self.assertNotIn("impl", LOCATOR)

    def test_a_second_work_in_the_same_authority_keeps_its_own_record(self):
        self.bound()
        other = self.second_work()
        self.bound(work=other, locator=OTHER_LOCATOR,
                   operation_id="op-bind-other")
        self.assertEqual(self.authority.dossier_of(self.work)["locator"],
                         LOCATOR)
        self.assertEqual(self.authority.dossier_of(other)["locator"],
                         OTHER_LOCATOR)

    def test_the_record_survives_CLOSING_the_store_AND_REOPENING_it(self):
        """Readback is acceptance: identity, record and citation survive a
        reopen without anything replaying them."""
        self.bound()
        self.authority.record_dossier_evidence(
            self.work, REFERENCE, DIGEST, operation_id="op-ev")
        self.authority.dispose()
        reopened = Authority.open(self.path, expected_authority_uuid=UUID)
        self.addCleanup(reopened.dispose)
        self.assertEqual(reopened.dossier_of(self.work)["locator"], LOCATOR)
        self.assertEqual([one["reference"]
                          for one in reopened.dossier_evidence(self.work)],
                         [REFERENCE])
        self.assertEqual(reopened.work_creation(self.work)["operation_id"],
                         "op-create")


class ItCitesEvidenceAndRefusesRewriting(DossierCase):

    def setUp(self):
        super().setUp()
        self.bound()

    def test_a_citation_records_the_reference_its_digest_and_its_act(self):
        held = self.authority.record_dossier_evidence(
            self.work, REFERENCE, DIGEST, operation_id="op-ev")
        self.assertEqual(held["reference"], REFERENCE)
        self.assertEqual(held["digest"], DIGEST)
        self.assertEqual(held["act_id"], "op-ev")

    def test_an_exact_recitation_replays(self):
        first = self.authority.record_dossier_evidence(
            self.work, REFERENCE, DIGEST, operation_id="op-ev")
        again = self.authority.record_dossier_evidence(
            self.work, REFERENCE, DIGEST, operation_id="op-ev")
        self.assertEqual(again, first)
        self.assertEqual(len(self.authority.dossier_evidence(self.work)), 1)

    def test_the_SAME_reference_at_a_DIFFERENT_digest_is_refused(self):
        """A durable citation is not rewritten in place: accepting it would let
        a record's evidence change without the record saying so."""
        self.authority.record_dossier_evidence(
            self.work, REFERENCE, DIGEST, operation_id="op-ev")
        with self.assertRaises(Refusal) as caught:
            self.authority.record_dossier_evidence(
                self.work, REFERENCE, OTHER_DIGEST, operation_id="op-ev-2")
        said = str(caught.exception)
        self.assertIn("not rewritten in place", said)
        self.assertIn("Nothing was changed", said)
        self.assertEqual(
            self.authority.dossier_evidence(self.work)[0]["digest"], DIGEST)

    def test_evidence_for_an_UNBOUND_work_is_refused(self):
        other = self.second_work()
        with self.assertRaises(Refusal) as caught:
            self.authority.record_dossier_evidence(
                other, REFERENCE, DIGEST, operation_id="op-ev-3")
        self.assertIn("no canonical dossier", str(caught.exception))

    def test_an_ABSOLUTE_or_ESCAPING_reference_is_refused_before_storage(self):
        for one in ("/etc/passwd", "~/secret", "a/../../etc/passwd",
                    "a//b", "./a", ""):
            with self.subTest(reference=one):
                with self.assertRaises(Refusal):
                    self.authority.record_dossier_evidence(
                        self.work, one, DIGEST, operation_id="op-ev-x")
        self.assertEqual(self.authority.dossier_evidence(self.work), [])

    def test_a_MALFORMED_DIGEST_is_refused(self):
        for one in ("a" * 64, "sha256:" + "A" * 64, "sha256:short",
                    "md5:" + "a" * 32, None, 7):
            with self.subTest(digest=one):
                with self.assertRaises(Refusal):
                    self.authority.record_dossier_evidence(
                        self.work, REFERENCE, one, operation_id="op-ev-y")

    def test_citations_read_back_SORTED_rather_than_insertion_ordered(self):
        """Two authorities given the same citations in different orders read
        identically -- the label projection's own rule."""
        for index, name in enumerate(("c/z.md", "a/b.md", "b/m.md")):
            self.authority.record_dossier_evidence(
                self.work, name, DIGEST, operation_id=f"op-ev-{index}")
        self.assertEqual(
            [one["reference"]
             for one in self.authority.dossier_evidence(self.work)],
            ["a/b.md", "b/m.md", "c/z.md"])

    def test_the_citation_limit_is_enforced_and_stated(self):
        for index in range(EVIDENCE_LIMIT):
            self.authority.record_dossier_evidence(
                self.work, f"evidence/{index:04d}.md", DIGEST,
                operation_id=f"op-ev-{index}")
        with self.assertRaises(Refusal) as caught:
            self.authority.record_dossier_evidence(
                self.work, "evidence/overflow.md", DIGEST,
                operation_id="op-ev-overflow")
        self.assertIn(str(EVIDENCE_LIMIT), str(caught.exception))


class TheSchemaBoundaryIsClosedAndExplicit(DossierCase):
    """The acceptance asks for closed version compatibility and an explicit
    refusal, not a guessed migration."""

    def test_this_build_speaks_the_version_that_carries_the_binding(self):
        self.assertEqual(SCHEMA_VERSION, 6)

    def test_an_OLDER_store_is_refused_READ_ONLY_and_not_one_byte_changes(self):
        """A retained authority written before the binding existed has no
        column a locator could be read out of, so it is refused rather than
        upgraded -- and the file is left exactly as it was found."""
        self.bound()
        self.authority.dispose()
        connection = sqlite3.connect(self.path)
        connection.execute("UPDATE meta SET value = '5' WHERE key = ?",
                           (META_SCHEMA_VERSION,))
        connection.commit()
        connection.close()
        with open(self.path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(Refusal) as caught:
            Authority.open(self.path, expected_authority_uuid=UUID)
        said = str(caught.exception)
        self.assertIn("does not migrate", said)
        self.assertIn(str(SCHEMA_VERSION), said)
        with open(self.path, "rb") as handle:
            self.assertEqual(handle.read(), before,
                             "a refused open changed the store")

    def test_a_NEWER_store_is_refused_in_the_same_direction(self):
        self.authority.dispose()
        connection = sqlite3.connect(self.path)
        connection.execute("UPDATE meta SET value = ? WHERE key = ?",
                           (str(SCHEMA_VERSION + 1), META_SCHEMA_VERSION))
        connection.commit()
        connection.close()
        with self.assertRaises(Refusal) as caught:
            Authority.open(self.path, expected_authority_uuid=UUID)
        self.assertIn("in either direction", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
