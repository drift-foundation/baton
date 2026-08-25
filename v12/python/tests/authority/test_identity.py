"""W2845 cut 1 — exact built-in operand ownership, and the frozen identities.

The migration obligation these carry is the reviewed SNAPSHOT correction from
the frozen Node authority.  There the defect was a getter that answered one
participant to the binding check and another to the execution; here the same
obligation is met against Python's own hazards -- container subclasses,
`__getitem__` overrides, arbitrary mappings and objects that run code when
anything touches them.

The property is portable even though the mechanism is not: A BEHAVIOUR-BEARING
CONTAINER NEVER ENTERS THE AUTHORITY, so validating one view and executing
another is impossible rather than merely guarded against.
"""

import ast
import pathlib
import unittest

# The EXPORTED names are imported from the package face rather than from the
# module, because these cases are about the doors people actually walk through.
from baton_v12.authority import Refusal, V11, V12, is_v12_contract
import baton_v12.authority.errors as errors_module
import baton_v12.authority.identity as identity_module
from baton_v12.authority.errors import name_of
from baton_v12.authority.identity import (
    ABSENT, GATE_QUIESCENCE, MAX_DEPTH, MAX_MEMBERS, MAX_SAFE_INTEGER,
    assignment_key, assignment_ref, check_authority_uuid, check_generation,
    check_opaque_id, check_participant, check_text, check_timestamp,
    check_work_id, claim_signature, gate_token, own, normalize_assignment,
    parse_gate, same_assignment, signature_of, work_ref,
)

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
WHO = "baton.claude"


class Hostile:
    """A value that RUNS something if anything touches it.

    Every hook a refusal might plausibly reach is here, so a case cannot pass
    merely because the boundary happened to avoid the one hook somebody thought
    of.
    """

    def __init__(self, record):
        object.__setattr__(self, "_record", record)

    def __repr__(self):
        self._record.append("repr")
        raise AssertionError("__repr__ ran")

    def __str__(self):
        self._record.append("str")
        raise AssertionError("__str__ ran")

    def __eq__(self, other):
        self._record.append("eq")
        raise AssertionError("__eq__ ran")

    def __hash__(self):
        self._record.append("hash")
        raise AssertionError("__hash__ ran")

    def __iter__(self):
        self._record.append("iter")
        raise AssertionError("__iter__ ran")

    def __len__(self):
        self._record.append("len")
        raise AssertionError("__len__ ran")

    def __getitem__(self, key):
        self._record.append("getitem")
        raise AssertionError("__getitem__ ran")

    def keys(self):
        self._record.append("keys")
        raise AssertionError("keys ran")


