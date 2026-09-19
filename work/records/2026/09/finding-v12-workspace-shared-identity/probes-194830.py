"""W194457 claim194830 -- reversal probes for the pre-grant revalidation.

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
    "W194457_PROBE_TREE", "/tmp/w194457-probes-194830")) / "v12"
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
    {"label": "R1-the-probe-directory-goes-back-to-a-fixed-name",
     "file": "oci",
     "before": '    root = tempfile.mkdtemp(prefix=".identity-probe-", dir=place)\n'
               "    made = os.lstat(root)",
     "after": '    root = os.path.join(place, ".identity-probe")\n'
              "    shutil.rmtree(root, ignore_errors=True)\n"
              "    os.makedirs(root)\n    made = os.lstat(root)",
     # PROVED NOTHING AS FIRST WRITTEN, and the gap was mine: the uniqueness
     # case compared a directory LISTING, which a fixed name that is created
     # and removed leaves unchanged. What a fixed name actually costs is
     # somebody else's directory, so that is what the case looks at now.
     "checks": [IDENT + "test_SOMETHING_ALREADY_AT_THE_PROBE_NAME_survives"],
     "intended": "AssertionError"},

    {"label": "R2-a-symlink-output-is-read-as-the-runtimes-own",
     "file": "oci",
     "before": "        handle = os.open(produced, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)",
     "after": "        handle = os.open(produced, os.O_RDONLY | os.O_NONBLOCK)",
     "checks": [IDENT + "test_a_SYMLINK_is_not_read_as_the_runtimes_own_output"],
     "intended": "is not None"},

    {"label": "R3-a-hardlinked-output-is-accepted",
     "file": "oci",
     "before": "        if not modes.S_ISREG(held.st_mode) or held.st_nlink != 1:",
     "after": "        if not modes.S_ISREG(held.st_mode):",
     "checks": [IDENT + "test_a_HARDLINK_to_something_outside_is_refused_too"],
     "intended": "is not None"},

    {"label": "R4-the-helper-is-not-reclaimed-when-the-engine-fails",
     "file": "oci",
     "before": '                port([engine, "rm", "--force", helper], seconds=60)',
     "after": "                pass",
     "checks": [IDENT + "test_an_engine_that_CANNOT_BE_ASKED_is_unmeasured_and_still_reclaimed"],
     # THE TOKEN WAS WRONG: the last vector is then the `run`, not a missing
     # one, so the case reports 'run' != 'rm'.
     "intended": "'run' != 'rm'"},

    {"label": "R5-a-failed-reclamation-is-swallowed",
     "file": "oci",
     "before": "            except Exception:                                # noqa: BLE001\n"
               "                # THE RECLAMATION IS ATTEMPTED AND ITS FAILURE IS NOT A\n"
               "                # MEASUREMENT. It is reported through the answer below being\n"
               "                # `None`, which refuses rather than proceeding.\n"
               "                status = None",
     "after": "            except Exception:                                # noqa: BLE001\n"
              "                pass",
     "checks": [IDENT + "test_a_helper_that_cannot_be_RECLAIMED_is_unmeasured"],
     "intended": "is not None"},

    {"label": "R6-an-unremovable-probe-directory-is-ignored",
     "file": "oci",
     "before": "    if (now.st_dev, now.st_ino) != (made.st_dev, made.st_ino):",
     "after": "    if False:",
     # SAME GAP, same correction: the replaced-directory case is what asks
     # whether removal is by identity rather than by name.
     "checks": [IDENT + "test_a_probe_directory_that_was_REPLACED_is_left_alone"],
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
                                 "tests.manager.test_oci",
                                 "tests.manager.test_custody"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-194830.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
