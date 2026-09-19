"""W194457 claim194683 -- reversal probes for the pre-grant revalidation.

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
    "W194457_PROBE_TREE", "/tmp/w194457-probes-194683")) / "v12"
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
    {"label": "P1-the-execution-vector-runs-as-the-pinned-pair-again",
     "file": "workspaces",
     "before": "    if type(group) is not WorkspaceGroup:",
     "after": "    if True:",
     "checks": [IDENT + "test_an_EXECUTION_vector_runs_as_the_shared_identity"],
     "intended": "not from an integer"},

    {"label": "P2-an-unmeasured-mapping-is-assumed-supported",
     "file": "workspaces",
     "before": "    if observed_identity is None:",
     "after": "    if False:",
     "checks": [IDENT + "test_an_UNMEASURED_mapping_is_refused_rather_than_assumed"],
     # PROVED NOTHING AS FIRST WRITTEN: without the guard the unpack raises
     # TypeError and the generic handler still refuses -- with the WRONG
     # sentence, "one uid-and-gid pair" instead of "unmeasured mapping". That
     # difference is the guard's whole value to an operator, so the token names
     # the mismatch the check reports.
     "intended": "does not match"},

    {"label": "P3-a-remapped-runtime-is-accepted",
     "file": "workspaces",
     "before": "    if (uid, gid) != (identity.uid, identity.gid):",
     "after": "    if False:",
     "checks": [IDENT + "test_a_REMAPPED_runtime_is_refused_by_name"],
     "intended": "ContractRefusal not raised"},

    {"label": "P4-a-root-manager-shares-its-identity-with-a-worker",
     "file": "workspaces",
     "before": "    uid = os.geteuid()\n    if uid == 0:\n"
               '        _denied("this manager runs as root, and an execution identity shared "\n'
               '                "with a worker may not be root; the deployment runs the "\n'
               '                "manager as the dedicated non-root account it provisions")\n'
               "    return WorkspaceIdentity(uid, group.gid, _MINT)",
     "after": "    return WorkspaceIdentity(os.geteuid() or 1, group.gid, _MINT)",
     "checks": [IDENT + "test_a_root_manager_gets_no_shared_identity"],
     "intended": "ContractRefusal not raised"},

    {"label": "P5-the-consent-runtime-is-given-the-shared-identity-too",
     "file": "oci",
     "before": '    if posture == "execution" and type(workspace_group) is workspaces.WorkspaceGroup:',
     "after": "    if type(workspace_group) is workspaces.WorkspaceGroup or True:",
     "checks": [IDENT + "test_a_CONSENT_vector_keeps_the_pinned_pair"],
     # PROVED NOTHING TWICE, and the second time taught me what the guard
     # actually protects: a CONSENT start carries no workspace group at all, so
     # dropping the posture condition asks `identity_for(None)` and the consent
     # vector stops composing entirely. The posture condition is what keeps
     # consent working, not merely what keeps its uid pinned.
     "intended": "not from an integer"},
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
(TREE.parent / "results-194683.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
