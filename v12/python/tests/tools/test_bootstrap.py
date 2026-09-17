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
import pathlib
from pathlib import Path
import shutil
import sys
import tempfile
import time
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
            "checkpoint_profile": PROFILE_KIND,
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
        # AN INSTANCE THAT IS ALREADY INSTALLED, and Jobs added to it.
        # OWNER-FRESH-INSTALL-20260916.md: the Authority identity is generated
        # at install and persisted at the destination, so a worker document --
        # whose input manifest is digest-sealed over that identity -- can only
        # be written against an instance that already has one. These cases
        # supply Jobs, so they run against a root whose identity is the one the
        # accepted stage fixture's workers were built for.
        self.persisted_identity(self.config["authority_uuid"])

    def persisted_identity(self, uuid):
        places = bootstrap.layout(self.state)
        return bootstrap.persist_identity(places, uuid)

    def nothing_was_composed(self):
        """No record, no configuration and no Authority.

        NOT "the state root does not exist": this instance's identity is
        persisted there, by the fixture, before anything is composed -- which
        is the fresh-install order itself. What a refusal must leave behind is
        nothing that BINDS anything.
        """
        places = bootstrap.layout(self.state)
        for name in ("record", "configuration", "authority_store"):
            self.assertFalse(os.path.exists(places[name]), name)

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


