"""W275775 — renewal and expiry arbitration, at the accepted token owner's own seam.

Every case here drives `tokens` public acts against a disposable control store. The
section 17 renewal row is the checklist, clause by clause:

    "Valid same-execution renewal is recorded once; competing expiry/renewal serialize;
     stale expiry cannot defeat a committed renewal; expired/revoked/stale/cross-execution
     renewal refuses; lost reply/replay does not extend twice"

No engine, no provider, no container: a token is a journal decision and this proves it as
one. Run standalone -- `python3 test_renewal_arbitration.py` -- so the fixture below is not
re-run by whole-module discovery of the suites it borrows nothing from.
"""
import os
import tempfile
import unittest

from baton_v12.contracts import ContractRefusal
from baton_v12.worker_manager import ControlStore, tokens


NOW = "2026-09-27T03:00:00.000Z"
# The Job ceilings this Work's non-reset proof populates, in the OWNER's own setting
# names (`execution_limits.LIMIT_MEMBERS`) and deliberately not the runner defaults.
REQUESTED = {"provider_turn_seconds": 60, "verification_command_seconds": 45}


class RenewalCase(unittest.TestCase):
    """One store, one governed domain, one acquired generation."""

    instant = NOW

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-token-b-")
        self.addCleanup(root.cleanup)
        self._path = os.path.join(root.name, "control.sqlite3")
        self.store = ControlStore.open(
            self._path,
            incarnation="token-b", clock=lambda: self.instant)
        self.addCleanup(self.store.close)
        self.domain = tokens.domain_of("workspace", "line-9/workspace")

    def held(self, *, seconds=900, operation="runtime.start:b",
             execution="attempt-b"):
        return tokens.acquire(self.store, self.domain, operation=operation,
                              execution=execution, attempt=execution,
                              seconds=seconds)

    def renewing(self, token, **changed):
        operands = {"execution": token["execution"],
                    "operation": token["operation"],
                    # W275775 [C3]: the OBSERVED revision, which is what `token_of`
                    # answers -- 0 for a generation nobody has renewed.
                    "expected_revision": self.current()["revision"]}
        operands.update(changed)
        return tokens.renew(self.store, token, **operands)

    def current(self, generation=1):
        return tokens.token_of(self.store, self.domain, generation)

    def refusal(self, call):
        with self.assertRaises(ContractRefusal) as caught:
            call()
        return caught.exception

    def fresh(self):
        """A new store AND this fixture's own clock again.

        `instant` is a CLASS attribute and `setUp` does not reset the instance one, so a case
        that drives several independent generations has to drop it -- the same correction the
        reclaim selector records, kept here rather than imported.
        """
        self.__dict__.pop("instant", None)
        self.setUp()

    def launched(self, token, container="container-b", launch="launch:b"):
        tokens.journal_launch(self.store, token, launch)
        tokens.bind_container(self.store, token, container, launch=launch)
        return {"domain": token["domain"], "generation": token["generation"],
                "launch": launch, "container": container,
                "stopped": True, "helpers": []}


class AValidRenewalIsRecordedOnce(RenewalCase):

    def test_the_deadline_moves_and_the_record_says_what_moved_it(self):
        token = self.held(seconds=900)
        before = self.current()
        # PARTWAY THROUGH THE LIFETIME, which is when a holder actually renews. The
        # deadline is `now + seconds` read from the STORE's clock, so the gain is the
        # time that has passed since the grant -- see the same-instant case below.
        self.instant = "2026-09-27T03:10:00.000Z"
        answered = self.renewing(token)
        after = self.current()
        self.assertEqual(answered["revision"], 1)
        self.assertEqual(answered["execution"], token["execution"])
        self.assertEqual(answered["operation"], token["operation"])
        self.assertGreater(after["expires_at"], before["expires_at"])
        self.assertEqual(after["expires_at"], answered["expires_at"])
        # THE ORIGINAL GRANT IS STILL READABLE, which a restart reconciling this
        # generation needs: what it was given, beside what it is owed now.
        self.assertEqual(after["acquired_expires_at"], before["expires_at"])
        self.assertEqual((after["revision"], after["renewals"]), (1, 1))

    def test_renewing_at_the_same_instant_records_a_revision_and_gains_nothing(self):
        """A property worth stating rather than discovering.

        The deadline is the HOST's: `now + seconds` at the moment of renewal, which is
        TOK-9's "trusted host's clock/deadline owner decides expiry". So a caller that
        renews the instant after acquiring, with the same lifetime, gets the same
        deadline it already had -- and still spends one of the bounded renewals. That is
        honest rather than wasteful-by-accident: nothing about asking again buys time
        that has not passed, and the bound counts requests rather than seconds.
        """
        token = self.held(seconds=900)
        before = self.current()["expires_at"]
        answered = self.renewing(token)
        self.assertEqual(answered["expires_at"], before)
        self.assertEqual(self.current()["revision"], 1)
        self.assertEqual(self.current()["renewals_remaining"],
                         tokens.RENEWAL_LIMIT - 1)

    def test_a_longer_lifetime_is_the_operand_that_buys_time(self):
        """The same instant, a longer requested lifetime, and the deadline does move --
        so the previous case is about the clock rather than a renewal that cannot
        extend."""
        token = self.held(seconds=900)
        before = self.current()["expires_at"]
        answered = self.renewing(token, seconds=1800)
        self.assertGreater(answered["expires_at"], before)
        self.assertEqual(answered["seconds"], 1800)

    def test_it_creates_no_writer_and_moves_no_other_row(self):
        """TOK-9: renewal does not create a writer or reset Job limits. Asserted as
        the database fact rather than by reading the function: exactly one operation
        row appears, and nothing else in the store changes."""
        token = self.held()
        rows = lambda: self.store._connection.execute(
            "SELECT COUNT(*) FROM operations").fetchone()[0]
        before, changes = rows(), self.store._connection.total_changes
        self.renewing(token)
        self.assertEqual(rows(), before + 1)
        self.assertGreater(self.store._connection.total_changes, changes)
        self.assertEqual(
            self.store._connection.execute(
                "SELECT COUNT(*) FROM attempts").fetchone()[0], 0)

    def test_each_revision_is_its_own_record_up_to_the_bound(self):
        token = self.held()
        seen = []
        for observed in range(tokens.RENEWAL_LIMIT):
            answered = self.renewing(token, expected_revision=observed)
            seen.append(answered["revision"])
            self.assertEqual(self.current()["revision"], observed + 1)
        self.assertEqual(seen, list(range(1, tokens.RENEWAL_LIMIT + 1)))
        self.assertEqual(self.current()["renewals_remaining"], 0)


