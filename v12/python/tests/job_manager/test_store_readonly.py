"""`JobStore.open_readonly` — the reader the Job store did not have.

W197661, claim201954, on review201931's direction. THE GAP THIS CLOSES was
recorded as that Work's finding F5: `JobStore.open` is write-capable — it
connects writable, `_initialize`s an absent store, `_adopt`s or MIGRATES an
existing one and requests WAL — and it was the ONLY opener. `ControlStore`,
`Authority` and `IntegrationStore` all already had a read-only counterpart, so
a caller that only wanted to read a Job store had nothing to use, and a
verifier composing `stage_execution.observation_from` reached a read-only
observation surface through a write-capable adapter.

WHY AN INTERIM GUARD WAS NOT ENOUGH, which is review201931's own correction and
the reason this file exists rather than another byte-fingerprint. The verifier's
stopgap checked SQLite's file header, which stops the demonstrated empty-file
initialization and stops nothing else: a VALID OLDER Job store passes the header
check and then reaches `_adopt` -> `_migrate`, which rewrites it. And a
fingerprint taken after the read can only report a change that has already
happened. Neither is a read-only capability.
`test_a_VALID_OLD_SCHEMA_store_is_refused_WITHOUT_migration` is the case that
separates this opener from that guard.

NO DEPLOYMENT, NO ENGINE, NO DESTINATION. Every case builds its own store in a
temporary directory.
"""

import os
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import JobStore
from baton_v12.job_manager import SCHEMA_VERSION, STORE_KIND, submission

from .fixtures import UUID, JobManagerCase
from .test_store import SCHEMA_1

OTHER_UUID = "f" * 32


def _is_database(path):
    """Whether SQLite can lock this path at all, for the leak probe below."""
    if not os.path.isfile(path):
        return False
    with open(path, "rb") as handle:
        return handle.read(16) == b"SQLite format 3\x00"


class ReadOnlyCase(JobManagerCase):
    """One owned store per case, and a reader over it."""

    def owned(self):
        """A current, Authority-bound store, written by the ordinary opener."""
        store = self.store()
        store.close()
        self.digest = self.bytes_of()
        return self.job_path

    def reading(self, path=None, authority_uuid=UUID, incarnation="reader-1"):
        store = JobStore.open_readonly(path or self.job_path,
                                       authority_uuid=authority_uuid,
                                       incarnation=incarnation,
                                       clock=self.clock)
        self.addCleanup(store.close)
        return store

    def bytes_of(self):
        with open(self.job_path, "rb") as handle:
            return handle.read()

    def beside(self):
        return sorted(one for one in os.listdir(self.root)
                      if one.startswith("jobs.sqlite3"))

    def refused(self, **named):
        with self.assertRaises(ContractRefusal) as caught:
            self.reading(**named)
        return caught.exception


class ItREADSAStoreThisBuildOwns(ReadOnlyCase):

    def test_an_owned_current_store_opens(self):
        self.owned()
        store = self.reading()
        self.assertEqual(store.authority_uuid, UUID)
        self.assertEqual(store.incarnation, "reader-1")

    def test_the_rows_it_answers_are_the_ONES_THAT_ARE_THERE(self):
        """An opener that returns a handle onto an empty schema would satisfy
        every refusal case in this file and be useless. The rows are read
        through the owning module rather than through raw SQL."""
        from . import fixtures

        writable = self.store()
        submission.submit(writable, fixtures.submission())
        writable.close()
        reader = self.reading()
        self.assertEqual(
            sorted(row["job_id"] for row in submission.job_rows(reader)),
            ["job-a", "job-b"])
        self.assertIsNotNone(submission.job_of(reader, "job-a"))

    def test_reading_leaves_the_store_BYTE_IDENTICAL(self):
        self.owned()
        self.reading()
        self.assertEqual(self.bytes_of(), self.digest)

    def test_reading_does_not_SWITCH_a_non_WAL_store_to_WAL(self):
        """`open` requests WAL; this must not, because changing a store's
        journal mode is a write to a store this caller only reads.

        THE STORE IS PUT BACK TO `delete` FIRST, and the case is worthless
        without that: the ordinary opener has already switched it to WAL, so
        reading `PRAGMA journal_mode` on an owned store reports `wal` whatever
        this opener does. The first form of this case asserted exactly that and
        would have passed a reader that requested WAL on every open.
        """
        self.owned()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.execute("PRAGMA journal_mode = delete")
        connection.close()
        store = self.reading()
        self.assertEqual(
            store._connection.execute("PRAGMA journal_mode").fetchone()[0]
            .lower(), "delete")
        store.close()
        self.assertEqual(self.beside(), ["jobs.sqlite3"])


