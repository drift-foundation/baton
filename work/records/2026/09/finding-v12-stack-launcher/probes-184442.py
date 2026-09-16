"""W183883 claim184442 reversal probes for D1/D2. Every probe must FAIL."""
import json, os, pathlib, shutil, subprocess, sys, time

TREE = pathlib.Path(os.environ.get("W183883_PROBE_TREE",
                                   "/tmp/w183883-probes/tree")) / "v12"
M = TREE / "python" / "tools" / "stack.py"
PRISTINE = M.read_text()

PROBES = [
 ("D1-register-for-rollback-after-a-second-write",
  '''        record.update(extra or {})
        write_record(root, name, record)''',
  '''        write_record(root, name, record)
        if extra:
            record.update(extra)
            write_record(root, name, record)''',
  ["EveryRecordWriteIsInsideTheRollback.test_the_spawned_identity_is_published_in_one_write",
   "EveryRecordWriteIsInsideTheRollback.test_start_adds_no_record_write_of_its_own_after_a_spawn"]),

 ("D1-a-record-failure-leaves-the-process",
  '''    except BaseException:
        _reap(child)
        raise''',
  '''    except BaseException:
        raise''',
  ["EveryRecordWriteIsInsideTheRollback.test_a_record_write_failure_still_rolls_the_process_back",
   "Admission.test_a_spawn_that_cannot_be_recorded_leaves_no_orphan"]),

 ("D1-one-failed-unwind-stops-the-rest",
  '''        try:
            _take_back(root, record, stream)
        except BaseException as failure:                     # noqa: BLE001''',
  '''        try:
            _take_back(root, record, stream)
        except StackRefusal as failure:''',
  ["EveryRecordWriteIsInsideTheRollback.test_one_process_that_cannot_be_unwound_does_not_hide_the_others"]),

 ("D1-the-acknowledgement-is-cached-in-the-record",
  '''    for record in started:
        print("started: %s pid %d" % (record["name"], record["pid"]), file=stream)''',
  '''    for record in started:
        print("started: %s pid %d" % (record["name"], record["pid"]), file=stream)
        if record.get("incarnation"):
            write_record(root, record["name"],
                         dict(record, serving_acknowledged=True))''',
  ["EveryRecordWriteIsInsideTheRollback.test_nothing_is_written_to_a_record_after_a_start_succeeds",
   "EveryRecordWriteIsInsideTheRollback.test_start_adds_no_record_write_of_its_own_after_a_spawn"]),

 ("D2-an-existing-live-manager-needs-no-evidence",
  '''    if held[MANAGER] == LIVE and not acknowledged(running[MANAGER]):
        expecting.append(running[MANAGER])''',
  '''    if False:
        expecting.append(running[MANAGER])''',
  ["AnExistingManagerNeedsEvidenceToo.test_both_live_but_unacknowledged_is_not_ready",
   "AnExistingManagerNeedsEvidenceToo.test_replacing_only_the_publisher_still_needs_the_managers_evidence",
   "AnExistingManagerNeedsEvidenceToo.test_a_repeated_start_waits_bounded_and_then_refuses"]),

 ("D2-both-live-returns-without-waiting",
  '''        if expecting:
            _await_ready(root, None, expecting, started=[],
                         require_snapshot=False, ready_seconds=ready_seconds,
                         sleep=sleep, monotonic=monotonic)''',
  '''        if False:
            pass''',
  ["AnExistingManagerNeedsEvidenceToo.test_both_live_but_unacknowledged_is_not_ready",
   "AnExistingManagerNeedsEvidenceToo.test_an_existing_manager_that_acknowledges_late_is_waited_for"]),

 ("D2-an-inherited-manager-is-not-named-in-the-refusal",
  '''                    + ("" if not inherited else''',
  '''                    + ("" if True else''',
  ["AnExistingManagerNeedsEvidenceToo.test_both_live_but_unacknowledged_is_not_ready",
   "AnExistingManagerNeedsEvidenceToo.test_a_repeated_start_waits_bounded_and_then_refuses"]),

 ("D2-an-acknowledged-manager-is-re-proved",
  '''    if held[MANAGER] == LIVE and not acknowledged(running[MANAGER]):''',
  '''    if held[MANAGER] == LIVE:''',
  ["AnExistingManagerNeedsEvidenceToo.test_an_acknowledged_manager_is_never_asked_to_initialize_again",
   "Lifecycle.test_a_repeated_start_does_not_duplicate_the_manager"]),

 ("D2-a-first-start-skips-the-observation-check",
  '''            if not require_snapshot:''',
  '''            if mark is None:''',
  ["Readiness.test_start_fails_when_nothing_is_ever_published",
   "EveryRecordWriteIsInsideTheRollback.test_one_process_that_cannot_be_unwound_does_not_hide_the_others"]),
]


def restore():
    M.write_text(PRISTINE)
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)


def run(names):
    started = time.monotonic()
    done = subprocess.run([sys.executable, "-B", "-m", "unittest"]
                          + ["tests.tools.test_stack." + one for one in names],
                          cwd=str(TREE / "python"), capture_output=True,
                          text=True, timeout=900)
    return done, time.monotonic() - started


results, spent = [], 0.0
for label, before, after, names in PROBES:
    restore()
    text = M.read_text()
    assert before in text, "probe %s does not apply" % label
    M.write_text(text.replace(before, after, 1))
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
done, seconds = run(["Admission", "UnknownOwnership", "Readiness", "RuntimeBoundary",
                     "Lifecycle", "Identity", "Configuration", "SpawnedArgv", "Status",
                     "Publication", "Boundary", "ValidIdleComposition",
                     "VisibilityLostDuringCleanup", "EveryFailedAdmissionUnwinds",
                     "ServingAcknowledgement", "MalformedSnapshots",
                     "EveryRecordWriteIsInsideTheRollback",
                     "AnExistingManagerNeedsEvidenceToo"])
spent += seconds
print("restored tree:", "OK" if done.returncode == 0 else "BROKEN")
(TREE.parent / "results.json").write_text(json.dumps(
    {"probes": results, "restored_ok": done.returncode == 0,
     "probe_seconds": round(spent, 3),
     "all_failed_as_required": all(one["failed_as_required"] for one in results)},
    indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results), "seconds: %.3f" % spent)
