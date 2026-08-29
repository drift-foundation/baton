"""W6592 cut A — the first public composition, and the capability it advertises.

The manager could certify a DIGEST and had never read the document that digest
named, so `client_capabilities` had nowhere to arrive and §2.2 had nothing to
enforce. These cases hold the composition to the frozen host's pinned
acceptance -- shape, then the document seal, then policy, IN THAT ORDER -- and
hold §2.2's rule to being EXACT rather than a subset check.

The fixture is the design model's own ACP profile, rebuilt here with this
package's `digest` so the seal is computed rather than transcribed.
"""

import ast
import os
import pathlib
import tempfile
import unittest

import baton_v12.worker_manager as worker_manager
import baton_v12.worker_manager.handshake as handshake
from baton_v12.contracts import (ContractRefusal, canonical_bytes,
                                 digest, own)
from baton_v12.worker_manager import (ACP_CLIENT_CAPABILITIES,
                                      ACP_CLIENT_CAPABILITY_MEMBERS,
                                      ControlStore, SESSION_CAPABILITIES,
                                      certified_agent_session_profile,
                                      certify_agent_session_profile,
                                      check_client_capabilities, negotiate_acp)

NOW = "2026-08-24T12:00:00.000Z"


def acp_profile(**overrides):
    body = {
        "session_family": "baton.agent-session",
        "version": {"major": 1, "minor": 0},
        "document": "profile",
        "profile_id": "profile-handshake-acp",
        "created_at": NOW,
        "wire_protocol": "acp",
        "pinned_wire_version": 1,
        "provider_binding": None,
        "adapter": {"name": "native-acp-relay", "version": "1.0-test",
                    "build_digest": digest("adapter")},
        "client_capabilities": {"fs": {}, "terminal": False},
        "session_capabilities": sorted(SESSION_CAPABILITIES),
        "postures": {
            "consent": {"policy": {"kind": "acp", "session_mode_id": "plan"},
                        "workspace": False, "declared_output": False},
            "execution": {"policy": {"kind": "acp",
                                     "session_mode_id": "acceptEdits"},
                          "workspace": True, "declared_output": True},
        },
        "mcp_servers": [],
        "limits": {"setup_deadline_ms": 120000, "turn_deadline_ms": 900000,
                   "cancel_drain_deadline_ms": 30000,
                   "max_event_bytes": 16000, "max_queue_events": 1024,
                   "max_queue_bytes": 4194304},
        "agent_policy_digest": digest("policy"),
    }
    body.update(overrides)
    return {**body, "document_digest": digest(body)}


class CompositionCase(unittest.TestCase):

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-composition-")
        self.addCleanup(root.cleanup)
        self.store = ControlStore.open(
            os.path.join(root.name, "control.sqlite3"),
            incarnation="manager-1", clock=lambda: NOW)
        self.addCleanup(self.store.close)


