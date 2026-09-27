"""W275776 R2 — the ACTUAL worker, killed inside its launch, then restarted.

The review is explicit that finding a `reconcile_runtime` branch in `single_worker` is not
proof that a persisted restart state reaches it. So this drives the REAL composed worker --
`single_worker.operations_from` over real stores, the worker suite's own engine boundary, and
the job manager's own reconcile tick -- kills the engine inside the two-act launch, and then
resumes with fresh stores and the same engine memory.

What it asserts is section 17's Recovery row on the connected path, and the prose says exactly
what the assertions say -- W275776 review 2026-09-27T12-00-40Z caught this paragraph claiming
"ONE activation" and "a resolved generation" when the cases assert ZERO activations and a token
that is still HELD and unresolved. Corrected: the resume composes NO second container and
performs NO activation, the generation stays held and unresolved, and nothing is returned or
replaced on the way.

Deterministic engine double, no live Docker, no provider. Run standalone.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "v12", "python"))

from baton_v12.job_manager import reconcile, status, submit
from baton_v12.worker_manager import attempts as manager_attempts
from baton_v12.worker_manager import tokens

from tests.job_manager import fixtures
from tests.tools.test_single_worker import Engine, SingleWorkerCase, activating

from tools import single_worker


class Dying(Engine):
    """The worker suite's own engine, which stops answering after the container exists.

    `create` composes the container and succeeds -- so the engine really holds it -- and the
    next vector for this attempt faults, which is what a manager losing its engine mid-launch
    leaves behind. `revive()` puts the same engine back, with its container still there.
    """

    def __init__(self):
        super().__init__()
        self.alive = True

    def __call__(self, argv, *, seconds=None):
        answered = super().__call__(argv, seconds=seconds)
        if not self.alive and not activating(argv) and argv[1] != "ps" \
                and argv[1] != "inspect":
            raise OSError("the engine stopped answering")
        if self.alive and argv[1] in ("create", "run"):
            # THE CONTAINER EXISTS NOW, and the engine dies before it can be started.
            self.alive = False
            raise OSError("the engine stopped answering after creating the container")
        return answered

    def revive(self):
        self.alive = True
        return self


class DyingAtActivation(Engine):
    """The container is created AND bound, and the engine dies on the activation vector.

    `oci.OciAdapter.start` composes `create`, then binds the container to the token and asks
    the admission, and only then runs the activation. So an engine that answers `create` and
    faults on `start` leaves `admitted-unsettled`: the manager asked for the activation and
    never learned whether it happened.
    """

    def __init__(self):
        super().__init__()
        self.alive = True

    def __call__(self, argv, *, seconds=None):
        if self.alive and activating(argv):
            self.alive = False
            raise OSError("the engine stopped answering at the activation")
        return super().__call__(argv, seconds=seconds)

    def revive(self):
        self.alive = True
        return self


class TheWorkerResumesItsOwnLaunchWithoutDispatchingAgain(SingleWorkerCase):
    """One composed worker, one interrupted launch, one restart."""

    def ticking(self, job, control, engine):
        return single_worker.operations_from(
            self.config, job, control, engine_run=engine,
            credential_provider=lambda *_: self.secret,
            clock=lambda: fixtures.NOW)

    def domain_of(self, control, attempt_id):
        row = manager_attempts._require_attempt(control, attempt_id)
        return tokens.domain_of(
            "workspace",
            tokens.workspace_governance(control=control).identity(row))

    def test_the_restarted_worker_reconciles_and_never_starts_a_second_container(self):
        engine = Dying()
        job, control = self.stores("interrupted-launch")
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        # THE FIRST PASS reaches the governed start and loses the engine inside it.
        for _ in range(6):
            try:
                reconcile(job, operations, now=fixtures.NOW)
            except OSError:
                break
        composed = len(engine.starts)
        self.assertEqual(composed, 1, "the first pass did not compose one container")
        self.assertEqual(engine.activations, [],
                         "the container was started despite the engine dying")
        attempt_id = self.only_attempt(control)
        domain = self.domain_of(control, attempt_id)
        held = tokens.unresolved(control, domain)
        self.assertEqual(len(held), 1, "the interrupted launch was not discoverable")
        # THE CUT THE REAL PATH LANDS ON, measured rather than guessed: the engine dies as
        # `create` answers, and the adapter binds the container the create RETURNED -- so
        # nothing was bound and the token's own record says `launched-unbound`. My first
        # assertion named the two later cuts and the measurement corrected it. This is
        # exactly the cut the reader was widened to select this claim.
        self.assertEqual(held[0]["cut"], "launched-unbound")
        self.assertIsNone(held[0]["container"])
        operations.close()
        job.close()
        control.close()

        # ---- THE RESTART: fresh stores, fresh worker, the same engine ----
        resumed_job, resumed_control = self.stores("interrupted-launch")
        resumed = self.ticking(resumed_job, resumed_control, engine.revive())
        self.addCleanup(resumed.close)
        for _ in range(6):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        # NO SECOND CONTAINER, which is the Recovery row's own words.
        self.assertEqual(len(engine.starts), composed,
                         "the restarted worker composed a second container")
        # AND THE RESOURCE IS STILL THIS GENERATION'S: nothing was returned or replaced
        # by the resume.
        self.assertEqual(len(tokens.outstanding(resumed_control, domain)), 1)
        state = tokens.token_of(resumed_control, domain, 1)
        self.assertFalse(state["returned"])
        self.assertFalse(state["revoked"])
        # AND WHATEVER THE RESUME CONCLUDED, it did so without a second container and
        # without releasing the resource -- which is what this case is for. The exact
        # resolution the worker reaches is asserted by the two cases below rather than
        # assumed here.

    def test_the_resume_reaches_an_ACTIONABLE_state_rather_than_spinning(self):
        """MEASURED, and this is the "actionable held result" half of R2.

        The resumed worker does not dispatch again and it does not loop forever asking: the
        stage reaches `exceptional`, which is a state an operator can act on, and repeated
        ticks compose nothing further. The resource stays held meanwhile -- an interrupted
        launch is not a licence to replace it.
        """
        from baton_v12.job_manager import status

        engine = Dying()
        job, control = self.stores("actionable")
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        for _ in range(6):
            try:
                reconcile(job, operations, now=fixtures.NOW)
            except OSError:
                break
        attempt_id = self.only_attempt(control)
        domain = self.domain_of(control, attempt_id)
        operations.close(); job.close(); control.close()

        resumed_job, resumed_control = self.stores("actionable")
        resumed = self.ticking(resumed_job, resumed_control, engine.revive())
        self.addCleanup(resumed.close)
        for _ in range(8):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        held = status(resumed_job, resumed,
                      observed_at=fixtures.NOW)["jobs"][0]["stages"][0]
        self.assertEqual(held["state"], "exceptional")
        self.assertEqual(len(engine.starts), 1)
        self.assertEqual(engine.activations, [])
        self.assertEqual(len(tokens.outstanding(resumed_control, domain)), 1)

    def test_the_production_pass_reports_that_hold_on_every_pass(self):
        """The hold is discoverable, not silent: the recovery pass names the exact
        unresolved execution, pass after pass.

        LABELLED ACCURATELY, per review 2026-09-27T12-00-40Z: this case does NOT reopen the
        stores, so it is not an independent restart cut -- it is repetition of the pass over
        the SAME handle. Fresh-store behaviour is proved by the two cases above and is not
        counted twice here.
        """
        from tools import job_manager

        engine = Dying()
        job, control = self.stores("reported")
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        for _ in range(6):
            try:
                reconcile(job, operations, now=fixtures.NOW)
            except OSError:
                break
        attempt_id = self.only_attempt(control)
        domain = self.domain_of(control, attempt_id)
        pass_over = job_manager._reclaiming(control, "docker", lambda *a, **k: {
            "status": 1, "stdout": "", "stderr": "no such object"})
        for _ in range(2):
            answer = pass_over(now=fixtures.NOW)
            self.assertEqual(len(answer["unresolved"]), 1)
            report = answer["unresolved"][0]
            self.assertEqual(report["execution"], attempt_id)
            self.assertEqual(report["cut"], "launched-unbound")
            self.assertEqual(report["observation"], "no-container-bound")
            self.assertTrue(report["held"])
        self.assertEqual(len(tokens.outstanding(control, domain)), 1)
        operations.close()

    def test_at_expiry_the_reclaim_REVOKES_and_the_unconfirmed_stop_stays_held(self):
        """RENAMED AND RE-ASSERTED to what it actually proves.

        Review 2026-09-27T12-00-40Z: the previous version was called "the hold is not
        permanent because expiry still reclaims it" and accepted ANY nonempty refused list,
        never asserting revocation, cessation, return or discharge -- and its engine answer
        named a made-up object rather than this runtime. That title was not proved.

        MEASURED, and this is the exact supported outcome for THIS cut. Past the deadline the
        accepted reclaim performs the first of its four acts -- the entitlement is REVOKED --
        and attempts the stop against the runtime the attempt row names. The stop cannot be
        confirmed here, so the outcome is `held` with state `uncertain` and the ending awaits
        a custody act this lean adapter does not perform. The resource is therefore STILL
        OUTSTANDING and NOT returned.

        THAT IS THE HONEST ANSWER RATHER THAN A DISAPPOINTING ONE: cessation cannot be
        established for a launch that bound no container, so an actionable unknown hold is the
        correct state, and nothing here forces a release to make a nicer claim. What a
        discharge would need -- positive cessation evidence naming the BOUND container, which
        this cut never produced -- is named in PROGRESS as owed rather than asserted here.
        """
        from tools import job_manager

        engine = Dying()
        job, control = self.stores("expiring")
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        for _ in range(6):
            try:
                reconcile(job, operations, now=fixtures.NOW)
            except OSError:
                break
        attempt_id = self.only_attempt(control)
        domain = self.domain_of(control, attempt_id)
        attached = manager_attempts._require_attempt(control, attempt_id)["runtime_id"]
        beyond = "2026-09-27T23:59:00.000Z"
        control._clock = lambda: beyond
        self.assertTrue(tokens.token_of(control, domain, 1)["expired"])
        vectors = []

        def engine_run(argv, *, seconds=None):
            del seconds
            vectors.append(list(argv))
            return {"status": 1, "stdout": "",
                    "stderr": "Error: No such object: " + argv[-1]}

        answer = job_manager._reclaiming(control, "docker", engine_run)(now=beyond)
        # THE STOP WAS ATTEMPTED AGAINST THIS EXACT RUNTIME, not an invented name.
        self.assertEqual([one[1] for one in vectors], ["stop"])
        self.assertEqual(vectors[0][-1], attached)
        # THE EXACT OUTCOME: revoked, held, uncertain, awaiting a custody act.
        self.assertEqual(len(answer["reclaimed"]), 1)
        outcome = answer["reclaimed"][0]
        self.assertEqual(outcome["reclaimed"], "held")
        self.assertEqual(outcome["state"], "uncertain")
        self.assertEqual(outcome["ending"], "awaits-normalizing-ending")
        self.assertEqual(answer["refused"], [])
        state = tokens.token_of(control, domain, 1)
        self.assertTrue(state["revoked"], "the entitlement was not withdrawn")
        self.assertFalse(state["returned"], "an unconfirmed stop returned the resource")
        self.assertEqual(len(tokens.outstanding(control, domain)), 1)
        # AND THE RECOVERY REPORT STILL NAMES IT, now as expired.
        self.assertEqual(len(answer["unresolved"]), 1)
        self.assertTrue(answer["unresolved"][0]["expired"])
        operations.close()

    def interrupted(self, label, engine, *, admitting=True):
        """One composed worker driven until its launch is interrupted, then handed back.

        `admitting=False` makes `tokens.admit_activation` fault the first time it is asked,
        which is the ONE cut no engine vector can produce: `Reservation.bind` journals the
        launch and binds the container and only then asks the admission, so the state between
        those two acts is reachable exactly by failing the admission. A fault injected at that
        real seam is what a manager dying there leaves.
        """
        job, control = self.stores(label)
        submit(job, self.submission)
        operations = self.ticking(job, control, engine)
        asked = []
        honest = tokens.admit_activation

        def once(*args, **named):
            if not admitting and not asked:
                asked.append(True)
                raise OSError("the manager stopped before the admission committed")
            return honest(*args, **named)

        tokens.admit_activation = once
        try:
            for _ in range(6):
                try:
                    reconcile(job, operations, now=fixtures.NOW)
                except OSError:
                    break
        finally:
            tokens.admit_activation = honest
        attempt_id = self.only_attempt(control)
        return {"job": job, "control": control, "operations": operations,
                "attempt_id": attempt_id,
                "domain": self.domain_of(control, attempt_id),
                "admission_asked": bool(asked)}

    def test_the_ADMITTED_UNSETTLED_cut_resumes_without_a_second_container(self):
        """The cut where the activation was admitted and its outcome never learned: the
        engine died on the activation vector itself."""
        engine = DyingAtActivation()
        held = self.interrupted("admitted-cut", engine)
        control, domain = held["control"], held["domain"]
        composed = len(engine.starts)
        self.assertEqual(composed, 1)
        unresolved = tokens.unresolved(control, domain)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]["cut"], "admitted-unsettled")
        self.assertEqual(unresolved[0]["container"], engine.runtime_id)
        held["operations"].close(); held["job"].close(); control.close()

        resumed_job, resumed_control = self.stores("admitted-cut")
        resumed = self.ticking(resumed_job, resumed_control, engine.revive())
        self.addCleanup(resumed.close)
        for _ in range(8):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        # NO SECOND CONTAINER, and the resource is still this generation's.
        self.assertEqual(len(engine.starts), composed)
        self.assertEqual(len(tokens.outstanding(resumed_control, domain)), 1)
        state = tokens.token_of(resumed_control, domain, 1)
        self.assertFalse(state["returned"])
        self.assertFalse(state["revoked"])

    def test_the_BOUND_NOT_ADMITTED_cut_resumes_without_a_second_container(self):
        """The cut between binding and admission, reachable only by failing the admission
        itself -- see `interrupted`. The container is bound; nothing ever admitted it."""
        engine = Engine()
        held = self.interrupted("bound-cut", engine, admitting=False)
        control, domain = held["control"], held["domain"]
        self.assertTrue(held["admission_asked"], "the admission seam was never reached")
        composed = len(engine.starts)
        self.assertEqual(composed, 1)
        unresolved = tokens.unresolved(control, domain)
        self.assertEqual(len(unresolved), 1)
        self.assertEqual(unresolved[0]["cut"], "bound-not-admitted")
        self.assertEqual(unresolved[0]["container"], engine.runtime_id)
        held["operations"].close(); held["job"].close(); control.close()

        resumed_job, resumed_control = self.stores("bound-cut")
        resumed = self.ticking(resumed_job, resumed_control, engine)
        self.addCleanup(resumed.close)
        for _ in range(8):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        self.assertEqual(len(engine.starts), composed,
                         "the restarted worker composed a second container")
        self.assertEqual(len(tokens.outstanding(resumed_control, domain)), 1)
        self.assertFalse(tokens.token_of(resumed_control, domain, 1)["returned"])

    def test_conflicting_engine_EVIDENCE_is_refused_before_use_not_substituted(self):
        """REPAIRED after W275776 review 2026-09-27T12-07-41Z, which was right twice.

        My previous version switched the engine double's `runtime_id` and then asserted only
        one create, an unchanged binding and `held=True` -- it never established that the
        resumed worker REACHED the conflicting evidence, and the reviewer's wrapper showed the
        recovery report naming the BOUND runtime as absent with no contradiction at all. The
        scenario proved nothing about mismatch handling and MATRIX row 9's claim about it was
        false.

        MEASURED, and the real behaviour is better than my framing suggested. The resumed
        worker DOES ask the engine -- the `ps`/`inspect` vectors below are the premise, asserted
        rather than assumed -- and when the listing carries a runtime that is NOT the one this
        attempt recorded, the production identification CANCELS rather than adopting it: the
        axis becomes `cancel-requested`, the recorded runtime is unchanged, the stage is
        `exceptional`, and no container is composed or activated. That is the exact actionable
        pre-use refusal the review asked to see, and nothing here forces an attachment.

        AND IT NARROWS MY EARLIER OBSERVATION rather than contradicting it. The helper-level
        case in `test_restart_recovery.py` saw a labelled container ADOPTED -- but there the
        attempt had no recorded runtime at all, so there was nothing for the engine's answer to
        contradict. With a recorded runtime, a different identity is refused. The token's
        binding is untouched in both.
        """
        engine = DyingAtActivation()
        held = self.interrupted("mismatch-cut", engine)
        control, domain = held["control"], held["domain"]
        attempt_id = held["attempt_id"]
        bound = tokens.token_of(control, domain, 1)["container"]
        recorded = manager_attempts._require_attempt(control, attempt_id)["runtime_id"]
        self.assertEqual(recorded, bound, "the cut did not record the bound runtime")
        composed = len(engine.starts)
        held["operations"].close(); held["job"].close(); control.close()

        resumed_job, resumed_control = self.stores("mismatch-cut")
        # THE ENGINE NOW NAMES ANOTHER CONTAINER for the same labels.
        engine.revive()
        engine.runtime_id = "another-runtime"
        before = len(engine.vectors)
        resumed = self.ticking(resumed_job, resumed_control, engine)
        self.addCleanup(resumed.close)
        for _ in range(8):
            reconcile(resumed_job, resumed, now=fixtures.NOW)
        asked = [one[1] for one in engine.vectors[before:]]
        # THE PREMISE: the conflicting evidence was actually reached.
        self.assertIn("ps", asked, f"the resume never asked the engine: {asked}")
        # THE OUTCOME: refused before use, not substituted.
        self.assertEqual(
            manager_attempts.attempt_runtime_of(
                resumed_control, attempt_id)["execution_runtime"],
            "cancel-requested")
        self.assertEqual(
            manager_attempts._require_attempt(
                resumed_control, attempt_id)["runtime_id"], recorded,
            "the conflicting identity was substituted into the attempt")
        self.assertEqual(
            status(resumed_job, resumed,
                   observed_at=fixtures.NOW)["jobs"][0]["stages"][0]["state"],
            "exceptional")
        # NO FURTHER EFFECT OF ANY KIND.
        self.assertEqual(len(engine.starts), composed)
        self.assertEqual(engine.activations, [])
        # AND THE RESOURCE IS STILL THIS GENERATION'S, with its binding intact.
        self.assertEqual(tokens.token_of(resumed_control, domain, 1)["container"], bound)
        self.assertEqual(len(tokens.outstanding(resumed_control, domain)), 1)
        # AND WHAT THE RECOVERY PASS REPORTS FOR THIS SCENARIO, which is the distinction the
        # review asks to be drawn: there is deliberately NO contradiction here, because the
        # worker REFUSED the conflicting identity rather than adopting it, so the attempt and
        # the token still name the same container. The contradiction report is a DIFFERENT
        # scenario -- an attempt row that really does name another runtime -- and it is proved
        # by `tests/job_manager/test_tool.py::TheRecoveryPassVisitsTheUNCERTAINTokensToo::
        # test_a_contradiction_between_the_attachment_and_the_binding_is_reported`.
        from tools import job_manager

        answer = job_manager._reclaiming(resumed_control, "docker", lambda *a, **k: {
            "status": 1, "stdout": "", "stderr": "Error: No such object: " + bound})(
                now=fixtures.NOW)
        self.assertEqual(len(answer["unresolved"]), 1)
        report = answer["unresolved"][0]
        self.assertEqual(report["container"], bound)
        self.assertNotIn("contradicts_binding", report)
        self.assertTrue(report["held"])

    # THE OLD NAME, KEPT AS AN ALIAS so an immutable artifact that wraps this scenario by
    # name still EXECUTES it rather than erroring on a missing attribute.
    # `review_mismatch_premise_20260927.py` calls
    # `test_an_ATTACHED_BOUND_MISMATCH_is_reported_and_never_dispatched_around`, and the
    # repair above renamed it, because "is reported" is not what the connected path does:
    # the worker REFUSES the conflicting identity before using it. The alias runs the
    # repaired case; that probe's own assertion -- that the scenario reports
    # `contradicts_binding == another-runtime` -- is the premise this repair disproves, so it
    # fails on that line rather than on an import error, which is the informative outcome.
    test_an_ATTACHED_BOUND_MISMATCH_is_reported_and_never_dispatched_around = \
        test_conflicting_engine_EVIDENCE_is_refused_before_use_not_substituted

    def only_attempt(self, control):
        rows = manager_attempts._attempts(control, "ORDER BY runtime_attempt_id")
        identities = [row["runtime_attempt_id"] for row in rows]
        self.assertEqual(len(identities), 1, identities)
        return identities[0]


if __name__ == "__main__":
    loader = unittest.TestLoader()
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(
        loader.loadTestsFromTestCase(
            TheWorkerResumesItsOwnLaunchWithoutDispatchingAgain)).wasSuccessful())
