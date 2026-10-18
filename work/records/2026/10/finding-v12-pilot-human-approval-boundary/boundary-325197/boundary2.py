"""W325034 — the human approval boundary, corrected: supported lookups, real
evidence evaluation, and checks that fail.

Review 2026-10-18T18-10-11Z found three faults in `../boundary-325098/
human_boundary.py`, all of them mine and all of them harness faults rather
than product ones:

  1. It read the coordination store with `held.control._connection.execute`
     and took `line[0]`. AGENTS prohibits raw coordination-store reads, and a
     first row is not an identity proof. My handoff ALSO claimed "no raw SQL",
     which was false. Corrected here: the line is resolved through
     `composed.deployment.line()` and `review_cycles.line_of`.
  2. Step 3 hashed the evidence and then wrote `passed`/`accepted`
     unconditionally. `ordinary_test_evidence` cross-binds observations but
     does NOT establish that the selected required task and command actually
     ran and exited zero -- `driver._ordinary_tests_passed` is where that
     distinction lives. Corrected here: the five requirement clauses are
     evaluated EXPLICITLY, by this driver, against the deployment's own
     derived requirements, and a judgment is published only if they hold.
  3. Owner outcomes were logged without assertions, so an unexpected success
     or refusal still returned 0. Corrected here: every expectation is a
     check that raises, a failed check fails its scenario, `main` exits
     non-zero on any unexpected failure, and `0-harness-self-check` asserts
     something deliberately false and MUST be reported failed.

Boundaries unchanged: the composed native Job world is imported and not
modified; the engine answers without a daemon and the provider is injected at
the adapter's process seam; the verifier's, reviewer's and owner's JUDGMENTS
are simulated and labelled. `_accepted_receipts`, `admit_accepted` and
`continue_accepted` are not called. No raw SQL -- this time actually, and the
old claim is corrected in `../boundary-325098/SUPERSESSION.md`. No product
edit, live model, live credential, deployment or Git mutation.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --evidence <directory>
"""
import argparse
import io
import json
import pathlib
import time
import traceback
from contextlib import redirect_stderr, redirect_stdout

VERIFIER = "baton.verifier-325034"
REVIEWER = "baton.reviewer-325034"
OWNER = "baton.slaw"
SIMULATED = "SIMULATED (W325034 rehearsal; no human act, no live provider)"


class CheckFailed(AssertionError):
    pass


class Checks:
    def __init__(self):
        self.held = []

    def expect(self, label, condition, detail=None):
        passed = bool(condition)
        self.held.append({"check": label, "passed": passed, "detail": detail})
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


def command(verb, *operands):
    from tools import stack_command

    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = stack_command.main([verb, *operands])
    return {"exit": code, "stderr": err.getvalue().strip(),
            "answer": json.loads(out.getvalue()) if out.getvalue().strip()
            else None}


def receipts_of(authority, proposal_id):
    return {kind: authority.receipt(proposal_id, kind)
            for kind in ("verification", "review", "approval",
                         "integration")}


def dispositions(receipts):
    return {kind: (one or {}).get("disposition")
            for kind, one in receipts.items()}


def requirement_faults(evidence, requirements):
    """The five clauses `_ordinary_tests_passed` names, evaluated HERE.

    This driver does the evaluation rather than importing the private helper,
    because the point is that the judgment rests on an evaluation the judge
    performed -- and because a private function is not a supported surface.
    Each clause is returned by name so a refusal says which one failed.
    """
    observed = evidence["observation"]
    faults = []
    for member in ("task_id", "task_digest"):
        if observed.get(member) != requirements.get(member):
            faults.append(f"{member}: required {requirements.get(member)!r}, "
                          f"observed {observed.get(member)!r}")
    if list(observed.get("argv") or []) != list(requirements.get("argv") or []):
        faults.append(f"argv: required {requirements.get('argv')!r}, observed "
                      f"{observed.get('argv')!r}")
    if evidence.get("input_manifest_digest") \
            != requirements.get("input_manifest_digest"):
        faults.append("input_manifest_digest: the required tests were "
                      "selected for another attempt's input manifest")
    if observed.get("status") is None:
        faults.append("status: the required command did not run, so nothing "
                      "about it is proved")
    elif observed.get("status") != 0:
        faults.append(f"status: the required command exited "
                      f"{observed.get('status')!r}")
    return faults


