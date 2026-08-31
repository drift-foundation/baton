"""W4 cut B — the control store, its journal, and what survives a restart.

PLAN item 4bc. The obligations are the frozen Node store's, ported by property
rather than by transliteration: ownership before adoption, one atomic boundary,
two kinds of refusal with opposite storage, presence as its own fact, and
byte-stable replay.
"""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest import mock

import baton_v12.worker_manager as worker_manager
from baton_v12.contracts import ContractRefusal, ERROR_CODES
from baton_v12.worker_manager import (ControlStore, SCHEMA_VERSION, STORE_KIND,
                                      manager_signature, revive_refusal,
                                      seal_refusal)

NOW = "2026-08-24T00:00:00.000Z"


class StoreCase(unittest.TestCase):

    def setUp(self):
        # `v12-worker-manager-`, not `v12-manager-`: the FROZEN NODE suite uses
        # the latter and left 435 roots on this machine from 2026-08-22, so a
        # hygiene check on my own prefix could not tell my leaks from its. A
        # check that cannot attribute what it counts reports the wrong thing --
        # which is the same lesson as attributing mutation failures to named
        # cases.
        self._root = tempfile.TemporaryDirectory(prefix="v12-worker-manager-")
        self.addCleanup(self._root.cleanup)
        self.root = self._root.name
        self.path = os.path.join(self.root, "control.sqlite3")

    def store(self, path=None, incarnation="manager-1", clock=None):
        store = ControlStore.open(path or self.path, incarnation=incarnation,
                                  clock=clock or (lambda: NOW))
        self.addCleanup(store.close)
        return store

    def bytes_at(self, path):
        with open(path, "rb") as handle:
            return handle.read()

    def foreign_store(self, name, statements):
        path = os.path.join(self.root, name)
        connection = sqlite3.connect(path, isolation_level=None)
        for statement in statements:
            connection.execute(statement)
        connection.close()
        return path

    def signature(self, kind="offer.issue", **operands):
        return manager_signature(kind, operands or {"work_id": "0000000a-W1"})


