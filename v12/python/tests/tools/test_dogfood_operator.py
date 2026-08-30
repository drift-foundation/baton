"""W39358 — the dogfood operator's composed halves, without a daemon.

`work/records/2026/08/finding-v12-first-useful-dogfood-task/findings/
finding-minimal-supervised-operator/`.

WHAT THIS FILE COVERS AND WHAT IT DOES NOT, said at the top because the
distinction is the honest part of this round. It covers the four units the
operator composes FROM: the deployment authority-session facade, the bounded
source staging, the frozen task read on the way in, and the two
manager-authored protocol documents. The composed ARC -- offer through
absence -- is not built yet and therefore is not tested here; `PROGRESS.md`
says so rather than leaving a reader to infer it from an absent class.

NO DAEMON AND NO CREDENTIAL. Everything here is a pure function over
directories and documents, which is what makes it worth running on every
change rather than only where Docker is reachable.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import ExitStack
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))

from baton_v12.contracts import ContractRefusal, digest      # noqa: E402

from tools import dogfood_operator                            # noqa: E402
from tools.dogfood_operator import (DeploymentSession, OperatorRefusal,
                                    assignment_manifest, frozen_task,
                                    input_manifest, stage_source)  # noqa: E402

WORK_REF = {"authority_uuid": "43c55d4b1234567890abcdef12345678",
            "work_id": "43c55d4b-W1439"}
NOW = "2026-08-30T00:00:00.000Z"
PROFILE = "sha256:" + "6" * 64
ROLE = "sha256:" + "2" * 64
TOOLCHAIN = "sha256:" + "4" * 64
IMAGE = "sha256:" + "5" * 64
POLICIES = {one: "sha256:" + f"{index}" * 64
            for index, one in enumerate(dogfood_operator.POLICY_DIGESTS,
                                        start=1)}
BINDING = {"root": "baton-repository",
           "path": "work/records/2026/08/finding-v12-first-useful-dogfood-task",
           "finding_digest": "sha256:" + "d" * 64,
           "plan_digest": "sha256:" + "e" * 64}
HUMAN = {"artifact_id": "human-contract-1", "media_type": "text/markdown",
         "bytes": 1200, "content_digest": "sha256:" + "b" * 64,
         "locator": "artifact://contracts/human-contract-1"}

TASK = {"schema": "baton.dogfood-task/1",
        "task_id": "w39364-ping-pong-coverage",
        "instructions": "Add focused unit coverage for _observed_readable.",
        "verification": ["python3", "harness.py"],
        "source_root": "source"}


class OperatorCase(unittest.TestCase):

    def setUp(self):
        home = tempfile.mkdtemp(prefix="v12-w39358-")
        self.addCleanup(shutil.rmtree, home, True)
        self.home = home
        self.source = os.path.join(home, "source")
        os.makedirs(self.source)
        self.write(os.path.join(self.source, "harness.py"),
                   "print('the staged harness')\n")
        self.write(os.path.join(self.source, "nested", "preflight.py"),
                   "def _observed_readable():\n    return True\n")
        self.inputs = os.path.join(home, "inputs")
        os.makedirs(self.inputs)

    @staticmethod
    def write(place, body):
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "w", encoding="utf-8") as handle:
            handle.write(body)

    def task(self, document=TASK):
        place = os.path.join(self.home, "task.json")
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(document, handle)
        return place


class OneSession(unittest.TestCase):
    """The facade, and the one member it deliberately does not carry."""

    class Session:
        participant = "baton.claude"

        def __init__(self):
            self.seen = []

        def __getattr__(self, name):
            def call(*arguments):
                self.seen.append((name, arguments))
                return {"answered": name}
            return call

    def test_the_six_operations_delegate_to_the_minted_session(self):
        held = self.Session()
        facade = DeploymentSession(held)
        for member in ("project_work", "slot_holder", "claim",
                       "settle_operation", "assignment_of", "cancel"):
            with self.subTest(member=member):
                self.assertEqual(getattr(facade, member)({"a": 1}),
                                 {"answered": member})
        self.assertEqual([one for one, _a in held.seen],
                         ["project_work", "slot_holder", "claim",
                          "settle_operation", "assignment_of", "cancel"])

    def test_the_bound_identity_is_read_from_the_session(self):
        """Read rather than configured: a deployment that named a participant
        of its own would be binding an authorization to an identity the
        authority never minted one for."""
        self.assertEqual(DeploymentSession(self.Session()).participant,
                         "baton.claude")

    def test_publishing_an_answer_is_a_typed_refusal(self):
        """This pilot runs no `inquire`, so a no-op would answer 'published'
        to something nobody published."""
        with self.assertRaises(OperatorRefusal) as caught:
            DeploymentSession(self.Session()).publish_answer({"a": 1})
        self.assertIn("runs no `inquire`", str(caught.exception))

    def test_the_refusal_is_not_a_contract_refusal(self):
        """A deployment saying it does not carry a capability is a different
        fact from the manager judging its own contract, and an operator that
        conflated them would read a composition mistake as a protocol one."""
        self.assertFalse(issubclass(OperatorRefusal, ContractRefusal))

    def test_a_session_missing_an_operation_is_refused_at_construction(self):
        """`AuthorityPort` checks its seven at construction for the reason
        this does: discovering halfway through an offer that the session
        cannot claim is discovering it after durable state depends on it."""
        class Partial:
            participant = "baton.claude"

            def claim(self, *documents):
                return {}

        with self.assertRaises(OperatorRefusal) as caught:
            DeploymentSession(Partial())
        self.assertIn("no callable", str(caught.exception))

    def test_the_facade_carries_every_operation_the_port_names(self):
        """The port's list is the contract; a facade that fell behind it would
        be refused by the manager rather than by this test, which is later and
        more expensive."""
        facade = DeploymentSession(self.Session())
        for member in SESSION_OPERATIONS_UNDER_TEST:
            with self.subTest(member=member):
                self.assertTrue(callable(getattr(facade, member, None)),
                                member)


SESSION_OPERATIONS_UNDER_TEST = tuple(
    __import__("baton_v12.worker_manager.authority_port", fromlist=["x"])
    .SESSION_OPERATIONS)


class TheSourceIsStagedBoundedAndOnce(OperatorCase):

    def test_the_exact_subset_lands_under_the_fixed_name(self):
        staged = stage_source(self.source, self.inputs)
        place = os.path.join(self.inputs, dogfood_operator.SOURCE_TARGET)
        self.assertTrue(os.path.isfile(os.path.join(place, "harness.py")))
        self.assertTrue(os.path.isfile(os.path.join(place, "nested",
                                                    "preflight.py")))
        self.assertEqual(staged["entry_count"], 2)
        self.assertIn("tree_digest", staged)

    def test_the_manifest_describes_what_was_copied(self):
        """Answered by the manager's own copier rather than measured again:
        two parties measuring one delivery is how they come to disagree."""
        staged = stage_source(self.source, self.inputs)
        self.assertEqual(sorted(one["path"] for one in staged["entries"]),
                         ["harness.py", os.path.join("nested",
                                                     "preflight.py")])

    def test_a_link_in_the_source_is_refused(self):
        """The bound is the manager's no-follow rule, reached through this
        path rather than restated by it."""
        os.symlink("/etc", os.path.join(self.source, "elsewhere"))
        with self.assertRaises(ContractRefusal):
            stage_source(self.source, self.inputs)

    def test_a_source_past_the_entry_ceiling_is_refused(self):
        with self.assertRaises(ContractRefusal):
            stage_source(self.source, self.inputs, max_entries=1)

    def test_a_source_past_the_byte_ceiling_is_refused(self):
        with self.assertRaises(ContractRefusal):
            stage_source(self.source, self.inputs, max_bytes=4)

    def test_staging_twice_into_one_input_root_is_refused(self):
        """An attempt stages its source once. A second staging would replace
        a delivery the manager has already measured."""
        stage_source(self.source, self.inputs)
        with self.assertRaises(OperatorRefusal) as caught:
            stage_source(self.source, self.inputs)
        self.assertIn("already exists", str(caught.exception))


class TheFrozenTaskIsReadOnTheWayIn(OperatorCase):
    """Read here as well as inside the container, so an operator learns about
    a malformed task before a container starts rather than from a failed
    attempt's evidence."""

    def refuses(self, document, expected):
        with self.assertRaises(OperatorRefusal) as caught:
            frozen_task(self.task(document))
        self.assertIn(expected, str(caught.exception))

    def test_the_operators_own_document_is_answered_whole(self):
        self.assertEqual(frozen_task(self.task()), TASK)

    def test_an_absent_task_is_refused(self):
        with self.assertRaises(OperatorRefusal) as caught:
            frozen_task(os.path.join(self.home, "no-such-task.json"))
        self.assertIn("no readable frozen task", str(caught.exception))

    def test_a_task_from_another_generation_is_refused(self):
        self.refuses(dict(TASK, schema="baton.dogfood-task/2"),
                     "this deployment stages")

    def test_an_extra_member_is_refused(self):
        self.refuses(dict(TASK, alias="a second identity"), "unexpected alias")

    def test_a_missing_member_is_refused(self):
        self.refuses({one: TASK[one] for one in TASK if one != "verification"},
                     "missing verification")

    def test_a_task_that_selects_another_source_root_is_refused(self):
        """The staged name is a constant of this deployment, exactly as it is
        a constant of the adapter that reads it."""
        self.refuses(dict(TASK, source_root="../elsewhere"),
                     "stages exactly")

    def test_every_task_member_is_held_before_the_container_starts(self):
        for member, value in (("task_id", 7), ("instructions", []),
                              ("instructions", ""),
                              ("verification", "python3 harness.py"),
                              ("verification", [])):
            with self.subTest(member=member, value=value):
                with self.assertRaises(OperatorRefusal):
                    frozen_task(self.task(dict(TASK, **{member: value})))

    def test_the_document_is_not_json_is_refused(self):
        place = os.path.join(self.home, "task.json")
        self.write(place, "not a document")
        with self.assertRaises(OperatorRefusal):
            frozen_task(place)


