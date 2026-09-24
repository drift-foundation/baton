"""The packet describes the files it ships, and keeps describing them.

Owner reroute 247663 item 6 asks for the complete packet with exact commands,
the provider question and consolidated evidence. The failure mode this module
exists for is the one this Job has already hit twice: PROSE THAT WAS TRUE WHEN
IT WAS WRITTEN. Review 2026-09-23T13:25:28Z refused a page that said `main` had
run when the case called three functions individually, and the page before this
one still advertised a receipt and a check count from six claims earlier.

So nothing here re-runs the supervisor or counts tests. Each case takes one
claim the packet makes and compares it against the file it is about.
"""
import ast
import hashlib
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SIBLING = os.path.join(os.path.dirname(HERE),
                       "finding-v12-single-implementation-proof")
for one in (HERE, SIBLING):
    if one not in sys.path:                                  # pragma: no cover
        sys.path.insert(0, one)

import packet
import review_supervisor

PAGE = os.path.join(HERE, "OPERATOR-239533.md")
EVIDENCE = os.path.join(HERE, "EVIDENCE-239533.json")
# A bare SHA256 in the page. `(?<![0-9a-f])` so the 64 hex characters inside a
# `line-<64>` or `checkpoint-<64>` identifier still match on their own, and a
# longer accidental run of hex does not match at all.
DIGEST = re.compile(r"(?<![0-9a-f])[0-9a-f]{64}(?![0-9a-f])")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def sha(path):
    reading = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            reading.update(block)
    return reading.hexdigest()


def documented_flags(program, function="main"):
    """The `--flags` a program's entry point actually declares.

    Read from the SOURCE by `ast` rather than by running it: the point is to
    compare what the page tells an operator to type against what the program
    accepts, and running the program would start doing the thing instead.
    """
    tree = ast.parse(read(os.path.join(HERE, program)))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == function:
            return {one.value for call in ast.walk(node)
                    if isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "add_argument"
                    for one in call.args
                    if isinstance(one, ast.Constant)
                    and isinstance(one.value, str)
                    and one.value.startswith("--")}
    raise AssertionError(f"{program} has no {function}")            # pragma: no cover


class PacketCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.page = read(PAGE)
        # THE PAGE IS WRAPPED AT 79 COLUMNS AND ITS BANNER IS A BLOCKQUOTE, so
        # a sentence a case wants to assert is usually split across lines and
        # may carry a `>` in the middle of it. `flat` drops the quote markers
        # and collapses whitespace, for phrase assertions; `page` stays exact
        # for digests and code.
        cls.flat = " ".join(
            line.lstrip(">").strip() for line in cls.page.splitlines())
        cls.flat = " ".join(cls.flat.split())
        cls.evidence = json.loads(read(EVIDENCE))


class TheEvidenceDocumentDescribesTheFilesItShips(PacketCase):
    """Derived, and therefore checkable."""

    def test_every_shipped_digest_is_the_file_on_disk(self):
        for group in ("programs", "suites", "documents"):
            for name, digest in self.evidence[group].items():
                with self.subTest(group=group, file=name):
                    self.assertEqual(sha(os.path.join(HERE, name)), digest)

    def test_every_reused_digest_is_the_file_on_disk(self):
        """The accepted bytes this dossier imports rather than copies.

        A drift in W239528's `baseline.py` or in the product's
        `stage_execution.py` has to be visible in the packet, because both are
        preconditions the supervisor checks at startup.
        """
        for name, digest in self.evidence["reused"].items():
            with self.subTest(file=name):
                self.assertEqual(sha(packet.REUSED[name]), digest)

    def test_the_execution_state_is_the_one_that_happened(self):
        """It WAS run, once, by the owner -- and it still authorizes nothing.

        This case used to assert `NOT RUNNABLE`. Leaving it that way after
        claim 248377 would have been the exact failure this module exists to
        catch, so it now asserts the state that is true instead.
        """
        held = self.evidence["execution"]
        self.assertEqual(held["state"], "executed")
        self.assertIn("owner", held["by"])
        self.assertIn("THIS PACKET HAS BEEN RUN ONCE", self.flat)
        self.assertIn("AUTHORIZES NOTHING", self.flat.upper())

    def test_every_named_receipt_exists(self):
        self.assertTrue(self.evidence["receipts"])
        for one in self.evidence["receipts"]:
            with self.subTest(receipt=one["receipt"]):
                self.assertTrue(
                    os.path.exists(os.path.join(HERE, one["receipt"])))
        self.assertEqual(
            self.evidence["retained_receipt_seconds"],
            sum(one["measured_seconds"] for one in self.evidence["receipts"]))

    def test_the_reviewers_measurements_are_kept_separate_from_mine(self):
        """Their numbers are theirs; folding them into mine would inflate it."""
        mine = {one["receipt"] for one in self.evidence["receipts"]}
        theirs = {one["evidence"]
                  for one in self.evidence["reviewer_measurements"]}
        self.assertTrue(theirs)
        self.assertFalse(mine & theirs)


