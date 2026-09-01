"""W6634 — the assignment-scoped credential lifecycle, end to end.

`work/records/2026/08/finding-v12-sealed-output-credentials/`.

THE APPROVED BOUNDARY is the approver's ruling of 2026-08-26 as superseded by
message 16691, and every case below belongs to one of its lines:

  - an assignment names closed logical SLOTS and never bearer bytes, a host
    path or a provider reference;
  - the TRUSTED PROFILE maps each slot to a provider and an opaque reference,
    and the manager materializes one assignment-private file per authorized
    slot;
  - the worker sees only the fixed read-only root `/run/baton/credentials`,
    whose entries are those closed slot names;
  - bearer bytes are absent from argv, environment, image layers, labels, logs,
    durable state and output metadata, and durable state may name the slot, the
    provider and the lifecycle state but never the bearer or a reusable digest;
  - the live-secret registry is armed BEFORE worker access and released only
    after teardown is PROVED;
  - success, failure and cancellation use one ordered teardown, restart adopts
    only an exactly agreeing attempt/container/mount/root, and everything else
    fails closed into bounded orphan cleanup;
  - cleanup uncertainty is never reported as settlement.

THE REGISTRY IS WHY MOST OF THESE ARE NOT VACUOUS. A §13 walk over an empty
registry passes because there is nothing to find, so the cases that matter hold
a bearer LIVE across the act they are about.
"""

import json
import os
import stat
import tempfile
import unittest

from baton_v12.contracts import (ContractRefusal, forget_secret, live_secret,
                                 remember_secret)
from baton_v12.worker_manager import ControlStore

from . import input_roots
from baton_v12.worker_manager import (credentials, launch, oci,
                                      workspaces,
                                      sealing)

BEARER = "bearer-" + "0" * 40
SECOND = "second-" + "1" * 40
# HEX AND PREFIXED. W6634 sixth review: the manager validates the worker's
# envelope against the frozen schema and §12's Work-reference rule, so a
# fixture identity that could not exist is refused before it reaches the rule
# a case aims at.
UUID = "0123456789abcdef0123456789abcdef"
JOB = f"{UUID[:8]}-W1"
DIGEST = "sha256:" + "a" * 64
IDENTITY = {"image_digest": "sha256:" + "b" * 64, "profile_digest": DIGEST,
            "policy_digest": "sha256:" + "c" * 64,
            "adapter_digest": "sha256:" + "d" * 64}
# W16823: the trusted authorization context an adapter request carries beside
# the fence, and the two label members it composes from.
# W33936: the deployment's configured workspace group. An execution adapter
# without one refuses before the engine, so every execution construction below
# names it -- `os.getgid()` is the group this process can actually adopt, which
# keeps the pre-launch proof a real measurement rather than a mocked one.
# W33936 review [P1]: the configured group is a CAPABILITY read from this
# manager's own record, never an integer a caller composes. Obtained per
# case in `setUp` -- see `input_roots.configured_group`.
WORKSPACE_GROUP = None

CONTEXT = {"principal": "principal:org-a",
           "effective_scope": "scope:deployment"}
ASSIGNMENT = {"work_ref": {"authority_uuid": UUID, "work_id": JOB},
              "participant": "baton.claude", "generation": 1}
PROFILE = {"api": {"provider": "vault", "reference": "kv/one"},
           "signing": {"provider": "vault", "reference": "kv/two"}}


class CredentialCase(unittest.TestCase):

    def setUp(self):
        self.home_place = tempfile.mkdtemp(prefix="v12-credentials-")
        self.addCleanup(self._release)
        self.workspace = os.path.join(self.home_place, "workspace")
        self.inputs = os.path.join(self.home_place, "inputs")
        for place in (self.inputs, self.workspace):
            os.makedirs(place, exist_ok=True)
        # W33936: the workspace root is put in the configured group at exactly
        # the mode an execution start proves before the engine. This fixture
        # builds its roots by hand rather than through `assignment_workspace`,
        # so it establishes what that boundary establishes -- and a case here
        # that started over an unprepared root would refuse for the workspace's
        # reason rather than its own.
        self.store = ControlStore.open(
            os.path.join(self.home_place, "control.sqlite3"),
            incarnation="credentials-1",
            clock=lambda: "2026-08-24T00:00:00.000Z")
        self.addCleanup(self.store.close)
        self.group = input_roots.configured_group(self.store)
        os.chown(self.workspace, -1, self.group.gid)
        os.chmod(self.workspace, workspaces.WORKSPACE_DIR)
        self.minted = []
        # NOTHING LEAKS OUT OF A CASE INTO THE PROCESS REGISTRY. A live value
        # left behind would arm every later case's §13 walk against a string
        # this one invented, which is how a suite starts proving things about
        # itself.
        self.addCleanup(self._quiet)

    def _release(self):
        for base, directories, files in os.walk(self.home_place,
                                                topdown=False):
            for one in directories:
                os.chmod(os.path.join(base, one), 0o700)
            for one in files:
                full = os.path.join(base, one)
                if not os.path.islink(full):
                    os.chmod(full, 0o600)
        os.chmod(self.home_place, 0o700)

    def _quiet(self):
        for value in (BEARER, SECOND):
            while live_secret(value):
                forget_secret(value)

    def home(self):
        return credentials.CredentialHome(self.home_place)

    def provider(self, *values):
        """A credential provider capability, answering in call order."""
        answers = list(values) or [BEARER, SECOND]

        def mint(name, reference):
            self.minted.append((name, reference))
            return answers[len(self.minted) - 1]
        return mint

    def delivery(self, slots=("api",), **overrides):
        # W52800: the slot's reader group is a grant, so it arrives as the
        # capability this fixture already minted from its own manager store --
        # never a bare integer, which is what `_reader_group` refuses.
        overrides.setdefault("workspace_group", self.group)
        return self.home().materialize(
            credentials.resolved_delivery(slots, profile=PROFILE),
            attempt_id="attempt-1",
            credential_provider=self.provider(), **overrides)

    def adapter(self, delivery=None):
        class Engine:
            def __call__(self, argv):
                return {"status": 0, "stdout": "runtime-1\n", "stderr": ""}

        return oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivery,
            launch_delivery=self.launched())

    def launched(self, attempt_id="attempt-1"):
        """One materialized launch document. W26291 re-review [P1]: a start
        now REQUIRES one, so every canonical start in this suite has it — the
        credential lifecycle is what these cases are about, and a start
        refused for a missing launch document would be about something else.
        """
        key = f"_launch_{attempt_id}"
        if getattr(self, key, None) is None:
            home = tempfile.mkdtemp(prefix="v12-cred-launch-")
            self.addCleanup(self._take_launch_away, home)
            setattr(self, key, launch.materialize(
                home, attempt_id=attempt_id, session="session-1",
                contract="do the thing", role="implementer"))
        return getattr(self, key)

    def _take_launch_away(self, home):
        for current, directories, files in os.walk(home, topdown=False):
            os.chmod(current, 0o700)
            for name in files:
                os.remove(os.path.join(current, name))
            for name in directories:
                os.rmdir(os.path.join(current, name))
        if os.path.lexists(home):
            os.rmdir(home)


class AnAssignmentNamesSlotsAndNothingElse(CredentialCase):

    def test_a_slot_that_is_not_a_name_is_refused(self):
        """The refusal worth having. An assignment handing a document rather
        than a name is one trying to carry a provider reference, a host path or
        the bytes themselves, and the approved boundary forbids all three."""
        for spoiled in ({"provider": "vault", "reference": "kv/one"},
                        "/etc/shadow", BEARER.upper() + "/x", 7, None,
                        ["api"]):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    credentials._authorized_slots([spoiled])

    def test_a_slot_cannot_name_something_outside_the_fixed_root(self):
        for escaping in ("../elsewhere", "a/b", ".", "..", "/api", "API",
                         "-leading", "x" * 64):
            with self.subTest(slot=escaping):
                with self.assertRaises(ContractRefusal):
                    credentials._authorized_slots([escaping])

    def test_one_slot_is_authorized_once(self):
        with self.assertRaises(ContractRefusal):
            credentials._authorized_slots(["api", "api"])

    def test_the_number_of_slots_is_bounded(self):
        with self.assertRaises(ContractRefusal):
            credentials._authorized_slots(
                [f"slot-{index}"
                 for index in range(credentials.MAX_SLOTS + 1)])


class TheTrustedProfileMapsEverySlot(CredentialCase):

    def test_an_unmapped_slot_is_denied(self):
        """An assignment may not name a credential this deployment does not
        grant, and materializing nothing for it would hand the worker a root
        missing an entry it was told to expect."""
        caught = None
        try:
            credentials.resolved_delivery(["invented"], profile=PROFILE)
        except ContractRefusal as refusal:
            caught = refusal
        self.assertIsNotNone(caught)
        self.assertEqual((caught.category, caught.code), ("policy", "denied"))

    def test_a_profile_entry_the_assignment_did_not_authorize_is_not_delivered(
            self):
        """CLOSED SLOT NAMES DETERMINE THE ROOT'S ENTRIES. A trusted profile is
        legitimately broader than one assignment; what it may not do is put an
        entry in front of a worker nobody authorized."""
        resolution = credentials.resolved_delivery(["api"], profile=PROFILE)
        self.assertEqual([one["slot"] for one in resolution], ["api"])
        delivered = self.delivery(slots=("api",))
        self.assertEqual(sorted(os.listdir(delivered.root)), ["api"])
        self.assertEqual([target for _source, target in delivered.mounts()],
                         ["/run/baton/credentials/api"])

    def test_the_reference_is_opaque(self):
        """Proved as text and never read for a meaning. The provider gets it
        back verbatim, which is the whole of this module's relationship to
        it."""
        self.home().materialize(
            credentials.resolved_delivery(["api"], profile=PROFILE),
            attempt_id="attempt-1",
            workspace_group=self.group,
            credential_provider=self.provider())
        self.assertEqual(self.minted, [("vault", "kv/one")])

    def test_a_mapping_missing_its_members_is_refused(self):
        for spoiled in ({"provider": "vault"}, {"reference": "kv/one"},
                        {"provider": "vault", "reference": "kv", "extra": 1},
                        "vault:kv/one", None):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    credentials.resolved_delivery(["api"],
                                                  profile={"api": spoiled})


