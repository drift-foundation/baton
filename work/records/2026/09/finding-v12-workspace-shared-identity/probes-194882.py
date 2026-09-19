"""W194457 claim194882 -- reversal probes for the pre-grant revalidation.

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
    "W194457_PROBE_TREE", "/tmp/w194457-probes-194882")) / "v12"
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
         "oci": TREE / "python" / "src" / "baton_v12" / "worker_manager"
                / "oci.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

LINE = "tests.manager.test_workspaces.InitialStableLineAccess."
RACE = [LINE + "test_a_link_added_AFTER_an_entry_was_checked_is_refused",
        LINE + "test_an_entry_REPLACED_during_the_walk_is_refused"]

IDENT = "tests.manager.test_workspaces.TheSharedExecutionIdentityReachesTheVECTORS."

PROBES = [
    {"label": "S1-the-removal-status-is-discarded-again",
     "file": "oci",
     "before": '    if removed["status"] != 0:',
     "after": "    if False:",
     "checks": [IDENT + "test_a_FAILED_REMOVAL_is_unmeasured_and_names_what_is_left"],
     "intended": "is not None"},

    {"label": "S2-the-ownership-label-is-not-compared",
     "file": "oci",
     "before": '    if found["stdout"].strip() != nonce:',
     "after": "    if False:",
     "checks": [IDENT + "test_an_object_THIS_PROBE_DOES_NOT_OWN_is_never_removed"],
     "intended": "AssertionError"},

    {"label": "S3-the-inspection-is-skipped-and-removal-is-unconditional",
     "file": "oci",
     "before": '    if found["status"] != 0:\n'
               "        # AN INSPECTION THAT FINDS NOTHING IS THE VERIFIED ABSENCE `--rm`",
     "after": "    if False:\n"
              "        # AN INSPECTION THAT FINDS NOTHING IS THE VERIFIED ABSENCE `--rm`",
     "checks": [IDENT + "test_a_COMPLIANT_engine_is_observed_and_accepted"],
     "intended": "AssertionError"},

    {"label": "S4-the-directory-is-removed-by-PATH-again",
     "file": "oci",
     "before": "            for name in os.listdir(held):\n"
               "                try:\n"
               "                    os.unlink(name, dir_fd=held)",
     "after": "            shutil.rmtree(root, ignore_errors=True)\n"
              "            for name in []:\n"
              "                try:\n"
              "                    os.unlink(name, dir_fd=held)",
     "checks": [IDENT + "test_the_probe_directory_is_removed_through_ITS_OWN_descriptor"],
     # THE TOKEN WAS BACKWARDS AGAIN: the reversal deletes the REPLACEMENT, so
     # the case's assertTrue reports "False is not true".
     "intended": "False is not true"},

    {"label": "S5-the-descriptor-pin-stops-being-compared",
     "file": "oci",
     "before": "            if (now.st_dev, now.st_ino) != (made.st_dev, made.st_ino):",
     "after": "            if False:",
     # NO BASELINE AS FIRST WRITTEN: I had rewritten the class and the case
     # this pointed at no longer existed, so the probe proved nothing about
     # anything. The pin now has a case that asks it directly.
     "checks": [IDENT + "test_a_probe_directory_that_is_no_longer_ours_is_left_alone"],
     "intended": "AssertionError"},

    {"label": "S6-a-symlink-output-is-read-as-the-runtimes-own",
     "file": "oci",
     "before": "        handle = os.open(produced, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)",
     "after": "        handle = os.open(produced, os.O_RDONLY | os.O_NONBLOCK)",
     "checks": [IDENT + "test_a_SYMLINK_is_not_read_as_the_runtimes_own_output"],
     "intended": "is not None"},
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
                                 "tests.manager.test_oci",
                                 "tests.manager.test_custody"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-194882.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
