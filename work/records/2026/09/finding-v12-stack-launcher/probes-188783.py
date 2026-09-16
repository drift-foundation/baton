"""W183883 claim188783 — reversal probes for the public error boundary.

Review 2026-09-16T19-20-14Z: `main` caught only `BootstrapRefusal`, so an
expected installation OSError escaped as a traceback after a clean unwind --
nothing an operator can act on.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-188783")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"bootstrap": TREE / "python" / "tools" / "bootstrap.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

DEPLOYED = "tests.tools.test_instance.TheDeploymentCarriesItsOwnJustfile."

PROBES = [
    {"label": "Y1-an-installation-failure-escapes-as-a-traceback-again",
     "file": "bootstrap",
     "before": "    except OSError as failure:\n"
               "        # AN EXPECTED INSTALLATION FAILURE, ANSWERED HERE.",
     "after": "    except _NothingRaisesThis as failure:\n"
              "        # AN EXPECTED INSTALLATION FAILURE, ANSWERED HERE.",
     "checks": [DEPLOYED + "test_the_PUBLIC_command_answers_an_installation_failure"],
     "intended": "NameError"},
    {"label": "Y2-a-programming-fault-is-dressed-up-as-a-refusal",
     "file": "bootstrap",
     "before": "    except OSError as failure:\n"
               "        # AN EXPECTED INSTALLATION FAILURE, ANSWERED HERE.",
     "after": "    except Exception as failure:\n"
              "        # AN EXPECTED INSTALLATION FAILURE, ANSWERED HERE.",
     "checks": [DEPLOYED + "test_a_programming_fault_is_NOT_dressed_up_as_a_refusal"],
     "intended": "TypeError not raised"},
]


def caches():
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def restore():
    for place, text in PRISTINE.items():
        place.write_text(text)
    caches()


def target_of(probe):
    return FILES[probe["file"]]


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"] + list(names),
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:.",
                 BATON_V12_STACK_TEST_ROOT="/var/tmp"))
    return done, time.monotonic() - started


results, spent = [], 0.0
for probe in PROBES:
    restore()
    target = target_of(probe)
    baseline, base_seconds = run(probe["checks"])
    spent += base_seconds
    text = target.read_text()
    # ONE EDIT OR SEVERAL. A guard that is genuinely two guards needs both
    # reverted, and saying so beats a probe that proves nothing.
    edits = probe.get("edits") or [(probe["before"], probe["after"])]
    for before, after in edits:
        assert before in text, probe["label"]
        text = text.replace(before, after, 1)
    target.write_text(text)
    caches()
    reverted, seconds = run(probe["checks"])
    spent += seconds
    restore()
    said = reverted.stderr
    intended = probe["intended"] in said
    killed = (baseline.returncode == 0 and reverted.returncode != 0 and intended)
    results.append({
        "probe": probe["label"], "checks": probe["checks"],
        "edits": len(probe.get("edits") or [1]),
        "baseline_passes_on_pristine": baseline.returncode == 0,
        "reverted_returncode": reverted.returncode,
        "failed_on_the_intended_assertion": intended,
        "valid_kill": killed,
        "seconds": round(base_seconds + seconds, 3)})
    if not killed:
        print("---- stderr tail, " + probe["label"] + " ----")
        print(said[-900:])
    print(("KILL   " if killed else "PROVES NOTHING ") + probe["label"]
          + ("" if baseline.returncode == 0 else "  (NO BASELINE -- INVALID)"))

restore()
restored, restore_seconds = run(["tests.tools.test_instance",
                                 "tests.tools.test_bootstrap"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-188783.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