class MaterializationArmsTheRegistryFirst(CredentialCase):

    def test_one_private_file_per_slot(self):
        delivered = self.delivery(slots=("api", "signing"))
        self.assertEqual(sorted(os.listdir(delivered.root)),
                         ["api", "signing"])
        self.assertEqual(stat.S_IMODE(os.stat(delivered.root).st_mode),
                         credentials.VOLATILE_DIR)
        for name, value in (("api", BEARER), ("signing", SECOND)):
            place = os.path.join(delivered.root, name)
            # W52800: the ruled group-readable mode, and the configured gid.
            self.assertEqual(stat.S_IMODE(os.stat(place).st_mode),
                             credentials.VOLATILE_FILE)
            self.assertEqual(os.stat(place).st_gid, self.group.gid)
            with open(place, "rb") as reading:
                self.assertEqual(reading.read().decode("utf-8"), value)
        self.home().tear_down(delivered)

    def test_the_bearer_is_live_before_its_bytes_reach_a_file(self):
        """THE ORDER IS THE SECURITY PROPERTY. Registering after the write
        leaves a window in which the bytes exist and the registry says there is
        nothing to find -- the one shape a leak check cannot survive.

        This watches the exact moment the file is created and asks the registry
        what it knows then.
        """
        seen = []
        opened = credentials.os.open

        def watched(path, flags, mode=0o777):
            seen.append(live_secret(BEARER))
            return opened(path, flags, mode)

        credentials.os.open = watched
        try:
            delivered = self.delivery()
        finally:
            credentials.os.open = opened
        self.assertEqual(seen, [True])
        self.home().tear_down(delivered)

    def test_a_short_file_write_does_not_truncate_the_credential(self):
        """`os.write` may accept fewer bytes than it was handed. A reported
        short write is not delivery of a shorter credential."""
        written = credentials.os.write

        def short(handle, content):
            return written(handle, content[:1])

        credentials.os.write = short
        try:
            delivered = self.delivery()
        finally:
            credentials.os.write = written
        with open(os.path.join(delivered.root, "api"), "rb") as reading:
            self.assertEqual(reading.read(), BEARER.encode("utf-8"))
        self.home().tear_down(delivered)

    def test_a_writer_that_makes_no_progress_refuses_rather_than_spins(self):
        """A writer accepting zero bytes twice will not accept them on the
        third attempt. Looping on it would hang inside a delivery instead of
        failing it."""
        written = credentials.os.write
        credentials.os.write = lambda handle, content: 0
        try:
            with self.assertRaises(ContractRefusal):
                self.delivery()
        finally:
            credentials.os.write = written
        self.assertFalse(
            os.path.exists(self.home().volatile_root("attempt-1")))
        self.assertFalse(live_secret(BEARER))

    def test_an_assignment_that_authorizes_no_slot_has_no_delivery(self):
        """A delivery with no slots would be a root and a record describing
        nothing, and every mount comparison over it would be vacuously
        satisfied."""
        with self.assertRaises(ContractRefusal):
            credentials.resolved_delivery([], profile=PROFILE)

    def test_a_failed_materialization_leaves_no_root_and_no_live_bearer(self):
        """Half a delivery is a root holding a bearer nobody is going to
        remove: the ending that would have removed it never starts, because the
        attempt never launched."""
        def mint(name, reference):
            self.minted.append((name, reference))
            if len(self.minted) == 1:
                return BEARER
            raise OSError("the provider is unreachable")

        with self.assertRaises(OSError):
            self.home().materialize(
                credentials.resolved_delivery(["api", "signing"],
                                              profile=PROFILE),
                attempt_id="attempt-1",
                workspace_group=self.group,
                credential_provider=mint)
        self.assertFalse(
            os.path.exists(self.home().volatile_root("attempt-1")))
        self.assertFalse(live_secret(BEARER))

    def test_an_existing_root_is_never_written_into(self):
        """An existing root is a live delivery or an orphan. `adopt` is the
        only way back to one, and it proves identity before it takes it."""
        delivered = self.delivery()
        with self.assertRaises(ContractRefusal):
            self.delivery()
        self.home().tear_down(delivered)

    def test_a_credential_wider_than_the_bound_is_refused(self):
        with self.assertRaises(ContractRefusal):
            self.home().materialize(
                credentials.resolved_delivery(["api"], profile=PROFILE),
                attempt_id="attempt-1",
                workspace_group=self.group,
            credential_provider=self.provider(
                    "x" * (credentials.MAX_BEARER + 1)))
        self.assertFalse(
            os.path.exists(self.home().volatile_root("attempt-1")))

    def test_a_provider_that_is_not_a_capability_refuses_before_anything(self):
        with self.assertRaises(ContractRefusal):
            self.home().materialize(
                credentials.resolved_delivery(["api"], profile=PROFILE),
                attempt_id="attempt-1",
                workspace_group=self.group,
                credential_provider="vault")
        self.assertFalse(
            os.path.exists(self.home().volatile_root("attempt-1")))




class ThePermissionsAreTheContractsRatherThanTheCodes(CredentialCase):
    """W26284 PLAN 1: the acceptance names permissions and nothing held them.

    `MaterializationArmsTheRegistryFirst.test_one_private_file_per_slot`
    asserts the observed mode equals `credentials.VOLATILE_FILE` -- the very
    constant that produced it. That proves internal CONSISTENCY and nothing
    about the required permission: measured, both constants can be changed to
    world-readable and world-traversable with the whole suite green.

    The acceptance says "fresh-run credential files and roots have the REQUIRED
    permissions", and a required value is a literal somewhere or it is not
    required at all.
    """

    def test_the_required_modes_are_exactly_these(self):
        # W52800: `VOLATILE_FILE` IS the ruled slot mode and is the one every
        # live slot is created at.
        # ONE authoritative constant. Review [P1]: the first cut exported a
        # second one at 0o640 and kept this name at the superseded 0o600 "as
        # decision history", and this case asserted BOTH -- so the suite
        # claimed two modes were required for one file. Review
        # 2026-08-31T15:45:28Z [P1]: the comment describing that arrangement
        # outlived it and still said nothing creates a slot at this constant,
        # which the line below has contradicted since the constant was
        # corrected.
        self.assertEqual(credentials.VOLATILE_FILE, 0o640)
        self.assertEqual(credentials.VOLATILE_DIR, 0o700)

    def test_a_delivered_credential_is_readable_by_its_ruled_group_only(self):
        """The LITERAL modes and the LITERAL gid, on the bytes that landed.

        W52800 replaces this case's old claim -- manager-only `0600` -- with
        the ruled one. The old contract was the right answer to who OWNS the
        bearer and the wrong answer to who READS it: the execution container
        runs as the fixed uid 65532, so an owner-only file is one it can
        `stat` and cannot open, which is exactly what stopped three live
        attempts.

        `other` STAYS EMPTY, and that is the half worth asserting hardest.
        `/input` is evidence and W33935 made it world-readable; this is a
        BEARER, so the grant is the group the execution runtime already holds
        and nothing wider.

        Under a permissive umask on purpose. `os.open`'s mode is masked by the
        process umask, so a case run under `0o077` would see a narrow mode
        even for a file created wide -- and would pass for exactly the defect
        it is meant to catch.
        """
        previous = os.umask(0)
        try:
            delivered = self.delivery(slots=("api", "signing"))
        finally:
            os.umask(previous)
        self.assertEqual(stat.S_IMODE(os.stat(delivered.root).st_mode), 0o700)
        for name in ("api", "signing"):
            place = os.path.join(delivered.root, name)
            found = os.stat(place)
            self.assertEqual(stat.S_IMODE(found.st_mode), 0o640, name)
            self.assertEqual(found.st_uid, os.getuid(),
                             f"{name} left this manager's ownership")
            self.assertEqual(found.st_gid, self.group.gid,
                             f"{name} is not in the configured group")
            self.assertEqual(stat.S_IMODE(found.st_mode) & 0o007, 0,
                             f"{name} is readable by anybody")
        self.home().tear_down(delivered)

    def test_a_restrictive_umask_cannot_narrow_the_ruled_mode(self):
        """The umask does not get to decide who may read the bearer.

        `os.open`'s mode is FILTERED by the umask, so under the ordinary
        service umask `0o077` the slot would be created `0600` and the worker
        would be handed a credential it cannot read -- the original defect,
        arriving by a different route. The `fchmod` after the `fchown` is what
        makes the mode exact, and this is the case that requires it.
        """
        for umask in (0o000, 0o022, 0o077, 0o007):
            with self.subTest(umask=oct(umask)):
                # The provider answers in call order from a fixed list, so a
                # loop that reuses the fixture has to reset its own counter.
                self.minted.clear()
                previous = os.umask(umask)
                try:
                    delivered = self.delivery()
                finally:
                    os.umask(previous)
                place = os.path.join(delivered.root, "api")
                found = os.stat(place)
                self.assertEqual(stat.S_IMODE(found.st_mode), 0o640,
                                 oct(umask))
                self.assertEqual(found.st_gid, self.group.gid)
                self.home().tear_down(delivered)
                self._quiet()

    def test_the_bearer_is_written_only_after_the_group_and_mode_are_set(self):
        """THE ORDER, watched rather than inferred from the final `stat`.

        W52800's ruling is an ordering: create empty, `fchown` the descriptor,
        `fchmod` the still-empty descriptor, and only then write. Every step
        before the write is on an inode holding no bearer, so a failure at any
        of them unwinds a file that never held one. A `stat` afterwards cannot
        tell that order from the reverse, which is why this watches the calls.
        """
        seen = []
        opened, chown, chmod, write = (credentials.os.open,
                                       credentials.os.fchown,
                                       credentials.os.fchmod,
                                       credentials.os.write)

        def watched_open(path, flags, mode=0o777):
            if os.path.dirname(path).startswith(self.home_place):
                seen.append(("open", os.path.basename(path), mode,
                             bool(flags & os.O_EXCL)))
            return opened(path, flags, mode)

        def watched_chown(handle, uid, gid):
            seen.append(("fchown", uid, gid, os.fstat(handle).st_size))
            return chown(handle, uid, gid)

        def watched_chmod(handle, mode):
            seen.append(("fchmod", mode, os.fstat(handle).st_size))
            return chmod(handle, mode)

        def watched_write(handle, body):
            seen.append(("write", len(body)))
            return write(handle, body)

        credentials.os.open = watched_open
        credentials.os.fchown = watched_chown
        credentials.os.fchmod = watched_chmod
        credentials.os.write = watched_write
        try:
            delivered = self.delivery()
        finally:
            (credentials.os.open, credentials.os.fchown,
             credentials.os.fchmod, credentials.os.write) = (opened, chown,
                                                             chmod, write)

        self.assertEqual(seen[0], ("open", "api", 0o640, True),
                         "the slot is not exclusively created at the ruled "
                         "mode")
        # THE OWNER IS UNTOUCHED and the group is the configured one, on a
        # file that is still EMPTY.
        self.assertEqual(seen[1], ("fchown", -1, self.group.gid, 0))
        self.assertEqual(seen[2], ("fchmod", 0o640, 0))
        self.assertEqual(seen[3][0], "write")
        self.home().tear_down(delivered)

    def test_a_group_that_is_not_the_deployments_capability_refuses(self):
        """The gid is a GRANT, so a number is not one.

        `oci.run_vector` holds the same capability the same way for the other
        half of this grant -- the `--group-add` that lets the runtime use it.
        An integer accepted here would be this module deciding who may read a
        bearer.
        """
        for given in (None, self.group.gid, str(self.group.gid), 0, True,
                      {"gid": self.group.gid}):
            with self.subTest(given=given):
                with self.assertRaises(ContractRefusal) as caught:
                    self.home().materialize(
                        credentials.resolved_delivery(("api",),
                                                      profile=PROFILE),
                        attempt_id="attempt-1", workspace_group=given,
                        credential_provider=self.provider())
                self.assertIn("configured workspace group",
                              str(caught.exception))
                self.assertFalse(
                    os.path.exists(self.home().volatile_root("attempt-1")),
                    "a refused group still made a root")
                self.assertFalse(live_secret(BEARER),
                                 "a refused group still armed the registry")


class TheAuthorizedSetIsBounded(CredentialCase):
    """W26284 PLAN 1: `MAX_SLOTS` was enforced and never observed.

    The bound is not decoration -- the delivery becomes that many mounts, that
    many files and that many registry entries, so an unbounded list is an
    unbounded act. Measured: raising the constant to 100000 changed no verdict.
    """

    def test_the_bound_is_exactly_sixteen(self):
        self.assertEqual(credentials.MAX_SLOTS, 16)

    def test_more_slots_than_the_bound_refuses(self):
        names = tuple(f"slot{index:02d}" for index in
                      range(credentials.MAX_SLOTS + 1))
        with self.assertRaises(ContractRefusal) as caught:
            credentials.resolved_delivery(
                names, profile={name: {"provider": "vault",
                                       "reference": f"kv/{name}"}
                                for name in names})
        self.assertEqual(caught.exception.code, "limit")

    def test_exactly_the_bound_is_allowed(self):
        """Or the rule would be a way of refusing everything."""
        names = tuple(f"slot{index:02d}" for index in
                      range(credentials.MAX_SLOTS))
        resolved = credentials.resolved_delivery(
            names, profile={name: {"provider": "vault",
                                   "reference": f"kv/{name}"}
                            for name in names})
        self.assertEqual(len(resolved), credentials.MAX_SLOTS)

    def test_the_adapter_refuses_more_mounts_than_slots(self):
        """The same bound at the adapter, which composes the binds.

        A separate owner from the one above -- `_credential_mounts` is handed
        pairs rather than an assignment -- so it is a separate rule and needed
        its own case.
        """
        pairs = tuple((os.path.join(self.home_place, f"s{index}"),
                       f"{credentials.CREDENTIAL_ROOT}/s{index}")
                      for index in range(credentials.MAX_SLOTS + 1))
        with self.assertRaises(ContractRefusal):
            oci._credential_mounts(pairs)