class AReplayDoesNotExtendTwice(RenewalCase):

    def test_the_same_request_answers_the_same_record(self):
        """The lost-reply case. The caller never learned its renewal committed, so it
        asks again with the same expected revision -- and is given the extension that
        already happened rather than a second one."""
        token = self.held()
        # THE OBSERVED REVISION IS CAPTURED BEFORE THE FIRST CALL, because that is what a
        # lost reply IS: the caller still believes the state it read, and asks again with
        # it. Reading it fresh on the second call would be a NEW request for the next
        # revision, which is a different case (and the one below).
        observed = self.current()["revision"]
        first = self.renewing(token, expected_revision=observed)
        deadline = self.current()["expires_at"]
        self.instant = "2026-09-27T03:05:00.000Z"
        again = self.renewing(token, expected_revision=observed)
        self.assertEqual(again, first)
        self.assertEqual(self.current()["expires_at"], deadline,
                         "a replay extended the deadline a second time")
        self.assertEqual(self.current()["renewals"], 1)

    def test_a_changed_operand_at_a_committed_revision_collides(self):
        """A replay is an exact repetition. The same revision asked for with different
        terms is a different act wearing a committed identity, and the journal refuses
        it rather than answering the first one."""
        token = self.held()
        observed = self.current()["revision"]
        self.renewing(token, expected_revision=observed)
        refusal = self.refusal(
            lambda: self.renewing(token, expected_revision=observed, seconds=1800))
        self.assertEqual(refusal.category, "refused")
        self.assertEqual(self.current()["renewals"], 1)

    def test_a_revision_further_ahead_than_the_next_one_refuses(self):
        token = self.held()
        refusal = self.refusal(lambda: self.renewing(token, expected_revision=2))
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("cannot skip the state", refusal.message)
        self.assertEqual(self.current()["renewals"], 0)


class ExpiryAndRenewalCompeteAgainstTheSameState(RenewalCase):

    def test_an_expired_generation_is_not_revived(self):
        """TOK-9: once expiry has won, no late request revives the token."""
        token = self.held(seconds=1)
        self.instant = "2026-09-27T04:00:00.000Z"
        self.assertTrue(self.current()["expired"])
        refusal = self.refusal(lambda: self.renewing(token))
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("expired at", refusal.message)
        self.assertEqual(self.current()["renewals"], 0)
        self.assertTrue(self.current()["expired"],
                        "a refused renewal must leave expiry exactly where it was")

    def test_a_renewed_deadline_defeats_a_STALE_expiry_observation(self):
        """The clause that needs the arbitration and not just the act.

        A sweep reads the token, sees a deadline about to pass, and is slow. The holder
        renews. The sweep then tries to revoke on what it observed -- and is refused,
        because revocation arbitrates against the CURRENT deadline rather than the one
        the observation carried.
        """
        token = self.held(seconds=60)
        stale = self.current()
        self.instant = "2026-09-27T03:00:30.000Z"
        self.renewing(token)
        self.instant = "2026-09-27T03:01:30.000Z"     # past the STALE deadline only
        self.assertGreaterEqual(self.instant, stale["expires_at"])
        self.assertFalse(self.current()["expired"])
        refusal = self.refusal(
            lambda: tokens.revoke(self.store, "line-9/workspace", "workspace",
                                  execution=token["execution"],
                                  operation=token["operation"]))
        self.assertEqual(refusal.category, "refused")
        self.assertIn("is not overdue", refusal.message)
        self.assertFalse(self.current()["revoked"])

    def test_expiry_wins_at_the_renewed_deadline_and_not_before(self):
        """The other half of the same fact: the renewal moved the deadline, it did not
        remove it. Past the RENEWED deadline the ordinary revocation proceeds."""
        token = self.held(seconds=60)
        self.renewing(token, seconds=60)
        self.instant = "2026-09-27T03:30:00.000Z"
        self.assertTrue(self.current()["expired"])
        answered = tokens.revoke(self.store, "line-9/workspace", "workspace",
                                 execution=token["execution"],
                                 operation=token["operation"])
        self.assertEqual(answered["generation"], 1)
        self.assertTrue(self.current()["revoked"])

    def test_a_revoked_generation_cannot_be_renewed(self):
        token = self.held(seconds=1)
        self.instant = "2026-09-27T04:00:00.000Z"
        tokens.revoke(self.store, "line-9/workspace", "workspace",
                      execution=token["execution"], operation=token["operation"])
        refusal = self.refusal(lambda: self.renewing(token))
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "already-terminal"))
        self.assertIn("REVOKED", refusal.message)

    def test_a_returned_generation_cannot_be_renewed(self):
        token = self.held()
        evidence = self.launched(token)
        tokens.admit_activation(self.store, token, container="container-b")
        tokens.settle_activation(self.store, token, container="container-b",
                                 started=True)
        tokens.returned(self.store, token, cessation=evidence)
        refusal = self.refusal(lambda: self.renewing(token))
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("has been returned", refusal.message)


