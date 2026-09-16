"""W183883 claim185976 reversal probes for G1 and G2. Every probe must FAIL."""
import json, os, pathlib, shutil, subprocess, sys, time

TREE = pathlib.Path(os.environ.get("W183883_PROBE_TREE",
                                   "/tmp/w183883-probes/tree")) / "v12"
B = TREE / "python" / "tools" / "bootstrap.py"
PRISTINE = B.read_text()

PROBES = [
 ("G1-the-record-shape-is-not-validated",
  '''    problem = _malformed_record(held, place)
    if problem is not None:''',
  '''    problem = None
    if problem is not None:''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_binding_that_says_nothing_is_refused_rather_than_trusted",
   "TheCustodyRecordIsEvidenceOrItIsNothing.test_a_record_naming_no_bindings_is_refused",
   "TheCustodyRecordIsEvidenceOrItIsNothing.test_a_record_naming_no_readable_authority_is_refused"]),

 ("G1-a-binding-may-say-nothing",
  '''        absent = [name for name in _BINDING if type(binding.get(name)) is not str
                  or not binding[name]]''',
  '''        absent = []''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_binding_that_says_nothing_is_refused_rather_than_trusted"]),

 ("G1-a-binding-may-be-any-type",
  '''        if type(binding) is not dict:''',
  '''        if False:''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_binding_of_the_wrong_type_is_refused_rather_than_traversed"]),

 ("G1-only-the-members-that-are-there-are-compared",
  '''        for member in _BINDING:
            if record["bindings"][job_id].get(member) != binding.get(member):''',
  '''        for member in binding:
            if record["bindings"][job_id].get(member) != binding.get(member):''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_binding_that_says_nothing_is_refused_rather_than_trusted",
   "RepeatingIt.test_a_conflicting_binding_is_refused_and_nothing_is_rewritten"]),

 ("G1-the-emitted-configuration-is-never-read",
  '''    drifted = _drifted(places, held)
    if drifted is not None:''',
  '''    drifted = None
    if drifted is not None:''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_corrupt_emitted_configuration_is_refused_beside_a_good_record",
   "TheCustodyRecordIsEvidenceOrItIsNothing.test_a_missing_emitted_configuration_is_refused",
   "TheCustodyRecordIsEvidenceOrItIsNothing.test_a_configuration_that_disagrees_with_its_record_is_refused"]),

 ("G1-a-drifted-configuration-is-not-compared",
  '''        for name, value in bound[None].items():
            if previous.get(name) != value:''',
  '''        for name, value in bound[None].items():
            if False:''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_configuration_that_disagrees_with_its_record_is_refused"]),

 ("G1-a-configuration-naming-another-authority-passes",
  '''    if emitted.get("authority_uuid") != held["authority_uuid"]:''',
  '''    if False:''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_configuration_naming_another_authority_is_refused"]),

 ("G1-a-different-job-count-passes",
  '''        if len(recorded) != 1:''',
  '''        if False:''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_configuration_binding_a_different_number_of_jobs_is_refused"]),

 ("G2-an-explicit-null-is-dropped-again",
  '''        if name in document:
            built[name] = document[name]''',
  '''        if document.get(name) is not None:
            built[name] = document[name]''',
  ["AnOptionalSelectionTravelsOrIsRefused.test_an_explicit_null_is_refused_in_the_consumers_own_words",
   "AnOptionalSelectionTravelsOrIsRefused.test_a_selected_false_is_carried_as_false_rather_than_omitted"]),
]


def restore():
    B.write_text(PRISTINE)
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run(names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"]
        + ["tests.tools.test_bootstrap." + one for one in names],
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:."))
    return done, time.monotonic() - started


results, spent = [], 0.0
for label, before, after, names in PROBES:
    restore()
    text = B.read_text()
    assert before in text, "probe %s does not apply" % label
    B.write_text(text.replace(before, after, 1))
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    done, seconds = run(names)
    spent += seconds
    results.append({"probe": label, "checks": names, "returncode": done.returncode,
                    "failed_as_required": done.returncode != 0,
                    "seconds": round(seconds, 3)})
    print("%-52s %s  (%.2fs)" % (label, "FAILED (required)" if done.returncode
                                 else "PASSED -- PROVES NOTHING", seconds))
restore()
done, seconds = run(["EveryMissingInputIsNamedAtOnce", "TheInputContractIsClosed",
                     "WhatItRefusesBeforeItTouchesAnything",
                     "AnIncompleteDeploymentIsRefusedBeforeAnythingIsMade",
                     "WhatItDerives", "AnOptionalSelectionTravelsOrIsRefused",
                     "TheCustodyRecordIsEvidenceOrItIsNothing",
                     "WhatItComposesOnTheAuthority", "RepeatingIt"])
spent += seconds
print("restored tree:", "OK" if done.returncode == 0 else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probes": results, "restored_ok": done.returncode == 0,
     "probe_seconds": round(spent, 3),
     "all_failed_as_required": all(one["failed_as_required"] for one in results)},
    indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results), "seconds: %.3f" % spent)
