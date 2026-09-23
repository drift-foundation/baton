import hashlib, json, os, pathlib, subprocess, sys, time, unittest
D = pathlib.Path(__file__).resolve().parent
R = D.parents[4]
sys.path[:0] = [str(D), str(R / "v12/python/src"), str(R / "v12/python")]
import test_preparation as t
started = time.monotonic()
with (D / "review-tests-244441.log").open("w") as log:
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(t))
case = t.TheDocumentedEntrypointRunsThroughComposition("test_the_documented_command_prepares_then_composes")
case.setUp()
try:
    selected, chosen = case.resolved_document()
    bound = "/home/sl/baton-runs/single-implementation-242687/manager-source"
    chosen["manager_source"] = bound
    chosen["code_boundary"] = bound
    selected.write_text(json.dumps({"compose":chosen}))
    command = ["/home/sl/.local/state/baton-v12-venv/bin/python", "-B", str(D / "prepare_instance.py"), "--selections", str(selected), "--base", case.base]
    env = dict(os.environ, PYTHONPATH=bound, PYTHONDONTWRITEBYTECODE="1")
    answers = [subprocess.run(command, cwd="/", env=env, text=True, capture_output=True, timeout=30) for _ in range(2)]
    assert all(a.returncode == 0 for a in answers), [a.stderr for a in answers]
    assert json.loads(answers[0].stdout) == json.loads(answers[1].stdout)
    # Call the actual composer entrypoint AFTER preparation, with the exact same file.
    compose = subprocess.run([command[0], "-B", str(D / "baseline_bindings.py"), "--selections", str(selected), "--base", case.base, "--run-root", str(pathlib.Path(case.root) / "review-composed")], cwd="/", env=env, text=True, capture_output=True, timeout=30)
    assert compose.returncode == 0, compose.stderr
    packet = json.loads((pathlib.Path(case.root) / "review-composed/PACKET.json").read_text())
    assert packet["bounds"] == t.baseline_bindings.BOUNDS
    assert packet["submission"]["job_id"] == "job-" + t.RUN_ID
    assert packet["worker_image"]["config_digest"] == "sha256:c862c055c6430addc918ca078a9e4d55f6bd8173ed9c9878a8ad9d6cad334ca2"
    preservation = {}
    for record in ["PRODUCT-CHANGE-242687.json", "PRODUCT-CHANGE-244098.json"]:
        for name, values in json.loads((D/record).read_text())["paths"].items():
            preservation[name] = values["after"]
    for name, expected in preservation.items():
        assert hashlib.sha256((R/name).read_bytes()).hexdigest() == expected, name
    evidence = {"claim":244441, "tests":result.testsRun, "success":result.wasSuccessful(), "skipped":len(result.skipped), "documented_preparation_exit_codes":[a.returncode for a in answers], "replay_equal":True, "composition_exit_code":compose.returncode, "composition_after_preparation":True, "selected_interpreter":command[0], "selected_manager_source":bound, "substitutions":"Disposable Authority, Work/principals, fixture source/runtime and credentials; no provider or container. Real selected interpreter and manager snapshot used for both CLI entrypoints.", "product_preservation":preservation, "elapsed_seconds":time.monotonic()-started, "sha256":{name:hashlib.sha256((D/name).read_bytes()).hexdigest() for name in ["prepare_instance.py","test_preparation.py","OPERATOR-SUCCESSOR-244216.md","SELECTIONS-SUCCESSOR-244216.json"]}}
    (D / "review-checks-244441.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))
finally:
    case.tearDown()
    case.doCleanups()
