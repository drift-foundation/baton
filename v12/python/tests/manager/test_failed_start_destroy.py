"""W34998 — the removal a FAILED START authorizes, and it is not a receipt.

A start that reached the engine, created a container and then failed leaves an
exact runtime and NO INTAKE RECEIPT: nothing was frozen, collected or admitted,
so there is no receipt to authorize a removal with.  `destroy` requires one --
correctly, because `runtimeDestroyBody`'s `intake_receipt_digest` means
"material was taken into custody under a policy" -- so this ending had no way
through it at all.  W32648 reached exactly that wall and stopped there.

APPROVER RULING M34998/M34999: an explicit SIBLING command and an explicit
sibling adapter capability.  The receipt-authorized document and method stay
closed to their original five members, and a failure-record digest never
occupies an `intake_receipt_digest` field.

WHAT THIS SUITE IS ABOUT, and what it deliberately is not.  It is about the
provider: the closed body, the distinct callable, the shared removal core and
the custody the removal must not touch.  It is NOT about the composition --
authority fencing, journal validation, the operation identity, retry and
collision, the cleanup axis and the delivery roots across the complete ending
are W32648's, and a case here that reached into them would be deciding that
Work's shape from outside it.

THE FROZEN 1.0 SCHEMAS ARE NOT EDITED, and a case says so by measuring the
files rather than by promising.
"""

import json
import os
import pathlib
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal, digest
from baton_v12.worker_manager import documents, oci

from .test_credentials import (BEARER, CredentialCase, IDENTITY,
                               WORKSPACE_GROUP, live_secret)

RETENTION = "sha256:" + "7" * 64
RECEIPT = "sha256:" + "6" * 64
ASSIGNMENT = {"work_ref": {"authority_uuid": "0123456789abcdef" * 2,
                           "work_id": "01234567-W1"},
              "participant": "baton.claude", "generation": 1}

# The manager-owned `runtime.start-failed` record W32648 journals, and the
# canonical digest OVER IT. Written out here rather than imported from that
# Work, because what this provider accepts is a DIGEST -- it never sees the
# record, and a suite that built one through W32648's composer would be
# asserting that composer instead of this contract.
FAILURE_RECORD = {
    "attempt_id": "attempt-1", "expect": ASSIGNMENT,
    "start_operation_id": "runtime.start:abc", "runtime_id": "runtime-1",
    "execution_runtime": "uncertain",
    "failure": {"category": "ambiguous", "code": "runtime-start",
                "message": "the engine created a container and then failed",
                "durable": True},
}
FAILED_START = digest(FAILURE_RECORD)


class Engine:
    """Every vector recorded, and the inspect answer a case may set."""

    def __init__(self, state="absent"):
        self.vectors = []
        self.state = state

    def __call__(self, argv):
        self.vectors.append(list(argv))
        if "inspect" in argv:
            if self.state == "absent":
                return {"status": 1, "stdout": "",
                        "stderr": "No such object: runtime-1"}
            return {"status": 0, "stdout": json.dumps(
                [{"Id": "runtime-1", "Name": "/baton-1",
                  "State": {"Status": self.state, "Running":
                            self.state == "running", "ExitCode": 0},
                  "Image": IDENTITY["image_digest"],
                  "Config": {"Labels": {}, "User": "65532:65532"},
                  "HostConfig": {"Mounts": []}}]), "stderr": ""}
        return {"status": 0, "stdout": "runtime-1\n", "stderr": ""}


class ProviderCase(CredentialCase):
    """The adapter, over a recording engine and this suite's own roots."""

    def built(self, engine=None, delivery=None):
        return oci.OciAdapter(
            "docker", engine or Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=WORKSPACE_GROUP,
            credential_delivery=delivery, launch_delivery=self.launched())

    def failed_start(self, **overrides):
        body = {"assignment_ref": dict(ASSIGNMENT),
                "runtime_attempt_id": "attempt-1",
                "runtime_id": "runtime-1",
                "failed_start_record_digest": FAILED_START,
                "retention_policy_digest": RETENTION}
        body.update(overrides)
        return body

    def receipt_authorized(self, **overrides):
        body = {"assignment_ref": dict(ASSIGNMENT),
                "runtime_attempt_id": "attempt-1",
                "runtime_id": "runtime-1",
                "intake_receipt_digest": RECEIPT,
                "retention_policy_digest": RETENTION}
        body.update(overrides)
        return body

    def result_directory(self):
        """The unique directory a failed start left behind, with a SENTINEL.

        Untrusted when it was created and untrusted afterwards: this provider
        must leave every byte of it exactly where it is.
        """
        place = os.path.join(self.workspace, "result-attempt-1")
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "sentinel.txt"), "wb") as handle:
            handle.write(b"the worker got this far")
        return place


