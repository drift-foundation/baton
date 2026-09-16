"""W183883 claim185774 reversal probes for E1, E2 and the bootstrap.

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
E = TREE / "python" / "tools" / "environment.py"
B = TREE / "python" / "tools" / "bootstrap.py"
J = TREE / "justfile"
PRISTINE = {E: E.read_text(), B: B.read_text(), J: J.read_text()}

PROBES = [
 # -- E1 -------------------------------------------------------------------
 ("E1-the-recipe-takes-a-named-option", J, "environment",
  '''	cd python && python3 -m tools.environment --python "{{PY}}" setup''',
  '''	cd python && python3 -m tools.environment --python "PY={{PY}}" setup''',
  ["TheInterpreterOverrideIsExecutable.test_a_positional_interpreter_reaches_the_helper_as_a_path"]),

 ("E1-the-refusal-recommends-the-broken-spelling", E, "environment",
  '''". Name one with `just setup /path/to/python3`.")''',
  '''". Name one with `just setup PY=/path/to/python3`.")''',
  ["TheInterpreterOverrideIsExecutable.test_nothing_recommends_the_spelling_that_does_not_work"]),

 # -- E2 -------------------------------------------------------------------
 ("E2-ownership-is-published-only-after-the-install", E, "environment",
  '''        _publish(root, version, installed=False, now=now)''',
  '''        pass''',
  ["AnInterruptedSetupResumes.test_a_failed_first_install_leaves_a_resumable_environment",
   "AnInterruptedSetupResumes.test_the_retry_resumes_without_recreating_the_environment"]),

 ("E2-an-incomplete-environment-reads-as-ready", E, "environment",
  '''    if not marker.get("installed"):''',
  '''    if False:''',
  ["AnInterruptedSetupResumes.test_an_incomplete_environment_is_not_admitted_as_ready",
   "AnInterruptedSetupResumes.test_a_failed_first_install_leaves_a_resumable_environment"]),

 ("E2-ready-is-published-before-the-install-succeeds", E, "environment",
  '''    _install(root, runner=runner)
    # AND READY ONLY NOW, after the locked install actually succeeded.
    _publish(root, version, installed=True, now=now)''',
  '''    _publish(root, version, installed=True, now=now)
    _install(root, runner=runner)''',
  ["AnInterruptedSetupResumes.test_ready_is_published_only_after_the_install_succeeds"]),

 ("E2-resumability-becomes-acceptance", E, "environment",
  '''    if marker is None or marker.get("unreadable"):''',
  '''    if False:''',
  ["AnInterruptedSetupResumes.test_a_genuinely_foreign_directory_is_still_refused",
   "WhatItSeesThere.test_a_directory_this_setup_did_not_create_is_foreign"]),

 # -- the bootstrap --------------------------------------------------------
 ("B-missing-inputs-are-not-named", B, "bootstrap",
  '''    absent = _missing(document)
    if absent:''',
  '''    absent = []
    if absent:''',
  ["EveryMissingInputIsNamedAtOnce.test_an_empty_document_names_every_operand_it_needs",
   "EveryMissingInputIsNamedAtOnce.test_a_missing_member_inside_a_worker_or_job_is_named_by_position"]),

 ("B-a-state-root-inside-the-checkout-is-accepted", B, "bootstrap",
  '''    if resolved == checkout or resolved.startswith(checkout.rstrip("/") + "/"):''',
  '''    if False:''',
  ["WhatItRefusesBeforeItTouchesAnything.test_a_state_root_inside_the_checkout_is_refused"]),

 ("B-implementation-may-review-itself", B, "bootstrap",
  '''    shared = producers & reviewers''',
  '''    shared = set()''',
  ["WhatItRefusesBeforeItTouchesAnything.test_implementation_and_review_may_share_no_participant"]),

 ("B-a-job-may-name-any-producer", B, "bootstrap",
  '''        if job["source_worker_id"] not in producing:''',
  '''        if False:''',
  ["WhatItRefusesBeforeItTouchesAnything.test_a_job_naming_a_producer_that_is_not_configured_is_refused"]),

 ("B-every-deployment-is-written-as-multi-job", B, "bootstrap",
  '''        "schema": ONE_JOB_SCHEMA if len(jobs) == 1 else MULTI_JOB_SCHEMA,
        "authority_store": places["authority_store"],''',
  '''        "schema": MULTI_JOB_SCHEMA,
        "authority_store": places["authority_store"],''',
  ["WhatItDerives.test_one_job_is_written_as_the_one_job_schema"]),

 ("B-a-binding-may-carry-two-different-works", B, "bootstrap",
  '''             "review_work_id": job["work_id"],''',
  '''             "review_work_id": job["work_id"] + "-review",''',
  ["WhatItDerives.test_each_binding_carries_one_work_on_both_axes"]),

 ("B-principals-are-not-written-into-the-document", B, "bootstrap",
  '''                worker["deployment"] = dict(
                    worker["deployment"],
                    participant=supplied["participant"],
                    principal=principals[supplied["participant"]],''',
  '''                worker["deployment"] = dict(
                    worker["deployment"],
                    participant=supplied["participant"],''',
  ["WhatItDerives.test_every_principal_is_derived_rather_than_configured"]),

 ("B-no-grants-are-issued", B, "bootstrap",
  '''        for name, capability in GRANTS.items():''',
  '''        for name, capability in {}.items():''',
  ["WhatItComposesOnTheAuthority.test_each_job_gets_its_work_its_routes_and_its_four_grants"]),

 ("B-a-conflicting-binding-is-rewritten", B, "bootstrap",
  '''    found = conflicts(places, configured)
    if found:''',
  '''    found = []
    if found:''',
  ["RepeatingIt.test_a_conflicting_binding_is_refused_and_nothing_is_rewritten",
   "RepeatingIt.test_a_conflicting_authority_is_refused",
   "RepeatingIt.test_the_conflict_is_found_before_the_authority_is_even_opened"]),

 ("B-the-conflict-is-found-after-the-authority-is-opened", B, "bootstrap",
  '''    # BEFORE ANYTHING DURABLE, like every other check above it.
    found = conflicts(places, configured)''',
  '''    found = []''',
  ["RepeatingIt.test_the_conflict_is_found_before_the_authority_is_even_opened"]),

 ("B-capacity-is-reported-as-a-concurrency-guarantee", B, "bootstrap",
  '''            "job_affinity": {job["job_id"]: job["source_worker_id"]
                             for job in jobs},''',
  '''            "job_affinity": {},''',
  ["WhatItDerives.test_capacity_is_what_is_configured_rather_than_a_concurrency_claim"]),
]


def restore():
    for place, content in PRISTINE.items():
        place.write_text(content)
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run(module, names):
    started = time.monotonic()
    done = subprocess.run(
        [sys.executable, "-B", "-m", "unittest"]
        + ["tests.tools.test_%s.%s" % (module, one) for one in names],
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=600,
        env=dict(os.environ, PYTHONPATH="src:."))
    return done, time.monotonic() - started


results, spent = [], 0.0
for label, place, module, before, after, names in PROBES:
    restore()
    text = place.read_text()
    assert before in text, "probe %s does not apply" % label
    place.write_text(text.replace(before, after, 1))
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    done, seconds = run(module, names)
    spent += seconds
    results.append({"probe": label, "file": place.name, "module": module,
                    "checks": names, "returncode": done.returncode,
                    "failed_as_required": done.returncode != 0,
                    "seconds": round(seconds, 3)})
    print("%-52s %s  (%.2fs)" % (label, "FAILED (required)" if done.returncode
                                 else "PASSED -- PROVES NOTHING", seconds))
restore()
one, seconds = run("environment", ["WhereItLives", "WhatItSeesThere",
                                   "NamingTheInterpreter", "PreparingIt",
                                   "TheRecipesUseIt",
                                   "TheInterpreterOverrideIsExecutable",
                                   "AnInterruptedSetupResumes"])
spent += seconds
other, seconds = run("bootstrap", ["EveryMissingInputIsNamedAtOnce",
                                   "WhatItRefusesBeforeItTouchesAnything",
                                   "WhatItDerives",
                                   "WhatItComposesOnTheAuthority", "RepeatingIt"])
spent += seconds
ok = one.returncode == 0 and other.returncode == 0
print("restored tree:", "OK" if ok else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probes": results, "restored_ok": ok, "probe_seconds": round(spent, 3),
     "all_failed_as_required": all(one["failed_as_required"] for one in results)},
    indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results), "seconds: %.3f" % spent)