class LyingDict(dict):
    """A dict SUBCLASS whose reads answer differently each time.

    This is Python's version of the shifting getter: the object passes any
    check that reads it once and then answers something else to whoever reads
    it next.  It is refused for being a subclass, before either answer matters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reads = 0

    def __getitem__(self, key):
        self.reads += 1
        return "baton.gemini" if self.reads > 1 else "baton.claude"


class OwningOperands(unittest.TestCase):

    def test_exact_json_data_is_taken_as_fresh_built_ins(self):
        source = {"a": 1, "b": [1, "two", True, None], "c": {"d": "e"}}
        taken = own(source)
        self.assertEqual(taken, source)
        self.assertIsNot(taken, source)
        self.assertIsNot(taken["b"], source["b"])
        self.assertIsNot(taken["c"], source["c"])
        # Owned in BOTH directions: the caller cannot reach in afterwards, and
        # the authority cannot leak back out.
        source["c"]["d"] = "changed"
        source["b"].append("appended")
        self.assertEqual(taken["c"]["d"], "e")
        self.assertEqual(len(taken["b"]), 4)
        taken["a"] = 99
        self.assertEqual(source["a"], 1)

    def test_a_behaviour_bearing_container_never_enters(self):
        class Mapping:
            def keys(self):
                return ["participant"]

            def __getitem__(self, key):
                return "baton.claude"

        for what, value in [
                ("a dict subclass", LyingDict({"participant": "baton.claude"})),
                ("a list subclass", type("L", (list,), {})([1, 2])),
                ("a mapping that is not a dict", Mapping()),
                ("a tuple", (1, 2)),
                ("a set", {1, 2}),
                ("an object", object()),
                ("a class", LyingDict),
                ("a function", lambda: None),
                ("bytes", b"data"),
                ("a float", 1.5),
                ("a complex", 1j)]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    own(value)

    def test_a_refusal_never_runs_the_value_it_refuses(self):
        ran = []
        for what, value in [
                ("the operand itself", Hostile(ran)),
                ("a member", {"member": Hostile(ran)}),
                ("an entry", [Hostile(ran)]),
                ("a nested member", {"a": {"b": [Hostile(ran)]}})]:
            with self.subTest(what=what):
                del ran[:]
                with self.assertRaises(Refusal):
                    own(value)
                self.assertEqual(ran, [], f"{what}: ran {ran}")

    def test_a_document_is_named_by_text(self):
        for what, value in [
                ("an integer key", {1: "a"}),
                ("a None key", {None: "a"}),
                ("a bool key", {True: "a"}),
                ("a tuple key", {(1, 2): "a"})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    own(value)

    def test_integers_are_bounded_by_what_a_consumer_can_read_back(self):
        self.assertEqual(own(MAX_SAFE_INTEGER), MAX_SAFE_INTEGER)
        self.assertEqual(own(-MAX_SAFE_INTEGER), -MAX_SAFE_INTEGER)
        for value in (MAX_SAFE_INTEGER + 1, -MAX_SAFE_INTEGER - 1, 10 ** 40):
            with self.subTest(value=value):
                with self.assertRaises(Refusal):
                    own(value)
        # `True` is an `int` in Python and is not one here.  Both survive `own`
        # as themselves; what must never happen is one becoming the other.
        self.assertIs(own(True), True)
        self.assertIs(own(False), False)
        self.assertNotEqual(type(own(1)), bool)

    def test_text_that_cannot_round_trip_is_not_a_durable_operand(self):
        for what, value in [
                ("a lone high surrogate", "\ud800"),
                ("a lone low surrogate", "\udfff"),
                ("a surrogate in a member", {"a": "x\ud800"}),
                ("a surrogate in a NAME", {"\ud800": "x"})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    own(value)
        # And ordinary non-ASCII text is data, not a hazard.
        self.assertEqual(own({"séance": "😀"}), {"séance": "😀"})

    def test_depth_and_width_are_bounded(self):
        deep = current = {}
        for _ in range(MAX_DEPTH + 2):
            current["next"] = {}
            current = current["next"]
        with self.assertRaises(Refusal):
            own(deep)
        with self.assertRaises(Refusal):
            own({str(index): 1 for index in range(MAX_MEMBERS + 1)})
        with self.assertRaises(Refusal):
            own(list(range(MAX_MEMBERS + 1)))
        # The bound is a limit, not a preference: exactly at it is accepted.
        self.assertEqual(len(own(list(range(MAX_MEMBERS)))), MAX_MEMBERS)


class FrozenIdentities(unittest.TestCase):

    def test_the_authority_uuid_grammar(self):
        self.assertEqual(check_authority_uuid(UUID), UUID)
        for value in (UUID.upper(), UUID[:-1], UUID + "0", "", None, 7,
                      "z" * 32, f"{UUID[:8]}-{UUID[9:]}"):
            with self.subTest(value=value):
                with self.assertRaises(Refusal):
                    check_authority_uuid(value)

    def test_a_work_id_is_the_full_canonical_identity(self):
        for value in ("0123abcd-W7", "ffffffff-W1", "00000000-W1000"):
            with self.subTest(value=value):
                self.assertEqual(check_work_id(value), value)
        # A LOCAL SELECTOR IS NOT AN IDENTITY.  §4 is explicit and this is the
        # case that keeps it true: `W7` is what an operator types and is never
        # what a durable document stores.
        for value in ("W7", "7", "0123abcd-W0", "0123abcd-W", "0123abc-W7",
                      "0123ABCD-W7", "0123abcd-w7", "0123abcd-W07", None, 7):
            with self.subTest(value=value):
                with self.assertRaises(Refusal):
                    check_work_id(value)

    def test_a_participant_is_team_member(self):
        for value in ("baton.claude", "a.b", "team-1.member_2"):
            self.assertEqual(check_participant(value), value)
        for value in ("baton", "baton.", ".claude", "Baton.claude",
                      "baton..claude", "1baton.claude", None, 7):
            with self.subTest(value=value):
                with self.assertRaises(Refusal):
                    check_participant(value)

    def test_a_generation_is_a_positive_safe_integer_or_absent(self):
        self.assertEqual(check_generation(1), 1)
        self.assertEqual(check_generation(MAX_SAFE_INTEGER), MAX_SAFE_INTEGER)
        self.assertIsNone(check_generation(None))
        for value in (0, -1, 1.0, True, False, "1", MAX_SAFE_INTEGER + 1):
            with self.subTest(value=value):
                with self.assertRaises(Refusal):
                    check_generation(value)
        with self.assertRaises(Refusal):
            check_generation(None, allow_null=False)

    def test_an_assignment_is_the_full_four_part_identity(self):
        reference = assignment_ref(UUID, WORK, WHO, 3)
        self.assertEqual(reference, {
            "work_ref": {"authority_uuid": UUID, "work_id": WORK},
            "participant": WHO, "generation": 3})
        self.assertIsInstance(assignment_key(reference), str)
        self.assertIsNone(assignment_key(None))
        # THREE QUARTERS OF AN IDENTITY IS NOT AN IDENTITY.  The same
        # participant may release generation 7 and claim generation 8, so an
        # identity that completed itself from current state would defeat the
        # one check §8 is built on.
        for what, value in [
                ("a participant alone", {"participant": WHO}),
                ("no work_ref", {"participant": WHO, "generation": 1}),
                ("no generation",
                 {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                  "participant": WHO}),
                ("a partial work_ref",
                 {"work_ref": {"work_id": WORK}, "participant": WHO,
                  "generation": 1}),
                ("an extra member",
                 {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                  "participant": WHO, "generation": 1, "extra": 1}),
                ("a local selector",
                 {"work_ref": {"authority_uuid": UUID, "work_id": "W7"},
                  "participant": WHO, "generation": 1})]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    assignment_key(value)

    def test_normalize_takes_the_snapshot_before_it_validates(self):
        lying = LyingDict({
            "work_ref": {"authority_uuid": UUID, "work_id": WORK},
            "participant": WHO, "generation": 1})
        with self.assertRaises(Refusal):
            normalize_assignment(lying)
        # `None` passes through, so an unclaimed close or gate arrival is not
        # forced to invent an assignment it does not have.
        self.assertIsNone(normalize_assignment(None))
        taken = normalize_assignment(
            {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
             "participant": WHO, "generation": 1})
        self.assertEqual(taken["participant"], WHO)

    def test_same_assignment_compares_all_four_parts(self):
        base = assignment_ref(UUID, WORK, WHO, 3)
        self.assertTrue(same_assignment(base, assignment_ref(UUID, WORK, WHO, 3)))
        self.assertTrue(same_assignment(None, None))
        self.assertFalse(same_assignment(base, None))
        for other in (assignment_ref(UUID, WORK, WHO, 4),
                      assignment_ref(UUID, WORK, "baton.gemini", 3),
                      assignment_ref(UUID, "0123abcd-W8", WHO, 3),
                      assignment_ref("f" * 32, WORK, WHO, 3)):
            with self.subTest(other=other):
                self.assertFalse(same_assignment(base, other))


class Signatures(unittest.TestCase):

    def test_member_order_is_not_part_of_the_signature(self):
        self.assertEqual(signature_of("k", {"a": 1, "b": 2}),
                         signature_of("k", {"b": 2, "a": 1}))
        self.assertEqual(signature_of("k", {"o": {"a": 1, "b": 2}}),
                         signature_of("k", {"o": {"b": 2, "a": 1}}))

    def test_the_missing_operand_is_not_the_null_one(self):
        # A transition that means "no gate" and one that forgot to pass a gate
        # must not share a signature, or one replays the other's result.
        self.assertNotEqual(signature_of("k", {"gate": None}),
                            signature_of("k", {"gate": ABSENT}))
        self.assertNotEqual(signature_of("k", {"gate": ABSENT}),
                            signature_of("k", {}))

    def test_the_prose_rides_the_signature(self):
        # Reusing one operation id with different durable text is a refusal,
        # not a silent replay of somebody else's result -- which is only true
        # if the text is IN the signature.
        self.assertNotEqual(signature_of("close", {"rationale": "done"}),
                            signature_of("close", {"rationale": "abandoned"}))
        self.assertNotEqual(signature_of("close", {}), signature_of("end", {}))

    def test_values_that_look_alike_are_not_alike(self):
        self.assertNotEqual(signature_of("k", {"v": 1}), signature_of("k", {"v": "1"}))
        self.assertNotEqual(signature_of("k", {"v": True}), signature_of("k", {"v": 1}))
        self.assertNotEqual(signature_of("k", {"v": None}), signature_of("k", {"v": "null"}))

    def test_the_claim_signature_is_the_authoritys_and_it_validates(self):
        first = claim_signature(WORK, WHO)
        self.assertEqual(first, claim_signature(WORK, WHO))
        self.assertNotEqual(first, claim_signature(WORK, "baton.gemini"))
        self.assertNotEqual(first, claim_signature("0123abcd-W8", WHO))
        # The manager persists this and must not recreate its encoding, so the
        # authority proves its operands rather than trusting the caller to have.
        for work, who in (("W7", WHO), (WORK, "baton"), (None, WHO), (WORK, None)):
            with self.subTest(work=work, who=who):
                with self.assertRaises(Refusal):
                    claim_signature(work, who)


class ExportedHelpersAreBoundaries(unittest.TestCase):
    """Review [P1]: an exported helper is a BOUNDARY.

    Three of them were not.  `is_v12_contract` invoked the caller's `__ne__`,
    `gate_token` invoked the caller's `__format__`, and `same_assignment`
    short-circuited on `None` before validating anything -- so an exported name
    ran caller code, or answered about an operand it had never proved.

    The `own` cases above prove the rule at the snapshot helper.  These prove it
    at the doors people actually walk through, because a rule enforced at the
    inner function and not at the exported one is a rule with a way around it.
    """

    def hostile(self, ran):
        class Hostile:
            def __ne__(self, other):
                ran.append("ne")
                raise RuntimeError("__ne__ ran")

            def __eq__(self, other):
                ran.append("eq")
                raise RuntimeError("__eq__ ran")

            def __hash__(self):
                ran.append("hash")
                raise RuntimeError("__hash__ ran")

            def __format__(self, spec):
                ran.append("format")
                raise RuntimeError("__format__ ran")

            def __str__(self):
                ran.append("str")
                raise RuntimeError("__str__ ran")

            def __repr__(self):
                ran.append("repr")
                raise RuntimeError("__repr__ ran")

        return Hostile()

    def test_no_exported_helper_runs_what_it_is_given(self):
        # EVERY ROW MUST REFUSE, and the first draft of this case did not say
        # so: it tolerated a helper that ACCEPTED the hostile operand, because
        # it only inspected the outcome when something was raised.  That let
        # `same_assignment(hostile, None)` pass by short-circuiting on the
        # `None` and answering about an operand it had never proved -- the exact
        # defect the case was written for.  A case that permits silent
        # acceptance is a case that permits the bug.
        ran = []
        hostile = self.hostile(ran)
        good = assignment_ref(UUID, WORK, WHO, 1)
        for what, call in [
                ("is_v12_contract", lambda: is_v12_contract(hostile)),
                ("gate_token kind", lambda: gate_token(hostile, "detail")),
                ("gate_token detail", lambda: gate_token("kind", hostile)),
                ("same_assignment left", lambda: same_assignment(hostile, good)),
                ("same_assignment right", lambda: same_assignment(good, hostile)),
                ("same_assignment against none",
                 lambda: same_assignment(hostile, None)),
                ("same_assignment against none, reversed",
                 lambda: same_assignment(None, hostile)),
                ("same_assignment member",
                 lambda: same_assignment(
                     {"work_ref": {"authority_uuid": UUID, "work_id": WORK},
                      "participant": WHO, "generation": hostile}, None)),
                ("work_ref", lambda: work_ref(hostile, WORK)),
                ("assignment_ref", lambda: assignment_ref(UUID, WORK, WHO, hostile)),
                ("claim_signature", lambda: claim_signature(hostile, WHO)),
                ("normalize_assignment", lambda: normalize_assignment(hostile)),
                ("assignment_key", lambda: assignment_key(hostile)),
                ("own", lambda: own(hostile))]:
            with self.subTest(what=what):
                del ran[:]
                with self.assertRaises(Refusal, msg=what):
                    call()
                self.assertEqual(ran, [], f"{what} ran {ran}")
        # `parse_gate` is the one exported helper whose contract is to ANSWER
        # rather than refuse: "this is not a gate token" is its whole job.  It
        # is asserted separately, on its own terms, rather than being folded
        # into the table above and quietly weakening it.
        del ran[:]
        self.assertIsNone(parse_gate(hostile))
        self.assertEqual(ran, [])

    def test_an_exported_helper_bounds_its_caller_supplied_label(self):
        huge = "label-" + "z" * 1_000_000
        for what, call in [
                ("own", lambda: own(object(), what=huge)),
                ("authority UUID", lambda: check_authority_uuid(None, what=huge)),
                ("Work id", lambda: check_work_id(None, what=huge)),
                ("participant", lambda: check_participant(None, what=huge)),
                ("generation", lambda: check_generation("bad", what=huge)),
                ("opaque id", lambda: check_opaque_id(None, huge)),
                ("text", lambda: check_text(None, huge)),
                ("timestamp", lambda: check_timestamp(None, what=huge)),
                ("assignment key", lambda: assignment_key(object(), what=huge)),
                ("normalize assignment",
                 lambda: normalize_assignment(object(), what=huge))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    call()
                message = str(caught.exception)
                self.assertLess(len(message), 500, what)
                self.assertNotIn(huge, message, what)

    def test_the_helpers_still_answer_for_the_values_they_are_for(self):
        # A boundary that refuses everything satisfies every case above and no
        # contract at all.
        self.assertTrue(is_v12_contract(V12))
        self.assertFalse(is_v12_contract(V11))
        self.assertEqual(gate_token(GATE_QUIESCENCE, "runtime-7"),
                         f"{GATE_QUIESCENCE}:runtime-7")
        base = assignment_ref(UUID, WORK, WHO, 3)
        self.assertTrue(same_assignment(base, assignment_ref(UUID, WORK, WHO, 3)))
        self.assertFalse(same_assignment(base, None))
        self.assertTrue(same_assignment(None, None))

    def test_a_gate_kind_may_not_smuggle_the_separator(self):
        # The token is parsed at its FIRST colon, so a kind carrying one parses
        # back as a different kind with the rest of itself in the detail.  A
        # token that does not round-trip is not an identity.
        with self.assertRaises(Refusal):
            gate_token("kind:extra", "detail")
        self.assertEqual(parse_gate(gate_token("kind", "a:b")),
                         {"kind": "kind", "detail": "a:b"})

    def test_an_integer_too_large_to_render_still_refuses_as_a_refusal(self):
        # Review [P1]: `str()` of an integer is not inert in Python 3.13 -- the
        # interpreter refuses one above 4,300 digits -- so the message built to
        # explain the refusal raised `ValueError` instead, and the rejected
        # value escaped through the DIAGNOSTIC after the check had already
        # decided against it.
        huge = 10 ** 5000
        for what, call in [
                ("a huge generation", lambda: check_generation(huge)),
                ("a huge negative generation", lambda: check_generation(-huge)),
                ("a huge generation in an identity",
                 lambda: assignment_ref(UUID, WORK, WHO, huge)),
                ("a huge integer operand", lambda: own(huge)),
                ("a huge integer inside a document",
                 lambda: own({"generation": huge}))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    call()
                # And the message is bounded rather than being 5,001 digits of
                # somebody else's number.
                self.assertLess(len(str(caught.exception)), 300, what)
        self.assertEqual(name_of(huge), f"an integer of {huge.bit_length()} bits")
        self.assertEqual(name_of(7), "7")


class Gates(unittest.TestCase):

    def test_a_gate_token_is_typed_and_parses_back(self):
        token = gate_token(GATE_QUIESCENCE, "runtime-7")
        self.assertEqual(parse_gate(token),
                         {"kind": GATE_QUIESCENCE, "detail": "runtime-7"})
        # The detail may itself contain the separator; only the FIRST one
        # divides the token, so a detail is never truncated by its own colon.
        self.assertEqual(parse_gate("kind:a:b"), {"kind": "kind", "detail": "a:b"})
        for value in (None, 7, "", ":detail", "nocolon"):
            with self.subTest(value=value):
                self.assertIsNone(parse_gate(value))


if __name__ == "__main__":
    unittest.main()


class TheLabelBoundIsMeasuredRatherThanChosen(unittest.TestCase):
    """A bound below what the authority itself writes breaks the authority.

    The first correction bound a caller-supplied label with the sixty-character
    VALUE rule, and that truncated this package's own longest label mid-word --
    taking with it the member name the refusal existed to report. Twelve cases
    caught it, which is the only reason this is a note rather than a defect.

    It is the settlement-signature lesson in another place, so the number is
    measured here rather than trusted: if a future label grows past the bound,
    this fails instead of a message quietly losing its ending.
    """

    def labels(self):
        package = pathlib.Path(identity_module.__file__).parent
        found = []
        for source in sorted(package.glob("*.py")):
            tree = ast.parse(source.read_text(encoding="utf-8"), str(source))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                labels = [keyword.value for keyword in node.keywords
                          if keyword.arg == "what"]
                name = (getattr(node.func, "id", "")
                        or getattr(node.func, "attr", ""))
                if name in ("check_text", "check_opaque_id", "_text",
                            "_optional_text") and len(node.args) >= 2:
                    labels.append(node.args[1])
                for label in labels:
                    if isinstance(label, ast.Constant) and type(label.value) is str:
                        text = label.value
                    elif isinstance(label, ast.JoinedStr):
                        # The literal parts only. An interpolated part is
                        # bounded by whatever renders it, which is the other
                        # rule's business.
                        text = "".join(piece.value for piece in label.values
                                       if isinstance(piece, ast.Constant))
                    else:
                        continue
                    found.append((len(text), f"{source.name}:{label.lineno}"))
        return sorted(found, reverse=True)

    def test_the_label_bound_exceeds_the_longest_label_we_write(self):
        found = self.labels()
        # The scanner has to be finding real labels, or the comparison below
        # passes for the wrong reason.
        self.assertGreater(len(found), 20, "the scanner found almost no labels")
        width, where = found[0]
        self.assertGreater(width, 50, "the scanner is missing the long ones")
        # The property is not "our longest literal fits". It is that our longest
        # literal PLUS one bounded value rendering fits, because that is what a
        # label with an interpolated member actually costs at runtime -- and the
        # publication label is exactly that shape.
        self.assertLess(width + errors_module._NAME_LIMIT,
                        errors_module._LABEL_LIMIT,
                        f"the longest label is {width} characters at {where}; "
                        f"with one rendered member it would be truncated")

    def test_a_label_at_the_bound_keeps_its_ending(self):
        # The property that actually matters: the member name a refusal exists
        # to report survives the bound.
        for member in ("result_digest", "candidate_digest", "input_digest",
                       "policy_digest"):
            with self.subTest(member=member):
                with self.assertRaises(Refusal) as caught:
                    check_text("", f"a proposal binds the exact assignment and "
                                   f"the result, candidate, input and policy "
                                   f"digests, and {member}")
                self.assertIn(member, str(caught.exception))

    def test_an_ordinary_label_is_returned_exactly_as_written(self):
        # Found by a mutation with no witness: rendering EVERY label through
        # `ascii` bounds and encodes just as well, and nothing in the suite
        # noticed -- so "preserve ordinary label prose" was an intention rather
        # than a property. A label is prose; quoting it would make every message
        # read like a citation, and that is the half of this rule that only a
        # case can hold.
        for label in ("work_id", "a durable instant",
                      "a settled operation's signature",
                      "the certified profile evidence"):
            with self.subTest(label=label):
                with self.assertRaises(Refusal) as caught:
                    check_text(None, label)
                self.assertTrue(str(caught.exception).startswith(label),
                                str(caught.exception))

    def test_a_caller_supplied_label_is_still_bounded(self):
        with self.assertRaises(Refusal) as caught:
            check_text(None, "z" * 1_000_000)
        self.assertLess(len(str(caught.exception)), 500)

    def test_a_caller_supplied_label_produces_encodable_diagnostics(self):
        # Exact `str` is inert but not necessarily text that can cross a wire.
        # `name_of` handles a lone surrogate through `ascii`; the parallel label
        # boundary must not put the raw surrogate back into the Refusal.
        with self.assertRaises(Refusal) as caught:
            check_work_id(None, what="\ud800")
        message = str(caught.exception)
        self.assertEqual(message.encode("utf-8").decode("utf-8"), message)

    def test_a_label_that_is_not_text_is_named_and_never_run(self):
        """A label is caller-supplied, so a HOSTILE label is a caller's choice.

        Found by a mutation with no witness: rendering a non-text label raw
        changed nothing in the suite, because every case supplied a string. But
        `f"{what}"` calls `__str__`, and a caller that wants to can make that
        raise -- which would replace the refusal the boundary had already decided
        on with an exception of the caller's choosing, at the boundary whose whole
        job is to describe a rejection safely.

        The same rule as the rejected VALUE, in the place nobody had checked it:
        a refusal must never run what it is refusing, and a label is part of what
        it is refusing.
        """
        ran = []

        class Hostile:
            def __str__(self):
                ran.append("str")
                raise RuntimeError("the caller chose this")

            __repr__ = __str__

            def __format__(self, specification):
                ran.append("format")
                raise RuntimeError("the caller chose this")

        for what, call in [
                ("own", lambda: own(object(), what=Hostile())),
                ("text", lambda: check_text(None, Hostile())),
                ("participant", lambda: check_participant(None, what=Hostile())),
                ("assignment", lambda: assignment_key(object(),
                                                      what=Hostile()))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal) as caught:
                    call()
                self.assertEqual(ran, [], "the label was RUN")
                # And it is still described, by its type, so the diagnostic is
                # useful rather than merely safe.
                self.assertIn("Hostile", str(caught.exception))