class TheTwoCommandsAreSiblingsAndNotAUnion(ProviderCase):

    def test_each_document_is_closed_to_its_own_five_members(self):
        self.assertEqual(
            documents.FAILED_START_DESTROY_COMMAND,
            ("assignment_ref", "runtime_attempt_id", "runtime_id",
             "failed_start_record_digest", "retention_policy_digest"))
        # AND THE RECEIPT-AUTHORIZED ONE IS UNTOUCHED, which is the ruling's
        # first sentence.
        self.assertEqual(
            documents.DESTROY_COMMAND,
            ("assignment_ref", "runtime_attempt_id", "runtime_id",
             "intake_receipt_digest", "retention_policy_digest"))
        # NEITHER DIGEST APPEARS IN THE OTHER'S DOCUMENT AT ALL -- required
        # or optional. Asserting only the required half was a real hole: a
        # mutation that added the failure digest as an OPTIONAL member of the
        # receipt-authorized command measured zero against this suite, which
        # is exactly the conflation the ruling forbids arriving through the
        # member set nobody was looking at.
        for name, forbidden in (("destroy.command",
                                 "failed_start_record_digest"),
                                ("destroy.failed-start-command",
                                 "intake_receipt_digest")):
            with self.subTest(document=name):
                required, optional = documents.CONTRACTS[name]
                self.assertNotIn(forbidden, required)
                self.assertNotIn(forbidden, optional)
                # AND NEITHER TAKES ANY OPTIONAL MEMBER: both are closed to
                # exactly five, and an optional member is a place a sixth
                # could arrive without anything saying so.
                self.assertEqual(optional, ())

    def test_the_constructor_holds_its_contract(self):
        made = documents.failed_start_destroy_command(**self.failed_start())
        self.assertEqual(sorted(made),
                         sorted(documents.FAILED_START_DESTROY_COMMAND))
        for member in documents.FAILED_START_DESTROY_COMMAND:
            with self.subTest(missing=member):
                body = self.failed_start()
                body.pop(member)
                with self.assertRaises(ContractRefusal):
                    documents.failed_start_destroy_command(**body)
        with self.assertRaises(ContractRefusal):
            documents.failed_start_destroy_command(
                **self.failed_start(), unexpected="hello")

    def test_neither_method_accepts_the_other_s_body(self):
        """CROSS-CALLING REFUSES, before any engine activity.

        This is the case the "not a union, no fallback" rule exists for: a
        receiver that took either body would let a caller authorize a removal
        with whichever digest it happened to hold, and the two mean opposite
        things.
        """
        for name, body in (("destroy", self.failed_start()),
                           ("destroy_failed_start",
                            self.receipt_authorized())):
            with self.subTest(method=name):
                engine = Engine()
                with self.assertRaises(ContractRefusal) as caught:
                    getattr(self.built(engine), name)(body)
                self.assertEqual(caught.exception.category, "integrity")
                self.assertEqual(engine.vectors, [],
                                 "a cross-called body reached the engine")

    def test_a_missing_or_extra_member_refuses_before_the_engine(self):
        for member in documents.FAILED_START_DESTROY_COMMAND:
            with self.subTest(missing=member):
                engine = Engine()
                body = self.failed_start()
                body.pop(member)
                with self.assertRaises(ContractRefusal):
                    self.built(engine).destroy_failed_start(body)
                self.assertEqual(engine.vectors, [])
        engine = Engine()
        with self.assertRaises(ContractRefusal):
            self.built(engine).destroy_failed_start(
                self.failed_start(unexpected="hello"))
        self.assertEqual(engine.vectors, [])

    def test_a_null_runtime_refuses_before_the_engine(self):
        """This command exists only for the exact runtime a post-create
        reconciliation attached, so a caller with nothing to remove has no
        command to send."""
        for value in (None, "", 7, ["runtime-1"]):
            with self.subTest(runtime_id=value):
                engine = Engine()
                with self.assertRaises(ContractRefusal) as caught:
                    self.built(engine).destroy_failed_start(
                        self.failed_start(runtime_id=value))
                self.assertIn("a failed-start runtime id",
                              caught.exception.message)
                self.assertEqual(engine.vectors, [])

    def test_the_operation_may_ride_beside_the_body(self):
        """The accepted destroy crossing carries its operation beside the
        body, and this one follows it -- without that metadata changing the
        five operands."""
        engine = Engine()
        answered = self.built(engine).destroy_failed_start(
            {**self.failed_start(),
             "operation": {"operation_id": "runtime.destroy-failed:1",
                           "signature_digest": RETENTION}})
        self.assertEqual(answered["state"], "absent")


