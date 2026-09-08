"""Read-only consistency audit of W106673's exported deterministic run.

No Docker, namespace operation, credential access or protected-original read.
Checks retained observations against independently stated acceptance conditions.
"""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
ROOT = HERE / "operator-export-k65r7btj"
NAMES = ("happy", "open-file", "cwd", "omitted", "before", "after", "stop-start-one", "stop-start-two")


def read(path):
    return json.loads(path.read_text())


def one(events, action):
    found = [e for e in events if e["action"] == action]
    assert len(found) == 1, (action, len(found))
    return found[0]


def main():
    hashes = dict((name, digest) for digest, name in re.findall(r"^([0-9a-f]{64})  (\S+)$", (ROOT / "PROVENANCE.md").read_text(), re.M))
    expected = {"runner.json", "result.json"} | {f"{name}/{file}.json" for name in NAMES for file in ("events", "gate")}
    assert set(hashes) == expected
    for name, digest in hashes.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, name
        read(ROOT / name)
    runner = read(ROOT / "runner.json")
    for name, digest in runner["scripts"].items():
        assert hashlib.sha256((HERE / name).read_bytes()).hexdigest() == digest, name
    assert runner["gid"] == 65532
    assert runner["image"] == "sha256:9351a9a0a697a69e156f8bd067dd5ef3f9fa9b110abbdbbda1f343c622c7adc0"
    result = read(ROOT / "result.json")
    assert result == read(HERE / "operator-result-2026-09-07.json")["result"]
    inspected = {}
    decoder = json.JSONDecoder()
    for row in read(HERE / "reviewer-container-state-2026-09-07.json")["stdout"].splitlines():
        values = []
        while row.strip():
            value, end = decoder.raw_decode(row.lstrip())
            row = row.lstrip()[end:]
            values.append(value)
        inspected[values[0]] = values
    summary = {}
    records = {}
    for name in NAMES:
        events = read(ROOT / name / "events.json")
        gate = read(ROOT / name / "gate.json")
        records[name] = (events, gate)
        times = [e["monotonic_ns"] for e in events]
        assert all(a < b for a, b in zip(times, times[1:])), name
        identity = one(events, "registered")["identity"]
        assert identity == gate["identity"]
        created = one(events, "created")
        assert created["container"] == identity["container"]
        assert created["workspace_pin"] == identity["workspace"]
        observed = inspected[identity["container"]]
        assert observed[1] == created["image"] == runner["image"]
        assert observed[3]["baton.run"] == created["nonce"]
        assert observed[2]["Running"] is False and observed[2]["Pid"] == 0
        source = None
        mount_ids = []
        for event in events:
            if event["action"] == "resident":
                answer = event["answer"]
                assert answer["session_nonce"] == identity["session"]
                assert answer["pid"] == 1 and answer["uid"] == answer["gid"] == 65532
                if answer["event"] == "written":
                    assert answer["workspace_identity"] == identity["workspace"]
                if answer["event"] == "security-probe":
                    assert answer["caps_zero"] and answer["no_new_privs"] == "1" and answer["seccomp"] == "2"
                    assert answer["mount_errno"] == answer["unshare_errno"] == 1
            if event["action"] != "topology":
                continue
            mounts = event["mounts"]
            roots = [m for m in mounts if m["target"] == "/"]
            assert len(roots) == 1 and "ro" in roots[0]["options"] and not roots[0]["propagation"]
            output = [m for m in mounts if m["target"] == "/output"]
            assert len(output) == int(event["attached"])
            if output:
                source = source or output[0]
                assert "rw" in output[0]["options"] and not output[0]["propagation"]
                mount_ids.append(output[0]["id"])
            assert source is not None
            for mount in mounts:
                if mount["device"] != source["device"]:
                    continue
                a, b = mount["root"].rstrip("/"), source["root"].rstrip("/")
                if a == b or a.startswith(b + "/") or b.startswith(a + "/"):
                    assert event["attached"] and mount["target"] == "/output" and a == b, (name, mount)
        stops = one(events, "shutdown-confirmed")
        consumed = [e for e in events if e["action"] == "consumed"]
        denials = [e for e in events if e["action"] == "both-gates-denied"]
        if name in NAMES[1:6]:
            assert len(denials) == 2 and len(consumed) == 1
            assert denials[-1]["monotonic_ns"] < stops["monotonic_ns"] < consumed[0]["monotonic_ns"]
            assert consumed[0]["content"] == "round 1\n"
            assert (gate["phase"], gate["generation"], gate["consumed"], gate["admissions"], gate["receipt"]) == ("reviewed", 1, 1, 1, None)
        if name in ("open-file", "cwd"):
            answer = one(events, "detach-result")["answer"]
            assert not answer["ok"] and answer["errno"] == 16
            assert one(events, "protocol-violation-busy")["monotonic_ns"] < denials[0]["monotonic_ns"]
        elif name in ("before", "after"):
            loss = one(events, "controller-interrupted")
            assert loss["point"] == name
            later = [e for e in events if e["action"] == "topology" and e["monotonic_ns"] > loss["monotonic_ns"]]
            assert len(later) == 1 and later[0]["attached"] == (name == "before")
        elif name == "omitted":
            assert not any(e["action"] == "detach-result" for e in events)
        elif name == "happy":
            assert [e["content"] for e in consumed] == ["round 1\n", "round 1\nround 2\n"]
            assert len(set(mount_ids)) == 2 and len(denials) == 1
            assert (gate["generation"], gate["consumed"], gate["admissions"]) == (2, 2, 2)
            previous = 0
            for consumed_event in consumed:
                span = [e for e in events if previous < e["monotonic_ns"] < consumed_event["monotonic_ns"]]
                detach = one(span, "detach-result")
                assert detach["answer"] == {"ok": True}
                probes = [e for e in span if e["action"] == "resident" and e["answer"]["event"] == "access-probe" and not e["answer"]["writable"]]
                assert len(probes) == 1 and probes[0]["answer"]["errno"] == 2
                assert detach["monotonic_ns"] < probes[0]["monotonic_ns"]
                previous = consumed_event["monotonic_ns"]
            assert consumed[-1]["monotonic_ns"] < stops["monotonic_ns"]
        if gate["phase"] == "shutdown":
            receipt = gate["receipt"]
            assert receipt["identity"] == identity and receipt["generation"] == gate["generation"]
            assert receipt["observation"] == {"container_stopped": True, "init_exited": True, "survivors": []}
        summary[name] = dict(events=len(events), container=identity["container"], pid=identity["pid"], session=identity["session"], workspace=identity["workspace"], mount_ids=sorted(set(mount_ids)), consumed=len(consumed), gate_denials=len(denials), final_phase=gate["phase"])
    first, second = records["stop-start-one"], records["stop-start-two"]
    assert first[1]["identity"]["workspace"] == second[1]["identity"]["workspace"]
    for member in ("container", "pid", "session", "start"):
        assert first[1]["identity"][member] != second[1]["identity"][member]
    assert one(first[0], "shutdown-confirmed")["monotonic_ns"] < one(first[0], "consumed")["monotonic_ns"] < one(second[0], "create-intent")["monotonic_ns"]
    assert len(inspected) == len(summary) == 8
    print(json.dumps(dict(outcome="export-consistency-checks-passed", exported_files=len(hashes), scenarios=summary, limitations="Operator-exported observations and reviewed runner; no protected-original hashes, new OS run, real Claude session or production-manager recovery."), indent=2))


if __name__ == "__main__":
    main()
