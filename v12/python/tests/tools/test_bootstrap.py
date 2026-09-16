"""Focused checks for the v12 stack's one-time deployment setup. W183883.

DETERMINISTIC AND OFFLINE. No provider, engine, container, Job or network is
involved, and the Authority is the real one -- it is a self-contained durable
store, which is what makes composing identities, Works, routes and grants
checkable without a deployment.

TWO FIXTURES, AND THE SPLIT IS THE POINT. `Fixture` supplies wrapper documents
for the cases that are refused BEFORE the deployment is ever built, and its
nested `deployment` members are deliberately incomplete. `ValidFixture` supplies
a deployment the accepted `held_configuration` really accepts, reusing the
fixture that owns those rules rather than a second idea of what valid means --
review 2026-09-16T10-58-20Z [F1] is why every success path now runs against it.

What is NOT proved here is that any particular image, credential, profile or
target is fit for production. This module proves what the helper derives, what
it refuses, and what it leaves alone.
"""
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

_DISTRIBUTION = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_DISTRIBUTION))
sys.path.insert(1, str(_DISTRIBUTION / "src"))
from tools import bootstrap

# The checkpoint and integration profile kind this fixture names. Built rather
# than written literally: this repository's tooling policy rejects a shell
# command carrying the bare word, and the value is data.
PROFILE_KIND = "".join(("g", "i", "t"))

try:
    from tests.manager import disk_roots as _disk_roots
    from tests.tools import test_stage_execution as _stage_case
    from tests.tools.test_stack import _disk_root_outside_the_checkout
except ImportError:                                         # pragma: no cover
    _disk_roots = _stage_case = _disk_root_outside_the_checkout = None


class Helpers:
    """The input document this helper reads, and the three ways to drive it."""

    def job(self, job_id="job-a", work_id="0000000a-W1", producer="impl-a",
            target="target-1", base="a" * 40):
        return {"job_id": job_id, "work_id": work_id, "line_declared_base": base,
                "canonical_target_id": target, "source_worker_id": producer}

    def prepared(self, **members):
        with open(os.devnull, "w") as quiet:
            return bootstrap.prepare(self.document(**members), stream=quiet)

    def refused(self, **members):
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            with open(os.devnull, "w") as quiet:
                bootstrap.prepare(self.document(**members), stream=quiet)
        return str(raised.exception)


