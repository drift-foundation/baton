"""W26291 — the worker's launch document, as the dossier's supersession left it.

`work/records/2026/08/finding-v12-oci-worker-launch-environment/`.

WHAT THIS FILE IS NOT ABOUT. It does not re-check that four `BATON_WORKER_*`
values reach a command line. That transport was superseded BEFORE acceptance
and its cases went with it, because a test of behaviour that no longer exists
asserts nothing. What replaced them is here and in
`TheLaunchDocumentIsAMountAndNotAChannel` in `test_oci`: one versioned document,
authored by this manager, written read-only, and delivered as a typed
capability rather than as data a caller can shape.

THE PROPERTY THE SUPERSESSION IS ABOUT is version and closure. An environment
vocabulary has neither, so a manager and a worker from two generations
disagree silently; a document whose `schema` is checked by equality and whose
member set is closed at both ends fails closed on exactly that disagreement.
"""

import json
import os
import stat
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal, held_secret
from baton_v12.worker_manager import launch


class Home(unittest.TestCase):

    def setUp(self):
        self.home = tempfile.mkdtemp(prefix="v12-launch-")
        self.addCleanup(self.take_it_away)

    def take_it_away(self):
        # The module delivers READ-ONLY trees on purpose, so the fixture has to
        # be able to take them away again.
        for current, directories, files in os.walk(self.home, topdown=False):
            os.chmod(current, 0o700)
            for name in files:
                os.remove(os.path.join(current, name))
            for name in directories:
                os.rmdir(os.path.join(current, name))
        os.rmdir(self.home)

    def made(self, **overrides):
        body = {"attempt_id": "attempt-1", "session": "session-1",
                "contract": "do the thing", "role": "implementer"}
        body.update(overrides)
        return launch.materialize(self.home, **body)


class TheDocumentIsAuthoredRatherThanAssembled(Home):

    def test_it_is_exactly_four_members_and_the_pinned_schema(self):
        document = launch.launch_document(
            session="s", contract="c", role="r")
        self.assertEqual(sorted(document), sorted(launch.LAUNCH_MEMBERS))
        self.assertEqual(document["schema"], "baton.worker-launch/1")
        self.assertEqual(document["schema"], launch.LAUNCH_SCHEMA)

    def test_there_is_no_posture_member(self):
        """The consent-posture supersession, stated as a case.

        V12 launches one runtime and consent/execution is not a runtime axis,
        so a `posture` member would be transporting a fact that no longer
        exists -- and the worker would then have a source for an axis the
        ruling removed.
        """
        document = launch.launch_document(session="s", contract="c", role="r")
        self.assertNotIn("posture", document)
        self.assertNotIn("posture", launch.LAUNCH_MEMBERS)

    def test_a_caller_supplies_values_and_never_a_shape(self):
        """The document is REBUILT over `LAUNCH_MEMBERS` rather than copied.

        A caller that could hand over a mapping could hand over a wider one,
        and that is the environment channel this Work replaced wearing a
        different name.
        """
        with self.assertRaises(TypeError):
            launch.launch_document(session="s", contract="c", role="r",
                                   posture="execution")

    def test_a_malformed_value_refuses_before_anything_is_written(self):
        for name in ("session", "contract", "role"):
            for value, why in ((None, "null"), ("", "empty"), (7, "not text"),
                               ("nul\x00inside", "a NUL")):
                with self.subTest(name=name, why=why):
                    with self.assertRaises(ContractRefusal):
                        self.made(**{name: value})

    def test_a_session_wider_than_the_workers_ceiling_refuses(self):
        """THE WORKER'S CEILING, ENFORCED HERE. `session` is what every frame
        on the worker-entry channel is bound to, and a value the worker would
        refuse is not one this manager may write -- writing it would move a
        manager mistake inside a container, where the manager can no longer
        say why."""
        self.assertEqual(launch.MAX_SESSION, 256)
        with self.assertRaises(ContractRefusal):
            self.made(session="s" * (launch.MAX_SESSION + 1))

    def test_prose_may_carry_newlines_and_is_bounded(self):
        """The retired transport refused a newline because one
        `--env NAME=VALUE` argument cannot survive it. That was a fact about
        the TRANSPORT, and a human contract is prose -- so the ban is not
        carried forward, and the ceiling is."""
        one = self.made(contract="first line\nsecond line")
        self.assertEqual(one.document["contract"], "first line\nsecond line")
        with self.assertRaises(ContractRefusal):
            self.made(attempt_id="attempt-2",
                      role="r" * (launch.MAX_LAUNCH_VALUE + 1))

    def test_a_live_bearer_cannot_ride_the_launch_document(self):
        """§13's own clause, driven rather than asserted about.

        This document is world-readable and lives for the life of a container,
        so a bearer pasted into a contract line would be exactly the durable
        surface the rule names. The walk runs before any byte is written.
        """
        with held_secret("live-bearer-nobody-may-publish"):
            with self.assertRaises(ContractRefusal) as caught:
                self.made(contract="live-bearer-nobody-may-publish")
            self.assertEqual(caught.exception.code, "secret-leak")
        self.assertFalse(os.listdir(self.home))