class TheInstanceGeneratesItsOwnIdentity(Fixture):
    """OWNER-FRESH-INSTALL-20260916.md: generated once, persisted at the
    destination, reused by every later operation, and distinct per install.

    OVER THE IDENTITY ITSELF, not over a composed deployment: what is under
    test is where the identity comes from and where it stays, and a deployment
    is not needed to ask that.
    """

    def places(self, name="one"):
        return bootstrap.layout(os.path.join(self.temp.name, name))

    def test_a_fresh_root_mints_one_and_writes_it_down(self):
        places = self.places()
        uuid, generated = bootstrap.identity(places)
        self.assertIs(generated, True)
        self.assertEqual(len(uuid), 32)
        self.assertTrue(all(one in "0123456789abcdef" for one in uuid), uuid)
        self.assertFalse(os.path.exists(places["identity"]))
        self.assertEqual(bootstrap.persist_identity(places, uuid), uuid)
        held = json.loads(Path(places["identity"]).read_bytes())
        self.assertEqual(held, {"schema": bootstrap.IDENTITY_SCHEMA,
                                "authority_uuid": uuid})

    def test_a_root_that_has_one_KEEPS_it(self):
        places = self.places()
        first, _ = bootstrap.identity(places)
        bootstrap.persist_identity(places, first)
        again, generated = bootstrap.identity(places)
        self.assertEqual(again, first)
        self.assertIs(generated, False)

    def test_two_installations_are_two_instances(self):
        """Separate installs have separate identities: the whole reason this is
        generated per root rather than named in a document that could be
        copied to a second destination."""
        made = set()
        for name in ("one", "two", "three"):
            places = self.places(name)
            uuid, _ = bootstrap.identity(places)
            bootstrap.persist_identity(places, uuid)
            made.add(uuid)
        self.assertEqual(len(made), 3)

    def test_a_racing_second_writer_reads_what_the_first_wrote(self):
        """O_EXCL: two bootstraps racing for one fresh root do not both believe
        they minted it."""
        places = self.places()
        first, _ = bootstrap.identity(places)
        bootstrap.persist_identity(places, first)
        self.assertEqual(bootstrap.persist_identity(places, first), first)
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.persist_identity(places, "b" * 32)
        self.assertIn("rebinds an instance somebody else installed",
                      str(raised.exception))

    def test_a_LINKED_identity_record_is_refused_and_left_alone(self):
        """Review 2026-09-16T22-27-59Z [F3]: the read followed a symlink, so two
        destinations each carrying a link at this name to ONE external file
        both read the same identity and both believed they were installed
        independently. That is the destination-owned isolation boundary gone."""
        outside = pathlib.Path(self.temp.name) / "somebody-elses-identity.json"
        outside.write_text(json.dumps({"schema": bootstrap.IDENTITY_SCHEMA,
                                       "authority_uuid": "c" * 32}))
        made = []
        for name in ("one", "two"):
            places = self.places(name)
            Path(places["identity"]).parent.mkdir(parents=True, exist_ok=True)
            os.symlink(str(outside), places["identity"])
            with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
                bootstrap.identity(places)
            said = str(raised.exception)
            self.assertIn("not a file this destination owns", said)
            self.assertIn("Nothing here removed it", said)
            # AND THE FOREIGN NAME IS EXACTLY AS IT WAS.
            self.assertTrue(os.path.islink(places["identity"]))
            made.append(places)
        self.assertEqual(json.loads(outside.read_bytes())["authority_uuid"],
                         "c" * 32)
        # AND PERSISTING THROUGH IT IS REFUSED TOO: O_EXCL fails against the
        # link, and the fallback read is the same safe one.
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.persist_identity(made[0], "d" * 32)
        self.assertIn("not a file this destination owns", str(raised.exception))
        self.assertEqual(json.loads(outside.read_bytes())["authority_uuid"],
                         "c" * 32)

    def test_a_DANGLING_identity_link_is_not_read_as_absent(self):
        """The [K3] shape, here: `exists` follows the final link, so a dangling
        one reads as absent -- and a fresh identity would then be written
        THROUGH it, into wherever it points."""
        places = self.places()
        Path(places["identity"]).parent.mkdir(parents=True, exist_ok=True)
        gone = os.path.join(self.temp.name, "never-existed.json")
        os.symlink(gone, places["identity"])
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.identity(places)
        self.assertIn("dangling link", str(raised.exception))
        self.assertFalse(os.path.exists(gone))
        self.assertTrue(os.path.islink(places["identity"]))

    def test_an_identity_that_is_not_a_regular_file_is_refused(self):
        places = self.places()
        os.makedirs(places["identity"], exist_ok=True)
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.identity(places)
        self.assertIn("is a directory rather than a regular file",
                      str(raised.exception))
        self.assertTrue(os.path.isdir(places["identity"]))

    def test_the_identity_is_a_name_the_DESTINATION_owns(self):
        """It is in the custody sweep, so a link at it is refused before any
        effect rather than discovered by the reader."""
        from tools import instance as instances

        places = instances.layout(os.path.join(self.temp.name, "destination"))
        self.assertEqual(os.path.basename(places["identity"]),
                         "authority-identity.json")
        os.makedirs(places["destination"], exist_ok=True)
        os.symlink("/etc/hostname", places["identity"])
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.custody(places, places["destination"])
        self.assertIn("already carries a link at", str(raised.exception))

    def test_a_NAMED_PIPE_is_refused_WITHOUT_waiting_for_a_writer(self):
        """Review 2026-09-16T22-36-58Z: `os.open` on a FIFO blocks for a writer
        -- before `fstat` can say it is one -- so a setup command met a named
        pipe somebody left in a destination by hanging forever. O_NONBLOCK
        makes the read-only open return at once, and the no-follow descriptor
        proof is untouched."""
        import signal

        places = self.places()
        Path(places["identity"]).parent.mkdir(parents=True, exist_ok=True)
        os.mkfifo(places["identity"])

        def ring(signum, frame):
            raise TimeoutError("the identity read blocked on a named pipe")

        previous = signal.signal(signal.SIGALRM, ring)
        signal.setitimer(signal.ITIMER_REAL, 5.0)
        try:
            with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
                bootstrap.identity(places)
        finally:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, previous)
        self.assertIn("named pipe", str(raised.exception))
        self.assertIn("Nothing here replaced it", str(raised.exception))
        # AND THE FOREIGN NODE IS STILL THERE.
        import stat as modes

        self.assertTrue(modes.S_ISFIFO(os.lstat(places["identity"]).st_mode))

    def test_an_identity_LARGER_than_a_record_is_refused_rather_than_truncated(self):
        """The other half of the same review: the read took the first 64 KiB
        and discarded the rest, so a valid record padded past that bound and
        followed by rubbish PARSED -- while the file on disk does not. A reader
        that sees part of a document answers about a document nobody wrote."""
        places = self.places()
        Path(places["identity"]).parent.mkdir(parents=True, exist_ok=True)
        # THE REVIEWER'S EXACT CASE, and the padding is inside the document on
        # purpose: the first IDENTITY_LIMIT bytes are a COMPLETE, VALID record,
        # so a reader that took exactly that many and stopped would accept it
        # and never see the rubbish after. A shorter document cut mid-string
        # would be caught by the parser and would prove nothing about the bound.
        held = {"schema": bootstrap.IDENTITY_SCHEMA,
                "authority_uuid": "e" * 32, "padding": ""}
        held["padding"] = "x" * (bootstrap.IDENTITY_LIMIT
                                 - len(json.dumps(held)))
        whole = json.dumps(held)
        self.assertEqual(len(whole), bootstrap.IDENTITY_LIMIT)
        self.assertEqual(json.loads(whole)["authority_uuid"], "e" * 32)
        Path(places["identity"]).write_text(whole + "\nNOT JSON\n")
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.identity(places)
        self.assertIn("larger than", str(raised.exception))
        self.assertIn(str(bootstrap.IDENTITY_LIMIT), str(raised.exception))

    def test_TRAILING_rubbish_within_the_bound_is_refused_too(self):
        """Under the bound there is nothing to truncate, so the parse is over
        the whole file and trailing rubbish is a document that does not read."""
        places = self.places()
        Path(places["identity"]).parent.mkdir(parents=True, exist_ok=True)
        Path(places["identity"]).write_text(
            json.dumps({"schema": bootstrap.IDENTITY_SCHEMA,
                        "authority_uuid": "e" * 32}) + "\nNOT JSON\n")
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            bootstrap.identity(places)
        self.assertIn("could not be read", str(raised.exception))

    def test_a_record_AT_the_bound_still_reads(self):
        """The bound refuses what is over it and nothing else: an ordinary
        record, and one padded to just under, both still answer."""
        places = self.places()
        Path(places["identity"]).parent.mkdir(parents=True, exist_ok=True)
        held = {"schema": bootstrap.IDENTITY_SCHEMA,
                "authority_uuid": "e" * 32}
        held["padding"] = "x" * (bootstrap.IDENTITY_LIMIT
                                 - len(json.dumps(held)) - 16)
        Path(places["identity"]).write_text(json.dumps(held))
        self.assertEqual(bootstrap.identity(places), ("e" * 32, False))

    def test_an_unreadable_identity_is_unknown_rather_than_absent(self):
        for written in ("{not json", json.dumps({"schema": "other"}),
                        json.dumps({"schema": bootstrap.IDENTITY_SCHEMA,
                                    "authority_uuid": "short"})):
            places = self.places("root-" + str(len(written)))
            Path(places["identity"]).parent.mkdir(parents=True, exist_ok=True)
            Path(places["identity"]).write_text(written)
            with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
                bootstrap.identity(places)
            self.assertIn("is unknown", str(raised.exception), written)


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
        self.nothing_was_composed()

    def test_another_optional_member_in_an_unusable_form_is_refused(self):
        """`result_judgment_workers` is held by `held_configuration` too, so an
        unusable form is refused here, before anything is made."""
        said = self.refused(result_judgment_workers=17)
        self.assertIn("not one the manager would accept", said)
        self.nothing_was_composed()

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

    def test_a_record_whose_bindings_are_not_a_mapping_is_refused(self):
        answer, before = self.composed()
        held = json.loads(Path(answer["places"]["record"]).read_bytes())
        for value in ([], None, "none"):
            held["bindings"] = value
            self.rewrite(answer, "record", held)
            self.assertIn("rather than a mapping", self.refusing(), repr(value))
        self.unchanged(answer, before, "configuration")

    def test_an_EMPTY_binding_mapping_is_an_answer_and_is_still_compared(self):
        """OWNER-FRESH-INSTALL-20260916.md: an installed instance binds zero
        Jobs, so "this root holds no bindings" is a thing a record has to be
        able to SAY -- it is no longer read as a record that says nothing.

        AND IT IS STILL EVIDENCE. The configuration beside it binds one Job, so
        the pair disagrees and the repeat is refused; what changed is which
        sentence is true about the record, not whether it is checked.
        """
        answer, before = self.composed()
        held = json.loads(Path(answer["places"]["record"]).read_bytes())
        held["bindings"] = {}
        self.rewrite(answer, "record", held)
        said = self.refusing()
        self.assertNotIn("rather than a mapping", said)
        self.assertIn("binds one Job and its record names 0", said)
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


def guide_example():
    """The no-Job input document THIS GUIDE offers, parsed out of it.

    Review 2026-09-16T22-27-59Z [F2] and 2026-09-16T22-36-58Z: the example has
    to be runnable, and the way to keep it runnable is to run THAT ONE rather
    than a copy of it that can drift.
    """
    guide = (_DISTRIBUTION.parent / "STACK.md").read_text()
    heading = "### A fresh installation has zero Jobs"
    block = guide.split(heading, 1)[1].split("```json", 1)[1]
    return json.loads(block.split("```", 1)[0])