class World:
    """One clean native reviewed candidate, resolved through SUPPORTED reads."""

    def __init__(self, case, checks):
        from baton_v12.authority import Authority
        from baton_v12.integration.driver import ordinary_test_evidence
        from baton_v12.worker_manager.review_cycles import (
            integration_checkpoint, line_of)

        self.case = case
        self.checks = checks
        self.uuid = case.config["authority_uuid"]
        self.store = case.authority_path
        self.work_id = case.submission["jobs"][0]["stages"][0]["work_id"]
        self.base = ["--authority-store", self.store,
                     "--authority-uuid", self.uuid]
        self.held = case.reviewed()
        case.drive(self.held.job, self.held.composed, "review", "completed",
                   ticks=14)
        # THE SUPPORTED LOOKUP, which is the first correction: the deployment
        # names its own line and the line owner reads it. No table traversal,
        # no first row.
        named = self.held.composed.deployment.line()
        self.line = line_of(self.held.control, named["line_id"])
        checks.expect("the deployment names its own line",
                      bool(named.get("line_id")), named)
        checks.expect("the line owner resolves that exact line",
                      self.line["line_id"] == named["line_id"], self.line)
        checks.expect("the line is bound to this Work",
                      self.line["work_id"] == self.work_id, self.line)
        reader = Authority.open_readonly(self.store,
                                         expected_authority_uuid=self.uuid)
        try:
            proposals = reader.proposals_of(self.work_id)
            checks.expect("exactly one candidate was published",
                          len(proposals) == 1, [one["proposal_id"]
                                                for one in proposals])
            self.proposal = proposals[-1]
            self.proposal_id = self.proposal["proposal_id"]
            self.clean = receipts_of(reader, self.proposal_id)
            checks.expect("all four receipts are absent before any judgment",
                          dispositions(self.clean) ==
                          {"verification": None, "review": None,
                           "approval": None, "integration": None},
                          dispositions(self.clean))
            self.accepted = integration_checkpoint(self.held.control,
                                                   named["line_id"])
            checks.expect("an accepted checkpoint exists",
                          bool(self.accepted), self.accepted)
            self.evidence = ordinary_test_evidence(
                self.held.control, reader, line_id=named["line_id"],
                proposal_id=self.proposal_id)
        finally:
            reader.dispose()
        # THE DERIVED REQUIREMENTS, from their own owner. `Integration`
        # exposes `required_tests`, derived from the configured task and its
        # bound input manifest -- never from what the worker reported, which
        # is owner ruling M115946's point and the reason this driver does not
        # read the observation to decide what was required.
        self.requirements = self.held.composed.integrator.required_tests()
        checks.note("the deployment's derived required tests",
                    self.requirements)
        # IDENTITY BINDING, asserted rather than assumed.
        checks.expect("the evidence names this proposal's result identity",
                      self.evidence["result_id"]
                      == self.proposal["result_id"],
                      [self.evidence.get("result_id"),
                       self.proposal.get("result_id")])
        checks.expect("the evidence names the producer attempt this Job ran",
                      self.evidence["attempt_id"] == self.held.attempt_id,
                      [self.evidence.get("attempt_id"), self.held.attempt_id])
        checks.expect("the evidence names the accepted checkpoint",
                      self.evidence["checkpoint_id"]
                      == self.accepted["checkpoint_id"],
                      [self.evidence.get("checkpoint_id"),
                       self.accepted.get("checkpoint_id")])

    def grants(self):
        from baton_v12.authority import Authority

        authority = Authority.open(self.store,
                                   expected_authority_uuid=self.uuid)
        try:
            scope = authority.project_work(self.work_id)["scope"]
            for who, capability in ((VERIFIER, "verify"), (REVIEWER, "review"),
                                    (OWNER, "approve"), (OWNER, "integrate"),
                                    (OWNER, "close")):
                authority.grant_capability(who, capability, scope=scope)
            self.generation = authority.policy_generation()
            held = {who: authority.capabilities_of(who)
                    for who in (VERIFIER, REVIEWER, OWNER)}
        finally:
            authority.dispose()
        self.checks.expect("the owner holds no verify or review grant",
                           not any("verify" in json.dumps(one)
                                   or "review" in json.dumps(one)
                                   for one in [held[OWNER]]), held[OWNER])
        return {"scope": scope, "grants": held,
                "policy_generation": self.generation}

    def receipts(self):
        from baton_v12.authority import Authority

        reader = Authority.open_readonly(self.store,
                                         expected_authority_uuid=self.uuid)
        try:
            return receipts_of(reader, self.proposal_id)
        finally:
            reader.dispose()


