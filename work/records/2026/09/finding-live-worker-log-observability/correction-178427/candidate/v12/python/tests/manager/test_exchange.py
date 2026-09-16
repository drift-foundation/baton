"""W81857 — the durable per-attempt file exchange, at both of its ends.

`work/records/2026/09/finding-v12-production-runtime-conversation/`.

WHAT THIS FILE IS NOT ABOUT. It does not re-check that a blocking
stdin/stdout conversation reaches a provider. That transport still exists and
`test_worker_entry` still owns it, but Slawomir's supersession of 2026-09-03
took its production authority away: a manager that holds the only reader of a
provider's answer has coupled the container's lifetime to its own, and a
restart there destroys protocol state a healthy container is still producing.

THE PROPERTY THIS FILE IS ABOUT is that nothing here needs a live manager. The
command is a durable file, the receipt is a durable file, and the fence that
stops a second provider turn is a durable file -- so the interesting cases are
the ones where a process disappears between two of them.
"""

import json
import os
import shutil
import stat
import tempfile
import unittest

from baton_v12.contracts import (ContractRefusal, forget_secret, held_secret,
                                 live_secret, remember_secret)
from baton_v12.worker_manager import (ControlStore, configure_workspace_group,
                                      configured_workspace_group)
from baton_v12.worker_manager import exchange, launch, workspaces


class Home(unittest.TestCase):
    """One launch home, one configured workspace group, one attempt."""

    ATTEMPT = "attempt-1"
    SESSION = "session-one"

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-exchange-")
        self.addCleanup(self.take_it_away)
        self.launch_home = os.path.join(self.home, "launch")
        os.makedirs(self.launch_home)
        self.control = ControlStore.open(
            os.path.join(self.home, "control.sqlite3"),
            incarnation="i-1", clock=lambda: "2026-09-04T00:00:00.000Z")
        self.addCleanup(self.control.close)
        # THE DEPLOYMENT'S OWN RECORD IS WHAT MINTS THE CAPABILITY, so the
        # fixture configures it rather than composing a `WorkspaceGroup`: a
        # type any caller can construct would leave exactly the hole the
        # frozen answer exists to close.
        configure_workspace_group(self.control, os.getgid())
        self.group = configured_workspace_group(self.control)

    def take_it_away(self):
        for current, directories, files in os.walk(self.home, topdown=False):
            os.chmod(current, 0o700)
            for name in files:
                os.remove(os.path.join(current, name))
            for name in directories:
                os.rmdir(os.path.join(current, name))
        os.rmdir(self.home)

    def delivered(self, attempt_id=None, session=None):
        return launch.materialize(
            self.launch_home, attempt_id=attempt_id or self.ATTEMPT,
            session=session or self.SESSION, contract="do the thing",
            role="implementation", transport=exchange.EXCHANGE_TRANSPORT,
            workspace_group=self.group)

    def adopted(self, attempt_id=None, session=None, **overrides):
        body = {"attempt_id": attempt_id or self.ATTEMPT,
                "session": session or self.SESSION,
                "contract": "do the thing", "role": "implementation",
                "transport": exchange.EXCHANGE_TRANSPORT,
                "workspace_group": self.group}
        body.update(overrides)
        return launch.adopt(self.launch_home, **body)

    def commanded(self, delivery=None, session=None):
        held = delivery if delivery is not None else self.delivered().exchange
        document = exchange.command_document(
            session=session or self.SESSION, attempt_id=held.attempt_id)
        exchange.publish_command(held, document)
        return held, document

    def wrote(self, delivery, name, document):
        """One worker-written event document, by the shortest honest route.

        The real worker publishes these atomically; what these cases are about
        is what the MANAGER does with the bytes, so the fixture writes them
        directly and `TheWorkerIsTheOtherEnd` drives the real publisher.
        """
        place = os.path.join(delivery.event_root, name)
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(document, writing)
        return place

    def one(self):
        """ONE delivery per case, reused across every subTest.

        `launch.materialize` refuses an existing root on purpose, so a helper
        that built a fresh delivery per spoiled value would be testing that
        refusal instead of the member rule. Every case here overwrites one
        event document at its fixed name, which is also what a worker that
        rewrote its own answer would do.
        """
        if getattr(self, "_one", None) is None:
            self._one = self.commanded()
        return self._one

    def bound(self, document, **members):
        return {"session": self.SESSION, "attempt_id": self.ATTEMPT,
                "sequence_id": document["sequence_id"],
                "command_digest": exchange.observation(
                    self.adopted().exchange)["command"]["command_digest"],
                **members}

    def receipt(self, document, **overrides):
        held = self.bound(document, schema=exchange.RECEIPT_SCHEMA,
                          accepted_at="2026-09-04T00:00:01.000Z")
        held.update(overrides)
        return held

    def state(self, document, operation, state):
        held = self.bound(document, schema=exchange.STATE_SCHEMA,
                          operation=operation,
                          operation_id=f"{operation}:{self.ATTEMPT}",
                          state=state)
        return held

    def chain(self, delivery, document, *, answered=None, ending="answered",
              stopped=None, **overrides):
        """The whole correlated sequence a real worker leaves behind.

        W81857 review 2026-09-04T04-17-15Z [P1]: a terminal is the END of a
        sequence and the manager now requires its beginning -- the receipt that
        proves dispatch was fenced, and a state event per operation agreeing
        with what the terminal claims. A fixture that wrote a terminal alone
        was writing something no worker produces, which is exactly the forgery
        the correction refuses.
        """
        answered = (list(exchange.OPERATIONS) if answered is None
                    else list(answered))
        self.wrote(delivery, exchange.RECEIPT_DOCUMENT,
                   self.receipt(document))
        for operation in answered:
            self.wrote(delivery, exchange.state_document(operation),
                       self.state(document, operation, "answered"))
        if stopped is not None:
            self.wrote(delivery, exchange.state_document(stopped),
                       self.state(document, stopped, "faulted"))
        self.wrote(delivery, exchange.TERMINAL_DOCUMENT,
                   self.terminal(document, ending=ending, answered=answered,
                                 **overrides))
        return exchange.observation(delivery)

    def terminal(self, document, **overrides):
        held = self.bound(document, schema=exchange.TERMINAL_SCHEMA,
                          ending="answered",
                          answered=list(exchange.OPERATIONS),
                          disposition="completed", fault_code=None,
                          manifest_digest="sha256:" + "4" * 64)
        held.update(overrides)
        return held


class TheLaunchDocumentSelectsTheTransport(Home):
    """A container speaks the exchange because its launch document says so.

    NOT BECAUSE ITS FILESYSTEM LOOKS RIGHT. A worker that used a mounted
    command directory whenever it found one would be a worker with two live
    contracts and no version -- which is precisely the environment channel
    W26291 retired.
    """

    def test_the_second_version_carries_exactly_one_more_member(self):
        document = launch.launch_document(
            session="s", contract="c", role="r",
            transport=exchange.EXCHANGE_TRANSPORT)
        self.assertEqual(sorted(document), sorted(launch.EXCHANGE_MEMBERS))
        self.assertEqual(document["schema"], "baton.worker-launch/2")
        self.assertEqual(document["transport"], "baton.worker-exchange/1")

    def test_the_first_version_is_unchanged_and_carries_no_transport(self):
        document = launch.launch_document(session="s", contract="c", role="r")
        self.assertEqual(sorted(document), sorted(launch.LAUNCH_MEMBERS))
        self.assertEqual(document["schema"], "baton.worker-launch/1")

    def test_a_transport_this_build_cannot_name_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            launch.launch_document(session="s", contract="c", role="r",
                                   transport="baton.worker-exchange/2")
        self.assertEqual(caught.exception.code, "denied")

    def test_the_schema_decides_the_member_set_rather_than_the_union(self):
        self.assertEqual(
            launch.members_for({"schema": launch.EXCHANGE_SCHEMA}),
            launch.EXCHANGE_MEMBERS)
        self.assertEqual(launch.members_for({"schema": launch.LAUNCH_SCHEMA}),
                         launch.LAUNCH_MEMBERS)

    def test_the_exchange_root_is_created_beside_the_document(self):
        delivered = self.delivered()
        self.assertEqual(sorted(os.listdir(delivered.root)),
                         ["command", "events", "launch.json"])
        self.assertIsNotNone(delivered.exchange)

    def test_a_first_version_launch_creates_no_namespaces(self):
        delivered = launch.materialize(
            self.launch_home, attempt_id="attempt-2", session="s",
            contract="c", role="r")
        self.assertEqual(sorted(os.listdir(delivered.root)), ["launch.json"])
        self.assertIsNone(delivered.exchange)

    def test_the_exchange_needs_the_configured_group_to_be_created(self):
        with self.assertRaises(ContractRefusal) as caught:
            launch.materialize(
                self.launch_home, attempt_id="attempt-3", session="s",
                contract="c", role="r",
                transport=exchange.EXCHANGE_TRANSPORT)
        self.assertEqual(caught.exception.code, "denied")


class TheParentIsClosedAndTheNamespacesAreNot(Home):
    """Where each mode comes from, and what each one is actually protecting.

    THE PARENT IS WHAT THE WORKER CANNOT MOVE. Renaming or replacing `command`
    is a permission of the root, not of the namespace, so the root's
    `READ_ONLY_DIR` is the whole defence -- and it can only be established
    once every entry exists, which is why it is set last.
    """

    def test_the_root_is_read_only_and_the_command_namespace_is_readable(self):
        delivered = self.delivered()
        self.assertEqual(stat.S_IMODE(os.stat(delivered.root).st_mode),
                         launch.READ_ONLY_DIR)
        self.assertEqual(
            stat.S_IMODE(os.stat(delivered.exchange.command_root).st_mode),
            exchange.COMMAND_DIR)

    def test_the_event_namespace_is_group_writable_in_the_configured_group(self):
        delivered = self.delivered()
        found = os.stat(delivered.exchange.event_root)
        self.assertEqual(stat.S_IMODE(found.st_mode), workspaces.WORKSPACE_DIR)
        self.assertEqual(found.st_gid, os.getgid())

    def test_a_published_command_is_read_only_for_everybody(self):
        held, document = self.commanded()
        place = os.path.join(held.command_root,
                             document["sequence_id"] + ".json")
        self.assertEqual(stat.S_IMODE(os.stat(place).st_mode),
                         exchange.COMMAND_FILE)

    def test_adoption_refuses_a_namespace_whose_modes_have_moved(self):
        delivered = self.delivered()
        os.chmod(delivered.root, 0o700)
        os.chmod(delivered.exchange.command_root, 0o777)
        os.chmod(delivered.root, launch.READ_ONLY_DIR)
        with self.assertRaises(ContractRefusal) as caught:
            self.adopted()
        self.assertEqual(caught.exception.code, "denied")

    def test_adoption_refuses_a_root_widened_past_what_this_build_creates(self):
        delivered = self.delivered()
        os.chmod(delivered.root, 0o700)
        os.mkdir(os.path.join(delivered.root, "somebody-elses"))
        os.chmod(delivered.root, launch.READ_ONLY_DIR)
        with self.assertRaises(ContractRefusal) as caught:
            self.adopted()
        self.assertEqual(caught.exception.code, "denied")

    def test_a_first_version_adoption_refuses_a_root_with_namespaces(self):
        self.delivered()
        with self.assertRaises(ContractRefusal) as caught:
            self.adopted(transport=None)
        self.assertEqual(caught.exception.code, "denied")

    def test_the_bytes_still_decide_which_delivery_this_is(self):
        self.delivered()
        with self.assertRaises(ContractRefusal) as caught:
            self.adopted(session="somebody-elses-session")
        self.assertEqual(caught.exception.code, "denied")

    def test_absence_adopts_nothing_rather_than_authoring_one(self):
        self.assertIsNone(self.adopted())


