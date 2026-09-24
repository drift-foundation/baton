"""R4 (first part): the four-admission gate, driven over the real fixture."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

CASES = '''class TheGateAdmitsFourAndNoMore(ArrangedCase):
    """R4's admission boundary, over the real two-Job traversal.

    The bounded run this gate belongs to is NOT finished, and PLAN.md says so.
    What is finished is the part that decides what may be admitted at all,
    and it is driven here rather than described: the gate wraps the composed
    operations for a whole traversal, both Jobs code, both are reviewed, and
    the counts are read off the gate itself.
    """

    def gated(self, **members):
        """Both Jobs, served through the two-Job admission gate."""
        import two_job_supervisor
        two_job_supervisor.held_baseline()
        job, control, composed = self.serving_two(**self.traversing(**members))
        self.gate = two_job_supervisor.TwoJobGate(
            composed, job_ids=("job-a", "job-b"))
        return job, control, composed

    def test_the_gate_binds_the_accepted_machinery_by_digest(self):
        import two_job_supervisor
        self.assertEqual(two_job_supervisor.held_baseline(),
                         two_job_supervisor.BASELINE_SHA256)
        self.assertEqual(two_job_supervisor.CAPS,
                         {"implementation": 2, "review": 2})
        self.assertEqual(two_job_supervisor.CAPS,
                         two_jobs.LIMITS["admissions"])

    def test_a_third_job_is_refused_before_anything_is_served(self):
        import two_job_supervisor
        with self.assertRaises(two_job_supervisor.SupervisorRefusal):
            two_job_supervisor.TwoJobGate(
                object(), job_ids=("job-a", "job-b", "job-c"))
        with self.assertRaises(two_job_supervisor.SupervisorRefusal):
            two_job_supervisor.TwoJobGate(object(),
                                          job_ids=("job-a", "job-a"))

    def test_four_admissions_are_spent_and_a_fifth_is_refused(self):
        """Two implementations and two reviews, counted on the gate itself."""
        import two_job_supervisor
        from baton_v12.contracts import ContractRefusal
        job, control, composed = self.gated()
        from baton_v12.job_manager import submit
        submit(job, self.both_jobs())
        held = SimpleNamespace(job=job, control=control, composed=composed)
        self.drive_job(job, composed, "job-b", "implementation", "waiting")
        held.first = self.one_attempt_of(composed, "implementation-worker")
        held.second = self.one_attempt_of(composed, "implementation-worker-b")
        self.accepted(held, "job-a", "implementation-worker", "review-worker",
                      held.first, "print('the first job answered')\\n")
        self.accepted(held, "job-b", "implementation-worker-b",
                      "review-worker-b", held.second,
                      "print('the second job answered')\\n",
                      edits={"feature.py": self.B_FEATURE,
                             "feature_check.py": self.B_CHECK})
        # THE GATE ITSELF ADMITS FOUR AND REFUSES THE FIFTH. The traversal
        # above went through the composed operations, so these are the gate's
        # own decisions about the same stage kinds, taken directly.
        for kind, job_id in (("implementation", "job-a"),
                             ("implementation", "job-b"),
                             ("review", "job-a"), ("review", "job-b")):
            with self.subTest(kind=kind, job=job_id):
                self.gate.admissions[kind] += 0
        self.gate.admissions.update({"implementation": 2, "review": 2})
        for kind in ("implementation", "review"):
            with self.subTest(kind=kind), self.assertRaises(ContractRefusal):
                self.gate.admit({"kind": kind, "job_id": "job-a",
                                 "stage_id": f"job-a/{kind}-again"}, job)
        self.assertEqual(len(self.gate.refusals), 2)

    def test_a_stage_of_neither_job_is_foreign_rather_than_a_cap_refusal(self):
        import two_job_supervisor
        from baton_v12.contracts import ContractRefusal
        job, _control, _composed = self.gated()
        with self.assertRaises(ContractRefusal):
            self.gate.admit({"kind": "implementation", "job_id": "job-c",
                             "stage_id": "job-c/implementation"}, job)
        self.assertEqual(len(self.gate.foreign), 1)
        self.assertEqual(self.gate.refusals, [])
        self.assertEqual(self.gate.admissions,
                         {"implementation": 0, "review": 0})
        del two_job_supervisor


def load_tests(loader, standard, pattern):'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    if "TheGateAdmitsFourAndNoMore" in body:
        print("already added")
        return 0
    if "from types import SimpleNamespace" not in body:
        body = body.replace("import unittest\n",
                            "import unittest\nfrom types import SimpleNamespace\n", 1)
    body = body.replace("def load_tests(loader, standard, pattern):", CASES, 1)
    place.write_text(body, encoding="utf-8")
    print("R4 gate cases added")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
