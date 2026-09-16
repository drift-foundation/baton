"""W183883 claim186672 — reversal probes for the destination-custody gates.

Review 2026-09-16T13-09-22Z showed that carrying the admission fixed one half
and opened the other: install believed a destination it had not looked at since. These probes ask the only
question that settles whether they are held: with one guard reverted, does a
named check fail, and does it fail on the assertion it is about?

Every probe proves a PASSING BASELINE on pristine code first [J1]. A probe that
cannot pass before the reversal measures nothing.

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-186672")) / "v12"
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

PROBES = [
    {"label": "L1-install-believes-the-destination-it-admitted",
     "file": "bootstrap",
     "before": "        custody(places, destination)\n",
     "after": "",
     "checks": [AGAIN + "test_a_STATE_LINK_that_appears_after_admission_is_refused"],
     # Reverted, install ACCEPTS the foreign link and publishes; the intended
     # failure is the refusal that never came.
     "intended": "BootstrapRefusal not raised"},
    {"label": "L2-publication-replaces-whatever-is-there",
     "file": "bootstrap",
     "before": '                instance.create(places["instance"], selector)',
     "after":  '                instance.publish(places["instance"], selector)',
     # NOT the selector that is there BEFORE install: `custody` refuses that
     # one, so reverting the publication would not show. The interval between
     # custody and publication is the only thing this guard owns.
     "checks": [AGAIN + "test_a_selector_appearing_BETWEEN_custody_and_publication_is_refused"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "L3-the-exclusive-link-becomes-an-atomic-replacement",
     "file": "instance",
     "before": "        os.link(temporary, place)",
     "after":  "        os.replace(temporary, place)",
     "checks": [PUBLISH + "test_an_existing_selector_is_left_exactly_as_it_was",
                PUBLISH + "test_a_DANGLING_link_is_not_written_through_either"],
     "intended": "InstanceRefusal not raised"},
    {"label": "L4-cooperating-attempts-do-not-serialize",
     "file": "bootstrap",
     "before": "    with serialized(places, wait):",
     "after":  "    with contextlib.nullcontext():",
     "checks": [AGAIN + "test_a_cooperating_bootstrap_holding_the_destination_is_waited_for"],
     "intended": "BootstrapRefusal not raised"},
    {"label": "L5-a-refused-attempt-leaves-its-own-copy-behind",
     "file": "bootstrap",
     "before": '            shutil.rmtree(places["distro"], ignore_errors=True)\n            raise',
     "after":  '            raise',
     "checks": [AGAIN + "test_a_selector_appearing_BETWEEN_custody_and_publication_is_refused"],
     # The copy only HAPPENS when the refusal comes after it.
     "intended": "is not false"},
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
(TREE.parent / "results-186672.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