class TheBoundNeverHIDESACommittedRenewal(RenewalCase):
    """W275775 review 02-43-54Z [P2]: the lost reply AT the limit must still replay.

    The defect the reviewer reproduced: with the allowance spent, the exhaustion refusal ran
    BEFORE the journal could answer a request whose record already existed -- so the one
    lost reply that could not be recovered was the last one, and TOK-9's "a lost renewal
    reply grants nothing beyond the committed authority state" was inverted into granting
    LESS than the committed state by hiding it.
    """

    def exhausted(self):
        """One generation with its whole allowance spent, and every answer kept."""
        token = self.held()
        answers = []
        for observed in range(tokens.RENEWAL_LIMIT):
            answers.append(self.renewing(token, expected_revision=observed))
        self.assertEqual(self.current()["renewals"], tokens.RENEWAL_LIMIT)
        self.assertEqual(self.current()["renewals_remaining"], 0)
        return token, answers

    def test_the_final_allowed_renewals_lost_reply_replays(self):
        token, answers = self.exhausted()
        deadline = self.current()["expires_at"]
        # WHILE THE TOKEN IS STILL UNEXPIRED, which is the reviewer's own scope and the
        # only state in which any late act is answered at all -- see the case below for
        # what happens after expiry, which is a deliberate choice rather than an accident.
        self.instant = "2026-09-27T03:10:00.000Z"
        self.assertFalse(self.current()["expired"])
        replay = self.renewing(token,
                               expected_revision=tokens.RENEWAL_LIMIT - 1)
        self.assertEqual(replay, answers[-1])
        self.assertEqual(self.current()["renewals"], tokens.RENEWAL_LIMIT)
        self.assertEqual(self.current()["expires_at"], deadline,
                         "a replay at the bound extended the deadline")

    def test_an_earlier_revisions_replay_also_answers_at_exhaustion(self):
        """Not only the last one: any committed revision is answerable, because the
        record exists and answering it spends nothing."""
        token, answers = self.exhausted()
        for observed, answered in enumerate(answers):
            with self.subTest(observed=observed):
                self.assertEqual(self.renewing(token, expected_revision=observed),
                                 answered)
        self.assertEqual(self.current()["renewals"], tokens.RENEWAL_LIMIT)

    def test_a_changed_operand_at_exhaustion_collides_rather_than_denying(self):
        """The distinction the review asks for: a replay and a NEW admission are told
        apart by the record, so a changed operand at a committed revision is a
        collision -- not a policy refusal that would hide which rule stopped it."""
        token, _answers = self.exhausted()
        refusal = self.refusal(
            lambda: self.renewing(token, expected_revision=0, seconds=1800))
        self.assertEqual(refusal.category, "refused")
        self.assertNotEqual(refusal.code, "denied")
        self.assertEqual(self.current()["renewals"], tokens.RENEWAL_LIMIT)

    def test_a_replay_arriving_AFTER_expiry_is_refused_as_expired_not_answered(self):
        """The choice this makes, stated rather than left to be discovered.

        A lost reply that arrives after the deadline has passed could be answered -- reading
        back a committed record grants nothing new. It is REFUSED instead, for the same
        reason `_owning` refuses every other late act on an expired generation: the uniform
        gate is what makes "an expired generation authorizes nothing further" true without
        exceptions, and the caller learns the fact that now matters (this token is expired)
        rather than a deadline it can no longer rely on. Nothing is revived either way.
        """
        token, _answers = self.exhausted()
        self.instant = "2026-09-27T03:20:00.000Z"
        refusal = self.refusal(
            lambda: self.renewing(token,
                                  expected_revision=tokens.RENEWAL_LIMIT - 1))
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("expired at", refusal.message)
        self.assertEqual(self.current()["renewals"], tokens.RENEWAL_LIMIT)

    def test_an_actual_fifth_extension_is_denied_and_the_resource_stays_held(self):
        token, _answers = self.exhausted()
        refusal = self.refusal(
            lambda: self.renewing(token, expected_revision=tokens.RENEWAL_LIMIT))
        self.assertEqual((refusal.category, refusal.code), ("policy", "denied"))
        self.assertIn("does not free the resource", refusal.message)
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)
        self.assertFalse(self.current()["returned"])


class AJudgedExPIRYCannotBeArguedWithByTheClock(RenewalCase):
    """W275775 review 02-43-54Z [P1]: expiry, once judged, is a record and not arithmetic."""

    def test_a_clock_moved_backwards_does_not_revive_a_refused_token(self):
        """The reviewer's own sequence: observe expired, be refused, roll the clock back,
        ask again. TOK-9 -- "no heartbeat, late renewal request or clock adjustment revives
        the token" -- and the ambiguous-timing hold."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.assertTrue(self.current()["expired"])
        first = self.refusal(lambda: self.renewing(token))
        self.assertIn("expired at", first.message)
        self.instant = "2026-09-27T03:00:30.000Z"          # backwards, inside the deadline
        again = self.refusal(lambda: self.renewing(token))
        self.assertEqual((again.category, again.code), ("refused", "precondition"))
        self.assertIn("judged expired at", again.message)
        self.assertEqual(self.current()["renewals"], 0)
        # AND THE READER DOES NOT CONTRADICT THE DECISION EITHER.
        self.assertTrue(self.current()["expired"])
        self.assertEqual(self.current()["expiry_judged_at"],
                         "2026-09-27T03:02:00.000Z")

    def test_the_judgement_is_recorded_once_at_the_instant_expiry_won(self):
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.refusal(lambda: self.renewing(token))
        self.instant = "2026-09-27T04:00:00.000Z"
        self.refusal(lambda: self.renewing(token))
        self.assertEqual(self.current()["expiry_judged_at"],
                         "2026-09-27T03:02:00.000Z",
                         "a later notice overwrote the moment expiry actually won")

    def test_a_FRESH_HANDLE_sees_the_same_hold(self):
        """The record is durable, so a second manager on the same store -- the shape a
        restart takes without importing Child C's restart scope -- reads the same
        judgement rather than recomputing one from its own clock."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.refusal(lambda: self.renewing(token))
        self.instant = "2026-09-27T03:00:30.000Z"
        fresh = ControlStore.open(self._path, incarnation="manager-fresh",
                                  clock=lambda: self.instant)
        self.addCleanup(fresh.close)
        state = tokens.token_of(fresh, self.domain, 1)
        self.assertTrue(state["expired"])
        self.assertEqual(state["expiry_judged_at"], "2026-09-27T03:02:00.000Z")
        with self.assertRaises(ContractRefusal):
            tokens.renew(fresh, token, execution=token["execution"],
                         operation=token["operation"], expected_revision=0)
        self.assertEqual(state["renewals"], 0)

    def test_the_hold_does_not_become_a_release(self):
        """TOK-5: a judged expiry frees nothing. The resource is still outstanding, still
        excludes a competitor, and its revocation path is still open -- which is the only
        way a held resource is ever reclaimed."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.refusal(lambda: self.renewing(token))
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)
        competing = self.refusal(
            lambda: tokens.acquire(self.store, self.domain,
                                   operation="runtime.start:other",
                                   execution="attempt-other"))
        self.assertIn("outstanding baton", competing.message)
        answered = tokens.revoke(self.store, "line-9/workspace", "workspace",
                                 execution=token["execution"],
                                 operation=token["operation"])
        self.assertEqual(answered["generation"], 1)

    def test_a_renewed_token_is_judged_against_its_renewed_deadline(self):
        """The judgement follows the arbitration rather than the original grant: a
        generation renewed past an instant is not judged expired at it."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:00:30.000Z"
        self.renewing(token, seconds=600)
        self.instant = "2026-09-27T03:05:00.000Z"          # past the ORIGINAL deadline
        self.assertFalse(self.current()["expired"])
        self.renewing(token, expected_revision=1, seconds=600)
        self.assertIsNone(self.current()["expiry_judged_at"])
        self.assertEqual(self.current()["renewals"], 2)


