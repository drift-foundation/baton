"""W4 cut A — §3.2 canonical bytes and digests, against the frozen oracle.

The port is by OBLIGATION, and the obligations here are unusually literal: a
canonicalizer that disagrees with the frozen reference by one byte disagrees
about every digest built from it. So the vectors are GENERATED FROM the Node
implementation rather than written here, and the interesting ones were chosen to
distinguish the two hosts rather than to agree with them.
"""

import json
import pathlib
import unittest

from baton_v12.contracts import (ContractRefusal, MAX_SAFE_INTEGER,
                                 MAX_DEPTH, MAX_MEMBERS, canonical_bytes,
                                 canonical_text, digest, digest_of_bytes)

VECTORS = json.loads(
    (pathlib.Path(__file__).parent / "canonical-vectors.json")
    .read_text(encoding="utf-8"))

# The documents the vectors were taken over, in the same order. Written here
# rather than serialized into the asset, because a JSON round trip would lose
# exactly the distinctions under test -- an astral member name survives, but
# nothing proves the file did not simply record this implementation's own answer.
DOCUMENTS = [
    {},
    [],
    None,
    True,
    False,
    0,
    MAX_SAFE_INTEGER,
    "hello",
    {"b": 1, "a": 2, "C": 3, "": 4},
    {"a": {"b": [1, 2, {"c": "d"}]}},
    "\"\\/\b\f\n\r\t",
    "\u0000\u0001\u001f",
    "\u007f",
    "séance \U0001F600 日本語",
    {"\U0001F600": 1, "\ue000": 2, "\uffff": 3},
    {"\U00010000": 1, "\ue000": 2},
    "\U0001F600",
    {"é": 1, "é": 2},
    {"a": {"b": {"c": {"d": {"e": {"f": {"g": 1}}}}}}},
    [{"b": 1, "a": 2}, {"d": 3, "c": 4}],
    {f"k{index}": index for index in range(40)},
]


class TheFrozenHostIsTheOracle(unittest.TestCase):

    def test_the_vector_corpus_is_the_one_that_was_generated(self):
        # A corpus nobody compares is a file. This asserts the documents above
        # and the recorded answers are the same list, so a vector cannot be
        # added on one side only.
        self.assertEqual(len(DOCUMENTS), len(VECTORS["vectors"]))
        self.assertIn("contracts.mjs", VECTORS["source"])

    def test_every_vector_canonicalizes_to_the_frozen_bytes(self):
        for document, vector in zip(DOCUMENTS, VECTORS["vectors"]):
            with self.subTest(vector=vector["name"]):
                self.assertEqual(canonical_text(document), vector["canonical"])
                self.assertEqual(canonical_bytes(document),
                                 vector["canonical"].encode("utf-8"))
                self.assertEqual(digest(document), vector["digest"])

    def test_member_order_is_by_utf16_code_units_and_not_code_points(self):
        """The one place a faithful-looking port is silently wrong.

        RFC 8785 orders member names by UTF-16 code units. U+1F600 encodes as
        the surrogate pair D83D DE00, so it sorts BELOW U+E000 -- while Python's
        `sorted()`, which orders by code points, puts it above U+FFFF. The two
        orders produce different canonical forms and therefore different digests
        from the same document.
        """
        document = {"\U0001F600": 1, "\ue000": 2, "\uffff": 3}
        # What this implementation answers, which is the frozen answer.
        self.assertEqual(canonical_text(document),
                         '{"\U0001F600":1,"\ue000":2,"\uffff":3}')
        # What a code-point sort would have answered. Spelled out so the case
        # fails with the two orders side by side rather than with one hash.
        code_point_order = "{" + ",".join(
            f'{json.dumps(name, ensure_ascii=False)}:{document[name]}'
            for name in sorted(document)) + "}"
        self.assertNotEqual(canonical_text(document), code_point_order)