class TheAdvertisedCapabilityIsExact(CompositionCase):
    """§2.2 -- the relay may advertise NOTHING, and the comparison is exact."""

    def test_the_wire_document_is_acps_own_and_is_fresh_each_time(self):
        """W641 kept ONE representation and this is it.

        The previous contract carried a Baton-invented snake_case summary
        alongside the wire document, with `read_text_file` and
        `write_text_file` explicitly false -- field names ACP does not have.
        W641 ruled the summary was the defect rather than a second shape to
        name, so the profile persists the same structural document the relay
        sends.
        """
        self.assertEqual(ACP_CLIENT_CAPABILITIES,
                         {"fs": {}, "terminal": False})
        # The constant STATES the rule and never travels: a caller cannot edit
        # it, and what goes on the wire is a fresh document built from it.
        with self.assertRaises(TypeError):
            ACP_CLIENT_CAPABILITIES["terminal"] = "edited"
        with self.assertRaises(TypeError):
            ACP_CLIENT_CAPABILITIES["fs"]["readTextFile"] = True
        sent = check_client_capabilities({"fs": {}, "terminal": False})
        sent["terminal"] = "edited"
        self.assertEqual(ACP_CLIENT_CAPABILITIES,
                         {"fs": {}, "terminal": False},
                         "a caller's edit reached this module's own answer")

    def test_the_canonical_document_is_accepted(self):
        self.assertEqual(check_client_capabilities({"fs": {},
                                                    "terminal": False}),
                         {"fs": {}, "terminal": False})

    def test_absence_is_how_the_wire_withholds(self):
        """A member present AT ALL, even set false, is a member ACP's optional
        type did not have to carry.

        This is the one place that difference is still visible, and it is the
        difference W641's correction is about: Baton does not synthesize an
        explicit false to restate an omission.
        """
        for member in ("readTextFile", "writeTextFile"):
            for value in (False, True):
                with self.subTest(member=member, value=value):
                    with self.assertRaises(ContractRefusal) as caught:
                        check_client_capabilities(
                            {"fs": {member: value}, "terminal": False})
                    self.assertEqual(
                        (caught.exception.category, caught.exception.code),
                        ("policy", "denied"))
                    self.assertIn("withholds by absence",
                                  caught.exception.message)

    def test_a_member_acp_adds_next_version_does_not_pass(self):
        """EXACT, not "no dangerous member set".

        A subset check asks whether what is here is safe when the rule is that
        nothing may be here -- so every one of these would pass one on the day
        it appeared, including the STABLE `session` member that §2.2
        nonetheless withholds.
        """
        for member in ACP_CLIENT_CAPABILITY_MEMBERS:
            if member in ("fs", "terminal"):
                continue
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as caught:
                    check_client_capabilities({"fs": {}, "terminal": False,
                                               member: {}})
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("policy", "denied"))
                self.assertIn(member, caught.exception.message)

    def test_terminal_is_false_and_not_merely_falsey(self):
        for value in (0, "", None, [], "false"):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ContractRefusal) as caught:
                    check_client_capabilities({"fs": {}, "terminal": value})
                self.assertIn("§2.2 sends false", caught.exception.message)

    def test_the_comparison_is_structural_rather_than_serialized(self):
        """Member ORDER carries no meaning in a JSON document.

        Comparing serialized output would have made insertion order part of
        the rule: the same document written differently is the same document,
        while a different member or value is a different one, and that is the
        comparison this boundary is for.
        """
        reordered = {"terminal": False, "fs": {}}
        self.assertEqual(list(reordered), ["terminal", "fs"])
        self.assertEqual(check_client_capabilities(reordered),
                         {"fs": {}, "terminal": False})

    def test_a_wide_document_is_refused_with_a_bounded_reason(self):
        """W1593's black-box acceptance, at the caller-local closed pair.

        The bounded exact-record diagnostic was signed off as a primitive with
        its acceptance explicitly waiting for a REAL public consumer. This is
        that consumer: a 20,000-member envelope is refused as `policy.denied` --
        this boundary's taxonomy, not the primitive's -- and the explanation
        stays bounded rather than growing with the rejected value.
        """
        wide = {"fs": {}, "terminal": False,
                **{f"member-{index}": index for index in range(20_000)}}
        with self.assertRaises(ContractRefusal) as caught:
            check_client_capabilities(wide)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "denied"))
        self.assertLess(len(caught.exception.message), 500)

    def test_the_offered_document_runs_nothing(self):
        """A refusal never runs the value it is refusing."""
        ran = []

        class Hostile(dict):
            def __iter__(self):
                ran.append("iter")
                raise AssertionError("iter ran")

            def keys(self):
                ran.append("keys")
                raise AssertionError("keys ran")

        with self.assertRaises(ContractRefusal):
            check_client_capabilities(Hostile({"fs": {}, "terminal": False}))
        self.assertEqual(ran, [])


