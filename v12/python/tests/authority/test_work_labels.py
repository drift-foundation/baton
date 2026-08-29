"""W29400 — the Work-label authority model.

The approved W28880 contract, implemented against the authority W16821 left.
A Work label is ONE OPAQUE KEY of cross-cutting metadata: it is not a
`name=value` pair, it inherits nowhere, it is not the Thread-Work `label`
relation, it is not the Worker Manager's OCI runtime labels, and no scheduler
or authority behaviour follows from how one is spelled.

WHAT EACH CLASS ESTABLISHES, and the matrix in the record names all of it:
grammar and cardinality; scope-resolved `manage-work-labels` authority and the
negatives the contract lists by name; audited mutation after terminal closure;
exact replay, operation collision and convergent `changed:false`; deterministic
projection and all-of/none-of predicates with no implicit OR; and that a
suggestive label changes nothing a scheduler reads.
"""

import os
import tempfile
import unittest

from baton_v12.authority import Authority, Refusal, V12
from baton_v12.authority.labels import (MAX_LABEL_LENGTH, MAX_LABELS,
                                        canonical_label, canonical_label_set)
from baton_v12.authority.principals import DEPLOYMENT_SCOPE, DIRECT

UUID = "0123456789abcdef0123456789abcdef"
WORK = "0123abcd-W7"
OTHER = "0123abcd-W8"
CLAUDE = "baton.claude"
GEMINI = "baton.gemini"
ROUTE = "impl"
NOW = "2026-08-28T23:00:00.000Z"
PLATFORM = "scope:platform"