class TheProtocolDocumentsAreComposedHere(OperatorCase):
    """`compose_input_root` takes both as operands, so the party that knows
    what this delivery IS authors them."""

    def given(self, staged):
        return input_manifest(
            work_ref=WORK_REF, staged=staged, created_at=NOW,
            manifest_id="input-w39358",
            assignment_contract="v12-assignment-1", human_contract=HUMAN,
            record_binding=BINDING, role_instructions_digest=ROLE,
            runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
            worker_image_digest=IMAGE, policies=POLICIES)

    def composed(self):
        staged = stage_source(self.source, self.inputs)
        given = self.given(staged)
        assignment = assignment_manifest(
            given=given, work_ref=WORK_REF, participant="baton.claude",
            generation=1, attempt_id="attempt-1", offer_id="offer-1",
            claim_receipt_digest="sha256:" + "d" * 64, claim_event_seq=44,
            created_at=NOW, activated_at=NOW,
            assignment_contract="v12-assignment-1",
            manifest_id="assignment-w39358")
        return given, assignment

    def test_the_input_manifest_seals_its_own_digest(self):
        given, _assignment = self.composed()
        held = dict(given)
        held.pop("manifest_digest")
        self.assertEqual(given["manifest_digest"], digest(held))

    def test_the_sources_entry_carries_the_copiers_own_manifest(self):
        """Not a second measurement. A deployment that measured the tree twice
        would be two parties disagreeing about one delivery."""
        staged = stage_source(self.source, self.inputs)
        given = self.given(staged)
        self.assertEqual(given["sources"][0]["content_manifest"], staged)
        self.assertEqual(given["sources"][0]["name"],
                         dogfood_operator.SOURCE_TARGET)

    def test_manifest_paths_are_relative_to_the_two_fixed_roots(self):
        """A source destination is below `/input` and an output path is below
        `/output`; neither spelling carries the retired `workspace/` prefix."""
        given, _assignment = self.composed()
        for role, actual, expected in (
                ("input", given["sources"][0]["destination"], "source"),
                ("output", given["outputs"][0]["path"], "proposal")):
            with self.subTest(role=role):
                self.assertEqual(actual, expected)

    def test_exactly_one_output_is_declared(self):
        """The parent finding's own ruling: the proposal is one directory
        tree, because a second top-level result document would be unmeasured
        auxiliary material."""
        given, _assignment = self.composed()
        self.assertEqual([one["name"] for one in given["outputs"]],
                         ["proposal"])
        self.assertEqual(given["outputs"][0]["type"], "directory-result")
        self.assertEqual(given["outputs"][0]["constraints"]["link_policy"],
                         "forbid")

    def test_the_task_does_not_travel_in_the_protocol_document(self):
        """The schema's ruling, not a preference. A first cut added `task_id`
        and the manager's own composer refused the document; the task is a
        WORKLOAD convention and travels in `/input/task.json`."""
        given, _assignment = self.composed()
        self.assertNotIn("task_id", given)
        self.assertNotIn(TASK["instructions"], json.dumps(given))

    def test_an_incomplete_policy_set_is_refused_before_the_manager_sees_it(
            self):
        """The frozen schema requires all seven, so an operator learns about a
        missing one here rather than from a refused root with the source
        already staged."""
        staged = stage_source(self.source, self.inputs)
        with self.assertRaises(OperatorRefusal) as caught:
            input_manifest(
                work_ref=WORK_REF, staged=staged, created_at=NOW,
                manifest_id="input-w39358",
                assignment_contract="v12-assignment-1", human_contract=HUMAN,
                record_binding=BINDING, role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
                worker_image_digest=IMAGE,
                policies={one: POLICIES[one]
                          for one in list(POLICIES)[:-1]})
        self.assertIn("missing retention_policy_digest", str(caught.exception))

    def test_a_policy_value_that_is_not_a_digest_is_refused_here(self):
        staged = stage_source(self.source, self.inputs)
        malformed = dict(POLICIES, policy_digest="not-a-digest")
        with self.assertRaises(OperatorRefusal):
            input_manifest(
                work_ref=WORK_REF, staged=staged, created_at=NOW,
                manifest_id="input-w39358",
                assignment_contract="v12-assignment-1",
                human_contract=HUMAN, record_binding=BINDING,
                role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
                worker_image_digest=IMAGE, policies=malformed)

    def test_the_assignment_binds_the_input_manifest_it_was_minted_against(
            self):
        given, assignment = self.composed()
        self.assertEqual(assignment["input_manifest_digest"],
                         given["manifest_digest"])
        self.assertEqual(assignment["policy_digest"], given["policy_digest"])
        self.assertEqual(assignment["runtime_profile_digest"],
                         given["runtime_profile_digest"])

    def test_the_assignment_seals_its_own_digest(self):
        _given, assignment = self.composed()
        held = dict(assignment)
        held.pop("manifest_digest")
        self.assertEqual(assignment["manifest_digest"], digest(held))

    def test_the_two_documents_compose_a_real_input_root(self):
        """THE ONE THAT MATTERS: the manager's own composer accepts them.

        A pair of documents this module shaped to look right proves nothing;
        `compose_input_root` is the boundary a real delivery crosses, and it
        holds both against the contract before writing either.
        """
        from baton_v12.worker_manager.workspaces import compose_input_root

        given, assignment = self.composed()
        compose_input_root(self.inputs, given, assignment,
                           assignment=dict(assignment["assignment_ref"]),
                           runtime_attempt_id="attempt-1")
        for name in ("input.json", "assignment.json"):
            self.assertTrue(os.path.isfile(os.path.join(self.inputs, name)),
                            name)
        # AND THE STAGED SOURCE SURVIVED THE COMPOSITION, which is the half a
        # document check cannot establish: the operator stages before the
        # manager composes, so a composer that cleared the root would have
        # taken the delivery with it.
        self.assertTrue(os.path.isfile(os.path.join(
            self.inputs, dogfood_operator.SOURCE_TARGET, "harness.py")))


