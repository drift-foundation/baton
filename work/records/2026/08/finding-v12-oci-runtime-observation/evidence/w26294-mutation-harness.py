"""Measure W26294's observation seam by removing its rules."""
import pathlib, shutil, subprocess, sys
HOME = pathlib.Path("/home/sl/src/baton/v12/python")
SRC = HOME / "src" / "baton_v12" / "worker_manager"
MODULES = ["tests.manager.test_attempts", "tests.manager.test_lifecycle_composition"]

MUTATIONS = [
    ("running is inferred from list membership again", "attempts.py",
     "        state, value, why = _observed(adapter, runtime[\"runtime_id\"])\n"
     "        return _settled(store, attempt, runtime[\"runtime_id\"],",
     "        state, value, why = _observed(adapter, runtime[\"runtime_id\"])\n"
     "        value = \"running\"\n"
     "        return _settled(store, attempt, runtime[\"runtime_id\"],"),

    ("the state is recorded inside the effectively-once attachment",
     "attempts.py",
     "    observe(store, attempt_id=attempt_id, axis=\"execution_runtime\",\n"
     "            value=value)\n"
     "    return documents.runtime_attached(",
     "    return documents.runtime_attached("),

    ("an unknown engine state is accepted", "attempts.py",
     "    if state not in OBSERVED_RUNTIME:", "    if False:"),

    # -- review [P0]: the two rules the first measurement did not have --------
    #
    # Nine mutations were caught while an exact identity was never observed
    # after removal and a failed observation left the axis at `running`. A
    # measurement is only as complete as the rules somebody thought to break,
    # and neither of these was one of them.
    ("a known runtime is never observed once the listing is empty",
     "attempts.py",
     "    if known is not None:\n"
     "        state, value, why = _observed(adapter, known)",
     "    if False:\n"
     "        state, value, why = _observed(adapter, known)"),

    ("an adapter that raises leaves the axis where it was", "attempts.py",
     "    try:\n"
     "        answer = adapter.observe(runtime_id)\n"
     "    except ContractRefusal as refusal:\n"
     "        return \"uncertain\", \"uncertain\", _inconclusive(refusal.message)",
     "    if True:\n"
     "        answer = adapter.observe(runtime_id)\n"
     "    elif False:\n"
     "        return \"uncertain\", \"uncertain\", _inconclusive(refusal.message)"),

    ("an unreadable observation is not normalized to uncertain",
     "attempts.py",
     "    if type(answer) is not dict:\n"
     "        return \"uncertain\", \"uncertain\", _inconclusive(",
     "    if type(answer) is not dict:\n"
     "        return \"running\", \"running\", _inconclusive("),

    ("the inconclusive reason is dropped", "attempts.py",
     "    attached = _attach(store, attempt, runtime_id, value,\n"
     "                       why if inconclusive else None)",
     "    attached = _attach(store, attempt, runtime_id, value)"),

    # -- re-review [P1]: the answer is REBUILT, never merged ----------------
    #
    # `_attach` is effectively-once and replays the FIRST pass's document, so
    # every one of these leaves some member of the answer as old as the
    # attachment. The first is the exact behaviour the re-review found; the
    # rest are the ways a rebuild can be half-done, which is the same defect.
    ("the answer merges the replayed document instead of rebuilding it",
     "attempts.py",
     '    return documents.runtime_attached(\n'
     '        **{"attempt_id": attempt_id, "decision": "attached",',
     '    return {**attached, "observed": value}\n'
     '    return documents.runtime_attached(\n'
     '        **{"attempt_id": attempt_id, "decision": "attached",'),

    ("a conclusive answer keeps a reason", "attempts.py",
     '        **({"why": why} if inconclusive else {}))',
     '        **({"why": why} if why is not None else {}))'),

    ("an inconclusive answer explains nothing", "attempts.py",
     '        **({"why": why} if inconclusive else {}))',
     '        **{})'),

    ("`inconclusive` is decided from something other than the answer",
     "attempts.py",
     '    inconclusive = value == "uncertain"',
     '    inconclusive = state == "absent"'),

    ("a cancellation is rebuilt as an attachment", "attempts.py",
     '    if attached["decision"] != "attached":\n        return attached',
     "    pass"),

    ("a non-document observation is accepted", "attempts.py",
     "    if type(answer) is not dict:", "    if False:"),

    ("a missing member is accepted", "attempts.py",
     '        if member not in answer:', "        if False:"),

    ("quiescent is reported as running", "attempts.py",
     'OBSERVED_RUNTIME = {"running": "running", "quiescent": "quiescent",',
     'OBSERVED_RUNTIME = {"running": "running", "quiescent": "running",'),

    ("absence is reported as uncertainty", "attempts.py",
     '                    "absent": "destroyed", "uncertain": "uncertain"}',
     '                    "absent": "uncertain", "uncertain": "uncertain"}'),

    ("the adapter's observe is no longer typed as a capability", "attempts.py",
     '    boundaries.capability(getattr(adapter, "observe", None),\n'
     '                          "the runtime adapter\'s observe")',
     "    pass"),
]


def run():
    return subprocess.run([sys.executable, "-B", "-m", "unittest", *MODULES],
        cwd=HOME, capture_output=True, timeout=1200,
        env={"PYTHONPATH": "src", "PATH": "/usr/bin:/bin", "HOME": "/home/sl"})


def drop_cache():
    for c in HOME.rglob("__pycache__"): shutil.rmtree(c, ignore_errors=True)


def main():
    drop_cache(); base = run()
    print(f"BASELINE  {'OK' if base.returncode == 0 else 'FAILING'}\n")
    if base.returncode != 0:
        print(base.stderr.decode()[-2500:]); return 1
    missed = []
    for name, where, before, after in MUTATIONS:
        place = SRC / where; original = place.read_text()
        if original.count(before) != 1:
            print(f"[ANCHOR] {name}: {original.count(before)}x"); missed.append(name); continue
        place.write_text(original.replace(before, after)); drop_cache()
        try: found = run()
        finally: place.write_text(original); drop_cache()
        if found.returncode == 0:
            print(f"[UNSEEN] {name}"); missed.append(name)
        else:
            t = found.stderr.decode()
            f = sorted({l.split(" ")[1] for l in t.splitlines() if l.startswith(("FAIL: ","ERROR: "))})
            print(f"[caught] {name}\n         {', '.join(f)[:130]}")
    print()
    if missed:
        print(f"{len(missed)} UNESTABLISHED:"); [print(" -", o) for o in missed]; return 1
    print(f"all {len(MUTATIONS)} mutations caught"); return 0


if __name__ == "__main__":
    sys.exit(main())
