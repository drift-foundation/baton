"""W32576 — every guard the ending adds, measured by removal.

One mutation at a time against the real source, the real daemon-free suite run
each time, and a mutation only counts if a NAMED case fails. A guard whose
removal breaks nothing is a guard no case drives.

`-B` and `PYTHONDONTWRITEBYTECODE=1`: two mutations that remove the same number
of characters in the same mtime second are exactly what CPython reuses a stale
`.pyc` for, and a harness that can silently measure the previous edit measures
nothing. (Learned on W33936, where it did.)
"""
import pathlib
import re
import subprocess
import sys

INTAKE = pathlib.Path("src/baton_v12/worker_manager/intake.py")
HANDSHAKE = pathlib.Path("src/baton_v12/worker_manager/handshake.py")
SUITE = "tests.manager.test_refused_session_cleanup"

MUTATIONS = [
    (INTAKE, "the authority is fenced before anything is destroyed",
     '''            f"a refused handshake is fenced at the authority before anything "
            f"is destroyed, and this assignment is still authorized to "
            f"execute")''',
     '''            f"a refused handshake is fenced at the authority before anything "
            f"is destroyed, and this assignment is still authorized to "
            f"execute") if False else None'''),
    (INTAKE, "a terminal cleanup is not revisited",
     '''    if attempt["cleanup"] not in ("pending", "blocked-on-intake"):
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{attempt['cleanup']}, which is terminal; an ending is not "
            f"revisited")
    # THE SAME FROZEN ASYMMETRY BOTH SIBLINGS ARE UNDER.''',
     '''    if False:
        raise ContractRefusal(
            "refused", "already-terminal",
            f"attempt {name_value(attempt_id)} cleanup is "
            f"{attempt['cleanup']}, which is terminal; an ending is not "
            f"revisited")
    # THE SAME FROZEN ASYMMETRY BOTH SIBLINGS ARE UNDER.'''),
    (INTAKE, "an uncertain runtime is never inferred absent",
     '''            f"uncertain; this manager cannot say what exists, so there is "
            f"nothing to remove and nothing to prove absent")''',
     '''            f"uncertain; this manager cannot say what exists, so there is "
            f"nothing to remove and nothing to prove absent") if False else None'''),
    (INTAKE, "the authorizing record must exist",
     '''    if held is None:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no recorded "''',
     '''    if held is not None and False:
        raise ContractRefusal(
            "refused", "precondition",
            f"attempt {name_value(attempt_id)} has no recorded "'''),
    (INTAKE, "the record's kind is verified",
     '''    if held["kind"] != "session.unsupported-version":''',
     '''    if False:'''),
    (INTAKE, "the record is owned as a document before it is read",
     '''    record = boundaries.document(committed, "a committed refusal record",
                                 required=documents.SESSION_UNSUPPORTED_VERSION)''',
     '''    record = committed'''),
    (INTAKE, "the record's members are compared against the world",
     """        if record[member] != mine:
            raise ContractRefusal(
                "integrity", "schema",
                f"the recorded refusal names {member} \"""",
     """        if False:
            raise ContractRefusal(
                "integrity", "schema",
                f"the recorded refusal names {member} \""""),
    (INTAKE, "the adapter's answer names the attached runtime",
     '''    if answer["runtime_id"] != attempt["runtime_id"]:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the adapter answered about {name_value(answer['runtime_id'])} "
            f"and this attempt is attached to "
            f"{name_value(attempt['runtime_id'])}")
    return answer


def _settle_recordless_cleanup''',
     '''    if False:
        raise ContractRefusal(
            "runtime-observation", "identity-mismatch",
            f"the adapter answered about {name_value(answer['runtime_id'])} "
            f"and this attempt is attached to "
            f"{name_value(attempt['runtime_id'])}")
    return answer


def _settle_recordless_cleanup'''),
    (INTAKE, "this ending demands its own adapter capability",
     '''    boundaries.capability(getattr(adapter, "destroy_refused_session", None),
                          "the runtime adapter's refused-session destroy")''',
     '''    pass'''),
    (INTAKE, "the lane is released only by a settled ending",
     '''    lanes._release_lane(connection, attempt_id=attempt_id,
                        reference=lanes.lane_reference(attempt), why=why)
    return documents.cleanup_settled(
        attempt_id=attempt_id, cleanup="retained", state=state,''',
     '''    return documents.cleanup_settled(
        attempt_id=attempt_id, cleanup="retained", state=state,'''),
    (INTAKE, "the record's closed verdict is required",
     """        if record[member] != expected:""",
     """        if False:"""),
    (INTAKE, "the recorded wire versions are integers",
     """        if type(record[member]) is not int or type(record[member]) is bool:""",
     """        if False:"""),
    (INTAKE, "a version pair that agrees authorizes nothing",
     """    if record["pinned_wire_version"] == record["agent_protocol_version"]:""",
     """    if False:"""),
    (INTAKE, "the refusal was derived against this session's profile",
     """    if record["profile_digest"] != row["profile_digest"]:""",
     """    if False:"""),
    (HANDSHAKE, "the refusal record names the runtime it is about",
     '''        if held_attempt["runtime_id"] is None:''',
     '''        if False:'''),
]


def run():
    return subprocess.run(
        [sys.executable, "-B", "-m", "unittest", SUITE],
        capture_output=True, text=True,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin",
             "PYTHONDONTWRITEBYTECODE": "1"})


def failures(output):
    return sorted(set(re.findall(r"^(?:FAIL|ERROR): \S+ \(([^)]+)\)", output,
                                 re.MULTILINE)))


originals = {path: path.read_text() for path in (INTAKE, HANDSHAKE)}
baseline = run()
print("BASELINE:", baseline.stderr.strip().splitlines()[-1])
if "OK" not in baseline.stderr:
    print(baseline.stderr[-3000:])
    raise SystemExit("baseline is not green; the harness measures nothing")

unmeasured = []
try:
    for path, what, before, after in MUTATIONS:
        if originals[path].count(before) != 1:
            print(f"\n!! MUTATION NOT APPLICABLE: {what} "
                  f"({originals[path].count(before)} matches)")
            unmeasured.append(what)
            continue
        path.write_text(originals[path].replace(before, after))
        result = run()
        named = failures(result.stderr)
        print(f"\n-- removed: {what}")
        print(f"   {result.stderr.strip().splitlines()[-1]}")
        for name in named:
            print(f"   FAILS: {name}")
        if not named:
            print("   MEASURED ZERO -- no case drives this guard")
            unmeasured.append(what)
        path.write_text(originals[path])
finally:
    for path, text in originals.items():
        path.write_text(text)

print(f"\n{len(MUTATIONS) - len(unmeasured)}/{len(MUTATIONS)} mutations named "
      f"a failing case")
for what in unmeasured:
    print(f"  UNMEASURED: {what}")
print("RESTORED:", run().stderr.strip().splitlines()[-1])