class AFailedMaterializationRemovesBeforeItForgets(CredentialCase):
    """W26284 PLAN 1: the failure path's ORDER was unobserved.

    A registry released while the bytes are still on disk says a credential is
    dead while it is readable -- the same rule teardown is held to, on the path
    that runs when a delivery never completes. Measured: swapping the two
    changed no verdict.
    """

    def test_the_root_is_gone_before_the_bearer_is_forgotten(self):
        seen = {}
        discard = credentials._discard

        def watched(root):
            seen["live_at_discard"] = live_secret(BEARER)
            answer = discard(root)
            seen["gone_after_discard"] = not os.path.exists(root)
            return answer

        credentials._discard = watched
        try:
            # The SECOND slot fails, so the first is already written and
            # live when the discard runs. The provider capability is handed
            # (provider, reference) rather than the slot name -- measured, my
            # first version keyed on the name and never raised at all.
            calls = []

            def failing(provider, reference):
                calls.append(reference)
                if len(calls) == 2:
                    # `unavailable/source-provider` is the pairing the
                    # taxonomy actually has for a provider that cannot answer;
                    # the closed pairing refused my first spelling, which is
                    # the check doing its job.
                    raise ContractRefusal("unavailable", "source-provider",
                                          "the provider is down")
                return BEARER

            with self.assertRaises(ContractRefusal):
                self.home().materialize(
                    credentials.resolved_delivery(("api", "signing"),
                                                  profile=PROFILE),
                    attempt_id="attempt-1", credential_provider=failing,
                        workspace_group=self.group)
        finally:
            credentials._discard = discard
        self.assertTrue(seen["live_at_discard"],
                        "the bearer was forgotten before its file was removed")
        self.assertTrue(seen["gone_after_discard"])
        self.assertFalse(live_secret(BEARER),
                         "the bearer stayed live after a proved removal")

    def test_a_removal_that_cannot_be_proved_keeps_every_bearer_live(self):
        """W26284 review [P1]: the ORDER was observed and the ANSWER was not.

        `_discard` exists to report whether the root is GONE, and this path
        threw that answer away and forgot every bearer regardless. A
        filesystem that refused the removal therefore left the bytes readable
        while the registry guarding every later §13 scan was disarmed — a
        check that cannot fail, which is worse than no check because it reads
        as evidence.

        The case above watches a SUCCESSFUL removal, which is why it could be
        green while this was unsafe. This one drives the false answer.
        """
        discard = credentials._discard
        credentials._discard = lambda root: False
        self.addCleanup(setattr, credentials, "_discard", discard)
        calls = []

        def failing(provider, reference):
            calls.append(reference)
            if len(calls) == 2:
                raise ContractRefusal("unavailable", "source-provider",
                                      "the provider is down")
            return BEARER

        with self.assertRaises(ContractRefusal) as caught:
            self.home().materialize(
                credentials.resolved_delivery(("api", "signing"),
                                              profile=PROFILE),
                attempt_id="attempt-1", credential_provider=failing,
                    workspace_group=self.group)
        # THE ENDING IS ITS OWN, and it is not the provider's failure wearing
        # a different hat: what an operator has to act on is a stranded
        # bearer, not a provider that was down a moment ago.
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "credential-lifetime"))
        # AND NOTHING WAS FORGOTTEN. The root is still there, so the registry
        # stays armed over bytes that are still readable.
        credentials._discard = discard
        root = self.home().volatile_root("attempt-1")
        self.assertTrue(os.path.lexists(root))
        self.assertTrue(live_secret(BEARER),
                        "a bearer was forgotten while its file remained")
        # The fixture removes what the component correctly refused to claim
        # was gone.
        discard(root)
        while live_secret(BEARER):
            forget_secret(BEARER)


class EveryPublicDoorOwnsWhatItIsHanded(CredentialCase):
    """The doors this module exposes, driven with operands nobody composed.

    `resolved_delivery` composes exactly the shape `materialize` wants, and
    `materialize`/`adopt` compose exactly the shape `Delivery` wants -- so it
    is tempting to own each value once and trust it downstream. These are
    public functions and a public constructor: what actually reaches them is
    whatever a caller passes, and an object that teardown, mounting and the
    durable record all read is one whose members should be true of it whoever
    built it.
    """

    def test_a_credential_home_is_an_absolute_canonical_path(self):
        for spoiled in ("relative/place", "/srv/../etc", "", 7, None):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    credentials.CredentialHome(spoiled)

    def test_materialize_owns_a_resolution_it_did_not_compose(self):
        for spoiled in ("not a list",
                        [{"slot": "api", "provider": "vault"}],
                        [{"slot": "../escape", "provider": "vault",
                          "reference": "kv/one"}],
                        [{"slot": "api", "provider": 7,
                          "reference": "kv/one"}],
                        [{"slot": "api", "provider": "vault",
                          "reference": None}]):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    self.home().materialize(
                        spoiled, attempt_id="attempt-1",
                        workspace_group=self.group,
            credential_provider=self.provider())
        self.assertFalse(
            os.path.exists(self.home().volatile_root("attempt-1")))

    def test_a_delivery_owns_its_own_members(self):
        whole = {"attempt_id": "attempt-1", "root": "/srv/a/credentials",
                 "slots": [{"slot": "api", "provider": "vault",
                            "target": "/run/baton/credentials/api"}],
                 "state": "live", "bearers": {"api": BEARER}}
        credentials.Delivery(**whole)
        for member, spoiled in (("attempt_id", 7), ("root", None),
                                ("slots", "not a list"),
                                ("slots", [{"slot": "api"}]),
                                ("state", "invented"),
                                ("bearers", ["api"]),
                                ("bearers", {"../escape": BEARER})):
            with self.subTest(member=member, spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    credentials.Delivery(**dict(whole, **{member: spoiled}))

    def test_the_durable_write_owns_the_record_before_it_writes_it(self):
        """A document missing `slots` is a record `adopt` would refuse forever
        after this call had already reported success."""
        for spoiled in ({"note": "not a lifecycle record"}, "prose", None):
            with self.subTest(spoiled=spoiled):
                with self.assertRaises(ContractRefusal):
                    self.home().written_state("attempt-1", spoiled)


class TheWorkerSeesOnlyTheFixedRoot(CredentialCase):

    def vector(self, **overrides):
        body = {"image_digest": IDENTITY["image_digest"],
                "labels": self.labels(), "assignment_roots":
                    {"inputs": self.inputs, "workspace": self.workspace},
                "posture": "execution", "name": "baton-v12-1",
                # W33936: an execution vector names the configured group.
                "workspace_group": self.group}
        body.update(overrides)
        return oci.run_vector("docker", **body)

    def labels(self, **overrides):
        from baton_v12.worker_manager import documents
        body = {"runtime_attempt_id": "attempt-1", "authority_uuid": UUID,
                "work_id": JOB, "participant": "baton.claude", "generation": 1,
                "principal": CONTEXT["principal"],
                "effective_scope": CONTEXT["effective_scope"],
                "profile_digest": IDENTITY["profile_digest"],
                "policy_digest": IDENTITY["policy_digest"],
                "adapter_digest": IDENTITY["adapter_digest"]}
        body.update(overrides)
        return documents.runtime_labels(**body)

    def test_a_delivery_becomes_one_read_only_bind_per_slot(self):
        delivered = self.delivery(slots=("api", "signing"))
        argv = self.vector(credentials_delivered=delivered.mounts())
        for name in ("api", "signing"):
            self.assertIn(
                f"type=bind,source={os.path.join(delivered.root, name)},"
                f"target=/run/baton/credentials/{name},readonly=true", argv)
        self.home().tear_down(delivered)

    def test_a_target_outside_the_fixed_root_is_refused(self):
        delivered = self.delivery()
        source = os.path.join(delivered.root, "api")
        for target in ("/run/baton/api", "/run/baton/credentials/sub/api",
                       "/etc/api", "run/baton/credentials/api",
                       "/run/baton/credentials"):
            with self.subTest(target=target):
                with self.assertRaises(ContractRefusal):
                    self.vector(credentials_delivered=((source, target),))
        self.home().tear_down(delivered)

    def test_a_slot_delivered_under_another_name_is_refused(self):
        """A file renamed on the way in is one nobody can trace back to what
        was authorized."""
        delivered = self.delivery()
        with self.assertRaises(ContractRefusal):
            self.vector(credentials_delivered=(
                (os.path.join(delivered.root, "api"),
                 "/run/baton/credentials/signing"),))
        self.home().tear_down(delivered)

    def test_two_deliveries_cannot_land_on_one_entry(self):
        delivered = self.delivery()
        source = os.path.join(delivered.root, "api")
        with self.assertRaises(ContractRefusal):
            self.vector(credentials_delivered=(
                (source, "/run/baton/credentials/api"),
                (source, "/run/baton/credentials/api")))
        self.home().tear_down(delivered)

    def test_an_assignment_mount_may_not_contain_the_credential_root(self):
        """An assignment mount over `/run/baton/credentials` would decide what
        the worker reads there, which is the one thing the fixed root exists to
        take away from it."""
        delivered = self.delivery()
        for target in ("/run/baton/credentials", "/run/baton", "/run"):
            with self.subTest(target=target):
                with self.assertRaises(ContractRefusal):
                    self.vector(
                        mounts=({"source": self.workspace, "target": target,
                                 "writable": False},),
                        credentials_delivered=delivered.mounts())
        self.home().tear_down(delivered)

    def test_no_bearer_reaches_the_argv(self):
        """§13's argv half, driven rather than asserted about. Every
        process on the host can read another's command line, so the whole
        vector is walked while the registry is live.

        W26284 review [P1] MOVED WHERE THAT WALK LIVES, and this case moved
        with it. `run_vector` used to sweep the vector IT composed and nothing
        swept the others, so the duplicate probe and the refusal path's own
        listing reached the engine unswept. The rule now has one owner —
        `EnginePort.__call__`, which is what every vector actually passes
        through — so the reachability half is driven THERE. What is asserted is
        unchanged: a live bearer does not reach a command line, and the guard
        that stops it can fail.
        """
        delivered = self.delivery()
        argv = self.vector(credentials_delivered=delivered.mounts())
        self.assertTrue(live_secret(BEARER))
        for piece in argv:
            self.assertNotIn(BEARER, piece)
        # And the walk is REACHABLE, at the one boundary that owns it: an argv
        # carrying the live value is refused instead of being handed to the
        # engine, whatever composed it.
        reached = []
        port = oci.EnginePort(lambda one: reached.append(tuple(one))
                              or {"status": 0, "stdout": "", "stderr": ""})
        with self.assertRaises(ContractRefusal) as caught:
            port(self.vector(labels=self.labels(participant=BEARER),
                             credentials_delivered=delivered.mounts()))
        self.assertEqual(caught.exception.code, "secret-leak")
        self.assertEqual(reached, [], "the engine was reached anyway")
        self.home().tear_down(delivered)

    def test_the_duplicate_probe_cannot_carry_a_bearer_to_the_engine(self):
        """W26284 review [P1]: the FIRST engine call was unswept.

        `start` asks the engine for duplicate candidates before any vector is
        composed, and the candidate selector puts `runtime_attempt_id` into a
        `--filter` argument. A provider answer is explicitly untrusted, so a
        bearer equal to that attempt identity was handed to the daemon by the
        very call that runs before anything else happens — and the later
        run-vector sweep, which was the only one there was, refused far too
        late to matter.

        The case that existed chose `participant` precisely because it is NOT
        a candidate filter. It proved the late sweep worked and said nothing
        about the early leak, which is why this one uses the attempt label.
        """
        reached = []

        class Engine:
            def __call__(self, argv):
                reached.append(tuple(argv))
                return {"status": 0, "stdout": "", "stderr": ""}

        delivered = self.home().materialize(
            credentials.resolved_delivery(("api",), profile=PROFILE),
            attempt_id=BEARER, workspace_group=self.group,
        credential_provider=self.provider())
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=self.launched())
        with self.assertRaises(ContractRefusal) as caught:
            built.start({"labels": self.labels(runtime_attempt_id=BEARER),
                         "operation_id": "runtime.start:w26284"})
        self.assertEqual(caught.exception.code, "secret-leak")
        # NOTHING AT ALL REACHED THE ENGINE. Not "no run" — no call: the
        # duplicate probe is the first invocation and it is the one that used
        # to leak.
        self.assertEqual(reached, [])
        self.assertTrue(live_secret(BEARER))
        credentials._discard(delivered.root)
        while live_secret(BEARER):
            forget_secret(BEARER)