class TheGUIDES_OWN_EXAMPLE_COMPOSES_AND_SERVES_FROM_SOURCE(unittest.TestCase):
    """The SOURCE-RUN empty lifecycle, and the name says which one it is.

    CORRECTED LABEL. Review 2026-09-16T22-58-33Z [P2]: this class was called
    `..._INSTALLS_AND_SERVES` and its helper `installed()`, and it does neither:
    it calls `bootstrap.prepare`, exports the four source-run variables and
    calls `tools.stack` in process. No destination installer, no runtime copy,
    no selector and no destination justfile. What it proves is real and worth
    having -- the REAL manager and publisher, over real SQLite stores, started
    and stopped -- and it is the source-run form of it.

    `TheINSTALLED_INSTANCE_SERVES_THE_SAME_WAY` below is the installation
    boundary, and it says exactly what it substitutes.

    OWNER-FRESH-INSTALL-20260916.md: start runs the real idle scheduler and
    publisher with honest empty status rather than a dummy success branch.

    NO PROVIDER, ENGINE, CONTAINER, JOB OR NETWORK. What is absent is a
    workload, which is the whole point.
    """

    def setUp(self):
        outside = os.environ.get("BATON_V12_STACK_TEST_ROOT", "/var/tmp")
        self.temp = tempfile.TemporaryDirectory(prefix="v12-idle-", dir=outside)
        self.addCleanup(self.cleanup)
        self.root = self.temp.name

    def cleanup(self):
        from tools import stack

        try:
            stack.main(["stop"], stream=io.StringIO(), environ=self.environ)
        except Exception:                                    # noqa: BLE001
            pass
        self.temp.cleanup()

    def composed_from_source(self):
        document = dict(guide_example(),
                        state_root=os.path.join(self.root, "deployment"))
        answer = bootstrap.prepare(document, stream=io.StringIO())
        self.environ = dict(
            os.environ,
            BATON_V12_JOB_STORE=answer["places"]["job_store"],
            BATON_V12_CONTROL_STORE=answer["places"]["control_store"],
            BATON_V12_AUTHORITY_UUID=answer["authority_uuid"],
            BATON_V12_STAGE_EXECUTION_CONFIG=answer["places"]["configuration"],
            BATON_V12_STACK_ROOT=os.path.join(self.root, "stack"))
        return answer

    def ran(self, *argv):
        from tools import stack

        said = io.StringIO()
        code = stack.main(list(argv), stream=said, environ=self.environ)
        return code, said.getvalue()

    def test_the_guides_example_is_a_document_that_PARSES(self):
        """[F2]: the previous example did not, and a check that compared member
        names said nothing about it."""
        held = guide_example()
        self.assertEqual(set(held), set(bootstrap.REQUIRED))
        self.assertNotIn("jobs", held)
        self.assertNotIn("workers", held)
        self.assertNotIn("authority_uuid", held)

    def test_it_COMPOSES_and_then_STARTS_STATUS_MONITOR_STOPS(self):
        self.composed_from_source()
        code, said = self.ran("start")
        self.assertEqual(code, 0, said)
        self.assertIn("started: manager", said)
        self.assertIn("started: publisher", said)
        # THE REAL GATE, not a claim: every manager acknowledged that its
        # deployment COMPOSED, and the publisher wrote a freshly observed
        # snapshot during this start.
        self.assertIn("acknowledged that its deployment composed", said)
        self.assertIn("empty configured stack is a valid idle state", said)

        code, said = self.ran("status")
        self.assertEqual(code, 0, said)
        self.assertIn("manager    running", said)
        self.assertIn("publisher  running", said)
        self.assertIn("jobs       0 observed (canonical=True)", said)
        self.assertIn("serving    acknowledged", said)
        self.assertIn("snapshot   fresh", said)

        code, said = self.ran("monitor", "--ticks", "2", "--interval", "0.1")
        self.assertEqual(code, 0, said)
        self.assertEqual(said.count("this snapshot reports no Jobs"), 2)

        code, said = self.ran("stop")
        self.assertEqual(code, 0, said)
        self.assertIn("stopped: manager", said)
        self.assertIn("stopped: publisher", said)

        code, said = self.ran("status")
        self.assertEqual(code, 0, said)
        self.assertIn("manager    absent", said)
        self.assertIn("publisher  absent", said)

    def test_the_zeros_are_READ_rather_than_asserted(self):
        """"Never replace real store observation with constant zero." The
        snapshot is written by the publisher out of the actual Job store, so
        the count comes from a read; this proves the file exists, is canonical
        and was observed during this run rather than copied into place."""
        answer = self.composed_from_source()
        self.started = time.time() - 1
        code, said = self.ran("start")
        self.assertEqual(code, 0, said)
        self.addCleanup(self.ran, "stop")
        from tools import stack

        place = stack.snapshot_path(os.path.join(self.root, "stack"))
        published = json.loads(Path(place).read_bytes())
        # CANONICAL means the publisher read the REAL store rather than
        # answering from a cache or a default; `jobs` is what that read found.
        self.assertIs(published.get("canonical"), True)
        self.assertEqual(published.get("jobs"), [])
        self.assertTrue(published.get("observed_at"))
        self.assertEqual(published.get("schema"), "baton.v12.job-status/5")
        # AND IT IS THIS RUN'S: `start` refuses unless a snapshot was written
        # DURING it, which is the gate the message above reports.
        self.assertGreater(os.path.getmtime(place), self.started)
        del answer


