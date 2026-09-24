"""R4: drive the gate's own rules over a recorder, not the real deployment."""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

NEW = '''    def gated(self, **members):
        """The gate, wrapping a RECORDER rather than the composed operations.

        The gate is a proxy over the three admitting acts, so what these
        cases measure is its decisions. Handing it the real composed
        operations and synthetic stage documents would reach the deployment
        and fail on the operands a real stage carries -- which says nothing
        about the rule under test. The real traversal is measured separately,
        by the cases above, through the composed operations themselves.
        """
        import two_job_supervisor
        two_job_supervisor.held_baseline()

        class Recorder:
            def __init__(self):
                self.admitted = []

            def admit(self, stage, job):
                self.admitted.append((stage.get("job_id"), stage.get("kind")))
                return {"stage_id": stage.get("stage_id")}

            def claim(self, stage):
                return stage

            def launch(self, attempt, job):
                return attempt

        self.recorder = Recorder()
        self.gate = two_job_supervisor.TwoJobGate(
            self.recorder, job_ids=("job-a", "job-b"))
        return self.recorder
'''


def main():
    place = HERE / "test_two_jobs.py"
    body = place.read_text(encoding="utf-8")
    start = body.index("    def gated(self, **members):")
    end = body.index("    def test_the_gate_binds_the_accepted_machinery")
    body = body[:start] + NEW + "\n" + body[end:]
    body = body.replace(
        "        job, _control, _composed = self.gated()",
        "        held = self.gated()\n        job = None")
    body = body.replace(
        '''        self.assertEqual(len(self.gate.foreign), 1)''',
        '''        self.assertEqual(len(self.gate.foreign), 1)
        self.assertEqual(held.admitted, [])''')
    body = body.replace(
        '''        self.assertEqual(self.gate.admissions,
                         {"implementation": 2, "review": 2})
        self.assertEqual(self.gate.refusals, [])''',
        '''        self.assertEqual(self.gate.admissions,
                         {"implementation": 2, "review": 2})
        self.assertEqual(self.gate.refusals, [])
        self.assertEqual(sorted(held.admitted),
                         [("job-a", "implementation"), ("job-a", "review"),
                          ("job-b", "implementation"), ("job-b", "review")])''')
    place.write_text(body, encoding="utf-8")
    print("gate cases now drive a recorder")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
