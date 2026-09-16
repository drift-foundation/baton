"""W183883 claim185884 reversal probes for F1, F2 and F3.

Every probe must FAIL. A probe that passes proves the guard is held by no
check, which is a test gap or a redundant guard -- not a result.
"""
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
PRISTINE = {B: B.read_text()}

PROBES = [
 # -- F1: the emitted configuration is validated ---------------------------
 ("F1-the-emitted-configuration-is-never-validated",
  '''        stage_execution.held_configuration(configured)''',
  '''        pass''',
  ["AnIncompleteDeploymentIsRefusedBeforeAnythingIsMade.test_the_missing_worker_members_are_named_and_nothing_is_created",
   "WhatItDerives.test_the_generated_deployment_is_one_the_manager_accepts"]),

 ("F1-validation-happens-after-the-authority-is-composed",
  '''    principals = principals_for(places, document, opener=opener)
    configured = validated(configuration(document, principals))''',
  '''    principals = principals_for(places, document, opener=opener)
    configured = configuration(document, principals)''',
  ["AnIncompleteDeploymentIsRefusedBeforeAnythingIsMade.test_the_missing_worker_members_are_named_and_nothing_is_created"]),

 ("F1-the-schema-is-chosen-by-job-count-alone",
  '''    one_each = all(len(by_role.get(role, [])) == 1 for role in ROLES)''',
  '''    one_each = True''',
  ["WhatItDerives.test_one_job_with_a_larger_pool_is_still_the_multi_job_schema"]),

 ("F1-the-derived-identities-are-not-in-what-is-validated",
  '''        if principals is not None:
            deployment["principal"] = principals[one["participant"]]''',
  '''        if False:
            deployment["principal"] = principals[one["participant"]]''',
  ["WhatItDerives.test_the_generated_deployment_is_one_the_manager_accepts",
   "WhatItDerives.test_every_principal_is_derived_rather_than_configured"]),

 # -- F2: a repeat preserves what is there ---------------------------------
 ("F2-an-unreadable-record-reads-as-absent",
  '''    if held.get("unreadable"):''',
  '''    if False:''',
  ["RepeatingIt.test_a_corrupt_record_is_refused_rather_than_overwritten",
   "RepeatingIt.test_a_configuration_with_no_record_is_refused",
   "RepeatingIt.test_a_record_of_another_schema_is_refused"]),

 ("F2-a-configuration-with-no-record-is-a-clean-root",
  '''        if emitted.exists():
            return {"unreadable": True,''',
  '''        if False:
            return {"unreadable": True,''',
  ["RepeatingIt.test_a_configuration_with_no_record_is_refused"]),

 ("F2-a-removed-job-is-not-noticed",
  '''        if job_id not in record["bindings"]:''',
  '''        if False:''',
  ["RepeatingIt.test_a_removed_job_is_refused_across_a_schema_change"]),

 ("F2-a-changed-binding-is-not-noticed",
  '''            if record["bindings"][job_id].get(member) != value:''',
  '''            if False:''',
  ["RepeatingIt.test_a_conflicting_binding_is_refused_and_nothing_is_rewritten",
   "RepeatingIt.test_a_changed_declared_base_is_refused_too"]),

 ("F2-the-conflict-is-settled-after-the-authority-is-read",
  '''    record = record_of(document)
    found = conflicts(places, record)''',
  '''    record = record_of(document)
    found = []''',
  ["RepeatingIt.test_the_conflict_is_found_before_the_authority_is_composed",
   "RepeatingIt.test_a_conflicting_authority_is_refused"]),

 ("F2-publication-is-not-atomic",
  '''    temporary = Path(str(place) + ".tmp")
    temporary.write_text(json.dumps(document, indent=2, sort_keys=True) + "\\n")
    os.replace(temporary, place)''',
  '''    Path(place).write_text(json.dumps(document, indent=2, sort_keys=True) + "\\n")''',
  ["RepeatingIt.test_both_documents_are_published_atomically"]),

 # -- F3: the input contract is closed -------------------------------------
 ("F3-the-input-member-set-is-open",
  '''    found = _unknown(document)
    if found:''',
  '''    found = []
    if found:''',
  ["TheInputContractIsClosed.test_an_unsupported_top_level_member_is_refused_by_name",
   "TheInputContractIsClosed.test_a_misspelled_member_is_refused_rather_than_ignored",
   "TheInputContractIsClosed.test_an_unsupported_nested_member_is_refused"]),

 ("F3-nested-wrappers-are-not-closed",
  '''    for index, worker in enumerate(document.get("workers") or []):
        if type(worker) is dict:
            found += ["workers[%d].%s" % (index, name) for name in worker
                      if name not in _WORKER]''',
  '''    for index, worker in enumerate(document.get("workers") or []):
        if False:
            pass''',
  ["TheInputContractIsClosed.test_an_unsupported_nested_member_is_refused"]),

 ("F3-a-supported-selection-is-dropped",
  '''    for name in OPTIONAL:
        if document.get(name) is not None:
            built[name] = document[name]''',
  '''    for name in ("integration_target", "integration_workspace"):
        if document.get(name) is not None:
            built[name] = document[name]''',
  ["WhatItDerives.test_a_supported_optional_selection_reaches_the_configuration"]),
]


def restore():
    for place, content in PRISTINE.items():
        place.write_text(content)
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
                     "WhatItDerives", "WhatItComposesOnTheAuthority",
                     "RepeatingIt"])
spent += seconds
print("restored tree:", "OK" if done.returncode == 0 else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probes": results, "restored_ok": done.returncode == 0,
     "probe_seconds": round(spent, 3),
     "all_failed_as_required": all(one["failed_as_required"] for one in results)},
    indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results), "seconds: %.3f" % spent)