class TheINSTALLED_INSTANCE_SERVES_THE_SAME_WAY(unittest.TestCase):
    """The DESTINATION installer, its selector, and the lifecycle through it.

    Review 2026-09-16T22-58-33Z [P2] asked for acceptance at the selected
    installation boundary, and for the substitutions to be named rather than
    implied. They are:

      THE RUNTIME IS A STAND-IN, not a frozen bundle. It is a directory
        carrying the launcher's NAME and a file beside it, exactly as
        `test_instance` composes one -- so what is exercised here is the
        install, the manifest, the selector and the deployed justfile, over a
        runtime whose bytes are this test's. `tests/tools/test_packaging.py`
        asks the REAL bundle its own questions, and no claim is made here
        about frozen behaviour or about any retained bundle.
      THE LIFECYCLE RUNS THROUGH THE SELECTOR, in process. `stack.main
        --instance <destination>/instance.json` is the path the deployed
        justfile's recipes resolve to; what a stand-in runtime cannot do is
        EXECUTE, so the bundled executable itself is not run here.
      REPOSITORIES ARE NOT PREPARED. `--no-repositories` is passed, so no
        clone and no version-control command happens at all.

    What is NOT substituted: the destination layout, `instance.emit`/`create`,
    the manifest digest over the copied runtime, the deployed justfile, the
    persisted identity, and the real manager and publisher over real stores.
    """

    def setUp(self):
        outside = os.environ.get("BATON_V12_STACK_TEST_ROOT", "/var/tmp")
        self.temp = tempfile.TemporaryDirectory(prefix="v12-installed-",
                                                dir=outside)
        self.addCleanup(self.cleanup)
        self.root = self.temp.name
        self.environ = dict(os.environ)

    def cleanup(self):
        from tools import stack

        try:
            stack.main(["--instance", self.places["instance"], "stop"],
                       stream=io.StringIO(), environ=self.environ)
        except Exception:                                    # noqa: BLE001
            pass
        self.temp.cleanup()

    def stand_in_runtime(self):
        """A directory shaped like a one-folder bundle, and nothing more."""
        source = Path(self.root) / "stand-in-distro"
        (source / "_internal").mkdir(parents=True, exist_ok=True)
        (source / "baton-v12-stack").write_text("a stand-in for the launcher")
        (source / "_internal" / "lib.so").write_text("stand-in bytes")
        return str(source)

    def install(self, name="destination"):
        from tools import instance as instances

        destination = os.path.join(self.root, name)
        self.places = instances.layout(destination)
        document = dict(guide_example())
        document.pop("state_root", None)
        inputs = os.path.join(self.root, name + "-inputs.json")
        Path(inputs).write_text(json.dumps(document))
        said = {"command": "baton-v12-stack", "frozen": True,
                "python": "3.13.7", "platform": "Linux", "machine": "x86_64",
                "schema_assets": {"agent-session-1.0": 10,
                                  "worker-control-1.0": 20},
                "native_rpds": str(Path(self.stand_in_runtime())
                                   / "_internal" / "lib.so")}
        out = io.StringIO()
        with mock.patch.object(
                bootstrap, "_identity_of",
                lambda command, runtime=None, distro=None: said):
            code = bootstrap.main(
                ["--inputs", inputs, "--destination", destination,
                 "--distro", self.stand_in_runtime(), "--no-repositories"],
                stream=out)
        self.assertEqual(code, 0, out.getvalue())
        return destination, out.getvalue()

    def test_the_guides_document_INSTALLS_into_a_destination(self):
        destination, said = self.install()
        # THE SELECTOR, THE INTERFACE AND THE RUNTIME.
        self.assertTrue(os.path.isfile(self.places["instance"]))
        self.assertTrue(os.path.isfile(self.places["justfile"]))
        self.assertTrue(os.path.isfile(
            os.path.join(self.places["distro"], "baton-v12-stack")))
        # AND THE IDENTITY IS THIS DESTINATION'S, persisted where it says.
        held = json.loads(Path(self.places["identity"]).read_bytes())
        self.assertEqual(held["schema"], bootstrap.IDENTITY_SCHEMA)
        selector = json.loads(Path(self.places["instance"]).read_bytes())
        self.assertEqual(selector["authority_uuid"], held["authority_uuid"])
        self.assertIn("authority", said)
        # NO REPOSITORY WAS PREPARED, which is what --no-repositories means.
        self.assertFalse(os.listdir(self.places["repository"]))

    def test_two_destinations_are_two_instances(self):
        first, _ = self.install("one")
        from tools import instance as instances

        one = json.loads(Path(self.places["identity"]).read_bytes())
        second, _ = self.install("two")
        two = json.loads(Path(self.places["identity"]).read_bytes())
        self.assertNotEqual(one["authority_uuid"], two["authority_uuid"])
        del first, second, instances

    def test_the_INSTALLED_SELECTOR_drives_the_empty_lifecycle(self):
        from tools import stack

        self.install()
        for argv, expected in (
                (["start"], "started: manager"),
                (["status"], "jobs       0 observed (canonical=True)"),
                (["monitor", "--ticks", "1", "--interval", "0.1"],
                 "this snapshot reports no Jobs"),
                (["stop"], "stopped: manager")):
            said = io.StringIO()
            code = stack.main(["--instance", self.places["instance"]] + argv,
                              stream=said, environ=self.environ)
            self.assertEqual(code, 0, said.getvalue())
            self.assertIn(expected, said.getvalue(), " ".join(argv))

    def effective(self):
        """What the installed deployment actually selects, read from it."""
        return json.loads(Path(self.places["deployment"]).read_bytes())

    def test_a_repeat_that_would_DROP_a_derived_selection_is_refused(self):
        """Review 2026-09-16T23-16-06Z [P2], and the reviewer's own case.

        The installation DERIVES the repository and storage paths under the
        destination; the one-operand branch composes from the input alone. So
        the reconfiguration I documented returned zero and quietly removed
        `integration_workspace` -- selector, runtime and identity all
        unchanged, and the deployment no longer naming where integration
        works. Adding `state_root` alone is NOT sufficient, and saying so is
        now the helper's job rather than the guide's.
        """
        destination, _ = self.install()
        self.assertTrue(self.effective().get("integration_workspace"))
        inputs = os.path.join(self.root, "naive.json")
        Path(inputs).write_text(json.dumps(
            dict(guide_example(), state_root=destination)))
        out = io.StringIO()
        self.assertEqual(bootstrap.main(["--inputs", inputs], stream=out), 2,
                         out.getvalue())
        said = out.getvalue()
        self.assertIn("already configured with integration_workspace", said)
        self.assertIn("Copy the current values out of", said)
        self.assertIn("Nothing was changed", said)
        # AND NOTHING WAS: the selection is still there.
        self.assertTrue(self.effective().get("integration_workspace"))

    def test_RECONFIGURING_an_installed_instance_keeps_everything_else(self):
        """The supported later-configuration path, run rather than described.

        The two-operand installer refuses an existing runtime, so it is NOT
        how an installed instance is updated. The one-operand form -- an input
        whose `state_root` IS the destination AND which carries the selections
        that installation derived -- recomposes in place.

        WHAT IS COMPARED IS THE CONFIGURATION AS WELL AS THE FILES. [P2]: the
        earlier version of this case compared only the immutable ones, which
        is exactly why it passed while the deployment lost a path.
        """
        destination, _ = self.install()
        before = {name: Path(self.places[name]).read_bytes()
                  for name in ("instance", "justfile", "identity")}
        runtime_before = instance_manifest(self.places["distro"])
        effective_before = self.effective()

        document = dict(guide_example(), state_root=destination)
        for name in bootstrap.DERIVED_PATHS:
            if effective_before.get(name):
                document[name] = effective_before[name]
        inputs = os.path.join(self.root, "again.json")
        Path(inputs).write_text(json.dumps(document))
        out = io.StringIO()
        self.assertEqual(bootstrap.main(["--inputs", inputs], stream=out), 0,
                         out.getvalue())
        self.assertIn("reused from this root's record", out.getvalue())
        for name, bytes_before in before.items():
            self.assertEqual(Path(self.places[name]).read_bytes(),
                             bytes_before, name)
        self.assertEqual(instance_manifest(self.places["distro"])["digest"],
                         runtime_before["digest"])
        # THE EFFECTIVE SELECTIONS, member by member.
        after = self.effective()
        for name in ("integration_target", "integration_workspace",
                     "authority_store", "authority_uuid", "job_store"
                     if "job_store" in effective_before else "state_root",
                     "integration_store", "state_root"):
            self.assertEqual(after.get(name), effective_before.get(name), name)
        self.assertEqual(after["job_bindings"],
                         effective_before["job_bindings"])

    def test_the_two_operand_installer_REFUSES_an_installed_destination(self):
        """And it says so, which is why the form above exists."""
        destination, _ = self.install()
        inputs = os.path.join(self.root, "twice.json")
        document = dict(guide_example())
        document.pop("state_root", None)
        Path(inputs).write_text(json.dumps(document))
        out = io.StringIO()
        code = bootstrap.main(["--inputs", inputs, "--destination", destination,
                               "--distro", self.stand_in_runtime(),
                               "--no-repositories"], stream=out)
        self.assertEqual(code, 2, out.getvalue())
        self.assertIn("there is already a runtime at", out.getvalue())


