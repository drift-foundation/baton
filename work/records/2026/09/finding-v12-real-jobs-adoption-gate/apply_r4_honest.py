"""R4: make the admission case prove what it claims, on the gate itself."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

NEW = '''    def test_four_admissions_are_spent_and_a_fifth_is_refused(self):
        """Two implementations and two reviews, taken ON THE GATE.

        The first version of this case ran the fixture traversal -- which
        goes through the COMPOSED operations, not through this gate -- and
        then SET `gate.admissions` by hand before asserting the fifth was
        refused. That would have been asserting an assignment. The four
        admitting acts are taken on the gate here, so the counts are its own.
        """
        from baton_v12.contracts import ContractRefusal
        job, _control, _composed = self.gated()
        for kind in ("implementation", "review"):
            for job_id in ("job-a", "job-b"):
                with self.subTest(kind=kind, job=job_id):
                    self.gate.admit({"kind": kind, "job_id": job_id,
                                     "stage_id": f"{job_id}/{kind}"}, job)
        self.assertEqual(self.gate.admissions,
                         {"implementation": 2, "review": 2})
        self.assertEqual(self.gate.refusals, [])
        # AND THE FIFTH OF EITHER KIND IS REFUSED, whichever Job asks.
        for kind in ("implementation", "review"):
            with self.subTest(kind=kind), self.assertRaises(ContractRefusal):
                self.gate.admit({"kind": kind, "job_id": "job-a",
                                 "stage_id": f"job-a/{kind}-again"}, job)
        self.assertEqual(len(self.gate.refusals), 2)
        self.assertEqual(self.gate.admissions,
                         {"implementation": 2, "review": 2})

    def test_a_stopped_gate_admits_nothing_further(self):
        """What a bounded stop rests on, asserted rather than assumed."""
        from baton_v12.contracts import ContractRefusal
        job, _control, _composed = self.gated()
        self.gate.admit({"kind": "implementation", "job_id": "job-a",
                         "stage_id": "job-a/implementation"}, job)
        self.gate.stopped = True
        with self.assertRaises(ContractRefusal):
            self.gate.admit({"kind": "review", "job_id": "job-b",
                             "stage_id": "job-b/review"}, job)
        self.assertEqual(self.gate.admissions,
                         {"implementation": 1, "review": 0})
'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    start = body.index(
        "    def test_four_admissions_are_spent_and_a_fifth_is_refused(self):")
    end = body.index(
        "    def test_a_stage_of_neither_job_is_foreign_rather_than_a_cap")
    body = body[:start] + NEW + "\n" + body[end:]
    place.write_text(body, encoding="utf-8")
    print("admission case rewritten to drive the gate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
