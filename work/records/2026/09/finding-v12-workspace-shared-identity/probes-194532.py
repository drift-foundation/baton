"""W194457 claim194532 -- reversal probes for the removed permission pass.

Review 2026-09-17T12-32-56Z: remove the permission-only whole-tree pass, bound
the descriptors the retained integrity/consumption traversal holds, and keep
every constraint that used to ride along with the removed pass.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. No engine, model, store, deployment
or version-control operation.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W194457_PROBE_TREE", "/tmp/w194457-probes-194532")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"workspaces": TREE / "python" / "src" / "baton_v12" / "worker_manager"
                       / "workspaces.py",
         "review_cycles": TREE / "python" / "src" / "baton_v12"
                          / "worker_manager" / "review_cycles.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

LINE = "tests.manager.test_workspaces.InitialStableLineAccess."
CONSUME = "tests.manager.test_workspaces.TheManagerProvesItCanReadTheLineItConsumes"
CYCLE = "tests.manager.test_review_cycles.StableLineLifecycle."

PROBES = [
    {"label": "M1-the-consumption-walk-holds-every-descriptor-again",
     "file": "workspaces",
     "before": "            held.append(child)\n            try:\n"
               "                visit(child, below)\n            finally:\n"
               "                held.pop()\n                os.close(child)",
     "after": "            held.append(child)\n            visit(child, below)",
     "checks": ["tests.manager.test_workspaces.TheConsumptionWalkIsBoundedToo"],
     # PROVED NOTHING AS FIRST WRITTEN, and the gap was MINE: I pointed this at
     # the existing consumption cases, whose fixtures are small enough that
     # holding every descriptor costs nothing. The bound is a property of a
     # WIDE tree, so a case that uses one now exists and this points at it.
     "intended": "AssertionError"},

    {"label": "M2-the-integrity-walk-holds-every-descriptor-again",
     "file": "workspaces",
     "before": "            held.append(child)\n            try:\n"
               "                visit(child, depth + 1)\n            finally:\n"
               "                held.pop()\n                os.close(child)",
     "after": "            held.append(child)\n            visit(child, depth + 1)",
     "checks": [LINE + "test_the_peak_descriptor_count_is_bounded_by_DEPTH",
                LINE + "test_it_runs_UNDER_a_soft_limit_the_old_pass_exhausted"],
     "intended": "AssertionError"},

    {"label": "M3-establishing-access-walks-the-tree-again",
     "file": "workspaces",
     "before": "        os.fchown(root, -1, identity.gid)\n"
               '        _permission_act("chown")',
     "after": "        for where, _names, files in os.walk(place):\n"
              "            for one in files:\n"
              '                _permission_act("chown")\n'
              "        os.fchown(root, -1, identity.gid)\n"
              '        _permission_act("chown")',
     "checks": [LINE + "test_the_permission_work_is_TWO_ACTS_whatever_the_tree_holds"],
     "intended": "AssertionError"},

    {"label": "M4-an-entry-this-identity-does-not-own-is-accepted",
     "file": "workspaces",
     "before": "        if found.st_uid != identity.uid:\n"
               '            _denied("the development line carries an entry this deployment\'s "',
     "after": "        if False:\n"
              '            _denied("the development line carries an entry this deployment\'s "',
     "checks": [LINE + "test_the_ceilings_and_a_foreign_owner_are_STILL_refused"],
     "intended": "ContractRefusal not raised"},

    {"label": "M5-hardlinks-stop-being-refused-with-the-removed-pass",
     "file": "workspaces",
     "before": "            if found.st_nlink != 1:\n"
               '                _denied("the development line carries a hardlinked file")',
     "after": "            if False:\n"
              '                _denied("the development line carries a hardlinked file")',
     "checks": [LINE + "test_hardlinks_and_special_files_are_STILL_refused"],
     "intended": "ContractRefusal not raised"},

    {"label": "M6-the-identity-becomes-a-pair-of-integers-again",
     "file": "workspaces",
     "before": "    if not isinstance(identity, WorkspaceIdentity):\n"
               '        _denied("establishing development-line access needs this deployment\'s "',
     "after": "    if False:\n"
              '        _denied("establishing development-line access needs this deployment\'s "',
     "checks": [LINE + "test_a_bad_identity_root_or_pin_refuses_before_any_act"],
     # PROVED NOTHING AS FIRST WRITTEN: without the guard a tuple reaches
     # `identity.uid` and the reversal dies on AttributeError rather than
     # succeeding. That IS the guard's value -- an operator-facing refusal
     # instead of an attribute error -- so the token names it.
     "intended": "AttributeError"},

    {"label": "M7-the-failure-stops-naming-its-errno",
     "file": "workspaces",
     "before": '        _denied(f"initial development-line access failed: "\n'
               '                f"{type(failure).__name__} (errno "\n'
               '                f"{getattr(failure, \'errno\', None)}); the root may carry a "',
     "after": '        _denied(f"initial development-line access failed: "\n'
              '                f"{type(failure).__name__}; the root may carry a "',
     "checks": [LINE + "test_a_failure_while_establishing_NAMES_its_errno"],
     # PROVED NOTHING AS FIRST WRITTEN: the refusal is still raised, it simply
     # no longer says which errno, so assertRaisesRegex reports a mismatch.
     "intended": "does not match"},

    {"label": "M8-create_line-stops-proving-integrity-at-all",
     "file": "review_cycles",
     "before": "        workspaces.prove_line_integrity(path, (device, inode), identity)\n",
     "after": "",
     "checks": [CYCLE + "test_creating_a_line_PROVES_its_integrity_before_granting_access"],
     # PROVED NOTHING AS FIRST WRITTEN, and again the gap was mine: the case I
     # pointed at only looks at modes, which stay 0600 whether the walk runs or
     # not. A hardlinked file is a property ONLY the walk refuses.
     "intended": "ContractRefusal not raised"},
]


def caches():
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def restore():
    for place, text in PRISTINE.items():
        place.write_text(text)
    caches()


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"] + list(names),
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=900,
        env=dict(os.environ, PYTHONPATH="src:.",
                 BATON_V12_STACK_TEST_ROOT="/var/tmp"))
    return done, time.monotonic() - started


results, spent = [], 0.0
for probe in PROBES:
    restore()
    target = FILES[probe["file"]]
    baseline, base_seconds = run(probe["checks"])
    spent += base_seconds
    text = target.read_text()
    assert probe["before"] in text, probe["label"]
    target.write_text(text.replace(probe["before"], probe["after"], 1))
    caches()
    reverted, seconds = run(probe["checks"])
    spent += seconds
    restore()
    said = reverted.stderr
    intended = probe["intended"] in said
    killed = (baseline.returncode == 0 and reverted.returncode != 0 and intended)
    results.append({
        "probe": probe["label"], "checks": probe["checks"],
        "baseline_passes_on_pristine": baseline.returncode == 0,
        "reverted_returncode": reverted.returncode,
        "failed_on_the_intended_assertion": intended,
        "valid_kill": killed,
        "seconds": round(base_seconds + seconds, 3)})
    if not killed:
        print("---- stderr tail, " + probe["label"] + " ----")
        print(said[-1800:])
    print(("KILL   " if killed else "PROVES NOTHING ") + probe["label"]
          + ("" if baseline.returncode == 0 else "  (NO BASELINE -- INVALID)"))

restore()
restored, restore_seconds = run(["tests.manager.test_workspaces",
                                 "tests.manager.test_review_cycles"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-194532.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
