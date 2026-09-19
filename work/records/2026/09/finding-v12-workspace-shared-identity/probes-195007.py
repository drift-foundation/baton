"""W194457 claim195007 -- reversal probes for the pre-grant revalidation.

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
    "W194457_PROBE_TREE", "/tmp/w194457-probes-195007")) / "v12"
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
    {"label": "U1-the-listing-goes-back-to-a-truncated-id",
     "file": "oci",
     "before": '                       f"name=^{helper}$", "--format", "{{.ID}}",\n'
               '                       "--no-trunc"], seconds=60)',
     "after": '                       f"name=^{helper}$", "--format", "{{.ID}}"],\n'
              "                      seconds=60)",
     "checks": [IDENT + "test_a_TRUNCATED_id_is_not_treated_as_an_identity"],
     "intended": "AssertionError"},

    {"label": "U2-a-prefix-is-accepted-as-an-identity",
     "file": "oci",
     "before": "    if not _FULL_ID.match(found):",
     "after": "    if False:",
     "checks": [IDENT + "test_a_TRUNCATED_id_is_not_treated_as_an_identity"],
     "intended": "is not None"},

    {"label": "U3-a-failed-read-escapes-past-the-settlement-again",
     "file": "oci",
     "before": "            finally:\n"
               "                # SETTLEMENT IS OWED BY THE ATTEMPT, not by the reading.",
     "after": "            except BaseException:\n"
              "                raise\n"
              "            else:\n"
              "                # SETTLEMENT IS OWED BY THE ATTEMPT, not by the reading.",
     "checks": [IDENT + "test_an_OSError_while_READING_still_settles_the_engine"],
     "intended": "AssertionError"},

    {"label": "U4-a-nonzero-listing-is-read-as-absence-again",
     "file": "oci",
     "before": '    if listed["status"] != 0:',
     "after": "    if False:",
     "checks": [IDENT + "test_a_daemon_that_CANNOT_ANSWER_is_not_read_as_absence"],
     "intended": "is not None"},

    {"label": "U5-the-filesystem-cleanup-outcome-stops-mattering",
     "file": "oci",
     "before": "        if ran == 0 and observed is not None and settled and removed:",
     "after": "        if ran == 0 and observed is not None and settled:",
     "checks": [IDENT + "test_a_FILESYSTEM_cleanup_that_did_not_finish_refuses",
                IDENT + "test_the_probe_directory_is_removed_through_ITS_OWN_descriptor"],
     "intended": "is not None"},

    {"label": "U6-the-ownership-label-is-not-compared",
     "file": "oci",
     "before": '    if labelled["stdout"].strip() != nonce:',
     "after": "    if False:",
     "checks": [IDENT + "test_an_object_THIS_PROBE_DOES_NOT_OWN_is_never_removed"],
     "intended": "AssertionError"},
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
(TREE.parent / "results-195007.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
