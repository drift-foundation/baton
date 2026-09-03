"""W71875 — the Job store: ownership, one atomic boundary, byte-stable replay.

The mechanism is the Worker Manager control store's and the obligations are
the same ones, held against THIS store: a database that is not ours is refused
without a byte changed, an operation identity carries one kind and one
signature, a durable refusal replays as itself, and presence is its own fact.

The case that matters most for this leaf is the last one in `Ownership`: the
Job store and the manager's control store sit side by side in one deployment,
and each must refuse the other.
"""

import os
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (SCHEMA_VERSION, STORE_KIND, JobStore,
                                   job_signature)
from baton_v12.worker_manager import ControlStore

if __package__:
    from .fixtures import NOW, JobManagerCase
else:
    from fixtures import NOW, JobManagerCase


class Ownership(JobManagerCase):

    def test_an_empty_database_becomes_this_manager_s_store(self):
        store = self.store()
        self.assertEqual(store.incarnation, "jobs-1")
        recorded = dict(store._connection.execute(
            "SELECT key, value FROM meta").fetchall())
        self.assertEqual(recorded["store_kind"], STORE_KIND)
        self.assertEqual(recorded["schema_version"], str(SCHEMA_VERSION))

    def test_reopening_our_own_store_adds_nothing(self):
        self.store().close()
        with open(self.job_path, "rb") as handle:
            before = handle.read()
        self.store()
        reading = sqlite3.connect(self.job_path)
        self.addCleanup(reading.close)
        objects = {row[0] for row in reading.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        self.assertEqual(objects & {"submissions", "jobs", "stages"},
                         {"submissions", "jobs", "stages"})
        self.assertTrue(before)

    def test_the_worker_manager_s_control_store_is_refused_untouched(self):
        # THE TWO STORES SIT SIDE BY SIDE IN ONE DEPLOYMENT and an operator
        # who swaps two paths gets a refusal rather than a scheduler writing
        # into the manager's database. "It is a v12 store" is not ownership.
        control = ControlStore.open(self.control_path, incarnation="manager-1",
                                    clock=self.clock)
        control.close()
        with open(self.control_path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(ContractRefusal) as caught:
            JobStore.open(self.control_path, incarnation="jobs-1",
                          clock=self.clock)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))
        self.assertIn("worker-manager", caught.exception.message)
        with open(self.control_path, "rb") as handle:
            self.assertEqual(handle.read(), before)

    def test_our_store_is_refused_by_the_worker_manager(self):
        self.store().close()
        with self.assertRaises(ContractRefusal) as caught:
            ControlStore.open(self.job_path, incarnation="manager-1",
                              clock=self.clock)
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("integrity", "schema"))

    def test_a_foreign_database_is_refused_without_a_byte_changed(self):
        path = os.path.join(self.root, "foreign.sqlite3")
        connection = sqlite3.connect(path, isolation_level=None)
        connection.execute("CREATE TABLE meta (id INTEGER)")
        connection.close()
        with open(path, "rb") as handle:
            before = handle.read()
        with self.assertRaises(ContractRefusal):
            JobStore.open(path, incarnation="jobs-1", clock=self.clock)
        with open(path, "rb") as handle:
            self.assertEqual(handle.read(), before)

    def test_a_store_at_another_schema_version_is_not_guessed_across(self):
        store = self.store()
        store._connection.execute(
            "UPDATE meta SET value = '99' WHERE key = 'schema_version'")
        store.close()
        with self.assertRaises(ContractRefusal) as caught:
            JobStore.open(self.job_path, incarnation="jobs-1",
                          clock=self.clock)
        self.assertIn("does not guess across versions",
                      caught.exception.message)

    def test_an_unnamed_path_is_refused_rather_than_defaulted(self):
        with self.assertRaises(ContractRefusal) as caught:
            JobStore.open("", incarnation="jobs-1", clock=self.clock)
        self.assertEqual(caught.exception.code, "path")

    def test_an_instance_names_its_incarnation(self):
        with self.assertRaises(ContractRefusal):
            JobStore.open(self.job_path, incarnation="", clock=self.clock)

    def test_a_clock_that_cannot_answer_is_found_at_open(self):
        def broken():
            return "not-an-instant"

        with self.assertRaises(ContractRefusal):
            JobStore.open(self.job_path, incarnation="jobs-1", clock=broken)