class OwnershipBeforeAdoption(StoreCase):

    def test_an_empty_database_becomes_this_manager_s_store(self):
        store = self.store()
        self.assertEqual(store.incarnation, "manager-1")
        recorded = dict(store._connection.execute(
            "SELECT key, value FROM meta").fetchall())
        self.assertEqual(recorded["store_kind"], STORE_KIND)
        self.assertEqual(recorded["schema_version"], str(SCHEMA_VERSION))

    def test_reopening_our_own_store_adds_nothing(self):
        self.store().close()
        before = self.bytes_at(self.path)
        self.store()
        # The second open validates. It may not grow the schema, and the marker
        # must still say the same thing.
        # W54881: this read used to be an unnamed `sqlite3.connect(...)` whose
        # handle nothing ever closed, so `test_store` reported OK and then
        # emitted one unclosed-database warning of its own. That is the same
        # custody failure this class now proves `ControlStore.open` does not
        # commit; a suite that leaks while asserting nothing leaks is one whose
        # warnings a reader learns to ignore.
        reading = sqlite3.connect(self.path)
        self.addCleanup(reading.close)
        objects = {row[0] for row in reading.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        # Cut C added the offers table and cut D the attempt and its
        # observations, each with the indexes their invariants need -- so the
        # shape a reopen must not grow is this one. Asserted from the module
        # rather than retyped, because a list written twice is a list that
        # agrees in one of the two places.
        from baton_v12.worker_manager import TABLES
        self.assertEqual(objects, set(TABLES) | {
            "offers_one_live_per_work", "offers_one_claim_per_attempt",
            "observations_manager_order", "profiles_by_digest",
            # W6627: one interrogation lists by the session it is addressed to.
            "interrogations_by_session",
            # W32649: the predecessor interlock reads by Work rather than by
            # lane, and one attempt holds at most one lane.
            "runtime_lanes_by_work", "runtime_lanes_one_per_holder"})
        del before

    def test_somebody_else_s_database_is_refused_with_nothing_changed(self):
        """Absence of our metadata is not evidence that a file is ours.

        The frozen host asked only whether `meta` existed and treated its
        absence as proof the file was new, so a pre-existing database holding
        `foreign_state` was ADOPTED and came back carrying both that table and
        every manager table.
        """
        path = self.foreign_store(
            "foreign.sqlite3", ["CREATE TABLE foreign_state (id INTEGER)"])
        before = self.bytes_at(path)
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(path, incarnation="manager-1", clock=lambda: NOW)
        self.assertEqual(caught.exception.category, "integrity")
        self.assertIn("Nothing was changed", str(caught.exception))
        self.assertEqual(self.bytes_at(path), before)

    def test_an_unrelated_meta_table_is_still_a_closed_refusal(self):
        path = self.foreign_store(
            "foreign-meta.sqlite3", ["CREATE TABLE meta (id INTEGER)"])
        before = self.bytes_at(path)
        with self.assertRaises(ContractRefusal):
            ControlStore.open(path, incarnation="manager-1", clock=lambda: NOW)
        self.assertEqual(self.bytes_at(path), before)

    def test_concurrent_first_openers_adopt_one_initialized_store(self):
        count = 4
        arrived = threading.Barrier(count)
        original = ControlStore._initialize

        def synchronized(connection):
            # Hold the first initializer before its write lock so every opener
            # has independently observed the same genuinely empty schema.
            arrived.wait(timeout=10)
            return original(connection)

        def open_one(index):
            store = ControlStore.open(
                self.path, incarnation=f"manager-{index}", clock=lambda: NOW)
            try:
                return store.incarnation
            finally:
                store.close()

        ControlStore._initialize = staticmethod(synchronized)
        try:
            with ThreadPoolExecutor(max_workers=count) as pool:
                opened = list(pool.map(open_one, range(count)))
        finally:
            ControlStore._initialize = staticmethod(original)
        self.assertEqual(set(opened), {f"manager-{index}" for index in range(count)})
        store = self.store()
        self.assertEqual(store.operation_record("none"), None)

    def test_another_product_s_store_is_refused_by_KIND_before_version(self):
        # Schema version 1 is true of several stores beside this one, so telling
        # a caller their store is the wrong VERSION when it is the wrong PRODUCT
        # sends them to fix the wrong thing.
        path = self.foreign_store("authority.sqlite3", [
            "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
            "INSERT INTO meta VALUES ('store_kind', "
            "'baton.v12.python.authority')",
            "INSERT INTO meta VALUES ('schema_version', '1')"])
        before = self.bytes_at(path)
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(path, incarnation="manager-1", clock=lambda: NOW)
        message = str(caught.exception)
        self.assertIn("authority", message)
        self.assertNotIn("schema 1", message)
        self.assertEqual(self.bytes_at(path), before)

    def test_the_two_foreign_shapes_are_told_apart(self):
        # A database with NO metadata and one with a `meta` we cannot read are
        # different facts, and the second message is wrong about the first. A
        # mutation that removed the first branch still refused -- with the wrong
        # reason -- so the case reads the reason.
        without = self.foreign_store(
            "no-meta.sqlite3", ["CREATE TABLE foreign_state (id INTEGER)"])
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(without, incarnation="m", clock=lambda: NOW)
        self.assertIn("none is this manager's metadata", str(caught.exception))
        unreadable = self.foreign_store(
            "odd-meta.sqlite3", ["CREATE TABLE meta (id INTEGER)"])
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(unreadable, incarnation="m", clock=lambda: NOW)
        self.assertIn("cannot read", str(caught.exception))

    def test_a_store_written_under_the_previous_shape_is_refused(self):
        # The version was raised WITH the row invariant, because a store written
        # under the weaker table cannot satisfy the rule this build enforces.
        # Keeping the number would have let this build adopt one.
        # EVERY earlier shape, not just the first. My version-bump cases named
        # v1 while the build moved to 2, then 3, then 4 -- so a mutation
        # reverting the number by one measured zero. A store recorded at ANY
        # version this build does not speak is refused, and the case walks them.
        for earlier in ("1", "2", "3"):
            with self.subTest(recorded=earlier):
                other = self.foreign_store(f"v{earlier}-shape.sqlite3", [
                    "CREATE TABLE meta (key TEXT PRIMARY KEY, "
                    "value TEXT NOT NULL)",
                    f"INSERT INTO meta VALUES ('store_kind', '{STORE_KIND}')",
                    f"INSERT INTO meta VALUES ('schema_version', '{earlier}')"])
                with self.assertRaises(ContractRefusal):
                    ControlStore.open(other, incarnation="m", clock=lambda: NOW)
        path = self.foreign_store("v1.sqlite3", [
            "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
            f"INSERT INTO meta VALUES ('store_kind', '{STORE_KIND}')",
            "INSERT INTO meta VALUES ('schema_version', '1')",
            "CREATE TABLE operations (operation_id TEXT PRIMARY KEY, "
            "kind TEXT NOT NULL, signature TEXT NOT NULL, state TEXT NOT NULL, "
            "result TEXT, refusal TEXT, settled_at TEXT NOT NULL)"])
        before = self.bytes_at(path)
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(path, incarnation="m", clock=lambda: NOW)
        self.assertIn("does not guess across versions", str(caught.exception))
        self.assertEqual(self.bytes_at(path), before)

    def test_a_store_of_another_version_is_refused_in_either_direction(self):
        for what, version in [("older", "0"), ("newer", "99"),
                              ("unrecorded", None)]:
            with self.subTest(what=what):
                statements = [
                    "CREATE TABLE meta (key TEXT PRIMARY KEY, "
                    "value TEXT NOT NULL)",
                    f"INSERT INTO meta VALUES ('store_kind', '{STORE_KIND}')"]
                if version is not None:
                    statements.append(
                        f"INSERT INTO meta VALUES ('schema_version', "
                        f"'{version}')")
                path = self.foreign_store(f"v{what}.sqlite3", statements)
                before = self.bytes_at(path)
                with self.assertRaises(ContractRefusal):
                    ControlStore.open(path, incarnation="manager-1",
                                      clock=lambda: NOW)
                self.assertEqual(self.bytes_at(path), before)

    def open_descriptors(self, path):
        """How many of THIS process's file descriptors point at `path`.

        My first version of the case below wrote to the file from another
        connection and called that proof. It was not: a leaked connection with
        no open transaction holds no lock, so the write succeeded either way and
        the case passed whether or not the handle leaked. Mutating the cleanup
        away changed nothing, which is how I found out.

        Descriptors are the fact the case is actually about.
        """
        target = os.path.realpath(path)
        found = 0
        for entry in os.listdir("/proc/self/fd"):
            try:
                if os.path.realpath(f"/proc/self/fd/{entry}") == target:
                    found += 1
            except OSError:
                continue
        return found

    def test_a_refused_open_leaves_no_handle_open(self):
        # A refused open that leaked a handle would hold an open descriptor on a
        # store this build has just said it must not touch -- and would take a
        # lock the moment anything used it.
        path = self.foreign_store(
            "locked.sqlite3", ["CREATE TABLE foreign_state (id INTEGER)"])
        before = self.open_descriptors(path)
        with self.assertRaises(ContractRefusal):
            ControlStore.open(path, incarnation="manager-1", clock=lambda: NOW)
        self.assertEqual(self.open_descriptors(path), before)

    def test_a_refused_open_of_our_own_store_leaks_nothing_either(self):
        # The other refusal path: the file IS ours in kind but not in version,
        # so the handle is opened, the marker is read, and the refusal happens
        # later. That is the path a `finally` is easiest to forget on.
        path = self.foreign_store("wrong-version.sqlite3", [
            "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)",
            f"INSERT INTO meta VALUES ('store_kind', '{STORE_KIND}')",
            "INSERT INTO meta VALUES ('schema_version', '99')"])
        before = self.open_descriptors(path)
        with self.assertRaises(ContractRefusal):
            ControlStore.open(path, incarnation="manager-1", clock=lambda: NOW)
        self.assertEqual(self.open_descriptors(path), before)

    def test_the_store_needs_an_explicit_path_and_an_incarnation(self):
        for what, arguments in [
                ("no path", {"path": "", "incarnation": "m"}),
                ("a path that is not text", {"path": 7, "incarnation": "m"}),
                ("no incarnation", {"path": self.path, "incarnation": ""}),
                ("an incarnation that is not text",
                 {"path": self.path, "incarnation": 7})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    ControlStore.open(arguments["path"],
                                      incarnation=arguments["incarnation"],
                                      clock=lambda: NOW)

    def test_a_clock_that_cannot_stamp_a_row_is_found_at_open(self):
        for what, clock in [("not callable", "2026"),
                            ("answers a number", lambda: 7),
                            ("answers nothing", lambda: ""),
                            # TEXT THAT IS NOT AN INSTANT. Every deadline this
                            # manager compares is derived from this value, so
                            # storable and ORDERABLE are two properties -- and a
                            # mutation that kept only the first measured zero
                            # until this row existed.
                            ("answers prose", lambda: "banana"),
                            ("answers a near-miss",
                             lambda: "2026-08-24T00:00:00Z"),
                            ("answers a local time",
                             lambda: "2026-08-24 00:00:00.000Z")]:
            with self.subTest(what=what):
                path = os.path.join(self.root, f"clock-{what[:4]}.sqlite3")
                with self.assertRaises(ContractRefusal):
                    ControlStore.open(path, incarnation="m", clock=clock)

    def test_a_refused_clock_answer_leaves_no_handle_open(self):
        """W54881: the refusal that happens LAST is the one custody forgot.

        `open`'s promise is that every failure closes the handle, and the two
        cases above prove it for the refusals that happen while the connection
        is still a local. The clock is proved after the `ControlStore` is
        constructed, and that construction used to be outside the
        close-on-error region: the refusal lost the only reference to the
        connection, so the caller had no object it could close and the handle
        waited for the collector. The focused clock case above reported `OK`
        and leaked five connections; W54182's 549-probe driver leaked one.

        DESCRIPTORS, for the same reason the two cases above use them: a
        leaked connection with no open transaction holds no lock, so proving
        that something else can still write proves nothing about custody.

        A FRESH PATH PER CLOCK, because a leaked descriptor from an earlier
        iteration would be counted against the next one and the case would
        report the wrong clock.
        """
        for what, clock in [("answers a number", lambda: 7),
                            ("answers nothing", lambda: ""),
                            ("answers prose", lambda: "banana"),
                            ("answers a near-miss",
                             lambda: "2026-08-24T00:00:00Z"),
                            ("answers a local time",
                             lambda: "2026-08-24 00:00:00.000Z")]:
            with self.subTest(what=what):
                path = os.path.join(self.root, f"leak-{what[8:12]}.sqlite3")
                before = self.open_descriptors(path)
                with self.assertRaises(ContractRefusal):
                    ControlStore.open(path, incarnation="m", clock=clock)
                self.assertEqual(self.open_descriptors(path), before,
                                 "a refused clock answer left its handle open")

    def test_a_clock_that_raises_takes_its_handle_with_it_and_nothing_else(self):
        """The other half of W54881, and the ruling it must not disturb.

        A configured clock that RAISES is a trusted collaborator's fault and is
        deliberately left to raise as itself -- the fault is not translated into
        a manager refusal, because rewriting it would hide whose fault it is.
        Widening the close-on-error region must not change that. So this
        requires both halves at once: the exact exception object escapes, and
        the connection it escaped through is closed.
        """
        fault = RuntimeError("the deployment's clock is broken")

        def raising():
            raise fault

        path = os.path.join(self.root, "clock-raises.sqlite3")
        before = self.open_descriptors(path)
        with self.assertRaises(RuntimeError) as caught:
            ControlStore.open(path, incarnation="m", clock=raising)
        self.assertIs(caught.exception, fault,
                      "the collaborator's own fault was translated")
        self.assertEqual(self.open_descriptors(path), before,
                         "a raising clock left its handle open")

    def test_a_successful_open_still_holds_its_handle(self):
        """The counterweight, so the two cases above cannot pass vacuously.

        `open_descriptors` returning the baseline for a refusal only means
        something if it does NOT return the baseline for a store that opened.
        Measured: without this, closing the connection unconditionally at the
        end of `open` would satisfy every leak case in this class.
        """
        path = os.path.join(self.root, "held.sqlite3")
        before = self.open_descriptors(path)
        store = self.store(path=path)
        self.assertGreater(self.open_descriptors(path), before,
                           "an opened store holds no descriptor on its file")
        store.close()
        self.assertEqual(self.open_descriptors(path), before,
                         "a closed store kept its handle")


class OneAtomicBoundary(StoreCase):

    def test_an_exact_repeat_replays_and_performs_nothing_twice(self):
        store = self.store()
        signature = self.signature()
        ran = []

        def action(connection):
            ran.append("ran")
            return {"issued": True}

        first = store.transact("op-1", "offer.issue", signature, action)
        again = store.transact("op-1", "offer.issue", signature,
                               lambda connection: {"issued": "SOMETHING ELSE"})
        self.assertEqual(first, {"issued": True})
        self.assertEqual(again, first)
        self.assertEqual(len(ran), 1)

    def test_a_committed_null_result_is_not_absence(self):
        """PRESENCE IS ITS OWN FACT.

        The frozen host answered `null` for both "no row" and "the committed
        result was JSON null", so an exact retry of a null-returning operation
        looked new, ran the action a SECOND time, and only then hit the primary
        key. Effectively-once cannot be built on a value that also means
        absence.
        """
        store = self.store()
        signature = self.signature()
        ran = []
        store.transact("op-1", "offer.issue", signature,
                       lambda connection: ran.append("ran"))
        self.assertIsNone(store.transact("op-1", "offer.issue", signature,
                                         lambda connection: ran.append("again")))
        self.assertEqual(len(ran), 1)
        self.assertEqual(store.replay("op-1", signature), (True, None))
        self.assertEqual(store.replay("op-unknown", signature), (False, None))

    def test_a_reused_id_with_different_operands_collides(self):
        store = self.store()
        store.transact("op-1", "offer.issue", self.signature(),
                       lambda connection: {"issued": True})
        with self.assertRaises(ContractRefusal) as caught:
            store.transact("op-1", "offer.issue",
                           self.signature(work_id="0000000a-W2"),
                           lambda connection: {"issued": "different"})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "operation-collision"))
        # And it CHANGED NOTHING: the first record stands.
        self.assertEqual(store.operation_record("op-1")["signature"],
                         self.signature())

    def test_the_operation_kind_is_part_of_the_collision_identity(self):
        store = self.store()
        signature = self.signature(kind="offer.issue")
        store.transact("op-1", "offer.issue", signature,
                       lambda connection: {"issued": True})
        with self.assertRaises(ContractRefusal) as caught:
            store.transact("op-1", "cleanup.destroy", signature,
                           lambda connection: {"destroyed": True})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "operation-collision"))

    def test_the_journal_schema_requires_exactly_one_sealed_outcome(self):
        store = self.store()
        malformed = [
            ("committed-without-result", "committed", None, None),
            ("committed-with-refusal", "committed", "null", "sealed"),
            ("refused-without-refusal", "refused", None, None),
            ("refused-with-result", "refused", "null", "sealed"),
        ]
        for operation_id, state, result, refusal in malformed:
            with self.subTest(operation_id=operation_id):
                with self.assertRaises(sqlite3.IntegrityError):
                    store._connection.execute(
                        "INSERT INTO operations (operation_id, kind, signature, "
                        "state, result, refusal, settled_at) VALUES (?, ?, ?, ?, "
                        "?, ?, ?)",
                        (operation_id, "kind", "signature", state, result,
                         refusal, NOW))

    def test_a_recorded_kind_that_disagrees_still_collides(self):
        # `_agreeing` stops a contradictory row being WRITTEN, so the replay
        # comparison is unreachable from the public path -- and unreachable is
        # not the same as unnecessary. A row written by another writer, or by an
        # older build, must still collide rather than replay an outcome that was
        # decided about something else.
        store = self.store()
        signature = self.signature(kind="offer.issue")
        store._connection.execute(
            "INSERT INTO operations (operation_id, kind, signature, state, "
            "result, settled_at) VALUES (?, ?, ?, 'committed', 'null', ?)",
            ("op-1", "cleanup.destroy", signature, NOW))
        with self.assertRaises(ContractRefusal) as caught:
            store.transact("op-1", "offer.issue", signature,
                           lambda connection: {"issued": True})
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_contradictory_kind_and_signature_write_no_row_at_all(self):
        # The other half: `_agreeing` runs BEFORE the journal, so a submission
        # whose two accounts of the kind disagree leaves nothing to replay.
        store = self.store()
        with self.assertRaises(ContractRefusal) as caught:
            store.transact("op-fresh", "cleanup.destroy",
                           self.signature(kind="offer.issue"),
                           lambda connection: {"issued": True})
        self.assertEqual(caught.exception.code, "operation-collision")
        self.assertIsNone(store.operation_record("op-fresh"))

    def test_a_signature_that_is_not_canonical_text_is_a_refusal(self):
        # Not a fault. `json.loads` raises `TypeError` for a non-text operand,
        # which my first version did not catch -- so a boundary that had a
        # refusal ready let a defect escape instead.
        store = self.store()
        for what, signature in [("none", None), ("a number", 7),
                                ("empty", ""), ("not json", "{"),
                                ("json that is not a record", "[1, 2]"),
                                ("bytes", b"{}")]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    store.transact("op-x", "offer.issue", signature,
                                   lambda connection: None)

    def test_a_noncanonical_json_spelling_is_not_a_durable_identity(self):
        canonical = self.signature()
        noncanonical = json.dumps(json.loads(canonical), indent=2)
        self.assertNotEqual(noncanonical, canonical)
        store = self.store()
        with self.assertRaises(ContractRefusal):
            store.transact("op-x", "offer.issue", noncanonical,
                           lambda connection: None)
        self.assertIsNone(store.operation_record("op-x"))

    def test_a_signature_has_exactly_the_manager_owned_shape(self):
        store = self.store()
        for what, signature in [
                ("missing operands", '{"kind":"offer.issue"}'),
                ("extra member",
                 '{"extra":null,"kind":"offer.issue","operands":{}}')]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    store.transact("op-" + what, "offer.issue", signature,
                                   lambda connection: None)
                self.assertIsNone(store.operation_record("op-" + what))

    def test_an_operation_kind_is_durable_text_before_it_reaches_sql(self):
        class HostileKind:
            def __eq__(self, other):
                raise AssertionError("a rejected operation kind was executed")

        store = self.store()
        for what, kind, signature in [
                ("null", None, '{"kind":null,"operands":{}}'),
                ("integer", 7, '{"kind":7,"operands":{}}'),
                ("empty", "", '{"kind":"","operands":{}}'),
                ("behaviour", HostileKind(),
                 '{"kind":"offer.issue","operands":{}}')]:
            with self.subTest(what=what):
                operation_id = "op-" + what
                with self.assertRaises(ContractRefusal):
                    store.transact(operation_id, kind, signature,
                                   lambda connection: {"committed": True})
                self.assertIsNone(store.operation_record(operation_id))

    def test_every_value_that_reaches_a_text_column_is_durable_text(self):
        """The review named the KIND; the rule applies at four values.

        A sweep of everything this store puts into a TEXT column found the same
        `UnicodeEncodeError` escaping from three more: the operation identity,
        the settled instant, and a durable refusal's sealed message. A rule
        applied at one of four sites is not applied, so it is applied at all
        four and each is measured.
        """
        surrogate = "\ud800"
        store = self.store()
        with self.subTest(value="the operation identity"):
            with self.assertRaises(ContractRefusal):
                store.transact("op-" + surrogate, "offer.issue",
                               self.signature(), lambda connection: {"a": 1})

        with self.subTest(value="the identity on the READ paths"):
            # Found by writing the case above: an identity that cannot be
            # durable text cannot name a row either, so a lookup for one is a
            # lookup for something that cannot exist -- and both reads were
            # faulting in the driver rather than refusing.
            for read in (lambda: store.operation_record("op-" + surrogate),
                         lambda: store.replay("op-" + surrogate,
                                              self.signature())):
                with self.assertRaises(ContractRefusal):
                    read()

        with self.subTest(value="the settled instant"):
            # Refused AT OPEN, which is earlier than I wrote the case for: the
            # clock is proved when the store is built, so a clock that cannot
            # stamp a row never gets one to stamp. Asserted where it actually
            # happens rather than where I expected it.
            with self.assertRaises(ContractRefusal):
                ControlStore.open(os.path.join(self.root, "clock.sqlite3"),
                                  incarnation="m",
                                  clock=lambda: "2026-" + surrogate)

        with self.subTest(value="a durable refusal's message"):
            unsealable = self.store(
                path=os.path.join(self.root, "sealed.sqlite3"))

            # MIGRATED by W7079. This raised a refusal whose MESSAGE was
            # unencodable, to prove the store refuses it at the text column.
            # `ContractRefusal` now owns its own message at construction, so
            # that message can no longer be built and this boundary is
            # unreachable through it -- the earlier owner is the better one.
            # The store's rule still needs a witness, so the unstorable text
            # now arrives on the operand the store itself composes.
            def action(connection):
                connection.execute(
                    "INSERT INTO operations (operation_id, kind, signature, "
                    "state, result, settled_at) "
                    "VALUES ('kept', 'k', 's', 'committed', 'null', ?)", (NOW,))
                raise ContractRefusal("policy", "retention",
                                      "held material", durable=True)

            # SUPERSEDED BY W7079, and the rest of this sub-case with it.
            # It drove an unstorable message through `transact` to prove the
            # store refuses it at the text column and rolls the durable
            # refusal's writes back. `ContractRefusal` now owns its own message
            # AT CONSTRUCTION, so that message cannot be built at all and the
            # store boundary is unreachable through it -- the earlier owner is
            # the better one, and this campaign removes a boundary it can no
            # longer reach rather than documenting one.
            #
            # What is still true, and is what this now asserts: the unstorable
            # message is refused, one step earlier.
            with self.assertRaises(AssertionError):
                ContractRefusal("policy", "retention", "held " + surrogate,
                                durable=True)
            del action, unsealable

    def test_the_exported_helper_cannot_build_an_identity_the_store_refuses(self):
        # A helper that manufactures a signature the store must then refuse is a
        # helper that invites the caller to discover the rule by hitting it.
        for what, kind in [("none", None), ("an integer", 7), ("empty", ""),
                           ("a surrogate", "offer.\ud800"),
                           ("a list", ["offer.issue"])]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    manager_signature(kind, {"work_id": "0000000a-W1"})

    def test_an_exported_text_rule_is_itself_a_closed_boundary(self):
        # The shared rule may stay private. If it is deliberately exported, its
        # diagnostic label becomes caller input and inherits the same no-code,
        # bounded-output rule as every other public label.
        if "durable_text" not in worker_manager.__all__:
            return

        class HostileLabel:
            def __format__(self, specification):
                raise AssertionError("a rejected label was executed")

        with self.assertRaises(ContractRefusal):
            worker_manager.durable_text(None, HostileLabel())
        with self.assertRaises(ContractRefusal) as caught:
            worker_manager.durable_text(None, "x" * 100_000)
        self.assertLess(len(str(caught.exception)), 500)

    def test_every_mutating_act_carries_an_operation_identity(self):
        store = self.store()
        for what, identity in [("empty", ""), ("none", None), ("a number", 7)]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal):
                    store.transact(identity, "offer.issue", self.signature(),
                                   lambda connection: None)

    def test_an_ordinary_refusal_rolls_back_what_it_wrote(self):
        store = self.store()

        def action(connection):
            connection.execute(
                # A COMPLETE row: the journal's invariant forbids a committed
                # row with no result, and my first fixtures wrote exactly that.
                # The invariant caught my own tests, which is the argument for
                # putting it in the schema rather than in the writer.
                "INSERT INTO operations (operation_id, kind, signature, state, "
                "result, settled_at) "
                "VALUES ('side-effect', 'k', 's', 'committed', 'null', ?)",
                (NOW,))
            raise ContractRefusal("refused", "precondition", "not yet")

        with self.assertRaises(ContractRefusal):
            store.transact("op-1", "offer.issue", self.signature(), action)
        # Nothing written, nothing journalled, and the identity stays usable.
        self.assertIsNone(store.operation_record("side-effect"))
        self.assertIsNone(store.operation_record("op-1"))
        self.assertEqual(store.transact("op-1", "offer.issue", self.signature(),
                                        lambda connection: {"later": True}),
                         {"later": True})

    def test_a_durable_refusal_keeps_its_writes_and_is_replayed(self):
        """The opposite storage, and the reason the action runs in a savepoint.

        A durable refusal is itself a committed outcome, so its writes and the
        refusal record survive and the retry REPLAYS the refusal rather than
        re-deciding it.
        """
        store = self.store()
        attempts = []

        def action(connection):
            attempts.append("ran")
            connection.execute(
                "INSERT INTO operations (operation_id, kind, signature, state, "
                "result, settled_at) "
                "VALUES ('kept', 'k', 's', 'committed', 'null', ?)", (NOW,))
            raise ContractRefusal("policy", "retention",
                                  "intake blocked the cleanup", durable=True)

        with self.assertRaises(ContractRefusal) as first:
            store.transact("op-1", "offer.issue", self.signature(), action)
        self.assertTrue(first.exception.durable)
        self.assertIsNotNone(store.operation_record("kept"))
        with self.assertRaises(ContractRefusal) as replayed:
            store.transact("op-1", "offer.issue", self.signature(), action)
        # THE SAME closed pair, not a rebuilt `refused.precondition`: a
        # `policy.retention` and a `refused.precondition` are different answers
        # with different retry policies.
        self.assertEqual(
            (replayed.exception.category, replayed.exception.code),
            ("policy", "retention"))
        self.assertEqual(replayed.exception.message, first.exception.message)
        self.assertTrue(replayed.exception.durable)
        self.assertEqual(len(attempts), 1)

    def test_the_re_read_inside_the_lock_is_what_decides(self):
        """The optimistic peek answers; the re-read DECIDES.

        Two managers can pass the peek concurrently, and a read-then-write check
        outside the transaction would let both through. The process race below
        exercises this too, but only when the timing happens to land inside the
        window -- so this case OPENS the window on purpose by having a competing
        writer commit between the peek and the lock.
        """
        store = self.store()
        signature = self.signature()
        competitor = sqlite3.connect(self.path, isolation_level=None)
        self.addCleanup(competitor.close)
        peeks = []
        original = store.replay

        def racing_replay(operation_id, sig, *, kind=None):
            answer = original(operation_id, sig, kind=kind)
            if not peeks:
                peeks.append("peeked")
                # The other manager wins the race, right here.
                competitor.execute(
                    "INSERT INTO operations (operation_id, kind, signature, "
                    "state, result, settled_at) VALUES (?, ?, ?, ?, ?, ?)",
                    ("op-1", "offer.issue", sig, "committed",
                     json.dumps({"by": "the other manager"}), NOW))
            return answer

        store.replay = racing_replay
        ran = []
        answer = store.transact("op-1", "offer.issue", signature,
                                lambda connection: ran.append("ran"))
        # The winner's answer, and OUR action never ran.
        self.assertEqual(answer, {"by": "the other manager"})
        self.assertEqual(ran, [])

    def test_a_fault_takes_the_transaction_down_and_records_nothing(self):
        # An operation whose failure we cannot describe is not one we may record
        # an outcome for.
        store = self.store()

        def action(connection):
            connection.execute(
                # A COMPLETE row: the journal's invariant forbids a committed
                # row with no result, and my first fixtures wrote exactly that.
                # The invariant caught my own tests, which is the argument for
                # putting it in the schema rather than in the writer.
                "INSERT INTO operations (operation_id, kind, signature, state, "
                "result, settled_at) "
                "VALUES ('side-effect', 'k', 's', 'committed', 'null', ?)",
                (NOW,))
            raise ZeroDivisionError("a defect, not a refusal")

        with self.assertRaises(ZeroDivisionError):
            store.transact("op-1", "offer.issue", self.signature(), action)
        self.assertIsNone(store.operation_record("side-effect"))
        self.assertIsNone(store.operation_record("op-1"))

    def test_the_journalled_result_is_owned_and_byte_stable(self):
        store = self.store()
        signature = self.signature()
        source = {"b": 1, "a": [1, {"c": "d"}]}
        first = store.transact("op-1", "offer.issue", signature,
                               lambda connection: source)
        # Owned: the caller's object is not the answer, and editing it after the
        # fact changes neither the answer nor the record.
        self.assertIsNot(first, source)
        source["a"].append("tampered")
        again = store.transact("op-1", "offer.issue", signature,
                               lambda connection: {"unused": True})
        self.assertEqual(again, {"b": 1, "a": [1, {"c": "d"}]})
        self.assertEqual(json.loads(store.operation_record("op-1")["result"]),
                         again)

    def test_a_result_that_is_not_ownable_takes_the_transaction_with_it(self):
        # A committed mutation whose journal row was rejected would be the
        # effectively-once mechanism's worst state: done, unrecorded, and
        # repeatable. So the ownership check runs INSIDE the transaction.
        store = self.store()

        def action(connection):
            connection.execute(
                # A COMPLETE row: the journal's invariant forbids a committed
                # row with no result, and my first fixtures wrote exactly that.
                # The invariant caught my own tests, which is the argument for
                # putting it in the schema rather than in the writer.
                "INSERT INTO operations (operation_id, kind, signature, state, "
                "result, settled_at) "
                "VALUES ('side-effect', 'k', 's', 'committed', 'null', ?)",
                (NOW,))
            return {"handle": object()}

        with self.assertRaises(ContractRefusal):
            store.transact("op-1", "offer.issue", self.signature(), action)
        self.assertIsNone(store.operation_record("side-effect"))
        self.assertIsNone(store.operation_record("op-1"))

    def test_the_record_is_a_fresh_document_and_not_a_live_row(self):
        store = self.store()
        store.transact("op-1", "offer.issue", self.signature(),
                       lambda connection: {"issued": True})
        record = store.operation_record("op-1")
        record["state"] = "tampered"
        self.assertEqual(store.operation_record("op-1")["state"], "committed")

    def test_the_settled_instant_comes_from_the_injected_clock(self):
        instants = iter(["2026-08-24T00:00:01.000Z", "2026-08-24T00:00:02.000Z"])
        store = self.store(clock=lambda: next(instants))
        store.transact("op-1", "offer.issue", self.signature(),
                       lambda connection: None)
        self.assertEqual(store.operation_record("op-1")["settled_at"],
                         "2026-08-24T00:00:02.000Z")


