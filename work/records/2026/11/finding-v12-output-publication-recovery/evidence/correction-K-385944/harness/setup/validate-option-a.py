"""THE OPTION A SETUP SCRIPT'S OWN ARGV, THROUGH THE REAL COMMANDS.

`option-a-setup.sh argv STEP` prints the exact argv a step would hand the installed command. This takes each
of them and enters the REAL `tools.pool.main`, `tools.bootstrap.main` and `tools.job_manager.main` with it,
against an instance the accepted connected-creation fixture really installs. No engine, no image, no container,
no provider: the fixture's worker image identity stands where this run's would be, and its checkpoint profile
is the deterministic seam every connected creation case uses.

What it proves: every verb and operand the script uses is one the commands take, in the order they take it; the
three workers compose (the publication one WITHOUT provider operands); the repeat admits exactly them; two
ordinary creations under the named template bind two servable Jobs.
What it does not prove: the serving and settlement phase, which needs containers.
"""
import io, json, os, subprocess, sys, unittest
from pathlib import Path
root = Path.cwd(); sys.path[:0] = [str(root), str(root / "src"), str(root.parent / "worker")]
from tests.tools import test_connected_creation as connected
SCRIPT = os.environ["OPTION_A_SCRIPT"]


class OptionA(connected.TheReusableInstanceComposesHandoffCapableWorkers):
    def argv_of(self, step, **extra):
        done = subprocess.run(["bash", SCRIPT, "argv", step], env={**self.script_env, **extra},
                              capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)
        return json.loads(done.stdout)

    def test_every_step_is_accepted_by_the_real_commands(self):
        from tools import bootstrap, job_manager, pool
        from baton_v12.worker_manager import source_boundary

        issued = []
        self.installed_with_repositories(issued, native_handoff_routing=dict(self.ROUTING))
        task, record_path = self.installed_task()
        marker = os.path.join(self.root, "verifier-layout-marker.json")
        Path(marker).write_text(json.dumps(source_boundary.image_layout_marker()))
        evidence = os.path.join(self.root, "evidence"); os.makedirs(evidence)
        Path(evidence, "run-id").write_text("RUN\n")
        image = self.config["image_digest"]
        Path(evidence, "images.owned").write_text(
            f"publication baton-v12-publication:w385695-RUN {image}\nfixture baton-v12-qualification-fixture:w385695-RUN {image}\n")
        instance = os.path.join(self.state, "instance.json")
        self.script_env = {
            "PATH": os.environ["PATH"], "EVIDENCE": evidence, "INSTANCE": instance,
            "CHECKOUT": self.checkout, "RECORD": record_path, "TASK_DOCUMENT": task,
            "WORKSPACE_GROUP": str(self.config["workspace_group"]), "NETWORK": self.config["network"],
            "CREDENTIAL_SOURCES": os.path.join(self.root, "credential-sources.json"),
            "CREDENTIAL": "claude=operator-file:w202663-development", "VERIFIER_LAYOUT": marker, "CLI_BUILD": "2.1.247",
            "IMPLEMENTER": "baton.impl-a", "REVIEWER": "baton.reviewer", "PUBLISHER": "baton.publisher",
            "REPOSITORY_SOURCE": self.SOURCE, "WORK_SCOPE": "v12/python/tools/job_manager.py"}
        deployment = os.path.join(self.state, "deployment.json")
        workers, seen = [], {}
        for step, role in (("compose-implementation", "implementation"), ("compose-review", "review"),
                           ("compose-publication", "publication")):
            argv = self.argv_of(step)
            self.assertEqual(argv[:2], ["pool", "compose-worker"])
            self.assertEqual(argv[argv.index("--deployment") + 1], deployment)
            self.assertEqual("--cli-build" in argv, role != "publication", step)
            said = io.StringIO()
            code = pool.main(argv[1:], stream=said)
            self.assertEqual(code, 0, said.getvalue())
            worker = json.loads(Path(argv[argv.index("--into") + 1]).read_text())
            self.assertEqual((worker["role"], worker["deployment"]["image_digest"]), (role, image))
            workers.append(worker); seen[step] = argv
        # THE REPEAT, with the document the script composes: the instance's own install document plus these three.
        document = json.loads(Path(self.state, "install-inputs.json").read_text())
        self.assertFalse(document.get("workers") or document.get("jobs"))
        document["workers"], document["jobs"] = workers, []
        argv = self.argv_of("repeat")
        self.assertEqual(argv[0], "bootstrap")
        Path(argv[argv.index("--inputs") + 1]).write_text(json.dumps(document, sort_keys=True))
        said = io.StringIO()
        code = bootstrap.main(argv[1:], stream=said, runner=self.git(issued))
        self.assertEqual(code, 0, said.getvalue())
        self.assertEqual(sorted(one["worker_id"] for one in self.configuration()["workers"]),
                         ["qualify-impl", "qualify-publisher", "qualify-review"])
        created = []
        for step in ("create-1", "create-2"):
            argv = self.argv_of(step)
            self.assertEqual(argv[0], "manager")
            said = io.StringIO()
            code = job_manager.main(argv[1:], stream=said)
            self.assertEqual(code, 0, said.getvalue())
            held = json.loads(said.getvalue())
            self.assertEqual(held["template"]["version"], "baton.v12.job-template.implementation-review/1")
            self.assertEqual(held["servable"]["implementation"], ["qualify-impl"])
            self.assertEqual(held["servable"]["review"], ["qualify-review"])
            created.append(held["job_id"])
        self.assertEqual(len(set(created)), 2)
        print("OPTION_A_ARGV", json.dumps({"steps": sorted(seen) + ["repeat", "create-1", "create-2"], "jobs": created,
                                           "workers": sorted(w["worker_id"] for w in workers)}))


if __name__ == "__main__":
    unittest.main(argv=["x", "OptionA.test_every_step_is_accepted_by_the_real_commands"], verbosity=2)
