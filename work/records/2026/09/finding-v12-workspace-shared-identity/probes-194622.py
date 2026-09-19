"""W194457 claim194622 -- reversal probes for the pre-grant revalidation.

Review 2026-09-17T12-47-56Z: finding 1 is a real regression -- my first cut
dropped the post-traversal owner/link-count/mode recheck when it stopped
retaining descriptors. Finding 3: a permission-operation check must observe
ACTUAL calls, and the earlier M3 probe incremented the product's own counter
instead of restoring a syscall, so its kill proved less than it looked.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. No engine, model, store, deployment
or version-control operation.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W194457_PROBE_TREE", "/tmp/w194457-probes-194622")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"workspaces": TREE / "python" / "src" / "baton_v12" / "worker_manager"
                       / "workspaces.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

LINE = "tests.manager.test_workspaces.InitialStableLineAccess."
RACE = [LINE + "test_a_link_added_AFTER_an_entry_was_checked_is_refused",
        LINE + "test_an_entry_REPLACED_during_the_walk_is_refused"]

PROBES = [
    {"label": "N1-the-pre-grant-revalidation-pass-is-removed-again",
     "file": "workspaces",
     "before": "        recording = None\n        count = 0\n"
               "        total = 0\n        visit(root, 0, \"\")",
     "after": "        pass",
     "checks": RACE,
     "intended": "ContractRefusal not raised"},

    {"label": "N2-the-second-pass-records-instead-of-comparing",
     "file": "workspaces",
     "before": "        if recording is not None:\n"
               "            recording[relative] = (found.st_dev, found.st_ino, found.st_uid,",
     "after": "        if True:\n"
              "            (seen if recording is None else recording)[relative] = "
              "(found.st_dev, found.st_ino, found.st_uid,",
     "checks": RACE,
     "intended": "ContractRefusal not raised"},

    {"label": "N3-an-EXTRA-REAL-permission-syscall-goes-uncounted",
     "file": "workspaces",
     # NOT the counter. Review finding 3: the earlier M3 incremented
     # `PERMISSION_ACTS` in its inserted loop, so its kill said nothing about a
     # chmod added BESIDE the counter. This adds a real `os.fchmod` per entry
     # and increments nothing, which is the blind spot the check must cover.
     "after_note": "a real syscall, and the product counter left alone",
     "before": "        os.fchmod(root, _LINE_DIR)\n"
               '        _permission_act("chmod")',
     "after": "        for _where, _dirs, _files in os.walk(place):\n"
              "            for _one in _files:\n"
              "                os.fchmod(root, _LINE_DIR)\n"
              "        os.fchmod(root, _LINE_DIR)\n"
              '        _permission_act("chmod")',
     "checks": [LINE + "test_the_permission_work_is_TWO_ACTS_whatever_the_tree_holds"],
     "intended": "AssertionError"},

    {"label": "N4-a-directory-that-gains-an-entry-mid-walk-is-accepted",
     "file": "workspaces",
     "before": "        if recording is None and len(entries) != counted_children.get(relative):",
     "after": "        if False:",
     # PROVED NOTHING AS FIRST WRITTEN, and the investigation is the finding:
     # with the count comparison gone an entry that APPEARS is still refused,
     # because a new name has no fingerprint and the per-entry check catches
     # it. What only the count catches is an entry that GOES -- the second pass
     # never visits it. So the case that asks this question is the removal one,
     # which did not exist until this probe earned it.
     "checks": [LINE + "test_an_entry_that_DISAPPEARS_during_the_walk_is_refused"],
     "intended": "ContractRefusal not raised"},

    {"label": "N5-the-revalidation-stops-comparing-object-identity",
     "file": "workspaces",
     "before": "            if was != (found.st_dev, found.st_ino, found.st_uid,\n"
               "                       found.st_nlink, found.st_mode):",
     "after": "            if was[2:] != (found.st_uid,\n"
              "                       found.st_nlink, found.st_mode):",
     "checks": [LINE + "test_an_entry_REPLACED_during_the_walk_is_refused"],
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
(TREE.parent / "results-194622.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