class DurableStateNamesTheSlotAndNeverTheBearer(CredentialCase):

    def test_the_lifecycle_record_carries_slot_provider_and_state(self):
        delivered = self.delivery(slots=("api", "signing"))
        record = delivered.record(runtime_id="runtime-1")
        self.assertEqual(record["container_root"], "/run/baton/credentials")
        self.assertEqual([one["slot"] for one in record["slots"]],
                         ["api", "signing"])
        self.assertEqual({one["provider"] for one in record["slots"]},
                         {"vault"})
        self.assertEqual(record["lifecycle_state"], "live")
        # NO BEARER AND NO DIGEST OF ONE -- a reusable digest is a bearer
        # somebody can confirm a guess against.
        written = json.dumps(record)
        for value in (BEARER, SECOND):
            self.assertNotIn(value, written)
        import hashlib
        for value in (BEARER, SECOND):
            self.assertNotIn(hashlib.sha256(value.encode()).hexdigest(),
                             written)
        self.home().tear_down(delivered)

    def test_a_record_that_would_carry_a_live_bearer_refuses(self):
        """Non-vacuous because the bearer is live at exactly this moment."""
        remember_secret(BEARER)
        self.addCleanup(forget_secret, BEARER)
        with self.assertRaises(ContractRefusal) as caught:
            self.home().written_state("attempt-1", {
                "attempt_id": "attempt-1", "runtime_id": "runtime-1",
                "credential_root": self.home().volatile_root("attempt-1"),
                "container_root": "/run/baton/credentials",
                # THE BEARER, SMUGGLED IN A MEMBER §13 DOES NOT NAME. The rule
                # is containment at any depth rather than a naming convention,
                # and this record is otherwise exactly the right shape -- so
                # the walk is what refuses it and not the document owner.
                "slots": [{"slot": "api", "provider": f"vault {BEARER}",
                           "target": "/run/baton/credentials/api"}],
                "lifecycle_state": "live"})
        self.assertEqual(caught.exception.code, "secret-leak")

    def test_the_record_is_published_atomically(self):
        delivered = self.delivery()
        stopped = credentials.os.replace

        def stop(source, target):
            raise KeyboardInterrupt("stopped between the write and the rename")

        credentials.os.replace = stop
        try:
            with self.assertRaises(KeyboardInterrupt):
                self.home().written_state(
                    "attempt-1",
                    delivered.record(runtime_id="runtime-1"))
        finally:
            credentials.os.replace = stopped
        self.assertIsNone(self.home().read_state("attempt-1"))
        self.home().tear_down(delivered)

    def test_an_unreadable_record_refuses_rather_than_faulting(self):
        place = self.home().state_path("attempt-1")
        os.makedirs(os.path.dirname(place), exist_ok=True)
        with open(place, "wb"):
            pass
        with self.assertRaises(ContractRefusal):
            self.home().read_state("attempt-1")


