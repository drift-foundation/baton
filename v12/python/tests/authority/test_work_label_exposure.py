"""W29401 — the exposure facts that HAVE a host in the current v12 product.

`work/records/2026/08/finding-v12-work-tags/findings/
finding-v12-work-label-protocol-cli/`.

WHY THIS FILE IS SMALL, and it is the finding's own instruction rather than a
shortfall. W29401's cut exposes the approved label contract through "canonical
create, mutation, projection, list and search protocol/CLI surfaces". Its Host
boundary says, in terms:

    Implementation must revalidate the current v12 protocol and CLI host after
    W29400. If a canonical Work create/list/search surface is still absent,
    document the observed absence and split or park only the unavailable
    exposure rather than introducing a parallel CLI or protocol product.

Revalidated 2026-08-29: **v12 has no CLI and no protocol host.** The product is
a Python library — `baton_v12.authority`, `.contracts`, `.worker_manager` —
and every `argparse`/`sys.argv` under `v12/` belongs to a test harness, a build
tool or the ping-pong spike. So the create/mutation/projection/list/search
bullets are already satisfied at the ONLY surface that exists, by W29400, and
`tests/authority/test_work_labels.py` holds them.

What is left for this file is the one acceptance bullet whose CLI form has no
host but whose UNDERLYING property does, and which nothing else asserts: that a
Work label and an OCI runtime label cannot be confused for one another. The
dossier's remaining CLI-shaped scope is parked rather than invented here.

THAT PREMISE IS NOW HALF FALSE, which is why this file grew rather than being
rewritten. W29401's first CLI slice gives the deployed bundle a `work`
subcommand (`tools/work_command.py`, proved as argv in
`tests/tools/test_work_command.py`) and `manager create --label`. The
revalidation above stays exactly as it was recorded: it is the history of why
the parked remainder was parked, and the two classes it produced are
unchanged.

WHAT THE NEW CLASSES ADD is the half the 2026-08-29 revalidation could not
reach, and it is a different surface rather than a second opinion. Those two
classes drive `Authority._core`, which is where a transaction is proved and is
not a surface anything outside this package may use. A command can reach only
the two PUBLIC faces -- the trusted-bootstrap `Authority` and the minted
participant-bound `Session` -- so the exposure a CLI actually depends on is
asserted there: the public creation face with its required operation identity,
the two session transitions and their enumerated table, the inventory
predicate's placement on the operator face, and a read-only handle that
answers every read while performing nothing. If a case below can do it,
`tools/work_command.py` can do it; if it cannot, no command can.
"""

import os
import tempfile
import unittest

from baton_v12.authority import V12
from baton_v12.authority.api import Authority
from baton_v12.authority.errors import Refusal
from baton_v12.authority.labels import MAX_LABELS, canonical_label
from baton_v12.authority.session import SESSION_READS, SESSION_TRANSITIONS
from baton_v12.worker_manager.oci import LABEL_PREFIX

UUID = "43c55d4b" + "0" * 24
WORK = "43c55d4b-W1"
ROUTE = "impl"
WHO = "baton.claude"
NOW = "2026-08-29T00:00:00.000Z"