class OneProfileIsCertifiedInOneOrder(CompositionCase):
    """Shape, then the document seal, then policy. The order is the content."""

    def test_a_valid_profile_is_certified_by_its_own_seal(self):
        profile = acp_profile()
        answer = certify_agent_session_profile(self.store, profile)
        self.assertEqual(answer["profile_id"], "profile-handshake-acp")
        self.assertEqual(answer["digest"], profile["document_digest"])

    def test_the_shape_is_proved_before_any_member_is_read(self):
        """Every later rule reads members, and reading one the schema has not
        established is how the worker-control entry's round-2 bypass
        happened."""
        for what, profile in [
                ("no document at all", {"profile_id": "p"}),
                ("a member the schema does not name",
                 {**acp_profile(), "unexpected": 1}),
                ("the wrong document kind",
                 acp_profile(document="not-a-profile")),
                ("a narrower capability list",
                 acp_profile(session_capabilities=["session.fresh"]))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    certify_agent_session_profile(self.store, profile)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))

    def test_a_document_that_is_not_its_own_seal_is_refused(self):
        """A policy decision about a document whose bytes do not match its own
        digest is a decision about something nobody agreed to."""
        profile = acp_profile()
        profile["document_digest"] = digest("somebody else's document")
        with self.assertRaises(ContractRefusal) as caught:
            certify_agent_session_profile(self.store, profile)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "digest"))

    def test_two_postures_with_one_policy_are_refused_at_certification(self):
        """The schema cannot compare two of its own members.

        A consent posture whose policy equals the execution one is a consent
        session with execution's permissions -- the separation the two postures
        exist for, removed by a document that otherwise validates. It is
        refused HERE rather than at run time.
        """
        same = {"kind": "acp", "session_mode_id": "plan"}
        profile = acp_profile(postures={
            "consent": {"policy": same, "workspace": False,
                        "declared_output": False},
            "execution": {"policy": dict(same), "workspace": True,
                          "declared_output": True}})
        with self.assertRaises(ContractRefusal) as caught:
            certify_agent_session_profile(self.store, profile)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "profile-uncertified"))

    def test_the_schema_alone_states_2_2_for_a_profile_carried_document(self):
        """MEASURED, and it is why there is no capability rule on this path.

        For a profile-carried document the frozen schema states §2.2 exactly:
        `clientCapabilities` requires `fs` and `terminal`, admits no other
        member, makes `fs` an empty closed object and pins `terminal` to the
        constant false. Every document `check_client_capabilities` refuses is
        refused HERE, as SHAPE, before any policy runs -- so repeating the rule
        after the schema has spoken would be the second live source of truth
        this schema's own prose warns about.

        The rule is enforced where it is NOT implied: at emission.
        """
        for capabilities in ({"fs": {"readTextFile": True}, "terminal": False},
                             {"fs": {}, "terminal": True},
                             {"fs": {}, "terminal": False, "session": {}},
                             {"fs": {}, "terminal": 0},
                             {"terminal": False}):
            with self.subTest(capabilities=capabilities):
                self.assertRaises(
                    ContractRefusal, check_client_capabilities, capabilities)
                profile = acp_profile(client_capabilities=capabilities)
                with self.assertRaises(ContractRefusal) as caught:
                    certify_agent_session_profile(self.store, profile)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("integrity", "schema"))

    def test_certification_is_journalled_and_replays_byte_stably(self):
        profile = acp_profile()
        first = certify_agent_session_profile(self.store, profile)
        again = certify_agent_session_profile(self.store, profile)
        self.assertEqual(first, again)

    def test_recertifying_prior_bytes_makes_them_current_again(self):
        """A historical journal result is not a current certification.

        Replacing one profile ID with new bytes makes the old digest absent.
        Asking to certify those old exact bytes again must restore them rather
        than replaying an answer for an effect a later certification replaced.
        """
        first = acp_profile()
        certify_agent_session_profile(self.store, first)
        replacement = acp_profile(agent_policy_digest=digest("replacement"))
        certify_agent_session_profile(self.store, replacement)
        self.assertIsNone(certified_agent_session_profile(
            self.store, first["document_digest"]))

        answer = certify_agent_session_profile(self.store, first)

        self.assertEqual(answer["digest"], first["document_digest"])
        self.assertEqual(certified_agent_session_profile(
            self.store, first["document_digest"]), first)


