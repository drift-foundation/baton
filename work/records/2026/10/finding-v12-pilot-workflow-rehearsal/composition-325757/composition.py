"""W321690 — the composition that ENFORCES the human approval boundary.

Review 2026-10-18T19-33-42Z found the real defect in my packet: §9A said the
manager serves and §9B told the operator not to call automatic integration
admission, and an instruction is not a control. `tools/stage_execution.py`
calls `admit_accepted` (3118, 3153) and `continue_accepted` (3149) during
ordinary manager progress with the deployment's own verification, review and
approval sessions, so a serving composition can pre-empt the owner however
firmly a document forbids it. The review asked for the supported shape that
enforces the boundary while preserving result pickup and review -- or the exact
unavailable operation.

THE SHAPE IS THE SUBMITTED JOB'S OWN STAGE SET, and it is pinned here by
driving it. A Job composed of `implementation` and `review` only:

  * is served normally -- pickup, a real worker turn, the implementation
    ending, the review assignment and a real review turn;
  * PUBLISHES the candidate at the implementation ending (`review_driver`
    correlates `integration.publish_candidate`'s own committed record), so the
    independent receipt actors have the exact proposal, line and checkpoint to
    judge;
  * writes NO receipt of any kind, because nothing reaches the integration
    driver at all -- there is no integration stage for it to drive;
  * leaves NO falsely complete integration stage, because there is none to
    leave; both declared stages are honestly `completed`;
  * and hands the Work on to the configured outgoing route, where the owner's
    `disposition` acts take it.

Scenario 2 then drives the whole human path on that same world, and scenario 3
measures the contrast: with an integration stage composed, the Work does NOT
reach the owner -- the stage holds and the sweep defers with the deployment's
own contained refusal, which is how this fixture's integration deployment is
configured. The retained `../rehearsal-324985/RECEIPT-BOUNDARY.md` is the
evidence for what a fully configured integration deployment does at that
boundary: it writes verification, review AND approval before any runtime.

Harness: the strict classifier from `../../finding-v12-pilot-diagnostic-recovery-matrix/matrix-325259/matrix3.py`.
`0-harness-self-check` must fail with its own named `CheckFailed`; a setup or
cleanup error counts unexpected, and `main` refuses the run if the self-check
did not fail for its own reason. A zero exit alone is never acceptance.

Boundaries: the composed native Job world is imported from
`tests.tools.test_stage_execution` and not modified; the engine answers without
a daemon; the provider is injected at the adapter's own process seam; the
verifier's, reviewer's and owner's JUDGMENTS are simulated and labelled. No
product edit, no forged receipt, no raw SQL, no live model, no live credential,
no deployment, and nothing that mutates this repository's history, index or
working tree (the imported fixture builds its own disposable history inside a
temporary root).

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --evidence <directory>
"""
import argparse
import copy
import io
import json
import pathlib
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout

VERIFIER = "baton.verifier-321690"
REVIEWER = "baton.reviewer-321690"
OWNER = "baton.slaw"
SIMULATED = "SIMULATED (W321690 composition rehearsal; no human act, no live "
RECEIPTS = ("verification", "review", "approval", "integration")


class CheckFailed(AssertionError):
    def __init__(self, label, detail=None):
        super().__init__(f"{label} (detail: {detail!r})")
        self.label = label


class Checks:
    def __init__(self):
        self.held = []

    def expect(self, label, condition, detail=None):
        passed = bool(condition)
        self.held.append({"check": label, "passed": passed, "detail": detail})
        if not passed:
            raise CheckFailed(label, detail)
        return passed

    def note(self, label, value):
        self.held.append({"observation": label, "value": value})
        return value

    def document(self):
        return self.held

    def passed(self):
        return sum(1 for one in self.held if one.get("passed"))


def say(place, name, answer):
    (place / name).write_text(
        json.dumps(answer, indent=2, sort_keys=True, default=str) + "\n")


def world():
    from tests.tools.test_stage_execution import (
        TheComposedJobTraversesReviewAndAcceptance as Composed)

    case = Composed()
    case.setUp()
    return case


def _now():
    from tests.job_manager import fixtures

    return fixtures.NOW


