"""W183883 claim186742 — reversal probes for temporary-file custody.

Review 2026-09-16T13-20-49Z: publication wrote a FIXED temporary name, so it
wrote through whatever was already at that name -- before the final name was
ever considered. A symlink there redirected the write into a foreign document
and published a symlink as the selector; a hardlink to an existing selector
destroyed its bytes while publication went on to refuse and say it had left
them alone. A temporary has to be OWNED before it is written.

Every probe proves a PASSING BASELINE on pristine code first [J1]. A probe that
cannot pass before the reversal measures nothing.

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-186742")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE,
                ignore=shutil.ignore_patterns(*SKIP), symlinks=True)

BOOTSTRAP = TREE / "python" / "tools" / "bootstrap.py"
INSTANCE = TREE / "python" / "tools" / "instance.py"
PRISTINE = {BOOTSTRAP: BOOTSTRAP.read_text(), INSTANCE: INSTANCE.read_text()}

MODULE = "tests.tools.test_instance."
AGAIN = MODULE + "TheDestinationIsAskedAboutAgain."
PUBLISH = MODULE + "PublicationRefusesToReplace."
DERIVES = MODULE + "WhatAnInstanceDerives."

# The owned temporary, and the fixed name it replaced.
OWNED = (
    '    handle, temporary = tempfile.mkstemp(prefix=".instance-", suffix=".new",\n'
    '                                         dir=str(Path(place).parent))\n'
    '    try:\n'
    '        with os.fdopen(handle, "w") as writing:\n'
    '            writing.write(json.dumps(document, indent=2, sort_keys=True) + "\\n")\n'
    '    except BaseException:\n'
    '        _discard(temporary)\n'
    '        raise\n'
    '    return temporary')
FIXED = (
    '    temporary = str(place) + ".new"\n'
    '    Path(temporary).write_text(\n'
    '        json.dumps(document, indent=2, sort_keys=True) + "\\n")\n'
    '    return temporary')

PROBES = [
    {"label": "M1-the-temporary-is-a-fixed-name-again",
     "file": "instance",
     "before": OWNED,
     "after": FIXED,
     "checks": [PUBLISH + "test_a_SYMLINK_at_the_old_temporary_name_cannot_redirect_the_write",
                PUBLISH + "test_a_HARDLINK_at_the_old_temporary_name_cannot_damage_the_selector"],
     "intended": "somebody else"},
    {"label": "M2-an-unknown-entry-is-treated-as-ours-to-remove",
     "file": "instance",
     "before": "    finally:\n        _discard(temporary)",
     "after": '    finally:\n        _discard(temporary)\n        _discard(str(place) + ".new")',
     "checks": [PUBLISH + "test_a_REGULAR_file_at_the_old_temporary_name_is_left_alone",
                PUBLISH + "test_a_SYMLINK_at_the_old_temporary_name_cannot_redirect_the_write"],
     "intended": "AssertionError"},
    {"label": "M3-the-final-name-is-replaced-rather-than-claimed",
     "file": "instance",
     "before": "        os.link(temporary, place)",
     "after": "        os.replace(temporary, place)",
     "checks": [PUBLISH + "test_an_existing_selector_is_left_exactly_as_it_was",
                AGAIN + "test_a_selector_appearing_BETWEEN_custody_and_publication_is_refused"],
     "intended": "not raised"},
    {"label": "M4-this-attempt-s-own-temporary-is-left-behind",
     "file": "instance",
     "before": "    finally:\n        _discard(temporary)",
     "after": "    finally:\n        pass",
     "checks": [PUBLISH + "test_a_REGULAR_file_at_the_old_temporary_name_is_left_alone"],
     "intended": "AssertionError"},
    {"label": "M5-the-selector-is-written-in-place-rather-than-renamed",
     "file": "instance",
     "before": "    temporary = _owned(place, document)\n    try:\n        os.replace(temporary, place)",
     "after": "    temporary = _owned(place, document)\n    try:\n        Path(place).write_text(Path(temporary).read_text())",
     "checks": [DERIVES + "test_publication_is_atomic"],
     "intended": "AssertionError"},
]


def caches():
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def restore():
    for place, text in PRISTINE.items():
        place.write_text(text)
    caches()


def target_of(probe):
    return BOOTSTRAP if probe["file"] == "bootstrap" else INSTANCE


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"] + list(names),
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:."))
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

restore()
restored, restore_seconds = run([MODULE.rstrip(".")])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-186742.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
