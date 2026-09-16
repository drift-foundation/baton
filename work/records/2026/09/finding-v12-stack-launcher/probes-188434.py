"""W183883 claim188434 — reversal probes for the standalone interface.

OWNER-STANDALONE-INTERFACE-20260916.md selects a two-operand bootstrap that
builds its own distribution and leaves a justfile in the destination, and a
deployed lifecycle that needs nothing but that destination. These ask whether
each of those is held.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-188434")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"justfile": TREE / "justfile",
         "bootstrap": TREE / "python" / "tools" / "bootstrap.py",
         "instance": TREE / "python" / "tools" / "instance.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

DEPLOYED = "tests.tools.test_instance.TheDeploymentCarriesItsOwnJustfile."
REPOS = "tests.tools.test_instance.TheBootstrapPreparesTheRepositories."
RECIPES = "tests.tools.test_environment.TheInterpreterOverrideIsExecutable."
REAL = "tests.tools.test_environment.TheRecipesRefuseAChangedRuntime."

PROBES = [
    {"label": "U1-the-destination-gets-no-justfile-of-its-own",
     "file": "bootstrap",
     "before": '            Path(places["justfile"]).write_text(deployed_justfile(places))\n',
     "after": "",
     "checks": [DEPLOYED + "test_installing_writes_it"],
     "intended": "FileNotFoundError"},
    {"label": "U2-the-deployed-recipes-resolve-from-the-caller-s-cwd",
     "file": "bootstrap",
     "before": 'HERE := justfile_directory()',
     "after": 'HERE := invocation_directory()',
     "checks": [DEPLOYED + "test_every_path_is_resolved_from_the_justfile_s_OWN_directory",
                REAL + "test_the_DEPLOYED_justfile_reaches_it_from_anywhere"],
     "intended": "AssertionError"},
    {"label": "U3-the-deployed-recipes-stop-naming-the-instance",
     "file": "bootstrap",
     "before": 'start:\n\t"{{{{COMMAND}}}}" start --instance "{{{{INSTANCE}}}}"',
     "after": 'start:\n\t"{{{{COMMAND}}}}" start',
     "checks": [DEPLOYED + "test_the_instance_selector_is_still_what_selects"],
     "intended": "AssertionError"},
    {"label": "U4-the-two-operand-bootstrap-stops-building",
     "file": "justfile",
     "before": '\tif [[ -n "{{DESTINATION}}" && -z "{{DISTRO}}" ]]; then\n\t\tjust --justfile "{{justfile()}}" build\n',
     "after": '\tif [[ -n "{{DESTINATION}}" && -z "{{DISTRO}}" ]]; then\n',
     "checks": [RECIPES + "test_bootstrap_builds_its_own_distribution_from_two_operands"],
     "intended": "not found in"},
    {"label": "U5-the-source-wrapper-reaches-into-the-deployment-again",
     "file": "justfile",
     "before": '\t\texec just --justfile "$(realpath -m "{{DESTINATION}}")/justfile" status',
     "after": '\t\texec "$(realpath -m "{{DESTINATION}}")/distro/baton-v12-stack" status',
     "checks": [RECIPES + "test_a_lifecycle_recipe_given_a_DESTINATION_dispatches_to_its_justfile"],
     "intended": "not found in"},
    {"label": "U6-a-repository-that-already-exists-is-replaced",
     "file": "bootstrap",
     "before": "        if os.path.lexists(place):",
     "after": "        if False:",
     "checks": [REPOS + "test_an_existing_path_is_refused_and_left_alone"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "U7-two-repositories-may-be-one-repository",
     "file": "bootstrap",
     "before": "            if seen == common:",
     "after": "            if False:",
     "checks": [REPOS + "test_two_repositories_that_are_ONE_repository_are_refused"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "U8-borrowed-objects-are-accepted",
     "file": "bootstrap",
     "before": "        if os.path.exists(borrowed) and os.path.getsize(borrowed):",
     "after": "        if False:",
     "checks": [REPOS + "test_borrowed_objects_are_refused"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "U9-the-declared-base-need-not-be-in-the-target",
     "file": "bootstrap",
     "before": '        _ran(runner, [REPOSITORY_COMMAND, "-C", target, "cat-file", "-e",\n'
               '                      base + "^{commit}"],',
     "after": '        _ran(runner, [REPOSITORY_COMMAND, "-C", target, "rev-parse",\n'
              '                      "--verify", "--quiet", "HEAD"],',
     "checks": [REPOS + "test_a_declared_base_that_is_not_in_the_target_is_refused"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "U10-nothing-is-prepared-when-a-source-IS-named",
     "file": "bootstrap",
     "before": '    if source in (None, "", {}):',
     "after": "    if True:",
     "checks": [REPOS + "test_three_roles_are_prepared_from_one_source"],
     "intended": "TypeError"},
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
        print(said[-900:])
    print(("KILL   " if killed else "PROVES NOTHING ") + probe["label"]
          + ("" if baseline.returncode == 0 else "  (NO BASELINE -- INVALID)"))

restore()
restored, restore_seconds = run(["tests.tools.test_instance",
                                 "tests.tools.test_environment"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-188434.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
