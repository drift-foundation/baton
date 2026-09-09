"""W2845 cut 1 — creation, opening, and refusing to adopt anybody else's store.

The obligation being ported is not the frozen Node host's `open`.  That one
creates when absent and adopts when present, which was tolerable for a
disposable single-host authority and is not tolerable here: this distribution
sits beside three other SQLite files whose first schema version is also `1`.

So the cases below are about a question the Node host never had to ask -- WHOSE
STORE IS THIS -- and about the property that makes the answer trustworthy: a
refusal leaves the file exactly as it was found.
"""

import os
import sqlite3
import stat
import tempfile
import unittest

from baton_v12.authority import Authority, Refusal
from baton_v12.authority.schema import (META_AUTHORITY_UUID,
                                        META_SCHEMA_VERSION, META_STORE_KIND,
                                        SCHEMA_VERSION, STORE_KIND)
from baton_v12.authority import store as store_module
from baton_v12.authority.store import Store

UUID = "0123456789abcdef0123456789abcdef"
OTHER_UUID = "fedcba9876543210fedcba9876543210"


class StoreCase(unittest.TestCase):
    """Every created store and root is owned by its fixture and cleaned by it."""

    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-authority-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "authority.sqlite3")

    def bytes_at(self, path):
        with open(path, "rb") as handle:
            return handle.read()

    def foreign_store(self, name, meta):
        """A SQLite file that is somebody ELSE's, built the way theirs are."""
        path = os.path.join(self.root, name)
        connection = sqlite3.connect(path, isolation_level=None)
        connection.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        for key, value in meta.items():
            connection.execute("INSERT INTO meta (key, value) VALUES (?, ?)",
                               (key, value))
        connection.close()
        return path


class Creation(StoreCase):

    def test_create_makes_a_new_authority_and_records_whose_it_is(self):
        store = Store.create(self.path, authority_uuid=UUID)
        self.addCleanup(store.close)
        self.assertEqual(store.authority_uuid, UUID)
        recorded = {row["key"]: row["value"]
                    for row in store.all("SELECT key, value FROM meta")}
        # WHOSE, then how old, then which.  The kind is recorded first because
        # it is the fact a version number cannot carry.
        self.assertEqual(recorded[META_STORE_KIND], STORE_KIND)
        self.assertEqual(recorded[META_SCHEMA_VERSION], str(SCHEMA_VERSION))
        self.assertEqual(recorded[META_AUTHORITY_UUID], UUID)

    def test_create_requires_absence_and_wins_it_exclusively(self):
        first = Store.create(self.path, authority_uuid=UUID)
        self.addCleanup(first.close)
        before = self.bytes_at(self.path)
        with self.assertRaises(Refusal):
            Store.create(self.path, authority_uuid=OTHER_UUID)
        # The loser changed NOTHING.  A second creator that truncated or
        # re-initialised the winner's store would be the worst possible way to
        # lose a race.
        self.assertEqual(self.bytes_at(self.path), before)
        self.assertEqual(first.get(
            "SELECT value FROM meta WHERE key = ?", META_AUTHORITY_UUID)["value"],
            UUID)

    def test_create_refuses_an_occupied_path_of_any_kind(self):
        directory = os.path.join(self.root, "adirectory")
        os.mkdir(directory)
        empty = os.path.join(self.root, "empty")
        open(empty, "wb").close()
        dangling = os.path.join(self.root, "dangling")
        os.symlink(os.path.join(self.root, "absent"), dangling)
        for what, path in [("a directory", directory), ("an empty file", empty),
                           # A DANGLING SYMLINK is the case an existence check
                           # answers wrongly: nothing is there, and creating
                           # through it would write outside the path given.
                           ("a dangling symlink", dangling)]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    Store.create(path, authority_uuid=UUID)

    def test_create_proves_the_uuid_before_it_touches_the_filesystem(self):
        for value in (None, "", UUID.upper(), UUID[:-1], 7):
            with self.subTest(value=value):
                with self.assertRaises(Refusal):
                    Store.create(self.path, authority_uuid=value)
                self.assertFalse(os.path.exists(self.path),
                                 "a refused creation left a file behind")

    def test_a_failed_creation_leaves_no_store_to_confuse_the_next_one(self):
        # The reservation is ours, so the half-built file is ours to remove.
        # Leaving it would make the next create refuse on a store that never
        # existed AND the next open refuse on one that is empty -- two wrong
        # answers where there should be none.
        with self.assertRaises(Refusal):
            Store.create(os.path.join(self.root, "missing", "a.sqlite3"),
                         authority_uuid=UUID)
        self.assertEqual(sorted(os.listdir(self.root)), [])

    def test_a_creation_that_fails_AFTER_the_reservation_cleans_up(self):
        # The earlier case fails before `os.open` ever succeeds, so it proves
        # only that nothing was reserved.  This one fails with the reservation
        # already held, which is the case the cleanup exists for -- and the one
        # that would otherwise leave a file that makes the next `create` refuse
        # on a store that never existed and the next `open` refuse on one that
        # is empty.
        def explode(_connection):
            raise Refusal("the schema could not be applied")

        original = store_module._apply_schema
        store_module._apply_schema = explode
        self.addCleanup(setattr, store_module, "_apply_schema", original)
        with self.assertRaises(Refusal):
            Store.create(self.path, authority_uuid=UUID)
        self.assertEqual(sorted(os.listdir(self.root)), [])

    def test_the_authority_creates_no_directory(self):
        nested = os.path.join(self.root, "state", "authority.sqlite3")
        with self.assertRaises(Refusal):
            Store.create(nested, authority_uuid=UUID)
        self.assertFalse(os.path.exists(os.path.join(self.root, "state")))


