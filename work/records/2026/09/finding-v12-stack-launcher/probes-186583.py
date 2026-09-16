"""W183883 claim186583 — reversal probes for the bootstrap admission gates.

Review 2026-09-16T12-53-30Z asked for deterministic regressions holding four
corrections that had only ever been DEMONSTRATED. These probes ask the only
question that settles whether they are held: with one guard reverted, does a
named check fail, and does it fail on the assertion it is about?

Every probe proves a PASSING BASELINE on pristine code first [J1]. A probe that
cannot pass before the reversal measures nothing.

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-186583")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE,
                ignore=shutil.ignore_patterns(*SKIP), symlinks=True)

TARGET = TREE / "python" / "tools" / "bootstrap.py"
PRISTINE = TARGET.read_text()

MODULE = "tests.tools.test_instance."
GATES = MODULE + "TheAdmissionDecidesBeforeAnythingHappens."
IDENT = MODULE + "TheIdentityHasToMeanSomething."
CARRY = MODULE + "TheAdmissionIsCarriedNotRepeated."

PROBES = [
    {"label": "K3-a-the-link-refusal-goes-away",
     "before": "        if os.path.islink(owned):",
     "after": "        if False and os.path.islink(owned):",
     "checks": [GATES + "test_a_DANGLING_selector_link_is_refused_rather_than_written_through",
                GATES + "test_an_owned_path_that_LINKS_out_of_the_destination_is_refused"],
     "intended": "carries a link at"},
    {"label": "K3-b-the-whole-owned-path-preflight-goes-away",
     "before": '    for name in ("distro", "instance", "stores", "repository", "logs", "state",\n'
               '                 "deployment_state", "deployment", "record"):',
     "after": '    for name in ():',
     "checks": [GATES + "test_a_DANGLING_selector_link_is_refused_rather_than_written_through",
                GATES + "test_an_owned_path_that_LINKS_out_of_the_destination_is_refused"],
     "intended": "BootstrapRefusal"},
    {"label": "K3-c-the-native-validator-is-anchored-to-what-the-build-SAYS",
     "before": '    held = os.path.realpath(named)\n'
               '    root = os.path.realpath(distro)\n'
               '    for relative in runtime["entries"]:\n'
               '        if os.path.realpath(os.path.join(root, relative)) == held:\n'
               '            return None',
     "after":  '    reported = identity.get("resources") or ""\n'
               '    if reported and os.path.realpath(named).startswith(\n'
               '            os.path.realpath(reported)):\n'
               '        return None',
     "checks": [IDENT + "test_a_permissive_resources_claim_cannot_widen_what_counts",
                IDENT + "test_a_path_under_the_reported_resources_that_is_not_in_the_manifest"],
     # The reverted anchoring ADMITS the host path, so the intended failure is
     # the refusal that never came -- not the message it would have carried.
     "intended": "BootstrapRefusal not raised"},
    {"label": "K3-d-the-identity-is-asked-without-the-admitted-runtime",
     "before": '    identity = _identity_of(Path(distro) / "baton-v12-stack", runtime, distro)',
     "after":  '    identity = _identity_of(Path(distro) / "baton-v12-stack")',
     "checks": [IDENT + "test_a_native_validator_from_the_HOST_is_refused",
                IDENT + "test_a_missing_native_report_is_refused"],
     "intended": "BootstrapRefusal"},
    {"label": "K3-e-the-source-may-change-after-it-was-admitted",
     "before": '    current = instance.manifest(distro)\n'
               '    if current["digest"] != runtime_before["digest"]:',
     "after":  '    current = instance.manifest(distro)\n'
               '    if False:',
     "checks": [CARRY + "test_a_source_changed_after_admission_is_refused"],
     # Reverted, the change is caught LATER by the copied-runtime comparison --
     # after the destination has been created and the distro copied. The
     # intended failure is that the refusal names the wrong thing.
     "intended": "changed after it was admitted"},
    {"label": "K3-f-an-admission-installs-into-any-destination",
     "before": '    if os.path.realpath(places["destination"]) != os.path.realpath(destination):',
     "after":  '    if False:',
     "checks": [CARRY + "test_an_admission_for_another_destination_is_refused"],
     "intended": "BootstrapRefusal"},
]


def caches():
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"] + list(names),
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:."))
    return done, time.monotonic() - started


results, spent = [], 0.0
for probe in PROBES:
    TARGET.write_text(PRISTINE)
    caches()
    baseline, base_seconds = run(probe["checks"])
    spent += base_seconds
    text = TARGET.read_text()
    assert probe["before"] in text, probe["label"]
    TARGET.write_text(text.replace(probe["before"], probe["after"], 1))
    caches()
    reverted, seconds = run(probe["checks"])
    spent += seconds
    TARGET.write_text(PRISTINE)
    caches()
    said = reverted.stderr
    # THE FAILURE IS THE INTENDED ONE, not any error at all [J1]: an import
    # error or a misnamed check also exits non-zero and proves nothing.
    intended = ("AssertionError" in said and probe["intended"] in said
                and "Error: " not in said.split("AssertionError")[0][-40:])
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
        print(said[-900:])
    print(("KILL   " if killed else "PROVES NOTHING ") + probe["label"]
          + ("" if baseline.returncode == 0 else "  (NO BASELINE -- INVALID)"))

TARGET.write_text(PRISTINE)
caches()
restored, restore_seconds = run([MODULE.rstrip(".")])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-186583.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