class Journal(JobManagerCase):

    def signature(self, **operands):
        return job_signature("probe", operands or {"one": 1})

    def act(self, answer):
        def perform(connection):
            self.performed.append(answer)
            return answer
        return perform

    def setUp(self):
        super().setUp()
        self.performed = []

    def test_an_exact_retry_replays_the_first_answer(self):
        store = self.store()
        signature = self.signature()
        first = store.transact("probe:1", "probe", signature,
                               self.act({"answer": 1}))
        second = store.transact("probe:1", "probe", signature,
                                self.act({"answer": 2}))
        self.assertEqual(first, {"answer": 1})
        self.assertEqual(second, {"answer": 1})
        self.assertEqual(self.performed, [{"answer": 1}])

    def test_presence_is_its_own_fact(self):
        # A committed `null` result must not read as "no row", or the retry
        # runs the action a second time and only then hits the primary key.
        store = self.store()
        signature = self.signature()
        store.transact("probe:null", "probe", signature, self.act(None))
        store.transact("probe:null", "probe", signature, self.act(None))
        self.assertEqual(len(self.performed), 1)

    def test_reusing_an_identity_with_other_operands_collides(self):
        store = self.store()
        store.transact("probe:1", "probe", self.signature(one=1),
                       self.act({"answer": 1}))
        with self.assertRaises(ContractRefusal) as caught:
            store.transact("probe:1", "probe", self.signature(one=2),
                           self.act({"answer": 2}))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_one_operation_has_one_kind(self):
        store = self.store()
        with self.assertRaises(ContractRefusal) as caught:
            store.transact("probe:1", "other", self.signature(),
                           self.act({"answer": 1}))
        self.assertEqual(caught.exception.code, "operation-collision")

    def test_a_signature_this_build_could_not_have_produced_is_refused(self):
        store = self.store()
        with self.assertRaises(ContractRefusal):
            store.transact("probe:1", "probe",
                           '{ "kind": "probe", "operands": {} }',
                           self.act({"answer": 1}))

    def test_a_durable_refusal_replays_as_itself(self):
        store = self.store()
        signature = self.signature()

        def refusing(connection):
            self.performed.append("ran")
            raise ContractRefusal("policy", "retention", "no", durable=True)

        for _ in range(2):
            with self.assertRaises(ContractRefusal) as caught:
                store.transact("probe:refused", "probe", signature, refusing)
            self.assertEqual((caught.exception.category,
                              caught.exception.code), ("policy", "retention"))
            self.assertTrue(caught.exception.durable)
        self.assertEqual(self.performed, ["ran"])

    def test_an_ordinary_refusal_leaves_the_act_retryable(self):
        store = self.store()
        signature = self.signature()
        attempts = []

        def sometimes(connection):
            attempts.append(len(attempts))
            if len(attempts) == 1:
                raise ContractRefusal("refused", "precondition", "not yet")
            return {"answer": "later"}

        with self.assertRaises(ContractRefusal):
            store.transact("probe:retry", "probe", signature, sometimes)
        self.assertEqual(store.transact("probe:retry", "probe", signature,
                                        sometimes), {"answer": "later"})

    def test_a_fault_is_not_journalled_as_an_outcome(self):
        store = self.store()

        def faulting(connection):
            raise ZeroDivisionError("a defect, not a refusal")

        with self.assertRaises(ZeroDivisionError):
            store.transact("probe:fault", "probe", self.signature(), faulting)
        self.assertIsNone(store.operation_record("probe:fault"))

    def test_the_journal_row_is_readable_as_a_fresh_document(self):
        store = self.store()
        store.transact("probe:1", "probe", self.signature(),
                       self.act({"answer": 1}))
        record = store.operation_record("probe:1")
        self.assertEqual(record["kind"], "probe")
        self.assertEqual(record["state"], "committed")
        self.assertEqual(record["settled_at"], NOW)


if __name__ == "__main__":
    unittest.main()