class ItREFUSESToWrite(ReadOnlyCase):
    """The capability, proved by attempting it rather than asserted."""

    def test_a_WRITE_through_the_handle_is_refused_by_SQLITE_ITSELF(self):
        self.owned()
        store = self.reading()
        with self.assertRaises(sqlite3.OperationalError) as caught:
            store._connection.execute(
                "INSERT INTO meta VALUES ('probe', 'x')")
        self.assertIn("readonly", str(caught.exception).lower())

    def test_and_the_store_is_STILL_byte_identical_afterwards(self):
        self.owned()
        store = self.reading()
        try:
            store._connection.execute(
                "INSERT INTO meta VALUES ('probe', 'x')")
        except sqlite3.OperationalError:
            pass
        self.assertEqual(self.bytes_of(), self.digest)


class ItCREATESNothingAndINITIALIZESNothing(ReadOnlyCase):

    def test_a_MISSING_store_is_refused(self):
        why = self.refused()
        self.assertIn("existing regular store", str(why))

    def test_and_the_missing_store_is_STILL_MISSING(self):
        """`open` would have created it. This is the whole difference."""
        self.refused()
        self.assertEqual(self.beside(), [])

    def test_a_DIRECTORY_at_the_path_is_refused(self):
        os.mkdir(self.job_path)
        self.assertIn("existing regular store", str(self.refused()))

    def test_an_EMPTY_FILE_is_refused_and_NOT_initialized(self):
        """The defect the verifier's header guard was written for, and this is
        the owner refusing it rather than a caller guessing at bytes."""
        with open(self.job_path, "wb"):
            pass
        why = self.refused()
        self.assertIn("empty", str(why))
        self.assertEqual(self.bytes_of(), b"",
                         "the read-only opener initialized a store")

    def test_a_store_with_NO_OBJECTS_is_refused_and_NOT_initialized(self):
        """An empty FILE and an empty DATABASE are different inputs."""
        connection = sqlite3.connect(self.job_path)
        connection.close()
        before = self.bytes_of()
        self.assertIn("empty", str(self.refused()))
        self.assertEqual(self.bytes_of(), before)


class ItMIGRATESNothing(ReadOnlyCase):
    """Review201931: "_adopt currently migrates; do not call it blindly from
    the new opener.\""""

    def write_schema_1(self):
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.executescript(SCHEMA_1)
        connection.execute("INSERT INTO meta VALUES ('store_kind', ?)",
                           (STORE_KIND,))
        connection.execute("INSERT INTO meta VALUES ('schema_version', '1')")
        connection.close()

    def test_a_VALID_OLD_SCHEMA_store_is_refused_WITHOUT_migration(self):
        """THE CASE THE INTERIM GUARD COULD NOT PASS. This store is a
        syntactically valid SQLite database with this build's own store kind
        and a schema version `MIGRATIONS` has a path from -- so a file-header
        check waves it through and `_adopt` carries it forward. A read-only
        open must refuse it and leave every byte where it was."""
        self.write_schema_1()
        before = self.bytes_of()
        why = self.refused()
        self.assertIn("carries no migration", str(why))
        self.assertEqual(self.bytes_of(), before,
                         "the read-only opener migrated the store")

    def test_the_ORDINARY_opener_still_migrates_it(self):
        """The shared validation must not have changed `open`'s behaviour, and
        a refusal case that silently broke migration would look identical."""
        self.write_schema_1()
        store = self.store()
        recorded = dict(store._connection.execute(
            "SELECT key, value FROM meta").fetchall())
        self.assertEqual(recorded["schema_version"], str(SCHEMA_VERSION))

    def test_a_FUTURE_schema_store_is_refused(self):
        self.owned()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.execute(
            "UPDATE meta SET value = '99' WHERE key = 'schema_version'")
        connection.close()
        before = self.bytes_of()
        self.assertIn("schema", str(self.refused()))
        self.assertEqual(self.bytes_of(), before)