if __name__ == "__main__":
    unittest.main()


class ThePreflightRunsBeforeAnythingIsStaged(OperatorCase):
    """W39358 review 2026-08-30T05:53:19Z [P1].

    The first round put the policy check inside `input_manifest`, which takes
    the already-produced staged manifest -- so the record claimed a refusal
    happened "while nothing has been staged" and the code could not deliver
    it. `preflight` is that refusal, and these cases hold it where the claim
    is: before `stage_source` writes anything.
    """

    def granted(self, **overrides):
        given = {"task": TASK, "policies": POLICIES,
                 "worker_image_digest": IMAGE, "toolchain_digest": TOOLCHAIN,
                 "runtime_profile_digest": PROFILE,
                 "role_instructions_digest": ROLE, "record_binding": BINDING,
                 "network": "baton-dogfood"}
        given.update(overrides)
        return given

    def refuses(self, expected, **overrides):
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(**self.granted(**overrides))
        self.assertIn(expected, str(caught.exception))
        # AND NOTHING WAS STAGED, which is the whole point of the ordering.
        self.assertFalse(os.path.exists(
            os.path.join(self.inputs, dogfood_operator.SOURCE_TARGET)))

    def test_a_complete_set_of_grants_passes(self):
        self.assertTrue(dogfood_operator.preflight(**self.granted()))

    def test_a_policy_value_that_is_not_a_digest_is_refused(self):
        """The other half of the finding: the first cut validated the seven
        KEY names, so `policy_digest="not-a-digest"` was accepted here and
        left for the manager to refuse after the delivery existed."""
        self.refuses("policy_digest is not a sha256 digest",
                     policies=dict(POLICIES, policy_digest="not-a-digest"))

    def test_an_incomplete_policy_set_is_refused(self):
        self.refuses("missing retention_policy_digest",
                     policies={one: POLICIES[one]
                               for one in list(POLICIES)[:-1]})

    def test_every_other_digest_operand_is_held_too(self):
        for name in ("worker_image_digest", "toolchain_digest",
                     "runtime_profile_digest", "role_instructions_digest"):
            with self.subTest(operand=name):
                self.refuses(f"{name} is not a sha256 digest",
                             **{name: "latest"})

    def test_a_mutable_image_tag_is_not_a_digest(self):
        """There is no mutable image tag anywhere in this module, and this is
        where an operator finds that out."""
        self.refuses("worker_image_digest is not a sha256 digest",
                     worker_image_digest="baton-dogfood:latest")

    def test_the_record_binding_is_exactly_its_four_members(self):
        self.refuses("the record binding is exactly",
                     record_binding={"root": "baton-repository"})

    def test_an_unnamed_network_is_a_grant_nobody_made(self):
        for wrong in ("", None, 5):
            with self.subTest(network=wrong):
                self.refuses("engine network name", network=wrong)

    def test_a_task_from_another_generation_is_refused_here_too(self):
        self.refuses("this deployment stages",
                     task=dict(TASK, schema="baton.dogfood-task/2"))

    def test_a_held_task_cannot_be_mutated_between_its_two_reads(self):
        """`frozen_task` answers an ordinary writable dict. Preflight must
        re-hold every member before that dict is copied into `/input`, rather
        than checking only the schema and trusting the earlier read."""
        for member, value in (("task_id", 7), ("instructions", ""),
                              ("verification", []),
                              ("source_root", "../elsewhere")):
            with self.subTest(member=member):
                self.refuses("frozen task", task=dict(
                    TASK, **{member: value}))

    def test_record_binding_values_are_held_before_staging(self):
        """Four right key names are not a binding: both digests and both
        locators reach the frozen manifest schema after staging otherwise."""
        for member, value in (("finding_digest", "latest"),
                              ("plan_digest", "sha256:no"),
                              ("root", ""), ("path", "/absolute")):
            with self.subTest(member=member):
                self.refuses("record binding", record_binding=dict(
                    BINDING, **{member: value}))

    def test_record_binding_locators_use_the_frozen_manifest_grammar(self):
        """A looser handwritten locator check only moves part of the frozen
        manifest refusal before staging.  Both the opaque root and relative
        path must hold the schema's length and character rules here too."""
        for member, value in (("root", "has space"),
                              ("root", "r" * 161),
                              ("path", "."),
                              ("path", "record\\binding"),
                              ("path", "record\0binding"),
                              ("path", "r" * 513)):
            with self.subTest(member=member, value=repr(value)):
                self.refuses("record binding", record_binding=dict(
                    BINDING, **{member: value}))

    def test_the_network_is_held_to_the_engine_grammar_before_staging(self):
        """Merely non-empty defers this refusal to `run_vector`, after the
        source and task already exist in the attempt input root."""
        for network in ("--network=host", "../bridge", "two words"):
            with self.subTest(network=network):
                self.refuses("engine network name", network=network)

    def test_a_non_document_policy_set_is_a_typed_preflight_refusal(self):
        """A public boundary reports a composition fault; it does not leak a
        `TypeError` while trying to iterate a value it never held."""
        for policies in (None, [], "policy_digest"):
            with self.subTest(policies=policies):
                self.refuses("policy identities", policies=policies)

    def test_one_refusal_reports_the_whole_preflight(self):
        """Named faults are collected rather than raised one at a time, so an
        operator fixes a launch once instead of discovering its grants in the
        order this module happens to check them."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(**self.granted(
                network="", worker_image_digest="latest",
                record_binding={}))
        message = str(caught.exception)
        for expected in ("worker_image_digest is not a sha256 digest",
                         "the record binding is exactly",
                         "engine network name"):
            self.assertIn(expected, message)


class TheStatedCeilingsAreACeiling(OperatorCase):
    """W39358 review 2026-08-30T05:53:19Z [P1]: the exported helper forwarded
    caller-selected bounds unchanged, so a caller could widen the bound this
    module states -- which makes a stated bound a suggestion."""

    def test_a_caller_may_narrow_its_own_delivery(self):
        staged = stage_source(self.source, self.inputs, max_entries=2,
                              max_bytes=1024)
        self.assertEqual(staged["entry_count"], 2)

    def test_a_caller_may_not_widen_the_operators_ceiling(self):
        for name, value in (
                ("max_entries", dogfood_operator.MAX_SOURCE_ENTRIES + 1),
                ("max_bytes", dogfood_operator.MAX_SOURCE_BYTES + 1)):
            with self.subTest(operand=name):
                with self.assertRaises(OperatorRefusal) as caught:
                    stage_source(self.source, self.inputs, **{name: value})
                self.assertIn("may not widen it", str(caught.exception))

    def test_a_narrower_ceiling_is_a_positive_whole_number(self):
        """Bool, zero and text currently reach comparisons or the copier as
        accidental Python coercions rather than as this operator's bound."""
        for name, value in (("max_entries", True), ("max_entries", 0),
                            ("max_bytes", False), ("max_bytes", "1024")):
            with self.subTest(operand=name, value=value):
                with self.assertRaises(OperatorRefusal):
                    stage_source(self.source, self.inputs, **{name: value})