# -- the scenarios -----------------------------------------------------------

def harness_self_check(case, checks):
    """DELIBERATELY FALSE, so a green run proves these checks are checks."""
    from baton_v12.job_manager import submit as submit_jobs

    job, control, composed = case.serving()
    submit_jobs(job, case.submission)
    states = case.states(job, composed)
    checks.note("actual stage states", states)
    checks.expect("the review stage is completed immediately after "
                  "submission (INTENTIONALLY FALSE)",
                  states.get("review") == "completed", states)
    return {}


def stale_task_withholds_the_judgment(case, checks):
    """A requirement naming another task must prevent a passing verification.

    The negative that matters most: if the evaluation is real, mutating the
    requirement must withhold the judgment AND leave the authority untouched.
    """
    world = World(case, checks)
    world.grants()
    for what, mutate in (("another task id", {"task_id": "not-this-task"}),
                         ("another task digest",
                          {"task_digest": "sha256:" + "f" * 64}),
                         ("another command", {"argv": ["python3", "other.py"]}),
                         ("another input manifest",
                          {"input_manifest_digest": "sha256:" + "e" * 64})):
        mutated = dict(world.requirements, **mutate)
        faults = requirement_faults(world.evidence, mutated)
        checks.expect(f"the evaluation refuses {what}", bool(faults), faults)
    # AND NOTHING WAS WRITTEN by any of those refusals.
    checks.expect("no receipt exists after the refused evaluations",
                  dispositions(world.receipts()) ==
                  {"verification": None, "review": None, "approval": None,
                   "integration": None}, dispositions(world.receipts()))
    return {"work_id": world.work_id, "proposal_id": world.proposal_id,
            "requirements": world.requirements,
            "observation": world.evidence["observation"]}