class WhatCannotAcquireADigest(unittest.TestCase):

    def refuses(self, value, *, because):
        with self.subTest(because=because):
            with self.assertRaises(ContractRefusal) as caught:
                canonical_text(value)
            self.assertEqual(caught.exception.category, "integrity")
            self.assertEqual(caught.exception.code, "schema")
            self.assertLess(len(str(caught.exception)), 500)

    def test_a_float_is_refused_by_the_rule_that_names_it(self):
        # A mutation with no witness: removing the float branch still REFUSES,
        # because a float falls through to "no representation for float". The
        # branch exists to give §3.2's reason rather than the generic one, so
        # the case checks the reason -- otherwise the branch is prose.
        for value in (1.5, 0.0, -0.0, float("inf"), float("nan")):
            with self.subTest(value=repr(value)):
                with self.assertRaises(ContractRefusal) as caught:
                    canonical_text(value)
                self.assertIn("floating point", str(caught.exception))

    def test_the_number_space_is_closed(self):
        self.refuses(-1, because="a negative integer")
        self.refuses(MAX_SAFE_INTEGER + 1, because="above the safe range")
        self.refuses(1.5, because="a float")
        self.refuses(-0.0, because="negative zero")
        self.refuses(float("nan"), because="not a number")
        self.refuses(float("inf"), because="infinity")
        self.refuses(0.0, because="a float that looks like an integer")

    def test_invalid_unicode_fails_wherever_it_sits(self):
        # RFC 8785 requires invalid Unicode to FAIL rather than be repaired into
        # a digestible document, and the frozen host was corrected because its
        # check ran on string VALUES only -- so moving the same malformed
        # Unicode into a member NAME made it digestible.
        self.refuses("\ud800", because="a lone high surrogate in a value")
        self.refuses("\udfff", because="a lone low surrogate in a value")
        self.refuses({"\ud800": 1}, because="a lone surrogate in a NAME")
        self.refuses({"a": ["x", "\ud800"]}, because="one nested in an array")

    def test_only_exact_built_in_containers_are_digestible(self):
        # A digest over "something else" is the one failure this boundary exists
        # to prevent, so a container that would serialize as something other
        # than what the caller meant is refused rather than serialized.
        self.refuses(type("D", (dict,), {})({"a": 1}), because="a dict subclass")
        self.refuses(type("L", (list,), {})([1]), because="a list subclass")
        self.refuses((1, 2), because="a tuple")
        self.refuses({1, 2}, because="a set")
        self.refuses(object(), because="an object")
        self.refuses(b"bytes", because="bytes")
        self.refuses({1: "a"}, because="an integer member name")

    def test_a_boolean_is_not_an_integer_and_an_integer_is_not_a_boolean(self):
        # `True` is an `int` in Python. Canonicalizing it as `1` would give two
        # different documents one digest, which is the whole hazard.
        self.assertEqual(canonical_text(True), "true")
        self.assertEqual(canonical_text(1), "1")
        self.assertNotEqual(digest({"a": True}), digest({"a": 1}))

    def test_a_refusal_never_runs_the_value_it_refuses(self):
        ran = []

        class Hostile:
            def __repr__(self):
                ran.append("repr")
                raise AssertionError("__repr__ ran")

            __str__ = __repr__

            def __format__(self, specification):
                ran.append("format")
                raise AssertionError("__format__ ran")

            def __iter__(self):
                ran.append("iter")
                raise AssertionError("__iter__ ran")

        for what, value in [("the document", Hostile()),
                            ("a member", {"a": Hostile()}),
                            ("an entry", [Hostile()]),
                            ("nested", {"a": {"b": [Hostile()]}})]:
            with self.subTest(what=what):
                del ran[:]
                with self.assertRaises(ContractRefusal):
                    canonical_text(value)
                self.assertEqual(ran, [], f"{what}: ran {ran}")

    def test_a_digest_over_bytes_needs_bytes(self):
        self.assertEqual(
            digest_of_bytes(b""),
            "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b"
            "7852b855")
        for what, value in [("text", "bytes"), ("a bytearray", bytearray(b"x")),
                            ("none", None), ("a memoryview", memoryview(b"x"))]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    digest_of_bytes(value)

    def test_canonicalization_enforces_the_owned_shape_bounds(self):
        deep = current = []
        for _ in range(MAX_DEPTH + 2):
            nested = []
            current.append(nested)
            current = nested
        for what, value in [
                ("a document beyond the frozen depth", deep),
                ("an array beyond the frozen width",
                 list(range(MAX_MEMBERS + 1))),
                ("an object beyond the frozen width",
                 {f"k{index}": index for index in range(MAX_MEMBERS + 1)})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    canonical_text(value)

    def test_a_caller_cannot_choose_the_canonicalizers_traversal_depth(self):
        deep = current = []
        for _ in range(MAX_DEPTH + 2):
            nested = []
            current.append(nested)
            current = nested
        with self.assertRaises((ContractRefusal, TypeError)):
            canonical_text(deep, -MAX_DEPTH * 2)


if __name__ == "__main__":
    unittest.main()