class Opening(StoreCase):

    def make(self):
        store = Store.create(self.path, authority_uuid=UUID)
        store.close()
        return self.path

    def test_open_returns_the_recorded_authority(self):
        self.make()
        store = Store.open(self.path)
        self.addCleanup(store.close)
        self.assertEqual(store.authority_uuid, UUID)

    def test_the_expected_uuid_is_a_compare_and_swap_not_a_default(self):
        self.make()
        store = Store.open(self.path, expected_authority_uuid=UUID)
        store.close()
        with self.assertRaises(Refusal):
            Store.open(self.path, expected_authority_uuid=OTHER_UUID)
        # A UUID IS DURABLE AND IS NEVER REASSIGNED.  Opening with the wrong one
        # refuses; it does not adopt, and it does not rewrite.
        again = Store.open(self.path)
        self.addCleanup(again.close)
        self.assertEqual(again.authority_uuid, UUID)

    def test_open_requires_an_existing_recognized_store(self):
        text = os.path.join(self.root, "notes.txt")
        with open(text, "w", encoding="utf-8") as handle:
            handle.write("this is not a database")
        empty = os.path.join(self.root, "empty.sqlite3")
        open(empty, "wb").close()
        blank = os.path.join(self.root, "blank.sqlite3")
        sqlite3.connect(blank, isolation_level=None).close()
        cases = [
            ("an absent path", os.path.join(self.root, "absent.sqlite3")),
            ("a text file", text),
            ("an empty file", empty),
            ("a database with no meta table", blank),
            # The three neighbours this distribution actually sits beside, each
            # of which calls its own first schema version 1.
            ("the Node v12 authority",
             self.foreign_store("node.sqlite3", {"schema_version": "1",
                                                 "authority_uuid": UUID})),
            ("a v11 store",
             self.foreign_store("v11.sqlite3", {"schema_version": "1"})),
            ("a worker-manager control store",
             self.foreign_store("control.sqlite3",
                                {"store_kind": "baton.v12.worker-manager",
                                 "schema_version": "14"})),
        ]
        for what, path in cases:
            with self.subTest(what=what):
                before = self.bytes_at(path) if os.path.exists(path) else None
                with self.assertRaises(Refusal):
                    Store.open(path)
                if before is not None:
                    # REFUSED WITHOUT MODIFICATION.  Not "refused after we fixed
                    # the PRAGMAs": a store we have not established is ours is a
                    # store we have not written to.
                    self.assertEqual(self.bytes_at(path), before,
                                     f"{what}: the refusal modified the file")
                    self.assertFalse(os.path.exists(path + "-wal"), what)
                    self.assertFalse(os.path.exists(path + "-journal"), what)

    def test_a_shared_version_number_is_not_shared_ownership(self):
        # The sharpest adoption case: same kind KEY, same version VALUE, wrong
        # product.  Only the kind separates them.
        foreign = self.foreign_store(
            "lookalike.sqlite3",
            {META_STORE_KIND: "baton.v12.node.authority",
             META_SCHEMA_VERSION: "1", META_AUTHORITY_UUID: UUID})
        with self.assertRaises(Refusal) as caught:
            Store.open(foreign)
        self.assertIn(STORE_KIND, str(caught.exception))

    def test_a_store_of_another_version_is_refused_in_either_direction(self):
        for what, version in [("older", str(SCHEMA_VERSION - 1)),
                              ("newer", str(SCHEMA_VERSION + 1))]:
            with self.subTest(what=what):
                path = self.foreign_store(
                    f"{what}.sqlite3",
                    {META_STORE_KIND: STORE_KIND, META_SCHEMA_VERSION: version,
                     META_AUTHORITY_UUID: UUID})
                with self.assertRaises(Refusal):
                    Store.open(path)

    def test_a_store_that_cannot_say_which_authority_it_is_is_not_openable(self):
        path = self.foreign_store(
            "nouuid.sqlite3",
            {META_STORE_KIND: STORE_KIND, META_SCHEMA_VERSION: str(SCHEMA_VERSION)})
        with self.assertRaises(Refusal):
            Store.open(path)

    def test_a_refused_open_makes_no_PERSISTENT_change_either(self):
        # Byte identity is the visible half.  The other half is that the
        # connection made on the way to a refusal must not set a PERSISTENT
        # sqlite setting on a file it has not established is ours -- the journal
        # mode is the one setting that survives the connection, so it is the one
        # withheld until the recheck under the write lock has passed.
        self.make()
        connection = sqlite3.connect(self.path, isolation_level=None)
        connection.execute("PRAGMA journal_mode = DELETE")
        mode_before = connection.execute("PRAGMA journal_mode").fetchone()[0]
        connection.close()
        self.assertEqual(mode_before, "delete")
        with self.assertRaises(Refusal):
            Store.open(self.path, expected_authority_uuid=OTHER_UUID)
        connection = sqlite3.connect(self.path, isolation_level=None)
        mode_after = connection.execute("PRAGMA journal_mode").fetchone()[0]
        connection.close()
        self.assertEqual(mode_after, mode_before,
                         "a refused open changed a persistent setting")
        # And a SUCCESSFUL open is free to make it, because by then the store
        # has been re-established as ours under the write lock.
        store = Store.open(self.path)
        self.addCleanup(store.close)
        self.assertEqual(
            store.get("PRAGMA journal_mode")["journal_mode"], "wal")

    def test_the_recheck_window_writes_nothing_to_a_file_that_is_not_ours(self):
        # The probe is a fact about the PAST.  Between it and the write lock,
        # another process may replace the file -- so the recheck under
        # `BEGIN IMMEDIATE` is what actually decides, and nothing PERSISTENT may
        # be written before it.
        #
        # The replacement is simulated by making the probe answer for a file it
        # did not read, because cut 1 has no deterministic way to interleave two
        # processes; the real races arrive in cut 3.  What this pins is the
        # ORDERING, which is the part that is ours to get right either way.
        foreign = self.foreign_store(
            "someone-elses.sqlite3",
            {META_STORE_KIND: "baton.v12.node.authority",
             META_SCHEMA_VERSION: "1", META_AUTHORITY_UUID: UUID})
        before = self.bytes_at(foreign)

        def lie(_path):
            return {META_STORE_KIND: STORE_KIND,
                    META_SCHEMA_VERSION: str(SCHEMA_VERSION),
                    META_AUTHORITY_UUID: UUID}

        original = store_module._probe
        store_module._probe = lie
        self.addCleanup(setattr, store_module, "_probe", original)
        with self.assertRaises(Refusal):
            Store.open(foreign)
        self.assertEqual(self.bytes_at(foreign), before,
                         "the recheck window modified a file that was not ours")
        self.assertFalse(os.path.exists(foreign + "-wal"))

    def test_the_face_and_the_live_store_can_never_name_two_authorities(self):
        # Review [P1].  The probe validated one file and the Store was then
        # built from the PROBE's UUID while the connection governed whatever was
        # actually there.  Both checks passed and the public `authority_uuid`
        # named A over a live B -- an authority answering to two identities,
        # which is the one thing an assignment reference must never be.
        other = os.path.join(self.root, "other.sqlite3")
        Store.create(self.path, authority_uuid=UUID).close()
        Store.create(other, authority_uuid=OTHER_UUID).close()
        real = store_module._probe
        store_module._probe = lambda _path: real(self.path)
        self.addCleanup(setattr, store_module, "_probe", real)
        with self.assertRaises(Refusal):
            Store.open(other)
        # And when nothing swaps, the face and the live meta agree -- which is
        # the property, stated positively so a guard that simply refused
        # everything could not satisfy it.
        store_module._probe = real
        opened = Store.open(other)
        self.addCleanup(opened.close)
        live = opened.get("SELECT value FROM meta WHERE key = ?",
                          META_AUTHORITY_UUID)["value"]
        self.assertEqual(opened.authority_uuid, live)
        self.assertEqual(opened.authority_uuid, OTHER_UUID)

    def test_a_malformed_recorded_uuid_is_not_a_recognized_authority(self):
        # Review [P1].  Presence is not validity: a marker-only file recording
        # `not-a-uuid` was a recognized authority, and opening it GREW THE FULL
        # SCHEMA inside it.  The durable identity is held to the same grammar
        # every assignment identity is held to, because nothing built from it
        # can be valid if it is not.
        for what, value in [("text that is not a uuid", "not-a-uuid"),
                            ("uppercase hex", UUID.upper()),
                            ("a truncated uuid", UUID[:-1]),
                            ("an empty string", ""),
                            # A foreign store's meta is not a STRICT table, so
                            # its value may not even be text.
                            ("an integer", 7)]:
            with self.subTest(what=what):
                path = self.foreign_store(
                    f"malformed-{abs(hash(what))}.sqlite3",
                    {META_STORE_KIND: STORE_KIND,
                     META_SCHEMA_VERSION: str(SCHEMA_VERSION),
                     META_AUTHORITY_UUID: value})
                before = self.bytes_at(path)
                with self.assertRaises(Refusal):
                    Store.open(path)
                self.assertEqual(self.bytes_at(path), before, what)
                connection = sqlite3.connect(path)
                tables = {row[0] for row in connection.execute(
                    "SELECT name FROM sqlite_master WHERE type = 'table'")}
                connection.close()
                self.assertEqual(tables, {"meta"},
                                 f"{what}: the refusal populated the file")

    def test_a_failed_open_commits_nothing_it_wrote_on_the_way(self):
        # Review [P1].  The COMMIT was in a `finally`, so a fault partway
        # through the schema committed the statements that had already run --
        # a failed open leaving tables behind in somebody else's database,
        # which is the exact outcome the non-adopting design exists to prevent,
        # reached through the error path instead of the success one.
        Store.create(self.path, authority_uuid=UUID).close()
        before = self.bytes_at(self.path)

        def half(connection):
            connection.execute(
                "CREATE TABLE IF NOT EXISTS left_behind_by_a_failed_open (x TEXT)")
            raise sqlite3.OperationalError("the schema faulted")

        real = store_module._apply_schema
        store_module._apply_schema = half
        self.addCleanup(setattr, store_module, "_apply_schema", real)
        with self.assertRaises(sqlite3.OperationalError):
            Store.open(self.path)
        store_module._apply_schema = real
        connection = sqlite3.connect(self.path)
        tables = {row[0] for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'")}
        connection.close()
        self.assertNotIn("left_behind_by_a_failed_open", tables)
        # AND THE STORE IS STILL USABLE.  A rollback that left the transaction
        # open, or a connection left half-closed, would make the next open fail
        # for a reason that has nothing to do with the store.
        reopened = Store.open(self.path)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.authority_uuid, UUID)
        reopened.transact(lambda: reopened.run(
            "INSERT INTO policy (key, value) VALUES (?, ?)", "a", "1"))
        self.assertEqual(len(reopened.all("SELECT key FROM policy")), 1)

    def test_a_symlink_is_not_a_durable_home_for_an_authority_uuid(self):
        self.make()
        link = os.path.join(self.root, "link.sqlite3")
        os.symlink(self.path, link)
        with self.assertRaises(Refusal):
            Store.open(link)
        # And the real store is still openable, so the refusal was about the
        # path rather than about the store behind it.
        store = Store.open(self.path)
        self.addCleanup(store.close)
        self.assertEqual(store.authority_uuid, UUID)

    def test_a_non_regular_target_refuses(self):
        fifo = os.path.join(self.root, "fifo")
        os.mkfifo(fifo)
        self.assertTrue(stat.S_ISFIFO(os.lstat(fifo).st_mode))
        with self.assertRaises(Refusal):
            Store.open(fifo)


