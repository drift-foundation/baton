"""W33936 round 3 — every guard the correction adds, measured by removal.

One mutation at a time: the guard is removed from the real source, the real
suite is run, and the mutation is only accounted for if a NAMED case fails.
A guard whose removal breaks nothing is a guard no case drives.
"""
import pathlib
import re
import subprocess
import sys

SOURCE = pathlib.Path("src/baton_v12/worker_manager/workspaces.py")
SUITE = "tests.manager.test_workspaces"

MUTATIONS = [
    ("the committed row's kind is verified",
     '''    if held["kind"] != CONFIGURE_OPERATION:''',
     '''    if False:'''),
    ("the committed answer is owned as a document",
     '''    answer = boundaries.document(committed,
                                 "the committed workspace group configuration",
                                 required=("workspace_group",))''',
     '''    answer = committed'''),
    ("the committed gid obeys the group rules",
     '''    gid = check_workspace_group(answer["workspace_group"],
                                what="the committed workspace group")''',
     '''    gid = answer["workspace_group"]'''),
    ("the signature is recomputed from the committed answer",
     '''    if held["signature"] != manager_signature(CONFIGURE_OPERATION,
                                              {"gid": gid}):''',
     '''    if False:'''),
    ("the answer is decoded through the journal's own reader",
     '''    _, committed = store.replay(CONFIGURE_OPERATION, held["signature"],
                                kind=CONFIGURE_OPERATION)''',
     '''    import json as _json
    committed = _json.loads(held["result"])'''),
    ("a projection with no committed act mints nothing",
     '''    if committed is None:
        _refuse(f"this manager's record names workspace group {projected} with '''
     '''"''',
     '''    if False:
        _refuse(f"this manager's record names workspace group {projected} with "'''),
    ("a committed act with no projection mints nothing",
     '''    if projected is None:
        _refuse(f"the deployment configured workspace group {committed} and "''',
     '''    if False:
        _refuse(f"the deployment configured workspace group {committed} and "'''),
    ("the two accounts must name the same group",
     '''    if projected != committed:''',
     '''    if False:'''),
    ("reconfiguration is guarded by the journal, not the projection",
     '''    held = _committed_workspace_group(store)
    if held is not None and held != gid:''',
     '''    held = _configured_gid(store)
    if held is not None and held != gid:'''),
]


def run():
    # NO BYTECODE CACHE. Found by this harness mis-attributing its own
    # measurement: two mutations removed exactly twelve characters each, so
    # the two source files had the SAME SIZE, and the writes landed in the
    # same mtime second -- which is precisely the pair of facts CPython
    # invalidates a `.pyc` on. The second run imported the FIRST mutation's
    # bytecode and named that mutation's failing case. A harness that can
    # silently measure the previous edit measures nothing.
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", SUITE],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin",
             "PYTHONDONTWRITEBYTECODE": "1"})


def failures(output):
    # THE FULL TEST ID, not the bare method name: attribution is the whole
    # output of this harness, and two classes may spell a case the same way.
    return sorted(set(re.findall(r"^(?:FAIL|ERROR): \S+ \(([^)]+)\)", output,
                                 re.MULTILINE)))


original = SOURCE.read_text()
baseline = run()
print("BASELINE:", baseline.stderr.strip().splitlines()[-1])
if "OK" not in baseline.stderr:
    print("baseline is not green; the harness measures nothing")
    raise SystemExit(1)

unmeasured = []
try:
    for what, before, after in MUTATIONS:
        if original.count(before) != 1:
            print(f"\n!! MUTATION NOT APPLICABLE: {what}")
            unmeasured.append(what)
            continue
        SOURCE.write_text(original.replace(before, after))
        result = run()
        named = failures(result.stderr)
        print(f"\n-- removed: {what}")
        print(f"   {result.stderr.strip().splitlines()[-1]}")
        for name in named:
            print(f"   FAILS: {name}")
        if not named:
            print("   MEASURED ZERO -- no case drives this guard")
            unmeasured.append(what)
finally:
    SOURCE.write_text(original)

print(f"\n{len(MUTATIONS) - len(unmeasured)}/{len(MUTATIONS)} mutations named "
      f"a failing case")
if unmeasured:
    print("UNMEASURED:")
    for what in unmeasured:
        print(f"  - {what}")
restored = run()
print("RESTORED:", restored.stderr.strip().splitlines()[-1])
