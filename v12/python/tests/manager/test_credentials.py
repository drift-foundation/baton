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
from baton_v12.worker_manager import credentials, oci, sealing

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
            posture="execution", credential_delivery=delivery)


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
            self.assertEqual(stat.S_IMODE(os.stat(place).st_mode),
                             credentials.VOLATILE_FILE)
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
                credential_provider=self.provider(
                    "x" * (credentials.MAX_BEARER + 1)))
        self.assertFalse(
            os.path.exists(self.home().volatile_root("attempt-1")))

    def test_a_provider_that_is_not_a_capability_refuses_before_anything(self):
        with self.assertRaises(ContractRefusal):
            self.home().materialize(
                credentials.resolved_delivery(["api"], profile=PROFILE),
                attempt_id="attempt-1",
                credential_provider="vault")
        self.assertFalse(
            os.path.exists(self.home().volatile_root("attempt-1")))


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
                "posture": "execution", "name": "baton-v12-1"}
        body.update(overrides)
        return oci.run_vector("docker", **body)

    def labels(self, **overrides):
        from baton_v12.worker_manager import documents
        body = {"runtime_attempt_id": "attempt-1", "authority_uuid": UUID,
                "work_id": JOB, "participant": "baton.claude", "generation": 1,
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
        vector is walked while the registry is live."""
        delivered = self.delivery()
        argv = self.vector(credentials_delivered=delivered.mounts())
        self.assertTrue(live_secret(BEARER))
        for piece in argv:
            self.assertNotIn(BEARER, piece)
        # And the walk is REACHABLE: a label carrying the live value refuses
        # rather than being spelled into the command line.
        with self.assertRaises(ContractRefusal) as caught:
            self.vector(labels=self.labels(participant=BEARER),
                        credentials_delivered=delivered.mounts())
        self.assertEqual(caught.exception.code, "secret-leak")
        self.home().tear_down(delivered)


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
            posture="execution", credential_delivery=delivered)
        labels = documents.runtime_labels(
            runtime_attempt_id="attempt-1", authority_uuid=UUID,
            work_id=JOB, participant="baton.claude", generation=1,
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
            posture="execution", credential_delivery=delivered)
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
            posture="execution", credential_delivery=delivered)
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
            posture="execution", credential_delivery=delivered)
        labels = dict(self.runtime_labels(), runtime_attempt_id="attempt-2")
        with self.assertRaises(ContractRefusal):
            built.start({"labels": labels,
                         "operation_id": "runtime.start:2"})
        self.assertTrue(live_secret(BEARER))

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
            posture="execution",
            mounts=({"source": self.workspace,
                     "target": "/run/baton/credentials",
                     "writable": False},),
            credential_delivery=delivered)
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
            posture="execution", credential_delivery=delivered)
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
                                    runtime_id="runtime-1")
        self.assertEqual(adopted.state, "adopted")
        self.assertTrue(live_secret(BEARER))
        self.assertEqual([target for _source, target in adopted.mounts()],
                         ["/run/baton/credentials/api"])
        self.home().tear_down(adopted)

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
                                      runtime_id="runtime-1")
        with self.subTest(member="target"):
            moved = dict(record, slots=[dict(record["slots"][0],
                                             target="/etc/api")])
            with self.assertRaises(ContractRefusal):
                self.home().adopt(moved,
                                  attempt_id="attempt-1",
                                  runtime_id="runtime-1")
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
                              runtime_id="runtime-1")

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
                                  runtime_id="runtime-1")
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
                              runtime_id="runtime-1")
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
                              runtime_id="runtime-1")
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
            posture="execution", credential_delivery=delivery)

    def request(self):
        return {"attempt_id": "attempt-1", "assignment": dict(ASSIGNMENT)}

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
            attempt_id="attempt-2", credential_provider=self.provider())
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
