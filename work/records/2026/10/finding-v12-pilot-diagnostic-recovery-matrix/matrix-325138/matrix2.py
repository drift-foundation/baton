"""W325035 — the matrix, with REAL assertions and a harness that can fail.

Review 2026-10-18T18-05-00Z's first blocker was this file's predecessor: it
marked any returning body `observed` regardless of what the body found, its
advertised asserts were strings rather than checks, `main` always exited 0 and
a cleanup failure did not fail a scenario. All four are corrected here:

  * `expect(...)` records a named check and RAISES on failure.
  * a scenario with any failed check is `failed`, and so is one whose cleanup
    raises.
  * `main` exits non-zero when any scenario fails unexpectedly.
  * `0-harness-self-check` asserts something DELIBERATELY FALSE and must be
    reported as failed. If it is ever reported as observed, this harness is not
    checking anything and the run says so and exits non-zero.

Boundaries unchanged and labelled per scenario: the composed native Job world
is imported from `tests.tools.test_stage_execution` (the parent W321690
lineage) and not modified; the ENGINE answers without a daemon; the PROVIDER is
injected at the adapter's own process seam. No product edit, no forged receipt,
no raw SQL against product tables, no live model or credential, no deployment,
no Git mutation.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --evidence <directory>
"""
import argparse
import json
import pathlib
import time
import traceback


class CheckFailed(AssertionError):
    pass


class Checks:
    """Named checks that actually fail."""

    def __init__(self):
        self.held = []

    def expect(self, label, condition, detail=None):
        passed = bool(condition)
        self.held.append({"check": label, "passed": passed,
                          "detail": detail})
        if not passed:
            raise CheckFailed(f"{label} (detail: {detail!r})")
        return passed

    def note(self, label, value):
        self.held.append({"observation": label, "value": value})
        return value

    def document(self):
        return self.held


def say(place, name, answer):
    (place / name).write_text(
        json.dumps(answer, indent=2, sort_keys=True, default=str) + "\n")


def world():
    from tests.tools.test_stage_execution import (
        TheComposedJobTraversesReviewAndAcceptance as Composed)

    case = Composed()
    case.setUp()
    return case


def identities(case):
    stage = case.submission["jobs"][0]
    return {"work_id": stage["stages"][0]["work_id"],
            "job_id": stage["job_id"],
            "submission_id": case.submission["submission_id"],
            "authority_uuid": case.config["authority_uuid"]}


def _now():
    from tests.job_manager import fixtures

    return fixtures.NOW


def settle(case, job, composed, ticks=12):
    from baton_v12.job_manager import sweep as tick
    from tests.job_manager import fixtures

    for _ in range(ticks):
        tick(job, composed, now=fixtures.NOW)
    return case.states(job, composed)


# -- the scenarios -----------------------------------------------------------

def harness_self_check(case, checks):
    """DELIBERATELY WRONG, so a green run proves the checks are checks."""
    from baton_v12.job_manager import submit as submit_jobs

    job, control, composed = case.serving()
    submit_jobs(job, case.submission)
    states = case.states(job, composed)
    checks.note("actual stage states", states)
    # The implementation stage is `queued` here. Asserting `completed` must
    # fail, and the run must report this scenario as failed.
    checks.expect("implementation is completed immediately after submission "
                  "(INTENTIONALLY FALSE)",
                  states.get("implementation") == "completed", states)
    return {}


def live_cancellation(case, checks):
    """Cancel an assignment that is actually LIVE, and prove the act."""
    from baton_v12.authority import Authority
    from baton_v12.job_manager import submit as submit_jobs

    job, control, composed = case.serving()
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    held = identities(case)
    uuid, store = held["authority_uuid"], case.authority_path
    authority = Authority.open(store, expected_authority_uuid=uuid)
    answer = {}
    try:
        live = authority.assignment_of(held["work_id"])
        checks.expect("an assignment is live before the cancellation",
                      live is not None, live)
        answer["live_before_cancel"] = live
        cancelled = authority.session(live["participant"]).cancel(
            {"expect": live, "operation_id": "w325035-live-cancel",
             "reason": "W325035 matrix: live cancellation"})
        answer["cancelled"] = cancelled
        checks.expect("the cancellation answered a result",
                      isinstance(cancelled, dict) and bool(cancelled),
                      cancelled)
        after = authority.project_work(held["work_id"])
        answer["work_after_cancel"] = {
            k: after[k] for k in ("status", "phase", "gate", "handler",
                                  "outcome")}
        checks.expect("the Work no longer has a handler",
                      after["handler"] is None, after["handler"])
        checks.expect("the Work is still open (a cancelled assignment is not "
                      "a cancelled Work)", after["status"] == "open",
                      after["status"])
        checks.expect("no outcome was recorded by the cancellation",
                      after["outcome"] is None, after["outcome"])
        events = authority.assignment_events(held["work_id"])
        answer["assignment_events"] = events[-2:]
        checks.expect("the cancellation is in the assignment events",
                      any("cancel" in json.dumps(one) for one in events),
                      events[-1] if events else None)
        checks.expect("the live assignment is gone",
                      authority.assignment_of(held["work_id"]) is None, None)
    finally:
        authority.dispose()
    answer["identities"] = held
    return answer


