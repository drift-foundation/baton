"""W194457 claim194939 -- reversal probes for the pre-grant revalidation.

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
    "W194457_PROBE_TREE", "/tmp/w194457-probes-194939")) / "v12"
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
    {"label": "T1-a-nonzero-listing-is-read-as-absence-again",
     "file": "oci",
     "before": '    if listed["status"] != 0:',
     "after": "    if False:",
     "checks": [IDENT + "test_a_daemon_that_CANNOT_ANSWER_is_not_read_as_absence"],
     "intended": "is not None"},

    {"label": "T2-an-unreachable-daemon-is-read-as-absence-again",
     "file": "oci",
     "before": "    except Exception:                                        # noqa: BLE001\n"
               '        _unresolved(helper, "the engine could not be asked whether anything of "\n'
               '                            "that name is there")\n'
               "        return False",
     "after": "    except Exception:                                        # noqa: BLE001\n"
              "        return True",
     "checks": [IDENT + "test_a_daemon_that_CANNOT_ANSWER_is_not_read_as_absence"],
     "intended": "is not None"},

    {"label": "T3-the-survivor-is-removed-by-NAME-rather-than-by-its-id",
     "file": "oci",
     "before": '        removed = port([engine, "rm", "--force", found], seconds=60)',
     "after": '        removed = port([engine, "rm", "--force", helper], seconds=60)',
     "checks": [IDENT + "test_a_surviving_object_is_removed_by_its_IMMUTABLE_ID"],
     "intended": "AssertionError"},

    {"label": "T4-the-filesystem-cleanup-outcome-stops-mattering",
     "file": "oci",
     "before": "        if ran == 0 and observed is not None and settled and removed:",
     "after": "        if ran == 0 and observed is not None and settled:",
     "checks": [IDENT + "test_a_FILESYSTEM_cleanup_that_did_not_finish_refuses",
                IDENT + "test_the_probe_directory_is_removed_through_ITS_OWN_descriptor"],
     "intended": "is not None"},

    {"label": "T5-a-failed-run-is-accepted-when-the-cleanup-was-clean",
     "file": "oci",
     "before": "        if ran == 0 and observed is not None and settled and removed:",
     "after": "        if observed is not None and settled and removed:",
     "checks": [IDENT + "test_a_RUN_that_failed_is_unmeasured_however_clean_the_rest"],
     # PROVED NOTHING AS FIRST WRITTEN, and the finding is about the CODE as
     # much as the case: a failing run that wrote nothing is refused by the
     # observation term anyway, so the run term was carrying nothing. The
     # observation is now taken whatever the status -- a container can write
     # its file and then exit non-zero -- and the matrix is where the run's
     # failure is decided. The case uses exactly that shape.
     "intended": "is not None"},

    {"label": "T6-more-than-one-object-under-the-name-is-removed-anyway",
     "file": "oci",
     "before": "    if len(identifiers) != 1:",
     "after": "    if False:",
     "checks": [IDENT + "test_MORE_THAN_ONE_object_under_the_name_removes_nothing"],
     "intended": "AssertionError"},

    {"label": "T7-the-ownership-label-is-not-compared",
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
(TREE.parent / "results-194939.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
