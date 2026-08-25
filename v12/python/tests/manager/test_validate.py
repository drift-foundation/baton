"""W4 cut A — Draft 2020-12 validation, in this package's words.

The library decides the CONTRACT; this package decides the DIAGNOSTIC. That
split is the whole design, because `jsonschema` renders the rejected instance
into its messages — which is what makes its errors useful to a developer and
exactly what a boundary that must never render a rejected value cannot do.
"""

import unittest

from baton_v12.contracts import (ContractRefusal, validate_against,
                                 validate_agent_session,
                                 validate_worker_control, WORKER_CONTROL)
from baton_v12.contracts import validate as validate_module


# A worker-control envelope the frozen schema ACCEPTS.
#
# Built by reading the schema rather than by guessing: the top level is a
# `oneOf` over seventeen message shapes, and `control.error` additionally
# requires `message_type: "reply"` and a body carrying all eight members of
# `controlErrorBody`. My first fixture was rejected, and the case that used it
# SKIPPED -- which is the silent-acceptance weakness I have been caught on
# before, so it is a real document now and the accept path genuinely runs.
ERROR_BODY = {"category": "integrity", "code": "schema",
              "summary": "a document did not validate", "retry": "never",
              "operation_state": "unsubmitted", "assignment_ref": None,
              "runtime_attempt_id": None, "diagnostic_artifact": None}


def envelope(**overrides):
    from baton_v12.contracts import digest
    body = dict(ERROR_BODY)
    document = {"protocol": "baton.worker-control",
                "version": {"major": 1, "minor": 0},
                "message_type": "reply",
                "kind": "control.error",
                "message_id": "msg-1",
                "correlation_id": "msg-0",
                "sent_at": "2026-08-24T00:00:00.000Z",
                "sender": {"role": "worker-manager", "instance_id": "inst-1"},
                "operation": None,
                "body_digest": digest(body),
                "body": body,
                "extensions": {}}
    document.update(overrides)
    return document


class TheLibraryDecidesTheContract(unittest.TestCase):

    def test_a_document_the_schema_rejects_is_refused(self):
        with self.assertRaises(ContractRefusal) as caught:
            validate_worker_control({"protocol": 7})
        self.assertEqual(caught.exception.category, "integrity")
        self.assertEqual(caught.exception.code, "schema")

    def test_the_refusal_names_the_keyword_and_the_path(self):
        # The schema's own vocabulary -- `type`, `required`, `pattern` -- and the
        # document's SHAPE. Both are facts about the contract rather than about
        # the caller's value.
        with self.assertRaises(ContractRefusal) as caught:
            validate_worker_control({"protocol": 7})
        message = str(caught.exception)
        self.assertIn("breaks", message)
        # A KEYWORD from the schema's own vocabulary. Which one depends on which
        # branch got furthest, so the case asserts the vocabulary rather than
        # guessing the branch -- my first version named two keywords and the
        # answer was a third.
        self.assertTrue(
            any(keyword in message for keyword in
                ("type", "required", "const", "enum", "pattern", "maxLength",
                 "additionalProperties", "minLength")), message)

    def test_a_combinator_is_followed_to_the_failure_underneath_it(self):
        """"The document breaks oneOf" is true and helps nobody.

        This schema's top level is one `oneOf` over every message shape, so a
        fault that stopped at the outer error would say nothing at all about
        what was wrong. Found by my own case rather than by a review.
        """
        with self.assertRaises(ContractRefusal) as caught:
            validate_worker_control(envelope(protocol="not-the-protocol"))
        message = str(caught.exception)
        self.assertIn("under oneOf", message)
        self.assertNotEqual(message.count("breaks"), 0)
        # And the count sees through the combinator too, or "and N more" would
        # always be zero for the document that needs it most.
        self.assertIn("more", message)

    def test_a_document_the_schema_accepts_is_accepted(self):
        # A boundary that refused everything would satisfy every other case here
        # and no contract at all.
        self.assertEqual(validate_worker_control(envelope()), envelope())

    def test_validation_returns_an_owned_document(self):
        source = envelope()
        taken = validate_worker_control(source)
        # Returned OWNED, so a caller that validates cannot then go on to use
        # the original -- the same "validate one view, execute another" defect
        # this cut exists to make impossible.
        self.assertIsNot(taken, source)
        self.assertEqual(taken, source)

    def test_a_caller_supplied_validator_is_not_executed(self):
        ran = []

        class HostileValidator:
            def iter_errors(self, document):
                ran.append("iter_errors")
                raise AssertionError("caller-supplied validator ran")

        with self.assertRaises(ContractRefusal):
            validate_against(HostileValidator(), envelope())
        self.assertEqual(ran, [])

    def test_mutating_the_readable_schema_does_not_change_validation(self):
        original = WORKER_CONTROL["oneOf"]
        try:
            WORKER_CONTROL["oneOf"] = []
            self.assertEqual(validate_worker_control(envelope()), envelope())
        finally:
            WORKER_CONTROL["oneOf"] = original