class AProfileIsReadBackOnlyWhenAllThreeWitnessesAgree(CompositionCase):
    """What it DECLARES, what its bytes RECOMPUTE to, and the KEY it is under.

    The frozen host's review [P1] found the declared member destructured away
    and never compared, so a retained profile whose every other byte matched
    its key could carry somebody else's well-formed seal and still open a
    session. Two of three agreeing is not agreement.
    """

    def test_a_certified_profile_comes_back(self):
        profile = acp_profile()
        certify_agent_session_profile(self.store, profile)
        self.assertEqual(
            certified_agent_session_profile(self.store,
                                            profile["document_digest"]),
            profile)

    def test_an_uncertified_digest_answers_absence_rather_than_a_fault(self):
        self.assertIsNone(certified_agent_session_profile(
            self.store, digest("never certified")))

    def test_a_row_edited_after_certification_is_refused(self):
        """A guard on the way IN cannot see an edit made afterwards."""
        profile = acp_profile()
        certify_agent_session_profile(self.store, profile)
        self.store._connection.execute(
            "UPDATE profiles SET body = ? WHERE kind = 'agent-session'",
            ('{"document": "profile"}',))
        with self.assertRaises(ContractRefusal) as caught:
            certified_agent_session_profile(self.store,
                                            profile["document_digest"])
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_a_well_sealed_profile_filed_under_another_key_is_refused(self):
        """TWO OF THREE IS NOT AGREEMENT.

        This row declares its own digest, recomputes to it, and is filed under
        somebody else's -- which is exactly the shape the frozen host's defect
        let through.
        """
        profile = acp_profile()
        certify_agent_session_profile(self.store, profile)
        stranger = digest("another profile entirely")
        self.store._connection.execute(
            "UPDATE profiles SET digest = ? WHERE kind = 'agent-session'",
            (stranger,))
        with self.assertRaises(ContractRefusal) as caught:
            certified_agent_session_profile(self.store, stranger)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "digest"))

    def test_undecodable_persisted_text_is_refused_rather_than_raised(self):
        profile = acp_profile()
        certify_agent_session_profile(self.store, profile)
        self.store._connection.execute(
            "UPDATE profiles SET body = ? WHERE kind = 'agent-session'",
            ("{not json",))
        with self.assertRaises(ContractRefusal):
            certified_agent_session_profile(self.store,
                                            profile["document_digest"])