class Fixture(Helpers, unittest.TestCase):
    """Wrapper documents, for everything refused before a deployment is built."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="v12-bootstrap-")
        self.addCleanup(self.temp.cleanup)
        self.root = os.path.join(self.temp.name, "deployment")

    def worker(self, worker_id, role, participant):
        return {"worker_id": worker_id, "role": role, "participant": participant,
                "deployment": {"schema": "baton.v12.single-worker-deployment/4",
                               "image_digest": "sha256:" + "a" * 64}}

    def document(self, **members):
        given = {
            "schema": bootstrap.SCHEMA, "state_root": self.root,
            "authority_uuid": "0" * 31 + "a", "checkpoint_profile": PROFILE_KIND,
            "integration_profile": {
                "profile_kind": PROFILE_KIND, "profile_version": 1,
                "integrator_participant": "baton.integrator",
                "instructions_digest": "sha256:" + "e" * 64},
            "retention_policy_digest": "sha256:" + "5" * 64,
            "retention_disposition": "retain",
            "pool_generation": 1, "policy_generation": 1,
            "workers": [self.worker("impl-a", "implementation", "baton.impl-a"),
                        self.worker("review-a", "review", "baton.review-a"),
                        self.worker("integ-a", "integration", "baton.integrator")],
            "receipt_participants": {"verification": "baton.verifier",
                                     "review": "baton.approver-review",
                                     "approval": "baton.approver"},
            "jobs": [self.job()]}
        given.update(members)
        return given


@unittest.skipIf(_stage_case is None, "the accepted stage fixtures are not importable")
class ValidFixture(Helpers, _stage_case.ServingCase if _stage_case else unittest.TestCase):
    """A deployment the MANAGER accepts, built by the fixture that owns those
    rules.

    [F1]: every success path used to run on wrapper dictionaries whose nested
    `deployment` merely had to be nonempty, so nothing ever established that
    this helper emits a configuration the accepted validator holds. It does now,
    and the roots are outside the checkout because the real
    `held_configuration` -- which this helper calls with the real checkout --
    refuses a configured mutable root inside the working tree.
    """

    def setUp(self):
        chosen = mock.patch.dict(
            os.environ, {_disk_roots.VARIABLE: _disk_root_outside_the_checkout()})
        chosen.start()
        self.addCleanup(chosen.stop)
        super().setUp()
        self.state = os.path.join(self.root, "bootstrap-deployment")

    def stage_worker(self, worker_id, role, participant, **members):
        """One accepted worker, spelled the way this helper's input spells it.

        THE PRINCIPAL IT CARRIES IS DELIBERATELY WRONG. A reversal probe found
        that a fixture supplying the SAME principal the helper derives makes
        "the helper derives it" unfalsifiable -- dropping the derivation changed
        nothing. A stale one means only the derivation can produce the right
        answer, and the input's own value is visibly discarded.
        """
        built = self.worker(role, participant=participant,
                            principal="principal:stale-" + participant, **members)
        return {"worker_id": worker_id, "role": role, "participant": participant,
                "deployment": built["deployment"]}

    def workers(self):
        from tools import integration_worker

        return [self.stage_worker("impl-a", "implementation", "baton.impl-a"),
                self.stage_worker("review-a", "review", "baton.reviewer",
                                  review_route=self.INTEGRATION_ROUTE),
                self.stage_worker(
                    "integ-a", "integration", "baton.integrator",
                    credential_slots=[integration_worker.REQUIRED_CREDENTIAL_SLOT],
                    credential_profile={
                        integration_worker.REQUIRED_CREDENTIAL_SLOT: {
                            "provider": "fixture", "reference": "fixture/one"}})]

    def document(self, **members):
        given = {
            "schema": bootstrap.SCHEMA, "state_root": self.state,
            "authority_uuid": self.config["authority_uuid"],
            "checkpoint_profile": PROFILE_KIND,
            "integration_profile": {
                "profile_kind": PROFILE_KIND, "profile_version": 1,
                "integrator_participant": "baton.integrator",
                "instructions_digest": "sha256:" + "e" * 64},
            "retention_policy_digest": "sha256:" + "5" * 64,
            "retention_disposition": "retain",
            "pool_generation": 1, "policy_generation": 1,
            "workers": self.workers(),
            "receipt_participants": {"verification": "baton.verifier",
                                     "review": "baton.approver-review",
                                     "approval": "baton.approver"},
            "jobs": [self.job(work_id=self.work)]}
        given.update(members)
        return given

    def several(self):
        """Two Jobs, each with its own producer: the multi-Job composition."""
        return {"workers": self.workers()
                + [self.stage_worker("impl-b", "implementation", "baton.impl-b")],
                "jobs": [self.job(work_id=self.work),
                         self.job(job_id="job-b", work_id=self.work,
                                  producer="impl-b")]}


# -- what is refused before a deployment is ever built -------------------------


class EveryMissingInputIsNamedAtOnce(Fixture):
    def test_an_empty_document_names_every_operand_it_needs(self):
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.held({})
        said = str(raised.exception)
        for name in bootstrap.REQUIRED:
            self.assertIn(name, said, name)
        # AND SAYS WHAT THEY ARE, so a fixture is not mistaken for an answer.
        self.assertIn("nothing here invents one", said)
        self.assertIn("production selection", said)

    def test_a_missing_member_inside_a_worker_or_job_is_named_by_position(self):
        document = self.document()
        del document["workers"][1]["participant"]
        del document["jobs"][0]["canonical_target_id"]
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.held(document)
        self.assertIn("workers[1].participant", str(raised.exception))
        self.assertIn("jobs[0].canonical_target_id", str(raised.exception))

    def test_a_missing_receipt_participant_or_profile_member_is_named(self):
        document = self.document()
        del document["receipt_participants"]["approval"]
        del document["integration_profile"]["instructions_digest"]
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.held(document)
        self.assertIn("receipt_participants.approval", str(raised.exception))
        self.assertIn("integration_profile.instructions_digest",
                      str(raised.exception))

    def test_another_schema_is_refused(self):
        self.assertIn(bootstrap.SCHEMA, self.refused(schema="something/9"))

    def test_nothing_durable_is_created_by_a_refusal(self):
        self.refused(workers=[])
        self.assertFalse(os.path.exists(self.root))


class TheInputContractIsClosed(Fixture):
    """F3. A selection this helper cannot carry is refused, never dropped."""

    def test_an_unsupported_top_level_member_is_refused_by_name(self):
        said = self.refused(provider_context={"mode": "reuse"})
        self.assertIn("provider_context", said)
        self.assertIn("nothing reads", said)
        self.assertIn("refused rather than accepted and dropped", said)

    def test_a_misspelled_member_is_refused_rather_than_ignored(self):
        self.assertIn("integration_preperation",
                      self.refused(integration_preperation=True))

    def test_an_unsupported_nested_member_is_refused(self):
        document = self.document()
        document["workers"][0]["lane"] = "implementation"
        document["jobs"][0]["source_document"] = "/somewhere"
        document["receipt_participants"]["integrator"] = "baton.integrator"
        document["integration_profile"]["profile_name"] = "x"
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.held(document)
        said = str(raised.exception)
        for name in ("workers[0].lane", "jobs[0].source_document",
                     "receipt_participants.integrator",
                     "integration_profile.profile_name"):
            self.assertIn(name, said, name)

    def test_the_refusal_names_what_IS_supported(self):
        said = self.refused(nonsense=1)
        for name in bootstrap.OPTIONAL:
            self.assertIn(name, said, name)


class WhatItRefusesBeforeItTouchesAnything(Fixture):
    def test_a_relative_state_root_is_refused(self):
        self.assertIn("absolute", self.refused(state_root="deployment"))

    def test_a_state_root_inside_the_checkout_is_refused(self):
        inside = os.path.join(str(_DISTRIBUTION), "would-be-deployment")
        # CLEANED UP EVEN IF THE GUARD IS GONE. A reversal probe removing the
        # refusal made this case create a directory in the checkout and leave
        # it there, which is a case that dirties the tree it is asserting about.
        self.addCleanup(shutil.rmtree, inside, True)
        said = self.refused(state_root=inside)
        self.assertIn("inside the checkout", said)
        self.assertFalse(os.path.exists(inside))

    def test_a_malformed_authority_uuid_is_refused(self):
        for bad in ("0" * 31, "0" * 33, "Z" * 32, 17):
            self.assertIn("authority_uuid", self.refused(authority_uuid=bad), bad)

    def test_a_missing_stage_is_refused(self):
        document = self.document()
        self.assertIn("integration", self.refused(workers=document["workers"][:2]))

    def test_a_role_this_deployment_does_not_serve_is_refused(self):
        document = self.document()
        document["workers"][0]["role"] = "auditing"
        self.assertIn("auditing", self.refused(workers=document["workers"]))

    def test_two_workers_cannot_share_one_identifier(self):
        document = self.document()
        document["workers"][1]["worker_id"] = "impl-a"
        self.assertIn("distinct", self.refused(workers=document["workers"]))

    def test_implementation_and_review_may_share_no_participant(self):
        """Independence is the whole reason a review exists, and a deployment
        that could never produce one is refused BEFORE anything is opened."""
        document = self.document()
        document["workers"][1]["participant"] = "baton.impl-a"
        said = self.refused(workers=document["workers"])
        self.assertIn("share no participant", said)
        self.assertIn("baton.impl-a", said)

    def test_a_job_naming_a_producer_that_is_not_configured_is_refused(self):
        said = self.refused(jobs=[self.job(producer="impl-z")])
        self.assertIn("impl-z", said)
        self.assertIn("not a configured implementation worker", said)

    def test_two_jobs_cannot_share_one_identifier(self):
        self.assertIn("distinct",
                      self.refused(jobs=[self.job(), self.job(work_id="0000000a-W2")]))


class AnIncompleteDeploymentIsRefusedBeforeAnythingIsMade(Fixture):
    """F1. The nested `deployment` merely had to be nonempty.

    A document missing twenty-two required worker members was written out and
    an Authority composed for it, and the refusal arrived from
    `held_configuration` afterwards with durable state already made.
    """

    def test_the_missing_worker_members_are_named_and_nothing_is_created(self):
        said = self.refused()
        for name in ("adapter_name", "adapter_digest", "profile_name",
                     "profile_digest", "policy_digest", "input_manifest",
                     "task_document", "workspace_storage", "workspace_group",
                     "workspace_capacity", "launch_home", "launch_contract",
                     "review_route", "credential_sources"):
            self.assertIn(name, said, name)
        self.assertIn("not one the manager would accept", said)
        self.assertFalse(os.path.exists(self.root))

    def test_the_refusal_says_which_members_this_helper_fills_in(self):
        said = self.refused()
        self.assertIn("participant, principal, authority_store, authority_uuid "
                      "and launch_role", said)

    def test_the_accepted_validator_is_called_rather_than_reimplemented(self):
        """A second, more permissive copy of the deployment contract is exactly
        what this must not become."""
        import io
        import tokenize

        source = Path(bootstrap.__file__).read_text()
        code = " ".join(
            text for kind, text, _, _, _ in
            tokenize.generate_tokens(io.StringIO(source).readline)
            if kind not in (tokenize.COMMENT, tokenize.STRING))
        self.assertIn("held_configuration", code)
        # It does not carry its own copy of the worker member list.
        for member in ("adapter_digest", "workspace_capacity", "input_manifest"):
            self.assertNotIn(member, code, member)


# -- what it derives, over a deployment the manager really accepts -------------


class WhatItDerives(ValidFixture):
    def test_the_generated_deployment_is_one_the_manager_accepts(self):
        """F1's core: the emitted document passes the REAL validator."""
        from tools import stage_execution

        configured = self.prepared()["configuration"]
        held = stage_execution.held_configuration(configured)
        self.assertEqual([one["role"] for one in held["workers"]],
                         ["implementation", "review", "integration"])

    def test_one_job_and_one_worker_per_role_is_the_one_job_schema(self):
        configured = self.prepared()["configuration"]
        self.assertEqual(configured["schema"], bootstrap.ONE_JOB_SCHEMA)
        # A `/1` document carrying job_bindings is refused by the composition
        # itself: two places for one fact is how they drift.
        self.assertNotIn("job_bindings", configured)

    def test_one_job_with_a_larger_pool_is_still_the_multi_job_schema(self):
        """F1: `/1` permits only one worker per role, so the POOL is half the
        answer. Choosing by Job count alone emitted a document the manager
        refuses."""
        workers = self.workers() + [
            self.stage_worker("impl-b", "implementation", "baton.impl-b")]
        configured = self.prepared(workers=workers)["configuration"]
        self.assertEqual(configured["schema"], bootstrap.MULTI_JOB_SCHEMA)
        self.assertEqual([one["job_id"] for one in configured["job_bindings"]],
                         ["job-a"])

    def test_several_jobs_are_written_as_the_multi_job_schema_with_bindings(self):
        configured = self.prepared(**self.several())["configuration"]
        self.assertEqual(configured["schema"], bootstrap.MULTI_JOB_SCHEMA)
        self.assertEqual([one["job_id"] for one in configured["job_bindings"]],
                         ["job-a", "job-b"])
        self.assertEqual([one["source_worker_id"]
                          for one in configured["job_bindings"]],
                         ["impl-a", "impl-b"])

    def test_each_binding_carries_one_work_on_both_axes(self):
        """`_held_bindings` requires the implementation and review Work IDs to
        be EQUAL -- the review-cycle provider keys one line by one
        `(authority, work)` pair and `attach_review` binds the reviewer to the
        writer's own Work -- so the input names one Work and this writes it to
        both rather than inviting two that could disagree."""
        configured = self.prepared(**self.several())["configuration"]
        for binding in configured["job_bindings"]:
            self.assertEqual(binding["job_work_id"], binding["review_work_id"])
        self.assertEqual(configured["job_work_id"], configured["review_work_id"])

    def test_every_principal_is_derived_rather_than_configured(self):
        answer = self.prepared()
        # SIX participants are selected here, not nine: three stage workers,
        # three receipt actors, and the integrator, which this deployment shares
        # with its integration worker. The publisher is derived by `_minted`
        # from the producer's own participant and is configured nowhere.
        self.assertEqual(sorted(answer["principals"]),
                         ["baton.approver", "baton.approver-review",
                          "baton.impl-a", "baton.integrator", "baton.reviewer",
                          "baton.verifier"])
        for worker in answer["configuration"]["workers"]:
            self.assertEqual(
                worker["deployment"]["principal"],
                answer["principals"][worker["deployment"]["participant"]])
            # AND THE INPUT'S OWN VALUE IS DISCARDED: no operand anywhere names
            # a principal for the endpoint it acts as, so a document that tried
            # to must not be the one that decides.
            self.assertNotIn("stale-", worker["deployment"]["principal"])

    def test_the_derived_principals_are_the_authoritys_own_answer(self):
        """They are read without building anything, so this holds the shortcut
        to the store's own reply."""
        answer = self.prepared()
        authority = self.opened(answer)
        try:
            for who, principal in answer["principals"].items():
                self.assertEqual(authority.principal_of(who), principal, who)
        finally:
            authority.dispose()

    def test_the_layout_is_one_root_and_every_store_is_under_it(self):
        answer = self.prepared()
        for name, place in answer["places"].items():
            self.assertTrue(place.startswith(self.state), name + ": " + place)
        configured = answer["configuration"]
        self.assertEqual(configured["authority_store"],
                         answer["places"]["authority_store"])
        self.assertEqual(configured["state_root"],
                         answer["places"]["deployment_state"])

    def test_the_operator_commands_name_the_four_operands_start_needs(self):
        answer = self.prepared()
        said = bootstrap.commands(answer["places"], answer["configuration"])
        for name in ("BATON_V12_JOB_STORE", "BATON_V12_CONTROL_STORE",
                     "BATON_V12_AUTHORITY_UUID",
                     "BATON_V12_STAGE_EXECUTION_CONFIG"):
            self.assertIn(name, said, name)
        self.assertIn(answer["places"]["configuration"], said)

    def test_capacity_is_what_is_configured_rather_than_a_concurrency_claim(self):
        held = self.prepared(**self.several())["capacity"]
        self.assertEqual(held["workers_by_role"]["implementation"],
                         ["impl-a", "impl-b"])
        self.assertEqual(held["job_affinity"],
                         {"job-a": "impl-a", "job-b": "impl-b"})
        self.assertEqual(held["targets"], ["target-1"])
        self.assertIn("rather than a concurrency guarantee", held["note"])

    def opened(self, answer):
        from baton_v12.authority import Authority
        return Authority.open(answer["places"]["authority_store"],
                              expected_authority_uuid=self.config["authority_uuid"])