class TheOperatorPageCarriesNoStaleClaim(PacketCase):

    def test_every_digest_on_the_page_is_one_the_evidence_knows(self):
        """No hash survives on the page after the file behind it moves."""
        known = set(DIGEST.findall(json.dumps(self.evidence)))
        for one in DIGEST.findall(self.page):
            with self.subTest(digest=one):
                self.assertIn(one, known)

    def test_the_baseline_digest_it_quotes_is_the_one_bound_at_startup(self):
        self.assertIn(review_supervisor.BASELINE_SHA256, self.page)

    def test_it_quotes_no_receipt_or_check_count_of_its_own(self):
        """The page defers to the derived document, on purpose.

        The version before this one said "64 focused deterministic checks" and
        named `verification-6.json` while the current receipt was
        `verification-17.json`. A number that has to be hand-updated in prose
        is a number that will be wrong.
        """
        self.assertNotRegex(self.page, r"verification-\d+\.json")
        self.assertNotRegex(self.page, r"\d+ focused deterministic checks")

    def test_it_names_the_evidence_document_and_how_to_regenerate_it(self):
        self.assertIn("EVIDENCE-239533.json", self.page)
        self.assertIn("packet.py", self.page)


class TheOpenChoicesAreListedExactly(PacketCase):

    def setUp(self):
        self.open_now = packet.operator_inputs()

    def test_the_evidence_lists_exactly_what_the_selections_still_ask(self):
        self.assertEqual(
            [one["member"] for one in self.evidence["operator_selected_inputs"]],
            [one["member"] for one in self.open_now])

    def test_the_page_names_every_one_of_them(self):
        for one in self.open_now:
            with self.subTest(member=one["member"]):
                self.assertIn(one["member"], self.page)

    def test_the_count_the_page_states_is_the_count_that_is_open(self):
        stated = re.search(r"^(\w+), listed exactly and in full",
                           self.page, re.M)
        self.assertIsNotNone(stated, "the page stopped stating a count")
        words = {"Nine": 9, "Ten": 10, "Eleven": 11, "Twelve": 12,
                 "Thirteen": 13, "Fourteen": 14}
        self.assertIn(stated.group(1), words, stated.group(1))
        self.assertEqual(words[stated.group(1)], len(self.open_now))

    def test_the_three_that_carry_a_refusal_are_called_out(self):
        """A choice that fails the run deserves a warning before it is made."""
        for member in ("compose.provider_network",
                       "compose.credential_profile.api.reference",
                       "compose.evidence_digest"):
            with self.subTest(member=member):
                self.assertIn(member, self.page)


