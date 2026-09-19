"""W194457 claim194767 -- reversal probes for the pre-grant revalidation.

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
    "W194457_PROBE_TREE", "/tmp/w194457-probes-194767")) / "v12"
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
    {"label": "Q1-the-probe-answers-without-observing-anything",
     "file": "oci",
     "before": "        produced = os.path.join(root, _PROBE_NAME)\n"
               "        if status != 0 or not os.path.isfile(produced):",
     "after": "        produced = os.path.join(root, _PROBE_NAME)\n"
              "        if False:",
     "checks": [IDENT + "test_an_engine_that_PRODUCES_NOTHING_is_unmeasured",
                IDENT + "test_an_engine_that_FAILS_is_unmeasured"],
     # PROVED NOTHING AS FIRST WRITTEN: without the guard `os.stat` raises
     # FileNotFoundError from the middle of the observation. That IS the
     # guard's value -- an honest "unmeasured" instead of a crash -- so the
     # token names what the reversal actually does.
     "intended": "FileNotFoundError"},

    {"label": "Q2-an-engine-that-cannot-be-asked-is-treated-as-compliant",
     "file": "oci",
     "before": "        except Exception:                                    # noqa: BLE001\n"
               "            # AN ENGINE THAT FAILED IS AN UNMEASURED MAPPING, not a passing\n"
               "            # one. The refusal belongs to the decision function, which says so\n"
               "            # in its own words.\n"
               "            _OBSERVED[key] = None\n            return None",
     "after": "        except Exception:                                    # noqa: BLE001\n"
              "            _OBSERVED[key] = (identity.uid, identity.gid)\n"
              "            return (identity.uid, identity.gid)",
     "checks": [IDENT + "test_an_engine_that_CANNOT_BE_ASKED_is_unmeasured"],
     # PROVED NOTHING AS FIRST WRITTEN: the case asserts the observation is
     # None BEFORE it asks for the refusal, so that is the assertion the
     # reversal reaches first.
     "intended": "is not None"},

    {"label": "Q3-the-observation-is-reused-across-different-images",
     "file": "oci",
     "before": '    key = (_engine(engine), image_digest, identity.uid, identity.gid)',
     "after": '    key = (_engine(engine),)',
     "checks": [IDENT + "test_the_observation_is_keyed_to_the_runtime_it_was_taken_for"],
     "intended": "1 != 2"},

    {"label": "Q4-the-probe-leaves-its-directory-behind",
     "file": "oci",
     "before": "    finally:\n        shutil.rmtree(root, ignore_errors=True)\n    _OBSERVED[key] = answer",
     "after": "    finally:\n        pass\n    _OBSERVED[key] = answer",
     "checks": [IDENT + "test_the_probe_leaves_nothing_behind"],
     # AND THIS TOKEN WAS BACKWARDS AGAIN: assertFalse prints
     # "True is not false".
     "intended": "True is not false"},

    {"label": "Q5-the-remedy-promises-a-fix-that-moves-both-sides",
     "file": "workspaces",
     "before": '                f"NOT a general fix: the requested container identity is "',
     "after": '                f"a general fix: the requested container identity is "',
     "checks": [IDENT + "test_a_REMAPPED_runtime_is_refused_by_name"],
     "intended": "not found in"},
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
(TREE.parent / "results-194767.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