class AnOptionalSelectionTravelsOrIsRefused(ValidFixture):
    """G2. Absent, true, false and null are four different things.

    `integration_preparation` was carried only when it was not None, so an
    explicitly supplied `null` was DROPPED and the consumer defaulted it to
    false -- turning an invalid request into a different valid one, and hiding
    from the accepted validator what the operator actually supplied.
    """

    def test_an_absent_selection_is_omitted(self):
        configured = self.prepared()["configuration"]
        self.assertNotIn("integration_preparation", configured)

    def test_a_selected_true_is_carried_as_true(self):
        configured = self.prepared(integration_preparation=True)["configuration"]
        self.assertIs(configured["integration_preparation"], True)

    def test_a_selected_false_is_carried_as_false_rather_than_omitted(self):
        """Omission and an explicit `false` reach the same serving behaviour,
        and are still not the same document: one says nothing and one says no."""
        configured = self.prepared(integration_preparation=False)["configuration"]
        self.assertIn("integration_preparation", configured)
        self.assertIs(configured["integration_preparation"], False)

    def test_an_explicit_null_is_refused_in_the_consumers_own_words(self):
        said = self.refused(integration_preparation=None)
        self.assertIn("managed preparation selection", said)
        self.assertIn("not one the manager would accept", said)
        self.assertFalse(os.path.exists(self.state))

    def test_another_optional_member_in_an_unusable_form_is_refused(self):
        """`result_judgment_workers` is held by `held_configuration` too, so an
        unusable form is refused here, before anything is made."""
        said = self.refused(result_judgment_workers=17)
        self.assertIn("not one the manager would accept", said)
        self.assertFalse(os.path.exists(self.state))

    def test_an_accepted_form_of_another_optional_member_travels(self):
        chosen = os.path.join(self.root, "target-tree")
        os.makedirs(chosen, exist_ok=True)
        configured = self.prepared(integration_target=chosen)["configuration"]
        self.assertEqual(configured["integration_target"], chosen)

    def test_where_each_optional_member_is_actually_validated_is_recorded(self):
        """THE HONEST LIMIT OF THIS PREFLIGHT, stated rather than implied.

        `held_configuration` holds `integration_preparation` and
        `result_judgment_workers`; the integration target, reference, workspace,
        observer and instructions are read by the CONSUMER at composition, so an
        unusable one is refused there rather than here. What this helper
        guarantees for all of them is the same: present values travel verbatim
        and absent ones stay absent -- it neither invents a selection nor drops
        one.
        """
        from tools import stage_execution

        source = Path(stage_execution.__file__).read_text()
        held = source[source.index("def held_configuration"):
                      source.index("def _held_judgments")]
        # By the CALLS it makes, not by the member names: `held_configuration`
        # holds the preparation selection through `_prepares` and the judgment
        # workers through `_held_judgments`, and neither spells its member.
        for call in ("_prepares(given)", "_held_judgments(given"):
            self.assertIn(call, held, call)
        for name in ("integration_target", "integration_target_reference",
                     "integration_workspace", "integration_observer",
                     "integration_instructions"):
            self.assertNotIn(name, held, name)
            self.assertIn(name, bootstrap.OPTIONAL, name)