def sweeps(case, job, composed, ticks=12):
    from baton_v12.job_manager import sweep as tick

    report = None
    for _ in range(ticks):
        report = tick(job, composed, now=_now())
    return case.states(job, composed), report


def two_stage_submission(case):
    """The Job this pilot submits for a human-approved Work."""
    held = copy.deepcopy(case.submission)
    held["jobs"][0]["stages"] = [one for one in held["jobs"][0]["stages"]
                                 if one["kind"] != "integration"]
    return held


def command(verb, *operands):
    from tools import stack_command

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            code = stack_command.main([verb, *operands])
        except SystemExit as exited:
            # argparse exits the PROCESS on an operand it cannot parse. A
            # driver that let that through would end mid-run with no summary,
            # which is exactly how this one failed once.
            code = exited.code if isinstance(exited.code, int) else 2
    return {"exit": code, "stderr": err.getvalue().strip(),
            "answer": json.loads(out.getvalue()) if out.getvalue().strip()
            else None}


def receipts_of(reader, proposal_id):
    return {kind: (reader.receipt(proposal_id, kind) or {}).get("disposition")
            for kind in RECEIPTS}


def reading(case):
    from baton_v12.authority import Authority

    return Authority.open_readonly(
        case.authority_path,
        expected_authority_uuid=case.config["authority_uuid"])


def served_two_stage(case, checks):
    """Serve one two-stage Job to a published, unjudged candidate."""
    from baton_v12.job_manager import submit as submit_jobs

    job, control, composed = case.serving()
    submit_jobs(job, two_stage_submission(case))
    case.drive(job, composed, "implementation", "waiting")
    attempt = case.only_attempt(composed, "implementation")
    roots = case.mounted(composed, "implementation", attempt)
    checks.expect("the implementation worker turn ran",
                  case.turn(control, "implementation", attempt, roots,
                            edits={"harness.py":
                                   "print('the pilot harness')\n"}) == 0)
    case.drive(job, composed, "implementation", "completed", ticks=16)
    case.drive(job, composed, "review", "waiting", ticks=16)
    review = case.only_attempt(composed, "review")
    report = copy.deepcopy(case.REPORT)
    checks.expect("the review worker turn ran",
                  case.turn(control, "review", review,
                            case.mounted(composed, "review", review),
                            edits={"review-report.json":
                                   json.dumps(report)}) == 0)
    states, _ = sweeps(case, job, composed, ticks=20)
    return job, control, composed, attempt, review, states


# -- scenario 0 --------------------------------------------------------------

SELF_CHECK = ("a two-stage Job carries an integration stage "
              "(INTENTIONALLY FALSE)")


def harness_self_check(case, checks):
    held = two_stage_submission(case)
    kinds = [one["kind"] for one in held["jobs"][0]["stages"]]
    checks.note("the stage kinds actually submitted", kinds)
    checks.expect(SELF_CHECK, "integration" in kinds, kinds)
    return {}


# -- scenario 1 --------------------------------------------------------------