class TheExactRuntimeIsRemovedAndProvedGone(ProviderCase):

    def test_the_exact_identity_is_force_removed_and_then_observed(self):
        engine = Engine()
        answered = self.built(engine).destroy_failed_start(
            self.failed_start())
        removed = [one for one in engine.vectors if "rm" in one]
        self.assertEqual(len(removed), 1, engine.vectors)
        self.assertIn("runtime-1", removed[0])
        self.assertIn("--force", removed[0])
        # AND THE REMOVAL IS NOT THE PROOF: the identity is inspected after it.
        self.assertTrue(any("inspect" in one for one in engine.vectors))
        self.assertEqual(answered["runtime_id"], "runtime-1")
        self.assertEqual(answered["state"], "absent")

    def test_only_absent_settles_and_the_others_stay_distinguishable(self):
        for state in ("running", "quiescent", "uncertain"):
            with self.subTest(state=state):
                answered = self.built(Engine(state=state)) \
                    .destroy_failed_start(self.failed_start())
                self.assertNotEqual(answered["state"], "absent")
                self.assertEqual(answered["launch"]["lifecycle_state"],
                                 "unresolved", answered)

    def test_the_answer_is_the_same_closed_observation_destroy_answers(self):
        """One observation shape, whichever command authorized the removal.

        A caller that had to read two shapes would have two ways to decide the
        same question, and the second one is the one nobody maintains.
        """
        engine, other = Engine(), Engine()
        failed = self.built(engine).destroy_failed_start(self.failed_start())
        receipted = self.built(other).destroy(self.receipt_authorized())
        self.assertEqual(sorted(failed), sorted(receipted))
        self.assertEqual(sorted(failed),
                         ["credentials", "launch", "runtime_id", "state",
                          "why"])

    def test_repeating_the_removal_answers_the_same_absence(self):
        adapter = self.built(Engine())
        first = adapter.destroy_failed_start(self.failed_start())
        again = adapter.destroy_failed_start(self.failed_start())
        self.assertEqual(first["state"], again["state"])
        self.assertEqual(again["state"], "absent")