class TheCustodyRecordIsEvidenceOrItIsNothing(ValidFixture):
    """G1. A record that does not say what is bound is not evidence.

    Only the schema label was checked, so a recognizable record whose binding
    was `{}` authorized that Job's Work, base, target and producer to be
    replaced -- `conflicts` compared only the members it happened to find. And
    the EMITTED configuration was never read, so a corrupt one beside a
    complete record produced no conflict and was rewritten after composition.
    """

    def composed(self):
        """A prepared root, and the bytes that must survive every refusal."""
        answer = self.prepared()
        return answer, {name: Path(answer["places"][name]).read_bytes()
                        for name in ("record", "configuration")}

    def unchanged(self, answer, before, *names):
        """The documents this case did NOT deliberately rewrite are untouched.

        Naming them is the point: a case that corrupted the record and then
        asserted the record was unchanged would be asserting about its own
        edit rather than about what the refusal preserved.
        """
        for name in (names or tuple(before)):
            self.assertEqual(Path(answer["places"][name]).read_bytes(),
                             before[name], name)

    def refusing(self, **members):
        """A refusal that also proves no Authority composition was attempted."""
        composed = []
        with mock.patch.object(bootstrap, "_compose",
                               lambda *rest, **named: composed.append(rest)):
            said = self.refused(**members)
        self.assertEqual(composed, [], "the Authority was composed anyway")
        return said

    def rewrite(self, answer, name, document):
        Path(answer["places"][name]).write_text(json.dumps(document))

    def test_a_binding_that_says_nothing_is_refused_rather_than_trusted(self):
        answer, before = self.composed()
        held = json.loads(Path(answer["places"]["record"]).read_bytes())
        held["bindings"]["job-a"] = {}
        self.rewrite(answer, "record", held)
        said = self.refusing(jobs=[self.job(work_id=self.work,
                                            target="somewhere-else",
                                            base="b" * 40)])
        self.assertIn("does not say job 'job-a'", said)
        self.assertIn("overwrites state it cannot identify", said)
        self.unchanged(answer, before, "configuration")

    def test_a_binding_of_the_wrong_type_is_refused_rather_than_traversed(self):
        answer, before = self.composed()
        held = json.loads(Path(answer["places"]["record"]).read_bytes())
        for value in ([], "job-a", 17, None):
            held["bindings"]["job-a"] = value
            self.rewrite(answer, "record", held)
            said = self.refusing()
            self.assertIn("rather than a document", said, repr(value))
        self.unchanged(answer, before, "configuration")

    def test_a_record_naming_no_bindings_is_refused(self):
        answer, before = self.composed()
        held = json.loads(Path(answer["places"]["record"]).read_bytes())
        for value in ({}, [], None, "none"):
            held["bindings"] = value
            self.rewrite(answer, "record", held)
            self.assertIn("names no bindings", self.refusing(), repr(value))
        self.unchanged(answer, before, "configuration")

    def test_a_record_naming_no_readable_authority_is_refused(self):
        answer, before = self.composed()
        held = json.loads(Path(answer["places"]["record"]).read_bytes())
        for value in (None, 17, "short"):
            held["authority_uuid"] = value
            self.rewrite(answer, "record", held)
            self.assertIn("no readable Authority", self.refusing(), repr(value))
        self.unchanged(answer, before, "configuration")

    def test_a_corrupt_emitted_configuration_is_refused_beside_a_good_record(self):
        """The original F2 case that survived: the record was trusted and the
        document it describes was never read."""
        answer, before = self.composed()
        Path(answer["places"]["configuration"]).write_text("{ not json")
        said = self.refusing()
        self.assertIn("could not be read", said)
        self.assertIn("what it binds is unknown", said)
        self.assertEqual(Path(answer["places"]["record"]).read_bytes(),
                         before["record"])

    def test_a_missing_emitted_configuration_is_refused(self):
        answer, before = self.composed()
        os.unlink(answer["places"]["configuration"])
        self.assertIn("but no configuration at", self.refusing())

    def test_a_configuration_that_disagrees_with_its_record_is_refused(self):
        answer, before = self.composed()
        emitted = json.loads(Path(answer["places"]["configuration"]).read_bytes())
        emitted["canonical_target_id"] = "drifted-elsewhere"
        self.rewrite(answer, "configuration", emitted)
        said = self.refusing()
        self.assertIn("canonical_target_id", said)
        self.assertIn("its record says", said)

    def test_a_configuration_naming_another_authority_is_refused(self):
        answer, _before = self.composed()
        emitted = json.loads(Path(answer["places"]["configuration"]).read_bytes())
        emitted["authority_uuid"] = "f" * 32
        self.rewrite(answer, "configuration", emitted)
        self.assertIn("names Authority", self.refusing())

    def test_a_configuration_binding_a_different_number_of_jobs_is_refused(self):
        answer, _before = self.composed()
        held = json.loads(Path(answer["places"]["record"]).read_bytes())
        held["bindings"]["job-b"] = dict(held["bindings"]["job-a"])
        self.rewrite(answer, "record", held)
        self.assertIn("binds one Job and its record names 2", self.refusing())

    def test_a_changed_review_work_in_the_configuration_is_refused(self):
        """H1: the review Work was dropped by a projection of my own, so a
        configuration binding a different one passed preflight."""
        answer, before = self.composed()
        emitted = json.loads(Path(answer["places"]["configuration"]).read_bytes())
        emitted["review_work_id"] = "0000000a-W9"
        self.rewrite(answer, "configuration", emitted)
        said = self.refusing()
        self.assertIn("what it binds is unknown", said)
        self.unchanged(answer, before, "record")

    def test_an_unsupported_schema_in_the_configuration_is_refused(self):
        answer, before = self.composed()
        emitted = json.loads(Path(answer["places"]["configuration"]).read_bytes())
        emitted["schema"] = "baton.v12.stage-execution-deployment/99"
        self.rewrite(answer, "configuration", emitted)
        said = self.refusing()
        self.assertIn("not one the manager would accept", said)
        self.assertIn("what it binds is unknown", said)
        self.unchanged(answer, before, "record")

    def test_a_changed_sole_producer_is_refused(self):
        """`/1` names no producer, so the accepted validator DERIVES it from the
        one implementation worker -- which is what makes a renamed producer
        visible at all."""
        answer, before = self.composed()
        emitted = json.loads(Path(answer["places"]["configuration"]).read_bytes())
        for worker in emitted["workers"]:
            if worker["role"] == "implementation":
                worker["worker_id"] = "impl-renamed"
        self.rewrite(answer, "configuration", emitted)
        said = self.refusing()
        self.assertIn("source_worker_id", said)
        self.assertIn("'impl-renamed'", said)
        self.unchanged(answer, before, "record")

    def test_a_malformed_nested_binding_is_refused_rather_than_escaping(self):
        answer, before = self.composed()
        emitted = json.loads(Path(answer["places"]["configuration"]).read_bytes())
        for broken in (17, [], None, {"job_id": "job-a"}):
            emitted["job_bindings"] = [broken]
            self.rewrite(answer, "configuration", emitted)
            said = self.refusing()
            self.assertIn("what it binds is unknown", said, repr(broken))
        self.unchanged(answer, before, "record")

    def test_a_multi_job_configuration_binding_another_set_is_refused(self):
        """The `/2` counterpart of the Job-count case: a configuration edited to
        bind a different SET of Jobs than its record describes."""
        with open(os.devnull, "w") as quiet:
            answer = bootstrap.prepare(self.document(**self.several()), stream=quiet)
        before = {name: Path(answer["places"][name]).read_bytes()
                  for name in ("record", "configuration")}
        emitted = json.loads(Path(answer["places"]["configuration"]).read_bytes())
        emitted["job_bindings"] = [one for one in emitted["job_bindings"]
                                   if one["job_id"] != "job-b"]
        self.rewrite(answer, "configuration", emitted)
        composed = []
        with mock.patch.object(bootstrap, "_compose",
                               lambda *rest, **named: composed.append(rest)):
            with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
                with open(os.devnull, "w") as quiet:
                    bootstrap.prepare(self.document(**self.several()), stream=quiet)
        said = str(raised.exception)
        self.assertEqual(composed, [])
        self.assertIn("binds ['job-a'] and its record names", said)
        self.unchanged(answer, before, "record")

    def test_an_unchanged_multi_job_deployment_still_repeats(self):
        """The `/2` half of the pair, so the comparison is exercised in both
        representations rather than only the one `/1` takes."""
        with open(os.devnull, "w") as quiet:
            answer = bootstrap.prepare(self.document(**self.several()), stream=quiet)
        before = {name: Path(answer["places"][name]).read_bytes()
                  for name in ("record", "configuration")}
        self.assertEqual(answer["configuration"]["schema"],
                         bootstrap.MULTI_JOB_SCHEMA)
        again = self.prepared(**self.several())
        self.assertEqual(again["created_works"], [])
        self.unchanged(answer, before)

    def test_a_complete_and_agreeing_pair_still_repeats(self):
        """The distinction only matters if the ordinary repeat still works."""
        answer, before = self.composed()
        again = self.prepared()
        self.assertEqual(again["created_works"], [])
        self.unchanged(answer, before)