def the_two_stage_shape_cannot_admit(case, checks):
    """The control, driven: no integration stage, so nothing can admit."""
    from baton_v12.worker_manager import review_cycles

    job, control, composed, attempt, review, states = served_two_stage(
        case, checks)
    checks.expect("both declared stages are completed",
                  states.get("implementation") == "completed"
                  and states.get("review") == "completed", states)
    checks.expect("and there is NO integration stage to be falsely complete",
                  "integration" not in states, sorted(states))

    reader = reading(case)
    try:
        proposals = reader.proposals_of(case.work)
        checks.expect("the candidate IS published by the implementation "
                      "ending, so the receipt actors have something exact to "
                      "judge", len(proposals) == 1,
                      [one["proposal_id"] for one in proposals])
        proposal = proposals[-1]
        checks.expect("ALL FOUR RECEIPTS ARE ABSENT: nothing admitted",
                      receipts_of(reader, proposal["proposal_id"])
                      == dict.fromkeys(RECEIPTS), receipts_of(
                          reader, proposal["proposal_id"]))
        work = reader.project_work(case.work)
        checks.expect("the Work is open with no handler, handed on to the "
                      "configured outgoing route",
                      work["status"] == "open" and work["handler"] is None,
                      {k: work.get(k) for k in ("status", "phase", "route",
                                                "handler")})
        checks.expect("and no outcome was invented",
                      work["outcome"] is None, work["outcome"])
        route = work["route"]
    finally:
        reader.dispose()

    # THE PUBLISHED CANDIDATE IS THE REVIEWED ONE, through the public readers.
    named = composed.deployment.line()
    line = review_cycles.line_of(control, named["line_id"])
    attached = review_cycles.review_for_attempt(
        control, attempt_id=review,
        generation=__import__("baton_v12.worker_manager",
                              fromlist=["assignment_of"]).assignment_of(
                                  control, review)["generation"])
    checkpoint = review_cycles.checkpoint_of(control,
                                             attached["checkpoint_id"])
    checks.expect("the review attachment and the line agree",
                  attached["line_id"] == line["line_id"] == line["line_id"],
                  attached["line_id"])
    checks.expect("the reviewed checkpoint is frozen on this Work's line",
                  checkpoint["state"] == "frozen"
                  and checkpoint["line_id"] == line["line_id"]
                  and line["work_id"] == case.work, checkpoint)
    checks.expect("the published candidate digest is that checkpoint's own "
                  "head", proposal["candidate_digest"]
                  == checkpoint["evidence"]["head"],
                  {"published": proposal["candidate_digest"],
                   "checkpoint_head": checkpoint["evidence"]["head"]})

    # AND SERVING ON, AND A RESTART, STILL CANNOT ADMIT. This is the property
    # an instruction cannot give: the composition has nothing to admit with.
    more, report = sweeps(case, job, composed, ticks=40)
    fresh_job, fresh_control, fresh = case.serving()
    recovered = fresh.recover(now=_now())
    after, _ = sweeps(case, fresh_job, fresh, ticks=40)
    reader = reading(case)
    try:
        checks.expect("40 further ticks admit nothing",
                      receipts_of(reader, proposal["proposal_id"])
                      == dict.fromkeys(RECEIPTS), more)
        checks.expect("a fresh serving composition over the same stores "
                      "admits nothing either",
                      receipts_of(reader, proposal["proposal_id"])
                      == dict.fromkeys(RECEIPTS), after)
        checks.expect("no second candidate was published",
                      [one["proposal_id"]
                       for one in reader.proposals_of(case.work)]
                      == [proposal["proposal_id"]])
        checks.expect("and the restarted composition still shows two stages "
                      "only", sorted(after) == ["implementation", "review"],
                      sorted(after))
    finally:
        reader.dispose()
    return {"identities": {"work_id": case.work,
                           "job_id": case.submission["jobs"][0]["job_id"],
                           "authority_uuid": case.config["authority_uuid"],
                           "implementation_attempt": attempt,
                           "review_attempt": review,
                           "proposal_id": proposal["proposal_id"],
                           "candidate_digest": proposal["candidate_digest"],
                           "line_id": line["line_id"],
                           "reviewed_checkpoint": attached["checkpoint_id"]},
            "stage_kinds_submitted": [one["kind"] for one in
                                      two_stage_submission(case)["jobs"][0]
                                      ["stages"]],
            "states": states, "states_after_restart": after,
            "outgoing_route": route, "recover_answer": recovered,
            "last_sweep_report_outcomes": [
                {k: one.get(k) for k in ("stage_id", "outcome")}
                for one in (report or {}).get("started", [])],
            "establishes": "The enforcing control is the submitted Job's own "
                           "stage set. With no integration stage there is no "
                           "integration driver call site in this Job at all, "
                           "so `admit_accepted`/`continue_accepted` cannot be "
                           "reached by serving, by further ticks or by a "
                           "restart -- while pickup, the ending, the "
                           "independent review and the candidate publication "
                           "all happen normally."}


# -- scenario 2 --------------------------------------------------------------