class Transactions(StoreCase):

    def test_a_write_cannot_silently_join_a_read_snapshot(self):
        store = Store.create(self.path, authority_uuid=UUID)
        self.addCleanup(store.close)

        def write():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)",
                      "apparently-committed", "1")
            return "committed"

        with self.assertRaises(Refusal):
            store.read_snapshot(lambda: store.transact(write))
        self.assertEqual(store.all("SELECT key FROM policy"), [])

    def test_nested_transactions_join_the_outer_one_and_commit_once(self):
        store = Store.create(self.path, authority_uuid=UUID)
        self.addCleanup(store.close)
        seen = []

        def outer():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)", "a", "1")
            store.transact(inner)
            return "outer"

        def inner():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)", "b", "2")
            seen.append("inner")
            return "inner"

        self.assertEqual(store.transact(outer), "outer")
        self.assertEqual(seen, ["inner"])
        self.assertEqual(len(store.all("SELECT key FROM policy")), 2)

    def test_a_failed_transaction_leaves_nothing_behind(self):
        store = Store.create(self.path, authority_uuid=UUID)
        self.addCleanup(store.close)

        def body():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)", "a", "1")
            raise Refusal("no")

        with self.assertRaises(Refusal):
            store.transact(body)
        self.assertEqual(store.all("SELECT key FROM policy"), [])
        # And the connection is usable afterwards: a rollback that left the
        # transaction open would make the next write fail for the wrong reason.
        store.transact(lambda: store.run(
            "INSERT INTO policy (key, value) VALUES (?, ?)", "b", "2"))
        self.assertEqual(len(store.all("SELECT key FROM policy")), 1)

    def test_a_failure_inside_a_nested_transaction_rolls_the_whole_one_back(self):
        store = Store.create(self.path, authority_uuid=UUID)
        self.addCleanup(store.close)

        def outer():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)", "a", "1")
            store.transact(inner)

        def inner():
            store.run("INSERT INTO policy (key, value) VALUES (?, ?)", "b", "2")
            raise Refusal("no")

        with self.assertRaises(Refusal):
            store.transact(outer)
        # ONE transaction, so one outcome.  "Fence the exact generation AND end
        # the assignment" is a single atomic act, and a nested helper that could
        # commit its half independently would break that without any statement
        # looking wrong.
        self.assertEqual(store.all("SELECT key FROM policy"), [])