class LabelCase(unittest.TestCase):
    def setUp(self):
        self._root = tempfile.TemporaryDirectory(prefix="v12-w29400-")
        self.addCleanup(self._root.cleanup)
        self.path = os.path.join(self._root.name, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID,
                                          clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core
        self._operations = 0

    def op(self):
        self._operations += 1
        return f"op-{self._operations}"

    def work(self, work_id=WORK, *, labels=(), scope=None, handlers=(CLAUDE,)):
        self.core.create_work(work_id, ROUTE, contract=V12, labels=labels, operation_id=("create-" + str(work_id))[:160],
                              scope=scope)
        for participant in handlers:
            self.core.add_route_handler(ROUTE, participant)
        return work_id

    def allowed(self, participant=GEMINI, scope=None):
        self.authority.grant_capability(participant, "manage-work-labels",
                                        scope=scope)
        return participant


class TheGrammarIsOneOpaqueKey(LabelCase):

    def test_mixed_case_normalizes_and_projects_lowercase(self):
        self.work(labels=["Release-Foo", "V12"])
        self.assertEqual(self.authority.project_work(WORK)["labels"],
                         ["release-foo", "v12"])

    def test_the_boundaries_of_the_grammar(self):
        for good in ("a", "0", "a" * MAX_LABEL_LENGTH, "a.b_c-d",
                     "requested-slaw"):
            with self.subTest(good=good):
                self.assertEqual(canonical_label(good), good)
        for bad in ("", "-leading", ".leading", "_leading",
                    "a" * (MAX_LABEL_LENGTH + 1), "has space", "has=equals",
                    "has/slash", "has\ttab", "has\nnewline", "café",
                    "İ", None, 7, ["v12"]):
            with self.subTest(bad=bad):
                with self.assertRaises(Refusal):
                    canonical_label(bad)

    def test_a_label_is_never_taken_apart(self):
        """Dots, underscores and hyphens are ordinary characters.

        A set carrying `a.b` does not carry `a`, and a filter for `a` does not
        match it: the whole normalized string is the key, and nothing in this
        model reads structure out of one.
        """
        self.work(labels=["a.b"])
        self.assertEqual(self.authority.project_work(WORK)["labels"], ["a.b"])
        self.assertEqual(self.core.works_with_labels(all_of=["a"]), [])
        self.assertEqual(self.core.works_with_labels(all_of=["a.b"]), [WORK])

    def test_two_operands_that_normalize_to_one_key_refuse(self):
        """A caller who wrote two things meant two things."""
        with self.assertRaises(Refusal) as caught:
            canonical_label_set(["v12", "V12"])
        self.assertIn("one label after normalization", str(caught.exception))
        with self.assertRaises(Refusal):
            self.core.create_work(OTHER, ROUTE, labels=["v12", "V12"], operation_id=("create-" + str(OTHER))[:160])
        # AND NOTHING WAS CREATED. A refusal about the operands leaves no Work.
        with self.assertRaises(Refusal):
            self.authority.project_work(OTHER)

    def test_the_cardinality_boundary(self):
        full = [f"label-{index:02d}" for index in range(MAX_LABELS)]
        self.work(labels=full)
        self.assertEqual(len(self.authority.project_work(WORK)["labels"]),
                         MAX_LABELS)
        self.allowed()
        with self.assertRaises(Refusal) as caught:
            self.core.label_work(WORK, "one-too-many", actor=GEMINI,
                                 operation_id=self.op())
        self.assertIn("maximum", str(caught.exception))
        with self.assertRaises(Refusal):
            self.core.create_work(OTHER, ROUTE, labels=full + ["extra"], operation_id=("create-" + str(OTHER))[:160])

    def test_a_full_set_still_accepts_a_label_it_already_holds(self):
        """The convergent no-op is not charged against the cardinality.

        Refusing it would refuse a caller asking for a state the Work is
        already in.
        """
        full = [f"label-{index:02d}" for index in range(MAX_LABELS)]
        self.work(labels=full)
        self.allowed()
        answer = self.core.label_work(WORK, full[0], actor=GEMINI,
                                      operation_id=self.op())
        self.assertFalse(answer["changed"])


class TheAuthorityIsScopeResolved(LabelCase):

    def test_a_grant_in_the_works_scope_authorizes(self):
        self.work(scope=PLATFORM)
        self.allowed(scope=PLATFORM)
        answer = self.core.label_work(WORK, "v12", actor=GEMINI,
                                      operation_id=self.op())
        self.assertTrue(answer["changed"])
        self.assertEqual(answer["decision"]["effective_scope"], PLATFORM)
        self.assertEqual(answer["decision"]["role"], "manage-work-labels")
        self.assertEqual(answer["decision"]["grant"], DIRECT)

    def test_a_deployment_grant_does_not_authorize_a_scoped_work(self):
        self.work(scope=PLATFORM)
        self.allowed()
        with self.assertRaises(Refusal) as caught:
            self.core.label_work(WORK, "v12", actor=GEMINI,
                                 operation_id=self.op())
        self.assertIn("manage-work-labels", str(caught.exception))
        self.assertEqual(self.authority.project_work(WORK)["labels"], [])

    def test_route_membership_and_the_claim_authorize_nothing(self):
        """The contract names these by name, so they are refused by name.

        `baton.claude` is the configured Route handler and takes the claim; it
        holds no `manage-work-labels` grant and therefore may not label.
        """
        self.work()
        self.core.claim(WORK, CLAUDE, operation_id=self.op())
        self.assertEqual(self.authority.project_work(WORK)["handler"], CLAUDE)
        for actor in (CLAUDE, GEMINI, "baton.nobody"):
            with self.subTest(actor=actor):
                with self.assertRaises(Refusal) as caught:
                    self.core.label_work(WORK, "v12", actor=actor,
                                         operation_id=self.op())
                self.assertIn("does not hold", str(caught.exception))

    def test_no_operand_names_a_principal_or_a_scope(self):
        import inspect

        for name in ("label_work", "unlabel_work"):
            parameters = set(inspect.signature(
                getattr(type(self.core), name)).parameters)
            with self.subTest(name=name):
                self.assertNotIn("principal", parameters)
                self.assertNotIn("scope", parameters)

    def test_a_revoked_grant_stops_authorizing_immediately(self):
        self.work()
        self.allowed()
        self.core.label_work(WORK, "v12", actor=GEMINI,
                             operation_id=self.op())
        self.authority.revoke_capability(GEMINI, "manage-work-labels")
        with self.assertRaises(Refusal):
            self.core.label_work(WORK, "release-foo", actor=GEMINI,
                                 operation_id=self.op())
        self.assertEqual(self.authority.project_work(WORK)["labels"], ["v12"])


class LabellingSurvivesTerminalClosure(LabelCase):
    """The contract permits audited label maintenance after closure.

    It changes archive metadata and reopens, reschedules and re-authorizes
    nothing -- so there is deliberately no status or phase check to remove.
    """

    def closed(self):
        self.work(labels=["v12"])
        self.authority.grant_capability(CLAUDE, "close")
        self.core.close(WORK, operation_id=self.op(), outcome="satisfying",
                        rationale="done", actor=CLAUDE)
        self.assertEqual(self.authority.project_work(WORK)["status"], "closed")

    def test_a_closed_work_can_still_be_labelled_and_unlabelled(self):
        self.closed()
        self.allowed()
        self.core.label_work(WORK, "archived", actor=GEMINI,
                             operation_id=self.op())
        self.core.unlabel_work(WORK, "v12", actor=GEMINI,
                               operation_id=self.op())
        self.assertEqual(self.authority.project_work(WORK)["labels"],
                         ["archived"])
        # AND THE WORK IS STILL CLOSED. A label change reopens nothing.
        projection = self.authority.project_work(WORK)
        self.assertEqual(projection["status"], "closed")
        self.assertIsNone(projection["phase"])
        self.assertEqual(projection["outcome"], "satisfying")

    def test_the_change_is_audited_like_any_other(self):
        self.closed()
        self.allowed()
        self.core.label_work(WORK, "archived", actor=GEMINI,
                             operation_id=self.op())
        events = self.authority.work_label_events(WORK)
        self.assertEqual([(one["label"], one["action"]) for one in events],
                         [("v12", "added"), ("archived", "added")])
        # THE CREATION'S ADDITION IS ATTRIBUTED TO THE CREATION ACT, and this
        # case used to require the opposite. It asserted `decision is None`,
        # which encoded exactly the gap the approved contract forbids: a
        # create-time addition that no reader could attribute. It names the
        # trusted bootstrap now -- a real answer to "under what authority" --
        # and the two acts are told apart by their kind and role rather than
        # by one of them being blank.
        self.assertEqual(events[0]["act"], "work-create")
        self.assertEqual(events[0]["decision"]["role"], "create-work")
        self.assertEqual(events[0]["decision"]["principal"],
                         "principal:authority-bootstrap")
        self.assertEqual(events[1]["act"], "work-label")
        self.assertEqual(events[1]["decision"]["principal"],
                         self.authority.principal_of(GEMINI))
        self.assertEqual(events[1]["decision"]["role"], "manage-work-labels")


class ReplayAndConvergence(LabelCase):

    def setUp(self):
        super().setUp()
        self.work()
        self.allowed()

    def test_an_exact_retry_replays_the_recorded_outcome(self):
        operation = self.op()
        first = self.core.label_work(WORK, "v12", actor=GEMINI,
                                     operation_id=operation)
        again = self.core.label_work(WORK, "v12", actor=GEMINI,
                                     operation_id=operation)
        self.assertEqual(again, first)
        self.assertTrue(first["changed"])
        self.assertEqual(len(self.authority.work_label_events(WORK)), 1)

    def test_an_exact_retry_does_not_reauthorize_after_revocation(self):
        """Replay answers the committed act, not whether it could happen now."""
        operation = self.op()
        first = self.core.label_work(WORK, "v12", actor=GEMINI,
                                     operation_id=operation)
        self.authority.revoke_capability(GEMINI, "manage-work-labels")
        self.assertEqual(
            self.core.label_work(WORK, "v12", actor=GEMINI,
                                 operation_id=operation),
            first)

    def test_reusing_the_id_for_another_label_collides(self):
        operation = self.op()
        self.core.label_work(WORK, "v12", actor=GEMINI,
                             operation_id=operation)
        with self.assertRaises(Refusal) as caught:
            self.core.label_work(WORK, "release-foo", actor=GEMINI,
                                 operation_id=operation)
        self.assertIn("reused for different operands",
                      str(caught.exception))
        self.assertEqual(self.authority.project_work(WORK)["labels"], ["v12"])

    def test_adding_a_present_label_changes_nothing_and_writes_no_event(self):
        self.core.label_work(WORK, "v12", actor=GEMINI,
                             operation_id=self.op())
        answer = self.core.label_work(WORK, "v12", actor=GEMINI,
                                      operation_id=self.op())
        self.assertFalse(answer["changed"])
        self.assertEqual(answer["labels"], ["v12"])
        self.assertEqual(len(self.authority.work_label_events(WORK)), 1)

    def test_removing_an_absent_label_changes_nothing_and_writes_no_event(self):
        answer = self.core.unlabel_work(WORK, "never-there", actor=GEMINI,
                                        operation_id=self.op())
        self.assertFalse(answer["changed"])
        self.assertEqual(answer["labels"], [])
        self.assertEqual(self.authority.work_label_events(WORK), [])

    def test_a_no_op_retains_no_authorization_decision(self):
        """A decision row for an act that did not happen would be evidence of
        a change the journal correctly does not have."""
        operation = self.op()
        self.core.unlabel_work(WORK, "never-there", actor=GEMINI,
                               operation_id=operation)
        self.assertIsNone(self.authority.decision_of("work-unlabel", operation))

    def test_add_then_remove_leaves_one_coherent_set_and_history(self):
        self.core.label_work(WORK, "v12", actor=GEMINI,
                             operation_id=self.op())
        self.core.unlabel_work(WORK, "v12", actor=GEMINI,
                               operation_id=self.op())
        self.core.label_work(WORK, "v12", actor=GEMINI,
                             operation_id=self.op())
        self.assertEqual(self.authority.project_work(WORK)["labels"], ["v12"])
        self.assertEqual(
            [one["action"] for one in self.authority.work_label_events(WORK)],
            ["added", "removed", "added"])


class ProjectionsAndPredicates(LabelCase):

    def setUp(self):
        super().setUp()
        self.work(WORK, labels=["v12", "release-foo"])
        self.core.create_work(OTHER, ROUTE, contract=V12, labels=["v12"], operation_id=("create-" + str(OTHER))[:160])
        self.core.create_work("0123abcd-W9", ROUTE, contract=V12, operation_id="create-" + "0123abcd-W9")

    def test_an_unlabelled_work_projects_an_empty_list(self):
        self.assertEqual(
            self.authority.project_work("0123abcd-W9")["labels"], [])

    def test_repeated_positives_intersect(self):
        self.assertEqual(self.core.works_with_labels(all_of=["v12"]),
                         sorted([WORK, OTHER]))
        self.assertEqual(
            self.core.works_with_labels(all_of=["v12", "release-foo"]), [WORK])

    def test_repeated_negatives_exclude(self):
        self.assertEqual(self.core.works_with_labels(none_of=["v12"]),
                         ["0123abcd-W9"])
        self.assertEqual(
            self.core.works_with_labels(all_of=["v12"],
                                        none_of=["release-foo"]), [OTHER])

    def test_a_contradictory_filter_refuses(self):
        with self.assertRaises(Refusal) as caught:
            self.core.works_with_labels(all_of=["v12"], none_of=["v12"])
        self.assertIn("cannot both carry and not carry", str(caught.exception))

    def test_matching_is_exact_membership_and_never_a_substring(self):
        for near in ("v1", "12", "v123", "release", "foo", "RELEASE-FOO "):
            with self.subTest(near=near):
                if near.strip() != near or not near.strip():
                    with self.assertRaises(Refusal):
                        self.core.works_with_labels(all_of=[near])
                    continue
                self.assertEqual(self.core.works_with_labels(all_of=[near]),
                                 [])
        # ...and the case-insensitive spelling of a real one DOES match.
        self.assertEqual(self.core.works_with_labels(all_of=["V12"]),
                         sorted([WORK, OTHER]))

    def test_an_empty_filter_is_every_work(self):
        self.assertEqual(self.core.works_with_labels(),
                         sorted([WORK, OTHER, "0123abcd-W9"]))

    def test_work_and_labels_are_read_from_one_snapshot(self):
        """A projection is wholly before or wholly after an interleaved act."""
        self.authority.grant_capability(CLAUDE, "close")
        self.allowed()
        other = Authority.open(self.path, expected_authority_uuid=UUID,
                               clock=lambda: NOW)
        self.addCleanup(other.dispose)
        original = self.core.labels_of
        crossed = False

        def labels_after_close(work_id):
            nonlocal crossed
            if not crossed:
                crossed = True
                other._core.close(
                    WORK, operation_id="snapshot-close",
                    outcome="satisfying", rationale="snapshot crossing",
                    actor=CLAUDE)
                other._core.label_work(
                    WORK, "archived", actor=GEMINI,
                    operation_id="snapshot-label")
            return original(work_id)

        self.core.labels_of = labels_after_close
        try:
            projection = self.core.project_work(WORK)
        finally:
            self.core.labels_of = original
        observed = projection["status"], tuple(projection["labels"])
        self.assertIn(observed, {
            ("open", ("release-foo", "v12")),
            ("closed", ("archived", "release-foo", "v12")),
        })

    def test_label_predicates_read_work_and_labels_from_one_snapshot(self):
        """A newly labelled Work is never observed without its label."""
        other = Authority.open(self.path, expected_authority_uuid=UUID,
                               clock=lambda: NOW)
        self.addCleanup(other.dispose)
        original = self.core._store.all
        created = False
        new_work = "0123abcd-W10"

        def rows_then_create(sql, *args):
            nonlocal created
            rows = original(sql, *args)
            if not created and sql == "SELECT work_id, label FROM work_label":
                created = True
                other._core.create_work(new_work, ROUTE, contract=V12, operation_id=("create-" + str(new_work))[:160],
                                        labels=["excluded"])
            return rows

        self.core._store.all = rows_then_create
        try:
            matched = self.core.works_with_labels(none_of=["excluded"])
        finally:
            self.core._store.all = original
        self.assertNotIn(new_work, matched)


class LabelsChangeNothingElse(LabelCase):
    """Section 6 of the contract, as a measurement.

    A suggestive spelling changes the label set and the label journal and
    NOTHING a scheduler, an assignment or a runtime reads.
    """

    def test_a_suggestive_label_leaves_every_other_fact_unchanged(self):
        self.work(scope=PLATFORM)
        self.allowed(scope=PLATFORM)
        before = self.authority.project_work(WORK)
        for suggestive in ("blocked", "priority-high", "route-rview",
                           "contract-v11", "baton.gemini", "closed"):
            self.core.label_work(WORK, suggestive, actor=GEMINI,
                                 operation_id=self.op())
        after = self.authority.project_work(WORK)
        self.assertNotEqual(before["labels"], after["labels"])
        for member in [name for name in before if name != "labels"]:
            with self.subTest(member=member):
                self.assertEqual(before[member], after[member])

    def test_labels_do_not_inherit_to_anything(self):
        """Every Work's set is explicit; nothing copies one."""
        self.work(WORK, labels=["v12"])
        self.core.create_work(OTHER, ROUTE, contract=V12, operation_id=("create-" + str(OTHER))[:160])
        self.assertEqual(self.authority.project_work(OTHER)["labels"], [])

    def test_a_labelled_work_is_still_claimable_exactly_as_before(self):
        self.work(WORK, labels=["blocked", "parked"])
        answer = self.core.claim(WORK, CLAUDE, operation_id=self.op())
        # W16823: the claim answers a closed result; the fence is a member.
        self.assertEqual(answer["assignment"]["participant"], CLAUDE)
        self.assertEqual(self.authority.project_work(WORK)["phase"], "active")


class RealCompetingConnectionsReachOneCoherentSet(LabelCase):
    """W29400 review: "the 28 submitted tests contain sequential convergence
    only".

    THESE ARE REAL SECOND CONNECTIONS over the same file, run from real
    threads, because the finding the corrections answer is about what happens
    BETWEEN two statements. A sequential case cannot reach that window: it is
    the window. Each case here opens a second `Authority` on the same path and
    lets the two contend.

    WHAT THEY PROVE is the pair of orderings the review required -- the
    decision, the mutation, the event and the decision row serialize together,
    and an exact retry consults the journal before current policy.
    """

    def setUp(self):
        super().setUp()
        self.work()
        self.allowed()

    def beside(self):
        """A SECOND authority over the same file, disposed with the case."""
        other = Authority.open(self.path, expected_authority_uuid=UUID,
                               clock=lambda: NOW)
        self.addCleanup(other.dispose)
        return other

    def race(self, first, second):
        """Both acts, from two threads, EACH OPENING ITS OWN CONNECTION.

        MY PREVIOUS HARNESS RACED NOTHING, and review [P1] was righter than it
        knew. It opened both authorities on the main thread and called them
        from workers, so every act died with `ProgrammingError: SQLite objects
        created in a thread can only be used in that same thread`. Nothing
        contended, no history was written, and the coherence assertion passed
        over an empty set. I then wrote "both writers losing is a legitimate
        outcome" into the record -- rationalising a broken harness instead of
        reading what it returned.

        So each thread opens its OWN `Authority` on the shared file, inside
        the thread, and a RAW EXCEPTION IS A FAILURE. The Store's contract is
        that contention WAITS on `busy_timeout`; a loser receives a reasoned
        `Refusal`, never a database-busy fault. Anything else is the harness
        or the store being wrong and this matrix now says so.
        """
        import threading
        answers = {}

        def call(name, act):
            other = Authority.open(self.path, expected_authority_uuid=UUID,
                                   clock=lambda: NOW)
            try:
                answers[name] = act(other)
            except Refusal as refused:
                answers[name] = refused
            except Exception as failure:      # noqa: BLE001
                answers[name] = ("raw", failure)
            finally:
                other.dispose()

        threads = [threading.Thread(target=call, args=("first", first)),
                   threading.Thread(target=call, args=("second", second))]
        for one in threads:
            one.start()
        for one in threads:
            one.join(timeout=30)
        for name, answer in answers.items():
            self.assertNotIsInstance(answer, tuple,
                                     f"{name} took a raw fault: {answer}")
        self.assertEqual(sorted(answers), ["first", "second"],
                         f"a racer never answered: {answers}")
        return answers

    def effective(self, answers):
        """AT LEAST ONE REQUEST TOOK EFFECT, which is the point of a race.

        Both sides being no-ops is not an outcome this matrix accepts: it is
        what a build where every mutation fails looks like, and that build
        used to pass the whole thing.
        """
        acted = [one for one in answers.values()
                 if isinstance(one, dict) and one.get("changed")]
        self.assertTrue(acted, f"no request took effect: {answers}")
        return acted

    def events(self):
        return self.authority.work_label_events(WORK)

    def coherent(self):
        """THE INVARIANT EVERY RACE BELOW IS ABOUT, and the only one.

        SUPERSEDED TEXT REMOVED. An earlier version of this docstring said
        both writers losing was a legitimate outcome. It is not, and it never
        was: that sentence was written to accommodate a harness whose threads
        could not use their connections at all. The Store's contract is that
        contention WAITS, a winner commits and a loser receives a reasoned
        refusal, and `race` and `effective` now hold it to that.

        What this checks is what remains true whichever request won: the
        append-only history replays EXACTLY to the live set and no act appears
        twice. A half-applied act or a duplicated event breaks it, and that is
        what the transaction corrections protect.
        """
        held = sorted(self.authority.labels_of(WORK))
        rebuilt = set()
        seen = []
        for one in self.events():
            self.assertIn(one["action"], ("added", "removed"), one)
            seen.append((one["label"], one["action"], one["seq"]))
            if one["action"] == "added":
                rebuilt.add(one["label"])
            else:
                rebuilt.discard(one["label"])
        self.assertEqual(sorted(rebuilt), held,
                         "the history does not replay to the live set")
        self.assertEqual(len(seen), len(set(seen)), "an act appears twice")
        return held

    def test_two_connections_adding_the_same_label_leave_one_event(self):
        answers = self.race(
            lambda one: one._core.label_work(WORK, "v12", actor=GEMINI,
                                             operation_id="race-add-a"),
            lambda one: one._core.label_work(WORK, "v12", actor=GEMINI,
                                             operation_id="race-add-b"))
        self.effective(answers)
        held = self.coherent()
        # EXACTLY ONE ADDITION. One connection commits and the other converges
        # on it as a `changed: False` no-op -- which is the contract, and is
        # what a real race actually returns.
        added = [one for one in self.events() if one["action"] == "added"]
        self.assertEqual(len(added), 1, self.events())
        self.assertEqual(held, ["v12"])

    def test_two_connections_removing_the_same_label_leave_one_event(self):
        self.core.label_work(WORK, "v12", actor=GEMINI, operation_id=self.op())
        answers = self.race(
            lambda one: one._core.unlabel_work(WORK, "v12", actor=GEMINI,
                                               operation_id="race-rm-a"),
            lambda one: one._core.unlabel_work(WORK, "v12", actor=GEMINI,
                                               operation_id="race-rm-b"))
        self.effective(answers)
        held = self.coherent()
        removed = [one for one in self.events() if one["action"] == "removed"]
        self.assertEqual(len(removed), 1, self.events())
        self.assertEqual(held, [])

    def test_an_add_racing_a_remove_settles_on_one_of_the_two(self):
        """EITHER outcome is correct; a THIRD is not.

        The label is present or absent, the history agrees with whichever it
        is, and nothing is half-applied.
        """
        self.core.label_work(WORK, "v12", actor=GEMINI, operation_id=self.op())
        answers = self.race(
            lambda one: one._core.unlabel_work(WORK, "v12", actor=GEMINI,
                                               operation_id="race-x-rm"),
            lambda one: one._core.label_work(WORK, "second", actor=GEMINI,
                                             operation_id="race-x-add"))
        self.effective(answers)
        self.coherent()

    def test_the_final_slot_is_taken_once(self):
        """THIRTY-TWO IS THE CEILING and two connections want the last one."""
        for index in range(31):
            self.core.label_work(WORK, f"held-{index}", actor=GEMINI,
                                 operation_id=self.op())
        self.assertEqual(len(self.authority.labels_of(WORK)), 31)
        answers = self.race(
            lambda one: one._core.label_work(WORK, "last-a", actor=GEMINI,
                                             operation_id="race-slot-a"),
            lambda one: one._core.label_work(WORK, "last-b", actor=GEMINI,
                                             operation_id="race-slot-b"))
        self.effective(answers)
        held = self.coherent()
        # THE CEILING IS NEVER EXCEEDED and EXACTLY ONE contender took the
        # last slot: 32 labels, one of the two names, never both.
        self.assertEqual(len(held), 32, held)
        self.assertEqual(len(set(held)), len(held))
        self.assertEqual(len({"last-a", "last-b"} & set(held)), 1, held)

    def test_a_revocation_racing_a_first_execution_never_half_applies(self):
        """The window the review named: authorization outside the write.

        Whatever the race decides, a label that was added carries a decision
        row and a label that was refused left no event -- the decision, the
        mutation and the event are one act or they are none of it.
        """
        answers = self.race(
            lambda one: one._core.label_work(WORK, "v12", actor=GEMINI,
                                             operation_id="race-grant"),
            lambda one: one.revoke_capability(GEMINI, "manage-work-labels"))
        held = self.coherent()
        events = self.events()
        if "v12" in held:
            self.assertEqual(len(events), 1, events)
            self.assertIsNotNone(events[0]["decision"], events[0])
        else:
            self.assertEqual(events, [], events)