class TheCommandsAreTheOnesTheProgramsAccept(PacketCase):

    def test_the_composition_command_matches_review_bindings(self):
        flags = documented_flags("review_bindings.py")
        self.assertEqual(flags, {"--selections", "--run-root"})
        for one in flags:
            with self.subTest(flag=one):
                self.assertIn(one, self.page)
        # And the operand it deliberately does NOT take.
        self.assertNotIn("--base", flags)
        self.assertIn("no `--base` operand", self.page)

    def test_the_run_command_matches_review_supervisor(self):
        flags = documented_flags("review_supervisor.py")
        self.assertEqual(flags, {"--packet", "--incarnation"})
        for one in flags:
            with self.subTest(flag=one):
                self.assertIn(one, self.page)

    def test_the_regeneration_command_matches_packet(self):
        self.assertEqual(documented_flags("packet.py"), {"--claim"})
        self.assertIn("--claim", self.page)

    def test_the_snapshot_verify_command_matches_the_builder(self):
        self.assertIn("--verify", documented_flags("snapshot_247947.py"))
        self.assertIn("snapshot_247947.py\" --verify", self.page)


class TheTwoProofsAreDistinguished(PacketCase):
    """The thing owner 247663 item 6 asks for by name.

    A startup path that is `held` and a lifecycle that settles are two
    different proofs, and a packet that let them blur would be claiming a
    working review it does not have.
    """

    def test_the_startup_proof_is_recorded_as_held(self):
        held = self.evidence["startup_proof"]
        self.assertIn("main", held["entry_point"])
        self.assertIn("held", held["result"])
        self.assertEqual(set(held["seams_supplied"]),
                         {"image_inspect", "compose"})

    def test_the_lifecycle_proof_is_recorded_as_not_entering_main(self):
        settled = self.evidence["lifecycle_proof"]
        self.assertIn("supervise", settled["entry_point"])
        self.assertIn("NOT `main`", settled["entry_point"])
        self.assertIn("settled", settled["result"])
        self.assertIn("provider", settled["simulated"])

    def test_the_gap_between_them_is_stated_in_both_documents(self):
        """Scoped to the DETERMINISTIC suite, because the live run closed it."""
        missing = [one for one in self.evidence["not_established"]
                   if "main" in one["claim"]]
        self.assertTrue(missing, self.evidence["not_established"])
        self.assertIn("DETERMINISTIC", missing[0]["claim"])
        self.assertIn("THE LIVE RUN DOES BOTH", missing[0]["detail"])
        self.assertIn("no deterministic case here both enters `main` and "
                      "settles", self.flat.lower().replace("**", ""))

    def test_the_implementer_still_claims_no_provider_of_its_own(self):
        """The distinction that matters now: who ran it.

        The owner reached the provider; this implementer read the records it
        left. Collapsing those two would be claiming someone else's act.
        """
        first = self.evidence["not_established"][0]
        self.assertIn("this implementer has still reached no provider",
                      first["claim"])
        self.assertIn("baton.claude has still reached no container, image, "
                      "engine, provider, network or credential", self.flat)
        self.assertIn("the OWNER", self.evidence["live_run"]["executed_by"]
                      .replace("owner", "OWNER"))


