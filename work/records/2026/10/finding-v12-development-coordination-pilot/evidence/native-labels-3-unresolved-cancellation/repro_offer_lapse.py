"""Bounded deterministic reproduction of native-labels-3's unresolved cancellation.

WHAT IT DRIVES. Real Job store, real control store, the real `ManagerOperations`
(offers, acceptance, claim submission) over the fixture Authority session; only
the Authority's claim answer is a stand-in, and it answers exactly what
native-labels-3's Authority answered: a non-durable `refused/precondition`
"route ... does not resolve to ...", the shape `single_worker._claim_refusal`
produces. The Job is admitted under control profile `documentation/1`, the
profile `w29401-labels-2` was created under, so the stage deadline is the
real 4800 s.

WHAT IT SHOWS, in order:
  1. admit issues the offer; the single-worker composition accepts it;
  2. every serving tick re-submits the claim, the Authority refuses it on the
     route, nothing is recorded on the offer -- including after the offer's
     own 120 s TTL has elapsed, because the claim path never reads expiry;
  3. the stage deadline fences the Job; from then on no claim is owed, the
     cancellation pass has no effect to order for an offered stage with no
     attempt row, and the accepted offer is never settled: the target is
     reported `awaiting-offer-lapse` and the shutdown `unresolved` forever;
  4. a read-only report (what `manager cancel-status` composes) says the same;
  5. a manager RESTART does NOT settle it: `recover_on_restart` reports the
     ACCEPTED offer as recoverable (`expire_overdue` CASes from `issued`
     only), the attach republishes `accepted`, which ends nothing, the fence
     keeps the claim from being owed, and the report stays `unresolved`;
     nothing is replaced, admitted, claimed or launched by the restart;
  6. the retirement the owners designed for exactly this -- `settle_claim`
     with positive refusal evidence, which records `claim-refused` on the
     offer and ends the episode -- settles the report `complete` when it is
     called; it has no production caller (the fixture session answers the
     Authority's settlement read here, so this step proves the Job-store
     side only).

Run from `v12/python` with the prepared interpreter and `PYTHONPATH=src:.`.
Not a registered test module; evidence for the owning dossier only.
"""

import json
import sqlite3
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.job_manager import (JobStore, ManagerOperations, cancellation,
                                   documents, episodes_of, live_of, reconcile,
                                   status, submit, sweep)
from baton_v12.worker_manager import AuthorityPort, accept_offer

from tests.job_manager.fixtures import (NOW, UUID, WORK_A, WORK_B,
                                        JobManagerCase, fake_claim_signature,
                                        job, stage, submission)
from tests.job_manager.test_job_control import PROFILE, STAGE_SECONDS, at

ROUTE_REFUSAL = ("the authority refused this claim: route 'baton.impl' does "
                 "not resolve to 'baton.claude-native'")
IMPL = "job-a/implementation"
REVIEW = "job-a/review"


def show(label, value):
    print(f"--- {label}")
    print(json.dumps(value, indent=1, sort_keys=True, default=str))


