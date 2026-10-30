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

import io
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

    def delivered(self, attempt_id=None, session=None,
                  role="implementation"):
        """W376586: THE ROLE IS AN OPERAND, so a case can deliver the launch
        document for the lane it is actually about. Every existing caller gets
        the implementation launch it got before."""
        return launch.materialize(
            self.launch_home, attempt_id=attempt_id or self.ATTEMPT,
            session=session or self.SESSION, contract="do the thing",
            role=role, transport=exchange.EXCHANGE_TRANSPORT,
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
                          manifest_digest="sha256:" + "4" * 64,
                          # W376586: `/2`'s MANDATORY added member, null here
                          # because an answered ending has no typed
                          # pre-provider declaration cause. Every case below
                          # that overrides it is overriding a member a
                          # conforming worker always writes.
                          adapter_failure=None)
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
        """W376586: THE `/2` DOCUMENT IS NOW THE PAYLOAD, and the assertion
        moves with it rather than being relaxed. `/5` wraps a file-exchange
        launch, so the two levels are asserted separately: the wrapper is
        exactly its three members and the payload is exactly `/2`'s five."""
        document = launch.launch_document(
            session="s", contract="c", role="r",
            transport=exchange.EXCHANGE_TRANSPORT)
        self.assertEqual(sorted(document), sorted(launch.WRAPPER_MEMBERS))
        self.assertEqual(document["schema"], "baton.worker-launch/5")
        self.assertEqual(document["wire_profile"],
                         "typed-adapter-file-exchange/1")
        payload = document["payload"]
        self.assertEqual(sorted(payload), sorted(launch.EXCHANGE_MEMBERS))
        self.assertEqual(payload["schema"], "baton.worker-launch/2")
        self.assertEqual(payload["transport"], "baton.worker-exchange/1")
        # AND THE TRANSPORT IS STILL ONE QUESTION with one answer, whichever
        # level a reader starts from.
        self.assertEqual(launch.selected_transport(document),
                         exchange.EXCHANGE_TRANSPORT)

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
                         # W376586 adds `adapter_failure`, null here, and
                         # `terminal_digest`, which is THIS MANAGER'S OWN
                         # measurement of the bytes it validated rather than
                         # anything the worker wrote.
                         ["adapter_failure", "answered", "disposition",
                          "ending", "fault_code", "manifest_digest",
                          "terminal_digest"])
        self.assertIsNone(view["terminal"]["adapter_failure"])

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
             # W376586: THE TERMINAL IS AT `/2`. The receipt and the state
             # events did not move -- only the terminal gained a mandatory
             # member -- and these literals are spelled rather than read from
             # the module so a version change has to be stated here too.
             "baton.worker-exchange.terminal/2"))


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

    def test_a_REFUSED_LAUNCH_writes_nothing_and_the_exchange_says_WAITING(
            self):
        """W197661, the composed shape of the reported incident.

        THE INCIDENT. The manager published this exact command, the container
        came up with a launch document its image could not read, and `serve`
        fell into `read_frame` on a stdin the exchange never uses. The
        container stayed up, the exchange stayed empty, and the manager
        observed a healthy runtime for as long as anybody was willing to wait.

        WHAT THIS PINS IS BOTH HALVES. The worker refuses promptly without
        reading the channel at all -- `_Unreadable` fails the case if it is
        touched -- and the manager's own projection of that attempt is
        unchanged by the failure: `waiting`, the manager's own command, and
        NOT ONE worker-authored member. A startup refusal may not be read as a
        receipt, a state, a terminal or an ending, and this asks the real
        `observation` rather than asserting it.

        The attempt is named by the manager's own sequence, so the projection
        is about THIS attempt and could not be a stale or foreign one.
        """
        import baton_worker

        held, document = self.commanded()
        place = os.path.join(self.home, "incompatible-launch.json")
        with open(place, "w", encoding="utf-8") as writing:
            # A `/3` document at an image that reads `/1` and `/2` is what was
            # actually mounted; here it is simply invalid, which is the same
            # refusal from `launched`'s point of view.
            json.dump({"schema": "baton.worker-launch/3",
                       "session": self.SESSION, "contract": "do the thing",
                       "role": "implementation",
                       "transport": exchange.EXCHANGE_TRANSPORT,
                       "job_execution": {"job_id": "codex-adapter-first"}},
                      writing)
        os.chmod(place, 0o444)

        class Unreadable:
            def read(inner, _count=None):
                raise AssertionError("the refused launch read stdin")

        class NeverDispatched:
            def __getattr__(inner, name):
                raise AssertionError(f"the refused launch reached {name}")

        stdout = io.BytesIO()
        stderr = io.StringIO()
        status = baton_worker.serve(Unreadable(), stdout, NeverDispatched(),
                                    place, held.command_root, held.event_root,
                                    stderr=stderr)
        self.assertEqual(status, baton_worker.STARTUP_REFUSED)
        self.assertEqual(stdout.getvalue(), b"")
        self.assertIn("baton-worker: ", stderr.getvalue())
        # NOTHING WAS WRITTEN INTO THE EXCHANGE. The manager's own command is
        # the only thing in either namespace.
        self.assertEqual(os.listdir(held.event_root), [])
        self.assertEqual(os.listdir(held.command_root),
                         [document["sequence_id"] + ".json"])

        view = exchange.observation(held)
        self.assertEqual(view["state"], "waiting")
        self.assertIsNone(view["receipt"])
        self.assertIsNone(view["terminal"])
        self.assertEqual(view["states"], [])
        self.assertEqual(view["foreign"], [])
        self.assertIsNone(view["unreadable"])
        # AND IT IS THIS ATTEMPT'S EXCHANGE, by the manager's own sequence.
        self.assertEqual(view["sequence_id"],
                         exchange.sequence_of(self.ATTEMPT))
        self.assertEqual(view["command"]["sequence_id"],
                         document["sequence_id"])
        self.assertEqual(view["command"]["operations"],
                         [one["operation"] for one in document["operations"]])

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

    def test_a_launch_document_naming_an_unknown_transport_is_REFUSED(self):
        """A `/2` that selects a channel nothing is listening to.

        W197661 CHANGED THE STATUS AND NOT THE PROPERTY. This ended `1`: the
        fault was latched and the framing loop then ended at once because the
        fixture handed it a CLOSED stdin. A real `/2` container's stdin is an
        open pipe with no writer, and there the same path waited forever --
        which is the incident this Work corrects. `/2` speaks the exchange, so
        the refusal now goes to stderr and ends `3` without reading at all.

        WHAT IS UNCHANGED is what this case was always about: the exchange
        beside it is untouched, because a worker that picked its transport
        from the filesystem would be a worker with two live contracts and no
        version.
        """
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
                               held.event_root, stderr=io.StringIO()),
            baton_worker.STARTUP_REFUSED)
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


