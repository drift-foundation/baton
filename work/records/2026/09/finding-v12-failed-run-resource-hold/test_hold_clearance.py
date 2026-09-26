"""R2: only exact settlement evidence clears ONE hold.

Owner 260109 selects R2 only: "Implement exact-episode settlement and
clearance validation in custody.py and test_hold_clearance.py… Prove exact
positive clearance, replay, rejection of mismatched or malformed evidence, and
continued hold on ambiguous settlement."

THE PLAN'S BAR, and it is the whole subject of this stage: "Plain observation
text, local CLI exit, an empty helper listing after client timeout, or any
nonzero/unaccountable answer is not enough to exclude a delayed daemon
request. If that evidence cannot be supplied, the selected result is still
held."

So every refusal below is one of those four, and the positive case is the one
shape that is none of them: the daemon's own accountable answer for the exact
helper this episode recorded, under the exact custodian image it recorded.

WHAT IS REAL HERE: the manager's own `clear_custody_hold` and `custody_holds`,
its own `ControlStore` journal and signatures, and real directories on the
owner-selected disk-backed root. The ENGINE is the accepted fake port this
campaign's focused cases use, so no daemon, container or image is reached --
which is also why the crash and the settlement are SIMULATED, and this module
says so rather than implying a live engine answered anything.

NO oci.py CHANGE WAS NEEDED. R2 permits one "only if its engine-answer
contract needs a coordinated bounded change". Nothing here asks an engine
anything: a settlement is a document DELIVERED to the manager, and what the
manager owns is whether the delivered answer settles the episode it names. So
the engine-answer contract is read and not touched, and no ownership
amendment is required.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:                                     # pragma: no cover
    sys.path.insert(0, HERE)

from baton_v12.contracts import ContractRefusal                # noqa: E402
from baton_v12.worker_manager import custody                   # noqa: E402
from baton_v12.worker_manager import workspaces                # noqa: E402
from baton_v12.worker_manager.store import (manager_signature   # noqa: E402
                                            )

from test_abandonment import TheComposedAbandonmentIsCalled    # noqa: E402


class OnlyExactSettlementClearsOneHold(TheComposedAbandonmentIsCalled):
    """One real uncertainty episode, and everything that does not lift it."""

    # -- one real held episode ------------------------------------------------

    def held_episode(self, incarnation):
        """A REAL uncertainty: the request crossed and nothing answered.

        Reuses the parent fixture's own severing path, so the episode under
        test is one `custody_act` actually recorded rather than a row this
        module wrote.
        """
        control, composed, attempt_id = self.unresolved_custody(incarnation)
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        [episode] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(episode["cleared"])
        return control, composed, attempt_id, episode["held"]

    def reopened(self, incarnation):
        """A SECOND manager over the same control store file."""
        from baton_v12.worker_manager import ControlStore
        from tests.job_manager import fixtures

        return ControlStore.open(self.control_path, incarnation=incarnation,
                                 clock=lambda: fixtures.NOW)

    def restored(self):
        """Let the fake custodian answer again, for the post-clearance act."""
        for engine in self.engines:
            engine.__class__.acting = \
                TheComposedAbandonmentIsCalled.Removing.acting

    # -- the one shape that settles ------------------------------------------

    def submitted(self, index=-1):
        """The token the provider was actually handed, in submission order.

        W257624 R2, ATTRIBUTION-PLAN item 4: the fake provider records what it
        received on the ARGV, which is the only place a provider could learn
        it. A fixture that read the latest hold instead would manufacture the
        attribution the real boundary cannot supply, so `index` names the
        submission a case is reconciling -- 0 is the first act over that root.
        """
        seen = []
        for engine in self.engines:
            seen.extend(getattr(engine, "submissions", []))
        return seen[index]

    def answered(self, held, *, verb=None, entries=1, status=0, source=None,
                 document=None, helper=None, image=None, submission=None):
        """The daemon's own answer about this helper, as delivered evidence.

        Composed from what the EPISODE recorded, so a case that changes one
        member is changing exactly one thing. The document's shape is the
        custodian program's own -- the same one `_accountable` holds a live act
        to -- rather than a shape this module invented for itself.
        """
        verb = held["verb"] if verb is None else verb
        return {
            "source": (custody.CUSTODY_ENGINE_ANSWER if source is None
                       else source),
            "helper_identity": (held["helper_identity"] if helper is None
                                else helper),
            "custodian_image_digest": (held["custodian_image_digest"]
                                       if image is None else image),
            "status": status,
            "document": ({"custody": verb,
                          "submission": (self.submitted()
                                         if submission is None
                                         else submission),
                          "entries": entries, "not_ours": 0,
                          "running_as": [os.getuid(), os.getgid()]}
                         if document is None else document)}

    def clearing(self, control, attempt_id, held, **operands):
        """One clearance, with each operand defaulted from the episode.

        The defaults are resolved BEFORE the call rather than inside keyword
        defaults: `dict.pop(key, default)` evaluates its default eagerly, so
        composing the settlement there ran `answered(**operands)` even when a
        case had supplied a whole settlement of its own. Found by the run.
        """
        observed = operands.pop(
            "observed", "I asked the daemon for this helper and it answered")
        helper_identity = operands.pop("helper_identity",
                                       held["helper_identity"])
        if "settlement" in operands:
            settlement = operands.pop("settlement")
            if operands:
                raise AssertionError(f"unused operands: {sorted(operands)}")
        else:
            settlement = self.answered(held, **operands)
        return custody.clear_custody_hold(
            control, attempt_id=attempt_id, which="result", episode=0,
            observed=observed, helper_identity=helper_identity,
            settlement=settlement)

    def refuses(self, control, attempt_id, held, **operands):
        """One clearance that must refuse, lifting nothing when it does."""
        with self.assertRaises(ContractRefusal) as caught:
            self.clearing(control, attempt_id, held, **operands)
        [standing] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(standing["cleared"],
                         "a refused clearance lifted the hold anyway")
        return caught.exception.message

    # -- positive ------------------------------------------------------------

    def test_an_exact_engine_answer_clears_exactly_one_episode(self):
        """THE POSITIVE: the one evidence that is none of the four."""
        control, composed, attempt_id, held = self.held_episode("clear-exact")
        answer = self.clearing(control, attempt_id, held)

        # THE CLEARANCE RECORDS WHAT SETTLED IT, not only that somebody looked.
        self.assertEqual(answer["episode"], 0)
        self.assertEqual(answer["helper_identity"], held["helper_identity"])
        self.assertEqual(answer["settlement"]["source"],
                         custody.CUSTODY_ENGINE_ANSWER)
        self.assertEqual(answer["settlement"]["status"], 0)
        self.assertEqual(answer["settlement"]["document"]["custody"],
                         held["verb"])

        [cleared] = custody.custody_holds(control, attempt_id, "result")
        self.assertTrue(cleared["cleared"])
        # AND THE ACT MAY PROCEED, which is what a clearance is FOR.
        self.restored()
        proceeded = custody.normalize_directory(control, composed,
                                                assignment_id=attempt_id,
                                                which="result")
        self.assertEqual(proceeded["root"], "result")

    def test_the_clearance_replays_rather_than_being_written_twice(self):
        """IMMUTABLE REPLAY, and it is the store's rule rather than a new one.

        An identical clearance at the same identity replays its own record --
        what a journal does. A DIFFERENT one at that identity is refused by
        §4.2, one identity carries one act, so a second operator cannot revise
        what the first recorded.
        """
        control, _composed, attempt_id, held = self.held_episode(
            "clear-replay")
        first = self.clearing(control, attempt_id, held)
        again = self.clearing(control, attempt_id, held)
        self.assertEqual(again, first)
        self.assertEqual(
            len(custody.custody_holds(control, attempt_id, "result")), 1)

        # A REVISION AT THE SAME IDENTITY IS REFUSED.
        with self.assertRaises(ContractRefusal):
            self.clearing(control, attempt_id, held,
                          observed="actually I observed something else")
        [cleared] = custody.custody_holds(control, attempt_id, "result")
        self.assertTrue(cleared["cleared"])

    # -- the four the PLAN names ---------------------------------------------

    def test_plain_operator_text_no_longer_clears(self):
        """THE CHANGE R2 MAKES, stated as the case that used to pass.

        "I inspected the daemon; no helper of that name exists" is a true
        account of an absence and was accepted before this stage. It is true of
        a request that has not run yet, so it no longer clears anything.
        """
        control, _composed, attempt_id, held = self.held_episode("clear-text")
        with self.assertRaises(TypeError):
            # THERE IS NO LONGER A CALL THAT OMITS THE EVIDENCE. The operand is
            # required, so the old shape is not a weaker clearance -- it is not
            # a clearance at all.
            custody.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=0,
                observed="I inspected the daemon; no helper of that name "
                         "exists",
                helper_identity=held["helper_identity"])
        [standing] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(standing["cleared"])
        # AND THE OPERATOR'S ACCOUNT IS STILL REQUIRED, just not sufficient.
        why = self.refuses(control, attempt_id, held, observed="   ")
        self.assertIn("not an observation", why)

    def test_a_local_exit_status_is_not_a_settlement(self):
        """A local command's exit says nothing about the daemon's queue."""
        control, _composed, attempt_id, held = self.held_episode("clear-local")
        why = self.refuses(control, attempt_id, held, source="local-exit")
        self.assertIn("still pending", why)

    def test_an_empty_helper_listing_is_not_a_settlement(self):
        """AN ABSENCE IS NOT AN ENDING, which is the whole hold in one case.

        A listing that comes back without the helper is the evidence a client
        timeout produces, and it is exactly compatible with a request the
        daemon has not started. Refused by its source, and refused again when
        it is dressed as an engine answer whose document is an empty listing
        for a different verb than the one this episode submitted.
        """
        control, _composed, attempt_id, held = self.held_episode("clear-list")
        self.assertIn("still pending",
                      self.refuses(control, attempt_id, held,
                                   source="helper-listing"))
        # DRESSED AS AN ENGINE ANSWER: an `inspect` of nothing is accountable
        # as an inspect and is still not an account of the submitted verb.
        why = self.refuses(control, attempt_id, held, document={
            "custody": "inspect", "entries": [],
            "running_as": [os.getuid(), os.getgid()]})
        self.assertIn("an account of a different act", why)
        self.assertIn(held["verb"], why)

    def test_a_nonzero_answer_never_clears(self):
        """A failing act is an unaccounted act, which is what is held."""
        control, _composed, attempt_id, held = self.held_episode("clear-fail")
        why = self.refuses(control, attempt_id, held, status=1)
        self.assertIn("nonzero", why)

    def test_an_unaccountable_answer_never_clears(self):
        """Four ways a document fails the accountability rule."""
        control, _composed, attempt_id, held = self.held_episode("clear-junk")
        for document in (
                {},                                    # nothing to read
                {"custody": held["verb"], "entries": 1,
                 "not_ours": 0},                       # no running_as
                {"custody": held["verb"], "entries": 1, "not_ours": 0,
                 "running_as": [os.getuid(), os.getgid()],
                 "extra": "unreviewed"},               # an unexpected member
                {"custody": "refused", "why": "the custodian refused"}):
            with self.subTest(document=sorted(document)):
                why = self.refuses(control, attempt_id, held,
                                   document=document)
                self.assertIn("not an accountable", why)

    def test_an_ambiguous_answer_never_clears(self):
        """THE UNRESOLVED SHAPE ITSELF, which is why the episode exists.

        `CustodyAnswer` calls an act with no engine answer UNRESOLVED by
        `status is None`. A settlement may not carry that: there is no integer
        status to read, so the contract refuses it as the schema violation it
        is rather than treating absence as zero.
        """
        control, _composed, attempt_id, held = self.held_episode("clear-amb")
        for status in (None, "0", True):
            with self.subTest(status=status):
                settlement = self.answered(held)
                settlement["status"] = status
                why = self.refuses(control, attempt_id, held,
                                   settlement=settlement)
                self.assertIn("status", why)

    # -- mismatched binding --------------------------------------------------

    def test_a_settlement_for_another_helper_refuses(self):
        control, _composed, attempt_id, held = self.held_episode(
            "clear-other-helper")
        why = self.refuses(control, attempt_id, held,
                           helper=custody.CUSTODY_NAME + "-" + "0" * 32)
        self.assertIn("another act", why)

    def test_a_settlement_under_another_custodian_image_refuses(self):
        """The same name under a different custodian is a different act."""
        control, _composed, attempt_id, held = self.held_episode(
            "clear-other-image")
        why = self.refuses(control, attempt_id, held,
                           image="sha256:" + "f" * 64)
        self.assertIn("another act", why)

    def test_a_clearance_naming_another_helper_refuses(self):
        control, _composed, attempt_id, held = self.held_episode(
            "clear-named-helper")
        why = self.refuses(control, attempt_id, held,
                           helper_identity=custody.CUSTODY_NAME + "-"
                           + "1" * 32)
        self.assertIn("evidence about the helper", why)

    def test_an_episode_this_manager_never_recorded_refuses(self):
        control, _composed, attempt_id, held = self.held_episode(
            "clear-no-episode")
        with self.assertRaises(ContractRefusal) as caught:
            custody.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=3,
                observed="I asked the daemon", settlement=self.answered(held),
                helper_identity=held["helper_identity"])
        self.assertIn("no uncertainty episode", caught.exception.message)

    def test_the_other_root_cannot_be_cleared_by_this_evidence(self):
        """The hold is per root, and so is its clearance."""
        control, _composed, attempt_id, held = self.held_episode(
            "clear-other-root")
        with self.assertRaises(ContractRefusal) as caught:
            custody.clear_custody_hold(
                control, attempt_id=attempt_id, which="workspace", episode=0,
                observed="I asked the daemon", settlement=self.answered(held),
                helper_identity=held["helper_identity"])
        self.assertIn("no uncertainty episode", caught.exception.message)
        [standing] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(standing["cleared"])

    # -- malformed and forged records ----------------------------------------

    def rewrite(self, control, identity, **columns):
        """Replace journal columns for one operation, in the real store.

        A DISPOSABLE STORE IS THE ONLY PLACE THIS IS HONEST: what is being
        tested is what the manager does when the row it reads is not the row it
        committed, and that state cannot be reached through the API by
        construction -- which is the point.
        """
        sets = ", ".join(f"{name} = ?" for name in sorted(columns))
        control._connection.execute(
            f"UPDATE operations SET {sets} WHERE operation_id = ?",
            [columns[name] for name in sorted(columns)] + [identity])

    def test_a_hold_whose_document_was_replaced_cannot_be_cleared(self):
        """THE SIGNATURE IS CHECKED, so a swapped document is not evidence."""
        control, _composed, attempt_id, held = self.held_episode(
            "clear-forged-hold")
        identity = custody._hold_identity(custody.CUSTODY_HOLD_KIND,
                                          attempt_id, "result", 0)
        forged = dict(held, helper_identity=custody.CUSTODY_NAME + "-"
                      + "2" * 32)
        self.rewrite(control, identity, result=json.dumps(forged))
        with self.assertRaises(ContractRefusal) as caught:
            custody.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=0,
                observed="I asked the daemon",
                settlement=self.answered(forged),
                helper_identity=forged["helper_identity"])
        self.assertIn("signature", caught.exception.message)

    def test_a_hold_record_of_another_kind_is_not_cleared(self):
        control, _composed, attempt_id, held = self.held_episode(
            "clear-wrong-kind")
        identity = custody._hold_identity(custody.CUSTODY_HOLD_KIND,
                                          attempt_id, "result", 0)
        self.rewrite(control, identity, kind="runtime.destroy")
        with self.assertRaises(ContractRefusal) as caught:
            self.clearing(control, attempt_id, held)
        self.assertIn("kind", caught.exception.message)

    def test_a_hold_that_names_another_episode_is_not_cleared(self):
        """The document's own binding is checked, not just its key."""
        control, _composed, attempt_id, held = self.held_episode(
            "clear-other-binding")
        identity = custody._hold_identity(custody.CUSTODY_HOLD_KIND,
                                          attempt_id, "result", 0)
        moved = dict(held, episode=7)
        self.rewrite(control, identity, result=json.dumps(moved),
                     signature=manager_signature(custody.CUSTODY_HOLD_KIND,
                                                 moved))
        with self.assertRaises(ContractRefusal) as caught:
            self.clearing(control, attempt_id, held)
        self.assertIn("episode it actually describes",
                      caught.exception.message)

    def test_a_clearance_whose_document_was_replaced_lifts_nothing(self):
        """The READER checks the lift's signature too.

        A clearance is the one direction where believing an unverifiable
        document is unsafe, so `custody_holds` refuses rather than reporting
        `cleared` on the strength of a key.
        """
        control, _composed, attempt_id, held = self.held_episode(
            "clear-forged-lift")
        self.clearing(control, attempt_id, held)
        identity = custody._hold_identity(custody.CUSTODY_CLEARED_KIND,
                                          attempt_id, "result", 0)
        self.rewrite(control, identity,
                     result=json.dumps({"attempt_id": attempt_id,
                                        "root": "result", "episode": 0,
                                        "helper_identity":
                                            held["helper_identity"],
                                        "observed": "forged"}))
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_holds(control, attempt_id, "result")
        self.assertIn("signature", caught.exception.message)

    def test_an_unreadable_clearance_lifts_nothing(self):
        control, _composed, attempt_id, held = self.held_episode(
            "clear-unreadable-lift")
        self.clearing(control, attempt_id, held)
        identity = custody._hold_identity(custody.CUSTODY_CLEARED_KIND,
                                          attempt_id, "result", 0)
        self.rewrite(control, identity, result="{not a document")
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_holds(control, attempt_id, "result")
        # THE STORE'S OWN DECODER REFUSES FIRST, which is a stronger boundary
        # than this module's: an undecodable persisted value never becomes a
        # document for anything to read. Measured, not assumed -- I expected
        # the signature check here and the run said otherwise.
        self.assertIn("round-trips", caught.exception.message)

    # -- two uncertainties stay two ------------------------------------------

    def test_a_second_uncertainty_is_its_own_episode(self):
        """Clearing one episode does not lift the next one.

        This is the separation the episode-bearing identity exists for: a
        clearance written for the first act must not authorize acting past a
        second, later uncertainty over the same root.
        """
        control, composed, attempt_id, held = self.held_episode(
            "clear-second")
        self.clearing(control, attempt_id, held)
        # A SECOND ACT, still severed, records its OWN episode.
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertEqual(len(holds), 2, holds)
        self.assertTrue(holds[0]["cleared"])
        self.assertFalse(holds[1]["cleared"])
        # AND THE ROOT IS FROZEN AGAIN: the first clearance lifted episode 0
        # and nothing else.
        self.restored()
        with self.assertRaises(ContractRefusal) as caught:
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertIn("FROZEN", caught.exception.message)
        # AND THE SECOND EPISODE IS NOT SETTLED BY THE FIRST ACT'S ANSWER.
        #
        # THE HISTORY OF THIS ONE CASE IS THE HISTORY OF THE STAGE. It first
        # "cleared episode 1 with its own evidence" and passed, which was
        # hollow: the helper identity excludes the episode, so the two
        # documents were byte-identical. I then made it assert a
        # document-equality refusal, which review 2026-09-24T21-55-12Z rightly
        # called deduplication rather than attribution. What holds now is the
        # SUBMISSION TOKEN: episode 0's act echoed episode 0's token, and that
        # answer cannot settle a different submission however ordinary its
        # contents look.
        second = holds[1]["held"]
        self.assertEqual(second["helper_identity"], held["helper_identity"],
                         "the helper identity is still not "
                         "submission-specific, which is why the token is what "
                         "does the work")
        self.assertNotEqual(self.submitted(0), self.submitted(1),
                            "two submissions must carry two tokens")
        with self.assertRaises(ContractRefusal) as stale:
            custody.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=1,
                observed="the answer I already recorded for episode zero",
                helper_identity=second["helper_identity"],
                settlement=self.answered(second,
                                         submission=self.submitted(0)))
        self.assertIn("answers for submission", stale.exception.message)
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertTrue(holds[0]["cleared"])
        self.assertFalse(holds[1]["cleared"],
                         "a stale answer lifted a second submission")

    def test_identical_results_from_distinct_submissions_still_settle(self):
        """ATTRIBUTION-PLAN item 6, which the dedup rule would have blocked.

        Two legitimate acts over one root can report the SAME counts and the
        same identities -- repetition of output content is not repetition of
        the submitted act. So this case settles the second episode with an
        answer whose ordinary fields are identical to the first's, and only its
        token differs. The document-equality check I had written would have
        refused this valid evidence; the token accepts it and still refuses the
        stale one above.
        """
        control, composed, attempt_id, held = self.held_episode(
            "clear-second-distinct")
        self.clearing(control, attempt_id, held)
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        holds = custody.custody_holds(control, attempt_id, "result")
        second = holds[1]["held"]
        first = self.answered(second, submission=self.submitted(0))
        same = self.answered(second, submission=self.submitted(1))
        self.assertEqual(
            {one: value for one, value in first["document"].items()
             if one != "submission"},
            {one: value for one, value in same["document"].items()
             if one != "submission"},
            "this case is only meaningful while the ordinary fields match")
        custody.clear_custody_hold(
            control, attempt_id=attempt_id, which="result", episode=1,
            observed="I asked the daemon about the second act",
            helper_identity=second["helper_identity"], settlement=same)
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertTrue(all(one["cleared"] for one in holds), holds)

    # -- the reader's own limits ----------------------------------------------

    def test_a_gap_in_the_episodes_stops_the_reader(self):
        """A missing episode bounds the scan rather than being read past."""
        control, composed, attempt_id, held = self.held_episode("clear-gap")
        # A SECOND EPISODE ONLY EXISTS PAST A CLEARED FIRST ONE -- the standing
        # hold refuses the act outright otherwise, which is R1's rule and is
        # why this case clears before it accumulates.
        self.clearing(control, attempt_id, held)
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertEqual(
            len(custody.custody_holds(control, attempt_id, "result")), 2)
        # SPOIL THE FIRST. The journal defends its own shape twice over and
        # both were measured here rather than assumed: `state` is constrained
        # to `committed` or `refused`, and a second constraint ties each state
        # to its columns -- a refused row carries a refusal and NO result. So
        # the only not-committed row this store will hold is a properly refused
        # one, which is exactly what a reader must not act past.
        self.rewrite(control,
                     custody._hold_identity(custody.CUSTODY_HOLD_KIND,
                                            attempt_id, "result", 0),
                     state="refused", result=None,
                     refusal=json.dumps({"category": "refused",
                                         "code": "precondition",
                                         "message": "spoiled for this case",
                                         "durable": True},
                                        sort_keys=True))
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_holds(control, attempt_id, "result")
        self.assertIn("is not one it may act past", caught.exception.message)

    def test_an_absent_intermediate_episode_is_refused_not_read_past(self):
        """A GENUINE ABSENCE, which is the case review 2026-09-24T21-39-09Z
        asked for.

        My earlier gap case marked a row `refused`, which is a different
        record rather than a missing one. This removes episode 0 outright. The
        reader used to `break` there and report NOTHING -- so a root carrying
        an uncleared episode 1 read as unheld, which is the one way this
        machinery could fail open. It refuses now.
        """
        control, composed, attempt_id, held = self.held_episode("clear-absent")
        self.clearing(control, attempt_id, held)
        with self.assertRaises(ContractRefusal):
            custody.normalize_directory(control, composed,
                                        assignment_id=attempt_id,
                                        which="result")
        self.assertEqual(
            len(custody.custody_holds(control, attempt_id, "result")), 2)
        for kind in (custody.CUSTODY_HOLD_KIND, custody.CUSTODY_CLEARED_KIND):
            control._connection.execute(
                "DELETE FROM operations WHERE operation_id = ?",
                (custody._hold_identity(kind, attempt_id, "result", 0),))
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_holds(control, attempt_id, "result")
        self.assertIn("and no episode 0", caught.exception.message)

    def test_more_episodes_than_this_manager_counts_are_refused(self):
        """OVERFLOW: reaching the bound is itself a refusal.

        Written through the store's own transaction API rather than as real
        acts, because what is under test is the READER's bound and 65 real
        uncertainties would be 65 fake-engine round trips proving the same
        thing.
        """
        control, _composed, attempt_id, held = self.held_episode(
            "clear-overflow")
        for episode in range(1, custody._MOST_HOLDS + 1):
            body = dict(held, episode=episode)
            control.transact(
                custody._hold_identity(custody.CUSTODY_HOLD_KIND, attempt_id,
                                       "result", episode),
                custody.CUSTODY_HOLD_KIND,
                manager_signature(custody.CUSTODY_HOLD_KIND, body),
                lambda _c, one=body: dict(one))
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_holds(control, attempt_id, "result")
        self.assertIn("more uncertainty episodes than this manager counts",
                      caught.exception.message)

    def test_a_hold_naming_no_helper_is_reconciled_rather_than_read(self):
        control, _composed, attempt_id, held = self.held_episode(
            "clear-no-helper")
        empty = {one: value for one, value in held.items()
                 if one != "helper_identity"}
        self.rewrite(control,
                     custody._hold_identity(custody.CUSTODY_HOLD_KIND,
                                            attempt_id, "result", 0),
                     result=json.dumps(empty),
                     signature=manager_signature(custody.CUSTODY_HOLD_KIND,
                                                 empty))
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_holds(control, attempt_id, "result")
        self.assertIn("names no helper", caught.exception.message)

    # -- author equivalents for the reviewer setups R2 invalidated -----------
    #
    # The three reviewer modules are HISTORICAL IMMUTABLE EVIDENCE and are not
    # edited. Two of their cases build custodian documents without the
    # `submission` field, which this stage now requires, so their SETUPS no
    # longer reach the boundary they were written for -- their safety CLAIMS
    # are unchanged and are re-asserted here with the token in place, as
    # review-2026-09-24T22-22-09Z directs.
    #
    # The third, `review_r2_counterexamples`'s stale-settlement case, is
    # re-asserted by `test_a_second_uncertainty_is_its_own_episode` above.

    def test_a_nonzero_accountable_answer_stays_held(self):
        """Equivalent of `review_r2_direct_clearance`, with the token echoed.

        A nonzero answer is the client's account of its own failure, so the
        daemon may still be running what it accepted. The document is complete
        and attributed here -- so the ONLY thing keeping this held is the
        status, which is what the case is about.
        """
        control, composed, attempt_id = self.unresolved_custody(
            "clear-nonzero")

        def failing(one, argv, mount, verb):
            del mount, verb
            one.vectors.append(list(argv))
            one.__dict__.setdefault("submissions", []).append(argv[-1])
            return one.answer(status=1, stdout=json.dumps(
                {"custody": "normalize", "submission": argv[-1],
                 "entries": 1, "not_ours": 0,
                 "running_as": [os.getuid(), os.getgid()]}))

        for engine in self.engines:
            engine.__class__.acting = failing
        answer = composed.normalize_directory(control,
                                              assignment_id=attempt_id,
                                              which="result")
        self.assertEqual(answer.status, 1)
        self.assertFalse(answer.ok)
        self.assertIsNone(answer.unaccounted, "the document is complete")
        [held] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(held["cleared"])

    def test_an_unused_earlier_direct_answer_cannot_settle_a_new_one(self):
        """Equivalent of `review_r2_evidence_binding`, with the token echoed.

        The first act SUCCEEDS and clears itself, so its output is a real
        accountable answer this manager consumed. The second act loses its
        response. The first act's answer -- unused as a settlement, and
        otherwise perfectly valid -- carries the first submission's token and
        cannot settle the second.
        """
        control, composed, attempt_id = self.unresolved_custody("clear-unused")

        def succeeding(one, argv, mount, verb):
            del mount, verb
            one.vectors.append(list(argv))
            one.__dict__.setdefault("submissions", []).append(argv[-1])
            return one.answer(status=0, stdout=json.dumps(
                {"custody": "normalize", "submission": argv[-1],
                 "entries": 1, "not_ours": 0,
                 "running_as": [os.getuid(), os.getgid()]}))

        for engine in self.engines:
            engine.__class__.acting = succeeding
        self.assertTrue(composed.normalize_directory(
            control, assignment_id=attempt_id, which="result").ok)
        [first] = custody.custody_holds(control, attempt_id, "result")
        self.assertTrue(first["cleared"])

        def lost(one, argv, mount, verb):
            del mount, verb
            one.vectors.append(list(argv))
            one.__dict__.setdefault("submissions", []).append(argv[-1])
            raise RuntimeError("lost the response to the second submission")

        for engine in self.engines:
            engine.__class__.acting = lost
        self.assertFalse(composed.normalize_directory(
            control, assignment_id=attempt_id, which="result").ok)
        holds = custody.custody_holds(control, attempt_id, "result")
        self.assertEqual(len(holds), 2)
        self.assertFalse(holds[1]["cleared"])
        with self.assertRaises(ContractRefusal) as caught:
            custody.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=1,
                observed="retained output from the first successful act",
                helper_identity=holds[1]["held"]["helper_identity"],
                settlement=self.answered(holds[1]["held"],
                                         submission=self.submitted(0)))
        self.assertIn("answers for submission", caught.exception.message)
        self.assertFalse(custody.custody_holds(control, attempt_id,
                                               "result")[1]["cleared"])

    def test_the_embedded_program_refuses_a_missing_or_bad_token(self):
        """THE PROGRAM'S OWN INPUT CONTRACT, run rather than described.

        `CUSTODY_PROGRAM` is this module's source, not the image's, so the
        actual embedded program can be executed here. A missing or malformed
        token is refused BEFORE the root is touched, and a good one is echoed.
        """
        import subprocess
        import tempfile

        # THE MARKER GOES IN THE ROOT THE PROGRAM ACTUALLY WALKS.
        #
        # Review 2026-09-24T23-02-34Z: my first version put it in an unrelated
        # temporary directory while the program's `ROOT` stayed `/custody`, so
        # "a refused act touched nothing" was true of a directory the program
        # was never going to look at. The program's ROOT is substituted here --
        # the same technique the accepted contract cases use -- so the
        # marker is in the tree a `discard` would have emptied.
        with tempfile.TemporaryDirectory(prefix="w257624-program-") as room:
            marker = os.path.join(room, "worker-output")
            with open(marker, "w", encoding="utf-8") as writing:
                writing.write("untouched\n")
            program = custody.CUSTODY_PROGRAM.replace(
                'ROOT = "/custody"', f"ROOT = {room!r}", 1)
            self.assertIn(f"ROOT = {room!r}", program,
                          "the root substitution did not take")
            # `discard` is the destructive verb, so a refusal that still left
            # this file is the statement worth making.
            for operands in ([], ["not-hex"], [""], ["A" * 200]):
                with self.subTest(operands=operands):
                    ran = subprocess.run(
                        [sys.executable, "-c", program, "discard", *operands],
                        capture_output=True, text=True, timeout=30)
                    self.assertEqual(ran.returncode, 2)
                    answered = json.loads(ran.stdout)
                    self.assertEqual(answered["custody"], "refused")
                    self.assertIn("no readable submission", answered["why"])
                    self.assertTrue(os.path.exists(marker),
                                    "a refused act emptied the root it walks")
            # AND A GOOD TOKEN IS ECHOED, by the same program over the same
            # root -- so the refusals above are about the token and not about
            # the substitution.
            good = "a" * 32
            ran = subprocess.run(
                [sys.executable, "-c", program, "inspect", good],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(ran.returncode, 0, ran.stderr)
            answered = json.loads(ran.stdout)
            self.assertEqual(answered["custody"], "inspect")
            self.assertEqual(answered["submission"], good)
            self.assertTrue(any(one["path"] == "worker-output"
                                for one in answered["entries"]),
                            "the program did not walk the root it was given")

    # -- reopen, and holds that carry no token --------------------------------

    def test_the_token_survives_a_reopen_and_still_settles(self):
        """CORRELATION IS DURABLE, which is what makes it usable after a crash.

        The token is committed with the hold, so a restarted manager reads back
        the same value and the provider's answer still attributes. A token held
        only in the process that submitted would be no better than no token.
        """
        control, _composed, attempt_id, held = self.held_episode(
            "clear-reopen")
        submitted = self.submitted()
        control.close()

        reopened = self.reopened("clear-reopen-again")
        self.addCleanup(reopened.close)
        [again] = custody.custody_holds(reopened, attempt_id, "result")
        self.assertEqual(again["held"]["claimant"], held["claimant"])
        self.assertEqual(again["held"]["claimant"], submitted,
                         "the committed token is the one the act carried")

        # AND THE REOPENED MANAGER ACCEPTS THE ANSWER ABOUT THAT SUBMISSION.
        custody.clear_custody_hold(
            reopened, attempt_id=attempt_id, which="result", episode=0,
            observed="I asked the daemon after restarting",
            helper_identity=again["held"]["helper_identity"],
            settlement=self.answered(again["held"], submission=submitted))
        [cleared] = custody.custody_holds(reopened, attempt_id, "result")
        self.assertTrue(cleared["cleared"])

    def test_a_hold_that_committed_no_token_stays_held(self):
        """LEGACY HOLDS GAIN NO INVENTED EVIDENCE.

        An episode recorded before this contract carries no `claimant`, so
        nothing delivered can be attributed to its act. It is refused at the
        settlement AND on readback of a direct receipt, and its bytes and
        history are left exactly as they are.
        """
        control, _composed, attempt_id, held = self.held_episode(
            "clear-legacy")
        legacy = {one: value for one, value in held.items()
                  if one != "claimant"}
        identity = custody._hold_identity(custody.CUSTODY_HOLD_KIND,
                                          attempt_id, "result", 0)
        self.rewrite(control, identity, result=json.dumps(legacy),
                     signature=manager_signature(custody.CUSTODY_HOLD_KIND,
                                                 legacy))
        # IT IS STILL READ AS A STANDING HOLD -- refusing to read it would lose
        # the uncertainty, which is the opposite of conservative.
        [standing] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(standing["cleared"])
        self.assertNotIn("claimant", standing["held"])

        with self.assertRaises(ContractRefusal) as caught:
            custody.clear_custody_hold(
                control, attempt_id=attempt_id, which="result", episode=0,
                observed="I asked the daemon about the old act",
                helper_identity=legacy["helper_identity"],
                settlement=self.answered(legacy, submission=self.submitted()))
        self.assertIn("committed no submission token",
                      caught.exception.message)
        [after] = custody.custody_holds(control, attempt_id, "result")
        self.assertFalse(after["cleared"])

    def test_a_direct_receipt_cannot_lift_a_hold_with_no_token(self):
        """The same legacy rule on the READBACK path."""
        control, _composed, attempt_id, held = self.held_episode(
            "clear-legacy-direct")
        legacy = {one: value for one, value in held.items()
                  if one != "claimant"}
        self.rewrite(control,
                     custody._hold_identity(custody.CUSTODY_HOLD_KIND,
                                            attempt_id, "result", 0),
                     result=json.dumps(legacy),
                     signature=manager_signature(custody.CUSTODY_HOLD_KIND,
                                                 legacy))
        body = {"attempt_id": attempt_id, "root": "result", "episode": 0,
                "helper_identity": legacy["helper_identity"],
                "observed": "an old direct receipt",
                "accounted": custody.CUSTODY_DIRECT_ACT,
                "accounted_document": self.answered(
                    legacy, submission=self.submitted())["document"]}
        control.transact(
            custody._hold_identity(custody.CUSTODY_CLEARED_KIND, attempt_id,
                                   "result", 0),
            custody.CUSTODY_CLEARED_KIND,
            manager_signature(custody.CUSTODY_CLEARED_KIND, body),
            lambda _c: dict(body))
        with self.assertRaises(ContractRefusal) as caught:
            custody.custody_holds(control, attempt_id, "result")
        self.assertIn("committed no submission token",
                      caught.exception.message)

    # -- the selected runner root ---------------------------------------------

    def test_the_runner_root_is_the_one_the_owner_selected(self):
        """Owner 260109 names `/var/tmp/baton-w257624` for this stage too."""
        from baton_v12.worker_manager.source_boundary import (
            MEMORY_FILESYSTEMS, filesystem_of)
        from tests.manager import disk_roots

        named = os.environ.get(disk_roots.VARIABLE)
        if named is None:                                # pragma: no cover
            self.skipTest(f"{disk_roots.VARIABLE} is unset")
        self.assertNotIn(filesystem_of(named), MEMORY_FILESYSTEMS)
        self.assertEqual(os.stat(named).st_uid, os.getuid())
        self.assertTrue(os.access(named, os.W_OK))
        checkout = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
        self.assertFalse(os.path.abspath(named).startswith(
            os.path.abspath(checkout) + os.sep))


def load_tests(loader, standard, pattern):                   # noqa: ARG001
    """Only this module's own cases."""
    suite = unittest.TestSuite()
    for name in loader.getTestCaseNames(OnlyExactSettlementClearsOneHold):
        if name in OnlyExactSettlementClearsOneHold.__dict__:
            suite.addTest(OnlyExactSettlementClearsOneHold(name))
    return suite


if __name__ == "__main__":                                   # pragma: no cover
    unittest.main()
