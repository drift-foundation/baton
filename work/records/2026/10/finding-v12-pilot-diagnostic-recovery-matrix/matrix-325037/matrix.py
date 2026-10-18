"""W325035 — the joined diagnostic and recovery matrix, driven case by case.

LINEAGE AND PROVENANCE. This reuses the composed native Job fixture the parent
W321690 drove (`work/records/2026/10/finding-v12-pilot-workflow-rehearsal/
rehearsal-324890/joined_rehearsal.py`), by IMPORTING the accepted world
`tests.tools.test_stage_execution.ComposedOneJobCase` and its subclasses rather
than by modifying the parent's evidence. Nothing in the parent's dossier is
edited by this file.

WHAT IS REAL. `tools.stage_execution`'s own `operations_from` composition; real
Authority, Job, Control and Integration stores on disposable paths; a real
version-controlled line materialized by the accepted checkpoint profile; the
actual `claude_agent` workload entered through `baton_worker.serve_exchange`;
`review_driver`'s endings; the manager's own `sweep` for every transition.

WHAT IS SIMULATED, LABELLED PER SCENARIO. The ENGINE answers without a daemon.
The PROVIDER is injected at the one process seam the adapter already has: a
scenario that needs a failed or empty provider turn sets its exit status or its
edits and nothing else. NOTHING here claims live isolation or engine evidence,
and no owner receipt, candidate or verdict is fabricated: every durable fact
below is written by the product's own operations.

WHAT IS NOT REACHED: no daemon, no container, no image, no network, no live
model, no live credential, no deployment, no raw SQL, no Git mutation.

Each scenario records its own exact Work/Job/attempt/proposal identities, its
assertions, its measured duration and its injected inputs, and a scenario that
fails records the failure rather than taking the others down with it.

Run from `v12/python`:

    PYTHONPATH=src:. python3 <this file> --evidence <directory>
"""
import argparse
import json
import os
import pathlib
import time
import traceback

PROVENANCE = {
    "fixture_lineage": "tests.tools.test_stage_execution ComposedOneJobCase "
                       "and TheComposedJobTraversesReviewAndAcceptance",
    "parent_driver": "work/records/2026/10/finding-v12-pilot-workflow-"
                     "rehearsal/rehearsal-324890/joined_rehearsal.py",
    "reuse": "imported, not modified; the parent's evidence is untouched",
}


def receipts_of(authority, proposal_id):
    return {kind: authority.receipt(proposal_id, kind)
            for kind in ("verification", "review", "approval",
                         "integration")}


def proposals_of(store, uuid, work_id):
    from baton_v12.authority import Authority

    authority = Authority.open_readonly(store, expected_authority_uuid=uuid)
    try:
        held = authority.proposals_of(work_id)
        return [dict(one, receipts=receipts_of(authority,
                                               one["proposal_id"]))
                for one in held]
    finally:
        authority.dispose()