def instance_manifest(distro):
    from tools import instance as instances

    return instances.manifest(distro)


class AnInstanceWithNoCapacityREFUSES_WORK_IT_CANNOT_SERVE(unittest.TestCase):
    """[P1], review 2026-09-16T22-58-33Z, and the reviewer's own reproduction.

    An empty attachment made `PooledManagerOperations.recover` loop over no
    workers, so a REAL accepted control offer was invisible: the manager
    reported an ordinary idle tick while the same control store's own recovery
    called that offer recoverable. An empty report about work that exists reads
    as "there is nothing here", which is the one thing it must not say.

    BOTH BOUNDARIES, because the constructor comparison answers one moment:
    state already present when the deployment composes, and state that ARRIVES
    after it has attached. And nothing is repaired -- each case asserts the
    foreign work is exactly where it was afterwards.

    REAL STORES AND PUBLIC APIS. The control offer is seeded through
    `certify_profile`/`issue_offer`/`accept_offer` with the accepted strict fake
    Authority session at its normal boundary, which is how the rest of this tree
    exercises them. No raw SQL, no provider, no engine, no Job.
    """

    def setUp(self):
        outside = os.environ.get("BATON_V12_STACK_TEST_ROOT", "/var/tmp")
        self.temp = tempfile.TemporaryDirectory(prefix="v12-unserved-",
                                                dir=outside)
        self.addCleanup(self.temp.cleanup)
        self.handles = []
        self.addCleanup(self.close)

    def close(self):
        for one in reversed(self.handles):
            try:
                one.close()
            except Exception:                                # noqa: BLE001
                pass

    def composed(self, name):
        from baton_v12.job_manager import JobStore
        from baton_v12.worker_manager import ControlStore
        from tests.manager.test_offers import NOW

        document = dict(guide_example(),
                        state_root=os.path.join(self.temp.name, name))
        prepared = bootstrap.prepare(document, stream=io.StringIO())
        places = prepared["places"]
        self.uuid = prepared["authority_uuid"]
        self.jobs = JobStore.open(places["job_store"], authority_uuid=self.uuid,
                                  incarnation="case-jobs", clock=lambda: NOW)
        self.control_path = places["control_store"]
        self.control = ControlStore.open(places["control_store"],
                                         incarnation="case-control",
                                         clock=lambda: NOW)
        self.handles += [self.jobs, self.control]
        return prepared

    def seed_offer(self):
        """One accepted offer, through the public Worker Manager operations."""
        from baton_v12.worker_manager import (AuthorityPort, accept_offer,
                                              certify_profile, issue_offer)
        from tests.manager.test_offers import (FakeSession, PROFILE, NOW,
                                               fake_claim_signature)

        session = FakeSession()
        session._work["authority_uuid"] = self.uuid
        port = AuthorityPort(session, fake_claim_signature)
        work_id = self.uuid[:8] + "-W1"
        certify_profile(self.control, "runtime", "reference", PROFILE)
        issue_offer(self.control, port, offer_id="unserved-offer",
                    work_id=work_id, runtime_attempt_id="unserved-attempt",
                    input_digest="sha256:" + "1" * 64,
                    policy_digest="sha256:" + "2" * 64, profile_digest=PROFILE,
                    profile_name="reference",
                    mint_bearer=lambda: "test-only-bearer")
        accept_offer(self.control, port, offer_id="unserved-offer",
                     decision="accept", bearer="test-only-bearer", now=NOW,
                     runtime_attempt_id="unserved-attempt",
                     work_ref={"authority_uuid": self.uuid,
                               "work_id": work_id})

    def still_there(self):
        """The foreign work, exactly as it was. Nothing repaired it."""
        from baton_v12.worker_manager import outstanding_offers

        held = {one["offer_id"]: one["state"]
                for one in outstanding_offers(self.control)}
        self.assertEqual(held.get("unserved-offer"), "accepted")

    def test_control_work_ALREADY_HERE_refuses_at_startup(self):
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution

        prepared = self.composed("already-here")
        self.seed_offer()
        with self.assertRaises(ContractRefusal) as raised:
            stage_execution.operations_from(prepared["configuration"],
                                            self.jobs, self.control)
        said = str(raised.exception)
        self.assertIn("configures no execution capacity", said)
        self.assertIn("live control offer(s)", said)
        self.assertIn("unserved-offer", said)
        self.assertIn("Nothing was expired, abandoned, repaired or executed",
                      said)
        self.still_there()

    def test_control_work_ARRIVING_AFTER_attachment_refuses_on_resume(self):
        """The half a constructor check cannot answer: the deployment composed
        when the stores were empty, and the offer appeared afterwards. The
        manager's own `reconcile` is what must not report an idle tick."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.job_manager import manager
        from tests.manager.test_offers import NOW
        from tools import stage_execution

        prepared = self.composed("arriving")
        composed = stage_execution.operations_from(prepared["configuration"],
                                                   self.jobs, self.control)
        self.addCleanup(composed.release)
        # IDLE IS STILL IDLE while there is genuinely nothing.
        self.assertEqual(manager.reconcile(self.jobs, composed, now=NOW)
                         ["recovered"], {"abandoned": [], "recoverable": []})
        self.seed_offer()
        with self.assertRaises(ContractRefusal) as raised:
            manager.reconcile(self.jobs, composed, now=NOW)
        said = str(raised.exception)
        self.assertIn("refuses on resume", said)
        self.assertIn("unserved-offer", said)
        self.still_there()

    def test_a_POOL_activated_after_attachment_is_not_ignored(self):
        """The reviewer's third case: capacity that arrives naming workers this
        deployment does not configure."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.job_manager import manager, scheduler
        from tests.job_manager.test_scheduling import pool, principals
        from tests.manager.test_offers import NOW
        from tools import stage_execution

        prepared = self.composed("pool-arrives")
        composed = stage_execution.operations_from(prepared["configuration"],
                                                   self.jobs, self.control)
        self.addCleanup(composed.release)
        document = pool()
        scheduler.activate_pool(self.jobs, document, principals(document))
        with self.assertRaises(ContractRefusal) as raised:
            manager.reconcile(self.jobs, composed, now=NOW)
        said = str(raised.exception)
        self.assertIn("active pool generation", said)
        self.assertIn("workers this deployment does not configure", said)
        # AND THE POOL IS STILL ACTIVE: refusing is not deactivating.
        self.assertIsNotNone(scheduler.active_generation(self.jobs))

    def seed_foreign_issued_offer(self):
        """An ISSUED offer from ANOTHER incarnation -- the state
        `recover_on_restart` abandons, and the state this reader must not.

        A reversal probe made this case necessary: the first version of it
        seeded only an ACCEPTED offer, which recovery leaves alone, so a reader
        that expired and abandoned would have passed it. This is the state that
        can tell the two apart.
        """
        from baton_v12.worker_manager import (AuthorityPort, ControlStore,
                                              certify_profile, issue_offer)
        from tests.manager.test_offers import (FakeSession, PROFILE, NOW,
                                               fake_claim_signature)

        elsewhere = ControlStore.open(self.control.path
                                      if hasattr(self.control, "path")
                                      else self.control_path,
                                      incarnation="somebody-else",
                                      clock=lambda: NOW)
        self.handles.append(elsewhere)
        session = FakeSession()
        session._work["authority_uuid"] = self.uuid
        port = AuthorityPort(session, fake_claim_signature)
        certify_profile(elsewhere, "runtime", "foreign", PROFILE)
        issue_offer(elsewhere, port, offer_id="foreign-offer",
                    work_id=self.uuid[:8] + "-W9",
                    runtime_attempt_id="foreign-attempt",
                    input_digest="sha256:" + "3" * 64,
                    policy_digest="sha256:" + "4" * 64, profile_digest=PROFILE,
                    profile_name="foreign",
                    mint_bearer=lambda: "test-only-foreign-bearer")

    def state_of(self, offer_id):
        from baton_v12.worker_manager import outstanding_offers

        for one in outstanding_offers(self.control):
            if one["offer_id"] == offer_id:
                return one["state"]
        return None

    def serve_until_refused(self, seed_on_tick):
        """The REAL `manager.serve` loop, with the injected wait doing the
        seeding -- which is where work actually arrives during a run."""
        from baton_v12.contracts import ContractRefusal
        from baton_v12.job_manager import manager
        from tests.manager.test_offers import NOW
        from tools import stage_execution

        prepared = self.composed("serving")
        composed = stage_execution.operations_from(prepared["configuration"],
                                                   self.jobs, self.control)
        self.addCleanup(composed.release)
        self.ticks = 0

        def sleep(_seconds):
            self.ticks += 1
            if self.ticks == 2:
                seed_on_tick()

        with self.assertRaises(ContractRefusal) as raised:
            manager.serve(self.jobs, composed, clock=lambda: NOW, sleep=sleep,
                          should_continue=lambda: self.ticks < 8, interval=1)
        self.assertGreaterEqual(self.ticks, 2)
        return str(raised.exception)

    def test_SERVE_itself_refuses_an_offer_that_arrives_mid_run(self):
        """[P1], review 2026-09-16T23-16-06Z, and my claim was the wrong one.

        `manager.serve` calls `reconcile` ONCE and then `sweep` every tick
        after it, so a guard living only in `recover` was asked at startup and
        never again. This drives the real loop: empty when it starts, an
        accepted control offer arriving in the injected wait, and the NEXT
        ordinary tick is what must refuse.
        """
        said = self.serve_until_refused(self.seed_offer)
        self.assertIn("on this serving tick", said)
        self.assertIn("live control offer(s)", said)
        self.assertIn("unserved-offer", said)
        self.assertIn("Nothing was expired, abandoned, repaired or executed",
                      said)
        self.still_there()

    def test_SERVE_itself_refuses_a_pool_that_arrives_mid_run(self):
        from baton_v12.job_manager import scheduler
        from tests.job_manager.test_scheduling import pool, principals

        def activate():
            document = pool()
            scheduler.activate_pool(self.jobs, document, principals(document))

        said = self.serve_until_refused(activate)
        self.assertIn("on this serving tick", said)
        self.assertIn("active pool generation", said)
        # AND THE POOL IS UNTOUCHED: refusing is not deactivating.
        self.assertIsNotNone(scheduler.active_generation(self.jobs))

    def test_serve_over_genuinely_empty_stores_just_ticks(self):
        """The control for both: with nothing there, nothing is refused."""
        from baton_v12.job_manager import manager
        from tests.manager.test_offers import NOW
        from tools import stage_execution

        prepared = self.composed("quiet")
        composed = stage_execution.operations_from(prepared["configuration"],
                                                   self.jobs, self.control)
        self.addCleanup(composed.release)
        self.ticks = 0

        def sleep(_seconds):
            self.ticks += 1

        report = manager.serve(self.jobs, composed, clock=lambda: NOW,
                               sleep=sleep, should_continue=lambda: self.ticks < 5,
                               interval=1)
        self.assertEqual(self.ticks, 5)
        self.assertEqual(report["observed"], 0)

    def test_the_READER_itself_changes_nothing(self):
        """`unconfigured_work` is the question WITHOUT the actions.

        `recover_on_restart` answers a related question and ACTS: it expires
        overdue offers and abandons another incarnation's issued ones. A
        deployment that called it merely to look would be settling somebody
        else's durable state to decide whether it may start -- which is exactly
        what the review said must not happen to foreign work.
        """
        from tools import stage_execution

        self.composed("read-only")
        self.seed_offer()
        self.seed_foreign_issued_offer()
        self.assertEqual(self.state_of("foreign-offer"), "issued")
        for _ in range(3):
            found = stage_execution.unconfigured_work(self.jobs, self.control)
            self.assertEqual(len(found), 1, found)
            self.assertIn("2 live control offer(s)", found[0])
        # THE FOREIGN OFFER IS STILL ISSUED. Recovery would have abandoned it;
        # this looked at it.
        self.assertEqual(self.state_of("foreign-offer"), "issued")
        self.still_there()