def the_human_path_on_that_shape(case, checks):
    """The receipt path and the owner chain, on the enforcing composition."""
    from baton_v12.authority import Authority

    job, control, composed, attempt, review, states = served_two_stage(
        case, checks)
    store, uuid = case.authority_path, case.config["authority_uuid"]
    base = ["--authority-store", store, "--authority-uuid", uuid]
    reader = reading(case)
    try:
        proposal = reader.proposals_of(case.work)[-1]
    finally:
        reader.dispose()
    proposal_id = proposal["proposal_id"]
    answer = {"identities": {"work_id": case.work,
                             "proposal_id": proposal_id,
                             "candidate_digest":
                             proposal["candidate_digest"],
                             "implementation_attempt": attempt,
                             "review_attempt": review}}

    authority = Authority.open(store, expected_authority_uuid=uuid)
    try:
        scope = authority.project_work(case.work)["scope"]
        for who, capability in ((VERIFIER, "verify"), (REVIEWER, "review"),
                                (OWNER, "approve"), (OWNER, "integrate"),
                                (OWNER, "close")):
            authority.grant_capability(who, capability, scope=scope)
        generation = authority.policy_generation()
        answer["grants"] = {"verification": VERIFIER, "review": REVIEWER,
                            "owner": OWNER, "scope": scope,
                            "policy_generation": generation}
        checks.expect("the owner holds no verify or review grant",
                      not authority.holds_capability(OWNER, "verify",
                                                     scope=scope)
                      and not authority.holds_capability(OWNER, "review",
                                                         scope=scope))

        # THE INDEPENDENT JUDGMENTS, on the published candidate.
        verification = authority.session(VERIFIER).verify(
            {"proposal_id": proposal_id,
             "verification_id": "w321690-verification",
             "observation": "passed",
             "operation_id": "w321690-verify"})
        reviewed = authority.session(REVIEWER).review(
            {"proposal_id": proposal_id, "review_id": "w321690-review",
             "disposition": "accepted", "operation_id": "w321690-review-op"})
        answer["verification"] = verification
        answer["review"] = reviewed
        held = receipts_of(authority, proposal_id)
        answer["receipts_after_judgments"] = held
        checks.expect("verification is passed and review accepted",
                      held["verification"] == "passed"
                      and held["review"] == "accepted", held)
        checks.expect("THE APPROVAL IS STILL ABSENT on the enforcing shape",
                      held["approval"] is None, held)
        checks.expect("and so is the integration receipt",
                      held["integration"] is None, held)
        actors = {kind: (authority.receipt(proposal_id, kind) or {}).get(
            "actor") for kind in ("verification", "review")}
        answer["judgment_actors"] = actors
        checks.expect("the judgments are attributed to the independent "
                      "participants", actors == {"verification": VERIFIER,
                                                 "review": REVIEWER}, actors)
    finally:
        authority.dispose()

    pending = command("disposition", "pending", *base, "--participant", OWNER,
                      "--work", case.work)
    answer["pending"] = pending
    checks.expect("the owner's pending answers approval-due",
                  pending["exit"] == 0
                  and (pending["answer"] or {}).get("owner_action")
                  == "approval-due", pending)

    # WITHHELD APPROVAL STILL REFUSES DELIVERY ON THIS SHAPE.
    negatives = {}
    record = pathlib.Path(case.root) / "human-integration.json"
    record.write_text(json.dumps(
        {"schema": "baton.v12.human-integration-record/1",
         "work_id": case.work, "proposal_id": proposal_id,
         "candidate_digest": proposal["candidate_digest"],
         "commit": "0" * 40, "integrated_by": OWNER,
         "note": SIMULATED + "commit; forty zeroes are a labelled fixture)"},
        indent=2) + "\n")
    negatives["integration with approval withheld"] = command(
        "disposition", "integrated", *base, "--participant", OWNER,
        "--work", case.work, "--proposal", proposal_id,
        "--record", str(record), "--operation-id", "w321690-early-integrated")
    negatives["satisfying closure with approval withheld"] = command(
        "disposition", "close", *base, "--participant", OWNER,
        "--work", case.work, "--outcome", "satisfying",
        "--rationale", "too early", "--operation-id", "w321690-early-close")
    answer["negatives"] = negatives
    for what, got in negatives.items():
        checks.expect(f"{what} is refused", got["exit"] != 0, got)
    reader = reading(case)
    try:
        checks.expect("no receipt changed across the refusals",
                      receipts_of(reader, proposal_id)
                      == {"verification": "passed", "review": "accepted",
                          "approval": None, "integration": None},
                      receipts_of(reader, proposal_id))
    finally:
        reader.dispose()
    return dict(answer, states=states,
                establishes="On the enforcing two-stage shape the independent "
                            "receipt path works exactly as W325034 proved it "
                            "on a clean candidate: separate verify and review "
                            "actors publish their judgments, the approval "
                            "stays absent, the owner's pending answers "
                            "approval-due, and delivery is refused while the "
                            "approval is withheld. The owner's own "
                            "approve/integrated/close chain and its readback "
                            "are the accepted W325034 proof "
                            "(boundary-325197 scenario 2) and are not "
                            "repeated here.",
                labelled=[SIMULATED + "provider)",
                          "engine: no daemon",
                          "provider: injected at the adapter's process seam",
                          "the human integration record's commit is forty "
                          "zeroes: a labelled fixture, not delivery"])