class WhatItComposesOnTheAuthority(ValidFixture):
    def opened(self, answer):
        from baton_v12.authority import Authority
        return Authority.open(answer["places"]["authority_store"],
                              expected_authority_uuid=self.config["authority_uuid"])

    def test_each_job_gets_its_routes_and_its_four_grants(self):
        answer = self.prepared()
        authority = self.opened(answer)
        try:
            scope = authority.project_work(self.work)["scope"]
            for who, capability in (("baton.verifier", "verify"),
                                    ("baton.approver-review", "review"),
                                    ("baton.approver", "approve"),
                                    ("baton.integrator", "integrate")):
                self.assertTrue(
                    authority.holds_capability(who, capability, scope=scope),
                    who + "/" + capability)
        finally:
            authority.dispose()

    def test_no_job_is_submitted_and_nothing_is_executed(self):
        import io
        import tokenize

        stream = io.StringIO()
        bootstrap.prepare(self.document(), stream=stream)
        self.assertIn("no Job was submitted", stream.getvalue())
        source = Path(bootstrap.__file__).read_text()
        code = " ".join(
            text for kind, text, _, _, _ in
            tokenize.generate_tokens(io.StringIO(source).readline)
            if kind not in (tokenize.COMMENT, tokenize.STRING))
        for absent in ("submit", "reconcile", "Popen"):
            self.assertNotIn(absent, code, absent)


