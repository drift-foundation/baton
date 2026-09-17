"""W183883 claim189914 -- reversal probes for the real empty-instance lifecycle.

Review 2026-09-16T22-36-58Z: finish the owner's selected outcome -- a fresh
installation with zero Jobs that STARTS, reports honestly, monitors and stops,
with no stage-execution session or per-Work grant invented for a Work nobody
bound, failing closed on work that needs absent capacity. Plus the two bounded
identity-reader details: a named pipe must not block the open, and a record
larger than the bound must not be silently truncated.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here builds, clones, submits
a Job, reaches an index or touches version control.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-189914")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"bootstrap": TREE / "python" / "tools" / "bootstrap.py",
         "stage": TREE / "python" / "tools" / "stage_execution.py",
         "scheduler": TREE / "python" / "src" / "baton_v12" / "job_manager"
                      / "scheduler.py",
         "guide": TREE / "STACK.md"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

SERVES = ("tests.tools.test_bootstrap."
          "TheGUIDES_OWN_EXAMPLE_INSTALLS_AND_SERVES.")
CLOSED = ("tests.tools.test_bootstrap."
          "AnInstanceWithNoCAPACITY_FAILS_CLOSED.")
IDENTITY = "tests.tools.test_bootstrap.TheInstanceGeneratesItsOwnIdentity."
LIFECYCLE = SERVES + "test_it_INSTALLS_and_then_STARTS_STATUS_MONITOR_STOPS"

PROBES = [
    {"label": "H1-a-document-configuring-no-capacity-is-refused-again",
     "file": "stage",
     "before": "        if not empty_ok:\n",
     "after": "        if True:\n",
     "checks": [LIFECYCLE],
     "intended": "non-empty list"},

    {"label": "H2-the-scheduler-refuses-an-empty-attachment-again",
     "file": "scheduler",
     "before": "        if type(workers) is not dict:\n",
     "after": "        if type(workers) is not dict or not workers:\n",
     "checks": [LIFECYCLE],
     "intended": "worker operations keyed by"},

    {"label": "H3-an-instance-with-no-capacity-activates-a-pool-anyway",
     "file": "stage",
     "before": "        pool = None if empty else _pool_generation(job_store, given, resolved)",
     "after": "        pool = _pool_generation(job_store, given, resolved)",
     "checks": [LIFECYCLE],
     "intended": "non-empty workers list"},

    {"label": "H4-sessions-are-minted-for-a-Work-nobody-bound",
     "file": "stage",
     "before": "    if _serves_nothing(given):\n        # NOTHING TO MINT FOR.",
     "after": "    if False:\n        # NOTHING TO MINT FOR.",
     "checks": [LIFECYCLE],
     "intended": "AssertionError"},

    {"label": "H5-a-named-pipe-blocks-the-identity-open-again",
     "file": "bootstrap",
     "before": "        handle = os.open(str(place),\n"
               "                         os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)",
     "after": "        handle = os.open(str(place), os.O_RDONLY | os.O_NOFOLLOW)",
     "checks": [IDENTITY + "test_a_NAMED_PIPE_is_refused_WITHOUT_waiting_for_a_writer"],
     "intended": "TimeoutError"},

    {"label": "H6-an-oversize-identity-record-is-truncated-again",
     "file": "bootstrap",
     "before": '        raw, chunk = b"", True\n'
               "        while chunk:\n"
               "            chunk = os.read(handle, 8192)\n"
               "            raw += chunk\n"
               "            if len(raw) > IDENTITY_LIMIT:",
     "after": '        raw, chunk = os.read(handle, IDENTITY_LIMIT), b""\n'
              "        while chunk:\n"
              "            chunk = b\"\"\n"
              "            raw += chunk\n"
              "            if False:",
     "checks": [IDENTITY + "test_an_identity_LARGER_than_a_record_is_refused_rather_than_truncated"],
     "intended": "BootstrapRefusal not raised"},

    {"label": "H7-an-empty-attachment-stops-failing-closed",
     "file": "scheduler",
     "before": "        if set(self.workers) != configured:",
     "after": "        if self.workers and set(self.workers) != configured:",
     "checks": [CLOSED + "test_a_store_with_an_ACTIVE_POOL_refuses_an_empty_composition"],
     # PROVED NOTHING AS FIRST WRITTEN. With the comparison weakened the
     # attachment does not SUCCEED -- it reaches `self.workers[key]` for a
     # worker it was never given and raises KeyError from inside the loop. The
     # guard is still the load-bearing one; what it buys is a refusal naming
     # the mismatch instead of a KeyError two frames down.
     "intended": "KeyError"},

    {"label": "H8-a-deployment-with-no-worker-answers-SOME-operation",
     "file": "scheduler",
     "before": "        if not self.workers:\n            _refuse(",
     "after": "        if False:\n            _refuse(",
     "checks": [CLOSED + "test_an_attached_deployment_with_no_worker_answers_no_operation"],
     "intended": "IndexError"},

    {"label": "H9-the-guides-example-stops-being-a-document",
     "file": "guide",
     "before": '  "pool_generation": 1,',
     "after": '  "pool_generation": { … },',
     "checks": [SERVES + "test_the_guides_example_is_a_document_that_PARSES"],
     "intended": "JSONDecodeError"},
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
(TREE.parent / "results-189914.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