class OneOrderedTeardownOnEveryEnding(CredentialCase):

    def test_teardown_removes_everything_and_then_forgets(self):
        delivered = self.delivery(slots=("api", "signing"))
        self.home().written_state("attempt-1",
                                  delivered.record(runtime_id="runtime-1"))
        self.assertTrue(live_secret(BEARER))
        answer = self.home().tear_down(delivered)
        self.assertEqual(answer["lifecycle_state"], "torn-down")
        self.assertFalse(os.path.exists(delivered.root))
        self.assertIsNone(self.home().read_state("attempt-1"))
        self.assertFalse(live_secret(BEARER))
        self.assertFalse(live_secret(SECOND))

    def test_an_unprovable_removal_refuses_and_keeps_the_bearer_live(self):
        """Cleanup uncertainty is not settlement and is not a free worker slot.
        The bearer stays registered, so anything sealed afterwards is still
        checked against it."""
        delivered = self.delivery()
        removed = credentials.os.remove

        def refuse(place):
            raise PermissionError("the root is not this manager's today")

        credentials.os.remove = refuse
        try:
            with self.assertRaises(ContractRefusal) as caught:
                self.home().tear_down(delivered)
        finally:
            credentials.os.remove = removed
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "credential-lifetime"))
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(delivered)

    def test_a_removal_that_did_not_happen_is_not_a_teardown(self):
        """The removal's own error is not the answer -- the state afterwards
        is. A filesystem that reports success while the file is still there is
        exactly what proving absence is for, and it is a different case from
        one that raises."""
        delivered = self.delivery()
        removed = credentials.os.remove
        credentials.os.remove = lambda place: None
        try:
            with self.assertRaises(ContractRefusal) as caught:
                self.home().tear_down(delivered)
        finally:
            credentials.os.remove = removed
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "credential-lifetime"))
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(delivered)

    def test_destroy_tears_down_once_the_runtime_is_proved_gone(self):
        delivered = self.delivery()
        built = self.adapter(delivered)
        built.observe = lambda runtime_id: {"state": "absent",
                                            "why": "the engine says so"}
        answer = built.destroy(self.command())
        self.assertEqual(answer["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(os.path.exists(delivered.root))
        self.assertFalse(live_secret(BEARER))

    def test_an_engine_declined_start_releases_the_undelivered_credential(self):
        """A start the engine refuses has no runtime that can retain the
        mount. It is still a failure ending and must not strand the bearer."""
        from baton_v12.worker_manager import documents

        class Engine:
            def __call__(self, argv):
                if "ps" in argv:
                    return {"status": 0, "stdout": "", "stderr": ""}
                return {"status": 1, "stdout": "", "stderr": "declined"}

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=self.launched())
        labels = documents.runtime_labels(
            runtime_attempt_id="attempt-1", authority_uuid=UUID,
            work_id=JOB, participant="baton.claude", generation=1,
            principal=CONTEXT["principal"],
            effective_scope=CONTEXT["effective_scope"],
            profile_digest=IDENTITY["profile_digest"],
            policy_digest=IDENTITY["policy_digest"],
            adapter_digest=IDENTITY["adapter_digest"])
        with self.assertRaises(ContractRefusal):
            built.start({"labels": labels,
                         "operation_id": "runtime.start:1"})
        self.assertFalse(os.path.exists(delivered.root))
        self.assertFalse(live_secret(BEARER))

    def test_a_declined_start_with_a_surviving_runtime_stays_unresolved(self):
        """A declined start is strong evidence that nothing holds the mount and
        it is not proof: an engine can create a container and then fail. So the
        settlement asks, and a runtime that carries this attempt's labels keeps
        the credential explicitly unresolved."""
        case = self

        class Engine:
            def __call__(self, argv):
                if "ps" in argv:
                    row = {"ID": "runtime-1",
                           "Image": IDENTITY["image_digest"],
                           "Labels": {f"baton.v12.{name}": str(value)
                                      for name, value in
                                      case.runtime_labels().items()}}
                    return {"status": 0, "stdout": json.dumps(row),
                            "stderr": ""}
                return {"status": 1, "stdout": "", "stderr": "declined"}

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=self.launched())
        with self.assertRaises(ContractRefusal) as caught:
            built.start({"labels": self.runtime_labels(),
                         "operation_id": "runtime.start:1"})
        # The duplicate-start guard refuses FIRST, and it is the same shape:
        # a runtime carrying these labels may hold the mount, so the delivery
        # is settled as unresolved rather than torn down.
        self.assertIn("already carry", caught.exception.message)
        self.assertIn("unresolved", caught.exception.message)
        self.assertTrue(os.path.exists(delivered.root))
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(delivered)

    def test_a_start_the_engine_never_named_settles_the_credential(self):
        """No runtime id means no lifecycle record, so nothing later could
        adopt or tear this delivery down by name. It is a failure ending."""
        class Engine:
            def __call__(self, argv):
                return {"status": 0, "stdout": "  \n", "stderr": ""}

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=self.launched())
        answer = built.start({"labels": self.runtime_labels(),
                              "operation_id": "runtime.start:1"})
        self.assertIsNone(answer["runtime_id"])
        self.assertEqual(answer["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(os.path.exists(delivered.root))
        self.assertFalse(live_secret(BEARER))

    def test_a_delivery_cannot_start_under_another_attempts_labels(self):
        """The mounted root is keyed by attempt-1. Labelling its runtime as
        attempt-2 would make reconciliation and restart look for the delivery
        under a different identity."""
        class Engine:
            def __call__(self, argv):
                if "ps" in argv:
                    return {"status": 0, "stdout": "", "stderr": ""}
                return {"status": 0, "stdout": "runtime-2\n", "stderr": ""}

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=self.launched())
        labels = dict(self.runtime_labels(), runtime_attempt_id="attempt-2")
        with self.assertRaises(ContractRefusal):
            built.start({"labels": labels,
                         "operation_id": "runtime.start:2"})
        self.assertTrue(live_secret(BEARER))

    def test_a_missing_launch_document_still_settles_the_credential(self):
        """W26291 second re-review [P1]: the refusal bypassed the settlement.

        The missing-launch check called `_denied` directly, on the reasoning
        that nothing had been created yet — which is true only when no OTHER
        provider has materialized anything. A canonical adapter may already
        hold a credential delivery whose root and live registration exist
        before `start` is called, and that refusal stranded the bearer on a
        path with no runtime id for the destroy crossing to name.
        """
        class Engine:
            def __call__(self, argv):
                if "ps" in argv:
                    return {"status": 0, "stdout": "", "stderr": ""}
                raise AssertionError("a start with no document reached a run")

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=None)
        with self.assertRaises(ContractRefusal) as caught:
            built.start({"labels": self.runtime_labels(),
                         "operation_id": "runtime.start:1"})
        self.assertIn("no launch document", caught.exception.message)
        # SETTLED, not merely refused: the ending names the credential and the
        # bytes are gone.
        self.assertIn("credential delivery is torn-down",
                      caught.exception.message)
        self.assertFalse(os.path.exists(delivered.root))
        self.assertFalse(live_secret(BEARER))

    def test_a_missing_launch_document_with_a_live_runtime_stays_unresolved(
            self):
        """The settlement ASKS, and a runtime carrying this attempt's labels
        may still hold the mount — so the credential is explicitly unresolved
        rather than torn down under it."""
        case = self

        class Engine:
            def __call__(self, argv):
                if "ps" in argv:
                    row = {"ID": "runtime-1",
                           "Image": IDENTITY["image_digest"],
                           "Labels": {f"baton.v12.{name}": str(value)
                                      for name, value in
                                      case.runtime_labels().items()}}
                    return {"status": 0, "stdout": json.dumps(row),
                            "stderr": ""}
                raise AssertionError("a start with no document reached a run")

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=None)
        with self.assertRaises(ContractRefusal) as caught:
            built.start({"labels": self.runtime_labels(),
                         "operation_id": "runtime.start:1"})
        self.assertIn("credential delivery is unresolved",
                      caught.exception.message)
        self.assertTrue(os.path.exists(delivered.root))
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(delivered)

    def test_a_missing_launch_document_with_an_unusable_listing_is_unresolved(
            self):
        """W26291 third review [P2]: the LISTING ITSELF failing is a distinct
        branch from a listing that succeeds and names a runtime.

        A surviving-runtime case is the adapter INFERRING possible use from a
        row the engine really answered. This is the other half: the inventory
        is unavailable or untrustworthy, so the adapter knows nothing at all —
        and an unavailable inventory must never become proved absence, because
        that would tear a credential root down under a container nobody could
        rule out.
        """
        for what, answer in (
                ("the engine refused the listing",
                 {"status": 1, "stdout": "", "stderr": "the daemon is down"}),
                ("the listing is not readable",
                 {"status": 0, "stdout": "{not json", "stderr": ""}),
                ("the listing names no runtime this manager can own",
                 {"status": 0, "stdout": json.dumps({"Labels": {}}),
                  "stderr": ""})):
            with self.subTest(what=what):
                class Engine:
                    def __call__(self, argv):
                        if "ps" in argv:
                            return answer
                        raise AssertionError(
                            "a start with no document reached a run")

                delivered = self.home().materialize(
                    credentials.resolved_delivery(("api",), profile=PROFILE),
                    attempt_id="attempt-1",
                    workspace_group=self.group,
                    credential_provider=lambda _p, _r: BEARER)
                built = oci.OciAdapter(
                    "docker", Engine(), identity=dict(IDENTITY),
                    assignment_roots={"inputs": self.inputs,
                                      "workspace": self.workspace},
                    posture="execution", workspace_group=self.group, credential_delivery=delivered,
                    launch_delivery=None)
                with self.assertRaises(ContractRefusal) as caught:
                    built.start({"labels": self.runtime_labels(),
                                 "operation_id": "runtime.start:1"})
                self.assertIn("no launch document", caught.exception.message)
                # UNRESOLVED, never torn down: nothing was established, and an
                # inventory this manager could not read is not absence.
                self.assertIn("credential delivery is unresolved",
                              caught.exception.message)
                self.assertTrue(os.path.exists(delivered.root))
                self.assertTrue(live_secret(BEARER))
                # The fixture ends what the adapter correctly refused to call
                # ended, so the next spelling of an unusable listing starts
                # from a clean root.
                self.home().tear_down(delivered)
                self.assertFalse(os.path.exists(delivered.root))

    def test_a_missing_launch_document_infers_nothing_about_another_attempt(
            self):
        """AND THE MISMATCH STILL REFUSES ABOVE THE SETTLEMENT.

        `_refused_start` settles by asking which runtimes carry THESE labels.
        A credential belonging to a different attempt must refuse before that
        question is asked at all: an empty answer about attempt 2 says nothing
        about attempt 1's runtime, and acting on it would be inferring absence
        from the wrong question.
        """
        reached = []

        class Engine:
            def __call__(self, argv):
                reached.append(tuple(argv))
                return {"status": 0, "stdout": "", "stderr": ""}

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=None)
        labels = dict(self.runtime_labels(), runtime_attempt_id="attempt-2")
        with self.assertRaises(ContractRefusal) as caught:
            built.start({"labels": labels, "operation_id": "runtime.start:1"})
        self.assertIn("credential root of attempt", caught.exception.message)
        # NOTHING WAS ASKED, because nothing could be answered.
        self.assertEqual(reached, [])
        self.assertTrue(os.path.exists(delivered.root))
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(delivered)

    def test_a_pre_engine_vector_refusal_settles_the_credential(self):
        """Mount validation can refuse after the duplicate probe but before
        the engine is asked to create anything. That is still a refusing exit
        from start, with absence already proved by the probe."""
        class Engine:
            def __call__(self, argv):
                if "ps" in argv:
                    return {"status": 0, "stdout": "", "stderr": ""}
                raise AssertionError("an invalid vector reached the engine")

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group,
            mounts=({"source": self.workspace,
                     "target": "/run/baton/credentials",
                     "writable": False},),
            credential_delivery=delivered,
            launch_delivery=self.launched())
        with self.assertRaises(ContractRefusal):
            built.start({"labels": self.runtime_labels(),
                         "operation_id": "runtime.start:1"})
        self.assertFalse(os.path.exists(delivered.root))
        self.assertFalse(live_secret(BEARER))

    def test_a_started_runtime_with_an_invalid_identity_is_explicitly_unresolved(self):
        """The engine has already acted when its stdout is interpreted. If
        the returned runtime id is not one this manager can own, the start
        refusal still has to run the credential lifecycle rather than escape
        between creation and lifecycle-record publication.
        """
        case = self
        bad = chr(0xDCFF)

        class Engine:
            def __init__(self):
                self.created = False

            def __call__(self, argv):
                if "ps" in argv:
                    if not self.created:
                        return {"status": 0, "stdout": "", "stderr": ""}
                    row = {"ID": bad,
                           "Image": IDENTITY["image_digest"],
                           "Labels": {f"baton.v12.{name}": str(value)
                                      for name, value in
                                      case.runtime_labels().items()}}
                    return {"status": 0, "stdout": json.dumps(row),
                            "stderr": ""}
                self.created = True
                return {"status": 0, "stdout": bad + "\n",
                        "stderr": ""}

        delivered = self.delivery()
        built = oci.OciAdapter(
            "docker", Engine(), identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivered,
            launch_delivery=self.launched())
        with self.assertRaises(ContractRefusal) as caught:
            built.start({"labels": self.runtime_labels(),
                         "operation_id": "runtime.start:1"})
        self.assertIn("unresolved", caught.exception.message.lower())
        self.assertTrue(os.path.exists(delivered.root))
        self.assertTrue(live_secret(BEARER))

    def test_a_runtime_not_proved_gone_leaves_the_lifecycle_unresolved(self):
        """A container this manager cannot say is absent may still be reading
        the mount. Removing the file under it would be reporting an ending that
        has not happened."""
        delivered = self.delivery()
        built = self.adapter(delivered)
        built.observe = lambda runtime_id: {"state": "uncertain",
                                            "why": "the engine said nothing"}
        answer = built.destroy(self.command())
        self.assertEqual(answer["credentials"]["lifecycle_state"],
                         "unresolved")
        self.assertNotEqual(answer["state"], "absent")
        self.assertTrue(os.path.exists(delivered.root))
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(delivered)

    def test_a_cancelled_attempt_settles_through_the_same_act(self):
        """The CANCELLATION ending, driven rather than counted.

        Fourth review: do not substitute source-text call counts for driven
        endings. A cancellation reaches this adapter as an ordered stop and
        then the same destroy every other ending takes, so this drives both
        and asserts the credential settled once at the end of it.
        """
        delivered = self.delivery()
        built = self.adapter(delivered)
        states = iter([{"state": "quiescent", "why": "the stop was accepted"},
                       {"state": "absent", "why": "the engine says so"}])
        built.observe = lambda runtime_id: next(states)

        ordered = built.stop({"runtime_id": "runtime-1",
                              "operation_id": "runtime.stop:1"})
        self.assertEqual(ordered["state"], "quiescent")
        self.assertTrue(live_secret(BEARER),
                        "a stopped runtime may still hold the mount")

        answer = built.destroy(self.command())
        self.assertEqual(answer["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(os.path.exists(delivered.root))
        self.assertFalse(live_secret(BEARER))

    def test_a_failure_ending_settles_through_the_same_act(self):
        """The FAILURE ending. `destroy` carries the manager's authorization
        whatever the disposition was, so a failed attempt settles exactly as a
        completed one does -- there is no second path to drift from."""
        delivered = self.delivery()
        built = self.adapter(delivered)
        built.observe = lambda runtime_id: {"state": "absent",
                                            "why": "the engine says so"}
        answer = built.destroy(self.command(
            intake_receipt_digest=DIGEST, retention_policy_digest=DIGEST))
        self.assertEqual(answer["credentials"]["lifecycle_state"],
                         "torn-down")
        self.assertFalse(live_secret(BEARER))

    def runtime_labels(self):
        from baton_v12.worker_manager import documents
        return documents.runtime_labels(
            runtime_attempt_id="attempt-1", authority_uuid=UUID, work_id=JOB,
            participant="baton.claude", generation=1,
            principal=CONTEXT["principal"],
            effective_scope=CONTEXT["effective_scope"],
            profile_digest=IDENTITY["profile_digest"],
            policy_digest=IDENTITY["policy_digest"],
            adapter_digest=IDENTITY["adapter_digest"])

    def command(self, **overrides):
        body = {"assignment_ref": dict(ASSIGNMENT),
                "runtime_attempt_id": "attempt-1", "runtime_id": "runtime-1",
                "intake_receipt_digest": DIGEST,
                "retention_policy_digest": DIGEST}
        body.update(overrides)
        return body


class RestartAdoptsOnlyAnExactAgreement(CredentialCase):

    def published(self, delivered):
        return self.home().written_state(
            "attempt-1", delivered.record(runtime_id="runtime-1"))

    def test_an_exact_record_is_adopted_and_the_bearer_re_registered(self):
        """A restarted manager that adopted WITHOUT re-registering would seal
        that attempt's output with the leak check silently disarmed, and a
        check that cannot fail is worse than no check because it reads as
        evidence."""
        delivered = self.delivery()
        record = self.published(delivered)
        # The restart: this process forgets everything it held in memory.
        forget_secret(BEARER)
        self.assertFalse(live_secret(BEARER))

        adopted = self.home().adopt(record,
                                    attempt_id="attempt-1",
                                    runtime_id="runtime-1", workspace_group=self.group)
        self.assertEqual(adopted.state, "adopted")
        self.assertTrue(live_secret(BEARER))
        self.assertEqual([target for _source, target in adopted.mounts()],
                         ["/run/baton/credentials/api"])
        self.home().tear_down(adopted)

    def restarted(self, delivered):
        """The restart: this process forgets what it held in memory."""
        record = self.published(delivered)
        forget_secret(BEARER)
        self.assertFalse(live_secret(BEARER))
        return record

    def refuses_recovery(self, record, why):
        """Adoption refuses, and NOTHING was re-registered.

        The second half is the one that matters. Recovery's whole job is to
        put the bearer back in the registry, so a refusal that had already
        done that would leave a live value no `Delivery` owns -- the exact
        shape this module's fourth review found and fixed.
        """
        with self.assertRaises(ContractRefusal) as caught:
            self.home().adopt(record, attempt_id="attempt-1",
                              runtime_id="runtime-1",
                              workspace_group=self.group)
        self.assertIn(why, str(caught.exception))
        self.assertFalse(live_secret(BEARER),
                         "a refused recovery re-registered the bearer anyway")

    def test_a_widened_root_is_refused_before_any_bearer_is_read(self):
        """W52800 review [P0]. The ruling has TWO halves and this is the one
        recovery did not check.

        The slot is group-readable at `0640` ONLY because the root above it is
        manager-owned at `0700`, so nothing else can traverse to it. A root at
        `0770` hands every host member of the configured workspace group a
        path to the bearer -- the group grant was scoped to a container
        holding it as a supplementary group, not to every account on the host.
        """
        delivered = self.delivery()
        record = self.restarted(delivered)
        os.chmod(delivered.root, 0o770)

        self.refuses_recovery(record, "is mode 0o770")
        os.chmod(delivered.root, 0o700)
        self.home().tear_down(self.home().adopt(
            record, attempt_id="attempt-1", runtime_id="runtime-1",
            workspace_group=self.group))

    def test_a_substituted_root_is_refused_rather_than_followed(self):
        """A link where the root should be is refused AS ITSELF.

        `lstat` and not `stat`: resolving it would run every child check under
        a pathname whose custody nobody proved, which is what makes
        substitution worth attempting in the first place.
        """
        delivered = self.delivery()
        record = self.restarted(delivered)
        elsewhere = os.path.join(self.home_place, "elsewhere")
        os.makedirs(elsewhere, mode=0o700, exist_ok=True)
        # The real root moves aside so the recorded path resolves to a
        # directory this manager did make -- so what the refusal catches is
        # the SUBSTITUTION rather than a missing file.
        moved = delivered.root + ".moved"
        os.rename(delivered.root, moved)
        os.symlink(elsewhere, delivered.root)
        self.addCleanup(lambda: os.path.islink(delivered.root)
                        and os.unlink(delivered.root))

        self.refuses_recovery(record, "is mode")

        os.unlink(delivered.root)
        os.rename(moved, delivered.root)
        self.home().tear_down(self.home().adopt(
            record, attempt_id="attempt-1", runtime_id="runtime-1",
            workspace_group=self.group))

    def test_a_root_this_manager_cannot_interrogate_is_refused(self):
        """An `lstat` that fails is a REFUSAL, not an exception escaping.

        A door that promises a typed answer owes one even when the filesystem
        will not answer it. Driven by making the PARENT untraversable, which
        is a real state a host can be in rather than a mocked one.
        """
        delivered = self.delivery()
        record = self.restarted(delivered)
        parent = os.path.dirname(delivered.root)
        self.addCleanup(os.chmod, parent, 0o700)
        os.chmod(parent, 0o000)
        try:
            self.refuses_recovery(record, "could not be interrogated")
        finally:
            os.chmod(parent, 0o700)
        self.home().tear_down(self.home().adopt(
            record, attempt_id="attempt-1", runtime_id="runtime-1",
            workspace_group=self.group))

    def test_a_slot_whose_mode_or_kind_drifted_is_refused(self):
        """The child half, over state this process did not write.

        Each is a different way the delivered bearer stops being the thing
        this deployment ruled: a mode that widened, a mode that narrowed back
        to the superseded owner-only one, and a name that is no longer a
        regular file. All three are arranged on the REAL filesystem, because
        all three are things an unprivileged process can actually do to a file
        it owns.

        THE OTHER TWO FIELDS `_proved_slot` COMPARES -- owner and group -- are
        driven by the case below instead. Review 2026-08-31T15:45:28Z [P1]:
        this case used to name them and arrange neither. Its group arrangement
        called `chown(2)`, which answers `EINVAL` on this host for every gid
        including ones this process belongs to, so the subtest skipped and the
        comparison went undriven; and its name promised an owner case that was
        never written at all. Acceptance must not depend on privilege to give
        an inode away.
        """
        for what, spoil, why in (
                ("a widened mode", lambda place: os.chmod(place, 0o644),
                 "is not the delivery this manager writes"),
                ("a narrowed mode", lambda place: os.chmod(place, 0o600),
                 "is not the delivery this manager writes"),
                ("a link in its place", self._relinked,
                 "is not the delivery this manager writes")):
            with self.subTest(what=what):
                # A FRESH ATTEMPT PER ITERATION. A spoiled root is not one
                # this manager will materialize into again, and reusing the
                # name would make the next iteration refuse for the previous
                # one's reason.
                self.minted.clear()
                self._quiet()
                delivered = self.delivery()
                record = self.published(delivered)
                forget_secret(BEARER)
                place = os.path.join(delivered.root, "api")
                # THE ORPHAN GOES WHATEVER HAPPENS: a spoiled root left behind
                # makes the NEXT iteration refuse for the previous one's
                # reason, which is a case proving nothing about itself.
                try:
                    spoil(place)
                    with self.assertRaises(ContractRefusal) as caught:
                        self.home().adopt(record, attempt_id="attempt-1",
                                          runtime_id="runtime-1",
                                          workspace_group=self.group)
                    self.assertIn(why, str(caught.exception))
                    self.assertFalse(
                        live_secret(BEARER),
                        "a refused recovery re-registered the bearer anyway")
                finally:
                    self.home().discard_orphan("attempt-1")
                self.assertFalse(os.path.lexists(delivered.root),
                                 "the spoiled root survived its discard")

    def drifting(self, place, field):
        """Make `lstat` answer a drifted uid or gid for exactly one slot.

        WHAT THE FILESYSTEM WILL NOT ARRANGE, ASKED OF THE BOUNDARY DIRECTLY.
        `_proved_slot` decides on what `os.lstat` ANSWERS, so controlling that
        answer for the one path under test drives the owner and group
        comparisons deterministically, on every host, without this suite
        needing the privilege to chown an inode to somebody else -- which is
        the requirement the review set.

        EXACTLY ONE PATH, and everything else is the real answer: `adopt` also
        proves the ROOT through this call, and a substitution that answered for
        every path would be arranging a different test. Returns the restore,
        so the caller can put `os.lstat` back before the discard runs.
        """
        real = os.lstat

        def answering(target, *rest, **named):
            found = real(target, *rest, **named)
            if isinstance(target, str) and target == place:
                fields = list(found)
                # PLUS ONE, so the drifted identity is a different one and
                # nothing else about the slot changes: it is still a regular
                # file at the ruled mode, so this drives the uid/gid halves of
                # the comparison and only those.
                fields[field] += 1
                return os.stat_result(fields)
            return found

        os.lstat = answering
        return lambda: setattr(os, "lstat", real)

    def test_a_slot_whose_owner_or_group_drifted_is_refused(self):
        """The two identity fields, driven rather than promised.

        A recovered slot owned by somebody else, or granted to a group this
        deployment did not configure, is not the delivery this manager wrote --
        and reading a bearer back out of it would register a value another
        party's permissions govern. Both refusals must land BEFORE the read,
        which is why each case also requires the bearer still unregistered.
        """
        for what, field in (("a foreign owner", 4), ("a foreign group", 5)):
            with self.subTest(what=what):
                self.minted.clear()
                self._quiet()
                delivered = self.delivery()
                record = self.published(delivered)
                forget_secret(BEARER)
                place = os.path.join(delivered.root, "api")
                restore = self.drifting(place, field)
                try:
                    with self.assertRaises(ContractRefusal) as caught:
                        self.home().adopt(record, attempt_id="attempt-1",
                                          runtime_id="runtime-1",
                                          workspace_group=self.group)
                    self.assertIn("is not the delivery this manager writes",
                                  str(caught.exception))
                    self.assertFalse(
                        live_secret(BEARER),
                        "a refused recovery re-registered the bearer anyway")
                finally:
                    # THE REAL `lstat` BACK BEFORE THE DISCARD, so the cleanup
                    # acts on the filesystem rather than on the substitution.
                    restore()
                    self.home().discard_orphan("attempt-1")
                self.assertFalse(os.path.lexists(delivered.root),
                                 "the drifted root survived its discard")

    def test_the_drift_arrangement_can_actually_fail(self):
        """The substitution above is only evidence if it changes the answer.

        A wrapper that quietly returned the real `lstat` for every path would
        make both cases above pass against an implementation that compares
        nothing. So: the same delivery adopts cleanly with the real answer, and
        the drifted answer is the only difference between that and the refusal.
        """
        delivered = self.delivery()
        place = os.path.join(delivered.root, "api")
        restore = self.drifting(place, 4)
        try:
            drifted = os.lstat(place)
        finally:
            restore()
        honest = os.lstat(place)
        self.assertEqual(drifted.st_uid, honest.st_uid + 1)
        self.assertEqual(drifted.st_gid, honest.st_gid)
        self.assertEqual(stat.S_IMODE(drifted.st_mode), 0o640)
        # And an untouched path is untouched, which is what lets the ROOT keep
        # being proved for real while one slot is drifted.
        restore = self.drifting(place, 4)
        try:
            self.assertEqual(os.lstat(delivered.root).st_uid, os.getuid())
        finally:
            restore()
        record = self.published(delivered)
        forget_secret(BEARER)
        adopted = self.home().adopt(record, attempt_id="attempt-1",
                                    runtime_id="runtime-1",
                                    workspace_group=self.group)
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(adopted)

    @staticmethod
    def _relinked(place):
        target = place + ".real"
        os.rename(place, target)
        os.symlink(target, place)

    def test_any_disagreement_fails_closed(self):
        delivered = self.delivery()
        record = self.published(delivered)
        spoiled = (
            ("attempt_id", "attempt-2"),
            ("runtime_id", "runtime-2"),
            ("credential_root", "/tmp/somewhere-else"),
            ("container_root", "/run/baton/other"),
            ("lifecycle_state", "torn-down"),
        )
        for member, value in spoiled:
            with self.subTest(member=member):
                with self.assertRaises(ContractRefusal):
                    self.home().adopt(dict(record, **{member: value}),
                                      attempt_id="attempt-1",
                                      runtime_id="runtime-1",
                                  workspace_group=self.group)
        with self.subTest(member="target"):
            moved = dict(record, slots=[dict(record["slots"][0],
                                             target="/etc/api")])
            with self.assertRaises(ContractRefusal):
                self.home().adopt(moved,
                                  attempt_id="attempt-1",
                                  runtime_id="runtime-1", workspace_group=self.group)
        self.home().tear_down(delivered)

    def test_a_volatile_file_wider_than_the_bound_is_not_adoptable(self):
        """Registering a PREFIX of a bearer would arm every later leak check
        against a string that is not the secret -- a check that looks armed and
        cannot fire."""
        delivered = self.delivery()
        record = self.published(delivered)
        forget_secret(BEARER)
        with open(os.path.join(delivered.root, "api"), "wb") as handle:
            handle.write(b"x" * (credentials.MAX_BEARER + 1))
        with self.assertRaises(ContractRefusal):
            self.home().adopt(record, attempt_id="attempt-1",
                              runtime_id="runtime-1", workspace_group=self.group)

    def test_a_registration_that_cannot_finish_unwinds_completely(self):
        """The unwind, driven. Everything is proved before the first
        `remember_secret`, so this drives the one window that is left: a fault
        BETWEEN registrations. Nothing may stay live, because the object that
        would have owned those values never came into existence."""
        delivered = self.delivery(slots=("api", "signing"))
        record = self.published(delivered)
        forget_secret(BEARER)
        forget_secret(SECOND)
        built = credentials.Delivery

        def refusing(**operands):
            raise ContractRefusal("integrity", "schema",
                                  "a delivery this build cannot construct")

        credentials.Delivery = refusing
        try:
            with self.assertRaises(ContractRefusal):
                self.home().adopt(record, attempt_id="attempt-1",
                                  runtime_id="runtime-1", workspace_group=self.group)
        finally:
            credentials.Delivery = built
        self.assertFalse(live_secret(BEARER))
        self.assertFalse(live_secret(SECOND))

    def test_a_record_whose_volatile_file_is_gone_is_not_adoptable(self):
        delivered = self.delivery()
        record = self.published(delivered)
        os.remove(os.path.join(delivered.root, "api"))
        with self.assertRaises(ContractRefusal):
            self.home().adopt(record, attempt_id="attempt-1",
                              runtime_id="runtime-1", workspace_group=self.group)
        forget_secret(BEARER)

    def test_a_partial_adoption_does_not_leave_an_unowned_live_bearer(self):
        """If a later slot prevents adoption, earlier re-registrations have
        no returned delivery to own or eventually release them."""
        delivered = self.delivery(slots=("api", "signing"))
        record = self.published(delivered)
        forget_secret(BEARER)
        forget_secret(SECOND)
        os.remove(os.path.join(delivered.root, "signing"))

        with self.assertRaises(ContractRefusal):
            self.home().adopt(record, attempt_id="attempt-1",
                              runtime_id="runtime-1", workspace_group=self.group)
        self.assertFalse(live_secret(BEARER))
        self.assertFalse(live_secret(SECOND))


class RecoveryIsDrivenAgainstTheLiveRuntime(CredentialCase):
    """The production restart path, driven end to end.

    Fourth review [P1]: adoption compared a self-authored record with locally
    derived paths and its own files, which proves document consistency; and
    nothing in production called `read_state`, `adopt` or `discard_orphans` at
    all. These cases drive `OciAdapter.recover_credentials`, which is that
    path, and every one of them decides on what the ENGINE says the live
    container has rather than on what the record says it should have.
    """

    def engine(self, listed=True, mounts=None, running=False,
               runtime_id="runtime-1"):
        case = self

        def bind(source, target, writable=False):
            return {"Source": source, "Destination": target, "RW": writable}

        class Engine:
            def __call__(self, argv):
                case.vectors.append(list(argv))
                if "ps" in argv:
                    if not listed:
                        return {"status": 0, "stdout": "", "stderr": ""}
                    row = {"ID": runtime_id, "Image": IDENTITY["image_digest"],
                           "Labels": {f"baton.v12.{name}": str(value)
                                      for name, value in
                                      case.labels().items()}}
                    return {"status": 0, "stdout": json.dumps(row),
                            "stderr": ""}
                if "inspect" in argv:
                    body = {"Id": runtime_id, "State": {"Running": running}}
                    if mounts is not None:
                        body["Mounts"] = [bind(*one) if type(one) is tuple
                                          else one for one in mounts]
                    return {"status": 0, "stdout": json.dumps(body),
                            "stderr": ""}
                return {"status": 0, "stdout": "", "stderr": ""}

        return Engine()

    def labels(self):
        from baton_v12.worker_manager import documents
        return documents.runtime_labels(
            runtime_attempt_id="attempt-1", authority_uuid=UUID, work_id=JOB,
            participant="baton.claude", generation=1,
            principal=CONTEXT["principal"],
            effective_scope=CONTEXT["effective_scope"],
            profile_digest=IDENTITY["profile_digest"],
            policy_digest=IDENTITY["policy_digest"],
            adapter_digest=IDENTITY["adapter_digest"])

    def setUp(self):
        super().setUp()
        self.vectors = []

    def built(self, engine, delivery=None):
        return oci.OciAdapter(
            "docker", engine, identity=dict(IDENTITY),
            assignment_roots={"inputs": self.inputs,
                              "workspace": self.workspace},
            posture="execution", workspace_group=self.group, credential_delivery=delivery)

    def request(self):
        # W16823: the recovery selects by the whole label set, which now
        # names the principal, so the trusted context crosses with the fence.
        return {"attempt_id": "attempt-1", "assignment": dict(ASSIGNMENT),
                "context": dict(CONTEXT)}

    def launched(self, slots=("api",)):
        """One materialized, recorded delivery, as a restart would find it."""
        delivered = self.delivery(slots=slots)
        self.home().written_state(
            "attempt-1", delivered.record(runtime_id="runtime-1"))
        # THE RESTART: this process forgets what it held in memory.
        for value in (BEARER, SECOND)[:len(slots)]:
            forget_secret(value)
        return delivered

    def agreeing(self, delivered):
        return [(os.path.join(delivered.root, one["slot"]), one["target"],
                 False) for one in delivered.slots]

    def test_an_exactly_agreeing_runtime_is_adopted(self):
        delivered = self.launched()
        answer = self.built(
            self.engine(mounts=self.agreeing(delivered))
        ).recover_credentials(self.request())
        self.assertEqual(answer["lifecycle_state"], "adopted")
        self.assertEqual(answer["runtime_id"], "runtime-1")
        self.assertTrue(live_secret(BEARER))
        self.home().tear_down(answer["delivery"])

    def test_the_live_binds_decide_and_not_the_record(self):
        """Every one of these has a record that agrees with itself perfectly.
        What refuses is the CONTAINER, which is the half the previous version
        never asked about."""
        delivered = self.launched()
        source = os.path.join(delivered.root, "api")
        for what, mounts in (
                ("the engine reported no binds at all", None),
                ("the slot is not mounted", []),
                ("mounted from somewhere else",
                 [("/tmp/planted", "/run/baton/credentials/api", False)]),
                ("mounted writable",
                 [(source, "/run/baton/credentials/api", True)]),
                ("an extra entry under the fixed root",
                 [(source, "/run/baton/credentials/api", False),
                  ("/tmp/extra", "/run/baton/credentials/invented", False)])):
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    self.built(self.engine(mounts=mounts)).recover_credentials(
                        self.request())
                self.assertIn("no output is accepted",
                              caught.exception.message.lower())
                self.assertFalse(live_secret(BEARER),
                                 "a refused recovery registers nothing")

    def test_a_bind_shadowing_the_fixed_root_is_not_exact_agreement(self):
        delivered = self.launched()
        source = os.path.join(delivered.root, "api")
        mounts = [(source, "/run/baton/credentials/api", False),
                  ("/tmp/shadow", "/run/baton/credentials", False)]
        with self.assertRaises(ContractRefusal):
            self.built(self.engine(mounts=mounts)).recover_credentials(
                self.request())
        self.assertFalse(live_secret(BEARER))

    def test_two_live_binds_cannot_satisfy_one_recorded_slot(self):
        delivered = self.launched()
        source = os.path.join(delivered.root, "api")
        mounts = [(source, "/run/baton/credentials/api", False),
                  (source, "/run/baton/credentials/api", False)]
        with self.assertRaises(ContractRefusal):
            self.built(self.engine(mounts=mounts)).recover_credentials(
                self.request())
        self.assertFalse(live_secret(BEARER))

    def test_a_record_naming_another_container_is_not_this_one(self):
        """The container identity, which is one of the four the ruling names.
        A record that agrees with itself perfectly still describes a different
        container than the one the engine says is running this attempt."""
        delivered = self.delivery()
        self.home().written_state(
            "attempt-1", delivered.record(runtime_id="runtime-2"))
        forget_secret(BEARER)
        with self.assertRaises(ContractRefusal) as caught:
            self.built(
                self.engine(mounts=self.agreeing(delivered))
            ).recover_credentials(self.request())
        self.assertIn("runtime-2", caught.exception.message)
        self.assertFalse(live_secret(BEARER))

    def test_a_recovery_that_cannot_identify_one_container_fails_closed(self):
        self.launched()
        with self.assertRaises(ContractRefusal):
            self.built(self.engine(listed=False)).recover_credentials(
                self.request())

    def test_a_stale_record_with_no_runtime_converges_to_absence(self):
        """Zero matching runtimes is positive absence, not uncertainty.

        A restart may find a live lifecycle record after the container is
        already gone. With nothing left to stop, that absence proves the
        attempt's root and record stale and permits the same bounded cleanup
        as a proved stop. Leaving both behind makes every later recovery
        repeat the same unresolved answer forever.
        """
        delivered = self.launched()
        built = self.built(self.engine(listed=False))

        with self.assertRaises(ContractRefusal) as caught:
            built.recover_credentials(self.request())
        self.assertNotIn("UNRESOLVED", caught.exception.message)
        self.assertFalse(os.path.exists(delivered.root))
        self.assertIsNone(self.home().read_state("attempt-1"))

        answer = built.recover_credentials(self.request())
        self.assertEqual(answer["lifecycle_state"], "absent")

    def test_a_failed_recovery_stops_the_worker_and_cleans_up(self):
        """The approved disagreement path, driven: no output, stop, bounded
        orphan cleanup -- and the cleanup only removes the root once the stop
        is proved."""
        delivered = self.launched()
        built = self.built(self.engine(mounts=[]))
        with self.assertRaises(ContractRefusal) as caught:
            built.recover_credentials(self.request())
        self.assertTrue(any("stop" in v for v in self.vectors),
                        "the worker was never stopped")
        # The fake engine answers `inspect` with a not-running record rather
        # than positive absence, so the stop is NOT proved and the root stays.
        self.assertIn("UNRESOLVED", caught.exception.message)
        self.assertTrue(os.path.exists(delivered.root))
        self.home().discard_orphans(live=[])

    def test_a_proved_stop_lets_cleanup_discard_the_root(self):
        delivered = self.launched()

        class Engine:
            def __init__(self, inner):
                self.inner = inner

            def __call__(self, argv):
                if "inspect" in argv:
                    return {"status": 1, "stdout": "",
                            "stderr": "Error response from daemon: No such "
                                      "container: runtime-1"}
                return self.inner(argv)

        with self.assertRaises(ContractRefusal) as caught:
            self.built(Engine(self.engine(mounts=[]))).recover_credentials(
                self.request())
        self.assertNotIn("UNRESOLVED", caught.exception.message)
        self.assertFalse(os.path.exists(delivered.root))

    def test_a_proved_failed_recovery_removes_its_stale_record(self):
        """A proved stop plus cleanup must converge. Leaving the lifecycle
        record after deleting its volatile root makes the next recovery see a
        delivery that can neither be adopted nor classified absent.
        """
        delivered = self.launched()

        class Engine:
            def __init__(self, inner):
                self.inner = inner

            def __call__(self, argv):
                if "inspect" in argv:
                    return {"status": 1, "stdout": "",
                            "stderr": "Error response from daemon: No such "
                                      "container: runtime-1"}
                return self.inner(argv)

        with self.assertRaises(ContractRefusal):
            self.built(Engine(self.engine(mounts=[]))).recover_credentials(
                self.request())
        self.assertFalse(os.path.exists(delivered.root))
        self.assertIsNone(self.home().read_state("attempt-1"))

    def test_no_record_is_an_ordinary_answer_that_still_cleans_up(self):
        delivered = self.delivery()
        answer = self.built(self.engine()).recover_credentials(self.request())
        self.assertEqual(answer["lifecycle_state"], "absent")
        self.assertEqual(answer["orphans"]["discarded"], ["attempt-1"])
        self.assertFalse(os.path.exists(delivered.root))

    def test_no_record_for_one_attempt_does_not_discard_another_attempt(self):
        """An orphan pass needs the complete live set. Recovery of attempt-1
        cannot infer that attempt-2 is stale merely because attempt-1 has no
        lifecycle record."""
        other = self.home().materialize(
            credentials.resolved_delivery(["api"], profile=PROFILE),
            attempt_id="attempt-2", credential_provider=self.provider(),
                workspace_group=self.group)
        self.home().written_state(
            "attempt-2", other.record(runtime_id="runtime-2"))

        answer = self.built(self.engine()).recover_credentials(self.request())
        self.assertNotIn("attempt-2", answer["orphans"]["discarded"])
        self.assertTrue(os.path.exists(other.root))
        self.home().tear_down(other)

    def test_a_failed_recovery_does_not_discard_a_sibling_attempt(self):
        """The other half of the orphan rule. A recovery that fails for
        attempt-1 and proves its container gone may remove attempt-1's root
        and nothing else -- a `CredentialHome` is assignment-scoped, and
        attempt-2's root is not evidence about attempt-1."""
        mine = self.launched()
        other = self.home().materialize(
            credentials.resolved_delivery(["api"], profile=PROFILE),
            attempt_id="attempt-2",
            workspace_group=self.group,
            # A FRESH PROVIDER: `self.provider` answers in call order and the
            # first delivery already spent this case's first answer.
            credential_provider=lambda name, reference: SECOND)

        class Engine:
            def __init__(self, inner):
                self.inner = inner

            def __call__(self, argv):
                if "inspect" in argv:
                    return {"status": 1, "stdout": "",
                            "stderr": "Error response from daemon: No such "
                                      "container: runtime-1"}
                return self.inner(argv)

        with self.assertRaises(ContractRefusal):
            self.built(Engine(self.engine(mounts=[]))).recover_credentials(
                self.request())
        self.assertFalse(os.path.exists(mine.root))
        self.assertTrue(os.path.exists(other.root),
                        "a sibling attempt's root is not this recovery's to "
                        "remove")
        self.home().tear_down(other)

    def test_a_multi_slot_recovery_adopts_every_slot(self):
        delivered = self.launched(slots=("api", "signing"))
        answer = self.built(
            self.engine(mounts=self.agreeing(delivered))
        ).recover_credentials(self.request())
        self.assertEqual([one["slot"] for one in answer["delivery"].slots],
                         ["api", "signing"])
        self.assertTrue(live_secret(BEARER))
        self.assertTrue(live_secret(SECOND))
        self.home().tear_down(answer["delivery"])


class OrphanCleanupIsBoundedAndSaysSo(CredentialCase):

    def planted(self, *attempts):
        holding = os.path.join(self.home_place, "credentials")
        for one in attempts:
            place = os.path.join(holding, one)
            os.makedirs(place, mode=0o700, exist_ok=True)
            with open(os.path.join(place, "api"), "wb") as handle:
                handle.write(b"whatever a stopped process left")
        return holding

    def test_a_root_no_live_attempt_owns_is_discarded(self):
        holding = self.planted("attempt-1", "attempt-2", "attempt-3")
        answer = self.home().discard_orphans(live=["attempt-2"])
        self.assertEqual(answer["discarded"], ["attempt-1", "attempt-3"])
        self.assertEqual(sorted(os.listdir(holding)), ["attempt-2"])
        self.assertFalse(answer["bounded"])

    def test_cleanup_stops_at_its_bound_and_reports_the_remainder(self):
        """A pass that stopped at its limit and answered like one that finished
        would be cleanup uncertainty reported as success."""
        self.planted(*[f"attempt-{index:03d}"
                       for index in range(credentials.MAX_ORPHANS + 5)])
        answer = self.home().discard_orphans(live=[])
        self.assertTrue(answer["bounded"])
        self.assertEqual(len(answer["discarded"]), credentials.MAX_ORPHANS)
        self.assertEqual(answer["remaining"], 5)

    def test_cleanup_never_reads_what_it_removes(self):
        """A root belonging to an attempt this process knows nothing about is
        removed without its bytes ever entering this process."""
        import builtins
        self.planted("attempt-9")
        opened = builtins.open

        def watched(*args, **overrides):
            raise AssertionError("orphan cleanup read a credential file")

        builtins.open = watched
        try:
            self.home().discard_orphans(live=[])
        finally:
            builtins.open = opened
        self.assertEqual(
            os.listdir(os.path.join(self.home_place, "credentials")), [])

    def test_nothing_to_clean_is_an_ordinary_answer(self):
        self.assertEqual(self.home().discard_orphans(live=[]),
                         {"discarded": [], "remaining": 0, "bounded": False})


class TheRegistrySpansTheOutputLeakChecks(CredentialCase):

    def envelope(self, place):
        """The worker's `/output/output.json`, so the freeze gets that far.

        W6634 sixth review [P1]: the manager validates the worker's envelope
        BEFORE it freezes, so a case aiming at the staging leak check has to
        publish one or it never reaches the rule it is about -- which is the
        vacuous-probe shape rather than a passing test.
        """
        import hashlib
        from baton_v12.contracts import digest as contract_digest
        entries = []
        for name in sorted(os.listdir(place)):
            with open(os.path.join(place, name), "rb") as reading:
                content = reading.read()
            entries.append({"path": name, "bytes": len(content),
                            "content_digest": "sha256:" + hashlib.sha256(
                                content).hexdigest()})
        body = {"version": {"major": 1, "minor": 0},
                "manifest_id": "completion-1",
                "created_at": "2026-08-26T00:00:00.000Z", "extensions": {},
                "schema": "baton.worker-manifest/completion",
                "assignment_ref": dict(ASSIGNMENT), "disposition": "completed",
                "outputs": [{
                    "name": "proposal", "type": "directory-result",
                    "path": "out", "status": "present",
                    "content_manifest": {
                        "entries": entries, "entry_count": len(entries),
                        "total_bytes": sum(one["bytes"] for one in entries),
                        "tree_digest": contract_digest(entries)},
                    "result_metadata": {}}]}
        body["manifest_digest"] = contract_digest(body)
        with open(os.path.join(self.workspace, "output.json"), "wb") as handle:
            handle.write(json.dumps(body, sort_keys=True).encode("utf-8"))
        return body

    def test_a_worker_that_writes_its_credential_into_the_output_refuses(self):
        """The bearer in the ARTIFACT, which is where no walk of a manager
        document has ever looked. Staging is the one moment the content is in
        hand, and it is the copy that makes the bytes this manager's."""
        delivered = self.delivery()
        place = os.path.join(self.workspace, "out")
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "leaked.txt"), "wb") as handle:
            handle.write(f"the token is {BEARER}\n".encode("utf-8"))
        self.envelope(place)

        declared = sealing.declared_outputs([
            {"name": "proposal", "type": "directory-result", "path": "out",
             "required": True,
             "constraints": {"max_bytes": 1 << 20, "max_entries": 100,
                             "allowed_media_types": ["text/plain"],
                             "link_policy": "forbid",
                             "validator_digest": None}}])
        with self.assertRaises(ContractRefusal) as caught:
            sealing.sealed_result(
                {"attempt_id": "attempt-1", "assignment": dict(ASSIGNMENT),
                 "disposition": "completed",
                 "now": "2026-08-26T00:00:00.000Z",
                 "operation": {"operation_id": "output.freeze:1",
                               "signature_digest": DIGEST}},
                roots={"inputs": self.inputs, "workspace": self.workspace},
                declared=declared, identity=dict(IDENTITY),
                custody=os.path.join(self.home_place, "custody", "attempt-1"),
                input_manifest_digest=DIGEST)
        self.assertEqual(caught.exception.code, "secret-leak")
        self.home().tear_down(delivered)

    def test_the_same_output_seals_once_the_bearer_is_gone(self):
        """The other half, without which the case above proves only that
        sealing refuses something."""
        place = os.path.join(self.workspace, "out")
        os.makedirs(place, exist_ok=True)
        with open(os.path.join(place, "leaked.txt"), "wb") as handle:
            handle.write(f"the token is {BEARER}\n".encode("utf-8"))
        self.envelope(place)
        declared = sealing.declared_outputs([
            {"name": "proposal", "type": "directory-result", "path": "out",
             "required": True,
             "constraints": {"max_bytes": 1 << 20, "max_entries": 100,
                             "allowed_media_types": ["text/plain"],
                             "link_policy": "forbid",
                             "validator_digest": None}}])
        sealed = sealing.sealed_result(
            {"attempt_id": "attempt-1", "assignment": dict(ASSIGNMENT),
             "disposition": "completed", "now": "2026-08-26T00:00:00.000Z",
             "operation": {"operation_id": "output.freeze:1",
                           "signature_digest": DIGEST}},
            roots={"inputs": self.inputs, "workspace": self.workspace},
            declared=declared, identity=dict(IDENTITY),
            custody=os.path.join(self.home_place, "custody", "attempt-1"),
            input_manifest_digest=DIGEST)
        self.assertEqual(sealed["outputs"][0]["status"], "present")