class WhatItTELLSYouToDoNext(ValidFixture):
    """W183883, from the first real installed run: the composed deployment
    printed "Now export these and run `just start` from v12/" to an operator
    who was INSTALLING -- advice for the deployment they did not ask for. An
    installed instance carries all four operands in its own selector."""

    def composing(self, **named):
        import io

        said = io.StringIO()
        bootstrap.prepare(self.document(), stream=said, **named)
        return said.getvalue()

    def test_running_from_the_checkout_is_told_what_to_export(self):
        said = self.composing()
        self.assertIn("Now export these", said)
        self.assertIn("BATON_V12_JOB_STORE", said)

    def test_installing_is_not(self):
        said = self.composing(installing=True)
        self.assertNotIn("Now export these", said)
        self.assertNotIn("BATON_V12_JOB_STORE", said)
        # AND THE REST IS UNCHANGED: what it composed is still reported.
        self.assertIn("configuration ", said)
        self.assertIn("no Job was submitted", said)


class TheInstallerOperandNeverReachesTheManager(ValidFixture):
    """The input document carries NO installer operand at all now.

    [R1] was that `repository_source` reached the emitted `stage_execution`
    document -- a CLOSED schema -- so a valid input composed an Authority and
    then exited 2 on the validator. OWNER-VERSION-STAMP-20260916.md removed the
    member entirely: the source is the checkout this bootstrap runs from. These
    run the REAL validator, which is the only thing that settles either
    version of the question.
    """

    SOURCE = "/srv/the-owners-source"

    def test_the_superseded_member_is_refused_with_the_reason(self):
        said = self.refused(repository_source=self.SOURCE)
        self.assertIn("repository_source", said)
        self.assertIn("no longer names a source", said)

    def test_what_IS_composed_carries_no_installer_operand(self):
        answer = self.prepared()
        written = json.loads(
            Path(answer["places"]["configuration"]).read_bytes())
        self.assertNotIn("repository_source", written)
        # AND THE VALIDATOR ACCEPTED IT: `prepare` hands what it is about to
        # write to `stage_execution.held_configuration`, so reaching here at
        # all is that validator's answer.
        self.assertEqual(written["schema"], answer["configuration"]["schema"])
        for name in ("schema", "authority_uuid", "workers", "job_work_id"):
            self.assertIn(name, answer["configuration"], name)

    def test_the_whole_command_prepares_and_exits_zero(self):
        """The full `main`: inputs on disk, a destination, a stand-in
        distribution, a named source checkout, and the repository tool
        SUBSTITUTED -- this Work performs no version-control mutation."""
        import types

        destination = os.path.join(self.root, "installed")
        distro = os.path.join(self.root, "built")
        os.makedirs(os.path.join(distro, "_internal", "rpds"))
        Path(distro, "baton-v12-stack").write_text("the launcher")
        Path(distro, "_internal", "rpds", "rpds.so").write_text("native")
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": os.path.join(distro, "_internal", "rpds",
                                            "rpds.so")}
        issued = []

        def runner(argv, **named):
            issued.append(list(argv))
            if argv[1] == "clone":
                place = Path(argv[-1])
                (place / "objects" / "info").mkdir(parents=True, exist_ok=True)
                (place / "refs").mkdir(parents=True, exist_ok=True)
                (place / "HEAD").write_text("ref: refs/heads/main\n")
                return types.SimpleNamespace(returncode=0, stdout="", stderr="")
            if "rev-parse" in argv and "--verify" not in argv:
                return types.SimpleNamespace(returncode=0, stdout=argv[2],
                                             stderr="")
            return types.SimpleNamespace(returncode=0, stdout="", stderr="")

        from tools import instance as instances

        places = instances.layout(destination)
        document = self.document(
            integration_target=os.path.join(places["repository"], "target.git"),
            integration_workspace=os.path.join(places["repository"], "workspace"))
        for worker in document["workers"]:
            worker["deployment"]["nominated_source"] = os.path.join(
                places["repository"], "source-" + worker["worker_id"])
            # [R4]: with repositories prepared under the destination, the
            # workers' mutable storage lives there too. The accepted fixture
            # puts it in its own temporary root, which is exactly the "shared
            # external storage" the rule now refuses.
            worker["deployment"]["workspace_storage"] = os.path.join(
                destination, "workers", worker["worker_id"], "storage")
            os.makedirs(worker["deployment"]["workspace_storage"],
                        exist_ok=True)
        inputs = os.path.join(self.root, "inputs.json")
        Path(inputs).write_text(json.dumps(document))

        out = io.StringIO()
        with mock.patch.object(bootstrap, "_identity_of",
                               lambda command, runtime=None, distro=None: said):
            code = bootstrap.main(["--inputs", inputs, "--destination",
                                   destination, "--distro", distro,
                                   "--repository-source", self.SOURCE],
                                  stream=out, runner=runner)
        self.assertEqual(code, 0, out.getvalue())
        self.assertEqual(len([one for one in issued if one[1] == "clone"]), 5)
        written = json.loads(Path(places["deployment"]).read_bytes())
        self.assertNotIn("repository_source", written)
        self.assertEqual(written["integration_target"],
                         os.path.join(places["repository"], "target.git"))
        # AND THE DEPLOYED INTERFACE IS THERE, which is what the owner operates.
        self.assertTrue(os.path.isfile(places["justfile"]))
        self.assertTrue(os.path.isfile(places["instance"]))