class AStaleObservationCannotJudgeACommittedRenewalExpired(RenewalCase):
    """W275775 review 2026-09-27T03-02-01Z [P1]: the judgement is a decision, not a note.

    My first cut took the deadline and the instant as OPERANDS and wrote the expiry record
    unconditionally, so a caller holding an OLD deadline could permanently invalidate a
    renewal that had committed while it was paused -- with no clock rollback anywhere. The
    reviewer's schedule is reproduced here as a case of this Work's own, and the condition
    now lives inside the write.
    """

    def test_the_exact_stale_deadline_schedule_judges_nothing(self):
        """A reads the old deadline and pauses; B renews; A resumes past its OWN deadline
        and refuses itself -- and the renewed generation is untouched."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:00:30.000Z"
        peer = ControlStore.open(self._path, incarnation="renewing-peer",
                                 clock=lambda: self.instant)
        self.addCleanup(peer.close)
        honest, intercepted = tokens._deadline_of, []

        def paused(control, domain, generation, acquired=None):
            deadline = honest(control, domain, generation, acquired)
            if control is self.store and not intercepted:
                intercepted.append(True)
                # B COMMITS A RENEWAL WHILE A IS MID-DECISION.
                tokens.renew(peer, token, execution=token["execution"],
                             operation=token["operation"], expected_revision=0,
                             seconds=900)
                self.instant = "2026-09-27T03:02:00.000Z"   # past A's OLD deadline only
            return deadline

        tokens._deadline_of = paused
        self.addCleanup(setattr, tokens, "_deadline_of", honest)
        try:
            self.renewing(token, expected_revision=0)
        except ContractRefusal:
            pass            # A's own request may refuse; that is A's business
        tokens._deadline_of = honest

        state = self.current()
        self.assertEqual(state["revision"], 1)
        self.assertLess(self.instant, state["expires_at"])
        self.assertFalse(state["expired"],
                         "a stale observation judged a renewed generation expired")
        self.assertIsNone(state["expiry_judged_at"])

    def test_expiry_DISCOVERED_INSIDE_the_transaction_is_still_judged(self):
        """The equivalence the review asked for.

        The preflight passes -- the token is live when the request starts -- and the deadline
        passes while the renewal is inside its own write. The in-transaction re-proof refuses,
        that transaction rolls back, and the judgement is STILL recorded, because it is
        attempted around the whole attempt in its own short write rather than nested inside
        the one that failed.
        """
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:00:30.000Z"
        honest, moved = tokens._renewals_of, []

        def advancing(control, domain, generation):
            answer = honest(control, domain, generation)
            if control._connection.in_transaction and not moved:
                moved.append(True)
                self.instant = "2026-09-27T03:05:00.000Z"    # past the real deadline
            return answer

        tokens._renewals_of = advancing
        self.addCleanup(setattr, tokens, "_renewals_of", honest)
        refusal = self.refusal(lambda: self.renewing(token, expected_revision=0))
        tokens._renewals_of = honest

        self.assertTrue(moved, "the clock never moved inside the transaction")
        self.assertIn("expired", refusal.message)
        self.assertEqual(self.current()["renewals"], 0,
                         "the rolled-back renewal left a record behind")
        # THE DURABLE JUDGEMENT SURVIVED THE ROLLBACK, which is the point.
        self.assertTrue(self.current()["expired"])
        self.assertEqual(self.current()["expiry_judged_at"],
                         "2026-09-27T03:05:00.000Z")

    def test_a_judgement_records_which_state_expiry_won_against(self):
        """The record names the deadline and the revision it judged, so a reader can see
        WHICH state lost rather than only that one did."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:00:30.000Z"
        self.renewing(token, expected_revision=0, seconds=60)
        self.instant = "2026-09-27T03:05:00.000Z"
        self.refusal(lambda: self.renewing(token, expected_revision=1))
        judged = tokens._judged_expired(self.store, self.domain, 1)
        self.assertEqual(judged["revision"], 1)
        self.assertEqual(judged["expires_at"], "2026-09-27T03:01:30.000Z")
        self.assertEqual(judged["observed_at"], "2026-09-27T03:05:00.000Z")


