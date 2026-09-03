"""W71875 — recording a submission: atomic, idempotent, and refusing conflict.

THE WHOLE SUBMISSION IS ONE ACT. Two Jobs and three stages either all exist
afterwards or none does, because a half-recorded pipeline is one nobody
described and nothing can reconcile.

IDEMPOTENCE AND CONFLICT ARE ONE MECHANISM SEEN FROM TWO SIDES: the same
intent replays, and the same identity carrying a different intent refuses.
"""

import json
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (episodes_of, job_rows, jobs_of, live_of,
                                   stage_rows, stages_of, submission_of,
                                   submission_rows, submit)

if __package__:
    from .fixtures import (NOW, WORK_A, WORK_B, JobManagerCase, job,
                           submission)
else:
    from fixtures import (NOW, WORK_A, WORK_B, JobManagerCase, job,
                          submission)


class Recording(JobManagerCase):

    def test_one_submission_records_two_jobs_and_their_stages(self):
        store = self.store()
        recorded = submit(store, submission())
        self.assertEqual(recorded["submission_id"], "sub-1")
        self.assertEqual(recorded["jobs"], ["job-a", "job-b"])
        self.assertEqual(recorded["stages"],
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])
        self.assertEqual(recorded["recorded_at"], NOW)
        self.assertEqual([row["job_id"] for row in job_rows(store)],
                         ["job-a", "job-b"])
        self.assertEqual([row["stage_id"] for row in stage_rows(store)],
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])

    def test_the_stage_row_carries_the_submitted_intent_and_nothing_else(self):
        store = self.store()
        submit(store, submission())
        first = stages_of(store, "job-a")[0]
        self.assertEqual(first["kind"], "implementation")
        self.assertEqual(first["work_id"], WORK_A)
        self.assertEqual(first["profile_name"], "reference")
        self.assertEqual(json.loads(first["depends_on"]), [])
        # AND THE STAGE ROW CARRIES NO OFFER OR ATTEMPT. W73629 moved those
        # onto the episode, because a stage outlives the offer that was trying
        # to admit it and a copy on the stage would be a second account of
        # whichever episode is current.
        self.assertNotIn("offer_id", dict(first))
        self.assertNotIn("attempt_id", dict(first))

    def test_the_submission_opens_the_stages_first_episode(self):
        """One act: a stage with no episode is one nothing could admit.

        The identities are still DERIVED, and episode 1's are still the
        spelling a schema-1 store wrote, so a migrated store's canonical
        operation ids are the ones its receipts already name.
        """
        store = self.store()
        submit(store, submission())
        held = episodes_of(store, "job-a/implementation")
        self.assertEqual(len(held), 1)
        self.assertEqual(held[0]["episode"], 1)
        self.assertEqual(held[0]["offer_id"], "offer:job-a/implementation")
        self.assertEqual(held[0]["attempt_id"],
                         "attempt:job-a/implementation")
        self.assertIsNone(held[0]["ended_state"])
        self.assertEqual(live_of(store, "job-a/implementation")["episode"], 1)

    def test_the_review_stage_records_its_gate(self):
        store = self.store()
        submit(store, submission())
        review = stages_of(store, "job-a")[1]
        self.assertEqual(json.loads(review["depends_on"]),
                         [{"job_id": "job-a", "kind": "implementation"}])
        self.assertEqual(review["work_id"], WORK_B)

    def test_the_job_row_carries_the_immutable_input_identity(self):
        store = self.store()
        submit(store, submission())
        first = jobs_of(store, "sub-1")[0]
        self.assertEqual(first["input_digest"], "sha256:" + "1" * 64)
        self.assertEqual(first["policy_digest"], "sha256:" + "2" * 64)
        self.assertEqual(json.loads(first["test_scope"]),
                         ["v12/python/tests/job_manager"])
        self.assertEqual(first["terminal_policy"], "report-and-hold")

    def test_the_submitted_document_is_stored_normalized(self):
        store = self.store()
        submit(store, submission())
        row = submission_of(store, "sub-1")
        self.assertEqual(json.loads(row["document"])["schema"],
                         "baton.v12.job-submission/1")
        self.assertEqual(row["incarnation"], "jobs-1")

    def test_submission_rows_reads_every_submission(self):
        store = self.store()
        submit(store, submission("sub-1"))
        submit(store, submission("sub-2", jobs=[job("job-c")]))
        self.assertEqual([row["submission_id"]
                          for row in submission_rows(store)],
                         ["sub-1", "sub-2"])