class TheCommandIsAuthoredAndNotAssembled(Home):

    def test_it_is_exactly_the_closed_members_and_the_pinned_schema(self):
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        self.assertEqual(sorted(document), sorted(exchange.COMMAND_MEMBERS))
        self.assertEqual(document["schema"], exchange.COMMAND_SCHEMA)

    def test_the_order_is_this_contracts_and_not_a_callers(self):
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        self.assertEqual([one["operation"] for one in document["operations"]],
                         ["describe", "work"])
        self.assertEqual([one["operation_id"]
                          for one in document["operations"]],
                         [f"describe:{self.ATTEMPT}", f"work:{self.ATTEMPT}"])

    def test_the_sequence_identity_is_derived_from_the_attempt(self):
        self.assertEqual(exchange.sequence_of(self.ATTEMPT),
                         exchange.sequence_of(self.ATTEMPT))
        self.assertNotEqual(exchange.sequence_of(self.ATTEMPT),
                            exchange.sequence_of("attempt-2"))

    def test_a_live_bearer_cannot_ride_this_document(self):
        bearer = "exchange-bearer-" + "3" * 40
        remember_secret(bearer)
        self.addCleanup(self.forget, bearer)
        with self.assertRaises(ContractRefusal) as caught:
            exchange.command_document(session=bearer,
                                      attempt_id=self.ATTEMPT)
        self.assertEqual(caught.exception.code, "secret-leak")

    def forget(self, bearer):
        while live_secret(bearer):
            forget_secret(bearer)

    def test_the_published_name_is_derived_and_never_supplied(self):
        held, document = self.commanded()
        self.assertEqual(sorted(os.listdir(held.command_root)),
                         [document["sequence_id"] + ".json"])

    def test_two_managers_publishing_one_sequence_write_one_command(self):
        held, document = self.commanded()
        again = exchange.publish_command(held, document)
        self.assertFalse(again["published"])
        self.assertEqual(sorted(os.listdir(held.command_root)),
                         [document["sequence_id"] + ".json"])

    def test_a_different_command_under_that_name_refuses(self):
        held, document = self.commanded()
        other = dict(document)
        other["session"] = "another-session"
        with self.assertRaises(ContractRefusal) as caught:
            exchange.publish_command(held, other)
        self.assertEqual(caught.exception.code, "denied")

    def test_a_command_for_another_attempt_refuses_at_this_delivery(self):
        delivered = self.delivered()
        with self.assertRaises(ContractRefusal) as caught:
            exchange.publish_command(
                delivered.exchange,
                exchange.command_document(session=self.SESSION,
                                          attempt_id="attempt-2"))
        self.assertEqual(caught.exception.code, "denied")

    def test_publication_is_atomic_and_leaves_no_staging_name_behind(self):
        held, document = self.commanded()
        self.assertEqual([one for one in os.listdir(held.command_root)
                          if one.startswith(".")], [])

    def test_a_delivery_this_component_did_not_mint_refuses(self):
        with self.assertRaises(ContractRefusal) as caught:
            exchange.publish_command({"command_root": self.home},
                                     exchange.command_document(
                                         session=self.SESSION,
                                         attempt_id=self.ATTEMPT))
        self.assertEqual(caught.exception.code, "denied")


class PublicationConvergesFromStaleAndCompetingState(Home):
    """W81857 review 2026-09-04T03-43-45Z [P1], both halves of it.

    A fixed `.publishing` name plus `O_EXCL` turned one crash into a permanent
    wedge: the staging file survived, no final document existed, and every
    later incarnation -- and every concurrent second manager -- failed
    `FileExistsError` forever. Inside a transport whose whole purpose is
    surviving a dead process, that is the defect twice over.
    """

    def staging(self, delivery, document):
        return [one for one in os.listdir(delivery.command_root)
                if one.startswith(".") and one.endswith(".publishing")]

    def test_a_crash_created_staging_file_does_not_wedge_publication(self):
        delivery = self.delivered().exchange
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        # EXACTLY WHAT A DEATH BETWEEN CREATION AND RENAME LEAVES, under the
        # name the previous build would have chosen.
        stranded = os.path.join(delivery.command_root,
                                "." + document["sequence_id"]
                                + ".json.publishing")
        with open(stranded, "wb") as writing:
            writing.write(b"a partial document nobody finished")
        answer = exchange.publish_command(delivery, document)
        self.assertTrue(answer["published"])
        self.assertEqual(exchange.observation(delivery)["state"], "waiting")

    def test_stranded_staging_bytes_are_never_adopted(self):
        delivery = self.delivered().exchange
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        stranded = os.path.join(delivery.command_root,
                                "." + document["sequence_id"]
                                + ".json.publishing")
        with open(stranded, "wb") as writing:
            writing.write(b"{}")
        exchange.publish_command(delivery, document)
        view = exchange.observation(delivery)
        self.assertEqual(view["command"]["command_digest"],
                         exchange.publish_command(delivery,
                                                  document)["command_digest"])

    def test_an_ordinary_publication_leaves_no_staging_behind(self):
        delivery = self.delivered().exchange
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        exchange.publish_command(delivery, document)
        self.assertEqual(self.staging(delivery, document), [])

    def test_a_refused_write_leaves_no_staging_behind(self):
        """The unwind runs on the failure path too, not only the happy one."""
        delivery = self.delivered().exchange
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        held = exchange.MAX_EXCHANGE_BYTES
        try:
            exchange.MAX_EXCHANGE_BYTES = 4
            with self.assertRaises(ContractRefusal):
                exchange.publish_command(delivery, document)
        finally:
            exchange.MAX_EXCHANGE_BYTES = held
        self.assertEqual(sorted(os.listdir(delivery.command_root)), [])

    def test_an_ordinary_failure_at_any_step_leaves_no_staging_behind(self):
        """W81857 review 2026-09-04T04-17-15Z [P2], step by step.

        The unwind used to begin only after the write, the mode and the file
        sync had all succeeded. Unique names stopped a stranded file being a
        permanent wedge; they did not stop it being one leaked file per
        transient failure, which is exactly what this publisher's own docstring
        says does not happen.
        """
        delivery = self.delivered().exchange
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        for step, hook in (("write", "_write_whole"),):
            with self.subTest(step=step):
                held = getattr(exchange, hook)

                def failing(handle, payload):
                    # A PARTIAL WRITE FIRST, so the staging file exists and is
                    # non-empty when the failure lands.
                    os.write(handle, payload[:8])
                    raise OSError("injected " + step + " failure")

                setattr(exchange, hook, failing)
                try:
                    with self.assertRaises(OSError):
                        exchange.publish_command(delivery, document)
                finally:
                    setattr(exchange, hook, held)
                self.assertEqual(self.staging(delivery, document), [])

    def test_a_sync_failure_leaves_no_staging_behind(self):
        delivery = self.delivered().exchange
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        held = os.fsync

        def failing(descriptor):
            raise OSError("injected fsync failure")

        os.fsync = failing
        try:
            with self.assertRaises(OSError):
                exchange.publish_command(delivery, document)
        finally:
            os.fsync = held
        self.assertEqual(self.staging(delivery, document), [])
        self.assertEqual(sorted(os.listdir(delivery.command_root)), [])

    def test_two_managers_racing_the_final_name_write_one_command(self):
        """The genuine race, not two sequential calls after the file exists.

        The second publication is driven while the first has ALREADY STAGED
        and not yet taken the final name, which is the window the previous
        build could not survive at all: one fixed staging name meant the
        second caller refused before it reached the question.
        """
        delivery = self.delivered().exchange
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        raced = []
        held = exchange._write_whole

        def racing(handle, payload):
            written = held(handle, payload)
            if not raced:
                # THE GUARD IS SET BEFORE THE RE-ENTRY, not after: the nested
                # publication reaches this same hook, and a guard that only
                # closed once the inner call RETURNED would recurse forever.
                raced.append(None)
                raced[0] = exchange.publish_command(delivery, document)
            return written

        exchange._write_whole = racing
        try:
            mine = exchange.publish_command(delivery, document)
        finally:
            exchange._write_whole = held
        # ONE OF THE TWO TOOK THE NAME AND THE OTHER ADOPTED IT. Which one is
        # the kernel's business; that exactly one command exists is this
        # contract's.
        self.assertEqual(sorted(one["published"] for one in raced + [mine]),
                         [False, True])
        self.assertEqual(len([one for one in os.listdir(delivery.command_root)
                              if not one.startswith(".")]), 1)
        self.assertEqual(exchange.observation(delivery)["state"], "waiting")

    def test_the_final_name_is_never_clobbered_by_a_racing_publication(self):
        """`link` fails closed where `rename` would have replaced.

        A conflicting document arriving in the window between the existence
        check and the publication used to be overwritten -- silently replacing
        a command the worker may already have receipted.
        """
        delivery = self.delivered().exchange
        document = exchange.command_document(session=self.SESSION,
                                             attempt_id=self.ATTEMPT)
        other = dict(document)
        other["session"] = "somebody-elses-session"
        held = exchange._write_whole

        def racing(handle, payload):
            written = held(handle, payload)
            exchange._write_whole = held
            exchange.publish_command(delivery, other)
            return written

        exchange._write_whole = racing
        try:
            with self.assertRaises(ContractRefusal) as caught:
                exchange.publish_command(delivery, document)
        finally:
            exchange._write_whole = held
        self.assertEqual(caught.exception.code, "denied")
        # THE FIRST DOCUMENT IS STILL THERE, unreplaced.
        raw = exchange._read_exact(delivery.command_root,
                                   document["sequence_id"] + ".json",
                                   what="the command")
        self.assertIn(b"somebody-elses-session", raw)