class TimeMovingBackwardsIsHeldRatherThanGuessedAt(RenewalCase):
    """W275775 review 2026-09-27T03-12-19Z [C1]: the third answer, and TOK-9 names it.

    "Ambiguous timing means hold/reconcile." The window the reviewer found was between
    OBSERVING expiry and RECORDING it: the clock moved backwards in between, the conditional
    write declined, the caller stayed refused -- and the next attempt renewed. Neither
    "expired" nor "live" is true in that window, so neither is recorded: the ambiguity is.
    """

    def rolling_back(self, to="2026-09-27T03:00:30.000Z"):
        """Move the clock backwards between the observation and the judgement."""
        honest = tokens._judge_expired

        def rollback(control, domain, generation, observed):
            self.instant = to
            return honest(control, domain, generation, observed)

        tokens._judge_expired = rollback
        self.addCleanup(setattr, tokens, "_judge_expired", honest)

    def test_the_exact_window_holds_and_a_retry_cannot_renew(self):
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.rolling_back()
        first = self.refusal(lambda: self.renewing(token))
        self.assertIn("expired", first.message)
        # THE RETRY, on the rolled-back clock, against a deadline that has not passed.
        again = self.refusal(lambda: self.renewing(token))
        self.assertEqual((again.category, again.code), ("refused", "precondition"))
        self.assertIn("AMBIGUOUS", again.message)
        self.assertEqual(self.current()["renewals"], 0)

    def test_the_hold_is_recorded_with_both_readings(self):
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.rolling_back()
        self.refusal(lambda: self.renewing(token))
        state = self.current()
        self.assertTrue(state["timing_ambiguous"])
        self.assertEqual(state["timing_observed_at"], "2026-09-27T03:02:00.000Z")
        self.assertEqual(state["timing_decided_at"], "2026-09-27T03:00:30.000Z")
        # AND NO EXPIRY WAS CLAIMED, because that is not what was established.
        self.assertIsNone(state["expiry_judged_at"])

    def test_the_hold_is_not_a_release_and_the_resource_is_still_reclaimable(self):
        """TOK-5 again: a hold frees nothing. The resource stays outstanding and a
        competitor is still excluded; and once the deadline genuinely passes, the ordinary
        revocation path still reclaims it -- so the hold is not a way to lose a resource."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.rolling_back()
        self.refusal(lambda: self.renewing(token))
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)
        competing = self.refusal(
            lambda: tokens.acquire(self.store, self.domain,
                                   operation="runtime.start:other",
                                   execution="attempt-other"))
        self.assertIn("outstanding baton", competing.message)
        self.instant = "2026-09-27T04:00:00.000Z"
        answered = tokens.revoke(self.store, "line-9/workspace", "workspace",
                                 execution=token["execution"],
                                 operation=token["operation"])
        self.assertEqual(answered["generation"], 1)

    def test_a_FRESH_HANDLE_reads_the_same_hold(self):
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.rolling_back()
        self.refusal(lambda: self.renewing(token))
        fresh = ControlStore.open(self._path, incarnation="manager-fresh",
                                  clock=lambda: self.instant)
        self.addCleanup(fresh.close)
        self.assertTrue(tokens.token_of(fresh, self.domain, 1)["timing_ambiguous"])
        with self.assertRaises(ContractRefusal) as caught:
            tokens.renew(fresh, token, execution=token["execution"],
                         operation=token["operation"], expected_revision=0)
        self.assertIn("AMBIGUOUS", caught.exception.message)

    def test_an_OVERTAKEN_observation_is_not_an_ambiguity(self):
        """The distinction the correction rests on. A renewal committing in between means
        the observation was simply OLD -- nothing is recorded, and the renewed generation
        keeps its deadline. This is the previous claim's race, re-asserted here against the
        new three-outcome decision so the two cannot be confused."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:00:30.000Z"
        peer = ControlStore.open(self._path, incarnation="renewing-peer",
                                 clock=lambda: self.instant)
        self.addCleanup(peer.close)
        honest, seen = tokens._deadline_of, []

        def paused(control, domain, generation, acquired=None):
            deadline = honest(control, domain, generation, acquired)
            if control is self.store and not seen:
                seen.append(True)
                tokens.renew(peer, token, execution=token["execution"],
                             operation=token["operation"], expected_revision=0,
                             seconds=900)
                self.instant = "2026-09-27T03:02:00.000Z"
            return deadline

        tokens._deadline_of = paused
        self.addCleanup(setattr, tokens, "_deadline_of", honest)
        try:
            self.renewing(token, expected_revision=0)
        except ContractRefusal:
            pass
        tokens._deadline_of = honest
        state = self.current()
        self.assertEqual(state["revision"], 1)
        self.assertFalse(state["expired"])
        self.assertFalse(state["timing_ambiguous"],
                         "an overtaken observation was recorded as an ambiguity")
        self.assertIsNone(state["expiry_judged_at"])

    def test_a_TORN_observation_records_nothing_however_it_was_produced(self):
        """W275775 review 2026-09-27T03-21-53Z [P1b], proved at the decision rather than at
        the seam that used to produce it.

        The reviewer's probe tore the observation by renewing between `_owning`'s two reads --
        the deadline and the revision -- and the correction removed that seam: the pair now
        comes from ONE list of committed renewals. So the pair cannot be torn there any more,
        and this case proves the property the probe was about DIRECTLY instead: a torn pair
        handed to the judgement is rejected by correlation, whatever produced it. An old
        deadline beside a new revision correlates with nothing that stands, so nothing is
        recorded and the renewed generation keeps its deadline.
        """
        token = self.held(seconds=60)
        original = self.current()["expires_at"]
        self.instant = "2026-09-27T03:00:30.000Z"
        renewed = self.renewing(token, expected_revision=0, seconds=900)
        self.instant = "2026-09-27T03:02:00.000Z"          # past the OLD deadline only
        torn = {"expires_at": original,                    # revision 0's deadline
                "revision": 1,                             # revision 1's count
                "observed_at": self.instant}
        self.assertIsNone(tokens._judge_expired(self.store, self.domain, 1, torn))
        state = self.current()
        self.assertEqual(state["revision"], 1)
        self.assertEqual(state["expires_at"], renewed["expires_at"])
        self.assertFalse(state["expired"])
        self.assertFalse(state["timing_ambiguous"])
        self.assertIsNone(state["expiry_judged_at"])

    def test_a_correlated_observation_ALWAYS_leaves_one_record(self):
        """W275775 review [P1a]: the classification is exhaustive.

        A correlated observation -- same revision, same deadline -- must produce exactly one
        durable answer whatever the clock does between the refusal and the decision. Both
        directions are driven against the same generation state: the clock left alone gives
        EXPIRED, and the clock moved backwards gives the AMBIGUITY hold. Neither can give
        nothing, which is what two separate conditional writes allowed.
        """
        for rolled_back, wanted in ((None, "expired"), ("2026-09-27T03:00:30.000Z",
                                                        "ambiguous")):
            with self.subTest(rolled_back=rolled_back):
                self.fresh()
                token = self.held(seconds=60)
                deadline = self.current()["expires_at"]
                self.instant = "2026-09-27T03:02:00.000Z"
                observed = {"expires_at": deadline, "revision": 0,
                            "observed_at": self.instant}
                if rolled_back is not None:
                    self.instant = rolled_back
                answered = tokens._judge_expired(self.store, self.domain, 1, observed)
                self.assertIsNotNone(answered, "a correlated observation decided nothing")
                state = self.current()
                if wanted == "expired":
                    self.assertTrue(state["expired"])
                    self.assertFalse(state["timing_ambiguous"])
                else:
                    self.assertTrue(state["timing_ambiguous"])
                    self.assertIsNone(state["expiry_judged_at"])

    def test_a_genuine_expiry_is_still_judged_expired_and_not_ambiguous(self):
        """The ordinary case must not be swept into the new outcome: no clock moves, the
        deadline has simply passed."""
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"
        self.refusal(lambda: self.renewing(token))
        state = self.current()
        self.assertTrue(state["expired"])
        self.assertEqual(state["expiry_judged_at"], "2026-09-27T03:02:00.000Z")
        self.assertFalse(state["timing_ambiguous"])


