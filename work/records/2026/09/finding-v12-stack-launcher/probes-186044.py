"""W183883 claim186044 reversal probes for H1. Every probe must FAIL."""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

TREE = pathlib.Path(os.environ.get("W183883_PROBE_TREE",
                                   "/tmp/w183883-probes/tree")) / "v12"
B = TREE / "python" / "tools" / "bootstrap.py"
PRISTINE = B.read_text()

PROBES = [
 ("H1-the-existing-configuration-is-not-validated",
  '''        normalized = stage_execution.held_configuration(emitted)''',
  '''        normalized = dict(emitted, job_bindings=emitted.get("job_bindings") or [
            {"job_id": None, "job_work_id": emitted.get("job_work_id"),
             "review_work_id": emitted.get("review_work_id"),
             "line_declared_base": emitted.get("line_declared_base"),
             "canonical_target_id": emitted.get("canonical_target_id"),
             "source_worker_id": None}])''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_an_unsupported_schema_in_the_configuration_is_refused",
   "TheCustodyRecordIsEvidenceOrItIsNothing.test_a_changed_review_work_in_the_configuration_is_refused",
   "TheCustodyRecordIsEvidenceOrItIsNothing.test_a_changed_sole_producer_is_refused",
   "TheCustodyRecordIsEvidenceOrItIsNothing.test_a_malformed_nested_binding_is_refused_rather_than_escaping"]),

 ("H1-the-producer-identity-is-not-compared",
  '''        for member in ("line_declared_base", "canonical_target_id",
                       "source_worker_id"):''',
  '''        for member in ("line_declared_base", "canonical_target_id"):''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_changed_sole_producer_is_refused"]),

 ("H1-a-refused-configuration-is-treated-as-agreeing",
  '''    except ContractRefusal as refusal:
        return ("the configuration at " + str(place) + " is not one the manager "
                "would accept (" + refusal.message + "), so what it binds is "
                "unknown")''',
  '''    except ContractRefusal:
        return None''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_an_unsupported_schema_in_the_configuration_is_refused",
   "TheCustodyRecordIsEvidenceOrItIsNothing.test_a_malformed_nested_binding_is_refused_rather_than_escaping"]),

 ("H1-the-one-job-record-count-is-not-held",
  '''        if len(recorded) != 1:''',
  '''        if False:''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_configuration_binding_a_different_number_of_jobs_is_refused"]),

 ("H1-the-multi-job-key-sets-are-not-compared",
  '''        if set(bound) != set(recorded):''',
  '''        if False:''',
  ["TheCustodyRecordIsEvidenceOrItIsNothing.test_a_multi_job_configuration_binding_another_set_is_refused"]),
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