class TheOperatorAndTheWorkerAgreeOnTheTasksCONSTANTS(unittest.TestCase):
    """WHAT MOST OF THIS COMPARES IS CONSTANTS, and the name says so.

    THE LESSON THAT SURVIVED, and it is the useful one: equal regex TEXT did
    not prove equal PREDICATES. This class once carried a claim that the two
    ends held "one whole contract" while comparing only the member tuple, the
    schema, the source name and the pattern text — and the predicates differed,
    because `claude_agent._task` matched `str(document["task_id"])` while this
    operator required exact text. That gap became W44424.

    **Superseded (W44424, closed satisfying):** the asymmetry itself. The
    receiver holds the identity as text before matching now, so both ends
    refuse a numeric identity and the case below asks the receiver's actual
    predicate rather than its pattern — the constants comparison it used to do
    being the very confusion that found the defect.

    The reason the constants matter at all: the operator's read exists to move
    a refusal earlier, so a copy that drifted from the worker's would move it
    back to the failed provider attempt it was meant to avoid.
    """

    def worker(self):
        import importlib.util
        place = (pathlib_worker() / "claude_agent.py")
        spec = importlib.util.spec_from_file_location("claude_agent", place)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_the_closed_member_set_is_one_set(self):
        self.assertEqual(sorted(dogfood_operator._TASK_MEMBERS),
                         sorted(self.worker().TASK_MEMBERS))

    def test_the_schema_is_one_schema(self):
        self.assertEqual(dogfood_operator._TASK_SCHEMA,
                         self.worker().TASK_SCHEMA)

    def test_the_staged_source_name_is_one_name(self):
        """The operator stages it and the adapter reads it by equality; two
        spellings would be a delivery nobody receives."""
        self.assertEqual(dogfood_operator.SOURCE_TARGET,
                         self.worker().SOURCE_ROOT)

    def test_the_task_identity_pattern_text_is_one_pattern(self):
        """The PATTERN, which is not the same claim as the predicate — see
        the case below."""
        self.assertEqual(dogfood_operator._TASK_ID.pattern,
                         self.worker()._TASK_ID.pattern)

    def test_both_ends_refuse_a_numeric_task_id(self):
        """SUPERSEDED AND INVERTED, and it is worth saying why twice over.

        Until W44424 this asserted an ASYMMETRY: the receiver coerced with
        `str()` before matching, so a JSON number was a usable identity to it
        and not to this operator. W44424 closed that — `claude_agent._task`
        requires exact `str` before applying the pattern — so the property
        this case asserted no longer exists.

        AND ITS OLD FORM WAS THE SAME MISTAKE IT WAS ABOUT. It proved "the
        receiver takes it" by applying the receiver's REGEX to `str(7)`
        itself, which is a constants comparison standing in for a predicate —
        exactly the confusion that discovered W44424. Review
        2026-08-30T06:20:54Z [P2] caught it repeating in the case written to
        record it.

        So it asks the receiver's ACTUAL predicate now, through `_task`, over
        a document on disk — the way the receiver is really reached.
        """
        import shutil
        import tempfile

        numeric = dict(TASK, task_id=7)
        with self.assertRaises(OperatorRefusal):
            dogfood_operator.held_task(numeric)

        worker = self.worker()
        home = tempfile.mkdtemp(prefix="v12-w39358-receiver-")
        self.addCleanup(shutil.rmtree, home, True)
        place = os.path.join(home, worker.TASK_DOCUMENT)
        with open(place, "w", encoding="utf-8") as handle:
            json.dump(numeric, handle)
        # THE RECEIVER REFUSES IT TOO. Asked of `_task`, not of the pattern:
        # the pattern is a constant and the refusal is a predicate, and this
        # case exists because those were once confused.
        with self.assertRaises(worker.TaskRefusal):
            worker._task(place)