class TheExpectedRevisionIsTheReadersOwnRevision(RenewalCase):
    """W275775 review 02-43-54Z: one convention, in the prose and in the code."""

    def test_the_reader_to_renew_round_trip_works_on_the_first_call(self):
        """The obvious caller, which the previous convention refused: read the state,
        renew against what it says."""
        token = self.held()
        for expected in range(tokens.RENEWAL_LIMIT):
            with self.subTest(expected=expected):
                observed = self.current()["revision"]
                self.assertEqual(observed, expected)
                answered = tokens.renew(
                    self.store, token, execution=token["execution"],
                    operation=token["operation"], expected_revision=observed)
                self.assertEqual(answered["revision"], observed + 1)
                self.assertEqual(self.current()["revision"], observed + 1)

    def test_a_revision_past_the_state_is_refused_as_a_skip(self):
        token = self.held()
        refusal = self.refusal(lambda: self.renewing(token, expected_revision=1))
        self.assertEqual((refusal.category, refusal.code),
                         ("refused", "precondition"))
        self.assertIn("stands at 0", refusal.message)

    def test_a_revision_that_is_not_a_whole_number_is_refused_by_type(self):
        token = self.held()
        for offered in ("0", 1.0, True, None, -1, [0]):
            with self.subTest(expected_revision=repr(offered)):
                refusal = self.refusal(
                    lambda: self.renewing(token, expected_revision=offered))
                self.assertEqual((refusal.category, refusal.code),
                                 ("integrity", "schema"))
                self.assertEqual(self.current()["renewals"], 0)


class CompetingRenewalsSerializeIntoOneExtension(RenewalCase):
    """The proof row's concurrency clause, over two real handles on one store.

    WHY THIS RACE AND NOT RENEWAL-AGAINST-REVOCATION. Measured while writing this: with
    two managers and a deterministic clock, a revocation racing a renewal is refused in
    BOTH interleavings -- before the renewal it refuses because the token is not overdue
    yet, and after it because the deadline moved -- so the case could assert serialization
    but never distinguish which state the loser read. Its first cut asserted the loser's
    message named the RENEWED deadline and failed, quoting the acquisition's: the
    competitor had simply got there first. The arbitration point for expiry-versus-renewal
    is inherently AFTER a renewal commits, which is what
    `test_a_renewed_deadline_defeats_a_STALE_expiry_observation` proves deterministically.
    What concurrency genuinely risks here is a DOUBLE EXTENSION, and that is what this
    case is about.
    """

    def test_two_managers_renewing_one_revision_extend_it_exactly_once(self):
        """Both ask for revision 1. One commits; the other replays it or collides; the
        deadline moves once and the generation records one renewal.

        The rendezvous is real: the competitor signals before it asks and this thread does
        not ask until that signal arrives, so both requests are genuinely in flight. The
        ASSERTED outcome is deterministic in every interleaving, which is the property the
        proof row names -- "valid same-execution renewal is recorded once".
        """
        import threading

        token = self.held(seconds=60)
        original = self.current()["expires_at"]
        self.instant = "2026-09-27T03:00:30.000Z"
        answers = {}
        attempting = threading.Event()

        def competitor():
            second = ControlStore.open(self._path, incarnation="manager-2",
                                       clock=lambda: self.instant)
            try:
                attempting.set()
                answers["second"] = tokens.renew(
                    second, token, execution=token["execution"],
                    operation=token["operation"], expected_revision=0, seconds=600)
            except BaseException as failure:        # recorded, never swallowed
                answers["second"] = failure
            finally:
                second.close()

        runner = threading.Thread(target=competitor)
        runner.start()
        try:
            self.assertTrue(attempting.wait(10),
                            "the competing manager never asked for a renewal")
            try:
                answers["first"] = self.renewing(token, seconds=600)
            except ContractRefusal as refusal:
                answers["first"] = refusal
        finally:
            runner.join(10)
        self.assertFalse(runner.is_alive())

        committed = [one for one in answers.values()
                     if not isinstance(one, BaseException)]
        self.assertTrue(committed, f"neither manager renewed: {answers}")
        # EXACTLY ONE EXTENSION EXISTS, whichever of them wrote it.
        self.assertEqual(self.current()["renewals"], 1)
        self.assertEqual(self.current()["revision"], 1)
        self.assertGreater(self.current()["expires_at"], original)
        for one in committed:
            self.assertEqual(one["expires_at"], self.current()["expires_at"],
                             "a committed answer disagrees with the record")
        # AND A LOSER, IF THERE WAS ONE, LOST HONESTLY: refused, never a second record.
        for one in answers.values():
            if isinstance(one, BaseException):
                self.assertIsInstance(one, ContractRefusal)


