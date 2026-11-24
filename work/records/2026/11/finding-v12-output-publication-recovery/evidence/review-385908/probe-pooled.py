import json, os, pathlib, sys, unittest
sys.path[:0] = [str(pathlib.Path.cwd()), str(pathlib.Path.cwd()/"src")]
from tests.tools.test_stage_execution import ComposedOneJobCase as _Base
from tests.job_manager import fixtures
from baton_v12.job_manager import JobStore, submit, sweep, publication_recovery, documents, episodes
from tools import bootstrap, stage_execution

OWNER = "baton.owner"

class Explore(_Base):
    from tests.tools.test_bootstrap import ValidFixture as _B
    stage_worker = _B.stage_worker
    workers = _B.workers
    job = _B.job

    def setUp(self):
        self.now = fixtures.NOW
        super().setUp()
        self.state = os.path.join(self.root, "publication-instance")
        self.places = bootstrap.layout(self.state)
        bootstrap.persist_identity(self.places, self.config["authority_uuid"])
        self.install_document = self._B.document(self, owner_participant=OWNER,
            jobs=[self.job(work_id=self.work, base=self.base)])
        with open(os.devnull, "w") as quiet:
            self.installed = bootstrap.prepare(self.install_document, stream=quiet)
        pathlib.Path(self.places["install_inputs"]).write_text(json.dumps(self.install_document))
        self.authority_path = self.places["authority_store"]
        self.config["authority_store"] = self.authority_path

    def stores(self, incarnation):
        from baton_v12.worker_manager import ControlStore
        jobs = JobStore.open(self.places["job_store"], authority_uuid=self.config["authority_uuid"], incarnation=incarnation, clock=lambda: self.now)
        control = ControlStore.open(self.places["control_store"], incarnation=incarnation, clock=lambda: self.now)
        self.addCleanup(jobs.close); self.addCleanup(control.close)
        return jobs, control

    def composed_document(self, **members):
        return json.loads(pathlib.Path(self.places["configuration"]).read_text())

    def test_overflow(self):
        from baton_v12.worker_manager import frozen_output_of, attempt_runtime_of
        jobs, control, operations = self.serving()
        submit(jobs, self.submission)
        self.drive(jobs, operations, "implementation", "waiting")
        attempt = self.only_attempt(operations, "implementation")
        rc = self.turn(control, "implementation", attempt, self.mounted(operations, "implementation", attempt),
                       edits={"big.txt": "x" * (1048576 + 4096)})
        print("TURN rc", rc)
        for i in range(12):
            r = sweep(jobs, operations, now=self.now)
        print("STATES", self.states(jobs, operations))
        print("FROZEN", frozen_output_of(control, attempt))
        print("RUNTIME", attempt_runtime_of(control, attempt))
        from baton_v12.authority import Authority
        print("ASSIGN", operations.authority.assignment_of(self.work))
        roots = self.mounted(operations, "implementation", attempt)
        print("WS", sorted(os.listdir(roots["workspace"])))
        for name in os.listdir(roots["workspace"]):
            p = os.path.join(roots["workspace"], name)
            if os.path.isdir(p): print(" ", name, sorted(os.listdir(p))[:10])
        self.engine.stopped = True
        for i in range(6):
            r = sweep(jobs, operations, now=self.now)
        print("STATES2", self.states(jobs, operations))
        print("RUNTIME2", attempt_runtime_of(control, attempt))
        stage = episodes.attempting(next(row for row in __import__('baton_v12.job_manager.submission', fromlist=['stages_of']).stages_of(jobs, 'job-a') if row['stage_id'] == 'job-a/implementation'), episodes.episode_of(jobs, 'job-a/implementation', 1))
        settled = operations.abandon_attempt(attempt_id=attempt, reason='review deterministic failed publication settlement', stage=stage)
        print('SUPPORTED_SETTLEMENT', json.dumps(settled, default=str))
        print('RUNTIME_AFTER_SETTLEMENT', json.dumps(attempt_runtime_of(control, attempt)))
        self.assertIn(attempt_runtime_of(control, attempt)['cleanup'], ('retained', 'complete'))
        import io
        from tools import job_manager
        argv = ["publication-inspect", "--store", self.places["job_store"], "--authority-uuid", self.config["authority_uuid"],
                "--incarnation", "stage-composed", "--control", self.places["control_store"], "--authority", self.places["authority_store"],
                "--instance", self.state, "--job", "job-a", "--stage", "job-a/implementation", "--episode", "1", "--participant", OWNER]
        said = io.StringIO()
        code = job_manager.main(argv, clock=lambda: self.now, stream=said)
        print("INSPECT", code)
        read = json.loads(said.getvalue()) if said.getvalue().strip() else None
        self.assertFalse(read["eligible"])
        self.assertTrue(any("layout" in h["message"] for h in read["holds"]), read)
        if read:
            print("ELIGIBLE", read.get("eligible"))
            for one in read.get("holds", []): print("HOLD", one["category"], one["code"], one["message"][:300])

if __name__ == "__main__":
    unittest.main(verbosity=2)
