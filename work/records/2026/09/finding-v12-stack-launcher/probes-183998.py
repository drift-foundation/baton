"""W183883 reversal probes: revert one guard, run the checks that name it.

Every probe must FAIL. A probe that passes proves the guard was not held by
any check, which is a test gap or a redundant guard -- not a result.
"""
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time

# The tree these probes edit. It must be a COPY of the checkout's `v12/`, with
# `work/records/2026/08/finding-v12-isolated-agent-workers/findings/
# finding-v12-worker-contract/findings/finding-worker-control-api-manifests/
# evidence/vectors.json` present beside it, because the composition fixture
# reads that vector corpus. Never point this at the working tree: every probe
# deliberately breaks a guard.
TREE = pathlib.Path(os.environ.get("W183883_PROBE_TREE",
                                  "/tmp/w183883-probes/tree") ) / "v12"
MODULE = TREE / "python" / "tools" / "stack.py"
RECIPES = TREE / "justfile"
PRISTINE = {MODULE: MODULE.read_text(), RECIPES: RECIPES.read_text()}

PROBES = [
 ("R1-no-admission-lock", MODULE,
  '''    Path(root).mkdir(parents=True, exist_ok=True)
    handle = os.open(str(lock_path(root)),''',
  '''    Path(root).mkdir(parents=True, exist_ok=True)
    if True:
        yield
        return
    handle = os.open(str(lock_path(root)),''',
  ["Admission.test_a_second_start_cannot_enter_while_the_first_holds_admission",
   "Admission.test_a_stop_cannot_interleave_with_a_start"]),

 ("R1-orphan-on-record-failure", MODULE,
  '''    except BaseException:
        _reap(child)
        raise''',
  '''    except BaseException:
        raise''',
  ["Admission.test_a_spawn_that_cannot_be_recorded_leaves_no_orphan"]),

 ("R2-unknown-collapses-to-gone", MODULE,
  '''    if type(record) is not dict or record.get("unreadable"):
        return UNKNOWN''',
  '''    if type(record) is not dict or record.get("unreadable"):
        return GONE''',
  ["UnknownOwnership.test_an_unreadable_record_is_unknown_rather_than_gone",
   "UnknownOwnership.test_start_refuses_to_replace_an_owner_it_cannot_establish",
   "UnknownOwnership.test_stop_retains_an_unknown_record_and_reports_failure"]),

 ("R2-unreadable-identity-collapses", MODULE,
  '''    if type(pid) is not int or type(start) is not int or pid <= 0:''',
  '''    if False:''',
  ["UnknownOwnership.test_a_record_whose_identity_cannot_be_read_is_unknown"]),

 ("R2-denied-proc-read-is-absence", MODULE,
  '''    except OSError:
        return "unknown", None''',
  '''    except OSError:
        return "absent", None''',
  ["UnknownOwnership.test_the_proc_read_itself_tells_denial_from_absence"]),

 ("R2-denied-read-does-not-stop-a-start", MODULE,
  '''    state, observed = _proc(pid)
    if state == "absent":
        return GONE
    if state == "unknown":
        return UNKNOWN''',
  '''    state, observed = _proc(pid)
    if state == "absent":
        return GONE
    if state == "unknown":
        return GONE''',
  ["UnknownOwnership.test_a_denied_process_read_is_unknown_rather_than_absent",
   "UnknownOwnership.test_a_denied_process_read_also_stops_a_start"]),

 ("R2-a-zombie-reads-as-running", MODULE,
  '''    return GONE if state == "Z" else LIVE''',
  '''    return LIVE''',
  ["UnknownOwnership.test_a_terminated_but_unreaped_process_is_gone"]),

 ("R2-start-replaces-an-unknown-owner", MODULE,
  '''    unknown = [name for name in PROCESSES if held[name] == UNKNOWN]''',
  '''    unknown = []''',
  ["UnknownOwnership.test_start_refuses_to_replace_an_owner_it_cannot_establish",
   "UnknownOwnership.test_a_denied_process_read_also_stops_a_start"]),

 ("R3-no-package-path-for-children", MODULE,
  '''    wanted = [str(PACKAGE_PATH), str(DISTRIBUTION)]''',
  '''    wanted = []''',
  ["Readiness.test_the_child_environment_carries_this_distributions_package_path",
   "Readiness.test_the_documented_child_can_actually_import_its_package",
   "Readiness.test_the_monitors_child_can_import_the_same_package",
   "ValidIdleComposition.test_the_real_children_compose_an_empty_configured_stack"]),

 ("R3-no-readiness-gate-at-all", MODULE,
  '''        _await_ready(root, mark, ready_seconds=ready_seconds,
                     sleep=sleep, monotonic=monotonic)''',
  '''        pass''',
  ["Readiness.test_start_fails_with_the_childs_own_reason_when_it_exits_at_once",
   "Readiness.test_start_fails_when_nothing_is_ever_published",
   "ValidIdleComposition.test_a_deployment_that_does_not_compose_fails_the_start"]),

 ("R3-readiness-ignores-liveness", MODULE,
  '''            if held != LIVE:
                raise StackRefusal(
                    name + " did not stay up (" + held + "). Its log says:\\n"
                    + _log_tail(root, name))''',
  '''            if False:
                raise StackRefusal(name)''',
  ["Readiness.test_start_fails_with_the_childs_own_reason_when_it_exits_at_once"]),

 ("R3-any-snapshot-acknowledges", MODULE,
  '''        if current is not None and current != mark:''',
  '''        if current is not None:''',
  ["Readiness.test_a_previous_runs_snapshot_is_not_this_starts_acknowledgement"]),

 ("R3-unwind-clears-what-it-could-not-stop", MODULE,
  '''        if ownership(record) == LIVE:
            print("could not unwind %s pid %d (record retained)"
                  % (name, record["pid"]), file=stream)
            continue
        _collect(record["pid"])''',
  '''        if ownership(record) == LIVE:
            pass
        _collect(record["pid"])''',
  ["Readiness.test_an_unwind_that_cannot_take_a_process_back_retains_its_record"]),

 ("R3-recipes-drop-the-prerequisite", RECIPES,
  '''	cd python && PYTHONPATH=src:. python3 -m tools.stack start''',
  '''	cd python && python3 -m tools.stack start''',
  ["Readiness.test_every_recipe_that_runs_a_child_names_the_runtime_prerequisite"]),

 ("R4-stop-always-succeeds", MODULE,
  '''    if unresolved:
        print("unresolved: " + ", ".join(sorted(set(unresolved)))
              + "; this stack is NOT stopped", file=stream)
        return 1
    return 0''',
  '''    return 0''',
  ["Lifecycle.test_a_process_that_will_not_die_fails_the_stop",
   "UnknownOwnership.test_stop_retains_an_unknown_record_and_reports_failure"]),

 ("R4-stop-clears-an-unknown-record", MODULE,
  '''        if held == UNKNOWN:
            # [R2]/[R4]: the record stays, and this stop is NOT a success.
            print("unresolved ownership: %s (record retained at %s)"
                  % (name, _record(root, name)), file=stream)
            unresolved.append(name)
            continue''',
  '''        if held == UNKNOWN:
            clear_record(root, name)
            absent.append(name)
            continue''',
  ["UnknownOwnership.test_stop_retains_an_unknown_record_and_reports_failure"]),

 ("R4-no-runtime-boundary-reported", MODULE,
  '''    _print_runtime_boundary(runtime_boundary(root, now=now), stream)
    print("stores and evidence retained under the configured paths", file=stream)''',
  '''    print("stores and evidence retained under the configured paths", file=stream)''',
  ["RuntimeBoundary.test_stop_reports_what_it_did_not_resolve",
   "RuntimeBoundary.test_stop_without_a_snapshot_says_unknown_rather_than_none"]),

 ("R4-a-stale-snapshot-is-read-as-current", MODULE,
  '''    if age > PUBLISH_SECONDS * 3:
        return {"state": UNKNOWN, "snapshot_age_seconds": round(age, 3),
                "detail": "the last snapshot is %.1fs old" % age}''',
  '''    if False:
        pass''',
  ["RuntimeBoundary.test_a_stale_snapshot_is_unknown_rather_than_its_own_contents"]),

 ("R4-a-torn-snapshot-counts-as-zero", MODULE,
  '''    except (ValueError, OSError, KeyError, TypeError):
        return {"state": UNKNOWN, "snapshot_age_seconds": round(age, 3),''',
  '''    except (ValueError, OSError, KeyError, TypeError):
        jobs = []
        return {"state": "observed", "open_episodes": 0, "recorded_runtimes": 0,
                "snapshot_age_seconds": round(age, 3), "unused": (''',
  ["RuntimeBoundary.test_a_torn_snapshot_is_unknown_rather_than_zero"]),
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
restore()
for label, place, before, after, names in PROBES:
    restore()
    text = place.read_text()
    assert before in text, "probe %s does not apply" % label
    place.write_text(text.replace(before, after, 1))
    for cache in TREE.rglob("__pycache__"):
        shutil.rmtree(cache, ignore_errors=True)
    done, seconds = run(names)
    spent += seconds
    results.append({"probe": label, "checks": names, "returncode": done.returncode,
                    "failed_as_required": done.returncode != 0,
                    "seconds": seconds,
                    "tail": done.stderr.strip().splitlines()[-1:] })
    print("%-45s %s  (%.2fs)" % (label, "FAILED (required)" if done.returncode
                                 else "PASSED -- PROVES NOTHING", seconds))
restore()
done, seconds = run(["Admission", "UnknownOwnership", "Readiness",
                     "RuntimeBoundary", "Lifecycle", "Identity",
                     "Configuration", "SpawnedArgv", "Status", "Publication",
                     "Boundary", "ValidIdleComposition"])
spent += seconds
print("restored tree:", "OK" if done.returncode == 0 else "BROKEN")
TREE.parent / "results.json".write_text(
    json.dumps({"probes": results, "restored_ok": done.returncode == 0,
                "probe_seconds": round(spent, 3),
                "all_failed_as_required": all(one["failed_as_required"] for one in results)},
               indent=2, sort_keys=True))
print("probes:", len(results), "all failed as required:",
      all(one["failed_as_required"] for one in results),
      "seconds: %.3f" % spent)