class ASealedRefusalReproducesTheFirstAnswer(StoreCase):

    def test_public_sealing_owns_the_refusal_before_reading_it(self):
        """Removing an unreachable message check must not unown its operand."""
        ran = []

        class Hostile:
            def __getattribute__(self, name):
                ran.append(name)
                raise AssertionError("a rejected object ran")

        with self.assertRaises(ContractRefusal) as caught:
            seal_refusal(Hostile())
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertEqual(ran, [])

    def test_public_revival_owns_every_field_of_the_seal(self):
        for what, record in [
                ("category type",
                 {"category": [], "code": "retention", "message": "held",
                  "durable": True}),
                ("closed pairing",
                 {"category": "policy", "code": "precondition",
                  "message": "held", "durable": True}),
                ("message type",
                 {"category": "policy", "code": "retention", "message": 7,
                  "durable": True}),
                ("durable marker",
                 {"category": "policy", "code": "retention",
                  "message": "held", "durable": False})]:
            with self.subTest(what=what):
                with self.assertRaises(ContractRefusal) as caught:
                    revive_refusal(json.dumps(record))
                self.assertEqual((caught.exception.category,
                                  caught.exception.code),
                                 ("integrity", "schema"))

    def test_replay_does_not_readopt_a_refusal_owned_at_the_row(self):
        store = self.store()
        signature = self.signature()

        def refused(connection):
            raise ContractRefusal("policy", "retention", "held", durable=True)

        with self.assertRaises(ContractRefusal):
            store.transact("op-1", "offer.issue", signature, refused)
        with mock.patch(
                "baton_v12.worker_manager.store.boundaries.adopted",
                side_effect=AssertionError("the row was adopted twice")):
            with self.assertRaises(ContractRefusal) as caught:
                store.replay("op-1", signature, kind="offer.issue")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "retention"))

    def test_an_adopted_committed_result_is_owned_before_replay(self):
        store = self.store()
        signature = self.signature()
        store.transact("op-1", "offer.issue", signature,
                       lambda connection: {"answer": True})
        store._connection.execute(
            "UPDATE operations SET result = 'not-json' WHERE operation_id = 'op-1'")
        with self.assertRaises(ContractRefusal):
            store.replay("op-1", signature, kind="offer.issue")

    def test_an_adopted_refusal_is_owned_before_revival(self):
        store = self.store()
        signature = self.signature()

        def refused(connection):
            raise ContractRefusal("policy", "retention", "held", durable=True)

        with self.assertRaises(ContractRefusal):
            store.transact("op-1", "offer.issue", signature, refused)
        store._connection.execute(
            "UPDATE operations SET refusal = '{}' WHERE operation_id = 'op-1'")
        with self.assertRaises(ContractRefusal):
            store.replay("op-1", signature, kind="offer.issue")

    def test_an_adopted_refusals_members_are_owned_before_revival(self):
        store = self.store()
        signature = self.signature()

        def refused(connection):
            raise ContractRefusal("policy", "retention", "held", durable=True)

        with self.assertRaises(ContractRefusal):
            store.transact("op-1", "offer.issue", signature, refused)
        store._connection.execute(
            "UPDATE operations SET refusal = ? WHERE operation_id = 'op-1'",
            (json.dumps({"category": 7, "code": "retention",
                         "message": "held", "durable": True}),))
        with self.assertRaises(ContractRefusal) as caught:
            store.replay("op-1", signature, kind="offer.issue")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_an_adopted_refusal_types_its_category_before_pairing_it(self):
        store = self.store()
        signature = self.signature()

        def refused(connection):
            raise ContractRefusal("policy", "retention", "held", durable=True)

        with self.assertRaises(ContractRefusal):
            store.transact("op-1", "offer.issue", signature, refused)
        store._connection.execute(
            "UPDATE operations SET refusal = ? WHERE operation_id = 'op-1'",
            (json.dumps({"category": [], "code": "retention",
                         "message": "held", "durable": True}),))
        with self.assertRaises(ContractRefusal) as caught:
            store.replay("op-1", signature, kind="offer.issue")
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_a_caller_cannot_open_the_pairing_used_to_adopt_a_refusal(self):
        store = self.store()
        signature = self.signature()

        def refused(connection):
            raise ContractRefusal("policy", "retention", "held", durable=True)

        with self.assertRaises(ContractRefusal):
            store.transact("op-1", "offer.issue", signature, refused)
        store._connection.execute(
            "UPDATE operations SET refusal = ? WHERE operation_id = 'op-1'",
            (json.dumps({"category": "policy", "code": "caller-invented",
                         "message": "held", "durable": True}),))
        original = ERROR_CODES["policy"]
        try:
            ERROR_CODES["policy"] = original + ("caller-invented",)
            with self.assertRaises(ContractRefusal) as caught:
                store.replay("op-1", signature, kind="offer.issue")
            self.assertEqual((caught.exception.category,
                              caught.exception.code),
                             ("integrity", "schema"))
        finally:
            ERROR_CODES["policy"] = original

    def test_the_whole_closed_pair_survives_the_round_trip(self):
        for category, code in [("policy", "retention"),
                               ("refused", "precondition"),
                               ("integrity", "digest")]:
            with self.subTest(pair=f"{category}/{code}"):
                original = ContractRefusal(category, code, "why", durable=True)
                revived = revive_refusal(seal_refusal(original))
                self.assertEqual((revived.category, revived.code, revived.message),
                                 (category, code, "why"))
                self.assertTrue(revived.durable)