class TheTypedDeclarationCauseAndNothingElseCrosses(Home):
    """W376586 — `terminal/2`'s added member, at BOTH ends of the exchange.

    THE WRITER AND THE READER MOVE TOGETHER, which is what "matched" means in
    `AMENDMENT-376531.md`: one current closed release, `terminal/2` at both
    ends and no `/1` branch anywhere. These cases drive the REAL worker over a
    real exchange on disk and then read what it wrote with the REAL manager
    reader, so neither end is standing in for the other.

    AND THE PRODUCER IS THE REAL ONE. The exception an agent raises here is
    `claude_agent.DeclarationRefusal` -- the class the shipped adapter raises
    from its four existing check sites -- imported from the module the image
    carries. Review 2026-10-28T20-07-16Z: "do not claim the direct selector
    tests prove the worker catch." They do not; this is the catch, and what
    makes it meaningful is that the type crossing it is the adapter's own.
    """

    def setUp(self):
        super().setUp()
        from .test_worker_image import staged

        self.inputs, self.outputs = staged(self)

    def worker(self, delivery, agent=None, role="implementation"):
        import baton_worker
        from scripted_agent import ScriptedAgent

        return baton_worker.serve_exchange(
            ScriptedAgent() if agent is None else agent, self.launched(role),
            self.SESSION, delivery.command_root, delivery.event_root)

    def launched(self, role="implementation"):
        """THE SELECTED LAUNCH ROLE IS AN OPERAND NOW, and that is the whole
        correction review 2026-10-28T21-25-27Z asked for in these cases: this
        fixture used to launch `implementation` for every case, including the
        ones labelled `review`, so the both-role coverage was a label rather
        than a selection and a foreign-role typed cause was being ASSERTED
        CORRECT."""
        return {"schema": launch.EXCHANGE_SCHEMA, "session": self.SESSION,
                "contract": "do the thing", "role": role,
                "transport": exchange.EXCHANGE_TRANSPORT}

    def refusal(self, code, role, *, message="the declaration is unusable"):
        import claude_agent

        return claude_agent.DeclarationRefusal(message, code=code, role=role)

    def raising(self, failed):
        """One agent whose `work` raises -- the frame the real adapter's own
        declaration check raises from."""
        from scripted_agent import ScriptedAgent

        class Refusing(ScriptedAgent):
            def work(self, seen, declared):
                raise failed

        return Refusing()

    def ran(self, failed, attempt=None, role="implementation"):
        """One real worker turn that raises `failed`, under its OWN attempt
        and under an EXPLICITLY SELECTED launch role.

        A fresh attempt id per turn rather than a re-entered fixture:
        `launch.materialize` refuses an existing root on purpose, and an
        exchange is per-attempt, so a case that drives several turns drives
        several attempts -- which is also what a deployment does.
        """
        delivery = self.delivered(
            attempt_id=self.ATTEMPT if attempt is None else attempt,
            role=role).exchange
        held, _document = self.commanded(delivery)
        self.assertEqual(
            self.worker(held, agent=self.raising(failed), role=role), 1)
        return held, exchange.observation(held)

    def published(self, delivery):
        with open(os.path.join(delivery.event_root,
                               exchange.TERMINAL_DOCUMENT), "rb") as reading:
            return reading.read()

    # -- the two copies of one contract ------------------------------------

    def test_the_two_ends_agree_about_the_added_member(self):
        """`baton_worker` cannot import this package, so the vocabulary exists
        twice; these are the cases that keep the copies from drifting."""
        import adapter_refusal
        import baton_worker

        self.assertEqual(baton_worker.ADAPTER_FAILURE_MEMBERS,
                         exchange.ADAPTER_FAILURE_MEMBERS)
        self.assertEqual(baton_worker.ADAPTER_FAILURE_OPERATION,
                         exchange.ADAPTER_FAILURE_OPERATION)
        self.assertEqual(baton_worker.ADAPTER_FAILURE_CODE,
                         exchange.ADAPTER_FAILURE_CODE)
        self.assertEqual(baton_worker.MAX_ADAPTER_FAILURE_BYTES,
                         exchange.MAX_ADAPTER_FAILURE_BYTES)
        self.assertEqual(adapter_refusal.COMPONENT,
                         exchange.ADAPTER_COMPONENT)
        self.assertEqual(adapter_refusal.CODES, exchange.ADAPTER_CODES)
        self.assertEqual(adapter_refusal.ROLES, exchange.ADAPTER_ROLES)
        self.assertEqual(baton_worker.TERMINAL_SCHEMA,
                         exchange.TERMINAL_SCHEMA)
        self.assertTrue(exchange.TERMINAL_SCHEMA.endswith("/2"))
        self.assertIn("adapter_failure", exchange.TERMINAL_MEMBERS)

    def test_the_catch_tests_identity_against_the_adapter_s_own_class(self):
        """ONE MODULE SO ONE TYPE, proved by object identity rather than by
        name: a duplicate definition in either program would make this
        `except` miss."""
        import adapter_refusal
        import baton_worker
        import claude_agent

        self.assertIs(baton_worker.adapter_refusal, adapter_refusal)
        self.assertTrue(issubclass(claude_agent.DeclarationRefusal,
                                   adapter_refusal.AdapterDeclarationRefusal))
        self.assertIs(claude_agent._SharedDeclarationRefusal,
                      adapter_refusal.AdapterDeclarationRefusal)

    # -- the ordinary ending is unchanged ----------------------------------

    def test_an_answered_ending_says_there_was_no_typed_cause(self):
        """A STATEMENT RATHER THAN AN ABSENCE, which is why the member is
        mandatory: null means "no typed cause was established", and a `/1`
        worker that cannot say either is refused by the schema instead."""
        held, _document = self.commanded()
        self.assertEqual(self.worker(held), 0)
        view = exchange.observation(held)
        self.assertEqual(view["state"], "answered")
        self.assertIsNone(view["terminal"]["adapter_failure"])
        self.assertIn(b'"adapter_failure":null', self.published(held))

    def test_an_untyped_agent_failure_keeps_the_ending_it_had(self):
        """The generic clause is byte-unchanged: same `faulted`, same `agent`
        code, and the added member explicitly null."""
        held, view = self.ran(ValueError("something else entirely"))
        self.assertEqual(view["state"], "faulted")
        self.assertEqual(view["terminal"]["fault_code"], "agent")
        self.assertEqual(view["terminal"]["answered"], ["describe"])
        self.assertIsNone(view["terminal"]["adapter_failure"])

    # -- the four codes, both roles, through the real worker ---------------

    def test_every_code_and_role_crosses_as_the_manager_s_own_identity(self):
        import adapter_refusal

        for index, code in enumerate(adapter_refusal.CODES):
            for turn, role in enumerate(adapter_refusal.ROLES):
                attempt = f"attempt-{index}-{turn}"
                with self.subTest(code=code, role=role):
                    # THE LANE IS SELECTED, not labelled: this turn is
                    # launched as `role` and the adapter's refusal names the
                    # same one.
                    held, view = self.ran(self.refusal(code, role),
                                          attempt=attempt, role=role)
                    self.assertEqual(view["state"], "faulted")
                    self.assertEqual(view["terminal"]["fault_code"], "agent")
                    self.assertEqual(view["terminal"]["answered"],
                                     ["describe"])
                    self.assertEqual(
                        view["terminal"]["adapter_failure"],
                        {"component": "role-adapter", "code": code,
                         "role": role, "operation": "work",
                         # THE MANAGER'S OWN MINTED IDENTITY, not a value the
                         # worker composed and not a grammar that looks right.
                         "operation_id": exchange.worker_operation_id(
                             attempt, "work")})
                    self.assertEqual([one["state"]
                                      for one in view["states"]],
                                     ["answered", "faulted"])

    def test_a_foreign_role_claim_never_becomes_typed_evidence(self):
        """THE DEFECT REVIEW 2026-10-28T21-25-27Z REPRODUCED, both directions.

        The serialization boundary held the role to the two allowed literals
        and never compared it with the launch, so a container launched
        `implementation` published a typed cause saying `review`. A valid
        vocabulary word is not an identity. The ending is unchanged -- faulted,
        `agent` -- and the typed evidence is null, which is what the amendment
        already required of a wrong role.
        """
        import adapter_refusal

        for launched, claimed in (("implementation", "review"),
                                  ("review", "implementation")):
            with self.subTest(launched=launched, claimed=claimed):
                held, view = self.ran(
                    self.refusal(adapter_refusal.ROLE_OUTPUT_MISSING,
                                 claimed),
                    attempt=f"attempt-foreign-{launched}", role=launched)
                self.assertEqual(view["state"], "faulted")
                self.assertEqual(view["terminal"]["fault_code"], "agent")
                self.assertIsNone(view["terminal"]["adapter_failure"])
                self.assertIn(b'"adapter_failure":null', self.published(held))
                # AND THE FOREIGN ROLE IS NOWHERE IN THE DOCUMENT, which is
                # the half a reader of a later report would have believed.
                self.assertNotIn(claimed.encode("utf-8"),
                                 self.published(held))

    def test_the_published_role_is_the_launch_s_and_not_the_exception_s(self):
        """The literal published is resolved from the SELECTED role. The two
        agree in every admitted case, so the way to see which one is carried
        is to check that it is the launch's in both lanes."""
        import adapter_refusal

        for role in adapter_refusal.ROLES:
            with self.subTest(role=role):
                _held, view = self.ran(
                    self.refusal(adapter_refusal.SET_INVALID, role),
                    attempt=f"attempt-published-{role}", role=role)
                self.assertEqual(
                    view["terminal"]["adapter_failure"]["role"], role)
        # THE OBJECT IDENTITY IS A PROPERTY OF THE BOUNDARY, not of the
        # document: the published value travels through JSON and comes back a
        # different object with the same content. So it is asserted where it
        # exists -- and with the exception carrying a `str` SUBCLASS that
        # compares equal, which is exactly the vehicle a payload would ride.
        import baton_worker

        class Carrying(str):
            payload = "/host/credentials"

        for role in adapter_refusal.ROLES:
            with self.subTest(role=role, vehicle="str subclass"):
                failed = self.refusal(adapter_refusal.SET_INVALID, role)
                failed.role = Carrying(role)
                facts = baton_worker._adapter_failure(
                    failed, "work", "work:attempt-1", role)
                # The exception's own value is refused by `type(...) is str`,
                # so there is no typed cause at all -- and the published role
                # could not have been it either way.
                self.assertIsNone(facts)
                ok = self.refusal(adapter_refusal.SET_INVALID, role)
                facts = baton_worker._adapter_failure(
                    ok, "work", "work:attempt-1", role)
                self.assertIs(facts["role"],
                              adapter_refusal.ROLES[
                                  adapter_refusal.ROLES.index(role)])

    def test_a_launch_role_outside_the_typed_vocabulary_stays_generic(self):
        """`integration` is a real launch role this deployment runs, and no
        development declaration cause can name it -- so a container launched
        that way produces the ordinary generic fault rather than a mismatch
        report about a lane that does not exist here."""
        import adapter_refusal
        import baton_worker

        failed = self.refusal(adapter_refusal.SET_INVALID, "implementation")
        for selected in ("integration", "", None, 7, True, "Implementation"):
            with self.subTest(selected=selected):
                self.assertIsNone(baton_worker._adapter_failure(
                    failed, "work", "work:attempt-1", selected))

    def test_the_cause_arrives_beside_a_receipt_and_a_real_history(self):
        """`_caused` is not relaxed for the typed path: the receipt that fenced
        dispatch and the describe/work state events are still required, and the
        typed cause additionally pins `answered` to the one reachable prefix."""
        import adapter_refusal

        held, view = self.ran(self.refusal(adapter_refusal.SET_INVALID,
                                           "implementation"),
                              role="implementation")
        self.assertIsNotNone(view["receipt"])
        self.assertEqual(view["states"],
                         [{"operation": "describe", "state": "answered"},
                          {"operation": "work", "state": "faulted"}])
        self.assertEqual(view["foreign"], [])

    # -- secrecy at the serialization boundary -----------------------------

    def test_an_overridden_facts_method_is_never_called_or_carried(self):
        """Review 2026-10-28T20-07-16Z: "do not serialize exception text" or
        "invoke arbitrary overridden `facts` methods as trusted evidence".

        This object's `facts()` would raise if it were called at all, and its
        message and args carry secret-shaped values. The code and role are
        VALID, so the typed cause is still established -- from this build's own
        literals -- and nothing the object supplied reaches the document.
        """
        import adapter_refusal

        planted = "/host/credentials/token-AKIAEXAMPLE"

        import claude_agent

        class Overridden(claude_agent.DeclarationRefusal):
            def facts(self):
                raise AssertionError("facts() was called at the boundary")

        failed = Overridden(planted, code=adapter_refusal.SET_INVALID,
                            role="review")
        failed.extra = planted
        held, view = self.ran(failed, role="review")
        self.assertEqual(view["terminal"]["adapter_failure"]["code"],
                         adapter_refusal.SET_INVALID)
        raw = self.published(held)
        self.assertNotIn(planted.encode("utf-8"), raw)
        self.assertNotIn(b"Overridden", raw)
        self.assertNotIn(b"extra", raw)

    def test_a_mutated_code_or_role_degrades_to_the_generic_fault(self):
        """The class checks its code and role in `__init__` and NOTHING stops a
        later assignment, so the boundary asks again. A value it cannot hold to
        the closed literals is not a cause -- and the ending is still the one
        the generic clause would have published."""
        import adapter_refusal

        for name, value in (("code", "declaration-set-invalid-ish"),
                            ("code", "/host/secret"),
                            ("code", None),
                            ("role", "integration"),
                            ("role", True),
                            ("component", "role-adapter-other"),
                            ("component", "")):
            with self.subTest(member=name, value=value):
                failed = self.refusal(adapter_refusal.NAME_UNSUPPORTED,
                                      "implementation")
                setattr(failed, name, value)
                held, view = self.ran(
                    failed, attempt=f"attempt-mutated-{name}-{value!r}")
                self.assertEqual(view["terminal"]["fault_code"], "agent")
                self.assertIsNone(view["terminal"]["adapter_failure"])
                self.assertIn(b'"adapter_failure":null', self.published(held))

    def test_an_equal_comparing_string_subclass_is_not_a_literal(self):
        """`type(...) is str` rather than `==`: a `str` subclass equal to a
        valid code can carry an arbitrary payload, and what is stored is the
        matching literal from this build's own tuple either way."""
        import adapter_refusal
        import baton_worker

        class Carrying(str):
            payload = "/host/credentials"

        failed = self.refusal(adapter_refusal.ROLE_OUTPUT_MISSING, "review")
        failed.code = Carrying(adapter_refusal.ROLE_OUTPUT_MISSING)
        self.assertIsNone(baton_worker._adapter_failure(
            failed, "work", "work:attempt-1", "review"))
        ok = self.refusal(adapter_refusal.ROLE_OUTPUT_MISSING, "review")
        facts = baton_worker._adapter_failure(ok, "work", "work:attempt-1",
                                              "review")
        for member in ("component", "code", "role"):
            with self.subTest(member=member):
                self.assertIs(type(facts[member]), str)

    def test_a_missing_member_is_a_degradation_and_not_a_crash(self):
        """A `property` that raises and a deleted attribute are the same answer
        at this boundary: `None`, and the ordinary generic fault."""
        import adapter_refusal
        import baton_worker

        failed = self.refusal(adapter_refusal.OTHER_ROLE_OUTPUT_REQUIRED,
                              "review")
        del failed.role
        self.assertIsNone(baton_worker._adapter_failure(
            failed, "work", "work:attempt-1", "review"))

    def test_the_phase_is_the_operation_the_command_names(self):
        """"Wrong phase keeps the safe generic agent failure." The phase is
        asked at the boundary rather than inferred: this transport does not
        reach an agent for `describe` at all -- `handle` answers it from the
        protocol itself -- so the rule is proved where a cause would have to be
        composed."""
        import adapter_refusal
        import baton_worker

        failed = self.refusal(adapter_refusal.SET_INVALID, "implementation")
        self.assertIsNone(baton_worker._adapter_failure(
            failed, "describe", "describe:attempt-1", "implementation"))
        self.assertIsNone(baton_worker._adapter_failure(
            failed, "consider", "work:attempt-1", "implementation"))
        self.assertIsNotNone(baton_worker._adapter_failure(
            failed, "work", "work:attempt-1", "implementation"))

    def test_an_unrelated_exception_type_never_becomes_a_cause(self):
        """A bare `TaskRefusal`, an arbitrary exception and a worker fault are
        not typed causes -- the amendment forbids reaching a code by
        resemblance, and the only admission here is the shared class."""
        import baton_worker
        import claude_agent

        for failed in (claude_agent.TaskRefusal("no"), ValueError("no"),
                       RuntimeError("no"), Exception("no")):
            with self.subTest(failed=type(failed).__name__):
                self.assertIsNone(baton_worker._adapter_failure(
                    failed, "work", "work:attempt-1", "implementation"))