class TheFileIsThisManagersOwn(Home):

    def test_it_is_a_regular_file_at_the_documents_own_name(self):
        one = self.made()
        self.assertTrue(os.path.isfile(one.place))
        self.assertEqual(os.path.basename(one.place), "launch.json")
        with open(one.place, "rb") as reading:
            self.assertEqual(json.loads(reading.read().decode("utf-8")),
                             one.document)

    def test_the_mode_is_established_rather_than_requested(self):
        """W26291 review [P0]: a creation mode is FILTERED BY THE UMASK.

        This passed `READ_ONLY_FILE` to `os.open` and stopped there, so a
        manager running under the ordinary service umask 077 authored a 0400
        document — one the container's fixed uid 65532 cannot read. That is the
        unrunnable worker this whole Work exists to fix, arriving silently and
        only on a host whose umask happens to be restrictive.

        The case that existed observed the TEST PROCESS'S OWN umask and
        therefore could not see it. This one sets a restrictive umask
        deliberately, and restores it whatever happens.
        """
        original = os.umask(0o077)
        self.addCleanup(os.umask, original)
        for mask in (0o077, 0o027, 0o022, 0o000):
            with self.subTest(umask=oct(mask)):
                os.umask(mask)
                one = self.made(attempt_id=f"attempt-{mask}")
                self.assertEqual(stat.S_IMODE(os.stat(one.place).st_mode),
                                 0o444)
                self.assertEqual(stat.S_IMODE(os.stat(one.root).st_mode),
                                 0o555)

    def test_a_partial_document_is_never_readable(self):
        """The other half of establishing the mode rather than requesting it.

        The file is created at 0000 and becomes readable on the descriptor
        that wrote it, after the last byte — so there is no instant at which
        a half-written launch document is something a container could read and
        refuse as malformed.
        """
        module = launch.os
        seen = []

        class Watching:
            def __getattr__(self, name):
                return getattr(module, name)

            def write(self, handle, payload):
                seen.append(stat.S_IMODE(module.fstat(handle).st_mode))
                return module.write(handle, payload)

        launch.os = Watching()
        self.addCleanup(setattr, launch, "os", module)
        one = self.made()
        launch.os = module
        self.assertTrue(seen, "nothing was written")
        for mode in seen:
            self.assertEqual(mode, 0o000,
                             "the document was readable while still partial")
        self.assertEqual(stat.S_IMODE(os.stat(one.place).st_mode), 0o444)

    def test_it_is_readable_by_anybody_and_writable_by_nobody(self):
        """BOTH HALVES ARE DELIBERATE, and the first one is the interesting
        one. The container runs as a fixed non-root uid and a bind mount
        carries the host mode through unchanged, so an owner-only mode would
        make delivery depend on which user the manager happens to be. That is
        only acceptable because §13 keeps this document non-secret, which the
        case above drives.
        """
        one = self.made()
        self.assertEqual(stat.S_IMODE(os.stat(one.place).st_mode), 0o444)
        self.assertEqual(stat.S_IMODE(os.stat(one.root).st_mode), 0o555)
        with self.assertRaises(OSError):
            os.open(one.place, os.O_WRONLY)

    def test_the_bytes_are_canonical_and_bounded(self):
        one = self.made()
        with open(one.place, "rb") as reading:
            raw = reading.read()
        self.assertEqual(raw, json.dumps(one.document, ensure_ascii=False,
                                         sort_keys=True,
                                         separators=(",", ":")).encode())
        self.assertLessEqual(len(raw), launch.MAX_LAUNCH_BYTES)

    def test_an_existing_root_refuses_rather_than_being_written_into(self):
        """A live delivery or an orphan, and replacing bytes this manager
        cannot account for is how one attempt's container reads another
        attempt's launch contract."""
        first = self.made()
        with self.assertRaises(ContractRefusal) as caught:
            self.made()
        self.assertEqual(caught.exception.code, "precondition")
        with open(first.place, "rb") as reading:
            self.assertIn(b"session-1", reading.read())

    def test_a_relative_storage_refuses(self):
        with self.assertRaises(ContractRefusal):
            launch.materialize("relative/place", attempt_id="attempt-1",
                               session="s", contract="c", role="r")

    def test_a_link_left_at_the_documents_name_is_not_written_through(self):
        """`O_EXCL | O_NOFOLLOW`, and the race they exist for.

        The root-exists refusal above closes the ordinary door, so this drives
        the interval it cannot see: the instant between this module creating
        its own root and opening the file inside it. Something that can write
        there in that instant -- an interrupted attempt, or anything else --
        must not become the thing written THROUGH, because the bytes would
        land outside a tree this manager owns and the container would then be
        told what it is by a file nobody authored.
        """
        outside = os.path.join(self.home, "outside.txt")
        with open(outside, "wb") as handle:
            handle.write(b"UNTOUCHED")
        module = launch.os

        class Racing:
            def __getattr__(self, name):
                return getattr(module, name)

            def makedirs(self, place, **rest):
                module.makedirs(place, **rest)
                module.symlink(outside, module.path.join(place,
                                                         "launch.json"))

        launch.os = Racing()
        self.addCleanup(setattr, launch, "os", module)
        with self.assertRaises(OSError):
            self.made()
        with open(outside, "rb") as reading:
            self.assertEqual(reading.read(), b"UNTOUCHED")

    def test_a_short_write_is_not_a_delivered_document(self):
        """`os.write` is allowed to write fewer bytes than it was given.

        A short write is ordinary rather than exotic and is not an error the
        call reports, so a writer that ignored the answer would deliver a
        PREFIX of the document -- which the worker refuses as malformed while
        this manager believes it delivered a whole one.
        """
        module = launch.os

        class Grudging:
            def __getattr__(self, name):
                return getattr(module, name)

            def write(self, handle, payload):
                # Eight bytes at a time, which is what a pipe, a signal or a
                # filesystem near its limit does without saying so.
                return module.write(handle, payload[:8])

        launch.os = Grudging()
        self.addCleanup(setattr, launch, "os", module)
        one = self.made()
        launch.os = module
        with open(one.place, "rb") as reading:
            self.assertEqual(json.loads(reading.read().decode("utf-8")),
                             one.document)

    def test_a_failed_write_leaves_no_half_delivery(self):
        """The ending that would have removed a partial root never starts,
        because the attempt never launched."""
        original = launch._write_whole

        def refusing(handle, payload):
            raise ContractRefusal("integrity", "schema", "no progress")

        launch._write_whole = refusing
        self.addCleanup(setattr, launch, "_write_whole", original)
        with self.assertRaises(ContractRefusal):
            self.made()
        self.assertEqual(os.listdir(self.home), [])

    def test_discard_removes_the_root_it_froze(self):
        one = self.made()
        self.assertTrue(launch.discard(one.root))
        self.assertFalse(os.path.lexists(one.root))
        # ABSENCE IS THE STATE ASKED FOR, not a refusal.
        self.assertTrue(launch.discard(one.root))


