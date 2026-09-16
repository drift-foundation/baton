"""W183883 claim189538 -- reversal probes for the two returned corrections.

review-2026-09-16T21-31-10Z.md returned two bounded things: [B1] the focused
recipe check for the documented two-operand form ran a REAL `just build` --
pip and PyInstaller -- before Python could refuse the absent input document,
and [B2] the guide's direct-helper example named `python/build/out/distro`
from inside `v12/python`, which resolves to a path that does not exist.

Both are now held by checks over the RECIPE and the GUIDE, so these ask the
only question worth asking of a check: does it fail when the thing it is
about is broken?

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout, and
nothing here builds, clones or reaches an index.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-189538")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"justfile": TREE / "justfile", "guide": TREE / "STACK.md"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

RECIPE = "tests.tools.test_environment.TheBootstrapRecipeReachesTheHelper."
TWO = RECIPE + "test_the_TWO_OPERAND_form_forwards_the_built_path_without_building"
GUIDE = RECIPE + "test_the_guides_DIRECT_helper_example_resolves_from_where_it_stands"

PROBES = [
    {"label": "B1-the-two-operand-form-forwards-the-wrong-built-path",
     "file": "justfile",
     "before": 'DISTRO_HERE="$(dirname "{{justfile()}}")/python/build/out/distro"',
     "after": 'DISTRO_HERE="$(dirname "{{justfile()}}")/build/out/distro"',
     "checks": [TWO],
     "intended": "build/out/distro' != '"},
    {"label": "B2-the-two-operand-form-stops-building-at-all",
     "file": "justfile",
     "before": '\t\tjust --justfile "{{justfile()}}" build\n',
     "after": "",
     "checks": [TWO],
     "intended": "not found in"},
    {"label": "B3-the-guide-s-direct-example-names-the-path-that-does-not-exist",
     "file": "guide",
     "before": "    --distro build/out/distro --no-repositories",
     "after": "    --distro python/build/out/distro --no-repositories",
     "checks": [GUIDE],
     "intended": "does not name the built runtime from"},
    {"label": "B4-the-guide-s-direct-example-uses-ambient-python-again",
     "file": "guide",
     "before": ('cd v12/python && PYTHONPATH=src:. '
                '"$(python3 -m tools.environment interpreter)" \\\n    -m tools.bootstrap \\'),
     "after": "cd v12/python && PYTHONPATH=src:. python3 -m tools.bootstrap \\",
     "checks": [GUIDE],
     "intended": "not found in"},
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
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
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
        print(said[-1200:])
    print(("KILL   " if killed else "PROVES NOTHING ") + probe["label"]
          + ("" if baseline.returncode == 0 else "  (NO BASELINE -- INVALID)"))

restore()
restored, restore_seconds = run(["tests.tools.test_environment"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-189538.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