def evidence_based_judgments(case, checks):
    """Evaluate the requirements, THEN judge; approval must stay absent."""
    from baton_v12.authority import Authority

    world = World(case, checks)
    answer = {"grants": world.grants()}
    faults = requirement_faults(world.evidence, world.requirements)
    checks.expect("the selected required tests actually ran and exited zero "
                  "for THIS producer, task, command and input manifest",
                  faults == [], faults)
    answer["requirement_evaluation"] = {
        "requirements": world.requirements,
        "observation": world.evidence["observation"],
        "faults": faults, "judgement": SIMULATED}
    authority = Authority.open(world.store,
                               expected_authority_uuid=world.uuid)
    try:
        answer["verification"] = authority.session(VERIFIER).verify(
            {"proposal_id": world.proposal_id,
             "verification_id": "w325034-verification",
             "observation": "passed", "operation_id": "w325034-verify"})
        answer["review"] = authority.session(REVIEWER).review(
            {"proposal_id": world.proposal_id,
             "review_id": "w325034-review", "disposition": "accepted",
             "operation_id": "w325034-review"})
        # THE DUPLICATE RETRY, at this boundary: the same identity replays and
        # a different receipt identity collides.
        answer["verify_replay"] = authority.session(VERIFIER).verify(
            {"proposal_id": world.proposal_id,
             "verification_id": "w325034-verification",
             "observation": "passed", "operation_id": "w325034-verify"})
        checks.expect("an identical verification replays its exact receipt",
                      answer["verify_replay"] == answer["verification"],
                      [answer["verify_replay"], answer["verification"]])
        from baton_v12.authority import Refusal

        try:
            authority.session(VERIFIER).verify(
                {"proposal_id": world.proposal_id,
                 "verification_id": "w325034-verification-second",
                 "observation": "passed",
                 "operation_id": "w325034-verify-second"})
            answer["second_verification"] = "ACCEPTED"
        except Refusal as refusal:
            answer["second_verification"] = f"refused: {refusal}"
        checks.expect("a second verification receipt is refused as immutable",
                      "refused" in str(answer["second_verification"]),
                      answer["second_verification"])
    finally:
        authority.dispose()
    now = dispositions(world.receipts())
    checks.expect("verification is passed and review accepted",
                  now["verification"] == "passed"
                  and now["review"] == "accepted", now)
    checks.expect("THE APPROVAL IS STILL ABSENT after both judgments",
                  now["approval"] is None, now)
    answer["receipts_after_judgments"] = now
    answer["receipt_actors"] = {
        kind: (one or {}).get("actor")
        for kind, one in world.receipts().items()}
    checks.expect("the judgments are attributed to the independent "
                  "participants", answer["receipt_actors"]["verification"]
                  == VERIFIER and answer["receipt_actors"]["review"]
                  == REVIEWER, answer["receipt_actors"])
    # -- the owner's half, with every outcome asserted ---------------------
    pending = command("disposition", "pending", *world.base,
                      "--work", world.work_id, "--participant", OWNER)
    checks.expect("pending answers", pending["exit"] == 0, pending["stderr"])
    due = pending["answer"] or {}
    checks.expect("the owner action is approval-due",
                  due.get("owner_action") == "approval-due",
                  due.get("owner_action"))
    answer["pending"] = {"owner_action": due.get("owner_action"),
                         "holds": due.get("holds")}
    candidate = world.proposal["candidate_digest"]
    root = pathlib.Path(world.store).parent / "w325034-integration-root"
    root.mkdir(parents=True, exist_ok=True)
    reference = "INTEGRATION.json"
    (root / reference).write_text(json.dumps(
        {"schema": "baton.v12.human-integration-record/1",
         "authority_uuid": world.uuid, "work_id": world.work_id,
         "proposal_id": world.proposal_id, "candidate_digest": candidate,
         "commit": "0" * 40, "integrated_by": SIMULATED,
         "integrated_at": "2026-10-18T18:20:00Z",
         "notes": "W325034 rehearsal fixture; no human act, no commit."},
        indent=2, sort_keys=True) + "\n")
    # NEGATIVES, each asserted to refuse AND to mutate nothing.
    before = dispositions(world.receipts())
    negatives = {
        "integration with approval withheld": command(
            "disposition", "integrated", *world.base, "--participant", OWNER,
            "--work", world.work_id, "--proposal", world.proposal_id,
            "--expect-candidate-digest", candidate, "--root", str(root),
            "--reference", reference, "--commit", "0" * 40,
            "--integration-id", "early-int",
            "--operation-id", "early-integrated",
            "--evidence-operation-id", "early-citation"),
        "satisfying closure with approval withheld": command(
            "disposition", "close", *world.base, "--participant", OWNER,
            "--work", world.work_id, "--outcome", "satisfying",
            "--rationale", "too early", "--proposal", world.proposal_id,
            "--expect-candidate-digest", candidate, "--root", str(root),
            "--operation-id", "early-close"),
        "stale candidate digest": command(
            "disposition", "approve", *world.base, "--participant", OWNER,
            "--work", world.work_id, "--proposal", world.proposal_id,
            "--expect-candidate-digest", "sha256:" + "a" * 64,
            "--expect-review", "w325034-review",
            "--policy-generation", str(world.generation),
            "--approval-id", "stale-approval",
            "--operation-id", "stale-approve"),
        "wrong review receipt": command(
            "disposition", "approve", *world.base, "--participant", OWNER,
            "--work", world.work_id, "--proposal", world.proposal_id,
            "--expect-candidate-digest", candidate,
            "--expect-review", "not-the-review",
            "--policy-generation", str(world.generation),
            "--approval-id", "wrong-review-approval",
            "--operation-id", "wrong-review-approve"),
        "wrong principal": command(
            "disposition", "approve", *world.base, "--participant", REVIEWER,
            "--work", world.work_id, "--proposal", world.proposal_id,
            "--expect-candidate-digest", candidate,
            "--expect-review", "w325034-review",
            "--policy-generation", str(world.generation),
            "--approval-id", "wrong-actor-approval",
            "--operation-id", "wrong-actor-approve")}
    for what, outcome in negatives.items():
        checks.expect(f"{what} is refused", outcome["exit"] == 2, outcome)
    checks.expect("no receipt changed across every refusal",
                  dispositions(world.receipts()) == before,
                  [before, dispositions(world.receipts())])
    answer["negatives"] = {what: {"exit": one["exit"],
                                  "stderr": one["stderr"][:200]}
                           for what, one in negatives.items()}
    # THE OWNER'S OWN DECISION, then the rest of the chain.
    bound = command("record", "bind", *world.base, "--work", world.work_id,
                    "--locator", "pilot-human-boundary-" + world.uuid[:8],
                    "--operation-id", "w325034-bind")
    checks.expect("the canonical dossier binds", bound["exit"] == 0,
                  bound["stderr"])
    approve = command("disposition", "approve", *world.base,
                      "--participant", OWNER, "--work", world.work_id,
                      "--proposal", world.proposal_id,
                      "--expect-candidate-digest", candidate,
                      "--expect-review", "w325034-review",
                      "--policy-generation", str(world.generation),
                      "--approval-id", "w325034-approval",
                      "--operation-id", "w325034-approve")
    checks.expect("the owner's approval is accepted", approve["exit"] == 0,
                  approve["stderr"])
    replay = command("disposition", "approve", *world.base,
                     "--participant", OWNER, "--work", world.work_id,
                     "--proposal", world.proposal_id,
                     "--expect-candidate-digest", candidate,
                     "--expect-review", "w325034-review",
                     "--policy-generation", str(world.generation),
                     "--approval-id", "w325034-approval",
                     "--operation-id", "w325034-approve")
    checks.expect("an identical owner approval replays", replay["exit"] == 0,
                  replay["stderr"])
    checks.expect("the replay preserves the exact receipt identity",
                  (replay["answer"] or {}).get("approval", {}).get(
                      "receipt_id") == "w325034-approval",
                  replay["answer"])
    integrated = command(
        "disposition", "integrated", *world.base, "--participant", OWNER,
        "--work", world.work_id, "--proposal", world.proposal_id,
        "--expect-candidate-digest", candidate, "--root", str(root),
        "--reference", reference, "--commit", "0" * 40,
        "--integration-id", "w325034-integration",
        "--operation-id", "w325034-integrated",
        "--evidence-operation-id", "w325034-citation")
    checks.expect("the human integration is recorded",
                  integrated["exit"] == 0, integrated["stderr"])
    closed = command("disposition", "close", *world.base,
                     "--participant", OWNER, "--work", world.work_id,
                     "--outcome", "satisfying",
                     "--rationale", "W325034 rehearsal closure (simulated)",
                     "--proposal", world.proposal_id,
                     "--expect-candidate-digest", candidate,
                     "--root", str(root), "--operation-id", "w325034-close")
    checks.expect("the satisfying closure is accepted", closed["exit"] == 0,
                  closed["stderr"])
    readback = command("disposition", "pending", *world.base,
                       "--work", world.work_id, "--participant", OWNER,
                       "--root", str(root))
    said = readback["answer"] or {}
    checks.expect("the readback answers closed",
                  said.get("owner_action") == "closed",
                  said.get("owner_action"))
    checks.expect("the readback carries the selected acceptance",
                  (said.get("closure_acceptance") or {}).get(
                      "candidate_digest") == candidate,
                  said.get("closure_acceptance"))
    checks.expect("the cited human record is intact at readback",
                  (said.get("evidence_now") or {}).get("state") == "intact",
                  said.get("evidence_now"))
    final = world.receipts()
    answer["final_receipts"] = {
        kind: {"actor": (one or {}).get("actor"),
               "disposition": (one or {}).get("disposition"),
               "receipt_id": (one or {}).get("receipt_id")}
        for kind, one in final.items()}
    checks.expect("the four receipts carry their own distinct actors",
                  answer["final_receipts"]["verification"]["actor"] == VERIFIER
                  and answer["final_receipts"]["review"]["actor"] == REVIEWER
                  and answer["final_receipts"]["approval"]["actor"] == OWNER
                  and answer["final_receipts"]["integration"]["actor"]
                  == OWNER, answer["final_receipts"])
    answer["identities"] = {"work_id": world.work_id,
                            "proposal_id": world.proposal_id,
                            "line_id": world.line["line_id"],
                            "implementation_attempt": world.held.attempt_id,
                            "review_attempt": world.held.review,
                            "candidate_digest": candidate}
    answer["labelled"] = SIMULATED
    return answer