class ItREFUSESWhatIsNotItsOwn(ReadOnlyCase):

    def test_a_FOREIGN_database_is_refused(self):
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.execute("CREATE TABLE somebody_elses (x TEXT)")
        connection.close()
        before = self.bytes_of()
        self.assertIn("not a Job store this build owns", str(self.refused()))
        self.assertEqual(self.bytes_of(), before)

    def test_a_database_with_a_COINCIDENTAL_meta_table_is_refused(self):
        """The name `meta` is not permission to read `key, value` out of it."""
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.execute("CREATE TABLE meta (key TEXT, value TEXT)")
        connection.execute("INSERT INTO meta VALUES ('key', 'value')")
        connection.close()
        self.assertIn("not a", str(self.refused()))

    def test_ANOTHER_AUTHORITYS_store_is_refused(self):
        self.owned()
        why = self.refused(authority_uuid=OTHER_UUID)
        self.assertIn("belongs to Authority", str(why))
        self.assertEqual(self.bytes_of(), self.digest)

    def test_a_MALFORMED_authority_operand_is_refused_before_the_path(self):
        """Proved by refusing at a path that is not even there: if the operand
        were checked after the file, this would report the missing store."""
        why = self.refused(authority_uuid="not-a-uuid")
        self.assertNotIn("existing regular store", str(why))

    def test_an_EMPTY_incarnation_is_refused(self):
        self.owned()
        self.assertIn("incarnation", str(self.refused(incarnation="")))


class EveryFailurePathRELEASESItsHandle(ReadOnlyCase):
    """`open`'s own words: "A refused open that leaked one would hold a lock on
    a store this build has just said it must not touch.\""""

    def leaves_nothing(self, **named):
        """THE DATABASE IS THE THING THAT MUST NOT MOVE, and SQLite's own
        working files are a different question -- review201931: "distinguish
        SQLite-managed sidecars from logical database mutation".

        TWO CORRECTIONS ARE BAKED IN HERE. The first form compared the file
        list against an empty one, so a case that first wrote an owned store
        through the WRITABLE opener blamed this refusal for that opener's
        sidecars. The second form compared the list before and after, and found
        something real: opening a WAL-mode database `mode=ro` makes SQLite
        create `-shm`/`-wal` to read it, and a read-only connection cannot
        checkpoint or remove them on close. That is SQLite reading a WAL
        database, not this opener writing one -- so what is asserted is that
        the DATABASE's bytes are identical and no handle was leaked.
        """
        before = self.bytes_of() if os.path.isfile(self.job_path) else None
        with self.assertRaises(ContractRefusal):
            JobStore.open_readonly(self.job_path, clock=self.clock,
                                   **{"authority_uuid": UUID,
                                      "incarnation": "reader-1", **named})
        after = self.bytes_of() if os.path.isfile(self.job_path) else None
        self.assertEqual(after, before, "a refusal changed the database")
        # THE HANDLE IS GONE, proved by taking the exclusive lock a leaked
        # reader would still be holding. A path that is not a database cannot
        # be locked at all, so it is exempted rather than reported as a leak --
        # the case that supplies one has nothing to leak a lock ON.
        if not _is_database(self.job_path):
            return
        writer = sqlite3.connect(self.job_path, isolation_level=None)
        try:
            writer.execute("PRAGMA locking_mode = EXCLUSIVE")
            writer.execute("BEGIN EXCLUSIVE")
            writer.execute("ROLLBACK")
        except sqlite3.OperationalError as why:
            self.fail(f"a refusal leaked its handle: {why}")
        finally:
            writer.close()

    def test_a_foreign_database_releases(self):
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.execute("CREATE TABLE somebody_elses (x TEXT)")
        connection.close()
        self.leaves_nothing()

    def test_another_authority_releases(self):
        self.owned()
        self.leaves_nothing(authority_uuid=OTHER_UUID)

    def test_an_old_schema_releases(self):
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.executescript(SCHEMA_1)
        connection.execute("INSERT INTO meta VALUES ('store_kind', ?)",
                           (STORE_KIND,))
        connection.execute("INSERT INTO meta VALUES ('schema_version', '1')")
        connection.close()
        self.leaves_nothing()

    def test_a_NON_DATABASE_file_releases_and_is_a_CONTRACT_refusal(self):
        """A driver's own exception escaping here would make a reader handle
        two vocabularies for the same answer."""
        with open(self.job_path, "wb") as handle:
            handle.write(b"NOT A DATABASE AT ALL\n")
        self.leaves_nothing()

    def test_the_non_database_refusal_names_NO_WRITABLE_FALLBACK(self):
        with open(self.job_path, "wb") as handle:
            handle.write(b"NOT A DATABASE AT ALL\n")
        with self.assertRaises(ContractRefusal) as caught:
            self.reading()
        self.assertIn("no write-capable fallback", str(caught.exception))