class NegotiationIsAnAnnouncementRatherThanABargain(CompositionCase):

    def setUp(self):
        super().setUp()
        self.profile = acp_profile()
        certify_agent_session_profile(self.store, self.profile)
        self.digest = self.profile["document_digest"]

    def negotiate(self, **overrides):
        call = {"agent_protocol_version": 1,
                "agent_session_capabilities": list(SESSION_CAPABILITIES)}
        call.update(overrides)
        return negotiate_acp(self.store, self.digest, **call)

    def test_an_exact_match_answers_with_the_wire_document(self):
        answer = self.negotiate()
        self.assertEqual(answer["wire_version"], 1)
        self.assertEqual(answer["client_capabilities"],
                         {"fs": {}, "terminal": False})
        self.assertEqual(answer["session_capabilities"],
                         sorted(SESSION_CAPABILITIES))

    def test_the_wire_document_is_derived_from_the_profile_and_checked(self):
        """§2.2's REAL boundary: what is SENT, not what may be stored.

        W641's correction was about exactly this difference -- the host had one
        constant standing for two documents and emitted the durable summary
        onto the transport, sending field names ACP does not have. Answering
        from a module constant would restore the seam: the profile could say
        one thing and the wire carry another with nothing comparing them.

        So the emitted document is the PROFILE's, passed through the rule. A
        profile whose stored capabilities are not what §2.2 permits cannot be
        negotiated under, however it came to be stored.
        """
        self.store._connection.execute(
            "UPDATE profiles SET body = ? WHERE kind = 'agent-session'",
            (canonical_bytes({**self.profile,
                              "client_capabilities": {"fs": {},
                                                      "terminal": True}})
             .decode("utf-8"),))
        with self.assertRaises(ContractRefusal):
            self.negotiate()

    def test_the_emitted_document_is_plain_built_in_data(self):
        """What goes on the wire is DATA, not this module's constant.

        A mutation found this: answering with a shallow copy of the read-only
        constant left `fs` as the mapping proxy itself, and every case still
        passed. A document carrying a proxy is not a document a consumer can
        canonicalize, own or store -- `own` refuses it as a value that is not
        JSON data -- so the wire answer is built plainly all the way down.
        """
        answer = self.negotiate()
        self.assertIs(type(answer["client_capabilities"]), dict)
        self.assertIs(type(answer["client_capabilities"]["fs"]), dict)
        self.assertIs(type(answer["session_capabilities"]), list)
        # The proof that matters: it survives the boundary every durable value
        # crosses.
        self.assertEqual(own(answer), answer)

    def test_the_public_door_cannot_be_handed_profile_bytes(self):
        """W32576 [P0], and it was mine to cause.

        A correction gave `negotiate_acp` an optional `profile=` operand so
        one snapshot could serve a verdict and the evidence signed beside it.
        `negotiate_acp` is on the public surface, so that let ANY caller pair
        an uncertified digest with arbitrary bytes and receive a verdict from
        them — a behaviour-bearing mapping included, since the rule subscripts
        what it is given. A single-snapshot requirement is not a licence to
        widen a trust boundary.

        Asserted black-box rather than by reading the signature: a caller who
        tries it gets a TypeError, and an uncertified digest is refused
        whatever else is passed.
        """
        forged = acp_profile(pinned_wire_version=99)
        with self.assertRaises(TypeError):
            negotiate_acp(self.store, forged["document_digest"],
                          agent_protocol_version=99,
                          agent_session_capabilities=sorted(
                              SESSION_CAPABILITIES),
                          profile=forged)
        # AND THE DIGEST ALONE BUYS NOTHING: it was never certified here.
        with self.assertRaises(ContractRefusal) as caught:
            negotiate_acp(self.store, forged["document_digest"],
                          agent_protocol_version=99,
                          agent_session_capabilities=sorted(
                              SESSION_CAPABILITIES))
        self.assertEqual(caught.exception.code, "profile-uncertified")

    def test_the_emitted_capabilities_come_from_the_profile_structurally(self):
        """THE MUTANT THAT COULD NOT BE KILLED BEHAVIOURALLY, and why.

        Replacing the emitted document with this module's own constant leaves
        every case green -- measured -- and that is not a gap in the cases. The
        frozen schema pins `client_capabilities` to exactly `{"fs": {},
        "terminal": false}`, so a stored profile that reaches emission at all
        CANNOT differ from the constant. The two are behaviourally
        indistinguishable today.

        They are not the same code. W641's defect was one constant standing for
        two documents, and the manager emitting its own idea of the answer
        instead of the profile's is that shape restored -- it would come apart
        the day the contract admits more than one capability document, which is
        the day nobody would be looking. So the property is checked where it
        lives: the emitted value is the PROFILE's member, passed through the
        rule.
        """
        source = pathlib.Path(handshake.__file__).read_text(encoding="utf-8")
        # W32576 [P0]: the RULE moved to the private `_negotiated_against`
        # when the public door stopped accepting a caller-supplied profile,
        # so this looks where the emission now lives. The property asserted
        # below is unchanged -- exactly one emission, and it is
        # `check_client_capabilities` over the profile's own member.
        negotiate = next(
            node for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef)
            and node.name == "_negotiated_against")
        emitted = [
            keyword.value for piece in ast.walk(negotiate)
            if isinstance(piece, ast.Call)
            for keyword in piece.keywords
            if keyword.arg == "client_capabilities"]
        self.assertEqual(len(emitted), 1, "one emission, or this says nothing")
        call = emitted[0]
        self.assertIsInstance(call, ast.Call)
        self.assertEqual(call.func.id, "check_client_capabilities")
        self.assertEqual([piece.value.id for piece in ast.walk(call)
                          if isinstance(piece, ast.Subscript)
                          and isinstance(piece.value, ast.Name)],
                         ["profile"],
                         "the emitted capabilities are not the profile's")

    def test_there_is_no_downgrade(self):
        """A version the agent answers with is not a negotiation, it is an
        announcement, and the profile pinned the one this manager certified
        against."""
        for answered in (0, 2, None, "1"):
            with self.subTest(answered=repr(answered)):
                with self.assertRaises(ContractRefusal) as caught:
                    self.negotiate(agent_protocol_version=answered)
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("refused", "unsupported-version"))

    def test_a_boolean_is_not_the_integer_wire_version_it_compares_equal_to(self):
        """The frozen reference uses type-strict equality for the pin.

        Python's booleans compare equal to integers, but accepting ``True`` as
        ACP version 1 would widen the exact-match rule during the port.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.negotiate(agent_protocol_version=True)
        self.assertEqual(
            (caught.exception.category, caught.exception.code),
            ("refused", "unsupported-version"))

    def test_all_six_session_capabilities_are_mandatory(self):
        for absent in SESSION_CAPABILITIES:
            with self.subTest(absent=absent):
                with self.assertRaises(ContractRefusal) as caught:
                    self.negotiate(agent_session_capabilities=[
                        capability for capability in SESSION_CAPABILITIES
                        if capability != absent])
                self.assertEqual(
                    (caught.exception.category, caught.exception.code),
                    ("refused", "capability"))
                self.assertIn(absent, caught.exception.message)

    def test_the_capability_answer_is_one_list_containing_only_text(self):
        """Owning JSON is not yet owning the list this boundary promises.

        A record happens to iterate over its names, and non-text JSON members
        can be silently discarded. Neither is the agent's capability list.
        """
        every = list(SESSION_CAPABILITIES)
        invalid = ({capability: None for capability in every},
                   every + [1], every + [True], every + [None])
        for offered in invalid:
            with self.subTest(offered=offered):
                with self.assertRaises(ContractRefusal):
                    self.negotiate(agent_session_capabilities=offered)

    def test_a_handshake_is_conducted_under_a_certified_profile_or_not_at_all(
            self):
        with self.assertRaises(ContractRefusal) as caught:
            negotiate_acp(self.store, digest("uncertified"),
                          agent_protocol_version=1)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "profile-uncertified"))

    def test_the_capability_list_is_the_frozen_schemas_own(self):
        """A list written twice holds in one of the two places."""
        self.assertEqual(
            sorted(SESSION_CAPABILITIES),
            sorted(self.profile["session_capabilities"]))
        self.assertEqual(len(SESSION_CAPABILITIES), 6)


class TheCompositionIsOnThePublicSurface(CompositionCase):

    def test_every_operation_this_cut_adds_is_exported(self):
        """A composition reachable only by importing a private module is not a
        public composition, and W1593's acceptance is explicitly a BLACK-BOX
        one through the package's own door."""
        for name in ("ACP_CLIENT_CAPABILITIES", "ACP_CLIENT_CAPABILITY_MEMBERS",
                     "SESSION_CAPABILITIES", "certify_agent_session_profile",
                     "certified_agent_session_profile",
                     "check_client_capabilities", "negotiate_acp"):
            with self.subTest(name=name):
                self.assertIn(name, worker_manager.__all__)
                self.assertTrue(hasattr(worker_manager, name))

    def test_the_profiles_table_is_declared_where_the_store_declares_tables(
            self):
        self.assertIn("profiles", worker_manager.TABLES)
        self.assertEqual(
            sorted(row["name"] for row in self.store._connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%'")),
            sorted(worker_manager.TABLES))


if __name__ == "__main__":
    unittest.main()