class WhatSurvivesARestart(StoreCase):

    def test_the_journal_survives_and_replays_after_a_reopen(self):
        signature = self.signature()
        first = self.store()
        answer = first.transact("op-1", "offer.issue", signature,
                                lambda connection: {"issued": True})
        first.close()
        again = self.store()
        ran = []
        self.assertEqual(
            again.transact("op-1", "offer.issue", signature,
                           lambda connection: ran.append("ran")),
            answer)
        self.assertEqual(ran, [])

    def test_a_durable_refusal_replays_after_a_reopen(self):
        signature = self.signature()
        first = self.store()
        with self.assertRaises(ContractRefusal):
            first.transact("op-1", "offer.issue", signature,
                           lambda connection: (_ for _ in ()).throw(
                               ContractRefusal("policy", "retention", "held",
                                               durable=True)))
        first.close()
        again = self.store()
        with self.assertRaises(ContractRefusal) as caught:
            again.transact("op-1", "offer.issue", signature,
                           lambda connection: {"never": True})
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("policy", "retention"))

    def test_a_projection_read_after_restart_is_fresh_data(self):
        first = self.store()
        first.transact("op-1", "offer.issue", self.signature(),
                       lambda connection: {"issued": True})
        first.close()
        again = self.store()
        record = again.operation_record("op-1")
        record["result"] = "tampered"
        self.assertNotEqual(again.operation_record("op-1")["result"], "tampered")