class WorkLabelsAndRuntimeLabelsAreDifferentVOCABULARIES(unittest.TestCase):
    """The acceptance bullet is about DISPATCH, and the spelling is the trap.

    W29401 asks that "Work-label commands cannot dispatch Thread-label or
    OCI-label behaviour". That is a CLI-parsing property and there is no CLI —
    but the reason the bullet exists survives the absence of its host, and it
    is sharper than it looks: the two vocabularies OVERLAP in spelling.
    """

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-w29401-")
        self.addCleanup(root.cleanup)
        self.authority = Authority.create(
            os.path.join(root.name, "authority.sqlite3"),
            authority_uuid=UUID, clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core
        self.core.add_route_handler(ROUTE, WHO)

    def test_a_work_label_may_be_spelled_like_a_runtime_label_key(self):
        """MEASURED, because it decides what a future CLI may do.

        `canonical_label`'s grammar admits dots, so `baton.v12.work_id` — an
        OCI runtime label KEY this manager writes on every container — is a
        perfectly valid Work label. Only the `key=value` form is refused, and
        only because `=` is outside the alphabet.

        This is not a defect. The parent decision says no spelling is reserved
        and no behaviour is inferred from one. It IS a constraint on the
        exposure this Work exists to build: a CLI must separate Work labels
        from runtime labels by the COMMAND it dispatches, never by inspecting
        how a label is spelled, because the spellings are not disjoint.
        """
        overlapping = f"{LABEL_PREFIX}work_id"
        self.assertEqual(canonical_label(overlapping), overlapping)
        with self.assertRaises(Refusal):
            canonical_label(f"{LABEL_PREFIX}generation=1")

    def test_such_a_label_still_carries_no_runtime_meaning(self):
        """The property that makes the overlap safe, asserted rather than
        assumed: a Work wearing a runtime-shaped label is unchanged in every
        fact anything reads."""
        self.core.create_work(WORK, ROUTE, operation_id="create-1",
                              labels=(f"{LABEL_PREFIX}work_id",))
        projected = self.authority.project_work(WORK)
        self.assertEqual(projected["labels"], [f"{LABEL_PREFIX}work_id"])
        # NOTHING ELSE MOVED. The label is metadata and the scheduler axes are
        # exactly what an unlabelled Work's would be.
        self.assertEqual(projected["route"], ROUTE)
        self.assertEqual(projected["phase"], "queued")
        self.assertEqual(projected["status"], "open")
        self.assertIsNone(projected["handler"])
        self.assertIsNone(projected["gate"])

    def test_the_two_vocabularies_are_separate_functions_in_separate_packages(
            self):
        """There is no shared entry point that could dispatch the wrong one.

        `authority.labels.canonical_label` owns Work labels;
        `worker_manager.oci` owns the runtime label set. Neither package
        imports the other's label surface, which is what makes a CLI's job
        later a matter of naming two commands rather than untangling one.
        """
        from baton_v12.authority import labels as work_labels
        from baton_v12.worker_manager import oci

        self.assertFalse(hasattr(work_labels, "LABEL_PREFIX"))
        self.assertFalse(hasattr(oci, "canonical_label"))
        source = (os.path.join(os.path.dirname(work_labels.__file__),
                               "labels.py"))
        with open(source, encoding="utf-8") as reading:
            self.assertNotIn("worker_manager", reading.read())


class TheLibrarySurfaceAlreadyCarriesTheApprovedContract(unittest.TestCase):
    """One end-to-end pass over W29401's acceptance matrix at the host that
    exists, so the revalidation recorded in `FINDING.md` is a test rather than
    a claim.

    Every individual rule is W29400's and is held in detail by
    `tests/authority/test_work_labels.py`. What this adds is the ONE reading
    the exposure Work is accountable for: that create, projection and
    list/search compose into the contract W28880 approved.
    """

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-w29401-")
        self.addCleanup(root.cleanup)
        self.authority = Authority.create(
            os.path.join(root.name, "authority.sqlite3"),
            authority_uuid=UUID, clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self.core = self.authority._core
        self.core.add_route_handler(ROUTE, WHO)

    def made(self, number, labels):
        work = f"43c55d4b-W{number}"
        self.core.create_work(work, ROUTE, operation_id=f"create-{number}",
                              labels=labels)
        return work

    def test_create_takes_zero_one_and_repeated_labels(self):
        self.assertEqual(self.authority.labels_of(self.made(1, ())), [])
        self.assertEqual(self.authority.labels_of(self.made(2, ("alpha",))),
                         ["alpha"])
        # NORMALIZED AND DETERMINISTICALLY SORTED, which is what a projection
        # consumer and a future CLI both depend on.
        self.assertEqual(
            self.authority.labels_of(self.made(3, ("beta", "Gamma", "delta"))),
            ["beta", "delta", "gamma"])

    def test_the_projection_is_additive_for_unlabelled_work(self):
        """Backward compatibility, stated as the thing it actually is: a Work
        with no labels projects an empty list rather than a missing member, so
        a reader never has to tell absence from omission."""
        self.assertEqual(self.authority.project_work(self.made(1, ()))["labels"],
                         [])

    def test_positives_are_all_of_negatives_are_none_of_and_they_compose(self):
        self.made(1, ())
        self.made(2, ("alpha",))
        self.made(3, ("alpha", "beta"))
        self.assertEqual(sorted(self.authority.works_with_labels(
            all_of=("alpha", "beta"))), ["43c55d4b-W3"])
        self.assertEqual(sorted(self.authority.works_with_labels(
            none_of=("alpha",))), ["43c55d4b-W1"])
        self.assertEqual(sorted(self.authority.works_with_labels(
            all_of=("alpha",), none_of=("beta",))), ["43c55d4b-W2"])
        # AN EMPTY FILTER IS EVERY WORK, which is what makes the unfiltered
        # listing behaviour compatible rather than a special case.
        self.assertEqual(len(self.authority.works_with_labels()), 3)

    def test_no_or_syntax_is_introduced_and_a_contradiction_refuses(self):
        """This cut introduces no OR, and the one form that would need it —
        requiring and excluding the same label — is refused explicitly rather
        than silently answering nothing."""
        self.made(1, ("alpha",))
        with self.assertRaises(Refusal) as caught:
            self.authority.works_with_labels(all_of=("alpha",),
                                             none_of=("alpha",))
        self.assertIn("cannot both carry and not carry", str(caught.exception))


# -- W29401 slice 1: the same contract, through the PUBLIC faces only --------
#
# Nothing below touches `_core`. `V12` is the assignment contract a deployment
# creates its Work under, named so these cases create Work the way
# `creation_ports.WorkAuthorization` does.

SLAW = "baton.slaw"
OTHER = "43c55d4b-W2"
THIRD = "43c55d4b-W3"
PLATFORM = "scope:platform"


class PublicFaceCase(unittest.TestCase):
    """One disposable authority, reached only through its two public faces."""

    def setUp(self):
        root = tempfile.TemporaryDirectory(prefix="v12-w29401-public-")
        self.addCleanup(root.cleanup)
        self.path = os.path.join(root.name, "authority.sqlite3")
        self.authority = Authority.create(self.path, authority_uuid=UUID,
                                          clock=lambda: NOW)
        self.addCleanup(self.authority.dispose)
        self._operations = 0

    def op(self):
        self._operations += 1
        return f"op-{self._operations}"

    def work(self, work_id=WORK, *, labels=(), scope=None, operation_id=None):
        self.authority.create_work(
            work_id, ROUTE, contract=V12, labels=labels, scope=scope,
            operation_id=operation_id or ("create-" + work_id))
        self.authority.add_route_handler(ROUTE, WHO)
        return work_id

    def allow(self, participant=SLAW, scope=None):
        self.authority.grant_capability(participant, "manage-work-labels",
                                        scope=scope)
        return self.authority.session(participant)


class ThePublicCreationFaceCarriesLabels(PublicFaceCase):
    """`Authority.create_work(labels=..., operation_id=...)`.

    The zero/one/repeated and normalization readings are
    `TheLibrarySurfaceAlreadyCarriesTheApprovedContract`'s and are not
    repeated. What is new is the face: this one REQUIRES an operation
    identity, which is what makes a creation and its create-time labels
    replayable and gives every initial label event an act to be attributed
    to -- and a CLI has nothing else to call.
    """

    def test_the_public_face_applies_and_sorts_the_labels_it_is_given(self):
        self.work(WORK, labels=["Release-Foo", "V12", "hot"])
        self.assertEqual(self.authority.labels_of(WORK),
                         ["hot", "release-foo", "v12"])
        self.assertEqual(self.authority.project_work(WORK)["labels"],
                         ["hot", "release-foo", "v12"])

    def test_two_operands_that_are_one_key_refuse_and_create_nothing(self):
        with self.assertRaises(Refusal) as caught:
            self.work(WORK, labels=["v12", "V12"])
        self.assertIn("one label after normalization", str(caught.exception))
        with self.assertRaises(Refusal):
            self.authority.project_work(WORK)

    def test_a_malformed_create_time_label_refuses_and_creates_nothing(self):
        for bad in ("team=core", "v12,hot", "has space", "-leading", 7):
            with self.subTest(bad=bad):
                with self.assertRaises(Refusal):
                    self.work(WORK, labels=[bad])
                with self.assertRaises(Refusal):
                    self.authority.project_work(WORK)

    def test_the_cardinality_bound_is_the_works_and_is_checked_at_creation(self):
        full = [f"label-{index:02d}" for index in range(MAX_LABELS)]
        with self.assertRaises(Refusal) as caught:
            self.work(WORK, labels=full + ["one-too-many"])
        self.assertIn("at most", str(caught.exception))
        with self.assertRaises(Refusal):
            self.authority.project_work(WORK)
        # ...AND EXACTLY THE BOUND IS ACCEPTED, so that is the limit rather
        # than an off-by-one.
        self.work(WORK, labels=full)
        self.assertEqual(len(self.authority.labels_of(WORK)), MAX_LABELS)

    def test_an_exact_creation_retry_replays_and_adds_no_second_event(self):
        first = self.authority.create_work(
            WORK, ROUTE, contract=V12, operation_id="create-once",
            labels=["v12"])
        again = self.authority.create_work(
            WORK, ROUTE, contract=V12, operation_id="create-once",
            labels=["v12"])
        self.assertEqual(again, first)
        self.assertEqual(len(self.authority.work_label_events(WORK)), 1)

    def test_a_creation_retried_with_other_labels_collides(self):
        self.authority.create_work(WORK, ROUTE, contract=V12,
                                   operation_id="create-once", labels=["v12"])
        with self.assertRaises(Refusal) as caught:
            self.authority.create_work(WORK, ROUTE, contract=V12,
                                       operation_id="create-once",
                                       labels=["v12", "hot"])
        self.assertIn("reused for different operands", str(caught.exception))
        self.assertEqual(self.authority.labels_of(WORK), ["v12"])

    def test_a_create_time_label_is_attributed_to_the_creation_act(self):
        """Not to a `manage-work-labels` grant, because there was not one."""
        self.work(WORK, labels=["v12"], operation_id="create-attributed")
        event, = self.authority.work_label_events(WORK)
        self.assertEqual(event["act"], "work-create")
        self.assertEqual(event["act_id"], "create-attributed")
        self.assertIsNone(event["decision"])
        self.assertEqual(event["creation"]["kind"], "trusted-bootstrap")


class TheRuntimeFaceOwnsTheMutations(PublicFaceCase):
    """The two transitions, reached only through a minted session."""

    def test_the_enumerated_table_names_the_two_work_label_transitions(self):
        self.assertIn("label_work", SESSION_TRANSITIONS)
        self.assertIn("unlabel_work", SESSION_TRANSITIONS)

    def test_no_transition_is_spelled_like_v11s_thread_relation(self):
        """v11's `baton label` BINDS A THREAD TO A WORK.

        A v12 Work label is one opaque value carried BY a Work, and the two
        hosts run side by side. So the shorter spellings are deliberately
        ABSENT here rather than meaning a second thing -- which is the
        dispatch property `WorkLabelsAndRuntimeLabelsAreDifferentVOCABULARIES`
        states for the OCI vocabulary, in the direction a session faces.
        """
        for absent in ("label", "unlabel", "tag", "untag"):
            with self.subTest(absent=absent):
                self.assertNotIn(absent, SESSION_TRANSITIONS)
                self.assertNotIn(absent, SESSION_READS)

    def test_the_session_reads_one_works_labels_and_not_the_inventory(self):
        """`works_with_labels` answers about the whole deployment, and the
        runtime face reads facts rather than inventories."""
        self.assertIn("labels_of", SESSION_READS)
        self.assertIn("work_label_events", SESSION_READS)
        self.assertNotIn("works_with_labels", SESSION_READS)
        self.assertFalse(hasattr(self.authority.session(SLAW),
                                 "works_with_labels"))

    def test_a_session_may_not_name_the_actor_it_acts_as(self):
        self.work()
        session = self.allow()
        for forbidden in ("actor", "participant"):
            with self.subTest(forbidden=forbidden):
                with self.assertRaises(Refusal) as caught:
                    session.label_work({"work_id": WORK, "label": "v12",
                                        "operation_id": self.op(),
                                        forbidden: WHO})
                self.assertIn("takes its identity from the session",
                              str(caught.exception))
        self.assertEqual(self.authority.labels_of(WORK), [])

    def test_an_authorized_addition_and_removal_are_attributed_acts(self):
        self.work(WORK, labels=["v12"])
        session = self.allow()
        added = session.label_work({"work_id": WORK, "label": "Release-Foo",
                                    "operation_id": self.op()})
        self.assertTrue(added["changed"])
        self.assertEqual(added["label"], "release-foo")
        self.assertEqual(added["decision"]["role"], "manage-work-labels")
        self.assertEqual(added["decision"]["principal"],
                         self.authority.principal_of(SLAW))
        removed = session.unlabel_work({"work_id": WORK, "label": "v12",
                                        "operation_id": self.op()})
        self.assertTrue(removed["changed"])
        self.assertEqual(self.authority.labels_of(WORK), ["release-foo"])

    def test_a_participant_without_the_grant_changes_nothing(self):
        self.work(WORK, labels=["v12"])
        # THE ROUTE HANDLER AND THE CLAIMANT ARE NAMED NEGATIVES: holding the
        # Work is not holding the metadata capability.
        handler = self.authority.session(WHO)
        handler.claim({"work_id": WORK, "operation_id": self.op()})
        for one in (handler, self.authority.session("baton.nobody")):
            with self.subTest(participant=one.participant):
                with self.assertRaises(Refusal) as caught:
                    one.label_work({"work_id": WORK, "label": "hot",
                                    "operation_id": self.op()})
                self.assertIn("manage-work-labels", str(caught.exception))
                with self.assertRaises(Refusal):
                    one.unlabel_work({"work_id": WORK, "label": "v12",
                                      "operation_id": self.op()})
        self.assertEqual(self.authority.labels_of(WORK), ["v12"])
        self.assertEqual(len(self.authority.work_label_events(WORK)), 1)

    def test_the_decision_is_resolved_in_the_works_own_scope(self):
        self.work(WORK, scope=PLATFORM)
        self.allow()
        with self.assertRaises(Refusal):
            self.authority.session(SLAW).label_work(
                {"work_id": WORK, "label": "v12",
                 "operation_id": self.op()})
        self.assertEqual(self.authority.labels_of(WORK), [])
        session = self.allow(scope=PLATFORM)
        answer = session.label_work({"work_id": WORK, "label": "v12",
                                     "operation_id": self.op()})
        self.assertEqual(answer["decision"]["effective_scope"], PLATFORM)

    def test_an_exact_retry_replays_the_committed_act(self):
        self.work()
        session = self.allow()
        operation = self.op()
        first = session.label_work({"work_id": WORK, "label": "v12",
                                    "operation_id": operation})
        again = session.label_work({"work_id": WORK, "label": "v12",
                                    "operation_id": operation})
        self.assertEqual(again, first)
        self.assertEqual(len(self.authority.work_label_events(WORK)), 1)

    def test_the_same_identity_for_another_label_collides(self):
        self.work()
        session = self.allow()
        operation = self.op()
        session.label_work({"work_id": WORK, "label": "v12",
                            "operation_id": operation})
        with self.assertRaises(Refusal) as caught:
            session.label_work({"work_id": WORK, "label": "hot",
                                "operation_id": operation})
        self.assertIn("reused for different operands", str(caught.exception))
        self.assertEqual(self.authority.labels_of(WORK), ["v12"])

    def test_a_convergent_request_succeeds_and_reports_changed_false(self):
        self.work(WORK, labels=["v12"])
        session = self.allow()
        held = session.label_work({"work_id": WORK, "label": "v12",
                                   "operation_id": self.op()})
        self.assertFalse(held["changed"])
        self.assertEqual(held["labels"], ["v12"])
        absent = session.unlabel_work({"work_id": WORK,
                                       "label": "never-there",
                                       "operation_id": self.op()})
        self.assertFalse(absent["changed"])
        # NO EVENT FOR EITHER: a journal that recorded nothing happening could
        # no longer say what did.
        self.assertEqual(len(self.authority.work_label_events(WORK)), 1)


class LabelsOutliveTheWorkTheyDescribe(PublicFaceCase):
    """Audited label maintenance after terminal closure, through a session."""

    def closed(self):
        self.work(WORK, labels=["v12"])
        self.authority.grant_capability(WHO, "close")
        self.authority.session(WHO).close(
            {"work_id": WORK, "operation_id": self.op(),
             "outcome": "satisfying", "rationale": "done"})
        self.assertEqual(self.authority.project_work(WORK)["status"], "closed")

    def test_a_closed_work_is_still_labelled_and_unlabelled(self):
        self.closed()
        session = self.allow()
        session.label_work({"work_id": WORK, "label": "archived",
                            "operation_id": self.op()})
        session.unlabel_work({"work_id": WORK, "label": "v12",
                              "operation_id": self.op()})
        self.assertEqual(self.authority.labels_of(WORK), ["archived"])
        projection = self.authority.project_work(WORK)
        # AND THE CLOSURE IS UNTOUCHED: archive metadata reopens nothing.
        self.assertEqual(projection["status"], "closed")
        self.assertIsNone(projection["phase"])
        self.assertEqual(projection["outcome"], "satisfying")

    def test_the_post_closure_change_is_audited_like_any_other(self):
        self.closed()
        self.allow().label_work({"work_id": WORK, "label": "archived",
                                 "operation_id": "after-closure"})
        event = self.authority.work_label_events(WORK)[-1]
        self.assertEqual((event["act"], event["act_id"], event["action"]),
                         ("work-label", "after-closure", "added"))
        self.assertEqual(event["decision"]["role"], "manage-work-labels")


class AReadOnlyHandleAnswersEveryLabelRead(PublicFaceCase):
    """W29401's `work labels` and `work list` take this handle, so it has to
    answer -- and a mutation through it must not."""

    def test_the_three_reads_answer_and_a_mutation_refuses(self):
        self.work(WORK, labels=["v12", "release-foo"])
        self.authority.create_work(OTHER, ROUTE, contract=V12,
                                   operation_id="create-" + OTHER,
                                   labels=["v12"])
        self.authority.create_work(THIRD, ROUTE, contract=V12,
                                   operation_id="create-" + THIRD)
        self.authority.grant_capability(SLAW, "manage-work-labels")
        with Authority.open_readonly(
                self.path, expected_authority_uuid=UUID) as reader:
            self.assertEqual(reader.labels_of(WORK), ["release-foo", "v12"])
            self.assertEqual(
                [one["label"] for one in reader.work_label_events(WORK)],
                ["release-foo", "v12"])
            self.assertEqual(reader.works_with_labels(all_of=["v12"]),
                             sorted([WORK, OTHER]))
            self.assertEqual(reader.works_with_labels(none_of=["v12"]),
                             [THIRD])
            with self.assertRaises(Refusal) as caught:
                reader.session(SLAW).label_work(
                    {"work_id": WORK, "label": "hot",
                     "operation_id": self.op()})
            self.assertIn("opened for reading", str(caught.exception))
        self.assertEqual(self.authority.labels_of(WORK),
                         ["release-foo", "v12"])


if __name__ == "__main__":
    unittest.main()