class TheObservationIsTheDurableFilesAndNothingElse(Home):

    def test_an_exchange_with_no_command_is_not_requested(self):
        view = exchange.observation(self.delivered().exchange)
        self.assertEqual(view["state"], "not-requested")
        self.assertIsNone(view["command"])

    def test_a_published_command_with_no_receipt_is_waiting(self):
        held, _document = self.commanded()
        self.assertEqual(exchange.observation(held)["state"], "waiting")

    def test_a_receipt_with_no_terminal_is_working_and_never_lost(self):
        held, document = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(document))
        view = exchange.observation(held)
        self.assertEqual(view["state"], "working")
        self.assertIsNone(view["terminal"])

    def test_an_answered_terminal_carries_only_bounded_protocol_facts(self):
        held, document = self.commanded()
        view = self.chain(held, document)
        self.assertEqual(view["state"], "answered")
        self.assertEqual(sorted(view["terminal"]),
                         ["answered", "disposition", "ending", "fault_code",
                          "manifest_digest"])

    def test_a_faulted_terminal_keeps_its_code_and_carries_no_message(self):
        held, document = self.commanded()
        view = self.chain(held, document, answered=[], ending="faulted",
                          stopped="describe", disposition=None,
                          fault_code="agent", manifest_digest=None)
        self.assertEqual(view["state"], "faulted")
        self.assertEqual(view["terminal"]["fault_code"], "agent")

    def test_a_terminal_naming_another_command_is_not_this_exchanges(self):
        held, document = self.commanded()
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(document,
                                 command_digest="sha256:" + "0" * 64))
        view = exchange.observation(held)
        self.assertEqual(view["state"], "unreadable")
        self.assertEqual(view["unreadable"]["category"], "refused")

    def test_a_terminal_naming_another_session_is_not_this_exchanges(self):
        held, document = self.commanded()
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(document, session="somebody-else"))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_an_answered_ending_that_skipped_an_operation_is_not_an_answer(self):
        held, document = self.commanded()
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(document, answered=["describe"]))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_a_reordered_answer_is_not_the_sequence_that_was_commanded(self):
        held, document = self.commanded()
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(document, answered=["work", "describe"]))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_an_ending_outside_the_closed_set_is_never_the_calmest_one(self):
        held, document = self.commanded()
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(document, ending="finished"))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_an_extra_member_is_refused_rather_than_ignored(self):
        held, document = self.commanded()
        held_terminal = self.terminal(document)
        held_terminal["recap"] = "the provider said a great many things"
        self.wrote(held, exchange.TERMINAL_DOCUMENT, held_terminal)
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_a_worker_document_that_is_not_json_is_untrusted(self):
        held, _document = self.commanded()
        with open(os.path.join(held.event_root, exchange.TERMINAL_DOCUMENT),
                  "wb") as writing:
            writing.write(b"\xff\xfe not a document")
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_an_oversized_worker_document_is_refused_before_it_is_read(self):
        held, _document = self.commanded()
        with open(os.path.join(held.event_root, exchange.TERMINAL_DOCUMENT),
                  "wb") as writing:
            writing.write(b"x" * (exchange.MAX_EXCHANGE_BYTES + 10))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_a_link_at_a_fixed_event_name_is_refused_rather_than_followed(self):
        held, document = self.commanded()
        elsewhere = os.path.join(self.home, "elsewhere.json")
        with open(elsewhere, "w", encoding="utf-8") as writing:
            json.dump(self.terminal(document), writing)
        os.symlink(elsewhere,
                   os.path.join(held.event_root, exchange.TERMINAL_DOCUMENT))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_a_foreign_entry_is_reported_and_never_read(self):
        held, document = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(document))
        with open(os.path.join(held.event_root, "provider.log"), "w",
                  encoding="utf-8") as writing:
            writing.write("a secret-shaped diagnostic nobody asked for")
        view = exchange.observation(held)
        self.assertEqual(view["foreign"], ["provider.log"])
        self.assertEqual(view["state"], "working")

    def test_a_command_this_manager_would_not_have_authored_is_untrusted(self):
        held, document = self.commanded()
        os.chmod(held.command_root, 0o755)
        place = os.path.join(held.command_root,
                             document["sequence_id"] + ".json")
        os.chmod(place, 0o644)
        spoiled = dict(document)
        spoiled["operations"] = [{"operation": "work",
                                  "operation_id": f"work:{self.ATTEMPT}"}]
        with open(place, "w", encoding="utf-8") as writing:
            json.dump(spoiled, writing, sort_keys=True, separators=(",", ":"))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_a_delivery_this_component_did_not_mint_cannot_be_observed(self):
        with self.assertRaises(ContractRefusal) as caught:
            exchange.observation({"event_root": self.home})
        self.assertEqual(caught.exception.code, "denied")


class NoWorkerValueCrossesWithoutItsOwnShape(Home):
    """W81857 review 2026-09-04T03-43-45Z [P1]: the credential-safety boundary.

    A BYTE CEILING IS NOT A CREDENTIAL-SAFETY BOUNDARY, and that is the whole
    finding. `_decoded` accepted any bounded string for every scalar member, so
    `accepted_at`, `fault_code`, `disposition` and `manifest_digest` reached
    the status document and the sweep report as whatever the writer of those
    files chose -- and the provider shares the container identity that owns the
    event namespace, so it can be the writer.

    Every member now has a closed vocabulary or a canonical grammar, the
    ending decides which of them apply at all, and §13's durable-secret walk
    runs over the whole projection as the second line rather than the first.
    """

    def refuses(self, name, document):
        held, command = self.one()
        self.wrote(held, name, document(command))
        view = exchange.observation(held)
        self.assertEqual(view["state"], "unreadable")
        return view

    def test_a_receipt_instant_is_held_to_the_managers_own_grammar(self):
        for spoiled in ("not-an-instant", "2026-09-04 00:00:01",
                        "2026-09-04T00:00:01Z", ""):
            with self.subTest(accepted_at=spoiled):
                view = self.refuses(
                    exchange.RECEIPT_DOCUMENT,
                    lambda command: self.receipt(command,
                                                 accepted_at=spoiled))
                self.assertIsNone(view["receipt"])

    def test_a_receipt_instant_with_no_calendar_behind_it_refuses(self):
        # The grammar and the calendar are two properties and both are needed:
        # this has the shape of an instant and is not a date.
        view = self.refuses(
            exchange.RECEIPT_DOCUMENT,
            lambda command: self.receipt(
                command, accepted_at="2026-99-99T99:99:99.999Z"))
        self.assertIsNone(view["receipt"])

    def test_a_live_bearer_in_any_worker_document_cannot_cross(self):
        bearer = "worker-event-bearer-" + "9" * 40
        remember_secret(bearer)
        self.addCleanup(self.forget, bearer)
        for name, document in (
                (exchange.RECEIPT_DOCUMENT,
                 lambda command: self.receipt(command, accepted_at=bearer)),
                (exchange.TERMINAL_DOCUMENT,
                 lambda command: self.terminal(command, ending="faulted",
                                               answered=[], disposition=None,
                                               fault_code=bearer,
                                               manifest_digest=None)),
                (exchange.TERMINAL_DOCUMENT,
                 lambda command: self.terminal(command,
                                               manifest_digest=bearer))):
            with self.subTest(document=name):
                view = self.refuses(name, document)
                self.assertNotIn(bearer, json.dumps(view, sort_keys=True))

    def forget(self, bearer):
        while live_secret(bearer):
            forget_secret(bearer)

    def test_the_secret_walk_covers_a_member_no_shape_rule_reached(self):
        """§13 is the second line and it has to be able to catch on its own.

        Every scalar above is held to a shape, so the walk would never fire if
        the shapes were the only thing keeping bearers out. This drives the
        walk directly over a projection carrying a registered bearer, so the
        second line is proved to work rather than assumed.
        """
        from baton_v12.contracts import check_no_durable_secret

        bearer = "worker-projection-bearer-" + "8" * 40
        remember_secret(bearer)
        self.addCleanup(self.forget, bearer)
        with self.assertRaises(ContractRefusal) as caught:
            check_no_durable_secret({"receipt": {"accepted_at": bearer}},
                                    what="a worker exchange projection")
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_an_answered_terminal_must_name_the_envelope_it_published(self):
        for spoiled in (None, "", "not-a-digest", "sha256:" + "z" * 64,
                        "SHA256:" + "a" * 64):
            with self.subTest(manifest_digest=spoiled):
                view = self.refuses(
                    exchange.TERMINAL_DOCUMENT,
                    lambda command: self.terminal(command,
                                                  manifest_digest=spoiled))
                self.assertIsNone(view["terminal"])

    def test_an_answered_terminal_must_name_a_known_disposition(self):
        for spoiled in (None, "finished", "COMPLETED"):
            with self.subTest(disposition=spoiled):
                self.refuses(exchange.TERMINAL_DOCUMENT,
                             lambda command: self.terminal(
                                 command, disposition=spoiled))

    def test_an_answered_terminal_carries_no_fault_code(self):
        self.refuses(exchange.TERMINAL_DOCUMENT,
                     lambda command: self.terminal(command,
                                                   fault_code="agent"))

    def test_a_faulted_terminal_names_one_code_this_build_knows(self):
        for spoiled in (None, "something-went-wrong", "AGENT"):
            with self.subTest(fault_code=spoiled):
                self.refuses(exchange.TERMINAL_DOCUMENT,
                             lambda command: self.terminal(
                                 command, ending="faulted", answered=[],
                                 disposition=None, fault_code=spoiled,
                                 manifest_digest=None))

    def test_a_faulted_terminal_carries_no_disposition_or_manifest(self):
        for member in ("disposition", "manifest_digest"):
            with self.subTest(member=member):
                spoiled = {"ending": "faulted", "answered": [],
                           "disposition": None, "fault_code": "agent",
                           "manifest_digest": None}
                spoiled[member] = ("completed" if member == "disposition"
                                   else "sha256:" + "4" * 64)
                self.refuses(exchange.TERMINAL_DOCUMENT,
                             lambda command: self.terminal(command, **spoiled))

    def test_a_lost_terminal_carries_none_of_the_three(self):
        held, command = self.one()
        view = self.chain(held, command, answered=["describe"], ending="lost",
                          disposition=None, fault_code=None,
                          manifest_digest=None)
        self.assertEqual(view["state"], "lost")
        self.assertEqual(view["terminal"]["fault_code"], None)
        for member, value in (("disposition", "completed"),
                              ("fault_code", "agent"),
                              ("manifest_digest", "sha256:" + "4" * 64)):
            with self.subTest(member=member):
                spoiled = {"ending": "lost", "answered": ["describe"],
                           "disposition": None, "fault_code": None,
                           "manifest_digest": None, member: value}
                self.refuses(exchange.TERMINAL_DOCUMENT,
                             lambda command: self.terminal(command,
                                                           **spoiled))

    def test_a_state_event_outside_the_closed_vocabulary_refuses(self):
        held, command = self.one()
        self.wrote(held, exchange.state_document("describe"),
                   self.bound(command, schema=exchange.STATE_SCHEMA,
                              operation="describe",
                              operation_id=f"describe:{self.ATTEMPT}",
                              state="thinking"))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_the_positive_controls_still_project(self):
        held, command = self.one()
        view = self.chain(held, command)
        self.assertEqual(view["state"], "answered")
        self.assertEqual(view["receipt"]["accepted_at"],
                         "2026-09-04T00:00:01.000Z")
        self.assertEqual(view["terminal"]["disposition"], "completed")
        self.assertEqual(view["terminal"]["manifest_digest"],
                         "sha256:" + "4" * 64)

    def test_an_unreadable_exchange_projects_no_worker_value_at_all(self):
        held, command = self.one()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(command))
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(command, disposition="whatever-it-liked"))
        view = exchange.observation(held)
        self.assertEqual(view["state"], "unreadable")
        # NOT A PARTIAL ANSWER. One refused document makes the whole
        # projection unreadable rather than leaving the members that happened
        # to parse standing beside it, because a reader cannot tell which half
        # of a disagreement it is holding.
        self.assertIsNone(view["receipt"])
        self.assertIsNone(view["terminal"])
        self.assertEqual(view["states"], [])