if __name__ == "__main__":
    unittest.main()


class TheOrphanEndingStandsInForADeliveryNobodyHolds(CredentialCase):
    """W55758: the ending for a credential whose OWNER PROCESS died.

    `work/records/2026/08/finding-interrupted-dogfood-attempt-strands-runtime-
    credential/`.

    THE DEFECT, MEASURED. An interrupted supervised attempt left its runtime,
    its bounded credential root and its lifecycle record on the host while the
    in-memory `Delivery` died with the process. A recovery then reconstructed
    the adapter with `credential_delivery is None`, and the ending answered
    `not-delivered` -- a positive claim that no credential was ever delivered,
    about an attempt that left a readable bearer on disk for hours.
    """

    def delivered(self, home=None, attempt="attempt-1"):
        """One real materialized delivery, then FORGET the object.

        Which is the whole shape under test: the files and the record survive
        the process, and the thing that owned them does not.
        """
        place = home or self.home()
        delivery = place.materialize(
            credentials.resolved_delivery(
                ["api"], profile={"api": {"provider": "vault",
                                          "reference": "kv/one"}}),
            attempt_id=attempt, workspace_group=self.group,
            credential_provider=self.provider())
        place.written_state(attempt, delivery.record(runtime_id="runtime-1"))
        for value in delivery.bearers().values():
            forget_secret(value)
        return place

    def test_the_evidence_reports_presence_and_opens_nothing(self):
        home = self.delivered()
        found = home.orphan_evidence("attempt-1")
        self.assertEqual(found["home"], self.home_place)
        self.assertTrue(found["volatile_root"])
        self.assertTrue(found["lifecycle_record"])
        # AND THE BEARER IS NOWHERE IN THE ANSWER, which is the point of
        # answering presence rather than contents.
        self.assertNotIn(BEARER, json.dumps(found))

    def test_an_attempt_with_nothing_here_says_so(self):
        found = self.home().orphan_evidence("attempt-9")
        self.assertFalse(found["volatile_root"])
        self.assertFalse(found["lifecycle_record"])

    def test_the_teardown_removes_the_root_and_the_record_and_proves_it(self):
        home = self.delivered()
        answered = home.tear_down_orphan("attempt-1")
        self.assertTrue(answered["held_root"])
        self.assertTrue(answered["held_record"])
        self.assertFalse(os.path.lexists(home.volatile_root("attempt-1")))
        self.assertFalse(os.path.exists(home.state_path("attempt-1")))
        self.assertNotIn(BEARER, json.dumps(answered))

    def test_it_reads_no_byte_of_the_slot_it_removes(self):
        """The canary: a slot this manager cannot READ is still torn down.

        Unreadable to the owner as well, so a teardown that opened the file
        would raise rather than quietly succeed -- which is what makes this
        an assertion about reading and not about permissions.
        """
        home = self.delivered()
        slot = os.path.join(home.volatile_root("attempt-1"), "api")
        os.chmod(slot, 0o000)
        home.tear_down_orphan("attempt-1")
        self.assertFalse(os.path.lexists(slot))

    def test_an_already_absent_attempt_is_torn_down_rather_than_refused(self):
        """`torn-down` MEANS PROVED ABSENT.

        A separately invoked emergency `discard_orphan` had already removed
        run7's and run8's bearers, and the ending still has to be reachable
        afterwards -- an ending that cannot be reached twice is not an ending.
        """
        home = self.home()
        answered = home.tear_down_orphan("attempt-never")
        self.assertFalse(answered["held_root"])
        self.assertFalse(answered["held_record"])

    def test_it_touches_exactly_one_attempt(self):
        """A `CredentialHome` is ASSIGNMENT-scoped and holds siblings.

        "This attempt is over" is not evidence about any other one, and a pass
        that removed what it had not proved stale would be a second failure
        caused by the first.
        """
        home = self.delivered()
        self.delivered(home=home, attempt="attempt-2")
        home.tear_down_orphan("attempt-1")
        self.assertTrue(os.path.isdir(home.volatile_root("attempt-2")))
        self.assertTrue(os.path.exists(home.state_path("attempt-2")))

    # -- the typed capability -------------------------------------------------

    def test_the_capability_refuses_anything_that_is_not_a_home(self):
        with self.assertRaises(ContractRefusal):
            credentials.OrphanTeardown("attempt-1",
                                       homes=[self.home_place])
        with self.assertRaises(ContractRefusal):
            credentials.OrphanTeardown("attempt-1", homes=[])
        with self.assertRaises(ContractRefusal):
            credentials.OrphanTeardown("attempt-1", homes="not a list")

    def test_two_names_for_one_home_are_one_home(self):
        """The ordinary case from now on: the granted home and the
        assignment-derived one agree, and one ending is one ending."""
        orphan = credentials.OrphanTeardown(
            "attempt-1", homes=[self.home(), self.home()])
        self.assertEqual(len(orphan.homes), 1)

    def test_it_ends_the_split_the_deployment_really_left(self):
        """Run7's shape: the root under one home, the record under another.

        The legacy split is handled by HOLDING both proved homes, never by
        following the `credential_root` member of a record -- a raw path out
        of a document is not authority for touching a filesystem.
        """
        second_place = os.path.join(self.home_place, "assignment")
        os.makedirs(second_place, exist_ok=True)
        second = credentials.CredentialHome(second_place)
        granted = self.delivered()
        # The record moves to the OTHER home, exactly as the deployment's own
        # split put it there.
        second.written_state("attempt-1",
                             granted.read_state("attempt-1"))
        os.remove(granted.state_path("attempt-1"))
        orphan = credentials.OrphanTeardown("attempt-1",
                                            homes=[granted, second])
        answered = orphan.tear_down()
        # THE CROSSING'S SHAPE, which is closed: `intake._provider_ending`
        # refuses a member it does not name, so the per-home account lives on
        # the capability rather than in the ending the manager reads.
        self.assertEqual(sorted(answered),
                         ["attempt_id", "lifecycle_state"])
        self.assertEqual(answered["lifecycle_state"], "torn-down")
        self.assertEqual(len(orphan.ending["homes"]), 2)
        self.assertFalse(os.path.lexists(granted.volatile_root("attempt-1")))
        self.assertFalse(os.path.exists(second.state_path("attempt-1")))
        self.assertNotIn(BEARER, json.dumps(answered))
        # AND THE CAPABILITY KEPT ITS OWN ACCOUNT, so a deployment can record
        # what it did without repeating the act.
        self.assertEqual(orphan.ending["lifecycle_state"], "torn-down")

    def test_the_evidence_after_the_ending_is_empty(self):
        granted = self.delivered()
        orphan = credentials.OrphanTeardown("attempt-1", homes=[granted])
        orphan.tear_down()
        for found in orphan.evidence():
            self.assertFalse(found["volatile_root"])
            self.assertFalse(found["lifecycle_record"])