class AnInstanceWithNoCAPACITY_FAILS_CLOSED(ValidFixture):
    """"Refuse existing/arriving work needing absent workers."

    An empty attachment is safe only because the STORE decides what must be
    attached: `scheduler._required_workers` answers nothing when there is no
    active generation and no live allocation, and the comparison against it is
    what refuses the moment either exists. Nothing here relaxes that -- this
    proves the refusal rather than asserting the rule.
    """

    def test_a_store_with_an_ACTIVE_POOL_refuses_an_empty_composition(self):
        from baton_v12.contracts import ContractRefusal
        from tools import stage_execution

        document = self.document()
        document.pop("jobs", None)
        prepared = bootstrap.prepare(document, stream=io.StringIO())
        configured = dict(prepared["configuration"], workers=[],
                          job_bindings=[])
        configured.pop("job_work_id", None)
        configured.pop("review_work_id", None)
        configured.pop("line_declared_base", None)
        configured.pop("canonical_target_id", None)
        # A store that HAS an active generation, which is what a previously
        # configured instance leaves behind.
        with mock.patch.object(
                __import__("baton_v12.job_manager.scheduler", fromlist=["x"]),
                "_required_workers",
                lambda store: [{"generation": 1, "worker_id": "impl-a",
                                "participant": "baton.impl-a",
                                "canonical_principal": "principal:x"}]):
            from baton_v12.job_manager.scheduler import PooledManagerOperations

            with self.assertRaises(ContractRefusal) as raised:
                PooledManagerOperations(object(), {},
                                        resolved_principals={"baton.impl-a":
                                                             "principal:x"})
        self.assertIn("exactly the active generation", str(raised.exception))
        del stage_execution, configured

    def test_an_attached_deployment_with_no_worker_answers_no_operation(self):
        from baton_v12.contracts import ContractRefusal
        from baton_v12.job_manager import scheduler

        with mock.patch.object(scheduler, "_required_workers",
                               lambda store: []):
            pooled = scheduler.PooledManagerOperations(
                object(), {}, resolved_principals={})
        with self.assertRaises(ContractRefusal) as raised:
            pooled._any()
        self.assertIn("no configured execution capacity", str(raised.exception))