class EveryWorkerDocumentIsHeldToItsOwnKind(Home):
    """W81857 review 2026-09-04T04-17-15Z [P1]: the schema discriminator.

    `schema` was in every closed member set and was compared with nothing, so a
    document explicitly identifying itself as another protocol was read as this
    one merely because it carried the right member names at the right filename.
    That is the same silent cross-generation agreement the versioned launch
    document exists to refuse, one contract down.
    """

    def refuses_schema(self, name, document):
        held, command = self.commanded()
        self.wrote(held, name, document(command))
        view = exchange.observation(held)
        self.assertEqual(view["state"], "unreadable")
        self.assertEqual(view["unreadable"]["category"], "refused")

    def test_a_receipt_from_another_protocol_is_not_this_ones(self):
        self.refuses_schema(
            exchange.RECEIPT_DOCUMENT,
            lambda command: self.receipt(
                command, schema="somebody.elses.receipt/9"))

    def test_a_state_event_from_another_protocol_is_not_this_ones(self):
        self.refuses_schema(
            exchange.state_document("describe"),
            lambda command: self.state(command, "describe", "answered")
            | {"schema": "somebody.elses.state/9"})

    def test_a_terminal_from_another_protocol_is_not_this_ones(self):
        self.refuses_schema(
            exchange.TERMINAL_DOCUMENT,
            lambda command: self.terminal(
                command, schema="somebody.elses.terminal/9"))

    def test_a_document_wearing_another_kinds_schema_refuses(self):
        """Not only a FOREIGN schema: one of this exchange's OWN, in the wrong
        file.

        The three kinds are three contracts, so a terminal that says it is a
        receipt is a document nobody in this protocol wrote either.
        """
        self.refuses_schema(
            exchange.TERMINAL_DOCUMENT,
            lambda command: self.terminal(
                command, schema=exchange.RECEIPT_SCHEMA))

    def test_the_pinned_schemas_are_what_each_document_must_say(self):
        held, command = self.commanded()
        view = self.chain(held, command)
        self.assertEqual(view["state"], "answered")
        self.assertEqual(
            (exchange.RECEIPT_SCHEMA, exchange.STATE_SCHEMA,
             exchange.TERMINAL_SCHEMA),
            ("baton.worker-exchange.receipt/1",
             "baton.worker-exchange.state/1",
             "baton.worker-exchange.terminal/1"))


class ATerminalNeedsTheSequenceThatProducedIt(Home):
    """W81857 review 2026-09-04T04-17-15Z [P1]: the causal chain.

    The receipt, the states and the terminal were read independently, so a
    worker or provider that wrote ONLY an answered terminal skipped the
    pre-dispatch replay fence and every per-operation event and was still
    projected as a successful answer. The receipt is the one document that must
    not be forgeable alone: it is the durable proof that dispatch was fenced
    BEFORE any provider ran.
    """

    def test_an_answered_terminal_with_no_receipt_is_not_an_answer(self):
        held, command = self.commanded()
        for operation in exchange.OPERATIONS:
            self.wrote(held, exchange.state_document(operation),
                       self.state(command, operation, "answered"))
        self.wrote(held, exchange.TERMINAL_DOCUMENT, self.terminal(command))
        view = exchange.observation(held)
        self.assertEqual(view["state"], "unreadable")
        self.assertIsNone(view["terminal"])

    def test_a_faulted_terminal_with_no_receipt_is_not_a_fault_either(self):
        held, command = self.commanded()
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(command, ending="faulted", answered=[],
                                 disposition=None, fault_code="agent",
                                 manifest_digest=None))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_an_answered_operation_with_no_state_event_refuses(self):
        held, command = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(command))
        self.wrote(held, exchange.state_document("describe"),
                   self.state(command, "describe", "answered"))
        self.wrote(held, exchange.TERMINAL_DOCUMENT, self.terminal(command))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_an_answered_operation_still_dispatched_refuses(self):
        """The reordering control: a terminal ahead of its own evidence."""
        held, command = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(command))
        self.wrote(held, exchange.state_document("describe"),
                   self.state(command, "describe", "answered"))
        self.wrote(held, exchange.state_document("work"),
                   self.state(command, "work", "dispatched"))
        self.wrote(held, exchange.TERMINAL_DOCUMENT, self.terminal(command))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_a_faulted_terminal_names_the_operation_it_stopped_on(self):
        held, command = self.commanded()
        view = self.chain(held, command, answered=["describe"],
                          ending="faulted", stopped="work",
                          disposition=None, fault_code="agent",
                          manifest_digest=None)
        self.assertEqual(view["state"], "faulted")

    def test_a_faulted_terminal_whose_stop_says_nothing_refuses(self):
        held, command = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(command))
        self.wrote(held, exchange.state_document("describe"),
                   self.state(command, "describe", "answered"))
        self.wrote(held, exchange.state_document("work"),
                   self.state(command, "work", "dispatched"))
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(command, ending="faulted",
                                 answered=["describe"], disposition=None,
                                 fault_code="agent", manifest_digest=None))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_a_faulted_terminal_answering_everything_refuses(self):
        """A fault happened to one of them; a fault that happened to none is
        not one."""
        held, command = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(command))
        for operation in exchange.OPERATIONS:
            self.wrote(held, exchange.state_document(operation),
                       self.state(command, operation, "answered"))
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(command, ending="faulted",
                                 answered=list(exchange.OPERATIONS),
                                 disposition=None, fault_code="agent",
                                 manifest_digest=None))
        view = exchange.observation(held)
        self.assertEqual(view["state"], "unreadable")

    def test_no_impossible_state_tail_is_accepted(self):
        """W81857 review 2026-09-04T04-31-34Z [P1]: the exact reachable vector.

        The first correction required the answered prefix and rejected only a
        later `answered` state, which left every OTHER impossible tail
        acceptable. Each of these is a history the reference worker cannot
        publish, and "the parts I checked agree" is not the same claim as
        "this is a history".
        """
        cases = (
            # `work` reached before `describe` ever completed.
            ("later-operation-before-prefix",
             {"ending": "lost", "answered": [],
              "states": {"work": "dispatched"}}),
            # Loss claimed beside a positively observed fault. Loss is the
            # ABSENCE of an observation; a worker that saw a fault saw one.
            ("lost-but-fault-observed",
             {"ending": "lost", "answered": [],
              "states": {"describe": "faulted"}}),
            # Loss claimed after the whole sequence is positively answered.
            ("lost-after-every-operation-answered",
             {"ending": "lost", "answered": list(exchange.OPERATIONS),
              "states": {"describe": "answered", "work": "answered"}}),
            # An operation reached after the sequence already stopped faulted.
            ("state-after-fault",
             {"ending": "faulted", "answered": [],
              "states": {"describe": "faulted", "work": "dispatched"}}),
            # A faulted ending that answers everything: a fault happened to
            # one of them.
            ("faulted-after-every-operation-answered",
             {"ending": "faulted", "answered": list(exchange.OPERATIONS),
              "states": {"describe": "answered", "work": "answered"}}),
            # The prefix itself only half-published.
            ("answered-prefix-still-dispatched",
             {"ending": "faulted", "answered": ["describe"],
              "states": {"describe": "dispatched", "work": "faulted"}}),
        )
        for name, held in cases:
            with self.subTest(case=name):
                view = self.spoiled(held)
                self.assertEqual(view["state"], "unreadable")
                self.assertIsNone(view["terminal"])
                self.assertEqual(view["states"], [])

    def spoiled(self, held):
        """One receipt, one hand-composed state map, one terminal."""
        delivery, command = self.one()
        for operation in exchange.OPERATIONS:
            place = os.path.join(delivery.event_root,
                                 exchange.state_document(operation))
            if os.path.lexists(place):
                os.chmod(place, 0o644)
                os.unlink(place)
        self.wrote(delivery, exchange.RECEIPT_DOCUMENT, self.receipt(command))
        for operation, state in held["states"].items():
            self.wrote(delivery, exchange.state_document(operation),
                       self.state(command, operation, state))
        self.wrote(delivery, exchange.TERMINAL_DOCUMENT,
                   self.terminal(command, ending=held["ending"],
                                 answered=held["answered"],
                                 disposition=None,
                                 fault_code=("agent"
                                             if held["ending"] == "faulted"
                                             else None),
                                 manifest_digest=None))
        return exchange.observation(delivery)

    def test_every_legitimate_crash_boundary_is_a_readable_loss(self):
        """The positive half: `lost` is the honest answer at real boundaries.

        A process that died before publishing `dispatched` leaves no event for
        the operation it was about to reach; one that died after publishing it
        and before the answer leaves exactly that event. Both are real, and a
        rule strict enough to refuse the contradictions above must still accept
        these or it refuses the states the transport exists to survive.
        """
        cases = (
            ("died-before-the-first-dispatch", [], {}),
            ("died-inside-the-first-operation", [],
             {"describe": "dispatched"}),
            ("died-between-the-two-operations", ["describe"],
             {"describe": "answered"}),
            ("died-inside-the-second-operation", ["describe"],
             {"describe": "answered", "work": "dispatched"}),
        )
        for name, answered, states in cases:
            with self.subTest(case=name):
                view = self.spoiled({"ending": "lost", "answered": answered,
                                     "states": states})
                self.assertEqual(view["state"], "lost")
                self.assertEqual(view["terminal"]["ending"], "lost")

    def test_every_legitimate_fault_boundary_is_a_readable_fault(self):
        for name, answered, states in (
                ("faulted-on-the-first-operation", [],
                 {"describe": "faulted"}),
                ("faulted-on-the-second", ["describe"],
                 {"describe": "answered", "work": "faulted"})):
            with self.subTest(case=name):
                view = self.spoiled({"ending": "faulted",
                                     "answered": answered, "states": states})
                self.assertEqual(view["state"], "faulted")
                self.assertEqual(view["terminal"]["fault_code"], "agent")

    def test_an_answered_terminal_has_the_whole_answered_vector(self):
        view = self.spoiled({"ending": "answered",
                             "answered": list(exchange.OPERATIONS),
                             "states": {"describe": "answered",
                                        "work": "answered"}})
        # The digest and disposition rules refuse this one for their own
        # reasons -- `spoiled` composes a null pair -- so what is asserted here
        # is the vector rule's own positive control through `chain`.
        self.assertEqual(view["state"], "unreadable")
        delivery, command = self.one()
        self.assertEqual(self.chain(delivery, command)["state"], "answered")

    def test_a_terminal_disowning_an_operation_its_events_answered_refuses(self):
        held, command = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(command))
        for operation in exchange.OPERATIONS:
            self.wrote(held, exchange.state_document(operation),
                       self.state(command, operation, "answered"))
        self.wrote(held, exchange.TERMINAL_DOCUMENT,
                   self.terminal(command, ending="lost",
                                 answered=["describe"], disposition=None,
                                 fault_code=None, manifest_digest=None))
        self.assertEqual(exchange.observation(held)["state"], "unreadable")

    def test_a_receipt_alone_is_still_working_and_not_an_ending(self):
        held, command = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(command))
        view = exchange.observation(held)
        self.assertEqual(view["state"], "working")
        self.assertIsNone(view["terminal"])