class OnlyTheSameExecutionAndOperationMayRenew(RenewalCase):

    def test_another_execution_is_not_a_renewal(self):
        token = self.held()
        refusal = self.refusal(
            lambda: self.renewing(token, execution="attempt-somebody-else"))
        self.assertEqual((refusal.category, refusal.code),
                         ("runtime-observation", "identity-mismatch"))
        self.assertIn("somebody else's permission", refusal.message)
        self.assertEqual(self.current()["renewals"], 0)

    def test_another_operation_is_not_a_renewal(self):
        token = self.held()
        refusal = self.refusal(
            lambda: self.renewing(token, operation="runtime.start:other"))
        self.assertEqual((refusal.category, refusal.code),
                         ("runtime-observation", "identity-mismatch"))
        self.assertEqual(self.current()["renewals"], 0)

    def test_a_forged_owner_cannot_renew(self):
        """The caller's document is evidence, not authority: the committed record's
        owner is what `_owning` compares."""
        token = self.held()
        refusal = self.refusal(
            lambda: self.renewing(dict(token, owner="somebody-elses-owner")))
        self.assertEqual(refusal.code, "identity-mismatch")
        self.assertEqual(self.current()["renewals"], 0)


class ExhaustionHoldsRatherThanFrees(RenewalCase):

    def test_the_bound_refuses_and_the_resource_stays_held(self):
        token = self.held()
        for observed in range(tokens.RENEWAL_LIMIT):
            self.renewing(token, expected_revision=observed)
        refusal = self.refusal(
            lambda: self.renewing(token, expected_revision=tokens.RENEWAL_LIMIT))
        self.assertEqual((refusal.category, refusal.code), ("policy", "denied"))
        self.assertIn("does not free the resource", refusal.message)
        # STILL HELD, AND STILL THIS HOLDER'S: exhaustion is not a return.
        self.assertEqual(len(tokens.outstanding(self.store, self.domain)), 1)
        self.assertFalse(self.current()["returned"])
        self.assertFalse(self.current()["revoked"])
        # AND A COMPETITOR IS STILL EXCLUDED.
        competing = self.refusal(
            lambda: tokens.acquire(self.store, self.domain,
                                   operation="runtime.start:other",
                                   execution="attempt-other"))
        self.assertIn("outstanding baton", competing.message)


class ARenewalDoesNotResetAPopulatedJobsLimits(RenewalCase):
    """TOK-9's "It does not create a new writer or reset Job execution limits", proved
    against POPULATED state and the real reader rather than an empty table.

    W275775 review 02-43-54Z: my first version counted one extra operation row and an empty
    `attempts` table, which shows that nothing ELSE happened in the control store -- not that
    a Job's ceilings survive. Job limits live in the JOB store, read by
    `job_manager.submission.boundary_seconds` through
    `execution_limits.resolved`, so that store is populated here and that reader is asked.
    """

    def submitted(self):
        """One real Job with EXPLICIT non-default ceilings, through its own owner."""
        from baton_v12.job_manager import JobStore, submit
        from tests.job_manager import fixtures

        jobs = JobStore.open(os.path.join(os.path.dirname(self._path),
                                          "jobs.sqlite3"),
                             authority_uuid=fixtures.UUID, incarnation="jobs-b",
                             clock=lambda: self.instant)
        self.addCleanup(jobs.close)
        from baton_v12.job_manager import documents as job_documents

        # THE SCHEMA THAT ACCEPTS CEILINGS, measured rather than assumed: the shared
        # fixture composes submission `/1`, and `execution_limits` is optional only on
        # `SUBMISSION_LIMITS_SCHEMAS`, which is `/2`. A `/1` document carrying limits is
        # refused as an unknown member -- which is how I found this.
        submission = dict(fixtures.submission(),
                          schema=job_documents.SUBMISSION_SCHEMA)
        # THE SETTING NAMES ARE THE OWNER'S OWN (`execution_limits.LIMIT_MEMBERS`), not
        # the boundary names a reader asks by -- measured, because a document naming the
        # boundaries is refused member by member.
        submission["jobs"] = [dict(submission["jobs"][0],
                                   execution_limits=REQUESTED)]
        submit(jobs, submission)
        return jobs, submission["jobs"][0]["job_id"]

    def ceilings(self, jobs, job_id):
        from baton_v12.job_manager import submission as job_submission

        return {boundary: job_submission.boundary_seconds(jobs, job_id, boundary)
                for boundary in ("provider_turn", "ordinary_verification")}

    def test_the_real_reader_answers_the_same_ceilings_after_a_renewal(self):
        jobs, job_id = self.submitted()
        before = self.ceilings(jobs, job_id)
        # THE CONFIGURED VALUES, not the defaults -- otherwise this could pass while
        # reading a Job it never populated.
        from baton_v12.job_manager import execution_limits

        self.assertEqual(before["provider_turn"],
                         REQUESTED["provider_turn_seconds"])
        self.assertNotEqual(before["provider_turn"],
                            execution_limits.boundary_default("provider_turn"))

        token = self.held()
        changes = jobs._connection.total_changes
        for observed in range(tokens.RENEWAL_LIMIT):
            self.renewing(token, expected_revision=observed)
        self.assertEqual(self.current()["renewals"], tokens.RENEWAL_LIMIT)

        # NOT ONE WRITE IN THE JOB STORE, and the reader still answers the same numbers.
        self.assertEqual(jobs._connection.total_changes, changes)
        self.assertEqual(self.ceilings(jobs, job_id), before)
        # AND THE LIMIT ROW ITSELF IS UNTOUCHED.
        from baton_v12.job_manager.submission import execution_limits_of
        self.assertEqual(execution_limits_of(jobs, job_id)["requested"], REQUESTED)

    def test_an_exhausted_renewal_allowance_is_not_a_job_limit_at_all(self):
        """The two bounds are separate, which is the other half of the requirement: a
        generation with no renewals left still has its Job's full per-invocation
        ceilings, because a renewal allowance is not a Job budget."""
        jobs, job_id = self.submitted()
        token = self.held()
        for observed in range(tokens.RENEWAL_LIMIT):
            self.renewing(token, expected_revision=observed)
        self.refusal(lambda: self.renewing(token,
                                           expected_revision=tokens.RENEWAL_LIMIT))
        self.assertEqual(self.current()["renewals_remaining"], 0)
        self.assertEqual(self.ceilings(jobs, job_id),
                         {"provider_turn": REQUESTED["provider_turn_seconds"],
                          "ordinary_verification":
                              REQUESTED["verification_command_seconds"]})