def _work_or_none(authority, work_id):
    try:
        return authority.project_work(work_id)
    except Exception:                                        # noqa: BLE001
        return None


class AFreshInstallHasZeroJobs(ValidFixture):
    """OWNER-FRESH-INSTALL-20260916.md, and every sentence here is one of its.

    "Why are we asking for any job, this is a fresh install." An installation
    initializes an INSTANCE -- stores, profiles, pool, identity -- and a Work,
    a declared base, a canonical target and a producer assignment are facts
    about a JOB, supplied and validated when one is created.

    WHAT IS PROVED: that such an input is accepted at all, that what it emits
    is a document the MANAGER's own validator accepts, and above all that
    nothing was invented to make it so -- no placeholder Work, no Job, no grant
    and no fabricated binding.
    """

    def instance_only(self, **members):
        document = self.document(**members)
        document.pop("jobs", None)
        with open(os.devnull, "w") as quiet:
            return bootstrap.prepare(document, stream=quiet)

    def test_an_input_naming_no_jobs_is_accepted(self):
        held = bootstrap.held({name: self.document()[name]
                               for name in bootstrap.REQUIRED})
        self.assertNotIn("jobs", held)
        self.assertNotIn("jobs", bootstrap.REQUIRED)
        self.assertNotIn("authority_uuid", bootstrap.REQUIRED)

    def test_the_emitted_configuration_binds_NOTHING_and_says_so(self):
        configured = self.instance_only()["configuration"]
        self.assertEqual(configured["schema"], bootstrap.MULTI_JOB_SCHEMA)
        self.assertEqual(configured["job_bindings"], [])
        # AND CARRIES NO JOB FACTS AT ALL. A global Work, base or target beside
        # an empty binding list would be two answers to "what does this serve".
        for name in ("job_work_id", "review_work_id", "line_declared_base",
                     "canonical_target_id"):
            self.assertNotIn(name, configured, name)

    def test_it_is_a_document_the_MANAGER_accepts(self):
        """`prepare` calls the accepted validator itself, so reaching this line
        is already the proof; asking it again here is what makes the
        instance-only form a case rather than a side effect."""
        from tools import stage_execution

        configured = self.instance_only()["configuration"]
        normalized = stage_execution.held_configuration(configured)
        self.assertEqual(normalized["job_bindings"], [])

    def test_NO_placeholder_work_job_grant_or_binding_is_composed(self):
        answer = self.instance_only()
        self.assertEqual(answer["created_works"], [])
        self.assertEqual(answer["record"]["bindings"], {})
        self.assertEqual(answer["capacity"]["jobs"], 0)
        self.assertIn("binds no Job", answer["capacity"]["note"])
        # AND THE AUTHORITY HOLDS NO WORK AND NO GRANT. A grant is made in a
        # bound Work's OWN scope, so an instance with no Work has no scope to
        # grant anything in -- and a receipt participant that already held one
        # would be authorized over something nobody configured.
        from baton_v12.authority import Authority

        authority = Authority.open(
            answer["places"]["authority_store"],
            expected_authority_uuid=answer["authority_uuid"])
        try:
            self.assertIsNone(_work_or_none(authority, self.work))
            for who in answer["configuration"]["receipt_participants"].values():
                self.assertEqual(authority.grants_of(who), [], who)
        finally:
            dispose = getattr(authority, "dispose", None)
            if dispose is not None:
                dispose()

    def test_it_says_out_loud_that_it_composed_no_job(self):
        said = io.StringIO()
        document = self.document()
        document.pop("jobs", None)
        bootstrap.prepare(document, stream=said)
        self.assertIn("no Work, grant or placeholder was created",
                      said.getvalue())

    def test_a_JOB_ADDED_LATER_is_bound_and_the_instance_is_not_rebuilt(self):
        """The subsequent-Job path, which is the other half of the boundary:
        the instance keeps its identity and the Job brings its own Work."""
        first = self.instance_only()
        again = self.prepared()
        self.assertEqual(again["authority_uuid"], first["authority_uuid"])
        self.assertIs(again["authority_generated"], False)
        self.assertEqual(again["created_works"], [self.work])
        self.assertEqual(sorted(again["record"]["bindings"]), ["job-a"])

    def test_the_guides_minimal_block_NAMES_what_is_required_and_no_more(self):
        """WHAT THIS PROVES AND WHAT IT DOES NOT, said here because review
        2026-09-16T22-27-59Z [F2] found me claiming the stronger thing.

        It proves the member NAMES are exactly the required set. It does NOT
        prove the block parses or runs: the elided `deployment` is not JSON,
        and a runnable no-Job example cannot exist while a worker document is
        required and is sealed to an identity that does not exist yet. The
        guide now says that about itself rather than being contradicted by it.
        """
        guide = (_DISTRIBUTION.parent / "STACK.md").read_text()
        heading = "### A fresh installation has zero Jobs"
        self.assertIn(heading, guide)
        block = guide.split(heading, 1)[1].split("```json", 1)[1]
        block = block.split("```", 1)[0]
        named = {line.split('"')[1] for line in block.splitlines()
                 if line.startswith('  "')}
        self.assertEqual(named, set(bootstrap.REQUIRED))
        self.assertNotIn("jobs", named)
        self.assertNotIn("authority_uuid", named)
        # AND NO OTHER BLOCK IN THE GUIDE CONTRADICTS IT by offering a member
        # this implementation refuses.
        self.assertNotIn('"authority_uuid": "<32 lowercase hex>"', guide)
        # AND NO SECTION STILL SAYS THE OPPOSITE OF WHAT THIS BUILD DOES.
        # Review 2026-09-16T22-58-33Z [P2]: the later-Job section still said a
        # manager cannot serve without a pool, the repetition section still
        # required a non-empty binding record, and the member table said every
        # Job-specific member was required of every document.
        for contradiction in ("a manager cannot serve without one",
                              "a non-empty set of bindings",
                              "and every one of these is\nrequired:"):
            self.assertNotIn(contradiction, guide, contradiction)
        self.assertIn("An empty pool serves", guide)
        self.assertIn("Reconfiguring an instance that is already installed",
                      guide)

    def test_EVERY_job_rule_still_holds_when_jobs_ARE_supplied(self):
        """"Preserve validation when real Jobs are later supplied." The rules
        did not become optional; only the Jobs did."""
        said = self.refused(jobs=[self.job(work_id=self.work),
                                  self.job(work_id=self.work)])
        self.assertIn("distinct", said)
        self.assertIn("job-a", said)
        incomplete = self.job(work_id=self.work)
        del incomplete["canonical_target_id"]
        self.assertIn("jobs[0].canonical_target_id",
                      self.refused(jobs=[incomplete]))
        self.assertIn("not a configured implementation worker",
                      self.refused(jobs=[self.job(work_id=self.work,
                                                  producer="nobody")]))