class TheTeardownWalksWhatTheWorkerWrote(Home):
    """`launch.discard` removes names it wrote; this removes names it did not.

    The event namespace is writable by the container, so the entries under it
    are DYNAMIC. A flat by-name loop cannot remove them and a recursive
    `rmtree` would follow whatever a worker pointed at.
    """

    def test_dynamic_worker_entries_are_removed_with_the_delivery(self):
        delivered = self.delivered()
        held, document = self.commanded(delivered.exchange)
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(document))
        with open(os.path.join(held.event_root, "whatever"), "w",
                  encoding="utf-8") as writing:
            writing.write("worker material")
        self.assertTrue(launch.discard(delivered.root))
        self.assertFalse(os.path.lexists(delivered.root))

    def test_a_link_in_the_event_namespace_is_unlinked_and_not_followed(self):
        delivered = self.delivered()
        outside = os.path.join(self.home, "keep-me")
        with open(outside, "w", encoding="utf-8") as writing:
            writing.write("not the delivery's")
        os.symlink(outside,
                   os.path.join(delivered.exchange.event_root, "pointer"))
        self.assertTrue(launch.discard(delivered.root))
        self.assertTrue(os.path.exists(outside))


class TheWorkerIsTheOtherEnd(Home):
    """The real in-image program, driven over a real exchange on disk.

    NOT A SECOND IMPLEMENTATION OF THE PROTOCOL. `baton_worker` cannot import
    this package -- that is the isolation rule the image is built on -- so the
    two ends carry two copies of the same constants, and these cases are what
    hold them together.
    """

    def setUp(self):
        super().setUp()
        from .test_worker_image import staged

        self.inputs, self.outputs = staged(self)

    def worker(self, delivery, agent=None, seen=None):
        import baton_worker
        from scripted_agent import ScriptedAgent

        return baton_worker.serve_exchange(
            ScriptedAgent() if agent is None else agent,
            seen if seen is not None else self.launched(),
            self.SESSION, delivery.command_root, delivery.event_root)

    def launched(self):
        return {"schema": launch.EXCHANGE_SCHEMA, "session": self.SESSION,
                "contract": "do the thing", "role": "implementation",
                "transport": exchange.EXCHANGE_TRANSPORT}

    def test_the_two_ends_agree_about_every_constant(self):
        import baton_worker

        self.assertEqual(baton_worker.EXCHANGE_TRANSPORT,
                         exchange.EXCHANGE_TRANSPORT)
        self.assertEqual(baton_worker.EXCHANGE_LAUNCH_SCHEMA,
                         launch.EXCHANGE_SCHEMA)
        self.assertEqual(baton_worker.EXCHANGE_LAUNCH_MEMBERS,
                         launch.EXCHANGE_MEMBERS)
        self.assertEqual(baton_worker.COMMAND_ROOT, exchange.COMMAND_TARGET)
        self.assertEqual(baton_worker.EVENT_ROOT, exchange.EVENT_TARGET)
        self.assertEqual(baton_worker.COMMAND_SCHEMA, exchange.COMMAND_SCHEMA)
        self.assertEqual(baton_worker.RECEIPT_SCHEMA, exchange.RECEIPT_SCHEMA)
        self.assertEqual(baton_worker.STATE_SCHEMA, exchange.STATE_SCHEMA)
        self.assertEqual(baton_worker.TERMINAL_SCHEMA,
                         exchange.TERMINAL_SCHEMA)
        self.assertEqual(baton_worker.COMMAND_MEMBERS,
                         exchange.COMMAND_MEMBERS)
        self.assertEqual(baton_worker.EXCHANGE_ENDINGS, exchange.ENDINGS)
        self.assertEqual(baton_worker.EXCHANGE_STATES, exchange.STATES)
        self.assertEqual(baton_worker.RECEIPT_DOCUMENT,
                         exchange.RECEIPT_DOCUMENT)
        self.assertEqual(baton_worker.TERMINAL_DOCUMENT,
                         exchange.TERMINAL_DOCUMENT)

    def test_one_command_reaches_the_provider_and_answers_the_manager(self):
        held, _document = self.commanded()
        self.assertEqual(self.worker(held), 0)
        view = exchange.observation(held)
        self.assertEqual(view["state"], "answered")
        self.assertEqual(view["terminal"]["ending"], "answered")
        self.assertEqual(view["terminal"]["disposition"], "completed")
        self.assertEqual(view["terminal"]["answered"], ["describe", "work"])
        self.assertEqual([one["state"] for one in view["states"]],
                         ["answered", "answered"])
        self.assertTrue(os.path.exists(
            os.path.join(self.outputs, "output.json")))

    def test_the_terminal_names_the_completion_envelope_it_published(self):
        held, _document = self.commanded()
        self.worker(held)
        with open(os.path.join(self.outputs, "output.json"),
                  encoding="utf-8") as reading:
            published = json.load(reading)
        self.assertEqual(exchange.observation(held)["terminal"]
                         ["manifest_digest"], published["manifest_digest"])

    def test_the_receipt_is_published_before_the_provider_is_dispatched(self):
        held, _document = self.commanded()
        seen = []

        class Watching:
            def work(inner, launched, declared):
                seen.append(sorted(os.listdir(held.event_root)))
                raise RuntimeError("stop here")

            def consider(inner, launched, request):
                raise AssertionError("not this runtime's operation")

        self.worker(held, agent=Watching())
        self.assertIn(exchange.RECEIPT_DOCUMENT, seen[0])

    def test_a_second_worker_over_one_receipt_starts_no_second_turn(self):
        held, _document = self.commanded()
        calls = []

        class Counting:
            def work(inner, launched, declared):
                calls.append(1)
                return {"disposition": "completed", "outputs": [], "recap": ""}

            def consider(inner, launched, request):
                raise AssertionError("not this runtime's operation")

        self.worker(held, agent=Counting())
        self.worker(held, agent=Counting())
        self.worker(held, agent=Counting())
        self.assertEqual(len(calls), 1)

    def test_a_worker_re_entering_after_a_receipt_alone_claims_nothing(self):
        held, document = self.commanded()
        self.wrote(held, exchange.RECEIPT_DOCUMENT, self.receipt(document))
        calls = []

        class Counting:
            def work(inner, launched, declared):
                calls.append(1)
                return {"disposition": "completed", "outputs": [], "recap": ""}

            def consider(inner, launched, request):
                raise AssertionError("not this runtime's operation")

        # 4 IS "THE SEQUENCE IS ACCEPTED AND UNFINISHED", not `lost`. Claiming
        # loss would be claiming an observation this side does not have: the
        # provider a previous incarnation started may still be running, and
        # only the manager's own runtime observation can decide.
        self.assertEqual(self.worker(held, agent=Counting()), 4)
        self.assertEqual(calls, [])
        self.assertIsNone(exchange.observation(held)["terminal"])

    def test_an_agent_failure_is_faulted_and_carries_no_diagnostic(self):
        held, _document = self.commanded()

        class Exploding:
            def work(inner, launched, declared):
                raise RuntimeError("a path from inside the image")

            def consider(inner, launched, request):
                raise AssertionError("not this runtime's operation")

        self.assertEqual(self.worker(held, agent=Exploding()), 1)
        view = exchange.observation(held)
        self.assertEqual(view["state"], "faulted")
        self.assertEqual(view["terminal"]["fault_code"], "agent")
        self.assertNotIn("a path from inside the image",
                         json.dumps(view, sort_keys=True))

    def test_a_command_naming_another_session_is_refused_before_dispatch(self):
        held, _document = self.commanded(session="somebody-elses")
        calls = []

        class Counting:
            def work(inner, launched, declared):
                calls.append(1)
                return {"disposition": "completed", "outputs": [], "recap": ""}

            def consider(inner, launched, request):
                raise AssertionError("not this runtime's operation")

        self.assertEqual(self.worker(held, agent=Counting()), 2)
        self.assertEqual(calls, [])
        self.assertEqual(sorted(os.listdir(held.event_root)), [])

    def test_a_writable_command_namespace_is_refused_by_the_worker(self):
        held, _document = self.commanded()
        os.chmod(held.command_root, 0o755)
        os.chmod(os.path.join(held.command_root,
                              exchange.sequence_of(self.ATTEMPT) + ".json"),
                 0o644)
        self.assertEqual(self.worker(held), 2)
        self.assertEqual(sorted(os.listdir(held.event_root)), [])

    def test_the_worker_waits_for_a_command_rather_than_inventing_one(self):
        import baton_worker

        delivered = self.delivered()
        waits = []

        def sleeping(seconds):
            waits.append(seconds)
            if len(waits) == 2:
                # THE COMMAND ARRIVES AFTER THE CONTAINER IS UP, which is what
                # makes its publication a level-triggered manager act rather
                # than a launch-time one.
                self.commanded(delivered.exchange)

        self.assertEqual(
            baton_worker.serve_exchange(
                _CountingAgent(), self.launched(), self.SESSION,
                delivered.exchange.command_root,
                delivered.exchange.event_root, sleep=sleeping),
            0)
        self.assertEqual(len(waits), 2)
        self.assertEqual(exchange.observation(delivered.exchange)["state"],
                         "answered")

    def test_an_ordinary_worker_publication_failure_leaves_no_staging(self):
        """W81857 review 2026-09-04T04-17-15Z [P2], the worker half.

        The same audit the manager's publisher got: one cleanup boundary over
        everything after the create, so a transient failure at ANY step leaves
        no residue in the namespace the manager scans.

        BOTH INJECTIONS, and re-review 2026-09-04T04-31-34Z is why. The
        preceding package claimed write- and sync-failure cases "at both ends"
        and the worker half injected only `fsync`; the implementation was
        already correct, so what was wrong was the accounting. A claim about
        coverage is checked by the coverage existing.
        """
        for step, name, failure in (("sync", "fsync", self.failing_sync),
                                    ("write", "write", self.failing_write)):
            with self.subTest(step=step):
                held, _document = self.commanded(
                    self.delivered(attempt_id="attempt-" + step).exchange)
                original = getattr(os, name)
                setattr(os, name, failure)
                try:
                    with self.assertRaises(OSError):
                        self.worker(held)
                finally:
                    setattr(os, name, original)
                self.assertEqual(sorted(os.listdir(held.event_root)), [])

    @staticmethod
    def failing_sync(descriptor):
        raise OSError("injected fsync failure")

    @staticmethod
    def failing_write(descriptor, payload):
        # A PARTIAL WRITE FIRST, so the staging file exists and is non-empty
        # when the failure lands -- an empty one would be removed by a weaker
        # unwind too, and would prove less.
        os.pwrite(descriptor, payload[:8], 0)
        raise OSError("injected write failure")

    def test_a_crash_created_staging_file_does_not_wedge_the_worker(self):
        """W81857 review [P1], the worker half of the publication wedge.

        A death between creating the staging file and renaming it left a file
        under the one fixed `.publishing` name, and every later incarnation of
        this program then failed `O_EXCL` on its very first publication -- the
        receipt -- so no turn could ever be begun again.
        """
        held, _document = self.commanded()
        stranded = os.path.join(held.event_root,
                                "." + exchange.RECEIPT_DOCUMENT
                                + ".publishing")
        with open(stranded, "wb") as writing:
            writing.write(b"a partial receipt nobody finished")
        self.assertEqual(self.worker(held), 0)
        self.assertEqual(exchange.observation(held)["state"], "answered")

    def test_the_worker_leaves_no_staging_name_behind(self):
        held, _document = self.commanded()
        self.worker(held)
        self.assertEqual([one for one in os.listdir(held.event_root)
                          if one.startswith(".")], [])

    def test_an_answered_terminal_names_the_digest_the_manager_reads(self):
        """The correlation the terminal member exists to provide, end to end.

        The manager holds this to a canonical sha256 grammar and then compares
        it with the digest its own validation of `/output/output.json`
        produced, so a worker that published anything else would be refused
        rather than believed.
        """
        held, _document = self.commanded()
        self.worker(held)
        with open(os.path.join(self.outputs, "output.json"),
                  encoding="utf-8") as reading:
            published = json.load(reading)
        view = exchange.observation(held)
        self.assertEqual(view["terminal"]["manifest_digest"],
                         published["manifest_digest"])
        self.assertRegex(view["terminal"]["manifest_digest"],
                         r"\Asha256:[0-9a-f]{64}\Z")

    def test_an_answer_with_no_readable_envelope_is_faulted_not_answered(self):
        """A turn that cannot name its own completion envelope has not
        answered.

        Publishing `answered` with a null digest would be asking the manager to
        accept a correlation this program could not make -- and the manager
        refuses exactly that, so the honest report is a fault.
        """
        held, _document = self.commanded()
        self.assertEqual(self.faulted_envelope(held), 1)
        view = exchange.observation(held)
        self.assertEqual(view["state"], "faulted")
        self.assertEqual(view["terminal"]["fault_code"], "output")
        self.assertIsNone(view["terminal"]["manifest_digest"])

    def faulted_envelope(self, held):
        """Run the worker with its completion envelope made unreadable.

        The envelope is published by `publish_completion` and read back by
        `_published_manifest_digest`; replacing the read with one that finds
        nothing is the smallest way to reach the branch without corrupting a
        document the freeze would independently reject anyway.
        """
        import baton_worker

        original = baton_worker._published_manifest_digest
        baton_worker._published_manifest_digest = lambda: None
        try:
            return self.worker(held)
        finally:
            baton_worker._published_manifest_digest = original

    def test_a_launch_document_selecting_no_transport_uses_stdin(self):
        import io

        import baton_worker

        held, _document = self.commanded()
        place = os.path.join(self.home, "launch.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump({"schema": launch.LAUNCH_SCHEMA,
                       "session": self.SESSION, "contract": "c",
                       "role": "implementation"}, writing)
        os.chmod(place, 0o444)
        # A CLOSED STDIN IS THE MANAGER CLOSING THE CHANNEL, so the framing
        # loop ends at once -- and the exchange beside it is untouched, because
        # a worker that picked its transport from the filesystem would be a
        # worker with two live contracts and no version.
        self.assertEqual(
            baton_worker.serve(io.BytesIO(b""), io.BytesIO(),
                               _CountingAgent(), place, held.command_root,
                               held.event_root), 0)
        self.assertEqual(sorted(os.listdir(held.event_root)), [])

    def test_a_launch_document_naming_an_unknown_transport_is_latched(self):
        import io

        import baton_worker

        held, _document = self.commanded()
        place = os.path.join(self.home, "launch.json")
        with open(place, "w", encoding="utf-8") as writing:
            json.dump({"schema": launch.EXCHANGE_SCHEMA,
                       "session": self.SESSION, "contract": "c",
                       "role": "implementation",
                       "transport": "baton.worker-exchange/2"}, writing)
        os.chmod(place, 0o444)
        self.assertEqual(
            baton_worker.serve(io.BytesIO(b""), io.BytesIO(),
                               _CountingAgent(), place, held.command_root,
                               held.event_root), 1)
        self.assertEqual(sorted(os.listdir(held.event_root)), [])


