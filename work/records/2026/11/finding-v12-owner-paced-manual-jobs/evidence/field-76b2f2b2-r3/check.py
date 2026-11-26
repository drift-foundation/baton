"""Offline packet checks. No engine, installation, store, worker or manager."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

packet = Path(__file__).resolve().parent
repo = Path(sys.argv[1])
pin = "76b2f2b2359a1211139625f8f5062d980c5f68bf"
record = "work/records/2026/11/finding-v12-owner-paced-manual-jobs"
with tempfile.TemporaryDirectory(dir=repo / "work/scratch", prefix="manual-field-check-") as tmp, tempfile.TemporaryDirectory(dir="/var/tmp", prefix="manual-layout-check-") as layout:
    root = Path(tmp)
    with subprocess.Popen(["git", "-C", repo, "archive", pin, "v12/python", "v12/worker", "v12/instance-inputs.json", "v12/README.md", "v12/QUICKSTART.md"], stdout=subprocess.PIPE, env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")) as archive:
        subprocess.run(["tar", "-x", "-C", root], stdin=archive.stdout, check=True)
        if archive.wait():
            raise RuntimeError("archive failed")
    v12 = root / "v12"
    # The packaging correction: hash-pinned patch, applies to the pinned spec, and yields the spec the
    # launcher expects, carrying worker_instructions.md at its package-relative path.
    launcher = (packet / "owner-run.sh").read_text()
    pinned = dict(line.split("=", 1) for line in launcher.splitlines() if line.split("=", 1)[0] in ("patch_sha256", "spec_sha256", "instructions_sha256"))
    patch = (packet / "packaging-fix.patch").read_bytes()
    assert hashlib.sha256(patch).hexdigest() == pinned["patch_sha256"]
    spec = v12 / "python/packaging/stack.spec"
    assert "worker_instructions" not in spec.read_text(), "the pinned spec already names the instructions"
    subprocess.run(["patch", "-p1", "-s"], input=patch, cwd=root, check=True)
    assert hashlib.sha256(spec.read_bytes()).hexdigest() == pinned["spec_sha256"]
    assert '(INSTRUCTIONS, os.path.join("baton_v12", "provider_policy"))' in spec.read_text()
    instructions = v12 / "python/src/baton_v12/provider_policy/worker_instructions.md"
    assert hashlib.sha256(instructions.read_bytes()).hexdigest() == pinned["instructions_sha256"]
    # Nothing else under the package is a non-Python resource outside the two carried places.
    package = v12 / "python/src/baton_v12"
    stray = [str(p.relative_to(package)) for p in package.rglob("*") if p.is_file() and p.suffix != ".py" and "__pycache__" not in p.parts and p != instructions and package / "contracts/schema" not in p.parents]
    assert not stray, stray
    # The launcher runs the packaged preflight before any Docker build or network.
    order = [launcher.index(word) for word in ("packaging/stack.spec)", "PACKAGED PREFLIGHT", 'compose "$placeholder"', "PREFLIGHT PASSED", "docker build ", "docker network create", 'compose "$image"')]
    assert order == sorted(order), "the packaged preflight is not ahead of Docker setup"
    sys.path[:0] = [str(v12 / "python/src"), str(v12 / "python")]
    from baton_v12 import provider_policy
    from tools import pool, instance, bootstrap
    bindings = root / "records" / record
    bindings.mkdir(parents=True)
    for name in ["FINDING.md", "PLAN.md"]:
        (bindings / name).write_bytes((packet / name).read_bytes())
    task = root / "task.json"
    task.write_text(json.dumps(dict(task_id="manual-field", base_commit=pin)))
    places = instance.layout(str(Path(layout) / "instance"))
    install = json.loads((v12 / "instance-inputs.json").read_bytes())
    install.update(line_declared_base=pin, canonical_target_id="manual-field", owner_participant="baton.slaw", state_root=places["destination"])
    sel = dict(provider="claude", requested_model="field-fixture", reported_identity="field-fixture", cli_build="2.1.247")
    held = dict(install, authority_uuid="1"*32, state_root=places["state"], authority_store=places["authority_store"])
    image = "sha256:" + "a"*64
    out = pool.composed(held, worker_id="field-research", role="research", participant="field.research", image_reference=image, image_digest=image, cli_build="2.1.247", network="manual-field-test", credential_sources=str(root/"registry.json"), credentials=["claude=operator-file:fixture"], workspace_group=1000, task_document=str(task), record_path=record, checkout=str(root/"records"), verifier_layout=json.loads((v12/"worker/verifier-layout-marker.json").read_bytes()), provider_selection=sel)
    bootstrap._routing_preflight(dict(install, workers=[out["worker"]]))
    Path(out["worker"]["deployment"]["nominated_source"]).mkdir(parents=True)
    bootstrap.validated(bootstrap.configuration(dict(install, authority_uuid=held["authority_uuid"], workers=[out["worker"]]), principals={"field.research": "principal-research"}))
    assert out["declared"] == ["findings"]
    # The same predicate the launcher applies to the packaged executable's output.
    composed = root / "composed-worker.json"
    composed.write_text(json.dumps(out["worker"]))
    subprocess.run(["jq", "-e", "--arg", "d", "sha256:" + pinned["instructions_sha256"], "-f", str(packet / "preflight.jq"), str(composed)], check=True, stdout=subprocess.DEVNULL)
    broken = dict(out["worker"], role="review")
    composed.write_text(json.dumps(broken))
    assert subprocess.run(["jq", "-e", "--arg", "d", "sha256:" + pinned["instructions_sha256"], "-f", str(packet / "preflight.jq"), str(composed)], stdout=subprocess.DEVNULL).returncode != 0
    adapter = out["worker"]["deployment"]["provider_contract"]["adapter"]
    for file in ["v12/README.md", "v12/QUICKSTART.md"]:
        raw = (root / file).read_bytes()
        assert len(raw) < 49152
        prompt = "Answer this research assignment using only the supplied source. Return your findings as text.\nAssignment: Measure " + file + "\nSource: " + json.dumps({file: raw.decode()}, ensure_ascii=False)
        argv = provider_policy.argv(adapter, sel, provider_policy.labelled(adapter, "research", prompt))
        response = json.loads(subprocess.check_output([sys.executable, "-B", packet/"fixture-claude", *argv[1:]]))
        assert response["result"] == f"Deterministic research: {file}, {len(raw)} bytes, sha256 {hashlib.sha256(raw).hexdigest()}"
        assert list(response["modelUsage"]) == ["field-fixture"]
    # Both assignment documents carry the pinned source commit (second field run's refusal).
    generator = next(line for line in launcher.splitlines() if line.startswith("phase_doc() {"))
    for file in ["v12/README.md", "v12/QUICKSTART.md"]:
        made = json.loads(subprocess.check_output(["bash", "-c", "pin=" + pin + "; " + generator + "; phase_doc " + file]))
        assert made == dict(kind="research", statement="Measure " + file, scope=[file], depends_on=[], source_commit=pin), made
    assert launcher.count("phase_doc v12/") == 2 and "'.line_declared_base==null'" in launcher
    for command in ["manager create --mode manual", "manager add-phase", "manager start-phase", "manager close-job", "view", "pool compose-worker"]:
        subprocess.run([sys.executable, "-B", "-m", "tools.stack_command", *command.split(), "--help"], cwd=v12/"python", env=dict(os.environ, PYTHONPATH="src:."), check=True, stdout=subprocess.DEVNULL)
    print("PASS: pinned source, packaging patch applies and yields the expected spec, preflight predicate holds for the composed research worker and rejects a wrong role, preflight precedes Docker setup, both assignment documents name the pinned source commit, bootstrap routing validation, report-only argv and both deterministic report bodies, six operator parser paths. No instance, build or engine.")