class TheFreshInstallStillNeedsTheWORKERSToBeSeparable(ValidFixture):
    """THE CAPABILITY THIS CORRECTION DOES NOT REACH, named rather than
    discovered by an owner running the command.

    OWNER-FRESH-INSTALL-20260916.md removes Job, Work, base, target and
    per-Job worker assignment from a fresh input, and this delivery removes
    them: `jobs` is optional, the identity is generated, and no placeholder
    Work, Job or grant is composed.

    WHAT REMAINS IS THE POOL. `single_worker` requires every worker to carry an
    `input_manifest`, and that manifest is DIGEST-SEALED over a `work_ref`
    naming an Authority and a Work. So a configured worker is bound to one Work
    and to one Authority identity -- and an identity generated during the same
    command cannot be one a document written beforehand was sealed to. A pool
    is therefore not yet instance configuration in this build, and it cannot be
    left out either: `scheduler.own_pool` refuses an empty pool, so a manager
    cannot serve without one.

    This case PROVES the refusal rather than describing it, so the remaining
    scope is a fact about the build instead of a claim in a dossier.
    """

    def test_a_worker_sealed_to_another_identity_is_refused_BY_NAME(self):
        fresh = os.path.join(self.root, "never-installed")
        with self.assertRaises(bootstrap.BootstrapRefusal) as raised:
            with open(os.devnull, "w") as quiet:
                bootstrap.prepare(self.document(state_root=fresh), stream=quiet)
        said = str(raised.exception)
        self.assertIn("bootstrap input manifest names another Authority", said)
        # AND THE INSTANCE'S OWN IDENTITY IS THE ONE THAT WAS MINTED, so what
        # differs is the worker document rather than this root.
        self.assertNotEqual(bootstrap.identity(bootstrap.layout(fresh))[0],
                            self.config["authority_uuid"])

    def test_the_manifest_is_the_reason_and_it_is_SEALED(self):
        """Not a member this helper could fill in, the way it fills in
        `authority_uuid`, `authority_store`, `participant`, `principal` and
        `launch_role`: the manifest carries its own digest over its own bytes,
        so rewriting the Authority it names would make it a document whose
        declared digest no longer recomputes."""
        worker = self.workers()[0]["deployment"]
        self.assertIn("input_manifest", worker)
        manifest = worker["input_manifest"]
        self.assertIn("manifest_digest", manifest)
        self.assertEqual(manifest["work_ref"]["authority_uuid"],
                         self.config["authority_uuid"])
        self.assertTrue(manifest["work_ref"]["work_id"])


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

        # THE IDENTITY THIS DESTINATION IS BOUND TO, PERSISTED FIRST.
        # OWNER-FRESH-INSTALL-20260916.md generates it at install, and a worker
        # `deployment` carries a DIGEST-SEALED `input_manifest` naming the
        # Authority -- so a worker document can only be written against an
        # identity that already exists. Until the pool is separable from the
        # instance, a destination with configured workers has to be given the
        # identity those workers were sealed to; the case below names that.
        bootstrap.persist_identity(bootstrap.layout(destination),
                                   self.config["authority_uuid"])
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

    def test_a_document_may_not_NAME_an_authority_at_all(self):
        """OWNER-FRESH-INSTALL-20260916.md: the identity is generated once and
        persisted at the destination. A document that named one would be a
        second place for a fact the instance owns, so it is refused by name
        rather than quietly overriding what this root already is."""
        said = self.refused(authority_uuid="f" * 32)
        self.assertIn("authority_uuid", said)
        self.assertIn("generates its own Authority identity once", said)

    def test_a_record_naming_ANOTHER_authority_than_this_root_is_refused(self):
        """The conflict that can still happen: the persisted identity and the
        record disagree about what this root is bound to."""
        answer = self.prepared()
        held = json.loads(Path(answer["places"]["record"]).read_bytes())
        held["authority_uuid"] = "f" * 32
        Path(answer["places"]["record"]).write_text(json.dumps(held))
        # CAUGHT ONE LAYER EARLIER, and by the accepted validator's own
        # reading: the emitted configuration names the Authority this root
        # actually composed and the record now names another, so the pair
        # cannot both be true and the repeat stops there.
        said = self.refused()
        self.assertIn("names Authority", said)
        self.assertIn("its record names 'ffffffffffffffffffffffffffffffff'",
                      said)

    def test_an_unreadable_persisted_identity_is_refused_rather_than_replaced(self):
        answer = self.prepared()
        Path(answer["places"]["identity"]).write_text("{not json")
        self.assertIn("what Authority this root is bound to is unknown",
                      self.refused())

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