class TheReaderHoldsTheAddedMemberToTheWholeEnding(Home):
    """W376586 — the manager's half, driven from bytes a worker could write.

    A NON-NULL TYPED CAUSE IS A CLAIM ABOUT THE WHOLE ENDING, so every case
    here writes a terminal whose ten original members and whose added member
    disagree, and the answer is `unreadable` rather than a view with half of a
    contradiction in it. The amendment's degrade-only-this-branch rule is the
    REPORT's, downstream of here; a terminal that contradicts itself is not a
    document to read either half of.
    """

    def cause(self, **overrides):
        held = {"component": "role-adapter",
                "code": "declaration-set-invalid",
                "role": "implementation", "operation": "work",
                "operation_id": exchange.worker_operation_id(self.ATTEMPT,
                                                             "work")}
        held.update(overrides)
        return held

    def faulted(self, **overrides):
        """The one reachable typed history: receipt, describe answered, work
        faulted, and a faulted terminal answering exactly `["describe"]`."""
        delivery, document = self.one()
        self.wrote(delivery, exchange.RECEIPT_DOCUMENT,
                   self.receipt(document))
        self.wrote(delivery, exchange.state_document("describe"),
                   self.state(document, "describe", "answered"))
        self.wrote(delivery, exchange.state_document("work"),
                   self.state(document, "work", "faulted"))
        body = {"ending": "faulted", "answered": ["describe"],
                "disposition": None, "manifest_digest": None,
                "fault_code": "agent", "adapter_failure": self.cause()}
        body.update(overrides)
        self.wrote(delivery, exchange.TERMINAL_DOCUMENT,
                   self.terminal(document, **body))
        return exchange.observation(delivery)

    def test_the_one_reachable_history_reads(self):
        view = self.faulted()
        self.assertEqual(view["state"], "faulted")
        self.assertIsNone(view["unreadable"])
        self.assertEqual(view["terminal"]["adapter_failure"], self.cause())

    def test_an_answered_ending_with_a_cause_is_unreadable(self):
        delivery, document = self.one()
        self.wrote(delivery, exchange.RECEIPT_DOCUMENT,
                   self.receipt(document))
        for operation in exchange.OPERATIONS:
            self.wrote(delivery, exchange.state_document(operation),
                       self.state(document, operation, "answered"))
        self.wrote(delivery, exchange.TERMINAL_DOCUMENT,
                   self.terminal(document, adapter_failure=self.cause()))
        view = exchange.observation(delivery)
        self.assertEqual(view["state"], "unreadable")
        # THE REASON IS NOT DURABLE and is deliberately not asserted here:
        # `_safe` keeps the category and the code, because a refusal's prose is
        # composed from values a worker wrote. The message is checked directly
        # against the validator below, where no durable surface is involved.
        self.assertEqual(view["unreadable"],
                         {"category": "refused", "code": "precondition"})
        self.assertIsNone(view["terminal"])

    def test_another_fault_code_with_a_cause_is_unreadable(self):
        for code in ("output", "exchange", "protocol", "replay"):
            with self.subTest(fault_code=code):
                view = self.faulted(fault_code=code)
                self.assertEqual(view["state"], "unreadable")

    def test_a_history_the_cause_could_not_have_stopped_is_unreadable(self):
        """"a declaration is checked when the provider turn is composed", so
        the only prefix a typed cause can sit after is `["describe"]`."""
        for answered in ([], ["describe", "work"]):
            with self.subTest(answered=answered):
                view = self.faulted(answered=answered)
                self.assertEqual(view["state"], "unreadable")

    def test_every_vocabulary_member_is_closed(self):
        for name, value in (("component", "role-adapter-other"),
                            ("component", ""),
                            ("component", None),
                            ("code", "declaration-set-invalid-ish"),
                            ("code", "agent"),
                            ("code", None),
                            ("role", "integration"),
                            ("role", "implementation,review"),
                            ("role", True),
                            ("operation", "describe"),
                            ("operation", "consider")):
            with self.subTest(member=name, value=value):
                view = self.faulted(
                    adapter_failure=self.cause(**{name: value}))
                self.assertEqual(view["state"], "unreadable")
                self.assertIsNone(view["terminal"])

    def test_a_worker_composed_operation_identity_is_refused(self):
        """The identity is held against the one THIS MANAGER minted, not
        against a grammar: a worker-asserted operation id is the one thing this
        reader will not take."""
        for value in ("work:attempt-2", "work:" + "a" * 40, "work",
                      "describe:attempt-1", "", None, 7):
            with self.subTest(operation_id=value):
                view = self.faulted(
                    adapter_failure=self.cause(operation_id=value))
                self.assertEqual(view["state"], "unreadable")

    def test_the_added_object_is_exactly_its_five_members(self):
        for spoiled in (self.cause(extra="x"),
                        {one: value for one, value in self.cause().items()
                         if one != "role"},
                        [], "a cause", 7, True, {}):
            with self.subTest(spoiled=spoiled):
                view = self.faulted(adapter_failure=spoiled)
                self.assertEqual(view["state"], "unreadable")

    def test_the_added_object_is_bounded_on_its_own(self):
        """A bound separate from the whole document's, because this is the
        first member composed from an object the adapter raised."""
        view = self.faulted(
            adapter_failure=self.cause(
                role="implementation" + " " * exchange.MAX_ADAPTER_FAILURE_BYTES))
        self.assertEqual(view["state"], "unreadable")

    def test_a_terminal_without_the_member_at_all_is_refused(self):
        """MANDATORY, not optional. A worker that cannot state the member is a
        worker from the generation before this release, and the closed member
        set says so rather than defaulting it to null."""
        delivery, document = self.one()
        held = self.terminal(document)
        del held["adapter_failure"]
        self.wrote(delivery, exchange.RECEIPT_DOCUMENT,
                   self.receipt(document))
        for operation in exchange.OPERATIONS:
            self.wrote(delivery, exchange.state_document(operation),
                       self.state(document, operation, "answered"))
        self.wrote(delivery, exchange.TERMINAL_DOCUMENT, held)
        view = exchange.observation(delivery)
        self.assertEqual(view["state"], "unreadable")
        self.assertEqual(view["unreadable"],
                         {"category": "refused", "code": "precondition"})

    def test_the_previous_terminal_version_is_refused_as_another_protocol(self):
        """One current closed release: there is no `/1` branch at either end,
        and the version is asked by equality before anything else."""
        delivery, document = self.one()
        self.wrote(delivery, exchange.RECEIPT_DOCUMENT,
                   self.receipt(document))
        for operation in exchange.OPERATIONS:
            self.wrote(delivery, exchange.state_document(operation),
                       self.state(document, operation, "answered"))
        held = self.terminal(document,
                             schema="baton.worker-exchange.terminal/1")
        del held["adapter_failure"]
        self.wrote(delivery, exchange.TERMINAL_DOCUMENT, held)
        view = exchange.observation(delivery)
        self.assertEqual(view["state"], "unreadable")

    def test_the_digest_is_of_the_exact_bytes_this_reader_validated(self):
        """No reopen-for-digest race: the identity is taken over the one `raw`
        the reader bounded and parsed, so two reads of a file the worker can
        replace cannot be reported as one document."""
        import hashlib

        view = self.faulted()
        delivery, _document = self.one()
        place = os.path.join(delivery.event_root, exchange.TERMINAL_DOCUMENT)
        with open(place, "rb") as reading:
            raw = reading.read()
        self.assertEqual(view["terminal"]["terminal_digest"],
                         "sha256:" + hashlib.sha256(raw).hexdigest())
        # AND IT FOLLOWS THE BYTES. A worker that rewrites its own terminal
        # publishes a different document, and the identity says so.
        with open(place, "wb") as writing:
            writing.write(json.dumps(json.loads(raw),
                                     separators=(",", ":"))
                          .encode("utf-8"))
        again = exchange.observation(delivery)
        self.assertEqual(again["state"], "faulted")
        self.assertNotEqual(again["terminal"]["terminal_digest"],
                            view["terminal"]["terminal_digest"])
        self.assertEqual(again["terminal"]["adapter_failure"],
                         view["terminal"]["adapter_failure"])

    def test_the_refusal_says_which_disagreement_it_was(self):
        """The prose is checked HERE rather than off the projection, because
        `_safe` keeps only the category and the code on a durable surface."""
        delivery, _document = self.one()
        for overrides, said in (
                ({"ending": "answered"}, "is not an ending of its own"),
                ({"answered": []}, "one reachable history"),
                ({"adapter_failure": self.cause(role="integration")},
                 "vocabulary is closed"),
                ({"adapter_failure": self.cause(operation_id="work:other")},
                 "not one this manager commanded"),
                ({"adapter_failure": self.cause(extra="x")},
                 "unexpected extra"),
                ({"adapter_failure": 7}, "not one closed object or null")):
            with self.subTest(said=said):
                body = {"ending": "faulted", "answered": ["describe"],
                        "disposition": None, "manifest_digest": None,
                        "fault_code": "agent",
                        "adapter_failure": self.cause()}
                body.update(overrides)
                with self.assertRaises(ContractRefusal) as caught:
                    exchange._adapter_failure(
                        body["adapter_failure"], delivery,
                        ending=body["ending"], fault=body["fault_code"],
                        answered=body["answered"])
                self.assertIn(said, str(caught.exception))