def pathlib_worker():
    import pathlib
    return pathlib.Path(__file__).resolve().parents[3] / "worker"


class TheTaskIsHeldEverywhereItIsBelieved(OperatorCase):
    """W39358 review 2026-08-30T06:05:02Z [P1]: checking the schema a second
    time is not the same hold. `held_task` is one pure function applied at the
    first read, at the preflight and immediately before the copy."""

    def granted(self, task):
        return {"task": task, "policies": POLICIES,
                "worker_image_digest": IMAGE, "toolchain_digest": TOOLCHAIN,
                "runtime_profile_digest": PROFILE,
                "role_instructions_digest": ROLE, "record_binding": BINDING,
                "network": "baton-dogfood"}

    def test_a_task_changed_after_its_first_read_does_not_pass_preflight(self):
        for member, value in (("task_id", "../elsewhere"),
                              ("instructions", ""),
                              ("verification", []),
                              ("source_root", "somewhere-else")):
            with self.subTest(member=member):
                held = frozen_task(self.task())
                held[member] = value
                with self.assertRaises(OperatorRefusal):
                    dogfood_operator.preflight(**self.granted(held))

    def test_a_task_changed_after_preflight_is_not_the_task_copied(self):
        """The third application, immediately before the write, is what makes
        the interval between the second and the copy uninteresting."""
        held = frozen_task(self.task())
        dogfood_operator.preflight(**self.granted(held))
        held["verification"] = []
        with self.assertRaises(OperatorRefusal):
            dogfood_operator._copied_task(held, self.inputs)
        self.assertFalse(os.path.exists(os.path.join(self.inputs,
                                                     "task.json")))

    def test_one_function_answers_at_all_three_places(self):
        """A second spelling of the hold is a second chance to disagree."""
        for place in (dogfood_operator.frozen_task,
                      dogfood_operator.preflight,
                      dogfood_operator._copied_task):
            with self.subTest(place=place.__name__):
                self.assertIn("held_task", place.__code__.co_names)