class _CountingAgent:
    """A provider that produces the declared output and records the ask.

    IT DELEGATES TO THE FIXTURE AGENT rather than answering `outputs: []`,
    because the worker holds an agent's answer against the manager's own
    declarations: a provider that answered a REQUIRED output away would be
    settling its own attempt, and the worker refuses that before the frame is
    written. A counting agent that could not satisfy the declarations would be
    measuring a fault path while claiming to measure a successful one.
    """

    def __init__(self):
        from scripted_agent import ScriptedAgent

        self.calls = []
        self._agent = ScriptedAgent()

    def work(self, launched, declared):
        self.calls.append(1)
        return self._agent.work(launched, declared)

    def consider(self, launched, request):
        raise AssertionError("not this runtime's operation")


class TheOptionalActivityDocument(Home):
    """W61599: the liveness count, on its own name under its own schema.

    WHY IT IS NOT A MEMBER OF `state-work.json`. That document is published
    TWICE around the provider and its member set is closed and text-only, so a
    periodic writer sharing it would race the terminal causality every other
    case in this file depends on AND change the wire. Everything here holds the
    separate document to the same discipline the four lifecycle documents get:
    closed members, schema identity, exact binding, and a count no worker may
    make this manager believe.
    """

    def expected(self, delivery=None):
        held = delivery if delivery is not None else self.one()[0]
        return exchange.activity_identities(held, session=self.SESSION)

    def activity(self, document, **overrides):
        held = self.bound(document, schema=exchange.ACTIVITY_SCHEMA,
                          operation="work",
                          operation_id=f"work:{self.ATTEMPT}",
                          bytes_observed=4096)
        held.update(overrides)
        return held

    def test_the_lifecycle_documents_did_not_move(self):
        """THE COMPATIBILITY CLAIM, asserted rather than argued. A new document
        beside the old ones is only backward compatible if the old ones are
        byte-identical, which is exactly what an added member would have
        broken."""
        self.assertEqual(exchange.STATE_SCHEMA,
                         "baton.worker-exchange.state/1")
        self.assertEqual(exchange.STATE_MEMBERS,
                         ("schema", "session", "attempt_id", "sequence_id",
                          "command_digest", "operation", "operation_id",
                          "state"))
        self.assertEqual(exchange.RECEIPT_MEMBERS,
                         ("schema", "session", "attempt_id", "sequence_id",
                          "command_digest", "accepted_at"))
        self.assertNotIn("bytes_observed", exchange.STATE_MEMBERS)
        self.assertNotIn("bytes_observed", exchange.TERMINAL_MEMBERS)

    def test_an_absent_document_is_unknown_and_never_a_zero(self):
        """NEW MANAGER, OLD WORKER. Nothing is published, and absence means
        exactly what a never-observed attempt already meant."""
        held, _document = self.one()
        self.assertIsNone(exchange.observed_activity(held,
                                                     self.expected(held)))

    def test_a_bound_count_is_read(self):
        held, document = self.one()
        self.wrote(held, exchange.ACTIVITY_DOCUMENT, self.activity(document))
        self.assertEqual(exchange.observed_activity(held, self.expected(held)),
                         4096)

    def test_the_document_is_not_reported_as_a_foreign_entry(self):
        """OLD MANAGER, NEW WORKER is the other pairing, and this is the half
        a conforming manager owes: an entry in its own closed vocabulary is not
        something a container is doing outside the contract."""
        held, document = self.one()
        self.wrote(held, exchange.ACTIVITY_DOCUMENT, self.activity(document))
        self.assertIn(exchange.ACTIVITY_DOCUMENT, exchange.EVENT_DOCUMENTS)
        self.assertEqual(exchange.observation(held)["foreign"], [])

    def test_the_whole_namespace_still_fits_the_entry_budget(self):
        """THE PART THAT COULD ACTUALLY BITE. More than `MAX_EVENT_ENTRIES`
        does not truncate one document -- it makes the manager refuse to
        enumerate the namespace at all -- so the accounting is asserted with
        the worker's one staging temporary present."""
        held, document = self.one()
        self.chain(held, document)
        self.wrote(held, exchange.ACTIVITY_DOCUMENT, self.activity(document))
        with open(os.path.join(held.event_root, ".activity.json.tmp"),
                  "w", encoding="utf-8") as writing:
            writing.write("{}")
        entries = sorted(os.listdir(held.event_root))
        self.assertEqual(len(entries), exchange.ACTIVITY_NAMESPACE_ENTRIES)
        self.assertLessEqual(len(entries), exchange.MAX_EVENT_ENTRIES)
        self.assertEqual(exchange.observation(held)["foreign"],
                         [".activity.json.tmp"])

    def test_a_count_for_another_turn_is_discarded(self):
        held, document = self.one()
        for member, spoiled in (("session", "somebody-elses"),
                                ("attempt_id", "attempt-2"),
                                ("sequence_id", "sequence-other"),
                                ("command_digest", "sha256:" + "9" * 64),
                                ("operation", "describe"),
                                ("operation_id", "work:attempt-2")):
            with self.subTest(member=member):
                self.wrote(held, exchange.ACTIVITY_DOCUMENT,
                           self.activity(document, **{member: spoiled}))
                with self.assertRaises(ContractRefusal) as caught:
                    exchange.observed_activity(held, self.expected(held))
                # `refused` AND NOT `integrity`: the least trusted program in
                # the deployment wrote something outside its contract, which
                # is a different answer to an operator from this build
                # disagreeing with its own durable state.
                self.assertEqual(caught.exception.category, "refused")

    def test_a_hostile_count_is_refused_by_this_parser_alone(self):
        held, document = self.one()
        for value in (-1, True, False, 1.5, "4096", None, [4096],
                      exchange.MAX_ACTIVITY_BYTES + 1):
            with self.subTest(value=value):
                self.wrote(held, exchange.ACTIVITY_DOCUMENT,
                           self.activity(document, bytes_observed=value))
                with self.assertRaises(ContractRefusal):
                    exchange.observed_activity(held, self.expected(held))
        # AND THE CEILING ITSELF IS ADMITTED, so the refusal above is a bound
        # rather than an off-by-one that refuses every large count.
        self.wrote(held, exchange.ACTIVITY_DOCUMENT,
                   self.activity(document,
                                 bytes_observed=exchange.MAX_ACTIVITY_BYTES))
        self.assertEqual(exchange.observed_activity(held, self.expected(held)),
                         exchange.MAX_ACTIVITY_BYTES)

    def test_no_existing_parser_learned_to_accept_an_integer(self):
        """THE RELAXATION THAT DID NOT HAPPEN, asked of the parser itself.

        A CASE DRIVEN THROUGH `observation` CANNOT ANSWER THIS. Every member of
        every lifecycle document has a second guard -- a closed vocabulary, a
        canonical grammar or the correlation -- so a document carrying an
        integer is refused whether or not the decoder still holds its members
        to bounded text, and a test that only watched the outcome would go on
        passing with the decoder wide open. So the decoder is asked directly:
        the `numeric` opt-in is named by the activity parser and by nothing
        else, and without it an integer is refused exactly as it was before
        this document existed.
        """
        for members, member in ((exchange.RECEIPT_MEMBERS, "accepted_at"),
                                (exchange.STATE_MEMBERS, "state"),
                                (exchange.TERMINAL_MEMBERS, "ending"),
                                (exchange.ACTIVITY_MEMBERS, "operation")):
            with self.subTest(member=member):
                raw = json.dumps({one: (4096 if one == member else "x")
                                  for one in members}).encode("utf-8")
                with self.assertRaises(ContractRefusal):
                    exchange._decoded(raw, "whatever.json", what="a document",
                                      members=members)
        # AND THE OPT-IN ADMITS EXACTLY THE ONE MEMBER THAT NAMES IT.
        raw = json.dumps({one: (4096 if one == "bytes_observed" else "x")
                          for one in exchange.ACTIVITY_MEMBERS}).encode("utf-8")
        self.assertEqual(
            exchange._decoded(raw, exchange.ACTIVITY_DOCUMENT,
                              what="a worker activity count",
                              members=exchange.ACTIVITY_MEMBERS,
                              numeric=("bytes_observed",))["bytes_observed"],
            4096)
        # AND THE DOCUMENT AS A WHOLE IS STILL REFUSED WITH THE OPT-IN AWAY.
        with self.assertRaises(ContractRefusal):
            exchange._decoded(raw, exchange.ACTIVITY_DOCUMENT,
                              what="a worker activity count",
                              members=exchange.ACTIVITY_MEMBERS)

    def test_a_document_from_another_protocol_is_not_read(self):
        held, document = self.one()
        self.wrote(held, exchange.ACTIVITY_DOCUMENT,
                   self.activity(document, schema="baton.something-else/1"))
        with self.assertRaises(ContractRefusal):
            exchange.observed_activity(held, self.expected(held))

    def test_an_extra_or_missing_member_is_refused(self):
        """A CLOSED SET, not an allowlist. An extra member is how a second
        contract alias arrives from a program this manager does not trust."""
        held, document = self.one()
        extra = self.activity(document)
        extra["also"] = "x"
        missing = self.activity(document)
        del missing["operation_id"]
        for spoiled, what in ((extra, "extra"), (missing, "missing")):
            with self.subTest(what=what):
                self.wrote(held, exchange.ACTIVITY_DOCUMENT, spoiled)
                with self.assertRaises(ContractRefusal):
                    exchange.observed_activity(held, self.expected(held))

    def test_a_link_at_the_fixed_name_is_refused_rather_than_resolved(self):
        held, _document = self.one()
        outside = os.path.join(self.home, "elsewhere.json")
        with open(outside, "w", encoding="utf-8") as writing:
            writing.write("{}")
        os.symlink(outside,
                   os.path.join(held.event_root, exchange.ACTIVITY_DOCUMENT))
        with self.assertRaises(ContractRefusal):
            exchange.observed_activity(held, self.expected(held))

    def test_a_terminal_operation_is_skipped_rather_than_read(self):
        """OWNER M174788's SEMANTICS, and the boundary it is NOT. The terminal
        check is a cheap skip so most late work never happens; it is not
        claimed to eliminate a write already in flight, and nothing here
        changes a terminal state."""
        held, document = self.one()
        self.wrote(held, exchange.ACTIVITY_DOCUMENT, self.activity(document))
        self.assertEqual(exchange.observed_activity(held, self.expected(held)),
                         4096)
        self.chain(held, document)
        self.assertIsNone(exchange.observed_activity(held,
                                                     self.expected(held)))

    def test_the_expectation_comes_from_this_managers_own_command(self):
        """SIX WIRE IDENTITIES, NONE OF THEM TAKEN FROM THE DOCUMENT. Five are
        derived by rule and the sixth is the digest of the bytes this manager
        published, read back from the namespace the container holds
        read-only."""
        held, _document = self.one()
        expected = self.expected(held)
        self.assertEqual(sorted(expected), ["attempt_id", "command_digest",
                                            "operation", "operation_id",
                                            "sequence_id", "session"])
        self.assertEqual(expected["attempt_id"], self.ATTEMPT)
        self.assertEqual(expected["sequence_id"],
                         exchange.sequence_of(self.ATTEMPT))
        self.assertEqual(expected["operation"], "work")
        self.assertEqual(expected["operation_id"],
                         exchange.worker_operation_id(self.ATTEMPT, "work"))
        self.assertEqual(
            expected["command_digest"],
            exchange.observation(held)["command"]["command_digest"])

    def test_an_undispatched_attempt_has_nothing_to_expect(self):
        delivered = self.delivered(attempt_id="attempt-9")
        self.assertIsNone(
            exchange.activity_identities(delivered.exchange,
                                         session=self.SESSION))

    def test_a_command_naming_another_session_refuses_the_expectation(self):
        delivered = self.delivered(attempt_id="attempt-8",
                                   session="somebody-elses")
        held, _document = self.commanded(delivered.exchange,
                                         session="somebody-elses")
        with self.assertRaises(ContractRefusal):
            exchange.activity_identities(held, session=self.SESSION)