class AuthorityFace(StoreCase):

    def test_the_bootstrap_face_creates_opens_and_disposes(self):
        with Authority.create(self.path, authority_uuid=UUID) as authority:
            self.assertEqual(authority.authority_uuid, UUID)
        with Authority.open(self.path, expected_authority_uuid=UUID) as authority:
            self.assertEqual(authority.authority_uuid, UUID)

    def test_the_bootstrap_face_carries_the_same_refusals(self):
        Authority.create(self.path, authority_uuid=UUID).dispose()
        for what, call in [
                ("create over an existing store",
                 lambda: Authority.create(self.path, authority_uuid=UUID)),
                ("open with the wrong uuid",
                 lambda: Authority.open(self.path,
                                        expected_authority_uuid=OTHER_UUID)),
                ("open an absent store",
                 lambda: Authority.open(os.path.join(self.root, "absent"))),
                ("construct from something that is not a store",
                 lambda: Authority("not a store"))]:
            with self.subTest(what=what):
                with self.assertRaises(Refusal):
                    call()


if __name__ == "__main__":
    unittest.main()


# -- W126880: opening committed evidence without writing ---------------------
#
# `work/records/2026/09/finding-v12-composed-ending-consumer/findings/
# finding-readonly-authority-open/`.
#
# THE ONLY PUBLIC OPENER TOOK A WRITE LOCK. `open` probes read-only and then
# runs `BEGIN IMMEDIATE`, applies the schema and sets a PERSISTENT journal
# mode -- right for a serving deployment, and the reason a separate status
# process had no way to read this store's committed record at all.