CHILD = textwrap.dedent("""
    import json, sys
    sys.path[:0] = json.loads(sys.argv[4])
    from baton_v12.contracts import ContractRefusal
    from baton_v12.worker_manager import ControlStore, manager_signature

    path, operation_id, barrier = sys.argv[1], sys.argv[2], sys.argv[3]
    store = ControlStore.open(path, incarnation="child",
                              clock=lambda: "2026-08-24T00:00:00.000Z")
    signature = manager_signature("offer.issue", {"work_id": "0000000a-W1"})
    # A REAL barrier: every child waits for the file to appear, so they contend
    # for the write lock rather than politely queueing behind each other's
    # start-up.
    import os, time
    while not os.path.exists(barrier):
        time.sleep(0.001)
    try:
        answer = store.transact(operation_id, "offer.issue", signature,
                                lambda connection: {"by": os.getpid()})
        print(json.dumps({"outcome": "committed", "answer": answer,
                          "me": os.getpid()}))
    except ContractRefusal as refusal:
        print(json.dumps({"outcome": "refused", "code": refusal.code,
                          "me": os.getpid()}))
    finally:
        store.close()
""")


class RealProcessRaces(StoreCase):
    """Threads share a connection; processes do not.

    The one-writer rule has to be decided by a refusal INSIDE a transaction, and
    the only way to know a `BEGIN IMMEDIATE` really serializes two managers is to
    have two managers.
    """

    def children(self, count, operation_id="op-race"):
        self.store().close()
        barrier = os.path.join(self.root, "go")
        path = json.dumps([p for p in sys.path if p])
        running = [subprocess.Popen(
            [sys.executable, "-c", CHILD, self.path, operation_id, barrier,
             path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            for _ in range(count)]
        with open(barrier, "wb") as handle:
            handle.write(b"go")
        answers = []
        for child in running:
            out, err = child.communicate(timeout=60)
            self.assertEqual(child.returncode, 0, err)
            answers.append(json.loads(out.strip().split("\n")[-1]))
        return answers

    def test_one_fixed_operation_id_across_processes_commits_once(self):
        answers = self.children(4)
        committed = [a for a in answers if a["outcome"] == "committed"]
        self.assertEqual(len(committed), 4, answers)
        # THE RACE ACTUALLY HAPPENED. Every child replays the same answer, so
        # the answers alone cannot say whether four processes contended or one
        # ran four times -- each reports its own pid so the case can tell. A
        # race case that cannot prove it raced is a case that passes for the
        # wrong reason.
        self.assertEqual(len({a["me"] for a in answers}), 4, answers)
        self.assertNotIn(os.getpid(), {a["me"] for a in answers})
        # Every one of them answers with the SAME committed result -- the first
        # writer's, replayed -- rather than each performing the act.
        self.assertEqual({json.dumps(a["answer"], sort_keys=True)
                          for a in committed}, {json.dumps(
                              committed[0]["answer"], sort_keys=True)})
        store = self.store()
        self.assertEqual(store.operation_record("op-race")["state"], "committed")
        rows = store._connection.execute(
            "SELECT COUNT(*) FROM operations").fetchone()[0]
        self.assertEqual(rows, 1)


if __name__ == "__main__":
    unittest.main()