def _ActivityPublisherOver(baton_worker, held, case, observe):
    """One real publisher bound to this delivery, over an injected observer.

    W61599. The publisher's operands are `serve_exchange`'s, and composing them
    here is how a case can drive the real thread without a provider turn
    standing between it and the file.
    """
    from baton_v12.worker_manager import exchange as _exchange

    return baton_worker._ActivityPublisher(
        held.event_root,
        baton_worker._bound(
            {"session": case.SESSION, "attempt_id": held.attempt_id,
             "sequence_id": _exchange.sequence_of(held.attempt_id)},
            _exchange.observation(held)["command"]["command_digest"],
            operation="work",
            operation_id=_exchange.worker_operation_id(held.attempt_id,
                                                       "work")),
        observe, seconds=0.01)


class TheWorkerPublishesTheOptionalCount(Home):
    """W61599 at the OTHER end: the real in-image publisher, on real files.

    NOT A SECOND IMPLEMENTATION. `baton_worker` cannot import this package, so
    these cases drive the actual program against an actual delivery and read
    the result back through the manager's own parser -- which is the only way
    two copies of one contract are held together.
    """

    def setUp(self):
        super().setUp()
        from .test_worker_image import staged

        self.inputs, self.outputs = staged(self)

    def launched(self):
        return {"schema": launch.EXCHANGE_SCHEMA, "session": self.SESSION,
                "contract": "do the thing", "role": "implementation",
                "transport": exchange.EXCHANGE_TRANSPORT}

    def worker(self, delivery, agent):
        import baton_worker

        return baton_worker.serve_exchange(agent, self.launched(),
                                           self.SESSION,
                                           delivery.command_root,
                                           delivery.event_root)

    def observing(self, totals, *, seen=None):
        """A provider-shaped agent whose native stream grows while it works."""
        from scripted_agent import ScriptedAgent

        held = list(totals)
        inner = ScriptedAgent()
        watched = [] if seen is None else seen

        class Observing:
            def work(self, launched, declared):
                # THE COUNT MOVES WHILE THE TURN IS STILL RUNNING, which is the
                # whole property: an operator must be able to see growth BEFORE
                # completion rather than only after it.
                while len(held) > 1:
                    self._await()
                    held.pop(0)
                return inner.work(launched, declared)

            def _await(self):
                import time

                for _ in range(200):
                    if watched and watched[-1] == held[0]:
                        return
                    time.sleep(0.01)

            def observed_activity(self):
                total = held[0]
                watched.append(total)
                return total

            def consider(self, launched, request):
                raise AssertionError("not this runtime's operation")

        return Observing()

    def test_the_two_ends_agree_about_the_activity_contract(self):
        import baton_worker

        self.assertEqual(baton_worker.ACTIVITY_DOCUMENT,
                         exchange.ACTIVITY_DOCUMENT)
        self.assertEqual(baton_worker.ACTIVITY_SCHEMA,
                         exchange.ACTIVITY_SCHEMA)
        self.assertEqual(baton_worker.ACTIVITY_DOCUMENT_OPERATION,
                         exchange.ACTIVITY_OPERATION)

    def test_growth_is_observable_before_the_turn_completes(self):
        held, _document = self.commanded()
        agent = self.observing([1024, 4096])
        self.assertEqual(self.worker(held, agent), 0)
        expected = exchange.activity_identities(held, session=self.SESSION)
        # THE TERMINAL IS WRITTEN BY NOW, so the manager's own reader skips it
        # -- which is the selected semantics rather than a missing count. The
        # document is still on disk and still correctly bound.
        self.assertIsNone(exchange.observed_activity(held, expected))
        with open(os.path.join(held.event_root, exchange.ACTIVITY_DOCUMENT),
                  encoding="utf-8") as reading:
            published = json.load(reading)
        self.assertEqual(sorted(published), sorted(exchange.ACTIVITY_MEMBERS))
        self.assertEqual(published["schema"], exchange.ACTIVITY_SCHEMA)
        self.assertEqual(published["attempt_id"], self.ATTEMPT)
        self.assertEqual(published["operation"], "work")
        self.assertEqual(published["bytes_observed"], 4096)

    def test_the_count_is_readable_while_the_operation_is_still_live(self):
        """THE CASE THE PREVIOUS ONE CANNOT MAKE: the manager reads the
        document at the moment the provider is still inside its turn."""
        held, _document = self.commanded()
        found = []

        class Watching:
            def work(inner, launched, declared):
                found.append(exchange.observed_activity(
                    held,
                    exchange.activity_identities(held,
                                                 session=self.SESSION)))
                raise RuntimeError("stop here")

            def observed_activity(inner):
                return 2048

            def consider(inner, launched, request):
                raise AssertionError("not this runtime's operation")

        import baton_worker

        agent = Watching()
        publisher = baton_worker._activity_publisher(
            agent, held.event_root,
            {"session": self.SESSION, "attempt_id": self.ATTEMPT,
             "sequence_id": exchange.sequence_of(self.ATTEMPT)},
            exchange.observation(held)["command"]["command_digest"],
            "work", exchange.worker_operation_id(self.ATTEMPT, "work"))
        self.addCleanup(publisher.stop)
        for _ in range(200):
            import time

            if os.path.lexists(os.path.join(held.event_root,
                                            exchange.ACTIVITY_DOCUMENT)):
                break
            time.sleep(0.01)
        self.assertEqual(
            exchange.observed_activity(
                held, exchange.activity_identities(held,
                                                   session=self.SESSION)),
            2048)
        self.assertEqual(exchange.observation(held)["state"], "waiting")

    def test_an_agent_that_observes_nothing_publishes_no_document(self):
        """AN OLD WORKER, AND EVERY SCRIPTED ONE. No `observed_activity` means
        no publisher at all, and absence is unknown."""
        from scripted_agent import ScriptedAgent

        held, _document = self.commanded()
        self.assertEqual(self.worker(held, ScriptedAgent()), 0)
        self.assertNotIn(exchange.ACTIVITY_DOCUMENT,
                         os.listdir(held.event_root))

    def test_an_unknown_or_empty_count_publishes_nothing_at_all(self):
        """`None`, `0` AND A PUBLISHED COUNT ARE THREE ANSWERS. A provider
        whose stream this adapter cannot account for leaves the projection
        absent, and so does one that has produced nothing yet -- writing a zero
        would assert "observed, and empty", which is a claim neither end has
        evidence for. Both are asserted, because they reach the publisher by
        different values and only one of them is caught by the cadence."""
        from scripted_agent import ScriptedAgent

        for index, answer in enumerate((None, 0, False, 1.5, "10")):
            with self.subTest(answer=answer):
                # ONE DELIVERY PER VALUE. `launch.materialize` refuses an
                # existing root on purpose, so each value gets its own attempt
                # rather than a fixture that reused one worker's namespace.
                held, _document = self.commanded(
                    self.delivered(attempt_id=f"attempt-{index}").exchange)
                inner = ScriptedAgent()

                class Silent:
                    def work(self, launched, declared):
                        return inner.work(launched, declared)

                    def observed_activity(self):
                        return answer

                    def consider(self, launched, request):
                        raise AssertionError("not this runtime's operation")

                self.assertEqual(self.worker(held, Silent()), 0)
                self.assertNotIn(exchange.ACTIVITY_DOCUMENT,
                                 os.listdir(held.event_root))

    def test_an_observer_that_raises_never_stops_the_turn(self):
        from scripted_agent import ScriptedAgent

        held, _document = self.commanded()
        inner = ScriptedAgent()

        class Exploding:
            def work(self, launched, declared):
                return inner.work(launched, declared)

            def observed_activity(self):
                raise RuntimeError("the scan failed")

            def consider(self, launched, request):
                raise AssertionError("not this runtime's operation")

        self.assertEqual(self.worker(held, Exploding()), 0)
        self.assertEqual(exchange.observation(held)["state"], "answered")
        self.assertNotIn(exchange.ACTIVITY_DOCUMENT,
                         os.listdir(held.event_root))

    def test_a_transient_observer_fault_does_not_end_the_publisher(self):
        """THE HALF THE TURN'S SURVIVAL CANNOT PROVE. The publisher runs on its
        own thread, so the turn would finish whether or not a fault killed it;
        what the guard actually buys is that a scan which fails once -- a file
        replaced mid-walk, a transient EIO -- leaves the NEXT observation still
        able to publish. A publisher that died on the first fault would report
        nothing for the rest of a turn that was going perfectly well."""
        import time

        import baton_worker

        held, _document = self.commanded()
        answers = [RuntimeError("the scan failed"), 3072]

        def observe():
            held_answer = answers[0]
            if len(answers) > 1:
                answers.pop(0)
            if isinstance(held_answer, BaseException):
                raise held_answer
            return held_answer

        publisher = _ActivityPublisherOver(baton_worker, held, self,
                                           observe).start()
        self.addCleanup(publisher.stop)
        place = os.path.join(held.event_root, exchange.ACTIVITY_DOCUMENT)
        for _ in range(400):
            if os.path.lexists(place):
                break
            time.sleep(0.01)
        self.assertTrue(os.path.lexists(place),
                        "the publisher never recovered from one fault")
        self.assertEqual(
            exchange.observed_activity(
                held, exchange.activity_identities(held,
                                                   session=self.SESSION)),
            3072)

    def test_describe_runs_no_publisher(self):
        """`describe` INVOKES NO PROVIDER, so there is no native stream for a
        count to be a count of."""
        import baton_worker

        held, _document = self.commanded()

        class Observing:
            def observed_activity(self):
                raise AssertionError("describe must not be observed")

        self.assertIsNone(baton_worker._activity_publisher(
            Observing(), held.event_root, {}, "sha256:" + "0" * 64,
            "describe", "describe:" + self.ATTEMPT))

    def test_an_existing_temporary_suppresses_the_write(self):
        """EXCLUSIVE STAGING. An entry already at the one staging name may be
        an abandoned publisher's; the write is suppressed rather than
        unlinking, truncating or writing through a file this program did not
        create."""
        import baton_worker

        held, _document = self.commanded()
        stale = os.path.join(held.event_root, baton_worker.ACTIVITY_STAGING)
        with open(stale, "w", encoding="utf-8") as writing:
            writing.write("somebody else's")
        self.assertFalse(baton_worker._publish_activity(
            held.event_root, {"schema": exchange.ACTIVITY_SCHEMA}))
        with open(stale, encoding="utf-8") as reading:
            self.assertEqual(reading.read(), "somebody else's")
        self.assertNotIn(exchange.ACTIVITY_DOCUMENT,
                         os.listdir(held.event_root))

    def test_a_symlink_at_the_staging_name_is_never_written_through(self):
        import baton_worker

        held, _document = self.commanded()
        outside = os.path.join(self.home, "not-the-deliverys")
        with open(outside, "w", encoding="utf-8") as writing:
            writing.write("keep me")
        os.symlink(outside,
                   os.path.join(held.event_root,
                                baton_worker.ACTIVITY_STAGING))
        self.assertFalse(baton_worker._publish_activity(
            held.event_root, {"schema": exchange.ACTIVITY_SCHEMA}))
        with open(outside, encoding="utf-8") as reading:
            self.assertEqual(reading.read(), "keep me")

    def test_the_published_file_is_replaced_and_never_renamed_away(self):
        """A READER CONCURRENT WITH PUBLICATION never sees absence caused by
        the publisher: the name is replaced by a rename OVER it."""
        import baton_worker

        held, document = self.commanded()
        digested = exchange.observation(held)["command"]["command_digest"]
        first = {"schema": exchange.ACTIVITY_SCHEMA,
                 "session": self.SESSION, "attempt_id": self.ATTEMPT,
                 "sequence_id": document["sequence_id"],
                 "command_digest": digested, "operation": "work",
                 "operation_id": exchange.worker_operation_id(self.ATTEMPT,
                                                              "work"),
                 "bytes_observed": 10}
        self.assertTrue(baton_worker._publish_activity(held.event_root, first))
        place = os.path.join(held.event_root, exchange.ACTIVITY_DOCUMENT)
        opened = os.open(place, os.O_RDONLY)
        try:
            self.assertTrue(baton_worker._publish_activity(
                held.event_root, {**first, "bytes_observed": 20}))
            # THE OLD INODE IS STILL COMPLETE AND STILL THE OLD ANSWER.
            self.assertEqual(json.loads(os.read(opened, 65536))
                             ["bytes_observed"], 10)
        finally:
            os.close(opened)
        self.assertEqual(exchange.observed_activity(
            held, exchange.activity_identities(held, session=self.SESSION)),
            20)
        # AND NO TEMPORARY SURVIVED EITHER PUBLICATION.
        self.assertNotIn(baton_worker.ACTIVITY_STAGING,
                         os.listdir(held.event_root))

    def test_a_blocked_publisher_is_abandoned_within_its_bound(self):
        """A DIAGNOSTIC MAY NOT GATE THE TURN. A wedged observer is abandoned
        without joining once the finite stop bound passes, and what makes that
        safe is the binding every document carries."""
        import threading
        import time

        import baton_worker

        held, _document = self.commanded()
        entered, release = threading.Event(), threading.Event()
        self.addCleanup(release.set)

        class Wedged:
            def observed_activity(self):
                entered.set()
                release.wait(30)
                return 1

        publisher = baton_worker._ActivityPublisher(
            held.event_root, {}, Wedged().observed_activity, seconds=0.01)
        publisher.start()
        thread = publisher._thread
        try:
            self.assertTrue(entered.wait(5))
            started = time.monotonic()
            self.assertFalse(publisher.stop(0.02))
            self.assertFalse(publisher.stop(0.02))
            self.assertIs(publisher._thread, thread)
            self.assertTrue(thread.is_alive())
            self.assertLess(time.monotonic() - started, 5)
        finally:
            release.set()
            thread.join(5)
            self.assertFalse(thread.is_alive())
        self.assertTrue(publisher.stop(0.01))