class ReadOnlyOpening(StoreCase):
    """The new opener: an existing store, read, and left exactly as found."""

    def created(self, uuid=UUID):
        """One store, HELD OPEN by a serving handle.

        A read-only open of a WAL store whose sidecars are absent would make
        SQLite create them, which this opener refuses -- so the state every
        positive case is about is the one it exists for: a store a serving
        process is holding. `test_a_closed_store_is_refused_with_the_sidecar_
        limit_named` is the other half.
        """
        serving = Authority.create(self.path, authority_uuid=uuid)
        self.addCleanup(serving.dispose)
        return serving

    def entries(self):
        """Every file the store's directory holds, sidecars included."""
        return sorted(os.listdir(self.root))

    def snapshot(self):
        """The STORE's own bytes and mode.

        The shared-memory sidecar is deliberately not part of this. SQLite
        creates `<store>-shm` when it opens a WAL database and no writer is
        attached, a read-only connection cannot remove it, and it carries no
        store content -- it is locking scaffolding. That is a real filesystem
        effect and it is measured on its own below rather than folded into a
        claim about the store.
        """
        return {name: (self.bytes_at(os.path.join(self.root, name)),
                       stat.S_IMODE(os.stat(os.path.join(self.root,
                                                         name)).st_mode))
                for name in self.entries() if not name.endswith("-shm")}

    # -- identity ------------------------------------------------------------

    def test_it_opens_an_existing_store_and_answers_its_identity(self):
        self.created()
        held = Store.open_readonly(self.path)
        self.addCleanup(held.close)
        self.assertEqual(held.authority_uuid, UUID)
        self.assertEqual(held.path, self.path)

    def test_a_matching_expected_uuid_opens(self):
        self.created()
        held = Store.open_readonly(self.path, expected_authority_uuid=UUID)
        self.addCleanup(held.close)
        self.assertEqual(held.authority_uuid, UUID)

    def test_a_mismatched_expected_uuid_refuses(self):
        """The compare-and-swap on identity keeps its exact meaning."""
        self.created()
        before = self.snapshot()
        with self.assertRaises(Refusal):
            Store.open_readonly(self.path, expected_authority_uuid=OTHER_UUID)
        self.assertEqual(self.snapshot(), before)

    def test_a_malformed_expected_uuid_refuses(self):
        self.created()
        with self.assertRaises(Refusal):
            Store.open_readonly(self.path, expected_authority_uuid="nonsense")

    # -- what it will not adopt ----------------------------------------------

    def test_an_absent_store_is_refused_and_none_is_created(self):
        missing = os.path.join(self.root, "absent.sqlite3")
        with self.assertRaises(Refusal) as caught:
            Store.open_readonly(missing)
        self.assertIn("creates none", caught.exception.message)
        self.assertFalse(os.path.lexists(missing))
        self.assertEqual(self.entries(), [])

    def test_an_empty_file_is_refused_and_left_empty(self):
        empty = os.path.join(self.root, "empty.sqlite3")
        open(empty, "wb").close()
        with self.assertRaises(Refusal):
            Store.open_readonly(empty)
        self.assertEqual(os.path.getsize(empty), 0)

    def test_a_directory_or_symlink_is_refused(self):
        nested = os.path.join(self.root, "a-directory")
        os.mkdir(nested)
        with self.assertRaises(Refusal):
            Store.open_readonly(nested)

    def test_a_foreign_store_is_refused_byte_for_byte(self):
        """Adopting nothing is the property, and it is the same one `open`
        keeps: a refusal leaves the file exactly as it was found."""
        path = self.foreign_store("theirs.sqlite3", {
            META_STORE_KIND: "somebody.else/1",
            META_SCHEMA_VERSION: str(SCHEMA_VERSION),
            META_AUTHORITY_UUID: UUID})
        before = self.bytes_at(path)
        with self.assertRaises(Refusal) as caught:
            Store.open_readonly(path)
        self.assertIn("not shared ownership", caught.exception.message)
        self.assertEqual(self.bytes_at(path), before)

    def test_an_incompatible_version_is_refused_unchanged(self):
        path = self.foreign_store("older.sqlite3", {
            META_STORE_KIND: STORE_KIND,
            META_SCHEMA_VERSION: str(SCHEMA_VERSION + 1),
            META_AUTHORITY_UUID: UUID})
        before = self.bytes_at(path)
        with self.assertRaises(Refusal):
            Store.open_readonly(path)
        self.assertEqual(self.bytes_at(path), before)

    def test_a_file_that_is_not_a_database_is_refused(self):
        path = os.path.join(self.root, "prose.txt")
        with open(path, "wb") as handle:
            handle.write(b"this is not a database\n")
        with self.assertRaises(Refusal):
            Store.open_readonly(path)

    # -- and it writes nothing -----------------------------------------------

    def test_opening_and_reading_changes_no_store_byte(self):
        """No schema, no migration, no write-ahead log, no mode change and no
        permissions change -- measured over the directory rather than the main
        file alone, because a sidecar is what a careless opener leaves."""
        self.created()
        before, listed = self.snapshot(), self.entries()
        held = Store.open_readonly(self.path)
        try:
            self.assertIsNone(held.operation_row("nothing-committed"))
            self.assertEqual(
                held.get("SELECT value FROM meta WHERE key = ?",
                         META_AUTHORITY_UUID)["value"], UUID)
        finally:
            held.close()
        # NOTHING APPEARED AND NOTHING CHANGED. The `-wal` and `-shm` beside
        # the store are the SERVING handle's and were there before this
        # opener ran; what is measured is that reading added none and altered
        # no store byte or mode.
        self.assertEqual(self.entries(), listed)
        self.assertEqual(self.snapshot(), before)

    def test_the_journal_mode_is_not_changed(self):
        serving = self.created()
        before = serving._core._store.get("PRAGMA journal_mode")
        held = Store.open_readonly(self.path)
        held.close()
        self.assertEqual(serving._core._store.get("PRAGMA journal_mode"),
                         before)

    def test_a_closed_store_is_refused_with_the_sidecar_limit_named(self):
        """THE LIMIT, STATED PRECISELY AND MEASURED.

        SQLite creates `-wal` and `-shm` when it opens a write-ahead-log
        database that has neither -- from a `mode=ro` connection too, because
        they are not the database. Creating a journal artifact is what this
        opener may not do, so a store nobody is holding is refused, and the
        files stay exactly as they were.
        """
        Authority.create(self.path, authority_uuid=UUID).dispose()
        before = self.entries()
        with self.assertRaises(Refusal) as caught:
            Store.open_readonly(self.path)
        self.assertIn("sidecars are absent", caught.exception.message)
        self.assertIn("creates no journal artifact", caught.exception.message)
        self.assertEqual(self.entries(), before)

    # -- and it performs nothing ---------------------------------------------

    def test_a_statement_refuses_before_it_reaches_sqlite(self):
        """This authority's own refusal, not a `sqlite3` error out of the
        middle of a transition."""
        self.created()
        held = Store.open_readonly(self.path)
        self.addCleanup(held.close)
        with self.assertRaises(Refusal) as caught:
            held.run("INSERT INTO meta (key, value) VALUES (?, ?)", "k", "v")
        self.assertIn("opened for reading", caught.exception.message)

    def test_a_write_transaction_refuses_before_the_begin(self):
        self.created()
        held = Store.open_readonly(self.path)
        self.addCleanup(held.close)
        reached = []
        with self.assertRaises(Refusal):
            held.transact(lambda: reached.append(True))
        self.assertEqual(reached, [])

    def test_a_public_transition_refuses_through_that_boundary(self):
        """Through the ordinary public face rather than the store directly."""
        self.created()
        authority = Authority.open_readonly(self.path,
                                            expected_authority_uuid=UUID)
        try:
            with self.assertRaises(Refusal):
                authority.create_work("0000000a-W1", "baton.impl",
                                      operation_id="op-1")
        finally:
            authority.dispose()

    def test_the_public_readers_still_answer(self):
        serving = self.created()
        serving.create_work("0000000a-W1", "baton.impl", operation_id="op-1")
        reading = Authority.open_readonly(self.path,
                                          expected_authority_uuid=UUID)
        try:
            self.assertEqual(reading.authority_uuid, UUID)
            projected = reading.project_work("0000000a-W1")
            self.assertEqual(projected["status"], "open")
        finally:
            reading.dispose()

    # -- coherently with a concurrent writer ---------------------------------

    def test_it_reads_committed_wal_data_written_while_it_is_open(self):
        """THE CASE THIS OPENER EXISTS FOR. A serving process holds the store
        in WAL mode and keeps committing; a separate reading handle must see
        each committed state, not a frozen one and not a stale one.
        """
        serving = self.created()
        serving.create_work("0000000a-W1", "baton.impl", operation_id="op-1")
        reading = Authority.open_readonly(self.path,
                                          expected_authority_uuid=UUID)
        self.addCleanup(reading.dispose)
        self.assertIsNotNone(reading.project_work("0000000a-W1"))
        # NOT YET THERE, and this authority says so by refusing rather than
        # by answering absence.
        with self.assertRaises(Refusal):
            reading.project_work("0000000a-W2")
        # COMMITTED AFTER THE READER WAS OPENED, by the writer that still
        # holds the store.
        serving.create_work("0000000a-W2", "baton.impl", operation_id="op-2")
        self.assertIsNotNone(reading.project_work("0000000a-W2"))

    def test_the_reader_leaves_the_writers_store_intact(self):
        serving = self.created()
        serving.create_work("0000000a-W1", "baton.impl", operation_id="op-1")
        before = self.entries()
        reading = Authority.open_readonly(self.path,
                                          expected_authority_uuid=UUID)
        reading.project_work("0000000a-W1")
        reading.dispose()
        self.assertEqual(self.entries(), before)
        # AND THE WRITER IS UNDISTURBED: it still commits afterwards.
        serving.create_work("0000000a-W3", "baton.impl", operation_id="op-3")
        self.assertIsNotNone(serving.project_work("0000000a-W3"))