def _turned(case, checks):
    """One submitted Job carried to a COMMITTED worker turn, unprocessed."""
    from baton_v12.job_manager import submit as submit_jobs

    job, control, composed = case.serving()
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    attempt = case.only_attempt(composed, "implementation")
    roots = case.mounted(composed, "implementation", attempt)
    status = case.turn(
        control, "implementation", attempt, roots,
        edits={"harness.py": "print('the corrected harness')\n"})
    checks.expect("the worker turn committed", status == 0, status)
    checks.note("states with the reply committed and unprocessed",
                case.states(job, composed))
    return job, control, composed, attempt


def restart_of_a_committed_turn(case, checks):
    """A fresh composition over a committed-but-unprocessed worker reply.

    WHAT THIS ESTABLISHES, and it is deliberately narrower than the vector the
    FINDING names. A first cut of this scenario flipped `case.running`,
    believing it was this world's engine-absence seam. It is not -- that flag
    belongs to the integration-worker world, and setting it here reads and
    writes nothing. So the "absence observed" conclusion that cut would have
    recorded is withdrawn before it was ever claimed, and what is asserted
    below is only what was actually driven.
    """
    job, control, composed, attempt = _turned(case, checks)
    fresh_job, fresh_control, fresh_composed = case.serving()
    recovered = fresh_composed.recover(now=_now())
    checks.note("the supported recover verb's answer for a fresh "
                "composition", recovered)
    settled = settle(case, fresh_job, fresh_composed, ticks=14)
    checks.note("states after recover() and ordinary sweeps", settled)
    # THE TWO THINGS THAT MUST HOLD WHATEVER ELSE DOES: nothing finished
    # falsely and nothing was offered twice.
    checks.expect("the stage did not falsely finish",
                  settled.get("implementation") != "completed", settled)
    checks.expect("the successors stay blocked",
                  settled.get("review") == "blocked", settled)
    prepared = sorted(case.worker_of(fresh_composed,
                                     "implementation").stage._prepared)
    # MY EXPECTATION HERE WAS WRONG, and the product's answer is better than
    # the one I wrote down: the fresh composition re-adopts the SAME attempt
    # identity rather than preparing none or a second one. The check is
    # corrected to the stronger property that actually holds.
    checks.expect("the fresh composition re-adopted the original attempt and "
                  "prepared no other", prepared == [attempt], prepared)
    original = sorted(case.worker_of(composed,
                                     "implementation").stage._prepared)
    checks.expect("the original attempt identity is unchanged",
                  original == [attempt], original)
    return {"identities": dict(identities(case),
                               implementation_attempt=attempt),
            "recover_answer": recovered, "settled": settled,
            "prepared_in_fresh_composition": prepared,
            "not_demonstrated": "A committed reply is NOT adopted across a "
                                "restart by `recover()` plus ordinary sweeps "
                                "in this world: recover answers {'abandoned': "
                                "[], 'recoverable': []} and the stage stays "
                                "`answering`. That is consistent with §10.8 -- "
                                "this world's engine keeps answering that the "
                                "runtime is present, and an unreachable or "
                                "running runtime is not a dead one -- but it "
                                "means the lost-reply-across-restart vector "
                                "is NOT demonstrated here. Demonstrating it "
                                "needs an engine seam that reports positive "
                                "absence for this composition, which this "
                                "fixture does not expose; the "
                                "integration-worker world's `running` flag is "
                                "a different world's seam. Named as remaining "
                                "scope rather than asserted either way."}


