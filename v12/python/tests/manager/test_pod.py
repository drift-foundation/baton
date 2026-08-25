"""W4 cut A — the approved POD ruling, in Python.

Slawomir ruled that a section 3.1 session reference is plain old data: an exact
record with own data members, no compatibility for accessors, proxies, arrays,
class instances, hidden members or extras. The Node host's version of that
ruling is about `Proxy` and getters; this is the same ruling against Python's
own hazards, which is what "ported by obligation, not transliterated" means.
"""

import ast
import pathlib
import unittest

import baton_v12.contracts.errors as errors

from baton_v12.contracts import (ContractRefusal, MAX_DEPTH, MAX_MEMBERS,
                                 MAX_SAFE_INTEGER, own, own_record)
from baton_v12.contracts.errors import counted_sample_of

REFERENCE = ("authority_uuid", "work_id", "participant", "provider_session_id")


class Hostile:
    """A value that RUNS something if anything touches it.

    Every hook a refusal might plausibly reach, so a case cannot pass merely
    because the boundary happened to avoid the one hook somebody thought of.
    """

    def __init__(self, record):
        object.__setattr__(self, "_record", record)

    def __repr__(self):
        self._record.append("repr")
        raise AssertionError("__repr__ ran")

    __str__ = __repr__

    def __format__(self, specification):
        self._record.append("format")
        raise AssertionError("__format__ ran")

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


