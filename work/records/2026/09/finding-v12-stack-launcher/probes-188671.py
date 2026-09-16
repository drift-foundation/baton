"""W183883 claim188671 — reversal probes for the three remainders.

Review 2026-09-16T19-00-59Z: custody was asked before waiting for the lock, so
a destination taken meanwhile was cloned into anyway [R2]; a failed publication
left this attempt's own justfile and blocked its own retry [R3]; and worker
storage outside the destination was accepted and emitted [R4].

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-188671")) / "v12"
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

REPOS = "tests.tools.test_instance.TheBootstrapPreparesTheRepositories."
DEPLOYED = "tests.tools.test_instance.TheDeploymentCarriesItsOwnJustfile."

PROBES = [
    {"label": "W1-custody-is-asked-before-the-wait-and-not-after",
     "file": "bootstrap",
     "before": "        custody(places, places[\"destination\"])\n"
               "        repositories_agree(document, places)\n"
               "        for name, place, _mirror in planned:",
     "after": "        for name, place, _mirror in planned:",
     "checks": [REPOS + "test_a_destination_TAKEN_while_this_attempt_queued_is_refused"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "W2-a-failed-publication-leaves-this-attempt-s-justfile",
     "file": "bootstrap",
     "before": "            if wrote_justfile and os.path.lexists(places[\"justfile\"]):",
     "after": "            if False:",
     "checks": [DEPLOYED + "test_a_FAILED_publication_unwinds_what_this_attempt_made",
                DEPLOYED + "test_and_the_retry_then_SUCCEEDS"],
     "intended": "AssertionError"},
    {"label": "W3-the-unwind-removes-a-justfile-it-did-not-write",
     "file": "bootstrap",
     "before": "            if wrote_justfile and os.path.lexists(places[\"justfile\"]):",
     "after": "            if os.path.lexists(places[\"justfile\"]):",
     "checks": [DEPLOYED + "test_a_FOREIGN_justfile_that_appears_is_never_removed_either"],
     "intended": "AssertionError"},
    {"label": "W4-worker-storage-may-leave-the-destination",
     "file": "bootstrap",
     # COMBINED, because two rules cover it: `storage_bound` refuses it
     # where the derivation happens, and `repositories_agree` refuses it
     # again with the other path disagreements. Either alone is enough,
     # so the defect needs both gone -- recorded rather than dressed up.
     "edits": [
         ("            if held != inside and not held.startswith(inside.rstrip(\"/\") + \"/\"):\n"
          "                outside.append((str(worker.get(\"worker_id\")), named, held))",
          "            if False:\n"
          "                outside.append((str(worker.get(\"worker_id\")), named, held))"),
         ("        if held != inside and not held.startswith(inside.rstrip(\"/\") + \"/\"):\n"
          "            disagreements.append(\n"
          "                (\"workers[\" + str(worker.get(\"worker_id\"))",
          "        if False:\n"
          "            disagreements.append(\n"
          "                (\"workers[\" + str(worker.get(\"worker_id\"))")],
     "checks": [REPOS + "test_worker_storage_OUTSIDE_the_destination_is_refused"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "W5-absent-worker-storage-is-not-derived",
     "file": "bootstrap",
     "before": "            deployment[\"workspace_storage\"] = os.path.join(",
     "after": "            deployment[\"nothing_reads_this\"] = os.path.join(",
     "checks": [REPOS + "test_absent_worker_storage_is_DERIVED_under_the_destination"],
     "intended": "KeyError"},
    {"label": "W6-every-named-storage-is-refused-including-a-shared-local-one",
     "file": "bootstrap",
     # The POSITIVE property: two workers of one instance sharing a
     # path inside it is the operator's business and is left alone.
     "before": "            if held != inside and not held.startswith(inside.rstrip(\"/\") + \"/\"):\n"
               "                outside.append((str(worker.get(\"worker_id\")), named, held))",
     "after": "            if True:\n"
              "                outside.append((str(worker.get(\"worker_id\")), named, held))",
     "checks": [REPOS + "test_two_workers_sharing_storage_INSIDE_the_instance_is_left_alone"],
     "intended": "BootstrapRefusal"},
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
(TREE.parent / "results-188671.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