class AScheduledExpiryAndRenewalCompeteAtTheWriteBoundary(RenewalCase):
    """The two-handle arbitration at the ACTUAL transaction boundary, both directions.

    The earlier concurrent case proved two renewals serialize into one extension. This one
    schedules expiry against renewal with a DETERMINISTIC winner, and it does so by holding
    the winner inside its own write transaction while the loser's act is issued on a second
    handle: SQLite's write lock is what makes the order certain, so the loser cannot commit
    first no matter how the threads are scheduled.

    The pause is taken inside the production act's OWN in-transaction work -- the callback
    `transact` runs under the lock -- rather than by wrapping a connection from outside,
    which measured as `cannot start a transaction within a transaction`: every act here
    takes its own transaction, so a fixture that took one first broke the act rather than
    scheduling it.
    """

    def issued(self, act):
        """Issue `act` on a SECOND handle, and answer once it has been attempted.

        Returns the thread plus an event that is set immediately before the call, so the
        act under test can wait for the competitor to be in flight while it still holds
        the write lock.
        """
        import threading

        attempting, answers = threading.Event(), {}

        def competitor():
            second = ControlStore.open(self._path, incarnation="manager-2",
                                       clock=lambda: self.instant)
            try:
                attempting.set()
                answers["second"] = act(second)
            except BaseException as failure:            # recorded, never swallowed
                answers["second"] = failure
            finally:
                second.close()

        runner = threading.Thread(target=competitor)
        runner.start()
        self.addCleanup(runner.join, 10)
        return attempting, answers, runner

    def revoking(self):
        return lambda second: tokens.revoke(
            second, "line-9/workspace", "workspace",
            execution="attempt-b", operation="runtime.start:b")

    def test_a_renewal_holding_the_write_lock_wins_and_the_revocation_refuses(self):
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:00:30.000Z"
        state = {}
        honest = tokens._renewals_of

        def pausing(control, domain, generation):
            answer = honest(control, domain, generation)
            # PAUSE ONLY WHILE THE WRITE LOCK IS ACTUALLY HELD, asked of the connection
            # rather than counted. MEASURED: counting calls put the pause on the
            # pre-transaction read, so the competitor never blocked at all, read the
            # pre-renewal state and refused against the ORIGINAL deadline -- the case
            # looked like a race and was not one.
            if control._connection.in_transaction and "answers" not in state:
                attempting, answers, runner = self.issued(self.revoking())
                state.update(answers=answers, runner=runner)
                self.assertTrue(attempting.wait(10))
            return answer

        tokens._renewals_of = pausing
        self.addCleanup(setattr, tokens, "_renewals_of", honest)
        renewed = self.renewing(token, seconds=600)
        state["runner"].join(10)
        tokens._renewals_of = honest

        held = state["answers"]["second"]
        self.assertIsInstance(held, ContractRefusal)
        self.assertIn("is not overdue", held.message)
        # IT REFUSED AGAINST THE RENEWED DEADLINE: the arbitration, not the ordering, is
        # what decided it.
        self.assertIn(renewed["expires_at"], held.message)
        self.assertFalse(self.current()["revoked"])
        self.assertEqual(self.current()["renewals"], 1)

    def test_a_revocation_holding_the_write_lock_wins_and_the_renewal_refuses(self):
        token = self.held(seconds=60)
        self.instant = "2026-09-27T03:02:00.000Z"       # overdue: revocation is eligible
        state = {}
        honest = tokens.generation_of

        def pausing(control, domain, *, execution, operation):
            answer = honest(control, domain, execution=execution, operation=operation)
            # `revoke` resolves the generation INSIDE its own `BEGIN IMMEDIATE`, so this
            # call is the one holding the write lock.
            if "answers" not in state:
                attempting, answers, runner = self.issued(
                    lambda second: tokens.renew(
                        second, token, execution=token["execution"],
                        operation=token["operation"], expected_revision=0))
                state.update(answers=answers, runner=runner)
                self.assertTrue(attempting.wait(10))
            return answer

        tokens.generation_of = pausing
        self.addCleanup(setattr, tokens, "generation_of", honest)
        revoked = tokens.revoke(self.store, "line-9/workspace", "workspace",
                               execution=token["execution"],
                               operation=token["operation"])
        state["runner"].join(10)
        tokens.generation_of = honest

        self.assertEqual(revoked["generation"], 1)
        self.assertTrue(self.current()["revoked"])
        held = state["answers"]["second"]
        self.assertIsInstance(held, ContractRefusal)
        self.assertEqual(self.current()["renewals"], 0,
                         "a renewal committed after revocation won")
        # AND IT LOST FOR A REASON THAT NAMES THE WINNER's fact, not a generic error.
        self.assertTrue("REVOKED" in held.message or "expired" in held.message,
                        held.message)


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = unittest.TestSuite(
        loader.loadTestsFromTestCase(case) for case in
        (AValidRenewalIsRecordedOnce, AReplayDoesNotExtendTwice,
         ExpiryAndRenewalCompeteAgainstTheSameState,
         TheBoundNeverHIDESACommittedRenewal,
         AJudgedExPIRYCannotBeArguedWithByTheClock,
         AStaleObservationCannotJudgeACommittedRenewalExpired,
         TimeMovingBackwardsIsHeldRatherThanGuessedAt,
         TheExpectedRevisionIsTheReadersOwnRevision,
         CompetingRenewalsSerializeIntoOneExtension,
         ARenewalDoesNotResetAPopulatedJobsLimits,
         AScheduledExpiryAndRenewalCompeteAtTheWriteBoundary,
         OnlyTheSameExecutionAndOperationMayRenew, ExhaustionHoldsRatherThanFrees))
    raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