class Shifting(dict):
    """A dict SUBCLASS whose reads answer differently each time.

    Python's version of the shifting getter that produced the original defect:
    the object passes any check that reads it once and then answers something
    else to whoever reads it next. It is refused for being a subclass, before
    either answer matters.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.reads = 0

    def __getitem__(self, key):
        self.reads += 1
        return "baton.gemini" if self.reads > 1 else "baton.claude"


class ABehaviourBearingContainerNeverEnters(unittest.TestCase):

    def test_exact_json_data_is_taken_as_fresh_built_ins(self):
        source = {"a": 1, "b": [1, "two", True, None], "c": {"d": "e"}}
        taken = own(source)
        self.assertEqual(taken, source)
        # Owned in BOTH directions: the caller cannot reach in afterwards, and
        # this package cannot leak a live reference back out.
        self.assertIsNot(taken, source)
        self.assertIsNot(taken["b"], source["b"])
        self.assertIsNot(taken["c"], source["c"])
        source["c"]["d"] = "changed"
        source["b"].append("appended")
        self.assertEqual(taken["c"]["d"], "e")
        self.assertEqual(len(taken["b"]), 4)

    def test_the_shifting_container_is_refused_before_either_answer(self):
        shifting = Shifting({"participant": "baton.claude"})
        with self.assertRaises(ContractRefusal):
            own(shifting)
        # Refused for its TYPE, so nothing read it: validating one view and
        # executing another is impossible rather than guarded against.
        self.assertEqual(shifting.reads, 0)

    def test_every_container_that_is_not_exactly_built_in_is_refused(self):
        class Mapping:
            def keys(self):
                return ["participant"]

            def __getitem__(self, key):
                return "baton.claude"

        for what, value in [
                ("a dict subclass", Shifting()),
                ("a list subclass", type("L", (list,), {})([1, 2])),
                ("a mapping that is not a dict", Mapping()),
                ("a tuple", (1, 2)),
                ("a set", {1, 2}),
                ("an object", object()),
                ("a class", Shifting),
                ("a function", lambda: None),
                ("bytes", b"data"),
                ("a float", 1.5),
                ("a complex", 1j)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    own(value)
                self.assertEqual(caught.exception.category, "integrity")

    def test_a_refusal_never_runs_the_value_it_refuses(self):
        ran = []
        for what, value in [("the operand itself", Hostile(ran)),
                            ("a member", {"member": Hostile(ran)}),
                            ("an entry", [Hostile(ran)]),
                            ("a nested member", {"a": {"b": [Hostile(ran)]}})]:
            with self.subTest(what=what):
                del ran[:]
                with self.assertRaises(ContractRefusal):
                    own(value)
                self.assertEqual(ran, [], f"{what}: ran {ran}")

    def test_naming_a_rejected_type_does_not_run_its_metaclass(self):
        ran = []

        class HostileMeta(type):
            def __getattribute__(cls, name):
                if name == "__name__":
                    ran.append(name)
                    raise AssertionError("metaclass __getattribute__ ran")
                return super().__getattribute__(name)

        class Value(metaclass=HostileMeta):
            pass

        with self.assertRaises(ContractRefusal):
            own(Value())
        self.assertEqual(ran, [])

    def test_a_metaclass_cannot_change_or_refuse_the_name_at_all(self):
        """SUPERSEDED and strengthened, rather than deleted.

        My previous version asserted these two shapes produced the "will not
        name itself" fallback, which was true when the name was read through
        `type.__getattribute__` -- that skips a metaclass `__getattribute__`
        override but still resolves a DESCRIPTOR the metaclass installs. The
        review found that, and the correction binds the built-in slot on `type`
        itself.

        So the property is stronger now and the case says the stronger thing:
        a metaclass descriptor is not consulted, so it neither runs nor changes
        the answer. The class is named by what `type` knows about it.
        """
        ran = []

        class RaisingName(type):
            @property
            def __name__(cls):
                ran.append("raising")
                raise RuntimeError("the caller chose this")

        class LyingName(type):
            @property
            def __name__(cls):
                ran.append("lying")
                return 7

        for what, meta in [("a name that raises", RaisingName),
                           ("a name that is not text", LyingName)]:
            with self.subTest(what=what):
                del ran[:]
                value = meta("Value", (), {})()
                with self.assertRaises(ContractRefusal) as caught:
                    own(value)
                message = str(caught.exception)
                self.assertEqual(ran, [], "the metaclass descriptor RAN")
                # Named by `type`'s own record of the class, not by anything
                # the metaclass offered.
                self.assertIn("Value", message)
                self.assertNotIn("caller-chosen", message)
                self.assertLess(len(message), 500)

    def test_naming_a_type_does_not_run_a_metaclass_descriptor(self):
        ran = []

        class DescribedName(type):
            @property
            def __name__(cls):
                ran.append("name descriptor")
                return "caller-chosen-name"

        value = DescribedName("Value", (), {})()
        with self.assertRaises(ContractRefusal):
            own(value)
        self.assertEqual(ran, [])

    def test_own_bounds_its_own_label_rather_than_inheriting_one(self):
        # A mutation with no witness: every label case went through
        # `own_record`, which bounds the label itself before calling `own`. So
        # `own`'s own bounding was untested, and a caller reaching `own`
        # directly -- which the exported surface invites -- was relying on a
        # guard nothing measured.
        ran = []
        with self.assertRaises(ContractRefusal) as caught:
            own(object(), what=Hostile(ran))
        self.assertEqual(ran, [], "the label was RUN")
        self.assertIn("Hostile", str(caught.exception))
        with self.assertRaises(ContractRefusal) as caught:
            own(object(), what="z" * 1_000_000)
        self.assertLess(len(str(caught.exception)), 500)

    def test_a_boolean_stays_a_boolean_and_an_integer_stays_one(self):
        self.assertIs(own(True), True)
        self.assertIs(own(False), False)
        self.assertNotEqual(type(own(1)), bool)

    def test_integers_are_bounded_by_what_a_consumer_can_read_back(self):
        self.assertEqual(own(MAX_SAFE_INTEGER), MAX_SAFE_INTEGER)
        self.assertEqual(own(-MAX_SAFE_INTEGER), -MAX_SAFE_INTEGER)
        for value in (MAX_SAFE_INTEGER + 1, -MAX_SAFE_INTEGER - 1, 10 ** 40):
            with self.subTest(value=value):
                with self.assertRaises(ContractRefusal):
                    own(value)

    def test_text_that_cannot_round_trip_is_not_a_durable_operand(self):
        for what, value in [("a lone high surrogate", "\ud800"),
                            ("a lone low surrogate", "\udfff"),
                            ("a surrogate in a member", {"a": "x\ud800"}),
                            ("a surrogate in a NAME", {"\ud800": "x"})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    own(value)
        self.assertEqual(own({"séance": "\U0001F600"}),
                         {"séance": "\U0001F600"})

    def test_depth_and_width_are_bounded(self):
        deep = current = {}
        for _ in range(MAX_DEPTH + 2):
            current["next"] = {}
            current = current["next"]
        with self.assertRaises(ContractRefusal):
            own(deep)
        with self.assertRaises(ContractRefusal):
            own({f"k{index}": index for index in range(MAX_MEMBERS + 1)})
        with self.assertRaises(ContractRefusal):
            own(list(range(MAX_MEMBERS + 1)))

    def test_a_document_is_named_by_text(self):
        for what, value in [("an integer name", {1: "a"}),
                            ("a none name", {None: "a"}),
                            ("a bool name", {True: "a"}),
                            ("a tuple name", {(1, 2): "a"})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    own(value)

    def test_a_caller_cannot_choose_the_ownership_traversal_depth(self):
        deep = current = []
        for _ in range(MAX_DEPTH + 2):
            nested = []
            current.append(nested)
            current = nested
        with self.assertRaises((ContractRefusal, TypeError)):
            own(deep, _depth=-MAX_DEPTH * 2)


class AnExactRecordCarriesExactlyItsMembers(unittest.TestCase):

    def reference(self, **overrides):
        base = {"authority_uuid": "0" * 32, "work_id": "0123abcd-W7",
                "participant": "baton.claude", "provider_session_id": "s-1"}
        base.update(overrides)
        return base

    def test_the_four_members_are_taken_and_owned(self):
        source = self.reference()
        taken = own_record(source, REFERENCE, what="a session reference")
        self.assertEqual(taken, source)
        self.assertIsNot(taken, source)

    def test_an_extra_member_is_refused_rather_than_dropped(self):
        with self.assertRaises(ContractRefusal) as caught:
            own_record(self.reference(extra=1), REFERENCE)
        self.assertIn("extra", str(caught.exception))

    def test_an_absent_member_is_named_rather_than_rewritten_to_null(self):
        # The approved ruling retained exact POD precisely so an absent
        # `provider_session_id` is NOT silently rewritten to null. The frozen
        # host read it with `?? null`, which is why 168 of the 228 measured
        # refusals in the cost study were this one benign cause -- and why the
        # question of required-versus-optional had to be decided rather than
        # inherited from a defaulting read.
        source = self.reference()
        del source["provider_session_id"]
        with self.assertRaises(ContractRefusal) as caught:
            own_record(source, REFERENCE)
        self.assertIn("provider_session_id", str(caught.exception))

    def test_a_null_member_is_not_an_absent_one(self):
        taken = own_record(self.reference(provider_session_id=None), REFERENCE)
        self.assertIsNone(taken["provider_session_id"])

    def test_a_record_that_is_not_a_record_is_refused(self):
        for what, value in [("a list", [1]), ("text", "ref"), ("a number", 7),
                            ("none", None), ("a dict subclass", Shifting())]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    own_record(value, REFERENCE)

    def test_many_extras_become_a_bounded_sample_and_a_count(self):
        # A bounded OUTPUT is not a bounded OPERATION, and an unbounded caller
        # value in a durable message is a different problem again. Both rules
        # were bought with review rounds; both apply here from the start.
        wide = self.reference()
        wide.update({f"{'z' * 300}{index}": index for index in range(60)})
        with self.assertRaises(ContractRefusal) as caught:
            own_record(wide, REFERENCE)
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        self.assertIn("and 57 more", message)

    def test_one_diagnostic_reports_the_rule_missing_received_and_extra(self):
        """W1593's approved hybrid is one diagnostic, not two alternatives.

        A record can be missing required names and carry unexpected names at
        the same time. Reporting the extras and returning early hides half the
        violated exact-record rule; reporting only how many extras were omitted
        is not the approved total received-member count either.
        """
        received = {"authority_uuid": "0" * 32,
                    **{f"unexpected-{index}": index for index in range(7)}}
        with self.assertRaises(ContractRefusal) as caught:
            own_record(received, REFERENCE, what="a session reference")
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        self.assertIn("exact record", message)
        self.assertIn("work_id", message)
        self.assertIn("participant", message)
        self.assertIn("provider_session_id", message)
        self.assertIn("8 received members", message)
        shown = sum(f"unexpected-{index}" in message for index in range(7))
        self.assertGreater(shown, 0)
        self.assertLessEqual(shown, 4)
        self.assertIn(f"and {7 - shown} more", message)

    def test_zero_through_more_than_four_extras_keep_the_bound(self):
        for count in range(6):
            with self.subTest(unexpected=count):
                record = self.reference()
                record.update({f"extra-{index}": index
                               for index in range(count)})
                if count == 0:
                    self.assertEqual(own_record(record, REFERENCE), record)
                    continue
                with self.assertRaises(ContractRefusal) as caught:
                    own_record(record, REFERENCE)
                message = str(caught.exception)
                self.assertLess(len(message), 500)
                self.assertIn(f"{len(REFERENCE) + count} received members",
                              message)

    def test_the_rejected_names_are_walked_once_and_never_copied(self):
        """A BOUNDED OUTPUT IS NOT A BOUNDED OPERATION -- W2929's words.

        The message was already bounded before W1593; the WORK behind it was
        not, because the sampler took `list(names)` and sliced three off the
        front. That copy is proportional to the rejected value, which is the
        property this Work exists to hold.

        A generator is the witness, because a generator CANNOT BE WALKED
        TWICE. If anything here listed, sorted, re-counted or re-read the
        rejected names, the second pass would see an exhausted iterator and
        this would fail. The counter proves the one pass is exactly one, and
        the sample is still honest about how many there were.
        """
        walked = []

        def names():
            for index in range(60):
                walked.append(index)
                yield f"extra-{index}"

        text, total = counted_sample_of(names())
        self.assertEqual(total, 60)
        self.assertEqual(len(walked), 60)
        self.assertIn("and 57 more", text)
        self.assertEqual(text.count("extra-"), 3)

    def test_the_sampler_never_materializes_the_names_it_is_given(self):
        """The generator above is NOT enough, and a mutation said so.

        Putting `list(names)` back in front of that walk leaves every
        behavioural case green: the copy consumes the generator exactly once
        and then walks the copy, so "walked once" is still true and the sample
        and count are still right. The property W1593 is about -- that the
        transient work does not scale with the rejected value -- is a property
        of the CODE SHAPE, and nothing observable from outside distinguishes
        the two. So it is checked where it lives.

        This is deliberately narrow: it forbids materializing THE OPERAND, not
        the small bounded list of shown names the sampler builds on purpose.
        """
        source = pathlib.Path(errors.__file__).read_text(encoding="utf-8")
        sampler = next(
            node for node in ast.parse(source).body
            if isinstance(node, ast.FunctionDef)
            and node.name == "counted_sample_of")
        operand = sampler.args.args[0].arg
        for piece in ast.walk(sampler):
            if isinstance(piece, ast.Call) and isinstance(piece.func, ast.Name):
                greedy = piece.func.id in ("list", "tuple", "set", "frozenset",
                                           "sorted", "len", "reversed")
                names_it = any(isinstance(argument, ast.Name)
                               and argument.id == operand
                               for argument in piece.args)
                self.assertFalse(
                    greedy and names_it,
                    f"`{piece.func.id}({operand})` materializes the rejected "
                    f"names; the sample is bounded but the work would not be")
            if isinstance(piece, ast.Subscript) \
                    and isinstance(piece.value, ast.Name) \
                    and piece.value.id == operand:
                self.fail(f"`{operand}` is subscripted, which walks or copies "
                          f"the whole of it")

    def test_the_diagnostic_holds_the_rule_when_only_one_half_is_broken(self):
        """One message, and only the clauses that are true of this document.

        The combined case is the reviewer's. This is the other half of the
        same rule: a record that breaks ONE side must not be told about a
        violation it did not commit, or the diagnostic teaches the reader to
        stop believing it.
        """
        missing_only = self.reference()
        del missing_only["work_id"]
        with self.assertRaises(ContractRefusal) as caught:
            own_record(missing_only, REFERENCE, what="a session reference")
        message = str(caught.exception)
        self.assertIn("it needs 'work_id'", message)
        self.assertNotIn("does not carry", message)
        self.assertIn("3 received members", message)

        extra_only = self.reference(extra=1)
        with self.assertRaises(ContractRefusal) as caught:
            own_record(extra_only, REFERENCE, what="a session reference")
        message = str(caught.exception)
        self.assertIn("does not carry 'extra'", message)
        self.assertNotIn("it needs", message)
        self.assertIn("5 received members", message)

    def test_no_member_value_reaches_the_diagnostic(self):
        """The message most likely to be logged is a refusal.

        The names of unexpected members are the caller's mistake and are named,
        bounded. Their VALUES are the caller's data and are never the reason
        for anything here, so they do not go into a durable message at all --
        and neither does anything a value might do when asked to render.
        """
        ran = []

        class Value:
            def __repr__(self):
                ran.append("repr")
                return "SECRET"

            __str__ = __repr__

        record = self.reference()
        record["extra"] = Value()
        with self.assertRaises(ContractRefusal) as caught:
            own_record(record, REFERENCE)
        message = str(caught.exception)
        self.assertNotIn("SECRET", message)
        self.assertEqual(ran, [])
        # The frozen member VALUES of a valid-looking record are equally
        # absent: an identifier is data, not a rule.
        wide = self.reference(authority_uuid="a" * 32)
        wide["extra"] = 1
        self.assertNotIn("a" * 32, str(self.refusal(wide)))

    def refusal(self, record):
        with self.assertRaises(ContractRefusal) as caught:
            own_record(record, REFERENCE)
        return caught.exception

    def test_a_non_string_name_is_not_rendered_or_iterated(self):
        ran = []

        class Name:
            def __hash__(self):
                return 17

            def __repr__(self):
                ran.append("repr")
                raise AssertionError("repr ran")

            __str__ = __repr__

            def __iter__(self):
                ran.append("iter")
                raise AssertionError("iter ran")

        record = self.reference()
        record[Name()] = "not a member"
        with self.assertRaises(ContractRefusal) as caught:
            own_record(record, REFERENCE)
        self.assertEqual(ran, [])
        self.assertLess(len(str(caught.exception)), 500)

    def test_coarse_refusal_of_a_mapping_subclass_enumerates_no_keys(self):
        ran = []

        class MappingWithHooks(dict):
            def __len__(self):
                ran.append("len")
                raise AssertionError("len ran")

            def __iter__(self):
                ran.append("iter")
                raise AssertionError("iter ran")

            def items(self):
                ran.append("items")
                raise AssertionError("items ran")

            def keys(self):
                ran.append("keys")
                raise AssertionError("keys ran")

        with self.assertRaises(ContractRefusal) as caught:
            own_record(MappingWithHooks(self.reference()), REFERENCE)
        self.assertEqual(ran, [])
        self.assertLess(len(str(caught.exception)), 500)

    def test_a_hostile_label_is_named_and_never_run(self):
        ran = []
        with self.assertRaises(ContractRefusal) as caught:
            own_record([1], REFERENCE, what=Hostile(ran))
        self.assertEqual(ran, [])
        self.assertIn("Hostile", str(caught.exception))

    def test_a_wide_label_is_bounded(self):
        with self.assertRaises(ContractRefusal) as caught:
            own_record([1], REFERENCE, what="z" * 1_000_000)
        self.assertLess(len(str(caught.exception)), 500)

    def test_escaped_unicode_does_not_expand_a_bounded_diagnostic(self):
        wide = self.reference()
        wide.update({f"{'😀' * 300}{index}": index for index in range(4)})
        with self.assertRaises(ContractRefusal) as caught:
            own_record(wide, REFERENCE)
        self.assertLess(len(str(caught.exception)), 500)

        with self.assertRaises(ContractRefusal) as caught:
            own_record([], REFERENCE, what="\ud800" * 300)
        self.assertLess(len(str(caught.exception)), 500)


if __name__ == "__main__":
    unittest.main()