class ThisPackageDecidesTheDiagnostic(unittest.TestCase):

    HUGE = "q" * 1_000_000

    def test_the_library_prose_never_leaves_the_module(self):
        """The finding this module exists to prevent.

        `jsonschema` puts the rejected instance in its message. If that prose
        were forwarded, a one-million-character rejected value would arrive in a
        diagnostic by way of a dependency's helpfulness -- past every bound this
        package spent three reviews establishing.
        """
        with self.assertRaises(ContractRefusal) as caught:
            validate_worker_control(envelope(kind=self.HUGE))
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        self.assertNotIn(self.HUGE, message)
        self.assertNotIn("is not one of", message)

    def test_a_wide_member_name_is_rendered_by_our_rule(self):
        with self.assertRaises(ContractRefusal) as caught:
            validate_worker_control(envelope(**{self.HUGE: 1}))
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        self.assertNotIn(self.HUGE, message)

    def test_many_failures_become_a_bounded_sample_and_a_count(self):
        # A wide record can break hundreds of constraints. The W1593 rule
        # applies to the explanation: a fixed budget, a bounded sample, a total,
        # and no rejected values.
        broken = {f"member{index}": index for index in range(200)}
        with self.assertRaises(ContractRefusal) as caught:
            validate_worker_control(broken)
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        self.assertIn("more", message)

    def test_the_shown_failures_are_capped_when_there_are_several(self):
        """The sampling cap, witnessed where it can actually be reached.

        Against the whole schema `iter_errors` yields ONE top-level error -- the
        `oneOf` -- so the cap on shown failures is unreachable there and a
        mutation removing it changed nothing. It is reachable against a single
        message shape, which is what `validate_against` exists to allow, so the
        case goes there rather than pretending the cap is covered.
        """
        import json
        import jsonschema
        from baton_v12.contracts import WORKER_CONTROL
        one_shape = dict(WORKER_CONTROL)
        one_shape.pop("oneOf")
        one_shape.update(WORKER_CONTROL["$defs"]["controlEnvelope"])
        validator = jsonschema.Draft202012Validator(one_shape)
        broken = envelope(message_type="command", kind="control.error",
                          message_id="", sent_at="not-a-timestamp",
                          body_digest="not-a-digest")
        with self.assertRaises(ContractRefusal) as caught:
            # The PRIVATE body, deliberately. `validate_against` now refuses a
            # validator this package does not own, which is the seam the review
            # closed -- so the cap is witnessed below that door rather than by
            # reopening it.
            validate_module._validate_with(validator, broken, what="an envelope")
        message = str(caught.exception)
        self.assertLess(len(message), 500)
        # Three shown, the rest counted.
        self.assertEqual(message.count("breaks"), 3)
        self.assertIn("more", message)

    def test_a_behaviour_bearing_document_never_reaches_the_validator(self):
        """Ownership FIRST, and the order is the property.

        The validator is never the thing that decides whether a `__getitem__`
        override is admissible, because one cannot reach it -- `own` refuses it
        while the library is still uninvolved. Measured by counting reads on a
        subclass that would answer differently each time.
        """
        class Shifting(dict):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.reads = 0

            def __getitem__(self, key):
                self.reads += 1
                return "core.errors"

        shifting = Shifting(envelope())
        with self.assertRaises(ContractRefusal):
            validate_worker_control(shifting)
        self.assertEqual(shifting.reads, 0)

    def test_a_hostile_value_is_refused_without_being_run(self):
        ran = []

        class Hostile:
            def __repr__(self):
                ran.append("repr")
                raise AssertionError("__repr__ ran")

            __str__ = __repr__

            def __format__(self, specification):
                ran.append("format")
                raise AssertionError("__format__ ran")

        with self.assertRaises(ContractRefusal):
            validate_worker_control(envelope(kind=Hostile()))
        self.assertEqual(ran, [])

    def test_the_label_is_the_callers_and_is_bounded_like_any_other(self):
        with self.assertRaises(ContractRefusal) as caught:
            validate_worker_control({"protocol": 7}, what=self.HUGE)
        self.assertLess(len(str(caught.exception)), 500)


class BothFrozenSchemasAreReachable(unittest.TestCase):

    def test_each_frozen_schema_has_its_own_entry_point(self):
        for validate in (validate_worker_control, validate_agent_session):
            with self.subTest(validate=validate.__name__):
                with self.assertRaises(ContractRefusal):
                    validate({"nothing": "here"})

    def test_the_two_validators_are_not_the_same_object(self):
        # One validator serving two schemas would accept a worker-control
        # document as an agent-session one, which is the kind of agreement
        # nobody notices until it matters.
        self.assertIsNot(validate_module._WORKER_CONTROL,
                         validate_module._AGENT_SESSION)

    def test_validate_against_accepts_the_validators_this_package_owns(self):
        # A door that refused everything would satisfy the hostile-validator
        # case and no contract at all.
        for validator in (validate_module._WORKER_CONTROL,
                          validate_module._AGENT_SESSION):
            with self.subTest(validator=id(validator)):
                with self.assertRaises(ContractRefusal):
                    validate_against(validator, {"protocol": 7})
        self.assertEqual(validate_against(validate_module._WORKER_CONTROL,
                                          envelope()), envelope())


if __name__ == "__main__":
    unittest.main()
