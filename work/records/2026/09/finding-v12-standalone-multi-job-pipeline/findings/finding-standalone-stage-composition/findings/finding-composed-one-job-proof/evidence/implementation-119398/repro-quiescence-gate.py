"""Scratch prototype for the composed one-Job lifecycle. Not a deliverable."""
import copy
import json
import os
import subprocess
import sys
import unittest

os.chdir("/home/sl/src/baton/v12/python")
sys.path.insert(0, "/home/sl/src/baton/v12/python")
sys.path.insert(0, "/home/sl/src/baton/v12/python/src")
sys.path.insert(0, "/home/sl/src/baton/v12/worker")
sys.path.insert(0, "/home/sl/src/baton/v12/python/src/baton_v12")

from baton_v12.contracts import digest, digest_of_bytes
from baton_v12.job_manager import reconcile, status, submit, sweep
from tests.job_manager import fixtures
from tests.tools.test_stage_execution import ServingCase
from tools import single_worker, stage_execution


DECLARATIONS = (("proposal", "git-change-proposal"),
                ("findings", "directory-result"),
                ("logs", "directory-result"))


def _git(*arguments, at):
    answer = subprocess.run(["git", "-C", at] + list(arguments),
                            capture_output=True, text=True, check=True,
                            env=dict(os.environ,
                                     GIT_CONFIG_GLOBAL=os.devnull,
                                     GIT_CONFIG_SYSTEM=os.devnull,
                                     GIT_AUTHOR_NAME="Baton Test",
                                     GIT_AUTHOR_EMAIL="t@baton.invalid",
                                     GIT_COMMITTER_NAME="Baton Test",
                                     GIT_COMMITTER_EMAIL="t@baton.invalid"))
    return answer.stdout


def _report_place(argv):
    """The report path the review prompt names, read back out of the prompt."""
    for word in argv[-1].split():
        if word.endswith("review-report.json"):
            return word
    return None