def diagnostic_owner(case, checks):
    """What a failed turn reaches, and what it does NOT reach.

    The review's instruction: establish the explicit native diagnostic owner or
    document the precise missing supported operation, without renaming a state
    to an owner. This scenario does the second, because the first is not there
    to find -- and it says exactly which read was asked.
    """
    from baton_v12.job_manager import submit as submit_jobs
    from baton_v12.job_manager import status as projected_status
    from baton_v12.job_manager.ending import pending_endings
    from tests.job_manager import fixtures

    job, control, composed = case.serving()
    submit_jobs(job, case.submission)
    case.drive(job, composed, "implementation", "waiting")
    attempt = case.only_attempt(composed, "implementation")
    roots = case.mounted(composed, "implementation", attempt)
    case.turn(control, "implementation", attempt, roots, edits={}, status=1)
    settle(case, job, composed)
    projected = projected_status(job, composed, observed_at=fixtures.NOW)
    stage = [one for one in projected["jobs"][0]["stages"]
             if one["kind"] == "implementation"][0]
    checks.expect("the stage is exceptional", stage["state"] == "exceptional",
                  stage["state"])
    checks.expect("no candidate was published",
                  not stage.get("proposal"), stage.get("proposal"))
    # THE QUESTION, asked of every supported surface this stage exposes.
    members = sorted(stage)
    checks.note("every member the status projection gives this stage",
                members)
    owner_members = [one for one in members
                     if one in ("owner", "diagnostic_owner", "assignee",
                                "principal", "route", "handler",
                                "eligible_for", "awaiting")]
    checks.expect("the projection names NO diagnostic owner member for an "
                  "exceptional stage", owner_members == [], owner_members)
    held = list(pending_endings(job))
    checks.expect("pending_endings offers no diagnostic assignment either",
                  held == [], held)
    return {"identities": dict(identities(case),
                               implementation_attempt=attempt),
            "stage": stage, "stage_members": members,
            "pending_endings": held,
            "finding": "An exceptional stage is an operator-facing TERMINAL "
                       "STATE, not an assignment routed to a diagnostic "
                       "principal. projection.py's own words: 'an operator "
                       "has to see that, so it is exceptional rather than a "
                       "stage that will quietly be offered again.' The "
                       "precise missing supported operation is therefore: "
                       "nothing creates an eligible diagnostic assignment or "
                       "names a diagnostic principal for an exceptional "
                       "stage. The only supported surfaces are this status "
                       "projection and the installed `logs` verb over the "
                       "attempt's retained output. If the pilot requires a "
                       "diagnostic OWNER rather than a state an operator must "
                       "notice, that operation does not exist and is a "
                       "bounded product gap with this spec basis: W325035's "
                       "FINDING asks that these outcomes 'reach explicit "
                       "diagnostic owner'."}


SCENARIOS = (
    ("0-harness-self-check", harness_self_check, True,
     "a deliberately false expectation; this scenario MUST fail"),
    ("1-live-cancellation", live_cancellation, False,
     "a cancellation driven while the assignment is live"),
    ("2-restart-of-a-committed-turn", restart_of_a_committed_turn, False,
     "a committed worker turn, then a fresh composition and the supported "
     "recover verb; asserts only no-false-finish and no-duplicate"),
    ("3-diagnostic-owner", diagnostic_owner, False,
     "a provider turn exiting 1, then every supported surface asked who owns "
     "the diagnosis"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    place.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    answers = []
    unexpected = 0

    print("W325035 matrix, asserting:")
    for name, body, expected_failure, injected in SCENARIOS:
        at = time.monotonic()
        checks = Checks()
        record = {"scenario": name, "injected": injected,
                  "expected_failure": expected_failure,
                  "simulated": ["engine: run/inspect/ps with no daemon",
                                "provider: injected at the adapter's process "
                                "seam"]}
        case = None
        try:
            case = world()
            record.update(body(case, checks) or {})
            record["outcome"] = "observed"
        except CheckFailed as failure:
            record["outcome"] = "failed"
            record["failed_check"] = str(failure)
        except Exception:                                    # noqa: BLE001
            record["outcome"] = "failed"
            record["failure"] = traceback.format_exc()[-2000:]
        finally:
            if case is not None:
                try:
                    case.doCleanups()
                except Exception:                            # noqa: BLE001
                    record["outcome"] = "failed"
                    record["cleanup_failure"] = \
                        traceback.format_exc()[-800:]
        record["checks"] = checks.document()
        record["seconds"] = round(time.monotonic() - at, 3)
        failed = record["outcome"] == "failed"
        if failed != expected_failure:
            unexpected += 1
            record["unexpected"] = True
        answers.append(record)
        say(place, f"scenario-{name}.json", record)
        print(f"  {name}: {record['outcome']}"
              f"{' (expected)' if failed and expected_failure else ''}"
              f"{' UNEXPECTED' if record.get('unexpected') else ''}"
              f" ({record['seconds']}s)")

    answer = {"schema": "baton.w325035.matrix/2",
              "supersedes": "matrix-325037 (its observations are preserved; "
                            "its cancellation prose is corrected by scenario "
                            "1 here and by SUPERSESSION.md)",
              "boundary": "composed native Job world imported from "
                          "tests.tools.test_stage_execution and not modified; "
                          "engine and provider simulated at their own "
                          "boundaries and labelled; no product edit, forged "
                          "receipt, live model, live credential, deployment "
                          "or Git mutation",
              "scenarios": answers,
              "observed": sum(1 for one in answers
                              if one["outcome"] == "observed"),
              "failed_as_expected": sum(
                  1 for one in answers
                  if one["outcome"] == "failed" and one["expected_failure"]),
              "unexpected": unexpected,
              "harness_self_check_proves_checks_are_checks": any(
                  one["scenario"] == "0-harness-self-check"
                  and one["outcome"] == "failed" for one in answers),
              "seconds": round(time.monotonic() - started, 3)}
    say(place, "MATRIX2.json", answer)
    print(f"observed {answer['observed']}, "
          f"failed-as-expected {answer['failed_as_expected']}, "
          f"unexpected {answer['unexpected']}, {answer['seconds']}s")
    if not answer["harness_self_check_proves_checks_are_checks"]:
        print("REFUSED: the self-check did not fail, so these checks are not "
              "checking anything")
        return 2
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
