"""Deployment-wide lifecycle tests, using only local stand-in services."""

import importlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "tools" / "infra_deployment.py"


@pytest.fixture
def controller(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "tools"))
    return importlib.import_module("infra_deployment")


@pytest.fixture
def deployment(tmp_path):
    root = tmp_path / "deployment"
    root.mkdir(mode=0o700)
    entries = [{"name": "main", "directory": "."}, {"name": "reviewer", "directory": "reviewer"}, {"name": "coder", "directory": "coder"}]
    (root / "infra-stacks.json").write_text(json.dumps({"version": 1, "stacks": entries}))
    events = tmp_path / "events"
    service = tmp_path / "standin.py"
    service.write_text("""import signal, sys, time
def record(event):
    with open(sys.argv[1], 'a') as f:
        f.write(event + ' ' + sys.argv[2] + '\\n')
def stop(*args):
    record('stop')
    raise SystemExit(0)
signal.signal(signal.SIGTERM, stop)
record('start')
while True:
    time.sleep(0.02)
""")
    for member in entries:
        directory = root / member["directory"]
        directory.mkdir(mode=0o700, exist_ok=True)
        (directory / "infra.json").write_text(json.dumps({"version": 1, "services": [{"name": member["name"], "command": [sys.executable, str(service), str(events), member["name"]], "readiness": {"type": "process", "stableMilliseconds": 100}, "startTimeoutSeconds": 2, "stopTimeoutSeconds": 2}]}))
    yield root, entries, events
    # Use exact per-fixture ownership, even if a test damaged its registry.
    for member in reversed(entries):
        directory = root / member["directory"]
        if directory.exists():
            result = cli("stop", directory, single=True)
            assert result.returncode == 0, result.stdout + result.stderr


def cli(command, root, single=False):
    script = ROOT / "tools" / "infra.py" if single else CONTROLLER
    return subprocess.run([sys.executable, str(script), command, str(root)], capture_output=True, text=True, timeout=15)


def report(done):
    return json.loads(done.stdout or done.stderr)


def test_three_stack_lifecycle_and_missing_reviewer(deployment):
    root, _, events = deployment
    assert cli("start", root, single=True).returncode == 0
    before = report(cli("status", root))
    assert before["succeeded"] is False
    assert [row["report"]["state"] for row in before["stacks"]] == ["running", "stopped", "stopped"]
    started = cli("start", root)
    assert started.returncode == 0, started.stderr + started.stdout
    first = report(started)
    assert first["stacks"][0]["report"]["already_running"] is True
    assert report(cli("status", root))["succeeded"] is True
    assert cli("start", root).returncode == 0
    assert events.read_text().splitlines() == ["start main", "start reviewer", "start coder"]
    stopped = cli("stop", root)
    assert stopped.returncode == 0
    assert [row["name"] for row in report(stopped)["stacks"]] == ["coder", "reviewer", "main"]
    assert events.read_text().splitlines()[-3:] == ["stop coder", "stop reviewer", "stop main"]
    assert cli("status", root).returncode != 0


def test_partial_start_retains_healthy_main_and_marks_unattempted(deployment):
    root, _, events = deployment
    assert cli("start", root, single=True).returncode == 0
    pid = report(cli("status", root, single=True))["services"][0]["pid"]
    path = root / "reviewer" / "infra.json"
    document = json.loads(path.read_text())
    document["services"][0]["command"] = [sys.executable, "-c", "raise SystemExit(3)"]
    path.write_text(json.dumps(document))
    failed = cli("start", root)
    assert failed.returncode != 0
    rows = report(failed)["stacks"]
    assert rows[0]["report"]["already_running"] is True
    assert rows[1]["exit_code"] != 0
    assert rows[2]["report"]["state"] == "not-attempted"
    assert report(cli("status", root, single=True))["services"][0]["pid"] == pid
    assert "start coder" not in events.read_text()


def test_malformed_manifest_does_not_prevent_owned_stop_or_status_of_others(deployment):
    root, _, _ = deployment
    assert cli("start", root).returncode == 0
    path = root / "reviewer" / "infra.json"
    saved = path.read_text()
    path.write_text("not json")
    try:
        status = cli("status", root)
        assert status.returncode != 0
        rows = report(status)["stacks"]
        assert len(rows) == 3
        assert "error" in rows[1]["report"]
        assert rows[2]["report"]["state"] == "running"
        assert cli("stop", root).returncode == 0
    finally:
        path.write_text(saved)