class TheIdentityHoldIsAppliedTwice(OperatorCase):
    """`preflight` is where an operator learns before anything is staged; the
    composer applies the same hold again, which is the second party proving it
    rather than assuming the first did."""

    def test_the_composer_refuses_the_same_malformed_identities(self):
        staged = stage_source(self.source, self.inputs)
        with self.assertRaises(OperatorRefusal) as caught:
            input_manifest(
                work_ref=WORK_REF, staged=staged, created_at=NOW,
                manifest_id="input-w39358",
                assignment_contract="v12-assignment-1", human_contract=HUMAN,
                record_binding=dict(BINDING, path="/absolute/record"),
                role_instructions_digest=ROLE, runtime_profile_digest=PROFILE,
                toolchain_digest=TOOLCHAIN, worker_image_digest=IMAGE,
                policies=POLICIES)
        # THE FROZEN CONTRACT'S OWN NAME FOR THE RULE. Review
        # 2026-08-30T06:13:35Z [P1]: this asserted my handwritten
        # "repository-relative" prose, and the approximation behind it is
        # superseded by `validate_fragment(..., "relativePath")` -- the
        # definition's own owner. This case is mine and changed with the rule
        # it was asserting.
        self.assertIn("relativePath", str(caught.exception))

    def test_a_malformed_policy_container_refuses_at_the_composer_too(self):
        staged = stage_source(self.source, self.inputs)
        with self.assertRaises(OperatorRefusal):
            input_manifest(
                work_ref=WORK_REF, staged=staged, created_at=NOW,
                manifest_id="input-w39358",
                assignment_contract="v12-assignment-1", human_contract=HUMAN,
                record_binding=BINDING, role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE, toolchain_digest=TOOLCHAIN,
                worker_image_digest=IMAGE, policies=None)


