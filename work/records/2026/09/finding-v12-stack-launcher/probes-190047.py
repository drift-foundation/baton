"""W183883 claim190047 -- reversal probes for the no-capacity refusal.

Review 2026-09-16T22-58-33Z [P1]: an instance that configures no capacity
attached no worker, so `PooledManagerOperations.recover` looped over nothing
and a real accepted control offer was invisible -- an ordinary idle report
about work that exists. [P2]: the guide contradicted the implementation and the
installed boundary was never exercised.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here builds, clones, submits
a Job, reaches an index or touches version control.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-190047")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"stage": TREE / "python" / "tools" / "stage_execution.py",
         "offers": TREE / "python" / "src" / "baton_v12" / "worker_manager"
                   / "offers.py",
         "guide": TREE / "STACK.md"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

UNSERVED = ("tests.tools.test_bootstrap."
            "AnInstanceWithNoCapacityREFUSES_WORK_IT_CANNOT_SERVE.")
INSTALLED = ("tests.tools.test_bootstrap."
             "TheINSTALLED_INSTANCE_SERVES_THE_SAME_WAY.")
GUIDE = ("tests.tools.test_bootstrap.AFreshInstallHasZeroJobs."
         "test_the_guides_minimal_block_NAMES_what_is_required_and_no_more")

PROBES = [
    {"label": "K1-startup-stops-asking-what-this-instance-already-holds",
     "file": "stage",
     "before": "        if empty:\n            # AT ADMISSION,",
     "after": "        if False:\n            # AT ADMISSION,",
     "checks": [UNSERVED + "test_control_work_ALREADY_HERE_refuses_at_startup"],
     "intended": "ContractRefusal not raised"},

    {"label": "K2-resume-stops-asking-and-reports-an-idle-tick-again",
     "file": "stage",
     "before": "        if self.no_capacity_stores is not None:",
     "after": "        if False:",
     "checks": [UNSERVED + "test_control_work_ARRIVING_AFTER_attachment_refuses_on_resume",
                UNSERVED + "test_a_POOL_activated_after_attachment_is_not_ignored"],
     "intended": "ContractRefusal not raised"},

    {"label": "K3-control-work-with-no-Job-row-stops-being-looked-for",
     "file": "stage",
     "before": "    offers = outstanding_offers(control_store)\n    if offers:",
     "after": "    offers = outstanding_offers(control_store)\n    if False:",
     "checks": [UNSERVED + "test_control_work_ALREADY_HERE_refuses_at_startup"],
     "intended": "ContractRefusal not raised"},

    {"label": "K4-a-pool-arriving-after-attachment-stops-counting",
     "file": "stage",
     "before": "    active = scheduler.active_generation(job_store)\n    if active is not None:",
     "after": "    active = scheduler.active_generation(job_store)\n    if False:",
     "checks": [UNSERVED + "test_a_POOL_activated_after_attachment_is_not_ignored"],
     "intended": "ContractRefusal not raised"},

    {"label": "K5-the-read-only-question-starts-acting-on-foreign-state",
     "file": "offers",
     "before": '''    return _offers(store, "WHERE state IN ('issued', 'accepted', 'claimed') "
                          "ORDER BY issued_at")''',
     # PROVED NOTHING AS FIRST WRITTEN, and the check was the weak part rather
     # than the token: `expire_overdue` leaves an ACCEPTED offer alone, and an
     # accepted offer was all the case seeded. It now seeds a FOREIGN ISSUED
     # one too -- the state `recover_on_restart` abandons -- so a reader that
     # acts is visible. The reversal is that reader.
     "after": '''    held = recover_on_restart(store, now=store._now())
    del held
    return _offers(store, "WHERE state IN ('issued', 'accepted', 'claimed') "
                          "ORDER BY issued_at")''',
     "checks": [UNSERVED + "test_the_READER_itself_changes_nothing"],
     # AND THE TOKEN WAS WRONG TOO: once abandoned the offer leaves the live
     # states this reader asks about, so `state_of` answers None rather than
     # the settled word.
     "intended": "None != 'issued'"},

    {"label": "K6-the-installed-selector-stops-being-written",
     "file": "stage",
     "before": "        if empty:\n            composed.no_capacity_stores = (job_store, control_store)",
     "after": "        if False:\n            composed.no_capacity_stores = (job_store, control_store)",
     "checks": [UNSERVED + "test_control_work_ARRIVING_AFTER_attachment_refuses_on_resume"],
     "intended": "ContractRefusal not raised"},

    {"label": "K7-the-guide-says-again-that-a-manager-needs-a-pool",
     "file": "guide",
     "before": "**An empty pool serves.**",
     "after": "a manager cannot serve without one. **An empty pool serves.**",
     "checks": [GUIDE],
     "intended": "a manager cannot serve without one"},

    {"label": "K8-the-guide-requires-a-non-empty-binding-record-again",
     "file": "guide",
     "before": "the Authority it names, a bindings **mapping**, and every",
     "after": "the Authority it names, a non-empty set of bindings, and every",
     "checks": [GUIDE],
     "intended": "a non-empty set of bindings"},
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
(TREE.parent / "results-190047.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
print("installed-boundary checks are exercised by", INSTALLED)