def test_missing_member_manifest_prevents_all_start_and_is_visible(deployment):
    root, _, events = deployment
    path = root / "reviewer" / "infra.json"
    saved = path.read_text()
    path.unlink()
    try:
        result = cli("start", root)
        assert result.returncode != 0
        assert all(row["report"]["state"] == "not-attempted" for row in report(result)["stacks"])
        assert not events.exists()
        status = report(cli("status", root))
        assert len(status["stacks"]) == 3
        assert status["stacks"][1]["exit_code"] != 0
    finally:
        path.write_text(saved)


@pytest.mark.parametrize("entries", [[], [{"name": "main", "directory": "."}, {"name": "main", "directory": "reviewer"}], [{"name": "main", "directory": "."}, {"name": "alias", "directory": "./"}], [{"name": "main", "directory": "."}, {"name": "outside", "directory": "../outside"}], [{"name": "reviewer", "directory": "reviewer"}], [{"name": "main", "directory": ".", "unknown": 1}]])
def test_invalid_registry_has_no_lifecycle_side_effects(deployment, entries):
    root, _, events = deployment
    (root / "infra-stacks.json").write_text(json.dumps({"version": 1, "stacks": entries}))
    assert cli("start", root).returncode != 0
    assert not events.exists()
    assert not (root / "run").exists()


def test_registry_is_required_and_aliases_cannot_duplicate_stack(deployment):
    root, _, events = deployment
    (root / "infra-stacks.json").unlink()
    assert "register all stacks" in report(cli("start", root))["error"]
    (root / "alias").symlink_to(root / "reviewer", target_is_directory=True)
    entries = [{"name": "main", "directory": "."}, {"name": "reviewer", "directory": "reviewer"}, {"name": "alias", "directory": "alias"}]
    (root / "infra-stacks.json").write_text(json.dumps({"version": 1, "stacks": entries}))
    assert cli("start", root).returncode != 0
    assert not events.exists()


def test_stop_continues_after_individual_refusal(controller, deployment, monkeypatch, capsys):
    root, _, _ = deployment
    calls = []
    def refuse_one(command, member):
        calls.append(member["name"])
        if member["name"] == "reviewer":
            return {**member, "exit_code": 2, "report": {"healthy": False, "error": "identity mismatch"}}
        return {**member, "exit_code": 0, "report": {"healthy": True}}
    monkeypatch.setattr(controller, "invoke", refuse_one)
    assert controller.run(["stop", str(root)]) == 1
    assert calls == ["coder", "reviewer", "main"]
    assert len(json.loads(capsys.readouterr().out)["stacks"]) == 3


def test_only_selected_lifecycle_commands_are_called(controller, deployment, monkeypatch, capsys):
    root, _, _ = deployment
    calls = []
    def fake_run(argv):
        calls.append(argv)
        print(json.dumps({"healthy": True, "services": []}))
        return 0
    monkeypatch.setattr(controller.infra, "run", fake_run)
    assert controller.run(["start", str(root)]) == 0
    assert [argv[0] for argv in calls] == ["start"] * 3
    assert json.loads(capsys.readouterr().out)["succeeded"] is True


def test_deployment_lock_serializes_canonical_root_alias(controller, deployment, tmp_path):
    root, _, events = deployment
    alias = tmp_path / "alias"
    alias.symlink_to(root, target_is_directory=True)
    # Child announces that it is about to request start, then must wait on
    # our canonical deployment lock. No additional member lock is held here.
    code = "import sys; sys.path.insert(0, sys.argv[1]); import infra_deployment as d; print('ready', flush=True); raise SystemExit(d.run(['start', sys.argv[2]]))"
    child = None
    try:
        with controller.deployment_lock(str(root)):
            child = subprocess.Popen([sys.executable, "-c", code, str(ROOT / "tools"), str(alias)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            assert child.stdout.readline().strip() == "ready"
            with pytest.raises(subprocess.TimeoutExpired):
                child.wait(timeout=0.15)
            assert not events.exists()
        stdout, stderr = child.communicate(timeout=10)
        assert child.returncode == 0, stderr + stdout
        assert json.loads(stdout)["succeeded"] is True
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            child.communicate(timeout=10)


def test_stale_start_refusal_is_not_automatic_recovery(deployment):
    root, _, _ = deployment
    assert cli("start", root).returncode == 0
    # Change manifest digest without changing owned process identity.
    path = root / "reviewer" / "infra.json"
    path.write_text(path.read_text() + "\n")
    result = cli("start", root)
    assert result.returncode != 0
    assert "refusing to adopt" in report(result)["stacks"][1]["report"]["error"]
    assert cli("stop", root / "reviewer", single=True).returncode == 0
    assert cli("start", root).returncode == 0