class Matrix:
    """One scenario per method; each builds its own disposable world."""

    def __init__(self, place):
        self.place = place
        self.answers = []

    def world(self, kind="composed"):
        from tests.tools.test_stage_execution import (
            TheComposedJobTraversesReviewAndAcceptance as Composed)

        case = Composed()
        case.setUp()
        return case

    @staticmethod
    def settle(case, job, composed, ticks=12):
        """Ordinary ticks, reporting where the manager SETTLES.

        `case.drive` asserts a wanted state, which is right for a test and
        wrong for a matrix: a failed or empty turn is supposed NOT to reach
        completion, and the useful record is the state the manager actually
        held after its own sweeps plus how many it took.
        """
        from baton_v12.job_manager import sweep as tick
        from tests.job_manager import fixtures

        seen = []
        for _ in range(ticks):
            tick(job, composed, now=fixtures.NOW)
            held = case.states(job, composed)
            if not seen or seen[-1] != held:
                seen.append(held)
        return {"settled": case.states(job, composed), "progression": seen,
                "ticks": ticks}

    def identities(self, case, held=None):
        work_id = case.submission["jobs"][0]["stages"][0]["work_id"]
        answer = {"work_id": work_id,
                  "job_id": case.submission["jobs"][0]["job_id"],
                  "submission_id": case.submission["submission_id"],
                  "authority_uuid": case.config["authority_uuid"]}
        if held is not None:
            answer["implementation_attempt"] = getattr(held, "attempt_id",
                                                       None)
            answer["review_attempt"] = getattr(held, "review", None)
        return answer

    def run(self, name, body, *, injected, asserts):
        started = time.monotonic()
        record = {"scenario": name, "injected": injected,
                  "asserted": asserts,
                  "simulated": ["engine: answers run/inspect/ps with no "
                                "daemon",
                               "provider: injected at the adapter's process "
                               "seam"]}
        case = None
        try:
            case = self.world()
            record.update(body(case) or {})
            record["outcome"] = "observed"
        except Exception:                                    # noqa: BLE001
            record["outcome"] = "failed"
            record["failure"] = traceback.format_exc()[-2400:]
        finally:
            if case is not None:
                try:
                    case.doCleanups()
                except Exception:                            # noqa: BLE001
                    record.setdefault("cleanup_failure",
                                      traceback.format_exc()[-800:])
        record["seconds"] = round(time.monotonic() - started, 3)
        self.answers.append(record)
        (self.place / f"scenario-{name}.json").write_text(
            json.dumps(record, indent=2, sort_keys=True, default=str) + "\n")
        print(f"  {name}: {record['outcome']} ({record['seconds']}s)")
        return record

    # -- 1. the diagnostic owner ------------------------------------------

    def provider_failed(self, case):
        """A provider turn that exits non-zero produces no candidate."""
        job, control, composed = case.serving()
        from baton_v12.job_manager import submit as submit_jobs

        submit_jobs(job, case.submission)
        case.drive(job, composed, "implementation", "waiting")
        attempt = case.only_attempt(composed, "implementation")
        roots = case.mounted(composed, "implementation", attempt)
        status = case.turn(control, "implementation", attempt, roots,
                           edits={}, status=1)
        answer = {"identities": dict(self.identities(case),
                                     implementation_attempt=attempt),
                  "worker_turn_exit": status,
                  "stage_states_after_turn": case.states(job, composed),
                  "after_ordinary_ticks": self.settle(case, job, composed)}
        # THE DIAGNOSTIC OWNER, asked for rather than inferred, and asked
        # AFTER the manager's own sweeps have settled.
        from baton_v12.job_manager.ending import pending_endings

        answer["pending_endings"] = [
            {k: v for k, v in one.items()
             if k in ("stage_id", "kind", "attempt_id", "state", "cause",
                      "disposition", "detail", "owner", "episode")}
            for one in pending_endings(job)] if callable(pending_endings) \
            else str(pending_endings)
        answer["proposals"] = proposals_of(case.authority_path,
                                           case.config["authority_uuid"],
                                           answer["identities"]["work_id"])
        return answer

    def no_candidate(self, case):
        """A provider turn that exits zero and changes nothing."""
        job, control, composed = case.serving()
        from baton_v12.job_manager import submit as submit_jobs
        from baton_v12.job_manager.ending import pending_endings

        submit_jobs(job, case.submission)
        case.drive(job, composed, "implementation", "waiting")
        attempt = case.only_attempt(composed, "implementation")
        roots = case.mounted(composed, "implementation", attempt)
        status = case.turn(control, "implementation", attempt, roots,
                           edits={}, status=0)
        return {"identities": dict(self.identities(case),
                                   implementation_attempt=attempt),
                "worker_turn_exit": status,
                "stage_states_after_turn": case.states(job, composed),
                "after_ordinary_ticks": self.settle(case, job, composed),
                "pending_endings": [dict(one) for one in
                                    pending_endings(job)],
                "proposals": proposals_of(
                    case.authority_path, case.config["authority_uuid"],
                    self.identities(case)["work_id"])}

    # -- 2. restart and a lost reply --------------------------------------

    def restart_no_duplicate(self, case):
        """A fresh serving object over the same stores, mid-flight."""
        held = case.implemented()
        before = case.states(held.job, held.composed)
        attempts_before = case.only_attempt(held.composed, "implementation")
        # THE RESTART: a new composition over the SAME stores, which is what an
        # ordinary manager restart is. Nothing is reset by hand.
        job, control, composed = case.serving()
        case.drive(job, composed, "review", "waiting")
        review_attempt = case.only_attempt(composed, "review")
        after = case.states(job, composed)
        return {"identities": dict(self.identities(case, held),
                                   review_attempt_after_restart=
                                   review_attempt),
                "stage_states_before_restart": before,
                "stage_states_after_restart": after,
                "implementation_attempt_unchanged":
                    attempts_before == held.attempt_id,
                "one_review_attempt": review_attempt,
                "proposals": proposals_of(
                    case.authority_path, case.config["authority_uuid"],
                    self.identities(case)["work_id"])}

    # -- 3. stale episode and wrong principal -----------------------------

    def stale_and_wrong_principal(self, case):
        """The authority's own refusals, asked through real sessions."""
        from baton_v12.authority import Authority, Refusal

        # STOPPED WHERE AN ASSIGNMENT IS LIVE. `implemented()` carries the
        # stage to its ending, which releases the assignment -- so a stale or
        # wrong-principal act would have had nothing to be refused against.
        from baton_v12.job_manager import submit as submit_jobs

        job, control, composed = case.serving()
        submit_jobs(job, case.submission)
        case.drive(job, composed, "implementation", "waiting")
        held = None
        work_id = self.identities(case)["work_id"]
        uuid = case.config["authority_uuid"]
        authority = Authority.open(case.authority_path,
                                   expected_authority_uuid=uuid)
        refusals = {}
        try:
            live = authority.assignment_of(work_id)
            if live is None:
                refusals["no_live_assignment"] = True
            else:
                stale = dict(live, generation=(live.get("generation") or 1)
                             + 7)
                for what, operands, participant in (
                        ("stale episode",
                         {"expect": stale, "operation_id": "m-stale",
                          "reason": "stale"}, live["participant"]),
                        ("wrong principal",
                         {"expect": live, "operation_id": "m-wrong",
                          "reason": "not mine"}, "baton.gemini")):
                    try:
                        authority.session(participant).cancel(operands)
                        refusals[what] = "ACCEPTED (no refusal)"
                    except Refusal as refusal:
                        refusals[what] = str(refusal)
            answer = {"live_assignment": live, "refusals": refusals}
        finally:
            authority.dispose()
        answer["identities"] = self.identities(case, held)
        return answer

    # -- 4. the correction round ------------------------------------------

    def correction_binding(self, case):
        """A changes-requested verdict, and what the correction is bound to."""
        held = case.reviewed(verdict="changes-requested")
        states = case.states(held.job, held.composed)
        settled = self.settle(case, held.job, held.composed)
        # THE CORRECTION ROUND, driven: the reopened implementation stage gets
        # a NEW attempt while the Work and Job identities are unchanged, which
        # is what "bound to the exact candidate and attempt" has to mean.
        corrected = {}
        try:
            case.drive(held.job, held.composed, "implementation", "waiting")
            # THE ATTEMPTS, LISTED rather than asserted to be one: a
            # correction round legitimately gives the reopened stage a SECOND
            # attempt, and that is the binding this scenario is about.
            prepared = sorted(case.worker_of(held.composed,
                                             "implementation").stage._prepared)
            corrected = {"implementation_attempts": prepared,
                         "first_attempt": held.attempt_id,
                         "correction_attempt": [one for one in prepared
                                                if one != held.attempt_id],
                         "first_attempt_retained":
                             held.attempt_id in prepared,
                         "states": case.states(held.job, held.composed)}
        except Exception as failure:                          # noqa: BLE001
            corrected = {"detail": f"{type(failure).__name__}: {failure}"}
        return {"identities": self.identities(case, held),
                "stage_states_after_verdict": states,
                "after_ordinary_ticks": settled,
                "correction_round": corrected,
                "proposals": proposals_of(
                    case.authority_path, case.config["authority_uuid"],
                    self.identities(case)["work_id"])}

    # -- 5. cancellation and a non-satisfying ending ----------------------

    def cancellation_and_non_satisfying(self, case):
        """Cancel the live assignment, then close the Work non-satisfying."""
        import io
        from contextlib import redirect_stderr, redirect_stdout

        from baton_v12.authority import Authority
        from tools import stack_command

        held = case.implemented()
        work_id = self.identities(case)["work_id"]
        uuid = case.config["authority_uuid"]
        answer = {"identities": self.identities(case, held)}
        authority = Authority.open(case.authority_path,
                                   expected_authority_uuid=uuid)
        try:
            live = authority.assignment_of(work_id)
            answer["live_before_cancel"] = live
            if live is not None:
                answer["cancelled"] = authority.session(
                    live["participant"]).cancel(
                    {"expect": live, "operation_id": "m-cancel",
                     "reason": "W325035 matrix cancellation"})
            answer["work_after_cancel"] = {
                k: v for k, v in authority.project_work(work_id).items()
                if k in ("status", "phase", "gate", "handler", "outcome")}
            scope = authority.project_work(work_id)["scope"]
            authority.grant_capability("baton.slaw", "close", scope=scope)
        finally:
            authority.dispose()
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = stack_command.main([
                "disposition", "close",
                "--authority-store", case.authority_path,
                "--authority-uuid", uuid, "--participant", "baton.slaw",
                "--work", work_id, "--outcome", "non-satisfying",
                "--rationale", "W325035 matrix: honest non-satisfying ending",
                "--operation-id", "m-close"])
        answer["close"] = {"exit": code, "stderr": err.getvalue(),
                           "answer": json.loads(out.getvalue())
                           if out.getvalue().strip() else None}
        authority = Authority.open_readonly(case.authority_path,
                                            expected_authority_uuid=uuid)
        try:
            answer["work_after_close"] = {
                k: v for k, v in authority.project_work(work_id).items()
                if k in ("status", "phase", "outcome", "rationale")}
            answer["evidence_preserved"] = {
                "proposals": [one["proposal_id"] for one in
                              authority.proposals_of(work_id)],
                "dossier": authority.dossier_of(work_id)}
        finally:
            authority.dispose()
        return answer

    # -- 6. one writable authority ----------------------------------------

    def one_writable_authority(self, case):
        """A second writable open of the same store, and a read-only one."""
        from baton_v12.authority import Authority, Refusal

        uuid = case.config["authority_uuid"]
        held = Authority.open(case.authority_path,
                              expected_authority_uuid=uuid)
        answer = {"identities": self.identities(case)}
        try:
            try:
                second = Authority.open(case.authority_path,
                                        expected_authority_uuid=uuid)
                answer["second_writable_open"] = "ACCEPTED"
                second.dispose()
            except Refusal as refusal:
                answer["second_writable_open"] = f"refused: {refusal}"
            reader = Authority.open_readonly(case.authority_path,
                                             expected_authority_uuid=uuid)
            try:
                answer["read_only_open"] = "accepted, and it performs nothing"
                try:
                    reader.session("baton.claude").close(
                        {"work_id": self.identities(case)["work_id"],
                         "operation_id": "m-readonly",
                         "outcome": "cancelled", "rationale": "should refuse"})
                    answer["read_only_transition"] = "ACCEPTED"
                except Refusal as refusal:
                    answer["read_only_transition"] = f"refused: {refusal}"
            finally:
                reader.dispose()
            # TWO WRITABLE HANDLES RACING ONE CLAIM. A second handle is what
            # SQLite allows; what must not be allowed is two live claims, and
            # that is the slot's own compare-and-swap rather than the file's.
            work_id = self.identities(case)["work_id"]
            racing = {}
            try:
                first = Authority.open(case.authority_path,
                                       expected_authority_uuid=uuid)
                second = Authority.open(case.authority_path,
                                        expected_authority_uuid=uuid)
                try:
                    racing["first_claim"] = first.session(
                        "baton.claude").claim(
                        {"work_id": work_id, "operation_id": "m-race-1"}
                    )["assignment"]
                except Refusal as refusal:
                    racing["first_claim"] = f"refused: {refusal}"
                try:
                    second.session("baton.reviewer").claim(
                        {"work_id": work_id, "operation_id": "m-race-2"})
                    racing["second_claim"] = "ACCEPTED"
                except Refusal as refusal:
                    racing["second_claim"] = f"refused: {refusal}"
                first.dispose()
                second.dispose()
            except Exception as failure:                      # noqa: BLE001
                racing["detail"] = f"{type(failure).__name__}: {failure}"
            answer["two_handles_racing_one_claim"] = racing
            answer["wrong_authority_uuid"] = None
            try:
                Authority.open_readonly(case.authority_path,
                                        expected_authority_uuid="f" * 32)
                answer["wrong_authority_uuid"] = "ACCEPTED"
            except Refusal as refusal:
                answer["wrong_authority_uuid"] = f"refused: {refusal}"
        finally:
            held.dispose()
        return answer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", required=True)
    taken = parser.parse_args()
    place = pathlib.Path(taken.evidence).resolve()
    place.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()

    matrix = Matrix(place)
    print("W325035 matrix:")
    matrix.run("1a-provider-failed", matrix.provider_failed,
               injected="provider exits 1 and writes nothing",
               asserts="no candidate is published, the stage does not "
                       "complete, and an ending is pending for a diagnostic "
                       "owner")
    matrix.run("1b-no-candidate", matrix.no_candidate,
               injected="provider exits 0 and writes nothing",
               asserts="an empty turn does not become an accepted proposal")
    matrix.run("2-restart-no-duplicate", matrix.restart_no_duplicate,
               injected="a fresh serving composition over the same stores",
               asserts="the implementation attempt is unchanged and exactly "
                       "one review attempt exists after the restart")
    matrix.run("3-stale-and-wrong-principal",
               matrix.stale_and_wrong_principal,
               injected="a stale generation, and another participant's "
                        "session",
               asserts="both are refused by the authority")
    matrix.run("4-correction-binding", matrix.correction_binding,
               injected="a changes-requested review verdict",
               asserts="the correction round stays bound to the same "
                       "candidate and attempt")
    matrix.run("5-cancellation-and-non-satisfying",
               matrix.cancellation_and_non_satisfying,
               injected="a cancellation of the live assignment",
               asserts="the Work ends honestly and its evidence is preserved")
    matrix.run("6-one-writable-authority", matrix.one_writable_authority,
               injected="a second writable open, a read-only open, and a "
                        "wrong authority uuid",
               asserts="one writer, a reader that performs nothing, and an "
                       "exact identity check")

    answer = {"schema": "baton.w325035.matrix/1",
              "provenance": PROVENANCE,
              "boundary": "real coordination on disposable stores; engine and "
                          "provider simulated at their own boundary and "
                          "labelled per scenario; no daemon, container, "
                          "image, network, live model, live credential, "
                          "deployment, raw SQL or Git mutation",
              "scenarios": matrix.answers,
              "observed": sum(1 for one in matrix.answers
                              if one["outcome"] == "observed"),
              "failed": sum(1 for one in matrix.answers
                            if one["outcome"] == "failed"),
              "seconds": round(time.monotonic() - started, 3)}
    (place / "MATRIX.json").write_text(
        json.dumps(answer, indent=2, sort_keys=True, default=str) + "\n")
    print(f"observed {answer['observed']}, failed {answer['failed']}, "
          f"{answer['seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