class OfferedStageUnderDeadlineFence(JobManagerCase):

    def setUp(self):
        super().setUp()
        self.session.claim_answer = ContractRefusal("refused", "precondition",
                                                    ROUTE_REFUSAL)
        self.jobs = self.store()
        self.first = self.operations(control=self.control())
        held = job("job-a", stages=[
            stage("implementation", WORK_A),
            stage("review", WORK_B, depends_on=[{"job_id": "job-a",
                                                 "kind": "implementation"}])])
        held["control"] = {"profile": PROFILE}
        document = submission(jobs=[held])
        document["schema"] = documents.SUBMISSION_CONTROL_SCHEMA
        submit(self.jobs, document)

    # -- helpers -------------------------------------------------------------

    def tick(self, acts, seconds):
        self.instants.append(at(seconds))
        return sweep(self.jobs, acts, now=at(seconds))

    def entry(self, acts, seconds):
        self.instants.append(at(seconds))
        document = status(self.jobs, acts, observed_at=at(seconds))
        [held] = [one for one in document["jobs"] if one["job_id"] == "job-a"]
        return held

    def offer_states(self, control):
        return {row["offer_id"][:14]: row["state"] for row in
                control._connection.execute("SELECT offer_id, state FROM offers")}

    def attempt_rows(self, control):
        return control._connection.execute(
            "SELECT count(*) AS n FROM attempts").fetchone()["n"]

    def claim_calls(self):
        return len([one for one in self.session.calls if one[0] == "claim"])

    def targets(self, report):
        return {one["stage_id"]: one["state"] for one in report["targets"]}

    # -- the reproduction ----------------------------------------------------

    def test_a_route_refused_offer_never_lapses_while_serving_and_settles_on_restart(self):
        control = self.first.control
        # 1. ADMIT, then the single-worker composition accepts on delivery.
        report = self.tick(self.first, 0)
        self.assertEqual([(one["act"], one["outcome"], one["episode"])
                          for one in report["acts"]], [("admit", "performed", 1)])
        row = self.attempting(self.jobs)
        accept_offer(control, self.first.port, offer_id=row["offer_id"],
                     decision="accept", bearer=self.delivered[-1]["bearer"],
                     now=at(1), runtime_attempt_id=row["attempt_id"],
                     work_ref={"authority_uuid": UUID, "work_id": WORK_A})
        self.assertEqual(self.offer_states(control), {row["offer_id"][:14]: "accepted"})

        # 2. THE CLAIM IS RE-SUBMITTED EVERY TICK AND REFUSED ON THE ROUTE,
        # before and after the offer's own 120 s TTL; the offer row is never
        # touched by the claim path.
        for seconds in (5, 25, 130, 600):
            report = self.tick(self.first, seconds)
            [claim] = [one for one in report["acts"] if one["act"] == "claim"]
            self.assertEqual(claim["outcome"], "deferred", claim)
            self.assertEqual(claim["detail"]["message"], ROUTE_REFUSAL, claim)
            self.assertEqual(self.offer_states(control)[row["offer_id"][:14]], "accepted")
        self.assertEqual(self.attempt_rows(control), 0)
        before = self.entry(self.first, 600)
        impl = [one for one in before["stages"] if one["stage_id"] == IMPL][0]
        self.assertEqual(impl["state"], "offered")
        self.assertEqual(impl["deferral"][0]["message"], ROUTE_REFUSAL)
        self.assertTrue(impl["deferral"][0]["outstanding"])
        self.assertIsNone(before["cancellation"])
        show("status before the fence (implementation deferral)", impl["deferral"])

        # 3. THE STAGE DEADLINE FENCES THE JOB. Nothing is owed any more, the
        # cancellation pass orders nothing, the offer stays `accepted`.
        report = self.tick(self.first, STAGE_SECONDS + 5)
        show("sweep report at the stage deadline", {k: report[k] for k in ("acts", "expired", "cancelled") if k in report})
        self.assertEqual([one["trigger"] for one in report["expired"]], ["stage-deadline"])
        claims = self.claim_calls()
        for seconds in (STAGE_SECONDS + 10, STAGE_SECONDS + 100, STAGE_SECONDS + 130,
                        STAGE_SECONDS + 3000, STAGE_SECONDS + 21655):
            report = self.tick(self.first, seconds)
            self.assertEqual(report["acts"], [], report["acts"])
            self.assertEqual(report.get("cancelled", []), [])
            self.assertEqual(report["replaced"], [])
            self.assertEqual(report["started"], [])
        self.assertEqual(self.claim_calls(), claims, "no claim after the fence")
        self.assertEqual(self.offer_states(control)[row["offer_id"][:14]], "accepted")
        self.assertEqual(self.attempt_rows(control), 0)
        fenced = self.entry(self.first, STAGE_SECONDS + 21655)
        held = fenced["cancellation"]
        show("cancellation report while serving, 21655 s after the fence", held)
        self.assertEqual(held["trigger"], "stage-deadline")
        self.assertEqual(held["shutdown"], "unresolved")
        self.assertEqual(held["elapsed_seconds"], 21655)
        self.assertEqual(self.targets(held), {IMPL: "awaiting-offer-lapse",
                                              REVIEW: "retired-before-admission"})
        self.assertEqual([(one["episode"], one["ended_state"]) for one in episodes_of(self.jobs, IMPL)], [(1, None)])
        self.assertEqual(self.claim_calls(), claims)

        # 4. THE READ-ONLY REPORT `cancel-status` COMPOSES says the same: the
        # store's rows, not a serving manager's memory, carry the state.
        reader = JobStore.open_readonly(self.job_path, authority_uuid=UUID,
                                        incarnation="cancellation-reader",
                                        clock=self.clock)
        try:
            read = cancellation.report(
                reader, "job-a", now=at(STAGE_SECONDS + 21700),
                observed_of=lambda entry: cancellation.observed_from(
                    control, entry["attempt"]["attempt_id"]))
        finally:
            reader.close()
        self.assertEqual(read["shutdown"], "unresolved")
        self.assertEqual(self.targets(read), self.targets(held))

        # 5. A MANAGER RESTART. `reconcile` recovers first: `expire_overdue`
        # settles the elapsed offer, the attach republishes the row, and the
        # episode ends `expired`. Fenced, so nothing is replaced, admitted,
        # claimed or launched.
        self.jobs.close()
        resumed = JobStore.open(self.job_path, authority_uuid=UUID,
                                incarnation="jobs-2", clock=self.clock)
        self.addCleanup(resumed.close)
        self.jobs = resumed
        second = ManagerOperations(self.control(incarnation="manager-2"),
                                   AuthorityPort(self.session, fake_claim_signature),
                                   mint_bearer=self.mint, deliver_bearer=self.deliver)
        self.instants.append(at(STAGE_SECONDS + 22000))
        report = reconcile(resumed, second, now=at(STAGE_SECONDS + 22000))
        show("reconcile report on restart", {k: report[k] for k in ("recovered", "observed", "replaced", "acts", "started", "cancelled") if k in report})
        self.assertEqual(report["replaced"], [])
        self.assertEqual(report["acts"], [])
        self.assertEqual(report["started"], [])
        show("offer states after the restart", self.offer_states(second.control))
        show("implementation episodes after the restart", [(one["episode"], one["ended_state"], one["ended_at"]) for one in episodes_of(resumed, IMPL)])
        self.assertEqual(self.claim_calls(), claims, "no claim on restart")
        self.assertEqual(self.attempt_rows(second.control), 0)
        self.assertEqual(len(self.minted), 1, "no second offer was minted")
        after = self.entry(second, STAGE_SECONDS + 22010)
        settled = after["cancellation"]
        show("cancellation report after the restart", settled)
        show("stage states after the restart", {one["stage_id"]: one["state"] for one in after["stages"]})
        self.assertEqual([one["offer_id"] for one in report["recovered"]["recoverable"]], [row["offer_id"]])
        self.assertEqual(self.offer_states(second.control)[row["offer_id"][:14]], "accepted")
        self.assertEqual([(one["episode"], one["ended_state"]) for one in episodes_of(resumed, IMPL)], [(1, None)])
        self.assertEqual(settled["shutdown"], "unresolved")
        self.assertEqual(self.targets(settled), self.targets(held))
        for seconds in (STAGE_SECONDS + 22100, STAGE_SECONDS + 30000):
            report = self.tick(second, seconds)
            self.assertEqual((report["acts"], report["replaced"], report["started"]), ([], [], []))
            self.assertEqual(report.get("cancelled", []), [])
        self.assertEqual(self.claim_calls(), claims)
        self.assertEqual(self.offer_states(second.control)[row["offer_id"][:14]], "accepted")
        self.assertEqual(self.entry(second, STAGE_SECONDS + 30001)["cancellation"]["shutdown"], "unresolved")

        # 6. THE DESIGNED RETIREMENT, uncalled in production: positive refusal
        # evidence lets `settle_claim` retire the accepted offer at once. The
        # fixture session answers the Authority's settlement read as
        # `refused`, so what this proves is the Job-store side: the offer is
        # recorded `claim-refused`, the episode ends, the report completes.
        from baton_v12.worker_manager import settle_claim
        self.session.settle_answer = {"kind": "refused", "detail": ROUTE_REFUSAL}
        settlement = settle_claim(second.control, second.port, offer_id=row["offer_id"],
                                  now=at(STAGE_SECONDS + 30100), refused_evidence=ROUTE_REFUSAL)
        show("settle_claim with refusal evidence", settlement)
        self.assertEqual(self.offer_states(second.control)[row["offer_id"][:14]], "claim-refused")
        # The settlement reaches the Job store as an offer-state assertion,
        # which this build publishes only on attach (a resume); an ordinary
        # tick first adopts the committed `offer.settle` row as a performed
        # claim instead -- retained in repro_offer_lapse-settle-in-tick.log.
        # So the ending is observed through a restart here.
        resumed.close()
        third = JobStore.open(self.job_path, authority_uuid=UUID,
                              incarnation="jobs-3", clock=self.clock)
        self.addCleanup(third.close)
        self.jobs = third
        last = ManagerOperations(self.control(incarnation="manager-3"),
                                 AuthorityPort(self.session, fake_claim_signature),
                                 mint_bearer=self.mint, deliver_bearer=self.deliver)
        self.instants.append(at(STAGE_SECONDS + 30200))
        report = reconcile(third, last, now=at(STAGE_SECONDS + 30200))
        show("reconcile report after the retirement", {k: report[k] for k in ("recovered", "acts", "replaced", "started", "cancelled", "observed") if k in report})
        self.assertEqual(report["observed"], 1)
        self.assertEqual((report["acts"], report["replaced"], report["started"]), ([], [], []))
        self.assertEqual(report.get("cancelled", []), [])
        self.assertEqual([(one["episode"], one["ended_state"]) for one in episodes_of(third, IMPL)], [(1, "claim-refused")])
        second = last
        final = self.entry(second, STAGE_SECONDS + 30201)
        show("final cancellation report", final["cancellation"])
        show("final stage states", {one["stage_id"]: one["state"] for one in final["stages"]})
        self.assertEqual(final["cancellation"]["shutdown"], "complete")
        self.assertEqual(self.targets(final["cancellation"]), {IMPL: "ceased",
                                                               REVIEW: "retired-before-admission"})
        self.assertEqual(self.claim_calls(), claims)
        self.assertEqual(self.attempt_rows(second.control), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
