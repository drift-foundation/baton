"""W183883 claim189383 — reversal probes for the version stamp.

OWNER-VERSION-STAMP-20260916.md: one authoritative application version, a
commit and dirty flag CAPTURED at packaging time, an unknown that is never
reported as clean, and a bootstrap source inferred from the repository that
contains v12/justfile rather than from the caller's cwd.

Every probe proves a PASSING BASELINE on pristine code first [J1].

Run against an isolated COPY of the tree. Nothing here edits the checkout.
"""
import json, os, pathlib, shutil, subprocess, sys, time

HERE = pathlib.Path("/home/sl/src/baton/v12")
TREE = pathlib.Path(os.environ.get(
    "W183883_PROBE_TREE", "/tmp/w183883-probes-189383")) / "v12"
SKIP = {".venv", "dist", "build", "__pycache__", ".pytest_cache"}

if TREE.exists():
    shutil.rmtree(TREE)
TREE.parent.mkdir(parents=True, exist_ok=True)
shutil.copytree(HERE, TREE, ignore=shutil.ignore_patterns(*SKIP), symlinks=True)
link = TREE.parent / "work"
if not link.exists():
    os.symlink("/home/sl/src/baton/work", link)

FILES = {"version": TREE / "python" / "src" / "baton_v12" / "version.py",
         "stamp": TREE / "python" / "tools" / "build_stamp.py",
         "command": TREE / "python" / "tools" / "stack_command.py",
         "bootstrap": TREE / "python" / "tools" / "bootstrap.py"}
PRISTINE = {place: place.read_text() for place in FILES.values()}

BANNER = "tests.tools.test_version.TheBannerSaysWhatIsKnown."
STAMP = "tests.tools.test_version.TheStampIsCapturedFromTheCheckout."
COMMAND = "tests.tools.test_version.TheCommandAnswersWithoutAnythingElse."
ONCE = "tests.tools.test_version.TheVersionIsWrittenOnce."
REPOS = "tests.tools.test_instance.TheBootstrapPreparesTheRepositories."

PROBES = [
    {"label": "A1-an-unknown-commit-is-reported-as-a-clean-build",
     "file": "version",
     "before": '    if not stamp or not stamp.get("commit"):',
     "after": "    if False:",
     "checks": [BANNER + "test_an_unknown_commit_is_not_a_clean_one",
                BANNER + "test_no_stamp_at_all_is_still_unknown_rather_than_clean"],
     "intended": "AssertionError"},
    {"label": "A2-a-dirty-build-does-not-say-so",
     "file": "version",
     "before": '        if stamp.get("dirty") is True:',
     "after": "        if False:",
     "checks": [BANNER + "test_a_dirty_build_is_allowed_and_says_so"],
     "intended": "AssertionError"},
    {"label": "A3-an-unreadable-tree-state-is-called-clean",
     "file": "stamp",
     "before": '    if said is None:\n'
               '        stamp["detail"] = "the repository tool could not report the tree state"\n'
               '        return stamp',
     "after": '    if said is None:\n        said = ""',
     "checks": [STAMP + "test_a_readable_commit_with_an_unreadable_status_is_unknown_too"],
     "intended": "AssertionError"},
    {"label": "A4-the-checkout-is-found-from-the-caller-s-cwd",
     "file": "stamp",
     "before": '    here = Path(start or __file__).resolve()',
     "after": '    here = Path(start or os.getcwd()).resolve()',
     "checks": [STAMP + "test_the_checkout_is_found_from_THIS_file_not_the_cwd"],
     "intended": "AssertionError"},
    {"label": "A5-version-is-answered-only-after-the-subcommand-parser",
     "file": "command",
     "before": '    if argv and argv[0] in ("-V", "--version"):\n        return _version()',
     "after": "    pass",
     "checks": [COMMAND + "test_it_answers_and_exits_zero",
                COMMAND + "test_it_is_answered_BEFORE_the_subcommand_parser"],
     # Reverted, argparse refuses `--version` as a subcommand and the command
     # exits 2; the intended failure is that exit, not an exception.
     "intended": "2 != 0"},
    {"label": "A6-the-metadata-repeats-the-version-literal",
     "file": "version",
     "before": 'VERSION = "12.0.0"',
     "after": 'VERSION = "12.0.1"',
     "checks": [ONCE + "test_the_module_states_it_and_nothing_else_does"],
     "intended": "AssertionError"},
    {"label": "A7-a-superseded-input-member-is-silently-ignored",
     "file": "bootstrap",
     "before": '    found = [name + " -- " + SUPERSEDED[name] if name in SUPERSEDED else name\n'
               '             for name in document if name not in allowed]',
     "after": '    found = [name for name in document\n'
              '             if name not in allowed and name not in SUPERSEDED]',
     "checks": [REPOS + "test_a_document_that_still_names_a_source_is_REFUSED_by_name"],
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
restored, restore_seconds = run(["tests.tools.test_version",
                                 "tests.tools.test_instance"])
spent += restore_seconds
print("restored:", "OK" if restored.returncode == 0 else "BROKEN")
(TREE.parent / "results-189383.json").write_text(json.dumps(
    {"probes": results, "restored_ok": restored.returncode == 0,
     "all_killed": all(one["valid_kill"] for one in results),
     "total_seconds": round(spent, 3)}, indent=2, sort_keys=True))
print("all probes killed:", all(one["valid_kill"] for one in results))