class TheLocatorGrammarHasONEOwner(OperatorCase):
    """W39358 review 2026-08-30T06:13:35Z [P1]. A second approximation
    maintained in this tool is a second grammar with nothing comparing the
    two — the same rule the engine network operand is already under."""

    def test_the_frozen_definitions_are_what_refuses(self):
        """Asserted through the module rather than restated: a case that
        listed the rules itself would be a THIRD copy."""
        from baton_v12.contracts import validate_fragment

        for definition, value in (("opaqueId", "has space"),
                                  ("relativePath", "/absolute")):
            with self.subTest(definition=definition):
                with self.assertRaises(ContractRefusal):
                    validate_fragment(value, definition, what="probe")

    def test_a_root_the_frozen_grammar_refuses_never_reaches_staging(self):
        for wrong in ("has space", "r" * 161, ""):
            with self.subTest(root=wrong):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.preflight(
                        task=TASK, policies=POLICIES,
                        worker_image_digest=IMAGE,
                        toolchain_digest=TOOLCHAIN,
                        runtime_profile_digest=PROFILE,
                        role_instructions_digest=ROLE,
                        record_binding=dict(BINDING, root=wrong),
                        network="baton-dogfood")
                self.assertIn("opaqueId", str(caught.exception))
                self.assertFalse(os.path.exists(os.path.join(
                    self.inputs, dogfood_operator.SOURCE_TARGET)))

    def test_a_path_the_frozen_grammar_refuses_never_reaches_staging(self):
        for wrong in (".", "work\\records", "work/../escape", "p" * 513,
                      "work//records"):
            with self.subTest(path=wrong):
                with self.assertRaises(OperatorRefusal) as caught:
                    dogfood_operator.preflight(
                        task=TASK, policies=POLICIES,
                        worker_image_digest=IMAGE,
                        toolchain_digest=TOOLCHAIN,
                        runtime_profile_digest=PROFILE,
                        role_instructions_digest=ROLE,
                        record_binding=dict(BINDING, path=wrong),
                        network="baton-dogfood")
                self.assertIn("relativePath", str(caught.exception))

    def test_the_refusal_carries_the_contracts_own_sentence(self):
        """A class name would send an operator reading the operator's source
        instead of their own document."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(
                task=TASK, policies=POLICIES, worker_image_digest=IMAGE,
                toolchain_digest=TOOLCHAIN, runtime_profile_digest=PROFILE,
                role_instructions_digest=ROLE,
                record_binding=dict(BINDING, path="/absolute/record"),
                network="baton-dogfood")
        self.assertNotIn("ContractRefusal", str(caught.exception))
        self.assertIn("the record binding's path", str(caught.exception))

    def test_an_owner_defect_is_not_relabelled_as_bad_operator_input(self):
        """Only an owner's typed contract judgement says the supplied grant
        is wrong.  An unexpected failure is a defect at that owner and must
        not become an `OperatorRefusal` telling the human to edit its input."""
        for owner in ("_validate_fragment", "_engine_network"):
            with self.subTest(owner=owner):
                original = getattr(dogfood_operator, owner)

                def broken(*_arguments, **_keywords):
                    raise RuntimeError("the grammar owner failed")

                setattr(dogfood_operator, owner, broken)
                try:
                    with self.assertRaises(RuntimeError):
                        dogfood_operator.preflight(
                            task=TASK, policies=POLICIES,
                            worker_image_digest=IMAGE,
                            toolchain_digest=TOOLCHAIN,
                            runtime_profile_digest=PROFILE,
                            role_instructions_digest=ROLE,
                            record_binding=BINDING,
                            network="baton-dogfood")
                finally:
                    setattr(dogfood_operator, owner, original)

    def test_this_tool_keeps_no_second_locator_grammar(self):
        """`posixpath` was imported only to hand-roll the path rule, so the
        module no longer importing it is what makes the deletion deliberate
        rather than drift.

        ASKED OF THE MODULE, not of its text. The superseded rule is described
        in a comment on purpose — this record keeps the history of what was
        replaced — so a source-text search would find the word and report a
        grammar that is no longer there.
        """
        self.assertFalse(hasattr(dogfood_operator, "posixpath"))
        self.assertTrue(hasattr(dogfood_operator, "_validate_fragment"))


class AnOwnerDefectIsNotABadGrant(OperatorCase):
    """W39358 review 2026-08-30T06:20:54Z [P2].

    `OperatorRefusal` says a deployment was asked for something it does not
    do. An implementation defect inside a grammar owner is not that, and
    reporting it as one tells a human to edit a grant that is fine while
    hiding the boundary that actually failed.
    """

    def granted(self, **overrides):
        given = {"task": TASK, "policies": POLICIES,
                 "worker_image_digest": IMAGE, "toolchain_digest": TOOLCHAIN,
                 "runtime_profile_digest": PROFILE,
                 "role_instructions_digest": ROLE, "record_binding": BINDING,
                 "network": "baton-dogfood"}
        given.update(overrides)
        return given

    def broken(self, name):
        """Replace one grammar owner with a defect, for one case."""
        def raising(*arguments, **operands):
            raise RuntimeError("the owner is broken")

        held = getattr(dogfood_operator, name)
        setattr(dogfood_operator, name, raising)
        self.addCleanup(setattr, dogfood_operator, name, held)

    def test_a_network_owner_defect_propagates(self):
        self.broken("_engine_network")
        with self.assertRaises(RuntimeError):
            dogfood_operator.preflight(**self.granted())

    def test_a_locator_owner_defect_propagates(self):
        self.broken("_validate_fragment")
        with self.assertRaises(RuntimeError):
            dogfood_operator.preflight(**self.granted())

    def test_the_typed_outcome_is_still_a_collected_fault(self):
        """The other half: an invalid VALUE is still the operator's to fix."""
        with self.assertRaises(OperatorRefusal) as caught:
            dogfood_operator.preflight(**self.granted(network="two words"))
        self.assertIn("engine network name", str(caught.exception))