SCENARIOS = (
    ("0-harness-self-check", harness_self_check, True,
     "a deliberately false expectation; this scenario MUST fail"),
    ("1-stale-task-withholds-judgment", stale_task_withholds_the_judgment,
     False, "four mutated requirement selections, each of which must withhold "
            "the judgment and write nothing"),
    ("2-evidence-based-judgments-and-owner-chain", evidence_based_judgments,
     False, "the five requirement clauses evaluated, then independent "
            "judgments, the withheld-approval negatives, and the owner's own "
            "decision through to readback"),
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

    from tests.tools.test_stage_execution import (
        TheComposedJobTraversesReviewAndAcceptance as Composed)

    print("W325034 boundary, asserting:")
    for name, body, expected_failure, injected in SCENARIOS:
        at = time.monotonic()
        checks = Checks()
        record = {"scenario": name, "injected": injected,
                  "expected_failure": expected_failure,
                  "simulated": ["engine: no daemon",
                                "provider: injected at the adapter's seam",
                                "verifier/reviewer/owner judgments"],
                  "not_called": ["_accepted_receipts", "admit_accepted",
                                 "continue_accepted", "raw SQL"]}
        case = None
        try:
            case = Composed()
            case.setUp()
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
                    record["cleanup_failure"] = traceback.format_exc()[-800:]
        record["checks"] = checks.document()
        record["seconds"] = round(time.monotonic() - at, 3)
        failed = record["outcome"] == "failed"
        if failed != expected_failure:
            unexpected += 1
            record["unexpected"] = True
        answers.append(record)
        say(place, f"scenario-{name}.json", record)
        passed = sum(1 for one in record["checks"] if one.get("passed"))
        print(f"  {name}: {record['outcome']} "
              f"({passed} checks passed"
              f"{', expected failure' if failed and expected_failure else ''}"
              f"{', UNEXPECTED' if record.get('unexpected') else ''}) "
              f"{record['seconds']}s")

    answer = {"schema": "baton.w325034.boundary/2",
              "supersedes": "boundary-325098 (preserved; its raw-SQL read and "
                            "unconditional judgments are corrected here and "
                            "in its SUPERSESSION.md)",
              "scenarios": answers,
              "checks_passed": sum(
                  sum(1 for check in one["checks"] if check.get("passed"))
                  for one in answers),
              "observed": sum(1 for one in answers
                              if one["outcome"] == "observed"),
              "failed_as_expected": sum(
                  1 for one in answers if one["outcome"] == "failed"
                  and one["expected_failure"]),
              "unexpected": unexpected,
              "harness_self_check_failed_as_it_must": any(
                  one["scenario"] == "0-harness-self-check"
                  and one["outcome"] == "failed" for one in answers),
              "seconds": round(time.monotonic() - started, 3)}
    say(place, "BOUNDARY2.json", answer)
    print(f"checks passed {answer['checks_passed']}, observed "
          f"{answer['observed']}, failed-as-expected "
          f"{answer['failed_as_expected']}, unexpected {unexpected}, "
          f"{answer['seconds']}s")
    if not answer["harness_self_check_failed_as_it_must"]:
        print("REFUSED: the self-check did not fail, so nothing here is "
              "checking anything")
        return 2
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