class TheFileExchangeLaunchIsWrapped(Home):
    """W376586 — the matched `worker-launch/5` wrapper, at BOTH of its ends.

    `AMENDMENT-376531.md`: "one current worker-launch/5 wrapper
    {schema,wire_profile,payload}, wire_profile=typed-adapter-file-exchange/1.
    Payload preserves current ordinary/context/role launch semantics in the
    existing mode-specific /2-/4 payload shapes; these are internal payload
    variants, not support for executing historical unwrapped file launches...
    typed worker refuses unsupported/unwrapped file-exchange launch before
    adapter construction/receipt/provider. No nested wrapper or arbitrary
    profile... No silent downgrade."

    THE MANAGER COMPOSES AND THE REAL WORKER READS. Nothing here asserts the
    wrapper against a second copy of the rule: the documents are the ones
    `launch_document` authors, and the validation is `baton_worker.launched`.
    """

    def setUp(self):
        super().setUp()
        # The worker directory reaches `sys.path` through this import, the same
        # way `TheWorkerIsTheOtherEnd` reaches it; `staged` also gives the one
        # case below that really runs a turn its `/input` and `/output`.
        from .test_worker_image import staged

        self.inputs, self.outputs = staged(self)

    def wrapped(self, **changed):
        held = launch.launch_document(
            session=self.SESSION, contract="do the thing",
            role="implementation",
            transport=exchange.EXCHANGE_TRANSPORT)
        held.update(changed)
        return held

    def refusing(self, document):
        import baton_worker

        with self.assertRaises(baton_worker.WorkerFault) as caught:
            baton_worker.launched(document, place="/run/baton/launch.json")
        return str(caught.exception)

    # -- the two ends agree -------------------------------------------------

    def test_the_two_ends_agree_about_the_wrapper(self):
        import baton_worker

        self.assertEqual(baton_worker.WRAPPER_LAUNCH_SCHEMA,
                         launch.WRAPPER_SCHEMA)
        self.assertEqual(baton_worker.WRAPPER_LAUNCH_MEMBERS,
                         launch.WRAPPER_MEMBERS)
        self.assertEqual(baton_worker.WIRE_PROFILE, launch.WIRE_PROFILE)
        self.assertEqual(launch.WRAPPER_SCHEMA, "baton.worker-launch/5")
        self.assertEqual(launch.WIRE_PROFILE,
                         "typed-adapter-file-exchange/1")
        # THE WRAPPER IS NOT A PAYLOAD GENERATION, which is what makes a
        # nested wrapper refuse by a membership test rather than a depth count.
        self.assertNotIn(launch.WRAPPER_SCHEMA, launch.PAYLOAD_SCHEMAS)
        self.assertNotIn(launch.WRAPPER_SCHEMA,
                         baton_worker.SUPPORTED_LAUNCH_SCHEMAS)

    # -- the positives, through the real reader -----------------------------

    def test_every_mode_specific_payload_is_carried_and_read(self):
        """ORDINARY, JOB AND CONTEXT, each wrapped and each read back as the
        container document it always was -- "internal payload variants"."""
        import baton_worker

        # ORDINARY `/2` through the composer, and the `/3` and `/4` variants
        # through the fixtures that already build valid ones: `test_claude_
        # context` drives a real `/4` context stage end to end and
        # `test_single_worker` a real `/3`, both of which now go through this
        # wrapper. What is asserted HERE is the carriage rule itself.
        document = launch.launch_document(
            session=self.SESSION, contract="do the thing",
            role="implementation", transport=exchange.EXCHANGE_TRANSPORT)
        self.assertEqual(document["schema"], launch.WRAPPER_SCHEMA)
        self.assertEqual(document["payload"]["schema"],
                         launch.EXCHANGE_SCHEMA)
        seen = baton_worker.launched(document)
        # WHAT THE WORKER SEES IS THE CONTAINER DOCUMENT, unchanged: every
        # reader downstream of `launched` is untouched.
        self.assertEqual(seen, document["payload"])
        self.assertEqual(seen["transport"], exchange.EXCHANGE_TRANSPORT)
        # AND EVERY PAYLOAD GENERATION IS ADMITTED BY THE READER, asked of the
        # closed table rather than of one example: a `/3` or `/4` carrying the
        # exchange is read exactly as a `/2` is.
        for inside in launch.PAYLOAD_SCHEMAS:
            with self.subTest(payload=inside):
                self.assertIn(inside, baton_worker.SUPPORTED_LAUNCH_SCHEMAS)

    def test_both_roles_are_carried_unchanged(self):
        import baton_worker

        for role in ("implementation", "review"):
            with self.subTest(role=role):
                document = launch.launch_document(
                    session=self.SESSION, contract="do the thing", role=role,
                    transport=exchange.EXCHANGE_TRANSPORT)
                self.assertEqual(
                    baton_worker.launched(document)["role"], role)

    def test_the_delivery_on_disk_is_wrapped_and_still_composes_its_namespaces(self):
        """THE DEFECT THIS WRAPPER COULD HAVE REINTRODUCED, and the case that
        holds it closed. `_exchange_materialized` reads the DOCUMENT to decide
        whether to compose the command and event namespaces; `/5` moved the
        transport one level down, and a reader asking the top level would have
        composed none -- which `_exchange_materialized`'s own comment records
        costing 54 cases the last time the proxy went stale."""
        import baton_worker

        delivery = self.delivered()
        self.assertIsNotNone(delivery.exchange)
        self.assertEqual(delivery.document["schema"], launch.WRAPPER_SCHEMA)
        with open(delivery.place, "rb") as reading:
            raw = json.loads(reading.read().decode("utf-8"))
        self.assertEqual(raw, delivery.document)
        self.assertEqual(launch.selected_transport(raw),
                         exchange.EXCHANGE_TRANSPORT)
        # AND THE BYTES ON DISK ARE WHAT THE WORKER READS.
        self.assertEqual(baton_worker.launched(raw), raw["payload"])

    def test_adoption_re_derives_the_same_wrapped_bytes(self):
        """`adopt` authors through the same owner and compares canonical
        bytes, so a wrapped delivery is recovered by the one comparison that
        already closed identity and value drift together."""
        self.delivered()
        adopted = self.adopted()
        self.assertEqual(adopted.document["schema"], launch.WRAPPER_SCHEMA)
        self.assertIsNotNone(adopted.exchange)

    def test_the_framed_and_one_shot_launches_are_untouched(self):
        """The amendment puts the framed transport outside this feature. A
        `/1`, and a `/3` validly naming no transport, are composed and read
        exactly as before -- unwrapped."""
        import baton_worker

        ordinary = launch.launch_document(session=self.SESSION,
                                          contract="do the thing", role="r")
        self.assertEqual(ordinary["schema"], launch.LAUNCH_SCHEMA)
        self.assertEqual(baton_worker.launched(ordinary), ordinary)
        self.assertIsNone(launch.selected_transport(ordinary))

    # -- the refusals, all of them before anything starts -------------------

    def test_an_unwrapped_file_exchange_launch_is_refused(self):
        """THE HALF THAT MAKES THE WRAPPER A RELEASE RATHER THAN AN OPTION,
        and the amendment's "no silent downgrade": a `/2`-`/4` document that
        selects the file exchange and did not arrive wrapped is not executed."""
        for payload in (self.wrapped()["payload"],
                        dict(self.wrapped()["payload"],
                             schema=launch.JOB_SCHEMA,
                             job_execution={
                                 "job_id": "job-a",
                                 "attempt_id": self.ATTEMPT,
                                 "job_input_digest": "sha256:" + "1" * 64,
                                 "job_policy_digest": "sha256:" + "2" * 64,
                                 "runtime_input_digest": "sha256:" + "1" * 64,
                                 "runtime_policy_digest": "sha256:" + "2" * 64,
                                 "execution_limits": None,
                                 "execution_limits_digest": None})):
            with self.subTest(schema=payload["schema"]):
                said = self.refusing(payload)
                self.assertIn("without the", said)
                self.assertIn("baton.worker-launch/5", said)
                self.assertIn("is not one this worker executes", said)

    def test_an_arbitrary_wire_profile_is_refused(self):
        for value in ("typed-adapter-file-exchange/2", "", None, 7, True,
                      "TYPED-ADAPTER-FILE-EXCHANGE/1",
                      "typed-adapter-file-exchange/1 "):
            with self.subTest(profile=value):
                said = self.refusing(self.wrapped(wire_profile=value))
                self.assertIn("a profile this program cannot name", said)
                self.assertIn("no", said)

    def test_a_nested_wrapper_is_refused(self):
        held = self.wrapped()
        said = self.refusing(self.wrapped(payload=dict(held)))
        self.assertIn("inside a", said)
        self.assertIn("never another wrapper", said)

    def test_a_wrapper_around_a_launch_selecting_no_exchange_is_refused(self):
        """Wrapped around a framed or one-shot launch it would describe a wire
        nobody is on -- the silent-downgrade direction in reverse."""
        framed = launch.launch_document(session=self.SESSION,
                                        contract="do the thing", role="r")
        said = self.refusing(self.wrapped(payload=framed))
        self.assertIn("describe a wire nothing is on", said)

    def test_the_wrapper_is_exactly_its_three_members(self):
        for spoiled in ({"schema": launch.WRAPPER_SCHEMA},
                        dict(self.wrapped(), extra="x"),
                        {one: value for one, value in self.wrapped().items()
                         if one != "wire_profile"}):
            with self.subTest(spoiled=sorted(spoiled)):
                self.assertIn("is exactly schema, wire_profile, payload",
                              self.refusing(spoiled))

    def test_a_payload_that_is_not_a_document_or_is_from_elsewhere_refuses(self):
        for value in (None, [], "a launch", 7, True):
            with self.subTest(payload=value):
                self.assertIn("payload that is not one document",
                              self.refusing(self.wrapped(payload=value)))
        said = self.refusing(self.wrapped(
            payload={"schema": "baton.worker-launch/6", "session": "s",
                     "contract": "c", "role": "r",
                     "transport": exchange.EXCHANGE_TRANSPORT}))
        self.assertIn("baton.worker-launch/6", said)

    def test_the_whole_launch_bound_is_measured_on_the_wrapper(self):
        """THE BOUND IS ON THE DOCUMENT THAT IS WRITTEN, which is now the
        wrapper -- so the wrapper's own bytes are what the worker's ceiling
        applies to.

        Asserted against `_bytes` directly, and the reason is honest rather
        than convenient: the closed `/2` member set at `MAX_LAUNCH_VALUE` each
        cannot reach `MAX_LAUNCH_BYTES` through the composer at all, so a case
        that drove the composer would be asserting a refusal no composition
        can produce. What matters is that the writer bounds the OUTER
        document, and that is exactly what this asks.
        """
        held = self.wrapped()
        self.assertEqual(
            launch._bytes(held),
            json.dumps(held, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":")).encode("utf-8"))
        fat = dict(held, payload=dict(
            held["payload"],
            contract="c" * (launch.MAX_LAUNCH_BYTES + 1)))
        with self.assertRaises(ContractRefusal) as caught:
            launch._bytes(fat)
        self.assertIn(str(launch.MAX_LAUNCH_BYTES), str(caught.exception))
        self.assertEqual(caught.exception.code, "denied")

    def test_the_refusal_happens_before_any_receipt_or_provider(self):
        """"before adapter construction/receipt/provider" is a property of the
        ORDER, and this proves it the only way it can be proved: the real
        worker is given an unwrapped exchange launch over a real delivery, and
        the event namespace is still empty afterwards."""
        import baton_worker
        from scripted_agent import ScriptedAgent

        delivery = self.delivered()
        held, _document = self.commanded(delivery.exchange)
        payload = launch.payload_of(delivery.document)
        with self.assertRaises(baton_worker.WorkerFault):
            baton_worker.launched(payload)
        # NOTHING WAS PUBLISHED, because `launched` raises before `serve`
        # reaches the receipt. The exchange namespace holds only what this
        # manager wrote.
        self.assertEqual(sorted(os.listdir(held.event_root)), [])
        view = exchange.observation(held)
        self.assertEqual(view["state"], "waiting")
        self.assertIsNone(view["receipt"])
        self.assertIsNone(view["terminal"])
        # And the same delivery WRAPPED runs to an answer, so the refusal
        # above is about the wrapper and not about the fixture.
        self.assertEqual(
            baton_worker.serve_exchange(
                ScriptedAgent(), baton_worker.launched(delivery.document),
                self.SESSION, held.command_root, held.event_root), 0)