class TheDeliveriesUseTheirExistingOrderedTeardown(ProviderCase):

    def test_a_delivered_credential_is_torn_down_on_positive_absence(self):
        delivered = self.delivery()
        self.assertTrue(live_secret(BEARER))
        answered = self.built(Engine(), delivery=delivered) \
            .destroy_failed_start(self.failed_start())
        self.assertEqual(answered["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(os.path.exists(delivered.root))
        self.assertFalse(live_secret(BEARER))

    def test_a_surviving_runtime_leaves_the_delivery_unresolved(self):
        """A container this manager cannot say is absent may still be reading
        the mount, so removing the file under it would report an ending that
        has not happened."""
        delivered = self.delivery()
        answered = self.built(Engine(state="running"), delivery=delivered) \
            .destroy_failed_start(self.failed_start())
        self.assertEqual(answered["credentials"]["lifecycle_state"],
                         "unresolved")
        self.assertTrue(os.path.exists(delivered.root))
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(delivered)

    def test_the_retry_after_an_unresolved_teardown_settles_it(self):
        delivered = self.delivery()
        adapter = self.built(Engine(state="running"), delivery=delivered)
        self.assertEqual(
            adapter.destroy_failed_start(self.failed_start())
            ["credentials"]["lifecycle_state"], "unresolved")
        # THE PROVIDER'S STATE IS THE PROVIDER'S FACT, re-asked rather than
        # remembered: a second adapter over an engine that now answers absent
        # finishes the teardown the first one could not.
        settled = self.built(Engine(), delivery=delivered) \
            .destroy_failed_start(self.failed_start())
        self.assertEqual(settled["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(os.path.exists(delivered.root))

    def test_no_second_teardown_owner_is_introduced(self):
        """The ordered teardown has ONE implementation.

        Both public methods reach it through the same private core, so there
        is no second order that could drift from the accepted one.
        """
        import inspect
        source = inspect.getsource(oci.OciAdapter.destroy_failed_start)
        self.assertIn("self._removed(", source)
        self.assertNotIn("_torn_down", source)
        self.assertNotIn("_launch_ended", source)
        self.assertIn("self._removed(",
                      inspect.getsource(oci.OciAdapter.destroy))


class TheUntrustedResultDirectoryIsLeftExactlyWhereItIs(ProviderCase):

    def sentinel_survives(self, place):
        with open(os.path.join(place, "sentinel.txt"), "rb") as handle:
            self.assertEqual(handle.read(), b"the worker got this far")

    def test_a_successful_removal_touches_nothing_in_it(self):
        place = self.result_directory()
        before = sorted(os.listdir(place))
        self.built(Engine()).destroy_failed_start(self.failed_start())
        self.assertTrue(os.path.isdir(place))
        self.assertEqual(sorted(os.listdir(place)), before)
        self.sentinel_survives(place)

    def test_repeated_removal_and_a_rebuilt_adapter_touch_nothing_either(self):
        """Process reconstruction: nothing about the directory is remembered
        between adapters, so nothing about it can be acted on."""
        place = self.result_directory()
        for _ in range(2):
            self.built(Engine()).destroy_failed_start(self.failed_start())
        rebuilt = self.built(Engine(state="running"), delivery=self.delivery())
        rebuilt.destroy_failed_start(self.failed_start())
        self.sentinel_survives(place)
        self.assertTrue(os.path.isdir(place))

    def test_the_provider_names_no_result_directory_operand_at_all(self):
        """The strongest form of "does not touch it": there is nothing to
        touch it with. The five operands are an assignment, an attempt, a
        runtime and two digests."""
        self.assertNotIn("result", " ".join(
            documents.FAILED_START_DESTROY_COMMAND))
        # THE CODE, NOT THE PROSE. The docstring says what the method must not
        # do and therefore contains every one of these words; scanning it too
        # would make this case fail for saying the right thing.
        import ast
        import inspect
        body = ast.parse(inspect.getsource(
            oci.OciAdapter.destroy_failed_start).strip())
        statements = body.body[0].body
        if isinstance(statements[0], ast.Expr) \
                and isinstance(statements[0].value, ast.Constant):
            statements = statements[1:]
        source = "\n".join(ast.unparse(one) for one in statements)
        for forbidden in ("os.remove", "os.rmdir", "shutil", "open(",
                          "collect", "quarantine", "freeze"):
            self.assertNotIn(forbidden, source, forbidden)
        # AND THE CHECK CAN ACTUALLY FAIL, which a scan over a body this short
        # is worth proving: the words it does contain are found.
        self.assertIn("_removed", source)


class NoFrozenSchemaIsEdited(ProviderCase):

    def test_no_worker_control_schema_names_the_failure_digest(self):
        """The provider boundary is trusted manager-to-adapter traffic.

        No worker or remote peer needs this command, and putting it on the
        wire would require a new negotiated minor version -- so a case that
        measures the frozen files is the honest form of "we did not".
        """
        schemas = pathlib.Path(oci.__file__).parent.parent / "contracts" \
            / "schema"
        found = sorted(one.name for one in schemas.glob("*.schema.json"))
        self.assertTrue(found)
        for name in found:
            with self.subTest(schema=name):
                text = (schemas / name).read_text(encoding="utf-8")
                self.assertNotIn("failed_start_record_digest", text)
                self.assertNotIn("destroy.failed-start-command", text)

    def test_the_frozen_destroy_body_still_requires_its_receipt(self):
        schemas = pathlib.Path(oci.__file__).parent.parent / "contracts" \
            / "schema"
        control = json.loads(
            (schemas / "worker-control-1.0.schema.json").read_text(
                encoding="utf-8"))
        found = []

        def walk(node):
            if isinstance(node, dict):
                if "intake_receipt_digest" in node.get("properties", {}):
                    found.append(sorted(node.get("required", [])))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for value in node:
                    walk(value)

        walk(control)
        self.assertTrue(found, "the frozen destroy body was not located")
        for required in found:
            self.assertIn("intake_receipt_digest", required)


if __name__ == "__main__":
    unittest.main()