class LifecycleCase(ServingCase):

    def setUp(self):
        super().setUp()
        # A REAL GIT SOURCE, because the composed line is a real Git line.
        _git("init", "-q", "-b", "main", at=self.source)
        with open(os.path.join(self.source, "harness.py"), "w") as writing:
            writing.write("print('the accepted verification ran')\n")
        _git("add", "--all", at=self.source)
        _git("commit", "-q", "--message", "base", at=self.source)
        self.base = _git("rev-parse", "HEAD", at=self.source).strip()
        # THE AUTHORITY'S CANONICAL TARGET IS THE LINE'S OWN BASE OBJECT.
        from baton_v12.authority import Authority
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            authority.set_policy("canonical_target", self.base)
        finally:
            authority.dispose()

        self.task_bytes = json.dumps(
            {"schema": "baton.dogfood-task/2", "task_id": "w119114-lifecycle",
             "instructions": "Add focused coverage for the composed line.",
             "source_root": "source", "source_profile": "git-line",
             "declared_base": self.base,
             "verification": ["python3", "harness.py"]},
            sort_keys=True).encode("utf-8")
        with open(self.task_document, "wb") as writing:
            writing.write(self.task_bytes)

        manifest = copy.deepcopy(self.config["input_manifest"])
        held = manifest["outputs"][0]
        manifest["outputs"] = [
            dict(held, name=name, type=kind, path=name, required=False)
            for name, kind in DECLARATIONS]
        manifest["human_contract"] = dict(
            manifest["human_contract"], bytes=len(self.task_bytes),
            content_digest=digest_of_bytes(self.task_bytes))
        manifest.pop("manifest_digest")
        manifest["manifest_digest"] = digest(manifest)
        self.manifest = manifest
        self.config["input_manifest"] = manifest
        self.submission = fixtures.submission(jobs=[fixtures.job(
            "job-a", input_digest=manifest["manifest_digest"],
            policy_digest=fixtures.POLICY_DIGEST,
            stages=[
                fixtures.stage("implementation", self.work),
                fixtures.stage("review", self.work,
                               depends_on=[{"job_id": "job-a",
                                            "kind": "implementation"}]),
                fixtures.stage("integration", self.work,
                               depends_on=[{"job_id": "job-a",
                                            "kind": "review"}])])])

    def serving(self, **members):
        self.engine = self.quiescing()
        job, control = self.stores("stage-serving")
        composed = stage_execution.operations_from(
            self.composed_document(line_declared_base=self.base, **members),
            job, control, engine_run=self.engine,
            credential_provider=lambda provider, reference: self.secret,
            clock=lambda: fixtures.NOW, checkout=self.checkout)
        self.addCleanup(composed.close)
        return job, control, composed

    def quiescing(self):
        """The deterministic engine seam, modelling three real facts.

        A stopped container stops RUNNING; a removed container is positively
        ABSENT to a later inspection in the engine's own absence sentence; and
        the custody helper answers the verb it was asked for. No daemon.
        """
        from tests.tools.test_single_worker import Engine
        from tests.manager.test_custody import reported
        original = Engine.__call__

        def call(engine, argv, *, seconds=None):
            gone = engine.__dict__.setdefault("gone", set())
            if argv[1] == "run" and "--entrypoint" in argv:
                engine.vectors.append(list(argv))
                return Engine.answer(stdout=json.dumps(reported(argv[-1])))
            if argv[1] == "rm":
                gone.add(argv[-1])
                if engine.runtime_id == argv[-1]:
                    engine.runtime_id = None
                engine.vectors.append(list(argv))
                return Engine.answer()
            if argv[1] == "inspect" and argv[-1] in gone:
                engine.vectors.append(list(argv))
                return Engine.answer(
                    status=1,
                    stderr=("Error response from daemon: No such container: "
                            + argv[-1]))
            if argv[1] == "stop":
                engine.stopped = True
            answer = original(engine, argv, seconds=seconds)
            if argv[1] == "inspect" and getattr(engine, "stopped", False):
                body = json.loads(answer["stdout"])
                body["State"]["Running"] = False
                answer = Engine.answer(stdout=json.dumps(body))
            return answer

        Engine.__call__ = call
        self.addCleanup(setattr, Engine, "__call__", original)
        return Engine()

    def states(self, job, composed):
        projected = status(job, composed, observed_at=fixtures.NOW)
        return {one["kind"]: one["state"]
                for one in projected["jobs"][0]["stages"]}

    # -- one real worker turn ------------------------------------------------

    def environment(self):
        return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": self.root,
                "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_CONFIG_SYSTEM": os.devnull,
                "GIT_TERMINAL_PROMPT": "0"}

    def provider(self, edits=None, status=0, report=None):
        def run(argv, **options):
            import claude_agent
            if argv[0] == "git":
                return subprocess.run(list(argv), env=self.environment(),
                                      **options)
            if argv[0] == claude_agent.PROVIDER_PROGRAM:
                for name, body in (edits or {}).items():
                    place = os.path.join(options["cwd"], name)
                    os.makedirs(os.path.dirname(place), exist_ok=True)
                    with open(place, "w") as writing:
                        writing.write(body)
                if report is not None:
                    place = _report_place(argv)
                    if place is not None:
                        with open(place, "w") as writing:
                            json.dump(report, writing)
                return subprocess.CompletedProcess(argv, status, None, None)
            return subprocess.run(list(argv), **options)
        return run

    def turn(self, composed, control, role, attempt_id, roots, **operands):
        import baton_worker
        import claude_agent
        from tools.single_worker import exchange, launch
        credentials = os.path.join(self.root, "cred-" + attempt_id[:12])
        os.makedirs(credentials, exist_ok=True)
        with open(os.path.join(credentials, "claude"), "w") as writing:
            writing.write("not-a-credential\n")
        delivered = launch.adopt(
            self.config["launch_home"], attempt_id=attempt_id,
            session="session-" + digest(attempt_id)[7:31],
            contract=self.config["launch_contract"], role=role,
            transport=exchange.EXCHANGE_TRANSPORT,
            workspace_group=single_worker.configured_workspace_group(control))
        held = []
        for module, name, value in (
                (baton_worker, "INPUT_ROOT", roots["inputs"]),
                (baton_worker, "OUTPUT_ROOT", roots["workspace"]),
                (claude_agent, "INPUT_ROOT", roots["inputs"]),
                (claude_agent, "OUTPUT_ROOT", roots["workspace"]),
                (claude_agent, "CREDENTIAL_ROOT", credentials)):
            held.append((module, name, getattr(module, name)))
            setattr(module, name, value)
        try:
            agent = claude_agent.ClaudeAgent(
                run=self.provider(**operands),
                home=os.path.join(self.root, "scratch-" + attempt_id[:12]))
            os.makedirs(agent._home if hasattr(agent, "_home") else
                        os.path.join(self.root, "scratch-" + attempt_id[:12]),
                        exist_ok=True)
            if os.environ.get("PROTO_DIRECT"):
                import traceback
                try:
                    print("DIRECT", agent.work(delivered.document,
                                               list(self.manifest["outputs"])))
                except BaseException:
                    traceback.print_exc()
            return baton_worker.serve_exchange(
                agent, delivered.document, delivered.document["session"],
                delivered.exchange.command_root, delivered.exchange.event_root)
        finally:
            for module, name, value in held:
                setattr(module, name, value)

    # -- one composed round --------------------------------------------------

    def worker_of(self, composed, role):
        return {one["role"]: one["operations"]._worker
                for one in composed.workers}[role]

    def drive(self, job, composed, kind, want, ticks=10):
        for _ in range(ticks):
            report = sweep(job, composed, now=fixtures.NOW)
            if os.environ.get("PROTO_TRACE"):
                print("  tick", [(o["act"], o["outcome"],
                                  str(o.get("detail"))[:300])
                                 for o in report["spoken"]],
                      "ACTS", [(o.get("act"), o.get("outcome"),
                                str(o.get("detail"))[:400])
                               for o in report["acts"]])
            held = self.states(job, composed)
            if held.get(kind) == want:
                return held
        self.fail(f"{kind} never reached {want}: {self.states(job, composed)}")

    def staged(self, composed, role, seen):
        worker = self.worker_of(composed, role)
        fresh = [one for one in worker.stage._prepared if one not in seen]
        assert len(fresh) == 1, (fresh, seen)
        attempt_id = fresh[0]
        seen.add(attempt_id)
        return attempt_id, worker.stage._prepared[attempt_id]["boundary"]["roots"]

    def test_lifecycle(self):
        job, control, composed = self.serving()
        submit(job, self.submission)
        seen = set()

        self.drive(job, composed, "implementation", "waiting")
        attempt_id, roots = self.staged(composed, "implementation", seen)
        self.assertEqual(self.turn(composed, control, "implementation",
                                   attempt_id, roots,
                                   edits={"harness.py":
                                          "print('round one')\n"}), 0)
        sweep(job, composed, now=fixtures.NOW)
        from baton_v12.worker_manager import (intake_receipt_of, retentions_of)
        print("AFTER ONE CONCLUDE", {
            k: v for k, v in dict(control._connection.execute(
                "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
                (attempt_id,)).fetchone()).items()
            if k in ("cleanup", "execution_runtime", "output", "runtime_id")})
        print("VECTORS", [v[:3] for v in self.engine.vectors][-14:])
        print("INTAKE", bool(intake_receipt_of(control, attempt_id)),
              "RETENTIONS", len(retentions_of(control, attempt_id)))
        print("STATES", self.states(job, composed))

        from baton_v12.authority import Authority
        from baton_v12.worker_manager import attempt_runtime_of
        print("ATTEMPT ROW", {k: v for k, v in dict(
            control._connection.execute(
                "SELECT * FROM attempts WHERE runtime_attempt_id = ?",
                (attempt_id,)).fetchone()).items()
            if "cleanup" in k or "runtime" in k or "failure" in k})
        print("JOURNAL", [dict(r) for r in control._connection.execute(
            "SELECT kind, operation_id FROM operations "
            "WHERE kind LIKE '%cleanup%' OR kind LIKE '%destroy%'")])
        print("ATTEMPT AFTER ENDING", json.dumps(
            attempt_runtime_of(control, attempt_id), indent=1))
        authority = Authority.open(
            self.authority_path,
            expected_authority_uuid=self.config["authority_uuid"])
        try:
            print("WORK", json.dumps(authority.project_work(self.work),
                                     indent=1))
        finally:
            authority.dispose()
        self.drive(job, composed, "review", "waiting")
        review_attempt, review_roots = self.staged(composed, "review", seen)
        print("REVIEW ROOTS", dict(review_roots))
        answered = self.turn(
            composed, control, "review", review_attempt, review_roots,
            report={"schema": "baton.review-report/1",
                    "verdict": "changes-requested",
                    "findings": "round one needs one more change\n"})
        print("REVIEW RC", answered)
        report = sweep(job, composed, now=fixtures.NOW)
        print("REVIEW", json.dumps(
            [(o["act"], o["outcome"], str(o.get("detail"))[:500])
             for o in report["spoken"]], indent=1)[:3000])
        print("STATES", self.states(job, composed))


if __name__ == "__main__":
    unittest.main()