class TheDeliveryIsACapabilityAndNotAPath(Home):

    def test_it_authorizes_exactly_one_mount_at_the_fixed_target(self):
        one = self.made()
        self.assertEqual(one.mount(), (one.place, launch.LAUNCH_TARGET))
        self.assertEqual(launch.LAUNCH_TARGET, "/run/baton/launch.json")

    def test_readonly_is_not_something_it_can_be_asked_for(self):
        """A delivery that could ask to be writable would be a launch document
        the worker could rewrite between reading it and being asked what it
        is."""
        one = self.made()
        self.assertEqual(len(one.mount()), 2)
        self.assertNotIn("writable", dir(one))

    def test_it_remembers_which_attempt_it_belongs_to(self):
        one = self.made()
        self.assertEqual(one.attempt_id, "attempt-1")
        self.assertTrue(one.root.endswith("attempt-1"))


class TheComponentIsOnThePublicSurface(unittest.TestCase):

    def test_every_operation_this_cut_adds_is_exported(self):
        for name in launch.__all__:
            with self.subTest(name=name):
                self.assertTrue(hasattr(launch, name))


if __name__ == "__main__":
    unittest.main()


class TheDeliveryIsAdoptedRatherThanReconstructed(Home):
    """W47225: a restarted process recovers the delivery it already made."""

    def adopted(self, **overrides):
        """Adoption asks for the values this attempt was LAUNCHED with.

        Review 2026-08-30T15:05:35Z [P0]: shape agreement is not delivery
        identity, so the expectation is authored through the same owner that
        wrote the document and the canonical bytes must match exactly.
        """
        given = {"attempt_id": "attempt-1", "session": "session-1",
                 "contract": "do the thing", "role": "implementer"}
        given.update(overrides)
        return launch.adopt(self.home, **given)

    def test_an_existing_delivery_is_adopted_whole(self):
        made = self.made()

        adopted = self.adopted()

        self.assertIsInstance(adopted, launch.LaunchDelivery)
        self.assertEqual(adopted.root, made.root)
        self.assertEqual(adopted.place, made.place)
        self.assertEqual(adopted.document, made.document)
        self.assertEqual(adopted.mount(), made.mount())

    def test_an_attempt_with_no_delivery_adopts_nothing(self):
        """An ordinary state, and distinguishable from a failed proof: an
        attempt may have had no launch delivery at all."""
        self.assertIsNone(self.adopted())

    def test_a_root_this_manager_did_not_write_is_refused(self):
        """Bytes this manager cannot account for are not a launch contract,
        and a container told to read them would be told what it is by
        somebody else."""
        os.makedirs(os.path.join(self.home, "attempt-1"), mode=0o555)

        with self.assertRaises(ContractRefusal):
            self.adopted()

    def test_a_delivery_whose_modes_have_moved_is_refused(self):
        """`materialize` chmods both exactly, so anything else is a root
        somebody has since changed -- and a writable launch document is one
        the worker could rewrite between being given it and being asked."""
        made = self.made()
        os.chmod(made.root, 0o755)

        with self.assertRaises(ContractRefusal):
            self.adopted()

    def test_a_document_that_is_not_this_contract_is_refused(self):
        made = self.made()
        os.chmod(made.root, 0o700)
        os.chmod(made.place, 0o600)
        with open(made.place, "wb") as writing:
            writing.write(b'{"schema": "somebody.else/1"}')
        os.chmod(made.place, launch.READ_ONLY_FILE)
        os.chmod(made.root, launch.READ_ONLY_DIR)

        with self.assertRaises(ContractRefusal):
            self.adopted()

    def test_a_well_formed_document_from_another_delivery_is_refused(self):
        """Schema agreement is not delivery identity.

        Both documents are valid launch contracts, so validating only the
        closed shape and schema adopts the second attempt's session and role
        as the first attempt's typed capability.  Restart adoption must hold
        the bytes against the launch values this attempt was actually given.
        """
        first = self.made()
        other = self.made(attempt_id="attempt-2", session="session-2",
                          contract="another contract", role="reviewer")
        with open(other.place, "rb") as reading:
            foreign = reading.read()
        os.chmod(first.root, 0o700)
        os.chmod(first.place, 0o600)
        with open(first.place, "wb") as writing:
            writing.write(foreign)
        os.chmod(first.place, launch.READ_ONLY_FILE)
        os.chmod(first.root, launch.READ_ONLY_DIR)

        with self.assertRaises(ContractRefusal):
            self.adopted()

    def test_adoption_applies_the_member_value_contract(self):
        """A closed member set does not validate any member's value."""
        made = self.made()
        malformed = dict(made.document)
        malformed["session"] = 7
        os.chmod(made.root, 0o700)
        os.chmod(made.place, 0o600)
        with open(made.place, "wb") as writing:
            writing.write(json.dumps(malformed).encode("utf-8"))
        os.chmod(made.place, launch.READ_ONLY_FILE)
        os.chmod(made.root, launch.READ_ONLY_DIR)

        with self.assertRaises(ContractRefusal):
            self.adopted()

    def test_adoption_refuses_an_extra_entry_it_would_later_delete(self):
        """The root materializer made exactly one entry.

        Adopting a wider root would authorize ``launch.discard`` to delete a
        file this component did not create when cleanup later proves the
        runtime absent.
        """
        made = self.made()
        os.chmod(made.root, 0o700)
        with open(os.path.join(made.root, "foreign"), "wb") as writing:
            writing.write(b"not this component's launch document")
        os.chmod(made.root, launch.READ_ONLY_DIR)

        with self.assertRaises(ContractRefusal):
            self.adopted()

    def test_a_document_authored_for_other_values_is_refused(self):
        """Which delivery, not which kind of thing.

        The bytes are what prove it, so a document this component would have
        written for a DIFFERENT session, contract or role is refused even
        though it is a perfectly valid launch document.
        """
        self.made()
        for member, wrong in (("session", "session-2"),
                              ("contract", "do something else"),
                              ("role", "reviewer")):
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal) as caught:
                    self.adopted(**{member: wrong})
                self.assertIn("not the one this manager would have written",
                              str(caught.exception))

    def test_the_expectation_is_authored_by_the_owner_that_writes_it(self):
        """Reused rather than copied: a value contract re-implemented here
        would drift from the one `materialize` enforces, and would silently
        drop the authored document's own whole-document secret check."""
        self.made()
        for wrong in (7, "", "x" * 100000):
            with self.subTest(session=type(wrong).__name__):
                with self.assertRaises(ContractRefusal):
                    self.adopted(session=wrong)

    def test_adoption_is_on_the_public_surface(self):
        """A deployment that built its own delivery from a path would be
        minting the typed capability the adapter trusts out of bytes nobody
        proved, which is why the proving lives in this component."""
        self.assertIn("adopt", launch.__all__)
