"""W183883 claim188582 — reversal probes for the four review corrections.

Review 2026-09-16T18-45-20Z: an installer-only operand leaked into the closed
manager schema [R1]; repository effects ran before structural and containment
checks [R2]; an existing regular justfile was overwritten [R3]; and the prepared
repositories could differ from the configured ones [R4].

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-188582")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"justfile": TREE / "justfile",
         "bootstrap": TREE / "python" / "tools" / "bootstrap.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

REPOS = "tests.tools.test_instance.TheBootstrapPreparesTheRepositories."
DEPLOYED = "tests.tools.test_instance.TheDeploymentCarriesItsOwnJustfile."
GATES = "tests.tools.test_instance.TheAdmissionDecidesBeforeAnythingHappens."

PROBES = [
    {"label": "V1-the-installer-operand-reaches-the-manager-again",
     "file": "bootstrap",
     # A COMBINED REVERSAL, and the reason is recorded rather than hidden:
     # TWO things keep this operand out of the emitted document -- it is
     # not in OPTIONAL (which is what `configuration` carries through) and
     # `prepare` strips installer members before composing at all. Either
     # alone is enough, so reverting either alone proves nothing; the
     # defect the review reproduced needs both gone.
     "edits": [
         ('OPTIONAL = ("integration_target", "integration_target_reference",',
          'OPTIONAL = ("repository_source", "integration_target", "integration_target_reference",'),
         ("    return {name: value for name, value in document.items()\n"
          "            if name not in INSTALLER_ONLY}",
          "    return document")],
     "checks": ["tests.tools.test_bootstrap.TheInstallerOperandNeverReachesTheManager"],
     # Reverted, the CLOSED schema refuses the installer's operand -- which is
     # exactly the exit 2 the review reproduced.
     "intended": "repository_source"},
    {"label": "V2-repositories-are-cloned-before-the-structure-is-proved",
     "file": "bootstrap",
     "before": "        held(without_installer_members(document))\n",
     "after": "",
     "checks": [REPOS + "test_a_source_only_input_clones_NOTHING"],
     # Reverted, nothing refuses: it clones and returns. The intended failure
     # is the refusal that never came.
     "intended": "BootstrapRefusal not raised"},
    {"label": "V3-a-worker-id-may-be-a-path-again",
     "file": "bootstrap",
     "before": '    if not said or said in (".", "..") or "/" in said',
     "after": "    if False",
     "checks": [REPOS + "test_a_worker_id_that_is_a_PATH_is_refused_before_anything"],
     # BELT AND BRACES, RECORDED AS SUCH. Reverted, the escape is STILL
     # refused -- by the containment rule that follows, which is what makes it
     # safe. What this measures is that the name check is the earlier and
     # clearer refusal, so the intended failure is the message, not a
     # permitted escape.
     "intended": "one path component"},
    {"label": "V4-the-plan-and-the-configuration-may-disagree",
     "file": "bootstrap",
     "before": "        repositories_agree(document, places)\n",
     "after": "",
     "checks": [REPOS + "test_a_named_target_that_is_not_the_prepared_one_is_REFUSED",
                REPOS + "test_a_named_source_that_is_not_the_prepared_one_is_REFUSED"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "V5-an-existing-justfile-is-overwritten-again",
     "file": "bootstrap",
     "before": '    if os.path.lexists(places["justfile"]):',
     "after": "    if False:",
     "checks": [DEPLOYED + "test_existing_material_at_that_name_is_refused"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "V6-a-partial-preparation-is-not-reported",
     "file": "bootstrap",
     "before": "        if made:",
     "after": "        if False:",
     "checks": [REPOS + "test_what_was_already_prepared_is_NAMED_when_a_later_clone_fails"],
     "intended": "AssertionError"},
    {"label": "V7-preparation-stops-serializing-with-other-attempts",
     "file": "bootstrap",
     "before": "    with serialized(places, wait):\n        for name, place, _mirror in planned:",
     "after": "    with contextlib.nullcontext():\n        for name, place, _mirror in planned:",
     "checks": [REPOS + "test_preparation_is_serialized_with_other_attempts"],
     "intended": "BootstrapRefusal not raised"},
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
(TREE.parent / "results-188582.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
