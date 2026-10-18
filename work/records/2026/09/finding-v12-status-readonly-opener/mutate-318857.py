import json, pathlib, subprocess, sys

STORE = pathlib.Path("src/baton_v12/worker_manager/store.py")
VECTOR = ["tests.job_manager.test_tool", "tests.job_manager.test_store_readonly",
          "tests.manager.test_store"]

MUTATIONS = [
    ("sqlite's own words are dropped, leaving the exception class alone",
     '    return name_value(str(failure)[:200])',
     '    return name_value("")'),
    ("the known-unreadable-shape paragraph is never reached",
     '        if (_declares_wal(whole) and _permitted(directory, os.W_OK) is False\n                and not {"-wal", "-shm"} & set(sidecars)):',
     '        if False:'),
    ("the refusal stops naming the store it could not read",
     '    said = [f"{what} at {name_value(path)} could not be read through its "',
     '    said = [f"{what} could not be read through its "'),
    ("the measured read/write/directory facts are withheld",
     '    if type(whole) is str:\n        said.append(',
     '    if False:\n        said.append('),
]


def run():
    finished = subprocess.run(
        [sys.executable, "-m", "unittest", "-q", *VECTOR],
        capture_output=True, text=True, env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin"})
    tail = finished.stderr.strip().splitlines()[-1]
    return finished.returncode, tail


original = STORE.read_text()
report = {"vector": VECTOR, "mutations": []}
code, tail = run()
report["unmutated"] = {"exit": code, "tail": tail}
print("unmutated:", code, tail)
for name, old, new in MUTATIONS:
    assert old in original, name
    STORE.write_text(original.replace(old, new, 1))
    code, tail = run()
    print(("CAUGHT  " if code else "ESCAPED "), name, "|", tail)
    report["mutations"].append({"mutation": name, "caught": bool(code), "tail": tail})
    STORE.write_text(original)
code, tail = run()
report["restored"] = {"exit": code, "tail": tail}
print("restored:", code, tail)
pathlib.Path("/tmp/w316915-mutations.json").write_text(json.dumps(report, indent=2))
