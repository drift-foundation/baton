"""W183883 standalone installer review; no actual Git or live stack operation."""
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from unittest import mock

D = Path(__file__).resolve().parent
ROOT = D.parents[4]
sys.path[:0] = [str(ROOT / "v12/python"), str(ROOT / "v12/python/src")]
sys.dont_write_bytecode = True
from tools import bootstrap, instance, stage_execution


def main():
    started = time.monotonic()
    scratch = Path(tempfile.mkdtemp(prefix="w183883-review188542-", dir="/tmp"))
    evidence = {"claim": 188542, "scratch_retained": str(scratch), "cases": {}}
    author = json.loads((D / "EVIDENCE-188434.json").read_text())
    evidence["candidate_hashes"] = {}
    for name, expected in author["candidates"].items():
        actual = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
        assert actual == expected, name
        evidence["candidate_hashes"][name] = actual
    source = scratch / "fake-runtime"
    (source / "_internal/rpds").mkdir(parents=True)
    (source / "baton-v12-stack").write_text("inert fake executable bytes")
    (source / "_internal/rpds/rpds.so").write_text("inert fake native bytes")
    identity = {"command": "baton-v12-stack", "frozen": True, "python": "3.13.7", "platform": "Linux", "machine": "x86_64", "schema_assets": {"agent-session-1.0": 10, "worker-control-1.0": 20}, "native_rpds": str(source / "_internal/rpds/rpds.so")}

    # Counterexample to the explicit claim that an existing justfile is never replaced.
    dest = scratch / "regular-justfile"
    dest.mkdir()
    marker = dest / "justfile"
    marker.write_text("# pre-existing owner material\n")
    before = marker.read_text()
    with mock.patch.object(bootstrap, "_identity_of", return_value=identity):
        bootstrap.install(str(dest), str(source), {"authority_uuid": "a" * 32}, stream=io.StringIO())
    evidence["cases"]["regular_justfile"] = {"before": before, "after": marker.read_text(), "selector_published": (dest / "instance.json").exists()}
    assert marker.read_text() != before and (dest / "instance.json").exists()

    # This is the retained fixture CONFIGURATION, not a store or credential file.
    live = Path("/var/tmp/w183883-standalone-188434/deployment")
    configured = json.loads((live / "deployment.json").read_text())
    stage_execution.held_configuration(configured)
    given = {key: copy.deepcopy(configured[key]) for key in bootstrap.REQUIRED if key in configured}
    given.update(schema=bootstrap.SCHEMA, state_root=str(scratch / "unused"))
    given["workers"] = [{"worker_id": w["worker_id"], "role": w["role"], "participant": w["deployment"]["participant"], "deployment": copy.deepcopy(w["deployment"])} for w in configured["workers"]]
    given["jobs"] = [{"job_id": "review-fixture", "work_id": configured["job_work_id"], "line_declared_base": configured["line_declared_base"], "canonical_target_id": configured["canonical_target_id"], "source_worker_id": given["workers"][0]["worker_id"]}]
    given["repository_source"] = str(scratch / "owner-source")
    bootstrap.held(given)
    principals = {w["participant"]: w["deployment"]["principal"] for w in given["workers"]}
    built = bootstrap.configuration(given, principals)
    without_source = dict(built)
    without_source.pop("repository_source")
    bootstrap.validated(without_source)
    try:
        bootstrap.validated(built)
    except bootstrap.BootstrapRefusal as e:
        evidence["cases"]["repository_source_leaks"] = {"baseline_without_source_accepted": True, "with_source_refusal": str(e), "extra_keys": sorted(set(built) - set(stage_execution._MEMBERS) - set(stage_execution._OPTIONAL_MEMBERS))}
    else:
        raise AssertionError("Expected repository_source schema refusal")

    def exercise(label, document):
        dest = scratch / label
        inputs = scratch / (label + ".json")
        inputs.write_text(json.dumps(document))
        calls = []
        def fake_run(argv, **kwargs):
            calls.append(list(argv))
            if argv[1] == "clone":
                place = Path(argv[-1]).resolve()
                assert place.is_relative_to(scratch), place
                (place / "objects/info").mkdir(parents=True, exist_ok=True)
                said = ""
            elif "rev-parse" in argv and "--git-common-dir" in argv:
                said = str(Path(argv[2]).resolve())
            else:
                said = ""
            return subprocess.CompletedProcess(argv, 0, said, "")
        out = io.StringIO()
        with mock.patch.object(bootstrap, "_identity_of", return_value=identity), mock.patch.object(subprocess, "run", side_effect=fake_run), mock.patch.object(bootstrap, "_authority", side_effect=AssertionError("must not open an Authority")):
            code = bootstrap.main(["--inputs", str(inputs), "--destination", str(dest), "--distro", str(source)], stream=out)
        clones = [c for c in calls if c[1] == "clone"]
        return {"exit": code, "output": out.getvalue(), "calls": calls, "clone_targets": [c[-1] for c in clones], "selector_exists": (dest / "instance.json").exists(), "destination_exists": dest.exists()}

    result = exercise("valid-source-install", given)
    assert result["exit"] == 2 and len(result["clone_targets"]) == 5 and not result["selector_exists"]
    assert "carries exactly" in result["output"]
    evidence["cases"]["valid_source_install"] = result
    result = exercise("missing-input-install", {"repository_source": str(scratch / "owner-source")})
    assert result["exit"] == 2 and len(result["clone_targets"]) == 2 and result["destination_exists"]
    evidence["cases"]["missing_input_mutates_first"] = result
    traversal = {"repository_source": str(scratch / "owner-source"), "workers": [{"worker_id": "x/../../../escape"}]}
    result = exercise("traversal-install", traversal)
    outside = [str(Path(p).resolve()) for p in result["clone_targets"] if not Path(p).resolve().is_relative_to(scratch / "traversal-install")]
    assert result["exit"] == 2 and outside and (scratch / "escape").exists()
    result["outside_destination_targets"] = outside
    evidence["cases"]["worker_path_escapes_before_validation"] = result

    places = instance.layout(str(scratch / "binding"))
    selected = copy.deepcopy(given)
    selected["integration_target"] = str(scratch / "unrelated-target")
    selected["integration_workspace"] = str(scratch / "binding/repo/unprepared-workspace")
    bound = bootstrap.repositories_bound(bootstrap.workspace_bound(selected, places), places)
    planned = bootstrap.repository_plan(bound, places)
    evidence["cases"]["prepared_paths_not_bound"] = {"planned": planned, "selected_target": bound["integration_target"], "selected_workspace": bound["integration_workspace"], "selected_sources": [w["deployment"]["nominated_source"] for w in bound["workers"]], "selected_storage": [w["deployment"]["workspace_storage"] for w in bound["workers"]]}
    assert bound["integration_target"] not in [p for _,p,_ in planned]
    assert all(w["deployment"]["nominated_source"] not in [p for _,p,_ in planned] for w in bound["workers"])
    evidence["limits"] = "Real installer/configuration/validation functions with inert runtime identity and simulated Git subprocess boundary. Ordinary scratch directories only, retained. No real Git, Authority/store open, provider, engine, Job or stack process. Binding case demonstrates mapping, not a successful full install."
    evidence["seconds"] = time.monotonic() - started
    (D / "REVIEW-EVIDENCE-188542.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"seconds": evidence["seconds"], "scratch": str(scratch), "cases": {k: {key: value for key,value in v.items() if key in ("exit", "selector_published", "selector_exists", "clone_targets", "outside_destination_targets", "extra_keys", "baseline_without_source_accepted")} for k,v in evidence["cases"].items()}}, indent=2))

if __name__ == "__main__":
    main()
