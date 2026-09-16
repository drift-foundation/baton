"""W183883 claim184239 reversal probes: revert one C1-C4 guard, run its checks.

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
MODULE = TREE / "python" / "tools" / "stack.py"
SERVER = TREE / "python" / "tools" / "job_manager.py"
PRISTINE = {MODULE: MODULE.read_text(), SERVER: SERVER.read_text()}

PROBES = [
 ("C1-stop-clears-on-anything-but-live", MODULE,
  '''        held = ownership(record)
        if held == LIVE:
            # Truthful rather than optimistic: the record stays so a later stop''',
  '''        held = ownership(record)
        if False:
            # Truthful rather than optimistic: the record stays so a later stop''',
  ["VisibilityLostDuringCleanup.test_stop_does_not_announce_a_process_it_can_no_longer_see"]),

 ("C1-stop-does-not-require-positive-gone", MODULE,
  '''        if held != GONE:
            # [C1]: `unknown` AFTER SIGNALLING IS NOT COMPLETION.''',
  '''        if False:
            # [C1]: `unknown` AFTER SIGNALLING IS NOT COMPLETION.''',
  ["VisibilityLostDuringCleanup.test_stop_does_not_announce_a_process_it_can_no_longer_see"]),

 ("C1-unwind-does-not-require-positive-gone", MODULE,
  '''        held = ownership(record)
        if held != GONE:
            # [C1]: ONLY A POSITIVE `gone` CLEARS A RECORD.''',
  '''        held = ownership(record)
        if held == LIVE:
            # [C1]: ONLY A POSITIVE `gone` CLEARS A RECORD.''',
  ["VisibilityLostDuringCleanup.test_a_failed_start_does_not_take_back_what_it_can_no_longer_see",
   "EveryFailedAdmissionUnwinds.test_cleanup_after_an_ordinary_failure_still_keeps_unknown_ownership"]),

 ("C2-only-a-refusal-unwinds", MODULE,
  '''    except BaseException:
        # [C2]: EVERY FAILED ADMISSION UNWINDS, not only a refusal.''',
  '''    except StackRefusal:
        # [C2]: EVERY FAILED ADMISSION UNWINDS, not only a refusal.''',
  ["EveryFailedAdmissionUnwinds.test_a_publisher_spawn_failure_takes_the_manager_back",
   "EveryFailedAdmissionUnwinds.test_a_publisher_record_failure_takes_the_manager_back_too",
   "EveryFailedAdmissionUnwinds.test_cleanup_after_an_ordinary_failure_still_keeps_unknown_ownership"]),

 ("C3-readiness-needs-no-serving-acknowledgement", MODULE,
  '''        pending = [record for record in expecting if not acknowledged(record)]''',
  '''        pending = []''',
  ["ServingAcknowledgement.test_a_manager_that_never_acknowledges_fails_the_start",
   "ServingAcknowledgement.test_a_previous_runs_acknowledgement_does_not_answer_for_this_start",
   "ServingAcknowledgement.test_an_acknowledgement_naming_another_incarnation_is_not_this_ones"]),

 ("C3-acknowledgement-ignores-the-incarnation", MODULE,
  '''    wanted = (SERVING_ACKNOWLEDGEMENT + repr(named)).encode()''',
  '''    wanted = SERVING_ACKNOWLEDGEMENT.encode()''',
  ["ServingAcknowledgement.test_an_acknowledgement_naming_another_incarnation_is_not_this_ones"]),

 ("C3-acknowledgement-ignores-the-log-offset", MODULE,
  '''            handle.seek(record.get("log_from") or 0)''',
  '''            handle.seek(0)''',
  ["ServingAcknowledgement.test_a_previous_runs_acknowledgement_does_not_answer_for_this_start"]),

 ("C3-every-start-reuses-one-incarnation", MODULE,
  '''    return "v12-stack-%d-%d" % (os.getpid(), time.time_ns())''',
  '''    return "v12-stack-%d" % os.getpid()''',
  ["ServingAcknowledgement.test_every_manager_start_is_given_a_fresh_incarnation"]),

 ("C3-the-serving-loop-says-nothing", SERVER,
  '''                print(f"serving initialization complete: "
                      f"incarnation={taken.incarnation!r} "
                      f"operations={taken.operations!r}",
                      file=sys.stderr, flush=True)''',
  '''                pass''',
  ["ValidIdleComposition.test_the_real_children_compose_an_empty_configured_stack"]),

 ("C4-traverse-without-validating", MODULE,
  '''    problem = _malformed(document)
    if problem is not None:''',
  '''    problem = None
    if problem is not None:''',
  ["MalformedSnapshots.test_every_nested_shape_is_refused_before_it_is_walked",
   "MalformedSnapshots.test_a_stop_over_a_malformed_snapshot_does_not_crash_after_signalling"]),

 ("C4-any-schema-is-a-status-document", MODULE,
  '''    if document.get("schema") != STATUS_SCHEMA:''',
  '''    if False:''',
  ["Status.test_a_document_of_another_schema_is_unreadable_not_empty"]),

 ("C4-no-observation-time-is-required", MODULE,
  '''    if _instant(document.get("observed_at")) is None:''',
  '''    if False:''',
  ["MalformedSnapshots.test_a_document_that_never_says_when_it_looked_is_unreadable"]),

 ("C4-freshness-ignores-the-observation-time", MODULE,
  '''    oldest = max(observed, published)''',
  '''    oldest = published''',
  ["Status.test_a_freshly_written_document_can_still_be_stalely_observed",
   "MalformedSnapshots.test_a_freshly_written_but_stalely_observed_document_is_unknown"]),

 ("C4-a-partial-observation-speaks-for-every-job", MODULE,
  '''    if not answer["canonical"]:''',
  '''    if False:''',
  ["MalformedSnapshots.test_a_non_canonical_snapshot_cannot_say_what_is_not_executing"]),

 ("C4-the-pinned-schema-may-drift", MODULE,
  '''STATUS_SCHEMA = "baton.v12.job-status/5"''',
  '''STATUS_SCHEMA = "baton.v12.job-status/4"''',
  ["Status.test_the_pinned_status_schema_is_the_one_the_manager_writes"]),
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
        + ["tests.tools.test_stack." + one for one in names],
        cwd=str(TREE / "python"), capture_output=True, text=True, timeout=900)
    return done, time.monotonic() - started


results, spent = [], 0.0
for label, place, before, after, names in PROBES:
    restore()
    text = place.read_text()
    assert before in text, "probe %s does not apply" % label
    place.write_text(text.replace(before, after, 1))
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    done, seconds = run(names)
    spent += seconds
    results.append({"probe": label, "file": place.name, "checks": names,
                    "returncode": done.returncode,
                    "failed_as_required": done.returncode != 0,
                    "seconds": round(seconds, 3)})
    print("%-48s %s  (%.2fs)" % (label, "FAILED (required)" if done.returncode
                                 else "PASSED -- PROVES NOTHING", seconds))
restore()
done, seconds = run(["Admission", "UnknownOwnership", "Readiness", "RuntimeBoundary",
                     "Lifecycle", "Identity", "Configuration", "SpawnedArgv",
                     "Status", "Publication", "Boundary", "ValidIdleComposition",
                     "VisibilityLostDuringCleanup", "EveryFailedAdmissionUnwinds",
                     "ServingAcknowledgement", "MalformedSnapshots"])
spent += seconds
print("restored tree:", "OK" if done.returncode == 0 else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probes": results, "restored_ok": done.returncode == 0,
     "probe_seconds": round(spent, 3),
     "all_failed_as_required": all(one["failed_as_required"] for one in results)},
    indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results), "seconds: %.3f" % spent)
