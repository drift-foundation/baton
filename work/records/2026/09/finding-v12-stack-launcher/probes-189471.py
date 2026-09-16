"""W183883 claim189471 — reversal probes for the three stamp/source corrections.

Review 2026-09-16T21-21-54Z: `--porcelain` honours `status.showUntrackedFiles=no`
[V1]; the build output is UNTRACKED rather than ignored, so one build dirtied
every later capture [V2]; and an option written after the destination binds as
the distribution path [V3].

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-189471")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"stamp": TREE / "python" / "tools" / "build_stamp.py",
         "justfile": TREE / "justfile"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

STAMP = "tests.tools.test_version.TheStampIsCapturedFromTheCheckout."
RECIPE = "tests.tools.test_environment.TheBootstrapRecipeReachesTheHelper."

PROBES = [
    {"label": "B1-untracked-observation-is-left-to-the-host-again",
     "file": "stamp",
     "before": '    said = ran([TOOL, "-C", str(where), "status", "--porcelain",\n'
               '                "--untracked-files=normal"], where)',
     "after": '    said = ran([TOOL, "-C", str(where), "status", "--porcelain"], where)',
     "checks": [STAMP + "test_untracked_entries_are_ASKED_FOR_rather_than_left_to_the_host"],
     "intended": "AssertionError"},
    {"label": "B2-this-run-s-own-output-dirties-every-later-capture",
     "file": "stamp",
     "before": "    excused = [one for one in changed if _is_generated(one)]",
     "after": "    excused = []",
     "checks": [STAMP + "test_only_THIS_distribution_s_build_output_is_excused",
                STAMP + "test_a_REPEATED_capture_after_a_build_is_still_clean"],
     "intended": "AssertionError"},
    {"label": "B3-the-excuse-widens-past-the-pinned-paths",
     "file": "stamp",
     "before": '    if not line.startswith("?? "):\n        return False',
     "after": "    pass",
     "checks": [STAMP + "test_a_tracked_change_under_the_build_directory_is_not_excused"],
     "intended": "AssertionError"},
    {"label": "B4-an-option-in-a-positional-slot-is-bound-again",
     "file": "justfile",
     "before": '\tfor SLOT in "{{DESTINATION}}" "{{DISTRO}}"; do',
     "after": '\tfor SLOT in; do',
     "checks": [RECIPE + "test_an_OPTION_in_a_positional_slot_is_refused_by_the_recipe"],
     # Reverted, the option reaches `realpath`, which rejects it with exit 1
     # and a usage message about a tool the operator never named. The intended
     # failure is that exit, and the confusion is the point of the guard.
     "intended": "1 != 2"},
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
restored, restore_seconds = run(["tests.tools.test_version",
                                 "tests.tools.test_environment"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-189471.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