class Idempotence(JobManagerCase):

    def test_resubmitting_the_same_intent_replays_the_first_outcome(self):
        store = self.store()
        first = submit(store, submission())
        self.instants.append("2026-09-02T00:01:00.000Z")
        second = submit(store, submission())
        self.assertEqual(first, second)
        self.assertEqual(second["recorded_at"], NOW)
        self.assertEqual(len(job_rows(store)), 2)

    def test_a_differently_spelled_document_is_the_same_submission(self):
        store = self.store()
        first = submit(store, submission())
        other = submission()
        other = {"jobs": other["jobs"], "schema": other["schema"],
                 "submission_id": other["submission_id"]}
        self.assertEqual(submit(store, other), first)

    def test_reusing_a_submission_id_for_another_intent_collides(self):
        store = self.store()
        submit(store, submission())
        changed = submission()
        changed["jobs"][0]["input_digest"] = "sha256:" + "9" * 64
        with self.assertRaises(ContractRefusal) as caught:
            submit(store, changed)
        self.assertEqual(caught.exception.code, "operation-collision")
        # AND NOTHING MOVED. A conflicting resubmission must not rewrite the
        # durable rows the running pipeline is derived from.
        self.assertEqual(jobs_of(store, "sub-1")[0]["input_digest"],
                         "sha256:" + "1" * 64)

    def test_a_job_identity_already_recorded_refuses_durably(self):
        store = self.store()
        submit(store, submission())
        with self.assertRaises(ContractRefusal) as caught:
            submit(store, submission("sub-2", jobs=[job("job-a")]))
        self.assertEqual((caught.exception.category, caught.exception.code),
                         ("refused", "precondition"))
        self.assertTrue(caught.exception.durable)
        # Sealed, so the resubmission is told the SAME thing every time rather
        # than something new once the store has moved on.
        with self.assertRaises(ContractRefusal) as again:
            submit(store, submission("sub-2", jobs=[job("job-a")]))
        self.assertEqual(again.exception.message, caught.exception.message)

    def test_a_refused_submission_records_none_of_its_jobs(self):
        store = self.store()
        submit(store, submission("sub-1", jobs=[job("job-a")]))
        with self.assertRaises(ContractRefusal):
            submit(store, submission("sub-2", jobs=[job("job-b"),
                                                    job("job-a")]))
        # The whole submission is one act: `job-b` came first in the document
        # and must not survive the refusal of the Job after it.
        self.assertEqual([row["job_id"] for row in job_rows(store)],
                         ["job-a"])
        self.assertEqual([row["submission_id"]
                          for row in submission_rows(store)], ["sub-1"])

    def test_an_invalid_submission_is_refused_before_the_store_is_touched(self):
        store = self.store()
        with self.assertRaises(ContractRefusal):
            submit(store, submission(jobs=[job(terminal_policy="auto")]))
        self.assertEqual(submission_rows(store), [])
        self.assertIsNone(store.operation_record("submission.record:sub-1"))


class Persistence(JobManagerCase):

    def test_a_second_incarnation_reads_the_same_submission(self):
        first = self.store()
        submit(first, submission())
        first.close()
        second = self.store(incarnation="jobs-2")
        self.assertEqual([row["stage_id"] for row in stage_rows(second)],
                         ["job-a/implementation", "job-a/review",
                          "job-b/implementation"])
        # AND RESUBMITTING FROM THE NEW INCARNATION STILL REPLAYS. The
        # identity is the submitted intent, not the process that recorded it.
        self.assertEqual(submit(second, submission())["recorded_at"], NOW)

    def test_a_stage_row_whose_persisted_json_no_longer_decodes_refuses(self):
        store = self.store()
        submit(store, submission())
        store._connection.execute(
            "UPDATE stages SET depends_on = 'not json' "
            "WHERE stage_id = 'job-a/review'")
        with self.assertRaises(ContractRefusal):
            stage_rows(store)

    def test_the_stage_table_refuses_two_stages_of_one_kind(self):
        # The submission boundary refuses it first; this proves the TABLE does
        # too, so a second writer cannot reach past the document rule.
        store = self.store()
        submit(store, submission())
        with self.assertRaises(sqlite3.IntegrityError):
            store._connection.execute(
                "INSERT INTO stages (stage_id, job_id, ordinal, kind, "
                "work_id, profile_name, profile_digest, depends_on) "
                "VALUES ('other', 'job-a', 9, 'implementation', "
                "'w', 'p', 'd', '[]')")


if __name__ == "__main__":
    unittest.main()
