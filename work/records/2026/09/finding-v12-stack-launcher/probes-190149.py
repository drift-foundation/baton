"""W183883 claim190149 -- reversal probes for the no-capacity refusal.

Review 2026-09-16T23-16-06Z [P1]: `manager.serve` calls `reconcile` ONCE and
then `sweep` every tick after it, so a guard living only in `recover` was asked
at startup and never again -- and my own handoff claimed the opposite. [P2]:
the documented one-operand reconfiguration returned zero and DROPPED the
`integration_workspace` the installation had derived.

The earlier guards stay proved by probes-190047.py; these are this claim's.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here builds, clones, submits
a Job, reaches an index or touches version control.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-190149")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"stage": TREE / "python" / "tools" / "stage_execution.py",
         "bootstrap": TREE / "python" / "tools" / "bootstrap.py",
         "offers": TREE / "python" / "src" / "baton_v12" / "worker_manager"
                   / "offers.py",
         "guide": TREE / "STACK.md"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

UNSERVED = ("tests.tools.test_bootstrap."
            "AnInstanceWithNoCapacityREFUSES_WORK_IT_CANNOT_SERVE.")
INSTALLED = ("tests.tools.test_bootstrap."
             "TheINSTALLED_INSTANCE_SERVES_THE_SAME_WAY.")

PROBES = [
    {"label": "L1-the-every-tick-guard-goes-and-serve-is-quiet-again",
     "file": "stage",
     "before": '        self._nothing_unserved("on this serving tick")\n',
     "after": "",
     "checks": [UNSERVED + "test_SERVE_itself_refuses_an_offer_that_arrives_mid_run",
                UNSERVED + "test_SERVE_itself_refuses_a_pool_that_arrives_mid_run"],
     "intended": "ContractRefusal not raised"},

    {"label": "L2-the-every-tick-boundary-stops-being-this-ones",
     "file": "stage",
     "before": '    def drain(self, handlers, *, quiescent=()):',
     "after": '    def drain_off(self, handlers, *, quiescent=()):',
     "checks": [UNSERVED + "test_SERVE_itself_refuses_an_offer_that_arrives_mid_run"],
     "intended": "ContractRefusal not raised"},

    {"label": "L3-a-repeat-may-drop-the-derived-selections-again",
     "file": "bootstrap",
     "before": "    lost = dropped_selections(places, configured)\n    if lost:",
     "after": "    lost = dropped_selections(places, configured)\n    if False:",
     "checks": [INSTALLED + "test_a_repeat_that_would_DROP_a_derived_selection_is_refused"],
     # BOTH TOKENS WERE BACKWARDS, for the third time in this line of work:
     # `assertEqual(main(...), 2)` prints the FIRST operand first, so the
     # reverted run reads `0 != 2`. The reversals killed; the tokens did not
     # name what they printed.
     "intended": "0 != 2"},

    {"label": "L4-the-dropped-path-stops-being-looked-for",
     "file": "bootstrap",
     "before": "    found = [name for name in DERIVED_PATHS\n"
               "             if held.get(name) and not configured.get(name)]",
     "after": "    found = []",
     "checks": [INSTALLED + "test_a_repeat_that_would_DROP_a_derived_selection_is_refused"],
     # BOTH TOKENS WERE BACKWARDS, for the third time in this line of work:
     # `assertEqual(main(...), 2)` prints the FIRST operand first, so the
     # reverted run reads `0 != 2`. The reversals killed; the tokens did not
     # name what they printed.
     "intended": "0 != 2"},

    {"label": "L5-the-reconfiguration-stops-preserving-the-workspace",
     "file": "bootstrap",
     "before": 'DERIVED_PATHS = ("integration_target", "integration_workspace")',
     "after": 'DERIVED_PATHS = ("integration_target",)',
     "checks": [INSTALLED + "test_RECONFIGURING_an_installed_instance_keeps_everything_else"],
     "intended": "integration_workspace"},
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
restored, restore_seconds = run(["tests.tools.test_bootstrap"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-190149.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
print("installed-boundary checks are exercised by", INSTALLED)