# -- scenario 3 --------------------------------------------------------------

def the_three_stage_contrast(case, checks):
    """What a composed integration stage does instead -- measured, not assumed.

    This fixture's deployment configures no integration instructions, so the
    stage is CONTAINED rather than admitted: the sweep defers it with the
    deployment's own refusal and writes nothing. That is not the hazard the
    review named, and this scenario does not pretend it is. The hazard is what
    a FULLY configured integration deployment does at that boundary, which the
    retained `../rehearsal-324985/RECEIPT-BOUNDARY.md` measured: verification,
    review and approval written together before any runtime.

    What this scenario does establish is the operational difference that makes
    the two-stage shape the control: with an integration stage composed, the
    Work does NOT reach the owner's route -- it is held in the integration
    stage, under a deployment-configured decision nobody has made yet.
    """
    held = case.reviewed()
    states, report = sweeps(case, held.job, held.composed, ticks=20)
    checks.expect("the implementation and review stages completed",
                  states.get("implementation") == "completed"
                  and states.get("review") == "completed", states)
    checks.expect("the integration stage is composed and HOLDS rather than "
                  "completing", states.get("integration") == "claimed",
                  states)
    deferred = [one for one in (report or {}).get("started", [])
                if one.get("stage_id", "").endswith("integration")]
    checks.note("the sweep's own account of the integration stage", deferred)
    checks.expect("the sweep defers it with the deployment's own contained "
                  "refusal", bool(deferred)
                  and deferred[0].get("outcome") == "deferred"
                  and deferred[0].get("detail", {}).get("category")
                  == "refused", deferred)
    reader = reading(case)
    try:
        proposals = reader.proposals_of(case.work)
        checks.expect("a candidate is published here too",
                      len(proposals) == 1,
                      [one["proposal_id"] for one in proposals])
        checks.expect("and this configuration wrote no receipt either",
                      receipts_of(reader, proposals[-1]["proposal_id"])
                      == dict.fromkeys(RECEIPTS),
                      receipts_of(reader, proposals[-1]["proposal_id"]))
        work = reader.project_work(case.work)
        checks.expect("but the Work did NOT reach the owner: it is held by "
                      "the integration participant",
                      work["handler"] is not None, {k: work.get(k) for k in
                                                    ("status", "phase",
                                                     "route", "handler")})
    finally:
        reader.dispose()
    return {"identities": {"work_id": case.work,
                           "implementation_attempt": held.attempt_id,
                           "review_attempt": held.review},
            "states": states,
            "integration_stage_account": deferred,
            "not_claimed": "This scenario does NOT show automatic admission "
                           "happening, because this fixture's deployment "
                           "configures no integration instructions and the "
                           "refusal is contained per stage. The source call "
                           "sites are tools/stage_execution.py 3118 and 3153 "
                           "(admit_accepted) and 3149 "
                           "(continue_accepted), reached during ordinary "
                           "manager progress with the deployment's own "
                           "verification, review and approval sessions; "
                           "../rehearsal-324985/RECEIPT-BOUNDARY.md is the "
                           "retained evidence that all three receipts are "
                           "written at that boundary before any runtime. The "
                           "conclusion carried into the packet is therefore "
                           "about COMPOSITION: a Job whose stage set includes "
                           "integration has a call site a serving manager can "
                           "reach, and a Job without one does not."}