class TheLiveRunIsRecordedAsWhatItWas(PacketCase):
    """One run, re-derived rather than believed.

    The outcome file is the run's own account of itself. What makes it
    evidence is that the same verdict comes back out of the retained store
    through public readers, which is what `attribution.py` did and what
    `ATTRIBUTION-248565.json` holds.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.attribution = json.loads(
            read(os.path.join(HERE, "ATTRIBUTION-248565.json")))
        cls.manifest = json.loads(
            read(os.path.join(HERE, "live-review-248377", "MANIFEST.json")))

    def test_the_hashes_agree_with_the_reviewers_retained_manifest(self):
        """Their manifest and my export must name the same bytes."""
        held = self.evidence["live_run"]
        self.assertEqual(held["executed_packet_sha256"],
                         self.manifest["PACKET-executed.json"]["sha256"])
        self.assertEqual(held["original_packet_sha256"],
                         self.manifest["PACKET-original.json"]["sha256"])
        self.assertEqual(held["outcome_sha256"],
                         self.manifest["outcome.json"]["sha256"])
        bound = self.attribution["bound_to"]
        self.assertEqual(bound["executed_packet_sha256"],
                         held["executed_packet_sha256"])
        self.assertEqual(bound["outcome_sha256"], held["outcome_sha256"])

    def test_the_retained_files_still_hash_to_what_the_manifest_says(self):
        for name, held in self.manifest.items():
            if held["source"].startswith("reviewer observation"):
                continue
            with self.subTest(file=name):
                self.assertEqual(
                    sha(os.path.join(HERE, "live-review-248377", name)),
                    held["sha256"])

    def test_the_verdict_was_derived_and_not_copied(self):
        derived = self.attribution["derived_verdict"]
        self.assertEqual(derived["verdict"], "accepted")
        self.assertTrue(self.attribution["agreement_with_outcome"]["agrees"])
        self.assertEqual(
            len(self.attribution["agreement_with_outcome"]
                ["compared_members"]), 8)
        self.assertEqual(self.evidence["live_run"]["reported"]["verdict"],
                         derived["verdict"])

    def test_independence_was_compared_and_not_assumed(self):
        """All three identities, with values on both sides.

        The first version of the export read the attachment's identities under
        the wrong names, got `None` for all three, and reported independence
        while having compared nothing. An empty `shared` list is only
        meaningful if both sides are populated.
        """
        held = self.attribution["independence"]
        self.assertTrue(held["independent"])
        self.assertEqual(held["shared"], [])
        self.assertEqual(sorted(held["compared"]),
                         ["participant", "principal", "worker_id"])
        for side in ("producer", "reviewer"):
            for name, value in held[side].items():
                with self.subTest(side=side, identity=name):
                    self.assertTrue(value, f"{side}.{name} is empty")

    def test_the_packet_difference_is_named_exactly(self):
        self.assertIn("bounds._note",
                      self.evidence["live_run"]["packet_difference"])
        self.assertIn("bounds._note", self.flat)

    def test_the_reader_refusal_keeps_its_cause_unknown(self):
        """A hypothesis that reads as a diagnosis is worse than no answer."""
        held = self.evidence["live_run"]["reader_refusal"]
        self.assertIn("UNKNOWN", held["cause"])
        self.assertIn("HYPOTHESIS", held["cause"].upper())
        self.assertIn("No product defect is claimed", held["cause"])
        unknown = [one for one in self.evidence["not_established"]
                   if "reader refusal" in one["claim"]]
        self.assertTrue(unknown, "the unknown cause stopped being named")

    def test_one_run_is_not_claimed_as_a_rate(self):
        rate = [one for one in self.evidence["not_established"]
                if "ONE run" in one["claim"]]
        self.assertTrue(rate, self.evidence["not_established"])
        self.assertIn("changes-requested", rate[0]["detail"])


class TheLimitationsComeBeforeTheClaims(PacketCase):

    def test_the_page_sends_a_reader_to_not_established_first(self):
        self.assertIn("Read `not_established` in", self.page)

    def test_the_unknown_spending_is_named_as_unknown(self):
        unknown = [one for one in self.evidence["not_established"]
                   if "spending" in one["claim"]]
        self.assertTrue(unknown, "the unmeasured spending stopped being named")
        self.assertIn("not estimated", unknown[0]["detail"])

    def test_every_established_claim_names_where_it_is_proved(self):
        for one in self.evidence["established"]:
            with self.subTest(claim=one["claim"]):
                for module in one["where"].split(", "):
                    self.assertTrue(
                        os.path.exists(os.path.join(HERE, module.strip())),
                        f"{one['claim']} points at {module}")

    def test_the_provider_question_asks_rather_than_asserts(self):
        asking = self.evidence["provider_question"]
        self.assertTrue(asking["question"].rstrip().endswith("?"))
        self.assertEqual(
            len(asking["negative_answers_that_are_evidence_rather_than_bugs"]),
            3)
        self.assertIn("changes-requested", asking["not_a_negative_answer"])
        self.assertIn(" ".join(asking["question"][:60].split()), self.flat)


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    suite = unittest.TestSuite()
    for name, value in sorted(globals().items()):
        if isinstance(value, type) and issubclass(value, unittest.TestCase) \
                and value.__module__ == __name__ \
                and name not in ("PacketCase",):
            suite.addTests(loader.loadTestsFromTestCase(value))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
