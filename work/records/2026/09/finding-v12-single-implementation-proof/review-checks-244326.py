import hashlib, json, os, pathlib, subprocess, sys, time, unittest
D = pathlib.Path(__file__).resolve().parent
R = D.parents[4]
sys.path[:0] = [str(D), str(R / "v12/python/src"), str(R / "v12/python")]
import test_preparation as t
started = time.monotonic()
with (D / "review-tests-244326.log").open("w") as log:
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(t))
case = t.ThePreparationActsRunAgainstADisposableAuthority()
case.setUp()
try:
    chosen = case.resolved()
    nested = case.root / t.RUN_ID / "db"
    nested.mkdir(parents=True)
    for key in t.prepare_instance.STORES:
        chosen["instance"][key] = str(nested / (key + ".sqlite3"))
    t.Authority.create(chosen["instance"]["authority_store"], authority_uuid=case.uuid).dispose()
    selected = case.root / "selections.json"
    selected.write_text(json.dumps({"compose": chosen}))
    command = ["/home/sl/.local/state/baton-v12-venv/bin/python", "-B", str(D / "prepare_instance.py"), "--selections", str(selected), "--base", t.BASE]
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    exact = subprocess.run(command, env=env, text=True, capture_output=True, timeout=20)
    env["PYTHONPATH"] = "/home/sl/baton-runs/single-implementation-242687/manager-source"
    bound = subprocess.run(command, env=env, text=True, capture_output=True, timeout=20)
    refused = {}
    for run in t.prepare_instance.CONSUMED:
        old = json.loads(json.dumps(chosen))
        old["run_id"] = run
        for key in t.prepare_instance.STORES:
            old["instance"][key] = f"/home/sl/baton-runs/{run}/db/{key}.sqlite3"
        try:
            refused[run] = {"accepted_marker": t.prepare_instance.fresh(old)}
        except t.prepare_instance.PreparationRefusal as exc:
            refused[run] = {"refusal": str(exc)}
    evidence = {"claim":244326, "tests": result.testsRun, "success":result.wasSuccessful(), "skipped":len(result.skipped), "exact_document_command":{"returncode":exact.returncode,"stdout":exact.stdout,"stderr":exact.stderr}, "with_bound_PYTHONPATH":{"returncode":bound.returncode,"stdout":bound.stdout,"stderr":bound.stderr}, "consumed_name_check":refused, "elapsed_seconds":time.monotonic()-started, "sha256":{name:hashlib.sha256((D/name).read_bytes()).hexdigest() for name in ["prepare_instance.py","test_preparation.py","OPERATOR-SUCCESSOR-244216.md","SELECTIONS-SUCCESSOR-244216.json"]}}
    (D / "review-checks-244326.json").write_text(json.dumps(evidence,indent=2)+"\n")
    print(json.dumps(evidence,indent=2))
finally:
    case.doCleanups()