SCENARIOS = (
    ("0-harness-self-check", harness_self_check, SELF_CHECK,
     "a deliberately false expectation about the submitted stage set"),
    ("1-the-two-stage-shape-cannot-admit", the_two_stage_shape_cannot_admit,
     None,
     "one Job submitted with implementation and review only, served to a "
     "published candidate, then 40 further ticks and a fresh composition"),
    ("2-the-human-path-on-that-shape", the_human_path_on_that_shape, None,
     "independent verify and review on the published candidate, then the "
     "owner's pending and the two refusals while approval is withheld"),
    ("3-the-three-stage-contrast", the_three_stage_contrast, None,
     "the same fixture with the integration stage composed"),
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    place.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    answers, unexpected, passed = [], 0, 0

    print("W321690 composition boundary:")
    for name, body, intended, injected in SCENARIOS:
        at = time.monotonic()
        checks = Checks()
        record = {"scenario": name, "injected": injected,
                  "expected_failure": intended is not None,
                  "intended_failed_check": intended,
                  "simulated": ["engine: no daemon",
                                "provider: injected at the adapter's own "
                                "process seam",
                                "verifier, reviewer and owner judgments"],
                  "not_called": ["_accepted_receipts", "admit_accepted",
                                 "continue_accepted", "raw SQL",
                                 "any product-source edit"]}
        case, failure = None, None
        try:
            case = world()
            record.update(body(case, checks) or {})
            record["outcome"] = "observed"
        except CheckFailed as caught:
            record["outcome"] = "failed"
            record["failed_check"] = caught.label
            failure = caught
        except BaseException:                                # noqa: BLE001
            # BaseException deliberately: a SystemExit raised under a scenario
            # is a failure of this run, not a reason to leave it unreported.
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
                    failure = None
        record["checks"] = checks.document()
        record["checks_passed"] = checks.passed()
        record["seconds"] = round(time.monotonic() - at, 3)
        passed += record["checks_passed"]
        if intended is None:
            wanted = record["outcome"] == "observed"
        else:
            wanted = (record["outcome"] == "failed"
                      and isinstance(failure, CheckFailed)
                      and failure.label == intended
                      and "cleanup_failure" not in record
                      and "failure" not in record)
            record["failed_for_intended_reason"] = wanted
        if not wanted:
            unexpected += 1
            record["unexpected"] = True
        answers.append(record)
        say(place, f"scenario-{name}.json", record)
        print(f"  {name}: {record['outcome']} "
              f"({record['checks_passed']} checks passed"
              f"{', as intended' if record.get('failed_for_intended_reason') else ''}"
              f"{', UNEXPECTED' if record.get('unexpected') else ''}) "
              f"{record['seconds']}s")

    self_check = [one for one in answers
                  if one["scenario"] == "0-harness-self-check"]
    sound = bool(self_check) and self_check[0].get(
        "failed_for_intended_reason") is True
    answer = {"schema": "baton.w321690.composition-boundary/1",
              "question": "which SUPPORTED composition prevents automatic "
                          "integration admission from pre-empting the human "
                          "owner, while preserving result pickup, the "
                          "independent review and the candidate publication",
              "answer": "the submitted Job's own stage set: implementation "
                        "and review only. Driven in scenario 1 and used by "
                        "scenario 2; scenario 3 measures the contrast.",
              "boundary": "composed native Job world imported from "
                          "tests.tools.test_stage_execution and not modified; "
                          "engine and provider simulated at their own "
                          "boundaries; verifier, reviewer and owner judgments "
                          "simulated and labelled; no product edit, forged "
                          "receipt, raw SQL, live model, live credential or "
                          "deployment",
              "repository_provenance": "nothing here mutates this "
                                       "repository's history, index or "
                                       "working tree; the imported fixture "
                                       "builds its own disposable history "
                                       "inside a temporary root",
              "scenarios": answers,
              "checks_passed": passed,
              "observed": sum(1 for one in answers
                              if one["outcome"] == "observed"),
              "failed_as_intended": sum(
                  1 for one in answers
                  if one.get("failed_for_intended_reason")),
              "unexpected": unexpected,
              "harness_self_check_failed_for_its_own_reason": sound,
              "seconds": round(time.monotonic() - started, 3)}
    say(place, "COMPOSITION.json", answer)
    print(f"checks passed {passed}, observed {answer['observed']}, "
          f"failed-as-intended {answer['failed_as_intended']}, "
          f"unexpected {unexpected}, {answer['seconds']}s")
    if not sound:
        print("REFUSED: the self-check did not fail for its own intended "
              "reason, so these checks are not checking anything")
        return 2
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