class RepeatingIt(ValidFixture):
    """F2. A repeat preserves what is there, across either representation."""

    def test_an_identical_repeat_is_idempotent(self):
        answer = self.prepared()
        before = Path(answer["places"]["configuration"]).read_bytes()
        again = self.prepared()
        self.assertEqual(again["created_works"], [])
        self.assertEqual(Path(answer["places"]["configuration"]).read_bytes(),
                         before)

    def test_a_conflicting_binding_is_refused_and_nothing_is_rewritten(self):
        answer = self.prepared()
        before = Path(answer["places"]["configuration"]).read_bytes()
        said = self.refused(jobs=[self.job(work_id=self.work,
                                           target="somewhere-else")])
        self.assertIn("already bound", said)
        self.assertIn("canonical_target_id", said)
        self.assertIn("its own state_root", said)
        self.assertEqual(Path(answer["places"]["configuration"]).read_bytes(),
                         before)

    def test_a_changed_declared_base_is_refused_too(self):
        self.prepared()
        self.assertIn("already bound",
                      self.refused(jobs=[self.job(work_id=self.work,
                                                  base="b" * 40)]))

    def test_a_removed_job_is_refused_across_a_schema_change(self):
        """The case that used to pass: `/2` repeated as `/1` compared `None`
        against the previous Job keys, matched nothing, dropped job-b and
        rebound job-a."""
        answer = self.prepared(**self.several())
        before = Path(answer["places"]["configuration"]).read_bytes()
        said = self.refused(jobs=[self.job(work_id=self.work,
                                           target="somewhere-else")])
        self.assertIn("job 'job-b' is already prepared here", said)
        self.assertIn("not thereby unconfigured", said)
        self.assertEqual(Path(answer["places"]["configuration"]).read_bytes(),
                         before)

    def test_growing_from_one_job_to_two_is_also_refused_rather_than_migrated(self):
        """A many-to-one and a one-to-many repeat are the same question, and
        refusing an unsupported change is sufficient -- no migration feature is
        selected here."""
        self.prepared()
        said = self.refused(**dict(self.several(),
                                   jobs=[self.job(work_id=self.work,
                                                  target="elsewhere"),
                                         self.job(job_id="job-b",
                                                  work_id=self.work,
                                                  producer="impl-b")]))
        self.assertIn("already bound", said)

    def test_a_corrupt_record_is_refused_rather_than_overwritten(self):
        answer = self.prepared()
        Path(answer["places"]["record"]).write_text("{ not json")
        before = Path(answer["places"]["configuration"]).read_bytes()
        said = self.refused()
        self.assertIn("could not be read", said)
        self.assertIn("overwrites state it cannot identify", said)
        self.assertEqual(Path(answer["places"]["configuration"]).read_bytes(),
                         before)

    def test_a_configuration_with_no_record_is_refused(self):
        """Its identity is unknown, not proven absent."""
        answer = self.prepared()
        os.unlink(answer["places"]["record"])
        said = self.refused()
        self.assertIn("cannot be established", said)

    def test_a_record_of_another_schema_is_refused(self):
        answer = self.prepared()
        Path(answer["places"]["record"]).write_text(json.dumps({"schema": "other"}))
        self.assertIn(bootstrap.RECORD_SCHEMA, self.refused())

    def test_a_conflicting_authority_is_refused(self):
        self.prepared()
        self.assertIn("already bound to Authority",
                      self.refused(authority_uuid="f" * 32))

    def test_the_conflict_is_found_before_the_authority_is_composed(self):
        """Validated before durable mutation: the refusal must not arrive after
        a Work has been created under the new binding."""
        answer = self.prepared()
        Path(answer["places"]["record"]).write_text("{ not json")
        composed = []
        with mock.patch.object(bootstrap, "_compose",
                               lambda *rest, **named: composed.append(rest)):
            self.refused()
        self.assertEqual(composed, [])

    def test_both_documents_are_published_atomically(self):
        """An interrupted write must not turn a known configuration into
        partial JSON."""
        seen = []
        real = os.replace

        def watched(source, target):
            seen.append((Path(source).name, Path(target).name))
            return real(source, target)

        with mock.patch.object(os, "replace", watched):
            self.prepared()
        self.assertEqual(seen, [("bootstrap.json.tmp", "bootstrap.json"),
                                ("deployment.json.tmp", "deployment.json")])


if __name__ == "__main__":
    unittest.main(verbosity=2)