class SQLiteManagedSidecarsAreNOTDatabaseMutation(ReadOnlyCase):
    """The distinction review201931 asked for, pinned rather than assumed.

    A Job store an ordinary manager has used is in WAL mode, persistently.
    SQLite needs `-shm` (and `-wal`) to READ such a database, and a `mode=ro`
    connection can neither checkpoint nor remove them. So a read-only open of a
    WAL store can leave those files behind -- and that is SQLite reading a WAL
    database, not this opener writing to one.

    WHY IT IS SAID OUT LOUD INSTEAD OF EXCUSED: W197661's verifier reports a
    surviving sidecar as a FAILED check, and a reader who did not know this
    would read that failure as evidence the store was modified. The database
    bytes are the fact that matters, and these cases prove they do not move.
    """

    def wal_store(self):
        self.owned()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.execute("PRAGMA journal_mode = WAL")
        connection.close()
        return self.bytes_of()

    def test_a_successful_read_of_a_WAL_store_changes_no_DATABASE_byte(self):
        before = self.wal_store()
        store = self.reading()
        store.close()
        self.assertEqual(self.bytes_of(), before)

    def test_a_REFUSED_read_of_a_WAL_store_changes_no_DATABASE_byte(self):
        before = self.wal_store()
        with self.assertRaises(ContractRefusal):
            self.reading(authority_uuid=OTHER_UUID)
        self.assertEqual(self.bytes_of(), before)

    def test_a_NON_WAL_store_gains_no_sidecar_at_all(self):
        """The clean case, so the one above reads as SQLite's WAL requirement
        rather than as something this opener does generally."""
        self.owned()
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.execute("PRAGMA journal_mode = delete")
        connection.close()
        store = self.reading()
        store.close()
        self.assertEqual(self.beside(), ["jobs.sqlite3"])


class TheORDINARYOpenerIsUNCHANGED(ReadOnlyCase):
    """Review201931: "Share nonmutating validation where sound without changing
    writable open behavior." `_adopt` now calls `_recognized`; these pin that
    the powers it kept are the ones it had."""

    def test_open_STILL_INITIALIZES_an_absent_store(self):
        self.assertFalse(os.path.exists(self.job_path))
        self.store()
        self.assertTrue(os.path.isfile(self.job_path))

    def test_open_STILL_REFUSES_a_foreign_database(self):
        connection = sqlite3.connect(self.job_path, isolation_level=None)
        connection.execute("CREATE TABLE somebody_elses (x TEXT)")
        connection.close()
        with self.assertRaises(ContractRefusal) as caught:
            self.store()
        self.assertIn("not a Job store this build owns", str(caught.exception))

    def test_open_STILL_REFUSES_another_Authoritys_store(self):
        self.owned()
        with self.assertRaises(ContractRefusal) as caught:
            self.store(authority_uuid=OTHER_UUID)
        self.assertIn("belongs to Authority", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