class EveryPostStartBranchEntersTheEnding(OperatorCase):
    """W39358 review 2026-08-30T06:35:56Z [P0].

    A returned unresolved document is not an ending. Once the manager has
    started a named runtime, transport loss and a worker answer without a
    disposition must enter the same quiescence/cleanup owner as the ordinary
    result rather than return around it.
    """

    class Adapter:

        def __init__(self):
            self.stops = []

        def stop(self, request):
            self.stops.append(dict(request))
            return {"runtime_id": request["runtime_id"], "ordered": True,
                    "state": "quiescent", "why": "stopped for the ending"}

        def observe(self, runtime_id):
            return {"runtime_id": runtime_id, "state": "quiescent",
                    "why": "the ending observed it"}

    def run_until_conversation(self, spoken):
        import baton_v12.worker_manager as manager
        from baton_v12.worker_manager import launch, worker_entry, workspaces

        adapter = self.Adapter()
        roots = {"inputs": self.inputs,
                 "workspace": os.path.join(self.home, "workspace"),
                 "outputs": os.path.join(self.home, "outputs")}
        given = {"manifest_digest": "sha256:" + "a" * 64,
                 "policy_digest": POLICIES["policy_digest"],
                 "outputs": [{"name": "proposal"}]}
        assignment = {"manifest_digest": "sha256:" + "b" * 64,
                      "assignment_ref": {"work_ref": dict(WORK_REF),
                                         "participant": "baton.claude",
                                         "generation": 1}}
        claimed = {"assignment": dict(assignment["assignment_ref"]),
                   "claim_event": 44, "decision": {"grant": "direct"}}
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                dogfood_operator, "frozen_task", return_value=dict(TASK)))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "preflight", return_value=True))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "_configured_group", return_value=object()))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "stage_source",
                return_value={"tree_digest": "sha256:" + "c" * 64}))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "input_manifest", return_value=given))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "assignment_manifest",
                return_value=assignment))
            patches.enter_context(mock.patch.object(
                dogfood_operator, "_copied_task", return_value="task.json"))
            patches.enter_context(mock.patch.object(
                workspaces, "assignment_workspace",
                return_value=roots))
            patches.enter_context(mock.patch.object(
                workspaces, "compose_input_root", return_value=None))
            patches.enter_context(mock.patch.object(
                launch, "materialize", return_value=object()))
            for name, answer in (
                    ("issue_offer", {}), ("accept_offer", {}),
                    ("record_attempt", {}), ("submit_claim", claimed),
                    ("activate_assignment", {}), ("retain_manifest", {}),
                    ("request_runtime_start", {"runtime_id": "runtime-1"})):
                patches.enter_context(mock.patch.object(
                    manager, name, return_value=answer))
            patches.enter_context(mock.patch.object(
                worker_entry, "converse", return_value=spoken))
            evidence = dogfood_operator.run_dogfood_task(
                engine="docker", run=lambda _argv: None,
                open_channel=lambda _argv: None, store=object(), port=object(),
                adapter_of=lambda **_operands: adapter,
                attempt_id="attempt-1", offer_id="offer-1",
                source=self.source, task_path=self.task(), storage=self.home,
                launch_home=self.home, credential_delivery=object(),
                image_digest=IMAGE, network="baton-dogfood",
                work_ref=WORK_REF, participant="baton.claude", generation=1,
                now=NOW, policies=POLICIES, record_binding=BINDING,
                assignment_contract="v12-assignment-1", human_contract=HUMAN,
                role_instructions_digest=ROLE,
                runtime_profile_digest=PROFILE,
                toolchain_digest=TOOLCHAIN, adapter_digest=IMAGE,
                adapter_name="oci", labels={"attempt": "attempt-1"},
                retention_policy_digest=POLICIES["retention_policy_digest"],
                bearer="one-use-bearer")
        return adapter, evidence

    def test_transport_and_disposition_failures_do_not_return_around_ending(
            self):
        for spoken in (
                {"ending": "lost", "why": "EOF", "answers": []},
                {"ending": "answered", "why": "clean",
                 "answers": [{"operation": "describe", "answer": {}}]}):
            with self.subTest(ending=spoken["ending"]):
                adapter, evidence = self.run_until_conversation(spoken)
                self.assertFalse(evidence["resolved"])
                self.assertEqual(len(adapter.stops), 1,
                                 "a started runtime returned around its ending")

    def test_an_empty_intake_receipt_still_authorizes_cleanup(self):
        """A committed receipt is the authorization even when it is empty.

        W39358 review 2026-08-30T06:44:13Z [P0] required every early custody
        ending to reach manager cleanup. Raising instead of returning closes
        the control-flow bypass only if the durable receipt is recorded in the
        operator evidence BEFORE its artifacts are interpreted.
        """
        import baton_v12.worker_manager as manager
        from baton_v12.worker_manager import worker_entry

        adapter = self.Adapter()
        evidence = {"conversation": None, "worker_disposition": None,
                    "cleanup": None, "resolved": False, "unresolved": []}
        spoken = {
            "ending": "answered", "why": "clean",
            "answers": [
                {"operation": "work",
                 "answer": {"disposition": "succeeded"}}]}
        with ExitStack() as patches:
            patches.enter_context(mock.patch.object(
                worker_entry, "converse", return_value=spoken))
            for name, answer in (
                    ("reconcile_runtime", {}), ("observe", {}),
                    ("request_freeze", {}),
                    ("request_intake", {"artifacts": []})):
                patches.enter_context(mock.patch.object(
                    manager, name, return_value=answer))
            cleanup = patches.enter_context(mock.patch.object(
                manager, "authorize_cleanup",
                return_value={"cleanup": "complete", "state": "absent"}))
            answered = dogfood_operator._after_start(
                object(), object(), adapter, evidence,
                engine="docker", open_channel=lambda _argv: None,
                attempt_id="attempt-1", runtime_id="runtime-1",
                roots={}, task=dict(TASK), source=self.source,
                retention_policy_digest=POLICIES[
                    "retention_policy_digest"], seconds=1)
        cleanup.assert_called_once()
        self.assertEqual(answered["cleanup"],
                         {"cleanup": "complete", "state": "absent"})