class TheWrapperReachesTheExchangeThroughRealStartup(Home):
    """W376586 review 2026-10-28T22-29-20Z — the two P1s, at the owner.

    THE REVIEW'S CENTRAL POINT, and it was right: `TheFileExchangeLaunchIsWrapped`
    calls `launched` directly and its positive calls `serve_exchange` with an
    ALREADY-UNWRAPPED document, so it never reaches `serve`'s `session_of`
    ordering. Every valid current wrapper lost its session there and the
    container exited 2 before the new validator or the exchange ran -- a
    correct manager delivery looking like a broken image.

    So these cases enter at `baton_worker.serve` with the launch document THIS
    MANAGER WROTE, on disk, at the path it wrote it to; and at
    `dogfood_entry._production` with a constructor spy, which is where "before
    adapter construction" is actually decided.
    """

    def setUp(self):
        super().setUp()
        from .test_worker_image import staged

        self.inputs, self.outputs = staged(self)

    def execution(self, attempt):
        """A `/3` Job context with REAL execution limits, resolved by the Job
        owner's own rules. My first attempt passed `execution_limits: None`,
        which the launch owner refuses -- correctly, since every member of
        that context is required."""
        from baton_v12.job_manager import execution_limits as rules

        held = rules.resolved(rules.owned_execution_limits({}), 1)
        return {"job_id": "job-a", "attempt_id": attempt,
                "job_input_digest": "sha256:" + "1" * 64,
                "job_policy_digest": "sha256:" + "2" * 64,
                "runtime_input_digest": "sha256:" + "1" * 64,
                "runtime_policy_digest": "sha256:" + "2" * 64,
                "execution_limits": held,
                "execution_limits_digest": launch._digest(held)}

    def spoiled(self, delivery, payload, name=None):
        """One deliberately wrong delivery, at ITS OWN path.

        THE REAL LAUNCH FILE IS NOT OVERWRITTEN, and that is the launch
        owner's property rather than an inconvenience: the document is created
        read-only inside a read-only root precisely so a worker cannot rewrite
        what it says it is. So a case about a wrong document writes its own
        file and hands `serve` that path, which is the one operand `serve`
        takes.
        """
        # A UNIQUE NAME PER CALL, because the file below is made read-only
        # and a case that spoils several documents would otherwise be unable
        # to write the second one -- which is how my first version of the
        # multi-vector case failed.
        place = os.path.join(
            self.home,
            f"spoiled-{delivery.attempt_id}-{name or len(payload)}.json")
        with open(place, "wb") as writing:
            writing.write(payload)
        # READ-ONLY, because `read_launch` refuses a launch document the
        # container could rewrite -- and it is right to. A fixture that left
        # it writable would be testing that refusal instead of the one the
        # case is about, which is what my first attempt did: every spoiled
        # case answered 2 for the mode rather than for the document.
        os.chmod(place, 0o444)
        return place

    def served(self, delivery, agent=None, place=None):
        """THE REAL STARTUP OWNER, over the real document on disk.

        `serve` reads the file itself, reads the session before validating,
        latches, selects the transport and resolves the adapter. Nothing here
        hands it a document: the only operand is the PATH this manager wrote.
        """
        import baton_worker
        from scripted_agent import ScriptedAgent

        return baton_worker.serve(
            io.BytesIO(b""), io.BytesIO(),
            ScriptedAgent() if agent is None else agent,
            delivery.place if place is None else place,
            delivery.exchange.command_root, delivery.exchange.event_root)

    # -- P1: the session survives the wrapper at real startup --------------

    def test_a_wrapped_delivery_reaches_the_exchange_from_real_startup(self):
        """THE DEFECT, as a case. Before the correction this returned 2 as
        uncorrelated; the exchange was never reached and the event namespace
        stayed empty."""
        delivery = self.delivered()
        held, _document = self.commanded(delivery.exchange)
        self.assertEqual(delivery.document["schema"], launch.WRAPPER_SCHEMA)
        self.assertEqual(self.served(delivery), 0)
        view = exchange.observation(held)
        self.assertEqual(view["state"], "answered")
        self.assertEqual(view["terminal"]["answered"], ["describe", "work"])

    def test_the_session_read_before_validation_is_the_container_s(self):
        """`session_of` runs BEFORE `launched`, deliberately -- so a document
        that is correlatable and wrong in some other way can still answer.
        That property has to hold through the wrapper, which is what broke."""
        import baton_worker

        document = launch.launch_document(
            session=self.SESSION, contract="do the thing",
            role="implementation",
            transport=exchange.EXCHANGE_TRANSPORT)
        self.assertNotIn("session", document)
        self.assertEqual(
            baton_worker.session_of(baton_worker.container_of(document)),
            self.SESSION)
        # AND THE RULE IS NARROW: only an outer document DECLARING this
        # wrapper with an object payload is unwrapped. Nothing else is
        # searched for a session.
        for value in ({"schema": launch.LAUNCH_SCHEMA, "session": "s"},
                      {"payload": {"session": "s"}},
                      {"schema": "baton.worker-launch/6",
                       "payload": {"session": "s"}}):
            with self.subTest(document=value):
                self.assertIs(baton_worker.container_of(value), value)

    def test_a_nested_wrapper_has_no_container_session(self):
        """It exits 2 rather than answering a fault, which is `session_of`'s
        own rule applied honestly: there is no identity to correlate to."""
        import baton_worker

        delivery = self.delivered()
        self.commanded(delivery.exchange)
        place = self.spoiled(delivery, self.wrapped_bytes(nested=True))
        self.assertEqual(self.served(delivery, place=place), 2)
        self.assertEqual(sorted(os.listdir(delivery.exchange.event_root)), [])

    def wrapped_bytes(self, *, nested=False, **changed):
        held = launch.launch_document(
            session=self.SESSION, contract="do the thing",
            role="implementation", transport=exchange.EXCHANGE_TRANSPORT)
        if nested:
            held = dict(held, payload=dict(held))
        held.update(changed)
        return json.dumps(held, sort_keys=True,
                          separators=(",", ":")).encode("utf-8")

    def test_every_mode_specific_payload_starts_through_serve(self):
        """ORDINARY `/2`, JOB `/3` AND CONTEXT-SHAPED `/3` deliveries, each
        composed by the manager, each wrapped, each reaching the exchange from
        the real startup owner. The review asked for real startup variants
        rather than `/2` plus a membership assertion."""
        for label, operands in (
                ("ordinary", {}),
                ("job", {"job_execution": self.execution("attempt-job")})):
            with self.subTest(payload=label):
                attempt = "attempt-job" if operands else "attempt-ordinary"
                delivery = launch.materialize(
                    self.launch_home, attempt_id=attempt,
                    session=self.SESSION, contract="do the thing",
                    role="implementation",
                    transport=exchange.EXCHANGE_TRANSPORT,
                    workspace_group=self.group, **operands)
                held, _document = self.commanded(delivery.exchange)
                self.assertEqual(delivery.document["schema"],
                                 launch.WRAPPER_SCHEMA)
                self.assertEqual(self.served(delivery), 0)
                self.assertEqual(
                    exchange.observation(held)["state"], "answered")

    def test_an_unwrapped_exchange_delivery_refuses_at_real_startup(self):
        """And it does NOT hang: `/5` is not `/1`, so the refusal takes the
        prompt path rather than waiting on a stdin nobody writes."""
        import baton_worker

        delivery = self.delivered()
        held, _document = self.commanded(delivery.exchange)
        place = self.spoiled(delivery, json.dumps(
            launch.payload_of(delivery.document), sort_keys=True,
            separators=(",", ":")).encode("utf-8"))
        errors = io.StringIO()
        self.assertEqual(
            baton_worker.serve(io.BytesIO(b""), io.BytesIO(),
                               None, place,
                               delivery.exchange.command_root,
                               delivery.exchange.event_root, stderr=errors), 3)
        self.assertIn("without the", errors.getvalue())
        self.assertIn("baton.worker-launch/5", errors.getvalue())
        # NOTHING WAS PUBLISHED: the refusal is before the receipt.
        self.assertEqual(sorted(os.listdir(held.event_root)), [])
        self.assertIsNone(exchange.observation(held)["receipt"])

    # -- P1: the adapter is constructed after the boundary, not before -----

    def test_the_scripted_default_is_resolved_after_validation(self):
        """`main` evaluated `_scripted_default()` as an ARGUMENT, so the
        reference image's adapter existed before `serve` had read anything. It
        is passed through unresolved now and `serve` resolves it after the
        delivery is validated and the transport selected."""
        import baton_worker

        delivery = self.delivered()
        self.commanded(delivery.exchange)
        place = self.spoiled(delivery,
                             b'{"schema": "baton.worker-launch/9", '
                             b'"session": "session-one"}')
        errors = io.StringIO()
        # `agent=None` and a refused delivery: if the default were resolved
        # before the read this would construct one.
        self.assertEqual(
            baton_worker.serve(io.BytesIO(b""), io.BytesIO(), None,
                               place,
                               delivery.exchange.command_root,
                               delivery.exchange.event_root,
                               stderr=errors), 3)
        self.assertIn("from another generation", errors.getvalue())

    def test_a_latched_container_builds_no_default_either(self):
        """`/1` IS THE FRAMED TRANSPORT AND OUTSIDE THIS FEATURE, so this is a
        free uniformity rather than an amendment requirement -- but a latched
        container answers one correlated fault and never reaches `handle`, so
        resolving the reference default there would construct a provider for a
        container that is already refusing.

        Driven with `agent=None`, which is the only way to see it: the
        existing latch cases inject an agent object, so they cannot tell
        whether one would have been built.
        """
        import baton_worker

        delivery = self.delivered(attempt_id="attempt-latched")
        # A `/1` document that is correlatable and wrong in another way: it
        # carries a member `/1` does not have, so it latches rather than
        # taking the prompt path.
        place = self.spoiled(delivery, json.dumps(
            {"schema": launch.LAUNCH_SCHEMA, "session": self.SESSION,
             "contract": "do the thing", "role": "implementation",
             "posture": "leaked"},
            sort_keys=True, separators=(",", ":")).encode("utf-8"),
            name="latched")
        built = []
        held = baton_worker._scripted_default

        def counting():
            built.append("constructed")
            return held()

        baton_worker._scripted_default = counting
        self.addCleanup(setattr, baton_worker, "_scripted_default", held)
        answered = io.BytesIO()
        # ONE IDENTITY ENVELOPE on stdin, which is what a latched container
        # reads before answering its single fault.
        request = json.dumps(
            {"protocol": baton_worker.PROTOCOL, "session": self.SESSION,
             "operation_id": "describe:attempt-latched",
             "operation": "describe"}).encode("utf-8")
        status = baton_worker.serve(
            io.BytesIO(b"%d\n" % len(request) + request), answered, None,
            place, delivery.exchange.command_root,
            delivery.exchange.event_root)
        self.assertEqual(status, 1)
        self.assertEqual(built, [])
        self.assertIn(b"launch", answered.getvalue())

    def test_a_refused_delivery_builds_nothing_and_still_reports(self):
        """THE SHIPPED ENTRY PATH, with a constructor spy AND the worker's own
        reporting.

        Two reviews meet in this case. 22-29-20Z: the entry evaluated
        `ClaudeAgent()` before anything read the launch, so "before adapter
        construction" was false. 23-07-14Z: my first correction then SWALLOWED
        the refusal -- it returned 2 before `main`, losing the bounded stderr
        sentence `serve` emits and misreporting a correlatable document as
        uncorrelatable. My own case asserted that 2, which is why it passed;
        the expectation was the defect.

        So the assertion is now the one that matters: the entry answers
        EXACTLY what `serve` answers for the same document, says the same
        thing, and builds nothing.
        """
        import baton_worker
        import dogfood_entry

        built = []

        class Spy:
            def __init__(self):
                built.append("constructed")

        for label, document, status in (
                ("unwrapped exchange",
                 launch.payload_of(launch.launch_document(
                     session=self.SESSION, contract="c",
                     role="implementation",
                     transport=exchange.EXCHANGE_TRANSPORT)),
                 baton_worker.STARTUP_REFUSED),
                ("wrong profile",
                 dict(json.loads(self.wrapped_bytes()),
                      wire_profile="typed-adapter-file-exchange/2"),
                 baton_worker.STARTUP_REFUSED),
                ("an unknown outer member",
                 dict(json.loads(self.wrapped_bytes()), extra="x"),
                 baton_worker.STARTUP_REFUSED),
                ("nested wrapper",
                 json.loads(self.wrapped_bytes(nested=True)), 2),
                ("another generation",
                 {"schema": "baton.worker-launch/9",
                  "session": self.SESSION}, baton_worker.STARTUP_REFUSED),
                ("no session anywhere",
                 {"schema": launch.WRAPPER_SCHEMA}, 2)):
            with self.subTest(delivery=label):
                built.clear()
                delivery = self.delivered(
                    attempt_id="attempt-" + label.replace(" ", "-"))
                place = self.spoiled(delivery, json.dumps(
                    document, sort_keys=True,
                    separators=(",", ":")).encode("utf-8"))
                errors = io.StringIO()
                # WHAT THE WORKER ITSELF ANSWERS for this document, measured
                # rather than assumed, so the entry is compared with the owner
                # instead of with a number I chose.
                owned = baton_worker.serve(
                    io.BytesIO(b""), io.BytesIO(), None, place,
                    delivery.exchange.command_root,
                    delivery.exchange.event_root, stderr=errors)
                self.assertEqual(owned, status)
                answered = dogfood_entry._production(
                    place=place, build=Spy,
                    command_root=delivery.exchange.command_root,
                    event_root=delivery.exchange.event_root)
                self.assertEqual(answered, owned)
                self.assertEqual(built, [])
                # AND THE CORRELATABLE REFUSALS STILL SAY WHY, which is the
                # evidence my first correction destroyed. An uncorrelatable
                # document says nothing, and stays distinct.
                if status == baton_worker.STARTUP_REFUSED:
                    self.assertTrue(
                        errors.getvalue().startswith("baton-worker: "))
                    self.assertIn("launch", errors.getvalue())
                else:
                    self.assertEqual(errors.getvalue(), "")
                # NOTHING WAS PUBLISHED on either route.
                self.assertEqual(
                    sorted(os.listdir(delivery.exchange.event_root)), [])

    def test_a_valid_delivery_does_construct_the_adapter(self):
        """The other direction, so the case above is about the refusal and not
        about a seam that never builds anything."""
        import dogfood_entry

        built, served = [], []
        delivery = self.delivered()
        held, _document = self.commanded(delivery.exchange)

        class Answering:
            def __init__(self):
                built.append("constructed")

            def work(self, seen, declared):
                served.append(seen["session"])
                raise RuntimeError("far enough: the adapter was reached")

        # THE EXCHANGE ROOTS ARE THIS ATTEMPT'S. Without them `main` uses the
        # image's fixed paths and `serve_exchange` waits for a command nobody
        # published -- which is what my first version of this case did, and it
        # hung rather than failed.
        self.assertEqual(
            dogfood_entry._production(
                place=delivery.place, build=Answering,
                command_root=held.command_root,
                event_root=held.event_root), 1)
        self.assertEqual(built, ["constructed"])
        # AND IT WAS REACHED THROUGH THE REAL STARTUP, with the container's own
        # session -- the member the wrapper moved.
        self.assertEqual(served, [self.SESSION])
